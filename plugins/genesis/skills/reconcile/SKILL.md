---
name: reconcile
description: Reconcile a project's status documents against the actual repository. Use at the start of a working session, or whenever a status file, handoff item, or README claim might have gone stale. Catches headers that describe work as unfinished when it has already landed, and documents that exist but are unreachable from the entry point.
---

# Reconcile the record against the tree

A status document is a **claim about the repository**, not the repository. This
skill verifies those claims and corrects the ones that have drifted.

## Why this is worth a dedicated pass

Staleness in status documents is not random — it is **structurally
pessimistic**. Entries get written when work is identified and are rarely
rewritten when it lands, because landing feels like the completion. So drift
accumulates on the side that makes the project look less finished than it is.

The failure that follows is expensive: a session inherits a stale header,
believes something is broken, and either redoes finished work or hunts a bug
that was fixed two sessions ago.

**Corollary, and it cuts the other way:** a stale entry can still have been
right. Currency and soundness are different properties. Do not treat "out of
date" as "discredited" — check what it claimed before discarding it.

## Procedure

### 1. Verify against the tree, never the headers

For each open item, find the thing it claims and check it:

- claims code is missing → grep for the symbol
- claims a file is absent → look
- claims a step is unrun → check for its output
- claims a number → find the script or record that produced it

Do not accept a header's own summary of itself as evidence.

### 2. Check both forms of drift

**Staleness** is wrong text. An entry describes a state the tree has moved past.

**Orphaning** is missing text. A document exists but nothing points at it, so a
session that reads the entry point never learns it exists. This is harder to
catch because nothing looks incorrect — the record simply has a hole.

Confirm every document under `docs/` and any analysis directory is reachable
from the entry point. If the project has no document index, that is the finding.

### 3. Respect the precedence order

Where an evidence log and a handoff disagree, **the evidence log wins** and the
handoff is what gets corrected. Never the reverse. An evidence log is where
measurements are recorded; a handoff is a working summary of them.

### 4. Correct in the same commit as the discovery

Deferring is how drift accumulates in the first place. Fix each finding as you
find it, with the reason recorded.

## What to report

- items closed in the tree but open in the record
- items whose stated cause has been fixed but whose conclusion still holds
  (keep the conclusion, correct the mechanism)
- documents unreachable from the entry point
- claims in any public-facing file that the record no longer supports

For the last category, be specific about which claim and which record
contradicts it. A public document is the one place drift does real damage.

## What not to do

Do not open new work. This is a reconciliation pass. If it surfaces something
that needs doing, file it and stop.
