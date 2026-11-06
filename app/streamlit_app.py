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
from plotly.subplots import make_subplots
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
GITHUB_URL = "https://github.com/dominicjburns2003-gif/curiosity-index"

# Fixed colour order: the company page first, then its products (at most 4)
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
PRICE_COLOUR = "#6250d6"  # its own colour, so the price is never confused with a page

st.set_page_config(page_title="Curiosity Index", page_icon="🔎", layout="wide")


@st.cache_data
def load_data():
    universe = pd.read_csv(PROJECT_DIR / "data" / "mapping" / "products_to_companies.csv")
    views = pd.read_csv(DATA_DIR / "pageviews_monthly.csv")
    daily_index = pd.read_csv(DATA_DIR / "pageviews_daily.csv", usecols=["date"])
    sorts = pd.read_csv(DATA_DIR / "sorts_summary.csv")
    prices = pd.read_csv(DATA_DIR / "prices_daily.csv", index_col="date", parse_dates=True)
    return universe, views, daily_index["date"].max(), sorts, prices


universe, views, last_day, sorts, prices = load_data()

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
# Attention on top, share price underneath, on the same timeline (two charts,
# not two y-axes on one, which would let the scales suggest a link)
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38],
                    vertical_spacing=0.06)
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
    ), row=1, col=1)
price = prices[ticker].loc[str(pages["month"].min().year):].dropna()
fig.add_trace(go.Scatter(
    x=price.index, y=price, name=f"{ticker} share price", mode="lines",
    line=dict(color=PRICE_COLOUR, width=1.5),
    hovertemplate="%{x|%d %b %Y}: $%{y:,.2f}<extra>Share price</extra>",
), row=2, col=1)
grid = "rgba(128,128,128,0.2)"
fig.update_yaxes(title_text="Views per month (log)", type="log", dtick=1, gridcolor=grid, row=1, col=1)
fig.update_yaxes(title_text="Share price ($)", gridcolor=grid, row=2, col=1)
fig.update_xaxes(showgrid=False)
fig.update_layout(
    hovermode="x unified", height=620,
    legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0), margin=dict(l=10, r=10, t=40, b=10),
)
st.plotly_chart(fig, width="stretch")

change = price.iloc[-1] / price.iloc[0] - 1
st.caption(f"Top: monthly views on English Wikipedia (human readers), on a log scale so the company "
           f"and its products, which can differ 100-fold, fit on one chart. Renamed pages have all "
           f"their titles added up, and one-day spikes that look automated are capped. "
           f"Bottom: daily share price, adjusted for splits and dividends "
           f"({change:+.0%} since {price.index[0]:%b %Y}). Seeing the two together does not show "
           f"that one causes the other: that is what the tests below are for.")

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
