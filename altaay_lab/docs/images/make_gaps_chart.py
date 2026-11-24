"""Draw altaay_lab/docs/images/gaps_by_area.png from the GAPS.md inventory.

The counts are the 42 rows in that page. If a row is added or its closer
changes, change this table in the same commit. Run from the repo root:

    python3 altaay_lab/docs/images/make_gaps_chart.py
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gaps_by_area.png")

AREAS = [
    "Software",
    "Twin and sim",
    "Electrical",
    "Mechanical and CAD",
    "Manufacturing and cost",
    "Compliance and safety",
    "Product and business",
]
STATUSES = [
    "Software or sim now",
    "Needs hardware",
    "Needs a decision",
    "Needs money",
    "In progress",
]
# Rows follow AREAS. Columns follow STATUSES. Sum is 42.
DATA = np.array(
    [
        [8, 1, 1, 0, 0],
        [3, 3, 1, 0, 0],
        [4, 1, 0, 1, 0],
        [1, 2, 3, 0, 1],
        [2, 1, 1, 0, 0],
        [1, 1, 3, 1, 0],
        [0, 1, 1, 0, 0],
    ],
    dtype=int,
)
COLORS = ["#2F6F4E", "#C46B2C", "#3D5A80", "#8C3A4B", "#6B5B95"]


def main():
    if DATA.shape != (len(AREAS), len(STATUSES)):
        raise SystemExit("chart table shape does not match the labels")
    if int(DATA.sum()) != 42:
        raise SystemExit("chart table does not sum to 42")
    fig, ax = plt.subplots(figsize=(11.2, 6.6), dpi=140)
    y = np.arange(len(AREAS))
    height = 0.15
    offsets = (np.arange(len(STATUSES)) - (len(STATUSES) - 1) / 2.0) * height
    for index, (status, color, shift) in enumerate(zip(STATUSES, COLORS, offsets)):
        values = DATA[:, index]
        bars = ax.barh(y + shift, values, height=height * 0.92, color=color, label=status)
        for bar, value in zip(bars, values):
            if value <= 0:
                continue
            ax.text(
                bar.get_width() + 0.08,
                bar.get_y() + bar.get_height() / 2.0,
                str(int(value)),
                va="center",
                ha="left",
                fontsize=8,
                color="#222",
            )
    ax.set_yticks(y)
    ax.set_yticklabels(AREAS)
    ax.set_xlabel("Open gaps")
    ax.set_xlim(0, 10)
    ax.invert_yaxis()
    ax.set_title("Duckie: open gaps by area and what closes them", loc="left", fontsize=14, pad=12)
    fig.text(
        0.125,
        0.93,
        "42 gaps in GAPS.md, 2026-11-24. A sim, a calc, or a CAD check does not pass a gate.",
        fontsize=9,
        color="#333",
    )
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(OUT, dpi=140)
    size = os.path.getsize(OUT)
    if size > 5 * 1024 * 1024:
        raise SystemExit("png is over 5 MB: %d" % size)
    print("wrote %s (%d bytes)" % (os.path.basename(OUT), size))
    print("status totals:", DATA.sum(axis=0).tolist())
    print("area totals:", DATA.sum(axis=1).tolist())


if __name__ == "__main__":
    main()
