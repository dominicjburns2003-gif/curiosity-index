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

## Results (added on 6 Nov 2026, after running `src/clickthrough_tests.py` once)

6,775 company-months with usable click-through, November 2017 to September
2026 (259 left out as mostly hidden).

**Test 1, volatility** (average monthly slope, standardised; t over months):

| Signal | Slope | t |
|---|---|---|
| Size of the change in click-through | −0.003 | −1.8 |
| Size of the gap from normal | +0.000 | 0.2 |

No sign that click-through predicts bigger moves once current volatility and
the other attention measures are included; if anything, the main signal points
slightly the wrong way.

**Test 2, level** (top third minus bottom third by click-through, next-month
return vs the market, % a month):

| Version | Result | t |
|---|---|---|
| Click-through level | −0.50% | −1.7 |
| Against its sector's median (new) | +0.21% | 0.7 |
| To the end of 2021 (new) | −0.01% | 0.0 |
| 2022 onwards (new) | −0.93% | −2.2 |

The "high click-through does worse" pattern is a **sector effect**: it
disappears (and turns slightly positive) once click-through is compared within
sectors, and it only appears from 2022. Consumer staples (beer, nappies, soap)
have by far the highest click-through (median about 6%, against about 1% for
the other sectors) and underperformed the market by about 1.3% a month from
2022 onwards.

**Conclusion on click-through:** it measures something real (whether readers
connect a product to the company behind it, highest for consumer staples), but
it does not predict returns, volatility or, through the model, anything beyond
product attention.
