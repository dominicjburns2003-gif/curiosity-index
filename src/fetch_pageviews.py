"""
Curiosity Index - step 6: page views for the whole universe.

Reads the final universe (data/mapping/products_to_companies.csv) and downloads
daily English Wikipedia page views since 2017 for every company page and every
product page. A page that was renamed has all its titles added up
(e.g. Meta_Platforms + Facebook,_Inc., or Hoka + Hoka_One_One), so its series
has no fake collapse at the rename.

Writes to data/processed/:
  pageviews_daily/       - one file per month: one row per day, one column per
                           article (see src/pageview_store.py); only articles
                           that are new, or whose titles changed, are downloaded
                           from 2017; the others from the start of last month
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

from pageview_store import STORE_DIR, load_daily, load_titles, save_daily
from wiki_api import daily_views

START = date(2017, 1, 1)
END = date.today() - timedelta(days=1)  # yesterday: today's data isn't complete
SPIKE_CAP = 10  # a day counts for at most 10x the median of the week around it
WEEK = 7  # the day itself and 3 days either side
MIN_NORMAL = 100  # only cap pages with a median of at least 100 views a day
PAUSE = 0.1  # seconds between requests (about 5 a second, well within Wikimedia's limits)

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
        if not r["product_article"]:  # a company tracked by its own page only
            continue
        articles[r["product_article"]] = {
            "titles": r["product_titles"].split("|"), "ticker": r["ticker"],
            "kind": "product", "from": r["product_from"],
        }

    # What is already saved. An article whose titles are unchanged only needs
    # the recent days (from the start of last month, to pick up days Wikimedia
    # published late); a new article, or one with new titles, needs everything.
    stored = load_daily()
    stored_titles = load_titles()
    refresh_from = (pd.Timestamp(END).to_period("M") - 1).to_timestamp().date()
    complete = {a for a, info in articles.items()
                if a in stored.columns and stored_titles.get(a) == "|".join(info["titles"])}
    to_full = [a for a in articles if a not in complete]
    n_titles = sum(len(articles[a]["titles"]) for a in to_full)
    print(f"{len(articles)} articles: {len(to_full)} downloaded from {START} ({n_titles} titles), "
          f"{len(complete)} from {refresh_from} to {END} ...")

    def download(article: str, start: date) -> pd.Series:
        parts = []
        for title in articles[article]["titles"]:
            parts.append(daily_views(title, start, END))
            time.sleep(PAUSE)  # be polite to the API
        return sum(parts)  # add up old and new titles day by day

    columns = {}
    for i, article in enumerate(list(articles), start=1):
        columns[article] = download(article, START if article in to_full else refresh_from)
        if i % 100 == 0:
            print(f"  {i}/{len(articles)} done", flush=True)

    fresh = pd.DataFrame(columns)
    days = pd.date_range(START, END, freq="D")
    daily = stored.reindex(index=days, columns=list(articles)) if not stored.empty else \
        pd.DataFrame(index=days, columns=list(articles), dtype=float)
    daily.loc[fresh.index, fresh.columns] = fresh.where(fresh.notna(), daily.loc[fresh.index, fresh.columns])
    for article in to_full:
        daily[article] = fresh[article].reindex(days).fillna(0)
    daily = daily.astype(float)
    daily.index.name = "date"
    # Wikimedia publishes each day with a delay; a day not yet published comes
    # back as all zeros, which would look like an attention crash. Cut it off.
    published = daily.index[daily.sum(axis=1) > 0]
    daily = daily.loc[: published.max()]
    last_day = daily.index.max()
    print(f"Last published day: {last_day.date()}")

    # Rewrite every month if articles were added in full, else only the refreshed months
    months = None if to_full else sorted({d.strftime("%Y-%m") for d in fresh.index})
    save_daily(daily, {a: "|".join(info["titles"]) for a, info in articles.items()}, months)

    long = monthly_totals(daily, articles)
    long.to_csv(OUT_DIR / "pageviews_monthly.csv", index=False)

    print(f"Saved {len(daily):,} days x {daily.shape[1]} articles to {STORE_DIR}")
    print(f"Saved {len(long):,} article-months to {OUT_DIR / 'pageviews_monthly.csv'}")


if __name__ == "__main__":
    main()
