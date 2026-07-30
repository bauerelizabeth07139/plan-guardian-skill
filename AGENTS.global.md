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

### Step 5: Verifier Subagents - STRICT FUNCTIONAL VERIFICATION

For EVERY completed step, you MUST spawn a verifier. The verifier must perform ACTUAL functional testing, not just file existence checks.

**Verifier prompt template:**
```
multi_agent_v1__spawn_agent(
  message="You are a STRICT functional verifier. Your job is to BREAK the work, not approve it.

**Task:** Verify the following artifact with ACTUAL functional testing.

**Artifact:** <path or description>

**Acceptance Criteria:**
- CRITERION 1: <description>
- CRITERION 2: <description>

**You MUST perform these verification steps:**

1. READ: Actually read the file contents. Report the first 20 lines and last 20 lines.
2. CHECK STRUCTURE: Verify all required sections, fields, keys exist.
3. CHECK CONTENT: Verify values are correct, not placeholders, not empty.
4. CHECK SYNTAX: If it's code/config, verify no syntax errors.
5. FUNCTIONAL TEST: If possible, actually run/test the artifact:
   - For code: run it and check output
   - For configs: validate them
   - For APIs: call them
   - For servers: start them and test endpoints
   - For frontend: take a screenshot and verify visually
6. EDGE CASES: Look for missing error handling, empty values, wrong types.
7. VISUAL CHECK (if multimodal): Take a screenshot and verify the UI looks correct.

**Output Format:**
For each criterion:
- CRITERION N: PASS or FAIL
- Evidence: <exact file content, line number, test output, or screenshot that proves PASS or FAIL>
- Test performed: <what you actually did to verify>

End with: VERDICT: ALL PASS or VERDICT: FAIL (list unmet criteria numbers and exact reasons)

**CRITICAL: If you cannot perform functional testing, report FAIL with reason: 'Cannot verify - no functional test performed'. Do NOT approve based on file existence alone.**",
  fork_context=false
)
```

If Step 0 = NOT_MULTIMODAL, add `model="<multimodal model>"` for visual verification.

NEVER skip verification. ALWAYS spawn a verifier for every completed step.

### After Verification

If a verifier returns FAIL, fix the issue, spawn a NEW worker, then spawn a NEW verifier. Never reuse failed agents.