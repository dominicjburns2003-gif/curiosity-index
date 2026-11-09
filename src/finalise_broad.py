"""
Curiosity Index - step 22c: add the broad universe to the mapping.

Appends the 435 new S&P 500 and Nasdaq-100 companies (cohort "broad") to
data/mapping/products_to_companies.csv, leaving the 112 hand-checked
companies exactly as they are (docs/broad_universe_plan.md):

  - one row per reviewed product page (data/mapping/broad_draft_review.csv,
    rows whose "final" decision is keep or fix), with earlier titles of
    renamed product pages added up;
  - one row with no product page for every new company without one, so it is
    still tracked by its company page.

Re-runnable: it always starts again from the 112 ("original" and "expansion").

Run it from the project folder:
    python src/finalise_broad.py                    # with the reviewed products
    python src/finalise_broad.py --companies-only   # company pages only, before the review
"""

from pathlib import Path
import sys

import pandas as pd

from build_broad_universe import old_titles

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
UNIVERSE_PATH = MAPPING_DIR / "products_to_companies.csv"
REVIEW_PATH = MAPPING_DIR / "broad_review.csv"

# Decisions on the review, 9 Nov 2026 (Claude's recommendations, for Dominic to
# confirm), by the same rules as for the 112: a product page must be about a
# product or brand people look up, not a market index, an event, a place, a
# generic technology or a business unit that is really a company of its own
OVERRIDES = {
    "Mason_jar": "drop",                                 # generic jar, not Ball's
    "Phoenix_Open": "drop",                              # a sponsored golf event
    "EUV_lithography": "drop",                           # a technology, used by several firms
    "Grupo_Modelo": "drop",                              # AB InBev's brewer outside the US
    "2024_CrowdStrike-related_IT_outages": "drop",       # an event
    "S&P_500": "drop", "Nasdaq-100": "drop", "Nasdaq_Composite": "drop", "MSCI_World": "drop",
    "New_York_Stock_Exchange": "drop", "Chicago_Mercantile_Exchange": "drop",  # read for markets, not the firm
    ".com": "drop",                                      # a web domain used by everyone
    "Vogtle_Electric_Generating_Plant": "drop", "Grasberg_mine": "drop",       # places
    "Newport_News_Shipbuilding": "drop", "Ingalls_Shipbuilding": "drop",       # shipyards (business units)
}


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    universe = universe[universe["cohort"].isin(["original", "expansion"])]
    companies = pd.read_csv(MAPPING_DIR / "broad_companies.csv", keep_default_na=False)
    # A company with no Wikipedia page of its own cannot be tracked (Insulet, PODD)
    no_page = companies["qid"] == ""
    if no_page.any():
        print(f"Left out, no Wikipedia page: {', '.join(companies.loc[no_page, 'ticker'])}")
    companies = companies[~no_page]

    products = pd.DataFrame(columns=["ticker", "product_article"])
    if "--companies-only" not in sys.argv:
        review = pd.read_csv(REVIEW_PATH, keep_default_na=False)
        # product_article is already the current title (redirects followed by prepare_review.py)
        suggested = review["suggestion"].where(~review["product_article"].isin(OVERRIDES),
                                               review["product_article"].map(OVERRIDES))
        decision = review["final"].where(review["final"] != "", suggested).str.lower()
        if (review["final"] == "").any():
            print(f"Note: {(review['final'] == '').sum()} rows have no final decision; using the suggestion")
        review.assign(decision=decision).to_csv(MAPPING_DIR / "broad_decisions.csv", index=False)
        review = review[decision.isin(["keep", "fix"])]
        products = review[["ticker", "product_article"]]

    renamed = old_titles(products["product_article"].tolist()) if len(products) else {}
    rows = []
    for c in companies.itertuples():
        base = {"ticker": c.ticker, "company": c.company, "sector": c.sector,
                "company_article": c.company_article, "company_titles": c.company_titles, "company_from": "",
                "cohort": "broad", "consumer": c.sub_industry != "Aerospace & Defense"}
        mine = products[products["ticker"] == c.ticker]["product_article"].drop_duplicates()
        for product in mine:
            rows.append({**base, "product_article": product,
                         "product_titles": "|".join([product, *renamed.get(product, [])]), "product_from": ""})
        if mine.empty:
            rows.append({**base, "product_article": "", "product_titles": "", "product_from": ""})
    out = pd.concat([universe, pd.DataFrame(rows)[universe.columns]], ignore_index=True)
    out.to_csv(UNIVERSE_PATH, index=False)
    broad = out[out["cohort"] == "broad"]
    print(f"Saved {len(out)} rows: {out['ticker'].nunique()} companies, of which {broad['ticker'].nunique()} "
          f"broad ({(broad['product_article'] != '').sum()} product pages for "
          f"{broad.loc[broad['product_article'] != '', 'ticker'].nunique()} companies)")


if __name__ == "__main__":
    main()
