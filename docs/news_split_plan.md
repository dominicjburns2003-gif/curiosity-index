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
