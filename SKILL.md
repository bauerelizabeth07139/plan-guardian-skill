---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict 7-step verifiable plan before acting, then validate execution with memoryless subagents. Apply to ALL tasks without exception. Never skip any step. Never respond without completing all 7 steps."
metadata:
  short-description: Strict 7-step planning on every request
---

# Plan Guardian

Every request goes through the full 7-step workflow. No shortcuts, no exceptions.

## Trigger Rule

**This skill MUST activate on every single user message.** No exceptions for simple questions, short answers, casual conversation, quick lookups, or any task that seems trivial.

## Hard Rules

0. NEVER skip any step.
1. NEVER respond to the user without completing all 7 steps.
2. NEVER self-verify. All verification uses subagents.
3. NEVER execute non-trivial work inline. Always delegate to a Worker subagent.
4. NEVER assume a step passed without verifier evidence.
5. NEVER produce a plan with fewer than 7 steps.
6. When verification fails, revise the plan before retrying.

## Required Workflow

### Step 1: Clarify Intent
- Restate the user request in one paragraph.
- Identify the core deliverable.
- Identify any implicit requirements the user didn't explicitly state.

### Step 2: Draft Plan
- Produce a numbered plan with **exactly 7 concrete steps**.
- Each step must have a clear deliverable.
- The plan must be specific enough that a stranger could execute it.

### Step 3: Define Acceptance Criteria
- For **every** plan step, write **at least one** measurable acceptance criterion.
- Each criterion must be observable and binary (PASS or FAIL).

### Step 4: Execute via Worker Subagents
**This step is MANDATORY. You MUST spawn subagents for execution.**

For each plan step that involves file editing, command execution, or multi-step logic, you MUST call `multi_agent_v1__spawn_agent` to create a Worker subagent. Do NOT execute work inline.

**Required tool call pattern for each worker:**

```json
{
  "tool": "multi_agent_v1__spawn_agent",
  "input": {
    "message": "<specific task instructions for this worker>",
    "fork_context": false
  }
}
```

**Rules:**
- Spawn one worker per plan step (or group related steps).
- Each worker receives ONLY: the specific plan step, deliverable description, and relevant file paths.
- Workers execute independently and return structured results.
- After spawning workers, use `multi_agent_v1__wait_agent` to collect results.
- If a worker returns errors, fix the issue and spawn a NEW worker (do not reuse failed ones).

**Example: spawning two workers in parallel:**

First, spawn both workers (make two tool calls in the same block):
```
Call multi_agent_v1__spawn_agent with fork_context=false, message="Step 1: Create file X at path Y with content Z"
Call multi_agent_v1__spawn_agent with fork_context=false, message="Step 2: Run tests in directory A and report pass/fail"
```

Then wait for results:
```
Call multi_agent_v1__wait_agent with targets=["<worker1_id>", "<worker2_id>"]
```

### Step 5: Verify via Verifier Subagents
**This step is MANDATORY. You MUST spawn verifiers.**

For each completed plan step, spawn a memoryless Verifier subagent to check acceptance criteria.

**Required tool call pattern for each verifier:**

```json
{
  "tool": "multi_agent_v1__spawn_agent",
  "input": {
    "message": "Verify the following:\n\n**Artifact:** <path or description>\n\n**Acceptance Criteria:**\n- CRITERION 1: <description>\n- CRITERION 2: <description>\n\nRead the actual files/artifacts. For each criterion, report PASS or FAIL with reason. End with: VERDICT: ALL PASS or VERDICT: FAIL",
    "fork_context": false
  }
}
```

**Rules:**
- Verifiers MUST have `fork_context: false` (memoryless).
- Verifiers receive ONLY deliverables + criteria. Do NOT pass conversation history.
- Each verifier independently reads the actual artifacts.
- If a verifier returns FAIL, fix the issue and spawn a NEW verifier.
- If two verifiers disagree, spawn a third. If conflict persists, treat as FAIL.

### Step 6: Re-Plan if Needed
- If any verifier returned FAIL, analyze the failure.
- Revise the plan (do NOT blindly retry).
- Re-execute failed steps with new workers.
- Re-verify with new verifiers.

### Step 7: Final Report
- Summarize what was done.
- List all plan steps and their verification status (PASS/FAIL).
- List any files changed or artifacts created.
- Report the overall verdict: ALL PASS or FAIL (with details).