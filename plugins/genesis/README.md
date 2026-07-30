# genesis

Session continuity and verification discipline for long-running projects.

**The plugin ships the machinery. The project ships the content.** Nothing here
knows anything about your repo; everything it reads is a file your repo
optionally provides.

---

## What it does

| Component | Kind | Effect |
|---|---|---|
| `SessionStart` | hook | Injects git state and your durable state files into a fresh or resumed session, marked as overriding conflicting context. In a project with none, names what it looked for and where the write guard is rooted. Adds one line offering `prior-art` while no pass is recorded |
| `PreCompact` | hook | Snapshots the full transcript before compaction, so nothing is only recoverable from a summary |
| `Stop` | hook | Runs your project's own verification gate; a failing gate prevents the turn from ending |
| `PreToolUse` | hook | Denies `Write`/`Edit`/`NotebookEdit` calls whose target is outside the project. Does **not** cover writes made through Bash — see Design notes |
| `/genesis:reconcile` | skill | Verifies status documents against the tree and corrects drift |
| `/genesis:handoff` | skill | Closes a session so the next resumes from disk |
| `/genesis:preregister` | skill | Fixes a decision rule before a measurement runs |
| `/genesis:prior-art` | skill | Checks "this needs inventing" against the field, under a protocol that makes "found nothing" falsifiable |
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

### A project skill and a plugin skill of the same name both stay live

The situation this arises in: you write a skill inside a project as
`.claude/skills/<name>/SKILL.md`, it earns its keep, and you generalise it into
this plugin. **The two copies do not shadow one another.** Both are live. The
project copy owns the bare `<name>`; the plugin's copy is reachable only as
`genesis:<name>`.

That is worse than shadowing would be. Both look correct in the listing,
neither is wrong to invoke, and which protocol you actually run depends on
which name you happen to type — so the fork you meant to replace keeps winning
by default, in the project where you are most likely to be testing the
replacement.

**The check is to start a fresh non-interactive session and read its own skill
listing** — not to restart and assume the new copy took. Verified that way in
FieldGold on 2026-07-29. The remedy is to delete the project copy once the
plugin is installed; there is nothing to configure.

### Releasing

`version` in `plugins/genesis/.claude-plugin/plugin.json` **must be bumped
whenever the shipped plugin content changes — meaning anything under
`plugins/genesis/`.** Claude Code uses that field as the cache key that decides
whether an update is available, and skips the update when it matches what is
installed. Ship a change without bumping it and existing installs keep the old
copy indefinitely — they are never told there is anything to fetch.

**Documentation elsewhere in the repo is not a release.** `STATE.md`, `docs/`,
the root `README.md` and anything else outside `plugins/genesis/` never reach an
install, so a bump for one of those advertises an update whose payload is
nothing. The rule used to say *bump on every release* and never said what a
release was; see Provenance for the bump that exposed the gap.

The line is *shipped content*, and it is checkable rather than a matter of
taste — an install's copy lives at
`~/.claude/plugins/cache/<marketplace>/genesis/<version>/`, so `ls` that
directory to see what a bump would actually deliver. **This README is in
there**, which means a change to it is a release even though it changes no
behaviour.

The failure the rule exists for is silent on both ends, which is what makes it
worth a rule rather than a habit: the author sees a pushed commit and assumes it
landed, the user sees a plugin that works and has no reason to look, and nothing
anywhere reports that the two are different versions of the same thing.

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

That second constraint has **one** exemption, the prior-art line added in 1.0.5.
It was not waived: the test now requires that deleting that single line
reproduces the pinned baseline byte for byte, so the exemption is bounded by an
assertion rather than by whoever remembers it. Anything else that drifts into
every session's context still fails the suite.

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

**Why a research protocol lives in a session-continuity plugin.** `prior-art` is
the odd one out on first read, and a later reader will fairly ask what it is
doing here. The other three skills all keep a claim record honest across
sessions: `reconcile` checks the record against the tree, `preregister` fixes a
decision rule before a result can select its own threshold, `handoff` preserves
the reasoning that compaction destroys. **`prior-art` is the same discipline
pointed outward.** It checks one specific claim — *this needs inventing* —
against the world rather than against the repository, and it does it the way the
others do: by fixing a required shape in advance, so that a comfortable answer
becomes a falsifiable one. "I searched and found nothing" fails in exactly the
manner "the header still says unfinished" fails, and for the same reason —
nothing in the record contradicts it, so nothing prompts a second look.

The alternative was a second plugin. It was rejected because a research-protocol
plugin holding one skill would ship this same argument twice, and would split the
machinery that makes the protocol stick — the durable state where a fetched
citation is recorded, the gate, the verifier agent — across two installs that
have to be kept in step.

**Why the prior-art notice is a line rather than a setting.** A capability
nobody knows about is not available, so `SessionStart` says once per session
that the pass exists — until the project's state records one, after which it
stops. The tempting alternatives were all worse. A toggle or a marker file is a
preference someone has to remember, which is a prompt with extra steps and
leaves the plugin needing to be asked before it works. An unconditional line is
a permanent tax on every session of every project forever.

**What the line claims is exactly what it checks**, which is the part worth
copying. The hook greps the state files it already reads; it cannot know whether
a pass happened, so it says *none recorded in this project's state* rather than
*this project has never checked*. That distinction is what let the check exist
at all — an honest weak signal is available where an accurate one is not, and a
line that overclaims would be wrong in every project that recorded its pass
somewhere else.

It is the skill that makes the signal real: `prior-art` step 4 writes the report
into the durable state, so the thing being detected is a project declaration in
a project file rather than a plugin's guess. That is also the off switch, and it
is one nobody has to be told about — the notice stops when the thing it is
asking for exists. It fires whether or not state files are present, because a
mature project that has never checked the field is the case that most needs it.

**Why the skill description lists mechanisms by name.** It used to say "anything
this project has not built before — a new interaction, a new state model." That
describes nearly every request, and deciding whether something *is* a new state
model is itself the judgment the skill was supposed to remove, so it fired
inconsistently. The description now leads with things a request can be matched
against without interpretation — scheduler, queue, cache, parser, state machine,
diffing algorithm, retry policy, rate limiter — and keeps the abstract category
only as a second clause, calibrated to *a field plausibly has a documented
answer* rather than to novelty. **A check that fires everywhere gets dismissed
everywhere**, and that is measured rather than asserted: one of the projects
this plugin was extracted from had a flat 2000m avoid radius that read seven of
eight clean benches as encumbered. A filter that says yes to almost everything
carries no information, and stops being read.

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
- the prior-art skill, because one project's pass over a single design document
  checked six mechanisms and found prior art for **all six** — every one of them
  hidden behind a name the project had invented for itself. Three turned up
  failure modes the design was about to rediscover, and one supplied a
  correction the design had no way to know it was missing. The searches that
  returned nothing were the ones run against project vocabulary, which is why
  renaming is step 1 of the protocol rather than an aside inside it
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

- the release rule's **scope**, from the first version this repo published with
  nothing in it — 1.0.6, withdrawn, and the withdrawal shipped as 1.0.7. The
  prior-art pass over genesis's own six mechanisms recorded its findings in
  `STATE.md` and `docs/PRIOR-ART.md`, changed no plugin file, and bumped the
  version anyway. Correctly, by the rule as written: it said *bump on every
  release* and never said what a release was.

  **A version that moves without a payload teaches people that the version
  means nothing** — and that is the same failure this README already measures
  one section away, where a filter that read seven of eight clean benches as
  encumbered stopped being read at all. A bump is a signal, and a signal that
  fires when nothing shipped carries no information. The cost is not the wasted
  number; it is that the next bump, the one carrying a fix someone reported, is
  now indistinguishable from a documentation commit.

  **Rolling the number back to 1.0.5 was the obvious repair and it was the
  wrong one.** Mechanically it would have worked: the version is a *cache key
  compared for equality, not an ordering* — an update is skipped only when the
  resolved version matches what is installed — so a lower number is still a
  different key and still applies. What made it wrong is that reusing a key
  requires the content behind it to be unchanged, and the commit that reworded
  this rule **edits this file, which is shipped content.** Verified rather than
  assumed: `README.md` is present in the install cache at
  `~/.claude/plugins/cache/<marketplace>/genesis/<version>/`, byte-identical to
  the commit it was fetched from. A 1.0.5 pointing at a corrected README would
  have been a key resolving to content every existing 1.0.5 install already
  holds a different copy of — and would never be told about, because the key
  matches. That is the 1.0.1 failure again, wearing the costume of a fix.

  So the wasted number stands and the correction ships as 1.0.7. **The rule's
  first application was to the commit that introduced it, and it said bump** —
  which is the cheapest possible demonstration that the scope is drawn in the
  right place.

  What this instance adds to the 1.0.1 story is the other edge of the same
  rule. 1.0.1 established that an unbumped change never reaches anyone. This
  establishes that a bumped non-change reaches everyone for nothing. The rule
  needed a scope, not more force — and the scope is *shipped content*, which is
  a fact about what lands in the cache rather than a judgment about what feels
  like a release.

Apache-2.0.
