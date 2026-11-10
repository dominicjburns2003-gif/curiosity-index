"""
Curiosity Index - step 14: earnings announcement dates.

For every company, the dates it reported its quarterly results since 2017,
with analysts' EPS estimate and the EPS reported, from Yahoo Finance. Used by
earnings_test.py (see docs/earnings_test_plan.md).

Writes data/processed/earnings_dates.csv: date, ticker, eps_estimate,
eps_reported, surprise_pct. Only past announcements are kept.

With 546 companies, asking Yahoo for every one takes about an hour, so the
daily run only asks about companies that could have reported since: new
companies, and those whose last saved announcement is at least DUE_AFTER days
old (companies report about every 91 days). Saved announcements are kept as
they are, which also stops Yahoo's occasional revisions of old estimates from
moving past results.

Run it from the project folder:
    python src/fetch_earnings.py          # only companies that may have reported
    python src/fetch_earnings.py --full   # every company, all announcements again
"""

from pathlib import Path
import sys
import time

import pandas as pd
import yfinance as yf

START = "2017-01-01"
DUE_AFTER = 75  # days since the last saved announcement before asking again

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
        # Keep going: the company's saved announcements stay, and it is asked again tomorrow
        print(f"  {ticker}: no answer from Yahoo after 3 tries, skipped this time")
        return pd.DataFrame()
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
    saved = (pd.read_csv(OUT_PATH, parse_dates=["date"]) if OUT_PATH.exists() and "--full" not in sys.argv
             else pd.DataFrame(columns=["date", "ticker", "eps_estimate", "eps_reported", "surprise_pct"]))
    last = saved.groupby("ticker")["date"].max()
    today = pd.Timestamp.today().normalize()
    todo = [t for t in tickers if t not in last.index or (today - last[t]).days >= DUE_AFTER]
    print(f"Asking Yahoo about {len(todo)} of {len(tickers)} companies ...", flush=True)
    found = [earnings_dates(t) for t in todo]
    # Keep what is saved; add only announcements not saved yet
    out = pd.concat([saved[saved["ticker"].isin(tickers)], *found])
    out = out.drop_duplicates(["ticker", "date"], keep="first").sort_values(["ticker", "date"])
    out = out[["date", "ticker", "eps_estimate", "eps_reported", "surprise_pct"]]
    out.to_csv(OUT_PATH, index=False)
    counts = out.groupby("ticker").size().reindex(tickers, fill_value=0)
    print(f"Saved {len(out):,} announcements for {(counts > 0).sum()} companies to {OUT_PATH}")
    print("Companies with fewer than 10:", counts[counts < 10].to_dict())


if __name__ == "__main__":
    main()
