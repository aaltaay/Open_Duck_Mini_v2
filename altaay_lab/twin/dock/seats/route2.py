"""V1 track 8 phase 3 (D50) seats and routes of the duck-side dock parts, CAD check only. Run in order: vox, vox_print, pick3, route2, views (each takes the scratch folder as argv[1]; search.py holds the shared box tests)."""
import os, sys
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(OUT)
import numpy as np, json, heapq
from scipy import ndimage
d = np.load('occ.npz'); occ, lo, h = d['occ'], d['lo'], float(d['h'])
dist = ndimage.distance_transform_edt(~occ) * h
def idx(p): return tuple(np.round((np.array(p) - lo) / h).astype(int))
def pos(i): return lo + np.array(i) * h
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
def astar(a, b, need):
    A, B = idx(a), idx(b); free = dist >= need
    for q in (A, B):
        sl = tuple(slice(max(0, q[k] - 2), q[k] + 3) for k in range(3)); free[sl] |= True   # the lead exit only (2 mm)
    # bounding box of the two ends plus margin, to keep the graph small
    lo_i = np.maximum(np.minimum(A, B) - 70, 0); hi_i = np.minimum(np.maximum(A, B) + 71, occ.shape)
    sub = free[lo_i[0]:hi_i[0], lo_i[1]:hi_i[1], lo_i[2]:hi_i[2]]; dsub = dist[lo_i[0]:hi_i[0], lo_i[1]:hi_i[1], lo_i[2]:hi_i[2]]
    ids = -np.ones(sub.shape, int); nz = np.argwhere(sub); ids[tuple(nz.T)] = np.arange(len(nz))
    rows, cols, w = [], [], []
    for dv in [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) if (i, j, k) > (0, 0, 0)]:
        q = nz + dv; ok = np.all((q >= 0) & (q < sub.shape), 1); p0, q0 = nz[ok], q[ok]
        tgt = ids[tuple(q0.T)]; m = tgt >= 0
        cost = np.linalg.norm(dv) * (1 + 0.3 / np.maximum(dsub[tuple(q0[m].T)], 0.5))
        rows += [ids[tuple(p0[m].T)]]; cols += [tgt[m]]; w += [cost]
    rows, cols, w = map(np.concatenate, (rows, cols, w))
    Gm = csr_matrix((np.r_[w, w], (np.r_[rows, cols], np.r_[cols, rows])), shape=(len(nz), len(nz)))
    sa, sb = ids[tuple(np.array(A) - lo_i)], ids[tuple(np.array(B) - lo_i)]
    if sa < 0 or sb < 0: return None
    D, pred = dijkstra(Gm, indices=sa, return_predecessors=True)
    if not np.isfinite(D[sb]): return None
    path = [sb]
    while path[-1] != sa: path.append(pred[path[-1]])
    P = [pos(nz[q] + lo_i) for q in path[::-1]]; P[0] = np.array(a, float); P[-1] = np.array(b, float)
    out = [P[0]]; i = 0
    while i < len(P) - 1:
        j = len(P) - 1
        while j > i + 1:
            seg = np.linspace(out[-1], P[j], int(np.linalg.norm(P[j] - out[-1]) / 0.5) + 2)
            if all(dist[idx(s)] >= need or np.linalg.norm(s - P[0]) < 4 or np.linalg.norm(s - P[-1]) < 4 for s in seg): break
            j -= 1
        out.append(P[j]); i = j
    # validate every final segment: outside 3 mm of the two ends no sample may sit in an occupied voxel or under the clearance
    for p, q in zip(out[:-1], out[1:]):
        for t in np.linspace(p, q, int(np.linalg.norm(q - p) / 0.5) + 2):
            if min(np.linalg.norm(t - P[0]), np.linalg.norm(t - P[-1])) > 3.0 and dist[idx(t)] < need:
                return None
    return [p.round(2).tolist() for p in out]
T = {  # terminals, world mm at the zero pose (trunk_assembly link)
    'DKP.HOLE': [34.5, 0.0, 38.0], 'DK2.VIN': [33.0, 0.0, 28.5], 'DK2.VOUT': [33.0, 0.0, 19.5],
    'F2.IN': [-85.0, -42.0, 53.0], 'F2.OUT': [-85.0, -42.0, -1.0], 'BMS.P': [-126.3, -29.5, 33.0],
    'DK6.VIN': [-104.0, -4.5, 43.0], 'DK6.VOUT': [-110.0, 1.0, 43.0], 'DK7.VIN': [-104.0, 19.0, 43.0], 'DK7.VOUT': [-104.0, 7.0, 43.0],
    'SW1.VIN': [-107.8, 14.0, 29.0], 'SW1.GND': [-107.8, 34.0, 29.0], 'SW1.CTL': [-107.8, 24.0, 44.0], 'RT1': [-129.6, 0.0, 66.0]}
RUNS = {'DC1': [('DKP.HOLE', 'DK2.VIN', 1.5), ('DK2.VOUT', 'F2.IN', 1.5), ('F2.OUT', 'BMS.P', 1.5)],
        'DC2': [('DKP.HOLE', 'BMS.P', 1.5)],
        'DC3': [('DKP.HOLE', 'RT1', 0.7), ('DKP.HOLE', 'SW1.CTL', 0.7), ('RT1', 'BMS.P', 0.7)],
        'DC4': [('DKP.HOLE', 'DK6.VIN', 1.0), ('DK6.VOUT', 'SW1.VIN', 1.5), ('DK7.VOUT', 'SW1.VIN', 1.0)]}
def mouth(p, need=2.0):
    i = np.array(idx(p)); best = None
    for d in np.argwhere(np.ones((31, 31, 31), bool)) - 15:
        j = i + d
        if (j >= 0).all() and (j < occ.shape).all() and dist[tuple(j)] >= need:
            n = np.linalg.norm(d)
            if best is None or n < best[0]: best = (n, j)
    return pos(best[1]).round(2).tolist()
PAD = dict(T)
LEAD_IN = {}
for k in T:                     # route from each terminal's lead exit: the nearest point with 2 mm clearance
    T[k] = mouth(PAD[k], 1.2 if k == 'DK6.VIN' else 2.0); LEAD_IN[k] = round(float(np.linalg.norm(np.subtract(T[k], PAD[k]))), 1)
print('lead-in mm', LEAD_IN)
res = {}
for cid, runs in RUNS.items():
    res[cid] = []
    for a, b, rad in runs:
        P = astar(T[a], T[b], rad + 1.0) or astar(T[a], T[b], rad + 0.3) or astar(T[a], T[b], rad)
        if P is not None:
            P = [list(PAD[a])] * (LEAD_IN[a] > 0) + P + [list(PAD[b])] * (LEAD_IN[b] > 0)
        L = None if P is None else float(np.sum(np.linalg.norm(np.diff(np.array(P), axis=0), axis=1)))
        mind = None if P is None else float(min(dist[idx(s)] for p, q in zip(P[:-1], P[1:]) for s in np.linspace(p, q, 20)
                                               if np.linalg.norm(s - np.array(T[a])) > 3 and np.linalg.norm(s - np.array(T[b])) > 3) if len(P) > 1 else 0)
        res[cid].append(dict(frm=a, to=b, points=P, length_mm=None if L is None else round(L, 1), min_clear_centre_mm=mind))
        print(cid, a, b, L and round(L, 1), mind)
json.dump(dict(terminals=PAD, lead_exit=T, lead_in_mm=LEAD_IN, runs=res), open('routes.json', 'w'), indent=1)
