"""Thermal geometry of the Open Duck Mini v2 from the CAD meshes (no sim, no guesses).

Measures, on the upstream assembly at the zero pose (audit/assembly.json: every URDF visual mesh with its
transform; the meshes in mini_bdx/robots/open_duck_mini_v2/ are the same files as print/*.stl, areas checked):
  1. Each of the 14 STS3215 servos: the outer case area that faces the air (rays along the face normal that do
     not hit the servo's own case), and how far the nearest other part is along each normal (free air, within
     2, 10, 30 mm). These set the convection area of the servo body node.
  2. Which printed parts touch each servo case (closest distance under 0.3 mm and under 1.0 mm), with the
     touching area: the PLA parts that see the servo case temperature (task 4).
  3. The trunk and head enclosures: outer skin area (rays that leave the shell group), inner skin area, the wall
     thickness along the normal, and the shell plastic volume. These set the enclosure air rise (task 3).
  4. Which shell walls the hot electronics sit on (audit/placements.json seats), with the distance.

Run from the repo root:  python3 altaay_lab/twin/thermal/geometry.py
Writes altaay_lab/twin/thermal/geometry.json (small) and prints a summary.
"""
import json, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
MESH_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
CASE = ("wj-wk00-0122topcabinetcase_95.stl", "wj-wk00-0123middlecase_56.stl", "wj-wk00-0124bottomcase_45.stl")
HORNS = ("drive_palonier.stl", "passive_palonier.stl")
NOT_PRINTED = set(CASE) | set(HORNS) | {"bms.stl", "bno055.stl", "board.stl", "cell.stl", "holder.stl", "power_switch.stl",
                                        "roll_bearing.stl", "usb_c_charger.stl", "raspberrypizerow.stl", "sg90.stl", "antenna.stl"}
TRUNK_SHELL = ("body_front.stl", "body_back.stl", "body_middle_bottom.stl", "body_middle_top.stl", "trunk_bottom.stl",
               "trunk_top.stl", "battery_pack_lid.stl")
HEAD_SHELL = ("head.stl", "head_bot_sheet.stl")
# servo body -> joint: the body sits in the joint's parent link, except the head yaw and head roll servos,
# whose bodies ride on the child link (robot.urdf joint list; checked by listing each link's meshes)
SERVO_OF_LINK = {"hip_roll_assembly": ["left_hip_roll"], "hip_roll_assembly_2": ["right_hip_roll"],
                 "left_roll_to_pitch_assembly": ["left_hip_pitch"], "right_roll_to_pitch_assembly": ["right_hip_pitch"],
                 "knee_and_ankle_assembly": ["left_knee"], "knee_and_ankle_assembly_2": ["left_ankle"],
                 "knee_and_ankle_assembly_3": ["right_knee"], "knee_and_ankle_assembly_4": ["right_ankle"],
                 "neck_pitch_assembly": ["head_pitch"], "neck_yaw_assembly": ["head_yaw"], "head_assembly": ["head_roll"]}
SAMPLE_MM2 = 1.0      # one surface sample per 1 mm2


def load_assembly():
    d = json.load(open(os.path.join(LAB, "audit", "assembly.json")))
    cache, inst = {}, []
    for k, i in enumerate(d["inst"]):
        fn = i["mesh"]
        if fn not in cache:
            m = trimesh.load(os.path.join(MESH_DIR, fn), force="mesh")
            m.apply_scale(1000.0)
            cache[fn] = m
        m = cache[fn].copy()
        m.apply_transform(np.array(i["T"]))
        inst.append(dict(k=k, link=i["link"], mesh=fn, m=m, origin=np.array(i["T"])[:3, 3]))
    return inst


def samples(mesh, per_mm2=SAMPLE_MM2, seed=0):
    n = max(200, int(mesh.area / per_mm2))
    pts, fid = trimesh.sample.sample_surface(mesh, n, seed=seed)
    return pts, mesh.face_normals[fid], np.full(len(pts), mesh.area / n)


def first_hit(meshes, origins, dirs):
    """distance along each ray to the first hit on any mesh in the list (inf if none)"""
    best = np.full(len(origins), np.inf)
    for m in meshes:
        loc, ri, _ = m.ray.intersects_location(origins, dirs, multiple_hits=False)
        if len(ri):
            dist = np.linalg.norm(loc - origins[ri], axis=1)
            best[ri] = np.minimum(best[ri], dist)
    return best


def closest(mesh, pts, margin=10.0, per_mm2=0.1):
    """distance from points to a mesh surface: nearest neighbour among dense surface samples (one per 0.1 mm2,
    so the error is under about 0.2 mm) of the faces within `margin` of the points' bounding box"""
    from scipy.spatial import cKDTree
    lo, hi = pts.min(0) - margin, pts.max(0) + margin
    keep = np.all((mesh.triangles_center > lo) & (mesh.triangles_center < hi), axis=1)
    if not keep.any():
        return np.full(len(pts), np.inf)
    sub = mesh.submesh([np.where(keep)[0]], append=True)
    sp, _ = trimesh.sample.sample_surface(sub, max(2000, int(sub.area / per_mm2)), seed=2)
    d, _ = cKDTree(sp).query(pts)
    return d


def servo_groups(inst):
    """the 14 servos: 3 case meshes and 2 horns sharing one origin in one link"""
    groups = {}
    for i in inst:
        if i["mesh"] in CASE + HORNS:
            key = (i["link"], tuple(np.round(i["origin"][[0, 2]] if i["mesh"] == "passive_palonier.stl" else i["origin"][[0, 2]], 0)))
            groups.setdefault(i["link"], []).append(i)
    out = []
    for link, items in groups.items():
        cases = [i for i in items if i["mesh"] in CASE]
        # cluster cases by origin (the trunk link holds three servos)
        cl = {}
        for c in cases:
            cl.setdefault(tuple(np.round(c["origin"], 0)), []).append(c)
        for org, cs in cl.items():
            horns = [h for h in items if h["mesh"] in HORNS and np.linalg.norm(h["origin"][[0, 2]] - np.array(org)[[0, 2]]) < 4.0
                     and abs(h["origin"][1] - org[1]) < 4.0]
            if link == "trunk_assembly":
                name = "neck_pitch" if abs(org[0] - 1.0) < 3 else ("left_hip_yaw" if org[1] > 0 else "right_hip_yaw")
            else:
                name = SERVO_OF_LINK[link][0]
            out.append(dict(name=name, link=link, origin=np.array(org), cases=cs, horns=horns))
    return sorted(out, key=lambda s: s["name"])


def servo_exposure(inst, servo):
    case_m = [c["m"] for c in servo["cases"]]
    case_ids = {c["k"] for c in servo["cases"]}
    pts, nrm, area = [], [], []
    for m in case_m:
        p, n, a = samples(m)
        pts.append(p); nrm.append(n); area.append(a)
    pts, nrm, area = np.vstack(pts), np.vstack(nrm), np.concatenate(area)
    o = pts + nrm * 1e-3
    own = first_hit(case_m, o, nrm)
    ext = ~np.isfinite(own) | (own > 60.0)          # leaves the case: outer surface
    pe, ne, ae = pts[ext], nrm[ext], area[ext]
    lo, hi = pts.min(0) - 40.0, pts.max(0) + 40.0
    others = [i for i in inst if i["k"] not in case_ids and np.all(i["m"].bounds[1] > lo) and np.all(i["m"].bounds[0] < hi)]
    free = first_hit([i["m"] for i in others], pe + ne * 1e-3, ne)
    res = dict(outer_case_area_mm2=float(ae.sum()), all_case_mesh_area_mm2=float(area.sum()),
               free_beyond_30mm=float(ae[free > 30].sum() / ae.sum()), within_10_30mm=float(ae[(free > 10) & (free <= 30)].sum() / ae.sum()),
               within_2_10mm=float(ae[(free > 2) & (free <= 10)].sum() / ae.sum()), within_2mm=float(ae[free <= 2].sum() / ae.sum()))
    # contacts with printed parts: closest distance from the outer case samples
    contacts = []
    for i in others:
        if i["mesh"] in NOT_PRINTED:
            continue
        dist = closest(i["m"], pe)
        a03 = float(ae[dist < 0.3].sum()); a10 = float(ae[dist < 1.0].sum())
        if a10 > 1.0:
            contacts.append(dict(part=i["mesh"].replace(".stl", ""), link=i["link"], area_under_0p3mm_mm2=round(a03, 1),
                                 area_under_1mm_mm2=round(a10, 1), min_gap_mm=round(float(dist.min()), 2)))
    # horn contact with printed parts (the horns carry gear heat out of the output shaft)
    horn = []
    for h in servo["horns"]:
        hp, hn, ha = samples(h["m"])
        for i in others:
            if i["mesh"] in NOT_PRINTED:
                continue
            dist = closest(i["m"], hp)
            a = float(ha[dist < 0.3].sum())
            if a > 1.0:
                horn.append(dict(horn=h["mesh"].replace(".stl", ""), part=i["mesh"].replace(".stl", ""), link=i["link"], area_under_0p3mm_mm2=round(a, 1)))
    res["contacts"] = sorted(contacts, key=lambda c: -c["area_under_1mm_mm2"])
    res["horn_contacts"] = horn
    return res


def enclosure(inst, names, link):
    shell = [i for i in inst if i["link"] == link and i["mesh"] in names]
    shell_m = [i["m"] for i in shell]
    out = dict(parts={}, outer_area_mm2=0.0, inner_area_mm2=0.0)
    thick_all, w_all = [], []
    for i in shell:
        p, n, a = samples(i["m"], per_mm2=2.0)
        hit = first_hit(shell_m, p + n * 1e-3, n)
        ext = ~np.isfinite(hit)
        # wall thickness on the outer skin: inward ray to the same part's other side
        t = first_hit([i["m"]], p[ext] - n[ext] * 1e-3, -n[ext])
        t = t[np.isfinite(t) & (t < 30)]
        out["parts"][i["mesh"].replace(".stl", "")] = dict(outer_mm2=round(float(a[ext].sum())), inner_mm2=round(float(a[~ext].sum())),
                                                           plastic_cm3=round(float(i["m"].volume) / 1000, 1),
                                                           wall_median_mm=round(float(np.median(t)), 2) if len(t) else None)
        out["outer_area_mm2"] += float(a[ext].sum()); out["inner_area_mm2"] += float(a[~ext].sum())
        thick_all.append(t); w_all.append(np.full(len(t), a[0]))
    t = np.concatenate(thick_all); w = np.concatenate(w_all)
    out["wall_area_weighted_mean_mm"] = round(float((t * w).sum() / w.sum()), 2)
    out["wall_median_mm"] = round(float(np.median(t)), 2)
    out["wall_p10_p90_mm"] = [round(float(np.percentile(t, 10)), 2), round(float(np.percentile(t, 90)), 2)]
    out["plastic_cm3"] = round(sum(float(i["m"].volume) for i in shell) / 1000, 1)
    bmin = np.min([m.bounds[0] for m in shell_m], axis=0); bmax = np.max([m.bounds[1] for m in shell_m], axis=0)
    out["bbox_mm"] = np.round(bmax - bmin, 1).tolist()
    out["bbox_area_mm2"] = round(float(2 * ((bmax - bmin)[0] * (bmax - bmin)[1] + (bmax - bmin)[1] * (bmax - bmin)[2] + (bmax - bmin)[0] * (bmax - bmin)[2])))
    hull = trimesh.util.concatenate(shell_m).convex_hull
    out["convex_hull_area_mm2"] = round(float(hull.area)); out["convex_hull_volume_cm3"] = round(float(hull.volume) / 1000, 1)
    out["outer_area_mm2"] = round(out["outer_area_mm2"]); out["inner_area_mm2"] = round(out["inner_area_mm2"])
    return out


def seats(inst):
    """distance from each seated electronics box (audit/placements.json) to the nearest shell wall; nearest-neighbour
    distance to dense surface samples of each shell part (0.25 mm2 per sample) inside a 10 mm margin of the box"""
    from scipy.spatial import cKDTree
    pl = json.load(open(os.path.join(LAB, "audit", "placements.json")))
    shell = [i for i in inst if i["link"] == "trunk_assembly" and i["mesh"] in TRUNK_SHELL]
    res = {}
    for p in pl:
        c = np.array(p["center_mm"]); dims = np.array(p.get("box_with_margin_mm", p["dims_xyz_mm"]), float)
        box = trimesh.creation.box(extents=dims); box.apply_translation(c)
        bp, _, ba = samples(box, per_mm2=1.0)
        lo, hi = c - dims / 2 - 10.0, c + dims / 2 + 10.0
        best = []
        for i in shell:
            m = i["m"]
            keep = np.all((m.triangles_center > lo) & (m.triangles_center < hi), axis=1)
            if not keep.any():
                continue
            sub = m.submesh([np.where(keep)[0]], append=True)
            sp, _ = trimesh.sample.sample_surface(sub, max(2000, int(sub.area / 0.25)), seed=1)
            dist, _ = cKDTree(sp).query(bp)
            best.append((float(dist.min()), i["mesh"].replace(".stl", ""), float(ba[dist < 1.5].sum())))
        best.sort()
        res[p["id"]] = dict(nearest_wall=best[0][1] if best else None, gap_mm=round(best[0][0], 2) if best else None,
                            walls_within_1p5mm={b[1]: round(b[2]) for b in best if b[2] > 1})
    return res


def main():
    inst = load_assembly()
    sv = servo_groups(inst)
    assert len(sv) == 14, [s["name"] for s in sv]
    res = dict(source="audit/assembly.json (URDF zero pose) + mini_bdx/robots/open_duck_mini_v2 meshes (= print/*.stl)", servos={})
    for s in sv:
        res["servos"][s["name"]] = servo_exposure(inst, s)
        r = res["servos"][s["name"]]
        sys.stdout.flush(); print(f"{s['name']:16s} outer case {r['outer_case_area_mm2']:6.0f} mm2 | free >30 mm {r['free_beyond_30mm']:.2f} | <=2 mm {r['within_2mm']:.2f} | "
              f"PLA touching (<0.3 mm): " + ", ".join(f"{c['part']} {c['area_under_0p3mm_mm2']:.0f}" for c in r["contacts"] if c["area_under_0p3mm_mm2"] > 0))
    json.dump(res, open(os.environ.get("TWIN_GEOM_OUT", os.path.join(HERE, "geometry.json")), "w"), indent=1)
    res["trunk"] = enclosure(inst, TRUNK_SHELL, "trunk_assembly")
    res["head"] = enclosure(inst, HEAD_SHELL, "head_assembly")
    for k in ("trunk", "head"):
        e = res[k]
        print(f"{k}: outer {e['outer_area_mm2']} mm2, inner {e['inner_area_mm2']} mm2, wall median {e['wall_median_mm']} mm, "
              f"bbox {e['bbox_mm']}, hull {e['convex_hull_area_mm2']} mm2 / {e['convex_hull_volume_cm3']} cm3, plastic {e['plastic_cm3']} cm3")
    json.dump(res, open(os.environ.get("TWIN_GEOM_OUT", os.path.join(HERE, "geometry.json")), "w"), indent=1)
    res["seats"] = seats(inst)
    for k, v in res["seats"].items():
        print("seat", k, v)
    json.dump(res, open(os.environ.get("TWIN_GEOM_OUT", os.path.join(HERE, "geometry.json")), "w"), indent=1)


if __name__ == "__main__":
    main()
