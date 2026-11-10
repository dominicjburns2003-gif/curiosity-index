"""
Curiosity Index - step 24: the attention-wave strategy.

Runs the test written down in docs/attention_wave_plan.md (committed on
10 Nov 2026 before this was written): each week, buy the companies whose
Wikipedia attention has surged to at least E times its usual week, hold them
while it lasts, and sell when it fades (back to normal, or below half the
peak) or after 26 weeks. Only companies in the S&P 500 at the time; S&P 500
when nothing is held; 0.1% trading costs.

Six versions (E = 1.5, 2, 3; exit "normal" or "half") on company pages, and
the same six on product pages as a control.

Writes to data/processed/:
  wave_summary.csv    one row per version
  wave_monthly.csv    monthly returns of each version and the benchmarks
  wave_trades.csv     every purchase and sale (main version, company pages)

Run it from the project folder:
    python src/attention_wave.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from fetch_pageviews import cap_spikes
from pageview_store import load_daily

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

FIRST_DECISION = "2022-01-01"
PUBLICATION_LAG = 2      # days: the attention week ends 2 days before the decision
WEEKS_OF_NORMAL = 8      # the usual week: average over the 8 weeks before
MIN_USUAL_WEEK = 2000    # views; smaller pages cannot trigger a purchase
MAX_WEEKS = 26           # longest holding
COST_PER_TRADE = 0.001
ENTRIES = [1.5, 2.0, 3.0]
EXITS = ["normal", "half"]
MAIN = (2.0, "normal")


def weekly_attention(daily: pd.DataFrame, decision_days: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    """For each decision day: views in the 7 days ending PUBLICATION_LAG days
    before it, and the usual week (average of the WEEKS_OF_NORMAL weeks before)."""
    seven = daily.rolling(7, min_periods=7).sum()
    usual = daily.rolling(7 * WEEKS_OF_NORMAL, min_periods=7 * WEEKS_OF_NORMAL).sum().shift(7) / WEEKS_OF_NORMAL
    ends = decision_days - pd.Timedelta(days=PUBLICATION_LAG)
    return (seven.reindex(ends).set_axis(decision_days), usual.reindex(ends).set_axis(decision_days))


def simulate(this_week: pd.DataFrame, usual: pd.DataFrame, prices: pd.DataFrame, member: pd.DataFrame,
             entry: float, exit_rule: str) -> tuple[pd.DataFrame, list[dict]]:
    days = this_week.index
    held, weights, rows, trades = {}, pd.Series({"SPY": 1.0}), [], []
    for d, d_next in zip(days[:-1], days[1:]):
        eligible = member.loc[d] & prices.loc[d].reindex(member.columns).notna()
        # 1. Sales
        for ticker in list(held):
            info = held[ticker]
            now = this_week.at[d, ticker]
            info["peak"] = max(info["peak"], now) if pd.notna(now) else info["peak"]
            info["weeks"] += 1
            faded = (now <= info["usual_at_entry"]) if exit_rule == "normal" else (now < 0.5 * info["peak"])
            if pd.isna(now) or faded or info["weeks"] >= MAX_WEEKS or not eligible.get(ticker, False):
                trades.append({"ticker": ticker, "bought": info["bought"], "sold": d, "weeks": info["weeks"]})
                del held[ticker]
        # 2. Purchases: a surge to at least `entry` times the usual week
        ratio = this_week.loc[d] / usual.loc[d]
        surging = ratio[(ratio >= entry) & (usual.loc[d] >= MIN_USUAL_WEEK) & eligible]
        for ticker in surging.index:
            if ticker not in held:
                held[ticker] = {"bought": d, "usual_at_entry": usual.at[d, ticker],
                                "peak": this_week.at[d, ticker], "weeks": 0}
        # 3. Equal amounts in everything held, or the S&P 500
        new_weights = (pd.Series(1 / len(held), index=list(held)) if held else pd.Series({"SPY": 1.0}))
        turnover = new_weights.sub(weights, fill_value=0).abs().sum()
        weights = new_weights
        week_returns = prices.loc[d_next] / prices.loc[d] - 1
        held_returns = week_returns.reindex(weights.index)
        gross = (weights * held_returns.fillna(0)).sum() / weights[held_returns.notna()].sum()
        members_returns = week_returns.reindex(eligible.index)[eligible]
        average = members_returns.mean()
        rows.append({"week_end": d_next, "net": gross - COST_PER_TRADE * turnover, "average_company": average,
                     "spy": week_returns["SPY"], "n_held": len(held)})
    for ticker, info in held.items():  # still held at the end
        trades.append({"ticker": ticker, "bought": info["bought"], "sold": pd.NaT, "weeks": info["weeks"]})
    return pd.DataFrame(rows).set_index("week_end"), trades


def monthly(weekly: pd.DataFrame) -> pd.DataFrame:
    """Weekly returns compounded within each month (by the week's end date)."""
    grouped = (1 + weekly[["net", "average_company", "spy"]]).groupby(weekly.index.to_period("M")).prod() - 1
    grouped.index = grouped.index.astype(str)
    return grouped


def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x)))


def main() -> None:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    joined = pd.read_csv(MAPPING_DIR / "index_membership.csv").set_index("ticker")["sp500_added"]
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)

    company_article = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    products = universe[universe["product_article"] != ""].groupby("ticker")["product_article"].apply(list)
    articles = sorted(set(company_article) | {p for ps in products for p in ps})
    daily = cap_spikes(load_daily(since="2021-06", columns=articles))
    company_views = daily.reindex(columns=company_article.values).set_axis(company_article.index, axis=1)
    product_views = pd.DataFrame({t: daily[ps].sum(axis=1, min_count=1) for t, ps in products.items()
                                  if set(ps) <= set(daily.columns)})

    trading = prices.loc[FIRST_DECISION:].index
    decision_days = pd.DatetimeIndex(trading.to_series().groupby(trading.to_period("W-FRI")).max().values)
    tickers = [t for t in company_article.index if t in prices.columns]
    member = pd.DataFrame({t: decision_days >= pd.Timestamp(joined[t]) if t in joined.index
                           else np.zeros(len(decision_days), bool) for t in tickers}, index=decision_days)
    week_prices = prices.reindex(decision_days)

    rows, monthly_rows = [], []
    for pages, views in [("company", company_views), ("products", product_views)]:
        cols = [t for t in tickers if t in views.columns]
        this_week, usual = weekly_attention(views[cols], decision_days)
        for entry in ENTRIES:
            for exit_rule in EXITS:
                weekly, trades = simulate(this_week, usual, week_prices[cols + ["SPY"]], member[cols],
                                          entry, exit_rule)
                m = monthly(weekly)
                excess, vs_spy = m["net"] - m["average_company"], m["net"] - m["spy"]
                done = [t for t in trades if pd.notna(t["sold"])]
                rows.append({
                    "pages": pages, "entry": entry, "exit": exit_rule, "main": (entry, exit_rule) == MAIN,
                    "months": len(m), "first_month": m.index[0], "last_month": m.index[-1],
                    "excess": excess.mean(), "t_stat": t_stat(excess),
                    "excess_vs_spy": vs_spy.mean(), "t_vs_spy": t_stat(vs_spy),
                    "growth_100": 100 * (1 + m["net"]).prod(),
                    "growth_100_average": 100 * (1 + m["average_company"]).prod(),
                    "growth_100_spy": 100 * (1 + m["spy"]).prod(),
                    "avg_held": weekly["n_held"].mean(), "weeks_empty": (weekly["n_held"] == 0).mean(),
                    "purchases": len(trades), "avg_weeks_held": np.mean([t["weeks"] for t in done]) if done else np.nan,
                })
                monthly_rows.append(m.assign(pages=pages, entry=entry, exit=exit_rule).reset_index(names="month"))
                if pages == "company" and (entry, exit_rule) == MAIN:
                    pd.DataFrame(trades).to_csv(DATA_DIR / "wave_trades.csv", index=False)

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "wave_summary.csv", index=False)
    pd.concat(monthly_rows).to_csv(DATA_DIR / "wave_monthly.csv", index=False)
    show = summary.copy()
    show[["excess", "excess_vs_spy"]] *= 100
    print(show[["pages", "entry", "exit", "excess", "t_stat", "excess_vs_spy", "t_vs_spy", "growth_100",
                "growth_100_average", "growth_100_spy", "avg_held", "weeks_empty", "purchases",
                "avg_weeks_held"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
