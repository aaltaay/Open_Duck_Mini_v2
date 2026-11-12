#!/usr/bin/env python3
"""close_run.py: keep the nest in view for the last stretch. sim pass only.

Same walk law and same seeds as the blind walk-in: mixed controller, two 1 mm steps,
aim 20 mm right at 7.2 V, sun 190 mm from the wall. The perception loop is that
walk-in's: a pose fix only while a target point is inside the camera field, then
dead reckoning at the speed measured on the fixes. Four changes, one at a time.

  pitch   once the sun is inside 0.75 m, hold head_pitch at -8 deg for the rest of the approach
  marker  a 40 mm card on the wall, centred 350 mm up, also counts as a target
  wide    Camera Module 3 Wide field (102 deg up-down, 67 deg left-right on this head)
  turn    before the calibrated turn, look down (neck -12, head -19) and creep if the sun is seen

The cute sit is the nest sit: torque off, head in the sit pose. This file does not
change that path.

  PYTHONDONTWRITEBYTECODE=1 python3 close_run.py MODE N_PER_CELL [seed]
MODE is pitch, marker, wide, turn, or base. base is the blind walk-in again, for a check.
NEST_SCRATCH and ODM_PLAYGROUND are the same variables the nest sim uses.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
NEST = os.path.abspath(os.path.join(HERE, "..", "nest", "sim"))
sys.path.insert(0, os.path.join(NEST, "v3"))
sys.path.insert(0, os.path.join(NEST, "v2"))
sys.path.insert(0, NEST)

import mujoco  # noqa: E402
import nest_run as NR  # noqa: E402
import nest_run_v2 as R2  # noqa: E402
import nest_run_v3 as V3  # noqa: E402
import nestlib as NL  # noqa: E402

D = np.radians
# Camera Module 3 standard, installed with the 66 deg axis up-down (CAMERA_TWIN.md).
HX_STD, HY_STD = D(33.0), D(20.5)
# Camera Module 3 Wide, same board turned the same way: brief horizontal 102 deg is up-down,
# brief vertical 67 deg is left-right. Product brief RP-008151-DS-1, page 5, wide column.
HX_WIDE, HY_WIDE = D(51.0), D(33.5)
# software/servo_limits.json, head_pitch soft_lo. The sit model already uses this as ctrlrange.
# Two degrees inside the -22 deg software stop, so a 1 deg position overshoot stays inside it.
# The printed stop is -25 deg (servo_limits.json hard_lo). The playground range goes to -0.78 rad
# and is not used.
HEAD_SOFT_DEG = -8.0
# Stand-still look at the turn. Deeper than the walking pitch, still inside the -22 deg soft stop.
# Neck soft stop is -17 deg. -15 leaves room for overshoot. Head -18 is inside the -22 stop.
LOOK_NECK_DEG = -12.0
LOOK_DEG = -19.0
# 40 mm card centre. Wall: just room-side of the wall plane, at a height a walking head sees.
# Edge tab: room-side point of the outer felt (247 mm upper + 20 mm tread), standing 120 mm.
MARKER_Z = 0.350
CARD_MM = 40.0
RCAM = np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]])
PUPIL = 0.040
MI = NL.MI


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def look_deg(R):
    f = R[:, 2]
    return float(np.degrees(np.arctan2(f[2], np.hypot(f[0], f[1]))))


class CamEst:
    """Pose fixes while a target is in the field, then the measured walking speed.

    The noise while a target is in the field is the nest sim's noise schedule, not a
    measured detector. Same rule as the blind walk-in.
    """

    def __init__(self, run, hx, hy):
        sim = run.s
        sx, sy = NR.NOISE[run.cfg["noise"]]
        self.run = run
        self.s = sim
        self.hx, self.hy = hx, hy
        self.sig, self.sigy = sx, D(sy)
        self.T = 1.0 / run.rate
        self.lat = run.lat
        self.next = 0.0
        self.q = []
        self.got = []
        self.on = True
        self.cmd = (0.0, 0.0, 0.0)
        self.est = None
        self.scale = 1.0
        self.cmd_hist = []
        self.fix_hist = []
        self.ever = False
        self.fixes = 0
        self.edge_fixes = 0
        self.z_samples = []
        self.look_samples = []
        self.head_samples = []
        self.yaw_samples = []
        self.sun_tx_abs_min = None
        self.sun_ty_abs_min = None
        self.sun_behind = 0
        self.lost_range_m = None
        self.last_fix_range_m = None
        self.last_fix_kind = None
        self.last_look_deg = None
        self.last_head_deg = None
        self.last_neck_deg = None
        self.blind_steps = 0
        self.head = sim.model.body("head_assembly").id
        self.j_head = mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_JOINT, "head_pitch")
        self.j_neck = mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_JOINT, "neck_pitch")

    def pupil(self):
        dd = self.s.data
        Rh = dd.xmat[self.head].reshape(3, 3)
        R = Rh @ RCAM
        p = dd.xpos[self.head] + R[:, 2] * PUPIL
        return p, R

    def _in(self, d_world, R):
        d = R.T @ np.asarray(d_world, float)
        if d[2] <= 1e-6:
            return False
        tx = float(np.arctan2(d[0], d[2]))
        ty = float(np.arctan2(d[1], d[2]))
        return abs(tx) <= self.hx and abs(ty) <= self.hy

    def targets(self):
        mode = self.run.mode
        pts = [("sun", np.zeros(3))]
        if mode == "marker":
            pts.append(("wall", np.array([NL.WALL_X - 0.004, 0.0, MARKER_Z])))
        return pts

    def visible(self):
        p, R = self.pupil()
        hits = []
        sun_rng = float(np.hypot(p[0], p[1]))
        ds = R.T @ (-p)
        if ds[2] <= 1e-6:
            self.sun_behind += 1
        else:
            tx = abs(float(np.degrees(np.arctan2(ds[0], ds[2]))))
            ty = abs(float(np.degrees(np.arctan2(ds[1], ds[2]))))
            self.sun_tx_abs_min = tx if self.sun_tx_abs_min is None else min(self.sun_tx_abs_min, tx)
            self.sun_ty_abs_min = ty if self.sun_ty_abs_min is None else min(self.sun_ty_abs_min, ty)
        for name, pt in self.targets():
            d = np.asarray(pt, float) - p
            rng = float(np.hypot(d[0], d[1]))
            if name == "sun":
                sun_rng = rng
            if self._in(d, R):
                hits.append((name, rng))
        return hits, sun_rng, look_deg(R)

    def joint_deg(self, jid):
        return float(np.degrees(self.s.data.qpos[self.s.model.jnt_qposadr[jid]]))

    def tick(self):
        s = self.s
        dt = 0.02
        vx, vy, wz = self.cmd
        hits, sun_rng, look = self.visible()
        if self.s.k % 25 == 0:
            if len(self.z_samples) < 500:
                self.z_samples.append(float(self.pupil()[0][2]))
            if len(self.look_samples) < 500:
                self.look_samples.append(round(look, 1))
            if len(self.head_samples) < 500:
                self.head_samples.append(round(self.joint_deg(self.j_head), 1))
            if len(self.yaw_samples) < 500:
                self.yaw_samples.append(round(float(np.degrees(self.s.trunk_pose()[0][2])), 1))
        seen = len(hits) > 0
        sun_seen = any(h[0] == "sun" for h in hits)
        if seen:
            sun = [h for h in hits if h[0] == "sun"]
            rng, kind = (sun[0][1], "sun") if sun else (hits[0][1], hits[0][0])
        else:
            rng, kind = sun_rng, None
        self.cmd_hist.append((s.t, vx))
        if self.est is not None:
            use = vx
            if (not seen) and self.ever:
                use = vx * self.scale
            yaw = self.est[2]
            c, sn = np.cos(yaw), np.sin(yaw)
            self.est[0] += (c * use - sn * vy) * dt
            self.est[1] += (sn * use + c * vy) * dt
            self.est[2] = wrap(self.est[2] + wz * dt)
        if (not sun_seen) and self.ever and self.lost_range_m is None:
            self.lost_range_m = round(sun_rng, 3)
        if not seen and self.ever:
            self.blind_steps += 1
        if s.t >= self.next:
            self.next = s.t + self.T
            if self.on and seen:
                p, _, _ = s.trunk_pose()
                r = s.rng
                meas = np.array([
                    p[0] + r.normal(0, self.sig),
                    p[1] + r.normal(0, self.sig),
                    wrap(p[2] + r.normal(0, self.sigy)),
                ])
                self.q.append((s.t + self.lat, meas, rng, kind, look))
                self.fixes += 1
                if kind == "edge":
                    self.edge_fixes += 1
        while self.q and self.q[0][0] <= s.t:
            item = self.q.pop(0)
            meas = item[1]
            self.est = meas.copy()
            self.ever = True
            self.last_fix_range_m = round(item[2], 3)
            self.last_fix_kind = item[3]
            self.last_look_deg = round(item[4], 1)
            # Lower the head only after the sun is already in hand, inside 0.90 m, so the
            # search still uses the policy head. 0.90 m is inside the level field.
            if self.run.mode == "pitch" and item[3] == "sun" and item[2] < 0.75:
                self.run.pitch_flag[0] = True
            self.last_head_deg = round(self.joint_deg(self.j_head), 1)
            self.last_neck_deg = round(self.joint_deg(self.j_neck), 1)
            self.fix_hist.append((s.t, float(meas[0]), float(meas[1]), float(meas[2])))
            h = [v for v in self.fix_hist if s.t - v[0] <= 0.8]
            ch = [v for v in self.cmd_hist if s.t - v[0] <= 0.8 and abs(v[1]) > 0.05]
            if len(h) >= 2 and h[-1][0] - h[0][0] >= 0.3 and ch:
                dtv = h[-1][0] - h[0][0]
                yaw = h[-1][3]
                c, sn = np.cos(yaw), np.sin(yaw)
                fwd = c * (h[-1][1] - h[0][1]) + sn * (h[-1][2] - h[0][2])
                vcmd = float(np.mean([abs(v[1]) for v in ch]))
                if vcmd > 0.05 and dtv > 0:
                    self.scale = float(np.clip((fwd / dtv) / vcmd, 0.35, 1.15))
        if self.est is not None:
            e = self.est
            self.got.append((s.t, s.t, float(e[0]), float(e[1]), float(e[2])))

    def latest(self):
        if not self.got:
            return None
        return self.got[-1]

    def mean_since(self, t0):
        g = [m for m in self.got if m[1] >= t0]
        if not g:
            return None, 0
        g = np.array(g)
        yaw = np.arctan2(np.sin(g[:, 4]).mean(), np.cos(g[:, 4]).mean())
        return np.array([g[:, 2].mean(), g[:, 3].mean(), yaw]), len(g)

    def report(self):
        return dict(fixes=self.fixes, ever_seen=self.ever, sun_lost_range_m=self.lost_range_m,
                    last_fix_range_m=self.last_fix_range_m, last_fix_kind=self.last_fix_kind,
                    last_look_deg=self.last_look_deg, last_head_pitch_deg=self.last_head_deg,
                    last_neck_pitch_deg=self.last_neck_deg, blind_s=round(self.blind_steps * 0.02, 2),
                    speed_scale=round(self.scale, 3),
                    cam_z_m=None if not self.z_samples else round(float(np.median(self.z_samples)), 3),
                    look_deg_p50=None if not self.look_samples else round(float(np.median(self.look_samples)), 1),
                    look_deg_min=None if not self.look_samples else min(self.look_samples),
                    look_deg_max=None if not self.look_samples else max(self.look_samples),
                    head_pitch_deg_min=None if not self.head_samples else min(self.head_samples),
                    head_pitch_deg_max=None if not self.head_samples else max(self.head_samples),
                    yaw_deg_min=None if not self.yaw_samples else min(self.yaw_samples),
                    yaw_deg_max=None if not self.yaw_samples else max(self.yaw_samples),
                    sun_tx_abs_min_deg=None if self.sun_tx_abs_min is None else round(self.sun_tx_abs_min, 1),
                    sun_ty_abs_min_deg=None if self.sun_ty_abs_min is None else round(self.sun_ty_abs_min, 1),
                    sun_behind=self.sun_behind,
                    edge_fixes=self.edge_fixes)


def _bind(run):
    mode = run.mode
    hx, hy = (HX_WIDE, HY_WIDE) if mode == "wide" else (HX_STD, HY_STD)
    run.est = CamEst(run, hx, hy)
    _install_pitch(run)


def _install_pitch(run):
    """While pitch_flag is set, hold head_pitch on the soft stop. Otherwise the nest step is untouched."""
    sim = run.s
    original = sim.step
    names = ("neck_pitch", "head_pitch", "head_yaw", "head_roll")
    aids = [mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in names]
    if any(a < 0 for a in aids):
        raise RuntimeError("missing a head actuator")
    # neck 0, head pitch at the soft stop, yaw 0, roll 0. All inside software/servo_limits.json.
    # The neck is held at 0 because a positive neck cancels a negative head pitch (the sit uses that pair).
    flag = run.pitch_flag

    def step(cmd=(0, 0, 0)):
        if not flag[0]:
            return original(cmd)
        # Walking pitch holds head_pitch only, so the neck can keep the gait.
        # The turn look also holds the neck, yaw and roll at 0, so the neck does not cancel the pitch.
        if run.look_deep[0]:
            goals = [D(LOOK_NECK_DEG), D(LOOK_DEG), 0.0, 0.0]
        else:
            goals = [None, D(HEAD_SOFT_DEG), None, None]
        m = sim.m
        for _ in range(m.decimation):
            sim._phys()
        if sim.policy_on:
            # The walk command stays the nest's (head command 0). The servo target is what pitches the head.
            # Putting the angle in the command as well stops the policy turning onto the sun.
            m.commands = [float(cmd[0]), float(cmd[1]), float(cmd[2]), 0.0, 0.0, 0.0, 0.0]
            m.imitation_i = (m.imitation_i + m.phase_frequency_factor) % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(sim.data, m.commands)
            a = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = a.copy()
            old = m.prev_motor_targets.copy()
            m.motor_targets = m.default_actuator + a * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                lim = m.max_motor_velocity * (m.sim_dt * m.decimation)
                m.motor_targets = np.clip(m.motor_targets, old - lim, old + lim)
            else:
                lim = None
            for aid, goal0 in zip(aids, goals):
                if goal0 is None:
                    continue
                lo, hi = sim.model.actuator_ctrlrange[aid]
                goal = float(np.clip(goal0, lo, hi))
                if lim is not None:
                    goal = float(np.clip(goal, old[aid] - lim, old[aid] + lim))
                m.motor_targets[aid] = goal
            m.prev_motor_targets = m.motor_targets.copy()
            sim.data.ctrl = m.motor_targets.copy()
        sim._after()

    sim.step = step


def _look_before_turn(run):
    """Start of the turn: look down at the sun, creep if it is seen, then the calibrated turn.

    A tab on the mat edge is behind the camera once the duck has turned to face the room, so the
    re-sight is the sun, while the duck is still facing the wall. The head goes to the stand-still
    look, the body yaws a little so the narrow left-right field can cross the sun, then the head
    comes back up and the nest's own turn runs.
    """
    s = run.s
    run.look_deep[0] = True
    run.pitch_flag[0] = True
    run.est.on = True
    run.est.next = s.t
    before = run.est.fixes
    for _ in range(40):
        run.step((0, 0, 0))
        if run.est.fixes > before:
            break
    p, R = run.est.pupil()
    dcam = R.T @ (-p)
    run.extra["look_pupil_m"] = [round(float(v), 3) for v in p]
    run.extra["look_deg_now"] = round(look_deg(R), 1)
    run.extra["look_head_deg"] = round(run.est.joint_deg(run.est.j_head), 1)
    run.extra["look_neck_deg"] = round(run.est.joint_deg(run.est.j_neck), 1)
    run.extra["sun_range_m"] = round(float(np.hypot(p[0], p[1])), 3)
    if dcam[2] > 1e-6:
        run.extra["sun_deg"] = [round(float(np.degrees(np.arctan2(dcam[0], dcam[2]))), 1),
                                round(float(np.degrees(np.arctan2(dcam[1], dcam[2]))), 1)]
    else:
        run.extra["sun_deg"] = None
    if run.est.fixes == before and not s.fallen:
        # a short yaw each way, the beginning of the turn, head still down
        for wz, n in ((0.5, 25), (-0.5, 50), (0.5, 25)):
            for _ in range(n):
                run.step((0, 0, wz))
                if run.est.fixes > before or s.fallen:
                    break
            if run.est.fixes > before or s.fallen:
                break
    for _ in range(15):
        if s.fallen:
            break
        run.step((0, 0, 0))
    got = run.est.fixes > before and run.est.last_fix_kind == "sun"
    run.extra["resight"] = bool(got)
    run.extra["resight_look_deg"] = run.est.last_look_deg
    run.pitch_flag[0] = False
    run.look_deep[0] = False
    for _ in range(20):
        if s.fallen:
            break
        run.step((0, 0, 0))
    if got and not s.fallen:
        run.fine(lambda psi: (*run.turn_target(psi), 0.0), max_rounds=4, stage="resight")
    run.est.on = True


class Close6(NR.Run):
    def __init__(self, cfg):
        self.mode = cfg["mode"]
        self.pitch_flag = [False]
        self.look_deep = [False]
        self.resight_phase = [False]
        self.extra = {}
        super().__init__(cfg)
        _bind(self)

    def step(self, cmd):
        if not self.est.ever:
            cmd = (0.0, 0.0, 0.5)
        self.est.cmd = cmd
        NR.Run.step(self, cmd)

    def turn(self, psi_est):
        if self.mode == "pitch":
            self.pitch_flag[0] = False
        if self.mode == "turn" and not self.s.fallen:
            _look_before_turn(self)
            m = self.est.latest()
            if m is not None:
                psi_est = m[4]
        return NR.Run.turn(self, psi_est)


class Close7(R2.Run2):
    def __init__(self, cfg):
        self.mode = cfg["mode"]
        self.pitch_flag = [False]
        self.look_deep = [False]
        self.resight_phase = [False]
        self.extra = {}
        super().__init__(cfg)
        _bind(self)

    def step(self, cmd):
        if not self.est.ever:
            cmd = (0.0, 0.0, 0.5)
        self.est.cmd = cmd
        R2.Run2.step(self, cmd)

    def turn(self, psi_est):
        if self.mode == "pitch":
            self.pitch_flag[0] = False
        if self.mode == "turn" and not self.s.fallen:
            _look_before_turn(self)
            m = self.est.latest()
            if m is not None:
                psi_est = m[4]
        return R2.Run2.turn(self, psi_est)


def slim(out, extra):
    if "error" in out:
        return dict(cfg=out.get("cfg"), error=out["error"])
    sits = []
    for s in out.get("sits") or []:
        sits.append(dict(
            seat_xy=[round(float(v), 4) for v in s["seat_xy"]],
            fell=bool(s["fell"]),
            ok=bool(s["nest"]["ok"]),
        ))
    cfg = out["cfg"]
    return dict(
        cfg={k: cfg[k] for k in ("noise", "volt", "mu", "k", "seed")},
        fell=bool(out.get("fell")),
        fall_stage=out.get("fall_stage"),
        t_total_s=out.get("t_total_s"),
        sits=sits,
        camera=out.get("camera"),
        extra=extra,
    )


def job(cfg):
    V3.world_from_cfg(cfg)
    try:
        run = Close6(cfg) if cfg["volt"] < 6.6 else Close7(cfg)
        if cfg["volt"] >= 6.6 and cfg.get("aim_mm"):
            run.p = dict(run.p, **{"aim_left": {"6.0": 0.0, "7.2": -float(cfg["aim_mm"]) / 1000.0}})
        out = run.go()
        out["camera"] = run.est.report()
        return slim(out, run.extra)
    except Exception as e:
        import traceback
        return dict(cfg={k: cfg[k] for k in ("noise", "volt", "mu", "k", "seed", "mode")},
                    error=repr(e), tb=traceback.format_exc())


def configs(n, mode, wall_x, aim_mm, only_seed):
    J = []
    for c in NR.configs(n):
        if only_seed is not None and c["seed"] != only_seed:
            continue
        c = dict(c)
        c["mode"] = mode
        c["edge"] = "steps"
        c["wall_x"] = wall_x
        c["aim_mm"] = aim_mm
        c["trace"] = False
        J.append(c)
    return J


def main():
    mode = sys.argv[1]
    n = int(sys.argv[2])
    only = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if mode not in ("base", "pitch", "marker", "wide", "turn"):
        raise SystemExit("mode must be base, pitch, marker, wide, or turn")
    wall_x = 0.190
    aim_mm = 20.0
    os.environ["NEST_EDGE"] = "steps"
    os.environ["NEST_WALL_X"] = "0.190"
    J = configs(n, mode, wall_x, aim_mm, only)
    t = time.time()
    R = []
    jobs = int(os.environ.get("JOBS", "4"))
    with Pool(jobs, maxtasksperchild=4) as p:
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=1)):
            R.append(r)
            if r.get("error"):
                print("ERR", r.get("cfg"), r["error"], flush=True)
                if r.get("tb"):
                    print(r["tb"], flush=True)
            if (i + 1) % 20 == 0 or (i + 1) == len(J):
                print(mode, i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: r.get("cfg", {}).get("seed", 0))
    doc = dict(
        label="sim pass only",
        mode=mode,
        wall_x_m=wall_x,
        aim_mm_right_at_7v2=aim_mm,
        edge="steps",
        head_soft_deg=HEAD_SOFT_DEG,
        marker_z_m=MARKER_Z,
        card_mm=CARD_MM,
        head_pitch_deg=HEAD_SOFT_DEG,
        look_deg=LOOK_DEG,
        field="wide 102 by 67" if mode == "wide" else "standard 66 by 41",
        note="Approved sun distance 190 mm. Detector noise is the nest schedule, not a measured camera. The cute sit is unchanged.",
        runs=R,
    )
    path = os.path.join(HERE, "close_%s.json" % mode)
    json.dump(doc, open(path, "w"))
    print("wrote", len(R), path, "%.0f s" % (time.time() - t))


if __name__ == "__main__":
    main()
