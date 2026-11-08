"""
Curiosity Index - step 18: two final click-through tests.

Runs the tests written down in docs/clickthrough_tests_plan.md (committed on
6 Nov 2026, before running):

  1. Volatility: does the size of a change in click-through predict next
     month's volatility, beyond this month's volatility, size and the size of
     the changes in company and product attention? Monthly cross-sectional
     regressions, slopes averaged over months (Fama-MacBeth).
  2. Level: do companies with high click-through do worse next month? Thirds
     by click-through, top minus bottom; the same against the sector median;
     and the first version split into two halves (to 2021, and 2022 onwards).

Company-months with more than half of the product views' clicks hidden
(censored_share above 0.5) are left out.

Writes data/processed/clickthrough_tests_summary.csv.

Run it from the project folder:
    python src/clickthrough_tests.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from strategy import SECTOR_GROUPS

MAX_CENSORED = 0.5

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def fama_macbeth(df: pd.DataFrame, outcome: str, signal: str, controls: list[str]) -> dict:
    """Average monthly slope on `signal` (all variables standardised within the month)."""
    slopes = []
    for _, month in df.dropna(subset=[outcome, signal, *controls]).groupby("month"):
        if len(month) < 20:
            continue
        X = month[[signal, *controls]]
        X = (X - X.mean()) / X.std()
        X = np.column_stack([np.ones(len(X)), X.fillna(0).to_numpy()])
        coef, *_ = np.linalg.lstsq(X, month[outcome].to_numpy(), rcond=None)
        slopes.append(coef[1])
    slopes = pd.Series(slopes)
    return {"test": "volatility", "signal": signal, "months": len(slopes),
            "result": slopes.mean(), "t_stat": t_stat(slopes)}


def top_minus_bottom(df: pd.DataFrame, signal: str, outcome: str, label: str) -> dict:
    """Thirds by `signal` within each month; top-third minus bottom-third `outcome`."""
    data = df.dropna(subset=[signal, outcome])
    data = data.assign(third=data.groupby("month")[signal].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)))
    by_month = data.groupby(["month", "third"])[outcome].mean().unstack()
    diff = by_month[2] - by_month[0]
    return {"test": "level", "signal": label, "months": len(diff),
            "bottom": by_month[0].mean(), "top": by_month[2].mean(),
            "result": diff.mean(), "t_stat": t_stat(diff)}


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"] == "original"]  # the pre-registered tests use the original 68 companies
    sectors = pd.read_csv(UNIVERSE_PATH).drop_duplicates("ticker").set_index("ticker")["sector"]
    df = panel[panel["conversion"].notna() & (panel["censored_share"] <= MAX_CENSORED)].copy()
    df["sector_group"] = df["ticker"].map(sectors).map(SECTOR_GROUPS)

    # Test 1: volatility (sizes of changes, since volatility has no direction)
    df["abs_conversion_change"] = df["conversion_change"].abs()
    df["abs_conversion_vs_normal"] = df["conversion_vs_normal"].abs()
    df["abs_company_growth"] = df["company_growth"].abs()
    df["abs_product_growth"] = df["product_growth"].abs()
    controls = ["vol", "log_mcap", "abs_company_growth", "abs_product_growth"]
    rows = [fama_macbeth(df, "vol_next", signal, controls)
            for signal in ["abs_conversion_change", "abs_conversion_vs_normal"]]

    # Test 2: level of click-through and next month's return vs the market
    df["conversion_vs_sector"] = df["conversion"] - df.groupby(["month", "sector_group"])["conversion"].transform("median")
    rows.append(top_minus_bottom(df, "conversion", "ret_vs_mkt_next", "conversion"))
    rows.append(top_minus_bottom(df, "conversion_vs_sector", "ret_vs_mkt_next", "conversion vs sector"))
    rows.append(top_minus_bottom(df[df["month"] <= "2021-12"], "conversion", "ret_vs_mkt_next", "conversion, to 2021"))
    rows.append(top_minus_bottom(df[df["month"] >= "2022-01"], "conversion", "ret_vs_mkt_next", "conversion, 2022 on"))

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "clickthrough_tests_summary.csv", index=False)
    print(f"{len(df):,} company-months with usable click-through "
          f"({(panel['conversion'].notna() & (panel['censored_share'] > MAX_CENSORED)).sum()} left out as mostly hidden)")
    show = summary.copy()
    level = show["test"] == "level"
    show.loc[level, ["bottom", "top", "result"]] *= 100
    print("Volatility: average standardised slope (annualised volatility per 1 std of the signal).")
    print("Level: next-month return vs market, % a month.")
    print(show.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
