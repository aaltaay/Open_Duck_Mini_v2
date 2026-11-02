"""Free space inside the trunk for parts that are not in the upstream CAD (B11, B12, B22).

Method (all geometry from the upstream URDF meshes, Open_Duck_Mini b23317a, print STLs 730c14b):
1. Pose the robot from robot.urdf for a set of joint angles that cover the joint ranges of every part that
   moves inside or next to the trunk (hip yaw, hip roll, neck pitch at both limits and zero).
2. Voxelize every visual mesh at PITCH mm (surface voxels plus filled interior) and mark them occupied.
   The union over all poses is the swept, occupied volume.
3. Interior = inside the convex hull of the trunk shell parts (body_*, trunk_top, trunk_bottom,
   battery_pack_lid) AND enclosed: a ray from the voxel along +x, -x, +y, -y, +z and -z hits a shell part.
4. Free = interior and not occupied, eroded by CLEAR mm (cable and assembly clearance).
5. For each candidate part box, every axis-aligned orientation and position is tested with a 3D prefix sum.
Output: JSON with the free volume, the largest free boxes and every fitting position per part.
"""
import json, os, sys, itertools
import numpy as np, trimesh, yourdfpy
from scipy import ndimage

R = os.environ.get("ODM_URDF_DIR", os.path.join(os.path.dirname(__file__), "../../mini_bdx/robots/open_duck_mini_v2/"))
PITCH = float(os.environ.get("ODM_PITCH", "1.0"))
CLEAR = float(os.environ.get("ODM_CLEAR", "1.0"))
SHELL = {"body_front.stl", "body_back.stl", "body_middle_bottom.stl", "body_middle_top.stl",
         "trunk_top.stl", "trunk_bottom.stl", "battery_pack_lid.stl"}

u = yourdfpy.URDF.load(os.path.join(R, "robot.urdf"), load_meshes=False, build_scene_graph=True)
movers = ["left_hip_yaw", "right_hip_yaw", "left_hip_roll", "right_hip_roll", "neck_pitch"]
lim = {j.name: (j.limit.lower, j.limit.upper) for j in u.robot.joints if j.type == "revolute"}

def poses():
    base = {n: 0.0 for n in u.actuated_joint_names}
    yield dict(base)
    for jn in movers:
        lo, hi = lim[jn]
        for q in np.linspace(lo, hi, 5):
            c = dict(base); c[jn] = float(q); yield c

_mesh_cache = {}
def mesh(fn):
    if fn not in _mesh_cache:
        m = trimesh.load(os.path.join(R, fn), force="mesh"); m.apply_scale(1000.0)
        _mesh_cache[fn] = m
    return _mesh_cache[fn].copy()

def instances(cfg):
    u.update_cfg(cfg)
    out = []
    for ln, link in u.link_map.items():
        Tl = u.get_transform(ln)
        for v in link.visuals:
            fn = os.path.basename(v.geometry.mesh.filename)
            T = Tl @ (v.origin if v.origin is not None else np.eye(4)); T = T.copy(); T[:3, 3] *= 1000.0
            out.append((ln, fn, T))
    return out

# Trunk frame: express everything relative to the trunk_assembly link.
def to_trunk(insts):
    Tt = [T for ln, fn, T in insts if ln == "trunk_assembly"][0]
    # use the link transform itself (first visual origin is not the link frame), recompute:
    Tlink = u.get_transform("trunk_assembly").copy(); Tlink[:3, 3] *= 1000.0
    Ti = np.linalg.inv(Tlink)
    return [(ln, fn, Ti @ T) for ln, fn, T in insts]

base_insts = to_trunk(instances({n: 0.0 for n in u.actuated_joint_names}))
shell = [mesh(fn).apply_transform(T) for ln, fn, T in base_insts if ln == "trunk_assembly" and fn in SHELL]
shell_union = trimesh.util.concatenate(shell)
hull = shell_union.convex_hull
lo = np.floor(shell_union.bounds[0]) - 2; hi = np.ceil(shell_union.bounds[1]) + 2
shape = np.ceil((hi - lo) / PITCH).astype(int)
gx, gy, gz = [lo[i] + (np.arange(shape[i]) + 0.5) * PITCH for i in range(3)]
occ = np.zeros(shape, bool)

def mark(m):
    if np.any(m.bounds[1] < lo) or np.any(m.bounds[0] > hi):
        return
    vg = m.voxelized(pitch=PITCH).fill()
    pts = vg.points
    idx = np.floor((pts - lo) / PITCH).astype(int)
    ok = np.all((idx >= 0) & (idx < shape), axis=1)
    idx = idx[ok]
    occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True

seen = set()
print("grid", shape.tolist(), flush=True)
for ip, cfg in enumerate(poses()):
    print("pose", ip, len(seen), flush=True)
    for ln, fn, T in to_trunk(instances(cfg)):
        key = (ln, fn, tuple(np.round(T[:3, :].ravel(), 2)))
        if key in seen: continue
        seen.add(key)
        mark(mesh(fn).apply_transform(T))

from scipy.spatial import Delaunay
tri = Delaunay(hull.vertices)
X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
inside = np.zeros(len(P), bool)
for a in range(0, len(P), 500000):
    inside[a:a + 500000] = tri.find_simplex(P[a:a + 500000]) >= 0
inside = inside.reshape(shape)
del X, Y, Z, P
print("inside done", int(inside.sum()), flush=True)

# enclosed test on the shell occupancy grid (cheap ray march along grid axes)
shell_occ = np.zeros(shape, bool)
for m in shell:
    vg = m.voxelized(pitch=PITCH)
    idx = np.floor((vg.points - lo) / PITCH).astype(int)
    ok = np.all((idx >= 0) & (idx < shape), axis=1); idx = idx[ok]
    shell_occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True
enc = np.ones(shape, bool)
for ax in range(3):
    c = np.cumsum(shell_occ, axis=ax)
    tot = np.take(c, [-1], axis=ax)
    enc &= (c > 0) & ((tot - c) > 0)
free = inside & enc & ~occ
if CLEAR > 0:
    free = ndimage.binary_erosion(free, iterations=int(round(CLEAR / PITCH)))

S = np.zeros(np.array(shape) + 1, np.int32)
S[1:, 1:, 1:] = np.cumsum(np.cumsum(np.cumsum(free.astype(np.int32), 0), 1), 2)
def fits(dims):
    """all (orientation, min corner mm) where a dims box is fully free"""
    res = []
    for perm in set(itertools.permutations(dims)):
        n = np.ceil(np.array(perm) / PITCH).astype(int)
        if np.any(n > shape): continue
        a, b, c = n
        tot = (S[a:, b:, c:] - S[:-a, b:, c:] - S[a:, :-b, c:] - S[a:, b:, :-c]
               + S[:-a, :-b, c:] + S[:-a, b:, :-c] + S[a:, :-b, :-c] - S[:-a, :-b, :-c])
        ok = np.argwhere(tot == a * b * c)
        for i, j, k in ok:
            res.append(dict(dims_xyz=list(map(float, perm)),
                            min_mm=[round(float(lo[0] + i * PITCH), 1), round(float(lo[1] + j * PITCH), 1), round(float(lo[2] + k * PITCH), 1)]))
    return res

def summarize_fit(name, dims, want=None):
    r = fits(dims)
    out = dict(part=name, dims=dims, n_positions=len(r))
    if r:
        cs = np.array([np.array(x["min_mm"]) + np.array(x["dims_xyz"]) / 2 for x in r])
        out["centre_bounds_min"] = cs.min(0).round(1).tolist(); out["centre_bounds_max"] = cs.max(0).round(1).tolist()
        if want is not None:
            d = np.linalg.norm(cs - np.array(want), axis=1); i = int(np.argmin(d))
            out["closest_to"] = want; out["best"] = r[i]; out["best_centre"] = cs[i].round(1).tolist(); out["best_dist_mm"] = round(float(d[i]), 1)
        # cluster summary by orientation
        orient = {}
        for x, c in zip(r, cs):
            k = "x".join(str(int(v)) for v in x["dims_xyz"])
            orient.setdefault(k, []).append(c)
        out["by_orientation"] = {k: dict(n=len(v), centre_min=np.min(v, 0).round(1).tolist(), centre_max=np.max(v, 0).round(1).tolist()) for k, v in orient.items()}
    return out

if __name__ == "__main__":
    parts = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    report = dict(pitch_mm=PITCH, clearance_mm=CLEAR, grid_lo=lo.tolist(), grid_shape=shape.tolist(),
                  interior_cm3=round(float((inside & enc).sum()) * PITCH ** 3 / 1000, 1),
                  free_cm3=round(float(free.sum()) * PITCH ** 3 / 1000, 1),
                  trunk_parts_modelled=sorted({fn for ln, fn, T in base_insts if ln == "trunk_assembly"}))
    # placed modelled parts for reference (centres in trunk frame)
    report["modelled_centres"] = {fn: mesh(fn).apply_transform(T).bounds.mean(0).round(1).tolist()
                                  for ln, fn, T in base_insts if ln == "trunk_assembly" and fn not in SHELL}
    report["fits"] = [summarize_fit(k, v["dims"], v.get("near")) for k, v in parts.items()]
    np.save(os.environ.get("ODM_FREE_NPY", "/tmp/odm_free.npy"), free)
    json.dump(dict(report=report, lo=lo.tolist(), pitch=PITCH), open(os.environ.get("ODM_FREE_JSON", "/tmp/odm_free.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "fits"}, indent=1))
    for f in report["fits"]:
        print(json.dumps({k: f.get(k) for k in ("part", "dims", "n_positions", "best_centre", "best_dist_mm", "by_orientation")}))
