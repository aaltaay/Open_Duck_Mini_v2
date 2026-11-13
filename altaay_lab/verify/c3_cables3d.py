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
             2 x 20 mm service slack, one per fixed end) <= summed cut (kit cables: the 150 mm kit length). The
             routed length of a twisted made cable is multiplied by its take-up at the shortest lay (wiring/netlist.yaml
             cable 'twist', D25; NASA-STD-8739.4A 7.2.16 to 7.2.18). Routed longer than the cut: FAIL; shorter but
             under the 40 mm slack: WARN (test fit)
  loops      every joint the netlist lists for a cable is crossed by its 3D route; every crossing has a free loop
             between two ties (cables3d.json service_loops: ties_at_mm, or the plug where the loop runs to a connector).
             Two crossings a few mm apart with no tie between them (head_pitch and head_yaw: the link head_pitch_to_yaw
             carries 0 to 3 mm of route) are one loop (service_loops "spans"): its cable need at a pose is the fixed
             pieces, the route on the middle link and the sum of the span chords.
             Recomputed here from the route and the URDF (61 samples per joint over the URDF range): bend R = free
             length / largest joint angle from zero; length storage R = the cable the loop needs at the farthest pose
             (fixed pieces + span chord) bowed as one circular arc over the closest tie-to-tie chord. Both >= 3 x the
             run diameter (NASA-STD-8739.4A Change 4, Table 7-1, overall harness of AWG 10 or smaller without coax:
             minimum 3 x OD, optimum 10 x OD). The same is reported within the head ranges of the Runtime gamepad code
  retention  every tie point and what holds it (D25): an existing printed feature, a stick-on tie mount (BOM line 34
             MB3A 19 x 19 mm or line 34b Panduit ABM1M-AT-C 12.7 x 12.7 mm, with the flat-patch check cables3d
             records; some on the STS3215 case), a tie to an anchored neighbour cable (D25 i), a drilled tie-hole pair
             through a printed part after printing (D25 ii, print/PRINT_PLAN.md After printing), or a tie round the
             bundle only, checked at the TEST_PLAN 1.4 test fit ("bundle tie, test fit", D25 as decided). An open point
             must carry a named plan (FAIL without one). BOM lines 32, 34 and 34b Need vs these counts
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
             "FPC ribbon": "fixed-length FPC: keep the 150 mm BOM E7 cable and test fit it (TEST_PLAN.md 1.4, test order TO9); "
                           "the fallback named in the BOM E7 note (D25) is the 200 mm Raspberry Pi Standard-Mini camera cable, "
                           "Adafruit 5818 (22-pin 0.5 mm to 15-pin 1 mm)"}


def twist_factors(net):
    """cable id -> (take-up factor, branch or None) from the netlist cable 'twist' records (D25)"""
    out = {}
    for cb in net.get("cables", []):
        tw = cb.get("twist") or {}
        if tw.get("lay_mm") and tw.get("takeup_max"):
            m = str(tw.get("wires", ""))
            out[cb["id"]] = (float(tw["takeup_max"]), m.split()[1] if m.startswith("branch ") else None)
    return out


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
    """recompute one service loop from the route and the URDF: (bend R, storage R, both within the Runtime ranges).
    A merged loop (two spans, no tie on the short link between them) is one free section: its cable need at a pose is
    the fixed pieces outside the spans, the route on the middle link and the sum of the span chords at that pose"""
    pts = r["points"]
    spans = lp.get("spans") or [lp["span"]]
    i0, i9 = spans[0][0], spans[-1][1]
    P = np.array([(kin.T(p["link"], {}) @ np.r_[p["p"], 1.0])[:3] for p in pts])
    Bk = [p["link"] for p in pts]
    acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    a0, a1 = max(lp["ties_at_mm"][0], 0.0), min(lp["ties_at_mm"][1], acc[-1])

    def along(a):
        k = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
        t = (a - acc[k]) / max(float(np.linalg.norm(P[k + 1] - P[k])), 1e-9)
        return P[k] + (P[k + 1] - P[k]) * t
    la, lb = Bk[i0], Bk[i9]
    A0 = np.linalg.inv(kin.T(la, {})) @ np.r_[along(a0), 1.0]
    B0 = np.linalg.inv(kin.T(lb, {})) @ np.r_[along(a1), 1.0]
    ends = [(Bk[a], np.linalg.inv(kin.T(Bk[a], {})) @ np.r_[P[a], 1.0], Bk[b], np.linalg.inv(kin.T(Bk[b], {})) @ np.r_[P[b], 1.0])
            for a, b in spans]
    js = lp["joints"]
    fixed = (acc[i0] - a0) + (a1 - acc[i9]) + sum(acc[spans[k + 1][0]] - acc[spans[k][1]] for k in range(len(spans) - 1))

    def sweep(ranges):
        n = {1: 61, 2: 21, 3: 9}.get(len(js), 5)
        grids = np.meshgrid(*[np.linspace(ranges[j][0], ranges[j][1], n) for j in js], indexing="ij")
        cmin, smax = math.inf, 0.0
        for q in zip(*[g.ravel() for g in grids]):
            cfg = dict(zip(js, q))
            Ta, Tb = kin.T(la, cfg), kin.T(lb, cfg)
            cmin = min(cmin, float(np.linalg.norm((Ta @ A0)[:3] - (Tb @ B0)[:3])))
            smax = max(smax, sum(float(np.linalg.norm((kin.T(l1, cfg) @ p1)[:3] - (kin.T(l2, cfg) @ p2)[:3]))
                                 for l1, p1, l2, p2 in ends))
        return cmin, smax
    cmin, smax = sweep(kin.rng)
    length = fixed + smax
    th = sum(max(abs(kin.rng[j][0]), abs(kin.rng[j][1])) for j in js)
    free = a1 - a0
    out = dict(free=free, length=length, chord=cmin, bend=free / max(th, 1e-9), storage=arc_radius(cmin, length), th=th,
               spans=len(spans))
    rt = dict(kin.rng)
    rt.update(rt_ranges or {})
    if any(j in (rt_ranges or {}) for j in js):
        cmin_rt, _ = sweep(rt)               # the loop keeps the length the full range needs (the full loop is built)
        th_rt = sum(max(abs(rt[j][0]), abs(rt[j][1])) for j in js)
        out.update(bend_rt=free / max(th_rt, 1e-9), storage_rt=arc_radius(cmin_rt, length), th_rt=th_rt)
    else:
        out.update(bend_rt=out["bend"], storage_rt=out["storage"], th_rt=th)
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
    missing = [cb["id"] for cb in active if cb["id"] not in C and not cb.get("no_route")]
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
    TW = twist_factors(net)

    def routed(k):
        cid, w = allw[k]
        f, br = TW.get(cid, (1.0, None))
        return w["length_max_mm"] * (f if br is None or w.get("branch") == br else 1.0)
    made = {"16 AWG", "20 AWG", "22 AWG", "26 AWG"}
    no_dec = [cb["id"] for cb in active if sum(1 for w in net["wires"] if w["cable"] == cb["id"] and w.get("gauge") in made) >= 2
              and not isinstance(cb.get("twist"), dict)]
    R.ev("twist (D25, NASA-STD-8739.4A 7.2.16 to 7.2.18): %d made multi-wire cables twisted (%s); %d not, with the reason in "
         "the netlist; chain lengths below carry the take-up at the shortest lay" % (
             len(TW), ", ".join("%s x%.3f%s" % (k, v[0], " branch " + v[1] if v[1] else "") for k, v in sorted(TW.items())),
             sum(1 for cb in active if isinstance(cb.get("twist"), dict) and not cb["twist"].get("lay_mm"))))
    if no_dec:
        R.find("WARN", "made multi-wire cables with no twist decision in the netlist: %s" % ", ".join(no_dec),
               fix="add twist {lay_mm, ...} or {lay_mm: null, note} to each (D25)", where="altaay_lab/wiring/netlist.yaml")
    worst = {}                                       # id(wire) -> (margin, chain)
    rows = []
    n_unknown = 0
    for ch in CH:
        cuts = [allw[k][1].get("cut_mm") for k in ch]
        if any(v is None for v in cuts):
            n_unknown += 1
            continue
        L = sum(routed(k) for k in ch)
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
    for k_, (cid, w) in enumerate(allw):
        if w.get("cut_mm") and routed(k_) + SLACK > w["cut_mm"] and id(w) in worst and worst[id(w)][0] >= 0:
            if any(x.split(".")[0] in floating for x in (w["from"], w["to"])):
                own_short.append("%s %s>%s cut %s, route %.0f, chain margin %.0f mm" % (
                    cid, w["from"], w["to"], w["cut_mm"], routed(k_), worst[id(w)][0]))
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
    n_cross = n_loop = n_ok = n_ok_rt = 0
    bad, bad_rt, mism, joint_miss, merged_rows, yaw_rows = [], [], [], [], [], []
    ret = D.get("retention", [])
    for cb in active:
        c = C.get(cb["id"])
        if not c:
            continue
        joints_3d = set()
        for r in c["runs"]:
            for sp in r.get("spans", []):
                joints_3d |= set(sp["joints"])
            if r.get("name", "").startswith("tail_"):
                continue                       # data lead tails share the power tail run (same points)
            cover = {}
            for lp in r.get("service_loops", []):
                for sp in (lp.get("spans") or [lp["span"]]):
                    cover[tuple(sp)] = lp
            for sp in r.get("spans", []):
                if not sp["joints"]:
                    continue
                n_cross += 1
                if tuple(sp["span"]) not in cover:
                    bad.append((0.0, c["id"], r["name"], "+".join(sp["joints"]), None, "no free loop between ties recorded"))
            for lp in r.get("service_loops", []):
                n_loop += 1
                x = loop_check(kin, r, lp, rt_ranges)
                od = x["od"] = r["d_mm"]
                ok = x["bend"] >= BEND_MIN * od - 0.05 and x["storage"] >= BEND_MIN * od - 0.05
                ok_rt = x["bend_rt"] >= BEND_MIN * od - 0.05 and x["storage_rt"] >= BEND_MIN * od - 0.05
                n_ok += ok
                n_ok_rt += ok_rt
                worst_r = min(x["bend"], x["storage"])
                jn = "+".join(lp["joints"])
                if not ok:
                    bad.append((worst_r / od, c["id"], r["name"], jn, x, ""))
                if not ok_rt:
                    bad_rt.append((min(x["bend_rt"], x["storage_rt"]) / od, c["id"], jn))
                if x["spans"] > 1:
                    merged_rows.append("%s %s: free %.0f mm, bend R %.1f, storage R %.1f mm (loop %.0f over a %.1f mm chord), "
                                       "needs %.1f" % (c["id"], jn, x["free"], x["bend"], x["storage"], x["length"], x["chord"],
                                                       BEND_MIN * od))
                if "head_yaw" in lp["joints"]:
                    yaw_rows.append("%s %s: full URDF range bend R %.1f, storage R %.1f; Runtime ranges bend R %.1f, storage R "
                                    "%.1f; needs %.1f mm (%s)" % (c["id"], jn, x["bend"], x["storage"], x["bend_rt"],
                                                                  x["storage_rt"], BEND_MIN * od, "meets" if ok else "under"))
                # a tie (or the plug) at both ends of the loop
                spans = lp.get("spans") or [lp["span"]]
                for side, a_mm, anc in ((0, lp["ties_at_mm"][0], lp.get("anchor_a")), (1, lp["ties_at_mm"][1], lp.get("anchor_b"))):
                    if anc:
                        continue
                    pts = r["points"]
                    P = np.array([(kin.T(p["link"], {}) @ np.r_[p["p"], 1.0])[:3] for p in pts])
                    acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
                    k = int(np.clip(np.searchsorted(acc, a_mm) - 1, 0, len(P) - 2))
                    t = (a_mm - acc[k]) / max(float(np.linalg.norm(P[k + 1] - P[k])), 1e-9)
                    q = P[k] + (P[k + 1] - P[k]) * t
                    link = pts[spans[0][0] if side == 0 else spans[-1][1]]["link"]
                    near = [rr for rr in ret if c["id"] in rr["cables"] and rr["link"] == link
                            and min(np.linalg.norm(np.array(x) - q) for x in
                                    [rr["center_mm"]] + [a["center_mm"] for a in rr.get("also_holds", [])]) <= 8.0]
                    if not near:
                        mism.append("%s %s at %s %.0f mm" % (c["id"], r["name"], jn, a_mm))
        want = set(cb.get("joints") or [])
        if want - joints_3d:
            joint_miss.append(cb["id"])
            R.find("FAIL", "%s: netlist joints %s are not crossed by a free span in the 3D route (no service loop)" % (
                cb["id"], sorted(want - joints_3d)), fix="route a free span (loop) across each joint", where="altaay_lab/cables3d")
        if joints_3d - want:
            R.find("WARN", "%s: the 3D route crosses %s, which the netlist does not list for this cable" % (cb["id"], sorted(joints_3d - want)),
                   fix="add the joint to the cable's 'joints' in wiring/netlist.yaml (it feeds the CABLE_MAP length rule)",
                   where="altaay_lab/wiring/netlist.yaml")
    R.ev("service loops (recomputed from the route and robot.urdf, 61 samples per joint, 21 x 21 for a two-joint loop): %d "
         "crossings in %d loops (%d loops span two crossings); %d loops meet 3 x OD in both models over the full URDF range, "
         "%d within the Runtime head ranges (%s)" % (
             n_cross, n_loop, len(merged_rows), n_ok, n_ok_rt, ("%s from %s" % (rt_ranges, os.path.relpath(rt_path, os.path.dirname(V.REPO))))
             if rt_ranges else "Runtime checkout not found at %s: URDF ranges used" % rt_path))
    if merged_rows:
        R.ev("two-crossing loops (no tie on the short link between them): " + "; ".join(merged_rows))
    if yaw_rows:
        R.ev("head yaw loops: " + "; ".join(yaw_rows))
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
    # ---------------------------------------------------------------- retention (D25)
    grp = Counter()
    mount_types = Counter()
    open_pts, on_case, holes, neigh, test_fit = [], [], [], [], []
    ids = {t["id"]: t for t in ret}
    for t in ret:
        k = str(t.get("kind"))
        if k == "adhesive tie mount":
            mf = t.get("mount_fit") or {}
            mount_types[mf.get("type") or "none"] += 1
            if mf.get("on_servo_case"):
                on_case.append(t)
        elif k == "drilled printed feature":
            holes.append(t)
        elif k == "cable tie to a neighbour cable":
            neigh.append(t)
        if t.get("hold") == "bundle tie, test fit":
            k = "bundle tie, test fit"
            test_fit.append(t)
        grp[k] += 1
        if t.get("open"):
            open_pts.append(t)
    uses_tie = len(ret)                   # every retention item is closed with one line 32 tie (a shared anchor: one tie)
    n_join = sum(len(t.get("also_holds", [])) for t in ret)
    R.ev("retention: %d tie points: %s; stick-on mounts by fit (exact-ray flat patch, cables3d): MB3A 19 x 19 mm (BOM 34) %d, "
         "ABM1M-AT-C 12.7 x 12.7 mm (BOM 34b) %d, of them on an STS3215 case %d; no fit %d; drilled tie-hole pairs %d; tied to a "
         "neighbour %d; bundle tie, test fit %d; open %d; %d tie points share the anchor of a nearby one (one anchor per "
         "spot, one tie round both)" % (
             len(ret), ", ".join("%d %s" % (v, k) for k, v in grp.most_common()), mount_types.get("MB3A", 0),
             mount_types.get("ABM1M", 0), len(on_case), mount_types.get("none", 0), len(holes), len(neigh), len(test_fit),
             len(open_pts), n_join))
    # drilled pairs: the numbers seats_ties checked with exact rays, re-read here against the D25 rule
    hole_bad, hole_rows = [], []
    for t in holes:
        h = t.get("tie_holes") or {}
        sp, walls, dmm = h.get("spacing_mm") or 0.0, h.get("wall_mm") or [], h.get("hole_d_mm")
        need_sp = max((h.get("for_bundle_mm") or t["bundle_d_mm"]) + 4.0, 4.0 + 1.6) - 0.05   # bundle it was drilled for
        strap = (math.pi / 2 + 1.0) * t["bundle_d_mm"] + sum(walls) + sp
        hole_rows.append("%s %s on %s: 2 x %.1f mm, %.1f mm apart, walls %s mm, %.0f mm from the cable line, strap path about %.0f "
                         "mm, %s" % (t["id"], ",".join(t["cables"]), h.get("part"), dmm or 0, sp, "/".join("%.1f" % w for w in walls),
                                     h.get("from_cable_mm") or 0, strap,
                                     "no moving part near" if (h.get("sweep_gap_mm") or 0) > 1e6 else
                                     "%.1f mm from moving parts over the sweep" % h["sweep_gap_mm"]))
        if dmm != 4.0 or sp < need_sp or not walls or min(walls) < 1.6 or max(walls) > 12.0 or (h.get("sweep_gap_mm") or 0) < 1.0:
            hole_bad.append(t["id"])
    if hole_rows:
        R.ev("drilled tie-hole pairs (D25 ii; 4.0 mm, the BOM T14 bit; edge distance and web >= 1.6 mm; walls 1.6 to 12 mm; screws, "
             "inserts and empty holes >= 1.6 mm off; 1.5 mm free behind the wall; >= 1 mm from moving parts; print/PRINT_PLAN.md "
             "After printing): " + "; ".join(hole_rows))
    if hole_bad:
        R.find("FAIL", "drilled tie-hole pairs outside the D25 rule: %s" % ", ".join(hole_bad),
               fix="re-run cables3d/seats_ties.py", where="altaay_lab/cables3d")
    bad_n = [t["id"] for t in neigh if t.get("anchor_tie") not in ids or ids[t["anchor_tie"]].get("open")
             or ids[t["anchor_tie"]]["kind"] in ("cable tie", "cable tie to a neighbour cable")]
    if neigh:
        R.ev("tied to a neighbour cable (D25 i): " + "; ".join("%s %s to %s (held by %s)" % (
            t["id"], ",".join(t["cables"]), t.get("tied_to"), t.get("anchor_tie")) for t in neigh))
    if bad_n:
        R.find("FAIL", "neighbour ties whose anchor tie is not itself anchored: %s" % ", ".join(bad_n),
               fix="re-run cables3d/seats_ties.py", where="altaay_lab/cables3d")
    if on_case:
        R.find("WARN", "%d stick-on mounts sit on an STS3215 servo case (no printed face or hole pair fits there): %s; the hold of "
               "the mount tape on the case plastic is not published" % (len(on_case), "; ".join("%s %s on %s (%s)" % (
                   t["id"], ",".join(t["cables"]), t["part"], t["mount_fit"]["type"]) for t in on_case)),
               fix="press and pull check each one at the dry fit (TEST_PLAN.md 1.4); a mount that lifts gets the line 32 tie "
                   "round the bundle only and is reported", where="altaay_lab/TEST_PLAN.md")
    need32, need34, need34b = bom_need("32") or "", bom_need("34") or "", bom_need("34b") or ""
    m32 = re.search(r"(\d+) along the cables", need32)
    m34 = re.match(r"\s*(\d+)", need34)
    m34b = re.match(r"\s*(\d+)", need34b)
    R.ev("BOM line 32 Need: %s; line 34 Need: %s; line 34b Need: %s" % (need32[:160], need34[:120], need34b[:120]))
    if not m32 or int(m32.group(1)) != uses_tie:
        R.find("WARN", "BOM line 32 counts %s ties along the cables, cables3d.json has %d tie points (one tie each)" % (
            m32.group(1) if m32 else "?", uses_tie), fix="BOM.md line 32 Need from cables3d.json retention", where="altaay_lab/BOM.md")
    if not m34 or int(m34.group(1)) != mount_types.get("MB3A", 0):
        R.find("WARN", "BOM line 34 counts %s MB3A mounts, cables3d.json has %d spots where an MB3A fits" % (
            m34.group(1) if m34 else "?", mount_types.get("MB3A", 0)), fix="BOM.md line 34 Need from cables3d.json retention",
            where="altaay_lab/BOM.md")
    if not m34b or int(m34b.group(1)) != mount_types.get("ABM1M", 0):
        R.find("WARN", "BOM line 34b counts %s ABM1M-AT-C mounts, cables3d.json has %d spots that take one" % (
            m34b.group(1) if m34b else "?", mount_types.get("ABM1M", 0)), fix="BOM.md line 34b Need from cables3d.json retention",
            where="altaay_lab/BOM.md")
    if test_fit:
        R.find("WARN", "%d tie points are a tie round the bundle only (no printed feature, mount, hole pair or anchored "
               "neighbour fits; D25: no new printed parts, no STL change): %s" % (len(test_fit), "; ".join("%s %s on %s" % (
                   t["id"], ",".join(t["cables"]), t["link"]) for t in test_fit)),
               fix="check each at both joint limits at the TEST_PLAN.md 1.4 test fit; a drilled tie-hole pair or a printed "
                   "anchor only if the bundle reaches a moving part", where="altaay_lab/TEST_PLAN.md")
        tried = [t["id"] for t in test_fit if "route change tried" in (t.get("plan") or "")]
        if tried:
            R.ev("route changes tried and not kept (cuts would not fit with the slack): " + "; ".join(
                "%s: route change tried%s" % (t["id"], t["plan"].split("; route change tried", 1)[1]) for t in test_fit if t["id"] in tried))
    no_plan = [t for t in open_pts if not t.get("plan")]
    if open_pts:
        R.find("WARN", "%d tie points are open (no printed feature, mount, hole pair or anchored neighbour fits), each with a "
               "named plan: %s" % (len(open_pts), "; ".join("%s %s on %s: %s" % (
                   t["id"], ",".join(t["cables"]), t["link"], t.get("plan") or "NO PLAN") for t in open_pts)),
               fix="carry out the named plan; check at the TEST_PLAN.md 1.4 dry fit", where="altaay_lab/HARNESS_BUILD.md")
    if no_plan:
        R.find("FAIL", "%d open tie points have no named plan (D25: nothing open without one): %s" % (
            len(no_plan), ", ".join(t["id"] for t in no_plan)), fix="give each a plan in cables3d/seats_ties.py",
            where="altaay_lab/cables3d")
    chk = Counter(c.get("check") for c in C.values())
    R.ev("cables3d's own check field: %s" % dict(chk))
    if chk.get("pending") == len(C):
        R.find("WARN", "cables3d.json is not checked by its own checker yet (check_cables.py: every cable 'pending')")
    json.dump(dict(bad=[(b[0], b[1], b[2], b[3], b[4]) for b in bad], chains=[(m, label(ch), L, cut) for m, ch, L, cut in sorted(rows, key=lambda x: x[0])]),
              open(os.path.join(V.out_dir(), "c3_details.json"), "w"), indent=0, default=str)
    R.key("%d of %d active cables routed in 3D (%d runs still straight placeholders); by chain (twist take-up in): %d wires "
          "cannot reach, %d with less than 40 mm slack; %d of %d joint loops (%d crossings) meet 3 x OD (%d within the Runtime "
          "head ranges); %d tie points: %s (MB3A %d, ABM1M %d); %d open" % (
              len(active) - len(missing), len(active), len(unrouted), sum(len(v) for v in cannot.values()),
              sum(len(v) for v in no_slack.values()), n_ok, n_loop, n_cross, n_ok_rt, len(ret),
              ", ".join("%d %s" % (v, k) for k, v in grp.most_common()), mount_types.get("MB3A", 0),
              mount_types.get("ABM1M", 0), len(open_pts)))
    R.write()


if __name__ == "__main__":
    main()
