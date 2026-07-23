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

