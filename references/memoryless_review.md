# Memoryless Review Protocol

## Purpose
Use memoryless subagents to verify completion without inherited assumptions.

## Input Packet
Provide only:
- Final plan
- Acceptance criteria
- Deliverable references
- Minimal repro instructions

Do not include:
- Internal thoughts
- Previous draft answers
- Suspected fixes
- Intended conclusions

## Multimodal Parity

**Critical rule: verifier capability must match task modality.**

- If the task involves images, screenshots, diagrams, UI layouts, rendered output, PDFs with visual layout, or any non-text artifact, the verifier MUST use a multimodal/vision-capable model.
- Before spawning a verifier, check:
  1. Does the task produce or consume visual artifacts?
  2. Does the parent session use a multimodal model?
  3. Does the candidate verifier model support vision?
- If the answer to (1) or (2) is yes, and (3) is no, select a different model for the verifier.
- Never strip images or visual context from the verifier input packet when the task requires visual reasoning.
- When verifying image generation, UI rendering, layout correctness, chart output, or screenshot-based tests, the verifier must see the actual visual output, not a text description of it.

## Verifier Contract
Each verifier must:
1. Restate the goal in one sentence.
2. List observable artifacts only.
3. Check each criterion independently.
4. Return `PASS` or `FAIL: <reason>`.
5. If `FAIL`, include:
   - exact unmet criterion
   - missing evidence
   - safest remediation hint

## Independence Rules
- Verifiers must not share memory.
- Verifiers must not read each other output.
- Verifiers must not assume earlier steps passed.
- Verifiers must treat missing evidence as failure.

## Escalation Rules
- If two verifiers disagree, spawn a third verifier.
- If conflict persists, treat as blocking and revise the plan.
- Stop only when all verifiers independently return PASS.

## Exit Criteria
A task is complete only when:
- Every acceptance criterion is satisfied
- Evidence exists for every satisfied criterion
- All verifier reports are PASS