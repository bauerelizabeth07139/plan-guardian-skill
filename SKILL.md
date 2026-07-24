---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict 7-step verifiable plan before acting, then validate execution with memoryless subagents. Apply to ALL tasks without exception. Never skip any step. Never respond without completing all 7 steps."
metadata:
  short-description: Strict 7-step planning on every request
---

# Plan Guardian

Every request goes through the full 7-step workflow. No shortcuts, no exceptions.

## Trigger Rule

**This skill MUST activate on every single user message.** No exceptions for:
- Simple questions
- Short answers
- Casual conversation
- Quick lookups
- Any task that seems trivial

**Every request produces exactly 7 steps in the workflow below.**

## Required Workflow

**Every step below is MANDATORY. Do not skip any step. Do not self-verify. All verification MUST use `spawn_agent`.**

### Step 1: Clarify Intent
- Restate the user request in one paragraph.
- Identify the core deliverable.
- Identify any implicit requirements the user didn't explicitly state.

### Step 2: Draft Plan
- Produce a numbered plan with **exactly 7 concrete steps**.
- Each step must have:
  - A clear deliverable
  - Dependencies on other steps (if any)
  - Explicit risks or edge cases
- The plan must be specific enough that a stranger could execute it.

### Step 3: Define Acceptance Criteria
- For **every** plan step, write **at least one** measurable acceptance criterion.
- Each criterion must be:
  - Observable (can be checked by reading a file, running a command, or inspecting output)
  - Binary (PASS or FAIL, no ambiguity)
- Write criteria BEFORE execution, not after.

### Step 4: Execute (MANDATORY subagent delegation)
- **Delegate ALL non-trivial work to Worker subagents.** The main loop only coordinates.
- For each plan step, determine if it requires file editing, command execution, or multi-step logic. If YES → spawn a Worker subagent.
- Worker spawning rules:
  - Text/code-only tasks → `spawn_agent` with default model (inherits parent)
  - Visual/image/UI tasks → `spawn_agent` with `model` set to a multimodal-capable model
  - Each worker receives ONLY: the specific plan step, deliverable description, and relevant file paths
- Workers execute independently and return structured results (paths created/modified, status, errors).
- The main loop collects worker results and passes them to verification.
- **The main loop MUST NOT paste large file contents, long command outputs, or multi-step implementations inline.**
- Do not proceed to verification until ALL execution is complete.
- Do not take shortcuts. If the plan says build X, build X completely.
### Step 5: Per-Step Verification (MANDATORY - uses `spawn_agent`)
- After execution, for **each** plan step:
  1. Collect the deliverable for that step.
  2. Spawn a memoryless verifier subagent with `spawn_agent` (fork_context=false).
  3. Give the verifier ONLY: the deliverable, the plan step, and its acceptance criteria.
  4. The verifier MUST independently read the actual artifacts.
  5. The verifier MUST output PASS or FAIL for each criterion.
  6. Use `wait_agent` with `timeout_ms=120000` (2 minutes).
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
5. Use `wait_agent` with `timeout_ms=180000` (3 minutes) for final verifiers.
6. If ANY final verifier returns FAIL, fix the issue and re-run the entire final gate with NEW verifiers.
7. Only respond to the user when ALL final verifiers return ALL PASS for ALL criteria.

### Step 7: Report
- Present the final plan, status per step, verifier evidence, and remediation actions taken.
- Do NOT respond until Step 6 passes.

## Verifier Timeout Rules

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

Use three explicit roles to keep the main loop lightweight:

### 0. Planner (main loop)
- Purpose: clarify intent, draft plan, collect acceptances, and coordinate work.
- Rule: keep the planner context minimal. Do not paste large files, logs, or long diffs into the planner.
- Rule: when a step is non-trivial, delegate to a Worker subagent.
- Rule: when a step is non-trivial, delegate to a Worker subagent. NEVER do execution inline in the planner.
- Rule: the planner MUST NOT self-verify.
- Rule: the planner response MUST be only the final report after the final gate passes.
- Rule: use `spawn_agent` for ALL workers. Use `model` override for visual tasks when the parent model is not multimodal.
- Purpose: implement, build, fix, edit, inspect files, run tests, and collect artifacts.
- Default: inherit the parent model when the task is text/code-only.
- Visual rule: if the task involves images, screenshots, diagrams, UI layout, PDFs with visual layout, or rendered artifacts, the worker MUST use a multimodal-capable model.
- Context rule: workers should minimize echoed context back to the planner. Return only structured results, paths, and pass/fail summaries.

### 2. Verifier Subagents (review)
- Purpose: independently verify completion against acceptance criteria.
- Rule: verifiers are memoryless (`fork_context=false`) and receive only deliverables + criteria.
- Visual rule: if the task involves visual artifacts, the verifier MUST use a multimodal model.
- Context rule: verifiers must read actual artifacts themselves and must not request full conversation history.

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

1. NEVER respond to the user without completing all 7 steps.
2. NEVER self-verify. All verification uses `spawn_agent` with `fork_context=false`.
3. NEVER reuse a verifier that returned FAIL. Spawn a NEW one after fixing.
4. NEVER pass conversation history to verifiers. They get deliverables + criteria only.
5. NEVER assume a step passed without verifier evidence.
6. NEVER produce a plan with fewer than 7 steps. Every plan MUST have exactly 7 concrete steps.
7. If two final verifiers disagree, spawn a third. If conflict persists, treat as FAIL.
8. NEVER use default timeout for verifiers. Always set `timeout_ms` explicitly per the timeout table.
9. NEVER execute non-trivial plan steps inline in the main loop. Always delegate to a Worker subagent.
10. If a verifier times out, treat as FAIL, increase timeout by 60000, and retry with a NEW verifier.

