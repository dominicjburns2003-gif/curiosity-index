"""
Curiosity Index - the web app (pre-pitch version).

Three tabs, all read from the files the pipeline writes to data/processed/:
  Explorer        - one company: attention, click-through and share price
  Results         - the portfolio sorts and the out-of-sample model, honestly
  Method & data   - how it works, sources and limits

The monthly signal board, trending products and the full backtest page come later.

Run it from the project folder:
    streamlit run app/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
GITHUB_URL = "https://github.com/dominicjburns2003-gif/curiosity-index"

# Fixed colour order: the company page first, then its products (at most 4)
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
CLICK_COLOUR = "#52514e"  # click-through and price each get their own colour,
PRICE_COLOUR = "#6250d6"  # so they are never confused with a page
GRID = "rgba(128,128,128,0.2)"
# Hover boxes: small and see-through, so they cover as little of the chart as possible
HOVER_LABEL = dict(bgcolor="rgba(255,255,255,0.82)", bordercolor="#dbe3ee",
                   font=dict(size=11, family="Inter, sans-serif", color="#0f1b2d"))
DISCLAIMER = "Student research project. Not investment advice."
# Wikipedia titles must start with a capital letter, so restore the real names
TITLE_FIXES = {"IPhone": "iPhone", "IPad": "iPad", "IMac": "iMac", "IPod": "iPod"}


def pretty(article: str) -> str:
    """A Wikipedia title as people write the name."""
    first, _, rest = article.replace("_", " ").partition(" ")
    return " ".join(filter(None, [TITLE_FIXES.get(first, first), rest]))

SIGNAL_LABELS = {
    "company_abn": "Unusual company attention",
    "company_growth": "Rising company attention",
    "product_growth": "Rising product attention",
    "gap": "Products ahead of company",
    "conversion_vs_normal": "Unusual click-through",
    "conversion_change": "Rising click-through",
}
SIGNAL_MEANINGS = {
    "company_abn": "The company's page is much busier than usual",
    "company_growth": "Views of the company's page are rising",
    "product_growth": "Views of its product pages are rising",
    "gap": "Its products are getting more attention than the company",
    "conversion_vs_normal": "More product readers than usual click through to the company",
    "conversion_change": "Click-through is up on the month before",
}
VERSION_LABELS = {
    "company": "Company attention only",
    "products": "+ product attention",
    "clicks": "+ product attention and click-through",
}
VERSION_COLOURS = {"company": "#9aa5b1", "products": "#2a78d6", "clicks": "#eb6834"}


def verdict(t: float) -> tuple[str, str]:
    """Plain-English verdict from a t-statistic, and its style class."""
    if t >= 2:
        return "Likely real", "yes"
    if t >= 1.5:
        return "Promising, not proven", "maybe"
    if t >= 0.5:
        return "Positive but weak", "weak"
    return "No effect", "no"


def chip(t: float) -> str:
    label, style = verdict(t)
    return f'<span class="ci-chip {style}">{label}</span>'


def html_table(headers: list[str], rows: list[list[str]], numeric: set[int]) -> str:
    """A simple styled table; columns in `numeric` are right-aligned."""
    head = "".join(f'<th class="{"num" if i in numeric else ""}">{h}</th>' for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i in numeric else ""}">{c}</td>'
                                    for i, c in enumerate(row)) + "</tr>" for row in rows)
    return f'<div class="ci-table-wrap"><table class="ci-table"><tr>{head}</tr>{body}</table></div>'

st.set_page_config(page_title="Curiosity Index", page_icon=":material/query_stats:", layout="wide")

# Charts: no zoom or pan, so touching a chart on a phone shows the values
# instead of zooming in; and no floating toolbar
CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False}

# Page styling: Streamlit's defaults plus a hero banner, white cards on a light
# grey page, and a footer. Kept in one place so the look is easy to change.
PAGE_CSS = """
<style>
/* Page: a light blue-grey background, so the navy banner, tab bar and footer
   frame white cards, and the whole page shares one colour scheme */
.stApp { background: #eef2f7; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 3.4rem; padding-bottom: 1rem; }

/* Banner */
.ci-hero { background: linear-gradient(135deg, #0f1b2d 0%, #16325a 60%, #1f4f8f 100%);
           color: #fff; border-radius: 16px; padding: 40px 44px 30px; margin-bottom: 18px; }
.ci-eyebrow { font-size: .76rem; letter-spacing: .12em; text-transform: uppercase;
              color: #9ec5f4; font-weight: 600; margin-bottom: 14px; }
.ci-hero h1 { color: #fff; font-size: 2.7rem; font-weight: 700; margin: 0 0 12px;
              line-height: 1.1; padding: 0; letter-spacing: -.02em; }
.ci-lead { font-size: 1.1rem; color: #d7e3f4; max-width: 760px; margin: 0 0 26px; line-height: 1.6; }
.ci-lead b { color: #fff; font-weight: 600; }
.ci-stats { display: flex; flex-wrap: wrap; gap: 14px 44px;
            border-top: 1px solid rgba(255,255,255,.16); padding-top: 20px; }
.ci-stat .n { display: block; font-size: 1.4rem; font-weight: 600; color: #fff; }
.ci-stat .l { font-size: .82rem; color: #9fb3cc; }

/* Tab bar: a navy strip matching the banner */
[data-testid="stTabs"] [role="tablist"] { background: #16325a; border-radius: 12px; padding: 6px; gap: 4px; }
[data-testid="stTabs"] [role="tablist"]::after { display: none; }
[data-testid="stTab"] { border-radius: 8px; padding: 8px 18px; border: none !important;
                        box-shadow: none !important; height: auto; }
[data-testid="stTab"] p { color: #c9d6e8; font-size: .95rem; font-weight: 600; }
[data-testid="stTab"][aria-selected="true"] { background: rgba(255,255,255,.14); }
[data-testid="stTab"][aria-selected="true"] p { color: #fff; }
[data-testid="stTab"]:hover p { color: #fff; }

/* Content cards: white, with a blue accent line along the top */
[class*="st-key-card"] { background: #fff; border-radius: 12px; padding: 22px 24px 14px;
                         border: 1px solid #dbe3ee; border-top: 3px solid #2a78d6;
                         box-shadow: 0 1px 3px rgba(15,27,45,.05); }
[class*="st-key-card"] h2, [class*="st-key-card"] h3 { color: #16325a; }

/* Results summary: one row per question, with a plain verdict label */
.ci-answer { display: flex; justify-content: space-between; align-items: center; gap: 18px;
             padding: 14px 0; border-bottom: 1px solid #e6ebf2; }
.ci-answer:last-child { border-bottom: none; }
.ci-q { font-weight: 600; color: #0f1b2d; }
.ci-d { font-size: .9rem; color: #4a5568; margin-top: 3px; line-height: 1.45; }
.ci-chip { white-space: nowrap; font-size: .8rem; font-weight: 600; padding: 5px 12px; border-radius: 999px; }
.ci-chip.no { background: #eef1f5; color: #4a5568; }
.ci-chip.maybe { background: #fdf1dc; color: #8a5a00; }
.ci-chip.weak { background: #e6eef8; color: #1f4f8f; }
.ci-picks { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 6px 18px;
            margin: 8px 0 12px; font-size: .9rem; }
.ci-picks span { color: #6b7280; font-size: .82rem; }
.ci-chip.yes { background: #e3f3e8; color: #1d6b3a; }

/* Results tables */
.ci-table-wrap { overflow-x: auto; margin: 6px 0 14px; }
.ci-table { width: 100%; border-collapse: collapse; font-size: .9rem; }
.ci-table th { text-align: left; color: #4a5568; font-weight: 600; font-size: .76rem;
               text-transform: uppercase; letter-spacing: .05em; padding: 10px 12px;
               border-bottom: 2px solid #e6ebf2; white-space: nowrap; }
.ci-table td { padding: 12px; border-bottom: 1px solid #eef1f5; vertical-align: middle; color: #0f1b2d; }
.ci-table tr:last-child td { border-bottom: none; }
.ci-table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.ci-table .sub { display: block; color: #6b7280; font-size: .83rem; margin-top: 2px; }

/* Company picker: a highlighted panel so visitors notice it straight away */
.st-key-picker { background: #16325a; border-radius: 12px; padding: 18px 22px 20px; }
.ci-picker-title { color: #fff; font-size: 1.2rem; font-weight: 700; margin-bottom: 2px; }
.ci-picker-hint { color: #c9d6e8; font-size: .9rem; margin-bottom: 10px; }
.st-key-company_picker [role="group"] { background: #fff; border: 2px solid #9ec5f4; border-radius: 10px;
    min-height: 54px; box-shadow: 0 2px 10px rgba(0,0,0,.18); }
.st-key-company_picker [role="group"]:hover, .st-key-company_picker [role="group"]:focus-within {
    border-color: #fff; }
.st-key-company_picker input[role="combobox"] { font-size: 1.1rem; font-weight: 600; color: #0f1b2d;
    height: 50px; }
.st-key-company_picker button svg { width: 26px; height: 26px; color: #2a78d6; }

/* Key-number cards: a light navy tint */
[data-testid="stMetric"] { background: #e6eef8; border-color: #cfdcec !important; }
[data-testid="stMetricLabel"] p { color: #16325a; font-weight: 600; }
[data-testid="stMetricValue"] { color: #0f1b2d; }
.st-key-metrics_row [data-testid="stMetricValue"] { font-size: 1.75rem; }
.st-key-metrics_row [data-testid="stMetricValue"] *, .st-key-metrics_row [data-testid="stMetricLabel"] * {
    white-space: normal; overflow: visible; text-overflow: clip; }

/* Drop-down sections */
[data-testid="stExpander"] details { background: #fff; border-color: #dbe3ee; }

/* Footer: a navy strip that closes the page */
.ci-footer { margin-top: 36px; padding: 22px 26px; border-radius: 12px; background: #0f1b2d;
             color: #9fb3cc; font-size: .85rem; display: flex; justify-content: space-between;
             flex-wrap: wrap; gap: 8px 24px; }
.ci-footer a { color: #9ec5f4; text-decoration: none; }

@media (max-width: 720px) {
  .ci-hero { padding: 26px 22px 20px; }
  .ci-hero h1 { font-size: 2rem; }
  .ci-lead { font-size: 1rem; }
  .ci-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 20px; }
  .ci-stat .n { font-size: 1.2rem; }
  .ci-answer { flex-direction: column; align-items: flex-start; gap: 8px; }
  [class*="st-key-card"] h3 { font-size: 1.3rem; }
  [class*="st-key-card"] { padding: 16px 14px 8px; }
  [data-testid="stTab"] { padding: 8px 10px; }
  /* Key numbers in a 2 x 2 grid on phones instead of one long column */
  .st-key-metrics_row [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: 10px; }
  .st-key-metrics_row [data-testid="stColumn"] { flex: 1 1 calc(50% - 10px) !important;
                                                 min-width: calc(50% - 10px) !important; }
  .st-key-metrics_row [data-testid="stMetricValue"] { font-size: 1.25rem; }
}
</style>
"""


DATA_FILES = {
    "universe": PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv",
    "views": DATA_DIR / "pageviews_monthly.csv",
    "daily": DATA_DIR / "pageviews_daily.csv",
    "prices": DATA_DIR / "prices_daily.csv",
    "conversion": DATA_DIR / "conversion_monthly.csv",
    "sorts": DATA_DIR / "sorts_summary.csv",
    "model": DATA_DIR / "walk_forward_summary.csv",
    "model_monthly": DATA_DIR / "walk_forward_monthly.csv",
    "strategy": DATA_DIR / "strategy_summary.csv",
    "strategy_monthly": DATA_DIR / "strategy_monthly.csv",
    "live_picks": DATA_DIR / "live_picks_log.csv",
    "earnings": DATA_DIR / "earnings_test_summary.csv",
    "longer": DATA_DIR / "longer_test_summary.csv",
    "track_daily": DATA_DIR / "track_record_daily.csv",
    "track_monthly": DATA_DIR / "track_record_monthly.csv",
    "clickthrough": DATA_DIR / "clickthrough_tests_summary.csv",
    "trending": DATA_DIR / "trending.csv",
    "replication": DATA_DIR / "replication_summary.csv",
    "replication_monthly": DATA_DIR / "replication_monthly.csv",
    "last_update": DATA_DIR / "last_update.json",
}
CLICKTHROUGH_PLAN_URL = GITHUB_URL + "/blob/main/docs/clickthrough_tests_plan.md"
EARNINGS_PLAN_URL = GITHUB_URL + "/blob/main/docs/earnings_test_plan.md"
REPLICATION_PLAN_URL = GITHUB_URL + "/blob/main/docs/expansion_replication_plan.md"
PLAN_URL = GITHUB_URL + "/blob/main/docs/strategy_plan.md"
DEV_END = "2024-12"  # last month of the development period (see src/strategy.py)


@st.cache_data
def load_data(versions: tuple) -> dict:
    """Read the data files once and keep them in memory. The argument is the
    files' last-changed times: when the daily update (or a push) changes a
    file, it changes, so the cache is refreshed instead of serving old data."""
    data = {}
    for name, path in DATA_FILES.items():
        if name == "daily":
            data[name] = pd.read_csv(path, usecols=["date"])["date"].max()
        elif name == "last_update":
            data[name] = pd.read_json(path, typ="series")
        elif name == "prices":
            data[name] = pd.read_csv(path, index_col="date", parse_dates=True)
        else:
            data[name] = pd.read_csv(path)
    return data


@st.cache_data(ttl=900, show_spinner=False)
def latest_prices(tickers: tuple) -> pd.DataFrame:
    """Latest price and its date for each ticker from Yahoo (about 15 minutes
    delayed during trading), kept for 15 minutes. For display only: every test
    uses daily closing prices. Empty if Yahoo does not answer."""
    try:
        bars = yf.download(list(tickers), period="5d", interval="1d", progress=False,
                           auto_adjust=True, threads=True)["Close"].ffill()
    except Exception:
        return pd.DataFrame(columns=["price", "date"])
    last = bars.iloc[-1].dropna()
    return pd.DataFrame({"price": last, "date": bars.index[-1].normalize()})


def price_status(day: pd.Timestamp) -> str:
    """'live' wording during US trading hours, otherwise the close it refers to."""
    now = pd.Timestamp.now(tz="America/New_York")
    trading = now.weekday() < 5 and (9, 30) <= (now.hour, now.minute) < (16, 0)
    if trading and day.date() == now.date():
        return f"live, about {now - pd.Timedelta(minutes=15):%-H:%M} New York time (15-minute delay)"
    return f"at the close on {day:%-d %b %Y}"


data = load_data(tuple(path.stat().st_mtime for path in DATA_FILES.values()))
universe, views, prices = data["universe"], data["views"], data["prices"]
last_day = pd.Timestamp(data["daily"])
# When the daily update last ran (it runs every evening, even when there is no new
# data, e.g. at weekends); the newest data itself lags by a day or two
checked = pd.Timestamp(data["last_update"]["checked_at_utc"])

# ---- Header -------------------------------------------------------------------
st.html(PAGE_CSS)
st.html(f"""
<div class="ci-hero">
  <div class="ci-eyebrow">Research project &middot; emlyon business school</div>
  <h1>Curiosity Index</h1>
  <p class="ci-lead">Does public curiosity about a company's products tell us anything about its
     stock? The index follows English Wikipedia at three levels: views of a <b>company's own
     page</b>, views of its <b>products' pages</b>, and the share of product readers who
     <b>click through</b> to the company. It then tests whether these predict the following
     month's returns.</p>
  <div class="ci-stats">
    <div class="ci-stat"><span class="n">{universe['ticker'].nunique()}</span><span class="l">US companies</span></div>
    <div class="ci-stat"><span class="n">{len(universe)}</span><span class="l">product pages</span></div>
    <div class="ci-stat"><span class="n">Since {views['month'].min()[:4]}</span><span class="l">daily attention data</span></div>
    <div class="ci-stat"><span class="n">Updated {checked:%-d %b %Y}</span><span class="l">data to {last_day:%-d %b}; checked every evening</span></div>
  </div>
</div>
""")

explorer, trending_tab, results, track, method = st.tabs(
    ["Explorer", "Trending", "Results", "Track record", "Method and data"])

# ---- Explorer -------------------------------------------------------------------
with explorer:
    companies = universe.drop_duplicates("ticker").sort_values("company")
    labels = {r.ticker: f"{r.company} ({r.ticker})" for r in companies.itertuples()}
    default = list(labels).index("NVO") if "NVO" in labels else 0
    with st.container(key="picker"):
        st.markdown('<div class="ci-picker-title">Choose a company to explore</div>'
                    f'<div class="ci-picker-hint">{len(labels)} companies. Click the box below, or start '
                    'typing a name or ticker to search.</div>', unsafe_allow_html=True)
        ticker = st.selectbox("Company", list(labels), index=default, format_func=labels.get,
                              label_visibility="collapsed", key="company_picker")

    pages = views[views["ticker"] == ticker].copy()
    pages["month"] = pd.to_datetime(pages["month"])
    clicks = data["conversion"][data["conversion"]["ticker"] == ticker].copy()
    clicks["month"] = pd.to_datetime(clicks["month"])
    price = prices[ticker].loc[str(pages["month"].min().year):].dropna()
    live = latest_prices((ticker,))
    if ticker in live.index and live.at[ticker, "date"] >= price.index[-1]:
        price.loc[live.at[ticker, "date"]] = live.at[ticker, "price"]  # today's latest price
    price_note = price_status(price.index[-1])

    # Key numbers for the latest complete month, each against its own recent past
    company_series = pages[pages["kind"] == "company"].groupby("month")["views"].sum(min_count=1).dropna()
    product_series = pages[pages["kind"] == "product"].groupby("month")["views"].sum(min_count=1).dropna()
    latest = company_series.index.max()

    def vs_normal(series: pd.Series) -> str:
        normal = series.iloc[-7:-1].mean()  # the 6 months before
        return f"{series.iloc[-1] / normal - 1:+.0%} vs normal"

    c1, c2, c3, c4 = st.container(key="metrics_row").columns(4)
    c1.metric("Company page", f"{company_series.iloc[-1]:,.0f} views",
              vs_normal(company_series), border=True)
    c2.metric("Product pages", f"{product_series.iloc[-1]:,.0f} views",
              vs_normal(product_series), border=True)
    if len(clicks) >= 2:
        change = (clicks["conversion"].iloc[-1] - clicks["conversion"].iloc[-2]) * 100
        c3.metric("Click-through rate", f"{clicks['conversion'].iloc[-1]:.2%}", f"{change:+.2f} pts", border=True)
    else:
        c3.metric("Click-through rate", "n/a", border=True)
    year_ago = price.loc[: price.index[-1] - pd.DateOffset(years=1)]
    c4.metric(f"Share price, {'live' if price_note.startswith('live') else 'last close'}",
              f"${price.iloc[-1]:,.2f}",
              f"{price.iloc[-1] / year_ago.iloc[-1] - 1:+.0%} in a year" if len(year_ago) else None,
              border=True)
    # Wikipedia's overall traffic moves too (it fell through 2026), so give the
    # typical company's change as a benchmark for the numbers above
    all_companies = views[views["kind"] == "company"].pivot_table(
        index="month", columns="ticker", values="views", aggfunc="sum")
    typical = (all_companies.iloc[-1] / all_companies.iloc[-7:-1].mean() - 1).median()
    normal_from, normal_to = (latest - pd.DateOffset(months=6)), (latest - pd.DateOffset(months=1))
    click_note = (f"Click-through: {clicks['month'].iloc[-1]:%B %Y}, change in percentage points from "
                  f"{clicks['month'].iloc[-2]:%B %Y}. " if len(clicks) >= 2 else "")
    st.caption(f"**Time frames.** Page views: {latest:%B %Y}, against their average over the 6 months "
               f"before ({normal_from:%B} to {normal_to:%B %Y}), shown as \"vs normal\". {click_note}"
               f"Share price: {price_note}; change over the 12 months to that date. For comparison, the "
               f"typical company page was {typical:+.0%} vs normal in {latest:%B}, as Wikipedia's overall "
               f"traffic changes too.")

    chart_card = st.container(key="card_chart")
    # Three stacked charts sharing ONE date axis, so the hover line and tooltip
    # cover all of them at the same date (not two y-axes on one chart, which
    # would let the scales suggest a link)
    fig = go.Figure()
    order = list(pages.loc[pages["kind"] == "company", "article"].unique()) + \
        sorted(pages.loc[pages["kind"] == "product", "article"].unique())
    for colour, article in zip(COLOURS, order):
        series = pages[pages["article"] == article]
        kind = series["kind"].iloc[0]
        name = "Company page" if kind == "company" else pretty(article)
        fig.add_trace(go.Scatter(
            x=series["month"], y=series["views"], name=name, mode="lines",
            line=dict(color=colour, width=3 if kind == "company" else 2),
            hovertemplate="%{y:.3s} views<extra>" + name + "</extra>",
        ))
    fig.add_trace(go.Scatter(
        x=clicks["month"], y=clicks["conversion"] * 100, name="Click-through", mode="lines",
        line=dict(color=CLICK_COLOUR, width=2), yaxis="y2",
        hovertemplate="%{y:.2f}%<extra>Click-through</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=price.index, y=price, name="Share price", mode="lines",
        line=dict(color=PRICE_COLOUR, width=1.5), yaxis="y3",
        hovertemplate="$%{y:,.2f}<extra>Share price</extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="Views a month (log)", type="log", dtick=1, gridcolor=GRID, domain=[0.52, 1]),
        yaxis2=dict(title="Click-through (%)", gridcolor=GRID, domain=[0.27, 0.46], rangemode="tozero"),
        yaxis3=dict(title="Share price ($)", gridcolor=GRID, domain=[0, 0.21]),
        xaxis=dict(showgrid=False, anchor="y3", hoverformat="%b %Y",
                   showspikes=True, spikemode="across", spikesnap="cursor",
                   spikedash="dot", spikethickness=1, spikecolor="#888"),
        hovermode="x unified", hoversubplots="axis", height=720,
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
        margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False, hoverlabel=HOVER_LABEL,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    with chart_card:
        st.markdown(f"**{labels[ticker]}**: attention, click-through and share price")
        st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)

    with st.expander("How to read this chart"):
        st.markdown(
            "- **Top:** monthly views on English Wikipedia by human readers, on a log scale so the "
            "company and its products (which can differ 100-fold) fit on one chart. Renamed pages "
            "have all their titles added up, and one-day spikes that look automated are capped.\n"
            "- **Middle:** of everyone who read the company's product pages that month, the share "
            "who clicked a link to the company's own page. Months with 10 clicks or fewer are "
            "hidden by Wikipedia, so they count as zero here.\n"
            "- **Bottom:** daily share price, adjusted for splits and dividends.\n"
            "- Hover (or tap, on a phone) anywhere to see all three at the same date. Seeing them move together does "
            "**not** show that one causes the other: that is what the **Results** tab tests."
        )

# ---- Trending ---------------------------------------------------------------------
with trending_tab:
    trend = data["trending"]

    shown = pd.concat([trend.head(12), trend.tail(6)])
    live = latest_prices(tuple(sorted(shown["ticker"].unique())))

    def latest_session(ticker: str) -> str:
        """Change on the latest trading day: live price (or last close) vs the close before."""
        if ticker not in live.index:
            return "n/a"
        day = live.at[ticker, "date"]
        before = prices.loc[prices.index < day, ticker].dropna()
        return f"{live.at[ticker, 'price'] / before.iloc[-1] - 1:+.1%}" if len(before) else "n/a"

    def trend_rows(df: pd.DataFrame) -> list[list[str]]:
        return [[f'{pretty(r.product)}<span class="sub">{r.company} ({r.ticker})</span>',
                 f"{r.views_week:,.0f}", f"{r.change:+.0%}", f"{r.company_change:+.0%}",
                 f"{r.price_change:+.1%}", latest_session(r.ticker)] for r in df.itertuples()]

    headers = ["Product", "Views, latest week", "vs usual week", "Company page vs usual week",
               "Share price, latest week", "Share price, latest day"]
    week_start, week_end = pd.Timestamp(trend["week_start"].iloc[0]), pd.Timestamp(trend["week_end"].iloc[0])
    usual_start, usual_end = week_start - pd.Timedelta(days=56), week_start - pd.Timedelta(days=1)
    price_from, price_to = pd.Timestamp(trend["price_from"].iloc[0]), pd.Timestamp(trend["price_to"].iloc[0])
    latest_day_label = (price_status(live["date"].max()) if len(live) else "not available right now")
    time_frames = (
        f"**Time frames.** Latest week: {week_start:%-d %b} to {week_end:%-d %b %Y} (the 7 most recent "
        f"days of Wikipedia data). Usual week: the average week over the 8 weeks before, "
        f"{usual_start:%-d %b} to {usual_end:%-d %b}. The company page column uses the same two "
        f"periods. Share price, latest week: close on {price_from:%-d %b} to close on {price_to:%-d %b}. "
        f"Share price, latest day: {latest_day_label}, against the previous close."
    )
    spy_week = (trend["price_change"] - trend["price_vs_market"]).iloc[0]
    week = f"{pd.Timestamp(trend['week_start'].iloc[0]):%-d %b} to {pd.Timestamp(trend['week_end'].iloc[0]):%-d %b %Y}"
    with st.container(key="card_trending"):
        st.subheader("Trending products this week")
        st.markdown(
            f"Product pages getting much more attention than usual: views from {week}, against the "
            f"average week over the 8 weeks before. The company page column shows whether interest "
            f"in the company itself is rising too, and the share price columns how its shares moved "
            f"over the same week and on the latest trading day."
        )
        st.markdown(time_frames)
        st.html(html_table(headers, trend_rows(trend.head(12)), numeric={1, 2, 3, 4, 5}))
        st.caption(f"The S&P 500 moved {spy_week:+.1%} over the latest week. Only the {len(trend)} product "
                   f"pages with at least 2,000 views in a usual week are included. Seasonal events show up "
                   f"too (for example sweets around Halloween).")

    with st.container(key="card_cooling"):
        st.subheader("Cooling off")
        st.html(html_table(headers, trend_rows(trend.tail(6).iloc[::-1]), numeric={1, 2, 3, 4, 5}))

    with st.container(key="card_trend_read"):
        st.subheader("How to read this")
        st.markdown(
            "- **A starting point for research, not a buy list.** A product taking off is a reason "
            "to look at the company, not proof that its shares will rise.\n"
            "- **Product rising, company flat** (for example WhatsApp while Meta's page is quiet) "
            "usually means consumer interest in the product. **Company rising more than its "
            "products** more often means news about the company itself, good or bad.\n"
            "- **Watch expectations.** This project's earnings test found that companies whose "
            "products drew much more attention than a year earlier beat analysts' estimates *less* "
            "often: analysts may already be expecting a lot.\n"
            "- Updated every evening, after the US market close. Not investment advice."
        )

# ---- Results ----------------------------------------------------------------------
with results:
    model = data["model"].set_index("version")
    sorts = data["sorts"].set_index("signal").loc[list(SIGNAL_LABELS)]
    strategy = data["strategy"]
    chosen = strategy.loc[strategy["chosen"], "version"].iloc[0]
    chosen_name = strategy.loc[strategy["chosen"], "name"].iloc[0]
    monthly = data["strategy_monthly"]
    run = monthly[monthly["version"] == chosen].sort_values("month").copy()
    run["excess"] = run["net"] - run["average_company"]
    excess_t = run["excess"].mean() / (run["excess"].std() / len(run) ** 0.5)
    first, last = pd.Period(run["month"].iloc[0]), pd.Period(run["month"].iloc[-1])

    # Users see one universe of 112 companies; how the results were built up (first
    # 68, then 44 more) is in the research detail sections lower down
    group = "All 112 companies"
    replication_monthly = data["replication_monthly"]
    group_runs = {
        "Original 68": run.assign(benchmark=run["average_company"]),
        "All 112 companies": replication_monthly[(replication_monthly["group"] == "all 112")
                                                 & (replication_monthly["detail"] == "trained on this group")],
        "44 new companies": replication_monthly[(replication_monthly["group"] == "new 44")
                                                & (replication_monthly["detail"] == "trained on this group")],
    }
    group_size = {"Original 68": 68, "All 112 companies": 112, "44 new companies": 44}[group]
    size_runs = {
        "Original 68": monthly[monthly["version"] == "A_size"],
        "All 112 companies": replication_monthly[(replication_monthly["group"] == "all 112")
                                                 & (replication_monthly["detail"] == "by size")],
        "44 new companies": replication_monthly[(replication_monthly["group"] == "new 44")
                                                & (replication_monthly["detail"] == "by size")],
    }
    shown_run = group_runs[group].sort_values("month").copy()
    shown_run["excess"] = shown_run["net"] - shown_run["benchmark"]
    shown_t = shown_run["excess"].mean() / (shown_run["excess"].std() / len(shown_run) ** 0.5)

    def answer(question: str, detail: str, t: float, improves: bool = True,
               label: str = "", style: str = "") -> str:
        if not label:
            label, style = verdict(t) if improves else ("No improvement", "no")
        return (f'<div class="ci-answer"><div><div class="ci-q">{question}</div>'
                f'<div class="ci-d">{detail}</div></div><span class="ci-chip {style}">{label}</span></div>')

    earnings = data["earnings"]
    beat_sort = earnings[(earnings["test"] == "sort") & (earnings["signal"] == "product_surge")
                         & (earnings["outcome"] == "beat")].iloc[0]
    reaction_sort = earnings[(earnings["test"] == "sort") & (earnings["signal"] == "product_surge")
                             & (earnings["outcome"] == "reaction")].iloc[0]
    dev = strategy[strategy["period"] == "development"].set_index("version")
    best_improved = dev.loc[["B", "C", "D"], "excess"].max()

    def growth_of_100(returns: pd.Series) -> float:
        return 100 * (1 + returns).prod()

    by_size = size_runs[group].sort_values("month")
    vs_spy = by_size["net"] - by_size["spy"]
    vs_spy_t = vs_spy.mean() / (vs_spy.std() / len(vs_spy) ** 0.5)
    replication = data["replication"]

    def replicated(group: str, test: str, detail: str) -> pd.Series:
        return replication[(replication["group"] == group) & (replication["test"] == test)
                           & (replication["detail"] == detail)].iloc[0]

    new_strategy = replicated("new 44", "strategy", "trained on this group")
    # The long-short research comparison for the selected group (company / + products / + clicks)
    if group == "Original 68":
        long_short = model[["long_short", "t_stat"]]
    else:
        name = {"All 112 companies": "all 112", "44 new companies": "new 44"}[group]
        long_short = (replication[(replication["group"] == name) & (replication["test"] == "long-short")]
                      .set_index("detail").rename(columns={"result": "long_short"})[["long_short", "t_stat"]])
    new_beat = replicated("new 44", "earnings", "beat: top minus bottom third")
    all_beat = replicated("all 112", "earnings", "beat: top minus bottom third")
    with st.container(key="card_summary"):
        st.subheader("The short answer so far")
        st.html(
            answer("Does buying the companies with the most product curiosity beat the average company?",
                   f"Buying the model's top third each month (no short selling, after trading costs) "
                   f"{'beat' if shown_run['excess'].mean() > 0 else 'trailed'} the average of the "
                   f"{group_size} companies by {abs(shown_run['excess'].mean()) * 100:.2f}% a month from "
                   f"{first + 1:%B %Y} to {last + 1:%B %Y}"
                   + (", but not by enough to rule out luck." if shown_t < 2 else "."),
                   shown_t)
            + answer("Does attention to products add anything to attention to the company?",
                     f"In the research test (buying the top third and selling the bottom third), a model "
                     f"using product attention did {long_short.loc['products', 'long_short'] * 100:+.2f}% a "
                     f"month, against {long_short.loc['company', 'long_short'] * 100:+.2f}% for company "
                     f"attention alone.", long_short.loc["products", "t_stat"],
                     long_short.loc["products", "long_short"] > long_short.loc["company", "long_short"])
            + answer("Does click-through from products to the company add anything?",
                     f"Adding click-through gave {long_short.loc['clicks', 'long_short'] * 100:+.2f}% a month, "
                     f"against {long_short.loc['products', 'long_short'] * 100:+.2f}% with product attention "
                     f"alone. Two further tests found it does not predict volatility "
                     f"either, and that high click-through companies only seemed to do worse because "
                     f"they are mostly consumer staples, which lagged from 2022.",
                     long_short.loc["clicks", "t_stat"],
                     long_short.loc["clicks", "long_short"] > long_short.loc["products", "long_short"])
            + answer("Does it beat the S&P 500?",
                     f"Weighted by company size, as most funds are, the picks turned $100 into "
                     f"${growth_of_100(by_size['net']):.0f}, against ${growth_of_100(by_size['spy']):.0f} "
                     f"for the S&P 500. Simply holding all {group_size} companies the same way made "
                     f"${growth_of_100(by_size['benchmark']):.0f}, so "
                     + ("most of the lead comes from the companies tracked, not the signal."
                        if growth_of_100(by_size['benchmark']) > growth_of_100(by_size['spy'])
                        and growth_of_100(by_size['net']) > growth_of_100(by_size['spy'])
                        else "the picks add nothing over the companies they are chosen from."),
                     vs_spy_t)
            + answer("Does product curiosity before results predict how they go?",
                     f"Yes, but not the way you might expect. Across {int(all_beat['events']):,} quarterly "
                     f"results, companies whose products drew much more attention than a year earlier "
                     f"beat analysts' estimates less often ({all_beat['top']:.0%} against "
                     f"{all_beat['bottom']:.0%}). The share price reaction was no different. The pattern "
                     f"was found in the first 68 companies and held in the 44 added later.",
                     all_beat["t_stat"], label=verdict(abs(all_beat["t_stat"]))[0],
                     style=verdict(abs(all_beat["t_stat"]))[1])
        )
        st.caption("Research results, updated monthly. Not investment advice.")

    with st.container(key="card_strategy"):
        st.subheader("The strategy")
        if chosen == "A":
            st.markdown(
                "At the end of every month:\n\n"
                "1. **Measure seven things for each company.** Four are about "
                "attention: whether the company's own Wikipedia page is unusually busy, whether "
                "views of it are rising, whether views of its product pages are rising, and whether "
                "its products are getting more attention than the company itself. Three are "
                "standard stock measures, so attention is not just standing in for something "
                "already known: the past year's share-price return, company size and recent "
                "volatility. Each is ranked against the other companies that month.\n"
                "2. **Turn them into one score per company** with a machine-learning model "
                "(gradient-boosted trees). The model learned how these measures related to the "
                "following month's return from past data only, and is retrained every January.\n"
                "3. **Buy the highest-scoring third** (37 of the 112 companies), in equal amounts "
                "(or, in the size-weighted version, in proportion to their market value).\n"
                "4. **Hold them for one month**, then repeat with the new scores. Trading costs of "
                "0.1% are paid on whatever changes."
            )
            st.markdown(
                "It does **not** sell anything short, and it does not use click-through or a "
                "bad-news filter: both were tested and made results worse."
            )
        else:
            st.markdown(f"Current version: **{chosen_name}**. See the plan linked below for details.")

    with st.container(key="card_growth"):
        st.subheader("What $100 would have become")
        weighting = st.segmented_control(
            "Invest in the picks", ["In equal amounts", "In proportion to company size"],
            default="In equal amounts", key="weighting") or "In equal amounts"
        size_weighted = weighting != "In equal amounts"
        shown = by_size if size_weighted else shown_run
        st.markdown(
            f"Following the strategy from {first + 1:%B %Y}: each month, buy the top third of the "
            f"{group_size} companies as ranked by the model, "
            + ("in proportion to their market value (no company above 15%), "
               if size_weighted else "in equal amounts, ")
            + f"after trading costs. Compared with holding all {group_size} companies the same way "
            "(the fair comparison) and with the S&P 500."

        )
        dates = pd.PeriodIndex(shown["month"], freq="M").to_timestamp(how="end").normalize() + pd.offsets.MonthEnd(1)
        start = dates[0] - pd.offsets.MonthEnd(1)
        lines = {
            "Strategy": (shown["net"], "#2a78d6", 3),
            (f"All {group_size} companies, by size" if size_weighted else f"All {group_size} companies, equal amounts"):
                (shown["benchmark"], "#9aa5b1", 2),
            "S&P 500": (shown["spy"], "#0f1b2d", 1.5),
        }
        growth = go.Figure()
        for name, (returns, colour, width) in lines.items():
            value = pd.concat([pd.Series([100.0]), 100 * (1 + returns.reset_index(drop=True)).cumprod()])
            growth.add_trace(go.Scatter(
                x=[start, *dates], y=value, name=name, mode="lines", line=dict(color=colour, width=width),
                hovertemplate="$%{y:.0f}<extra>" + name + "</extra>",
            ))
        growth.update_layout(
            yaxis=dict(title="Value of $100 ($)", gridcolor=GRID), xaxis=dict(showgrid=False, hoverformat="%b %Y"),
            hovermode="x unified", height=380, legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
            margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False, hoverlabel=HOVER_LABEL,
        )
        growth.update_xaxes(fixedrange=True)
        growth.update_yaxes(fixedrange=True)
        st.plotly_chart(growth, width="stretch", config=CHART_CONFIG)
        st.caption("Out of sample: the model behind each month's picks was trained only on earlier "
                   "years. Equal amounts compare with all 112 companies held equally; by size, with "
                   "all 112 weighted by market value (no company above 15%).")

    with st.container(key="card_picks"):
        live = data["live_picks"]
        pick_month = pd.Period(live["month"].max())
        current = live[live["month"] == live["month"].max()].sort_values("rank")
        names = universe.drop_duplicates("ticker").set_index("ticker")["company"]
        st.subheader(f"Current picks for {pick_month + 1:%B %Y}")
        st.html('<div class="ci-picks">' + "".join(
            f"<div>{names.get(t, t)} <span>{t}</span></div>" for t in current["ticker"]) + "</div>")
        recorded = pd.Timestamp(current["recorded_on"].iloc[0])
        timing = (f"recorded on {recorded:%-d %B %Y}, using data up to the end of {pick_month:%B}; "
                  f"the live record counts from the close on the next trading day, so no returns that "
                  f"had already happened are included")
        source = ("all 112 companies" if "all 112" in str(current["version"].iloc[0])
                  else "the first 68 companies (the live strategy covers all 112 from December 2026)")
        st.caption(f"Chosen at the end of {pick_month:%B %Y} from {source}, and {timing}. Each month's "
                   f"picks are added to a permanent record and never changed, so the strategy's live "
                   f"track record can be checked later. Not investment advice.")

    with st.expander("Research detail: how the strategy was developed (on the first 68 companies)"):
        st.markdown(
            f"The strategy was designed on the first 68 companies. Five changes were "
            f"[planned and written down]({PLAN_URL}) before any were tested; none beat the original "
            f"model over 2022 to 2024, so the original was kept. "
            f"Each version was run on 2022 to 2024 and the best one chosen by a fixed rule (highest "
            f"return above the average company, after costs). Only then was it checked on 2025 to 2026."
        )
        rows = []
        for version in ["A", "B", "C", "D", "B_no_filter", "B_1m", "A_size",
                        "A_3m", "A_quarter", "A_quarter_3m"]:
            d = strategy[(strategy["version"] == version) & (strategy["period"] == "development")].iloc[0]
            f = strategy[(strategy["version"] == version) & (strategy["period"] == "final")].iloc[0]
            name = d["name"] + (" (chosen)" if d["chosen"] else "")
            rows.append([f"<b>{name}</b>" if d["chosen"] else name,
                         f"{d['excess'] * 100:+.2f}%", f"{d['excess_t']:.1f}",
                         f"{f['excess'] * 100:+.2f}%", f"{f['excess_t']:.1f}"])
        st.html(html_table(["Version", "2022–24: vs the 68", "t", "2025–26: vs the 68", "t"],
                           rows, numeric={1, 2, 3, 4}))
        st.markdown(
            "- **The bad-news filter hurt.** Companies whose price was falling while their "
            "attention rose tended to bounce back the next month, so skipping them removed good picks.\n"
            "- **Comparing within sectors hurt**: part of the signal seems to come from picking whole "
            "sectors, such as consumer brands with viral products.\n"
            "- **Holding for 3 months** cut trading costs by more than half, but lowered returns.\n"
            "- The 1-month check looks best in 2025–26, but it lost in 2022–24 and was not a "
            "candidate, so choosing it now would be picking results after seeing them.\n"
            "- **Weighted by company size** (planned separately, after the S&P 500 comparison): "
            "behind the 68 companies weighted by size in 2022–24, ahead in 2025–26.\n"
            "- **Robustness checks** (also planned first): holding the chosen picks for 3 months, "
            "buying only the top quarter, or both. All beat the average company in both periods, "
            "so the small edge does not depend on these choices. Holding for 3 months also cuts "
            "trading costs from about 0.10% to 0.04% a month."
        )
        longer = data["longer"].set_index("version")
        equal = longer.loc["A, equal amounts (vs 68 equal)"]
        st.markdown(
            f"- **Longer test from {pd.Period(equal['first_month']):%B %Y}** ({int(equal['months'])} "
            f"months, also planned first): the same pattern, with a smaller edge: "
            f"{equal['result'] * 100:+.2f}% a month above the average company (t = {equal['t_stat']:.1f}). "
            f"Product attention still beats company attention alone, and click-through still adds "
            f"nothing. More months did not make the result more certain, so the edge, if real, is small."
        )

    with st.container(key="card_earnings"):
        st.subheader("Earnings announcements")
        all_reaction = replicated("all 112", "earnings", "reaction: top minus bottom third")
        beat_sort, reaction_sort = all_beat, all_reaction.rename({"result": "top_minus_bottom"})
        beat_sort = beat_sort.rename({"result": "top_minus_bottom"})
        st.markdown(
            f"The test [planned in advance]({EARNINGS_PLAN_URL}): for {int(beat_sort['events']):,} "
            f"quarterly results of the 112 companies, from {int(beat_sort['months'])} quarters since "
            f"2018, measure how much "
            f"attention the company's product pages got from 35 to 6 days before the results date, "
            f"compared with the same days a year earlier, then see how the results went. The share-price "
            f"reaction is measured from the close 2 trading days before the results to the close 1 day after."
        )
        thirds = ["Products quieter than a year ago", "About the same", "Products much busier"]
        beat_chart = go.Figure(go.Bar(
            x=thirds, y=[beat_sort["bottom"] * 100, beat_sort["middle"] * 100, beat_sort["top"] * 100],
            marker_color=["#9ec5f4", "#5598e7", "#1c5cab"],
            text=[f"{v:.1%}" for v in [beat_sort["bottom"], beat_sort["middle"], beat_sort["top"]]],
            textposition="outside", hovertemplate="%{y:.1f}% beat estimates<extra></extra>",
        ))
        beat_chart.update_layout(
            yaxis=dict(title="Share beating analysts' estimates (%)", range=[0, 100], gridcolor=GRID),
            height=300, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False, hoverlabel=HOVER_LABEL,
        )
        beat_chart.update_xaxes(fixedrange=True)
        beat_chart.update_yaxes(fixedrange=True)
        st.plotly_chart(beat_chart, width="stretch", config=CHART_CONFIG)
        st.markdown(
            f"- **More product buzz, fewer beats:** {beat_sort['top']:.1%} of companies with the busiest "
            f"product pages beat estimates, against {beat_sort['bottom']:.1%} of the quietest "
            f"(t = {beat_sort['t_stat']:.1f}), the opposite of what was expected. It was first found in "
            f"the first 68 companies and held in the 44 added later.\n"
            f"- **No difference in the share-price reaction** around the results "
            f"({reaction_sort['top_minus_bottom'] * 100:+.2f}%, t = {reaction_sort['t_stat']:.1f}).\n"
            "- A likely reading: analysts see the same buzz and raise their forecasts, sometimes too "
            "far, so beating them is harder; and the market, seeing both, is not surprised on average."
        )

    with st.expander("Research detail: checking the findings on companies the tests had never seen"):
        st.markdown(
            f"Every test was first designed on 68 companies. In November 2026, 44 more "
            f"companies with 92 product pages were added and checked by the same rules, and the "
            f"same tests were [planned in advance]({REPLICATION_PLAN_URL}) and run once on them, with "
            f"every setting unchanged. A finding counts as replicated if it points the same way."
        )

        def row(finding: str, original: str, detail_test: str, detail: str, pct: bool,
                original_value: float) -> list[str]:
            """One finding: its value in the original 68 and the new 44, and whether it replicates
            (same direction), worked out from the current numbers."""
            r = replicated("new 44", detail_test, detail)
            value = f"{r['result'] * 100:+.2f}% a month" if pct else f"{r['result'] * 100:+.1f} pts"
            if abs(r["t_stat"]) < 0.5:
                outcome = "Does not replicate (about zero)"
            elif (r["result"] > 0) != (original_value > 0):
                outcome = "Does not replicate (opposite direction)"
            elif abs(r["t_stat"]) >= 2:
                outcome = "Replicates strongly"
            elif abs(r["result"]) < abs(original_value) / 2:
                outcome = "Same direction, much smaller"
            else:
                outcome = "Replicates"
            return [finding, original, f"{value} (t = {r['t_stat']:.1f})", outcome]

        strategy_68 = run["excess"]
        st.html(html_table(
            ["Finding", "Original 68", "44 new companies", "Verdict"],
            [row("Strategy beats its own average", f"{strategy_68.mean() * 100:+.2f}% a month (t = {excess_t:.1f})",
                 "strategy", "trained on this group", True, strategy_68.mean()),
             row("Products ahead of company (single signal)",
                 f"{sorts.loc['gap', 'long_short'] * 100:+.2f}% a month (t = {sorts.loc['gap', 't_stat']:.1f})",
                 "sort", "Gap (products vs company)", True, sorts.loc["gap", "long_short"]),
             row("Rising click-through (single signal)",
                 f"{sorts.loc['conversion_change', 'long_short'] * 100:+.2f}% a month "
                 f"(t = {sorts.loc['conversion_change', 't_stat']:.1f})",
                 "sort", "Click-through change", True, sorts.loc["conversion_change", "long_short"]),
             row("Product buzz before results means fewer beats",
                 f"{beat_sort['top_minus_bottom'] * 100:+.1f} pts (t = {beat_sort['t_stat']:.1f})",
                 "earnings", "beat: top minus bottom third", False, beat_sort["top_minus_bottom"])],
            numeric=set()))
        st.markdown(
            f"- **The earnings finding is the one that survives**: almost the same gap in the new "
            f"companies, and over all 112 companies together it is statistically significant "
            f"({all_beat['result'] * 100:+.1f} points, t = {all_beat['t_stat']:.1f}). It is weaker in "
            f"another version of the test, so it should still be read with care.\n"
            "- **The return results do not carry over**: the strategy's edge and the two promising "
            "signals were most likely luck in the original 68.\n"
            "- From December 2026 the live strategy covers all 112 companies (decided on 9 Nov 2026, "
            "before any December returns existed); November's picks came from the first 68.\n"
            "- These figures are recomputed every day. The machine-learning results can move by "
            "about ±0.3% a month when Yahoo revises past prices or share counts, which is itself a "
            "sign that the edge is too small to rely on. The results as first run are recorded in "
            "the plan, linked above."
        )

    with st.expander("Research detail: the final click-through tests"):
        clicks_tests = data["clickthrough"].set_index("signal")
        st.markdown(
            f"Two last questions where click-through might show something product attention cannot, "
            f"[planned in advance]({CLICKTHROUGH_PLAN_URL})."
        )
        st.html(html_table(
            ["Test", "Result", "t"],
            [["Does a big change in click-through predict a more volatile next month?",
              f"{clicks_tests.loc['abs_conversion_change', 'result']:+.3f}",
              f"{clicks_tests.loc['abs_conversion_change', 't_stat']:.1f}"],
             ["Do companies with high click-through do worse next month?",
              f"{clicks_tests.loc['conversion', 'result'] * 100:+.2f}% a month",
              f"{clicks_tests.loc['conversion', 't_stat']:.1f}"],
             ["The same, compared within sectors",
              f"{clicks_tests.loc['conversion vs sector', 'result'] * 100:+.2f}% a month",
              f"{clicks_tests.loc['conversion vs sector', 't_stat']:.1f}"]],
            numeric={1, 2},
        ))
        st.markdown(
            "Click-through does not predict volatility. The apparent underperformance of high "
            "click-through companies disappears within sectors: consumer staples (beer, nappies, "
            "soap) have by far the highest click-through and lagged the market from 2022. "
            "Click-through measures something real, how strongly readers link a product to the "
            "company behind it, but it does not predict returns."
        )

    with st.expander("Research detail: each signal on its own, and the long-short model"):
        st.markdown(
            "These tests buy the top third **and sell the bottom third**, a standard research "
            "measure of whether a signal separates winners from losers. They are not the strategy "
            "above, which only buys."
        )
        st.html(html_table(
            ["Signal", "Top minus bottom, a month", "t", "Verdict"],
            [[f'{SIGNAL_LABELS[sig]}<span class="sub">{SIGNAL_MEANINGS[sig]}</span>',
              f"{sorts.loc[sig, 'long_short'] * 100:+.2f}%",
              f"{sorts.loc[sig, 't_stat'] + 0:.1f}".replace("-0.0", "0.0"),
              chip(sorts.loc[sig, "t_stat"])] for sig in sorts.index],
            numeric={1, 2},
        ))
        st.html(html_table(
            ["Model version (2022–26)", "Top minus bottom, a month", "After costs", "t", "Verdict"],
            [[VERSION_LABELS[v], f"{model.loc[v, 'long_short'] * 100:+.2f}%",
              f"{model.loc[v, 'long_short_net'] * 100:+.2f}%", f"{model.loc[v, 't_stat']:.1f}",
              chip(model.loc[v, "t_stat"])] for v in model.index],
            numeric={1, 2, 3},
        ))
        st.image(str(PROJECT_DIR / "charts" / "sorts_next_month_returns.png"), width="stretch")

    with st.expander("Terms used on this page"):
        st.markdown(
            "- **Top third:** each month the 68 companies are ranked and the best 23 are bought "
            "in equal amounts.\n"
            "- **Average of the 68 companies:** buying all of them in equal amounts; the fair "
            "comparison, because the strategy also uses equal amounts.\n"
            "- **Trading costs:** 0.1% of every amount bought or sold.\n"
            "- **t (confidence score):** how far the average result is from zero compared with how "
            "much it varies month to month. About 2 or more is unlikely to be luck; 1.5 to 2 is "
            "promising; 0.5 to 1.5 is positive but weak; below 0.5 is no effect.\n"
            "- **Years the model never saw:** the model is retrained each year on past data only, "
            "and tested on the following year."
        )

# ---- Track record -------------------------------------------------------------------
with track:
    track_daily = data["track_daily"]
    track_monthly = data["track_monthly"]
    names = universe.drop_duplicates("ticker").set_index("ticker")["company"]
    with st.container(key="card_track"):
        st.subheader("Live track record")
        st.markdown(
            "Every month, as soon as the previous month's data is complete, the strategy's picks "
            "are recorded and never changed afterwards. This page follows those recorded picks day "
            "by day: **bought in equal amounts at the close on the next trading day after they are "
            "recorded**, as a real investor could, and held to the end of the month, after 0.1% "
            "trading costs. "
            "Nothing here can be tuned with hindsight."
        )
        if track_daily.empty:
            first = data["live_picks"].iloc[0]
            st.info(f"The first picks were recorded on {pd.Timestamp(first['recorded_on']):%-d %B %Y} "
                    f"and are bought at the close on the next trading day. Results appear here from "
                    f"the trading day after that.")
        else:
            track_daily["date"] = pd.to_datetime(track_daily["date"])
            first_day, last_day_held = track_daily["date"].iloc[0], track_daily["date"].iloc[-1]
            m1, m2, m3 = st.columns(3)
            for column, key, label in [(m1, "strategy", "Strategy picks"),
                                       (m2, "average_company", "All 68 companies"),
                                       (m3, "spy", "S&P 500")]:
                column.metric(label, f"${track_daily[key].iloc[-1]:,.2f}",
                              f"{track_daily[key].iloc[-1] / 100 - 1:+.2%} so far", border=True)
            st.caption(f"Value of $100 invested at the close on {first_day:%-d %B %Y}, as of the close "
                       f"on {last_day_held:%-d %B %Y}.")

            live_chart = go.Figure()
            for key, label, colour, width in [("strategy", "Strategy picks", "#2a78d6", 3),
                                              ("average_company", "All 68 companies", "#9aa5b1", 2),
                                              ("spy", "S&P 500", "#0f1b2d", 1.5)]:
                live_chart.add_trace(go.Scatter(
                    x=track_daily["date"], y=track_daily[key], name=label, mode="lines+markers",
                    line=dict(color=colour, width=width), marker=dict(size=5),
                    hovertemplate="$%{y:.2f}<extra>" + label + "</extra>",
                ))
            live_chart.add_hline(y=100, line_color="#888", line_width=1, line_dash="dot")
            live_chart.update_layout(
                yaxis=dict(title="Value of $100 ($)", gridcolor=GRID), xaxis=dict(showgrid=False, hoverformat="%-d %b %Y"),
                hovermode="x unified", height=340, legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
                margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False, hoverlabel=HOVER_LABEL,
            )
            live_chart.update_xaxes(fixedrange=True)
            live_chart.update_yaxes(fixedrange=True)
            st.plotly_chart(live_chart, width="stretch", config=CHART_CONFIG)

            st.html(html_table(
                ["Month held", "Picks recorded on", "Strategy", "All 68", "S&P 500", "Status"],
                [[f"{pd.Period(r.month_held):%B %Y}", f"{pd.Timestamp(r.recorded_on):%-d %b %Y}",
                  f"{r.strategy:+.2%}", f"{r.average_company:+.2%}", f"{r.spy:+.2%}",
                  "Complete" if r.complete else f"In progress, to {pd.Timestamp(r.through):%-d %b}"]
                 for r in track_monthly.itertuples()],
                numeric={2, 3, 4},
            ))
            st.caption("A few weeks, or even a few months, say almost nothing about whether the strategy "
                       "works: short-term returns are mostly noise. The record becomes meaningful after a "
                       "year or more.")

    with st.expander("Each month's recorded picks"):
        for month, picks in data["live_picks"].groupby("month", sort=False):
            st.markdown(f"**Chosen at the end of {pd.Period(month):%B %Y}**, recorded on "
                        f"{pd.Timestamp(picks['recorded_on'].iloc[0]):%-d %B %Y}")
            st.html('<div class="ci-picks">' + "".join(
                f"<div>{names.get(t, t)} <span>{t}</span></div>" for t in picks.sort_values("rank")["ticker"])
                + "</div>")

# ---- Method & data -------------------------------------------------------------------
with method:
    with st.container(key="card_how"):
        st.subheader("How it works")
        st.markdown(
            "1. **Universe:** 112 US-listed companies with well-known products on Wikipedia, "
            "checked by hand (232 product pages, e.g. Novo Nordisk → Ozempic and Semaglutide). The "
            "first 68 were used to design and run every test; 44 were added in November 2026 to "
            "check the results on companies the tests had never seen.\n"
            "2. **Attention:** daily page views since 2017, and the monthly clickstream (how many "
            "readers clicked from which page to which) since November 2017.\n"
            "3. **Signals:** each company's attention compared with its own recent past, so large "
            "and small companies can be compared.\n"
            "4. **Tests:** portfolio sorts, risk-factor alpha (Fama-French 5 factors and "
            "momentum), and an out-of-sample machine-learning model, net of trading costs.\n"
            "5. **Automation:** every evening, after the US market close, a script on GitHub "
            "downloads the new data, "
            "recomputes everything and updates this site."
        )
    with st.container(key="card_timeframes"):
        st.subheader("Time frames")
        st.markdown("Every comparison on this site, and the period it covers.")
        st.html(html_table(
            ["Where", "What is measured", "Compared with", "Why this window"],
            [["Explorer: number cards", "Page views in the latest complete month",
              "Their average over the 6 months before", "Six monthly points define a stable normal; "
              "this is the window the strategy uses"],
             ["Explorer: click-through card", "Click-through in the latest month",
              "The month before", "Shows the most recent change"],
             ["Explorer: share price card", "Latest price (live in US trading hours, 15-min delay)",
              "The price 12 months earlier", "Long enough to see the trend"],
             ["Trending", "Views in the 7 most recent days of data", "The average week over the 8 weeks "
              "before", "Recent enough to catch sudden jumps without reaching into another season"],
             ["Trending: share price", "Latest week (close to close), and the latest trading day",
              "The S&P 500 over the same week", "Matches the attention week"],
             ["Strategy and research tests", "Attention signals at each month end", "The 6 months before; "
              "returns over the following month", "Set by the project brief; decided before testing"],
             ["Out-of-sample test", "January 2022 to the latest month", "Models trained only on earlier "
              "years, retrained each January", "Never judged on data the model has seen"],
             ["Earnings test", "Product views 35 to 6 days before each results date",
              "The same days a year earlier", "Year on year handles seasonal products; ends before "
              "previews of the results"],
             ["Track record", "From the close on the next trading day after picks are recorded",
              "All 68 companies and the "
              "S&P 500 over the same days", "Only returns that had not happened yet"]],
            numeric=set(),
        ))
        st.caption("The 8-week Trending window is a display choice for spotting change; it is not a "
                   "tested trading signal.")

    left, right = st.columns(2)
    with left.container(key="card_sources"):
        st.subheader("Data sources")
        st.markdown(
            "- Wikimedia Pageviews API and Wikipedia clickstream\n"
            "- Yahoo Finance (via `yfinance`): share prices and share counts\n"
            "- Kenneth French's data library: risk factors\n"
            f"- Code and data: [{GITHUB_URL.removeprefix('https://')}]({GITHUB_URL})"
        )
    with right.container(key="card_limits"):
        st.subheader("Known limits")
        st.markdown(
            "- **Small universe** (112 large companies, about 9 years): real but small effects "
            "are hard to prove, and most results did not hold on the 44 companies added later.\n"
            "- **Wikipedia quirks:** renamed pages (old titles added up), automated traffic "
            "counted as human before 2020 (one-day spikes capped), clicks hidden when a link has "
            "10 or fewer in a month.\n"
            "- **Share counts** from Yahoo needed cleaning; market cap is accurate to a few percent.\n"
            "- **Today's product list** is used for the whole history, a mild form of hindsight.\n"
            "- **Model results move** by about ±0.3% a month when Yahoo revises past prices or share "
            "counts: the tree model is sensitive to small changes in how companies rank."
        )

# ---- Footer ---------------------------------------------------------------------------
st.html(f"""
<div class="ci-footer">
  <span>Curiosity Index &middot; Machine Learning for Factor Investing, emlyon business school, 2026</span>
  <span>{DISCLAIMER} &middot; <a href="{GITHUB_URL}" target="_blank">Code on GitHub</a></span>
</div>
""")
