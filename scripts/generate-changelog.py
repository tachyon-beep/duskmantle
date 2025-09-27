#!/usr/bin/env python
"""Generate changelog entries from Conventional Commits."""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
CATEGORY_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "docs": "Documentation",
    "perf": "Performance",
    "refactor": "Changed",
    "chore": "Chore",
    "test": "Tests",
}


def _run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def discover_commits(since: str | None) -> list[str]:
    rev_range = f"{since}..HEAD" if since else "HEAD"
    log = _run_git(["log", rev_range, "--pretty=%s"])
    return [line for line in log.splitlines() if line]


def categorize(commits: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for subject in commits:
        prefix = subject.split(":", 1)[0]
        key = prefix.split("(")[0]
        category = CATEGORY_MAP.get(key, "Other")
        buckets[category].append(subject)
    return buckets


def update_changelog(version: str, released: str, entries: dict[str, list[str]]) -> None:
    if not CHANGELOG.exists():
        raise SystemExit("CHANGELOG.md not found. Create it before running this script.")

    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    header = f"## {version} - {released}"
    new_section = [header]
    for category in sorted(entries.keys()):
        new_section.append(f"### {category}")
        for subject in entries[category]:
            new_section.append(f"- {subject}")
        new_section.append("")

    insertion_index = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
    updated = lines[:insertion_index] + new_section + lines[insertion_index:]
    CHANGELOG.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate changelog entries from git log.")
    parser.add_argument("version", help="Version string, e.g., 0.2.0")
    parser.add_argument("--date", default=date.today().isoformat(), help="Release date (YYYY-MM-DD)")
    parser.add_argument("--since", help="Git reference to start from (e.g., previous tag)")
    args = parser.parse_args()

    commits = discover_commits(args.since)
    if not commits:
        print("No commits found for changelog section", file=sys.stderr)
        return

    categories = categorize(commits)
    update_changelog(args.version, args.date, categories)
    print(f"Updated CHANGELOG.md with {len(commits)} commits under version {args.version}")


if __name__ == "__main__":
    main()
