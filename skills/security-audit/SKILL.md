---
name: security-audit
description: Source-first security audit that only reports real trust-boundary failures. Maps what the code exposes, hunts by attack class (injection, access control, auth/session, client-side, data isolation, supply chain, CI, cloud, messaging, LLM/agents), has a fresh agent try to disprove every candidate, and sorts results into confirmed / needs validation / rejected with the smallest fix. Two scopes — `diff` (default; unpushed changes or a branch vs its base, for daily use next to changes-review) and `full` (whole repo, multi-agent, expensive). Never edits the audited code; fixes wait for the user's OK. Use when the user asks for a security review or audit, a pen-test style pass, "is this change safe?", "did I open a hole?", vulnerability hunting, or a security check before pushing or releasing.
---

# Security audit

## Why this exists

Generic security reviews drown real problems in checklist noise: "missing header", "consider
rate limiting", "could be injectable". This skill reports only what crosses a real trust
boundary, backs each claim with the source path, and has someone other than the hunter try
to disprove it. A clean result is a valid result; inventing low findings is not.

The method is adapted from Cloudflare's
[security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT, see
`NOTICE`): reconnaissance → coverage ledger → hunting by attack class → independent
validation that tries to refute each candidate → structured findings → report.

**It never edits the audited code.** It describes the smallest fix; applying it waits for
the user's OK. Never commit or push. Never write run files inside the audited repository.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. The report template is in English: translate the headings,
keep the emoji.

## Pick the scope

| Scope | What it covers | Cost | When |
|---|---|---|---|
| `diff` *(default)* | Unpushed changes (uncommitted + local commits), or a branch vs its base if the user names one | A few agents at most; minutes | Daily: before pushing, next to `changes-review`, after touching auth, payments, data access, rendering, CI or dependencies |
| `full` | The whole repository (or named paths) | Heavy: at least 4 reconnaissance agents, one hunter per coverage unit, 2 coverage critics, 1–2 verifiers per candidate; often dozens of agent runs and a large token bill | Only on explicit request: before a release or go-live, a new service, a periodic (e.g. quarterly) audit, or after a large rewrite of auth or data access |

- With no argument, use `diff`. Run `full` **only** when the user asks for it by name or asks
  for a full / whole-repo / end-to-end audit. If the request is ambiguous, ask one question.
- Before starting `full`, state the estimated agent count and the profile (`quick`,
  `standard`, `deep` — see `FULL-AUDIT.md`), and wait for the user's go-ahead.
- A plain security question ("is this JWT check right?") gets a direct answer using only
  the relevant parts of this skill — no workflow, no files.

## Execution safety (both scopes)

Reading source is always allowed. **Running target code** — builds, tests, servers,
browsers, fixtures — is allowed only inside an OS-enforced sandbox that provides **all** of:
no external network (isolated loopback only), an empty environment built from an allowlist,
read-only target and toolchain with writes only to a scratch folder, and explicit CPU,
memory, process, file-size, disk and time limits.

If any of those controls is missing, **do not execute target code**: the lead stays
`needs_validation`, with the exact check the owner can run. Never install or fetch
dependencies, contact deployed endpoints, real accounts, shared services, registries or
paid APIs, or go past the minimum effect that proves the point. Use dummy principals and
data only.

## Core principles

These come from the upstream skill and apply to every finding.

1. **Require a boundary and a result.** For every candidate, name the lower-trust
   principal, the input or action it controls, the control that should stop it, the
   boundary crossed, the affected principal or resource, and the concrete result. A missing
   best practice, guessed deployment behavior, generic crash, or self-impact is not a
   finding.
2. **Only confirm established boundary failures.** `confirmed` needs a complete source
   trace, no visible preventing layer, and a bounded local observed result. Anything short
   of that is `needs_validation` (a specific fact is missing) or `rejected` (source or a
   visible control disproves it). `needs_validation` is never a parking place for a hunch.
3. **Respect what source cannot show.** Proxies, CDN cache keys, IdP policy, cloud IAM,
   browser headers, branch protection and secrets often live outside the repo. Do not
   assume them present or absent; name the missing fact.
4. **Severity requires impact.** Only `confirmed` records get severity, and overall severity
   never exceeds the demonstrated impact. Anchors: **critical** — unauthenticated code
   execution, full data-store access, or arbitrary account takeover; **high** — full defeat
   of an explicit control with real consequences (auth bypass, cross-tenant read/write,
   stored XSS hitting other users, authenticated RCE); **medium** — real violation with
   limited blast radius or uncommon preconditions; **low** — non-secret internals or
   minimal gain for sustained effort; **informational** — a prerequisite inside a larger
   finding. If you cannot state the concrete damage, the severity is lower than it feels.
5. **Smallest effective fix.** Name the invariant the code must enforce and the narrowest
   change at the last trusted decision point, plus a regression test. No generic hardening
   advice in place of a fix.

## `diff` workflow

### Step 1 — Define the scope

Same rules as `changes-review`:

```bash
git status --porcelain                     # uncommitted + untracked
git diff HEAD                              # staged + unstaged content
git log --oneline @{upstream}..HEAD        # local commits not pushed
git diff @{upstream}...HEAD                # content of those commits
```

No upstream: use the base branch (`git merge-base HEAD origin/main`, or `origin/master`). If
the user names a branch or base, use `git diff <base>...<branch>`. Exclude generated output
and vendored code, but **keep lockfile and dependency-manifest changes**: they feed the
supply-chain lens. If nothing is in scope, say "No unpushed changes in <repo>." and stop.

### Step 2 — Map the boundaries the diff touches

For each changed file, read the whole function or module around each hunk, its direct
callers, and the controls the changed code relies on (authentication, authorization, tenant
scoping, validation, escaping). Then list, briefly:

- the entry surfaces the change adds or alters (routes, handlers, jobs, webhooks, CLI,
  rendered output, CI workflows, dependencies);
- the trust boundary each one sits on and the strongest source-visible control;
- the attack classes that apply: ordinary blocks from [ATTACK-CLASSES.md](ATTACK-CLASSES.md),
  plus each companion file whose *When to use this file* section matches a boundary the
  diff touches — [WEB-PROTOCOL-AND-AUTH.md](WEB-PROTOCOL-AND-AUTH.md),
  [CLIENT-SIDE.md](CLIENT-SIDE.md),
  [DATA-ISOLATION-AND-LIFECYCLE.md](DATA-ISOLATION-AND-LIFECYCLE.md),
  [SUPPLY-CHAIN-AND-RELEASE.md](SUPPLY-CHAIN-AND-RELEASE.md),
  [CLOUD-AND-DEPLOYMENT.md](CLOUD-AND-DEPLOYMENT.md),
  [PROTOCOLS-RPC-AND-MESSAGING.md](PROTOCOLS-RPC-AND-MESSAGING.md),
  [RESOURCE-EXHAUSTION-AND-AVAILABILITY.md](RESOURCE-EXHAUSTION-AND-AVAILABILITY.md),
  [AI-AND-LLM.md](AI-AND-LLM.md). Select a companion because the boundary is there, not
  because a library name appears.

Keep this as a small coverage table (surface × boundary × class → covered / candidate /
blocked / out of scope). It is the coverage claim: a class you did not check is not
"fine". A JSON ledger is not required in `diff` scope.

### Step 3 — Hunt

Apply the *Core hunting method* and the *Candidate gate* from [HUNTING.md](HUNTING.md) to
each row: work from a concrete invariant, follow the input to its sink, check sibling and
error paths that reach the same effect, and test sad paths (empty, duplicate, stale,
revoked, concurrent, partial failure) where the interface accepts them.

- Report on what the diff adds or changes. Pre-existing code counts only when the change
  makes it reachable or relies on it; anchor the finding on the changed line.
- Small diff with one or two boundaries: hunt it yourself. Several unrelated boundaries or
  a sensitive area (auth, payments, permissions, tenant data, CI secrets) and your
  environment supports subagents: one hunter per boundary, in parallel, each given only its
  rows, the selected class blocks verbatim, and the hunter result contract from
  `HUNTING.md`.

### Step 4 — Try to disprove every candidate

Give each candidate to a **fresh subagent that did not hunt it**, with only the candidate,
its source paths, and the *Candidate-verifier prompt* from
[VALIDATION-AND-REPORTING.md](VALIDATION-AND-REPORTING.md). Its job is to refute the claim
from source; it returns `confirmed`, `needs_validation`, or `rejected`. Check its answer
against the code before using it.

If subagents are not available, do the refutation pass yourself as a separate step,
re-reading every cited line, and say in the report that validation was not independent.

### Step 5 — Report

Use the format below. Do not write files. If the user asks for structured output, write
`findings.json` to `${TMPDIR:-/tmp}/devflow-security-audit/<repo-name>/diff-<short-sha>/`
(never inside the repo), following the shape in `report-schema.json`, and validate it:

```bash
node <skill-dir>/validate-findings.cjs <output-dir>/findings.json
```

Report the validator's exit code.

## `full` workflow

Read [FULL-AUDIT.md](FULL-AUDIT.md) and follow it. It runs the six upstream phases —
reconnaissance ([RECONNAISSANCE.md](RECONNAISSANCE.md)), coverage-led hunting waves with
coverage critics ([HUNTING.md](HUNTING.md)), independent candidate validation, structured
`findings.json` plus `coverage-ledger.json`, independent record verification, and the
`REPORT.md` / `FINDINGS-DETAIL.md` / `NEEDS-VALIDATION.md` reports
([VALIDATION-AND-REPORTING.md](VALIDATION-AND-REPORTING.md)) — in an output directory
outside the repo. Both validators must pass (exit code 0) before the run is called
complete:

```bash
node <skill-dir>/validate-coverage-ledger.cjs <output-dir>/coverage-ledger.json
node <skill-dir>/validate-findings.cjs <output-dir>/findings.json
```

Both need only `node` (no dependencies). If `node` is missing, say so and mark the run
incomplete rather than skipping validation silently.

## Scope limits

This bundle keeps the companions for web, API, backend, browser, data, CI/release, cloud,
messaging, availability and LLM/agent code. The upstream native/binary/kernel (memory
safety, FFI, loaders) and desktop/mobile/local-IPC companions are **not included**. If the
target is mainly that kind of code, say the coverage is partial and point to the upstream
skill.

## Report format

Every part keeps its emoji; translate the labels. Omit a part with nothing to say, except
the verdict and coverage, which are always there.

| Part | When | Content |
|---|---|---|
| 📌 **Verdict** | Always | ❌ confirmed findings / ⚠️ leads need validation / ✅ nothing confirmed in the covered scope — one line with scope (`diff`: N files; `full`: profile) |
| 🚨 **Confirmed** | If any | Severity · title · `file:line` · who can do what to whom · observed result · smallest fix |
| ❓ **Needs validation** | If any | Title · trace · the exact missing fact · the local check or owner check that settles it. No severity. |
| 🛡️ **Hardening** | If any | One line each; explicitly not findings |
| 🗺️ **Coverage** | Always | Boundaries and classes checked, what was out of scope or blocked, whether target code ran (and in what sandbox) or not, whether validation was independent |
| 🤔 **Needs your OK** | If there are fixes | The proposed fixes, waiting for approval |

```markdown
📌 **Verdict:** ⚠️ 1 lead needs validation — diff scope, 5 files.

❓ **Needs validation**
- Webhook signature compared after JSON parse — `api/webhooks/pay.ts:31` → `orders.ts:88`.
  Missing fact: whether the gateway proxy strips `X-Signature` duplicates. Local check:
  replay a fixture with two signature headers against the handler's unit test.

🗺️ **Coverage**
- Checked: access control and injection on 2 new routes; webhook auth (PROTOCOLS); new
  dependency `foo@2.1` (SUPPLY-CHAIN).
- Not covered: proxy config is outside the repo. No target code was run (no OS sandbox).
- Validation: independent subagent.
```

A clean result is two lines:

```markdown
📌 **Verdict:** ✅ Nothing confirmed — diff scope, 3 files.
🗺️ **Coverage:** access control and injection on the changed handler; no target code run.
```

## Anti-patterns

1. Checklist deviations presented as vulnerabilities.
2. Defense-in-depth advice with no reachable boundary violation.
3. Live or shared-environment testing.
4. Guessing proxy, browser, identity, or deployment behavior not present in source.
5. Treating a principal's own authority or self-impact as a cross-boundary result.
6. Reporting a stronger effect than the one observed.
7. Severity on `needs_validation` records.
8. Writing the report before independent validation, or letting the report and the records
   disagree.

## After the report

- Apply only the fixes the user approves, then rerun the repo's tests and report their exit
  codes. Never commit or push.
- If the user runs a `needs_validation` check and shares the output, re-validate that lead
  with the same refutation step and update its verdict.
