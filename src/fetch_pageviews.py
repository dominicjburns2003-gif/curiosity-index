"""
Curiosity Index - step 6: page views for the whole universe.

Reads the final universe (data/mapping/products_to_companies.csv) and downloads
daily English Wikipedia page views since 2017 for every company page and every
product page. A page that was renamed has all its titles added up
(e.g. Meta_Platforms + Facebook,_Inc., or Hoka + Hoka_One_One), so its series
has no fake collapse at the rename.

Writes two files to data/processed/:
  pageviews_daily.csv    - one row per day, one column per article
  pageviews_monthly.csv  - one row per article per complete month, with the
                           ticker and whether it is a company or product page

One-day spikes are capped before the monthly totals are added up: no day can
count for more than 10 times the median of the week around it (3 days either
side, within the same month, so nothing from the next month is used). Some
spikes are automated traffic counted as human readers (e.g. Arm & Hammer:
183,353 views on 1 Dec 2017 against about 200 a day), and one such day can
make up most of a month. Real news keeps views high for several days, which
lifts the median of the week, so it is left alone (Boeing 737 MAX grounding,
Kate Spade's death, Pfizer's vaccine: all unchanged). Comparing with the month
before instead cut those real stories by 60-80%, so that was not used. Pages
with a median below 100 views a day are not capped. The daily file keeps the
raw views, and the monthly file has both: views (capped) and views_raw.

Run it from the project folder:
    python src/fetch_pageviews.py
"""

from datetime import date, timedelta
from pathlib import Path
import time

import pandas as pd

from wiki_api import daily_views

START = date(2017, 1, 1)
END = date.today() - timedelta(days=1)  # yesterday: today's data isn't complete
SPIKE_CAP = 10  # a day counts for at most 10x the median of the week around it
WEEK = 7  # the day itself and 3 days either side
MIN_NORMAL = 100  # only cap pages with a median of at least 100 views a day

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_DIR = PROJECT_DIR / "data" / "processed"


def cap_spikes(daily: pd.DataFrame) -> pd.DataFrame:
    """Limit each day to SPIKE_CAP times the median of the week around it."""
    by_month = daily.groupby(daily.index.to_period("M"), group_keys=False)
    normal = by_month.apply(lambda month: month.rolling(WEEK, center=True, min_periods=3).median())
    cap = (SPIKE_CAP * normal).where(normal >= MIN_NORMAL)  # no cap: NaN
    return daily.where(cap.isna() | (daily <= cap), cap)


def monthly_totals(daily: pd.DataFrame, articles: dict) -> pd.DataFrame:
    """Monthly views per article (complete months only), in long format."""
    last_day = daily.index.max()
    totals = {"views": cap_spikes(daily), "views_raw": daily}
    for name, table in totals.items():
        monthly = table.resample("MS").sum()
        if last_day.month == (last_day + timedelta(days=1)).month:  # month not finished
            monthly = monthly.iloc[:-1]
        totals[name] = monthly.stack()
    long = pd.DataFrame(totals).reset_index()
    long.columns = ["month", "article", "views", "views_raw"]
    long["month"] = long["month"].dt.strftime("%Y-%m")
    long["ticker"] = long["article"].map(lambda a: articles[a]["ticker"])
    long["kind"] = long["article"].map(lambda a: articles[a]["kind"])

    # Months before a series becomes usable are missing, not zero
    usable_from = long["article"].map(lambda a: articles[a]["from"])
    long.loc[(usable_from != "") & (long["month"] < usable_from), ["views", "views_raw"]] = None
    return long[["month", "ticker", "kind", "article", "views", "views_raw"]]


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # One entry per article we track: which titles to add up, and what it is
    articles = {}
    for _, r in universe.iterrows():
        articles[r["company_article"]] = {
            "titles": r["company_titles"].split("|"), "ticker": r["ticker"],
            "kind": "company", "from": r["company_from"],
        }
        articles[r["product_article"]] = {
            "titles": r["product_titles"].split("|"), "ticker": r["ticker"],
            "kind": "product", "from": r["product_from"],
        }

    n_titles = sum(len(a["titles"]) for a in articles.values())
    print(f"Downloading {len(articles)} articles ({n_titles} titles), {START} to {END} ...")
    columns = {}
    for i, (article, info) in enumerate(articles.items(), start=1):
        parts = []
        for title in info["titles"]:
            parts.append(daily_views(title, START, END))
            time.sleep(0.5)  # be polite to the API
        columns[article] = sum(parts)  # add up old and new titles day by day
        if i % 20 == 0:
            print(f"  {i}/{len(articles)} done")

    daily = pd.DataFrame(columns)
    daily.index.name = "date"
    # Wikimedia publishes each day with a delay; a day not yet published comes
    # back as all zeros, which would look like an attention crash. Cut it off.
    published = daily.index[daily.sum(axis=1) > 0]
    daily = daily.loc[: published.max()]
    last_day = daily.index.max()
    print(f"Last published day: {last_day.date()}")
    daily.to_csv(OUT_DIR / "pageviews_daily.csv")

    long = monthly_totals(daily, articles)
    long.to_csv(OUT_DIR / "pageviews_monthly.csv", index=False)

    print(f"Saved {len(daily):,} days x {daily.shape[1]} articles to {OUT_DIR / 'pageviews_daily.csv'}")
    print(f"Saved {len(long):,} article-months to {OUT_DIR / 'pageviews_monthly.csv'}")


if __name__ == "__main__":
    main()
