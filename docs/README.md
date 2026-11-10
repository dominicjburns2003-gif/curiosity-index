# The research, in the order it was done

Each file is a plan written and committed **before** its test was run (the
commit dates on GitHub show this), with the results added below it afterwards,
whatever they were. Read them in this order:

| # | File | Question | Result in one line |
|---|---|---|---|
| 1 | [strategy_plan.md](strategy_plan.md) | Can a model using attention pick stocks that beat the average? (68 companies; also the live strategy's rules and every change to them) | Small edge, not significant; planned improvements did not help |
| 2 | [earnings_test_plan.md](earnings_test_plan.md) | Does product buzz before results predict how they go? | Fewer beats with more buzz (68 companies), later not replicated |
| 3 | [clickthrough_tests_plan.md](clickthrough_tests_plan.md) | Does click-through predict volatility, or returns within sectors? | No |
| 4 | [expansion_replication_plan.md](expansion_replication_plan.md) | Do the findings hold on 44 new companies? | Only the earnings one, and only partly |
| 5 | [broad_universe_plan.md](broad_universe_plan.md) | Do they hold on every S&P 500 and Nasdaq-100 company (434 more)? Does click-through help? | No; the apparent strategy edge was hindsight in the index list |
| 6 | [attention_wave_plan.md](attention_wave_plan.md) | Buy on a surge in attention, hold while it lasts? (and a follow-up without a time limit) | No, in either period; the biggest surges did worse |
| 7 | [earnings_drift_plan.md](earnings_drift_plan.md) | Does low attention slow the reaction to earnings surprises? | No; the drift is larger with high attention |
| 8 | [ftse_plan.md](ftse_plan.md) | Do the findings hold in the FTSE 100? | No |
| 9 | [short_plan.md](short_plan.md) | Short companies whose attention falls away? | No |
| 10 | [news_split_plan.md](news_split_plan.md) | Buy only surges that come with good news (price beating the market)? | No: works after 2022, fails before; reverses between periods |
| 11 | [fundamentals_plan.md](fundamentals_plan.md) | Does attention add anything to company fundamentals (P/E, book value, profitability)? | No (+0.03% a month, t 0.3) |
| 12 | [risk_off_plan.md](risk_off_plan.md) | Switch from shares to bonds when public worry is high? | No: caught the 2020 crash, failed in 2022 |
| 13 | [risk_signals_plan.md](risk_signals_plan.md) | Does worry predict the market's return or volatility, beyond the VIX and trend? (and back to 2016) | Worry no; market-wide attention just misses (t −1.99) |
| 14 | [crypto_plan.md](crypto_plan.md) | Does attention predict Bitcoin, Ethereum, Solana and Cardano prices? | Yes over 4 weeks (t 2.1), but only in the 2017 and 2020–21 booms |

The top-100 version and the survivorship check are in `strategy_plan.md`
(addendum of 10 Nov 2026). Exploratory checks, not planned in advance, are
labelled as such where they appear.
