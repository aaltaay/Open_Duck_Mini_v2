#!/usr/bin/env python3
"""Check every routed cable in cables3d.json and write the results back into it (field "check" and friends).

Usage: python3 altaay_lab/cables3d/check_cables.py --scratch <folder outside the repo>
Needs the grid cache written by route_cables.py in the same scratch folder.

Checks (rules and sources in CABLES_3D.md):
1. Length: every wire, cut_mm >= worst routed length over the full URDF range of the joints it crosses + SLACK_MM.
   SLACK_MM = 2 x 20 mm, the service-slack term of the lab length rule (CABLE_MAP.md); the other terms of that rule
   (2 x 22.6 mm connector tolerance, 10 mm per radian) are replaced here by measured terminals and the joint sweep.
2. Rub: smallest gap between the cable surface and any part of another link, joints swept one at a time over the
   full range (13 samples each, every joint whose parts come within 30 mm of the cable). Also the static gap to the
   cable's own link. Connector zones (8 mm from a run end) are left out.
3. Bend radius: at every corner of a fixed run, the largest fillet that fits the two adjacent straight pieces,
   against NASA-STD-8739.4A Table 7-1 (harness of AWG 10 or smaller: minimum 3 x OD, optimum 10 x OD). Service loops:
   radius of the arc that stores the free-span length change.
4. Connector room: free straight length along each terminal's exit direction, against 3 x OD + OD/2.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3d_lib as L  # noqa: E402
import route_cables as RC  # noqa: E402

SLACK_MM = 40.0          # 2 x 20 mm: 20 mm service slack at each fixed end (CABLE_MAP.md rule)
CHAINS = []
WORLD = []
BEND_MIN, BEND_OPT = 3.0, 10.0
RUB_WARN = 2.0          # mm surface gap below which a cable is flagged as a rub risk
END_ZONE = 8.0          # mm from a run end treated as the connector zone


INLINE = {"VSW", "G", "YD3", "YG3", "JG20", "JG10", "JG30", "J5", "JG"}     # floating inline splices


def node(pin):
    c = pin.split(".")[0]
    return c if c in INLINE else pin


def chains(cables):
    """conductor chains between fixed ends through inline splices (all cables). Returns list of lists of wire refs"""
    W = []
    for c in cables:
        for w in c["wires"]:
            if w.get("runs"):
                W.append((c["id"], w))
    adj = {}
    for k, (cid, w) in enumerate(W):
        a, b = node(w["from"]), node(w["to"])
        adj.setdefault(a, []).append((b, k))
        adj.setdefault(b, []).append((a, k))
    out = []
    seen = set()
    for k, (cid, w) in enumerate(W):
        for start in (node(w["from"]), node(w["to"])):
            if start.split(".")[0] in INLINE:
                continue
            stack = [(start, [], {start})]
            while stack:
                n, path, vis = stack.pop()
                for m, j in adj.get(n, []):
                    if j in path or m in vis:
                        continue
                    p2 = path + [j]
                    if m.split(".")[0] in INLINE:
                        stack.append((m, p2, vis | {m}))
                    else:
                        key = tuple(sorted(p2))
                        if key not in seen:
                            seen.add(key)
                            out.append([W[i] for i in p2])
    return out


def link_trees(g):
    from scipy.spatial import cKDTree
    out = {}
    for k, ln in enumerate(g.links):
        I = np.argwhere(g.label == k + 1)
        if len(I):
            out[ln] = cKDTree(g.lo + I + 0.5)
    return out


def run_world(s, poser, pts, cfg, step=2.0):
    """resampled world points of a run at cfg, with the link each sample is fixed to (None on a free span)"""
    T = poser.T(cfg)
    W = [(T[p["link"]] @ np.linalg.inv(s.T0[p["link"]]) @ np.r_[s.T0[p["link"]][:3, :3] @ np.array(p["p"]) +
                                                                  s.T0[p["link"]][:3, 3], 1.0])[:3] for p in pts]
    out, lk, sd = [], [], []
    acc = 0.0
    for i in range(len(W) - 1):
        a, b = W[i], W[i + 1]
        same = pts[i]["link"] == pts[i + 1]["link"]
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        for t in np.linspace(0, 1, n + 1)[:-1]:
            out.append(a + (b - a) * t)
            lk.append(pts[i]["link"] if same else None)
            sd.append(acc + t * np.linalg.norm(b - a))
        acc += np.linalg.norm(b - a)
    out.append(W[-1])
    lk.append(pts[-1]["link"])
    sd.append(acc)
    return np.array(out), lk, np.array(sd)


SPAN_BEST = [1e9, None]


def gaps(s, trees, poser, pts, r, cfgs, near_links):
    """min surface gap to other links and to the own link over the configs (free-span samples go to SPAN_BEST)"""
    best_other, best_own = (1e9, None, None), (1e9, None)
    for cfg in cfgs:
        P, lk, sd = run_world(s, poser, pts, cfg)
        keep = (sd > END_ZONE) & (sd < sd[-1] - END_ZONE)
        if not keep.any():
            continue
        T = poser.T(cfg)
        for ln in near_links:
            M = s.T0[ln] @ np.linalg.inv(T[ln])
            Q = (M[:3, :3] @ P[keep].T).T + M[:3, 3]
            d = trees[ln].query(Q, k=1)[0] - 0.5 - r
            lks = [l_ for l_, k in zip(lk, keep) if k]
            own = np.array([l_ == ln for l_ in lks])
            span = np.array([l_ is None for l_ in lks])
            if own.any():
                v = float(d[own].min())
                if v < best_own[0]:
                    best_own = (v, ln)
            other = ~own & ~span
            if other.any():
                v = float(d[other].min())
                if v < best_other[0]:
                    best_other = (v, ln, {k: round(float(x), 3) for k, x in cfg.items()})
            if span.any():
                v = float(d[span].min())
                if v < SPAN_BEST[0]:
                    SPAN_BEST[0] = v
                    SPAN_BEST[1] = (ln, {k: round(float(x), 3) for k, x in cfg.items()})
    return best_other, best_own


def smooth_bend(g, Pw, links, r, iters=120, lam=0.5, win=3):
    """Relax the fixed pieces of a run inside free space (a point moves toward the mid of its neighbours only where
    the distance field stays >= r), then the smallest radius of the circle through points win mm apart.
    Free-span ends and run ends stay put. Returns (min radius, smoothed points)"""
    P = L_resample_keep(Pw, links, 1.0)
    pts, lk = P
    pts = np.array(pts)
    fixed = np.zeros(len(pts), bool)
    fixed[0] = fixed[-1] = True
    for i in range(1, len(pts)):
        if lk[i] != lk[i - 1]:
            fixed[i] = fixed[i - 1] = True
    for _ in range(iters):
        mid = 0.5 * (pts[:-2] + pts[2:])
        cand = pts[1:-1] + lam * (mid - pts[1:-1])
        ok = (g.sample(cand) >= r) & ~fixed[1:-1]
        pts[1:-1][ok] = cand[ok]
    best = float("inf")
    n = len(pts)
    for i in range(win + 3, n - win - 3):
        if lk[i - win] != lk[i] or lk[i + win] != lk[i]:
            continue
        a, b, c = pts[i - win], pts[i], pts[i + win]
        ab, bc, ca = np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c)
        area = np.linalg.norm(np.cross(b - a, c - a)) / 2
        if area < 1e-6:
            continue
        best = min(best, ab * bc * ca / (4 * area))
    return best, pts


def L_resample_keep(P, links, step):
    out, lk = [P[0]], [links[0]]
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        for t in np.linspace(0, 1, n + 1)[1:]:
            out.append(a + (b - a) * t)
            lk.append(links[i + 1] if t >= 1.0 - 1e-9 else (links[i] if links[i] == links[i + 1] else "SPAN"))
    return out, lk


def loop_radius(c, a):
    """radius of a circular arc of length a over chord c (service loop at the shortest span)"""
    if a <= c + 1e-6:
        return float("inf")
    if a >= np.pi * c / 2:
        return a / (2 * np.pi)
    lo, hi = c / 2 + 1e-6, 1e6
    for _ in range(80):
        R = (lo + hi) / 2
        if 2 * R * np.arcsin(min(1.0, c / (2 * R))) > a:
            lo = R
        else:
            hi = R
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    t0 = time.time()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    g0 = RC.load_grid(s, os.path.abspath(a.scratch))
    data = json.load(open(RC.OUT_JSON))
    seats = {t["id"]: dict(link=t["link"], center=t["center_mm"], dims=t["dims_xyz_mm"]) for t in data["terminals"]}
    g = g0.overlay([(v["link"], tuple(v["center"]), tuple(v["dims"]), None, k) for k, v in seats.items() if v["center"]])
    trees = link_trees(g)
    global WORLD
    WORLD = [s.world_mesh(i) for i in s.inst]
    poser = RC.Poser(s)
    par = RC.tree(s)
    ends = {e["id"]: e for e in data["cable_ends"]}
    global CHAINS
    CHAINS = chains(data["cables"])
    summary = []
    for c in data["cables"]:
        findings = []
        # 1. length per conductor chain (fixed end to fixed end through inline splices), 20 mm slack per fixed end
        worst_fail = None
        for w in c["wires"]:
            if not w.get("runs"):
                continue
            mine = [ch for ch in CHAINS if any(x is w for _, x in ch)]
            res = []
            for ch in mine:
                cuts = [x["cut_mm"] for _, x in ch]
                Lmax = sum(x["length_max_mm"] for _, x in ch)
                Lrt = sum(x.get("length_max_runtime_mm", x["length_max_mm"]) for _, x in ch)
                need = Lmax + SLACK_MM
                if any(v is None for v in cuts):
                    res.append(dict(chain=["%s:%s>%s" % (ci, x["from"], x["to"]) for ci, x in ch], length_max_mm=round(Lmax, 1),
                                    required_mm=round(need, 1), cut_mm=None, margin_mm=None))
                    continue
                res.append(dict(chain=["%s:%s>%s" % (ci, x["from"], x["to"]) for ci, x in ch], length_max_mm=round(Lmax, 1),
                                required_mm=round(need, 1), cut_mm=sum(cuts), margin_mm=round(sum(cuts) - need, 1),
                                margin_runtime_mm=round(sum(cuts) - Lrt - SLACK_MM, 1)))
            w["chains"] = res
            known = [r for r in res if r["margin_mm"] is not None]
            if not known:
                w["length_check"] = "no cut length in the netlist (lead ships with the part)"
                continue
            wr = min(known, key=lambda r: r["margin_mm"])
            w["required_mm"] = wr["required_mm"]
            w["margin_mm"] = wr["margin_mm"]
            w["margin_runtime_mm"] = wr.get("margin_runtime_mm")
            w["fits_mm"] = round(wr["cut_mm"] - wr["length_max_mm"], 1)
            w["length_check"] = "pass" if wr["margin_mm"] >= 0 else ("fail (fits without slack)" if w["fits_mm"] >= 0 else "fail")
            if w["margin_mm"] < 0 and (worst_fail is None or w["margin_mm"] < worst_fail["margin_mm"]):
                worst_fail = w
        # 2.-4. per run
        rub_min, own_min, bend_min, room = (1e9, None, None), (1e9, None), (1e9, None, None), []
        for r in c["runs"]:
            pts = r["points"]
            rr = r["d_mm"] / 2.0
            P0, lk0, _ = run_world(s, poser, pts, {})
            near = set()
            for ln, tr in trees.items():
                M = s.T0[ln] @ np.linalg.inv(s.T0[ln])
                if (tr.query(P0, k=1, distance_upper_bound=30.0)[0] < 30.0).any():
                    near.add(ln)
            # joints that move a nearby link relative to a link the run rides on
            rel = set()
            ride = {p["link"] for p in pts}
            for ln in near:
                for l2 in ride:
                    if ln != l2:
                        rel |= set(RC.chain(par, l2, ln)[1])
            cfgs = [{}] + [{j: q} for j in sorted(rel) for q in np.linspace(RC.REV[j][0], RC.REV[j][1], 13)]
            cfgs_rt = [{}] + [{j: q} for j in sorted(rel) for q in np.linspace(*RC.RUNTIME.get(j, RC.REV[j]), 13)]
            SPAN_BEST[0], SPAN_BEST[1] = 1e9, None
            other, own = gaps(s, trees, poser, pts, rr, cfgs, sorted(near))
            r["span_taut_min_gap_mm"] = round(SPAN_BEST[0], 1) if SPAN_BEST[1] else None
            r["span_taut_at"] = SPAN_BEST[1]
            if any(j in RC.RUNTIME for j in rel):
                SPAN_BEST[0], SPAN_BEST[1] = 1e9, None
                o_rt, _ = gaps(s, trees, poser, pts, rr, cfgs_rt, sorted(near))
                r["rub_min_gap_runtime_mm"] = round(o_rt[0], 1) if o_rt[1] else None
            else:
                r["rub_min_gap_runtime_mm"] = round(other[0], 1) if other[1] else None
            r["rub_min_gap_mm"] = round(other[0], 1) if other[1] else None
            r["rub_part_link"] = other[1]
            r["rub_at"] = other[2] if other[1] else None
            r["static_min_gap_mm"] = round(own[0], 1) if own[1] else None
            r["swept_joints"] = sorted(rel)
            if other[1] and other[0] < rub_min[0]:
                rub_min = (other[0], other[1], other[2], r["name"])
            if own[1] and own[0] < own_min[0]:
                own_min = (own[0], own[1], r["name"])
            # bend radius
            Wz = np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in pts])
            rmin, _ = smooth_bend(g, Wz, [p["link"] for p in pts], max(0.5, rr))
            loops = []
            for sp in r.get("spans", []):
                Rl = loop_radius(sp["min_mm"], sp["max_mm"])
                loops.append(Rl)
            r["bend_min_radius_mm"] = round(rmin, 1) if np.isfinite(rmin) else None
            r["loop_min_radius_mm"] = round(min(loops), 1) if loops and np.isfinite(min(loops)) else None
            r["bend_rule_mm"] = dict(min=round(BEND_MIN * r["d_mm"], 1), optimum=round(BEND_OPT * r["d_mm"], 1))
            if rmin < bend_min[0]:
                bend_min = (rmin, "corner", r["name"])
            # connector room at both terminal ends
            for side, key in (("from", 0), ("to", -1)):
                tid = r[side]
                if tid not in ends:
                    continue
                e = ends[tid]
                p = np.array(e["p_world0"])
                d = np.array(e["dir_world0"])
                need = BEND_MIN * r["d_mm"] + r["d_mm"] / 2.0
                free_len = 40.0
                for m in WORLD:
                    if np.any(m.bounds[0] - 41 > p) or np.any(m.bounds[1] + 41 < p):
                        continue
                    loc, _, _ = m.ray.intersects_location([p + d * 0.2], [d], multiple_hits=False)
                    if len(loc):
                        free_len = min(free_len, float(np.linalg.norm(loc[0] - p)))
                gap_other = None
                if tid.startswith("SV"):
                    # exact clearance from the plug back (wire exit) to parts of other links at the zero pose
                    own = e["link"]
                    for inst, m in zip(s.inst, WORLD):
                        if inst["link"] == own or np.any(m.bounds[0] - 20 > p) or np.any(m.bounds[1] + 20 < p):
                            continue
                        dd = float(abs(L.trimesh.proximity.signed_distance(m, [p])[0]))
                        if gap_other is None or dd < gap_other[0]:
                            gap_other = (round(dd, 2), inst["key"], inst["link"])
                room.append(dict(run=r["name"], end=tid, free_mm=round(free_len, 1), need_mm=round(need, 1),
                                 ok=bool(free_len >= need or free_len >= 39.5),
                                 plug_gap_mm=gap_other[0] if gap_other else None,
                                 plug_gap_part=("%s (%s)" % gap_other[1:]) if gap_other else None))
        c["rub_min_gap_mm"] = round(rub_min[0], 1) if rub_min[1] else None
        c["rub"] = dict(gap_mm=c["rub_min_gap_mm"], link=rub_min[1], at=rub_min[2], run=rub_min[3]) if rub_min[1] else None
        c["static_min_gap_mm"] = round(own_min[0], 1) if own_min[1] else None
        c["bend_min_radius_mm"] = round(bend_min[0], 1) if np.isfinite(bend_min[0]) else None
        c["bend_min_kind"] = bend_min[1]
        c["connector_room"] = room
        lp = [dict(run=r["name"], **x) for r in c["runs"] for x in r.get("service_loops", [])]
        c["service_loops"] = lp
        bad_lp = [x for x in lp if not x["ok"]]
        bad_rt = [x for x in lp if not x["ok_runtime"]]
        od = c["d_mm"]
        # verdict
        if worst_fail:
            findings.append("length: %s -> %s chain needs %.0f mm (worst routed %.0f + %.0f slack), cut %s mm: short by %.0f%s" % (
                worst_fail["from"], worst_fail["to"], worst_fail["required_mm"], worst_fail["required_mm"] - SLACK_MM, SLACK_MM,
                sum(1 for _ in [0]) and min((r["cut_mm"] for r in worst_fail["chains"] if r["cut_mm"]), default=None),
                -worst_fail["margin_mm"], "" if worst_fail["fits_mm"] < 0 else " (fits taut, %.0f mm to spare without the slack)" % worst_fail["fits_mm"]))
        rt = [r.get("rub_min_gap_runtime_mm") for r in c["runs"] if r.get("rub_min_gap_runtime_mm") is not None]
        c["rub_min_gap_runtime_mm"] = round(min(rt), 1) if rt else None
        if c["rub_min_gap_mm"] is not None and c["rub_min_gap_mm"] < RUB_WARN:
            findings.append("rub: %.1f mm gap to %s at %s (full URDF range)%s" % (
                c["rub_min_gap_mm"], c["rub"]["link"], c["rub"]["at"],
                "; %.1f mm within the Runtime head ranges" % c["rub_min_gap_runtime_mm"]
                if c["rub_min_gap_runtime_mm"] is not None and c["rub_min_gap_runtime_mm"] != c["rub_min_gap_mm"] else ""))
        if c["bend_min_radius_mm"] is not None and c["bend_min_radius_mm"] < BEND_MIN * od:
            findings.append("bend: taut route radius %.1f mm < 3 x OD %.1f mm (dress the slack into a wider bend there)" % (
                bend_min[0], BEND_MIN * od))
        if bad_lp:
            findings.append("service loop: %d of %d loops cannot reach R >= 3 x OD over the full range (worst %s: free %.0f mm "
                            "over %.2f rad gives R %.1f mm, needs %.1f mm; route room limits it)%s" % (
                                len(bad_lp), len(lp), "+".join(min(bad_lp, key=lambda x: x["radius_mm"] or 0)["joints"]),
                                min(bad_lp, key=lambda x: x["radius_mm"] or 0)["free_mm"],
                                min(bad_lp, key=lambda x: x["radius_mm"] or 0)["angle_rad"],
                                min(bad_lp, key=lambda x: x["radius_mm"] or 0)["radius_mm"] or 0,
                                min(bad_lp, key=lambda x: x["radius_mm"] or 0)["rule_mm"],
                                "; within the Runtime head ranges %d fail" % len(bad_rt)))
        bad_room = [x for x in room if not x["ok"]]
        if bad_room:
            findings.append("connector room: " + ", ".join("%s %.0f of %.0f mm" % (x["end"], x["free_mm"], x["need_mm"]) for x in bad_room))
        unrouted = [r["name"] for r in c["runs"] if not r.get("routed", True)]
        if unrouted:
            findings.append("no clear path found for run(s) %s (straight placeholder)" % unrouted)
        c["check"] = "fail" if (worst_fail or unrouted) else ("pass" if not findings else "pass with notes")
        c["findings"] = findings
        live = [w for w in c["wires"] if w.get("runs") and w.get("cut_mm")]
        if live:
            ww = min(live, key=lambda w: w.get("margin_mm", 1e9))
            c["worst_mm"] = ww["length_max_mm"]
            c["required_mm"] = ww["required_mm"]
            c["margin_mm"] = ww.get("margin_mm")
        summary.append((c["id"], c["check"], c.get("margin_mm"), c["rub_min_gap_mm"], c["bend_min_radius_mm"]))
        print("%-4s %-15s margin %-7s rub %-6s bend %-6s %s" % (c["id"], c["check"], c.get("margin_mm"),
                                                               c["rub_min_gap_mm"], c["bend_min_radius_mm"],
                                                               "; ".join(findings)[:150]), flush=True)
    data["meta"]["check"] = dict(script="altaay_lab/cables3d/check_cables.py", slack_mm=SLACK_MM,
                                 bend_rule="NASA-STD-8739.4A Table 7-1: minimum 3 x OD, optimum 10 x OD",
                                 rub_warn_mm=RUB_WARN, generated_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
    RC.write_json_atomic(data, RC.OUT_JSON)
    print("checked %d cables in %.1f s" % (len(summary), time.time() - t0))


if __name__ == "__main__":
    main()
