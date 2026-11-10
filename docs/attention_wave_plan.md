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

## Results (added on 10 Nov 2026, after running `src/attention_wave.py` once)

Decisions from 7 January 2022 to 6 November 2026 (59 months), after costs,
only companies in the S&P 500 at the time. Return above the equal-weighted
average of those companies, % a month (t); $100 became (average company
$166, S&P 500 $172 over the same weeks).

**Company pages**

| Entry | Exit | Above average | $100 became | Companies held (avg) | Purchases | Weeks held (avg) |
|---|---|---|---|---|---|---|
| 1.5× | normal | −0.04 (−0.1) | $160 | 27.9 | 958 | 7.4 |
| 1.5× | half | +0.12 (0.4) | $179 | 33.8 | 941 | 9.1 |
| **2×** | **normal (main)** | **+0.18 (0.4)** | **$174** | 13.3 | 425 | 8.0 |
| 2× | half | +0.20 (0.3) | $167 | 4.9 | 441 | 2.8 |
| 3× | normal | −0.71 (−1.0) | $98 | 5.4 | 151 | 9.2 |
| 3× | half | −1.30 (−1.1) | $62 | 0.9 | 155 | 1.5 |

**Product pages (control; average company $178 for these companies)**

| Entry | Exit | Above average | $100 became |
|---|---|---|---|
| 1.5× | normal | +0.15 (0.5) | $193 |
| 1.5× | half | +0.25 (0.9) | $206 |
| 2× | normal | −0.78 (−1.4) | $108 |
| 2× | half | −0.59 (−1.0) | $120 |
| 3× | normal | −0.02 (0.0) | $154 |
| 3× | half | −0.57 (−0.9) | $121 |

**Verdict, by the rule fixed in advance:** **it does not work.** Only 3 of
the 6 company-page versions beat the average company (the rule needed 4),
and none comes close to t 2. The product-page control does no better (2 of
6).

**One pattern, for the record (not a test):** the bigger the surge, the worse
the result. Companies whose page views tripled went on to do clearly worse
than the average (−0.7% to −1.3% a month, though on few companies and with t
around −1). Very large surges in attention are often bad news (a crisis, a
scandal, a collapse) or hype that fades, which fits earlier research on
"attention-grabbing" stocks (Barber and Odean, 2008). Moderate surges are
about neutral.

## Follow-up: no maximum holding time (written on 10 Nov 2026, after the results above, before running it)

**Change (Dominic's, on reflection):** the 26-week limit is the one rule not
driven by the data; it forces a sale even while attention stays high (it ended
42 of the 425 holdings in the main version, including Nvidia twice, Palantir,
Meta, Apple and Alphabet). In the follow-up **there is no maximum**: a company
is sold only when its attention fades by the exit rule ("normal" or "half"),
or when it can no longer be held (no price). Everything else is unchanged.

Because this change was made after seeing the results, it is judged on **two
periods**:

- **2022 – 2026**, the period already seen (for comparison with the original);
- **2017 – 2021**, five years this strategy has never been run on
  (decisions from March 2017, once 8 weeks of views exist). Caveat: before
  2020 Wikipedia counted some automated traffic as human; the spike cap
  removes most of it.

For comparison, the original rule (26-week cap) is also run on 2017 – 2021.

**It counts as working only if at least 4 of the 6 company-page versions
beat the average company in *both* periods.** All versions are reported, run
once.
