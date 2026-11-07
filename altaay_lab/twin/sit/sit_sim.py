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
# the A1b path (sitlib.PATH_A1B: the study path with the trunk leaned forward in the middle, SIT.md section 5) with the
# head forward waypoints inside the software limits (servo_limits.json); the ramp times are the study's
NH = (-19, -22)
_W = [w[:3] for w in L.PATH_A1B[1:6]]
DOWN = [((*w, *NH), T) for w, T in zip(_W, (1.5, 1.5, 1.5, 1.2, 1.2))]
SIT = (-60, 147, -92, 22, -22)
UP = [w[:3] for w in L.PATH_A1B[5:0:-1]] + [STAND]


# ---------------------------------------------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------------------------------------------
_MD = {}


def model(out, mu=0.8, mass=None):
    """the sit model with the floor at friction mu and, with mass {body: factor}, those bodies' mass and inertia
    scaled: a model variant per (mu, mass), each compiled once. The mass edit comes before the collision edits and
    mj_setConst refreshes the compiled constants (body_subtreemass, the solver's inverse weights) while the model is
    still in its compiled collision state (after the collision edits mj_setConst refuses the model)."""
    import mujoco as m
    k = (out, mu, tuple(sorted((mass or {}).items())))
    if k in _MD:
        return _MD[k]
    d = os.path.join(out, "sit")
    md = SM.check(d) if os.path.exists(os.path.join(d, "sit_model.json")) else None
    if md is None:
        raise SystemExit("build the model first: sit_model.py --out %s" % out)
    if mass:
        for bn, f in mass.items():
            b = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, bn)
            if b < 0:
                raise SystemExit("mass edit: no body %s" % bn)
            md.body_mass[b] *= f
            md.body_inertia[b] *= f
        m.mj_setConst(md, m.MjData(md))
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


def stance_start(md, kp=KP):
    import mujoco as m
    dd = m.MjData(md)
    torque(md, True, kp)
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


def enter(md, off=None, pins_on=True, kp=KP):
    """stand, then the A1b path down with torque on at gain kp (the caller's randomized gain is kept throughout)"""
    import mujoco as m
    dd, c0 = stance_start(md, kp)
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
    jn = {j: m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j) for j in range(1, md.njnt)}
    stops = Stops(md, jn)
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
        # every physics step from the moment the torque goes off: the largest constraint torque on each joint (the
        # landing on the stops comes first; an impact lasts a few steps, a decimated or delayed sample would miss it)
        for j in range(1, md.njnt):
            f = abs(dd.qfrc_constraint[md.jnt_dofadr[j]])
            n = jn[j]
            if f > lim.get(n, 0.0):
                lim[n] = float(f)
        stops(dd)
        if t >= t_first - 0.1:
            # every physics step once it has settled: the least pins per pad, the pitch and head ranges at rest
            p = pin_eval(md, dd, SF, pins)
            for k, v in p.items():
                minpads[k] = min(minpads.get(k, 99), v)
            ts_ = trunk_state(md, dd)
            pr = [min(pr[0], ts_["pitch"]), max(pr[1], ts_["pitch"])]
            he = head_elev(md, dd)
            hr = [min(hr[0], he), max(hr[1], he)]
    ts_ = trunk_state(md, dd)
    pads = pin_eval(md, dd, SF, pins)
    return dict(F=F, dirs=list(dirs), drift_mm=float(np.linalg.norm(dd.qpos[0:2] - ref[0:2]) * 1000), pitch=ts_["pitch"],
                pitch_range=pr, head_elev=head_elev(md, dd), head_range=hr, z_mm=ts_["z"] * 1000, fell=bool(ts_["up"] < 0.8),
                pads_final=pads, pads_min=minpads, all4_final=bool(min(pads.values()) >= 2), all4_always=bool(min(minpads.values()) >= 2),
                constraint_torque_max={k: round(v, 3) for k, v in lim.items() if v > 0.01},
                **stops.report(),
                joints={n: round(float(np.degrees(dd.qpos[md.jnt_qposadr[j]])), 1) for j in range(1, md.njnt)
                        for n in [m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j)]})


class Stops:
    """per joint end ("<joint>:lo" / "<joint>:hi"): the largest joint limit constraint torque so far (force, a stop
    load belongs to the end it acts at: the designed stop is one end only), the largest impact speed (|qvel| on the
    step before the limit constraint first becomes active in an event: the energy method's omega, which converges
    with the step unlike the peak force), and the limit torque on the last step (rest). Call after every mj_step."""

    def __init__(self, md, jn):
        self.md, self.jn = md, jn
        self.force, self.omega, self.rest = {}, {}, {}
        self.active = set()
        self.qvel_prev = None

    def __call__(self, dd):
        import mujoco as m
        md = self.md
        now = {}
        for i in range(dd.nefc):
            if dd.efc_type[i] == m.mjtConstraint.mjCNSTR_LIMIT_JOINT:
                j = dd.efc_id[i]
                lo, hi = md.jnt_range[j]
                k = "%s:%s" % (self.jn[j], "lo" if dd.qpos[md.jnt_qposadr[j]] < 0.5 * (lo + hi) else "hi")
                now[k] = now.get(k, 0.0) + abs(float(dd.efc_force[i]))
        for k, f in now.items():
            if f > self.force.get(k, 0.0):
                self.force[k] = f
            if k not in self.active and self.qvel_prev is not None:
                j = m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, k.split(":")[0])
                w = abs(float(self.qvel_prev[md.jnt_dofadr[j]]))
                if w > self.omega.get(k, 0.0):
                    self.omega[k] = w
        self.active = set(now)
        self.rest = now
        self.qvel_prev = dd.qvel.copy()

    def report(self):
        r3 = lambda d: {k: round(v, 3) for k, v in sorted(d.items()) if v > 0.01}  # noqa: E731
        return dict(limit_torque_max=r3(self.force), limit_omega_max={k: round(v, 4) for k, v in sorted(self.omega.items())},
                    limit_torque_rest=r3(self.rest))


def rise(md, dd, cb, off=None, T=1.5, kp=KP):
    import mujoco as m
    q = np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i, 0]]] for i in range(md.nu)])
    lo, hi = md.actuator_ctrlrange[:, 0], md.actuator_ctrlrange[:, 1]
    c = np.clip(q, lo, hi)
    dd.ctrl[:] = c
    torque(md, True, kp)
    for _ in range(int(0.3 / md.opt.timestep)):
        m.mj_step(md, dd)
        cb(md, dd)
    # the torque-off sit lets the legs splay onto the outward hip roll stops (-8 deg): the first ramp, while the seat
    # still carries the trunk, brings roll and yaw back to the stance's 0 so the feet keep their place on the pads as the
    # legs extend (keeping the splay slid the feet 20 mm apart, off the pads: SIT.md section 5)
    roll = yaw = 0.0
    hp = np.degrees(q[aid(md, "left_hip_pitch")])
    n, hd = NH
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
    saved = (md.dof_frictionloss.copy(), md.dof_damping.copy(), md.opt.timestep)
    md.opt.timestep = opt.get("dt", saved[2])
    if "fric" in opt:
        md.dof_frictionloss[6:] = opt["fric"]
    dd, SF, pins, tr, cb = enter(md, pins_on=opt.get("pins", True))
    if "off_damp" in opt:
        md.dof_damping[6:] = opt["off_damp"]
    r = hold(md, dd, SF, pins, F=opt["F"], dirs=opt.get("dirs", DIRS), T=opt.get("T", 60.0), pins_on=opt.get("pins", True))
    md.dof_frictionloss[:], md.dof_damping[:], md.opt.timestep = saved
    r.update(name=name, opt=opt, secs=round(time.time() - t, 1), entry_tau_max={md.actuator(i).name: round(float(tr.tmax[i]), 3) for i in range(md.nu)})
    print(name, "fell", r["fell"], "drift %.1f" % r["drift_mm"], "pitch %.1f face %.1f" % (r["pitch"], r["head_elev"]), "pads", r["pads_final"], "min", r["pads_min"], flush=True)
    return r


SHOVE_N = 12.0                   # a shove on the head (D59 review: a toy gets shoved)


def shove_job(a):
    """a SHOVE_N horizontal force on the head's CoM, forward or back along the trunk heading, for dur s, from the settled
    sit with the torque off or on (on: the sit commands, neck +22 and head -22, 3 deg off their stops); the joint limit
    torques at each end on every step (sim pass only)"""
    name, opt = a
    import mujoco as m
    t0 = time.time()
    # the body held (a hand or a wall behind it): the trunk 1000 x heavier does not move, so the whole shove goes
    # into the neck and head stops (the stop load case; free, a 12 N head shove tips the sit over). A model variant
    # (model(mass=...)): the compiled constants follow the mass and the cached nominal model is not edited.
    md = model(OUT[0], mass={"trunk_assembly": 1000.0} if opt.get("held") else None)
    dt0 = md.opt.timestep
    md.opt.timestep = opt.get("dt", dt0)
    dd, SF, pins, tr, cb = enter(md)
    trb = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    jn = {j: m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j) for j in range(1, md.njnt)}
    if opt["torque"] == "off":
        torque(md, False)
    for _ in range(int(3.0 / md.opt.timestep)):
        pin_eval(md, dd, SF, pins, apply=True)
        m.mj_step(md, dd)
    hd = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")
    R = dd.xmat[trb].reshape(3, 3)
    f = np.r_[R[:2, 0] / np.linalg.norm(R[:2, 0]), 0.0] * (SHOVE_N if opt["dir"] == "forward" else -SHOVE_N)
    q = {}
    stops = Stops(md, jn)
    nk, hp = (m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, n) for n in ("neck_pitch", "head_pitch"))
    q0 = {n: float(np.degrees(dd.qpos[md.jnt_qposadr[j]])) for n, j in (("neck", nk), ("head", hp))}
    for i in range(int(2.0 / md.opt.timestep)):
        pin_eval(md, dd, SF, pins, apply=True)
        if i * md.opt.timestep < opt["dur"]:
            m.mj_applyFT(md, dd, f, np.zeros(3), dd.xipos[hd].copy(), hd, dd.qfrc_applied)
        m.mj_step(md, dd)
        stops(dd)
        for n_, j in (("neck", nk), ("head", hp)):
            v = float(np.degrees(dd.qpos[md.jnt_qposadr[j]]))
            q[n_] = [min(q.get(n_, [v, v])[0], v), max(q.get(n_, [v, v])[1], v)]
    torque(md, True)
    md.opt.timestep = dt0
    return dict(name=name, opt=opt, start_deg=q0, range_deg=q, **stops.report(),
                fell=bool(trunk_state(md, dd)["up"] < 0.8), secs=round(time.time() - t0, 1))


LOAD_DT = 0.0005                 # s: the stop loads converge here (the 12 N push case: within 15 % of 0.25 ms; 2 ms, the
                                 # model's own step, overstates the stiff printed lug stops up to 2.7 x)


def shove_cases(dt=LOAD_DT):
    return [("head_%s_torque_%s_%.1fs%s" % (d, t, u, "_held" if h else ""), dict(dir=d, torque=t, dur=u, dt=dt, held=h))
            for d in ("forward", "back") for t in ("off", "on") for u in (0.2, 1.0) for h in (True, False)]


def load_cases(dt=LOAD_DT):
    """the stop load runs of sit_stress.py: every push case at LOAD_DT (the behaviour runs keep the model's step)"""
    return [(n, dict(o, dt=dt)) for n, o in push_cases()]


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
    # a zero error moves the servo's own angle limit registers with it (they are written from the calibrated offset,
    # bench/set_angle_limits.py): the clamp shifts with the commands, so the control range moves by the same error
    saved_cr = md.actuator_ctrlrange.copy()
    md.actuator_ctrlrange[:] = saved_cr + off[:, None]
    dd, SF, pins, tr_in, cb = enter(md, off=off, kp=kp)
    dirs = list(rng.choice(DIRS, 3))
    F = float(rng.uniform(3, 8))
    r = hold(md, dd, SF, pins, F=F, dirs=dirs, T=20, t_first=3, gap=5)
    tr = Track(md)

    def cb2(md, dd):
        pin_eval(md, dd, SF, pins, apply=True)
        tr(md, dd)
    rise(md, dd, cb2, off=off, kp=kp)
    ts = trunk_state(md, dd)
    pads = pin_eval(md, dd, SF, pins)
    stood = bool(ts["up"] > 0.95 and ts["z"] > 0.17)
    md.actuator_forcerange[:], md.dof_damping[:] = saved
    md.actuator_ctrlrange[:] = saved_cr
    return dict(seed=seed, sig=sig, lim=lim, sit_pads=r["pads_final"], sit_all4=r["all4_final"], sit_fell=r["fell"], stood=stood,
                success=bool(stood and min(pads.values()) >= 2), pads_after=pads,
                rise_tau={md.actuator(i).name: float(tr.tmax[i]) for i in range(md.nu)},
                entry_tau={md.actuator(i).name: float(tr_in.tmax[i]) for i in range(md.nu)}, stop_torque=r["constraint_torque_max"], limit_torque_max=r["limit_torque_max"],
                limit_omega_max=r["limit_omega_max"], limit_torque_rest=r["limit_torque_rest"])


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
    key = inputs_key(out)
    stale = [t for t, j in J.items() if j.get("inputs_key") != key]
    if stale:
        raise SystemExit("sit_sim_%s.json was run on another model or sim code: run it again" % ", ".join(stale))
    M = json.load(open(os.path.join(out, "sit", "sit_model.json")))
    P = J["push"]["results"]
    push = dict(cases=len(P), falls=sum(r["fell"] for r in P), all4_pads_at_end=sum(r["all4_final"] for r in P),
                all4_pads_throughout=sum(r["all4_always"] for r in P),
                not_all4_at_end=[r["name"] for r in P if not r["all4_final"]],
                lost_a_pad_on_the_way=[r["name"] for r in P if not r["all4_always"]],
                max_drift_mm=round(max(r["drift_mm"] for r in P), 1),
                pitch_deg=[round(min(r["pitch"] for r in P), 1), round(max(r["pitch"] for r in P), 1)])
    def up_table(res):
        G = defaultdict(list)
        for r in res:
            G["%s deg, %s limit" % (r["sig"], r["lim"])].append(r)
        return {k: dict(seeds="%d to %d" % (min(r["seed"] for r in v), max(r["seed"] for r in v)), n=len(v),
                        sat_with_4_pads=sum(r["sit_all4"] for r in v), fell_in_the_sit=sum(r["sit_fell"] for r in v),
                        stood=sum(r["stood"] for r in v), stood_and_4_pads=sum(r["success"] for r in v),
                        failed_seeds=[r["seed"] for r in v if not r["success"]]) for k, v in G.items()}
    up = up_table(J["up"]["results"])
    up_held = None
    ph = os.path.join(out, "sit_sim_up_heldout.json")
    if os.path.exists(ph):
        H = json.load(open(ph))
        if H.get("inputs_key") != key:
            raise SystemExit("sit_sim_up_heldout.json was run on another model or sim code: run it again")
        up_held = up_table(H["results"])
    pk = {}
    for r in J["up"]["results"]:
        for src in ("rise_tau", "entry_tau"):
            for j_, t_ in (r.get(src) or {}).items():
                pk[j_] = max(pk.get(j_, 0.0), t_)
    shove = None
    ps = os.path.join(out, "sit_sim_shove.json")
    if os.path.exists(ps):
        H = json.load(open(ps))
        if H.get("inputs_key") != key:
            raise SystemExit("sit_sim_shove.json was run on another model or sim code: run it again")
        shove = {r["name"]: dict(fell=r["fell"], neck_deg=r["range_deg"]["neck"], head_deg=r["range_deg"]["head"],
                                 stop_Nm={k: v for k, v in r["limit_torque_max"].items() if k in ("neck_pitch:hi", "head_pitch:lo")})
                 for r in H["results"]}
    W = defaultdict(list)
    for r in J["walk"]["results"]:
        W[r["tag"]].append(r)
    walk = {k: dict(seeds=len(v), falls=sum(r["fell"] for r in v), forward_m_s=round(float(np.mean([r["v"] for r in v])), 4),
                    turn_rad_s=round(float(np.mean([r["turn"] for r in v if r["turn"] is not None])), 3)) for k, v in W.items()}
    return dict(generated_by="altaay_lab/twin/sit/sit_sim.py summary", label="sim pass only", inputs_key=key, model=M, push=push, up=up,
                up_heldout_seeds=up_held, head_shove_12N=shove,
                up_peak_torque_Nm={k: round(v, 2) for k, v in sorted(pk.items())}, walk=walk)


def _cached_job(args):
    fn, path, job = args
    r = fn(job)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(r, fh, default=float)
    os.replace(tmp, path)                       # one file per case, written whole: a restart keeps every finished case
    return r


def inputs_key(out):
    """the hash of everything a sim case reads: every file of the written model folder (the generated XML with every
    placement transform, sit_model.json), the bytes of every mesh and XML asset the model loads (SM.assets), the sim
    code (this file and the modules it imports for the run: sitlib.py, sit_model.py) and the MuJoCo and numpy
    versions. The run parameters of each case go into its file name (case_name)."""
    import hashlib
    import mujoco
    h = hashlib.sha256()
    d = os.path.join(out, "sit")
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            h.update(b"model/" + f.encode() + b"\0" + open(p, "rb").read())
    for k, v in sorted(SM.assets(d).items()):
        h.update(b"asset/" + k.encode() + b"\0" + v)
    for f in ("sit_sim.py", "sitlib.py", "sit_model.py"):
        h.update(b"code/" + f.encode() + b"\0" + open(os.path.join(HERE, f), "rb").read())
    h.update(("mujoco %s numpy %s" % (mujoco.__version__, np.__version__)).encode())
    return h.hexdigest()[:16]


def case_name(name, job):
    """a case file name: the readable case name and the hash of every run parameter of the job"""
    import hashlib
    return "%s_%s" % (name, hashlib.sha256(json.dumps(job, sort_keys=True, default=str).encode()).hexdigest()[:10])


def run_cached(a, test, J, fn, key):
    """run the cases of a test in a pool, one result file per case under <out>/cases_<test>_<inputs_key>/: a changed
    model, mesh, placement or sim code starts a fresh folder; a case whose file exists (same name and parameters) is
    not run again"""
    d = os.path.join(a.out, "cases_%s_%s" % (test, inputs_key(a.out)))
    os.makedirs(d, exist_ok=True)
    path = {key(j): os.path.join(d, case_name(key(j), j) + ".json") for j in J}
    if len(path) != len(J):
        raise SystemExit("%s: two cases share a name" % test)
    todo = [(fn, path[key(j)], j) for j in J if not os.path.exists(path[key(j)])]
    print("%s: %d cases, %d done before (%s)" % (test, len(J), len(J) - len(todo), os.path.basename(d)), flush=True)
    if todo:
        with Pool(a.jobs, initializer=_init, initargs=(a.out,)) as p:
            p.map(_cached_job, todo, chunksize=1)
    R = [json.load(open(path[key(j)])) for j in J]
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("test", choices=("push", "up", "walk", "shove", "loads", "summary"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=0, help="up: the first seed (100: the held-out seeds 100 to 119, never used "
                    "for tuning the sequence; written to sit_sim_up_heldout.json)")
    a = ap.parse_args()
    OUT[0] = a.out
    t0 = time.time()
    if a.test == "summary":
        L.dump(summary(a.out), os.path.join(HERE, "sit_sim.json"))
        print("wrote altaay_lab/twin/sit/sit_sim.json")
        return
    if a.test == "push":
        R = run_cached(a, "push", push_cases(), push_job, lambda j: j[0])
    elif a.test == "shove":
        R = run_cached(a, "shove", shove_cases(), shove_job, lambda j: j[0])
    elif a.test == "loads":
        R = run_cached(a, "loads", load_cases(), push_job, lambda j: j[0])
    elif a.test == "up":
        J = [(s, sig, lim) for sig, lim in ((0.0, "model"), (0.5, "model"), (1.0, "model"), (1.0, "sheet")) for s in range(a.seed0, a.seed0 + a.seeds)]
        R = run_cached(a, "up", J, up_job, lambda j: "s%d_sig%s_%s" % j)
    else:
        dirs = walk_model_dirs(a.out)
        if not dirs["before"] or not os.path.isdir(dirs["before"]):
            raise SystemExit("set ODM_BEFORE_MODEL to the C8 'ours' model folder of the commit before the sit (the walk compares both)")
        J = [(tag, d, s) for tag, d in dirs.items() if d for s in range(10)]
        with Pool(a.jobs, initializer=_init, initargs=(a.out,)) as p:
            R = p.map(walk_job, J, chunksize=1)
    L.dump(dict(test=a.test, inputs_key=inputs_key(a.out), seconds=round(time.time() - t0), results=R),
           os.path.join(a.out, "sit_sim_%s.json" % (a.test + ("_heldout" if a.test == "up" and a.seed0 else ""))))
    print("done", a.test, round(time.time() - t0), "s")


def _init(out):
    OUT[0] = out


if __name__ == "__main__":
    main()
