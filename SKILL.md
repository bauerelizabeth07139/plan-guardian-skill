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
7. **Final gate: spawn memoryless subagent verifiers to independently audit the entire plan against all acceptance criteria before responding.**

## Final Verification Gate (MANDATORY)

**This step MUST NOT be skipped. Before returning the final answer to the user, spawn at least two memoryless subagent verifiers.**

### How to execute the final gate:

1. Collect all deliverables produced during execution.
2. Write a checklist of every acceptance criterion from the plan.
3. Spawn two or more subagents with `spawn_agent`. Each verifier:
   - Receives ONLY the deliverables, the plan, and the acceptance criteria.
   - Receives ZERO prior conversation context.
   - Has NO memory of how the work was done.
   - Must independently read the actual files/artifacts.
   - Must output PASS or FAIL for each criterion.
   - If FAIL, must state the exact unmet criterion and missing evidence.
4. If ANY verifier returns FAIL, fix the issue and re-run the final gate.
5. Only respond to the user when ALL verifiers return ALL PASS.

### Final gate prompt template:

```
You are a strict code reviewer. You have NO prior memory of how these files were created.
Verify the following deliverable against acceptance criteria. Be harsh. FAIL if anything is missing or wrong.

## Deliverable
<path or description>

## Acceptance Criteria
<list every criterion from the plan>

## Output Format
For each criterion:
- CRITERION N: PASS or FAIL
- If FAIL: exact reason and what is missing

End with: VERDICT: ALL PASS or VERDICT: FAIL
```

## Subagent Roles and Model Strategy

Use two distinct subagent roles:

### 1. Worker Subagents (execution)
- Purpose: implement, build, fix, edit.
- Model: inherit the parent model by default. Do NOT override unless there is a specific reason.
- Spawn with `spawn_agent` without the `model` parameter.

### 2. Verifier Subagents (review)
- Purpose: independently verify completion against acceptance criteria.
- Used in the final verification gate.
- Model: must support multimodal input when the task involves images, screenshots, diagrams, UI, PDFs with layout, or any visual artifact.
- Spawn with `spawn_agent` and set `model` explicitly when the parent model is not multimodal or when a stronger vision model is needed.

### Runtime Multimodal Detection

APIs do not always advertise multimodal capability in the models list. To detect it at runtime, use `scripts/detect_multimodal.py`:

```bash
python scripts/detect_multimodal.py <base_url> <api_key> <model_id>
```

- Exit code 0 + `"multimodal": true` -> model accepts images
- Exit code 1 + `"multimodal": false` -> model rejects images
- Exit code 2 -> network/auth error, cannot determine

Detection strategy: send a minimal 1x1 PNG to `/chat/completions`. If the API returns 200, the model is multimodal. If it returns 404 with "image" in the error message, it is not.

### Model Selection Decision Tree

```
Task involves visual artifacts?
|-- NO  -> verifiers inherit parent model
`-- YES -> runtime detect: is parent model multimodal?
    |-- YES -> verifiers inherit parent model
    `-- NO  -> verifiers MUST use explicit multimodal model override
```

## Verification Rules

- Spawn two or more short-lived verifiers for complex tasks.
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