#!/usr/bin/env python3
"""
Generate stats.md with lifetime, last-year and last-month numbers.
Stdlib only.
"""

import csv
import datetime as dt
import pathlib
from collections import defaultdict
from textwrap import dedent

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_FILE = ROOT / "stats.md"

TODAY = dt.date.today()
D30  = TODAY - dt.timedelta(days=30)
D365 = TODAY - dt.timedelta(days=365)


def read_rows(csv_path: pathlib.Path) -> list[dict]:
    with csv_path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def aggregate(repo_rows: list[dict]) -> dict:
    sums = {
        "views_30": 0,
        "views_365": 0,
        "views_all": 0,
        "clones_30": 0,
        "clones_365": 0,
        "clones_all": 0,
        "stars_now": 0,
        "stars_delta_30": 0,
        "stars_delta_365": 0,
    }

    # rows are chronological; last row is latest snapshot
    latest = repo_rows[-1]
    sums["stars_now"] = int(latest["stars"])

    # helper for delta in star count
    def star_delta(days: int) -> int:
        cutoff = TODAY - dt.timedelta(days=days)
        earlier = next(
            (int(r["stars"]) for r in reversed(repo_rows) if dt.date.fromisoformat(r["date"]) <= cutoff),
            int(repo_rows[0]["stars"]),
        )
        return sums["stars_now"] - earlier

    sums["stars_delta_30"] = star_delta(30)
    sums["stars_delta_365"] = star_delta(365)

    for r in repo_rows:
        when = dt.date.fromisoformat(r["date"])
        v = int(r["views"])
        c = int(r["clones"])
        sums["views_all"] += v
        sums["clones_all"] += c
        if when >= D30:
            sums["views_30"] += v
            sums["clones_30"] += c
        if when >= D365:
            sums["views_365"] += v
            sums["clones_365"] += c
    return sums


def fmt(n: int) -> str:
    return f"{n:,}"


def main() -> None:
    repo_sections: list[str] = []
    grand = defaultdict(int)
    last_run = "—"

    for fp in sorted(DATA_DIR.glob("*.csv")):
        rows = read_rows(fp)
        if not rows:
            continue

        a = aggregate(rows)
        last_run = rows[-1]["date"]

        repo_name = fp.stem.replace("_", "/")

        repo_sections.append(
            dedent(
                f"""
                ### `{repo_name}`

                | metric | last 30 d | last 12 mo | lifetime |
                |--------|---------:|-----------:|---------:|
                | ⭐ stars (total) | +{fmt(a['stars_delta_30'])} | +{fmt(a['stars_delta_365'])} | {fmt(a['stars_now'])} |
                | 👁 views        | {fmt(a['views_30'])} | {fmt(a['views_365'])} | {fmt(a['views_all'])} |
                | 📥 clones       | {fmt(a['clones_30'])} | {fmt(a['clones_365'])} | {fmt(a['clones_all'])} |
                """
            ).strip()
        )

        for k, v in a.items():
            if k.startswith(("views_", "clones_")):
                grand[k] += v
        grand["stars_now"] += a["stars_now"]
        grand["stars_delta_30"] += a["stars_delta_30"]
        grand["stars_delta_365"] += a["stars_delta_365"]

    header = dedent(
        f"""
        # 📊 GitHub stats snapshot

        **Last run:** {last_run}

        | metric | last 30 d | last 12 mo | lifetime |
        |--------|---------:|-----------:|---------:|
        | ⭐ stars (total) | +{fmt(grand['stars_delta_30'])} | +{fmt(grand['stars_delta_365'])} | {fmt(grand['stars_now'])} |
        | 👁 views        | {fmt(grand['views_30'])} | {fmt(grand['views_365'])} | {fmt(grand['views_all'])} |
        | 📥 clones       | {fmt(grand['clones_30'])} | {fmt(grand['clones_365'])} | {fmt(grand['clones_all'])} |

        ---
        """
    ).strip()

    OUT_FILE.write_text(header + "\n\n" + "\n\n---\n\n".join(repo_sections), encoding="utf-8")
    print(f"✅ wrote {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
