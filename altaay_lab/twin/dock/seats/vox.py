"""V1 track 8 phase 3 (D50) seats and routes of the duck-side dock parts, CAD check only. Run in order: vox, vox_print, pick3, route2, views (each takes the scratch folder as argv[1]; search.py holds the shared box tests)."""
import os, sys
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(OUT)
import sys, json, numpy as np, trimesh
sys.path.insert(0, os.path.join(LAB, 'twin', 'complete3d'))
import common as C
S = C.scene()
ms = [S.world_mesh(i) for i in S.inst if i['link'] == 'trunk_assembly']
P = json.load(open(os.path.join(LAB, 'audit', 'placements.json')))
P = P if isinstance(P, list) else P['placements']
# seat search grid: the dock parts are left out here because they are the ones being placed; route2.py adds them back
# as obstacles for the cable routes
for p in [q for q in P if not q['id'].startswith('dock_')]:
    if p['center_mm'][2] < 120:
        b = trimesh.creation.box(extents=p['dims_xyz_mm']); b.apply_translation(p['center_mm']); ms.append(b)
lo = np.array([-154., -55, -35]); hi = np.array([46., 55, 108]); h = 1.0
ax = [np.arange(lo[k], hi[k], h) + h / 2 for k in range(3)]
G = np.stack(np.meshgrid(*ax, indexing='ij'), -1)
occ = np.zeros(G.shape[:3], bool)
for m in ms:
    bl, bh = m.bounds
    sl = tuple(slice(max(0, int((bl[k] - lo[k]) / h) - 1), int((bh[k] - lo[k]) / h) + 2) for k in range(3))
    pts = G[sl].reshape(-1, 3)
    if len(pts): occ[sl] |= m.contains(pts).reshape(G[sl].shape[:3])
# inside the shell: the trunk inner volume = points enclosed by body shells along +x and -x rays? use: not occupied and between walls
np.savez_compressed('occ.npz', occ=occ, lo=lo, h=h)
print(occ.shape, occ.mean())
