"""close-up sections of the bay before and after (CAD check only)"""
import sys, numpy as np, trimesh, subprocess
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import os
WT = os.environ.get("ODM_REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
OUTD = os.environ.get("BAY_OUT", os.path.join(os.path.expanduser("~"), "v1_out", "battery", "bay")); sys.path.insert(0, WT + "/altaay_lab/fasteners")
from fastlib import Scene
S = Scene(os.path.join(OUTD, "out", "scene")); K = {i["key"]: k for k, i in enumerate(S.inst)}
T = S.inst[K["body_back"]]["T"]
old = trimesh.load(os.environ.get("BAY_BEFORE_STL", os.path.join(OUTD, "body_back_before.stl"))); old.apply_transform(T)
new = trimesh.load(WT + "/print/body_back.stl"); new.apply_transform(T)
lid = S.mesh(K["battery_pack_lid"]); bms = S.mesh(K["bms"])
XC, YC, RP = -133.1, (-9.35, 12.2), 11.1
fig, ax = plt.subplots(2, 3, figsize=(17, 11))
planes = (((0, 0, 31.5), (0, 0, 1), "z = 31.5 mm (x right, y up)", (0, 1)), ((-133.1, 0, 0), (1, 0, 0), "x = -133.1 mm (y right, z up)", (1, 2)), ((0, 12.2, 0), (0, 1, 0), "y = +12.2 mm, through the +y cell (x right, z up)", (0, 2)))
for row, (m, tag) in enumerate(((old, "as built (D42 base)"), (new, "grown bay (track 9)"))):
    for col, (orig, nrm, lab, ij) in enumerate(planes):
        a = ax[row, col]
        for mm, c in ((m, "k"), (lid, "tab:blue"), (bms, "tab:green")):
            sec = mm.section(plane_origin=orig, plane_normal=nrm)
            if sec is None: continue
            for e in sec.discrete: a.plot(e[:, ij[0]], e[:, ij[1]], c, lw=0.8)
        if row == 1:
            if col == 0:
                for yc in YC: a.add_patch(plt.Circle((XC, yc), RP, fill=False, ec="tab:red", lw=1.4, ls="--"))
            elif col == 1: a.add_patch(plt.Rectangle((YC[0] - RP, -4.0), YC[1] - YC[0] + 2 * RP, 71.0, fill=False, ec="tab:red", lw=1.4, ls="--"))
            else: a.add_patch(plt.Rectangle((XC - RP, -4.0), 2 * RP, 71.0, fill=False, ec="tab:red", lw=1.4, ls="--"))
        elif col == 0:
            for yc in (-10.5, 10.5): a.add_patch(plt.Circle((-129.6, yc), 9.3, fill=False, ec="tab:orange"))
        a.set_title(f"{tag}: {lab}", fontsize=9); a.set_aspect("equal"); a.grid(alpha=0.3)
        if col == 0: a.set_xlim(-160, -105); a.set_ylim(-40, 45)
        elif col == 1: a.set_xlim(-45, 45); a.set_ylim(-20, 90)
        else: a.set_xlim(-160, -105); a.set_ylim(-20, 90)
fig.suptitle("battery bay in body_back: black body_back, blue battery_pack_lid, green Tenergy BMS, red dashed the 2S1P P45B pack (2 x 21.4 x 70 mm cells in sleeve), orange today's 18650 cells (CAD check only)", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(OUTD, "bay_sections.png"), dpi=105); print("ok")
