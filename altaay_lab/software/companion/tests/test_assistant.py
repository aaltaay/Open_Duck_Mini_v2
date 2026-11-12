"""Demo checks. No hardware, no network, no credentials."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import assistant
from mock_llm import MockCloudLLM


DOCK_FILE = pathlib.Path(__file__).resolve().parents[2] / "dock" / "autodock" / "autodock_utils.py"


class AssistantTests(unittest.TestCase):
    def test_timer_stays_local(self):
        llm = MockCloudLLM()
        bot = assistant.Assistant(mode="adult", cloud="mock", llm=llm)
        reply = bot.handle("set a timer for 5 minutes")
        self.assertEqual(bot.timers, [5])
        self.assertFalse(reply["used_cloud"])
        self.assertEqual(llm.calls, 0)
        self.assertIn("5", reply["said"])

    def test_reminder_stays_local(self):
        bot = assistant.Assistant(mode="kid", cloud="off")
        reply = bot.handle("remind me to stretch")
        self.assertEqual(bot.reminders, ["stretch"])
        self.assertEqual(reply["stored"], "reminder")
        self.assertFalse(reply["used_cloud"])

    def test_kid_question_does_not_call_cloud(self):
        llm = MockCloudLLM()
        bot = assistant.Assistant(mode="kid", cloud="mock", llm=llm)
        reply = bot.handle("What is the weather?")
        self.assertEqual(llm.calls, 0)
        self.assertFalse(reply["used_cloud"])
        self.assertIn("timer", reply["said"])

    def test_adult_question_uses_mock(self):
        llm = MockCloudLLM()
        bot = assistant.Assistant(mode="adult", cloud="mock", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 1)
        self.assertTrue(reply["used_cloud"])
        self.assertIn("Mock answer", reply["said"])

    def test_offline_question_stays_local(self):
        llm = MockCloudLLM()
        bot = assistant.Assistant(mode="adult", cloud="off", llm=llm)
        reply = bot.handle("What is a duck?")
        self.assertEqual(llm.calls, 0)
        self.assertFalse(reply["used_cloud"])

    def test_kid_mail_refused(self):
        llm = MockCloudLLM()
        bot = assistant.Assistant(mode="kid", cloud="mock", llm=llm)
        reply = bot.handle("check my email")
        self.assertEqual(llm.calls, 0)
        self.assertIn("off", reply["said"])

    def test_adult_mail_is_mock(self):
        bot = assistant.Assistant(mode="adult", cloud="mock")
        reply = bot.handle("check my email")
        self.assertTrue(reply["used_cloud"])
        self.assertEqual(reply["records"][0]["subject"], "Mock inbox note")

    def test_calendar_offline(self):
        bot = assistant.Assistant(mode="adult", cloud="off")
        reply = bot.handle("what is on my calendar")
        self.assertFalse(reply["used_cloud"])
        self.assertIn("off", reply["said"])

    def test_go_home_names_existing_dock_states(self):
        text = DOCK_FILE.read_text(encoding="utf-8")
        for name in assistant.DOCK_WALK_TURN_SIT:
            self.assertIn(name + " =", text)
        reply = assistant.Assistant(mode="kid", cloud="off").handle("go home")
        self.assertEqual(reply["dock_states"], assistant.DOCK_WALK_TURN_SIT)
        self.assertFalse(reply["used_cloud"])

    def test_night_light_uses_eye_flag(self):
        reply = assistant.Assistant(mode="kid", cloud="off").handle("good night")
        self.assertTrue(reply["eye_on"])
        self.assertFalse(reply["used_cloud"])

    def test_mock_rejects_a_credential_argument(self):
        value = "plain-value"
        with self.assertRaises(ValueError) as caught:
            MockCloudLLM().complete("hello", tools=(), api_key=value)
        self.assertNotIn(value, str(caught.exception))

    def test_live_cloud_is_not_a_choice(self):
        with self.assertRaises(ValueError):
            assistant.Assistant(mode="adult", cloud="live")


if __name__ == "__main__":
    unittest.main()
