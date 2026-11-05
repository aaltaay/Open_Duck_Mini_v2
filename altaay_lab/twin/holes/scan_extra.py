"""Mesh scan for round holes that no list has (CAD check only).

feat3d (audit/feat3d.py) finds round holes only along the 3 axes of each STL's frame (or of its largest facets).
Here every printed STL (print/ and twin/screws/stl) is also searched along any other axis that its concave
(reflex) edges point to: for each concave edge the crease direction is n1 x n2; directions with at least 12 mm of
such edges that are more than 3 deg from the feat3d axes are sectioned with the same ring finder (feat3d.rings3d,
cluster3d). Writes data/extra_holes.json (part frame and world frame).
"""
import json, os, sys, glob
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib
sys.path.insert(0, os.path.join(hlib.LAB, "audit"))
import feat3d

def feat_frame(m):
    n = m.face_normals; a = m.area_faces
    R = np.eye(3)
    if a[np.abs(n).max(1) > 0.999].sum() / a.sum() <= 0.1:
        fa = m.facets_area; fn = m.facets_normal
        o = np.argsort(-fa); z = fn[o[0]]; x = None
        for i in o[1:]:
            if abs(np.dot(fn[i], z)) < 0.02:
                x = fn[i] - np.dot(fn[i], z) * z; break
        if x is None:
            x = np.cross(z, [1, 0, 0]) if abs(z[0]) < 0.9 else np.cross(z, [0, 1, 0])
        x /= np.linalg.norm(x); y = np.cross(z, x); R = np.vstack([x, y, z])
    return R  # rows: the 3 axes feat3d sections along

def cand_axes(m, R):
    adj = m.face_adjacency
    conc = ~m.face_adjacency_convex
    ang = m.face_adjacency_angles
    sel = conc & (ang > np.radians(2)) & (ang < np.radians(60))
    n1 = m.face_normals[adj[sel, 0]]; n2 = m.face_normals[adj[sel, 1]]
    d = np.cross(n1, n2); d /= np.linalg.norm(d, axis=1)[:, None]
    e = m.vertices[m.face_adjacency_edges[sel, 0]] - m.vertices[m.face_adjacency_edges[sel, 1]]
    L = np.linalg.norm(e, axis=1)
    s = np.sign(d[np.arange(len(d)), np.abs(d).argmax(1)]); d = d * s[:, None]
    out = []
    used = np.zeros(len(d), bool)
    order = np.argsort(-L)
    for k in order:
        if used[k]:
            continue
        c = np.abs(d @ d[k]) > np.cos(np.radians(1.5))
        c &= ~used
        if L[c].sum() < 12:
            used[k] = True; continue
        ax = (d[c] * L[c, None]).sum(0); ax /= np.linalg.norm(ax)
        used |= c
        if np.degrees(np.arccos(np.clip(np.abs(R @ ax).max(), -1, 1))) > 3:
            out.append((ax, float(L[c].sum())))
    return out

def rings_along(m, ax):
    z = ax / np.linalg.norm(ax)
    x = np.cross(z, [1, 0, 0]) if abs(z[0]) < 0.9 else np.cross(z, [0, 1, 0]); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4); T[:3, :3] = np.vstack([x, y, z])
    mm = m.copy(); mm.apply_transform(T)
    feats = feat3d.cluster3d(feat3d.rings3d(mm, 2), 2)
    Ti = np.linalg.inv(T)
    return [dict(kind=f["kind"], d=f["d"], p0=(Ti @ np.r_[f["p0"], 1])[:3], p1=(Ti @ np.r_[f["p1"], 1])[:3]) for f in feats]

S = hlib.scene()
srcs = sorted({i["src"] for i in S.inst if i["printed"]}) + sorted(glob.glob(os.path.join(hlib.LAB, "twin", "screws", "stl", "body_*.stl")))
res = []
for src in srcs:
    m = trimesh.load(src, force="mesh")
    R = feat_frame(m)
    axes = cand_axes(m, R)
    found = []
    for ax, Ltot in axes:
        for f in rings_along(m, ax):
            if 0.8 <= f["d"] <= 12:
                found.append(dict(axis=ax.round(4).tolist(), crease_mm=round(Ltot, 1), kind=f["kind"], d=f["d"],
                                  p0=np.round(f["p0"], 2).tolist(), p1=np.round(f["p1"], 2).tolist()))
    wl = []
    for i in S.inst:
        if i["src"] != src:
            continue
        for f in found:
            p0 = (i["T"] @ np.r_[f["p0"], 1])[:3]; p1 = (i["T"] @ np.r_[f["p1"], 1])[:3]
            wl.append(dict(inst=i["idx"], p0=p0.round(2).tolist(), p1=p1.round(2).tolist()))
    res.append(dict(stl=os.path.relpath(src, hlib.REPO), n_axes=len(axes), axes=[(a.round(3).tolist(), round(l, 1)) for a, l in axes][:20],
                    holes=found, world=wl))
    print(os.path.basename(src), "off-frame axes", len(axes), "round holes on them", len(found),
          [(f["d"], f["axis"]) for f in found][:6], flush=True)
hlib.jdump(res, "extra_holes.json")
