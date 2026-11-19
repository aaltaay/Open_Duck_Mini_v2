"""Demo checks. No hardware, no network, no credentials.

Run from the repo root so the package import is the one a caller uses.
"""

import pathlib
import unittest

from altaay_lab.software.companion.assistant import DOCK_WALK_TURN_SIT, Assistant
from altaay_lab.software.companion.mock_llm import MockCloudLLM


DOCK_FILE = pathlib.Path(__file__).resolve().parents[2] / "dock" / "autodock" / "autodock_utils.py"


class AssistantTests(unittest.TestCase):
    def test_timer_stays_local(self):
        llm = MockCloudLLM()
        bot = Assistant(mode="adult", cloud="mock", llm=llm)
        reply = bot.handle("set a timer for 5 minutes")
        self.assertEqual(bot.timers, [5])
        self.assertFalse(reply["used_cloud"])
        self.assertEqual(llm.calls, 0)
        self.assertIn("5", reply["said"])

    def test_reminder_stays_local(self):
        bot = Assistant(mode="kid", cloud="off")
        reply = bot.handle("remind me to stretch")
        self.assertEqual(bot.reminders, ["stretch"])
        self.assertEqual(reply["stored"], "reminder")
        self.assertFalse(reply["used_cloud"])

    def test_kid_question_does_not_call_cloud(self):
        llm = MockCloudLLM()
        bot = Assistant(mode="kid", cloud="mock", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 0)
        self.assertFalse(reply["used_cloud"])
        self.assertIn("timer", reply["said"])
        self.assertNotIn("thinking", reply["phases"])

    def test_adult_question_uses_mock(self):
        llm = MockCloudLLM()
        bot = Assistant(mode="adult", cloud="mock", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 1)
        self.assertTrue(reply["used_cloud"])
        self.assertIn("Mock answer", reply["said"])

    def test_offline_question_stays_local(self):
        llm = MockCloudLLM()
        bot = Assistant(mode="adult", cloud="off", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 0)
        self.assertFalse(reply["used_cloud"])

    def test_kid_mail_refused(self):
        llm = MockCloudLLM()
        bot = Assistant(mode="kid", cloud="mock", llm=llm)
        reply = bot.handle("check my email")
        self.assertEqual(llm.calls, 0)
        self.assertIn("off", reply["said"])

    def test_adult_mail_is_mock(self):
        bot = Assistant(mode="adult", cloud="mock")
        reply = bot.handle("check my email")
        self.assertTrue(reply["used_cloud"])
        self.assertEqual(reply["records"][0]["subject"], "Mock inbox note")

    def test_calendar_offline(self):
        bot = Assistant(mode="adult", cloud="off")
        reply = bot.handle("what is on my calendar")
        self.assertFalse(reply["used_cloud"])
        self.assertIn("off", reply["said"])

    def test_go_home_names_existing_dock_states(self):
        text = DOCK_FILE.read_text(encoding="utf-8")
        for name in DOCK_WALK_TURN_SIT:
            self.assertIn(name + " =", text)
        reply = Assistant(mode="kid", cloud="off").handle("go home")
        self.assertEqual(reply["dock_states"], DOCK_WALK_TURN_SIT)
        self.assertFalse(reply["used_cloud"])

    def test_night_light_uses_eye_flag(self):
        reply = Assistant(mode="kid", cloud="off").handle("good night")
        self.assertTrue(reply["eye_on"])
        self.assertFalse(reply["used_cloud"])

    def test_mock_rejects_a_credential_argument(self):
        value = "plain-value"
        with self.assertRaises(ValueError) as caught:
            MockCloudLLM().complete("hello", tools=(), api_key=value)
        self.assertNotIn(value, str(caught.exception))

    def test_unknown_cloud_is_not_a_choice(self):
        with self.assertRaises(ValueError):
            Assistant(mode="adult", cloud="vendor")

    def test_live_without_a_key_does_not_call_out(self):
        from altaay_lab.software.companion.cloud_llm import LiveCloudLLM

        llm = LiveCloudLLM(base_url="https://example.invalid/v1", model="none")
        bot = Assistant(mode="adult", cloud="live", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 0)
        self.assertFalse(reply["used_cloud"])
        self.assertNotIn("thinking", reply["phases"])
        self.assertIn("outside this repo", reply["said"])

    def test_weather_in_kid_mode_uses_the_lookup(self):
        class Lookup:
            def report(self, city):
                return "%s is 40 F and clear." % city

        bot = Assistant(mode="kid", cloud="off", weather=Lookup())
        reply = bot.handle("What is the weather in Chicago?")
        self.assertEqual(reply["stored"], "weather")
        self.assertIn("Chicago", reply["said"])
        self.assertFalse(reply["used_cloud"])
        self.assertEqual(reply["phases"], ("listening", "speaking", "done"))

    def test_weather_offline_says_so(self):
        class Down:
            def report(self, city):
                raise OSError("down")

        bot = Assistant(mode="kid", cloud="off", weather=Down(), weather_city="Chicago")
        reply = bot.handle("what is the weather")
        self.assertIn("network", reply["said"])
        self.assertFalse(reply["used_cloud"])

    def test_clock_is_local(self):
        from datetime import datetime

        bot = Assistant(mode="kid", cloud="off", clock=lambda: datetime(2026, 11, 19, 15, 5))
        reply = bot.handle("what time is it")
        self.assertEqual(reply["stored"], "time")
        self.assertIn("3:05 PM", reply["said"])
        self.assertFalse(reply["used_cloud"])

    def test_timer_fires_on_poll(self):
        now = {"t": 1000.0}
        bot = Assistant(mode="kid", cloud="off", now=lambda: now["t"])
        bot.handle("set a timer for 5 minutes")
        self.assertEqual(bot.poll(now=1000.0), [])
        fired = bot.poll(now=1000.0 + 5 * 60)
        self.assertEqual(fired[0][0], "timer")
        self.assertEqual(fired[0][1]["expression"], "startled")

    def test_reminder_in_ten_minutes(self):
        now = {"t": 50.0}
        bot = Assistant(mode="kid", cloud="off", now=lambda: now["t"])
        reply = bot.handle("remind me to stretch in 10 minutes")
        self.assertEqual(bot.reminders, ["stretch"])
        self.assertEqual(reply["stored"], "reminder")
        self.assertEqual(bot.poll(now=50.0 + 9 * 60), [])
        fired = bot.poll(now=50.0 + 10 * 60)
        self.assertEqual(fired[0][0], "reminder")
        self.assertEqual(fired[0][1]["reminder"], "search")

    def test_listening_body_is_the_tilt(self):
        reply = Assistant(mode="kid", cloud="off").handle("set a timer for 5 minutes")
        self.assertEqual(reply["bodies"]["listening"]["expression"], "curious_tilt")
        self.assertEqual(reply["bodies"]["speaking"]["expression"], "nod")
        self.assertEqual(reply["bodies"]["done"]["expression"], "settle")

    def test_kid_mail_body_is_a_shake(self):
        reply = Assistant(mode="kid", cloud="off").handle("check my email")
        self.assertEqual(reply["phase"], "refused")
        self.assertEqual(reply["bodies"]["refused"]["expression"], "shake")
        self.assertTrue(reply["bodies"]["refused"]["kid_mode"])


if __name__ == "__main__":
    unittest.main()
