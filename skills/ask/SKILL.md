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
- Read-only database queries (no inserts, updates, deletes, or schema changes).
- Read-only integrations (tools that `get`, `list`, `search`, `read`, `fetch`…).
- Web and documentation search.

## How to answer

Answer like a knowledgeable colleague: **the answer first, then only what is needed**. No
fixed template, no summary heading.

1. **List the questions first.** A message often holds more than one question ("what does it
   send, and is it the same in the other API?"). Split it into its distinct questions before
   investigating; each one gets an answer, or is named in ⚠️ as not answered and why.
   Answering a neighbouring question instead of the one asked counts as not answered.
2. Use what is already in the conversation first. If information is missing, investigate
   read-only.
3. **Separate what you saw from what you concluded.** A fact you read or ran goes with its
   source. A conclusion drawn from it is marked as inferred. "Not found" is never proof of
   absence: say where you searched (which files, folders, repos, or queries).
4. Answer in the user's language — the language of their question, unless their own
   instructions say otherwise. No flattery.
5. Build the reply from these parts, in this order, and **skip any part that does not apply**:

| Part | When | Content |
|---|---|---|
| **Answer** | Always | The direct answer as the opening paragraph, no heading. With several questions, one short answer per question, in the order they were asked. For a simple question, stop here. |
| **Sources** | When something was looked up | Where each fact comes from: `file:line`, table, query, URL. A table when several items share the same attributes. |
| **⚠️ Unverified** | If something was inferred, assumed, or left unanswered | What was not checked or not answered, and how to check it. |
| **If you want to change it** | Only if the answer implies a change | What would need to be done, as a proposal. `/ask` never acts on it. |

### Examples

Simple question — *"which framework version does the backend use?"*:

> Version **3.4.1**, pinned in the root build file (`build-config:12`).

Larger question — *"which tables will we touch and which columns get added?"*:

> Two tables change: `payment_transaction` gets 2 columns and `booking` gets 1. Nothing is dropped.
>
> | Table | New column | Type | Source |
> |---|---|---|---|
> | `payment_transaction` | `gateway_reason` | text | `migration-012:3` |
> | `payment_transaction` | `attempt_number` | integer | `migration-012:4` |
> | `booking` | `payment_status` | text | `booking-model:58` |
>
> **⚠️ Unverified:** the size of `payment_transaction` in production. If it is large, the
> schema change may lock the table.
>
> **If you want to change it:** make `payment_status` nullable so old rows need no backfill.
