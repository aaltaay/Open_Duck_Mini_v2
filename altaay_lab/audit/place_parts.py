"""Pick positions for parts that are not in the upstream CAD, from the free-space grid of free_space.py.

For each part: every axis-aligned orientation and position where the box (plus a wire-exit margin on one
axis) is fully free is scored by distance to an anchor (where its wires go), a bonus for touching a wall
(so it can be taped or tied to a printed surface) and a keep-out distance from the BNO055.
Writes placements.json (frame: URDF zero-pose world in mm; the trunk link is the URDF root) and prints a table.
"""
import json, os, itertools, sys
import numpy as np
from scipy import ndimage

FREE = os.environ.get("ODM_FREE_NPY", "/tmp/odm_free.npy")
META = os.environ.get("ODM_FREE_JSON", "/tmp/odm_free.json")
OUT = os.environ.get("ODM_PLACEMENTS", os.path.join(os.path.dirname(__file__), "placements.json"))
free = np.load(FREE); meta = json.load(open(META)); lo = np.array(meta["lo"]); pitch = meta["pitch"]
shape = np.array(free.shape)
geom_free = free.copy()   # free space from geometry only, used to find real walls to mount on
# keep-outs for things the CAD does not model (all mm, URDF zero-pose frame)
gx, gy, gz = [lo[i] + (np.arange(shape[i]) + 0.5) * pitch for i in range(3)]
X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
def box_keepout(c, half):
    return (np.abs(X - c[0]) <= half[0]) & (np.abs(Y - c[1]) <= half[1]) & (np.abs(Z - c[2]) <= half[2])
def tube_keepout(a, b, r):
    a, b = np.array(a, float), np.array(b, float); ab = b - a; L2 = ab @ ab
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / L2, 0, 1)
    return (X - a[0] - t * ab[0]) ** 2 + (Y - a[1] - t * ab[1]) ** 2 + (Z - a[2] - t * ab[2]) ** 2 <= r * r
ADAPTER = (-84.5, 0.0, 59.6); NECK = (1.0, 19.2, 90.0); SWITCH = (-123.8, 0.0, 93.6)
HIPL = (-31.5, 35.0, 63.5); HIPR = (-31.5, -35.0, 63.5); IMU0 = (-87.1, 0.0, 43.3)
KEEP = [
    ("adapter components and plugs (board is a bare plate in CAD): 15 mm above, 5 mm margin", box_keepout((ADAPTER[0], 0, 60.4 + 7.5), (21 + 5, 16.5 + 5, 7.5))),
    ("BNO055 components and wires: 6 mm both sides, 4 mm margin", box_keepout(IMU0, (10 + 4, 13.5 + 4, 1.5 + 6))),
    ("S1 adapter to left hip yaw", tube_keepout(ADAPTER, HIPL, 6)), ("S6 adapter to right hip yaw", tube_keepout(ADAPTER, HIPR, 6)),
    ("D1 USB adapter to neck", tube_keepout(ADAPTER, NECK, 6)), ("S14 and D3 left hip to neck", tube_keepout(HIPL, NECK, 6)),
    ("D4 right hip to neck", tube_keepout(HIPR, NECK, 5)), ("D2 IMU to neck", tube_keepout(IMU0, NECK, 4)),
    ("P13 pack bus to head", tube_keepout(SWITCH, NECK, 5)), ("P9/P11 switch to adapter", tube_keepout(SWITCH, ADAPTER, 5)),
]
for _, k in KEEP:
    free = free & ~k
del X, Y, Z
def prefix(g):
    P = np.zeros(shape + 1, np.int32); P[1:, 1:, 1:] = np.cumsum(np.cumsum(np.cumsum(g.astype(np.int32), 0), 1), 2)
    return P
S = prefix(free)
wall = free & ~ndimage.binary_erosion(geom_free)     # free voxels next to a real printed or modelled surface
W = np.zeros(shape + 1, np.int32)
W[1:, 1:, 1:] = np.cumsum(np.cumsum(np.cumsum(wall.astype(np.int32), 0), 1), 2)

# solid = static printed or modelled trunk parts at the zero pose (real mounting surfaces only)
import trimesh, yourdfpy
_R = os.environ.get("ODM_URDF_DIR", os.path.join(os.path.dirname(__file__), "../../mini_bdx/robots/open_duck_mini_v2/"))
_u = yourdfpy.URDF.load(os.path.join(_R, "robot.urdf"), load_meshes=False, build_scene_graph=True)
solid = np.zeros(shape, bool)
_Tl = _u.get_transform("trunk_assembly")
for _v in _u.link_map["trunk_assembly"].visuals:
    _fn = os.path.basename(_v.geometry.mesh.filename)
    if _fn.startswith(("wj-", "drive_", "passive_")): continue   # servo cases and horns are not tape surfaces
    _T = _Tl @ (_v.origin if _v.origin is not None else np.eye(4)); _T = _T.copy(); _T[:3, 3] *= 1000.0
    _m = trimesh.load(os.path.join(_R, _fn), force="mesh"); _m.apply_scale(1000.0); _m.apply_transform(_T)
    _pts = _m.voxelized(pitch=pitch).points
    _i = np.floor((_pts - lo) / pitch).astype(int); _ok = np.all((_i >= 0) & (_i < shape), axis=1); _i = _i[_ok]
    solid[_i[:, 0], _i[:, 1], _i[:, 2]] = True
SD = []   # per axis: prefix sums of solid dilated 3 voxels along that axis (a surface within 3 mm counts)
for _ax in range(3):
    _st = np.zeros([1 if i == _ax else 1 for i in range(3)], bool)
    _fp = np.zeros([7 if i == _ax else 1 for i in range(3)], bool); _fp[...] = True
    _d = ndimage.binary_dilation(solid, structure=_fp)
    _P = np.zeros(shape + 1, np.int32); _P[1:, 1:, 1:] = np.cumsum(np.cumsum(np.cumsum(_d.astype(np.int32), 0), 1), 2)
    SD.append(_P)

def boxsum(P, a, b, c):
    return (P[a:, b:, c:] - P[:-a, b:, c:] - P[a:, :-b, c:] - P[a:, b:, :-c]
            + P[:-a, :-b, c:] + P[:-a, b:, :-c] + P[a:, :-b, :-c] - P[:-a, :-b, :-c])

IMU = np.array([-87.1, 0.0, 43.3])   # BNO055 centre (MOUNTING.md)
PARTS = [
    # id, label, dims (mm), wire margin (mm, added on the longest axis), anchor (mm), keep-out from IMU (mm)
    ("bec_pro", "Castle CC BEC Pro (servo 7.2 V regulator); envelope covers 43x33x24 (Castle guide), 47x33x22 (Horizon), 1.7x1.3x1 in (Motion RC)", (47, 33, 26), 8, (-84.5, 0.0, 59.6), 25),
    ("fuse_holder", "Littelfuse FHAC0001ZXJ inline ATO fuse holder: body 50 x 17.2 x 17.2 mm plus cover on a strap (Littelfuse drawing via parts check)", (52, 22, 18), 0, (-108.0, -25.0, 50.0), 0),
    ("mosfet_switch", "Pololu 2815 Big MOSFET Slide Switch HP (20.3 x 22.9 mm board, 25.4 with the slide switch overhang)", (20.3, 25.4, 4.1), 4, (-112.0, 0.0, 85.0), 0),
    ("power_splice", "Servo power splices (V+ and GND, soldered in heat shrink) feeding the 3 chain branches (D15)", (30, 16, 10), 0, (-60.0, 0.0, 0.0), 0),
    ("usb_slack", "Adafruit 3878 USB cable slack, about 0.4 m coiled and tied", (45, 35, 10), 0, (-60.0, 0.0, 10.0), 0),
]
res = []
for pid, label, dims, margin, anchor, keep in PARTS:
    best = None
    for perm in set(itertools.permutations(dims)):
        d = np.array(perm, float); d[np.argmax(d)] += margin
        n = np.ceil(d / pitch).astype(int)
        if np.any(n >= shape): continue
        ok = boxsum(S, *n) == np.prod(n)
        idx = np.argwhere(ok)
        if not len(idx): continue
        cen = lo + (idx + n / 2.0) * pitch
        wallfrac = boxsum(W, *n)[ok] / np.prod(n)
        # support: share of solid voxels in a 3-voxel slab just outside the largest face (either side)
        ax = int(np.argmin(n)); m = list(n); m[ax] = 1
        slab = boxsum(SD[ax], *m)                  # 1-voxel slab of the dilated solid, every position
        sup = np.zeros(len(idx))
        for side in (-1, int(n[ax])):
            j = idx.copy(); j[:, ax] += side
            valid = np.all((j >= 0) & (j < np.array(slab.shape)), axis=1)
            v = np.zeros(len(idx)); v[valid] = slab[j[valid, 0], j[valid, 1], j[valid, 2]] / np.prod(m)
            sup = np.maximum(sup, v)
        dist = np.linalg.norm(cen - np.array(anchor), axis=1)
        imu = np.linalg.norm(cen - IMU, axis=1)
        score = dist + np.where(sup >= 0.6, 0.0, 1000.0) + np.where(imu < keep + d.max() / 2, 500.0, 0.0)
        i = int(np.argmin(score))
        cand = dict(id=pid, label=label, dims_xyz_mm=[float(x) for x in perm], box_with_margin_mm=d.round(1).tolist(),
                    center_mm=cen[i].round(1).tolist(), frame="urdf_world_mm", n_positions=int(len(idx)),
                    dist_to_anchor_mm=round(float(dist[i]), 1), dist_to_imu_mm=round(float(imu[i]), 1),
                    flat_face_support=round(float(sup[i]), 2), score=round(float(score[i]), 1))
        if best is None or cand["score"] < best["score"]:
            best = cand
    res.append(best or dict(id=pid, label=label, dims_xyz_mm=list(dims), center_mm=None, frame="urdf_world_mm", n_positions=0))
    if best:   # reserve this part (box with wire margin plus 3 mm) before placing the next one
        c = np.array(best["center_mm"]); h = np.array(best["box_with_margin_mm"]) / 2 + 3
        a0 = np.clip(np.floor((c - h - lo) / pitch).astype(int), 0, shape); a1 = np.clip(np.ceil((c + h - lo) / pitch).astype(int), 0, shape)
        free[a0[0]:a1[0], a0[1]:a1[1], a0[2]:a1[2]] = False
        S = prefix(free)

# Parts placed from the CAD or measured positions rather than the free-space search
res += [
    dict(id="bms_tenergy", label="BatterySpace PCM-L04S30-566, 60 x 60 x 5 mm, in the rear pocket (D65)", dims_xyz_mm=[5, 60, 60],
         center_mm=[-159.2, 0.0, 40.0], frame="urdf_world_mm",
         source="CAD check only, 2026-11-14. Rear boss on body_back, 66 x 66 x 8 mm, recess 61 x 61 x 6 mm. The old measured slot 17.75 x 47.2 x 5.33 mm does not hold this board."),
]
np.save(os.environ.get("ODM_FREE_KEEP_NPY", "/tmp/odm_free_keep.npy"), free)
json.dump(res, open(OUT, "w"), indent=1)
for r in res:
    print(json.dumps(r))
