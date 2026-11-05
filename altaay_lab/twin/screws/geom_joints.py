"""Geometry of the screw joints outside the servo chain, in the URDF world frame (CAD check only).

Uses the lab scene (altaay_lab/fasteners/fastlib.py Scene: robot.urdf at zero joint angles, print/ STLs swapped in,
head internals on the head.stl transform), read only. For each candidate joint (screw head part -> mating part):
  - the screws (ids, seats, axis), the frame check (seat to the part surface, mm);
  - the contact area between the two parts, split by the contact face normal against the screw axis:
    axial (|n.a| > 0.7: carries push along the screw), lateral (|n.a| < 0.3: a lip or wall that carries
    shear by bearing), and the lateral area per side (+u, -u, +v, -v) so a one-sided ledge is not
    taken for a capture;
  - the centre of mass of the screw head part (uniform density), for the screw choice rule.
Writes data/geom_joints.json. Peak about 0.5 GB (wrap with ramcap.py).
"""
import json, os, sys, collections
import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(LAB, "fasteners"))
from fastlib import Scene  # noqa: E402  (read-only reuse)

SCRATCH = "/home/user/v1_out/screws/scene"
CANDIDATES = {("body_front", "body_middle_top"), ("body_front", "body_middle_bottom"),
              ("body_back", "body_middle_top"), ("body_back", "body_middle_bottom"),
              ("body_middle_bottom", "trunk_bottom"), ("trunk_top", "trunk_bottom"),
              ("battery_pack_lid", "body_back"), ("head_bot_sheet", "head"), ("speaker_stand", "head"),
              ("speaker_interface", "speaker_stand"), ("head_roll_mount", "head"), ("raspberrypizerow", "head"),
              ("board", "trunk_top"), ("bno055", "trunk_top"), ("bulb", "right_eye"), ("bulb", "left_eye")}
PER_MM2, TOUCH = 4.0, 0.35


def basis(a):
    a = a / np.linalg.norm(a)
    t = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, t); u /= np.linalg.norm(u)
    return a, u, np.cross(a, u)


def main():
    S = Scene(SCRATCH)
    F = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))["fasteners"]
    groups = collections.OrderedDict()
    for x in F:
        if x["kind"] == "screw" and (x["part"], x["into"]) in CANDIDATES:
            groups.setdefault((x["part"], x["into"], x["part_inst"], x["into_inst"]), []).append(x)
    samples, out = {}, []
    for (part, into, pi, ii), rows in groups.items():
        mA, mB = S.mesh(pi), S.mesh(ii)
        seats = np.array([r["seat_world"] for r in rows], float)
        a, u, v = basis(np.array(rows[0]["axis_world"], float))
        _, dist, _ = trimesh.proximity.closest_point(mA, seats)
        for k, m in ((pi, mA), (ii, mB)):
            if k not in samples:
                n = int(max(4000, m.area * PER_MM2))
                p, fi = trimesh.sample.sample_surface_even(m, n, seed=1)
                samples[k] = (p, m.face_normals[fi], m.area / len(p))
        pA, nA, wA = samples[pi]
        dd, _ = cKDTree(samples[ii][0]).query(pA, distance_upper_bound=TOUCH)
        t = np.isfinite(dd)
        c = nA[t] @ a
        lat = np.abs(c) < 0.3
        side = {}
        for nm, e in (("+u", u), ("-u", -u), ("+v", v), ("-v", -v)):
            side[nm] = round(float(((nA[t] @ e) > 0.7).sum() * wA), 0)
        com = mA.center_mass if mA.is_volume else mA.centroid
        out.append(dict(part=part, into=into, part_inst=pi, into_inst=ii, n=len(rows), ids=[r["id"] for r in rows],
                        seats_world=seats.round(2).tolist(), axis_world=a.round(4).tolist(),
                        u=u.round(4).tolist(), v=v.round(4).tolist(),
                        seat_to_part_mm=round(float(dist.max()), 2),
                        contact_mm2=dict(total=round(float(t.sum() * wA), 0),
                                         axial=round(float((np.abs(c) > 0.7).sum() * wA), 0),
                                         lateral=round(float(lat.sum() * wA), 0), lateral_by_side=side),
                        part_com_world=np.round(com, 2).tolist(), part_volume_mm3=round(float(mA.volume), 0),
                        part_bounds_world=np.round(mA.bounds, 1).tolist(),
                        into_bounds_world=np.round(mB.bounds, 1).tolist(),
                        part_T=np.round(S.inst[pi]["T"], 6).tolist(), into_T=np.round(S.inst[ii]["T"], 6).tolist()))
        r = out[-1]
        print(part, "->", into, r["n"], "seat_d", r["seat_to_part_mm"], "axis", r["axis_world"], r["contact_mm2"])
    json.dump(out, open(os.path.join(HERE, "data", "geom_joints.json"), "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
