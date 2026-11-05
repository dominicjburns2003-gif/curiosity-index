"""
Curiosity Index - step 1: the first data pull.

Downloads daily English Wikipedia page views for a company page and its
product pages, saves them to a CSV file, and draws a chart.

Run it from the project folder:
    python src/fetch_pageviews.py
"""

from datetime import date, timedelta
from pathlib import Path
import time

import matplotlib.pyplot as plt
import pandas as pd
import requests

# ---- Settings you can change ------------------------------------------------

# One column per series: (chart label, list of Wikipedia titles to add up).
# Titles are written as in the page URL (spaces become underscores).
#
# Articles get renamed: on 14 Sep 2026 "Novo Nordisk" was moved to
# "Novo (company)" after the rebrand. Views are counted under whichever title
# the reader landed on, so the company series is old title + new title.
#
# "Ozempic" is a redirect to "Semaglutide", included to show how few people
# arrive through the brand name.
ARTICLES = {
    "Novo_Nordisk": ("Company page", ["Novo_Nordisk", "Novo_(company)"]),
    "Semaglutide": ("Product page (Ozempic / Wegovy drug)", ["Semaglutide"]),
    "Ozempic": ("Redirect: 'Ozempic' -> Semaglutide", ["Ozempic"]),
}

START = date(2017, 1, 1)
END = date.today() - timedelta(days=1)  # yesterday: today's data isn't complete

# Wikimedia asks every script to identify itself. Add your own contact
# details here if you like (e.g. a project URL or email).
HEADERS = {"User-Agent": "CuriosityIndex/0.1 (emlyon student research project)"}

API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user/{article}/daily/{start}/{end}"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
CHART_DIR = PROJECT_DIR / "charts"


def fetch_daily_views(article: str, start: date, end: date) -> pd.Series:
    """Ask the Wikimedia API for one article's daily views; return them as a series."""
    url = API.format(
        article=article,
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
    )
    response = requests.get(url, headers=HEADERS, timeout=30)
    if response.status_code == 404:  # title had no views at all in this period
        return pd.Series(dtype=int, name=article)
    response.raise_for_status()  # stop with a clear error if the request failed
    items = response.json()["items"]

    dates = pd.to_datetime([item["timestamp"][:8] for item in items], format="%Y%m%d")
    views = [item["views"] for item in items]
    return pd.Series(views, index=dates, name=article)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    CHART_DIR.mkdir(exist_ok=True)

    series = []
    for column, (label, titles) in ARTICLES.items():
        parts = []
        for title in titles:
            print(f"Downloading {title} ...")
            parts.append(fetch_daily_views(title, START, END))
            time.sleep(0.5)  # be polite to the API
        # Add up all titles of the same article (days missing from one title count as 0)
        combined = pd.concat(parts, axis=1).fillna(0).sum(axis=1).rename(column)
        series.append(combined)

    # One row per day, one column per series. Days with no views come back
    # missing from the API, so fill them with 0.
    daily = pd.concat(series, axis=1).fillna(0).astype(int)
    daily.index.name = "date"

    csv_path = DATA_DIR / "pageviews_novo_nordisk.csv"
    daily.to_csv(csv_path)
    print(f"Saved {len(daily):,} days of data to {csv_path}")

    # Daily numbers are noisy, so the chart shows monthly totals.
    monthly = daily.resample("MS").sum().iloc[:-1]  # drop the unfinished month

    fig, ax = plt.subplots(figsize=(10, 5))
    for column, (label, _) in ARTICLES.items():
        ax.plot(monthly.index, monthly[column] / 1000, label=label, linewidth=2)
    ax.set_title("Wikipedia attention: Novo Nordisk vs. its blockbuster drug")
    ax.set_ylabel("Monthly page views (thousands)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    chart_path = CHART_DIR / "novo_nordisk_attention.png"
    fig.savefig(chart_path, dpi=150)
    print(f"Saved chart to {chart_path}")

    # A quick summary in the terminal
    print("\nTotal views since", START, ":")
    print(daily.sum().map("{:,}".format).to_string())


if __name__ == "__main__":
    main()
