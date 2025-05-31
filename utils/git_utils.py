"""
Tiny git helper – no external packages.
Assumes the script is invoked *inside* the repository root.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def commit_if_changes(msg: str = "chore: update traffic data") -> None:
    """Stage everything under data/ and commit if the tree is dirty."""
    subprocess.run(["git", "add", "data"], cwd=ROOT, check=True)
    dirty = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
    ).returncode != 0
    if not dirty:
        print("ℹ️  No changes – nothing to commit")
        return

    subprocess.run(
        ["git", "config", "user.name", "github-stats-bot"], cwd=ROOT, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "bot@github-stats.local"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
    print("✅ Committed new snapshot")
