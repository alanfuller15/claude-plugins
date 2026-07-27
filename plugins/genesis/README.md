# genesis

Session continuity and verification discipline for long-running projects.

**The plugin ships the machinery. The project ships the content.** Nothing here
knows anything about your repo; everything it reads is a file your repo
optionally provides.

---

## What it does

| Component | Kind | Effect |
|---|---|---|
| `SessionStart` | hook | Injects git state and your durable state files into a fresh or resumed session, marked as overriding conflicting context |
| `PreCompact` | hook | Snapshots the full transcript before compaction, so nothing is only recoverable from a summary |
| `Stop` | hook | Runs your project's own verification gate; a failing gate prevents the turn from ending |
| `PreToolUse` | hook | Denies writes outside the project directory |
| `/genesis:reconcile` | skill | Verifies status documents against the tree and corrects drift |
| `/genesis:handoff` | skill | Closes a session so the next resumes from disk |
| `/genesis:preregister` | skill | Fixes a decision rule before a measurement runs |
| `verifier` | agent | Read-only verification sweep in an isolated context |

---

## Install

```
/plugin marketplace add alanfuller15/claude-plugins
/plugin install genesis@alanfuller15-tools
/reload-plugins
```

Local development:

```
/plugin marketplace add ./claude-plugins
/plugin install genesis@alanfuller15-tools
```

Or load without installing: `claude --plugin-dir ./claude-plugins/plugins/genesis`

---

## Per-project setup

All of it is optional. With none of it, the plugin injects git state and
guards writes — useful, and free.

### 1. Durable state (recommended)

Create any of `STATE.md`, `docs/STATE.md`, `HANDOFF.md`, `docs/HANDOFF.md`.
Whatever exists is injected at session start. Keep them short — this is read
every session.

The convention worth adopting: **an evidence log outranks a handoff.** Record
measurements with their bounds in one file; keep working state in the other.
Where they disagree, the evidence log wins and the handoff is corrected.

### 2. The verification gate

Create `.claude/verify.sh`. It runs on turn end **only when the working tree is
dirty**, and a non-zero exit prevents the turn from ending.

```bash
#!/usr/bin/env bash
set -e
python3 examples/fixtures/verify_cross_tool_key.py
python3 examples/fixtures/verify_dedup_render.py
```

Keep it fast — it runs on every turn that changed something. If it takes
minutes, gate a subset here and run the full suite deliberately.

To skip it during a deliberate mid-refactor: `touch .genesis/skip-verify`.
Delete the file when done. It announces itself in the transcript each time, so
it will not be forgotten silently.

### 3. Ignore the snapshots

```
echo '.genesis/' >> .gitignore
```

Transcripts can contain anything that was in the conversation. They are local
recovery, not project history.

---

## Design notes

**Why the gate is a hook rather than a convention.** A rule in `CLAUDE.md` is
context a model may or may not honour. A `Stop` hook is enforcement that does
not depend on careful reading. Anything that must hold regardless belongs here;
anything advisory belongs in `CLAUDE.md`.

**Why the write guard only checks location.** It does not police what you
write, only where. Narrow scope means it fires rarely and is trusted when it
does. A guard that cries wolf gets disabled.

**Why the plugin does not define "verified."** It cannot know. Projects declare
their own gate at a known path; the plugin runs it and reports. That is what
makes this portable across a Python research repo and a static web app without
modification.

**Why state precedence is stated in the injected text.** A compacted session
inherits a summary and a set of files, and needs to know which wins. Saying so
explicitly costs three lines and prevents a class of error where a summary's
paraphrase quietly overrides a measurement.

---

## Provenance

Extracted from two projects after a workflow audit. Every component exists
because its absence cost something real:

- the compaction snapshot, because a summary silently thinned a session's
  picture of its own state
- the state injection, because two sessions redid work that had already landed
- the reconciliation skill, because stale headers drifted pessimistic four
  separate times, once propagating into a public document
- the pre-registration skill, because a signal excluded in advance came back at
  74% against an 18.75% result — and only the advance exclusion made the 18.75%
  credible
- the verifier agent, because verification is high-volume input and low-volume
  output, which is exactly what an isolated context is for

Apache-2.0.
