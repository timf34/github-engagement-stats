"""
Pure-stdlib GitHub collector.

Exposes one public helper:
    collect_repo(full_name: 'owner/repo', token: str) -> dict
that returns the snapshot needed for the CSV.
"""

from __future__ import annotations

import datetime as dt
import json
import time
import urllib.error
import urllib.request
from typing import Dict, List, Tuple

BASE_URL = "https://api.github.com"
UA       = "github-traffic-collector/1.0"


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def _request(endpoint: str, token: str) -> Dict:
    """GET <endpoint>, return decoded JSON, retry once on rate-limit."""
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept"               : "application/vnd.github+json",
            "Authorization"        : f"Bearer {token}",
            "X-GitHub-Api-Version" : "2022-11-28",
            "User-Agent"           : UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        # Soft-retry on secondary rate-limit (status 403 + special header)
        if err.code == 403 and err.headers.get("X-RateLimit-Reset"):
            reset = int(err.headers["X-RateLimit-Reset"])
            sleep_for = max(0, reset - int(time.time()) + 1)
            time.sleep(sleep_for)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        raise


def _latest_day(items: List[Dict]) -> Tuple[int, int]:
    """Return (count, uniques) for *today* or the most recent entry."""
    if not items:
        return 0, 0
    today = dt.date.today().isoformat()
    for it in items:
        if it["timestamp"].startswith(today):
            return it["count"], it["uniques"]
    newest = max(items, key=lambda d: d["timestamp"])
    return newest["count"], newest["uniques"]


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def collect_repo(full_name: str, token: str) -> Dict:
    """
    Collect stars + today's traffic snapshot for one repo.

    Returns a mapping with keys:
        date, owner, repo, stars, clones, unique_clones, views, unique_views
    """
    owner, repo = full_name.split("/", 1)

    repo_json   = _request(f"/repos/{owner}/{repo}", token)
    stars       = repo_json["stargazers_count"]

    try:
        clones_json = _request(f"/repos/{owner}/{repo}/traffic/clones", token)
        views_json  = _request(f"/repos/{owner}/{repo}/traffic/views",  token)
        clones, u_clones = _latest_day(clones_json["clones"])
        views,  u_views  = _latest_day(views_json["views"])
    except urllib.error.HTTPError as err:
        # If traffic endpoints are unavailable (e.g. repo is a fork),
        # still record stars and zeroes for traffic.
        if err.code in (403, 404):
            clones = u_clones = views = u_views = 0
        else:
            raise

    return {
        "date"          : dt.date.today().isoformat(),
        "owner"         : owner,
        "repo"          : repo,
        "stars"         : stars,
        "clones"        : clones,
        "unique_clones" : u_clones,
        "views"         : views,
        "unique_views"  : u_views,
    }
