---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict 7-step verifiable plan before acting, then validate execution with memoryless subagents. Apply to ALL tasks without exception. Never skip any step. Never respond without completing all 7 steps."
metadata:
  short-description: Strict 7-step planning on every request
---

# Plan Guardian

Every request goes through the full 7-step workflow. No shortcuts, no exceptions.

## Trigger Rule

**This skill MUST activate on every single user message received by the MAIN planning agent.** No exceptions. Step 0 (model detection) runs ONLY on the first message; subsequent messages skip Step 0 and reuse the cached result.

**Scope restriction: This 7-step workflow applies ONLY to the main planning agent.** Spawned subagents (workers, verifiers, diagnostics) MUST NOT run this workflow. Subagents should execute their assigned task directly and return results.

## Hard Rules

0. NEVER skip any step.
1. NEVER respond to the user without completing all 7 steps.
2. NEVER self-verify. All verification uses subagents.
3. NEVER execute non-trivial work inline. Always delegate to a Worker subagent.
4. NEVER assume a step passed without verifier evidence.
5. NEVER produce a plan with fewer than 7 steps.
6. When verification fails, revise the plan before retrying.
7. Verifier subagents MUST always be spawned. No exceptions.
8. Worker subagents SHOULD be spawned for all non-trivial steps to minimize main-loop context.
9. Verifiers must perform ACTUAL functional testing, not just file existence checks.
10. All subagents inherit the parent model. Never override model in spawn_agent calls.

## Required Workflow

### Step 0: Detect Model Capabilities (ONCE per conversation)

**Run this step ONLY at the start of the conversation (first user message).** Cache the result and reuse it for all subsequent messages.

Run the detection script to probe the actual model API:

`
python <skill_dir>/scripts/detect_multimodal.py
`

The script automatically reads credentials from ~/.codex/config.toml and ~/.codex/auth.json, lists ALL available models, and probes each one for multimodal support.

**Output format:**
`json
{
  "models": [
    {"id": "mimo-v2.5", "multimodal": true},
    {"id": "mimo-v2.5-pro", "multimodal": false}
  ],
  "selected": "mimo-v2.5",
  "status": "MULTIMODAL"
}
`

**Purpose: capability awareness only.** The result tells the main agent which tasks CAN include visual checks (screenshots, UI verification). It does NOT change which model is used - all subagents inherit the parent model.

| Detection Result | Behavior |
|------------------|----------|
| MULTIMODAL | Verifiers MAY include visual/screenshot checks |
| NOT_MULTIMODAL | Verifiers skip visual checks, do text/code verification only |
| UNKNOWN | Verifiers skip visual checks |

> **Known Limitation:** spawn_agent only accepts built-in Codex models (gpt-5.6-sol, gpt-5.6-terra, etc.). Custom models from Codex++ proxy (e.g., mimo-v2.5) cannot be used as spawn_agent model overrides. All subagents must inherit the parent model. Step 0 result is for capability awareness only.


### Step 1: Clarify Intent
- Restate the user request in one paragraph.
- Identify the core deliverable.
- Identify any implicit requirements.

### Step 2: Draft Plan
- Produce a numbered plan with **exactly 7 concrete steps**.
- Each step must have a clear deliverable.
- Plan must be specific enough that a stranger could execute it.
- **Separate implementation steps from verification steps.** Do NOT mix them.

### Step 3: Define Acceptance Criteria
- For **every** plan step, write **at least one** measurable acceptance criterion.
- Each criterion must be observable and binary (PASS or FAIL).
- These criteria are passed to VERIFIER subagents in Step 5, not to workers.

### Step 4: Execute via Worker Subagents

**Spawn workers for all non-trivial steps.** Workers receive ONLY:
- The task description (what to do)
- Deliverable description (what to produce)
- Relevant file paths

Workers do NOT receive:
- Acceptance criteria (that is for verifiers)
- The 7-step workflow instructions
- Verification instructions

**Worker spawn template:**
`
multi_agent_v1__spawn_agent(
  message="<specific task instructions>",
  fork_context=false
)
`

**Rules:**
- Spawn one worker per plan step (or group small related steps).
- Workers can run in parallel when steps are independent.
- After spawning, call multi_agent_v1__wait_agent(targets=[...]) to collect results.
- If a worker fails, fix and spawn a NEW worker.

### Step 5: Verify via Verifier Subagents

**Verification is MANDATORY.** Spawn a verifier for every completed step.

Verifiers receive ONLY:
- The artifact path or description
- The acceptance criteria from Step 3
- Previous phase summaries (if applicable)

**Verifier spawn template:**
`
multi_agent_v1__spawn_agent(
  message="You are a strict verifier. Check the following artifact against the acceptance criteria.

**Artifact:** <path>

**Acceptance Criteria:**
- CRITERION 1: <description>
- CRITERION 2: <description>

For each criterion report PASS or FAIL with evidence.
If you can run/test the artifact, do so.
End with: VERDICT: ALL PASS or VERDICT: FAIL",
  fork_context=false
)
`

**Visual verification (only when Step 0 = MULTIMODAL):**
When the task involves UI, frontend, or visual output AND Step 0 detected multimodal support, the verifier SHOULD include screenshot/visual checks in its verification steps.

**Rules:**
- Verifiers MUST have fork_context=false (memoryless).
- Verifiers receive ONLY deliverables + criteria. Do NOT pass conversation history.
- If a verifier returns FAIL, fix the issue and spawn a NEW verifier.
- Split verification by scope when tasks are large (e.g., one verifier for code, one for UI).

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
- Output language must match the user's language.
