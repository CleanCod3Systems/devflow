---
name: tests-audit
description: Find out whether a test result can be trusted. Diagnoses false reds (a test, suite, hook, or CI job fails without a real bug — load, ports, stale caches, lost exit codes) and false greens (it passes but would not catch the bug — asserts its own mock, never runs, swallowed failure). Establishes a baseline, reproduces in isolation, proves green tests can fail, and reports a classified verdict; fixes wait for the user's OK. Use when tests fail and the change seems unrelated, a suite is flaky, CI and local disagree, a check "passes" suspiciously, or the user asks whether the tests really protect something.
---

# Tests audit

## Why this exists

A test result is evidence only if it would have come out differently when the code was
wrong. Two things break that: a **false red** sends people chasing a bug that does not
exist, and a **false green** lets a real bug through. The cheap reactions — rerun until it
passes, raise the timeout, delete the assertion — hide both. This skill replaces them with a
baseline and a reproduction.

**It investigates, it does not repair.** The only edits allowed without the user's OK are
temporary perturbations in Step 4, always reverted. Fixes are proposed and wait for approval.
Never commit or push.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The report template is in English: translate the headings,
keep the emoji.

## Step 1 — Pin the baseline

Record, before running anything:

- Commit (`git rev-parse HEAD`) and whether the tree is dirty (`git status --porcelain`).
- The exact command, where it ran, and the toolchain versions that matter.
- What else was running at the same time: dev servers, builds, other test runs, and who holds
  the ports the tests need.
- What the test depends on outside the code: env files, caches (incremental build info,
  framework caches), databases, mocked or real services.

## Step 2 — Read the real result

- Take the status from the **exit code**, not from filtered output. In
  `output="$(cmd | grep …)"` the status is grep's, not the command's; the same happens with
  `| tail` or `| head`. Redirect to a log and read `$?`.
- Read the first failure in full, not the summary line. Note whether the failing assertion is
  about the behavior or about timing (timeouts, "element not found").

## Step 3 — Reproduce in isolation

1. Run **only** the failing test or suite, alone, with nothing else competing for CPU or
   ports.
2. If it now passes, that does not explain the first failure. Run it with the change and
   without it (the previous commit, or the changed file restored from `HEAD` temporarily):
   - fails without the change too → pre-existing or environmental, not this change;
   - passes in both when run alone → the first run was environmental; name the suspect
     (load, port, cache) as **inferred** unless you reproduced it;
   - fails only with the change → real regression.
3. Clear only the cache you suspect (and say which) before concluding a result is stale.

## Step 4 — Prove green tests can fail

For a test that passes but is under suspicion, break the behavior it claims to protect —
invert a condition, return a wrong value — and run it. It must fail. Revert the perturbation
immediately and confirm the tree matches the baseline (`git diff`).

Typical false greens: the assertion checks the value the mock returns, the test file is not
picked up by the runner's pattern, the code under test is never called, an error is caught
and the test still passes, a skipped test counted as passing.

## Step 5 — Classify

| Class | Meaning |
|---|---|
| **Real regression** | Fails only with the change, reproduced alone. |
| **Environment** | Load, port taken, stale cache, missing env or dependency. Reproduced, or marked inferred. |
| **Test defect** | The test is wrong: false green from Step 4, brittle timing, fixture out of date. |
| **Tooling defect** | The harness lies: lost exit code, hook or CI step reading the wrong status. |
| **Unresolved** | Not enough evidence. Say what would settle it. |

Not allowed as fixes: blanket retries, longer timeouts, deleting or weakening assertions,
skipping the test. They are acceptable only with a named, reproduced cause they address.

## Report format

```markdown
📌 **Verdict:** <class> — <one line: what failed and why, with the evidence that proves it>

🔬 **Evidence**
- Baseline: <commit, dirty?, command, what else was running>
- Runs: <command → exit code> for each run that mattered (alone, with/without the change)

🤔 **Proposed fix** (waits for your OK)
- <smallest change at the owning place: the test, the harness, or the code>

🧪 **Not verified**
- <what remains inferred, and how to confirm it>
```

Omit 🤔 when there is nothing to fix and 🧪 when everything was reproduced.

## After the report

Apply only the fixes the user approves, then rerun the same commands from Step 3 and report
their exit codes.
