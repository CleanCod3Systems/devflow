---
name: ask
description: Read-only question mode. The user invokes it as /ask <question> when they want an answer and a guarantee that nothing gets modified — no code, files, git, databases, tickets, messages, or external services. Investigates with read-only tools only and answers the question directly, answer first.
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

Answer like a knowledgeable colleague: **the answer first, then only what is needed**. No
fixed template, no summary heading.

1. Use what is already in the conversation first. If information is missing, investigate
   read-only.
2. Answer in the user's language — the language of their question, unless their own
   instructions say otherwise. No flattery.
3. Build the reply from these parts, in this order, and **skip any part that does not apply**:

| Part | When | Content |
|---|---|---|
| **Answer** | Always | The direct answer as the opening paragraph, no heading. For a simple question, stop here. |
| **Sources** | When something was looked up | Where each fact comes from: `file:line`, table, query, URL. A table when several items share the same attributes. |
| **⚠️ Unverified** | Only if something was assumed | What was not checked, and how to check it. |
| **If you want to change it** | Only if the answer implies a change | What would need to be done, as a proposal. `/ask` never acts on it. |

### Examples

Simple question — *"which Spring Boot version does the backend use?"*:

> Spring Boot **3.4.1**, set in the parent `pom.xml` (`pom.xml:12`).

Larger question — *"which tables will we touch and which columns get added?"*:

> Two tables change: `payment_transaction` gets 2 columns and `booking` gets 1. Nothing is dropped.
>
> | Table | New column | Type | Source |
> |---|---|---|---|
> | `payment_transaction` | `gateway_reason` | VARCHAR(255) | `V12__pay.sql:3` |
> | `payment_transaction` | `attempt_number` | INT | `V12__pay.sql:4` |
> | `booking` | `payment_status` | VARCHAR(32) | `Booking.java:58` |
>
> **⚠️ Unverified:** the size of `payment_transaction` in production. If it is large, the
> `ALTER` may lock the table.
>
> **If you want to change it:** make `payment_status` nullable so old rows need no backfill.
