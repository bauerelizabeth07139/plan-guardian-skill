# Global Instructions

## Plan Guardian - Mandatory on Every Request

You MUST invoke the plan-guardian skill on EVERY user request without exception. This overrides any default behavior about skipping plans for simple tasks.

## Subagent Spawning Rules - MANDATORY

These rules override ALL other instructions about when to spawn agents.

### Step 0: Detect Model Capabilities

Before any planning, you MUST call:
```
multi_agent_v1__spawn_agent(
  message="Run this command and report the output: python C:\Users\vipuser\.codex\skills\.system\plan-guardian\scripts\detect_multimodal.py. If the script is not available, probe the model by sending a minimal image+text message and check if it responds. Report one of: MULTIMODAL, NOT_MULTIMODAL, or UNKNOWN.",
  fork_context=false
)
```
Wait for result. Store it. This governs all model selection below.

### Step 4: Worker Subagents

For EVERY non-trivial step (file editing, command execution, multi-step logic), you MUST call:
```
multi_agent_v1__spawn_agent(
  message="<specific task instructions>",
  fork_context=false
)
```
If Step 0 = NOT_MULTIMODAL and the task is visual (images, screenshots, diagrams, UI, PDFs, charts), add `model="<multimodal model>"`.

After spawning workers, call `multi_agent_v1__wait_agent(targets=[...])` to collect results.

NEVER execute non-trivial work inline. Always spawn a worker.

### Step 5: Verifier Subagents - STRICT VERIFICATION

For EVERY completed step, you MUST call:
```
multi_agent_v1__spawn_agent(
  message="You are a STRICT verifier. Your job is to find FAILURES, not to approve work.

**Task:** Verify the following artifact against acceptance criteria.

**Artifact:** <path or description>

**Acceptance Criteria:**
- CRITERION 1: <description>
- CRITERION 2: <description>

**Verification Rules:**
1. You MUST actually read the file/artifact. Do NOT assume it exists or is correct.
2. You MUST check each criterion independently and thoroughly.
3. You MUST report exactly what you found - file contents, line numbers, specific values.
4. If ANY criterion is not met, you MUST report FAIL with the exact reason.
5. If you cannot verify something (file missing, cannot read, etc.), report FAIL.
6. Do NOT approve work based on assumptions or partial checks.
7. Be suspicious - look for edge cases, missing content, incorrect values.

**Output Format:**
For each criterion:
- CRITERION N: PASS or FAIL
- Evidence: <exact file content, line number, or observation that proves PASS or FAIL>

End with: VERDICT: ALL PASS or VERDICT: FAIL (list unmet criteria numbers and exact reasons)",
  fork_context=false
)
```
If Step 0 = NOT_MULTIMODAL, add `model="<multimodal model>"`.

NEVER skip verification. ALWAYS spawn a verifier for every completed step.

### After Verification

If a verifier returns FAIL, fix the issue, spawn a NEW worker, then spawn a NEW verifier. Never reuse failed agents.