"""
Curiosity Index - step 7: clickstream history for the whole universe.

Wikipedia publishes a monthly "clickstream" file: for every pair of pages,
how many times readers clicked a link from page A (prev) to page B (curr).
Each file is about 470 MB compressed, so we stream it line by line, keep only
the rows we need, and never save the full file.

We keep every click INTO one of our company pages (under any of its titles).
That includes the clicks from product pages, which give the conversion rate,
and the clicks from everywhere else (search engines, news, lawsuits), which
show where company readers come from.

Each month is saved as its own small file in data/processed/clickstream/, so
an interrupted run picks up where it stopped. Two months are downloaded at a
time, which is what Wikimedia's dump servers allow.

Run it from the project folder:
    python src/fetch_clickstream.py                    # every month, Nov 2017 onwards
    python src/fetch_clickstream.py 2024-09 2026-10    # only these months
"""

from concurrent.futures import ThreadPoolExecutor
import gzip
from pathlib import Path
import sys

import pandas as pd
import requests

from wiki_api import HEADERS

FIRST_MONTH = "2017-11"  # earliest file on the dump server
URL = "https://dumps.wikimedia.org/other/clickstream/{month}/clickstream-enwiki-{month}.tsv.gz"
PARALLEL_DOWNLOADS = 2

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_DIR = PROJECT_DIR / "data" / "processed" / "clickstream"


def available_months() -> list[str]:
    """Every month from FIRST_MONTH whose file has been published."""
    listing = requests.get(
        "https://dumps.wikimedia.org/other/clickstream/", headers=HEADERS, timeout=30
    ).text
    months = pd.period_range(FIRST_MONTH, pd.Timestamp.today(), freq="M").strftime("%Y-%m")
    return [m for m in months if f'href="{m}/"' in listing]


def fetch_month(month: str, company_titles: set[str]) -> None:
    """Stream one month's file and save the clicks into our company pages."""
    out_path = OUT_DIR / f"{month}.csv.gz"
    if out_path.exists():
        return
    rows = []
    with requests.get(URL.format(month=month), headers=HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        with gzip.open(response.raw, mode="rt", encoding="utf-8") as lines:
            for line in lines:
                prev, curr, link_type, n = line.rstrip("\n").split("\t")
                if curr in company_titles:
                    rows.append((month, prev, curr, link_type, int(n)))
    data = pd.DataFrame(rows, columns=["month", "prev", "curr", "type", "n"])
    # Write to a temporary name first, so a crash never leaves a half-written file
    tmp_path = out_path.with_suffix(".tmp")
    data.to_csv(tmp_path, index=False, compression="gzip")
    tmp_path.rename(out_path)
    print(f"{month}: kept {len(data):,} rows")


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    company_titles = {t for titles in universe["company_titles"] for t in titles.split("|")}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    months = sys.argv[1:] or available_months()
    todo = [m for m in months if not (OUT_DIR / f"{m}.csv.gz").exists()]
    print(f"{len(months)} months requested, {len(todo)} still to download "
          f"({len(company_titles)} company titles)")

    with ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOADS) as pool:
        # list() makes any error inside a download show up here
        list(pool.map(lambda m: fetch_month(m, company_titles), todo))

    print(f"Done. Files in {OUT_DIR}")


if __name__ == "__main__":
    main()
