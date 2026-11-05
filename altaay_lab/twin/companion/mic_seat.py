"""mic_seat.py: seats for the two I2S MEMS microphone boards in the head (V1 track 11, D47). CAD check only.

Run: python3 altaay_lab/twin/companion/mic_seat.py
Writes altaay_lab/twin/companion/mic_seats.json and altaay_lab/twin/companion/stl/head.stl (print/head.stl plus the
mic bosses, the port tubes and the two sound ports; the print/ frame is kept, so orientation and supports stay).

Method:
  1. Search the inner face of each side wall of print/head.stl (URDF world, zero pose) for a flat patch that takes
     the 16.51 x 12.7 mm board: rays from inside the head along +y and -y on a grid of (x, z) seats; for each seat the
     wall is fitted with a plane over 15 rays across the board footprint (flatness, thickness, normal).
  2. The board sits BOARD_GAP mm off the inner wall, parallel to the fitted plane, on two printed bosses at its two
     plated holes (a mirror pair about the board centre line, D42), M2 self-tapping into 1.65 mm pilots (the camera
     pilot, D34). A printed tube joins the wall to the board around the bottom port of the mic; a 1.2 mm sound port
     runs through the wall on the port axis (a sound hole, kept open by D39).
  3. Clearance of the board envelope (PCB, top parts and the soldered wires) to every other head part at the zero
     pose: the head shell itself (away from the bosses), the head internals, the head_roll_mount, the neck servo case
     and horns, the SG90 antenna servos.
  4. The left seat is chosen, the right one is its mirror (y -> -y), and both are checked on the real mesh.
Sources:
  board: [I] Adafruit-I2S-MEMS-Microphone-Breakout-PCB (github.com/adafruit, the 6049 board files, read 2026-11-05):
         outline 16.51 x 12.7 mm, 2 plated holes 2.5 mm at (2.54, 10.16) and (13.97, 10.16), mic footprint
         SPH0645LM4H at (8.255, 7.112), 6 pads at 2.54 mm on y = 2.54. Adafruit states SPH0645LM4H is the drop-in
         part for the discontinued ICS-43434 (adafruit.com/product/6049 text, seen in a search result 2026-11-05).
  BLOCKERS: the 3421 (SPH0645) board outline is not read (adafruit.com is not reachable from this session); the
         SPH0645LM4H port offset and the PCB thickness are not read (the Knowles datasheet hosts are not reachable).
         Stand-ins: the 6049 outline and holes, the port at the mic footprint centre, PCB 1.6 mm (checked 0.8 to 1.6).
         The 2.0 mm port tube bore takes a port offset up to 0.4 mm. Settles it: caliper on the received board.
"""
import json
import os
import sys

import numpy as np
import trimesh
import manifold3d

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "twin", "complete3d"))
from common import scene, inst_world, head_instances, inst_name   # noqa: E402

BOARD = dict(w=16.51, h=12.7, holes=[(2.54, 10.16), (13.97, 10.16)], mic=(8.255, 7.112), hole_d=2.5)
PCB_T, PCB_T_RANGE = 1.6, (0.8, 1.6)
TOP_PARTS = 2.5          # tallest part on the top face (mic can and 0603 parts, stand-in) plus the soldered wire bend
WIRE_BEND = 4.0
BOARD_GAP = 3.0          # wall to board back face
BOSS_D, PILOT_D, PILOT_DEPTH = 5.0, 1.65, 5.0
TUBE_OD, TUBE_ID, PORT_D = 4.0, 2.0, 1.2
SCREW = dict(spec="M2x6 self-tapping pan head", line="17h", d=2.0, L=6.0, rule_engage=4.0, head_dk=3.7, head_k=1.4)
OUT_STL = os.path.join(HERE, "stl", "head.stl")
OUT_JSON = os.path.join(HERE, "mic_seats.json")


def plane_fit(P):
    c = P.mean(0)
    _, _, vt = np.linalg.svd(P - c)
    n = vt[2]
    return c, n, float(np.abs((P - c) @ n).max())


def wall_at(head, x, z, side):
    """inner and outer wall hits along side*y from (x, 0, z): (p_in, p_out) or None"""
    o = np.array([[x, 0.0, z]]); d = np.array([[0.0, side, 0.0]])
    loc, _, _ = head.ray.intersects_location(o, d)
    if len(loc) < 2:
        return None
    loc = loc[np.argsort(np.abs(loc[:, 1]))]
    # the outermost pair is the side wall
    return loc[-2], loc[-1]


def seat_frame(head, x, z, side):
    """board frame on the inner wall: origin at the board corner (0, 0), axes u (along x), v (up), n (inward)"""
    w = wall_at(head, x, z, side)
    if w is None:
        return None
    pts, outs = [], []
    for du in np.linspace(-BOARD["w"] / 2, BOARD["w"] / 2, 5):
        for dv in np.linspace(-BOARD["h"] / 2, BOARD["h"] / 2, 3):
            ww = wall_at(head, x + du, z + dv, side)
            if ww is None:
                return None
            pts.append(ww[0]); outs.append(ww[1])
    pts, outs = np.array(pts), np.array(outs)
    c, n, flat = plane_fit(pts)
    if n[1] * side > 0:
        n = -n                       # inward
    thick = float(np.median(np.linalg.norm(outs - pts, axis=1)))
    u = np.array([1.0, 0, 0]); u = u - (u @ n) * n; u /= np.linalg.norm(u)
    v = np.cross(n, u) if side > 0 else np.cross(u, n)
    if v[2] < 0:
        v = -v
    # board centre on the plane at the ray point
    centre = w[0] + ((c - w[0]) @ n) * n
    return dict(centre=centre, u=u, v=v, n=n, flat=flat, thick=thick, inner=w[0], outer=w[1])


def board_point(F, bu, bv, off):
    """board coordinates (bu, bv from the board corner, off along n from the inner wall) to world"""
    return F["centre"] + (bu - BOARD["w"] / 2) * F["u"] + (bv - BOARD["h"] / 2) * F["v"] + off * F["n"]


def envelope_box(F, pcb_t=PCB_T):
    """the board envelope as a box mesh in world: PCB plus top parts plus the wire bend"""
    depth = pcb_t + TOP_PARTS + WIRE_BEND
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2] = F["u"], F["v"], F["n"]
    T[:3, 3] = F["centre"] + (BOARD_GAP + depth / 2) * F["n"]
    return trimesh.creation.box(extents=[BOARD["w"], BOARD["h"], depth], transform=T)


def cyl(p0, p1, r, sections=40):
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)


def surface_cloud(m, n=40000):
    pts = trimesh.sample.sample_surface_even(m, n, seed=2)[0] if len(m.faces) else np.zeros((0, 3))
    return np.vstack([pts, m.vertices])


def box_clearance(F, cloud, pcb_t=PCB_T):
    """smallest distance from the board envelope box to a point cloud (negative: points inside the box, by depth)"""
    depth = pcb_t + TOP_PARTS + WIRE_BEND
    c = F["centre"] + (BOARD_GAP + depth / 2) * F["n"]
    R = np.stack([F["u"], F["v"], F["n"]], 1)
    q = (cloud - c) @ R
    half = np.array([BOARD["w"] / 2, BOARD["h"] / 2, depth / 2])
    out = np.maximum(np.abs(q) - half, 0.0)
    dist = np.linalg.norm(out, axis=1)
    inside = np.all(np.abs(q) < half, axis=1)
    if inside.any():
        return -float(np.min(half - np.abs(q[inside]), axis=None))
    return float(dist.min())


def clearance(F, clouds, pcb_t=PCB_T):
    return {k: box_clearance(F, v, pcb_t) for k, v in clouds.items()}


def main():
    S = scene()
    hi = [i for i in head_instances(S) if inst_name(i).startswith("head[")][0]
    Thead = inst_world(S, hi)
    head = S.world_mesh(hi)
    others = {}
    for i in head_instances(S):
        if i is hi:
            continue
        m = S.world_mesh(i)
        if len(m.faces) and np.ptp(m.bounds, axis=0).min() > 0.5:
            others[inst_name(i)] = surface_cloud(m, 20000)
    shell = surface_cloud(head, 200000)
    # search the left wall (side +1)
    best = None
    rows = []
    for x in np.arange(-50.0, -4.9, 2.5):
        for z in np.arange(190.0, 214.1, 2.0):
            F = seat_frame(head, x, z, +1)
            if F is None or F["flat"] > 0.3 or not (2.4 < F["thick"] < 4.5):
                continue
            c = clearance(F, others)
            cs = box_clearance(F, shell)      # the head shell (the box starts BOARD_GAP off the seat wall)
            worst = min(min(c.values()), cs)
            rows.append(dict(x=float(x), z=float(z), flat=round(F["flat"], 3), thick=round(F["thick"], 2), worst=round(worst, 2)))
            score = worst - 0.02 * abs(z - 202)
            if worst >= 1.0 and (best is None or score > best[0]):
                best = (score, x, z, F, c, cs)
    if best is None:
        raise SystemExit("no left seat clears 1.0 mm")
    _, bx, bz, FL, cL, csL = best
    FR = seat_frame(head, bx, bz, -1)
    sides = {"left": FL, "right": FR}
    add, cut, seats = [], [], {}
    for name, F in sides.items():
        c = {k: min(clearance(F, others, t)[k] for t in PCB_T_RANGE) for k in others}
        cs = min(box_clearance(F, shell, t) for t in PCB_T_RANGE)
        holes = []
        for (hu, hv) in BOARD["holes"]:
            base = board_point(F, hu, hv, -0.4)               # 0.4 mm into the wall so the union fuses
            top = board_point(F, hu, hv, BOARD_GAP)
            add.append(cyl(base, top, BOSS_D / 2))
            pilot_top = board_point(F, hu, hv, BOARD_GAP + 0.01)
            pilot_bot = board_point(F, hu, hv, BOARD_GAP - PILOT_DEPTH)
            cut.append(cyl(pilot_bot, pilot_top + 0.2 * F["n"], PILOT_D / 2, 24))
            # material left past the pilot bottom, along -n, to the outer surface
            loc, _, _ = head.ray.intersects_location([pilot_bot], [-F["n"]])
            rem = float(np.min(np.linalg.norm(loc - pilot_bot, axis=1))) if len(loc) else None
            holes.append(dict(seat_world=np.round(top, 3).tolist(), axis_world=np.round(-F["n"], 4).tolist(), material_past_pilot_mm=None if rem is None else round(rem, 2)))
        pu, pv = BOARD["mic"]
        t0 = board_point(F, pu, pv, -0.4); t1 = board_point(F, pu, pv, BOARD_GAP)
        add.append(cyl(t0, t1, TUBE_OD / 2))
        cut.append(cyl(board_point(F, pu, pv, 0.0), t1 + 0.2 * F["n"], TUBE_ID / 2, 24))
        port_out = F["outer"] + ((board_point(F, pu, pv, 0.0) - F["inner"]))   # same offset on the outer face
        cut.append(cyl(board_point(F, pu, pv, 0.05) , board_point(F, pu, pv, -F["thick"] - 1.5), PORT_D / 2, 24))
        engage = {f"pcb_{t}": round(SCREW["L"] - t, 2) for t in PCB_T_RANGE}
        seats[name] = dict(
            board_centre_world=np.round(board_point(F, BOARD["w"] / 2, BOARD["h"] / 2, BOARD_GAP), 3).tolist(),
            mic_port_world=np.round(board_point(F, pu, pv, 0.0), 3).tolist(),
            port_outer_world=np.round(port_out, 3).tolist(),
            inward_normal=np.round(F["n"], 4).tolist(), wall_flatness_mm=round(F["flat"], 3), wall_thickness_mm=round(F["thick"], 2),
            clearance_mm={k: round(v, 2) for k, v in sorted(c.items(), key=lambda kv: kv[1])[:6]}, shell_clearance_mm=round(cs, 2),
            screws=holes, screw_engagement_mm=engage)
    # build: union bosses and tubes, then cut pilots, tube bores and ports; in the print/ frame
    Tinv = np.linalg.inv(Thead)
    to_m = lambda t: manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    base_local = trimesh.load(hi["path"], force="mesh")
    M = to_m(base_local)
    for a in add:
        a = a.copy(); a.apply_transform(Tinv); M = M + to_m(a)
    for c_ in cut:
        c_ = c_.copy(); c_.apply_transform(Tinv); M = M - to_m(c_)
    mo = M.to_mesh()
    out = trimesh.Trimesh(np.asarray(mo.vert_properties, float)[:, :3], np.asarray(mo.tri_verts), process=False)
    os.makedirs(os.path.dirname(OUT_STL), exist_ok=True)
    out.export(OUT_STL)
    # symmetry of the pair and the DOA geometry
    pl, pr = np.array(seats["left"]["mic_port_world"]), np.array(seats["right"]["mic_port_world"])
    sym = float(np.linalg.norm(pl * [1, -1, 1] - pr))
    # head link frame
    Tlink = S.T0["head_assembly"]
    to_link = lambda p: (np.linalg.inv(Tlink) @ np.r_[p, 1.0])[:3]
    checks = dict(
        watertight=bool(out.is_watertight), volume_added_mm3=round(float(out.volume - base_local.volume), 1),
        stl_bytes=os.path.getsize(OUT_STL), left_right_mirror_error_mm=round(sym, 3),
        min_part_clearance_mm=round(min(min(s["clearance_mm"].values()) for s in seats.values()), 2),
        min_shell_clearance_mm=round(min(s["shell_clearance_mm"] for s in seats.values()), 2),
        screw_engagement_min_mm=min(min(s["screw_engagement_mm"].values()) for s in seats.values()),
        engagement_rule_mm=SCREW["rule_engage"],
        material_past_pilot_min_mm=min(h["material_past_pilot_mm"] for s in seats.values() for h in s["screws"] if h["material_past_pilot_mm"] is not None))
    checks["pass"] = bool(checks["watertight"] and checks["min_part_clearance_mm"] >= 1.0 and checks["min_shell_clearance_mm"] >= 0.5
                          and checks["screw_engagement_min_mm"] >= SCREW["rule_engage"] and checks["material_past_pilot_min_mm"] >= 0.8
                          and checks["left_right_mirror_error_mm"] < 1.0)
    J = dict(meta=dict(script="altaay_lab/twin/companion/mic_seat.py", label="CAD check only", frame="URDF world, zero pose, mm",
                       board=BOARD, pcb_t_mm=PCB_T, board_gap_mm=BOARD_GAP, boss_d_mm=BOSS_D, pilot=dict(d=PILOT_D, depth=PILOT_DEPTH),
                       tube=dict(od=TUBE_OD, id=TUBE_ID), port_d_mm=PORT_D, screw=SCREW,
                       blockers=["3421 board outline not read (adafruit.com blocked here); 6049 board files used",
                                 "SPH0645LM4H port offset and PCB thickness not read (datasheet hosts blocked); port at the footprint centre, PCB 0.8 to 1.6 mm checked"]),
             seat_search=dict(n_candidates=len(rows), chosen=dict(x=bx, z=bz)),
             seats=seats,
             mics_head_link_mm=dict(left=np.round(to_link(pl), 2).tolist(), right=np.round(to_link(pr), 2).tolist()),
             mic_spacing_mm=round(float(np.linalg.norm(pl - pr)), 2),
             checks=checks)
    with open(OUT_JSON, "w") as f:
        json.dump(J, f, indent=1)
    print(json.dumps(dict(chosen=(bx, bz), spacing=J["mic_spacing_mm"], link=J["mics_head_link_mm"], checks=checks), indent=1))


if __name__ == "__main__":
    main()
