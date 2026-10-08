# devflow

Everyday checkpoints for coding agents, packaged as portable [Agent Skills](https://agentskills.io).

| Skill | What it does |
|---|---|
| `tldr` | Summarizes the session (what we did, where we are, next steps, your call, recommendation) or answers a question in TL;DR form. |
| `ask` | Read-only questions: the agent investigates and answers, but never creates, edits, deletes, or sends anything. Hook-enforced in Claude Code. |
| `changes-review` | Reviews your **unpushed** changes through seven lenses (needed?, bugs, over-engineering, conventions, blast radius, gaps, DB/deploy risk), runs the tests, applies safe fixes, and proposes the risky ones. |

Skills are written in English and **answer in your language**: they reply in the language
you write in (or the one your agent instructions set).

## Install

### Claude Code (plugin, recommended)

```text
/plugin marketplace add CleanCod3Systems/devflow
/plugin install devflow@devflow
```

Then use `/devflow:tldr`, `/devflow:ask <question>`, `/devflow:changes-review`.

### Any agent that supports Agent Skills

Copy the folders under `skills/` into your agent's skills directory, for example:

| Agent | Skills directory |
|---|---|
| Claude Code (without the plugin) | `~/.claude/skills/` or `.claude/skills/` |
| Other agents | see your agent's documentation for its skills path |

## About `ask` enforcement

`ask` works everywhere as a strict instruction. **Only the Claude Code plugin enforces it**:

- `disallowed-tools` removes edit/write tools while `/ask` runs.
- A `PreToolUse` hook (`skills/ask/scripts/guard.py`) blocks any non-read-only tool call
  while your latest message is an `/ask`. It uses an allowlist: read tools, read-only shell
  commands (`ls`, `cat`, `grep`, `find`, read-only `git`…), read-only database queries, and
  integration tools whose names read like `get` / `list` / `search` / `read`. Everything else
  is blocked, including redirections to files, command substitution, and interpreters.

Installed as plain skills (without the plugin), the hook does not run: `ask` then relies on
the agent following its instructions.

The guard needs `python3` on your `PATH`.

## What `changes-review` touches

It edits only files that have unpushed changes, and it backs them up first with
`git stash store` (restore with `git stash apply`). It never commits, pushes, or writes to
databases. Fixes that change behavior, contracts, schemas, or permissions are proposed and
wait for your OK.

## License

MIT
