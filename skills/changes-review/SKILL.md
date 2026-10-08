---
name: changes-review
description: Self-contained review of local changes that have not been pushed yet — uncommitted, or committed but not pushed. Builds an inventory, reviews every change through seven lenses (is it needed?, logic bugs, over-engineering, project conventions, blast radius, failure gaps, database/deploy risk), runs the tests, applies safe fixes directly, proposes the ones that change behavior, and reports verdict-first. Use when the user asks to review what we did, go over the changes, check whether something broke, whether all gaps are closed, whether it is over-engineered, or wants a pre-commit / pre-push review of the session's work.
---

# Changes review

## Why this exists

After changing code, the user wants to be sure before pushing: every change is needed,
simple, consistent with the project, breaks nothing else, and leaves no gaps. The main risk
is that the reviewer is the author and tends to approve its own work. So this review demands
evidence (`file:line`, tests run, callers found) instead of opinions, and drops any finding
that cannot name a concrete failure.

**Scope:** only files with **unpushed** changes — uncommitted (staged, unstaged, untracked)
or committed locally without a push. Anything already pushed is out of scope.

**It fixes things:** safe findings are applied directly to in-scope files; findings that
change behavior or scope are proposed and wait for the user's OK (Step 6). Never commit,
push, edit files outside the scope, or write to databases.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The report template is in English: translate the headings,
keep the emoji.

## Step 1 — Define the scope

1. **Repos to review:** the one given as argument; otherwise the git repo of the current
   directory; if the directory is not a repo (e.g. an umbrella folder), the repos where
   files were edited in this session; if none, look for repos with changes
   (`find . -maxdepth 3 -name .git`) and review only those with something unpushed.
2. **For each repo:**
   ```bash
   git status --porcelain                     # uncommitted + untracked
   git diff HEAD                              # staged + unstaged content
   git log --oneline @{upstream}..HEAD        # local commits not pushed
   git diff @{upstream}...HEAD                # content of those commits
   ```
   No upstream (branch never pushed): use the base branch
   (`git merge-base HEAD origin/main`, or `origin/master`) instead of `@{upstream}`.
   Untracked files: read the whole file, it is all new.
3. **Exclude** lockfiles, generated artifacts, and vendored code (dependency folders, build
   output, or any third-party source copied into the repo).
4. If nothing is unpushed: answer "No unpushed changes in <repos>." and stop.

## Step 2 — Inventory and context

- For each file: what changed and **why** (take it from the conversation). If a changed file
  was not touched in this session, flag it as "not from this session" — it may be earlier
  work by the user; review it anyway but say so.
- Read the repo's agent instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or similar) and
  the **whole method or file** around each change, not just the hunk. Read context, but
  report only on changed lines (see Step 5).

## Step 3 — Review each change

Go through every change with these seven lenses. Always with evidence (`file:line`, grep,
command output); a suspicion without evidence is not a finding.

### 3.1 Is it needed?
- Does it answer something the user asked for? Anything not requested is a candidate for removal.
- Did the repo already have something that solved it? Search by name and by concept before
  accepting a new helper, util, or type.

### 3.2 Logic bugs
Read the whole method, not just the hunk, and look for:
- Inverted conditions, off-by-one, comparisons with the wrong type or operator
  (identity vs value equality, text vs number), badly grouped boolean logic.
- Null or empty values arriving unchecked: parameters, external responses, empty search
  results, empty collections, optional values used without a check.
- Swallowed errors (empty error handlers, errors caught and ignored), wrong error types, error messages
  that leak sensitive data.
- Unclosed resources (connections, streams, files), transactions without rollback.
- Asynchronous code: tasks or streams that are never awaited or started, blocking calls
  inside non-blocking flows, errors that do not propagate.
- Shared state without protection: concurrency, race conditions, double execution.
- Money, dates, and time zones: rounding, currency, `float` for amounts, UTC vs local.
- Security: unvalidated input at a trust boundary, queries built by concatenating input,
  secrets in code, missing permission checks.

### 3.3 Over-engineering
The best thing that can happen to a change is that it gets shorter. Tag each finding and
name its replacement:

| Tag | What it is | Replacement |
|---|---|---|
| `delete` | dead code, unused flexibility, speculative feature | nothing |
| `stdlib` | hand-rolled code the standard library already ships | name the function |
| `native` | dependency or code doing what the platform, framework, or database already does | name the feature |
| `yagni` | interface with one implementation, config nobody sets, layer with one caller | inline it |
| `shrink` | same logic in fewer lines | show the shorter form |

Examples:
- `utils:12-38` · `stdlib` · 27-line hand-written validator → the standard library's blank-string check + the pattern already in `validators`.
- `repository:88` · `yagni` · abstract repository with a single implementation → inline it until a second one exists.
- `payment:52-71` · `delete` · retry wrapper around an idempotent local call → nothing.

A minimal test or a self-check `assert` is **not** over-engineering: never flag it.

### 3.4 Does it follow the project's conventions?
- Compare with 1–2 sibling files (same kind of class, service, view, or script) and with
  the repo's agent instructions: naming, structure, error handling, logging, language of
  user-facing text, how tests are written.
- It is a finding only if the convention holds across most of the module; if the module is
  inconsistent, do not report it.
- On stable branches, the existing file's style wins over generic preferences.

### 3.5 What else does it affect?
For every function, signature, field, column, endpoint, event, config key, or cache key that
changed: find who uses it (grep in the repo, and in sibling repos when it is a contract
between services). Cite `file:line` for each caller. If the right fix belongs in a shared
function, fix it once there, not in every caller.

### 3.6 Are there gaps left?
Walk through: null or empty inputs, external service errors (timeouts, 4xx/5xx), retries and
idempotency (what if it runs twice?), concurrency, existing data already in the database,
permissions and tenant/company isolation, backward compatibility with clients or older versions.

### 3.7 Database and deploy
Schema migrations, new columns with an index, required columns or defaults, type changes: can
it lock a large table on deploy? Does existing data satisfy the new constraint? If the table
size is unknown, it goes under "Not verified" in 🧪 Verification.

## Step 4 — Verify

- Build and run the tests of the touched module with the commands the repo's agent
  instructions or README give. Report the command and the actual result.
- If they cannot run (they need services, a database, credentials), say so; never claim
  "it works" without running it.

**Independent review** — only if the scope exceeds ~5 files or touches something sensitive
(payments, database migrations, authentication/permissions, contracts between services), and your
environment supports subagents: launch a fresh subagent that receives **only** the diff and
the user's original request — none of this session's reasoning — with the task of finding
concrete failures. Check each of its findings against the code before including it.

## Step 5 — Filter before reporting

- **Only lines the diff adds or modifies.** Pre-existing code is not reported, unless the
  change makes it reachable or dangerous (then anchor the finding on the new line).
- **Every finding names a concrete failure:** which input or state → what breaks. If you
  cannot, drop it. Silence is a valid outcome.
- Deduplicate what shows up in several lenses or in the independent review; keep the most
  specific version.
- ~6 findings max, ordered by severity. No praise, no filler.

## Step 6 — Apply fixes

1. **Back up before editing**, per repo:
   `git stash store -m "changes-review backup" "$(git stash create)"`.
   It does not touch the working tree; restore with `git stash apply`. (With no uncommitted
   changes, `git stash create` prints nothing: no backup needed.) This backup **does not
   include untracked files**: before editing one, copy it to a temporary directory and give
   the path in the report.
2. **Classify each finding:**

   | Apply directly 🔧 | Propose and wait for OK 🤔 |
   |---|---|
   | Bug with an obvious, local fix (null check, inverted condition, unclosed resource) | Changes visible behavior or the scope of what was asked |
   | Over-engineering: dead code, single-implementation abstraction, what the stdlib or the repo already has | Deletes something the user explicitly asked for |
   | Deviation from the project's conventions (naming, structure, repo language) | Signatures, contracts between services, endpoints, events, cache keys |
   | Gap with a clear handling (validate input, catch error, idempotency guard) | Database schema, migrations, security/permissions |
   | | More than one reasonable fix |

3. **Edit surgically**: only the finding's lines, only in-scope files, matching the file's
   style. Do not "take the chance" to clean up untouched neighboring code.
4. **Re-verify**: run the build and tests from Step 4 again. If a fix breaks something,
   revert **that** fix and move it to 🤔 with the error you got.

## Report format

Four parts, in this order. **Omit any part with nothing to say** — except the verdict and
the verification, which are always there. Every part keeps its emoji; translate the labels
into the user's language.

| Part | When | Content |
|---|---|---|
| 📌 **Verdict** | Always | ✅ ready to push / ⚠️ with notes / ❌ needs fixes — one line with the reason and the scope ("6 files in 2 repos") |
| 🔧 **Fixed** | If something was applied | `file:line`, what was failing, and what changed |
| 🤔 **Needs your OK** | If there are proposals | Each one: the problem, when it fails, the proposal, and the recommended option |
| 🧪 **Verification** | Always | Tests run and their result, where the backup is, and what could not be checked |

```markdown
📌 **Verdict:** ⚠️ With notes — 6 files in 2 repos; fixed 2 issues, 1 needs your OK.

🔧 **Fixed**
- `payment-service:88` — a gateway timeout was silently ignored. It is now logged and propagated.
- `utils:12-38` — hand-written validator replaced with the standard library's (−25 lines).

🤔 **Needs your OK**
- `booking-api:40` — `status` was renamed to `payment_status`, but `admin-panel:112` still
  reads `status`. It breaks as soon as it is deployed. **Proposal:** keep both names for one
  release *(recommended)*, or update the admin panel in this same batch.

🧪 **Verification**
- Payment module test suite → 48/48 OK, after the fixes.
- Backup: `git stash list` → "changes-review backup".
- Not verified: the admin panel has no tests.
```

When everything is fine, the whole report is two lines:

```markdown
📌 **Verdict:** ✅ Ready to push — 3 files reviewed, no findings.
🧪 **Verification:** payment module test suite → 48/48 OK.
```

## After the report

Apply only the 🤔 proposals the user approves, then run the tests again. If the user does not
want a 🔧 fix that was already applied, revert just that one. Never commit or push without an
explicit request.
