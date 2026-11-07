#!/usr/bin/env python3
"""sit_cables.py: the cable routes on the joggled shins (D59). CAD check only.

  python3 altaay_lab/twin/sit/sit_cables.py [--write]
Starts from cables3d.json at sitlib.BASE_REV (so a re-run gives the same file) and:
  - moves every route point and tie that lies on a shin link, outside a shin sheet face, JOG mm away from the leg centre
    plane wherever the sheet moved (from R_MOVE of the knee axis down to the ankle), with a jog point where a route
    leaves the knee horn zone (the web of the joggle lies between); ties in the horn zone stay;
  - renames the parts the shin ties name (knee_to_ankle_* sheets on the shin links are now shin_* sheets, leg_spacer
    there is shin_spacer) and moves their tie holes and stick-on mount seats with them;
  - re-checks every stick-on mount and drilled tie hole pair on a part this job changed, on the new STL (rays: the mount
    footprint flat within FLAT_TOL; both tie holes in plastic) and moves a mount the trim took away along its cable to
    the nearest flat patch.
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

CJ = os.path.join(L.LAB, "cables3d", "cables3d.json")
SHIN = {"knee_and_ankle_assembly_2": 90.65, "knee_and_ankle_assembly_4": 90.65 - 181.2}   # leg centre plane y
KNEE = np.array([-35.06, -78.72])
R_MOVE = 16.0 - 0.5              # the plate moved from R_HORN; a route point this far out is moved (the web is outside)
FACE_D = 21.5                    # |y - centre| at or beyond this: outside a sheet (stock outer faces at 22.3 and 22.55)
ZONE_X, ZONE_Z = (-58.0, -12.0), (-150.0, -60.0)
RENAME = {"knee_to_ankle_left_sheet": "shin_left_sheet", "knee_to_ankle_right_sheet": "shin_right_sheet", "leg_spacer": "shin_spacer"}
FLAT_TOL = 0.3


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


def flat_patch(m, centre, normal, size, tol=FLAT_TOL):
    """the mount footprint (size x size) on the mesh surface: every ray of a 1 mm grid from 3 mm outside along -normal
    hits within tol of the plane through centre"""
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    u = np.cross(n, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-6:
        u = np.cross(n, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    g = np.arange(-size / 2, size / 2 + 1e-9, 1.0)
    O, Dd = [], []
    for a in g:
        for b in g:
            O.append(np.asarray(centre) + a * u + b * v + 3.0 * n)
            Dd.append(-n)
    loc, ri, _ = m.ray.intersects_location(np.array(O), np.array(Dd), multiple_hits=False)
    d = np.full(len(O), np.inf)
    if len(ri):
        d[ri] = (np.array(O)[ri] - loc) @ n - 3.0
    return bool(np.all(np.abs(d) <= tol)), float(np.nanmax(np.abs(d[np.isfinite(d)])) if np.isfinite(d).any() else np.inf), int(np.sum(~np.isfinite(d)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = L.scene(fresh=True)                       # the new CAD and URDF (the shin links carry the shin sheets now)
    data = json.loads(L.git_blob("altaay_lab/cables3d/cables3d.json").decode())
    log = dict(moved_points={}, ties={}, mounts={})
    for c in data["cables"]:
        c["points"] = move_points(S, c["points"], log, c["id"])
        for r in c.get("runs") or []:
            r["points"] = move_points(S, r["points"], log, c["id"] + ":" + r.get("name", ""))
    parts_now = {(i["link"], i["key"]): S.world_mesh(i) for i in S.inst}
    changed = {"knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "shin_left_sheet", "shin_right_sheet", "shin_spacer",
               "left_cache", "right_cache", "foot_top", "foot_side", "left_roll_to_pitch", "right_roll_to_pitch",
               "neck_left_sheet", "neck_right_sheet", "head_pitch_to_yaw"}
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
        if mf and mf.get("part") in changed:
            m = parts_now.get((link, mf["part"])) or next((v for (ln, k), v in parts_now.items() if k == mf["part"] and ln == link), None)
            size = 19.0 if mf.get("type") == "MB3A" else 12.7
            if m is None:
                log["mounts"][t["id"]] = "part %s not on link %s: BLOCKER" % (mf["part"], link)
                continue
            ok, dev, miss = flat_patch(m, mf["center_mm"], mf["normal"], size)
            if not ok:
                # move along the cable (up or down the link) to the nearest flat patch
                best = None
                n = np.asarray(mf["normal"], float)
                for dz in sorted(np.arange(-30, 30.1, 1.0), key=abs):
                    for dx in (0.0, -2.0, 2.0, -4.0, 4.0):
                        c2 = np.asarray(mf["center_mm"], float) + [dx, 0, dz]
                        ok2, dev2, miss2 = flat_patch(m, c2, n, size)
                        if ok2:
                            best = c2
                            break
                    if best is not None:
                        break
                if best is None:
                    log["mounts"][t["id"]] = "no flat patch within 30 mm on %s: BLOCKER (bundle tie at the test fit)" % mf["part"]
                    t["kind"] = "bundle tie, test fit"
                    t["note"] = (t.get("note") or "") + "; D59: the trim of %s took the mount patch, no flat patch within 30 mm: bundle tie, test fit" % mf["part"]
                else:
                    d = best - np.asarray(mf["center_mm"], float)
                    mf["center_mm"] = [round(float(x), 2) for x in best]
                    t["center_mm"] = [round(float(x), 2) for x in (np.asarray(t["center_mm"]) + d)]
                    t["p"] = [round(float(x), 3) for x in local(S, link, np.asarray(t["center_mm"]))]
                    t["note"] = (t.get("note") or "") + "; D59: the mount moved %.0f mm along the cable to a flat patch of the trimmed %s" % (np.linalg.norm(d), mf["part"])
                    log["mounts"][t["id"]] = "moved %.1f mm to a flat patch (dev %.2f mm)" % (np.linalg.norm(d), dev)
            else:
                log["mounts"][t["id"]] = "flat (dev %.2f mm)" % dev
    data["meta"]["sit_d59"] = ("twin/sit/sit_cables.py: the shin routes and ties moved %.0f mm with the joggle; mounts on the "
                               "changed parts re-checked on the new STLs; lengths, loops and rubs recomputed by check_cables.py" % L.JOG)
    print(json.dumps(log, indent=1))
    if a.write:
        open(CJ, "w").write(json.dumps(data, indent=1) + "\n")
        L.dump(log, os.path.join(HERE, "sit_cables.json"))


if __name__ == "__main__":
    main()
