"""
Curiosity Index - step 26: attention and the drift after earnings surprises.

Runs the test written down in docs/earnings_drift_plan.md (committed on
10 Nov 2026 before this was written): is the share-price drift after an
earnings surprise larger when the company draws little Wikipedia attention
around the announcement?

Writes to data/processed/:
  drift_events.csv    one row per announcement: surprise, attention, drift
  drift_summary.csv   the results, whole period and each half

Run it from the project folder:
    python src/earnings_drift.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from fetch_pageviews import cap_spikes
from pageview_store import load_daily

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

START = "2017-01-01"
DRIFT_FROM, DRIFT_TO, DRIFT_SHORT = 2, 60, 20   # trading days after the announcement
MIN_PER_CELL = 3                                # announcements per surprise third and attention half


def build_events() -> pd.DataFrame:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    joined = pd.read_csv(MAPPING_DIR / "index_membership.csv").set_index("ticker")["sp500_added"]
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    earnings = pd.read_csv(DATA_DIR / "earnings_dates.csv", parse_dates=["date"])
    earnings = earnings[(earnings["date"] >= START) & earnings["eps_estimate"].notna()
                        & earnings["eps_reported"].notna()]

    article = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    daily = cap_spikes(load_daily(columns=list(article)))
    days = prices.index
    rows = []
    for e in earnings.itertuples():
        if e.ticker not in joined.index or pd.Timestamp(joined[e.ticker]) > e.date or e.ticker not in prices:
            continue  # only companies in the S&P 500 at the time
        a = days.searchsorted(e.date)  # the announcement day (or the next trading day)
        if a < 2 or a + DRIFT_TO >= len(days):
            continue
        p = prices[e.ticker]
        before, start, short_end, end = days[a - 2], days[a + DRIFT_FROM], days[a + DRIFT_SHORT], days[a + DRIFT_TO]
        if pd.isna(p[before]) or pd.isna(p[start]) or pd.isna(p[end]):
            continue
        views = daily[article[e.ticker]] if article[e.ticker] in daily else None
        if views is None:
            continue
        around = views.loc[e.date - pd.Timedelta(days=1): e.date + pd.Timedelta(days=1)]
        usual = views.loc[e.date - pd.Timedelta(days=35): e.date - pd.Timedelta(days=6)]
        if len(around) < 3 or len(usual) < 25 or usual.mean() <= 0:
            continue
        spy = prices["SPY"]
        rows.append({
            "ticker": e.ticker, "date": e.date, "quarter": str(e.date.to_period("Q")),
            "surprise": (e.eps_reported - e.eps_estimate) / p[before],
            "attention": around.mean() / usual.mean(),
            "drift": (p[end] / p[start] - 1) - (spy[end] / spy[start] - 1),
            "drift_20": (p[short_end] / p[start] - 1) - (spy[short_end] / spy[start] - 1),
        })
    return pd.DataFrame(rows)


def by_quarter(events: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Per quarter: the drift spread (most positive minus most negative surprise
    third) overall, among low-attention and among high-attention announcements."""
    out = []
    for quarter, q in events.groupby("quarter"):
        q = q.dropna(subset=["surprise", "attention", outcome]).copy()
        if len(q) < 6 * MIN_PER_CELL:
            continue
        q["third"] = pd.qcut(q["surprise"].rank(method="first"), 3, labels=False)
        q["low_attention"] = q["attention"] < q["attention"].median()
        cells = q.groupby(["low_attention", "third"])[outcome].agg(["mean", "size"])
        if (cells["size"] < MIN_PER_CELL).any() or len(cells) < 6:
            continue
        spread = lambda low: cells.loc[(low, 2), "mean"] - cells.loc[(low, 0), "mean"]
        overall = q.groupby("third")[outcome].mean()
        out.append({"quarter": quarter, "events": len(q), "spread": overall[2] - overall[0],
                    "spread_low": spread(True), "spread_high": spread(False),
                    "difference": spread(True) - spread(False)})
    return pd.DataFrame(out)


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def main() -> None:
    events = build_events()
    events.to_csv(DATA_DIR / "drift_events.csv", index=False)
    rows = []
    for outcome, label in [("drift", "60 days"), ("drift_20", "20 days")]:
        quarters = by_quarter(events, outcome)
        for period, part in {"2017-2026": quarters,
                             "2017-2021": quarters[quarters["quarter"] < "2022"],
                             "2022-2026": quarters[quarters["quarter"] >= "2022"]}.items():
            rows.append({"drift_to": label, "period": period, "quarters": len(part),
                         "events": int(part["events"].sum()),
                         "spread": part["spread"].mean(), "spread_t": t_stat(part["spread"]),
                         "spread_low": part["spread_low"].mean(), "spread_high": part["spread_high"].mean(),
                         "difference": part["difference"].mean(), "difference_t": t_stat(part["difference"])})
    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "drift_summary.csv", index=False)
    show = summary.copy()
    for c in ["spread", "spread_low", "spread_high", "difference"]:
        show[c] = (show[c] * 100).round(2)
    print(show.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
