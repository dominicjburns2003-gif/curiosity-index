"""
Curiosity Index - step 38: what the live model's trees look like (descriptive only).

The live strategy's gradient-boosted tree model (walk_forward.py settings, the
"products" features, all US companies the site follows) is retrained here on
the data its 2026 predictions were trained on (months to November 2025), and
described, for the pitch and the write-up:

  - the first of its 200 trees: every split and, for each leaf, how many
    company-months fall in it and their average next-month return rank
    (0 = worst, 1 = best that month);
  - feature importance as each feature's share of the total split gain over
    all 200 trees (how much each feature reduced the training error).

Nothing here is a test and nothing is tuned: the settings are the fixed ones
in walk_forward.py.

Writes data/processed/tree_first_tree.csv and data/processed/tree_importance.csv.

Run it from the project folder:
    python src/tree_explainer.py
"""

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from walk_forward import MODEL_SETTINGS, VERSIONS, rank_within_month

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
TRAIN_TO = "2025-11"  # the training data behind the 2026 predictions


def leaf_of(row: np.ndarray, nodes: np.ndarray) -> int:
    i = 0
    while not nodes[i]["is_leaf"]:
        value = row[nodes[i]["feature_idx"]]
        left = nodes[i]["missing_go_to_left"] if np.isnan(value) else value <= nodes[i]["num_threshold"]
        i = nodes[i]["left"] if left else nodes[i]["right"]
    return i


def main() -> None:
    everyone = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    mapping = pd.read_csv(PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv")
    tracked = set(mapping.loc[mapping["cohort"].isin(["original", "expansion", "broad"]), "ticker"])
    everyone = everyone[everyone["ticker"].isin(tracked)].reset_index(drop=True)
    everyone["rank_next"] = everyone.groupby("month")["ret_next"].rank(pct=True)
    features = VERSIONS["products"]
    data = rank_within_month(everyone, features)
    train = data[(data["month"] <= TRAIN_TO) & data["rank_next"].notna()]
    model = HistGradientBoostingRegressor(**MODEL_SETTINGS).fit(train[features], train["rank_next"])

    nodes = model._predictors[0][0].nodes  # the first tree
    leaves = pd.Series([leaf_of(r, nodes) for r in train[features].to_numpy()], index=train.index)
    rows = []
    for i, n in enumerate(nodes):
        in_node = train["rank_next"][leaves == i] if n["is_leaf"] else None
        rows.append({
            "node": i, "depth": int(n["depth"]), "is_leaf": bool(n["is_leaf"]),
            "feature": None if n["is_leaf"] else features[n["feature_idx"]],
            "threshold": None if n["is_leaf"] else round(float(n["num_threshold"]), 3),
            "missing_goes_left": None if n["is_leaf"] else bool(n["missing_go_to_left"]),
            "left": None if n["is_leaf"] else int(n["left"]), "right": None if n["is_leaf"] else int(n["right"]),
            "company_months": int(n["count"]),
            "avg_next_month_rank": round(float(in_node.mean()), 4) if in_node is not None else None,
        })
    pd.DataFrame(rows).to_csv(DATA_DIR / "tree_first_tree.csv", index=False)

    gain = defaultdict(float)
    for tree in model._predictors:
        for n in tree[0].nodes:
            if not n["is_leaf"]:
                gain[features[n["feature_idx"]]] += float(n["gain"])
    total = sum(gain.values())
    importance = pd.DataFrame({"feature": list(gain), "gain_share": [g / total for g in gain.values()]})
    importance = importance.sort_values("gain_share", ascending=False)
    importance.to_csv(DATA_DIR / "tree_importance.csv", index=False)

    print(f"Trained on {len(train):,} company-months, {train['month'].min()} to {train['month'].max()}")
    print(pd.DataFrame(rows).to_string(index=False))
    print(importance.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
