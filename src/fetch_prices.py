"""
Curiosity Index - step 8: share prices and risk factors.

1. Share prices from Yahoo Finance (via yfinance) for every company in the
   universe, plus SPY (an S&P 500 fund) as a simple market benchmark for the
   app. Prices are "adjusted": dividends and splits are built in, so the
   change in price is the full return to a shareholder.
2. Fama-French risk factors from Kenneth French's data library: the market,
   size (SMB), value (HML), profitability (RMW), investment (CMA), momentum
   (Mom) and the risk-free rate (RF). Used later to test for alpha.

Writes to data/processed/:
  prices_daily.csv          - adjusted close, one column per ticker
  volume_daily.csv          - shares traded, one column per ticker
  returns_monthly.csv       - monthly return per ticker (long format)
  ff_factors_monthly.csv    - monthly factors, as decimals (0.01 = 1%)

Run it from the project folder:
    python src/fetch_prices.py
"""

import io
from pathlib import Path
import time
import zipfile

import pandas as pd
import requests
import yfinance as yf

from wiki_api import HEADERS

# Prices start a year before the clickstream (Nov 2017), because momentum
# needs the past 12 months of returns
START = "2016-01-01"
BENCHMARK = "SPY"
UK_BENCHMARK = "CUKX.L"  # iShares FTSE 100, dividends reinvested: the UK equivalent of SPY
FX = "GBPUSD=X"          # dollars per pound, to compare company sizes across markets

FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"
FRENCH_FILES = {
    "F-F_Research_Data_5_Factors_2x3": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"],
    "F-F_Momentum_Factor": ["Mom"],
}

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_DIR = PROJECT_DIR / "data" / "processed"


def fetch_french(name: str) -> pd.DataFrame:
    """Download one Fama-French zip file and return its monthly table."""
    response = requests.get(FRENCH_URL.format(name=name), headers=HEADERS, timeout=60)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")

    # The file has some notes, then the monthly table (rows start with YYYYMM),
    # then an annual table (rows start with YYYY). Keep the monthly rows only.
    lines = text.splitlines()
    header_at = next(i for i, line in enumerate(lines) if line.strip().startswith(","))
    header = [h.strip() for h in lines[header_at].split(",")[1:]]
    rows = []
    for line in lines[header_at + 1 :]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != 6 or not parts[0].isdigit():
            break  # end of the monthly table
        rows.append(parts)
    table = pd.DataFrame([r[1:] for r in rows], columns=header, index=[r[0] for r in rows])
    table.index = pd.to_datetime(table.index, format="%Y%m").strftime("%Y-%m")
    table.columns = [c.replace("Mom   ", "Mom").strip() for c in table.columns]
    return table.astype(float) / 100  # the file is in percent


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH)
    tickers = sorted(universe["ticker"].unique()) + [BENCHMARK]
    if universe["ticker"].str.endswith(".L").any():
        tickers += [UK_BENCHMARK, FX]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Prices
    print(f"Downloading prices for {len(tickers)} tickers from {START} ...")
    data = yf.download(tickers, start=START, auto_adjust=True, progress=False)
    prices = data["Close"][tickers].copy()
    volume = data["Volume"][tickers].copy()

    # Yahoo sometimes fails on a ticker for no reason; retry those one by one,
    # and stop rather than save a company with no prices
    for ticker in prices.columns[prices.isna().all()]:
        for attempt in range(3):
            print(f"  retrying {ticker} ...")
            single = yf.download(ticker, start=START, auto_adjust=True, progress=False)
            if len(single):
                prices[ticker] = single["Close"][ticker]
                volume[ticker] = single["Volume"][ticker]
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"No price data for {ticker} after 3 retries")
    # One calendar for every market: the days the US market was open. London has
    # different holidays; keeping its extra days would put gaps in every US
    # series (and the US days it misses are simply gaps for UK shares)
    us_days = prices[BENCHMARK].notna()
    prices, volume = prices[us_days], volume[us_days]
    prices.index.name = volume.index.name = "date"
    prices.round(4).to_csv(OUT_DIR / "prices_daily.csv")
    volume.to_csv(OUT_DIR / "volume_daily.csv")

    # Monthly return = last price of the month / last price of the month before - 1.
    # The current month is unfinished, so it is left out.
    month_end = prices.resample("ME").last()
    returns = month_end.pct_change(fill_method=None).iloc[1:]
    if returns.index[-1] >= pd.Timestamp.today().normalize():
        returns = returns.iloc[:-1]
    returns.index = returns.index.strftime("%Y-%m")
    returns_long = returns.stack().rename("ret").reset_index()
    returns_long.columns = ["month", "ticker", "ret"]
    returns_long.to_csv(OUT_DIR / "returns_monthly.csv", index=False)

    # 2. Fama-French factors
    print("Downloading Fama-French factors ...")
    factors = pd.concat(
        [fetch_french(name)[cols] for name, cols in FRENCH_FILES.items()], axis=1
    )
    factors = factors.sort_index().loc[START[:7] :].dropna()  # months both files cover
    factors.index.name = "month"
    factors.to_csv(OUT_DIR / "ff_factors_monthly.csv")

    print(f"Prices: {prices.index.min().date()} to {prices.index.max().date()}, "
          f"{prices.shape[1]} tickers")
    print(f"Monthly returns: {returns.index.min()} to {returns.index.max()}")
    print(f"Factors: {factors.index.min()} to {factors.index.max()}, "
          f"columns {list(factors.columns)}")


if __name__ == "__main__":
    main()
