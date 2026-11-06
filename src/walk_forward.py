"""
Curiosity Index - step 12: the out-of-sample model (CLAUDE.md section 7.3, tests 3-5).

A gradient-boosted tree model predicts each company's next-month return rank
from its features. It is tested "walk-forward": train on the past only,
predict the next year, then add that year to the training data and repeat:

    train 2017-2021 -> predict 2022
    train 2017-2022 -> predict 2023   ... and so on

Three versions are compared. The difference between them is the project's answer:
    1. company   - company attention + controls (momentum, size, volatility)
    2. products  - version 1 + product attention and the gap
    3. clicks    - version 2 + click-through (needs the full clickstream)

Each month, the companies are split into 3 groups on the model's prediction:
long the top group, short the bottom one, equally weighted, as in backtest.py.
Results are reported before and after trading costs.

Settings fixed BEFORE looking at any result, and never tuned on the test
years: the tree settings below, 3 groups, cost of 0.1% per trade.

Writes to data/processed/:
  walk_forward_predictions.csv  - every out-of-sample prediction
  walk_forward_monthly.csv      - monthly portfolio returns per version
  walk_forward_summary.csv      - one row per version

Run it from the project folder:
    python src/walk_forward.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

FIRST_TEST_YEAR = 2022
GROUPS = 3
COST_PER_TRADE = 0.001  # 0.1% of the amount traded

CONTROLS = ["momentum", "log_mcap", "vol"]
VERSIONS = {
    "company": ["company_abn", "company_growth"] + CONTROLS,
    "products": ["company_abn", "company_growth", "product_growth", "gap"] + CONTROLS,
    "clicks": ["company_abn", "company_growth", "product_growth", "gap",
               "conversion", "conversion_change", "conversion_vs_normal", "censored_share"] + CONTROLS,
}

# Small, slow-learning trees: with about 5,000 training rows and a weak signal,
# a big model would mostly learn noise
MODEL_SETTINGS = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=100,
                      l2_regularization=1.0, early_stopping=False, random_state=0)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"


def rank_within_month(panel: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Replace each feature by its rank among the companies that month (0 to 1).
    The model then compares companies with each other, and one extreme value
    (e.g. Boeing's attention in Jan 2024) cannot dominate."""
    ranked = panel.groupby("month")[columns].rank(pct=True)
    return panel[["month", "ticker", "rank_next", "ret_next", "ret_vs_mkt_next"]].join(ranked)


def walk_forward(data: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Out-of-sample predictions, retraining once a year on the past only."""
    predictions = []
    last_year = int(data["month"].max()[:4])
    for year in range(FIRST_TEST_YEAR, last_year + 1):
        # Trained at the end of the previous year: a row's target is the next
        # month's return, so rows up to November are the last ones fully known
        train = data[(data["month"] <= f"{year - 1}-11") & data["rank_next"].notna()]
        test = data[data["month"].str.startswith(str(year))]
        if test.empty:
            continue
        model = HistGradientBoostingRegressor(**MODEL_SETTINGS)
        model.fit(train[features], train["rank_next"])
        predictions.append(test[["month", "ticker"]].assign(prediction=model.predict(test[features])))
    return pd.concat(predictions)


def portfolio(predictions: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    """Monthly long-short returns from the predictions, before and after costs."""
    df = predictions.merge(data[["month", "ticker", "ret_next", "ret_vs_mkt_next"]], on=["month", "ticker"])
    df = df.dropna(subset=["ret_next"])
    df["group"] = df.groupby("month")["prediction"].transform(
        lambda s: pd.qcut(s.rank(method="first"), GROUPS, labels=False) + 1)
    long_names = df[df["group"] == GROUPS].groupby("month")["ticker"].apply(set)
    short_names = df[df["group"] == 1].groupby("month")["ticker"].apply(set)

    def turnover(names: pd.Series) -> pd.Series:
        # Share of the group replaced since last month (the first month: all of it)
        previous = names.shift(1)
        return pd.Series([1.0 if not isinstance(p, set) else 1 - len(n & p) / len(n)
                          for n, p in zip(names, previous)], index=names.index)

    out = pd.DataFrame({
        "long": df[df["group"] == GROUPS].groupby("month")["ret_next"].mean(),
        "short": df[df["group"] == 1].groupby("month")["ret_next"].mean(),
        "long_vs_mkt": df[df["group"] == GROUPS].groupby("month")["ret_vs_mkt_next"].mean(),
        # Each name replaced means one sale and one purchase, in each leg
        "cost": 2 * COST_PER_TRADE * (turnover(long_names) + turnover(short_names)),
        "ic": df.groupby("month").apply(
            lambda g: g["prediction"].rank().corr(g["ret_next"].rank()), include_groups=False),
    })
    out["long_short"] = out["long"] - out["short"]
    out["long_short_net"] = out["long_short"] - out["cost"]
    return out


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    all_features = sorted({f for features in VERSIONS.values() for f in features})
    present = [f for f in all_features if f in panel.columns]
    data = rank_within_month(panel, present)

    summary, monthly, preds = [], [], []
    for version, features in VERSIONS.items():
        missing = [f for f in features if f not in panel.columns or panel[f].notna().sum() == 0]
        if missing:
            print(f"{version}: skipped, no data yet for {', '.join(missing)}")
            continue
        p = walk_forward(data, features)
        result = portfolio(p, data)
        preds.append(p.assign(version=version))
        monthly.append(result.assign(version=version).reset_index())
        summary.append({
            "version": version, "features": len(features),
            "first_month": result.index.min(), "last_month": result.index.max(), "months": len(result),
            "ic": result["ic"].mean(), "ic_t": t_stat(result["ic"]),
            "long_short": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
            "long_short_net": result["long_short_net"].mean(), "t_stat_net": t_stat(result["long_short_net"]),
            "hit_rate": (result["long_short"] > 0).mean(),
            "sharpe_net": result["long_short_net"].mean() / result["long_short_net"].std() * np.sqrt(12),
            "long_vs_mkt": result["long_vs_mkt"].mean(), "long_vs_mkt_t": t_stat(result["long_vs_mkt"]),
            "avg_cost": result["cost"].mean(),
        })

    summary = pd.DataFrame(summary)
    summary.to_csv(DATA_DIR / "walk_forward_summary.csv", index=False)
    pd.concat(monthly).to_csv(DATA_DIR / "walk_forward_monthly.csv", index=False)
    pd.concat(preds).to_csv(DATA_DIR / "walk_forward_predictions.csv", index=False)

    show = summary.set_index("version")
    pct = ["long_short", "long_short_net", "long_vs_mkt", "avg_cost"]
    show[pct] = show[pct] * 100
    print(f"Out of sample, {show['first_month'].iloc[0]} to {show['last_month'].iloc[0]} "
          f"({show['months'].iloc[0]} months); returns in % per month:")
    print(show[["ic", "ic_t", "long_short", "t_stat", "long_short_net", "t_stat_net",
                "hit_rate", "sharpe_net", "long_vs_mkt", "long_vs_mkt_t", "avg_cost"]].round(3).to_string())


if __name__ == "__main__":
    main()
