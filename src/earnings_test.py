"""
Curiosity Index - step 15: the earnings announcement test.

Runs the test written down in docs/earnings_test_plan.md (committed on
6 Nov 2026, before the earnings data was downloaded): does a surge in product
page views in the weeks before a company reports predict the share-price
reaction to its results?

For each announcement on day D:
  product_surge    log(product views, days D-35 to D-6) minus log(the same
                   days a year earlier); spikes capped as elsewhere
  company_surge    the same for the company page
  gap              product_surge - company_surge
  reaction         stock return from the close 2 trading days before D to the
                   close 1 trading day after D, minus the S&P 500 (SPY)
  beat             reported EPS above analysts' estimate (1) or not (0)

Tests: thirds by product surge (and by gap) within each calendar quarter, top
minus bottom, t-statistic over quarters; and a regression of the reaction on
product and company surge together, standard errors clustered by quarter.

Writes to data/processed/:
  earnings_events.csv         one row per announcement with all measures
  earnings_test_summary.csv   the results

Run it from the project folder, after src/fetch_earnings.py:
    python src/earnings_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from fetch_pageviews import cap_spikes
from pageview_store import load_daily

START = "2018-01-01"   # a year-on-year comparison needs 2017 data
MIN_ANNOUNCEMENTS = 10
WINDOW = (35, 6)       # days before the announcement: from D-35 to D-6

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def window_views(daily: pd.DataFrame, columns: list[str], day: pd.Timestamp) -> pd.Series:
    """Total views per article over D-35 to D-6."""
    return daily.loc[day - pd.Timedelta(days=WINDOW[0]): day - pd.Timedelta(days=WINDOW[1]), columns].sum(min_count=1)


def surge(daily: pd.DataFrame, columns: list[str], day: pd.Timestamp) -> float:
    """Year-on-year log change in views, over the articles with views in both windows."""
    now = window_views(daily, columns, day)
    before = window_views(daily, columns, day - pd.DateOffset(years=1))
    usable = (now > 0) & (before > 0)
    if not usable.any():
        return np.nan
    return np.log(now[usable].sum()) - np.log(before[usable].sum())


def reaction(prices: pd.DataFrame, ticker: str, day: pd.Timestamp) -> float:
    """Return from 2 trading days before to 1 after the announcement, minus SPY."""
    days = prices.index
    i = days.searchsorted(day)  # the announcement day, or the next trading day
    if i - 2 < 0 or i + 1 >= len(days):
        return np.nan
    start, end = days[i - 2], days[i + 1]
    stock = prices.at[end, ticker] / prices.at[start, ticker] - 1
    market = prices.at[end, "SPY"] / prices.at[start, "SPY"] - 1
    return stock - market


def top_minus_bottom(events: pd.DataFrame, signal: str, outcome: str) -> dict:
    """Thirds by `signal` within each quarter; top-third minus bottom-third `outcome`."""
    data = events.dropna(subset=[signal, outcome])
    data = data[data.groupby("quarter")[signal].transform("size") >= 6]
    data = data.assign(third=data.groupby("quarter")[signal].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)))
    by_quarter = data.groupby(["quarter", "third"])[outcome].mean().unstack()
    diff = by_quarter[2] - by_quarter[0]
    return {"signal": signal, "outcome": outcome, "quarters": len(diff), "events": len(data),
            "bottom": by_quarter[0].mean(), "middle": by_quarter[1].mean(), "top": by_quarter[2].mean(),
            "top_minus_bottom": diff.mean(), "t_stat": diff.mean() / (diff.std() / np.sqrt(len(diff)))}


def clustered_regression(events: pd.DataFrame, outcome: str, signals: list[str]) -> list[dict]:
    """OLS of `outcome` on `signals`, standard errors clustered by quarter."""
    data = events.dropna(subset=[outcome, *signals])
    X = np.column_stack([np.ones(len(data)), data[signals].to_numpy()])
    y = data[outcome].to_numpy()
    xtx_inv = np.linalg.inv(X.T @ X)
    coef = xtx_inv @ X.T @ y
    resid = y - X @ coef
    meat = np.zeros((X.shape[1], X.shape[1]))
    for _, idx in data.groupby("quarter").indices.items():
        score = X[idx].T @ resid[idx]
        meat += np.outer(score, score)
    n, k, g = len(y), X.shape[1], data["quarter"].nunique()
    correction = g / (g - 1) * (n - 1) / (n - k)
    se = np.sqrt(np.diag(correction * xtx_inv @ meat @ xtx_inv))
    return [{"outcome": outcome, "variable": name, "coefficient": c, "t_stat": c / s, "events": n}
            for name, c, s in zip(["intercept", *signals], coef, se)]


def build_events(universe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One row per earnings announcement of the companies in `universe`, with all
    measures; and the companies left out for having too few announcements."""
    earnings = pd.read_csv(DATA_DIR / "earnings_dates.csv", parse_dates=["date"])
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    daily = load_daily()
    daily = cap_spikes(daily)

    # Views before a page became usable (e.g. Meta's company page before Dec 2019) are missing
    for _, row in universe.iterrows():
        for article, start in [(row["company_article"], row["company_from"]),
                               (row["product_article"], row["product_from"])]:
            if start and article:
                daily.loc[daily.index < start, article] = np.nan

    earnings = earnings[(earnings["date"] >= START) & earnings["ticker"].isin(universe["ticker"])]
    counts = earnings.groupby("ticker").size()
    left_out = sorted(set(universe["ticker"]) - set(counts[counts >= MIN_ANNOUNCEMENTS].index))
    earnings = earnings[earnings["ticker"].isin(counts[counts >= MIN_ANNOUNCEMENTS].index)]

    rows = []
    for event in earnings.itertuples():
        pages = universe[universe["ticker"] == event.ticker]
        products = [p for p in pages["product_article"] if p]  # none for company-only rows
        company = [pages["company_article"].iloc[0]]
        beat = np.nan
        if pd.notna(event.eps_estimate):
            beat = float(event.eps_reported > event.eps_estimate)
        rows.append({
            "date": event.date, "ticker": event.ticker,
            "quarter": str(event.date.to_period("Q")),
            "product_surge": surge(daily, products, event.date),
            "company_surge": surge(daily, company, event.date),
            "reaction": reaction(prices, event.ticker, event.date),
            "beat": beat,
        })
    events = pd.DataFrame(rows)
    events["gap"] = events["product_surge"] - events["company_surge"]
    return events.dropna(subset=["reaction"]), left_out


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    universe = universe[universe["cohort"] == "original"]  # the pre-registered tests use the original 68 companies
    events, left_out = build_events(universe)
    events.to_csv(DATA_DIR / "earnings_events.csv", index=False)

    sorts = [top_minus_bottom(events, signal, outcome)
             for outcome in ["reaction", "beat"] for signal in ["product_surge", "gap"]]
    regressions = [r for outcome in ["reaction", "beat"]
                   for r in clustered_regression(events, outcome, ["product_surge", "company_surge"])]
    summary = pd.concat([pd.DataFrame(sorts).assign(test="sort"),
                         pd.DataFrame(regressions).assign(test="regression")])
    summary.to_csv(DATA_DIR / "earnings_test_summary.csv", index=False)

    print(f"{len(events):,} announcements, {events['ticker'].nunique()} companies, "
          f"{events['date'].min():%b %Y} to {events['date'].max():%b %Y}. Left out (<{MIN_ANNOUNCEMENTS}): {left_out}")
    print("\nSorts (reaction in %, beat as a share):")
    show = pd.DataFrame(sorts)
    pct = show["outcome"] == "reaction"
    show.loc[pct, ["bottom", "middle", "top", "top_minus_bottom"]] *= 100
    print(show.round(3).to_string(index=False))
    print("\nRegressions (clustered by quarter):")
    print(pd.DataFrame(regressions).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
