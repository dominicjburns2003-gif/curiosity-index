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

## Results (added on 10 Nov 2026, after running `src/risk_off.py` once)

Weekly decisions from March 2018 to November 2026, after switching costs.
Sharpe ratio (higher is better), $100 became and worst fall; holding the S&P
500 for comparison. **Main versions (bonds when worried):**

| Signal | Level | Weeks worried | 2018–2021 Sharpe | 2022–2026 Sharpe | Whole: $100 became | Whole: worst fall |
|---|---|---|---|---|---|---|
| Market-wide attention | 80th | 17% | 0.66 | 0.52 | $272 | −23% |
| Market-wide attention | 90th | 8% | 0.72 | 0.37 | $259 | −23% |
| Market-wide attention | 95th | 4% | 0.62 | 0.36 | $250 | −32% |
| Worry pages | 80th | 23% | 0.75 | 0.06 | $188 | −32% |
| Worry pages | 90th | 14% | **1.23** | 0.17 | $258 | −34% |
| Worry pages | 95th | 8% | **1.27** | 0.28 | $294 | −34% |
| *Holding the S&P 500* | | | *0.82* | *0.49* | *$319* | *−32%* |

**Verdict, by the rule fixed in advance: it does not work.** None of the 6
versions has a higher Sharpe ratio than the S&P 500 in both periods (two do
in 2018–2021, one in 2022–2026, none in both). Holding cash instead of bonds
(the check) gives the same verdict.

**What it shows:**

- **The worry pages caught the 2020 crash.** Views of *Recession*, *Stock
  market crash* and the like jumped in late February 2020, and switching to
  bonds then cut the worst fall in 2018–2021 from −32% to −14%, with a much
  better Sharpe ratio (1.27 against 0.82).
- **They failed in 2022.** Worry views soared during the 2022 inflation scare,
  but that year bonds fell together with shares (interest rates rose), so
  switching gave no protection; worry then stayed high while shares recovered
  in 2023, so the strategy missed much of the rebound. Over 2022–2026 every
  version did worse than simply holding the S&P 500.
- **Market-wide attention** to company pages smoothed falls a little (worst
  fall −23% against −32%) but gave up more return than it saved.
- One episode where it worked and one where it did not is not enough to tell
  a real signal from luck; with Wikipedia's overall traffic falling since 2023,
  "worried" weeks have also become rarer.
