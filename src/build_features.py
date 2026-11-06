"""
Curiosity Index - step 10: the monthly panel.

One row per company per month t. Every feature uses only what was known at the
end of month t; every target is measured over month t+1. This is the table
the portfolio sorts, the model and the app all read.

Features (CLAUDE.md section 7.1):
  company_views       company-page views in month t
  company_abn         abnormal company attention: log views in t vs the mean
                      and spread of the previous 6 months, in standard deviations
  company_growth      log(views in t / average of the previous 6 months)
  product_views       total views of the company's product pages in t
  product_growth      the same growth measure, for total product views
  gap                 product_growth - company_growth: products getting more
                      attention than the company itself
  momentum            return over months t-11 to t-1 (the usual 12-month
                      momentum, leaving out the latest month)
  log_mcap            log market cap at the end of t (size)
  vol                 volatility of daily returns in month t (annualised)

Targets (section 7.2), all over month t+1:
  ret_next            return
  ret_vs_mkt_next     return minus the market return (Fama-French Mkt-RF + RF)
  rank_next           rank of ret_next among the companies that month (0 to 1)
  vol_next            volatility of daily returns (annualised)

Click-through (conversion) features are added once the clickstream is final.

Run it from the project folder:
    python src/build_features.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

WINDOW = 6  # months of history that "normal" attention is measured against

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"


def trailing_growth(wide: pd.DataFrame) -> pd.DataFrame:
    """log(this month / average of the previous WINDOW months), per column.
    1 is added to both, so growth from a page with no views yet is finite."""
    past_mean = wide.shift(1).rolling(WINDOW).mean()
    return np.log((wide + 1) / (past_mean + 1))


def to_long(wide: pd.DataFrame, name: str) -> pd.Series:
    """Months x tickers table -> one column indexed by (month, ticker)."""
    return wide.stack(future_stack=True).rename(name)


def main() -> None:
    views = pd.read_csv(DATA_DIR / "pageviews_monthly.csv")
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    returns = returns.drop(columns="SPY")  # the market fund, not a company
    factors = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")
    mcap = pd.read_csv(DATA_DIR / "market_cap_monthly.csv").pivot(index="month", columns="ticker", values="mcap")
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    prices = prices.drop(columns="SPY")

    # ---- Company attention ---------------------------------------------------
    company = views[views["kind"] == "company"].pivot(index="month", columns="ticker", values="views")
    company = company.where(company > 0)  # 0 views = no usable series, not "no interest"
    log_company = np.log(company)
    past = log_company.shift(1).rolling(WINDOW)
    company_abn = (log_company - past.mean()) / past.std()
    company_growth = trailing_growth(company)

    # ---- Product attention ---------------------------------------------------
    # Total product views per company. A product only counts in a month if it
    # had views in that month and the WINDOW months before. Otherwise a new page
    # being created (e.g. a drug page going from 0 to 2,000 views) would look
    # like a huge jump in attention.
    product = views[views["kind"] == "product"].pivot(index="month", columns="article", values="views")
    has_history = (product > 0).rolling(WINDOW + 1).sum() == WINDOW + 1
    ticker_of = views[views["kind"] == "product"].groupby("article")["ticker"].first()
    product_views = product.T.groupby(ticker_of).sum(min_count=1).T
    growth_parts = {}
    for ticker, articles in ticker_of.groupby(ticker_of).groups.items():
        cols = list(articles)
        # For each month t, sum views (t and the 6 months before) of the products usable at t
        totals = pd.DataFrame(index=product.index, columns=range(WINDOW + 1), dtype=float)
        for lag in range(WINDOW + 1):
            totals[lag] = product[cols].shift(lag).where(has_history[cols]).sum(axis=1, min_count=1)
        growth_parts[ticker] = np.log((totals[0] + 1) / (totals.loc[:, 1:].mean(axis=1) + 1))
    product_growth = pd.DataFrame(growth_parts)

    # ---- Returns, size and volatility ----------------------------------------
    momentum = (1 + returns).shift(1).rolling(11).apply(np.prod, raw=True) - 1
    daily_ret = prices.pct_change(fill_method=None)
    vol = daily_ret.groupby(daily_ret.index.strftime("%Y-%m")).std() * np.sqrt(252)
    vol = vol.where(daily_ret.groupby(daily_ret.index.strftime("%Y-%m")).count() >= 15)
    if vol.index[-1] > returns.index[-1]:
        vol = vol.iloc[:-1]  # the current month is not finished
    log_mcap = np.log(mcap)

    # ---- Targets: month t+1, placed on the row of month t -------------------
    market = factors["Mkt-RF"] + factors["RF"]
    ret_next = returns.shift(-1)
    ret_vs_mkt_next = ret_next.sub(market.reindex(returns.index).shift(-1), axis=0)
    rank_next = ret_next.rank(axis=1, pct=True)
    vol_next = vol.shift(-1)

    panel = pd.concat([
        to_long(company, "company_views"),
        to_long(company_abn, "company_abn"),
        to_long(company_growth, "company_growth"),
        to_long(product_views, "product_views"),
        to_long(product_growth, "product_growth"),
        to_long(momentum, "momentum"),
        to_long(log_mcap, "log_mcap"),
        to_long(vol, "vol"),
        to_long(ret_next, "ret_next"),
        to_long(ret_vs_mkt_next, "ret_vs_mkt_next"),
        to_long(rank_next, "rank_next"),
        to_long(vol_next, "vol_next"),
    ], axis=1)
    panel.index.names = ["month", "ticker"]
    panel["gap"] = panel["product_growth"] - panel["company_growth"]
    panel = panel.reset_index()

    # Keep months where attention data exists (pageviews start Jan 2017)
    panel = panel[(panel["month"] >= views["month"].min()) & (panel["month"] <= views["month"].max())]
    panel = panel.sort_values(["month", "ticker"])
    panel.to_csv(DATA_DIR / "panel_monthly.csv", index=False)
    print(f"Saved {len(panel):,} company-months ({panel['ticker'].nunique()} companies, "
          f"{panel['month'].min()} to {panel['month'].max()}) to {DATA_DIR / 'panel_monthly.csv'}")


if __name__ == "__main__":
    main()
