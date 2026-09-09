#!/usr/bin/env python3
"""Fail if a credential, or a file that holds one, is tracked by git.

`.gitignore` is not the safety net people assume. It only stops *untracked*
files from being added, so renaming the tracked `.env.example` to `.env`, which
the GitHub web UI offers as a one-click rename, commits a real `.env` straight
past it. That happened in linkedin-skills#28 and put a live Publora key and an
Apify token into a public branch.

Removing the file in a later commit does not help: the blob stays reachable at
the earlier SHA. The only thing that helps is never committing it.

Usage: python3 scripts/check_no_secrets.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Files that hold credentials by definition, wherever they sit in the tree.
FORBIDDEN_NAMES = re.compile(r"(^|/)\.env(\.[^/]*)?$")
# `.env.example` and `.env.sample` are the documented templates and carry no
# secrets, so they are the one exception.
TEMPLATE_NAMES = re.compile(r"(^|/)\.env\.(example|sample|template)$")

# Real key shapes, with enough trailing entropy to exclude the placeholders that
# appear all over the docs (`sk_your_api_key`, `apify_api_xxx`).
SECRET_PATTERNS = [
    ("Publora API key", re.compile(r"\bsk_[a-z0-9]{6,}[._][A-Za-z0-9]{32,}")),
    ("Apify token", re.compile(r"\bapify_api_[A-Za-z0-9]{30,}")),
    ("Pixfaro token", re.compile(r"\bpf_live_[A-Za-z0-9]{24,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("OpenAI key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9_-]{40,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

TEXT_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".txt", ".sh", ".toml",
                 ".cfg", ".ini", ".env", ".example", ""}


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def main() -> int:
    problems: list[str] = []

    for rel in tracked_files():
        if FORBIDDEN_NAMES.match(rel) and not TEMPLATE_NAMES.search(rel):
            problems.append(
                f"{rel}: a .env file is tracked. Untrack it with "
                f"`git rm --cached {rel}`, then rotate anything it held: removing "
                f"it in a later commit leaves the blob reachable in history.")

        path = ROOT / rel
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text[:match.start()].count("\n") + 1
                problems.append(
                    f"{rel}:{line}: looks like a live {label}. If it is real, "
                    f"rotate it now; the value is already in git history.")

    if problems:
        print("Tracked credentials:\n" + "\n".join("  " + p for p in problems))
        return 1

    print(f"OK: {len(tracked_files())} tracked files, no .env and no credential "
          f"patterns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
