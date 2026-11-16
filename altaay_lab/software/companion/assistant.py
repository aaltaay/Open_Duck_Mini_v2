"""Home assistant layer for the duck.

Voice in is text here. A wake word and a speech engine plug in later.
The cloud client is the mock in mock_llm.py. Live credentials are refused.

Kid or adult mode, and how a privacy choice is shown on the body, are still
not decided here. The body for listening, thinking, speaking, done, and
refused is the personality engine. A due reminder is carried by that engine.
What the body does while seated, and when a low pack starts the existing dock
states, live in the same engine. The engine is not called from the walk thread.
"""

from __future__ import annotations

import re

from ..personality.engine import Personality, Sensors
from .mock_llm import MockCloudLLM

# Existing dock state machine (software/dock). Walk on, turn, sit.
# Not a new policy.
DOCK_WALK_TURN_SIT = ("APPROACH", "STEER_DOCK", "ACTIVATE_CHARGER")

_TIMER = re.compile(r"(\d+)\s*minute")
_CLOUD_TOOLS = ("list_inbox", "list_calendar")


class Assistant:
    def __init__(self, *, mode="kid", cloud="off", llm=None, personality=None):
        if mode not in ("kid", "adult"):
            raise ValueError("mode must be kid or adult")
        if cloud not in ("off", "mock"):
            raise ValueError("cloud must be off or mock")
        self.mode = mode
        self.cloud = cloud
        self.llm = llm if llm is not None else MockCloudLLM()
        self.timers = []
        self.reminders = []
        self.personality = personality if personality is not None else Personality(mode=mode)
        self._phase_log = []
        self._phase_bodies = {}

    def handle(self, text):
        self._phase_log = []
        self._phase_bodies = {}
        self._mark("listening")
        reply = self._route(text)
        if reply.get("refused"):
            self._mark("refused")
            final = "refused"
        else:
            self._mark("speaking")
            self._mark("done")
            final = "done"
        reply["phase"] = final
        reply["phases"] = tuple(self._phase_log)
        reply["bodies"] = dict(self._phase_bodies)
        reply["body"] = self._phase_bodies[final]
        return reply

    def reminder_due(self):
        """The stored note is due. The body looks for a person. No cloud."""
        if not self.reminders:
            return None
        self.personality.clear_assistant()
        cmd = self.personality.step(0.05, Sensors(), ["reminder_due"])
        return cmd.as_dict()

    def timer_due(self):
        """A stored timer has fired. The body startles. No cloud."""
        if not self.timers:
            return None
        self.personality.clear_assistant()
        cmd = self.personality.step(0.05, Sensors(), ["timer_fired"])
        return cmd.as_dict()

    def _mark(self, phase):
        cmd = self.personality.show_assistant(phase)
        self._phase_log.append(phase)
        self._phase_bodies[phase] = cmd.as_dict()
        return cmd

    def _route(self, text):
        lowered = " ".join(text.lower().split())
        if "timer" in lowered:
            return self._timer(lowered)
        if lowered.startswith("remind me"):
            return self._reminder(text)
        if "go home" in lowered or "go charge" in lowered:
            return self._go_home()
        if "good night" in lowered or "night light" in lowered:
            return self._night()
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

    def _go_home(self):
        self.personality.request_home()
        return self._reply(
            "I will start the dock program that is already written.",
            dock_states=DOCK_WALK_TURN_SIT,
        )

    def _night(self):
        self.personality.night_light = True
        return self._reply("Night light on.", eye_on=True)

    def _question(self, text):
        if self.mode == "kid" or self.cloud != "mock":
            return self._reply("I can set a timer or a reminder.")
        self._mark("thinking")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True)

    def _cloud_tools(self, text):
        if self.mode == "kid":
            return self._reply("Mail and calendar stay off in kid mode.", refused=True)
        if self.cloud != "mock":
            return self._reply("Mail and calendar need the cloud, and it is off.", refused=True)
        self._mark("thinking")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True, records=result["records"])

    def _reply(self, said, *, used_cloud=False, eye_on=None, dock_states=(), stored=None, records=(), refused=False):
        return {
            "said": said,
            "used_cloud": used_cloud,
            "eye_on": eye_on,
            "dock_states": tuple(dock_states),
            "stored": stored,
            "records": tuple(records),
            "refused": refused,
        }
