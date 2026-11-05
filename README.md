# Curiosity Index

*When people wonder who makes it, does the stock move?*

A self-updating app that tracks Wikipedia attention for listed companies at three levels:

1. **Company attention**: views of the company's own page (e.g. Novo Nordisk)
2. **Product attention**: views of its products' pages (e.g. Semaglutide / Ozempic)
3. **Click-through**: the share of product readers who click on to the company page

Research question: do product attention and click-through predict stock returns
beyond company attention and standard risk factors?

Course project, Machine Learning for Factor Investing, emlyon business school (2026).

## Project structure

```
curiosity-index/
├── src/
│   ├── wiki_api.py            shared helpers for Wikimedia (polite requests, daily views)
│   ├── check_universe.py      automatic checks on a company/product list
│   ├── prepare_review.py      keep/drop/fix/decide suggestions for the hand check
│   ├── finalise_universe.py   applies the decisions -> products_to_companies.csv
│   ├── fetch_pageviews.py     daily views 2017-now for the whole universe
│   ├── fetch_clickstream.py   clickstream test (Novo Nordisk)
│   └── chart_novo_pitch.py    slide-1 chart: Novo Nordisk vs. Semaglutide
├── data/
│   ├── mapping/               universe draft, checks, review and final list
│   └── processed/             page views (daily and monthly), clickstream rows
├── charts/                    saved charts
├── LLM_LOG.md                 record of AI tool use (required by the brief)
└── README.md
```

## Running the pipeline

From this folder:

```
python src/fetch_pageviews.py
```

Downloads daily page views since 2017 for all 68 companies and 140 products in
`data/mapping/products_to_companies.csv` (renamed pages have their old titles
added up) and writes `data/processed/pageviews_daily.csv` and
`data/processed/pageviews_monthly.csv`.

## Data sources

- Wikimedia Pageviews API (daily page views, from July 2015; we use 2017 onwards)
- Wikipedia clickstream (monthly link clicks, available from November 2017)
- yfinance (stock prices)
- Kenneth French data library (risk factors) - coming next
