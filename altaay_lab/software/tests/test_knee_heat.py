"""Knee heat guard, no hardware and no Runtime.

Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/tests -v
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, os.path.dirname(HERE))
import knee_heat as K  # noqa: E402


def feed(g, samples):
    """samples: (t, temp or None, posture). One servo, id 13, unless temp is a dict."""
    out = []
    decisions = []
    for t, temp, posture in samples:
        temps = {} if temp is None else (temp if isinstance(temp, dict) else {13: temp})
        d = g.update(t, temps, posture)
        decisions.append(d)
        out += d.events
    return out, decisions


class RisingKnee(unittest.TestCase):
    def test_second_reading_at_55_warns_and_stops(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 54.0, "walking"),
            (0.5, 55.0, "walking"),
            (1.0, 55.0, "walking"),
        ])
        self.assertEqual([e["event"] for e in events], ["warn_stop", "torque_off"])
        self.assertEqual(events[0]["servo"], 13)
        self.assertEqual(events[0]["temp_c"], 55.0)
        self.assertEqual(events[0]["threshold_c"], 55.0)
        self.assertEqual(dec[0].torque, "allow")
        self.assertEqual(dec[1].torque, "allow")
        self.assertEqual(dec[2].torque, "off")
        self.assertTrue(g.latched)

    def test_does_not_resume_until_two_readings_strictly_below_45(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 55.0, "walking"),
            (0.5, 55.0, "walking"),
            (1.0, 50.0, "walking"),
            (1.5, 45.0, "walking"),
            (2.0, 45.0, "walking"),
            (2.5, 44.9, "walking"),
            (3.0, 44.9, "walking"),
        ])
        names = [e["event"] for e in events]
        self.assertEqual(names, ["warn_stop", "torque_off", "resume"])
        self.assertEqual(events[-1]["temp_c"], 44.9)
        self.assertEqual(events[-1]["threshold_c"], 45.0)
        self.assertEqual(dec[3].torque, "off")
        self.assertEqual(dec[4].torque, "off")
        self.assertEqual(dec[5].torque, "off")
        self.assertEqual(dec[6].torque, "allow")
        self.assertFalse(g.latched)

    def test_one_spike_does_not_stop(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 40.0, "walking"),
            (0.5, 90.0, "walking"),
            (1.0, 40.0, "walking"),
        ])
        self.assertEqual(events, [])
        self.assertTrue(all(d.torque == "allow" for d in dec))
        self.assertFalse(g.latched)

    def test_implausible_reading_is_dropped(self):
        g = K.KneeHeatGuard()
        events, _ = feed(g, [
            (0.0, 200.0, "walking"),
            (0.5, -1.0, "walking"),
            (1.0, 40.0, "walking"),
        ])
        self.assertEqual(events, [])
        self.assertEqual(g.dropped, 2)

    def test_empty_samples_do_not_clear_a_rest(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 55.0, "walking"),
            (0.5, 55.0, "walking"),
            (1.0, None, "walking"),
            (1.5, None, "walking"),
            (2.0, 40.0, "walking"),
            (2.5, 40.0, "walking"),
        ])
        self.assertEqual([e["event"] for e in events], ["warn_stop", "torque_off", "resume"])
        self.assertEqual(dec[2].torque, "off")
        self.assertEqual(dec[3].torque, "off")
        self.assertEqual(dec[5].torque, "allow")


class IdleAndSit(unittest.TestCase):
    def test_idle_and_sitting_are_torque_off_when_cool(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 30.0, "idle"),
            (0.5, 30.0, "idle"),
            (1.0, 30.0, "sitting"),
        ])
        self.assertEqual([e["event"] for e in events], ["torque_off"])
        self.assertTrue(all(d.torque == "off" for d in dec))
        self.assertFalse(g.latched)

    def test_unknown_posture_is_idle(self):
        g = K.KneeHeatGuard()
        _, dec = feed(g, [(0.0, 30.0, "flying")])
        self.assertEqual(dec[0].torque, "off")

    def test_sit_while_hot_then_walk_only_after_it_cools(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, 60.0, "sitting"),
            (0.5, 60.0, "sitting"),
            (1.0, 40.0, "sitting"),
            (1.5, 40.0, "sitting"),
            (2.0, 40.0, "walking"),
        ])
        names = [e["event"] for e in events]
        self.assertEqual(names[0], "torque_off")
        self.assertIn("warn_stop", names)
        self.assertEqual(names[-1], "resume")
        self.assertEqual(dec[2].torque, "off")
        self.assertEqual(dec[3].torque, "off")
        self.assertEqual(dec[4].torque, "allow")

    def test_cool_streak_while_sitting_allows_the_next_walk(self):
        """Two cool reads during the sit count. The walk call may resume."""
        g = K.KneeHeatGuard()
        _, dec = feed(g, [
            (0.0, 55.0, "sitting"),
            (0.5, 55.0, "sitting"),
            (1.0, 40.0, "sitting"),
            (1.5, 40.0, "sitting"),
            (2.0, 40.0, "walking"),
        ])
        self.assertEqual(dec[-1].torque, "allow")

    def test_a_new_rise_stops_again_after_a_resume(self):
        g = K.KneeHeatGuard()
        events, _ = feed(g, [
            (0.0, 55.0, "walking"),
            (0.5, 55.0, "walking"),
            (1.0, 40.0, "walking"),
            (1.5, 40.0, "walking"),
            (2.0, 55.0, "walking"),
            (2.5, 55.0, "walking"),
        ])
        self.assertEqual([e["event"] for e in events],
                         ["warn_stop", "torque_off", "resume", "warn_stop", "torque_off"])


class AnyServo(unittest.TestCase):
    def test_a_head_servo_stops_the_walk_too(self):
        g = K.KneeHeatGuard()
        events, dec = feed(g, [
            (0.0, {33: 55.0}, "walking"),
            (0.5, {33: 55.0}, "walking"),
        ])
        self.assertEqual(events[0]["event"], "warn_stop")
        self.assertEqual(events[0]["servo"], 33)
        self.assertEqual(dec[-1].torque, "off")

    def test_staggered_reads_confirm_on_one_servo(self):
        g = K.KneeHeatGuard()
        d1 = g.update(0.0, {23: 55.0, 13: 40.0}, "walking")
        d2 = g.update(0.5, {13: 40.0}, "walking")
        d3 = g.update(1.0, {23: 56.0}, "walking")
        self.assertEqual(d1.torque, "allow")
        self.assertEqual(d2.events, [])
        self.assertEqual(d3.events[0]["event"], "warn_stop")
        self.assertEqual(d3.events[0]["servo"], 23)

    def test_start_refuses_at_55(self):
        g = K.KneeHeatGuard()
        ok, hot = g.check_start({13: 54.0, 23: 55.0})
        self.assertFalse(ok)
        self.assertEqual(hot, {23: 55.0})
        ok, hot = g.check_start({13: 30.0})
        self.assertTrue(ok)
        self.assertEqual(hot, {})
        self.assertFalse(g.latched)


class Gate(unittest.TestCase):
    def test_off_skips_writes_and_on_allows_them(self):
        class Hwi:
            def __init__(self):
                self.off = 0
                self.on = 0

            def turn_off(self):
                self.off += 1

            def turn_on(self):
                self.on += 1

        hwi = Hwi()
        gate = K.TorqueGate()
        sent = []

        def write(pos):
            sent.append(pos)
            return pos

        g = K.KneeHeatGuard()
        d = g.update(0.0, {13: 30.0}, "walking")
        gate.apply(hwi, d)
        self.assertEqual(gate.filter_write(hwi, [1], write), [1])
        d = g.update(0.5, {13: 30.0}, "idle")
        gate.apply(hwi, d)
        self.assertIsNone(gate.filter_write(hwi, [2], write))
        self.assertEqual(hwi.off, 1)
        self.assertEqual(sent, [[1]])
        d = g.update(1.0, {13: 30.0}, "walking")
        gate.apply(hwi, d)
        self.assertEqual(gate.filter_write(hwi, [3], write), [3])
        self.assertEqual(hwi.on, 1)
        self.assertEqual(gate.skipped, 1)
        self.assertEqual(gate.writes, 2)

    def test_turn_off_failure_is_not_swallowed(self):
        class Hwi:
            def turn_off(self):
                raise RuntimeError("bus")

        gate = K.TorqueGate()
        g = K.KneeHeatGuard()
        d = g.update(0.0, {13: 30.0}, "sitting")
        with self.assertRaises(K.TorqueOffFailed):
            gate.apply(Hwi(), d)
        self.assertEqual(gate.failures, 1)
        self.assertTrue(gate.hold_off)


class Coverage(unittest.TestCase):
    def test_a_cool_group_does_not_clear_a_hot_knee(self):
        g = K.KneeHeatGuard(watched=(13, 23, 33))
        g.update(0.0, {13: 55.0}, "walking")
        d = g.update(0.5, {13: 55.0}, "walking")
        self.assertEqual(d.events[0]["event"], "warn_stop")
        g.update(1.0, {23: 30.0, 33: 30.0}, "walking")
        d = g.update(1.5, {23: 30.0, 33: 30.0}, "walking")
        self.assertTrue(g.latched)
        self.assertEqual(d.torque, "off")
        self.assertNotIn("resume", [e["event"] for e in g.events])

    def test_missing_knee_replies_do_not_restart(self):
        g = K.KneeHeatGuard(watched=(13, 23))
        g.update(0.0, {13: 55.0}, "walking")
        g.update(0.5, {13: 55.0}, "walking")
        g.update(1.0, {23: 30.0}, "walking")
        d = g.update(1.5, {23: 30.0}, "walking")
        self.assertTrue(g.latched)
        self.assertEqual(d.torque, "off")

    def test_each_servo_must_cool_twice_after_the_stop(self):
        g = K.KneeHeatGuard(watched=(13, 23))
        g.update(0.0, {13: 55.0}, "walking")
        g.update(0.5, {13: 55.0}, "walking")
        g.update(1.0, {23: 30.0}, "walking")
        g.update(1.5, {23: 30.0}, "walking")
        g.update(2.0, {13: 40.0}, "walking")
        d = g.update(2.5, {13: 40.0}, "walking")
        self.assertFalse(g.latched)
        self.assertEqual(d.torque, "allow")
        self.assertEqual(d.events[-1]["event"], "resume")

    def test_restart_must_be_below_the_stop(self):
        with self.assertRaises(ValueError):
            K.KneeHeatGuard(warn_c=55.0, restart_c=55.0)


class BootPath(unittest.TestCase):
    def test_service_starts_the_guard(self):
        path = os.path.join(os.path.dirname(HERE), "odm-walk-guard.service")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("--knee-heat", text)
        self.assertIn("walk_with_guard.py", text)

    def test_walk_program_calls_the_guard(self):
        path = os.path.join(os.path.dirname(HERE), "..", "bench", "walk_with_guard.py")
        with open(os.path.normpath(path), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("--knee-heat", text)
        self.assertIn("knee_heat", text)
        self.assertIn("KneeHeatGuard", text)


if __name__ == "__main__":
    unittest.main()
