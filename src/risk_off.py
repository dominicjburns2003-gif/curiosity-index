"""
Curiosity Index - step 33: risk-off, switching from shares to bonds.

Runs the test written down in docs/risk_off_plan.md (committed on 10 Nov 2026
before this was written): hold the S&P 500 normally, and US government bonds
(IEF) in weeks when public worry on Wikipedia is unusually high, by one of two
signals (market-wide attention to company pages; views of five "worry"
pages), at three levels (above the 80th, 90th or 95th percentile of earlier
weeks). Also a check with cash (T-bills) instead of bonds.

Writes data/processed/risk_off_summary.csv, risk_off_weekly.csv and
worry_pages_daily.csv.

Run it from the project folder:
    python src/risk_off.py
"""

from datetime import date, timedelta
from pathlib import Path
import time

import numpy as np
import pandas as pd
import yfinance as yf

from attention_wave import PUBLICATION_LAG, weekly_attention
from fetch_pageviews import cap_spikes
from pageview_store import load_daily
from wiki_api import daily_views

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

WORRY_PAGES = ["Recession", "Stock_market_crash", "Inflation", "Stagflation", "Bank_run"]
LEVELS = [0.80, 0.90, 0.95]
FIRST_DECISION = "2018-03-01"
COST_PER_SWITCH = 0.001
BONDS = "IEF"


def worry_views() -> pd.Series:
    """Combined daily views of the worry pages (spikes capped as everywhere else)."""
    start, end = date(2017, 1, 1), date.today() - timedelta(days=1)
    daily = pd.DataFrame({page: daily_views(page, start, end) for page in WORRY_PAGES})
    time.sleep(0.2)
    published = daily.index[daily.sum(axis=1) > 0]
    daily = daily.loc[: published.max()]
    daily.index.name = "date"
    daily.to_csv(DATA_DIR / "worry_pages_daily.csv")
    return cap_spikes(daily).sum(axis=1)


def above_past(series: pd.Series, level: float) -> pd.Series:
    """True when a week's value is above the given percentile of all earlier weeks."""
    past = series.shift(1).expanding(min_periods=52).quantile(level)
    return series > past


def measures(r: pd.Series, rf: pd.Series) -> dict:
    weeks = len(r)
    growth = (1 + r).prod()
    annual = growth ** (52 / weeks) - 1
    vol = r.std() * np.sqrt(52)
    rf_annual = (1 + rf).prod() ** (52 / weeks) - 1
    path = (1 + r).cumprod()
    return {"weeks": weeks, "growth_100": 100 * growth, "annual_return": annual, "volatility": vol,
            "sharpe": (annual - rf_annual) / vol, "worst_fall": (path / path.cummax().clip(lower=1) - 1).min()}


def main() -> None:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    universe = universe[universe["cohort"] != "ftse"]
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    bonds = yf.download(BONDS, start="2016-01-01", auto_adjust=True, progress=False)["Close"][BONDS]
    rf_month = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")["RF"]

    trading = prices.loc["2017-01-01":].index
    days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)

    # Signal 1: the median company's views this week against its usual week
    article = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    company = cap_spikes(load_daily(columns=list(article))).reindex(columns=article.values)
    this_week, usual = weekly_attention(company, days)
    market_wide = (this_week / usual.where(usual > 0)).median(axis=1)
    # Signal 2: the worry pages' combined views over the same 7 days
    worry_daily = worry_views()
    ends = days - pd.Timedelta(days=PUBLICATION_LAG)
    worry = worry_daily.rolling(7, min_periods=7).sum().reindex(ends).set_axis(days)
    signals = {"market-wide attention": market_wide, "worry pages": worry}

    spy = prices["SPY"].reindex(days)
    ief = bonds.reindex(bonds.index.union(days)).ffill().reindex(days)
    spy_next, ief_next = spy.shift(-1) / spy - 1, ief.shift(-1) / ief - 1  # the week after each decision
    rf_week = pd.Series([(1 + rf_month.get(d.strftime("%Y-%m"), 0.0)) ** (12 / 52) - 1 for d in days], index=days)
    rf_next = rf_week.shift(-1)

    keep = (days >= FIRST_DECISION) & spy_next.notna().to_numpy()
    rows, weekly = [], {"week_of": days[keep], "spy": spy_next[keep].values, "bonds": ief_next[keep].values}
    periods = {"2018-2021": ("2018-03", "2021-12"), "2022-2026": ("2022-01", "2026-12"), "whole": ("2018-03", "2026-12")}
    for name, signal in signals.items():
        for level in LEVELS:
            worried = above_past(signal, level).reindex(days).fillna(False)
            for safe, safe_next in [("bonds", ief_next), ("cash", rf_next)]:
                held = np.where(worried, safe_next, spy_next)
                switches = worried.astype(int).diff().abs().fillna(0)
                net = pd.Series(held, index=days) - COST_PER_SWITCH * switches
                column = f"{name}, {int(level * 100)}th, {safe}"
                weekly[column] = net[keep].values
                for period, (a, b) in periods.items():
                    in_period = keep & (days.strftime("%Y-%m") >= a) & (days.strftime("%Y-%m") <= b)
                    r, base, rf = net[in_period], spy_next[in_period], rf_next[in_period].fillna(0)
                    rows.append({"signal": name, "level": level, "safe_asset": safe, "period": period,
                                 "weeks_worried": float(worried[in_period].mean()),
                                 "switches": int(switches[in_period].sum()),
                                 **measures(r, rf),
                                 **{f"spy_{k}": v for k, v in measures(base, rf).items() if k != "weeks"}})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "risk_off_summary.csv", index=False)
    pd.DataFrame(weekly).to_csv(DATA_DIR / "risk_off_weekly.csv", index=False)
    show = summary.copy()
    for c in ["annual_return", "volatility", "worst_fall", "spy_annual_return", "spy_worst_fall", "weeks_worried"]:
        show[c] = (show[c] * 100).round(1)
    print(show[["signal", "level", "safe_asset", "period", "weeks_worried", "switches", "growth_100",
                "spy_growth_100", "sharpe", "spy_sharpe", "worst_fall", "spy_worst_fall"]]
          .round(2).to_string(index=False))


if __name__ == "__main__":
    main()
