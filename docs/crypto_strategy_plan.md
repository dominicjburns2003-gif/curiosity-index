# A crypto strategy from Wikipedia attention (pre-registered)

Written on 10 November 2026, after the crypto attention test
(`crypto_plan.md`) and before any of this was coded or run, and committed so
the date can be checked.

## Why

The crypto test passed narrowly: over the whole period, a coin whose Wikipedia
page was busier than usual tended to rise over the next 4 weeks (t 2.1). A
t-statistic does not say whether an investor would have made money after
costs, or how that compares with simply holding the coins. This turns the
signal into a simple strategy and measures it in money, over the whole period.

## Data

As in `crypto_plan.md`: Bitcoin, Ethereum, Solana and Cardano, weekly
decisions every Sunday at that day's price, attention = log of the coin's
views over the 7 days ending 2 days before, against its usual week (the 8
weeks before). Each coin enters once it has a usable attention value (Bitcoin
April 2017, Ethereum December 2017, Cardano January 2018, Solana September
2021). The period runs to the latest Sunday with a following week's price.

## The strategy (fixed now)

- **Signal "on"** for a coin in a week when its attention is above zero (its
  page busier than its usual week).
- Because the effect was found over 4 weeks, **each "on" signal holds the coin
  for 4 weeks**: the money for each coin is split into 4 equal parts, one
  decided each week, so a coin's holding is the share of its last 4 weekly
  signals that were "on" (0, 25%, 50%, 75% or 100%).
- **Basket:** equal money for each coin available that week; the part not
  held in coins earns the US T-bill rate (cash).
- **Costs:** 0.25% on every change in holding (crypto trading costs are higher
  than for shares).

## Compared with

1. **Holding the coins:** the same equal-weight basket, always fully invested
   (rebalanced weekly, no costs counted, which favours it).
2. **Price trend instead of attention (the check):** the same rules, but the
   signal is "on" when the coin's return over the previous 4 weeks is above
   zero. Attention often follows price, so this shows whether attention adds
   anything a simple price trend does not.
3. **Bitcoin alone:** the attention strategy on Bitcoin only, against holding
   Bitcoin, reported alongside.

## How it will be judged

- Measures, over the whole period: $100 became, annual return, volatility,
  Sharpe ratio (return above the T-bill rate per unit of volatility), worst
  fall, and the share of the time in coins. Also shown for 2017–2021 and
  2022–2026 separately, for information only.
- **The attention strategy works if, over the whole period, its Sharpe ratio
  is higher than holding the coins.**
- **It adds something beyond price trend if its Sharpe ratio is also higher
  than the price-trend version's.**
- Run once and reported whatever the result. Four coins that move largely
  together over about 9 years are a small sample, and the strategy uses the
  same data that the test found the signal in, so even a pass is weak
  evidence for the future.

## Results (added on 10 Nov 2026, after running `src/crypto_strategy.py` once)

501 weeks, April 2017 to November 2026, after costs. Equal-weight basket of
the four coins unless stated.

| Strategy | Time in coins | $100 became | Annual return | Volatility | Sharpe | Worst fall |
|---|---|---|---|---|---|---|
| **Attention strategy** | 37% | **$4,023** | 46.7% | 43.4% | **1.02** | **−54%** |
| Price-trend strategy (check) | 53% | $8,024 | 57.6% | 55.3% | 1.00 | −68% |
| Holding the coins | 100% | $7,225 | 55.9% | 83.1% | 0.64 | −91% |
| Bitcoin: attention strategy | 39% | $3,218 | 43.4% | 40.7% | 1.00 | −48% |
| Bitcoin: holding | 100% | $6,767 | 54.9% | 68.9% | 0.76 | −83% |

For information, Sharpe ratio by half: attention strategy 1.80 (2017–2021)
and 0.14 (2022–2026); holding the coins 1.69 and −0.16; price trend 1.88 and
0.15.

**Verdicts, by the rules fixed in advance:**

- **The attention strategy works,** by the rule: over the whole period its
  Sharpe ratio is 1.02 against 0.64 for holding the coins. It made less money
  ($4,023 against $7,225 from $100), because it held coins only about a third
  of the time, but with half the volatility and a much smaller worst fall
  (−54% against −91%).
- **It adds almost nothing beyond price trend.** Its Sharpe ratio is higher
  than the price-trend version's by 0.02 (1.02 against 1.00), which passes the
  rule as written but is far too small to mean anything; the price-trend rule
  made twice as much money.

**Reading:** in crypto, almost any rule that steps out of the market for part
of the time cuts the huge crashes (−80% to −90%) and so improves the Sharpe
ratio; attention does this about as well as simply following the price,
which it largely tracks. The gain over holding came mostly in 2017–2021;
since 2022 both timing rules have barely beaten cash, though they avoided the
2022 crash that left buy-and-hold below its starting value.
