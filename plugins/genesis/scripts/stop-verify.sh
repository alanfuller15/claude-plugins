#!/usr/bin/env bash
# genesis :: Stop
#
# Runs the project's own verification gate when the turn ends. Exit 2 prevents
# the turn from ending and feeds stderr back, so a session cannot finish on a
# red tree.
#
# CONVENTION, and the reason this is portable: the project declares its own
# gate at .claude/verify.sh. This plugin has no idea what "verified" means for
# your repo and does not guess. No verify.sh, no gate — silent, exit 0.
#
# The gate only runs when the turn actually changed something. A conversational
# turn that edited nothing does not pay for a test run.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0

GATE=".claude/verify.sh"
[ -x "$GATE" ] || [ -f "$GATE" ] || exit 0

# Only gate turns that touched the working tree. Skip when nothing changed.
if git rev-parse --git-dir >/dev/null 2>&1; then
  if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    exit 0
  fi
fi

# Opt-out for a turn that is deliberately mid-refactor.
if [ -f ".genesis/skip-verify" ]; then
  echo "genesis: verification skipped (.genesis/skip-verify present)" >&2
  exit 0
fi

OUT=$(bash "$GATE" 2>&1)
RC=$?

if [ "$RC" -ne 0 ]; then
  {
    echo "VERIFICATION GATE FAILED (.claude/verify.sh exited $RC)."
    echo "The working tree is modified and the project's own gate does not pass."
    echo "Fix it, or state explicitly why the tree should be left red, before ending the turn."
    echo
    echo "$OUT" | tail -40
  } >&2
  exit 2
fi

exit 0
