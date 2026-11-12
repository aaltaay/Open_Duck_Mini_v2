#!/usr/bin/env python3
"""nest_checks.py: the CAD checks of the nest. Writes nest_checks.json and prints a PASS or FAIL line per check.

Run: python3 nest_checks.py     (after duck_pins.py, nest_parts.py, nest_assembly.py and walk_clearance.py)
Labels: CAD check only (geometry measured on the meshes), calc only (arithmetic), sim pass only (numbers taken from
NEST_SIM.md, sit_contacts.json or walk_clearance.json), est / UNVERIFIED (pin dimensions not read from the data sheet).

  A  interference: the new duck parts against every trunk part, the placed boards (audit/placements.json) and the trunk
     fasteners (fasteners/fasteners.json); the leads against the same.
  B  moving parts: the pins against the legs and feet along the sit path, in the sit, standing, and over the hip ranges.
  C  pin reach across the 2.5 to 6.0 mm bumper gap, forces, the flush stop.
  C2 the torque-off sit with the chosen pins in the sim harness (pins_sit_check.json, sim pass only).
  D  ground clearance standing (CAD) and walking (sim).
  E  mass added to the duck.
  F  print orientation and overhang of the printed parts.
  G  the mat and rim: landing window, margins, steps, the box.
  H  fasteners and holes (D42, D39).
"""
import json
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestcad_lib as N  # noqa: E402
from nestcad_lib import L  # noqa: E402
import nest_assembly as A  # noqa: E402
import nest_parts as NPARTS  # noqa: E402

RES, FAIL = {}, []


def verdict(name, ok, text):
    print("%-4s %s: %s" % ("PASS" if ok else "FAIL", name, text))
    if not ok:
        FAIL.append(name)
    return bool(ok)


def seg_dist(P, a, b):
    """distance of points P to the segment a-b"""
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def sample_tube(pts, step=1.0):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / step) + 1)
        out.append(a + np.linspace(0, 1, n)[:, None] * (b - a))
    return np.vstack(out)


def min_gap_points(mesh, P):
    """smallest distance from points P to the surface of mesh, and whether any point is inside (watertight meshes)"""
    c, d, _ = trimesh.proximity.closest_point(mesh, P)
    k = int(np.argmin(d))
    inside = bool(mesh.contains(P[[k]])[0]) if mesh.is_watertight else False
    return float(d[k]), P[k], inside


# ------------------------------------------------------------------------------------------------------------------
def check_A(S, DP):
    """static interference in the trunk frame"""
    P = N.PIN
    trunk = [(i, S.world_mesh(i)) for i in S.inst if i["link"] == N.TR and i["key"] not in ("body_middle_bottom",)]
    Tb = S.T0[N.TR] @ L.inst(S, N.TR, "body_middle_bottom")["T"]
    body_new = A.load_part("body_middle_bottom")
    body_new.apply_transform(Tb)
    new = {}
    for which, stem, car in (("seat", "sit_seat", "pin_carrier_seat"), ("bump", "sit_bumper", "pin_carrier_bumper")):
        i = L.inst(S, stem, stem)
        m = A.load_part(stem)
        m.apply_transform(S.T0[stem] @ i["T"])
        new[stem] = m
        c = A.load_part(car)
        c.apply_transform(np.array(DP["placements"][car][0]["T_link_mm"]))
        new[car] = c
        T = N.pin_frame(which)
        r_ = N.BLOCK[which]["r"]
        for side, y in (("L", N.PIN_Y), ("R", -N.PIN_Y)):
            t = -r_ - N.PROUD[which]
            mouth = t + P["exposed"]
            new["plunger_%s_%s" % (which, side)] = N.cyl_u(T, y, t, mouth + 2.0, P["tip_d"], 16)       # the tip head's width over the travel
            new["socket_%s_%s" % (which, side)] = N.cyl_u(T, y, mouth, mouth + P["socket_len"] + P["tail_len"], P["socket_d"], 16)
    rows = []
    worst_vol = 0.0
    # 1 new solids against each other where they must clear, and against the body
    pairs = [("pin_carrier_seat", "sit_seat", "fit %.1f mm" % N.CARRIER["fit"]), ("pin_carrier_bumper", "sit_bumper", "fit %.1f mm" % N.CARRIER["fit"])]
    for a, b, note in pairs:
        v = (N.man(new[a]) ^ N.man(new[b])).volume()
        g = N.man(new[a]).min_gap(N.man(new[b]), 5.0)
        rows.append(dict(a=a, b=b, overlap_mm3=N.r(v, 2), min_gap_mm=N.r(g), note=note))
        worst_vol = max(worst_vol, v)
    for a in new:
        v = (N.man(new[a]) ^ N.man(body_new)).volume()
        g = N.man(new[a]).min_gap(N.man(body_new), 6.0)
        rows.append(dict(a=a, b="body_middle_bottom (changed)", overlap_mm3=N.r(v, 2), min_gap_mm=N.r(g)))
        worst_vol = max(worst_vol, v)
        if a.startswith(("plunger", "socket")):
            blk = "sit_seat" if "seat" in a else "sit_bumper"
            car = "pin_carrier_seat" if "seat" in a else "pin_carrier_bumper"
            v2 = (N.man(new[a]) ^ N.man(new[blk])).volume()
            rows.append(dict(a=a, b=blk + " (changed)", overlap_mm3=N.r(v2, 2), min_gap_mm=N.r(N.man(new[a]).min_gap(N.man(new[blk]), 6.0))))
            worst_vol = max(worst_vol, v2)
            if a.startswith("socket"):
                v3 = (N.man(new[a]) ^ N.man(new[car])).volume()
                rows.append(dict(a=a, b=car, overlap_mm3=N.r(v3, 2), note="the socket (%.2f est) in the %.2f bore: the press ring makes the fit" % (P["socket_d"], P["mount_hole"])))
                worst_vol = max(worst_vol, v3)
    # 2 against every other trunk part
    near = []
    worst = (99.0, "", "")
    for a, m in new.items():
        Ma = N.man(m)
        for i, t in trunk:
            if (m.bounds[0] > t.bounds[1] + 8).any() or (m.bounds[1] < t.bounds[0] - 8).any():
                continue
            try:
                Mt = N.man(t)
                v = (Ma ^ Mt).volume()
                g = Ma.min_gap(Mt, 8.0)
            except Exception:
                v = 0.0
                g, _, ins = min_gap_points(t, m.vertices)
                v = 1.0 if ins else 0.0
            if a in ("sit_seat", "sit_bumper") and i["key"] in ("body_back",):
                note = "as before the change (the D59 block is 1 mm off body_back)"
            else:
                note = ""
            near.append(dict(a=a, b="%s#%d" % (i["key"], i["idx"]), overlap_mm3=N.r(v, 2), min_gap_mm=N.r(g), note=note))
            worst_vol = max(worst_vol, v)
            if g < worst[0] and not a.startswith("sit_"):
                worst = (g, a, i["key"])
    # 3 placed boards and boxes
    boxes = []
    for p in json.load(open(os.path.join(N.LAB, "audit", "placements.json"))):
        d = np.array(p.get("box_with_margin_mm") or p["dims_xyz_mm"], float)
        c = np.array(p["center_mm"], float)
        boxes.append((p["id"], L.box(c - d / 2, c + d / 2)))
    box_rows = []
    for a, m in new.items():
        for bid, bm in boxes:
            if (m.bounds[0] > bm.bounds[1] + 10).any() or (m.bounds[1] < bm.bounds[0] - 10).any():
                continue
            v = (N.man(m) ^ N.man(bm)).volume()
            box_rows.append(dict(a=a, b=bid, overlap_mm3=N.r(v, 2), min_gap_mm=N.r(N.man(m).min_gap(N.man(bm), 10.0))))
            worst_vol = max(worst_vol, v)
    # 4 the leads: 1 mm samples of each new route against trunk parts (the changed body included) and boxes
    lead_rows = []
    lead_min = 99.0
    allm = trunk + [(dict(key="body_middle_bottom(changed)", idx=-1), body_new)] + [(dict(key=k, idx=-2), v) for k, v in new.items() if k.startswith("pin_carrier")]
    for nm, v in A.routes(DP).items():
        if nm == "NM3":
            lead_rows.append(dict(lead=nm, length_mm=v["length_mm"], note="not re-checked: it is the repo's DC2 leg (dock_routes.json: min clearance of the centre line 2.0 mm, self_check PASS)"))
            continue
        pts = sample_tube(v["points"])
        # the first 9 mm (seat) or 6 mm (bumper) lies in the feedthrough itself
        skip = 9.0 if nm.startswith("NP") else 6.5
        dist_from_start = np.linalg.norm(pts - pts[0], axis=1)
        free = pts[dist_from_start > skip] if nm != "NP3" else pts[np.linalg.norm(pts - pts[-1], axis=1) > 4.0]   # NP3 ends ON DK6
        best = (99.0, "")
        for i, t in allm:
            if (free.min(0) > t.bounds[1] + 6).any() or (free.max(0) < t.bounds[0] - 6).any():
                continue
            g, p_, ins = min_gap_points(t, free)
            g = -g if ins else g
            if g < best[0]:
                best = (g, i["key"], p_)
        for bid, bm in boxes:
            if (free.min(0) > bm.bounds[1] + 6).any() or (free.max(0) < bm.bounds[0] - 6).any():
                continue
            g, p_, ins = min_gap_points(bm, free)
            g = -g if ins else g
            if g < best[0]:
                best = (g, bid, p_)
        clear = best[0] - v["d"] / 2
        lead_min = min(lead_min, clear)
        lead_rows.append(dict(lead=nm, gauge=v["gauge"], length_mm=v["length_mm"], nearest=best[1], surface_clearance_mm=N.r(clear),
                              at_trunk_mm=np.round(best[2], 1).tolist()))
    # 5 fasteners of the trunk near the feedthroughs and carriers
    F = json.load(open(os.path.join(N.LAB, "fasteners", "fasteners.json")))["fasteners"]
    fast = []
    probe = np.vstack([new["pin_carrier_seat"].vertices, new["pin_carrier_bumper"].vertices] +
                      [new[k].vertices for k in new if k.startswith(("socket", "plunger"))])
    fmin = (99.0, "")
    for f in F:
        if "seat_world" not in f or f.get("link") not in (N.TR, None):
            continue
        a = np.array(f["seat_world"], float)
        b = a + np.array(f["axis_world"], float) * float(f.get("draw_length_mm") or f.get("length_mm") or 6.0)
        d = seg_dist(probe, a, b).min() - float(f.get("d", 3.0)) / 2
        if d < fmin[0]:
            fmin = (d, f["id"])
        if d < 10:
            fast.append(dict(id=f["id"], spec=f.get("spec"), clearance_mm=N.r(d)))
    ok = worst_vol < 0.05 and lead_min > 0.5 and fmin[0] > 1.0
    RES["A_interference"] = dict(label="CAD check only", frame="trunk frame, zero pose", pairs_new_parts=rows, against_trunk_parts=near, against_placed_boxes=box_rows,
                                 leads=lead_rows, lead_min_surface_clearance_mm=N.r(lead_min), nearest_trunk_fastener=dict(id=fmin[1], clearance_mm=N.r(fmin[0])),
                                 fasteners_within_10mm=fast, worst_overlap_mm3=N.r(worst_vol, 3),
                                 closest_new_part_to_an_unchanged_trunk_part=dict(gap_mm=N.r(worst[0]), part=worst[1], trunk_part=worst[2]),
                                 trunk_parts_checked=len(trunk), boxes_checked=len(boxes), **{"pass": bool(ok)})
    verdict("A interference", ok, "worst overlap %.3f mm3 over %d trunk parts and %d placed boxes; closest unchanged trunk part %.2f mm (%s to %s); "
            "leads clear by %.2f mm or more; nearest trunk fastener %s at %.1f mm" % (worst_vol, len(trunk), len(boxes), worst[0], worst[1], worst[2], lead_min, fmin[1], fmin[0]))
    return new


def check_B(S, DP):
    """the free pins against the legs and feet"""
    segs = {k: (np.array(v["block_face_trunk_mm"]), np.array(v["tip_free_trunk_mm"])) for k, v in DP["pins"].items()}
    legs = [i for i in S.inst if i["link"] not in (N.TR, "sit_seat", "sit_bumper", "neck_stop", "neck_pads") and "head" not in i["link"] and "neck" not in i["link"]
            and "antenna" not in i["link"]]
    V = {}
    for i in legs:
        V[i["idx"]] = (i, S.world_mesh(i).vertices)
    P = A.sit_pose()
    poses = [("sit (sit_pose.json)", {k: np.radians(v) for k, v in P["joints_deg"].items()})]
    pth = L.PATH_A1B
    for (h0, k0, a0, *_), (h1, k1, a1, *_) in zip(pth[:-1], pth[1:]):
        for s in np.linspace(0, 1, 6, endpoint=False):
            poses.append(("sit path", L.cfg_left(h=h0 + s * (h1 - h0), k=k0 + s * (k1 - k0), a=a0 + s * (a1 - a0))))
    poses.append(("stand (-15, 5, 0)", L.cfg_left(h=-15, k=5, a=0)))
    lim = S.joints
    for jn in ("left_hip_yaw", "left_hip_roll"):
        lo, hi = np.degrees(lim[jn]["lo"]), np.degrees(lim[jn]["hi"])
        for v in np.linspace(lo, hi, 9):
            kw = dict(h=-15, k=5, a=0)
            kw["yaw" if "yaw" in jn else "roll"] = v
            poses.append(("stand, %s %.0f deg (both legs mirrored)" % (jn[5:], v), L.cfg_left(**kw)))
    for hp in np.linspace(np.degrees(lim["left_hip_pitch"]["lo"]), np.degrees(lim["left_hip_pitch"]["hi"]), 9):
        for kn in (0.0, 75.0, 150.0):
            poses.append(("hip pitch %.0f, knee %.0f" % (hp, kn), L.cfg_left(h=hp, k=kn, a=0)))
    best = (1e9, "", "", "")
    per = {}
    for nm, cfg in poses:
        Tl = S.link_T(cfg)
        Tt = np.linalg.inv(Tl[N.TR])
        pm = 1e9
        for idx, (i, v0) in V.items():
            T = Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]])
            v = v0 @ T[:3, :3].T + T[:3, 3]
            if v[:, 2].min() > -40 and nm.startswith("stand"):
                pass
            for pk, (a, b) in segs.items():
                d = seg_dist(v, a, b).min() - N.PIN["tip_d"] / 2
                pm = min(pm, d)
                if d < best[0]:
                    best = (d, nm, pk, i["key"])
        key = nm.split(",")[0] if nm.startswith("stand,") else nm.split(" ")[0] if nm.startswith("hip") else nm
        per[key] = min(per.get(key, 1e9), pm)
    ok = best[0] > 3.0
    RES["B_moving_parts"] = dict(label="CAD check only", method="vertex to pin-axis distance less the tip head radius; plungers free (fully out); %d poses" % len(poses),
                                 min_clearance_mm=N.r(best[0]), at=dict(pose=best[1], pin=best[2], part=best[3]),
                                 by_group_mm={k: N.r(v) for k, v in per.items()}, **{"pass": bool(ok)})
    verdict("B legs and feet", ok, "closest leg or foot part to a free pin: %.1f mm (%s, %s, %s) over %d poses" % (best[0], best[1], best[2], best[3], len(poses)))


def check_C():
    P = N.PIN
    rows = []
    for g in (2.5, 2.9, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0):
        c = N.PROUD["bump"] - g
        rows.append(dict(bumper_gap_mm=g, compression_mm=N.r(c), force_per_pin_n=N.r(N.pin_force(c)), of_rated_stroke_pct=N.r(100 * c / P["rated_stroke"], 0)))
    tol = 0.5 + (N.FOIL_T + N.CLOTH_T)                       # print and tape tolerance (est) plus the sun stack that lifts the seat end
    worst_far = N.PROUD["bump"] - (N.GAP_RANGE[1] + tol)
    worst_near = N.PROUD["bump"] - (N.GAP_RANGE[0] - tol)
    seat = [dict(seat_gap_mm=g, compression_mm=N.r(N.PROUD["seat"] - g), force_per_pin_n=N.r(N.pin_force(N.PROUD["seat"] - g))) for g in (0.0, 0.3, N.SEAT_LIFT_MAX)]
    f_nom = 2 * N.pin_force(N.PROUD["seat"]) + 2 * N.pin_force(N.PROUD["bump"] - 2.9)
    f_max = 2 * N.pin_force(N.PROUD["seat"]) + 2 * N.pin_force(N.PROUD["bump"] - N.GAP_RANGE[0])
    sim_pins_on = 2 * 1.38 + 2 * 0.93                         # NEST_SIM.md 2.7: the assumed pins, 8 of 8 joints on their stops
    flush = dict(seat=dict(compression_mm=N.PROUD["seat"], spare_before_bottom_mm=N.r(P["full_stroke"] - N.PROUD["seat"]), force_n=N.r(N.pin_force(N.PROUD["seat"]))),
                 bump=dict(compression_mm=N.PROUD["bump"], spare_before_bottom_mm=N.r(P["full_stroke"] - N.PROUD["bump"]), force_n=N.r(N.pin_force(N.PROUD["bump"]))))
    # how far a solid TPU column squashes before the plunger bottoms (calc only): area of a 12 mm column less the well
    col_area = np.pi * (6.0 ** 2 - (N.TPU_BORE / 2) ** 2)
    k_col = L.E_TPU * col_area / (N.CARRIER["u_bot"] + N.BLOCK["bump"]["r"])        # N per mm, one column, bumper
    f_bottom = 2 * k_col * (P["full_stroke"] - N.PROUD["bump"])
    ok = worst_far >= 0.5 and worst_near <= P["rated_stroke"] and N.PROUD["bump"] < P["full_stroke"] - 2.0 and f_max <= 2 * sim_pins_on
    RES["C_pin_reach"] = dict(
        label="calc only on index pin data (force 0.42 N preload to 1.58 N at 8.05 mm, full stroke 10.16 mm) and sim pass only gaps (NEST_SIM.md 2.7)",
        proud_mm=N.PROUD, bumper=rows, seat=seat,
        margin=dict(tolerance_assumed_mm=N.r(tol), compression_left_at_6mm_gap_mm=N.r(N.PROUD["bump"] - N.GAP_RANGE[1]),
                    compression_left_at_6mm_gap_with_tolerance_mm=N.r(worst_far), force_there_n=N.r(N.pin_force(worst_far)),
                    compression_at_2p5mm_gap_with_tolerance_mm=N.r(worst_near), rated_stroke_mm=P["rated_stroke"],
                    largest_gap_still_touching_mm=N.PROUD["bump"], largest_gap_with_0p5mm_compression_mm=N.PROUD["bump"] - 0.5),
        flush_stop=flush, flush_note="when a block is pressed flat on the floor (a fall, the get-up roll, the rock onto the bumper) the plunger is level with the TPU: the TPU carries the load",
        tpu_squash_before_a_bumper_plunger_bottoms=dict(spare_mm=N.r(P["full_stroke"] - N.PROUD["bump"]), force_n=N.r(f_bottom, 0),
                                                        note="two solid 12 mm TPU columns round the wells (E 26 MPa est, sitlib.E_TPU), 7.5 mm high; calc only"),
        total_pin_force_n=dict(nominal_gap_2p9=N.r(f_nom), worst_gap_2p5=N.r(f_max), sim_assumed_pins=N.r(sim_pins_on), sim_twice_assumed=N.r(2 * sim_pins_on),
                               note="NEST_SIM.md 2.7: with the assumed pins (4.62 N in all) and with twice that (9.24 N) all 8 loaded joints stay on their stops (sim pass only)"),
        seat_block_lift_expected_mm="0.1 to 0.3 (sim pass only, for 2.76 N on the seat pins; here they push %.2f N, the seat's own load is 0.88 N)" % (2 * N.pin_force(N.PROUD["seat"])),
        **{"pass": bool(ok)})
    verdict("C pin reach", ok, "bumper pin 7.5 mm proud: %.1f mm of compression left at the 6.0 mm gap (%.1f with %.2f mm tolerance, %.2f N), %.1f mm at 2.5 mm; "
            "flush stop leaves %.2f mm of stroke; total pin force %.2f N nominal, %.2f N worst (sim: joints stay on stops at 4.62 and 9.24 N)" % (
                N.PROUD["bump"] - N.GAP_RANGE[1], worst_far, tol, N.pin_force(worst_far), N.PROUD["bump"] - N.GAP_RANGE[0], P["full_stroke"] - N.PROUD["bump"], f_nom, f_max))


def check_C2():
    """the sit with the chosen pins in the sim harness (pins_sit_check.py)"""
    p = os.path.join(HERE, "pins_sit_check.json")
    if not os.path.exists(p):
        RES["C2_sit_with_chosen_pins"] = dict(label="sim pass only", status="NOT RUN: pins_sit_check.json is missing", **{"pass": False})
        return verdict("C2 sit with the chosen pins", False, "pins_sit_check.json is missing (run pins_sit_check.py)")
    J = json.load(open(p))
    S_ = J["summary"]
    pl, hf = S_["chosen pins, mat as a plane"], S_["chosen pins, mat as height field"]
    ok = pl["all_4_pins_touch"] == pl["n"] and hf["all_4_pins_touch"] == hf["n"] and pl["joints_on_stops"][1] == 8 and pl["falls"] == 0 and pl["stood_up"] == pl["n"]
    RES["C2_sit_with_chosen_pins"] = dict(label=J["label"], note=J["note"], pin_model=J["pin_model"], plane=pl, height_field=hf,
                                          reading="on the height field the legs do not always settle onto the hip roll stops, with or without pins "
                                                  "(NEST_SIM.md 2.7 calls it a contact artefact: 6 to 8 joints on stops there too); the pins still reach",
                                          **{"pass": bool(ok)})
    verdict("C2 sit with the chosen pins", ok, "plane: all 4 pins touch in %d of %d sits, bumper pin pressed %.2f to %.2f mm, seat block lift %.2f mm at most, %d of 8 joints on stops at worst, "
            "stood up %d of %d; height field: all 4 touch in %d of %d, bumper gap up to %.2f mm, least bumper pin compression %.2f mm" % (
                pl["all_4_pins_touch"], pl["n"], pl["min_bump_pin_comp_mm"], pl["max_bump_pin_comp_mm"], pl["seat_block_lift_mm"][2], int(pl["joints_on_stops"][1]),
                pl["stood_up"], pl["n"], hf["all_4_pins_touch"], hf["n"], hf["bumper_gap_mm"][2], hf["min_bump_pin_comp_mm"]))


def check_D(S, DP):
    cfg = L.cfg_left(h=-15, k=5, a=0)
    Tl = S.link_T(cfg)
    Tt = np.linalg.inv(Tl[N.TR])
    planes = []
    for i in S.inst:
        if i["key"] == "foot_bottom_tpu":
            T = Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]])
            m = S.world_mesh(i).copy()
            m.apply_transform(T)
            # the sole's floor face: the largest flat facet that looks down
            k = max((j for j in range(len(m.facets)) if m.facets_normal[j][2] < -0.9), key=lambda j: m.facets_area[j])
            planes.append((m.facets_origin[k], -m.facets_normal[k], float(m.facets_area[k])))
    # the floor under the standing duck: the plane of the two soles' floor faces (trunk frame)
    n = np.mean([p[1] for p in planes], axis=0)
    n /= np.linalg.norm(n)
    c = np.mean([p[0] for p in planes], axis=0)
    sole_mismatch = abs(float((planes[0][0] - planes[1][0]) @ n))
    h = lambda p: float((np.asarray(p) - c) @ n)  # noqa: E731
    stand = {k: dict(tip_mm=N.r(h(v["tip_free_trunk_mm"]), 1), block_face_mm=N.r(h(v["block_face_trunk_mm"]), 1)) for k, v in DP["pins"].items()}
    trunk_z = h((0, 0, 0))
    W = json.load(open(os.path.join(HERE, "walk_clearance.json")))
    walk_low = W["lowest_tip_any_segment_mm"]
    stand_low = min(v["tip_mm"] for v in stand.values())
    ok = stand_low > 50 and walk_low > 50
    RES["D_ground_clearance"] = dict(
        standing=dict(label="CAD check only: robot.urdf at the stand pose of sit_sim.STAND (hip -15, knee 5, ankle 0 deg), floor = the plane of the two soles' floor faces",
                      soles_coplanar_within_mm=N.r(sole_mismatch, 3),
                      trunk_origin_height_mm=N.r(trunk_z, 1), floor_tilt_in_trunk_frame_deg=N.r(np.degrees(np.arccos(n[2])), 2), pins=stand,
                      study_values="seat block 117.1 mm, bumper 136.4 mm, trunk 201.2 mm (sit_contacts.json, sim pass only)"),
        walking=dict(label=W["label"], lowest_tip_mm=walk_low, segments={k: dict(tip_min_mm=v["tip_min_mm"], trunk_z_mm=v["trunk_z_mm"]) for k, v in W["segments"].items()},
                     falls=W["falls"], note="the stock walk carries the trunk at 155 to 170 mm, lower than the 201 mm stand pose"),
        **{"pass": bool(ok)})
    verdict("D ground clearance", ok, "standing (stand pose): lowest pin tip %.1f mm above the floor (seat tips %.1f, bumper tips %.1f); walking and turning (sim): lowest tip %.1f mm" % (
        stand_low, stand["seat_L"]["tip_mm"], stand["bump_L"]["tip_mm"], walk_low))


def check_E(DP):
    P = N.PIN
    parts = DP["parts"]
    car = {k: parts[k]["volume_mm3"] * N.PLA_RHO for k in ("pin_carrier_seat", "pin_carrier_bumper")}
    eff = dict(sit_seat=22.61 / 88291.6, sit_bumper=12.18 / 40885.2)        # g/mm3 as sliced at 10 % infill (PRINT_CHECK.md rows, BOM 28)
    tpu = {k: -(parts[k]["volume_before_mm3"] - parts[k]["volume_mm3"]) * eff[k] for k in eff}
    solid = {}
    for k, which in (("sit_seat", "seat"), ("sit_bumper", "bump")):
        hgt = N.CARRIER["u_bot"] + N.BLOCK[which]["r"]
        solid[k] = 2 * np.pi * (6.0 ** 2 - (N.TPU_BORE / 2) ** 2) * hgt * (N.TPU_RHO - eff[k])
    R = A.routes(DP)
    g_m = {"22 AWG silicone": 4.3, "20 AWG": 6.5}          # g per m, est
    leads = {k: v["length_mm"] / 1000 * g_m[v["gauge"]] for k, v in R.items() if k != "NM3"}
    pins = 4 * (P["probe_g"] + P["socket_g"])
    vhb = 2 * N.CARRIER["flange_x"] * N.CARRIER["flange_y"] * N.VHB_T * 0.8e-3
    body = -(parts["body_middle_bottom"]["volume_before_mm3"] - parts["body_middle_bottom"]["volume_mm3"]) * N.PLA_RHO
    misc = 0.6                                               # two splices with heat shrink, est
    total = sum(car.values()) + sum(tpu.values()) + sum(solid.values()) + sum(leads.values()) + pins + vhb + body + misc
    RES["E_mass"] = dict(label="calc only (CAD volumes x density; pin, lead and splice masses est)",
                         carriers_g={k: N.r(v) for k, v in car.items()}, tpu_removed_g={k: N.r(v) for k, v in tpu.items()},
                         tpu_solid_columns_g={k: N.r(v) for k, v in solid.items()}, pins_and_sockets_g=N.r(pins), new_leads_g={k: N.r(v) for k, v in leads.items()},
                         vhb_g=N.r(vhb), body_holes_g=N.r(body), splices_g=misc, total_added_g=N.r(total, 1),
                         not_counted="the duck-side charger board and its leads (not designed, BLOCKER); NM3 is the existing DC2 leg",
                         comes_off_with_the_wall_dock="chest contact pad 9.5 g and its short leads (DOCK_INTERFACE.md: about 13 g with the leads), DK2",
                         where="all in the trunk, low: seat pair 111 mm behind and 55 mm below the trunk origin, bumper pair 19 mm in front and 60 mm below")
    verdict("E mass", True, "added to the duck: %.1f g (carriers %.1f, pins and sockets %.1f est, new leads %.1f, TPU %.1f, other %.1f); the charger board is not counted" % (
        total, sum(car.values()), pins, sum(leads.values()), sum(tpu.values()) + sum(solid.values()), vhb + body + misc))


def overhang(m, up, bed_tol=0.3):
    """area of faces that look down steeper than 45 deg from the vertical and are not on the bed (mm2), and the height"""
    up = np.asarray(up, float) / np.linalg.norm(up)
    hgt = m.vertices @ up
    z0 = hgt.min()
    fz = m.triangles_center @ up
    down = (m.face_normals @ up) < -np.cos(np.radians(45.0)) - 1e-6
    off = fz > z0 + bed_tol
    bed = float(m.area_faces[(m.face_normals @ up < -0.999) & ~off].sum())
    return float(m.area_faces[down & off].sum()), float(hgt.max() - z0), bed


def check_F():
    rows = {}
    spec = [("pin_carrier_seat", (0, 0, 1), "flange face on the bed (part frame z up); the columns lean 14 deg; sockets bores near vertical, reamed after printing; 100 % infill, PLA"),
            ("pin_carrier_bumper", (0, 0, 1), "flange face on the bed; bores vertical; 100 % infill, PLA"),
            ("sit_seat", (-0.2873, 0, -0.9578), "as today (PRINT_CHECK.md row: turned, the VHB face on the bed); the pocket opens on the bed face; TPU 95A, 10 % infill, solid within 6 mm of each well"),
            ("sit_bumper", (0, 0, -1), "as today (PRINT_CHECK.md row: -z up, the VHB face on the bed); the pocket opens on the bed face; TPU 95A, 10 % infill, solid within 6 mm of each well"),
            ("body_middle_bottom", None, "as today (print/parts.csv); the four 3.4 mm feedthroughs are near vertical in the print and need no support"),
            ("pin_gauge", (0, 0, 1), "flat on the bed, PLA"),
            ("nest_box_tray", (0, 0, 1), "floor on the bed; the 45 deg front chamfer and the 8 mm jack hole need no support; PLA; 180 mm long: fits a 220 mm bed"),
            ("nest_box_lid", (0, 0, 1), "flat on the bed, PLA")]
    ok = True
    for name, up, note in spec:
        m = A.load_part(name)
        row = dict(note=note, bbox_mm=np.round(m.extents, 1).tolist(), fits_220_bed=bool(sorted(m.extents)[1] <= 220 and max(m.extents) <= 220))
        if up is not None:
            a, h, bed = overhang(m, up)
            row.update(up=list(up), height_mm=N.r(h, 1), bed_contact_mm2=N.r(bed, 0), overhang_over_45deg_mm2=N.r(a, 1))
        rows[name] = row
        ok &= row["fits_220_bed"]
    rows["pin_carrier_seat"]["overhang_note"] = "the columns and web lean about 14 deg from the vertical: no support"
    RES["F_print"] = dict(label="CAD check only (bounding boxes, overhang area by face normals); not sliced", parts=rows,
                          not_printed="felt layers, cloth, foil, foam blocks and the felt sleeve are cut or sewn", **{"pass": bool(ok)})
    verdict("F print", ok, "all %d printed parts fit a 220 mm bed; overhang over 45 deg (mm2): %s" % (len(rows), ", ".join(
        "%s %.0f" % (k, v["overhang_over_45deg_mm2"]) for k, v in rows.items() if "overhang_over_45deg_mm2" in v)))


def check_G(DP):
    S = NPARTS.mat_shapes()
    sun, ring = S["sun"], S["ring"]
    sun_in, ring_in = sun.buffer(-N.TIP_M), ring.buffer(-N.TIP_M)
    sun_out, ring_out = sun.buffer(N.TIP_M), ring.buffer(N.TIP_M)
    D = DP["pair_spacing_along_floor_mm"]
    cs = [(r_ * np.cos(a), r_ * np.sin(a)) for r_ in np.linspace(0, N.WINDOW, 10) for a in np.linspace(0, 2 * np.pi, max(1, int(r_ * 0.8)), endpoint=False)]
    from shapely import contains_xy
    hd = np.arange(0, 360, 2.0)
    strict, lenient, short = [], [], []
    C = np.array(cs)
    for th in hd:
        f = np.array([np.cos(np.radians(th)), np.sin(np.radians(th))])
        nrm = np.array([-f[1], f[0]])
        sp = [C + s * N.PIN_Y * nrm for s in (1, -1)]
        bp = [C + D * f + s * N.PIN_Y * nrm for s in (1, -1)]
        s_on = [contains_xy(sun_in, p[:, 0], p[:, 1]) for p in sp]
        b_on = [contains_xy(ring_in, p[:, 0], p[:, 1]) for p in bp]
        s_bad = [contains_xy(ring_out, p[:, 0], p[:, 1]) for p in sp]
        b_bad = [contains_xy(sun_out, p[:, 0], p[:, 1]) for p in bp]
        bad = s_bad[0] | s_bad[1] | b_bad[0] | b_bad[1]
        strict.append(float((s_on[0] & s_on[1] & b_on[0] & b_on[1]).mean()))
        lenient.append(float(((s_on[0] | s_on[1]) & (b_on[0] | b_on[1]) & ~bad).mean()))
        short.append(float(bad.mean()))
    strict, lenient, short = np.array(strict), np.array(lenient), np.array(short)
    # headings are measured from +x (facing the wall); 180 = facing the room
    dev = np.abs((hd % 360) - 180)                              # degrees away from facing the room
    ok_dev = 0.0
    for d_ in np.arange(0, 181, 2.0):
        if (lenient[dev <= d_] >= 0.999).all():
            ok_dev = d_
        else:
            break
    # the largest window in which all four pins land, for every heading within 90 deg of facing the room
    strict_R = 0.0
    for R_ in np.arange(30.0, 46.0, 1.0):
        Cr = np.array([(R_ * np.cos(a), R_ * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 72, endpoint=False)])
        good = True
        for th in hd[dev <= 90]:
            f = np.array([np.cos(np.radians(th)), np.sin(np.radians(th))])
            nrm = np.array([-f[1], f[0]])
            for s_ in (1, -1):
                p, q = Cr + s_ * N.PIN_Y * nrm, Cr + D * f + s_ * N.PIN_Y * nrm
                good &= bool(contains_xy(sun_in, p[:, 0], p[:, 1]).all() and contains_xy(ring_in, q[:, 0], q[:, 1]).all())
        if good:
            strict_R = R_
        else:
            break
    # pin radii in the window
    r_seat_near, r_seat_far = N.WINDOW - N.PIN_Y, N.WINDOW + N.PIN_Y          # along the lateral line, the worst case
    r_b_min, r_b_max = np.hypot(D, N.PIN_Y) - N.WINDOW, np.hypot(D, N.PIN_Y) + N.WINDOW
    asm = json.load(open(os.path.join(HERE, "nest_assembly.json")))
    ext = np.array(asm["duck_extent_nest_mm"])
    items, _ = A.scene(room=False, standins=False)
    duckv = np.vstack([it["mesh"].vertices for it in items if it["group"].startswith("duck")])
    low = duckv[(duckv[:, 2] < N.RIM["height"]) & (np.abs(duckv[:, 1]) < N.RIM["half_len"])]
    rim_gap_sit = float((N.WALL_X - N.RIM["depth"]) - low[:, 0].max())
    rim_margin = N.SIM_RIM_MIN + (N.SIM_RIM_DEPTH - N.RIM["depth"])
    # the box inside the sleeve, the stand-ins inside the box
    tray, lid, cover = A.load_part("nest_box_tray"), A.load_part("nest_box_lid"), A.load_part("nest_rim_cover")
    boxm = N.man(tray) + N.man(lid)
    v_cov = (boxm ^ N.man(cover)).volume()
    # felt over the box: distance from the box to the sleeve's OUTER surface (the loaf), sampled on the box vertices
    outer = NPARTS.loaf(N.WALL_X - N.RIM["depth"], N.WALL_X + 30, -N.RIM["half_len"], N.RIM["half_len"], N.RIM["height"], N.RIM["r_top"])
    om = N.tm(outer)
    bv = np.vstack([tray.vertices, lid.vertices])
    bv = bv[bv[:, 0] < N.WALL_X - 3]
    _, dcov, _ = trimesh.proximity.closest_point(om, bv)
    st_rows = []
    cav_ok = True
    for k, v in NPARTS.STANDINS.items():
        s, c = np.array(v["size"]), np.array(v["c"])
        bm = L.box(c - s / 2, c + s / 2)
        vt, vl = (N.man(bm) ^ N.man(tray)).volume(), (N.man(bm) ^ N.man(lid)).volume()
        allowed = k == "jack"                                   # the jack's bushing passes through its hole in the end wall
        st_rows.append(dict(part=k, overlap_tray_mm3=N.r(vt, 1), overlap_lid_mm3=N.r(vl, 1), note=v["note"]))
        cav_ok &= (vt < 0.5 or allowed) and vl < 0.5
    NP = json.load(open(os.path.join(HERE, "nest_parts.json")))
    # cloth resistance, order of magnitude (calc only): a point contact of radius a spreading in a sheet out to radius b
    rs = 0.07                                                   # ohm per square, the study's Flectron figure (index)
    r_spread = lambda a, b: rs / (2 * np.pi) * np.log(b / a)   # noqa: E731
    ring_path = r_spread(1.0, 75.0) + rs * (np.pi * 158.0 / 2) / 153.0 / 2      # spread, then half way round the ring both ways in parallel
    sun_path = rs * N.CLOTH_T / 1e3 / (np.pi * 1.0 ** 2) * 1e3                   # through the cloth onto the foil: negligible
    ok = (ok_dev >= 90 and r_seat_near <= N.SUN_R - N.TIP_M and r_seat_far <= N.RING_R0 - N.TIP_M and r_b_min >= N.RING_R0 + N.TIP_M and r_b_max <= N.RING_R1 - N.TIP_M
          and v_cov < 0.5 and cav_ok and dcov.min() >= 1.9)
    RES["G_nest"] = dict(
        landing_window=dict(label="calc only on the cut shapes of nest_parts.py (rules of coverage.py: 3 mm tip margin, no pin on the other pole)",
                            rule="the study's: charging = at least one seat pin on the sun, at least one bumper pin on the ring, no pin on the other pole's zone",
                            window_radius_mm=N.WINDOW, pair_spacing_mm=D, nearer_seat_pin_max_radius_mm=N.r(r_seat_near), sun_radius_less_margin_mm=N.SUN_R - N.TIP_M,
                            farther_seat_pin_max_radius_mm=N.r(r_seat_far), ring_inner_less_margin_mm=N.RING_R0 - N.TIP_M,
                            window_radius_for_all_four_pins_mm=float(strict_R),
                            bumper_pin_radius_range_mm=[N.r(r_b_min), N.r(r_b_max)], ring_band_less_margin_mm=[N.RING_R0 + N.TIP_M, N.RING_R1 - N.TIP_M],
                            charging_for_every_point_of_the_window_up_to_deg_from_facing_the_room=float(ok_dev),
                            strict_share_by_heading_deg_from_facing_the_room={str(int(d_)): N.r(float(strict[dev == d_].min()), 3) for d_ in (0, 30, 60, 90, 120, 130, 140, 150, 160, 180)},
                            charging_share_same={str(int(d_)): N.r(float(lenient[dev == d_].min()), 3) for d_ in (0, 90, 120, 130, 140, 150, 160, 180)},
                            wrong_pole_share_same={str(int(d_)): N.r(float(short[dev == d_].max()), 3) for d_ in (0, 90, 140, 160, 180)},
                            note="facing the wall the bumper pins land beyond the ring's cut (56 mm from the wall) and on the feed notch: the duck does not charge there, and nothing is shorted"),
        margins=dict(tail_to_wall_sitting_mm=asm["tail_to_wall_mm"], duck_to_rim_sitting_mm=N.r(rim_gap_sit, 1),
                     foot_to_rim_worst_run_mm=dict(sim_with_72mm_rim=N.SIM_RIM_MIN, this_rim_50mm=N.r(rim_margin, 1), label="sim pass only number plus the CAD change of the rim depth (calc only); not re-run"),
                     head_to_wall_worst_run_mm=dict(value=N.SIM_WALL_MIN, label="sim pass only; unchanged, the sun stays 190 mm from the wall as the brief asks",
                                                    option="every mm the sun centre moves out adds a mm: at 215 mm it would be 48.5 mm (calc only, needs a re-run; WALL_X in nestcad_lib.py)")),
        steps=dict(label="CAD check only", felt_layers_mm=[N.FELT_T, N.FELT_T], tread_mm=N.BASE_R - N.TOP_R, highest_step_mm=N.FELT_T,
                   cloth_step_mm=N.CLOTH_T, sun_step_mm=N.FOIL_T + N.CLOTH_T, thickness_mm=NP["stack_mm"],
                   mat_size_mm=[N.r(N.BASE_R + N.WALL_X - N.MAT_BACK, 0), 2 * N.BASE_R],
                   note="the sim tripped on one 2 mm rise while steering; two 1 mm rises 20 mm apart are not simulated yet (BLOCKER)"),
        gap_and_coin=dict(felt_gap_mm=N.GAP, us_quarter_mm=24.26, feed_notch_mm=24.0, note="the plus feed under the notch is wrapped in polyimide tape and lies under 1 mm of felt"),
        box=dict(label="CAD check only", inner_clear_mm=NP["box"]["inner_clear"], standins=st_rows, overlap_box_with_sleeve_mm3=N.r(v_cov, 2),
                 felt_or_foam_over_the_box_min_mm=N.r(float(dcov.min()), 2), lid_screw_head_top_mm=N.r(NPARTS.BZ1 + 1.65), rim_top_mm=N.RIM["height"],
                 cover_over_screw_heads_mm=N.r(N.RIM["height"] - NPARTS.BZ1 - 1.65)),
        cloth_resistance=dict(label="calc only, order of magnitude; cloth 0.07 ohm per square is the study's index figure, contact resistance not included (BLOCKER 2 of the study)",
                              ring_one_pin_to_tab_ohm=N.r(ring_path, 3), sun_one_pin_to_foil_ohm=N.r(sun_path, 5),
                              drop_at_2A_one_pin_v=N.r(2 * ring_path, 2), heat_at_2A_w=N.r(4 * ring_path, 2)),
        **{"pass": bool(ok)})
    verdict("G nest", ok, "charging (study rule) for every point of the 45 mm window up to %.0f deg either side of facing the room; all four pins inside a %.0f mm window; "
            "bumper pins at radius %.1f to %.1f (ring band %.0f to %.0f); tail to wall %.0f mm; foot to rim worst run %.1f mm (sim 9.5 with the 72 mm rim); highest step %.1f mm; "
            "%.1f mm of sleeve over the box" % (ok_dev, strict_R, r_b_min, r_b_max, N.RING_R0 + N.TIP_M, N.RING_R1 - N.TIP_M, asm["tail_to_wall_mm"], rim_margin, N.FELT_T, dcov.min()))


def check_H(DP):
    lp = np.array(NPARTS.LID_POSTS)
    lid = A.load_part("nest_box_lid")
    top = lid.vertices[lid.vertices[:, 2] > lid.bounds[1][2] - 0.01]
    cx = (top[:, 0].min() + top[:, 0].max()) / 2                 # the centre line of the lid's top face
    sym_y = set(map(tuple, np.round(lp * [1, -1], 3))) == set(map(tuple, np.round(lp, 3)))
    sym_x = set(map(tuple, np.round(np.c_[2 * cx - lp[:, 0], lp[:, 1]], 2))) == set(map(tuple, np.round(lp, 2)))
    fasteners = [
        dict(id="NL1 to NL4", what="lid to tray", spec="M3x6 button head ISO 7380-1 A2 (BOM 17j)", qty=4, into="M3 heat-set insert (BOM 16) in each lid post",
             pattern="the lid's 4 corners, 6 mm in: mirror-symmetric about both centre lines (D42)", engagement_mm=4.0, positions_nest_xy_mm=np.round(lp, 2).tolist()),
        dict(id="NT1, NT2", what="mat terminals: the ring tab (y +25) and the plus feed (y -25), each clamped under an M3 ring lug",
             spec="M3x8 SHCS DIN 912 A2 (BOM 17a)", qty=2, into="M3 heat-set insert (BOM 16) in each terminal post",
             pattern="a mirror pair about the box centre line (D42)", engagement_mm=5.7, positions_nest_xy_mm=[[NPARTS.POST_X, 25.0], [NPARTS.POST_X, -25.0]]),
        dict(id="inserts", what="M3 heat-set inserts", spec="CNC Kitchen M3 x 5.7, hole 4.0 mm (BOM 16)", qty=6, into="4 lid posts, 2 terminal posts"),
        dict(id="duck", what="pin carriers, TPU blocks", spec="no screw: VHB 4950 (BOM 29); each carrier is held captive in its block's pocket", qty=0,
             pattern="none (D42 has nothing to make uniform; D39: a printed seat holds the part)"),
        dict(id="wall", what="rim to the wall or skirting board", spec="VHB 4950 (BOM 29), 2 strips of 170 mm on the tray's back face", qty=0, pattern="none"),
        dict(id="jack", what="DC jack", spec="its own 5/16-32 nut and washer (Same Sky PJ-005A, dock BOM K6b)", qty=1, pattern="single, on the end wall's centre height"),
    ]
    holes = [
        dict(part="body_middle_bottom", hole="4 x 3.4 mm, on the pin axes", purpose="feedthrough: socket solder cup and one 22 AWG lead each (filled)"),
        dict(part="sit_seat, sit_bumper", hole="2 x 3.6 mm wells each, and the carrier pocket", purpose="plunger travel; the pocket holds the pin carrier"),
        dict(part="pin_carrier_seat, pin_carrier_bumper", hole="2 x 1.75 mm bores each (est, reamed to the data sheet)", purpose="probe socket, press fit"),
        dict(part="nest_box_tray", hole="4 x 4.0 mm insert bores in the lid posts", purpose="M3 inserts for NL1 to NL4"),
        dict(part="nest_box_tray", hole="2 x 4.0 mm insert bores in the terminal posts", purpose="M3 inserts for NT1, NT2"),
        dict(part="nest_box_tray", hole="2 floor slots 16 x 2.5 mm", purpose="the ring tab and the plus feed come up from the mat"),
        dict(part="nest_box_tray", hole="1 x 8.0 mm in the left end wall", purpose="DC jack bushing"),
        dict(part="nest_box_lid", hole="4 x 3.4 mm", purpose="NL1 to NL4"),
        dict(part="nest_felt_top", hole="sun slit 14 x 1.5 mm, box slit 16 x 2.5 mm", purpose="the plus feed dives under the sun and comes up in the box"),
        dict(part="pin_gauge", hole="2 slots 20 x 4 mm", purpose="the plunger tips of a pair sit in the slot while the socket is pressed to height"),
        dict(part="nest_bolster_left", hole="cord channel and plug pocket", purpose="adapter cord and plug"),
        dict(part="body_front (repo, not changed here)", hole="the 6 mm chest lead hole of D50", purpose="EMPTY once the chest pad goes: it must be closed in the repo (D39), see the landing plan"),
    ]
    ok = sym_y and sym_x
    RES["H_fasteners_holes"] = dict(label="CAD check only", fasteners=fasteners, holes=holes, screw_sizes_new_to_the_project=[],
                                    lid_pattern_mirror_y=bool(sym_y), lid_pattern_mirror_x=bool(sym_x), **{"pass": bool(ok)})
    verdict("H fasteners and holes", ok, "6 screws in 2 sizes, both already in the BOM (17a, 17j), 6 inserts (BOM 16); lid pattern mirror-symmetric about both centre lines; "
            "no screw on the duck; every hole has a named job; 1 repo hole becomes empty (body_front chest hole)")


def main():
    S = L.scene(fresh=True)
    DP = A.duck_pins_json()
    check_A(S, DP)
    check_B(S, DP)
    check_C()
    check_C2()
    check_D(S, DP)
    check_E(DP)
    check_F()
    check_G(DP)
    check_H(DP)
    RES["summary"] = dict(failed=FAIL, all_pass=not FAIL)
    N.dump(RES, os.path.join(HERE, "nest_checks.json"))
    print("FAILED: %s" % FAIL if FAIL else "all checks pass")


if __name__ == "__main__":
    main()
