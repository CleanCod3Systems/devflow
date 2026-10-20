---
name: adr
description: Record a decision that had real alternatives as an Architecture Decision Record (minimal MADR plus a one-line Y-statement). Detects the project's ADR folder and numbering (docs/adr, doc/adr, docs/decisions, adr-tools), keeps the index up to date, links superseded decisions both ways, and shows the diff without committing. Refuses trivial or freely reversible decisions, and points decisions that span several repos to the shared knowledge base the project defines. Use when the user invokes adr, asks to "record this decision", "write an ADR", "document why we chose X", or a session just settled a choice between real options.
argument-hint: "<decision>"
---

# ADR

## Why this exists

Months later nobody remembers why the code is the way it is, and the same debate starts
again. An Architecture Decision Record keeps the context, the options that were really on
the table, the choice, and what it costs — in the repo, next to the code it explains. This
skill writes a short one in the [MADR](https://adr.github.io/madr/) shape, with a one-line
Y-statement on top so the decision reads in a single sentence.

**Never commit.** Create or edit the files, show the diff, and leave them in the working tree.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The ADR is written in that language too, unless the existing
ADRs use another one.

## 1. Does it deserve an ADR?

Record it only when there were **real alternatives** and the choice is costly to undo: a
library, a data model, a protocol, a boundary between services, a security or deploy
approach. A trivial decision, or one that can be reverted at no cost (a variable name, a log
level, a refactor inside one function), does not: say so in one line ("Not worth an ADR:
<reason>.") and do not create a file.

If the decision is still open, it is not an ADR yet: say so, or record it as `proposed` only
if the user asks.

## 2. Does it belong in this repo?

If the decision spans several repos, or belongs to none (an organisation-wide practice, a
contract between teams), do not force it into one repo. Say it belongs in the shared memory
or knowledge base the project defines in its agent instructions (`AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, or similar). If those instructions name a tool or command for recording
decisions, propose using it with the same content. If they name nothing, say so and ask where
it should live. Do not create the file in this repo unless the user insists.

## 3. Find the convention

1. Look for an existing ADR location: `docs/adr/`, `doc/adr/`, `docs/decisions/`,
   `docs/architecture/decisions/`, an `.adr-dir` file at the root (adr-tools writes the folder
   there), or a rule in the agent instructions. Follow what exists: folder, file naming,
   numbering width and template. With nothing in place, use `docs/adr/NNNN-slug.md`.
2. **Number:** the highest existing number + 1, with the same zero padding (`0001` by
   default). Slug in lowercase kebab-case, a few words.
3. **Index:** if the folder has an index (`README.md` or `index.md` listing the ADRs), update
   it. With the first ADR in a new folder, create `docs/adr/README.md` with the table below.

## 4. Write the ADR

If the context, the options or the chosen one are not clear from the conversation, ask once,
all together, at most 3 questions. Then write, in this shape:

```markdown
# NNNN. <Decision title: what was decided, in a few words>

> In the context of <situation>, facing <concern>, we decided for <option> and against
> <other options>, to achieve <goal>, accepting <downside>.

- **Status:** proposed | accepted | superseded by [NNNN](NNNN-slug.md) | deprecated
- **Date:** YYYY-MM-DD

## Context
<2–5 lines: the forces at play, what makes a decision necessary now. Facts, with sources.>

## Decision
<1–3 lines: what we will do.>

## Considered options
### <Option A — chosen>
- 👍 <pro>
- 👎 <con>

### <Option B>
- 👍 <pro>
- 👎 <con>

## Consequences
- <What becomes easier, what becomes harder, what we must do or watch next>
```

Rules:
1. **Real options only.** At least two, each one something that was actually considered. Do
   not invent a straw man to make the choice look obvious.
2. **Status:** `accepted` when the user or the session settled it; `proposed` when it still
   needs someone's approval. Today's date unless the user gives another.
3. **Grounded.** Facts in the Context (numbers, limits, incidents) come from what was read or
   run in the session, with a link or `file:line`. Anything assumed is marked as assumed.
4. **One screen.** ~40 lines. Context and consequences are short; the detail lives in the
   code, the PR or the linked spec.
5. If the existing ADRs use a different template (Nygard, full MADR), follow theirs, keeping
   at least the Y-statement, options and consequences.

## 5. Superseding a decision

When the new ADR replaces an earlier one:

1. In the old ADR, set `Status: superseded by [NNNN](NNNN-slug.md)`. Change nothing else in it.
2. In the new ADR, add `- **Supersedes:** [MMMM](MMMM-slug.md)` under Status.
3. Update both rows in the index.

## 6. Index

```markdown
# Architecture Decision Records

| # | Decision | Status | Date |
|---|---|---|---|
| [0001](0001-use-postgres-for-bookings.md) | Use PostgreSQL for bookings | accepted | 2026-03-02 |
```

## 7. Close

Show what changed and the diff (`git diff` for edited files; for new files, which `git diff`
does not show, `git diff --no-index /dev/null <file>`):

```markdown
🧭 **ADR NNNN:** `<path>` — <status> · <supersedes MMMM, if any> · index updated.

<diff>
```

## Example

Request: *"record that we went with a queue for refund retries"*, after a session comparing a
cron job and the existing job queue:

```markdown
# 0007. Retry failed refunds through the job queue

> In the context of refunds failing on gateway timeouts, facing ~30 manual retries a week,
> we decided for delayed jobs on the existing queue and against a cron sweep, to retry within
> minutes with one idempotency key, accepting that retries depend on the queue being healthy.

- **Status:** accepted
- **Date:** 2026-10-20

## Context
Support retries ~30 timed-out refunds by hand each week (ticket PAY-412). The project already
runs a job queue with delayed jobs (`jobs/queue.py:14`).

## Decision
Each timed-out refund schedules up to 3 delayed retry jobs, 5 minutes apart, reusing its
idempotency key.

## Considered options
### Delayed jobs on the existing queue — chosen
- 👍 Retries in minutes; no new infrastructure.
- 👎 A queue outage also stops retries.

### Cron sweep every 15 minutes
- 👍 Simple; independent from the queue.
- 👎 Up to 15 minutes of delay; needs a lock against overlapping runs.

## Consequences
- Queue health now affects refunds: add the retry jobs to the queue dashboard.
- Spec: [2026-10-20-refund-retry](../specs/2026-10-20-refund-retry.md).
```
