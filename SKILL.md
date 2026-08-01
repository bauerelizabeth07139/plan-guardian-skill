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

### Step 0: Detect Model Capabilities (ONCE per conversation)

**Run this step ONLY at the start of the conversation (first user message).** Cache the result and reuse it for all subsequent messages in the same conversation. Do NOT re-run the detection script on follow-up messages.

**CRITICAL: You MUST execute the script below using exec_command or spawn_agent. Do NOT declare MULTIMODAL based on available tools, skills, environment inspection, or capability guessing. The script probes the actual model API with a real image payload. Without running the script, Step 0 is INCOMPLETE and the result is INVALID.**

Run the detection script to probe the actual model API:

`ash
python <skill_dir>/scripts/detect_multimodal.py
`

The script automatically:
- Reads API key from ~/.codex/auth.json
- Reads base URL from ~/.codex/config.toml (under [model_providers.custom])
- Reads model name from ~/.codex/config.toml (top-level model = "...")
- Lists ALL available models from the endpoint
- Probes EACH model with a real image+text chat completion request
- Returns a JSON with all models and their multimodal status

**Output format:**
`json
{
  "mode": "auto",
  "used_base": "http://127.0.0.1:57321/v1",
  "models": [
    {"id": "mimo-v2.5", "multimodal": true},
    {"id": "mimo-v2.5-pro", "multimodal": false},
    {"id": "mimo-v2.5-asr", "multimodal": false}
  ],
  "selected": "mimo-v2.5",
  "status": "MULTIMODAL"
}
`

Use selected as the multimodal model for visual workers/verifiers. Use any multimodal: false model for text/code tasks if needed.

If credentials are not available or discovery fails, the script reports UNKNOWN.

> **Note:** The Codex++ proxy port is dynamic and read from config.toml at runtime. No manual arguments needed.

**Caching rule:** After Step 0 completes, remember the selected model name and status. For all subsequent user messages in this conversation, skip Step 0 and reuse the cached result directly.

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

For each plan step that involves file editing, command execution, or multi-step logic, call multi_agent_v1__spawn_agent.

**Text/code worker (non-visual tasks):**
`
multi_agent_v1__spawn_agent(
  message="This is a subagent task. Do NOT run the 7-step plan-guardian workflow. Just do the assigned task directly.\n\n<specific task instructions>",
  fork_context=false
)
`

**Visual worker (UI, frontend, beautification, screenshots) — when Step 0 = MULTIMODAL:**
`
multi_agent_v1__spawn_agent(
  message="This is a subagent task. Do NOT run the 7-step plan-guardian workflow. Just do the assigned task directly.\n\n<specific task instructions>",
  fork_context=false,
  model="<detected multimodal model, e.g. mimo-v2.5>"
)
`

**Visual worker — when Step 0 = NOT_MULTIMODAL or UNKNOWN:**
Same as text/code worker (inherit parent, no override).

**How to determine the model name:** Use the selected field from the Step 0 detection script output (e.g., "selected": "mimo-v2.5" → model="mimo-v2.5").

**Rules:**
- Spawn one worker per plan step (or group small related steps).
- Each worker receives ONLY: the plan step, deliverable description, and relevant file paths.
- After spawning workers, call multi_agent_v1__wait_agent(targets=[...]) to collect results.
- If a worker fails, fix the issue and spawn a NEW worker.

### Step 5: Verify via Verifier Subagents - STRICT FUNCTIONAL VERIFICATION

**Verification is MANDATORY. You MUST spawn a verifier for every completed step.**

**Verifier model selection (based on Step 0):**
- Step 0 = MULTIMODAL: use model="<detected multimodal model>" for ALL verifiers
- Step 0 = NOT_MULTIMODAL or UNKNOWN: inherit parent (no override)

**The verifier must perform ACTUAL functional testing, not just file existence checks.**

**Verifier template:**
`
multi_agent_v1__spawn_agent(
  message="This is a subagent task. Do NOT run the 7-step plan-guardian workflow.

You are a STRICT functional verifier. Your job is to BREAK the work, not approve it.

**Task:** Verify the following artifact with ACTUAL functional testing.

**Artifact:** <path or description>

**Acceptance Criteria:**
- CRITERION 1: <description>
- CRITERION 2: <description>

**You MUST perform these verification steps:**
1. READ: Actually read the file contents. Report the first 20 lines and last 20 lines.
2. CHECK STRUCTURE: Verify all required sections, fields, keys exist.
3. CHECK CONTENT: Verify values are correct, not placeholders, not empty.
4. CHECK SYNTAX: If it is code/config, verify no syntax errors.
5. FUNCTIONAL TEST: If possible, actually run/test the artifact.
6. EDGE CASES: Look for missing error handling, empty values, wrong types.
7. VISUAL CHECK (if multimodal): Take a screenshot and verify the UI looks correct.

**Output Format:**
For each criterion:
- CRITERION N: PASS or FAIL
- Evidence: <exact evidence>
- Test performed: <what you actually did>

End with: VERDICT: ALL PASS or VERDICT: FAIL

**CRITICAL: If you cannot perform functional testing, report FAIL.**",
  fork_context=false,
  model="<detected multimodal model>"  # omit this line when NOT_MULTIMODAL or UNKNOWN
)
`

**Rules:**
- Verifiers MUST have ork_context=false (memoryless).
- Verifiers receive ONLY deliverables + criteria. Do NOT pass conversation history.
- Each verifier independently reads the actual artifacts.
- If a verifier returns FAIL, fix the issue and spawn a NEW verifier.
- If two verifiers disagree, spawn a third. If conflict persists, treat as FAIL.
- Phase 3 must be split by scope. Use multiple subagents for different types of checks.
- Keep Phase 3 subagents small and time-bounded.

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