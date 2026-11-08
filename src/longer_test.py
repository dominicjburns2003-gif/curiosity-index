"""
Curiosity Index - step 16: the same tests over a longer stretch, from 2020.

Runs the check written down in docs/strategy_plan.md (addendum, committed on
6 Nov 2026 before running): the same models and settings as walk_forward.py
and strategy.py, but with the first test year moved from 2022 to 2020, so
about 81 test months instead of 57. The main results keep starting in 2022;
this only shows whether they hold over a longer period.

Writes data/processed/longer_test_summary.csv.

Run it from the project folder:
    python src/longer_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import walk_forward as wf
from strategy import portfolio

FIRST_YEAR = 2020

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"] == "original"]  # the pre-registered tests use the original 68 companies
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    spy_next = returns["SPY"].shift(-1)  # on the row of month t: SPY's return in t+1
    all_features = sorted({f for features in wf.VERSIONS.values() for f in features})
    data = wf.rank_within_month(panel, all_features)

    rows = []
    # 1. The chosen strategy (A), long-only, equal amounts and by size
    predictions = wf.walk_forward(data, wf.VERSIONS["products"], first_year=FIRST_YEAR)
    score = pd.Series(predictions.set_index(["month", "ticker"])["prediction"]
                      .reindex(pd.MultiIndex.from_frame(panel[["month", "ticker"]])).values, index=panel.index)
    for label, by_size in [("A, equal amounts (vs 68 equal)", False), ("A, by size (vs 68 by size)", True)]:
        result = portfolio(panel, score, use_filter=False, hold=1, by_size=by_size, first_year=FIRST_YEAR)
        spy = spy_next.reindex(result.index)
        excess = result["net"] - result["benchmark"]
        rows.append({
            "test": "long-only", "version": label, "first_month": result.index.min(),
            "last_month": result.index.max(), "months": len(result),
            "result": excess.mean(), "t_stat": t_stat(excess),
            "vs_spy": (result["net"] - spy).mean(), "vs_spy_t": t_stat(result["net"] - spy),
            "growth_100": 100 * (1 + result["net"]).prod(),
            "growth_100_benchmark": 100 * (1 + result["benchmark"]).prod(),
            "growth_100_spy": 100 * (1 + spy).prod(),
        })

    # 2. The three long-short research versions
    for version, features in wf.VERSIONS.items():
        result = wf.portfolio(wf.walk_forward(data, features, first_year=FIRST_YEAR), data)
        rows.append({
            "test": "long-short", "version": version, "first_month": result.index.min(),
            "last_month": result.index.max(), "months": len(result),
            "result": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
        })

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "longer_test_summary.csv", index=False)
    show = summary.copy()
    show[["result", "vs_spy"]] = show[["result", "vs_spy"]] * 100
    print(f"From {FIRST_YEAR} (% a month; long-only: above its benchmark after costs):")
    print(show.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
