"""
Curiosity Index - step 17: the live track record.

strategy.py adds each month's picks to live_picks_log.csv as soon as they can
be made, before the month's returns exist, and never changes them. This script
follows those recorded picks day by day:

  - each month, the recorded picks are bought in equal amounts at the close
    on the first trading day after the day they were recorded, and held to the
    last close of that month (or to the latest close, while the month is
    still running). Picks can only be made once the previous month's data is
    complete, a day or two into the month, and the daily update runs after the
    US market close, so the next close is the first price anyone acting on the
    picks could actually trade at;
  - if a month has a second record (the switch to all companies, recorded on
    9 Nov 2026), the first picks are held until the close at which the second
    ones are bought, and the second from then to the end of the month;
  - compared with buying, in equal amounts, all the companies the picks were
    chosen from (the original 68 until 10 Nov 2026, all companies from then),
    and with the S&P 500;
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
    universe = pd.read_csv(UNIVERSE_PATH)
    original_68 = sorted(universe.loc[universe["cohort"] == "original", "ticker"].unique())
    all_112 = sorted(universe.loc[universe["cohort"].isin(["original", "expansion"]), "ticker"].unique())
    everyone = sorted(universe["ticker"].unique())

    def chosen_from(version: str) -> list[str]:
        if "all companies" in version:
            return everyone
        return all_112 if "all 112" in version else original_68
    last_close = prices.index.max()

    value = {"strategy": 100.0, "average_company": 100.0, "spy": 100.0}
    daily, monthly, previous = [], [], set()
    days = prices.index
    segments = list(log.groupby(["month", "recorded_on"], sort=True))
    for i, ((chosen_month, recorded_on), picks) in enumerate(segments):
        held_month = pd.Period(chosen_month, freq="M") + 1
        recorded = pd.Timestamp(recorded_on)
        after = days[days > recorded]
        if after.empty:
            continue  # no trading day since the picks were recorded
        start = after[0]  # bought at the close on the next trading day
        end = days[days <= held_month.end_time].max()
        # A later record for the same month takes over at the close it is bought at
        if i + 1 < len(segments) and segments[i + 1][0][0] == chosen_month:
            later = days[days > pd.Timestamp(segments[i + 1][0][1])]
            if len(later):
                end = min(end, later[0])
        if end <= start:
            continue  # no full trading day held yet

        tickers = list(picks["ticker"])
        turnover = len(set(tickers) - previous) / len(tickers) * (2 if previous else 1)
        cost = COST_PER_TRADE * turnover  # first month: buying only; then selling and buying
        paths = {
            "strategy": growth(prices, tickers, start, end) * (1 - cost),
            # Compared with the companies the picks were chosen from that month:
            # the original 68 until November 2026, all 112 from December
            "average_company": growth(prices, chosen_from(str(picks["version"].iloc[0])), start, end),
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
            "complete": pd.Timestamp.today().normalize() > held_month.end_time or end < days[days <= held_month.end_time].max(),
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
