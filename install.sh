#!/bin/bash
# Merge dotfiles/settings.json into ~/.claude/settings.json and link statusline.py.
# Safe to re-run. Does NOT touch the plugin itself (install that via
# `/plugin marketplace add <this repo path>` inside Claude Code, see README.md).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

mkdir -p "$CLAUDE_DIR"

echo "== statusline.py =="
cp "$REPO_DIR/dotfiles/statusline.py" "$CLAUDE_DIR/statusline.py"
chmod +x "$CLAUDE_DIR/statusline.py"
echo "コピーしました: $CLAUDE_DIR/statusline.py"

echo "== settings.json =="
TARGET="$CLAUDE_DIR/settings.json"
if [ -f "$TARGET" ]; then
  BACKUP="$TARGET.bak.$(date +%s)"
  cp "$TARGET" "$BACKUP"
  echo "既存設定をバックアップ: $BACKUP"
fi

python3 - "$REPO_DIR/dotfiles/settings.json" "$TARGET" <<'PYEOF'
import json, sys, os

src_path, dst_path = sys.argv[1], sys.argv[2]

def deep_merge(base, overlay):
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base

with open(src_path) as f:
    overlay = json.load(f)

if os.path.exists(dst_path):
    with open(dst_path) as f:
        base = json.load(f)
else:
    base = {}

merged = deep_merge(base, overlay)

with open(dst_path, "w") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF

echo "マージ完了: $TARGET"
echo
echo "注意: permissions.defaultMode=bypassPermissions と skipDangerousModePermissionPrompt=true が入ります。"
echo "      権限プロンプトを全て自動許可する設定です。意図しない場合はこの2つを settings.json から削除してください。"
