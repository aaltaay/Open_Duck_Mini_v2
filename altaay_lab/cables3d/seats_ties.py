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
  1. a fixed point on both sides of every joint crossing (each end of the free loop). The two ties are pushed away from
     the crossing until the loop between them meets 3 x OD (NASA-STD-8739.4A Table 7-1 minimum) in both models:
       uniform bend: free length / largest joint angle from zero >= 3 x OD;
       length storage: the free length the cable needs at the farthest pose (routed, fixed pieces plus the span chord)
       bowed as one circular arc over the tie-to-tie chord at the closest pose (61 samples per joint) >= 3 x OD;
     or until the route runs out (previous tie of the run, midpoint to the next crossing, 60 mm per side at most);
  2. a fixed point 25.4 to 50.8 mm from each connector or terminal (NASA-STD-8739.4A Table 9-2, bundles < 12.7 mm);
  3. then at most 76.2 mm between fixed points along a fixed run. [L] lab rule: NASA-STD-8739.4A Table 9-1 gives the
     spacing of the ties that bind a harness (19.1 mm for a harness of 6.4 mm or less, 76.2 mm only above 25.4 mm) and
     no spacing for fixing a harness to the structure (7.2.29 asks for support without a number);
  4. ties within 8 mm of each other on the same link are merged into one tie holding the bundle.
  Each fixed point uses the nearest tie anchor on the same link within 15 mm (kind "existing printed feature");
  otherwise the nearest printed surface on the same link within 15 mm gets an adhesive tie mount (kind "adhesive tie
  mount"), checked with exact rays: a flat patch (surface within 0.4 mm of the mount plane, normals within 15 deg) under
  the whole base, with the mount height free above it, the base centre shifted up to 12 mm in the surface plane and at
  most 20 mm from the cable line (the bundle is dressed over to it; at a loop end the loop length to leave is unchanged)
  [L].
  mount_fit.type = "MB3A" (BOM line 34, 19 x 19 x 4.8 mm) where it fits, else "ABM1M" (BOM line 34b, Panduit
  ABM1M-AT-C 12.7 x 12.7 mm, checked as 13 x 13 x 4.1 mm), else None. One mount per spot: a mount or hole never
  overlaps one already placed on the same face.
  A point still without an anchor (free air: no printed surface within 15 mm; or a mount spot with no flat patch) is
  resolved in the D25 order:
  i.   tied to a neighbour cable that passes within 4 mm and is held by its own anchor within 20 mm
       (kind "cable tie to a neighbour cable");
  ii.  two 4.0 mm tie holes drilled through a printed wall of the same link after printing (kind "drilled printed
       feature", record tie_holes; checks in tie_hole_pair; print/PRINT_PLAN.md After printing);
  iii. a loop tie moved further out along the route (the loop still meets 3 x OD, the tie stays on its link and 8 mm
       from other ties) to a feature, mount or hole pair; a point that is not a loop end may take a mount or hole pair
       on a printed part of its link up to 25 mm away (the bundle dressed over to it);
  iv.  at a loop end, a stick-on mount on the STS3215 case of the same link (mount_fit.on_servo_case), 8 mm off the plug
       axis and 1 mm from moving parts over the joint sweep;
  else open ("open": true) with a named plan ("plan": a route change to a mount or hole pair up to 40 mm away, or a
  printed tie anchor, a design change).
  Usage: --json <file> to work on a copy; --plans-only to rewrite only the plans of the open points.
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
MAX_SPACING = 76.2         # [L] lab support spacing (see the docstring: not a NASA value for this harness size)
SCREW_D = (1.6, 3.45)      # pilot and clearance sizes used by screws and inserts (MOUNTING.md): not tie anchors
BEND_MIN = 3.0             # x OD, NASA-STD-8739.4A Table 7-1, overall harness of AWG 10 or smaller without coax
LOOP_CAP = 60.0            # mm: longest push of one loop tie away from its crossing
MERGE_GAP = 8.0            # mm: two crossings closer than this along the route (on the link between them) make one loop [L]
MOUNT_BASE, MOUNT_H = 19.0, 4.8   # HellermannTyton MB3A (BOM line 34 spec sheet): base 19.0 x 19.0 mm, 4.8 mm high
FLAT_TOL, FLAT_DEG = 0.4, 15.0     # [L] flat patch: surface within 0.4 mm of the mount plane, normals within 15 deg
MOUNT_SHIFT = (0.0, 4.0, -4.0, 8.0, -8.0, 12.0, -12.0)   # mm, in-plane shifts of the mount centre tried (bundle dressed onto it)
FREE_MOUNT_REACH = 25.0    # mm: free-air point, farthest printed surface of the same link a mount may go on
DRESS_MAX, DRESS_MAX_LOOP = 20.0, 20.0   # mm: farthest mount centre from the cable line, also at a loop end [L]
NEIGH_GAP, NEIGH_ANCHOR = 4.0, 20.0   # mm: neighbour bundle surface gap, and its own anchor within this distance
SMALL_BASE, SMALL_H = 13.0, 4.1   # checked as 13.0 x 13.0 x 4.1 mm: the HellermannTyton MB2APT (Product Catalogue 2016/2017
                                  # p. 1.7, https://docs.rs-online.com/fd67/0900766b8139134b.pdf, read 2026-11-02 1:53 AM ET),
                                  # which also covers the bought small mount, Panduit ABM1M-AT-C, 0.50 x 0.50 in (12.7 mm)
                                  # (BOM line 34b; its height is not on the page read)
SMALL_TYPE = "ABM1M"              # BOM line 34b
HOLE_D = 4.0               # mm, the BOM T14 bit (as D24); passes the 2.54 mm wide line 32 tie up to 3.1 mm thick
LIG_MIN = 1.6              # mm of solid plastic round a hole (the lab's insert-wall minimum, CNC Kitchen, PRINT_CHECK.md flag 1)
WALL_MAX = 12.0            # mm, thickest wall a tie-hole pair goes through [L]
STRAP_GAP = 1.5            # mm free behind the wall for the strap between the two holes [L] (tie thickness not published)
SWEEP_GAP = 1.0            # mm from the back strap (or a servo-case mount) to parts of other links over the joint sweep [L]
SERVO_CASE = ("servo_bottom", "servo_mid", "servo_top")   # STS3215 case pieces in the scene (fixed to their link)
CONN_KEEP, PLUG_LEN = 8.0, 12.0   # mm: servo-case mount base kept this far from the plug axis, taken 12 mm each way [L]
POSER = None


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


def arc_radius_v(c, a):
    """radius of a circular arc of length a over chord c, element-wise (inf where a <= c): the loop that stores the
    cable a over the tie-to-tie distance c"""
    c, a = np.broadcast_arrays(np.asarray(c, float), np.asarray(a, float))
    out = np.full(c.shape, np.inf)
    m = a > c + 1e-6
    cc, aa = c[m], a[m]
    major = aa > np.pi * cc / 2
    lo, hi = np.maximum(cc / 2, 1e-9), np.maximum(aa, cc) * 1e3
    for _ in range(100):
        R = (lo + hi) / 2
        h = np.arcsin(np.minimum(1.0, cc / (2 * R)))
        go = (2 * R * np.where(major, np.pi - h, h) > aa) != major
        lo, hi = np.where(go, R, lo), np.where(go, hi, R)
    R = (lo + hi) / 2
    out[m] = np.where(cc < 1e-6, aa / (2 * np.pi), R)
    return out


def _along(P, acc, a):
    i = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
    t = (a - acc[i]) / max(float(np.linalg.norm(P[i + 1] - P[i])), 1e-9)
    return P[i] + (P[i + 1] - P[i]) * t


def loop_search(s, P, acc, B, group, od, lroom, rroom):
    """free loop across the crossing(s) in `group` (span start indexes; two consecutive crossings with a few mm of the
    middle link between them form one loop): ties `left` mm before the first span and `right` mm after the last.
    Returns the shortest (left, right) that meets 3 x OD in both models (uniform bend and length storage), or the best
    one inside the room, with the loop numbers"""
    i0, i9 = group[0], group[-1]
    la, lb = B[i0], B[i9 + 1]
    js = []
    for i in group:
        js += [j for j in RC.chain(PAR, B[i], B[i + 1])[1] if j not in js]
    Ls = np.arange(0.0, min(lroom, LOOP_CAP) + 1e-9, 1.0)
    Rs = np.arange(0.0, min(rroom, LOOP_CAP) + 1e-9, 1.0)
    QA = np.array([_along(P, acc, acc[i0] - x) for x in Ls])
    QB = np.array([_along(P, acc, acc[i9 + 1] + x) for x in Rs])
    pa = (np.linalg.inv(s.T0[la]) @ np.c_[QA, np.ones(len(QA))].T).T[:, :3]
    pb = (np.linalg.inv(s.T0[lb]) @ np.c_[QB, np.ones(len(QB))].T).T[:, :3]
    ends = [((B[i], (np.linalg.inv(s.T0[B[i]]) @ np.r_[P[i], 1.0])[:3]),
             (B[i + 1], (np.linalg.inv(s.T0[B[i + 1]]) @ np.r_[P[i + 1], 1.0])[:3])) for i in group]
    mid = sum(float(acc[b] - acc[a + 1]) for a, b in zip(group[:-1], group[1:]))   # route on the middle link(s)

    def sweep(ranges):
        n = {1: 61, 2: 21, 3: 9}.get(len(js), 5)
        grids = np.meshgrid(*[np.linspace(ranges[j][0], ranges[j][1], n) for j in js], indexing="ij")
        cmin, smax = np.full((len(Ls), len(Rs)), np.inf), 0.0
        for q in zip(*[g.ravel() for g in grids]):
            T = POSER.T(dict(zip(js, q)))
            A = (T[la] @ np.c_[pa, np.ones(len(pa))].T).T[:, :3]
            Bw = (T[lb] @ np.c_[pb, np.ones(len(pb))].T).T[:, :3]
            cmin = np.minimum(cmin, np.linalg.norm(A[:, None, :] - Bw[None, :, :], axis=2))
            sp = sum(float(np.linalg.norm((T[l2] @ np.r_[p2, 1.0])[:3] - (T[l1] @ np.r_[p1, 1.0])[:3]))
                     for (l1, p1), (l2, p2) in ends)
            smax = max(smax, sp)
        return cmin, smax
    rt = dict(RC.REV)
    rt.update({j: v for j, v in RC.RUNTIME.items()})
    cmin, smax = sweep(RC.REV)
    cmin_rt, _ = sweep(rt) if any(j in RC.RUNTIME for j in js) else (cmin, smax)
    th = sum(max(abs(RC.REV[j][0]), abs(RC.REV[j][1])) for j in js)
    th_rt = sum(max(abs(rt[j][0]), abs(rt[j][1])) for j in js)
    route0 = float(acc[i9 + 1] - acc[i0])
    span0 = route0 - mid
    S = Ls[:, None] + Rs[None, :] + route0
    Lmax = Ls[:, None] + Rs[None, :] + mid + smax      # cable the loop needs at the farthest pose
    unif, unif_rt = S / max(th, 1e-9), S / max(th_rt, 1e-9)
    arc, arc_rt = arc_radius_v(cmin, Lmax), arc_radius_v(cmin_rt, Lmax)
    rule = BEND_MIN * od - 0.05
    ok = (unif >= rule) & (arc >= rule)
    strict = (unif >= BEND_MIN * od + 0.02) & (arc >= BEND_MIN * od + 0.02)   # a little over the rule where the room allows,
    pick = strict if strict.any() else ok                                    # so a recompute from rounded ties still passes
    if pick.any():
        tot = np.where(pick, Ls[:, None] + Rs[None, :] - 1e-3 * np.minimum(arc, 1e3), np.inf)
        a, b = np.unravel_index(int(np.argmin(tot)), tot.shape)
    else:
        score = np.minimum(np.minimum(unif, arc), 1e6) - 1e-3 * (Ls[:, None] + Rs[None, :])
        a, b = np.unravel_index(int(np.argmax(score)), score.shape)
    return dict(left=float(Ls[a]), right=float(Rs[b]), free=float(S[a, b]), th=th, th_rt=th_rt, joints=js,
                unif=float(unif[a, b]), unif_rt=float(unif_rt[a, b]), arc=float(arc[a, b]), arc_rt=float(arc_rt[a, b]),
                chord_min=float(cmin[a, b]), length_build=float(Lmax[a, b]), extra=float(smax - span0),
                ok=bool(unif[a, b] >= rule and arc[a, b] >= rule),
                ok_rt=bool(unif_rt[a, b] >= rule and arc_rt[a, b] >= rule),
                grid=dict(Ls=Ls, Rs=Rs, ok=ok, unif=unif, arc=arc, unif_rt=unif_rt, arc_rt=arc_rt, cmin=cmin, Lmax=Lmax,
                          rule=rule, S=S, smax=smax, span0=span0))


MESH_CACHE = {}
PLACED_MOUNTS = []        # (centre, normal, u, v, half side) of every mount placed so far (one mount per spot)
PLACED_HOLES = []         # (centre, normal) of every drilled tie hole placed so far


def overlaps_placed(g, n, u, v, half, gap=0.5):
    """True if a mount square (centre g, plane normal n, in-plane axes u, v, half side) overlaps a mount already placed on
    the same face (separating axis test in the plane) or comes within LIG_MIN of a drilled hole"""
    for c2, n2, u2, v2, h2 in PLACED_MOUNTS:
        if float(np.dot(n, n2)) < 0.9 or abs(float(np.dot(g - c2, n))) > 2.0:
            continue
        sep = False
        for ax in (u, v, u2, v2):
            r1 = half * (abs(float(np.dot(u, ax))) + abs(float(np.dot(v, ax))))
            r2 = h2 * (abs(float(np.dot(u2, ax))) + abs(float(np.dot(v2, ax))))
            if abs(float(np.dot(g - c2, ax))) >= r1 + r2 + gap:
                sep = True
                break
        if not sep:
            return True
    for c2, n2 in PLACED_HOLES:
        if abs(float(np.dot(c2 - g, n))) < 3.0:
            d = c2 - g - np.dot(c2 - g, n) * n
            if abs(float(np.dot(d, u))) < half + HOLE_D / 2 + LIG_MIN and abs(float(np.dot(d, v))) < half + HOLE_D / 2 + LIG_MIN:
                return True
    return False


def _wmesh(s, inst):
    k = inst["idx"]
    if k not in MESH_CACHE:
        MESH_CACHE[k] = s.world_mesh(inst)
    return MESH_CACHE[k]


def mount_patch(s, link, c, axis, reach, parts=None, base=None, height=None, max_dist=None, printed_only=True,
                accept=None):
    """flat base x base patch (default the MB3A 19 x 19 mm) on a printed part of `link` within `reach` of c, with the
    mount height (default 4.8 mm) free above it (exact rays against every part at the zero pose). Every face direction
    of the part near c is tried (faces grouped by normal within 15 deg): the closest point of each group is the start,
    then the base centre is shifted in that plane. printed_only=False with `parts` allows other parts of the link (the
    servo case); accept(g, n, u, v) can veto a spot. Returns dict(part, center, normal, dist, surface_mm) or None"""
    base = MOUNT_BASE if base is None else base
    height = MOUNT_H if height is None else height
    max_dist = DRESS_MAX if max_dist is None else max_dist
    cands = []
    cos_t = np.cos(np.radians(FLAT_DEG))
    for inst in s.inst:
        if inst["link"] != link or (printed_only and not inst["printed"]) or (parts and inst["key"] not in parts):
            continue
        m = _wmesh(s, inst)
        if np.any(m.bounds[0] - reach > c) or np.any(m.bounds[1] + reach < c):
            continue
        idx = np.where(np.linalg.norm(m.triangles_center - c, axis=1) <= reach + base)[0]
        if not len(idx):
            continue
        left = idx[np.argsort(-m.area_faces[idx])]
        while len(left):
            n0 = m.face_normals[left[0]]
            sel = m.face_normals[left] @ n0 >= cos_t      # faces facing the same way as the largest one left
            grp, left = left[sel], left[~sel]
            if m.area_faces[grp].sum() < 0.5 * base * base:
                continue
            sub = m.submesh([grp], append=True)
            q, d, _ = trimesh.proximity.closest_point(sub, [c])
            if d[0] <= reach:
                n = (m.face_normals[grp] * m.area_faces[grp][:, None]).sum(0)
                cands.append((float(d[0]), inst, m, q[0], n / np.linalg.norm(n)))
    cands.sort(key=lambda x: x[0])
    near_all = None
    g1 = np.linspace(-base / 2, base / 2, 5)
    shifts = sorted([(a_, b_) for a_ in MOUNT_SHIFT for b_ in MOUNT_SHIFT], key=lambda x: abs(x[0]) + abs(x[1]))
    for d0, inst, m, q, n in cands:
        u = np.asarray(axis, float) - np.dot(axis, n) * n
        if np.linalg.norm(u) < 0.2:
            u = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        if near_all is None:
            near_all = [_wmesh(s, i2) for i2 in s.inst]
        others = [mm for mm in near_all if not (np.any(mm.bounds[0] - 30 > q) or np.any(mm.bounds[1] + 30 < q))]
        for a_, b_ in shifts:
            g = q + a_ * u + b_ * v
            if np.linalg.norm(g - c) > max_dist:
                continue                   # the bundle would have to be dressed too far over to reach the mount
            if overlaps_placed(g, n, u, v, base / 2.0):
                continue                   # another mount (or a drilled hole) is already there
            pts = np.array([g + x * u + y * v for x in g1 for y in g1])
            loc, ri, ti = m.ray.intersects_location(pts + n * 2.0, np.tile(-n, (len(pts), 1)), multiple_hits=False)
            if len(ri) < len(pts):
                continue
            dist = np.linalg.norm(loc - (pts + n * 2.0)[ri], axis=1)
            if np.any(np.abs(dist - 2.0) > FLAT_TOL) or np.any(m.face_normals[ti] @ n < cos_t):
                continue
            foot = loc + n * 0.05          # just above the real surface under each sample
            clear = True
            for mm in others:
                l2, r2, _ = mm.ray.intersects_location(foot, np.tile(n, (len(foot), 1)), multiple_hits=False)
                if len(r2) and np.any(np.linalg.norm(l2 - foot[r2], axis=1) < height + 0.3):
                    clear = False
                    break
            if clear and (accept is None or accept(g, n, u, v)):
                return dict(part=inst["key"], center=g, normal=n, dist=float(np.linalg.norm(g - c)), surface_mm=d0,
                            u=u, v=v, half=base / 2.0)
    return None


FASTENERS = []


def load_fasteners():
    """screws, inserts and unused holes as capsules (a, b, radius) in world mm at the zero pose (fasteners/fasteners.json)"""
    p = os.path.join(RC.LAB, "fasteners", "fasteners.json")
    if not os.path.exists(p):
        return []
    F = json.load(open(p))
    out = []
    for f in F.get("fasteners", []):
        a, ax = np.array(f["seat_world"], float), np.array(f["axis_world"], float)
        head = f.get("head") or {}
        r = max(float(f.get("d") or 3.0), float(head.get("dk") or 0.0)) / 2.0
        k = float(head.get("k") or 0.0)
        out.append((a - ax * k, a + ax * float(f.get("length_mm") or 6.0), r, f["id"]))
    for h in F.get("empty_holes", []):
        a, ax = np.array(h["at"], float), np.array(h["axis"], float)
        for hh in h.get("holes", []):
            out.append((a, a + ax * float(hh.get("len") or 5.0), float(hh.get("d") or 3.0) / 2.0, "hole %s" % h["site"]))
    return out


def seg_seg(p1, q1, p2, q2):
    """smallest distance between segments p1q1 and p2q2"""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-12 and e < 1e-12:
        return float(np.linalg.norm(r))
    if a < 1e-12:
        s_, t = 0.0, np.clip(f / e, 0, 1)
    else:
        c = d1 @ r
        if e < 1e-12:
            t, s_ = 0.0, np.clip(-c / a, 0, 1)
        else:
            b = d1 @ d2
            den = a * e - b * b
            s_ = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
            t = (b * s_ + f) / e
            if t < 0:
                t, s_ = 0.0, np.clip(-c / a, 0, 1)
            elif t > 1:
                t, s_ = 1.0, np.clip((b - c) / a, 0, 1)
    return float(np.linalg.norm(p1 + d1 * s_ - (p2 + d2 * t)))


FK_CACHE = {}


def sweep_clear(s, link, pts, near_mm=30.0, margin=10.0, stop_below=None):
    """smallest distance (mm) from points fixed to `link` to parts of other links, every joint that moves a nearby link
    swept alone over its URDF range (13 samples), as check_cables.py does for the cables. Parts whose box stays more than
    `margin` away at a pose are skipped (the result is then 'more than margin'); stop_below ends the sweep early"""
    pts = np.atleast_2d(pts)
    others = []
    for inst in s.inst:
        if inst["link"] == link:
            continue
        m = _wmesh(s, inst)
        if float(np.min(np.linalg.norm(m.vertices - pts.mean(0), axis=1))) > 80.0:
            continue
        others.append((inst, m))
    rel = set()
    for inst, _ in others:
        rel |= set(RC.chain(PAR, link, inst["link"])[1])
    cfgs = [{}] + [{j: q} for j in sorted(rel) for q in np.linspace(RC.REV[j][0], RC.REV[j][1], 13)]
    best = 1e9
    for cfg in cfgs:
        key = tuple(sorted(cfg.items()))
        if key not in FK_CACHE:
            FK_CACHE[key] = POSER.T(cfg)
        T = FK_CACHE[key]
        W = (T[link] @ np.linalg.inv(s.T0[link]) @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
        for inst, m in others:
            ln = inst["link"]
            Q = (s.T0[ln] @ np.linalg.inv(T[ln]) @ np.c_[W, np.ones(len(W))].T).T[:, :3]
            if np.any(m.bounds[0] - margin > Q.max(0)) or np.any(m.bounds[1] + margin < Q.min(0)):
                continue
            d = -trimesh.proximity.signed_distance(m, Q)          # > 0 outside
            best = min(best, float(d.min()))
            if stop_below is not None and best < stop_below:
                return best
    return best


HOLE_WHY = {}


def tie_hole_pair(s, link, c, axis, bundle_d, reach, max_dist=None):
    """two 4.0 mm tie holes drilled through a printed wall of `link` near c, one each side of the bundle, the strap
    going through one hole, behind the wall and back out of the other. Checks (exact rays, zero pose): flat face with
    LIG_MIN of plastic round each hole and between them (edge distance r + 1.6 mm), wall thickness LIG_MIN to WALL_MAX
    at each hole, no other part inside the drilled path, STRAP_GAP free behind the wall along the strap, every screw,
    insert and unused hole at least LIG_MIN from the hole edge, the bundle room above the web, and the back strap at
    least SWEEP_GAP from parts of other links over the joint sweep. Returns a dict or None"""
    max_dist = DRESS_MAX if max_dist is None else max_dist
    r = HOLE_D / 2.0
    sp = max(bundle_d + HOLE_D, HOLE_D + LIG_MIN)            # centre spacing: hole edges at the bundle sides
    cos_t = np.cos(np.radians(FLAT_DEG))
    cands = []
    for inst in s.inst:
        if inst["link"] != link or not inst["printed"]:
            continue
        m = _wmesh(s, inst)
        if np.any(m.bounds[0] - reach > c) or np.any(m.bounds[1] + reach < c):
            continue
        idx = np.where(np.linalg.norm(m.triangles_center - c, axis=1) <= reach + sp + 10)[0]
        if not len(idx):
            continue
        left = idx[np.argsort(-m.area_faces[idx])]
        while len(left):
            n0 = m.face_normals[left[0]]
            sel = m.face_normals[left] @ n0 >= cos_t      # faces facing the same way as the largest one left
            grp, left = left[sel], left[~sel]
            if m.area_faces[grp].sum() < 2.0 * sp * HOLE_D:
                continue
            sub = m.submesh([grp], append=True)
            q, d, _ = trimesh.proximity.closest_point(sub, [c])
            if d[0] <= reach:
                n = (m.face_normals[grp] * m.area_faces[grp][:, None]).sum(0)
                cands.append((float(d[0]), inst, m, q[0], n / np.linalg.norm(n)))
    cands.sort(key=lambda x: x[0])
    allm = None
    shifts = sorted([(a_, b_) for a_ in MOUNT_SHIFT for b_ in MOUNT_SHIFT], key=lambda x: abs(x[0]) + abs(x[1]))
    ring = [np.array([np.cos(t), np.sin(t)]) for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    for d0, inst, m, q, n in cands:
        u = np.asarray(axis, float) - np.dot(axis, n) * n
        if np.linalg.norm(u) < 0.2:
            u = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        if allm is None:
            allm = [(i2, _wmesh(s, i2)) for i2 in s.inst]
        near = [(i2, mm) for i2, mm in allm if not (np.any(mm.bounds[0] - 40 > q) or np.any(mm.bounds[1] + 40 < q))]
        for a_, b_ in shifts:
            g = q + a_ * u + b_ * v
            if np.linalg.norm(g - c) > max_dist:
                continue
            H = [g - v * sp / 2, g + v * sp / 2]
            if any(np.linalg.norm(h_ - c2) < HOLE_D + LIG_MIN for h_ in H for c2, _ in PLACED_HOLES) or any(
                    overlaps_placed(h_, n, u, v, HOLE_D / 2.0 + LIG_MIN, gap=0.0) for h_ in H):
                HOLE_WHY["a mount or another tie hole already there"] = HOLE_WHY.get("a mount or another tie hole already there", 0) + 1
                continue
            # flat face round each hole (edge distance) and across the web
            pts = [h + (x * u + y * v) * (r + LIG_MIN) for h in H for x, y in ring] + H + [g]
            pts = np.array(pts)
            loc, ri, ti = m.ray.intersects_location(pts + n * 2.0, np.tile(-n, (len(pts), 1)), multiple_hits=False)
            if len(ri) < len(pts):
                HOLE_WHY["edge distance (less than 1.6 mm of plastic round a hole)"] = HOLE_WHY.get("edge distance (less than 1.6 mm of plastic round a hole)", 0) + 1
                continue
            dist = np.linalg.norm(loc - (pts + n * 2.0)[ri], axis=1)
            if np.any(np.abs(dist - 2.0) > FLAT_TOL) or np.any(m.face_normals[ti] @ n < cos_t):
                HOLE_WHY["face not flat round the holes"] = HOLE_WHY.get("face not flat round the holes", 0) + 1
                continue
            front = {int(k): loc[j] for j, k in enumerate(ri)}
            F1, F2 = front[len(pts) - 3], front[len(pts) - 2]
            # wall thickness at each hole and the drilled path through this part only
            ok, walls, backs = True, [], []
            for F in (F1, F2):
                l2, r2, _ = m.ray.intersects_location([F - n * 0.05], [-n], multiple_hits=False)
                if not len(l2):
                    ok = False
                    break
                t = float(np.linalg.norm(l2[0] - F))
                if t < LIG_MIN or t > WALL_MAX:
                    HOLE_WHY["wall under 1.6 or over 12 mm"] = HOLE_WHY.get("wall under 1.6 or over 12 mm", 0) + 1
                    ok = False
                    break
                walls.append(t)
                backs.append(F - n * t)
            if not ok:
                continue
            for i2, mm in near:
                if mm is m:
                    continue
                for F, Bk in zip((F1, F2), backs):
                    for off in [np.zeros(3)] + [(x * u + y * v) * r for x, y in ring[::2]]:
                        l3, r3, _ = mm.ray.intersects_location([F + off + n * 0.5], [-n], multiple_hits=False)
                        if len(l3) and np.linalg.norm(l3[0] - (F + off + n * 0.5)) < np.linalg.norm(Bk - F) + 0.5 + STRAP_GAP:
                            HOLE_WHY["another part (servo or bracket) in the drilled path or right behind it"] = HOLE_WHY.get("another part (servo or bracket) in the drilled path or right behind it", 0) + 1
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                continue
            # strap path behind the wall between the two hole exits
            strap = [backs[0] + (backs[1] - backs[0]) * t for t in np.linspace(0, 1, 5)]
            for i2, mm in near:
                l4, r4, _ = mm.ray.intersects_location(np.array(strap) - n * 0.05, np.tile(-n, (len(strap), 1)),
                                                       multiple_hits=False)
                if len(r4) and np.any(np.linalg.norm(l4 - (np.array(strap) - n * 0.05)[r4], axis=1) < STRAP_GAP):
                    HOLE_WHY["no 1.5 mm gap behind the wall for the strap"] = HOLE_WHY.get("no 1.5 mm gap behind the wall for the strap", 0) + 1
                    ok = False
                    break
            if not ok:
                continue
            # bundle room above the web
            for i2, mm in near:
                l5, r5, _ = mm.ray.intersects_location([g + n * 0.05], [n], multiple_hits=False)
                if len(l5) and np.linalg.norm(l5[0] - (g + n * 0.05)) < bundle_d + 1.0:
                    HOLE_WHY["no room for the bundle over the holes"] = HOLE_WHY.get("no room for the bundle over the holes", 0) + 1
                    ok = False
                    break
            if not ok:
                continue
            # screws, inserts, unused holes
            for a_f, b_f, r_f, fid in FASTENERS:
                if any(seg_seg(F, Bk, a_f, b_f) < r + r_f + LIG_MIN for F, Bk in zip((F1, F2), backs)):
                    HOLE_WHY["a screw, insert or hole within 1.6 mm"] = HOLE_WHY.get("a screw, insert or hole within 1.6 mm", 0) + 1
                    ok = False
                    break
            if not ok:
                continue
            gap_sweep = sweep_clear(s, link, np.array(strap) - n * 0.75, stop_below=SWEEP_GAP)
            if gap_sweep < SWEEP_GAP:
                HOLE_WHY["a moving part comes within 1 mm of the strap"] = HOLE_WHY.get("a moving part comes within 1 mm of the strap", 0) + 1
                continue
            Tl = s.T0[inst["link"]] @ inst["T"]
            Tinv = np.linalg.inv(Tl)
            loc_stl = [(Tinv @ np.r_[F, 1.0])[:3] for F in (F1, F2)]
            n_stl = Tinv[:3, :3] @ n
            return dict(part=inst["key"], link=inst["link"], holes_world=[F1, F2], normal=n, spacing=sp, walls=walls,
                        dist=float(np.linalg.norm(g - c)), surface_mm=d0, holes_stl=loc_stl, normal_stl=n_stl,
                        mirrored=bool(inst.get("mirrored")), sweep_gap=gap_sweep, bundle_d=float(bundle_d))
    return None


def place_retention(s, data, anchors):
    items = []
    loop_ref = {}
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
            cross = [i for i in range(len(P) - 1) if B[i] != B[i + 1]]
            k = 0
            while k < len(cross):
                # designed free section (service loop): ties pushed away from the crossing until the loop meets
                # 3 x OD in the uniform bend model and in the length storage model (docstring), or the room ends.
                # Two crossings with less than MERGE_GAP of route on the link between them make one loop (a tie on a
                # few mm of a small link, e.g. head_pitch_to_yaw, cannot be placed). The free section may run into the
                # connector zone (no tie within 25.4 mm of a connector, Table 9-2): the plug is then the fixed point
                group = [cross[k]]
                if k + 1 < len(cross) and acc[cross[k + 1]] - acc[cross[k] + 1] < MERGE_GAP:
                    group.append(cross[k + 1])
                i, i9 = group[0], group[-1]
                prev_lim = max([a for a, _ in want]) if want else 0.0
                nxt = cross[k + len(group)] if k + len(group) < len(cross) else None
                next_lim = (acc[nxt] + acc[i9 + 1]) / 2 if nxt is not None else total
                lroom, rroom = max(acc[i] - prev_lim, 0.0), max(next_lim - acc[i9 + 1], 0.0)
                lp = loop_search(s, P, acc, B, group, r["d_mm"], lroom, rroom)
                js = lp["joints"]
                a0 = acc[i] - lp["left"]
                a1 = acc[i9 + 1] + lp["right"]
                S = a1 - a0
                loops.append(dict(span=[i, i9 + 1], spans=[[g, g + 1] for g in group], joints=js,
                                  angle_rad=round(lp["th"], 3), angle_runtime_rad=round(lp["th_rt"], 3), od_mm=r["d_mm"],
                                  free_needed_mm=round(BEND_MIN * r["d_mm"] * lp["th"], 1), free_mm=round(S, 1),
                                  radius_mm=round(min(lp["unif"], lp["arc"]), 1),
                                  radius_runtime_mm=round(min(lp["unif_rt"], lp["arc_rt"]), 1),
                                  radius_bend_mm=round(lp["unif"], 1), radius_bend_runtime_mm=round(lp["unif_rt"], 1),
                                  radius_storage_mm=round(min(lp["arc"], 1e6), 1),
                                  radius_storage_runtime_mm=round(min(lp["arc_rt"], 1e6), 1),
                                  chord_min_mm=round(lp["chord_min"], 1), loop_length_mm=round(lp["length_build"], 1),
                                  dress_extra_mm=round(lp["extra"], 1),
                                  rule_mm=round(BEND_MIN * r["d_mm"], 1), ok=lp["ok"], ok_runtime=lp["ok_rt"],
                                  room_mm=[round(lroom, 1), round(rroom, 1)],
                                  ties_at_mm=[round(a0, 1), round(a1, 1)]))
                loops[-1]["_ctx"] = dict(P=P, acc=acc, B=B, i0=i, i9=i9, grid=lp["grid"])
                if len(group) > 1:
                    loops[-1]["merged"] = "one loop across %s: the link %s carries %.1f mm of route between them" % (
                        " and ".join(js), B[i + 1], float(acc[group[1]] - acc[i + 1]))
                if a0 > 1.0:
                    want.append((a0, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i], S)))
                    loop_ref[(round(a0, 4), want[-1][1])] = (loops[-1], 0)
                else:
                    loops[-1]["anchor_a"] = "connector (no tie needed)"
                if a1 < total - 1.0:
                    want.append((a1, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i9 + 1], S)))
                    loop_ref[(round(a1, 4), want[-1][1])] = (loops[-1], 1)
                else:
                    loops[-1]["anchor_b"] = "connector (no tie needed)"
                k += len(group)
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
                    extra.append((a0 + k * (a1 - a0) / (n + 1), "support spacing <= 76.2 mm (lab rule)"))
            for a, why in sorted(want + extra):
                i = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
                t = (a - acc[i]) / max(seg[i], 1e-9)
                q = P[i] + (P[i + 1] - P[i]) * t
                link = B[i] if t < 0.5 or B[i] == B[i + 1] else B[i + 1]
                ax = (P[i + 1] - P[i]) / max(seg[i], 1e-9)
                items.append(dict(cable=c["id"], run=r["name"], p=q, axis=ax, link=link, why=why, d=r["d_mm"],
                                  ref=loop_ref.get((round(a, 4), why)), a=a))
    # merge ties of the same link within TIE_NEAR
    merged = []
    for it in items:
        for m in merged:
            if m["link"] == it["link"] and np.linalg.norm(m["p"] - it["p"]) < TIE_NEAR:
                m["cables"].add(it["cable"])
                m["whys"].add(it["why"])
                m["ds"].append(it["d"])
                m["pts"].append(it["p"])
                m["refs"].append(it["ref"])
                m["items"].append(it)
                break
        else:
            merged.append(dict(link=it["link"], p=it["p"], pts=[it["p"]], axis=it["axis"], cables={it["cable"]},
                               whys={it["why"]}, ds=[it["d"]], refs=[it["ref"]], items=[it]))
    for k, m in enumerate(merged):            # each loop end names the tie that holds it
        for ref in m["refs"]:
            if ref:
                lp_, side = ref
                lp_.setdefault("tie_ids", [None, None])[side] = "T%03d" % (k + 1)
    an = [a for a in anchors]
    out = []

    PLACED_MOUNTS.clear()
    PLACED_HOLES.clear()

    def fit_record(f, typ):
        PLACED_MOUNTS.append((np.array(f["center"]), np.array(f["normal"]), np.array(f["u"]), np.array(f["v"]), f["half"]))
        return dict(type=typ, part=f["part"], center_mm=[round(float(x), 1) for x in f["center"]],
                    normal=[round(float(x), 3) for x in f["normal"]], from_cable_mm=round(f["dist"], 1))

    def find_mount(link, c, axis, reach, max_dist):
        """MB3A (BOM 34) first, then the small mount (BOM 34b)"""
        for typ, base, h in (("MB3A", MOUNT_BASE, MOUNT_H), (SMALL_TYPE, SMALL_BASE, SMALL_H)):
            f = mount_patch(s, link, c, axis, reach, base=base, height=h, max_dist=max_dist)
            if f:
                return f, typ
        return None, None

    def mount_text(typ):
        return "MB3A (BOM 34)" if typ == "MB3A" else "Panduit ABM1M-AT-C 12.7 x 12.7 mm (BOM 34b)"

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
        part, gap, fit = None, False, None
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
                mw = _wmesh(s, inst)
                if np.any(mw.bounds[0] - 25 > c) or np.any(mw.bounds[1] + 25 < c):
                    continue
                d = float(abs(trimesh.proximity.signed_distance(mw, [c])[0]))
                if near is None or d < near[0]:
                    near = (d, inst["key"])
            gap = True
            if near and near[0] <= ANCHOR_REACH:
                kind, part = "adhesive tie mount", near[1]
                f, typ = find_mount(m["link"], c, m["axis"], ANCHOR_REACH, DRESS_MAX)
                if f:
                    part, fit = f["part"], fit_record(f, typ)
                    note = ("GAP: no tie anchor in the CAD here; stick-on tie mount %s on a flat patch of %s, %.0f mm from "
                            "the cable line (exact rays)" % (mount_text(typ), part, f["dist"]))
                else:
                    fit = dict(type=None)
                    note = "NO FLAT PATCH"   # resolved below
            else:
                kind = "cable tie"
                note = "FREE AIR"            # resolved below, once every anchored neighbour is known
        out.append(dict(id="T%03d" % (k + 1), cables=sorted(m["cables"]), kind=kind, gap=gap, center_mm=[round(float(x), 1) for x in c],
                        axis=[round(float(x), 3) for x in m["axis"]], link=m["link"], part=part,
                        p=[round(float(x), 2) for x in (np.linalg.inv(s.T0[m["link"]]) @ np.r_[c, 1.0])[:3]],
                        bundle_d_mm=round(bundle, 1), tie="nylon cable tie 2.5 x 100 mm" if bundle <= 20 else "nylon cable tie 3.6 x 150 mm",
                        why=sorted(m["whys"]), note=note, mount_fit=fit,
                        loop_end=any(w_.startswith("joint crossing") for w_ in m["whys"])))
    # D25 order for the points still without an anchor (free air, or a mount spot with no flat patch):
    # (i) tie to an anchored neighbour cable, (ii) a drilled tie-hole pair through the printed bracket,
    # (iii) the tie moved: a mount or hole pair on a printed part of the link up to 25 mm away (not at a loop end),
    # else open with the reason
    segs = {}                   # cable -> [(link, a, b, d)] fixed route pieces at the zero pose
    for c_ in data["cables"]:
        for r in c_.get("runs", []):
            P, B = run_world(s, r)
            for i in range(len(P) - 1):
                if B[i] == B[i + 1]:
                    segs.setdefault(c_["id"], []).append((B[i], P[i], P[i + 1], r["d_mm"]))

    def seg_dist(q, a, b):
        ab = b - a
        t = np.clip(np.dot(q - a, ab) / max(np.dot(ab, ab), 1e-9), 0.0, 1.0)
        return float(np.linalg.norm(q - (a + t * ab)))

    def what_of(t):
        return ("free air, no printed part within 15 mm on this link" if t["note"] == "FREE AIR" else
                "no flat patch for a 19 x 19 mm (MB3A) or 12.7 x 12.7 mm (ABM1M) stick-on mount within 15 mm of %s" % t["part"])

    def neighbour(t):
        anchored = [u for u in out if not u.get("merged_into") and (u["kind"] in ("existing printed feature", "drilled printed feature")
                    or (u["kind"] == "adhesive tie mount" and (u.get("mount_fit") or {}).get("type")))]
        c = np.array(t["center_mm"])
        best = None
        for u in anchored:
            if u["link"] != t["link"] or set(u["cables"]) & set(t["cables"]):
                continue
            du = float(np.linalg.norm(np.array(u["center_mm"]) - c))
            if du > NEIGH_ANCHOR:
                continue
            for k_ in u["cables"]:
                for ln, a, b, d in segs.get(k_, []):
                    if ln != t["link"]:
                        continue
                    gap_ = seg_dist(c, a, b) - t["bundle_d_mm"] / 2 - d / 2
                    if gap_ <= NEIGH_GAP and (best is None or gap_ < best[0]):
                        best = (gap_, k_, u["id"], du)
        return best

    def hole_record(h):
        for p_ in h["holes_world"]:
            PLACED_HOLES.append((np.array(p_, float), np.array(h["normal"], float)))
        return dict(part=h["part"], link=h["link"], hole_d_mm=HOLE_D, spacing_mm=round(h["spacing"], 1),
                    holes_world=[[round(float(x), 1) for x in p_] for p_ in h["holes_world"]],
                    normal_world=[round(float(x), 3) for x in h["normal"]],
                    holes_stl=[[round(float(x), 1) for x in p_] for p_ in h["holes_stl"]],
                    normal_stl=[round(float(x), 3) for x in h["normal_stl"]], mirrored=h["mirrored"],
                    wall_mm=[round(w_, 1) for w_ in h["walls"]], from_cable_mm=round(h["dist"], 1),
                    sweep_gap_mm=round(h["sweep_gap"], 1), for_bundle_mm=round(h["bundle_d"], 1))

    todo = [t for t in out if t["note"] in ("FREE AIR", "NO FLAT PATCH")]
    for t in todo:
        t["what"] = what_of(t)
    T0_ = time.time()
    print("retention: %d tie points, %d without an anchor after the mount pass" % (len(out), len(todo)), flush=True)

    def anchor_at(u):
        """where the anchor of a held tie point is (None if it holds nothing by itself)"""
        if u.get("merged_into") or u.get("open"):
            return None
        mf = u.get("mount_fit") or {}
        if u["kind"] == "adhesive tie mount" and mf.get("type"):
            return np.array(mf["center_mm"])
        if u["kind"] == "drilled printed feature" and u.get("tie_holes"):
            return np.mean(np.array(u["tie_holes"]["holes_world"]), 0)
        if u["kind"] == "existing printed feature":
            return np.array(u["center_mm"])
        return None

    def join(t, u, d):
        """merge tie point t into u: both bundles on u's anchor, one tie round both"""
        u["cables"] = sorted(set(u["cables"]) | set(t["cables"]))
        u["why"] = sorted(set(u["why"]) | set(t["why"]))
        u["bundle_d_mm"] = round(float(np.hypot(u["bundle_d_mm"], t["bundle_d_mm"])), 1)
        u["loop_end"] = bool(u["loop_end"] or t["loop_end"])
        u.setdefault("also_holds", []).append(dict(tie=t["id"], cables=t["cables"], center_mm=t["center_mm"],
                                                   to_anchor_mm=round(d, 1)))
        u["note"] += ("; one anchor per spot: also holds %s from tie point %s, dressed %.0f mm over to it (one tie round "
                      "both bundles)" % (", ".join(t["cables"]), t["id"], d))
        t.update(merged_into=u["id"], done=True)

    def share(t, c=None):
        """a point with no anchor of its own joins the nearest anchor (mount, drilled pair or stock hole) of another tie
        of its link within the dressing distance (DRESS_MAX at a loop end, FREE_MOUNT_REACH elsewhere)"""
        c = np.array(t["center_mm"]) if c is None else c
        lim = DRESS_MAX if t["loop_end"] else FREE_MOUNT_REACH
        best = None
        for u in out:
            if u is t or u["link"] != t["link"]:
                continue
            q = anchor_at(u)
            if q is None:
                continue
            d = float(np.linalg.norm(q - c))
            if d <= lim and (best is None or d < best[0]):
                best = (d, u)
        if not best:
            return False
        join(t, best[1], best[0])
        return True
    n_sh = sum(1 for t in todo if share(t))
    print("  shared mounts: %d tie points joined a mount placed for a nearby tie" % n_sh, flush=True)
    for rnd in range(2):           # a hole pair made in round 0 can anchor a neighbour in round 1
        for t in todo:
            if t.get("done"):
                continue
            best = neighbour(t)
            if best:
                t.update(kind="cable tie to a neighbour cable", tied_to=best[1], anchor_tie=best[2], mount_fit=None, part=None,
                         done=True, note="GAP: %s; tied to the neighbour cable %s (surface gap %.1f mm), which tie %s holds "
                                         "%.0f mm away (D25 i)" % (t["what"], best[1], max(best[0], 0.0), best[2], best[3]))
                continue
            if rnd == 1:
                continue
            c = np.array(t["center_mm"])
            h = tie_hole_pair(s, t["link"], c, np.array(t["axis"]), t["bundle_d_mm"], ANCHOR_REACH)
            if h:
                t.update(kind="drilled printed feature", part=h["part"], mount_fit=None, tie_holes=hole_record(h), done=True,
                         note="GAP: %s; drill two %.1f mm tie holes %.1f mm apart through %s (wall %s mm), the strap behind "
                              "the wall, %.0f mm from the cable line (D25 ii, print/PRINT_PLAN.md After printing)" % (
                                  t["what"], HOLE_D, h["spacing"], h["part"], " and ".join("%.1f" % w_ for w_ in h["walls"]),
                                  h["dist"]))
    # (iii) loop-end ties moved outward along the route (the loop only gets longer) until an anchor fits there;
    # every loop through the point must still meet the rule at the new tie position
    def slide(t, k):
        mem = merged[k]["items"]
        if any(it["ref"] is None for it in mem):
            return False
        for dlt in np.arange(2.0, 31.0, 2.0):
            moves, okm = [], True
            for it in mem:
                lp_, side = it["ref"]
                cx = lp_["_ctx"]
                g = cx["grid"]
                left = cx["acc"][cx["i0"]] - lp_["ties_at_mm"][0]
                right = lp_["ties_at_mm"][1] - cx["acc"][cx["i9"] + 1]
                L2, R2 = (left + dlt, right) if side == 0 else (left, right + dlt)
                li, ri_ = int(round(L2)), int(round(R2))
                if li >= len(g["Ls"]) or ri_ >= len(g["Rs"]) or not g["ok"][li, ri_]:
                    okm = False
                    break
                a_new = cx["acc"][cx["i0"]] - L2 if side == 0 else cx["acc"][cx["i9"] + 1] + R2
                jj = int(np.clip(np.searchsorted(cx["acc"], a_new) - 1, 0, len(cx["P"]) - 2))
                if cx["B"][jj] != it["link"] or cx["B"][jj + 1] != it["link"]:
                    okm = False
                    break
                moves.append((it, lp_, side, li, ri_, a_new, _along(cx["P"], cx["acc"], a_new)))
            if not okm:
                break                         # further out only leaves the room or the link
            pts_ = np.array([mv[6] for mv in moves])
            c2 = pts_.mean(0)
            if np.max(np.linalg.norm(pts_ - c2, axis=1)) > TIE_NEAR:
                continue
            found = None
            near_u = [u_ for u_ in out if u_ is not t and not u_.get("merged_into") and u_["link"] == t["link"]
                      and np.linalg.norm(np.array(u_["center_mm"]) - c2) < TIE_NEAR]
            if near_u:
                held = [u_ for u_ in near_u if anchor_at(u_) is not None]
                if not held:
                    continue                  # another tie of this link is already there and holds nothing: go on
                found = ("share", held[0])
            for a in an:
                if found:
                    break
                if a["link"] == t["link"] and np.linalg.norm(np.array(a["center_mm"]) - c2) <= ANCHOR_REACH:
                    found = ("feature", a)
            if not found:
                f, typ = find_mount(t["link"], c2, np.array(t["axis"]), ANCHOR_REACH, DRESS_MAX)
                if f:
                    found = ("mount", (f, typ))
            if not found:
                h = tie_hole_pair(s, t["link"], c2, np.array(t["axis"]), t["bundle_d_mm"], ANCHOR_REACH)
                if h:
                    found = ("holes", h)
            if not found:
                continue
            for it, lp_, side, li, ri_, a_new, q in moves:      # apply: the loop numbers at the new tie position
                g = lp_["_ctx"]["grid"]
                lp_["ties_at_mm"][side] = round(float(a_new), 1)
                lp_.update(free_mm=round(float(g["S"][li, ri_]), 1),
                           radius_bend_mm=round(float(g["unif"][li, ri_]), 1),
                           radius_storage_mm=round(float(min(g["arc"][li, ri_], 1e6)), 1),
                           radius_bend_runtime_mm=round(float(g["unif_rt"][li, ri_]), 1),
                           radius_storage_runtime_mm=round(float(min(g["arc_rt"][li, ri_], 1e6)), 1),
                           radius_mm=round(float(min(g["unif"][li, ri_], g["arc"][li, ri_])), 1),
                           radius_runtime_mm=round(float(min(g["unif_rt"][li, ri_], g["arc_rt"][li, ri_])), 1),
                           chord_min_mm=round(float(g["cmin"][li, ri_]), 1), loop_length_mm=round(float(g["Lmax"][li, ri_]), 1),
                           ok=bool(g["ok"][li, ri_]), tie_moved_mm=round(float(dlt), 1))
                lp_["ok_runtime"] = bool(g["unif_rt"][li, ri_] >= g["rule"] and g["arc_rt"][li, ri_] >= g["rule"])
            t["center_mm"] = [round(float(x), 1) for x in c2]
            t["p"] = [round(float(x), 2) for x in (np.linalg.inv(s.T0[t["link"]]) @ np.r_[c2, 1.0])[:3]]
            moved = "the loop tie moved %.0f mm further from the joint (the loop meets 3 x OD there too); " % dlt
            if found[0] == "share":
                u = found[1]
                t["note"] = "GAP: %s; %sit joins tie %s there (D25 iii)" % (t["what"], moved, u["id"])
                join(t, u, float(np.linalg.norm(anchor_at(u) - c2)))
                return True
            if found[0] == "feature":
                a = found[1]
                t.update(kind="existing printed feature", part=a["part"], mount_fit=None, gap=False, done=True,
                         note="%scable tie through the %s %.1f x %.1f mm in %s (D25 iii)" % (
                             moved, a["kind"], a["size_mm"][0], a["size_mm"][1], a["part"]))
            elif found[0] == "mount":
                f, typ = found[1]
                t.update(kind="adhesive tie mount", part=f["part"], mount_fit=fit_record(f, typ), done=True,
                         note="GAP: %s; %sstick-on tie mount %s on a flat patch of %s, %.0f mm from the cable line (D25 iii)" % (
                             t["what"], moved, mount_text(typ), f["part"], f["dist"]))
            else:
                h = found[1]
                t.update(kind="drilled printed feature", part=h["part"], mount_fit=None, tie_holes=hole_record(h), done=True,
                         note="GAP: %s; %sdrill two %.1f mm tie holes %.1f mm apart through %s (wall %s mm), %.0f mm from the "
                              "cable line (D25 ii and iii, print/PRINT_PLAN.md After printing)" % (
                                  t["what"], moved, HOLE_D, h["spacing"], h["part"], " and ".join("%.1f" % w_ for w_ in h["walls"]),
                                  h["dist"]))
            return True
        return False
    print("  D25 i and ii done in %.0f s: %d left" % (time.time() - T0_, sum(1 for t in todo if not t.get("done"))), flush=True)
    for k, t in enumerate(out):
        if t in todo and not t.get("done") and t["loop_end"]:
            slide(t, k)
    print("  D25 iii slides done in %.0f s: %d left" % (time.time() - T0_, sum(1 for t in todo if not t.get("done"))), flush=True)
    for t in todo:
        if t.get("done"):
            continue
        best = neighbour(t)                   # anchors made by the slides can hold a neighbour now
        if best:
            t.update(kind="cable tie to a neighbour cable", tied_to=best[1], anchor_tie=best[2], mount_fit=None, part=None,
                     done=True, note="GAP: %s; tied to the neighbour cable %s (surface gap %.1f mm), which tie %s holds "
                                     "%.0f mm away (D25 i)" % (t["what"], best[1], max(best[0], 0.0), best[2], best[3]))
    # (iv) loop ends still without an anchor: a stick-on mount on the STS3215 case of the same link (not printed, but
    # fixed to the link), the base CONN_KEEP clear of the servo plugs and the mount and bundle SWEEP_GAP clear of every
    # moving part over the joint sweep. Adhesion of the mount tape to the case plastic is not published: pull check at
    # the dry fit
    ends = [(np.array(e["p_world0"], float), np.array(e.get("dir_world0") or [0.0, 0.0, 0.0], float), e["link"])
            for e in data.get("cable_ends", []) if e.get("p_world0")]

    def case_accept(link, base, height, bundle_d, keep):
        def acc_(g, n, u, v):
            corners = [g + (x * u + y * v) * base / 2.0 for x in (-1, 1) for y in (-1, 1)]
            for p0, d0, ln in ends:
                if ln == link and min(seg_dist(q_, p0 - d0 * PLUG_LEN, p0 + d0 * PLUG_LEN) for q_ in corners + [g]) < CONN_KEEP:
                    return False
            pts = np.array([q_ + n * height for q_ in corners] + [g + n * (height + bundle_d)])
            keep["sweep"] = sweep_clear(s, link, pts, margin=3.0, stop_below=SWEEP_GAP)
            return keep["sweep"] >= SWEEP_GAP
        return acc_
    for t in todo:
        if t.get("done") or not t["loop_end"]:
            continue
        c = np.array(t["center_mm"])
        cases = sorted({i_["key"] for i_ in s.inst if i_["link"] == t["link"] and i_["key"] in SERVO_CASE})
        for typ, base, h in (("MB3A", MOUNT_BASE, MOUNT_H), (SMALL_TYPE, SMALL_BASE, SMALL_H)):
            keep = {}
            f = mount_patch(s, t["link"], c, np.array(t["axis"]), ANCHOR_REACH, parts=cases, base=base, height=h,
                            max_dist=DRESS_MAX, printed_only=False,
                            accept=case_accept(t["link"], base, h, t["bundle_d_mm"], keep)) if cases else None
            if f:
                fit = fit_record(f, typ)
                fit.update(on_servo_case=True, sweep_gap_mm=None if keep["sweep"] > 1e6 else round(keep["sweep"], 1))
                t.update(kind="adhesive tie mount", part=f["part"], mount_fit=fit, done=True,
                         note="GAP: %s; no anchored neighbour cable within 4 mm and no tie-hole pair that passes the checks; "
                              "stick-on tie mount %s on a flat face of the STS3215 servo case (%s) of this link, %.0f mm from "
                              "the cable line, %.0f mm or more from the servo plugs, %s from moving parts over the joint "
                              "sweep (D25 iv [L]; the tape's hold on the case plastic is not published: pull check at the "
                              "dry fit)" % (t["what"], mount_text(typ), f["part"], f["dist"], CONN_KEEP,
                                            "more than 3 mm" if keep["sweep"] > 1e6 else "%.1f mm" % keep["sweep"]))
                break
    print("  D25 iv servo cases done in %.0f s: %d left" % (time.time() - T0_, sum(1 for t in todo if not t.get("done"))), flush=True)
    for t in todo:
        if not t.get("done"):
            share(t)                          # mounts placed by the passes above
    for t in todo:
        if t.get("done"):
            continue
        c = np.array(t["center_mm"])
        if not t["loop_end"]:
            f, typ = find_mount(t["link"], c, np.array(t["axis"]), FREE_MOUNT_REACH, FREE_MOUNT_REACH)
            if f:
                t.update(kind="adhesive tie mount", part=f["part"], mount_fit=fit_record(f, typ), done=True,
                         note="GAP: %s; stick-on tie mount %s on a flat patch of %s %.0f mm away: dress the bundle over to "
                              "it (D25 iii)" % (t["what"], mount_text(typ), f["part"], f["dist"]))
                continue
            h = tie_hole_pair(s, t["link"], c, np.array(t["axis"]), t["bundle_d_mm"], FREE_MOUNT_REACH, FREE_MOUNT_REACH)
            if h:
                t.update(kind="drilled printed feature", part=h["part"], mount_fit=None, tie_holes=hole_record(h), done=True,
                         note="GAP: %s; drill two %.1f mm tie holes %.1f mm apart through %s (wall %s mm) %.0f mm away and "
                              "dress the bundle over to them (D25 ii and iii, print/PRINT_PLAN.md After printing)" % (
                                  t["what"], HOLE_D, h["spacing"], h["part"], " and ".join("%.1f" % w_ for w_ in h["walls"]),
                                  h["dist"]))
                continue
        near = None
        for inst in s.inst:
            if inst["link"] != t["link"] or not inst["printed"]:
                continue
            mw = _wmesh(s, inst)
            d = float(abs(trimesh.proximity.signed_distance(mw, [c])[0]))
            if near is None or d < near[0]:
                near = (d, inst["key"])
        HOLE_WHY.clear()
        tie_hole_pair(s, t["link"], c, np.array(t["axis"]), t["bundle_d_mm"], FREE_MOUNT_REACH, FREE_MOUNT_REACH)
        why_h = sorted(HOLE_WHY.items(), key=lambda x: -x[1])
        t["open"] = True
        t["hole_rejects"] = dict(why_h)
        t["note"] = ("GAP: %s; no anchored neighbour cable within 4 mm, no tie-hole pair that passes the checks%s, and the "
                     "loop tie cannot move further (room or link ends): OPEN (nearest printed part %s, %.0f mm away; tie-hole "
                     "candidates within 25 mm rejected for: %s)" % (
                         t["what"], "" if t["loop_end"] else " and no mount or hole pair within 25 mm",
                         near[1] if near else "-", near[0] if near else 0.0,
                         "; ".join("%s (%d)" % (k_, v_) for k_, v_ in why_h[:3]) or "no printed face of this link within 25 mm"))
    remap = {t["id"]: t["merged_into"] for t in out if t.get("merged_into")}
    for c_ in data["cables"]:
        for r in c_.get("runs", []):
            for lp_ in r.get("service_loops", []):
                lp_["tie_ids"] = [remap.get(x, x) for x in lp_.get("tie_ids", [None, None])]
    out = [t for t in out if not t.get("merged_into")]
    for t in out:
        t.pop("done", None)
        t.pop("what", None)
        if t.get("anchor_tie") in remap:
            t["anchor_tie"] = remap[t["anchor_tie"]]
    return out

PLAN_REACH = 40.0          # mm: how far from an open point a route change may bring the bundle to an anchor [L]


def open_plans(s, data):
    """a named plan for every open tie point (D25: nothing open without one). The same anchors are searched again with
    the bundle moved up to PLAN_REACH from the present route (a route change, D25 iii): a mount on a printed face, then a
    tie-hole pair. If none fits, the plan is a printed tie anchor (a design change for the print side)"""
    out = []
    for t in data.get("retention", []):
        if not t.get("open"):
            continue
        c, ax = np.array(t["center_mm"]), np.array(t["axis"])
        plan = None
        for typ, base, h in (("MB3A", MOUNT_BASE, MOUNT_H), (SMALL_TYPE, SMALL_BASE, SMALL_H)):
            f = mount_patch(s, t["link"], c, ax, PLAN_REACH, base=base, height=h, max_dist=PLAN_REACH)
            if f:
                plan = ("route change (D25 iii): bring %s %.0f mm over to the flat patch of %s at %s (world, zero pose) and "
                        "stick a %s there; then re-run route_cables.py and seats_ties.py so the loop is checked again" % (
                            ", ".join(t["cables"]), f["dist"], f["part"], [round(float(x), 1) for x in f["center"]],
                            "MB3A (BOM 34)" if typ == "MB3A" else "ABM1M-AT-C (BOM 34b)"))
                break
        if not plan:
            hp = tie_hole_pair(s, t["link"], c, ax, t["bundle_d_mm"], PLAN_REACH, PLAN_REACH)
            if hp:
                plan = ("route change (D25 iii): bring %s %.0f mm over to a 4.0 mm tie-hole pair %.1f mm apart in %s (walls "
                        "%s mm, centres %s in the part STL frame); then re-run route_cables.py and seats_ties.py" % (
                            ", ".join(t["cables"]), hp["dist"], hp["spacing"], hp["part"],
                            " and ".join("%.1f" % w_ for w_ in hp["walls"]),
                            "; ".join(str([round(float(x), 1) for x in q]) for q in hp["holes_stl"])))
        if not plan:
            near = None
            for inst in s.inst:
                if inst["link"] != t["link"] or not inst["printed"]:
                    continue
                d = float(abs(trimesh.proximity.signed_distance(_wmesh(s, inst), [c])[0]))
                if near is None or d < near[0]:
                    near = (d, inst["key"])
            plan = ("printed tie anchor (design change for the print side): no mount or hole pair within %.0f mm of the "
                    "route and no servo-case spot within 20 mm; the nearest printed part of %s is %s, %.0f mm away. Until "
                    "it exists: a tie round the bundle only, and turn the joints by hand at the TEST_PLAN 1.4 dry fit" % (
                        PLAN_REACH, t["link"], near[1] if near else "-", near[0] if near else 0.0))
        t["plan"] = plan
        out.append((t["id"], plan))
    return out


PAR = {}


def main():
    global POSER
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", default=RC.OUT_JSON, help="cables3d.json to read and rewrite (default: the lab file)")
    ap.add_argument("--plans-only", action="store_true", help="only (re)write the plan of every open tie point")
    a = ap.parse_args()
    t0 = time.time()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    PAR.update(RC.tree(s))
    POSER = RC.Poser(s)
    FASTENERS[:] = load_fasteners()
    data = json.load(open(a.json))
    if a.plans_only:
        for k, v in open_plans(s, data):
            print(k, v, flush=True)
        RC.write_json_atomic(data, a.json)
        print("plans written in %.1f s" % (time.time() - t0))
        return
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
    for k, v in open_plans(s, data):
        print("open %s: %s" % (k, v), flush=True)
    for c in data["cables"]:
        for r in c.get("runs", []):
            for lp_ in r.get("service_loops", []):
                for k_ in [k_ for k_ in lp_ if k_.startswith("_")]:
                    lp_.pop(k_)
    data["tie_anchors"] = anchors
    kinds = {}
    for t in data["retention"]:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    data["meta"]["retention"] = dict(script="altaay_lab/cables3d/seats_ties.py", count=len(data["retention"]), by_kind=kinds,
                                     rule="both sides of every joint crossing, loop ties pushed out until the loop meets 3 x OD "
                                          "(NASA-STD-8739.4A Table 7-1) in the uniform bend and length storage models; first "
                                          "tie 25.4-50.8 mm from each connector (Table 9-2); support <= 76.2 mm apart (lab "
                                          "rule, not Table 9-1); merged within 8 mm; stick-on mounts on a flat patch (MB3A 19 x 19 "
                                          "mm, BOM 34, else ABM1M-AT-C 12.7 x 12.7 mm, BOM 34b), one per spot; the rest in the "
                                          "D25 order: neighbour tie, drilled tie-hole pair, tie moved along the route, servo-case "
                                          "mount; open points carry a named plan",
                                     generated_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
    RC.write_json_atomic(data, a.json)
    print("retention items %d %s in %.1f s" % (len(data["retention"]), kinds, time.time() - t0))


if __name__ == "__main__":
    main()
