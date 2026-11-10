"""
Curiosity Index - step 25: every strategy tested, side by side.

Collects the monthly returns of the main strategies already tested (nothing
new is tested here) and measures each the way a fund factsheet would:

  $100 became             after trading costs
  annual return           compounded
  volatility              annualised standard deviation of monthly returns
  Sharpe ratio            annual return above the risk-free rate (US T-bills,
                          Kenneth French's data), divided by volatility
  worst fall              the largest fall from a previous high (maximum drawdown)
  beta                    how much it moves with the S&P 500 (1 = in step)
  above the average       return above holding the same companies in equal
                          amounts, % a month, with its t

Writes data/processed/strategy_overview.csv.

Run it from the project folder:
    python src/strategy_overview.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{name}.csv")


def measures(net: pd.Series, average: pd.Series, spy: pd.Series, rf: pd.Series) -> dict:
    months = len(net)
    growth = (1 + net).prod()
    annual = growth ** (12 / months) - 1
    vol = net.std() * np.sqrt(12)
    rf_annual = (1 + rf).prod() ** (12 / months) - 1
    path = (1 + net).cumprod()
    worst = (path / path.cummax().clip(lower=1) - 1).min()
    beta = np.cov(net, spy)[0, 1] / spy.var()
    excess = net - average
    return {
        "months": months, "growth_100": 100 * growth, "average_100": 100 * (1 + average).prod(),
        "spy_100": 100 * (1 + spy).prod(), "annual_return": annual, "volatility": vol,
        "sharpe": (annual - rf_annual) / vol, "worst_fall": worst, "beta": beta,
        "excess": excess.mean(), "t_stat": excess.mean() / (excess.std() / np.sqrt(months)),
    }


def main() -> None:
    rf = load("ff_factors_monthly").set_index("month")["RF"]
    rf_next = rf.shift(-1)  # files keyed by the month the picks were made: returns are in the next month

    runs = []  # (name, description, family, verdict note, frame with net/average/spy, keyed by pick month?)
    strategy = load("strategy_monthly")
    a = strategy[strategy["version"] == "A"].set_index("month")
    runs.append(("Top third, first 68 companies", "Ranked by the model, top third, 1 month", "Ranking",
                 a["net"], a["average_company"], a["spy"], True))
    broad = load("broad_monthly")

    def broad_run(detail: str) -> pd.DataFrame:
        return broad[(broad["group"] == "all") & (broad["detail"] == detail)].set_index("month")

    for detail, name, desc in [
        ("equal amounts", "Top third, all companies (today's members)", "Ranked, top third; hindsight in the universe"),
        ("members at the time: top third", "Top third, all companies", "Ranked, top third, index members at the time"),
        ("top 100", "Top 100 (today's members)", "Ranked, top 100; hindsight in the universe"),
        ("members at the time: top 100", "Top 100 (live strategy)", "Ranked, top 100, index members at the time"),
        ("members at the time: top 100 by size", "Top 100, by size", "As above, weighted by market value"),
    ]:
        r = broad_run(detail)
        runs.append((name, desc, "Ranking", r["net"], r["benchmark"], r["spy"], True))

    threshold = load("threshold_monthly").set_index("month")
    runs.append(("Top third + minimum product interest", "Only picks with product views 20%+ above normal",
                 "Ranking", threshold["threshold"], threshold["average_company"], threshold["spy"], True))

    wave = load("wave_followup_monthly")
    for entry, exit_rule, name, desc in [
        (2.0, "normal", "Attention wave (main)", "Buy at 2x usual views, sell when back to normal"),
        (1.5, "half", "Attention wave, earlier entry", "Buy at 1.5x, sell below half the peak"),
        (3.0, "half", "Attention wave, big surges only", "Buy at 3x, sell below half the peak"),
    ]:
        w = wave[(wave["max_hold"] == "no maximum") & (wave["entry"] == entry)
                 & (wave["exit"] == exit_rule)].sort_values("month").set_index("month")
        runs.append((name, desc + "; checked weekly, index members at the time, 2017-2026",
                     "Event", w["net"], w["average_company"], w["spy"], False))

    fund = load("fundamentals_monthly_returns").set_index("month")
    for column, name, desc in [("F", "Fundamentals model (top 100)",
                                "Earnings yield, book-to-market, profitability, asset growth + stock measures; "
                                "SEC accounts as filed, index members at the time"),
                               ("F + A", "Fundamentals + attention (top 100)",
                                "Both sets of measures in one model; index members at the time")]:
        runs.append((name, desc, "Ranking", fund[column], fund["average_company"], fund["spy"], True))

    shorts = load("short_monthly")
    for signal, level, exit_rule, name, desc in [
        ("fade", 0.5, "normal", "Short the fading (main)",
         "Short when views halve, close when back to normal; vs shorting the average company"),
        ("surge", 3.0, "half", "Short the biggest surges (check)",
         "Short at 3x usual views, close below half the peak; vs shorting the average company"),
    ]:
        sh = shorts[(shorts["signal"] == signal) & (shorts["level"].round(3) == round(level, 3))
                    & (shorts["exit"] == exit_rule)].sort_values("month").set_index("month")
        runs.append((name, desc + "; weekly, index members at the time, 2017-2026", "Short",
                     sh["net"], sh["average_company"], sh["spy"], False))

    rows = []
    for name, desc, family, net, average, spy, by_pick_month in runs:
        rates = rf_next if by_pick_month else rf
        first, last = (pd.Period(net.index[0]), pd.Period(net.index[-1]))
        if by_pick_month:  # returns are earned in the month after the pick
            first, last = first + 1, last + 1
        rows.append({"strategy": name, "description": desc, "family": family,
                     "first_month": str(first), "last_month": str(last),
                     **measures(net, average, spy, rates.reindex(net.index).fillna(0))})
    # The S&P 500 itself over the longest period, for reference
    w = wave[(wave["max_hold"] == "no maximum") & (wave["entry"] == 2.0) & (wave["exit"] == "normal")]
    w = w.sort_values("month").set_index("month")
    rows.append({"strategy": "S&P 500 (for reference)", "description": "Buy and hold the index fund",
                 "family": "Reference", "first_month": w.index[0], "last_month": w.index[-1],
                 **measures(w["spy"], w["average_company"], w["spy"], rf.reindex(w.index).fillna(0))})
    r = broad_run("members at the time: top 100")
    rows.append({"strategy": "S&P 500 (for reference)", "description": "Buy and hold the index fund",
                 "family": "Reference", "first_month": str(pd.Period(r.index[0]) + 1),
                 "last_month": str(pd.Period(r.index[-1]) + 1),
                 **measures(r["spy"], r["benchmark"], r["spy"], rf_next.reindex(r.index).fillna(0))})
    out = pd.DataFrame(rows)
    out.to_csv(DATA_DIR / "strategy_overview.csv", index=False)
    show = out.copy()
    for c in ["annual_return", "volatility", "worst_fall"]:
        show[c] = (show[c] * 100).round(1)
    show["excess"] = (show["excess"] * 100).round(2)
    print(show[["strategy", "first_month", "last_month", "growth_100", "average_100", "spy_100",
                "annual_return", "volatility", "sharpe", "worst_fall", "beta", "excess", "t_stat"]]
          .round(2).to_string(index=False))


if __name__ == "__main__":
    main()
