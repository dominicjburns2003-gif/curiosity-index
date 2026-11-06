# Two final click-through tests (pre-registered)

Written on 6 November 2026, before running either test, and committed so the
date can be checked.

## Why

Click-through (the share of a company's product readers who go on to the
company's own page) did not improve the return model: it overlaps with product
attention. Two questions remain where it could still show something product
attention cannot.

## Data

The monthly panel (`data/processed/panel_monthly.csv`), November 2017 onwards.
Click-through on the row of month t is month t−1's (it is published after the
month ends). Company-months where more than half of the product views had
hidden clicks (Wikipedia removes links with 10 or fewer clicks;
`censored_share` above 0.5) are left out, because their click-through is mostly
guesswork.

## Test 1: does click-through predict volatility?

Attention can signal that a stock is about to move a lot, in either direction.

- **Signal:** the size of the change in click-through, |conversion_change|
  (main), and the size of its gap from normal, |conversion_vs_normal| (second).
- **Outcome:** next month's volatility of daily returns (`vol_next`).
- **Test:** every month, a cross-sectional regression of next month's
  volatility on the signal **and** this month's volatility, company size, and
  the size of the changes in company and product attention (each standardised
  within the month). The slope on the signal is averaged over months
  (Fama–MacBeth) with a t-statistic over months.
- It matters only if it predicts volatility beyond what current volatility and
  the other attention measures already explain.

## Test 2: does the level of click-through predict returns?

**Not fully blind:** a quick check on 6 Nov 2026 suggested companies with high
click-through did slightly worse the next month (rank correlation −0.03,
t ≈ −1.9). This test is therefore partly confirming something already seen,
and will be reported as such. Two parts are new:

- **Signal:** the level of click-through, `conversion`.
- **Outcome:** next month's return minus the market (`ret_vs_mkt_next`).
- **Tests:**
  1. Thirds by click-through each month, top minus bottom, t over months.
  2. **New:** the same with click-through measured against its sector's
     median (5 broad sectors, as in `src/strategy.py`), to see whether it is
     just picking sectors (e.g. beer brands have high click-through).
  3. **New:** test 1 split into two halves (to the end of 2021, and 2022
     onwards), to see whether it holds in both.

Each test is run once and reported whatever the result.
