"""
Curiosity Index - step 5b: add the expansion companies to the universe.

The original 68 companies (finalise_universe.py) were used for every
pre-registered test. The expansion adds 44 more, chosen and checked on
8 Nov 2026 the same way (data/mapping/expansion_review.csv), as an
independent group: the same strategy can be tested on companies it has never
seen, and the original results stay exactly as they were.

Adds two columns to data/mapping/products_to_companies.csv:
  cohort     "original" (the 68) or "expansion" (the 44 new ones)
  consumer   False for companies whose "products" are not sold to consumers
             (defence: fighter jets, bombers, business jets), so results can
             also be run without them

Run it from the project folder, after finalise_universe.py:
    python src/finalise_expansion.py
"""

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAPPING_DIR = PROJECT_DIR / "data" / "mapping"
UNIVERSE_PATH = MAPPING_DIR / "products_to_companies.csv"

# Decisions on 8 Nov 2026 (Claude's recommendations, accepted by Dominic)
DROP_DECIDED = {
    "List_of_Walmart_brands",  # Great Value was merged into a list of many brands
    "Slow_cooker",             # Crock-Pot now redirects to the general appliance article
}
NOT_CONSUMER = {"LMT", "NOC", "GD"}  # defence; kept, but marked

# Old titles of renamed pages, from their move histories since 2016, keeping
# only old titles that still redirect to the page today
OLD_TITLES = {
    "Booking_Holdings": ["The_Priceline_Group"],
    "Calvin_Klein_(fashion_house)": ["Calvin_Klein_(company)", "Calvin_Klein_Inc."],
    "Campbell's": ["Campbell_Soup_Company"],
    "Capri_Holdings": ["Michael_Kors_(brand)"],
    "Carnival_Corporation": ["Carnival_Corporation_&_plc"],
    "Cisco": ["Cisco_Systems"],
    "Conagra_Brands": ["ConAgra_Brands", "ConAgra_Foods"],
    "Coty": ["Coty,_Inc.", "Coty_(beauty_company)", "Coty_Inc."],
    "Dine_Brands": ["DineEquity", "Dine_Brands_Global"],
    "Expedia": ["Expedia_(website)"],
    "Expedia_Group": ["Expedia,_Inc."],
    "Goldfish_(cracker)": ["Goldfish_(snack)"],
    "Hilton_Worldwide": ["Hilton_Inc.", "Hilton_Worldwide_Holdings"],
    "IHOP": ["International_House_Of_Pancakes", "International_House_of_Pancakes"],
    "Indian_Motorcycle": ["Indian_Motocycle_Manufacturing_Company", "Indian_Motorcycle_Manufacturing_Company",
                          "Indian_Motorcycle_Manufacturing_Company_(Company)"],
    "Jimmy_Choo_(fashion_house)": ["Jimmy_Choo_(company)", "Jimmy_Choo_Ltd"],
    "Kayak_(company)": ["Kayak.com"],
    "Keurig_Dr_Pepper": ["Keurig_Green_Mountain"],
    "Mailchimp": ["MailChimp"],
    "Marlboro": ["Marlboro_(cigarette)"],
    "News_Corp": ["News_Corp_(2013–present)"],
    "Northrop_B-2_Spirit": ["Northrop_Grumman_B-2_Spirit"],
    "Northrop_Grumman_B-21_Raider": ["Northrop_Grumman_B-21"],
    "PVH_Corp.": ["PVH_(company)"],
    "Peacock_(streaming_service)": ["Peacock_(service)"],
    "Pebbles_(cereal)": ["Pebbles_cereal"],
    "Polaris_Inc.": ["Polaris_Industries"],
    "Popeyes": ["Popeyes_Louisiana_Kitchen"],
    "Salesforce": ["Salesforce.com"],
    "Stranger_Things": ["Stranger_Things_(TV_series)"],
    "V8_(drink)": ["V8_(beverage)"],
    "Webex": ["Cisco_Webex", "WebEx"],
    "Wordle": ["Wordle_(online_game)", "Wordle_(video_game)", "Wordle_(word_game)"],
    "Xfinity": ["Comcast_Cable"],
}

# Company series that only start later: Stellantis was formed by a merger in
# January 2021 (the Fiat Chrysler page is a separate article); Norwegian Cruise
# Line Holdings had no page of its own before January 2019 (it was covered in
# the Norwegian Cruise Line article, its product), as with Meta and Facebook
COMPANY_FROM = {"STLA": "2021-01", "NCLH": "2019-01"}


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    if "cohort" in universe.columns:  # re-running: start again from the original 68
        universe = universe[universe["cohort"] != "expansion"].drop(columns=["cohort", "consumer"])
    universe = universe.copy()
    universe["cohort"] = "original"
    universe["consumer"] = True

    review = pd.read_csv(MAPPING_DIR / "expansion_review.csv")
    new = review[(review["suggestion"] != "drop") & ~review["product_article"].isin(DROP_DECIDED)].copy()
    new["company_titles"] = ["|".join([c] + OLD_TITLES.get(c, [])) for c in new["company_article"]]
    new["company_from"] = new["ticker"].map(COMPANY_FROM).fillna("")
    new["product_titles"] = ["|".join([p] + OLD_TITLES.get(p, [])) for p in new["product_article"]]
    new["product_from"] = ""
    new["cohort"] = "expansion"
    new["consumer"] = ~new["ticker"].isin(NOT_CONSUMER)

    columns = list(universe.columns)
    combined = pd.concat([universe, new[columns]]).sort_values(["cohort", "sector", "ticker", "product_article"],
                                                                ascending=[False, True, True, True])
    combined.to_csv(UNIVERSE_PATH, index=False)
    for cohort, rows in combined.groupby("cohort", sort=False):
        print(f"{cohort}: {rows['ticker'].nunique()} companies, {len(rows)} products")


if __name__ == "__main__":
    main()
