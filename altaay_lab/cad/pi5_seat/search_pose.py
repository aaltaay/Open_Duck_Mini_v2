#!/usr/bin/env python3
"""Search a Pi 5 seat that clears the print shells and the servo meshes.

The forward-first score is a search order. The published seat is the Active
Cooler pose in seat_fit.json, which keeps a larger gap than the further
forward passive-sink pose.

CAD check only. The hip yaw, roll, and pitch joints are sampled from stop
to stop. A pose is kept only when the keep-out box stays at least 2 mm off
every print shell and at least 2 mm off every sampled servo vertex.
"""
from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_seat as seat

URDF_DIR = os.path.join(seat.ROOT, "mini_bdx", "robots", "open_duck_mini_v2")
SHIFT = np.array([19.0, 0.0, -64.9])
HIP_JOINTS = (
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
)
# Samples from stop to stop, including both stops. CAD check only.
SAMPLES = {
    "yaw": 7,
    "roll": 5,
    "pitch": 7,
}
BODY = (
    "body_middle_top.stl",
    "body_middle_bottom.stl",
    "body_front.stl",
    "body_back.stl",
    "trunk_top.stl",
)


def rodrigues(axis, angle):
    a = np.asarray(axis, dtype=float)
    n = np.linalg.norm(a)
    if n < 1e-12 or abs(angle) < 1e-12:
        return np.eye(3)
    x, y, z = a / n
    c, s = np.cos(angle), np.sin(angle)
    one = 1.0 - c
    return np.array([
        [c + x * x * one, x * y * one - z * s, x * z * one + y * s],
        [y * x * one + z * s, c + y * y * one, y * z * one - x * s],
        [z * x * one - y * s, z * y * one + x * s, c + z * z * one],
    ])


def load_model():
    root = ET.parse(os.path.join(URDF_DIR, "robot.urdf")).getroot()
    joints = {}
    limits = {}
    for joint in root.findall("joint"):
        origin = joint.find("origin")
        xyz = np.zeros(3)
        rpy = np.zeros(3)
        if origin is not None:
            xyz = np.array([float(v) for v in origin.attrib.get("xyz", "0 0 0").split()])
            rpy = np.array([float(v) for v in origin.attrib.get("rpy", "0 0 0").split()])
        axis_el = joint.find("axis")
        axis = np.array([0.0, 0.0, 1.0])
        if axis_el is not None and axis_el.attrib.get("xyz"):
            axis = np.array([float(v) for v in axis_el.attrib["xyz"].split()])
        name = joint.attrib["name"]
        child = joint.find("child").attrib["link"]
        parent = joint.find("parent").attrib["link"]
        joints[child] = (parent, xyz, rpy, axis, name)
        lim = joint.find("limit")
        if lim is not None and "lower" in lim.attrib:
            limits[name] = (float(lim.attrib["lower"]), float(lim.attrib["upper"]))
    visuals = []
    cache = {}
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
            path = os.path.join(URDF_DIR, fn)
            if path not in cache:
                cache[path] = seat.load_tris(path).reshape(-1, 3)
            local = np.eye(4)
            local[:3, :3] = seat.rpy_matrix(rpy)
            local[:3, 3] = xyz
            visuals.append((lname, fn, cache[path], local))
    return joints, limits, visuals


def chain(joints, link, angles, memo):
    key = (link, tuple(sorted(angles.items())))
    if key in memo:
        return memo[key]
    if link not in joints:
        memo[key] = np.eye(4)
        return memo[key]
    parent, xyz, rpy, axis, jname = joints[link]
    pose = np.eye(4)
    pose[:3, :3] = seat.rpy_matrix(rpy) @ rodrigues(axis, angles.get(jname, 0.0))
    pose[:3, 3] = xyz
    memo[key] = chain(joints, parent, angles, memo) @ pose
    return memo[key]


def moving_joints(joints, link):
    names = []
    seen = set()
    while link in joints and link not in seen:
        seen.add(link)
        parent, _xyz, _rpy, _axis, jname = joints[link]
        if jname in HIP_JOINTS:
            names.append(jname)
        link = parent
    return names


def sample_angles(limits, joint_names):
    if not joint_names:
        return [{}]
    grids = []
    for name in joint_names:
        lo, hi = limits[name]
        kind = "pitch" if name.endswith("pitch") else "roll" if name.endswith("roll") else "yaw"
        count = SAMPLES[kind]
        grids.append((name, np.linspace(lo, hi, count)))
    rows = [{}]
    for name, values in grids:
        rows = [{**old, name: float(v)} for old in rows for v in values]
    return rows


def in_body(bmin, bmax):
    """The keep-out has to sit in the body cavity, not outside the shells.

    The cavity bounds are the inner faces read off the print shells:
    body_back ends near x -95, body_front starts near x 47, the middle
    shells span y -55 to 55. CAD check only.
    """
    return (
        bmin[0] >= -95.0 and bmax[0] <= 47.0
        and bmin[1] >= -52.0 and bmax[1] <= 52.0
        and bmin[2] >= -98.0 and bmax[2] <= 40.0
    )


def swept_points(joints, limits, visuals, step):
    """Union of servo vertices over the hip samples, in the print frame, mm."""
    groups = {}
    fixed = []
    for lname, fn, verts, local in visuals:
        depends = moving_joints(joints, lname)
        hip = [n for n in depends if n in HIP_JOINTS]
        if not hip:
            fixed.append((lname, fn, verts, local))
        else:
            # One side's joints do not move the other side.
            key = tuple(sorted(hip))
            groups.setdefault(key, []).append((lname, fn, verts, local))
    clouds = []
    labels = []
    memo = {}
    for lname, fn, verts, local in fixed:
        use = verts[::step]
        full = chain(joints, lname, {}, memo) @ local
        pts = (full[:3, :3] @ use.T).T + full[:3, 3]
        pts = pts * 1000.0 + SHIFT
        clouds.append(pts)
        labels.append("fixed %s %s" % (lname, fn))
    for key, items in groups.items():
        for angles in sample_angles(limits, list(key)):
            memo = {}
            for lname, fn, verts, local in items:
                use = verts[::step]
                full = chain(joints, lname, angles, memo) @ local
                pts = (full[:3, :3] @ use.T).T + full[:3, 3]
                pts = pts * 1000.0 + SHIFT
                # Keep vertices that can reach the body cavity.
                keep = (
                    (pts[:, 0] > -160.0) & (pts[:, 0] < 80.0)
                    & (pts[:, 1] > -80.0) & (pts[:, 1] < 80.0)
                    & (pts[:, 2] > -120.0) & (pts[:, 2] < 70.0)
                )
                if keep.any():
                    clouds.append(pts[keep])
                    labels.append("%s %s %s" % (lname, fn, _short(angles)))
    stacked = np.vstack(clouds)
    return stacked, labels


def _short(angles):
    return ",".join("%s=%.2f" % (k.replace("_hip", ""), v) for k, v in sorted(angles.items()))


def hash_points(points, cell=8.0):
    keys = np.floor(points / cell).astype(int)
    buckets = {}
    for i, key in enumerate(map(tuple, keys)):
        buckets.setdefault(key, []).append(i)
    packed = {k: points[v] for k, v in buckets.items()}
    return packed, cell


def servo_gap(packed, cell, bmin, bmax):
    lo = np.floor((bmin - 2.0) / cell).astype(int)
    hi = np.floor((bmax + 2.0) / cell).astype(int)
    chunks = []
    for ix in range(lo[0], hi[0] + 1):
        for iy in range(lo[1], hi[1] + 1):
            for iz in range(lo[2], hi[2] + 1):
                chunk = packed.get((ix, iy, iz))
                if chunk is not None:
                    chunks.append(chunk)
    if not chunks:
        return 99.0
    return float(seat.point_box_distance(np.vstack(chunks), bmin, bmax).min())


def orientations():
    """Axis-aligned keep-out boxes. Stack is plate plus the cooler.

    Active stack is 12.70 mm cooler plus 2.4 mm plate (CAD check only).
    Passive stack uses the ED-Pi5PCOOLER height, 9.3 mm, plus the same plate.
    That sink's outline is 65 by 58 mm, so the in-plane keep-out grows to
    85 by 58 mm.
    """
    rows = []
    specs = (
        ("active", 85.0, 56.0, seat.COOLER_H + seat.PLATE_T),
        ("passive", 85.0, 58.0, 9.3 + seat.PLATE_T),
    )
    for name, length, width, stack in specs:
        dims = { (length, width, stack), (width, length, stack),
                 (length, stack, width), (width, stack, length),
                 (stack, length, width), (stack, width, length) }
        for sx, sy, sz in sorted(dims):
            rows.append({
                "cooler": name,
                "size_mm": [round(sx, 2), round(sy, 2), round(sz, 2)],
            })
    return rows


def search(shells, packed, cell):
    best = None
    nearest = None
    tried = 0
    for orient in orientations():
        sx, sy, sz = orient["size_mm"]
        for x in np.arange(-130.0, 55.0 - sx, 8.0):
            for y in np.arange(-48.0, 48.0 - sy, 6.0):
                for z in np.arange(-96.0, 36.0 - sz, 8.0):
                    tried += 1
                    origin = np.array([x, y, z], dtype=float)
                    bmin = origin
                    bmax = origin + np.array([sx, sy, sz])
                    if not in_body(bmin, bmax):
                        continue
                    gap = servo_gap(packed, cell, bmin, bmax)
                    if nearest is None or gap > nearest["servo_mm"]:
                        nearest = {
                            "servo_mm": round(gap, 2),
                            "origin_mm": [round(v, 2) for v in origin],
                            "size_mm": orient["size_mm"],
                            "cooler": orient["cooler"],
                        }
                    if gap < seat.CLEAR_MM:
                        continue
                    total, _detail = seat.overlaps(shells, BODY, bmin, bmax)
                    if total:
                        continue
                    shell = seat.clearance(shells, BODY, bmin, bmax, limit=6.0)
                    if shell < seat.CLEAR_MM:
                        continue
                    # Further forward first, then the tighter of the two gaps.
                    score = (float(x + sx), min(gap, shell))
                    row = {
                        "cooler": orient["cooler"],
                        "origin_mm": [round(float(v), 2) for v in origin],
                        "size_mm": orient["size_mm"],
                        "servo_mm": round(gap, 2),
                        "shell_mm": shell,
                        "score": score,
                    }
                    if best is None or score > best["score"]:
                        best = row
                        print("hit", row, flush=True)
    return best, nearest, tried


def verify(joints, limits, visuals, origin, size):
    """Full-vertex minimum over the hip samples. CAD check only."""
    bmin = np.array(origin, dtype=float)
    bmax = bmin + np.array(size, dtype=float)
    groups = {}
    fixed = []
    for lname, fn, verts, local in visuals:
        hip = [n for n in moving_joints(joints, lname) if n in HIP_JOINTS]
        if hip:
            groups.setdefault(tuple(sorted(hip)), []).append((lname, fn, verts, local))
        else:
            fixed.append((lname, fn, verts, local))
    worst = {"mm": 99.0, "who": "none", "angles": {}}
    memo = {}
    for lname, fn, verts, local in fixed:
        full = chain(joints, lname, {}, memo) @ local
        pts = (full[:3, :3] @ verts.T).T + full[:3, 3]
        pts = pts * 1000.0 + SHIFT
        gap = float(seat.point_box_distance(pts, bmin, bmax).min())
        if gap < worst["mm"]:
            worst = {"mm": round(gap, 2), "who": "%s %s" % (lname, fn), "angles": {}}
    for key, items in groups.items():
        for angles in sample_angles(limits, list(key)):
            memo = {}
            for lname, fn, verts, local in items:
                full = chain(joints, lname, angles, memo) @ local
                pts = (full[:3, :3] @ verts.T).T + full[:3, 3]
                pts = pts * 1000.0 + SHIFT
                near = np.all(pts > bmin - 25.0, axis=1) & np.all(pts < bmax + 25.0, axis=1)
                if not near.any():
                    continue
                gap = float(seat.point_box_distance(pts[near], bmin, bmax).min())
                if gap < worst["mm"]:
                    worst = {
                        "mm": round(gap, 2),
                        "who": "%s %s" % (lname, fn),
                        "angles_rad": {k: round(v, 3) for k, v in angles.items()},
                    }
    return worst


def shell_report(shells, bmin, bmax):
    detail = {}
    for name in BODY:
        detail[name] = seat.clearance(shells, (name,), bmin, bmax, limit=8.0)
    return detail


def refine(shells, packed, cell, centre, size, cooler):
    """2 mm grid around a hit. Keeps the further-forward pose, then the gap."""
    sx, sy, sz = size
    best = None
    cx, cy, cz = centre
    for x in np.arange(cx - 12.0, cx + 12.1, 2.0):
        for y in np.arange(cy - 12.0, cy + 12.1, 2.0):
            for z in np.arange(cz - 12.0, cz + 12.1, 2.0):
                origin = np.array([x, y, z], dtype=float)
                bmin = origin
                bmax = origin + np.array([sx, sy, sz])
                if not in_body(bmin, bmax):
                    continue
                gap = servo_gap(packed, cell, bmin, bmax)
                if gap < seat.CLEAR_MM:
                    continue
                total, _ = seat.overlaps(shells, BODY, bmin, bmax)
                if total:
                    continue
                shell = seat.clearance(shells, BODY, bmin, bmax, limit=8.0)
                if shell < seat.CLEAR_MM:
                    continue
                score = (float(x + sx), min(gap, shell))
                row = {
                    "cooler": cooler,
                    "origin_mm": [round(float(v), 2) for v in origin],
                    "size_mm": [sx, sy, sz],
                    "servo_mm": round(gap, 2),
                    "shell_mm": shell,
                    "shells": shell_report(shells, bmin, bmax),
                    "score": score,
                }
                if best is None or score > best["score"]:
                    best = row
    return best


def main():
    joints, limits, visuals = load_model()
    points, labels = swept_points(joints, limits, visuals, step=8)
    print("swept vertices", len(points), "groups", len(labels), flush=True)
    packed, cell = hash_points(points)
    shells = seat.load_shells()
    best, nearest, tried = search(shells, packed, cell)
    refined = None
    if best is not None:
        refined = refine(
            shells, packed, cell, best["origin_mm"], best["size_mm"], best["cooler"])
        print("refined", refined, flush=True)
        if refined is not None:
            best = refined
    checked = None
    if best is not None:
        checked = verify(joints, limits, visuals, best["origin_mm"], best["size_mm"])
        print("dense", checked, flush=True)
    report = {
        "label": "CAD check only",
        "tried": tried,
        "swept_vertices": int(len(points)),
        "hip_samples": SAMPLES,
        "best": best,
        "dense_servo": checked,
        "largest_servo_gap": nearest,
    }
    path = os.path.join(HERE, "pose_search.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
