"""
Curiosity Index - company descriptions for the Explorer.

Wikipedia's one-line "short description" of each company page (e.g. Games
Workshop: "British maker of miniature wargames"). Only companies without a
saved description are asked for, so the daily update is quick.

Writes data/mapping/company_descriptions.csv (ticker, description).

Run it from the project folder:
    python src/fetch_descriptions.py
"""

from pathlib import Path
import time

import pandas as pd

from wiki_api import polite_get

MAPPING_DIR = Path(__file__).resolve().parent.parent / "data" / "mapping"
OUT_PATH = MAPPING_DIR / "company_descriptions.csv"


def main() -> None:
    universe = pd.read_csv(MAPPING_DIR / "products_to_companies.csv", keep_default_na=False)
    pages = universe.drop_duplicates("ticker").set_index("ticker")["company_article"]
    saved = pd.read_csv(OUT_PATH, keep_default_na=False) if OUT_PATH.exists() else pd.DataFrame(
        columns=["ticker", "description"])
    todo = pages[~pages.index.isin(saved["ticker"])]
    found = {}
    for i in range(0, len(todo), 50):
        chunk = todo.iloc[i:i + 50]
        params = {"action": "query", "prop": "description", "titles": "|".join(chunk.values),
                  "redirects": 1, "format": "json", "formatversion": 2}
        answer = polite_get("https://en.wikipedia.org/w/api.php", params=params).json()["query"]
        titles = {n["to"]: n["from"] for n in answer.get("normalized", [])}
        described = {titles.get(p["title"], p["title"]).replace(" ", "_"): p.get("description", "")
                     for p in answer["pages"]}
        for ticker, page in chunk.items():
            found[ticker] = described.get(page, "")
        time.sleep(0.2)
    new = pd.DataFrame({"ticker": list(found), "description": list(found.values())})
    out = pd.concat([saved[saved["ticker"].isin(pages.index)], new]).sort_values("ticker")
    out.to_csv(OUT_PATH, index=False)
    print(f"{len(new)} descriptions added; {(out['description'] == '').sum()} companies have none")


if __name__ == "__main__":
    main()
