"""C3: every active cable has a 3D route (altaay_lab/cables3d/cables3d.json, cables3d agent) whose worst-case length plus
the stated slack fits its cut length, and every joint crossing has a service loop.

  coverage   every active netlist cable is in cables3d.json, every run routed, every netlist wire present with the
             same cut length; netlist pieces joined in series at a splice that the 3D record does not route (a lead and
             its extension, e.g. P7 at JFI and JFO) count as one conductor with the summed cut length
  length     per wire: worst routed length over the joint ranges + 40 mm (CABLE_MAP.md length rule: 2 x 20 mm
             service slack) <= cut length (kit cables: the 150 mm kit length)
  crossings  every joint the netlist lists for a cable is crossed by its 3D route, and every crossing (free span) has a
             service loop: the span's length change (max - min) is stored as an arc over the shortest chord; its
             radius is compared with 3 x the run diameter (NASA-STD-8739.4A table 7-1 minimum, as cables3d cites)
  retention  ties, mounts and guides in cables3d.json, and the ones with no CAD feature to hold them (gap)
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c3_cables3d.py
"""
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

SLACK = 40.0


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
BEND_MIN = 3.0
CJ = V.lab("cables3d", "cables3d.json")


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


def main():
    R = V.Result("C3", "Every active cable has a 3D route whose worst length plus slack fits its cut, and a service loop at every joint",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py",
                 "Every active cable: route present and routed, wires and cut lengths as in the netlist, worst length over the "
                 "joint ranges + 40 mm vs cut, netlist joints vs 3D crossings, loop radius at every crossing vs 3 x OD, ties",
                 "Real cable stiffness and where the slack sits, connector back-shell sizes (Molex drawing not reached), "
                 "rubbing against moving parts beyond the cables3d sweep (TEST_PLAN.md section 1.4 test fit)")
    if not os.path.exists(CJ):
        R.not_run("altaay_lab/cables3d/cables3d.json not found (cables3d agent output not landed)")
        R.write()
        return
    D = json.load(open(CJ))
    net = V.load_netlist()
    R.inp(CJ, V.lab("wiring", "netlist.yaml"), V.lab("CABLE_MAP.md"))
    C = {c["id"]: c for c in D["cables"]}
    active = [cb for cb in net["cables"] if cb.get("status", "active") == "active"]
    nwires = Counter(w["cable"] for w in net["wires"])
    kinds = {cp["id"]: cp.get("kind") for cp in net.get("components", [])}
    merges = []
    R.ev("cables3d.json %s: %d cables, %d cable ends, %d retention items; netlist %d active cables" % (
        D["meta"].get("generated_utc", "?"), len(C), len(D.get("cable_ends", [])), len(D.get("retention", [])), len(active)))
    missing = [cb["id"] for cb in active if cb["id"] not in C]
    for m in missing:
        R.find("FAIL", "cable %s has no 3D route" % m, fix="route it in cables3d/route_cables.py", where="altaay_lab/cables3d")
    n_len = n_short = n_span = n_tight = 0
    worst_margin = []
    tight = []
    unrouted = []
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
                R.find("FAIL", "%s %s -> %s: cut %s mm in 3D, %s mm in the netlist" % (cb["id"], w["from"], w["to"], w.get("cut_mm"), netc))
            cut = w.get("cut_mm")
            if not cut or w.get("length_max_mm") is None:
                continue
            n_len += 1
            need = w["length_max_mm"] + SLACK
            worst_margin.append((cut - need, cb["id"], w["from"], w["to"], w["length_max_mm"], cut))
            if need > cut:
                n_short += 1
        joints_3d = set()
        for r in c["runs"]:
            for sp in r.get("spans", []):
                joints_3d |= set(sp["joints"])
                n_span += 1
                rad = arc_radius(sp["min_mm"], sp["max_mm"])
                if rad < BEND_MIN * r["d_mm"]:
                    n_tight += 1
                    tight.append((rad / r["d_mm"], cb["id"], r["name"], "+".join(sp["joints"]), sp["min_mm"], sp["max_mm"], rad, r["d_mm"]))
        want = set(cb.get("joints") or [])
        if want - joints_3d:
            R.find("FAIL", "%s: netlist joints %s are not crossed by a free span in the 3D route (no service loop)" % (
                cb["id"], sorted(want - joints_3d)), fix="route a free span (loop) across each joint", where="altaay_lab/cables3d")
        if joints_3d - want:
            R.find("WARN", "%s: the 3D route crosses %s, which the netlist does not list for this cable" % (cb["id"], sorted(joints_3d - want)),
                   fix="add the joint to the cable's 'joints' in wiring/netlist.yaml (it feeds the CABLE_MAP length rule)",
                   where="altaay_lab/wiring/netlist.yaml")
    for u in unrouted:
        R.find("FAIL", "run %s: no clear 3D path (straight placeholder)" % u, where="altaay_lab/cables3d")
    if merges:
        R.ev("series pieces summed: " + "; ".join(merges))
    worst_margin.sort()
    cannot = [x for x in worst_margin if x[4] > x[5]]                 # routed worst longer than the cut: cannot reach
    no_slack = [x for x in worst_margin if x[4] <= x[5] < x[4] + SLACK]
    R.ev("length: %d wires checked; %d cannot reach (worst routed length over the cut); %d reach but with less than the "
         "%.0f mm service slack of the CABLE_MAP rule (test fit); %d have the full slack" % (
             n_len, len(cannot), len(no_slack), SLACK, n_len - len(cannot) - len(no_slack)))
    short_by = {}
    for m, cid, a, b, L, cut in cannot:
        short_by.setdefault(cid, []).append((a, b, L, cut))
    for cid, rows in sorted(short_by.items()):
        L, cut = max(r[2] for r in rows), rows[0][3]
        R.find("FAIL", "%s: %d wire(s) cannot reach: %s; worst routed length %.0f mm over the joint ranges, cut %s mm, too short by %.0f mm "
               "before any slack" % (cid, len(rows), ", ".join("%s -> %s" % (a, b) for a, b, _, _ in rows), L, cut, L - cut),
               fix="wiring/netlist.yaml %s: cut_mm %s -> %d on %s (worst %.0f mm + 2 x 20 mm slack), and the same in CABLE_MAP.md" % (
                   cid, cut, int(math.ceil((L + SLACK) / 10.0) * 10), " and ".join("%s -> %s" % (a, b) for a, b, _, _ in rows), L),
               where="altaay_lab/wiring/netlist.yaml")
    groups = {}
    for m, cid, a, b, L, cut in no_slack:
        groups.setdefault(cid, []).append((m, a, b, L, cut))
    for cid, rows in sorted(groups.items()):
        m, a, b, L, cut = min(rows)
        R.find("WARN", "%s: %d wire(s) reach with only %.0f mm to spare (worst %s -> %s %.0f mm, cut %s mm), under the 2 x 20 mm "
               "service slack: a test fit decides (CABLE_MAP length rule)" % (cid, len(rows), cut - L, a, b, L, cut),
               fix=("kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2" if cut == 150 and cid.startswith("S")
                    else ("cut it %d mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack" if cut <= 60
                          else "cut it %d mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)") % int(math.ceil((L + SLACK) / 10.0) * 10)))
    R.ev("joint crossings: %d free spans; %d with a loop radius under 3 x OD (all the span's length change stored in one arc at "
         "the shortest pose)" % (n_span, n_tight))
    tight.sort()
    if tight:
        R.find("WARN", "%d of %d joint crossings store their length change in a loop tighter than 3 x OD: the routes tie the "
               "cable to both links close to each joint axis (spans %.1f to %.1f mm at the shortest pose). Worst: %s" % (
                   len(tight), n_span, min(t[4] for t in tight), max(t[4] for t in tight),
                   "; ".join("%s at %s %.1f to %.1f mm, loop R %.1f mm = %.1f x OD" % (t[1], t[3], t[4], t[5], t[6], t[0]) for t in tight[:5])),
               fix="place the ties at each joint far enough from the axis that the loop radius reaches 3 x OD, and check every "
                   "loop at both joint limits on the first leg (TEST_PLAN.md section 1.4)", where="altaay_lab/cables3d")
    json.dump(dict(tight=tight, margins=worst_margin), open(os.path.join(V.out_dir(), "c3_details.json"), "w"), indent=0, default=str)
    R.key("%d of %d active cables routed in 3D (%d runs still straight placeholders); %d wires too short before slack, %d with "
          "less than 40 mm slack; %d of %d joint loops under 3 x OD" % (len(active) - len(missing), len(active), len(unrouted),
                                                                         len(cannot), len(no_slack), n_tight, n_span))
    ret = D.get("retention", [])
    gaps = [r for r in ret if r.get("gap") or "gap" in str(r.get("kind", "")).lower()]
    R.ev("retention: %d items (%s), %d with no CAD feature to hold them" % (len(ret), dict(Counter(str(r.get("kind")) for r in ret)), len(gaps)))
    if gaps:
        R.find("WARN", "%d retention points have no printed surface to hold a tie mount (%s)" % (
            len(gaps), "; ".join("%s for %s" % (g.get("id"), ",".join(g.get("cables") or [])) for g in gaps[:8])),
            fix="decide each (tie to a neighbour cable, a printed clip, or move the route) before the harness is built",
            where="altaay_lab/cables3d")
    chk = Counter(c.get("check") for c in C.values())
    R.ev("cables3d's own check field: %s" % dict(chk))
    if chk.get("pending") == len(C):
        R.find("WARN", "cables3d.json is not checked by its own checker yet (check_cables.py: every cable 'pending')")
    R.write()


if __name__ == "__main__":
    main()
