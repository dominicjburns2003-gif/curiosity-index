"""
Curiosity Index - step 17: the live track record.

strategy.py adds each month's picks to live_picks_log.csv as soon as they can
be made, before the month's returns exist, and never changes them. This script
follows those recorded picks day by day:

  - each month, the recorded picks are bought in equal amounts at the close
    on the day they were recorded (the next trading day if markets were shut),
    and held to the last close of that month (or to the latest close, while
    the month is still running). Picks can only be made once the previous
    month's data is complete, a day or two into the month, so buying any
    earlier would use returns that had already happened;
  - compared with buying all 68 companies in equal amounts, and the S&P 500;
  - trading costs of 0.1% of the amount traded are taken at each change.

Writes to data/processed/:
  track_record_daily.csv     value of $100 by day, strategy and benchmarks
  track_record_monthly.csv   one row per month held, complete or in progress

Run it from the project folder:
    python src/track_record.py
"""

from pathlib import Path

import pandas as pd

COST_PER_TRADE = 0.001

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
UNIVERSE_PATH = PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv"


def growth(prices: pd.DataFrame, tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Value of 1 invested in equal amounts at the close on `start`, each day to `end`."""
    window = prices.loc[start:end, tickers].dropna(axis=1, subset=[start])
    return (window / window.loc[start]).mean(axis=1)


def main() -> None:
    log = pd.read_csv(DATA_DIR / "live_picks_log.csv")
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    companies = sorted(pd.read_csv(UNIVERSE_PATH)["ticker"].unique())
    last_close = prices.index.max()

    value = {"strategy": 100.0, "average_company": 100.0, "spy": 100.0}
    daily, monthly, previous = [], [], set()
    for chosen_month, picks in log.groupby("month"):
        held_month = pd.Period(chosen_month, freq="M") + 1
        days = prices.index
        recorded = pd.Timestamp(picks["recorded_on"].iloc[0])
        on_or_after = days[days >= recorded]
        if on_or_after.empty:
            continue  # no close since the picks were recorded
        start = on_or_after[0]  # bought at the close on the day they were recorded
        end = days[days <= held_month.end_time].max()
        if end <= start:
            continue  # no full trading day held yet

        tickers = list(picks["ticker"])
        turnover = len(set(tickers) - previous) / len(tickers) * (2 if previous else 1)
        cost = COST_PER_TRADE * turnover  # first month: buying only; then selling and buying
        paths = {
            "strategy": growth(prices, tickers, start, end) * (1 - cost),
            "average_company": growth(prices, companies, start, end),
            "spy": growth(prices, ["SPY"], start, end),
        }
        if not daily:
            daily.append({"date": start, **value})  # $100 at the first purchase
        for day in paths["strategy"].index[1:]:  # the start is the previous month's last day
            daily.append({"date": day, **{k: value[k] * paths[k][day] for k in paths}})
        monthly.append({
            "month_held": str(held_month), "chosen_at_end_of": chosen_month,
            "recorded_on": picks["recorded_on"].iloc[0], "version": picks["version"].iloc[0],
            "picks": len(tickers), "through": end.date(),
            "complete": pd.Timestamp.today().normalize() > held_month.end_time,
            **{k: paths[k].iloc[-1] - 1 for k in paths},
        })
        value = {k: value[k] * paths[k].iloc[-1] for k in paths}
        previous = set(tickers)

    # Column names are written even before the first full day, so the app can read the files
    pd.DataFrame(daily, columns=["date", "strategy", "average_company", "spy"]).to_csv(
        DATA_DIR / "track_record_daily.csv", index=False)
    pd.DataFrame(monthly, columns=["month_held", "chosen_at_end_of", "recorded_on", "version", "picks",
                                   "through", "complete", "strategy", "average_company", "spy"]).to_csv(
        DATA_DIR / "track_record_monthly.csv", index=False)
    if not monthly:
        print("No full trading day held yet since the first picks were recorded")
    for row in monthly:
        status = "complete" if row["complete"] else f"in progress, to {row['through']}"
        print(f"{row['month_held']} ({status}): strategy {row['strategy']:+.2%}, "
              f"average company {row['average_company']:+.2%}, S&P 500 {row['spy']:+.2%}")


if __name__ == "__main__":
    main()
