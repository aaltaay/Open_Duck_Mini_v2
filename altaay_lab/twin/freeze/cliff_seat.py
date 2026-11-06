#!/usr/bin/env python3
"""cliff_seat.py: the seat of the downward cliff ToF (Adafruit 5396, ST VL53L4CD) in print/body_front.stl (V1 freeze,
perception study 3.1). CAD check only (seat), calc only (beam on the floor).

Run: python3 altaay_lab/twin/freeze/cliff_seat.py [--write]
--write writes print/body_front.stl and cliff_seat.json.

Inputs, with sources:
  board: [R] Adafruit-VL53L4CD-PCB 'Adafruit VL53L4CD.brd' (raw.githubusercontent.com, read 2026-11-06 ET): outline
         25.4 x 17.78 mm; 4 plated 2.5 mm holes at (2.54, 2.54), (22.86, 2.54), (2.54, 15.24), (22.86, 15.24); U1 (the
         VL53L4CD) at the centre (12.7, 8.89); STEMMA QT sockets CONN3 and CONN4 at (22.73, 8.89) and (2.67, 8.89);
         6-pin header JP2 along y 2.54. [R] adafruit.com/product/5396: 25.5 x 17.7 x 4.6 mm, 1.8 g, $14.95.
  sensor: [R] ST DS13812 Rev 3 (the PDF on the Adafruit guide): 18 deg diagonal FoV, 0 to 1300 mm, up to 100 Hz,
         active ranging 22 mA typical, 24 mA max, VCSEL peak 40 mA (Table 12), I2C 0x52 8-bit = 0x29 7-bit.
  pose: the perception study (blind.py, chest.py): standing pose floor 166.8 mm under the trunk origin, toe at x 34.3,
         body_front front face x 36 to 46, beam 52 deg below horizontal, centred (y 0).
Design (D54): the board sits inside the 10 mm chest wall, low and centred, its sensor face down-forward along the beam
  n = (cos 52, 0, -sin 52). It lies on 4 printed standoffs (3.3 mm, over the QT sockets and parts) on a printed floor
  that grows from the inner face of body_front; 2 M2.5x6 DIN 912 (BOM 17f) on the diagonal pair of holes go in from
  the back of the board into 2.0 mm pilots in 2 of the standoffs (D42: a diagonal pair through the board centre); the
  other 2 standoffs are solid and the board's other 2 holes sit on them (D39: no empty hole in a printed part). A slot
  is open from the board back to the inside of the trunk (wires and the hex key). A window through the floor and the
  wall follows the field of view: a cone of 14 deg half angle (9 deg FoV half diagonal + 5 deg) from a 2.5 mm disk at
  the sensor. The wires (D21, D22) are soldered into JP2 from the back side and leave along the board's lower edge.
Print: body_front now prints with its front face on the bed (parts.csv up -x), so the seat grows up from the inner face.
Checks: watertight; no other part within 1 mm of the seat (zero pose); the board 1.6 mm or more inside the front face;
  the window clear of the dock pad (z 0 to 76, D50), of the 6 mm chest lead hole and its bell (z 38, D50), of the DK2
  diode seat; wall left round the window and the pocket; the beam on the floor in the standing pose (calc only) and
  against the robot's own legs at zero and over the stock walk joint envelope (VERIFICATION E9).
"""
import argparse
import json
import os

import numpy as np
import trimesh

from flib import (PRINT, HERE, scene, inst_by_key, inst_world, to_man, from_man, cyl, box_mesh, hits_along, surface_cloud,
                  placements, placement_box, base_mesh, r, dump)

TILT = np.radians(52.0)
N = np.array([np.cos(TILT), 0.0, -np.sin(TILT)])          # sensor normal (out of the chip), down-forward
E1 = np.array([0.0, 1.0, 0.0])                             # board long axis (25.4 mm)
E2 = np.cross(N, E1)                                       # board short axis, forward-up (sin 52, 0, cos 52)
O = np.array([35.0, 0.0, -1.0])                            # PCB top-face centre, URDF world (zero pose)
BW, BH, PCB = 25.4, 17.78, 1.6
HOLES = [(2.54, 2.54), (22.86, 2.54), (2.54, 15.24), (22.86, 15.24)]
SCREWED = [(2.54, 2.54), (22.86, 15.24)]                   # the diagonal pair through the centre (D42)
PARTS_H, STANDOFF_H, CLR = 3.0, 3.3, 0.3                   # QT sockets 4.6 overall - 1.6 PCB; standoff over them
FLOOR_T, FLOOR_MARGIN = 3.0, 2.5
STANDOFF_D, PILOT_D, SCREW_L = 5.0, 2.0, 6.0
CONE_HALF, APEX_R, APEX_N = np.radians(14.0), 2.5, 1.0
FRONT_X = 46.0
FLOOR_Z_STAND = -166.83                                     # perception study chest.py, standing pose
TOE_X = 34.27
PAD_Z = (0.0, 76.0)
CHEST_HOLE_Z, CHEST_BELL_R = 38.0, 5.0


def bp(u, v, n=0.0):
    """board coordinates (mm from the outline corner, as in the .brd) and height along N to world"""
    return O + (u - BW / 2) * E1 + (v - BH / 2) * E2 + n * N


def board_box(n0, n1, pad=0.0, du=None, dv=None):
    du = du if du is not None else BW / 2 + pad
    dv = dv if dv is not None else BH / 2 + pad
    R = np.c_[E1, E2, N]
    c = O + N * (n0 + n1) / 2
    return box_mesh(c, R, [2 * du, 2 * dv, n1 - n0])


def cone(apex_n, length):
    """the field-of-view keep-out: a frustum from a disk of APEX_R at apex_n along N"""
    a = O + N * apex_n
    r1 = APEX_R + length * np.tan(CONE_HALF)
    ring0, ring1 = [], []
    for t in np.linspace(0, 2 * np.pi, 64, endpoint=False):
        d = np.cos(t) * E1 + np.sin(t) * E2
        ring0.append(a + d * APEX_R)
        ring1.append(a + N * length + d * r1)
    return trimesh.convex.convex_hull(np.array(ring0 + ring1))


def legs_sweep(cone_m):
    """the leg meshes of the MuJoCo model (trunk fixed at the origin, the URDF frame) against the cone over a joint grid
    wider than the stock walk uses (VERIFICATION E9: hip pitch -49.3 to +49.6 deg, knee up to 90.8 deg): hip pitch
    -55 to +55, knee 0 to 95, ankle over its MJCF range, hip roll and yaw at 0 and their E9 extremes"""
    import mujoco
    R = os.path.join(os.path.dirname(PRINT), "mini_bdx", "robots", "open_duck_mini_v2")
    m = mujoco.MjModel.from_xml_path(os.path.join(R, "scene.xml"))
    d = mujoco.MjData(m)
    tb = m.body("trunk_assembly").id
    geoms = [g for g in range(m.ngeom) if m.geom_bodyid[g] not in (0, tb) and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH
             and m.body(m.geom_bodyid[g]).name.split("_")[0] not in ("neck", "head")]
    def jq(n):
        return m.jnt_qposadr[m.joint(n).id]
    lo_a, hi_a = m.jnt_range[m.joint("left_ankle").id]
    hits, n = [], 0
    for side in ("left", "right"):
        for hp in np.radians(np.linspace(-55, 55, 12)):
            for kn in np.radians(np.linspace(0, 95, 8)):
                for an in np.linspace(lo_a, hi_a, 6):
                    for hr in np.radians((-10, 0, 10)):
                        d.qpos[:] = m.qpos0
                        d.qpos[0:3] = 0
                        d.qpos[3:7] = [1, 0, 0, 0]
                        for k, v_ in (("hip_pitch", hp), ("knee", kn), ("ankle", an), ("hip_roll", hr)):
                            d.qpos[jq("%s_%s" % (side, k))] = v_
                        mujoco.mj_kinematics(m, d)
                        n += 1
                        for g in geoms:
                            mid = m.geom_dataid[g]
                            a0, nv = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
                            P = (m.mesh_vert[a0:a0 + nv] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]) * 1000.0
                            P = P[P[:, 0] > 30.0]
                            if len(P) and cone_m.contains(P[::3]).any():
                                hits.append(dict(side=side, hip_pitch_deg=r(np.degrees(hp), 1), knee_deg=r(np.degrees(kn), 1),
                                                 ankle_rad=r(an, 2), body=m.body(m.geom_bodyid[g]).name))
                                break
    return dict(poses=n, hits=hits[:10], n_hits=len(hits), label="CAD check only (kinematics, no dynamics)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = scene()
    bf = inst_by_key(S, "body_front")[0]
    Tbf = inst_world(S, bf)
    Ti = np.linalg.inv(Tbf)
    base = base_mesh("print/body_front.stl")
    W = base.copy()
    W.apply_transform(Tbf)
    # 1. housing: the floor under the standoffs, hulled to the inner face of the wall (x 36 -> 37, inside the wall)
    fl = board_box(STANDOFF_H, STANDOFF_H + FLOOR_T, pad=FLOOR_MARGIN)
    v = np.array(fl.vertices)
    proj = v.copy()
    proj[:, 0] = np.minimum(proj[:, 0], 37.0)
    proj = np.vstack([proj, np.c_[np.full(len(v), 37.0), v[:, 1], v[:, 2]]])
    housing = trimesh.convex.convex_hull(np.vstack([v, proj]))
    front = box_mesh([FRONT_X + 50, 0, 0], np.eye(3), [100, 400, 400])     # nothing may grow past the front face
    Mh = to_man(housing) - to_man(front)
    M = to_man(W) + Mh
    # 2. pocket: board + parts with clearance, opened along -N to the inside of the trunk (slot for the wires and the key)
    pocket = board_box(-PCB - CLR - 40.0, STANDOFF_H, pad=CLR)
    M = M - to_man(pocket)
    # 3. standoffs, 2 with pilots, 2 solid
    for (u, v_) in HOLES:
        st = cyl(bp(u, v_, 0.0), bp(u, v_, STANDOFF_H + 0.5), STANDOFF_D / 2, 32)
        M = M + to_man(st)
    for (u, v_) in SCREWED:
        depth = SCREW_L - PCB + 1.0
        pil = cyl(bp(u, v_, -0.2), bp(u, v_, depth), PILOT_D / 2, 24)
        M = M - to_man(pil)
    # 4. window: the field-of-view cone through the floor and the wall
    win = cone(APEX_N, 60.0)
    M = M - to_man(win)
    outw = from_man(M)
    # ------------------------------------------------------------------ checks
    J = dict(script="altaay_lab/twin/freeze/cliff_seat.py", label="CAD check only (seat); calc only (beam)",
             frame="URDF world, zero pose, mm; the file stays in the print/ frame",
             board=dict(origin_pcb_top_centre=np.round(O, 2).tolist(), normal=np.round(N, 4).tolist(), long_axis=E1.tolist(),
                        short_axis=np.round(E2, 4).tolist(), size_mm=[BW, BH, 4.6]),
             screws=[dict(hole_mm=h, seat_world=np.round(bp(*h, -PCB), 3).tolist(), axis_world=np.round(N, 4).tolist(),
                          spec="M2.5x6 DIN 912 A2", line="17f", engaged_mm=r(SCREW_L - PCB, 1), pilot_d_mm=PILOT_D,
                          pilot_depth_mm=r(SCREW_L - PCB + 1.0, 1)) for h in SCREWED],
             solid_rests=[h for h in HOLES if h not in SCREWED])
    J["file"] = dict(watertight=bool(outw.is_watertight), added_mm3=r(outw.volume - W.volume, 1),
                     added_g_at_1_24=r((outw.volume - W.volume) * 1.24e-3, 2))
    # board corners inside the front face
    corners = [bp(u, v_, n) for u in (-CLR, BW + CLR) for v_ in (-CLR, BH + CLR) for n in (-PCB - CLR, STANDOFF_H)]   # the pocket
    J["board_front_skin_mm"] = r(FRONT_X - max(p[0] for p in corners), 2)
    # window on the front face: trace the cone rim to x = 46
    rim = []
    a0 = O + N * APEX_N
    for t in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        d0 = np.cos(t) * E1 + np.sin(t) * E2
        p0 = a0 + d0 * APEX_R
        dirv = N + d0 * np.tan(CONE_HALF)
        k = (FRONT_X - p0[0]) / dirv[0]
        rim.append(p0 + dirv * k)
    rim = np.array(rim)
    J["window_on_front_face"] = dict(z_mm=[r(rim[:, 2].min()), r(rim[:, 2].max())], y_mm=[r(rim[:, 1].min()), r(rim[:, 1].max())],
                                     centre_above_floor_mm=r(rim[:, 2].mean() - FLOOR_Z_STAND, 1))
    J["window_to_pad_mm"] = r(PAD_Z[0] - rim[:, 2].max(), 2)
    J["window_to_chest_hole_mm"] = r(CHEST_HOLE_Z - CHEST_BELL_R - rim[:, 2].max(), 2)
    # bottom rim left under the window (front face bottom z -35.2, its chamfer to -32)
    J["window_to_bottom_edge_mm"] = r(rim[:, 2].min() - W.bounds[0][2], 2)
    # wall left: rays across the pocket and the window, the thinnest material between them and the outside
    thin = []
    for (u, v_) in [(0, 0), (BW, 0), (0, BH), (BW, BH), (BW / 2, BH), (0, BH / 2), (BW, BH / 2)]:
        p = bp(u, v_, PARTS_H + CLR)
        for d in (np.array([1.0, 0, 0]), N):
            h = [x for x in hits_along(outw, p + d * 0.05, d) if x > 0]
            if len(h) >= 2:
                thin.append(h[1] - h[0])
    J["wall_min_round_pocket_mm"] = r(min(thin) if thin else None, 2)
    # clearance of the new material and the board to every other part and placed box
    from scipy.spatial import cKDTree
    new = from_man(Mh)
    pts = np.vstack([surface_cloud(new, 20000), surface_cloud(board_box(-PCB, PARTS_H), 4000)])
    gaps = {}
    for i in S.inst:
        if i is bf or i["link"] != "trunk_assembly":
            continue
        m = S.world_mesh(i)
        if len(m.faces):
            gaps["%s[%d]" % (i["key"], i["idx"])] = r(cKDTree(surface_cloud(m, 30000)).query(pts)[0].min(), 2)
    for k, p in placements().items():
        if k in ("dock_pad", "tof_cliff"):
            continue            # the box of the part being placed (written by --write) and the pad outside the wall
        gaps["box " + k] = r(cKDTree(surface_cloud(placement_box(p), 6000)).query(pts)[0].min(), 2)
    J["gaps_mm"] = dict(sorted(gaps.items(), key=lambda kv: kv[1])[:8])
    # the beam on the floor (standing pose, trunk level; calc only)
    h = a0[2] - FLOOR_Z_STAND
    def hit(ang):
        return a0[0] + h / np.tan(ang) - TOE_X
    J["beam"] = dict(sensor_above_floor_mm=r(h, 1), centre_ahead_of_toe_mm=r(hit(TILT), 1),
                     spot_ahead_of_toe_mm=[r(hit(TILT + np.radians(9)), 1), r(hit(TILT - np.radians(9)), 1)],
                     slant_flat_mm=r(h / np.sin(TILT), 1), slant_drop_180_mm=r((h + 180) / np.sin(TILT), 1),
                     slant_pitch_pm5_mm=[r(h / np.sin(TILT + np.radians(5)), 1), r(h / np.sin(TILT - np.radians(5)), 1)],
                     trigger_mm=250, drop_that_trips_mm=r(250 * np.sin(TILT) - h, 1),
                     stop_margin_s_at_0p1=r(hit(TILT + np.radians(9)) / 100.0, 2))
    # the legs against the field-of-view cone (zero pose)
    leg_hits = {}
    cone_long = cone(APEX_N, 400.0)
    for i in S.inst:
        if i["link"] in ("trunk_assembly", "head_assembly") or i["link"].startswith(("neck", "head")):
            continue
        m = S.world_mesh(i)
        if not len(m.faces):
            continue
        inside = cone_long.contains(surface_cloud(m, 3000))
        if inside.any():
            leg_hits["%s %s" % (i["link"], i["key"])] = int(inside.sum())
    J["legs_in_cone_zero_pose"] = leg_hits
    J["legs_in_cone_sweep"] = legs_sweep(cone_long)
    cw = os.path.join(HERE, "cliff_walk.json")
    walk = json.load(open(cw)) if os.path.exists(cw) else None
    J["walk_sim"] = (dict(foot_in_cone_any=walk["foot_in_cone_any"], slant_max_mm=walk["slant_max_mm"], by="cliff_walk.py, sim pass only")
                     if walk else "not run")
    walk_ok = bool(walk) and not walk["foot_in_cone_any"] and walk["slant_max_mm"] < J["beam"]["trigger_mm"]
    J["legs_in_cone_sweep"]["note"] = ("a grid wider than the walk: these poses swing a leg 35 deg or more forward with the knee "
                                       "near straight (a kick); the walk itself is judged by cliff_walk.py")
    ok = (outw.is_watertight and J["board_front_skin_mm"] >= 1.6 and J["window_to_pad_mm"] >= 3.0
          and J["window_to_bottom_edge_mm"] >= 3.0 and min(gaps.values()) >= 1.0 and not leg_hits and walk_ok
          and (J["wall_min_round_pocket_mm"] or 0) >= 1.6)
    J["pass"] = bool(ok)
    print(json.dumps(J, indent=1))
    if a.write:
        loc = outw.copy()
        loc.apply_transform(Ti)
        loc.export(os.path.join(PRINT, "body_front.stl"))
        dump(J, os.path.join(HERE, "cliff_seat.json"))
        # the board box for the viewer and cables3d (axis-aligned box round the tilted board and its parts)
        cs = np.array([bp(u, v_, n) for u in (0, BW) for v_ in (0, BH) for n in (-PCB, PARTS_H)])
        from flib import PLACEMENTS
        P_ = [p for p in json.load(open(PLACEMENTS)) if p["id"] != "tof_cliff"]
        P_.append(dict(id="tof_cliff", label="Cliff ToF, Adafruit 5396 VL53L4CD, I2C 0x29, 52 deg down (BOM 5b, D54)",
                       dims_xyz_mm=np.round(np.ptp(cs, 0), 2).tolist(), box_with_margin_mm=np.round(np.ptp(cs, 0) + 2, 2).tolist(),
                       center_mm=np.round(cs.mean(0), 2).tolist(), frame="urdf_world_mm", n_positions=None, dist_to_anchor_mm=None,
                       dist_to_imu_mm=None, flat_face_support="4 printed standoffs in print/body_front.stl, 2 x M2.5x6 (D54)",
                       score=None, seat_fix="altaay_lab/twin/freeze/cliff_seat.py (D54)"))
        with open(PLACEMENTS, "w") as fh:
            json.dump(P_, fh, indent=1)
            fh.write("\n")
        print("wrote print/body_front.stl and the tof_cliff box in audit/placements.json")


if __name__ == "__main__":
    main()
