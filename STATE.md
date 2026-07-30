# State

Read every session via genesis's own `SessionStart` hook. Keep it short.

## Where things stand

`genesis` 1.0.6 published. Four hooks, four skills, one agent, two test suites,
gate green (`bash .claude/verify.sh`, ~1.7s). No open defects. The one external
bug report (Windows write guard, 1.0.1) is fixed and covered by tests.

## Prior art

**Pass run 2026-07-29 over genesis's own six mechanisms. Full report, with all
19 queries verbatim and the fetch record: [docs/PRIOR-ART.md](docs/PRIOR-ART.md).**

Six checked, six have prior art. Five were hidden behind vocabulary this project
invented — the same result the `prior-art` skill cites as its own case study.

| what we call it | what the field calls it |
|---|---|
| durable state injection | checkpoint–recovery; task resumption cues (HCI); structured handoff (I-PASS/SBAR); externalized memory |
| compaction snapshot | write-ahead logging; best evidence rule (FRE 1002/1006); verbatim vs summary record |
| the verifier agent | independence of V&V (IEEE 1012); separation of duties; Cross-Context Review |
| the gate | quality gate; jidoka / andon; Scripts To Rule Them All (`script/test`) |
| pre-registration | *name matched* — but pre-analysis plan, Registered Reports, HARKing, garden of forking paths |
| recorded failure classes | Orthogonal Defect Classification; lessons-learned repository; pesticide paradox |

**Fourteen conflicts filed (C1–C14), none resolved** — resolving is a decision,
that was a research pass. The four that would change behaviour:

- **C4** — `pre-compact.sh` instantiates WAL and fails open on every error path,
  so compaction can proceed with no snapshot and no signal. Open question first:
  can `PreCompact` block compaction at all?
- **C5** — Cross-Context Review measured a *context-aware* subagent at 23.8% F1,
  indistinguishable from same-session self-review (24.6%) and below fresh-context
  review (28.6%). The verifier is prompted by the context under review.
- **C10** — `preregister` has no confirmatory/exploratory distinction, which is
  the field's central contribution. Read literally the skill discourages
  unplanned analysis; the field permits it, labelled.
- **C1** — `handoff`'s test is self-administered. I-PASS's fifth component is
  synthesis *by the receiver*, and the receiving session is a different context.

Two are free: cite Huang et al. (arXiv:2310.01798, ICLR 2024) for why the
verifier exists, and cite andon for the skip-file argument `.claude/verify.sh`
already makes independently.

## Residue

The pass was run on the plugin that ships the skill, and the `SessionStart`
prior-art notice was firing here truthfully — no mechanism in genesis had ever
been checked against the field. Creating this file is what turns that notice
off, which is the documented off switch working, not a workaround.

The strongest finding is `#6`'s pesticide paradox: a catalogue of failure
classes decays *by succeeding*, and genesis has no prune step anywhere. The
strongest thing the pass found in genesis's favour is that unconditional
hook-injected retrieval solves the failure mode that kills lessons-learned
repositories — nobody reads them. The README argues for that as convenience; it
is more than convenience.

## Next

Decide C1/C4/C5/C10 individually — each is a separate call, and C4 needs the
harness question answered before it can be judged. Take the two free citations
whenever the relevant file is next touched.
