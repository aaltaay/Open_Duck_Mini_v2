"""Synthetic frames for the nest finder. No MuJoCo. No hardware."""

from __future__ import annotations

import os
import time
import unittest

import numpy as np

from altaay_lab.software.autonomy.disc_loop import SIT_FWD_M, DiscLoop
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
            img[cy - 8:cy + 36, cx + 6:cx + 46] = (168, 189, 148)
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
        self.assertEqual(len(cmd), 4)

    def test_close_sun_turns(self):
        loop = DiscLoop()
        loop.phase = "approach"
        loop.t_phase = 0.0
        est = {"seen": True, "clipped": False, "sun_fwd": SIT_FWD_M - 0.02, "sun_left": 0.01,
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
