"""
Curiosity Index - step 4: prepare the universe for the hand check.

Takes the automatic checks (data/mapping/universe_check.csv) and adds a
suggested decision and a plain-English reason for every company-product row:

  keep    - passed every check
  drop    - fails a criterion from the brief (delisted, too few views, no clicks,
            or the "product" page is really the company page)
  fix     - fine, but a title needs updating (e.g. the company page was renamed)
  decide  - a judgement call for Dominic (e.g. the click goes to a subsidiary)

Dominic edits the "final" column of data/mapping/universe_review.csv by hand.

Run it from the project folder:
    python src/prepare_review.py
"""

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
MIN_PRODUCT_VIEWS = 3000

# Titles found by hand after the check (the draft had the wrong title)
TITLE_FIXES = {
    "Dove_(brand)": "Dove_(Unilever_brand)",
    "Zyn_(nicotine_pouch)": "Zyn",
    "Ugg_(brand)": "UGG_(brand)",
}

# Old names of company pages that were renamed (found in the page histories).
# Their views must be added to the current title, as with Novo Nordisk.
OLD_COMPANY_TITLES = {
    "Meta_Platforms": "Facebook,_Inc. (Oct 2021)",
    "Amazon_(company)": "Amazon.com (2017, to verify)",
    "Adobe_Inc.": "Adobe_Systems (Oct 2018, to verify)",
    "Block,_Inc.": "Square_(financial_services_company) (Feb 2022)",
    "Royal_Caribbean_Group": "Royal_Caribbean_Cruises_Ltd. (Jul 2020)",
    "Bristol_Myers_Squibb": "Bristol-Myers_Squibb (Aug 2020)",
    "Regeneron_Pharmaceuticals": "Regeneron (Jul 2019)",
    "Hormel_Foods": "Hormel (Oct 2021)",
    "Deckers_Brands": "Deckers_Outdoor_Corporation (Sep 2023)",
    "Tapestry,_Inc.": "Coach,_Inc. (Oct 2017)",
    "Tesla,_Inc.": "Tesla_Motors (Feb 2017, to verify)",
    "Novo_(company)": "Novo_Nordisk (Sep 2026)",
}

# Judgement calls: the product's readers click to a brand/subsidiary page,
# or the listing itself is unusual
DECIDE = {
    ("GOOGL", None): "Product pages link to 'Google', not 'Alphabet Inc.'. "
                     "Track Google as the company page instead?",
    ("BUD", "Bud_Light"): "Article merged into 'Anheuser-Busch brands' (a list page), "
                          "so clicks no longer measure Bud Light alone",
    ("STZ", "Modelo_Especial"): "Article merged into 'Grupo Modelo' (the brewer, owned "
                                "by AB InBev outside the US); STZ only sells it in the US",
    ("NTDOY", None): "Trades over the counter (OTC ADR), not on a US exchange",
    ("SNAP", None): "Listed March 2017; fine since click-through only starts Nov 2017",
}


def suggest(r: pd.Series) -> tuple[str, str]:
    """Return (suggestion, reason) for one company-product row."""
    flags = r["flags"] if isinstance(r["flags"], str) else ""

    if "delisted" in flags:
        return "drop", f"Delisted: last price {r['price_last']} (taken private)"
    if r["product_current"] == r["company_current"]:
        return "drop", "Product page redirects to the company page, so no click-through"
    if r["product_article"] in TITLE_FIXES:
        return "fix", f"Wrong title; use {TITLE_FIXES[r['product_article']]} (recheck views/clicks)"
    if r["product_views_12m"] < MIN_PRODUCT_VIEWS:
        return "drop", f"Too few views ({r['product_views_12m']:,}/month)"
    if r["clicks_to_company"] == 0 and r["ticker"] != "GOOGL":
        return "drop", "No clicks to the company page in Oct 2026"

    for (ticker, product), reason in DECIDE.items():
        if r["ticker"] == ticker and product in (None, r["product_article"]):
            return "decide", reason

    if r["company_current"] in OLD_COMPANY_TITLES and r["company_current"] != "Novo_(company)":
        return "fix", f"Company page renamed; add views of {OLD_COMPANY_TITLES[r['company_current']]}"
    if r["company_current"] != r["company_article"]:
        return "fix", f"Company title is now {r['company_current']}"
    if r["product_current"] != r["product_article"] and r["product_article"] not in ("iPhone", "iPad"):
        return "fix", f"Product title is now {r['product_current']}"
    return "keep", ""


def main() -> None:
    check = pd.read_csv(MAPPING_DIR / "universe_draft_check.csv")
    # Where a title couldn't be resolved, show the title from the draft
    check["product_current"] = check["product_current"].fillna(check["product_article"])
    check[["suggestion", "reason"]] = check.apply(suggest, axis=1, result_type="expand")
    check["final"] = ""  # for Dominic to fill in: keep / drop

    columns = [
        "ticker", "company", "sector", "company_current", "product_current",
        "product_views_12m", "company_views_12m", "clicks_to_company", "conversion_pct",
        "suggestion", "reason", "final",
    ]
    review = check[columns].rename(
        columns={"company_current": "company_article", "product_current": "product_article"}
    )
    review.to_csv(MAPPING_DIR / "universe_review.csv", index=False)

    print(review["suggestion"].value_counts().to_string())
    kept = review[review["suggestion"] != "drop"]
    print(f"\nCompanies with at least one product not dropped: {kept['ticker'].nunique()}")
    gone = sorted(set(review["ticker"]) - set(kept["ticker"]))
    print("Companies that lose every product:", ", ".join(gone))


if __name__ == "__main__":
    main()
