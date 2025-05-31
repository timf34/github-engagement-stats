#!/usr/bin/env python3
"""
Create stats.md with a one-page markdown summary for every repo.
Stdlib only – no third-party installs needed.
"""

import csv
import pathlib
from collections import defaultdict
from textwrap import dedent

ROOT      = pathlib.Path(__file__).resolve().parent
DATA_DIR  = ROOT / "data"
OUT_FILE  = ROOT / "stats.md"


def latest_row(csv_path: pathlib.Path) -> dict[str, str]:
    """Return the newest (last) row from one repo CSV."""
    with csv_path.open() as fh:
        rows = list(csv.DictReader(fh))
    return rows[-1] if rows else {}


def main() -> None:
    sections: list[str] = []
    aggregate = defaultdict(int)
    last_date = "—"

    for fp in sorted(DATA_DIR.glob("*.csv")):
        row = latest_row(fp)
        if not row:
            continue                          # empty file, skip

        repo = fp.stem.replace("_", "/")
        last_date = row["date"]               # date is identical for all rows today

        for k in ("stars", "views", "clones"):
            aggregate[k] += int(row[k])

        sections.append(
            dedent(
                f"""
                ### `{repo}`

                | date | ⭐ stars | 👁 views | 📥 clones |
                |------|--------:|---------:|----------:|
                | {row['date']} | {row['stars']} | {row['views']} | {row['clones']} |
                """
            ).strip()
        )

    header = dedent(
        f"""
        # 📊 GitHub stats snapshot

        **Last run:** {last_date}

        **Totals across all tracked repos**

        | ⭐ stars | 👁 views | 📥 clones |
        |--------:|---------:|----------:|
        | {aggregate['stars']} | {aggregate['views']} | {aggregate['clones']} |

        ---
        """
    ).strip()

    OUT_FILE.write_text(
        header + "\n\n" + "\n\n---\n\n".join(sections),
        encoding="utf-8",
	)
    print(f"✅ wrote {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
