"""V1 track 8 phase 3 (D50) seats and routes of the duck-side dock parts, CAD check only. Run in order: vox, vox_print, pick3, route2, views (each takes the scratch folder as argv[1]; search.py holds the shared box tests)."""
import os, sys
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(OUT)
import numpy as np, itertools, json
from scipy import ndimage
d = np.load('occ.npz'); occ, lo, h = d['occ'], d['lo'], float(d['h'])
occ1 = ndimage.binary_dilation(occ, iterations=1)          # 1 mm clearance
I = np.pad(occ1.astype(np.int32), ((1, 0), (1, 0), (1, 0))).cumsum(0).cumsum(1).cumsum(2)
def cnt(a, b):
    (x0, y0, z0), (x1, y1, z1) = a, b
    return (I[x1, y1, z1] - I[x0, y1, z1] - I[x1, y0, z1] - I[x1, y1, z0] + I[x0, y0, z1] + I[x0, y1, z0] + I[x1, y0, z0] - I[x0, y0, z0])
def idx(p): return np.round((np.array(p) - lo) / h).astype(int)
def free_box(c, dims):
    a = idx(np.array(c) - np.array(dims) / 2); b = idx(np.array(c) + np.array(dims) / 2)
    if (a < 0).any() or (b > np.array(occ.shape)).any(): return False
    return cnt(a, b) == 0
def touch(c, dims, gap=1.6):
    """a face of the box within gap of an occupied voxel (the VHB face): returns the face side"""
    out = []
    for k in range(3):
        for s in (-1, 1):
            p = np.array(c, float); p[k] += s * (dims[k] / 2 + gap)
            dd = np.array(dims, float); dd[k] = 0.6
            a = idx(p - dd / 2); b = idx(p + dd / 2); b = np.maximum(b, a + 1)
            if (a >= 0).all() and (b <= np.array(occ.shape)).all():
                n = cnt(a, b); tot = np.prod(b - a)
                if n > 0.8 * tot: out.append((k, s))
    return out
inner = dict(x=(-113, 35), y=(-49, 49), z=(-15, 104))
res = {}
for name, dims_list, region in (
        ("F2", [(52, 18, 18), (18, 52, 18), (18, 18, 52)], inner),
        ("DK2", [(3, 8, 13), (3, 13, 8)], dict(x=(20, 35), y=(-25, 25), z=(10, 70))),
        ("DK67", [(3, 8, 13), (3, 13, 8), (8, 3, 13), (13, 8, 3)], dict(x=(-114, -95), y=(-10, 49), z=(0, 75)))):
    best = []
    for dims in dims_list:
        for x in np.arange(*region['x'], 1.0):
            for y in np.arange(*region['y'], 1.0):
                for z in np.arange(*region['z'], 1.0):
                    c = (x, y, z)
                    if free_box(c, dims):
                        t = touch(c, dims)
                        if t: best.append(dict(c=[float(v) for v in c], dims=dims, faces=t))
    res[name] = best
    print(name, len(best), best[:3])
json.dump(res, open('cands.json', 'w'))
