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

## Results (added on 23 Nov 2026, after running `src/l2_test.py` once)

Jan 2022 to Sep 2026, 57 months, top 100 among S&P 500 members at the time,
after costs, against the average of those companies ($100 became $169).
Learning rate 0.05, 200 trees. Spread: average monthly standard deviation of
the predictions across companies (in next-month rank units, 0 to 1).

| L2 | Above average company, a month (t) | $100 became | IC | Spread |
|---|---|---|---|---|
| 0 | +0.17% (1.05) | $183 | +0.006 | 0.0186 |
| **1 (fixed in advance)** | **+0.17% (1.01)** | **$183** | **+0.007** | **0.0186** |
| 10 | +0.11% (0.69) | $178 | +0.002 | 0.0185 |
| 100 | +0.12% (0.71) | $178 | +0.004 | 0.0175 |
| 1,000 | +0.12% (0.72) | $178 | +0.007 | 0.0157 |
| 10,000 | +0.10% (0.56) | $175 | +0.007 | 0.0139 |

**Verdict, by the rule fixed in advance: the conclusion is robust to the L2
penalty.** No run reaches t 1.96 (the highest is 1.05, at L2 = 0). With the 9
learning-rate runs, 14 settings have now been tried and none is significant.

**Reading, with caution (6 runs, none significant):**

- As expected, L2 = 0 and L2 = 1 give the same result: with at least 100
  rows in every leaf, a penalty of 1 changes almost nothing.
- Also as expected, the penalty only holds the model back clearly from
  about 100 upwards, and even 10,000 narrows the spread of predictions by
  only a quarter, because most leaves hold thousands of rows.
- **Not expected:** L2 = 10 hardly changes the predictions (spread 0.0186
  to 0.0185) but lowers the return from +0.17% to +0.11% a month. The
  predictions are so close together (a spread of about 2 rank points) that
  a tiny change reorders which companies fall just inside or outside the
  top 100. A difference of 0.05% a month between settings is therefore
  within what the choice of picks at the margin can produce, and should not
  be read as one setting being better.
- Unlike the learning rate, more shrinkage here did not help: the most
  penalised model did slightly worst. Both checks agree only on what
  matters: no setting makes the strategy significant.
