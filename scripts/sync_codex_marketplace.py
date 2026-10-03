#!/usr/bin/env python3
"""Refresh the nested Codex marketplace package from the repo root.

Codex marketplace entries must point at a plugin directory below the
marketplace root. Claude uses the repo root directly. This script keeps the
hidden Codex package in sync without changing the Claude-facing layout.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".codex-marketplace" / "x-skills"

PATHS_TO_COPY = [
    ".codex-plugin",
    "SKILL.md",
    "README.md",
    "assets",
    "skills",
    "references",
    "lib",
    "scripts",
    "requirements.txt",
    ".env.example",
    "LICENSE",
]


#: The user fills these with their own material. The package ships blank copies:
#: a sync must never carry a filled Voice Profile or Story Bank into a commit.
PERSONAL = ("voice-profile.md", "story-bank.md")
FILLED = re.compile(r"^\s*[-*]?\s*filled:\s*yes\b", re.M | re.I)


def copy_path(src: Path, dest: Path) -> None:
    if src.is_dir():
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        if src.name == "references":
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", *PERSONAL)
        if src.name == "scripts":
            ignore = shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "check_markdown_references.py",
                "sync_codex_marketplace.py",
            )
        shutil.copytree(src, dest, ignore=ignore)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)



def restore_blank_templates() -> list[str]:
    """Write the committed blank template into the package, never the fill.

    The working-tree copy is whatever the user filled in. The package must ship
    what git holds, so take each template from HEAD and skip any the repo does
    not track yet.
    """
    package_references = DEST / "references"
    if not package_references.is_dir():
        return []
    restored = []
    for name in PERSONAL:
        source = ROOT / "references" / name
        if not source.is_file():
            continue
        blob = subprocess.run(["git", "show", f"HEAD:references/{name}"],
                              cwd=ROOT, capture_output=True, text=True)
        if blob.returncode == 0:
            text = blob.stdout
        else:
            # A template added in the working tree is not in HEAD yet. Copy it
            # only while it is still blank, so a first sync can never be the
            # thing that publishes someone's filled bank.
            text = source.read_text(encoding="utf-8")
            if FILLED.search(text[:4000]):
                print(f"  refusing to copy {name}: it is marked `filled: yes` and "
                      f"is not committed blank yet")
                continue
        (package_references / name).write_text(text, encoding="utf-8")
        restored.append(name)
    return restored

def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    for rel in PATHS_TO_COPY:
        copy_path(ROOT / rel, DEST / rel)

    kept = restore_blank_templates()

    print(f"Synced Codex marketplace package: {DEST.relative_to(ROOT)}")
    if kept:
        print("  templates kept blank, not copied from the working "
              "tree: " + ", ".join(kept))


if __name__ == "__main__":
    main()
