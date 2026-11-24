"""Synthetic frames for the nest finder. No MuJoCo. No hardware."""

from __future__ import annotations

import os
import time
import unittest

import numpy as np

from altaay_lab.software.autonomy.disc_loop import HEAD_YAW_HI, HEAD_YAW_LO, SIT_FWD_M, DiscLoop
from altaay_lab.software.perception.nest_find import find_nest, intrinsics, sun_in_trunk


def _frame(h, w, tint=(1.0, 1.0, 1.0), cover=False, cliff=False, blob=False, empty=False):
    img = np.zeros((h, w, 3), np.float32)
    img[:] = (168, 189, 148)
    if not empty:
        cy, cx = int(h * 0.58), int(w * 0.50)
        radius = 18
        yy, xx = np.ogrid[:h, :w]
        dx = xx - cx
        dy = (yy - cy) / 0.55
        rho = np.hypot(dx, dy)
        ring = (rho > radius * 2.6) & (rho < radius * 4.6)
        img[ring] = (242, 222, 153)
        disc = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        img[disc] = (230, 178, 56)
        if cover:
            # One side of the ring, including the cloth above and below the
            # disc. The disc itself stays.
            disc_px = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
            right = (xx > cx + 2) & (rho < radius * 5.2) & ~disc_px
            img[right] = (168, 189, 148)
    if cliff:
        y0 = int(h * 0.78)
        img[y0:y0 + 14, :] = (6, 6, 8)
    if blob:
        img[int(h * 0.62):int(h * 0.62) + 26, 18:46] = (10, 10, 12)
    img *= np.array(tint, np.float32).reshape(1, 1, 3)
    return np.clip(img, 0, 255).astype(np.uint8)


class FindTests(unittest.TestCase):
    def setUp(self):
        self.h, self.w = 348, 200
        self.fx, self.fy, self.cx, self.cy, self.hfov = intrinsics(self.w, self.h)

    def test_field_matches_the_brief(self):
        self.assertGreater(self.hfov, 39.0)
        self.assertLess(self.hfov, 43.0)

    def test_disc_and_ring(self):
        img = _frame(self.h, self.w)
        est = find_nest(img, self.fx, self.fy, self.cx, self.cy)
        self.assertTrue(est["seen"])
        self.assertTrue(est["ring"])
        self.assertFalse(est["occluded"])
        self.assertGreater(est["width_px"], 30)
        self.assertLess(est["width_px"], 44)

    def test_warm_and_dim_still_find_the_disc(self):
        for tint in ((1.0, 0.70, 0.42), (0.45, 0.50, 0.62)):
            est = find_nest(_frame(self.h, self.w, tint=tint), self.fx, self.fy, self.cx, self.cy)
            self.assertTrue(est["seen"], tint)

    def test_cover_marks_occlusion_and_keeps_the_disc(self):
        est = find_nest(_frame(self.h, self.w, cover=True), self.fx, self.fy, self.cx, self.cy)
        self.assertTrue(est["seen"])
        self.assertTrue(est["occluded"])

    def test_empty_felt_is_not_a_nest(self):
        est = find_nest(_frame(self.h, self.w, empty=True), self.fx, self.fy, self.cx, self.cy)
        self.assertFalse(est["seen"])

    def test_cliff_and_obstacle(self):
        est = find_nest(_frame(self.h, self.w, cliff=True, blob=True), self.fx, self.fy, self.cx, self.cy)
        self.assertTrue(est["cliff"])
        self.assertTrue(est["obstacle"])

    def test_depth_and_trunk_frame(self):
        width = 40.0
        depth = 0.100 * self.fx / width
        # Camera x right, y up, z back. Forward is trunk +x, left is trunk +y.
        r = np.array([[0.0, 0.0, -1.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        got = sun_in_trunk(self.cx, self.cy, width, self.fx, self.fy, self.cx, self.cy, r, np.zeros(3))
        self.assertAlmostEqual(got["depth_m"], depth, places=6)
        self.assertAlmostEqual(got["sun_fwd"], depth, places=5)
        self.assertAlmostEqual(got["sun_left"], 0.0, places=5)

    def test_x86_frame_time(self):
        img = _frame(self.h, self.w)
        find_nest(img, self.fx, self.fy, self.cx, self.cy)
        t0 = time.perf_counter()
        n = 20
        for _ in range(n):
            find_nest(img, self.fx, self.fy, self.cx, self.cy)
        ms = (time.perf_counter() - t0) * 1000.0 / n
        # A bound, not the number in the report. The report measures the sim frame.
        self.assertLess(ms, 80.0)


class LoopTests(unittest.TestCase):
    def test_far_sun_walks_forward(self):
        loop = DiscLoop()
        est = {"seen": True, "clipped": False, "sun_fwd": 1.2, "sun_left": 0.05,
               "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertEqual(loop.phase, "approach")
        cmd = loop.command(est, 0.0, 0.02)
        self.assertGreater(cmd[0], 0.05)
        self.assertEqual(len(cmd), 5)

    def test_close_sun_turns(self):
        loop = DiscLoop()
        loop.phase = "approach"
        loop.t_phase = 0.0
        est = {"seen": True, "clipped": False, "sun_fwd": SIT_FWD_M - 0.02, "sun_left": 0.06,
               "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        loop.command(est, 0.2, 0.02)
        self.assertEqual(loop.phase, "turn")

    def test_lost_close_disc_turns_without_a_world_pose(self):
        loop = DiscLoop()
        loop.phase = "approach"
        loop.last_fwd = 0.55
        loop.last_left = 0.0
        loop.ever_seen = True
        loop.command(None, 0.2, 0.02)
        self.assertEqual(loop.phase, "turn")

    def test_lost_far_disc_creeps(self):
        loop = DiscLoop()
        loop.phase = "approach"
        loop.last_fwd = 1.15
        loop.last_left = 0.0
        loop.ever_seen = True
        loop.command(None, 0.0, 0.02)
        self.assertEqual(loop.phase, "creep")
        cmd = loop.command(None, 0.0, 0.02)
        self.assertGreater(cmd[0], 0.0)

    def test_obstacle_on_the_right_yaws_left(self):
        loop = DiscLoop()
        loop.phase = "approach"
        est = {"seen": True, "clipped": False, "sun_fwd": 0.8, "sun_left": 0.0,
               "cliff": False, "obstacle": True, "obstacle_right": 0.2}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertGreater(cmd[2], 0.0)
        self.assertEqual(cmd[0], 0.0)
        est["obstacle_right"] = -0.2
        cmd = loop.command(est, 0.0, 0.02)
        self.assertLess(cmd[2], 0.0)
        self.assertEqual(cmd[0], 0.0)

    def test_a_head_yaw_does_not_hide_an_obstacle_on_the_other_side(self):
        from altaay_lab.software.autonomy.disc_loop import _obs_left
        # Head looking left. The disc is along that look. An image-right
        # obstacle is then on the other side of the trunk and is not the disc.
        self.assertAlmostEqual(_obs_left(0.30, 0.0), 0.30, places=5)
        self.assertAlmostEqual(_obs_left(0.30, 0.25), 0.05, places=5)
        loop = DiscLoop()
        loop.phase = "approach"
        loop.head_cmd = 0.30
        est = {"seen": True, "clipped": False, "sun_fwd": 0.8, "sun_left": 0.25,
               "cliff": False, "obstacle": True, "obstacle_right": 0.25}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertGreater(cmd[2], 0.0)
        self.assertEqual(cmd[0], 0.0)
        est["obstacle_right"] = 0.0
        cmd = loop.command(est, 0.0, 0.02)
        self.assertNotEqual(cmd[2], 0.50)
        self.assertNotEqual(cmd[2], -0.50)

    def test_trim_turns_toward_a_sun_that_is_behind(self):
        loop = DiscLoop()
        loop.phase = "trim"
        est = {"seen": True, "clipped": False, "sun_fwd": -0.4, "sun_left": 0.08,
               "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertEqual(loop.phase, "trim")
        self.assertLess(cmd[2], 0.0)
        est["sun_left"] = -0.08
        cmd = loop.command(est, 0.0, 0.02)
        self.assertGreater(cmd[2], 0.0)

    def test_cliff_stops_a_creep(self):
        loop = DiscLoop()
        loop.phase = "approach"
        loop.last_fwd = 1.15
        loop.last_left = 0.0
        loop.ever_seen = True
        loop.command(None, 0.0, 0.02)
        self.assertEqual(loop.phase, "creep")
        est = {"seen": False, "clipped": False, "sun_fwd": None, "sun_left": None,
               "cliff": True, "obstacle": False, "obstacle_right": 0.0}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertEqual(loop.phase, "creep")
        self.assertEqual(cmd[0], 0.0)
        self.assertNotEqual(cmd[2], 0.0)

    def test_a_new_fix_waits_out_the_latency(self):
        from altaay_lab.twin.dock.camera.disc_dock import due_estimate
        fresh = {
            "seen": True, "sun_fwd": 1.0, "sun_left": 0.05,
            "cliff": True, "obstacle": False, "obstacle_right": 0.1,
        }
        queued = {"seen": True, "sun_fwd": 1.0, "sun_left": 0.0,
                  "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        early = due_estimate([(0.10, queued)], 0.0, fresh)
        self.assertFalse(early["seen"])
        self.assertTrue(early["cliff"])
        due = due_estimate([(0.10, queued)], 0.10, fresh)
        self.assertTrue(due["seen"])
        self.assertAlmostEqual(due["sun_fwd"], 1.0)
        self.assertTrue(due["cliff"])

    def test_search_sweeps_inside_the_head_stops(self):
        loop = DiscLoop()
        yaws = []
        spins = []
        for _ in range(50):
            cmd = loop.command(None, 0.0, 0.10)
            yaws.append(cmd[4])
            spins.append(cmd[2])
            self.assertGreaterEqual(cmd[4], HEAD_YAW_LO - 1e-6)
            self.assertLessEqual(cmd[4], HEAD_YAW_HI + 1e-6)
        # The standing sweep reaches both sides of the stops, then the
        # body turns. The two are not commanded in the same step.
        self.assertLess(min(yaws), -0.4)
        self.assertGreater(max(yaws), 0.4)
        self.assertTrue(any(abs(z) > 0.4 for z in spins))
        self.assertGreater(min(yaws), HEAD_YAW_LO - 1e-6)
        self.assertLess(max(yaws), HEAD_YAW_HI + 1e-6)

    def test_close_negative_bearing_squares_up_before_the_turn(self):
        loop = DiscLoop()
        loop.phase = "approach"
        est = {"seen": True, "clipped": False, "sun_fwd": SIT_FWD_M - 0.02, "sun_left": -0.08,
               "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertEqual(loop.phase, "approach")
        self.assertLess(cmd[2], 0.0)
        self.assertEqual(cmd[0], 0.0)

    def test_memory_walks_toward_the_last_bearing(self):
        loop = DiscLoop()
        est = {"seen": True, "clipped": False, "sun_fwd": 1.2, "sun_left": 0.15,
               "cliff": False, "obstacle": False, "obstacle_right": 0.0}
        loop.command(est, 0.0, 0.02)
        loop.phase = "search"
        cmd = loop.command(None, 0.0, 0.02)
        self.assertGreater(cmd[0], 0.05)

    def test_cliff_does_not_walk_forward(self):
        loop = DiscLoop()
        loop.phase = "approach"
        est = {"seen": True, "clipped": False, "sun_fwd": 0.8, "sun_left": 0.0,
               "cliff": True, "obstacle": False, "obstacle_right": 0.0}
        cmd = loop.command(est, 0.0, 0.02)
        self.assertEqual(cmd[0], 0.0)

    def test_no_dash_in_sources(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        for name in ("nest_find.py",):
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("\u2014", text)
            self.assertNotIn("\u2013", text)
        loop = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "autonomy", "disc_loop.py"))
        with open(loop, encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("\u2014", text)
        self.assertNotIn("\u2013", text)


if __name__ == "__main__":
    unittest.main()
