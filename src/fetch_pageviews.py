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

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_DIR = PROJECT_DIR / "data" / "processed"


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

    # Monthly totals, complete months only
    monthly = daily.resample("MS").sum()
    if last_day.month == (last_day + timedelta(days=1)).month:  # month not finished
        monthly = monthly.iloc[:-1]
    long = monthly.stack().rename("views").reset_index()
    long.columns = ["month", "article", "views"]
    long["month"] = long["month"].dt.strftime("%Y-%m")
    long["ticker"] = long["article"].map(lambda a: articles[a]["ticker"])
    long["kind"] = long["article"].map(lambda a: articles[a]["kind"])

    # Months before a series becomes usable are missing, not zero
    usable_from = long["article"].map(lambda a: articles[a]["from"])
    long.loc[(usable_from != "") & (long["month"] < usable_from), "views"] = None

    long = long[["month", "ticker", "kind", "article", "views"]]
    long.to_csv(OUT_DIR / "pageviews_monthly.csv", index=False)

    print(f"Saved {len(daily):,} days x {daily.shape[1]} articles to {OUT_DIR / 'pageviews_daily.csv'}")
    print(f"Saved {len(long):,} article-months to {OUT_DIR / 'pageviews_monthly.csv'}")


if __name__ == "__main__":
    main()
