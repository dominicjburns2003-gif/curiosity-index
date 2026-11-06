"""
Curiosity Index - step 14: earnings announcement dates.

For every company, the dates it reported its quarterly results since 2017,
with analysts' EPS estimate and the EPS reported, from Yahoo Finance. Used by
earnings_test.py (see docs/earnings_test_plan.md).

Writes data/processed/earnings_dates.csv: date, ticker, eps_estimate,
eps_reported, surprise_pct. Only past announcements are kept.

Run it from the project folder:
    python src/fetch_earnings.py
"""

from pathlib import Path
import time

import pandas as pd
import yfinance as yf

START = "2017-01-01"

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_PATH = PROJECT_DIR / "data" / "processed" / "earnings_dates.csv"


def earnings_dates(ticker: str) -> pd.DataFrame:
    """Past earnings announcements of one company (empty if Yahoo has none)."""
    for attempt in range(3):
        try:
            dates = yf.Ticker(ticker).get_earnings_dates(limit=100)
            break
        except Exception as error:  # Yahoo fails at random sometimes
            print(f"  {ticker}: {error}, retrying ...")
            time.sleep(5)
    else:
        raise RuntimeError(f"No earnings dates for {ticker} after 3 tries")
    if dates is None or dates.empty:
        return pd.DataFrame()
    dates = dates.reset_index()
    dates.columns = ["date", "eps_estimate", "eps_reported", "surprise_pct"]
    # Yahoo gives the time of day in New York; keep the date only
    dates["date"] = dates["date"].dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    dates = dates[(dates["date"] >= START) & dates["eps_reported"].notna()]
    return dates.assign(ticker=ticker)


def main() -> None:
    tickers = sorted(pd.read_csv(UNIVERSE_PATH)["ticker"].unique())
    found = [earnings_dates(t) for t in tickers]
    out = pd.concat(found).drop_duplicates(["ticker", "date"]).sort_values(["ticker", "date"])
    out = out[["date", "ticker", "eps_estimate", "eps_reported", "surprise_pct"]]
    out.to_csv(OUT_PATH, index=False)
    counts = out.groupby("ticker").size().reindex(tickers, fill_value=0)
    print(f"Saved {len(out):,} announcements for {(counts > 0).sum()} companies to {OUT_PATH}")
    print("Companies with fewer than 10:", counts[counts < 10].to_dict())


if __name__ == "__main__":
    main()
