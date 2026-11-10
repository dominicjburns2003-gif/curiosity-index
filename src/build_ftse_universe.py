"""
Curiosity Index - step 28: the FTSE 100.

Builds the UK part of the universe (docs/ftse_plan.md), the same way as the
S&P 500 expansion:

  1. Companies: the FTSE 100 as listed on Wikipedia (FTSE_100_Index, the
     constituents table) on 10 Nov 2026. London tickers on Yahoo end in ".L"
     (BT.A becomes BT-A.L). The five already tracked through their US listing
     (AstraZeneca, BAT, Coca-Cola Europacific, Diageo, Unilever) are not added
     again. Earlier titles of renamed company pages are added up.
  2. Products: drafted from general knowledge (PRODUCTS below), then checked
     automatically (src/check_universe.py) and reviewed, by the same rules as
     before. Companies without product pages are tracked by their page alone.

Writes data/mapping/ftse_companies.csv and ftse_draft.csv; with --finalise,
adds the reviewed companies and products to products_to_companies.csv
(cohort "ftse").

Run it from the project folder:
    python src/build_ftse_universe.py
    python src/check_universe.py data/mapping/ftse_draft.csv
    python src/prepare_review.py data/mapping/ftse_draft_check.csv
    python src/build_ftse_universe.py --finalise
"""

from pathlib import Path
import re
import sys

import pandas as pd
import requests

from build_broad_universe import old_titles, resolve
from wiki_api import HEADERS

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
UNIVERSE_PATH = MAPPING_DIR / "products_to_companies.csv"

PRODUCTS = {
    "ABF.L": ["Primark", "Twinings", "Ovaltine", "Kingsmill_(bread)", "Silver_Spoon_(brand)"],
    "BA.L": ["BAE_Systems_Hawk", "Astute-class_submarine", "Type_26_frigate"],
    "BP.L": ["Castrol", "Aral_(company)"],
    "BT-A.L": ["EE_Limited", "Openreach", "Plusnet"],
    "GAW.L": ["Warhammer_40,000", "Warhammer_Age_of_Sigmar", "Warhammer_(game)"],
    "GSK.L": ["Shingrix", "Arexvy", "Trelegy_Ellipta", "Dovato"],
    "HLN.L": ["Sensodyne", "Panadol", "Centrum_(brand)", "Aquafresh", "Advil"],
    "HSBA.L": ["First_Direct"],
    "IHG.L": ["Holiday_Inn", "Crowne_Plaza", "Holiday_Inn_Express", "Kimpton_Hotels_&_Restaurants"],
    "IMB.L": ["Davidoff_(cigarette)", "JPS_(cigarette)", "Rizla", "Blu_(electronic_cigarette)"],
    "IAG.L": ["British_Airways", "Iberia_(airline)", "Aer_Lingus", "Vueling", "Avios"],
    "KGF.L": ["B&Q", "Screwfix", "Castorama"],
    "LLOY.L": ["Halifax_(bank)", "Bank_of_Scotland", "Lloyds_Bank"],
    "LSEG.L": ["Refinitiv"],
    "MKS.L": ["Percy_Pig"],
    "NWG.L": ["NatWest", "Royal_Bank_of_Scotland", "Coutts"],
    "PSON.L": ["Edexcel"],
    "RKT.L": ["Dettol", "Durex", "Nurofen", "Vanish_(brand)", "Finish_(detergent)", "Strepsils", "Gaviscon",
              "Lysol", "Air_Wick"],
    "REL.L": ["LexisNexis", "The_Lancet", "Elsevier"],
    "RR.L": ["Rolls-Royce_Trent", "Rolls-Royce_Trent_XWB"],
    "SBRY.L": ["Argos_(retailer)", "Nectar_(loyalty_card)"],
    "TSCO.L": ["Tesco_Clubcard", "Booker_Group"],
    "WTB.L": ["Premier_Inn", "Beefeater_(restaurant)"],
    "WPP.L": ["Ogilvy_(agency)"],
    "CNA.L": ["British_Gas"],
    "BARC.L": ["Barclaycard"],
    "MRO.L": ["GKN_Aerospace"],
    "SMIN.L": ["Smiths_Detection"],
}


# Decisions on the review, 10 Nov 2026, by the same rules as before: the page must
# be about this company's product, not a generic one or another company
OVERRIDES = {
    "Zoster_vaccine": "drop",                                 # generic: several makers
    "Respiratory_syncytial_virus_vaccine": "drop",            # generic: several makers
    "GKN": "drop",                                            # the old group; Melrose owns only GKN Aerospace
}


def company_list() -> pd.DataFrame:
    params = {"action": "parse", "page": "FTSE_100_Index", "prop": "wikitext", "format": "json", "formatversion": 2}
    wikitext = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS,
                            timeout=60).json()["parse"]["wikitext"]
    start = wikitext.index('id="constituents"')
    table = wikitext[start: wikitext.index("|}", start)]
    rows = []
    for row in table.split("\n|-")[2:]:
        cells = [c.strip() for c in re.split(r"\|\|", row.strip().lstrip("|"))]
        if len(cells) < 4:
            continue
        link = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", cells[0])
        epic = cells[1].strip()
        rows.append({"listed_as": link.group(1).replace(" ", "_"), "company": link.group(2) or link.group(1),
                     "ticker": epic.replace(".", "-").rstrip("-") + ".L", "sector": cells[3].strip(),
                     "sub_industry": cells[3].strip()})
    companies = pd.DataFrame(rows)
    current = resolve(companies["listed_as"].tolist())
    companies["company_article"] = companies["listed_as"].map(lambda a: current[a][0])
    companies["qid"] = companies["listed_as"].map(lambda a: current[a][1] or "")
    return companies


def main() -> None:
    if "--finalise" in sys.argv:
        finalise()
        return
    existing = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    companies = company_list()
    new = companies[~companies["company_article"].isin(existing["company_article"])].copy()
    print(f"{len(companies)} FTSE 100 companies; {len(companies) - len(new)} already tracked; {len(new)} new")
    renamed = old_titles(new["company_article"].tolist())
    new["company_titles"] = new["company_article"].map(lambda a: "|".join([a, *renamed[a]]))
    new.to_csv(MAPPING_DIR / "ftse_companies.csv", index=False)
    draft = pd.DataFrame([{"ticker": c.ticker, "company": c.company, "sector": c.sector,
                           "company_article": c.company_article, "product_article": p}
                          for c in new.itertuples() for p in PRODUCTS.get(c.ticker, [])])
    draft = draft[draft["product_article"] != draft["company_article"]]
    draft.to_csv(MAPPING_DIR / "ftse_draft.csv", index=False)
    print(f"{len(draft)} drafted product pages for {draft['ticker'].nunique()} companies")


def finalise() -> None:
    """Add the FTSE companies (cohort "ftse") with their reviewed products."""
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    universe = universe[universe["cohort"] != "ftse"]  # re-runnable
    companies = pd.read_csv(MAPPING_DIR / "ftse_companies.csv", keep_default_na=False)
    review = pd.read_csv(MAPPING_DIR / "ftse_review.csv", keep_default_na=False)
    suggested = review["suggestion"].where(~review["product_article"].isin(OVERRIDES),
                                           review["product_article"].map(OVERRIDES))
    decision = review["final"].where(review["final"] != "", suggested).str.lower()
    review.assign(decision=decision).to_csv(MAPPING_DIR / "ftse_decisions.csv", index=False)
    products = review[decision.isin(["keep", "fix"])][["ticker", "product_article"]]
    renamed = old_titles(products["product_article"].tolist()) if len(products) else {}
    rows = []
    for c in companies.itertuples():
        base = {"ticker": c.ticker, "company": c.company, "sector": c.sector, "company_article": c.company_article,
                "company_titles": c.company_titles, "company_from": "", "cohort": "ftse",
                "consumer": c.sub_industry != "Aerospace and Defense"}
        mine = products[products["ticker"] == c.ticker]["product_article"].drop_duplicates()
        for p in mine:
            rows.append({**base, "product_article": p, "product_titles": "|".join([p, *renamed.get(p, [])]),
                         "product_from": ""})
        if mine.empty:
            rows.append({**base, "product_article": "", "product_titles": "", "product_from": ""})
    out = pd.concat([universe, pd.DataFrame(rows)[universe.columns]], ignore_index=True)
    out.to_csv(UNIVERSE_PATH, index=False)
    ftse = out[out["cohort"] == "ftse"]
    print(f"Saved {len(out)} rows: {out['ticker'].nunique()} companies; FTSE: {ftse['ticker'].nunique()} companies, "
          f"{(ftse['product_article'] != '').sum()} product pages")


if __name__ == "__main__":
    main()
