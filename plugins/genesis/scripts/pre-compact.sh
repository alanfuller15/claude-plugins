#!/usr/bin/env bash
# genesis :: PreCompact
#
# Compaction is lossy and silent: it produces a plausible summary and the
# session continues on a thinner picture. This snapshots the full transcript
# first, so nothing is ever only recoverable from a summary.
#
# Writes to .genesis/backups/ in the project. Add that to .gitignore —
# transcripts can contain anything that was in the conversation.

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

if [ "$TRANSCRIPT" != "-" ] && [ -f "$TRANSCRIPT" ]; then
  cp "$TRANSCRIPT" "$DEST/transcript.jsonl" 2>/dev/null
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
