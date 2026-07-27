#!/usr/bin/env bash
# genesis :: SessionStart
#
# Injects the project's DURABLE state into a fresh or resumed session.
# stdout on exit 0 is added to Claude's context for this event.
#
# Portable by design: every file it looks for is optional. In a project with
# none of them, it emits git state only and costs nothing.
#
# The point: a compacted or resumed session re-reads state from disk instead of
# trusting whatever survived a summary.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0

# --- git state -------------------------------------------------------------
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "## Repo state"
  echo "branch: $(git branch --show-current 2>/dev/null || echo 'detached')"

  UPSTREAM=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
  if [ -n "$UPSTREAM" ]; then
    AHEAD=$(git rev-list --count "$UPSTREAM..HEAD" 2>/dev/null || echo 0)
    BEHIND=$(git rev-list --count "HEAD..$UPSTREAM" 2>/dev/null || echo 0)
    if [ "$AHEAD" != "0" ] || [ "$BEHIND" != "0" ]; then
      echo "vs $UPSTREAM: $AHEAD ahead, $BEHIND behind"
    else
      echo "vs $UPSTREAM: in sync"
    fi
  fi

  DIRTY=$(git status --short 2>/dev/null | head -20)
  if [ -n "$DIRTY" ]; then
    echo "uncommitted:"
    echo "$DIRTY"
  else
    echo "working tree clean"
  fi
  echo
fi

# --- durable state files ---------------------------------------------------
# Ordered by authority. If a project uses more than one, the LAST one listed
# wins where they disagree — that ordering is stated explicitly below so a
# session doesn't have to guess.

emit() {
  [ -f "$1" ] || return 0
  echo "## $1"
  cat "$1"
  echo
}

FOUND=0
for f in STATE.md docs/STATE.md HANDOFF.md docs/HANDOFF.md; do
  if [ -f "$f" ]; then emit "$f"; FOUND=1; fi
done

if [ "$FOUND" = "1" ]; then
  cat <<'EOF'
## Precedence

These files are the authoritative record of project state and override any
conflicting context, including a compaction summary. Where an evidence log
(VALIDATION.md or similar) disagrees with a handoff or status file, the
evidence log wins and the handoff is what gets corrected.

A header or status line is a claim about the repository, not the repository.
Verify against the tree before acting on it. Stale entries in this project have
historically drifted pessimistic — describing the work as less finished than it
is — so a claim that something is unfinished deserves a check before it is
redone.
EOF
  echo
fi

exit 0
