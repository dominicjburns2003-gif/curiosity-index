# CLAUDE.md: Curiosity Index project brief

This file explains the whole project to Claude Code. Read it at the start of every session.

---

## 1. Who I am and how to work with me

- **Me:** Dominic Burns, Master in Finance student (Financial Markets track) at emlyon business school, Lyon. Economics graduate (University of Glasgow, 2025). Native English speaker.
- **Coding level:** beginner. I understand econometrics, regressions, portfolio sorts and data cleaning from my economics dissertations, but I have little programming experience. You will write most of the code.
- **Machine:** MacBook Air (Apple Silicon). Python through Anaconda; I use PyCharm. The project lives in `~/PycharmProjects/curiosity-index`.
- **Language:** Python only, not R. I want to get good at one language.

**How I want you to work:**

1. **Explain everything in plain English.** After writing or changing a script, give me a short explanation of what it does and why, written so I could repeat it to my professor. I have to present and defend this work myself.
2. **Work in small steps that each produce something visible:** a CSV, a chart, a printed summary. Run the code and check the output before moving on.
3. **Check results for sense,** not just that the code runs. Flag anything suspicious (impossible values, gaps, a backtest that looks too good).
4. **Ask before big decisions,** such as changing the research design, the company universe or the deadline plan. Make small technical decisions yourself and tell me what you chose.
5. **Keep it simple.** Prefer readable code over clever code. Use pandas, matplotlib or plotly, requests, scikit-learn or LightGBM, and Streamlit. Avoid heavy frameworks.
6. **Update `LLM_LOG.md` at the end of each session** with one line: date | tool | what I asked | what you produced | leave the last column ("what I checked / changed") for me to fill in. The course requires declaring all LLM use.
7. **Never fake data or results.** If something can't be fetched or doesn't work, say so.

---

## 2. The course and what is required

- **Course:** Machine Learning for Factor Investing (Prof. Guillaume Coqueret, emlyon). Individual project; projects that overlap too much with a classmate's fail.
- **The object:** something an outsider (professor, recruiter) can open, ideally online at a URL. Ours is a **public Streamlit app, updated automatically**. A self-updating dataset also counts.
- **Three deliverables:**
  1. **Oral pitch** in session 7: 5 minutes, **3 slides** (date to be confirmed).
  2. **The object:** the app URL plus the GitHub repository.
  3. **Written report, 2–5 pages:** how it was built, sample prompts, which AI tools were used, problems met and how they were solved, limitations, and extensions not done for lack of time.
- **Deadline:** app URL and report on Brightspace by **31 December 2026**.
- **Grading:** originality, quality, difficulty and ambition.
- **Rule 1 of the brief:** LLMs help, not replace. Declare when and how they were used. Hence the LLM log and the plain-English explanations.

---

## 3. The project in one paragraph

**Curiosity Index** (*"When people wonder who makes it, does the stock move?"*) tracks Wikipedia attention for about 75 listed companies at three levels: views of the **company's own page**, views of its **products' pages**, and the **click-through**, meaning the share of product readers who click on to the company page. Existing tools track only company pages. The research question is:

> **Do product attention and product-to-company click-through predict stock returns (or volatility) beyond company-page attention and standard risk factors?**

The output is a live app that each month ranks the companies into long and short groups, explains why, and shows honestly, out of sample, whether the strategy would have worked.

---

## 4. Why it is original (the gap)

**Existing tools track company-page Wikipedia views only:**
- TrendSpider has a page-views indicator for about 1,500 US stocks, a spike scanner, and a simple Apple backtest.
- AltIndex shows Wikipedia views among about 25 alternative-data signals and combines them into a black-box "AI Score".
- Brain's dataset on QuantConnect gives a daily "buzz" score for about 1,000 US stocks, from 2023.
- Quiver Quantitative sells retail alternative data with a Python package.

**Academic backing:**
- **Da, Engelberg & Gao (2011), "In Search of Fundamentals":** Google searches for a firm's *products* predict revenue surprises and announcement returns. This is our closest reference: same idea with Google, not Wikipedia.
- **Pyun (2024), "The Wikipedia Effect", *Economics Letters*:** rising *company*-page views predict higher returns, and a long-short portfolio earns returns not explained by standard factors.
- **Da, Engelberg & Gao (2011), "In Search of Attention":** attention spikes raise prices short term, followed by partial reversal.
- **Moat et al. (2013), *Scientific Reports*:** Wikipedia views of large US companies tended to rise before market falls.

**The gap:** nobody (as far as we found) combines **Wikipedia product pages mapped to companies** with **product-to-company click-through**, live. Why Wikipedia rather than Google Trends: it gives actual view counts rather than a relative 0–100 index, it is free and unlimited, it goes back to 2015, and it is easy to automate.

**Key idea for the report:** product readers are mostly consumers and patients, not investors. Product views measure **demand**; company views measure **investor and news attention**. The gap between the two, and the share of consumers who go looking for the company, is the signal.

---

## 5. Data sources and technical notes

### 5.1 Pageviews (daily), already working in `src/fetch_pageviews.py`
- Endpoint: `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{Article_Title}/daily/{YYYYMMDD}/{YYYYMMDD}`
- `agent=user` excludes known bots. Data available from July 2015; **we use 2017 onwards**.
- Send a descriptive `User-Agent` header and stay well under the rate limits (about 0.5 s between calls is fine).
- **Redirects:** a redirect title (e.g. "Ozempic" → "Semaglutide") only counts people who arrived via that name. Track the **target article**. Resolve redirects with the MediaWiki API (`action=query&redirects=1`).
- **Article renames:** pages get moved over time. Check title history for the main articles.

### 5.2 Clickstream (monthly)
- Files: `https://dumps.wikimedia.org/other/clickstream/YYYY-MM/clickstream-enwiki-YYYY-MM.tsv.gz`
- Columns: `prev` (where the reader came from), `curr` (the page reached), `type` (`link`, `external`, `other`), `n` (count).
- Pairs with **10 or fewer clicks a month are removed** for privacy, so niche products drop out.
- Files are large. **Stream them and keep only our pairs; never commit raw files to Git.**
- Use **2017 onwards**, because methods changed in 2015–16.
- **Release lag:** a month's file appears after the month ends, so month *t* clickstream can only be used for predictions from month *t+1* onwards.
- **Main metric:**
  `conversion_rate = clicks(product page → company page) / product page views (same month)`
- **Optional extra feature ("bad attention"):** the share of a company page's incoming clicks that come from negative-news pages (recalls, lawsuits, scandals), compared with clicks coming from its product pages.

### 5.3 Product → company mapping (Wikidata, then a hand check)
- Query Wikidata with SPARQL (`https://query.wikidata.org/sparql`) for products whose maker or owner is a listed company. Useful properties: **P176** manufacturer, **P178** developer, **P1716** brand, **P127** owned by, **P749** parent organisation, and **P414** stock exchange with qualifier **P249** ticker symbol.
- Follow parent chains up to the listed company (e.g. Instagram → Meta).
- Use Wikidata IDs, not names, to avoid ambiguity (Apple the fruit vs. Apple Inc.).
- Export to `data/mapping/products_to_companies.csv` and **hand-check the final universe** (I do this; you prepare it).
- **Start with a hand-built list of about 50–75 companies** so we have something working quickly. Wikidata automation is an upgrade.

### 5.4 Prices and factors
- Stock prices: `yfinance` (daily, adjusted close). Free data has **survivorship bias**; note it as a limitation and choose companies listed throughout 2017–2026.
- Fama-French factors (market, size, value, momentum, and the 5-factor set): Kenneth French's data library, free CSV downloads.

---

## 6. The universe

- About **75 US-listed companies with well-known consumer-facing products** (e.g. Novo Nordisk → Ozempic/Wegovy/semaglutide; Apple → iPhone; Nintendo → Nintendo Switch; Tesla → Model Y; Nike → Air Jordan).
- Criteria: listed in the US throughout 2017–2026; at least one product page with meaningful monthly views; the product article links to the company article, which the clickstream needs.
- Keep the list fixed once chosen. **No scope creep** until the whole pipeline works end to end.

---

## 7. Methodology

All work is at **monthly frequency** per company (a panel of company × month).

### 7.1 Features (computed only from information available at the time)
- **Abnormal company attention:** this month's company-page views vs. its own trailing 6-month average, in standard deviations.
- **Product attention growth:** change in total views across the company's products.
- **Conversion rate**, and its change vs. last month (lagged one month for the release delay).
- **Gap:** product attention rising while company attention stays flat.
- **Controls:** past 12-month return excluding the last month (momentum), market cap (size), recent volatility.

### 7.2 Targets
- Main: **next-month return** relative to the market, or its cross-sectional rank.
- Second: **next-month volatility**, in case attention predicts the size of moves rather than their direction.

### 7.3 Tests, from simple to advanced
1. **Portfolio sorts:** each month, split stocks into **3 groups** on one signal (not 5, because the universe is small). Long the top group, short the bottom one, equal-weighted. Report average next-month return per group, the long-short spread and its **t-statistic**.
2. **Alpha:** regress long-short returns on the Fama-French factors. Is there return left over?
3. **ML model:** gradient-boosted trees (LightGBM or scikit-learn's `HistGradientBoostingRegressor`) predicting next-month return rank from all features.
4. **Walk-forward (out of sample):** train on 2017–2021, predict 2022; retrain including 2022, predict 2023; and so on. **The model must never see future data.**
5. **Compare three versions:** company only → + product attention → + click-through. **The difference between them is the project's answer.**
6. **Explanations:** SHAP values per stock, giving one-line reasons for the app.
7. **Realism:** subtract trading costs (e.g. 0.1% per trade) and report results net of costs. Also show a long-only version (top group vs. market).

### 7.4 Look-ahead traps (check every time)
- Clickstream for month *t* is only usable from month *t+1*.
- Features at the end of month *t* use data up to month *t* only; returns are measured over month *t+1*.
- The product mapping uses today's Wikidata, which is a limitation to state in the report.
- Never tune the model on the test years.

### 7.5 Possible outcomes (all are fine)
- The signal works, and the app is a live strategy.
- It predicts volatility, not direction, and the app becomes a "turbulence watchlist".
- It adds nothing beyond company attention. That is still a finding (consumer curiosity is already priced in), and the app remains a unique live dataset. **Report honestly either way.**

---

## 8. The app (Streamlit), five pages

1. **This month's signals:** all companies ranked into Long / Neutral / Short groups, each with a one-line reason (e.g. "Semaglutide views +40% vs. normal; click-through to Novo Nordisk at a 12-month high").
2. **Company deep dive:** one timeline showing company views, each product's views, the click-through rate and the share price, with big spikes labelled; plus a SHAP breakdown of the score.
3. **Trending products:** this week's biggest jumps in product attention, with the parent company and ticker.
4. **Does it work?:** the out-of-sample backtest vs. the market, net of costs; a **signal report card** with one row per signal (long-short return, t-stat, alpha, hit rate); and the comparison of the three versions.
5. **Method and limits:** how it works, its weaknesses, and when it was last updated.

Disclaimer on every page: research project, not investment advice.

---

## 9. Architecture

```
Wikimedia Pageviews API (daily) ─┐
Clickstream files (monthly)  ────┤
Wikidata (mapping, rarely)   ────┼──► GitHub Actions (scheduled) ──► data files in repo ──► Streamlit app (public URL)
yfinance prices (daily)      ────┘     fetch → compute signals → retrain monthly
```

**Suggested repository layout:**
```
curiosity-index/
├── CLAUDE.md, README.md, LLM_LOG.md, requirements.txt, .gitignore
├── config.py                  # dates, universe file path, settings
├── data/
│   ├── mapping/               # products_to_companies.csv (hand-checked)
│   ├── raw/                   # downloads (ignored by Git if large)
│   └── processed/             # monthly panel, signals, backtest results
├── src/
│   ├── fetch_pageviews.py
│   ├── fetch_clickstream.py
│   ├── build_mapping.py
│   ├── fetch_prices.py
│   ├── build_features.py
│   ├── backtest.py            # sorts, alpha, walk-forward ML
│   └── update_all.py          # what GitHub Actions runs
├── app/
│   └── streamlit_app.py
├── charts/
└── .github/workflows/update.yml
```

- **Automation:** GitHub Actions runs `update_all.py` daily (views, prices) and monthly (clickstream, retraining) and commits the processed outputs. Streamlit Community Cloud (free) serves the app from the repository.
- Keep committed data small (processed files only). Add a `.gitignore` for raw dumps.

---

## 10. Roadmap (revised, starting 5 November 2026)

| Phase | Dates | Done when… |
|---|---|---|
| 1. Setup | 5–9 Nov | Git and GitHub set up; first data pull works; chart of Novo Nordisk vs. Semaglutide exists |
| 2. Data pipeline | 10–23 Nov | Hand-checked universe of ~75 companies and products; pageviews 2017–now; clickstream pairs extracted; prices downloaded; monthly panel built |
| 3. Signals and model | 24 Nov – 7 Dec | Portfolio sorts, t-stats, Fama-French alpha; walk-forward ML; comparison of the three versions; results charts |
| 4. App and automation | 8–17 Dec | Streamlit app with five pages deployed at a public URL; GitHub Actions updating it. **Feature freeze 17 Dec** |
| 5. Report | 18–31 Dec | 2–5 page report and LLM log; submit by 31 Dec |

**Session 7 pitch (date TBC):** by then have the idea, the data sources, and at least one real chart (slide 1: "people don't read about Novo Nordisk, they read about Ozempic").

**Fallbacks if behind:** cap the universe at 50; use 3 groups; drop Wikidata automation; make volatility the headline result if direction is weak. Start deploying early with a dummy page.

---

## 11. Limitations to keep in mind (for the report)

- Wikipedia readers are not all investors; a click doesn't prove investment intent.
- English Wikipedia skews towards US and UK readers.
- The clickstream threshold (more than 10 clicks a month) removes small products.
- Survivorship bias in free price data.
- The product mapping uses today's Wikidata, not historical mappings.
- The universe is small (about 75), so results are noisy; report confidence intervals.

---

## 12. Current status

- ✅ Project folder created with README, LLM log and requirements.
- ✅ `src/fetch_pageviews.py` written (Novo_Nordisk, Semaglutide, and the Ozempic redirect, 2017 to yesterday → `data/pageviews_novo_nordisk.csv` and `charts/novo_nordisk_attention.png`). Tested with dummy data only; **first real run still to do**.
- ⬜ Git repository and GitHub not yet set up.
- ⬜ Email to the professor to confirm the subject (Dominic to check whether it was sent).

**Next session should:** run `src/fetch_pageviews.py` for real and check the chart makes sense; set up Git and a GitHub repository (with a `.gitignore`); then start Phase 2 by drafting the company and product universe.
