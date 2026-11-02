#!/usr/bin/env python3
"""Route every active cable of wiring/netlist.yaml in 3D, bound to the URDF links, and write cables3d.json.

Usage: python3 altaay_lab/cables3d/route_cables.py --scratch <folder outside the repo> [--grid-only]
The scratch folder holds the occupancy grid cache (about 45 MB) and nothing else; outputs go to altaay_lab/cables3d/.

Method (details in CABLES_3D.md):
1. Pose robot.urdf at zero (yourdfpy, mm). Collect every visual mesh (print/ STLs for printed parts), the head parts
   that exist only in print/, the boxes of bought parts not in the CAD (audit/placements.json, viewer seats, the
   seats chosen here for the XT30, amp, speaker and LEDs).
2. 1 mm occupancy grid with a distance field (c3d_lib.build). A voxel is solid when its centre is inside a watertight
   part or the part surface crosses it.
3. Terminals: the real connector or pad of every wire end (terminal table in this file, sources in each entry).
4. Each cable is one or more runs (a branch is a run). A run is routed between its two terminals through hand-set
   vias (joint crossings, seats) by a shortest clear path (Dijkstra on free voxels, clearance = cable radius + 1 mm,
   mild preference for lying along surfaces), then string pulled.
5. Every point is bound to the link of the part it rides on: dynamic programming over the kinematic chain between
   the two ends, cost = distance to that link's solids. Where the link changes, the segment is a free span across
   the joint(s) between the two links.
6. Lengths at the zero pose and min/max over the full URDF range of every joint the run crosses (sweep).
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3d_lib as L  # noqa: E402

LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
NETLIST = os.path.join(LAB, "wiring", "netlist.yaml")
PLACEMENTS = os.path.join(LAB, "audit", "placements.json")
OUT_JSON = os.path.join(HERE, "cables3d.json")

# ------------------------------------------------------------------------------------------------ sources
SRC = dict(
    feetech="[I] Feetech STS3215 spec A/0 p.5/7, bottom view: 2 x 5264 3P sockets, pins G V S, row 12.5 mm from the idle "
            "shaft (https://www.mantech.co.za/Datasheets/Products/STS3215-200620A.pdf)",
    case_slot="[L] slot measured on wj-wk00-0124bottomcase_45.stl: 4.5 x 20.0 mm through the bottom case at case "
              "x -13.8..-9.3, z -10.0..10.0, mouth at y -24.1 (case STL frame)",
    pi_draw="[I] Raspberry Pi Zero 2 W mechanical drawing (https://datasheets.raspberrypi.com/rpizero2/"
            "raspberry-pi-zero-2-w-mechanical-drawing.pdf), mapped onto raspberrypizerow.stl [L]: header pin 1 at "
            "x -24.13, rows z -10.23 (odd) and -12.77 (even); USB at x 8.9 on the z +15 edge; CSI on the x +32.5 edge",
    ws_photo="[I] Waveshare photos (https://www.waveshare.com/w/upload/a/a3/Bus_Servo_Adapter%28A%29-A.jpg, "
             "https://www.waveshare.com/w/upload/5/52/Bus_servo_adapter_a.jpg): two vertical 5264 sockets D V G on one "
             "long edge, USB-C, DC+/DC- and the jack on the other",
    bno_brd="[U] Adafruit-BNO055-Breakout-PCB 'Adafruit BNO055.brd' (64c5a38): JP1 6 pins Vin 3Vo GND SDA SCL RST on a "
            "26.67 mm edge, 1.27 mm in",
    viewer="[L] seat computed by altaay_lab/viewer/make_viewer_data.py (run of 2026-11-02 into the scratch folder)",
    placement="[L] altaay_lab/audit/placements.json",
    cad="[U] upstream CAD body (mini_bdx/robots/open_duck_mini_v2, Open_Duck_Mini b23317a)",
    od16="[I] BNTECHGO 16 AWG silicone, outside diameter 3.0 +/- 0.1 mm (https://www.amazon.com/dp/B01MCRY7OT)",
    od20="[I] BNTECHGO 20 AWG silicone, outside diameter 1.8 +/- 0.1 mm (https://www.amazon.com/BNTECHGO-Gauge-Silicone-"
         "Wire-Temperature/dp/B01F8PO5XE)",
    od22="[I] BNTECHGO 22 AWG silicone, outer diameter 1.7 +/- 0.1 mm (https://www.amazon.com/BNTECHGO-Silicone-Spool-"
         "Color-100ft/dp/B09X4KY56S)",
    od26="[I] BNTECHGO 26 AWG silicone, outer diameter 1.5 +/- 0.1 mm (https://www.amazon.com/dp/B08F9CF85N)",
    odusb="[L] BOM.md line 20 (Adafruit 3878, 3.5 mm diameter)",
)
WIRE_OD = {"16 AWG": (3.0, "od16"), "20 AWG": (1.8, "od20"), "22 AWG": (1.7, "od22"), "26 AWG": (1.5, "od26"),
           "USB 2.0 cable": (3.5, "odusb")}
# not published: drawn with these sizes and marked UNVERIFIED
WIRE_OD_UNVERIFIED = {"kit cable": 1.3, "SG90 lead": 1.0, "SG90 lead + 26 AWG": 1.5, "BEC lead": 2.0,
                      "FPC ribbon": 1.0, "holder lead": 3.0, "resistor lead": 0.6}
COLOR = {"red": "#d62728", "black": "#222222", "yellow": "#e6c200", "white": "#f2f2f2", "green": "#2ca02c",
         "blue": "#1f77b4", "orange": "#ff7f0e", "brown": "#8c564b", "kit": "#b8c4cc", "holder lead": "#b22222",
         "black jacket": "#333333", "white ribbon": "#e8e0c8", "none": "#b0b0b0"}

# ------------------------------------------------------------------------------------------------ seats
# boxes (link, centre world mm, dims xyz mm, rotation or None, id) for bought parts that are not in the CAD
VIEWER_SEATS = [   # values of the viewer run, frame urdf_world_mm
    ("head_assembly", (40.6, 54.4, 182.6), (17.8, 20.3, 8.0), None, "reg_5v"),
    ("head_assembly", (99.55, -6.15, 217.89), (11.5, 24.0, 25.0), None, "camera"),
    ("foot_assembly", (-50.76, 89.9, -175.35), (6.4, 19.8, 10.2), None, "foot_switch_l1"),
    ("foot_assembly", (-0.76, 89.9, -175.35), (6.4, 19.8, 10.2), None, "foot_switch_l2"),
    ("foot_assembly_2", (-50.76, -91.3, -175.35), (6.4, 19.8, 10.2), None, "foot_switch_r1"),
    ("foot_assembly_2", (-0.76, -91.3, -175.35), (6.4, 19.8, 10.2), None, "foot_switch_r2"),
]
KEEPOUTS = [   # unmodelled components and plugs, kept solid so no cable is routed through them
    ("trunk_assembly", (-84.5, 0.0, 60.4 + 5.5), (42.0, 33.0, 11.0), None, "adapter_components"),
    ("head_assembly", (36.0, 59.6, 224.5 - 4.25), (51.0, 5.1, 8.5), None, "pi_header"),
]
# seats chosen here against the grid (terminals list of cables3d.json); see TERMINAL_SEATS below
NEW_SEATS = {
    "xt30": dict(link="trunk_assembly", center=(-123.0, 31.0, 30.0), dims=(10.0, 5.2, 32.0),
                 how="[L] battery bay, standing, left of the cell holder as Tnkr places it: nearest fully free 10 x 5.2 x "
                     "32 mm box (0.5 mm margin) to the holder +y face and the cell axis, found on the 1 mm grid by "
                     "cables3d/route_cables.py; female half down (toward the BMS leads), male half up"),
    "amp": None,       # filled by seat_amp() from the floor search
    "speaker": dict(link="head_assembly", center=(28.0, -42.5, 198.0), dims=(36.1, 14.5, 36.1),
                    how="[L] nearest fully free 36.1 x 14.5 x 36.1 mm box to speaker_interface (ring frame, x 2.2..40.8, "
                        "y -74.9..-54.0): the box clears CAD parts only from y -49.75 inward, 4.3 mm behind the "
                        "interface face; the 38.5 x 38.7 x 15 envelope of B8 is not reproduced by this test. Not credible "
                        "as a final seat: check the speaker against the printed stand (B8, test order 7)"),
    "led_1": dict(link="head_assembly", center=(93.5, 40.1, 204.2), dims=(5.0, 8.0, 8.0),
                  how="[L] left eye: behind the left bulb (bulb x 96..98, centre y 40.1, z 204.2 from the print STL in "
                      "the head.stl frame), 5 mm deep box free on the grid; emitter faces +x through the bulb"),
    "led_2": dict(link="head_assembly", center=(93.5, -39.9, 204.2), dims=(5.0, 8.0, 8.0),
                  how="[L] right eye: behind the right bulb (x 96..98, centre y -39.9, z 204.2), box free on the grid"),
    "led_3": dict(link="head_assembly", center=(87.5, 99.19, 209.33), dims=(5.0, 8.0, 8.0),
                  how="[L] projector: in the flash_reflector_interface cone just ahead of the 7.93 mm narrow end "
                      "(bore measured by sections: 7.93 mm at x 84.5, 13.65 at 85.5, 17.2 at 89.5, axis y 99.19 z "
                      "209.33); leads go back through the 7.93 mm aperture and the 3 mm channel of flash_light_module "
                      "(free voxels on the axis x 66..84). An 8 x 8 mm bead fits the cone from x 85.5; a starred 1 W "
                      "LED (20 mm) does not"),
}


# the CAD bms.stl body is replaced by the smaller Tenergy 32175 (placements.json bms_tenergy): its bounding box is
# cleared from the grid and the Tenergy box is put back (nothing else overlaps that box)
CLEAR_BMS = ((-134.3, -28.6, -1.5), (-118.3, -24.8, 39.3))


def base_boxes():
    out = []
    for r in json.load(open(PLACEMENTS)):
        if r.get("center_mm") is None:
            continue
        out.append(("trunk_assembly", tuple(r["center_mm"]), tuple(r["dims_xyz_mm"]), None, r["id"]))
    return out + VIEWER_SEATS + KEEPOUTS


def make_scene():
    s = L.Scene()
    # B7: the board.stl copy in the head marks the Pi footprint, it is not a part (HARDWARE_AUDIT.md B7)
    s.inst = [i for i in s.inst if not (i["key"] == "board" and i["link"] == "head_assembly")]
    for k, i in enumerate(s.inst):
        i["idx"] = k
    return s


def load_grid(s, scratch):
    """CAD-only grid (cached); every box (placements, viewer seats, keep-outs, seats chosen here) is an overlay"""
    cache = os.path.join(scratch, "c3d_grid_cad.npz")
    t = time.time()
    g = L.build(s, [], cache=cache)
    print("grid %s from %s in %.1f s" % (g.shape, cache, time.time() - t), flush=True)
    return g


# ------------------------------------------------------------------------------------------------ terminals
SERVO_ID = {"left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
            "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
            "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33}
# STS3215 socket wire exit in the case STL frame: slot mouth y -24.1, plug back taken 2.9 mm out (UNVERIFIED)
SERVO_PORT = {"BUS1": (-11.55, -27.0, 5.0), "BUS2": (-11.55, -27.0, -5.0)}


def pi_pin_mesh(pin):
    c = (pin - 1) // 2
    return np.array([-24.13 + 2.54 * c, 0.0, (4.77 if pin % 2 else 2.23) - 15.0])


class Terminals(dict):
    def add(self, tid, link, p, d, kind, how, **kw):
        d = np.asarray(d, float)
        self[tid] = dict(id=tid, link=link, p=np.asarray(p, float), dir=d / np.linalg.norm(d), kind=kind, how=how, **kw)


def free_near(g, p, d=None, r=12.0, need=1.0):
    """walk from p along d (0.5 mm steps, never through a solid voxel) to the first point with edt >= need, else the
    point of largest edt on that walk; without d, the nearest voxel with edt >= need within r"""
    p = np.asarray(p, float)
    if d is not None:
        d = np.asarray(d, float)
        best, bv = p, -1.0
        for k in np.arange(0.0, r + 0.01, 0.5):
            q = p + d * k
            I = g.idx(q)[0]
            if not g.inside(I)[0]:
                break
            if g.label[tuple(I)] and k > 1.0:
                break
            v = g.sample(q)[0]
            if v >= need:
                return q
            if v > bv:
                best, bv = q, v
        return best
    I = g.idx(p)[0]
    rr = int(r)
    lo = np.maximum(I - rr, 0)
    sub = g.edt[lo[0]:I[0] + rr + 1, lo[1]:I[1] + rr + 1, lo[2]:I[2] + rr + 1]
    cand = np.argwhere(sub >= need)
    if not len(cand):
        cand = np.argwhere(sub >= sub.max() * 0.999)
    P = g.lo + cand + lo + 0.5
    return P[np.argmin(np.linalg.norm(P - p, axis=1))]


def placement(pid):
    for r in json.load(open(PLACEMENTS)):
        if r["id"] == pid:
            return np.array(r["center_mm"], float), np.array(r["dims_xyz_mm"], float)
    raise KeyError(pid)


def build_terminals(s, g, seats):
    T = Terminals()
    bec_c, bec_d = placement("bec_pro")
    fu_c, fu_d = placement("fuse_holder")
    sw_c, sw_d = placement("mosfet_switch")
    us_c, us_d = placement("usb_slack")
    sp_c, sp_d = placement("power_splice")
    tf = lambda M, p: (M @ np.r_[np.asarray(p, float), 1.0])[:3]
    rot = lambda M, d: M[:3, :3] @ np.asarray(d, float)
    inst = {(i["link"], i["key"]): i for i in s.inst}
    W = lambda i: s.T0[i["link"]] @ i["T"]
    # servos
    for sv in s.servos():
        M = s.T0[sv["link"]] @ sv["T_case_link"]
        sid = SERVO_ID[sv["joint"]]
        for port, q in SERVO_PORT.items():
            T.add("SV%d.%s" % (sid, port), sv["link"], tf(M, q), rot(M, (0, -1, 0)), "Molex 5264-type socket",
                  SRC["feetech"] + "; " + SRC["case_slot"] + "; BUS1 = socket at case +z, BUS2 = socket at case -z "
                  "(ports in parallel); plug back 2.9 mm out of the slot mouth UNVERIFIED (Molex drawing not reachable)",
                  servo=sid, joint=sv["joint"])
    # Raspberry Pi Zero 2 W, components down; wires on the header pin tips (8.5 mm header)
    pi = [i for i in s.inst if i["key"] == "raspberrypizerow"][0]
    Mp = W(pi)
    for pin in (1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15, 16, 17, 18, 20, 22, 32, 33, 35, 40):
        T.add("PI.%d" % pin, pi["link"], tf(Mp, pi_pin_mesh(pin) + np.array([0, 1.4 + 8.5 + 1.0, 0])), rot(Mp, (0, 1, 0)),
              "2x20 header pin", SRC["pi_draw"] + "; wire soldered 1 mm below the tip of an 8.5 mm header")
    T.add("PI.USB", pi["link"], tf(Mp, (8.9, 2.75, 16.25 + 20.0)), rot(Mp, (0, 0, 1)), "micro-USB B, plug overmold 20 mm",
          SRC["pi_draw"] + "; overmold length 20 mm UNVERIFIED (Adafruit 3878 page gives no plug size)")
    T.add("PI.CSI", pi["link"], tf(Mp, (33.4 + 1.0, 2.5, -0.25)), rot(Mp, (1, 0, 0)), "22-pin FPC",
          SRC["pi_draw"] + "; connector on the short edge (mesh)")
    # Waveshare adapter (CAD board.stl): board x 0..42 = world -x, y 0..33 = world -y, top face z 0
    Ma = W(inst[("trunk_assembly", "board")])
    board = lambda u, v, h: tf(Ma, (42.0 - u, v, h))
    T.add("U2.H3", "trunk_assembly", board(22.4, 2.6, 12.0), (0, 0, 1), "vertical 5264 socket, plug top",
          SRC["ws_photo"] + "; photo scaled to 42 x 33 mm; H3 = front socket, socket edge on +y [L] (H3, H5 in parallel)")
    T.add("U2.H5", "trunk_assembly", board(10.4, 2.6, 12.0), (0, 0, 1), "vertical 5264 socket, plug top",
          SRC["ws_photo"] + "; H5 = rear socket [L]")
    T.add("U2.USB", "trunk_assembly", board(32.5, 33.0 + 20.0, 1.6), rot(Ma, (0, 1, 0)), "USB-C, plug overmold 20 mm",
          SRC["ws_photo"] + "; USB-C end toward the neck as MOUNTING.md says; overmold 20 mm UNVERIFIED")
    Mb = W(inst[("trunk_assembly", "bno055")])
    T.add("BNO.JP1", "trunk_assembly", tf(Mb, (8.73, 0.0, -1.0)), (0, 0, -1), "0.1 in header holes, wires from below",
          SRC["bno_brd"] + "; header on the front 27 mm edge [L] (CAD body has no holes; orientation ties to B20). The board "
          "hangs under the trunk_top plate with a 3 mm gap above it (section at y 0), so the wires are soldered from the "
          "underside and leave downward [L]")
    # battery bay (part-level pads; exact pad spots are not in any drawing we hold: marked approximate)
    appr = " Pad spot on the part approximate [L] (no pad drawing in hand); no joint, length set at the bench fit."
    T.add("PACK.LEADS", "trunk_assembly", (-129.6, -10.5, -6.5), (0, 0, -1), "holder leads",
          SRC["cad"] + " holder.stl x -139.6..-119.6, y -20.5..20.5, z -5.5..70.5; leads out of the low end face (its "
          "-y face lies against the 5 mm body_back wall of the BMS slot, so they cannot leave sideways)." + appr)
    T.add("PACK.MID", "trunk_assembly", (-129.6, -10.5, 71.5), (0, 0, 1), "series strap pad",
          SRC["cad"] + " holder.stl; strap on the top end face (the end away from the leads), over the cell at y -10.5."
          + appr)
    T.add("BMS.B", "trunk_assembly", (-126.3, -29.5, 4.0), (0, -1, 0), "pads B- B1 B+",
          SRC["placement"] + " bms_tenergy (-126.3, -26.7, 18.9), 16 x 4.5 x 34 standing; B pads at the low end." + appr)
    T.add("BMS.P", "trunk_assembly", (-126.3, -29.5, 33.0), (0, -1, 0), "pads P- P+",
          SRC["placement"] + " bms_tenergy; P pads at the high end." + appr)
    T.add("CHG.OUT", "trunk_assembly", (-126.3, -32.0, 41.0), (0, -1, 0), "pads B+ B-",
          SRC["cad"] + " usb_c_charger.stl x -135.4..-117.2, y -30.9..-25.7, z 39.2..77.4." + appr)
    xt = seats["xt30"]
    c = np.array(xt["center"])
    T.add("XT30.F", "trunk_assembly", c - [0, 0, 16.0 + 1.0], (0, 0, -1), "XT30U female solder cups", xt["how"])
    T.add("XT30.M", "trunk_assembly", c + [0, 0, 16.0 + 1.0], (0, 0, 1), "XT30U male solder cups", xt["how"])
    T.add("F1.IN", "trunk_assembly", fu_c + [0, fu_d[1] / 2 + 1.0, 0], (0, 1, 0), "holder lead 1 exit",
          SRC["placement"] + " fuse_holder %s, %s, 52 mm edge along y; inline leads at both ends" % (fu_c.tolist(), fu_d.tolist()))
    T.add("F1.OUT", "trunk_assembly", fu_c - [0, fu_d[1] / 2 + 1.0, 0], (0, -1, 0), "holder lead 2 exit",
          SRC["placement"] + " fuse_holder, far end")
    for tid, dy, dz, how in (("SW1.VIN", -10.0, -7.5, "large hole VIN"), ("SW1.VOUT", 0.0, -7.5, "large hole VOUT"),
                             ("SW1.GND", 10.0, -7.5, "large hole GND"), ("SW1.CTL", 0.0, 7.5, "0.1 in SW and GND pads")):
        T.add(tid, "trunk_assembly", sw_c + [sw_d[0] / 2 + 1.05, dy, dz], (1, 0, 0), how,
              SRC["placement"] + " mosfet_switch %s, %s standing, wires on the +x face." % (sw_c.tolist(), sw_d.tolist()) + appr)
    sw = inst[("trunk_assembly", "power_switch")]
    Ms = W(sw)
    T.add("CTL.LUGS", "trunk_assembly", tf(Ms, (0.0, 0.0, -4.0 - 1.0)), rot(Ms, (0, 0, -1)), "2 solder lugs",
          SRC["cad"] + " power_switch.stl (body_back cutout); lugs on the inner end (local -z)." + appr)
    # splices and the servo regulator
    T.add("VSW", "trunk_assembly", free_near(g, sw_c + [8.5, -2.0, -12.5], need=2.0), (1, 0, 0), "solder splice",
          "[L] splice next to the 2815 (netlist: 'next to the 2815'); nearest free point to the 2815 front face")
    T.add("G", "trunk_assembly", free_near(g, sw_c + [8.5, 6.0, -12.5], need=2.0), (1, 0, 0), "solder splice",
          "[L] splice next to the 2815")
    bx = bec_c[0] - bec_d[0] / 2 - 1.5
    T.add("U1.IN", "trunk_assembly", (bx, bec_c[1] - 7.5, bec_c[2]), (-1, 0, 0), "BEC input leads exit",
          SRC["placement"] + " bec_pro %s, %s; leads toward the battery bay (MOUNTING.md). Lead length not published: "
          "the route ends at the BEC case" % (bec_c.tolist(), bec_d.tolist()))
    T.add("U1.OUT", "trunk_assembly", (bx, bec_c[1] + 8.5, bec_c[2]), (-1, 0, 0), "BEC output leads exit",
          SRC["placement"] + " bec_pro; both output leads")
    T.add("JB", "trunk_assembly", free_near(g, (bx - 7.5, bec_c[1] + 8.5, bec_c[2] + 3.0), need=2.0), (1, 0, 0),
          "solder splices JB+ JB-", "[L] where both BEC output leads are joined, 8 mm off the BEC end (lead length not published)")
    T.add("SPV.IN", "trunk_assembly", sp_c - [sp_d[0] / 2 + 1.0, 0, 0], (-1, 0, 0), "power splices, BEC side",
          SRC["placement"] + " power_splice %s, %s" % (sp_c.tolist(), sp_d.tolist()))
    T.add("SP.L", "trunk_assembly", sp_c + [0, sp_d[1] / 2 + 1.0, 0], (0, 1, 0), "power splices, left leg side", SRC["placement"])
    T.add("SP.R", "trunk_assembly", sp_c - [0, sp_d[1] / 2 + 1.0, 0], (0, -1, 0), "power splices, right leg side", SRC["placement"])
    T.add("SP.N", "trunk_assembly", sp_c + [sp_d[0] / 2 + 1.0, 0, 0], (1, 0, 0), "power splices, neck side", SRC["placement"])
    # ground splices JG20, JG10, JG30: placed in main() 20 mm back along the power lead route (netlist tail 20 mm)
    # head: 5 V regulator, splices, LEDs, antennas, amp, speaker, camera
    T.add("U3.IN", "head_assembly", (35.5, 54.4, 187.6), (0, 0, 1), "0.1 in holes VIN GND",
          SRC["viewer"] + " reg_5v (40.6, 54.4, 182.6) on 1.1 mm VHB tape, 17.8 x 20.3 x 8; input pins on the -x half [L]." + appr)
    T.add("U3.OUT", "head_assembly", (45.5, 54.4, 187.6), (0, 0, 1), "0.1 in holes VOUT GND",
          SRC["viewer"] + " reg_5v; output pins on the +x half [L]." + appr)
    T.add("J5", "head_assembly", free_near(g, (57.6, 54.0, 203.0), need=1.5), (0, 0, -1), "solder splice",
          "[L] head 5 V splice 12 mm below header pin 4")
    T.add("JG", "head_assembly", free_near(g, (44.9, 54.0, 203.0), need=1.5), (0, 0, -1), "solder splice",
          "[L] head ground splice 12 mm below header pin 14")
    T.add("HOLE.IN", "head_assembly", (64.5, 81.0, 209.33), (0, -1, 0), "inner face of the head left wall, behind the module",
          "[L] head.stl wall at x 66, z 209.3 spans y 83.2 to 86.4 (exact rays); PROPOSED 4 mm hole through it on y at "
          "(64.5, 84.8, 209.3), 2.5 mm behind the module back face: not in the stock CAD (CAD edit for the lead agent)")
    T.add("HOLE.OUT", "head_assembly", (64.5, 88.5, 209.33), (0, 1, 0), "outer face of the head left wall, behind the module",
          "[L] free space behind flash_light_module (x 66 is behind its back face x 67)")
    T.add("LEDP.BACK", "head_assembly", (64.5, 99.19, 209.33), (-1, 0, 0), "back end of the flash_light_module lead channel",
          "[L] the 4 mm channel on the reflector axis (sections at x 70 and y 99.19) opens at the module back, x 67, "
          "OUTSIDE the head shell (left wall at y 84 to 86 there); no hole through head.stl behind the module")
    for led, tid in (("led_1", "LEDL"), ("led_2", "LEDR"), ("led_3", "LEDP")):
        st = seats[led]
        c = np.array(st["center"])
        T.add(tid, "head_assembly", c - [st["dims"][0] / 2 + 1.0, 0, 0], (-1, 0, 0), "LED leads + inline 100 ohm",
              st["how"] + "; resistor soldered inline at the LED (netlist)")
    for k, key in enumerate(("SGL", "SGR")):
        sg = sorted([i for i in s.inst if i["key"] == "sg90"], key=lambda i: -W(i)[1, 3])[k]
        Mg = W(sg)
        T.add(key, sg["link"], tf(Mg, (-11.5 - 1.0, 0.0, 4.0)), rot(Mg, (-1, 0, 0)), "SG90 lead exit",
              SRC["cad"] + " sg90.stl; lead exit on the end face away from the output shaft, 4 mm above the base: "
              "UNVERIFIED (the CAD body has no lead)")
    am = seats["amp"]
    c = np.array(am["center"])
    T.add("AMP.HDR", "head_assembly", c + [-am["dims"][0] / 2 - 1.0, 0, 0.5], (-1, 0, 0), "0.1 in header holes",
          am["how"] + "; header edge toward the back (Pi side) [L]")
    T.add("AMP.SPK", "head_assembly", c + [am["dims"][0] / 2 + 1.0, 0, 0.5], (1, 0, 0), "speaker terminal block",
          am["how"] + "; terminal block on the opposite edge (Adafruit 3006 layout) [L]")
    sp = seats["speaker"]
    c = np.array(sp["center"])
    T.add("SPK.TABS", "head_assembly", c + [0, sp["dims"][1] / 2 + 1.0, -8.0], (0, 1, 0), "solder tabs on the back",
          sp["how"])
    T.add("CAM.CSI", "head_assembly", (94.3, -19.2, 217.9), (0, -1, 0), "15-pin FPC",
          SRC["viewer"] + " camera box on the 4 head pilots; FPC exits at the board edge opposite the lens row "
          "(Raspberry Pi drawing RP-008153-DS-1 via the viewer note), here world -y")
    for tid, link, c in (("FSL1", "foot_assembly", (-50.76, 89.9, -175.35)), ("FSL2", "foot_assembly", (-0.76, 89.9, -175.35)),
                         ("FSR1", "foot_assembly_2", (-50.76, -91.3, -175.35)), ("FSR2", "foot_assembly_2", (-0.76, -91.3, -175.35))):
        T.add(tid, link, np.array(c) + [0, 0, 5.1 + 3.0], (0, 0, 1), "Omron SS-01 solder terminals",
              SRC["viewer"] + " foot_top slot; terminals up (lever toward foot_bottom), 3 mm terminal length UNVERIFIED")
    return T


def seat_amp(g):
    """amp 19 x 18 x 3 mm flat on the head floor (top z 177.5), 2 mm clear all round, nearest to the speaker stand,
    preferring the stand's -y side (Tnkr: right of the speaker stand); U3 is already solid in the grid"""
    occ = g.label > 0
    S = np.zeros(np.array(occ.shape) + 1, np.int32)
    S[1:, 1:, 1:] = np.cumsum(np.cumsum(np.cumsum(occ, 0, dtype=np.int32), 1), 2)

    def cnt(c, d):
        lo = np.floor(np.asarray(c) - np.asarray(d) / 2 - g.lo + 1e-6).astype(int)
        hi = np.ceil(np.asarray(c) + np.asarray(d) / 2 - g.lo - 1e-6).astype(int)
        a, b = lo, hi
        return int(S[b[0], b[1], b[2]] - S[a[0], b[1], b[2]] - S[b[0], a[1], b[2]] - S[b[0], b[1], a[2]]
                   + S[a[0], a[1], b[2]] + S[a[0], b[1], a[2]] + S[b[0], a[1], a[2]] - S[a[0], a[1], a[2]]), \
            int(np.prod(b - a))
    best = None
    stand = ((-1.1, 50.3), (-74.9, -28.9))
    for x in np.arange(-40, 92, 1.0):
        for y in np.arange(-95, 95, 1.0):
            for d in ((19.0, 18.0), (18.0, 19.0)):
                n, _ = cnt((x, y, 179.0 + 1.75), (d[0] + 4, d[1] + 4, 3.5))   # 179: above the 1 mm surface layer
                if n:
                    continue
                m, tot = cnt((x, y, 176.5), (d[0], d[1], 1.0))
                if m < 0.9 * tot:
                    continue
                dx = max(0.0, stand[0][0] - (x + d[0] / 2), (x - d[0] / 2) - stand[0][1])
                dy = max(0.0, stand[1][0] - (y + d[1] / 2), (y - d[1] / 2) - stand[1][1])
                if dx < 2.0 and dy < 2.0:
                    continue          # not under the speaker or inside the stand frame
                score = np.hypot(dx, dy) + (0.0 if y < -28.9 else 10.0)
                if best is None or score < best[0]:
                    best = (score, x, y, d)
    if best is None:
        return dict(link="head_assembly", center=None, dims=(19.0, 18.0, 3.0),
                    how="no free flat 23 x 22 mm patch on the head floor next to the speaker stand: not credible from the CAD")
    sc, x, y, d = best
    return dict(link="head_assembly", center=(float(x), float(y), 177.5 + 1.1 + 1.5), dims=(d[0], d[1], 3.0),
                how="[L] head floor (head_bot_sheet top z 177.5), flat on foam tape: nearest free 19 x 18 mm patch with "
                    "2 mm clearance and full floor support to the speaker stand, on its -y side (Tnkr: right of the "
                    "speaker stand), %.1f mm from the stand box, on 1.1 mm VHB tape (BOM 29); clear of the D30V30F5 seat" % sc)


# ------------------------------------------------------------------------------------------------ runs
# A run is one physical path. a, b: terminal ids or groups (tuple of terminal ids: the run ends at their centroid,
# each wire adds the distance from the centroid to its own terminal). vias: list of terminal ids or ("pt", link, xyz).
# Corridor vias shared by bundles: the servo port exits (10 mm out) of the chain the bundle follows.
NECK = ["@SV30.BUS1", "@SV31.BUS2", "@SV32.BUS2"]          # trunk -> neck -> yaw servo (cables ride the servo chain)
LEG_L = ["@SV21.BUS2", "@SV22.BUS2", "@SV23.BUS2", "@SV24.BUS2"]     # D3 follows the left leg chain from the hip roll
LEG_R = ["@SV11.BUS2", "@SV12.BUS2", "@SV13.BUS2", "@SV14.BUS2"]     # servo down (the hip yaw sockets face up)
RUNS = [
    # battery bay and belly (trunk_assembly only)
    dict(cable="P1", run="main", a="PACK.LEADS", b="BMS.B"),
    dict(cable="P2", run="main", a="PACK.LEADS", b="BMS.B"),
    dict(cable="P3", run="main", a="PACK.MID", b="BMS.B", near_extra=["trunk_assembly"]),
    dict(cable="P4", run="main", a="BMS.P", b="CHG.OUT"),
    dict(cable="P5", run="main", a="BMS.P", b="CHG.OUT"),
    dict(cable="P6", run="main", a="BMS.P", b="XT30.F"),
    dict(cable="P8", run="main", a="BMS.P", b="XT30.F"),
    dict(cable="P7", run="line", a="XT30.M", b="F1.IN"),
    dict(cable="P7", run="load", a="F1.OUT", b="SW1.VIN"),
    dict(cable="P14", run="main", a="XT30.M", b="G"),
    dict(cable="P9", run="main", a="SW1.VOUT", b="VSW"),
    dict(cable="P16", run="main", a="G", b="SW1.GND"),
    dict(cable="P15", run="main", a="SW1.CTL", b="CTL.LUGS"),
    dict(cable="P10", run="main", a=("VSW", "G"), b="U1.IN"),
    dict(cable="P11", run="leads", a="U1.OUT", b="JB"),
    dict(cable="P11", run="main", a="JB", b="SPV.IN"),
    # split distances below are defaults; main() replaces them from the netlist cut (split_from_netlist)
    dict(cable="SP1", run="main", a="SP.L", b="JG20", split=("JG20", "SP.L", "SV20.BUS2", 20.0)),
    dict(cable="SP1", run="tail", a="JG20", b="SV20.BUS2"),
    dict(cable="SP2", run="main", a="SP.R", b="JG10", split=("JG10", "SP.R", "SV10.BUS2", 20.0)),
    dict(cable="SP2", run="tail", a="JG10", b="SV10.BUS2"),
    dict(cable="SP3", run="main", a="SP.N", b="JG30", split=("JG30", "SP.N", "SV30.BUS2", 20.0)),
    dict(cable="SP3", run="tail", a="JG30", b="SV30.BUS2"),
    dict(cable="SD1", run="stem", a="U2.H3", b="Y.SD1", split=("Y.SD1", "U2.H3", "JG20", -25.0)),
    dict(cable="SD1", run="a", a="Y.SD1", b="JG20"),
    dict(cable="SD1", run="b", a="Y.SD1", b="JG30"),
    dict(cable="SD2", run="main", a="U2.H5", b="JG10"),
    # D23 ankle power feeds along the leg chain cables
    dict(cable="SP4", run="main", a="SP.L", b="SV24.BUS1", vias=LEG_L[:-1]),
    dict(cable="SP5", run="main", a="SP.R", b="SV14.BUS1", vias=LEG_R[:-1]),
    # servo kit cables (one joint each, S12 two)
    dict(cable="S2", run="main", a="SV20.BUS1", b="SV21.BUS2"),
    dict(cable="S3", run="main", a="SV21.BUS1", b="SV22.BUS2"),
    dict(cable="S4", run="main", a="SV22.BUS1", b="SV23.BUS2"),
    dict(cable="S5", run="main", a="SV23.BUS1", b="SV24.BUS2"),
    dict(cable="S7", run="main", a="SV10.BUS1", b="SV11.BUS2"),
    dict(cable="S8", run="main", a="SV11.BUS1", b="SV12.BUS2"),
    dict(cable="S9", run="main", a="SV12.BUS1", b="SV13.BUS2"),
    dict(cable="S10", run="main", a="SV13.BUS1", b="SV14.BUS2"),
    dict(cable="S11", run="main", a="SV30.BUS1", b="SV31.BUS2"),
    dict(cable="S12", run="main", a="SV31.BUS1", b="SV32.BUS2"),
    dict(cable="S13", run="main", a="SV32.BUS1", b="SV33.BUS2"),
    # trunk to head through the neck
    dict(cable="P13", run="main", a=("VSW", "G"), b="U3.IN", vias=NECK),
    dict(cable="D1", run="main", a="U2.USB", b="PI.USB", vias=["@USB_SLACK"] + NECK),
    dict(cable="D2", run="main", a="BNO.JP1", b=("PI.1", "PI.9", "PI.3", "PI.5"), vias=NECK),
    dict(cable="D3", run="main", a=("PI.15", "PI.9"), b="FSL1", vias=NECK[::-1] + LEG_L[:-1]),
    dict(cable="D3", run="jumper", a="FSL1", b="FSL2"),
    dict(cable="D4", run="main", a=("PI.13", "PI.9"), b="FSR1", vias=NECK[::-1] + LEG_R[:-1]),
    dict(cable="D4", run="jumper", a="FSR1", b="FSR2"),
    # head
    dict(cable="P12", run="main", hug=True, a="U3.OUT", b=("PI.2", "PI.6")),
    dict(cable="P17", run="main", hug=True, a=("PI.4", "PI.14"), b=("J5", "JG")),
    dict(cable="D5", run="main", hug=True, a=("PI.18", "PI.20"), b="LEDL"),
    dict(cable="D6", run="main", hug=True, a=("PI.16", "PI.20"), b="LEDR"),
    dict(cable="D7", run="main", a=("PI.22", "PI.20"), b="HOLE.IN", hug=True),
    dict(cable="D7", run="hole", a="HOLE.IN", b="HOLE.OUT", straight=True, through="head (proposed 4 mm hole)"),
    dict(cable="D7", run="outside", a="HOLE.OUT", b="LEDP.BACK", straight=True),
    dict(cable="D7", run="channel", a="LEDP.BACK", b="LEDP", straight=True),
    dict(cable="D8", run="main", hug=True, a="SGL", b=("PI.33", "J5", "JG")),
    dict(cable="D9", run="main", hug=True, a="SGR", b=("PI.32", "J5", "JG")),
    dict(cable="D10", run="main", hug=True, a=("PI.35", "PI.12", "PI.40", "J5", "JG"), b="AMP.HDR"),
    dict(cable="D11", run="main", hug=True, a="AMP.SPK", b="SPK.TABS"),
    dict(cable="D12", run="main", hug=True, a="PI.CSI", b="CAM.CSI"),
]


# ------------------------------------------------------------------------------------------------ helpers
def tree(s):
    par = {}
    for j in s.u.robot.joints:
        par[j.child] = (j.parent, j.name, j.type)
    return par


def chain(par, a, b):
    """links from a to b through the tree, and the revolute joints crossed"""
    up = lambda l: [l] + (up(par[l][0]) if l in par else [])
    A, B = up(a), up(b)
    common = next(l for l in A if l in B)
    path = A[:A.index(common) + 1] + B[:B.index(common)][::-1]
    joints = [par[l][1] for l in A[:A.index(common)]] + [par[l][1] for l in B[:B.index(common)][::-1]]
    return path, [j for j in joints if j in REV]


REV = {}
SPLIT = {}
# head joint ranges the Runtime commands from the gamepad (Open_Duck_Mini_Runtime 376de65,
# mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py lines 15-17); other joints keep the URDF range
RUNTIME = {"head_pitch": (-0.78, 0.3), "head_yaw": (-0.5, 0.5), "head_roll": (-0.5, 0.5)}


class LinkDist:
    """distance from world points (zero pose) to the solids of one link, from the occupied voxels (KD-tree)"""
    def __init__(self, g):
        from scipy.spatial import cKDTree
        self.trees = {}
        lab = g.label
        for k, ln in enumerate(g.links):
            I = np.argwhere(lab == k + 1)
            if len(I):
                self.trees[ln] = cKDTree(g.lo + I + 0.5)

    def __call__(self, ln, P):
        if ln not in self.trees:
            return np.full(len(P), 1e9)
        return self.trees[ln].query(np.atleast_2d(P), k=1)[0]


def resample(P, step):
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        L_ = np.linalg.norm(b - a)
        n = max(1, int(np.ceil(L_ / step)))
        for t in np.linspace(0, 1, n + 1)[1:]:
            out.append(a + (b - a) * t)
    return np.array(out)


def bind(P, links, ld, start_link, end_link):
    """monotone assignment of each point to a link of the chain (DP), first point to start_link, last to end_link"""
    n, m = len(P), len(links)
    C = np.stack([ld(l, P) for l in links], 1)
    C = np.minimum(C, 60.0)
    best = np.full((n, m), np.inf)
    arg = np.zeros((n, m), int)
    best[0, links.index(start_link)] = 0.0
    for i in range(1, n):
        cm = np.minimum.accumulate(best[i - 1])
        am = np.zeros(m, int)
        for k in range(1, m):
            am[k] = am[k - 1] if best[i - 1, am[k - 1]] <= best[i - 1, k] else k
        best[i] = C[i] + cm
        arg[i] = am
    k = links.index(end_link)
    out = [k]
    for i in range(n - 1, 0, -1):
        k = arg[i, k]
        out.append(k)
    return [links[k] for k in out[::-1]]


def simplify(P, B, keep_every=30.0, ang_deg=4.0, g=None, need=0.0):
    """drop collinear points on the same link; keep link changes (both sides) and a point every keep_every mm;
    a point is only dropped when the shortcut keeps the grid clearance `need`"""
    keep = [0]
    acc = 0.0
    for i in range(1, len(P) - 1):
        acc += np.linalg.norm(P[i] - P[i - 1])
        if B[i] != B[i - 1] or B[i] != B[i + 1]:
            keep.append(i)
            acc = 0.0
            continue
        a, b = P[i] - P[keep[-1]], P[i + 1] - P[i]
        if np.linalg.norm(a) > 1e-6 and np.linalg.norm(b) > 1e-6:
            c = np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b)
            short_ok = True
            if g is not None and need > 0:
                a_, b_ = P[keep[-1]], P[i + 1]
                n_ = max(2, int(np.linalg.norm(b_ - a_) / 0.5))
                Q_ = a_ + (b_ - a_) * np.linspace(0, 1, n_)[:, None]
                short_ok = bool(g.sample(Q_[1:-1]).min() >= need) if n_ > 2 else True
            if np.degrees(np.arccos(np.clip(c, -1, 1))) > ang_deg or acc > keep_every or not short_ok:
                keep.append(i)
                acc = 0.0
    keep.append(len(P) - 1)
    return P[keep], [B[k] for k in keep]


def to_link(s, ln, p):
    return (np.linalg.inv(s.T0[ln]) @ np.r_[p, 1.0])[:3]


class Poser:
    """link transforms (mm) for joint configurations, cached"""
    def __init__(self, s):
        self.s = s
        self.cache = {}

    def T(self, cfg):
        key = tuple(sorted((k, round(v, 5)) for k, v in cfg.items() if v))
        if key not in self.cache:
            self.cache[key] = self.s.link_T(cfg)
        return self.cache[key]


def run_length(s, poser, pts, links, cfg):
    T = poser.T(cfg)
    W = [(T[l] @ np.linalg.inv(s.T0[l]) @ np.r_[p, 1.0])[:3] for p, l in zip(pts, links)]
    return float(sum(np.linalg.norm(b - a) for a, b in zip(W[:-1], W[1:])))


def sweep(s, poser, pts, links, par, ranges=None):
    """min and max run length over the joint ranges (default full URDF) of the joints the run crosses; per span"""
    rng = dict(REV)
    if ranges:
        rng.update(ranges)
    zero = run_length(s, poser, pts, links, {})
    spans = []
    for i in range(len(pts) - 1):
        if links[i] != links[i + 1]:
            spans.append((i, chain(par, links[i], links[i + 1])[1]))
    lo_, hi_ = zero, zero
    detail = []
    for i, js in spans:
        if not js:
            continue
        n = {1: 61, 2: 21, 3: 9}.get(len(js), 5)
        grids = np.meshgrid(*[np.linspace(rng[j][0], rng[j][1], n) for j in js], indexing="ij")
        a0 = np.linalg.norm(pts[i + 1] - pts[i])
        vals = []
        for q in zip(*[gg.ravel() for gg in grids]):
            cfg = dict(zip(js, q))
            T = poser.T(cfg)
            pa = (T[links[i]] @ np.linalg.inv(s.T0[links[i]]) @ np.r_[pts[i], 1.0])[:3]
            pb = (T[links[i + 1]] @ np.linalg.inv(s.T0[links[i + 1]]) @ np.r_[pts[i + 1], 1.0])[:3]
            vals.append(np.linalg.norm(pb - pa))
        vals = np.array(vals)
        lo_ += vals.min() - a0
        hi_ += vals.max() - a0
        k = int(np.argmax(vals))
        detail.append(dict(span=[i, i + 1], joints=js, zero_mm=round(float(a0), 1), min_mm=round(float(vals.min()), 1),
                           max_mm=round(float(vals.max()), 1),
                           at_max={j: round(float(g_.ravel()[k]), 3) for j, g_ in zip(js, grids)}))
    return zero, lo_, hi_, detail


def write_json_atomic(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, separators=(",", ":"))
    json.load(open(tmp))
    os.replace(tmp, path)


# ------------------------------------------------------------------------------------------------ pins -> terminals
PIN_MAP = [("PACK.MID", "PACK.MID"), ("PACK.", "PACK.LEADS"), ("BMS.B", "BMS.B"), ("BMS.P", "BMS.P"), ("CHG.", "CHG.OUT"),
           ("XT30.F", "XT30.F"), ("XT30.M", "XT30.M"), ("F1.IN", "F1.IN"), ("F1.OUT", "F1.OUT"), ("SW1.VIN", "SW1.VIN"),
           ("SW1.VOUT", "SW1.VOUT"), ("SW1.GND_SW", "SW1.CTL"), ("SW1.SW", "SW1.CTL"), ("SW1.GND", "SW1.GND"),
           ("CTL.", "CTL.LUGS"), ("VSW.", "VSW"), ("G.S", "G"), ("U1.IN", "U1.IN"), ("U1.OUT", "U1.OUT"), ("JBP.", "JB"),
           ("JBN.", "JB"), ("JG20.", "JG20"), ("JG10.", "JG10"), ("JG30.", "JG30"), ("YD3.", "Y.SD1"), ("YG3.", "Y.SD1"),
           ("U2.H3", "U2.H3"), ("U2.H5", "U2.H5"), ("U2.USB", "U2.USB"), ("BNO.", "BNO.JP1"), ("U3.VIN", "U3.IN"),
           ("U3.GND.1", "U3.IN"), ("U3.VOUT", "U3.OUT"), ("U3.GND.2", "U3.OUT"), ("J5.", "J5"), ("JG.", "JG"),
           ("RL.", "LEDL"), ("LEDL.", "LEDL"), ("RR.", "LEDR"), ("LEDR.", "LEDR"), ("RP.", "LEDP"), ("LEDP.", "LEDP"),
           ("SGL.", "SGL"), ("SGR.", "SGR"), ("AMP.SPK", "AMP.SPK"), ("AMP.", "AMP.HDR"), ("SPK.", "SPK.TABS"),
           ("CAM.", "CAM.CSI"), ("FSL1.", "FSL1"), ("FSL2.", "FSL2"), ("FSR1.", "FSR1"), ("FSR2.", "FSR2")]
SPLICE_ALIAS = {"P11": "SPV.IN", "SP1": "SP.L", "SP2": "SP.R", "SP3": "SP.N", "SP4": "SP.L", "SP5": "SP.R"}
# where a splice sits along a crimped lead: the cut minus the part inside the terminal and half the lap splice
TERM_IN = 3.5     # mm of the cut inside the 08-70-1040 crimp section (Molex 5263 catalog drawing B-101: 3.50 of 7.00 mm)
HALF_LAP = 3.0    # mm, half of a 6 mm lap splice (NASA-STD-8739.4A 19.4.1 c: 3 to 6 wire diameters; 22 AWG OD 1.7 mm)
SPLIT_WIRE = {"JG20": ("JG20.S", "SV20.BUS2.G"), "JG10": ("JG10.S", "SV10.BUS2.G"), "JG30": ("JG30.S", "SV30.BUS2.G"),
              "Y.SD1": ("U2.H3.D", "YD3.S")}


def split_from_netlist(wires):
    """splice id -> distance along the route from the crimped end (cut - TERM_IN - HALF_LAP), from the netlist cuts"""
    out = {}
    for tid, (a, b) in SPLIT_WIRE.items():
        w = [x for x in wires if {x["from"], x["to"]} == {a, b}]
        if w and w[0].get("cut_mm"):
            out[tid] = float(w[0]["cut_mm"]) - TERM_IN - HALF_LAP
    return out

# D23 (altaay_lab/sim/POWER_FIX.md): second power feed to each ankle servo. Used only until the lead adds the records
# to wiring/netlist.yaml (then the netlist version wins). cut_mm here is the power agent's estimate; the routed value
# is proposed in CABLES_3D.md.
D23_CABLES = [
    {"id": "SP4", "status": "active", "desc": "power pair SPV and SPG to ID 24 BUS 1 (V and G), left leg (D23)",
     "regions": ["belly", "trunk_bottom", "left_leg"], "joints": ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee"],
     "polyline_mm": None, "rule_mm": None, "source": "[L] D23", "note": "provisional record from cables3d (D23)"},
    {"id": "SP5", "status": "active", "desc": "power pair SPV and SPG to ID 14 BUS 1 (V and G), right leg (D23)",
     "regions": ["belly", "trunk_bottom", "right_leg"], "joints": ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee"],
     "polyline_mm": None, "rule_mm": None, "source": "[L] D23", "note": "provisional record from cables3d (D23)"},
]
D23_WIRES = [
    {"cable": cab, "from": frm, "to": to, "net": net, "gauge": "22 AWG", "color": col, "cut_mm": 545, "i_mean_a": None,
     "i_peak_a": None, "ends": ["splice", "Molex 50-37-5033 housing (DATA position empty) + 08-70-1040 crimp"],
     "source": "[L] D23; cut 545 = power agent estimate"}
    for cab, sv in (("SP4", "SV24"), ("SP5", "SV14"))
    for frm, to, net, col in (("SPV.S", sv + ".BUS1.V", "SERVO_7V2", "red"), ("SPG.S", sv + ".BUS1.G", "GND", "black"))
]


def pin_to_term(pin, cable):
    if pin.startswith(("SPV.", "SPG.")):
        return SPLICE_ALIAS[cable]
    m = pin.split(".")
    if m[0].startswith("SV") and m[0][2:].isdigit():
        return "%s.%s" % (m[0], m[1])
    if m[0] == "PI":
        return pin
    for pre, t in PIN_MAP:
        if pin.startswith(pre):
            return t
    return None


def bundle_od(ods):
    """bundle diameter estimate for n round conductors (hexagonal packing approximation) [L]"""
    n = len(ods)
    d = max(ods)
    return d if n == 1 else (2.0 * d if n == 2 else 1.155 * d * np.sqrt(n))


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", required=True, help="folder outside the repo for the grid cache")
    ap.add_argument("--grid-only", action="store_true")
    ap.add_argument("--only", default="", help="comma list of cable ids (debug)")
    a = ap.parse_args()
    scratch = os.path.abspath(a.scratch)
    if os.path.commonpath([scratch, REPO]) == REPO:
        sys.exit("scratch folder must be outside the repo")
    os.makedirs(scratch, exist_ok=True)
    t0 = time.time()
    s = make_scene()
    for jn, j in s.joints.items():
        REV[jn] = (j["lo"], j["hi"])
    g0 = load_grid(s, scratch)
    if a.grid_only:
        return
    seats = dict(NEW_SEATS)
    boxes = [(v["link"], tuple(v["center"]), tuple(v["dims"]), None, k) for k, v in seats.items() if v and v.get("center")]
    boxes += base_boxes()
    g1 = g0.overlay(boxes, clear=[CLEAR_BMS])
    seats["amp"] = seat_amp(g1)            # after the speaker, LEDs and XT30 are solid
    am = seats["amp"]
    g = g1.overlay([(am["link"], tuple(am["center"]), tuple(am["dims"]), None, "amp")]) if am.get("center") else g1
    print("seats placed, grid overlay done %.1f s" % (time.time() - t0), flush=True)
    T = build_terminals(s, g, seats)
    # extra vias
    us_c, us_d = placement("usb_slack")
    T.add("USB_SLACK", "trunk_assembly", us_c - [0, us_d[1] / 2 + 1.0, 0], (0, -1, 0), "coil of the spare USB length",
          SRC["placement"] + " usb_slack %s, %s; cable enters and leaves at the -y face" % (us_c.tolist(), us_d.tolist()))
    net = yaml.safe_load(open(NETLIST))
    ids = {c_["id"] for c_ in net["cables"]}
    for rec in D23_CABLES:
        if rec["id"] not in ids:
            net["cables"].append(dict(rec))
            net["wires"] += [dict(w_) for w_ in D23_WIRES if w_["cable"] == rec["id"]]
            print("D23: %s not in the netlist yet, provisional record used" % rec["id"])
    cabrec = {c["id"]: c for c in net["cables"]}
    wires = [w for w in net["wires"] if cabrec[w["cable"]]["status"] == "active"]
    SPLIT.update(split_from_netlist(wires))
    print("splice positions from the netlist cuts (mm along the route from the crimped end): %s" % SPLIT, flush=True)
    par = tree(s)
    ld = LinkDist(g)
    poser = Poser(s)
    lab = {ln: k + 1 for k, ln in enumerate(g.links)}
    only = set(x for x in a.only.split(",") if x)

    def ref(x):
        """terminal id, group tuple or @via -> (point, link, dir, members)"""
        if isinstance(x, tuple):
            P = np.array([T[m]["p"] for m in x])
            return P.mean(0), T[x[0]]["link"], T[x[0]]["dir"], list(x)
        if x.startswith("@"):
            t = T[x[1:]]
            q = free_near(g, t["p"] + 1.0 * t["dir"], d=t["dir"], r=12.0, need=2.5) if x[1:] != "USB_SLACK" else t["p"]
            return q, t["link"], t["dir"], []
        t = T[x]
        return t["p"], t["link"], t["dir"], [x]

    routes = {}
    runs_out = []
    tight = []
    for R in RUNS:
        if only and R["cable"] not in only:
            continue
        cid = R["cable"]
        cw = [w for w in wires if w["cable"] == cid and w["gauge"] != "resistor lead"]
        ods = []
        for w in cw:
            od = WIRE_OD.get(w["gauge"], (WIRE_OD_UNVERIFIED.get(w["gauge"], 1.5), None))[0]
            ods.append(od)
        # conductors in this run: the wires whose terminal path uses it (resolved later); size from all for now
        n_c = {"stem": 2, "a": 2, "b": 2, "tail": 3, "leads": 4, "jumper": 1, "line": 1, "load": 1}.get(R["run"], len(cw))
        od = bundle_od((ods or [1.5])[:max(1, n_c)])
        clr = od / 2.0 + 1.0          # 1 mm grid: voxel-centre distance error up to 0.87 mm, so the true gap stays >= radius
        if R.get("split"):
            # place a splice on the route between two terminals: (new id, from, to, distance); distance > 0 is
            # measured back from `to`, < 0 forward from `from`
            tid, fa, fb, dist = R["split"]
            if tid in SPLIT:
                dist = SPLIT[tid] if dist > 0 else -SPLIT[tid]
            pa_, la_, da_, _ = ref(fa)
            pb_, lb_, db_, _ = ref(fb)
            u0 = free_near(g, pa_ + 1.0 * da_, d=da_, r=12.0, need=clr)
            v0 = free_near(g, pb_ + 1.0 * db_, d=db_, r=12.0, need=clr)
            P = None
            for c_ in (clr, max(0.8, clr - 0.7), 0.6):
                P = L.route(g, u0, v0, c_, hulls=[g.trunk_hull], free_radius=10.0)
                if P is not None:
                    break
            if P is None:
                P = np.vstack([u0, v0])
                print("WARN split route %s failed, straight" % tid)
            Pr = resample(np.vstack([pa_, P, pb_]), 1.0)
            acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pr, axis=0), axis=1))]
            k = int(np.searchsorted(acc, acc[-1] - dist)) if dist > 0 else int(np.searchsorted(acc, -dist))
            k = min(max(k, 1), len(Pr) - 2)
            q = Pr[k]
            T.add(tid, la_ if dist < 0 else lb_, q, (Pr[k + 1] - Pr[k - 1]) / np.linalg.norm(Pr[k + 1] - Pr[k - 1]),
                  "solder splice", "[L] splice centre %.1f mm along the route %s from %s (netlist cut minus %.1f mm in the "
                  "terminal and half the lap splice)" % (abs(dist), "back" if dist > 0 else "forward", fb if dist > 0 else fa,
                                                          TERM_IN + HALF_LAP))
        pa, la, da, ma = ref(R["a"])
        pb, lb, db, mb = ref(R["b"])
        vias = [ref(v) for v in R.get("vias", [])]
        key = (R["a"] if isinstance(R["a"], str) else tuple(R["a"]), R["b"] if isinstance(R["b"], str) else tuple(R["b"]),
               tuple(R.get("vias", [])))
        # chain of links through the vias
        stops = [la] + [v[1] for v in vias] + [lb]
        links = [stops[0]]
        for u, v in zip(stops[:-1], stops[1:]):
            links += chain(par, u, v)[0][1:]
        cl = []
        for l_ in links:
            if not cl or cl[-1] != l_:
                cl.append(l_)
        hulls = ([g.trunk_hull] if "trunk_assembly" in cl else []) + ([g.head_hull] if "head_assembly" in cl else [])
        near = [lab[l_] for l_ in cl if l_ not in ("trunk_assembly", "head_assembly")] + [lab[l_] for l_ in R.get("near_extra", [])]
        if R.get("straight"):
            A0, B0 = pa, pb
        else:
            A0 = free_near(g, pa + 1.0 * da, d=da, r=12.0, need=clr) if not (isinstance(R["a"], str) and R["a"].startswith("@")) else pa
            B0 = free_near(g, pb + 1.0 * db, d=db, r=12.0, need=clr)
        pts_chain = [A0] + [v[0] for v in vias] + [B0]
        P_all = [pa]
        ok = True
        for u, v in zip(pts_chain[:-1], pts_chain[1:]):
            if key in routes:
                break
            if R.get("straight"):
                P_all += [u, v]
                continue
            wall = (0.5, 6.0, 2.5) if R.get("hug") else (3.0, 12.0, 0.6)
            seg = L.route(g, u, v, clr, hulls=hulls, near_labels=near, free_radius=3.0, wall=wall)
            if seg is None:
                seg = L.route(g, u, v, clr, hulls=hulls, near_labels=near, near_mm=24.0, free_radius=6.0, wall=wall)
            if seg is None:
                seg = L.route(g, u, v, max(0.8, od / 2.0 + 0.3), hulls=hulls, near_labels=near, near_mm=24.0,
                              free_radius=6.0, wall=wall)
                if seg is not None:
                    tight.append("%s.%s" % (cid, R["run"]))
            if seg is None:
                seg = L.route(g, u, v, 0.6, hulls=hulls, near_labels=near, near_mm=30.0, free_radius=12.0)
                if seg is not None:
                    tight.append("%s.%s" % (cid, R["run"]))
            if seg is None:
                print("WARN no route %s.%s between %s and %s" % (cid, R["run"], np.round(u, 1), np.round(v, 1)), flush=True)
                seg = np.vstack([u, v])
                ok = False
            P_all += list(seg) if np.linalg.norm(seg[0] - P_all[-1]) > 1e-6 else list(seg[1:])
        if key in routes:
            P_all, ok = routes[key]
        else:
            P_all.append(pb)
            P_all = np.array(P_all)
            routes[key] = (P_all, ok)
        # bind
        Pr = resample(P_all, 3.0)
        B = bind(Pr, cl, ld, la, lb)
        Ps, Bs = simplify(Pr, B, g=g, need=max(0.5, clr - 0.5)) if not R.get("straight") else simplify(Pr, B)
        z0, mn, mx, spans = sweep(s, poser, Ps, Bs, par)
        _, mn_rt, mx_rt, _ = sweep(s, poser, Ps, Bs, par, RUNTIME)
        joints = []
        for sp in spans:
            joints += [j for j in sp["joints"] if j not in joints]
        runs_out.append(dict(cable=cid, run=R["run"], a=R["a"], b=R["b"], members_a=ma, members_b=mb,
                             d_mm=round(float(od), 2), clearance_mm=round(clr, 2), routed=ok,
                             tight=("%s.%s" % (cid, R["run"])) in tight, through=R.get("through"),
                             points=[dict(link=l_, p=[round(float(x), 2) for x in to_link(s, l_, p)],
                                          world0=[round(float(x), 2) for x in p]) for p, l_ in zip(Ps, Bs)],
                             length_zero_mm=round(z0, 1), length_min_mm=round(mn, 1), length_max_mm=round(mx, 1),
                             length_max_runtime_mm=round(mx_rt, 1), joints=joints, spans=spans))
        print("%-4s %-7s pts %3d  L0 %6.1f  min %6.1f  max %6.1f  joints %s %s" % (
            cid, R["run"], len(Ps), z0, mn, mx, joints, "" if ok else "UNROUTED"), flush=True)
    # duplicate tails for the data leads (same bundle as the power tails)
    for cid, tail_src, jg in (("SD1", "SP1", "JG20"), ("SD1", "SP3", "JG30"), ("SD2", "SP2", "JG10")):
        src_r = [r for r in runs_out if r["cable"] == tail_src and r["run"] == "tail"]
        if src_r and (not only or cid in only):
            r2 = dict(src_r[0])
            r2.update(cable=cid, run="tail_" + jg, note="same bundle as %s tail" % tail_src)
            runs_out.append(r2)
    out = assemble(s, T, seats, net, wires, runs_out)
    dest = OUT_JSON if not only else os.path.join(scratch, "cables3d_partial.json")   # debug runs never touch the repo file
    write_json_atomic(out, dest)
    print("wrote %s (%.0f kB) in %.1f s; tight clearance runs: %s" % (dest, os.path.getsize(dest) / 1024, time.time() - t0, tight))


def wire_path(runs, ft, tt):
    """runs (list) as edges between endpoint nodes; group members attach to their endpoint. BFS ft -> tt."""
    def nodes_of(r, side):
        x = r[side]
        mem = r["members_" + side]
        key = x if isinstance(x, str) else "+".join(x)
        return key, mem
    adj = {}
    for k, r in enumerate(runs):
        ka, ma = nodes_of(r, "a")
        kb, mb = nodes_of(r, "b")
        adj.setdefault(ka, []).append((kb, k))
        adj.setdefault(kb, []).append((ka, k))
    starts = [nodes_of(r, sd)[0] for r in runs for sd in ("a", "b") if ft == nodes_of(r, sd)[0] or ft in nodes_of(r, sd)[1]]
    goals = {nodes_of(r, sd)[0] for r in runs for sd in ("a", "b") if tt == nodes_of(r, sd)[0] or tt in nodes_of(r, sd)[1]}
    from collections import deque
    for st in starts:
        dq, seen = deque([(st, [])]), {st}
        while dq:
            n, path = dq.popleft()
            if n in goals and path:
                return st, n, path
            for m, k in adj.get(n, []):
                if m not in seen:
                    seen.add(m)
                    dq.append((m, path + [k]))
    return None


def assemble(s, T, seats, net, wires, runs_out):
    cab = {c["id"]: c for c in net["cables"]}
    cables = []
    for cid in [c["id"] for c in net["cables"] if c["status"] == "active"]:
        runs = [r for r in runs_out if r["cable"] == cid]
        if not runs:
            continue
        cw = [w for w in wires if w["cable"] == cid]
        wout = []
        for w in cw:
            rec = dict(**{"from": w["from"]}, to=w["to"], net=w["net"], gauge=w["gauge"], color=w["color"],
                       cut_mm=w["cut_mm"], branch=w.get("branch"))
            if w["gauge"] == "resistor lead" or w.get("cut_mm") == 0:
                rec.update(runs=[], length_zero_mm=0.0, length_min_mm=0.0, length_max_mm=0.0,
                           note="resistor lead or direct joint, no wire")
                wout.append(rec)
                continue
            od, srck = WIRE_OD.get(w["gauge"], (WIRE_OD_UNVERIFIED.get(w["gauge"]), None))
            rec["od_mm"] = od
            rec["od_source"] = SRC[srck] if srck else "UNVERIFIED (not published)"
            ft, tt = pin_to_term(w["from"], cid), pin_to_term(w["to"], cid)
            wp = wire_path(runs, ft, tt) if ft and tt else None
            if wp is None:
                rec.update(runs=[], note="no run path found for %s -> %s" % (ft, tt))
                wout.append(rec)
                continue
            st, en, path = wp
            off = 0.0
            for term, node in ((ft, st), (tt, en)):
                if "+" in node and term in T:
                    cen = np.mean([T[m]["p"] for m in node.split("+")], 0)
                    off += float(np.linalg.norm(T[term]["p"] - cen))
            rec["runs"] = [runs[k]["run"] for k in path]
            for key in ("length_zero_mm", "length_min_mm", "length_max_mm", "length_max_runtime_mm"):
                rec[key] = round(sum(runs[k].get(key, runs[k]["length_max_mm"]) for k in path) + off, 1)
            rec["pin_offset_mm"] = round(off, 1)
            wout.append(rec)
        main = max(runs, key=lambda r: r["length_zero_mm"]) if not any(r["run"] == "main" for r in runs) else \
            [r for r in runs if r["run"] == "main"][0]
        live = [w for w in wout if w.get("runs")]
        worst = max(live, key=lambda w: w["length_max_mm"]) if live else None
        frm = "/".join(dict.fromkeys(w["from"] for w in cw if w["gauge"] != "resistor lead"))
        to = "/".join(dict.fromkeys(w["to"] for w in cw if w["gauge"] != "resistor lead"))
        cols = [COLOR.get(w["color"], "#888888") for w in cw if w["gauge"] != "resistor lead"]
        cables.append(dict(
            id=cid, desc=cab[cid]["desc"], **{"from": frm}, to=to,
            gauge=", ".join(dict.fromkeys(w["gauge"] for w in cw)),
            color=cols[0] if cols else "#888888", colors=cols,
            d_mm=main["d_mm"], wires_n=len(live),
            cut_mm=worst["cut_mm"] if worst else None,
            length_zero_mm=worst["length_zero_mm"] if worst else main["length_zero_mm"],
            length_min_mm=worst["length_min_mm"] if worst else main["length_min_mm"],
            length_max_mm=worst["length_max_mm"] if worst else main["length_max_mm"],
            joints=sorted({j for r in runs for j in r["joints"]}),
            points=[dict(link=p["link"], p=p["p"]) for p in main["points"]],
            runs=[dict(name=r["run"], **{"from": r["a"] if isinstance(r["a"], str) else "+".join(r["a"])},
                       to=r["b"] if isinstance(r["b"], str) else "+".join(r["b"]),
                       d_mm=r["d_mm"], points=[dict(link=p["link"], p=p["p"]) for p in r["points"]],
                       length_zero_mm=r["length_zero_mm"], length_min_mm=r["length_min_mm"],
                       length_max_mm=r["length_max_mm"], length_max_runtime_mm=r.get("length_max_runtime_mm"),
                       joints=r["joints"], spans=r["spans"], routed=r["routed"], through=r.get("through"))
                  for r in runs],
            wires=wout, check="pending", seats=[], note=cab[cid].get("note", "")))
    term_out = []
    for k in ("xt30", "amp", "speaker", "led_1", "led_2", "led_3"):
        v = seats[k]
        term_out.append(dict(id=k, center_mm=[round(float(x), 2) for x in v["center"]] if v.get("center") else None,
                             dims_xyz_mm=[float(x) for x in v["dims"]], link=v["link"], how=v["how"]))
    ends = [dict(id=t["id"], link=t["link"], p_world0=[round(float(x), 2) for x in t["p"]],
                 p=[round(float(x), 2) for x in to_link(s, t["link"], t["p"])],
                 dir_world0=[round(float(x), 3) for x in t["dir"]], kind=t["kind"], how=t["how"]) for t in T.values()]
    return dict(
        meta=dict(script="altaay_lab/cables3d/route_cables.py", generated_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                  units="mm", frame="points: {link, p} with p in the URDF link frame (yourdfpy link transform, metres x1000) "
                  "at the zero pose; world0 = URDF world at the zero pose (x forward, y left, z up)",
                  netlist="altaay_lab/wiring/netlist.yaml rev %s" % net["meta"]["rev"],
                  sources={k: v for k, v in SRC.items()}, status="v1 routes; checks, seats and retention in later versions"),
        terminals=term_out, cable_ends=ends, cables=cables, retention=[])


if __name__ == "__main__":
    main()
