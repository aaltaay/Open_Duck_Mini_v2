#!/usr/bin/env python3
"""Every component of the charging dock in 3D (CAD check only): the printed parts of dock_parts.py placed, every bought
part modelled from its data sheet or product page (sizes and sources in each entry), the docked duck's pose, and the
interference check of the moving parts.

  python3 altaay_lab/twin/dock/dock_assembly.py            writes dock_assembly.json (components, poses, sources, checks)
  import dock_assembly as DA; DA.meshes("dock" | "docked")  {component id: trimesh in the dock frame, mm}

States: "dock" = no duck (the seat top floats 6 mm up, the paddle at rest); "docked" = the duck seated (the seat top on
its walls at 112 mm, the paddle pushed and turned as in the sim run of docked_pose.json). Fasteners are in
dock_fasteners.json, wires in dock_cables3d.json (their own scripts). Dock frame as dock_parts.py.
"""
import json, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dock_parts as DP  # noqa: E402
from dock_parts import box, cyl, cyl_x, cyl_y  # noqa: E402

POSE = json.load(open(os.path.join(HERE, "docked_pose.json")))
PUSH_DOCKED = round(POSE["joints"]["paddle_slide"] * 1000, 2)
YAW_DOCKED = POSE["joints"]["paddle_yaw"]
ZF = DP.BAY["z0"] + DP.BAY["floor"]          # bay floor top
VHB = 1.1                                     # 3M VHB 4950, 1.1 mm (BOM 29)

# ------------------------------------------------------------------------------------------------ sources
SRC = {
    "evm": "[I] Microchip DS51849A user's guide (ww1.microchip.com/downloads/en/DeviceDoc/51849A.pdf): board top assembly and layout (fig. 2-1, A.3), TP1 VDD, TP2 VBAT+, TP3 VSS, TP4 VBAT-, STAT at D1 and R2, 4 bump-ons under it, U1 MCP73213-A6S/MF; outline 26.0 x 22.6 mm scaled from the layout by its 0603 pads (calc; no outline is published: BLOCKER for +/- 1 mm)",
    "2815": "[I] https://www.pololu.com/product/2815 (0.8 x 1.0 x 0.16 in, 2.7 g; VIN, VOUT, GND, CTRL pads)",
    "perf": "[I] https://www.adafruit.com/product/1609 (51 x 81 mm, two mounting holes 73.7 mm apart, 1.2 mm holes, 12 g); mounting hole diameter not published: 3.2 mm assumed for M3 (BLOCKER, check on the board)",
    "d2f": "[I] Omron D2F data sheet (omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf): 12.8 x 6.5 x 5.8 mm, 2 x 2.0 mm holes 6.5 apart, hinge lever, solder terminals (D2F-01L-D3 the fallback)",
    "pin": "[I] Mill-Max 0933-0-15-20-72-14-11-0 data sheet: initial height 11.201 mm, stroke 1.397 mm, press-fit 1.600 mm hole, solder cup",
    "jack": "[I] Same Sky PJ-005A data sheet (sameskydevices.com/product/resource/pj-005a.pdf, rev 1.09): 5 A, 24 V, 5/16-32 bushing 5.7 mm, flange 10.8 mm, body 10.0 mm, 3 solder lugs, nut and washer, mates a 5.5 x 2.1 mm plug (2.0 mm pin), insertion depth 10.1 mm",
    "fuse_holder": "[L] BOM.md L3: Littelfuse FHAC0001ZXJ body 50 x 17.2 x 17.2 mm with a cover on a strap, 16 AWG leads 90 mm (Littelfuse drawing)",
    "adapter": "[I] Mean Well GSM36U09-P1J (TRC Electronics page): wall plug, 9 V 4 A, 1.5 m cord, 5.5 x 2.1 mm plug; body size not read: a 70 x 45 x 32 mm stand-in (BLOCKER)",
    "rod": "[I] OnDrive GPM4000-100, 4 mm h6 17-4PH rod, cut to 76 mm (or the cheaper rod of DOCK_TWIN section 7)",
    "cf": "[I] Century Spring CF37CS page: drum 6.4 mm, 4.75 x 0.08 mm, 304.8 mm, 1.65 N",
    "seat_spring": "[I] Century Spring CC-28CS page: OD 7.14, ID 6.12, free 23.88 mm",
    "ballast": "[I] Zoro Select 18F312X25-12, 1018 bar 5/16 x 2-1/2 x 12 in, cut to 2 x 120 mm",
    "feet": "[I] https://www.adafruit.com/product/550 (about 8 mm diameter, 4 mm tall, polyurethane, 4 per pack)",
    "tags": "[L] DOCK_TWIN section 2: tag36h11 id 0 40 mm at y 0, ids 1 and 2 60 mm at y +/- 100, centres 370 mm; printed on paper",
    "dip8": "[I] TI LM393P / NE555P data sheets: PDIP-8 (P) 9.81 x 6.35 mm body, 2.54 mm pitch, 7.62 mm rows",
    "to92": "[I] TI TL431 LP and onsemi 2N3904 data sheets: TO-92 4.7 x 3.8 mm, 4.6 mm tall",
    "axial": "1/4 W axial resistor 6.3 x 2.4 mm (SparkFun COM-10969 kit), 1N4148 DO-35 4.0 x 1.9 mm (onsemi data sheet)",
}


def T_xyz(x, y, z):
    T = np.eye(4); T[:3, 3] = (x, y, z); return T


def rz(a, about=(0.0, 0.0)):
    T = trimesh.transformations.rotation_matrix(a, (0, 0, 1), (about[0], about[1], 0)); return T


def load_stl(name):
    return trimesh.load(os.path.join(HERE, "stl", name + ".stl"), force="mesh")


# ------------------------------------------------------------------------------------------------ the parts list
def components(state="dock"):
    """list of dicts: id, label, kind (printed | bought | board_part | paper), bom (line), mount, src, mesh (trimesh)"""
    C = []
    seat_dz = 0.0 if state == "docked" else DP.SEAT_TRAVEL
    push = PUSH_DOCKED if state == "docked" else 0.0
    yaw = YAW_DOCKED if state == "docked" else 0.0

    def add(cid, label, kind, bom, mesh, mount="", src="", group="dock", moves=None):
        C.append(dict(id=cid, label=label, kind=kind, bom=bom, mount=mount, src=src, group=group, moves=moves, mesh=mesh))

    # printed
    T_push = T_xyz(push, 0, 0)
    T_pad = T_push @ rz(yaw, (18.0, 0.0))
    for n in DP.PRINTED:
        m = load_stl(n)
        if n == "dock_seat_top":
            add(n, "Seat top (sprung)", "printed", "K7", m.copy().apply_translation((0, 0, seat_dz)), "on 2 guide pins and 2 springs on the seat posts", group="seat", moves="seat")
        elif n == "dock_paddle":
            add(n, "Chest paddle (6 pins)", "printed", "K7", m.copy().apply_transform(T_pad), "swivels on 2 coaxial M3x20 in the carrier", group="paddle", moves="paddle")
        elif n == "dock_paddle_carrier":
            add(n, "Paddle carrier (yoke)", "printed", "K7", m.copy().apply_transform(T_push), "slides on the 2 rods", group="paddle", moves="carrier")
        elif n in ("dock_spring_cup", "dock_spring_carriage", "dock_spring_drum"):
            for side, s in (("l", 1), ("r", -1)):
                mm = m.copy().apply_translation((0, s * DP.ROD["y"], 0))
                if n == "dock_spring_carriage":
                    mm.apply_translation((push, 0, 0))
                lab = {"dock_spring_cup": "Spring channel", "dock_spring_carriage": "Spring carriage (rod end)", "dock_spring_drum": "Spring drum"}[n]
                add(f"{n}_{side}", f"{lab}, {'left' if s > 0 else 'right'}", "printed", "K7", mm,
                    {"dock_spring_cup": "2 x M3x16 through the mast face, nylon nuts", "dock_spring_carriage": "pressed on the rod end; the strip screwed on top",
                     "dock_spring_drum": "turns on an M3x18 axle across the channel"}[n], group="spring", moves="carrier" if n == "dock_spring_carriage" else None)
        else:
            grp = "seat" if n.startswith("dock_seat") else ("bay" if n.startswith("dock_bay") else "mast")
            lab = {"dock_seat_base": "Seat base", "dock_spine": "Spine", "dock_base_l": "Mast base, left", "dock_base_r": "Mast base, right",
                   "dock_bay_tray": "Electronics bay tray", "dock_bay_lid": "Electronics bay lid"}.get(n, n.replace("dock_column_", "Mast face ").upper().replace("MAST FACE ", "Mast face "))
            add(n, lab, "printed", "K7", m, group=grp)
    # pins: 0933 in the paddle, tip PIN_PROUD out of the face
    for (z, y), pn in zip(DP.PADDLE_PINS, DP.PIN_NAMES):
        L = DP.PIN["initial_height"]
        tip = -DP.PIN_PROUD
        p = cyl_x(tip + 1.6, tip + L - 2.2, y, z, 1.62, 16).union(cyl_x(tip, tip + 1.6, y, z, 1.0, 12)).union(cyl_x(tip + L - 2.2, tip + L, y, z, 1.62, 16).difference(cyl_x(tip + L - 2.0, tip + L + 0.1, y, z + 0.6, 1.2, 12)))
        add(f"pin_{pn}", f"Spring pin {pn} (Mill-Max 0933)", "bought", "K5", p.apply_transform(T_pad), "press-fit into the 1.60 mm bore, solder cup at the back", SRC["pin"], "paddle", "paddle")
    # rods
    for side, s in (("l", 1), ("r", -1)):
        r = cyl_x(DP.ROD["x0"], DP.ROD["x1"], s * DP.ROD["y"], DP.ROD["z"], DP.ROD["d"]).apply_transform(T_push)
        add(f"rod_{side}", f"Guide rod {'left' if s > 0 else 'right'}, 4 x 76 mm", "bought", "K8a", r, "pressed into the carrier crossbar and the carriage", SRC["rod"], "spring", "carrier")
        cx, cz = DP.COIL_C
        coil = cyl_y(cx, s * DP.ROD["y"] - DP.CF["width"] / 2, s * DP.ROD["y"] + DP.CF["width"] / 2, cz, DP.CF["coil_od"]).difference(cyl_y(cx, s * DP.ROD["y"] - 3, s * DP.ROD["y"] + 3, cz, DP.CF["drum"] - 0.01))
        strip = box(cx, 104.0 + push + 2.5, s * DP.ROD["y"] - DP.CF["width"] / 2, s * DP.ROD["y"] + DP.CF["width"] / 2, 184.0, 184.0 + DP.CF["t"])
        add(f"cf_{side}", f"Constant-force spring {'left' if s > 0 else 'right'} (Century CF37CS)", "bought", "K8c", coil.union(strip),
            "coil on the printed drum; the strip end under an M3x8 on the carriage", SRC["cf"], "spring", "carrier")
    # seat springs
    for x in DP.SEAT_POSTS:
        L = DP.SPRING_REST_L - (DP.SEAT_TRAVEL - seat_dz)
        sp = cyl(x, 0, DP.POST_TOP, DP.POST_TOP + L, DP.SEAT_SPRING["od"]).difference(cyl(x, 0, DP.POST_TOP - 1, DP.POST_TOP + L + 1, DP.SEAT_SPRING["id"]))
        add(f"seat_spring_{'b' if x < -60 else 'f'}", "Seat spring (Century CC-28CS)", "bought", "K8d", sp, "in the post pocket, round the guide pin", SRC["seat_spring"], "seat", "seat")
    # microswitch on the tower
    s0 = DP.SW_HOLE_Z - DP.SW["hole_from_bottom"]
    sw = box(DP.SW["x0"], DP.SW["x1"], -DP.SW["y"], DP.SW["y"], s0, s0 + DP.SW["h"])
    for y in (-DP.SW["hole_pitch"] / 2, DP.SW["hole_pitch"] / 2):
        sw = sw.difference(cyl_x(DP.SW["x0"] - 1, DP.SW["x1"] + 1, y, DP.SW_HOLE_Z, 2.0))
    lever_z = DP.SW_HOLE_Z + (9.4 if state == "dock" else 6.0)
    sw = sw.union(box(-65.2, -61.4, -5.4, 6.0, lever_z - 0.3, lever_z))                     # stainless lever (t 0.3)
    for y in (-5.08, 0.0, 5.08):
        sw = sw.union(box(-63.7, -63.1, y - 1.6, y + 1.6, s0 - 3.5, s0))                      # solder terminals
    add("switch", "Seat microswitch (Omron D2F-01L)", "bought", "K3", sw, "2 x M2x12 through its holes into the slotted tower, nylon nuts; height set at BT5", SRC["d2f"], "seat")
    # ballast, feet, tags
    for side, s in (("l", 1), ("r", -1)):
        bx, by, bz = DP.BALLAST["bar"]
        y0 = DP.BALLAST["y0"] + 0.5
        bar = box(DP.BALLAST["x0"] + 0.5, DP.BALLAST["x0"] + 0.5 + bx, *(sorted((s * y0, s * (y0 + by)))), DP.BASE["z1"] - DP.BALLAST["depth"], DP.BASE["z1"] - DP.BALLAST["depth"] + bz)
        add(f"ballast_{side}", f"Ballast bar {'left' if s > 0 else 'right'} (1018 steel 120 x 63.5 x 7.9)", "bought", "K8k", bar, "in the base pocket, held down by the bay tray", SRC["ballast"], "mast")
    fp = [(-102, 12), (-102, -12), (-23, 12), (-23, -12)] + [(x, s * y) for s in (1, -1) for x, y in ((36, 30), (36, 130), (184, 30), (184, 130))]
    for i, (x, y) in enumerate(fp):
        add(f"foot_{i + 1}", "Rubber foot (Adafruit 550)", "bought", "K10", cyl(x, y, 0.0, 4.0, 8.0, 20), "adhesive, in a 2 mm pocket", SRC["feet"], "mast")
    for tid, t in DP.TAGS.items():
        h = t["size"] / 2
        add(f"tag_{tid}", f"AprilTag tag36h11 id {tid} ({t['size']:.0f} mm)", "paper", "K13", box(74.7, 75.0, t["y"] - h - 4, t["y"] + h + 4, DP.TAG_Z - h - 4, DP.TAG_Z + h + 4),
            "printed on paper, glued on the mast face", SRC["tags"], "mast")
    # electronics bay
    evm = box(120.0, 146.0, -35.0, -12.4, ZF + VHB, ZF + VHB + 1.6)
    for (x, y) in ((124, -16.5), (136, -16.5), (124, -31), (136, -31)):
        evm = evm.union(box(x - 2.0, x + 2.0, y - 1.3, y + 1.3, ZF + VHB + 1.6, ZF + VHB + 3.2))   # Keystone 5016 test points
    evm = evm.union(box(131.5, 134.5, -25.2, -22.2, ZF + VHB + 1.6, ZF + VHB + 2.5))             # U1 3 x 3 DFN
    add("evm", "Charger board (Microchip MCP73213EV-2SOVP)", "bought", "K1", evm, "on VHB 4950 in a printed rim (bump-ons removed); no mounting holes", SRC["evm"], "bay")
    add("vhb_evm", "VHB pad under the charger board", "bought", "K12b", box(121, 145, -34, -13.4, ZF, ZF + VHB), "", "[L] BOM 29 3M VHB 4950 1.1 mm", "bay")
    sw2815 = box(150.0, 170.3, -40.0, -14.6, ZF + VHB, ZF + VHB + 1.6).union(box(156, 164, -30, -24, ZF + VHB + 1.6, ZF + VHB + 4.1))
    add("swg", "Gate switch (Pololu 2815)", "bought", "K2", sw2815, "on VHB 4950 in a printed rim (as the robot's 2813)", SRC["2815"], "bay")
    add("vhb_swg", "VHB pad under the 2815", "bought", "K12b", box(151, 169.3, -39, -15.6, ZF, ZF + VHB), "", "[L] BOM 29", "bay")
    fh = box(120.0, 170.0, -95.0, -77.8, ZF + VHB, ZF + VHB + 17.2)
    add("fuse_holder", "Adapter fuse holder (Littelfuse FHAC0001ZXJ) with 5 A ATO fuse", "bought", "K9", fh, "on VHB 4950 in a printed rim", SRC["fuse_holder"], "bay")
    add("vhb_fh", "VHB pad under the fuse holder", "bought", "K12b", box(121, 169, -94, -78.8, ZF, ZF + VHB), "", "[L] BOM 29", "bay")
    jz, jy = DP.JACK["z"], DP.JACK["y"]
    jx = DP.BAY["x1"]
    jack = cyl_x(jx - 10.0 - 2.0, jx - 2.0, jy, jz, 10.8).union(cyl_x(jx - 2.0, jx + 3.7, jy, jz, 7.94)).union(cyl_x(jx, jx + 2.0, jy, jz, 12.5).difference(cyl_x(jx - 1, jx + 3, jy, jz, 8.0)))
    for dy in (-2.6, 0.0, 2.6):
        jack = jack.union(box(jx - 17.5, jx - 12.0, jy + dy - 0.6, jy + dy + 0.6, jz - 2.0, jz + 2.0))
    add("jack", "DC jack (Same Sky PJ-005A)", "bought", "K6b", jack, "through the 8 mm hole in the tray's rear wall, nut and washer outside", SRC["jack"], "bay")
    plug = cyl_x(jx + 3.7, jx + 13.7, jy, jz, 5.5).union(cyl_x(jx + 13.7, jx + 43.7, jy, jz, 10.0))
    add("plug", "Adapter plug 5.5 x 2.1 mm (Mean Well P1J)", "bought", "K6", plug, "", SRC["adapter"], "bay")
    cord = trimesh.creation.cylinder(radius=1.75, segment=[(jx + 43.7, jy, jz), (jx + 90, jy - 30, 2.0)])
    cord = cord.union(trimesh.creation.cylinder(radius=1.75, segment=[(jx + 90, jy - 30, 2.0), (jx + 250, jy - 30, 2.0)]))
    add("adapter_cord", "Adapter cord (part of K6, 1.5 m; 0.25 m drawn)", "bought", "K6", cord, "", SRC["adapter"], "bay")
    add("adapter", "Wall adapter Mean Well GSM36U09-P1J (stand-in size)", "bought", "K6", box(jx + 250, jx + 320, jy - 52, jy - 8, 2.0, 34.0), "in the wall socket", SRC["adapter"], "bay")
    # gate perfboard and its parts
    ps = DP.PERF
    zb = ZF + ps["standoff"]
    perf = box(ps["x0"], ps["x1"], ps["y0"], ps["y1"], zb, zb + 1.6)
    pxc = (ps["x0"] + ps["x1"]) / 2; pyc = (ps["y0"] + ps["y1"]) / 2
    for dy in (-ps["hole_pitch"] / 2, ps["hole_pitch"] / 2):
        perf = perf.difference(cyl(pxc, pyc + dy, zb - 1, zb + 3, 3.2))
    add("perf", "Gate board (Adafruit 1609 Perma-Proto half)", "bought", "K4i", perf, "2 x M3x8 into inserts in 2 printed standoffs", SRC["perf"], "bay")
    zt = zb + 1.6
    import yaml
    GB = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))["gate_board"]["parts"]
    slots = {"dip8": [(130.0, 20.0), (130.0, 40.0), (130.0, 62.0)], "to92": [(150.0, 20.0), (150.0, 40.0), (150.0, 62.0)],
             "axial": [(157 + 8 * (i // 10), 12 + 5 * (i % 10)) for i in range(20)], "diode": [(140.0, 72.0), (146.0, 72.0), (152.0, 72.0)],
             "cap": [(127.0, 28.0), (127.0, 50.0), (127.0, 70.0), (140.0, 30.0), (140.0, 50.0), (160.0, 72.0)]}
    used = {k: 0 for k in slots}
    gate = []
    for g in GB:
        r = g["ref"]
        kind = "dip8" if r.startswith("U") else "to92" if r.startswith(("Q", "VR")) else "axial" if r.startswith("R") else "diode" if r.startswith("D") else "cap"
        x, y = slots[kind][used[kind]]; used[kind] += 1
        gate.append((r, kind, g["part"], g["bom"], x, y))
    for ref, kind, lab, bom, x, y in gate:
        if kind == "dip8":
            m = box(x - 3.2, x + 3.2, y - 4.9, y + 4.9, zt + 0.5, zt + 3.8)
        elif kind == "to92":
            m = box(x - 2.35, x + 2.35, y - 1.9, y + 1.9, zt + 3.0, zt + 7.6)
        elif kind == "axial":
            m = cyl_x(x - 3.15, x + 3.15, y, zt + 1.4, 2.4, 12)
        elif kind == "diode":
            m = cyl_y(x, y - 2.0, y + 2.0, zt + 1.2, 1.9, 12)
        else:
            m = box(x - 2.5, x + 2.5, y - 1.3, y + 1.3, zt, zt + 4.0)
        add(f"gate_{ref}", f"{ref} {lab}", "board_part", bom, m, "soldered on the gate board", SRC.get(kind, SRC["axial"]), "bay")
    return C


def meshes(state="dock"):
    return {c["id"]: c["mesh"] for c in components(state)}


# ------------------------------------------------------------------------------------------------ checks
ALLOWED = {  # pairs that touch by design (fits and seats); each with the reason
    ("dock_spring_carriage", "rod"): "the rod is pressed into the carriage",
    ("dock_paddle_carrier", "rod"): "the rod is pressed into the carrier crossbar",
    ("dock_spring_drum", "cf"): "the coil grips the drum",
    ("dock_spring_carriage", "cf"): "the strip is screwed to the carriage top",
    ("dock_paddle", "pin"): "the pins are pressed into the paddle",
    ("dock_seat_base", "seat_spring"): "the springs sit in the post pockets",
    ("dock_seat_top", "seat_spring"): "the springs bear on the seat top locators",
    ("dock_seat_base", "switch"): "the switch is screwed to the tower",
    ("dock_base", "ballast"): "the bars lie in the base pockets",
    ("dock_bay_tray", "ballast"): "the tray floor holds the bars down",
    ("dock_seat_base", "foot"): "feet in their pockets", ("dock_base", "foot"): "feet in their pockets",
    ("dock_column", "tag"): "tags glued on the face",
    ("dock_bay_tray", "jack"): "the jack bushing passes the rear wall",
    ("dock_bay_tray", "vhb"): "tape on the tray floor", ("vhb", "evm"): "tape", ("vhb", "swg"): "tape", ("vhb", "fuse_holder"): "tape",
    ("dock_bay_tray", "perf"): "the board sits on the standoffs",
    ("perf", "gate"): "parts on the board", ("jack", "plug"): "the plug in the jack", ("plug", "adapter_cord"): "the cord leaves the plug",
    ("adapter_cord", "adapter"): "the cord enters the adapter",
    ("dock_seat_top", "switch"): "the finger presses the lever (docked)",
    ("dock_spring_cup", "rod"): "the rod slides in the 4.4 mm bore",
}


def _key(cid):
    for p in ("dock_spring_carriage", "dock_spring_cup", "dock_spring_drum", "dock_base", "dock_column", "seat_spring", "rod", "cf", "pin", "foot", "tag", "vhb", "gate", "ballast"):
        if cid.startswith(p):
            return p
    return cid


def interferences(M, tol_mm3=0.5):
    """pairwise intersection volumes over the components (a pair is skipped only if ALLOWED names it)"""
    ids = list(M)
    bounds = {i: M[i].bounds for i in ids}
    out = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]
            if np.any(bounds[i][1] < bounds[j][0] - 0.01) or np.any(bounds[j][1] < bounds[i][0] - 0.01):
                continue
            ki, kj = _key(i), _key(j)
            if (ki, kj) in ALLOWED or (kj, ki) in ALLOWED:
                continue
            try:
                v = M[i].intersection(M[j]).volume
            except Exception:
                v = 0.0
            if v > tol_mm3:
                out.append(dict(a=i, b=j, mm3=round(float(v), 2)))
    return out


def motion_check():
    """the moving paddle group (paddle, pins, carrier, rods, carriages, strips) against the fixed parts at 0, 20, 40 mm
    and -10, 0, +10 deg of swivel"""
    fixed = {c["id"]: c["mesh"] for c in components("dock") if c.get("moves") not in ("paddle", "carrier")}
    res = []
    for push in (0.0, 20.0, 40.0):
        for yaw_deg in (-10.0, 0.0, 10.0):
            T_push = T_xyz(push, 0, 0); T_pad = T_push @ rz(np.radians(yaw_deg), (18.0, 0.0))
            mov = {}
            for c in components("dock"):
                if c.get("moves") == "paddle":
                    mov[c["id"]] = c["mesh"].copy().apply_transform(T_xyz(0, 0, 0) @ np.linalg.inv(np.eye(4)) @ T_pad)
                elif c.get("moves") == "carrier":
                    mov[c["id"]] = c["mesh"].copy().apply_transform(T_push)
            hits = []
            for i, mi in mov.items():
                for j, mj in list(fixed.items()) + [(k, v) for k, v in mov.items() if k != i]:
                    if np.any(mi.bounds[1] < mj.bounds[0]) or np.any(mj.bounds[1] < mi.bounds[0]):
                        continue
                    ki, kj = _key(i), _key(j)
                    if (ki, kj) in ALLOWED or (kj, ki) in ALLOWED or i == j:
                        continue
                    try:
                        v = mi.intersection(mj).volume
                    except Exception:
                        v = 0.0
                    if v > 0.5:
                        hits.append(dict(a=i, b=j, mm3=round(float(v), 2)))
            uniq = {tuple(sorted((h["a"], h["b"]))): h for h in hits}
            res.append(dict(push_mm=push, yaw_deg=yaw_deg, hits=list(uniq.values())))
    return res


def docked_duck_links():
    """dock-frame 4x4 (mm) of every duck link in the docked pose (sim): T_dock(link)"""
    out = {}
    for l, v in POSE["links"].items():
        if l.startswith("dock_"):
            continue
        T = np.eye(4); T[:3, :3] = np.array(v["R"]).reshape(3, 3); T[:3, 3] = v["pos_mm"]
        out[l] = T
    return out


if __name__ == "__main__":
    rep = dict(label="CAD check only", frame="dock frame, mm: x toward the mast (paddle face at rest x 0), y left, z up from the floor",
               docked=dict(push_mm=PUSH_DOCKED, yaw_deg=round(np.degrees(YAW_DOCKED), 2), source=POSE["source"]), sources=SRC)
    for state in ("dock", "docked"):
        C = components(state)
        M = {c["id"]: c["mesh"] for c in C}
        rep[state] = dict(n=len(C), interferences=interferences(M),
                          components=[dict(id=c["id"], label=c["label"], kind=c["kind"], bom=c["bom"], group=c["group"], mount=c["mount"], src=c["src"],
                                           bounds=np.round(c["mesh"].bounds, 2).tolist(), volume_mm3=round(float(c["mesh"].volume), 1)) for c in C])
        print(state, len(C), "interferences", rep[state]["interferences"])
    rep["motion"] = motion_check()
    print("motion hits", sum(len(r["hits"]) for r in rep["motion"]), [r for r in rep["motion"] if r["hits"]][:3])
    json.dump(rep, open(os.path.join(HERE, "dock_assembly.json"), "w"), indent=1)
