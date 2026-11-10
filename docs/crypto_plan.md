# Does Wikipedia attention predict crypto prices? (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked.

## Why

Cryptocurrencies are driven far more by public attention than company shares
are, and have no earnings or fundamentals, so if attention predicts prices
anywhere, it might be here. Research has found that Google and Wikipedia
interest in Bitcoin moves with its price (e.g. Kristoufek, 2013), but mostly
alongside it rather than ahead of it.

## Data

- **Coins:** Bitcoin, Ethereum, Solana, Cardano (BTC-USD, ETH-USD, SOL-USD,
  ADA-USD on Yahoo, every calendar day, as crypto trades all week), each from
  the first week with both a price and 9 weeks of page views (Solana from
  about 2020).
- **Attention:** views of the coin's own Wikipedia page (spikes capped as
  everywhere else) over the 7 days ending 2 days before the decision day,
  against its average week over the 8 weeks before; the signal is the log of
  that ratio.
- **Weekly decisions** every Sunday, at that day's price.

## Outcomes and test

- **Next week's return** (Sunday to Sunday, log), and the **next 4 weeks'**.
- For each outcome, a pooled regression across the four coins:
  return = a + b × attention + c × the coin's return over the previous 4
  weeks (attention often follows a price move, so this keeps the two apart),
  with Newey–West standard errors (lag 1 for one week, 4 for four weeks), and
  the same regression for each coin on its own.

## How it will be judged

- **Attention predicts crypto prices** if, for either outcome, the pooled
  coefficient **b has |t| of 2 or more and the same sign in at least 3 of the
  4 coins**. Either sign counts (attention could warn of a rise or a fall),
  and both are reported.
- Run once and reported whatever the result. Four coins that move largely
  together, over about 5 to 9 years, are a small sample.

## Results (added on 10 Nov 2026, after running `src/crypto_test.py`)

1,599 coin-weeks (Bitcoin from April 2017, Ethereum from December 2017,
Cardano from January 2018, Solana from September 2021). Effect of a one
standard deviation rise in attention on the log return, % (t), with the
previous 4 weeks' return included.

| Outcome | Pooled | Bitcoin | Ethereum | Solana | Cardano |
|---|---|---|---|---|---|
| Next week | +0.30 (0.7) | +0.96 (1.7) | +0.54 (0.7) | −0.24 (−0.4) | −0.41 (−0.5) |
| **Next 4 weeks** | **+2.48 (2.1)** | **+3.12 (2.4)** | **+5.79 (3.1)** | +1.04 (0.7) | −1.57 (−0.5) |

**A correction made before reporting:** the first run of the pooled test gave
t 2.46 for the next 4 weeks, but its standard errors were wrong: with up to
four coins per week, the 4-lag correction covered only about one week, and it
ignored that coins move together within a week. The pooled test was rerun
with Driscoll–Kraay standard errors (each week's coins grouped, then 4 weeks
of lags), the correct method for this set-up; that is the t of 2.1 in the
table. Coin-by-coin results were not affected.

**Verdict, by the rule fixed in advance: it passes, narrowly.** For the next
4 weeks, the pooled effect has t 2.1 and is positive for 3 of the 4 coins:
when a coin's Wikipedia page was busier than usual, its price tended to rise
over the following month, even allowing for its recent price move. Not for
the next week alone (t 0.7). The only earlier passes in the project (the
first earnings test on 68 companies, and the strategy on today's index
members) did not survive later checks, so this one needs the same scrutiny.

**Exploratory check, not part of the plan: the two halves.**

| | Pooled effect, next 4 weeks | Correlation, Bitcoin / Ethereum / Solana / Cardano |
|---|---|---|
| 2017–2021 | +5.31 (t 2.6) | 0.20 / 0.29 / 0.30 / −0.04 |
| 2022–2026 | +0.26 (t 0.2) | 0.07 / 0.03 / 0.01 / 0.00 |

**Reading, with caution:** the whole effect comes from 2017–2021, the two
big crypto booms (2017 and 2020–21), when rising public curiosity went with
prices that kept rising; since 2022 it has been close to zero. The four coins
move largely together, so this is close to one market observed over a few
cycles, and many tests have been run in this project. It is the strongest
evidence of any attention signal here, but it looks like a feature of
speculative booms rather than a lasting rule.
