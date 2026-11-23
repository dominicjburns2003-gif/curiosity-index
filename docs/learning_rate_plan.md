# Learning-rate sensitivity of the tree model (pre-registered)

Written on 23 November 2026, before any of this was coded or run, and
committed so the date can be checked.

## Why

At the pitch on 18 November 2026 the professor asked why the learning rate
is 0.05 and suggested varying it. The model's settings (`walk_forward.py`:
learning rate 0.05, 200 trees, depth 3, at least 100 rows per leaf, L2 1.0)
were fixed before any test and never tuned, so that no setting could be
chosen because it happened to work on the test years.

This check asks a narrower question: **does the conclusion depend on the
learning rate?** It is not a search for a better setting. Whatever the
result, the main result stays the one with 0.05, the setting fixed in
advance.

## What is run

The live strategy exactly as in `broad_tests.py` ("members at the time:
top 100"): the "products" features, all US companies the site follows,
walk-forward (train to November of the year before, predict each year from
2022), then each month the model's top 100 among companies that were in the
S&P 500 at the time, equal amounts, 0.1% trading costs, against the average
of those companies. Only the model settings below change; everything else,
including the data, is the same for every run.

**A. Learning rate, 200 trees (the main question):**
0.01, 0.025, 0.05, 0.1, 0.2.

**B. Learning rate and number of trees together** (each pair moves the
prediction by the same total, learning rate x trees = 10, so this separates
"smaller steps" from "fewer total steps"):
0.01 x 1,000 trees, 0.025 x 400, 0.05 x 200 (the same run as in A),
0.1 x 100, 0.2 x 50.

That is 9 different runs. For each: the average monthly return above the
average company (and its t-statistic, as in `broad_tests.py`), what $100
became for the strategy and the average company, and the model's average
monthly rank correlation between prediction and next month's return among
the companies it could pick (the information coefficient, IC).

## How it will be judged (fixed now)

- **The conclusion is robust to the learning rate** if no run has a
  t-statistic of 1.96 or more for the return above the average company.
- With 9 runs, one may pass 1.96 by chance. A run that passes would be
  reported, but counted as significant only at t of 2.77 or more (5%
  divided by 9, Bonferroni). Even then it would not replace 0.05: a setting
  chosen after seeing the test years would need its own live test.
- Run once and reported whatever the result.

The baseline (0.05, 200 trees) is recomputed in the same run, so all 9 rows
use the same, latest data; it can differ slightly from the figure in the
pitch, which used the data as of mid-November.
