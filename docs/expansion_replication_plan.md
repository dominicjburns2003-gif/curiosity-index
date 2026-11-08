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

## Results (added on 8 Nov 2026, after running `src/replication.py` once)

44 new companies (41 without defence); all settings as in the original tests.
Earnings dates were too few on Yahoo for British American Tobacco and
Stellantis, which are left out of test 5.

| Test | Original 68 | New 44 | New, consumer only | All 112 |
|---|---|---|---|---|
| 1. Strategy vs own average, % a month (t) | +0.31 (1.0) | +0.08 (0.4) | +0.18 (0.8) | +0.03 (0.1) |
| 2. Transfer: model from the original 68 | — | +0.14 (0.5) | +0.16 (0.6) | — |
| 3. Long-short, company only | +0.05 (0.1) | +0.74 (1.9) | +0.51 (1.2) | +0.27 (0.7) |
| 3. Long-short, + products | +0.51 (0.9) | +0.60 (1.5) | +0.50 (1.5) | +0.18 (0.5) |
| 3. Long-short, + click-through | +0.23 (0.5) | +0.21 (0.4) | +0.63 (1.4) | +0.47 (1.4) |
| 4. Sort: products ahead of company | +0.46 (1.8) | +0.01 (0.0) | −0.02 (−0.1) | +0.15 (0.8) |
| 4. Sort: rising click-through | +0.44 (1.8) | −0.10 (−0.3) | +0.05 (0.1) | +0.15 (0.8) |
| 5. Beat rate, busiest minus quietest products | −4.0 pts (−2.1) | −4.2 pts (−1.8) | −3.7 pts (−1.4) | −3.9 pts (−2.4) |
| 5. Beat rate, regression on product surge | −3.9 pts (−2.5) | −0.3 pts (−0.1) | +0.1 pts (0.0) | −3.2 pts (−2.1) |

(The original 68's strategy row is the whole period, Jan 2022 – Sep 2026, after the
8 Nov data refresh.)

**Verdicts, using the rule fixed in advance (same sign = replicates; also
|t| ≥ 2 in the new group = strong):**

- **Strategy (test 1): replicates in sign only, and is very small.** The edge
  in the new companies (+0.08% a month) is about a quarter of the original and far
  from significant. Pooled over all 112 it is essentially zero. **The
  original strategy edge is most likely luck.**
- **"Products add to company attention" (test 3): does not replicate.** In the
  new companies, company attention alone did best.
- **The two promising single signals (test 4): do not replicate**, both about
  zero in the new companies.
- **Product buzz before results means fewer beats (test 5): replicates in the
  sort**, with almost the same size (−4.2 vs −4.0 points), though not
  significant on the new companies alone (t −1.8); pooled over 112 companies it
  is significant (t −2.4). The regression version does **not** replicate in the
  new group (t −0.1, and still about zero with the most extreme values capped,
  an exploratory check): in the new companies the difference shows up between
  the busiest and the quietest third, but not as a steady straight-line
  relationship. The finding is therefore weaker than the original test
  suggested.

**Overall:** the one finding that survives a fair test on new companies is
the earnings one: when a company's products draw unusually much attention,
analysts' expectations tend to be set too high. The return-prediction
results from the original 68 do not carry over.

## Addendum: size-weighted strategy for every group (written on 8 Nov 2026, before running it)

The size-weighted version of the strategy (plan addendum in
`docs/strategy_plan.md`) was only run on the original 68. It is now run the
same way for the 44 new companies, the 41 without defence, and all 112: the
same picks as test 1, weighted by market cap with no company above 15%,
compared with all of the group's companies weighted the same way and with the
S&P 500, after costs, January 2022 to the latest month. Reported once,
whatever the result; it is not used to choose anything.

### Size-weighted results (added on 8 Nov 2026, after running once)

| Group | Picks by size vs the group by size | $100 became | Group by size | S&P 500 |
|---|---|---|---|---|
| Original 68 | see `docs/strategy_plan.md` | | | |
| New 44 | −0.10% a month (t −0.3) | $144 | $155 | $179 |
| New, consumer only | −0.10% a month (t −0.3) | $144 | $154 | $179 |
| All 112 | −0.06% a month (t −0.2) | $175 | $186 | $179 |

Weighted by size, the picks slightly trail simply holding the same companies
by size in every new group, and over all 112 they end just below the S&P 500.
The original 68's lead over the S&P 500 does not carry over.
