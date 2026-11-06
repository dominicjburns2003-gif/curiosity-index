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
    "company_abn": "Abnormal company attention",
    "company_growth": "Company attention growth",
    "product_growth": "Product attention growth",
    "gap": "Gap: products vs company",
    "conversion_vs_normal": "Click-through vs normal",
    "conversion_change": "Click-through change",
}
VERSION_LABELS = {
    "company": "1. Company attention + controls",
    "products": "2. + Product attention",
    "clicks": "3. + Click-through",
}

st.set_page_config(page_title="Curiosity Index", page_icon=":material/query_stats:", layout="wide")

# Charts: no zoom or pan, so touching a chart on a phone shows the values
# instead of zooming in; and no floating toolbar
CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False}

# Page styling: Streamlit's defaults plus a hero banner, white cards on a light
# grey page, and a footer. Kept in one place so the look is easy to change.
PAGE_CSS = """
<style>
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 1.2rem; padding-bottom: 2rem; }
.ci-hero { background: linear-gradient(135deg, #0f1b2d 0%, #16325a 60%, #1f4f8f 100%);
           color: #fff; border-radius: 16px; padding: 44px 44px 32px; }
.ci-eyebrow { font-size: .76rem; letter-spacing: .12em; text-transform: uppercase;
              color: #9ec5f4; font-weight: 600; margin-bottom: 14px; }
.ci-hero h1 { color: #fff; font-size: 2.7rem; font-weight: 700; margin: 0 0 12px;
              line-height: 1.1; padding: 0; letter-spacing: -.02em; }
.ci-lead { font-size: 1.15rem; color: #d7e3f4; max-width: 700px; margin: 0 0 30px; line-height: 1.55; }
.ci-stats { display: flex; flex-wrap: wrap; gap: 14px 44px;
            border-top: 1px solid rgba(255,255,255,.16); padding-top: 22px; }
.ci-stat .n { display: block; font-size: 1.45rem; font-weight: 600; color: #fff; }
.ci-stat .l { font-size: .82rem; color: #9fb3cc; }
.ci-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 18px 0 10px; }
.ci-step { background: #fff; border: 1px solid #e3e6eb; border-radius: 12px; padding: 20px 22px; }
.ci-step .k { display: inline-flex; width: 28px; height: 28px; border-radius: 50%;
              background: #e8f1fc; color: #2a78d6; font-weight: 700; font-size: .9rem;
              align-items: center; justify-content: center; margin-bottom: 12px; }
.ci-step h3 { font-size: 1rem; font-weight: 600; margin: 0 0 6px; padding: 0; color: #0f1b2d; }
.ci-step p { font-size: .9rem; color: #4a5568; margin: 0; line-height: 1.5; }
[class*="st-key-card"] { background: #fff; border-radius: 12px; padding: 22px 24px 14px;
                         border: 1px solid #e3e6eb; box-shadow: 0 1px 2px rgba(15,27,45,.04); }
[data-testid="stMetric"] { background: #fff; }
[data-baseweb="tab-list"] { gap: 6px; }
button[data-baseweb="tab"] p { font-size: .98rem; font-weight: 600; }
.ci-footer { margin-top: 40px; padding: 22px 2px 6px; border-top: 1px solid #e3e6eb;
             color: #6b7280; font-size: .85rem; display: flex; justify-content: space-between;
             flex-wrap: wrap; gap: 8px 24px; }
.ci-footer a { color: #2a78d6; text-decoration: none; }
@media (max-width: 720px) {
  .ci-hero { padding: 28px 22px 22px; }
  .ci-hero h1 { font-size: 2rem; }
  .ci-steps { grid-template-columns: 1fr; }
  [class*="st-key-card"] { padding: 16px 14px 8px; }
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
}


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
     stock? The index tracks Wikipedia attention to US companies and their products, and tests
     whether it predicts the following month's returns.</p>
  <div class="ci-stats">
    <div class="ci-stat"><span class="n">{universe['ticker'].nunique()}</span><span class="l">US companies</span></div>
    <div class="ci-stat"><span class="n">{len(universe)}</span><span class="l">product pages</span></div>
    <div class="ci-stat"><span class="n">Since {views['month'].min()[:4]}</span><span class="l">daily attention data</span></div>
    <div class="ci-stat"><span class="n">{last_day:%-d %b %Y}</span><span class="l">latest data, updated daily</span></div>
  </div>
</div>
<div class="ci-steps">
  <div class="ci-step"><span class="k">1</span><h3>Company attention</h3>
    <p>Daily views of each company's own Wikipedia page, such as Novo Nordisk.</p></div>
  <div class="ci-step"><span class="k">2</span><h3>Product attention</h3>
    <p>Views of its products' pages, such as Ozempic and Semaglutide.</p></div>
  <div class="ci-step"><span class="k">3</span><h3>Click-through</h3>
    <p>The share of product readers who go on to the company's page.</p></div>
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Company page views", f"{company_series.iloc[-1]:,.0f}",
              vs_normal(company_series), border=True)
    c2.metric("Product page views", f"{product_series.iloc[-1]:,.0f}",
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
        margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", dragmode=False,
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
    with st.container(key="card_sorts"):
        st.subheader("Test 1: portfolio sorts")
        st.markdown(
            "Each month, the 68 companies are split into three equal groups on one signal and held "
            "for the next month. If the signal carries information, the high group should beat "
            "the low group. Each bar shows that difference; |t| of about 2 or more would suggest "
            "more than luck."
        )
        sorts = data["sorts"].set_index("signal").loc[list(SIGNAL_LABELS)]
        bars = go.Figure(go.Bar(
            y=[f"{SIGNAL_LABELS[s]}  (t = {t + 0:.1f})".replace("-0.0", "0.0")
               for s, t in zip(sorts.index, sorts["t_stat"])],
            x=sorts["long_short"] * 100, orientation="h",
            # Darker = closer to significance (|t| of 1.5 or more)
            marker_color=["#2a78d6" if abs(t) >= 1.5 else "#9ec5f4" for t in sorts["t_stat"]],
            customdata=sorts[["ret_g1", "ret_g3", "months"]].assign(ret_g1=lambda d: d.ret_g1 * 100,
                                                                    ret_g3=lambda d: d.ret_g3 * 100),
            hovertemplate="High − low: %{x:+.2f}% a month<br>Low group %{customdata[0]:.2f}%, "
                          "high group %{customdata[1]:.2f}%<br>%{customdata[2]} months<extra></extra>",
        ))
        bars.add_vline(x=0, line_color="#888", line_width=1)
        bars.update_layout(
            xaxis=dict(title="High group minus low group, % a month", gridcolor=GRID, zeroline=False),
            yaxis=dict(autorange="reversed"), height=330, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", dragmode=False,
        )
        bars.update_xaxes(fixedrange=True)
        bars.update_yaxes(fixedrange=True)
        st.plotly_chart(bars, width="stretch", config=CHART_CONFIG)
        with st.expander("See the low, middle and high groups for each signal"):
            st.image(str(PROJECT_DIR / "charts" / "sorts_next_month_returns.png"), width="stretch")

    with st.container(key="card_model"):
        st.subheader("Test 2: out-of-sample model")
        model = data["model"].set_index("version")
        model_monthly = data["model_monthly"]
        years_positive = (model_monthly.assign(year=model_monthly["month"].str[:4])
                          .groupby(["version", "year"])["long_short"].mean().gt(0)
                          .groupby("version").agg(["sum", "count"]))
        st.markdown(
            f"A machine-learning model (gradient-boosted trees) learns from the past only and "
            f"predicts the following year, retrained every year: "
            f"{pd.Period(model['first_month'].iloc[0]):%b %Y} to "
            f"{pd.Period(model['last_month'].iloc[0]):%b %Y} are months it never saw while "
            f"learning. It buys the top third of its predictions and sells the bottom third. "
            f"Three versions show what each kind of attention adds."
        )
        table = pd.DataFrame({
            "Version": [VERSION_LABELS[v] for v in model.index],
            "Long-short, % a month": (model["long_short"] * 100).round(2),
            "t-stat": model["t_stat"].round(1),
            "After 0.1% trading costs": (model["long_short_net"] * 100).round(2),
            "Years positive": [f"{years_positive.loc[v, 'sum']} of {years_positive.loc[v, 'count']}"
                               for v in model.index],
        })
        st.dataframe(table, hide_index=True, width="stretch")

    with st.container(key="card_findings"):
        st.subheader("What it shows so far")
        st.markdown(
            "- **Company-page attention alone does not predict returns** for these large "
            "companies, in the sorts or in the model.\n"
            "- **Product attention adds something**: the products version beats the company-only "
            "version, and the gap signal points the same way in the sorts. But nothing is "
            "statistically significant yet.\n"
            "- **Click-through:** a change in click-through looks as promising as the gap in the "
            "sorts, but adding it to the model did not help.\n"
            "- Several signals were tried, so one coming close to significance by chance is "
            "possible. Results are updated every month as new data arrives."
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
