"""Figures for the flush-contact study. Calc only. No sim, no hardware.

Run from the repo root:
  python3 altaay_lab/twin/dock/flush/draw_flush.py
Writes figs/F1_belly_field.png and figs/F2_feet_zones.png beside this file.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figs")

# Seat contact patch that actually touches, trunk frame, torque off.
# NATURAL_DOCK_IDEAS.md section 1: x -113 to -103, y +/-28. sim pass only.
PATCH_X = 10.0
PATCH_Y = 56.0
# Five 3 mm wells inside that patch. Spacing is this study's layout. calc only.
WELLS_Y = np.array([-24.0, -12.0, 0.0, 12.0, 24.0])
WELL_R = 1.5
STRIPE = 20.0
GAP = 5.0
PERIOD = STRIPE + GAP
# Active field half-sizes, mm. Chosen so the inscribed window holds the
# straight-crossing worst radial in NEST_SIM_V2.md (158.9 mm, sim pass only).
FIELD_HY = 280.0
FIELD_HX = 180.0


def band(y):
    p = np.mod(y, PERIOD)
    if p >= STRIPE:
        return "G"
    return "P" if int(np.floor(y / PERIOD)) % 2 == 0 else "M"


def classify(heading_deg, phase, need_two=False):
    th = np.deg2rad(heading_deg)
    wy = WELLS_Y * np.cos(th) + phase
    hits = []
    for y in wy:
        labs = [band(y - WELL_R), band(y), band(y + WELL_R)]
        if labs[0] == labs[1] == labs[2] and labs[0] in ("P", "M"):
            hits.append(labs[0])
        elif "P" in labs and "M" in labs:
            return "short"
        else:
            hits.append("miss")
    n_p = hits.count("P")
    n_m = hits.count("M")
    if need_two:
        return "ok" if n_p >= 2 and n_m >= 2 else "miss"
    return "ok" if n_p >= 1 and n_m >= 1 else "miss"


def heading_band(need_two=False):
    phases = np.arange(0.0, PERIOD, 0.25)
    good = []
    for h in range(0, 91):
        if all(classify(h, p, need_two) == "ok" for p in phases):
            good.append(h)
    return good


def window(max_heading):
    th = np.deg2rad(max_heading)
    reach_y = max(abs(WELLS_Y) * np.cos(th)) + WELL_R
    reach_x = max(abs(WELLS_Y) * np.sin(th)) + WELL_R
    # At heading 0 the row is longest in y.
    reach_y = max(reach_y, abs(WELLS_Y).max() + WELL_R)
    hy = FIELD_HY - reach_y
    hx = FIELD_HX - reach_x
    return hy, hx, reach_y, reach_x, min(hy, hx)


def summary():
    one = heading_band(False)
    two = heading_band(True)
    hy, hx, ry, rx, rins = window(max(one) if one else 0)
    return {
        "one_lo": min(one) if one else None,
        "one_hi": max(one) if one else None,
        "two_lo": min(two) if two else None,
        "two_hi": max(two) if two else None,
        "win_y": hy,
        "win_x": hx,
        "reach_y": ry,
        "reach_x": rx,
        "inscribed": rins,
        "field_y": 2 * FIELD_HY,
        "field_x": 2 * FIELD_HX,
    }


def _save(fig, name):
    os.makedirs(FIGS, exist_ok=True)
    path = os.path.join(FIGS, name)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def draw_belly(s):
    fig = plt.figure(figsize=(10.2, 7.4), facecolor="#f7f4ee")
    fig.suptitle("Finalist A. Flush wells in the seat, on a dead-until-covered field",
                 fontsize=13, color="#2b2722", y=0.98)
    ax = fig.add_axes([0.04, 0.38, 0.46, 0.54])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Underside, sitting. Nothing stands proud.", fontsize=10, color="#2b2722")
    # body
    body = FancyBboxPatch((-70, -150), 140, 230, boxstyle="round,pad=2,rounding_size=28",
                           facecolor="#f3efe6", edgecolor="#2b2722", linewidth=1.2)
    ax.add_patch(body)
    # seat
    ax.add_patch(FancyBboxPatch((-32, -128), 64, 28, boxstyle="round,pad=0,rounding_size=6",
                                facecolor="#3a342f", edgecolor="#1c1917", linewidth=0.8))
    for y in WELLS_Y:
        ax.add_patch(Circle((y, -114), 2.2, facecolor="#e0b33a", edgecolor="#7a5a12", linewidth=0.6, zorder=3))
    ax.text(0, -96, "five gold wells, flush", ha="center", va="center", fontsize=7.5, color="#3a342f")
    # bumper, plain
    ax.add_patch(FancyBboxPatch((-24, 18), 48, 16, boxstyle="round,pad=0,rounding_size=5",
                                facecolor="#3a342f", edgecolor="#1c1917", linewidth=0.8))
    ax.text(0, 42, "bumper plain\n2.9 mm up, no metal", ha="center", va="center", fontsize=7, color="#5c564e")
    # feet plain
    for sng, x in ((1, 78), (-1, -78)):
        ax.add_patch(FancyBboxPatch((x - 16, -70), 32, 78, boxstyle="round,pad=0,rounding_size=8",
                                    facecolor="#d9d3c8", edgecolor="#2b2722", linewidth=0.8))
        ax.text(x, -28, "plain\nsole", ha="center", va="center", fontsize=7, color="#5c564e")
    ax.annotate("wires stay\nin the belly", xy=(0, -114), xytext=(0, -168),
                ha="center", fontsize=8, color="#1f4d3a",
                arrowprops=dict(arrowstyle="-", color="#1f4d3a"))
    ax.set_xlim(-120, 120)
    ax.set_ylim(-180, 90)

    ax2 = fig.add_axes([0.52, 0.38, 0.46, 0.54])
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("Mat field. High current only under the seat.", fontsize=10, color="#2b2722")
    ax2.add_patch(Rectangle((-FIELD_HY, -FIELD_HX), 2 * FIELD_HY, 2 * FIELD_HX,
                            facecolor="#c4b49a", edgecolor="#2b2722", linewidth=1.0))
    # stripe hint
    y = -FIELD_HY
    while y < FIELD_HY:
        if band(y + 10) == "P":
            ax2.add_patch(Rectangle((y, -FIELD_HX), min(STRIPE, FIELD_HY - y), 2 * FIELD_HX,
                                    facecolor="#d7b56a", edgecolor="none", alpha=0.55))
        y += PERIOD
    hy, hx = s["win_y"], s["win_x"]
    ax2.add_patch(Rectangle((-hy, -hx), 2 * hy, 2 * hx, fill=False, edgecolor="#1f4d3a",
                            linewidth=1.4, linestyle=(0, (4, 2))))
    ax2.add_patch(Circle((0, 0), 8, facecolor="#3a342f", edgecolor="none"))
    ax2.annotate("seat can land\nanywhere in the box", xy=(0, hx * 0.55), ha="center",
                 fontsize=8, color="#1f4d3a")
    ax2.text(0, -FIELD_HX - 28, "felt  %d x %d mm   window +/-%d along the wall, +/-%d deep" % (
        s["field_y"], s["field_x"], round(hy), round(hx)), ha="center", fontsize=7.5, color="#2b2722")
    ax2.set_xlim(-FIELD_HY - 20, FIELD_HY + 20)
    ax2.set_ylim(-FIELD_HX - 50, FIELD_HX + 30)

    ax3 = fig.add_axes([0.08, 0.06, 0.84, 0.26])
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 30)
    ax3.axis("off")
    ax3.set_title("Section. The gold is level with the seat. The pin tip is level with the felt.", fontsize=10, color="#2b2722")
    ax3.add_patch(Rectangle((6, 10), 58, 7, facecolor="#c4b49a", edgecolor="#2b2722", lw=0.6))
    ax3.add_patch(Rectangle((6, 17), 58, 8, facecolor="#3a342f", edgecolor="#2b2722", lw=0.6))
    ax3.add_patch(Rectangle((30, 17), 7, 2.2, facecolor="#e0b33a", edgecolor="#7a5a12", lw=0.4))
    ax3.add_patch(Rectangle((33.2, 10), 0.9, 7, facecolor="#c0c4c8", edgecolor="#5c656b", lw=0.3))
    ax3.text(33.5, 26.2, "gold, flush with the seat face", fontsize=8, color="#3a342f", ha="center")
    ax3.text(36, 12.5, "pin tip stops at the felt", fontsize=7.5, color="#3a342f", ha="left")
    ax3.text(6, 3.2, "A flat sheet can still touch that gold. Diodes in the belly are what keep it from draining the pack.",
             fontsize=8, color="#6b2d2d")
    return _save(fig, "F1_belly_field.png")


def draw_feet():
    fig = plt.figure(figsize=(10.2, 7.2), facecolor="#f7f4ee")
    fig.suptitle("Finalist B. Flush strips on the inner sole edges", fontsize=13, color="#2b2722", y=0.98)
    ax = fig.add_axes([0.04, 0.34, 0.50, 0.58])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Soles, from below. The strip is flush, and a wire leaves each foot.", fontsize=9.5, color="#2b2722")
    for sng, cx in ((1, 28), (-1, -28)):
        ax.add_patch(FancyBboxPatch((cx - 18, -40), 36, 84, boxstyle="round,pad=0,rounding_size=10",
                                    facecolor="#d9d3c8", edgecolor="#2b2722", lw=1.0))
        # inner edge is toward x=0
        inner = cx - sng * 14
        ax.add_patch(Rectangle((inner - 1.2, -22), 2.4, 50, facecolor="#e0b33a", edgecolor="#7a5a12", lw=0.4))
        ax.plot([cx, cx], [44, 70], color="#1f4d3a", lw=1.4)
        ax.text(cx, 76, "22 AWG\nup the leg", ha="center", fontsize=7, color="#1f4d3a")
    ax.text(0, -58, "left foot is plus, right foot is minus", ha="center", fontsize=8, color="#3a342f")
    ax.set_xlim(-70, 70)
    ax.set_ylim(-70, 95)

    ax2 = fig.add_axes([0.52, 0.34, 0.46, 0.58])
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("Two zones. The box is the published window.", fontsize=9.5, color="#2b2722")
    ax2.add_patch(Rectangle((-160, -120), 320, 240, facecolor="#c4b49a", edgecolor="#2b2722", lw=0.8))
    ax2.add_patch(Rectangle((-160, -120), 140, 240, facecolor="#e4d3a1", edgecolor="none"))
    ax2.add_patch(Rectangle((20, -120), 140, 240, facecolor="#efe6c8", edgecolor="none"))
    ax2.add_patch(Rectangle((-20, -120), 40, 240, facecolor="#8d8478", edgecolor="none"))
    ax2.add_patch(Rectangle((-69, -72), 138, 144, fill=False, edgecolor="#1f4d3a", lw=1.4, linestyle=(0, (4, 2))))
    ax2.text(0, 0, "+/-69 mm\n+/-72 mm\n+/-30 deg", ha="center", va="center", fontsize=8, color="#1f4d3a")
    ax2.text(0, -145, "40 mm dead gap. A metal floor joins the two soles.", ha="center", fontsize=7.5, color="#6b2d2d")
    ax2.set_xlim(-180, 180)
    ax2.set_ylim(-170, 140)

    ax3 = fig.add_axes([0.08, 0.05, 0.84, 0.24])
    ax3.axis("off")
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 20)
    ax3.text(2, 14, "The strip does not protrude. It is on the walking face, so it scuffs every step.",
             fontsize=9, color="#2b2722")
    ax3.text(2, 8, "One new 22 AWG wire per leg crosses hip yaw, hip roll, hip pitch, the knee, and the ankle.",
             fontsize=9, color="#2b2722")
    ax3.text(2, 2, "That is the same walk the servo wires already take, plus the first power wire through the ankle.",
             fontsize=9, color="#1f4d3a")
    return _save(fig, "F2_feet_zones.png")


def main():
    s = summary()
    print("heading one-each deg", s["one_lo"], s["one_hi"])
    print("heading two-each deg", s["two_lo"], s["two_hi"])
    print("window +/-y %.1f +/-x %.1f inscribed %.1f" % (s["win_y"], s["win_x"], s["inscribed"]))
    print("reach y %.2f x %.2f" % (s["reach_y"], s["reach_x"]))
    print(_save_msg(draw_belly(s)))
    print(_save_msg(draw_feet()))


def _save_msg(path):
    return "%s %d" % (path, os.path.getsize(path))


if __name__ == "__main__":
    main()
