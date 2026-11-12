#!/usr/bin/env python3
"""figs.py: the three figures of NEST_SIM.md, from nest_runs_<tag>.json and nest_results.json. sim pass only.
  PYTHONDONTWRITEBYTECODE=1 python3 figs.py [tag ...]
F1_pin_landing.png   where the 4 belly pins landed at the first sit, on the nest and on the pond rug (top view)
F2_run_traces.png    top-view traces of a few full runs
F3_success.png       success by pose noise level
Style: the friendly look of the parent folder (ducklib.py colours). The wall is on the left, as in A1 / A2.
Series colours checked with the dataviz validator (light surface): #2a78d6, #e0812b, #8a4fd0.
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ducklib import BG, INK, INK2, SOFT, WALL, plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402

W = 190.0                                    # sun centre from the wall, mm
RC, GAP, ROUT, MATR = 50.0, 32.0, 235.0, 247.0
RUG_A, RUG_B, RUG_HALF, RUG_SHIFT = (140.0, 250.0), (282.0, 520.0), 280.0, 14.2
FELT, FELT_E, RIM, RIM_E = "#e4ecd6", "#9fb487", "#b9cba3", "#8fa678"
SUN, SUN_E, RINGC, RING_E = "#f1cf6b", "#c9a02a", "#f6e7b4", "#d8bf78"
SAND, WATER, WATER_E = "#eedfae", "#cfe2ee", "#8fb0cf"
C = {"low": "#2a78d6", "mid": "#e0812b", "high": "#8a4fd0"}
NTXT = {"low": "5 mm / 1 deg", "mid": "15 mm / 3 deg", "high": "30 mm / 6 deg"}


def d_of(x):
    """sim x (m, sun centre = 0, wall at +0.19) -> distance from the wall, mm"""
    return W - np.asarray(x) * 1000.0


def wall(ax, y0, y1):
    ax.add_patch(Rectangle((-30, y0), 30, y1 - y0, fc=WALL, ec="none", zorder=1))
    ax.plot([0, 0], [y0, y1], color=SOFT, lw=1.2, zorder=1.1)


def nest(ax, zones=True, z=2):
    th = np.linspace(0, 2 * np.pi, 200)
    P = np.c_[W + MATR * np.cos(th), MATR * np.sin(th)]
    P[:, 0] = np.maximum(P[:, 0], 22)
    ax.add_patch(Polygon(P, closed=True, fc=FELT, ec=FELT_E, lw=1.2, zorder=z))
    if zones:
        Q = np.c_[W + ROUT * np.cos(th), ROUT * np.sin(th)]
        Q[:, 0] = np.maximum(Q[:, 0], 74)
        ax.add_patch(Polygon(Q, closed=True, fc=RINGC, ec=RING_E, lw=1.0, zorder=z + 0.1))
        ax.add_patch(Circle((W, 0), RC + GAP, fc=FELT, ec=RING_E, lw=1.0, zorder=z + 0.2))
        ax.add_patch(Circle((W, 0), RC, fc=SUN, ec=SUN_E, lw=1.2, zorder=z + 0.3))
    ax.add_patch(Rectangle((0, -227), 72, 454, fc=RIM, ec=RIM_E, lw=1.0, zorder=z + 0.4))


def rug(ax, z=2):
    ax.add_patch(Rectangle((RUG_A[0] - 30, -RUG_HALF - 20), RUG_B[1] - RUG_A[0] + 50, 2 * RUG_HALF + 40, fc="#f4efe2", ec="#cbbf9f", lw=1.2, zorder=z))
    ax.add_patch(Rectangle((RUG_A[0], -RUG_HALF), RUG_A[1] - RUG_A[0], 2 * RUG_HALF, fc=SAND, ec="#c9b37c", lw=1.0, zorder=z + 0.1))
    ax.add_patch(Rectangle((RUG_B[0], -RUG_HALF), RUG_B[1] - RUG_B[0], 2 * RUG_HALF, fc=WATER, ec=WATER_E, lw=1.0, zorder=z + 0.1))
    ax.add_patch(Rectangle((6, -150), 56, 300, fc=RIM, ec=RIM_E, lw=1.0, zorder=z + 0.3))


def finish(ax, xl, yl, title, sub=None):
    ax.set_aspect("equal")
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.set_xlabel("distance from the wall, mm", color=INK2, fontsize=10)
    ax.set_ylabel("along the wall, mm", color=INK2, fontsize=10)
    ax.tick_params(colors=INK2, labelsize=9, length=3)
    for s in ax.spines.values():
        s.set_color(SOFT)
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=(20 + 14 * sub.count("\n")) if sub else 8)
    if sub:
        ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")


def fig1(R):
    fig, axs = plt.subplots(1, 2, figsize=(15.5, 6.6))
    for ax, kind in zip(axs, ("nest", "rug")):
        if kind == "nest":
            wall(ax, -150, 150)
            nest(ax)
        else:
            wall(ax, -150, 150)
            rug(ax)
        n_ok = n_all = n_out = 0
        for r in sorted(R, key=lambda r: -{"low": 0, "mid": 1, "high": 2}.get(r["cfg"]["noise"], 0) if "cfg" in r else 0):
            if "error" in r or not r["sits"]:
                continue
            s = r["sits"][0]
            key = "nest" if kind == "nest" else "rug_own_aim"
            ok = s[key]["ok"]
            n_all += 1
            n_ok += ok
            col = C[r["cfg"]["noise"]]
            sh = RUG_SHIFT if kind == "rug" else 0.0
            n_out += abs(s["seat_xy"][1]) > 0.15
            for k, v in s["pins"].items():
                mk = "o" if k.startswith("seat") else "^"
                ax.scatter(d_of(v["xy"][0]) + sh, v["xy"][1] * 1000, s=15 if mk == "o" else 18, marker=mk, facecolor=col if ok else "white", edgecolor=col,
                           linewidth=0.9 if ok else 1.5, alpha=0.75 if ok else 1.0, zorder=6 if ok else 7)
        if kind == "nest":
            ax.add_patch(Circle((W, 0), 45, fc="none", ec=INK, lw=1.0, ls=(0, (4, 3)), zorder=5))
            ax.annotate("dashed: 45 mm window\nfor the seat pins", (W + 45 * np.cos(np.radians(-120)), 45 * np.sin(np.radians(-120))), (88, -112), fontsize=9.5, color=INK, ha="left", va="center",
                        arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), zorder=9)
            ax.annotate("sun (plus)", (W - 30, 38), (88, 118), fontsize=9.5, color=INK, ha="left", va="center", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), zorder=9)
            ax.text(W + 150, 118, "ring (minus)", ha="center", fontsize=9.5, color=INK, zorder=9)
            ax.text(W + 82, -128, "felt gap", ha="center", fontsize=9.5, color=INK, zorder=9)
            ax.annotate("", (W + 66, -8), (W + 80, -118), arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), zorder=9)
            ax.text(36, 0, "rim", rotation=90, ha="center", va="center", fontsize=9.5, color=INK, zorder=9)
            finish(ax, (-30, 400), (-150, 150), "On the nest with a sun", "Seat pins (circles) belong on the sun, bumper pins (triangles) on the ring. %d of %d first sits charge.\n%d sits landed more than 150 mm to the side and are off this picture." % (n_ok, n_all, n_out))
        else:
            ax.text(0.5 * sum(RUG_A), 132, "sand band (plus)", ha="center", fontsize=9.5, color=INK, zorder=9)
            ax.text(RUG_B[0] + 62, 132, "blue band (minus)", ha="center", fontsize=9.5, color=INK, zorder=9)
            finish(ax, (-30, 400), (-150, 150), "The same sits scored on the pond rug",
                   "Rug aim point 14 mm further from the wall (landings shifted to match). %d of %d first sits charge.\nThe rug is 560 mm long, so the far-side sits still charge here." % (n_ok, n_all))
            ax.text(36, 0, "reed box", rotation=90, ha="center", va="center", fontsize=9.5, color=INK, zorder=9)
    h = [Line2D([], [], marker="o", ls="", mfc=C[k], mec=C[k], ms=7, label="pose noise %s" % NTXT[k]) for k in C]
    h += [Line2D([], [], marker="o", ls="", mfc=INK2, mec=INK2, ms=7, label="seat pin"), Line2D([], [], marker="^", ls="", mfc=INK2, mec=INK2, ms=7, label="bumper pin"),
          Line2D([], [], marker="o", ls="", mfc="white", mec=INK2, mew=1.5, ms=7, label="hollow: this sit does not charge")]
    fig.legend(handles=h, loc="lower center", ncol=6, frameon=False, fontsize=10, labelcolor=INK)
    fig.suptitle("Where the belly pins landed at the first sit (seen from above, the wall is on the left). sim pass only",
                 x=0.012, ha="left", fontsize=14.5, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(os.path.join(HERE, "F1_pin_landing.png"), dpi=100)
    plt.close(fig)


def fig2(R):
    fig, ax = plt.subplots(figsize=(13.5, 8.2))
    wall(ax, -420, 420)
    nest(ax)
    T = [r for r in R if "trace" in r and "error" not in r and r["sits"]]
    pick = []
    for nz in ("low", "mid", "high"):
        g = [r for r in T if r["cfg"]["noise"] == nz]
        g.sort(key=lambda r: r["start"]["y"])
        if g:
            pick += [g[0], g[len(g) // 2], g[-1]][:3] if len(g) >= 3 else g
    seen = set()
    for r in pick:
        if id(r) in seen:
            continue
        seen.add(id(r))
        tr = r["trace"]
        col = C[r["cfg"]["noise"]]
        x = d_of([t[1] for t in tr])
        y = np.array([t[2] for t in tr]) * 1000
        st = [t[4] for t in tr]
        off = np.array([s in ("walk_off", "walk_off_stand") for s in st])
        ax.plot(x[~off], y[~off], color=col, lw=2.0, alpha=0.9, zorder=6, solid_capstyle="round")
        if off.any():
            ax.plot(x[off], y[off], color=col, lw=1.6, ls=(0, (2, 2.5)), alpha=0.9, zorder=6)
        ax.scatter([x[0]], [y[0]], s=70, facecolor="white", edgecolor=col, linewidth=2, zorder=7)
        hd = r["start"]["yaw"]
        ax.annotate("", (x[0] - 70 * np.cos(hd), y[0] + 70 * np.sin(hd)), (x[0], y[0]), arrowprops=dict(arrowstyle="->", color=col, lw=1.6), zorder=7)
        s0 = r["sits"][-1]
        ax.scatter([d_of(s0["seat_xy"][0])], [s0["seat_xy"][1] * 1000], s=46, marker="o", facecolor=col, edgecolor="white", linewidth=1.5, zorder=8)
    ax.text(1245, 395, "starts: 1.0 to 1.5 m from the wall,\n+/-0.3 m sideways, heading +/-30 deg\n(rings, arrow = first heading)", fontsize=10, color=INK, ha="right", va="top")
    ax.annotate("walk on, creep,\nturn left on the spot,\nsit (dot = seat pins)", (W + 30, -45), (430, -330), fontsize=10, color=INK, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), zorder=9)
    ax.text(700, -395, "dotted: stand up and walk straight out", fontsize=10, color=INK, ha="left", va="bottom")
    h = [Line2D([], [], color=C[k], lw=2.2, label="pose noise %s" % NTXT[k]) for k in C]
    ax.legend(handles=h, loc="upper left", bbox_to_anchor=(0.30, 1.0), frameon=False, fontsize=10, labelcolor=INK)
    finish(ax, (-30, 1560), (-420, 420), "A few full runs seen from above (trunk path, the wall is on the left). sim pass only")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "F2_run_traces.png"), dpi=100)
    plt.close(fig)


def fig3():
    S = json.load(open(os.path.join(HERE, "nest_results.json")))["by_noise"]
    series = [("nest_ok_first_sit", "nest, first sit", "#2a78d6"), ("nest_ok_within_3_sits", "nest, within 3 sits", "#e0812b"),
              ("rug_at_rug_aim_ok_first_sit", "pond rug, first sit (rug aim)", "#8a4fd0")]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    w = 0.24
    for j, (key, lab, col) in enumerate(series):
        for i, nz in enumerate(("low", "mid", "high")):
            d = S[nz]["success"][key]
            x = i + (j - 1) * (w + 0.02)
            ax.bar(x, d["pct"], width=w, color=col, zorder=3, label=lab if i == 0 else None)
            lo, hi = d["ci95"] if "ci95" in d else (d["pct"], d["pct"])
            ax.plot([x, x], [lo, hi], color=INK, lw=1.2, zorder=4)
            ax.text(x, 101.5 if hi > 93 else hi + 1.5, "%.0f %%" % d["pct"], ha="center", va="bottom", fontsize=10.5, color=INK, zorder=5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["pose noise %s\n(%d runs)" % (NTXT[k], S[k]["n"]) for k in ("low", "mid", "high")], fontsize=10.5, color=INK)
    ax.set_ylim(0, 124)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("runs that end charging, %", color=INK2, fontsize=10.5)
    ax.tick_params(colors=INK2, length=0)
    ax.grid(axis="y", color="#e6e2d8", lw=0.8, zorder=0)
    for k, s in ax.spines.items():
        s.set_visible(k == "bottom")
        s.set_color(SOFT)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=3, frameon=False, fontsize=10.5, labelcolor=INK, columnspacing=2.2)
    ax.set_title("Charging success by pose noise (falls count as failures; thin lines: 95 % range). sim pass only", loc="left", fontsize=13, fontweight="bold", color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "F3_success.png"), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    tags = sys.argv[1:] or ["main"]
    R = []
    for t in tags:
        R += json.load(open(os.path.join(HERE, "nest_runs_%s.json" % t)))["runs"]
    fig1(R)
    fig2(R)
    fig3()
    print("wrote F1_pin_landing.png F2_run_traces.png F3_success.png")
