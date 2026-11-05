"""Stage 1: every hole stack (site) of the lab scene, per part instance, with who uses it (CAD check only).

Sources (read only): fasteners.json (fasteners with their site, empty_holes with their reason), the lab scene sites
(fastlib Scene.sites(): feat3d circle and hex features of every STL, coaxial stacks), cables3d.json (cable polylines,
tie anchors, retention ties). Writes data/sites_raw.json: one row per (site, instance).
A screw uses a hole of its site when the hole's span along the axis overlaps the screw from the head top (seat - k)
to the tip (seat + length); a hole on the head side beyond the head that is at least the head diameter is the way the
screw and its driver go in ("screwdriver access").
"""
import json, os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib

S = hlib.scene()
sites, W = hlib.sites_cached(S)
FJ = hlib.load_fj()
F = FJ["fasteners"]
E = {e["site"]: e for e in FJ["empty_holes"]}
C3 = json.load(open(os.path.join(hlib.LAB, "cables3d", "cables3d.json")))
inst = S.inst
print("sites", len(sites), "fasteners meta sites", FJ["meta"]["scene"]["sites"], "instances", len(inst))

# fasteners.json "site" numbers come from an earlier STL set: match every fastener to the current sites by geometry
# (parallel axis, the screw line within 0.6 mm of the site line, or a pilot drilled up to 25 deg off it near the tip)
def line_d(p, o, a):
    v = p - o
    return float(np.linalg.norm(v - (v @ a) * a))
by_site = collections.defaultdict(list)
for f in F:
    a2 = np.asarray(f["axis_world"], float); p = np.asarray(f["seat_world"], float)
    L = float(f.get("length_mm") or 6)
    hit = False
    for si, s in enumerate(sites):
        o, ax = np.asarray(s["o"], float), np.asarray(s["ax"], float)
        c = abs(a2 @ ax)
        if c > 0.999 and line_d(p, o, ax) < 0.6:
            by_site[si].append(f); hit = True
        elif f.get("pilot_angle_deg") and 0.88 < c < 0.97:
            tip = p + a2 * L
            if line_d(tip, o, ax) < 1.2 or line_d(p + a2 * L * 0.6, o, ax) < 1.2:
                by_site[si].append(dict(f, _pilot=True)); hit = True
    if not hit:
        print("no site for", f["id"], f["part"], f["into"])
E = {}
for e in FJ["empty_holes"]:
    at, axe = np.asarray(e["at"], float), np.asarray(e["axis"], float)
    best = [si for si, s in enumerate(sites) if abs(np.asarray(s["ax"]) @ axe) > 0.995 and np.linalg.norm(np.asarray(s["o"]) - at) < 0.2]
    if len(best) != 1:
        print("empty hole match", e["site"], best)
    for si in best:
        E[si] = e

# cable polylines in world (zero pose) and tie anchors
cab_pts = []
for c in C3["cables"]:
    P = np.array([p["p"] for p in c["points"]], float)
    if len(P) >= 2:
        # resample every 0.5 mm
        seg = []
        for a, b in zip(P[:-1], P[1:]):
            n = max(1, int(np.linalg.norm(b - a) / 0.5))
            seg.append(a + (b - a) * np.linspace(0, 1, n, endpoint=False)[:, None])
        seg.append(P[-1:])
        Q = np.vstack(seg)
        cab_pts.append((c["id"], Q, float(c.get("d_mm") or 2.0)))
ties = [(r["id"], np.array(r.get("center_mm") or r.get("p"), float), r.get("kind"), r.get("part")) for r in C3["retention"]]
anchors = [(k, np.array(a["center_mm"], float), a.get("kind"), a.get("part"), a.get("size_mm")) for k, a in enumerate(C3["tie_anchors"])]

rows = []
for si, s in enumerate(sites):
    o, ax = np.asarray(s["o"], float), np.asarray(s["ax"], float)
    per = collections.OrderedDict()
    for seg in s["segs"]:
        t0, t1, mesh, kind, d, ii = seg
        per.setdefault(ii, []).append(dict(t0=t0, t1=t1, kind=kind, d=d))
    users = by_site.get(si, [])
    for ii, segs in per.items():
        I = inst[ii]
        t0, t1 = min(x["t0"] for x in segs), max(x["t1"] for x in segs)
        dmax = max(x["d"] for x in segs)
        use = []
        for f in users:
            if f["kind"] == "insert":
                ts_i = (np.asarray(f["seat_world"], float) - o) @ ax
                if (f["into_inst"] == ii or f["into"] == I["key"]) and t0 - 1.0 <= ts_i <= t1 + 1.0:
                    use.append(dict(id=f["id"], kind="insert", fitted=hlib.fitted(f), how="insert bore", status=f.get("status")))
                continue
            a2 = np.asarray(f["axis_world"], float)
            sg = 1.0 if a2 @ ax > 0 else -1.0
            ts = (np.asarray(f["seat_world"], float) - o) @ ax
            k = float(f["head"]["k"]) if f.get("head") else 2.0
            L = float(f.get("length_mm") or 6)
            lo, hi = sorted([ts - sg * k, ts + sg * L])
            how = None
            if f.get("_pilot"):
                how = "pilot (off axis)" if ii == f["into_inst"] else None
            elif t1 > lo - 0.05 and t0 < hi + 0.05:
                how = "head seat" if ii == f["part_inst"] else ("anchor" if ii == f["into_inst"] else "screw passes")
            else:
                # beyond the head side: access if wide enough for the head
                side = (t0 + t1) / 2 - ts
                if side * sg < 0 and dmax >= float(f["head"]["dk"]) - 0.3 if f.get("head") else False:
                    how = "screwdriver access"
            if how:
                use.append(dict(id=f["id"], kind="screw", fitted=hlib.fitted(f), how=how, status=f.get("status"),
                                spec=f["spec"], part=f["part"], into=f["into"], src=f["source"]))
        # cables through the hole: cable points within the hole radius and inside its span
        cen = o + ax * (t0 + t1) / 2
        cab = []
        for cid, Q, cd in cab_pts:
            v = Q - o
            t = v @ ax
            r = np.linalg.norm(v - np.outer(t, ax), axis=1)
            m = (t > t0 - 0.5) & (t < t1 + 0.5) & (r < dmax / 2 + cd / 2)
            if m.any():
                cab.append(cid)
        tie = [tid for tid, c, kd, part in ties if np.linalg.norm(c - cen) < max(4.0, dmax)]
        anc = [k for k, c, kd, part, sz in anchors if kd == "hole" and np.linalg.norm(c - cen) < max(4.0, dmax)]
        rows.append(dict(site=si, inst=ii, part=I["key"], printed=bool(I["printed"]), link=I["link"],
                         mirror=bool(I["mirror"]), segs=segs, t0=t0, t1=t1, dmax=dmax,
                         o=o.round(3).tolist(), ax=ax.round(5).tolist(), centre=cen.round(2).tolist(),
                         users=use, empty_why=E.get(si, {}).get("why"), cables=cab, ties=tie, tie_anchor_holes=anc))

hlib.jdump(rows, "sites_raw.json")
used_sites = set(by_site)
print("sites used by fasteners", len(used_sites), "empty", len(E), "union", len(used_sites | set(E)),
      "neither", sorted(set(range(len(sites))) - used_sites - set(E))[:40])
pr = [r for r in rows if r["printed"]]
print("printed holes (site x instance)", len(pr), "bought", len(rows) - len(pr))
cnt = collections.Counter()
for r in pr:
    fit = any(u["fitted"] for u in r["users"])
    cut = any(not u["fitted"] for u in r["users"])
    cat = "fitted" if fit else ("cut/notfitted only" if cut else ("empty: " + (r["empty_why"] or "NONE")[:50]))
    cnt[cat] += 1
for k, v in cnt.most_common():
    print("%4d  %s" % (v, k))
