#!/usr/bin/env python3
"""Check (a): every screw head and every protruding screw tip against every other part, over each joint's range.

  python3 altaay_lab/fasteners/sweep_fasteners.py --scratch <folder outside the repo> [--steps 37] [--grid 13]

Reads altaay_lab/fasteners/fasteners.json (make_fasteners.py), rebuilds the same scene (fastlib.Scene) and writes
the result back into fasteners.json (field `sweep` per screw) plus fasteners/sweep_results.json.

Method (same idea as print/check_hip_roll_screw.py, extended to every fastener and every joint):
- each screw is two cylinders in its link frame: the head (dk x k, from the head seat outwards) and the protruding
  tip (major diameter, from the far end of the anchor to the screw end, only when the screw passes its anchor);
- every part surface is sampled (about 6 points per mm2, spacing about 0.4 mm) in its zero-pose world frame; servo
  horns move with the part screwed to them (the URDF puts horns on the servo body link);
- static check at the zero pose: head against every part, including the part under the head (catches heads that
  do not fit their recess); tip against every part except the anchor;
- single-joint sweeps: each revolute joint over its URDF limits (others at zero), screws on one side of the joint
  against parts on the other side; consecutive joint pairs on a grid (hip yaw-roll, roll-pitch, pitch-knee,
  knee-ankle, neck pitch-head pitch, head pitch-yaw, yaw-roll, head roll-antennas) for parts two joints apart;
- clearance = distance from the part surface to the cylinder; negative = part surface inside the cylinder
  (overlap depth); a cylinder centre inside a part is also an overlap.
Heads use the models in fasteners.json `meta.head_models` (DIN 912 from the Westfield table; servo bag and SG90
screws are stand-ins, marked UNVERIFIED there).
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fastlib  # noqa: E402

NEAR = 0.3   # mm: report as "near" below this clearance [L]


def rot(axis, origin, q):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + np.sin(q) * K + (1 - np.cos(q)) * K @ K
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = origin - R @ origin
    return T


def cyl_dist(P, c, a, h, r):
    """Signed distance from points P to a finite cylinder (centre c, unit axis a, half height h, radius r).
    Negative inside (minus the depth to the nearest cylinder face)."""
    v = P - c
    z = v @ a
    rad = np.linalg.norm(v - np.outer(z, a), axis=1)
    dz = np.abs(z) - h
    dr = rad - r
    out = np.where((dz <= 0) & (dr <= 0), np.maximum(dz, dr), 0.0)
    ox = np.maximum(dz, 0)
    orr = np.maximum(dr, 0)
    return out + np.sqrt(ox ** 2 + orr ** 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", default=os.environ.get("ODM_FASTENER_SCRATCH"))
    ap.add_argument("--steps", type=int, default=37)
    ap.add_argument("--grid", type=int, default=13)
    ap.add_argument("--density", type=float, default=6.0, help="surface samples per mm2")
    a = ap.parse_args()
    if not a.scratch:
        sys.exit("give --scratch or ODM_FASTENER_SCRATCH (outside the repo)")
    t0 = time.time()
    path = os.path.join(HERE, "fasteners.json")
    D = json.load(open(path))
    S = fastlib.Scene(os.path.abspath(a.scratch))
    inst = S.inst
    recs = [r for r in D["fasteners"] if r["kind"] == "screw"]

    # physical link of each instance: horns turn with the part screwed to them
    plink = {k: i["link"] for k, i in enumerate(inst)}
    for r in recs:
        if (r.get("anchor") or "").startswith("horn") and r.get("into_inst") is not None:
            plink[r["into_inst"]] = r["link"]
    # surface samples per instance (zero-pose world), cached
    cache = os.path.join(S.scratch, "sweep_samples_%g.npz" % a.density)
    if os.path.exists(cache):
        Z = np.load(cache)
        P_all, owner = Z["P"], Z["owner"]
    else:
        Ps, ow = [], []
        for k in range(len(inst)):
            m = S.mesh(k)
            n = max(2000, int(m.area * a.density))
            p, _ = __import__("trimesh").sample.sample_surface(m, n, seed=k + 1)
            Ps.append(np.vstack([p, m.vertices]).astype(np.float32))
            ow.append(np.full(len(Ps[-1]), k, np.int32))
        P_all, owner = np.vstack(Ps), np.concatenate(ow)
        np.savez(cache, P=P_all, owner=owner)
    P_all = P_all.astype(np.float64)
    print("samples: %d points on %d instances, %.0f s" % (len(P_all), len(inst), time.time() - t0))
    link_of_pt = np.array([plink[k] for k in range(len(inst))])[owner]

    # cylinders per screw, zero-pose world
    cyls = []   # (rec index, kind, centre, axis, half height, radius, excluded instances)
    for n, r in enumerate(recs):
        s0 = np.array(r["seat_world"], float)
        ax = np.array(r["axis_world"], float)
        h = r.get("head") or {}
        if h.get("dk"):
            wsh = (r.get("washer") or {}).get("t", 0.0)
            k = float(h["k"])
            c = s0 - ax * (wsh + 0.02 + k / 2)
            cyls.append((n, "head", c, ax, k / 2, float(h["dk"]) / 2, set()))
        if (h.get("type") or "").endswith("din912"):
            dkl, kl = {"M3": (5.7, 1.65), "M2.5": (4.5, 1.5)}[r["size"]]     # ISO 7380-1 button head, for the fix test
            wsh = (r.get("washer") or {}).get("t", 0.0)
            # the part under the head is left out here: the button head's fit in its recess is checked by make_fasteners
            cyls.append((n, "head_low", s0 - ax * (wsh + 0.02 + kl / 2), ax, kl / 2, dkl / 2,
                         {r.get("part_inst")} - {None}))
        L = r.get("length_mm")
        far = r.get("far")
        if L and far is not None and L > far + 0.05 and r.get("source") != "servo_case":
            t_a, t_b = far + 0.05, float(L)
            c = s0 + ax * (t_a + t_b) / 2
            excl = {r.get("into_inst")} | ({r.get("part_inst")} if r.get("part_inst") is not None else set())
            cyls.append((n, "tip", c, ax, (t_b - t_a) / 2, float(r["d"]) / 2, excl - {None}))
    print("cylinders: %d (%d heads, %d tips) on %d screws" % (len(cyls), sum(1 for c in cyls if c[1] == "head"),
                                                             sum(1 for c in cyls if c[1] == "tip"), len(recs)))
    from scipy.spatial import cKDTree
    tree = cKDTree(P_all)
    print("kd-tree built, %.0f s" % (time.time() - t0))
    worst = defaultdict(lambda: dict(clear=np.inf))
    hits = []
    hit_pose = {}
    worst_lab = defaultdict(lambda: dict(clear=np.inf))

    def check(ci, Tcyl, allowed, label, angle, test_inside=False):
        """Cylinder ci moved by Tcyl (4x4) against zero-pose sample points where allowed[point] is True."""
        n, kind, c, ax, hh, rr, excl = cyls[ci]
        cc = Tcyl[:3, :3] @ c + Tcyl[:3, 3]
        aa = Tcyl[:3, :3] @ ax
        idx = np.asarray(tree.query_ball_point(cc, np.sqrt(hh ** 2 + rr ** 2) + 1.0), int)
        if len(idx) == 0:
            return
        if allowed is not None:
            idx = idx[allowed[idx]]
        if excl:
            idx = idx[~np.isin(owner[idx], list(excl))]
        if len(idx) == 0:
            return
        d = cyl_dist(P_all[idx], cc, aa, hh, rr)
        j = int(np.argmin(d))
        val, part = float(d[j]), int(owner[idx[j]])
        if test_inside and val > 0:
            for k in set(owner[idx].tolist()):
                if bool(S.mesh(k).contains(cc[None, :])[0]):
                    val, part = -min(rr, hh), k
                    break
        key = (n, kind)
        if val < worst[key]["clear"]:
            worst[key] = dict(clear=round(val, 3), part=inst[part]["key"], part_inst=part, where=label, angle_deg=angle)
        kl = (n, kind, label)
        if val < worst_lab[kl]["clear"]:
            worst_lab[kl] = dict(clear=round(val, 3), part=inst[part]["key"], part_inst=part, where=label, angle_deg=angle)
        if val < 0 and kind != "head_low":
            hits.append(dict(rec=n, kind=kind, clear=round(val, 3), part=inst[part]["key"], part_inst=part, where=label,
                             angle_deg=angle, T=Tcyl.copy()))
            hk = (n, kind, part, label)
            if val < hit_pose.get(hk, (0,))[0]:
                hit_pose[hk] = (val, Tcyl.copy(), idx[d < 0].copy())

    # ---- static, zero pose: every part
    for ci in range(len(cyls)):
        check(ci, np.eye(4), None, "zero pose (static)", 0.0, test_inside=True)
    print("static check done, %.0f s" % (time.time() - t0))

    # ---- single-joint sweeps: screws on one side against parts on the other side
    for j in S.joints:
        moving = S.subtree(j["child"])
        mov_pt = np.isin(link_of_pt, list(moving))
        qs = np.linspace(j["lo"], j["hi"], a.steps)
        for ci, cy in enumerate(cyls):
            n = cy[0]
            on_moving = recs[n]["link"] in moving
            other = ~mov_pt if on_moving else mov_pt
            for q in qs:
                T = rot(j["axis"], j["origin"], q if on_moving else -q)
                check(ci, T, other, j["name"], round(float(np.degrees(q)), 1))
        print("  sweep %-16s %6.1f..%6.1f deg done, %.0f s" % (j["name"], np.degrees(j["lo"]), np.degrees(j["hi"]), time.time() - t0))

    # ---- consecutive joint pairs: screws two joints apart from the parts (A above j1, C below j2)
    jb = {j["name"]: j for j in S.joints}
    pairs = [(p, c) for p in jb for c in jb if jb[c]["parent"] == jb[p]["child"]]
    all_links = set(S.u.link_map)
    for p, c in pairs:
        j1, j2 = jb[p], jb[c]
        A_links = all_links - S.subtree(j1["child"])
        C_links = S.subtree(j2["child"])
        inA = np.isin(link_of_pt, list(A_links))
        inC = np.isin(link_of_pt, list(C_links))
        grid = [(q1, q2) for q1 in np.linspace(j1["lo"], j1["hi"], a.grid) for q2 in np.linspace(j2["lo"], j2["hi"], a.grid)]
        for ci, cy in enumerate(cyls):
            ln = recs[cy[0]]["link"]
            if ln in A_links:
                other, sign = inC, -1
            elif ln in C_links:
                other, sign = inA, 1
            else:
                continue
            for q1, q2 in grid:
                T = rot(j1["axis"], j1["origin"], q1) @ rot(j2["axis"], j2["origin"], q2)   # pose of C relative to A
                check(ci, T if sign == 1 else np.linalg.inv(T), other, "%s+%s" % (p, c),
                      (round(float(np.degrees(q1)), 1), round(float(np.degrees(q2)), 1)))
        print("  pair %s + %s done, %.0f s" % (p, c, time.time() - t0))

    # ---- part against part: at the worst pose of each moving hit, are the intruding points already inside the parts
    # that carry the screw? Then the bare parts collide there (a joint-range question), not the screw.
    # The test: at the smallest joint angle where the screw is hit, does the part that hits it already cut into any
    # part on the screw's side of the joint(s)? If so the bare parts collide first and the joint cannot get there.
    jb_ = {j["name"]: j for j in S.joints}
    all_links_ = set(S.u.link_map)
    pts_of = {}

    def own_side(n, label):
        ln = recs[n]["link"]
        if "+" in label:
            p_, c_ = label.split("+")
            A_ = all_links_ - S.subtree(jb_[p_]["child"])
            return A_ if ln in A_ else S.subtree(jb_[c_]["child"])
        sub = S.subtree(jb_[label]["child"])
        return sub if ln in sub else all_links_ - sub
    groups_ = defaultdict(list)
    for h in hits:
        groups_[(h["rec"], h["kind"], h["part_inst"], h["where"])].append(h)
    klass = {}
    for key, hs in groups_.items():
        n, kind, pk, label = key
        if label == "zero pose (static)":
            klass[key] = ("static contact" if min(h["clear"] for h in hs) > -0.1 else "static overlap", None)
            continue
        first = min(hs, key=lambda h: np.linalg.norm(np.atleast_1d(h["angle_deg"])))
        Ti = np.linalg.inv(first["T"])
        if pk not in pts_of:
            pts_of[pk] = P_all[owner == pk]
        Q = (Ti[:3, :3] @ pts_of[pk].T).T + Ti[:3, 3]
        side = own_side(n, label)
        lo_, hi_ = Q.min(0) - 1, Q.max(0) + 1
        n_in = 0
        for k in range(len(inst)):
            if plink[k] not in side or k == pk:
                continue
            b = S.mesh(k).bounds
            if np.any(b[0] > hi_) or np.any(b[1] < lo_):
                continue
            sel = np.all((Q >= b[0] - 0.01) & (Q <= b[1] + 0.01), axis=1)
            if sel.any():
                n_in += int(S.mesh(k).contains(Q[sel]).sum())
        klass[key] = ("parts collide first" if n_in >= 10 else "screw", n_in)
    out_hits = defaultdict(list)
    for h in hits:
        out_hits[(h["rec"], h["kind"], h["part_inst"], h["where"])].append(h)
    hit_rows = []
    for (n, kind, part, where), hs in out_hits.items():
        hs.sort(key=lambda h: h["clear"])
        angs = [h["angle_deg"] for h in hs]
        pk = hs[0]["part_inst"]
        cls, frac = klass.get((n, kind, pk, where), ("?", None))
        for h in hs:
            h.pop("T", None)
        hit_rows.append(dict(id=recs[n]["id"], spec=recs[n]["spec"], link=recs[n]["link"], kind=kind, against=inst[part]["key"],
                             against_inst=part,
                             where=where, worst_mm=hs[0]["clear"], at=hs[0]["angle_deg"], n_steps=len(hs),
                             angles=angs if where != "zero pose (static)" and "+" not in where else None,
                             cls=cls, part_points_inside=frac,
                             onset=min(angs, key=lambda x: float(np.linalg.norm(np.atleast_1d(x))))))
    hit_rows.sort(key=lambda h: (h["id"], h["kind"]))
    for n, r in enumerate(recs):
        sw = {}
        for kind in ("head", "tip", "head_low"):
            w = worst.get((n, kind))
            if w and np.isfinite(w["clear"]):
                sw[kind] = dict(clearance_mm=w["clear"], against=w["part"], where=w["where"], at=w["angle_deg"])
        # worst over the checks whose contact is the screw's own (labels where the bare parts collide first are left out)
        eff = None
        for (n2, k2, lab), wv in worst_lab.items():
            if n2 != n or k2 == "head_low" or not np.isfinite(wv["clear"]):
                continue
            if klass.get((n2, k2, wv["part_inst"], lab), ("",))[0] == "parts collide first":
                continue
            if eff is None or wv["clear"] < eff["clear"]:
                eff = dict(wv, kind=k2)
        if eff:
            sw_eff = dict(clearance_mm=eff["clear"], against=eff["part"], where=eff["where"], at=eff["angle_deg"], cylinder=eff["kind"])
        low = sw.pop("head_low", None)
        if sw:
            m = min(sw.values(), key=lambda x: x["clearance_mm"])
            sw["worst_text"] = "%.2f mm vs %s (%s %s)" % (m["clearance_mm"], m["against"], m["where"], m["at"])
            mine = [h for h in hit_rows if h["id"] == r["id"]]
            if any(h["cls"] in ("screw", "static overlap") for h in mine):
                sw["status"] = "HIT"
            elif mine and any(h["cls"] == "parts collide first" for h in mine):
                sw["status"] = "PARTS COLLIDE FIRST"
            elif mine:
                sw["status"] = "CONTACT"
            else:
                sw["status"] = "NEAR" if m["clearance_mm"] < NEAR else "CLEAR"
        if low:
            sw["with_iso7380_head"] = low
        if eff:
            sw["screw_first"] = sw_eff
        r["sweep"] = sw
    D["sweep"] = dict(method=__doc__.split("Method")[1].strip()[:1200], steps=a.steps, grid=a.grid, density=a.density,
                      near_mm=NEAR, joints=[dict(name=j["name"], lo_deg=round(np.degrees(j["lo"]), 1), hi_deg=round(np.degrees(j["hi"]), 1))
                                            for j in S.joints],
                      pairs=["%s+%s" % pc for pc in pairs], hits=hit_rows)
    with open(path, "w") as fh:
        json.dump(D, fh, separators=(",", ":"))
    json.dump(dict(hits=hit_rows, worst=[dict(id=recs[n]["id"], kind=k, **w) for (n, k), w in worst.items()]),
              open(os.path.join(S.scratch, "sweep_results_full.json"), "w"), default=str)
    print("hits: %d rows on %d screws; %.0f s" % (len(hit_rows), len({h["id"] for h in hit_rows}), time.time() - t0))
    from collections import Counter as _C
    print("hit classes:", dict(_C(h["cls"] for h in hit_rows)))
    for h in hit_rows:
        if h["cls"] in ("screw", "static overlap"):
            print("  %s %-34s %-4s vs %-28s %-22s worst %.2f at %s (%d steps) %s %s" % (
                h["id"], h["spec"][:34], h["kind"], h["against"], h["where"][:22], h["worst_mm"], h["at"], h["n_steps"],
                h["cls"], h["part_points_inside"]))


if __name__ == "__main__":
    main()
