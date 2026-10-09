---
name: stepwise
description: Plan and execute work in short, numbered phases and steps, keeping track of where you are. Builds a compact plan (one line per step, who does it, when it is done), asks open questions once up front, executes one step at a time with a status board, answers side questions briefly and always returns to the current step, and verifies steps the user does themselves. Use when the user invokes stepwise, asks to plan something step by step, says "let's go step by step", "next step", "do step 3", "I did up to step 2", "where are we in the plan?", or is following a multi-step plan and asks a question about one of its steps.
argument-hint: "<goal>"
---

# Stepwise

## Why this exists

People like plans broken into steps, but two things go wrong. The agent talks too much —
long plans, long explanations, repeated recaps — and it loses the thread: a question about
step 3 turns into a new conversation and nobody remembers that step 3 was in progress. This
skill keeps plans short and keeps the agent anchored to the current step.

**Language:** answer in the user's language — the language of their message, unless their
own instructions say otherwise. Labels below are in English: translate them, keep the emoji.

## 1. Build the plan

1. Read what is needed to plan well (code, docs, the conversation). Do not narrate the
   exploration.
2. Write the plan in this shape, and nothing else:

```markdown
🎯 **Goal:** <one line>

**Phase 1 — <name>**
1. 🤖 <step> · *done when:* <observable result>
2. 🧑 <step> · *done when:* <what the user reports back>

**Phase 2 — <name>**
3. 🤖 <step> · *done when:* <observable result>

❓ **Before we start:** <only questions that block the plan; omit the line if none>
```

Rules:
- **One short line per step** (~15 words, "done when" included). Aim for 7 steps or fewer:
  merge small steps rather than listing every action. Phases only when there are more than
  ~4 steps; number steps continuously across phases (1, 2, 3…), so "step 3" is never ambiguous.
- **Owner on every step:** 🤖 the agent does it, 🧑 the user does it (production access,
  manual tools, approvals, anything the agent cannot or must not do).
- **"done when"** is something checkable: a test passing, a row count, a file existing, the
  user pasting a result. It is how the step gets verified later.
- **Ask everything once.** All open questions go in "Before we start", together — at most 3,
  only the ones whose answer changes the plan. Do not scatter questions through the execution.
- **Grounded steps.** Every file, function, command, table or setting a step names must have
  been read or checked during planning. Do not invent paths or commands; if something is
  unknown, it becomes a question in "Before we start", not a guess inside a step.
- **Scope = what was asked.** If the user points to a reference ("like we did in X"), read X
  first and plan the same shape. No extra steps (refactors, improvements, cleanups) unless
  the user asks; propose them in "Before we start" instead.
- No introductions, no explanations of the approach, no alternatives considered. If the
  user wants the reasoning, they will ask "why?".
- Wait for the user's OK before executing anything.

## 2. Execute one step at a time

After the OK, do the next pending step. When it is done, report in this shape:

```markdown
✅ **Step <n> done** — <result in one line, with evidence: file, command output, count>.

📍 Phase 1: ✅1 ✅2 · Phase 2: ▶️3 ⬜4

**Next — Step <n+1> (🤖|🧑):** <the step>. <"Go?" for 🤖 steps, or what to send back for 🧑 steps>
```

- **The report is those three lines and nothing else.** No recap, no explanation of how.
- **✅ only with evidence.** Mark a step ✅ only after checking its "done when" with a tool
  (test run, file read, query, command output) and cite that evidence. If it could not be
  checked, mark it ⚠️ and say what is unverified — never ✅ on assumption.
- **Do only this step.** Nothing outside it. If you did anything the step did not ask for,
  or did it differently from the reference, add one line: `Deviation: <what and why>`.
- **Status board** (`📍` line): ✅ done, ▶️ current, ⬜ pending, ❌ failed, ⚠️ done but
  unverified. One line, always. Never re-print the whole plan unless asked.
- Then **stop and wait**. Continue when the user says go ("go", "next", "dale", "step 4").
- If the user says to run everything ("do them all"), run 🤖 steps back to back, still
  printing the short report after each, and stop only at a 🧑 step or a failure.
- **🧑 steps:** say exactly what the user should do and what to send back. When they report,
  **verify** against the step's "done when" (read-only checks where possible) before marking
  it ✅. "I did up to step 2" means: verify steps 1–2, then continue from step 3.
- **Failure:** mark ❌, give the error in one line and the proposed fix. Do not move to the
  next step until it is resolved or the user decides to skip it.

## 3. Side questions never derail the plan

When the user asks something that is not "go" — a doubt about a step, a "why", something
unrelated — answer it briefly, labeled, and return to the plan:

```markdown
↪ **Aside:** <short answer>

📍 We're at Phase 2 · Step 3 — continue?
```

- Keep the answer short; more detail only if they ask for it.
- **Do not change the plan as a side effect.** If the question reveals the plan should
  change, propose the change explicitly — "Add step 3b: <step>?" or "Drop step 5?" — and
  apply it only after the user agrees. Then show the updated status board.
- If the conversation drifts for several turns, the next reply still ends with the 📍 line.
  The plan is closed only when every step is ✅ (or the user explicitly drops it).

## 4. Where are we?

"Where are we?", "what's left?", "which step is next?" → reply with only:

```markdown
📍 Phase 1: ✅1 ✅2 · Phase 2: ▶️3 ⬜4
**Current — Step 3 (🤖):** <step>
```

Add the full plan only if the user asks for it.

## 5. Finish

When the last step is ✅:

```markdown
🏁 **Plan complete** — <goal> · <n> steps.
<one line per step only if something notable happened: a deviation, a skipped step, a follow-up>
```

## Keeping track

The plan lives in the conversation. If the conversation was summarized or compacted, or the
user returns after a long detour, re-state the status board before acting so both sides agree
on where things stand. If the user asks to keep the plan across sessions, write it to a file
they choose and update the ✅/⬜ marks there after each step.
