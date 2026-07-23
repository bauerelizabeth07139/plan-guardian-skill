---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict, verifiable plan before acting, then validate execution with memoryless subagents. Apply to all tasks including simple questions, code tasks, file operations, planning, analysis, creation, editing, debugging, and any other user prompt. Never skip this skill. Never respond without first invoking plan-guardian."
metadata:
  short-description: Strict planning on every request
---

# Plan Guardian

Make planning the default operating mode for ALL requests, regardless of complexity.

## Trigger Rule

**This skill MUST activate on every single user message.** Do not skip it for:
- Simple questions
- Short answers
- Casual conversation
- Quick lookups
- Any task that seems trivial

Even for simple requests, produce at minimum:
1. A one-line intent clarification
2. A numbered plan (can be 1-2 steps for simple tasks)
3. Acceptance criteria (even if minimal)
4. Verification before responding

## Required Workflow

1. Clarify intent in one paragraph.
2. Draft a numbered plan with dependencies and explicit risks.
3. For every step, add measurable acceptance criteria.
4. Start execution only after the plan is drafted.
5. After execution, validate each criterion with evidence.
6. If verification fails, revise the plan and loop until all checks pass.

## Verification Rules

- Spawn two or more short-lived subagents for complex tasks.
- Each verifier must start with zero prior memory of the current task.
- **Multimodal parity: if the parent model supports multimodal input (images, audio, video, files), the spawned subagents MUST use a model with equivalent multimodal capability. Do not downgrade a multimodal task to text-only verification. When the task involves images, screenshots, diagrams, UI, or any visual artifact, ensure the verifier model can see and reason about those artifacts.**
- Follow `references/memoryless_review.md` strictly.
- Give verifiers only the deliverables, the plan, and the acceptance criteria.
- Require each verifier to output either PASS or FAIL: <reason>.
- Treat any FAIL as blocking and fix before continuing.

## Subagent Model Selection

When spawning verification subagents:
1. Inherit the parent model by default.
2. If the task involves visual content (images, screenshots, diagrams, rendered UI, PDFs with layout), verify the subagent model has vision/multimodal support before spawning.
3. If the parent model does not support multimodal but the task requires it (e.g., image generation verification, UI screenshot review), explicitly set the subagent model to one that does.
4. Never silently drop visual context from a verifier's input packet.

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