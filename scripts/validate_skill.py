from __future__ import annotations
import sys
from pathlib import Path

required_files = ["SKILL.md", "agents/openai.yaml"]
required_frontmatter = ["name", "description"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_skill.py <skill-folder>")
        return 2
    root = Path(sys.argv[1])
    errors: list[str] = []

    for rel in required_files:
        p = root / rel
        if not p.exists():
            errors.append(f"Missing required file: {rel}")

    skill_path = root / "SKILL.md"
    if skill_path.exists():
        text = read_text(skill_path)
        if not text.startswith("---"):
            errors.append("SKILL.md must start with YAML frontmatter")
        for field in required_frontmatter:
            if f"{field}:" not in text:
                errors.append(f"SKILL.md frontmatter missing field: {field}")
    else:
        errors.append("Cannot validate frontmatter because SKILL.md is missing")

    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("VALIDATION OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

