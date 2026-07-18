#!/usr/bin/env python3
import json
import sys

data = json.load(sys.stdin)
subagent_type = data.get("tool_input", {}).get("subagent_type")

if subagent_type == "general-purpose":
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "general-purpose agent is blocked by local policy",
        }
    }))
else:
    print(json.dumps({}))
