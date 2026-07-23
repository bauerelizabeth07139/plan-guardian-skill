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

**Every step below is mandatory. Do not skip any step. Do not self-verify. All verification MUST use `spawn_agent`.**

### Step 1: Clarify Intent
- Restate the user request in one paragraph.

### Step 2: Draft Plan
- Produce a numbered plan with dependencies and explicit risks.
- Each step must have a clear deliverable.

### Step 3: Define Acceptance Criteria
- For every plan step, write one or more measurable acceptance criteria.
- Each criterion must be observable and binary (pass/fail).

### Step 4: Execute
- Implement the plan step by step.
- Do not proceed to verification until execution is complete.

### Step 5: Per-Step Verification (MANDATORY - uses `spawn_agent`)
- After execution, for each plan step:
  1. Collect the deliverable for that step.
  2. Spawn a memoryless verifier subagent with `spawn_agent` (fork_context=false).
  3. Give the verifier ONLY: the deliverable, the plan step, and its acceptance criteria.
  4. The verifier MUST independently read the actual artifacts.
  5. The verifier MUST output PASS or FAIL for each criterion.
  6. Use `wait_agent` with `timeout_ms=120000` (2 minutes) to allow enough time for the verifier to read files and produce results.
- If ANY verifier returns FAIL for ANY step, fix the issue and re-verify that step with a NEW verifier.
- Do not proceed to the final gate until ALL per-step verifiers return PASS.

### Step 6: Final Gate (MANDATORY - uses `spawn_agent`)
**You MUST NOT respond to the user until this step completes successfully.**

1. Collect ALL deliverables from ALL plan steps.
2. Write a single checklist of EVERY acceptance criterion from the entire plan.
3. Spawn at least TWO memoryless verifier subagents with `spawn_agent` (fork_context=false).
4. Each final verifier:
   - Receives ONLY the deliverables, the full plan, and all acceptance criteria.
   - Receives ZERO prior conversation context.
   - Has NO memory of how the work was done.
   - MUST independently read the actual files/artifacts.
   - MUST output PASS or FAIL for each criterion.
   - If FAIL, MUST state the exact unmet criterion and missing evidence.
5. Use `wait_agent` with `timeout_ms=180000` (3 minutes) for final verifiers since they check more deliverables.
6. If ANY final verifier returns FAIL, fix the issue and re-run the entire final gate with NEW verifiers.
7. Only respond to the user when ALL final verifiers return ALL PASS for ALL criteria.

### Step 7: Report
- Present the final plan, status per step, verifier evidence, and remediation actions taken.

## Verifier Timeout Rules

Verifiers need time to read actual files and produce thorough analysis. Use these timeout values:

| Verifier type | wait_agent timeout_ms |
|---|---|
| Per-step verifier (Step 5) | 120000 (2 min) |
| Final gate verifier (Step 6) | 180000 (3 min) |
| Retry after FAIL | 180000 (3 min) |

If a verifier times out, treat it as FAIL and spawn a new verifier with a longer timeout (add 60000 each retry, max 360000).

## Verifier Prompt Template

Use this template for every verifier spawned in Steps 5 and 6:

```
You are a strict code reviewer. You have NO prior memory of how these files were created.
Verify the following deliverable against acceptance criteria. Be harsh. FAIL if anything is missing or wrong.

## Deliverable
<path or description of what to check>

## Acceptance Criteria
<criterion 1>
<criterion 2>
...

## Instructions
- Read the actual files/artifacts. Do not assume they exist.
- Check each criterion independently.
- Do not guess. If you cannot verify something, mark it FAIL.

## Output Format
For each criterion:
- CRITERION N: PASS or FAIL
- If FAIL: exact reason and what is missing

End with: VERDICT: ALL PASS or VERDICT: FAIL (list unmet criteria numbers)
```

## Subagent Roles and Model Strategy

Use two distinct subagent roles:

### 1. Worker Subagents (execution)
- Purpose: implement, build, fix, edit.
- Model: inherit the parent model by default. Do NOT override.
- Spawn with `spawn_agent` without the `model` parameter.
- Used in Step 4.

### 2. Verifier Subagents (review)
- Purpose: independently verify completion against acceptance criteria.
- Model: must support multimodal input when the task involves images, screenshots, diagrams, UI, PDFs with layout, or any visual artifact.
- Spawn with `spawn_agent`. Set `model` explicitly when the parent model is not multimodal.
- Used in Steps 5 and 6.

### Runtime Multimodal Detection

APIs do not always advertise multimodal capability in the models list. To detect it at runtime, use `scripts/detect_multimodal.py`:

```bash
python scripts/detect_multimodal.py <base_url> <api_key> <model_id>
```

- Exit code 0 + `"multimodal": true` -> model accepts images
- Exit code 1 + `"multimodal": false` -> model rejects images
- Exit code 2 -> network/auth error, cannot determine

### Model Selection Decision Tree

```
Task involves visual artifacts?
|-- NO  -> verifiers inherit parent model
`-- YES -> runtime detect: is parent model multimodal?
    |-- YES -> verifiers inherit parent model
    `-- NO  -> verifiers MUST use explicit multimodal model override
```

## Hard Rules

1. NEVER respond to the user without completing Step 6 (final gate).
2. NEVER self-verify. All verification uses `spawn_agent` with `fork_context=false`.
3. NEVER reuse a verifier that returned FAIL. Spawn a NEW one after fixing.
4. NEVER pass conversation history to verifiers. They get deliverables + criteria only.
5. NEVER assume a step passed without verifier evidence.
6. If two final verifiers disagree, spawn a third. If conflict persists, treat as FAIL.
7. NEVER use default timeout for verifiers. Always set `timeout_ms` explicitly per the timeout table.
8. If a verifier times out, treat as FAIL, increase timeout by 60000, and retry with a NEW verifier.