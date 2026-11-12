#!/usr/bin/env python3
"""nest_run.py: the full "go to the nest" sequence, Monte Carlo. sim pass only.

One run: start 1.0 to 1.5 m from the wall (+/-0.3 m sideways, +/-30 deg) -> approach -> walk on to the turn spot -> fine
moves -> turn 180 deg on the spot (left, IMU yaw) -> stop, settle -> SIT.md sit -> torque off -> score the 4 belly pins on the
nest zones and on the pond rug zones -> if no contact: stand, shuffle, sit again (up to 3 sits) -> stand up, walk straight out.

Perception is NOT simulated. Stand-in: true trunk pose (x, y, yaw) + Gaussian noise, sampled at 5 to 10 Hz (drawn per run),
delivered 70 to 170 ms late (drawn per run; the off-board path of PERCEPTION_STUDY.md). It is used in the approach, the fine
moves and before a re-sit. During the turn only the simulated IMU yaw is used. Nothing is sensed between the turn start and the
first sit.

  PYTHONDONTWRITEBYTECODE=1 python3 nest_run.py N_PER_CELL [tag]    N_PER_CELL runs for each noise level x voltage x mat friction
Writes nest_runs_<tag>.json (every run) next to this file.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestlib as N  # noqa: E402

D = np.radians
NOISE = {"low": (0.005, 1.0), "mid": (0.015, 3.0), "high": (0.030, 6.0)}      # 1 sigma: m per axis, deg
VOLTS = (6.0, 7.2)
MUS = (0.6, 0.8, 1.0)
CT = json.load(open(os.path.join(HERE, "calib_turn.json")))["summary"]
# the repeatable shift from "standing at the turn start" to "seat pins after torque off", in the heading frame at the turn start
# (left turn, command +1.0), per bus voltage: calib_turn.json. The duck can read its bus voltage from the servos.
SHIFT = {v: (CT["+1 V%.1f" % v]["seat_fwd_mm"]["mean"] / 1000, CT["+1 V%.1f" % v]["seat_left_mm"]["mean"] / 1000) for v in VOLTS}
COAST = {v: D(CT["+1 V%.1f" % v]["yaw_coast_deg"]["mean"]) for v in VOLTS}       # yaw gained after the turn command ends
SIT_SHIFT = (CT["+1 all"]["sit_shift_fwd_mm"]["mean"] / 1000, CT["+1 all"]["sit_shift_left_mm"]["mean"] / 1000)   # standing trunk -> seat pins
TURN_WZ = 1.0
TOL_XY, TOL_BACK, TOL_LEFT, TOL_YAW = 0.010, 0.015, 0.012, D(8.0)
BIAS_RIGHT = 0.020              # the walk-in aims 20 mm right of the line: the stock walk can side-step left only
LEAD = 0.040                    # stop the walk-in 40 mm short (coast and latency), then creep forward
BP = json.load(open(os.path.join(HERE, "burst_probe.json")))["summary"]
GYRO_BIAS_SD, GYRO_SCALE_SD = D(0.2), 0.01                                     # est: rad/s, fraction
RUG_AIM_SHIFT = 0.0142          # rug aim 204.2 mm from the wall (coverage.json, yaw 20 row) against 190 mm for the sun


def interp(tab, v):
    a, b = VOLTS
    w = (v - a) / (b - a)
    return np.array(tab[a]) * (1 - w) + np.array(tab[b]) * w


def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


class Est:
    """the perception stand-in: truth + noise at a fixed rate, delivered late"""

    def __init__(self, sim, sig_xy, sig_yaw_deg, rate, lat):
        self.s, self.sig, self.sigy, self.T, self.lat = sim, sig_xy, D(sig_yaw_deg), 1.0 / rate, lat
        self.next = 0.0
        self.q = []          # (deliver_t, capture_t, x, y, yaw)
        self.got = []        # delivered
        self.on = True

    def tick(self):
        s = self.s
        if s.t >= self.next:
            self.next = s.t + self.T
            if self.on:
                p, _, _ = s.trunk_pose()
                r = s.rng
                self.q.append((s.t + self.lat, s.t, p[0] + r.normal(0, self.sig), p[1] + r.normal(0, self.sig), p[2] + r.normal(0, self.sigy)))
        while self.q and self.q[0][0] <= s.t:
            self.got.append(self.q.pop(0))

    def latest(self):
        return self.got[-1] if self.got else None

    def mean_since(self, t0):
        g = [m for m in self.got if m[1] >= t0]
        if not g:
            return None, 0
        g = np.array(g)
        return np.array([g[:, 2].mean(), g[:, 3].mean(), np.arctan2(np.sin(g[:, 4]).mean(), np.cos(g[:, 4]).mean())]), len(g)


class Run:
    def __init__(self, cfg):
        self.cfg = cfg
        rng = np.random.default_rng(cfg["seed"])
        self.start = dict(x=N.WALL_X - rng.uniform(1.0, 1.5), y=rng.uniform(-0.3, 0.3), yaw=D(rng.uniform(-30, 30)))
        self.mu_floor = float(rng.uniform(0.5, 1.0))
        self.rate, self.lat = float(rng.uniform(5, 10)), float(rng.uniform(0.07, 0.17))
        s = self.s = N.Sim(seed=cfg["seed"], x0=self.start["x"], y0=self.start["y"], yaw0=self.start["yaw"], mu_mat=cfg["mu"], mu_floor=self.mu_floor,
                           volt=cfg["volt"], pins_on=cfg.get("pins", True), record=cfg.get("record"), mat=cfg.get("mat", True))
        s.gyro_bias = float(rng.normal(0, GYRO_BIAS_SD))
        s.gyro_scale = 1.0 + float(rng.normal(0, GYRO_SCALE_SD))
        sx, sy = NOISE[cfg["noise"]]
        self.est = Est(s, sx, sy, self.rate, self.lat)
        self.shift = interp(SHIFT, cfg["volt"])
        self.coast = float(interp(COAST, cfg["volt"]))
        self.moves = []
        self.out = dict(cfg={k: v for k, v in cfg.items() if k != "record"}, start=self.start, mu_floor=round(self.mu_floor, 3), rate_hz=round(self.rate, 2),
                        latency_s=round(self.lat, 3), stages={}, sits=[])

    # ------------------------------------------------------------ low level
    def step(self, cmd):
        self.s.step(cmd)
        self.est.tick()

    def stage(self, name):
        self.s.stage = name
        self.out["stages"].setdefault(name, 0.0)
        self._t0 = self.s.t

    def end_stage(self):
        self.out["stages"][self.s.stage] += self.s.t - self._t0

    def dwell(self, T=1.0):
        """stand still (zero command) and average the pose stand-in over the last T - 0.4 s"""
        t0 = self.s.t
        n = int(round(T / 0.02))
        for _ in range(n):
            self.step((0, 0, 0))
        for _ in range(int(self.lat / 0.02) + 2):
            self.step((0, 0, 0))
        m, k = self.est.mean_since(t0 + 0.4)
        if m is None:
            m, k = self.est.mean_since(t0)
        return m

    def burst_steps(self, name, want, col):
        """control steps of command `name` that move `want` (mm or deg, column col of burst_probe.json: 0 forward, 1 left,
        2 yaw) at this bus voltage: the measured mean table, linear in steps and in voltage; None if out of reach in 60 steps"""
        tab = {}
        for r in BP:
            if r["cmd"] == name:
                tab.setdefault(r["steps"], {})[r["volt"]] = r[("fwd_mm", "left_mm", "yaw_deg")[col]][0]
        ns = sorted(tab)
        w = (self.cfg["volt"] - VOLTS[0]) / (VOLTS[1] - VOLTS[0])
        d = [abs(tab[n][VOLTS[0]] * (1 - w) + tab[n][VOLTS[1]] * w) for n in ns]
        for i in range(1, len(ns)):
            if d[i] >= want and d[i] > d[i - 1]:
                f = np.clip((want - d[i - 1]) / (d[i] - d[i - 1]), 0, 1)
                return int(round(ns[i - 1] + f * (ns[i] - ns[i - 1])))
        return ns[-1]

    def burst(self, ex, ey, eyaw):
        """one open-loop creep move, then look again. Only the moves the stock walk can make (burst_probe.json):
        forward at 0.15 or 0.10, back at -0.15 (slow), left at +0.20, yaw at +/-0.6. There is no right side-step."""
        if abs(eyaw) > 0:
            name = "yaw +0.6" if eyaw > 0 else "yaw -0.6"
            n = self.burst_steps(name, abs(np.degrees(eyaw)), 2) if eyaw > 0 else 20
            cmd = (0, 0, 0.6 * np.sign(eyaw))
        elif ex > 0.025:
            n, cmd = self.burst_steps("fwd 0.15", ex * 1000, 0), (0.15, 0, 0)
        elif ex > TOL_XY:
            n, cmd = self.burst_steps("fwd 0.10", ex * 1000, 0), (0.10, 0, 0)
        elif ex < -TOL_BACK:
            n, cmd = self.burst_steps("back 0.15", -ex * 1000, 0), (-0.15, 0, 0)
        elif ey > TOL_LEFT:
            n, cmd = self.burst_steps("left 0.20", ey * 1000, 1), (0, 0.20, 0)
        else:
            return False
        for _ in range(n):
            self.step(cmd)
        self.moves.append((cmd, n))
        return True

    # ------------------------------------------------------------ the sequence
    def turn_target(self, psi):
        """where the trunk must stand, heading psi, so the seat pins land on the sun centre after the turn and the sit"""
        return -rot(psi) @ self.shift

    def approach(self):
        s = self.s
        self.stage("approach")
        PT = self.turn_target(0.0)
        W1 = PT + np.array([-0.40, -BIAS_RIGHT])
        phase = 0
        filt = None
        t_start = s.t
        t_in = t_out = None
        while s.t - t_start < 60 and not s.fallen:
            pt, _, _ = s.trunk_pose()
            rr = float(np.hypot(pt[0], pt[1]))
            if t_in is None and rr < 0.33:
                t_in = s.t
            if t_in is not None and t_out is None and rr < 0.17:
                t_out = s.t
                self.out["edge_cross_s"] = round(t_out - t_in, 2)      # 160 mm of travel across the mat edge
            m = self.est.latest()
            if m is None:
                self.step((0, 0, 0))
                continue
            z = np.array(m[2:5])
            if filt is None or m[1] != filt[1]:
                if filt is None:
                    f = z
                else:
                    f = filt[0] + 0.6 * (z - filt[0])
                    f[2] = filt[0][2] + 0.6 * N.wrap(z[2] - filt[0][2])
                filt = (f, m[1])
            x, y, yaw = filt[0]
            if phase == 0:
                d = W1 - np.array([x, y])
                dist = np.hypot(*d)
                if dist < 0.10 or x > W1[0]:
                    phase = 1
                    self.end_stage()
                    self.stage("walk_on")
                    continue
                yd = np.arctan2(d[1], d[0])
                e = N.wrap(yd - yaw)
                wz = float(np.clip(1.5 * e, -0.8, 0.8))
                vx = 0.15 if abs(e) < D(35) else 0.0
                self.step((vx, 0.0, wz))
            else:
                dist = PT[0] - x
                if dist < self.cfg.get("lead", LEAD):
                    break
                ey = PT[1] - BIAS_RIGHT - y
                yd = float(np.clip(np.arctan2(ey, max(dist, 0.20)), -D(25), D(25)))    # steer to the line right up to the stop
                wz = float(np.clip(1.5 * N.wrap(yd - yaw), -0.6, 0.6))
                self.step((0.15, 0.0, wz))
        self.end_stage()
        return not s.fallen and s.t - t_start < 60

    def fine(self, target_fn, max_rounds=6, stage="fine"):
        """stand, look (averaged), creep to the target pose; returns the last averaged estimate"""
        s = self.s
        self.stage(stage)
        rounds = 0
        while True:
            m = self.dwell(1.0)
            if s.fallen or m is None:
                break
            tx, ty, tyaw = target_fn(m[2])
            e = rot(-m[2]) @ (np.array([tx, ty]) - m[:2])
            eyaw = N.wrap(tyaw - m[2])
            if rounds >= max_rounds or not self.burst(e[0], e[1], eyaw if abs(eyaw) > TOL_YAW else 0.0):
                break
            rounds += 1
        self.end_stage()
        return m, rounds

    def turn(self, psi_est):
        s = self.s
        self.stage("turn")
        self.est.on = False                           # nothing is seen from here to the first sit
        s.imu_yaw = 0.0
        want = np.pi - psi_est - self.coast           # end heading pi
        n = 0
        while abs(s.imu_yaw) < want and n < 700 and not s.fallen:
            s.step((0, 0, TURN_WZ))
            n += 1
        self.end_stage()
        return n * 0.02

    def sit_and_score(self):
        s = self.s
        self.stage("settle")
        st = s.settle()
        self.end_stage()
        pre, _, _ = s.trunk_pose()
        self.stage("sit")
        s.sit_down(t_off=3.0)
        self.end_stage()
        self.stage("rest")
        acc, n = {}, 150
        for _ in range(n):
            s._phys()
            for k, v in s.contact_forces().items():
                acc[k] = acc.get(k, 0.0) + v / n
        s._after()
        self.end_stage()
        pins = s.pins()
        seat = np.mean([pins["seat_L"]["xy"], pins["seat_R"]["xy"]], 0)
        bump = np.mean([pins["bump_L"]["xy"], pins["bump_R"]["xy"]], 0)
        head = float(np.arctan2(bump[1] - seat[1], bump[0] - seat[0]))
        p, z, up = s.trunk_pose()
        rec = dict(t=round(s.t, 2), settle=st, pre_sit_trunk=[float(pre[0]), float(pre[1]), float(pre[2])], seat_xy=seat.tolist(), bump_xy=bump.tolist(), heading=head,
                   pins={k: dict(xy=[round(v["xy"][0], 4), round(v["xy"][1], 4)], F=round(v["F"], 3), comp_mm=round(v["comp"] * 1000, 2)) for k, v in pins.items()},
                   nest=N.score_nest(pins), rug=N.score_rug(pins), rug_own_aim=N.score_rug(pins, RUG_AIM_SHIFT),
                   nest_geom=N.score_nest(pins, need_force=False), contacts_N={k: round(v, 2) for k, v in acc.items() if v > 0.01},
                   stops=s.joints_on_stops(), surface=getattr(s, "sit_surface", ""), trunk_z_mm=round(z * 1000, 1), up=round(up, 4), fell=bool(s.fallen))
        self.out["sits"].append(rec)
        return rec

    def go(self):
        s, o = self.s, self.out
        t_wall = time.time()
        for _ in range(25):
            self.step((0, 0, 0))
        ok = self.approach()
        o["approach_ok"] = bool(ok)
        if ok:
            m, rounds = self.fine(lambda psi: (*self.turn_target(psi), 0.0))
            o["fine_rounds"] = rounds
        if ok and not s.fallen and m is not None:
            p0, _, _ = s.trunk_pose()
            o["pre_turn"] = dict(truth=[float(v) for v in p0], est=[float(v) for v in m], target=[float(v) for v in self.turn_target(p0[2])])
            o["turn_s"] = self.turn(m[2])
            o["imu_yaw_err_deg"] = float(np.degrees(N.wrap(s.imu_yaw - N.wrap(s.trunk_pose()[0][2] - p0[2]))))
        if ok and not s.fallen and m is not None:
            for k in range(3):
                rec = self.sit_and_score()
                if k == 0:
                    o["t_first_sit_s"] = round(s.t, 2)
                if s.fallen or rec["nest"]["ok"] or k == 2:
                    break
                # no contact: stand, look, shuffle so the seat pins would land on the sun, sit again
                self.stage("stand_up")
                s.stand_up()
                s.resume()
                self.end_stage()
                if s.fallen:
                    break
                self.est.on = True
                self.est.next = s.t

                def tgt(psi):
                    return (*(-rot(psi) @ np.array(SIT_SHIFT)), np.pi)
                self.fine(tgt, max_rounds=5, stage="shuffle")
                self.est.on = False
                if s.fallen:
                    break
            o["t_done_s"] = round(s.t, 2)
            o["n_sits"] = len(o["sits"])
            # walk-off: stand up from the sit and walk straight out
            if not s.fallen:
                self.stage("walk_off_stand")
                s.stand_up()
                s.resume()
                self.end_stage()
                p1, _, _ = s.trunk_pose()
                self.stage("walk_off")
                for _ in range(350):
                    s.step((0.15, 0, 0))
                self.end_stage()
                p2, _, _ = s.trunk_pose()
                o["walk_off"] = dict(stood=[float(v) for v in p1], end=[float(v) for v in p2], dist_m=float(np.hypot(*(p2[:2] - p1[:2]))),
                                     fell=bool(s.fallen), fall_stage=s.fall_stage)
        o["fell"] = bool(s.fallen)
        o["fall_stage"] = s.fall_stage
        o["fall_t"] = s.tfall
        if s.fallen:
            p, _, _ = s.trunk_pose()
            o["fall_xy"] = [float(p[0]), float(p[1])]
        o["events"] = s.events
        o["min_wall_clear_mm"] = [round(s.min_wall_clear[0] * 1000, 1), s.min_wall_clear[1], s.min_wall_clear[2]]
        o["min_rim_clear_mm"] = [round(s.min_rim_clear[0] * 1000, 1), s.min_rim_clear[1], s.min_rim_clear[2]]
        o["currents"] = s.current_report()
        o["moves"] = [[list(c), n] for c, n in self.moves]
        o["t_total_s"] = round(s.t, 2)
        o["wall_s"] = round(time.time() - t_wall, 1)
        if self.cfg.get("trace"):
            o["trace"] = s.trace
        return o


def job(cfg):
    try:
        return Run(cfg).go()
    except Exception as e:                        # a crashed run is reported, never dropped
        import traceback
        return dict(cfg=cfg, error=repr(e), tb=traceback.format_exc())


def configs(n):
    J = []
    for ni, noise in enumerate(NOISE):
        for vi, v in enumerate(VOLTS):
            for mi, mu in enumerate(MUS):
                for k in range(n):
                    J.append(dict(noise=noise, volt=v, mu=mu, k=k, seed=100000 * ni + 10000 * vi + 1000 * mi + k, trace=(k < 2)))
    return J


if __name__ == "__main__":
    n = int(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else "main"
    J = configs(n)
    if len(sys.argv) > 3:                         # k range a:b, to add runs later
        a, b = map(int, sys.argv[3].split(":"))
        J = [j for j in configs(b) if j["k"] >= a]
    t = time.time()
    R = []
    with Pool(int(os.environ.get("JOBS", "4")), maxtasksperchild=6) as p:      # a fresh worker every 6 runs (each run loads the model anew)
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=1)):
            R.append(r)
            if (i + 1) % 20 == 0:
                print(i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: r["cfg"]["seed"])
    json.dump(dict(label="sim pass only", noise_levels=NOISE, shift=dict((str(k), list(v)) for k, v in SHIFT.items()), sit_shift=SIT_SHIFT,
                   coast_deg={str(k): float(np.degrees(v)) for k, v in COAST.items()}, runs=R),
              open(os.path.join(HERE, "nest_runs_%s.json" % tag), "w"))
    print("wrote", len(R), "runs", "%.0f s" % (time.time() - t))
