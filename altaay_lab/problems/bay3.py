#!/usr/bin/env python3
"""CAD check: three P45B cells in the grown bay. Does not edit print/body_back.stl.

The two cells stay on the axes in twin/battery/BAY.md. The third sits behind them,
one sleeve diameter back, and the shell grows a 2.5 mm blister so the cut does not
open a hole. Screws are not moved. The mesh copy is written outside the repo.

CAD check only.
"""
import json
import os
import sys

import numpy as np
import trimesh
import manifold3d

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
OUT = os.environ.get("BAY3_OUT", os.path.join(__import__("tempfile").gettempdir(), "bay3"))
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(LAB, "fasteners"))
from fastlib import Scene  # noqa: E402

# Existing sleeve axes and the cut radius, from twin/battery/bay_edit.py.
XC = -133.1
YC = (-9.35, 12.2)
RC = 11.35
RP = 11.1
Z = (-4.5, 67.5)
PITCH = 22.2  # sleeve diameter, the same 22.2 mm circles as the two-cell pack
WALL = 2.5


def man(m):
    return manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(m.vertices, np.float32),
        tri_verts=np.asarray(m.faces, np.uint32)))


def tm(M):
    g = M.to_mesh()
    return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts, process=True)


def cyl(x, y, r, z=Z):
    h = z[1] - z[0]
    return trimesh.creation.cylinder(
        radius=r, height=h, sections=96,
        transform=trimesh.transformations.translation_matrix((x, y, (z[0] + z[1]) / 2)),
    )


def main():
    S = Scene(os.path.join(OUT, "scene"))
    k = [i["idx"] for i in S.inst if i["key"] == "body_back"][0]
    src = S.mesh(k)
    y_mid = (YC[0] + YC[1]) / 2
    half = abs(YC[1] - YC[0]) / 2
    dx = float(np.sqrt(PITCH ** 2 - half ** 2))
    x3 = XC - dx
    y3 = y_mid
    inner = man(cyl(x3, y3, RC))
    # tunnel into the existing pocket so the rear cell is one cavity, not a closed hole
    tunnel = man(trimesh.creation.box(
        extents=(dx, 2 * RC, Z[1] - Z[0]),
        transform=trimesh.transformations.translation_matrix((XC - dx / 2, y3, (Z[0] + Z[1]) / 2)),
    ))
    outer = man(cyl(x3, y3, RC + WALL))
    edited = man(src) + outer - inner - tunnel
    mesh = tm(edited)
    mesh.export(os.path.join(OUT, "body_back_3s.stl"))

    def overlap(a, b):
        return round(float((a ^ b).volume()), 2)

    sleeves = {
        "left": (XC, YC[0]),
        "right": (XC, YC[1]),
        "rear": (x3, y3),
    }
    pack_ov = {name: overlap(man(cyl(x, y, RP, z=(-4.0, 67.0))), man(mesh)) for name, (x, y) in sleeves.items()}
    before = man(src)
    others = {}
    for i in S.inst:
        if i["key"] in ("body_back", "holder", "cell", "battery"):
            continue
        m = S.mesh(i["idx"])
        if m.bounds[1][0] < x3 - 30 or m.bounds[0][0] > -100:
            continue
        mm = man(m)
        after_v = overlap(man(mesh), mm)
        before_v = overlap(before, mm)
        if after_v > before_v + 0.05:
            others[i["key"]] = dict(before_mm3=before_v, after_mm3=after_v)
    F = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))["fasteners"]
    near = []
    for f in F:
        sw = np.array(f["seat_world"], float)
        d = float(np.hypot(sw[0] - x3, sw[1] - y3))
        if d < 30 and Z[0] - 10 < sw[2] < Z[1] + 10:
            near.append(dict(id=f["id"], spec=f.get("spec"), dist_mm=round(d, 2)))
    # ray out the back of the blister
    rmi = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
    origin = np.array([x3 - RC, y3, 31.5])
    loc, _, _ = rmi.intersects_location([origin], [np.array([-1.0, 0, 0])], multiple_hits=False)
    wall = None if len(loc) == 0 else round(float(np.linalg.norm(loc[0] - origin)), 2)
    rep = dict(
        label="CAD check only",
        rear_axis_mm=dict(x=round(x3, 2), y=round(y3, 2), z=list(Z)),
        pitch_mm=PITCH,
        wall_mm=WALL,
        dx_behind_front_axes_mm=round(dx, 2),
        watertight=bool(mesh.is_watertight),
        volume_before_mm3=round(float(src.volume), 1),
        volume_after_mm3=round(float(mesh.volume), 1),
        back_before_mm=round(float(src.bounds[0][0]), 2),
        back_after_mm=round(float(mesh.bounds[0][0]), 2),
        protrusion_mm=round(float(src.bounds[0][0] - mesh.bounds[0][0]), 2),
        sleeve_overlap_mm3=pack_ov,
        other_part_overlap_mm3=others,
        fasteners_within_30mm=sorted(near, key=lambda r: r["dist_mm"]),
        back_wall_ray_mm=wall,
        mesh_outside_repo=os.path.join(OUT, "body_back_3s.stl"),
        print_stl_unchanged=True,
    )
    # the path above is a local scratch path; do not keep it in the committed json
    rep.pop("mesh_outside_repo")
    path = os.path.join(HERE, "bay3.json")
    json.dump(rep, open(path, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
