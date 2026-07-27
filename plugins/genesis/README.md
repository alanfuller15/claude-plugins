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
| `PreToolUse` | hook | Denies `Write`/`Edit`/`NotebookEdit` calls whose target is outside the project. Does **not** cover writes made through Bash — see Design notes |
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

### If `/reload-plugins` says `0 skills`

It does, and **the skills are fine.** Verify it rather than taking this on
faith: run `/genesis:reconcile`. It resolves and loads normally.

The count includes `commands/*.md` files only; it does not count
`skills/*/SKILL.md`. Tracked as
[anthropics/claude-code#81551](https://github.com/anthropics/claude-code/issues/81551),
filed from this plugin — it is the live issue for the count.

The behaviour was described earlier in
[#41842](https://github.com/anthropics/claude-code/issues/41842), but do not
cite that one as current: it is **closed as a duplicate** of #42471, fixed in
2.1.98, and its headline complaint (that `skills/` plugins are not invocable as
slash commands *at all*) does **not** reproduce. On 2.1.220 the skills resolve
as slash commands and only the count is wrong — which is why #81551 exists
separately rather than as a comment on a fixed bug.

**Do not add a `commands/` directory to fix the count.** It is the workaround
that issue names, and it duplicates every skill's full content into a second
file in order to change a display number. Two copies that must be kept in sync
is a real cost; a wrong count is a cosmetic one. The invocation bugs the
workaround existed for are fixed.

### Releasing

`version` in `plugins/genesis/.claude-plugin/plugin.json` **must be bumped on
every release.** Claude Code compares on that field to decide whether an
install is stale. Ship a change without bumping it and existing installs keep
the old copy indefinitely — they are never told there is anything to fetch.

The failure is silent on both ends, which is what makes it worth a rule rather
than a habit: the author sees a pushed commit and assumes it landed, the user
sees a plugin that works and has no reason to look, and nothing anywhere
reports that the two are different versions of the same thing.

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
context a model may or may not honour. The `Stop` gate is enforcement that does
not depend on careful reading: the turn cannot end while it fails, whatever the
model believes. Anything that must hold regardless belongs here; anything
advisory belongs in `CLAUDE.md`. **That strength is specific to the `Stop`
gate and does not transfer to the write guard** — see the next two notes.

**What the write guard actually covers, stated precisely.** It denies
`Write`, `Edit` and `NotebookEdit` calls whose target path resolves outside the
project directory. **It does not cover writes performed through Bash** — shell
redirection, `sed -i`, `tee`, `python3 -c`, or anything else a command can do.
Those reach the filesystem without passing the hook at all.

So it catches the ACCIDENTAL case, which is the common one: a model reaching
for a path outside the repo because it seemed like the obvious place. It is
**not a sandbox and must not be relied on as one.** If you need a real
boundary, use the harness's own permission modes and directory settings; this
guard is a seatbelt, not a wall.

**Why that gap is left open rather than closed.** Covering Bash would mean
parsing shell to find write targets — redirections, tool-specific in-place
flags, interpreters invoked with inline scripts, anything behind a variable.
That analysis is undecidable in general and wrong often enough in practice to
produce false denials on ordinary commands. A guard that misfires gets
disabled, and a disabled guard catches nothing. **A narrow guard that is
trusted beats a broad one that is not**, so the scope is deliberately the part
that can be checked exactly: a literal path in a known field.

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
- the write guard's own documentation, narrowed by a worked instance during
  this repo's first commit. The guard blocked a legitimate edit to a file in
  this very directory, from a session whose project root was elsewhere. Its
  deny message asks for an explanation to the user rather than a silent retry
  — and writing that explanation is what surfaced the mismatch: the hook
  matches `Write|Edit|NotebookEdit`, Bash was never covered, and this README
  claimed it "denies writes outside the project directory".

  Two things are worth taking from that. The guard firing on a legitimate
  write is the design working, not a false positive to tune away — the block
  is cheap and the explanation it forces is where the error surfaced. And the
  claim was caught by its own machinery rather than by review, which is a
  better argument for the design than the overstated sentence it replaced.

Apache-2.0.
