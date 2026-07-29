# genesis

Session continuity and verification discipline for long-running projects.

**The plugin ships the machinery. The project ships the content.** Nothing here
knows anything about your repo; everything it reads is a file your repo
optionally provides.

---

## What it does

| Component | Kind | Effect |
|---|---|---|
| `SessionStart` | hook | Injects git state and your durable state files into a fresh or resumed session, marked as overriding conflicting context. In a project with none, names what it looked for and where the write guard is rooted |
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

**Platforms.** macOS and Linux are what it is developed and tested on. Windows
is supported through Git Bash/MSYS as of **1.0.1** — before that the write
guard denied every write there (see Provenance). The Windows path handling is
covered by tests that run anywhere, but the MSYS environment itself is verified
by hand; if something looks wrong on Windows, it is worth reporting rather than
assuming it is your setup.

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

**1.0.1 is the release that made this concrete rather than hypothetical.** The
rule was written against an imagined stale install; the first real one was a
user running a build of the write guard that denied every write on his
platform. Without the bump he would have kept it — a pushed fix he could not
receive, for a bug he had already reported. A rule that had only ever been
argued for was, on its first live test, the difference between a fix shipping
and a fix existing.

### Tests

```
for t in plugins/genesis/tests/test_*.py; do python3 "$t"; done
```

`test_guard_writes.py` covers the write guard: POSIX behaviour end-to-end
against the real hook, the denial message's three `git:` states and two root
sources, and the path comparison under Windows semantics via `ntpath`, which
runs on any platform. Read its module docstring before extending it — it is
specific about which part of the Windows fix the suite does **not** cover, and
why adding a test that appeared to cover it would be worse than leaving the gap
visible.

`test_session_start.py` covers the first-run block, including its two hard
constraints: at most four lines, and byte-identical output to the previous
version whenever a state file exists. The second is checked by running the
previously committed script side by side rather than against a stored snapshot,
which would drift with the file it is meant to pin.

---

## Per-project setup

All of it is optional. With none of it, the plugin injects git state and
guards writes — useful, and free.

With none of it, `SessionStart` also spends up to four lines saying so: which
state files it looked for, that no gate exists, and **where the write guard is
rooted.** That last line is the one to read. The root is `CLAUDE_PROJECT_DIR`,
or the directory the session was launched in if that is unset — so launching
one level too high silently makes "the project" your home folder, and you would
otherwise not discover it until something was blocked. Those lines disappear
entirely once a state file exists.

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

**What a denial says, and why it says that much.** As of 1.0.2 a denial names
the root, the source that produced it, and whether that root is a repository:

```
  project root:  C:\Users\marke
  root from:     current directory at session start (CLAUDE_PROJECT_DIR not set)
  git:           no repository at this root
```

The criterion it was built to: **a reader with nothing but the message can
decide whether the root is the one they meant.** Naming the root alone does not
allow that — "outside `C:\Users\marke`" is equally consistent with a correct
root and with a session launched one directory too high, and the second is both
the common mistake and the invisible one. The source line says which lever
changes it. The `git:` line has a third state, `inside repository <toplevel>`,
which is the one that catches a root aimed at a subdirectory of a real project
— more frequent than the no-repo case, and indistinguishable from a correct
denial before this existed.

**The guard fires even when the root is not a repository**, and that is a
decision rather than an oversight. The alternative — go quiet with no repo —
removes the guard exactly where accidental writes are most likely: scratch
directories, folders of notes, one-off scripts, where "somewhere else on disk"
is the plausible mistake. It also removes it *silently*, so a user who
installed a write guard has none and no way to notice. A guard that fires with
a good explanation is a smaller surprise than a guard that is not there.

**Why that gap is left open rather than closed.** Covering Bash would mean
parsing shell to find write targets — redirections, tool-specific in-place
flags, interpreters invoked with inline scripts, anything behind a variable.
That analysis is undecidable in general and wrong often enough in practice to
produce false denials on ordinary commands. A guard that misfires gets
disabled, and a disabled guard catches nothing. **A narrow guard that is
trusted beats a broad one that is not**, so the scope is deliberately the part
that can be checked exactly: a literal path in a known field.

**Why the write guard normalises paths through `cygpath` on Windows.** Under
Git Bash/MSYS the environment gives POSIX-style paths — `$PWD`, `$HOME` and
`CLAUDE_PROJECT_DIR` all arrive as `/c/Users/name` — while the tool reports the
write target as a native path, `C:\Users\name\project\file.md`. Windows Python
does not reject the POSIX form: `os.path.realpath("/c/Users/name")` returns
`C:\c\Users\name` and raises nothing. So the root and the target never shared a
prefix, no in-project path ever matched, and **the guard denied every write on
Windows.** Not a degraded check — an inverted one.

The fix has three parts, and each is doing separate work. Paths go through
`cygpath -w` before Python sees them, because MSYS's own translation is the
only thing that gets root mappings and drive mounts right, and because MSYS
argv translation is not a substitute — it rewrites arguments on the way into a
native binary but not the environment variables this script reads, which is
precisely the asymmetry that caused the bug. Target and root are then resolved
in a **single** Python invocation by the same function, with
`os.path.normcase`, so there is no seam where the two sides can diverge again.
And where `cygpath` is absent the value passes through untouched, so macOS and
Linux behaviour is unchanged — verified by running the pre-fix suite against
both builds.

The general lesson is worth more than the fix: the failure was not that the
comparison was wrong, but that **the two sides of it were normalised by
different code paths.** One invocation for both operands is the structural
version of that fix, and it is why the patch consolidates rather than adding a
second special case.

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

- the write guard's Windows path handling, and the test suite around it, from
  **the first external bug report this plugin received** — v1.0.1, from the
  first person to install it who was not its author.

  **The guard had never been run on Windows before 1.0.0 shipped.** It was
  written on macOS, reasoned about on macOS, and documented as though the
  platform question had been settled rather than never asked. What shipped was
  not a guard that worked less well on Windows; it was a guard that denied
  every write on Windows, and would have looked to a new user like a plugin
  that simply does not work.

  Worth recording precisely because of how the bug hid. `os.path.realpath` on
  a POSIX-style path under Windows Python does not fail, does not warn, and
  returns a plausible-looking string — `/c/Users/name` becomes
  `C:\c\Users\name`. Every individual step succeeded. Nothing in the design
  reasoning was wrong; the untested assumption was that a path is a path. The
  cost of "obviously portable, no need to check" is only ever paid by someone
  else, and here that someone was a first-time user whose first experience of
  the plugin was it refusing to let the model write anything at all.

  It also fixed the tests, which is the larger repair. 1.0.0 had none — the
  guard's correctness rested entirely on reading it. The suite added in 1.0.1
  covers Windows path comparison on any platform via `ntpath`, which means the
  class of bug that required an external user to find is now caught on the
  author's own machine.

- the denial message and the first-run lines, from the same install's first
  hour — v1.0.2. The experience was: installed something, nothing happened,
  then it blocked me. Every no-op on the way there was correct behaviour.
  `SessionStart` had no state files to inject, `reconcile` had nothing to
  reconcile, the gate had no `verify.sh` to run. Correct, and illegible.

  **The brief for this work was built on a denial that was not current
  behaviour, and correcting that changed what got built.** The blocked write
  cited as motivation — `C:\Users\marke\alan\blackjack.py` refused against root
  `C:\Users\marke` — is a path *inside* that root. It was denied only because
  of the 1.0.1 Windows bug, and on any fixed version it is allowed. Building
  from the brief as written would have meant tuning a guard that was no longer
  misfiring.

  What survived the correction is a better problem than the one reported.
  The failure is not that the guard denied something it should have allowed;
  it is that **a CORRECT denial does not tell you whether the root it is
  defending is the one you meant.** On that user's setup the root really was
  his entire home directory, inherited from wherever he happened to launch, and
  nothing anywhere said so. The next denial he hits will be correct behaviour
  against a root he never chose — and the message, before 1.0.2, gave him
  nothing to notice that with.

  The general form is worth keeping: a bug report describes the moment someone
  noticed, which is not always the moment something broke. Here the noticing
  was a real defect and the fix for it had already shipped, while the thing
  worth building sat one question behind it. Checking the reported symptom
  against current behaviour before designing from it cost one paragraph and
  changed the whole scope.

Apache-2.0.
