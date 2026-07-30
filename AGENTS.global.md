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

### Step 5: Verifier Subagents

For EVERY completed step, you MUST call:
```
multi_agent_v1__spawn_agent(
  message="Verify the following:\n\n**Artifact:** <path>\n\n**Acceptance Criteria:**\n- CRITERION 1: <description>\n\nRead the actual artifact. Report PASS or FAIL with reason. End with: VERDICT: ALL PASS or VERDICT: FAIL",
  fork_context=false
)
```
If Step 0 = NOT_MULTIMODAL, add `model="<multimodal model>"`.

NEVER skip verification. ALWAYS spawn a verifier for every completed step.

### After Verification

If a verifier returns FAIL, fix the issue, spawn a NEW worker, then spawn a NEW verifier. Never reuse failed agents.