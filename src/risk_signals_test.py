"""
Curiosity Index - step 34: does public worry predict the market, beyond the
VIX and trend?

Runs the test written down in docs/risk_signals_plan.md (committed on
10 Nov 2026 before this was written): weekly regressions of the S&P 500's
next-4-week excess return and volatility on the worry signal and on
market-wide attention, alone and together with the VIX and the 200-day trend,
with Newey-West standard errors (4 lags).

Writes data/processed/risk_signals_summary.csv and risk_signals_weekly.csv.

Run it from the project folder (after src/risk_off.py, which saves the worry
pages' daily views):
    python src/risk_signals_test.py
    python src/risk_signals_test.py --extended   # every series back to July 2015
"""

from datetime import date, timedelta
from pathlib import Path
import sys
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
FIRST_WEEK = "2018-03-01"
HORIZON = 4  # weeks
LAGS = 4


def newey_west(y: np.ndarray, X: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    """OLS coefficients and Newey-West t-statistics."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n = len(y)
    xu = X * resid[:, None]
    S = xu.T @ xu
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        g = xu[lag:].T @ xu[:-lag]
        S += w * (g + g.T)
    xtx_inv = np.linalg.inv(X.T @ X)
    cov = xtx_inv @ S @ xtx_inv * n / (n - X.shape[1])
    return beta, beta / np.sqrt(np.diag(cov))


EXTENDED_START = date(2015, 7, 1)  # the first day of Wikimedia's page-view service


def extended_views(titles_by_page: dict[str, list[str]], path: Path) -> pd.DataFrame:
    """Daily views from July 2015 to the end of 2016 (the store starts in 2017), saved once."""
    if path.exists():
        return pd.read_csv(path, index_col="date", parse_dates=True)
    out = {}
    for i, (page, titles) in enumerate(titles_by_page.items(), start=1):
        parts = []
        for title in titles:
            parts.append(daily_views(title, EXTENDED_START, date(2016, 12, 31)))
            time.sleep(0.1)
        out[page] = sum(parts)
        if i % 100 == 0:
            print(f"  {i}/{len(titles_by_page)} pages", flush=True)
    frame = pd.DataFrame(out)
    frame.index.name = "date"
    frame.to_csv(path)
    return frame


def main() -> None:
    extended = "--extended" in sys.argv
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    spy = prices["SPY"].dropna()
    vix = yf.download("^VIX", start="2014-01-01", auto_adjust=True, progress=False)["Close"]["^VIX"]
    rf_month = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")["RF"]
    first_day = "2017-01-01"
    if extended:
        # Yahoo's SPY from 2014, so the 200-day average exists from 2015; joined to our series
        early = yf.download("SPY", start="2014-01-01", end="2016-01-01", auto_adjust=True, progress=False)["Close"]["SPY"]
        early = early * spy.iloc[0] / yf.download("SPY", start=str(spy.index[0].date()),
                                                   end=str((spy.index[0] + pd.Timedelta(days=5)).date()),
                                                   auto_adjust=True, progress=False)["Close"]["SPY"].iloc[0]
        spy = pd.concat([early[early.index < spy.index[0]], spy])
        first_day = str(EXTENDED_START)

    trading = spy.loc[first_day:].index
    days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)
    ends = days - pd.Timedelta(days=PUBLICATION_LAG)

    # Worry: the worry pages' views that week against their average week over the previous 52
    worry_raw = pd.read_csv(DATA_DIR / "worry_pages_daily.csv", index_col="date", parse_dates=True)
    if extended:
        early_worry = extended_views({p: [p] for p in worry_raw.columns}, DATA_DIR / "worry_pages_daily_2015.csv")
        worry_raw = pd.concat([early_worry[early_worry.index < worry_raw.index[0]], worry_raw])
    worry_daily = cap_spikes(worry_raw).sum(axis=1)
    week = worry_daily.rolling(7, min_periods=7).sum()
    past_year = week.shift(7).rolling(364, min_periods=364).mean()  # average week over the 52 weeks before
    worry = np.log(week / past_year).reindex(ends).set_axis(days)

    # Market-wide attention: the median company's views against its usual week
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    us = universe[universe["cohort"].isin(["original", "expansion", "broad"])].drop_duplicates("ticker")
    article = us["company_article"]
    stored = load_daily(columns=list(article))
    if extended:
        titles = {r.company_article: r.company_titles.split("|") for r in us.itertuples()}
        early_company = extended_views(titles, DATA_DIR / "company_pages_daily_2015.csv")
        stored = pd.concat([early_company[early_company.index < stored.index[0]], stored])
    company = cap_spikes(stored).reindex(columns=article.values)
    this_week, usual = weekly_attention(company, days)
    market_wide = np.log((this_week / usual.where(usual > 0)).median(axis=1))

    # Fear gauges, known at each decision day's close
    vix_week = np.log(vix.reindex(vix.index.union(days)).ffill().reindex(days))
    trend = (spy / spy.rolling(200).mean() - 1).reindex(days)

    # Outcomes over the next 4 weeks
    position = {d: i for i, d in enumerate(spy.index)}
    ret, vol = [], []
    for i, d in enumerate(days):
        if i + HORIZON >= len(days):
            ret.append(np.nan); vol.append(np.nan); continue
        end = days[i + HORIZON]
        r = spy[end] / spy[d] - 1
        rf = sum(rf_month.get(x.strftime("%Y-%m"), 0.0) for x in days[i + 1: i + HORIZON + 1]) / 52 * 12
        ret.append(r - rf)
        daily = spy.iloc[position[d]: position[end] + 1].pct_change().dropna()
        vol.append(np.log(daily.std() * np.sqrt(252)))
    data = pd.DataFrame({"worry": worry, "market_wide": market_wide, "vix": vix_week, "trend": trend,
                         "ret_next4": ret, "logvol_next4": vol}, index=days)
    data = data.loc["2016-07-01" if extended else FIRST_WEEK:].dropna()
    data.index.name = "week"
    suffix = "_extended" if extended else ""
    data.to_csv(DATA_DIR / f"risk_signals_weekly{suffix}.csv")

    signals = ["worry", "market_wide", "vix", "trend"]
    z = (data[signals] - data[signals].mean()) / data[signals].std()
    rows = []
    periods = {"2018-2026": data.index, "2018-2021": data.index[data.index < "2022"],
               "2022-2026": data.index[data.index >= "2022"]}
    if extended:
        periods = {"Jul 2016-2026": data.index, "new weeks only (Jul 2016-Feb 2018)": data.index[data.index < FIRST_WEEK],
                   "2018-2021": data.index[(data.index >= FIRST_WEEK) & (data.index < "2022")],
                   "2022-2026": data.index[data.index >= "2022"]}
    for outcome in ["ret_next4", "logvol_next4"]:
        for period, idx in periods.items():
            y = data.loc[idx, outcome].to_numpy()
            specs = {s: [s] for s in signals}
            specs["worry + VIX + trend"] = ["worry", "vix", "trend"]
            specs["market-wide + VIX + trend"] = ["market_wide", "vix", "trend"]
            for spec, columns in specs.items():
                X = np.column_stack([np.ones(len(idx)), z.loc[idx, columns].to_numpy()])
                beta, t = newey_west(y, X, LAGS)
                for name, b, tv in zip(columns, beta[1:], t[1:]):
                    rows.append({"outcome": outcome, "period": period, "model": spec, "signal": name,
                                 "coefficient": b, "t_stat": tv, "weeks": len(idx)})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / f"risk_signals_summary{suffix}.csv", index=False)
    show = summary.copy()
    show.loc[show["outcome"] == "ret_next4", "coefficient"] *= 100  # % over 4 weeks per standard deviation
    print(f"{len(data)} weeks, {data.index.min().date()} to {data.index.max().date()}")
    print(show.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
