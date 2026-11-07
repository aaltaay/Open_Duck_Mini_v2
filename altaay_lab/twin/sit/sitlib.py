"""Shared code for altaay_lab/twin/sit (the A1b alert sit, D59). CAD check only, calc only.

Frames: URDF world at the zero pose, mm, x forward, y left, z up (cables3d/c3d_lib.Scene, the viewer, complete3d).
The print/ STLs keep their own part frame; the scene gives each instance its world transform. The left leg is built and
the right leg parts are the y mirror of the left ones in the part frame (the stock left and right cache and roll_to_pitch
are exact y mirrors: 0.00 mm, checked by sit_cad.py).

Inputs are read from the repo on every run (never from a cache): robot.urdf, print/*.stl, the URDF mesh copies. The CAD
builder (sit_cad.py) starts every edited part from the STL of BASE_REV, so a re-run gives the same file.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import trimesh
import manifold3d

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.dirname(HERE)
LAB = os.path.dirname(TWIN)
REPO = os.path.dirname(LAB)
PRINT = os.path.join(REPO, "print")
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
URDF = os.path.join(URDF_DIR, "robot.urdf")
sys.path.insert(0, os.path.join(LAB, "cables3d"))
import c3d_lib  # noqa: E402

BASE_REV = "d6179ae"          # altaay-lab before the sit job (PR 27 merged)
D = np.radians

# ---------------------------------------------------------------------------------------------------------------
# The joint stops of the A1b sit (D59). Left side, degrees; the right side mirrors hip roll and hip pitch (URDF signs).
# 'stop' is the hard stop the part touches; the software limit is 3 deg inside every hard stop (servo.py).
# Sources: SIT_DESIGN.md (v1) changes 1 to 3 and 5, SIT_V2.md (A1b) changes 1 and 2; the angles are the approved ones.
# ---------------------------------------------------------------------------------------------------------------
STOPS = {
    "knee_fold": dict(joint="left_knee", stop=150.0, side="hi", kind="TPU knee bumper on the shin spacer, onto the thigh"),
    "ankle_sit": dict(joint="left_ankle", stop=-95.0, side="lo", kind="TPU pad on foot_top under the shin end"),
    "hip_roll_out": dict(joint="left_hip_roll", stop=-8.0, side="lo", kind="printed lug on roll_to_pitch onto roll_motor_bottom"),
    "hip_pitch_back": dict(joint="left_hip_pitch", stop=-75.0, side="lo", kind="TPU face on the thigh cover top onto roll_to_pitch"),
    "neck_back": dict(joint="neck_pitch", stop=25.0, side="hi", kind="printed lug on the neck sheets onto the trunk top"),
    "head_fwd": dict(joint="head_pitch", stop=-25.0, side="lo", kind="printed lug on head_pitch_to_yaw onto the neck"),
}
SOFT_MARGIN_DEG = 3.0          # software commands stay this far inside every hard stop (D59)
JOG = 9.0                      # shin sheet joggle, mm away from the leg centre plane (SIT_DESIGN change 1)
R_HORN = 16.0                  # the joggle starts this far from the knee axis (SIT_DESIGN change 1)
SPACER_GROW = 18.0             # the shin spacer is this much longer (2 x JOG)

# A1b sit and stand path (SIT_V2.md 3.2), left (hip pitch, knee, ankle, neck, head) in degrees, and what the software
# commands with the 3 deg rule (servo.py): the head forward waypoint is clamped to the software limits.
PATH_A1B = [(-15, 5, 0, 0, 0), (-21, 40, -29, -22, -25), (-33, 75, -49, -22, -25), (-54, 110, -67, -22, -25),
            (-58, 130, -82, -22, -25), (-60, 147, -92, -22, -25), (-60, 147, -92, 25, -25)]
SIT_TARGET = (-60, 147, -92, 25, -25)


# ---------------------------------------------------------------------------------------------------------------
# scene and meshes
# ---------------------------------------------------------------------------------------------------------------
_S = None


def scene(fresh=False):
    """robot.urdf at the zero pose with the print/ STLs of the working tree (read now, not cached across runs)"""
    global _S
    if _S is None or fresh:
        _S = c3d_lib.Scene()
    return _S


def inst(S, link, key):
    r = [i for i in S.inst if i["link"] == link and i["key"] == key]
    if len(r) != 1:
        raise KeyError("%s %s: %d instances" % (link, key, len(r)))
    return r[0]


def inst_world(S, i):
    return S.T0[i["link"]] @ i["T"]


def git_blob(rel, rev=BASE_REV):
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, rel)], check=True, capture_output=True).stdout


def base_mesh(rel, rev=BASE_REV):
    """a repo STL as it is at rev (the input of every builder)"""
    with tempfile.NamedTemporaryFile(suffix=".stl") as fh:
        fh.write(git_blob(rel, rev))
        fh.flush()
        return trimesh.load(fh.name, force="mesh")


def to_man(m):
    m = m if isinstance(m, trimesh.Trimesh) else trimesh.Trimesh(*m)
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                               tri_verts=np.asarray(m.faces, np.uint32)))


def from_man(M):
    mo = M.to_mesh()
    return trimesh.Trimesh(np.asarray(mo.vert_properties, float)[:, :3], np.asarray(mo.tri_verts), process=False)


def xform(M, T):
    """manifold transformed by a 4x4"""
    return M.transform(np.asarray(T, float)[:3, :4])


def cyl(a, b, rad, sections=64):
    a, b = np.asarray(a, float), np.asarray(b, float)
    c = trimesh.creation.cylinder(radius=rad, height=float(np.linalg.norm(b - a)), sections=sections)
    z = (b - a) / np.linalg.norm(b - a)
    T = trimesh.geometry.align_vectors([0, 0, 1], z)
    T[:3, 3] = (a + b) / 2
    c.apply_transform(T)
    return c


def box(lo, hi, T=None):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    b = trimesh.creation.box(extents=hi - lo)
    b.apply_translation((lo + hi) / 2)
    if T is not None:
        b.apply_transform(T)
    return b


def mirror_y_part(m):
    """the y mirror in the part frame (right part from the left part), normals kept outward"""
    r = m.copy()
    r.apply_transform(np.diag([1.0, -1.0, 1.0, 1.0]))
    r.invert()
    return r


def mesh_ok(m):
    return dict(watertight=bool(m.is_watertight), volume_mm3=round(float(m.volume), 1), faces=int(len(m.faces)),
                euler=int(m.euler_number))


def rel_T(S, cfg, moving, fixed):
    """transform of the moving link's zero-pose world points into the fixed link's zero-pose world frame at cfg"""
    Tl = S.link_T(cfg)
    return S.T0[fixed] @ np.linalg.inv(Tl[fixed]) @ Tl[moving] @ np.linalg.inv(S.T0[moving])


def cfg_left(h=0.0, k=0.0, a=0.0, roll=0.0, yaw=0.0, neck=None, head=None, both=True):
    """joint config dict in radians from left-side degrees; both=True mirrors onto the right leg (URDF signs)"""
    c = {"left_hip_pitch": D(h), "left_knee": D(k), "left_ankle": D(a), "left_hip_roll": D(roll), "left_hip_yaw": D(yaw)}
    if both:
        c.update({"right_hip_pitch": -D(h), "right_knee": D(k), "right_ankle": D(a), "right_hip_roll": -D(roll),
                  "right_hip_yaw": -D(yaw)})
    if neck is not None:
        c["neck_pitch"] = D(neck)
    if head is not None:
        c["head_pitch"] = D(head)
    return c


def r(x, n=2):
    return None if x is None else round(float(x), n)


def dump(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")


# ---------------------------------------------------------------------------------------------------------------
# swept volumes and clearance cuts
# ---------------------------------------------------------------------------------------------------------------
_DIRS = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]] +
                 [[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
_DIRS = _DIRS / np.linalg.norm(_DIRS, axis=1)[:, None]


def union(ms):
    ms = [m for m in ms if not m.is_empty()]
    if not ms:
        return manifold3d.Manifold()
    return manifold3d.Manifold.batch_boolean(ms, manifold3d.OpType.Add)


def dilate(M, c):
    """M grown by about c in every direction: the union of M moved c along 14 directions (the 6 axes and the 8
    diagonals); every point within 0.82 c of M is covered"""
    if c <= 0:
        return M
    return union([M] + [M.translate(tuple(c * d)) for d in _DIRS])


def swept(M, Ts):
    """union of M placed by each 4x4 in Ts"""
    return union([xform(M, T) for T in Ts])


def finalize(M, tol=1e-3):
    """remove slivers that would pinch on an STL round trip (float32 vertices): simplify with a growing tolerance until
    the STL round trip is watertight; returns a trimesh (raises if no tolerance up to 0.05 mm works)"""
    M = solid(M)
    for t in (tol, 3e-3, 1e-2, 2e-2, 5e-2):
        m = from_man(M.simplify(t))
        if stl_roundtrip_ok(m)[0]:
            return m
    raise RuntimeError("no clean STL within a 0.05 mm simplify tolerance")


def solid(M, min_vol=1.0):
    """the components of M above min_vol mm3 (drops the zero-volume slivers a boolean leaves on a cut surface)"""
    comps = [c for c in M.decompose() if c.volume() > min_vol]
    return union(comps)


def man_to_arrays(M):
    g = M.to_mesh64()
    return np.asarray(g.vert_properties, float)[:, :3].copy(), np.asarray(g.tri_verts, np.int64).copy()


def man_from_arrays(a):
    V, F = a
    return manifold3d.Manifold(manifold3d.Mesh64(vert_properties=np.asarray(V, float), tri_verts=np.asarray(F, np.uint64)))


def stl_roundtrip_ok(m):
    with tempfile.NamedTemporaryFile(suffix=".stl") as fh:
        m.export(fh.name)
        t = trimesh.load(fh.name, force="mesh")
    return bool(t.is_watertight), float(t.volume)


# convex pieces, swept hulls: the cut volumes (a part is cut by everything that moves past it, grown by a clearance)
_ICO = None


def _ico():
    """the 12 vertices of an icosahedron whose inscribed sphere has radius 1 (a dilation by it covers a ball)"""
    global _ICO
    if _ICO is None:
        s = trimesh.creation.icosphere(subdivisions=0)
        v = np.asarray(s.vertices, float)
        v /= np.linalg.norm(v, axis=1)[:, None]
        inr = float(np.min(np.abs(np.einsum("ij,ij->i", s.face_normals, v[s.faces[:, 0]]))))
        _ICO = v / inr
    return _ICO


def _hull_vertices(P):
    from scipy.spatial import ConvexHull
    P = np.asarray(P, float)
    if len(P) < 5:
        return P
    try:
        return P[ConvexHull(P).vertices]
    except Exception:
        return P


def convex_pieces(m, slab=6.0, axis=2):
    """a mesh cut into slabs along an axis, each replaced by its convex hull (a cover of the part: holes and pockets are
    filled, so a cut made with it clears the outside of the part with margin). Returns the hull vertex sets."""
    M = to_man(m) if isinstance(m, trimesh.Trimesh) else m
    lo, hi = M.bounding_box()[axis], M.bounding_box()[axis + 3]
    out = []
    edges = np.arange(lo, hi + slab, slab)
    for a, b in zip(edges[:-1], edges[1:]):
        lo3 = [-1e4] * 3
        hi3 = [1e4] * 3
        lo3[axis], hi3[axis] = a - 0.01, b + 0.01
        piece = M ^ to_man(box(lo3, hi3))
        if piece.volume() < 1e-3:
            continue
        for comp in piece.decompose():
            if comp.volume() > 1e-3:
                out.append(_hull_vertices(np.asarray(comp.to_mesh().vert_properties, float)[:, :3]))
    return out


def hull_pts(P):
    return manifold3d.Manifold.hull_points(np.asarray(P, float))


def swept_cut(pieces, Ts, clearance, cells=None, near=None):
    """union over consecutive transforms (or over cells of transforms) of the convex hull of each piece at those poses,
    grown by clearance (a circumscribed icosahedron, so every point within clearance is covered). near: (lo, hi) box; hulls
    that miss it are skipped (they cannot cut a part inside it)"""
    D_ = _ico() * clearance if clearance > 0 else np.zeros((1, 3))
    groups = cells if cells is not None else ([(Ts[i], Ts[i + 1]) for i in range(len(Ts) - 1)] or [(Ts[0],)])
    out = []
    for P in pieces:
        Ph = np.c_[P, np.ones(len(P))]
        posed = {}
        for g in groups:
            Q = []
            for T in g:
                k = id(T)
                if k not in posed:
                    posed[k] = (Ph @ np.asarray(T).T)[:, :3]
                Q.append(posed[k])
            Q = np.vstack(Q)
            if near is not None:
                lo, hi = Q.min(0) - clearance, Q.max(0) + clearance
                if np.any(hi < near[0]) or np.any(lo > near[1]):
                    continue
            if clearance > 0:
                Q = (Q[:, None, :] + D_[None, :, :]).reshape(-1, 3)
            out.append(hull_pts(Q))
    return union(out)


def bbox_of(M, pad=0.0):
    b = np.asarray(M.bounding_box(), float)
    return b[:3] - pad, b[3:] + pad
