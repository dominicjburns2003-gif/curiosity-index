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
