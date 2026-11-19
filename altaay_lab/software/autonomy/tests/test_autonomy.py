"""Autonomy supervisor checks. No hardware and no MuJoCo.

Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/autonomy/tests -v
"""

from __future__ import annotations

import os
import tempfile
import unittest

import yaml

from altaay_lab.software.autonomy.camera_states import MEASURED, RETRY_CAP, charging_count
from altaay_lab.software.autonomy.plant import (
    CHARGE_A,
    PACK_LOW_V,
    RAIL_V,
    WALK_PACK_A,
    HomePlant,
)
from altaay_lab.software.autonomy.supervisor import GETUP_S, Supervisor
from altaay_lab.software.personality.limits import PACK_FULL_V, PACK_WALK_STOP_V


def _limits():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "verify", "part_limits.yaml")
    with open(os.path.abspath(path), encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _netlist():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "wiring", "netlist.yaml")
    with open(os.path.abspath(path), encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class Scripted:
    def __init__(self, docks, getups=None):
        self.docks = [dict(row) for row in docks]
        self.getups = list(getups or [])

    def dock(self):
        if not self.docks:
            raise AssertionError("dock() called more times than scripted")
        return dict(self.docks.pop(0))

    def getup(self):
        if not self.getups:
            raise AssertionError("getup() called more times than scripted")
        return self.getups.pop(0)


def _miss(seed=32):
    return {"seed": seed, "t_s": 2.0, "charging": False, "reason": "no_marker", "fell": False}


def _hit(seed=1):
    return {"seed": seed, "t_s": 2.0, "charging": True, "reason": "docked", "fell": False}


class TableTests(unittest.TestCase):
    def test_gold_dome_rate_is_the_published_40(self):
        self.assertEqual(len(MEASURED), 40)
        self.assertEqual(charging_count(), 38)
        by_seed = {row["seed"]: row for row in MEASURED}
        self.assertFalse(by_seed[29]["charging"])
        self.assertEqual(by_seed[29]["reason"], "one_well")
        self.assertFalse(by_seed[32]["charging"])
        self.assertEqual(by_seed[32]["reason"], "no_marker")
        self.assertEqual(RETRY_CAP, 2)

    def test_charge_current_matches_the_netlist_and_the_sheets(self):
        net = _netlist()
        found = None
        for comp in net["components"]:
            ratings = comp.get("ratings") or {}
            if "i_charge_a" in ratings and "BQ24133" in comp.get("part", ""):
                found = float(ratings["i_charge_a"])
        self.assertIsNotNone(found)
        self.assertAlmostEqual(CHARGE_A, found, places=3)
        limits = _limits()
        chip = limits["parts"]["bq24133"]
        cell = limits["parts"]["p45b"]
        self.assertGreaterEqual(CHARGE_A, chip["i_charge_min_a"])
        self.assertLessEqual(CHARGE_A, chip["i_charge_max_a"])
        self.assertLessEqual(CHARGE_A, cell["i_charge_max_a"])
        self.assertLess(WALK_PACK_A, cell["i_cont_a"])
        self.assertGreater(RAIL_V, 0.0)
        self.assertLess(PACK_WALK_STOP_V, PACK_FULL_V)
        self.assertGreaterEqual(PACK_LOW_V, cell["series"] * cell["v_cut"])


class LifeTests(unittest.TestCase):
    def test_three_misses_sit_and_show_help(self):
        outcomes = Scripted([_miss(32), _miss(29), _miss(32)])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        sup.personality.asked_home = True
        for _ in range(3):
            sup.step(plant, plant.t, 2.0)
        self.assertTrue(sup.stuck)
        self.assertEqual(sup.dock_attempts, 3)
        self.assertEqual(sup.dock_success, 0)
        self.assertEqual(sup.stuck_events, 1)
        row = sup.step(plant, plant.t, 0.5)
        self.assertEqual(row["mode"], "stuck")
        self.assertEqual(row["expression"], "help_me")
        self.assertEqual(sup.personality._command().eye_color, "white")

    def test_a_hit_after_a_miss_charges(self):
        outcomes = Scripted([_miss(), _hit()])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        sup.personality.asked_home = True
        sup.step(plant, 0.0, 2.0)
        self.assertFalse(sup.stuck)
        self.assertEqual(sup.dock_attempts, 2)
        sup.step(plant, plant.t, 2.0)
        self.assertTrue(sup.on_nest or sup.dock_success == 1)
        self.assertEqual(sup.dock_success, 1)
        self.assertGreater(plant.q_mAh, 0.0)
        q0 = plant.q_mAh
        sup.step(plant, plant.t, 5.0)
        self.assertLess(plant.q_mAh, q0)
        self.assertLessEqual(plant.v_pack, PACK_FULL_V)
        self.assertGreaterEqual(plant.min_pack_v, PACK_LOW_V)

    def test_fall_then_getup(self):
        outcomes = Scripted([], [True])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        plant.fallen = True
        sup.step(plant, 0.0, GETUP_S)
        self.assertFalse(plant.fallen)
        self.assertEqual(sup.falls, 1)
        row = sup.step(plant, plant.t, 0.5)
        self.assertNotEqual(row["mode"], "stuck")
        self.assertEqual(sup.stuck_events, 0)

    def test_two_failed_getups_ask_for_help(self):
        outcomes = Scripted([], [False, False])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        plant.fallen = True
        sup.step(plant, 0.0, GETUP_S)
        self.assertTrue(plant.fallen)
        self.assertFalse(sup.stuck)
        sup.step(plant, plant.t, GETUP_S)
        self.assertTrue(sup.stuck)
        row = sup.step(plant, plant.t, 0.2)
        self.assertEqual(row["expression"], "help_me")

    def test_a_pet_clears_the_wait(self):
        outcomes = Scripted([_miss(), _miss(), _miss(), _hit()])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        sup.personality.asked_home = True
        for _ in range(3):
            sup.step(plant, plant.t, 2.0)
        self.assertTrue(sup.stuck)
        sup.step(plant, plant.t, 0.2, ["petted"])
        self.assertFalse(sup.stuck)
        self.assertNotEqual(sup.personality.help_me, True)

    def test_restart_keeps_the_episode(self):
        outcomes = Scripted([{"seed": 4, "t_s": 10.0, "charging": True, "reason": "docked", "fell": False}])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        sup.personality.asked_home = True
        sup.step(plant, 0.0, 1.0)
        self.assertEqual(sup.dock_attempts, 1)
        self.assertIsNotNone(sup.episode)
        left = sup.episode_left
        snap = sup.snapshot(plant)
        fresh_outcomes = Scripted([])
        again = Supervisor(seed=0, outcomes=fresh_outcomes)
        again.restore(plant, snap)
        again.step(plant, plant.t, 1.0)
        self.assertEqual(again.dock_attempts, 1)
        self.assertAlmostEqual(again.episode_left, left - 1.0, places=3)

    def test_log_and_checkpoint_round_trip(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "life.jsonl")
        outcomes = Scripted([_hit()])
        sup = Supervisor(seed=3, outcomes=outcomes, log_path=path)
        plant = HomePlant()
        sup.personality.asked_home = True
        sup.step(plant, 0.0, 2.0)
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("dock_attempt", text)
        snap = sup.snapshot(plant)
        other = HomePlant()
        nxt = Supervisor(seed=3, outcomes=Scripted([]))
        nxt.restore(other, snap)
        self.assertEqual(nxt.dock_success, sup.dock_success)
        self.assertAlmostEqual(other.q_mAh, plant.q_mAh, places=5)

    def test_goes_home_as_the_pack_falls(self):
        sup = Supervisor(seed=2)
        plant = HomePlant()
        saw_dock = False
        t = 0.0
        while t < 6 * 3600 and not saw_dock:
            row = sup.step(plant, t, 5.0)
            t = plant.t
            if row["mode"] == "dock" or sup.dock_attempts:
                saw_dock = True
        self.assertTrue(saw_dock)
        self.assertGreaterEqual(plant.min_pack_v, PACK_LOW_V)
        self.assertLessEqual(plant.v_pack, PACK_FULL_V)

    def test_assistant_go_home_uses_this_loop(self):
        slow = _hit()
        slow["t_s"] = 8.0
        outcomes = Scripted([slow])
        sup = Supervisor(seed=0, outcomes=outcomes)
        plant = HomePlant()
        reply = sup.assistant.handle("go home")
        self.assertIn("APPROACH", reply["dock_states"])
        row = sup.step(plant, 0.0, 1.0)
        self.assertEqual(row["mode"], "dock")
        self.assertEqual(row["camera"], "search")
        sup.step(plant, plant.t, 8.0)
        self.assertEqual(sup.dock_success, 1)

    def test_hello_is_social(self):
        sup = Supervisor(seed=0, outcomes=Scripted([]))
        plant = HomePlant()
        plant.attention = "face"
        plant.bearing = 0.2
        sup.assistant.handle("hello")
        row = sup.step(plant, 0.0, 0.5, ["face_seen"])
        self.assertEqual(row["mode"], "social")
        self.assertNotEqual(row["expression"], "help_me")


if __name__ == "__main__":
    unittest.main()
