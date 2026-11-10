"""
Curiosity Index - step 9: company size (market capitalisation).

Bigger companies get more Wikipedia attention, so size is a control in the
model. Market cap = share price x number of shares. Yahoo Finance has the
history of shares outstanding, but it needs three clean-ups:

1. Splits: share counts are reported in the units of their date (Apple shows
   about 4.3 bn shares before its 4-for-1 split in Aug 2020 and 17 bn after).
   Every count is converted to today's units, like the prices.
2. Bad points: some dates have two conflicting counts, or a one-off wrong
   value. A point more than 25% away from the median of its neighbours is
   dropped.
3. Bad stretches: for some companies Yahoo switches for a while to a count
   for one share class only, or in the wrong units, then switches back
   (Hershey, Intuitive Surgical, Unilever). A jump of more than 15% that is
   reversed within two years is treated as an error, and the months in
   between are filled in from the months either side. Real events such as
   takeovers paid in shares (AbbVie-Allergan, AMD-Xilinx) are not reversed,
   so they stay.

Companies whose ticker changed also use the counts under their old ticker
(Facebook FB -> META, Square SQ -> XYZ, Sony SNE -> SONY, Michael Kors KORS ->
Capri CPRI, Dr Pepper Snapple DPS -> KDP, Fiat Chrysler FCAU -> Stellantis STLA),
where Yahoo still has them.

Restaurant Brands (QSR) has about 455 million shares counting the partnership
units exchangeable into shares; for long stretches Yahoo reports ordinary
shares only, so counts below 400 million are treated as errors.

The price used is the closing price adjusted for splits only, not dividends,
because market cap is about the actual value of the shares on that day.

Writes data/processed/market_cap_monthly.csv: month, ticker, shares, mcap
(in US dollars, at the last trading day of the month).

Run it from the project folder:
    python src/fetch_market_cap.py
"""

from pathlib import Path
import time

import pandas as pd
import yfinance as yf

START = "2016-01-01"
MAX_GAP = 0.25  # drop share counts more than 25% away from their neighbours
MAX_JUMP = 0.15  # a monthly change this big that later reverses is an error
OLD_TICKERS = {"META": "FB", "XYZ": "SQ", "SONY": "SNE", "CPRI": "KORS", "KDP": "DPS", "STLA": "FCAU"}
MIN_SHARES = {"QSR": 400e6}  # counts below this leave out exchangeable partnership units

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"
OUT_DIR = PROJECT_DIR / "data" / "processed"


def share_counts(symbol: str) -> pd.Series:
    """Raw shares outstanding from Yahoo, as reported."""
    shares = yf.Ticker(symbol).get_shares_full(start=START)
    if shares is None or shares.empty:
        raise RuntimeError(f"No share counts for {symbol}")
    shares.index = pd.to_datetime(shares.index, utc=True).tz_localize(None).normalize()
    return shares.astype(float)


def clean_shares(ticker: yf.Ticker) -> pd.Series:
    """Shares outstanding over time, in today's units, with bad points removed."""
    shares = share_counts(ticker.ticker)
    if ticker.ticker in OLD_TICKERS:  # counts from before the ticker changed
        try:
            old = share_counts(OLD_TICKERS[ticker.ticker])
            shares = pd.concat([old[old.index < shares.index.min()], shares])
        except RuntimeError:
            pass  # Yahoo no longer has the old ticker
    if ticker.ticker in MIN_SHARES:
        shares = shares[shares >= MIN_SHARES[ticker.ticker]]

    # Convert counts from before each split into today's units
    for split_date, ratio in ticker.splits.items():
        split_date = split_date.tz_localize(None).normalize()
        shares[shares.index < split_date] *= ratio

    # Compare each point with the median of the 9 points around it
    shares = shares.sort_index()
    neighbours = shares.rolling(9, center=True, min_periods=1).median()
    shares = shares[(shares / neighbours - 1).abs() <= MAX_GAP]
    return shares.groupby(level=0).median()  # one value per date


def remove_reversals(monthly: pd.Series) -> pd.Series:
    """Blank out stretches between a big jump and the jump that undoes it."""
    monthly = monthly.copy()
    values = monthly.to_numpy()
    i = 1
    while i < len(values):
        before = values[i - 1]
        if abs(values[i] / before - 1) > MAX_JUMP:
            # Does the count come back to within 10% of where it was?
            back = [j for j in range(i + 1, min(i + 25, len(values)))
                    if abs(values[j] / before - 1) < 0.10]
            if back:
                monthly.iloc[i : back[0]] = None
                i = back[0]
                continue
        i += 1
    # Fill the gaps smoothly between the good months either side
    return monthly.interpolate(limit_area="inside")


CURRENCY_PATH = PROJECT_DIR / "data" / "mapping" / "quote_currencies.csv"
FX_TICKERS = {"GBP": "GBPUSD=X", "EUR": "EURUSD=X"}  # dollars per unit


def quote_currencies(tickers: list[str]) -> pd.Series:
    """The currency each London share is quoted in (most in pence, "GBp"; a few in
    dollars or pounds), saved once so the daily update does not ask again."""
    saved = pd.read_csv(CURRENCY_PATH).set_index("ticker")["currency"] if CURRENCY_PATH.exists() else pd.Series(dtype=str)
    todo = [t for t in tickers if t.endswith(".L") and t not in saved.index]
    for t in todo:
        for attempt in range(3):
            try:
                saved.loc[t] = yf.Ticker(t).fast_info["currency"]
                break
            except Exception:
                time.sleep(5)
        else:
            raise RuntimeError(f"No currency for {t}")
    if todo:
        saved.rename("currency").rename_axis("ticker").to_csv(CURRENCY_PATH)
    return saved


def to_dollars(out: pd.DataFrame, currencies: pd.Series) -> pd.DataFrame:
    """Market caps of London shares in dollars, at each month end's exchange rate,
    so companies in both markets can be compared by size."""
    london = out["ticker"].str.endswith(".L")
    if not london.any():
        return out
    fx = yf.download(list(FX_TICKERS.values()), start=START, auto_adjust=False, progress=False)["Close"]
    fx_month = fx.resample("ME").last()
    fx_month.index = fx_month.index.strftime("%Y-%m")
    currency = out["ticker"].map(currencies)
    rate = pd.Series(1.0, index=out.index)
    for code, fx_ticker in FX_TICKERS.items():
        is_code = currency.isin([code, code[:2] + code[2].lower()])  # GBP or GBp (pence)
        rate[is_code] = out.loc[is_code, "month"].map(fx_month[fx_ticker]).values
    rate[currency == "GBp"] /= 100  # pence to pounds
    out = out.copy()
    out.loc[london, "mcap"] = out.loc[london, "mcap"] * rate[london]
    return out.dropna(subset=["mcap"])


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH)
    tickers = sorted(universe["ticker"].unique())

    print(f"Downloading split-adjusted prices for {len(tickers)} tickers ...")
    prices = yf.download(tickers, start=START, auto_adjust=False, progress=False)["Close"]
    # Yahoo sometimes fails on a ticker for no reason; retry those one by one
    for ticker in prices.columns[prices.isna().all()]:
        for attempt in range(3):
            print(f"  retrying prices for {ticker} ...")
            single = yf.download(ticker, start=START, auto_adjust=False, progress=False)
            if len(single):
                prices[ticker] = single["Close"][ticker]
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"No prices for {ticker} after 3 retries")
    month_end = prices.resample("ME").last()
    if month_end.index[-1] >= pd.Timestamp.today().normalize():
        month_end = month_end.iloc[:-1]  # current month not finished

    rows = []
    for ticker in tickers:
        for attempt in range(3):
            try:
                shares = clean_shares(yf.Ticker(ticker))
                break
            except Exception as error:  # Yahoo fails at random sometimes
                print(f"  {ticker}: {error}, retrying ...")
                time.sleep(5)
        else:
            raise RuntimeError(f"No share counts for {ticker} after 3 tries")
        # Last known share count at each month end
        monthly_shares = shares.reindex(shares.index.union(month_end.index)).ffill()
        monthly_shares = remove_reversals(monthly_shares.reindex(month_end.index).dropna())
        monthly_shares = monthly_shares.reindex(month_end.index)
        for date, n in monthly_shares.items():
            rows.append((date.strftime("%Y-%m"), ticker, n, n * month_end.at[date, ticker]))

    out = pd.DataFrame(rows, columns=["month", "ticker", "shares", "mcap"]).dropna()
    out = to_dollars(out, quote_currencies(tickers))
    out.to_csv(OUT_DIR / "market_cap_monthly.csv", index=False)
    print(f"Saved {len(out):,} company-months, {out['month'].min()} to {out['month'].max()}")


if __name__ == "__main__":
    main()
