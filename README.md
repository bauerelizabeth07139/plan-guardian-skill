# Plan Guardian

A Codex skill that enforces strict, verifiable planning before execution, then validates completion with memoryless subagents.

## Why

Complex tasks fail silently when plans are loose and verification is shallow. Plan Guardian forces:
- numbered plans with measurable acceptance criteria
- independent memoryless subagent verification
- automatic revision loops until all checks pass

## Install

Copy into your Codex skills directory:

```
cp -r plan-guardian-skill ~/.codex/skills/plan-guardian
```

Or use the Codex skill install helper against this repo path.

## Usage

The skill triggers automatically on ambiguous, multi-step, or risky tasks.
You can also invoke it explicitly with `$plan-guardian`.

## Validate

```bash
python scripts/validate_skill.py .
# or with the official validator:
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Structure

```
plan-guardian/
  SKILL.md                              # Core skill instructions
  agents/openai.yaml                    # UI metadata
  assets/plan-guardian-small.svg        # Icon
  references/memoryless_review.md       # Strict verifier protocol
  references/plan_protocol.md           # Acceptance criteria patterns
  scripts/plan_guardian.py              # Sample plan generator
  scripts/validate_skill.py             # Local validator
```

## How It Works

1. Clarify intent in one paragraph.
2. Draft a numbered plan with dependencies and risks.
3. Add measurable acceptance criteria to every step.
4. Execute only after the plan is drafted.
5. Spawn memoryless subagents to verify each criterion.
6. If any verifier returns FAIL, revise the plan and re-verify.
7. Stop only when all verifiers independently return PASS.

## License

MIT
