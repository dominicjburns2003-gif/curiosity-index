# The FTSE 100 (pre-registered)

Written on 10 November 2026, before any UK page views, prices or results were
downloaded, and committed so the date can be checked.

## Why

A second market: are the patterns found in US companies the same in the UK,
whose companies all have English Wikipedia pages?

## The universe

- **Companies:** the FTSE 100 as listed on Wikipedia (`FTSE_100_Index`,
  constituents table) on 10 Nov 2026; London tickers on Yahoo (".L").
  AstraZeneca, BAT, Coca-Cola Europacific, Diageo and Unilever are already
  tracked through their US listings and are not added again, so the UK group
  is **95 companies** (`cohort = "ftse"`). Built by `src/build_ftse_universe.py`.
- **Products:** drafted from general knowledge, checked automatically and
  reviewed by the same rules as before; companies without product pages are
  tracked by their company page alone.
- **Prices** are in the currency each share is quoted in (mostly pence);
  returns are in pounds. Market values are converted to dollars at each month
  end's exchange rate, so size can be compared with US companies.
- **Benchmark:** the iShares FTSE 100 fund with dividends reinvested (CUKX.L),
  and the equal-weighted average of the 95.

**Known bias, accepted in advance:** no record of past FTSE 100 membership is
available here, so today's members are used back to 2017. In the US this
flattered the strategy a lot (top 100: +0.76% a month with today's members,
+0.17% with members at the time). **UK strategy results are therefore
reported as flattered by hindsight**, and judged mainly on the tests this
affects less: the long-short comparison and the single-signal sorts (which
compare companies with each other) and the earnings test.

## What is tested

The same tests as for the S&P 500 expansion (`docs/broad_universe_plan.md`),
every setting unchanged, on the 95 UK companies, ranked among themselves:

1. **Strategy:** version A trained on the UK companies, top third in equal
   amounts and by size, against their own average, after costs (flattered,
   see above).
2. **Long-short:** company only, + products.
3. **The single-signal sorts** (company and product attention; click-through
   is not included, see below).
4. **Earnings:** product attention before results and the beat rate, if
   Yahoo has enough UK announcements (it has far fewer than for US companies,
   as UK companies report twice a year).

**Click-through is not tested in the UK:** it would need the whole
clickstream history downloaded again (about 50 GB), and it did not help in
the US.

## How it will be judged

- A finding **holds in the UK** if it has the same sign as in the US
  ("broad new" in `docs/broad_universe_plan.md`), and is **strong** if |t| is
  2 or more.
- Run once and reported whatever the result. The UK companies are not added
  to the US tests or to the live strategy.

## Results (added on 10 Nov 2026, after running `src/ftse_tests.py` once)

95 UK companies (20 with product pages that have enough history), ranked
among themselves; picks from January 2022 (strategy and long-short) or
2017 (sorts) to October 2026; % a month (t). For comparison, the same tests
on the 435 new US companies ("broad new").

| Test | UK (FTSE 100) | US, broad new |
|---|---|---|
| 1. Strategy vs own average, equal amounts (UK flattered by hindsight) | −0.01 (−0.1) | +0.28 (2.2) |
| 1. Strategy vs own average, by size (flattered) | −0.26 (−0.8) | +0.33 (1.4) |
| 2. Long-short, company only | +0.33 (1.2) | +0.55 (2.5) |
| 2. Long-short, + products | +0.06 (0.3) | +0.52 (2.6) |
| 3. Sort: abnormal company attention | −0.12 (−0.6) | +0.32 (1.9) |
| 3. Sort: company attention growth | −0.18 (−0.9) | +0.31 (1.7) |
| 3. Sort: product attention growth | −0.46 (−1.1) | +0.03 (0.1) |
| 3. Sort: products ahead of company | +0.10 (0.2) | +0.04 (0.1) |

$100 in the UK strategy became £158, against £161 for the 95 companies held
equally and £170 for the FTSE 100 fund.

*Correction, same day:* the first run had a bug in the shared price calendar
(London's extra trading days, which are US holidays, left gaps in the daily
series), which slightly changed the model's inputs. The bug was fixed before
anything else was done, and the table shows the corrected run; the verdict
did not change (first run: strategy +0.01, long-short +0.24 and +0.17).

**Earnings (test 4): not enough data.** Yahoo has analyst estimates for only
17 of the 95 UK companies, over 6 quarters (417 announcements), too few for
the test to mean anything; it is not counted.

**Verdict:** nothing replicates in the UK. The strategy does not beat its own
average even with hindsight in the company list, product attention again adds
nothing to company attention, and the company-attention signals that were
mildly positive among the new US companies point the other way in the UK.
