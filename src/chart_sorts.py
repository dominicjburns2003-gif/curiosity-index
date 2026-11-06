"""
Curiosity Index - chart of the portfolio sorts, for the pitch and the report.

One small panel per signal: the average next-month return of the low, middle
and high group, with the long-short spread and its t-statistic underneath.

Run it from the project folder, after src/backtest.py:
    python src/chart_sorts.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = PROJECT_DIR / "data" / "processed" / "sorts_summary.csv"
CHART_PATH = PROJECT_DIR / "charts" / "sorts_next_month_returns.png"

# One blue hue, light to dark = low to high signal
GROUP_COLOURS = ["#86b6ef", "#2a78d6", "#104281"]
INK, INK_SOFT, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def main() -> None:
    summary = pd.read_csv(SUMMARY_PATH)
    columns = 3
    rows = -(-len(summary) // columns)  # enough rows for every signal
    fig, axes = plt.subplots(rows, columns, figsize=(12, 4.2 * rows), sharey=True,
                             facecolor=SURFACE, squeeze=False)

    for ax, row in zip(axes.flat, summary.itertuples()):
        values = [row.ret_g1 * 100, row.ret_g2 * 100, row.ret_g3 * 100]
        bars = ax.bar(["Low", "Mid", "High"], values, color=GROUP_COLOURS, width=0.6,
                      edgecolor=SURFACE, linewidth=2)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.03, f"{v:.2f}%",
                    ha="center", va="bottom", fontsize=9, color=INK)
        ax.set_title(row.label, fontsize=10.5, color=INK, loc="left")
        ax.text(0, -0.16, f"High − low: {row.long_short * 100:+.2f}% a month (t = {row.t_stat:.1f}, {row.months} months)",
                transform=ax.transAxes, fontsize=9, color=INK_SOFT)
        ax.set_ylim(0, max(summary[["ret_g1", "ret_g2", "ret_g3"]].max()) * 100 * 1.15)
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ["top", "right", "left"]:
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(INK_SOFT)
        ax.tick_params(colors=INK_SOFT, length=0)

    for ax in axes[:, 0]:
        ax.set_ylabel("Average return next month (%)", color=INK_SOFT)
    for ax in axes.flat[len(summary):]:
        ax.set_visible(False)  # unused panels
    fig.suptitle("Next-month return by attention group: 68 US companies, monthly since 2017",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.text(0.01, 0.01, "Each month, companies are split into 3 equal groups on the signal and held "
             "for the next month, equally weighted. |t| of about 2 or more would suggest more than luck.",
             fontsize=8.5, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95), h_pad=3)
    CHART_PATH.parent.mkdir(exist_ok=True)
    fig.savefig(CHART_PATH, dpi=200, facecolor=SURFACE)
    print(f"Saved {CHART_PATH}")


if __name__ == "__main__":
    main()
