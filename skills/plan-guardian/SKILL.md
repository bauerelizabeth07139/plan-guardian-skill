---
name: plan-guardian
description: "ALWAYS use this skill on every user request without exception. Generate a strict 7-step verifiable plan before acting, then validate execution with memoryless subagents. Apply to ALL tasks without exception. Never skip any step. Never respond without completing all 7 steps."
metadata:
  short-description: Strict 7-step planning on every request
---

# Plan Guardian

Every request goes through the full 7-step workflow. No shortcuts, no exceptions.

## Trigger Rule

**This skill MUST activate on every single user message received by the MAIN planning agent.** No exceptions. Step 0 runs once per conversation and its result is reused.

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
10. All subagents inherit the parent session's model. Never override the model in a subagent call.

## Required Workflow

### Step 0: Establish Verification Capability (ONCE per conversation)

**Run this step ONLY at the start of the conversation.** Cache the result and reuse it for all subsequent messages.

On DeepSeek Harness there is no model probe to run:

- **Visual checks are always available.** The harness ships `read_image`, which reads a PNG/JPEG/WebP/GIF into the conversation. Any verifier can therefore inspect a screenshot, a rendered chart or a diagram even when the session model has no built-in vision. Treat capability as `MULTIMODAL`.
- **Subagents cannot be given a different model.** `subagent` and `subagent_fork` run on the session's model, so "detect which model to spawn" is not a decision this skill makes. The original Codex script that probed a model API is still in [`scripts/detect_multimodal.py`](../../scripts/detect_multimodal.py) for Codex users; it reads `~/.codex` and `~/.mimo2codex` and is not used here.

| Capability | Behavior |
|---|---|
| always (DSH) | Verifiers MAY include visual checks through `read_image` |

### Step 1: Clarify Intent
- Restate the user request in one paragraph.
- Identify the core deliverable.
- Identify any implicit requirements.

### Step 2: Draft Plan
- Produce a numbered plan with **exactly 7 concrete steps**.
- Each step must have a clear deliverable.
- Plan must be specific enough that a stranger could execute it.
- **Separate implementation steps from verification steps.** Do NOT mix them.
- The acceptance-criteria pattern and the plan shape are in
  [`references/plan_protocol.md`](references/plan_protocol.md).

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

```
subagent(
  description="<3-5 word task name>",
  prompt="<specific task instructions: what to do, the deliverable, the paths>"
)
```

**Rules:**
- Spawn one worker per plan step (or group small related steps).
- Subagents run in the background and report back when they settle; spawn the
  independent ones together and keep working while they run.
- If a worker fails, fix and spawn a NEW worker.

### Step 5: Verify via Verifier Subagents

**Verification is MANDATORY.** Spawn a verifier for every completed step.

Verifiers receive ONLY:
- The artifact path or description
- The acceptance criteria from Step 3
- Previous phase summaries (if applicable)

**Verifier spawn template:**

```
subagent(
  description="Verify <artifact>",
  prompt="You are a strict verifier. Check the following artifact against the acceptance criteria.

**Artifact:** <path>

**Acceptance Criteria:**
- CRITERION 1: <description>
- CRITERION 2: <description>

For each criterion report PASS or FAIL with evidence.
If you can run/test the artifact, do so.
End with: VERDICT: ALL PASS or VERDICT: FAIL"
)
```

**Rules:**
- Verifiers MUST be memoryless: spawn them with `subagent`, never
  `subagent_fork`. A forked verifier inherits this conversation's assumptions
  and is not independent. The protocol is in
  [`references/memoryless_review.md`](references/memoryless_review.md).
- Verifiers receive ONLY deliverables + criteria. Do NOT pass conversation history.
- If a verifier returns FAIL, fix the issue and spawn a NEW verifier.
- Split verification by scope when tasks are large (e.g., one verifier for code, one for UI).
- Visual verification is always permitted: a verifier may use `read_image` on a
  screenshot or a rendered artifact.

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

## Tool mapping (Codex → DeepSeek Harness)

| Codex | DeepSeek Harness |
|---|---|
| `multi_agent_v1__spawn_agent(message=…, fork_context=false)` | `subagent(description=…, prompt=…)` |
| `multi_agent_v1__wait_agent(targets=[…])` | subagents report back on their own; collect results when notified |
| `apply_patch` | `edit` / `write` |
| `shell` | `pwsh` (Windows) or the session's shell tool |
| `read_file` | `read` |
| a vision model probe | `read_image`, available to every agent |
