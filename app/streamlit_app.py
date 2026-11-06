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

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
GITHUB_URL = "https://github.com/dominicjburns2003-gif/curiosity-index"

# Fixed colour order: the company page first, then its products (at most 4)
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
CLICK_COLOUR = "#52514e"  # click-through and price each get their own colour,
PRICE_COLOUR = "#6250d6"  # so they are never confused with a page
GRID = "rgba(128,128,128,0.2)"
DISCLAIMER = "Student research project. Not investment advice."

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

/* Key-number cards: a light navy tint */
[data-testid="stMetric"] { background: #e6eef8; border-color: #cfdcec !important; }
[data-testid="stMetricLabel"] p { color: #16325a; font-weight: 600; }
[data-testid="stMetricValue"] { color: #0f1b2d; }

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
  .st-key-metrics_row [data-testid="stMetricValue"] { font-size: 1.5rem; }
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
}
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
        elif name == "prices":
            data[name] = pd.read_csv(path, index_col="date", parse_dates=True)
        else:
            data[name] = pd.read_csv(path)
    return data


data = load_data(tuple(path.stat().st_mtime for path in DATA_FILES.values()))
universe, views, prices = data["universe"], data["views"], data["prices"]
last_day = pd.Timestamp(data["daily"])

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
    <div class="ci-stat"><span class="n">{last_day:%-d %b %Y}</span><span class="l">latest data, updated daily</span></div>
  </div>
</div>
""")

explorer, results, method = st.tabs(["Explorer", "Results", "Method and data"])

# ---- Explorer -------------------------------------------------------------------
with explorer:
    companies = universe.drop_duplicates("ticker").sort_values("company")
    labels = {r.ticker: f"{r.company} ({r.ticker})" for r in companies.itertuples()}
    default = list(labels).index("NVO") if "NVO" in labels else 0
    ticker = st.selectbox("Choose a company", list(labels), index=default, format_func=labels.get)

    pages = views[views["ticker"] == ticker].copy()
    pages["month"] = pd.to_datetime(pages["month"])
    clicks = data["conversion"][data["conversion"]["ticker"] == ticker].copy()
    clicks["month"] = pd.to_datetime(clicks["month"])
    price = prices[ticker].loc[str(pages["month"].min().year):].dropna()

    # Key numbers for the latest complete month, each against its own recent past
    company_series = pages[pages["kind"] == "company"].groupby("month")["views"].sum(min_count=1).dropna()
    product_series = pages[pages["kind"] == "product"].groupby("month")["views"].sum(min_count=1).dropna()
    latest = company_series.index.max()

    def vs_normal(series: pd.Series) -> str:
        normal = series.iloc[-7:-1].mean()  # the 6 months before
        return f"{series.iloc[-1] / normal - 1:+.0%} vs normal"

    c1, c2, c3, c4 = st.container(key="metrics_row").columns(4)
    c1.metric("Company page", f"{company_series.iloc[-1]:,.0f}",
              vs_normal(company_series), border=True)
    c2.metric("Product pages", f"{product_series.iloc[-1]:,.0f}",
              vs_normal(product_series), border=True)
    if len(clicks) >= 2:
        change = (clicks["conversion"].iloc[-1] - clicks["conversion"].iloc[-2]) * 100
        c3.metric("Click-through", f"{clicks['conversion'].iloc[-1]:.2%}", f"{change:+.2f} pts", border=True)
    else:
        c3.metric("Click-through", "n/a", border=True)
    year_ago = price.loc[: price.index[-1] - pd.DateOffset(years=1)]
    c4.metric("Share price", f"${price.iloc[-1]:,.2f}",
              f"{price.iloc[-1] / year_ago.iloc[-1] - 1:+.0%} in a year" if len(year_ago) else None,
              border=True)
    # Wikipedia's overall traffic moves too (it fell through 2026), so give the
    # typical company's change as a benchmark for the numbers above
    all_companies = views[views["kind"] == "company"].pivot_table(
        index="month", columns="ticker", values="views", aggfunc="sum")
    typical = (all_companies.iloc[-1] / all_companies.iloc[-7:-1].mean() - 1).median()
    st.caption(f"Views and click-through for {latest:%B %Y}; \"normal\" = the 6 months before; "
               f"click-through change vs the month before; share price on {price.index[-1]:%-d %b %Y}. "
               f"For comparison, the typical company page was {typical:+.0%} vs normal that month, "
               f"as Wikipedia's overall traffic changes too.")

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
        name = f"{labels[ticker]} – company page" if kind == "company" else article.replace("_", " ")
        fig.add_trace(go.Scatter(
            x=series["month"], y=series["views"], name=name, mode="lines",
            line=dict(color=colour, width=3 if kind == "company" else 2),
            hovertemplate="%{y:,.0f} views<extra>" + name + "</extra>",
        ))
    fig.add_trace(go.Scatter(
        x=clicks["month"], y=clicks["conversion"] * 100, name="Click-through to company", mode="lines",
        line=dict(color=CLICK_COLOUR, width=2), yaxis="y2",
        hovertemplate="%{y:.2f}%<extra>Click-through</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=price.index, y=price, name=f"{ticker} share price", mode="lines",
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
        margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False,
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

    def answer(question: str, detail: str, t: float, improves: bool = True) -> str:
        label, style = verdict(t) if improves else ("No improvement", "no")
        return (f'<div class="ci-answer"><div><div class="ci-q">{question}</div>'
                f'<div class="ci-d">{detail}</div></div><span class="ci-chip {style}">{label}</span></div>')

    dev = strategy[strategy["period"] == "development"].set_index("version")
    best_improved = dev.loc[["B", "C", "D"], "excess"].max()
    with st.container(key="card_summary"):
        st.subheader("The short answer so far")
        st.html(
            answer("Does buying the companies with the most product curiosity beat the average company?",
                   f"Buying the model's top third each month (no short selling, after trading costs) "
                   f"beat the average of the 68 companies by {run['excess'].mean() * 100:+.2f}% a month "
                   f"from {first + 1:%B %Y} to {last + 1:%B %Y}, but not by enough to rule out luck.",
                   excess_t)
            + answer("Does attention to products add anything to attention to the company?",
                     f"A model using product attention did {model.loc['products', 'long_short'] * 100:+.2f}% "
                     f"a month in the research test, against {model.loc['company', 'long_short'] * 100:+.2f}% "
                     f"for company attention alone.", model.loc["products", "t_stat"],
                     model.loc["products", "long_short"] > model.loc["company", "long_short"])
            + answer("Does click-through from products to the company add anything?",
                     f"Adding click-through gave {model.loc['clicks', 'long_short'] * 100:+.2f}% a month, "
                     f"lower than with product attention alone.", model.loc["clicks", "t_stat"],
                     model.loc["clicks", "long_short"] > model.loc["products", "long_short"])
            + answer("Did the planned improvements help?",
                     "A bad-news filter, comparing companies within their sector, a simpler score and "
                     "holding for 3 months were all planned in advance. None beat the original model "
                     "over 2022 to 2024.", 0, best_improved > dev.loc["A", "excess"])
        )
        st.caption("Research results, updated monthly. Not investment advice.")

    with st.container(key="card_growth"):
        st.subheader("What $100 would have become")
        st.markdown(
            f"Following the strategy from {first + 1:%B %Y}: each month, buy the top third of the "
            f"68 companies as ranked by the model, in equal amounts, after trading costs. Compared "
            f"with buying all 68 equally (the fair comparison) and with the S&P 500."
        )
        dates = pd.PeriodIndex(run["month"], freq="M").to_timestamp(how="end").normalize() + pd.offsets.MonthEnd(1)
        start = dates[0] - pd.offsets.MonthEnd(1)
        lines = {
            "Strategy": (run["net"], "#2a78d6", 3),
            "Average of the 68 companies": (run["average_company"], "#9aa5b1", 2),
            "S&P 500": (run["spy"], "#0f1b2d", 1.5),
        }
        growth = go.Figure()
        for name, (returns, colour, width) in lines.items():
            value = pd.concat([pd.Series([100.0]), 100 * (1 + returns.reset_index(drop=True)).cumprod()])
            growth.add_trace(go.Scatter(
                x=[start, *dates], y=value, name=name, mode="lines", line=dict(color=colour, width=width),
                hovertemplate="$%{y:.0f}<extra>" + name + "</extra>",
            ))
        # Value after the last development month's return (end of Jan 2025)
        final_start = (pd.Period(DEV_END) + 1).to_timestamp(how="end").normalize()
        growth.add_vline(x=final_start, line_color="#888", line_width=1, line_dash="dot")
        growth.add_annotation(x=final_start, y=1, yref="paper", text="Final check", showarrow=False,
                              xanchor="left", xshift=6, font=dict(size=11, color="#6b7280"))
        growth.update_layout(
            yaxis=dict(title="Value of $100 ($)", gridcolor=GRID), xaxis=dict(showgrid=False, hoverformat="%b %Y"),
            hovermode="x unified", height=380, legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
            margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"), dragmode=False,
        )
        growth.update_xaxes(fixedrange=True)
        growth.update_yaxes(fixedrange=True)
        st.plotly_chart(growth, width="stretch", config=CHART_CONFIG)
        st.caption("Before the dotted line: the period used to choose between the planned versions. "
                   "After it: the final check, run once.")

    with st.container(key="card_picks"):
        live = data["live_picks"]
        pick_month = pd.Period(live["month"].max())
        current = live[live["month"] == live["month"].max()].sort_values("rank")
        names = universe.drop_duplicates("ticker").set_index("ticker")["company"]
        st.subheader(f"Current picks for {pick_month + 1:%B %Y}")
        st.html('<div class="ci-picks">' + "".join(
            f"<div>{names.get(t, t)} <span>{t}</span></div>" for t in current["ticker"]) + "</div>")
        st.caption(f"Chosen at the end of {pick_month:%B %Y} and recorded on "
                   f"{pd.Timestamp(current['recorded_on'].iloc[0]):%-d %B %Y}, before any of the month's "
                   f"returns were known. Each month's picks are added to a permanent record, so the "
                   f"strategy's live track record can be checked later. Not investment advice.")

    with st.container(key="card_versions"):
        st.subheader("Versions tested")
        st.markdown(
            f"Five changes were [planned and written down]({PLAN_URL}) before any were tested. "
            f"Each version was run on 2022 to 2024 and the best one chosen by a fixed rule (highest "
            f"return above the average company, after costs). Only then was it checked on 2025 to 2026."
        )
        rows = []
        for version in ["A", "B", "C", "D", "B_no_filter", "B_1m"]:
            d = strategy[(strategy["version"] == version) & (strategy["period"] == "development")].iloc[0]
            f = strategy[(strategy["version"] == version) & (strategy["period"] == "final")].iloc[0]
            name = d["name"] + (" (chosen)" if d["chosen"] else "")
            rows.append([f"<b>{name}</b>" if d["chosen"] else name,
                         f"{d['excess'] * 100:+.2f}%", f"{d['excess_t']:.1f}",
                         f"{f['excess'] * 100:+.2f}%", f"{f['excess_t']:.1f}"])
        st.html(html_table(["Version", "2022–24: vs average", "t", "2025–26: vs average", "t"],
                           rows, numeric={1, 2, 3, 4}))
        st.markdown(
            "- **The bad-news filter hurt.** Companies whose price was falling while their "
            "attention rose tended to bounce back the next month, so skipping them removed good picks.\n"
            "- **Comparing within sectors hurt**: part of the signal seems to come from picking whole "
            "sectors, such as consumer brands with viral products.\n"
            "- **Holding for 3 months** cut trading costs by more than half, but lowered returns.\n"
            "- The 1-month check looks best in 2025–26, but it lost in 2022–24 and was not a "
            "candidate, so choosing it now would be picking results after seeing them."
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

# ---- Method & data -------------------------------------------------------------------
with method:
    with st.container(key="card_how"):
        st.subheader("How it works")
        st.markdown(
            "1. **Universe:** 68 US-listed companies with well-known products on Wikipedia, "
            "checked by hand (140 product pages, e.g. Novo Nordisk → Ozempic and Semaglutide).\n"
            "2. **Attention:** daily page views since 2017, and the monthly clickstream (how many "
            "readers clicked from which page to which) since November 2017.\n"
            "3. **Signals:** each company's attention compared with its own recent past, so large "
            "and small companies can be compared.\n"
            "4. **Tests:** portfolio sorts, risk-factor alpha (Fama-French 5 factors and "
            "momentum), and an out-of-sample machine-learning model, net of trading costs.\n"
            "5. **Automation:** every morning a script on GitHub downloads the new data, "
            "recomputes everything and updates this site."
        )
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
            "- **Small universe** (68 large companies, about 9 years): real but small effects "
            "are hard to prove.\n"
            "- **Wikipedia quirks:** renamed pages (old titles added up), automated traffic "
            "counted as human before 2020 (one-day spikes capped), clicks hidden when a link has "
            "10 or fewer in a month.\n"
            "- **Share counts** from Yahoo needed cleaning; market cap is accurate to a few percent.\n"
            "- **Today's product list** is used for the whole history, a mild form of hindsight.\n"
            "- **Results move a little** when Yahoo revises past data, by about ±0.15% a month."
        )

# ---- Footer ---------------------------------------------------------------------------
st.html(f"""
<div class="ci-footer">
  <span>Curiosity Index &middot; Machine Learning for Factor Investing, emlyon business school, 2026</span>
  <span>{DISCLAIMER} &middot; <a href="{GITHUB_URL}" target="_blank">Code on GitHub</a></span>
</div>
""")
