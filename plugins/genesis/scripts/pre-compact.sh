#!/usr/bin/env bash
# genesis :: PreCompact
#
# Compaction is lossy and silent: it produces a plausible summary and the
# session continues on a thinner picture. This snapshots the full transcript
# first, so nothing is ever only recoverable from a summary.
#
# Writes to .genesis/backups/ in the project. Add that to .gitignore —
# transcripts can contain anything that was in the conversation.
#
# WHAT BLOCKS, AND WHY ONLY THAT. Exit 2 from a PreCompact hook blocks
# compaction. Until 1.0.8 this script never used that: every failure path was
# exit 0, so a snapshot could fail and the summary would proceed as the only
# record — the exact loss the hook exists to prevent, occurring silently.
#
# It now blocks in ONE case: a transcript existed and copying it failed. That is
# the write-ahead rule this hook is an instance of — do not perform the lossy
# operation until the log is durable.
#
# Everything else still proceeds, deliberately:
#
#   - mkdir failure, at either level. Blocking here would turn an unwritable
#     .genesis/ into a session that can never compact.
#   - no transcript_path in the payload, or a path that does not exist. Nothing
#     was lost, so there is nothing to protect.
#   - a malformed payload. Failing open is the same choice guard-writes.sh makes
#     for a missing python3.
#   - the durable-state, HEAD and dirty-tree extras below. They are context for
#     a later reader, not the irreplaceable artifact.
#
# The narrowness is the design, not timidity. A hook that blocked on any failure
# would, on a full disk, give you a session that cannot compact at all — and the
# lean-manufacturing version of this mechanism is a TIME-BOXED escalation, not an
# indefinite halt (see the andon note in README.md). Since this hook has no
# time-box available to it, the scope is kept to the one case where the thing
# being protected is genuinely already gone, and the message carries the way out.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0

BACKUP_DIR=".genesis/backups"
mkdir -p "$BACKUP_DIR" || exit 0

INPUT=$(cat)

read -r TRANSCRIPT TRIGGER <<<"$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(" unknown"); raise SystemExit
print(d.get("transcript_path", "") or "-", d.get("trigger", "unknown"))
' 2>/dev/null || echo "- unknown")"

STAMP=$(date +%Y%m%d-%H%M%S)
DEST="$BACKUP_DIR/$STAMP-$TRIGGER"
mkdir -p "$DEST" || exit 0

# The one blocking path. cp's exit status is CHECKED rather than discarded, and
# its stderr is captured for the message instead of being sent to /dev/null —
# "cp said" is the line that tells the reader whether this is a full disk, a
# permission problem, or something else.
if [ "$TRANSCRIPT" != "-" ] && [ -f "$TRANSCRIPT" ]; then
  if ! CP_ERR=$(cp "$TRANSCRIPT" "$DEST/transcript.jsonl" 2>&1); then
    {
      echo "genesis: COMPACTION BLOCKED — the transcript snapshot failed."
      echo
      echo "A full copy of this session's transcript was expected at"
      echo "  $DEST/transcript.jsonl"
      echo "and the copy did not succeed. Compaction is lossy, so allowing it now"
      echo "would leave the summary as the only record of this session."
      echo
      echo "  transcript:   $TRANSCRIPT"
      echo "  destination:  $DEST/transcript.jsonl"
      echo "  cp said:      ${CP_ERR:-(no error text)}"
      echo
      echo "Fix the cause and compact again — most often free disk space, or write"
      echo "permission on .genesis/backups."
      echo
      echo "THERE IS NO SKIP FILE FOR THE SNAPSHOT. .genesis/skip-verify turns off"
      echo "the verification gate only; it is not read here. If the cause cannot be"
      echo "fixed and losing this transcript is acceptable, disabling the plugin"
      echo "(/plugin disable genesis) removes the hook and lets compaction proceed."
    } >&2
    exit 2
  fi
fi

# Snapshot the durable state alongside it, so the pair can be compared later.
for f in STATE.md docs/STATE.md HANDOFF.md docs/HANDOFF.md; do
  [ -f "$f" ] && cp "$f" "$DEST/$(echo "$f" | tr '/' '_')" 2>/dev/null
done

if git rev-parse --git-dir >/dev/null 2>&1; then
  git rev-parse HEAD >"$DEST/head.txt" 2>/dev/null
  git status --short >"$DEST/dirty.txt" 2>/dev/null
fi

# Retain the 20 most recent snapshots.
ls -1dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +21 | xargs -r rm -rf 2>/dev/null

exit 0
