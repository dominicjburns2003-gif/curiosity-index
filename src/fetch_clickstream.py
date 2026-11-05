"""
Curiosity Index - step 2: the clickstream test.

Wikipedia publishes a monthly "clickstream" file: for every pair of pages,
how many times readers clicked a link from page A (prev) to page B (curr).
Each file is about 470 MB compressed, so we stream it line by line, keep only
the rows that involve our pages, and never save the full file.

We keep two kinds of rows:
  1. every click INTO the company page (to see where its readers come from)
  2. every click OUT OF a product page (to see where product readers go)
The row "Semaglutide -> Novo_Nordisk" is in both, and is the one that matters.

Run it from the project folder, giving the months to fetch:
    python src/fetch_clickstream.py 2018-09 2024-09 2026-10
"""

import gzip
from pathlib import Path
import sys

import pandas as pd
import requests

# ---- Settings you can change ------------------------------------------------

# All titles the company article has had (it was renamed on 14 Sep 2026)
COMPANY_TITLES = {"Novo_Nordisk", "Novo_(company)"}
PRODUCT_TITLES = {"Semaglutide"}

HEADERS = {"User-Agent": "CuriosityIndex/0.1 (emlyon student research project)"}
URL = "https://dumps.wikimedia.org/other/clickstream/{month}/clickstream-enwiki-{month}.tsv.gz"

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT_DIR / "data" / "processed" / "clickstream_novo.csv"


def fetch_month(month: str) -> pd.DataFrame:
    """Stream one month's clickstream file and keep only the rows we need."""
    url = URL.format(month=month)
    rows = []
    with requests.get(url, headers=HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        # Decompress on the fly while downloading
        with gzip.open(response.raw, mode="rt", encoding="utf-8") as lines:
            for line in lines:
                prev, curr, link_type, n = line.rstrip("\n").split("\t")
                if curr in COMPANY_TITLES or prev in PRODUCT_TITLES:
                    rows.append((month, prev, curr, link_type, int(n)))
    return pd.DataFrame(rows, columns=["month", "prev", "curr", "type", "n"])


def main() -> None:
    months = sys.argv[1:]
    if not months:
        sys.exit("Give at least one month, e.g. python src/fetch_clickstream.py 2024-09")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Keep months already downloaded, so re-running only fetches new ones
    if OUT_PATH.exists():
        saved = pd.read_csv(OUT_PATH, dtype={"month": str})
    else:
        saved = pd.DataFrame(columns=["month", "prev", "curr", "type", "n"])

    for month in months:
        if month in set(saved["month"]):
            print(f"{month}: already saved, skipping")
            continue
        print(f"{month}: streaming the file (a few minutes) ...")
        new = fetch_month(month)
        print(f"{month}: kept {len(new):,} rows")
        saved = pd.concat([saved, new], ignore_index=True)
        saved.to_csv(OUT_PATH, index=False)  # save after every month

    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
