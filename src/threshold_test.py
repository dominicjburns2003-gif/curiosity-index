"""
Curiosity Index - step 21: a minimum level of product interest.

Runs the test written down in docs/strategy_plan.md ("Addendum: a minimum
level of product interest", committed on 9 Nov 2026 before running): version
A's top third on all 112 companies, keeping only picks whose product views are
at least 20% above their 6-month average; with fewer than 5 such picks, the
month is held in the S&P 500 (SPY) instead.

Writes data/processed/threshold_monthly.csv and threshold_summary.csv.

Run it from the project folder:
    python src/threshold_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import walk_forward as wf
from replication import as_score, t_stat
from strategy import COST_PER_TRADE, portfolio

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

MIN_GROWTH = np.log(1.2)  # product views at least 20% above their 6-month average
MIN_PICKS = 5             # fewer qualifying picks: hold the S&P 500 that month


def threshold_portfolio(panel: pd.DataFrame, score: pd.Series, spy_next: pd.Series) -> pd.DataFrame:
    data = panel.assign(score=score)
    data = data[data["month"] >= f"{wf.FIRST_TEST_YEAR}-01"]
    weights, rows = pd.Series(dtype=float), []
    for month in sorted(data["month"].unique()):
        now = data[data["month"] == month]
        candidates = now.dropna(subset=["score"])
        top = candidates.nlargest(round(len(candidates) * 1 / 3), "score")
        keep = top[top["product_growth"] >= MIN_GROWTH]["ticker"]
        returns = now.set_index("ticker")["ret_next"].copy()
        if returns.isna().all():
            break  # next month's returns are not known yet
        returns["SPY"] = spy_next.get(month, np.nan)
        new_weights = (pd.Series(1 / len(keep), index=keep.values) if len(keep) >= MIN_PICKS
                       else pd.Series({"SPY": 1.0}))
        turnover = new_weights.sub(weights, fill_value=0).abs().sum()
        weights = new_weights
        held = returns.reindex(weights.index)
        rows.append({"month": month, "gross": (weights * held.fillna(0)).sum() / weights[held.notna()].sum(),
                     "cost": COST_PER_TRADE * turnover, "n_held": len(keep) if len(keep) >= MIN_PICKS else 0,
                     "in_spy": len(keep) < MIN_PICKS, "picks": " ".join(sorted(weights.index))})
    out = pd.DataFrame(rows).set_index("month")
    out["net"] = out["gross"] - out["cost"]
    return out


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel["rank_next"] = panel.groupby("month")["ret_next"].rank(pct=True)  # across all 112
    features = wf.VERSIONS["products"]
    score = as_score(wf.walk_forward(wf.rank_within_month(panel, features), features), panel)

    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    spy_next = returns["SPY"].shift(-1)

    base = portfolio(panel, score, use_filter=False, hold=1)
    new = threshold_portfolio(panel, score, spy_next)
    months = new.index.intersection(base.index)
    monthly = pd.DataFrame({"threshold": new.loc[months, "net"], "version_a": base.loc[months, "net"],
                            "average_company": base.loc[months, "average_company"],
                            "spy": spy_next.reindex(months), "n_held": new.loc[months, "n_held"],
                            "in_spy": new.loc[months, "in_spy"], "picks": new.loc[months, "picks"]})
    monthly.to_csv(DATA_DIR / "threshold_monthly.csv")

    rows = []
    for name in ["threshold", "version_a"]:
        for against in ["version_a", "average_company", "spy"]:
            if name == against:
                continue
            diff = monthly[name] - monthly[against]
            rows.append({"strategy": name, "against": against, "difference": diff.mean(), "t_stat": t_stat(diff)})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "threshold_summary.csv", index=False)

    print(f"Months: {len(monthly)} ({monthly.index[0]} picks to {monthly.index[-1]} picks)")
    print(f"Months held in the S&P 500: {int(monthly['in_spy'].sum())}; "
          f"average companies held otherwise: {monthly.loc[~monthly['in_spy'], 'n_held'].mean():.1f}")
    for column in ["threshold", "version_a", "average_company", "spy"]:
        print(f"$100 -> {column}: ${100 * (1 + monthly[column]).prod():.0f}")
    show = summary.assign(difference=summary["difference"] * 100).round(2)
    print(show.to_string(index=False))


if __name__ == "__main__":
    main()
