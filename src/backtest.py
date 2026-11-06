"""
Curiosity Index - step 11: portfolio sorts (CLAUDE.md section 7.3, tests 1-2).

For each attention signal, every month t:
  1. split the companies into 3 equal groups on the signal (low, mid, high);
  2. hold each group, equally weighted, during month t+1;
  3. long-short = high group minus low group.

Then, over all months:
  - average next-month return of each group, and of long-short;
  - t-statistic of the long-short average: about 2 or more (in absolute
    value) means the difference is unlikely to be luck;
  - hit rate: share of months the long-short made money;
  - alpha: what is left of the long-short return after the Fama-French
    5 factors and momentum explain what they can (regression), with its t-stat;
  - the same sort on next-month volatility, in case attention predicts how
    much a stock moves rather than which way.

This is a first look on the full sample: nothing is fitted or tuned, so there
is nothing to over-fit. The out-of-sample model comes later (tests 3-5).

Writes to data/processed/:
  sorts_summary.csv   - one row per signal
  sorts_monthly.csv   - each group's return in each month, per signal

Run it from the project folder:
    python src/backtest.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

GROUPS = 3  # not 5: with about 68 companies, 5 groups would hold only 13 each
SIGNALS = {
    "company_abn": "Abnormal company attention",
    "company_growth": "Company attention growth",
    "product_growth": "Product attention growth",
    "gap": "Gap (products vs company)",
}
FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"


def t_stat(x: pd.Series) -> float:
    """Average divided by its standard error."""
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def alpha(long_short: pd.Series, factors: pd.DataFrame) -> tuple[float, float]:
    """Monthly alpha and its t-stat from regressing long-short on the factors."""
    data = pd.concat([long_short.rename("y"), factors[FACTORS]], axis=1, join="inner").dropna()
    X = np.column_stack([np.ones(len(data)), data[FACTORS].to_numpy()])
    y = data["y"].to_numpy()
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    sigma2 = resid @ resid / (len(y) - X.shape[1])
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X.T @ X)))
    return coef[0], coef[0] / se[0]


def sort_on(panel: pd.DataFrame, signal: str, target: str) -> pd.DataFrame:
    """Average target of each group, month by month (months x groups)."""
    data = panel.dropna(subset=[signal, target]).copy()
    # Rank within the month, then cut into equal groups: 1 = low, GROUPS = high
    data["group"] = data.groupby("month")[signal].transform(
        lambda s: pd.qcut(s.rank(method="first"), GROUPS, labels=False) + 1
    )
    return data.groupby(["month", "group"])[target].mean().unstack()


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    factors = pd.read_csv(DATA_DIR / "ff_factors_monthly.csv", index_col="month")
    # The factors are for month t+1, because returns are measured over t+1
    factors_next = factors.copy()
    factors_next.index = (pd.PeriodIndex(factors.index, freq="M") - 1).astype(str)

    summary, monthly = [], []
    for signal, label in SIGNALS.items():
        groups = sort_on(panel, signal, "ret_next")
        long_short = groups[GROUPS] - groups[1]
        a, a_t = alpha(long_short, factors_next)
        vol = sort_on(panel, signal, "vol_next")
        summary.append({
            "signal": signal, "label": label,
            "first_month": groups.index.min(), "months": len(groups),
            **{f"ret_g{g}": groups[g].mean() for g in range(1, GROUPS + 1)},
            "long_short": long_short.mean(), "t_stat": t_stat(long_short),
            "hit_rate": (long_short > 0).mean(),
            "alpha": a, "alpha_t": a_t,
            **{f"vol_g{g}": vol[g].mean() for g in range(1, GROUPS + 1)},
            "vol_spread_t": t_stat(vol[GROUPS] - vol[1]),
        })
        groups.columns = [f"g{g}" for g in groups.columns]
        monthly.append(groups.assign(long_short=long_short, signal=signal).reset_index())

    summary = pd.DataFrame(summary)
    summary.to_csv(DATA_DIR / "sorts_summary.csv", index=False)
    pd.concat(monthly).to_csv(DATA_DIR / "sorts_monthly.csv", index=False)

    show = summary.set_index("label")
    pct = ["ret_g1", "ret_g2", "ret_g3", "long_short", "alpha"]
    show[pct] = show[pct] * 100  # monthly returns in %
    print("Next-month returns by group (% per month), long-short = high - low:")
    print(show[pct + ["t_stat", "alpha_t", "hit_rate"]].round(2).to_string())
    print("\nNext-month volatility by group (annualised):")
    print(show[["vol_g1", "vol_g2", "vol_g3", "vol_spread_t"]].round(3).to_string())


if __name__ == "__main__":
    main()
