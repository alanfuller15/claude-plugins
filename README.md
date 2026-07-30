# claude-plugins

Personal [Claude Code](https://code.claude.com) plugins. Workflow machinery
extracted from real projects, after the friction was measured rather than
guessed at.

## Install

```
/plugin marketplace add alanfuller15/claude-plugins
```

Then install what you want:

```
/plugin install genesis@alanfuller15-tools
/reload-plugins
```

## Plugins

### [`genesis`](plugins/genesis/) — session continuity and verification

Four hooks, four skills, one agent. Injects durable state at session start,
snapshots transcripts before compaction, runs the project's own verification
gate before a turn can end, and blocks writes outside the project. The skills
are the same discipline by hand: reconciling the record against the tree, fixing
a decision rule before measuring, closing a session so the next one resumes from
disk, and checking "this needs inventing" against the field before designing it.

Ships no project knowledge. Everything it reads is a file your repo optionally
provides, so it works unchanged across a Python research repo and a static web
app.

## Local development

```
/plugin marketplace add ./claude-plugins
/plugin install genesis@alanfuller15-tools
```

Or load without installing:

```
claude --plugin-dir ./claude-plugins/plugins/genesis
```

### The gate

```
bash .claude/verify.sh
```

Manifest validation, a syntax check on every hook script, and the write guard's
test suite — about 1.7s. This is `genesis`'s own convention applied to the repo
that ships it: `.claude/verify.sh` is the path the `Stop` hook looks for, so
with the plugin installed here, **a turn that leaves the tree dirty cannot end
while this fails.**

It was added in 1.0.1, later than it should have been. This repo published a
plugin arguing that projects should declare a gate while declaring none itself,
and that gap has a name now: the Windows bug in the write guard reached a user
because nothing here ran the guard against anything before it shipped.

The gate deliberately does **not** check that the plugin version was bumped.
The bump correctly comes last, so such a check would fail every turn of the
work leading up to it — failing for a reason the turn cannot yet fix, which is
how a gate teaches people to skip it. `claude plugin tag` checks that at
release time, which is where it belongs.

`genesis` pins a `version` in its `plugin.json`, and **it must be bumped on
every release** — Claude Code compares on that field to decide whether an
install is stale, so an unbumped change never reaches anyone who already has
the plugin. This README previously said versions were omitted deliberately, on
the reasoning that every commit to a git-hosted marketplace is its own version.
That was wrong, and it was wrong in the direction that costs a user a fix they
have already been told exists. See
[the release rule](plugins/genesis/README.md#releasing).

## Licence

Apache-2.0.
