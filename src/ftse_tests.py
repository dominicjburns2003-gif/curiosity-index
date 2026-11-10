"""
Curiosity Index - step 29: the tests on the FTSE 100.

Runs the tests written down in docs/ftse_plan.md (committed on 10 Nov 2026,
before any UK data was downloaded), every setting unchanged from the S&P 500
tests, on the 95 UK companies ranked among themselves:

  1. strategy     version A trained on the UK companies, top third, equal
                  amounts and by size, against their own average (flattered:
                  today's FTSE 100 members are used back to 2017)
  2. long-short   company only, + products
  3. sorts        company and product attention signals
  4. earnings     product attention before results and the beat rate

Writes data/processed/ftse_summary.csv and ftse_monthly.csv.

Run it from the project folder:
    python src/ftse_tests.py
"""

from pathlib import Path

import pandas as pd

import replication
import walk_forward as wf
from backtest import SIGNALS, sort_on
from earnings_test import build_events, clustered_regression, top_minus_bottom
from replication import as_score, strategy_result, t_stat

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
UK_BENCHMARK = "CUKX.L"


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    uk = panel[panel["cohort"] == "ftse"].copy()
    uk["rank_next"] = uk.groupby("month")["ret_next"].rank(pct=True)
    uk = uk.reset_index(drop=True)
    uk_universe = universe[universe["cohort"] == "ftse"]
    with_products = set(uk_universe.loc[uk_universe["product_article"] != "", "ticker"])
    print(f"{uk['ticker'].nunique()} UK companies, {len(with_products)} with product pages")

    rows, name = [], "ftse"
    features = wf.VERSIONS["products"]
    data = wf.rank_within_month(uk, sorted({f for v in ["company", "products"] for f in wf.VERSIONS[v]}))
    score = as_score(wf.walk_forward(data, features), uk)
    for detail, by_size in [("equal amounts (today's members)", False), ("by size (today's members)", True)]:
        rows.append({"group": name, "test": "strategy", "detail": detail,
                     **strategy_result(uk, score, name, detail, by_size=by_size)})
    for version in ["company", "products"]:
        result = wf.portfolio(wf.walk_forward(data, wf.VERSIONS[version]), data)
        rows.append({"group": name, "test": "long-short", "detail": version,
                     "result": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
                     "months": len(result)})
    for signal, label in SIGNALS.items():
        if "conversion" in signal:
            continue
        groups = sort_on(uk, signal, "ret_next")
        if groups.empty or 3 not in groups:
            continue
        diff = groups[3] - groups[1]
        rows.append({"group": name, "test": "sort", "detail": label,
                     "result": diff.mean(), "t_stat": t_stat(diff), "months": len(diff)})
    events, left_out = build_events(uk_universe)
    print(f"Earnings: {len(events)} announcements; left out (too few): {len(left_out)} companies")
    for outcome in ["beat", "reaction"]:
        sort = top_minus_bottom(events, "product_surge", outcome)
        rows.append({"group": name, "test": "earnings", "detail": f"{outcome}: top minus bottom third",
                     "result": sort["top_minus_bottom"], "t_stat": sort["t_stat"], "months": sort["quarters"],
                     "events": sort["events"], "bottom": sort["bottom"], "middle": sort["middle"],
                     "top": sort["top"]})

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "ftse_summary.csv", index=False)
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    monthly = pd.concat(replication.MONTHLY)
    monthly["ftse_fund"] = monthly["month"].map(returns[UK_BENCHMARK].shift(-1))
    monthly.to_csv(DATA_DIR / "ftse_monthly.csv", index=False)
    show = summary.copy()
    pct = show["test"].isin(["strategy", "long-short", "sort"]) | show["detail"].str.startswith("reaction")
    show.loc[pct, "result"] *= 100
    print(show[["test", "detail", "result", "t_stat", "months"]].round(3).to_string(index=False))
    for detail in monthly["detail"].unique():
        m = monthly[monthly["detail"] == detail]
        print(f"{detail}: $100 -> {100 * (1 + m['net']).prod():.0f}; own average "
              f"{100 * (1 + m['benchmark']).prod():.0f}; FTSE 100 fund {100 * (1 + m['ftse_fund']).prod():.0f}")


if __name__ == "__main__":
    main()
