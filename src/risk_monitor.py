"""
Curiosity Index - step 37: the risk monitor (worry gauge and the live test of
market-wide attention).

1. Worry gauge: keeps the five worry pages' daily views up to date
   (data/processed/worry_pages_daily.csv, only the missing days are
   downloaded) and works out how busy they are this week against their
   average week over the past year, together and page by page. Descriptive
   only: no trading rule (see docs/live_market_attention_plan.md).
2. Live test, as pre-registered in docs/live_market_attention_plan.md
   (committed on 14 Nov 2026 before this was written): each week's
   market-wide attention signal; from the decision on 20 Nov 2026, each
   decision is appended to market_attention_live_log.csv once and never
   changed; then the rule (50% S&P 500 and 50% cash in high weeks, otherwise
   all S&P 500) is followed week by week against holding the S&P 500.

Writes worry_gauge_weekly.csv, worry_gauge_latest.csv,
market_attention_weekly.csv, market_attention_live_log.csv and
market_attention_live_track.csv in data/processed.

Run it from the project folder (the nightly update runs it):
    python src/risk_monitor.py
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
FIRST_LIVE_DECISION = pd.Timestamp("2026-11-20")
HIGH_LEVEL = 0.90
HIGH_WEIGHT = 0.5  # share of the money in the S&P 500 in a high week
COST = 0.001


# ---- 1. Worry gauge ----------------------------------------------------------------------
def update_worry_pages() -> pd.DataFrame:
    """The worry pages' daily views, downloading only the days not yet saved."""
    path = DATA_DIR / "worry_pages_daily.csv"
    saved = pd.read_csv(path, index_col="date", parse_dates=True)
    start, end = saved.index.max().date() + timedelta(days=1), date.today() - timedelta(days=1)
    if start <= end:
        new = {}
        for page in WORRY_PAGES:
            new[page] = daily_views(page, start, end)
            time.sleep(0.1)
        new = pd.DataFrame(new)
        new = new.loc[: new.index[new.sum(axis=1) > 0].max()] if (new.sum(axis=1) > 0).any() else new.iloc[0:0]
        if len(new):
            saved = pd.concat([saved, new])
            saved = saved[~saved.index.duplicated(keep="last")].sort_index()
            saved.index.name = "date"
            saved.to_csv(path)
    return saved


def worry_gauge(pages: pd.DataFrame) -> None:
    capped = cap_spikes(pages)
    week = capped.rolling(7, min_periods=7).sum()
    past_year = week.shift(7).rolling(364, min_periods=364).mean()  # average week over the 52 weeks before
    ratio = (week / past_year)
    combined = week.sum(axis=1, min_count=len(WORRY_PAGES)) / past_year.sum(axis=1, min_count=len(WORRY_PAGES))
    weekly = pd.DataFrame({"worry_vs_usual": combined}).dropna()
    weekly = weekly[weekly.index.day_of_week == weekly.index[-1].day_of_week]  # one reading a week
    weekly["percentile"] = [(weekly["worry_vs_usual"].iloc[:i] < v).mean() if i else np.nan
                            for i, v in enumerate(weekly["worry_vs_usual"])]
    try:
        vix = yf.download("^VIX", start="2017-01-01", auto_adjust=True, progress=False)["Close"]["^VIX"]
        weekly["vix"] = vix.reindex(vix.index.union(weekly.index)).ffill().reindex(weekly.index)
    except Exception as error:  # the gauge does not depend on the VIX
        print(f"  VIX not available ({error})")
        weekly["vix"] = np.nan
    weekly.index.name = "week_ending"
    weekly.to_csv(DATA_DIR / "worry_gauge_weekly.csv")

    last = ratio.dropna().index.max()
    latest = pd.DataFrame({"page": [p.replace("_", " ") for p in WORRY_PAGES],
                           "views_week": week.loc[last, WORRY_PAGES].values,
                           "vs_usual": ratio.loc[last, WORRY_PAGES].values})
    latest["week_ending"] = last.date()
    latest.to_csv(DATA_DIR / "worry_gauge_latest.csv", index=False)
    print(f"Worry gauge: week to {last.date()}, {combined.loc[last]:.2f}x the usual week")


# ---- 2. Live test of market-wide attention -------------------------------------------------
def market_attention(prices: pd.DataFrame) -> pd.DataFrame:
    """Each week's signal (as in risk_signals_test.py) and whether it is high against all earlier weeks."""
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    us = universe[universe["cohort"].isin(["original", "expansion", "broad"])].drop_duplicates("ticker")
    company = cap_spikes(load_daily(columns=list(us["company_article"]))).reindex(columns=us["company_article"].values)
    trading = prices["SPY"].dropna().loc["2017-01-01":].index
    days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)
    # The current week's decision day may still be ahead: add it (Friday) so it is ready on the day
    this_friday = pd.Timestamp(date.today()) + pd.Timedelta(days=(4 - date.today().weekday()) % 7)
    if this_friday.to_period("W-FRI") not in set(days.to_period("W-FRI")):  # not if this week already traded to its end
        days = days.append(pd.DatetimeIndex([this_friday]))
    this_week, usual = weekly_attention(company, days)
    have = this_week.notna().sum(axis=1) >= 0.9 * this_week.shape[1]  # Wikipedia data published for that week
    signal = np.log((this_week / usual.where(usual > 0)).median(axis=1)).where(have)
    weekly = pd.DataFrame({"signal": signal}).dropna()
    threshold = weekly["signal"].shift(1).expanding(min_periods=52).quantile(HIGH_LEVEL)
    weekly["threshold_90th"] = threshold
    weekly["high"] = weekly["signal"] > threshold
    weekly["views_to"] = (weekly.index - pd.Timedelta(days=PUBLICATION_LAG)).date
    weekly.index.name = "decision_day"
    weekly.to_csv(DATA_DIR / "market_attention_weekly.csv")
    return weekly


def record_decisions(weekly: pd.DataFrame) -> pd.DataFrame:
    """Append each new live decision once; rows already recorded are never changed."""
    path = DATA_DIR / "market_attention_live_log.csv"
    log = (pd.read_csv(path, parse_dates=["decision_day"]) if path.exists()
           else pd.DataFrame(columns=["decision_day", "recorded_on", "signal", "threshold_90th", "high", "sp500_weight"]))
    done = set(log["decision_day"])
    new = []
    for day, row in weekly[weekly.index >= FIRST_LIVE_DECISION].iterrows():
        if day in done or pd.isna(row["threshold_90th"]):
            continue
        new.append({"decision_day": day, "recorded_on": date.today(), "signal": row["signal"],
                    "threshold_90th": row["threshold_90th"], "high": bool(row["high"]),
                    "sp500_weight": HIGH_WEIGHT if row["high"] else 1.0})
    if new:
        log = pd.concat([log, pd.DataFrame(new)], ignore_index=True)
        log["decision_day"] = pd.to_datetime(log["decision_day"]).dt.date
        log.to_csv(path, index=False)
        print(f"Live test: recorded {len(new)} new decision(s)")
    return log


def follow_rule(log: pd.DataFrame, prices: pd.DataFrame) -> None:
    """The rule against holding the S&P 500, from the close on each decision day to the next."""
    spy = prices["SPY"].dropna()
    rf_month = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")["RF"]
    rows, before = [], 1.0
    log = log.assign(decision_day=pd.to_datetime(log["decision_day"])).sort_values("decision_day")
    for _, row in log.iterrows():
        start = row["decision_day"]
        later = log.loc[log["decision_day"] > start, "decision_day"]
        end = later.iloc[0] if len(later) else start + pd.Timedelta(days=7)
        if start not in spy.index or end not in spy.index:
            continue  # the week is not over yet
        r_spy = spy[end] / spy[start] - 1
        month = start.strftime("%Y-%m")
        rf_m = rf_month.get(month, rf_month.iloc[-1])  # the latest rate if this month is not published yet
        r_cash = (1 + rf_m) ** (12 / 52) - 1
        w = float(row["sp500_weight"])
        rows.append({"decision_day": start.date(), "week_to": end.date(), "sp500_weight": w,
                     "sp500": r_spy, "rule": w * r_spy + (1 - w) * r_cash - COST * abs(w - before)})
        before = w
    track = pd.DataFrame(rows, columns=["decision_day", "week_to", "sp500_weight", "sp500", "rule"])
    if len(track):
        track["sp500_100"] = 100 * (1 + track["sp500"]).cumprod()
        track["rule_100"] = 100 * (1 + track["rule"]).cumprod()
    track.to_csv(DATA_DIR / "market_attention_live_track.csv", index=False)
    print(f"Live test: {len(track)} completed week(s)")


def main() -> None:
    worry_gauge(update_worry_pages())
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    weekly = market_attention(prices)
    latest = weekly.iloc[-1]
    print(f"Market-wide attention: decision day {weekly.index[-1].date()}, signal {latest['signal']:+.3f}, "
          f"90th percentile {latest['threshold_90th']:+.3f}, {'HIGH' if latest['high'] else 'normal'}")
    follow_rule(record_decisions(weekly), prices)


if __name__ == "__main__":
    main()
