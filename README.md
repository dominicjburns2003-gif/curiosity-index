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
├── src/        Python scripts
├── data/       downloaded data (CSV files)
├── charts/     saved charts
├── LLM_LOG.md  record of AI tool use (required by the brief)
└── README.md
```

## Running step 1

From this folder:

```
python src/fetch_pageviews.py
```

It downloads daily page views since 2017 for Novo Nordisk, Semaglutide and the
"Ozempic" redirect, saves them to `data/pageviews_novo_nordisk.csv` and draws
`charts/novo_nordisk_attention.png`.

## Data sources

- Wikimedia Pageviews API (daily page views, from July 2015)
- Wikipedia clickstream (monthly link clicks) - coming next
- Wikidata (product to company mapping) - coming next
- yfinance (stock prices) - coming next
