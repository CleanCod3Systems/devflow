# Defect report — ticket template

Use it only when the user asks for a ticket, or a defect needs to be handed to someone else.
In the QA report itself a defect is one line (see SKILL.md).

```markdown
## <ID> — <concrete title: what fails, where, under which condition>

- **Severity:** <critical | high | medium | low> — <why: impact on users or the business>
- **Priority (proposed):** <P1–P4> — <why now or why it can wait>
- **Environment:** <env, URL or local>, commit `<sha>`, <browser/device if it matters>
- **Preconditions and data:** <account role, records, configuration — no real personal data>

### Steps to reproduce
1. <minimal step>
2. <minimal step>

### Expected
<result> — **source:** <requirement, ticket, spec criterion, documented behavior>

### Observed
<result> — **frequency:** <reproductions>/<attempts>

### Impact
<who is affected, how often, what it costs: money, data, blocked flow, support load>

### Evidence
- <command + exit code, test name, log line, query and its result, screenshot path>

### Possible cause (hypothesis)
<only with a trace in code or logs: `file:line`, log message — otherwise omit this section>
```

## Severity vs priority

Severity is how bad the failure is; priority is when to fix it. They differ: a typo on the
home page is low severity and may be high priority; a crash in a feature nobody uses yet is
high severity and may wait.

| Severity | Typical meaning |
|---|---|
| Critical | Money charged wrongly, data lost or exposed to another user, a core flow fully blocked |
| High | A core flow fails for a group of users or inputs, with no reasonable workaround |
| Medium | A flow fails with a workaround, or a secondary feature fails |
| Low | Cosmetic, wording, minor inconsistency |

## Rules

- One defect per root cause. Several symptoms with the same confirmed cause are one ticket
  listing the symptoms; with only a suspected shared cause, separate tickets cross-linked.
- Defects, improvements and product questions are separate items. A disagreement with the
  requirement is a question, not a defect.
- Remove tokens, card numbers, personal data and internal hostnames from the evidence.
