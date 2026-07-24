# Repository Instructions for Codex

## Scope
These instructions apply to every file in this repository.

## Execution Policy
- Keep the main planning loop lightweight.
- Delegate implementation, file inspection, builds, and test execution to subagents whenever a task touches multiple files, runs commands, or requires long context.
- Never self-verify. Use memoryless verifier subagents for acceptance checks.

## Model Policy
- Prefer inheriting the parent model for text/code-only subtasks.
- When a task involves images, screenshots, diagrams, UI, PDFs with visual layout, or rendered artifacts, use a multimodal model for workers and verifiers.
- If the parent model is not multimodal, set the subagent model explicitly for that visual subtask.

## Context Minimization
- Pass file paths and acceptance criteria to subagents instead of pasting long content into the planner.
- Return structured results only: paths, artifacts, and PASS/FAIL summaries.
