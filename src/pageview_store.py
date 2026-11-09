"""
Where the daily page views are kept.

With thousands of pages, one file of daily views since 2017 would be about
50 MB and would be saved again in full by every evening's update, making the
repository grow by gigabytes a year. So the views are kept as one file per
month (data/processed/pageviews_daily/2026-11.csv, ...): past months never
change, and each evening only the current month's file is rewritten.

pageviews_recent.csv holds the last RECENT_DAYS days in one small file, for the
Trending table and the app.
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
STORE_DIR = DATA_DIR / "pageviews_daily"
TITLES_PATH = STORE_DIR / "titles.json"  # the titles added up for each article
RECENT_PATH = DATA_DIR / "pageviews_recent.csv"
RECENT_DAYS = 120


def load_daily(since: str | None = None, columns: list[str] | None = None) -> pd.DataFrame:
    """Daily views (one column per article), from the month of `since` onwards."""
    files = sorted(STORE_DIR.glob("????-??.csv"))
    if since:
        files = [f for f in files if f.stem >= since[:7]]
    if not files:
        return pd.DataFrame()
    usecols = None if columns is None else (lambda c: c == "date" or c in set(columns))
    parts = [pd.read_csv(f, index_col="date", parse_dates=True, usecols=usecols) for f in files]
    daily = pd.concat(parts).sort_index()
    return daily.loc[since:] if since else daily


def load_titles() -> dict:
    return json.loads(TITLES_PATH.read_text()) if TITLES_PATH.exists() else {}


def save_daily(daily: pd.DataFrame, titles: dict, months: list[str] | None = None) -> None:
    """Write the given months (all if None), the titles and the recent-days file."""
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    daily = daily.sort_index()
    by_month = daily.groupby(daily.index.strftime("%Y-%m"))
    for month, part in by_month:
        if months is None or month in months:
            part.index.name = "date"
            part.round(0).astype("Int64").to_csv(STORE_DIR / f"{month}.csv")
    TITLES_PATH.write_text(json.dumps(titles, indent=0, sort_keys=True))
    recent = daily.iloc[-RECENT_DAYS:]
    recent.index.name = "date"
    recent.round(0).astype("Int64").to_csv(RECENT_PATH)
