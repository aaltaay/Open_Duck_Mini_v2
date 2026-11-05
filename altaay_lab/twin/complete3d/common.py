"""Shared helpers for altaay_lab/twin/complete3d (V1 "everything in 3D", phase 1). CAD check only.

Frames: URDF world at the zero pose, mm, x forward, y left, z up (same as viewer/make_viewer_data.py).
Scene: cables3d/c3d_lib.Scene (robot.urdf at the zero pose with the print/ STLs and the head internals).
Viewer data: a base run of viewer/make_viewer_data.py (default /home/user/v1_out/3d/viewer_base), never inside the repo.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.dirname(HERE)
LAB = os.path.dirname(TWIN)
REPO = os.path.dirname(LAB)
sys.path.insert(0, os.path.join(LAB, "cables3d"))
import c3d_lib  # noqa: E402

OUT = os.environ.get("C3D_OUT", "/home/user/v1_out/3d")
VIEWER_BASE = os.environ.get("C3D_VIEWER", os.path.join(OUT, "viewer_base"))
CABLES3D = os.path.join(LAB, "cables3d", "cables3d.json")
FASTENERS = os.path.join(LAB, "fasteners", "fasteners.json")
HEAD_LINK = "head_assembly"

# glTF root of make_viewer_data.py: URDF z-up mm -> glTF y-up m. Inverse: x_u = x_g, y_u = -z_g, z_u = y_g, x1000.
GL_TO_URDF = np.array([[1000.0, 0, 0, 0], [0, 0, -1000.0, 0], [0, 1000.0, 0, 0], [0, 0, 0, 1.0]])

_S = None


def scene():
    global _S
    if _S is None:
        _S = c3d_lib.Scene()
    return _S


def inst_world(S, i):
    return S.T0[i["link"]] @ i["T"]


def head_instances(S):
    return [i for i in S.inst if i["link"] == HEAD_LINK]


def inst_name(i):
    return "%s[%d]" % (i["key"], i["idx"])


def glb_meshes(names=None, prefix=None, path=None):
    """viewer GLB nodes as world meshes in URDF mm (zero pose, explode 0)"""
    path = path or os.path.join(VIEWER_BASE, "duck.glb")
    sc = trimesh.load(path, force="scene")
    out = {}
    for name in sc.graph.nodes_geometry:
        if names is not None and name not in names:
            continue
        if prefix is not None and not name.startswith(prefix):
            continue
        T, g = sc.graph.get(name)
        m = sc.geometry[g].copy()
        m.apply_transform(GL_TO_URDF @ T)
        out[name] = m
    return out


def first_hits(mesh, origins, dirs, skip=1e-6):
    """distance to the first hit along each ray (inf if none)"""
    origins = np.atleast_2d(np.asarray(origins, float))
    dirs = np.atleast_2d(np.asarray(dirs, float))
    if len(dirs) == 1 and len(origins) > 1:
        dirs = np.repeat(dirs, len(origins), 0)
    loc, ri, _ = mesh.ray.intersects_location(origins, dirs, multiple_hits=True)
    d = np.full(len(origins), np.inf)
    if len(ri):
        t = np.einsum("ij,ij->i", loc - origins[ri], dirs[ri])
        for r, tt in zip(ri, t):
            if skip < tt < d[r]:
                d[r] = tt
    return d


def all_hits(mesh, origin, direction):
    loc, ri, _ = mesh.ray.intersects_location(np.atleast_2d(origin), np.atleast_2d(direction), multiple_hits=True)
    if not len(ri):
        return np.array([])
    t = (loc - np.asarray(origin)) @ np.asarray(direction)
    return np.sort(t[t > 1e-6])


def perp_basis(a):
    a = np.asarray(a, float) / np.linalg.norm(a)
    h = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(a, h)
    u /= np.linalg.norm(u)
    return u, np.cross(a, u)


def box(center, R, dims):
    """oriented box mesh: R columns are the world directions of dims[0], dims[1], dims[2]"""
    m = trimesh.creation.box(extents=dims)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = center
    m.apply_transform(T)
    return m


def r(x, n=2):
    if isinstance(x, dict):
        return {k: r(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [r(v, n) for v in x]
    if isinstance(x, np.ndarray):
        return r(x.tolist(), n)
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), n)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def write_json(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(r(obj), f, indent=1)
        f.write("\n")
    os.replace(tmp, path)
