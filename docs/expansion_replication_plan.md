# Replication on new companies (pre-registered)

Written on 8 November 2026, before any results for the new companies were
computed (their data was still downloading), and committed so the date can be
checked.

## Why

Every test so far used the same 68 companies, and several were designed after
looking at those companies' data. The fairest check of whether the findings
are real is to run **exactly the same tests on companies they have never
seen**. On 8 Nov 2026, 44 new US-listed companies with 92 product pages were
added (`data/mapping/expansion_review.csv`), chosen and checked by the same
rules as the original 68 (`cohort = "expansion"` in
`data/mapping/products_to_companies.csv`). Three of them (Lockheed Martin,
Northrop Grumman, General Dynamics) are defence companies whose "products"
are not sold to consumers; they are marked `consumer = False`.

## What is replicated

All settings are copied unchanged from the original tests: the same features,
the same tree-model settings, 3 groups, 0.1% trading costs, the same periods.

1. **The strategy (main test).** Version A from `docs/strategy_plan.md`: the
   tree model (product-attention version) trained walk-forward **on the new
   companies only** (first test year 2022, retrained each January), buying the
   top third each month in equal amounts. Compared with the equal-weighted
   average of the new companies, after costs, January 2022 to the latest month.
2. **Transfer:** the same, but the model trained on the original 68 is used to
   score the new companies, to see whether what it learned carries over.
3. **The long-short research comparison:** company only, + products,
   + click-through, on the new companies.
4. **The single-signal sorts** (the six signals in `src/backtest.py`), on the
   new companies, whole history.
5. **The earnings test** from `docs/earnings_test_plan.md`, on the new
   companies: product attention before results and the beat rate.

Each is also shown **without the three defence companies**, and for **all 112
companies together**.

## How it will be judged

- A finding **replicates** if it has the same sign in the new companies. It is
  **strong** if it is also statistically significant there (|t| of 2 or more).
- The two findings that matter most: the strategy beating its own average
  (test 1) and product buzz before results meaning fewer beats (test 5).
- Everything is run once and reported whatever the result. The original
  68-company results are not changed.
