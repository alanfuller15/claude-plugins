#!/usr/bin/env bash
# The verification gate for this repo.
#
# Run by genesis's own Stop hook (plugins/genesis/scripts/stop-verify.sh) on
# any turn that left the working tree dirty; a non-zero exit prevents the turn
# from ending. Also runnable by hand from anywhere: bash .claude/verify.sh
#
# This repo had no gate until 1.0.1, while shipping a plugin whose central
# claim is that a project should declare one. That gap was not free: the
# Windows bug in the write guard reached a user because nothing here ran the
# guard against anything before it shipped.
#
# WHAT BELONGS IN HERE: checks that are fast, deterministic, and that fail only
# for reasons the turn can actually fix. This runs on every dirty turn, so a
# check that misfires trains the author to reach for .genesis/skip-verify, and
# a gate that is habitually skipped is not a gate. That is the same argument
# the write guard's own scope rests on.
#
# WHAT IS DELIBERATELY NOT IN HERE: a check that the plugin version was bumped.
# The release rule matters — it is why 1.0.1 reached the user who reported the
# bug — but the bump correctly comes last, so a gate enforcing it would fail
# every turn of the work leading up to it. Enforcing it here would fail for a
# reason the turn cannot yet fix, which is the misfire described above. It
# belongs at release time, where `claude plugin tag` already checks it.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

FAILED=0

# Run every check even after one fails. A gate that stops at the first error
# hides the rest, and re-running to discover them one at a time is slower than
# the whole suite.
step() {
  local name="$1"; shift
  local out rc
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then
    printf '  ok    %s\n' "$name"
  else
    printf '  FAIL  %s (exit %d)\n' "$name" "$rc"
    printf '%s\n' "$out" | sed 's/^/        /'
    FAILED=1
  fi
}

# 1. Hook scripts must parse. These run in every session of every install, so a
#    syntax error here is the highest-consequence breakage this repo can ship,
#    and it costs milliseconds to rule out.
check_hook_syntax() {
  local rc=0
  for f in plugins/genesis/scripts/*.sh .claude/verify.sh; do
    bash -n "$f" || rc=1
  done
  return $rc
}
step "hook scripts parse" check_hook_syntax

# 2. Manifests must validate. Skipped rather than failed where the CLI is
#    absent, so this is runnable outside a machine with Claude Code installed.
if command -v claude >/dev/null 2>&1; then
  step "marketplace manifest" claude plugin validate .
  step "plugin manifest" claude plugin validate ./plugins/genesis
else
  printf '  skip  manifest validation (claude CLI not on PATH)\n'
fi

# 3. Hook behaviour. Every suite under tests/, discovered rather than listed, so
#    a new one is gated the moment it exists instead of the moment someone
#    remembers to add it here. Each module's docstring states what it does and
#    does not establish — the guard's in particular is specific about which part
#    of the Windows fix no test on this platform can cover.
for suite in plugins/genesis/tests/test_*.py; do
  step "$(basename "$suite" .py)" python3 "$suite"
done

if [ "$FAILED" -ne 0 ]; then
  echo "verify: FAILED"
  exit 1
fi

echo "verify: ok"
exit 0
