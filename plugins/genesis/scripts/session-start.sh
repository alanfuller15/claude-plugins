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

# Duplicated from guard-writes.sh, where the reasoning lives. Seven lines of
# copy beats a sourced sibling: this runs on every session start, and a shared
# file would add a path-resolution failure mode to the one hook that must never
# fail. The plugin already keeps each hook self-contained for this reason.
to_native() {
  [ -n "${1:-}" ] || return 0
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1" 2>/dev/null || printf '%s' "$1"
  else
    printf '%s' "$1"
  fi
}

# --- git state -------------------------------------------------------------
GIT_TOP=$(git rev-parse --show-toplevel 2>/dev/null || true)

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

# --- first-run orientation -------------------------------------------------
#
# ONLY when no state file was found. A project that has state gets output that
# is byte-identical to what it got before this block existed — this text enters
# context every session and that cost is real.
#
# The problem it addresses: with nothing configured, this hook emitted git
# state and stopped, which reads as "installed something, nothing happened".
# Every no-op was correct; none of them was legible. Naming what was looked for
# turns an absent feature into an available one.
#
# The last line is the one that matters most, and it is not about setup at all.
# It puts the write guard's root in front of the user BEFORE a denial can
# surprise them with it — the same reasoning as the denial message itself,
# applied earlier. A root inherited from wherever the session happened to be
# launched is the failure mode, and it is invisible until something is blocked.
#
# Four lines is the ceiling. Anything that does not survive that limit does not
# belong here.
if [ "$FOUND" = "0" ]; then
  echo "## genesis"
  echo "state: no STATE.md, docs/STATE.md, HANDOFF.md or docs/HANDOFF.md — create one and it is injected here every session"
  [ -f ".claude/verify.sh" ] || \
    echo "gate: no .claude/verify.sh — create one and a turn cannot end while it fails"

  ROOT_DISPLAY=$(to_native "$PWD")
  if [ -z "$GIT_TOP" ]; then
    echo "write guard active; project root is $ROOT_DISPLAY (no git repository here)"
  elif [ "$(to_native "$GIT_TOP")" = "$ROOT_DISPLAY" ]; then
    echo "write guard active; project root is $ROOT_DISPLAY (git repository root)"
  else
    echo "write guard active; project root is $ROOT_DISPLAY (inside repository $(to_native "$GIT_TOP"))"
  fi
  echo
fi

exit 0
