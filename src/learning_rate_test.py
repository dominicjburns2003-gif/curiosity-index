"""
Curiosity Index - step 39: does the conclusion depend on the learning rate?

As pre-registered in docs/learning_rate_plan.md (committed on 23 Nov 2026
before this was written): the live strategy of broad_tests.py ("members at
the time: top 100") rerun with 9 settings of the tree model, changing only
the learning rate and, in part B, the number of trees. Everything else is as
in broad_tests.py.

Writes data/processed/learning_rate_summary.csv.

Run it from the project folder:
    python src/learning_rate_test.py
"""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import walk_forward as wf
from broad_tests import MEMBERSHIP_PATH, group_panel
from replication import as_score, strategy_result

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

RUNS = [  # (part, learning rate, trees)
    ("A", 0.01, 200), ("A", 0.025, 200), ("A, B", 0.05, 200), ("A", 0.1, 200), ("A", 0.2, 200),
    ("B", 0.01, 1000), ("B", 0.025, 400), ("B", 0.1, 100), ("B", 0.2, 50),
]


def walk_forward(data: pd.DataFrame, features: list[str], settings: dict) -> pd.DataFrame:
    """wf.walk_forward() with the given model settings."""
    predictions = []
    for year in range(wf.FIRST_TEST_YEAR, int(data["month"].max()[:4]) + 1):
        train = data[(data["month"] <= f"{year - 1}-11") & data["rank_next"].notna()]
        test = data[data["month"].str.startswith(str(year))]
        if test.empty:
            continue
        model = HistGradientBoostingRegressor(**settings).fit(train[features], train["rank_next"])
        predictions.append(test[["month", "ticker"]].assign(prediction=model.predict(test[features])))
    return pd.concat(predictions)


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"].isin(["original", "expansion", "broad"])].reset_index(drop=True)
    data_panel = group_panel(panel, panel["ticker"].notna())  # the "all" group of broad_tests.py
    data = wf.rank_within_month(data_panel, sorted({f for v in ["company", "products"] for f in wf.VERSIONS[v]}))
    features = wf.VERSIONS["products"]

    added = pd.read_csv(MEMBERSHIP_PATH).set_index("ticker")["sp500_added"]
    joined = data_panel["ticker"].map(added)
    member = (joined.notna() & (joined.str[:7] <= data_panel["month"])).to_numpy()
    members = data_panel[member].reset_index(drop=True)

    rows = []
    for part, rate, trees in RUNS:
        settings = {**wf.MODEL_SETTINGS, "learning_rate": rate, "max_iter": trees}
        score = as_score(walk_forward(data, features, settings), data_panel)[member].reset_index(drop=True)
        result = strategy_result(members, score, "all", f"lr {rate}, {trees} trees", n_top=100)
        scored = members.assign(score=score).dropna(subset=["score", "ret_next"])
        ic = scored.groupby("month").apply(
            lambda g: g["score"].corr(g["ret_next"], method="spearman"), include_groups=False)
        rows.append({"part": part, "learning_rate": rate, "trees": trees,
                     "excess_per_month": result["result"], "t_stat": result["t_stat"], "months": result["months"],
                     "strategy_100": result["growth_100"], "average_100": result["growth_100_benchmark"],
                     "ic": ic.mean()})
        print(f"{part:5} lr {rate:<6} trees {trees:<5} excess {result['result']:+.3%} a month "
              f"(t {result['t_stat']:.2f}), ${result['growth_100']:.0f} vs ${result['growth_100_benchmark']:.0f}, "
              f"IC {ic.mean():+.4f}", flush=True)
    pd.DataFrame(rows).to_csv(DATA_DIR / "learning_rate_summary.csv", index=False)


if __name__ == "__main__":
    main()
