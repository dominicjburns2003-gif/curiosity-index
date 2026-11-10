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

## Results (added on 10 Nov 2026, after running `src/risk_signals_test.py` once)

451 weeks, March 2018 to October 2026. Coefficients per one standard
deviation of the signal (Newey–West t in brackets). Returns: % over the next
4 weeks above the T-bill rate. Volatility: change in log volatility over the
next 4 weeks (0.10 is roughly 10% higher volatility).

**Next 4 weeks' return**

| Signal | Alone, 2018–2026 | With VIX and trend, 2018–2026 | With VIX and trend, 2018–2021 | With VIX and trend, 2022–2026 |
|---|---|---|---|---|
| Worry | +0.23 (0.5) | −0.30 (−0.9) | −0.04 (−0.1) | −0.47 (−1.3) |
| Market-wide attention | −0.61 (−1.9) | −0.51 (−1.6) | −0.33 (−0.6) | −0.61 (−1.7) |
| VIX (with worry) | +1.13 (3.1) alone | +0.95 (2.5) | +1.13 (2.7) | +0.58 (0.6) |

**Next 4 weeks' volatility**

| Signal | Alone, 2018–2026 | With VIX and trend, 2018–2026 | With VIX and trend, 2018–2021 | With VIX and trend, 2022–2026 |
|---|---|---|---|---|
| Worry | +0.16 (4.1) | +0.04 (1.7) | +0.08 (1.0) | +0.05 (1.8) |
| Market-wide attention | 0.00 (0.1) | +0.03 (1.3) | +0.05 (1.0) | +0.03 (1.1) |
| VIX (with worry) | +0.30 (11.4) alone | +0.25 (7.2) | +0.26 (6.7) | +0.18 (3.5) |

**Verdicts, by the rules fixed in advance:**

- **Worry does not predict returns.** Alone it points the wrong way; with the
  VIX and trend it is negative but far from significant (t −0.9).
- **Market-wide attention does not predict returns either,** although it is
  the closest: negative in both halves and with the fear gauges (t −1.6),
  below the bar of 2.
- **Worry does not pass for volatility, but comes close.** On its own it
  clearly predicts a bumpier market (t 4.1, positive in both halves); once
  the VIX is included, most of that disappears (t 1.7, positive in both
  halves but below 2). Wikipedia worry mostly repeats what the VIX already
  says, a little later and less precisely.
- **The VIX itself does the job:** it predicts volatility very strongly
  (t 7 to 11), and a high VIX was followed by *higher* returns (t 3.1), the
  well-known reward for holding shares when others are frightened.

**Reading:** with nothing to choose, the attention data says the same as the
switching test: worry tracks how turbulent markets are about to be, not which
way they go, and the market's own fear gauge already captures that. So there
is no case for the next step (older archives) on these signals.
