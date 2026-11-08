"""
Curiosity Index - step 20: replication on companies the tests have never seen.

Runs the tests written down in docs/expansion_replication_plan.md (committed on
8 Nov 2026, before any of the new companies' results were computed), with
every setting copied unchanged from the original tests:

  1. strategy     version A, trained walk-forward on the group itself, top third
                  in equal amounts, vs the group's own average, after costs
  2. transfer     the same, scored by the model trained on the original 68
  3. long-short   company only / + products / + click-through
  4. sorts        the six single signals, whole history
  5. earnings     product attention before results and the beat rate

for three groups: the 44 new companies, the new ones without defence, and all
112 together.

Writes data/processed/replication_summary.csv.

Run it from the project folder:
    python src/replication.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import walk_forward as wf
from backtest import SIGNALS, sort_on
from earnings_test import build_events, clustered_regression, top_minus_bottom
from strategy import portfolio

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def strategy_result(panel: pd.DataFrame, score: pd.Series) -> dict:
    """Version A's long-only portfolio on `score`, against the group's own average."""
    result = portfolio(panel, score, use_filter=False, hold=1)
    excess = result["net"] - result["benchmark"]
    return {"result": excess.mean(), "t_stat": t_stat(excess), "months": len(result),
            "growth_100": 100 * (1 + result["net"]).prod(),
            "growth_100_benchmark": 100 * (1 + result["benchmark"]).prod()}


def as_score(predictions: pd.DataFrame, panel: pd.DataFrame) -> pd.Series:
    """Predictions lined up with the panel's rows."""
    lookup = predictions.set_index(["month", "ticker"])["prediction"]
    return pd.Series(lookup.reindex(pd.MultiIndex.from_frame(panel[["month", "ticker"]])).values,
                     index=panel.index)


def transfer_predictions(train_data: pd.DataFrame, test_data: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """walk_forward(), but trained on one group of companies and used on another."""
    predictions = []
    last_year = int(test_data["month"].max()[:4])
    for year in range(wf.FIRST_TEST_YEAR, last_year + 1):
        train = train_data[(train_data["month"] <= f"{year - 1}-11") & train_data["rank_next"].notna()]
        test = test_data[test_data["month"].str.startswith(str(year))]
        if test.empty:
            continue
        model = HistGradientBoostingRegressor(**wf.MODEL_SETTINGS)
        model.fit(train[features], train["rank_next"])
        predictions.append(test[["month", "ticker"]].assign(prediction=model.predict(test[features])))
    return pd.concat(predictions)


def run_group(name: str, panel: pd.DataFrame, universe: pd.DataFrame, original: pd.DataFrame) -> list[dict]:
    rows = []
    features = wf.VERSIONS["products"]
    all_features = sorted({f for fs in wf.VERSIONS.values() for f in fs})
    data = wf.rank_within_month(panel, all_features)

    # 1. Strategy, trained on the group itself
    rows.append({"group": name, "test": "strategy", "detail": "trained on this group",
                 **strategy_result(panel, as_score(wf.walk_forward(data, features), panel))})

    # 2. Transfer: scored by the model trained on the original 68
    if name != "all 112":
        trained_on = wf.rank_within_month(original, all_features)
        rows.append({"group": name, "test": "strategy", "detail": "model from the original 68",
                     **strategy_result(panel, as_score(transfer_predictions(trained_on, data, features), panel))})

    # 3. Long-short research comparison
    for version, version_features in wf.VERSIONS.items():
        result = wf.portfolio(wf.walk_forward(data, version_features), data)
        rows.append({"group": name, "test": "long-short", "detail": version,
                     "result": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
                     "months": len(result)})

    # 4. Single-signal sorts, whole history
    for signal, label in SIGNALS.items():
        groups = sort_on(panel, signal, "ret_next")
        diff = groups[3] - groups[1]
        rows.append({"group": name, "test": "sort", "detail": label,
                     "result": diff.mean(), "t_stat": t_stat(diff), "months": len(diff)})

    # 5. Earnings: product attention before results and the beat rate
    events, _ = build_events(universe)
    for outcome in ["beat", "reaction"]:
        sort = top_minus_bottom(events, "product_surge", outcome)
        rows.append({"group": name, "test": "earnings", "detail": f"{outcome}: top minus bottom third",
                     "result": sort["top_minus_bottom"], "t_stat": sort["t_stat"], "months": sort["quarters"],
                     "events": sort["events"], "bottom": sort["bottom"], "top": sort["top"]})
    regression = clustered_regression(events, "beat", ["product_surge", "company_surge"])
    product = next(r for r in regression if r["variable"] == "product_surge")
    rows.append({"group": name, "test": "earnings", "detail": "beat: regression on product surge",
                 "result": product["coefficient"], "t_stat": product["t_stat"], "events": product["events"]})
    return rows


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    universe["consumer"] = universe["consumer"].astype(str) == "True"
    original = panel[panel["cohort"] == "original"]

    groups = {
        "new 44": (panel["cohort"] == "expansion", universe["cohort"] == "expansion"),
        "new, consumer only": ((panel["cohort"] == "expansion") & panel["consumer"],
                               (universe["cohort"] == "expansion") & universe["consumer"]),
        "all 112": (panel["ticker"].notna(), universe["ticker"].notna()),
    }
    rows = []
    for name, (in_panel, in_universe) in groups.items():
        print(f"Running: {name} ({panel.loc[in_panel, 'ticker'].nunique()} companies)", flush=True)
        group_panel = panel[in_panel].copy()
        if name == "all 112":
            # Targets are ranked within each cohort in the panel; rank across all 112 here
            group_panel["rank_next"] = group_panel.groupby("month")["ret_next"].rank(pct=True)
        rows += run_group(name, group_panel.reset_index(drop=True), universe[in_universe], original)

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "replication_summary.csv", index=False)
    show = summary.copy()
    pct = show["test"].isin(["strategy", "long-short", "sort"]) | show["detail"].str.startswith("reaction")
    show.loc[pct, "result"] *= 100
    print(show[["group", "test", "detail", "result", "t_stat", "months"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
