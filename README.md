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
```

Versions are omitted from the manifests deliberately — for a marketplace hosted
in git, every commit is treated as a new version, which is the right setup for
something under active development. Pin a `version` field only once a plugin
stabilises.

## Licence

Apache-2.0.
