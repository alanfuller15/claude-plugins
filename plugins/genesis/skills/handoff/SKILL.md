---
name: handoff
description: Close out a working session so the next one can resume from disk rather than from conversation history. Use when context is running high, when stopping for the day, or before switching tasks. Writes durable state, commits, and records the residue that documents do not already capture.
---

# Close the session

The goal: **a fresh session with no memory of this conversation can pick up
exactly where this one stopped.** If that is not true when you finish, the
handoff is not done.

## Procedure

### 1. Land the work

Write results to the durable records before anything else. Nothing that matters
should exist only in the conversation.

- measurements and their bounds → the evidence log
- state changes, open items, decisions → the status/handoff file
- anything public-facing that a finding invalidated → fix it now

Commit. A finding that is not committed did not happen.

### 2. Verify the tree is clean

Working tree clean, local in sync with the remote, the project's own
verification gate passing. If any of those is false, either fix it or record
explicitly why it is being left that way.

### 3. Write the residue

The records capture conclusions. What they systematically lose is **the
reasoning that produced them** — and that is exactly what compaction destroys.

Write a short handoff note covering only what is *not* already in the
documents:

- what was in flight when the session ended, and what the next step was
- why a decision went the way it did, where the record shows only the outcome
- anything learned that shaped a choice but never became a formal entry
- constraints that silently forced a method (a missing tool, a rate limit, an
  unavailable corpus) — these read as choices later unless named
- threads noticed and deliberately not pulled

Be specific about anything a later session would otherwise have to rediscover.

### 4. Name the next action

One line. What the next session should do first, and what it needs in hand to
do it. If the next step is blocked, say what unblocks it.

## The test

Read your own handoff as if you had never seen this project. If you would have
to ask a question to proceed, answer it now.

## What not to do

- Do not summarise the conversation. The transcript is snapshotted; a retelling
  adds nothing and buries the residue.
- Do not start new work to "finish something first." Stopping mid-task with a
  clear note beats stopping after a rushed one.
