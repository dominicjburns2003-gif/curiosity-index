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
