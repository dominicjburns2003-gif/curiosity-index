"""
Curiosity Index - step 32b: the four fundamental measures, month by month.

From the annual figures in fundamentals_annual.csv (fetch_fundamentals.py),
at each month end and for each company, using only the latest annual report
filed by then (docs/fundamentals_plan.md):

  earnings_yield        net income / market value
  book_to_market        shareholders' equity / market value
  gross_profitability   gross profit (or revenue minus cost of revenue) / assets
  asset_growth          assets / assets a year earlier - 1

Writes data/processed/fundamentals_monthly.csv.

Run it from the project folder:
    python src/fundamentals.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main() -> None:
    annual = pd.read_csv(DATA_DIR / "fundamentals_annual.csv", parse_dates=["period_end", "filed"])
    mcap = pd.read_csv(DATA_DIR / "market_cap_monthly.csv")
    months = sorted(mcap["month"].unique())

    # One row per company and financial year end: every item, and when it was first known
    wide = annual.pivot_table(index=["ticker", "period_end"], columns="item", values="value", aggfunc="first")
    filed = annual.pivot_table(index=["ticker", "period_end"], columns="item", values="filed", aggfunc="first")
    wide["gross"] = wide.get("gross_profit").combine_first(wide.get("revenue") - wide.get("cost_of_revenue"))
    # A year counts once its net income and assets are both published
    wide["known_from"] = filed[["net_income", "assets"]].max(axis=1)
    wide = wide.reset_index().sort_values(["ticker", "period_end"])
    # Assets a year earlier: the previous financial year end, 11 to 13 months before
    wide["assets_before"] = wide.groupby("ticker")["assets"].shift(1)
    gap = (wide["period_end"] - wide.groupby("ticker")["period_end"].shift(1)).dt.days
    wide.loc[~gap.between(330, 400), "assets_before"] = np.nan
    wide = wide.dropna(subset=["known_from"])

    rows = []
    for month in months:
        month_end = pd.Period(month).end_time.normalize()
        known = wide[wide["known_from"] <= month_end]
        latest = known.sort_values("period_end").groupby("ticker").tail(1)
        latest = latest[(month_end - latest["period_end"]).dt.days <= 550]  # no accounts older than ~18 months
        rows.append(latest.assign(month=month))
    panel = pd.concat(rows).merge(mcap[["month", "ticker", "mcap"]], on=["month", "ticker"], how="inner")
    out = pd.DataFrame({
        "month": panel["month"], "ticker": panel["ticker"],
        "earnings_yield": panel["net_income"] / panel["mcap"],
        "book_to_market": panel["equity"] / panel["mcap"],
        "gross_profitability": panel["gross"] / panel["assets"],
        "asset_growth": panel["assets"] / panel["assets_before"] - 1,
        "accounts_for": panel["period_end"].dt.date,
    })
    out.to_csv(DATA_DIR / "fundamentals_monthly.csv", index=False)
    latest_month = out[out["month"] == out["month"].max()]
    print(f"Saved {len(out):,} company-months, {out['month'].min()} to {out['month'].max()}; "
          f"latest month: {len(latest_month)} companies")
    print(latest_month[["earnings_yield", "book_to_market", "gross_profitability", "asset_growth"]]
          .describe().round(3).to_string())


if __name__ == "__main__":
    main()
