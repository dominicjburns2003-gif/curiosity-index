# Curiosity Index

*When people wonder who makes it, does the stock move?*

A self-updating app that tracks English Wikipedia attention to **641 listed
companies** (every company in the S&P 500, the Nasdaq-100 and the FTSE 100) at
three levels:

1. **Company attention:** views of the company's own page (e.g. Novo Nordisk)
2. **Product attention:** views of its products' pages (e.g. Ozempic), for the
   204 companies with product pages checked by hand (410 pages)
3. **Click-through:** the share of product readers who click on to the company
   page (US companies)

**Research question:** does public curiosity about companies and their
products predict stock returns, beyond company attention and standard risk
measures?

Course project, Machine Learning for Factor Investing, emlyon business school (2026).

**Live app:** https://curiosity-index.streamlit.app/ (updated every evening
after the US market close)

## What we found

Every test was written down before it was run (the plans are in `docs/`; start
with [docs/README.md](docs/README.md)), run once, and checked on companies and
years it was not designed on.

- **No strategy beats simply holding the market once it is tested fairly.**
  Over 20 versions were tested: a machine-learning ranking (gradient-boosted
  trees, walk-forward, out of sample), buying the top third or the top 100,
  minimum-interest filters, buying on a surge and holding while attention
  lasts, short selling fading attention, click-through, and attention around
  earnings announcements. The live strategy (top 100) beat the average company
  by about +0.2% a month from 2022 (t about 1), not enough to rule out luck;
  the S&P 500 had a similar or better return per unit of risk.
- **Early findings did not survive replication.** Results that looked
  promising on the first 68 companies (product attention adding to company
  attention; product buzz before earnings meaning fewer beats) did not hold on
  44 new companies, on the 434 further S&P 500 and Nasdaq-100 companies, or in
  the FTSE 100.
- **Two traps were found and corrected.** Using today's index members back to
  2017 made the top-100 strategy look strong (+0.76% a month, t 3.3); counting
  only companies in the index at the time cut it to about +0.2% (t 1.0),
  because the model had picked, with hindsight, companies that later soared
  into the index. A rule changed after seeing results worked on 2022–2026 but
  failed in all six versions on 2017–2021, the years held back.
- **What attention seems to measure is size, not direction.** The largest
  surges in attention (page views tripling) were followed by below-average
  returns in both periods, and earnings surprises drawing a lot of attention
  drifted further afterwards. Attention looks like a sign that something big
  is happening, not of which way the price will go.

In the app, **Results** shows all of this, with a factsheet-style table of
every strategy; **Trending** and **Discovery** show where attention is moving
now (Discovery also finds listed companies the index does not track); **Track
record** follows the live strategy's recorded picks, the only fully
hindsight-free test, from 10 November 2026.

## Project structure

```
curiosity-index/
├── src/
│   ├── wiki_api.py, pageview_store.py          Wikimedia helpers; daily views stored month by month
│   ├── check_universe.py, prepare_review.py    automatic checks and suggestions for the hand check
│   ├── finalise_universe.py, finalise_expansion.py   the first 68 and the 44 added on 8 Nov 2026
│   ├── build_broad_universe.py, draft_broad_products.py, finalise_broad.py   S&P 500 + Nasdaq-100
│   ├── wikidata_products.py                    automatic product links (rejected for research; used by Discovery)
│   ├── build_ftse_universe.py                  FTSE 100
│   ├── fetch_pageviews.py                      daily views 2017-now, monthly totals, spikes capped
│   ├── fetch_clickstream.py                    clicks into every company page, Nov 2017-now
│   ├── fetch_prices.py, fetch_market_cap.py    prices, returns, factors; market cap in dollars
│   ├── fetch_earnings.py, fetch_descriptions.py   earnings dates and estimates; company descriptions
│   ├── build_features.py                       the monthly panel: attention features, controls, targets
│   ├── backtest.py, chart_sorts.py             portfolio sorts and their chart
│   ├── walk_forward.py, strategy.py            out-of-sample model; long-only strategy and live picks
│   ├── earnings_test.py, longer_test.py, clickthrough_tests.py   the first pre-registered tests
│   ├── replication.py, broad_tests.py, ftse_tests.py   replication on 44, 434 and 95 new companies
│   ├── threshold_test.py, attention_wave.py, short_strategy.py, earnings_drift.py   later strategies
│   ├── strategy_overview.py                    every strategy measured like a fund factsheet
│   ├── track_record.py                         follows the recorded live picks day by day
│   ├── trending.py, discovery.py               this week's attention jumps; listed companies in Wikipedia's top 1,000
│   └── update_all.py                           every step in order: what GitHub Actions runs each evening
├── .github/workflows/update.yml                daily update at 22:00 UTC, commits new data
├── app/streamlit_app.py                        the web app
├── data/mapping/                               company and product lists, checks, reviews, decisions
├── data/processed/                             page views, clickstream, prices, panel, results
├── charts/                                     saved charts
├── docs/                                       pre-registered plans and their results (start with docs/README.md)
├── LLM_LOG.md                                  record of AI tool use (required by the brief)
└── README.md
```

## Running it

Everything, in order (what GitHub Actions runs every evening):

```
python src/update_all.py
```

Each script says at the top what it reads and writes. The first full download
(page views since 2017 for about 1,000 pages, and the monthly clickstream,
about 50 GB streamed) takes several hours; after that each evening only fetches
what is new. The one-off tests (`threshold_test.py`, `attention_wave.py`,
`short_strategy.py`, `earnings_drift.py`) are run by hand.

To run the app on your own computer:

```
streamlit run app/streamlit_app.py
```

## Data sources

- Wikimedia Pageviews API (daily page views, 2017 onwards) and the daily list
  of the 1,000 most-read pages
- Wikipedia clickstream (monthly link clicks, from November 2017)
- Wikidata (links between pages and listed companies, for Discovery)
- yfinance (prices, share counts, earnings dates and analysts' estimates)
- Kenneth French data library (Fama-French 5 factors, momentum, T-bill rate)

## Known limits

- Companies that have left the S&P 500 since 2017 are missing, and past
  FTSE 100 membership was not available, which flatters some results (stated
  wherever it applies).
- Yahoo revises past prices, share counts and analysts' estimates; the tree
  model's results move by up to about ±0.3% a month as a result.
- Product lists are today's, used for the whole history.
