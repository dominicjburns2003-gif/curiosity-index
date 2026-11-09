# Strategy improvement plan (pre-registered)

Written on 6 November 2026, **before** running any of the tests below, and
committed to the repository so the date can be checked. The point is that every
change is decided by reasoning first and then tested once, instead of trying
variations until one looks good.

## Why change the strategy

The first walk-forward test (Jan 2022 – Sep 2026, `src/walk_forward.py`) bought
the top third of the model's picks and shorted the bottom third. Two problems:

1. **Shorting low attention has no clear logic.** A quiet month for a
   company's Wikipedia page is not a reason to expect its share price to fall,
   and most investors who would use this cannot short.
2. **Attention can be bad news.** Scandals about a *product* look like product
   excitement: the signal ranked Boeing in its top group in March 2019
   (737 MAX grounding) and January 2024 (door-plug blowout). Scandals about the
   *company* (Bud Light boycott, Tesla in Nov 2022) were already avoided,
   because they lift the company page more than the products.

## The changes (all decided now)

1. **Long-only.** Buy the top third of companies each month, equally weighted.
   Compared with the **equal-weighted average of all 68 companies** (the fair
   benchmark, since we also weight equally) and with the S&P 500 (SPY).
   Long-short is kept as a secondary research number only.
2. **Bad-news filter.** A company is not bought if its share price is in the
   bottom third of the 68 that month: attention arriving with a falling price
   is more likely bad news. The next-best companies fill its place.
3. **Compare within sectors.** Each signal is measured relative to the median
   of the company's sector that month, using 5 broad sectors (the original 19
   labels are too small, e.g. Boeing is alone in Aerospace):
   Health (Pharma, Medtech), Consumer staples (Beverages, Household, Food,
   Tobacco), Consumer discretionary (Apparel, Restaurants, Toys, Retail,
   Travel, Media), Technology (software, hardware, semiconductors, fintech,
   games), Autos & aerospace.
4. **A simple combined score** alongside the tree model: the average of each
   company's monthly rank on the two most promising signals from the sorts,
   "products ahead of company" (gap) and "rising click-through"
   (conversion_change). Where click-through is missing, the gap rank is used alone.
5. **Hold for 3 months.** Each month a new top third is chosen and held for 3
   months, so the portfolio is an equal mix of the last 3 months' picks. This
   cuts trading (costs were about 0.2% a month).

Trading costs: 0.1% of every amount bought or sold, as before.

## Versions compared

| Version | Score | Sector-relative | Bad-news filter | Holding |
|---|---|---|---|---|
| A. Baseline | tree model, products version (as before) | no | no | 1 month |
| B. Simple score | gap + rising click-through | no | yes | 3 months |
| C. Simple score, sectors | gap + rising click-through | yes | yes | 3 months |
| D. Tree model, improved | tree model on sector-relative features + this month's return | yes | yes | 3 months |

Two extra checks on version B only, to show what each change does: B without
the filter, and B held for 1 month.

## How the winner is chosen and tested

- **Development period: Jan 2022 – Dec 2024** (36 months).
- **Rule fixed now:** the version with the highest average monthly return
  **above the equal-weighted average of the 68 companies, after costs**, over
  the development period is chosen.
- **Final check: Jan 2025 – latest month.** The chosen version is run on this
  period once, and the result is reported whatever it is. All versions are
  shown for transparency, but only the development period decides.
- **Honest caveat:** the earlier long-short results for 2025–2026 were seen
  on 6 Nov 2026, so the final period is not perfectly unseen.
- **Truly unseen test:** from November 2026 the app records its picks each
  month before the returns are known, building a live record.

Tree model settings are unchanged from `src/walk_forward.py`. Nothing is tuned
on either test period.

## Results (added on 6 Nov 2026, after running `src/strategy.py`)

Long-only, after costs, average monthly return above the equal-weighted
average of the 68 companies (t-statistic in brackets):

| Version | Development 2022–24 | Final 2025–26 |
|---|---|---|
| A. Baseline tree model, monthly | +0.18% (0.6) | +0.40% (0.7) |
| B. Simple score, filter, 3 months | −0.08% (−0.5) | +0.28% (1.0) |
| C. As B, vs sector | −0.12% (−0.7) | −0.09% (−0.5) |
| D. Tree vs sector, filter, 3 months | −0.16% (−1.0) | −0.22% (−0.7) |
| Check: B without the filter | +0.20% (1.4) | +0.15% (0.7) |
| Check: B held 1 month | −0.04% (−0.2) | +1.08% (2.2) |

- **Chosen by the rule: A**, the baseline. It beat the average company in
  both periods, but weakly (t below 1).
- **None of the planned improvements helped** in the development period.
- **The bad-news filter hurt.** Among the top third by signal (2022 onwards),
  companies whose price was falling that month earned +1.27% the next month,
  against +1.01% for the others: when attention and bad news arrive together
  the price tends to bounce back, so the filter removed good picks.
- **Comparing within sectors hurt**: the signals seem to work partly by
  picking whole sectors (for example consumer brands with viral products).
- **Holding for 3 months** cut costs from about 0.13% to 0.05% a month.
- **"B held 1 month" looks best in the final period (t = 2.2) but is not
  chosen**: it was a check, not a candidate, and it lost in the development
  period. Picking it now would be exactly the kind of result-shopping this
  plan was written to prevent.
- All long-only versions trailed the S&P 500 in 2022–24, when a handful of
  very large technology companies drove the index; the 68 companies are
  equally weighted, so they are compared with their own average first.


## Addendum: size-weighted version (written on 6 Nov 2026, before running it)

**Why:** every version above lost to the S&P 500 over 2022–2024, mainly because
the S&P 500 is weighted by company size and was driven by a few very large
technology companies, while our strategy and benchmark weight every company
equally. Most funds weight by size, so it is a fair question in its own right
whether the signal still adds value when the portfolio is built that way.

**The test (one version, no choosing):**

- **Same picks as the chosen version (A)**: the top third of companies by the
  tree model each month, held for 1 month, no filter.
- **Weighted by market cap** at the end of the month, with **no company above
  15%** (anything above is shared out among the others in proportion to their
  size). 15% is about the largest single weight among the 68 companies.
- **Benchmark:** all 68 companies weighted the same way (market cap, 15% cap).
  Also compared with the S&P 500.
- **Costs:** 0.1% of every amount traded, as before.
- **Reported for both periods** (2022–24 and 2025–26), once, whatever the
  result. It does not replace the chosen version; it is shown alongside it.

### Size-weighted results (added on 6 Nov 2026, after running)

| Size-weighted picks vs | 2022–24 | 2025–26 | Whole period, $100 became |
|---|---|---|---|
| 68 companies weighted by size | −0.24%/month (t −0.6) | +0.74%/month (t 1.6) | $201 vs $193 |
| S&P 500 | −0.06%/month (t −0.1) | +0.93%/month (t 1.2) | $201 vs $179 |

- Weighted by size, the picks beat the S&P 500 over the whole period, but
  **most of that lead comes from the companies tracked**: holding all 68 by
  size made $193. The signal itself added about $8 per $100 (t 0.4).
- The picks **lagged in 2022–24** and pulled ahead only in 2025–26.

## Addendum: robustness checks on the chosen version (written on 6 Nov 2026, before running them)

**Why:** to see whether the chosen version's small edge depends on two
arbitrary choices, the holding period (1 month) and the group size (top third).
Suggested by Dominic.

**The checks**, all with the chosen version's picks (A: tree model, no filter,
equal amounts), compared with the 68-company average after 0.1% costs:

1. Held for **3 months** (an equal mix of the last 3 months' picks), top third.
2. Held for 1 month, **top quarter** (17 companies instead of 23).
3. Held for **3 months**, **top quarter**.

**These do not replace the chosen version**: it was already chosen by the fixed
rule. They are reported for both periods, once, whatever the result. If the
edge is similar across them, the signal is robust; if it swings a lot, it is
fragile.

### Robustness results (added on 6 Nov 2026, after running)

Above the 68-company average, after costs (t in brackets):

| Version | 2022–24 | 2025–26 | Whole period, $100 became |
|---|---|---|---|
| A (top third, 1 month) | +0.18% (0.6) | +0.40% (0.7) | $163 |
| Held 3 months | +0.28% (1.3) | +0.37% (0.8) | $169 |
| Top quarter | +0.09% (0.2) | +0.61% (0.7) | $163 |
| Top quarter, 3 months | +0.24% (0.9) | +0.65% (0.9) | $175 |

All four are positive in both periods: the edge does not depend on the holding
period or the group size, though none is statistically significant (largest
whole-period t: 1.4, for 3 months). Holding for 3 months cuts costs from about
0.10% to 0.04% a month. The S&P 500 made $179 over the same period. As planned,
these do not replace the chosen version.

## Addendum: a longer test starting in 2020 (written on 6 Nov 2026, before running it)

**Why:** the walk-forward test starts in January 2022, giving 57 test months.
Starting in January 2020 gives about 81, which makes the t-statistics more
reliable. The cost is that the first models learn from only about 2½ years
(mid-2017 to late 2019), and the test then includes the COVID crash.

**The test:** exactly the same models and settings, with the first test year
moved from 2022 to 2020 (trained on data to November 2019, predicting 2020,
then retrained every January as before):

1. The chosen strategy (A: tree model, top third, 1 month, no filter), in equal
   amounts vs the 68-company average, and weighted by size (15% cap) vs the 68
   weighted by size; both also vs the S&P 500.
2. The three long-short research versions (company only, + products,
   + click-through).

Reported once, for January 2020 to the latest month, whatever the result. It
does not change the chosen version or the main results, which keep starting in
2022; it shows whether they hold over a longer stretch.

### Longer test results (added on 6 Nov 2026, after running `src/longer_test.py` once)

January 2020 to September 2026, 81 test months, after costs:

| Test | Result | t | $100 became |
|---|---|---|---|
| A, equal amounts, vs the 68-company average | +0.13%/month | 0.6 | $237 vs $218 (S&P 500 $258) |
| A by size, vs the 68 by size | +0.14%/month | 0.6 | $353 vs $325 (S&P 500 $258) |
| Long-short: company attention only | −0.17%/month | −0.4 | |
| Long-short: + product attention | +0.23%/month | 0.6 | |
| Long-short: + click-through | +0.06%/month | 0.2 | |

- **The same pattern holds over the longer period**: the strategy beats its
  own benchmark in both forms, product attention beats company attention
  alone, and click-through adds nothing.
- **But the edge is smaller and no more significant**: 2020–2021 (COVID, with
  models trained on only 2½ years) diluted it. More months did not raise the
  t-statistics, which suggests the edge, if real, is small.
- Equal amounts still trail the S&P 500; weighted by size the picks beat it,
  again mostly because of the companies tracked ($325 for the 68 by size).

## Live record: how it is counted (6 Nov 2026)

Monthly picks can only be made once the previous month's data is complete,
which (with Wikipedia's one-day publishing delay) is a day or two into the
month. So the live record counts each month's picks **from the close on the day
they were recorded**, as a real investor could, to the end of that month. Any
returns that had already happened before the picks were recorded are left out.
The first picks (for November 2026) were recorded on 6 November 2026.

**Changed on 8 Nov 2026, before the record had a single completed day:** the
daily update now runs at 22:00 UTC, after the US market close (a 07:00 run
always missed the latest Wikipedia day). Picks recorded in the evening come
after that day's close, which can no longer be traded, so each month's picks
are now counted from the close on the **next** trading day after they are
recorded. November's picks (recorded on 6 Nov 2026, after the close) are
therefore counted from the close on 9 Nov 2026.

## Change to the live strategy: all 112 companies from December 2026 (written on 9 Nov 2026)

From the picks chosen at the end of November 2026 (held in December) onwards,
the live strategy uses **all 112 companies**: the same version A (tree model,
same settings, top third, equal amounts, 1 month), trained walk-forward on all
112 and choosing from all 112. Its track record is compared with the
equal-weighted average of all 112 and with the S&P 500.

**Why:** for users of the app there is one universe of 112 companies, and the
replication (`docs/expansion_replication_plan.md`) showed no edge in either
the original 68 or the new 44, so this is not chosen to improve results.
**It only affects future months**, whose returns did not exist when this was
written, so it cannot use hindsight. November 2026's picks (from the original
68, recorded on 6 Nov 2026) stay in the record unchanged. All backtest and
replication results above stay as they are.

## Addendum: a minimum level of product interest (written on 9 Nov 2026, before running it)

**Idea (Dominic's):** the top third is a relative cut-off, so in a quiet month
the lowest of the picks may have almost no unusual interest. This version only
buys picks whose products are genuinely drawing more attention than usual.

**Rule, fixed before running:**
1. Take version A's top third on all 112 companies (same model, same settings,
   trained walk-forward on all 112, as in the all-112 replication).
2. Keep only the picks whose **product page views in the month are at least
   20% above their average over the previous 6 months** (`product_growth` ≥
   ln 1.2, the same measure the model already uses).
3. If **5 or more** qualify, buy them in equal amounts. If **fewer than 5**
   qualify, hold the **S&P 500 (SPY)** for that month instead.
4. Hold for one month; 0.1% trading costs on everything that changes,
   including moves into and out of SPY.

**Compared with:** version A on all 112 (the current strategy), the
equal-weighted average of the 112, and the S&P 500, after costs, from January
2022 picks to the latest month. Reported: return above each, t, how many
months were held in SPY, and the average number of companies held.

**Caveat, written in advance:** the 2022–2026 results of many versions have
already been seen, so a good result here could be luck from trying one more
version. It is run once and reported whatever the result. It does not change
the live strategy; any switch would be a separate decision, recorded here with
this caveat.

### Result (added on 9 Nov 2026, after running `src/threshold_test.py` once)

57 months (picks from January 2022 to September 2026), after costs. In 17
months fewer than 5 picks qualified and the S&P 500 was held; in the others
the strategy held 7.8 companies on average.

| | $100 became | vs version A, % a month (t) | vs average company (t) | vs S&P 500 (t) |
|---|---|---|---|---|
| Minimum interest version | $97 | −0.65 (−1.5) | −0.58 (−1.2) | −1.03 (−2.2) |
| Version A, all 112 (current) | $143 | | +0.07 (0.3) | −0.38 (−1.4) |
| Average of the 112 | $139 | | | |
| S&P 500 | $179 | | | |

It did worse than the current strategy in four of the five years. Keeping
only the picks with a product-attention surge left a handful of companies
that, on average, then did worse, consistent with the earnings finding (a
surge in product attention tends to come before disappointing results). The
live strategy is not changed.

## Change to the live strategy: all 546 companies from 10 November 2026 (written on 9 Nov 2026, during US trading hours)

This replaces the switch to all 112 from December, recorded earlier today.
From the close on **10 November 2026**, the live strategy uses **every
company in the universe** (all 546: the S&P 500, the Nasdaq-100 and the 112):
the same version A (tree model, same settings, top third, equal amounts,
1 month), trained walk-forward on all of them and choosing from all of them.
Its track record is compared with the equal-weighted average of all of them
and with the S&P 500.

- **November 2026:** the 23 picks recorded on 6 Nov 2026 (from the original
  68) are held from the close on 9 Nov to the close on 10 Nov, as already
  recorded. New picks for the rest of November, chosen the same way from all
  546 with data up to the end of October, are recorded today (9 Nov) and,
  by the existing rule, bought at the close on the next trading day (10 Nov)
  and held to the end of November. Both are kept in the record; nothing
  already recorded is changed.
- **From December:** the picks are chosen from all companies each month.
- **Why:** for the app there is now one universe of 546 companies, and on it
  the strategy's edge is if anything clearer (+0.28% a month, t 2.0, in
  `docs/broad_universe_plan.md`), but this is not a claim that it works: it
  only affects returns that have not happened yet (the first price used is
  the close on 10 Nov), so it cannot use hindsight.
