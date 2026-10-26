---
name: qa-check
description: Behavior-first QA of what you changed. Takes the expected result from the request, ticket or spec (never from the code), maps the change two caller levels out at low cost, finds which affected behavior has no test, writes and runs only the missing tests in the repo's own framework, exercises the running flow when the change reaches users, reduces each failure to a minimal reproduction, and gives a release verdict (ready / ready with risks / not ready / insufficient evidence). Never edits production code. Use when the user asks to test or QA the change, "does it actually work?", "is this ready for users?", "write the tests that are missing for this", "verify the fix for bug X", or wants evidence before releasing — next to changes-review, which reads the code instead of running the behavior.
argument-hint: "[diff|fix <defect>|plan] [file, flow or ticket to focus on]"
---

# QA check

## Why this exists

`changes-review` asks *is the code right?* and answers by reading it. This skill asks *does
the behavior match what was needed?* and answers by running it. It exists against two
failures: tests that copy the implementation (they pass because they assert what the code
does, not what it should do), and "it works" backed only by a 200, a toast, a screenshot or
a green build. The expected result always comes from the requirement; the proof always
comes from an execution.

**Scope:** only what was touched — the changed code and up to two levels of its callers.
Never the whole repository.

**What it edits:** test files only (new test files, or new cases in existing ones), left
uncommitted. Never production code, configuration, schema or data. Never commit or push.

**Not this skill:** naming, style, over-engineering, conventions → `changes-review`. A red or
green result that may be lying → `tests-audit`. Trust-boundary issues → `security-audit`. If
one of those shows up, add one line pointing there; it is not a QA finding.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The report template is in English: translate the headings,
keep the emoji.

## Modes

| Mode | When | What runs |
|---|---|---|
| `diff` *(default)* | Unpushed changes, or a branch vs its base if the user names one | Steps 1–6 |
| `fix <defect>` | A defect was fixed and needs verifying | Step 1, then the original repro on the base (must fail) and on the fix (must pass), near variants, and the L1 tests from Step 2 |
| `plan` | Nothing can be executed (no runner, no environment, no access), or the user asks for a plan | Steps 1–3; every case is reported as *not run* |

A focus argument (a file, a flow, a ticket) narrows the scope further.

## Budget — applies to every step

- **Size from the diff.** Up to 3 changed source files: at most 6 cases. 4–10 files: at most
  12. More than 10: ask one question — which flow to focus on — before Step 2.
- **Read call sites, not files.** Use LSP references if the agent has them, otherwise
  `grep -n` with word boundaries and a few lines of context. Open a whole file only when a
  caller's behavior cannot be judged from the call site.
- **Level 2 only where the change propagates** (Step 2). At most 10 callers per symbol per
  level; with more, take the ones on critical flows and say so under Coverage.
- **Run only the affected tests**, filtered by file or name. The full suite only if the repo
  offers no way to filter.
- **No subagents**, except the single verifier in Step 6 when there is a defect to confirm.
- **Reference files load only when needed:** [TECHNIQUES.md](TECHNIQUES.md) when the right
  technique is not obvious; [DEFECT-REPORT.md](DEFECT-REPORT.md) only for a defect ticket.

## Step 1 — Scope and expected behavior

1. **Changed files** — per repo:
   ```bash
   git status --porcelain
   git diff HEAD
   git log --oneline @{upstream}..HEAD
   git diff @{upstream}...HEAD
   ```
   No upstream: use `git merge-base HEAD origin/main` (or `origin/master`). Exclude
   lockfiles, generated output, vendored code, and test files (they are evidence, not scope).
   Nothing changed → "No unpushed changes in <repo>." and stop.
2. **Expected behavior (the oracle)**, from these sources in order: the user's request in the
   conversation; the ticket or PR description if given; a spec in `docs/specs/` or the
   project's spec folder (the `spec` skill's acceptance criteria are ready-made cases); the
   feature's docs. Write it as 1–5 checkable statements, each with its source.
3. **Ambiguity is not a defect.** Where the expected result cannot be determined, record a
   question for whoever owns the product. Ask the user only if it blocks the main case;
   otherwise keep going.
4. Read the repo's agent instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or similar):
   how tests run, test environment and accounts, forbidden actions.

## Step 2 — Impact map, two levels out

For every changed symbol — function, method, endpoint, component, model field, query,
event:

- **L0 — the contract change:** inputs it now accepts or rejects, what it returns, its side
  effects (writes, outgoing calls, events), the errors it raises.
- **L1 — direct users:** grep the name; for a component, its imports and usages; for an
  endpoint, its route in clients; for a model field, views, domains and computed fields.
- **L2 — users of L1, only when the change propagates:** the L1 caller passes the changed
  result on (returns, stores, renders or sends it). A caller that only logs it, ignores it,
  or fully absorbs it ends the walk there.
- **Stop at boundaries:** an HTTP API consumed elsewhere, a database schema, a queue or
  event, a cache key, another repo. Do not follow it; list it under Coverage with the
  consumer that should be checked.
- **Existing tests** for L0–L2: grep the test folders for the symbol, the module path, the
  route. Mark each behavior: *tested* (a test targets the changed behavior), *touched* (a test
  runs it but would not catch this change), or *none*.

Keep the map as a short working table. The report shows it only compressed, under Coverage.

## Step 3 — Risk and cases

1. **Rank** the affected behaviors by impact × likelihood: charges and money, data loss or
   corruption, access to someone else's data, a blocked core flow — first; cosmetic — last.
   State in one line what goes first and why.
2. **Gaps get new tests; covered behavior gets re-run.** A gap is a *none* or *touched*
   behavior from Step 2.
3. **Pick the technique the change calls for** — boundary values for limits, a decision
   table for combined conditions, transitions for statuses, a double run for anything that
   can execute twice. Only the ones this change needs.
4. **Each case:** id, the requirement or risk it covers, preconditions and data, action,
   expected result (from Step 1 — never derived from reading the implementation), and the
   **lowest layer that sees the risk faithfully**: unit < integration < API < end-to-end <
   manual.
5. Do not stop for approval, unless a case needs one of the authorizations in Step 4.

## Step 4 — Execute

**How this repo runs things:** agent instructions and README first; then configuration —
`package.json` scripts, `playwright.config.*`, vitest or jest config, `pytest.ini` /
`pyproject.toml`, Odoo `--test-tags`, `pom.xml` / `build.gradle`. Write tests in the repo's
framework, with its fixtures and naming: copy the shape of the closest sibling test.

1. **Smoke:** run one existing test of the affected area. If the environment itself fails,
   stop and report it as blocked with the error — do not design further on a broken base.
2. **Re-run** the existing L0–L2 tests, filtered.
3. **Write the missing tests and run them.** Assert observable behavior and business results;
   deterministic data; no fixed sleeps; no selectors tied to markup details; never mock the
   unit under test.
4. **Prove each new test can fail** — at least the top-risk ones: break the behavior it
   protects (invert the condition, return a wrong value), run it, it must go red. Revert and
   confirm with `git diff` that production files match the start. Same technique as
   `tests-audit` Step 4.
5. **Run the real flow only when the change reaches a user flow or an API:** the repo's
   end-to-end runner, a browser tool if the agent has one, or a request to the local server.
   Compare what the screen or response *says* with what actually *happened*: the persisted
   row (test database, read-only query), the outgoing call, the state after a reload.
6. **Status comes from the exit code**, never from output piped through `grep` or `tail`. A
   red that looks unrelated to the change → `tests-audit` before calling it a defect.

**Needs the user's explicit OK, even mid-run:** writes to shared or production systems, real
payments or charges, sending emails or messages, load tests, anything destructive or
irreversible, installing dependencies. Production databases are read-only. Test data is
identifiable (`qa-check-<date>`) and removed afterwards.

## Step 5 — Isolate failures

For every failing case:

- Reduce it to the minimal reproduction, changing one variable at a time.
- Classify it: **product defect**, **environment**, **test data**, or **the test itself**.
  Only product defects go to 🐞 Defects; the rest go under 🧪 Cases with their class.
- Record the frequency as reproductions/attempts.
- Name a possible cause only with a trace in code or logs, marked as a hypothesis.

## Step 6 — Independent confirmation

Only when there is at least one product defect, and the agent supports subagents: give one
fresh subagent **only** the reproduction steps, the expected result with its source, and the
commands — none of this session's reasoning — and ask it to reproduce each defect and to
argue that the expected result is wrong. A defect it cannot reproduce goes back to
*needs validation*. Without subagents, rerun each reproduction from a clean start yourself
and say the confirmation was not independent.

## Report format

Every part keeps its emoji; translate the labels. Omit a part with nothing to say, except
the verdict, the cases and the coverage, which are always there.

| Part | When | Content |
|---|---|---|
| 📌 **Verdict** | Always | ✅ Ready within the evaluated scope / ⚠️ Ready with risks / ❌ Not ready / ❓ Insufficient evidence — one line with the reason and the scope |
| 🐞 **Defects** | If any | One per defect: id · severity · title · minimal repro · expected (source) vs observed · reproductions/attempts |
| 🧪 **Cases** | Always | Passed / failed / blocked / not run, then one line per failed or blocked case; the command and exit code of each run that mattered |
| ➕ **Tests added** | If any | File — the behavior it protects — proved to fail when broken: yes/no |
| ❔ **Questions** | If any | Ambiguities from Step 1 and who answers them |
| 🗺️ **Coverage** | Always | How far the map reached (symbols at L0/L1/L2), contracts not followed and their consumers, what was not executed and why, whether confirmation was independent |

**Verdict rules:** ✅ only if every top-risk case ran and passed. ❌ if a product defect hits
money, data, access or a core flow. ⚠️ for lesser defects, or top risks left uncovered. ❓
when the main case could not run. No coverage percentages; never "no bugs". Release is the
product owner's call — the verdict is evidence for it.

```markdown
📌 **Verdict:** ❌ Not ready — refund retry sends the second attempt with a new idempotency key; 3 files, 7 cases.

🐞 **Defects**
- D1 · High · Retried refund gets a new idempotency key · `retry_refund(id)` twice after a
  timeout → gateway mock receives keys `k1`, `k2`. Expected the same key (spec
  `2026-10-20-refund-retry`, criterion 4). 3/3.

🧪 **Cases:** 5 passed · 1 failed (D1) · 1 not run
- C7 not run: the e2e checkout needs the payment sandbox, which is down (`curl` → 503).
- `npx vitest run src/refunds` → exit 1 (1 failed, 14 passed).

➕ **Tests added**
- `src/refunds/retry.test.ts` — same idempotency key across retries — fails when broken: yes.

🗺️ **Coverage**
- L0: `retry_refund`, `RefundJob`. L1: 3 callers. L2: 1 (admin "retry" button).
- Not followed: the `refund.retried` event — consumed by the notifications service.
- Confirmation: independent subagent reproduced D1 3/3.
```

A clean result is three lines:

```markdown
📌 **Verdict:** ✅ Ready within the evaluated scope — 2 files, 4 cases.
🧪 **Cases:** 4 passed · `npx vitest run src/cart` → exit 0.
🗺️ **Coverage:** L0 `applyCoupon`; L1 2 callers; L2 none (results not propagated). No real flow run: no UI change.
```

## After the report

- Added tests stay uncommitted; the user decides whether to keep them.
- Fixing a defect is not part of this skill: propose the fix, apply it only with the user's
  OK, then verify it with mode `fix`. If that verification cannot run in full, say
  "fix pending validation".
- For a Jira-style ticket of a defect, use [DEFECT-REPORT.md](DEFECT-REPORT.md).
