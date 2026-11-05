"""
Curiosity Index - step 5: turn the reviewed draft into the final universe.

Applies the decisions from the hand check (data/mapping/universe_review.csv)
and the title fixes, and writes the file every later script uses:

    data/mapping/products_to_companies.csv

One row per company-product pair, with:
  company_titles   - every title the company page has had, separated by "|"
                     (views of all of them are added up, as for Novo Nordisk)
  company_from     - first month with a usable company series (blank = from the start)

Run it from the project folder:
    python src/finalise_universe.py
"""

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"

# ---- Decisions from the hand check (5 Nov 2026) -----------------------------

# The "decide" rows: Dominic accepted the suggested picks
DROP_DECIDED = {("BUD", "Anheuser-Busch_brands"), ("STZ", "Grupo_Modelo")}
COMPANY_PAGE_OVERRIDE = {"GOOGL": "Google"}  # consumers click to Google, not Alphabet

# Correct titles for products that were wrong in the draft
PRODUCT_FIXES = {
    "Dove_(disambiguation)": "Dove_(Unilever_brand)",
    "Zyn_(nicotine_pouch)": "Zyn",
    "Ugg_(brand)": "UGG_(brand)",
}

# Old titles of renamed company pages, checked against the page histories and
# the month views moved from the old title to the new one
OLD_COMPANY_TITLES = {
    "Meta_Platforms": ["Facebook,_Inc."],             # Oct 2021
    "Amazon_(company)": ["Amazon.com"],               # Oct 2017
    "Adobe_Inc.": ["Adobe_Systems"],                  # Oct 2018
    "Block,_Inc.": ["Square_(financial_services_company)"],  # Feb 2022
    "Royal_Caribbean_Group": ["Royal_Caribbean_Cruises_Ltd."],  # Jul 2020
    "Bristol_Myers_Squibb": ["Bristol-Myers_Squibb"],  # Aug 2020
    "Regeneron_Pharmaceuticals": ["Regeneron"],       # Jul 2019
    "Hormel_Foods": ["Hormel"],                       # Oct 2021
    "Deckers_Brands": ["Deckers_Outdoor_Corporation"],  # Sep 2023
    "Tapestry,_Inc.": ["Coach,_Inc."],                # Oct 2017
    "Tesla,_Inc.": ["Tesla_Motors"],                  # Feb 2017
    "Novo_(company)": ["Novo_Nordisk"],               # Sep 2026
}

# Company series that only become meaningful later: before Dec 2019 Facebook the
# company and Facebook the product shared one article, so there is no clean
# company-attention series for Meta before then
COMPANY_FROM = {"META": "2019-12"}


def main() -> None:
    review = pd.read_csv(MAPPING_DIR / "universe_review.csv")

    # Fill in the decision column: drop what was suggested or decided, keep the rest
    decided = pd.Series(
        [(t, p) in DROP_DECIDED for t, p in zip(review["ticker"], review["product_article"])],
        index=review.index,
    )
    dropped = review["suggestion"].eq("drop") | decided
    review["final"] = ["drop" if d else "keep" for d in dropped]
    review.to_csv(MAPPING_DIR / "universe_review.csv", index=False)

    final = review[review["final"] == "keep"].copy()
    final["company_article"] = final["ticker"].map(COMPANY_PAGE_OVERRIDE).fillna(final["company_article"])
    final["product_article"] = final["product_article"].replace(PRODUCT_FIXES)
    final["company_titles"] = [
        "|".join([c] + OLD_COMPANY_TITLES.get(c, [])) for c in final["company_article"]
    ]
    final["company_from"] = final["ticker"].map(COMPANY_FROM).fillna("")

    columns = ["ticker", "company", "sector", "company_article", "company_titles",
               "company_from", "product_article"]
    final = final[columns].sort_values(["sector", "ticker", "product_article"])
    final.to_csv(MAPPING_DIR / "products_to_companies.csv", index=False)

    print(f"Final universe: {final['ticker'].nunique()} companies, {len(final)} products")
    print(final.groupby("sector")["ticker"].nunique().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
