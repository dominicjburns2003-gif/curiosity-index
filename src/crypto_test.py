"""
Curiosity Index - step 35: does Wikipedia attention predict crypto prices?

Runs the test written down in docs/crypto_plan.md (committed on 10 Nov 2026
before this was written): weekly (Sundays), for Bitcoin, Ethereum, Solana and
Cardano, regress the next week's and the next 4 weeks' log return on the
coin's attention (log of its page views that week against its usual week)
and its return over the previous 4 weeks, pooled and coin by coin, with
Newey-West standard errors (coin by coin) and Driscoll-Kraay standard
errors (pooled: coins in the same week move together).

Writes data/processed/crypto_summary.csv and crypto_weekly.csv.

Run it from the project folder:
    python src/crypto_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from attention_wave import PUBLICATION_LAG, weekly_attention
from fetch_pageviews import cap_spikes
from pageview_store import load_daily
from risk_signals_test import newey_west

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"


def driscoll_kraay(y: np.ndarray, X: np.ndarray, weeks: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    """OLS with standard errors that allow for coins moving together in the same week
    and for overlap across neighbouring weeks: each week's scores are added up
    across coins, then Newey-West over weeks (Driscoll and Kraay, 1998)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    scores = pd.DataFrame(X * (y - X @ beta)[:, None]).groupby(weeks).sum().sort_index().to_numpy()
    S = scores.T @ scores
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        g = scores[lag:].T @ scores[:-lag]
        S += w * (g + g.T)
    xtx_inv = np.linalg.inv(X.T @ X)
    cov = xtx_inv @ S @ xtx_inv
    return beta, beta / np.sqrt(np.diag(cov))


def main() -> None:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    coins = universe[universe["cohort"] == "crypto"].set_index("ticker")["company_article"]
    prices = yf.download(list(coins.index), start="2016-06-01", auto_adjust=True, progress=False)["Close"]
    views = cap_spikes(load_daily(columns=list(coins.values)))
    sundays = pd.date_range("2017-03-05", prices.index.max(), freq="W-SUN")
    this_week, usual = weekly_attention(views, sundays)

    rows = []
    for ticker, page in coins.items():
        p = prices[ticker].reindex(sundays)
        log_p = np.log(p)
        frame = pd.DataFrame({
            "coin": ticker,
            "attention": np.log(this_week[page] / usual[page].where(usual[page] > 0)),
            "past_4w": log_p - log_p.shift(4),
            "next_1w": log_p.shift(-1) - log_p,
            "next_4w": log_p.shift(-4) - log_p,
        }, index=sundays)
        rows.append(frame)
    # A week with no views (e.g. before a page existed) has no usable attention value
    weekly = pd.concat(rows).replace([np.inf, -np.inf], np.nan).dropna(subset=["attention", "past_4w"])
    weekly.index.name = "week"
    weekly.to_csv(DATA_DIR / "crypto_weekly.csv")

    out = []
    for outcome, lags in [("next_1w", 1), ("next_4w", 4)]:
        groups = {"pooled": weekly, **{c: g for c, g in weekly.groupby("coin")}}
        for name, g in groups.items():
            g = g.dropna(subset=[outcome])
            # Pooled: each coin's signals standardised, plus a constant per coin
            X_parts = [g[["attention", "past_4w"]].groupby(g["coin"]).transform(lambda s: (s - s.mean()) / s.std())]
            if name == "pooled":
                dummies = pd.get_dummies(g["coin"], dtype=float)
                X = np.column_stack([X_parts[0].to_numpy(), dummies.to_numpy()])
            else:
                X = np.column_stack([np.ones(len(g)), X_parts[0].to_numpy()])
            # Sorted by week so the Newey-West lags compare neighbouring weeks
            order = np.argsort(g.index.values, kind="stable")
            if name == "pooled":  # several coins in the same week: Driscoll-Kraay, lags in weeks
                beta, t = driscoll_kraay(g[outcome].to_numpy(), X, g.index.values, lags)
            else:
                beta, t = newey_west(g[outcome].to_numpy()[order], X[order], lags)
            first = 0 if name == "pooled" else 1
            out.append({"outcome": outcome, "group": name, "weeks": len(g),
                        "first_week": g.index.min().date(), "attention_b": beta[first], "attention_t": t[first],
                        "past_4w_b": beta[first + 1], "past_4w_t": t[first + 1]})
    summary = pd.DataFrame(out)
    summary.to_csv(DATA_DIR / "crypto_summary.csv", index=False)
    show = summary.copy()
    show[["attention_b", "past_4w_b"]] *= 100  # % change in the log return per standard deviation
    print(show.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
