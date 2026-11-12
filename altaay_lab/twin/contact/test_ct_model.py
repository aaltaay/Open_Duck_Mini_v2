"""Checks for the contact twin. Arithmetic only."""

import os
import unittest

import ct_model as m

HERE = os.path.dirname(os.path.abspath(__file__))


class ContactTwin(unittest.TestCase):
    def test_catalog_table_points(self):
        self.assertAlmostEqual(m.spring_n(0.0), 0.42, places=2)
        self.assertAlmostEqual(m.spring_n(2.54), 2.8 * m.OZ_TO_N, places=3)
        self.assertAlmostEqual(m.spring_n(5.08), 4.1 * m.OZ_TO_N, places=3)
        self.assertAlmostEqual(m.spring_n(10.16), 6.5 * m.OZ_TO_N, places=3)

    def test_rated_point_near_catalog_line(self):
        # The catalog also prints 1.58 N at 8.05 mm, off the ounce grid.
        self.assertAlmostEqual(m.spring_n(8.05), 1.58, delta=0.03)

    def test_force_rises(self):
        self.assertLess(m.spring_n(3.0), m.spring_n(4.55))
        self.assertLess(m.spring_n(4.55), m.spring_n(7.5))

    def test_weight_closes(self):
        total = m.PLANE["soles_N"][0] + m.PLANE["seat_block_N"][0] + m.PLANE["total_pin_N"][0]
        self.assertAlmostEqual(total, m.SIT_MASS_KG * m.G, delta=0.02)

    def test_open_when_a_pole_is_gone(self):
        self.assertFalse(m.loop(0, 2, 1.0, 0.06)["closed"])
        self.assertFalse(m.loop(2, 0, 1.0, 0.06)["closed"])
        self.assertFalse(m.loop(1, 0, 1.0, 0.06)["closed"])
        self.assertFalse(m.loop(0, 1, 1.0, 0.06)["closed"])

    def test_one_miss_still_charges_and_takes_the_current(self):
        row = m.loop(1, 2, 2.8, 0.0601)
        self.assertTrue(row["closed"])
        self.assertAlmostEqual(row["i_plus_each"], 2.8)
        self.assertAlmostEqual(row["i_minus_each"], 1.4)

    def test_pair_cannot_bridge_the_gap(self):
        c = m.classify(0.0, 0.0, 0.0)
        self.assertFalse(c["pair_can_bridge_gap"])
        self.assertLess(c["metal_span_mm"], m.GAP)
        self.assertEqual(c["n_miss"], 0)

    def test_lateral_bands(self):
        self.assertEqual(m.classify(0.0, 37.0, 0.0)["n_miss"], 0)
        self.assertEqual(m.classify(0.0, 40.0, 0.0)["n_miss"], 1)
        self.assertTrue(m.classify(0.0, 40.0, 0.0)["charges"])
        self.assertFalse(m.classify(0.0, 60.0, 0.0)["charges"])

    def test_radial_window_matches_the_cad_45(self):
        w = m.window()
        self.assertEqual(w["toward_wall_mm"], 45.0)
        self.assertEqual(w["away_from_wall_mm"], 45.0)

    def test_tip_pressure_is_many_times_the_f1_ten_percent(self):
        felt = m.felt_block()
        self.assertGreater(felt["times_10pct_pressure"]["F-1"], 5.0)

    def test_local_dent_unloads_the_spring(self):
        # A lower contact surface increases s in comp = Lp - s, so the dent subtracts.
        held = m.stroke_after_dent(1.85, 0.2)
        lost = m.stroke_after_dent(1.85, 2.0)
        self.assertTrue(held["touching"])
        self.assertAlmostEqual(held["stroke_mm"], 1.65, places=2)
        self.assertFalse(lost["touching"])
        seat = m.stroke_after_dent(3.0, 2.0)
        self.assertTrue(seat["touching"])
        self.assertAlmostEqual(seat["stroke_mm"], 1.0, places=2)
        self.assertGreater(m.spring_n(seat["stroke_mm"]), 0.42)

    def test_voltage_is_far_under_paschen(self):
        self.assertLess(m.V_MAT / m.PASCHEN_V, 0.05)
        self.assertLess(m.V_PACK / m.PASCHEN_V, 0.05)

    def test_report_has_no_em_dash(self):
        path = os.path.join(HERE, "CONTACT_TWIN.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("\u2014", text)
        self.assertNotIn("\u2013", text)


if __name__ == "__main__":
    unittest.main()
