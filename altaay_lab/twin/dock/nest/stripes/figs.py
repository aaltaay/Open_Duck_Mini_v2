#!/usr/bin/env python3
"""figs.py: the four figures of STRIPE_MAT_STUDY.md. calc only (drawn from stripe_cov.py, stripe_cov.json, sit_soles.json)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

import stripe_cov as C

HERE = os.path.dirname(os.path.abspath(__file__))
BG, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#dddcd6"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"
PLUS_F, MINUS_F = "#f6c9b5", "#b7d3f6"          # stripe fills (light steps of the two contact colours)
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "font.family": "DejaVu Sans"})
W_, G_ = 20, 5                                   # the pick S2
OUT_L, OUT_W = 101.9, 40.7                       # sole outline (print/foot_bottom_tpu.stl)
SOLE_FWD = -15.5                                 # sole centre ahead of the trunk origin in the sit (sit_soles.json)
BODY = dict(back=-156.5, front=65.4, half=131.0)  # sitting footprint in the trunk frame (sit_soles.json)


def stripes(ax, x0, x1, y0, y1, w=W_, g=G_):
    P = 2 * (w + g)
    k = int(np.floor(x0 / P)) - 1
    while k * P < x1:
        for off, col in ((0, PLUS_F), (w + g, MINUS_F)):
            a, b = max(k * P + off, x0), min(k * P + off + w, x1)
            if b > a:
                ax.add_patch(Rectangle((a, y0), b - a, y1 - y0, fc=col, ec="none", zorder=1))
        k += 1


def duck(ax, X, Y, yaw_deg, W=C.W_SIT, body=False, label=None, lab_off=(0, 0)):
    """soles (outline and flat face), the 5 + 5 contacts coloured by what they touch; returns powered"""
    psi = np.radians(yaw_deg)
    c, s = np.cos(psi), np.sin(psi)
    R = np.array([[c, -s], [s, c]])
    T = lambda P: (np.asarray(P) + [SOLE_FWD, 0]) @ R.T + [X, Y]
    if body:
        B = np.array([[BODY["back"], -BODY["half"]], [BODY["front"], -BODY["half"]], [BODY["front"], BODY["half"]], [BODY["back"], BODY["half"]]])
        ax.add_patch(Polygon(B @ R.T + [X, Y], closed=True, fc="none", ec=INK2, lw=1.2, ls=(0, (4, 3)), zorder=3))
    for f in (1, -1):
        for L, Wd, kw in ((OUT_L, OUT_W, dict(fc="#ffffff", ec=INK2, lw=1.0, alpha=0.75)), (C.FLAT_L, C.FLAT_W, dict(fc="#e9e8e2", ec=INK, lw=1.0))):
            P = np.array([[-L / 2, -Wd / 2], [L / 2, -Wd / 2], [L / 2, Wd / 2], [-L / 2, Wd / 2]]) + [0, f * W / 2]
            ax.add_patch(Polygon(T(P), closed=True, zorder=4, **kw))
    aL, aR, _ = C.layout(5, False)
    z = np.zeros(1)
    x, y = C.contacts(z + X + SOLE_FWD * c, z + Y + SOLE_FWD * s, z + psi, z + W, z, z, z, aL, aR)
    pol = C.pat_stripes_par(x, y, W_, G_)[0]
    for xi, yi, p in zip(x[0], y[0], pol):
        ax.plot(xi, yi, "o", ms=6.5, mfc={1: ORANGE, -1: BLUE, 0: "#ffffff"}[int(p)], mec=INK, mew=0.9, zorder=6)
    ok = (pol > 0).any() and (pol < 0).any()
    # heading arrow
    h = np.array([c, s])
    ax.add_patch(FancyArrowPatch(tuple(np.array([X, Y]) + 32 * h), tuple(np.array([X, Y]) + 78 * h), arrowstyle="-|>", mutation_scale=12, color=INK, lw=1.2, zorder=7))
    if label:
        ax.text(X - 22 * c + lab_off[0], Y - 22 * s + lab_off[1], label + ("\npowered" if ok else "\nNOT powered"), ha="center", va="center", fontsize=9,
                color=INK, zorder=8, bbox=dict(fc="#ffffff", ec=GRID, boxstyle="round,pad=0.3", alpha=0.95))
    return ok


def fig1():
    fig, ax = plt.subplots(figsize=(11, 8.2))
    stripes(ax, 0, 760, 0, 560)
    poses = [(150, 420, 0, "A: heading 0 deg", (0, 0)), (420, 400, 35, "B: 35 deg", (0, 0)),
             (640, 175, -60, "C: -60 deg", (0, 0)), (160, 140, 90, "D: 90 deg (sideways)", (0, 0)), (410, 130, 12, "E: 12 deg", (0, 0))]
    for X, Y, yw, lab, off in poses:
        duck(ax, X, Y, yw, label=lab, lab_off=off)
    ax.set_xlim(0, 760)
    ax.set_ylim(0, 560)
    ax.set_aspect("equal")
    ax.set_xlabel("distance from the wall side, mm (stripes run parallel to the wall)")
    ax.set_ylabel("along the wall, mm")
    ax.set_title("Fig 1. Pick S2 to scale: 20 mm stripes, 5 mm gaps; 5 contacts per foot, 19 mm apart, on the inner edge of each sole (calc only)",
                 fontsize=10.5, color=INK, loc="left")
    hs = [plt.Line2D([], [], marker="s", ls="", ms=11, mfc=PLUS_F, mec="none", label="+ stripe"),
          plt.Line2D([], [], marker="s", ls="", ms=11, mfc=MINUS_F, mec="none", label="- stripe"),
          plt.Line2D([], [], marker="o", ls="", ms=7, mfc=ORANGE, mec=INK, label="contact on +"),
          plt.Line2D([], [], marker="o", ls="", ms=7, mfc=BLUE, mec=INK, label="contact on -"),
          plt.Line2D([], [], marker="o", ls="", ms=7, mfc="#ffffff", mec=INK, label="contact on a gap (open)"),
          plt.Line2D([], [], marker="s", ls="", ms=11, mfc="#e9e8e2", mec=INK, label="sole flat face 84.8 x 15.8 mm"),
          plt.Line2D([], [], marker="s", ls="", ms=11, mfc="#ffffff", mec=INK2, label="sole outline 101.9 x 40.7 mm")]
    ax.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "F1_pattern_poses.png"), dpi=130)
    plt.close(fig)


def fig2():
    J = json.load(open(os.path.join(HERE, "stripe_cov.json")))
    D = {d["id"]: d for d in J["designs"]}
    M = json.load(open(os.path.join(HERE, "stripe_map_S2.json")))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 5.6), gridspec_kw=dict(width_ratios=[1.15, 1]))
    series = [("S2", "stripes parallel to the wall (pick)", BLUE, 2.6), ("P1", "stripes perpendicular to the wall", ORANGE, 1.8),
              ("C1", "checkerboard 30 mm", AQUA, 1.8), ("H1", "hexagons 30 mm", YELLOW, 1.8)]
    for k, lab, col, lw in series:
        g = D[k]["grid"]
        yw, v = np.array(g["yaw_deg"]), np.array(g["powered"]) * 100
        sel = np.abs(yw) <= 90
        # 5 deg running mean for the 2-D patterns keeps the line readable; S2 and P1 are exact
        a1.plot(yw[sel], v[sel], color=col, lw=lw, label=lab, zorder=3 if k == "S2" else 2)
    a1.axvspan(-60, 60, color="#eeeeea", zorder=0)
    a1.text(0, 3, "grey band: heading within 60 deg of facing the room", ha="center", fontsize=9, color=INK2)
    a1.set_xlim(-90, 90)
    a1.set_ylim(0, 102)
    a1.set_xticks(range(-90, 91, 30))
    a1.set_xlabel("heading, deg (0 = back to the wall, face to the room)")
    a1.set_ylabel("positions that are powered, %")
    a1.grid(color=GRID, lw=0.6)
    a1.set_title("Powered positions against heading, every position on the grid\n(nominal sit stance, exhaustive, calc only)", fontsize=10, loc="left")
    a1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=False, fontsize=9)
    mp = np.array(M["map"])
    yaws = np.arange(-180, 180)
    sel = (yaws >= -90) & (yaws <= 90)
    from matplotlib.colors import ListedColormap
    a2.imshow(mp[sel].T, origin="lower", aspect="auto", extent=[-90, 90, 0, M["period_mm"]], cmap=ListedColormap([ORANGE, "#d5e6fa"]), interpolation="nearest")
    a2.set_xticks(range(-90, 91, 30))
    a2.set_xlabel("heading, deg")
    a2.set_ylabel("position across one stripe period, mm")
    a2.set_title("Pick S2: where it is powered (light blue) and where not (orange)\n100 % for every heading within 78 deg", fontsize=10, loc="left")
    hs = [plt.Line2D([], [], marker="s", ls="", ms=10, mfc="#d5e6fa", mec=INK2, label="powered"),
          plt.Line2D([], [], marker="s", ls="", ms=10, mfc=ORANGE, mec=INK2, label="not powered")]
    a2.legend(handles=hs, loc="upper center", ncol=2, frameon=True, facecolor="#ffffff", edgecolor=GRID, fontsize=9)
    fig.suptitle("Fig 2. Coverage", x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(HERE, "F2_coverage.png"), dpi=130)
    plt.close(fig)


def box(ax, x, y, w, h, text, fc="#ffffff", ec=INK2, fs=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.1, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3)


def arrow(ax, p, q, text=None, off=(0, 0.13), col=INK, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=11, color=col, lw=1.3, ls=ls, zorder=1, shrinkA=0, shrinkB=0))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="center", fontsize=8, color=INK2)


def fig3():
    fig, ax = plt.subplots(figsize=(14, 7.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.add_patch(Rectangle((0.15, 0.3), 5.5, 6.2, fc="#f3f2ee", ec=GRID, zorder=0))
    ax.add_patch(Rectangle((6.55, 0.3), 7.3, 6.2, fc="#f3f2ee", ec=GRID, zorder=0))
    ax.text(0.3, 6.25, "MAT (against the wall)", fontsize=10.5, weight="bold")
    ax.text(6.7, 6.25, "DUCK", fontsize=10.5, weight="bold")
    box(ax, 0.35, 4.6, 1.5, 0.9, "12 V wall\nadapter\n5 A fuse")
    box(ax, 2.2, 4.6, 1.5, 0.9, "step-down\nset to 10.5 V")
    box(ax, 4.0, 4.6, 1.45, 0.9, "current-limit\nswitch (eFuse)\noff by default")
    box(ax, 0.9, 2.7, 3.85, 1.2, "probe and signature check\n5 V, 1 mA at most, on the stripes;\nlooks for the duck's signature;\nrechecks every 2 s; leak check at 1 V", fc="#fff6e0")
    box(ax, 0.35, 0.7, 5.1, 1.2, "stripes: net A (+) and net B (-), alternating\n20 mm wide, 5 mm gaps\n0 V and dead until the signature is seen", fc=PLUS_F)
    arrow(ax, (1.85, 5.05), (2.2, 5.05))
    arrow(ax, (3.7, 5.05), (4.0, 5.05))
    arrow(ax, (4.3, 3.9), (4.3, 4.6), "enable", off=(-0.4, 0))
    arrow(ax, (5.2, 4.6), (5.2, 1.9), None)
    ax.text(5.33, 3.3, "10.5 V", fontsize=8, color=INK2, rotation=90, va="center")
    arrow(ax, (2.8, 2.7), (2.8, 1.9), "probe", off=(0.38, 0))
    # duck
    box(ax, 6.75, 0.7, 2.3, 1.2, "10 sole contacts\n(5 per foot)\neach its own node", fc=MINUS_F)
    box(ax, 6.75, 2.7, 2.3, 1.2, "20 Schottky diodes\n(2 per contact, one small\nboard in each foot)\nsorts the polarity")
    box(ax, 9.6, 2.7, 1.9, 1.2, "signature\n(only the mat's probe\nsees it)", fc="#fff6e0")
    box(ax, 9.6, 4.6, 1.9, 0.9, "ideal diode DK6\n(as today)")
    box(ax, 11.9, 4.6, 1.75, 0.9, "2813 switch\nthen the Pi, BEC,\nservos (awake)")
    box(ax, 9.6, 0.7, 1.9, 1.2, "MCP73213 charger\nMOVED from the dock\n8.40 V, 1.0 A, 6 h timer\nNTC window 5 to 45 C", fs=7.8)
    box(ax, 11.9, 0.7, 1.75, 1.2, "DK2, 5 A fuse\n2S P45B pack\n(only charges)")
    box(ax, 11.9, 2.7, 1.75, 1.2, "ideal diode DK7\npack to the 2813\n(off the mat)")
    arrow(ax, (5.45, 1.3), (6.75, 1.3), "feet on stripes", off=(0, 0.17))
    arrow(ax, (7.9, 1.9), (7.9, 2.7), "1 wire each", off=(0.55, 0))
    ax.plot([9.05, 9.3], [3.3, 3.3], color=INK, lw=1.3)
    ax.plot([9.3, 9.3], [1.3, 5.05], color=INK, lw=1.3)
    ax.text(8.0, 4.25, "BUS: 2 wires\nup each leg", fontsize=8, color=INK2, ha="center")
    arrow(ax, (9.3, 5.05), (9.6, 5.05))
    arrow(ax, (9.3, 3.3), (9.6, 3.3))
    arrow(ax, (9.3, 1.3), (9.6, 1.3))
    arrow(ax, (11.5, 5.05), (11.9, 5.05))
    ax.text(11.7, 5.75, "runs the duck", fontsize=8, color=INK2, ha="center")
    arrow(ax, (11.5, 1.3), (11.9, 1.3))
    ax.text(11.7, 0.48, "charge", fontsize=8, color=INK2, ha="center")
    arrow(ax, (12.77, 1.9), (12.77, 2.7))
    arrow(ax, (12.77, 3.9), (12.77, 4.6))
    ax.text(7.0, 6.8, "Fig 3. The 2-net circuit (calc only, nothing built). D50 is kept: the mat runs the duck through DK6, the pack only charges.",
            ha="center", fontsize=10.5)
    fig.savefig(os.path.join(HERE, "F3_circuit_2net.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig4():
    fig, ax = plt.subplots(figsize=(10.5, 9))
    MW, MD, F0, F1 = 600, 500, 90, 490          # mat width, depth, striped field from the wall
    ax.add_patch(Rectangle((-28, -360), 28, 720, fc="#b9b8b0", ec=INK2, hatch="///", zorder=1))
    ax.text(-14, 0, "WALL", rotation=90, ha="center", va="center", fontsize=10, weight="bold",
            bbox=dict(fc="#ffffff", ec="none", pad=1.5), zorder=5)
    ax.add_patch(Rectangle((0, -MW / 2), MD, MW, fc="#f0efe9", ec=INK2, lw=1.2, zorder=1))
    stripes(ax, F0, F1, -MW / 2 + 10, MW / 2 - 10)
    ax.add_patch(Rectangle((0, -MW / 2), 60, MW, fc="#d9d8d0", ec=INK2, lw=1.0, zorder=2))
    ax.text(30, 205, "electronics kerb at the wall", rotation=90, ha="center", va="center", fontsize=8.5, color=INK)
    # window for the trunk origin
    ax.add_patch(Rectangle((225, -180), 145, 360, fc="none", ec=VIOLET, lw=2.0, ls=(0, (5, 3)), zorder=5))
    duck(ax, 250, 20, 0, body=True)
    ax.annotate("", xy=(318, 21), xytext=(360, -115), arrowprops=dict(arrowstyle="-", color=INK2, lw=0.9), zorder=9)
    ax.text(385, -128, "duck faces the room", fontsize=9, ha="center", va="center", bbox=dict(fc="#ffffff", ec=GRID, pad=2.5), zorder=9)
    ax.text(297, 215, "trunk centre may be anywhere\nin this box, heading within 60 deg", color=INK, fontsize=9, ha="center", va="center",
            bbox=dict(fc="#ffffff", ec=VIOLET, boxstyle="round,pad=0.3"), zorder=9)
    ax.text(250, -212, "sitting footprint 222 x 262 mm (dashed)", fontsize=8.5, color=INK, ha="center", va="center",
            bbox=dict(fc="#ffffff", ec=GRID, pad=2), zorder=9)
    ax.annotate("", xy=(0, -330), xytext=(MD, -330), arrowprops=dict(arrowstyle="<->", color=INK2))
    ax.text(MD / 2, -345, "mat 500 mm deep, 600 mm along the wall, about 2 mm thick", ha="center", fontsize=9, color=INK2)
    ax.text(560, 0, "ROOM", fontsize=11, color=INK2, ha="center", va="center", rotation=90)
    ax.set_xlim(-40, 600)
    ax.set_ylim(-365, 330)
    ax.set_aspect("equal")
    ax.set_xlabel("distance from the wall, mm")
    ax.set_ylabel("along the wall, mm")
    ax.set_title("Fig 4. Top view: the striped mat against the wall, the duck sitting back to the wall (calc only, to scale)", fontsize=10.5, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "F4_mat_wall_top.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
