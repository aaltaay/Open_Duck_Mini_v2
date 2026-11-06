#!/usr/bin/env python3
"""Dock printed parts for the Open Duck Mini v2 contact dock (CAD check only): writes the STLs in stl/ next to this
file and stl/parts.json. Geometry matches the dock sim of the shared lab gym (overlay gym/overlays/duck,
dock/dock_course.py; DOCK_TWIN.md section 2). Dock frame, mm: x toward the mast (the paddle face at rest is x = 0),
y left, z up from the floor. Every part fits a 220 x 220 mm bed and a 150 mm print height.

Rev 2026-11-06 (ET), the full dock job (DOCK_TWIN.md section 12). What changed against the phase 2 parts:
- The floor parts stand on rubber feet (BOM K10, 8 x 4 mm) in 2.0 mm pockets, so their bottoms are at z FOOT = 2.0 and
  every height to the floor is the sim's (the seat top under a duck at 112 mm, the tags at 370 mm).
- Seat: the walls end at z 100 and the sprung top sits on them under the duck, so the loaded seat is at 112 (the sim's
  rigid seat); at rest the top floats 6 mm higher on two Century CC-28CS springs. The D2F-01L switch sits on a slotted
  tower (2 x M2x12 and nylon nuts, height set at BT5) and a printed finger on the seat top presses its lever, with a
  beam that flexes past the lever's over-travel. The seat top no longer has the unused pin-holder pocket.
- Seat to spine: 2 x M3x8 from inside the seat into heat-set inserts in the spine (was M3x50 through 45 mm: too short).
- Spine to base: the spine gets a 6 mm flange on top of the mast base (x 30..70) with 4 x M3x12 into inserts in the base
  halves (the old holes at x 40 and 60 met no spine).
- Base to column: the M3x12 from below now ends in heat-set inserts in the column bottoms (no bore before).
- Column: the halves are split at different heights (left 160 and 310, right 210 and 360) so the rib bolts lock the stack;
  ribs 13 mm per half; 9 rib bolts M3x30 with nylon nuts, uniform 50 mm pitch.
- Ballast: one 1018 bar 120 x 63.5 x 7.9 mm per half in a 121 x 64.5 x 8.0 mm pocket under the bay tray (the old comment
  said 100 x 120 x 10, the old pocket was 7 mm deep).
- Paddle return: a Century CF37CS constant-force spring per side (1.65 N each, 3.29 N for the pair at any travel), coiled
  on a printed drum in an open-top spring channel behind the mast; the strip end is screwed to a printed carriage
  pressed on the rod end, and the carriage nose is the rest stop (no shaft collar). Rods 76 mm.
- Pins: Mill-Max 0933-0-15-20-72-14-11-0 (press-fit into an insulator, 1.600 mm hole, solder cup, 45 gf at mid stroke,
  1.397 mm stroke), 1.05 mm proud of the face: the face is the stop at 75 % of the stroke. No PTFE tape.
- Electronics bay: a printed tray and lid behind the mast on the two base halves (charger board, gate perfboard,
  Pololu 2815, fuse holder, DC jack); cable groove in base_l and channels in the spine and the seat for the switch leads.

Parts (name: what it is; prints):
  dock_seat_base, dock_seat_top, dock_spine, dock_base_l, dock_base_r, dock_column_l1..l3, dock_column_r1..r3,
  dock_paddle, dock_paddle_carrier, dock_spring_cup (x2), dock_spring_carriage (x2), dock_spring_drum (x2),
  dock_bay_tray, dock_bay_lid. dock_pin_holder is the old belly-pad option and is not printed.
Every part is written in its assembled pose (the seat top under a seated duck; the spring parts of the left side at
y 0, placed at y +40 and -40 by dock_assembly.py).
"""
import json, os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    b.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return b


def cyl(x, y, z0, z1, d, sections=32):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=sections)
    c.apply_translation((x, y, (z0 + z1) / 2))
    return c


def cyl_y(x, y0, y1, z, d, sections=24):
    c = trimesh.creation.cylinder(radius=d / 2, height=abs(y1 - y0), sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    c.apply_translation((x, (y0 + y1) / 2, z))
    return c


def cyl_x(x0, x1, y, z, d, sections=24):
    c = trimesh.creation.cylinder(radius=d / 2, height=abs(x1 - x0), sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    c.apply_translation(((x0 + x1) / 2, y, z))
    return c


hole_x, hole_y = cyl_x, cyl_y

# ------------------------------------------------------------------------------------------------ shared dimensions
M3 = 3.4           # clearance for M3
M2 = 2.4           # clearance for M2
INSERT = 4.0       # M3 heat-set insert hole (BOM 16: CNC Kitchen M3 x 5.7, hole 4.0)
INSERT_DEPTH = 7.0
PILOT_M3 = 2.5     # M3 self-tapped into PLA (the paddle pivot rule)
FOOT = 2.0         # rubber foot (Adafruit 550, about 8 x 4 mm) in a 2.0 mm pocket: floor parts start at z 2
FOOT_POCKET = (8.6, 2.0)
Z_SEAT = 147.1     # seated trunk origin, world z (dock sim)
SEAT_LOADED = 112.0  # seat top under a duck (the sim's rigid seat)
SEAT_TRAVEL = 6.0    # the top floats this much higher with no duck
STRIPS = {"SYS": (0.0, 17.5), "GND": (19.5, 37.0), "SENSE": (39.0, 56.5), "CHG+": (58.5, 76.0)}   # trunk z (D50)
PADDLE_PINS = [(round(Z_SEAT + sum(STRIPS[n]) / 2, 2), y) for n, ys in (("SYS", (-3.0, 3.0)), ("GND", (-3.0, 3.0)), ("SENSE", (0.0,)), ("CHG+", (0.0,))) for y in ys]
PIN_NAMES = ["SYS_R", "SYS_L", "GND_R", "GND_L", "SENSE", "CHG"]
PINS = {"SENSE": [(-38.7, 0.0)], "CHG+": [(-30.2, 5.0), (-30.2, -5.0)], "GND": [(-47.2, 5.0), (-47.2, -5.0)]}  # old belly option
# Mill-Max 0933-0-15-20-72-14-11-0 [I] mm.digikey.com .../7171/0933-0-15-20-72-14-11-0.pdf (Mill-Max data sheet 8/8/25)
PIN = dict(hole_max=1.600, initial_height=11.201, stroke=1.397, force_mid_gf=45.0, i_max_a=6.0, i_derated_a=4.80, r_max_mohm=40.0)
PIN_PROUD = 1.05   # tip proud of the paddle face: the face stops the chest at 75 % of the stroke
PIN_BORE = 1.60    # printed 1.4 mm, drilled 1/16 in (1.59 mm) to the data sheet's 1.600 mm maximum hole
# seat springs: Century Spring CC-28CS [I] https://www.centuryspring.com/shop/cc-28cs (page 2026-11-06): free 23.88,
# OD 7.14, ID 6.12, rate 0.25 N/mm, solid 6.1, max deflection 17.78 mm, max load 4.45 N
SEAT_SPRING = dict(free=23.88, od=7.14, id=6.12, rate=0.25, solid=6.1, max_defl=17.78, max_load=4.45)
SPRING_REST_L = 22.88                                   # 1.0 mm preload at rest (0.25 N a spring, carries the top)
POST_TOP = SEAT_LOADED + SEAT_TRAVEL - 12.0 - SPRING_REST_L   # 83.12: the spring pocket floor (the post rises 1.5 mm more)
SEAT_POSTS = (-95.0, -30.0)
# Omron D2F-01L [I] https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf: 12.8 x 6.5 x 5.8 mm, 2 x 2.0 mm mounting
# holes 6.5 mm apart, hinge lever OF max 0.78 N, OT min 0.55 mm, FP max 10 mm, OP 6.8 +/- 1.5 mm (from the hole line)
SW = dict(x0=-66.2, x1=-60.4, y=6.4, h=6.5, hole_pitch=6.5, hole_from_bottom=3.15)
SW_HOLE_Z = SEAT_LOADED + SEAT_TRAVEL - 12.0 - 18.0 - 12.02     # 75.98: closes at 5.0 of 6.0 mm of travel at the nominal OP
FINGER_TIP_LOADED = SW_HOLE_Z + 6.02                            # 82.0
# constant-force spring: Century Spring CF37CS [I] https://www.centuryspring.com/shop/cf37cs (page 2026-11-06): 0.37 lb
# (1.65 N), drum 6.4 mm, width 4.75 mm, thickness 0.08 mm, length 304.8 mm, hole 3.25 mm
CF = dict(load_n=0.37 * 4.4482216, drum=6.4, width=4.75, t=0.08, length=304.8, hole=3.25, coil_id=5.59)
CF["coil_od"] = round(float(np.sqrt(CF["coil_id"] ** 2 + 4 * CF["length"] * CF["t"] / np.pi)), 2)
ROD = dict(d=4.0, x0=24.0, x1=100.0, z=180.0, y=40.0)        # guide rods, the carrier crossbar to the carriage
COIL_C = (92.0, 184.0 + CF["t"] + CF["coil_od"] / 2)          # fixed coil centre (x, z) in the spring channel
TRAVEL = 40.0
CUP_BOLT_DZ = (-17.0, 17.0)            # spring channel flange bolts, clear of the coil and the channel
COLUMN_SPLITS = {"l": [12.0, 160.0, 310.0, 460.0], "r": [12.0, 210.0, 360.0, 460.0]}
RIB_T = 13.0
RIB_BOLTS_Z = [35.0 + 50.0 * i for i in range(9)]
BASE = dict(x0=30.0, x1=190.0, z0=FOOT, z1=FOOT + 10.0)
BALLAST = dict(x0=114.0, x1=178.5, y0=8.0, y1=129.0, depth=8.0, bar=(63.5, 120.0, 7.9))   # pocket per half, bar x, y, z
SPINE_BOLTS = [(40.0, 8.0), (60.0, 8.0)]
COLUMN_BOLTS = [(79.0, 70.0), (93.0, 5.0)]
BAY = dict(x0=104.0, x1=189.0, y=100.0, z0=BASE["z1"], floor=2.0, wall=2.0, z1=BASE["z1"] + 36.0, lid=2.0)
BAY_FLOOR_BOLTS = [(110.0, 60.0), (182.0, 60.0)]
BAY_LID_BOSSES = [(107.5, 96.5), (185.5, 96.5)]
CABLE_HOLE = dict(y=20.0, z=200.0, d=9.0)          # paddle cable bundle (4 conductors, 4.4 mm) through the face plate (column l2)          # paddle cable through the face plate (column l2)
GROOVE = dict(y0=12.0, y1=16.0, depth=4.0, x1=110.0)  # switch cable groove in base_l top
JACK = dict(y=-65.0, z=BASE["z1"] + 2.0 + 16.0, hole=8.0)   # Same Sky PJ-005A 5/16-32 bushing in the tray rear wall
PERF = dict(x0=120.0, x1=171.0, y0=5.0, y1=86.0, standoff=6.0, hole_pitch=73.7)
TAGS = {0: dict(size=40.0, y=0.0), 1: dict(size=60.0, y=100.0), 2: dict(size=60.0, y=-100.0)}
TAG_Z = 370.0


def feet(m, pts):
    for x, y in pts:
        m = m.difference(cyl(x, y, FOOT - 0.01, FOOT + FOOT_POCKET[1], FOOT_POCKET[0]))
    return m


def parts():
    P = {}
    # ---------------------------------------------------------------- seat base
    zt = SEAT_LOADED - 12.0                                                            # 100: wall top, the loaded stop
    base = box(-110, -15, -20, 20, FOOT, zt).difference(box(-107, -18, -17, 17, FOOT + 3, zt + 1))
    for x in SEAT_POSTS:
        base = base.union(cyl(x, 0, FOOT + 3, POST_TOP + 1.5, 10.0))
        base = base.difference(cyl(x, 0, POST_TOP, POST_TOP + 2.5, 7.6))               # spring pocket, its floor at POST_TOP
        base = base.difference(cyl(x, 0, POST_TOP - 18.0, POST_TOP + 1, 4.2))          # guide pin bore
    base = base.union(box(-60.4, -57.4, -10, 10, FOOT + 3, SW_HOLE_Z + 6.0))          # switch tower plate
    base = base.union(box(-60.4, -48.0, -10, -7, FOOT + 3, SW_HOLE_Z + 6.0)).union(box(-60.4, -48.0, 7, 10, FOOT + 3, SW_HOLE_Z + 6.0))  # ribs
    for y in (-SW["hole_pitch"] / 2, SW["hole_pitch"] / 2):
        slot = box(-61, -57, y - 1.2, y + 1.2, SW_HOLE_Z - 2.0, SW_HOLE_Z + 2.0)
        slot = slot.union(cyl_x(-61, -57, y, SW_HOLE_Z - 2.0, 2.4)).union(cyl_x(-61, -57, y, SW_HOLE_Z + 2.0, 2.4))
        base = base.difference(slot)                                                  # 4 mm of height adjustment
    for z in (30.0, 70.0):
        base = base.difference(cyl_x(-19, -14, 0, z, M3))                              # 2 x M3x8 into the spine inserts
    base = base.difference(cyl_x(-19, -14, 14.0, 20.0, 5.0))                           # switch lead hole into the spine
    base = feet(base, [(-102, 12), (-102, -12), (-23, 12), (-23, -12)])
    P["dock_seat_base"] = base
    # ---------------------------------------------------------------- seat top (loaded pose)
    top = box(-110, -15, -20, 20, zt, SEAT_LOADED)
    for x in SEAT_POSTS:
        top = top.union(cyl(x, 0, zt - 1.5, zt, 5.8))                                  # spring locator
        top = top.union(cyl(x, 0, POST_TOP - SEAT_TRAVEL - 11.0, zt, 4.0))             # guide pin: 11 mm in the bore at rest, 1 mm off its floor loaded
    top = top.union(box(-76, -72, 1, 5, FINGER_TIP_LOADED, zt))                        # finger post
    top = top.union(box(-74, -62, 1, 5, FINGER_TIP_LOADED, FINGER_TIP_LOADED + 1.2))   # finger beam 12 x 4 x 1.2 (3.5 N/mm)
    P["dock_seat_top"] = top
    holder = box(-51.6, -25.4, -18.6, 18.6, 104.2, 112)
    for pts in PINS.values():
        for x, y in pts:
            holder = holder.difference(cyl(x, y, 103, 113, 1.9, 16)).difference(cyl(x, y, 103, 106, 3.2, 16))
    P["dock_pin_holder"] = holder
    # ---------------------------------------------------------------- spine with its flange on the mast base
    spine = box(-15, 30, -20, 20, FOOT, 90).union(box(30, 70, -20, 20, BASE["z1"], BASE["z1"] + 6.0))
    for z in (30.0, 70.0):
        spine = spine.difference(cyl_x(-16, -15 + INSERT_DEPTH + 1, 0, z, INSERT))
    for x, y in SPINE_BOLTS:
        for s in (1, -1):
            spine = spine.difference(cyl(x, s * y, BASE["z1"] - 1, BASE["z1"] + 7, M3))
    ch = cyl_x(-16, 28.6, 14.0, 20.0, 5.0).union(cyl(27.0, 14.0, BASE["z1"] - 3.3, 21.3, 5.0, 20)).union(cyl_x(25.3, 31, 14.0, BASE["z1"] - 2, 4.0))
    spine = spine.difference(ch).difference(box(30, 70, GROOVE["y0"], GROOVE["y1"], BASE["z1"] - 0.5, BASE["z1"] + 2.0))
    P["dock_spine"] = spine
    # ---------------------------------------------------------------- mast base halves
    for side, s in (("l", 1), ("r", -1)):
        y0, y1 = (0, 140) if s > 0 else (-140, 0)
        b = box(BASE["x0"], BASE["x1"], y0, y1, BASE["z0"], BASE["z1"])
        by0, by1 = (BALLAST["y0"], BALLAST["y1"]) if s > 0 else (-BALLAST["y1"], -BALLAST["y0"])
        b = b.difference(box(BALLAST["x0"], BALLAST["x1"], by0, by1, BASE["z1"] - BALLAST["depth"], BASE["z1"] + 1))
        for x, y in SPINE_BOLTS + BAY_FLOOR_BOLTS:
            b = b.difference(cyl(x, s * y, BASE["z1"] - INSERT_DEPTH, BASE["z1"] + 1, INSERT))
        for x, y in COLUMN_BOLTS:
            b = b.difference(cyl(x, s * y, BASE["z0"] - 1, BASE["z1"] + 1, M3)).difference(cyl(x, s * y, BASE["z0"] - 1, BASE["z0"] + 3.2, 6.0))
        if s > 0:
            b = b.difference(box(BASE["x0"] - 1, GROOVE["x1"], GROOVE["y0"], GROOVE["y1"], BASE["z1"] - GROOVE["depth"], BASE["z1"] + 1))
        b = feet(b, [(36, s * 30), (36, s * 130), (184, s * 30), (184, s * 130)])
        P[f"dock_base_{side}"] = b
    # ---------------------------------------------------------------- column halves (staggered splits)
    for side, s in (("l", 1), ("r", -1)):
        y0, y1 = (0, 140) if s > 0 else (-140, 0)
        zc = COLUMN_SPLITS[side]
        for i in range(3):
            c = box(75, 83, y0, y1, zc[i], zc[i + 1])
            ry0, ry1 = (0, RIB_T) if s > 0 else (-RIB_T, 0)
            c = c.union(box(83, 103, ry0, ry1, zc[i], zc[i + 1]))
            for z in RIB_BOLTS_Z:
                if zc[i] + 5 < z < zc[i + 1] - 5:
                    c = c.difference(hole_y(93, y0 - 1, y1 + 1, z, M3))
            if i == 0:
                for x, y in COLUMN_BOLTS:
                    c = c.difference(cyl(x, s * y, zc[0] - 1, zc[0] + INSERT_DEPTH + 1, INSERT))
            if zc[i] < ROD["z"] < zc[i + 1]:
                c = c.difference(hole_x(74, 84, s * ROD["y"], ROD["z"], 4.4))
                for dz in CUP_BOLT_DZ:
                    c = c.difference(hole_x(74, 84, s * ROD["y"], ROD["z"] + dz, M3))
            if s > 0 and zc[i] < CABLE_HOLE["z"] < zc[i + 1]:
                c = c.difference(hole_x(74, 84, CABLE_HOLE["y"], CABLE_HOLE["z"], CABLE_HOLE["d"]))
            P[f"dock_column_{side}{i + 1}"] = c
    # ---------------------------------------------------------------- paddle plate (D50 rows, 0933 pins)
    pad = box(0, 12, -55, 55, 140, 230)
    for z, y in PADDLE_PINS:
        pad = pad.difference(hole_x(-1, 13, y, z, PIN_BORE, 16)).difference(hole_x(8, 13, y, z, 3.2, 16))
    for z0, z1 in ((140.0, 152.0), (218.0, 230.0)):
        pad = pad.union(box(11, 18, -5, 5, z0, z1)).union(cyl(18, 0, z0, z1, 10.0))
        pad = pad.difference(cyl(18, 0, z0 - 1, z1 + 1, PILOT_M3))
    P["dock_paddle"] = pad
    car = box(24, 32, -6, 6, 133, 237)
    for z0, z1 in ((133.0, 139.5), (230.5, 237.0)):
        car = car.union(box(18, 24, -6, 6, z0, z1)).union(cyl(18, 0, z0, z1, 10.0))
        car = car.difference(cyl(18, 0, z0 - 1, z1 + 1, M3))
    car = car.union(box(24, 32, -46, 46, 174, 186))
    for y in (-ROD["y"], ROD["y"]):
        car = car.difference(hole_x(23, 33, y, ROD["z"], 3.9))
    P["dock_paddle_carrier"] = car
    # ---------------------------------------------------------------- spring channel, carriage, drum (y 0)
    zc0 = ROD["z"]
    cup = box(83, 152, -7, 7, 172.5, 196).union(box(83, 86, -7, 7, zc0 - 22, zc0 + 22))
    cup = cup.difference(box(86, 149, -4.5, 4.5, 174.5, 197))                       # open-top channel
    cup = cup.difference(hole_x(82, 87, 0, zc0, 4.4))
    for dz in CUP_BOLT_DZ:
        cup = cup.difference(hole_x(82, 87, 0, zc0 + dz, M3))
    cup = cup.difference(hole_y(COIL_C[0], -8, 8, COIL_C[1], M3))                    # drum axle
    P["dock_spring_cup"] = cup
    cr = box(86, 97, -4, 4, 174.8, 182.5).union(box(97, 108, -4, 4, 174.8, 184.0))
    cr = cr.difference(hole_x(85, ROD["x1"], 0, zc0, 3.9)).difference(cyl(104, 0, 175.4, 184.5, PILOT_M3))
    P["dock_spring_carriage"] = cr
    dr = cyl_y(COIL_C[0], -2.45, 2.45, COIL_C[1], CF["drum"]).union(cyl_y(COIL_C[0], -3.25, -2.45, COIL_C[1], 9.0)).union(cyl_y(COIL_C[0], 2.45, 3.25, COIL_C[1], 9.0))
    P["dock_spring_drum"] = dr.difference(cyl_y(COIL_C[0], -4, 4, COIL_C[1], M3))
    # ---------------------------------------------------------------- electronics bay
    t = box(BAY["x0"], BAY["x1"], -BAY["y"], BAY["y"], BAY["z0"], BAY["z1"])
    t = t.difference(box(BAY["x0"] + BAY["wall"], BAY["x1"] - BAY["wall"], -BAY["y"] + BAY["wall"], BAY["y"] - BAY["wall"], BAY["z0"] + BAY["floor"], BAY["z1"] + 1))
    zf = BAY["z0"] + BAY["floor"]
    for x, y in BAY_LID_BOSSES:
        for s in (1, -1):
            t = t.union(cyl(x, s * y, zf - 0.5, BAY["z1"], 8.0)).difference(cyl(x, s * y, BAY["z1"] - INSERT_DEPTH, BAY["z1"] + 1, INSERT))
    for x, y in BAY_FLOOR_BOLTS:
        for s in (1, -1):
            t = t.difference(cyl(x, s * y, BAY["z0"] - 1, zf + 1, M3))
    ps = PERF; pxc = (ps["x0"] + ps["x1"]) / 2; pyc = (ps["y0"] + ps["y1"]) / 2
    for dy in (-ps["hole_pitch"] / 2, ps["hole_pitch"] / 2):
        t = t.union(cyl(pxc, pyc + dy, zf - 0.5, zf + ps["standoff"], 6.0)).difference(cyl(pxc, pyc + dy, zf + ps["standoff"] - INSERT_DEPTH, zf + ps["standoff"] + 1, INSERT))
    for (x0, x1, y0, y1) in ((119.5, 146.5, -35.5, -11.9), (149.5, 170.8, -40.5, -14.1), (119.5, 170.5, -95.5, -77.3)):
        rim = box(x0 - 1.2, x1 + 1.2, y0 - 1.2, y1 + 1.2, zf - 0.5, zf + 2.0).difference(box(x0, x1, y0, y1, zf - 1, zf + 3))
        t = t.union(rim)                                                               # locating rims for the taped boards
    t = t.difference(box(BAY["x0"] - 1, BAY["x0"] + BAY["wall"] + 1, CABLE_HOLE["y"] - 1.0, CABLE_HOLE["y"] + 9.0, zf, zf + 16))   # paddle cable notch (bundle 5.1 mm)
    t = t.difference(box(BAY["x0"] + BAY["wall"] + 0.5, GROOVE["x1"], GROOVE["y0"], GROOVE["y1"], BAY["z0"] - 1, zf + 1))       # switch cable from the groove
    t = t.difference(hole_x(BAY["x1"] - 3, BAY["x1"] + 1, JACK["y"], JACK["z"], JACK["hole"]))
    P["dock_bay_tray"] = t
    lid = box(BAY["x0"], BAY["x1"], -BAY["y"], BAY["y"], BAY["z1"], BAY["z1"] + BAY["lid"])
    for x, y in BAY_LID_BOSSES:
        for s in (1, -1):
            lid = lid.difference(cyl(x, s * y, BAY["z1"] - 1, BAY["z1"] + 3, M3))
    for i in range(6):                                                                 # vent slots over the charger (2.8 W at most)
        lid = lid.difference(box(122 + 4 * i, 124 + 4 * i, -40, -12, BAY["z1"] - 1, BAY["z1"] + 3))
    P["dock_bay_lid"] = lid
    return P


PRINTED = ["dock_seat_base", "dock_seat_top", "dock_spine", "dock_base_l", "dock_base_r", "dock_column_l1", "dock_column_l2",
           "dock_column_l3", "dock_column_r1", "dock_column_r2", "dock_column_r3", "dock_paddle", "dock_paddle_carrier",
           "dock_spring_cup", "dock_spring_carriage", "dock_spring_drum", "dock_bay_tray", "dock_bay_lid"]
QTY = {"dock_spring_cup": 2, "dock_spring_carriage": 2, "dock_spring_drum": 2}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    old = json.load(open(os.path.join(OUT, "parts.json"))) if os.path.exists(os.path.join(OUT, "parts.json")) else {}
    rep = {}
    for name, m in parts().items():
        m.process(validate=True)
        ext = m.extents
        path = os.path.join(OUT, name + ".stl")
        m.export(path)
        rep[name] = dict(watertight=bool(m.is_watertight), volume_cm3=round(m.volume / 1000.0, 2), extents_mm=[round(float(e), 1) for e in ext],
                         fits_220=bool(sorted(ext)[1] <= 220 and sorted(ext)[0] <= 150), bytes=os.path.getsize(path),
                         printed=name in PRINTED, qty=QTY.get(name, 1 if name in PRINTED else 0))
    json.dump(rep, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
    bad = [n for n, r in rep.items() if not (r["watertight"] and r["fits_220"])]
    print(json.dumps(rep, indent=1))
    print("BAD", bad)
