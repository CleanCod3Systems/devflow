---
name: debug
description: Diagnose and fix a bug or a slowdown by first building one command that reproduces it (a failing test, a curl, a browser script, a replayed request), then testing 3–5 ranked, falsifiable hypotheses one at a time, fixing the cause, and locking it with a regression test. Never guesses a cause before the bug reproduces. Use when the user says "debug", "diagnose", "why does this fail", "it's broken", "it throws", "it got slow", pastes an error, a stack trace, a curl or a screenshot of a bug and wants it fixed.
---

# Debug

## Why this exists

A bug is found by a **red loop**: one command that fails on this bug and passes once it is
fixed. With it, the cause falls out of a few measured experiments. Without it, reading code
and guessing produces plausible fixes for a different bug. Most of the effort goes into
Step 1.

**Scope.** It edits code to fix the cause and may add temporary debug logs. It never commits
or pushes, and it never writes to a production system: against production, only read-only
queries and logs. A fix that changes behavior beyond the bug waits for the user's OK.

**Redact** every secret in commands and outputs you show (`<REDACTED>`); keep tokens in
environment variables, not in the loop's text.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The report template is in English: translate the headings,
keep the emoji.

**Not this skill:** a test that fails or passes without a real bug → `tests-audit`. Review
of a finished change → `changes-review`. A project skill that debugs its own stack (for
example one for a specific framework) wins over this one for that stack.

## Step 1 — Build a red loop

Pick the first that reaches the bug:

1. **Failing test** at the seam that reaches the bug (unit, integration, end to end).
2. **HTTP script**: the user's curl, or a new one, against a running dev or test server.
3. **Browser script** (Playwright or similar) that drives the UI and asserts on the screen,
   the console or the network — the usual loop for a bug shown in a screenshot.
4. **Replay**: save a real request, payload or log line to a file and run it through the
   code path alone.
5. **Differential**: the same input through the last good and the current version (or two
   configs), and diff the outputs. Between two known commits, automate it with
   `git bisect run`.
6. **Human loop**, last resort: when only the user can click, give one instruction at a
   time and ask for the exact observation after each.

Then make it **tight**: faster (skip unrelated setup), sharper (assert the user's exact
symptom, not "did not crash"), deterministic (pin time, seed, data). For a flaky bug, raise
the reproduction rate (repeat 100×, add load) until it is debuggable.

**Done when** you can show one command, already run, that goes red on the user's exact
symptom, gives the same verdict every run, and runs in seconds without the user.

If no loop is possible, stop: list what you tried and ask for one thing — access to the
environment that fails, a captured artifact (log, HAR, request, screen recording with
times), or permission to add temporary logging. Do not hypothesize without a loop.

## Step 2 — Reproduce and shrink

Run the loop and confirm it shows the **user's** failure, not a nearby one. Then cut inputs,
data, config and steps one at a time, rerunning after each cut. Done when every element
left is needed: removing any one turns the loop green.

## Step 3 — Rank hypotheses

Write 3–5 hypotheses, most likely first, each with its prediction: "If X is the cause,
then changing Y makes the bug disappear." A hypothesis without a prediction is discarded.
Show the list to the user before testing — they often know one is already ruled out — and
continue with your ranking if they do not answer.

## Step 4 — Test one variable at a time

Each probe tests one prediction. Prefer a debugger or REPL; otherwise targeted logs at the
boundary that separates two hypotheses, each tagged with one prefix (`[DEBUG-a4f2]`) so
cleanup is one search. For a slowdown, measure a baseline first (timer, profiler, query
plan) and compare against it; logs rarely explain slowness.

## Step 5 — Fix and lock it

1. Turn the shrunk repro into a regression test at a seam that runs the real bug path. If
   no such seam exists, say so: that is a finding, not a reason to write a shallow test.
2. Watch the test fail.
3. Apply the smallest fix at the cause, not at the place that crashes.
4. Watch the test pass, then rerun the original loop from Step 1.

## Step 6 — Clean up

- The original loop is green; the regression test passes, or the missing seam is stated.
- No `[DEBUG-` prefix left (search for it); throwaway scripts deleted.
- The confirmed hypothesis is in the report, ready for the commit or PR message.

## Report format

```markdown
📌 **Cause:** <one line: what was wrong and where, `file:line`>

🔁 **Loop:** `<command>` — red before the fix, green after

🔬 **Evidence**
- <hypothesis confirmed, with the probe that proved it>
- <hypotheses ruled out, one line each>

🛠️ **Fix:** <what changed, `file:line`> · 🧪 **Regression test:** <path, or why there is no seam>

⚠️ **Not verified:** <what remains inferred, and how to confirm it>
```

Omit ⚠️ when everything was reproduced.
