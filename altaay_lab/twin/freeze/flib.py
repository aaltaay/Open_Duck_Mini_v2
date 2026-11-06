"""Shared helpers for altaay_lab/twin/freeze (the V1 pre-freeze pass, 2026-11-06 ET). CAD check only.

Frames: URDF world at the zero pose, mm, x forward, y left, z up (the frame of cables3d, the viewer and complete3d).
The print/ STLs keep their own part frame; the scene (cables3d/c3d_lib.Scene) gives each instance its world transform.
"""
import json
import os
import sys

import numpy as np
import trimesh
import manifold3d

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(LAB)
PRINT = os.path.join(REPO, "print")
sys.path.insert(0, os.path.join(LAB, "twin", "complete3d"))
from common import scene, inst_world, head_instances, inst_name   # noqa: E402,F401

FASTENERS = os.path.join(LAB, "fasteners", "fasteners.json")
CABLES3D = os.path.join(LAB, "cables3d", "cables3d.json")
PLACEMENTS = os.path.join(LAB, "audit", "placements.json")


BASE_REV = "1473799"        # altaay-lab before the freeze pass


def base_mesh(rel):
    """a repo STL as it was before the freeze (git rev BASE_REV), so every freeze script starts from the same input"""
    import subprocess
    import tempfile
    blob = subprocess.run(["git", "-C", LAB, "show", "%s:%s" % (BASE_REV, rel)], check=True, capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".stl") as fh:
        fh.write(blob)
        fh.flush()
        return trimesh.load(fh.name, force="mesh")


def r(x, n=2):
    return None if x is None else round(float(x), n)


def to_man(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                               tri_verts=np.asarray(m.faces, np.uint32)))


def from_man(M):
    mo = M.to_mesh()
    return trimesh.Trimesh(np.asarray(mo.vert_properties, float)[:, :3], np.asarray(mo.tri_verts), process=False)


def cyl(a, b, rad, sections=48):
    """solid cylinder from point a to point b"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    c = trimesh.creation.cylinder(radius=rad, height=float(np.linalg.norm(b - a)), sections=sections)
    z = (b - a) / np.linalg.norm(b - a)
    T = trimesh.geometry.align_vectors([0, 0, 1], z)
    T[:3, 3] = (a + b) / 2
    c.apply_transform(T)
    return c


def frame_from_axis(ax, up=(0, 0, 1)):
    """unit axis plus two unit vectors across it (u horizontal where possible)"""
    ax = np.asarray(ax, float) / np.linalg.norm(ax)
    u = np.cross(ax, up)
    if np.linalg.norm(u) < 1e-6:
        u = np.cross(ax, [1, 0, 0])
    u /= np.linalg.norm(u)
    return ax, u, np.cross(ax, u)


def first_hit(mesh, o, d):
    loc, _, _ = mesh.ray.intersects_location([o], [d])
    if not len(loc):
        return np.inf
    t = (loc - np.asarray(o)) @ np.asarray(d)
    t = t[t > 1e-6]
    return float(t.min()) if len(t) else np.inf


def hits_along(mesh, o, d):
    loc, _, _ = mesh.ray.intersects_location([o], [d])
    if not len(loc):
        return []
    return sorted(float(x) for x in (loc - np.asarray(o)) @ np.asarray(d))


def head_inst(S):
    return [i for i in head_instances(S) if inst_name(i).startswith("head[")][0]


def inst_by_key(S, key):
    return [i for i in S.inst if i["key"] == key]


def speaker_frame():
    """speaker axis (out of the cone toward the right side wall), centre of the 4 interface screw seats, and the two
    across-axis unit vectors, from fasteners.json F352 to F355 (the 32 x 32 mm square on the interface plate)"""
    F = {f["id"]: f for f in json.load(open(FASTENERS))["fasteners"]}
    ax = -np.array(F["F353"]["axis_world"], float)
    c = np.array([F[k]["seat_world"] for k in ("F352", "F353", "F354", "F355")], float).mean(0)
    ax, u, v = frame_from_axis(ax)
    return c, ax, u, v, F


def surface_cloud(m, n=20000, seed=1):
    p, _ = trimesh.sample.sample_surface(m, n, seed=seed)
    return np.asarray(p)


def box_mesh(center, R, dims):
    b = trimesh.creation.box(extents=dims)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = center
    b.apply_transform(T)
    return b


def placements():
    return {p["id"]: p for p in json.load(open(PLACEMENTS))}


def placement_box(p):
    """world box of a placements.json row (axis aligned, dims_xyz_mm)"""
    return box_mesh(p["center_mm"], np.eye(3), p["dims_xyz_mm"])


def dump(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")
