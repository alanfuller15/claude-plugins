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
# permission flow still applies. Same if python3 is missing entirely: this
# guard fails open, because a hook that denies everything when a dependency is
# absent is worse than one that denies nothing.
[ -n "$TARGET" ] || exit 0

# --- Windows/MSYS path normalisation -----------------------------------------
#
# On Windows under Git Bash/MSYS, $PWD, $HOME and CLAUDE_PROJECT_DIR are
# POSIX-style (/c/Users/marke) while the tool reports the target as a native
# path (C:\Users\marke\project\file.md). Windows Python does not reject the
# POSIX form — os.path.realpath("/c/Users/marke") returns "C:\c\Users\marke"
# without error — so the project root and the target never share a prefix, no
# in-project path ever matches, and EVERY write is denied. The guard was
# unusable on Windows until 1.0.1.
#
# cygpath ships with Git for Windows and is the translation MSYS itself uses,
# so it is the right authority here rather than a hand-rolled /c/ → C:\ rewrite
# (which would get MSYS root mappings, UNC paths and drive mounts wrong).
# Relying on MSYS argv translation instead is not an option: it rewrites
# arguments that look like paths on the way into a native binary, but not the
# environment variables this script reads, so the two sides would still be
# normalised differently.
#
# Where cygpath is absent — macOS, Linux — the value passes through untouched
# and behaviour is identical to before.
to_native() {
  [ -n "${1:-}" ] || return 0
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1" 2>/dev/null || printf '%s' "$1"
  else
    printf '%s' "$1"
  fi
}

TARGET_N=$(to_native "$TARGET")
PROJECT_N=$(to_native "$PROJECT")
HOME_N=$(to_native "${HOME:-}")

# Target and root are resolved in ONE python invocation, by the same function,
# so both sides go through identical logic. Two invocations invite exactly the
# asymmetry the Windows bug was made of. os.path.normcase folds case and
# separators on Windows and is the identity on POSIX, so one comparison is
# correct on both.
#
# NOTE: tests/test_guard_writes.py extracts the snippet between the PY_PATHCHECK
# markers and runs it under ntpath to exercise the Windows comparison on any
# platform. Keep it self-contained, and keep it addressing the path flavour
# through os.path.* (including os.path.sep) rather than os.sep.
python3 - "$TARGET_N" "$PROJECT_N" "$HOME_N" <<'PY_PATHCHECK'
import json, os, sys


def resolve(p):
    return os.path.realpath(os.path.abspath(p))


def contains(root, target):
    """True if target is root itself or lies beneath it."""
    root_n = os.path.normcase(root)
    target_n = os.path.normcase(target)
    if target_n == root_n:
        return True
    return target_n.startswith(root_n.rstrip(os.path.sep) + os.path.sep)


target = resolve(sys.argv[1])
root = resolve(sys.argv[2])
home = sys.argv[3]

if contains(root, target):
    raise SystemExit(0)

# Allow the user's own Claude config — skills and settings live there.
if home and contains(resolve(os.path.join(home, ".claude")), target):
    raise SystemExit(0)

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
PY_PATHCHECK

exit 0
