#!/usr/bin/env python3
"""One-page surge path. Numbers are the ones in NEST_TWO_NET.md."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nest_surge.png")


def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=color, edgecolor="#222", linewidth=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8, color="#111")


def main():
    fig, ax = plt.subplots(figsize=(10.2, 4.6), dpi=120)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.set_title("Nest surge path. Cited numbers. The 26.0 V clamp is not on PVCC.", fontsize=11)
    box(ax, 0.25, 1.7, 1.7, 1.2, "rim\nSMAJ16A\n26.0 V at 15.4 A", "#fde8e8")
    box(ax, 2.2, 1.7, 1.5, 1.2, "SS33\nsteering\nF2 5 A", "#e8f0fe")
    box(ax, 4.0, 1.7, 2.2, 1.2, "TPS259470\ntrip 18.345 V max\n1.2 us typical", "#fff4d6")
    box(ax, 6.5, 2.5, 1.8, 1.1, "TVS1400\n19.3 V at 35 A", "#e7f6e7")
    box(ax, 6.5, 0.9, 1.8, 1.1, "BQ24133 PVCC\nabsolute max 20 V", "#e7f6e7")
    ax.annotate("", xy=(2.15, 2.3), xytext=(1.95, 2.3),
                arrowprops=dict(arrowstyle="->", color="#222"))
    ax.annotate("", xy=(3.95, 2.3), xytext=(3.7, 2.3),
                arrowprops=dict(arrowstyle="->", color="#222"))
    ax.annotate("", xy=(6.45, 3.05), xytext=(6.2, 2.5),
                arrowprops=dict(arrowstyle="->", color="#222"))
    ax.annotate("", xy=(6.45, 1.45), xytext=(6.2, 2.1),
                arrowprops=dict(arrowstyle="->", color="#222"))
    ax.text(0.3, 0.35, "IN absolute maximum 28 V covers 26.0 V. Recommended input maximum is 23 V.\n"
            "TVS1400 recommended standoff is 14 V. The 15.0 V set point is above it and below the 16.2 V breakdown minimum.",
            fontsize=8, color="#333")
    fig.tight_layout()
    fig.savefig(OUT)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
