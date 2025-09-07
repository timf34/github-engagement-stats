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
        if err.code == 403:
            remaining = err.headers.get("X-RateLimit-Remaining")
            retry_after = err.headers.get("Retry-After")
            reset_hdr = err.headers.get("X-RateLimit-Reset")
            is_rate_limited = (remaining == "0") or (retry_after is not None)
            if is_rate_limited:
                sleep_for = 0
                if retry_after is not None:
                    try:
                        sleep_for = int(retry_after)
                    except ValueError:
                        sleep_for = 0
                elif reset_hdr:
                    try:
                        reset = int(reset_hdr)
                        sleep_for = max(0, reset - int(time.time()) + 1)
                    except ValueError:
                        sleep_for = 0
                sleep_for = min(sleep_for, 60)
                if sleep_for:
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

# --------------------------------------------------------------------------- #
# Repo-discovery helpers  
# --------------------------------------------------------------------------- #
def _paginate(endpoint: str, token: str) -> List[Dict]:
    """Return a full list from any paginated GitHub REST endpoint."""
    items, page = [], 1
    while True:
        chunk = _request(f"{endpoint}?per_page=100&page={page}", token)
        items.extend(chunk)
        if len(chunk) < 100:     # last page
            break
        page += 1
    return items


def discover_repos(owner: str | None, token: str, min_stars: int = 3) -> List[str]:
    """
    Return ['owner/repo', …] for every *public* repo that
    1. belongs to <owner>  –OR–  if <owner> is falsy, belongs to the
       account tied to the token (GET /user) and
    2. has at least <min_stars> stars.
    """
    if not owner:  # local run where GITHUB_REPOSITORY is absent
        owner = _request("/user", token)["login"]

    # try personal account first
    try:
        raw = _paginate(f"/users/{owner}/repos", token)
    except urllib.error.HTTPError as err:
        if err.code != 404:
            raise
        # maybe an organisation
        raw = _paginate(f"/orgs/{owner}/repos", token)

    return [
        f"{owner}/{repo['name']}"
        for repo in raw
        if not repo.get("private")
        and repo.get("stargazers_count", 0) >= min_stars
    ]
