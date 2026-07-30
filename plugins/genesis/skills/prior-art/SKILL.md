---
name: prior-art
description: Search for prior art before designing a mechanism, under a protocol that makes "I found nothing" a checkable claim. Use when about to design a scheduler, queue, cache, parser, state machine, diffing algorithm, sync mechanism, retry policy, permissions model, undo system, plugin architecture, or rate limiter — or any comparable mechanism where a field plausibly already has a documented answer, including its failure modes. Requires two mechanically different searches, both recorded verbatim, and reports in a fixed shape. Not for bug fixes, rewordings, or work already grounded in a source that has been cited and fetched.
---

# Check the field before designing it

"Look for prior art" is not an instruction that can be checked — it has no
shape, so it cannot be done wrong. This skill gives it one, so that **"I
searched and found nothing" becomes a claim that can be false rather than a
sentence that ends an inquiry.**

## Why this is worth a dedicated pass

The other passes in this plugin check a claim record against the repository.
This one checks a claim against the world: the claim that **the thing needs
inventing.**

It earns a pass because the failure is invisible from inside. A design invents a
vocabulary, searches for that vocabulary, finds nothing, and records "no prior
art" — while the field that has studied the problem for thirty years calls it
something else and has already written down the failure modes the design is
about to rediscover in production. Nothing in that sequence looks like an error.
The search was real, the result was reported honestly, and the answer was wrong.

**When it applies.** Before designing any mechanism this project has not built
before. **Not** for a bug fix, not for a rewording, not for work already
grounded — if a source is already cited *and fetched* in a design document or in
the durable state, it does not get re-searched.

Four steps. **The third is mandatory and is the one that does the work.**

## Procedure

### 1. Rename the thing in field vocabulary, not project vocabulary

**This step decides whether the search can succeed at all**, which is why it is
step one and not preamble. A project's own name for something finds nothing,
because the field that studied it does not call it that — and projects generate
private vocabulary freely, without noticing they have done it.

Write both, explicitly:

- **what we call it**
- **what someone who studies this class of thing would call it**

If you cannot produce the second, **say so, and make the name itself the first
search.** "What is this called" is a legitimate query and is often the only one
that matters. A search that returns a *name* has succeeded even if it returns
nothing else.

### 2. First search — does this already exist, and what is it called

Search the field's name for it, not the project's.

**Not "how to build X."** That returns tutorials, which are the least useful
tier and crowd out everything above them. Use the forms that return the studied
version: "what is X", "X pattern", "X standard", "X convention", "X guideline".

**Record the query verbatim**, not a paraphrase of it. A paraphrase cannot be
re-run, and re-running it is the only way anyone can check this.

### 3. Second search — mandatory, and mechanically different

**Run this regardless of what the first search returned.** A hit does not excuse
it; a miss does not excuse it. Its purpose is to defeat the framing of the first
query, which silently constrains what can be found — and a first query that
succeeded is precisely the case where the constraint goes unnoticed.

"Mechanically different" is specified rather than left to judgment. **The second
query must differ from the first in at least two of these four dimensions:**

| | dimension | varying it means |
|---|---|---|
| **a** | **REGISTER** | practitioner vocabulary vs academic vs specification language — "undo stack" vs "command pattern" vs "reversible operation history" |
| **b** | **DISCIPLINE** | the same problem is studied under different names in HCI, software engineering, human factors, information science, library science, safety engineering. **Ask which other field owns this.** A form's autosave is a UX question, a durability question, and a records-management question |
| **c** | **ABSTRACTION LEVEL** | the concrete technique, the pattern's name, the standard that governs it, the theory underneath. These return near-disjoint results — "peek height" vs "bottom sheet component" vs the WCAG criterion that constrains both |
| **d** | **ERA** | was this settled before the current vocabulary existed. Many interaction problems were solved in the 1980s and 90s and renamed since — lifecycle hooks predate every framework that made them implicit |

**Record the second query verbatim, and name which two dimensions it varied.**
More than two searches is fine and usually better; two is the floor, not the
target.

### 4. Report in a fixed shape

For each thing checked:

- **NAME** — what the field calls it, or "no established name found"
- **STATUS** — exists / partially exists / searched and did not find
- **THE SOURCE** — the specification, pattern or guideline, with its identifier
- **WHAT THEY LEARNED** — the failure modes, caveats and constraints the field
  already documents. **This is usually worth more than the solution**, and it is
  the part a design cannot obtain by reinventing
- **FIT** — what applies here, what does not, and why
- **DELTA** — what genuinely remains ours to design
- **THE TWO QUERIES** — verbatim, with the dimensions the second varied

**Record the report in the project's durable state** (`STATE.md`, `HANDOFF.md`
or whichever the project uses), not only in the conversation. A pass that exists
only in a transcript cannot be inherited: the next session re-searches ground
already covered, and the recorded queries — the thing that makes "found nothing"
checkable by someone else — are exactly what compaction discards first.

## The rules that make the report honest

**"Searched and did not find", never "does not exist."** No prior art found is a
legitimate finding, and that is the wording it gets. The recorded queries are
what make it checkable: they let the next person vary a dimension you did not,
rather than inherit your conclusion.

**Fetch before citing.** An identifier you have not opened is worth *less* than
a plain description of the same idea, because a description invites a check and a
spec number looks like one already happened. A search-result summary is not a
fetch; label anything drawn from one as search-derived. Where a source cannot be
reached — a paywall, a JS-only documentation site, a dead archive — **record it
as unverified** and let the claim stand or fall on other grounds.

**A found standard does not obligate adoption.** Report the fit, *including
where it does not fit*, and name the parts being declined. A pattern is
knowledge; a library is a dependency. This protocol delivers the first and is
not an argument for the second.

**A found standard does not override a recorded project decision.** Where one
contradicts a filed decision or a stated constraint, **report the conflict and
stop.** Resolving it is a decision, and this is a research pass.

**Prefer a specification, a standard, or peer-reviewed work to a blog post.**
Where only practitioner sources exist, say so. The quality of the source is part
of the finding, not a detail to be smoothed away once the claim has been written
down somewhere.

**Distinguish "the field solved this" from "the field named this."** A name with
no guidance attached is still valuable — it is the search term everyone after you
will need — but it is not a solution and must not be reported as one.

## Case studies

From one project's pass over a single design document. **These are that
project's results, not claims this plugin makes** — but their shape is why the
protocol is built this way.

**Six mechanisms were checked. Six had prior art. All of it was hidden behind
invented vocabulary**, which is the entire argument for step 1 being step 1: the
searches that failed were the ones run against project names.

- One project term returned nothing at all. Two field terms — **"scratch
  layer"** and **"selection set"** — returned a documented history that included
  the exact data-loss failure the design was already worried about.
- A behaviour described as "survives backgrounding, cleared on deliberate exit"
  read as an invention. It ships as a **named platform primitive**, documented
  with a table stating precisely what survives what.
- A pair of lifecycle hooks called "init/enter" read as an invention. They are
  **`viewDidLoad`/`viewWillAppear`** — and the field's own correction to that
  design, a *third* hook because the second runs before layout geometry is
  final, was a gap the design had not accounted for.

The last is the most valuable kind of result: prior art that supplies a
correction the project had not yet earned the right to know it needed.

## What not to do

- Do not start designing inside this pass. Findings, then stop. A protocol that
  slides into implementation stops producing checkable output.
- Do not report one search. Two, or the pass is not done — whatever the first
  one found.
- Do not launder a search summary into a citation. If it was not opened, label
  it as not opened.
