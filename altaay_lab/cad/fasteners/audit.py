#!/usr/bin/env python3
"""Measure the fastener CAD that is already in the repo.

Reuses altaay_lab/fasteners/fasteners.json, twin/assembly/BUILD_ORDER.md,
twin/holes/data/sym_checks.json, the nest CAD constants, and the same
visual origin rule as twin/structure/st_fea_run.py visual_T.

Does not design a new screw, a new hole, or a new mount.
Writes schedule.json, findings.json, and two figures next to this file.

Labels on every number are in the JSON: cad, calc, or cited.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True

import numpy as np
import trimesh
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
URDF = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "robot.urdf")
PRINT = os.path.join(REPO, "print")
FAST = os.path.join(LAB, "fasteners", "fasteners.json")
BUILD = os.path.join(LAB, "twin", "assembly", "BUILD_ORDER.md")
SYM = os.path.join(LAB, "twin", "holes", "data", "sym_checks.json")
CABLES = os.path.join(LAB, "cables3d", "cables3d.json")
NEST_LIB = os.path.join(LAB, "twin", "dock", "nest", "cad")

# Cited from the PDF opened for this audit: RLS Installation guide TTD01_03,
# issue 03, 6 December 2023. DIN 912 / ISO 4762, A2/A4/70, Nm.
# ISO 7380, A2/A4/70, Nm. The same page: the depth of the screw in the
# threaded hole is at least 1 x D nominal for steel or 2 x D nominal for aluminum.
TORQUE_912 = {"M2": 0.35, "M2.5": 0.7, "M3": 1.2}
TORQUE_7380 = {"M2": 0.19, "M2.5": 0.37, "M3": 0.6}
TORQUE_SRC = "cited, RLS TTD01_03 issue 03 (6 Dec 2023), DIN 912 / ISO 4762 and ISO 7380, A2/A4/70"

PRINT_NAME = {
    "left_knee_to_ankle_left_sheet": "knee_to_ankle_left_sheet",
    "left_knee_to_ankle_right_sheet": "knee_to_ankle_right_sheet",
}
HEAD_K = {"M2": 2.0, "M2.5": 2.5, "M3": 3.0}  # DIN 912 k max, already in fasteners.json meta
HEAD_R_KNURL = {"M2": 3.98 / 2, "M2.5": 4.68 / 2, "M3": 5.68 / 2}


def mm(T):
    T = np.array(T, float).copy()
    T[:3, 3] *= 1000.0
    return T


def fitted(row):
    st = str(row.get("status") or row.get("len_status") or "")
    return not any(s in st for s in ("NOT FITTED", "LEAVE OUT"))


def load_urdf():
    u = yourdfpy.URDF.load(URDF, load_meshes=False, build_scene_graph=True)
    u.update_cfg({j: 0.0 for j in u.actuated_joint_names})
    return u, {ln: mm(u.get_transform(ln)) for ln in u.link_map}


def visual_T(u, link, part):
    """Same rule as st_fea_run.visual_T: the URDF visual origin, in mm."""
    for v in u.link_map[link].visuals:
        fn = os.path.basename(v.geometry.mesh.filename)[:-4]
        if PRINT_NAME.get(fn, fn) == part:
            T = np.array(v.origin, float).copy()
            T[:3, 3] *= 1000.0
            return T
    raise KeyError((link, part))


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n else v


def pattern_ok(pts, tol):
    """Mirror or half turn about the screw-set centre. Same test idea as sym_checks."""
    pts = np.asarray(pts, float)
    if len(pts) <= 1:
        return True, "one screw", 0.0
    C = pts.mean(0)
    Q = pts - C
    normals = [np.eye(3)[i] for i in range(3)]
    w, V = np.linalg.eigh(Q.T @ Q)
    for i in range(3):
        normals.append(V[:, i])
    best = 1e9
    best_name = "not uniform"

    def score(img):
        d = np.linalg.norm(img[:, None, :] - Q[None, :, :], axis=2).min(1)
        return float(d.max())

    for n in normals:
        n = unit(n)
        img = Q - 2.0 * np.outer(Q @ n, n)
        err = score(img)
        if err < best:
            best, best_name = err, "mirror"
        R = 2.0 * np.outer(n, n) - np.eye(3)
        err = score(Q @ R.T)
        if err < best:
            best, best_name = err, "half turn"
    return best <= tol, best_name if best <= tol else "not uniform", best


def seg_point_dist(a, b, p):
    ab = b - a
    L2 = float(np.dot(ab, ab))
    if L2 < 1e-12:
        return float(np.linalg.norm(p - a)), 0.0
    t = float(np.clip(np.dot(p - a, ab) / L2, 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab))), t


def cylinder_gap(points, a, b, radius):
    """Gap from points to a finite cylinder. Negative is inside. Ends are flat disks."""
    points = np.asarray(points, float)
    ab = np.asarray(b, float) - np.asarray(a, float)
    length = float(np.linalg.norm(ab))
    if length < 1e-9 or len(points) == 0:
        return np.full(len(points), 1e9)
    axis = ab / length
    rel = points - np.asarray(a, float)
    along = rel @ axis
    radial = np.linalg.norm(rel - along[:, None] * axis, axis=1)
    gap = np.empty(len(points))
    mid = (along >= 0.0) & (along <= length)
    gap[mid] = radial[mid] - radius
    for mask, axial in ((along < 0.0, -along), (along > length, along - length)):
        if not np.any(mask):
            continue
        rad = radial[mask]
        ax = axial[mask]
        out = np.hypot(np.maximum(rad - radius, 0.0), ax)
        # Inside the end disk's radius the gap is just the axial distance.
        out = np.where(rad <= radius, ax, out)
        gap[mask] = out
    return gap


def ring_basis(axis):
    a = unit(axis)
    tmp = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = unit(np.cross(tmp, a))
    y = np.cross(a, x)
    return x, y


def head_stack(mesh, seat, axis, radius):
    """How far material at this radius runs on the head side of the old seat.

    axis points into the part. The head sits on the opposite side.
    Returns (first_solid_mm, last_solid_mm) along -axis, or (None, None).
    """
    x, y = ring_basis(axis)
    angs = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    first, last = None, None
    for t in np.arange(0.3, 12.01, 0.4):
        c = seat - axis * t
        pts = np.stack([c + radius * (np.cos(th) * x + np.sin(th) * y) for th in angs])
        solid = int(np.asarray(mesh.contains(pts)).sum())
        if solid >= 6:
            if first is None:
                first = round(float(t), 2)
            last = round(float(t), 2)
        elif first is not None:
            break
    return first, last


def shank_solid(mesh, seat, axis, near):
    far = max(0.8, float(near) - 0.3) if near else 2.0
    ts = np.linspace(0.4, far, 8)
    pts = seat + ts[:, None] * axis
    hit = np.asarray(mesh.contains(pts))
    return int(hit.sum()), int(len(pts))


def main():
    data = json.load(open(FAST))
    rows = data["fasteners"]
    screws = [r for r in rows if r["kind"] == "screw"]
    inserts = [r for r in rows if r["kind"] == "insert"]
    fit = [r for r in screws if fitted(r)]
    left = [r for r in screws if not fitted(r)]

    u, Tlink = load_urdf()
    # Sanity: seat_world must match the link transform of seat_link.
    err = []
    for r in fit:
        Tw = Tlink[r["link"]]
        w = Tw[:3, :3] @ np.array(r["seat_link"], float) + Tw[:3, 3]
        err.append(float(np.linalg.norm(w - np.array(r["seat_world"], float))))
    seat_err = round(max(err), 3) if err else None

    # Wires, zero pose, same URDF transforms the fastener file uses.
    cables = json.load(open(CABLES))
    # Sample each run along the segments, not only at the stored vertices.
    wire_xyz, wire_rad, wire_id = [], [], []
    for c in cables["cables"]:
        for run in c.get("runs") or []:
            rad = float(run.get("d_mm") or c.get("d_mm") or 1.0) / 2.0
            pts = []
            for p in run.get("points") or []:
                Tw = Tlink[p["link"]]
                pts.append(Tw[:3, :3] @ np.array(p["p"], float) + Tw[:3, 3])
            if not pts:
                continue
            sampled = [pts[0]]
            for i in range(1, len(pts)):
                step = pts[i] - pts[i - 1]
                dist = float(np.linalg.norm(step))
                n = int(np.ceil(dist / 0.25)) if dist > 1e-6 else 1
                for k in range(1, n + 1):
                    sampled.append(pts[i - 1] + step * (k / n))
            for w in sampled:
                wire_xyz.append(w)
                wire_rad.append(rad)
                wire_id.append(c["id"])
    W = np.stack(wire_xyz) if wire_xyz else np.zeros((0, 3))
    WR = np.array(wire_rad) if wire_rad else np.zeros(0)

    schedule = []
    wire_close = []
    for r in screws:
        seat = np.array(r["seat_world"], float)
        axis = unit(r["axis_world"])
        length = float(r.get("length_mm") or 0)
        k = float((r.get("head") or {}).get("k") or 0)
        dk = float((r.get("head") or {}).get("dk") or r.get("d") or 0)
        shank_r = float(r.get("d") or 0) / 2.0
        gap = None
        cable = None
        if len(W):
            # Finite head cylinder and finite shank cylinder. Flat ends, not a sphere.
            head_gap = cylinder_gap(W, seat, seat - axis * k, dk / 2.0) - WR
            shank_gap = cylinder_gap(W, seat, seat + axis * max(length, 0.1), shank_r) - WR
            both = np.minimum(head_gap, shank_gap)
            i = int(np.argmin(both))
            gap = round(float(both[i]), 2)
            cable = wire_id[i]
            if fitted(r) and gap < 2.0:
                wire_close.append({"id": r["id"], "gap_mm": gap, "cable": cable,
                                   "label": "cad", "pose": "zero", "sample_mm": 0.25,
                                   "model": "finite head and shank cylinders, cable segments"})
        spec = r.get("spec") or ""
        size = r.get("size")
        button = "7380" in spec or "button" in spec.lower()
        chart = (TORQUE_7380 if button else TORQUE_912).get(size)
        # Chart depth rule. Horn thread is the aluminum case the chart names.
        # Plastic pilots and brass inserts are not in that sentence.
        anchor = r.get("anchor") or ""
        e = r.get("e")
        metal_horn = anchor.startswith("horn") or "output shaft" in anchor
        if metal_horn and size in HEAD_K:
            need = 2.0 * float(r.get("d") or 0)
            applies = e is not None and float(e) + 1e-6 >= need
            why = "aluminum, chart asks 2 x D (%g mm), engaged %s mm" % (need, e)
        elif "insert" in anchor and size in HEAD_K:
            applies = False
            why = "brass insert in plastic, not the steel or aluminum line on the chart"
        else:
            applies = False
            why = "not a steel or aluminum tapped hole of the depth the chart names"
        touches = bool(r.get("servo")) or "servo" in anchor or metal_horn or "case" in anchor
        locker = "yes" if metal_horn else "no"
        locker_why = ("docs/assembly_guide.md: a little Loctite 243 when the screw is metal into the motor metal. BOM 19 is that bottle."
                      if metal_horn else
                      "the same guide names metal against metal in the motors. This thread is not that.")
        rec = r.get("recess_check") or {}
        clr = r.get("clearance") or {}
        sw = r.get("sweep") or {}
        head_sw = (sw.get("head") or {})
        schedule.append({
            "id": r["id"],
            "fitted": fitted(r),
            "status": r.get("status") or r.get("len_status"),
            "group": r.get("group"),
            "joint": "%s -> %s" % (r.get("part"), r.get("into")),
            "anchor": anchor,
            "spec": spec,
            "size": size,
            "length_mm": r.get("length_mm"),
            "head": r.get("head"),
            "material": "A2" if "A2" in spec else ("factory" if "FACTORY" in str(r.get("len_status")) else "as named on the spec"),
            "nut": None,
            "insert": anchor if "insert" in anchor else None,
            "washer": "two 0.3 mm M2.5" if (fitted(r) and "eye" in anchor) else None,
            "hole_mm": clr.get("hole"),
            "hole_margin_mm": clr.get("margin"),
            "hole_status": clr.get("status"),
            "recess_mm": rec.get("recess"),
            "recess_status": rec.get("status"),
            "e_mm": e,
            "e_rule_mm": r.get("e_min"),
            "e_rule": r.get("rule"),
            "tip_gap_mm": r.get("tip_gap"),
            "near_mm": r.get("near"),
            "stop_mm": r.get("stop"),
            "wall_clearance_mm": head_sw.get("clearance_mm"),
            "wall_against": head_sw.get("against"),
            "wall_where": head_sw.get("where"),
            "wire_gap_mm": gap,
            "wire_id": cable,
            "wire_label": "cad" if gap is not None else None,
            "torque_chart_nm": chart,
            "torque_chart_applies": applies,
            "torque_why": why,
            "torque_src": TORQUE_SRC,
            "threadlocker": locker,
            "threadlocker_why": locker_why,
            "touches_servo": touches,
            "link": r.get("link"),
            "part": r.get("part"),
            "part_inst": r.get("part_inst"),
            "into": r.get("into"),
            "seat_world": r.get("seat_world"),
            "bom_line": r.get("line"),
            "supply": r.get("supply"),
            "number_label": "cad",
        })

    # D42: existing file, plus a split by anchor on the parts that file marks not uniform.
    sym = json.load(open(SYM))
    by_inst = {}
    for r in fit:
        by_inst.setdefault((r.get("part"), r.get("part_inst")), []).append(r)
    d42_parts = []
    for (part, inst), rs in sorted(by_inst.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        ok, name, errp = pattern_ok([x["seat_link"] for x in rs], 2.5)
        joints = {}
        for x in rs:
            joints.setdefault((x.get("into"), x.get("anchor")), []).append(x)
        joint_rows = []
        for (into, anchor), js in joints.items():
            jok, jname, jerr = pattern_ok([x["seat_link"] for x in js], 2.5)
            joint_rows.append({"into": into, "anchor": anchor, "n": len(js),
                               "uniform": jok, "pattern": jname, "max_mm": round(jerr, 2),
                               "ids": [x["id"] for x in js], "label": "cad"})
        d42_parts.append({"part": part, "inst": inst, "n": len(rs), "uniform": ok,
                          "pattern": name, "max_mm": round(errp, 2),
                          "joints": joint_rows, "label": "cad"})
    d42_fail_parts = [p for p in d42_parts if not p["uniform"]]
    d42_fail_joints = [j for p in d42_parts for j in p["joints"] if not j["uniform"]]

    # Left and right inner hip-roll screws, the D18 pair.
    pair = []
    for r in fit:
        if r["id"] in ("F133", "F135"):
            pair.append({"id": r["id"], "y": r["seat_world"][1], "part": r["part"]})

    # Empty holes already classified by the fastener file.
    why = {}
    for h in data.get("empty_holes") or []:
        why[h.get("why") or "?"] = why.get(h.get("why") or "?", 0) + 1

    # BUILD_ORDER coverage.
    text = open(BUILD).read()
    named = set(re.findall(r"\bF\d+\b", text))
    fit_ids = {r["id"] for r in fit}
    left_ids = {r["id"] for r in left}
    factory_ids = {r["id"] for r in fit if "FACTORY" in str(r.get("status") or r.get("len_status") or "")}
    missing = sorted(fit_ids - named - factory_ids, key=lambda s: int(s[1:]))
    stale = sorted((named & left_ids), key=lambda s: int(s[1:]))
    # Spec text in the order vs the JSON, for ids the order still drives.
    order_specs = {}
    for line in text.splitlines():
        ids = re.findall(r"\bF\d+\b", line)
        if ids and line[:1].isdigit() or (line[:3].rstrip(".").isdigit() if False else False):
            pass
        m = re.match(r"\d+\.\s+(?:JOIN\s+)?(?:\d+\s+x\s+)?(.+?):", line)
        if m:
            for i in ids:
                order_specs.setdefault(i, m.group(1).strip())
    spec_mismatch = []
    for r in fit:
        if r["id"] in order_specs and r.get("spec") and r["spec"] not in order_specs[r["id"]] and order_specs[r["id"]] not in r["spec"]:
            # Loose: the order line is a group spec. Flag only when the size/length token differs.
            tok = re.search(r"M\d(?:\.\d)?x\d+", r["spec"] or "")
            otok = re.search(r"M\d(?:\.\d)?x\d+", order_specs[r["id"]])
            if tok and otok and tok.group(0) != otok.group(0):
                spec_mismatch.append({"id": r["id"], "json": r["spec"], "order": order_specs[r["id"]], "label": "cad"})

    # Chest hole in the print STL. Constants are the ones in twin/dock/chest_hole.py.
    chest = None
    body = os.path.join(PRINT, "body_front.stl")
    if os.path.exists(body):
        m = trimesh.load(body, force="mesh")
        # chest_hole.py: world = STL + OFF, the hole axis is along x through the wall
        # at world y 0, z 38. The wall in that file is world x 36 to 46.
        off = np.array([-19.0, 0.0, 64.89093881])
        x_in, x_out = 36.0 - off[0], 46.0 - off[0]
        mid = np.array([(x_in + x_out) / 2.0, 0.0, 38.0 - off[2]])
        beside = mid + np.array([0.0, 8.0, 0.0])
        centre = bool(m.contains([mid])[0])
        wall = bool(m.contains([beside])[0])
        chest = {"centre_solid": centre, "wall_beside_solid": wall,
                 "hole_open": (not centre) and wall, "watertight": bool(m.is_watertight),
                 "label": "cad", "source": "twin/dock/chest_hole.py wall coordinates on print/body_front.stl"}

    # Proposed STLs: shank hole and head-side material. No new shape is built.
    proposals = []
    stl_jobs = []
    topo = os.path.join(LAB, "twin", "structure", "topology", "stl")
    for fn in sorted(os.listdir(topo)):
        if fn.endswith(".stl"):
            stl_jobs.append((os.path.join(topo, fn), fn[:-4], "topology"))
    eye = os.path.join(LAB, "twin", "structure", "shin_eye", "stl")
    for fn in sorted(os.listdir(eye)):
        if not fn.endswith(".stl"):
            continue
        part = fn[:-4]
        for suf in ("_web_cbore", "_collar_cbore", "_taper_cbore", "_web", "_taper"):
            if part.endswith(suf):
                part = part[: -len(suf)]
                break
        stl_jobs.append((os.path.join(eye, fn), part, "shin_eye"))

    screws_by_part = {}
    for r in fit:
        screws_by_part.setdefault(r["part"], []).append(r)

    for path, part, kind in stl_jobs:
        rs = screws_by_part.get(part) or []
        links = sorted({r["link"] for r in rs})
        mesh0 = trimesh.load(path, force="mesh")
        for link in links:
            try:
                Tv = visual_T(u, link, part)
            except KeyError as ex:
                proposals.append({"stl": os.path.relpath(path, REPO), "part": part, "link": link,
                                  "error": "no visual: %s" % (ex,), "kind": kind})
                continue
            mesh = mesh0.copy()
            mesh.apply_transform(Tv)
            per = []
            for r in rs:
                if r["link"] != link:
                    continue
                seat = np.array(r["seat_link"], float)
                axis = unit(r["axis_link"])
                nsol, n = shank_solid(mesh, seat, axis, r.get("near"))
                size = r.get("size") or "M3"
                rad = HEAD_R_KNURL.get(size, 2.84)
                first, last = head_stack(mesh, seat, axis, rad)
                per.append({"id": r["id"], "shank_solid": nsol, "shank_n": n,
                            "head_solid_from_mm": first, "head_solid_to_mm": last,
                            "spec": r.get("spec"), "e_mm": r.get("e"), "label": "cad"})
            proposals.append({"stl": os.path.relpath(path, REPO), "part": part, "link": link,
                              "kind": kind, "watertight": bool(mesh.is_watertight),
                              "screws": per})

    # Control: the same head test on the print STL, one link each. If the print
    # file is open and the proposal is solid, the pad filled the existing recess.
    controls = []
    for part, link, fid in (
        ("shin_left_sheet", "knee_and_ankle_assembly_2", "F203"),
        ("knee_to_ankle_left_sheet", "knee_and_ankle_assembly", "F197"),
        ("neck_left_sheet", "neck_pitch_assembly", "F228"),
        ("left_roll_to_pitch", "left_roll_to_pitch_assembly", "F187"),
    ):
        src = next(r for r in fit if r["id"] == fid)
        path = os.path.join(PRINT, part + ".stl")
        mesh0 = trimesh.load(path, force="mesh")
        Tv = visual_T(u, link, part)
        mesh0.apply_transform(Tv)
        seat = np.array(src["seat_link"], float)
        axis = unit(src["axis_link"])
        nsol, n = shank_solid(mesh0, seat, axis, src.get("near"))
        first, last = head_stack(mesh0, seat, axis, HEAD_R_KNURL["M3"])
        controls.append({"part": part, "id": fid, "shank_solid": nsol, "shank_n": n,
                         "head_solid_from_mm": first, "head_solid_to_mm": last,
                         "label": "cad", "stl": "print/" + part + ".stl"})

    # Nest constants, read from the existing module so the numbers are not retyped.
    sys.path.insert(0, NEST_LIB)
    import nestcad_lib as N  # noqa: E402
    import nest_parts as P  # noqa: E402

    WX = N.WALL_X
    BX0, BX1 = WX - N.BOX["x1"], WX - N.VHB_T
    lid_posts = [(BX0 + 14.0, 84.0), (BX0 + 14.0, -84.0), (BX1 - 6.0, 84.0), (BX1 - 6.0, -84.0)]
    # Confirm the list in nest_parts matches the arithmetic above.
    posts_match = list(P.LID_POSTS) == [(round(a, 5), round(b, 5)) for a, b in
                                        [(BX0 + 14.0, 84.0), (BX0 + 14.0, -84.0), (BX1 - 6.0, 84.0), (BX1 - 6.0, -84.0)]] \
        or [tuple(np.round(p, 5)) for p in P.LID_POSTS] == [tuple(np.round(p, 5)) for p in lid_posts]
    part_cx = (BX0 + BX1) / 2.0
    part_cy = 0.0
    xs = [p[0] for p in P.LID_POSTS]
    ys = [p[1] for p in P.LID_POSTS]
    pat_c = (sum(xs) / len(xs), sum(ys) / len(ys))
    # Mirror of each post through the part centre.
    def mirror_hit(posts, cx, cy, tol=0.2):
        worst = 0.0
        for x, y in posts:
            mx, my = 2 * cx - x, 2 * cy - y
            d = min(np.hypot(mx - a, my - b) for a, b in posts)
            worst = max(worst, d)
        return worst

    lid_err = mirror_hit(P.LID_POSTS, part_cx, part_cy)
    lid_err_own = mirror_hit(P.LID_POSTS, pat_c[0], pat_c[1])
    term = [(P.POST_X, P.TAB_Y), (P.POST_X, -P.TAB_Y)]
    term_err = mirror_hit(term, part_cx, part_cy)
    # Engagement of the lid screw the nest CAD already chose.
    lid_t = float(N.BOX["lid"])
    e_lid = 6.0 - lid_t
    e_lid_8 = 8.0 - lid_t
    nest = {
        "label": "calc",
        "source": "twin/dock/nest/cad/nest_parts.py and nestcad_lib.py",
        "lid_screws": {
            "ids": ["NL1", "NL2", "NL3", "NL4"],
            "spec": "M3x6 ISO 7380 A2 button head",
            "bom": "17j",
            "insert": "M3 heat-set, BOM 16, bore 4.0 mm, depth 5.8 mm",
            "washer": None,
            "nut": None,
            "qty": 4,
            "hole_mm": N.M3_CLEAR,
            "e_mm": round(e_lid, 2),
            "e_rule_mm": 4.5,
            "e_if_M3x8_mm": round(e_lid_8, 2),
            "bottoms_if_M3x8": e_lid_8 > N.INSERT_DEPTH,
            "insert_depth_mm": N.INSERT_DEPTH,
            "posts_match_source": bool(posts_match),
            "part_centre_mm": [round(part_cx, 2), round(part_cy, 2)],
            "pattern_centre_mm": [round(pat_c[0], 2), round(pat_c[1], 2)],
            "shift_from_part_centre_mm": round(pat_c[0] - part_cx, 2),
            "mirror_error_about_part_centre_mm": round(lid_err, 2),
            "mirror_error_about_pattern_centre_mm": round(lid_err_own, 2),
            "posts_xy": [[round(a, 2), round(b, 2)] for a, b in P.LID_POSTS],
            "box_x_mm": [round(BX0, 2), round(BX1, 2)],
        },
        "terminals": {
            "ids": ["NT1", "NT2"],
            "spec": "M3x8 DIN 912 A2",
            "bom": "17a",
            "insert": "M3 heat-set, BOM 16",
            "qty": 2,
            "hole_mm": N.M3_CLEAR,
            "mirror_error_about_part_centre_mm": round(term_err, 2),
            "posts_xy": [[round(a, 2), round(b, 2)] for a, b in term],
            "clamped_stack": "M3 ring lug named in NEST_CAD.md, thickness not in the CAD",
        },
        "jack": {
            "part": "Same Sky PJ-005A, dock line K6b, nut and washer come with the jack",
            "hole_mm": N.JACK["hole"],
            "wrench": "not in the repo",
        },
        "duck_screws_added": 0,
    }

    # Counts the existing fastener file already publishes, recomputed here.
    from collections import Counter
    st_count = Counter((r.get("status") or r.get("len_status") or "") for r in screws)
    recess_count = Counter((r.get("recess_check") or {}).get("status") for r in fit)
    hole_count = Counter((r.get("clearance") or {}).get("status") for r in fit)
    len_count = Counter(r.get("len_status") for r in fit)

    findings = {
        "seat_world_max_error_mm": seat_err,
        "seat_world_label": "cad",
        "screws": len(screws),
        "fitted": len(fit),
        "left_out": len(left),
        "inserts": len(inserts),
        "inserts_fitted": sum(1 for r in inserts if fitted(r) and not r.get("leave_out")),
        "status": dict(st_count),
        "fitted_length_status": {str(k): v for k, v in len_count.items()},
        "fitted_recess": {str(k): v for k, v in recess_count.items()},
        "fitted_hole": {str(k): v for k, v in hole_count.items()},
        "sym_not_uniform_existing": sym.get("not_uniform"),
        "d42_parts_not_uniform": [{"part": p["part"], "inst": p["inst"], "n": p["n"],
                                  "max_mm": p["max_mm"], "pattern": p["pattern"]} for p in d42_fail_parts],
        "d42_joints_not_uniform": d42_fail_joints,
        "d18_pair": pair,
        "empty_hole_why": why,
        "build_order_missing_fitted": missing,
        "factory_screws_not_in_build_order": len(factory_ids - named),
        "build_order_names_left_out": stale,
        "build_order_length_mismatch": spec_mismatch,
        "wire_gap_under_2mm": sorted(wire_close, key=lambda z: z["gap_mm"])[:40],
        "wire_overlap": [z for z in wire_close if z["gap_mm"] < 0],
        "chest": chest,
        "print_head_control": controls,
        "nest": nest,
        "proposals": proposals,
        "torque_src": TORQUE_SRC,
    }
    json.dump({"robot": schedule, "nest": nest,
               "read": "robot rows are every screw in fasteners/fasteners.json. nest is the nest CAD and is not in that file. cad is a measurement. calc is arithmetic on those measurements. cited is a page."},
              open(os.path.join(HERE, "schedule.json"), "w"), indent=1)
    # Proposals can be large; keep them, they are small lists.
    json.dump(findings, open(os.path.join(HERE, "findings.json"), "w"), indent=1)
    write_figures(nest, findings)
    print("seat_world max error mm", seat_err)
    print("fitted", len(fit), "left", len(left), "missing from order", missing)
    print("stale in order", stale)
    print("length mismatch", spec_mismatch)
    print("d42 part fails", len(d42_fail_parts), "joint fails", len(d42_fail_joints))
    print("wire under 2 mm", len(wire_close), "overlap", len(findings["wire_overlap"]))
    print("chest", chest)
    print("print head control", controls)
    print("driven missing", missing)
    print("nest lid shift", nest["lid_screws"]["shift_from_part_centre_mm"],
          "mirror err", nest["lid_screws"]["mirror_error_about_part_centre_mm"])
    # Proposal headline
    for p in proposals:
        if "error" in p:
            print("STL", p["stl"], p["error"])
            continue
        bad = [s for s in p["screws"] if s["shank_solid"] or (s["head_solid_from_mm"] is not None and s["head_solid_from_mm"] <= 0.5)]
        if bad:
            print("HEAD/SHANK", p["kind"], os.path.basename(p["stl"]), p["link"],
                  [(s["id"], s["shank_solid"], s["head_solid_from_mm"], s["head_solid_to_mm"]) for s in bad[:6]],
                  "n", len(bad))


def write_figures(nest, findings):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lid = nest["lid_screws"]
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    x0, x1 = lid["box_x_mm"]
    ax.add_patch(plt.Rectangle((x0, -90), x1 - x0, 180, fill=False, lw=1.2, color="#333"))
    xs, ys = zip(*lid["posts_xy"])
    ax.scatter(xs, ys, s=60, c="#1f4e79", zorder=3, label="lid screw, as drawn")
    ax.scatter([lid["part_centre_mm"][0]], [lid["part_centre_mm"][1]], marker="+", s=120, c="#333", label="part centre")
    ax.scatter([lid["pattern_centre_mm"][0]], [lid["pattern_centre_mm"][1]], marker="x", s=80, c="#b00020", label="pattern centre")
    tx, ty = zip(*nest["terminals"]["posts_xy"])
    ax.scatter(tx, ty, s=40, c="#c47b00", zorder=3, label="terminal screw")
    ax.annotate("", xy=(lid["pattern_centre_mm"][0], 8), xytext=(lid["part_centre_mm"][0], 8),
                arrowprops=dict(arrowstyle="<->", color="#b00020"))
    ax.text(0.5 * (lid["part_centre_mm"][0] + lid["pattern_centre_mm"][0]), 14,
            "4.0 mm", color="#b00020", ha="center", fontsize=8)
    ax.set_aspect("equal")
    ax.set_xlabel("x mm, nest frame, toward the wall")
    ax.set_ylabel("y mm, along the wall")
    ax.set_title("Nest lid screws as drawn. Calc only, from nest_parts.py")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8, frameon=False)
    ax.set_xlim(x0 - 12, x1 + 12)
    ax.set_ylim(-105, 105)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "nest_lid_screws.png"), dpi=140, bbox_inches="tight")
    plt.close()

    # Installed-set counts, recomputed from fasteners.json.
    labels = []
    vals = []
    for k, v in sorted(findings["fitted_length_status"].items(), key=lambda kv: -kv[1]):
        if k in ("None", "FACTORY"):
            continue
        labels.append(str(k)[:42])
        vals.append(v)
    for k, v in sorted(findings["fitted_recess"].items(), key=lambda kv: -kv[1]):
        if k in ("None", "OK"):
            continue
        labels.append("recess " + str(k)[:32])
        vals.append(v)
    labels.append("driven screws missing from BUILD_ORDER")
    vals.append(len(findings["build_order_missing_fitted"]))
    labels.append("left-out id mentioned, not driven")
    vals.append(len(findings["build_order_names_left_out"]))
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ypos = np.arange(len(labels))
    ax.barh(ypos, vals, color="#1f4e79")
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("count, CAD check only, from fasteners.json and BUILD_ORDER.md")
    ax.set_title("Installed screw checks")
    for i, v in enumerate(vals):
        ax.text(v + 0.4, i, str(v), va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "installed_screw_checks.png"), dpi=140)
    plt.close()


if __name__ == "__main__":
    main()
