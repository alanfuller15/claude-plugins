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

Four hooks, three skills, one agent. Injects durable state at session start,
snapshots transcripts before compaction, runs the project's own verification
gate before a turn can end, and blocks writes outside the project.

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

Validate before pushing:

```
claude plugin validate .
claude plugin validate ./plugins/genesis
python3 plugins/genesis/tests/test_guard_writes.py
```

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
