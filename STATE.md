# State

Read every session via genesis's own `SessionStart` hook. Keep it short.

## Where things stand

`genesis` 1.0.7. Four hooks, four skills, one agent, two test suites, gate green
(`bash .claude/verify.sh`, ~1.7s). The one external bug report (Windows write
guard, 1.0.1) is fixed and covered by tests.

**One open defect: C4** — `pre-compact.sh` can block compaction and does not.
Confirmed by fetched documentation and an observed test; see the Resolutions
section of [docs/PRIOR-ART.md](docs/PRIOR-ART.md) for both, and for what the fix
would be and the hard case it has to decide (a hook that blocks on a full disk
blocks every subsequent compaction).

**1.0.6 was published and withdrawn**, 2026-07-30 ~02:00Z, live about 20
minutes. It carried no plugin payload — `git diff 50a64f1 c29281e --
plugins/genesis/` is the version string alone. The rule now scopes to shipped
content, meaning anything under `plugins/genesis/`; reasoning is a Provenance
entry in the plugin README.

**The withdrawal shipped as 1.0.7, not as a rollback to 1.0.5**, and the reason
is the finding: the commit correcting the rule edits
`plugins/genesis/README.md`, which **is** shipped content — verified present in
the install cache at
`~/.claude/plugins/cache/alanfuller15-tools/genesis/1.0.5/README.md`,
byte-identical to 50a64f1. Reusing the 1.0.5 key against a corrected README
would leave every existing install holding the old copy with nothing to tell
them, which is the 1.0.1 failure. A rollback would have been mechanically fine
(the version is a cache key compared for equality, not an ordering) and wrong on
content. **1.0.6 is burnt — never reuse it**: an install that fetched it would
see a matching key and skip.

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

**Fourteen conflicts filed (C1–C14). C4 settled; thirteen open** — resolving is
a decision, that was a research pass. The four that would change behaviour:

- **C4 — SETTLED, real defect.** `pre-compact.sh` instantiates WAL and fails
  open on every error path, so compaction proceeds with no snapshot and no
  signal. A `PreCompact` hook *can* block: exit 2 blocks compaction (docs), and
  an observed test produced `Compaction blocked by PreCompact hook`. The
  divergence is chosen, not forced. Fix not written.
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

Fix C4 — it is the only confirmed defect, the harness question is answered, and
the narrow form (check `cp`'s exit status; block only when a transcript existed
and its copy failed) is written up. That fix touches `plugins/genesis/`, so it
is a real release: bump to 1.0.8.

Then decide C1/C5/C10 individually — each is a separate call, and C10 is a
ruling not yet made. Take the two free citations whenever the relevant file is
next touched.
