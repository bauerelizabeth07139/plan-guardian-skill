---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict 7-step verifiable plan before acting, then validate execution with memoryless subagents. Apply to ALL tasks without exception. Never skip any step. Never respond without completing all 7 steps."
metadata:
  short-description: Strict 7-step planning on every request
---

# Plan Guardian

Every request goes through the full 7-step workflow. No shortcuts, no exceptions.

## Trigger Rule

**This skill MUST activate on every single user message received by the MAIN planning agent.** No exceptions for simple questions, short answers, casual conversation, quick lookups, or any task that seems trivial.

**Scope restriction: This 7-step workflow applies ONLY to the main planning agent.** Spawned subagents (workers, verifiers, diagnostics) MUST NOT run this workflow. Subagents should execute their assigned task directly and return results. When spawning a subagent, include "This is a subagent task. Do NOT run the 7-step plan-guardian workflow. Just do the assigned task directly." in the message.

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
10. Verifiers must use multimodal capabilities (screenshots) when available.

## Required Workflow

### Step 0: Detect Model Capabilities

**CRITICAL: You MUST execute the script below using exec_command or spawn_agent. Do NOT declare MULTIMODAL based on available tools, skills, environment inspection, or capability guessing. The script probes the actual model API with a real image payload. Without running the script, Step 0 is INCOMPLETE and the result is INVALID.**

Run the detection script to probe the actual model API:

`ash
python <skill_dir>/scripts/detect_multimodal.py
`

The script automatically:
- Reads API key from ~/.codex/auth.json
- Reads base URL from ~/.codex/config.toml (under [model_providers.custom])
- Reads model name from ~/.codex/config.toml (top-level model = "...")
- Probes each model with a real image+text chat completion request
- Reports MULTIMODAL / NOT_MULTIMODAL / UNKNOWN with the selected model name

If credentials are not available or discovery fails, the script reports UNKNOWN.

> **Note:** The Codex++ proxy port is dynamic and read from config.toml at runtime. No manual arguments needed.


**Store the result. It governs ALL worker/verifier model selection below.**

| Detection Result | Text/Code Worker | Visual Worker | Verifier |
|------------------|-----------------|---------------|----------|
| MULTIMODAL | Inherit parent | Use detected multimodal model | Use detected multimodal model |
| NOT_MULTIMODAL | Inherit parent | Inherit parent | Inherit parent |
| UNKNOWN | Inherit parent | Inherit parent | Inherit parent |

> **Step 0 detection subagent:** Always uses parent model (no override). Only the detection script probes for multimodal models.
> **Visual task keywords** requiring multimodal model when available: images, screenshots, diagrams, UI layout, frontend, beautification, PDFs, charts, rendered output, SVG, canvas, CSS preview.

**Visual task keywords** that require multimodal worker when NOT_MULTIMODAL:
images, screenshots, diagrams, UI layout, PDFs, charts, rendered output, SVG, canvas, CSS preview

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
- Criteria must include functional tests where applicable.

### Step 4: Execute via Worker Subagents

**Spawn workers for all non-trivial steps.** This reduces main-loop context and keeps the planner focused on coordination.

For each plan step that involves file editing, command execution, or multi-step logic, call `multi_agent_v1__spawn_agent`.

**Text/code worker (non-visual tasks):**
```
multi_agent_v1__spawn_agent(
  message="<specific task instructions>",
  fork_context=false
)
```

**Multimodal worker (visual tasks, only when Step 0 = NOT_MULTIMODAL):**
```
multi_agent_v1__spawn_agent(
  message="<specific task instructions>",
  fork_context=false
  # Do NOT override model. Always inherit parent model.
)
```

**Rules:**
- Spawn one worker per plan step (or group small related steps).
- Each worker receives ONLY: the plan step, deliverable description, and relevant file paths.
- After spawning workers, call `multi_agent_v1__wait_agent(targets=[...])` to collect results.
- If a worker fails, fix the issue and spawn a NEW worker.

**Example parallel spawn:**
```
multi_agent_v1__spawn_agent(message="Step 1: Create file X with content Z", fork_context=false)
multi_agent_v1__spawn_agent(message="Step 2: Run tests in directory A", fork_context=false)
multi_agent_v1__wait_agent(targets=["<id1>", "<id2>"])
```

### Step 5: Verify via Verifier Subagents - STRICT FUNCTIONAL VERIFICATION

**Verification is MANDATORY. You MUST spawn a verifier for every completed step.**

Verifier subagents MUST use a multimodal model when available (see Step 0 table).

**The verifier must perform ACTUAL functional testing, not just file existence checks.**

**Standard verifier (when MULTIMODAL or UNKNOWN):**
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

**Multimodal verifier (when NOT_MULTIMODAL, MUST override):**
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
  # Do NOT override model. Always inherit parent model.
)
```

**Rules:**
- Verifiers MUST have `fork_context=false` (memoryless).
- Verifiers receive ONLY deliverables + criteria. Do NOT pass conversation history.
- Each verifier independently reads the actual artifacts.
- If a verifier returns FAIL, fix the issue and spawn a NEW verifier.
- If two verifiers disagree, spawn a third. If conflict persists, treat as FAIL.
- Phase 3 must be split by scope. Use multiple subagents (for example: API functional checks, UI functional checks, edge-case and error handling checks). Do not overload one subagent with all interactions.
- Keep Phase 3 subagents small and time-bounded. Prefer fewer criteria per subagent and more subagents over a single long-running verifier.

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
- Report the Step 0 detection result and which model strategy was applied.
- Report what functional tests were performed and their results.
- Report any visual verification results (screenshots, UI checks).
- Output language must match the user's language. Internal reasoning may stay in the model language, but the final report must be in the user's language.
- Emoji is allowed, but prevent garbled output. Ensure environment/file encoding supports emoji (prefer UTF-8). If encoding is uncertain, sanitize or normalize to avoid mojibake or corrupted CJK characters.