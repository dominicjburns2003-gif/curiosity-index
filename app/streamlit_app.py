"""
Curiosity Index - the web app (first version: a "dummy" page for the pitch).

Shows what the project tracks and the first results, using the files that the
pipeline writes to data/processed/. The ranking, the model and the backtest
pages are added later.

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

# Fixed colour order: the company page first, then its products
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

st.set_page_config(page_title="Curiosity Index", page_icon="🔎", layout="wide")


@st.cache_data
def load_data():
    universe = pd.read_csv(PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv")
    views = pd.read_csv(DATA_DIR / "pageviews_monthly.csv")
    daily_index = pd.read_csv(DATA_DIR / "pageviews_daily.csv", usecols=["date"])
    sorts = pd.read_csv(DATA_DIR / "sorts_summary.csv")
    return universe, views, daily_index["date"].max(), sorts


universe, views, last_day, sorts = load_data()

# ---- Header -----------------------------------------------------------------
st.title("Curiosity Index")
st.markdown(
    "**Does public curiosity about a company's *products* tell us anything about its stock?**  \n"
    "This project tracks English Wikipedia attention for US-listed companies at three levels: "
    "the company's own page, its products' pages, and how many readers click from a product "
    "through to the company."
)
st.info("Early version, still being built. The live rankings and the full out-of-sample "
        "backtest come later.", icon="🚧")

c1, c2, c3 = st.columns(3)
c1.metric("Companies", universe["ticker"].nunique())
c2.metric("Product pages", len(universe))
c3.metric("Months of data", views["month"].nunique())
st.caption(f"Page views up to {pd.Timestamp(last_day):%-d %B %Y}.")

# ---- Attention explorer -------------------------------------------------------
st.header("Attention explorer")
companies = universe.drop_duplicates("ticker").sort_values("company")
labels = {r.ticker: f"{r.company} ({r.ticker})" for r in companies.itertuples()}
default = list(labels).index("NVO") if "NVO" in labels else 0
ticker = st.selectbox("Company", list(labels), index=default, format_func=labels.get)

pages = views[views["ticker"] == ticker].copy()
pages["month"] = pd.to_datetime(pages["month"])
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
        hovertemplate="%{x|%b %Y}: %{y:,.0f} views<extra>" + name + "</extra>",
    ))
fig.update_layout(
    yaxis=dict(title="Views per month (log scale)", type="log", dtick=1,
               gridcolor="rgba(128,128,128,0.2)"),
    xaxis=dict(showgrid=False), hovermode="x unified", height=450,
    legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0), margin=dict(l=10, r=10, t=40, b=10),
)
st.plotly_chart(fig, width="stretch")
st.caption("Monthly views on English Wikipedia (human readers). Renamed pages have all their "
           "titles added up, and one-day spikes that look automated are capped. A log scale is "
           "used so the company and its products, which can differ 100-fold, fit on one chart.")

# ---- First results -----------------------------------------------------------------
st.header("First results: portfolio sorts")
st.markdown(
    "Each month, the companies are split into three equal groups on an attention signal and "
    "held for the next month. If the signal carries information, the high group should do "
    "better than the low group."
)
st.image(str(PROJECT_DIR / "charts" / "sorts_next_month_returns.png"), width="stretch")
gap = sorts.set_index("signal").loc["gap"]
st.markdown(
    f"- **Company-page attention alone** shows no link with next-month returns.\n"
    f"- **The gap** (products getting more attention than the company) is the most promising "
    f"signal: high minus low is **{gap['long_short'] * 100:+.2f}% a month**, with t = "
    f"{gap['t_stat']:.1f}. That is **not yet statistically significant** (the usual bar is about 2).\n"
    "- Click-through (product → company) features are added once the clickstream history "
    "is complete."
)

# ---- About -----------------------------------------------------------------------
st.header("About")
st.markdown(
    "**Data:** Wikimedia page views and clickstream (Wikipedia), share prices from Yahoo "
    "Finance, risk factors from Kenneth French's data library. All free and public.  \n"
    f"**Code:** [{GITHUB_URL.removeprefix('https://')}]({GITHUB_URL})  \n"
    "A student project for *Machine Learning for Factor Investing* (emlyon business school). "
    "Not investment advice."
)
