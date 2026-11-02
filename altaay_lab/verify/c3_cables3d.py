"""C3: every active cable has a 3D route (altaay_lab/cables3d/cables3d.json, cables3d agent) whose worst-case length plus
the stated slack fits its cut length, every joint crossing has a service loop that meets 3 x OD, and every tie point has
something to hold it.

  coverage   every active netlist cable is in cables3d.json, every run routed, every netlist wire present with the
             same cut length; netlist pieces joined in series at a splice that the 3D record does not route (a lead and
             its extension, e.g. P7 at JFI and JFO) count as one conductor with the summed cut length
  length     by conductor chain, the way cables3d/check_cables.py judges it: a solder splice that no part holds floats
             along the bundle at build time (its position is set only by the wire lengths), so the wires joined there
             are judged together, fixed end to fixed end. Floating: every netlist splice except SPV and SPG (seated on
             the belly, MOUNTING.md "Servo power splices") and JBP and JBN (the BEC output leads end there; their length
             is not published). Per chain: worst routed length over the joint ranges + 40 mm (CABLE_MAP.md length rule:
             2 x 20 mm service slack, one per fixed end) <= summed cut (kit cables: the 150 mm kit length).
             Routed longer than the cut: FAIL; shorter but under the 40 mm slack: WARN (test fit)
  loops      every joint the netlist lists for a cable is crossed by its 3D route; every crossing has a free loop
             between two ties (cables3d.json service_loops: ties_at_mm, or the plug where the loop runs to a connector).
             Recomputed here from the route and the URDF (61 samples per joint over the URDF range): bend R = free
             length / largest joint angle from zero; length storage R = the cable the loop needs at the farthest pose
             (fixed pieces + span chord) bowed as one circular arc over the closest tie-to-tie chord. Both >= 3 x the
             run diameter (NASA-STD-8739.4A Change 4, Table 7-1, overall harness of AWG 10 or smaller without coax:
             minimum 3 x OD, optimum 10 x OD). The same is reported within the head ranges of the Runtime gamepad code
  retention  every tie point and what holds it: an existing printed feature, a stick-on tie mount (BOM line 34 MB3A,
             with the flat-patch check cables3d records), a tie to an anchored neighbour cable, or nothing yet (open);
             BOM lines 32 and 34 Need vs these counts
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c3_cables3d.py
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

SLACK = 40.0
BEND_MIN = 3.0
CJ = os.environ.get("C3_CABLES3D") or V.lab("cables3d", "cables3d.json")   # env: dry run on a copy (agent use only)
URDF = os.path.join(V.REPO, "mini_bdx", "robots", "open_duck_mini_v2", "robot.urdf")
SEATED = {"SPV": "seated on the belly (MOUNTING.md, servo power splices: cable tie or foam tape)",
          "SPG": "seated on the belly (MOUNTING.md, servo power splices: cable tie or foam tape)",
          "JBP": "the BEC output leads end there (lead length not published)",
          "JBN": "the BEC output leads end there (lead length not published)"}
FIXED_LEN = {"kit cable": "kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2",
             "FPC ribbon": "fixed-length FPC: test fit (TEST_PLAN.md 1.4, test order TO9); proposal: the 200 mm Raspberry Pi "
                           "Standard-Mini camera cable, Adafruit 5818 (22-pin 0.5 mm to 15-pin 1 mm, for the Pi 5 and Zero), "
                           "instead of BOM E7 (cables3d/CABLES_3D.md)"}


def series_merged(wires3d, netwires, kinds):
    """netlist wires of one cable, with the two pieces joined at a splice that the 3D record does not route summed into
    one conductor (a holder lead and its extension: the physical path is the same). Returns {(from, to): (cut, pieces,
    splice)} for both directions of every merged conductor and for every other wire."""
    ends3d = {x.split(".")[0] for w in wires3d for x in (w["from"], w["to"])}
    by_node = {}
    for w in netwires:
        for e in (w["from"], w["to"]):
            by_node.setdefault(e.split(".")[0], []).append(w)
    out, used = {}, set()
    for j, ws in by_node.items():
        if kinds.get(j) == "splice" and len(ws) == 2 and j not in ends3d:
            a, b = ws
            ea = a["from"] if a["to"].split(".")[0] == j else a["to"]
            eb = b["to"] if b["from"].split(".")[0] == j else b["from"]
            cut = a["cut_mm"] + b["cut_mm"] if a.get("cut_mm") is not None and b.get("cut_mm") is not None else None
            out[(ea, eb)] = out[(eb, ea)] = (cut, [a, b], j)
            used |= {id(a), id(b)}
    for w in netwires:
        if id(w) not in used:
            out[(w["from"], w["to"])] = (w.get("cut_mm"), [w], None)
    return out, len(netwires) - len(used) // 2


def arc_radius(c, a):
    """radius of a circular arc of length a through two points c apart (minor or major arc); inf if a <= c"""
    if a <= c + 1e-6:
        return math.inf
    if c < 1e-6:
        return a / (2 * math.pi)

    def length(R, major):
        h = math.asin(min(1.0, c / (2 * R)))
        return 2 * R * (math.pi - h if major else h)
    major = a > math.pi * c / 2
    lo, hi = c / 2, max(a, c) * 1e3
    for _ in range(200):
        R = (lo + hi) / 2
        L = length(R, major)
        if (L > a) != major:     # minor arc: length falls as R grows; major arc: length grows with R
            lo = R
        else:
            hi = R
    return R


def chains(wires, floating):
    """conductor chains between fixed ends through floating splices. wires: list of (cable, rec). Returns list of
    lists of indexes into wires"""
    def node(pin):
        c = pin.split(".")[0]
        return c if c in floating else pin
    adj = defaultdict(list)
    for k, (_, w) in enumerate(wires):
        a, b = node(w["from"]), node(w["to"])
        adj[a].append((b, k))
        adj[b].append((a, k))
    out, seen = [], set()
    for k, (_, w) in enumerate(wires):
        for start in (node(w["from"]), node(w["to"])):
            if start in floating:
                continue
            stack = [(start, [], {start})]
            while stack:
                n, path, vis = stack.pop()
                for m, j in adj.get(n, []):
                    if j in path or m in vis:
                        continue
                    p2 = path + [j]
                    if m in floating:
                        stack.append((m, p2, vis | {m}))
                    else:
                        key = tuple(sorted(p2))
                        if key not in seen:
                            seen.add(key)
                            out.append(p2)
    return out


class Kin:
    """link transforms (mm) of robot.urdf for joint configurations (yourdfpy), and the revolute joint ranges"""
    def __init__(self):
        import yourdfpy
        self.u = yourdfpy.URDF.load(URDF, load_meshes=False, build_scene_graph=True)
        self.rng = {j.name: (float(j.limit.lower), float(j.limit.upper)) for j in self.u.robot.joints if j.type == "revolute"}
        self.zero = {n: 0.0 for n in self.u.actuated_joint_names}
        self.cache = {}

    def T(self, link, cfg):
        key = (link, tuple(sorted((k, round(v, 6)) for k, v in cfg.items())))
        if key not in self.cache:
            c = dict(self.zero)
            c.update(cfg)
            self.u.update_cfg(c)
            M = np.array(self.u.get_transform(link), float)
            M[:3, 3] *= 1000.0
            self.cache[key] = M
            self.u.update_cfg(self.zero)
        return self.cache[key]


def runtime_head_ranges():
    """head ranges of the Runtime gamepad code (ODM_RUNTIME at 376de65), or None"""
    p = os.path.join(V.RUNTIME, "mini_bdx_runtime", "mini_bdx_runtime", "xbox_controller.py")
    if not os.path.exists(p):
        return None, p
    txt = open(p).read()
    out = {}
    for name, joint in (("HEAD_PITCH_RANGE", "head_pitch"), ("HEAD_YAW_RANGE", "head_yaw"), ("HEAD_ROLL_RANGE", "head_roll")):
        m = re.search(name + r"\s*=\s*\[([-\d.]+),\s*([-\d.]+)\]", txt)
        if m:
            out[joint] = (float(m.group(1)), float(m.group(2)))
    return out, p


def loop_check(kin, r, lp, rt_ranges):
    """recompute one service loop from the route and the URDF: (bend R, storage R, both within the Runtime ranges)"""
    pts = r["points"]
    i, i1 = lp["span"]
    P = np.array([(kin.T(p["link"], {}) @ np.r_[p["p"], 1.0])[:3] for p in pts])
    Bk = [p["link"] for p in pts]
    acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    a0, a1 = max(lp["ties_at_mm"][0], 0.0), min(lp["ties_at_mm"][1], acc[-1])

    def along(a):
        k = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
        t = (a - acc[k]) / max(float(np.linalg.norm(P[k + 1] - P[k])), 1e-9)
        return P[k] + (P[k + 1] - P[k]) * t
    la, lb = Bk[i], Bk[i1]
    A0 = np.linalg.inv(kin.T(la, {})) @ np.r_[along(a0), 1.0]
    B0 = np.linalg.inv(kin.T(lb, {})) @ np.r_[along(a1), 1.0]
    S0 = np.linalg.inv(kin.T(la, {})) @ np.r_[P[i], 1.0]
    S1 = np.linalg.inv(kin.T(lb, {})) @ np.r_[P[i1], 1.0]
    js = lp["joints"]
    fixed = (acc[i] - a0) + (a1 - acc[i1])

    def sweep(ranges):
        n = {1: 61, 2: 21, 3: 9}.get(len(js), 5)
        grids = np.meshgrid(*[np.linspace(ranges[j][0], ranges[j][1], n) for j in js], indexing="ij")
        cmin, smax = math.inf, 0.0
        for q in zip(*[g.ravel() for g in grids]):
            cfg = dict(zip(js, q))
            Ta, Tb = kin.T(la, cfg), kin.T(lb, cfg)
            cmin = min(cmin, float(np.linalg.norm((Ta @ A0)[:3] - (Tb @ B0)[:3])))
            smax = max(smax, float(np.linalg.norm((Ta @ S0)[:3] - (Tb @ S1)[:3])))
        return cmin, smax
    cmin, smax = sweep(kin.rng)
    length = fixed + smax
    th = sum(max(abs(kin.rng[j][0]), abs(kin.rng[j][1])) for j in js)
    free = a1 - a0
    out = dict(free=free, length=length, chord=cmin, bend=free / max(th, 1e-9), storage=arc_radius(cmin, length), th=th)
    rt = dict(kin.rng)
    rt.update(rt_ranges or {})
    if any(j in (rt_ranges or {}) for j in js):
        cmin_rt, _ = sweep(rt)
        th_rt = sum(max(abs(rt[j][0]), abs(rt[j][1])) for j in js)
        out.update(bend_rt=free / max(th_rt, 1e-9), storage_rt=arc_radius(cmin_rt, length))
    else:
        out.update(bend_rt=out["bend"], storage_rt=out["storage"])
    return out


def bom_need(line_id):
    for ln in open(V.lab("BOM.md"), encoding="utf-8").read().splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) > 4 and cells[0] == line_id:
            return cells[3]
    return None


def main():
    R = V.Result("C3", "Every active cable has a 3D route whose worst length plus slack fits its cut, a service loop at every joint, and a hold at every tie point",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py",
                 "Every active cable: route present and routed, wires and cut lengths as in the netlist, worst length over the "
                 "joint ranges + 40 mm vs cut by conductor chain through floating splices, netlist joints vs 3D crossings, the "
                 "loop between the ties at every crossing (bend and length storage vs 3 x OD, recomputed from the URDF), what "
                 "holds every tie point, BOM lines 32 and 34 vs the tie and mount counts",
                 "Real cable stiffness and where the slack sits, connector back-shell sizes (Molex 5264 housing drawing not "
                 "read), rubbing against moving parts beyond the cables3d sweep, the real flat area under each mount (TEST_PLAN.md "
                 "section 1.4 test fit)")
    if not os.path.exists(CJ):
        R.not_run("altaay_lab/cables3d/cables3d.json not found (cables3d agent output not landed)")
        R.write()
        return
    D = json.load(open(CJ))
    net = V.load_netlist()
    R.inp(CJ, V.lab("wiring", "netlist.yaml"), V.lab("CABLE_MAP.md"), V.lab("BOM.md"), V.lab("MOUNTING.md"), URDF)
    C = {c["id"]: c for c in D["cables"]}
    active = [cb for cb in net["cables"] if cb.get("status", "active") == "active"]
    nwires = Counter(w["cable"] for w in net["wires"])
    kinds = {cp["id"]: cp.get("kind") for cp in net.get("components", [])}
    R.ev("cables3d.json %s (checked %s): %d cables, %d cable ends, %d retention items; netlist %d active cables" % (
        D["meta"].get("generated_utc", "?"), D["meta"].get("check", {}).get("generated_utc", "?"), len(C),
        len(D.get("cable_ends", [])), len(D.get("retention", [])), len(active)))
    missing = [cb["id"] for cb in active if cb["id"] not in C]
    for m in missing:
        R.find("FAIL", "cable %s has no 3D route" % m, fix="route it in cables3d/route_cables.py", where="altaay_lab/cables3d")
    # ---------------------------------------------------------------- coverage and cut lengths
    merges, unrouted, allw = [], [], []
    for cb in active:
        c = C.get(cb["id"])
        if not c:
            continue
        for r in c["runs"]:
            if not r.get("routed", True):
                unrouted.append("%s %s" % (cb["id"], r["name"]))
        mine = [w for w in net["wires"] if w["cable"] == cb["id"]]
        M, n_cond = series_merged(c["wires"], mine, kinds)
        for (a, b), (cut, pcs, j) in M.items():
            if j and (a, b) in {(w["from"], w["to"]) for w in c["wires"]}:
                merges.append("%s %s -> %s = %s = %s mm (inline splice %s, not routed in 3D)" % (
                    cb["id"], a, b, " + ".join("%s %s" % (x["from"].split(".")[0] + "-" + x["to"].split(".")[0], x["cut_mm"]) for x in pcs), cut, j))
        if len(c["wires"]) != n_cond:
            R.find("FAIL", "%s: %d wires in 3D, %d conductors in the netlist (%d wires)" % (cb["id"], len(c["wires"]), n_cond, nwires[cb["id"]]))
        for w in c["wires"]:
            netc = M.get((w["from"], w["to"]), (None,))[0]
            if netc != w.get("cut_mm"):
                R.find("FAIL", "%s %s -> %s: cut %s mm in 3D, %s mm in the netlist" % (cb["id"], w["from"], w["to"], w.get("cut_mm"), netc),
                       fix="sync cut_mm in cables3d.json from wiring/netlist.yaml (or re-route)", where="altaay_lab/cables3d")
            if w.get("runs") and w.get("length_max_mm") is not None:
                allw.append((cb["id"], w))
    for u in unrouted:
        R.find("FAIL", "run %s: no clear 3D path (straight placeholder)" % u, where="altaay_lab/cables3d")
    if merges:
        R.ev("series pieces summed: " + "; ".join(merges))
    # ---------------------------------------------------------------- length by chain through floating splices
    floating = {k for k, v in kinds.items() if v == "splice"} - set(SEATED)
    try:
        src = open(V.lab("cables3d", "check_cables.py")).read()
        m = re.search(r"INLINE\s*=\s*\{([^}]*)\}", src)
        inline = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    except OSError:
        inline = set()
    R.ev("floating splices (judged by chain): %s; fixed: %s" % (", ".join(sorted(floating)),
                                                                 "; ".join("%s %s" % (k, v) for k, v in sorted(SEATED.items()))))
    diff = (floating - inline) - {"JFI", "JFO"}       # JFI and JFO are summed into P7's routed conductors (series merge)
    if inline and (diff or (inline - floating)):
        R.find("WARN", "floating splices differ from cables3d/check_cables.py INLINE: only here %s, only there %s" % (
            sorted(diff), sorted(inline - floating)), fix="make the two lists the same", where="altaay_lab/cables3d/check_cables.py")
    CH = chains(allw, floating)
    worst = {}                                       # id(wire) -> (margin, chain)
    rows = []
    n_unknown = 0
    for ch in CH:
        cuts = [allw[k][1].get("cut_mm") for k in ch]
        if any(v is None for v in cuts):
            n_unknown += 1
            continue
        L = sum(allw[k][1]["length_max_mm"] for k in ch)
        cut = sum(cuts)
        margin = cut - (L + SLACK)
        rows.append((margin, ch, L, cut))
        for k in ch:
            if id(allw[k][1]) not in worst or margin < worst[id(allw[k][1])][0]:
                worst[id(allw[k][1])] = (margin, ch, L, cut)
    n_len = len(worst)

    def label(ch):
        return " + ".join("%s %s>%s %s" % (allw[k][0], allw[k][1]["from"], allw[k][1]["to"], allw[k][1]["cut_mm"]) for k in ch)
    cannot, no_slack = {}, {}
    for k, (cid, w) in enumerate(allw):
        if id(w) not in worst:
            continue
        margin, ch, L, cut = worst[id(w)]
        if L > cut:
            cannot.setdefault(cid, []).append((margin, w, ch, L, cut))
        elif margin < 0:
            no_slack.setdefault(cid, []).append((margin, w, ch, L, cut))
    # splice tails that pass only because their splice floats
    own_short = []
    for cid, w in allw:
        if w.get("cut_mm") and w["length_max_mm"] + SLACK > w["cut_mm"] and id(w) in worst and worst[id(w)][0] >= 0:
            if any(x.split(".")[0] in floating for x in (w["from"], w["to"])):
                own_short.append("%s %s>%s cut %s, route %.0f, chain margin %.0f mm" % (
                    cid, w["from"], w["to"], w["cut_mm"], w["length_max_mm"], worst[id(w)][0]))
    R.ev("length by chain: %d wires in %d chains (%d chains with an unpublished cut skipped: BEC leads); %d chains cannot reach "
         "(worst routed over the summed cut); %d wires reach but with less than the %.0f mm service slack (test fit); %d have "
         "the full slack" % (n_len, len(rows), n_unknown, sum(len(v) for v in cannot.values()), sum(len(v) for v in no_slack.values()),
                             SLACK, n_len - sum(len(v) for v in cannot.values()) - sum(len(v) for v in no_slack.values())))
    if own_short:
        R.ev("wires short of the slack alone that pass by chain (their splice floats): " + "; ".join(own_short))
    for cid, lst in sorted(cannot.items()):
        margin, w, ch, L, cut = min(lst, key=lambda x: x[0])
        R.find("FAIL", "%s: %d wire(s) cannot reach: chain %s routes %.0f mm over the joint ranges, cut %s mm, too short by %.0f "
               "mm before any slack" % (cid, len(lst), label(ch), L, cut, L - cut),
               fix="wiring/netlist.yaml %s: lengthen the longest made wire of the chain by %d mm (worst %.0f + 2 x 20 mm slack), "
                   "and the same in CABLE_MAP.md" % (cid, int(math.ceil(-margin / 10.0) * 10), L),
               where="altaay_lab/wiring/netlist.yaml")
    for cid, lst in sorted(no_slack.items()):
        margin, w, ch, L, cut = min(lst, key=lambda x: x[0])
        g = w.get("gauge", "")
        fix = FIXED_LEN.get(g) or ("cut %s -> %s %d mm (the chain then has the 2 x 20 mm slack), or keep the cut and test fit "
                                   "it (TEST_PLAN.md 1.4)" % (w["from"], w["to"], int(math.ceil((w["cut_mm"] - margin) / 10.0) * 10)))
        R.find("WARN", "%s: %d wire(s) reach with only %.0f mm to spare (worst chain %s, %.0f mm routed, cut %s mm), under the "
               "2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule)" % (cid, len(lst), cut - L, label(ch), L, cut),
               fix=fix, where="altaay_lab/wiring/netlist.yaml" if g not in FIXED_LEN else None)
    # ---------------------------------------------------------------- crossings and service loops (recomputed)
    rt_ranges, rt_path = runtime_head_ranges()
    kin = Kin()
    n_loop = n_ok = n_ok_rt = 0
    bad, bad_rt, mism, joint_miss = [], [], [], []
    ret = D.get("retention", [])
    for cb in active:
        c = C.get(cb["id"])
        if not c:
            continue
        joints_3d = set()
        for r in c["runs"]:
            spans = {tuple(sp["span"]): sp for sp in r.get("spans", [])}
            for sp in r.get("spans", []):
                joints_3d |= set(sp["joints"])
            loops = {tuple(lp["span"]): lp for lp in r.get("service_loops", [])}
            if r.get("name", "").startswith("tail_"):
                continue                       # data lead tails share the power tail run (same points)
            for key, sp in spans.items():
                if not sp["joints"]:
                    continue
                n_loop += 1
                lp = loops.get(key)
                if not lp:
                    bad.append((0.0, c["id"], r["name"], "+".join(sp["joints"]), None, "no free loop between ties recorded"))
                    continue
                x = loop_check(kin, r, lp, rt_ranges)
                od = x["od"] = r["d_mm"]
                ok = x["bend"] >= BEND_MIN * od - 0.05 and x["storage"] >= BEND_MIN * od - 0.05
                ok_rt = x["bend_rt"] >= BEND_MIN * od - 0.05 and x["storage_rt"] >= BEND_MIN * od - 0.05
                n_ok += ok
                n_ok_rt += ok_rt
                worst_r = min(x["bend"], x["storage"])
                if not ok:
                    bad.append((worst_r / od, c["id"], r["name"], "+".join(sp["joints"]), x, ""))
                if not ok_rt:
                    bad_rt.append((min(x["bend_rt"], x["storage_rt"]) / od, c["id"], "+".join(sp["joints"])))
                # a tie (or the plug) at both ends of the loop
                for side, a_mm, anc in ((0, lp["ties_at_mm"][0], lp.get("anchor_a")), (1, lp["ties_at_mm"][1], lp.get("anchor_b"))):
                    if anc:
                        continue
                    pts = r["points"]
                    P = np.array([(kin.T(p["link"], {}) @ np.r_[p["p"], 1.0])[:3] for p in pts])
                    acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
                    k = int(np.clip(np.searchsorted(acc, a_mm) - 1, 0, len(P) - 2))
                    t = (a_mm - acc[k]) / max(float(np.linalg.norm(P[k + 1] - P[k])), 1e-9)
                    q = P[k] + (P[k + 1] - P[k]) * t
                    link = pts[key[side]]["link"]
                    near = [rr for rr in ret if c["id"] in rr["cables"] and rr["link"] == link
                            and np.linalg.norm(np.array(rr["center_mm"]) - q) <= 8.0]
                    if not near:
                        mism.append("%s %s at %s %.0f mm" % (c["id"], r["name"], "+".join(sp["joints"]), a_mm))
        want = set(cb.get("joints") or [])
        if want - joints_3d:
            joint_miss.append(cb["id"])
            R.find("FAIL", "%s: netlist joints %s are not crossed by a free span in the 3D route (no service loop)" % (
                cb["id"], sorted(want - joints_3d)), fix="route a free span (loop) across each joint", where="altaay_lab/cables3d")
        if joints_3d - want:
            R.find("WARN", "%s: the 3D route crosses %s, which the netlist does not list for this cable" % (cb["id"], sorted(joints_3d - want)),
                   fix="add the joint to the cable's 'joints' in wiring/netlist.yaml (it feeds the CABLE_MAP length rule)",
                   where="altaay_lab/wiring/netlist.yaml")
    R.ev("service loops (recomputed from the route and robot.urdf, 61 samples per joint): %d crossings; %d meet 3 x OD in both "
         "models over the full URDF range, %d within the Runtime head ranges (%s)" % (
             n_loop, n_ok, n_ok_rt, ("%s from %s" % (rt_ranges, os.path.relpath(rt_path, os.path.dirname(V.REPO))))
             if rt_ranges else "Runtime checkout not found at %s: URDF ranges used" % rt_path))
    bad.sort(key=lambda b: b[0])
    if bad:
        R.find("WARN", "%d of %d joint loops cannot reach 3 x OD over the full URDF range inside the route room: %s" % (
            len(bad), n_loop, "; ".join(
                "%s at %s: free %.0f mm between the ties, bend R %.1f mm, length storage R %.1f mm (loop %.0f mm over a %.1f mm "
                "closest tie-to-tie chord), worst %.1f x OD, needs 3 x OD (%.1f mm)" % (
                    b[1], b[3], b[4]["free"], b[4]["bend"], b[4]["storage"], b[4]["length"], b[4]["chord"], b[0],
                    BEND_MIN * b[4]["od"]) if b[4] else
                "%s %s at %s: %s" % (b[1], b[2], b[3], b[5]) for b in bad)),
            fix="turn the joint through its whole range by hand with the loop dressed and look for a kink or a pull at the ties "
                "(TEST_PLAN.md section 1.4); %d of them meet the rule within the Runtime head ranges" % (len(bad) - len(bad_rt)),
            where="altaay_lab/TEST_PLAN.md")
    if mism:
        R.find("WARN", "%d loop ends have no retention item within 8 mm on the same link: %s" % (len(mism), "; ".join(mism[:10])),
               fix="re-run cables3d/seats_ties.py", where="altaay_lab/cables3d")
    # ---------------------------------------------------------------- retention
    grp = Counter()
    mount_types = Counter()
    open_pts, small = [], []
    for t in ret:
        k = str(t.get("kind"))
        if k == "adhesive tie mount":
            typ = (t.get("mount_fit") or {}).get("type")
            mount_types[typ or "none"] += 1
            if typ == "MB2APT":
                small.append(t["id"])
        grp[k] += 1
        if t.get("open"):
            open_pts.append(t)
    uses_tie = len(ret)                   # every retention item is closed with one line 32 tie
    R.ev("retention: %d tie points: %s; stick-on mount spots by fit (exact-ray flat patch, cables3d): MB3A 19 x 19 mm %d, "
         "only the smaller MB2APT 13 x 13 mm %d, no flat patch %d; open (nothing holds them yet) %d" % (
             len(ret), ", ".join("%d %s" % (v, k) for k, v in grp.most_common()), mount_types.get("MB3A", 0),
             mount_types.get("MB2APT", 0), mount_types.get("none", 0), len(open_pts)))
    need32, need34 = bom_need("32") or "", bom_need("34") or ""
    m32 = re.search(r"(\d+) along the cables", need32)
    m34 = re.match(r"\s*(\d+)", need34)
    R.ev("BOM line 32 Need: %s; line 34 Need: %s" % (need32[:160], need34[:160]))
    if not m32 or int(m32.group(1)) != uses_tie:
        R.find("WARN", "BOM line 32 counts %s ties along the cables, cables3d.json has %d tie points (one tie each)" % (
            m32.group(1) if m32 else "?", uses_tie), fix="BOM.md line 32 Need from cables3d.json retention", where="altaay_lab/BOM.md")
    if not m34 or int(m34.group(1)) != mount_types.get("MB3A", 0):
        R.find("WARN", "BOM line 34 counts %s MB3A mounts, cables3d.json has %d spots where an MB3A fits" % (
            m34.group(1) if m34 else "?", mount_types.get("MB3A", 0)), fix="BOM.md line 34 Need from cables3d.json retention",
            where="altaay_lab/BOM.md")
    if small:
        R.find("WARN", "%d stick-on mount spots have no flat 19 x 19 mm patch for the BOM line 34 MB3A but fit the smaller "
               "HellermannTyton MB2APT (13 x 13 x 4.1 mm, not in the BOM): %s" % (len(small), ", ".join(small)),
               fix="proposal for the lead: a BOM line for a 13 x 13 mm stick-on tie mount (MB2APT 151-00996 or equal), or fit "
                   "these spots at the TEST_PLAN.md 1.4 test fit", where="altaay_lab/BOM.md")
    if open_pts:
        R.find("WARN", "%d tie points have nothing to hold them yet (no printed feature, no flat patch for a stick-on mount, no "
               "anchored neighbour cable): %s" % (len(open_pts), "; ".join("%s %s on %s (%s)" % (
                   t["id"], ",".join(t["cables"]), t["link"], "free air" if t["kind"] == "cable tie" else "mount spot, no flat patch")
                   for t in open_pts)),
               fix="printed cable guides or a route change at these points (a design change: proposed D25); until then a tie "
                   "around the bundle only, checked at the TEST_PLAN.md 1.4 test fit", where="altaay_lab/DECISIONS.md")
    chk = Counter(c.get("check") for c in C.values())
    R.ev("cables3d's own check field: %s" % dict(chk))
    if chk.get("pending") == len(C):
        R.find("WARN", "cables3d.json is not checked by its own checker yet (check_cables.py: every cable 'pending')")
    json.dump(dict(bad=[(b[0], b[1], b[2], b[3], b[4]) for b in bad], chains=[(m, label(ch), L, cut) for m, ch, L, cut in sorted(rows, key=lambda x: x[0])]),
              open(os.path.join(V.out_dir(), "c3_details.json"), "w"), indent=0, default=str)
    R.key("%d of %d active cables routed in 3D (%d runs still straight placeholders); by chain: %d wires cannot reach, %d with "
          "less than 40 mm slack; %d of %d joint loops meet 3 x OD (%d within the Runtime head ranges); %d tie points: %s; %d open" % (
              len(active) - len(missing), len(active), len(unrouted), sum(len(v) for v in cannot.values()),
              sum(len(v) for v in no_slack.values()), n_ok, n_loop, n_ok_rt, len(ret),
              ", ".join("%d %s" % (v, k) for k, v in grp.most_common()), len(open_pts)))
    R.write()


if __name__ == "__main__":
    main()
