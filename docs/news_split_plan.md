# Good-news and bad-news attention surges (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked. Idea: Dominic's.

## Why

A surge in attention can come from good news (a hit product, strong results)
or bad news (a scandal, a crisis, a collapse). The attention-wave test
(`docs/attention_wave_plan.md`) found that the biggest surges were followed by
below-average returns; this test asks whether that comes from the bad-news
surges, and whether buying only good-news surges works.

The original "bad-news filter" (`docs/strategy_plan.md`, 68 companies) used
the share price over a whole month and made results worse: companies with
attention and a falling price tended to bounce back. This test looks at the
surge week itself.

## The rule

Exactly the attention-wave rule (weekly checks; buy when the company page's
views over the 7 days ending 2 days before the decision reach **E** times the
usual week, with at least 2,000 views in a usual week; sell when views are
back to normal or below half the peak; no maximum holding time; equal amounts;
the S&P 500 when nothing is held; 0.1% trading costs; only companies in the
S&P 500 at the time), with one addition at the moment of buying:

- **Price move in the surge week:** the company's share-price change over the
  same 7 days as the attention window (last close on or before the window's
  end, against the last close on or before 7 days earlier), minus the S&P
  500's change over the same days.
- **Good-news surge:** price move above zero. **Bad-news surge:** at or below
  zero.

Two strategies, each in the six usual versions (E = 1.5, 2, 3; exit "normal"
or "half"):

1. **Buy only good-news surges** (the main test).
2. **Buy only bad-news surges** (reported alongside, to show which kind of
   surge drives the result).

Periods: 2017–2021 (decisions from March 2017) and 2022–2026.

## How it will be judged

- Return above the equal-weighted average of the companies in the index at
  the time, % a month (t), per version and period, and $100 became.
- **Buying good-news surges counts as working only if at least 4 of its 6
  versions beat the average company in both periods.**
- **Caveat, written in advance:** both periods were already used for the
  attention-wave test, so this split is tested on data that has been looked
  at. A pass would be encouraging but not conclusive; the only fully fresh
  test is the future.
- Run once and reported whatever the result.

## Results (added on 10 Nov 2026, after running `src/news_split.py` once)

Only companies in the S&P 500 at the time, after costs; return above the
average company, % a month (t), and $100 became (average company: $223 in
2017–2021, $166 in 2022–2026).

**Buying only good-news surges (price beat the market in the surge week)**

| Entry | Exit | 2017–2021 | 2022–2026 |
|---|---|---|---|
| 1.5× | normal | −0.60 (−2.0), $157 | +0.19 (0.4), $180 |
| 1.5× | half | −0.30 (−1.5), $189 | +0.06 (0.2), $172 |
| 2× | normal | −0.80 (−1.9), $139 | +0.75 (1.2), $237 |
| 2× | half | −1.06 (−1.9), $116 | +1.14 (1.1), $271 |
| 3× | normal | −0.75 (−1.2), $140 | +0.71 (0.8), $214 |
| 3× | half | −0.99 (−1.6), $119 | −0.27 (−0.4), $132 |

**Buying only bad-news surges (price lagged the market)**

| Entry | Exit | 2017–2021 | 2022–2026 |
|---|---|---|---|
| 1.5× | normal | −0.19 (−0.9), $199 | −0.24 (−0.7), $142 |
| 1.5× | half | −0.17 (−0.7), $199 | +0.28 (1.0), $196 |
| 2× | normal | −0.09 (−0.3), $209 | −0.17 (−0.3), $140 |
| 2× | half | +0.05 (0.1), $217 | −0.01 (0.0), $148 |
| 3× | normal | +0.15 (0.4), $241 | −1.04 (−1.4), $80 |
| 3× | half | −0.32 (−0.5), $175 | −0.66 (−0.6), $94 |

**Verdict, by the rule fixed in advance: it does not work.** Good-news surges
beat the average in 5 of 6 versions in 2022–2026 but in **none** of the 6 in
2017–2021, where every version did worse than the average (t close to −2 in
three of them).

**What it shows:** the effect of a surge reverses between the two periods.
In 2022–2026, companies whose attention surged on good news kept rising and
those surging on bad news kept falling (momentum); in 2017–2021, good-news
surges were followed by clear underperformance (reversal), and bad-news
surges by about average returns. Separating good from bad news does not give
a stable signal: which one pays depends on the period, which is what a
fragile, regime-dependent pattern looks like.

### Check: is 2017–2021 driven by the pandemic? (exploratory, 10 Nov 2026)

Dominic's question. Good-news surges, 2017–2021, return above the average
company, % a month (t), with the pandemic months left out:

| Entry | Exit | All months | Without Feb–Jul 2020 | Without 2020 | 2017–2019 only |
|---|---|---|---|---|---|
| 1.5× | normal | −0.60 (−2.0) | −0.82 (−2.6) | −0.82 (−2.3) | −0.83 (−1.8) |
| 1.5× | half | −0.30 (−1.5) | −0.46 (−2.3) | −0.58 (−2.7) | −0.38 (−1.5) |
| 2× | normal | −0.80 (−1.9) | −1.02 (−2.4) | −0.96 (−2.0) | −1.07 (−1.7) |
| 2× | half | −1.06 (−1.9) | −1.32 (−2.2) | −1.46 (−2.2) | −1.46 (−1.8) |
| 3× | normal | −0.75 (−1.2) | −1.05 (−1.7) | −0.87 (−1.3) | −0.97 (−1.1) |
| 3× | half | −0.99 (−1.6) | −1.17 (−1.8) | −1.40 (−2.1) | −0.95 (−1.4) |

**Reading:** the pandemic does not explain it. Leaving 2020 out makes the
good-news result *worse* in every version (0 of 6 beat the average in every
case); before 2020, buying companies after a good-news surge in attention
consistently lagged the average.

### Check: did the pandemic change how attention works? (exploratory, 10 Nov 2026)

Dominic's question: the pandemic changed investor behaviour (the retail
trading boom of 2020–2021), so perhaps the pattern changed then. Good-news
surges, return above the average company, % a month (t):

| Entry | Exit | Jan 2017 – Jan 2020 | Aug 2020 – Dec 2021 (retail boom) | Jan 2022 – Nov 2026 |
|---|---|---|---|---|
| 1.5× | normal | −0.82 (−1.8) | −0.83 (−2.5) | +0.19 (0.4) |
| 1.5× | half | −0.37 (−1.5) | −0.64 (−1.8) | +0.06 (0.2) |
| 2× | normal | −1.09 (−1.8) | −0.87 (−2.2) | +0.75 (1.2) |
| 2× | half | −1.41 (−1.8) | −1.14 (−1.4) | +1.14 (1.1) |
| 3× | normal | −1.13 (−1.3) | −0.87 (−2.1) | +0.71 (0.8) |
| 3× | half | −1.07 (−1.6) | −1.39 (−1.0) | −0.27 (−0.4) |

**Reading:** the retail boom straight after the pandemic looks like the years
*before* it (0 of 6 versions beat the average), not like 2022–2026 (5 of 6).
If there was a change in how attention works, it came in 2022, not with the
pandemic; with one later period to go on, it cannot be told apart from chance.

### The whole period, March 2017 to November 2026 (added on 10 Nov 2026, at Dominic's request)

The two periods joined (holdings restart in January 2022, which barely
matters). $100 became: average company $371, S&P 500 $375.

| Entry | Exit | Good-news surges | Bad-news surges |
|---|---|---|---|
| 1.5× | normal | −0.20 (−0.7), $283 | −0.22 (−1.0), $282 |
| 1.5× | half | −0.12 (−0.7), $324 | +0.06 (0.3), $391 |
| 2× | normal | −0.02 (0.0), $330 | −0.13 (−0.4), $293 |
| 2× | half | +0.05 (0.1), $315 | +0.02 (0.0), $320 |
| 3× | normal | −0.01 (0.0), $301 | −0.45 (−1.1), $193 |
| 3× | half | −0.62 (−1.3), $156 | −0.49 (−0.8), $164 |

Over nine years, buying good-news surges ends at about the average company or
below in every version (1 of 6 marginally ahead); the two periods cancel out.

## Follow-up: leave out companies that were already far ahead (written on 10 Nov 2026, after the results above, before running it)

**Idea (Dominic's):** a company whose shares have already soared gets
attention *because* of the soaring price (news reports about the rally), not
because of news about the company itself; buying it then is buying the rally
late.

**Rule, fixed before running:** as "buying only good-news surges" above, but
a surge is **not bought** if, over the 13 weeks before the surge week (from
13 weeks before the start of the attention window to its start), the company
beat the S&P 500 by **more than 20 percentage points**. Six versions as
before, 2017–2021 and 2022–2026, only companies in the S&P 500 at the time.

**Judged by the same rule:** it counts as working only if at least 4 of the
6 versions beat the average company in both periods. Because this is a
further rule tested on surges and years that have already been looked at, a
pass would be weak evidence; it is reported whatever the result.

### Follow-up results (added on 10 Nov 2026, after running `src/news_split.py --followup` once)

Good-news surges, leaving out companies more than 20 points ahead of the
S&P 500 over the previous 13 weeks. Above the average company, % a month (t),
and $100 became (average company: $223 in 2017–2021, $166 in 2022–2026, $371
over the whole period).

| Entry | Exit | 2017–2021 | 2022–2026 | Whole period |
|---|---|---|---|---|
| 1.5× | normal | −0.59 (−1.9), $158 | −0.24 (−0.6), $142 | −0.41 (−1.7), $225 |
| 1.5× | half | −0.30 (−1.5), $189 | −0.09 (−0.4), $158 | −0.19 (−1.2), $299 |
| 2× | normal | −0.75 (−1.8), $143 | −0.37 (−0.7), $127 | −0.56 (−1.6), $181 |
| 2× | half | −1.04 (−1.9), $117 | −0.18 (−0.2), $136 | −0.61 (−1.3), $160 |
| 3× | normal | −0.61 (−0.9), $151 | −1.20 (−1.3), $70 | −0.91 (−1.6), $106 |
| 3× | half | −0.96 (−1.5), $121 | −0.03 (0.0), $153 | −0.49 (−1.1), $185 |

**Verdict: it does not work, and it is worse than without the rule.** None
of the 6 versions beats the average company in either period (without the
rule: 5 of 6 in 2022–2026).

**What it shows:** the good-news result in 2022–2026 came almost entirely
from companies that were *already* far ahead, the momentum stocks of that
period. Taking them out removes the whole edge. So whatever worked there was
riding existing price momentum, not attention picking up something new; and
good-news surges in companies that had not already run up did worse than
the average in both periods.

## Second follow-up: leave out only clearly bad news (written on 10 Nov 2026, before running it)

**Idea (Dominic's):** counting every surge whose price lagged the market at
all as "bad news" is too strict: share prices move a little every week, so a
small dip is not news. Leave out only **clearly** bad news, and still leave
out companies that were already far ahead.

**Threshold, set from the data before running:** the typical (median) size of
a company's weekly move against the S&P 500, over all 276,822 company-weeks
from 2017, is 1.97%, so **clearly bad news = the share price fell more than 2
percentage points behind the S&P 500 in the surge week** (about a quarter of
all weeks).

**Rule:** buy every surge **except** clearly bad news (more than 2 points
behind the market that week) and companies already more than 20 points ahead
of the market over the previous 13 weeks. Everything else as before: six
versions, 2017–2021 and 2022–2026, only companies in the S&P 500 at the time,
judged by at least 4 of 6 versions beating the average company in both
periods. This is a further rule on surges and years already looked at, so a
pass would be weak evidence; it is reported whatever the result.

### Second follow-up results (added on 10 Nov 2026, after running `src/news_split.py --followup2` once)

Every surge except clearly bad news (more than 2 points behind the market in
the surge week) and companies already more than 20 points ahead. Above the
average company, % a month (t), and $100 became (average company: $223,
$166, and $371 over the whole period).

| Entry | Exit | 2017–2021 | 2022–2026 | Whole period |
|---|---|---|---|---|
| 1.5× | normal | −0.60 (−2.3), $158 | −0.11 (−0.3), $154 | −0.35 (−1.6), $243 |
| 1.5× | half | −0.31 (−1.8), $188 | −0.12 (−0.5), $156 | −0.21 (−1.5), $294 |
| 2× | normal | −0.75 (−2.1), $143 | −0.33 (−0.7), $132 | −0.54 (−1.8), $188 |
| 2× | half | −1.18 (−2.4), $108 | −0.19 (−0.3), $135 | −0.68 (−1.5), $146 |
| 3× | normal | −0.37 (−0.6), $174 | −1.61 (−1.5), $52 | −1.00 (−1.6), $90 |
| 3× | half | −0.79 (−1.3), $136 | −0.18 (−0.3), $141 | −0.48 (−1.1), $192 |

**Verdict: it does not work.** None of the 6 versions beats the average in
either period; in 2017–2021 three of them do significantly worse (t −2.1 to
−2.4).

**Overall, across the good-news / bad-news tests:** once companies already
riding a price rally are taken out, buying on a surge in attention does
*worse* than holding the average company, whether the surge comes with good
news or with anything short of clearly bad news. The only version that ever
looked good (good-news surges, 2022–2026) was price momentum in disguise.
