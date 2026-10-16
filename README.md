# devflow

Everyday checkpoints for coding agents, packaged as portable [Agent Skills](https://agentskills.io).

| Skill | What it does |
|---|---|
| `tldr` | Summarizes the session (what we did, where we are, next steps, your call, recommendation) or answers a question in short, sectioned form. |
| `ask` | Read-only questions: the agent investigates and answers, but never creates, edits, deletes, or sends anything. Hook-enforced in Claude Code. |
| `changes-review` | Reviews your **unpushed** changes through seven lenses (needed?, bugs, over-engineering, conventions, blast radius, gaps, DB/deploy risk), runs the tests, applies safe fixes, and proposes the risky ones. |
| `stepwise` | Plans work in short numbered steps (who does each, when it is done), executes one step at a time with a status board, answers side questions briefly and always returns to the current step. |
| `tests-audit` | Tells whether a test result can be trusted: separates real regressions from false reds (load, ports, stale caches, lost exit codes) and false greens (tests that would not catch the bug). Proposes fixes, never retries or loosens tests to turn them green. |
| `focus` | Answer-first replies for readers who need to act fast (ADHD-friendly): next action first, numbered steps, no filler, one next action at the end, a short evidence block only when closing a task. Per session with `/focus`, or always on (see [Focus everywhere](#focus-everywhere)). |
| `security-audit` | Source-first security audit that reports only real trust-boundary failures, each one challenged by a fresh agent and sorted into confirmed / needs validation / rejected. `diff` scope (default) checks your unpushed changes; `full` audits the whole repo with many agents and is expensive. Never edits your code. |

Skills are written in English and **answer in your language**: they reply in the language
you write in (or the one your agent instructions set).

## Install

Skills are installed by the **agent** you use, and work with whatever model that agent runs.

### Any agent (skills CLI)

```bash
npx skills add CleanCod3Systems/devflow
```

Installs the skills into the agents it detects on your machine. Add `--skill <name>` to pick
one, or `--list` to see them first.

### Claude Code

```text
/plugin marketplace add CleanCod3Systems/devflow
/plugin install devflow@devflow
```

Use `/devflow:tldr`, `/devflow:ask <question>`, `/devflow:changes-review`, `/devflow:stepwise <goal>`, `/devflow:tests-audit`, `/devflow:security-audit [diff|full]`, `/devflow:focus`. This is the only
install that enforces `ask` with a hook (see below).

### Codex

```bash
codex plugin marketplace add CleanCod3Systems/devflow
codex plugin add devflow@devflow
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add CleanCod3Systems/devflow
copilot plugin install devflow@devflow
```

### Gemini CLI

```bash
gemini extensions install https://github.com/CleanCod3Systems/devflow
```

The skills under `skills/` are discovered automatically.

### OpenCode

```bash
npx skills add CleanCod3Systems/devflow -a opencode        # this project
npx skills add CleanCod3Systems/devflow -a opencode -g     # every project
```

Or copy the folders under `skills/` into `.opencode/skills/` (one project) or
`~/.config/opencode/skills/` (every project). OpenCode also loads skills from
`~/.claude/skills/` and `~/.agents/skills/`, so skills installed there for other agents
show up too. Check with `opencode debug skill`.

### Any other agent with Agent Skills support

Copy the folders under `skills/` into your agent's skills directory (for Claude Code without
the plugin: `~/.claude/skills/` or `.claude/skills/`; for others, see your agent's docs).

## About `ask` enforcement

`ask` works everywhere as a strict instruction. **Only the Claude Code plugin enforces it**,
because the guard reads Claude Code's session format:

- `disallowed-tools` removes edit/write tools while `/ask` runs.
- A `PreToolUse` hook (`hooks/claude-hooks.json` → `skills/ask/scripts/guard.py`) blocks any non-read-only tool call
  while your latest message is an `/ask`. It uses an allowlist: read tools, read-only shell
  commands (`ls`, `cat`, `grep`, `find`, read-only `git`…), read-only database queries, and
  integration tools whose names read like `get` / `list` / `search` / `read`. Everything else
  is blocked, including redirections to files, command substitution, and interpreters.

In every other install (skills CLI, Codex, Copilot, Gemini, OpenCode, manual copy), the hook does not run: `ask` then relies on
the agent following its instructions.

The guard needs `python3` on your `PATH`.

## What `changes-review` touches

It edits only files that have unpushed changes, and it backs them up first with
`git stash store` (restore with `git stash apply`). It never commits, pushes, or writes to
databases. Fixes that change behavior, contracts, schemas, or permissions are proposed and
wait for your OK.

## Focus everywhere

`/focus` turns the mode on for one session in any agent with Agent Skills. To keep it **always
on**:

- **Claude Code (plugin):** the plugin ships the same rules as an output style. Pick **focus**
  in `/config` → Output style; it is saved in your settings.
- **Any other agent:** paste [`rules/focus.md`](rules/focus.md) into the agent's always-loaded
  rules — `AGENTS.md` (Codex, OpenCode, and others), `GEMINI.md`, `.cursor/rules`,
  `.windsurf/rules`, or Copilot's instructions file.

Optional, Claude Code only — make the evidence block mandatory when a task is closed. Add this
`Stop` hook to your own `settings.json` (the plugin does not install it, so nobody gets it
unasked):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "$ARGUMENTS · if stop_hook_active is true → ok. Block ONLY if last_assistant_message closes a file change (says something was done/implemented/fixed) and has no 🔎 block with a 'Deviations' line (in any language, e.g. 'Desvíos'). Progress updates, questions, proposals, answers to doubts and recaps of earlier turns → ok. Reason: ≤10 words."
          }
        ]
      }
    ]
  }
}
```

## Credits

`focus` is adapted from [i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT).

The evidence rules in `ask` and `changes-review` (observed vs. inferred, "not found is not
absence", coverage stated explicitly) and the approach of `tests-audit` are adapted from
[REA](https://github.com/morluto/rea) (MIT), notably its `reverse-engineer-anything` and
`rea-ci-tests-audit` skills.

`security-audit` is adapted from Cloudflare's
[security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT); copied
files and the original license are listed in `skills/security-audit/NOTICE`.

## License

MIT
