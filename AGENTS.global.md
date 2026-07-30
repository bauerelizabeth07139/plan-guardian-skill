# MANDATORY WORKFLOW - READ THIS FIRST

**You MUST follow this workflow on EVERY user message. No exceptions. No shortcuts.**

## Step 0: Detect Model Capabilities

Before ANY other action, spawn a diagnostic subagent:
```
multi_agent_v1__spawn_agent(message="Run: python C:\Users\vipuser\.codex\skills\.system\plan-guardian\scripts\detect_multimodal.py. Report: MULTIMODAL, NOT_MULTIMODAL, or UNKNOWN.", fork_context=false)
```
Wait for result. Store it for all model selection decisions.

## Step 1: Clarify Intent

Restate the user request. Identify core deliverable. Identify implicit requirements.

## Step 2: Draft Plan

Produce exactly 7 numbered steps. Each with clear deliverable.

## Step 3: Define Acceptance Criteria

For each step, write at least one binary PASS/FAIL criterion.

## Step 4: Execute via Worker Subagents

For each non-trivial step, spawn a worker:
```
multi_agent_v1__spawn_agent(message="<task instructions>", fork_context=false)
```
If Step 0 = NOT_MULTIMODAL and task is visual, add model="<multimodal model>".

After spawning, call multi_agent_v1__wait_agent(targets=[...]).

NEVER execute work inline. Always spawn workers.

## Step 5: Verify via Verifier Subagents

For EVERY completed step, spawn a STRICT verifier:
```
multi_agent_v1__spawn_agent(message="You are a STRICT functional verifier. Your job is to BREAK the work, not approve it.

**Artifact:** <path>

**Acceptance Criteria:**
- CRITERION 1: <description>

**You MUST:**
1. READ the actual file contents. Report first 20 lines.
2. CHECK all required fields/sections exist.
3. CHECK values are correct, not placeholders.
4. CHECK syntax - no errors.
5. FUNCTIONAL TEST - actually run/test the artifact.
6. CHECK edge cases - missing error handling, empty values.
7. VISUAL CHECK (if multimodal) - screenshot and verify UI.

For each criterion: PASS or FAIL with exact evidence.

VERDICT: ALL PASS or VERDICT: FAIL with reasons.

CRITICAL: If you cannot functional test, report FAIL. Do NOT approve based on file existence alone.", fork_context=false)
```
If Step 0 = NOT_MULTIMODAL, add model="<multimodal model>".

## Step 6: Re-Plan if Needed

If any verifier FAIL: analyze, revise plan, re-execute with new worker, re-verify with new verifier.

## Step 7: Final Report

Summarize: what done, all steps status (PASS/FAIL), files changed, verdict, Step 0 result.