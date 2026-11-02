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
  mount_fit.type = "MB3A" (BOM line 34, 19 x 19 x 4.8 mm) where it fits, else "MB2APT" (13 x 13 x 4.1 mm, a smaller
  HellermannTyton mount, not in the BOM: a proposal), else None.
  A point still without an anchor (free air: no printed surface within 15 mm; or a mount spot with no flat patch) is
  resolved in this order:
  a. tied to a neighbour cable that passes within 4 mm and is held by its own mount or printed feature within 20 mm
     (kind "cable tie to a neighbour cable");
  b. else (not at a loop end) a mount on a flat patch of a printed part of the same link within 25 mm, the bundle dressed
     over to it (kind "adhesive tie mount");
  c. else left open ("open": true; free-air points keep kind "cable tie"): a printed guide or a route change is needed.
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
MOUNT_BASE, MOUNT_H = 19.0, 4.8   # HellermannTyton MB3A (BOM line 34 spec sheet): base 19.0 x 19.0 mm, 4.8 mm high
FLAT_TOL, FLAT_DEG = 0.4, 15.0     # [L] flat patch: surface within 0.4 mm of the mount plane, normals within 15 deg
MOUNT_SHIFT = (0.0, 4.0, -4.0, 8.0, -8.0, 12.0, -12.0)   # mm, in-plane shifts of the mount centre tried (bundle dressed onto it)
FREE_MOUNT_REACH = 25.0    # mm: free-air point, farthest printed surface of the same link a mount may go on
DRESS_MAX, DRESS_MAX_LOOP = 20.0, 20.0   # mm: farthest mount centre from the cable line, also at a loop end [L]
NEIGH_GAP, NEIGH_ANCHOR = 4.0, 20.0   # mm: neighbour bundle surface gap, and its own anchor within this distance
SMALL_BASE, SMALL_H = 13.0, 4.1   # HellermannTyton MB2APT (151-00996): 13.0 x 13.0 x 4.1 mm, ties up to 2.7 mm wide, modified
                                  # acrylate (HellermannTyton Product Catalogue 2016/2017 p. 1.7, read 2026-11-02 1:53 AM ET at
                                  # https://docs.rs-online.com/fd67/0900766b8139134b.pdf); not in the BOM: a proposal
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


def loop_search(s, P, acc, B, i, js, od, lroom, rroom):
    """free loop across the crossing at span i: ties `left` mm before the span start and `right` mm after its end.
    Returns the shortest (left, right) that meets 3 x OD in both models (uniform bend and length storage), or the best
    one inside the room, with the loop numbers"""
    la, lb = B[i], B[i + 1]
    Ls = np.arange(0.0, min(lroom, LOOP_CAP) + 1e-9, 1.0)
    Rs = np.arange(0.0, min(rroom, LOOP_CAP) + 1e-9, 1.0)
    QA = np.array([_along(P, acc, acc[i] - x) for x in Ls])
    QB = np.array([_along(P, acc, acc[i + 1] + x) for x in Rs])
    pa = (np.linalg.inv(s.T0[la]) @ np.c_[QA, np.ones(len(QA))].T).T[:, :3]
    pb = (np.linalg.inv(s.T0[lb]) @ np.c_[QB, np.ones(len(QB))].T).T[:, :3]
    s0a = (np.linalg.inv(s.T0[la]) @ np.r_[P[i], 1.0])[:3]
    s0b = (np.linalg.inv(s.T0[lb]) @ np.r_[P[i + 1], 1.0])[:3]

    def sweep(ranges):
        n = {1: 61, 2: 21, 3: 9}.get(len(js), 5)
        grids = np.meshgrid(*[np.linspace(ranges[j][0], ranges[j][1], n) for j in js], indexing="ij")
        cmin, smax = np.full((len(Ls), len(Rs)), np.inf), 0.0
        for q in zip(*[g.ravel() for g in grids]):
            T = POSER.T(dict(zip(js, q)))
            A = (T[la] @ np.c_[pa, np.ones(len(pa))].T).T[:, :3]
            Bw = (T[lb] @ np.c_[pb, np.ones(len(pb))].T).T[:, :3]
            cmin = np.minimum(cmin, np.linalg.norm(A[:, None, :] - Bw[None, :, :], axis=2))
            smax = max(smax, float(np.linalg.norm((T[lb] @ np.r_[s0b, 1.0])[:3] - (T[la] @ np.r_[s0a, 1.0])[:3])))
        return cmin, smax
    rt = dict(RC.REV)
    rt.update({j: v for j, v in RC.RUNTIME.items()})
    cmin, smax = sweep(RC.REV)
    cmin_rt, _ = sweep(rt) if any(j in RC.RUNTIME for j in js) else (cmin, smax)
    th = sum(max(abs(RC.REV[j][0]), abs(RC.REV[j][1])) for j in js)
    th_rt = sum(max(abs(rt[j][0]), abs(rt[j][1])) for j in js)
    span0 = float(acc[i + 1] - acc[i])
    S = Ls[:, None] + Rs[None, :] + span0
    Lmax = Ls[:, None] + Rs[None, :] + smax            # cable the loop needs at the farthest pose
    unif, unif_rt = S / max(th, 1e-9), S / max(th_rt, 1e-9)
    arc, arc_rt = arc_radius_v(cmin, Lmax), arc_radius_v(cmin_rt, Lmax)
    rule = BEND_MIN * od - 0.05
    ok = (unif >= rule) & (arc >= rule)
    if ok.any():
        tot = np.where(ok, Ls[:, None] + Rs[None, :] - 1e-3 * np.minimum(arc, 1e3), np.inf)
        a, b = np.unravel_index(int(np.argmin(tot)), tot.shape)
    else:
        score = np.minimum(np.minimum(unif, arc), 1e6) - 1e-3 * (Ls[:, None] + Rs[None, :])
        a, b = np.unravel_index(int(np.argmax(score)), score.shape)
    return dict(left=float(Ls[a]), right=float(Rs[b]), free=float(S[a, b]), th=th, th_rt=th_rt,
                unif=float(unif[a, b]), unif_rt=float(unif_rt[a, b]), arc=float(arc[a, b]), arc_rt=float(arc_rt[a, b]),
                chord_min=float(cmin[a, b]), length_build=float(Lmax[a, b]), extra=float(smax - span0),
                ok=bool(unif[a, b] >= rule and arc[a, b] >= rule),
                ok_rt=bool(unif_rt[a, b] >= rule and arc_rt[a, b] >= rule))


MESH_CACHE = {}


def _wmesh(s, inst):
    k = inst["idx"]
    if k not in MESH_CACHE:
        MESH_CACHE[k] = s.world_mesh(inst)
    return MESH_CACHE[k]


def mount_patch(s, link, c, axis, reach, parts=None, base=None, height=None, max_dist=None):
    """flat base x base patch (default the MB3A 19 x 19 mm) on a printed part of `link` within `reach` of c, with the
    mount height (default 4.8 mm) free above it (exact rays against every part at the zero pose). Every face direction
    of the part near c is tried (faces grouped by normal within 15 deg): the closest point of each group is the start,
    then the base centre is shifted in that plane. Returns dict(part, center, normal, dist, surface_mm) or None"""
    base = MOUNT_BASE if base is None else base
    height = MOUNT_H if height is None else height
    max_dist = DRESS_MAX if max_dist is None else max_dist
    cands = []
    cos_t = np.cos(np.radians(FLAT_DEG))
    for inst in s.inst:
        if inst["link"] != link or not inst["printed"] or (parts and inst["key"] not in parts):
            continue
        m = _wmesh(s, inst)
        if np.any(m.bounds[0] - reach > c) or np.any(m.bounds[1] + reach < c):
            continue
        idx = np.where(np.linalg.norm(m.triangles_center - c, axis=1) <= reach + base)[0]
        if not len(idx):
            continue
        left = list(idx[np.argsort(-m.area_faces[idx])])
        while left:
            n0 = m.face_normals[left[0]]
            grp = [f for f in left if m.face_normals[f] @ n0 >= cos_t]
            left = [f for f in left if f not in set(grp)]
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
            if clear:
                return dict(part=inst["key"], center=g, normal=n, dist=float(np.linalg.norm(g - c)), surface_mm=d0)
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
            for i in range(len(P) - 1):
                if B[i] != B[i + 1]:
                    # designed free section (service loop): ties pushed away from the crossing until the loop meets
                    # 3 x OD in the uniform bend model and in the length storage model (docstring), or the room ends.
                    # The free section may run into the connector zone (no tie within 25.4 mm of a connector, Table 9-2):
                    # the plug is then the fixed point on that side
                    js = RC.chain(PAR, B[i], B[i + 1])[1]
                    prev_lim = max([a for a, _ in want]) if want else 0.0
                    nxt = [acc[k] for k in range(i + 1, len(P) - 1) if B[k] != B[k + 1]]
                    next_lim = (nxt[0] + acc[i + 1]) / 2 if nxt else total
                    lroom, rroom = max(acc[i] - prev_lim, 0.0), max(next_lim - acc[i + 1], 0.0)
                    lp = loop_search(s, P, acc, B, i, js, r["d_mm"], lroom, rroom)
                    a0 = acc[i] - lp["left"]
                    a1 = acc[i + 1] + lp["right"]
                    S = a1 - a0
                    loops.append(dict(span=[i, i + 1], joints=js, angle_rad=round(lp["th"], 3),
                                      angle_runtime_rad=round(lp["th_rt"], 3), od_mm=r["d_mm"],
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
                    if a0 > 1.0:
                        want.append((a0, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i], S)))
                        loop_ref[(round(a0, 4), want[-1][1])] = (loops[-1], 0)
                    else:
                        loops[-1]["anchor_a"] = "connector (no tie needed)"
                    if a1 < total - 1.0:
                        want.append((a1, "joint crossing, %s side (end of the %.0f mm free loop)" % (B[i + 1], S)))
                        loop_ref[(round(a1, 4), want[-1][1])] = (loops[-1], 1)
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
                    extra.append((a0 + k * (a1 - a0) / (n + 1), "support spacing <= 76.2 mm (lab rule)"))
            for a, why in sorted(want + extra):
                i = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
                t = (a - acc[i]) / max(seg[i], 1e-9)
                q = P[i] + (P[i + 1] - P[i]) * t
                link = B[i] if t < 0.5 or B[i] == B[i + 1] else B[i + 1]
                ax = (P[i + 1] - P[i]) / max(seg[i], 1e-9)
                items.append(dict(cable=c["id"], run=r["name"], p=q, axis=ax, link=link, why=why, d=r["d_mm"],
                                  ref=loop_ref.get((round(a, 4), why))))
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
                break
        else:
            merged.append(dict(link=it["link"], p=it["p"], pts=[it["p"]], axis=it["axis"], cables={it["cable"]},
                               whys={it["why"]}, ds=[it["d"]], refs=[it["ref"]]))
    for k, m in enumerate(merged):            # each loop end names the tie that holds it
        for ref in m["refs"]:
            if ref:
                lp_, side = ref
                lp_.setdefault("tie_ids", [None, None])[side] = "T%03d" % (k + 1)
    an = [a for a in anchors]
    out = []

    def fit_record(f, typ):
        return dict(type=typ, part=f["part"], center_mm=[round(float(x), 1) for x in f["center"]],
                    normal=[round(float(x), 3) for x in f["normal"]], from_cable_mm=round(f["dist"], 1))

    def find_mount(link, c, axis, reach, loop_end=False):
        """MB3A (BOM 34) first, then the smaller MB2APT (proposal, not in the BOM)"""
        for typ, base, h in (("MB3A", MOUNT_BASE, MOUNT_H), ("MB2APT", SMALL_BASE, SMALL_H)):
            f = mount_patch(s, link, c, axis, reach, base=base, height=h,
                            max_dist=DRESS_MAX_LOOP if loop_end else (DRESS_MAX if reach <= ANCHOR_REACH else FREE_MOUNT_REACH))
            if f:
                return f, typ
        return None, None

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
                f, typ = find_mount(m["link"], c, m["axis"], ANCHOR_REACH,
                                    loop_end=any(w_.startswith("joint crossing") for w_ in m["whys"]))
                if f:
                    part, fit = f["part"], fit_record(f, typ)
                    note = ("GAP: no tie anchor in the CAD here; stick-on tie mount %s on a flat %s patch of %s, %.0f mm from "
                            "the cable line (exact rays)" % (
                                "MB3A (BOM 34)" if typ == "MB3A" else "MB2APT 13 x 13 mm (not in the BOM, proposal)",
                                "19 x 19 mm" if typ == "MB3A" else "13 x 13 mm", part, f["dist"]))
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
    # points with no anchor yet (free air, or a mount spot with no flat patch): (a) tie to an anchored neighbour cable,
    # (b) a mount on a flat patch within 25 mm (not at a loop end: moving a loop tie changes the loop), (c) left open
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
    anchored = [t for t in out if t["kind"] == "existing printed feature" or (t.get("mount_fit") or {}).get("type")]
    for t in out:
        if t["note"] not in ("FREE AIR", "NO FLAT PATCH"):
            continue
        free = t["note"] == "FREE AIR"
        what = ("free air, no printed part within 15 mm on this link" if free else
                "no flat patch for a 19 x 19 mm (MB3A) or 13 x 13 mm (MB2APT) stick-on mount within 15 mm of %s" % t["part"])
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
        if best:
            t.update(kind="cable tie to a neighbour cable", tied_to=best[1], anchor_tie=best[2], mount_fit=None, part=None,
                     note="GAP: %s; tied to the neighbour cable %s (surface gap %.1f mm), which tie %s holds %.0f mm away" % (
                         what, best[1], max(best[0], 0.0), best[2], best[3]))
            continue
        if not t["loop_end"]:
            f, typ = find_mount(t["link"], c, np.array(t["axis"]), FREE_MOUNT_REACH)
            if f:
                t.update(kind="adhesive tie mount", part=f["part"], mount_fit=fit_record(f, typ),
                         note="GAP: %s; stick-on tie mount %s on a flat patch of %s %.0f mm away: dress the bundle over to it" % (
                             what, "MB3A (BOM 34)" if typ == "MB3A" else "MB2APT 13 x 13 mm (not in the BOM, proposal)",
                             f["part"], f["dist"]))
                continue
        near = None
        for inst in s.inst:
            if inst["link"] != t["link"] or not inst["printed"]:
                continue
            mw = _wmesh(s, inst)
            d = float(abs(trimesh.proximity.signed_distance(mw, [c])[0]))
            if near is None or d < near[0]:
                near = (d, inst["key"])
        t["open"] = True
        t["note"] = ("GAP: %s; no anchored neighbour cable within 4 mm%s: OPEN, needs a printed guide, a drilled tie hole or a "
                     "route change (nearest printed part %s, %.0f mm away), checked at the TEST_PLAN 1.4 fit" % (
                         what, "" if t["loop_end"] else " and no flat mount patch within 25 mm",
                         near[1] if near else "-", near[0] if near else 0.0))
    return out

PAR = {}


def main():
    global POSER
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", default=RC.OUT_JSON, help="cables3d.json to read and rewrite (default: the lab file)")
    a = ap.parse_args()
    t0 = time.time()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    PAR.update(RC.tree(s))
    POSER = RC.Poser(s)
    data = json.load(open(a.json))
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
                                     rule="both sides of every joint crossing, loop ties pushed out until the loop meets 3 x OD "
                                          "(NASA-STD-8739.4A Table 7-1) in the uniform bend and length storage models; first "
                                          "tie 25.4-50.8 mm from each connector (Table 9-2); support <= 76.2 mm apart (lab "
                                          "rule, not Table 9-1); merged within 8 mm; MB3A mounts on a flat 19 x 19 mm patch; "
                                          "free-air points tied to an anchored neighbour cable or moved to a mount within 25 mm",
                                     generated_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
    RC.write_json_atomic(data, a.json)
    print("retention items %d %s in %.1f s" % (len(data["retention"]), kinds, time.time() - t0))


if __name__ == "__main__":
    main()
