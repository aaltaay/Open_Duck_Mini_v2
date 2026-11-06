#!/usr/bin/env python3
"""Write altaay_lab/viewer/scene_extras.json: every small real part the exploded 3D view does not draw yet.

Items: a connector body at every cable end (Mini-SPOX housings with their crimp terminals, kit cable 5264 plugs,
XT30 halves, USB plugs, camera FPC ends, the Pi 2x20 header, the amp speaker terminal block), a solder joint
marker at every soldered pad, header pin, hole, lug, tab and terminal, 13 of the 15 splices (JFI and JFO at the fuse
holder are placed by viewer/make_viewer_data.py step 10f), the 5 resistors, heat
shrink sleeves at the XT30 cups and the inline lead joints, foam tape pads under the taped parts, the eye glass
discs, the projector reflector, the microSD card, the ATO fuse, the eye screw washers, the SG90 horns and the
kapton wrap of the BMS.

Inputs (all read-only): altaay_lab/cables3d/cables3d.json (cable_ends: the wire exit point and direction of
every terminal, seats of xt30, amp, speaker and LEDs, routed cable polylines), wiring/netlist.yaml (which end is
a plug, a crimp, a splice or a solder joint), fasteners/fasteners.json (eye screw washers), audit/placements.json
(taped parts), bom_full.csv (row ids), the URDF and print/ meshes (servo case frames, Pi, adapter, eye glass
seats, reflector seat, microSD slot, mounting faces for the foam pads).

Frame: URDF world at the zero pose, x forward, y left, z up, mm (same as the viewer and cables3d).
Box convention (viewer/make_viewer_data.py step 10e): center_mm, axis = box long axis (dims_mm[0] along it);
the viewer turns box z onto axis with rot_z_to(axis) and lays dims_mm[1] along that frame's x and dims_mm[2]
along its y. dims_mm is written for that convention, so axis-aligned boxes come out right. rotation_3x3
(columns: world directions of the box width, height and length) and dims_local_mm [length, width, height]
give the exact box for boxes that are not axis aligned (SG90 horns, panel switch lugs).

Usage: python3 altaay_lab/blueprint/make_scene_extras.py [--check]
"""
import argparse
import csv
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scene3d import Scene, tf, rot, LAB  # noqa: E402

OUT = os.path.join(LAB, "viewer", "scene_extras.json")
COVER = os.path.join(HERE, "coverage.json")
CABLES3D = os.path.join(LAB, "cables3d", "cables3d.json")
FASTENERS = os.path.join(LAB, "fasteners", "fasteners.json")
PLACEMENTS = os.path.join(LAB, "audit", "placements.json")
NETLIST = os.path.join(LAB, "wiring", "netlist.yaml")
BOMFULL = os.path.join(LAB, "bom_full.csv")

# ------------------------------------------------------------------------------------------------ sources
U_MOLEX = ("UNVERIFIED stand-in 10.0 x 9.9 x 4.4 mm (Molex sales drawing for 50-37-5033 not reachable from this "
           "session: molex.com refused, lcsc.com and digikey not allowed). 9.9 mm along the pin row so two fit end to end "
           "in the 20.0 mm socket slot and 4.4 mm thick so it fits the 4.5 mm slot (slot measured on "
           "wj-wk00-0124bottomcase_45.stl), 10.0 mm along the mating axis assumed")
SRC = dict(
    feetech="[I] Feetech STS3215 datasheet bottom view: 2 x 5264 3P sockets end to end, pins G V S from case +z, pin row "
            "12.5 mm from the idle shaft (https://www.mantech.co.za/Datasheets/Products/STS3215-200620A.pdf p.5)",
    c3d="altaay_lab/cables3d/cables3d.json cable_ends (wire exit point and direction of the terminal)",
    ws="[I] Waveshare photo, top view: sockets printed D V G left to right, along robot +x "
       "(https://www.waveshare.com/w/upload/a/a3/Bus_Servo_Adapter%28A%29-A.jpg)",
    pi="[I] Raspberry Pi Zero 2 W mechanical drawing (https://datasheets.raspberrypi.com/rpizero2/"
       "raspberry-pi-zero-2-w-mechanical-drawing.pdf) mapped onto raspberrypizerow.stl as in cables3d (pin 1 x -24.13)",
    bno="[U] Adafruit BNO055 board file via cables3d: JP1 Vin 3Vo GND SDA SCL RST at 2.54 mm; which end is Vin is [I]",
    amp="[I] netlist AMP group note: printed LRC BCLK DIN GAIN SD GND Vin, order on the board not checked",
    marker="solder joint marker 3.0 x 1.8 x 1.8 mm (drawing convention, not a part size)",
    splice="UNVERIFIED size: solder splice in 3:1 adhesive heat shrink (BOM 26), 20 mm long stand-in, diameter = bundle "
           "of the wire outside diameters (cables3d WIRE_OD, BNTECHGO pages; packing 1.155 d sqrt(n)) + 1.0 mm shrink wall",
    resistor="UNVERIFIED stand-in body 6.3 x 2.4 mm (typical 1/4 W axial; the Adafruit 2782 and SparkFun PRT-14493 pages "
             "give no body size)",
    foam="3M VHB 4950, 1.1 mm thick, 3/4 in (19.05 mm) wide (BOM line 29); one strip per part, on the face MOUNTING.md tapes",
    xt30="UNVERIFIED 16 x 10 x 5.2 mm per half: half of the 32 x 10 x 5.2 mm mated stand-in used by make_viewer_data.py "
         "and the cables3d xt30 seat (Amass drawing not reachable)",
    usbm="UNVERIFIED stand-in overmold 20 x 10.5 x 7.0 mm (Adafruit 3878 page gives no plug size; 20 mm as the cables3d "
         "PI.USB terminal)",
    usbc="UNVERIFIED stand-in overmold 20 x 12.4 x 6.5 mm (no plug size published for Adafruit 3878; 20 mm as cables3d U2.USB)",
    fpc="UNVERIFIED stand-in: FPC end 6 mm long, 0.3 mm thick; width 11.5 mm (22-pin 0.5 mm pitch) and 16 mm (15-pin 1 mm "
        "pitch) (Adafruit 3157 page gives no drawing)",
    header="standard 2.54 mm 2 x 20 male header: 50.8 x 5.08 mm, plastic 2.5 mm thick [I], 8.5 mm overall as the cables3d "
           "pi_header keepout; pins not drawn except where a wire is soldered (solder markers)",
    glass="BOM line E4 disc 29.6 x 1.85 mm; seat measured on the print STL (29.6 mm bore, back face on the 25.0 mm lip)",
    reflector="BOM line E5 Aurorad S5 20 x 15 mm, read as 20 mm diameter x 15 mm tall (UNVERIFIED reading), drawn as its "
              "envelope; narrow end on the 8.1 mm aperture face measured on flash_reflector_interface.stl",
    microsd="microSD card 15 x 11 x 1.0 mm (SD Association form factor; not opened from this session); slot measured on "
            "raspberrypizerow.stl (raised body 1.5 mm, card inserted from the board end)",
    ato="UNVERIFIED 19.1 x 18.8 x 5.1 mm (ATO size from distributor listings seen in search, Littelfuse 287 datasheet not "
        "reached); orientation inside the holder [I]",
    washer="fasteners.json: two M2.5 flat washers, ISO 7092 A4 HV200, 2.7 x 5.0 x 0.3 mm (BOM 17l, BelMetric WFHV2.5X5SSA4) "
           "under each eye screw head (D21 note)",
    sg90horn="UNVERIFIED stand-in 7 x 7 x 2 mm on the SG90 output shaft (antenna joint axis), under the antenna holder "
             "recess; the SG90 bag horn has no published size and is not in the CAD",
    tblock="UNVERIFIED stand-in 7.0 x 7.0 x 8.5 mm: 2-position 3.5 mm terminal block that ships with the Adafruit 3006 "
           "(netlist AMP spk group, pitch 3.5 [I])",
    kapton="MOUNTING.md: 'wrap in kapton tape before it goes in' (BMS); drawn as a 0.1 mm skin over the BMS box "
           "(BOM.md polyimide tape line when present)",
)
# wire outside diameters (cables3d route_cables.py WIRE_OD and WIRE_OD_UNVERIFIED)
WIRE_OD = {"16 AWG": 3.0, "20 AWG": 1.8, "22 AWG": 1.7, "26 AWG": 1.5, "USB 2.0 cable": 3.5, "kit cable": 1.3,
           "SG90 lead": 1.0, "SG90 lead + 26 AWG": 1.5, "BEC lead": 2.0, "FPC ribbon": 1.0, "holder lead": 3.0,
           "resistor lead": 0.6}
COLOR = dict(housing="#efe6cf", plug="#e6dbbf", crimp="#c8a951", xt30="#f2c94c", usb="#1f1f1f", fpc="#d8a657",
             header="#1c1c1c", solder="#b9bdc2", splice="#202020", shrink="#2b2b2b", resistor="#d9c49c", foam="#efefe8",
             glass="#bfe6f5", reflector="#d6dbe0", microsd="#2a2a2a", ato="#2b6cd4", washer="#c0c6cc", horn="#f4f4f4",
             tblock="#3a7d44", kapton="#c8862a")

# Feetech socket layout in the bottom case STL frame (cables3d: plug back 2.9 mm out of the slot mouth at y -24.1)
PIN_ROW_X = -25.5 + 12.5             # datasheet: pin row 12.5 mm from the idle shaft (shaft at case x -25.5)
SOCKET_Z = {"BUS1": 5.0, "BUS2": -5.0}  # cables3d: BUS1 = socket at case +z, BUS2 at case -z (ports in parallel)
PIN_DZ = {"G": 2.5, "V": 0.0, "D": -2.5}  # G V S from case +z in each socket (datasheet bottom view) [I]
MSX = (10.0, 9.9, 4.4)               # Mini-SPOX housing stand-in: length (mating), width (pin row), thickness


# ------------------------------------------------------------------------------------------------ helpers
def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot_z_to(ax):
    """same as make_viewer_data.py"""
    z = unit(ax)
    t = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(t, z)
    x /= np.linalg.norm(x)
    return np.c_[x, np.cross(z, x), z]


class Rows:
    """BOM_FULL row ids by item name (ids shift when the BOM is regenerated, so match by name)"""
    KEYS = {"housing": r"^Mini-SPOX housing", "crimp": r"^Mini-SPOX crimp terminal", "shrink": r"^Heat shrink pieces",
            "solder": r"^Solder wire", "foam": r"^Foam mounting tape", "xt30": r"^XT30U connector pair",
            "pi": r"^Raspberry Pi Zero 2 W", "pullup": r"^Foot switch pull-up", "ledres": r"^LED resistor",
            "glass": r"^Eye glass disc", "reflector": r"^Projector reflector", "microsd": r"^microSD card",
            "fuse": r"^Fuse, Littelfuse", "amp": r"^I2S amplifier", "sg90": r"^SG90-class antenna servo",
            "kitcable": r"^Servo kit cable", "kapton": r"Kapton|[Pp]olyimide", "washer": r"^M2\.5 flat washer"}

    def __init__(self, path):
        self.rows = list(csv.DictReader(open(path, encoding="utf-8"))) if os.path.exists(path) else []

    def get(self, key):
        if key is None:
            return "", ""
        if key.startswith("cable:"):
            cid = key.split(":", 1)[1]
            for r in self.rows:
                if r["item"].startswith(cid + ":"):
                    return r["id"], r["item"]
            return "", ""
        pat = self.KEYS[key]
        for r in self.rows:
            if re.search(pat, r["item"]):
                return r["id"], r["item"]
        return "", ""


def bom_md_lines(path=os.path.join(LAB, "BOM.md")):
    """BOM.md purchase line id by item name (tables headed '| # | Item |')"""
    out, hdr = {}, None
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("| # | Item"):
            hdr = True
            continue
        if hdr and ln.startswith("|") and not ln.startswith("|---"):
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) > 2:
                out[c[1]] = c[0]
        elif not ln.startswith("|"):
            hdr = None
    return out


def line_of(lines, pat, default=""):
    return next((lid for item, lid in lines.items() if re.search(pat, item)), default)


class Out:
    def __init__(self, rows):
        self.items, self.rows = [], rows

    def add(self, iid, kind, label, rowkey, line, link, center, e_len, e_w, dims, color, source, **kw):
        e_len = unit(e_len)
        e_w = np.asarray(e_w, float)
        e_w = unit(e_w - np.dot(e_w, e_len) * e_len)
        e_h = np.cross(e_len, e_w)
        R = rot_z_to(e_len)
        L, W, H = (float(x) for x in dims)
        wx = abs(R[:, 0] @ e_w) * W + abs(R[:, 0] @ e_h) * H
        hy = abs(R[:, 1] @ e_w) * W + abs(R[:, 1] @ e_h) * H
        rid, ritem = self.rows.get(rowkey)
        it = dict(id=iid, kind=kind, label=label, bom_full_row=rid, bom_full_item=ritem, bom_line=line or "", link=link,
                  center_mm=[round(float(x), 2) for x in center], axis=[round(float(x), 4) for x in e_len],
                  dims_mm=[round(L, 2), round(float(wx), 2), round(float(hy), 2)], color=color, source=source,
                  dims_local_mm=[round(L, 2), round(W, 2), round(H, 2)],
                  rotation_3x3=[[round(float(v), 4) for v in row] for row in np.c_[e_w, e_h, e_len]])
        it.update({k: v for k, v in kw.items() if v is not None})
        self.items.append(it)
        return it


def bundle_od(ods):
    n, d = len(ods), max(ods)
    return d if n == 1 else (2.0 * d if n == 2 else 1.155 * d * np.sqrt(n))


def end_kind(e):
    e = (e or "").lower()
    if "50-37-5033" in e:
        return "molex"
    if "5264 plug" in e:
        return "kit_plug"
    if "xt30" in e:
        return "xt30_cup"
    if e == "splice":
        return "splice"
    if "usb" in e and "plug" in e:
        return "usb_plug"
    if "fpc" in e:
        return "fpc"
    if "screw terminal" in e:
        return "screw_terminal"
    if "bec lead" in e and "solder" in e:
        return "inline_bec"
    if e.startswith("solder") or e == "header pin":
        return "solder"
    return "lead"                       # holder lead, BEC lead, SG90 servo lead, resistor lead, LED lead


# pin -> terminal id in cables3d (same mapping as route_cables.py pin_to_term)
PIN_MAP = [("PACK.MID", "PACK.MID"), ("PACK.", "PACK.LEADS"), ("BMS.B", "BMS.B"), ("BMS.P", "BMS.P"), ("CHG.", "CHG.OUT"),
           ("XT30.F", "XT30.F"), ("XT30.M", "XT30.M"), ("F1.IN", "F1.IN"), ("F1.OUT", "F1.OUT"), ("SW1.VIN", "SW1.VIN"),
           ("SW1.VOUT", "SW1.VOUT"), ("SW1.GND_SW", "SW1.CTL"), ("SW1.SW", "SW1.CTL"), ("SW1.GND", "SW1.GND"),
           ("CTL.", "CTL.LUGS"), ("U1.IN", "U1.IN"), ("U1.OUT", "U1.OUT"), ("U2.H3", "U2.H3"), ("U2.H5", "U2.H5"),
           ("U2.USB", "U2.USB"), ("BNO.", "BNO.JP1"), ("U3.VIN", "U3.IN"), ("U3.GND.1", "U3.IN"), ("U3.VOUT", "U3.OUT"),
           ("U3.GND.2", "U3.OUT"), ("RL.", "LEDL"), ("LEDL.", "LEDL"), ("RR.", "LEDR"), ("LEDR.", "LEDR"),
           ("RP.", "LEDP"), ("LEDP.", "LEDP"), ("SGL.", "SGL"), ("SGR.", "SGR"), ("AMP.SPK", "AMP.SPK"),
           ("AMP.", "AMP.HDR"), ("SPK.", "SPK.TABS"), ("CAM.", "CAM.CSI"), ("FSL1.", "FSL1"), ("FSL2.", "FSL2"),
           ("FSR1.", "FSR1"), ("FSR2.", "FSR2")]


def pin_term(pin):
    m = pin.split(".")
    if m[0].startswith("SV") and m[0][2:].isdigit():
        return "%s.%s" % (m[0], m[1])
    if m[0] == "PI":
        return pin
    for pre, t in PIN_MAP:
        if pin.startswith(pre):
            return t
    return None


# spread of the pads of one grouped terminal: terminal -> (pin order, spacing mm, spread axis in world or a function)
SPREAD = {
    "BMS.B": (["B-", "B1", "B+"], 5.0, (1, 0, 0), "[I] pad spacing not in any drawing in hand"),
    "BMS.P": (["P-", "P+"], 8.0, (1, 0, 0), "[I] pad spacing not in any drawing in hand"),
    "CHG.OUT": (["B+", "B-"], 5.0, (1, 0, 0), "[I] pad labels and spacing not verified (netlist CHG)"),
    "SW1.CTL": (["SW", "GND_SW"], 2.54, (0, 1, 0), "[L] Pololu 2815 0.1 in control holes; which is which [I]"),
    "CTL.LUGS": (["1", "2"], 5.0, "ctl", "[I] lug count and pitch not verified (netlist CTL)"),
    "U3.IN": (["VIN", "GND.1"], 2.54, (0, 1, 0), "[I] pin order on the edge not checked (netlist U3)"),
    "U3.OUT": (["VOUT", "GND.2"], 2.54, (0, 1, 0), "[I] pin order on the edge not checked (netlist U3)"),
    "BNO.JP1": (["VIN", "3VO", "GND", "SDA", "SCL", "RST"], 2.54, (0, 1, 0), SRC["bno"]),
    "AMP.HDR": (["LRC", "BCLK", "DIN", "GAIN", "SD", "GND", "VIN"], 2.54, (0, 1, 0), SRC["amp"]),
    "FSL1": (["COM", "NO", "NC"], 5.0, (0, 1, 0), "[I] Omron SS terminal order and pitch not in hand (stand-in 5.0 mm)"),
    "FSL2": (["COM", "NO", "NC"], 5.0, (0, 1, 0), "[I] Omron SS terminal order and pitch not in hand (stand-in 5.0 mm)"),
    "FSR1": (["COM", "NO", "NC"], 5.0, (0, 1, 0), "[I] Omron SS terminal order and pitch not in hand (stand-in 5.0 mm)"),
    "FSR2": (["COM", "NO", "NC"], 5.0, (0, 1, 0), "[I] Omron SS terminal order and pitch not in hand (stand-in 5.0 mm)"),
    "LEDL": (["A", "K"], 3.0, (0, 0, 1), "[I] LED bead lead spacing not given (BOM E3)"),
    "LEDR": (["A", "K"], 3.0, (0, 0, 1), "[I] LED bead lead spacing not given (BOM E3)"),
    "LEDP": (["A", "K"], 3.0, (0, 0, 1), "[I] LED bead lead spacing not given (BOM E3)"),
    "SPK.TABS": (["+", "-"], 6.0, (1, 0, 0), "[I] tab spacing not checked (netlist SPK)"),
}


# ------------------------------------------------------------------------------------------------ geometry
def eye_seat(s, key):
    """glass seat of an eye print STL: axis centre (y, z) of the 29.6 mm bore and x of the lip face it rests on"""
    i = s.find(key)[0]
    m = s.world_mesh(i)
    lo, hi = m.bounds
    rows = []
    for x in np.arange(lo[0] + 0.02, hi[0], 0.05):
        sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
        if sec is None:
            continue
        P, T = sec.to_2D()
        best = None
        for pg in P.polygons_full:
            for r in pg.interiors:
                c = np.array(r.coords)
                w = c.max(0) - c.min(0)
                if best is None or w.max() > best[0]:
                    cc = (c.max(0) + c.min(0)) / 2.0
                    best = (w.max(), (T @ np.r_[cc, 0, 1])[:3])
        if best:
            rows.append((x, best[0], best[1]))
    big = [r for r in rows if abs(r[1] - 29.6) < 0.15]
    x0 = min(r[0] for r in big)
    prev = max(r[0] for r in rows if r[0] < x0)
    lip = (x0 + prev) / 2.0
    cen = np.mean([r[2] for r in big], 0)
    depth = max(r[0] for r in big) - lip
    return lip, cen[1], cen[2], depth


def reflector_seat(s):
    """aperture face (front of the 8.1 mm ring) and axis of the cone in flash_reflector_interface"""
    i = s.find("flash_reflector_interface")[0]
    m = s.world_mesh(i)
    lo, hi = m.bounds
    rows = []
    for x in np.arange(lo[0] + 0.02, hi[0], 0.05):
        sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
        if sec is None:
            continue
        P, T = sec.to_2D()
        for pg in P.polygons_full:
            for r in pg.interiors:
                c = np.array(r.coords)
                w = (c.max(0) - c.min(0)).max()
                cc = (T @ np.r_[(c.max(0) + c.min(0)) / 2.0, 0, 1])[:3]
                rows.append((x, w, cc))
    ring = [r for r in rows if abs(r[1] - 8.1) < 0.2]
    x_ap = max(r[0] for r in ring) + 0.025
    front = hi[0]
    return x_ap, ring[0][2][1], ring[0][2][2], front


def sd_slot(s):
    """microSD slot body on raspberrypizerow.stl (raised 1.5 mm body at the board end), in the Pi STL frame"""
    pi = s.find("raspberrypizerow")[0]
    V = s.mesh(pi).vertices
    sel = V[(V[:, 1] > 2.9) & (V[:, 1] < 3.1) & (V[:, 0] < -15.0)]
    return sel.min(0), sel.max(0)


def face_gap(s, center, normal, keys=None, skip=("servo_top", "servo_mid", "servo_bottom")):
    """distance from a point along normal to the first printed or CAD part (mm), and that part"""
    best, who = None, None
    o = np.asarray(center, float)
    for i in s.inst:
        if i["key"] in skip or (keys and i["key"] not in keys):
            continue
        m = s.world_mesh(i)
        if np.any(m.bounds[1] < o - 80) or np.any(m.bounds[0] > o + 80):
            continue
        loc, _, _ = m.ray.intersects_location([o], [normal], multiple_hits=False)
        if len(loc):
            d = float(np.linalg.norm(loc[0] - o))
            if best is None or d < best:
                best, who = d, i["key"]
    return best, who


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="print the coverage table only, write nothing")
    a = ap.parse_args()
    t0 = time.time()
    s = Scene()
    rows = Rows(BOMFULL)
    o = Out(rows)
    bl = bom_md_lines()
    L_SOLDER = line_of(bl, r"^Solder wire")
    L_KAPTON = line_of(bl, r"Kapton|[Pp]olyimide")
    L_WASHER = line_of(bl, r"[Ww]asher")
    net = yaml.safe_load(open(NETLIST, encoding="utf-8"))
    cab = {c["id"]: c for c in net["cables"]}
    wires = [w for w in net["wires"] if cab[w["cable"]]["status"] == "active"]
    c3 = json.load(open(CABLES3D)) if os.path.exists(CABLES3D) else {}
    E = {t["id"]: t for t in c3.get("cable_ends", [])}
    seats = {t["id"]: t for t in c3.get("terminals", [])}
    routes = {c["id"]: c for c in c3.get("cables", [])}
    if not E:
        sys.exit("cables3d.json with cable_ends is needed (altaay_lab/cables3d/route_cables.py)")
    P = lambda tid: np.array(E[tid]["p_world0"], float)
    D = lambda tid: unit(E[tid]["dir_world0"])
    LK = lambda tid: E[tid]["link"]
    servo = {sv["id"]: sv for sv in s.servos()}
    pi = s.find("raspberrypizerow")[0]
    Mp = pi["W"]
    ada = s.find("board", "trunk_assembly")[0]
    Ma = ada["W"]
    notes, coverage = [], []

    # what each wire end is
    ends = []                               # (cable, wire, side, pin, kind)
    for w in wires:
        for side, e in zip(("from", "to"), w.get("ends") or []):
            ends.append((w["cable"], w, side, w[side], end_kind(e), e))

    # ---------------------------------------------------------------- 1. servo socket plugs and housings
    def servo_port_frame(sid, bus):
        M = servo[sid]["W"]
        return M, rot(M, (0, 0, 1)), rot(M, (1, 0, 0))

    plug_ends = {}                          # (cable, comp, bus) -> wires
    molex_ends = {}                         # (comp, group) -> [(cable, pin letter, wire)]
    for cid, w, side, pin, kind, e in ends:
        comp = pin.split(".")[0]
        if kind == "kit_plug":
            bus = pin.split(".")[1]
            plug_ends.setdefault((cid, comp, bus), []).append(w)
        elif kind == "molex":
            grp = pin.split(".")[1]
            molex_ends.setdefault((comp, grp), []).append((cid, pin.split(".")[-1], w))
    for (cid, comp, bus), ws in sorted(plug_ends.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        sid = int(comp[2:])
        tid = "%s.%s" % (comp, bus)
        p, d = P(tid), D(tid)
        M, ez, ex = servo_port_frame(sid, bus)
        it = o.add("plug-%s-%s-%s" % (cid, comp, bus), "connector",
                   "Kit cable %s 5264 plug at ID %d %s (%s)" % (cid, sid, bus.replace("BUS", "BUS "), servo[sid]["joint"]),
                   "cable:%s" % cid, "1", LK(tid), p - d * MSX[0] / 2.0, d, ez, MSX, COLOR["plug"],
                   "Position: %s (plug back 2.9 mm out of the slot mouth, UNVERIFIED); socket layout %s. Size: Feetech "
                   "kit cable 5264-3P plug, %s" % (SRC["c3d"], SRC["feetech"], U_MOLEX),
                   cable=cid, end_of=tid, bom_full_rows_also=[rows.get("kitcable")[0]])
        coverage.append((cid, tid, it["id"]))
    for (comp, grp), lst in sorted(molex_ends.items()):
        if comp.startswith("SV"):
            sid = int(comp[2:])
            tid = "%s.%s" % (comp, grp)
            p, d = P(tid), D(tid)
            M, ez, ex = servo_port_frame(sid, grp)
            lab = "Mini-SPOX housing 50-37-5033 at ID %d %s (%s): %s" % (
                sid, grp.replace("BUS", "BUS "), servo[sid]["joint"], ", ".join("%s %s" % (c, l) for c, l, _ in lst))
            it = o.add("msx-%s-%s" % (comp, grp), "connector", lab, "housing", "21", LK(tid), p - d * MSX[0] / 2.0, d, ez, MSX,
                       COLOR["housing"], "Position: %s; socket layout %s. Size: %s" % (SRC["c3d"], SRC["feetech"], U_MOLEX),
                       cables=sorted({c for c, _, _ in lst}), end_of=tid)
            for c, letter, w in lst:
                q = (PIN_ROW_X, -22.0, SOCKET_Z[grp] + PIN_DZ[letter])
                o.add("crimp-%s-%s-%s" % (comp, grp, letter), "connector",
                      "Crimp terminal 08-70-1040, ID %d %s pin %s (%s %s)" % (sid, grp.replace("BUS", "BUS "), letter, c, w["net"]),
                      "crimp", "22", LK(tid), tf(M, q), d, ez, (8.0, 1.6, 1.4), COLOR["crimp"],
                      "Inside msx-%s-%s at the pin: row x %.1f in the case frame, %s. Size UNVERIFIED stand-in 8.0 x 1.6 x "
                      "1.4 mm (Molex drawing not reachable)" % (comp, grp, PIN_ROW_X, SRC["feetech"]), cable=c)
                coverage.append((c, "%s.%s.%s" % (comp, grp, letter), "crimp-%s-%s-%s" % (comp, grp, letter)))
        else:                               # adapter H3 / H5
            tid = "%s.%s" % (comp, grp)
            p, d = P(tid), D(tid)
            ex = np.array([1.0, 0, 0])
            c0 = p - d * MSX[0] / 2.0
            lab = "Mini-SPOX housing 50-37-5033 at adapter %s, D and G only (V empty): %s" % (
                grp, ", ".join(sorted({c for c, _, _ in lst})))
            o.add("msx-%s-%s" % (comp, grp), "connector", lab, "housing", "21", LK(tid), c0, d, ex, MSX, COLOR["housing"],
                  "Position: %s; pin order %s. Size: %s" % (SRC["c3d"], SRC["ws"], U_MOLEX),
                  cables=sorted({c for c, _, _ in lst}), end_of=tid)
            for c, letter, w in lst:
                off = {"D": -2.5, "V": 0.0, "G": 2.5}[letter]
                o.add("crimp-%s-%s-%s" % (comp, grp, letter), "connector",
                      "Crimp terminal 08-70-1040, adapter %s pin %s (%s %s)" % (grp, letter, c, w["net"]), "crimp", "22", LK(tid),
                      c0 + ex * off, d, ex, (8.0, 1.6, 1.4), COLOR["crimp"],
                      "Inside msx-%s-%s, %s. Size UNVERIFIED stand-in 8.0 x 1.6 x 1.4 mm" % (comp, grp, SRC["ws"]), cable=c)
                coverage.append((c, "%s.%s.%s" % (comp, grp, letter), "crimp-%s-%s-%s" % (comp, grp, letter)))

    # ---------------------------------------------------------------- 2. XT30, USB, FPC, header, terminal block
    xs = seats.get("xt30")
    if xs and xs.get("center_mm"):
        c = np.array(xs["center_mm"], float)
        for half, sgn, tid in (("female (pack side)", -1, "XT30.F"), ("male (robot side)", 1, "XT30.M")):
            o.add("conn-%s" % tid.replace(".", "-"), "connector", "XT30U %s" % half, "xt30", "12", xs["link"],
                  c + np.array([0, 0, sgn * 8.0]), (0, 0, 1), (1, 0, 0), (16.0, 10.0, 5.2), COLOR["xt30"],
                  "Seat: cables3d terminals xt30 (%s). Size: %s" % (xs["how"][:160], SRC["xt30"]),
                  replaces_placeholder="xt30", end_of=tid)
        cups = {"XT30.F+": ("P6", -1, 2.5), "XT30.F-": ("P8", -1, -2.5), "XT30.M+": ("P7", 1, 2.5), "XT30.M-": ("P14", 1, -2.5)}
        for pin, (cid, sgn, dx) in cups.items():
            o.add("hs-%s%s" % (pin.replace(".", "-")[:-1], "p" if pin.endswith("+") else "n"), "heat_shrink",
                  "Heat shrink over the XT30U solder cup %s (%s)" % (pin, cid), "shrink", "26", xs["link"],
                  c + np.array([dx, 0, sgn * 16.0]), (0, 0, sgn), (1, 0, 0), (10.0, 4.5, 4.5), COLOR["shrink"],
                  "netlist end 'XT30 solder cup', HARNESS_BUILD 'heat shrink over the cup'; contact spacing 5.0 mm and "
                  "sleeve 10 x 4.5 mm UNVERIFIED stand-ins", cable=cid)
            coverage.append((cid, pin, "conn-%s" % ("XT30-F" if ".F" in pin else "XT30-M")))
    else:
        notes.append("xt30 seat missing in cables3d.json terminals: XT30 halves not written")

    for tid, iid, lab, dims, ew, src in (
            ("PI.USB", "plug-D1-PI-USB", "USB micro-B plug of the D1 cable at the Pi USB (OTG data) port", (20.0, 10.5, 7.0),
             rot(Mp, (1, 0, 0)), SRC["usbm"]),
            ("U2.USB", "plug-D1-U2-USB", "USB-C plug of the D1 cable at the servo adapter", (20.0, 12.4, 6.5),
             (1.0, 0, 0), SRC["usbc"])):
        p, d = P(tid), D(tid)
        o.add(iid, "connector", lab, "cable:D1", "20", LK(tid), p - d * dims[0] / 2.0, d, ew, dims, COLOR["usb"],
              "Position: %s (overmold back). Size: %s" % (SRC["c3d"], src), cable="D1", end_of=tid)
        coverage.append(("D1", tid, iid))
    for tid, iid, lab, w_, ew in (("PI.CSI", "fpc-D12-PI-CSI", "Camera cable 22-pin FPC end in the Pi CSI connector", 11.5,
                                    rot(Mp, (0, 0, 1))),
                                   ("CAM.CSI", "fpc-D12-CAM-CSI", "Camera cable 15-pin FPC end in the Camera Module 3 connector",
                                    16.0, (0, 0, 1.0))):
        p, d = P(tid), D(tid)
        o.add(iid, "connector", lab, "cable:D12", "E7", LK(tid), p - d * 3.0, d, ew, (6.0, w_, 0.3), COLOR["fpc"],
              "Position: %s. Size: %s" % (SRC["c3d"], SRC["fpc"]), cable="D12", end_of=tid)
        coverage.append(("D12", tid, iid))
    o.add("hdr-PI-2x20", "connector", "2 x 20 male header on the Pi Zero 2 W (pre-soldered on the CanaKit fallback, else fitted)",
          "pi", "3", pi["link"], tf(Mp, (0.0, 1.4 + 1.25, -11.5)), rot(Mp, (1, 0, 0)), rot(Mp, (0, 0, 1)), (50.8, 5.08, 2.5),
          COLOR["header"], "Row positions %s; %s. No BOM line buys a header strip if the bare board (Adafruit 5291) is "
          "bought (D7)" % (SRC["pi"], SRC["header"]))
    am = seats.get("amp")
    if am and am.get("center_mm"):
        c = np.array(am["center_mm"], float)
        dd = np.array(am["dims_xyz_mm"], float)
        tb = c + np.array([dd[0] / 2.0 - 3.5, 0.0, dd[2] / 2.0 + 4.25])
        o.add("tb-AMP-SPK", "connector", "Speaker terminal block on the MAX98357A (D11 + and -)", "amp", "E2", am["link"],
              tb, (0, 1, 0), (1, 0, 0), (7.0, 7.0, 8.5), COLOR["tblock"],
              "On the amp seat from cables3d terminals amp, at the AMP.SPK edge. Size: %s" % SRC["tblock"], cable="D11")
        for pin in ("AMP.SPK+", "AMP.SPK-"):
            coverage.append(("D11", pin, "tb-AMP-SPK"))
    else:
        notes.append("amp seat missing in cables3d.json: terminal block, header joints and amp foam pad not written")

    # ---------------------------------------------------------------- 3. solder joints
    joints = {}
    for cid, w, side, pin, kind, e in ends:
        if kind != "solder":
            continue
        joints.setdefault(pin, []).append((cid, e))
    n_solder = 0
    for pin, lst in sorted(joints.items()):
        tid = pin_term(pin)
        if tid not in E:
            notes.append("no cables3d terminal for %s: solder marker skipped" % pin)
            continue
        p, d = P(tid), D(tid)
        cables = sorted({c for c, _ in lst})
        how = SRC["c3d"]
        if tid.startswith("PI."):
            c = p - d * 2.5                 # terminal is 1 mm past the pin tip: marker on the outer 3 mm of the pin
            ew = rot(Mp, (1, 0, 0))
            how += "; on the header pin, 1.5 mm from its tip"
        else:
            c = p - d * 1.0                 # terminals sit about 1 mm off the part surface: blob half on the pad
            ew = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
            sp = SPREAD.get(tid)
            if sp:
                order, pitch, axis, why = sp
                sub = pin.split(".", 1)[1]
                if axis == "ctl":
                    axis = rot(s.find("power_switch")[0]["W"], (1, 0, 0))
                k = order.index(sub) if sub in order else 0
                c = c + unit(axis) * (k - (len(order) - 1) / 2.0) * pitch
                how += "; pad offset %s" % why
        it = o.add("sj-%s" % pin.replace(".", "-").replace("+", "p"), "other",
                   "Solder joint %s (%s)" % (pin, ", ".join(cables)), "solder", L_SOLDER, LK(tid), c, d, ew, (3.0, 1.8, 1.8),
                   COLOR["solder"], how + "; " + SRC["marker"], cables=cables, end_kind=", ".join(sorted({x for _, x in lst})))
        for cc in cables:
            coverage.append((cc, pin, it["id"]))
        n_solder += 1

    # ---------------------------------------------------------------- 4. splices
    od_of = lambda cids_gauges: bundle_od([WIRE_OD.get(g, 1.5) for g in cids_gauges]) + 1.0
    sp_wires = {}
    for cid, w, side, pin, kind, e in ends:
        if kind == "splice":
            sp_wires.setdefault(pin.split(".")[0], []).append((cid, w["gauge"]))

    def splice(name, center, axis, link, how):
        lst = sp_wires.get(name, [])
        od = od_of([g for _, g in lst]) if lst else 4.0
        cables = sorted({c for c, _ in lst})
        it = o.add("splice-%s" % name, "splice", "Splice %s (%s), solder in adhesive heat shrink" % (name, ", ".join(cables)),
                   "shrink", "26", link, center, axis, (1, 0, 0) if abs(unit(axis)[0]) < 0.9 else (0, 1, 0),
                   (20.0, od, od), COLOR["splice"], how + "; " + SRC["splice"], cables=cables, n_wires=len(lst))
        for c in cables:
            coverage.append((c, name, it["id"]))
        return it

    for name in ("VSW", "G", "J5", "JG", "JG20", "JG10", "JG30"):
        splice(name, P(name), D(name), LK(name), SRC["c3d"] + " (%s)" % E[name]["how"][:120])
    splice("JBP", P("JB") + np.array([0, 4.5, 0]), D("JB"), LK("JB"), SRC["c3d"] + " JB, JB+ placed 4.5 mm to +y")
    splice("JBN", P("JB") + np.array([0, -4.5, 0]), D("JB"), LK("JB"), SRC["c3d"] + " JB, JB- placed 4.5 mm to -y")
    pc = next((r for r in json.load(open(PLACEMENTS)) if r["id"] == "power_splice"), None)
    if pc:
        c = np.array(pc["center_mm"], float)
        splice("SPV", c + np.array([0, 0, 2.5]), (1, 0, 0), "trunk_assembly",
               "audit/placements.json power_splice box (-62, 0, 39), SPV in its upper half").update(replaces_placeholder="power_splice")
        splice("SPG", c + np.array([0, 0, -2.5]), (1, 0, 0), "trunk_assembly",
               "audit/placements.json power_splice box, SPG in its lower half").update(replaces_placeholder="power_splice")
    if "Y.SD1" in E:
        y0, yd = P("Y.SD1"), D("Y.SD1")
        how = SRC["c3d"] + " Y.SD1"
    else:                                   # SD1 not routed yet: 25 mm from the H3 plug top toward JG20 (straight line)
        a0 = P("U2.H3")
        yd = unit(P("JG20") - a0)
        y0 = a0 + yd * 25.0
        how = "[L] SD1 not routed in cables3d.json yet: 25 mm from the U2.H3 plug top toward JG20 on a straight line " \
              "(netlist stem 30 mm, 'next to the adapter [I]')"
    side = unit(np.cross(yd, (0, 0, 1))) if abs(yd[2]) < 0.9 else np.array([1.0, 0, 0])
    splice("YD3", y0 + side * 2.5, yd, "trunk_assembly", how + ", YD3 2.5 mm to one side")
    splice("YG3", y0 - side * 2.5, yd, "trunk_assembly", how + ", YG3 2.5 mm to the other side")

    # ---------------------------------------------------------------- 5. resistors and the joints around them
    for tid, rid, ledn, cid in (("LEDL", "R1", "left eye", "D5"), ("LEDR", "R2", "right eye", "D6"), ("LEDP", "R3", "projector", "D7")):
        p, d = P(tid), D(tid)
        o.add("res-%s" % rid, "resistor", "%s 100 ohm 1/4 W, inline at the %s LED (%s)" % (rid, ledn, cid), "ledres", "E3b",
              LK(tid), p + d * (2.0 + 3.15), d, (0, 1, 0), (6.3, 2.4, 2.4), COLOR["resistor"],
              "At the LED back (%s, netlist 'resistor soldered inline at the LED'); %s" % (SRC["c3d"], SRC["resistor"]), cable=cid)
        o.add("hs-%s-LED" % rid, "heat_shrink", "Heat shrink over the %s lead to %s LED anode joint (%s)" % (rid, ledn, cid),
              "shrink", "26", LK(tid), p + d * 1.0, d, (0, 1, 0), (6.0, 3.0, 3.0), COLOR["shrink"],
              "netlist D5 to D7 joint 'resistor lead' to 'LED lead', HARNESS_BUILD 'solder joint covered with heat shrink'; "
              "sleeve 6 x 3 mm UNVERIFIED stand-in", cable=cid)
    p17 = P("PI.17")
    dpin = D("PI.17")
    for rid, other, cid, out in (("R4", "PI.15", "D3", 1.0), ("R5", "PI.13", "D4", 4.0)):
        q = (p17 + P(other)) / 2.0 + dpin * out
        o.add("res-%s" % rid, "resistor", "%s 2.2 kOhm pull-up, leads on Pi pins 17 and %s (%s)" % (rid, other[3:], cid), "pullup",
              "13b", LK("PI.17"), q, rot(Mp, (1, 0, 0)), dpin, (6.3, 2.4, 2.4), COLOR["resistor"],
              "Between the pin tips of 17 and %s (netlist D17 'leads soldered at the header'); body %.0f mm past the tips "
              "so R4 and R5 do not overlap [I]; %s" % (other[3:], out + 1.0, SRC["resistor"]), cable=cid)

    # ---------------------------------------------------------------- 6. other heat shrink
    p, d = P("U1.IN"), D("U1.IN")
    for pol, dz in (("+", 2.5), ("-", -2.5)):
        coverage.append(("P10", "U1.IN" + pol, "hs-P10-BEC-IN%s" % ("p" if pol == "+" else "n")))
        o.add("hs-P10-BEC-IN%s" % ("p" if pol == "+" else "n"), "heat_shrink",
              "Heat shrink over the P10 to BEC input lead %s joint" % pol, "shrink", "26", LK("U1.IN"),
              p + d * 6.0 + np.array([0, 0, dz]), d, (0, 1, 0), (12.0, 4.5, 4.5), COLOR["shrink"],
              "netlist P10 end 'solder to BEC lead'; drawn 6 mm out of the BEC case exit (cables3d U1.IN): the BEC input "
              "lead length is not published, so the real joint sits further along; sleeve 12 x 4.5 mm UNVERIFIED", cable="P10")
    pj = P("JB")
    for k, dy in ((1, 7.5), (2, -7.5)):
        o.add("hs-U1-OUT%dS" % k, "heat_shrink", "Insulation cap on the cut third wire of BEC output lead %d" % k, "shrink", "26",
              LK("JB"), pj + np.array([12.0, dy, 0]), (1, 0, 0), (0, 1, 0), (6.0, 3.0, 3.0), COLOR["shrink"],
              "netlist U1 OUT%dS 'third wire insulated [I]' (P11); placed next to the JB splices [I]" % k, cable="P11")
    if any(w["gauge"] == "SG90 lead + 26 AWG" for w in wires if w["cable"] == "D9"):   # D9 sleeves only while the netlist extends the lead
        # D9: 20 mm of 26 AWG added to each SG90 lead wire near the Pi end
        grp = np.mean([P("PI.32"), P("J5"), P("JG")], 0)
        r9 = routes.get("D9")
        if r9:
            pts = [np.array(q["p"], float) for q in (r9.get("runs") or [r9])[0]["points"]]
            pts_w = []
            for q in (r9.get("runs") or [r9])[0]["points"]:
                T = s.T0[q["link"]]
                pts_w.append(T[:3, :3] @ np.array(q["p"], float) + T[:3, 3])
            pts_w = np.array(pts_w)
            if np.linalg.norm(pts_w[0] - grp) < np.linalg.norm(pts_w[-1] - grp):
                pts_w = pts_w[::-1]
            acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts_w, axis=0), axis=1))]
            tgt = acc[-1] - 20.0
            k = max(1, int(np.searchsorted(acc, tgt)))
            q0 = pts_w[k - 1] + (pts_w[k] - pts_w[k - 1]) * (tgt - acc[k - 1]) / max(acc[k] - acc[k - 1], 1e-6)
            dq = unit(pts_w[k] - pts_w[k - 1])
            how9 = "20 mm from the Pi end along the routed D9 run (cables3d.json)"
        else:
            dq = unit(grp - P("SGR"))
            q0 = grp - dq * 20.0
            how9 = "D9 not routed in cables3d.json yet: 20 mm from the Pi end on the straight line toward the right SG90 lead exit"
        sd9 = unit(np.cross(dq, (0, 0, 1))) if abs(dq[2]) < 0.9 else np.array([1.0, 0, 0])
        for k, wn in enumerate(("SIG", "VCC", "GND")):
            o.add("hs-D9-%s" % wn, "heat_shrink", "Heat shrink over the D9 lead extension joint, right SG90 %s" % wn, "shrink", "26",
                  "head_assembly", q0 + sd9 * (k - 1) * 2.2, dq, sd9, (8.0, 2.0, 2.0), COLOR["shrink"],
                  "netlist D9 'lead 250 mm is 18 mm short: add 20 mm of 26 AWG x3'; %s; sleeve 8 x 2 mm UNVERIFIED" % how9, cable="D9")

    # ---------------------------------------------------------------- 7. foam tape pads
    pl = {r["id"]: r for r in json.load(open(PLACEMENTS))}
    pads = [("bec_pro", pl["bec_pro"]["center_mm"], pl["bec_pro"]["dims_xyz_mm"], 2, -1, "trunk_assembly",
             "MOUNTING.md: foam tape on the 47 x 33 face against the belly floor"),
            ("fuse_holder", pl["fuse_holder"]["center_mm"], pl["fuse_holder"]["dims_xyz_mm"], 0, -1, "trunk_assembly",
             "MOUNTING.md: inner face of the battery bay front wall (measured: battery_pack_lid side, -x)"),
            ("mosfet_switch", pl["mosfet_switch"]["center_mm"], pl["mosfet_switch"]["dims_xyz_mm"], 0, -1, "trunk_assembly",
             "MOUNTING.md: inner face of the battery bay front wall (measured: battery_pack_lid side, -x)"),
            ("usb_slack", pl["usb_slack"]["center_mm"], pl["usb_slack"]["dims_xyz_mm"], 1, 1, "trunk_assembly",
             "MOUNTING.md: belly side wall, left side; cable tie to the coil, foam tape")]
    reg = next((t for t in c3.get("cable_ends", []) if t["id"] == "U3.IN"), None)
    pads.append(("reg_5v", [40.6, 54.4, 182.6], [17.8, 20.3, 8.0], 2, -1, "head_assembly",
                 "MOUNTING.md: head floor below the Pi, foam tape; seat of make_viewer_data.py (head_floor_spot, on the 1.1 mm "
                 "tape since the 2026-11-01 seat fix)"))
    if am and am.get("center_mm"):
        pads.append(("amp", am["center_mm"], am["dims_xyz_mm"], 2, -1, "head_assembly",
                     "MOUNTING.md: head floor, double-sided foam; seat from cables3d terminals amp"))
    fits = {}
    for pid, c, dims, ax, sgn, link, why in pads:
        c, dims = np.array(c, float), np.array(dims, float)
        nrm = np.zeros(3)
        nrm[ax] = sgn
        inplane = [k for k in range(3) if k != ax]
        a_, b_ = sorted(inplane, key=lambda k: -dims[k])
        L, W = dims[a_], min(19.05, dims[b_])
        gap, who = face_gap(s, c + nrm * (dims[ax] / 2.0 - 0.01), nrm)
        left = None if gap is None else round(gap - 1.1, 2)
        # the tape lies on the mounting surface; the part should sit on the tape (fit says how far the seat is off)
        cen = c + nrm * (dims[ax] / 2.0 + (gap if gap is not None and gap < 10.0 else 1.1) - 0.55)
        fits[pid] = dict(gap_box_to_surface_mm=None if gap is None else round(gap, 2), surface=who, after_tape_mm=left)
        e_len = np.eye(3)[a_]
        e_w = np.eye(3)[b_]
        o.add("foam-%s" % pid, "foam_pad", "Foam tape pad under %s" % pid.replace("_", " "), "foam", "29", link, cen, e_len, e_w,
              (L, W, 1.1), COLOR["foam"],
              "%s; %s. Pad drawn on the mounting surface. Fit: part box face to %s %.2f mm, %s after the 1.1 mm tape" % (
                  why, SRC["foam"], who, gap if gap is not None else float("nan"),
                  ("%.2f mm gap left: the seat should move %.2f mm toward the surface" % (left, left)) if left is not None and left >= 0 else
                  ("%.2f mm overlap: the seat should move %.2f mm off the surface" % (-left, -left) if left is not None else "n/a")),
              fit=fits[pid])

    # ---------------------------------------------------------------- 8. discs, reflector, microSD, fuse, washers, horns, kapton
    for key, side in (("left_eye", "left"), ("right_eye", "right")):
        lip, cy, cz, depth = eye_seat(s, key)
        o.add("glass-%s" % side, "disc", "Eye glass disc, %s eye (29.6 x 1.85 mm)" % side, "glass", "E4", "head_assembly",
              (lip + 0.925, cy, cz), (1, 0, 0), (0, 1, 0), (1.85, 29.6, 29.6), COLOR["glass"],
              "%s: lip face at x %.2f, bore %.2f mm deep, axis y %.2f z %.2f (%s.stl in the head frame)" % (
                  SRC["glass"], lip, depth, cy, cz, key.replace("_eye", "_eye")), shape="cylinder")
    x_ap, ry, rz, front = reflector_seat(s)
    o.add("reflector", "disc", "Projector reflector, Aurorad S5 (20 mm x 15 mm envelope)", "reflector", "E5", "head_assembly",
          (x_ap + 7.5, ry, rz), (1, 0, 0), (0, 1, 0), (15.0, 20.0, 20.0), COLOR["reflector"],
          "%s. Aperture face x %.2f, seat front face x %.2f: a 15 mm tall reflector stands %.1f mm proud of the seat; height and "
          "retention on test order 10 (MOUNTING.md)" % (SRC["reflector"], x_ap, front, x_ap + 15.0 - front), shape="cone")
    lo, hi = sd_slot(s)
    sdc = ((hi[0] - 7.5), 1.5 + 0.75, (lo[2] + hi[2]) / 2.0)
    o.add("microsd", "other", "microSD card, SanDisk Ultra 32 GB, in the Pi slot", "microsd", "4", pi["link"], tf(Mp, sdc),
          rot(Mp, (1, 0, 0)), rot(Mp, (0, 0, 1)), (15.0, 11.0, 1.0), COLOR["microsd"],
          "%s: slot body x %.1f..%.1f, z %.1f..%.1f (Pi STL frame); the card stands %.1f mm out of the board end" % (
              SRC["microsd"], lo[0], hi[0], lo[2], hi[2], max(0.0, -32.5 - (hi[0] - 15.0))))
    fh = pl["fuse_holder"]
    o.add("fuse-ATO15", "other", "Fuse, Littelfuse 0287015.PXCN ATO 15 A, in the inline holder", "fuse", "L4", "trunk_assembly",
          fh["center_mm"], (0, 1, 0), (0, 0, 1), (19.1, 18.8, 5.1), COLOR["ato"],
          "Centre of the fuse_holder box (audit/placements.json); %s" % SRC["ato"])
    fz = json.load(open(FASTENERS))
    nw = 0
    for r in fz.get("fasteners", []):
        if not r.get("washer"):
            continue
        if str(r.get("status") or "").startswith(("LEAVE OUT", "NOT FITTED")):
            continue          # D38, D39: a screw left out has no washers either (fasteners.json fits 8 washers under 4 eye screws)
        ax = unit(r["axis_world"])
        seat = np.array(r["seat_world"], float)
        n, te = int(r["washer"].get("n", 1)), float(r["washer"].get("t_each", r["washer"].get("t", 0.5)))
        for k in range(n):
            nw += 1
            o.add("washer-%s-%d" % (r["id"], k + 1), "other", "M2.5 washer %.1f mm, %d of %d under %s (%s into %s)" % (
                      te, k + 1, n, r["id"], r["spec"].split(" +")[0], r.get("into")), "washer", L_WASHER, r["link"],
                  seat - ax * te * (k + 0.5), ax, (0, 1, 0) if abs(ax[1]) < 0.9 else (1, 0, 0), (te, 5.0, 5.0), COLOR["washer"],
                  "fasteners.json %s seat_world and axis_world, washer %d of %d from %.1f to %.1f mm out of the seat; %s" % (
                      r["id"], k + 1, n, te * k, te * (k + 1), SRC["washer"]), shape="cylinder", fastener=r["id"])
    for side in ("left", "right"):
        j = s.joints[side + "_antenna"]
        Tc = s.T0[j["child"]]
        axw = unit(Tc[:3, :3] @ j["axis"])
        sg = min(s.find("sg90"), key=lambda i: np.linalg.norm(i["W"][:3, 3] - Tc[:3, 3]))
        Wg = sg["W"]
        out_ax = rot(Wg, (0, 0, 1))
        o.add("horn-SG90-%s" % side, "other", "SG90 horn (from the SG90 bag), %s antenna" % side, "sg90", "14", "head_assembly",
              tf(Wg, (5.68, 0.0, 30.97 + 1.0)), out_ax, rot(Wg, (1, 0, 0)), (2.0, 7.0, 7.0), COLOR["horn"],
              "On the %s_antenna joint axis (URDF), on top of the SG90 case (sg90.stl local z 30.97); %s" % (side, SRC["sg90horn"]))
    bm = pl.get("bms_tenergy")
    if bm:
        dims = np.array(bm["dims_xyz_mm"], float) + 0.2
        o.add("kapton-BMS", "other", "Kapton tape wrap on the Tenergy BMS", "kapton", L_KAPTON, "trunk_assembly", bm["center_mm"],
              (0, 0, 1), (1, 0, 0), (dims[2], dims[0], dims[1]), COLOR["kapton"], SRC["kapton"], render="translucent")

    # ---------------------------------------------------------------- coverage: every active cable end has a body or a lead
    covered = {}
    for c, end, iid in coverage:
        covered.setdefault(c, []).append(iid)
    leads = []
    for cid, w, side, pin, kind, e in ends:
        if kind in ("lead",):
            leads.append((cid, pin, e))
    per_cable = []
    for c in [x["id"] for x in net["cables"] if x["status"] == "active"]:
        cw = [x for x in ends if x[0] == c]
        drawn = [x for x in cw if x[4] not in ("lead",)]
        miss = []
        for cid, w, side, pin, kind, e in drawn:
            ok = any(iid for (cc, end, iid) in coverage if cc == c and (end == pin or end == pin_term(pin) or
                                                                      (kind == "splice" and end == pin.split(".")[0])))
            if not ok:
                miss.append(pin)
        per_cable.append(dict(cable=c, ends=len(cw), lead_ends=len(cw) - len(drawn), drawn_ends=len(drawn) - len(miss),
                              missing=sorted(set(miss))))
    from collections import Counter
    kinds = Counter(it["kind"] for it in o.items)
    summary = dict(items=len(o.items), by_kind=dict(kinds), solder_joints=n_solder, washers=nw,
                   cables=len(per_cable), cables_all_ends_drawn=sum(1 for r in per_cable if not r["missing"]),
                   cable_ends=sum(r["ends"] for r in per_cable), lead_ends=sum(r["lead_ends"] for r in per_cable),
                   ends_with_body=sum(r["drawn_ends"] for r in per_cable),
                   no_bom_row=sorted({it["id"].split("-")[0] for it in o.items if not it["bom_full_row"]}))
    print(json.dumps(summary, indent=1))
    for r in per_cable:
        if r["missing"]:
            print("MISSING ends", r)
    if notes:
        print("notes:", *notes, sep="\n  ")
    if a.check:
        return
    meta = dict(
        generated_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), script="altaay_lab/blueprint/make_scene_extras.py",
        frame="URDF world at the zero pose, x forward, y left, z up, mm",
        convention="center_mm and axis (long axis, dims_mm[0] along it). dims_mm[1] and dims_mm[2] lie along x and y of "
                   "rot_z_to(axis) as in make_viewer_data.py step 10e. rotation_3x3 columns are the world directions of the "
                   "box width, height and length for dims_local_mm [length, width, height] (exact for every item). shape: "
                   "cylinder or cone where the real part is round (draw a box if not supported). replaces_placeholder: the "
                   "viewer placeholder box this item details (xt30, power_splice). render translucent: wrap or skin.",
        sources=dict(cables3d=c3.get("meta", {}).get("generated_utc", "absent"), netlist=net["meta"]["rev"],
                     fasteners=fz.get("meta", {}).get("generated_by", ""), bom_full=os.path.relpath(BOMFULL, LAB),
                     placements="audit/placements.json"),
        bom_full_rows="ids from bom_full.csv at generation time; ids shift when BOM_FULL is regenerated, so bom_full_item "
                      "gives the row name to match on; empty = no BOM_FULL row",
        summary=summary, notes=notes)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(dict(meta=meta, items=o.items), fh, indent=1)
    json.load(open(tmp))
    os.replace(tmp, OUT)
    json.dump(dict(summary=summary, per_cable=per_cable, foam_fit=fits), open(COVER, "w"), indent=1)
    print("wrote %s (%d items, %.0f kB) and %s in %.1f s" % (OUT, len(o.items), os.path.getsize(OUT) / 1024, COVER,
                                                         time.time() - t0))


if __name__ == "__main__":
    main()
