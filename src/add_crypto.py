"""
Curiosity Index - four cryptocurrencies, tracked alongside the stocks.

Adds Bitcoin, Ethereum, Solana and Cardano (cohort "crypto") to
data/mapping/products_to_companies.csv, tracked by their own Wikipedia page
and their price in dollars (Yahoo: BTC-USD, ETH-USD, SOL-USD, ADA-USD). They
appear in the Explorer, but are kept out of every stock test, the live
strategy and the track record. Earlier titles of renamed pages are added up.
Re-runnable.

Run it from the project folder:
    python src/add_crypto.py
"""

from pathlib import Path

import pandas as pd

from build_broad_universe import old_titles

UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "data" / "mapping" / "products_to_companies.csv"
CRYPTO = {  # Yahoo ticker: (name, Wikipedia page)
    "BTC-USD": ("Bitcoin", "Bitcoin"),
    "ETH-USD": ("Ethereum", "Ethereum"),
    "SOL-USD": ("Solana", "Solana_(blockchain_platform)"),
    "ADA-USD": ("Cardano", "Cardano_(blockchain_platform)"),
}


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH, keep_default_na=False)
    universe = universe[universe["cohort"] != "crypto"]
    renamed = old_titles([page for _, page in CRYPTO.values()])
    rows = [{"ticker": t, "company": name, "sector": "Cryptocurrency", "company_article": page,
             "company_titles": "|".join([page, *renamed[page]]), "company_from": "", "product_article": "",
             "product_titles": "", "product_from": "", "cohort": "crypto", "consumer": False}
            for t, (name, page) in CRYPTO.items()]
    out = pd.concat([universe, pd.DataFrame(rows)[universe.columns]], ignore_index=True)
    out.to_csv(UNIVERSE_PATH, index=False)
    print(f"Saved {len(out)} rows; {len(rows)} cryptocurrencies")


if __name__ == "__main__":
    main()
