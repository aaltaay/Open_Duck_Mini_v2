#!/usr/bin/env python3
"""sit_sim.py: the A1b sit (D59) on the repo sim model (sit_model.py). sim pass only.

  python3 altaay_lab/twin/sit/sit_sim.py --out <scratch> push|up|walk|all [--jobs 3]
Writes <scratch>/sit_sim_<test>.json; `summary` (after the three) writes altaay_lab/twin/sit/sit_sim.json, the numbers SIT.md quotes.

The tests are the SIT_V2.md tests, run on the repo model instead of the study's scratch copy:
  push   torque off for 60 s on the dock pads, 0.2 s pushes: 8 directions at 3, 5, 8 and 12 N, single 8 N pushes from 8
         directions (15 s), and the stress cases (power-off damping 0.05, joint friction 0.02 and 0.2, a mat at mu 0.4,
         no pin springs): 17 cases, the four pad zones (CHG+, SENSE, SYS, GND; FEET_DOCK pads and pins) at the end and at
         their lowest, drift, pitch and face angle, falls
  up     sit down with torque on, hold torque off 20 s with 3 random pushes, stand up; 20 seeds at zero error of
         0, 0.5 and 1.0 deg (1 sigma per leg joint) on the model torque limit and at 1.0 deg on the sheet limits
  walk   the stock BEST_WALK_ONNX_2 through the repo walk loop (sim/added_mass_sim.py run(), unchanged), 10 seeds:
         forward 0.15 m/s 14 s, turn 1.0 rad/s 6 s, side 0.2 m/s 6 s on mu 0.6: speed, falls, the lowest point of the seat
         and the bumper; on the sit model and on the model before the sit (C8's 'ours': the same mass budget and repo
         loop), so the difference is the sit change alone
Model differences to the study (SIT_V2.md): the mass is the repo mass budget with the sit parts (not ours_b, 2.767 kg);
the seat and bumper are the printed shapes (not capsules); the shins are the joggled sheets; the actuator ranges are
the software limits (3 deg inside every stop), so the sit is commanded at knee 147, ankle -92, neck +22, head -22 and
gravity carries the joints onto their stops when the torque goes off.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402
import sit_model as SM  # noqa: E402

D = np.radians
SOLES = ("left_foot_bottom_tpu", "right_foot_bottom_tpu")
FEET = ("foot_assembly", "foot_assembly_2")
KP = 13.37                       # the Playground sts3215 class
# dock pads: FEET_DOCK.md 2.3 (two per foot, centres +/-26 mm, 44 x 34 mm) and the mat's pin rows (2 x 7 per zone, 6 mm
# pitch, +/-7 mm); a pad is made with 2 or more pins within 1.0 mm (DEEP_ANALYSIS.md); pin force 0.30 to 0.58 N over
# 1.2 mm of travel (0.44 N mid stroke, Mill-Max 0933, FEET_DOCK.md 2.4; est)
PADS = [("L", "toe", "CHG+", 0, +0.026), ("L", "heel", "SENSE", 0, -0.026), ("R", "toe", "SYS", 1, +0.026), ("R", "heel", "GND", 1, -0.026)]
PIN_F0, PIN_F1, PIN_REACH = 0.30, 0.58, 0.0012
DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
STAND = (-15.0, 5.0, 0.0)
# the A1b path (SIT_V2.md 3.2) with every waypoint inside the software limits (servo_limits.json)
DOWN = [((-21, 40, -29, -19, -22), 1.5), ((-33, 75, -49, -19, -22), 1.5), ((-54, 110, -67, -19, -22), 1.5),
        ((-58, 130, -82, -19, -22), 1.2), ((-60, 147, -92, -19, -22), 1.2)]
SIT = (-60, 147, -92, 22, -22)
UP = [(-60, 147, -92), (-58, 130, -82), (-54, 110, -67), (-33, 75, -49), (-21, 40, -29), (-15, 5, 0)]


# ---------------------------------------------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------------------------------------------
_MD = {}


def model(out, mu=0.8):
    import mujoco as m
    k = (out, mu)
    if k in _MD:
        return _MD[k]
    d = os.path.join(out, "sit")
    md = SM.check(d) if os.path.exists(os.path.join(d, "sit_model.json")) else None
    if md is None:
        raise SystemExit("build the model first: sit_model.py --out %s" % out)
    for g in range(md.ngeom):
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or ""
        if nm == "floor":
            md.geom_contype[g], md.geom_conaffinity[g] = 1, 1
            md.geom_friction[g] = [mu, 0.02, 0.002]
            continue
        if md.geom_group[g] == 2 or nm in SOLES:          # every printed part touches the floor, not the robot
            md.geom_contype[g], md.geom_conaffinity[g] = 0, 1
            if nm not in SOLES:
                md.geom_friction[g] = [0.8, 0.02, 0.002]
    _MD[k] = md
    return md


def aid(md, n):
    import mujoco as m
    return m.mj_name2id(md, m.mjtObj.mjOBJ_ACTUATOR, n)


def targets(md, h, k, a, neck=0.0, head=0.0, roll=0.0, yaw=0.0, off=None):
    c = np.zeros(md.nu)
    for side, s in (("left", 1), ("right", -1)):
        c[aid(md, side + "_hip_pitch")] = s * D(h)
        c[aid(md, side + "_knee")] = D(k)
        c[aid(md, side + "_ankle")] = D(a)
        c[aid(md, side + "_hip_roll")] = s * D(roll)
        c[aid(md, side + "_hip_yaw")] = s * D(yaw)
    c[aid(md, "neck_pitch")] = D(neck)
    c[aid(md, "head_pitch")] = D(head)
    return c + (off if off is not None else 0.0)


def torque(md, on, kp=KP):
    md.actuator_gainprm[:, 0] = kp if on else 0.0
    md.actuator_biasprm[:, 1] = -kp if on else 0.0
    md.actuator_biasprm[:, 2] = 0.0


def sole_world(md, dd, j):
    import mujoco as m
    g = m.mj_name2id(md, m.mjtObj.mjOBJ_GEOM, SOLES[j])
    mid = md.geom_dataid[g]
    a, n = md.mesh_vertadr[mid], md.mesh_vertnum[mid]
    return md.mesh_vert[a:a + n] @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g]


def sole_frames(md, dd):
    import mujoco as m
    out = []
    for j in range(2):
        bi = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, FEET[j])
        vw = sole_world(md, dd, j)
        low = vw[vw[:, 2] < vw[:, 2].min() + 0.002]
        R = dd.xmat[bi].reshape(3, 3)
        p = dd.xpos[bi]
        c = ((low - p) @ R).mean(0)
        ax = np.argmax(abs(R[0, :]))
        f = np.zeros(3)
        f[ax] = np.sign(R[0, ax])
        nz = np.argmax(abs(R[2, :]))
        nn = np.zeros(3)
        nn[nz] = np.sign(R[2, nz])
        out.append((bi, c, f, np.cross(nn, f)))
    return out


def make_pins(dd, SF):
    pins = {}
    for side, end, net, j, pc in PADS:
        bi, c, f, l_ = SF[j]
        R = dd.xmat[bi].reshape(3, 3)
        p = dd.xpos[bi]
        pins[net] = np.array([(p + R @ (c + (pc + r) * f + y * l_))[:2] for r in (-0.007, 0.007) for y in np.arange(-0.018, 0.0181, 0.006)])
    return pins


def pin_eval(md, dd, SF, pins, apply=False, pins_on=True):
    import mujoco as m
    made = {}
    if apply:
        dd.qfrc_applied[:] = 0
    for side, end, net, j, pc in PADS:
        bi, c, f, l_ = SF[j]
        R = dd.xmat[bi].reshape(3, 3)
        p = dd.xpos[bi]
        fw, lw = R @ f, R @ l_
        A = np.array([[fw[0], lw[0]], [fw[1], lw[1]]])
        cnt = 0
        for P in pins[net]:
            o = p + R @ c
            loc = np.linalg.solve(A, P - o[:2])
            for _ in range(2):
                w = p + R @ (c + loc[0] * f + loc[1] * l_)
                loc = loc + np.linalg.solve(A, P - w[:2])
            w = p + R @ (c + loc[0] * f + loc[1] * l_)
            gap = w[2]
            if abs(loc[0] - pc) < 0.022 and abs(loc[1]) < 0.017 and gap < 0.0010:
                cnt += 1
            if apply and pins_on and abs(loc[0]) < 0.050 and abs(loc[1]) < 0.020 and gap < PIN_REACH:
                Fp = PIN_F0 + (PIN_F1 - PIN_F0) * (1 - max(gap, 0) / PIN_REACH)
                m.mj_applyFT(md, dd, np.array([0, 0, Fp]), np.zeros(3), np.array([P[0], P[1], 0.0]), bi, dd.qfrc_applied)
        made[net] = cnt
    return made


def trunk_state(md, dd):
    import mujoco as m
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    R = dd.xmat[tr].reshape(3, 3)
    return dict(z=float(dd.xpos[tr][2]), pitch=float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))),
                roll=float(np.degrees(np.arctan2(R[2, 1], R[2, 2]))), up=float(R[2, 2]))


def head_elev(md, dd):
    import mujoco as m
    h = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")
    R = dd.xmat[h].reshape(3, 3)
    f = -R[:, 2]
    return float(np.degrees(np.arcsin(np.clip(f[2], -1, 1))))


def stance_start(md):
    import mujoco as m
    dd = m.MjData(md)
    torque(md, True)
    q = md.key_qpos[0].copy()
    c0 = targets(md, *STAND)
    for i in range(md.nu):
        q[md.jnt_qposadr[md.actuator_trnid[i, 0]]] = c0[i]
    pit = D(-10.0)
    q[3:7] = [np.cos(pit / 2), 0, np.sin(pit / 2), 0]
    q[0:3] = [0, 0, 0.3]
    dd.qpos[:] = q
    for _ in range(30):
        m.mj_kinematics(md, dd)
        V = sole_world(md, dd, 0)
        s = np.linalg.lstsq(np.c_[V[:, 0], np.ones(len(V))], V[:, 2], rcond=None)[0][0]
        pit += np.arctan(s)
        dd.qpos[3:7] = [np.cos(pit / 2), 0, np.sin(pit / 2), 0]
    m.mj_kinematics(md, dd)
    z = min(sole_world(md, dd, j)[:, 2].min() for j in range(2))
    dd.qpos[2] -= z - 0.0002
    dd.ctrl[:] = c0
    m.mj_forward(md, dd)
    for _ in range(int(1.0 / md.opt.timestep)):
        m.mj_step(md, dd)
    return dd, c0


def ramp(md, dd, c0, c1, T, cb=None):
    import mujoco as m
    n = max(1, int(T / md.opt.timestep))
    for i in range(n):
        s = 0.5 - 0.5 * np.cos(np.pi * (i + 1) / n)
        dd.ctrl[:] = c0 * (1 - s) + c1 * s
        m.mj_step(md, dd)
        if cb:
            cb(md, dd)
    return c1.copy()


class Track:
    def __init__(self, md):
        self.tmax = np.zeros(md.nu)

    def __call__(self, md, dd):
        self.tmax = np.maximum(self.tmax, abs(dd.actuator_force))


def enter(md, off=None, pins_on=True):
    import mujoco as m
    dd, c0 = stance_start(md)
    SF = sole_frames(md, dd)
    pins = make_pins(dd, SF)
    tr = Track(md)

    def cb(md, dd):
        pin_eval(md, dd, SF, pins, apply=True, pins_on=pins_on)
        tr(md, dd)
    c = c0
    for (h, k, a, n, hd), T in DOWN:
        c = ramp(md, dd, c, targets(md, h, k, a, n, hd, off=off), T, cb)
    c = ramp(md, dd, c, targets(md, *SIT, off=off), 1.5, cb)
    for _ in range(int(0.5 / md.opt.timestep)):
        m.mj_step(md, dd)
        cb(md, dd)
    return dd, SF, pins, tr, cb


def hold(md, dd, SF, pins, F=3.0, dirs=DIRS, T=60.0, t_first=5.0, gap=6.0, dur=0.2, pins_on=True):
    """torque off, pushes on the trunk; pads, drift, pitch, face, stop torques (the joint limit forces)"""
    import mujoco as m
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    torque(md, False)
    sched = [(t_first + i * gap, d) for i, d in enumerate(dirs)]
    t0 = dd.time
    ref = None
    minpads = {}
    pr, hr = [99, -99], [99, -99]
    lim = {}
    for i in range(int(T / md.opt.timestep)):
        t = dd.time - t0
        dd.xfrc_applied[:] = 0
        for ts, dg in sched:
            if ts <= t < ts + dur:
                dd.xfrc_applied[tr, :3] = [F * np.cos(D(dg)), F * np.sin(D(dg)), 0]
        pin_eval(md, dd, SF, pins, apply=True, pins_on=pins_on)
        m.mj_step(md, dd)
        if ref is None and t >= t_first - 0.1:
            ref = dd.qpos[0:3].copy()
        if i % 50 == 0 and t >= t_first - 0.1:
            p = pin_eval(md, dd, SF, pins)
            for k, v in p.items():
                minpads[k] = min(minpads.get(k, 99), v)
            ts_ = trunk_state(md, dd)
            pr = [min(pr[0], ts_["pitch"]), max(pr[1], ts_["pitch"])]
            he = head_elev(md, dd)
            hr = [min(hr[0], he), max(hr[1], he)]
            # stop torques: the constraint force on each limited joint dof
            for j in range(1, md.njnt):
                f = abs(dd.qfrc_constraint[md.jnt_dofadr[j]])
                n = m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j)
                lim[n] = max(lim.get(n, 0.0), float(f))
    ts_ = trunk_state(md, dd)
    pads = pin_eval(md, dd, SF, pins)
    return dict(F=F, dirs=list(dirs), drift_mm=float(np.linalg.norm(dd.qpos[0:2] - ref[0:2]) * 1000), pitch=ts_["pitch"],
                pitch_range=pr, head_elev=head_elev(md, dd), head_range=hr, z_mm=ts_["z"] * 1000, fell=bool(ts_["up"] < 0.8),
                pads_final=pads, pads_min=minpads, all4_final=bool(min(pads.values()) >= 2), all4_always=bool(min(minpads.values()) >= 2),
                constraint_torque_max={k: round(v, 3) for k, v in lim.items() if v > 0.01},
                joints={n: round(float(np.degrees(dd.qpos[md.jnt_qposadr[j]])), 1) for j in range(1, md.njnt)
                        for n in [m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j)]})


def rise(md, dd, cb, off=None, T=1.5):
    import mujoco as m
    q = np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i, 0]]] for i in range(md.nu)])
    lo, hi = md.actuator_ctrlrange[:, 0], md.actuator_ctrlrange[:, 1]
    c = np.clip(q, lo, hi)
    dd.ctrl[:] = c
    torque(md, True)
    for _ in range(int(0.3 / md.opt.timestep)):
        m.mj_step(md, dd)
        cb(md, dd)
    roll = np.degrees(q[aid(md, "left_hip_roll")])
    yaw = np.degrees(q[aid(md, "left_hip_yaw")])
    hp = np.degrees(q[aid(md, "left_hip_pitch")])
    n, hd = -19.0, -22.0
    c = ramp(md, dd, c, targets(md, hp, 147, -92, n, hd, roll, yaw, off=off), 1.0, cb)
    for w in UP:
        c = ramp(md, dd, c, targets(md, *w, n, hd, roll, yaw, off=off), T, cb)
    c = ramp(md, dd, c, targets(md, *STAND, 0, 0, roll, yaw, off=off), 1.5, cb)
    for _ in range(int(1.0 / md.opt.timestep)):
        m.mj_step(md, dd)
        cb(md, dd)


# ---------------------------------------------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------------------------------------------
OUT = [None]


def push_job(a):
    name, opt = a
    t = time.time()
    md = model(OUT[0], opt.get("mu", 0.8))
    torque(md, True)
    saved = (md.dof_frictionloss.copy(), md.dof_damping.copy())
    if "fric" in opt:
        md.dof_frictionloss[6:] = opt["fric"]
    dd, SF, pins, tr, cb = enter(md, pins_on=opt.get("pins", True))
    if "off_damp" in opt:
        md.dof_damping[6:] = opt["off_damp"]
    r = hold(md, dd, SF, pins, F=opt["F"], dirs=opt.get("dirs", DIRS), T=opt.get("T", 60.0), pins_on=opt.get("pins", True))
    md.dof_frictionloss[:], md.dof_damping[:] = saved
    r.update(name=name, opt=opt, secs=round(time.time() - t, 1), entry_tau_max={md.actuator(i).name: round(float(tr.tmax[i]), 3) for i in range(md.nu)})
    print(name, "fell", r["fell"], "drift %.1f" % r["drift_mm"], "pitch %.1f face %.1f" % (r["pitch"], r["head_elev"]), "pads", r["pads_final"], "min", r["pads_min"], flush=True)
    return r


def push_cases():
    J = []
    for F in (3, 5, 8):
        J.append(("8dirs_F%d" % F, dict(F=F)))
    for d in DIRS:
        J.append(("single_%d_F8" % d, dict(F=8, dirs=[d], T=15)))
    J += [("poweroff_damp0.05_F8", dict(F=8, off_damp=0.05)), ("fric0.02_F5", dict(F=5, fric=0.02)),
          ("fric0.2_F8", dict(F=8, fric=0.2)), ("mat_mu0.4_F8", dict(F=8, mu=0.4)), ("pins_off_F8", dict(F=8, pins=False)),
          ("8dirs_F12", dict(F=12))]
    return J


def up_job(a):
    seed, sig, lim = a
    import mujoco as m
    rng = np.random.default_rng(seed)
    mu = float(rng.uniform(0.6, 1.0))
    kp = KP * float(rng.uniform(0.85, 1.15))
    md = model(OUT[0], round(mu, 3))
    saved = (md.actuator_forcerange.copy(), md.dof_damping.copy())
    if lim == "sheet":                                     # STS3250 knees 2.94 Nm at 7.2 V [F5], STS3215 1.91 Nm [F1]
        for i in range(md.nu):
            v = 2.94 if "knee" in md.actuator(i).name else 1.91
            md.actuator_forcerange[i] = [-v, v]
    off = np.zeros(md.nu)
    for i in range(md.nu):
        if any(s in md.actuator(i).name for s in ("hip", "knee", "ankle")):
            off[i] = D(rng.normal(0, sig))
    torque(md, True, kp)
    dd, SF, pins, tr_in, cb = enter(md, off=off)
    dirs = list(rng.choice(DIRS, 3))
    F = float(rng.uniform(3, 8))
    r = hold(md, dd, SF, pins, F=F, dirs=dirs, T=20, t_first=3, gap=5)
    if seed % 2:
        md.dof_damping[6:] = 0.05
    md.dof_damping[6:] = saved[1][6:]
    tr = Track(md)

    def cb2(md, dd):
        pin_eval(md, dd, SF, pins, apply=True)
        tr(md, dd)
    torque(md, True, kp)
    rise(md, dd, cb2, off=off)
    ts = trunk_state(md, dd)
    pads = pin_eval(md, dd, SF, pins)
    stood = bool(ts["up"] > 0.95 and ts["z"] > 0.17)
    md.actuator_forcerange[:], md.dof_damping[:] = saved
    return dict(seed=seed, sig=sig, lim=lim, sit_pads=r["pads_final"], sit_all4=r["all4_final"], sit_fell=r["fell"], stood=stood,
                success=bool(stood and min(pads.values()) >= 2), pads_after=pads,
                rise_tau={md.actuator(i).name: float(tr.tmax[i]) for i in range(md.nu)},
                entry_tau={md.actuator(i).name: float(tr_in.tmax[i]) for i in range(md.nu)}, stop_torque=r["constraint_torque_max"])


def walk_model_dirs(out):
    """the sit model and the model before the sit (C8's 'ours' of the base worktree, given as ODM_BEFORE_MODEL)"""
    return dict(sit=os.path.join(out, "sit"), before=os.environ.get("ODM_BEFORE_MODEL"))


def walk_job(a):
    """one seed of the stock walk on a model folder (the repo walk loop, sim/added_mass_sim.py run())"""
    tag, d, seed = a
    import importlib
    sys.path.insert(0, os.path.join(L.LAB, "sim"))
    os.environ.setdefault("ODM_SCRATCH", os.path.join(OUT[0], "am_scratch"))
    AM = importlib.import_module("added_mass_sim")
    import mujoco as m
    if os.path.exists(os.path.join(d, "sit_model.json")):
        A = SM.assets(d)
        ga = lambda: A  # noqa: E731
    else:
        def ga():
            a_ = {}
            for f in os.listdir(os.path.join(SM.SRC_XML, "assets")):
                a_[f] = open(os.path.join(SM.SRC_XML, "assets", f), "rb").read()
            for f in os.listdir(d):
                if f.endswith(".xml"):
                    a_[f] = open(os.path.join(d, f), "rb").read()
            return a_
    AM.CB.base.get_assets = ga
    sys.modules["playground.open_duck_mini_v2.base"].get_assets = ga
    AM._get_assets = ga
    sched = lambda t: [0.15, 0, 0, 0, 0, 0, 0] if t < 16 else ([0, 0, 1.0, 0, 0, 0, 0] if t < 22 else [0, 0.2, 0, 0, 0, 0, 0])  # noqa: E731
    res = AM.run(d, "scene_flat_terrain.xml", sched, 28.0, seed=seed)
    lg = res["log"]
    t, x, y = lg[:, 0], lg[:, 1], lg[:, 2]
    i0, i1 = np.searchsorted(t, 4.0), np.searchsorted(t, 16.0)
    v = float(np.hypot(x[i1] - x[i0], y[i1] - y[i0]) / (t[i1] - t[i0]))
    yaw = np.unwrap(lg[:, 4])
    j0, j1 = np.searchsorted(t, 16.5), np.searchsorted(t, 22.0)
    turn = float((yaw[j1] - yaw[j0]) / (t[j1] - t[j0]))
    return dict(tag=tag, seed=seed, v=v, turn=turn, falls=res["falls"], fell=bool(res["falls"]))


def summary(out):
    """the aggregate numbers of the three runs in <out> (sim pass only)"""
    from collections import defaultdict
    J = {t: json.load(open(os.path.join(out, "sit_sim_%s.json" % t))) for t in ("push", "up", "walk")}
    M = json.load(open(os.path.join(out, "sit", "sit_model.json")))
    P = J["push"]["results"]
    push = dict(cases=len(P), falls=sum(r["fell"] for r in P), all4_pads_at_end=sum(r["all4_final"] for r in P),
                all4_pads_throughout=sum(r["all4_always"] for r in P),
                not_all4_at_end=[r["name"] for r in P if not r["all4_final"]],
                lost_a_pad_on_the_way=[r["name"] for r in P if not r["all4_always"]],
                max_drift_mm=round(max(r["drift_mm"] for r in P), 1),
                pitch_deg=[round(min(r["pitch"] for r in P), 1), round(max(r["pitch"] for r in P), 1)])
    G = defaultdict(list)
    for r in J["up"]["results"]:
        G["%s deg, %s limit" % (r["sig"], r["lim"])].append(r)
    up = {k: dict(seeds=len(v), sat_with_4_pads=sum(r["sit_all4"] for r in v), fell_in_the_sit=sum(r["sit_fell"] for r in v),
                  stood=sum(r["stood"] for r in v), stood_and_4_pads=sum(r["success"] for r in v)) for k, v in G.items()}
    pk = {}
    for r in J["up"]["results"]:
        for src in ("rise_tau", "entry_tau"):
            for j_, t_ in (r.get(src) or {}).items():
                pk[j_] = max(pk.get(j_, 0.0), t_)
    W = defaultdict(list)
    for r in J["walk"]["results"]:
        W[r["tag"]].append(r)
    walk = {k: dict(seeds=len(v), falls=sum(r["fell"] for r in v), forward_m_s=round(float(np.mean([r["v"] for r in v])), 4),
                    turn_rad_s=round(float(np.mean([r["turn"] for r in v if r["turn"] is not None])), 3)) for k, v in W.items()}
    return dict(generated_by="altaay_lab/twin/sit/sit_sim.py summary", label="sim pass only", model=M, push=push, up=up,
                up_peak_torque_Nm={k: round(v, 2) for k, v in sorted(pk.items())}, walk=walk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("test", choices=("push", "up", "walk", "summary"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args()
    OUT[0] = a.out
    t0 = time.time()
    if a.test == "summary":
        L.dump(summary(a.out), os.path.join(HERE, "sit_sim.json"))
        print("wrote altaay_lab/twin/sit/sit_sim.json")
        return
    if a.test == "push":
        J = push_cases()
        with Pool(a.jobs, initializer=_init, initargs=(a.out,)) as p:
            R = p.map(push_job, J, chunksize=1)
    elif a.test == "up":
        J = [(s, sig, lim) for sig, lim in ((0.0, "model"), (0.5, "model"), (1.0, "model"), (1.0, "sheet")) for s in range(a.seeds)]
        with Pool(a.jobs, initializer=_init, initargs=(a.out,)) as p:
            R = p.map(up_job, J, chunksize=1)
    else:
        dirs = walk_model_dirs(a.out)
        if not dirs["before"] or not os.path.isdir(dirs["before"]):
            raise SystemExit("set ODM_BEFORE_MODEL to the C8 'ours' model folder of the commit before the sit (the walk compares both)")
        J = [(tag, d, s) for tag, d in dirs.items() if d for s in range(10)]
        with Pool(a.jobs, initializer=_init, initargs=(a.out,)) as p:
            R = p.map(walk_job, J, chunksize=1)
    L.dump(dict(test=a.test, seconds=round(time.time() - t0), results=R), os.path.join(a.out, "sit_sim_%s.json" % a.test))
    print("done", a.test, round(time.time() - t0), "s")


def _init(out):
    OUT[0] = out


if __name__ == "__main__":
    main()
