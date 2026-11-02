"""Draws altaay_lab/wiring/odm_v2_wiring_pictorial.svg and .png from netlist.yaml (A2 landscape).

Pictorial wiring diagram: every part drawn as a simple illustration with its real connectors and printed
labels, placed roughly where it sits in the robot (seen from behind: robot left on the left of the page),
and every conductor in netlist.yaml drawn terminal to terminal in its insulation colour, labelled with its
cable id (CABLE_MAP.md), gauge and cut length. The script stops with an error if a netlist wire has no
terminal on the drawing, so the drawing cannot drift from the netlist.
Own drawings only (no vendor images). Positions on the page are layout, not CAD.
"""
import os
import math
import yaml
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon, PathPatch, Ellipse
from matplotlib.path import Path

plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["font.family"] = "DejaVu Sans"

HERE = os.path.dirname(os.path.abspath(__file__))
NET = yaml.safe_load(open(os.path.join(HERE, "netlist.yaml"), encoding="utf-8"))
COMP = {c["id"]: c for c in NET["components"]}
CABLE = {c["id"]: c for c in NET["cables"]}

W, H = 594.0, 420.0                      # A2 landscape, mm
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")

ANCH = {}            # (comp, pin) -> (x, y, (dx, dy) or None)
BOXES = []           # occupied rectangles for label placement (x0, y0, x1, y1)
PCB_G, PCB_B, PCB_K = "#2e7d32", "#1565c0", "#263238"
GOLD, SILVER = "#c9a227", "#cfd8dc"
WIRE_COL = {"red": "#d32f2f", "black": "#212121", "yellow": "#f9c80e", "white": "#fafafa", "green": "#2e9e44",
            "blue": "#1e66d0", "orange": "#ef7d00", "brown": "#795548", "holder lead": "#d32f2f",
            "black jacket": "#37474f", "white ribbon": "#eceff1", "kit": "#757575", "none": "#9e9e9e"}
LIGHT = {"yellow", "white", "white ribbon"}


# ------------------------------------------------------------------ helpers
def T(x, y, s, size=6.5, color="black", ha="center", va="center", weight="normal", rot=0, z=9, bg=None):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.18,rounding_size=0.6", facecolor=bg, edgecolor="#9e9e9e", lw=0.4)
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, rotation=rot, zorder=z, **kw)


def rbox(x0, y0, w, h, fc, ec="#212121", lw=0.8, r=1.2, z=4, occupy=True):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=fc,
                                edgecolor=ec, lw=lw, zorder=z))
    if occupy:
        BOXES.append((x0, y0, x0 + w, y0 + h))


def rect(x0, y0, w, h, fc, ec="#212121", lw=0.6, z=5):
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor=fc, edgecolor=ec, lw=lw, zorder=z))


def hole(x, y, r=0.9, plated=True, used=False, z=6):
    ax.add_patch(Circle((x, y), r * 1.6, facecolor=(GOLD if plated else SILVER), edgecolor="#5d4037", lw=0.4, zorder=z))
    ax.add_patch(Circle((x, y), r * 0.75, facecolor=("#3e2723" if used else "#fafafa"), edgecolor="none", zorder=z + 0.1))


def anchor(cid, pin, x, y, d):
    if cid not in COMP:
        raise KeyError(cid)
    ANCH[(cid, pin)] = (x, y, d)


UP, DN, LF, RT = (0, 1), (0, -1), (-1, 0), (1, 0)


def region(x0, y0, x1, y1, name, sub, fc):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", facecolor=fc,
                                edgecolor="#90a4ae", lw=0.9, ls=(0, (5, 2)), zorder=1))
    T(x0 + 2.5, y1 - 3.2, name, 8.5, "#37474f", ha="left", weight="bold", z=2)
    if sub:
        T(x0 + 2.5, y1 - 7.0, sub, 6.0, "#546e7a", ha="left", z=2)


def title(x, y, s, sub=None, size=7.2, ha="center"):
    T(x, y, s, size, "black", ha=ha, weight="bold")
    if sub:
        T(x, y - 3.3, sub, 5.8, "#37474f", ha=ha)


# ------------------------------------------------------------------ parts
def holder(x0, y0):
    """2S spring holder, top view: cells side by side, series strap at the top, leads at the bottom."""
    w, h = 46.0, 86.0
    rbox(x0, y0, w, h, "#212121", lw=1.0, r=2.5)
    for k, (lbl, up) in enumerate((("cell 1", "+"), ("cell 2", "-"))):
        cx = x0 + 12.5 + k * 21.0
        rbox(cx - 9, y0 + 6, 18, h - 12, "#7e57c2", ec="#4527a0", lw=0.7, r=3, z=5, occupy=False)
        rect(cx - 9, y0 + h - 14, 18, 5, "#b39ddb", ec="none", z=5.2)
        T(cx, y0 + h / 2 + 6, "Molicel", 5.6, "white", rot=90)
        T(cx + 4.5, y0 + h / 2 + 6, "P30B", 6.2, "white", weight="bold", rot=90)
        T(cx, y0 + h - 9.0, up, 8, "white", weight="bold")
        T(cx, y0 + 9.5, "-" if up == "+" else "+", 8, "white", weight="bold")
    rect(x0 + 8, y0 + h - 4.2, 30, 2.6, SILVER, ec="#607d8b", z=6)          # series strap
    T(x0 + w / 2, y0 + h + 3.2, "series strap = MID", 5.8, "#37474f")
    anchor("PACK", "MID", x0 + w / 2, y0 + h - 2.9, UP)
    anchor("PACK", "B-", x0 + 12.5, y0, DN)
    anchor("PACK", "B+", x0 + 33.5, y0, DN)
    title(x0 + w / 2, y0 - 6.0, "BT1 2S holder B09WCT8672", "2x Molicel INR18650-P30B")


def bms(x0, y0, s=2.5):
    """Tenergy 32175 standing (16 x 34 mm board, rotated 90 deg from the product image)."""
    w, h = 16 * s, 34 * s
    rbox(x0, y0, w, h, "#1565c0", ec="#0d47a1", lw=1.0, r=1.5)
    pads = {"B-": (8.1, 1.7, 9, 2.6, DN), "B+": (8.0, 32.3, 9, 2.6, UP), "P+": (1.6, 31.0, 2.6, 4.8, LF),
            "T": (1.6, 22.1, 2.6, 4.2, LF), "B1": (14.4, 17.1, 2.6, 4.2, RT), "P-": (14.4, 25.2, 2.6, 5.2, RT)}
    for nm, (px, py, pw, ph, d) in pads.items():
        rect(x0 + (px - pw / 2) * s, y0 + (py - ph / 2) * s, pw * s, ph * s, SILVER, ec="#78909c", z=6)
        lx = x0 + px * s + {LF: 5.8, RT: -5.8, UP: 0, DN: 0}[d]
        ly = y0 + py * s + {UP: -6.0, DN: 6.0, LF: 0, RT: 0}[d]
        T(lx, ly, nm, 6.8, "white", weight="bold")
        ex = x0 + px * s + d[0] * (pw / 2) * s
        ey = y0 + py * s + d[1] * (ph / 2) * s
        anchor("BMS", nm, ex, ey, d)
    for k in range(2):                                        # R5 R6 sense resistors
        rect(x0 + (4.0 + k * 4.2) * s, y0 + 7.5 * s, 3.2 * s, 7.4 * s, "#263238", ec="#90a4ae", z=6)
    T(x0 + w / 2, y0 + 13.0 * s, "R006", 4.6, "white", rot=90)
    T(x0 + w / 2 - 1, y0 + 19.5 * s, "RYD-02S-032", 4.8, "white", rot=90)
    title(x0 + w / 2, y0 - 6.0, "U5 BMS Tenergy 32175", "10 A work, OC 22 +/- 5 A")


def charger(x0, y0, s=1.8):
    w, h = 38.2 * s, 18.1 * s
    rbox(x0, y0, w, h, "#00695c", ec="#004d40", lw=0.9, r=1.5)
    rect(x0 + w - 2.5, y0 + h / 2 - 5, 7.5, 10, "#b0bec5", ec="#455a64", z=6)
    T(x0 + w + 2.0, y0 + h / 2 + 7.2, "USB-C in", 5.6, ha="center")
    for nm, py in (("B+", 0.70), ("B-", 0.32)):
        rect(x0 + 1.0, y0 + h * py - 2.6, 6.5, 5.2, SILVER, ec="#78909c", z=6)
        T(x0 + 11.5, y0 + h * py, nm, 6.6, "white", weight="bold")
        anchor("CHG", nm, x0 + 1.0, y0 + h * py, LF)
    T(x0 + w / 2 + 6, y0 + h / 2, "pad labels [I]", 5.4, "#e0f2f1")
    title(x0 + w / 2, y0 + h + 6.6, "U6 USB-C 2S charger", "Adeept B0BJTW4QBR, on P+ / P-")


def xt30(x0, y0):
    """Amass XT30U, female (pack side) mated with male (robot side), solder cups out both ends."""
    for k, lab in enumerate(("F pack", "M robot")):
        bx = x0 + k * 17.0
        rbox(bx, y0, 17.0, 16.0, "#fbc02d", ec="#8d6e00", lw=0.8, r=2.0, z=5)
        T(bx + 8.5, y0 - 2.8, lab, 5.6, "#5d4037")
    for nm, yy in (("+", y0 + 11.5), ("-", y0 + 4.5)):
        T(x0 + 17.0, yy, nm, 9, "#5d4037", weight="bold")
        for side, cx in (("F", x0 - 1.5), ("M", x0 + 35.5)):
            rect(cx - 1.5, yy - 1.6, 3.0, 3.2, GOLD, ec="#5d4037", z=6)
            anchor("XT30", f"{side}{nm}", cx + (-1.5 if side == "F" else 1.5), yy, LF if side == "F" else RT)
    title(x0 + 17.0, y0 + 22.5, "J1 XT30U disconnect", "Amass, 2 pins, mated")


def fuse_holder(x0, y0):
    """Littelfuse FHAC0001ZXJ inline ATO holder, vertical, leads out of both ends."""
    w, h = 21.0, 60.0
    rbox(x0, y0, w, h, "#212121", lw=0.9, r=3.0)
    rbox(x0 + 4, y0 + 22, 13, 16, "#1e88e5", ec="#0d47a1", lw=0.6, r=1.0, z=6, occupy=False)
    T(x0 + w / 2, y0 + 30, "15", 8, "white", weight="bold")
    T(x0 + w / 2, y0 + 47, "ATO", 5.8, "#eceff1")
    anchor("F1", "IN", x0 + w / 2, y0 + h, UP)
    anchor("F1", "OUT", x0 + w / 2, y0, DN)
    T(x0 + w + 1.8, y0 + h - 4, "lead 1", 5.4, ha="left")
    T(x0 + w + 1.8, y0 + 4, "lead 2", 5.4, ha="left")
    title(x0 + w / 2 - 6, y0 - 6.0, "F1 15 A ATO fuse", "0287015.PXCN in FHAC0001ZXJ")


def pololu2815(x0, y0, s=2.3):
    """Pololu 2815 seen from the label side (bottom), as in the Pololu photo."""
    w, h = 20.3 * s, 22.9 * s
    rbox(x0, y0, w, h, PCB_G, ec="#1b5e20", lw=1.0, r=1.5)
    top = y0 + h - 3.0 * s
    for k, nm in enumerate(("VOUT", "GND", "GND", "VIN")):
        xx = x0 + (2.9 + k * 4.85) * s
        hole(xx, top, 1.6, used=nm in ("VOUT", "VIN") or k == 1)
        T(xx, top - 4.6, nm, 5.6, "white", weight="bold")
        if nm == "VOUT":
            anchor("SW1", "VOUT", xx, top + 1.6 * 1.6, UP)
        elif nm == "VIN":
            anchor("SW1", "VIN", xx, top + 1.6 * 1.6, UP)
        elif k == 1:
            anchor("SW1", "GND", xx, top + 1.6 * 1.6, UP)
    left = ["VOUT", "VOUT", "GND", "GND", "GND", "SW"]
    right = ["VIN", "VIN", "GND", "GND", "ON", "GND"]
    for i, (ln, rn) in enumerate(zip(left, right)):
        yy = y0 + h - (8.0 + i * 2.54) * s
        hole(x0 + 1.4 * s, yy, 0.8, used=i in (4, 5))
        hole(x0 + w - 1.4 * s, yy, 0.8)
        if i < 4:
            T(x0 + 3.2 * s, yy, ln, 4.8, "white", ha="left")
        T(x0 + w - 3.2 * s, yy, rn, 4.8, "white", ha="right")
    ys = y0 + h - (8.0 + 4.5 * 2.54) * s                    # switch symbol between the SW pad pair
    ax.plot([x0 + 3.0 * s, x0 + 5.2 * s], [ys - 1.2, ys + 1.6], color="white", lw=0.8, zorder=7)
    T(x0 + 6.0 * s, ys, "switch", 4.6, "white", ha="left")
    anchor("SW1", "GND_SW", x0, y0 + h - (8.0 + 4 * 2.54) * s, LF)
    anchor("SW1", "SW", x0, y0 + h - (8.0 + 5 * 2.54) * s, LF)
    rect(x0 + w / 2 - 6, y0 - 2.0, 12, 4.2, "#cfd8dc", ec="#455a64", z=6)
    rect(x0 + w / 2 + 1.5, y0 - 3.2, 3.2, 2.4, "#212121", ec="none", z=6.2)
    T(x0 + w / 2 - 4.0, y0 + 4.2, "On", 5.0, "white")
    T(x0 + w / 2 + 4.0, y0 + 4.2, "Off", 5.0, "white", weight="bold")
    T(x0 + w / 2, y0 - 6.2, "on-board slide set OFF", 5.6, "#b71c1c", weight="bold")
    T(x0 + w - 1.4 * s - 2.0, y0 + h - (8.0 + 4 * 2.54) * s - 2.6, "ON: open", 4.6, "#ffeb3b", ha="right")
    title(x0 + w / 2, y0 + h + 7.6, "SW1 Pololu 2815 MOSFET switch HP", "label side; 16 A cont, 6 A at 55 C")


def panel_switch(x0, y0):
    rbox(x0, y0, 40, 13, "#424242", lw=0.9, r=1.5)
    rect(x0 + 12, y0 + 4, 16, 5, "#212121", ec="#9e9e9e", z=6)
    rect(x0 + 21, y0 + 4.6, 5, 3.8, "#eeeeee", ec="none", z=6.2)
    for nm, xx in (("1", x0 + 13), ("2", x0 + 27)):
        rect(xx - 1.2, y0 - 3.6, 2.4, 3.6, GOLD, ec="#5d4037", z=6)
        T(xx + 3.0, y0 - 2.0, nm, 6, ha="left", weight="bold")
        anchor("CTL", nm, xx, y0 - 3.6, DN)
    title(x0 + 20, y0 + 19.5, "S1 stock panel switch (body_back cutout)", "switches only the 2815 SW pad, under 0.1 mA")


def bec(x0, y0):
    w, h = 56.0, 40.0
    rbox(x0, y0, w, h, "#212121", lw=1.0, r=2.5)
    T(x0 + w / 2, y0 + h - 7, "CASTLE", 8, "#ef6c00", weight="bold")
    T(x0 + w / 2, y0 + h - 13.5, "CC BEC Pro", 7.2, "white", weight="bold")
    T(x0 + w / 2, y0 + h - 19.5, "set to 7.2 V", 6.6, "#ffcc80", weight="bold")
    T(x0 + w / 2, y0 + 9.5, "010-0004-01", 5.6, "#bdbdbd")
    rect(x0 + w / 2 - 4, y0 + h - 1, 8, 3.2, "#616161", ec="#bdbdbd", z=6)
    T(x0 + w / 2 + 5.5, y0 + h + 0.6, "Link Port", 5.0, ha="left")
    for nm, yy, col in (("IN+", y0 + 27, WIRE_COL["red"]), ("IN-", y0 + 13, WIRE_COL["black"])):
        ax.plot([x0, x0 - 7], [yy, yy], color=col, lw=3.0, zorder=5, solid_capstyle="butt")
        T(x0 - 8.5, yy + 2.6, nm, 5.6, ha="right")
        anchor("U1", nm, x0 - 7, yy, LF)
    for k, base in enumerate((y0 + 31, y0 + 13)):            # two 3-pin output leads, cut and stripped
        for j, (col, pn) in enumerate(((WIRE_COL["red"], f"OUT{k + 1}+"), (WIRE_COL["black"], f"OUT{k + 1}-"),
                                       (WIRE_COL["white"], None))):
            yy = base - j * 2.6
            ax.plot([x0 + w, x0 + w + 9], [yy, yy], color="#757575" if pn is None else col, lw=1.6, zorder=5)
            if pn:
                anchor("U1", pn, x0 + w + 9, yy, RT)
            else:
                rect(x0 + w + 9, yy - 1.0, 3.0, 2.0, "#424242", ec="none", z=6)
        T(x0 + w + 4.5, base + 3.6, f"lead {k + 1}", 5.0)
    T(x0 + w + 15, y0 + 2.6, "3rd wires insulated [I]", 5.0, ha="left")
    title(x0 + w / 2, y0 - 6.0, "U1 Castle CC BEC Pro", "15 A cont (5 mph air), 20 A peak")


def splice(cid, x, y, label=None, color="#455a64"):
    rbox(x - 4.2, y - 2.0, 8.4, 4.0, "#37474f", ec="#90a4ae", lw=0.6, r=1.8, z=7, occupy=False)
    T(x, y, label or COMP[cid]["ref"], 4.8, "white", weight="bold", z=8)
    for p in COMP[cid]["pins"]:
        anchor(cid, p["pin"], x, y, None)


def adapter(x0, y0, s=1.55):
    """Waveshare Bus Servo Adapter (A), top view as in the Waveshare photo (black PCB)."""
    w, h = 42.0 * s, 33.0 * s
    rbox(x0, y0, w, h, PCB_K, ec="#000000", lw=1.0, r=2.5)
    for k, (nm, sx) in enumerate((("H3", x0 + 6 * s), ("H5", x0 + 17 * s))):
        rect(sx, y0 + h - 5.2 * s, 8.5 * s, 5.0 * s, "#f5f5f5", ec="#9e9e9e", z=6)
        for j, pn in enumerate(("D", "V", "G")):
            px = sx + (1.6 + j * 2.6) * s
            ax.add_patch(Circle((px, y0 + h - 1.2 * s), 0.8, color="#9e9e9e", zorder=7))
            T(px, y0 + h - 7.6 * s, pn, 6.0, "white", weight="bold")
            if COMP["U2"]["pins"] and any(p["pin"] == f"{nm}.{pn}" and p["dir"] != "nc" for p in COMP["U2"]["pins"]):
                anchor("U2", f"{nm}.{pn}", px, y0 + h, UP)
            elif pn == "V":
                T(px, y0 + h + 2.4, "empty", 4.6, "#b71c1c")
        T(sx + 4.25 * s, y0 + h - 10.0 * s, f"{nm} [I]", 5.2, "#b0bec5")
    for j, pn in enumerate(("TX", "RX", "GND")):
        hole(x0 + (32 + j * 2.54) * s, y0 + h - 2.0 * s, 0.7)
        T(x0 + (32 + j * 2.54) * s, y0 + h - 4.6 * s, pn, 4.4, "white")
    rect(x0 + 31 * s, y0 + 14 * s, 6 * s, 5 * s, "#fdd835", ec="#5d4037", z=6)
    T(x0 + 29.6 * s, y0 + 18 * s, "A", 5.6, "white", weight="bold")
    T(x0 + 38.6 * s, y0 + 18 * s, "B", 5.6, "#fdd835", weight="bold")
    T(x0 + 34 * s, y0 + 12.0 * s, "jumper on B", 5.0, "#fdd835")
    T(x0 + 34 * s, y0 + 9.9 * s, "(USB ~ SERVO)", 4.6, "white")
    rect(x0 + 1 * s, y0 - 1.5, 9 * s, 7 * s, "#111111", ec="#616161", z=6)
    T(x0 + 5.5 * s, y0 + 8.6 * s, "DC 9~12.6V", 4.4, "white")
    T(x0 + 5.5 * s, y0 + 2.0 * s, "not used", 4.4, "#ef9a9a")
    rect(x0 + 13 * s, y0 - 1.0, 8 * s, 5.5 * s, "#43a047", ec="#1b5e20", z=6)
    for j, pn in enumerate(("DC+", "DC-")):
        ax.add_patch(Circle((x0 + (15 + j * 4) * s, y0 + 2.0 * s), 1.6, facecolor="#cfd8dc", edgecolor="#455a64", zorder=7))
        T(x0 + (15 + j * 4) * s, y0 + 7.3 * s, pn, 5.0, "white", weight="bold")
    T(x0 + 17 * s, y0 - 4.8, "H1: NOT connected (D15)", 5.2, "#b71c1c", weight="bold")
    rect(x0 + 27 * s, y0 - 1.2, 7.5 * s, 3.4 * s, "#b0bec5", ec="#455a64", z=6)
    T(x0 + 30.75 * s, y0 + 4.6 * s, "USB", 5.2, "white", weight="bold")
    anchor("U2", "USB", x0 + 30.75 * s, y0 - 1.2, DN)
    T(x0 + 6.5 * s, y0 + h / 2 + 1, "Bus Servo Adapter (A)", 5.4, "white", rot=90)
    title(x0 + w / 2 + 6, y0 + h + 9.0, "U2 Waveshare Bus Servo Adapter (A)", "data only: logic from USB, no servo power through it")


def pi_zero(x0, y0, s=2.0):
    """Raspberry Pi Zero 2 W, component side, standard orientation: header on the top edge, pin 1 at the left."""
    w, h = 65.0 * s, 30.0 * s
    rbox(x0, y0, w, h, PCB_G, ec="#1b5e20", lw=1.1, r=3.0)
    for hx, hy in ((3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)):
        ax.add_patch(Circle((x0 + hx * s, y0 + hy * s), 2.2, facecolor="#fafafa", edgecolor=GOLD, lw=1.2, zorder=6))
    rect(x0 + 29 * s, y0 + 8 * s, 12 * s, 12 * s, "#212121", ec="#616161", z=6)
    T(x0 + 35 * s, y0 + 14 * s, "RP3A0", 5.6, "#bdbdbd")
    T(x0 + 14 * s, y0 + 15 * s, "Raspberry Pi", 6.8, "white", weight="bold")
    T(x0 + 14 * s, y0 + 11.5 * s, "Zero 2 W", 6.8, "white", weight="bold")
    used = {int(p["pin"]) for p in COMP["PI"]["pins"] if p["pin"].isdigit()}
    for k in range(20):
        px = x0 + (4.87 + k * 2.54) * s
        for pn, py in ((2 * k + 1, y0 + h - 4.77 * s), (2 * k + 2, y0 + h - 2.23 * s)):
            if pn == 1:
                rect(px - 1.6, py - 1.6, 3.2, 3.2, GOLD, ec="#5d4037", z=6)
                ax.add_patch(Circle((px, py), 0.9, facecolor="#3e2723", zorder=6.2))
            else:
                hole(px, py, 1.0, used=pn in used)
            if pn in used:
                anchor("PI", str(pn), px, py, UP)
            if pn % 2:
                T(px, py - 3.2, str(pn), 4.9, "white" if pn in used else "#a5d6a7", weight="bold" if pn in used else "normal")
            elif pn in used:
                T(px + 1.9, py + 2.6, str(pn), 4.6, "#0d47a1", weight="bold", ha="left")
    T(x0 + 4.87 * s - 2.2, y0 + h - 4.77 * s - 6.6, "pin 1", 5.0, "#ffeb3b", ha="left", weight="bold")
    # D17: R4 (pin 17 to 15) and R5 (pin 17 to 13), 2.2 kOhm, soldered straight onto the header pins
    yi = y0 + h - 4.77 * s
    px = lambda n: x0 + (4.87 + (n - 1) // 2 * 2.54) * s
    for rid, other, hgt in (("RFL", 15, 9.0), ("RFR", 13, 15.0)):
        xa, xb = px(17), px(other)
        ax.plot([xa, xa, xb, xb], [yi, yi + hgt, yi + hgt, yi], color="#9e9e9e", lw=0.8, zorder=11)
        xm = (xa + xb) / 2
        rbox(xm - 3.0, yi + hgt - 1.3, 6.0, 2.6, "#e6c9a0", ec="#8d6e63", lw=0.5, r=1.0, z=11.5, occupy=False)
        for k, c in enumerate(("#d32f2f", "#d32f2f", "#d32f2f", "#c9a227")):
            rect(xm - 2.2 + k * 1.3, yi + hgt - 1.3, 0.55, 2.6, c, ec="none", z=11.6)
        T(xm - 4.0, yi + hgt, COMP[rid]["ref"] + " 2.2k", 5.2, "#00695c", ha="right", weight="bold", z=12, bg="white")
        anchor(rid, "1", xa, yi, UP)
        anchor(rid, "2", xb, yi, UP)
    for nm, px, lab in (("HDMI", 12.4, "mini HDMI"), ("USB", 41.4, "USB"), ("PWR", 54.0, "PWR IN")):
        rect(x0 + px * s - 6, y0 - 3.0, 12, 4.4, "#b0bec5", ec="#455a64", z=6)
        T(x0 + px * s, y0 + 4.2, lab, 5.2, "white", weight="bold")
    anchor("PI", "USB", x0 + 41.4 * s, y0 - 3.0, DN)
    T(x0 + 54.0 * s, y0 - 6.0, "leave empty [I]", 5.0, "#b71c1c")
    rect(x0 + w - 2.0, y0 + 9 * s, 3.0, 12 * s, "#eeeeee", ec="#455a64", z=6)
    T(x0 + w - 4.2, y0 + 15 * s, "CSI", 5.4, "white", weight="bold", rot=90)
    anchor("PI", "CSI", x0 + w + 1.0, y0 + 15 * s, RT)
    T(x0 + 3.2, y0 + h / 2, "SD", 5.0, "#c8e6c9", rot=90)
    T(x0 + w / 2, y0 + h / 2 - 9.5, "U4: 40-pin header 2.54 mm; odd pins inner row; blue numbers = even pins", 5.2, "#e8f5e9")


def d30v30(x0, y0, s=1.5):
    w, h = 17.8 * s, 20.3 * s
    rbox(x0, y0, w, h, PCB_G, ec="#1b5e20", lw=1.0, r=1.2)
    rect(x0 + 4 * s, y0 + 9 * s, 8 * s, 6 * s, "#424242", ec="#9e9e9e", z=6)
    order = ["EN", "VIN", "GND.1", "GND.2", "VOUT"]
    for k, pn in enumerate(order):
        px = x0 + (2.7 + k * 2.54) * s
        hole(px, y0 + h - 1.8 * s, 0.75, used=pn != "EN")
        T(px, y0 + h - 6.4 * s, pn.split(".")[0], 4.4, "white", weight="bold", rot=90)
        if pn != "EN":
            anchor("U3", pn, px, y0 + h - 1.8 * s + 1.2, UP)
    T(x0 + w / 2, y0 + 3.0, "D30V30F5", 5.0, "white", weight="bold")
    T(x0 + w / 2, y0 - 3.2, "EN, PG open; pin order [I]", 4.8, "#33691e")
    title(x0 + w / 2, y0 - 9.0, "U3 Pololu D30V30F5", "5 V, 3.8 A at 6 to 8.4 V in")


def bno055(x0, y0, s=1.5):
    w, h = 20.0 * s, 27.0 * s
    rbox(x0, y0, w, h, "#1a237e", ec="#000051", lw=0.9, r=1.5)
    rect(x0 + 6 * s, y0 + 8 * s, 8 * s, 8 * s, "#212121", ec="#9e9e9e", z=6)
    T(x0 + w / 2, y0 + 4.0 * s, "BNO055", 6.0, "white", weight="bold")
    names = ["VIN", "3VO", "GND", "SDA", "SCL", "RST"]
    for k, pn in enumerate(names):
        px = x0 + (2.6 + k * 2.95) * s
        nc_pin = pn in ("3VO", "RST")
        hole(px, y0 + h - 1.8 * s, 0.75, used=not nc_pin)
        T(px, y0 + h - 5.4 * s, pn, 4.6, "white", rot=90)
        if not nc_pin:
            anchor("BNO", pn, px, y0 + h - 1.8 * s + 1.2, UP)
    title(x0 + w / 2, y0 - 6.0, "U7 BNO055, Adafruit 2472", "header order [I]")


def ss10(cid, x0, y0, label):
    w, h = 26.0, 9.0
    rbox(x0, y0, w, h, "#212121", lw=0.8, r=1.0)
    ax.plot([x0 + 3, x0 + w + 2], [y0 + h, y0 + h + 4], color="#9e9e9e", lw=1.4, zorder=5)
    for k, pn in enumerate(("COM", "NO", "NC")):
        px = x0 + 4 + k * 9
        rect(px - 1.2, y0 - 4.0, 2.4, 4.0, SILVER, ec="#607d8b", z=6)
        T(px, y0 + h / 2, pn, 4.8, "white", weight="bold")
        if pn != "NC":
            anchor(cid, pn, px, y0 - 4.0, DN)
    T(x0 + w + 2.5, y0 + h / 2, label, 5.4, ha="left")


def resistor(cid, x, y, vertical=False):
    if vertical:
        ax.plot([x, x], [y - 7, y + 7], color="#9e9e9e", lw=0.9, zorder=5)
        rbox(x - 1.6, y - 3.8, 3.2, 7.6, "#e6c9a0", ec="#8d6e63", lw=0.5, r=1.2, z=6, occupy=False)
        for k, c in enumerate(("#6d4c41", "#212121", "#6d4c41", "#c9a227")):
            rect(x - 1.6, y + 2.4 - k * 1.6, 3.2, 0.7, c, ec="none", z=6.5)
        anchor(cid, "1", x, y + 7, UP)
        anchor(cid, "2", x, y - 7, DN)
    else:
        ax.plot([x - 7, x + 7], [y, y], color="#9e9e9e", lw=0.9, zorder=5)
        rbox(x - 3.8, y - 1.6, 7.6, 3.2, "#e6c9a0", ec="#8d6e63", lw=0.5, r=1.2, z=6, occupy=False)
        for k, c in enumerate(("#6d4c41", "#212121", "#6d4c41", "#c9a227")):
            rect(x - 2.6 + k * 1.6, y - 1.6, 0.7, 3.2, c, ec="none", z=6.5)
        anchor(cid, "1", x - 7, y, LF)
        anchor(cid, "2", x + 7, y, RT)


def led(cid, x, y):
    ax.add_patch(Ellipse((x, y), 6.0, 4.4, facecolor="#fff59d", edgecolor="#f9a825", lw=0.7, zorder=6))
    ax.plot([x - 3, x - 6], [y, y], color="#9e9e9e", lw=0.9, zorder=5)
    ax.plot([x + 3, x + 6], [y, y], color="#9e9e9e", lw=0.9, zorder=5)
    T(x - 4.5, y + 2.6, "+", 6, weight="bold")
    T(x + 4.5, y + 2.6, "-", 6, weight="bold")
    anchor(cid, "A", x - 6, y, LF)
    anchor(cid, "K", x + 6, y, RT)


def led_set(rid, lid, x, y, name):
    """Resistor soldered straight to the LED anode (cut 0), then the LED."""
    resistor(rid, x, y)
    led(lid, x + 13, y)
    T(x + 5, y + 5.8, name, 5.6, weight="bold")
    T(x + 5, y - 4.4, "100 ohm + 1 W LED", 4.8, "#5d4037")


def sg90(cid, x0, y0, flip=False):
    w, h = 23.0, 12.5
    rbox(x0, y0, w, h, "#1e88e5", ec="#0d47a1", lw=0.8, r=1.0)
    ax.add_patch(Circle((x0 + (w - 6 if not flip else 6), y0 + h / 2), 3.2, facecolor="white", edgecolor="#0d47a1", lw=0.6, zorder=6))
    T(x0 + (8 if not flip else w - 8), y0 + h / 2, "SG90", 5.8, "white", weight="bold")
    side = x0 if not flip else x0 + w
    d = LF if not flip else RT
    for k, pn in enumerate(("SIG", "VCC", "GND")):
        anchor(cid, pn, side, y0 + h / 2 + 2.2 - k * 2.2, d)


def amp(x0, y0):
    w, h = 32.0, 26.0
    rbox(x0, y0, w, h, "#1a237e", ec="#000051", lw=0.9, r=1.5)
    T(x0 + w / 2 - 2, y0 + h - 4.0, "MAX98357A", 5.4, "white", weight="bold")
    names = ["LRC", "BCLK", "DIN", "GAIN", "SD", "GND", "VIN"]
    for k, pn in enumerate(names):
        px = x0 + 3.0 + k * 4.0
        hole(px, y0 + 2.2, 0.7, used=pn not in ("GAIN", "SD"))
        T(px, y0 + 8.6, "Vin" if pn == "VIN" else pn, 4.4, "white", rot=90)
        if pn not in ("GAIN", "SD"):
            anchor("AMP", pn, px, y0 + 1.0, DN)
    rect(x0 + w - 1.5, y0 + 9, 6, 12, "#2e7d32", ec="#1b5e20", z=6)
    for k, pn in enumerate(("SPK+", "SPK-")):
        py = y0 + 18 - k * 6
        ax.add_patch(Circle((x0 + w + 1.5, py), 1.3, facecolor="#cfd8dc", edgecolor="#455a64", zorder=7))
        T(x0 + w - 4.0, py, "+" if k == 0 else "-", 6.4, "white", weight="bold")
        anchor("AMP", pn, x0 + w + 4.5, py, RT)
    title(x0 + w / 2, y0 + h + 6.4, "U8 MAX98357A", "Adafruit 3006")


def speaker(x0, y0, s=0.85):
    a = 36.1 * s
    rbox(x0, y0, a, a, "#424242", lw=0.9, r=2.0)
    ax.add_patch(Circle((x0 + a / 2, y0 + a / 2), 11.5, facecolor="#757575", edgecolor="#212121", lw=0.8, zorder=6))
    ax.add_patch(Circle((x0 + a / 2, y0 + a / 2), 4.2, facecolor="#9e9e9e", edgecolor="#212121", lw=0.6, zorder=6.2))
    for k, pn in enumerate(("+", "-")):
        py = y0 + a / 2 + 4.5 - k * 9
        rect(x0 + a / 2 - 1.4 + (k - 0.5) * 8, y0 - 3.6, 2.8, 3.6, SILVER, ec="#607d8b", z=6)
        T(x0 + a / 2 + (k - 0.5) * 8, y0 + 3.0, pn, 7, "white", weight="bold")
        anchor("SPK", pn, x0 + a / 2 + (k - 0.5) * 8, y0 - 3.6, DN)
    T(x0 - 5.0, y0 + a - 3.0, "LS1 Same Sky", 5.8, ha="right", weight="bold")
    T(x0 - 5.0, y0 + a - 6.4, "CMS0361KLX 8 ohm 2 W", 5.2, "#37474f", ha="right")


def camera(x0, y0):
    w, h = 28.0, 27.0
    rbox(x0, y0, w, h, PCB_G, ec="#1b5e20", lw=0.9, r=1.5)
    ax.add_patch(Circle((x0 + w / 2 + 2, y0 + h / 2), 5.6, facecolor="#212121", edgecolor="#9e9e9e", lw=0.8, zorder=6))
    rect(x0 - 2, y0 + 8, 3, 11, "#eeeeee", ec="#455a64", z=6)
    anchor("CAM", "CSI", x0 - 2.0, y0 + 13.5, LF)
    title(x0 + w / 2, y0 + h + 6.2, "U9 Camera Module 3", "Adafruit 5657")


def sts3215(cid, x0, y0, name, side="R", free=None):
    """STS3215 C001 with BUS 1 and BUS 2 side by side on one face."""
    w, h = 40.0, 17.0
    rbox(x0, y0, w, h, "#212121", lw=0.9, r=2.0)
    sid = cid[2:]
    T(x0 + (16 if side == "R" else w - 16), y0 + h - 5.2, f"ID {sid}", 7.4, "white", weight="bold")
    T(x0 + (16 if side == "R" else w - 16), y0 + 4.6, name, 5.4, "#e0e0e0")
    ex = x0 + w if side == "R" else x0
    d = RT if side == "R" else LF
    for port, py in (("BUS2", y0 + h - 4.6), ("BUS1", y0 + 4.6)):
        rect(ex - (6.5 if side == "R" else 0), py - 3.4, 6.5, 6.8, "#f5f5f5", ec="#9e9e9e", z=6)
        T(ex + (-9.2 if side == "R" else 9.2), py, port[:3] + " " + port[3], 4.6, "#ffeb3b", weight="bold")
        for j, pn in enumerate(("D", "V", "G")):
            pin_dir = next(p["dir"] for p in COMP[cid]["pins"] if p["pin"] == f"{port}.{pn}")
            if pin_dir != "nc":
                anchor(cid, f"{port}.{pn}", ex, py + 2.0 - j * 2.0, d)
        if free == port:
            T(ex + d[0] * 6.0, py, "free", 5.0, "#9e9e9e", ha="left" if side == "R" else "right")


# ------------------------------------------------------------------ layout (page positions in mm)
region(8, 140, 232, 338, "BATTERY BAY (body_back)", "rear of the trunk, seen from behind", "#fff8e1")
region(238, 146, 586, 200, "BELLY (body_middle_bottom floor)", "servo regulator and power splices", "#fbe9e7")
region(238, 204, 586, 270, "TRUNK_TOP", "adapter, IMU, neck pitch servo", "#e8f5e9")
region(362, 272, 524, 300, "NECK", None, "#f3e5f5")
region(238, 302, 586, 400, "HEAD (head floor)", "Pi hangs from the head top wall, components down", "#e3f2fd")
region(238, 112, 586, 142, "TRUNK_BOTTOM", "hip yaw servos", "#ede7f6")
region(238, 8, 410, 108, "LEFT LEG", None, "#eceff1")
region(414, 8, 586, 108, "RIGHT LEG", None, "#eceff1")

# battery bay
panel_switch(18, 297)
pololu2815(14, 222)
splice("VSW", 84, 207)
splice("G", 84, 193)
holder(98, 220)
bms(160, 202)
charger(150, 300)
fuse_holder(208, 196)
xt30(150, 166)
# belly
bec(258, 153)
splice("JBP", 338, 186, "JB+")
splice("JBN", 338, 168, "JB-")
splice("SPV", 362, 186)
splice("SPG", 362, 168)
# trunk_top
adapter(412, 208)
sts3215("SV30", 300, 230, "neck_pitch", "R")
splice("YD3", 392, 236)
splice("YG3", 392, 224)
splice("JG30", 354, 222)
bno055(546, 210)
# neck
sts3215("SV31", 404, 277, "head_pitch", "R")
sts3215("SV32", 476, 277, "head_yaw", "L")
# head
pi_zero(372, 305, s=1.8)
d30v30(328, 322)
splice("J5", 392, 377)
splice("JG", 406, 377)
amp(466, 366)
speaker(552, 360)
camera(520, 326)
sg90("SGL", 250, 352, flip=True)
sg90("SGR", 556, 334, flip=False)
led_set("RL", "LEDL", 290, 390, "L eye (D5)")
led_set("RP", "LEDP", 424, 391, "projector (D7)")
led_set("RR", "LEDR", 290, 372, "R eye (D6)")
sts3215("SV33", 544, 304, "head_roll", "L", free="BUS1")
# trunk_bottom
sts3215("SV20", 300, 118, "L hip_yaw", "R")
sts3215("SV10", 494, 118, "R hip_yaw", "L")
splice("JG20", 352, 120)
splice("JG10", 482, 133)
# legs
legL = [("SV21", "L hip_roll"), ("SV22", "L hip_pitch"), ("SV23", "L knee"), ("SV24", "L ankle")]
legR = [("SV11", "R hip_roll"), ("SV12", "R hip_pitch"), ("SV13", "R knee"), ("SV14", "R ankle")]
for k, (cid, nm) in enumerate(legL):
    sts3215(cid, 300, 86 - k * 21, nm, "R", free="BUS1" if cid == "SV24" else None)
for k, (cid, nm) in enumerate(legR):
    sts3215(cid, 494, 86 - k * 21, nm, "L", free="BUS1" if cid == "SV14" else None)
ss10("FSL1", 250, 30, "SL1")
ss10("FSL2", 250, 17, "SL2")
T(250, 44.0, "left foot: 2x Omron SS-01 (SS-10 fallback)", 5.6, ha="left", weight="bold")
ss10("FSR1", 550, 30, "")
ss10("FSR2", 550, 17, "")
T(584, 44.0, "right foot: 2x SS-01 (SS-10 fallback)", 5.6, ha="right", weight="bold")
T(548, 34.5, "SR1", 5.4, ha="right")
T(548, 21.5, "SR2", 5.4, ha="right")

# ------------------------------------------------------------------ wire routing
# Waypoints for cables that run between regions (page mm). Wires of one cable follow them as a bundle.
UPLEFT = [(370, 368), (364, 330), (380, 292)]       # from the header up, round the Pi's left edge, into the neck
ROUTES = {
    "P13": [(112, 160), (234, 158), (246, 232), (300, 266), (366, 282), (362, 318), (350, 364)],
    "D1": [(455, 290), (458, 262), (470, 196), (452, 176), (438, 190), (464, 206)],
    "D2": UPLEFT + [(392, 266), (470, 266), (556, 262)],
    "D3": UPLEFT + [(372, 262), (300, 214), (246, 150), (246, 104), (244, 52)],
    "D4": UPLEFT + [(392, 268), (530, 262), (580, 200), (582, 104), (584, 52)],
    "P10": [(112, 176), (234, 172)],
    "SP1": [(372, 150), (352, 132)],
    "SP2": [(430, 156), (474, 146)],
    "SP3": [(374, 196), (352, 214)],
    "SD2": [(474, 196), (478, 150)],
    "P14": [(140, 160)],
    "P15": [(12, 290)],
    "D8": [(300, 368), (378, 369)],
    "D9": [(520, 362)],
}
BUNDLE_GAP = 1.5


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n) if n > 1e-9 else (0.0, 0.0)


def offset_points(pts, d):
    """Shift a polyline sideways by d (mm), using the local direction at each point."""
    out = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = unit((b[0] - a[0], b[1] - a[1]))
        out.append((p[0] - ty * d, p[1] + tx * d))
    return out


def catmull(points):
    """Smooth path through points (Catmull-Rom as cubic Bezier)."""
    P = [points[0]] + list(points) + [points[-1]]
    verts, codes = [points[0]], [Path.MOVETO]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        c1 = p1 + (p2 - p0) / 6.0
        c2 = p2 - (p3 - p1) / 6.0
        verts += [tuple(c1), tuple(c2), tuple(p2)]
        codes += [Path.CURVE4] * 3
    return Path(verts, codes)


def lw_for(gauge):
    g = str(gauge)
    if g.startswith("16"):
        return 3.0
    if g.startswith("20"):
        return 2.2
    if g.startswith("22"):
        return 1.7
    if "USB" in g:
        return 3.2
    if "FPC" in g:
        return 4.5
    if "kit" in g:
        return 1.1
    return 1.25


def wire_path(w, k, n):
    a = ANCH.get(tuple(w["from"].split(".", 1)))
    b = ANCH.get(tuple(w["to"].split(".", 1)))
    if a is None or b is None:
        raise SystemExit(f"no terminal on the drawing for {w['from']} or {w['to']} (cable {w['cable']})")
    way = ROUTES.get(w["cable"], [])
    if w.get("branch") in ("jumper", "joint", "tail", "lead1", "lead2", "stem", "a", "b"):
        way = [] if w["cable"] not in ("D3", "D4") or w.get("branch") == "jumper" else way
    off = (k - (n - 1) / 2.0) * BUNDLE_GAP
    way = offset_points(way, off) if way else []
    first = way[0] if way else (b[0], b[1])
    last = way[-1] if way else (a[0], a[1])
    da = a[2] or unit((first[0] - a[0], first[1] - a[1]))
    db = b[2] or unit((last[0] - b[0], last[1] - b[1]))
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    st = min(8.0, max(2.5, dist * 0.18))
    pts = [(a[0], a[1]), (a[0] + da[0] * st, a[1] + da[1] * st)] + way + [(b[0] + db[0] * st, b[1] + db[1] * st), (b[0], b[1])]
    return catmull(pts), pts


def draw_wire(path, color, lw, z=3.0):
    col = WIRE_COL.get(color, "#9e9e9e")
    if color in LIGHT:
        ax.add_patch(PathPatch(path, facecolor="none", edgecolor="#616161", lw=lw + 0.9, zorder=z, capstyle="round"))
    elif color in ("black", "black jacket", "brown"):
        ax.add_patch(PathPatch(path, facecolor="none", edgecolor="#ffffff", lw=lw + 0.7, zorder=z, capstyle="round"))
    ax.add_patch(PathPatch(path, facecolor="none", edgecolor=col, lw=lw, zorder=z + 0.05, capstyle="round"))


# group conductors by cable, branch and the pair of parts they join
groups = {}
for w in NET["wires"]:
    key = (w["cable"], w.get("branch"), w["from"].split(".")[0], w["to"].split(".")[0])
    groups.setdefault(key, []).append(w)

label_requests = []
label_paths = {}
for key, ws in groups.items():
    n = len(ws)
    mids = []
    for k, w in enumerate(ws):
        if w["cut_mm"] == 0:
            continue
        path, pts = wire_path(w, k, n)
        draw_wire(path, "kit" if w["gauge"] == "kit cable" else w["color"], lw_for(w["gauge"]))
        mids.append(path)
    if mids:
        lk = (key[0], key[1])
        label_paths.setdefault(lk, []).append((ws, mids[len(mids) // 2]))
    # coil symbol for the USB slack in the belly
    if key[0] == "D1":
        for j in range(4):
            ax.add_patch(Ellipse((452, 176 + j * 1.6), 16, 7, facecolor="none", edgecolor=WIRE_COL["black jacket"], lw=2.0, zorder=3.5))
        T(452, 158.5, "D1 slack coiled in the belly", 5.4, "#37474f")


for lk, items in label_paths.items():
    allw = [w for ws_, _ in items for w in ws_]
    ws_, pth = max(items, key=lambda it: len(it[0]))
    label_requests.append((lk, allw, pth))


def label_text(ws):
    w0 = ws[0]
    cuts = sorted({w["cut_mm"] for w in ws if w["cut_mm"] is not None})
    g = w0["gauge"]
    n = len(ws)
    br = w0.get("branch")
    name = w0["cable"] + (f" {br}" if br in ("a", "b", "stem") else "")
    if g == "kit cable":
        return f"{name} kit 150"
    cut = ("" if not cuts else (f" {int(cuts[0]) if float(cuts[0]).is_integer() else cuts[0]} mm" if len(cuts) == 1
                                else " " + "/".join(str(int(c)) for c in cuts) + " mm"))
    gs = g.replace(" AWG", "AWG") if "AWG" in g else g
    return f"{name} {g}{' x' + str(n) if n > 1 else ''}{cut}"


def overlaps(bb):
    for o in BOXES + PLACED:
        if bb[0] < o[2] and bb[2] > o[0] and bb[1] < o[3] and bb[3] > o[1]:
            return True
    return False


PLACED = []
fig.canvas.draw()
rend = fig.canvas.get_renderer()
inv = ax.transData.inverted()
for tx0 in list(ax.texts):
    bb0 = tx0.get_window_extent(renderer=rend)
    (a0, b0), (a1, b1) = inv.transform([(bb0.x0, bb0.y0), (bb0.x1, bb0.y1)])
    BOXES.append((a0, b0, a1, b1))


def overlap_area(bb):
    tot = 0.0
    for o in BOXES + PLACED:
        ox = min(bb[2], o[2]) - max(bb[0], o[0])
        oy = min(bb[3], o[3]) - max(bb[1], o[1])
        if ox > 0 and oy > 0:
            tot += ox * oy
    if bb[0] < 6 or bb[1] < 6 or bb[2] > W - 6 or bb[3] > H - 6:
        tot += 1e6
    return tot


for key, ws, path in label_requests:
    s = label_text(ws)
    curve = path.interpolated(30).vertices
    tx = T(0, 0, s, 5.4, "#212121", weight="bold", z=10, bg="white")
    bb = tx.get_window_extent(renderer=rend)
    (u0, v0), (u1, v1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    lw_, lh_ = (u1 - u0) + 1.2, (v1 - v0) + 1.2
    best = None
    for tt in (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82, 0.12, 0.88):
        cx, cy = curve[int(tt * (len(curve) - 1))]
        for dx, dy in ((0, 0), (0, 3.2), (0, -3.2), (lw_ / 2 + 1, 0), (-lw_ / 2 - 1, 0), (0, 6.0), (0, -6.0)):
            box_ = (cx + dx - lw_ / 2, cy + dy - lh_ / 2, cx + dx + lw_ / 2, cy + dy + lh_ / 2)
            sc = overlap_area(box_) + 0.02 * (abs(dx) + abs(dy)) + 0.01 * abs(tt - 0.5) * 100
            if best is None or sc < best[0]:
                best = (sc, cx + dx, cy + dy, box_)
        if best[0] < 0.5:
            break
    tx.set_position((best[1], best[2]))
    PLACED.append(best[3])

# ------------------------------------------------------------------ legend, notes, title
region(8, 8, 232, 136, "LEGEND AND NOTES", None, "#fafafa")
yy = 122
for col, lab in (("red", "red: + supply"), ("black", "black: ground"), ("yellow", "yellow: servo DATA, I2C SCL, MID"),
                 ("white", "white: control, I2S LRC, R foot"), ("blue", "blue: I2C SDA"), ("green", "green: L foot, I2S DIN, projector"),
                 ("orange", "orange / brown: SG90 lead [I]"), ("kit", "grey: kit servo cable (molded, 1:1)")):
    p = Path([(14, yy), (30, yy)])
    draw_wire(p, col, 2.2, z=9)
    T(33, yy, lab, 6.0, ha="left")
    yy -= 5.2
T(14, yy - 1.0, "Line width: 16 AWG thickest, then 20, 22, 26 AWG. Colours are the lab plan [I] unless the part ships with them.", 5.6, ha="left")
notes = [
    "Seen from behind: robot left is on the left. Positions are layout, not CAD (CAD centres in MOUNTING.md).",
    "Every wire comes from wiring/netlist.yaml. Label = cable id (CABLE_MAP.md), gauge, conductors, cut length.",
    "D15: servo power bypasses the adapter: BEC -> JB+/JB- -> P11 -> SPV/SPG -> SP1 SP2 SP3 -> first servo BUS 2.",
    "Adapter H3/H5 carry DATA and GND only (V position empty). H1 screw terminal NOT connected. Jumper on B.",
    "Bench check: the adapter must enumerate and drive the bus with H1 unpowered.",
    "Grounds return to BMS P- through splice G, P14, XT30, P8. Nothing but the cell on B-.",
    "Battery: Tenergy cuts at 2.40 V per cell, below the P30B 2.5 V minimum: stop in software at",
    "servo Present Voltage about 6.0 V (about 3.3 V per cell loaded).",
    "Eyes and antennas follow the Runtime code (D9), not the assembly_guide table: they are swapped.",
    "D17: feet SS-01 (SS-10 fallback); R4, R5 2.2 kOhm pull-ups from Pi pin 17 soldered on the header.",
    "Tags: [U] upstream, [L] lab decision, [I] inferred, check on the build.",
]
for i, s in enumerate(notes):
    T(14, yy - 7.5 - i * 4.4, s, 5.8, ha="left")
T(10, 410, "Open Duck Mini v2, altaay-lab build: pictorial wiring diagram (every wire, terminal to terminal)", 14, ha="left", weight="bold")
T(10, 404, "Rev 2026-11-01. Generated from wiring/netlist.yaml by wiring/make_pictorial.py. Companion sheets: odm_v2_schematic, odm_v2_harness. "
           "Print A2 landscape (or tabloid, scaled).", 7.0, "#37474f", ha="left")

# coverage: every netlist wire must have been drawn (cut 0 = parts soldered together)
missing = [w for w in NET["wires"] if tuple(w["from"].split(".", 1)) not in ANCH or tuple(w["to"].split(".", 1)) not in ANCH]
if missing:
    raise SystemExit(f"{len(missing)} wires without terminals")

if __name__ == "__main__":
    fig.savefig(os.path.join(HERE, "odm_v2_wiring_pictorial.svg"))
    png = os.path.join(HERE, "odm_v2_wiring_pictorial.png")
    fig.savefig(png, dpi=140)
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB")
        if os.path.getsize(png) > 900_000:
            im.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(png, optimize=True)
    except ImportError:
        pass
    print("wrote odm_v2_wiring_pictorial.svg and .png", os.path.getsize(png), "bytes")
