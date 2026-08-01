# Repository Instructions for Codex

## Scope
These instructions apply to every file in this repository.

## Execution Policy
- Keep the main planning loop lightweight.
- Delegate implementation to worker subagents.
- Delegate verification to verifier subagents (fork_context=false).
- Never self-verify.

## Model Policy
- All subagents inherit the parent model. Never override model in spawn_agent calls.
- Step 0 detection result is for capability awareness only (whether to attempt visual checks).
- Step 0 runs once per conversation, result is cached for reuse.

## Worker vs Verifier
- **Workers**: receive task + deliverable. Do the implementation. No acceptance criteria.
- **Verifiers**: receive artifact + acceptance criteria. Check the work. Memoryless (fork_context=false).

## Context Minimization
- Pass file paths and task descriptions to subagents, not full file contents.
- Return structured results: paths, artifacts, PASS/FAIL summaries.
