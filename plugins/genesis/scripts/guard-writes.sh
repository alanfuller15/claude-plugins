#!/usr/bin/env bash
# genesis :: PreToolUse (Write|Edit|NotebookEdit)
#
# Denies writes outside the project directory.
#
# This is a hook rather than a line in CLAUDE.md deliberately. A convention in
# context is something a model may or may not honour; a PreToolUse hook is
# enforcement that does not depend on the model reading carefully.
#
# Scope is narrow on purpose: it does not police WHAT you write, only WHERE.
# Anything inside the project is allowed. Anything outside is denied with a
# reason the model can act on.

set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-$PWD}"
INPUT=$(cat)

TARGET=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("notebook_path") or "")
' 2>/dev/null || echo "")

# No path to check — stay silent. Silence is not approval; the normal
# permission flow still applies.
[ -n "$TARGET" ] || exit 0

# Resolve without requiring the file to exist yet.
ABS=$(python3 -c '
import os, sys
print(os.path.realpath(os.path.abspath(sys.argv[1])))
' "$TARGET" 2>/dev/null || echo "$TARGET")

ROOT=$(python3 -c '
import os, sys
print(os.path.realpath(os.path.abspath(sys.argv[1])))
' "$PROJECT" 2>/dev/null || echo "$PROJECT")

case "$ABS" in
  "$ROOT"|"$ROOT"/*)
    exit 0
    ;;
esac

# Allow the user's own Claude config — skills and settings live there.
case "$ABS" in
  "$HOME"/.claude/*)
    exit 0
    ;;
esac

python3 - "$ABS" "$ROOT" <<'PY'
import json, sys
target, root = sys.argv[1], sys.argv[2]
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"Write blocked: {target} is outside the project directory ({root}). "
            "genesis denies writes outside the project. If this file genuinely "
            "belongs outside the repo, tell the user what you need to write and "
            "why, and let them do it."
        ),
    }
}))
PY

exit 0
