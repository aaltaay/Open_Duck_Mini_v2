"""Draws altaay_lab/wiring/odm_v2_harness.svg and .png from netlist.yaml (A3 landscape, print at 100%).

Harness and routing drawing: body regions (seen from behind, robot left on the left), the joints each cable
crosses, every cable with its CABLE_MAP id, gauge, conductor count and cut length, plus a cut list.
All cable data comes from netlist.yaml (cables and wires); the script stops if an active cable is not drawn
or listed. Positions are a map of the robot, not to scale.
"""
import os
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
from matplotlib.lines import Line2D

plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["font.family"] = "DejaVu Sans"

HERE = os.path.dirname(os.path.abspath(__file__))
NET = yaml.safe_load(open(os.path.join(HERE, "netlist.yaml"), encoding="utf-8"))
CAB = {c["id"]: c for c in NET["cables"]}
WIRES = {}
for w in NET["wires"]:
    WIRES.setdefault(w["cable"], []).append(w)
DRAWN = set()

W, H = 420.0, 297.0
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")
COL = {"P": "#c62828", "D": "#1565c0", "S": "#2e7d32"}
ABBR = {"neck_pitch": "NP", "head_pitch": "HP", "head_yaw": "HY", "head_roll": "HR",
        "left_hip_yaw": "LHY", "left_hip_roll": "LHR", "left_hip_pitch": "LHP", "left_knee": "LK", "left_ankle": "LA",
        "right_hip_yaw": "RHY", "right_hip_roll": "RHR", "right_hip_pitch": "RHP", "right_knee": "RK", "right_ankle": "RA"}


def t(x, y, s, size=6.0, color="black", ha="left", va="center", weight="normal", rot=0, bg=False):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.15,rounding_size=0.5", facecolor="white", edgecolor="#bdbdbd", lw=0.3)
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, rotation=rot, zorder=8, **kw)


def line(pts, color, lw=1.4, ls="-", z=3):
    ax.add_line(Line2D([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls, zorder=z,
                       solid_capstyle="round", solid_joinstyle="round"))


def region(x0, y0, x1, y1, name, fc):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=2.5", facecolor=fc,
                                edgecolor="#78909c", lw=0.9, zorder=1))
    t(x0 + 2, y1 - 2.8, name, 7.0, "#263238", weight="bold")


def joint(x0, x1, y, name):
    line([(x0, y), (x1, y)], "#6a1b9a", 1.0, (0, (4, 2)), z=2)
    t(x1 + 1.2, y, f"{name} ({ABBR[name]})", 5.4, "#6a1b9a", weight="bold")


def tile(x, y, s, fc="#eceff1", size=5.4, w=None):
    ww = w or (len(s) * size * 0.2 + 3)
    ax.add_patch(FancyBboxPatch((x - ww / 2, y - 2.2), ww, 4.4, boxstyle="round,pad=0,rounding_size=1", facecolor=fc,
                                edgecolor="#546e7a", lw=0.5, zorder=4))
    t(x, y, s, size, ha="center", weight="bold")


def cuts_text(ws):
    c = sorted({int(w["cut_mm"]) for w in ws if w["cut_mm"] not in (None, 0)})
    if not c:
        return "as shipped"
    return ("/".join(str(x) for x in c) if len(c) <= 2 else f"{c[0]} to {c[-1]}") + " mm"


def info(cid):
    """Main run of a cable from the netlist, e.g. 'P13 20 AWG x2, 550 mm' (+ tails, jumpers, Y branches)."""
    ws = [w for w in WIRES[cid] if w["cut_mm"] != 0]
    if ws[0]["gauge"] == "kit cable":
        return f"{cid} kit cable, 150 mm"
    br = {}
    for w in ws:
        br.setdefault(w.get("branch"), []).append(w)
    if "stem" in br:
        return (f"{cid} {ws[0]['gauge']} x{len(br['stem'])}: stem {cuts_text(br['stem'])}, "
                f"a {cuts_text(br['a'])}, b {cuts_text(br['b'])}")
    main = br.get(None) or ws
    g = main[0]["gauge"]
    out = f"{cid} {g} x{len(main)}, {cuts_text(main)}"
    for b, bw in br.items():
        if b is None or main is ws:
            continue
        out += f" + {b} {cuts_text(bw)}" if cuts_text(bw) != "as shipped" else " + BEC leads"
    return out


def joints_of(cid):
    j = CAB[cid]["joints"] or []
    return " ".join(ABBR[x] for x in j) if j else "none"


def cable(cid, pts, lx, ly, ha="left", lw=1.5):
    DRAWN.add(cid)
    line(pts, COL[cid[0]], lw)
    jj = joints_of(cid)
    t(lx, ly, info(cid) + ("" if jj == "none" else f"  [{jj}]"), 5.3, "#212121", ha=ha, weight="bold", bg=True)


def listing(x, y, title, cids, width=None):
    t(x, y, title, 5.6, "#37474f", weight="bold")
    for i, cid in enumerate(cids):
        DRAWN.add(cid)
        t(x, y - 3.3 * (i + 1), info(cid), 5.2)
    return y - 3.3 * (len(cids) + 1)


# ---------------------------------------------------------------- page
ax.add_patch(Rectangle((5, 5), 410, 287, facecolor="none", edgecolor="#455a64", lw=0.8, zorder=0))
t(9, 287.0, "Open Duck Mini v2, altaay-lab build: harness and routing by body region", 13, weight="bold")
t(9, 281.4, "Rev 2026-11-01, generated from wiring/netlist.yaml. Seen from behind (robot left on the left), not to scale. "
            "Label: cable id (CABLE_MAP.md), gauge x conductors, cut length, [joints crossed].", 6.4, "#455a64")

# regions
region(58, 236, 222, 276, "HEAD (Pi, U3, amp, LEDs, SG90s, camera, ID 33)", "#e3f2fd")
region(112, 200, 168, 234, "NECK", "#f3e5f5")
region(28, 162, 252, 198, "TRUNK_TOP (adapter U2, BNO055, ID 30)", "#e8f5e9")
region(8, 118, 126, 160, "BATTERY BAY (body_back)", "#fff8e1")
region(130, 118, 252, 160, "BELLY (BEC U1, splices SPV SPG)", "#fbe9e7")
region(28, 96, 252, 116, "TRUNK_BOTTOM (ID 20, ID 10)", "#ede7f6")
region(28, 10, 126, 94, "LEFT LEG", "#eceff1")
region(154, 10, 252, 94, "RIGHT LEG", "#eceff1")

# joints in the neck (bottom to top) and legs
joint(112, 168, 200.6, "neck_pitch")
joint(112, 168, 216.0, "head_pitch")
joint(112, 168, 222.0, "head_yaw")
joint(112, 168, 233.4, "head_roll")
tile(126, 208, "ID 31")
tile(126, 227.5, "ID 32")
for side, x0, x1, ids in (("left", 28, 126, (21, 22, 23, 24)), ("right", 154, 252, (11, 12, 13, 14))):
    for k, (jn, yy) in enumerate(((f"{side}_hip_yaw", 93.4), (f"{side}_hip_roll", 80.0), (f"{side}_hip_pitch", 64.0),
                                  (f"{side}_knee", 46.0), (f"{side}_ankle", 28.0))):
        line([(x0, yy), (x1, yy)], "#6a1b9a", 1.0, (0, (4, 2)), z=2)
        t(x0 + 1.5, yy + 1.8, ABBR[jn], 5.0, "#6a1b9a", weight="bold")
    xc = (x0 + x1) / 2
    for k, (sid, yy) in enumerate(zip(ids, (86.5, 72.0, 55.0, 37.0))):
        tile(xc - 18, yy, f"ID {sid}")
    tile(xc - 18, 18.5, "2x SS-01 (SS-10)")

# tiles in the trunk and head
tile(140, 182, "U2 adapter")
tile(205, 182, "BNO055")
tile(70, 182, "ID 30")
tile(108, 175, "YD3 YG3")
tile(88, 175, "JG30")
tile(165, 146, "U1 BEC")
tile(200, 146, "JB SPV SPG")
tile(232, 126, "D1 coil")
tile(66, 106, "ID 20 + JG20")
tile(214, 106, "ID 10 + JG10")
tile(140, 262, "Pi U4")
tile(96, 262, "U3")
tile(180, 262, "amp + speaker")
tile(24, 128, "SW1 VSW G", w=22)
tile(62, 140, "holder BMS", w=22)
tile(102, 128, "XT30 F1", w=16)

# ---------------------------------------------------------------- cables between regions
# neck bundle: P13, D1, D2, D3, D4 cross all 4 neck joints; kit cables S11 to S13 cross some
xs = {"P13": 132.0, "D1": 136.0, "D2": 140.0, "D3": 144.0, "D4": 148.0}
for cid, x in xs.items():
    DRAWN.add(cid)
    line([(x, 258), (x, 196)], COL[cid[0]], 1.8 if cid != "D1" else 2.4)
cl = ["Through the neck, crossing NP HP HY HR (4 joints, 9.69 rad):"] + [info(c) for c in xs]
for i, s in enumerate(cl):
    t(196.0, 231.0 - i * 3.3, s, 5.3, "#212121", weight="bold" if i == 0 else "normal")
t(196.0, 231.0 - len(cl) * 3.3, "D1 is Adafruit 3878 (0.9 m): coil the slack in the belly", 5.2, "#455a64")
cable("S11", [(70, 186), (70, 205), (122, 208)], 72.0, 204.0, lw=1.2)
cable("S12", [(126, 210.5), (126, 225.2)], 72.0, 218.6, lw=1.2)
cable("S13", [(130, 227.5), (160, 238), (199, 243)], 72.0, 228.4, lw=1.2)
# P13 from the battery bay splices up to the neck
cable("P13", [(30, 137), (24, 160), (24, 190), (132, 196)], 30.0, 166.0)
ax.texts[-1].remove()
t(21.6, 175.0, info("P13"), 5.2, "#212121", weight="bold", rot=90, bg=True)
line([(132, 196), (132, 196)], COL["P"])
# D1 down into the belly coil and back to the adapter
line([(136, 196), (236, 160), (232, 129)], COL["D"], 2.4)
line([(232, 129), (150, 178)], COL["D"], 2.4, (0, (3, 1.5)))
# D2 to the BNO055
line([(140, 196), (205, 185)], COL["D"], 1.8)
# D3 and D4 down to the feet
line([(144, 196), (36, 170), (34, 110), (36, 94), (36, 21)], COL["D"], 1.8)
line([(148, 196), (246, 170), (246, 110), (246, 94), (246, 21)], COL["D"], 1.8)
t(37.5, 50.0, info("D3"), 5.2, weight="bold", rot=90, bg=True)
t(244.5, 50.0, info("D4"), 5.2, weight="bold", rot=90, bg=True)
t(40.6, 50.0, "[" + joints_of("D3") + "]", 4.8, "#6a1b9a", rot=90)
t(241.4, 50.0, "[" + joints_of("D4") + "]", 4.8, "#6a1b9a", rot=90)
# power from the battery bay to the belly
cable("P10", [(36, 137), (60, 124), (160, 140)], 52.0, 128.5)
# servo power pairs and data leads (D15)
cable("SP1", [(196, 144), (110, 128), (68, 108)], 132.0, 124.0)
cable("SP2", [(204, 144), (214, 109)], 207.0, 132.5, ha="right")
cable("SP3", [(198, 149), (150, 158), (90, 176)], 160.0, 168.4, ha="right")
cable("SD1", [(108, 173), (78, 150), (66, 109)], 79.5, 141.5)
cable("SD2", [(146, 179), (196, 170), (214, 109)], 247.0, 170.0, ha="right")
# legs: kit cables cross one joint each
for side, x, cabs in (("L", 77, ("S2", "S3", "S4", "S5")), ("R", 203, ("S7", "S8", "S9", "S10"))):
    for k, (cid, y0, y1) in enumerate(zip(cabs, (104.0, 84.3, 69.8, 52.8), (88.7, 74.2, 57.2, 39.2))):
        cable(cid, [(x, y0), (x, y1)], x + 3.0, (y0 + y1) / 2, lw=1.4)

# local cables, listed per region
DRAWN.update({"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P14", "P15", "P16"})
t(11, 152.6, "Inside (no joints, details in the cut list):", 5.2, "#37474f", weight="bold")
t(11, 149.2, "P1 P2 P3 P4 P5 P6 P7 P8 P9 P14 P15 P16", 5.2, "#c62828", weight="bold")
DRAWN.update({"P11", "P12", "P17"})
t(134, 152.0, "Inside the belly: " + info("P11"), 5.2)
DRAWN.update({"P12", "P17", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"})
t(62, 254.0, "Inside (no joints, details in the cut list):", 5.2, "#37474f", weight="bold")
t(62, 250.6, "P12 P17 D5 D6 D7 D8 D9 D10 D11 D12", 5.2, "#1565c0", weight="bold")
t(62, 247.2, "R4, R5 2.2 kOhm foot pull-ups soldered at the Pi header (pins 17-15, 17-13; D17)", 5.0, "#00838f")
tile(205, 244, "ID 33")

# ---------------------------------------------------------------- cut list
X0 = 262.0
t(X0, 271.0, "Cut list (from netlist.yaml; cut = per conductor)", 7.0, weight="bold")
cols = [(X0, "ID"), (X0 + 11, "from -> to"), (X0 + 79, "wire"), (X0 + 104, "cut mm"), (X0 + 120, "joints")]
yy = 266.0
for x, h in cols:
    t(x, yy, h, 5.4, "#37474f", weight="bold")
line([(X0, yy - 1.8), (412, yy - 1.8)], "#90a4ae", 0.5)
order = sorted([c for c in CAB.values() if c["status"] == "active"], key=lambda c: ("PDS".index(c["id"][0]), int("".join(ch for ch in c["id"] if ch.isdigit()))))
for i, c in enumerate(order):
    yy = 262.6 - i * 4.55
    if i % 2 == 0:
        ax.add_patch(Rectangle((X0 - 1, yy - 2.25), 151, 4.55, facecolor="#f5f5f5", edgecolor="none", zorder=0.5))
    ws = [w for w in WIRES[c["id"]] if w["cut_mm"] != 0]
    brs = {}
    for w_ in ws:
        brs.setdefault(w_.get("branch"), []).append(w_)
    mainw = brs.get("stem") or brs.get(None) or ws
    g = mainw[0]["gauge"]
    n = len(mainw)
    desc = c["desc"]
    desc = desc if len(desc) <= 48 else desc[:46] + ".."
    t(X0, yy, c["id"], 5.2, COL[c["id"][0]], weight="bold")
    t(X0 + 11, yy, desc, 4.7)
    t(X0 + 79, yy, f"{g} x{n}" if g != "kit cable" else "kit cable", 4.8)
    t(X0 + 104, yy, cuts_text(ws).replace(" mm", ""), 4.8)
    t(X0 + 120, yy, joints_of(c["id"]), 4.6, "#6a1b9a")
yy -= 6.0
rem = [c["id"] for c in CAB.values() if c["status"] != "active"]
t(X0, yy, "Removed: " + ", ".join(rem) + " (kit S1 and S6 replaced by SP/SD made leads, S14 and the D14 Y-lead dropped, D15)", 4.8, "#b71c1c")
t(X0, yy - 3.6, "Joints: " + ", ".join(f"{v} {k}" for k, v in list(ABBR.items())[:4]) + "; L/R HY HR HP K A = hip yaw, hip roll,", 4.6, "#6a1b9a")
t(X0, yy - 6.8, "hip pitch, knee, ankle. Kit cables: test-fit the BLOCKER hops at both joint limits (B17).", 4.6, "#6a1b9a")

# notes
notes = ["Wire totals and the length rule: CABLE_MAP.md. Rule = polyline + 2 x 22.6 + 2 x 20 + 10 mm per radian crossed.",
         "Positions of parts not in the CAD come from audit/placements.json (MOUNTING.md, D11). Every wire, terminal to terminal: odm_v2_wiring_pictorial."]
for i, s in enumerate(notes):
    t(262.0, 18.0 - i * 3.6, s, 4.9, "#455a64")

missing = sorted(c for c, cb in CAB.items() if cb["status"] == "active" and c not in DRAWN)
if missing:
    raise SystemExit(f"active cables not on the harness drawing: {missing}")
if __name__ == "__main__":
    fig.savefig(os.path.join(HERE, "odm_v2_harness.svg"))
    png = os.path.join(HERE, "odm_v2_harness.png")
    fig.savefig(png, dpi=150)
    if os.path.getsize(png) > 900_000:                     # keep the PNG well under 1 MB
        from PIL import Image
        Image.open(png).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(png, optimize=True)
    print("wrote odm_v2_harness.svg and .png", os.path.getsize(png), "bytes")
