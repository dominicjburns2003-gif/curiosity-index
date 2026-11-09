"""
Shared helpers for talking to Wikimedia, used by several scripts.

Wikimedia asks every script to say who runs it and to slow down when told to,
so all requests go through polite_get().
"""

import time
from datetime import date
from urllib.parse import quote

import pandas as pd
import requests

HEADERS = {
    "User-Agent": "CuriosityIndex/0.1 "
    "(https://github.com/dominicjburns2003-gif/curiosity-index; emlyon student research project)"
}

DAILY_VIEWS_API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user/{title}/daily/{start}/{end}"
)


def polite_get(url: str, **kwargs) -> requests.Response:
    """GET a URL; if the server says "too many requests" (429), wait and try again."""
    for attempt in range(6):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 5:
                raise
            print(f"  no answer, trying again in {10 * (attempt + 1)}s ...")
            time.sleep(10 * (attempt + 1))
            continue
        if response.status_code != 429:
            return response
        wait = int(response.headers.get("Retry-After", 0)) or 5 * 2**attempt
        print(f"  rate-limited, waiting {wait}s ...")
        time.sleep(wait)
    response.raise_for_status()
    return response


def daily_views(title: str, start: date, end: date) -> pd.Series:
    """Daily page views (agent=user, so known bots excluded) of one article title.

    Days with no views are missing from the API's answer; they come back as 0.
    """
    url = DAILY_VIEWS_API.format(
        title=quote(title, safe=""), start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d")
    )
    response = polite_get(url)
    all_days = pd.date_range(start, end, freq="D")
    if response.status_code == 404:  # title had no views at all in this period
        return pd.Series(0, index=all_days, name=title)
    response.raise_for_status()
    items = response.json()["items"]
    dates = pd.to_datetime([item["timestamp"][:8] for item in items], format="%Y%m%d")
    views = pd.Series([item["views"] for item in items], index=dates, name=title)
    return views.reindex(all_days, fill_value=0)
