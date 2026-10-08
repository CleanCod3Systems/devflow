---
name: ask
description: Read-only question mode. The user invokes it as /ask <question> when they want an answer and a guarantee that nothing gets modified — no code, files, git, databases, tickets, messages, or external services. Investigates with read-only tools only and answers in TL;DR form.
disable-model-invocation: true
disallowed-tools: Edit, Write, NotebookEdit, Agent, Workflow
---

# /ask — ask without touching anything

The user asked a question and wants **only the answer**. This invocation forbids any action
that creates, edits, deletes, or sends anything: code, files, databases, git, tickets,
messages, artifacts, configuration. Not even "an obvious little fix".

Treat this as a hard rule, not a preference. In Claude Code (installed as the `devflow`
plugin) it is also enforced: a hook blocks every non-read-only tool call while the user's
latest message is an `/ask`. If a call is blocked, **do not look for another way to do it**:
that is exactly what the user wanted to prevent.

## Allowed

- Reading files and searching code (read tools, `grep`, `find`, `ls`, `cat`…).
- Read-only git: `status`, `log`, `diff`, `show`, `blame`.
- `SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` against connected databases.
- Read-only integrations (tools that `get`, `list`, `search`, `read`, `fetch`…).
- Web and documentation search.

## How to answer

1. Answer first from what is already in the conversation.
2. If information is missing, investigate read-only and cite the source of every fact
   (`file:line`, table, query, URL).
3. If the answer implies something should change, **describe it** as a proposal under
   "Your call" or "Recommendation". The user will ask for it later, outside `/ask`.
4. Answer in the user's language — the language of their question, unless their own
   instructions say otherwise. Translate the headings below, keep the emoji. No flattery.

```markdown
## 📌 TL;DR
<The direct answer in 1–2 lines.>

### 📋 Details
<The concrete facts behind it, with sources. A table when several items share the same
attributes; a list otherwise.>

### ⚠️ Unverified
- <Assumption or unchecked fact, and how to check it.> ("None" if everything is verified.)

### 🤔 Your call
- <A or B?> ("Nothing for now." if none.)

### 💡 Recommendation
<What I would do and why, 1–3 lines. Changes are proposed, never made.>
```

For a trivial question, TL;DR and Details are enough: never pad empty sections.
