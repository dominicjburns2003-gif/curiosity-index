# Risk-off: switching from shares to bonds on public worry (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. Idea: suggested to Dominic by his
father.

## Why

Every earlier test asked which companies would beat the others. This one asks
whether attention can tell when to be out of shares altogether. When
investors get nervous ("risk-off"), they usually sell shares and buy
government bonds. If public worry shows up on Wikipedia before or as markets
fall, a strategy could hold shares normally and switch to bonds while worry
is high. Earlier research found that rising views of finance-related
Wikipedia pages came before market falls (Moat, Curme, Avakian, Kenett,
Stanley and Preis, 2013), though later studies found this hard to repeat.

## The two worry signals (weekly)

Each measured over the 7 days ending 2 days before the decision day (Wikipedia
publishes a day or two late), like the attention-wave test:

1. **Market-wide attention:** for each US company's own page, views that week
   against its usual week (the average of the 8 weeks before); the signal is
   the **median** of this ratio across all US companies in the index.
2. **Worry pages:** the combined views of five pages fixed now: *Recession*,
   *Stock market crash*, *Inflation*, *Stagflation*, *Bank run*.

A signal is **"worried"** in a week when its value is above the **80th, 90th
or 95th percentile of all earlier weeks** (from January 2017 to the week
before; only past weeks, so no hindsight).

## The strategy

- Decisions at the close on the last trading day of each week, from March
  2018 (once a year of earlier weeks exists).
- **Not worried:** hold the S&P 500 (SPY). **Worried:** hold US government
  bonds (IEF, iShares 7–10 Year Treasury Bond), both with dividends
  reinvested.
- 0.1% trading cost on each switch.
- Six versions: 2 signals × 3 levels (80th, 90th, 95th percentile).
- **Check, reported alongside:** the same with cash (the US T-bill rate)
  instead of bonds, because in 2022 bonds fell together with shares.

## How it will be judged

- Against simply holding the S&P 500: Sharpe ratio (return above the T-bill
  rate per unit of volatility), annual return, worst fall, $100 became, and
  the share of weeks spent in bonds.
- **It counts as working only if at least 4 of the 6 versions have a higher
  Sharpe ratio than holding the S&P 500 in both 2018–2021 and 2022–2026.**
- Few real risk-off episodes fall in these years (the 2018 sell-off, March
  2020, 2022, the 2023 bank failures), so even a pass would rest on a handful
  of events. Run once and reported whatever the result.
