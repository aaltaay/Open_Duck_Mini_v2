"""camera_seat.py: Camera Module 3 seat, its 4 screws and its clearances, measured on print/head.stl. CAD check only.

Run: python3 altaay_lab/twin/complete3d/camera_seat.py   (needs a base viewer run in $C3D_VIEWER for the placeholder boxes)
Writes altaay_lab/twin/complete3d/camera_seat.json.

Method: the 4 blind pilots and the lens opening are found in audit/sites_head.json (the same pilots the viewer uses),
then every number is measured again by ray casts on print/head.stl in the URDF world frame: pilot diameter, depth,
material past the pilot bottom, boss face flatness, boss radius, lens opening centre and diameter, the free height in
front of the PCB and the free depth behind it (head shell plus every other head part and placeholder box).
Board numbers are the cited ones below; the PCB thickness and the connector side are not published at a source this
session can reach: they are BLOCKERS and the checks run at the stand-in and at a range.
"""
import itertools
import json
import os

import numpy as np
import trimesh

from common import (FASTENERS, CABLES3D, HEAD_LINK, HERE, LAB, all_hits, first_hits, glb_meshes, head_instances,
                    inst_name, inst_world, perp_basis, scene, write_json)

SRC = {
    "board": "[I] HARDWARE_AUDIT.md B9, from the Raspberry Pi Camera Module 3 mechanical drawing (datasheets.raspberrypi.com): "
             "board 25 x 24 mm, 4 holes 2.2 mm, 2 mm from the edges, 21 x 12.5 mm pattern",
    "lens": "[I] viewer/make_viewer_data.py lens note (drawing RP-008153-DS-1, checked 2026-11-01): lens dia 5.75 mm on the upper "
            "hole row, 14.5 mm from the bottom edge",
    "depth": "[I] BOM.md E6 and the viewer catalog: 25 x 24 x 11.5 mm overall",
    "screw": "[I] BOM.md 17h: METALLIXITY M2 pan head kit, M2 head 3.7 x 1.4 mm; M2x4 is its shortest M2",
    "rule": "[I] fasteners.json meta.sources.pla_rule: screw-in depth 2.0 x d in plastic (Westfield table 2, ABS row)",
    "fpc": "[I] CABLE_MAP.md D12 and BOM.md E7: camera end 15-pin 1 mm FPC, Pi end 22-pin 0.5 mm FPC",
}
BLOCKERS = {
    "pcb_t": "PCB thickness not published at a reachable source (fasteners.json F344 to F347 note 'PCB thickness UNVERIFIED'). "
             "Stand-in 1.0 mm, range 0.8 to 1.6 mm checked. Settles it: caliper on the received Camera Module 3 (parts check, TO8).",
    "conn_side": "Which face of the PCB carries the 15-pin connector, and the slot height, are not in any cited text in the repo "
                 "(RP-008153-DS-1 not reachable from this session: datasheets.raspberrypi.com is blocked). Both faces are checked. "
                 "Settles it: RP-008153-DS-1, or a look at the received camera.",
    "stack": "How the 11.5 mm splits between the lens side and the back side is not cited. The check below uses the free "
             "space on both sides of the PCB against the full 11.5 mm. Settles it: RP-008153-DS-1.",
}
T_PCB = 1.0
T_RANGE = (0.8, 1.0, 1.2, 1.6)
BOARD = (25.0, 24.0)
HOLE_EDGE = 2.0
PATTERN = (21.0, 12.5)
LENS_ROW_FROM_BOTTOM = 14.5
DEPTH = 11.5
SCREW_L, SCREW_D, HEAD_DK, HEAD_K = 4.0, 2.0, 3.7, 1.4


def main():
    S = scene()
    hi = [i for i in S.inst if i["key"] == "head"][0]
    Th = inst_world(S, hi)
    head_w = S.mesh(hi).copy()
    head_w.apply_transform(Th)
    sites = json.load(open(os.path.join(LAB, "audit", "sites_head.json")))
    pil, lens = [], []
    for s in sites:
        o, ax = np.array(s["o"], float), np.array(s["ax"], float)
        if abs(ax[0]) < 0.9:
            continue
        for t0, t1, part, kind, d, _ in s["segs"]:
            if part != "head":
                continue
            e = sorted([o + ax * t0, o + ax * t1], key=lambda p: p[0])
            if 1.55 <= d <= 1.75 and 2.5 <= t1 - t0 <= 4.0:
                pil.append((e[0], e[1], d))
            elif 7.0 <= d <= 9.5:
                lens.append((e[0], e[1], d))
    to_w = lambda p: (Th @ np.r_[p, 1.0])[:3]
    quad = None
    for q in itertools.combinations(range(len(pil)), 4):
        P = np.array([pil[k][0] for k in q])
        dd = sorted(np.linalg.norm(P[a] - P[b]) for a, b in itertools.combinations(range(4), 2))
        if np.allclose(dd, [12.5, 12.5, 21.0, 21.0, 24.43, 24.43], atol=0.5):
            quad = q
            break
    assert quad is not None, "camera pilots not found"
    F = np.array([to_w(pil[k][0]) for k in quad])            # boss faces (pilot mouths), world
    a = to_w(pil[quad[0]][1]) - F[0]
    a /= np.linalg.norm(a)                                   # into the pilot = toward the front wall = lens direction
    Pc = F.mean(0)
    # ---- pilots, measured by ray casts
    U = [np.cos(t) * perp_basis(a)[0] + np.sin(t) * perp_basis(a)[1] for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
    pilots = []
    for f in F:
        h = all_hits(head_w, f + a * 0.3, a)
        depth = 0.3 + h[0]
        beyond = (h[1] - h[0]) if len(h) > 1 else None
        m = f + a * depth / 2
        rad = np.array([first_hits(head_w, m, u)[0] for u in U])
        dia = 2 * np.median(rad)
        outer = []
        for u in U:
            hh = all_hits(head_w, m, u)
            outer.append(hh[1] if len(hh) > 1 else np.inf)
        face = first_hits(head_w, np.array([f - a * 2 + u * (dia / 2 + 0.5) for u in U]), a) - 2.0
        pilots.append(dict(face_world=f, axis_world=a, d_mm=dia, depth_mm=depth, material_past_bottom_mm=beyond,
                           boss_radius_min_mm=float(np.min(outer)), face_flatness_mm=float(np.ptp(face[np.isfinite(face)]))))
    # ---- board frame
    pairs = {k: None for k in ("21", "12.5")}
    for i, j in itertools.combinations(range(4), 2):
        v = F[j] - F[i]
        v -= (v @ a) * a
        L = np.linalg.norm(v)
        if abs(L - 21.0) < 0.6 and pairs["21"] is None:
            pairs["21"] = v / L
        if abs(L - 12.5) < 0.6 and pairs["12.5"] is None:
            pairs["12.5"] = v / L
    ys = pairs["12.5"] - (pairs["12.5"] @ pairs["21"]) * pairs["21"]
    ys /= np.linalg.norm(ys)
    lw = [(to_w(e0), to_w(e1), d) for e0, e1, d in lens]
    li = min(range(len(lw)), key=lambda k: np.linalg.norm((lw[k][0] - Pc) - ((lw[k][0] - Pc) @ a) * a))
    L_in, L_out, L_d = lw[li]
    if (L_in - Pc) @ ys < 0:
        ys = -ys                                             # Y_c toward the lens row (the board's top edge)
    Z = a
    Y = ys
    X = np.cross(Y, Z)
    R = np.c_[X, Y, Z]
    face_spread = float(np.ptp((F - Pc) @ a))
    # board outline: lower hole row 2 mm from the bottom edge; upper row (lens row) 14.5 mm from it
    y_bottom = -(PATTERN[1] / 2 + HOLE_EDGE)                 # -8.25
    y_top = y_bottom + BOARD[1]                              # +15.75
    Bc = Pc + Y * (y_bottom + y_top) / 2                     # board centre on the front face plane
    # ---- lens opening, measured again on the wall mid plane
    mid = (L_in + L_out) / 2
    hits = []
    for u in U:
        t = first_hits(head_w, mid, u)[0]
        if np.isfinite(t):
            hits.append(mid + u * t)
    Hp = np.array(hits)
    u1, u2 = perp_basis(a)
    A2 = np.c_[2 * (Hp - mid) @ u1, 2 * (Hp - mid) @ u2, np.ones(len(Hp))]
    b2 = ((Hp - mid) @ u1) ** 2 + ((Hp - mid) @ u2) ** 2
    cx, cy, cc = np.linalg.lstsq(A2, b2, rcond=None)[0]
    lens_c = mid + cx * u1 + cy * u2
    lens_d = 2 * np.sqrt(cc + cx ** 2 + cy ** 2)
    rim = np.array([lens_c - a * 3 + u * (lens_d / 2 + 1.0) for u in U])
    inner = np.nanmedian(np.where(np.isfinite(t_ := first_hits(head_w, rim, a)), t_, np.nan)) - 3.0
    wall_in = lens_c + a * inner
    wh = all_hits(head_w, lens_c - a * 3 + U[0] * (lens_d / 2 + 1.0), a)
    wall_t = (wh[1] - wh[0]) if len(wh) > 1 else None
    lens_pred = Pc + Y * PATTERN[1] / 2
    dl = (lens_c - lens_pred) - ((lens_c - lens_pred) @ a) * a
    boss_h = float((wall_in - Pc) @ a)                       # PCB front face to the wall inner face, at the lens
    # ---- neighbours: every other head part and the placeholder boxes in the head (not the camera box)
    S_head = [i for i in head_instances(S) if i["key"] != "head"]
    nb = {inst_name(i): S.world_mesh(i) for i in S_head}
    for k, m in glb_meshes(names={"ph-reg_5v", "ph-amp", "ph-speaker", "ph-led_1", "ph-led_2", "ph-led_3"}).items():
        nb[k] = m
    nb_all = trimesh.util.concatenate(list(nb.values()) + [head_w])
    # free height in front of the PCB (to the wall or a part) and free depth behind it, on a 1 mm grid of the board
    Rb = min(p["boss_radius_min_mm"] for p in pilots)
    front, back, lens_zone = [], [], []
    for xx in np.arange(-12.0, 12.01, 1.0):
        for yy in np.arange(y_bottom + 0.5, y_top - 0.49, 1.0):
            p = Pc + X * xx + Y * yy
            if min(np.linalg.norm((p - f) - ((p - f) @ a) * a) for f in F) < Rb + 0.3:
                continue
            fr = first_hits(nb_all, p + a * 0.02, a)[0]
            in_lens = np.linalg.norm((p - lens_c) - ((p - lens_c) @ a) * a) < lens_d / 2
            (lens_zone if in_lens else front).append((xx, yy, fr))
    for t in T_RANGE:
        bk = []
        for xx in np.arange(-12.0, 12.01, 1.0):
            for yy in np.arange(y_bottom + 0.5, y_top - 0.49, 1.0):
                p = Pc + X * xx + Y * yy - a * (t + 0.02)
                bk.append((xx, yy, first_hits(nb_all, p, -a)[0]))
        back.append((t, bk))
    fr_min = min(front, key=lambda q: q[2])
    # PCB slab interference (CAD check only): grid points inside the slab against every neighbour and the shell
    slab_pts = np.array([Pc + X * xx + Y * yy - a * zz for xx in np.arange(-12.25, 12.26, 0.7)
                         for yy in np.arange(y_bottom + 0.25, y_top - 0.24, 0.7) for zz in (0.1, T_PCB / 2, T_PCB - 0.1)])
    slab_hits = {}
    for k, m in list(nb.items()) + [("head shell", head_w)]:
        lo, hi_ = m.bounds
        sel = np.all((slab_pts > lo - 0.1) & (slab_pts < hi_ + 0.1), axis=1)
        if not sel.any():
            continue
        n_in = int(np.sum(m.contains(slab_pts[sel])))
        if n_in:
            slab_hits[k] = n_in
    # ---- screws: head seat on the PCB back face, +a into the pilot
    old = {x["id"]: x for x in json.load(open(FASTENERS))["fasteners"] if x.get("source") == "camera"}
    screws = []
    for k, (f, p) in enumerate(zip(F, pilots)):
        seat = f - a * T_PCB
        oid = min(old, key=lambda i: np.linalg.norm(np.array(old[i]["seat_world"]) - seat))
        heads = np.array([seat - a * z + (np.cos(t) * u1 + np.sin(t) * u2) * HEAD_DK / 2
                          for z in (0.2, 0.7, 1.2) for t in np.linspace(0, 2 * np.pi, 16, endpoint=False)])
        q = trimesh.proximity.closest_point(nb_all, heads)
        clr = float(np.min(q[1]))
        rows = []
        for t in T_RANGE:
            e = SCREW_L - t
            rows.append(dict(pcb_t=t, engaged_mm=e, to_bottom_mm=p["depth_mm"] - e, rule_mm=2 * SCREW_D,
                             verdict=("BOTTOMS" if e > p["depth_mm"] else ("below rule" if e < 2 * SCREW_D else "ok"))))
        screws.append(dict(id=oid, spec="M2x4 self-tapping pan head (BOM 17h)", seat_world=seat, axis_world=a,
                           tip_world=seat + a * SCREW_L, length_mm=SCREW_L, head_dk=HEAD_DK, head_k=HEAD_K,
                           old_seat_world=old[oid]["seat_world"],
                           moved_mm=float(np.linalg.norm(np.array(old[oid]["seat_world"]) - seat)),
                           pilot_depth_mm=p["depth_mm"], material_past_bottom_mm=p["material_past_bottom_mm"],
                           head_clearance_mm=clr, by_pcb_t=rows))
    # ---- viewer box today
    vb = glb_meshes(names={"ph-camera"}).get("ph-camera")
    viewer = None
    if vb is not None:
        vc = vb.bounds.mean(0)
        viewer = dict(center_world=vc, extents=vb.extents, board_centre_now=Bc - a * T_PCB / 2,
                      offset_mm=float(np.linalg.norm(vc - (Bc - a * T_PCB / 2))),
                      offset_along_Y_mm=float((vc - Bc) @ Y), offset_along_Z_mm=float((vc - Bc) @ a),
                      inside_shell_points=int(np.sum(head_w.contains(vb.sample(400)))))
    # ---- D12 connector end candidates (15-pin, bottom edge centre, strip leaves along -Y in the board plane)
    edge = Pc + Y * y_bottom
    ends = {"back face": edge - a * (T_PCB + 1.0), "front face": edge + a * 1.0}
    c3 = json.load(open(CABLES3D))
    cam_end = [e for e in c3["cable_ends"] if e["id"] == "CAM.CSI"][0]
    T0h = S.T0[HEAD_LINK]
    Tcw = np.eye(4)
    Tcw[:3, :3] = R
    Tcw[:3, 3] = Bc
    out = dict(
        meta=dict(script="altaay_lab/twin/complete3d/camera_seat.py", label="CAD check only", frame="URDF world, zero pose, mm",
                  sources=SRC, blockers=BLOCKERS, pcb_t_standin=T_PCB),
        pilots=pilots, pattern_centre_world=Pc, boss_face_spread_mm=face_spread,
        frame=dict(note="camera frame C: origin = board centre on the PCB front face (the boss faces); X along the 21 mm hole "
                        "spacing, Y along the 12.5 mm spacing toward the lens row (board top edge), Z = lens axis, forward",
                   T_cam_world=Tcw, T_cam_link=np.linalg.inv(T0h) @ Tcw, link=HEAD_LINK,
                   board_centre_offset_from_pattern_mm=(y_bottom + y_top) / 2),
        board=dict(dims_mm=[BOARD[0], BOARD[1], T_PCB], y_bottom=y_bottom, y_top=y_top,
                   pcb_slab_center_world=Bc - a * T_PCB / 2, R_world=R, slab_interference_points=slab_hits),
        lens=dict(opening_centre_world=lens_c, opening_d_mm=lens_d, sites_d_mm=L_d, predicted_centre_world=lens_pred,
                  offset_in_plane_mm=dl, offset_X_mm=float(dl @ X), offset_Y_mm=float(dl @ Y), wall_t_mm=wall_t,
                  pcb_front_to_wall_mm=boss_h, lens_d_drawing_mm=5.75),
        free=dict(front_min_mm=fr_min[2], front_min_at_XY=fr_min[:2], front_median_mm=float(np.median([q[2] for q in front])),
                  lens_zone_min_mm=min((q[2] for q in lens_zone), default=None),
                  back_min_mm={str(t): float(min(q[2] for q in bk)) for t, bk in back},
                  back_min_at_XY={str(t): min(bk, key=lambda q: q[2])[:2] for t, bk in back},
                  stack_room_mm={str(t): float(fr_min[2] + t + min(q[2] for q in bk)) for t, bk in back}, need_mm=DEPTH),
        screws=screws, viewer_box_today=viewer,
        d12_end=dict(candidates_world=ends, exit_dir_world=-Y, width_dir_world=X, plane_normal_world=a,
                     cables3d_CAM_CSI_world=cam_end["p_world0"], cables3d_dir=cam_end["dir_world0"],
                     moved_mm={k: float(np.linalg.norm(np.array(cam_end["p_world0"]) - v)) for k, v in ends.items()}),
    )
    write_json(out, os.path.join(HERE, "camera_seat.json"))
    pi = [i for i in head_instances(S) if "rasp" in i["key"].lower() or i["key"].lower().startswith("pi")]
    for i in pi:
        m = S.world_mesh(i)
        v = m.vertices - m.vertices.mean(0)
        w_, vec = np.linalg.eigh(v.T @ v)
        print("pi", inst_name(i), "bounds", m.bounds.round(1).tolist(), "normal", vec[:, 0].round(3).tolist())
    print(json.dumps({k: out[k] for k in ("lens", "free", "viewer_box_today", "d12_end")}, default=lambda o: np.round(o, 2).tolist())[:2400])
    print("pilots", [(round(p["d_mm"], 2), round(p["depth_mm"], 2), p["material_past_bottom_mm"] and round(p["material_past_bottom_mm"], 2),
                      round(p["boss_radius_min_mm"], 2), round(p["face_flatness_mm"], 2)) for p in pilots], "spread", round(face_spread, 3))
    print("slab interference", slab_hits)
    for s in screws:
        print(s["id"], np.round(s["seat_world"], 2).tolist(), "moved", round(s["moved_mm"], 2), "head clr", round(s["head_clearance_mm"], 2),
              [(q["pcb_t"], round(q["to_bottom_mm"], 2), q["verdict"]) for q in s["by_pcb_t"]])


if __name__ == "__main__":
    main()
