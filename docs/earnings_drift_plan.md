# Attention and the drift after earnings surprises (pre-registered)

Written on 10 November 2026, before any of it was coded or run, and
committed so the date can be checked.

## Why

Earlier tests asked whether attention predicts **which way** a share price
goes; it does not, reliably. This test asks something different: whether
attention changes **how fast news is priced in**.

After a company beats or misses analysts' forecasts, its share price tends to
keep drifting in the same direction for weeks: *post-earnings-announcement
drift* (Ball and Brown, 1968; Bernard and Thomas, 1989), one of the most
studied patterns in finance, usually explained by investors under-reacting.
Research suggests the under-reaction is larger when investors are paying
less attention: results released on Fridays drift more (DellaVigna and
Pollet, 2009), as do results released on days with many other announcements
(Hirshleifer, Lim and Teoh, 2009). Wikipedia views measure attention to each
company directly.

**Hypothesis:** the drift after an earnings surprise is **larger when the
company draws little attention around the announcement** than when it draws
a lot.

## Data

- **Announcements:** every quarterly result in `data/processed/earnings_dates.csv`
  (Yahoo Finance) from January 2017 with both an analyst estimate and a
  reported figure, for companies that were **in the S&P 500 at the time**
  (`data/mapping/index_membership.csv`).
- **Surprise:** (reported EPS − estimated EPS) ÷ share price at the close two
  trading days before the announcement (the standard scaling, so a 5-cent miss
  means more for a $20 stock than a $500 one).
- **Attention at the announcement:** views of the company's own page (all its
  titles, spikes capped as everywhere else) on the day before, the day of and
  the day after the announcement, against its usual level: the average daily
  views from 35 to 6 days before. Measured as the ratio of the two.
- **Drift:** the share's return from the close **2 trading days after** the
  announcement (so the first reaction, whatever time of day the results came
  out, is excluded) to the close **60 trading days** after (about three
  months), minus the S&P 500's return over the same days.

## The test

Within each calendar quarter (so every comparison is between announcements of
the same season):

1. Split the announcements into **thirds by surprise** (most negative, middle,
   most positive) and into **halves by attention** (below and above the
   quarter's median attention ratio).
2. **Drift spread** = average drift of the most positive third minus the most
   negative third, separately in the low-attention and high-attention halves.
3. **Main result: the difference, low-attention spread minus high-attention
   spread**, averaged over quarters, with its t across quarters. The
   hypothesis predicts it is **positive**.

Also reported: the overall drift spread (to check the basic drift exists in
these data), the same with drift measured to 20 trading days, and everything
for 2017–2021 and 2022–2026 separately.

## How it will be judged

- **Supported** only if the main result is positive over the whole period
  with t of 2 or more, **and** positive in both 2017–2021 and 2022–2026.
- **Weak support** if positive in both periods but with t below 2.
- Otherwise, not supported.
- Run once and reported whatever the result.

Known limits, accepted in advance: Yahoo's estimates are a consensus that is
sometimes revised later (161 were in one week of November 2026), and its
announcement dates are occasionally a day out; companies that left the index
are missing.
