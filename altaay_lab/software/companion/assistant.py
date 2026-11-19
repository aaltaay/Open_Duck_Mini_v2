"""Home assistant layer for the duck.

Text in, or the voice pipeline in pipeline.py. Timers, reminders, the clock,
and weather are local skills. Weather calls Open-Meteo only when a city is
known and the network works. It does not use a key.

Open questions, mail, and calendar use the cloud flag: off, mock, or live.
Live reads a key from the environment named in the config. The key is never
stored here. Kid mode does not call the cloud.

The body for listening, thinking, speaking, done, and refused is the
personality engine. Thinking is only for the chat model. A due reminder is
carried by that engine. The engine is not called from the walk thread.
"""

from __future__ import annotations

import re
import time
from datetime import datetime

from ..personality.engine import Personality
from .mock_llm import MockCloudLLM

# Existing dock state machine (software/dock). Walk on, turn, sit.
# Not a new policy.
DOCK_WALK_TURN_SIT = ("APPROACH", "STEER_DOCK", "ACTIVATE_CHARGER")

_WORD_NUM = {
    "a": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
}
_NUM = r"(\d+|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|forty|fifty|sixty)"
_TIMER = re.compile(_NUM + r"\s*(minute|minutes|min|second|seconds|sec)\b")
_IN = re.compile(r"\bin\s+" + _NUM + r"\s+(minute|minutes|min|second|seconds|sec)\b")
_CITY = re.compile(r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z .'-]{1,40})", re.IGNORECASE)
_CLOUD_TOOLS = ("list_inbox", "list_calendar")


def _number(token):
    if token.isdigit():
        return int(token)
    if token not in _WORD_NUM:
        raise ValueError("not a number")
    return _WORD_NUM[token]


def _norm(text):
    cleaned = text.lower().replace("'", "")
    cleaned = re.sub(r"[^a-z0-9 ?]", " ", cleaned)
    return " ".join(cleaned.split())


class Assistant:
    def __init__(
        self,
        *,
        mode="kid",
        cloud="off",
        llm=None,
        personality=None,
        weather=None,
        weather_city="",
        now=None,
        clock=None,
    ):
        if mode not in ("kid", "adult"):
            raise ValueError("mode must be kid or adult")
        if cloud not in ("off", "mock", "live"):
            raise ValueError("cloud must be off, mock, or live")
        self.mode = mode
        self.cloud = cloud
        self.llm = llm if llm is not None else MockCloudLLM()
        self.timers = []
        self.timer_jobs = []
        self.reminders = []
        self.reminder_jobs = []
        self.weather = weather
        self.weather_city = " ".join((weather_city or "").split())
        self.now = now or time.time
        self.clock = clock or datetime.now
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

    def poll(self, now=None):
        """Fire stored timers and timed reminders. No cloud."""
        moment = self.now() if now is None else now
        fired = []
        for job in self.timer_jobs:
            if job["due"] is not None and not job["fired"] and moment >= job["due"]:
                job["fired"] = True
                fired.append(("timer", self.timer_due()))
        for job in self.reminder_jobs:
            if job["due"] is not None and not job["fired"] and moment >= job["due"]:
                job["fired"] = True
                fired.append(("reminder", self.reminder_due()))
        return fired

    def reminder_due(self):
        """The stored note is due. The body looks for a person. No cloud."""
        if not self.reminders and not self.reminder_jobs:
            return None
        self.personality.clear_assistant()
        cmd = self.personality.step(0.05, None, ["reminder_due"])
        return cmd.as_dict()

    def timer_due(self):
        """A stored timer has fired. The body startles. No cloud."""
        if not self.timers and not self.timer_jobs:
            return None
        self.personality.clear_assistant()
        cmd = self.personality.step(0.05, None, ["timer_fired"])
        return cmd.as_dict()

    def _mark(self, phase):
        cmd = self.personality.show_assistant(phase)
        self._phase_log.append(phase)
        self._phase_bodies[phase] = cmd.as_dict()
        return cmd

    def _route(self, text):
        lowered = _norm(text)
        if "timer" in lowered:
            return self._timer(lowered)
        if lowered.startswith("remind me"):
            return self._reminder(text, lowered)
        if "go home" in lowered or "go charge" in lowered:
            return self._go_home()
        if "good night" in lowered or "night light" in lowered:
            return self._night()
        if "weather" in lowered:
            return self._weather(text)
        if self._is_clock(lowered):
            return self._clock()
        if any(word in lowered for word in ("email", "inbox", "mail", "calendar", "schedule")):
            return self._cloud_tools(text)
        if "?" in text or lowered.startswith(("what", "who", "when", "why", "how", "where")):
            return self._question(text)
        if lowered.startswith(("hello", "hi")):
            return self._reply("Hello.")
        return self._reply("I can set a timer or a reminder.")

    def _is_clock(self, lowered):
        if "timer" in lowered or "weather" in lowered:
            return False
        if "time" not in lowered:
            return False
        return (
            lowered.startswith(("what", "whats"))
            or "time is" in lowered
            or lowered in ("time", "the time", "tell me the time")
        )

    def _timer(self, lowered):
        match = _TIMER.search(lowered)
        if not match:
            return self._reply("Say a timer in minutes.")
        count = _number(match.group(1))
        unit = match.group(2)
        if unit.startswith("min"):
            self.timers.append(count)
            seconds = count * 60
            said = "Timer set for %d minutes." % count
        else:
            seconds = count
            said = "Timer set for %d seconds." % count
        self.timer_jobs.append({"seconds": seconds, "due": self.now() + seconds, "fired": False})
        return self._reply(said, stored="timer")

    def _reminder(self, text, lowered):
        note = text
        if lowered.startswith("remind me"):
            note = text.strip()
            # Drop the leading words from the original so the note keeps its case.
            parts = note.split(None, 2)
            note = parts[-1] if len(parts) >= 3 else ""
        note = note.strip()
        if note.lower().startswith("to "):
            note = note[3:]
        delay = None
        found = _IN.search(_norm(note))
        if found:
            count = _number(found.group(1))
            delay = count * 60 if found.group(2).startswith("min") else count
            note = _IN.sub(" ", _norm(note))
            note = " ".join(note.split()).strip()
        if not note:
            return self._reply("Say what I should remember.")
        self.reminders.append(note)
        self.reminder_jobs.append({"note": note, "due": None if delay is None else self.now() + delay, "fired": False})
        if delay is None:
            return self._reply("Reminder saved.", stored="reminder")
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

    def _city(self, text):
        match = _CITY.search(text.replace("'", ""))
        if not match:
            return ""
        city = match.group(1).strip(" .")
        low = city.lower()
        for stop in (" today", " now", " please"):
            if low.endswith(stop):
                city = city[: -len(stop)].strip()
                low = city.lower()
        return " ".join(city.split())

    def _weather(self, text):
        city = self._city(text) or self.weather_city
        if not city:
            return self._reply("Which city?")
        if self.weather is None:
            return self._reply("Weather needs the network.")
        try:
            said = self.weather.report(city)
        except (OSError, ValueError, TimeoutError):
            return self._reply("Weather needs the network.")
        if not said:
            return self._reply("I could not find that city.")
        return self._reply(said, stored="weather")

    def _clock(self):
        moment = self.clock()
        text = moment.strftime("%I:%M %p").lstrip("0")
        return self._reply("It is %s." % text, stored="time")

    def _cloud_ready(self):
        ready = getattr(self.llm, "ready", None)
        if ready is None:
            return True
        return bool(ready())

    def _question(self, text):
        if self.mode == "kid" or self.cloud == "off":
            return self._reply("I can set a timer or a reminder.")
        if self.cloud == "live" and not self._cloud_ready():
            return self._reply("The cloud model stays off until a key is set outside this repo.")
        self._mark("thinking")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True)

    def _cloud_tools(self, text):
        if self.mode == "kid":
            return self._reply("Mail and calendar stay off in kid mode.", refused=True)
        if self.cloud == "off":
            return self._reply("Mail and calendar need the cloud, and it is off.", refused=True)
        if self.cloud == "live" and not self._cloud_ready():
            return self._reply("The cloud model stays off until a key is set outside this repo.", refused=True)
        self._mark("thinking")
        result = self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        return self._reply(result["said"], used_cloud=True, records=result.get("records") or ())

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
