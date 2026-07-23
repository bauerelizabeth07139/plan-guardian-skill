from __future__ import annotations
import json
from dataclasses import dataclass


@dataclass
class PlanStep:
    step: str
    evidence_hint: str
    acceptance: str


DEFAULT_PLAN = [
    PlanStep("Understand intent", "Restated goal summary", "Goal summary exists"),
    PlanStep("Design artifacts", "Draft outline or schema", "Outline exists"),
    PlanStep("Implement artifacts", "Changed files or code paths", "Concrete artifacts exist"),
    PlanStep("Verify completion", "Verifier report", "All checks PASS"),
]


def build_plan(goal: str, context: str = "", strictness: int = 3) -> dict:
    return {
        "goal": goal,
        "context": context,
        "strictness": strictness,
        "requirements": [
            "Every step must have acceptance criteria",
            "Verification must use memoryless subagents",
            "Failures must trigger plan revision and re-verification",
        ],
        "steps": [vars(step) for step in DEFAULT_PLAN],
        "verification_policy": {
            "min_verifiers": 2,
            "allow_shared_memory": False,
            "required_output": ["PASS", "FAIL: <reason>"],
        },
        "loop_policy": {
            "continue_until": "all_steps_verified",
            "remediation_required_on_fail": True,
        },
    }


if __name__ == "__main__":
    sample = build_plan("Create a strict planning workflow")
    print(json.dumps(sample, indent=2, ensure_ascii=False))

