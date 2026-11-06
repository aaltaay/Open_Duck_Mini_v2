"""V1 track 8 phase 3 (D50) seats and routes of the duck-side dock parts, CAD check only. Run in order: vox, vox_print, pick3, route2, views (each takes the scratch folder as argv[1]; search.py holds the shared box tests)."""
import os, sys
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(OUT)
import numpy as np, json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
dp = np.load('occ_print.npz'); oc = np.load('occ_cab.npz'); lo, h = dp['lo'], float(dp['h'])
P, A = dp['occ'], oc['occ']
S = json.load(open('picked.json')) if False else json.load(open('picked.json'))
names = ['x', 'y', 'z']
fig, axs = plt.subplots(len(S), 3, figsize=(13, 4.2 * len(S)))
for r, (n, v) in enumerate(S.items()):
    c, dims = np.array(v[1]), np.array(v[2])
    i = np.round((c - lo) / h).astype(int)
    for k in range(3):
        ax = axs[r, k]; a, b = [j for j in range(3) if j != k]
        sl = [slice(None)] * 3; sl[k] = i[k]
        img = np.zeros(P[tuple(sl)].shape); img[A[tuple(sl)]] = 1; img[P[tuple(sl)]] = 2
        ext = [lo[a], lo[a] + h * img.shape[0], lo[b], lo[b] + h * img.shape[1]]
        ax.imshow(img.T, origin='lower', extent=ext, cmap='Greys', vmin=0, vmax=2.5)
        ax.add_patch(Rectangle((c[a] - dims[a] / 2, c[b] - dims[b] / 2), dims[a], dims[b], fill=False, ec='red', lw=1.5))
        R = 45; ax.set_xlim(c[a] - R, c[a] + R); ax.set_ylim(c[b] - R, c[b] + R)
        ax.set_title(f"{n} seat, section {names[k]} = {c[k]:.0f} mm (dark: printed, grey: cables and placed boxes)", fontsize=7)
        ax.set_xlabel(names[a] + ' mm'); ax.set_ylabel(names[b] + ' mm')
plt.tight_layout(); plt.savefig('dock_seats.png', dpi=110)
