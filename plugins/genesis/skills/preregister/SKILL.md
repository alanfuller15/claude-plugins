---
name: preregister
description: Fix a decision rule in writing before running a measurement, experiment, or benchmark. Use whenever the answer matters and the result could otherwise select its own threshold — evaluating whether a feature earns its place, comparing approaches, or measuring anything that will be quoted afterwards.
---

# Pre-register before measuring

Write the decision rule down and commit it **before** computing. It costs five
minutes and it is the difference between a result and a rationalisation.

## What this protects against

Once a number exists, every threshold looks negotiable. Pre-registration
removes the negotiation by fixing the criteria while you are still indifferent
to the outcome.

The concrete failure it prevents: a signal that looks strong is admitted, a
signal that looks weak is excluded, and the exclusion is justified after the
fact. Deciding in advance is what makes an exclusion credible rather than
convenient.

## What to write down, before running anything

1. **The question**, in a form that can come out either way.
2. **What gets measured**, precisely enough to reproduce.
3. **The comparator.** This is the one people skip and it is where results go
   wrong most often. Name what the result must beat. If you cannot name the
   alternative, you have not specified a measurement yet.
4. **The decision rule.** What outcome means adopt, what outcome means reject.
   Include the null: what result would close this direction entirely.
5. **Known confounders**, and how each is controlled.
6. **Your prediction**, stated so it can be wrong.

Commit that file. Then compute.

## Choosing the comparator

Ask two questions:

**What is this being compared to?** Not "is it better than nothing" — better
than the best available alternative, and better than a trivial baseline that
reads none of your inputs. A trivial baseline that beats you is the single most
informative result available, and it will not appear unless you run it.

**What does the significance test hold fixed?** A resampling test that resamples
only one arm is not a test of the comparison. If one group's numbers are held
constant while the other is resampled, the resulting p-value can be wrong by
orders of magnitude.

## Retaining a candidate you expect to fail

If one option is predicted to fail, **keep it in the evaluation**. Removing it
makes the prediction unfalsifiable; retaining it makes a confirmed failure into
evidence. A prediction that was written down and then held is worth far more
than one that was quietly dropped.

## Reporting

Report against the pre-registered rule, in the units the rule specified. If a
number differs from what the rule assessed, reconcile it before publishing —
a discrepancy is more often a unit mismatch than an error, and finding out
which is the whole point.

Record deviations as deviations. A pre-registration that was amended midway and
not marked is worse than none, because it looks stronger than it is.
