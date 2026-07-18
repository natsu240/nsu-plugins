#!/usr/bin/env python3
import json
import sys
import os
import re
import math
import subprocess
import time
from datetime import datetime

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"

EIGHTHS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]


def ceil_pct(x):
    if x is None:
        return None
    return int(math.ceil(x - 1e-9))


def fmt_window(size):
    if not size:
        return "?"
    if size % 10000 == 0:
        return f"{size // 10000}万"
    return f"{size:,}"


def fmt_tokens(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_duration_ms(ms):
    try:
        total_s = int(ms) // 1000
    except (TypeError, ValueError):
        total_s = 0
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def fmt_countdown(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def fmt_reset_dt(ts):
    if ts is None:
        return "?"
    dt = datetime.fromtimestamp(ts)
    return f"{dt.month}/{dt.day}({WEEKDAY_JA[dt.weekday()]}){dt.hour:02d}:{dt.minute:02d}"


def fmt_reset_time(ts):
    if ts is None:
        return "?"
    dt = datetime.fromtimestamp(ts)
    return f"{dt.hour:02d}:{dt.minute:02d}"


def fmt_remaining_full(seconds):
    """'あと4時間23分11秒' style full breakdown, with days when relevant."""
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d > 0:
        return f"{d}日{h:02d}時間{m:02d}分{s:02d}秒"
    if h > 0:
        return f"{h}時間{m:02d}分{s:02d}秒"
    if m > 0:
        return f"{m}分{s:02d}秒"
    return f"{s}秒"


def render_bar(pct, width=20):
    """Sub-character resolution bar using eighth-block glyphs."""
    pct = max(0.0, min(100.0, pct))
    total_eighths = round(pct / 100 * width * 8)
    full, remainder = divmod(total_eighths, 8)
    full = min(full, width)
    bar = "█" * full
    if full < width:
        bar += EIGHTHS[remainder]
        bar += "░" * (width - full - 1)
    return bar


def latest_cli_version():
    path = os.path.expanduser("~/.claude/cache/changelog.md")
    try:
        with open(path, "r") as f:
            for line in f:
                m = re.match(r"^##\s+([0-9][0-9.]*)", line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


def git_branch(cwd):
    try:
        out = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, capture_output=True, text=True, timeout=1,
        )
        branch = out.stdout.strip()
        return branch or None
    except Exception:
        return None


def cached_git_branch(cwd, state, now, ttl=5):
    """git spawns a subprocess; with refreshInterval=1 this runs every second,
    so cache the result for a few seconds instead of shelling out every tick."""
    ts = state.get("branch_ts")
    if ts is not None and (now - ts) < ttl:
        return state.get("branch_val")
    val = git_branch(cwd)
    state["branch_ts"] = now
    state["branch_val"] = val
    return val


def projected_pct(used_pct, resets_at, window_seconds, now):
    """Linear extrapolation: at the current pace, what % will be used by reset?"""
    if used_pct is None or resets_at is None:
        return None
    window_start = resets_at - window_seconds
    elapsed = max(now - window_start, 0)
    if elapsed <= 0:
        return used_pct
    return used_pct * window_seconds / elapsed


def state_path(session_id):
    return f"/tmp/claude-statusline-state-{session_id}"


def read_state(session_id):
    try:
        with open(state_path(session_id), "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_state(session_id, state):
    try:
        with open(state_path(session_id), "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def main():
    data = json.load(sys.stdin)
    now = time.time()

    model_name = data.get("model", {}).get("display_name", "?")
    version = data.get("version") or "?"
    latest = latest_cli_version()
    if latest and latest != version:
        version_str = f"v{version} → {latest}"
    else:
        version_str = f"v{version} (latest)"

    effort = data.get("effort", {}).get("level")

    cwd = data.get("workspace", {}).get("current_dir") or data.get("cwd") or "."
    dirname = os.path.basename(cwd.rstrip("/")) or cwd

    ctx = data.get("context_window", {}) or {}
    pct_raw = ctx.get("used_percentage")
    window_size = ctx.get("context_window_size") or 200000
    total_input = ctx.get("total_input_tokens")

    session_id = data.get("session_id", "unknown")
    state = read_state(session_id)
    branch = cached_git_branch(cwd, state, now)

    # --- Line 1: model, version, effort, dir, branch ---
    line1 = f"\U0001F916 {model_name} {version_str}"
    if effort:
        line1 += f"  ⚡{effort}"
    line1 += f"  \U0001F4C1 {dirname}"
    if branch:
        line1 += f"  \U0001F33F {branch}"

    # --- Line 2: context bar + tokens + elapsed ---
    if pct_raw is not None:
        pct = ceil_pct(pct_raw)
        bar_color = RED if pct >= 90 else YELLOW if pct >= 70 else GREEN
        bar = render_bar(pct_raw)
        tok_str = f"{fmt_tokens(total_input)} / {fmt_window(window_size)}"
        line2 = f"{bar_color}{bar}{RESET} {pct}% ({tok_str})"
    else:
        line2 = f"{DIM}--{RESET}"

    duration_ms = data.get("cost", {}).get("total_duration_ms")
    line2 += f"  ⏱️ {fmt_duration_ms(duration_ms)}"

    # --- Line 3: rate limits (5h / 7d) ---
    rate_parts = []
    rl = data.get("rate_limits", {}) or {}
    five_h = rl.get("five_hour", {}) or {}
    if five_h.get("used_percentage") is not None and five_h.get("resets_at") is not None:
        resets_at = five_h["resets_at"]
        proj = projected_pct(five_h["used_percentage"], resets_at, 5 * 3600, now)
        remaining = max(resets_at - now, 0)
        rate_parts.append(
            f"\U0001F4CA 5h: {ceil_pct(five_h['used_percentage'])}% → {ceil_pct(proj)}%"
            f" ({fmt_reset_time(resets_at)} / {fmt_remaining_full(remaining)})"
        )

    seven_d = rl.get("seven_day", {}) or {}
    if seven_d.get("used_percentage") is not None and seven_d.get("resets_at") is not None:
        resets_at = seven_d["resets_at"]
        proj = projected_pct(seven_d["used_percentage"], resets_at, 7 * 86400, now)
        remaining = max(resets_at - now, 0)
        rate_parts.append(
            f"\U0001F4CA 7d: {ceil_pct(seven_d['used_percentage'])}% → {ceil_pct(proj)}%"
            f" ({fmt_reset_dt(resets_at)} / {fmt_remaining_full(remaining)})"
        )

    # --- Line 4: cache hit rate + cache TTL ---
    cache_parts = []
    cur_usage = ctx.get("current_usage")
    if cur_usage:
        cache_read = cur_usage.get("cache_read_input_tokens") or 0
        cache_create = cur_usage.get("cache_creation_input_tokens") or 0
        fresh_input = cur_usage.get("input_tokens") or 0
        snapshot = [cache_read, cache_create, fresh_input]

        # Only count this as a "new" data point if it differs from the last
        # observed snapshot -- guards against double-counting when the script
        # re-runs on refreshInterval without a new API call having happened.
        if snapshot != state.get("last_snapshot"):
            state["last_snapshot"] = snapshot
            state["cum_read"] = state.get("cum_read", 0) + cache_read
            state["cum_total"] = state.get("cum_total", 0) + cache_read + cache_create + fresh_input
            # Anthropic's prompt cache TTL is refreshed by both reads and
            # writes, so any turn that touched the cache resets the clock.
            if cache_read > 0 or cache_create > 0:
                state["cache_last_touch"] = now

        cum_total = state.get("cum_total", 0)
        if cum_total > 0:
            hit_rate = state.get("cum_read", 0) / cum_total * 100
            cache_parts.append(f"\U0001F3AF {ceil_pct(hit_rate)}%ヒット")

        last_touch = state.get("cache_last_touch")
        if last_touch is not None:
            remaining = 3600 - (now - last_touch)
            if remaining > 1200:
                ttl_color = GREEN
            elif remaining > 300:
                ttl_color = YELLOW
            else:
                ttl_color = RED
            if remaining > 0:
                cache_parts.append(f"{ttl_color}\U0001F550 {fmt_countdown(remaining)}{RESET}")
            else:
                cache_parts.append(f"{RED}\U0001F550 期限切れ{RESET}")

    write_state(session_id, state)

    lines = [line1, line2]
    if rate_parts:
        lines.append("  ".join(rate_parts))
    if cache_parts:
        lines.append("  ".join(cache_parts))

    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"statusline error: {e}", file=sys.stderr)
        sys.exit(1)
