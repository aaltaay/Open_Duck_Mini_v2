#!/usr/bin/env python3
"""Seats (where each cable meets a printed part) and retention (every tie) for cables3d.json.

Usage: python3 altaay_lab/cables3d/seats_ties.py
Reads and rewrites altaay_lab/cables3d/cables3d.json (adds "seats" to every cable and the top-level "retention" and
"tie_anchors" lists). Geometry: zero-pose meshes from robot.urdf and print/ (same scene as route_cables.py).

Seats, from the meshes (exact ray casts, not the voxel grid):
  every 2 mm along each run, 16 rays in the plane across the cable, up to 12 mm, against the printed parts.
  hole    : the same printed part all round (>= 14 of 16 rays), short stretch (a hole or slot through a wall)
  channel : one printed part on three sides (>= 9 of 16 rays, spread over more than 180 degrees)
  edge    : the run turns by more than 25 degrees within 4 mm of a printed part (the cable wraps that edge)
  none    : no printed part within 12 mm along a stretch longer than 40 mm (free air, held by ties only)
Tie anchors: through-holes of 3.0 mm or more (or slots) in printed walls up to 8 mm thick, found by sectioning each
printed part across its thinnest axis; holes that carry a screw or insert (audit/sites.json, audit/screws2.json and
the 2.0 to 3.4 mm pilot and clearance sizes) are left out. A 2.5 mm cable tie passes a 3.0 mm hole.

Retention rule (sources in CABLES_3D.md):
  1. a fixed point on both sides of every joint crossing (each end of a free span);
  2. a fixed point 25.4 to 50.8 mm from each connector or terminal (NASA-STD-8739.4A Table 9-2, bundles < 12.7 mm);
  3. then at most 76.2 mm between fixed points along a fixed run (NASA-STD-8739.4A Table 9-1, largest spacing);
  4. ties within 8 mm of each other on the same link are merged into one tie holding the bundle.
  Each fixed point uses the nearest tie anchor on the same link within 15 mm (kind "existing printed feature");
  otherwise it is a gap and gets an adhesive tie mount proposal (kind "adhesive tie mount").
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3d_lib as L  # noqa: E402
import route_cables as RC  # noqa: E402

RAYS = 16
REACH = 12.0
STEP = 2.0
TIE_NEAR = 8.0
ANCHOR_REACH = 15.0
FIRST_TIE = (25.4, 50.8)
MAX_SPACING = 76.2
SCREW_D = (1.6, 3.45)      # pilot and clearance sizes used by screws and inserts (MOUNTING.md): not tie anchors


def printed_meshes(s):
    out = []
    for i in s.inst:
        if i["printed"]:
            out.append((i, s.world_mesh(i)))
    return out


def run_world(s, r):
    return np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in r["points"]]), [p["link"] for p in r["points"]]


def ring_hits(meshes, p, t, links):
    """16 rays across the cable at p; returns per ray (distance, part key) or None"""
    t = t / np.linalg.norm(t)
    a = np.cross(t, [0, 0, 1.0] if abs(t[2]) < 0.9 else [1.0, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(t, a)
    D = np.array([np.cos(q) * a + np.sin(q) * b for q in np.linspace(0, 2 * np.pi, RAYS, endpoint=False)])
    best = [None] * RAYS
    for i, m in meshes:
        if links and i["link"] not in links:
            continue
        if np.any(m.bounds[0] - REACH > p) or np.any(m.bounds[1] + REACH < p):
            continue
        loc, ri, _ = m.ray.intersects_location(np.tile(p, (RAYS, 1)), D, multiple_hits=False)
        for (q, k) in zip(loc, ri):
            d = float(np.linalg.norm(q - p))
            if d <= REACH and (best[k] is None or d < best[k][0]):
                best[k] = (d, i["key"], i["link"])
    return best, D


def seats_for_run(s, meshes, r):
    P, B = run_world(s, r)
    if len(P) < 2:
        return []
    Pr = RC.resample(P, STEP)
    # nearest simplified point index for each sample
    idx = [int(np.argmin(np.linalg.norm(P - q, axis=1))) for q in Pr]
    out = []
    cur = None
    for k, q in enumerate(Pr):
        t = Pr[min(k + 1, len(Pr) - 1)] - Pr[max(k - 1, 0)]
        if np.linalg.norm(t) < 1e-9:
            continue
        hits, D = ring_hits(meshes, q, t, None)
        parts = [h[1] for h in hits if h]
        kind, part, size, link = "none", None, None, None
        if parts:
            top = max(set(parts), key=parts.count)
            n = parts.count(top)
            ang = [j for j, h in enumerate(hits) if h and h[1] == top]
            spread = 0
            if ang:
                gaps = np.diff(sorted(ang) + [sorted(ang)[0] + RAYS])
                spread = (RAYS - (gaps.max() - 1)) * 360.0 / RAYS
            ds = [hits[j][0] for j in ang]
            link = [h[2] for h in hits if h and h[1] == top][0]
            if n >= 14:
                kind, part, size = "hole", top, round(2 * float(np.median(ds)), 1)
            elif n >= 9 and spread > 180:
                kind, part, size = "channel", top, round(2 * float(np.min(ds)), 1)
        key = (kind, part)
        if cur and cur["key"] == key and k - cur["k1"] <= 1:
            cur["k1"] = k
            cur["pts"].append(q)
            cur["sizes"].append(size)
        else:
            if cur:
                out.append(cur)
            cur = dict(key=key, k0=k, k1=k, pts=[q], sizes=[size], link=link, t=t / np.linalg.norm(t), idx=idx[k])
    if cur:
        out.append(cur)
    seats = []
    for c in out:
        kind, part = c["key"]
        L_ = (c["k1"] - c["k0"]) * STEP
        if kind == "none" and L_ < 40.0:
            continue
        if kind == "hole" and L_ > 14.0:
            kind = "channel"           # a long enclosed stretch is a closed channel, not a hole through a wall
        cen = np.mean(c["pts"], 0)
        seats.append(dict(kind=kind, part=part, link=c["link"], center_mm=[round(float(x), 1) for x in cen],
                          axis=[round(float(x), 3) for x in c["t"]],
                          size_mm=(max(x for x in c["sizes"] if x) if any(c["sizes"]) else None),
                          length_mm=round(L_, 1), point_index=c["idx"],
                          how="ray rings: %d rays every %.0f mm across the cable, reach %.0f mm, exact meshes" % (RAYS, STEP, REACH)))
    # edges: corners of the run within 4 mm of a printed part
    for i in range(1, len(P) - 1):
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        if np.linalg.norm(a) < 1e-6 or np.linalg.norm(b) < 1e-6:
            continue
        th = np.degrees(np.arccos(np.clip(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b), -1, 1)))
        if th < 25:
            continue
        best = None
        for inst, m in meshes:
            if np.any(m.bounds[0] - 5 > P[i]) or np.any(m.bounds[1] + 5 < P[i]):
                continue
            d = float(np.abs(trimesh.proximity.signed_distance(m, [P[i]])[0]))
            if d <= 4.0 + r["d_mm"] / 2 and (best is None or d < best[0]):
                best = (d, inst["key"], inst["link"])
        if best:
            seats.append(dict(kind="edge", part=best[1], link=best[2], center_mm=[round(float(x), 1) for x in P[i]],
                              axis=[round(float(x), 3) for x in (b / np.linalg.norm(b))], size_mm=None,
                              turn_deg=round(float(th), 1), gap_mm=round(best[0], 1), point_index=i,
                              how="corner of the routed polyline within 4 mm of the part surface (signed distance)"))
    seats.sort(key=lambda x: x["point_index"])
    return seats


def screw_sites():
    pts = []
    for fn in ("sites.json", "sites_head.json"):
        p = os.path.join(RC.LAB, "audit", fn)
        if os.path.exists(p):
            for sname in json.load(open(p)):
                o, ax = np.array(sname["o"], float), np.array(sname["ax"], float)
                for t0, t1, part, kind, d, *_ in sname["segs"]:
                    pts.append(o + ax * (t0 + t1) / 2)
    return np.array(pts) if pts else np.zeros((0, 3))


def tie_anchors(s, meshes):
    """through-holes (>= 3.0 mm) and slots in thin printed walls (<= 8 mm), by sections across the thinnest axis"""
    from shapely.geometry import Polygon
    sites = screw_sites()
    out = []
    seen = {}
    for inst, m in meshes:
        local = s.mesh(inst)
        obb = local.bounding_box_oriented
        T = obb.primitive.transform
        ext = obb.primitive.extents
        ax = int(np.argmin(ext))
        if ext[ax] > 12.0:
            levels = []        # thick parts: no plate-style tie holes searched
        else:
            levels = [0.0]
        nrm_local = T[:3, ax]
        org_local = T[:3, 3]
        key = inst["path"]
        if key not in seen:
            holes = []
            for lv in levels:
                sec = local.section(plane_origin=org_local + lv * nrm_local, plane_normal=nrm_local)
                if sec is None:
                    continue
                p2, M2 = sec.to_2D()
                for poly in p2.polygons_full:
                    for ring in poly.interiors:
                        q = Polygon(ring.coords)
                        rr = q.minimum_rotated_rectangle
                        xs, ys = rr.exterior.coords.xy
                        e = sorted([np.hypot(xs[1] - xs[0], ys[1] - ys[0]), np.hypot(xs[2] - xs[1], ys[2] - ys[1])])
                        dmin = e[0]
                        if dmin < 3.0:
                            continue
                        c2 = np.array(q.centroid.coords[0])
                        c3 = (M2 @ np.r_[c2, 0, 1])[:3]
                        holes.append((c3, e, ext[ax]))
            seen[key] = holes
        Tw = s.T0[inst["link"]] @ inst["T"]
        for c3, e, th in seen[key]:
            cw = (Tw @ np.r_[c3, 1.0])[:3]
            if inst.get("mirrored"):
                pass
            if len(sites) and np.min(np.linalg.norm(sites - cw, axis=1)) < 1.5 and e[0] <= 3.6:
                continue
            if abs(e[0] - e[1]) < 0.4 and SCREW_D[0] <= e[0] <= SCREW_D[1]:
                continue
            out.append(dict(part=inst["key"], link=inst["link"], center_mm=[round(float(x), 1) for x in cw],
                            normal=[round(float(x), 3) for x in (Tw[:3, :3] @ nrm_local)],
                            size_mm=[round(float(e[0]), 1), round(float(e[1]), 1)], wall_mm=round(float(th), 1),
                            kind="slot" if e[1] > 1.6 * e[0] else "hole"))
    return out


def place_retention(s, data, anchors):
    items = []
    for c in data["cables"]:
        for r in c.get("runs", []):
            P, B = run_world(s, r)
            if len(P) < 2:
                continue
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
            acc = np.r_[0, np.cumsum(seg)]
            total = acc[-1]
            want = []          # (arc length, reason)
            loops = []
            for i in range(len(P) - 1):
                if B[i] != B[i + 1]:
                    # designed free section (service loop): S >= 3 x OD x largest joint angle from zero (uniform bend)
                    js = RC.chain(PAR, B[i], B[i + 1])[1]
                    th = sum(max(abs(RC.REV[j][0]), abs(RC.REV[j][1])) for j in js)
                    th_rt = sum(max(abs(RC.RUNTIME.get(j, RC.REV[j])[0]), abs(RC.RUNTIME.get(j, RC.REV[j])[1])) for j in js)
                    need = 3.0 * r["d_mm"] * th
                    # the free section may run into the connector zone (no tie within 25.4 mm of a connector, Table 9-2):
                    # the plug is then the fixed point on that side
                    prev_lim = max([a for a, _ in want]) if want else 0.0
                    nxt = [acc[k] for k in range(i + 1, len(P) - 1) if B[k] != B[k + 1]]
                    next_lim = (nxt[0] + acc[i + 1]) / 2 if nxt else total
                    target = max(need - (acc[i + 1] - acc[i]), 0.0)
                    lroom, rroom = max(acc[i] - prev_lim, 0.0), max(next_lim - acc[i + 1], 0.0)
                    left = min(lroom, target / 2)
                    right = min(rroom, target - left)
                    left = min(lroom, max(left, target - right))      # borrow from the other side when one is clipped
                    a0 = acc[i] - left
                    a1 = acc[i + 1] + right
                    S = a1 - a0
                    loops.append(dict(span=[i, i + 1], joints=js, angle_rad=round(th, 3), angle_runtime_rad=round(th_rt, 3),
                                      od_mm=r["d_mm"], free_needed_mm=round(need, 1), free_mm=round(S, 1),
                                      radius_mm=round(S / th, 1) if th > 0 else None,
                                      radius_runtime_mm=round(S / th_rt, 1) if th_rt > 0 else None,
                                      rule_mm=round(3.0 * r["d_mm"], 1), ok=bool(S / max(th, 1e-9) >= 3.0 * r["d_mm"] - 0.05),
                                      ok_runtime=bool(S / max(th_rt, 1e-9) >= 3.0 * r["d_mm"] - 0.05),
                                      ties_at_mm=[round(a0, 1), round(a1, 1)]))
                    if a0 > 1.0:
                        want.append((a0, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i], S)))
                    else:
                        loops[-1]["anchor_a"] = "connector (no tie needed)"
                    if a1 < total - 1.0:
                        want.append((a1, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i + 1], S)))
                    else:
                        loops[-1]["anchor_b"] = "connector (no tie needed)"
            r["service_loops"] = loops
            if total > FIRST_TIE[1] + 10:
                if not any(l_.get("anchor_a") for l_ in loops) and not any(a < FIRST_TIE[1] for a, _ in want):
                    want.append((FIRST_TIE[0] + 5.0, "first tie after the connector (NASA Table 9-2)"))
                if not any(l_.get("anchor_b") for l_ in loops) and not any(a > total - FIRST_TIE[1] for a, _ in want):
                    want.append((total - FIRST_TIE[0] - 5.0, "first tie before the far connector (NASA Table 9-2)"))
            want.sort()
            # fill gaps over MAX_SPACING on fixed pieces
            full = [(0.0, "end")] + want + [(total, "end")]
            extra = []
            for (a0, _), (a1, _) in zip(full[:-1], full[1:]):
                n = int(np.floor((a1 - a0) / MAX_SPACING))
                for k in range(1, n + 1):
                    extra.append((a0 + k * (a1 - a0) / (n + 1), "spacing <= 76.2 mm (NASA Table 9-1)"))
            for a, why in sorted(want + extra):
                i = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
                t = (a - acc[i]) / max(seg[i], 1e-9)
                q = P[i] + (P[i + 1] - P[i]) * t
                link = B[i] if t < 0.5 or B[i] == B[i + 1] else B[i + 1]
                ax = (P[i + 1] - P[i]) / max(seg[i], 1e-9)
                items.append(dict(cable=c["id"], run=r["name"], p=q, axis=ax, link=link, why=why, d=r["d_mm"]))
    # merge ties of the same link within TIE_NEAR
    merged = []
    for it in items:
        for m in merged:
            if m["link"] == it["link"] and np.linalg.norm(m["p"] - it["p"]) < TIE_NEAR:
                m["cables"].add(it["cable"])
                m["whys"].add(it["why"])
                m["ds"].append(it["d"])
                m["pts"].append(it["p"])
                break
        else:
            merged.append(dict(link=it["link"], p=it["p"], pts=[it["p"]], axis=it["axis"], cables={it["cable"]},
                               whys={it["why"]}, ds=[it["d"]]))
    an = [a for a in anchors]
    out = []
    for k, m in enumerate(merged):
        c = np.mean(m["pts"], 0)
        bundle = float(np.sqrt(np.sum(np.square(m["ds"]))) * 1.15)
        best = None
        for a in an:
            if a["link"] != m["link"]:
                continue
            d = float(np.linalg.norm(np.array(a["center_mm"]) - c))
            if d <= ANCHOR_REACH and (best is None or d < best[0]):
                best = (d, a)
        part = None
        gap = False
        if best:
            kind = "existing printed feature"
            part = best[1]["part"]
            note = "cable tie through the %s %.1f x %.1f mm in %s (%.0f mm from the cable)" % (
                best[1]["kind"], best[1]["size_mm"][0], best[1]["size_mm"][1], part, best[0])
        else:
            # nearest printed surface on the same link for a stick-on mount
            near = None
            for inst in s.inst:
                if inst["link"] != m["link"] or not inst["printed"]:
                    continue
                mw = s.world_mesh(inst)
                if np.any(mw.bounds[0] - 25 > c) or np.any(mw.bounds[1] + 25 < c):
                    continue
                d = float(abs(trimesh.proximity.signed_distance(mw, [c])[0]))
                if near is None or d < near[0]:
                    near = (d, inst["key"])
            gap = True
            kind = "adhesive tie mount" if near and near[0] <= 15 else "cable tie"
            part = near[1] if (near and near[0] <= 15) else None
            note = ("GAP: no tie anchor in the CAD here; proposed stick-on cable tie mount on %s (%.0f mm away)" % (
                part, near[0])) if part else ("GAP: free air, no printed part within 15 mm on this link: a tie around the "
                                              "bundle only (keeps the bundle together, does not fix it); a printed guide is "
                                              "needed to fix it here")
        out.append(dict(id="T%03d" % (k + 1), cables=sorted(m["cables"]), kind=kind, gap=gap, center_mm=[round(float(x), 1) for x in c],
                        axis=[round(float(x), 3) for x in m["axis"]], link=m["link"], part=part,
                        p=[round(float(x), 2) for x in (np.linalg.inv(s.T0[m["link"]]) @ np.r_[c, 1.0])[:3]],
                        bundle_d_mm=round(bundle, 1), tie="nylon cable tie 2.5 x 100 mm" if bundle <= 20 else "nylon cable tie 3.6 x 150 mm",
                        why=sorted(m["whys"]), note=note))
    return out


PAR = {}


def main():
    t0 = time.time()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    PAR.update(RC.tree(s))
    data = json.load(open(RC.OUT_JSON))
    meshes = printed_meshes(s)
    anchors = tie_anchors(s, meshes)
    print("tie anchors found: %d" % len(anchors), flush=True)
    for c in data["cables"]:
        allseats = []
        for r in c.get("runs", []):
            ss = seats_for_run(s, meshes, r)
            for x in ss:
                x["run"] = r["name"]
            r["seats"] = ss
            allseats += ss
        c["seats"] = allseats
        print("%-4s seats %d (%s)" % (c["id"], len(allseats), ", ".join(sorted({x["kind"] for x in allseats}))), flush=True)
    data["retention"] = place_retention(s, data, anchors)
    data["tie_anchors"] = anchors
    kinds = {}
    for t in data["retention"]:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    data["meta"]["retention"] = dict(script="altaay_lab/cables3d/seats_ties.py", count=len(data["retention"]), by_kind=kinds,
                                     rule="both sides of every joint crossing; first tie 25.4-50.8 mm from each connector "
                                          "(NASA-STD-8739.4A Table 9-2); <= 76.2 mm spacing (Table 9-1); merged within 8 mm")
    RC.write_json_atomic(data, RC.OUT_JSON)
    print("retention items %d %s in %.1f s" % (len(data["retention"]), kinds, time.time() - t0))


if __name__ == "__main__":
    main()
