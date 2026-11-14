# Live test: does market-wide attention warn of weaker markets? (pre-registered)

Written on 14 November 2026, before any of it was coded, and committed so the
date can be checked. A follow-up to `risk_signals_plan.md`.

## Why

Over July 2016 to October 2026, when the typical US company's Wikipedia page
was unusually busy, the S&P 500 tended to do worse over the next 4 weeks,
even allowing for the VIX and the market's trend (t −1.99, significant at the
5% level). That result came from past data that has now been looked at many
times, so it cannot be fairly re-tested on the same years. The only clean
test is on weeks that have not happened yet. This plan fixes the signal and a
simple rule now, and records every decision as it is made.

## The signal (unchanged from `risk_signals_plan.md`)

- For each US company the site follows, its page views over the 7 days ending
  2 days before the decision day, against its usual week (the average of the
  8 weeks before). The signal is the log of the **median** of this ratio
  across companies.
- Decisions at the close on the last trading day of each week.
- **High** when the signal is above the **90th percentile of all earlier
  weeks** (from January 2017 to the week before).

## The rule (fixed now)

- **Normal week:** hold the S&P 500 (SPY, dividends reinvested).
- **High week:** hold **50% S&P 500 and 50% cash** (the US T-bill rate) for
  the following week.
- 0.1% trading cost on the part of the money that changes.
- The 90th percentile is the middle of the three levels used in
  `risk_off_plan.md`; half rather than all of the money is moved because the
  earlier tests showed the signal is weak and switching fully is costly. This
  exact rule has not been run on past data.

## Recording

- From the decision on **Friday 20 November 2026** onwards, the nightly
  update computes each week's signal once it has the Wikipedia data, and
  appends the decision to `data/processed/market_attention_live_log.csv`
  with the date it was recorded. Rows are never changed afterwards.
- The decision uses only page views up to 2 days before the decision day, so
  recording it a day or two late (when Wikipedia publishes late) cannot use
  any later information.

## How it will be judged

Results are shown on the site as they come in, but no verdict is given before
the checks below.

1. **The main test (at 52 and 104 weeks, i.e. November 2027 and November
   2028):** over the live weeks only, the S&P 500's return over the next 4
   weeks (minus the T-bill rate) regressed on the signal, the VIX and the
   trend, exactly as in `risk_signals_plan.md`, with Newey–West standard
   errors (4 lags). **The signal predicts weaker markets if its coefficient
   is negative with t of −1.96 or below** (the standard 5% level).
   The 52-week check is reported as interim: with about 50 weeks, only a
   strong effect could pass.
2. **The rule, reported alongside:** $100 in the rule against $100 in the
   S&P 500, Sharpe ratio, worst fall and the share of weeks it was high.
   High weeks are rare (about 1 in 10), so this will rest on few weeks.
- Reported whatever the result.

## Not part of this test: the worry gauge

The site also shows a **worry gauge**: views of *Recession*, *Stock market
crash*, *Inflation*, *Stagflation* and *Bank run* this week against their
average week over the past year, page by page. The earlier tests found that
worry views predict a bumpier market (t 4.1 on their own) but not its
direction, and add little to the VIX. The gauge is therefore shown as a
description of what the public is worried about, with no trading rule.
