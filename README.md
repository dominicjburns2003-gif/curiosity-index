# Curiosity Index

*When people wonder who makes it, does the stock move?*

A self-updating app that tracks Wikipedia attention for listed companies at three levels:

1. **Company attention**: views of the company's own page (e.g. Novo Nordisk)
2. **Product attention**: views of its products' pages (e.g. Semaglutide / Ozempic)
3. **Click-through**: the share of product readers who click on to the company page

Research question: do product attention and click-through predict stock returns
beyond company attention and standard risk factors?

Course project, Machine Learning for Factor Investing, emlyon business school (2026).

**Live app:** https://curiosity-index.streamlit.app/ (early version)

## Project structure

```
curiosity-index/
├── src/
│   ├── wiki_api.py            shared helpers for Wikimedia (polite requests, daily views)
│   ├── check_universe.py      automatic checks on a company/product list
│   ├── prepare_review.py      keep/drop/fix/decide suggestions for the hand check
│   ├── finalise_universe.py   applies the decisions -> products_to_companies.csv
│   ├── finalise_expansion.py  adds the 44 companies of the November 2026 expansion
│   ├── fetch_pageviews.py     daily views 2017-now, monthly totals with spikes capped
│   ├── fetch_clickstream.py   clicks into every company page, Nov 2017-now
│   ├── fetch_prices.py        share prices, monthly returns, Fama-French factors
│   ├── fetch_market_cap.py    monthly market cap from cleaned share counts
│   ├── build_features.py      the monthly panel: attention features, controls, targets
│   ├── backtest.py            portfolio sorts (3 groups), long-short t-stats, alpha
│   ├── chart_sorts.py         chart of the sorts
│   ├── chart_novo_pitch.py    pitch chart: Novo Nordisk vs. Semaglutide
│   ├── walk_forward.py        out-of-sample model, three versions compared, net of costs
│   ├── strategy.py            long-only strategy, pre-registered versions, live picks record
│   ├── fetch_earnings.py      earnings dates and analysts' estimates
│   ├── earnings_test.py       does product attention predict earnings surprises?
│   ├── longer_test.py         the same tests over a longer stretch, from 2020
│   ├── track_record.py        follows the recorded live picks day by day
│   ├── clickthrough_tests.py  click-through: volatility and level tests
│   ├── trending.py            this week's biggest jumps in product attention
│   ├── replication.py         the same tests on the 44 new companies
│   └── update_all.py          runs every step: what GitHub Actions runs each morning
├── .github/workflows/
│   └── update.yml             daily update at 06:00 UTC, commits new data
├── app/
│   └── streamlit_app.py       the web app
├── data/
│   ├── mapping/               universe draft, checks, review and final list
│   └── processed/             page views, clickstream, prices, panel, results
├── charts/                    saved charts
├── docs/                      pre-registered plans (strategy, earnings, click-through, replication) and their results
├── LLM_LOG.md                 record of AI tool use (required by the brief)
└── README.md
```

## Running the pipeline

From this folder, in this order:

```
python src/fetch_pageviews.py
python src/fetch_clickstream.py
python src/fetch_prices.py
python src/fetch_market_cap.py
python src/build_features.py
python src/backtest.py
python src/walk_forward.py
python src/strategy.py
python src/fetch_earnings.py
python src/earnings_test.py
python src/longer_test.py
python src/track_record.py
python src/clickthrough_tests.py
python src/trending.py
python src/replication.py
python src/chart_sorts.py
```

Or all of them at once (what GitHub Actions runs every morning):

```
python src/update_all.py
```

Each script says at the top what it reads and writes. The clickstream download
takes several hours the first time; after that it only fetches new months.

To run the app on your own computer:

```
streamlit run app/streamlit_app.py
```

## Data sources

- Wikimedia Pageviews API (daily page views, from July 2015; we use 2017 onwards)
- Wikipedia clickstream (monthly link clicks, available from November 2017)
- yfinance (stock prices and share counts for market cap)
- Kenneth French data library (Fama-French 5 factors and momentum)
