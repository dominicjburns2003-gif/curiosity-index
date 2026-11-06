# Earnings announcement test (pre-registered)

Written on 6 November 2026, **before** downloading the earnings data or running
anything below, and committed so the date can be checked.

## Question

Does a surge in curiosity about a company's **products** in the weeks before it
reports its results predict how the share price reacts to those results?

This is the setting where product attention is most likely to matter. Da,
Engelberg and Gao (2011) found that Google searches for a firm's products
predict its revenue surprises and its share-price reaction at earnings time. If
lots of people are reading about a product, sales may be strong, and the market
may not have fully priced that in before the company announces it.

## Data

- **Earnings dates** and analysts' EPS estimates from Yahoo Finance
  (`yfinance`, `get_earnings_dates`), for the 68 companies. Announcements from
  January 2018 (a year-on-year comparison needs 2017 data) to the latest date.
- A company is included only if it has **at least 10 announcements** in that
  period; the others are listed and left out.
- **Prices:** the adjusted daily prices already in `data/processed/prices_daily.csv`.

## Measures (fixed now)

For an announcement on day D:

- **Product attention surge** (the signal): log of the company's total product
  page views over days D−35 to D−6, minus the log of the same 30 days one year
  earlier. Year on year, so seasonal products (toys at Christmas, ice cream in
  summer) are compared with the same season. The window ends 6 days before the
  announcement so it does not include previews of the results. Daily views are
  capped for one-day spikes the same way as everywhere else. A product counts
  only if it had views in both windows.
- **Company attention surge** (control): the same measure for the company page.
- **Gap**: product surge minus company surge.

Outcomes:

1. **Main outcome: the announcement reaction**, the stock's return from the
   close two trading days before D to the close one trading day after D, minus
   the S&P 500 (SPY) over the same days. This covers results released before
   the open or after the close.
2. **Second outcome: beat rate**, whether reported EPS beat analysts' estimate
   (where the estimate is available).

## Tests

1. **Sort:** in each calendar quarter, rank the announcements on product
   attention surge and split them into thirds. Compare the average
   announcement reaction of the top and bottom thirds; average across
   quarters, with a t-statistic over quarters.
2. **Same sort on the gap** (products ahead of the company).
3. **Regression:** announcement reaction on product surge and company surge
   together, pooled, with standard errors clustered by quarter, to see whether
   product attention matters beyond company attention.
4. The same three for the **beat rate**.

The main result is test 1 on the main outcome. Everything is run once and
reported whatever the result. No windows, thresholds or periods are changed
after seeing results; any change would be reported as a new, separate test.
