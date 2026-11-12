"""Mesh silhouettes of the posed duck for 2D sketches (convex hull per geom)."""
import numpy as np
from scipy.spatial import ConvexHull
from stance import mod, dat, m, flat_pose, SOLE, TRUNK

FOOTB = {m.mj_name2id(mod, 1, 'foot_assembly'), m.mj_name2id(mod, 1, 'foot_assembly_2')}
HEADB = {m.mj_name2id(mod, 1, n) for n in ['head_assembly', 'neck_yaw_assembly', 'head_pitch_to_yaw', 'neck_pitch_assembly']}

def verts(g):
    mid = mod.geom_dataid[g]
    if mid < 0 or mod.geom_type[g] != 7: return None
    a, n = mod.mesh_vertadr[mid], mod.mesh_vertnum[mid]
    return mod.mesh_vert[a:a + n] @ dat.geom_xmat[g].reshape(3, 3).T + dat.geom_xpos[g]

def polys(axes=(0, 2), shift=(0, 0, 0)):
    out = []
    for g in range(mod.ngeom):
        if mod.geom_group[g] not in (0, 1, 2): pass
        v = verts(g)
        if v is None or len(v) < 4: continue
        if mod.geom_contype[g] and g not in SOLE: continue
        v = (v + np.array(shift)) * 1000
        P = v[:, list(axes)]
        try: h = ConvexHull(P)
        except Exception: continue
        b = mod.geom_bodyid[g]
        kind = 'sole' if g in SOLE else 'foot' if b in FOOTB else 'head' if b in HEADB else 'trunk' if b == TRUNK else 'leg'
        depth = v[:, 1 if axes == (0, 2) else 2].mean()
        out.append((kind, P[h.vertices], depth, g))
    return out

def pose(h, k, a):
    return flat_pose(h, k, a)
