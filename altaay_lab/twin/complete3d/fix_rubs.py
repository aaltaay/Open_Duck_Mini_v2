"""fix_rubs.py: push the routed points of the given cable runs away from the parts they rub or enter, measured exactly the
way cables3d/check_cables.py measures them: its grid with the terminal seat overlay, its near links (30 mm) and relevant
joints, each joint alone at 13 values over its URDF range, 8 mm end zones for the rub gap; its exact-mesh tube clearance
(3 mm ends) for the static check. Connector ends never move. CAD check only.

Run: python3 altaay_lab/twin/complete3d/fix_rubs.py --scratch <dir with c3d_grid_cad.npz> D13 P13 D10 SP4 SP5
Writes the moved points back into cables3d.json; run check_cables.py after it.
"""
import argparse
import json
import os
import sys

import numpy as np
import trimesh

from common import CABLES3D, LAB

sys.path.insert(0, os.path.join(LAB, "cables3d"))
import route_cables as RC  # noqa: E402
import check_cables as CK  # noqa: E402

TARGET, STATIC = 0.8, 0.5        # mm the run is pushed to: rub gap (a gap under 0 is a rub) and static tube clearance


def nearest_inner(pts, link, local, lo=1):
    """index of the run point (not an end) on `link` nearest to `local` (link frame)"""
    best = None
    for i in range(lo, len(pts) - 1):
        if pts[i]["link"] == link:
            d = np.linalg.norm(np.array(pts[i]["p"]) - local)
            if best is None or d < best[0]:
                best = (d, i)
    return best[1] if best else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("ids", nargs="+")
    a = ap.parse_args()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    g0 = RC.load_grid(s, os.path.abspath(a.scratch))
    c3 = json.load(open(CABLES3D))
    seats = {t["id"]: dict(link=t["link"], center=t["center_mm"], dims=t["dims_xyz_mm"]) for t in c3["terminals"]}
    g = g0.overlay([(v["link"], tuple(v["center"]), tuple(v["dims"]), None, k) for k, v in seats.items() if v["center"]])
    trees = CK.link_trees(g)
    CK.WORLD = [s.world_mesh(i) for i in s.inst]
    poser = RC.Poser(s)
    par = RC.tree(s)
    C = {c["id"]: c for c in c3["cables"]}
    report = {}
    for cid in a.ids:
        c = C[cid]
        run = [r for r in c["runs"] if r["name"] == "main"][0]
        pts = run["points"]
        rr = float(run["d_mm"]) / 2.0
        P0, _, _ = CK.run_world(s, poser, pts, {})
        near = {ln for ln, tr in trees.items() if (tr.query(P0, k=1, distance_upper_bound=30.0)[0] < 30.0).any()}
        ride = {p["link"] for p in pts}
        rel = set()
        for ln in near:
            for l2 in ride:
                if ln != l2:
                    rel |= set(RC.chain(par, l2, ln)[1])
        cfgs = [{}] + [{j: q} for j in sorted(rel) for q in np.linspace(RC.REV[j][0], RC.REV[j][1], 13)]
        hist = []
        for it in range(24):
            worst = (1e9,)
            for cfg in cfgs:
                P, lk, sd = CK.run_world(s, poser, pts, cfg)
                keep = np.where((sd > CK.END_ZONE) & (sd < sd[-1] - CK.END_ZONE))[0]
                if not len(keep):
                    continue
                T = poser.T(cfg)
                for ln in sorted(near):
                    M = s.T0[ln] @ np.linalg.inv(T[ln])
                    Q = (M[:3, :3] @ P[keep].T).T + M[:3, 3]
                    d, idx = trees[ln].query(Q, k=1)
                    d = d - 0.5 - rr
                    for jj in np.argsort(d)[:3]:
                        k = keep[jj]
                        if lk[k] is None or lk[k] == ln:
                            continue
                        if d[jj] < worst[0]:
                            vw = (np.linalg.inv(M) @ np.r_[trees[ln].data[idx[jj]], 1.0])[:3]
                            worst = (float(d[jj]), P[k], lk[k], T, vw, ln, cfg)
                        break
            st = CK.tube_clearance(s, pts, rr)
            hist.append((round(worst[0], 2), round(st[0], 2)))
            moved = False
            if worst[0] < TARGET:
                d, pw, link, T, vw, ln, cfg = worst
                dw = pw - vw
                dw /= max(np.linalg.norm(dw), 1e-9)
                local = (np.linalg.inv(T[link]) @ np.r_[pw, 1.0])[:3]
                i = nearest_inner(pts, link, local)
                if i is not None:
                    R = T[link][:3, :3]
                    for k in {i, max(1, i - 1) if pts[max(1, i - 1)]["link"] == link else i,
                              min(len(pts) - 2, i + 1) if pts[min(len(pts) - 2, i + 1)]["link"] == link else i}:
                        pts[k]["p"] = (np.array(pts[k]["p"]) + R.T @ dw * (TARGET - d + 0.3) * (1.0 if k == i else 0.5)).round(3).tolist()
                    moved = True
            elif st[0] < STATIC and st[2] is not None:
                val, key, q = st
                inst = [m for i_, m in zip(s.inst, CK.WORLD) if i_["key"] == key]
                cp = min((trimesh.proximity.closest_point(m, [q])[0][0] for m in inst), key=lambda x: np.linalg.norm(x - q))
                sdv = trimesh.proximity.signed_distance(min(inst, key=lambda m: np.linalg.norm(m.bounds.mean(0) - q)), [q])[0]
                dw = (cp - q) if sdv > 0 else (q - cp)
                dw /= max(np.linalg.norm(dw), 1e-9)
                best = None
                for i in range(1, len(pts) - 1):
                    pw_i = (s.T0[pts[i]["link"]] @ np.r_[pts[i]["p"], 1.0])[:3]
                    dd = np.linalg.norm(pw_i - q)
                    if best is None or dd < best[0]:
                        best = (dd, i)
                if best:
                    i = best[1]
                    R = s.T0[pts[i]["link"]][:3, :3]
                    pts[i]["p"] = (np.array(pts[i]["p"]) + R.T @ dw * (STATIC - val + 0.3)).round(3).tolist()
                    moved = True
            if not moved:
                break
        if len(c["points"]) == len(pts):
            c["points"] = [dict(q) for q in pts]
        report[cid] = hist
    json.dump(c3, open(CABLES3D + ".tmp", "w"), indent=1)
    os.replace(CABLES3D + ".tmp", CABLES3D)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
