"""
Curiosity Index - step 13: the improved, long-only strategy.

Runs the versions fixed in advance in docs/strategy_plan.md (written and
committed on 6 Nov 2026, before any of this was run):

  A. Baseline          tree model (products version), top third, 1-month hold
  B. Simple score      gap + rising click-through, bad-news filter, 3-month hold
  C. Simple, sectors   as B, each signal measured against its sector
  D. Tree, improved    tree model on sector-relative features and this month's
                       return, bad-news filter, 3-month hold
  plus two checks on B: without the filter, and with a 1-month hold.
  And (addenda in the plan) A weighted by company size instead of equally,
  compared with the 68 companies weighted the same way; and robustness checks
  on A: held 3 months, top quarter instead of top third, and both.

Long-only: buy the top third each month, equally weighted. Compared with the
equal-weighted average of all 68 companies and with the S&P 500 (SPY), after
trading costs of 0.1% of every amount traded.

The version with the highest return above the 68-company average after costs
over the development period (Jan 2022 - Dec 2024) is chosen, then reported on
the final period (Jan 2025 onwards). Nothing is tuned on either period.

Also keeps a live record: each month's picks from the chosen version are added
to live_picks_log.csv as soon as they can be made, before the returns are
known, and are never changed afterwards.

Writes to data/processed/:
  strategy_summary.csv    one row per version and period
  strategy_monthly.csv    monthly returns per version, with the benchmarks
  strategy_picks.csv      the chosen version's picks, every month
  live_picks_log.csv      the live record (only ever added to)

Run it from the project folder:
    python src/strategy.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from walk_forward import FIRST_TEST_YEAR, VERSIONS, rank_within_month, walk_forward

DEV_END = "2024-12"  # development period: Jan 2022 to Dec 2024; final: after
# From the picks chosen at the end of November 2026, the live strategy uses all
# 112 companies (docs/strategy_plan.md, written on 9 Nov 2026); earlier months'
# picks, and every backtest, use the original 68
LIVE_ALL_FROM = "2026-11"
COST_PER_TRADE = 0.001
MAX_WEIGHT = 0.15  # size-weighted version: no company above 15%

# 5 broad sectors, so that comparing with sector peers means something
SECTOR_GROUPS = {
    "Pharma": "Health", "Medtech": "Health",
    "Beverages": "Consumer staples", "Household": "Consumer staples",
    "Food": "Consumer staples", "Tobacco": "Consumer staples",
    "Apparel": "Consumer discretionary", "Restaurants": "Consumer discretionary",
    "Toys": "Consumer discretionary", "Retail": "Consumer discretionary",
    "Travel": "Consumer discretionary", "Media": "Consumer discretionary",
    "Tech software": "Technology", "Tech hardware": "Technology",
    "Semiconductors": "Technology", "Fintech": "Technology", "Games": "Technology",
    "Autos": "Autos & aerospace", "Aerospace": "Autos & aerospace",
}
ATTENTION = ["company_abn", "company_growth", "product_growth", "gap",
             "conversion", "conversion_change", "conversion_vs_normal"]

VERSION_NAMES = {
    "A": "A. Baseline: tree model, monthly",
    "B": "B. Simple score, filter, 3-month hold",
    "C": "C. Simple score vs sector, filter, 3-month hold",
    "D": "D. Tree model vs sector, filter, 3-month hold",
    "B_no_filter": "Check: B without the bad-news filter",
    "B_1m": "Check: B held for 1 month",
    "A_size": "A weighted by company size (vs 68 weighted by size)",
    "A_3m": "Robustness: A held for 3 months",
    "A_quarter": "Robustness: A, top quarter only",
    "A_quarter_3m": "Robustness: A, top quarter, held 3 months",
}
CANDIDATES = ["A", "B", "C", "D"]  # the checks are shown but never chosen

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def month_rank(df: pd.DataFrame, column: str) -> pd.Series:
    return df.groupby("month")[column].rank(pct=True)


def vs_sector(df: pd.DataFrame, column: str) -> pd.Series:
    """The signal minus its sector's median that month."""
    return df[column] - df.groupby(["month", "sector_group"])[column].transform("median")


def simple_score(df: pd.DataFrame, sector_relative: bool) -> pd.Series:
    """Average monthly rank of 'products ahead of company' and 'rising click-through'."""
    ranks = pd.DataFrame(index=df.index)
    for column in ["gap", "conversion_change"]:
        values = df.assign(x=vs_sector(df, column) if sector_relative else df[column])
        ranks[column] = month_rank(values, "x")
    return ranks.mean(axis=1, skipna=True)  # gap alone where click-through is missing


def size_weights(market_caps: pd.Series) -> pd.Series:
    """Weights in proportion to market cap, with none above MAX_WEIGHT: the
    excess is shared out among the others in proportion to their size."""
    weights = market_caps / market_caps.sum()
    capped = pd.Series(False, index=weights.index)
    while (weights > MAX_WEIGHT + 1e-12).any():
        capped |= weights > MAX_WEIGHT
        free = weights[~capped]
        weights[capped] = MAX_WEIGHT
        weights[~capped] = free / free.sum() * (1 - MAX_WEIGHT * capped.sum())
    return weights


def portfolio(df: pd.DataFrame, score: pd.Series, use_filter: bool, hold: int,
              by_size: bool = False, share: float = 1 / 3,
              first_year: int = FIRST_TEST_YEAR) -> pd.DataFrame:
    """Monthly returns of buying the top `share` (a third) on `score`, held
    `hold` months, in equal amounts or (by_size) in proportion to market cap."""
    data = df.assign(score=score)
    data = data[data["month"] >= f"{first_year}-01"]
    months = sorted(data["month"].unique())
    cohorts, weights, rows = [], pd.Series(dtype=float), []
    for month in months:
        now = data[data["month"] == month]
        candidates = now.dropna(subset=["score"])
        n_pick = round(len(candidates) * share)
        if use_filter:
            # Bad news: the share price is in the bottom third of the 68 this month
            falling = now["ret_now"] <= now["ret_now"].quantile(1 / 3)
            candidates = candidates[~falling.reindex(candidates.index, fill_value=False)]
        picks = candidates.nlargest(n_pick, "score")["ticker"]
        caps = np.exp(now.set_index("ticker")["log_mcap"])
        cohort = (size_weights(caps.reindex(picks.values)) if by_size
                  else pd.Series(1 / len(picks), index=picks.values))
        cohorts = (cohorts + [cohort])[-hold:]
        new_weights = pd.concat(cohorts, axis=1).fillna(0).sum(axis=1) / len(cohorts)
        turnover = new_weights.sub(weights, fill_value=0).abs().sum()
        weights = new_weights
        returns = now.set_index("ticker")["ret_next"]
        held = returns.reindex(weights.index)
        if held.isna().all():
            break  # next month's returns are not known yet
        known = returns.dropna().index.intersection(caps.dropna().index)
        size_average = (size_weights(caps[known]) * returns[known]).sum()
        rows.append({
            "month": month,
            "gross": (weights * held.fillna(0)).sum() / weights[held.notna()].sum(),
            "cost": COST_PER_TRADE * turnover,
            "average_company": returns.mean(),
            "size_average": size_average,
            "picks": " ".join(sorted(picks)),
        })
    out = pd.DataFrame(rows).set_index("month")
    # What the strategy is judged against: the 68 companies weighted the same way
    out["benchmark"] = out["size_average"] if by_size else out["average_company"]
    out["net"] = out["gross"] - out["cost"]
    return out


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def summarise(result: pd.DataFrame, spy: pd.Series, period: str) -> dict:
    r = result.loc[:DEV_END] if period == "development" else result.loc[f"{int(DEV_END[:4]) + 1}-01":]
    excess = r["net"] - r["benchmark"]
    excess_spy = r["net"] - spy.reindex(r.index)
    return {
        "period": period, "first_month": r.index.min(), "last_month": r.index.max(), "months": len(r),
        "return_net": r["net"].mean(), "benchmark": r["benchmark"].mean(),
        "excess": excess.mean(), "excess_t": t_stat(excess), "beat_average_share": (excess > 0).mean(),
        "excess_vs_spy": excess_spy.mean(), "excess_vs_spy_t": t_stat(excess_spy),
        "avg_cost": r["cost"].mean(),
        "growth_100": 100 * (1 + r["net"]).prod(),
        "growth_100_benchmark": 100 * (1 + r["benchmark"]).prod(),
        "growth_100_spy": 100 * (1 + spy.reindex(r.index)).prod(),
    }


def main() -> None:
    panel = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    panel = panel[panel["cohort"] == "original"]  # the pre-registered tests use the original 68 companies
    sectors = pd.read_csv(UNIVERSE_PATH).drop_duplicates("ticker").set_index("ticker")["sector"]
    returns = pd.read_csv(DATA_DIR / "returns_monthly.csv").pivot(index="month", columns="ticker", values="ret")
    spy_next = returns["SPY"].shift(-1)  # on the row of month t: SPY's return in t+1

    df = panel.copy()
    df["sector_group"] = df["ticker"].map(sectors).map(SECTOR_GROUPS)
    df["ret_now"] = returns.stack().rename("r").reindex(pd.MultiIndex.from_frame(df[["month", "ticker"]])).values

    # A: the original tree model's predictions, long-only
    base = rank_within_month(panel, VERSIONS["products"])
    pred_a = walk_forward(base, VERSIONS["products"]).set_index(["month", "ticker"])["prediction"]
    score_a = pd.Series(pred_a.reindex(pd.MultiIndex.from_frame(df[["month", "ticker"]])).values, index=df.index)

    # D: tree model on sector-relative attention, plus this month's return
    tree = df[["month", "ticker", "rank_next", "ret_next", "ret_vs_mkt_next"]].copy()
    features_d = []
    for column in ATTENTION:
        tree[column] = month_rank(df.assign(x=vs_sector(df, column)), "x")
        features_d.append(column)
    for column in ["censored_share", "momentum", "log_mcap", "vol", "ret_now"]:
        tree[column] = month_rank(df, column)
        features_d.append(column)
    pred_d = walk_forward(tree, features_d).set_index(["month", "ticker"])["prediction"]
    score_d = pd.Series(pred_d.reindex(pd.MultiIndex.from_frame(df[["month", "ticker"]])).values, index=df.index)

    score_b = simple_score(df, sector_relative=False)
    score_c = simple_score(df, sector_relative=True)
    results = {
        "A": portfolio(df, score_a, use_filter=False, hold=1),
        "B": portfolio(df, score_b, use_filter=True, hold=3),
        "C": portfolio(df, score_c, use_filter=True, hold=3),
        "D": portfolio(df, score_d, use_filter=True, hold=3),
        "B_no_filter": portfolio(df, score_b, use_filter=False, hold=3),
        "B_1m": portfolio(df, score_b, use_filter=True, hold=1),
        "A_size": portfolio(df, score_a, use_filter=False, hold=1, by_size=True),
        "A_3m": portfolio(df, score_a, use_filter=False, hold=3),
        "A_quarter": portfolio(df, score_a, use_filter=False, hold=1, share=1 / 4),
        "A_quarter_3m": portfolio(df, score_a, use_filter=False, hold=3, share=1 / 4),
    }

    summary = pd.DataFrame([
        {"version": v, "name": VERSION_NAMES[v], **summarise(r, spy_next, period)}
        for v, r in results.items() for period in ["development", "final"]
    ])
    dev = summary[(summary["period"] == "development") & summary["version"].isin(CANDIDATES)]
    chosen = dev.loc[dev["excess"].idxmax(), "version"]  # the rule fixed in advance
    summary["chosen"] = summary["version"] == chosen
    summary.to_csv(DATA_DIR / "strategy_summary.csv", index=False)

    monthly = pd.concat([r.drop(columns="picks").assign(version=v, spy=spy_next.reindex(r.index))
                         for v, r in results.items()]).reset_index()
    monthly.to_csv(DATA_DIR / "strategy_monthly.csv", index=False)

    # The chosen version's picks for every month, including the latest one,
    # whose returns are not known yet
    scores = {"A": score_a, "B": score_b, "C": score_c, "D": score_d}[chosen]
    use_filter = chosen != "A"
    picks = []
    for month, now in df.assign(score=scores).groupby("month"):
        candidates = now.dropna(subset=["score"])
        if candidates.empty or month < f"{FIRST_TEST_YEAR}-01":
            continue
        n_pick = round(len(candidates) / 3)
        if use_filter:
            falling = now["ret_now"] <= now["ret_now"].quantile(1 / 3)
            candidates = candidates[~falling.reindex(candidates.index, fill_value=False)]
        for rank, row in enumerate(candidates.nlargest(n_pick, "score").itertuples(), start=1):
            picks.append((month, rank, row.ticker, row.score))
    picks = pd.DataFrame(picks, columns=["month", "rank", "ticker", "score"])
    picks.to_csv(DATA_DIR / "strategy_picks.csv", index=False)

    # Live picks from LIVE_ALL_FROM: version A trained on and choosing from all 112
    everyone = pd.read_csv(DATA_DIR / "panel_monthly.csv")
    everyone["rank_next"] = everyone.groupby("month")["ret_next"].rank(pct=True)  # across all 112
    all_scores = walk_forward(rank_within_month(everyone, VERSIONS["products"]), VERSIONS["products"])
    live_112 = []
    for month, now in all_scores[all_scores["month"] >= LIVE_ALL_FROM].groupby("month"):
        n_pick = round(len(now.dropna(subset=["prediction"])) / 3)
        for rank, row in enumerate(now.nlargest(n_pick, "prediction").itertuples(), start=1):
            live_112.append((month, rank, row.ticker, row.prediction))
    live_112 = pd.DataFrame(live_112, columns=["month", "rank", "ticker", "score"])

    # Live record: add the latest month's picks once, and never change them
    log_path = DATA_DIR / "live_picks_log.csv"
    log = pd.read_csv(log_path) if log_path.exists() else pd.DataFrame(
        columns=["recorded_on", "month", "version", "rank", "ticker"])
    latest = max(picks["month"].max(), live_112["month"].max() if len(live_112) else "")
    if latest not in set(log["month"]):
        if latest >= LIVE_ALL_FROM:
            new = live_112[live_112["month"] == latest].assign(version=f"{chosen}, all 112")
        else:
            new = picks[picks["month"] == latest].assign(version=chosen)
        new = new.assign(recorded_on=pd.Timestamp.today().strftime("%Y-%m-%d"))
        log = pd.concat([log, new[log.columns]])
        log.to_csv(log_path, index=False)
        print(f"Live record: added the picks for {latest}")

    show = summary.set_index(["name", "period"])
    pct = ["return_net", "benchmark", "excess", "excess_vs_spy", "avg_cost"]
    show[pct] = show[pct] * 100
    print("Long-only, after costs, % a month (excess = above the 68 companies, weighted the same way):")
    print(show[pct + ["excess_t", "excess_vs_spy_t", "growth_100", "growth_100_benchmark",
                      "growth_100_spy"]].round(2).to_string())
    print(f"\nChosen by the development-period rule: {VERSION_NAMES[chosen]}")


if __name__ == "__main__":
    main()
