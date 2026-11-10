#!/usr/bin/env python3
"""Check every routed cable in cables3d.json and write the results back into it (field "check" and friends).

Usage: python3 altaay_lab/cables3d/check_cables.py --scratch <folder outside the repo>
Needs the grid cache written by route_cables.py in the same scratch folder.

Checks (rules and sources in CABLES_3D.md):
1. Length: every wire, cut_mm >= worst routed length over the full URDF range of the joints it crosses + SLACK_MM,
   judged per conductor chain through the floating splices (INLINE); the routed length of a twisted made cable is
   multiplied by its take-up at the shortest lay (wiring/netlist.yaml cable 'twist', D25).
   SLACK_MM = 2 x 20 mm, the service-slack term of the lab length rule (CABLE_MAP.md); the other terms of that rule
   (2 x 22.6 mm connector tolerance, 10 mm per radian) are replaced here by measured terminals and the joint sweep.
2. Rub: smallest gap between the cable surface and any part of another link, joints swept one at a time over the
   full range (13 samples each, every joint whose parts come within 30 mm of the cable). Also the static gap to the
   cable's own link. Connector zones (8 mm from a run end) are left out.
3. Bend radius: at every corner of a fixed run, the largest fillet that fits the two adjacent straight pieces,
   against NASA-STD-8739.4A Table 7-1 (harness of AWG 10 or smaller: minimum 3 x OD, optimum 10 x OD). Service loops:
   the loop between the two ties of each crossing (seats_ties.py service_loops): bend R = free length / largest joint
   angle, and length storage R = the cable the loop needs at the farthest pose bowed over the closest tie-to-tie chord.
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


INLINE = {"VSW", "G", "YD3", "YG3", "JG20", "JG10", "JG30", "J5", "JG", "JGD", "JSN"}     # floating inline splices (JGD, JSN: the D50 dock branches)


def twist_factors():
    """cable id -> (take-up factor, branch or None) for the twisted made cables (wiring/netlist.yaml cable 'twist': the
    length a twisted pair needs over the route at the shortest lay, NASA-STD-8739.4A 7.2.16 to 7.2.18 [L]). The factor
    is put on the whole routed length of each twisted wire (the 2 x 20 mm untwisted ends left in: conservative)"""
    import yaml
    net = yaml.safe_load(open(RC.NETLIST))
    out = {}
    for cb in net.get("cables", []):
        tw = cb.get("twist") or {}
        if tw.get("lay_mm") and tw.get("takeup_max"):
            m = str(tw.get("wires", ""))
            out[cb["id"]] = (float(tw["takeup_max"]), m.split()[1] if m.startswith("branch ") else None)
    return out


TWIST = {}


def routed(cid, w):
    """worst routed length of a wire with the twist take-up of its cable (TWIST)"""
    f, br = TWIST.get(cid, (1.0, None))
    if br is not None and w.get("branch") != br:
        f = 1.0
    return w["length_max_mm"] * f, w.get("length_max_runtime_mm", w["length_max_mm"]) * f


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


def tube_clearance(s, pts, r, end_mm=3.0):
    """exact: min over centreline samples (1 mm, ends left out) of (distance to the nearest part surface - r);
    negative = the tube enters that part. Returns (value, part key, world point)"""
    P = np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in pts])
    Q = RC.resample(P, 1.0)
    acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    Q = Q[(acc > end_mm) & (acc < acc[-1] - end_mm)]
    best = (1e9, None, None)
    if not len(Q):
        return best
    for inst, m in zip(s.inst, WORLD):
        if inst["key"] == "bms":
            continue      # CAD body replaced by the Tenergy 32175 (its box is solid in the routing grid)
        sel = np.all((Q >= m.bounds[0] - r - 3) & (Q <= m.bounds[1] + r + 3), axis=1)
        if not sel.any():
            continue
        sd = L.trimesh.proximity.signed_distance(m, Q[sel])        # > 0 inside
        cl = np.where(sd > 0, -sd, -sd) - r                         # outside: -sd = distance; inside: negative
        k = int(np.argmin(cl))
        if cl[k] < best[0]:
            best = (float(cl[k]), inst["key"], Q[sel][k])
    return best


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


LEN_KEYS = ("length_zero_mm", "length_min_mm", "length_max_mm", "length_max_runtime_mm")
LEN_TOL = 0.15        # mm: the 0.01 mm rounding of the stored points moves a sweep less than this


def refresh_lengths(s, poser, par, data):
    """the stored run lengths follow the points: a job that edits route points (twin/sit/sit_cables.py) or the joint
    ranges left them stale. Every run's zero, min, max and Runtime max length is taken again from its points over the
    URDF ranges (route_cables.py sweep). A wire and its cable take the change of their runs as a delta (some wires carry
    hand-set offsets from other jobs, kept as they are). Returns the changed runs as cable:run."""
    changed = []
    for c in data["cables"]:
        runs = {r["name"]: r for r in c.get("runs") or []}
        delta = {}
        for r in runs.values():
            links = [q["link"] for q in r["points"]]
            W0 = [(s.T0[l] @ np.r_[np.asarray(q["p"], float), 1.0])[:3] for q, l in zip(r["points"], links)]
            z0, mn, mx, spans = RC.sweep(s, poser, W0, links, par)
            _, _, mx_rt, _ = RC.sweep(s, poser, W0, links, par, RC.RUNTIME)
            new = dict(zip(LEN_KEYS, (round(z0, 1), round(mn, 1), round(mx, 1), round(mx_rt, 1))))
            r["spans"] = spans                      # the joint crossings of the points as they are now
            if any(r.get(k) is None or abs(new[k] - r[k]) > LEN_TOL for k in LEN_KEYS):
                delta[r["name"]] = {k: new[k] - r.get(k, r.get("length_max_mm", new[k])) if r.get(k) is not None else 0.0
                                    for k in LEN_KEYS}
                r.update(new)
                changed.append("%s:%s" % (c["id"], r["name"]))
        if not delta:
            continue
        wd = {k: [0.0] for k in LEN_KEYS}
        for w in c.get("wires") or []:
            if not w.get("runs"):
                continue
            for k in LEN_KEYS:
                d = sum(delta.get(n, {}).get(k, 0.0) for n in w["runs"])
                if w.get(k) is not None:
                    w[k] = round(w[k] + d, 1)
                wd[k].append(d)
        for k in ("length_zero_mm", "length_min_mm", "length_max_mm"):
            if c.get(k) is not None:
                c[k] = round(c[k] + max(wd[k], key=abs), 1)
    return changed


def check_loop_spans(par, data):
    """every service loop span pair [a, a + 1] must cross exactly the joints the loop names (a route edit that inserts
    points and leaves the loop indices behind would put a loop on a stationary segment). Returns the problems"""
    bad = []
    for c in data["cables"]:
        for r in c.get("runs") or []:
            pts = r["points"]
            for lp in r.get("service_loops", []):
                spans = lp.get("spans") or [lp["span"]]
                got = []
                for a, b in spans:
                    if b != a + 1 or b >= len(pts):
                        bad.append("%s %s: loop span %s is not a pair of route points" % (c["id"], r["name"], [a, b]))
                        continue
                    got += RC.chain(par, pts[a]["link"], pts[b]["link"])[1]
                if sorted(set(got)) != sorted(set(lp["joints"])):
                    bad.append("%s %s: loop %s spans %s cross %s, the loop names %s" % (
                        c["id"], r["name"], lp.get("tie_ids"), spans, sorted(set(got)), lp["joints"]))
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--json", default=RC.OUT_JSON, help="cables3d.json to read and rewrite (default: the lab file)")
    a = ap.parse_args()
    t0 = time.time()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    g0 = RC.load_grid(s, os.path.abspath(a.scratch))
    data = json.load(open(a.json))
    seats = {t["id"]: dict(link=t["link"], center=t["center_mm"], dims=t["dims_xyz_mm"]) for t in data["terminals"]}
    g = g0.overlay([(v["link"], tuple(v["center"]), tuple(v["dims"]), None, k) for k, v in seats.items() if v["center"]])
    trees = link_trees(g)
    global WORLD
    WORLD = [s.world_mesh(i) for i in s.inst]
    poser = RC.Poser(s)
    par = RC.tree(s)
    ends = {e["id"]: e for e in data["cable_ends"]}
    global CHAINS
    bad = check_loop_spans(par, data)
    if bad:
        raise SystemExit("service loop spans off their joints:\n  " + "\n  ".join(bad))
    relen = refresh_lengths(s, poser, par, data)
    print("lengths taken again from the points: %d runs changed %s" % (len(relen), relen), flush=True)
    CHAINS = chains(data["cables"])
    TWIST.update(twist_factors())
    print("twist take-up on the chain lengths: %s" % {k: v[0] for k, v in sorted(TWIST.items())}, flush=True)
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
                Lmax = sum(routed(ci, x)[0] for ci, x in ch)
                Lrt = sum(routed(ci, x)[1] for ci, x in ch)
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
            if r.get("through"):
                r["clearance_min_mm"], r["clearance_part"] = None, "run crosses %s on purpose" % r["through"]
            else:
                cv, ck, cp = tube_clearance(s, pts, rr)
                r["clearance_min_mm"] = round(cv, 2) if ck else None
                r["clearance_part"] = ck
                r["clearance_at"] = [round(float(x), 1) for x in cp] if ck else None
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
                tid = r.get(side)
                if tid not in ends:              # no named end (a run that starts or stops at a splice)
                    continue
                e = ends[tid]
                if not e.get("dir_world0"):
                    continue          # an end placed without an exit direction (the dock ends of D50): no room check
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
        # longest stretch with nothing holding the cable: no seat (hole, channel, edge) and no tie
        ties = [t for t in data.get("retention", []) if c["id"] in t["cables"]]
        worst_free = (0.0, None)
        for r in c["runs"]:
            P = np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in r["points"]])
            if len(P) < 2:
                continue
            acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            holds = [0.0, acc[-1]]
            for st in r.get("seats", []):
                if st["kind"] in ("hole", "channel", "edge") and st["point_index"] < len(acc):
                    holds.append(acc[st["point_index"]])
            for t in ties:
                q = np.array(t["center_mm"])
                d_ = np.linalg.norm(P - q, axis=1)
                k = int(np.argmin(d_))
                if d_[k] < 12.0:
                    holds.append(acc[k])
            for sp in r.get("spans", []):           # free spans are the designed loops, not unsupported runs
                holds += [acc[sp["span"][0]], acc[sp["span"][1]]]
            holds = sorted(holds)
            gap = max(b - a for a, b in zip(holds[:-1], holds[1:]))
            if gap > worst_free[0]:
                worst_free = (gap, r["name"])
        c["free_stretch_mm"] = round(worst_free[0], 1)
        c["free_stretch_run"] = worst_free[1]
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
            wl = min(bad_lp, key=lambda x: x["radius_mm"] or 0)
            findings.append("service loop: %d of %d loops cannot reach R >= 3 x OD over the full range (worst %s: free %.0f mm "
                            "between the ties, bend R %.1f mm over %.2f rad, length storage R %.1f mm (loop %.0f mm over a "
                            "%.1f mm closest tie-to-tie chord), needs %.1f mm; route room limits it)%s" % (
                                len(bad_lp), len(lp), "+".join(wl["joints"]), wl["free_mm"], wl.get("radius_bend_mm") or 0,
                                wl["angle_rad"], wl.get("radius_storage_mm") or 0, wl.get("loop_length_mm") or 0,
                                wl.get("chord_min_mm") or 0, wl["rule_mm"],
                                "; within the Runtime head ranges %d fail" % len(bad_rt)))
        cls = [(r_["clearance_min_mm"], r_["clearance_part"], r_["name"], r_.get("clearance_at")) for r_ in c["runs"]
               if r_.get("clearance_min_mm") is not None]
        if cls:
            cmin = min(cls)
            c["clearance_min_mm"] = cmin[0]
            c["clearance"] = dict(gap_mm=cmin[0], part=cmin[1], run=cmin[2], at=cmin[3])
            if cmin[0] < -0.1:       # within 0.1 mm counts as touching (a cable may lie on a part)
                findings.append("clearance: the tube enters %s by %.1f mm (run %s at %s, exact mesh, ends 3 mm left out)" % (
                    cmin[1], -cmin[0], cmin[2], cmin[3]))
        bad_room = [x for x in room if not x["ok"]]
        if bad_room:
            findings.append("connector room: " + ", ".join("%s %.0f of %.0f mm" % (x["end"], x["free_mm"], x["need_mm"]) for x in bad_room))
        unrouted = [r["name"] for r in c["runs"] if not r.get("routed", True)]
        if unrouted:
            findings.append("no clear path found for run(s) %s (straight placeholder)" % unrouted)
        # verdict: "fail" only when a wire cannot reach (its worst routed length is over its cut) or a run has no path; a
        # cable that reaches but has less than the 2 x 20 mm slack is "test fit": the TEST_PLAN.md 1.4 test fit at both
        # joint limits decides, as VERIFICATION.md C3 judges it (WARN). The fixed-length kit cables and the bought camera
        # FPC cannot be cut longer; a made cable can, and its finding gives the shortfall.
        cannot = [w for w in c["wires"] if w.get("margin_mm") is not None and w["margin_mm"] < 0 and (w.get("fits_mm") or 0) < 0]
        if cannot or unrouted:
            c["check"] = "fail"
        elif worst_fail:
            c["check"] = "test fit"
        else:
            c["check"] = "pass" if not findings else "pass with notes"
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
    RC.write_json_atomic(data, a.json)
    print("checked %d cables in %.1f s" % (len(summary), time.time() - t0))


if __name__ == "__main__":
    main()
