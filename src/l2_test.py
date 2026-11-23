"""
Curiosity Index - step 40: does the conclusion depend on the L2 penalty?

As pre-registered in docs/l2_plan.md (committed on 23 Nov 2026 before this
was written): the live strategy as in learning_rate_test.py, changing only
the tree model's L2 penalty (l2_regularization).

Writes data/processed/l2_summary.csv.

Run it from the project folder:
    python src/l2_test.py
"""

from pathlib import Path

import pandas as pd

import walk_forward as wf
from broad_tests import MEMBERSHIP_PATH, group_panel
from learning_rate_test import walk_forward
from replication import as_score, strategy_result

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

L2_VALUES = [0.0, 1.0, 10.0, 100.0, 1000.0, 10000.0]


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"].isin(["original", "expansion", "broad"])].reset_index(drop=True)
    data_panel = group_panel(panel, panel["ticker"].notna())
    data = wf.rank_within_month(data_panel, sorted({f for v in ["company", "products"] for f in wf.VERSIONS[v]}))
    features = wf.VERSIONS["products"]

    added = pd.read_csv(MEMBERSHIP_PATH).set_index("ticker")["sp500_added"]
    joined = data_panel["ticker"].map(added)
    member = (joined.notna() & (joined.str[:7] <= data_panel["month"])).to_numpy()
    members = data_panel[member].reset_index(drop=True)

    rows = []
    for l2 in L2_VALUES:
        settings = {**wf.MODEL_SETTINGS, "l2_regularization": l2}
        score = as_score(walk_forward(data, features, settings), data_panel)[member].reset_index(drop=True)
        result = strategy_result(members, score, "all", f"L2 {l2:g}", n_top=100)
        scored = members.assign(score=score).dropna(subset=["score", "ret_next"])
        ic = scored.groupby("month").apply(
            lambda g: g["score"].corr(g["ret_next"], method="spearman"), include_groups=False)
        spread = scored.groupby("month")["score"].std().mean()
        rows.append({"l2": l2, "excess_per_month": result["result"], "t_stat": result["t_stat"],
                     "months": result["months"], "strategy_100": result["growth_100"],
                     "average_100": result["growth_100_benchmark"], "ic": ic.mean(), "prediction_spread": spread})
        print(f"L2 {l2:<7g} excess {result['result']:+.3%} a month (t {result['t_stat']:.2f}), "
              f"${result['growth_100']:.0f} vs ${result['growth_100_benchmark']:.0f}, IC {ic.mean():+.4f}, "
              f"spread {spread:.4f}", flush=True)
    pd.DataFrame(rows).to_csv(DATA_DIR / "l2_summary.csv", index=False)


if __name__ == "__main__":
    main()
