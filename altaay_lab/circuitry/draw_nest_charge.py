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
    ax.set_xlim(0, 16)
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
    box(ax, 7.4, 4.5, 1.8, 1.0, "F2\n5 A", "#ffebee")
    ax.annotate("", xy=(7.4, 5.0), xytext=(6.9, 4.6), arrowprops=dict(arrowstyle="->", color="#263238"))
    box(ax, 9.7, 6.2, 2.8, 1.5, "BQ24133\nCELL to VREF\n12.6 V, 1.006 A", "#e8f5e9")
    box(ax, 9.7, 3.4, 2.8, 1.6, "DK6 OR DK7\nawake rail\ni7C holds 12.0 V", "#f3e5f5")
    ax.annotate("", xy=(9.7, 6.9), xytext=(9.2, 5.2), arrowprops=dict(arrowstyle="->", color="#2e7d32"))
    ax.annotate("", xy=(9.7, 4.2), xytext=(9.2, 4.8), arrowprops=dict(arrowstyle="->", color="#6a1b9a"))
    ax.text(9.3, 5.7, "NEST_P", fontsize=7, color="#2e7d32")
    box(ax, 13.1, 6.2, 2.5, 1.5, "3S P45B\ncharge only", "#efebe9")
    box(ax, 13.1, 3.4, 2.5, 1.6, "servos and 5 V\nstill on", "#f3e5f5")
    ax.annotate("", xy=(13.1, 6.9), xytext=(12.5, 6.9), arrowprops=dict(arrowstyle="->", color="#263238"))
    ax.annotate("", xy=(13.1, 4.2), xytext=(12.5, 4.2), arrowprops=dict(arrowstyle="->", color="#263238"))
    ax.text(0.4, 0.7, "SIM is not this picture. The 26 V TVS clamp versus the 20 V PVCC limit for 1 us is BLOCKER.\n"
            "MCP73213 at 8.40 V does not finish a 12.6 V pack.",
            fontsize=8, color="#455a64")
    fig.tight_layout()
    fig.savefig(OUT, dpi=120)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
