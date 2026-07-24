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

### Step 4: Execute\r\n- Implement the plan step by step.\r\n- When a step is non-trivial, multi-file, or command-heavy, delegate the work to a Worker subagent instead of doing it inline.\r\n- Keep the main loop focused on coordination, not on pasting large content or long outputs.\r\n- Do not proceed to verification until execution is complete.

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
## Subagent Roles and Model Strategy

Use three explicit roles to keep the main loop lightweight:

### 0. Planner (main loop)
- Purpose: clarify intent, draft plan, collect acceptances, and coordinate work.
- Rule: keep the planner context minimal. Do not paste large files, logs, or long diffs into the planner. Prefer delegating file reads, builds, tests, and verification to subagents.
- Rule: when a step is non-trivial, has multiple files, or requires running commands, delegate the execution to a Worker subagent instead of doing it inline.
- Rule: the planner MUST NOT self-verify. Verification always uses memoryless verifier subagents.
- Rule: the planner response MUST be only the final report after the final gate passes.

### 1. Worker Subagents (execution)
- Purpose: implement, build, fix, edit, inspect files, run tests, and collect artifacts.
- Default: inherit the parent model when the task is text/code-only.
- Visual rule: if the task involves images, screenshots, diagrams, UI layout, PDFs with visual layout, or rendered artifacts, the worker MUST use a multimodal-capable model. If the parent model is not multimodal, override `model` explicitly for that worker.
- Context rule: workers should minimize echoed context back to the planner. Return only structured results, paths, and pass/fail summaries.

### 2. Verifier Subagents (review)
- Purpose: independently verify completion against acceptance criteria.
- Rule: verifiers are memoryless (`fork_context=false`) and receive only deliverables + criteria.
- Visual rule: if the task involves visual artifacts, the verifier MUST use a multimodal model. If the parent model is not multimodal, override `model` explicitly for that verifier.
- Context rule: verifiers must read actual artifacts themselves and must not request full conversation history.

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
|-- NO  -> workers/verifiers inherit parent model
`-- YES -> runtime detect: is parent model multimodal?
    |-- YES -> workers/verifiers may inherit parent model
    `-- NO  -> workers/verifiers MUST use explicit multimodal model override
```

### Context Minimization Rules

1. Do not paste full file contents into the planner when a worker can read them directly.
2. Do not paste full test output into the planner; pass paths and only the failing lines summary.
3. Keep verification packets small: plan step, acceptance criteria, and artifact references only.
4. If a subtask is large, split it into independent worker subtasks and run them in parallel when safe.
5. If a subtask touches more than 3 files or requires nontrivial command execution, delegate it to a worker subagent by default.

## Hard Rules

1. NEVER respond to the user without completing Step 6 (final gate).
2. NEVER self-verify. All verification uses `spawn_agent` with `fork_context=false`.
3. NEVER reuse a verifier that returned FAIL. Spawn a NEW one after fixing.
4. NEVER pass conversation history to verifiers. They get deliverables + criteria only.
5. NEVER assume a step passed without verifier evidence.
6. If two final verifiers disagree, spawn a third. If conflict persists, treat as FAIL.
7. NEVER use default timeout for verifiers. Always set `timeout_ms` explicitly per the timeout table.
8. If a verifier times out, treat as FAIL, increase timeout by 60000, and retry with a NEW verifier.

