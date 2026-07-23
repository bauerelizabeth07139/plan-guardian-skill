---
name: plan-guardian
description: Generate a strict, verifiable plan before acting, then validate execution with memoryless subagents. Use when tasks are ambiguous, multi-step, risky, or require hard acceptance criteria, verification loops, and remediation until all checks pass.
metadata:
  short-description: Generate and enforce strict plans
---

# Plan Guardian

Make planning the default operating mode for complex requests.

## When To Use
- Use before multi-step work when success must be provable.
- Use when requirements are ambiguous, risky, or cross-cutting.
- Use when the task benefits from acceptance criteria, verification, and iteration.

## Required Workflow
1. Clarify intent in one paragraph.
2. Draft a numbered plan with dependencies and explicit risks.
3. For every step, add measurable acceptance criteria.
4. Start execution only after the plan is drafted.
5. After execution, validate each criterion with evidence.
6. If verification fails, revise the plan and loop until all checks pass.

## Verification Rules
- Spawn two or more short-lived subagents.
- Each verifier must start with zero prior memory of the current task.
- Follow `references/memoryless_review.md` strictly.
- Give verifiers only the deliverables, the plan, and the acceptance criteria.
- Require each verifier to output either PASS or FAIL: <reason>.
- Treat any FAIL as blocking and fix before continuing.

## Output Format
Return:
- The final plan.
- The current status for each step.
- The evidence collected from verifiers.
- The remediation actions taken, if any.

## Anti-Hallucination Rules
- Prefer concrete artifacts over claims.
- Prefer observable outputs over inferred intent.
- Do not assume a step passed without evidence.

## Failure Handling
- If evidence is missing, mark the step incomplete.
- If conflicting verifier results appear, add another independent verifier.
- Stop only when all acceptance criteria are satisfied.

