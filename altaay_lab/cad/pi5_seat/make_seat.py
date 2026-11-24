#!/usr/bin/env python3
"""Board seat for a Raspberry Pi 5 in the duck body. CAD check only.

Dimensions come from the official drawings named in the report. The script
writes a seat mesh, a fit report, and a picture. It does not edit the BOM.
"""

from __future__ import annotations

import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PRINT = os.path.join(ROOT, "print")

# Cited, RP-008347-DS-1, the mechanical drawing. Millimetres.
BOARD_X = 85.0
BOARD_Y = 56.0
HOLE_D = 2.7
HOLE_PITCH_X = 58.0
HOLE_INSET_X = 3.5
HOLE_PITCH_Y = 49.0
# Calc only: the drawing shows the 49 mm pitch on the 56 mm side.
HOLE_INSET_Y = (BOARD_Y - HOLE_PITCH_Y) / 2.0

# Cited, Active Cooler mechanical drawing. Height of the cooler body.
COOLER_H = 12.70
COOLER_X = 43.50
COOLER_Y = 42.50

# Seat plate. The pilot is the electronics rule in MOUNTING.md: 2.0 mm.
PLATE_T = 2.4
BOSS_H = 5.0
BOSS_D = 6.0
PILOT_D = 2.0
CLEAR_MM = 2.0

# CAD mass model cited in DECISIONS.md D66. Not a scale reading.
MASS_KG = 2.949
# Cited, Adafruit 5291 product weight, sim/mass_budget.py.
ZERO_KG = 0.010
# Head print bbox centre, used only as the old board's height band.
# The real Pi pose is the head mount. This z is the head shell centre.


def load_tris(path):
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 80)[0]
    kind = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    arr = np.frombuffer(data, dtype=kind, count=n, offset=84)
    return np.array(arr["v"], dtype=np.float64)


def tri_bounds(verts):
    return verts.min(axis=1), verts.max(axis=1)


SHELLS = (
    "body_middle_top.stl",
    "body_middle_bottom.stl",
    "body_front.stl",
    "body_back.stl",
    "trunk_top.stl",
    "head.stl",
)


def load_shells():
    out = {}
    for name in SHELLS:
        verts = load_tris(os.path.join(PRINT, name))
        tmin, tmax = tri_bounds(verts)
        flat = verts.reshape(-1, 3)
        out[name] = (verts, tmin, tmax, flat.min(axis=0), flat.max(axis=0))
    return out


def overlaps(shells, names, bmin, bmax):
    total = 0
    detail = {}
    for name in names:
        verts, tmin, tmax, _smin, _smax = shells[name]
        hit = np.all(tmax >= bmin, axis=1) & np.all(tmin <= bmax, axis=1)
        count = int(hit.sum())
        detail[name] = count
        total += count
    return total, detail


def clearance(shells, names, bmin, bmax, limit=8.0):
    """Largest margin, in 0.5 mm steps, that still misses every shell triangle."""
    best = 0.0
    pad = 0.0
    while pad <= limit + 1e-9:
        grown_min = bmin - pad
        grown_max = bmax + pad
        total, _ = overlaps(shells, names, grown_min, grown_max)
        if total:
            break
        best = pad
        pad += 0.5
    return best


def holes():
    xs = (HOLE_INSET_X, HOLE_INSET_X + HOLE_PITCH_X)
    ys = (HOLE_INSET_Y, HOLE_INSET_Y + HOLE_PITCH_Y)
    return [(x, y) for x in xs for y in ys]


def box_corners(origin, size):
    corners = []
    for ix in (0.0, 1.0):
        for iy in (0.0, 1.0):
            for iz in (0.0, 1.0):
                corners.append(origin + np.array([ix, iy, iz]) * size)
    return np.array(corners)


BODY = (
    "body_middle_top.stl",
    "body_middle_bottom.stl",
    "body_front.stl",
    "body_back.stl",
    "trunk_top.stl",
)


def rpy_matrix(rpy):
    roll, pitch, yaw = rpy
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
    ry = np.array([[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]])
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]])
    return rz @ ry @ rx


def servo_points_print_frame(step=5):
    """Servo case vertices in the print millimetre frame.

    The URDF is in metres. trunk_top.stl matches the print file on all six
    faces after +19.0 mm in x and -64.9 mm in z (CAD check only). That same
    shift is applied to every servo visual.
    """
    import xml.etree.ElementTree as ET
    urdf_dir = os.path.join(ROOT, "mini_bdx", "robots", "open_duck_mini_v2")
    tree = ET.parse(os.path.join(urdf_dir, "robot.urdf"))
    root = tree.getroot()
    joints = {}
    for joint in root.findall("joint"):
        origin = joint.find("origin")
        xyz = np.zeros(3)
        rpy = np.zeros(3)
        if origin is not None:
            xyz = np.array([float(v) for v in origin.attrib.get("xyz", "0 0 0").split()])
            rpy = np.array([float(v) for v in origin.attrib.get("rpy", "0 0 0").split()])
        joints[joint.find("child").attrib["link"]] = (
            joint.find("parent").attrib["link"], xyz, rpy)
    cache = {}

    def world(link):
        if link in cache:
            return cache[link]
        if link not in joints:
            cache[link] = np.eye(4)
            return cache[link]
        parent, xyz, rpy = joints[link]
        pose = np.eye(4)
        pose[:3, :3] = rpy_matrix(rpy)
        pose[:3, 3] = xyz
        cache[link] = world(parent) @ pose
        return cache[link]

    shift = np.array([19.0, 0.0, -64.9])
    clouds = []
    names = []
    for link in root.findall("link"):
        lname = link.attrib["name"]
        for vis in link.findall("visual"):
            mesh = vis.find("geometry/mesh")
            if mesh is None:
                continue
            fn = mesh.attrib["filename"].split("/")[-1]
            if not (fn.startswith("wj-wk") or fn == "sg90.stl"):
                continue
            origin = vis.find("origin")
            xyz = np.zeros(3)
            rpy = np.zeros(3)
            if origin is not None:
                xyz = np.array([float(v) for v in origin.attrib.get("xyz", "0 0 0").split()])
                rpy = np.array([float(v) for v in origin.attrib.get("rpy", "0 0 0").split()])
            pose = world(lname)
            local = np.eye(4)
            local[:3, :3] = rpy_matrix(rpy)
            local[:3, 3] = xyz
            full = pose @ local
            verts = load_tris(os.path.join(urdf_dir, fn)).reshape(-1, 3)
            # One sample in five is enough for a 2 mm clearance and keeps the search short.
            verts = verts[::step]
            pts = (full[:3, :3] @ verts.T).T + full[:3, 3]
            pts = pts * 1000.0 + shift
            clouds.append(pts)
            names.append("%s %s" % (lname, fn))
    counts = [len(c) for c in clouds]
    return names, np.vstack(clouds), shift.tolist(), counts


def point_box_distance(points, bmin, bmax):
    clamped = np.minimum(np.maximum(points, bmin), bmax)
    return np.linalg.norm(points - clamped, axis=1)


def search(shells, servo_pts):
    """Grid search. x is forward, y is left, z is up, print frame, mm.

    The USB end of the board is +x in the board frame, so the board's +x
    points toward the body front when the seat faces forward.
    """
    # Cooler on the component face, plate under the board. PCB thickness is
    # not a called-out dimension on the drawing, so it is not added.
    height = COOLER_H + PLATE_T
    best = None
    for swap in (False, True):
        size = np.array([BOARD_Y, BOARD_X, height] if swap else [BOARD_X, BOARD_Y, height])
        for x in np.arange(-70.0, 21.0, 5.0):
            for y in np.arange(-24.0, 25.0, 4.0):
                for z in np.arange(-78.0, -18.0, 4.0):
                    origin = np.array([x, y, z], dtype=float)
                    bmin = origin
                    bmax = origin + size
                    total, detail = overlaps(shells, BODY, bmin, bmax)
                    if total:
                        continue
                    servo_gap = float(point_box_distance(servo_pts, bmin, bmax).min())
                    gap = clearance(shells, BODY, bmin, bmax, limit=6.0)
                    if gap < CLEAR_MM:
                        continue
                    # Shells stay on the 2 mm rule. The servo gap is reported
                    # even when it is under 2 mm, and the search keeps the
                    # pose with the larger servo gap, then the more forward one.
                    score = (round(servo_gap, 2), float(x + size[0]))
                    row = {
                        "swap": swap,
                        "origin_mm": [round(v, 2) for v in origin],
                        "size_mm": [round(v, 2) for v in size],
                        "clear_mm": gap,
                        "servo_clear_mm": round(servo_gap, 2),
                        "score": score,
                    }
                    if best is None or score > best["score"]:
                        best = row
    return best


def head_try(shells):
    """The current mount is in the head. Try the same outline there."""
    _verts, _tmin, _tmax, tmin, tmax = shells["head.stl"]
    height = COOLER_H + PLATE_T
    size = np.array([BOARD_X, BOARD_Y, height])
    # Head shell spans a wide, thin volume. Sit the box in the upper half.
    center = (tmin + tmax) / 2.0
    origin = np.array([
        center[0] - size[0] / 2.0,
        center[1] - size[1] / 2.0,
        tmax[2] - size[2] - 4.0,
    ])
    bmin = origin
    bmax = origin + size
    total, detail = overlaps(shells, ("head.stl",), bmin, bmax)
    return {
        "fits": total == 0,
        "triangle_hits": total,
        "by_shell": detail,
        "origin_mm": [round(float(v), 2) for v in origin],
        "size_mm": [round(float(v), 2) for v in size],
        "head_bbox_mm": {
            "min": [round(float(v), 1) for v in tmin],
            "max": [round(float(v), 1) for v in tmax],
            "size": [round(float(v), 1) for v in (tmax - tmin)],
        },
    }


def _box_tris(p0, p1):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    faces = [
        ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)),
        ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),
        ((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)),
        ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)),
        ((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)),
        ((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)),
    ]
    tris = []
    for a, b, c, d in faces:
        tris.append((a, b, c))
        tris.append((a, c, d))
    return tris


def write_stl(path, tris):
    buf = bytearray(b"pi5 seat" + b"\0" * 72)
    buf += struct.pack("<I", len(tris))
    for a, b, c in tris:
        buf += struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0)
    with open(path, "wb") as handle:
        handle.write(buf)


def _split_span(spans, cut_a, cut_b):
    """Remove [cut_a, cut_b] from a list of [a, b] spans."""
    nxt = []
    for a, b in spans:
        if cut_b <= a or cut_a >= b:
            nxt.append((a, b))
            continue
        if a < cut_a:
            nxt.append((a, min(b, cut_a)))
        if cut_b < b:
            nxt.append((max(a, cut_b), b))
    return [(a, b) for a, b in nxt if b - a > 1e-6]


def rects_minus(outer, holes):
    """Solid rectangles left after cutting hole rectangles out of outer.

    Each rectangle is (x0, y0, x1, y1). Used so a pilot is an opening, not a
    note in the JSON.
    """
    x0, y0, x1, y1 = outer
    ys = {y0, y1}
    for hx0, hy0, hx1, hy1 in holes:
        ys.add(min(y1, max(y0, hy0)))
        ys.add(min(y1, max(y0, hy1)))
    ordered = sorted(ys)
    solid = []
    for ya, yb in zip(ordered, ordered[1:]):
        if yb - ya <= 1e-6:
            continue
        mid = (ya + yb) / 2.0
        spans = [(x0, x1)]
        for hx0, hy0, hx1, hy1 in holes:
            if hy0 < mid < hy1:
                spans = _split_span(spans, hx0, hx1)
        for a, b in spans:
            solid.append((a, ya, b, yb))
    return solid


def hole_rects(origin, swap):
    """2.0 mm square pilots, axis aligned, in the print frame."""
    ox, oy, _oz = origin
    half = PILOT_D / 2.0
    rects = []
    for hx, hy in holes():
        if swap:
            cx, cy = ox + hy, oy + hx
        else:
            cx, cy = ox + hx, oy + hy
        rects.append((cx - half, cy - half, cx + half, cy + half))
    return rects


def boss_wall_rects(hole_rect):
    """Four walls of a boss around one pilot. Outer size is BOSS_D."""
    hx0, hy0, hx1, hy1 = hole_rect
    cx = (hx0 + hx1) / 2.0
    cy = (hy0 + hy1) / 2.0
    outer = BOSS_D / 2.0
    return (
        (cx - outer, cy - outer, cx + outer, hy0),
        (cx - outer, hy1, cx + outer, cy + outer),
        (cx - outer, hy0, hx0, hy1),
        (hx1, hy0, cx + outer, hy1),
    )


def seat_mesh(origin, swap):
    """Plate and four bosses. Each boss and the plate under it have a 2.0 mm pilot."""
    ox, oy, oz = [float(v) for v in origin]
    plate = np.array([BOARD_Y, BOARD_X] if swap else [BOARD_X, BOARD_Y])
    # 2 mm lip past the board on the long sides, none past the USB and MIPI edges
    # so those connectors stay reachable.
    margin = 2.0
    outer = (ox - margin, oy - margin, ox + plate[0] + margin, oy + plate[1] + margin)
    openings = hole_rects(origin, swap)
    tris = []
    for x0, y0, x1, y1 in rects_minus(outer, openings):
        tris.extend(_box_tris((x0, y0, oz), (x1, y1, oz + PLATE_T)))
    z0 = oz + PLATE_T
    z1 = z0 + BOSS_H
    for hole in openings:
        for x0, y0, x1, y1 in boss_wall_rects(hole):
            tris.extend(_box_tris((x0, y0, z0), (x1, y1, z1)))
    return tris


def com_shift(origin, size):
    """Fore-aft shift if the Zero's 10 g leaves the head and a new mass arrives.

    The head shell centre stands in for the old board. Pi 5 mass was not on
    the product page, so this is a sensitivity, calc only.
    """
    head = load_tris(os.path.join(PRINT, "head.stl"))
    hmin = head.reshape(-1, 3).min(axis=0)
    hmax = head.reshape(-1, 3).max(axis=0)
    old = (hmin + hmax) / 2.0
    new = origin + size / 2.0
    # 50 g is the shop Weight field for the 4 GB board (SC1111). The 2 GB
    # board's own mass is not on that page. 40 g and 60 g stay a sensitivity.
    labels = {
        50.0: "calc only, using 50 g cited from raspberrypi.dk additional information, Raspberry Pi 5 4 GB, SC1111. Official drawing prints no mass.",
        40.0: "calc only, sensitivity around the 50 g shop weight",
        60.0: "calc only, sensitivity around the 50 g shop weight",
    }
    rows = []
    for grams in (40.0, 50.0, 60.0):
        m = grams / 1000.0
        mass = MASS_KG - ZERO_KG + m
        # Old whole-robot CoM x is taken as 0 in this sensitivity, which is
        # the ankle-axis band in MASS_BUDGET.md (0 to 1 mm ahead). The shift
        # is the change from removing the old mass and adding the new one.
        dx = (m * new[0] - ZERO_KG * old[0]) / mass
        dz = (m * new[2] - ZERO_KG * old[2]) / mass
        rows.append({
            "grams": grams,
            "label": labels[grams],
            "com_x_mm": round(float(dx), 3),
            "com_z_mm": round(float(dz), 3),
        })
    straight = float(np.linalg.norm(new - old))
    return {
        "old_head_centre_mm": [round(float(v), 1) for v in old],
        "new_centre_mm": [round(float(v), 1) for v in new],
        "straight_line_mm": round(straight, 1),
        "straight_line_label": "calc only, shell centres, not a routed cable",
        "mass_model_kg": MASS_KG,
        "mass_model_label": "CAD mass model, DECISIONS.md D66, not a scale",
        "rows": rows,
        "backward_margin_mm": "about 4 to 6",
        "backward_margin_label": "sim pass only, sim/ADDED_MASS_SIM.md table 7",
    }


def render(shells, origin, size, dest, servo_pts=None, extra=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(8.2, 6.2))
    ax = fig.add_subplot(111, projection="3d")
    colors = {
        "body_middle_top.stl": "#9bb7d4",
        "body_middle_bottom.stl": "#7f9bb5",
        "body_front.stl": "#c5d4c0",
        "body_back.stl": "#d4c4b0",
        "trunk_top.stl": "#e0d28a",
    }
    for name, color in colors.items():
        verts = shells[name][0]
        step = max(1, len(verts) // 2500)
        sample = verts[::step]
        coll = Poly3DCollection(sample, alpha=0.12, facecolor=color, edgecolor="none")
        ax.add_collection3d(coll)
    board = box_corners(origin, size)
    # Draw the seat box edges.
    edges = [
        (0, 1), (0, 2), (0, 4), (3, 1), (3, 2), (3, 7),
        (5, 1), (5, 4), (5, 7), (6, 2), (6, 4), (6, 7),
    ]
    # corner order from box_corners is ix, iy, iz nested
    for a, b in edges:
        ax.plot(*board[[a, b]].T, color="#1a73e8", linewidth=2.0)
    if extra is not None:
        other = box_corners(np.array(extra[0], dtype=float), np.array(extra[1], dtype=float))
        for a, b in edges:
            ax.plot(*other[[a, b]].T, color="#188038", linewidth=1.6)
    if servo_pts is not None and len(servo_pts):
        sample = servo_pts[:: max(1, len(servo_pts) // 4000)]
        ax.scatter(sample[:, 0], sample[:, 1], sample[:, 2], s=1, c="#c43b3b", depthshade=False)
    ax.set_xlim(-110, 70)
    ax.set_ylim(-60, 60)
    ax.set_zlim(-110, 50)
    ax.set_xlabel("x forward, mm")
    ax.set_ylabel("y left, mm")
    ax.set_zlabel("z up, mm")
    ax.set_title("CAD check only: seat behind the hips, servos at the yaw stops")
    fig.tight_layout()
    fig.savefig(dest, dpi=110)
    plt.close(fig)


def remesh(report_path=None):
    """Rewrite the seat STL from the saved pose. Does not rerun the search."""
    path = report_path or os.path.join(HERE, "seat_fit.json")
    report = json.loads(open(path, encoding="utf-8").read())
    origin = report["origin_mm"]
    swap = bool(report["long_side_along_y"])
    tris = seat_mesh(origin, swap)
    stl_path = os.path.join(HERE, "pi5_seat.stl")
    write_stl(stl_path, tris)
    return stl_path, len(tris)


def yaw_stop_cloud():
    """Servo vertices at the two hip-yaw stops used for the picture.

    Left yaw at its negative stop and right yaw at its positive stop.
    Those are the samples that set the published gaps. CAD check only.
    """
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import search_pose as sweep
    angles = {"left_hip_yaw": -0.524, "right_hip_yaw": 0.524}
    joints, _limits, visuals = sweep.load_model()
    memo = {}
    clouds = []
    for lname, _fn, verts, local in visuals:
        full = sweep.chain(joints, lname, angles, memo) @ local
        pts = (full[:3, :3] @ verts[::6].T).T + full[:3, 3]
        pts = pts * 1000.0 + sweep.SHIFT
        keep = (
            (pts[:, 0] > -150.0) & (pts[:, 0] < 70.0)
            & (pts[:, 1] > -70.0) & (pts[:, 1] < 70.0)
            & (pts[:, 2] > -110.0) & (pts[:, 2] < 40.0)
        )
        if keep.any():
            clouds.append(pts[keep])
    if not clouds:
        return None
    return np.vstack(clouds)


def publish_saved():
    """Rebuild the STL and the picture from seat_fit.json, then check clearance.

    This is the normal path. It does not run the old grid, which cannot
    reach this origin and would overwrite the hip-clear seat.
    """
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import search_pose as sweep
    path = os.path.join(HERE, "seat_fit.json")
    report = json.loads(open(path, encoding="utf-8").read())
    origin = [float(v) for v in report["origin_mm"]]
    size = [float(v) for v in report["size_mm"]]
    stl_path, count = remesh(path)
    joints, limits, visuals = sweep.load_model()
    shells = load_shells()
    bmin = np.array(origin, dtype=float)
    bmax = bmin + np.array(size, dtype=float)
    shells_gap = sweep.shell_report(shells, bmin, bmax)
    worst = sweep.verify(joints, limits, visuals, origin, size)
    report["shell_mm"] = shells_gap
    report["shell_min_mm"] = min(shells_gap.values())
    report["servo_mm"] = worst["mm"]
    report["servo_check"] = worst
    report["triangles"] = count
    png_path = os.path.join(HERE, "pi5_seat_in_body.png")
    extra = None
    reg = report.get("regulator") or {}
    if reg.get("origin_mm") and reg.get("size_mm"):
        extra = (reg["origin_mm"], reg["size_mm"])
    render(shells, bmin, bmax - bmin, png_path, yaw_stop_cloud(), extra=extra)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    ok = report["shell_min_mm"] >= CLEAR_MM and worst["mm"] >= CLEAR_MM
    print(json.dumps({
        "origin_mm": origin,
        "shell_min_mm": report["shell_min_mm"],
        "servo_mm": worst["mm"],
        "stl": stl_path,
        "ok": ok,
    }, indent=1))
    return 0 if ok else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--remesh"]:
        path, count = remesh()
        print(json.dumps({"stl": path, "triangles": count}))
        return 0
    if argv != ["--legacy-grid"]:
        return publish_saved()
    shells = load_shells()
    servo_names, servo_pts, shift, servo_counts = servo_points_print_frame()
    head = head_try(shells)
    found = search(shells, servo_pts)
    if found is None:
        report = {"fits": False, "head": head, "label": "CAD check only"}
    else:
        origin = np.array(found["origin_mm"], dtype=float)
        size = np.array(found["size_mm"], dtype=float)
        full_names, full_pts, _shift, full_counts = servo_points_print_frame(step=1)
        nearest_name = None
        nearest_gap = None
        cursor = 0
        for name, count in zip(full_names, full_counts):
            chunk = full_pts[cursor:cursor + count]
            cursor += count
            gap = float(point_box_distance(chunk, origin, origin + size).min())
            if nearest_gap is None or gap < nearest_gap:
                nearest_gap = gap
                nearest_name = name
        found["servo_clear_mm"] = round(nearest_gap, 2)
        left_y = None
        right_y = None
        cursor = 0
        for name, count in zip(full_names, full_counts):
            chunk = full_pts[cursor:cursor + count]
            cursor += count
            if "0123middlecase" not in name:
                continue
            if name.startswith("hip_roll_assembly "):
                left_y = float(chunk[:, 1].min())
            elif name.startswith("hip_roll_assembly_2 "):
                right_y = float(chunk[:, 1].max())
        hip_slot = None
        if left_y is not None and right_y is not None:
            hip_slot = {
                "left_hip_inner_y_mm": round(left_y, 2),
                "right_hip_inner_y_mm": round(right_y, 2),
                "gap_mm": round(left_y - right_y, 2),
                "board_y_mm": BOARD_Y,
                "shortfall_mm": round(BOARD_Y - (left_y - right_y), 2),
                "label": "CAD check only, middle-case vertices after the trunk_top shift. The board is wider than the slot between the hip cases.",
            }
        tris = seat_mesh(origin, found["swap"])
        stl_path = os.path.join(HERE, "pi5_seat.stl")
        write_stl(stl_path, tris)
        png_path = os.path.join(HERE, "pi5_seat_in_body.png")
        render(shells, origin, size, png_path, servo_pts)
        com = com_shift(origin, size)
        # Camera is in the head. Straight line from the seat centre to the
        # head shell centre, calc only.
        report = {
            "label": "CAD check only",
            "fits_in_body": True,
            "clear_mm": found["clear_mm"],
            "servo_clear_mm": found.get("servo_clear_mm"),
            "nearest_servo": nearest_name,
            "hip_slot": hip_slot,
            "servo_shift_mm": shift,
            "servo_visuals": len(servo_names),
            "servo_frame": "URDF metres times 1000, then +19.0 mm x and -64.9 mm z so trunk_top matches the print file on all six faces. CAD check only.",
            "clear_rule_mm": CLEAR_MM,
            "origin_mm": found["origin_mm"],
            "size_mm": found["size_mm"],
            "long_side_along_y": found["swap"],
            "head": head,
            "board_mm": [BOARD_X, BOARD_Y],
            "hole_d_mm": HOLE_D,
            "hole_pitch_mm": [HOLE_PITCH_X, HOLE_PITCH_Y],
            "hole_inset_x_mm": HOLE_INSET_X,
            "hole_inset_y_mm": HOLE_INSET_Y,
            "hole_inset_y_label": "calc only, (56 - 49) / 2",
            "holes_board_mm": [[round(a, 2), round(b, 2)] for a, b in holes()],
            "cooler_mm": [COOLER_X, COOLER_Y, COOLER_H],
            "plate_t_mm": PLATE_T,
            "boss_h_mm": BOSS_H,
            "pilot_d_mm": PILOT_D,
            "pcb_thickness": "BLOCKER, not a called-out dimension on the drawing",
            "com": com,
            "stl": "altaay_lab/cad/pi5_seat/pi5_seat.stl",
            "png": "altaay_lab/cad/pi5_seat/pi5_seat_in_body.png",
            "sources": {
                "board": "https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf",
                "cooler": "https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-mechanical-drawing.pdf",
            },
        }
    path = os.path.join(HERE, "seat_fit.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in report if k != "head"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
