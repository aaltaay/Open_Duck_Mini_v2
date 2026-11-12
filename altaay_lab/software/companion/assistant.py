"""Home assistant layer for the duck.

Voice in is text here. A wake word and a speech engine plug in later.
The cloud client is the mock in mock_llm.py. Live credentials are refused.

How kid or adult mode is chosen, how the body shows assistant state, how a
privacy choice is shown on the body, how a reminder is carried to a person,
what the body does while seated, and when to walk home beyond the guards
already written, are not decided in this file. Details held for later.
"""

from __future__ import annotations

import re

from mock_llm import MockCloudLLM

# Existing dock state machine (software/dock). Walk on, turn, sit.
# Not a new policy.
DOCK_WALK_TURN_SIT = ("APPROACH", "STEER_DOCK", "ACTIVATE_CHARGER")

_TIMER = re.compile(r"(\d+)\s*minute")
_CLOUD_TOOLS = ("list_inbox", "list_calendar")


class Assistant:
    def __init__(self, *, mode="kid", cloud="off", llm=None):
        if mode not in ("kid", "adult"):
            raise ValueError("mode must be kid or adult")
        if cloud not in ("off", "mock"):
            raise ValueError("cloud must be off or mock")
        self.mode = mode
        self.cloud = cloud
        self.llm = llm if llm is not None else MockCloudLLM()
        self.timers = []
        self.reminders = []

    def handle(self, text):
        lowered = " ".join(text.lower().split())
        if "timer" in lowered:
            return self._timer(lowered)
        if lowered.startswith("remind me"):
            return self._reminder(text)
        if "go home" in lowered or "go charge" in lowered:
            return self._reply(
                "I will start the dock program that is already written.",
                dock_states=DOCK_WALK_TURN_SIT,
            )
        if "good night" in lowered or "night light" in lowered:
            return self._reply("Night light on.", eye_on=True)
        if any(word in lowered for word in ("email", "inbox", "mail", "calendar", "schedule")):
            return self._cloud_tools(text)
        if "?" in text or lowered.startswith(("what", "who", "when", "why", "how", "where")):
            return self._question(text)
        if lowered.startswith(("hello", "hi")):
            return self._reply("Hello.")
        return self._reply("I can set a timer or a reminder.")

    def _timer(self, lowered):
        match = _TIMER.search(lowered)
        if not match:
            return self._reply("Say a timer in minutes.")
        minutes = int(match.group(1))
        self.timers.append(minutes)
        return self._reply("Timer set for %d minutes." % minutes, stored="timer")

    def _reminder(self, text):
        note = text.split(None, 2)[-1] if text.lower().startswith("remind me") else text
        note = note.strip()
        if note.lower().startswith("to "):
            note = note[3:]
        self.reminders.append(note)
        return self._reply("Reminder saved.", stored="reminder")

    def _question(self, text):
        if self.mode == "kid" or self.cloud != "mock":
            return self._reply("I can set a timer or a reminder.")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True)

    def _cloud_tools(self, text):
        if self.mode == "kid":
            return self._reply("Mail and calendar stay off in kid mode.")
        if self.cloud != "mock":
            return self._reply("Mail and calendar need the cloud, and it is off.")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True, records=result["records"])

    def _reply(self, said, *, used_cloud=False, eye_on=None, dock_states=(), stored=None, records=()):
        return {
            "said": said,
            "used_cloud": used_cloud,
            "eye_on": eye_on,
            "dock_states": tuple(dock_states),
            "stored": stored,
            "records": tuple(records),
        }
