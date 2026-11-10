# The attention-wave strategy (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. Idea: Dominic's.

## Why

Every strategy so far ranks all companies and buys a fixed slice for a fixed
month. This one reacts to events instead: **buy a company when attention to
it surges, and hold it while the attention lasts.** It rests on a known
finding: a surge in investor attention (e.g. Google searches, Da, Engelberg
and Gao, 2011) is followed by higher returns for a few weeks as new buyers
arrive, part of which later reverses, so holding while attention stays high
and selling as it fades is a natural rule.

## The rule

- **Checked weekly.** Each decision is made at the close on the last trading
  day of the week (usually Friday).
- **Attention measure:** views of the company's own Wikipedia page (all its
  titles added up, one-day automated spikes capped, as everywhere else), over
  the 7 days ending **2 days before** the decision day (Wikipedia publishes
  each day with a delay), against its **usual week**: the average week over
  the 8 weeks before those 7 days. This is the Trending tab's measure.
- **Buy** when this week's views are at least **E** times the usual week, and
  the usual week has at least 2,000 views (as in Trending, so tiny pages
  cannot trigger it).
- **Sell** at the first weekly check where the exit rule is met, or after
  **26 weeks** at most:
  - exit rule **"normal"**: views are back at or below the usual week as
    measured at the time of buying;
  - exit rule **"half"**: views have fallen below half of the highest week
    since buying.
- **Holdings:** equal amounts in everything held, rebalanced each week; when
  nothing is held, the money is in the S&P 500 (SPY). Trading costs of 0.1%
  of every amount bought or sold.
- **Universe:** only companies that were in the S&P 500 at the time
  (`data/mapping/index_membership.csv`), so nothing can be picked with
  hindsight; companies that later left the index are missing, which still
  flatters the results a little.
- **Period:** decisions from the first week of 2022 to the latest week.

## Versions (all reported)

| | Exit "normal" | Exit "half" |
|---|---|---|
| Entry E = 1.5 | ✓ | ✓ |
| Entry E = 2 (main) | ✓ | ✓ |
| Entry E = 3 | ✓ | ✓ |

The **main version** is E = 2 with exit "normal". The same six are also run
on **product pages** (the views of all a company's product pages added up,
for companies that have them), as the control for the project's original
idea.

## How it is judged

- Monthly returns (weekly returns compounded within each month), after
  costs, against the equal-weighted average of the companies in the index at
  the time (rebalanced weekly the same way) and against the S&P 500. Reported
  for each version: return above the average, % a month, with its t; $100
  became; the average number of companies held; the average holding time;
  the share of weeks with nothing held.
- **It counts as working only if at least 4 of the 6 company-page versions
  beat the average company**, and as **strong** only if at least 4 of the 6
  do so with t of 2 or more. The best single version is not the result.
- Run once and reported whatever the result. Nothing in the live strategy
  changes because of it; any use would be a separate decision recorded in
  `docs/strategy_plan.md` before it applies.
