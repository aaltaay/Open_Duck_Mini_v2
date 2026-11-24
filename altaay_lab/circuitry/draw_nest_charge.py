#!/usr/bin/env python3
"""Draw the two-net charger. The picture is a schematic, not a photo of a board."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nest_charge_schematic.png")


def box(ax, x, y, w, h, text, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=fc, edgecolor="#263238", lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8, color="#263238")


def main():
    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=120)
    ax.set_xlim(0, 16.2)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("In-duck nest charger, two nets  (schematic, not a built board)", fontsize=12, color="#263238", pad=8)
    box(ax, 0.4, 6.3, 2.4, 1.3, "15 V adapter\nmat fuse 5 A\ncord pocket", "#fff3e0")
    box(ax, 0.4, 3.6, 2.4, 1.6, "nest v2 mat\n20 mm foil\n5 mm felt", "#ffe082")
    ax.annotate("", xy=(1.6, 5.2), xytext=(1.6, 6.3), arrowprops=dict(arrowstyle="-", color="#263238"))
    ax.text(1.75, 5.6, "two nets", fontsize=8, color="#6d4c41")
    for i, y in enumerate((4.7, 4.35, 4.0, 3.65, 3.3)):
        ax.add_patch(Circle((3.5, y), 0.16, facecolor="#d4af37", edgecolor="#6d4c41"))
    ax.text(3.5, 2.85, "5 gold domes", ha="center", fontsize=8)
    box(ax, 4.3, 3.5, 2.6, 1.8, "10x MBRS540T3G\nsteering\nSMAJ16A on\neach dome", "#e3f2fd")
    ax.annotate("", xy=(4.3, 4.4), xytext=(3.7, 4.0), arrowprops=dict(arrowstyle="->", color="#263238"))
    box(ax, 7.2, 4.6, 2.2, 1.4, "F2 5 A\nSMAJ16A\n26 V on input", "#ffebee")
    ax.annotate("", xy=(7.2, 5.2), xytext=(6.9, 4.6), arrowprops=dict(arrowstyle="->", color="#263238"))
    box(ax, 9.6, 4.5, 2.4, 1.6, "TPS259470\nOVLO 18.3 V max\n1.2 us typical", "#e0f2f1")
    ax.annotate("", xy=(9.6, 5.3), xytext=(9.4, 5.3), arrowprops=dict(arrowstyle="->", color="#263238"))
    box(ax, 12.3, 6.2, 3.2, 1.5, "BQ24133\nCELL to VREF\n12.6 V, 1.006 A", "#e8f5e9")
    box(ax, 9.6, 2.4, 2.4, 1.4, "DK6 OR DK7\nawake rail\ni7C holds 12.0 V", "#f3e5f5")
    ax.annotate("", xy=(12.3, 6.9), xytext=(12.0, 5.6), arrowprops=dict(arrowstyle="->", color="#2e7d32"))
    ax.annotate("", xy=(10.8, 3.8), xytext=(10.8, 4.5), arrowprops=dict(arrowstyle="->", color="#6a1b9a"))
    ax.text(12.05, 6.1, "under 20 V", fontsize=7, color="#00695c")
    ax.text(0.4, 0.55, "The 26 V clamp is on the eFuse input (28 V absolute maximum). The charger sees the eFuse output.\n"
            "Pi 5 at 5 V and 5 A is pull request 111. SIM is not this picture.",
            fontsize=8, color="#455a64")
    fig.tight_layout()
    fig.savefig(OUT, dpi=120)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
