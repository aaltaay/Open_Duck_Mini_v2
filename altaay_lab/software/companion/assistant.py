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
from .cloud_llm import CloudError
from .mock_llm import MockCloudLLM

# Existing dock state machine (software/dock). Walk on, turn, sit.
# Not a new policy.
DOCK_WALK_TURN_SIT = ("APPROACH", "STEER_DOCK", "ACTIVATE_CHARGER")

_ONES = {
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
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_UNITS = {
    "minute": 60,
    "minutes": 60,
    "min": 60,
    "second": 1,
    "seconds": 1,
    "sec": 1,
}
_WAKE_PREFIXES = ("hey jarvis",)
_CITY = re.compile(r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z .'-]{1,40})", re.IGNORECASE)
_CLOUD_TOOLS = ("list_inbox", "list_calendar")


def _is_num_token(token):
    return token.isdigit() or token == "a" or token in _ONES or token in _TENS


def _eval_number(chunk):
    """One number, or tens plus a single digit. None means the phrase is not one we store."""
    if len(chunk) == 1:
        token = chunk[0]
        if token.isdigit():
            return int(token)
        if token == "a":
            return 1
        if token in _ONES:
            return _ONES[token]
        if token in _TENS:
            return _TENS[token]
        return None
    if len(chunk) == 2 and chunk[0] in _TENS and chunk[1] in _ONES and _ONES[chunk[1]] < 10:
        return _TENS[chunk[0]] + _ONES[chunk[1]]
    return None


def _duration_at(words):
    """(seconds, start, end) for the first duration. ('bad', None, None) if the number is not readable."""
    for index, word in enumerate(words):
        if word not in _UNITS:
            continue
        cursor = index - 1
        chunk = []
        while cursor >= 0 and _is_num_token(words[cursor]):
            # "a" is a number only when it is the whole count, as in "a minute".
            if words[cursor] == "a" and chunk:
                break
            chunk.append(words[cursor])
            cursor -= 1
        chunk.reverse()
        if not chunk:
            continue
        value = _eval_number(chunk)
        if value is None:
            return ("bad", None, None)
        return (value * _UNITS[word], cursor + 1, index + 1)
    return None


def _strip_wake(text):
    """Drop a leading wake phrase. The caller keeps the original line for the report."""
    lowered = _norm(text)
    for prefix in _WAKE_PREFIXES:
        if lowered == prefix or lowered.startswith(prefix + " "):
            skip = len(prefix.split())
            tail = text.split()[skip:]
            return " ".join(tail)
    return text


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
        text = _strip_wake(text)
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
        if "?" in text or "?" in lowered or lowered.startswith(("what", "who", "when", "why", "how", "where")):
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
        found = _duration_at(lowered.split())
        if not found or found[0] == "bad":
            return self._reply("Say a timer in minutes.")
        seconds = found[0]
        if seconds % 60 == 0 and seconds >= 60:
            count = seconds // 60
            self.timers.append(count)
            unit = "minute" if count == 1 else "minutes"
            said = "Timer set for %d %s." % (count, unit)
        else:
            unit = "second" if seconds == 1 else "seconds"
            said = "Timer set for %d %s." % (seconds, unit)
        self.timer_jobs.append({"seconds": seconds, "due": self.now() + seconds, "fired": False})
        return self._reply(said, stored="timer")

    def _reminder(self, text, lowered):
        note = text.strip()
        if lowered.startswith("remind me"):
            parts = note.split(None, 2)
            note = parts[-1] if len(parts) >= 3 else ""
        note = note.strip()
        if note.lower().startswith("to "):
            note = note[3:]
        delay = None
        original = note.split()
        words = _norm(note).split()
        found = _duration_at(words)
        if found and found[0] == "bad":
            return self._reply("Say the reminder time again.")
        if found and found[1] > 0 and words[found[1] - 1] == "in":
            delay = found[0]
            start, end = found[1] - 1, found[2]
            if len(original) == len(words):
                note = " ".join(original[:start] + original[end:])
            else:
                note = " ".join(words[:start] + words[end:])
            note = note.strip()
        if not note:
            return self._reply("Say what I should remember.")
        self.reminders.append(note)
        self.reminder_jobs.append({"note": note, "due": None if delay is None else self.now() + delay, "fired": False})
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
        result = self._complete(text)
        if result is None:
            return self._reply("The cloud model did not answer.")
        return self._reply(result["said"], used_cloud=True)

    def _complete(self, text):
        try:
            return self.llm.complete(text, tools=_CLOUD_TOOLS, kid=False)
        except CloudError:
            return None

    def _cloud_tools(self, text):
        if self.mode == "kid":
            return self._reply("Mail and calendar stay off in kid mode.", refused=True)
        if self.cloud == "off":
            return self._reply("Mail and calendar need the cloud, and it is off.", refused=True)
        if self.cloud == "live" and not self._cloud_ready():
            return self._reply("The cloud model stays off until a key is set outside this repo.", refused=True)
        self._mark("thinking")
        result = self._complete(text)
        if result is None:
            return self._reply("The cloud model did not answer.")
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
