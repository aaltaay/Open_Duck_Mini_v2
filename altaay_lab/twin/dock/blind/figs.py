#!/usr/bin/env python3
"""One figure for the blind walk-in. sim pass only."""
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

# counts of 540, from score.py on blind_runs_b190.json and blind_runs_b215.json
labels = ["falls", "first sit\ncharges", "within 3 sits\ncharges", "first seat inside\nthe flush window"]
a190 = [1, 35, 98, 380]
a215 = [2, 26, 92, 370]
x = np.arange(len(labels))
w = 0.36
fig, ax = plt.subplots(figsize=(8.2, 4.0))
b1 = ax.bar(x - w / 2, a190, w, color="#1f7a4d", label="190 mm, approved")
b2 = ax.bar(x + w / 2, a215, w, color="#2a78d6", label="215 mm, study only")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("runs, of 540")
ax.set_ylim(0, 480)
ax.legend(frameon=False)
ax.grid(axis="y", color=GRID, lw=0.7)
ax.tick_params(length=0)
for bars in (b1, b2):
    for rect in bars:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, h + 8, str(int(h)), ha="center", va="bottom", fontsize=8, color=INK)
ax.set_title("Blind walk-in. Camera field, then the measured walking speed. sim pass only.", loc="left", fontweight="bold")
fig.tight_layout()
path = os.path.join(HERE, "F1_blind.png")
fig.savefig(path, dpi=120)
print(path)
