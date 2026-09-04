#!/usr/bin/env python3
"""Check relative Markdown references declared by skill documents."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REFERENCE = re.compile(r"`((?:\.\.?/)+[^`#\s]+\.md)(?:#[^`]*)?`")


def main() -> None:
    broken: list[str] = []

    for document in sorted(SKILLS.rglob("*.md")):
        text = document.read_text(encoding="utf-8")
        for match in REFERENCE.finditer(text):
            target = (document.parent / match.group(1)).resolve()
            if not target.is_file():
                broken.append(
                    f"{document.relative_to(ROOT)}: {match.group(1)}"
                )

    if broken:
        raise SystemExit("Broken Markdown references:\n" + "\n".join(broken))

    print("All relative Markdown references resolve.")


if __name__ == "__main__":
    main()
