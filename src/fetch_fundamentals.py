"""
Curiosity Index - step 32a: company accounts from SEC EDGAR, point in time.

For every US company in the index, the figures needed for the fundamentals
test (docs/fundamentals_plan.md) from its annual reports (10-K), each with
the date it was filed, so later steps only use accounts that had been
published by then. Where the same year's figure appears in several filings
(e.g. as last year's comparison in the next report, or after a restatement),
the one filed first is kept.

The SEC asks automated users to give a contact in every request
(https://www.sec.gov/os/accessing-edgar-data); the contact below is used
only for requests to sec.gov.

Writes data/processed/fundamentals_annual.csv:
  ticker, item, period_end, value, filed

Run it from the project folder:
    python src/fetch_fundamentals.py
"""

from pathlib import Path
import time

import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_PATH = DATA_DIR / "fundamentals_annual.csv"

SEC_HEADERS = {"User-Agent": "CuriosityIndex student project Dominic Burns dominicjburns2003@gmail.com"}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# Each item and the US-GAAP tags it may be reported under, in order of preference
ITEMS = {
    "net_income": ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "gross_profit": ["GrossProfit"],
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "assets": ["Assets"],
}
FLOWS = {"net_income", "gross_profit", "revenue", "cost_of_revenue"}  # measured over a year, not at a date


def cik_map() -> dict[str, int]:
    data = requests.get(TICKERS_URL, headers=SEC_HEADERS, timeout=30).json()
    return {row["ticker"].replace(".", "-").upper(): row["cik_str"] for row in data.values()}


def annual_figures(facts: dict, ticker: str) -> list[dict]:
    gaap = facts.get("facts", {}).get("us-gaap", {})
    rows = []
    for item, tags in ITEMS.items():
        for tag in tags:
            entries = gaap.get(tag, {}).get("units", {}).get("USD", [])
            kept = []
            for e in entries:
                if not str(e.get("form", "")).startswith("10-K"):
                    continue
                if item in FLOWS:  # a full year: roughly 12 months between start and end
                    if "start" not in e:
                        continue
                    days = (pd.Timestamp(e["end"]) - pd.Timestamp(e["start"])).days
                    if not 340 <= days <= 380:
                        continue
                kept.append({"ticker": ticker, "item": item, "period_end": e["end"], "value": e["val"],
                             "filed": e["filed"]})
            if kept:
                rows += kept
                break  # the first tag with annual figures is used for this item
    return rows


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    tickers = sorted(universe.loc[universe["cohort"] != "ftse", "ticker"].unique())
    ciks = cik_map()
    rows, missing = [], []
    for i, ticker in enumerate(tickers, start=1):
        cik = ciks.get(ticker) or ciks.get(ticker.replace("-", ""))
        if cik is None:
            missing.append(ticker)
            continue
        for attempt in range(3):
            try:
                response = requests.get(FACTS_URL.format(cik=cik), headers=SEC_HEADERS, timeout=60)
                break
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
        else:
            missing.append(ticker)
            continue
        if response.status_code == 200:
            rows += annual_figures(response.json(), ticker)
        else:
            missing.append(ticker)
        time.sleep(0.15)  # the SEC allows up to 10 requests a second
        if i % 100 == 0:
            print(f"  {i}/{len(tickers)} done", flush=True)
    out = pd.DataFrame(rows)
    # The figure as first filed, for each company, item and period
    out = out.sort_values("filed").drop_duplicates(["ticker", "item", "period_end"], keep="first")
    out = out.sort_values(["ticker", "item", "period_end"])
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out):,} annual figures for {out['ticker'].nunique()} of {len(tickers)} companies")
    print(f"No SEC figures (not found, or not filing US-GAAP accounts): {len(missing)}: {missing[:40]}")


if __name__ == "__main__":
    main()
