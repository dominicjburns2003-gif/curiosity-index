"""
Curiosity Index - step 3: check the draft universe.

Reads data/mapping/universe_draft.csv (one row per company-product pair) and
checks every row automatically, so the hand check only has to deal with the
problems:

  1. Titles: does each Wikipedia article exist, and is the title a redirect
     (meaning the article now lives under another name)?
  2. Attention: average monthly views over the last 12 months, and the first
     month with meaningful views (a late start can mean a rename or a new page).
  3. Click-through: clicks from the product page to the company page in one
     recent clickstream month (pairs with 10 or fewer clicks are not published).
  4. Prices: does yfinance have the ticker from January 2017 up to now?

Writes data/mapping/universe_check.csv, one row per company-product pair with a
"flags" column listing anything to look at.

Run it from the project folder:
    python src/check_universe.py                     # checks the draft
    python src/check_universe.py data/mapping/products_to_companies.csv
"""

import gzip
from pathlib import Path
import sys
import time
from urllib.parse import quote

import pandas as pd
import requests
import yfinance as yf

# ---- Settings you can change ------------------------------------------------

CLICKSTREAM_MONTH = "2026-10"  # recent month used to test click-through
VIEWS_START, VIEWS_END = "20170101", "20261031"
MIN_PRODUCT_VIEWS = 3000  # monthly views below this are flagged as too small

HEADERS = {
    "User-Agent": "CuriosityIndex/0.1 "
    "(https://github.com/dominicjburns2003-gif/curiosity-index; emlyon student research project)"
}
WIKI_API = "https://en.wikipedia.org/w/api.php"
VIEWS_API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user/{title}/monthly/{start}/{end}"
)
CLICKSTREAM_URL = (
    "https://dumps.wikimedia.org/other/clickstream/{month}/"
    "clickstream-enwiki-{month}.tsv.gz"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
DRAFT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else MAPPING_DIR / "universe_draft.csv"
# Results are named after the input file, e.g. universe_draft -> universe_draft_check.csv
CLICKS_PATH = MAPPING_DIR / f"{DRAFT_PATH.stem}_clicks_{CLICKSTREAM_MONTH}.csv"
OUT_PATH = MAPPING_DIR / f"{DRAFT_PATH.stem}_check.csv"


def polite_get(url: str, **kwargs) -> requests.Response:
    """GET a URL; if the server says "too many requests" (429), wait and try again."""
    for attempt in range(6):
        response = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
        if response.status_code != 429:
            return response
        wait = int(response.headers.get("Retry-After", 0)) or 5 * 2**attempt
        print(f"  rate-limited, waiting {wait}s ...")
        time.sleep(wait)
    response.raise_for_status()
    return response


def resolve_titles(titles: list[str]) -> dict[str, str | None]:
    """Map each title to the article it really points to (None if it doesn't exist)."""
    result = {}
    for i in range(0, len(titles), 50):  # the API accepts 50 titles per call
        batch = titles[i : i + 50]
        params = {
            "action": "query", "titles": "|".join(batch),
            "redirects": 1, "format": "json", "formatversion": 2,
        }
        data = polite_get(WIKI_API, params=params).json()["query"]
        # Follow the API's chain: normalised spelling -> redirect -> final page
        step = {}
        for kind in ("normalized", "redirects"):
            for item in data.get(kind, []):
                step[item["from"]] = item["to"]
        missing = {p["title"] for p in data["pages"] if p.get("missing")}
        for title in batch:
            name = title.replace("_", " ")
            while name in step:
                name = step[name]
            result[title] = None if name in missing else name.replace(" ", "_")
        time.sleep(0.5)
    return result


def monthly_views(title: str) -> pd.Series:
    """Monthly page views of one article since 2017 (empty if none)."""
    url = VIEWS_API.format(title=quote(title, safe=""), start=VIEWS_START, end=VIEWS_END)
    response = polite_get(url)
    if response.status_code == 404:
        return pd.Series(dtype=int)
    response.raise_for_status()
    items = response.json()["items"]
    dates = pd.to_datetime([item["timestamp"][:8] for item in items], format="%Y%m%d")
    return pd.Series([item["views"] for item in items], index=dates)


def clickstream_pairs(products: set[str], companies: set[str]) -> pd.DataFrame:
    """Clicks from any of our product pages to any of our company pages, in one month.

    The file is streamed and only matching rows are kept. The result is saved, so
    the slow download only happens once.
    """
    if CLICKS_PATH.exists():
        return pd.read_csv(CLICKS_PATH)
    print(f"Streaming the {CLICKSTREAM_MONTH} clickstream file (a few minutes) ...")
    rows = []
    url = CLICKSTREAM_URL.format(month=CLICKSTREAM_MONTH)
    with requests.get(url, headers=HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        with gzip.open(response.raw, mode="rt", encoding="utf-8") as lines:
            for line in lines:
                prev, curr, link_type, n = line.rstrip("\n").split("\t")
                if prev in products and curr in companies:
                    rows.append((prev, curr, int(n)))
    pairs = pd.DataFrame(rows, columns=["prev", "curr", "n"])
    pairs.to_csv(CLICKS_PATH, index=False)
    return pairs


def price_coverage(tickers: list[str]) -> pd.DataFrame:
    """First and last trading day yfinance has for each ticker since 2017."""
    rows = []
    for ticker in tickers:
        prices = yf.download(ticker, start="2017-01-01", progress=False, auto_adjust=True)
        prices = prices.dropna()
        first = prices.index.min().date() if len(prices) else None
        last = prices.index.max().date() if len(prices) else None
        rows.append((ticker, first, last))
    return pd.DataFrame(rows, columns=["ticker", "price_first", "price_last"])


def main() -> None:
    draft = pd.read_csv(DRAFT_PATH)

    # 1. Titles
    titles = sorted(set(draft["company_article"]) | set(draft["product_article"]))
    print(f"Resolving {len(titles)} Wikipedia titles ...")
    current = resolve_titles(titles)
    draft["company_current"] = draft["company_article"].map(current)
    draft["product_current"] = draft["product_article"].map(current)

    # 2. Attention
    print("Downloading monthly views ...")
    stats = {}
    for title in sorted({t for t in current.values() if t}):
        views = monthly_views(title)
        last12 = views.iloc[-12:].mean() if len(views) else 0
        # First month with views above 10% of the recent level
        meaningful = views[views > 0.1 * last12] if len(views) else views
        first = meaningful.index.min().strftime("%Y-%m") if len(meaningful) else None
        stats[title] = (round(last12), first)
        time.sleep(0.5)
    draft["product_views_12m"] = draft["product_current"].map(lambda t: stats.get(t, (0, None))[0])
    draft["company_views_12m"] = draft["company_current"].map(lambda t: stats.get(t, (0, None))[0])
    draft["product_first_month"] = draft["product_current"].map(lambda t: stats.get(t, (0, None))[1])
    draft["company_first_month"] = draft["company_current"].map(lambda t: stats.get(t, (0, None))[1])

    # 3. Click-through
    pairs = clickstream_pairs(
        set(draft["product_current"].dropna()), set(draft["company_current"].dropna())
    )
    clicks = pairs.groupby(["prev", "curr"])["n"].sum()
    draft["clicks_to_company"] = [
        clicks.get((p, c), 0) for p, c in zip(draft["product_current"], draft["company_current"])
    ]
    month_views = {}
    for title in draft["product_current"].dropna().unique():
        v = monthly_views(title)
        month_views[title] = v.get(pd.Timestamp(CLICKSTREAM_MONTH + "-01"), 0)
        time.sleep(0.3)
    product_month_views = draft["product_current"].map(month_views).fillna(0)
    draft["conversion_pct"] = (
        100 * draft["clicks_to_company"] / product_month_views.where(product_month_views > 0)
    ).round(2)

    # 4. Prices
    print("Checking price history ...")
    draft = draft.merge(price_coverage(sorted(draft["ticker"].unique())), on="ticker", how="left")

    # Flags: anything worth a human look
    recent = pd.Timestamp.today().normalize() - pd.Timedelta(days=10)
    flags = []
    for _, r in draft.iterrows():
        f = []
        if r["company_current"] is None:
            f.append("company page missing")
        elif r["company_current"] != r["company_article"]:
            f.append(f"company renamed/redirects to {r['company_current']}")
        if r["product_current"] is None:
            f.append("product page missing")
        elif r["product_current"] != r["product_article"]:
            f.append(f"product redirects to {r['product_current']}")
        if r["product_views_12m"] < MIN_PRODUCT_VIEWS:
            f.append("low product views")
        if r["clicks_to_company"] == 0:
            f.append("no clicks to company page")
        if (r["company_first_month"] or "2017-01") > "2017-01":
            f.append(f"company views start {r['company_first_month']}")
        if r["price_first"] is None or pd.isna(r["price_first"]):
            f.append("no price data")
        else:
            if str(r["price_first"]) > "2017-01-31":
                f.append(f"prices start {r['price_first']}")
            if pd.Timestamp(r["price_last"]) < recent:
                f.append(f"prices end {r['price_last']} (delisted?)")
        flags.append("; ".join(f))
    draft["flags"] = flags

    draft.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(draft)} rows to {OUT_PATH}")
    print(f"{draft['ticker'].nunique()} companies, {(draft['flags'] == '').sum()} rows with no flags")


if __name__ == "__main__":
    main()
