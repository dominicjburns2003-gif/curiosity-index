"""
Curiosity Index - step 31: good-news and bad-news attention surges.

Runs the test written down in docs/news_split_plan.md (committed on
10 Nov 2026 before this was written): the attention-wave strategy (no maximum
holding time), buying only surges whose share price beat the S&P 500 in the
surge week ("good news"), or only those whose price lagged it ("bad news").
Six versions each, on 2017-2021 and 2022-2026.

Writes data/processed/news_split_summary.csv and news_split_monthly.csv.

Run it from the project folder:
    python src/news_split.py              # the planned test
    python src/news_split.py --followup   # good news, leaving out companies already far ahead
    python src/news_split.py --followup2  # all but clearly bad news, and not already far ahead
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

import attention_wave as aw
from fetch_pageviews import cap_spikes
from pageview_store import load_daily

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
PERIODS = {"2017-2021": ("2017-03-01", "2021-12-31"), "2022-2026": (aw.FIRST_DECISION, None)}


def surge_week_moves(prices: pd.DataFrame, decision_days: pd.DatetimeIndex, tickers: list[str],
                     before_days: int = 0, length_days: int = 7) -> pd.DataFrame:
    """Each company's price change over the attention window (the 7 days ending
    PUBLICATION_LAG days before the decision), minus the S&P 500's. With
    before_days, the same for a stretch of length_days ending that many days
    before the window's end (e.g. the 13 weeks before the window)."""
    filled = prices[tickers + ["SPY"]].ffill()
    ends = decision_days - pd.Timedelta(days=aw.PUBLICATION_LAG + before_days)
    at_end = filled.reindex(filled.index.union(ends)).ffill().loc[ends]
    starts = ends - pd.Timedelta(days=length_days)
    at_start = filled.reindex(filled.index.union(starts)).ffill().loc[starts]
    change = at_end.values / at_start.values - 1
    change = pd.DataFrame(change, index=decision_days, columns=tickers + ["SPY"])
    return change[tickers].sub(change["SPY"], axis=0)


ALREADY_AHEAD = 0.20  # follow-up: not bought if 20+ points ahead of the S&P 500 over the 13 weeks before
CLEARLY_BAD = -0.02   # second follow-up: more than 2 points behind the market in the surge week
                      # (the median absolute weekly move against the market is 1.97%)


def main() -> None:
    followup = "--followup" in sys.argv or "--followup2" in sys.argv
    second = "--followup2" in sys.argv
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    universe = universe[universe["cohort"].isin(["original", "expansion", "broad"])]
    joined = pd.read_csv(MAPPING_DIR / "index_membership.csv").set_index("ticker")["sp500_added"]
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    article = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    views = cap_spikes(load_daily(columns=list(article))).reindex(columns=article.values).set_axis(article.index, axis=1)
    tickers = [t for t in article.index if t in prices.columns]

    rows, monthly_rows = [], []
    for period, (first, last) in PERIODS.items():
        trading = prices.loc[first:last].index
        decision_days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)
        member = pd.DataFrame({t: decision_days >= pd.Timestamp(joined[t]) if t in joined.index
                               else np.zeros(len(decision_days), bool) for t in tickers}, index=decision_days)
        this_week, usual = aw.weekly_attention(views[tickers], decision_days)
        move = surge_week_moves(prices, decision_days, tickers)
        kinds = [("good news", move > 0), ("bad news", move <= 0)]
        if followup:
            before = surge_week_moves(prices, decision_days, tickers, before_days=7, length_days=91)
            kinds = [("good news, not already far ahead", (move > 0) & (before <= ALREADY_AHEAD))]
            if second:
                kinds = [("not clearly bad news, not already far ahead",
                          (move >= CLEARLY_BAD) & (before <= ALREADY_AHEAD))]
        for news, keep in kinds:
            # A surge can only be bought if its week's price move is of this kind:
            # blocking the usual week elsewhere stops purchases, not sales
            usual_kind = usual.where(keep)
            for entry in aw.ENTRIES:
                for exit_rule in aw.EXITS:
                    weekly, trades = aw.simulate(this_week, usual_kind, prices.reindex(decision_days)[tickers + ["SPY"]],
                                                 member, entry, exit_rule, max_weeks=None)
                    m = aw.monthly(weekly)
                    excess = m["net"] - m["average_company"]
                    rows.append({"period": period, "news": news, "entry": entry, "exit": exit_rule,
                                 "months": len(m), "excess": excess.mean(), "t_stat": aw.t_stat(excess),
                                 "growth_100": 100 * (1 + m["net"]).prod(),
                                 "growth_100_average": 100 * (1 + m["average_company"]).prod(),
                                 "avg_held": weekly["n_held"].mean(), "purchases": len(trades)})
                    monthly_rows.append(m.assign(period=period, news=news, entry=entry, exit=exit_rule)
                                        .reset_index(names="month"))
    summary = pd.DataFrame(rows)
    name = "news_split_followup2" if second else "news_split_followup" if followup else "news_split"
    summary.to_csv(DATA_DIR / f"{name}_summary.csv", index=False)
    pd.concat(monthly_rows).to_csv(DATA_DIR / f"{name}_monthly.csv", index=False)
    show = summary.assign(excess=summary["excess"] * 100)
    print(show[["period", "news", "entry", "exit", "excess", "t_stat", "growth_100", "growth_100_average",
                "avg_held", "purchases"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
