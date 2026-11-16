"""Personality checks. No hardware, no network, no physics.

Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/personality/tests -v
"""

import math
import random
import threading
import unittest

from altaay_lab.software.companion.assistant import DOCK_WALK_TURN_SIT, Assistant
from altaay_lab.software.dock.autodock.autodock_utils import DockState
from altaay_lab.software.personality.engine import (
    AROUSAL_BASE,
    BLEND_RATE_RAD_S,
    TAU_VALENCE_S,
    VALENCE_BASE,
    Personality,
    Sensors,
    _decay,
)
from altaay_lab.software.personality.expressions import BLINKS, NAMES
from altaay_lab.software.personality.limits import (
    ANTENNA_HI,
    ANTENNA_LO,
    DOCK_HOME,
    HEAD_JOINTS,
    HEAD_RATE_RAD_S,
    HOME_PACK_V,
    JOYSTICK_RAD,
    PACK_FULL_V,
    PACK_WALK_STOP_V,
    energy_from_pack,
    load_box,
)


def _full():
    return Sensors(pack_v=12.2, idle_s=1.0)


class LimitTests(unittest.TestCase):
    def test_box_is_the_tighter_end(self):
        box = load_box()
        neck = box.joints["neck_pitch"]
        self.assertLess(neck.hi, JOYSTICK_RAD["neck_pitch"][1])
        self.assertAlmostEqual(neck.hi, math.radians(22.0), places=6)
        yaw = box.joints["head_yaw"]
        self.assertAlmostEqual(yaw.lo, -1.5, places=6)
        self.assertLess(yaw.hi, 1.5)
        self.assertAlmostEqual(yaw.hi, math.radians(79.0), places=6)

    def test_pack_energy_is_the_cited_span(self):
        self.assertAlmostEqual(energy_from_pack(PACK_WALK_STOP_V), 0.0)
        self.assertAlmostEqual(energy_from_pack(PACK_FULL_V), 1.0)
        self.assertAlmostEqual(energy_from_pack(HOME_PACK_V), (10.8 - 10.0) / (12.6 - 10.0))

    def test_commands_stay_inside_and_under_the_rate(self):
        box = load_box()
        rng = random.Random(0)
        events = [
            "wake_word", "face_seen", "face_lost", "petted", "picked_up",
            "timer_fired", "reminder_due", "low_battery", "charging_started",
            "charging_finished", "idle_time", "fell_over", "stood_up",
            "knee_heat_rest", "knee_heat_cool",
        ]
        duck = Personality(seed=0, blend_rate=100.0)
        prev = None
        dt = 0.02
        for _ in range(400):
            ev = [rng.choice(events)] if rng.random() < 0.25 else []
            sensors = Sensors(
                pack_v=rng.uniform(9.2, 12.6),
                servo_median_v=rng.choice([None, rng.uniform(5.5, 8.0)]),
                knee_c=rng.choice([None, 30.0, 50.0, 56.0, 44.0]),
                idle_s=rng.uniform(0.0, 40.0),
                posture=rng.choice(["standing", "walking", "sitting"]),
                bearing_rad=rng.uniform(-2.0, 2.0),
                elevation_rad=rng.uniform(-1.0, 1.0),
                attention=rng.choice(["none", "face", "sound"]),
                face_close=rng.random() < 0.2,
            )
            cmd = duck.step(dt, sensors, ev)
            for name in HEAD_JOINTS:
                value = getattr(cmd, name)
                self.assertTrue(box.holds_joint(name, value))
                self.assertGreaterEqual(value, JOYSTICK_RAD[name][0] - 1e-9)
                self.assertLessEqual(value, JOYSTICK_RAD[name][1] + 1e-9)
            self.assertGreaterEqual(cmd.antenna_left, ANTENNA_LO)
            self.assertLessEqual(cmd.antenna_left, ANTENNA_HI)
            self.assertGreaterEqual(cmd.antenna_right, ANTENNA_LO)
            self.assertLessEqual(cmd.antenna_right, ANTENNA_HI)
            self.assertGreaterEqual(cmd.eye_brightness, 0.0)
            self.assertLessEqual(cmd.eye_brightness, 1.0)
            self.assertEqual(cmd.eye_color, "white")
            self.assertIn(cmd.blink, BLINKS)
            self.assertIn(cmd.expression, NAMES)
            self.assertIn(cmd.intent, ("none", "walk_to_person", "go_home", "sit", "nap"))
            if prev is not None:
                for name in HEAD_JOINTS:
                    moved = abs(getattr(cmd, name) - getattr(prev, name))
                    self.assertLessEqual(moved, HEAD_RATE_RAD_S * dt + 1e-9)
            prev = cmd

    def test_default_blend_is_slower_than_the_cited_clip(self):
        self.assertLess(BLEND_RATE_RAD_S, HEAD_RATE_RAD_S)
        duck = Personality(seed=1)
        duck.step(0.05, _full(), ["face_seen"])
        first = duck.head["head_yaw"]
        duck.step(0.02, Sensors(pack_v=12.2, bearing_rad=1.2, attention="face"))
        moved = abs(duck.head["head_yaw"] - first)
        self.assertLessEqual(moved, BLEND_RATE_RAD_S * 0.02 + 1e-9)


class DecayTests(unittest.TestCase):
    def test_valence_matches_the_exp_decay(self):
        duck = Personality(seed=1)
        duck.valence = 1.0
        dt = 0.1
        expected = 1.0
        for _ in range(50):
            duck.step(dt, _full())
            expected = _decay(expected, VALENCE_BASE, dt, TAU_VALENCE_S)
            self.assertAlmostEqual(duck.valence, expected, places=9)

    def test_arousal_moves_toward_the_base(self):
        duck = Personality(seed=1)
        duck.arousal = 1.0
        for _ in range(40):
            duck.step(0.2, _full())
        self.assertLess(duck.arousal, 0.6)
        self.assertGreater(duck.arousal, AROUSAL_BASE)


class ArbitrationTests(unittest.TestCase):
    def test_fall_beats_low_pack_and_a_face(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(pack_v=10.4, bearing_rad=0.4, attention="face"), ["fell_over", "face_seen"])
        self.assertEqual(cmd.priority, "safety")
        self.assertEqual(cmd.intent, "sit")
        self.assertEqual(cmd.dock_states, ())
        self.assertEqual(cmd.expression, "startled")

    def test_knee_heat_beats_a_face_until_it_is_cool(self):
        duck = Personality(seed=1)
        hot = duck.step(0.1, Sensors(pack_v=12.4, knee_c=56.0), ["face_seen"])
        self.assertEqual(hot.priority, "safety")
        self.assertEqual(hot.intent, "sit")
        held = duck.step(0.1, Sensors(pack_v=12.4, knee_c=50.0, bearing_rad=0.2, attention="face"))
        self.assertEqual(held.priority, "safety")
        cool = duck.step(0.1, Sensors(pack_v=12.4, knee_c=44.0, bearing_rad=0.2, attention="face"), ["face_seen"])
        self.assertEqual(cool.priority, "social")

    def test_hard_battery_does_not_walk_home(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(pack_v=9.9), ["face_seen"])
        self.assertEqual(cmd.priority, "safety")
        self.assertEqual(cmd.intent, "sit")
        self.assertEqual(cmd.dock_states, ())
        servo = Personality(seed=1).step(0.1, Sensors(servo_median_v=5.9), ["face_seen"])
        self.assertEqual(servo.priority, "safety")

    def test_low_pack_goes_home_ahead_of_a_face(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(pack_v=10.4, bearing_rad=0.3, attention="face"), ["face_seen"])
        self.assertEqual(cmd.priority, "needs")
        self.assertEqual(cmd.intent, "go_home")
        self.assertEqual(cmd.expression, "sleepy_droop")
        self.assertEqual(cmd.dock_states, DOCK_HOME)
        self.assertEqual(cmd.dock_states, DOCK_WALK_TURN_SIT)
        for name in DOCK_HOME:
            self.assertTrue(hasattr(DockState, name))

    def test_servo_median_below_start_min_goes_home(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(servo_median_v=6.4))
        self.assertEqual(cmd.intent, "go_home")
        self.assertEqual(cmd.priority, "needs")

    def test_full_pack_does_not_go_home(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(pack_v=12.4, idle_s=2.0))
        self.assertNotEqual(cmd.intent, "go_home")
        self.assertEqual(cmd.priority, "idle")

    def test_charging_does_not_walk_away(self):
        duck = Personality(seed=1)
        duck.step(0.1, Sensors(pack_v=10.4), ["charging_started"])
        cmd = duck.step(0.1, Sensors(pack_v=10.4))
        self.assertNotEqual(cmd.intent, "go_home")
        self.assertEqual(cmd.intent, "nap")
        social = duck.step(0.1, Sensors(pack_v=10.4, bearing_rad=0.2, attention="face"), ["face_seen"])
        self.assertEqual(social.priority, "social")
        self.assertNotEqual(social.intent, "go_home")

    def test_face_lost_wins_over_a_stale_attention_reading(self):
        duck = Personality(seed=1)
        duck.step(0.1, Sensors(pack_v=12.4, bearing_rad=0.3, attention="face"), ["face_seen"])
        cmd = duck.step(0.1, Sensors(pack_v=12.4, bearing_rad=0.3, attention="face"), ["face_lost"])
        self.assertFalse(duck.face_on)
        self.assertNotEqual(cmd.reason, "face")
        self.assertNotEqual(cmd.expression, "look_at")

    def test_face_beats_idle(self):
        duck = Personality(seed=1)
        cmd = duck.step(0.1, Sensors(pack_v=12.4, bearing_rad=0.4, attention="face", idle_s=30.0), ["face_seen"])
        self.assertEqual(cmd.priority, "social")
        self.assertEqual(cmd.expression, "greeting")

    def test_reminder_is_carried_to_a_person(self):
        duck = Personality(seed=1)
        search = duck.step(0.1, _full(), ["reminder_due"])
        self.assertEqual(search.reminder, "search")
        self.assertEqual(search.expression, "bored_glance")
        self.assertEqual(search.intent, "none")
        approach = duck.step(0.1, Sensors(pack_v=12.2, bearing_rad=0.5, attention="face"), ["face_seen"])
        self.assertEqual(approach.reminder, "approach")
        self.assertEqual(approach.intent, "walk_to_person")
        self.assertEqual(approach.priority, "social")
        done = duck.step(0.1, Sensors(pack_v=12.2, bearing_rad=0.1, attention="face", face_close=True))
        self.assertEqual(done.reminder, "delivered")
        self.assertEqual(done.expression, "nod")
        self.assertEqual(done.intent, "none")

    def test_seated_is_alert_then_a_nap(self):
        duck = Personality(seed=2)
        for _ in range(15):
            alert = duck.step(0.1, Sensors(pack_v=12.4, posture="sitting", idle_s=1.0))
        self.assertEqual(alert.intent, "sit")
        self.assertEqual(alert.expression, "seated_alert")
        self.assertGreater(alert.neck_pitch, 0.05)
        duck.arousal = 0.08
        for _ in range(15):
            nap = duck.step(0.1, Sensors(pack_v=12.4, posture="sitting", idle_s=40.0))
        self.assertEqual(nap.intent, "nap")
        self.assertEqual(nap.expression, "sleepy_droop")
        self.assertLess(nap.neck_pitch, 0.0)

    def test_low_arousal_while_standing_is_drowsy(self):
        duck = Personality(seed=1)
        duck.arousal = 0.08
        cmd = duck.step(0.1, _full())
        self.assertEqual(cmd.expression, "sleepy_droop")
        self.assertEqual(cmd.reason, "idle drowsy")


class SeedTests(unittest.TestCase):
    def _run(self, seed):
        duck = Personality(seed=seed)
        out = []
        for i in range(25):
            sensors = Sensors(pack_v=12.3, idle_s=4.0, bearing_rad=0.2 * ((i % 5) - 2))
            events = ["face_seen"] if i == 3 else []
            out.append(duck.step(0.1, sensors, events).as_dict())
        return out

    def test_same_seed_matches(self):
        self.assertEqual(self._run(7), self._run(7))

    def test_other_seed_is_a_different_glance(self):
        a = Personality(seed=1)
        b = Personality(seed=2)
        self.assertNotEqual((a.glance_sign, a.glance_phase), (b.glance_sign, b.glance_phase))
        self.assertNotEqual(self._run(1), self._run(2))


class ThreadTests(unittest.TestCase):
    def test_step_refuses_the_walk_thread(self):
        duck = Personality(seed=1)
        duck.bind_walk_thread()
        box = {}

        def other():
            try:
                box["cmd"] = duck.step(0.1, _full())
            except Exception as exc:
                box["err"] = exc

        thread = threading.Thread(target=other)
        thread.start()
        thread.join()
        self.assertNotIn("err", box)
        self.assertEqual(box["cmd"].priority, "idle")
        with self.assertRaises(RuntimeError):
            duck.step(0.1, _full())


class AssistantBodyTests(unittest.TestCase):
    def test_phases_show_on_the_body(self):
        reply = Assistant(mode="kid", cloud="off").handle("hello")
        self.assertEqual(reply["phases"], ("listening", "speaking", "done"))
        self.assertEqual(reply["bodies"]["listening"]["expression"], "curious_tilt")
        self.assertEqual(reply["bodies"]["speaking"]["expression"], "nod")
        self.assertEqual(reply["bodies"]["done"]["expression"], "settle")
        self.assertEqual(reply["bodies"]["listening"]["eye_color"], "white")
        self.assertFalse(reply["used_cloud"])

    def test_thinking_shows_only_when_the_mock_runs(self):
        reply = Assistant(mode="adult", cloud="mock").handle("What is a duck?")
        self.assertIn("thinking", reply["phases"])
        self.assertEqual(reply["bodies"]["thinking"]["expression"], "look_at")
        self.assertTrue(reply["used_cloud"])
        kid = Assistant(mode="kid", cloud="mock").handle("What is a duck?")
        self.assertNotIn("thinking", kid["phases"])
        self.assertFalse(kid["used_cloud"])

    def test_kid_mail_is_a_shake(self):
        reply = Assistant(mode="kid", cloud="mock").handle("check my email")
        self.assertTrue(reply["refused"])
        self.assertEqual(reply["phases"], ("listening", "refused"))
        self.assertEqual(reply["body"]["expression"], "shake")
        self.assertEqual(reply["body"]["eye_color"], "white")
        self.assertFalse(reply["used_cloud"])

    def test_go_home_uses_the_need_not_a_new_policy(self):
        reply = Assistant(mode="kid", cloud="off").handle("go home")
        self.assertEqual(reply["dock_states"], DOCK_WALK_TURN_SIT)
        self.assertEqual(reply["body"]["intent"], "go_home")
        self.assertEqual(reply["body"]["priority"], "needs")
        self.assertEqual(reply["body"]["dock_states"], DOCK_HOME)
        self.assertFalse(reply["used_cloud"])

    def test_night_light_stays_white_and_on(self):
        reply = Assistant(mode="kid", cloud="off").handle("good night")
        self.assertTrue(reply["eye_on"])
        self.assertGreaterEqual(reply["body"]["eye_brightness"], 0.75)
        self.assertEqual(reply["body"]["eye_color"], "white")

    def test_due_reminder_and_timer_stay_local(self):
        bot = Assistant(mode="kid", cloud="off")
        bot.handle("remind me to stretch")
        carried = bot.reminder_due()
        self.assertEqual(carried["reminder"], "search")
        self.assertTrue(carried["kid_mode"])
        bot.handle("set a timer for 5 minutes")
        fired = bot.timer_due()
        self.assertEqual(fired["expression"], "startled")
        self.assertEqual(bot.personality.mode, "kid")


if __name__ == "__main__":
    unittest.main()
