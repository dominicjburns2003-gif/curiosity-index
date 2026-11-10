# Short selling on fading attention (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. Idea: Dominic's.

## Why

Every strategy so far only bought. This one sells short: borrow a share, sell
it, buy it back later. It profits if the company does worse than the market.
**Idea:** companies whose Wikipedia attention clearly falls away, a real
drop-off rather than a quiet page, are being forgotten by investors and may
then do worse.

## The rule ("short the fading")

- **Checked weekly**, at the close on the last trading day of each week, using
  the same attention measure as the attention-wave test
  (`docs/attention_wave_plan.md`): views of the company's own page over the 7
  days ending 2 days before the decision day, against its usual week (the
  average of the 8 weeks before).
- **Short** a company when this week's views are at most **F** times its usual
  week, and the usual week has at least 2,000 views.
- **Close the short** (buy the shares back) by the exit rule:
  - **"normal":** when views are back at or above the usual week measured when
    the short was opened;
  - **"4 weeks":** after 4 weekly checks.
  A short is also closed if the company has no price.
- **Holdings:** equal amounts in every open short, rebalanced weekly. The cash
  from the sales earns the US Treasury-bill rate (Kenneth French's data), as it
  would at a broker; with nothing shorted, the money simply earns that rate.
- **Costs:** 0.1% of every amount traded, plus a borrowing fee of **0.5% a
  year** on the amount shorted (typical for large US shares).
- **Universe:** only companies in the S&P 500 at the time
  (`data/mapping/index_membership.csv`).
- **Periods:** 2017–2021 (decisions from March 2017, once 8 weeks of views
  exist) and 2022–2026, reported separately and together.

## Versions (all reported)

| | Exit "normal" | Exit "4 weeks" |
|---|---|---|
| F = ⅔ | ✓ | ✓ |
| **F = ½ (main)** | **✓** | ✓ |
| F = ⅓ | ✓ | ✓ |

## How it will be judged

- The measure is whether the shorted companies **did worse than the average
  company** (the equal-weighted average of the companies in the index at the
  time, rebalanced weekly the same way), after trading costs and the
  borrowing fee: the return of the short position minus the return of
  shorting the average company, % a month, with its t. This is what "makes
  money" means here: shorting the average company loses money whenever the
  market rises, so the question is whether these shorts lose less, or gain.
  Also reported: what $100 in the short position became in absolute terms.
- **It counts as working only if at least 4 of the 6 versions beat shorting
  the average company in both 2017–2021 and 2022–2026.**
- Run once and reported whatever the result. Nothing in the live strategy
  changes because of it.

## A second check, clearly labelled: short the biggest surges

The attention-wave test found that companies whose page views tripled did
worse afterwards, in both periods. Shorting them is the obvious response, but
because that pattern was found in this same data, a good result would be weak
evidence. Reported alongside, with that warning: short when views reach **3×**
the usual week, close when back to normal or below half the peak (as in the
attention wave), same costs and universe. Its only fair test is the future.

## Results (added on 10 Nov 2026, after running `src/short_strategy.py` once)

US companies in the S&P 500 at the time; after trading costs and the
borrowing fee. **Above shorting the average** = the short position's return
minus that of shorting the average company, % a month (t). $100 in the short
position became (shorting the average company: $37 in 2017–2021, $63 in
2022–2026: shorting loses money when shares rise, as they mostly did).

| Short when views fall to | Close | 2017–2021 | 2022–2026 | Shorts open (avg) | Weeks with none |
|---|---|---|---|---|---|
| ⅔ of usual | normal | +0.20 (1.2), $42 | −0.12 (−0.6), $58 | 65 | 0% |
| ⅔ of usual | 4 weeks | −0.02 (0.0), $36 | −0.35 (−0.8), $48 | 10 | 2% |
| **½ of usual (main)** | **normal** | **+0.30 (1.0), $44** | **+0.20 (0.5), $70** | 24 | 1% |
| ½ of usual | 4 weeks | −0.21 (−0.3), $33 | +0.11 (0.1), $59 | 2 | 22% |
| ⅓ of usual | normal | −0.26 (−0.6), $31 | −0.27 (−0.5), $51 | 8 | 1% |
| ⅓ of usual | 4 weeks | +0.91 (1.0), $64 | +0.31 (0.4), $72 | 0.6 | 56% |

**Verdict, by the rule fixed in advance: it does not work.** 3 of the 6
versions beat shorting the average company in 2017–2021, and 3 of 6 in
2022–2026 (the rule needed 4 in both). The main version is positive in both
periods but far from significant (t 1.0 and 0.5). The best-looking version
(⅓, 4 weeks) holds almost nothing, so most of its result is cash earning
interest while the market rose, not good shorts. Note also that early
January weeks look like drop-offs for many pages (holiday reading is lower),
which adds noise.

**Check: short the biggest surges (3×), labelled in advance as weak
evidence.**

| Close | 2017–2021 | 2022–2026 |
|---|---|---|
| normal | −0.04 (−0.1), $36 | −0.14 (−0.2), $54 |
| below half the peak | +0.52 (0.9), $47 | +0.31 (0.3), $61 |

Mixed: shorting huge surges does not reliably work either, even though the
companies concerned did somewhat worse when bought (attention-wave test).
