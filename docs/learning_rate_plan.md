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

## Results (added on 23 Nov 2026, after running `src/learning_rate_test.py` once)

Jan 2022 to Sep 2026, 57 months, the model's top 100 among S&P 500 members
at the time, after costs, against the average of those companies ($100 became
$169). IC: average monthly rank correlation between the model's prediction and
next month's return.

**A. Learning rate, 200 trees**

| Learning rate | Above average company, a month (t) | $100 became | IC |
|---|---|---|---|
| 0.01 | +0.22% (1.50) | $188 | +0.008 |
| 0.025 | +0.16% (1.03) | $182 | +0.006 |
| **0.05 (fixed in advance)** | **+0.17% (1.01)** | **$183** | **+0.007** |
| 0.1 | +0.11% (0.81) | $178 | +0.006 |
| 0.2 | +0.07% (0.57) | $174 | +0.006 |

**B. Learning rate x trees = 10**

| Learning rate x trees | Above average company, a month (t) | $100 became | IC |
|---|---|---|---|
| 0.01 x 1,000 | +0.17% (1.00) | $183 | +0.003 |
| 0.025 x 400 | +0.17% (0.98) | $183 | +0.004 |
| **0.05 x 200** | **+0.17% (1.01)** | **$183** | **+0.007** |
| 0.1 x 100 | +0.15% (0.94) | $181 | +0.006 |
| 0.2 x 50 | +0.14% (0.93) | $180 | +0.004 |

**Verdict, by the rule fixed in advance: the conclusion is robust to the
learning rate.** No run reaches t 1.96 (the highest is 1.50), so no setting
from 0.01 to 0.2 turns the strategy into one that beats the average company
significantly. The baseline matches the published figure for this strategy
(`broad_summary.csv`: +0.165% a month, t 1.01, $183).

**Reading, with caution (9 runs, none significant):**

- In A, a higher learning rate broadly does worse: from +0.22% at 0.01 to
  +0.07% at 0.2 (0.025 and 0.05 are level). That is the expected sign of overfitting: bigger steps let
  later trees chase noise in the training years.
- In B, where smaller steps come with more trees so the total adjustment is
  the same, the results are almost identical (+0.14% to +0.17%). So what
  matters is mainly how far the model is allowed to move from the average in
  total, not the size of each step.
- Read together: the most cautious model (0.01 with 200 trees, which barely
  moves from the average) did best, and the more freedom the model had, the
  less it earned. That fits the project's main finding that the signal is
  weak: the less the model tries to learn, the less noise it picks up.
- The ICs are all small (0.003 to 0.008): whatever the setting, the model's
  ranking is only very slightly better than chance.
