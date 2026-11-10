# Does attention add anything to company fundamentals? (pre-registered)

Written on 10 November 2026, before any accounts were downloaded or any of it
was coded, and committed so the date can be checked.

## Why

The obvious question from any investor: does Wikipedia attention tell you
anything that standard company fundamentals (profits, valuation, quality) do
not? Fundamentals-based factors such as value and profitability are decades
old, so a model using them may well do better; the question here is whether
**adding attention improves on fundamentals alone**.

## Data

- **Accounts:** the SEC's EDGAR database (companyfacts API, US-GAAP figures),
  for the US companies in the index. Only **annual reports (10-K)** are used,
  and each figure only from the **date it was filed**, so in every month the
  model sees only accounts that had been published by then (point in time).
  Where a year was later restated, the figure as first filed is used.
  Companies filing under other rules (e.g. foreign companies' 20-F, such as
  Novo Nordisk or Toyota) have no figures and their fundamentals are missing,
  which the model treats as missing. UK companies are not included.
- **Four measures** at each month end, from the latest annual report filed
  by then, with market value (in dollars) at that month end:
  1. **Earnings yield:** net income ÷ market value (the inverse of P/E)
  2. **Book-to-market:** shareholders' equity ÷ market value
  3. **Gross profitability:** gross profit ÷ total assets (gross profit, or
     revenue minus cost of revenue where gross profit is not reported)
  4. **Asset growth:** total assets ÷ total assets a year earlier − 1
  Each is ranked against the other companies that month, like every feature.

## Models

All three use the same tree model, settings and walk-forward training
(retrained each January on earlier years only, first test year 2022), on all
US companies:

- **F (fundamentals):** the four measures + the three standard stock
  measures (past-year return, size, volatility)
- **A (attention):** the current live model (four attention measures + the
  same three stock measures)
- **F + A:** all eleven

Each buys its **top 100** each month in equal amounts, counting only
companies in the S&P 500 at the time, after 0.1% trading costs, from January
2022 picks to the latest month, as the live strategy does.

## How it will be judged

- **Main question:** does F + A beat F? The monthly difference in return
  between the two, % a month, with its t. **Attention adds something** if it
  is positive with t of 2 or more; **weak support** if positive with t below
  2; otherwise it adds nothing.
- Also reported: each model against the average company (equal-weighted,
  index members at the time) and the S&P 500, and $100 became.
- Only one out-of-sample period is available (2022–2026), because the model
  needs earlier years to learn from. Run once and reported whatever the
  result. Nothing in the live strategy changes because of it.

## Results (added on 10 Nov 2026, after running `src/fundamentals_test.py` once)

Accounts for 523 of the 546 US companies (38,930 annual figures from SEC
EDGAR, each used only from its filing date). Top 100 each month among the
companies in the S&P 500 at the time, picks from January 2022 to September
2026 (57 months), after costs. Above the average company, % a month (t).

| Model | Above the average company | Above the S&P 500 | $100 became |
|---|---|---|---|
| F: fundamentals + stock measures | +0.05 (0.4) | −0.05 (−0.2) | $172 |
| A: attention + stock measures (the live model) | +0.21 (1.2) | +0.11 (0.4) | $187 |
| F + A: both | +0.08 (0.6) | −0.02 (−0.1) | $175 |
| *Average company* | | | *$169* |
| *S&P 500* | | | *$179* |

**Main question: does adding attention to fundamentals help? F + A minus F:
+0.03% a month (t 0.3).** By the rule fixed in advance that is "weak support"
(positive, t below 2), but at t 0.3 it is indistinguishable from zero:
**attention adds nothing measurable to fundamentals.**

**Also:** the fundamentals themselves did not beat the average company over
2022–2026 either (+0.05%, t 0.4); value and profitability had a weak period
among large US companies. Adding fundamentals to the attention model made it
slightly worse (+0.08% against +0.21%), within noise. Model A reproduces the
live strategy's figures exactly, as a check that the set-up matches.
