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
# 'stop' is the hard stop the part touches; the software limit is 3 deg inside every hard stop (servo_limits.py).
# Sources: SIT_DESIGN.md (v1) changes 1 to 3 and 5, SIT_V2.md (A1b) changes 1 and 2; the angles are the approved ones.
# ---------------------------------------------------------------------------------------------------------------
STOPS = {
    "knee_fold": dict(joint="left_knee", stop=150.0, side="hi", kind="TPU knee bumper on the shin spacer, onto the thigh"),
    "ankle_sit": dict(joint="left_ankle", stop=-95.0, side="lo", kind="TPU pad on foot_top under the shin end"),
    "hip_roll_out": dict(joint="left_hip_roll", stop=-8.0, side="lo", kind="printed lug on roll_to_pitch onto roll_motor_bottom"),
    "hip_pitch_back": dict(joint="left_hip_pitch", stop=-75.0, side="lo", kind="TPU face on the thigh cover top onto roll_to_pitch"),
    "neck_back": dict(joint="neck_pitch", stop=25.0, side="hi", kind="TPU faces on the printed neck stop block (trunk_top, F127 and F129) that the stock neck sheets' back edges meet"),
    "head_fwd": dict(joint="head_pitch", stop=-25.0, side="lo", kind="TPU face on the printed hook of head_pitch_to_yaw (left arm) that the left neck sheet's front edge meets"),
}

# Compliant stops (D59 review): each designed stop is modelled as the stack that takes the impact, a TPU face in series
# with printed parts, as a linear spring at the contact radius r: K = k_stack r^2 (N m/rad). The printed lugs, the
# spacer and the faces are taken as rigid next to the TPU (stiffer stack: a higher, conservative impact peak); a stop
# with no TPU face is the printed lug in compression, E A / h. sit_model.py writes K into the joint limit (solreflimit,
# solimplimit) of the MJCF; sit_stress.py checks every r here against the CAD (1 mm) and fails otherwise.
E_TPU = 26.0                  # MPa, TPU 95A, est (typical data sheet tensile modulus for 95A grades; not measured)
E_PLA = 3500.0                # MPa, printed PLA modulus, est (STRUCTURE_TWIN.md uses the Overture TDS strength)
STOP_DAMPRATIO = 0.1          # TPU 95A loss factor about 0.2 (est): a low damping ratio is the conservative peak
STOP_SOLIMP = (0.95, 0.95, 0.001, 0.5, 2.0)
STOP_STACK = {
    "knee_fold": dict(joints=("left_knee", "right_knee"), r_mm=24.1, pads=[(28.0, 14.0, 3.0, 1)]),
    "ankle_sit": dict(joints=("left_ankle", "right_ankle"), r_mm=34.5, pads=[(6.0, 7.5, 3.0, 2)]),
    "hip_roll_out": dict(joints=("left_hip_roll", "right_hip_roll"), r_mm=17.5, lug=dict(area_mm2=96.0, h_mm=6.0)),
    "hip_pitch_back": dict(joints=("left_hip_pitch", "right_hip_pitch"), r_mm=40.8, pads=[(22.0, 6.0, 1.5, 1)]),
    "neck_back": dict(joints=("neck_pitch",), r_mm=41.1, pads=[(10.0, 6.0, 3.0, 2)]),      # one face per sheet, in a pocket of the block (sit_cad.json pad_r_mm)
    "head_fwd": dict(joints=("head_pitch",), r_mm=29.3, pads=[(12.0, 6.1, 6.0, 1)]),       # one 6 mm face on the hook, half the stiffness of 3 mm (sit_cad.json pad_r_mm, pad_dims)
}


def stop_k_lin(st):
    """N/mm of a stop stack: TPU pads (n in parallel, E A / t), or the printed lug in compression"""
    if st.get("pads"):
        return sum(n * E_TPU * a * b / t for a, b, t, n in st["pads"])
    return E_PLA * st["lug"]["area_mm2"] / st["lug"]["h_mm"]


def stop_K(st):
    """N m/rad at the joint"""
    return stop_k_lin(st) * 1000.0 * (st["r_mm"] / 1000.0) ** 2

SOFT_MARGIN_DEG = 3.0          # software commands stay this far inside every hard stop (D59)
JOG = 9.0                      # shin sheet joggle, mm away from the leg centre plane (SIT_DESIGN change 1)
R_HORN = 16.0                  # the joggle starts this far from the knee axis (SIT_DESIGN change 1)
SPACER_GROW = 18.0             # the shin spacer is this much longer (2 x JOG)
# the new stuck-on parts in robot.urdf: one link each on a fixed joint (identity origin) to the link the part rides on,
# written after every upstream link (sit_urdf.py), so the upstream instance order stays (audit/assembly.json indices)
SIT_LINKS = {
    "left_knee_bumper": ("knee_and_ankle_assembly_2", "knee_bumper"),
    "right_knee_bumper": ("knee_and_ankle_assembly_4", "knee_bumper"),
    "left_ankle_pads": ("foot_assembly", "ankle_pad"),
    "right_ankle_pads": ("foot_assembly_2", "ankle_pad"),
    "left_hip_pad": ("left_roll_to_pitch_assembly", "hip_pad"),
    "right_hip_pad": ("right_roll_to_pitch_assembly", "hip_pad"),
    "sit_seat": ("trunk_assembly", "sit_seat"),
    "sit_bumper": ("trunk_assembly", "sit_bumper"),
    "neck_stop": ("trunk_assembly", "neck_stop"),
    "neck_pads": ("trunk_assembly", "neck_pad"),
    "head_pad": ("head_pitch_to_yaw", "head_pad"),
}
SIT_PARENT = {k: v[0] for k, v in SIT_LINKS.items()}
N_URDF_BASE = 131              # upstream URDF visuals (audit/assembly.json); the sit parts follow (N_SIT_VISUALS), then the head internals
N_SIT_VISUALS = 14             # knee_bumper 2, ankle_pad 4, hip_pad 2, sit_seat, sit_bumper, neck_stop, neck_pad 2, head_pad (sit_cad.json placements)

# A1b sit and stand path, left (hip pitch, knee, ankle, neck, head) in degrees. SIT_V2.md 3.2 kept the trunk near its
# standing pitch, which puts the CoM 14 to 27 mm in front of the heel edge of a 103 mm sole at every waypoint (the repo
# model, feet flat): zero errors of 1 deg tipped it back in the sit-down and at the end of the stand-up (sit_sim.py up,
# SIT.md section 5). LEAN tips the trunk forward at the four middle waypoints (hip pitch toward 0), which centres the CoM
# over the soles (42 to 48 mm from the heel, head forward). The sit and the stand ends are the approved ones. The
# software clamps the head forward waypoint to the software limits.
PATH_A1B_STUDY = [(-15, 5, 0, 0, 0), (-21, 40, -29, -22, -25), (-33, 75, -49, -22, -25), (-54, 110, -67, -22, -25),
                  (-58, 130, -82, -22, -25), (-60, 147, -92, -22, -25), (-60, 147, -92, 25, -25)]
LEAN = (0, 16, 15, 15, 15, 0, 0)
PATH_A1B = [(h + d, k, a, n, hd) for (h, k, a, n, hd), d in zip(PATH_A1B_STUDY, LEAN)]
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


_SB = None


def scene_base():
    """the scene as it was at BASE_REV: robot.urdf and every print/ STL from git, the other URDF meshes (servo cases,
    horns, boards: unchanged by this job) from the working tree. The CAD builder starts from this, so a re-run after
    sit_urdf.py --write (which renames the shin meshes) builds the same parts."""
    global _SB
    if _SB is not None:
        return _SB
    tmp = tempfile.mkdtemp(prefix="sit_base_")
    ud, pd = os.path.join(tmp, "urdf"), os.path.join(tmp, "print")
    os.makedirs(ud)
    os.makedirs(pd)
    open(os.path.join(ud, "robot.urdf"), "wb").write(git_blob("mini_bdx/robots/open_duck_mini_v2/robot.urdf"))
    for f in os.listdir(URDF_DIR):
        if f.endswith(".stl"):
            os.symlink(os.path.join(URDF_DIR, f), os.path.join(ud, f))
    names = subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", BASE_REV, "print/"], check=True,
                           capture_output=True, text=True).stdout.split()
    for n in names:
        if n.endswith(".stl"):
            open(os.path.join(pd, os.path.basename(n)), "wb").write(git_blob(n))
    old = (c3d_lib.URDF_DIR, c3d_lib.PRINT_DIR)
    c3d_lib.URDF_DIR, c3d_lib.PRINT_DIR = ud, pd
    try:
        _SB = c3d_lib.Scene()
    finally:
        c3d_lib.URDF_DIR, c3d_lib.PRINT_DIR = old
    return _SB


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
    """the y mirror in the part frame (right part from the left part); trimesh flips the winding of a reflection itself,
    so the normals stay outward (checked: the volume stays positive)"""
    r = m.copy()
    r.apply_transform(np.diag([1.0, -1.0, 1.0, 1.0]))
    if r.volume < 0:
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


# ---------------------------------------------------------------------------------------------------------------
# hole features (audit/feat3d.py): every existing hole stays as it was (the brief: keep every existing feature)
# ---------------------------------------------------------------------------------------------------------------
def hole_features(mesh):
    sys.path.insert(0, os.path.join(LAB, "audit"))
    from feat3d import features
    return features(mesh)


def holes_changed(base, new, tol=0.15):
    """hole features of two meshes of one part (same frame): the ones in one and not the other, matched by kind,
    diameter within tol and both ends within tol (either direction)"""
    fa, fb = hole_features(base), hole_features(new)

    def same(f, g):
        if f["kind"] != g["kind"] or abs(f["d"] - g["d"]) > tol:
            return False
        a0, a1, b0, b1 = (np.asarray(x, float) for x in (f["p0"], f["p1"], g["p0"], g["p1"]))
        return (np.abs(a0 - b0).max() <= tol and np.abs(a1 - b1).max() <= tol) or \
            (np.abs(a0 - b1).max() <= tol and np.abs(a1 - b0).max() <= tol)

    def unmatched(A, B):
        return [dict(kind=f["kind"], d=round(f["d"], 2), p0=np.round(f["p0"], 1).tolist(), p1=np.round(f["p1"], 1).tolist())
                for f in A if not any(same(f, g) for g in B)]
    return dict(base=len(fa), new=len(fb), gone=unmatched(fa, fb), added=unmatched(fb, fa))


def hole_keepout(mesh_world, extend=12.0, grow=0.4):
    """manifold of every hole feature of a part (world frame), each a cylinder grown by `grow` on the radius and
    run on `extend` mm past both ends along its axis: new material (a lug, a pad seat) is cut by it, so it never
    covers a hole, a recess or the driver's way to a screw"""
    cyls = []
    for f in hole_features(mesh_world):
        p0, p1 = np.asarray(f["p0"], float), np.asarray(f["p1"], float)
        a = p1 - p0
        n = np.linalg.norm(a)
        if n < 1e-6:
            continue
        a /= n
        cyls.append(to_man(cyl(p0 - a * extend, p1 + a * extend, f["d"] / 2 + grow, 48)))
    return union(cyls) if cyls else None


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


def prism_y(M, y0, y1):
    """the solid of M's shadow on the xz plane, from y0 to y1: a clean extrusion (flat faces, no steps)"""
    R = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])     # y -> z
    cs = M.transform(R[:3, :4]).project()
    P = manifold3d.Manifold.extrude(cs, float(y1 - y0)).translate((0.0, 0.0, float(y0)))
    return P.transform(np.linalg.inv(R)[:3, :4])


def swept(M, Ts):
    """union of M placed by each 4x4 in Ts"""
    return union([xform(M, T) for T in Ts])


def pinch_edges(m):
    """edges an STL round trip makes non-manifold (vertices merged by position): their midpoints"""
    from collections import Counter
    with tempfile.NamedTemporaryFile(suffix=".stl") as fh:
        m.export(fh.name)
        t = trimesh.load(fh.name, force="mesh")
    e = Counter(map(tuple, np.sort(t.edges, axis=1)))
    bad = [k for k, v in e.items() if v != 2]
    return [t.vertices[list(k)].mean(0) for k in bad]


def finalize(M, tol=1e-3, keep_largest=True):
    """a clean printable trimesh: the largest body only (cut-off crumbs dropped, keep_largest) or the bodies over
    1 mm3; slivers simplified away; a pinch (two faces of the solid touching along an edge, which an STL round trip turns
    non-manifold) is filled with a 0.4 mm cube (0.7 mm after 6 tries) so the solid joins properly there. Raises if it cannot be cleaned."""
    comps = sorted(M.decompose(), key=lambda c: -c.volume())
    M = comps[0] if keep_largest else solid(M)
    for k in range(12):
        m = from_man(M.simplify(tol))
        bad = pinch_edges(m)
        if not bad:
            return m
        h = 0.2 if k < 6 else 0.35                   # a larger cube when the small ones keep leaving a new pinch
        M = union([M] + [to_man(box(np.asarray(p) - h, np.asarray(p) + h)) for p in bad])
    raise RuntimeError("no clean STL after 12 pinch fills")


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
