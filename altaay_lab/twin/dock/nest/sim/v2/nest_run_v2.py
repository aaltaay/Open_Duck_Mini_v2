#!/usr/bin/env python3
"""nest_run_v2.py: "line up before the mat, then cross the edge straight". sim pass only.

Same world, same seeds, same start poses, same pose stand-in, same fine moves, turn, sit, re-sit and walk-off as ../nest_run.py
(imported, not changed). Only the walk-in is new:

  approach   steer (as before) to a run-up point on the line, then along the line to the staging point. All on the floor.
  stage      stand at the staging point, toes `stage_d` before the mat edge. Look (pose stand-in averaged), turn on the spot
             until the heading points at the turn spot within `tol_yaw`. No walking forward here.
  cross      forward command only, turn command 0, lateral command 0, until the pose stand-in says both heels are
             `feet_margin` inside the mat. A stall (no progress) triggers the retry rule.
  walk_on    what is left of the old steered walk-on, now wholly on the mat (usually a few cm or nothing).
  fine       unchanged: stand, look, creep moves on the mat. Then the turn.

  PYTHONDONTWRITEBYTECODE=1 python3 nest_run_v2.py N_PER_CELL [tag]      -> nest_runs_<tag>.json in this folder
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
import v2lib as L  # noqa: E402
import nest_run as NR  # noqa: E402   (the original, from the parent folder)

N = L.N
D = np.radians
rot = NR.rot

# the chosen values (see NEST_SIM_V2.md for the sweep). A run's cfg["v2"] overrides any of them.
P = dict(
    stage_d=0.030,        # m, toes this far before the mat edge at the staging point (plus stage_lead, minus the coast)
    runup=0.30,           # m, the run-up point on the line before the staging point
    stage_lead=0.030,     # m, the walk to the staging point stops this short (coast and latency)
    stage_dwell=1.0,      # s per look at the staging point
    stage_rounds=5,       # at most this many turn-on-the-spot moves at the staging point
    tol_yaw=4.0,          # deg, heading tolerance at the staging point
    max_aim=12.0,         # deg, beyond this a left side-step is tried first (there is no right side-step)
    min_gap=0.015,        # m, if the toes are closer to the edge than this at the staging point: step back first
    max_gap=9.0,          # m, if the toes are further from the edge than this at the staging point: creep forward first
    gap_goal=0.045,       # m, the toe gap that creep aims for
    aim_left={"6.0": 0.0, "7.2": 0.0},     # m, shift of the aim point to the left, per bus voltage (negative = right: drift allowance)
    fine_rounds=6,        # most fine moves on the mat before the turn (the original: 6)
    vx_cross={"6.0": 0.18, "7.2": 0.15},   # forward command while crossing, per bus voltage
    retry={"6.0": "none", "7.2": "none"},   # per bus voltage: none / pause / back / boost / wiggle / turnonly
    wz_retry=0.6,
    vx_retry=0.20,
    stall_T=1.5,          # s, stall check window
    stall_d=0.020,        # m, a stall = less progress than this between two windows (pose stand-in)
    feet_margin=0.020,    # m, both heels this far inside the mat outline (by the pose stand-in) ends the straight crossing
    cross_timeout=40.0,   # s
)


class Run2(NR.Run):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.p = dict(P, **cfg.get("v2", {}))
        self.filt = None
        self.viol = {}            # stage -> control steps with a turn or lateral command while a sole was on the edge (truth)
        self.edge_t = [None, None, 0.0]

    # ------------------------------------------------------------ low level
    def step(self, cmd):
        s = self.s
        if cmd[1] != 0 or cmd[2] != 0:
            if "edge" in L.feet_state(s):
                self.viol[s.stage] = self.viol.get(s.stage, 0) + 1
        # the same 160 mm window as the original (trunk 330 to 170 mm from the sun centre); standing at the staging
        # point is not counted
        pt, _, _ = s.trunk_pose()
        rr = float(np.hypot(pt[0], pt[1]))
        e = self.edge_t
        if e[0] is None and rr < 0.33:
            e[0] = s.t
        if e[0] is not None and e[1] is None:
            if s.stage == "stage":
                e[2] += 0.02
            if rr < 0.17:
                e[1] = s.t
                self.out["edge_cross_s"] = round(e[1] - e[0] - e[2], 2)
                self.out["edge_cross_incl_staging_s"] = round(e[1] - e[0], 2)
        super().step(cmd)

    def pose(self):
        """the walking filter of the original approach: 0.6 gain on each new sample of the pose stand-in"""
        m = self.est.latest()
        if m is None:
            return None
        z = np.array(m[2:5])
        if self.filt is None or m[1] != self.filt[1]:
            if self.filt is None:
                f = z
            else:
                f = self.filt[0] + 0.6 * (z - self.filt[0])
                f[2] = self.filt[0][2] + 0.6 * N.wrap(z[2] - self.filt[0][2])
            self.filt = (f, m[1])
        return self.filt[0]

    def truth(self):
        s = self.s
        P_ = np.vstack(L.sole_points(s))
        r = np.hypot(P_[:, 0], P_[:, 1]) - N.MAT_R
        return dict(pose=[float(v) for v in s.trunk_pose()[0]], feet=L.feet_state(s),
                    toe_to_edge_mm=round(float(r.min()) * 1000, 1),        # > 0: the foremost sole point is still off the mat
                    heel_inside_mm=round(float(-r.max()) * 1000, 1))       # > 0: the rearmost sole point is on the mat

    # ------------------------------------------------------------ the new walk-in
    def approach(self):
        s, p, o = self.s, self.p, self.out
        self.stage("approach")
        PT = self.turn_target(0.0)
        yline = PT[1] - NR.BIAS_RIGHT
        xs = L.edge_x(yline) - L.TOE - p["stage_d"]
        W1 = np.array([xs - p["runup"], yline])
        phase = 0
        t_start = s.t
        while s.t - t_start < 60 and not s.fallen:
            f = self.pose()
            if f is None:
                self.step((0, 0, 0))
                continue
            x, y, yaw = f
            if phase == 0:
                d = W1 - np.array([x, y])
                if np.hypot(*d) < 0.10 or x > W1[0]:
                    phase = 1
                    continue
                e = N.wrap(np.arctan2(d[1], d[0]) - yaw)
                self.step((0.15 if abs(e) < D(35) else 0.0, 0.0, float(np.clip(1.5 * e, -0.8, 0.8))))
            else:
                dist = xs - x
                if dist < p["stage_lead"]:
                    break
                yd = float(np.clip(np.arctan2(yline - y, max(dist, 0.20)), -D(25), D(25)))
                self.step((0.15, 0.0, float(np.clip(1.5 * N.wrap(yd - yaw), -0.6, 0.6))))
        self.end_stage()
        if s.fallen or s.t - t_start >= 60:
            return False

        # ---- staging: stand, look, turn on the spot until the heading points at the turn spot
        self.stage("stage")
        rounds, m, eyaw, psi = 0, None, 0.0, 0.0
        aim_left = float(NR.interp({v: p["aim_left"]["%.1f" % v] for v in NR.VOLTS}, self.cfg["volt"]))
        log = []
        while True:
            m = self.dwell(p["stage_dwell"])
            if s.fallen or m is None:
                break
            psi = 0.0
            for _ in range(2):                                      # the turn spot depends a little on the arrival heading
                tgt = self.turn_target(psi) + rot(psi) @ np.array([-NR.LEAD, -NR.BIAS_RIGHT + aim_left])
                dv = tgt - m[:2]
                psi = float(np.arctan2(dv[1], dv[0]))
            eyaw = float(N.wrap(psi - m[2]))
            gap = L.edge_x(m[1]) - (m[0] + L.TOE)                    # toes to the edge, by the pose stand-in
            log.append([round(float(np.degrees(psi)), 2), round(float(np.degrees(eyaw)), 2), round(float(gap) * 1000, 1)])
            if rounds >= p["stage_rounds"]:
                break
            n0 = len(self.moves)
            if gap < p["min_gap"]:
                self.burst(min(-0.016, gap - p["stage_d"]), 0.0, 0.0)
            elif gap > p["max_gap"]:
                self.burst(max(gap - p["gap_goal"], NR.TOL_XY + 0.001), 0.0, 0.0)
            elif psi > D(p["max_aim"]) and dv[1] > 0.03:
                self.burst(0.0, float(dv[1]) * 0.5, 0.0)
            elif abs(eyaw) > D(p["tol_yaw"]):
                self.burst(0.0, 0.0, eyaw)
            if len(self.moves) == n0:
                break
            rounds += 1
        self.end_stage()
        o["stage"] = dict(rounds=rounds, log=log, est=None if m is None else [float(v) for v in m], aim_deg=round(float(np.degrees(psi)), 2),
                          yaw_err_left_deg=round(float(np.degrees(eyaw)), 2), **self.truth())
        if s.fallen or m is None:
            return False

        # ---- cross: forward only, until both feet are wholly on the mat (by the pose stand-in)
        self.stage("cross")
        vx0 = float(NR.interp({v: p["vx_cross"]["%.1f" % v] for v in NR.VOLTS}, self.cfg["volt"]))
        vx = vx0
        hd = np.array([np.cos(m[2]), np.sin(m[2])])
        t0 = s.t
        mode, t_mode, t_chk = "go", s.t, s.t
        retry = p["retry"]["6.0" if self.cfg["volt"] < 6.6 else "7.2"]
        retries = 0
        t_touch = t_on = None
        done = False
        while s.t - t0 < p["cross_timeout"] and not s.fallen:
            f = self.pose()
            if L.feet_on_by_pose(f[0], f[1], f[2], p["feet_margin"]):
                done = True
                break
            if mode == "go":
                cmd = (vx, 0.0, 0.0)
            elif mode == "pause":
                cmd = (0.0, 0.0, 0.0)
                if s.t - t_mode > 1.0:
                    mode, t_mode, t_chk = "go", s.t, s.t
            elif mode in ("wiggle", "turnonly"):                     # a turn command for 1 s, the sign alternates (breaks the zero-turn rule)
                sg = 1 if retries % 2 else -1
                cmd = (vx if mode == "wiggle" else 0.0, 0.0, sg * p["wz_retry"])
                if s.t - t_mode > 1.0:
                    mode, t_mode, t_chk = "go", s.t, s.t
            else:                                                   # back
                cmd = (-0.15, 0.0, 0.0) if s.t - t_mode < 1.5 else (0.0, 0.0, 0.0)
                if s.t - t_mode > 2.0:
                    mode, t_mode, t_chk = "go", s.t, s.t
            self.step(cmd)
            fs = L.feet_state(s, 0.005)
            if t_touch is None and fs != ["off", "off"]:
                t_touch = s.t
            if t_on is None and fs == ["on", "on"]:
                t_on = s.t
            T = p["stall_T"]
            if mode == "go" and retry != "none" and s.t - t_chk >= 2 * T + self.lat:
                a = [g for g in self.est.got if s.t - 2 * T - self.lat <= g[1] < s.t - T - self.lat]
                b = [g for g in self.est.got if g[1] >= s.t - T - self.lat]
                if a and b:
                    prog = float((np.mean([g[2:4] for g in b], 0) - np.mean([g[2:4] for g in a], 0)) @ hd)
                    if prog < p["stall_d"]:
                        retries += 1
                        if retry == "boost":
                            vx = p["vx_retry"]
                        else:
                            mode, t_mode = retry, s.t
                t_chk = s.t - T
        self.end_stage()
        o["cross"] = dict(done=done, s=round(s.t - t0, 2), retries=retries, vx=vx0, truth_first_touch_to_both_on_s=(round(t_on - t_touch, 2) if (t_on and t_touch) else None),
                          **self.truth())
        if s.fallen or not done:
            return False

        # ---- what is left of the steered walk-on, now on the mat (the original law, unchanged)
        self.stage("walk_on")
        t1 = s.t
        while s.t - t1 < 20 and not s.fallen:
            x, y, yaw = self.pose()
            dist = PT[0] - x
            if dist < self.cfg.get("lead", NR.LEAD):
                break
            yd = float(np.clip(np.arctan2(yline - y, max(dist, 0.20)), -D(25), D(25)))
            self.step((0.15, 0.0, float(np.clip(1.5 * N.wrap(yd - yaw), -0.6, 0.6))))
        self.end_stage()
        return not s.fallen

    # ------------------------------------------------------------ the sequence (as the original go(), with the new records)
    def go(self):
        s, o = self.s, self.out
        t_wall = time.time()
        m = None
        for _ in range(25):
            self.step((0, 0, 0))
        ok = self.approach()
        o["approach_ok"] = bool(ok)
        if ok:
            o["on_mat"] = self.truth()
            m, rounds = self.fine(lambda psi: (*self.turn_target(psi), 0.0), max_rounds=self.p["fine_rounds"])
            o["fine_rounds"] = rounds
        if ok and not s.fallen and m is not None:
            p0, _, _ = s.trunk_pose()
            o["pre_turn"] = dict(truth=[float(v) for v in p0], est=[float(v) for v in m], target=[float(v) for v in self.turn_target(p0[2])], feet=L.feet_state(s))
        if ok and not s.fallen and m is not None and self.cfg.get("stop_after") != "fine":
            o["turn_s"] = self.turn(m[2])
            o["imu_yaw_err_deg"] = float(np.degrees(N.wrap(s.imu_yaw - N.wrap(s.trunk_pose()[0][2] - p0[2]))))
            for k in range(3):
                rec = self.sit_and_score()
                if k == 0:
                    o["t_first_sit_s"] = round(s.t, 2)
                if s.fallen or rec["nest"]["ok"] or k == 2:
                    break
                self.stage("stand_up")
                s.stand_up()
                s.resume()
                self.end_stage()
                if s.fallen:
                    break
                self.est.on = True
                self.est.next = s.t

                def tgt(psi):
                    return (*(-rot(psi) @ np.array(NR.SIT_SHIFT)), np.pi)
                self.fine(tgt, max_rounds=5, stage="shuffle")
                self.est.on = False
                if s.fallen:
                    break
            o["t_done_s"] = round(s.t, 2)
            o["n_sits"] = len(o["sits"])
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
        o["steer_on_edge_steps"] = self.viol
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
        return Run2(cfg).go()
    except Exception as e:                        # a crashed run is reported, never dropped
        import traceback
        return dict(cfg=cfg, error=repr(e), tb=traceback.format_exc())


def run_all(J, path, extra=None):
    t = time.time()
    R = []
    with Pool(int(os.environ.get("JOBS", "4")), maxtasksperchild=6) as p:
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=1)):
            R.append(r)
            if (i + 1) % 20 == 0:
                print(i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: (json.dumps(r["cfg"].get("v2", {}), sort_keys=True), r["cfg"]["seed"]))
    json.dump(dict(label="sim pass only", controller="v2: line up before the mat, cross the edge straight", params=P, noise_levels=NR.NOISE,
                   shift=dict((str(k), list(v)) for k, v in NR.SHIFT.items()), sit_shift=NR.SIT_SHIFT,
                   coast_deg={str(k): float(np.degrees(v)) for k, v in NR.COAST.items()}, **(extra or {}), runs=R), open(path, "w"))
    print("wrote", len(R), "runs", "%.0f s" % (time.time() - t))
    return R


if __name__ == "__main__":
    n = int(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else "v2"
    run_all(NR.configs(n), os.path.join(HERE, "nest_runs_%s.json" % tag))      # the same seeds and cells as the original
