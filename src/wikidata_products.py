"""
Curiosity Index - step 22a: candidate product pages from Wikidata.

For a list of companies (each with its Wikidata ID), finds every item that
Wikidata links to the company as a product, brand or subsidiary, and that has
an English Wikipedia page:

  manufacturer (P176), developer (P178), owned by (P127), parent organisation
  (P749) on the item; brand (P1716), product (P1056), subsidiary (P355) on
  the company.

Each relation is asked for separately in small batches (a combined query
timed out on Wikidata's servers), and every answer is saved as it arrives, so
an interrupted run picks up where it stopped. Then the "instance of" (P31)
classes of all the items are fetched, for filtering.

Writes data/mapping/wikidata_cache/ (links.csv, types.csv).
"""

from pathlib import Path
import time

import pandas as pd
import requests

from wiki_api import HEADERS

SPARQL = "https://query.wikidata.org/sparql"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "mapping" / "wikidata_cache"
RELATIONS = {  # name: pattern, with ?c the company and ?p the item
    "manufacturer": "?p wdt:P176 ?c", "developer": "?p wdt:P178 ?c", "owned by": "?p wdt:P127 ?c",
    "parent organisation": "?p wdt:P749 ?c", "brand": "?c wdt:P1716 ?p", "product": "?c wdt:P1056 ?p",
    "subsidiary": "?c wdt:P355 ?p",
}
BATCH = 25


def ask(query: str) -> list[dict]:
    for attempt in range(5):
        try:
            r = requests.post(SPARQL, data={"query": query},
                              headers={**HEADERS, "Accept": "application/sparql-results+json"}, timeout=60)
            if r.status_code == 200:
                return [{k: v["value"] for k, v in row.items()} for row in r.json()["results"]["bindings"]]
        except requests.RequestException:
            pass
        time.sleep(10 * (attempt + 1))
    raise RuntimeError("Wikidata did not answer after 5 tries")


def links(qids: list[str]) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / "links.csv"
    done = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["c", "p", "article", "sitelinks", "relation"])
    asked = set(zip(done.get("asked_company", []), done.get("relation", []))) if "asked_company" in done else set()
    rows = []
    for relation, pattern in RELATIONS.items():
        todo = [q for q in qids if (q, relation) not in asked]
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            values = " ".join("wd:" + q for q in batch)
            answer = ask(f"""SELECT ?c ?p ?article ?sl WHERE {{ VALUES ?c {{ {values} }} {pattern} .
                ?article schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> .
                ?p wikibase:sitelinks ?sl . }}""")
            got = pd.DataFrame(answer, columns=["c", "p", "article", "sl"])
            got = got.rename(columns={"sl": "sitelinks"}).assign(relation=relation)
            # One marker row per company asked, so a rerun knows it was asked even with no answer
            markers = pd.DataFrame({"asked_company": batch, "relation": relation})
            rows.append(pd.concat([got, markers]))
            pd.concat([done, *rows]).to_csv(path, index=False)
            time.sleep(0.5)
        print(f"  {relation}: done", flush=True)
    out = pd.concat([done, *rows]) if rows else done
    out = out[out["p"].notna()].copy()
    for column in ["c", "p"]:
        out[column] = out[column].str.rsplit("/", n=1).str[-1]
    out["article"] = out["article"].str.replace("https://en.wikipedia.org/wiki/", "", regex=False)
    out["article"] = out["article"].map(requests.utils.unquote)
    return out.drop(columns=["asked_company"], errors="ignore").drop_duplicates()


def types(items: list[str]) -> pd.DataFrame:
    path = CACHE_DIR / "types.csv"
    done = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["p", "type", "type_label"])
    todo = sorted(set(items) - set(done["p"]))
    rows = [done]
    for i in range(0, len(todo), 200):
        values = " ".join("wd:" + q for q in todo[i:i + 200])
        answer = ask(f"""SELECT ?p ?type ?type_label WHERE {{ VALUES ?p {{ {values} }}
            OPTIONAL {{ ?p wdt:P31 ?type . OPTIONAL {{ ?type rdfs:label ?type_label FILTER(lang(?type_label) = "en") }} }} }}""")
        got = pd.DataFrame(answer, columns=["p", "type", "type_label"])
        for column in ["p", "type"]:
            got[column] = got[column].str.rsplit("/", n=1).str[-1]
        rows.append(got)
        pd.concat(rows).to_csv(path, index=False)
        time.sleep(0.5)
    return pd.concat(rows).drop_duplicates()
