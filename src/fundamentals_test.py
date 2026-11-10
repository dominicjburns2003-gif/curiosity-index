"""
Curiosity Index - step 32c: does attention add anything to fundamentals?

Runs the test written down in docs/fundamentals_plan.md (committed on
10 Nov 2026 before the accounts were downloaded): three tree models trained
walk-forward on all US companies (F: fundamentals + stock measures; A: the
live attention model; F + A: both), each buying its top 100 among the
companies in the S&P 500 at the time, after costs, from January 2022.

Writes data/processed/fundamentals_summary.csv and fundamentals_monthly_returns.csv.

Run it from the project folder:
    python src/fundamentals_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import walk_forward as wf
from replication import as_score
from strategy import portfolio

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

FUNDAMENTALS = ["earnings_yield", "book_to_market", "gross_profitability", "asset_growth"]
STOCK = ["momentum", "log_mcap", "vol"]
MODELS = {
    "F": FUNDAMENTALS + STOCK,
    "A": wf.VERSIONS["products"],
    "F + A": FUNDAMENTALS + wf.VERSIONS["products"],
}


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"] != "ftse"]
    fundamentals = pd.read_csv(DATA_DIR / "fundamentals_monthly.csv")
    panel = panel.merge(fundamentals[["month", "ticker", *FUNDAMENTALS]], on=["month", "ticker"], how="left")
    panel = panel.reset_index(drop=True)
    panel["rank_next"] = panel.groupby("month")["ret_next"].rank(pct=True)  # across all US companies
    assert all(c in set(wf.VERSIONS["products"]) for c in STOCK)

    joined = pd.read_csv(MAPPING_DIR / "index_membership.csv").set_index("ticker")["sp500_added"]
    added = panel["ticker"].map(joined)
    member = (added.notna() & (added.str[:7] <= panel["month"])).to_numpy()

    data = wf.rank_within_month(panel, sorted({f for fs in MODELS.values() for f in fs}))
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    spy_next = returns["SPY"].shift(-1)
    nets, rows = {}, []
    for name, features in MODELS.items():
        score = as_score(wf.walk_forward(data, features), panel)
        result = portfolio(panel[member].reset_index(drop=True), score[member].reset_index(drop=True),
                           use_filter=False, hold=1, n_top=100)
        nets[name] = result["net"]
        excess = result["net"] - result["benchmark"]
        vs_spy = result["net"] - spy_next.reindex(result.index)
        rows.append({"model": name, "features": len(features), "months": len(result),
                     "excess": excess.mean(), "t_stat": t_stat(excess),
                     "excess_vs_spy": vs_spy.mean(), "t_vs_spy": t_stat(vs_spy),
                     "growth_100": 100 * (1 + result["net"]).prod(),
                     "growth_100_average": 100 * (1 + result["benchmark"]).prod(),
                     "growth_100_spy": 100 * (1 + spy_next.reindex(result.index)).prod()})
        if name == "F":
            average = result["benchmark"]
    diff = nets["F + A"] - nets["F"]
    rows.append({"model": "F + A minus F (does attention add?)", "months": len(diff),
                 "excess": diff.mean(), "t_stat": t_stat(diff)})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "fundamentals_summary.csv", index=False)
    pd.DataFrame({**nets, "average_company": average, "spy": spy_next.reindex(average.index)}).rename_axis(
        "month").to_csv(DATA_DIR / "fundamentals_monthly_returns.csv")
    show = summary.copy()
    show[["excess", "excess_vs_spy"]] *= 100
    print(show.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
