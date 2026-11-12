#!/usr/bin/env python3
"""blind_run.py: nest walk-in using only the camera field, then dead reckoning. sim pass only.

The pose stand-in in the nest sim is not used. While the sun centre is inside the Camera Module 3
field (66 deg up-down, 41 deg left-right, on the head, CAMERA_TWIN.md), the controller gets the true
trunk pose plus the run's noise, late, at the run's rate. That noise is a stand-in for a detector.
The camera twin has no detector. When the sun centre leaves the field, updates stop. The estimate
then moves with the walk command (forward and sideways in the estimated heading, yaw from the yaw
command). The real gait does not match that command. That gap is the dead-reckoning error.

The walk law is the mixed one from nest sim v3: old steering at 6.0 V, straight crossing at 7.2 V,
two 1 mm steps, aim 20 mm right at 7.2 V. Before the first time the sun is seen, the duck turns in
place so the field can sweep onto it.

  PYTHONDONTWRITEBYTECODE=1 python3 blind_run.py N_PER_CELL [tag]
NEST_WALL_X defaults to 0.190. Set 0.215 for the study. The approved distance stays 0.190.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
NEST = os.path.join(HERE, "..", "nest", "sim")
sys.path.insert(0, os.path.join(NEST, "v3"))
sys.path.insert(0, os.path.join(NEST, "v2"))
sys.path.insert(0, NEST)

import nest_run as NR  # noqa: E402
import nest_run_v2 as R2  # noqa: E402
import nest_run_v3 as V3  # noqa: E402

N = NR.N
D = np.radians
# Camera Module 3 on this head: 66 deg up-down, 41 deg left-right (CAMERA_TWIN.md, cited brief).
HX = D(33.0)
HY = D(20.5)
# camera axes in the head frame at the home key (head Z points back, head X points up):
# camera Z forward, camera X down, camera Y to the duck's left.
RCAM = np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]])
# pupil, metres in front of the head body origin along the lens axis. The measured opening is on the
# tall zero pose (CAMERA_TWIN.md). This walk uses the head body. 40 mm is the front of that body.
PUPIL = 0.040


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def in_field(d_world, R):
    """sun vector in the camera frame. Same test as camera_cone.in_fov."""
    d = R.T @ np.asarray(d_world, float)
    if d[2] <= 1e-6:
        return False
    tx = float(np.arctan2(d[0], d[2]))
    ty = float(np.arctan2(d[1], d[2]))
    return abs(tx) <= HX and abs(ty) <= HY


class CamEst:
    def __init__(self, sim, sig_xy, sig_yaw, rate, lat):
        self.s = sim
        self.sig = sig_xy
        self.sigy = sig_yaw
        self.T = 1.0 / rate
        self.lat = lat
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
        self.lost_range_m = None
        self.last_fix_range_m = None
        self.blind_steps = 0
        self.head = sim.model.body("head_assembly").id

    def pupil(self):
        dd = self.s.data
        Rh = dd.xmat[self.head].reshape(3, 3)
        R = Rh @ RCAM
        p = dd.xpos[self.head] + R[:, 2] * PUPIL
        return p, R

    def sun_seen(self):
        p, R = self.pupil()
        d = -p  # sun centre is the origin, on the floor
        rng = float(np.hypot(d[0], d[1]))
        return in_field(d, R), rng

    def tick(self):
        s = self.s
        dt = 0.02
        vx, vy, wz = self.cmd
        seen, rng = self.sun_seen()
        self.cmd_hist.append((s.t, vx))
        if self.est is not None:
            # while the sun is in the field a later fix overwrites this step. While it is not, advance at the
            # forward speed measured on the last fixes, times the command, not at the raw command. The gait is
            # slower than the command. A pure command integral stops the duck short of the sun.
            use = vx
            if (not seen) and self.ever:
                use = vx * self.scale
            yaw = self.est[2]
            c, sn = np.cos(yaw), np.sin(yaw)
            self.est[0] += (c * use - sn * vy) * dt
            self.est[1] += (sn * use + c * vy) * dt
            self.est[2] = wrap(self.est[2] + wz * dt)
        if (not seen) and self.ever and self.lost_range_m is None:
            self.lost_range_m = round(rng, 3)
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
                self.q.append((s.t + self.lat, meas, rng))
                self.fixes += 1
                self.last_fix_range_m = round(rng, 3)
        while self.q and self.q[0][0] <= s.t:
            item = self.q.pop(0)
            meas = item[1]
            self.est = meas.copy()
            self.ever = True
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
        return dict(fixes=self.fixes, ever_seen=self.ever, first_lost_range_m=self.lost_range_m,
                    last_fix_range_m=self.last_fix_range_m, blind_s=round(self.blind_steps * 0.02, 2),
                    speed_scale=round(self.scale, 3))


def _bind(run):
    sx, sy = NR.NOISE[run.cfg["noise"]]
    run.est = CamEst(run.s, sx, D(sy), run.rate, run.lat)


class B6(NR.Run):
    def __init__(self, cfg):
        super().__init__(cfg)
        _bind(self)

    def step(self, cmd):
        if not self.est.ever:
            cmd = (0.0, 0.0, 0.5)
        self.est.cmd = cmd
        NR.Run.step(self, cmd)


class B7(R2.Run2):
    def __init__(self, cfg):
        super().__init__(cfg)
        _bind(self)

    def step(self, cmd):
        if not self.est.ever:
            cmd = (0.0, 0.0, 0.5)
        self.est.cmd = cmd
        R2.Run2.step(self, cmd)


def job(cfg):
    V3.world_from_cfg(cfg)
    try:
        run = B6(cfg) if cfg["volt"] < 6.6 else B7(cfg)
        # 7.2 V aim, same as the v3 best combo
        if cfg["volt"] >= 6.6 and cfg.get("aim_mm"):
            v2 = dict(cfg.get("v2") or {})
            v2["aim_left"] = {"6.0": 0.0, "7.2": -float(cfg["aim_mm"]) / 1000.0}
            run.p = dict(run.p, **{"aim_left": v2["aim_left"]})
        out = run.go()
        out["camera"] = run.est.report()
        return out
    except Exception as e:
        import traceback
        return dict(cfg=cfg, error=repr(e), tb=traceback.format_exc())


def configs(n, wall_x, aim_mm):
    J = []
    for c in NR.configs(n):
        c = dict(c)
        c["edge"] = "steps"
        c["wall_x"] = wall_x
        c["aim_mm"] = aim_mm
        c["trace"] = False
        J.append(c)
    return J


if __name__ == "__main__":
    n = int(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else "b190"
    wall_x = float(os.environ.get("NEST_WALL_X", "0.190"))
    aim_mm = float(os.environ.get("AIM_MM", "20"))
    os.environ["NEST_EDGE"] = "steps"
    J = configs(n, wall_x, aim_mm)
    t = time.time()
    R = []
    with Pool(int(os.environ.get("JOBS", "4")), maxtasksperchild=6) as p:
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=1)):
            R.append(r)
            if (i + 1) % 20 == 0:
                print(i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: r["cfg"]["seed"])
    doc = dict(label="sim pass only",
               perception="camera field while the sun centre is inside 66 by 41 deg, then command dead reckoning",
               controller="mixed: steering at 6.0 V, straight crossing at 7.2 V, two 1 mm steps, aim 20 mm right at 7.2 V",
               wall_x_m=wall_x, aim_mm_right_at_7v2=aim_mm, edge="steps",
               field_deg=[66.0, 41.0], pupil_ahead_of_head_m=PUPIL,
               note="190 mm is the approved sun distance. 215 mm is a study only. The detector noise while the sun is in the field is the nest sim noise schedule, not a measured camera.",
               runs=R)
    path = os.path.join(HERE, "blind_runs_%s.json" % tag)
    json.dump(doc, open(path, "w"))
    print("wrote", len(R), "runs", "%.0f s" % (time.time() - t), path)
