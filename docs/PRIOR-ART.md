# Prior-art pass — genesis's own six mechanisms

Run 2026-07-29 under `/genesis:prior-art`, against the plugin that ships the
skill. Six mechanisms, ordered by how much a found standard would change what
the plugin is. 19 searches, 13 fetch attempts (11 succeeded, 2 returned
unparsed binary and were re-reached by another route).

**Nothing here changed plugin behaviour.** Where a finding contradicts a design
decision it is reported as a conflict and left open, per the skill's own rule.

**Headline.** Six mechanisms checked, six have prior art. Five of the six were
hidden behind vocabulary this project invented; the sixth (`preregister`) had
already landed on the field's own word and still missed the field's central
distinction. Two are governed by a published standard, one has a directly
comparable controlled experiment, one is an institution with registries and
templates. The pattern matches the case study this plugin cites in its own
skill, which is the least comfortable possible result.

---

## 1. Injecting durable state at session start

**NAME.** No single name; three fields own it under three.

- Systems: the **checkpoint–restart** / **checkpoint–recovery pattern** — save
  state to persistent storage during failure-free operation, restore from the
  last consistent checkpoint rather than replaying from the beginning.
- Cognitive psychology / HCI: **task resumption**, **resumption lag**,
  **resumption cues** — the interruption-and-resumption literature.
- Medicine and patient safety: **structured handoff / handover** — I-PASS, SBAR.
- Current agent practice: **externalized memory** / **context engineering**.

*What we call it:* "durable state injection", "the SessionStart hook".

**STATUS.** Exists, four times over, independently.

**THE SOURCE.**
- Checkpoint–recovery as a named resilience pattern — ScienceDirect
  *Checkpoint Restart* topic overview and Ashraf et al., *Resilience Design
  Patterns* (arXiv:1708.07422). **Search-derived; not fetched.**
- Altmann & Trafton, *Task Interruption: Resumption Lag and the Role of Cues*
  (CogSci 2004). **Fetch failed** — interruptions.net serves a PDF that
  returned unparsed binary. Recorded as unverified.
- Cegarra et al., *Resuming a Dynamic Task Following Increasingly Long
  Interruptions*, Front. Psychol. 12:659451 (2021). **Fetched.**
- AHRQ, *Making Healthcare Safer IV: Use of Structured Handoff Protocols for
  Intrahospital Within-Unit Transitions*, NCBI Bookshelf NBK613742.
  **Fetched.**
- Anthropic, *Context engineering: memory, compaction, and tool clearing*
  (Claude Cookbook). **Fetched.**
- Zhou et al., *Externalization in LLM Agents: A Unified Review*
  (arXiv:2604.08224, Apr 2026). **Abstract fetched.**

**WHAT THEY LEARNED.**

- **Resumption after a long gap is reconstruction, not retrieval.** Cegarra et
  al. found working-memory capacity predicted fast resumption only for
  interruptions of ≤5s; at 15–30s, visual search capacity dominated —
  "the importance of visual search for recovery seems to be greater following
  long interruptions". As the internal trace decays, the *environment* becomes
  the source of truth. This is the empirical case for injecting state rather
  than trusting what survived a summary, and the plugin did not have it.
- **Cues that say what to do next beat cues that re-present information.** The
  interruption literature separates "retrieval cues" from "assistant cues"; the
  latter, which name the position and the next action, reduce resumption lag
  further and reduce working-memory load. `handoff` step 4 ("one line: what the
  next session should do first") is exactly this. `SessionStart` itself carries
  no next-action field — it injects whatever the project wrote.
- **I-PASS names five components**: Illness severity, Patient summary, Action
  list, Situation awareness and contingency plans, **Synthesis by receiver**.
  AHRQ rates it moderate-certainty for improving clinical outcomes — the
  strongest evidence grade in that review, above SBAR's low.
- **The I-PASS caveat is worth more than the endorsement.** Outside the
  developer team, results did not hold: "three sites did not find statistically
  significant reductions in errors, and one site found more errors after
  implementation." And the intervention was never the artifact alone — the
  bundle included a 2-hour workshop, a simulation session, a computer module, a
  faculty development programme, direct-observation tools and a culture-change
  campaign.
- **Compaction's losses have been measured, not just asserted.** The Claude
  cookbook's probe test distinguishes what survives (high-level facts,
  organism identities, major comparisons, key decisions) from what is lost
  (specific table cells, heterogeneity statistics, exact numerical details from
  appendices, exact phrasing): "overly aggressive compaction can lose subtle
  but critical context whose importance only becomes apparent later."
- The same source recommends the opposite control model from this plugin's:
  the model elects what to save via a memory tool, on the reasoning that
  "the model decides what and when to save … is more effective than trying to
  predict ahead of time."

**FIT.** The mechanism is the checkpoint–recovery pattern applied to a
conversational agent, and the HCI result supplies the justification the plugin
argues for from anecdote. The medical handoff literature is the closest match
to what `handoff` actually produces, and it is a *protocol with an evidence
base* rather than a convention.

**DELTA — what genuinely remains ours.**

- Unconditional, hook-enforced injection at fixed paths. Every source above
  either relies on a human remembering to read the handoff, or on the model
  electing to consult memory. A `SessionStart` hook removes the election. The
  organisational-memory literature (§6) identifies non-retrieval as the primary
  decay mode of lessons-learned repositories, which makes this the plugin's
  strongest genuinely-original property.
- **The precedence declaration.** No source found states a rule for which wins
  when a summary and a state file disagree. Checkpoint–recovery has no summary;
  I-PASS has no competing record. The three lines of injected precedence text
  are, as far as this pass found, not prior art.
- "Verify against the tree before acting on it" as part of the injected block.

**CONFLICTS — reported, not resolved.**

- **C1. `handoff` has no receiver-side synthesis.** I-PASS's fifth component is
  read-back: the receiver restates and the sender confirms. `handoff`'s test is
  self-administered ("read your own handoff as if you had never seen this
  project"), which is the same context checking itself — the exact failure mode
  §3 documents. The receiving session is a different context and could confirm,
  and nothing asks it to.
- **C2. No criticality marker.** I-PASS leads with illness severity. The
  injected block has no field for "how urgent/fragile is this state", and
  `handoff` does not ask for one.
- **C3. The I-PASS non-replication bears directly on the plugin's central
  claim.** "The plugin ships the machinery. The project ships the content" is
  the design. The best-evidenced structured-handoff protocol in existence did
  not reliably transfer outside its authors *even shipping a training bundle
  around the artifact*. That is not an argument against the design, but it is
  evidence against expecting the artifact alone to carry.

---

## 2. Snapshotting a transcript before lossy summarisation

**NAME.** Three separate things, and the plugin was conflating them.

- The mechanism: **write-ahead logging** (WAL) — durably record the change
  before applying it; ARIES is the canonical algorithm.
- The property: **lossy vs lossless**; for text, **faithfulness**, and the
  intrinsic/extrinsic **hallucination** distinction.
- The institutional form: **verbatim record vs summary record**; in law, the
  **best evidence rule** (original-document requirement; summaries of
  voluminous records).

*What we call it:* "the compaction snapshot".

**STATUS.** The mechanism and the institutional rule **exist**. The specific
question — *what summarisation destroys, and what must be preserved verbatim* —
**partially exists**: named and studied for one half (added/wrong content),
much thinner for the other (omission), and **searched and did not find** any
general "must be preserved verbatim" content list.

**THE SOURCE.**
- Mohan et al., *ARIES* (ACM TODS 1992) — the WAL ordering rule. **Not
  fetched**; the rule as stated below is **search-derived** from teaching
  material (Berkeley CS262a, UBC CPSC 504, Sookocheff's review).
- Maynez, Narayan, Bohnet & McDonald, *On Faithfulness and Factuality in
  Abstractive Summarization*, ACL 2020. **Abstract fetched verbatim**; the
  paper's own intrinsic/extrinsic rates were not in the fetched page and are
  **not cited here as numbers.**
- U.S. Federal Rules of Evidence 1002 (requirement of the original) and 1006
  (summaries of voluminous writings). **Search-derived** from NY Courts'
  *Guide to New York Evidence* Art. 10 and Cornell LII; the rule text itself
  was not fetched.
- NARA appraisal policy — minutes "may be summaries, verbatim transcripts, or
  edited summaries". **Search-derived.**
- Anthropic Claude Cookbook compaction probe (fetched; see §1).

**WHAT THEY LEARNED.**

- **The WAL ordering rule is stated as a rule, with a reason for each half.**
  The log record for an update must be forced to durable storage *before* the
  corresponding data page reaches disk (the undo rule → atomicity), and all of
  a transaction's log records must be written before commit (the redo rule →
  durability). Recovery then works because "the log is the source of truth".
- **FRE 1006 is the plugin's own argument, already codified.** A summary of
  voluminous records is admissible **only if** the originals remain "available
  for examination or copying … by other parties at a reasonable time and
  place". The summary is usable *because* the original was retained. That is
  precisely why `PreCompact` exists, and the field wrote it down in a rule of
  evidence.
- The archival answer is more permissive than the plugin assumes: NARA treats
  summary minutes and verbatim transcripts as both potentially permanent. There
  is no archival principle that verbatim must be kept.
- **The concrete answer to "what does summarisation destroy" came from the
  vendor's measured probe, not the academic literature.** The summarization
  research found is overwhelmingly about *faithfulness* — content the summary
  adds or distorts — rather than *omission*, which is the failure `PreCompact`
  is built against. Exact numbers, appendix-level specifics, and exact phrasing
  are what go.

**FIT.** WAL names the mechanism and supplies an ordering rule. FRE 1006
supplies the justification in stronger form than the README states it. The
cookbook probe supplies the content answer.

**DELTA.**

- What must be preserved verbatim *from an agent transcript specifically* is not
  written down anywhere this pass reached. genesis answers by not answering —
  it snapshots everything, which is cheap and needs no taxonomy. Defensible,
  and now visibly a sidestep rather than a solution.
- Retention (20 snapshots, trigger-stamped directories) is ordinary practice
  and not claimed as novel.

**CONFLICT — reported, not resolved.**

- **C4. `pre-compact.sh` instantiates WAL and does not honour WAL's ordering
  rule.** Every failure path in that script is `exit 0`: `mkdir` failure,
  a missing or unreadable `transcript_path`, a `cp` that fails. Compaction then
  proceeds and the transcript is gone with no snapshot and no signal. WAL's
  entire content is that the lossy step must not proceed until the log is
  durable. The plugin's own reasoning elsewhere — the `Stop` gate is a hook
  "rather than a convention" precisely so it cannot be skipped — is the
  argument against its own choice here. Whether `PreCompact` can block
  compaction at all was not investigated in this pass; if it cannot, the
  divergence is forced rather than chosen, and that is worth recording as the
  reason.

---

## 3. Generator–evaluator separation

**NAME.**

- Software and systems engineering: **independent verification and validation
  (IV&V)**, and specifically the **independence** requirement of **IEEE Std
  1012** — decomposed into *technical*, *managerial* and *financial*
  independence.
- Process: **separation of duties** / **four-eyes principle**; **Fagan
  inspection** (the author is not the moderator).
- Current ML: **generator–evaluator separation**, **LLM-as-a-judge**, the
  **self-correction / self-verification limits** literature, **correlated
  error** between generator and judge, and **Cross-Context Review**.

*What we call it:* "the verifier agent", "an isolated context".

**STATUS.** Exists — with a standard in one discipline and a directly
comparable controlled experiment in another. This is the best-supported of the
six, and the one where the field has most to say back.

**THE SOURCE.**
- IEEE Std 1012-2016, *IEEE Standard for System, Software, and Hardware
  Verification and Validation* (IEEE Xplore doc 8055462). **Not fetched —
  paywalled.** The independence definitions below are **search-derived** from
  a hosted copy of the 1012 text (profs.etsmtl.ca) and the HHS *IV&V Practices
  Guide*, and are recorded as unverified against the standard itself.
- Huang, Chen, Mishra, Zheng, Yu, Song & Zhou, *Large Language Models Cannot
  Self-Correct Reasoning Yet*, arXiv:2310.01798, **ICLR 2024**. **Abstract
  fetched verbatim.**
- Song, *Cross-Context Review: Improving LLM Output Quality by Separating
  Production and Review Sessions*, arXiv:2603.12123 (12 Mar 2026). **Abstract
  fetched verbatim.** Single-author preprint, not peer-reviewed — source
  quality is part of the finding.
- Stechly, Valmeekam & Kambhampati, *On the Self-Verification Limitations of
  LLMs on Reasoning and Planning Tasks*, arXiv:2402.08115. **Not fetched.**

**WHAT THEY LEARNED.**

- **IEEE 1012 splits independence into three axes and scales the required level
  to criticality.** Technical independence means practitioners who assess the
  product independently of those who built it; managerial independence vests
  responsibility in a separate organisation from the one building the product.
  "The closer the tester is to the developer, the more difficult it is to be
  objective."
- **Huang et al. (verbatim):** "in the context of reasoning, our research
  indicates that LLMs struggle to self-correct their responses without external
  feedback, and at times, their performance even degrades after
  self-correction." The plugin's verifier exists on exactly this reasoning and
  had no citation for it.
- **The proposed mechanism is correlated error**: when generator and evaluator
  share failure modes, self-evaluation is weak evidence of correctness, and
  repeated self-critique amplifies confidence without adding information.
- **Cross-Context Review measured this design.** 30 artifacts, 150 injected
  errors, 360 reviews, four conditions. CCR (fresh session, no access to
  production history) reached **F1 28.6%**, beating same-session self-review
  **24.6%** (p=0.008, d=0.52), repeated same-session self-review **21.7%**
  (p<0.001, d=0.72), and **context-aware subagent review 23.8%** (p=0.004,
  d=0.57). Reviewing twice in the same session did not beat reviewing once
  (p=0.11) — which is what isolates context separation as the cause rather
  than repetition.

**FIT.** Very high. Two independent literatures converge on the plugin's
design, one of them by direct measurement of it.

**DELTA.**

- **Tool-level enforcement of read-only.** IEEE 1012 specifies organisational
  independence; it has no notion of restricting the reviewer's *capabilities*.
  `tools: Read, Grep, Glob, Bash` plus "Bash is for inspection only" is a
  mechanical form of independence the standard does not describe.
- **The three-outcome output contract** — holds / does not hold / cannot be
  determined from the tree, with "report the negative" made mandatory. The
  LLM-as-judge literature does not, in what this pass reached, require a judge
  to distinguish "could not determine" from "passed".

**CONFLICTS — reported, not resolved.**

- **C5. The measured result that most matters is the one about subagents, and
  it is not favourable.** In CCR's experiment a *context-aware* subagent review
  scored 23.8% — statistically indistinguishable from plain same-session
  self-review (24.6%), and significantly below fresh-context review. genesis's
  verifier is spawned from the producing session, and its method section
  actively invites the producing context in: "if the request is vague, state
  your reading of it before starting." The agent gets a clean context but its
  *prompt* is written by the context under review. If CCR is right about where
  the benefit comes from, the plugin may be shipping the SA condition while
  documenting the CCR one.
- **C6. Absolute performance is much worse than the plugin implies.** The best
  condition found ~29% of injected errors. Nothing in the verifier's
  documentation says a single sweep is weak evidence; "Findings only. Lead with
  anything that does not hold" reads as a complete audit. One pass missing two
  thirds of defects is a different instrument than that.
- **C7. Managerial independence is absent and unacknowledged.** Same model,
  same session, spawned and prompted by the producer, reporting back to it.
  IEEE 1012's own framework says that is one axis of three. The plugin claims
  "isolated context", which is accurate, and never distinguishes it from
  independence.

---

## 4. Blocking a turn on a project-declared gate

**NAME.** Two halves, each with its own name.

- The stop condition: **quality gate**; and in lean manufacturing, **jidoka**
  ("autonomation") with **andon** as its signalling tool — colloquially
  *stop-the-line*.
- The project-supplies-it-at-a-known-path half: **convention over
  configuration**, and concretely **Scripts To Rule Them All** (GitHub, 2015) —
  `script/test`, `script/cibuild`. Neighbours: git hooks, `Makefile` targets,
  `.pre-commit-config.yaml`, CI required status checks.

*What we call it:* "the gate", "`.claude/verify.sh`".

**STATUS.** Exists, both halves, under names the plugin uses nowhere.

**THE SOURCE.**
- *Scripts to Rule Them All*, GitHub Engineering blog (2015). **Fetched.**
- *Andon — Toyota Production System guide*, Toyota UK. **Fetched.**
- Quality-gate definitions (Sonar, TechTarget, ZetCode; and Bogner et al.,
  *Quality Gates in Software Development*, CEUR Vol-3845 paper 06).
  **Search-derived; not fetched.**
- *Convention over configuration* (Wikipedia). **Search-derived.**

**WHAT THEY LEARNED.**

- **STRTA's rationale is the plugin's rationale, in the plugin's own words,
  eleven years earlier**: "Normalizing on script names not only minimizes
  duplicated effort, it means contributors can do the things they need to do
  without having an extensive fundamental knowledge of how the project works."
  Language-agnostic by design — each script may be written in whatever suits
  the project. `.claude/verify.sh` is `script/test` at a different path.
- **STRTA already has two names for the split the plugin's README improvises.**
  `script/test` runs in development; `script/cibuild` is the CI entry point and
  calls `script/test`. The genesis README says "if it takes minutes, gate a
  subset here and run the full suite deliberately" — that is the
  test/cibuild distinction, and the convention supplies vocabulary for it.
- **Toyota's andon is not what the software world quotes it as, and the
  difference is the interesting part.** Per Toyota's own description, pulling
  the cord raises a signal; the team leader then has until the end of the
  worker's standard cycle time to resolve it, and **the line halts only if they
  cannot**. The real mechanism is a *time-boxed escalation*, not a binary stop.
- **The documented social precondition:** when the leader arrived, they thanked
  the person who pulled the cord — "unconditional behaviour reinforcement", so
  no one fears retribution for stopping the line. A gate people are punished
  for triggering stops being pulled.

**FIT.** High for the convention half. The lean half fits the plugin's
*argument* better than its *implementation*.

**DELTA.**

- The gated transition is a **conversational turn**, not a commit, a merge or a
  build stage. Neither the quality-gate literature nor STRTA nor git hooks
  cover an agent's turn boundary; the closest neighbour is a pre-commit hook,
  and a turn is not a commit.
- The **dirty-tree condition** — the gate runs only when the turn changed
  something — is not a feature of any source found.

**CONFLICTS — reported, not resolved.**

- **C8. Toyota's graduated stop versus genesis's binary one.** genesis has two
  states: gate passes, or the turn cannot end. Toyota has three: signal, bounded
  attempt-to-fix within cycle time, then halt. The plugin's escape hatch
  (`.genesis/skip-verify`) is a *manual, indefinite* override rather than a
  *bounded automatic* one, which is the opposite shape. Whether the turn
  boundary admits a time-box is a design question this pass does not answer.
- **C9. Convergence worth noting rather than a conflict.** `.claude/verify.sh`
  argues in its own comments that a check which misfires "trains the author to
  reach for `.genesis/skip-verify`, and a gate that is habitually skipped is
  not a gate." That is the andon social finding, derived independently. It now
  has a name and a source, and the plugin should probably cite it rather than
  re-derive it.

---

## 5. Fixing a decision rule before a measurement runs

**NAME.** The plugin already uses the field's word — **preregistration** — so
the expectation that this one hid behind an invented name is half wrong. What
it does *not* use is the rest of the vocabulary:

- The artifact: **pre-analysis plan (PAP)**; the strong publication form:
  **Registered Reports** with **in-principle acceptance**.
- The failure modes, each named: **HARKing** (hypothesising after the results
  are known — Kerr 1998), the **garden of forking paths** (Gelman & Loken
  2013), **p-hacking**, **outcome switching**, **researcher degrees of
  freedom**.
- The organising distinction: **confirmatory vs exploratory**.

**STATUS.** Exists — as an institution, with registries (OSF, AEA RCT
Registry, AsPredicted), discipline-specific templates, and standards.

**THE SOURCE.**
- Center for Open Science, *Preregistration* (cos.io/initiatives/prereg).
  **Fetched.**
- APA, *Preregistration Standards for Research in Quantitative Psychology*.
  **Search-derived.**
- J-PAL, *Pre-analysis plans*; *Experimentology* ch. 11; FORRT glossary
  (HARKing). **Search-derived.**
- Kerr, *HARKing: Hypothesizing After the Results are Known* (1998); Gelman &
  Loken, *The Garden of Forking Paths* (2013). **Not fetched.**

**WHAT THEY LEARNED.**

- **The confirmatory/exploratory separation is the field's central
  contribution**, and it is a *licence* as much as a restriction. Per COS:
  confirmatory work tests pre-specified hypotheses, minimises false positives,
  and p-values retain diagnostic value; exploratory work searches for
  unexpected relationships, minimises false negatives, and its p-values *lose*
  diagnostic value and require replication. "Both are important" — but they must
  be labelled differently.
- **"Preregistration is a plan, not a prison."** COS pairs this with a named
  artifact — a *Transparent Changes document* — for disclosing deviations.
- **Registered Reports do something no self-administered plan can**: the plan
  is peer-reviewed *before* results exist, and acceptance is guaranteed
  regardless of outcome. The credibility comes from an outside party at plan
  time, not from the author's discipline.
- Templates routinely require two things the skill's six-item list omits:
  **outlier and exclusion handling**, and a **stopping rule / sample size**
  decided in advance.

**FIT.** Very high. `preregister` is a compressed pre-analysis plan, and the
field's version is more complete.

**DELTA.**

- The **comparator emphasis** is stronger in the skill than in the templates
  found. "A trivial baseline that reads none of your inputs" and "a trivial
  baseline that beats you is the single most informative result available" is ML
  register, not psychology register, and it is the skill's best original
  content.
- **"Retain a candidate you expect to fail."** The field prevents dropping a
  *hypothesis*; the skill prevents dropping an *arm* of the evaluation to
  protect a prediction. Related, not the same, and not found stated elsewhere.
- The resampling warning ("a test that resamples only one arm is not a test of
  the comparison") is a specific methodological point not covered by the
  general preregistration sources.

**CONFLICT — reported, not resolved.**

- **C10. `preregister` has no confirmatory/exploratory distinction, and this is
  the most substantive gap the whole pass found.** The skill's rules are all
  restrictive — commit the rule, report against it, mark deviations, "a
  pre-registration that was amended midway and not marked is worse than none."
  It never says that unplanned analysis is legitimate when labelled as
  exploratory. Read literally, it discourages looking at anything you did not
  pre-specify, which is not what the field concluded; the field concluded that
  you may look at anything provided you do not call it confirmatory. Fixing this
  would change the skill's content, so it is filed and left.
- **C11. The plugin has an outside reviewer and never connects it to this
  skill.** Registered Reports' whole advantage is review of the plan before the
  result exists. genesis ships a read-only verifier agent in an isolated
  context — the closest thing a single-author project can have to
  in-principle-acceptance review — and `preregister` never mentions it. §3's
  literature says self-review is the weak case; §5's literature says plan-time
  outside review is the strong form. Nothing joins them.

---

## 6. A catalogue of recorded failure classes checked against new work

**NAME.**

- The taxonomy: **Orthogonal Defect Classification (ODC)** — Ram Chillarege,
  IBM Research, late 1980s–early 90s. Related: **defect causal analysis**.
- The use-as-a-test: **inspection checklists derived from defect history**
  (Fagan-style inspection), and **"every bug gets a regression test"** — the
  regression suite as institutional memory.
- The organisational form: **lessons-learned repository** /
  **organisational memory**; industry-wide instances: **CWE**, the ISTQB
  testing principles.
- The decay law: **the pesticide paradox** (Beizer).

*What we call it:* "recorded failure classes", "the project's own history used
as the test".

**STATUS.** Exists.

**THE SOURCE.**
- *Orthogonal defect classification* (Wikipedia). **Fetched.**
- Chillarege et al., *Orthogonal Defect Classification — A Concept for
  In-Process Measurements*, IEEE TSE 18(11), 1992. **Not fetched.**
- Beizer, *Software Testing Techniques* (2nd ed., 1990) — pesticide paradox.
  **Not fetched;** the quotation below is **search-derived** and should be
  checked against the book before being quoted publicly.
- Broekema, *Conceptualizing Organizational Forgetting in a Crisis Context*,
  Risk, Hazards & Crisis in Public Policy (2025); practitioner sources on
  lessons-learned repositories and regression-suite bloat. **Search-derived.**

**WHAT THEY LEARNED.** This is where the field pays out most.

- **Orthogonality is a requirement, not decoration.** ODC's value comes from
  categories that are mutually exclusive and span the space — that is what
  turns a pile of defects into "a measurement on the process". A catalogue whose
  entries overlap stops measuring anything.
- **ODC gives "what-is, not why"**, and its own documentation names this as the
  limit on its predictive power. A catalogue of past failures is a measurement
  of the process that produced them, not a forecast of the next one.
- **The pesticide paradox is the finding that most directly threatens this
  mechanism.** Beizer: "Every method you use to prevent or find bugs leaves a
  residue of subtler bugs against which those methods are ineffectual." A
  catalogue checked against new work **decays by succeeding**: once the recorded
  classes are reliably avoided, yield falls toward zero while cost stays
  constant — and nothing in the record announces that. This is structurally
  identical to the drift argument `reconcile` already makes about status
  documents, pointed at the checklist instead.
- **Add-without-retire is the documented decay mode**, in both the testing and
  the checklist literature; the remedy is an explicit periodic prune, treated
  as maintenance rather than loss.
- **Lessons-learned repositories fail at retrieval, not at capture.** They decay
  because nobody looks — scattered across wikis and drives, found only by
  someone who already knew to search. And psychological safety determines
  whether the entries are true: without it, postmortems record what is
  politically safe rather than what happened.

**FIT.** High, and mostly as warnings rather than as design.

**DELTA.**

- **Unconditional retrieval is genesis's real contribution here**, and the
  literature is what makes that visible. The dominant failure of every
  lessons-learned system found is that the record is not read; a `SessionStart`
  hook that injects the state file whether or not anyone asks removes that
  failure by construction. The plugin's README argues for this as convenience.
  It is more than that.
- The failure classes are about **the process of working with an agent** rather
  than product defects, so no existing taxonomy's categories transfer directly.

**CONFLICTS — reported, not resolved.**

- **C12. Nothing in genesis ever retires an entry.** `reconcile` corrects claims
  that have drifted and explicitly refuses to open new work; `handoff` appends;
  the README's provenance list only grows. Both the testing and the checklist
  literature identify add-without-prune as the decay mode, and the pesticide
  paradox says the highest-value entries are the ones most likely to have gone
  inert. There is no prune pass and no argument for not having one.
- **C13. No orthogonality constraint on the recorded classes.** ODC's central
  requirement has no analogue in genesis, where entries are prose of any shape.
  Whether that matters at this scale is a judgment, not a finding.
- **C14. The plugin's own instrument for judging "is this class still live" is
  the instrument §3 says is unreliable in absolute terms.** The failure-classes
  pattern rests on the verifier; the verifier's best measured analogue finds
  under a third of injected defects. Compounding, not additive.

---

## The queries, verbatim

19 searches. Each mechanism's first two are listed with the dimensions the
second varied — REGISTER, DISCIPLINE, ABSTRACTION LEVEL, ERA — followed by any
additional queries run for that mechanism.

### 1. Session-start state injection

1. `checkpoint restart pattern "what is checkpointing" process resumes from persisted state rather than replaying a log`
2. `"resumption lag" "resumption cue" interrupted task memory for goals what content helps a person resume`
   — varied **DISCIPLINE** (distributed systems → cognitive psychology/HCI),
   **ERA** (current HPC/stream-processing vocabulary → the 1990s–2000s
   interruption literature), **REGISTER** (practitioner → academic). 3 of 4.
3. `I-PASS SBAR structured handoff medicine what a handoff must contain evidence error reduction`
   — **DISCIPLINE** (medicine/patient safety), **ABSTRACTION** (the named
   protocol and its evidence grade).
4. `context engineering agents external memory write state to disk "what belongs in" persistent context file guidance`
   — **REGISTER** (vendor/practitioner guidance), **ERA** (2025–26).

### 2. Pre-summarisation snapshot

5. `"information loss in abstractive summarization" what summarization omits faithfulness research findings`
6. `"verbatim record" versus "summary record" archival appraisal what must be preserved verbatim`
   — varied **DISCIPLINE** (NLP → archival science / records management) and
   **REGISTER** (ML research → institutional appraisal language). 2 of 4.
7. `"best evidence rule" original record versus summary "record copy" why a summary is not a substitute retention`
   — **DISCIPLINE** (law of evidence), **ABSTRACTION** (the governing rule
   rather than the technique).
8. `write-ahead logging "log before" durability ordering rule ARIES recovery why the log is written first`
   — **ABSTRACTION** (the underlying mechanism), **DISCIPLINE** (database
   systems), **ERA** (1992).

### 3. Generator–evaluator separation

9. `"independent verification and validation" IEEE 1012 standard independence of verifier from developer`
10. `"cannot self-correct" LLM self-critique limitation generator judge separation intrinsic self-correction reasoning`
    — varied **REGISTER** (specification language → ML research),
    **ERA** (1998–2016 standards → 2023–26 literature), and
    **ABSTRACTION** (the standard that governs → the empirical result). 3 of 4.

### 4. Project-declared gate

11. `"scripts to rule them all" convention project provides script at known path build gate`
12. `jidoka "andon cord" stop the line principle a defect halts the process Toyota production system`
    — varied **DISCIPLINE** (software engineering → lean manufacturing /
    industrial engineering), **ERA** (a 2015 convention → post-war TPS), and
    **REGISTER** (engineering-blog practitioner → the principle's own
    vocabulary). 3 of 4.
13. `"quality gate" definition "well-known path" convention over configuration tool runs a project-supplied script exit status contract`
    — **ABSTRACTION** (the general pattern name). Returned the weakest results
    of any query here: quality-gate and convention-over-configuration
    definitions, and an explicit miss on the combination.

### 5. Pre-registration

14. `"pre-analysis plan" "registered reports" preregistration what it must specify template standard`
15. `HARKing Kerr 1998 "garden of forking paths" outcome switching what preregistration prevents`
    — varied **ABSTRACTION** (the artifact and its templates → the theory of
    the failure it prevents), **ERA** (Kerr 1998, Gelman & Loken 2013), and
    **REGISTER** (registry how-to → the methodological critique literature).
    3 of 4.

### 6. Recorded failure classes

16. `"orthogonal defect classification" defect taxonomy inspection checklist derived from a project's own defect history`
17. `"lessons learned" repository organizational memory why checklists decay checklist fatigue safety engineering`
    — varied **DISCIPLINE** (software quality measurement → knowledge
    management / safety and crisis research) and **ABSTRACTION** (the technique
    → why the technique degrades). 2 of 4.
18. `"every bug gets a regression test" defect becomes a test institutional memory practice checklist bloat`
    — **REGISTER** (practitioner), **ABSTRACTION** (the concrete practice).
19. `Beizer "pesticide paradox" tests lose effectiveness repeated same tests find fewer defects origin`
    — **ERA** (1990), **ABSTRACTION** (the named law). This query returned the
    single most consequential finding in the pass, and it was reachable only
    once query 17 supplied the phrase.

### Fetch record

**Fetched and read:** GitHub *Scripts to Rule Them All*; Toyota UK *Andon*;
Wikipedia *Orthogonal defect classification*; COS *Preregistration*;
arXiv:2310.01798 abstract page; arXiv:2603.12123 abstract page;
arXiv:2604.08224 abstract page; Front. Psychol. 12:659451 (full text);
NCBI Bookshelf NBK613742 (AHRQ); research.google page for Maynez et al.;
Claude Cookbook context-engineering page.

**Fetch attempted and failed** (returned unparsed binary PDF, recorded as
unverified): `arxiv.org/pdf/2310.01798` — recovered via the abstract page;
`interruptions.net/literature/Altmann-CogSci04.pdf` — **not recovered**, the
resumption-cue claims rest on Cegarra et al. 2021 and on search-derived
summaries of Altmann & Trafton.

**Not fetched, and cited as search-derived or by identifier only:** IEEE Std
1012-2016 (paywalled); Chillarege et al. TSE 1992; Beizer 1990; Kerr 1998;
Gelman & Loken 2013; Mohan et al. ARIES 1992; FRE 1002/1006 rule text;
arXiv:2402.08115; NARA appraisal policy.

---

## What this pass did not do

No behaviour changed. Fourteen conflicts (C1–C14) are filed above and none is
resolved — resolving them is a decision, and this was a research pass.

Two are cheap and purely additive if taken up (citing Huang et al. for the
verifier's existence; citing andon for the skip-file argument
`.claude/verify.sh` already makes). Two would change what a skill says
(C10 confirmatory/exploratory; C1 receiver read-back). One is a genuine
open question about what the harness permits (C4, whether `PreCompact` can
block compaction at all). The rest are judgments about scale.
