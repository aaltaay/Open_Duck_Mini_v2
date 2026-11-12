"""ducklib.py: draw the real duck (convex hull per mesh geom, from duck_outline.json; sim pass only pose) in friendly colours."""
import json
import os
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = json.load(open(os.path.join(HERE, "duck_outline.json")))
BG = "#fbfaf6"
INK, INK2, SOFT = "#2e2c28", "#6b6860", "#b9b5aa"
COL = dict(trunk=("#f8d559", "#c9a02a"), head=("#f8d559", "#c9a02a"), leg=("#f6bd6a", "#cf9440"), foot=("#f09448", "#c06a22"),
           sole=("#e27f35", "#b45f1c"), seat=("#8fb0cf", "#5f86ab"), bumper=("#8fb0cf", "#5f86ab"))
WALL, FLOOR = "#e9e4d8", "#d8d2c3"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                     "axes.edgecolor": SOFT, "text.color": INK})


def duck_side(ax, x0=0.0, pose="sit", z0=0.0, alpha=1.0, flip=False, zorder=5, lw=0.5):
    """side view: the duck's trunk origin is above floor point x0; it faces +x (or -x with flip)"""
    polys = sorted(OUT[pose], key=lambda r: -r["depth_y"])
    for r in polys:
        P = np.array(r["side"], float)
        if len(P) < 3:
            continue
        if flip:
            P[:, 0] *= -1
        fc, ec = COL[r["kind"]]
        ax.add_patch(Polygon(P + [x0, z0], closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=zorder, joinstyle="round"))


def duck_top(ax, x0=0.0, y0=0.0, yaw_deg=0.0, pose="sit", alpha=1.0, zorder=5, lw=0.5):
    """top view: trunk origin at (x0, y0), heading yaw (0 = +x)"""
    c, s = np.cos(np.radians(yaw_deg)), np.sin(np.radians(yaw_deg))
    R = np.array([[c, -s], [s, c]])
    polys = sorted(OUT[pose], key=lambda r: r["depth_z"])
    for r in polys:
        P = np.array(r["top"], float)
        if len(P) < 3:
            continue
        fc, ec = COL[r["kind"]]
        ax.add_patch(Polygon(P @ R.T + [x0, y0], closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=zorder, joinstyle="round"))


def clean(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


if __name__ == "__main__":
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.5))
    duck_side(axs[0], 0, "sit"); axs[0].set_xlim(-250, 200); axs[0].set_ylim(-20, 420)
    duck_side(axs[1], 0, "stand"); axs[1].set_xlim(-250, 200); axs[1].set_ylim(-20, 540)
    duck_top(axs[2], 0, 0, 0, "sit"); duck_top(axs[2], 350, 0, 60, "stand"); axs[2].set_xlim(-220, 560); axs[2].set_ylim(-220, 220)
    for a in axs:
        a.set_aspect("equal")
    fig.savefig(os.path.join(os.environ.get("NEST_SCRATCH", tempfile.gettempdir()), "ducktest.png"), dpi=90)
