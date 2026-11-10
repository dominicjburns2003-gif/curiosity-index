"""
Curiosity Index - step 30: short selling on fading attention.

Runs the test written down in docs/short_plan.md (committed on 10 Nov 2026
before this was written): each week, short the companies whose page views
have fallen to at most F times their usual week, and buy them back when views
recover (or after 4 weeks). Only companies in the S&P 500 at the time; cash
from the sales earns the T-bill rate; 0.1% trading costs and a 0.5% a year
borrowing fee. Six versions, on 2017-2021 and 2022-2026; plus a labelled
check that shorts the biggest surges (3x).

Writes data/processed/short_summary.csv and short_monthly.csv.

Run it from the project folder:
    python src/short_strategy.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from attention_wave import FIRST_DECISION, MIN_USUAL_WEEK, monthly, t_stat, weekly_attention
from fetch_pageviews import cap_spikes
from pageview_store import load_daily

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

COST_PER_TRADE = 0.001
BORROW_FEE = 0.005   # a year, on the amount shorted
FADES = [2 / 3, 1 / 2, 1 / 3]
EXITS = ["normal", "4 weeks"]
MAIN = (1 / 2, "normal")
PERIODS = {"2017-2021": ("2017-03-01", "2021-12-31"), "2022-2026": (FIRST_DECISION, None)}


def simulate(this_week, usual, prices, member, rf_week, signal: str, level: float, exit_rule: str):
    """Weekly returns of the short position and of shorting the average company."""
    days = this_week.index
    shorts, weights, rows = {}, pd.Series(dtype=float), []
    fee_week = (1 + BORROW_FEE) ** (1 / 52) - 1
    for d, d_next in zip(days[:-1], days[1:]):
        eligible = member.loc[d] & prices.loc[d].reindex(member.columns).notna()
        for ticker in list(shorts):  # 1. close shorts
            info = shorts[ticker]
            now = this_week.at[d, ticker]
            info["weeks"] += 1
            if pd.notna(now):
                info["peak"] = max(info["peak"], now)
            if exit_rule == "normal":
                done = now >= info["usual_at_entry"] if signal == "fade" else now <= info["usual_at_entry"]
            elif exit_rule == "half":
                done = now < 0.5 * info["peak"]
            else:
                done = info["weeks"] >= 4
            if pd.isna(now) or done or not eligible.get(ticker, False):
                del shorts[ticker]
        ratio = this_week.loc[d] / usual.loc[d]  # 2. open new shorts
        hit = (ratio <= level) if signal == "fade" else (ratio >= level)
        for ticker in ratio[hit & (usual.loc[d] >= MIN_USUAL_WEEK) & eligible].index:
            if ticker not in shorts:
                shorts[ticker] = {"usual_at_entry": usual.at[d, ticker], "peak": this_week.at[d, ticker],
                                  "weeks": 0}
        new_weights = pd.Series(1 / len(shorts), index=list(shorts)) if shorts else pd.Series(dtype=float)
        turnover = new_weights.sub(weights, fill_value=0).abs().sum()
        weights = new_weights
        week_returns = prices.loc[d_next] / prices.loc[d] - 1
        rf = rf_week.get(d_next.strftime("%Y-%m"), 0.0)
        if len(weights):
            r = week_returns.reindex(weights.index)
            shorted = (weights * r.fillna(0)).sum() / weights[r.notna()].sum()
            net = -shorted + rf - fee_week - COST_PER_TRADE * turnover
        else:
            net = rf - COST_PER_TRADE * turnover  # nothing shorted: cash earns the T-bill rate
        average = week_returns.reindex(eligible.index)[eligible].mean()
        rows.append({"week_end": d_next, "net": net,
                     "average_company": -average + rf - fee_week,  # shorting the average company
                     "spy": week_returns["SPY"], "n_short": len(shorts)})
    return pd.DataFrame(rows).set_index("week_end")


def main() -> None:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    universe = universe[universe["cohort"] != "ftse"]
    joined = pd.read_csv(MAPPING_DIR / "index_membership.csv").set_index("ticker")["sp500_added"]
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    rf_month = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")["RF"]
    rf_week = ((1 + rf_month) ** (12 / 52) - 1).to_dict()
    article = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    views = cap_spikes(load_daily(columns=list(article))).reindex(columns=article.values).set_axis(article.index, axis=1)
    tickers = [t for t in article.index if t in prices.columns]

    versions = [("fade", f, x, "short the fading") for f in FADES for x in EXITS] + \
               [("surge", 3.0, x, "check: short the biggest surges") for x in ["normal", "half"]]
    rows, monthly_rows = [], []
    for period, (first, last) in PERIODS.items():
        trading = prices.loc[first:last].index
        decision_days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)
        member = pd.DataFrame({t: decision_days >= pd.Timestamp(joined[t]) if t in joined.index
                               else np.zeros(len(decision_days), bool) for t in tickers}, index=decision_days)
        this_week, usual = weekly_attention(views[tickers], decision_days)
        for signal, level, exit_rule, family in versions:
            weekly = simulate(this_week, usual, prices.reindex(decision_days)[tickers + ["SPY"]], member,
                              rf_week, signal, level, exit_rule)
            m = monthly(weekly)
            excess = m["net"] - m["average_company"]
            rows.append({"period": period, "family": family, "signal": signal, "level": round(level, 3),
                         "exit": exit_rule, "main": signal == "fade" and (level, exit_rule) == MAIN,
                         "months": len(m), "excess": excess.mean(), "t_stat": t_stat(excess),
                         "growth_100": 100 * (1 + m["net"]).prod(),
                         "growth_100_short_average": 100 * (1 + m["average_company"]).prod(),
                         "avg_short": weekly["n_short"].mean(), "weeks_empty": (weekly["n_short"] == 0).mean()})
            monthly_rows.append(m.assign(period=period, signal=signal, level=level, exit=exit_rule)
                                .reset_index(names="month"))
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "short_summary.csv", index=False)
    pd.concat(monthly_rows).to_csv(DATA_DIR / "short_monthly.csv", index=False)
    show = summary.assign(excess=summary["excess"] * 100)
    print(show[["period", "family", "level", "exit", "excess", "t_stat", "growth_100",
                "growth_100_short_average", "avg_short", "weeks_empty"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
