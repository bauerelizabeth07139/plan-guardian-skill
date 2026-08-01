# Repository Instructions for Codex

## Scope
These instructions apply to every file in this repository.

## Execution Policy
- Keep the main planning loop lightweight.
- Delegate implementation, file inspection, builds, and test execution to subagents whenever a task touches multiple files, runs commands, or requires long context.
- Never self-verify. Use memoryless verifier subagents for acceptance checks.

## Model Policy
- Text/code tasks: inherit parent model.
- Visual tasks (images, UI, frontend, screenshots, beautification, diagrams, PDFs): use the multimodal model discovered by Step 0 when available (MULTIMODAL). Otherwise inherit parent.
- Step 0 detection subagent: always uses parent model (no override).
- Step 0 should discover available models when credentials are available, probe likely multimodal candidates, and fall back to UNKNOWN/parent when discovery is not possible.
- Subagents MUST NOT run the 7-step plan-guardian workflow. They execute assigned tasks directly.

## Context Minimization
- Pass file paths and acceptance criteria to subagents instead of pasting long content into the planner.
- Return structured results only: paths, artifacts, and PASS/FAIL summaries.
