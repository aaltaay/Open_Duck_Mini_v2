#!/usr/bin/env python3
"""sit_cables.py: the cable routes on the joggled shins (D59). CAD check only.

  python3 altaay_lab/twin/sit/sit_cables.py [--write]
Starts from cables3d.json at sitlib.BASE_REV (so a re-run gives the same file) and:
  - moves every route point and tie that lies on a shin link, outside a shin sheet face, JOG mm away from the leg centre
    plane wherever the sheet moved (from R_MOVE of the knee axis down to the ankle), with a jog point where a route
    leaves the knee horn zone (the web of the joggle lies between); ties in the horn zone stay;
  - renames the parts the shin ties name (knee_to_ankle_* sheets on the shin links are now shin_* sheets, leg_spacer
    there is shin_spacer) and moves their tie holes and stick-on mount seats with them;
  - grows the service loops the new ranges made too small (grow_loops: a loop tie with no anchor slides along the
    cable until verify/c3_cables3d.py's own loop check passes);
  - takes the trunk-side neck loops round the neck stop block (NECK_LANE: the block covers the diagonal they took across
    trunk_top), moves the ties on those segments onto the new line and checks every trunk segment of every cable clear
    of the block (exact mesh, LANE_GAP);
  - re-checks every stick-on mount and drilled tie hole pair on a part this job changed or next to one (within 30 mm: a
    new part can cover a mount on an unchanged one), on the new STL (rays: the mount footprint flat within FLAT_TOL, room
    above; both tie holes in plastic) and moves a mount the trim or a new part took away along its cable to the nearest
    flat patch.
Then cables3d/route_cables.py --grid-only and cables3d/check_cables.py recompute every length, loop and rub on the new
CAD and the new joint ranges (robot.urdf), and write them into cables3d.json (run them after this script; the sit
job's commands are in SIT.md).
"""
import argparse
import copy
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402
sys.path.insert(0, os.path.join(L.LAB, "cables3d"))
import seats_ties as ST  # noqa: E402
sys.path.insert(0, os.path.join(L.LAB, "verify"))
import c3_cables3d as C3  # noqa: E402

CJ = os.path.join(L.LAB, "cables3d", "cables3d.json")
SHIN = {"knee_and_ankle_assembly_2": 90.65, "knee_and_ankle_assembly_4": 90.65 - 181.2}   # leg centre plane y
KNEE = np.array([-35.06, -78.72])
R_MOVE = 16.0 - 0.5              # the plate moved from R_HORN; a route point this far out is moved (the web is outside)
FACE_D = 21.5                    # |y - centre| at or beyond this: outside a sheet (stock outer faces at 22.3 and 22.55)
ZONE_X, ZONE_Z = (-58.0, -12.0), (-150.0, -60.0)
RENAME = {"knee_to_ankle_left_sheet": "shin_left_sheet", "knee_to_ankle_right_sheet": "shin_right_sheet", "leg_spacer": "shin_spacer"}


def world(S, link, p):
    return (S.T0[link] @ np.r_[np.asarray(p, float), 1.0])[:3]


def local(S, link, w):
    return (np.linalg.inv(S.T0[link]) @ np.r_[np.asarray(w, float), 1.0])[:3]


def moved(link, w):
    """the y shift of a world point on a shin link (0 if it stays)"""
    if link not in SHIN:
        return 0.0
    yc = SHIN[link]
    d = w[1] - yc
    r = float(np.hypot(w[0] - KNEE[0], w[2] - KNEE[1]))
    if abs(d) >= FACE_D and ZONE_X[0] <= w[0] <= ZONE_X[1] and ZONE_Z[0] <= w[2] <= ZONE_Z[1] and r >= R_MOVE:
        return float(np.sign(d) * L.JOG)
    return 0.0


def move_points(S, pts, log, cid):
    out = []
    prev_shift, prev_w = 0.0, None
    for q in pts:
        w = world(S, q["link"], q["p"])
        sh = moved(q["link"], w)
        if sh and not prev_shift and prev_w is not None and q["link"] in SHIN:
            # a jog: out to the moved plane at the last point that stayed, then on along the plate
            jw = prev_w.copy()
            jw[1] += sh
            out.append(dict(link=q["link"], p=[round(float(v), 3) for v in local(S, q["link"], jw)]))
        if sh:
            w2 = w.copy()
            w2[1] += sh
            q = dict(q, p=[round(float(v), 3) for v in local(S, q["link"], w2)])
            log["moved_points"][cid] = log["moved_points"].get(cid, 0) + 1
        out.append(q)
        prev_shift, prev_w = sh, w
    return out


def flat_patch(m, centre, normal, size, axis, others=()):
    """the cables3d test of a stick-on mount spot (seats_ties.py mount_patch, its constants): a 5 x 5 ray grid over the
    base (size x size) from 2 mm out along -normal hits the part within FLAT_TOL of the plane, on faces within FLAT_DEG
    of the normal, and nothing of the other parts within the mount height above it. Returns (ok, worst deviation, why)"""
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    u = np.asarray(axis, float) - np.dot(axis, n) * n
    if np.linalg.norm(u) < 0.2:
        u = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    g1 = np.linspace(-size / 2, size / 2, 5)
    pts = np.array([np.asarray(centre, float) + x * u + y * v for x in g1 for y in g1])
    loc, ri, ti = m.ray.intersects_location(pts + n * 2.0, np.tile(-n, (len(pts), 1)), multiple_hits=False)
    if len(ri) < len(pts):
        return False, np.inf, "%d of %d rays miss the part" % (len(pts) - len(ri), len(pts))
    dist = np.linalg.norm(loc - (pts + n * 2.0)[ri], axis=1)
    dev = float(np.abs(dist - 2.0).max())
    if dev > ST.FLAT_TOL or np.any(m.face_normals[ti] @ n < np.cos(np.radians(ST.FLAT_DEG))):
        return False, dev, "not flat (%.2f mm)" % dev
    foot = loc + n * 0.05
    for mm in others:
        l2, r2, _ = mm.ray.intersects_location(foot, np.tile(n, (len(foot), 1)), multiple_hits=False)
        if len(r2) and np.any(np.linalg.norm(l2 - foot[r2], axis=1) < ST.MOUNT_H + 0.3):
            return False, dev, "no room above (another part within %.1f mm)" % (ST.MOUNT_H + 0.3)
    return True, dev, "flat"


MOVABLE = ("cable tie", "bundle tie, test fit")   # ties round the bundle, no anchor: they can slide along the cable
D59_JOINTS = ("knee", "ankle", "hip_roll", "hip_pitch", "neck_pitch", "head_pitch")
GROW_STEP, LOOP_MARGIN = 1.0, 1.05
# round 2 (2026-11-10): the neck stop block covers x -56 to -18, |y| 15 to 29 on trunk_top from z 85 (its foot and
# pillars). The trunk-side neck loops crossed that ground diagonally at z 89 and dropped forward past the right pillar's
# front corner. Each pair of consecutive trunk route points (matched within 0.2 mm) gets a point between them: behind
# the foot and inside the lane (|y| under 15), or forward of the pillar's front face before the drop.
NECK_LANE = (((-60.0, 28.0, 89.0), (-36.84, 5.42, 89.0), (-58.5, 12.0, 89.0)),     # D1
             ((-60.0, 20.0, 89.0), (-34.12, -0.06, 89.0), (-58.5, 11.0, 89.0)),    # SD1 b
             ((-20.0, -11.0, 89.0), (-12.0, -19.0, 81.0), (-15.0, -11.5, 88.0)))   # P13, D1, D13, SD1 b
NECK_LANE_N = 12                 # the pairs these must find (points and runs lists): P13 2, D1 4, D13 2, SD1 4
LANE_GAP = 0.3                   # every trunk segment's tube this far or more from the block (mm)


def say(msg):
    """progress on stderr, flushed (the json log comes at the end)"""
    import sys
    import time as _t
    print("[%s] %s" % (_t.strftime("%H:%M:%S"), msg), file=sys.stderr, flush=True)


def grow_loops(data, log):
    """the service loops the D59 ranges made too small: slide a loop tie that has no anchor (MOVABLE) away from the
    crossing, 1 mm at a time inside the loop's room, until C3's own recomputation (verify/c3_cables3d.py loop_check,
    the URDF ranges now) gives bend R and length storage R of 3 x OD or more (5 % over). Every loop of every cable that
    names the moved tie gets its new position (the tie's point projected onto that route)."""
    kin = C3.Kin()
    R = {t["id"]: t for t in data["retention"]}
    runs = [(c, r) for c in data["cables"] for r in (c.get("runs") or [])]

    def route(r):
        P = np.array([(kin.T(p["link"], {}) @ np.r_[p["p"], 1.0])[:3] for p in r["points"]])
        return P, np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]

    def along(P, acc, a):
        k = int(np.clip(np.searchsorted(acc, a) - 1, 0, len(P) - 2))
        t = (a - acc[k]) / max(float(np.linalg.norm(P[k + 1] - P[k])), 1e-9)
        return P[k] + (P[k + 1] - P[k]) * t, k

    def ok(r, lp):
        x = C3.loop_check(kin, r, lp, None)
        need = 3.0 * lp["od_mm"] * LOOP_MARGIN
        return min(x["bend"], x["storage"]) >= need, x
    for c, r in runs:
        for lp in r.get("service_loops", []):
            if not any(k in j for j in lp["joints"] for k in D59_JOINTS) or not lp.get("ties_at_mm"):
                continue
            good, x = ok(r, lp)
            if good:
                continue
            say("grow loop %s %s %s" % (c["id"], r["name"], "+".join(lp["joints"])))
            P, acc = route(r)
            spans = lp.get("spans") or [lp["span"]]
            i0, i9 = spans[0][0], spans[-1][1]
            room = lp.get("room_mm") or [0.0, 0.0]
            ids = lp.get("tie_ids") or []
            moved = None
            for side in (1, 0):                    # the far link side first, then the near one
                if side >= len(ids) or ids[side] not in R or R[ids[side]]["kind"] not in MOVABLE:
                    continue
                t = R[ids[side]]
                lim = acc[i9] + room[1] if side == 1 else acc[i0] - room[0]
                a = a_orig = lp["ties_at_mm"][side]
                while not good:
                    a2 = a + GROW_STEP if side == 1 else a - GROW_STEP
                    if (side == 1 and a2 > min(lim, acc[-1])) or (side == 0 and a2 < max(lim, 0.0)):
                        break
                    w, k = along(P, acc, a2)
                    if r["points"][k]["link"] != t["link"] and r["points"][min(k + 1, len(P) - 1)]["link"] != t["link"]:
                        break                      # the tie stays on its link
                    a = a2
                    lp["ties_at_mm"][side] = round(float(a), 1)
                    good, x = ok(r, lp)
                if a != a_orig:
                    moved = (t, a, side)
                if good:
                    break
            key = "%s %s %s" % (c["id"], r["name"], "+".join(lp["joints"]))
            if moved:
                t, a, side = moved
                w, _ = along(P, acc, a)
                old = np.asarray(t["center_mm"], float)
                t["center_mm"] = [round(float(v), 2) for v in w]
                t["p"] = [round(float(v), 3) for v in (np.linalg.inv(kin.T(t["link"], {})) @ np.r_[w, 1.0])[:3]]
                t["note"] = (t.get("note") or "") + "; D59: slid %.0f mm along the cable to grow the %s loop for the new range" % (
                    np.linalg.norm(w - old), "+".join(lp["joints"]))
                lp["free_mm"] = round(float(lp["ties_at_mm"][1] - lp["ties_at_mm"][0]), 1)
                # the same tie on the other cables it holds: its new point projected onto their routes
                for c2, r2 in runs:
                    for lp2 in r2.get("service_loops", []):
                        if lp2 is lp or t["id"] not in (lp2.get("tie_ids") or []):
                            continue
                        P2, acc2 = route(r2)
                        k2 = int(np.argmin(np.linalg.norm(P2 - w, axis=1)))
                        j = lp2["tie_ids"].index(t["id"])
                        lp2["ties_at_mm"][j] = round(float(acc2[k2]), 1)
                        lp2["free_mm"] = round(float(lp2["ties_at_mm"][1] - lp2["ties_at_mm"][0]), 1)
            meets = min(x["bend"], x["storage"]) >= 3.0 * lp["od_mm"]
            log["loops"][key] = ("%s%s: free %.0f mm, bend R %.1f, storage R %.1f, needs %.1f mm" % (
                "grown, " if moved else "", "meets 3 x OD" if meets else "under 3 x OD (its ties are anchored or out of room): test fit",
                x["free"], x["bend"], x["storage"], 3.0 * lp["od_mm"]))


def _seg_dist(p, a, b):
    ab = b - a
    t = float(np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-12), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab))), a + t * ab, ab


def neck_lane(S, data, log):
    """the trunk-side neck loops round the neck stop block (NECK_LANE), the ties on the moved segments onto the new line,
    then every trunk segment of every cable checked clear of the block (exact mesh); raises when a pair is missing or
    a segment is too close"""
    import trimesh
    tr = "trunk_assembly"
    hit, moved = 0, {}                                  # cable id -> [(old a, old b, new point)] in world mm
    for c in data["cables"]:
        for nm, pts in [("points", c["points"])] + [(r.get("name", ""), r["points"]) for r in c.get("runs") or []]:
            i = 0
            while i < len(pts) - 1:
                a, b = pts[i], pts[i + 1]
                if a["link"] == tr and b["link"] == tr:
                    for pa, pb, w in NECK_LANE:
                        if np.abs(np.subtract(a["p"], pa)).max() < 0.2 and np.abs(np.subtract(b["p"], pb)).max() < 0.2:
                            pts.insert(i + 1, {"link": tr, "p": [round(float(x), 3) for x in local(S, tr, w)]})
                            hit += 1
                            moved.setdefault(c["id"], []).append((world(S, tr, a["p"]), world(S, tr, b["p"]), np.asarray(w, float)))
                            log["neck_lane"]["%s:%s" % (c["id"], nm)] = log["neck_lane"].get("%s:%s" % (c["id"], nm), 0) + 1
                            i += 1
                            break
                i += 1
    if hit != NECK_LANE_N:
        raise SystemExit("neck lane: %d segment pairs found, %d expected (the base routes changed?)" % (hit, NECK_LANE_N))
    for t in data["retention"]:                         # a tie on a moved segment goes to the nearest point of the new line
        if t.get("link") != tr or not t.get("center_mm"):
            continue
        cen = np.asarray(t["center_mm"], float)
        for cid in t.get("cables") or []:
            best = None
            for a, b, w in moved.get(cid, []):
                d0, _, _ = _seg_dist(cen, a, b)
                if d0 > 3.0:
                    continue
                for s0, s1 in ((a, w), (w, b)):
                    d1, q, ab = _seg_dist(cen, s0, s1)
                    if best is None or d1 < best[0]:
                        best = (d1, q, ab / np.linalg.norm(ab))
            if best is not None:
                dq = best[1] - cen
                t["center_mm"] = [round(float(x), 2) for x in best[1]]
                t["p"] = [round(float(x), 3) for x in local(S, tr, best[1])]
                t["axis"] = [round(float(x), 4) for x in best[2]]
                if t.get("mount_fit"):
                    t["mount_fit"]["center_mm"] = [round(float(x), 2) for x in np.asarray(t["mount_fit"]["center_mm"], float) + dq]
                log["neck_lane"][t["id"]] = "tie moved %.1f mm onto the new line of %s" % (float(np.linalg.norm(dq)), cid)
                break
    block = trimesh.util.concatenate([S.world_mesh(i) for i in S.inst if i["key"] == "neck_stop"])
    pq = trimesh.proximity.ProximityQuery(block)
    lo, hi = block.bounds[0] - 15, block.bounds[1] + 15
    worst = (99.0, None)
    for c in data["cables"]:
        for r in c.get("runs") or [{"name": "", "points": c["points"], "d_mm": c.get("d_mm")}]:
            pts, rad = r["points"], float(r.get("d_mm") or c.get("d_mm") or 0) / 2
            for a, b in zip(pts[:-1], pts[1:]):
                if a["link"] != tr or b["link"] != tr:
                    continue
                A, B = world(S, tr, a["p"]), world(S, tr, b["p"])
                if np.any(np.maximum(A, B) < lo) or np.any(np.minimum(A, B) > hi):
                    continue
                P = A + np.linspace(0, 1, max(2, int(np.ceil(np.linalg.norm(B - A) / 0.25)) + 1))[:, None] * (B - A)
                g = float(-pq.signed_distance(P).max()) - rad
                if g < worst[0]:
                    worst = (g, "%s:%s" % (c["id"], r.get("name", "")))
                if g < LANE_GAP:
                    raise SystemExit("neck lane: %s run %s passes %.2f mm from the neck stop block (need %.1f)" % (
                        c["id"], r.get("name", ""), g, LANE_GAP))
    log["neck_lane"]["worst_gap_mm"] = [round(worst[0], 2), worst[1]]
    say("neck lane: %d pairs, worst trunk segment %.2f mm from the block (%s)" % (hit, worst[0], worst[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = L.scene(fresh=True)                       # the new CAD and URDF (the shin links carry the shin sheets now)
    data = json.loads(L.git_blob("altaay_lab/cables3d/cables3d.json").decode())
    log = dict(moved_points={}, ties={}, mounts={}, loops={}, neck_lane={})
    for c in data["cables"]:
        c["points"] = move_points(S, c["points"], log, c["id"])
        for r in c.get("runs") or []:
            r["points"] = move_points(S, r["points"], log, c["id"] + ":" + r.get("name", ""))
    neck_lane(S, data, log)
    parts_now = {(i["link"], i["key"]): S.world_mesh(i) for i in S.inst}
    changed = {"knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "shin_left_sheet", "shin_right_sheet", "shin_spacer",
               "left_cache", "right_cache", "foot_top", "foot_side", "left_roll_to_pitch", "right_roll_to_pitch",
               "head_pitch_to_yaw", "neck_stop", "neck_pad", "head_pad", "roll_pad_left", "roll_pad_right"}   # the neck sheets are stock again
    placed = {}                                     # every stick-on mount as seats_ties keeps them (one mount per spot)
    for t in data["retention"]:
        mf = t.get("mount_fit")
        if mf:
            n = np.asarray(mf["normal"], float)
            ax = np.asarray(t.get("axis") or [0, 0, 1.0], float)
            u = ax - np.dot(ax, n) * n
            u = u / np.linalg.norm(u) if np.linalg.norm(u) > 0.2 else (np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0]))
            u /= np.linalg.norm(u)
            placed[t["id"]] = (np.asarray(mf["center_mm"], float), n, u, np.cross(n, u), (19.0 if mf.get("type") == "MB3A" else 12.7) / 2)
    for t in data["retention"]:
        link = t.get("link")
        if link in SHIN:
            if t.get("part") in RENAME:
                t["part"] = RENAME[t["part"]]
            w = np.asarray(t["center_mm"], float)
            sh = moved(link, w)
            if sh:
                t["center_mm"] = [round(float(x), 2) for x in (w + [0, sh, 0])]
                t["p"] = [round(float(x), 3) for x in local(S, link, w + [0, sh, 0])]
                if t.get("mount_fit"):
                    mf = t["mount_fit"]
                    mf["center_mm"] = [round(float(x), 2) for x in (np.asarray(mf["center_mm"]) + [0, sh, 0])]
                    if t["id"] in placed:
                        placed[t["id"]] = (np.asarray(mf["center_mm"], float),) + placed[t["id"]][1:]
                    mf["part"] = RENAME.get(mf.get("part"), mf.get("part"))
                if t.get("tie_holes"):
                    th = t["tie_holes"]
                    th["part"] = RENAME.get(th["part"], th["part"])
                    th["holes_world"] = [[round(float(x), 2) for x in (np.asarray(h) + [0, sh, 0])] for h in th["holes_world"]]
                t["note"] = (t.get("note") or "") + "; moved %.0f mm with the shin joggle (D59, twin/sit/sit_cables.py)" % abs(sh)
                log["ties"][t["id"]] = "moved %+.0f mm in y" % sh
            if t.get("mount_fit"):
                t["mount_fit"]["part"] = RENAME.get(t["mount_fit"].get("part"), t["mount_fit"].get("part"))
            if t.get("tie_holes"):
                t["tie_holes"]["part"] = RENAME.get(t["tie_holes"]["part"], t["tie_holes"]["part"])
        # re-check stick-on mounts on changed parts, on the new mesh
        mf = t.get("mount_fit")
        near_new = mf and any(k in changed and not (np.any(v.bounds[0] - 30 > mf["center_mm"]) or np.any(v.bounds[1] + 30 < mf["center_mm"]))
                              for (ln, k), v in parts_now.items())     # a new or changed part can cover a mount on a stock one
        if mf and (mf.get("part") in changed or near_new):
            m = parts_now.get((link, mf["part"]))
            size = 19.0 if mf.get("type") == "MB3A" else 12.7
            if m is None:
                raise SystemExit("%s: part %s not on link %s" % (t["id"], mf["part"], link))
            # a mount on a stock part is checked against the changed and new parts only (did this job cover it?); a mount
            # on a changed part against every part near it, as before
            others = [v for (ln, k), v in parts_now.items() if (ln, k) != (link, mf["part"]) and
                      (mf.get("part") in changed or k in changed) and
                      not (np.any(v.bounds[0] - 30 > mf["center_mm"]) or np.any(v.bounds[1] + 30 < mf["center_mm"]))]
            ax = t.get("axis") or [0, 0, 1.0]
            ok, dev, why = flat_patch(m, mf["center_mm"], mf["normal"], size, ax, others)
            if ok:
                log["mounts"][t["id"]] = "flat (dev %.2f mm)" % dev
                continue
            # place it again the way cables3d placed it (seats_ties.py mount_patch: every face direction of the link's
            # printed parts within REACH of the tie, in-plane shifts, dressed at most DRESS_MAX from the cable line,
            # one mount per spot, room above), on the new CAD
            say("mount %s on %s: placing again" % (t["id"], mf.get("part")))
            ST.PLACED_MOUNTS[:] = [pm for tid, pm in placed.items() if tid != t["id"]]
            ST.MESH_CACHE.clear()
            got = None
            for typ, sz in (("MB3A", 19.0), ("ABM1M", 12.7)):          # the big mount first, then the small one (BOM 34b)
                if typ == "MB3A" and size < 19.0:
                    continue
                got = ST.mount_patch(S, link, np.asarray(t["center_mm"], float), np.asarray(ax, float), ST.REACH,
                                     base=sz, max_dist=ST.DRESS_MAX_LOOP if t.get("loop_end") else ST.DRESS_MAX)
                if got is not None:
                    if typ != mf.get("type"):
                        mf["type"] = typ
                        why += "; %s in place of %s" % (typ, "MB3A")
                    break
            if got is None:
                log["mounts"][t["id"]] = "%s at the old spot; no flat patch in reach on the new CAD: bundle tie at the test fit (D25)" % why
                t["kind"] = "bundle tie, test fit"
                t["note"] = (t.get("note") or "") + "; D59: %s on the changed %s and no flat patch in reach: bundle tie, test fit (D25)" % (why, mf["part"])
                t.pop("mount_fit")
                placed.pop(t["id"], None)
            else:
                old_c = np.asarray(mf["center_mm"], float)
                mf.update(part=got["part"], center_mm=[round(float(x), 2) for x in got["center"]],
                          normal=[round(float(x), 3) for x in got["normal"]], from_cable_mm=round(got["dist"], 1))
                t["part"] = got["part"]
                placed[t["id"]] = (np.asarray(got["center"], float), got["normal"], got["u"], got["v"], got["half"])
                t["note"] = (t.get("note") or "") + "; D59: %s at the old spot on the changed CAD; the mount placed again on %s, %.0f mm from the old spot (cables3d seats_ties.py mount_patch)" % (
                    why, got["part"], np.linalg.norm(np.asarray(got["center"]) - old_c))
                log["mounts"][t["id"]] = "%s; placed again on %s, %.1f mm away" % (why, got["part"], np.linalg.norm(np.asarray(got["center"]) - old_c))
    say("loops")
    grow_loops(data, log)
    say("loops done")
    data["meta"]["sit_d59"] = ("twin/sit/sit_cables.py: the shin routes and ties moved %.0f mm with the joggle; mounts on the "
                               "changed parts re-checked on the new STLs; lengths, loops and rubs recomputed by check_cables.py" % L.JOG)
    print(json.dumps(log, indent=1))
    if a.write:
        open(CJ, "w").write(json.dumps(data, indent=1) + "\n")
        L.dump(log, os.path.join(HERE, "sit_cables.json"))


if __name__ == "__main__":
    main()
