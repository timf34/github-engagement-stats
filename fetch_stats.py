#!/usr/bin/env python3
"""
GitHub-traffic snapshot CLI / GitHub Actions entry point.
Stdlib-only, depends on collectors/github.py and utils/git_utils.py
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Dict, List

from collectors.github import collect_repo
from utils.git_utils import commit_if_changes

ROOT      = Path(__file__).resolve().parent
DATA_DIR  = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_YML = ROOT / "config.yml"            # optional


# --------------------------------------------------------------------------- #
# Config helpers
# --------------------------------------------------------------------------- #
def _parse_config_file() -> List[str]:
    """Very light YAML parser: expects 'owner/repo' per '- ' line."""
    repos: List[str] = []
    if not CONFIG_YML.exists():
        return repos
    for line in CONFIG_YML.read_text().splitlines():
        line = line.strip()
        if line.startswith("- "):
            repos.append(line[2:].strip())
    return repos


def get_target_repos() -> List[str]:
    """Env var > config.yml > current repo (GITHUB_REPOSITORY)."""
    env = os.getenv("TARGET_REPOS")
    if env:
        return [r.strip() for r in env.split(",") if r.strip()]
    cfg = _parse_config_file()
    if cfg:
        return cfg
    current = os.getenv("GITHUB_REPOSITORY")
    if current:
        return [current]
    raise SystemExit("❌ No TARGET_REPOS and no config.yml – nothing to do")


# --------------------------------------------------------------------------- #
# CSV storage
# --------------------------------------------------------------------------- #
FIELDNAMES = [
    "date",
    "owner",
    "repo",
    "stars",
    "clones",
    "unique_clones",
    "views",
    "unique_views",
]


def _save_row(row: Dict, repo_full: str) -> bool:
    """Append row to data/<owner>_<repo>.csv. Return True if new."""
    csv_path = DATA_DIR / f"{repo_full.replace('/', '_')}.csv"
    already_has_today = False
    if csv_path.exists():
        for old in csv_path.read_text().splitlines():
            if old.startswith(row["date"]):
                already_has_today = True
                break
    if already_has_today:
        return False

    with csv_path.open("a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if fh.tell() == 0:
            writer.writeheader()
        writer.writerow(row)
    return True


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("❌ GITHUB_TOKEN is required (provided automatically in Actions)")

    repos = get_target_repos()
    print(f"📈 Collecting stats for {', '.join(repos)}")

    new_rows = 0
    for full in repos:
        try:
            row = collect_repo(full, token)
            added = _save_row(row, full)
            if added:
                new_rows += 1
                print(f"✅ {full}: {row['stars']}★ {row['views']}👁  {row['clones']}📥")
            else:
                print(f"ℹ️  {full}: already had today’s snapshot")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ {full}: {exc}")

    # Commit if run with --commit and something changed
    if "--commit" in sys.argv and new_rows:
        commit_if_changes()

    # Non-zero exit if any repo failed
    if new_rows == 0:
        sys.exit(0)


if __name__ == "__main__":
    main()
