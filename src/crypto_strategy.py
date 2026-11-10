"""
Curiosity Index - step 36: a crypto strategy from Wikipedia attention.

Runs the strategy written down in docs/crypto_strategy_plan.md (committed on
10 Nov 2026 before this was written): each Sunday, a coin's signal is "on"
when its page is busier than its usual week; each signal holds the coin for
4 weeks (four overlapping parts), equal money per coin, cash (T-bills) for the
rest, 0.25% cost per change in holding. Compared with holding the coins, the
same rules on a 4-week price trend, and Bitcoin alone.

Uses data/processed/crypto_weekly.csv from src/crypto_test.py (same attention
and past-return definitions). Writes crypto_strategy_summary.csv and
crypto_strategy_weekly.csv.

Run it from the project folder:
    python src/crypto_strategy.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from risk_off import measures

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
HOLD_WEEKS = 4
COST = 0.0025


def run(signal: pd.DataFrame, returns: pd.DataFrame, rf: pd.Series) -> pd.Series:
    """Weekly net return: each coin's holding is the share of its last 4 signals that were on."""
    available = signal.notna()
    on = signal.fillna(0).astype(float)
    share_on = on.rolling(HOLD_WEEKS, min_periods=1).mean().where(available, 0.0)
    weight = share_on.div(available.sum(axis=1), axis=0)  # equal money per coin available
    gross = (weight * returns.fillna(0)).sum(axis=1) + (1 - weight.sum(axis=1)) * rf
    trading = weight.diff().abs().sum(axis=1).fillna(weight.iloc[0].abs().sum())
    return gross - COST * trading, weight.sum(axis=1)


def main() -> None:
    weekly = pd.read_csv(DATA_DIR / "crypto_weekly.csv", parse_dates=["week"])
    attention = weekly.pivot(index="week", columns="coin", values="attention")
    trend = weekly.pivot(index="week", columns="coin", values="past_4w")
    returns = np.exp(weekly.pivot(index="week", columns="coin", values="next_1w")) - 1  # Sunday to next Sunday
    keep = returns.notna().any(axis=1)
    attention, trend, returns = attention[keep], trend[keep], returns[keep]
    weeks = returns.index

    rf_month = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")["RF"]
    months = weeks.strftime("%Y-%m")
    # The latest months may not be published yet: the last published rate carries on
    rf_m = rf_month.reindex(sorted(set(rf_month.index) | set(months))).ffill().reindex(months).to_numpy()
    rf = pd.Series((1 + rf_m) ** (12 / 52) - 1, index=weeks)

    strategies, time_in = {}, {}
    strategies["Attention strategy"], time_in["Attention strategy"] = run(
        (attention > 0).where(attention.notna()), returns, rf)
    strategies["Price-trend strategy (check)"], time_in["Price-trend strategy (check)"] = run(
        (trend > 0).where(trend.notna()), returns, rf)
    strategies["Holding the coins"] = returns.mean(axis=1)
    time_in["Holding the coins"] = pd.Series(1.0, index=weeks)
    btc = ["BTC-USD"]
    strategies["Bitcoin: attention strategy"], time_in["Bitcoin: attention strategy"] = run(
        (attention[btc] > 0).where(attention[btc].notna()), returns[btc], rf)
    strategies["Bitcoin: holding"] = returns["BTC-USD"]
    time_in["Bitcoin: holding"] = pd.Series(1.0, index=weeks)

    periods = {"whole": weeks, "2017-2021": weeks[weeks < "2022"], "2022-2026": weeks[weeks >= "2022"]}
    rows = []
    for name, r in strategies.items():
        for period, idx in periods.items():
            rows.append({"strategy": name, "period": period, "first_week": idx.min().date(),
                         "time_in_coins": float(time_in[name][idx].mean()), **measures(r[idx], rf[idx])})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "crypto_strategy_summary.csv", index=False)
    out = pd.DataFrame(strategies)
    out.index.name = "week"
    out.to_csv(DATA_DIR / "crypto_strategy_weekly.csv")

    show = summary.copy()
    for c in ["time_in_coins", "annual_return", "volatility", "worst_fall"]:
        show[c] = (show[c] * 100).round(1)
    print(f"{len(weeks)} weeks, {weeks.min().date()} to {weeks.max().date()}")
    print(show.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
