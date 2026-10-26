---
name: spec
description: Spec-first for non-trivial tasks. Before any code, writes a one-screen spec (Problem, For whom, Acceptance criteria, Out of scope, Constraints, Open questions) with a measurable finish line after asking a few clarifying questions at once, saves it in the repo (docs/specs/ or the project's own convention), and offers to plan it with stepwise. Refuses to write a spec for small bugs or one-line changes. Use when the user invokes spec, asks to "write a spec", "spec this out", "define what done means before coding", "let's agree on scope first", starts a non-trivial feature or change whose scope is still fuzzy, or asks to optimize, improve or perfect something without a target — the spec is what stops endless improvement rounds.
argument-hint: "<goal>"
---

# Spec

## Why this exists

Agents start coding before anyone agreed on what "done" means, and the scope grows while they
work. A short spec written first fixes that: what problem we solve, how we will know it is
solved, and what we will not touch. This is the **spec-first** level of Spec Driven
Development described by Birgitta Böckeler
([martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)):
one spec per task, written before the code — not a parallel tree of plans, research notes,
data models and task lists. The plan is `stepwise`'s job.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The spec is written in that language too. Headings below are
in English: translate them, keep the emoji.

## 1. Is a spec worth it?

Write a spec only for non-trivial work: several files or modules, a behavior change other
people must agree on, or scope that is still fuzzy. A small bug, a one-line change, a rename
or a config tweak does not need one — a spec there is a sledgehammer to crack a nut. Say so
in one line ("This does not need a spec: <reason>.") and offer to just do it, or to plan it
with `stepwise` if it has several steps. Do not create a file.

**Open-ended improvement requests always get a spec**, even when the code change is small:
"optimize", "improve", "clean up", "make it perfect", "best practices everywhere". Without a
finish line, each session finds a new round of improvements and the work never ends. The spec
is that finish line.

## 2. Read before asking

1. Read the repo's agent instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or similar):
   they are the project's constitution, and the spec's Constraints link to them instead of
   copying them.
2. Read the code the goal touches, enough to name real files and behavior. Do not narrate
   the exploration.
3. **Detect where specs live.** Look for an existing convention: a specs folder
   (`docs/specs/`, `specs/`, `docs/rfcs/`, `docs/design/`, spec-kit's `.specify/`) or a rule
   in the agent instructions. Follow it, including its file naming. With no convention, use
   `docs/specs/<date-or-ticket>-<slug>.md` — date as `YYYY-MM-DD`, or the ticket id if the
   user gave one; slug in lowercase kebab-case, a few words.
4. **Look for earlier work on the same area**: specs and ADRs in those folders, and
   `git log --oneline -- <paths>`. If an earlier spec already covered it and its criteria were
   met, say so with the evidence and ask what changed before writing a new one. Do not
   re-propose what was already done.

## 3. Clarify once

Ask everything at once, in a single message, before writing:

```markdown
❓ **Before I write the spec:**
1. <question> — <the options, if there are any>
2. <question>
```

- **3–5 questions at most**, only the ones whose answer changes the spec (scope, acceptance,
  a constraint). Anything you can answer by reading the code, read instead of asking.
- **Two things are never guessed:** who the result is for, and how we will know it is done.
  If the conversation does not say, they are the first questions — e.g. "Who is it for: you,
  the support team, customers?" and "Which number tells us it is done: load time, error
  count, a test passing?".
- **Disagree with evidence.** If the request rests on something the code or data contradicts,
  say so in the questions, with the source, instead of writing a spec around it.
- If nothing blocks the spec, skip this step. Unanswered questions that do not block it go to
  Open questions.
- Wait for the answers, then write. Do not ask again while writing.

## 4. Write the spec

Save it at the path from step 2, in this shape and nothing else. It must fit on one screen
(~40 lines).

```markdown
# <Title: what changes, in a few words>

## 🎯 Problem
<2–4 lines: who has the problem, what happens today, why it matters now.>

## 👤 For whom
<Who uses or reads the result, and what they will do with it — one line.>

## ✅ Acceptance criteria
- [ ] <Observable, checkable result: a test passing, a command output, a UI state, a row count>

## 🚫 Out of scope
- <What this work will not do, even if it is related>

## 📏 Constraints
- <Rule from [AGENTS.md](../../AGENTS.md) or CLAUDE.md that applies — link, do not copy>
- <Compatibility, data, performance or dependency limit>

## ❓ Open questions
- <Question> — <who answers it> ("None" if none)
```

Rules:
1. **Acceptance criteria are verifiable.** Each one is something a tool or the user can check
   later — `stepwise` uses them as its "done when". "Works well", "is fast" or "clean code"
   are not criteria; "refund retries stop after 3 attempts (test `test_refund_retry`)" is.
   For an improvement, at least one criterion is a number with today's value and the target,
   measured the same way both times: "home page load 3.4 s → under 2 s (Lighthouse, mobile)".
   If the user has no target, measure today's value and propose one. "Optimized" or
   "perfect" is never a criterion.
2. **Done means done.** When every criterion is met, the work is finished. More improvement is
   a new spec with a new reason, not another round of the same one.
3. **Out of scope is never empty.** Name what someone would reasonably expect and will not
   get. It is the plan's limit.
4. **Grounded.** Every file, endpoint, table or command named in the spec was read or checked.
   Unknowns go to Open questions, not into the spec as guesses.
5. **No solution design.** The spec says what and why, not how. No plan, task list or data
   model sections: those belong to `stepwise` and the code.
6. **Never commit.** Create the file and leave it in the working tree.

## 5. Close

```markdown
📝 **Spec:** `<path>` — <n> acceptance criteria, <n> open questions.

👣 **Next:** plan it with `stepwise`? Its steps will use these acceptance criteria as "done when".
```

If Open questions still block the work, say which ones before offering `stepwise`.

## Example

Request: *"spec: retry failed refunds automatically"* — after the user answered how many
retries and whether to notify the customer:

```markdown
# Automatic retry of failed refunds

## 🎯 Problem
Refunds that fail with a gateway timeout stay in `failed` and support retries them by hand,
about 30 a week. Customers wait days for money that should be back in minutes.

## 👤 For whom
Customers waiting for a refund, and the support team that today retries them by hand.

## ✅ Acceptance criteria
- [ ] A refund failing with a timeout is retried up to 3 times, 5 minutes apart (`test_refund_retry`).
- [ ] A refund failing with a decline is not retried.
- [ ] After the 3rd failure the refund stays `failed` and support gets the existing alert.
- [ ] The same refund is never sent twice to the gateway (idempotency key reused on retries).

## 🚫 Out of scope
- Retrying failed charges (only refunds).
- Changing the support alert or the admin screen.

## 📏 Constraints
- Background jobs go through the existing queue — see [AGENTS.md](../../AGENTS.md#jobs).
- No schema migration on `payment_transaction` in this change.

## ❓ Open questions
- Does the gateway accept the same idempotency key after 15 minutes? — payments team
```
