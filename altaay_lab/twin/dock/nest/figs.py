#!/usr/bin/env python3
"""figs.py: the sketches of NATURAL_DOCK_IDEAS.md. To scale (mm), real duck outline (duck_outline.json, sim pass only pose).
Feel sketches: A1/A2 (nest with a sun), B1/B2 (pond rug), C1/C2 (hidden coil nest). Technical: A3, B3, C3, T1.
  python3 figs.py
"""
import json
import os

import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, Wedge

from ducklib import BG, INK, INK2, SOFT, WALL, FLOOR, clean, duck_side, duck_top, plt

HERE = os.path.dirname(os.path.abspath(__file__))
COV = json.load(open(os.path.join(HERE, "coverage.json")))
SC = json.load(open(os.path.join(HERE, "sit_contacts.json")))
TP = json.load(open(os.path.join(HERE, "turn_probe.json")))

FELT, FELT_E, RIM, RIM_E = "#cfdcbc", "#9fb487", "#b9cba3", "#8fa678"
SUN, SUN_E, RINGC, RING_E = "#e9bd55", "#bb8f2a", "#f3e2a9", "#cdb669"
SAND, WATER, WATER_E, REED = "#ecdcb4", "#b4d6e6", "#7fb0c6", "#a9c08c"
SEAT_X, BUMP_X = COV["inputs"]["seat_button_x"], COV["inputs"]["bumper_button_x"]
RC = COV["concentric_pick"]["centre_disc_radius_mm"]
GAP = COV["concentric_pick"]["gap_mm"]
ROUT = COV["concentric_pick"]["ring_outer_radius_mm"]
WIN = COV["concentric_pick"]["any_heading_window_radius_mm"]
BACK_SHIFT = 18.7          # the trunk origin moves back this much from the stand to the sit (sit_soles.json)
PIVOT = 68.0               # the turn on the spot pivots about a point this far behind the trunk origin (turn_probe.json)
# concept A / C: the sun (seat-button target) 190 mm from the wall
SUNX = 190.0
TRUNK_A = SUNX - SEAT_X    # trunk origin of the sitting duck
PIV_A = TRUNK_A + BACK_SHIFT - PIVOT
# concept B: bands
BA0, BA1, BB0, BB1, BHW = 140.0, 250.0, 282.0, 520.0, 280.0
SEATB = [b for b in COV["bands_pick"]["windows"] if b["yaw"] == 0][0]["centre_from_wall"]
TRUNK_B = SEATB - SEAT_X
PIV_B = TRUNK_B + BACK_SHIFT - PIVOT


def arrow(ax, p0, p1, col=INK2, lw=1.6, rad=0.0, ms=14, z=9, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, color=col, lw=lw, zorder=z,
                                 connectionstyle="arc3,rad=%g" % rad, linestyle=ls))


def label(ax, xy, txt, to=None, ha="left", va="center", fs=10.5, col=INK, rad=0.0):
    if to is not None:
        ax.annotate(txt, xy=to, xytext=xy, ha=ha, va=va, fontsize=fs, color=col, zorder=12,
                    arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8, shrinkA=2, shrinkB=2, connectionstyle="arc3,rad=%g" % rad))
    else:
        ax.text(xy[0], xy[1], txt, ha=ha, va=va, fontsize=fs, color=col, zorder=12)


def face_mark(ax, x, y, yaw):
    """two small eyes on the head so the facing direction reads in a top view"""
    c, s = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    for sg in (-1, 1):
        px, py = 52, sg * 30
        ax.add_patch(Circle((x + px * c - py * s, y + px * s + py * c), 7, fc="#3b382f", ec="none", zorder=8))


def eye_side(ax, x0, pose):
    z = 268 if pose == "sit" else 408
    ax.add_patch(Circle((x0 + 38, z), 7, fc="#3b382f", ec="none", zorder=8))


def room_side(ax, x1, zmax):
    ax.add_patch(Rectangle((-40, -18), 40, zmax + 18, fc=WALL, ec="none", zorder=1))
    ax.add_patch(Rectangle((-40, -18), x1 + 40, 18, fc=FLOOR, ec="none", zorder=1))
    ax.plot([0, 0], [0, zmax], color=SOFT, lw=1.2, zorder=2)
    ax.plot([0, x1], [0, 0], color=SOFT, lw=1.2, zorder=2)


def room_top(ax, y0, y1):
    ax.add_patch(Rectangle((-40, y0), 40, y1 - y0, fc=WALL, ec="none", zorder=1))
    ax.plot([0, 0], [y0, y1], color=SOFT, lw=1.2, zorder=2)


# ------------------------------------------------------------------ nest shapes
def nest_top(ax, zones=True, stitched=False, z=2):
    R = ROUT + 12
    th = np.linspace(0, 2 * np.pi, 400)
    P = np.c_[SUNX + R * np.cos(th), R * np.sin(th)]
    P[:, 0] = np.maximum(P[:, 0], 22)
    ax.add_patch(Polygon(P, closed=True, fc=FELT, ec=FELT_E, lw=1.2, zorder=z))
    if zones:
        Q = np.c_[SUNX + ROUT * np.cos(th), ROUT * np.sin(th)]
        Q[:, 0] = np.maximum(Q[:, 0], 74)
        ax.add_patch(Polygon(Q, closed=True, fc=RINGC, ec=RING_E, lw=1.0, zorder=z + 0.1))
        ax.add_patch(Circle((SUNX, 0), RC + GAP, fc=FELT, ec=RING_E, lw=1.0, zorder=z + 0.2))
        ax.add_patch(Circle((SUNX, 0), RC, fc=SUN, ec=SUN_E, lw=1.2, zorder=z + 0.3))
    if stitched:
        ax.add_patch(Circle((SUNX + 63, 0), 85, fc="none", ec="#6f8a58", lw=2.0, ls=(0, (2, 2.5)), zorder=z + 0.2))
    # soft rim along the wall
    yy = np.linspace(-(R - 20), R - 20, 80)
    out = np.c_[22 + 0 * yy, yy]
    inn = np.c_[72 - 14 * (yy / (R - 20)) ** 2, yy[::-1]]
    ax.add_patch(Polygon(np.r_[out, inn], closed=True, fc=RIM, ec=RIM_E, lw=1.2, zorder=z + 0.5, joinstyle="round"))


def nest_side(ax, zones=True, coil=False):
    R = ROUT + 12
    ax.add_patch(Rectangle((22, 0), SUNX + R - 22, 2.5, fc=FELT, ec=FELT_E, lw=0.8, zorder=3))
    if zones:
        ax.add_patch(Rectangle((74, 2.5), SUNX - RC - GAP - 74, 1.2, fc=RINGC, ec=RING_E, lw=0.5, zorder=3.1))
        ax.add_patch(Rectangle((SUNX + RC + GAP, 2.5), ROUT - RC - GAP, 1.2, fc=RINGC, ec=RING_E, lw=0.5, zorder=3.1))
        ax.add_patch(Rectangle((SUNX - RC, 2.5), 2 * RC, 1.2, fc=SUN, ec=SUN_E, lw=0.5, zorder=3.1))
    ax.add_patch(FancyBboxPatch((24, 2), 44, 30, boxstyle="round,pad=0,rounding_size=14", fc=RIM, ec=RIM_E, lw=1.0, zorder=3.2))


def rug_top(ax, z=2):
    ax.add_patch(FancyBboxPatch((BA0 - 30, -BHW - 20), BB1 - BA0 + 50, 2 * BHW + 40, boxstyle="round,pad=0,rounding_size=30", fc="#f1ead8", ec="#cbbf9f", lw=1.2, zorder=z))
    ax.add_patch(FancyBboxPatch((BA0, -BHW), BA1 - BA0, 2 * BHW, boxstyle="round,pad=0,rounding_size=14", fc=SAND, ec="#c9b37c", lw=1.0, zorder=z + 0.1))
    ax.add_patch(FancyBboxPatch((BB0, -BHW), BB1 - BB0, 2 * BHW, boxstyle="round,pad=0,rounding_size=14", fc=WATER, ec=WATER_E, lw=1.0, zorder=z + 0.1))
    ax.add_patch(Rectangle((BA1 + 4, -BHW + 6), BB0 - BA1 - 8, 2 * BHW - 12, fc=REED, ec="none", zorder=z + 0.05, alpha=0.9))
    for yy, r in ((-190, 26), (150, 32), (40, 20)):                       # lily pads printed on the water, decoration only
        ax.add_patch(Wedge((BB1 - 60, yy), r, 25, 345, fc="#9cc7a0", ec="#6fa377", lw=0.8, zorder=z + 0.2))
    # low reed box on the wall (electronics inside)
    ax.add_patch(FancyBboxPatch((6, -150), 56, 300, boxstyle="round,pad=0,rounding_size=10", fc=RIM, ec=RIM_E, lw=1.2, zorder=z + 0.3))


def rug_side(ax):
    ax.add_patch(Rectangle((BA0 - 30, 0), BB1 - BA0 + 50, 2.5, fc="#f1ead8", ec="#cbbf9f", lw=0.8, zorder=3))
    ax.add_patch(Rectangle((BA0, 2.5), BA1 - BA0, 1.2, fc=SAND, ec="#c9b37c", lw=0.5, zorder=3.1))
    ax.add_patch(Rectangle((BB0, 2.5), BB1 - BB0, 1.2, fc=WATER, ec=WATER_E, lw=0.5, zorder=3.1))
    ax.add_patch(FancyBboxPatch((6, 0), 56, 60, boxstyle="round,pad=0,rounding_size=10", fc=RIM, ec=RIM_E, lw=1.0, zorder=3.2))
    for i, (xx, hh) in enumerate(((16, 150), (26, 210), (36, 175), (46, 235), (54, 160))):      # felt reeds, decoration
        ax.plot([xx, xx + (i % 2) * 4 - 2], [60, 60 + hh], color="#8fa678", lw=2.2, zorder=3.1, solid_capstyle="round")
        ax.add_patch(Ellipse((xx + (i % 2) * 4 - 2, 60 + hh), 9, 34, fc="#8a6a45", ec="none", zorder=3.15))


# ------------------------------------------------------------------ feel sheets: side + top
def sheet(tag, title, sub, top_fn, side_fn, trunk_x, notes_side, notes_top, keel=False, fname=None):
    fig = plt.figure(figsize=(15, 7.6))
    a1 = fig.add_axes([0.03, 0.08, 0.44, 0.76])
    a2 = fig.add_axes([0.52, 0.08, 0.46, 0.76])
    room_side(a1, 640, 430)
    side_fn(a1)
    duck_side(a1, trunk_x, "sit", z0=3.0)
    eye_side(a1, trunk_x, "sit")
    if keel:
        a1.add_patch(FancyBboxPatch((trunk_x - 92, 4.5), 112, 9, boxstyle="round,pad=0,rounding_size=4", fc="#8fb0cf", ec="#5f86ab", lw=0.8, zorder=6))
    a1.set_xlim(-40, 640)
    a1.set_ylim(-18, 430)
    clean(a1)
    for (xy, txt, to, ha) in notes_side:
        label(a1, xy, txt, to, ha=ha)
    a1.text(-40, 445, "From the side", fontsize=12, color=INK2)
    room_top(a2, -330, 330)
    top_fn(a2)
    duck_top(a2, trunk_x, 0, 0, "sit", alpha=0.62)
    face_mark(a2, trunk_x, 0, 0)
    a2.set_xlim(-40, 760)
    a2.set_ylim(-330, 330)
    clean(a2)
    for (xy, txt, to, ha) in notes_top:
        label(a2, xy, txt, to, ha=ha)
    a2.text(-40, 345, "From above", fontsize=12, color=INK2)
    # scale bar
    a2.plot([600, 700], [-305, -305], color=INK2, lw=2)
    a2.text(650, -292, "10 cm", ha="center", fontsize=9.5, color=INK2)
    fig.text(0.03, 0.945, title, fontsize=17, color=INK, weight="bold")
    fig.text(0.03, 0.895, sub, fontsize=11.5, color=INK2)
    fig.savefig(os.path.join(HERE, fname), dpi=120)
    plt.close(fig)


def strip(title, sub, frames, top_fn, fname, xlim=(-40, 800), ylim=(-300, 300), h=5.6):
    n = len(frames)
    fig = plt.figure(figsize=(3.3 * n, h))
    for i, fr in enumerate(frames):
        ax = fig.add_axes([0.01 + i * (0.99 / n), 0.24, 0.99 / n - 0.008, 0.58])
        room_top(ax, *ylim)
        top_fn(ax)
        for (x, y, yaw, pose, alpha) in fr["ducks"]:
            duck_top(ax, x, y, yaw, pose, alpha=alpha)
            if alpha > 0.6:
                face_mark(ax, x, y, yaw)
        for a in fr.get("arrows", []):
            arrow(ax, a[0], a[1], rad=a[2] if len(a) > 2 else 0.0, col="#4a6fa5", lw=2.0, ms=16)
        for (xy, t) in fr.get("texts", []):
            ax.text(xy[0], xy[1], t, fontsize=10, color=INK2, ha="center", va="center", zorder=12)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        clean(ax)
        fig.text(0.01 + i * (0.99 / n) + 0.004, 0.83, "%d" % (i + 1), fontsize=15, color="#4a6fa5", weight="bold")
        fig.text(0.01 + i * (0.99 / n) + 0.004, 0.21, fr["cap"], fontsize=11, color=INK, va="top", linespacing=1.35)
    fig.text(0.012, 0.95, title, fontsize=16, color=INK, weight="bold")
    fig.text(0.012, 0.905, sub, fontsize=11, color=INK2)
    fig.savefig(os.path.join(HERE, fname), dpi=115)
    plt.close(fig)


def stand_origin(pivot_xy, yaw):
    c, s = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    return pivot_xy[0] + PIVOT * c, pivot_xy[1] + PIVOT * s


def concept_A():
    sheet("A", "A. The nest with a sun", "A thin felt nest against the wall. The duck sits on the golden sun and charges through two soft buttons under its belly.",
          lambda ax: nest_top(ax, True), lambda ax: nest_side(ax, True), TRUNK_A,
          [((330, 395), "awake, head up,\nlooking at the room", (TRUNK_A + 40, 300), "left"),
           ((18, 150), "soft rim\n(plug and small\nelectronics inside)", (46, 34), "left"),
           ((440, 175), "golden cloth sun and ring\n(the sun is under the tail)", (SUNX + RC + GAP + 60, 5), "left"),
           ((500, 70), "felt nest, about 2 mm thin,\nflat enough to walk onto", (434, 2), "left")],
          [((560, 250), "golden sun, 10 cm across\n(under the tail)", (SUNX + 20, 36), "left"),
           ((560, 150), "pale gold ring", (SUNX + 200, 90), "left"),
           ((30, -300), "soft rim", (50, -200), "left"),
           ((560, -200), "open to the room:\nno edge to climb", (SUNX + ROUT, -120), "left")],
          fname="A1_nest_sun_side_top.png")
    px, py = PIV_A, 0.0
    f = []
    x1, y1 = stand_origin((px + 400, 60), 187)
    f.append(dict(ducks=[(x1, y1, 187, "stand", 1.0)], arrows=[((x1 - 170, y1 - 20), (px + 60, 8))],
                  cap="Feels low on energy, spots\nits nest and waddles over."))
    x2, y2 = stand_origin((px, py), 180)
    f.append(dict(ducks=[(x2, y2, 180, "stand", 1.0)], cap="Walks onto the felt and\nstops in the middle."))
    x3, y3 = stand_origin((px, py), 265)
    f.append(dict(ducks=[(x2, y2, 180, "stand", 0.25), (x3, y3, 265, "stand", 1.0)],
                  arrows=[((px + 150, 150), (px + 190, -60), -0.5)], cap="Turns round on the spot,\nlike a dog circling its bed."))
    f.append(dict(ducks=[(TRUNK_A, 0, 0, "sit", 1.0)], cap="Faces the room and sits down.\nNo power? It wiggles and\nsits again."))
    f.append(dict(ducks=[(TRUNK_A, 0, 0, "sit", 1.0)], texts=[((TRUNK_A + 340, 190), "awake,\nwatching\nthe room")],
                  cap="Rests and charges with motors\nrelaxed, still awake and\nlooking around."))
    x6, _ = stand_origin((px + 250, 0), 0)
    f.append(dict(ducks=[(TRUNK_A, 0, 0, "sit", 0.22), (x6, 0, 0, "stand", 1.0)], arrows=[((x6 + 110, 0), (x6 + 220, 0))],
                  cap="Full again: stands up and\nwalks straight out."))
    strip("A. Going to the nest", "Seen from above. The wall is on the left.", f, lambda ax: nest_top(ax, True), "A2_nest_sun_approach.png")


def concept_B():
    sheet("B", "B. The pond rug", "A flat two-tone rug along the wall: sand shore and blue water. The same two belly buttons; one lands on each colour.",
          rug_top, rug_side, TRUNK_B,
          [((330, 395), "awake, head up,\nlooking at the room", (TRUNK_B + 40, 300), "left"),
           ((8, 400), "felt reeds on a low box\n(plug and electronics inside)", (40, 290), "left"),
           ((455, 120), "sand cloth under the tail,\nblue cloth under the chest", (BB0 + 30, 5), "left")],
          [((580, 270), "blue cloth 'water'", (BB1 - 40, 230), "left"),
           ((60, 315), "sand cloth 'shore'", (BA0 + 50, 265), "left"),
           ((580, -210), "long along the wall:\nit can sit anywhere\nalong the rug", (BB1 - 10, -200), "left"),
           ((2, -250), "low reed\nbox", (30, -152), "left")],
          fname="B1_pond_rug_side_top.png")
    px = PIV_B
    f = []
    x1, y1 = stand_origin((px + 20, 560), 268)
    f.append(dict(ducks=[(x1, y1, 268, "stand", 1.0)], arrows=[((px + 10, 420), (px + 2, 290))], cap="Comes along the wall,\nlike walking a shoreline."))
    x2, y2 = stand_origin((px, 30), 270)
    f.append(dict(ducks=[(x2, y2, 270, "stand", 1.0)], cap="Steps onto the rug and\nstops. Anywhere along\nit will do."))
    x3, y3 = stand_origin((px, 30), 315)
    f.append(dict(ducks=[(x2, y2, 270, "stand", 0.25), (x3, y3, 315, "stand", 1.0)], arrows=[((px + 60, -190), (px + 215, -80), 0.4)],
                  cap="A quarter turn to face\nthe room. No backing up."))
    f.append(dict(ducks=[(TRUNK_B, 30, 0, "sit", 1.0)], cap="Sits: tail on the sand,\nchest over the water.\nCharges, awake."))
    x5, _ = stand_origin((px + 250, 30), 0)
    f.append(dict(ducks=[(TRUNK_B, 30, 0, "sit", 0.22), (x5, 30, 0, "stand", 1.0)], arrows=[((x5 + 110, 30), (x5 + 210, 30))],
                  cap="Later it stands and walks\nstraight out into the room."))
    strip("B. Coming home along the shore", "Seen from above. The wall is on the left.", f, rug_top, "B2_pond_rug_approach.png", xlim=(-40, 800), ylim=(-330, 700), h=7.4)


def concept_C():
    sheet("C", "C. The plain nest (no contacts, charging through the felt)", "The same nest with nothing on it. A hidden coil under the felt powers a flat pad under the duck's belly.",
          lambda ax: nest_top(ax, False, True), lambda ax: nest_side(ax, False), TRUNK_A,
          [((330, 395), "awake, head up,\nlooking at the room", (TRUNK_A + 40, 300), "left"),
           ((18, 150), "soft rim\n(plug and\nelectronics inside)", (46, 34), "left"),
           ((440, 175), "flat pad under the belly\nrests just above the felt", (TRUNK_A + 14, 11), "left"),
           ((500, 70), "plain felt: no metal,\nnothing to see", (434, 2), "left")],
          [((560, 250), "plain felt nest", (SUNX + 150, 150), "left"),
           ((560, 150), "a stitched circle shows\nwhere to sit", (SUNX + 63 + 60, 61), "left"),
           ((30, -300), "soft rim", (50, -200), "left")],
          keel=True, fname="C1_plain_nest_side_top.png")
    px, py = PIV_A, 0.0
    f = []
    x1, y1 = stand_origin((px + 400, -60), 173)
    f.append(dict(ducks=[(x1, y1, 173, "stand", 1.0)], arrows=[((x1 - 170, y1 + 20), (px + 60, -8))], cap="Heads for its nest."))
    x2, y2 = stand_origin((px, py), 180)
    f.append(dict(ducks=[(x2, y2, 180, "stand", 1.0)], cap="Walks on and stops over\nthe stitched circle."))
    x3, y3 = stand_origin((px, py), 265)
    f.append(dict(ducks=[(x2, y2, 180, "stand", 0.25), (x3, y3, 265, "stand", 1.0)], arrows=[((px + 150, 150), (px + 190, -60), -0.5)],
                  cap="Turns round on the spot."))
    f.append(dict(ducks=[(TRUNK_A, 0, 0, "sit", 1.0)], cap="Sits. It must land within\nabout a hand's width of\nthe circle, or shuffle."))
    f.append(dict(ducks=[(TRUNK_A, 0, 0, "sit", 1.0)], texts=[((TRUNK_A + 340, 190), "awake,\nwatching\nthe room")], cap="Charges through the felt.\nNothing touches metal."))
    strip("C. Same nest, same habit, nothing to see", "Seen from above. The wall is on the left.", f, lambda ax: nest_top(ax, False, True), "C2_plain_nest_approach.png")


# ------------------------------------------------------------------ technical figures
def tech_A():
    fig = plt.figure(figsize=(14.5, 7.4))
    ax = fig.add_axes([0.02, 0.05, 0.56, 0.84])
    room_top(ax, -290, 290)
    nest_top(ax, True)
    duck_top(ax, TRUNK_A, 0, 0, "sit", alpha=0.18)
    ax.add_patch(Circle((SUNX, 0), WIN, fc="none", ec="#1baf7a", lw=2.0, ls=(0, (5, 3)), zorder=9))
    for sg in (-1, 1):
        ax.plot(SUNX, sg * 10, "o", ms=7, mfc="#eb6834", mec=INK, mew=0.8, zorder=10)
        ax.plot(SUNX + BUMP_X - SEAT_X, sg * 10, "o", ms=7, mfc="#2a78d6", mec=INK, mew=0.8, zorder=10)
    label(ax, (500, 255), "seat buttons (+), 2 spring pins", (SUNX + 3, 12), fs=10)
    label(ax, (500, 215), "bumper buttons (-), 2 spring pins,\n%.0f mm in front of the seat buttons" % (BUMP_X - SEAT_X), (SUNX + BUMP_X - SEAT_X + 4, 12), fs=10)
    label(ax, (500, -150), "green dashed: the seat buttons may land\nanywhere inside, at any heading\n(radius %.0f mm, calc only)" % WIN, (SUNX + WIN * 0.7, -WIN * 0.7), fs=10)
    label(ax, (500, -235), "sun: %d mm across; felt gap %d mm;\nring out to %d mm across" % (2 * RC, GAP, 2 * ROUT), (SUNX + RC + GAP / 2, -50), fs=10)
    ax.annotate("", xy=(SUNX, -262), xytext=(0, -262), arrowprops=dict(arrowstyle="<->", color=INK2, lw=1))
    ax.text(SUNX / 2, -280, "%d mm from the wall" % SUNX, ha="center", fontsize=9.5, color=INK2)
    ax.set_xlim(-40, 780)
    ax.set_ylim(-295, 295)
    clean(ax)
    # side detail (schematic, heights to scale x4)
    a2 = fig.add_axes([0.61, 0.5, 0.37, 0.36])
    a2.add_patch(Rectangle((-170, -6), 300, 6, fc=FELT, ec=FELT_E, lw=0.8))
    a2.add_patch(Rectangle((-150, 0), 80, 2.5, fc=SUN, ec=SUN_E, lw=0.6))
    a2.add_patch(Rectangle((-40, 0), 160, 2.5, fc=RINGC, ec=RING_E, lw=0.6))
    a2.add_patch(FancyBboxPatch((-124, 3), 32, 40, boxstyle="round,pad=0,rounding_size=8", fc="#8fb0cf", ec="#5f86ab", lw=1))
    a2.add_patch(FancyBboxPatch((10, 14), 25, 30, boxstyle="round,pad=0,rounding_size=7", fc="#8fb0cf", ec="#5f86ab", lw=1))
    a2.add_patch(Rectangle((-135, 43), 185, 16, fc="#f8d559", ec="#c9a02a", lw=1))
    a2.plot([-108, -108], [2.5, 10], color="#eb6834", lw=3.5, solid_capstyle="round")
    a2.plot([22.5, 22.5], [2.5, 20], color="#2a78d6", lw=3.5, solid_capstyle="round")
    a2.text(-25, 51, "belly", ha="center", va="center", fontsize=9)
    a2.text(-86, 30, "seat\nblock", ha="left", va="center", fontsize=9)
    a2.text(-18, 34, "bumper", ha="left", va="center", fontsize=9)
    label(a2, (-165, 28), "rests on\nthe felt", (-122, 5), fs=9, ha="left")
    label(a2, (50, 24), "about 3 mm above the felt:\nits pin reaches down", (24, 9), fs=9)
    a2.set_xlim(-175, 135)
    a2.set_ylim(-12, 64)
    a2.set_aspect(2.2)
    a2.set_xticks([]); a2.set_yticks([])
    for s in a2.spines.values():
        s.set_visible(False)
    a2.set_title("Under the belly (side cut, heights stretched)", fontsize=10.5, color=INK2, loc="left")
    c = SC["flat_floor"]["contacts"]
    seat = [v["N"] for k, v in c.items() if "seat" in k][0]
    soles = [v["N"] for k, v in c.items() if "foot" in k]
    mc = COV["monte_carlo_first_sit"]["rows"]
    t180 = TP["summary"]["1.0"]["180"]
    txt = ("Numbers (sim pass only unless marked)\n"
           "- In the sit, torque off: soles %.1f and %.1f N, seat block %.2f N,\n  bumper %.1f mm above the floor (not touching).\n"
           "- So contact force must come from the pin springs:\n  about 1 N per pin, 2 pins per pole (calc only).\n"
           "- Standing, the seat block is %.0f mm and the bumper %.0f mm up:\n  the pins never touch the floor while walking.\n"
           "- Turn on the spot, stock walk: 180 deg in %.1f s, 0 falls in 40 runs;\n  the body shifts %.0f mm but the same way each time (spread %.0f mm).\n"
           "- First-sit success with that scatter: %.1f %% (calc only).\n"
           "- Current: 2.0 A typical, 2.8 A peak through each pole."
           % (soles[0], soles[1], seat, SC["flat_floor"]["geometry"]["bumper"]["lowest_z"], SC["standing"]["geometry"]["seat"]["lowest_z"],
              SC["standing"]["geometry"]["bumper"]["lowest_z"], t180["time_s_mean"], t180["dist_mm_mean"], t180["scatter_about_mean_mm_max"],
              100 * mc[1]["nest_sun_concentric"]["first_sit"]))
    fig.text(0.61, 0.43, txt, fontsize=10, color=INK, va="top", linespacing=1.45)
    fig.text(0.02, 0.945, "A3. Nest with a sun: the technical view (to scale, mm)", fontsize=15, color=INK, weight="bold")
    fig.savefig(os.path.join(HERE, "A3_nest_sun_technical.png"), dpi=115)
    plt.close(fig)


def tech_B():
    fig = plt.figure(figsize=(14.5, 7.4))
    ax = fig.add_axes([0.02, 0.05, 0.56, 0.84])
    room_top(ax, -330, 330)
    rug_top(ax)
    duck_top(ax, TRUNK_B, 0, 0, "sit", alpha=0.18)
    w0 = [b for b in COV["bands_pick"]["windows"] if b["yaw"] == 0][0]
    ax.add_patch(Rectangle((SEATB - w0["fore_aft_window_mm"] / 2, -247), w0["fore_aft_window_mm"], 494, fc="none", ec="#1baf7a", lw=2.0, ls=(0, (5, 3)), zorder=9))
    for sg in (-1, 1):
        ax.plot(SEATB, sg * 10, "o", ms=7, mfc="#eb6834", mec=INK, mew=0.8, zorder=10)
        ax.plot(SEATB + BUMP_X - SEAT_X, sg * 10, "o", ms=7, mfc="#2a78d6", mec=INK, mew=0.8, zorder=10)
    label(ax, (560, 285), "seat buttons", (SEATB + 3, 12), fs=10)
    label(ax, (560, 245), "bumper buttons", (SEATB + BUMP_X - SEAT_X + 4, 12), fs=10)
    label(ax, (560, -120), "green dashed: where the seat\nbuttons may land when the\nduck faces the room", (SEATB + 40, -160), fs=10)
    ax.text(BA0 - 30, -335, "shore band %d to %d mm from the wall, water band %d to %d mm" % (BA0, BA1, BB0, BB1), ha="left", fontsize=9.5, color=INK2)
    ax.set_xlim(-40, 800)
    ax.set_ylim(-350, 330)
    clean(ax)
    rows = COV["bands_pick"]["windows"]
    mc = COV["monte_carlo_first_sit"]["rows"]
    txt = ("Window of the seat buttons (calc only)\n"
           "- along the wall: %s mm\n" % COV["bands_pick"]["along_wall_window_mm"]
           + "".join("- facing within %d deg of the room: %.0f mm deep (+/-%.0f)\n" % (r["yaw"], r["fore_aft_window_mm"], r["fore_aft_window_mm"] / 2) for r in rows if r["yaw"] in (0, 30, 45, 60))
           + "- felt gap between the colours: 32 mm\n\n"
           "First-sit success for an assumed landing scatter (calc only)\n"
           + "".join("- 1 sigma %d mm, %d deg: rug %.0f %%, nest with a sun %.0f %%\n" % (r["sigma_mm"][0], r["sigma_yaw_deg"], 100 * r["pond_two_bands"]["first_sit"], 100 * r["nest_sun_concentric"]["first_sit"]) for r in mc)
           + "\nSame duck parts as concept A. Facing the wrong way swaps\nplus and minus: a small ideal-diode bridge in the duck\naccepts both, or the duck just does not charge.\n"
           "More bare cloth is uncovered than in A: the shore band\nis live along its whole length while the duck charges.")
    fig.text(0.6, 0.86, txt, fontsize=10, color=INK, va="top", linespacing=1.45)
    fig.text(0.02, 0.945, "B3. Pond rug: the technical view (to scale, mm)", fontsize=15, color=INK, weight="bold")
    fig.savefig(os.path.join(HERE, "B3_pond_rug_technical.png"), dpi=115)
    plt.close(fig)


def tech_C():
    fig = plt.figure(figsize=(14.5, 6.6))
    ax = fig.add_axes([0.06, 0.12, 0.5, 0.7])
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"]
    short = ["A phone-size pair (50 mm)", "B hobby pair (82 mm)", "C small 30 mm receiver", "D wide 160 mm sender,\n   50 mm receiver", "E wide 160 mm sender,\n   82 mm receiver"]
    ypos = {}
    for (nm, v), col, sh in zip(COV["coils"].items(), cols, short):
        xs = [r["offset_mm"] for r in v["rows"]]
        ys = [max(r["k"], 0) for r in v["rows"]]
        ax.plot(xs, ys, color=col, lw=2, marker="o", ms=5, mec=BG, mew=1.2, zorder=4)
        ypos[sh] = (ys, col)
    ax.axvspan(0, 45, color="#1baf7a", alpha=0.06, zorder=0)
    ax.text(0, 0.815, "shaded: the 45 mm that the nest with a sun forgives", ha="left", fontsize=9.5, color=INK2, clip_on=False)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 0.8)
    ax.set_xlabel("how far off-centre the duck sits, mm", color=INK2)
    ax.set_ylabel("coupling between the two coils (1 = perfect)", color=INK2)
    ax.grid(color="#e6e2d6", lw=0.8)
    ax.tick_params(colors=INK2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    hs = [plt.Line2D([], [], color=c, lw=2, marker="o", ms=5, label=s.replace("\n   ", " ")) for c, s in zip(cols, short)]
    ax.legend(handles=hs, loc="upper right", ncol=1, frameon=True, facecolor=BG, edgecolor="#e6e2d6", fontsize=9.5)
    # cross-section
    a2 = fig.add_axes([0.6, 0.5, 0.38, 0.32])
    a2.add_patch(Rectangle((-150, -6), 300, 3, fc="#d9d3c4", ec="none"))
    a2.add_patch(Rectangle((-80, -3), 160, 2.2, fc="#c98a4b", ec="#9a6226", lw=0.6))
    a2.add_patch(Rectangle((-150, -0.8), 300, 1.6, fc=FELT, ec=FELT_E, lw=0.6))
    a2.add_patch(FancyBboxPatch((-56, 3.5), 112, 9, boxstyle="round,pad=0,rounding_size=3", fc="#8fb0cf", ec="#5f86ab", lw=1))
    a2.add_patch(Rectangle((-25, 4.6), 50, 1.6, fc="#c98a4b", ec="#9a6226", lw=0.6))
    a2.add_patch(Rectangle((-28, 6.4), 56, 0.8, fc="#55524a", ec="none"))
    a2.add_patch(Rectangle((-70, 12.5), 150, 10, fc="#f8d559", ec="#c9a02a", lw=1))
    a2.text(5, 17.5, "belly (the cells are above 11 mm of plastic)", ha="center", va="center", fontsize=8.5)
    label(a2, (62, 8.5), "belly pad with the\nreceiver coil and shield", (30, 6), fs=9)
    label(a2, (95, -9.5), "sender coil under the felt", (60, -2), fs=9, va="top")
    label(a2, (-148, 6), "air gap\n2 to 3 mm", (-45, 2.2), fs=9)
    a2.set_xlim(-155, 155)
    a2.set_ylim(-13, 24)
    a2.set_aspect(4.0)
    a2.set_xticks([]); a2.set_yticks([])
    for s in a2.spines.values():
        s.set_visible(False)
    a2.set_title("Side cut (heights stretched)", fontsize=10.5, color=INK2, loc="left")
    h = COV["wireless_budget"]
    txt = ("What this says (calc only, air-core model)\n"
           "- Phone-size coils keep 70 %% of their coupling only within about 10 mm.\n"
           "  The duck needs about 45 mm. A wide sender coil gets there, but it is\n  a custom part and its coupling is 3 times weaker.\n"
           "- Power needed: %.1f W typical, %.1f W at the peak. A 15 W phone-class\n  receiver cannot run and charge the duck at the peak: the pack helps out.\n"
           "- Heat: about %.1f W in the belly pad (outside the body), %.1f W in the nest,\n  %.1f W in a charger inside the body."
           % (h["needs"]["total_typ_interface_W"], h["needs"]["total_peak_W"], h["heat"][1]["loss_in_receiver_coil_and_rectifier_W"],
              h["heat"][1]["loss_in_dock_W"], h["heat"][1]["loss_in_switching_charger_in_trunk_W"]))
    fig.text(0.6, 0.42, txt, fontsize=9.8, color=INK, va="top", linespacing=1.45)
    fig.text(0.03, 0.93, "C3. Charging through the felt: how much sideways error the coils forgive", fontsize=15, color=INK, weight="bold")
    fig.savefig(os.path.join(HERE, "C3_plain_nest_technical.png"), dpi=115)
    plt.close(fig)


def tech_T1():
    fig = plt.figure(figsize=(13.5, 6.2))
    ax = fig.add_axes([0.02, 0.06, 0.47, 0.78])
    ax.add_patch(Rectangle((-240, -14), 420, 14, fc=FLOOR, ec="none"))
    duck_side(ax, 0, "sit")
    eye_side(ax, 0, "sit")
    c = SC["flat_floor"]["contacts"]
    seat = [v for k, v in c.items() if "seat" in k][0]
    soles = [v for k, v in c.items() if "foot" in k]
    label(ax, (-235, 190), "tail: the rear-most point,\n%.0f mm behind, %.0f mm up" % (-SC["flat_floor"]["geometry"]["rear_most_geom"]["x"], SC["flat_floor"]["geometry"]["rear_most_geom"]["z_at"]), (-155, 122), fs=10)
    label(ax, (-235, 70), "seat block: touches,\nonly %.1f N" % seat["N"], (-112, 4), fs=10)
    label(ax, (60, 120), "soles: %.1f and %.1f N\n(nearly all the weight)" % (soles[0]["N"], soles[1]["N"]), (-20, 3), fs=10)
    label(ax, (60, 50), "belly bumper: %.1f mm\nabove the floor" % SC["flat_floor"]["geometry"]["bumper"]["lowest_z"], (23, 6), fs=10)
    ax.set_xlim(-240, 180)
    ax.set_ylim(-14, 400)
    clean(ax)
    ax.set_title("Side", fontsize=11, color=INK2, loc="left")
    a2 = fig.add_axes([0.52, 0.06, 0.46, 0.78])
    duck_top(a2, 0, 0, 0, "sit", alpha=0.28)
    for v, col in ((seat, "#8fb0cf"),):
        pass
    g = SC["flat_floor"]["geometry"]
    a2.add_patch(Rectangle((g["seat"]["within_1mm_of_lowest_x"][0], g["seat"]["within_1mm_of_lowest_y"][0]), g["seat"]["within_1mm_of_lowest_x"][1] - g["seat"]["within_1mm_of_lowest_x"][0],
                           g["seat"]["within_1mm_of_lowest_y"][1] - g["seat"]["within_1mm_of_lowest_y"][0], fc="#5f86ab", ec=INK, lw=0.8, zorder=8))
    a2.add_patch(Rectangle((g["bumper"]["within_1mm_of_lowest_x"][0], g["bumper"]["within_1mm_of_lowest_y"][0]), g["bumper"]["within_1mm_of_lowest_x"][1] - g["bumper"]["within_1mm_of_lowest_x"][0],
                           g["bumper"]["within_1mm_of_lowest_y"][1] - g["bumper"]["within_1mm_of_lowest_y"][0], fc="none", ec="#5f86ab", lw=1.6, ls=(0, (3, 2)), zorder=8))
    for s in soles:
        x, y = s["centre_of_pressure_trunk_frame_mm"]
        ye = y - np.sign(y) * 7.9
        a2.plot([x - 42, x + 42], [ye, ye], color="#b45f1c", lw=4, solid_capstyle="round", zorder=8)
    label(a2, (-215, 150), "seat block patch\n(touches, %.1f N)" % seat["N"], (-112, 20), fs=10)
    label(a2, (60, 165), "sole inner edges\n(%.1f and %.1f N):\neach sole rolls 8 deg\nonto this line" % (soles[0]["N"], soles[1]["N"]), (-10, 84), fs=10)
    label(a2, (75, -150), "bumper patch\n(dashed: %.1f mm up)" % g["bumper"]["lowest_z"], (26, -18), fs=10)
    a2.annotate("", xy=(BUMP_X, -55), xytext=(SEAT_X, -55), arrowprops=dict(arrowstyle="<->", color=INK2, lw=1), zorder=9)
    a2.text((SEAT_X + BUMP_X) / 2, -68, "%.0f mm" % (BUMP_X - SEAT_X), ha="center", fontsize=9.5, color=INK2, zorder=9)
    a2.set_xlim(-220, 200)
    a2.set_ylim(-190, 200)
    clean(a2)
    a2.set_title("From above (the duck faces right)", fontsize=11, color=INK2, loc="left")
    fig.text(0.02, 0.93, "T1. What actually touches the floor in the alert sit, motors relaxed (sim pass only)", fontsize=14.5, color=INK, weight="bold")
    fig.savefig(os.path.join(HERE, "T1_sit_contacts.png"), dpi=115)
    plt.close(fig)


if __name__ == "__main__":
    concept_A(); concept_B(); concept_C(); tech_A(); tech_B(); tech_C(); tech_T1()
    print("ok", TRUNK_A, PIV_A, SEATB, TRUNK_B, PIV_B)
