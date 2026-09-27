"""Render the README figure from the committed Power BI scenario rows."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "powerbi" / "data" / "scenario_daily.csv"
OUTPUT = ROOT / "docs" / "images" / "scenario-exposure.png"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: row["date"])
    if len(rows) != 75:
        raise ValueError(f"Expected 75 complete FIRM days; found {len(rows)}")

    days = [date.fromisoformat(row["date"]) for row in rows]
    original, earlier = [], []
    running_original = running_earlier = 0.0
    for row in rows:
        running_original += float(row["original_aud"])
        running_earlier += float(row["alternative_aud"])
        original.append(running_original)
        earlier.append(running_earlier)
    totals = (round(original[-1], 2), round(earlier[-1], 2), round(original[-1] - earlier[-1], 2))
    if totals != (291.74, 236.43, 55.31):
        raise ValueError("Scenario totals no longer match the labelled figure")

    blue, orange = "#203D6C", "#D47342"
    ink, muted, grid = "#182537", "#536171", "#DCE4EC"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    figure, ax = plt.subplots(figsize=(12, 5.8), dpi=160)
    figure.patch.set_facecolor("#FCFDFE")
    ax.set_facecolor("#FCFDFE")
    figure.subplots_adjust(left=0.09, right=0.77, bottom=0.22, top=0.70)

    ax.plot(days, original, color=blue, linewidth=2.8, label="Original: 16:00–18:00")
    ax.plot(days, earlier, color=orange, linewidth=2.8, label="Earlier: 11:00–13:00")
    ax.scatter(days[-1], original[-1], color=blue, s=45, zorder=3)
    ax.scatter(days[-1], earlier[-1], color=orange, s=45, zorder=3)
    ax.set_ylim(0, 320)
    ax.set_xlim(days[0], days[-1])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(colors=muted, length=0, pad=8)
    ax.grid(axis="y", color=grid, linewidth=0.8)
    ax.spines[:].set_visible(False)
    ax.set_ylabel("Cumulative wholesale exposure (AUD)", color=muted, labelpad=12)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.17), ncol=2, frameon=False, labelcolor=ink)

    figure.text(0.09, 0.90, "What changed when the activity moved earlier?", fontsize=19, weight="bold", color=ink)
    figure.text(0.09, 0.83, "Historical Queensland prices · 75 complete FIRM days in the 14 Jun–12 Sep 2026 holdout", fontsize=11, color=muted)
    figure.text(0.80, 0.62, "$55.31", fontsize=25, weight="bold", color=orange)
    figure.text(0.80, 0.56, "lower calculated", fontsize=11, color=ink)
    figure.text(0.80, 0.52, "wholesale exposure", fontsize=11, color=ink)
    figure.text(0.80, 0.39, "$291.74 original", fontsize=11, color=blue)
    figure.text(0.80, 0.34, "$236.43 earlier", fontsize=11, color=orange)
    figure.text(0.09, 0.09, "Invented 70 kWh/day load · 16 holdout days excluded · historical comparison, not a retail-bill saving", fontsize=9.5, color=muted)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, facecolor=figure.get_facecolor(), bbox_inches="tight", pad_inches=0.3)
    plt.close(figure)
    print(OUTPUT)


if __name__ == "__main__":
    main()
