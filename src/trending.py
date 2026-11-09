"""
Curiosity Index - step 19: trending products.

Which product pages are suddenly getting much more (or less) attention than
usual? For every product page:

  views_week      views in the latest 7 days of data
  usual_week      average weekly views over the 8 weeks before that
  change          views_week / usual_week - 1
  company_change  the same for the company's own page (is the company rising too?)
  price_change    the share price change over the same 7 days, and minus the S&P 500

One-day spikes are capped as everywhere else. Pages with fewer than 2,000 views
in a usual week are left out: on small pages a few hundred extra views look
like a big jump.

Writes data/processed/trending.csv.

Run it from the project folder:
    python src/trending.py
"""

from pathlib import Path

import pandas as pd

from fetch_pageviews import cap_spikes
from pageview_store import RECENT_PATH

MIN_USUAL_WEEK = 2000
WEEKS_OF_NORMAL = 8

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def weekly(views: pd.DataFrame, end: pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """Views in the 7 days to `end`, and the average week over the 8 weeks before."""
    this_week = views.loc[end - pd.Timedelta(days=6): end].sum()
    before = views.loc[end - pd.Timedelta(days=7 * (WEEKS_OF_NORMAL + 1) - 1): end - pd.Timedelta(days=7)]
    return this_week, before.sum() / WEEKS_OF_NORMAL


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH)
    daily = pd.read_csv(RECENT_PATH, index_col="date", parse_dates=True)
    daily = cap_spikes(daily)  # recent days only; enough history for the cap
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)

    end = daily.index.max()
    this_week, usual_week = weekly(daily, end)
    trading = prices.loc[: end]
    price_end = trading.index.max()
    price_start = trading.index[trading.index <= end - pd.Timedelta(days=7)].max()
    price_change = trading.loc[price_end] / trading.loc[price_start] - 1

    rows = []
    for r in universe.itertuples():
        rows.append({
            "product": r.product_article, "company": r.company, "ticker": r.ticker, "sector": r.sector,
            "views_week": this_week[r.product_article], "usual_week": usual_week[r.product_article],
            "change": this_week[r.product_article] / usual_week[r.product_article] - 1,
            "company_change": this_week[r.company_article] / usual_week[r.company_article] - 1,
            "price_change": price_change[r.ticker],
            "price_vs_market": price_change[r.ticker] - price_change["SPY"],
        })
    trending = pd.DataFrame(rows)
    trending = trending[trending["usual_week"] >= MIN_USUAL_WEEK].sort_values("change", ascending=False)
    trending["week_start"] = (end - pd.Timedelta(days=6)).date()
    trending["week_end"] = end.date()
    trending["price_from"] = price_start.date()
    trending["price_to"] = price_end.date()
    trending.to_csv(DATA_DIR / "trending.csv", index=False)

    print(f"Week {end - pd.Timedelta(days=6):%d %b} to {end:%d %b %Y}, {len(trending)} product pages "
          f"with at least {MIN_USUAL_WEEK:,} views in a usual week")
    show = trending[["product", "ticker", "views_week", "change", "company_change", "price_vs_market"]]
    print("Rising:\n", show.head(8).round(3).to_string(index=False))
    print("Falling:\n", show.tail(4).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
