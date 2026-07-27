#!/usr/bin/env bash
# genesis :: PreToolUse (Write|Edit|NotebookEdit)
#
# Denies Write, Edit and NotebookEdit calls whose target path resolves outside
# the project directory.
#
# WHAT THIS DOES NOT COVER: writes performed through Bash. Shell redirection,
# sed -i, tee, python3 -c, and anything else a command can do reach the
# filesystem without passing this hook at all, because the matcher in
# hooks.json is Write|Edit|NotebookEdit and Bash is not in it.
#
# So this catches the ACCIDENTAL case, which is the common one: reaching for a
# path outside the repo because it looked like the obvious place. It is a speed
# bump, NOT A SANDBOX, and must not be relied on as one. For a real boundary,
# use the harness's own permission modes and directory settings.
#
# WHY THE GAP IS LEFT OPEN rather than closed: covering Bash would mean parsing
# shell to find write targets — redirections, in-place flags, interpreters with
# inline scripts, anything behind a variable. Undecidable in general, and wrong
# often enough in practice to deny ordinary commands. A guard that misfires
# gets disabled, and a disabled guard catches nothing. A narrow guard that is
# trusted beats a broad one that is not, so the scope stays at the part that
# can be checked exactly: a literal path in a known field.
#
# This is a hook rather than a line in CLAUDE.md deliberately. A convention in
# context is something a model may or may not honour; a PreToolUse hook fires
# whether or not the model read carefully. That is a real gain over a
# convention, and it is bounded by the matcher above — not the same thing as
# the Stop gate, which the turn genuinely cannot end around.
#
# Scope is narrow on purpose in the other axis too: it does not police WHAT you
# write, only WHERE. Anything inside the project is allowed. Anything outside
# is denied with a reason the model can act on.

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
