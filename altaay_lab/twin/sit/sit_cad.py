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
  neck_left_sheet, neck_right_sheet: the neck back stop lug (+25 deg) against trunk_top.
  head_pitch_to_yaw: the head forward stop lug (-25 deg) against the head pitch servo case.
  sit_seat (new, TPU, 1) and sit_bumper (new, TPU, 1): under the rear and the front of body_middle_bottom on VHB.
"""
import argparse
import os
import sys
import time

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sitlib as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SH, TH, FT = "knee_and_ankle_assembly_2", "knee_and_ankle_assembly", "foot_assembly"
RP, HR, NK, HP, TR = "left_roll_to_pitch_assembly", "hip_roll_assembly", "neck_pitch_assembly", "head_pitch_to_yaw", "trunk_assembly"
CLR = 0.8                       # clearance of every cut to a part that moves past (printed tolerance plus margin)
R_WEB = 18.4                    # outer radius of the joggle web (the thigh sheet ends 19.0 mm from the knee axis)
Z_CLAMP = -119.6                # the servo clamp of the shin sheet starts below this z (zero pose, left shin)
OVL = 0.37                      # overlap of the joggle pieces (radially and at the clamp line)
STEP = 9.0 / 7.0                # sweep step of the web and the clamp block (not a divisor of the plate features)
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
M2_HEAD_CB = 4.6                # counterbore for the M2 pan head (dk 3.8 to 4.0) plus a driver gap
KNEE = np.array([-35.06, -78.72])
ANKLE = np.array([-35.06, -157.37])
HORNS = ("drive_palonier", "passive_palonier")
# lug regions (world zero pose, mm): the box a lug may fill; the sweep of the counterpart over the free range carves it
ROLL_LUG = ((-16.0, 50.0, 2.0), (-6.0, 62.8, 11.6))         # on left_roll_to_pitch, front of the D3/SP4/S3 loop
NECK_LUG = ((-26.0, None, 88.0), (-8.0, None, 104.0))       # on each neck sheet, behind its back edge, y = the sheet
HEAD_LUG = ((6.0, -9.0, 165.0), (15.5, 9.0, 173.0))          # on head_pitch_to_yaw, over the head pitch servo top
SEAT = dict(x=-110.0, z_low=-66.0, r=16.0, half_y=40.0)     # SIT_V2.md 3.3: lowest point 66 mm under the trunk origin
BUMPER = dict(x=20.0, z_low=-69.0, r=12.0, half_y=30.0)     # SIT_V2.md 3.3: 3 mm off the floor in the sit
SIT_BODY_SPLIT_X = -115.0       # the seat is glued to body_middle_bottom only (body_back comes off for the battery)


# ---------------------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------------------
def link_meshes(S, link, skip_prefix=HORNS, keys=None):
    return {"%s#%d" % (i["key"], i["idx"]): S.world_mesh(i) for i in S.inst
            if i["link"] == link and not i["key"].startswith(skip_prefix) and (keys is None or i["key"] in keys)}


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

    def sweep(M):
        return L.union([M] + [M.translate((0.0, n * s, 0.0)) for s in np.arange(STEP, L.JOG + 1e-6, STEP)])
    web, plate_j, block = sweep(band), plate.translate((0.0, n * L.JOG, 0.0)), sweep(clamp)
    new = L.union([horn, web, plate_j, block])
    y_in = (109.05 if n > 0 else 71.95) + n * L.JOG
    y_out = (112.95 if n > 0 else 68.10) + n * L.JOG
    lo, hi = min(y_in, y_out), max(y_in, y_out)
    for (x, z) in OLD_SPACER_HOLES:                           # D39: no empty hole; plugs flush with both plate faces
        new = new + L.to_man(L.cyl((x, lo, z), (x, hi, z), SHEET_RECESS / 2 + 0.4))
    holes = []
    for (x, z) in SPACER_HOLES:
        new = new - L.to_man(L.cyl((x, lo - 1, z), (x, hi + 1, z), SHEET_HOLE / 2))
        new = new - L.to_man(L.cyl((x, y_out - n * RECESS_DEPTH, z), (x, y_out + n * 1.0, z), SHEET_RECESS / 2))
        holes.append(dict(x=x, z=z, y_outer_face=L.r(y_out, 2), recess_floor=L.r(y_out - n * RECESS_DEPTH, 2)))
    zc = -128.4 if n > 0 else -124.6
    y_cb0 = (112.95 if n > 0 else 68.10)                     # the stock outer face where the M2 head sat
    cbs = []
    for x in (-24.8, -45.3):
        new = new - L.to_man(L.cyl((x, y_cb0, zc), (x, y_cb0 + n * (L.JOG + 1.0), zc), M2_HEAD_CB / 2))
        cbs.append(dict(x=x, z=zc, head_seat_y=y_cb0, depth=L.JOG))
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


# ---------------------------------------------------------------------------------------------------------------
# lugs by carving: a region on the host, minus everything the counterparts sweep over the free range
# ---------------------------------------------------------------------------------------------------------------
def carve_lug(S, host_link, host, region, counter, cfg_of, free, step=0.5):
    """host: manifold (world zero pose of host_link); region: box lo, hi; counter: {link: {name: mesh}};
    free: (a0, a1) the free range of the joint; returns the lug (new material only) and the touch report"""
    R = L.to_man(L.box(*region))
    near = (np.asarray(region[0]) - 2.0, np.asarray(region[1]) + 2.0)
    cutters = []
    angs = angles(free[0], free[1], step)
    for ln, ms in counter.items():
        Ts = sweep_T(S, ln, host_link, [cfg_of(a) for a in angs])
        cutters.append(L.swept_cut(pieces_of(ms, 2.0), Ts, 0.0, near=near))
    lug = (R - L.union(cutters)) - host
    comps = sorted(lug.decompose(), key=lambda m: -m.volume())
    # keep the pieces that touch the host (a lug must grow from it)
    keep = [cm for cm in comps if (L.dilate(cm, 0.2) ^ host).volume() > 0.5]
    return L.union(keep)


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
        thigh[key], v = cut_by(L.to_man(m), shin_parts_pc, Ts, CLR)
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
        for key in ("foot_top", "foot_side"):
            i = L.inst(S, FT, key)
            m = L.base_mesh("print/%s.stl" % key)
            m.apply_transform(L.inst_world(S, i))
            foot[key], v = cut_by(L.to_man(m), shin_parts_pc, Ts_a, CLR)
            info[key] = dict(notch_mm3=L.r(v, 1), ankle_range=[ast - 0.5, -40.0])
        # ankle pads: each shin clamp block lands on a flat pad seat at the stop. The block's back face is the plane
        # x = BACK_X of the left shin zero pose; at the stop it is a plane of the foot frame; the pad top is that plane.
        T_st = L.rel_T(S, L.cfg_left(a=ast, both=False), SH, FT)
        nrm = T_st[:3, :3] @ np.array([-1.0, 0, 0])                # outward normal of the back face, foot frame
        back_x = -50.25
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
            orig = L.base_mesh("print/%s.stl" % key)
            orig.apply_transform(L.inst_world(S, L.inst(S, FT, key)))
            seat_m = L.to_man(seat) ^ L.dilate(L.to_man(orig), 0.0).hull()   # the seat stays inside the plate's outline
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
        RPM, info["left_roll_to_pitch"] = pout["roll_to_pitch"], pinfo["left_roll_to_pitch"]
    else:
        lug = carve_lug(S, RP, RPM, ROLL_LUG, hip_counter, lambda a: L.cfg_left(roll=a, both=False), (rst, 25.0), step=0.5)
        info["left_roll_to_pitch"] = dict(lug_mm3=L.r(lug.volume(), 1))
        RPM = L.solid(RPM + lug)
    log("roll lug %.1f s" % (time.time() - t0))

    # ---- hip pad on the roll_to_pitch top face, landing the cover at hip pitch -75 ----
    hst = L.STOPS["hip_pitch_back"]["stop"]
    hp_dims = (6.0, 22.0, 1.5)                                 # thin TPU face: the cover is a shell
    Thp = np.eye(4)
    Thp[:3, 3] = (1.9, 96.5, 15.3 + VHB_T + hp_dims[2] / 2)
    hip_pad = L.to_man(pad_mesh(hp_dims)).transform(Thp[:3, :4])

    # ---- cache: everything that moves past it ----
    cache = dict(pout["cache"]) if keep("cache") else {}
    if keep("cache"):
        info["cache_L"], info["cache_R"] = pinfo["cache_L"], pinfo["cache_R"]
    for side, link_c, key_c, link_sh, link_ft, link_rp in (() if keep("cache") else (("L", TH, "left_cache", SH, FT, RP),
                                                          ("R", "knee_and_ankle_assembly_3", "right_cache", "knee_and_ankle_assembly_4", "foot_assembly_2", "right_roll_to_pitch_assembly"))):
        i = L.inst(S, link_c, key_c)
        m = L.base_mesh("print/%s.stl" % key_c)
        m.apply_transform(L.inst_world(S, i))
        CM = L.to_man(m)
        dy = 0.0 if side == "L" else -181.2                  # the right leg is the left leg moved in y (checked)
        shift = np.eye(4)
        shift[1, 3] = dy
        if side == "L":
            shin_side = shin_parts_pc
        else:                                                  # right leg: the same parts, moved
            shin_side = [P + np.array([0, dy, 0]) for P in shin_parts_pc]
        knee_cfg = (lambda k: L.cfg_left(k=k)) if True else None
        Ts_k = [L.rel_T(S, knee_cfg(k), link_sh, link_c) for k in angles(-25, 150.5, 2.0)]
        CM, v1 = cut_by(CM, shin_side, Ts_k, CLR)
        # the foot over the sit and stand band of (knee, ankle): the path +/-3 deg and the stop corner
        foot_pc = pieces_of(link_meshes(S, link_ft), 3.0)
        cells = sit_cells(S, link_ft, link_c)
        CM, v2 = cut_by(CM, foot_pc, None, CLR, cells=cells)
        # the hip pad (on roll_to_pitch) over hip pitch -75 to +30: contact at the stop, nothing before it
        hp_side = hip_pad if side == "L" else L.xform(hip_pad, np.diag([1.0, -1.0, 1.0, 1.0]))
        hp_pc = [np.asarray(hp_side.to_mesh().vert_properties, float)[:, :3]]
        Ts_h = [L.rel_T(S, L.cfg_left(h=h), link_rp, link_c) for h in angles(hst, 30.0, 0.5)]
        CM, v3 = cut_by(CM, hp_pc, Ts_h, 0.0)
        cache[side] = CM
        info["cache_" + side] = dict(by_shin_mm3=L.r(v1, 1), by_foot_mm3=L.r(v2, 1), by_hip_pad_mm3=L.r(v3, 1))
    log("caches %.1f s" % (time.time() - t0))

    # ---- neck back stop lugs (both sheets) ----
    nst = L.STOPS["neck_back"]["stop"]
    neck = dict(pout["neck"]) if keep("neck") else {}
    tr_counter = {TR: link_meshes(S, TR, keys=("trunk_top", "body_middle_top", "body_back", "body_front", "servo_top", "servo_mid", "servo_bottom"))}
    for key in (("neck_left_sheet", "neck_right_sheet") if keep("neck") else ()):
        info[key] = pinfo[key]
    for key in (() if keep("neck") else ("neck_left_sheet", "neck_right_sheet")):
        i = L.inst(S, NK, key)
        m = L.base_mesh("print/%s.stl" % key)
        m.apply_transform(L.inst_world(S, i))
        NM = L.to_man(m)
        b = m.bounds
        # the lug's side faces stay off the sheet's steps (16.1, 19.15, 21.15, 22.15 and their mirrors): a shared face pinches
        reg = ((NECK_LUG[0][0], b[0][1] + 0.27, NECK_LUG[0][2]), (NECK_LUG[1][0], b[1][1] - 0.38, NECK_LUG[1][2]))
        lug = carve_lug(S, NK, NM, reg, tr_counter, lambda a: {"neck_pitch": D(a)}, (-20.0, nst), step=0.5)
        neck[key] = L.solid(NM + lug)
        info[key] = dict(lug_mm3=L.r(lug.volume(), 1))
    # ---- head forward stop lug ----
    hst2 = L.STOPS["head_fwd"]["stop"]
    if keep("head"):
        HPM, info["head_pitch_to_yaw"] = pout["head"], pinfo["head_pitch_to_yaw"]
    i = L.inst(S, HP, "head_pitch_to_yaw")
    m = L.base_mesh("print/head_pitch_to_yaw.stl")
    m.apply_transform(L.inst_world(S, i))
    if not keep("head"):
        HPM = L.to_man(m)
        nk_counter = {NK: link_meshes(S, NK)}
        lug = carve_lug(S, HP, HPM, HEAD_LUG, nk_counter, lambda a: {"head_pitch": D(a)}, (hst2, 45.0), step=0.5)
        info["head_pitch_to_yaw"] = dict(lug_mm3=L.r(lug.volume(), 1))
        HPM = L.solid(HPM + lug)
    log("neck and head lugs %.1f s" % (time.time() - t0))

    # ---- seat and belly bumper ----
    if keep("seat"):
        seat, bump = pout["seat"], pout["bumper"]
        info.update({k: pinfo[k] for k in ("sit_seat", "sit_bumper")})
    else:
        seat, bump, sinfo = seat_and_bumper(S)
        info.update(sinfo)

    out = dict(shin=shin, Tw_sheet=Tw_sheet, spacer=sp, knee_bumper_T=T_kb, knee_bumper_dims=kb_dims, thigh=thigh, foot=foot,
               ankle_pad_T=pads, roll_to_pitch=RPM, hip_pad_T=Thp, hip_pad_dims=hp_dims, cache=cache, neck=neck, head=HPM,
               seat=seat, bumper=bump)
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
NEW_PARTS = ["shin_left_sheet", "shin_right_sheet", "shin_spacer", "knee_bumper", "ankle_pad", "hip_pad", "sit_seat", "sit_bumper"]
EDITED_PARTS = ["knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "foot_top", "foot_side", "left_cache", "right_cache",
                "left_roll_to_pitch", "right_roll_to_pitch", "neck_left_sheet", "neck_right_sheet", "head_pitch_to_yaw"]
URDF_COPY = {"knee_to_ankle_left_sheet": "left_knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet": "left_knee_to_ankle_right_sheet"}


def to_part(M, Tw):
    """into the part frame first, then cleaned there (the STL stores the part-frame float32 coordinates)"""
    if isinstance(M, trimesh.Trimesh):
        m = M.copy()
        m.apply_transform(np.linalg.inv(Tw))
        return m
    return L.finalize(L.xform(M, np.linalg.inv(Tw)))


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
    # cache: left and right as exact y mirrors, each cut by both legs' sweeps
    TwL = L.inst_world(S, L.inst(S, TH, "left_cache"))
    TwR = L.inst_world(S, L.inst(S, "knee_and_ankle_assembly_3", "right_cache"))
    cl = L.to_man(to_part(out["cache"]["L"], TwL))
    cr_m = L.to_man(to_part(out["cache"]["R"], TwR))
    left = cl ^ L.xform(cr_m, MIRROR)
    P["left_cache"] = L.finalize(left)
    if not L.stl_roundtrip_ok(L.mirror_y_part(P["left_cache"]))[0]:
        raise SystemExit("right_cache: the mirror of left_cache is not watertight")
    P["right_cache"] = L.mirror_y_part(P["left_cache"])
    P["left_roll_to_pitch"] = to_part(out["roll_to_pitch"], L.inst_world(S, L.inst(S, RP, "left_roll_to_pitch")))
    P["right_roll_to_pitch"] = L.mirror_y_part(P["left_roll_to_pitch"])
    for key in ("neck_left_sheet", "neck_right_sheet"):
        P[key] = to_part(out["neck"][key], L.inst_world(S, L.inst(S, NK, key)))
    P["head_pitch_to_yaw"] = to_part(out["head"], L.inst_world(S, L.inst(S, HP, "head_pitch_to_yaw")))
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


def write(S, out, info):
    P, place = outputs(S, out)
    rep = {}
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
        rep[stem] = dict(volume_mm3=L.r(vol, 1), faces=len(m.faces), print_file="print/%s.stl" % stem,
                         urdf_copy="mini_bdx/robots/open_duck_mini_v2/%s.stl" % URDF_COPY.get(stem, stem),
                         bytes=os.path.getsize(os.path.join(L.PRINT, stem + ".stl")))
    pl = {stem: [dict(link=ln, T_link_mm=np.round(T, 6).tolist()) for ln, T in v] for stem, v in place.items()}
    J = dict(generated_by="altaay_lab/twin/sit/sit_cad.py --write", base_rev=L.BASE_REV, units="mm", clearance_mm=CLR,
             frame="part frames as print/ (the URDF mesh frame x1000); placements of the local-frame parts in the URDF link frames",
             stops={k: v for k, v in L.STOPS.items()}, parts=rep, placements=pl, build=info)
    L.dump(J, os.path.join(HERE, "sit_cad.json"))
    return J


ANKLE_PAD_DIMS = (6.0, 7.5, PAD_T)
ANKLE_PAD_U = 6.1               # pad centre along the clamp face, toward the ankle: the foot_side pocket clears the F024
                                # M3 hole (x -62.2, z -176.7) by 1.0 mm or more


def _pack(o):
    if isinstance(o, dict):
        return {k: _pack(v) for k, v in o.items()}
    if hasattr(o, "to_mesh64"):
        return ("__man__", L.man_to_arrays(o))
    return o


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
    ap.add_argument("--cache", help="pickle of the build outside the repo (reused when it exists: delete it after a design change)")
    a = ap.parse_args()
    S = L.scene()
    import json
    import pickle
    if a.cache and os.path.exists(a.cache):
        pout, pinfo = pickle.load(open(a.cache, "rb"))
        prev = (_unpack(pout), pinfo)
        redo = tuple(x for x in a.redo.split(",") if x) if a.redo is not None else ()
        out, info = build(S, prev=prev, redo=redo)
    else:
        out, info = build(S)
    if a.cache:
        pickle.dump((_pack(out), info), open(a.cache, "wb"))
    if a.write:
        J = write(S, out, info)
        print(json.dumps(J["parts"], indent=1))
    else:
        print(json.dumps(info, indent=1, default=str))
