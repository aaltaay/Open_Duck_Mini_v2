#!/usr/bin/env python3
"""sit_balance.py: the balance gate of the A1b sit (D59) at the sim's settled torque-off pose. sim pass only (the
settled poses and the push sims) and calc only (the margins, tip angles and static tip forces from them).

  python3 altaay_lab/twin/sit/sit_balance.py --out <scratch>/model [--write]
Writes altaay_lab/twin/sit/sit_balance.json; exits non-zero when the gate fails.

Each case: the repo sim model (sit_model.py) sits down the scripted path with torque on (sit_sim.enter) and rests 10 s
with the torque off on the dock pads (sit_sim.hold, no push). At the end:
  support    the floor contacts of the soles, the seat and the belly bumper (MuJoCo contacts with the floor); the
             polygon is their convex hull; the CoM is the whole robot's (MuJoCo subtree CoM of the root)
  margin     the distance from the CoM's floor projection to the nearest polygon edge (mm) and which contacts make it
  tip angle  per direction (forward, back, left, right in the trunk's heading): the rotation about the support edge
             that direction that brings the CoM over it, atan(d / h), h the CoM height above the floor
  push       the smallest horizontal force at head height (the head's CoM) that tips it, 8 directions: about each
             polygon edge F H (u . n) >= W d (W the weight, H the head CoM height, n the edge's outward normal);
             with friction mu it slides first when mu W is lower (reported, a slide is not a tip)
  sim push   (nominal case only) a force at the head's CoM ramped up at 2 N/s in each of the 8 directions until the
             trunk turns 10 deg (tips) or the robot slides 20 mm; the force then (sim pass only)
Cases (the worst case of every number is the gate): nominal (mu 0.8); zero errors of +1 and -1 deg on every joint and
+1/-1 deg mirrored left and right; the head and the trunk mass +5 % and -5 %; floor friction at the low end (mu 0.4, the
mat of the push tests); off the dock (no pogo pins under the feet; the others sit on the dock pads, as the push tests).
Gate: CoM inside the polygon by MARGIN_MIN_MM and every tip angle at least TIP_MIN_DEG in every
case.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

MARGIN_MIN_MM = 10.0      # >= 5 x the CoM shift of a 1 deg tilt at the sit CoM height (about 1.7 mm per deg)
TIP_MIN_DEG = 8.0         # a 1 deg zero error, the 0.7 to 2.8 deg pitch scatter of the push tests and 4 deg to spare
G = 9.81
CASES = [("nominal", {}), ("zero +1 deg", dict(err=+1.0)), ("zero -1 deg", dict(err=-1.0)),
         ("zero +1 L / -1 R", dict(err=+1.0, mirror=True)), ("zero -1 L / +1 R", dict(err=-1.0, mirror=True)),
         ("head mass +5 %", dict(mass={"head_assembly": 1.05})), ("head mass -5 %", dict(mass={"head_assembly": 0.95})),
         ("trunk mass +5 %", dict(mass={"trunk_assembly": 1.05})), ("trunk mass -5 %", dict(mass={"trunk_assembly": 0.95})),
         ("friction mu 0.4", dict(mu=0.4)), ("off the dock (no pins)", dict(pins=False))]
DIRS8 = [0, 45, 90, 135, 180, 225, 270, 315]


def hull(P):
    """convex hull of 2D points, counter-clockwise (monotone chain); indices into P"""
    idx = sorted(range(len(P)), key=lambda i: (P[i][0], P[i][1]))

    def cross(o, a, b):
        return (P[a][0] - P[o][0]) * (P[b][1] - P[o][1]) - (P[a][1] - P[o][1]) * (P[b][0] - P[o][0])
    lo, up = [], []
    for i in idx:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], i) <= 0:
            lo.pop()
        lo.append(i)
    for i in reversed(idx):
        while len(up) >= 2 and cross(up[-2], up[-1], i) <= 0:
            up.pop()
        up.append(i)
    return lo[:-1] + up[:-1]


def settle_case(out, opt, T=10.0):
    import mujoco as m
    import sit_sim as SS
    SS.OUT[0] = out
    md = SS.model(out, opt.get("mu", 0.8))
    saved = (md.body_mass.copy(), md.body_inertia.copy(), md.actuator_ctrlrange.copy())
    for bn, f in opt.get("mass", {}).items():
        b = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, bn)
        md.body_mass[b] *= f
        md.body_inertia[b] *= f
    off = None
    if "err" in opt:
        off = np.zeros(md.nu)
        for i in range(md.nu):
            nm = md.actuator(i).name
            s = -1.0 if (opt.get("mirror") and nm.startswith("right")) else 1.0
            off[i] = np.radians(opt["err"] * s)
        md.actuator_ctrlrange[:] = saved[2] + off[:, None]
    try:
        dd, SF, pins, _, _ = SS.enter(md, off=off, pins_on=opt.get("pins", True))
        r = SS.hold(md, dd, SF, pins, F=0.0, dirs=[], T=T, t_first=T - 3.0, pins_on=opt.get("pins", True))
        res = measure(md, dd)
        res.update(pads=r["pads_final"], fell=r["fell"])
        if opt.get("push_sim"):
            res["sim_push_N"] = sim_push(md, dd, SF, pins, opt.get("pins", True))
    finally:
        md.body_mass[:], md.body_inertia[:], md.actuator_ctrlrange[:] = saved
    return res


def measure(md, dd):
    import mujoco as m
    floor = m.mj_name2id(md, m.mjtObj.mjOBJ_GEOM, "floor")
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    hd = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")
    pts, who = [], []
    for i in range(dd.ncon):
        c = dd.contact[i]
        if floor in (c.geom1, c.geom2) and c.dist < 1e-3:
            g = c.geom2 if c.geom1 == floor else c.geom1
            nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or ""
            lab = "left sole" if nm.startswith("left_foot") else "right sole" if nm.startswith("right_foot") else \
                "seat" if nm.startswith("sit_seat") else "bumper" if nm.startswith("sit_bumper") else nm
            pts.append(c.pos[:2].copy())
            who.append(lab)
    com = dd.subtree_com[tr].copy()
    W = float(sum(md.body_mass)) * G
    R = dd.xmat[tr].reshape(3, 3)
    fwd = R[:2, 0] / np.linalg.norm(R[:2, 0])
    left = np.array([-fwd[1], fwd[0]])
    P = np.array(pts)
    H = hull(P)
    edges = []
    inside = True
    for k in range(len(H)):
        a, b = P[H[k]], P[H[(k + 1) % len(H)]]
        e = b - a
        n = np.array([e[1], -e[0]]) / np.linalg.norm(e)          # outward for a counter-clockwise hull
        d = float((a - com[:2]) @ n)                              # CoM to the edge along the outward normal
        inside &= d > 0
        edges.append(dict(n=n, d=d, who="%s - %s" % (who[H[k]], who[(H[(k + 1) % len(H)])])))
    near = min(edges, key=lambda e: e["d"])
    h_com = float(com[2])
    h_head = float(dd.xipos[hd][2])

    def reach(u):
        """the CoM's distance to the polygon boundary along u (the edge it would tip over)"""
        best = None
        for e in edges:
            un = float(u @ e["n"])
            if un > 1e-9:
                s = e["d"] / un
                best = s if best is None or s < best[0] else best
        return best
    tips = {}
    for nm_, u in (("forward", fwd), ("back", -fwd), ("left", left), ("right", -left)):
        best = None
        for e in edges:                                        # the edge it rotates about: the smallest angle
            un = float(u @ e["n"])
            if un > 0.5:
                ang = float(np.degrees(np.arctan2(e["d"], h_com)))
                best = (ang, e["who"]) if best is None or ang < best[0] else best
        tips[nm_] = dict(deg=round(best[0], 1), edge=best[1]) if best else None
    push = {}
    for a in DIRS8:
        u = np.cos(np.radians(a)) * fwd + np.sin(np.radians(a)) * left
        F = min((W * e["d"] / (h_head * float(u @ e["n"])) for e in edges if float(u @ e["n"]) > 1e-9), default=float("inf"))
        push[str(a)] = round(F, 2)
    return dict(contacts=sorted(set(who)), n_contacts=len(pts), com_mm=np.round(com * 1000, 1).tolist(), com_h_mm=round(h_com * 1000, 1),
                head_h_mm=round(h_head * 1000, 1), weight_N=round(W, 2), inside=bool(inside), margin_mm=round(near["d"] * 1000, 1),
                nearest_edge=near["who"], tip_deg=tips, push_tip_N=push,
                trunk_pitch_deg=round(float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))), 2),
                polygon_mm=[np.round(P[i] * 1000, 1).tolist() for i in H])


def sim_push(md, dd0, SF, pins, pins_on=True, rate=2.0, Fmax=40.0):
    """a horizontal force at the head CoM ramped at rate N/s from the settled state, 8 directions (sim pass only)"""
    import mujoco as m
    import sit_sim as SS
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    hd = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")
    R0 = dd0.xmat[tr].reshape(3, 3).copy()
    fwd = R0[:2, 0] / np.linalg.norm(R0[:2, 0])
    left = np.array([-fwd[1], fwd[0]])
    out = {}
    for a in DIRS8:
        dd = m.MjData(md)
        dd.qpos[:], dd.qvel[:], dd.act[:] = dd0.qpos, dd0.qvel, dd0.act
        dd.ctrl[:] = dd0.ctrl
        m.mj_forward(md, dd)
        p0 = dd.xpos[tr].copy()
        u = np.cos(np.radians(a)) * fwd + np.sin(np.radians(a)) * left
        res = None
        for k in range(int(Fmax / rate / md.opt.timestep)):
            F = rate * k * md.opt.timestep
            dd.xfrc_applied[:] = 0
            fv = np.array([u[0] * F, u[1] * F, 0.0])
            SS.pin_eval(md, dd, SF, pins, apply=True, pins_on=pins_on)     # zeroes qfrc_applied, adds the dock pins
            m.mj_applyFT(md, dd, fv, np.zeros(3), dd.xipos[hd].copy(), hd, dd.qfrc_applied)
            m.mj_step(md, dd)
            R = dd.xmat[tr].reshape(3, 3)
            turn = float(np.degrees(np.arccos(np.clip((np.trace(R0.T @ R) - 1) / 2, -1, 1))))
            slide = float(np.linalg.norm(dd.xpos[tr][:2] - p0[:2]))
            if turn > 10.0:
                res = dict(N=round(F, 2), how="tips")
                break
            if slide > 0.020 and turn < 5.0:
                res = dict(N=round(F, 2), how="slides")
                break
        out[str(a)] = res or dict(N=None, how="holds to %.0f N" % Fmax)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="the sit_sim.py --out folder (the model in <out>/sit)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    import sit_sim as SS
    R = {}
    for name, opt in CASES:
        o = dict(opt)
        if name == "nominal":
            o["push_sim"] = True
        R[name] = settle_case(a.out, o)
        r = R[name]
        print("%-18s margin %5.1f mm (%s) tip %s push min %.1f N" % (name, r["margin_mm"], r["nearest_edge"],
              {k: v["deg"] if v else None for k, v in r["tip_deg"].items()}, min(r["push_tip_N"].values())), flush=True)
    worst = dict(margin_mm=min(r["margin_mm"] for r in R.values()),
                 margin_case=min(R, key=lambda k: R[k]["margin_mm"]),
                 tip_deg={d: min(r["tip_deg"][d]["deg"] for r in R.values() if r["tip_deg"][d]) for d in ("forward", "back", "left", "right")},
                 push_tip_N={d: min(r["push_tip_N"][d] for r in R.values()) for d in map(str, DIRS8)},
                 slide_N_at_mu_0_4=round(0.4 * min(r["weight_N"] for r in R.values()), 2))
    ok = bool(all(r["inside"] and not r["fell"] for r in R.values()) and worst["margin_mm"] >= MARGIN_MIN_MM
              and min(worst["tip_deg"].values()) >= TIP_MIN_DEG)
    J = dict(generated_by="altaay_lab/twin/sit/sit_balance.py", label="sim pass only (settled poses, sim push); calc only (margins, tip angles, static push)",
             inputs_key=SS.inputs_key(a.out), gate=dict(margin_min_mm=MARGIN_MIN_MM, tip_min_deg=TIP_MIN_DEG), ok=ok, worst=worst, cases=R)
    print("worst", json.dumps(worst), "GATE", "PASS" if ok else "FAIL")
    if a.write:
        L.dump(J, os.path.join(HERE, "sit_balance.json"))
    if not ok:
        raise SystemExit("sit balance gate: FAIL")


if __name__ == "__main__":
    main()
