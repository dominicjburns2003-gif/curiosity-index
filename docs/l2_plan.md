# L2-penalty sensitivity of the tree model (pre-registered)

Written on 23 November 2026, after the learning-rate check
(`learning_rate_plan.md`) and before any of this was coded or run, and
committed so the date can be checked.

## Why

The second of the model's settings the professor's question points to. The
L2 penalty (`l2_regularization` in scikit-learn) shrinks each leaf's
adjustment towards zero: roughly, a leaf's value is the sum of its rows'
errors divided by (number of rows + L2) instead of by the number of rows.
The model uses L2 = 1.0, fixed before any test. Because every leaf already
has at least 100 rows, L2 = 1 should change almost nothing; only penalties
of the order of the leaf sizes (hundreds to thousands of rows) can matter.

As before, this asks whether the conclusion depends on the setting, not
which setting is best. The main result stays the one with L2 = 1.

## What is run

The live strategy exactly as in `learning_rate_test.py` (top 100 among S&P
500 members at the time, Jan 2022 onwards, learning rate 0.05, 200 trees,
depth 3, at least 100 rows per leaf), changing only L2:

**0, 1 (fixed in advance), 10, 100, 1,000, 10,000.**

That is 6 runs. For each: the average monthly return above the average
company and its t-statistic, what $100 became, the information coefficient
(IC), and, to show how much the penalty actually holds the model back, the
**spread of the predictions** (the average over months of the standard
deviation of the model's predictions across companies).

## How it will be judged (fixed now)

- **The conclusion is robust to L2** if no run has a t-statistic of 1.96 or
  more for the return above the average company.
- A run that passes would be reported, but counted as significant only at t
  of 2.64 or more (5% divided by 6, Bonferroni), and would not replace L2 = 1
  without its own live test. Together with the 9 learning-rate runs, 14
  settings have now been tried, which is noted with the results.
- Expected beforehand: L2 of 0, 1 and 10 give almost the same result, and
  the prediction spread only shrinks clearly from 100 upwards.
- Run once and reported whatever the result.
