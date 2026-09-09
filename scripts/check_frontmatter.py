#!/usr/bin/env python3
"""Parse every SKILL.md frontmatter with a strict YAML loader.

Counting directories does not tell you a skill loads. In v1.0.26 an
unescaped apostrophe inside a single-quoted `description` terminated the
scalar early, the frontmatter failed to parse, and the loader skipped the
directory in silence: users got 10 of 11 skills with no error anywhere,
while sibling skills kept pointing at the one that had vanished.

Long prose descriptions outgrow whichever quoting style they were written
in, so this checks what a strict loader sees rather than trusting the
style. Reported by @FSLATT1 (linkedin-skills#21).

Usage: python3 scripts/check_frontmatter.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
REQUIRED = ("name", "description")


def documents() -> list[Path]:
    docs = sorted((ROOT / "skills").glob("*/SKILL.md"))
    root = ROOT / "SKILL.md"
    if root.is_file():
        docs.append(root)
    return docs


def main() -> int:
    problems: list[str] = []
    docs = documents()

    for path in docs:
        rel = path.relative_to(ROOT)
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{rel}: no YAML frontmatter block")
            continue
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            detail = str(exc).splitlines()[0]
            problems.append(f"{rel}: frontmatter does not parse ({detail})")
            continue
        if not isinstance(data, dict):
            problems.append(f"{rel}: frontmatter is not a mapping")
            continue
        for key in REQUIRED:
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{rel}: '{key}' is missing or empty")
        name = data.get("name")
        if isinstance(name, str) and path.parent != ROOT and name != path.parent.name:
            problems.append(f"{rel}: name '{name}' does not match folder '{path.parent.name}'")

    if problems:
        print("Frontmatter problems:\n" + "\n".join("  " + p for p in problems))
        return 1

    skills = [d for d in docs if d.parent != ROOT]
    print(f"OK: {len(skills)} skills plus the root document parse and declare "
          f"name and description.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
