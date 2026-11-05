"""D42 checks (calc only, CAD check only): every screw group in the build against the uniform pattern rule, and the
F1, F2 and rattle numbers of the joints D42 changes. Method of checks.py (twin/screws/screws_twin.py numbers).
Rule (DECISIONS.md D42): the screws left on a part are mirror-symmetric about the part's own centre line, or a
diagonal pair through the centre. Test: the centre is the centroid of the part's full hole pattern (every listed
screw); the kept set must map onto itself under the half turn about the pattern normal or a mirror plane through the
centre (the pattern's principal planes and the world x, y, z planes), within max(1.0 mm, 3 % of the pattern size).
Writes data/sym_checks.json. Inputs: fasteners/fasteners.json, twin/screws/data/joints.json and lips.json, data/close_report.json."""
import json, os, sys, math, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
FJ = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json"))); F = {f["id"]: f for f in FJ["fasteners"]}
J = json.load(open(os.path.join(LAB, "twin", "screws", "data", "joints.json")))
LIPS = json.load(open(os.path.join(LAB, "twin", "screws", "data", "lips.json")))
CR = json.load(open(os.path.join(HERE, "data", "close_report.json")))
fitted = lambda x: x.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)") and not x.get("leave_out")
HIT = {"soft": 900.0, "mid": 2800.0}


def frame(ids):
    P = np.array([F[i]["seat_world"] for i in ids], float)
    c = P.mean(0)
    ax = np.array([F[i]["axis_world"] for i in ids], float)
    _, sv, vt = np.linalg.svd(P - c) if len(P) > 1 else (None, np.zeros(3), np.eye(3))
    return P, c, sv, vt, ax


def uniform(all_ids, kept):
    if len(kept) == 0:
        return "none fitted", True
    if len(kept) == 1:
        return ("single screw (the part has 1 hole)" if len(all_ids) == 1 else "single screw of %d" % len(all_ids)), len(all_ids) == 1
    P, c, sv, vt, ax = frame(all_ids)
    K = np.array([F[i]["seat_world"] for i in kept], float)
    size = max(float(np.ptp(P, axis=0).max()), 1.0); tol = max(1.0, 0.03 * size)
    planar = sv[-1] < 0.05 * max(sv[0], 1e-9) or len(all_ids) <= 3
    nrm = vt[-1] if planar else None
    tests = []
    if planar:   # half turn about the pattern normal through the centre
        R = 2 * np.outer(nrm, nrm) - np.eye(3); tests.append(("half turn (diagonal through the centre)", lambda X: c + (X - c) @ R.T))
    else:
        tests.append(("point reflection through the centre", lambda X: 2 * c - X))
    cand = [vt[k] for k in range(3) if not (planar and k == 2) and sv[k] > 1e-6] + [np.eye(3)[k] for k in range(3)]
    for n in cand:
        if planar and abs(n @ nrm) > 0.9:
            continue
        H = np.eye(3) - 2 * np.outer(n, n)
        tests.append(("mirror about the plane through the centre, normal %s" % np.round(n, 2).tolist(), (lambda H: lambda X: c + (X - c) @ H.T)(H)))
    for name, T in tests:
        Q = T(K)
        d = np.linalg.norm(Q[:, None, :] - K[None, :, :], axis=2).min(1)
        if d.max() <= tol:
            return name, True
    return "NOT uniform (no half turn or mirror maps the kept set onto itself, tol %.1f mm)" % tol, False


def rim_span(ids, kept):
    """largest straight gap between neighbouring kept screws round the pattern (rattle, as checks.py), mm"""
    P, c, sv, vt, ax = frame(ids)
    u, v = vt[0], vt[1]
    pts = {i: np.array([(np.subtract(F[i]["seat_world"], c)) @ u, (np.subtract(F[i]["seat_world"], c)) @ v]) for i in kept}
    order = sorted(pts, key=lambda i: math.atan2(pts[i][1], pts[i][0]))
    return round(max(np.linalg.norm(pts[a] - pts[b]) for a, b in zip(order, order[1:] + order[:1])), 1) if len(order) > 1 else None


# ---- audit: joints.json groups, then fitted screws in no joint grouped by (part, into)
# a joint of joints.json can hold screws of several part pairs (servo case screws: bracket and roll motor plate):
# the rule is per part, so each joint is split by (part, instance, into, instance)
key = lambda f: (f.get("part"), f.get("part_inst"), f.get("into"), f.get("into_inst"))
groups, seen = [], set()
for j in J:
    sub = collections.OrderedDict()
    for i in j["ids"]:
        sub.setdefault(key(F[i]), []).append(i)
    for k, ids in sub.items():
        groups.append((j["joint"] + ("" if len(sub) == 1 else " [%s %s -> %s %s]" % k), ids))
    seen |= set(j["ids"])
rest = collections.OrderedDict()
for f in FJ["fasteners"]:
    if f["kind"] == "screw" and f["id"] not in seen:
        rest.setdefault(key(f), []).append(f["id"])
groups += [("%s %s -> %s %s (%s)" % (k + (F[ids[0]].get("link"),)), ids) for k, ids in rest.items()]
# and per part: every screw whose head sits on that part instance, whatever it screws into ("the screws left on any part")
per_part = collections.OrderedDict()
for f in FJ["fasteners"]:
    if f["kind"] == "screw":
        per_part.setdefault((f.get("part"), f.get("part_inst")), []).append(f["id"])
groups = [("part %s %s" % k, ids) for k, ids in per_part.items()] + [("pair " + g, ids) for g, ids in groups]
audit = []
for name, ids in groups:
    kept = [i for i in ids if fitted(F[i])]
    how, ok = uniform(ids, kept)
    audit.append(dict(group=name, listed=len(ids), kept=kept, n_kept=len(kept), pattern=how, uniform=ok))
bad = [a for a in audit if not a["uniform"]]

# ---- F1, F2, rattle for the D42 joints (before: D39 kept set, after: D42)
Jn = {j["joint"]: j for j in J}
D42 = {"body_front shell": (["F067", "F068", "F069", "F072"], ["F067", "F068", "F071", "F072"]),
       "battery_pack_lid -> body_back (trunk_assembly)": (["F017", "F018", "F028"], ["F017", "F018", "F027", "F028"]),
       "head_bot_sheet -> head (head_assembly)": (["F083", "F088", "F089"], ["F083", "F084", "F089", "F090"])}
joints = {}
for name, (before, after) in D42.items():
    j = Jn[name]
    r = dict(ids=j["ids"], before=before, after=after, F1_SF_one_screw=j["SF_F1_one_screw"], F1_src="twin/screws/data/joints.json (one screw takes the whole inertial pull)",
             rattle_mm=dict(before=rim_span(j["ids"], before), after=rim_span(j["ids"], after)),
             pattern=dict(before=uniform(j["ids"], before)[0], after=uniform(j["ids"], after)[0]))
    if j.get("F2_bearing_per_screw_N"):
        lip = LIPS.get(name.split()[0], {}).get("capacity_N", {})
        r["F2_SF"] = {lv: dict(before=dict(screws=round(len(before) * j["F2_bearing_per_screw_N"] / HIT[lv], 2), **{"with_lip_" + d: round((len(before) * j["F2_bearing_per_screw_N"] + lip.get(d, 0)) / HIT[lv], 2) for d in ("y", "z_up", "z_down")}),
                              after=dict(screws=round(len(after) * j["F2_bearing_per_screw_N"] / HIT[lv], 2), **{"with_lip_" + d: round((len(after) * j["F2_bearing_per_screw_N"] + lip.get(d, 0)) / HIT[lv], 2) for d in ("y", "z_up", "z_down")})) for lv in HIT}
        r["into"] = dict(before=collections.Counter(F[i]["into"] for i in before), after=collections.Counter(F[i]["into"] for i in after))
    joints[name] = r
# body_back shell: 6 screws and the 4 ear seats (rebuilt with body_middle_bottom here)
bb = Jn["body_back shell"]; lip = LIPS["body_back"]["capacity_N"]; seat = sum(s["capacity_N"] for s in CR["seats"])
kept_bb = [i for i in bb["ids"] if fitted(F[i])]
joints["body_back shell"] = dict(kept=kept_bb, seats_N=seat, F2_SF={lv: dict(side=round((len(kept_bb) * bb["F2_bearing_per_screw_N"] + lip["y"]) / HIT[lv], 2),
                                  up=round((len(kept_bb) * bb["F2_bearing_per_screw_N"] + lip["z_up"]) / HIT[lv], 2),
                                  down=round((len(kept_bb) * bb["F2_bearing_per_screw_N"] + lip["z_down"] + seat) / HIT[lv], 2)) for lv in HIT},
                                 rattle_mm=rim_span(bb["ids"], kept_bb), pattern=uniform(bb["ids"], kept_bb)[0])
scr = [f for f in FJ["fasteners"] if f["kind"] == "screw" and fitted(f)]
ins = [f for f in FJ["fasteners"] if f["kind"] == "insert" and fitted(f)]
out = dict(rule="D42: the screws left on a part form a uniform pattern (mirror-symmetric about the part's centre line, or a diagonal pair through the centre)",
           counts=dict(screws=len(scr), inserts=len(ins), washers=sum(2 for f in scr if "washers" in f["spec"])),
           audit=audit, not_uniform=[a["group"] for a in bad], joints=joints)
json.dump(out, open(os.path.join(HERE, "data", "sym_checks.json"), "w"), indent=1, default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))
for a in audit:
    if (a["group"].startswith("part") and a["listed"] != a["n_kept"]) or not a["uniform"] or len(sys.argv) > 1:
        print("%-62s %d of %d  %s" % (a["group"][:62], a["n_kept"], a["listed"], a["pattern"]))
print("groups", len(audit), "(parts %d, part pairs %d)" % (len(per_part), len(audit) - len(per_part)), "uniform", sum(a["uniform"] for a in audit), "NOT uniform", [a["group"] for a in bad])
print(json.dumps(dict(counts=out["counts"], joints=joints), default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))[:3000])
