# Does public worry predict the market, beyond the usual fear gauges? (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. A follow-up to `risk_off_plan.md`,
whose switching rule needed thresholds chosen in advance and rested on two
crises.

## Why

Before trusting any "switch to bonds" rule, the basic question has to be
answered without thresholds: **does a higher worry reading predict the
S&P 500's return, or its volatility, over the following weeks?** And does it
add anything to the measures investors already use: the **VIX** (the
market's "fear index") and the simplest risk-off rule in practice, **trend**
(the S&P 500 against its 200-day average)?

## Signals (each week, at the decision day's close; known by then)

- **Worry:** log of the worry pages' combined views over the 7 days ending 2
  days before the decision (*Recession*, *Stock market crash*, *Inflation*,
  *Stagflation*, *Bank run*, as in `risk_off_plan.md`), against their average
  week over the previous 52 weeks. Measuring against the past year keeps the
  signal comparable as Wikipedia's overall traffic falls.
- **Market-wide attention:** log of the median US company's views that week
  against its usual week (as in `risk_off_plan.md`).
- **VIX:** log of the VIX at the decision day's close (^VIX, Yahoo).
- **Trend:** the S&P 500's close against its 200-trading-day average, minus 1.

Each is standardised (mean 0, standard deviation 1 over the period), so the
coefficients are comparable; this does not change any t-statistic.

## Outcomes

- **Return:** the S&P 500's return (SPY, dividends reinvested) over the next
  4 weeks, minus the T-bill rate.
- **Volatility:** the log of the S&P 500's daily-return volatility over the
  next 4 weeks (annualised).

## Tests

Weekly observations from March 2018 (once a year of worry history exists) to
the latest week with 4 weeks of outcomes. Because 4-week outcomes overlap
from week to week, standard errors are Newey–West with 4 lags.

1. Each signal alone: outcome = a + b × signal.
2. **Worry with the fear gauges:** outcome = a + b₁ worry + b₂ VIX + b₃ trend;
   and the same with market-wide attention in place of worry.

## How it will be judged

- **Worry predicts returns** if, in test 2, its coefficient is **negative
  with t of −2 or below**, and negative in both 2018–2021 and 2022–2026.
- **Worry predicts volatility** if, in test 2, its coefficient is **positive
  with t of 2 or more**, and positive in both halves.
- The same rules for market-wide attention.
- Reported whatever the result, run once. If either signal passes, the next
  step (written down separately before it is run) would be to check it on
  older Wikipedia archives covering the 2008, 2011 and 2015–16 sell-offs.
