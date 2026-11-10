# Good-news and bad-news attention surges (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. Idea: Dominic's.

## Why

A surge in attention can come from good news (a hit product, strong results)
or bad news (a scandal, a crisis, a collapse). The attention-wave test
(`docs/attention_wave_plan.md`) found that the biggest surges were followed by
below-average returns; this test asks whether that comes from the bad-news
surges, and whether buying only good-news surges works.

The original "bad-news filter" (`docs/strategy_plan.md`, 68 companies) used
the share price over a whole month and made results worse: companies with
attention and a falling price tended to bounce back. This test looks at the
surge week itself.

## The rule

Exactly the attention-wave rule (weekly checks; buy when the company page's
views over the 7 days ending 2 days before the decision reach **E** times the
usual week, with at least 2,000 views in a usual week; sell when views are
back to normal or below half the peak; no maximum holding time; equal amounts;
the S&P 500 when nothing is held; 0.1% trading costs; only companies in the
S&P 500 at the time), with one addition at the moment of buying:

- **Price move in the surge week:** the company's share-price change over the
  same 7 days as the attention window (last close on or before the window's
  end, against the last close on or before 7 days earlier), minus the S&P
  500's change over the same days.
- **Good-news surge:** price move above zero. **Bad-news surge:** at or below
  zero.

Two strategies, each in the six usual versions (E = 1.5, 2, 3; exit "normal"
or "half"):

1. **Buy only good-news surges** (the main test).
2. **Buy only bad-news surges** (reported alongside, to show which kind of
   surge drives the result).

Periods: 2017–2021 (decisions from March 2017) and 2022–2026.

## How it will be judged

- Return above the equal-weighted average of the companies in the index at
  the time, % a month (t), per version and period, and $100 became.
- **Buying good-news surges counts as working only if at least 4 of its 6
  versions beat the average company in both periods.**
- **Caveat, written in advance:** both periods were already used for the
  attention-wave test, so this split is tested on data that has been looked
  at. A pass would be encouraging but not conclusive; the only fully fresh
  test is the future.
- Run once and reported whatever the result.

## Results (added on 10 Nov 2026, after running `src/news_split.py` once)

Only companies in the S&P 500 at the time, after costs; return above the
average company, % a month (t), and $100 became (average company: $223 in
2017–2021, $166 in 2022–2026).

**Buying only good-news surges (price beat the market in the surge week)**

| Entry | Exit | 2017–2021 | 2022–2026 |
|---|---|---|---|
| 1.5× | normal | −0.60 (−2.0), $157 | +0.19 (0.4), $180 |
| 1.5× | half | −0.30 (−1.5), $189 | +0.06 (0.2), $172 |
| 2× | normal | −0.80 (−1.9), $139 | +0.75 (1.2), $237 |
| 2× | half | −1.06 (−1.9), $116 | +1.14 (1.1), $271 |
| 3× | normal | −0.75 (−1.2), $140 | +0.71 (0.8), $214 |
| 3× | half | −0.99 (−1.6), $119 | −0.27 (−0.4), $132 |

**Buying only bad-news surges (price lagged the market)**

| Entry | Exit | 2017–2021 | 2022–2026 |
|---|---|---|---|
| 1.5× | normal | −0.19 (−0.9), $199 | −0.24 (−0.7), $142 |
| 1.5× | half | −0.17 (−0.7), $199 | +0.28 (1.0), $196 |
| 2× | normal | −0.09 (−0.3), $209 | −0.17 (−0.3), $140 |
| 2× | half | +0.05 (0.1), $217 | −0.01 (0.0), $148 |
| 3× | normal | +0.15 (0.4), $241 | −1.04 (−1.4), $80 |
| 3× | half | −0.32 (−0.5), $175 | −0.66 (−0.6), $94 |

**Verdict, by the rule fixed in advance: it does not work.** Good-news surges
beat the average in 5 of 6 versions in 2022–2026 but in **none** of the 6 in
2017–2021, where every version did worse than the average (t close to −2 in
three of them).

**What it shows:** the effect of a surge reverses between the two periods.
In 2022–2026, companies whose attention surged on good news kept rising and
those surging on bad news kept falling (momentum); in 2017–2021, good-news
surges were followed by clear underperformance (reversal), and bad-news
surges by about average returns. Separating good from bad news does not give
a stable signal: which one pays depends on the period, which is what a
fragile, regime-dependent pattern looks like.
