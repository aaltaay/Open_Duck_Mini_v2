"""Budget rules. No emulator and no models."""

import os
import unittest

from altaay_lab.software.pi_fit.budget import (
    BUS_ASSUMED_S,
    CHIP_MIB,
    OS_USED_MIB,
    PERIOD_S,
    VISIBLE_MIB,
    cpu_fits,
    percentile,
    period_jitter,
    quota_us,
    ram_fits,
    slice_stats,
    verdict,
    work_stats,
)
from altaay_lab.software.pi_fit.pi5_board import (
    BOARD_X_MM,
    BOARD_Y_MM,
    HOLE_D_MM,
    HOLE_PITCH_X_MM,
    HOLE_PITCH_Y_MM,
    hole_centers,
)
from altaay_lab.software.pi_fit.pin import apply_from_env


class BudgetTests(unittest.TestCase):
    def test_cited_constants(self):
        self.assertEqual(PERIOD_S, 0.020)
        self.assertEqual(CHIP_MIB, 512.0)
        self.assertEqual(VISIBLE_MIB, 417.0)
        self.assertEqual(OS_USED_MIB, 125.4)
        self.assertAlmostEqual(BUS_ASSUMED_S, 0.00518)

    def test_cpu_miss_when_work_passes_20_ms(self):
        stats = work_stats([0.010, 0.021, 0.019])
        self.assertEqual(stats["misses_cpu"], 1)
        self.assertEqual(stats["misses_cpu_plus_bus"], 2)
        self.assertFalse(cpu_fits(stats))

    def test_cpu_fits_when_bus_add_still_fits(self):
        stats = work_stats([0.004, 0.006, 0.010])
        self.assertEqual(stats["misses_cpu"], 0)
        self.assertEqual(stats["misses_cpu_plus_bus"], 0)
        self.assertTrue(cpu_fits(stats))

    def test_empty_trace_does_not_fit(self):
        self.assertFalse(cpu_fits(work_stats([])))

    def test_percentile_ends(self):
        self.assertEqual(percentile([1.0, 2.0, 3.0], 0), 1.0)
        self.assertEqual(percentile([1.0, 2.0, 3.0], 100), 3.0)
        self.assertEqual(percentile([4.0], 50), 4.0)

    def test_jitter_span(self):
        jitter = period_jitter([0.020, 0.022, 0.019])
        self.assertAlmostEqual(jitter["span_s"], 0.003)

    def test_slice_keeps_the_window(self):
        window = slice_stats([0.001, 0.030, 0.002], [0.020, 0.030, 0.020], 1, 2)
        self.assertEqual(window["work"]["n"], 1)
        self.assertEqual(window["work"]["misses_cpu"], 1)

    def test_ram_rejects_swap_and_a_peak_over_the_line(self):
        self.assertTrue(ram_fits(400.0, 0.0, 417.0))
        self.assertFalse(ram_fits(418.0, 0.0, 417.0))
        self.assertFalse(ram_fits(200.0, 8.0, 417.0))
        self.assertFalse(ram_fits(None, 0.0, 417.0))

    def test_verdict_words(self):
        self.assertEqual(verdict(True, True), "fits")
        self.assertEqual(verdict(True, False), "fits")
        self.assertEqual(verdict(False, True), "fits with fixes")
        self.assertEqual(verdict(False, False), "does not fit")

    def test_quota_matches_the_slower_cited_score(self):
        self.assertEqual(quota_us(10000.0, 2500.0, 100000), 25000)
        # A measured score below the cited score cannot grow past one full period.
        self.assertEqual(quota_us(1000.0, 5000.0, 100000), 100000)

    def test_pi5_holes_match_the_drawing_pitch(self):
        self.assertEqual(BOARD_X_MM, 85.0)
        self.assertEqual(BOARD_Y_MM, 56.0)
        self.assertEqual(HOLE_D_MM, 2.7)
        centers = hole_centers()
        self.assertEqual(len(centers), 4)
        xs = sorted({row[0] for row in centers})
        ys = sorted({row[1] for row in centers})
        self.assertAlmostEqual(xs[1] - xs[0], HOLE_PITCH_X_MM)
        self.assertAlmostEqual(ys[1] - ys[0], HOLE_PITCH_Y_MM)
        self.assertAlmostEqual(ys[0], (56.0 - 49.0) / 2.0)

    def test_pin_is_idle_without_the_variable(self):
        old = os.environ.pop("ODM_WALK_CPU", None)
        try:
            self.assertEqual(apply_from_env(), {"pinned": False})
        finally:
            if old is not None:
                os.environ["ODM_WALK_CPU"] = old

    def test_pin_uses_a_real_core_then_restores(self):
        allowed = os.sched_getaffinity(0)
        cpu = sorted(allowed)[0]
        old_cpu = os.environ.get("ODM_WALK_CPU")
        old_nice = os.environ.get("ODM_WALK_NICE")
        try:
            os.environ["ODM_WALK_CPU"] = str(cpu)
            os.environ["ODM_WALK_NICE"] = "0"
            note = apply_from_env()
            self.assertTrue(note["pinned"])
            self.assertEqual(note["cpu"], cpu)
            self.assertIn(cpu, os.sched_getaffinity(0))
        finally:
            os.sched_setaffinity(0, allowed)
            if old_cpu is None:
                os.environ.pop("ODM_WALK_CPU", None)
            else:
                os.environ["ODM_WALK_CPU"] = old_cpu
            if old_nice is None:
                os.environ.pop("ODM_WALK_NICE", None)
            else:
                os.environ["ODM_WALK_NICE"] = old_nice


if __name__ == "__main__":
    unittest.main()
