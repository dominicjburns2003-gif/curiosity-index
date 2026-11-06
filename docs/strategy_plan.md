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
