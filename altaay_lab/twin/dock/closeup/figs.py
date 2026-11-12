#!/usr/bin/env python3
"""One figure for the close-up comparison. Counts are sim pass only."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
INK, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3de", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUT, "xtick.color": MUT,
                     "ytick.color": MUT, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})


def row(block):
    a = block["all"]
    return [a["falls"], a["flush_first"], a["flush_within_3"]]


def main():
    blocks = json.load(open(os.path.join(HERE, "summary.json")))
    order = ["pitch", "marker", "wide", "turn"]
    by = {b["mode"]: b for b in blocks}
    labels = ["blind\ncamera", "head\ndown", "wall\ncard", "wide\nlens", "turn\nlook"]
    # Merged blind run file, 190 mm. Re-scored here. Not the pre-correction 1 fall and 386.
    series = [[0, 380, 383]] + [row(by[m]) for m in order]
    colors = ["#8a8580", "#c47b2b", "#1f7a4d", "#2a78d6", "#6b4c9a"]
    x = np.arange(3)
    w = 0.15
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    for i, (lab, vals, col) in enumerate(zip(labels, series, colors)):
        bars = ax.bar(x + (i - 2) * w, vals, w, color=col, label=lab.replace("\n", " "))
        for rect in bars:
            h = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, h + 6, str(int(h)), ha="center", va="bottom",
                    fontsize=7, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["falls", "flush window\nfirst sit", "flush window\nwithin 3 sits"])
    ax.set_ylabel("runs, of 540")
    ax.set_ylim(0, 620)
    ax.legend(frameon=False, ncol=5, loc="upper left")
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.tick_params(length=0)
    ax.set_title("Close-up sight. Same 540 seeds. sim pass only.", loc="left", fontweight="bold")
    fig.tight_layout()
    path = os.path.join(HERE, "F1_closeup.png")
    fig.savefig(path, dpi=120)
    print(path)


if __name__ == "__main__":
    main()
