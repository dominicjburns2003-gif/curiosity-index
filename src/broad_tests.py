"""
Curiosity Index - step 23: the tests on the broad universe.

Runs the tests written down in docs/broad_universe_plan.md (committed on
9 Nov 2026 before any of them were run), with every setting copied unchanged
from the earlier tests, for three groups:

  broad new                  the 435 companies added on 9 Nov 2026
  broad new, with products   those of them with at least one product page
  all                        all 547 companies

  1. strategy     version A trained on the group, top third, equal amounts and
                  by size, against the group's own average, after costs
  2. long-short   company only, + products (and + click-through, part 2)
  3. sorts        the six single signals
  4. earnings     product attention before results and the beat rate
  5. click-through, part 2: version A with the click-through features against
                  version A, long-only, on all companies with product pages

Part 1 (tonight) runs everything except the click-through versions; part 2
(python src/broad_tests.py --clickthrough) runs those once the full
clickstream history for the new companies has been downloaded.

Writes data/processed/broad_summary.csv (part 1), broad_clickthrough.csv
(part 2) and broad_monthly.csv (the strategy's monthly returns, for the app).

Run it from the project folder:
    python src/broad_tests.py
    python src/broad_tests.py --clickthrough
"""

from pathlib import Path
import sys

import pandas as pd

import replication
import walk_forward as wf
from backtest import SIGNALS, sort_on
from earnings_test import build_events, clustered_regression, top_minus_bottom
from replication import as_score, strategy_result, t_stat
from strategy import portfolio

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def groups(panel: pd.DataFrame, universe: pd.DataFrame) -> dict:
    with_products = set(universe.loc[universe["product_article"] != "", "ticker"])
    broad = panel["cohort"] == "broad"
    return {
        "broad new": (broad, universe["cohort"] == "broad"),
        "broad new, with products": (broad & panel["ticker"].isin(with_products),
                                     (universe["cohort"] == "broad") & universe["ticker"].isin(with_products)),
        "all": (panel["ticker"].notna(), universe["ticker"].notna()),
    }


def group_panel(panel: pd.DataFrame, rows: pd.Series) -> pd.DataFrame:
    """The group's rows, with next month's return ranked within the group."""
    out = panel[rows].copy()
    out["rank_next"] = out.groupby("month")["ret_next"].rank(pct=True)
    return out.reset_index(drop=True)


def part_one(panel: pd.DataFrame, universe: pd.DataFrame) -> None:
    rows = []
    features = wf.VERSIONS["products"]
    for name, (in_panel, in_universe) in groups(panel, universe).items():
        data_panel = group_panel(panel, in_panel)
        print(f"Running: {name} ({data_panel['ticker'].nunique()} companies)", flush=True)
        data = wf.rank_within_month(data_panel, sorted({f for v in ["company", "products"] for f in wf.VERSIONS[v]}))

        # 1. Strategy, equal amounts and by size
        score = as_score(wf.walk_forward(data, features), data_panel)
        rows.append({"group": name, "test": "strategy", "detail": "equal amounts",
                     **strategy_result(data_panel, score, name, "equal amounts")})
        rows.append({"group": name, "test": "strategy", "detail": "by size",
                     **strategy_result(data_panel, score, name, "by size", by_size=True)})

        # 2. Long-short: company only and + products
        for version in ["company", "products"]:
            result = wf.portfolio(wf.walk_forward(data, wf.VERSIONS[version]), data)
            rows.append({"group": name, "test": "long-short", "detail": version,
                         "result": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
                         "months": len(result)})

        # 3. Single-signal sorts, whole history (click-through sorts wait for part 2)
        for signal, label in SIGNALS.items():
            if "conversion" in signal:
                continue
            by_group = sort_on(data_panel, signal, "ret_next")
            if by_group.empty:
                continue
            diff = by_group[3] - by_group[1]
            rows.append({"group": name, "test": "sort", "detail": label,
                         "result": diff.mean(), "t_stat": t_stat(diff), "months": len(diff)})

        # 4. Earnings: product attention before results and the beat rate
        events, _ = build_events(universe[in_universe])
        for outcome in ["beat", "reaction"]:
            sort = top_minus_bottom(events, "product_surge", outcome)
            rows.append({"group": name, "test": "earnings", "detail": f"{outcome}: top minus bottom third",
                         "result": sort["top_minus_bottom"], "t_stat": sort["t_stat"], "months": sort["quarters"],
                         "events": sort["events"], "bottom": sort["bottom"], "middle": sort["middle"],
                         "top": sort["top"]})
        regression = clustered_regression(events, "beat", ["product_surge", "company_surge"])
        product = next(r for r in regression if r["variable"] == "product_surge")
        rows.append({"group": name, "test": "earnings", "detail": "beat: regression on product surge",
                     "result": product["coefficient"], "t_stat": product["t_stat"], "events": product["events"]})

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "broad_summary.csv", index=False)
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    monthly = pd.concat(replication.MONTHLY)
    monthly["spy"] = monthly["month"].map(returns["SPY"].shift(-1))
    monthly.to_csv(DATA_DIR / "broad_monthly.csv", index=False)
    show = summary.copy()
    pct = show["test"].isin(["strategy", "long-short", "sort"]) | show["detail"].str.startswith("reaction")
    show.loc[pct, "result"] *= 100
    print(show[["group", "test", "detail", "result", "t_stat", "months"]].round(3).to_string(index=False))


def part_two(panel: pd.DataFrame, universe: pd.DataFrame) -> None:
    rows = []
    for name, (in_panel, _) in groups(panel, universe).items():
        data_panel = group_panel(panel, in_panel)
        all_features = sorted({f for fs in wf.VERSIONS.values() for f in fs})
        data = wf.rank_within_month(data_panel, all_features)
        # 2. Long-short with click-through
        result = wf.portfolio(wf.walk_forward(data, wf.VERSIONS["clicks"]), data)
        rows.append({"group": name, "test": "long-short", "detail": "clicks",
                     "result": result["long_short"].mean(), "t_stat": t_stat(result["long_short"]),
                     "months": len(result)})
        # 3. The click-through sorts
        for signal, label in SIGNALS.items():
            if "conversion" in signal:
                by_group = sort_on(data_panel, signal, "ret_next")
                diff = by_group[3] - by_group[1]
                rows.append({"group": name, "test": "sort", "detail": label,
                             "result": diff.mean(), "t_stat": t_stat(diff), "months": len(diff)})

    # 5. Long-only: version A with click-through against version A, all companies with product pages
    with_products = set(universe.loc[universe["product_article"] != "", "ticker"])
    data_panel = group_panel(panel, panel["ticker"].isin(with_products))
    data = wf.rank_within_month(data_panel, sorted({f for fs in wf.VERSIONS.values() for f in fs}))
    nets = {}
    for version in ["products", "clicks"]:
        score = as_score(wf.walk_forward(data, wf.VERSIONS[version]), data_panel)
        nets[version] = portfolio(data_panel, score, use_filter=False, hold=1)["net"]
    diff = (nets["clicks"] - nets["products"]).dropna()
    rows.append({"group": "all, with products", "test": "click-through added (long-only)",
                 "detail": "A + click-through minus A", "result": diff.mean(), "t_stat": t_stat(diff),
                 "months": len(diff), "growth_100": 100 * (1 + nets["clicks"]).prod(),
                 "growth_100_benchmark": 100 * (1 + nets["products"]).prod()})
    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "broad_clickthrough.csv", index=False)
    show = out.assign(result=out["result"] * 100)
    print(show[["group", "test", "detail", "result", "t_stat", "months"]].round(3).to_string(index=False))


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    if "--clickthrough" in sys.argv:
        part_two(panel, universe)
    else:
        part_one(panel, universe)


if __name__ == "__main__":
    main()
