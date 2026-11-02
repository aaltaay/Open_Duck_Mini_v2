"""Draws altaay_lab/wiring/odm_v2_schematic.svg and .png from netlist.yaml (A3 landscape, print at 100%).

Electrical schematic for the altaay-lab Open Duck Mini v2 build (wiring decisions D8 to D13 and D15, 2026-11-01).
Layout is hand placed here; every cable id, gauge, Pi header row and device terminal text is read from
netlist.yaml, and the script stops if an active netlist cable is missing from the sheet.
Tags: [U] upstream, [L] lab decision, [I] inferred (check on the build).
Pure matplotlib, drawn in millimetres on a 420 x 297 mm sheet so the font sizes are true print sizes.
"""
import os
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc
from matplotlib.lines import Line2D

plt.rcParams["svg.fonttype"] = "none"      # keep text as text in the SVG (small file, searchable)
plt.rcParams["font.family"] = "DejaVu Sans"

HERE = os.path.dirname(os.path.abspath(__file__))
NET = yaml.safe_load(open(os.path.join(HERE, "netlist.yaml"), encoding="utf-8"))
COMP = {c["id"]: c for c in NET["components"]}
PIN = {(c["id"], p["pin"]): p for c in NET["components"] for p in c["pins"]}
CABLES = {c["id"]: c for c in NET["cables"]}
WIRES = {}
for _w in NET["wires"]:
    WIRES.setdefault(_w["cable"], []).append(_w)
USED = set()

W, H = 420.0, 297.0
PACK, VSW, SERVO, V5, V33 = "#c62828", "#ad1457", "#e65100", "#6a1b9a", "#00838f"
GND, SIG, BUS, USB, NOTE, GREY = "#212121", "#1565c0", "#2e7d32", "#00695c", "#444444", "#9e9e9e"
LW16, LW20, LW22, LW26, LWBUS = 2.4, 1.6, 1.2, 0.9, 2.8

fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


# ---------------------------------------------------------------- netlist lookups
def CL(cid, more=""):
    """Cable label from the netlist: id and gauge (and conductor count when > 1)."""
    ws = WIRES[cid]
    USED.add(cid)
    g = sorted({w["gauge"] for w in ws if w["cut_mm"] != 0 and "lead" not in w["gauge"]}) or sorted({w["gauge"] for w in ws})
    return f"{cid} {g[0]}{more}"


def ends(cid_pin):
    """Other ends of every wire on COMP.PIN: list of (comp, pin, cable, branch)."""
    out = []
    for w in NET["wires"]:
        for a, b in ((w["from"], w["to"]), (w["to"], w["from"])):
            if a == cid_pin:
                c, p = b.split(".", 1)
                out.append((c, p, w["cable"], w.get("branch")))
    return out


def sig_name(n):
    nm = PIN[("PI", str(n))]["name"].split()
    return nm[0] + (" " + nm[1] if nm[1:2] in (["SDA"], ["SCL"]) else "")


def to_pi(cid_pin):
    """'Pi 15 (GPIO22)' for a device pin wired straight to the Pi header, else the splice ref."""
    for c, p, cab, _ in ends(cid_pin):
        USED.add(cab)
        if c == "PI":
            return f"Pi {p} ({sig_name(p)})"
        if COMP[c]["kind"] == "splice":
            return f"{COMP[c]['ref']} ({cab})"
    raise SystemExit(f"{cid_pin} has no wire to the Pi in netlist.yaml")


SHORT = {"BNO": "BNO055", "FSL1": "L foot", "FSR1": "R foot", "RL": "L eye", "RR": "R eye", "RP": "projector",
         "LEDL": "L eye LED", "LEDR": "R eye LED", "LEDP": "projector LED", "U3": "U3", "J5": "splice J5",
         "JG": "splice JG", "SGL": "L antenna SG90", "SGR": "R antenna SG90", "AMP": "MAX98357A",
         "RFL": "R4 2.2k pull-up", "RFR": "R5 2.2k pull-up"}


def pi_dest(n):
    parts = []
    for c, p, cab, _ in ends(f"PI.{n}"):
        USED.add(cab)
        lab = PIN[(c, p)]["label"]
        lab = {"A": "+", "K": "-"}.get(lab, lab) if COMP[c]["kind"] == "led" else lab
        lab = "" if COMP[c]["kind"] in ("splice", "resistor") else " " + lab
        parts.append(f"{SHORT.get(c, c)}{lab} ({cab})")
    return parts


# ---------------------------------------------------------------- primitives
def wire(pts, color=GND, lw=LW26, ls="-", z=2):
    ax.add_line(Line2D([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls,
                       solid_capstyle="butt", solid_joinstyle="miter", zorder=z))


def vhop(x, y0, y1, ycross, color, lw):
    """Vertical wire from y0 to y1 that hops (no connection) over a horizontal wire at ycross."""
    r = 1.3
    lo, hi = sorted((y0, y1))
    wire([(x, lo), (x, ycross - r)], color, lw)
    wire([(x, ycross + r), (x, hi)], color, lw)
    ax.add_patch(Arc((x, ycross), 2 * r, 2 * r, theta1=-90, theta2=90, color=color, lw=lw, zorder=2))


def dot(x, y, color=GND, r=0.95):
    ax.add_patch(Circle((x, y), r, color=color, zorder=6))


def term(x, y, color=GND):
    ax.add_patch(Circle((x, y), 0.85, facecolor="white", edgecolor=color, lw=0.9, zorder=6))


def nc(x, y):
    d = 0.9
    wire([(x - d, y - d), (x + d, y + d)], GND, 0.8, z=6)
    wire([(x - d, y + d), (x + d, y - d)], GND, 0.8, z=6)


def t(x, y, s, size=6.0, color="black", ha="left", va="center", weight="normal", rot=0, bg=False):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="square,pad=0.08", facecolor="white", edgecolor="none")
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, rotation=rot, zorder=7, **kw)


def box(x0, y0, x1, y1, color=GND, fill="white", lw=1.0, ls="-", z=3):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fill, edgecolor=color, lw=lw, ls=ls, zorder=z))


def frame(x0, y0, x1, y1, title):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#bdbdbd", lw=0.6,
                           ls=(0, (4, 2)), zorder=1))
    t(x0 + 1.5, y1 - 2.6, title, 7.2, "#37474f", weight="bold")


def lines(x, y, rows, size=6.0, color="black", ha="center", step=3.4, weight="normal"):
    for i, s in enumerate(rows):
        t(x, y - i * step, s, size, color, ha=ha, weight=weight if i == 0 else "normal")


def clabel(x, y, s, color="#263238", ha="center", rot=0, size=6.0):
    return t(x, y, s, size, color, ha=ha, weight="bold", rot=rot, bg=True)


def cell(x, ytop, ybot, label):
    yc = (ytop + ybot) / 2
    wire([(x, ytop), (x, yc + 0.9)], PACK, LW16)
    wire([(x, yc - 0.9), (x, ybot)], GND, LW16)
    wire([(x - 4.5, yc + 0.9), (x + 4.5, yc + 0.9)], GND, 1.2)
    wire([(x - 2.4, yc - 0.9), (x + 2.4, yc - 0.9)], GND, 2.6)
    t(x + 5.3, yc + 2.4, "+", 7, PACK, weight="bold")
    t(x - 6, yc, label, 6.0, ha="right")


def fuse(x0, x1, y, color):
    xc = (x0 + x1) / 2
    wire([(x0, y), (xc - 5, y)], color, LW16)
    wire([(xc + 5, y), (x1, y)], color, LW16)
    box(xc - 5, y - 1.6, xc + 5, y + 1.6, GND, lw=1.0)
    wire([(xc - 5, y), (xc + 5, y)], GND, 0.8, z=4)


def switch_h(x0, x1, y, color=GND):
    term(x0, y, color)
    term(x1, y, color)
    wire([(x0 + 0.6, y + 0.5), (x1 - 0.4, y + 2.6)], color, 1.0, z=6)


def resistor_h(x0, x1, y, color, lbl):
    xc = (x0 + x1) / 2
    wire([(x0, y), (xc - 3.2, y)], color, LW26)
    wire([(xc + 3.2, y), (x1, y)], color, LW26)
    box(xc - 3.2, y - 1.1, xc + 3.2, y + 1.1, GND, lw=0.9)
    t(xc, y + 2.4, lbl, 5.6, ha="center")


def led_h(x0, x1, y, color):
    xc = (x0 + x1) / 2
    wire([(x0, y), (xc - 1.6, y)], color, LW26)
    wire([(xc + 1.6, y), (x1, y)], GND, LW26)
    ax.add_patch(Polygon([(xc - 1.6, y + 1.6), (xc - 1.6, y - 1.6), (xc + 1.6, y)], closed=True,
                         facecolor="white", edgecolor=GND, lw=0.9, zorder=5))
    wire([(xc + 1.6, y - 1.7), (xc + 1.6, y + 1.7)], GND, 1.0, z=5)
    for dx in (0.0, 1.4):
        ax.annotate("", xy=(xc + 1.2 + dx, y + 4.0), xytext=(xc - 0.2 + dx, y + 2.0),
                    arrowprops=dict(arrowstyle="-|>", lw=0.6, color=GND, mutation_scale=4), zorder=5)


def speaker(x, y):
    box(x, y - 2.2, x + 2.4, y + 2.2, GND, lw=0.9)
    ax.add_patch(Polygon([(x + 2.4, y - 2.2), (x + 5.6, y - 4.8), (x + 5.6, y + 4.8), (x + 2.4, y + 2.2)],
                         closed=True, facecolor="white", edgecolor=GND, lw=0.9, zorder=4))


def pin(x, y, side, name, color, length=4.0, size=5.8, weight="bold"):
    dx, dy = {"L": (-length, 0), "R": (length, 0), "T": (0, length), "B": (0, -length)}[side]
    wire([(x, y), (x + dx, y + dy)], color, LW26 if color in (SIG, V33) else 1.2, z=4)
    if side == "L":
        t(x + 1.0, y, name, size, ha="left", weight=weight)
    elif side == "R":
        t(x - 1.0, y, name, size, ha="right", weight=weight)
    elif side == "T":
        t(x, y - 1.9, name, size, ha="center", weight=weight)
    else:
        t(x, y + 1.9, name, size, ha="center", weight=weight)
    return (x + dx, y + dy)


def servo(xc, yc, sid, name, top_port, bot_port):
    box(xc - 14, yc - 6, xc + 14, yc + 6, BUS, fill="#f1f8e9", lw=1.0)
    t(xc, yc + 2.1, f"ID {sid}", 7.0, ha="center", weight="bold")
    t(xc, yc - 2.4, name, 6.0, ha="center")
    if top_port:
        wire([(xc, yc + 6), (xc, yc + 8)], BUS, LWBUS, z=4)
        t(xc + 1.6, yc + 7.4, top_port, 5.4, BUS, weight="bold")
    if bot_port:
        wire([(xc, yc - 6), (xc, yc - 8)], BUS, LWBUS, z=4)
        t(xc + 1.6, yc - 7.4, bot_port, 5.4, BUS, weight="bold")


def tag_h(x, y, color, label, ha="left", size=5.8):
    term(x, y, color)
    if ha == "left":
        t(x + 1.6, y, label, size, color if color != GND else "black", ha="left")
    else:
        t(x - 1.6, y, label, size, color if color != GND else "black", ha="right")


# ================================================================ sheet
box(5, 5, 415, 292, "#455a64", fill="none", lw=0.8, z=1)
t(9, 287.2, "Open Duck Mini v2, altaay-lab build: electrical schematic", 13, weight="bold")
t(9, 281.4, "Rev 2026-11-01, generated from wiring/netlist.yaml. Use with odm_v2_wiring_pictorial (every wire) and odm_v2_harness "
            "(routing, cut lengths). Cable IDs = CABLE_MAP.md. Tags: [U] upstream, [L] lab decision, [I] inferred.", 6.6, NOTE)

# ---------------------------------------------------------------- A: battery bay
frame(8, 190, 135, 276, "A  Battery bay (body_back): pack, BMS, charger")
YP, YM, YN = 250.0, 225.0, 200.0
XC = 30.0
lines(11, 268.5, ["2S pack: 2x Molicel INR18650-P30B [L]", "2S spring holder B09WCT8672 [U]", "6.0 to 8.4 V"], 6.0, ha="left")
cell(XC, YP, YM, "Cell 2")
cell(XC, YM, YN, "Cell 1")
dot(XC, YM, GND)
t(XC - 6, YM - 3.4, "series strap", 5.6, NOTE, ha="right")
bx0, bx1 = 56.0, 88.0
box(bx0, 194, bx1, 257, PACK, fill="#ffebee", lw=1.2)
for yy, nm in ((YP, "B+"), (YM, "B1"), (YN, "B-")):
    pin(bx0, yy, "L", nm, GND, 0.01)
for yy, nm in ((YP, "P+"), (YM, "T"), (YN, "P-")):
    pin(bx1, yy, "R", nm, GND, 0.01)
lines(72, 253.2, ["BMS [L]"], 7.0, weight="bold")
lines(72, 245.4, ["Tenergy", "P/N 32175", "2S PCM"], 6.0, step=3.2)
lines(72, 218.0, ["10 A working", "OC 22 +/- 5 A", "25 mOhm max", "34x16x4.5 mm"], 5.8, step=3.2)
wire([(XC, YP), (bx0, YP)], PACK, LW16)
clabel(43, YP + 2.6, CL("P1"))
wire([(XC, YM), (bx0, YM)], PACK, LW26)
clabel(43, YM + 2.4, CL("P3"))
wire([(XC, YN), (bx0, YN)], GND, LW16)
clabel(43, YN + 2.6, CL("P2"))
wire([(bx1, YM), (bx1 + 4, YM)], GND, LW26)
nc(bx1 + 4, YM)
lines(bx1 + 6.5, YM + 1.8, ["T = NTC output", "left open, insulate [I]"], 5.8, ha="left", step=3.1)
box(96, 256, 134, 272, PACK, fill="#ffebee", lw=1.0)
lines(115, 269.5, ["USB-C 2S charger [U]", "Adeept B0BJTW4QBR (BOM 11)", "charges with switch OFF [L]"], 5.8, step=3.2)
t(104, 258.3, "B+", 5.8, ha="center", weight="bold")
t(127, 258.3, "B-", 5.8, ha="center", weight="bold")
box(91.5, 266.0, 96, 269.6, GND, fill="#eeeeee", lw=0.8)
t(91.0, 267.8, "USB-C in", 5.4, ha="right")
wire([(bx1, YP), (141, YP)], PACK, LW16)
wire([(bx1, YN), (141, YN)], GND, LW16)
wire([(104, YP), (104, 256)], PACK, LW20)
dot(104, YP, PACK)
clabel(102.5, 253.0, CL("P4"), ha="right")
vhop(127, YN, 256, YP, GND, LW20)
dot(127, YN, GND)
clabel(125.5, 237.0, CL("P5"), ha="right")
clabel(117, YP + 2.6, CL("P6"))
clabel(114, YN + 2.6, CL("P8"))

# ---------------------------------------------------------------- B: disconnect, fuse, switch, splices
frame(137, 190, 258, 276, "B  Body_back: disconnect, fuse, main switch, splices")
for yy, sgn in ((YP, "+"), (YN, "-")):
    box(141, yy - 2.6, 153, yy + 2.6, GND, fill="#fff8e1", lw=0.9)
    wire([(147, yy - 2.6), (147, yy + 2.6)], GND, 0.8, z=4)
    t(144, yy, sgn, 6.5, ha="center", weight="bold")
    t(150, yy, sgn, 6.5, ha="center", weight="bold")
box(139.5, YN - 4.5, 154.5, YP + 4.5, GREY, fill="none", lw=0.7, ls=(0, (3, 2)), z=2)
lines(147, YP + 9.0, ["XT30U [U]"], 6.0, weight="bold")
lines(147, 230.0, ["Amass", "XT30U", "pack", "disconnect", "F: pack", "M: robot"], 5.6, step=3.0)
fuse(153, 190, YP, PACK)
lines(171.5, 259.5, ["F1 15 A ATO 32 V [L]", "Littelfuse 0287015.PXCN"], 5.8, step=3.2)
lines(171.5, 245.4, ["holder FHAC0001ZXJ", "20 A, leads 16 AWG 90 mm"], 5.6, step=3.0)
clabel(182.0, YP + 2.6, CL("P7"))
sx0, sx1, sy0, sy1 = 192.0, 236.0, 230.0, 258.0
box(sx0, sy0, sx1, sy1, VSW, fill="#fce4ec", lw=1.2)
pin(sx0, YP, "L", "VIN", PACK, 0.01)
pin(sx1, YP, "R", "VOUT", VSW, 0.01)
for xx, nm in ((198, "GND"), (209, "ON"), (222, "SW"), (230, "GND")):
    pin(xx, sy0, "B", nm, GND, 4.0)
nc(209, sy0 - 4.0)
lines(214, 254.6, ["SW1 Pololu 2815 [L]"], 6.4, weight="bold")
lines(214, 246.2, ["Big MOSFET Slide Switch HP", "slide switch on board: OFF", "16 A cont (MOSFET 150 C)",
                   "6 A at 55 C, 4.5 to 32 V"], 5.6, step=3.3)
wire([(222, sy0 - 4), (222, 219)], GND, LW26)
wire([(230, sy0 - 4), (230, 219)], GND, LW26)
switch_h(222, 230, 219)
lines(226, 214.4, ["S1 stock panel switch", CL("P15", " x2, under 0.1 mA")], 5.6, step=3.1)
XG, XV = 198.0, 248.0
wire([(153, YN), (XG, YN)], GND, LW16)
clabel(175.5, YN + 2.6, CL("P14"))
wire([(XG, sy0 - 4), (XG, YN)], GND, LW20)
clabel(196.5, 214.0, CL("P16"), ha="right")
dot(XG, YN, GND, 1.3)
t(XG + 2.0, YN - 3.2, "splice G", 6.0, weight="bold")
wire([(sx1, YP), (XV, YP)], VSW, LW16)
clabel(241.5, YP + 2.6, CL("P9"))
dot(XV, YP, VSW, 1.3)
t(XV - 1.0, YP + 5.6, "splice VSW", 6.0, VSW, ha="center", weight="bold")
t(XV - 1.0, YP + 9.0, "6.0 to 8.4 V", 5.6, VSW, ha="center")

# ---------------------------------------------------------------- C: servo supply (D15) and adapter (data only)
frame(260, 190, 412, 276, "C  Belly and trunk_top: servo supply (bypasses the adapter, D15) and adapter (data only)")
ux0, ux1 = 266.0, 302.0
wire([(XV, YP), (ux0, YP)], VSW, LW16)
clabel(257.0, YP + 2.6, CL("P10"))
wire([(XG, YN), (ux0, YN)], GND, LW16)
clabel(232.0, YN + 2.6, CL("P10"))
box(ux0, 195, ux1, 256, SERVO, fill="#fff3e0", lw=1.2)
pin(ux0, YP, "L", "IN+", VSW, 0.01)
pin(ux0, YN, "L", "IN-", GND, 0.01)
for yy, nm, col in ((244, "OUT1 +", SERVO), (237, "OUT2 +", SERVO), (213, "OUT1 -", GND), (206, "OUT2 -", GND)):
    pin(ux1, yy, "R", nm, col, 2.5)
lines(284, 252.4, ["U1 Castle", "CC BEC Pro [L]"], 6.4, weight="bold", step=3.4)
lines(284, 231.0, ["010-0004-01", "set to 7.2 V", "15 A cont at", "2S-4S (5 mph", "air), 20 A peak", "43x33x24 mm"],
      5.5, step=3.1)
wire([(ux1 + 2.5, 244), (307, 244), (307, 237), (ux1 + 2.5, 237)], SERVO, 1.2)
wire([(ux1 + 2.5, 213), (307, 213), (307, 206), (ux1 + 2.5, 206)], GND, 1.2)
dot(307, 240.5, SERVO)
dot(307, 209.5, GND)
t(307, 247.0, "JB+", 5.4, SERVO, ha="center", weight="bold")
t(307, 202.6, "JB-", 5.4, ha="center", weight="bold")
wire([(307, 240.5), (321, 240.5)], SERVO, LW16)
wire([(307, 209.5), (321, 209.5)], GND, LW16)
lines(314, 228.0, [CL("P11"), "x2, 60 mm", "3rd wires", "insulated [I]"], 5.2, step=2.9)
dot(321, 240.5, SERVO, 1.3)
dot(321, 209.5, GND, 1.3)
t(321, 246.4, "SPV", 6.0, SERVO, ha="center", weight="bold")
t(321, 203.8, "SPG", 6.0, ha="center", weight="bold")


def fan(xd, yd, col, outs, dy=4.6, lw=LW22):
    for k, lab in enumerate(outs):
        yo = yd + (len(outs) - 1) * dy / 2 - k * dy
        wire([(xd, yd), (xd + 4, yo), (xd + 8, yo)], col, lw)
        tag_h(xd + 8.85, yo, col, lab, size=5.4)


def fan_labels(splice_id, skip):
    out = []
    for c, p, cab, br in ends(f"{splice_id}.S"):
        if cab in skip:
            continue
        USED.add(cab)
        tgt = COMP[c]["ref"].replace("ID", "ID ") + (" " + p.split(".")[-1] if COMP[c]["kind"] != "splice" else "")
        out.append(f"{cab} to {tgt}")
    return out


fan(321, 240.5, SERVO, fan_labels("SPV", {"P11"}))
fan(321, 209.5, GND, fan_labels("SPG", {"P11"}))
t(336, 231.0, "22 AWG pairs (08-70-1040", 5.0, NOTE, ha="left")
t(336, 228.0, "takes 22 to 28 AWG)", 5.0, NOTE, ha="left")
# adapter: H1 not connected, H3/H5 carry DATA and GND only
ax0, ax1, ay0, ay1 = 364.0, 404.0, 214.0, 262.0
box(ax0, ay0, ax1, ay1, BUS, fill="#e8f5e9", lw=1.2)
for yy, nm in ((252.0, "DC+"), (245.0, "DC-")):
    end_ = pin(ax0, yy, "L", nm, GND, 3.0)
    nc(end_[0], yy)
t(ax0 - 4.5, 239.6, "H1 not", 5.2, "#b71c1c", ha="right", weight="bold")
t(ax0 - 4.5, 236.6, "connected", 5.2, "#b71c1c", ha="right", weight="bold")
lines(384, 258.6, ["U2 Waveshare", "Bus Servo", "Adapter (A) [U]"], 6.0, weight="bold", step=3.2)
lines(386, 245.6, ["SKU 25514", "jumper on B (USB)", "logic from USB", "VBUS (schematic)", "barrel: not used"], 5.2, step=2.9)
for x0s, nm in ((368.0, "H3"), (388.0, "H5")):
    for k, pn in enumerate(("D", "V", "G")):
        xx = x0s + k * 3.6
        if pn == "V":
            wire([(xx, ay0), (xx, ay0 - 2.0)], GREY, 0.8, z=4)
            nc(xx, ay0 - 2.0)
        else:
            wire([(xx, ay0), (xx, ay0 - 3.0)], BUS if pn == "D" else GND, LW22, z=4)
        t(xx, ay0 + 1.9, pn, 5.2, ha="center")
    t(x0s + 3.6, ay0 + 5.2, nm, 5.8, ha="center", weight="bold")
t(371.6, 208.6, "V", 4.6, NOTE, ha="center")
# H3: data Y (YD3, fan to the left) and ground Y (YG3, fan to the right); H5: SD2 straight down
wire([(368.0, ay0 - 3.0), (368.0, 199.8)], BUS, LW22)
dot(368.0, 199.8, BUS)
t(369.2, 202.2, "YD3", 5.0, BUS, ha="left", weight="bold")
wire([(375.2, ay0 - 3.0), (375.2, 194.6)], GND, LW22)
dot(375.2, 194.6, GND)
t(376.4, 197.0, "YG3", 5.0, ha="left", weight="bold")
for k, (c, p, cab, br) in enumerate([e for e in ends("YD3.S") if e[3] != "stem"]):
    yy = 201.6 - k * 3.6
    wire([(368.0, 199.8), (364.0, yy), (361.0, yy)], BUS, LW22)
    tag_h(360.15, yy, BUS, f"{cab} {br} to {COMP[c]['ref'].replace('ID', 'ID ')} D", ha="right", size=5.0)
for k, (c, p, cab, br) in enumerate([e for e in ends("YG3.S") if e[3] != "stem"]):
    yy = 196.4 - k * 3.6
    wire([(375.2, 194.6), (379.0, yy), (382.0, yy)], GND, LW22)
    tag_h(382.85, yy, GND, f"{cab} {br} to {COMP[c]['ref']}", size=5.0)
USED.add("SD1")
for xx, pp, col, yy in ((388.0, "H5.D", BUS, 204.6), (395.2, "H5.G", GND, 209.6)):
    c, p, cab, br = ends(f"U2.{pp}")[0]
    wire([(xx, ay0 - 3.0), (xx, yy + 0.85)], col, LW22)
    term(xx, yy, col)
    t(xx + 1.6, yy - 0.2, f"{cab} to {COMP[c]['ref'].replace('ID', 'ID ')}{' D' if pp.endswith('D') else ''}", 5.0,
      col if col != GND else "black", ha="left")
USED.add("SD2")
t(358.0, 270.6, "USB-C: D1 to the Pi USB port, /dev/ttyACM0 1 Mbaud [U]", 5.4, USB, ha="right")
box(392.0, ay1, 396.0, ay1 + 3.0, GND, fill="#eeeeee", lw=0.8)
wire([(394.0, ay1 + 3.0), (394.0, 270.6), (359.0, 270.6)], USB, 1.4, ls=(0, (3, 1.5)))
USED.add("D1")

# ---------------------------------------------------------------- D: Pi and its header
frame(8, 46, 283, 187, "D  Head floor and trunk_top: 5 V regulator U3, Raspberry Pi Zero 2 W, sensors, expression")
PIN_NAMES = {1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND",
             10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3",
             18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11", 24: "GPIO8", 25: "GND",
             26: "GPIO7", 27: "GPIO0", 28: "GPIO1", 29: "GPIO5", 30: "GND", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13",
             34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "GND", 40: "GPIO21"}
DCOL = {"3V3": V33, "5V": V5, "GND": GND}
USED_PINS = {int(p["pin"]) for p in COMP["PI"]["pins"] if p["pin"].isdigit()}
PITCH, Y1 = 4.6, 160.0
hx0, hx1 = 131.0, 149.0
box(hx0, Y1 - 19 * PITCH - 2.6, hx1, Y1 + 2.6, GND, fill="#e3f2fd", lw=1.1)
for r in range(20):
    y = Y1 - r * PITCH
    for p, xp, side in ((2 * r + 1, 136.0, "L"), (2 * r + 2, 144.0, "R")):
        used = p in USED_PINS
        ax.add_patch(Circle((xp, y), 0.85, facecolor=(GND if used else "white"), edgecolor=GND, lw=0.7, zorder=6))
        t(134.6 if side == "L" else 145.4, y, str(p), 5.2, ha="right" if side == "L" else "left",
          color=("black" if used else GREY))
        if used:
            sig = sig_name(p)
            col = DCOL.get(PIN[("PI", str(p))]["domain"], SIG)
            dest = pi_dest(p)
            if side == "L":
                wire([(hx0, y), (hx0 - 5, y)], col, 1.2, z=4)
                t(124.5, y, sig, 5.8, col if col != GND else "black", ha="right", weight="bold")
                xr = 110.5 if len(sig) > 6 else 115.5
                if len(dest) > 1 and len(", ".join(dest)) <= 36:
                    t(xr, y, ", ".join(dest), 5.2, ha="right")
                elif len(dest) > 1:
                    t(xr, y + 1.4, ", ".join(dest[:1]), 5.3, ha="right")
                    t(xr, y - 1.4, ", ".join(dest[1:]), 5.3, ha="right")
                else:
                    t(xr, y, dest[0], 5.5, ha="right")
            else:
                wire([(hx1, y), (hx1 + 5, y)], col, 1.2, z=4)
                t(155.5, y, sig, 5.8, col if col != GND else "black", ha="left", weight="bold")
                if len(dest) > 1:
                    t(166.0, y + 1.4, ", ".join(dest[:2]), 5.3, ha="left")
                    t(166.0, y - 1.4, ", ".join(dest[2:]), 5.3, ha="left")
                else:
                    t(166.0, y, dest[0], 5.5, ha="left")
        else:
            t(124.5 if side == "L" else 155.5, y, PIN_NAMES[p], 5.2, GREY, ha="right" if side == "L" else "left")
lines(140, 182.0, ["U4 Raspberry Pi Zero 2 W (head) [U]"], 6.6, weight="bold")
lines(140, 178.2, ["40-pin header, physical pin numbers, BCM GPIO names (pinout.xyz)",
                   "micro-USB port marked USB (OTG data): " + CL("D1") + " (Adafruit 3878, 0.9 m) to adapter USB-C",
                   "PWR IN micro-USB: leave empty, the Pi is fed on pins 2 and 6 [I]",
                   "CSI 22-pin: " + CL("D12") + " Adafruit 3157, 150 mm, to Camera Module 3 (Adafruit 5657)"], 5.5, step=3.1)
lines(140, 66.0, ["Eyes and antennas are swapped compared with the upstream assembly_guide pin table.",
                  "We follow the Runtime code at 376de65 (D9): eyes.py LEFT_EYE = D24, RIGHT_EYE = D23;",
                  "antennas.py LEFT = D13, RIGHT = D12; feet_contacts.py left D22, right D27 (pull-up);",
                  "projector.py D25. GND pins 6, 9, 14, 20, 25, 30, 34, 39 are one net (pinout.xyz)."],
      5.6, "#b71c1c", step=3.1)
# U3 5 V regulator: P13 from the splices up the neck, P12 down to Pi pins 2 and 6
rx0, rx1, ry0, ry1 = 212.0, 258.0, 150.0, 176.0
box(rx0, ry0, rx1, ry1, V5, fill="#f3e5f5", lw=1.2)
for xx, nm, col in ((222.0, "GND", GND), (XV, "VIN", VSW)):
    wire([(xx, ry1), (xx, ry1 + 4)], col, LW20, z=4)
    t(xx + 1.4, ry1 + 2.0, nm, 5.8, ha="left", weight="bold")
for xx, nm, col in ((238.0, "GND", GND), (250.0, "VOUT", V5)):
    pin(xx, ry0, "B", nm, col, 5.0)
for yy, nm in ((166.0, "EN"), (160.0, "PG")):
    pin(rx0, yy, "L", nm, GND, 3.0)
    nc(rx0 - 3.0, yy)
lines(235.5, 172.2, ["U3 Pololu D30V30F5"], 6.4, weight="bold")
lines(235.5, 168.6, ["[L] #4892, 5 V step-down", "3.8 A cont, 6 to 8.4 V in", "dropout 0.28 V at 2.5 A", "17.8 x 20.3 x 9 mm"],
      5.6, step=3.4)
wire([(XV, YP), (XV, ry1 + 4)], VSW, LW20)
vhop(XV, YN + 1.5, YN - 1.5, YN, VSW, LW20)
wire([(XG, YN), (XG, 183.0), (222.0, 183.0), (222.0, ry1 + 4)], GND, LW20)
clabel(XV + 1.7, 222.0, CL("P13", " red, up the neck"), ha="center", rot=90)
clabel(210.0, 185.2, CL("P13", " black"), ha="center")
tag_h(250.0, ry0 - 5.85, V5, to_pi("U3.VOUT").replace(" (P12)", ""), ha="left")
tag_h(238.0, ry0 - 5.85, GND, to_pi("U3.GND.2"), ha="right")
clabel(244.0, 140.2, CL("P12", " x2, 130 mm"))


def splice_fan(xd, yd, col, name, sid):
    src = [e for e in ends(f"{sid}.S") if e[0] == "PI"][0]
    outs = [e for e in ends(f"{sid}.S") if e[0] != "PI"]
    USED.add(src[2])
    tag_h(xd - 8.0, yd, col, f"Pi {src[1]} ({src[2]})", ha="right")
    wire([(xd - 8.0 + 0.85, yd), (xd, yd)], col, LW20)
    dot(xd, yd, col, 1.2)
    t(xd, yd + 2.8, name, 6.0, col if col != GND else "black", ha="center", weight="bold")
    for k, (c, p, cab, br) in enumerate(outs):
        USED.add(cab)
        yo = yd - k * 3.9
        wire([(xd, yd), (xd, yo), (xd + 8.0, yo)] if k else [(xd, yd), (xd + 8.0, yo)], col, LW26)
        tag_h(xd + 8.0, yo, col, f"{SHORT.get(c, c)} {PIN[(c, p)]['label']} ({cab})", ha="left")


splice_fan(236.0, 132.0, V5, "J5", "J5")
splice_fan(236.0, 117.0, GND, "JG", "JG")
lines(214.0, 102.6, ["1 W LED bead + 100 ohm in series (D13: projector too)"], 5.2, ha="left")
for k, (nm, rid, lid) in enumerate((("L eye", "RL", "LEDL"), ("R eye", "RR", "LEDR"), ("projector", "RP", "LEDP"))):
    yl = 97.0 - k * 6.4
    pl = to_pi(f"{rid}.1")
    tag_h(222.0, yl, SIG, pl.split(" (")[0], ha="right")
    resistor_h(222.85, 238.0, yl, SIG, "100")
    led_h(238.0, 252.0, yl, SIG)
    wire([(252.0, yl), (258.0, yl)], GND, LW26)
    cab = [e[2] for e in ends(f"{lid}.K")][0]
    tag_h(258.85, yl, GND, f"{to_pi(lid + '.K').split(' (')[0]}  {nm} ({cab})", ha="left")
mx0, mx1, my0, my1 = 224.0, 250.0, 50.0, 79.0
box(mx0, my0, mx1, my1, SIG, fill="#e3f2fd", lw=1.1)
for k, nm in enumerate(("LRC", "BCLK", "DIN", "GAIN", "SD", "GND", "VIN")):
    yy = 75.6 - k * 3.8
    col = SIG if nm in ("LRC", "BCLK", "DIN") else (V5 if nm == "VIN" else GND)
    end_ = pin(mx0, yy, "L", nm, col, 3.0, size=5.4)
    if PIN[("AMP", nm)]["dir"] == "nc":
        nc(end_[0], yy)
    else:
        tag_h(end_[0] - 0.85, yy, col, to_pi(f"AMP.{nm}").split(" (")[0] if nm in ("LRC", "BCLK", "DIN") else to_pi(f"AMP.{nm}").split(" (")[0], ha="right")
t(239.0, 63.4, "MAX98357A", 6.2, ha="center", weight="bold")
lines(239.0, 59.8, ["Adafruit 3006", CL("D10", " x5")], 5.4, step=3.1)
pin(mx1, 75.0, "R", "+", GND, 4.0)
pin(mx1, 70.0, "R", "-", GND, 4.0)
wire([(mx1 + 4, 75.0), (262.0, 75.0), (262.0, 73.4)], GND, LW26)
wire([(mx1 + 4, 70.0), (262.0, 70.0), (262.0, 71.0)], GND, LW26)
speaker(262.0, 72.2)
lines(266.0, 64.0, ["speaker 8 ohm", "2 W, Same Sky", "CMS0361KLX", CL("D11")], 5.4, step=3.0)
bnx0, bnx1, bny0, bny1 = 18.0, 34.0, 147.0, 170.0
lines(11, 180.2, ["BNO055 IMU, Adafruit 2472, on trunk_top [U]", CL("D2", " x4")], 5.8, ha="left", step=3.2)
box(bnx0, bny0, bnx1, bny1, SIG, fill="#e3f2fd", lw=1.1)
t((bnx0 + bnx1) / 2, 158.5, "BNO055", 5.6, ha="center", weight="bold", rot=90)
for yy, nm, col in ((166.5, "VIN", V33), (162.0, "GND", GND), (155.0, "SDA", SIG), (150.5, "SCL", SIG)):
    end_ = pin(bnx1, yy, "R", nm, col, 5.0, size=5.4)
    tag_h(end_[0] + 0.85, yy, col, to_pi(f"BNO.{nm}"))
for yy, nm in ((166.5, "3VO"), (150.5, "RST")):
    end_ = pin(bnx0, yy, "L", nm, GND, 3.0, size=5.4)
    nc(end_[0], yy)


def foot(ytop, name, ids, cab, rid):
    lines(11, ytop, [f"{name}: 2x Omron SS-01 (SS-10 fallback), {CL(cab)} x2", "COM to COM, NO to NO (Tnkr m11)"], 5.6, ha="left", step=3.0)
    ya, yb = ytop - 9.0, ytop - 15.0
    switch_h(22.0, 32.0, ya)
    switch_h(22.0, 32.0, yb)
    wire([(18.0, ya), (21.15, ya)], GND, LW26)
    wire([(18.0, yb), (21.15, yb)], GND, LW26)
    wire([(32.85, ya), (37.0, ya)], SIG, LW26)
    wire([(32.85, yb), (37.0, yb)], SIG, LW26)
    wire([(18.0, ya), (18.0, yb - 3.6), (42.0, yb - 3.6)], GND, LW26)
    wire([(37.0, ya), (37.0, yb)], SIG, LW26)
    wire([(37.0, (ya + yb) / 2), (42.0, (ya + yb) / 2)], SIG, LW26)
    dot(18.0, yb, GND, 0.7)
    dot(37.0, (ya + yb) / 2, SIG, 0.7)
    t(16.5, (ya + yb) / 2, "COM", 5.2, ha="right")
    t(35.0, ya + 2.6, "NO", 5.2, ha="center")
    tag_h(42.85, (ya + yb) / 2, SIG, to_pi(f"{ids}.NO"))
    tag_h(42.85, yb - 3.6, GND, to_pi(f"{ids}.COM"))
    dot(37.0, ya, SIG, 0.7)                                       # D17 pull-up, soldered at the Pi header
    resistor_h(37.0, 48.0, ya, V33, "")
    t(42.5, ya + 2.3, f"{COMP[rid]['ref']} 2.2k", 5.0, V33, ha="center", weight="bold")
    tag_h(48.85, ya, V33, to_pi(f"{rid}.1").split(" (")[0] + " 3V3", size=5.4)


foot(141.5, "L foot", "FSL1", "D3", "RFL")
foot(117.0, "R foot", "FSR1", "D4", "RFR")
lines(11, 94.6, ["Feet: internal pull-up plus 2.2 kOhm R4, R5 at the Pi header (D17),", "about 1.5 mA closed; pressed = low (feet_contacts.py)"], 5.4, NOTE, ha="left", step=3.0)


def sg90(y0, name, sid, extra):
    cab = ends(f"{sid}.SIG")[0][2]
    lines(11, y0 + 17.6, [f"{name} antenna SG90 (BOM 14), {cab}", extra], 5.6, ha="left", step=3.0)
    box(14.0, y0, 30.0, y0 + 12.0, SIG, fill="#e3f2fd", lw=1.0)
    t(22.0, y0 + 6.0, "SG90", 6.0, ha="center", weight="bold")
    for yy, nm, pn, col in ((y0 + 9.6, "sig", "SIG", SIG), (y0 + 6.0, "+5 V", "VCC", V5), (y0 + 2.4, "GND", "GND", GND)):
        wire([(30.0, yy), (36.0, yy)], col, LW26)
        t(30.6, yy + 1.35, nm, 5.2, ha="left")
        tag_h(36.85, yy, col, to_pi(f"{sid}.{pn}"))


sg90(68.0, "L", "SGL", "SG90 lead 250 mm, signal to the Pi pin")
sg90(48.5, "R", "SGR", "lead + 20 mm of 26 AWG x3 extension")

# ---------------------------------------------------------------- E: servo chains (D15)
frame(285, 46, 412, 187, "E  Servo bus (STS3215 x14, 7.4 V 1:345 [U])")
CX = {"L": 302.0, "N": 349.0, "R": 396.0}
ROWS = [150.0, 132.0, 114.0, 96.0, 78.0]
chains = {"L": ([20, 21, 22, 23, 24], ["L hip_yaw", "L hip_roll", "L hip_pitch", "L knee", "L ankle"], ["S2", "S3", "S4", "S5"]),
          "N": ([30, 31, 32, 33], ["neck_pitch", "head_pitch", "head_yaw", "head_roll"], ["S11", "S12", "S13"]),
          "R": ([10, 11, 12, 13, 14], ["R hip_yaw", "R hip_roll", "R hip_pitch", "R knee", "R ankle"], ["S7", "S8", "S9", "S10"])}
for col, (ids, names, cabs) in chains.items():
    xc = CX[col]
    for k, (sid, nm) in enumerate(zip(ids, names)):
        last = k == len(ids) - 1
        servo(xc, ROWS[k], sid, nm, "B2", "B1 free" if last else "B1")
        if last:
            wire([(xc, ROWS[k] - 6), (xc, ROWS[k] - 8)], GREY, 1.0)
        if k < len(ids) - 1:
            wire([(xc, ROWS[k] - 8), (xc, ROWS[k + 1] + 8)], BUS, LWBUS)
            clabel(xc - 2.0, (ROWS[k] + ROWS[k + 1]) / 2, f"{CL(cabs[k]).split()[0]} kit", ha="right")
    # made first lead on BUS 2 (D15): housing D V G; G joins two grounds at the JG splice
    head = f"SV{ids[0]}"
    yb = ROWS[0] + 8.0
    box(xc - 6.5, yb, xc + 6.5, yb + 3.6, GND, fill="#fafafa", lw=0.8, z=4)
    for j, pn in enumerate(("D", "V", "G")):
        t(xc - 4.2 + j * 4.2, yb + 1.8, pn, 5.0, ha="center", weight="bold")
    dsrc = ends(f"{head}.BUS2.D")[0]
    vsrc = ends(f"{head}.BUS2.V")[0]
    gsrc = ends(f"{head}.BUS2.G")[0]
    jg = gsrc[0]
    jins = [e for e in ends(f"{jg}.S") if e[0] != head]
    for cab in (dsrc[2], vsrc[2], gsrc[2]):
        USED.add(cab)
    xd, xv, xg = xc - 4.2, xc, xc + 4.2
    wire([(xd, yb + 3.6), (xd, yb + 9.0)], BUS, LW22)
    term(xd, yb + 9.85, BUS)
    t(xd - 0.2, yb + 11.4, f"{dsrc[2]}{dsrc[3] or ''} D {COMP[dsrc[0]]['ref']}", 4.8, BUS, ha="center", rot=90, va="bottom")
    wire([(xv, yb + 3.6), (xv, yb + 9.0)], SERVO, LW22)
    term(xv, yb + 9.85, SERVO)
    t(xv, yb + 11.4, f"{vsrc[2]} V {COMP[vsrc[0]]['ref']}", 4.8, SERVO, ha="center", rot=90, va="bottom")
    wire([(xg, yb + 3.6), (xg, yb + 6.0)], GND, LW22)
    dot(xg, yb + 6.0, GND, 0.8)
    t(xg + 1.4, yb + 5.2, jg, 4.6, ha="left", weight="bold")
    for m, (c, p, cab, br) in enumerate(jins):
        xx = xg + 2.8 * m
        wire([(xg, yb + 6.0), (xx, yb + 7.6), (xx, yb + 9.0)], GND, LW22)
        term(xx, yb + 9.85, GND)
        USED.add(cab)
        t(xx, yb + 11.4, f"{cab}{br if br in ('a', 'b') else ''} G {COMP[c]['ref']}", 4.6, ha="center", rot=90, va="bottom")
t(CX["L"] - 15.5, 176.0, "Left leg", 6.0, ha="right", weight="bold")
t(CX["N"] - 15.5, 176.0, "Neck", 6.0, ha="right", weight="bold")
t(CX["R"] - 15.5, 176.0, "Right leg", 6.0, ha="right", weight="bold")
lines(357.0, 66.0, ["Bus in each chain: 1 DATA, 2 V+ 7.2 V, 3 GND;", "kit cable 5264-3P 150 mm, BUS 1 = BUS 2.",
                             "First servo: made lead on BUS 2 (D15), Molex", "50-37-5033 housing, 08-70-1040 terminals,",
                             "one wire per terminal. D from the adapter,", "V and G from the belly splices SPV/SPG."],
      5.2, NOTE, ha="left", step=2.8)
# legend (bottom of E)
leg = [(PACK, LW16, "-", "pack +"), (VSW, LW16, "-", "switched VSW"), (SERVO, LW16, "-", "servo 7.2 V"),
       (GND, LW16, "-", "ground"), (V5, LW20, "-", "5 V"), (V33, LW26, "-", "3.3 V"),
       (SIG, LW26, "-", "GPIO I2C I2S"), (BUS, LWBUS, "-", "servo bus"), (USB, 1.4, (0, (3, 1.5)), "USB")]
for i, (col, lw, ls, txt) in enumerate(leg):
    xx = 288.0 + (i // 3) * 22.0
    yy = 62.5 - (i % 3) * 4.0
    wire([(xx, yy), (xx + 6, yy)], col, lw, ls)
    t(xx + 7.2, yy, txt, 5.0)
dot(290, 48.6, GND)
t(292, 48.6, "splice", 5.0)
term(304, 48.6)
t(306, 48.6, "named end", 5.0)
nc(322, 48.6)
t(324, 48.6, "NC", 5.0)

# ---------------------------------------------------------------- notes and title block
frame(8, 8, 283, 44, "Notes")
notes = [
    "1. All grounds are common and return to BMS P- (splice G, P14, XT30, P8). B- and P- are separate nodes on the Tenergy board: nothing but the cell goes on B- [L].",
    "2. Power on: XT30 in, panel switch ON. The 2815 slide switch stays OFF so the panel switch (between SW and GND) controls it. Not an emergency cutoff (Pololu): unplug the XT30.",
    "3. Battery: Tenergy cuts at 2.40 V per cell, below the P30B 2.5 V minimum: stop in software at servo Present Voltage about 6.0 V (about 3.3 V per cell loaded).",
    "4. D15: servo power bypasses the adapter (BEC -> SPV/SPG -> SP1 SP2 SP3). Adapter H1 NOT connected; its 3.3 V logic runs from USB VBUS. Bench check: it must enumerate and drive the bus with H1 unpowered.",
    "5. Program U1 to 7.2 V with Castle Link V4 through its Link Port (2-wire jumper, U1 at 5 V or more) and measure before connecting servos. Check U3 = 5 V with no load first.",
    "6. Solder 16 AWG into the 2815 large holes (Pololu: use them above 5 A). U3 EN and PG stay open. Pins 9 and 20 take 3 x 26 AWG each: twist and tin first [I].",
    "7. BMS pads (Tenergy image): B-, B1 (mid tap, to the holder series strap), B+, P-, P+, T (NTC output, left open [I]). Pin 6 holds the U3 ground, so the SG90s and amp return on pin 14 [I].",
]
notes.append("8. D17 (7:24 PM ET): foot switches Omron SS-01 gold contacts (min. load 5 VDC 1 mA), SS-10 fallback (5 VDC 160 mA); the feet feed the policy, so R4, R5 2.2 kOhm pull-ups give about 1.5 mA.")
for i, s in enumerate(notes):
    t(10.5, 38.6 - i * 3.75, s, 5.3)
box(285, 8, 412, 44, "#455a64", fill="none", lw=0.8, z=1)
lines(348.5, 39.5, ["Open Duck Mini v2, altaay-lab build"], 8.0, weight="bold")
lines(348.5, 34.0, ["Electrical schematic, sheet 1 of 1, rev 2026-11-01",
                    "Generated from wiring/netlist.yaml by make_schematic.py",
                    "Every wire: odm_v2_wiring_pictorial",
                    "Routing, cut lengths: odm_v2_harness",
                    "Supersedes odm_v2_wiring (old block diagram)",
                    "Print A3 or tabloid, landscape, at 100 %"], 6.0, step=3.6)

# ---------------------------------------------------------------- coverage check and save
active = {c for c, cb in CABLES.items() if cb["status"] == "active"}
missing = sorted(active - USED, key=lambda s: (s[0], int("".join(ch for ch in s if ch.isdigit()) or 0)))
if missing:
    raise SystemExit(f"cables in netlist.yaml not on the schematic: {missing}")
if __name__ == "__main__":
    fig.savefig(os.path.join(HERE, "odm_v2_schematic.svg"))
    png = os.path.join(HERE, "odm_v2_schematic.png")
    fig.savefig(png, dpi=150)
    if os.path.getsize(png) > 900_000:                     # keep the PNG well under 1 MB
        from PIL import Image
        Image.open(png).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(png, optimize=True)
    print("wrote odm_v2_schematic.svg and .png", os.path.getsize(png), "bytes")
