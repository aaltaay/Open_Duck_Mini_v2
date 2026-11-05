#!/usr/bin/env python3
"""Unit tests of the ported autodock (no ROS, no robot): the upstream bug fixes, the frame helpers, and full docks of
a planar stand-in duck that copies the stock policy's command response measured in the shared lab gym (overlay
gym/overlays/duck; sim pass only): no stepping under a 0.10 forward command, 0.096 m/s at 0.15, -0.044 m/s at
-0.15, sidestep only at 0.20 (0.092 m/s), turning 0.12 rad/s at 0.25 and 0.38 rad/s at 0.5.
Run from altaay_lab/software/dock:  python3 -m unittest discover -s tests -v
Optional: tests/data/replay_*.json, tag observations recorded by the gym dock sim, are replayed if present."""
import glob
import json
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from autodock import autodock_utils as U                                  # noqa: E402
from autodock.autodock_base import AutoDockBase, AutoDockConfig, DockIO   # noqa: E402
from autodock.duck_autodock import DuckAutoDock, DuckAutoDockConfig, load_config   # noqa: E402

YAML = os.path.join(os.path.dirname(HERE), "duck_autodock.yaml")


class RecIO(DockIO):
    def __init__(self):
        self.cmds = []
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, dt):
        self.t += dt

    def send_cmd(self, vx, vy, wz):
        self.cmds.append((vx, vy, wz))

    def get_marker(self, marker):
        return None

    def get_odom(self):
        return np.eye(4)


class TestFixes(unittest.TestCase):
    def test_clamp_each_axis(self):
        io = RecIO()
        b = AutoDockBase(AutoDockConfig(linear_vel_range=(-0.15, 0.15), linear_y_range=(-0.2, 0.2),
                                        angular_vel_range=(-0.5, 0.5)), io)
        self.assertEqual(b.publish_cmd(linear_vel=0.15, angular_vel=1.0, linear_y=0.5), (0.15, 0.2, 0.5))
        self.assertEqual(b.publish_cmd(linear_vel=-1.0, angular_vel=-1.0, linear_y=-0.5), (-0.15, -0.2, -0.5))
        # upstream bug: linear.x was clamped against the angular range (0.8 forward became 0.13 with tb3)
        b2 = AutoDockBase(AutoDockConfig(linear_vel_range=(-0.8, 0.8), angular_vel_range=(-0.13, 0.13)), io)
        self.assertEqual(b2.publish_cmd(linear_vel=0.5, angular_vel=0.3)[:1], (0.5,))
        self.assertAlmostEqual(b2.publish_cmd(linear_vel=0.5, angular_vel=0.3)[2], 0.13)

    def test_circular_mean(self):
        m = U.avg_2d_poses([(0, 0, math.pi - 0.1), (0, 0, -math.pi + 0.1)])
        self.assertAlmostEqual(abs(m[2]), math.pi, places=6)       # upstream gave 0.0
        self.assertAlmostEqual(U.avg_2d_poses([(1, 2, 0.2), (3, 4, 0.4)])[0], 2.0)
        self.assertIsNone(U.avg_2d_poses([]))

    def test_round_trips(self):
        for p in [(0.3, -0.2, 0.7), (-1.0, 2.0, -2.9), (0.0, 0.0, math.pi - 1e-3)]:
            q = U.flip_base_frame(U.flip_base_frame(p))
            self.assertTrue(np.allclose(q[:2], p[:2]) and abs(U.set_angle(q[2] - p[2])) < 1e-9)
            r = U.get_2d_inverse(U.get_2d_inverse(p))
            self.assertTrue(np.allclose(r[:2], p[:2]) and abs(U.set_angle(r[2] - p[2])) < 1e-9)
            m = U.mat_from_2d(p) @ U.mat_from_2d(U.get_2d_inverse(p))
            self.assertTrue(np.allclose(m, np.eye(4)))
        d = U.compute_tf_diff(U.mat_from_2d((1, 1, 0.5)), U.apply_2d_transform(U.mat_from_2d((1, 1, 0.5)), (0.2, -0.1, 0.3)))
        self.assertTrue(np.allclose(d, (0.2, -0.1, 0.3)))

    def test_bin_filter(self):
        self.assertEqual(U.bin_filter(-0.01, 0.25), -0.25)
        self.assertEqual(U.bin_filter(0.0, 0.25), 0.25)
        self.assertEqual(U.bin_filter(3.0, -0.25), 0.25)

    def test_no_exit_on_lost_odom(self):
        class NoOdom(RecIO):
            def get_odom(self):
                return None
        io = NoOdom()
        b = AutoDockBase(AutoDockConfig(), io)
        self.assertFalse(b.move_with_odom(0.2))        # upstream would have exited the process
        self.assertEqual(io.cmds[-1], (0.0, 0.0, 0.0))

    def test_yaml_keys(self):
        cfg = load_config(YAML)
        self.assertEqual(cfg.linear_vel_range, (-0.15, 0.15))


# --------------------------------------------------------------------------- planar stand-in duck
def response(vx, vy, wz, elapsed=10.0):
    """the stock policy's measured response (gym probes, our build, sim pass only): steady rates, and from standing
    the lag and rate that reproduce the pulse probe (wz 0.5: 0.17 rad in 0.5 s; wz 0.25: 0.03 rad in 1 s, 0.17 in
    2 s; vy 0.2: 10 mm in 0.5 s, 40 mm in 1 s; vx 0.15: 74 mm in 1 s)"""
    fwd = 0.0
    if vx >= 0.10:
        fwd = float(np.interp(vx, [0.10, 0.125, 0.15], [0.057, 0.079, 0.096])) if elapsed >= 0.15 else 0.0
    elif vx <= -0.15:
        fwd = -0.044 if elapsed >= 0.5 else 0.0
    side = 0.085 if vy >= 0.199 and elapsed >= 0.6 else 0.0          # no right sidestep at all (gym probe)
    turn = 0.0
    if wz >= 0.45:
        turn = 0.36
    elif wz <= -0.45:
        turn = -0.22                                                        # right turns are weaker (gym probe)
    elif abs(wz) >= 0.25 and elapsed >= 0.8:
        turn = math.copysign(0.12, wz)
    if fwd and turn:
        turn *= 0.6
    return fwd, side, turn


class PlanarDuck(DockIO):
    MAST_X = 2.0
    BUMPER_X = 2.0 - 0.075            # bumper face 75 mm in front of the tag face
    CHEST = 0.046                     # trunk origin to chest front
    TAGS = {"tag_0": 0.0, "tag_1": 0.10, "tag_2": -0.10}

    def __init__(self, x, y, th, seed=0, noise=0.002):
        self.p = np.array([x, y, th], float)
        self.cmd_req, self.t_cmd = (0.0, 0.0, 0.0), 0.0
        self.t = 0.0
        self.rng = np.random.default_rng(seed)
        self.noise = noise
        self.odom = np.array([0.0, 0.0, th])
        self.seated = False
        self.log = []

    def now(self):
        return self.t

    def sleep(self, dt):
        n = max(1, int(round(dt / 0.01)))
        for _ in range(n):
            f, s, w = response(*self.cmd, elapsed=self.t - self.t_cmd) if not self.seated else (0, 0, 0)
            f *= 1.0 + 0.05 * self.rng.standard_normal()
            c, si = math.cos(self.p[2]), math.sin(self.p[2])
            dx, dy = (f * c - s * si) * 0.01, (f * si + s * c) * 0.01
            if self.p[0] + dx + self.CHEST > self.BUMPER_X:
                dx = max(0.0, self.BUMPER_X - self.CHEST - self.p[0])
            self.p += (dx, dy + 0.004 * 0.01 * self.rng.standard_normal(), w * 0.01)
            # dead reckoning: the command times the nominal ratios, IMU yaw exact
            fn, sn, _ = response(*self.cmd) if not self.seated else (0, 0, 0)
            c, si = math.cos(self.p[2]), math.sin(self.p[2])
            self.odom += ((fn * c - sn * si) * 0.01, (fn * si + sn * c) * 0.01, 0.0)
            self.odom[2] = self.p[2]
            self.t += 0.01

    def send_cmd(self, vx, vy, wz):
        if (vx, vy, wz) != self.cmd_req:
            self.cmd_req, self.t_cmd = (vx, vy, wz), self.t
        self.log.append((round(self.t, 2), vx, vy, wz))

    @property
    def cmd(self):
        return self.cmd_req

    def get_marker(self, marker):
        ty = self.TAGS[marker]
        cam = self.p[:2] + 0.10 * np.array([math.cos(self.p[2]), math.sin(self.p[2])])
        v = np.array([self.MAST_X, ty]) - cam
        rng_ = np.linalg.norm(v)
        bearing = U.set_angle(math.atan2(v[1], v[0]) - self.p[2])
        if rng_ < (0.05 if marker == "tag_0" else 0.15) or rng_ > 4.0 or abs(bearing) > math.radians(30):
            return None
        # marker pose in world: x = -y_world, y = +z_world, z = -x_world (faces the duck)
        Rw = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], float)
        Tw = U.mat_from_rt(Rw, (self.MAST_X, ty, 0.36))
        base = U.mat_from_rt(np.eye(3), (0, 0, 0)) @ U.mat_from_2d(tuple(self.p))
        T = U.inverse_matrix(base) @ Tw
        T[:2, 3] += self.rng.normal(0, self.noise, 2)
        return T, self.t

    def get_odom(self):
        return U.mat_from_2d(tuple(self.odom))

    def bumper_contact(self):
        return self.p[0] + self.CHEST >= self.BUMPER_X - 1e-4

    def sit(self):
        gap = self.BUMPER_X - self.CHEST - self.p[0]
        if 0.030 <= gap <= 0.050:               # the gym sit window (hard floor 40 to 50 mm, soft 30 to 45 mm)
            self.p[0] = self.BUMPER_X - self.CHEST
        else:
            self.p[0] += min(0.0475, gap)
        self.seated = True
        return True

    def stand(self):
        self.seated = False
        return True

    def pads_ok(self):
        return self.bumper_contact() and abs(self.p[1]) <= 0.025 and abs(math.degrees(U.set_angle(self.p[2]))) <= 10.0

    def charge_state(self):
        return "CHARGING" if self.seated and self.pads_ok() else "NONE"


class TestDock(unittest.TestCase):
    def test_docks_from_starts(self):
        cfg = load_config(YAML)
        starts = [(0.6, 0.0, 0.0), (0.7, 0.25, -0.3), (0.5, -0.3, 0.35), (0.9, 0.1, 0.5), (0.4, -0.15, -0.6)]
        for i, (x, y, th) in enumerate(starts):
            io = PlanarDuck(x, y, th, seed=i)
            sm = DuckAutoDock(cfg, io)
            ok = sm.start()
            self.assertTrue(ok, f"start {i}: {sm.history[-4:]}")
            self.assertTrue(io.pads_ok(), f"start {i}: pose {io.p}")

    def test_retry_after_missed_pins(self):
        cfg = load_config(YAML)

        class Flaky(PlanarDuck):
            fails = 1

            def charge_state(self):
                if self.seated and self.fails > 0:
                    return "NONE"
                return super().charge_state()

            def stand(self):
                self.fails -= 1
                return super().stand()
        io = Flaky(0.7, 0.05, 0.1, seed=7)
        sm = DuckAutoDock(cfg, io)
        self.assertTrue(sm.start())
        self.assertGreaterEqual(sm.attempts, 2)
        self.assertIn("RETRY", [h[1] for h in sm.history])

    def test_lost_tags_face_mast(self):
        """the turn-away fix: tags seen once, then the duck faces 90 deg off with the mast out of the view; the
        approach turns to the mast remembered on odometry and reaches the staging point without a blind search"""
        cfg = load_config(YAML)
        io = PlanarDuck(1.25, -0.22, 0.0, seed=11)
        sm = DuckAutoDock(cfg, io)
        self.assertIsNotNone(sm.look())
        self.assertIsNotNone(sm.mast_odom)
        io.p[2] = io.odom[2] = -1.5                          # turned away to the right
        self.assertIsNone(sm.look())
        self.assertTrue(sm.do_approach())
        brg, rng = sm.mast_bearing()
        self.assertLess(abs(brg), 0.35)
        self.assertLess(io.t, 60.0)

    def test_gives_up_without_markers(self):
        cfg = load_config(YAML)
        io = PlanarDuck(0.7, 0.0, math.pi, seed=3)          # facing away and never turned toward: search then fail
        io.get_marker = lambda m: None
        sm = DuckAutoDock(cfg, io)
        self.assertFalse(sm.start())
        self.assertEqual(io.log[-1][1:], (0.0, 0.0, 0.0))


class TestReplay(unittest.TestCase):
    """Replays tag observations recorded by the gym dock sim (sim pass only): the dock-relative pose of each side-tag
    look is recomputed from the recorded marker poses and must match the recorded one."""

    def test_replays(self):
        files = sorted(glob.glob(os.path.join(HERE, "data", "replay_*.json")))
        if not files:
            self.skipTest("no recorded replay files")
        cfg = load_config(YAML)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                rec = json.load(fh)
            looks = [lk for lk in rec["looks"] if lk.get("src", "").startswith("sides")]   # centre looks also need the IMU yaw
            self.assertGreater(len(looks), 3)
            for look in looks:
                io = RecIO()
                sm = DuckAutoDock(cfg, io)
                mk = {k: (np.array(v), 0.0) for k, v in look["markers"].items()}
                io.get_marker = lambda m, mk=mk: mk.get(m)
                r = sm.dock_relative(use_centre=True)
                self.assertIsNotNone(r)
                self.assertTrue(np.allclose(r[:3], look["rel"][:3], atol=1e-6), f)


if __name__ == "__main__":
    unittest.main()
