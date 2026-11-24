#!/usr/bin/env python3
"""SIM figure: docked duck on nest v2, and the two-net charge path.

Not a hardware photo. The mat outline is the nest v2 mesh (CAD check only).
The 38 of 40 dock rate is the stored camera sim (sim pass only).

  python3 altaay_lab/cad/nest_v2/render_charge_path.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "stl")
OUT = os.path.join(HERE, "renders", "charge_path_sim.png")


def polys(name):
    m = trimesh.load(os.path.join(STL, name))
    v = np.asarray(m.vertices)[:, :2]
    return [v[f] for f in np.asarray(m.faces)]


def main():
    fig = plt.figure(figsize=(11.2, 6.4), dpi=120)
    fig.patch.set_facecolor("#f6f3ee")
    ax = fig.add_axes([0.04, 0.08, 0.55, 0.82])
    ax.set_facecolor("#efe8dc")
    ax.add_collection(PolyCollection(polys("felt_top.stl"), facecolor="#e4d3b4", edgecolor="none"))
    ax.add_collection(PolyCollection(polys("stripe_minus.stl"), facecolor="#a68448", edgecolor="none", label="minus foil"))
    ax.add_collection(PolyCollection(polys("stripe_plus.stl"), facecolor="#e0b85a", edgecolor="none", label="plus foil"))
    # The five domes, at the 12 mm pitch, drawn on the sun line. Schematic placement.
    ys = np.array([-24.0, -12.0, 0.0, 12.0, 24.0])
    ax.scatter(np.zeros_like(ys), ys, s=28, c="#ffe08a", edgecolors="#5c4314", linewidths=0.6, zorder=5, label="gold domes")
    seat = plt.Rectangle((-16, -40), 32, 80, fill=False, ec="#5c4314", lw=1.0, zorder=4)
    ax.add_patch(seat)
    ax.annotate("SIM", (0, 0), xytext=(-150, 90), fontsize=18, fontweight="bold", color="#8a3b12")
    ax.set_aspect("equal")
    ax.set_xlim(-280, 220)
    ax.set_ylim(-320, 340)
    ax.set_xlabel("x toward the wall, mm (CAD frame)")
    ax.set_ylabel("y along the wall, mm")
    ax.set_title("Nest v2, docked contact (SIM)")
    ax.legend(loc="lower right", frameon=False)
    ax.text(
        0.0, -0.16,
        "38 of 40 charging docks, sim pass only. Seat box is the part outline, not a new physics run.",
        transform=ax.transAxes, fontsize=8, color="#5c4314",
    )

    ax2 = fig.add_axes([0.62, 0.12, 0.35, 0.76])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 16)
    ax2.axis("off")
    ax2.set_title("Charge path (SIM)", loc="left", fontsize=12)
    lines = [
        "15.0 V adapter",
        "5 A fuse",
        "RXEF185  (wet / short)",
        "Pololu 2815  (reverse)",
        "SMAJ16A",
        "two foil buses",
        "five gold domes",
        "SS33 bridge  (either stripe)",
        "F2  5 A",
        "BQ24133  1.006 A  (calc only)",
        "pack only  12.6 V",
        "servo rail off while docked",
        "5 V pin stays on the pack",
    ]
    for i, text in enumerate(lines):
        y = 15 - i * 1.05
        ax2.text(0.3, y, text, fontsize=9, fontfamily="DejaVu Sans", color="#2b241c")
        if i < len(lines) - 1:
            ax2.annotate("", xy=(0.15, y - 0.85), xytext=(0.15, y - 0.15),
                         arrowprops=dict(arrowstyle="->", color="#8a3b12"))
    ax2.text(0.3, 0.6, "SIM", fontsize=16, fontweight="bold", color="#8a3b12")
    fig.savefig(OUT)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
