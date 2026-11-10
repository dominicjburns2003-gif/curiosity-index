"""
Curiosity Index - step 27: Discovery.

Finds listed companies, and products of listed companies, among the pages
English Wikipedia's readers looked at most in the last week, including ones
the index does not track. A tool for spotting where attention is going, not a
tested signal.

  1. Wikimedia's daily list of the 1,000 most-read pages, for the last
     DAYS published days (one small request per day).
  2. Wikidata: which of those pages is a company listed on the NYSE, Nasdaq
     or London Stock Exchange, or is linked to one as its maker, developer,
     owner or parent company. These links are automatic and can be wrong or
     out of date (e.g. a product sold years ago): the app says so.
  3. For each match: its busiest day, its views that day, and the surge: views
     that day against its average over the other days of the week. A day it
     was not in the top 1,000 counts at the 1,000th page's views (an upper
     bound), so the surge shown is if anything too small.

Writes data/processed/discovery.csv.

Run it from the project folder:
    python src/discovery.py
"""

from datetime import date, timedelta
from pathlib import Path
import time

import pandas as pd
import requests

from wiki_api import HEADERS, polite_get

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"

DAYS = 7
TOP_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{d:%Y/%m/%d}"
EXCHANGES = {"Q13677": "NYSE", "Q82059": "Nasdaq", "Q171240": "London"}
LINKS = {"P176": "made by", "P178": "developed by", "P127": "owned by", "P749": "part of"}


def top_lists() -> pd.DataFrame:
    """The most-read pages for the last DAYS published days."""
    rows, day = [], date.today() - timedelta(days=1)
    while len({r["date"] for r in rows}) < DAYS and day > date.today() - timedelta(days=DAYS + 10):
        response = polite_get(TOP_API.format(d=day))
        if response.status_code == 200:
            for a in response.json()["items"][0]["articles"]:
                rows.append({"date": pd.Timestamp(day), "article": a["article"], "views": a["views"]})
        day -= timedelta(days=1)
        time.sleep(0.2)
    top = pd.DataFrame(rows)
    # Not real articles: the main page, search, other namespaces
    return top[~top["article"].str.contains(":") & (top["article"] != "Main_Page")]


def wikidata_ids(titles: list[str]) -> dict[str, str]:
    ids = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        params = {"action": "query", "titles": "|".join(chunk), "prop": "pageprops", "ppprop": "wikibase_item",
                  "redirects": 1, "format": "json", "formatversion": 2}
        answer = polite_get("https://en.wikipedia.org/w/api.php", params=params).json()["query"]
        normal = {n["to"]: n["from"] for n in answer.get("normalized", [])}
        for page in answer["pages"]:
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                ids[normal.get(page["title"], page["title"]).replace(" ", "_")] = qid
        time.sleep(0.2)
    return ids


def listed_links(qids: list[str]) -> pd.DataFrame:
    """Each item that is a listed company, or is linked to one, with the company."""
    exchanges = " ".join("wd:" + q for q in EXCHANGES)
    link_path = "|".join("wdt:" + p for p in LINKS)
    rows = []
    for i in range(0, len(qids), 100):
        values = " ".join("wd:" + q for q in qids[i:i + 100])
        query = f"""SELECT ?item ?company ?companyLabel ?ex ?ticker ?how WHERE {{
          VALUES ?item {{ {values} }} VALUES ?ex {{ {exchanges} }}
          {{ ?item p:P414 ?s . ?s ps:P414 ?ex . OPTIONAL {{ ?s pq:P249 ?ticker }}
             BIND(?item AS ?company) BIND("company" AS ?how) }}
          UNION
          {{ ?item ?p ?company . VALUES ?p {{ {" ".join("wdt:" + p for p in LINKS)} }}
             ?company p:P414 ?s . ?s ps:P414 ?ex . OPTIONAL {{ ?s pq:P249 ?ticker }}
             ?prop wikibase:directClaim ?p . BIND(STRAFTER(STR(?prop), "entity/") AS ?how) }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        for attempt in range(4):
            try:
                r = requests.post("https://query.wikidata.org/sparql", data={"query": query},
                                  headers={**HEADERS, "Accept": "application/sparql-results+json"}, timeout=60)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError("Wikidata did not answer")
        for b in r.json()["results"]["bindings"]:
            rows.append({k: v["value"].rsplit("/", 1)[-1] if k in ("item", "company", "ex") else v["value"]
                         for k, v in b.items()})
        time.sleep(1)
    return pd.DataFrame(rows, columns=["item", "company", "companyLabel", "ex", "ticker", "how"])


def main() -> None:
    top = top_lists()
    days = sorted(top["date"].unique())
    floor = top.groupby("date")["views"].min()  # the 1,000th page's views each day
    wide = top.pivot_table(index="article", columns="date", values="views")
    wide = wide.fillna(floor)  # not in the list that day: at most the 1,000th page's views

    ids = wikidata_ids(list(wide.index))
    links = listed_links(sorted(set(ids.values())))
    item_of = {q: a for a, q in ids.items()}
    links["article"] = links["item"].map(item_of)
    links["exchange"] = links["ex"].map(EXCHANGES)
    links["us_first"] = links["exchange"].map({"NYSE": 0, "Nasdaq": 0, "London": 1})
    links["link"] = links["how"].map(lambda h: "is the company" if h == "company" else LINKS.get(h, h))
    # One row per page: prefer "is the company", then one company per page (the first listed)
    links = links.sort_values(["article", "how", "us_first"],
                              key=lambda s: s.ne("company") if s.name == "how" else s)
    links = links.groupby("article").agg(company=("companyLabel", "first"), ticker=("ticker", "first"),
                                         exchange=("exchange", "first"), link=("link", "first"),
                                         company_qid=("company", "first"))

    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    tracked_pages = set(universe["company_article"]) | set(universe["product_article"])
    # Our companies by Wikidata ID, so Wikidata's company is matched to our name and ticker
    ours = universe.drop_duplicates("ticker").set_index("company_article")
    our_ids = wikidata_ids(list(ours.index))
    by_qid = {q: ours.loc[a] for a, q in our_ids.items() if a in ours.index}
    rows = []
    for article, r in links.iterrows():
        mine = by_qid.get(r["company_qid"])
        if mine is not None:
            r = r.copy()
            r["company"], r["ticker"] = mine["company"], mine.name and mine["ticker"]
        elif str(r["company"]).startswith("Q") and str(r["company"])[1:].isdigit():
            r = r.copy()
            r["company"] = article.replace("_", " ") if r["link"] == "is the company" else r["ticker"]
        series = wide.loc[article]
        peak_day = series.idxmax()
        others = series.drop(peak_day)
        rows.append({
            "article": article, "company": r["company"], "ticker": r["ticker"], "exchange": r["exchange"],
            "link": r["link"], "peak_day": peak_day.date(), "peak_views": int(series.max()),
            "week_views": int(series.sum()), "days_in_top": int(top[top["article"] == article]["date"].nunique()),
            "surge": series.max() / others.mean() if len(others) else float("nan"),
            "status": ("page tracked" if article in tracked_pages
                       else "company tracked" if mine is not None else "new to the index"),
        })
    out = pd.DataFrame(rows).sort_values("peak_views", ascending=False)
    out["week_start"], out["week_end"] = days[0].date(), days[-1].date()
    out.to_csv(DATA_DIR / "discovery.csv", index=False)
    print(f"{len(top['article'].unique())} pages in the top 1,000 from {days[0].date()} to {days[-1].date()}; "
          f"{len(out)} linked to a listed company ({(out['status'] == 'new to the index').sum()} companies new to the index)")
    print(out.head(30)[["article", "company", "ticker", "exchange", "link", "peak_day", "peak_views", "surge", "status"]]
          .round(1).to_string(index=False))


if __name__ == "__main__":
    main()
