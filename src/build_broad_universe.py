"""
Curiosity Index - step 22: the broad universe (S&P 500 + Nasdaq-100).

Builds the list of companies and product pages for the broad expansion
written down in docs/broad_universe_plan.md. Every rule is applied by code,
the same way for every company, so nothing is picked by hand:

  1. Companies: the S&P 500 as listed on Wikipedia on 9 Nov 2026, plus the
     Nasdaq-100 companies not in it. One row per company (share classes such
     as GOOG/GOOGL are one company). Companies already in the hand-checked
     112 keep their hand-checked products and are not touched.
  2. Candidate products: every item Wikidata links to the company as a product,
     brand or subsidiary (src/wikidata_products.py) with an English page.
  3. Filters: items that are places, buildings, vehicles or satellites as
     single objects, people, events, technical components (file formats,
     protocols, programming languages, ...), or just a corporate entity with no
     product role are dropped; so are items linked to more than one company,
     items that are themselves companies in the universe or listed companies
     (an "owned by" link can be a shareholding), and lists. Wikidata's
     "product or material produced" is not used (it names general categories).
  4. Up to CANDIDATES per company are kept, the most widely covered first
     (number of Wikipedia language editions with a page: a measure of
     notability that has nothing to do with share prices).

Writes data/mapping/broad_candidates.csv. The attention check, renamed titles
and the final mapping come after (see the plan).

Run it from the project folder:
    python src/build_broad_universe.py
"""

from pathlib import Path
import re
import sys
import time
from urllib.parse import quote

import pandas as pd
import requests

import wikidata_products as wp
from wiki_api import HEADERS, polite_get

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
UNIVERSE_PATH = MAPPING_DIR / "products_to_companies.csv"
CANDIDATES = 8  # candidates per company
PRODUCTS = 5  # at most this many product pages per company are kept
MIN_VIEWS = 3000  # average monthly views over the last 12 months (as for the original universe)
MONTHLY_VIEWS_API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
                     "all-access/user/{title}/monthly/20251101/20261031")

# Nasdaq-100 companies not in the S&P 500, with their US tickers (from Wikidata)
NASDAQ_EXTRA_TICKERS = {
    "ASML": "ASML", "Alnylam_Pharmaceuticals": "ALNY", "Arm_Holdings": "ARM", "Astera_Labs": "ALAB",
    "Coca-Cola_Europacific_Partners": "CCEP", "CoreWeave": "CRWV", "Ferrovial": "FER",
    "MercadoLibre": "MELI", "MicroStrategy": "MSTR", "Nebius_Group": "NBIS", "Pinduoduo": "PDD",
    "Rocket_Lab": "RKLB", "Shopify": "SHOP", "SpaceX": "SPCX", "Thomson_Reuters": "TRI",
}

NASDAQ_EXTRA_SECTORS = {  # GICS sectors, as for the S&P 500 companies
    "ASML": "Information Technology", "Alnylam_Pharmaceuticals": "Health Care",
    "Arm_Holdings": "Information Technology", "Astera_Labs": "Information Technology",
    "Coca-Cola_Europacific_Partners": "Consumer Staples", "CoreWeave": "Information Technology",
    "Ferrovial": "Industrials", "MercadoLibre": "Consumer Discretionary",
    "MicroStrategy": "Information Technology", "Nebius_Group": "Communication Services",
    "Pinduoduo": "Consumer Discretionary", "Rocket_Lab": "Industrials", "Shopify": "Information Technology",
    "SpaceX": "Industrials", "Thomson_Reuters": "Industrials",
}

# Classes (Wikidata "instance of") that are not products people are curious about
NOT_PRODUCTS = {
    # single places, buildings and objects
    "shopping center", "skyscraper", "hotel", "cruise ship", "building", "office building", "factory",
    "railway line", "GPS satellite", "communications satellite", "attack submarine", "aircraft",
    "stadium", "airport", "power station", "nuclear power plant", "mine", "oil field", "ship",
    "outlet store", "headquarters", "campus", "television station", "radio station", "museum",
    "theme park", "amusement park", "data center", "research institute", "laboratory", "hospital",
    "golf course", "arena", "casino", "resort", "dam", "pipeline", "refinery", "satellite",
    "artificial satellite", "spacecraft", "container ship", "tanker", "oil tanker", "bridge",
    "railway station", "street", "park", "island", "estate", "mansion", "castle", "store",
    # people, events, pages that are not about one thing
    "human", "family", "event", "award", "Wikimedia disambiguation page", "Wikimedia list article",
    "foundation", "charitable organization", "sports team", "association football club",
    "lawsuit", "accident", "aviation accident", "recurring event", "conference",
    # technical components rather than products
    "file format", "file format family", "programming language", "CPU socket", "microarchitecture",
    "instruction set architecture", "software version", "computer network protocol",
    "application programming interface", "file system", "software library", "software framework",
    "communication protocol", "data format", "markup language", "query language", "algorithm",
    "technical standard", "UNIX 03", "Microsoft Windows component", "macOS", "technology",
    # more single objects and sites
    "ocean liner", "passenger vessel", "production platform", "liquefaction terminal", "bank building",
    "oil platform", "offshore platform", "LNG terminal", "port", "warehouse", "office", "tower",
    "commercial building", "industrial building", "plant", "facility", "natural gas processing plant",
    "built structure", "unfinished building", "supercarrier", "pre-commissioning unit", "scale model",
    "aircraft carrier", "warship", "conglomerate", "group of companies",
}
# Classes that only say "this is an organisation": dropped unless the item also has another class
CORPORATE_ONLY = {
    "business", "enterprise", "public company", "company", "subsidiary company", "organization",
    "holding company", "former entity", "division", "joint venture", "bank", "credit institution",
    "limited liability company", "privately held company", "corporation", "conglomerate",
    "financial institution", "investment company", "insurance company", "stock exchange",
    "real estate investment trust", "trust", "legal person", "business enterprise",
}
# Relations used. "Product or material produced" (P1056) is left out: it mostly
# names general categories ("software", "cheese", "electricity") whose pages are
# read for reasons that have nothing to do with the company.
RELATIONS_USED = {"manufacturer", "developer", "owned by", "parent organisation", "brand", "subsidiary"}


def company_list() -> pd.DataFrame:
    """The S&P 500 table on Wikipedia, plus the Nasdaq-100 extras."""
    params = {"action": "parse", "page": "List_of_S&P_500_companies", "prop": "wikitext",
              "format": "json", "formatversion": 2}
    wikitext = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS,
                            timeout=60).json()["parse"]["wikitext"]
    table = wikitext[wikitext.index("{|"): wikitext.index("|}", wikitext.index("{|"))]
    rows = []
    for row in table.split("\n|-")[2:]:
        # Cells start a line with "||", or occasionally share a line (e.g. Emcor's row)
        cells = [c.strip() for c in re.split(r"\n\|\|?|\|\|", row) if c.strip()]
        link = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", cells[1])
        rows.append({"ticker": re.search(r"\{\{[^|}]+\|([^}|]+)", cells[0]).group(1).strip().replace(".", "-"),
                     "listed_as": link.group(1).replace(" ", "_"), "company": link.group(2) or link.group(1),
                     "sector": cells[2], "sub_industry": cells[3], "index": "S&P 500",
                     "sp500_added": cells[5][:10]})
    companies = pd.DataFrame(rows)
    extra = pd.DataFrame({"listed_as": list(NASDAQ_EXTRA_TICKERS), "ticker": list(NASDAQ_EXTRA_TICKERS.values()),
                          "company": [a.replace("_", " ") for a in NASDAQ_EXTRA_TICKERS],
                          "sector": [NASDAQ_EXTRA_SECTORS[a] for a in NASDAQ_EXTRA_TICKERS],
                          "sub_industry": "", "index": "Nasdaq-100"})
    companies = pd.concat([companies, extra], ignore_index=True)
    resolved = resolve(companies["listed_as"].tolist())
    companies["company_article"] = companies["listed_as"].map(lambda a: resolved[a][0])
    companies["qid"] = companies["listed_as"].map(lambda a: resolved[a][1])
    # Share classes (GOOG/GOOGL, FOX/FOXA, NWS/NWSA) are one company: keep the first listed
    return companies.drop_duplicates("company_article").reset_index(drop=True)


def resolve(titles: list[str]) -> dict[str, tuple[str, str | None]]:
    """Each title's current page (following redirects) and its Wikidata ID."""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        params = {"action": "query", "titles": "|".join(t.replace("_", " ") for t in chunk), "redirects": 1,
                  "prop": "pageprops", "ppprop": "wikibase_item", "format": "json", "formatversion": 2}
        answer = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=60).json()
        normalized = {n["from"]: n["to"] for n in answer["query"].get("normalized", [])}
        redirects = {n["from"]: n["to"] for n in answer["query"].get("redirects", [])}
        pages = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in answer["query"]["pages"]}
        for title in chunk:
            current = title.replace("_", " ")
            current = redirects.get(normalized.get(current, current), normalized.get(current, current))
            out[title] = (current.replace(" ", "_"), pages.get(current))
    return out


def old_titles(pages: list[str]) -> dict[str, list[str]]:
    """Earlier titles of each page since 2016: titles it was moved from ("moved
    page [[A]] to [[B]]" in its edit history) that still redirect to it today.
    Their views are added to the page's, so a rename is not a fake collapse."""
    found = {}
    for page in pages:
        moved_from, params = set(), {
            "action": "query", "prop": "revisions", "titles": page.replace("_", " "), "rvprop": "comment",
            "rvlimit": 500, "rvend": "2016-01-01T00:00:00Z", "format": "json", "formatversion": 2}
        while True:
            answer = polite_get("https://en.wikipedia.org/w/api.php", params=params).json()
            for revision in answer["query"]["pages"][0].get("revisions", []):
                match = re.search(r"moved page \[\[([^\]]+)\]\] to \[\[([^\]]+)\]\]", revision.get("comment", ""))
                if match:
                    moved_from.add(match.group(1).replace(" ", "_"))
            if "continue" not in answer:
                break
            params.update(answer["continue"])
            time.sleep(0.1)
        current = resolve(sorted(moved_from)) if moved_from else {}
        # Only article titles (not drafts or user pages) that redirect to the page today
        found[page] = sorted(t for t, (target, _) in current.items()
                             if target == page and t != page and ":" not in t)
        time.sleep(0.1)
    return found


def candidates(companies: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    links = wp.links(companies["qid"].dropna().tolist())
    links = links[links["c"].isin(set(companies["qid"].dropna())) & links["relation"].isin(RELATIONS_USED)].copy()
    types = wp.types(links["p"].unique().tolist())
    labels = types.groupby("p")["type_label"].apply(lambda s: set(s.dropna()))
    links["types"] = links["p"].map(labels).apply(lambda s: s if isinstance(s, set) else set())

    company_qids = set(companies["qid"].dropna())
    taken = set(existing["company_article"]) | set(existing["product_article"])
    n_companies = links.groupby("p")["c"].nunique()
    keep = (
        ~links["types"].apply(lambda t: bool(t & NOT_PRODUCTS))
        & ~links["types"].apply(lambda t: bool(t) and t <= CORPORATE_ONLY)
        & ~links["types"].apply(lambda t: "public company" in t)  # a listed company (often a stake), not a product
        & (links["p"].map(n_companies) == 1)          # linked to one company only
        & ~links["p"].isin(company_qids)               # not itself a company in the universe
        & ~links["article"].isin(taken)
        & ~links["article"].str.startswith("List_of")
        # banks and asset managers "own" stakes in other firms, not products
        & ~((links["relation"] == "owned by") & links["c"].map(companies.set_index("qid")["sector"]).eq("Financials"))
    )
    kept = links[keep].copy()
    kept["sitelinks"] = kept["sitelinks"].astype(int)
    kept = kept.sort_values("sitelinks", ascending=False).drop_duplicates("p")
    kept = kept.groupby("c", group_keys=False).head(CANDIDATES)
    by_qid = companies.set_index("qid")
    out = pd.DataFrame({
        "ticker": kept["c"].map(by_qid["ticker"]), "company_article": kept["c"].map(by_qid["company_article"]),
        "product_article": kept["article"], "product_qid": kept["p"], "relation": kept["relation"],
        "sitelinks": kept["sitelinks"], "types": kept["types"].apply(lambda t: "; ".join(sorted(t))),
    })
    print(f"Candidates: {len(links['p'].unique()):,} items from Wikidata, {len(out):,} kept "
          f"for {out['ticker'].nunique()} companies")
    return out.sort_values(["ticker", "sitelinks"], ascending=[True, False])


def attention_check(cands: pd.DataFrame) -> pd.DataFrame:
    """Average monthly views over the last 12 complete months (Nov 2025 - Oct 2026),
    the same check as for the original universe; pages below MIN_VIEWS are dropped
    and at most PRODUCTS per company are kept, the most widely covered first."""
    views = []
    for article in cands["product_article"]:
        url = MONTHLY_VIEWS_API.format(title=quote(article, safe=""))
        response = polite_get(url)
        items = response.json().get("items", []) if response.status_code == 200 else []
        views.append(sum(i["views"] for i in items) / 12)
        time.sleep(0.1)
    cands = cands.assign(avg_monthly_views=[round(v) for v in views])
    passed = cands[cands["avg_monthly_views"] >= MIN_VIEWS]
    return passed.groupby("ticker", group_keys=False).head(PRODUCTS)


def main() -> None:
    existing = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    companies = company_list()
    # When each company joined the S&P 500, for tests that only use companies in the index at the time
    companies.loc[companies["index"] == "S&P 500", ["ticker", "sp500_added"]].to_csv(
        MAPPING_DIR / "index_membership.csv", index=False)
    new = companies[~companies["ticker"].isin(existing["ticker"])
                    & ~companies["company_article"].isin(existing["company_article"])]
    print(f"{len(companies)} companies listed; {len(companies) - len(new)} already in the 112; {len(new)} new")
    renamed = old_titles(new["company_article"].tolist())
    new = new.assign(company_titles=new["company_article"].map(lambda a: "|".join([a, *renamed[a]])))
    print(f"{sum(bool(v) for v in renamed.values())} company pages have earlier titles")
    new.to_csv(MAPPING_DIR / "broad_companies.csv", index=False)
    if "--companies-only" in sys.argv:
        return
    cands = candidates(new, existing)
    cands.to_csv(MAPPING_DIR / "broad_candidates.csv", index=False)
    chosen = attention_check(cands)
    print(f"After the attention check: {len(chosen)} product pages for {chosen['ticker'].nunique()} companies")
    chosen.to_csv(MAPPING_DIR / "broad_draft.csv", index=False)


if __name__ == "__main__":
    main()
