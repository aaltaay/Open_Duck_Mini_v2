#!/usr/bin/env python3
"""sit_cad.py: the CAD of the A1b alert sit (D59) in the real STLs. CAD check only (geometry), calc only (masses).

Run: python3 altaay_lab/twin/sit/sit_cad.py [--write]
--write writes the print/ STLs (mm, the slicer and viewer files), their URDF mesh copies in
mini_bdx/robots/open_duck_mini_v2/ (m, the files robot.urdf, robot.xml and the sim model load) and sit_cad.json.
Every edited part is rebuilt from its STL at sitlib.BASE_REV, so a re-run gives the same files. The joint stops are made
by construction: a stop face is placed so the two parts touch at the stop angle, and every clearance cut is the swept
volume of the moving parts over the joint range (convex pieces, hulled between poses 1 deg or less apart, grown by CLR).
Servo horns are left out of the sweeps (they turn with the part they are screwed to; the URDF keeps them on the case).

What changes (SIT_DESIGN.md changes 1, 2, 3 and 5; SIT_V2.md 3.3 changes 1 to 4; the v1 tail pad is dropped):
  shin_left_sheet, shin_right_sheet (new, 2 each): the stock knee_to_ankle sheets with the plate between the knee horn
      zone (R_HORN from the knee axis) and the ankle servo clamp moved JOG mm away from the leg centre plane, a web
      joining the horn zone to it (R_HORN to R_WEB), and the clamp left where it is with a solid block behind it: each M2
      ankle servo screw sits in a counterbore JOG deep and keeps its length. Old spacer holes closed (D39); new spacer
      holes as the stock hole (3.2 through, 6.5 recess 2.0 deep). The clamp's front corner is relieved for the thigh
      spacer at the fold.
  shin_spacer (new, 2): at the back edge, SPACER_GROW longer, 2 heat-set inserts per end on one pattern (D42); its front
      face is parallel to the knee servo case front face at knee 150, KNEE_STACK away.
  knee_bumper (new, TPU 95A, 2): flat pad on VHB 4950 on that face: the knee stop at 150.
  knee_to_ankle_left_sheet, knee_to_ankle_right_sheet: the thigh sheets only now (2 each), trimmed where the shin clamp
      passes at the fold (130 to 150 deg).
  foot_top, foot_side: notched where the shin clamp and the ankle servo case pass down to -95 (the heel notch), with a
      flat seat for an ankle pad on each plate.
  ankle_pad (new, TPU, 4): the ankle stop at -95, under the two shin clamp blocks.
  left_cache, right_cache: recessed where the joggled shin, the ankle servo and the foot pass (knee -25 to 150, the sit
      and stand path), and where the hip pad lands at hip pitch -75.
  left_roll_to_pitch, right_roll_to_pitch: the outward hip roll stop lug (8 deg) against roll_motor_bottom; a seat for
      the hip pad on the top face.
  hip_pad (new, TPU, 2): the hip pitch stop at -75 against the cover top.
  neck_stop (new, PLA, 1) and neck_pad (new, TPU, 2): the neck back stop at +25. A printed block on trunk_top behind the
      neck, one pillar each side joined by a bar over the cable run, held by the hip yaw servo screws F127 and F129
      (M2x6 to M2x12 through a FLANGE_T flange, the same thread engagement); each pillar carries a TPU face in a pocket
      that the stock neck sheet's back edge meets at +25 at NECK_R_MIN or more from the neck axis (the sheet is loaded
      in its plane). The neck sheets are the stock parts again (the D59 lugs are gone; the builder puts the stock STLs
      back).
  head_pad (new, TPU, 1) and head_pitch_to_yaw: the head forward stop at -25. A printed hook on the left arm of the yoke
      (the side without the neck cables) reaching down in front of the left neck sheet, with a TPU face in a pocket that
      the sheet's front edge meets at -25 (in-plane again), at twice the radius of the old lug; the old lug on the servo
      top is gone. F222 and the horn screws are nowhere near it.
  sit_seat (new, TPU, 1) and sit_bumper (new, TPU, 1): under the rear and the front of body_middle_bottom on VHB.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE_CAD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE_CAD)
import sitlib as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SH, TH, FT = "knee_and_ankle_assembly_2", "knee_and_ankle_assembly", "foot_assembly"
RP, HR, NK, HP, TR = "left_roll_to_pitch_assembly", "hip_roll_assembly", "neck_pitch_assembly", "head_pitch_to_yaw", "trunk_assembly"
CLR = 0.8                       # clearance of every cut to a part that moves past (printed tolerance plus margin)
R_WEB = 18.4                    # outer radius of the joggle web (the thigh sheet ends 19.0 mm from the knee axis)
Z_CLAMP = -119.6                # the servo clamp of the shin sheet starts below this z (zero pose, left shin)
OVL = 0.37                      # overlap of the joggle pieces (radially and at the clamp line)
VHB_T = 1.1                     # BOM 29 VHB 4950, 1.1 mm (D35)
PAD_T = 3.0                     # TPU 95A pad thickness
STACK = VHB_T + PAD_T           # a pad face touches its counterpart at the stop
SPACER_Y = (71.95 - 9.0 + 0.10, 109.05 + 9.0 - 0.20)       # the stock gaps to the plate faces (0.10 and 0.20 mm)
SPACER_Z = (-116.5, -97.5)
SPACER_BACK = ((-48.0, -97.5), (-50.0, -116.5))            # follows the sheet back edge (ray cast, 0.7 mm inside)
SPACER_HOLES = [(-44.0, -104.0), (-39.5, -112.9)]          # one pattern on both ends (D42); 2 inserts per end
INSERT_BORE, INSERT_DEPTH = 4.0, 5.8                       # as the stock leg_spacer (audit/sites.json)
SHEET_HOLE, SHEET_RECESS, RECESS_DEPTH = 3.2, 6.5, 2.0     # as the stock sheet at the spacer (audit/sites.json)
OLD_SPACER_HOLES = [(-27.1, -99.0), (-43.1, -99.0)]
M2_HEAD_CB = 5.0                # the stock M2 pan head recess (feat3d: 5.0 mm), continued out through the clamp block
KNEE = np.array([-35.06, -78.72])
ANKLE = np.array([-35.06, -157.37])
HORNS = ("drive_palonier", "passive_palonier")
# lug regions (world zero pose, mm): the box a lug may fill; the sweep of the counterpart over the free range carves it
ROLL_LUG = ((-16.0, 50.0, 2.0), (-2.0, 62.8, 11.6))         # on left_roll_to_pitch, front of the D3/SP4/S3 loop; 14 mm wide in x
                                                             # (the first cut was 10: the root grown for the energy loads, SIT.md 4)
ROLL_PAD_DIMS = (12.0, 9.0, PAD_T)                           # the TPU face on the lug: the box round the touch (along the case's edge, across it), thick
LUG_CLR = 0.8                                                # the lug as built stands this far behind the case's path: only the pad touches
                                                             # (0.4 grazed the case 0.5 deg past the stop: sitlib.dilate covers 0.82 of it and
                                                             # the STL's pinch fills stand 0.2 mm proud)
PAD_SET = 0.1                                                # the pad face this far behind the case's path at the stop (the STL's pinch fills stand up
                                                             # to 0.2 mm proud, sitlib.finalize): the case meets the pad within 0.5 deg of the stop
# the neck back stop block (world, mm): footprint on trunk_top (z 85.8 flat from x -59 to -21), the pillars outboard of
# the cable run (|y| >= NECK_TUNNEL_Y under z NECK_TUNNEL_Z: the trunk-side neck loops lie on trunk_top at z 89, y -11 to
# +13 over this x range, cables3d.json), the flange over the F127 and F129 seats
NECK_BLOCK = dict(x=(-56.0, -18.0), y=29.0, z_top=116.0)
NECK_FOOT = dict(x=-42.0, y=22.0)                            # behind x -42 the block is a FLANGE_T foot on trunk_top (flat to x -58 at
                                                             # |y| 22; the F126/F128 recesses start at |y| 22.4): the tip pivot of the pad
                                                             # load sits at its back edge, 28.7 mm behind the screws, and with the pad low
                                                             # on the sheet's edge the load's line passes in front of it, so the screws
                                                             # carry no pull-out at the stop (sit_stress.py neck rows)
NECK_TUNNEL_Y, NECK_BAR_Z, NECK_BAR_X = 15.0, (100.0, 108.0), -32.0    # the bar joining the pillars over the cable run
# the hip yaw servo cable windows in trunk_top (x -36.5 to -30, y 23.9 to 46 and its mirror, S2 and S7 come up through
# them, cables3d.json): no block material over them (feat3d does not list them as holes, so the keep-out is written here)
CABLE_WINDOW = ((-43.0, -29.5), (23.4, 47.0))            # and nothing of the block outboard of the pillars behind them: S2 and S7 run
                                                             # back from the windows at y 30 to 33, z 82 to 89 (C3 found a 1.2 mm rub)
SHELL_CLR = 0.5                                              # the block to the body shell's roof (same link, a printed fit)
ROOF_OPEN_Y, ROOF_Z = 25.0, 104.0                            # the shell's neck opening half width and its roof's underside (sections)
NECK_SCREWS = ((-27.301, -24.749), (-27.301, 24.751))        # F127, F129 seat x, y (fasteners.json), axis -z
NECK_SCREW_SEAT_Z = 83.791                                   # the stock seat (2.0 mm down in the trunk_top recess)
FLANGE_T = 4.0                                               # the block flange over trunk_top: the new seat is z 85.8 + 4.0
CB_D, SHANK_D = 4.6, 2.5                                     # counterbore over the M2 pan head (dk 4.0), shank hole as the stock 2.5
NECK_R_MIN = 23.0                                            # the pad starts here along the sheet's back edge (from the neck axis): the
                                                             # stock edge is straight from r 19 to 35 (32 deg off vertical) and again from
                                                             # r 35 to the top corner at 48.5 (25 deg); the pad sits on the lower run (a
                                                             # short pillar, a small tip moment), the line fit over the pad's own run
NECK_FIT_R = 12.0                                            # the edge points fitted: r NECK_R_MIN to NECK_R_MIN + this
NECK_PAD_DIMS = (10.0, 6.0, PAD_T)                           # along the edge, across the sheet (its back edge is 6.1 wide), thick
POCKET = 2.5                                                 # a pad sits in a pocket this deep (the pocket walls take the slide)
# the head forward stop hook on the left arm of head_pitch_to_yaw (world, yoke zero pose): the region it may fill, three
# boxes: a doubler over the arm's whole outer face (y 23.2, x -12 to 12, z 146 to 170.5: the head yaw bracket sweeps z 170.9
# up; the first cut was x 4 to 12, its root failed the free forward shove, SIT.md 4; the horn screw counterbores run through it),
# its drop outboard of the left neck sheet down to z 128, and a foot forward under z 147 (the head floor, rolled 27 deg,
# sweeps z 148 up at x 13.4 and beyond) that carries the TPU face in front of the sheet's front edge
HEAD_HOOK = dict(doubler=((-12.0, 22.8, 146.0), (12.0, 27.2, 170.5)), drop=((4.0, 22.8, 128.0), (13.4, 27.2, 147.0)),
                 foot=((12.0, 16.0, 128.0), (38.0, 27.2, 147.0)))       # the doubler bites 0.4 mm into the arm (y 23.2) so the union is one body
HEAD_PAD_Z = (125.0, 137.0)                                  # the sheet's front edge band the pad meets (world z, neck zero pose)
HEAD_PAD_T = 10.0                                            # a thick TPU face: 0.3 of the stack stiffness of 3 mm (the head stop sees the free head's
                                                             # forward whip; 6 mm in the first cut)
SEAT = dict(x=-110.0, z_low=-66.0, r=16.0, half_y=40.0)     # SIT_V2.md 3.3: lowest point 66 mm under the trunk origin
BUMPER = dict(x=20.0, z_low=-69.0, r=12.0, half_y=30.0)     # SIT_V2.md 3.3: 3 mm off the floor in the sit
SIT_BODY_SPLIT_X = -115.0       # the seat is glued to body_middle_bottom only (body_back comes off for the battery)


# ---------------------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------------------
def link_meshes(S, link, skip_prefix=HORNS, keys=None):
    """the parts of a link (world zero pose); every servo case comes with its inside filled (c3d_lib.SERVO_INNER, the
    servo body inside the cups), as the sweep and the v1 study model it"""
    out = {}
    for i in S.inst:
        if i["link"] != link or i["key"].startswith(skip_prefix) or (keys is not None and i["key"] not in keys):
            continue
        out["%s#%d" % (i["key"], i["idx"])] = S.world_mesh(i)
        if i["key"] == "servo_bottom":
            (x0, x1), (y0, y1), (z0, z1) = L.c3d_lib.SERVO_INNER
            b = L.box((x0, y0, z0), (x1, y1, z1))
            b.apply_transform(S.T0[i["link"]] @ i["T"])
            out["servo_fill#%d" % i["idx"]] = b
    return out


def pieces_of(meshes, slab=3.0):
    out = []
    for m in (meshes.values() if isinstance(meshes, dict) else meshes):
        out += L.convex_pieces(m, slab=slab)
    return out


def sweep_T(S, moving, fixed, cfgs):
    return [L.rel_T(S, c, moving, fixed) for c in cfgs]


def cut_by(target, pieces, Ts, clearance, cells=None):
    """target minus the swept hulls; returns (new target, removed volume)"""
    near = L.bbox_of(target, 2.0 + clearance)
    C = L.swept_cut(pieces, Ts, clearance, cells=cells, near=near)
    new = target - C
    return new, float(target.volume() - new.volume())


def angles(a0, a1, step=1.0):
    n = max(1, int(np.ceil(abs(a1 - a0) / step)))
    return list(np.linspace(a0, a1, n + 1))


# ---------------------------------------------------------------------------------------------------------------
# shin sheets, spacer, knee bumper
# ---------------------------------------------------------------------------------------------------------------
def knee_case_plane(S, knee_deg):
    """the knee servo case front face (thigh x max) at knee_deg in the left shin zero-pose frame: unit normal n (out of
    the case, xz) and offset c (the case is n.p <= c)"""
    T = L.rel_T(S, L.cfg_left(k=knee_deg, both=False), TH, SH)
    a = np.radians(180.0 - knee_deg)
    n = np.array([-np.cos(a), 0.0, -np.sin(a)])
    P = np.vstack([S.world_mesh(i).vertices for i in S.inst if i["link"] == TH and i["key"].startswith("servo")])
    P = P @ T[:3, :3].T + T[:3, 3]
    return n, float((P @ n).max())


def joggle_sheet(S, key):
    """world (left leg zero pose) manifold of the joggled shin sheet and its construction pieces"""
    i = L.inst(S, SH, key)
    Tw = L.inst_world(S, i)
    base = L.base_mesh("print/%s.stl" % key)
    base.apply_transform(Tw)
    n = 1.0 if "left" in key else -1.0                       # away from the leg centre plane (part +y / -y, both legs)
    W = L.to_man(base)
    big = 400.0
    kx, kz = KNEE
    C0 = L.to_man(L.cyl((kx, -big, kz), (kx, big, kz), L.R_HORN, 160))
    C1 = L.to_man(L.cyl((kx, -big, kz), (kx, big, kz), R_WEB, 160))
    C0i = L.to_man(L.cyl((kx, -big, kz), (kx, big, kz), L.R_HORN - OVL, 160))
    C1i = L.to_man(L.cyl((kx, -big, kz), (kx, big, kz), R_WEB - OVL, 160))
    below = L.to_man(L.box((-big, -big, -big), (big, big, Z_CLAMP)))
    below_o = L.to_man(L.box((-big, -big, -big), (big, big, Z_CLAMP + OVL)))
    # every piece overlaps the next by OVL so no two faces of the union coincide (coincident faces pinch on a round trip)
    horn = W ^ C0
    band = (W ^ C1) - C0i - below
    plate = W - C1i - below
    clamp = (W ^ below_o) - C0

    # the web and the clamp block are prisms of their pieces' shadows (flat faces: a swept union would leave 1.3 mm
    # steps on every chamfer and smear the outer-face reliefs into thin fins)
    y_in0, y_out0 = (109.05, 112.95) if n > 0 else (71.95, 68.10)      # stock inner and outer plate faces
    y_in = y_in0 + n * L.JOG
    y_out = y_out0 + n * L.JOG
    web = L.prism_y(band, min(y_in0, y_out), max(y_in0, y_out))
    # the block: the stock clamp as it is (its inner face fits the servo case) plus a slab from its outer face out JOG
    slab = L.prism_y(clamp, min(y_out0 - n * OVL, y_out0 + n * L.JOG), max(y_out0 - n * OVL, y_out0 + n * L.JOG))
    block = L.union([clamp, slab])
    plate_j = plate.translate((0.0, n * L.JOG, 0.0))
    new = L.union([horn, web, plate_j, block])
    lo, hi = min(y_in, y_out), max(y_in, y_out)
    for (x, z) in OLD_SPACER_HOLES:                           # D39: no empty hole; plugs flush with both plate faces
        new = new + L.to_man(L.cyl((x, lo, z), (x, hi, z), SHEET_RECESS / 2 + 0.4))
    holes = []
    for (x, z) in SPACER_HOLES:
        new = new - L.to_man(L.cyl((x, lo - 1, z), (x, hi + 1, z), SHEET_HOLE / 2))
        new = new - L.to_man(L.cyl((x, y_out - n * RECESS_DEPTH, z), (x, y_out + n * 1.0, z), SHEET_RECESS / 2))
        holes.append(dict(x=x, z=z, y_outer_face=L.r(y_out, 2), recess_floor=L.r(y_out - n * RECESS_DEPTH, 2)))
    zc = -128.4 if n > 0 else -124.6
    y_cb0 = y_out0                                            # the stock outer face over the M2 head recess
    cbs = []
    for x in (-24.8, -45.3):
        # the stock head recess (5.0 mm) runs on out through the slab: same seat, the driver comes in along the axis
        new = new - L.to_man(L.cyl((x, y_cb0 - n * 0.5, zc), (x, y_cb0 + n * (L.JOG + 1.0), zc), M2_HEAD_CB / 2))
        cbs.append(dict(x=x, z=zc, recess_d=M2_HEAD_CB, from_y=L.r(y_cb0, 2), depth_added=L.JOG))
    info = dict(spacer_holes=holes, counterbores=cbs, plate_faces_y=[L.r(lo, 2), L.r(hi, 2)])
    return new, dict(horn=horn, web=web, plate=plate_j, block=block), Tw, info


def shin_spacer(S):
    """world (left shin zero pose) manifolds of the new shin spacer and the TPU knee bumper on its front face"""
    n, c = knee_case_plane(S, L.STOPS["knee_fold"]["stop"])
    nx, nz = n[0], n[2]
    face = c + STACK
    z0, z1 = SPACER_Z
    xa = (face - nz * z1) / nx
    xb = (face - nz * z0) / nx
    from shapely.geometry import Polygon
    poly = [SPACER_BACK[0], (xa, z1), (xb, z0), SPACER_BACK[1]]
    y0, y1 = SPACER_Y
    pr = trimesh.creation.extrude_polygon(Polygon(poly), y1 - y0)
    pr.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0], [0, 0, 0, 1.0]]))
    if pr.volume < 0:
        pr.invert()
    sp = L.to_man(pr)
    for (x, z) in SPACER_HOLES:
        sp = sp - L.to_man(L.cyl((x, y0 - 1, z), (x, y0 + INSERT_DEPTH, z), INSERT_BORE / 2))
        sp = sp - L.to_man(L.cyl((x, y1 - INSERT_DEPTH, z), (x, y1 + 1, z), INSERT_BORE / 2))
    t = np.array([-nz, 0.0, nx])
    if t[2] > 0:
        t = -t
    s_top, s_bot = float(np.array([xa, 0, z1]) @ t), float(np.array([xb, 0, z0]) @ t)
    s_mid = 0.5 * (s_top + s_bot) + 1.0
    p0 = t * s_mid + n * (face - (t * s_mid) @ n)
    pad_c = p0 - n * (VHB_T + PAD_T / 2) + np.array([0, 0.5 * (74.0 + 105.7), 0])
    R = np.c_[t, [0, 1.0, 0], np.cross(t, [0, 1.0, 0])]
    if np.linalg.det(R) < 0:
        R[:, 2] = -R[:, 2]
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = pad_c
    info = dict(case_face_normal_xz=[L.r(nx, 4), L.r(nz, 4)], case_face_offset_at_150=L.r(c, 3), spacer_face_offset=L.r(face, 3),
                section_xz=[[L.r(a, 2), L.r(b, 2)] for a, b in poly], y=[L.r(y0, 2), L.r(y1, 2)], length=L.r(y1 - y0, 2),
                inserts=[dict(x=x, z=z, bore=INSERT_BORE, depth=INSERT_DEPTH) for (x, z) in SPACER_HOLES])
    return sp, T, (14.0, 28.0, PAD_T), info


def pad_mesh(dims):
    return trimesh.creation.box(extents=dims)


def move_heel_screw(S, key, m_world):
    """the foot plate with its heel screw hole stack moved HEEL_DX in x (plugged at the old place); world zero pose"""
    Tw = L.inst_world(S, L.inst(S, FT, key))
    feats = []
    for f in L.hole_features(L.from_man(L.xform(L.to_man(m_world), np.linalg.inv(Tw)))):
        p0, p1 = (Tw @ np.r_[f["p0"], 1])[:3], (Tw @ np.r_[f["p1"], 1])[:3]
        if abs(p0[0] - HEEL_OLD[0]) < 1.0 and abs(p0[2] - HEEL_OLD[1]) < 1.0 and abs(p1[0] - p0[0]) < 0.05:
            feats.append((f["d"], p0, p1))
    if not feats:
        raise SystemExit("%s: no heel screw hole at x %.2f z %.2f" % (key, HEEL_OLD[0], HEEL_OLD[1]))
    M = L.to_man(m_world)
    M = L.union([M] + [L.to_man(L.cyl(p0, p1, d / 2 + 0.3, 48)) for d, p0, p1 in feats])        # D39 plug
    for d, p0, p1 in feats:
        a = (p1 - p0) / np.linalg.norm(p1 - p0)
        dx = np.array([HEEL_DX, 0.0, 0.0])
        M = M - L.to_man(L.cyl(p0 + dx - 0.05 * a, p1 + dx + 0.05 * a, d / 2, 48))
    return L.solid(M), [dict(d=L.r(d, 2), y=[L.r(p0[1], 2), L.r(p1[1], 2)]) for d, p0, p1 in feats]


# ---------------------------------------------------------------------------------------------------------------
# lugs by carving: a region on the host, minus everything the counterparts sweep over the free range
# ---------------------------------------------------------------------------------------------------------------
def carve_lug(S, host_link, host, region, counter, cfg_of, free, step=0.5, clr=0.0):
    """host: manifold (world zero pose of host_link); region: box lo, hi; counter: {link: {name: mesh}};
    free: (a0, a1) the free range of the joint; clr: clearance to everything that passes (0: the lug's face is the
    counterpart's own envelope at the stop); returns the lug (new material only)"""
    R = L.to_man(L.box(*region))
    near = (np.asarray(region[0]) - 2.0 - clr, np.asarray(region[1]) + 2.0 + clr)
    cutters = []
    angs = angles(free[0], free[1], step)
    for ln, ms in counter.items():
        Ts = sweep_T(S, ln, host_link, [cfg_of(a) for a in angs])
        cutters.append(L.swept_cut(pieces_of(ms, 2.0), Ts, clr, near=near))
    lug = (R - L.union(cutters)) - host
    ko = L.hole_keepout(L.from_man(host))      # never over a hole, a recess or the driver's way to a screw
    if ko is not None:
        lug = lug - ko
    comps = sorted(lug.decompose(), key=lambda m: -m.volume())
    # keep the pieces that touch the host (a lug must grow from it)
    keep = [cm for cm in comps if (L.dilate(cm, 0.2) ^ host).volume() > 0.5]
    return L.union(keep)


def roll_pad(S, RPM, lug0, lugc, counter, rst):
    """the TPU face on the hip roll lug, conformal: the carved lug's face at the stop is the case corner's own envelope
    (zero clearance at the stop), and the pad is the case's path from the stop PAD_T deeper into the lug (the arc PAD_T
    at the touch radius), the pocket its path PAD_T + VHB_T deeper, both within a local box round the touch. So the
    whole corner region bears on the pad, as it did on the lug, and the pad's outer face is where the lug's was: the
    stop stays where it was. Returns the lug, the pad (manifold, world), its frame (world 4x4) and the record."""
    D = np.radians
    lug = lug0
    past = rst - 0.5
    T = L.rel_T(S, {"left_hip_roll": D(past)}, HR, RP)
    T2 = L.rel_T(S, {"left_hip_roll": D(past - 0.5)}, HR, RP)
    ov = []
    for ms in counter[HR].values():
        X = L.xform(L.to_man(ms), T) ^ lug
        if X.volume() > 1e-3:
            ov.append((X.volume(), L.from_man(X).center_mass))
    if not ov:
        raise SystemExit("roll pad: the lug does not touch the hip roll link 0.5 deg past the stop")
    v = np.array([o[0] for o in ov])
    cpt = (np.array([o[1] for o in ov]) * v[:, None]).sum(0) / v.sum()
    p1 = (T2 @ np.linalg.inv(T) @ np.r_[cpt, 1.0])[:3]
    fdir = p1 - cpt
    fdir = fdir / np.linalg.norm(fdir)                         # the case's motion at the touch: the force on the lug
    n = -fdir                                                  # the pad's mean normal, toward the incoming case
    ax_p, ax_d = S.joint_world("left_hip_roll")
    r_pad = float(np.linalg.norm(np.cross(cpt - ax_p, ax_d)))
    ex = np.array([1.0, 0.0, 0.0]) - n[0] * n                 # along the case's edge (x), in the mean face plane
    ex = ex / np.linalg.norm(ex)
    Tf = frame_T(cpt, ex, np.cross(-n, ex))                   # third axis = -n: into the lug (the pad's part frame)
    if np.dot(Tf[:3, 2], -n) < 0.999:
        raise SystemExit("roll pad: pad frame")
    a, b = ROLL_PAD_DIMS[0], ROLL_PAD_DIMS[1]
    deep = PAD_T + VHB_T + 2.0
    local = L.to_man(L.box((-a / 2, -b / 2, -6.0), (a / 2, b / 2, deep))).transform(Tf[:3, :4])
    local_pad = L.to_man(L.box((-a / 2 + 0.15, -b / 2 + 0.15, -6.0), (a / 2 - 0.15, b / 2 - 0.15, deep))).transform(Tf[:3, :4])
    hr_pc = pieces_of(counter[HR], 2.0)
    near = L.bbox_of(lug, 2.0 + deep)
    t_ang, s_ang = np.degrees(PAD_T / r_pad), np.degrees((PAD_T + VHB_T) / r_pad)     # the arcs of the skin and the stack
    d_ang = np.degrees(PAD_SET / r_pad)                                                # the pad face's set behind the stop

    def path(a0, a1):
        Ts = sweep_T(S, HR, RP, [L.cfg_left(roll=x_, both=False) for x_ in angles(a0, a1, 0.25)])
        return L.swept_cut(hr_pc, Ts, 0.0, near=near)
    pad = (path(rst - d_ang - t_ang, rst - d_ang) ^ lug0) ^ local_pad      # the case's path from PAD_SET behind the stop PAD_T deeper: the skin
    stack = (path(rst - d_ang - s_ang, rst) ^ lug0) ^ local                # to PAD_T + VHB_T deeper: the pocket, open to the stop
    if pad.volume() < 0.5 * a * b * PAD_T * 0.3:
        raise SystemExit("roll pad: the skin is %.1f mm3 only" % pad.volume())
    lug = lugc - stack                                        # the lug as built: LUG_CLR behind the case's path, the pocket cut
    comps = sorted(lug.decompose(), key=lambda m: -m.volume())
    keep = [cm for cm in comps if (L.dilate(cm, 0.2) ^ RPM).volume() > 0.5]
    if not keep:
        raise SystemExit("roll pad: nothing of the lug is left on roll_to_pitch")
    lug = L.union(keep)
    pcs = sorted(pad.decompose(), key=lambda m: -m.volume())
    if len(pcs) != 1:
        pad = pcs[0]
    if (pad ^ lug).volume() > 1e-3 or (pad ^ RPM).volume() > 1e-3:
        raise SystemExit("roll pad: the pad overlaps the lug or roll_to_pitch")
    # the pad's bearing on the case: the case's overlap with the pad grows from 0.5 to 1.0 deg past the stop by area x r x 0.5 deg
    def overlap_at(ang):
        Ta = L.rel_T(S, {"left_hip_roll": D(ang)}, HR, RP)
        return sum((L.xform(L.to_man(ms), Ta) ^ pad).volume() for ms in counter[HR].values())
    v1, v2 = overlap_at(past), overlap_at(past - 0.5)
    bearing = float((v2 - v1) / (r_pad * D(0.5)))
    if bearing < 10.0:
        raise SystemExit("roll pad: the case meets the pad on %.1f mm2 only" % bearing)
    pb = np.asarray(pad.bounding_box())
    info = dict(lug_mm3=L.r(lug.volume(), 1), pad_face_centre=np.round(cpt, 2).tolist(), pad_normal=np.round(n, 4).tolist(),
                pad_r_mm=round(r_pad, 2), pad_box=list(ROLL_PAD_DIMS), pad_mm3=L.r(pad.volume(), 1), pad_bbox=np.round(pb, 1).tolist(),
                skin_deg=round(float(t_ang), 2), stack_deg=round(float(s_ang), 2), bearing_mm2=round(bearing, 1), touch_mm3=round(float(v.sum()), 2),
                case_motion=np.round(fdir, 3).tolist(), lug_clr_mm=LUG_CLR, pad_set_mm=PAD_SET, pad_set_deg=round(float(d_ang), 2),
                kind="conformal: the case corner's path from %.1f mm behind the stop %.1f mm deeper, in a %.0f x %.0f box; the lug %.1f mm behind the path" % (PAD_SET, PAD_T, a, b, LUG_CLR))
    return lug, pad, Tf, info


def halfspace(point, normal, size=400.0):
    """manifold box of the half space {p: normal . (p - point) >= 0}"""
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    a = np.array([0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(n, a); e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    T = np.eye(4)
    T[:3, :3] = np.c_[e1, e2, n]
    T[:3, 3] = np.asarray(point, float) + n * (size / 2)
    return L.to_man(L.box((-size / 2, -size / 2, -size / 2), (size / 2, size / 2, size / 2), T))


def frame_T(origin, ex, ey):
    """4x4 with columns ex, ey, ex x ey (unit), at origin"""
    ex = np.asarray(ex, float) / np.linalg.norm(ex)
    ey = np.asarray(ey, float) - np.dot(ey, ex) * ex
    ey /= np.linalg.norm(ey)
    T = np.eye(4)
    T[:3, :3] = np.c_[ex, ey, np.cross(ex, ey)]
    T[:3, 3] = origin
    return T


def grid_pieces(m, lo, hi, cell=10.0):
    """point sets of a mesh cut into cell x cell columns (z through) inside the box lo..hi: for a part with a hole or a
    hollow (the head floor, the body shell) whose z slabs' convex hulls would fill it; each column's hull is close to
    the part (a chord of at most cell across a curve)"""
    M = L.to_man(m) if isinstance(m, trimesh.Trimesh) else m
    M = M ^ L.to_man(L.box(lo, hi))
    out = []
    if M.volume() < 0.5:
        return out
    b = np.asarray(M.bounding_box(), float)
    for x in np.arange(b[0], b[3], cell):
        for y in np.arange(b[1], b[4], cell):
            c = M ^ L.to_man(L.box((x, y, b[2] - 1), (x + cell, y + cell, b[5] + 1)))
            if c.volume() > 0.5:
                out.append(np.asarray(c.to_mesh().vert_properties, float)[:, :3])
    return out


def downstream_links(S, link):
    sub = {link}
    grow = True
    while grow:
        grow = False
        for j in S.u.robot.joints:
            if j.parent in sub and j.child not in sub:
                sub.add(j.child)
                grow = True
    sub.discard(link)
    return sub


def stock_sheets(S):
    """the stock neck sheets (world zero pose, from BASE_REV: the repo files may still carry the old lugs)"""
    out = {}
    for key in ("neck_left_sheet", "neck_right_sheet"):
        m = L.base_mesh("print/%s.stl" % key)
        m.apply_transform(L.inst_world(S, L.inst(S, NK, key)))
        out[key] = m
    return out


def neck_counter(S, sheets):
    """the neck link as the sweeps see it: the stock sheets and the head pitch servo case (filled), horns left out"""
    c = dict(link_meshes(S, NK, keys=("servo_top", "servo_mid", "servo_bottom")))
    c.update({k: v for k, v in sheets.items()})
    return c


def neck_block(S, log=print):
    """the neck back stop: block, pad placements (world 4x4, left then right), info. CAD check only."""
    t0 = time.time()
    D = np.radians
    nst = L.STOPS["neck_back"]["stop"]
    ax_p, ax_d = S.joint_world("neck_pitch")
    sheets = stock_sheets(S)
    # the left sheet's back edge at the stop: the backmost points per z bin, the ones NECK_R_MIN or more from the axis
    T25 = L.rel_T(S, {"neck_pitch": D(nst)}, NK, TR)
    sh = sheets["neck_left_sheet"].copy()
    sh.apply_transform(T25)
    # sections of the posed sheet (an STL has vertices at corners only): the backmost point of each cut in the band
    edge, ys = [], []
    for z0 in np.arange(100.0, 128.0, 0.5):
        sec = sh.section(plane_origin=[0, 0, z0], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        pts = np.vstack([np.asarray(l) for l in sec.discrete])
        pts = pts[(pts[:, 1] > 16.0) & (pts[:, 1] < 22.25)]     # the back face spans y 16.1 to 22.2; the outer skin steps forward
        if not len(pts):
            continue
        q = pts[np.argmin(pts[:, 0])]
        rr = np.linalg.norm(np.cross(q - ax_p, ax_d))
        if rr >= NECK_R_MIN:
            edge.append(q)
            ys.append(pts[pts[:, 0] < q[0] + 0.15][:, 1])
    edge = np.array(edge)
    if len(edge) < 10:
        raise SystemExit("neck block: too few back edge points past r %.0f" % NECK_R_MIN)
    rs = np.linalg.norm(np.cross(edge - ax_p, ax_d), axis=1)
    k = int(np.argmax(rs))                                   # the top back corner is the farthest point: above it the cut
    edge, ys = edge[:k + 1], ys[:k + 1]                      # runs along the top edge, not the back edge
    rs = rs[:k + 1]
    sel = rs <= NECK_R_MIN + NECK_FIT_R                      # the pad's own run of the edge (it kinks at r 35)
    edge, ys = edge[sel], [y_ for y_, s_ in zip(ys, sel) if s_]
    if len(edge) < 10:
        raise SystemExit("neck block: too few back edge points between r %.0f and %.0f" % (NECK_R_MIN, NECK_R_MIN + NECK_FIT_R))
    # the edge line in the x z plane (the backmost section point sits at either end of the back face in y)
    exz = edge[:, [0, 2]]
    c0 = np.array([exz[:, 0].mean(), 0.0, exz[:, 1].mean()])
    u, sv, vt = np.linalg.svd(exz - exz.mean(0))
    e2 = vt[0] / np.linalg.norm(vt[0])
    e = np.array([e2[0], 0.0, e2[1]])
    if e[2] < 0:
        e = -e
    resid = np.abs(np.cross(edge - c0, e)[:, 1]).max()
    if resid > 0.25:
        raise SystemExit("neck block: the sheet's back edge at +%.0f is not a straight line in the x z plane (resid %.2f)" % (nst, resid))
    n = np.array([e[2], 0.0, -e[0]])                        # normal to the edge in the x z plane, pointing forward and up
    if n[0] < 0:
        n = -n
    # the pad along the edge from its lowest point (r >= NECK_R_MIN) up
    tpar = (edge - c0) @ e
    lo_pt = c0 + e * tpar.min()
    if tpar.max() - tpar.min() < NECK_PAD_DIMS[0] - 0.5:
        raise SystemExit("neck block: the edge past r %.0f is %.1f mm, the pad %.1f" % (NECK_R_MIN, tpar.max() - tpar.min(), NECK_PAD_DIMS[0]))
    yy = np.concatenate(ys)
    y_band = (float(yy.min()), float(yy.max()))
    yc = 0.5 * (y_band[0] + y_band[1])
    face_c = lo_pt + e * (NECK_PAD_DIMS[0] / 2)             # the pad face centre, on the edge line
    face_c[1] = yc
    r_pad = float(np.linalg.norm(np.cross(face_c - ax_p, ax_d)))
    Tpad_L = frame_T(face_c - n * (NECK_PAD_DIMS[2] / 2), e, [0, 1, 0])   # third axis = e x y = -n (into the block)
    if np.dot(Tpad_L[:3, 2], -n) < 0.999:
        raise SystemExit("neck block: pad frame")
    # the block: box, the cable tunnel, the face plane (POCKET - PAD_T - VHB_T behind the pad face), the pockets
    bx = NECK_BLOCK
    B = L.to_man(L.box((bx["x"][0], -bx["y"], 85.0), (bx["x"][1], bx["y"], bx["z_top"])))
    x0, x1 = bx["x"][0] - 1, bx["x"][1] + 1
    B = B - L.to_man(L.box((x0, -NECK_TUNNEL_Y, 80.0), (x1, NECK_TUNNEL_Y, NECK_BAR_Z[0])))       # the cable lane
    B = B - L.to_man(L.box((x0, -NECK_TUNNEL_Y, NECK_BAR_Z[1]), (x1, NECK_TUNNEL_Y, bx["z_top"] + 1)))
    B = B - L.to_man(L.box((NECK_BAR_X, -NECK_TUNNEL_Y, 80.0), (x1, NECK_TUNNEL_Y, bx["z_top"] + 1)))
    for sgn in (1.0, -1.0):                                       # the servo cable windows
        (wx0, wx1), (wy0, wy1) = CABLE_WINDOW
        B = B - L.to_man(L.box((wx0, min(sgn * wy0, sgn * wy1), 80.0), (wx1, max(sgn * wy0, sgn * wy1), bx["z_top"] + 1)))
        # outside the body shell's neck opening (|y| 25) the block stays under the shell's roof (z 104): the shell is
        # fitted over the block from above, so nothing of ours may stand above the roof there
        B = B - L.to_man(L.box((x0, min(sgn * (ROOF_OPEN_Y - CLR), sgn * 60.0), ROOF_Z - SHELL_CLR), (x1, max(sgn * (ROOF_OPEN_Y - CLR), sgn * 60.0), bx["z_top"] + 1)))
    # behind NECK_FOOT x the block is a flange foot FLANGE_T thick, |y| to NECK_FOOT y: the tip pivot at its back edge
    B = B - L.to_man(L.box((x0, -60.0, 85.8 + FLANGE_T), (NECK_FOOT["x"], 60.0, bx["z_top"] + 1)))
    for sgn in (1.0, -1.0):
        B = B - L.to_man(L.box((x0, min(sgn * NECK_FOOT["y"], sgn * 60.0), 80.0), (NECK_FOOT["x"], max(sgn * NECK_FOOT["y"], sgn * 60.0), bx["z_top"] + 1)))
    face_off = PAD_T + VHB_T - POCKET                          # the block's outer face behind the pad face
    B = B - halfspace(face_c - n * face_off, n)
    pads, pockets = [], []
    for Tp in (Tpad_L, MIRROR @ Tpad_L @ MIRROR):
        pk = L.to_man(L.box((-NECK_PAD_DIMS[0] / 2 - 0.2, -NECK_PAD_DIMS[1] / 2 - 0.2, face_off - 0.01),
                            (NECK_PAD_DIMS[0] / 2 + 0.2, NECK_PAD_DIMS[1] / 2 + 0.2, PAD_T + VHB_T + 0.01)))
        Tf = Tp.copy()
        Tf[:3, 3] = Tp[:3, 3] - Tp[:3, 2] * (NECK_PAD_DIMS[2] / 2)   # back to the face plane
        pockets.append(pk.transform(Tf[:3, :4]))
        pads.append(Tp)
    B = B - L.union(pockets)
    # screw passages: counterbore from the flange seat up (open above: the driver comes in from the top), shank hole below
    seat_z = 85.8 + FLANGE_T
    for sx, sy in NECK_SCREWS:
        B = B - L.to_man(L.cyl((sx, sy, seat_z), (sx, sy, bx["z_top"] + 5), CB_D / 2, 48))
        B = B - L.to_man(L.cyl((sx, sy, 80.0), (sx, sy, seat_z + 0.01), SHANK_D / 2, 48))
    # everything that moves past it: the neck link (stock sheets, servo) over the neck range, the yoke and the head floor
    # at head angles over the neck range; CLR clearance (the pads are the only contact, at +25 only)
    near = L.bbox_of(B, 2.0 + CLR)
    nk_pc = pieces_of(neck_counter(S, sheets), 2.0)
    angs = angles(-20.0, nst, 0.5)
    cut = [L.swept_cut(nk_pc, sweep_T(S, NK, TR, [{"neck_pitch": D(a)} for a in angs]), CLR, near=near)]
    yoke = L.base_mesh("print/head_pitch_to_yaw.stl")
    yoke.apply_transform(L.inst_world(S, L.inst(S, HP, "head_pitch_to_yaw")))
    hd_links = downstream_links(S, HP)
    hd_low = {}
    for i in S.inst:
        if i["link"] in hd_links:
            m = S.world_mesh(i)
            if m.bounds[0][2] < 200.0:
                hd_low["%s#%d" % (i["key"], i["idx"])] = m
    yk_pc = L.convex_pieces(yoke, 2.0)
    for h in (-25.0, -5.0, 15.0, 39.0):
        cfgs = [{"neck_pitch": D(a), "head_pitch": D(h)} for a in angs]
        cut.append(L.swept_cut(yk_pc, sweep_T(S, HP, TR, cfgs), CLR, near=near))
        for key, m in hd_low.items():
            ln = [i["link"] for i in S.inst if "%s#%d" % (i["key"], i["idx"]) == key][0]
            cut.append(L.swept_cut(grid_pieces(m, (-120, -120, 100), (120, 120, 210), 10.0), sweep_T(S, ln, TR, cfgs), CLR, near=near))
    others = L.union(cut[1:])                                     # the yoke and the head over the neck range
    for Tp in pads:
        pm = L.to_man(pad_mesh(NECK_PAD_DIMS)).transform(Tp[:3, :4])
        if (pm ^ others).volume() > 1e-3:
            raise SystemExit("neck block: a pad meets the yoke or the head over the range (%.1f mm3)" % (pm ^ others).volume())
    B = B - L.union(cut)
    # the host: every trunk part; never over a hole of trunk_top but our two screws
    tt = [i for i in S.inst if i["link"] == TR and i["key"] == "trunk_top"][0]
    tt_m = S.world_mesh(tt)
    cyls = []
    for f in L.hole_features(tt_m):
        p0, p1 = np.asarray(f["p0"], float), np.asarray(f["p1"], float)
        if any(np.hypot(p0[0] - sx, p0[1] - sy) < 3.0 for sx, sy in NECK_SCREWS):
            continue
        a = p1 - p0
        if np.linalg.norm(a) < 1e-6:
            continue
        a = a / np.linalg.norm(a)
        cyls.append(L.to_man(L.cyl(p0 - a * 12.0, p1 + a * 12.0, f["d"] / 2 + 0.4, 48)))
    if cyls:
        B = B - L.union(cyls)
    host = L.union([L.to_man(m) for m in link_meshes(S, TR).values()])
    B = B - host
    # the body shell's roof (body_middle_top, z 104 to 108 outside the neck opening |y| 25) is a cover on the same link:
    # the block stays SHELL_CLR off it (a printed fit), so the screw lobes end under it (the screws are driven with the
    # shell off, as the stock ones are)
    shell = [L.to_man(m) for k, m in link_meshes(S, TR, keys=("body_middle_top",)).items()]
    if len(shell) != 1:
        raise SystemExit("neck block: body_middle_top not found on the trunk")
    roof = shell[0] ^ L.to_man(L.box((bx["x"][0] - 5, -bx["y"] - 5, 84.0), (bx["x"][1] + 5, bx["y"] + 5, bx["z_top"] + 5)))
    B = B - L.dilate(roof, SHELL_CLR)
    B = B ^ L.xform(B, MIRROR)                               # an exact mirror: clear of everything on either side
    comps = sorted(B.decompose(), key=lambda m: -m.volume())
    TT = L.to_man(tt_m)
    keep = [cm for cm in comps if (L.dilate(cm, 0.2) ^ TT).volume() > 0.5]       # the block stands on trunk_top
    if len(keep) != 1:
        raise SystemExit("neck block: %d pieces stand on trunk_top (one expected): %s" % (
            len(keep), [np.round(np.asarray(k_.bounding_box()), 1).tolist() + [round(k_.volume())] for k_ in keep]))
    slivers = [k_ for k_ in comps if k_ not in keep]
    if any(k_.volume() > 50.0 for k_ in slivers):
        raise SystemExit("neck block: a loose piece of %.0f mm3 (the cuts split the block): %s" % (
            max(k_.volume() for k_ in slivers), [np.round(np.asarray(k_.bounding_box()), 1).tolist() for k_ in slivers if k_.volume() > 50.0]))
    B = keep[0]
    # checks: the flange holds both screws with 1.5 mm of wall, the pads do not meet the counterbores, the pad face is
    # NECK_R_MIN or more from the axis, nothing of ours is in front of the sheet's +25 edge line
    # the seat under each head (the flange between the shank hole and the counterbore, the last 1.5 mm under the seat)
    # must be whole; the counterbore wall above it may open toward the servo cable window on its -x side (the stock
    # trunk_top recess has 0.7 mm there), so it is only asked for 70 % of a 1.5 mm ring
    seats = {}
    for sx, sy in NECK_SCREWS:
        seat = L.to_man(L.cyl((sx, sy, seat_z - 1.5), (sx, sy, seat_z), CB_D / 2, 48)) - L.to_man(L.cyl((sx, sy, seat_z - 2), (sx, sy, seat_z + 1), SHANK_D / 2, 48))
        wall = L.to_man(L.cyl((sx, sy, seat_z), (sx, sy, seat_z + 1.0), CB_D / 2 + 1.5, 48)) - L.to_man(L.cyl((sx, sy, seat_z - 1), (sx, sy, seat_z + 2), CB_D / 2, 48))
        fs, fw = (seat ^ B).volume() / seat.volume(), (wall ^ B).volume() / wall.volume()
        seats["y%+.1f" % sy] = dict(seat_fraction=round(fs, 3), wall_fraction=round(fw, 3))
        if fs < 0.98:
            raise SystemExit("neck block: the seat under the screw head at y %.1f is not whole (%.2f)" % (sy, fs))
        if fw < 0.7:
            raise SystemExit("neck block: the counterbore wall at y %.1f is open more than the cable window side (%.2f)" % (sy, fw))
    for Tp in pads:
        pm = L.to_man(pad_mesh(NECK_PAD_DIMS)).transform(Tp[:3, :4])
        if (pm ^ B).volume() > 1e-3:
            raise SystemExit("neck block: a pad overlaps the block")
        for sx, sy in NECK_SCREWS:
            if (pm ^ L.to_man(L.cyl((sx, sy, 80), (sx, sy, 140), CB_D / 2, 48))).volume() > 1e-3:
                raise SystemExit("neck block: a pad crosses a counterbore")
    if r_pad < NECK_R_MIN:
        raise SystemExit("neck block: pad centre at r %.1f" % r_pad)
    info = dict(volume_mm3=L.r(B.volume(), 1), slivers_dropped_mm3=[L.r(k_.volume(), 1) for k_ in slivers],
                pad_face_centre=np.round(face_c, 2).tolist(), pad_normal=np.round(n, 4).tolist(),
                edge_dir=np.round(e, 4).tolist(), pad_r_mm=round(r_pad, 2), sheet_back_edge_y=[round(float(v), 2) for v in y_band],
                edge_fit_resid_mm=round(float(resid), 3), foot=dict(x_back=NECK_FOOT["x"], half_y=NECK_FOOT["y"], t=FLANGE_T),
                screws=dict(ids=["F127", "F129"], seat_z_new=seat_z, seat_z_stock=NECK_SCREW_SEAT_Z,
                                                                          length_new=12, length_stock=6, flange_mm=FLANGE_T, counterbore_d=CB_D,
                                                                          shank_d=SHANK_D, seats=seats),
                bbox=np.round(np.asarray(B.bounding_box()), 1).tolist(), secs=round(time.time() - t0, 1))
    log("neck block %.1f s: %.0f mm3, pad r %.1f" % (time.time() - t0, B.volume(), r_pad))
    return B, pads, info


def head_hook(S, log=print):
    """the head forward stop: the yoke with its hook (world zero pose), the pad placement (world 4x4), info."""
    t0 = time.time()
    D = np.radians
    hst = L.STOPS["head_fwd"]["stop"]
    ax_p, ax_d = S.joint_world("head_pitch")
    sheets = stock_sheets(S)
    yoke = L.base_mesh("print/head_pitch_to_yaw.stl")
    yoke.apply_transform(L.inst_world(S, L.inst(S, HP, "head_pitch_to_yaw")))
    HPM = L.to_man(yoke)
    # the left sheet's front edge over HEAD_PAD_Z (neck zero pose): a vertical line x = x_front, its y band
    fr = []
    for z0 in np.arange(HEAD_PAD_Z[0], HEAD_PAD_Z[1] + 0.5, 1.0):
        sec = sheets["neck_left_sheet"].section(plane_origin=[0, 0, z0], plane_normal=[0, 0, 1])
        if sec is None:
            raise SystemExit("head hook: no sheet section at z %.1f" % z0)
        pts = np.vstack([np.asarray(l) for l in sec.discrete])
        xm = pts[:, 0].max()
        fr.append(pts[pts[:, 0] > xm - 0.3])
    fr = np.vstack(fr)
    x_front = float(fr[:, 0].max())
    if np.ptp(fr[:, 0]) > 0.3:
        raise SystemExit("head hook: the sheet's front edge is not a vertical line over z %s (x spread %.2f)" % (HEAD_PAD_Z, np.ptp(fr[:, 0])))
    y_band = (float(fr[:, 1].min()), float(fr[:, 1].max()))
    if y_band[1] - y_band[0] < 5.0:
        raise SystemExit("head hook: the sheet's front edge band is %.1f mm" % (y_band[1] - y_band[0]))
    yc = 0.5 * (y_band[0] + y_band[1])
    pad_w = min(7.0, round(y_band[1] - y_band[0] - 0.2, 1))
    pad_dims = (HEAD_PAD_T, pad_w, HEAD_PAD_Z[1] - HEAD_PAD_Z[0])     # x (thick), y, z in the stop pose
    # at head -25 (neck zero): the pad face on the plane x = x_front, normal -x (toward the sheet); into the yoke's zero pose
    Tm = L.rel_T(S, {"head_pitch": D(hst)}, HP, NK)
    Ti = np.linalg.inv(Tm)
    zc = 0.5 * (HEAD_PAD_Z[0] + HEAD_PAD_Z[1])
    Tpad_m = np.eye(4)
    Tpad_m[:3, 3] = (x_front + HEAD_PAD_T / 2, yc, zc)
    Tpad = Ti @ Tpad_m
    face_m = np.array([x_front, yc, zc])
    n_m = np.array([-1.0, 0.0, 0.0])                             # the pad face normal at the stop (toward the sheet)
    face0 = (Ti @ np.r_[face_m, 1.0])[:3]
    n0 = Ti[:3, :3] @ n_m
    r_pad = float(np.linalg.norm(np.cross(face0 - ax_p, ax_d)))
    # the hook region, its outer face behind the pad face, the pocket
    R = L.union([L.to_man(L.box(*HEAD_HOOK[k])) for k in ("doubler", "drop", "foot")])
    face_off = HEAD_PAD_T + VHB_T - POCKET
    # the hook's face round the pad lies POCKET - PAD_T - VHB_T behind the pad face: a local cut (the hook's body wraps
    # round behind the sheet's side of that plane to the arm; the sheet's sweep keeps everything else CLR off it)
    local = L.to_man(L.box((x_front - 2.0, yc - pad_w / 2 - 3.0, HEAD_PAD_Z[0] - 3.0), (x_front + face_off + 0.5, yc + pad_w / 2 + 3.0, HEAD_PAD_Z[1] + 3.0))).transform(Ti[:3, :4])
    R = R - (halfspace(face0 - n0 * face_off, n0) ^ local)
    pk = L.to_man(L.box((x_front + face_off - 0.01, yc - pad_w / 2 - 0.2, HEAD_PAD_Z[0] - 0.2),
                        (x_front + HEAD_PAD_T + VHB_T + 0.01, yc + pad_w / 2 + 0.2, HEAD_PAD_Z[1] + 0.2))).transform(Ti[:3, :4])
    R = R - pk
    # the neck link over the head range (the sheet's front edge meets the pad only), the head parts over yaw and roll
    near = L.bbox_of(R, 2.0 + CLR)
    nk_pc = pieces_of(neck_counter(S, sheets), 2.0)
    angs = angles(hst, 45.0, 0.5)
    cut = [L.swept_cut(nk_pc, sweep_T(S, NK, HP, [{"head_pitch": D(a)} for a in angs]), CLR, near=near)]
    hd_links = downstream_links(S, HP)
    yaws, rolls = (-105.0, -52.0, 0.0, 52.0, 79.0), (-27.0, 0.0, 27.0)
    cfgs = [{"head_yaw": D(y_), "head_roll": D(r_)} for y_ in yaws for r_ in rolls]
    for i in S.inst:
        if i["link"] in hd_links:
            m = S.world_mesh(i)
            if m.bounds[0][2] < 200.0:
                pcs = grid_pieces(m, (-120, -120, 120), (120, 120, 210), 10.0)     # columns: the floor's hole stays a hole
                Ts = sweep_T(S, i["link"], HP, cfgs)
                cut.append(L.swept_cut(pcs, Ts, CLR, cells=[(T,) for T in Ts], near=near))
    # the trunk's front top (the body shell's roof and front, trunk_top) over the neck and head ranges together: the hook
    # rides on the head and swings down in front when both pitch forward (the sit path's leaning waypoints)
    tr_box = ((-20.0, -45.0, 80.0), (75.0, 45.0, 140.0))
    tr_pcs = []
    for key, m in link_meshes(S, TR, keys=("body_middle_top", "body_front", "trunk_top")).items():
        tr_pcs += grid_pieces(m, tr_box[0], tr_box[1], 10.0)
    necks = angles(-20.0, 25.0, 2.5)
    heads = angles(hst, 45.0, 5.0)
    cells = []
    for nk_ in necks:
        Ts = sweep_T(S, TR, HP, [{"neck_pitch": D(nk_), "head_pitch": D(h)} for h in heads])
        cells += [(Ts[i], Ts[i + 1]) for i in range(len(Ts) - 1)]
    cut.append(L.swept_cut(tr_pcs, None, CLR, cells=cells, near=near))
    R = R - L.union(cut)
    ko = L.hole_keepout(yoke)
    if ko is not None:
        R = R - ko
    comps = sorted(R.decompose(), key=lambda m: -m.volume())
    keep = [cm for cm in comps if (cm ^ HPM).volume() > 0.5]           # grown from the arm: it overlaps the yoke
    if len(keep) != 1:
        raise SystemExit("head hook: %d pieces grow from the yoke (one expected)" % len(keep))
    part = L.solid(HPM + keep[0])
    hook = part - HPM                                                   # the new material only
    if len(part.decompose()) != 1 or abs(part.volume() - HPM.volume() - hook.volume()) > 0.5:
        raise SystemExit("head hook: the yoke and the hook did not join into one body")
    pm = L.to_man(pad_mesh(pad_dims)).transform(Tpad[:3, :4])
    if (pm ^ hook).volume() > 1e-3 or (pm ^ HPM).volume() > 1e-3:
        raise SystemExit("head hook: the pad overlaps the yoke or the hook")
    # the root: the hook within 0.5 mm of the stock yoke (area = that volume / 0.5)
    root = hook ^ (L.dilate(HPM, 0.5) - HPM)
    rc = L.from_man(root).center_mass if root.volume() > 1e-3 else None
    # the hook stays in its region: by volume, not by bounding box (a boolean leaves zero-volume slivers on the yoke's
    # surface that stretch the box but hold nothing)
    outside = hook - L.union([L.to_man(L.box(*HEAD_HOOK[k])) for k in ("doubler", "drop", "foot")])
    if outside.volume() > 0.5:
        raise SystemExit("head hook: %.1f mm3 outside its region (bbox %s)" % (outside.volume(), np.round(np.asarray(outside.bounding_box()), 1).tolist()))
    info = dict(hook_mm3=L.r(hook.volume(), 1), pad_dims=list(pad_dims), pad_face_centre=np.round(face0, 2).tolist(), pad_normal=np.round(n0, 4).tolist(),
                pad_r_mm=round(r_pad, 2), sheet_front_x=round(float(x_front), 2), sheet_front_edge_y=[round(v, 2) for v in y_band],
                root_area_mm2=L.r(root.volume() / 0.5, 1), root_centre=None if rc is None else np.round(rc, 2).tolist(),
                bbox=np.round(np.asarray(hook.bounding_box()), 1).tolist(), secs=round(time.time() - t0, 1))
    log("head hook %.1f s: %.0f mm3, pad r %.1f" % (time.time() - t0, hook.volume(), r_pad))
    return part, Tpad, pad_dims, info


# ---------------------------------------------------------------------------------------------------------------
# the build
# ---------------------------------------------------------------------------------------------------------------
STEPS_ALL = ("thigh", "foot", "roll", "cache", "neck", "head", "seat")


def build(S, log=print, prev=None, redo=STEPS_ALL):
    """the whole CAD; with prev (an earlier build) only the steps in redo are recomputed (the shin step always runs)"""
    t0 = time.time()
    out, info = {}, {}
    D = np.radians
    pout, pinfo = prev if prev else ({}, {})

    def keep(step):
        return prev is not None and step not in redo

    # ---- shin sheets, spacer, knee bumper (left shin zero pose) ----
    shin, shin_pc, Tw_sheet = {}, {}, {}
    for key, new_name in (("knee_to_ankle_left_sheet", "shin_left_sheet"), ("knee_to_ankle_right_sheet", "shin_right_sheet")):
        M, pcs, Tw, inf = joggle_sheet(S, key)
        shin[new_name], Tw_sheet[new_name], info[new_name] = M, Tw, inf
        shin_pc[new_name] = sum((L.convex_pieces(p, slab=3.0) for p in pcs.values()), [])
    sp, T_kb, kb_dims, inf = shin_spacer(S)
    info["shin_spacer"] = inf
    kb = L.to_man(pad_mesh(kb_dims)).transform(T_kb[:3, :4])
    shin_parts_pc = sum(shin_pc.values(), []) + L.convex_pieces(sp, 3.0) + L.convex_pieces(kb, 3.0)
    case_sh = link_meshes(S, SH, keys=("servo_top", "servo_mid", "servo_bottom"))
    shin_parts_pc += pieces_of(case_sh, 3.0)
    # the ankle horns (on the shin link in the URDF, discs on the ankle axis): they pass the thigh and the cover with the
    # shin, but the foot plates are screwed to them, so the foot notch leaves them out
    shin_parts_pc_h = shin_parts_pc + pieces_of(link_meshes(S, SH, skip_prefix=(), keys=HORNS), 3.0)
    # the foot turns about the ankle servo's own axis: its case (and horns) sit 0.1 to 0.5 mm off the foot plates and
    # clear them down to about -95 deg in the stock design. The foot notch is cut by the shin sheets, the spacer and the
    # knee bumper over the whole path, and by the case only past the stop (CASE_BAND, CASE_CLR): the TPU pad gives a
    # little under load, and a swept case with the full clearance would thin the plates at the horn screws
    shin_parts_pc_foot = sum(shin_pc.values(), []) + L.convex_pieces(sp, 3.0) + L.convex_pieces(kb, 3.0)
    case_pc = pieces_of(case_sh, 3.0)
    log("shin parts %.1f s" % (time.time() - t0))

    # thigh spacer relief on the shin clamp front corner (knee 130 to 150)
    thigh_sp = link_meshes(S, TH, keys=("leg_spacer",))
    Ts = sweep_T(S, TH, SH, [L.cfg_left(k=k, both=False) for k in angles(130, 150.5, 0.5)])
    for nm in ("shin_left_sheet", "shin_right_sheet"):
        shin[nm], v = cut_by(shin[nm], pieces_of(thigh_sp, 2.0), Ts, CLR)
        shin[nm] = L.solid(shin[nm])
        info[nm]["thigh_spacer_relief_mm3"] = L.r(v, 1)

    # ---- thigh sheets: the shin passes at the fold ----
    Ts = sweep_T(S, SH, TH, [L.cfg_left(k=k, both=False) for k in angles(100, 150.5, 0.5)])
    thigh = dict(pout["thigh"]) if keep("thigh") else {}
    for key in ([] if keep("thigh") else ("knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet")):
        i = L.inst(S, TH, key)
        m = L.base_mesh("print/%s.stl" % key)
        m.apply_transform(L.inst_world(S, i))
        thigh[key], v = cut_by(L.to_man(m), shin_parts_pc_h, Ts, CLR)
        info[key] = dict(trim_mm3=L.r(v, 1), knee_range=[100, 150.5])
    if keep("thigh"):
        for key in ("knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet"):
            info[key] = pinfo[key]
    log("thigh trims %.1f s" % (time.time() - t0))

    ast = L.STOPS["ankle_sit"]["stop"]
    if keep("foot"):
        foot, pads = dict(pout["foot"]), dict(pout["ankle_pad_T"])
        for key in ("foot_top", "foot_side"):
            info[key] = pinfo[key]
    else:
        # ---- foot plates: the shin passes down to the ankle stop ----
        ast = L.STOPS["ankle_sit"]["stop"]
        Ts_a = sweep_T(S, SH, FT, [L.cfg_left(a=a, both=False) for a in angles(ast - 0.5, -40.0, 0.5)])
        foot = {}
        foot_moved = {}
        for key in ("foot_top", "foot_side"):
            i = L.inst(S, FT, key)
            m = L.base_mesh("print/%s.stl" % key)
            m.apply_transform(L.inst_world(S, i))
            Mh, stack = move_heel_screw(S, key, m)
            foot_moved[key] = L.from_man(Mh)
            foot[key], v = cut_by(Mh, shin_parts_pc_foot, Ts_a, CLR)
            Ts_c = sweep_T(S, SH, FT, [L.cfg_left(a=a, both=False) for a in angles(CASE_BAND[0], CASE_BAND[1], 0.5)])
            foot[key], vc = cut_by(foot[key], case_pc, Ts_c, CASE_CLR)
            info[key] = dict(notch_mm3=L.r(v, 1), case_relief_mm3=L.r(vc, 1), case_band=list(CASE_BAND), ankle_range=[ast - 0.5, -40.0],
                             heel_screw=dict(moved_x_mm=HEEL_DX, from_xz=list(HEEL_OLD), stack=stack))
        # ankle pads: each shin clamp block lands on a flat pad seat at the stop. The block's back face is the plane
        # x = BACK_X of the left shin zero pose; at the stop it is a plane of the foot frame; the pad top is that plane.
        T_st = L.rel_T(S, L.cfg_left(a=ast, both=False), SH, FT)
        nrm = T_st[:3, :3] @ np.array([-1.0, 0, 0])                # outward normal of the back face, foot frame
        # the clamp blocks' back face: the least x of both shin sheets below the clamp line (the mesh, not a constant)
        back_x = min(float(np.asarray(L.from_man(shin[nm] ^ L.to_man(L.box((-400, -400, -400), (400, 400, Z_CLAMP)))).vertices)[:, 0].min())
                     for nm in ("shin_left_sheet", "shin_right_sheet"))
        pads = {}
        for key, ylo, yhi in (("foot_top", 105.5, 113.0), ("foot_side", 67.4, 74.9)):
            # face centre: the clamp block's back face centre (x back_x, z mid of the clamp) at the stop
            pc = T_st @ np.array([back_x, 0.5 * (ylo + yhi), 0.5 * (Z_CLAMP - 138.4), 1.0])
            e_y = np.array([0, 1.0, 0])
            e_u = np.cross(nrm, e_y)
            Rp = np.c_[e_u, e_y, nrm]                              # pad local z points into the foot (nrm: out of the shin)
            if np.linalg.det(Rp) < 0:
                Rp[:, 0] = -Rp[:, 0]
            dims = ANKLE_PAD_DIMS
            Tp = np.eye(4)
            Tp[:3, :3] = Rp
            Tp[:3, 3] = pc[:3] + Rp[:, 0] * ANKLE_PAD_U + nrm * (PAD_T / 2)   # the pad face the shin meets is on the stop plane
            # the seat: a block from the pad's VHB face down into the plate (solid to 6 mm), clipped to the plate's y
            seat = L.box((-dims[0] / 2 - 1.0, -dims[1] / 2, PAD_T / 2 + VHB_T), (dims[0] / 2 + 1.0, dims[1] / 2, PAD_T / 2 + VHB_T + 6.0))
            seat.apply_transform(Tp)
            pocket = L.box((-dims[0] / 2 - 0.3, -dims[1] / 2 - 0.3, -PAD_T / 2 - 0.01), (dims[0] / 2 + 0.3, dims[1] / 2 + 0.3, PAD_T / 2 + VHB_T))
            pocket.apply_transform(Tp)
            orig = foot_moved[key]
            seat_m = L.to_man(seat) ^ L.dilate(L.to_man(orig), 0.0).hull()   # the seat stays inside the plate's outline
            ko = L.hole_keepout(orig)
            if ko is not None:
                seat_m = seat_m - ko                                # and off every hole of the plate
            foot[key] = L.solid((foot[key] + seat_m) - L.to_man(pocket))
            if len(foot[key].decompose()) != 1:
                raise SystemExit("%s: the pad seat does not join the plate" % key)
            pads[key] = Tp
            info[key]["pad"] = dict(centre=np.round(Tp[:3, 3], 2).tolist(), normal_out=np.round(nrm, 3).tolist(), dims=dims)
    log("foot notches %.1f s" % (time.time() - t0))

    # ---- hip roll lug (left roll_to_pitch, mirrored to the right) ----
    rp_i = L.inst(S, RP, "left_roll_to_pitch")
    rp_m = L.base_mesh("print/left_roll_to_pitch.stl")
    rp_m.apply_transform(L.inst_world(S, rp_i))
    RPM = L.to_man(rp_m)
    hip_counter = {HR: link_meshes(S, HR), TR: link_meshes(S, TR, keys=("trunk_bottom", "body_middle_bottom", "servo_top", "servo_mid", "servo_bottom"))}
    rst = L.STOPS["hip_roll_out"]["stop"]
    if keep("roll"):
        RPM, info["left_roll_to_pitch"], Trp, roll_pad_m = pout["roll_to_pitch"], pinfo["left_roll_to_pitch"], pout["roll_pad_T"], pout["roll_pad"]
    else:
        # the lug twice: at zero clearance (its face the case corner's own envelope at the stop: the pad is cut from it)
        # and at LUG_CLR (the lug as built: it never touches, the pad does)
        lug0 = carve_lug(S, RP, RPM, ROLL_LUG, hip_counter, lambda a: L.cfg_left(roll=a, both=False), (rst, 25.0), step=0.5)
        lugc = carve_lug(S, RP, RPM, ROLL_LUG, hip_counter, lambda a: L.cfg_left(roll=a, both=False), (rst, 25.0), step=0.5, clr=LUG_CLR)
        lug, roll_pad_m, Trp, info["left_roll_to_pitch"] = roll_pad(S, RPM, lug0, lugc, hip_counter, rst)
        RPM = L.solid(RPM + lug)
    log("roll lug %.1f s" % (time.time() - t0))

    # ---- hip pad on the roll_to_pitch top face, landing the cover at hip pitch -75 ----
    hst = L.STOPS["hip_pitch_back"]["stop"]
    hp_dims = (6.0, 22.0, 1.5)                                 # thin TPU face: the cover is a shell
    Thp = np.eye(4)
    Thp[:3, 3] = (1.9, 96.5, 15.3 + VHB_T + hp_dims[2] / 2)
    hip_pad = L.to_man(pad_mesh(hp_dims)).transform(Thp[:3, :4])

    # ---- cache: everything that moves past it, on both legs. Both legs' sweeps cut the left cover (the right leg's
    # mapped through the y mirror of the part frame), and the right cover is the mirror of the result: exact mirrors.
    cache = dict(pout["cache"]) if keep("cache") else {}
    if keep("cache"):
        info["cache"] = pinfo["cache"]
    else:
        iL = L.inst(S, TH, "left_cache")
        iR = L.inst(S, "knee_and_ankle_assembly_3", "right_cache")
        TwL, TwR = L.inst_world(S, iL), L.inst_world(S, iR)
        m = L.base_mesh("print/left_cache.stl")
        m.apply_transform(TwL)
        CM = L.to_man(m)
        Tmap = TwL @ MIRROR @ np.linalg.inv(TwR)              # right cover world -> left cover world
        vol = {}
        for side, link_c, link_sh, link_ft, link_rp in (("L", TH, SH, FT, RP),
                                                       ("R", "knee_and_ankle_assembly_3", "knee_and_ankle_assembly_4", "foot_assembly_2", "right_roll_to_pitch_assembly")):
            to_left = np.eye(4) if side == "L" else Tmap
            dy = 0.0 if side == "L" else -181.2              # the right leg is the left leg moved in y (checked)
            shin_side = shin_parts_pc_h if side == "L" else [P + np.array([0, dy, 0]) for P in shin_parts_pc_h]
            Ts_k = [to_left @ L.rel_T(S, L.cfg_left(k=k), link_sh, link_c) for k in angles(-25, 150.5, 2.0)]
            CM, v1 = cut_by(CM, shin_side, Ts_k, CLR)
            # the foot over the sit and stand band of (knee, ankle): the path +/-3 deg and the stop corner
            foot_pc = pieces_of(link_meshes(S, link_ft), 3.0)
            cells = [tuple(to_left @ T for T in cell) for cell in sit_cells(S, link_ft, link_c)]
            CM, v2 = cut_by(CM, foot_pc, None, CLR, cells=cells)
            # the hip pad (on roll_to_pitch) over hip pitch -75 to +30: contact at the stop, nothing before it
            hp_side = hip_pad if side == "L" else L.xform(hip_pad, MIRROR)
            hp_pc = [np.asarray(hp_side.to_mesh().vert_properties, float)[:, :3]]
            Ts_h = [to_left @ L.rel_T(S, L.cfg_left(h=h), link_rp, link_c) for h in angles(hst, 30.0, 0.5)]
            CM, v3 = cut_by(CM, hp_pc, Ts_h, 0.0)
            vol[side] = dict(by_shin_mm3=L.r(v1, 1), by_foot_mm3=L.r(v2, 1), by_hip_pad_mm3=L.r(v3, 1))
        cache["L"] = L.solid(CM)
        info["cache"] = dict(cut_by_leg=vol, removed_mm3=L.r(m.volume - cache["L"].volume(), 1), base_mm3=L.r(m.volume, 1))
    log("caches %.1f s" % (time.time() - t0))

    # ---- neck back stop: the block on trunk_top with its two TPU faces (the neck sheets are stock again) ----
    if keep("neck"):
        neck_stop, neck_pad_T, info["neck_stop"] = pout["neck_stop"], pout["neck_pad_T"], pinfo["neck_stop"]
    else:
        neck_stop, neck_pad_T, info["neck_stop"] = neck_block(S, log)
    # ---- head forward stop: the hook on the yoke's left arm with its TPU face ----
    if keep("head"):
        HPM, head_pad_T, head_pad_dims, info["head_pitch_to_yaw"] = pout["head"], pout["head_pad_T"], pout["head_pad_dims"], pinfo["head_pitch_to_yaw"]
    else:
        HPM, head_pad_T, head_pad_dims, info["head_pitch_to_yaw"] = head_hook(S, log)
    log("neck block and head hook %.1f s" % (time.time() - t0))

    # ---- seat and belly bumper ----
    if keep("seat"):
        seat, bump = pout["seat"], pout["bumper"]
        info.update({k: pinfo[k] for k in ("sit_seat", "sit_bumper")})
    else:
        seat, bump, sinfo = seat_and_bumper(S)
        info.update(sinfo)

    out = dict(shin=shin, Tw_sheet=Tw_sheet, spacer=sp, knee_bumper_T=T_kb, knee_bumper_dims=kb_dims, thigh=thigh, foot=foot,
               ankle_pad_T=pads, roll_to_pitch=RPM, roll_pad_T=Trp, roll_pad=roll_pad_m, hip_pad_T=Thp, hip_pad_dims=hp_dims, cache=cache, head=HPM,
               neck_stop=neck_stop, neck_pad_T=neck_pad_T, head_pad_T=head_pad_T, head_pad_dims=head_pad_dims, seat=seat, bumper=bump)
    log("all %.1f s" % (time.time() - t0))
    return out, info


def sit_cells(S, link_ft, link_c):
    """(knee, ankle) cells of the sit and stand band: the A1b path +/-3 deg on both joints, and the stop corner"""
    cfgs = []
    P = [(w[1], w[2]) for w in L.PATH_A1B]
    path = []
    for (k0, a0), (k1, a1) in zip(P[:-1], P[1:]):
        for s in np.linspace(0, 1, 12, endpoint=False):
            path.append((k0 + s * (k1 - k0), a0 + s * (a1 - a0)))
    path.append(P[-1])
    cells = []

    def T(k, a):
        return L.rel_T(S, L.cfg_left(k=k, a=a), link_ft, link_c)
    for (k, a) in path:
        if k < 60:
            continue
        cells.append((T(k - 3, a - 3), T(k + 3, a - 3), T(k - 3, a + 3), T(k + 3, a + 3)))
    for k in np.arange(140.0, 150.5, 1.0):
        for a in np.arange(-95.5, -79.9, 3.0):
            cells.append((T(k, a), T(min(k + 1.0, 150.5), a), T(k, a + 3.0), T(min(k + 1.0, 150.5), a + 3.0)))
    return cells


def seat_and_bumper(S):
    """TPU blocks under body_middle_bottom: a rounded bottom (a cylinder along y with round ends, lowest point as
    SIT_V2.md) hulled up to the body underside, the top face 1.1 mm (VHB) below the underside"""
    body = {k: S.world_mesh(L.inst(S, TR, k)) for k in ("body_middle_bottom", "body_back")}
    info = {}
    blocks = {}
    for name, P in (("sit_seat", SEAT), ("sit_bumper", BUMPER)):
        r, hy = P["r"], P["half_y"]
        cx, cz = P["x"], P["z_low"] + r
        caps = []
        for ys in (-hy + r, hy - r):
            caps.append(trimesh.creation.icosphere(subdivisions=3, radius=r).apply_translation((cx, ys, cz)))
        cyl = L.cyl((cx, -hy + r, cz), (cx, hy - r, cz), r, 96)
        # underside height over the block footprint: ray cast down onto body_middle_bottom
        xs = np.linspace(cx - r, cx + r, 9)
        ys = np.linspace(-hy, hy, 9)
        top = []
        bm = body["body_middle_bottom"]
        for x in xs:
            for y in ys:
                loc, _, _ = bm.ray.intersects_location([(x, y, -200.0)], [(0, 0, 1.0)])
                if len(loc):
                    top.append((x, y, loc[:, 2].min() - VHB_T))
        top = np.array(top)
        pts = np.vstack([np.vstack([c.vertices for c in caps]), cyl.vertices, top])
        Mb = L.hull_pts(pts)
        # the footprint stays on body_middle_bottom and 1 mm clear of body_back (it comes off for the battery, D45)
        Mb = Mb - L.dilate(L.to_man(body["body_back"]), 1.0)
        blocks[name] = Mb
        b = np.asarray(Mb.bounding_box())
        info[name] = dict(volume_mm3=L.r(Mb.volume(), 1), bbox=np.round(b, 1).tolist(), lowest_z=L.r(b[2], 2),
                          height_mm=L.r(top[:, 2].mean() - b[2], 1), width_y=L.r(b[4] - b[1], 1))
    return blocks["sit_seat"], blocks["sit_bumper"], info


# ---------------------------------------------------------------------------------------------------------------
# output: part frames, print/ (mm) and the URDF mesh copies (m)
# ---------------------------------------------------------------------------------------------------------------
MIRROR = np.diag([1.0, -1.0, 1.0, 1.0])
# new parts and where the URDF places them: (stl stem, link, kind); local-frame parts carry their placement 4x4 per link
NEW_PARTS = ["shin_left_sheet", "shin_right_sheet", "shin_spacer", "knee_bumper", "ankle_pad", "hip_pad", "sit_seat", "sit_bumper",
             "neck_stop", "neck_pad", "head_pad", "roll_pad_left", "roll_pad_right"]
EDITED_PARTS = ["knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "foot_top", "foot_side", "left_cache", "right_cache",
                "left_roll_to_pitch", "right_roll_to_pitch", "head_pitch_to_yaw"]
STOCK_AGAIN = ["neck_left_sheet", "neck_right_sheet"]       # edited by an earlier D59 pass, stock again: the builder restores the STLs
URDF_COPY = {"knee_to_ankle_left_sheet": "left_knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet": "left_knee_to_ankle_right_sheet"}


def to_part(M, Tw):
    """into the part frame first, then cleaned there (the STL stores the part-frame float32 coordinates); finalize keeps
    the largest body, so a part that came out as two bodies (an added lug or hook not joined) is refused, never dropped"""
    if isinstance(M, trimesh.Trimesh):
        m = M.copy()
        m.apply_transform(np.linalg.inv(Tw))
        return m
    m = L.finalize(L.xform(M, np.linalg.inv(Tw)))
    if abs(m.volume - M.volume()) > 2.0:
        raise SystemExit("a part lost %.1f mm3 of %.1f in finalize (a body not joined to the rest)" % (M.volume() - m.volume, M.volume()))
    return m


def outputs(S, out):
    """{stem: mesh in its part frame (mm)} and the placements of the local-frame parts {stem: [(link, 4x4 link frame)]}"""
    P, place = {}, {}
    sh = L.inst(S, SH, "knee_to_ankle_left_sheet")
    P["shin_left_sheet"] = to_part(out["shin"]["shin_left_sheet"], out["Tw_sheet"]["shin_left_sheet"])
    P["shin_right_sheet"] = to_part(out["shin"]["shin_right_sheet"], out["Tw_sheet"]["shin_right_sheet"])
    P["shin_spacer"] = to_part(out["spacer"], L.inst_world(S, L.inst(S, SH, "leg_spacer")))
    for key in ("knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet"):
        P[key] = to_part(out["thigh"][key], L.inst_world(S, L.inst(S, TH, key)))
    for key in ("foot_top", "foot_side"):
        P[key] = to_part(out["foot"][key], L.inst_world(S, L.inst(S, FT, key)))
    # cache: the left cover carries both legs' cuts; the right cover is its exact y mirror (MIRROR in the part frame)
    P["left_cache"] = to_part(out["cache"]["L"], L.inst_world(S, L.inst(S, TH, "left_cache")))
    P["right_cache"] = L.mirror_y_part(P["left_cache"])
    if not L.stl_roundtrip_ok(P["right_cache"])[0]:
        raise SystemExit("right_cache: the mirror of left_cache is not watertight")
    P["left_roll_to_pitch"] = to_part(out["roll_to_pitch"], L.inst_world(S, L.inst(S, RP, "left_roll_to_pitch")))
    P["right_roll_to_pitch"] = L.mirror_y_part(P["left_roll_to_pitch"])
    P["head_pitch_to_yaw"] = to_part(out["head"], L.inst_world(S, L.inst(S, HP, "head_pitch_to_yaw")))
    # the neck block: part origin on the trunk_top surface under the screws' x, on the centre plane (prints standing)
    Tn = np.eye(4)
    Tn[:3, 3] = [NECK_SCREWS[0][0], 0.0, 85.8]
    P["neck_stop"] = to_part(out["neck_stop"], Tn)
    place["neck_stop"] = [(TR, np.linalg.inv(S.T0[TR]) @ Tn)]
    P["neck_pad"] = pad_mesh(NECK_PAD_DIMS)
    place["neck_pad"] = [(TR, np.linalg.inv(S.T0[TR]) @ T) for T in out["neck_pad_T"]]
    P["head_pad"] = pad_mesh(out["head_pad_dims"])
    place["head_pad"] = [(HP, np.linalg.inv(S.T0[HP]) @ out["head_pad_T"])]
    # local-frame parts: centred meshes and their placements in the link frames
    P["knee_bumper"] = pad_mesh(out["knee_bumper_dims"])
    place["knee_bumper"] = [(SH, np.linalg.inv(S.T0[SH]) @ out["knee_bumper_T"]),
                            ("knee_and_ankle_assembly_4", np.linalg.inv(S.T0["knee_and_ankle_assembly_4"]) @ _shift_y(out["knee_bumper_T"], -181.2))]
    P["ankle_pad"] = pad_mesh(ANKLE_PAD_DIMS)
    place["ankle_pad"] = []
    for link, dy in ((FT, 0.0), ("foot_assembly_2", -181.2)):
        for key in ("foot_top", "foot_side"):
            place["ankle_pad"].append((link, np.linalg.inv(S.T0[link]) @ _shift_y(out["ankle_pad_T"][key], dy)))
    P["hip_pad"] = pad_mesh(out["hip_pad_dims"])
    Thp = out["hip_pad_T"]
    place["hip_pad"] = [(RP, np.linalg.inv(S.T0[RP]) @ Thp),
                        ("right_roll_to_pitch_assembly", np.linalg.inv(S.T0["right_roll_to_pitch_assembly"]) @ (MIRROR @ Thp @ MIRROR))]
    # the roll pads: conformal (the case corner's path), so the right one is the left one's mirror, its own file
    Trp = out["roll_pad_T"]
    P["roll_pad_left"] = to_part(out["roll_pad"], Trp)
    P["roll_pad_right"] = L.mirror_y_part(P["roll_pad_left"])
    if not L.stl_roundtrip_ok(P["roll_pad_right"])[0]:
        raise SystemExit("roll_pad_right: the mirror of roll_pad_left is not watertight")
    place["roll_pad_left"] = [(RP, np.linalg.inv(S.T0[RP]) @ Trp)]
    place["roll_pad_right"] = [("right_roll_to_pitch_assembly", np.linalg.inv(S.T0["right_roll_to_pitch_assembly"]) @ (MIRROR @ Trp @ MIRROR))]
    for nm in ("sit_seat", "sit_bumper"):
        M = out["seat"] if nm == "sit_seat" else out["bumper"]
        b = np.asarray(M.bounding_box())
        T = np.eye(4)
        T[:3, 3] = [(b[0] + b[3]) / 2, 0.0, b[5]]                # part origin: top centre (the VHB face)
        P[nm] = to_part(M, T)
        place[nm] = [(TR, np.linalg.inv(S.T0[TR]) @ T)]
    return P, place


def _shift_y(T, dy):
    T = np.array(T, float).copy()
    T[1, 3] += dy
    return T


# stock parts this job changes: every hole feature of the base print STL must be there, the same (audit/feat3d.py)
HOLES_KEPT = ("knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "foot_top", "foot_side", "left_cache", "right_cache",
              "left_roll_to_pitch", "right_roll_to_pitch", "head_pitch_to_yaw")


def write(S, out, info):
    P, place = outputs(S, out)
    rep = {}
    holes = {}
    for stem in HOLES_KEPT:
        hc = L.holes_changed(L.base_mesh("print/%s.stl" % stem), P[stem])
        if stem in ("foot_top", "foot_side"):
            # the heel screw stack moved HEEL_DX in x (part frame x = world x + 19): every gone feature must come back
            # moved by HEEL_DX, and nothing else may change
            def moved_to(f, g, tol=0.2):
                return f["kind"] == g["kind"] and abs(f["d"] - g["d"]) <= tol and all(
                    abs(f[k][0] + HEEL_DX - g[k][0]) <= tol and abs(f[k][1] - g[k][1]) <= tol and abs(f[k][2] - g[k][2]) <= tol
                    for k in ("p0", "p1"))
            ok = (hc["gone"] and len(hc["gone"]) == len(hc["added"]) and all(any(moved_to(f, g) for g in hc["added"]) for f in hc["gone"])
                  and all(any(moved_to(f, g) for f in hc["gone"]) for g in hc["added"]))
            if not ok:
                raise SystemExit("%s: the heel screw holes did not move cleanly by %.1f mm: %s" % (stem, HEEL_DX, json.dumps(hc)))
            holes[stem] = "the same %d hole features as the base STL, the heel screw stack (%d) moved %.0f mm in x" % (
                hc["base"], len(hc["gone"]), HEEL_DX)
            continue
        if hc["gone"] or hc["added"]:
            raise SystemExit("%s: hole features changed (the edit must keep every hole): %s" % (stem, json.dumps(hc)))
        holes[stem] = "the same %d hole features as the base STL" % hc["base"]
    info["holes_kept"] = holes
    for stem, m in P.items():
        ok, vol = L.stl_roundtrip_ok(m)
        if not ok:
            raise SystemExit("%s: not watertight after an STL round trip" % stem)
        m.export(os.path.join(L.PRINT, stem + ".stl"))
        mm = m.copy()
        mm.apply_scale(0.001)
        mm.export(os.path.join(L.URDF_DIR, URDF_COPY.get(stem, stem) + ".stl"))
        if stem in URDF_COPY:            # the right leg reuses the same file name in the URDF (left_ prefix as upstream)
            pass
        if vol <= 0:
            raise SystemExit("%s: inside out (volume %.1f)" % (stem, vol))
        rep[stem] = dict(volume_mm3=L.r(vol, 1), faces=len(m.faces), print_file="print/%s.stl" % stem,
                         urdf_copy="mini_bdx/robots/open_duck_mini_v2/%s.stl" % URDF_COPY.get(stem, stem),
                         bytes=os.path.getsize(os.path.join(L.PRINT, stem + ".stl")))
    # parts an earlier pass edited and this one leaves stock: the base STL goes back (print and the URDF copy)
    restored = {}
    for stem in STOCK_AGAIN:
        for rel, path in (("print/%s.stl" % stem, os.path.join(L.PRINT, stem + ".stl")),
                          ("mini_bdx/robots/open_duck_mini_v2/%s.stl" % stem, os.path.join(L.URDF_DIR, stem + ".stl"))):
            open(path, "wb").write(L.git_blob(rel))
        restored[stem] = "stock again (print/%s.stl and its URDF copy are the %s files, byte for byte)" % (stem, L.BASE_REV)
    info["stock_again"] = restored
    pl = {stem: [dict(link=ln, T_link_mm=np.round(T, 6).tolist()) for ln, T in v] for stem, v in place.items()}
    J = dict(generated_by="altaay_lab/twin/sit/sit_cad.py --write", base_rev=L.BASE_REV, units="mm", clearance_mm=CLR,
             frame="part frames as print/ (the URDF mesh frame x1000); placements of the local-frame parts in the URDF link frames",
             stops={k: v for k, v in L.STOPS.items()}, parts=rep, placements=pl, build=info)
    L.dump(J, os.path.join(HERE, "sit_cad.json"))
    return J


ANKLE_PAD_DIMS = (6.0, 7.5, PAD_T)
ANKLE_PAD_U = 6.1               # pad centre along the clamp face, toward the ankle (kept from when the F024 hole was beside it)
# The heel screw F024 (F026 right: M3x10 from foot_side into the foot_top insert I34, I46) sits where the shin's ankle
# clamp corner (the M2 screw F043 and its boss) arrives past about -88 deg: both are about 34 mm from the ankle axis.
# Its whole hole stack (foot_side: 6.5 counterbore and 3.5 clearance; foot_top: 4.0 insert bore and 2.0 pilot) moves
# HEEL_DX toward the toe, out of the foot notch (notch edge x -51.6 at the heel height, boss radius 4.5, 0.5 margin) and
# 3.3 mm off the Omron switch slot (x -53.96 to -47.56); the old stack is plugged (D39). Same stack, so the same screw.
CASE_BAND, CASE_CLR = (-97.5, -94.0), 0.3     # ankle angles where the ankle servo case is cleared out of the foot plates
HEEL_OLD = (-62.25, -176.7)     # world x, z of the stock heel screw axis (fasteners.json F024 seat; axis +y)
HEEL_DX = 20.0


def _pack(o):
    if isinstance(o, dict):
        return {k: _pack(v) for k, v in o.items()}
    if hasattr(o, "to_mesh64"):
        return ("__man__", L.man_to_arrays(o))
    return o


def cache_key():
    """what a cached build depends on: this file, sitlib.py and the libraries it imports (cables3d, audit/feat3d.py),
    and the base revision every stock part is read from (git blobs at L.BASE_REV)"""
    import hashlib
    h = hashlib.sha256(L.BASE_REV.encode())
    for p in (os.path.abspath(__file__), os.path.join(HERE_CAD, "sitlib.py"), os.path.join(L.LAB, "cables3d", "c3d_lib.py"),
              os.path.join(L.LAB, "audit", "feat3d.py")):
        h.update(open(p, "rb").read())
    return h.hexdigest()


def _unpack(o):
    if isinstance(o, dict):
        return {k: _unpack(v) for k, v in o.items()}
    if isinstance(o, tuple) and len(o) == 2 and o[0] == "__man__":
        return L.man_from_arrays(o[1])
    return o


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--redo", default=None, help="with --cache: steps to recompute (%s)" % ",".join(STEPS_ALL))
    ap.add_argument("--cache", help="pickle of the build outside the repo, reused only when it was built by the same code from "
                    "the same base (cache_key); --redo recomputes steps of a matching cache")
    a = ap.parse_args()
    S = L.scene_base()
    import json
    import pickle
    key = cache_key()
    prev = None
    if a.cache and os.path.exists(a.cache):
        c = pickle.load(open(a.cache, "rb"))
        if isinstance(c, dict) and c.get("key") == key:
            prev = (_unpack(c["out"]), c["info"])
        else:
            print("cache %s was built by other code or from another base: full build" % os.path.basename(a.cache))
    if prev is not None:
        redo = tuple(x for x in a.redo.split(",") if x) if a.redo is not None else ()
        out, info = build(S, prev=prev, redo=redo)
    else:
        out, info = build(S)
    if a.cache:
        pickle.dump(dict(key=key, out=_pack(out), info=info), open(a.cache, "wb"))
    if a.write:
        J = write(S, out, info)
        print(json.dumps(J["parts"], indent=1))
    else:
        print(json.dumps(info, indent=1, default=str))
