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
