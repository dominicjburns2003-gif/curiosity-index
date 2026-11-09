# Broad universe: S&P 500 and Nasdaq-100 (pre-registered)

Written on 9 November 2026, before any returns, signals or test results for
the new companies were computed (their page views and prices had not been
downloaded), and committed so the date can be checked.

## Why

112 companies is a small set: the tests have little power, and the app can
only follow companies chosen by hand. This expansion adds every company in
the S&P 500 and the Nasdaq-100, so that (a) the findings get a third, much
larger test on companies they were not designed on, and (b) the app covers
the large US companies an investor would actually look at.

## The universe

- **Companies:** the S&P 500 as listed on Wikipedia on 9 Nov 2026
  (`List_of_S&P_500_companies`), plus the 15 Nasdaq-100 companies not in it.
  Share classes (GOOG/GOOGL, FOX/FOXA, NWS/NWSA) count as one company. 79 of
  them are already among the 112; the other **435** are new
  (`cohort = "broad"`). Built by `src/build_broad_universe.py`.
- **Company pages:** the page the list links to, after redirects. Earlier
  titles of renamed pages (found in the page history, still redirecting to
  the page today) are added up, as for the 112.
- **Product pages:** drafted from general knowledge
  (`src/draft_broad_products.py`), then checked automatically
  (`src/check_universe.py`: page exists, redirects, at least 3,000 views a
  month over the last 12 months, clicks to the company page, prices) and
  reviewed by hand, by the same rules as the 112. An automatic search of
  Wikidata was tried first and rejected before any data was downloaded: about
  a third of its links were wrong (other companies' products, products sold
  years ago, weapons systems).
- **Companies with no product page** (most banks, insurers, utilities,
  property trusts and industrial suppliers) are still included, tracked by
  their company page alone: their product measures are missing, and the
  model treats missing values as missing (no value is made up).
- The 112 hand-checked companies, their products and all their results are
  not changed.

**Known bias, accepted in advance:** this is today's index membership applied
back to 2017, so companies that left the index (often after falling) are
missing and the group's average return is flattered. The tests compare
companies within the same group, which this affects much less, but returns
against the S&P 500 should be read with this in mind.

## What is tested

Every setting is copied unchanged from the earlier tests (the same seven
features, tree-model settings, top third, 0.1% trading costs, walk-forward
from 2022, retrained each January), for three groups:

- **broad new:** the 435 new companies;
- **broad new, with products:** those of them with at least one product page;
- **all:** every company (the 112 and the 435 together).

1. **The strategy:** version A trained on the group, top third in equal
   amounts, against the group's equal-weighted average, after costs; and the
   same picks weighted by size against the group weighted by size.
2. **Long-short:** company only, + products, + click-through.
3. **The single-signal sorts** (the six signals in `src/backtest.py`).
4. **The earnings test** (`docs/earnings_test_plan.md`): product attention
   before results and the beat rate (companies with product pages only).
5. **Click-through (Dominic's question, 9 Nov 2026):** does adding
   click-through improve the long-only strategy? Version A with the
   click-through features added (the `clicks` feature set of
   `src/walk_forward.py`), against version A, on "all" companies with product
   pages: the monthly difference in return, with its t, after costs.

## How it will be judged

- A finding **replicates** if it has the same sign in "broad new"; it is
  **strong** if |t| is 2 or more there.
- The findings that matter most: the strategy beating its own average (1),
  product buzz before results meaning fewer beats (4), and click-through
  adding to product attention (2 and 5).
- Everything is run once and reported whatever the result.
- The live strategy is **not** changed by this. Switching it to the broad
  universe would be a separate decision, recorded in `docs/strategy_plan.md`
  before the month it applies to.

## Addendum: universe as built, and timing (written on 9 Nov 2026, before running any test)

- **As built:** 547 companies: the 112, plus 435 new. 72 of the new companies
  have product pages (136 pages, after the checks and the review in
  `data/mapping/broad_decisions.csv`, confirmed by Dominic); the other 363
  are tracked by their company page alone. Ferrovial has no price history on
  Yahoo and so drops out of every test.
- **Timing:** the click-through history for the new companies' pages needs
  every monthly clickstream file again (about 50 GB), which takes a night. So
  the tests are run in two parts, each **once**: tonight, everything that
  does not use click-through (tests 1, 3, 4 and the company-only and
  + products versions of test 2); once the download is complete, the
  + click-through version of test 2 and test 5. Nothing in the first part is
  changed after the second.

## Results, part 1 (added on 9 Nov 2026, after running `src/broad_tests.py` once)

January 2022 to October 2026 (57 months) for the strategy and long-short;
2017 to 2026 for the sorts; 36 quarters for earnings. Per cent a month (t).
Insulet (PODD) turned out to have no Wikipedia page; it was in this run with
no attention data, and is left out of the universe from now on.

| Test | Original 68 (for comparison) | Broad new (435) | Broad new, with products (72) | All (547) |
|---|---|---|---|---|
| 1. Strategy vs own average, equal amounts | +0.31 (1.0) | **+0.28 (2.2)** | −0.36 (−1.7) | +0.28 (2.0) |
| 1. Strategy vs own average, by size | | +0.33 (1.4) | −0.29 (−0.9) | +0.04 (0.1) |
| 2. Long-short, company only | +0.05 (0.1) | **+0.55 (2.5)** | −0.78 (−2.0) | +0.35 (1.6) |
| 2. Long-short, + products | +0.51 (0.9) | **+0.52 (2.6)** | −0.71 (−1.8) | **+0.54 (2.2)** |
| 3. Sort: abnormal company attention | | +0.32 (1.9) | 0.00 (0.0) | +0.26 (1.6) |
| 3. Sort: company attention growth | | +0.31 (1.7) | −0.22 (−0.6) | +0.25 (1.4) |
| 3. Sort: product attention growth | | +0.03 (0.1) | +0.03 (0.1) | −0.01 (0.0) |
| 3. Sort: products ahead of company | +0.46 (1.8) | +0.04 (0.1) | +0.04 (0.1) | +0.09 (0.5) |
| 4. Beat rate, busiest minus quietest products | −4.0 pts (−2.1) | +2.8 pts (1.1) | +2.8 pts (1.1) | −1.0 pts (−0.7) |
| 4. Reaction, busiest minus quietest | | +0.45 (1.2) | +0.45 (1.2) | −0.04 (−0.2) |
| 4. Beat rate, regression on product surge | −3.9 pts (−2.5) | +1.7 pts (1.1) | +1.7 pts (1.1) | −1.2 pts (−1.0) |

(Test 4 needs product pages, so "broad new" and "broad new, with products"
are the same 72 companies there.)

**Verdicts, by the rule fixed in advance:**

- **Strategy (1): replicates, and is strong in the new companies** (+0.28% a
  month, t 2.2). But it comes entirely from the companies **without** product
  pages: in the 72 new companies with product pages it is negative. So the
  edge is not product curiosity; the model is picking up company attention
  and the standard stock measures in banks, utilities, industrials and the
  like. Weighted by size it is not significant.
- **Products adding to company attention (2): does not replicate.** In the
  new companies the model with products does no better than company
  attention alone (+0.52 against +0.55).
- **Product signals on their own (3): do not replicate** (all about zero).
  **Company attention does better** in the new companies (abnormal company
  attention +0.32, t 1.9), unlike in the 112.
- **Product buzz before results means fewer beats (4): does not replicate.**
  In the new companies it points the other way (+2.8 points, t 1.1), and
  pooled over all 547 it is no longer significant (−1.0 points, t −0.7). In
  the same run, after Yahoo revised 161 past analyst estimates, the 112's own
  result moved from t −2.8 to t −2.4.

**Overall:** on a much larger and fairer set, the product-curiosity findings
do not hold up; what shows up instead is a modest effect of attention to the
company itself, mainly among companies the public does not otherwise follow.
Many tests have now been run, so even t 2.2 is weaker evidence than it looks.
Part 2 (click-through) follows once the download is complete.
