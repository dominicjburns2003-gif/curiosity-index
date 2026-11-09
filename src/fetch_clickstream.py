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
    python src/fetch_clickstream.py --new-only         # only months newer than the
                                                       # latest saved one (daily update)
    python src/fetch_clickstream.py --into DIR         # every month, into another folder
                                                       # (e.g. when companies are added: the
                                                       # current files stay in use until done)
"""

from concurrent.futures import ThreadPoolExecutor
import gzip
from pathlib import Path
import sys
import time

import pandas as pd
import requests
import urllib3

from wiki_api import HEADERS

FIRST_MONTH = "2017-11"  # earliest file on the dump server
URL = "https://dumps.wikimedia.org/other/clickstream/{month}/clickstream-enwiki-{month}.tsv.gz"
PARALLEL_DOWNLOADS = 2
TIMEOUT = (30, 180)  # seconds to connect, and to wait for the next piece of data

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


def stream_rows(month: str, company_titles: set[str]) -> list[tuple]:
    """Stream one month's file once and return the clicks into our company pages."""
    rows = []
    with requests.get(URL.format(month=month), headers=HEADERS, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        with gzip.open(response.raw, mode="rt", encoding="utf-8") as lines:
            for line in lines:
                prev, curr, link_type, n = line.rstrip("\n").split("\t")
                if curr in company_titles:
                    rows.append((month, prev, curr, link_type, int(n)))
    return rows


def fetch_month(month: str, company_titles: set[str]) -> bool:
    """Download one month (retrying if the connection drops) and save it.
    Returns False if it still failed, so the other months can carry on."""
    out_path = OUT_DIR / f"{month}.csv.gz"
    if out_path.exists():
        return True
    # Long downloads sometimes get cut off or time out; start that month again.
    # Errors in the middle of a download come from urllib3 (the library under requests).
    for attempt in range(1, 5):
        try:
            rows = stream_rows(month, company_titles)
            break
        except (requests.RequestException, urllib3.exceptions.HTTPError, OSError, EOFError) as error:
            print(f"{month}: download failed ({type(error).__name__}), attempt {attempt} of 4")
            time.sleep(60 * attempt)  # give a busy server time to recover
    else:
        print(f"{month}: download failed 4 times, skipping it for now")
        return False
    data = pd.DataFrame(rows, columns=["month", "prev", "curr", "type", "n"])
    # Write to a temporary name first, so a crash never leaves a half-written file
    tmp_path = out_path.with_suffix(".tmp")
    data.to_csv(tmp_path, index=False, compression="gzip")
    tmp_path.rename(out_path)
    print(f"{month}: kept {len(data):,} rows")
    return True


def main() -> None:
    global OUT_DIR
    if "--into" in sys.argv:
        position = sys.argv.index("--into")
        OUT_DIR = Path(sys.argv[position + 1]).resolve()
        del sys.argv[position:position + 2]
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    company_titles = {t for titles in universe["company_titles"] for t in titles.split("|")}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if sys.argv[1:] == ["--new-only"]:
        saved = sorted(p.name[:7] for p in OUT_DIR.glob("*.csv.gz"))
        if not saved:
            # The full history is downloaded by hand once (it takes hours);
            # the daily update only adds new months on top of it
            print("No clickstream history saved yet: run without --new-only first")
            return
        months = [m for m in available_months() if m > saved[-1]]
    else:
        months = sys.argv[1:] or available_months()
    todo = [m for m in months if not (OUT_DIR / f"{m}.csv.gz").exists()]
    print(f"{len(months)} months requested, {len(todo)} still to download "
          f"({len(company_titles)} company titles)")

    with ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOADS) as pool:
        # list() makes any other error inside a download show up here
        succeeded = list(pool.map(lambda m: fetch_month(m, company_titles), todo))

    failed = [m for m, ok in zip(todo, succeeded) if not ok]
    if failed:
        # Exit with an error, so a scheduled run is marked as failed
        sys.exit(f"Failed months (run the script again to retry them): {', '.join(failed)}")
    print(f"Done. Files in {OUT_DIR}")


if __name__ == "__main__":
    main()
