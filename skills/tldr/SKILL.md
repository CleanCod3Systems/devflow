---
name: tldr
description: TL;DR answers with fixed, emoji-tagged sections. Two modes — (1) no arguments, summarize the current session state (What we did, Where we are, Next steps, Your call, Recommendation); (2) with a question, answer it briefly (TL;DR, Details, Unverified, Your call, Recommendation). Use when the user invokes tldr, asks "where are we?", "what's left?", "sum it up", "what do I need to decide?", wants to wrap up or resume a long session, or asks a concrete question and wants the answer in TL;DR form.
---

# TL;DR

## Why this exists

The user wants to understand fast and decide. Whether it is the state of a long session or
the answer to a specific question, they need the conclusion on top, the supporting detail
right below, and what is on them. Being **exact and short** matters more than being
complete: anything that does not help them decide or act is noise.

## Pick the mode

- **Session mode** — invoked with no arguments, or the request is about the state of the
  work ("where are we?", "sum up the session", "let's wrap up").
- **Question mode** — a concrete question comes as an argument or in the message
  ("which tables will we touch?", "why did payment X fail? tldr").

When in doubt, a concrete question wins: question mode.

## Rules for both modes

1. **Language.** Answer in the user's language — the language of their message, unless
   their own instructions say otherwise. The templates below are in English: translate the
   headings, keep the emoji.
2. **Separate verified from assumed.** The user decides based on this; a false "done" or an
   invented fact is expensive. If something was not checked, say so.
3. **Every heading keeps its emoji**, as in the templates: they make the answer scannable.
4. **Your call**: only decisions that truly belong to the user (scope, approving a
   commit/push/deploy/data change, choosing between options with real trade-offs). Phrase
   them as questions with options. If there are none, write "Nothing for now." — never
   invent decisions.
5. **Recommendation**: one clear position, not a menu. If it answers a "Your call"
   question, say which option and why.
6. **Length**: fit on one screen (~15–30 lines). Small topic, small summary: never pad
   sections to make them look full. No flattery or celebratory prose.

---

## Session mode

### How to build it

- **Rebuild it from the actual conversation**: files edited, commands run, test/build
  results, open questions, requests not yet fulfilled.
- **Do not run anything new** (no tests, queries, or git). This is a snapshot, not a
  continuation of the work. If a key fact is missing, list it as a next step.

### Template

```markdown
## 📌 TL;DR
<1–2 lines: the essence. Anything blocking or risky goes here.>

### ✅ What we did
- <Concrete fact, with `file:line` or command> — <result / evidence>

### 📍 Where we are
<1–3 lines: what works, what is half-done, what still needs verification.>

### 👣 Next steps
1. <Concrete action, in order>

### 🤔 Your call
- <A or B?>

### 💡 Recommendation
<What I would do and why, 1–3 lines.>
```

- **What we did**: only what actually happened in the session, ~6 bullets max, grouping
  minor items.
- **Next steps**: concrete actions ("run the test suite of the `api` module"), not vague
  intentions ("check stuff").

### Example

```markdown
## 📌 TL;DR
The double-charge fix is in and tests pass; it needs your OK to commit.

### ✅ What we did
- Root cause: `payment-service:142` did not check whether the transaction already existed.
- Idempotency guard in the shared `charge` function — covers all 3 callers.
- Payment module test suite → 48/48 OK.

### 📍 Where we are
Fix done and tested locally. Not tried against the staging environment.

### 👣 Next steps
1. Commit on branch `fix/double-charge`.
2. Try it in staging with a real booking.

### 🤔 Your call
- Commit now, or test in staging first?

### 💡 Recommendation
Commit on the branch and test in staging before opening the PR: the change is small and
the tests cover the case.
```

---

## Question mode

### How to build it

1. **Answer first from what is already in the conversation** (agreed plan, files read,
   results obtained).
2. **If information is missing, investigate read-only**: read code, grep, read-only
   queries. Never write, migrate, commit, or run anything with side effects to answer: the
   question asks for information, not action.
3. **Cite the source of every fact** in Details (`file:line`, table, query). Anything
   inferred rather than checked goes under "Unverified".

### Template

```markdown
## 📌 TL;DR
<The direct answer in 1–2 lines.>

### 📋 Details
<The concrete facts behind the answer. Use a table when several items share the same
attributes (tables/columns, files/changes, endpoints/methods); a list otherwise.>

### ⚠️ Unverified
- <Assumption or unchecked fact, and how to check it.> ("None" if everything is verified.)

### 🤔 Your call
- <A or B?>

### 💡 Recommendation
<What I would do and why, 1–3 lines.>
```

### Example

Question: *"which tables will we touch and which columns get added?"*

```markdown
## 📌 TL;DR
**2 tables** change: `payment_transaction` gets 2 columns and `booking` gets 1. Nothing is dropped.

### 📋 Details
| Table | New column | Type | Purpose | Source |
|---|---|---|---|---|
| `payment_transaction` | `gateway_reason` | text | real decline reason | `migration-012:3` |
| `payment_transaction` | `attempt_number` | integer | number the retries | `migration-012:4` |
| `booking` | `payment_status` | text | payment state in the admin panel | `booking-model:58` |

### ⚠️ Unverified
- Size of `payment_transaction` in production: if it is large, the schema change may lock the
  table. Check its row count first.

### 🤔 Your call
- `payment_status` with a default value, or nullable?

### 💡 Recommendation
Nullable: the schema change is faster and old rows do not need a backfill.
```
