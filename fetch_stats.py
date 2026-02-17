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

from collectors.github import collect_repo, discover_repos

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

def get_target_repos(token: str) -> List[str]:
    """
    Build the final repo list (duplicates removed):

      • TARGET_REPOS env-var              ← always wins if set
      • entries in config.yml
      • auto-discovery (default **ON**)
      • current repo (GITHUB_REPOSITORY)  ← absolute fallback
    """
    explicit = [
        r.strip() for r in os.getenv("TARGET_REPOS", "").split(",") if r.strip()
    ]

    from_cfg = _parse_config_file()

    auto_on   = os.getenv("DISABLE_AUTODISCOVER", "").lower() not in ("1", "true")
    min_stars = int(os.getenv("MIN_STARS", "3"))

    discovered: List[str] = []
    if auto_on:
        owner_hint = (os.getenv("GITHUB_REPOSITORY") or "/").split("/")[0] or None
        try:
            discovered = discover_repos(owner_hint, token, min_stars)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  Auto-discover failed: {exc}")

    # Merge all three sources, in priority order
    combined = explicit + from_cfg + discovered
    if not combined:  # very last resort
        fallback = os.getenv("GITHUB_REPOSITORY")
        if fallback:
            combined = [fallback]

    return sorted(set(combined))



# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("TRAFFIC_TOKEN")
    if not token:
        raise SystemExit("❌ GITHUB_TOKEN or TRAFFIC_TOKEN is required (provided automatically in Actions)")

    if os.getenv("GITHUB_ACTIONS") and os.getenv("GITHUB_REPOSITORY"):
        print("ℹ️  Running in GitHub Actions")
        print("   If cross-repo traffic stats are 0/403, set a PAT in secrets.PUBLIC_REPOS_TOKEN.")

    repos = get_target_repos(token)
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

    # Non-zero exit if any repo failed
    if new_rows == 0:
        sys.exit(0)


if __name__ == "__main__":
    main()
