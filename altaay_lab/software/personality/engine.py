"""Personality engine.

Call step() from any thread except the 50 Hz walk thread. The walk loop only
reads the latest command. Nothing here opens a network socket or a cloud model.

Mood numbers, blend speed, and the home-voltage margin are set points.
Pack stop, servo stop, knee temperatures, head ranges, and ear values are the
cited or calc limits in limits.py.
"""

from __future__ import annotations

import math
import random
import threading

from . import expressions
from .limits import (
    ANTENNA_HI,
    ANTENNA_LO,
    DOCK_HOME,
    HEAD_JOINTS,
    HEAD_RATE_RAD_S,
    HOME_PACK_V,
    KNEE_RESUME_C,
    KNEE_STOP_C,
    PACK_WALK_STOP_V,
    SERVO_START_MIN_V,
    SERVO_WALK_STOP_V,
    clip_antenna,
    energy_from_pack,
    load_box,
)

# Set points. Not measurements.
VALENCE_BASE = 0.05
AROUSAL_BASE = 0.35
CURIOSITY_BASE = 0.40
SOCIABILITY_BASE = 0.40
TAU_VALENCE_S = 12.0
TAU_AROUSAL_S = 8.0
TAU_CURIOSITY_S = 18.0
TAU_SOCIABILITY_S = 14.0
BLEND_RATE_RAD_S = 1.5
ANTENNA_RATE = 2.0
EYE_RATE = 3.0
DROWSY_AROUSAL = 0.20
NAP_AROUSAL = 0.22
NAP_IDLE_S = 25.0
# Set point, below the nap line. A quiet sit eases toward this so a nap
# can happen from the calm baseline. Not a measurement.
NAP_REST_AROUSAL = 0.10
NIGHT_LIGHT_FLOOR = 0.75
GREET_S = 1.6
WAKE_S = 2.0
PET_S = 1.8
TIMER_S = 5.0
FALL_STARTLE_S = 0.8
SOUND_HOLD_S = 0.4
ASSISTANT_HOLD_S = 1.5
START_ENERGY = 0.8

PHASE_EXPRESSION = {
    "listening": "curious_tilt",
    "thinking": "look_at",
    "speaking": "nod",
    "done": "settle",
    "refused": "shake",
}

INTENTS = ("none", "walk_to_person", "go_home", "sit", "nap")


def _decay(value, base, dt, tau):
    return base + (value - base) * math.exp(-dt / tau)


def _clamp(value, lo, hi):
    return min(hi, max(lo, float(value)))


def _slew(current, target, limit):
    delta = target - current
    if delta > limit:
        return current + limit
    if delta < -limit:
        return current - limit
    return target


class Sensors:
    """Readings the walk thread, or a test, already gathered.

    bearing_rad and elevation_rad are a stub. A face finder and a sound
    direction on this Pi are BLOCKER (USEFULNESS.md, COMPANION.md).
    """

    def __init__(
        self,
        pack_v=None,
        servo_median_v=None,
        knee_c=None,
        idle_s=0.0,
        posture="standing",
        bearing_rad=None,
        elevation_rad=None,
        attention="none",
        face_close=False,
    ):
        if posture not in ("standing", "walking", "sitting"):
            raise ValueError("posture must be standing, walking, or sitting")
        if attention not in ("none", "face", "sound"):
            raise ValueError("attention must be none, face, or sound")
        self.pack_v = pack_v
        self.servo_median_v = servo_median_v
        self.knee_c = knee_c
        self.idle_s = float(idle_s)
        self.posture = posture
        self.bearing_rad = bearing_rad
        self.elevation_rad = elevation_rad
        self.attention = attention
        self.face_close = bool(face_close)


class Command:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def as_dict(self):
        mood = dict(self.mood)
        return {
            "neck_pitch": self.neck_pitch,
            "head_pitch": self.head_pitch,
            "head_yaw": self.head_yaw,
            "head_roll": self.head_roll,
            "antenna_left": self.antenna_left,
            "antenna_right": self.antenna_right,
            "eye_brightness": self.eye_brightness,
            "eye_color": self.eye_color,
            "blink": self.blink,
            "eye_on": self.eye_on,
            "sound": self.sound,
            "intent": self.intent,
            "expression": self.expression,
            "dock_states": tuple(self.dock_states),
            "priority": self.priority,
            "reason": self.reason,
            "assistant_phase": self.assistant_phase,
            "mood": mood,
            "energy": self.energy,
            "reminder": self.reminder,
            "kid_mode": self.kid_mode,
            "t": self.t,
        }


class Personality:
    def __init__(self, seed=0, mode="kid", blend_rate=BLEND_RATE_RAD_S, box=None):
        if mode not in ("kid", "adult"):
            raise ValueError("mode must be kid or adult")
        self.mode = mode
        self.box = box if box is not None else load_box()
        self.blend_rate = min(float(blend_rate), HEAD_RATE_RAD_S)
        self.rng = random.Random(seed)
        self.glance_sign = 1.0 if self.rng.randrange(2) == 0 else -1.0
        self.glance_phase = self.rng.random() * math.tau
        self.t = 0.0
        self.valence = VALENCE_BASE
        self.arousal = AROUSAL_BASE
        self.curiosity = CURIOSITY_BASE
        self.sociability = SOCIABILITY_BASE
        self.energy = START_ENERGY
        self.head = {name: 0.0 for name in HEAD_JOINTS}
        self.antenna_left = 0.0
        self.antenna_right = 0.0
        self.eye_brightness = 0.5
        self.blink = "steady"
        self.expression = "settle"
        self.intent = "none"
        self.priority = "idle"
        self.reason = "idle"
        self.sound = None
        self.assistant_phase = None
        self.carry = "none"
        self.reminder = "none"
        self.night_light = False
        self.asked_home = False
        self.help_me = False
        self.fallen = False
        self.fall_at = None
        self.knee_hot = False
        self.on_dock = False
        self.low_latched = False
        self.face_on = False
        self.face_close = False
        self.bearing = None
        self.elevation = None
        self.attention = "none"
        self.greet_until = -1.0
        self.wake_until = -1.0
        self.pet_until = -1.0
        self.timer_until = -1.0
        self._sound_until = -1.0
        self._sound_name = None
        self._last_phase = None
        self._phase_until = -1.0
        self._walk_thread_id = None
        self._expr_t = 0.0
        self._expr_name = "settle"
        self._last_sensors = Sensors()

    def bind_walk_thread(self, ident=None):
        """Remember the walk thread. step() refuses to run there."""
        self._walk_thread_id = threading.get_ident() if ident is None else ident

    def request_home(self):
        """Spoken go-home. Same need as a low pack, same dock state names."""
        self.asked_home = True

    def request_help(self):
        """Sit and wait. The help_me pose stays until a person pets or picks up."""
        self.help_me = True

    def export_state(self):
        """Plain numbers so a restart can continue. The walk thread id is not saved."""
        version, state, gauss = self.rng.getstate()
        sensors = self._last_sensors
        return {
            "t": self.t,
            "mode": self.mode,
            "valence": self.valence,
            "arousal": self.arousal,
            "curiosity": self.curiosity,
            "sociability": self.sociability,
            "energy": self.energy,
            "head": dict(self.head),
            "antenna_left": self.antenna_left,
            "antenna_right": self.antenna_right,
            "eye_brightness": self.eye_brightness,
            "blink": self.blink,
            "expression": self.expression,
            "intent": self.intent,
            "priority": self.priority,
            "reason": self.reason,
            "assistant_phase": self.assistant_phase,
            "carry": self.carry,
            "reminder": self.reminder,
            "night_light": self.night_light,
            "asked_home": self.asked_home,
            "help_me": self.help_me,
            "fallen": self.fallen,
            "fall_at": self.fall_at,
            "knee_hot": self.knee_hot,
            "on_dock": self.on_dock,
            "low_latched": self.low_latched,
            "face_on": self.face_on,
            "face_close": self.face_close,
            "bearing": self.bearing,
            "elevation": self.elevation,
            "attention": self.attention,
            "glance_sign": self.glance_sign,
            "glance_phase": self.glance_phase,
            "greet_until": self.greet_until,
            "wake_until": self.wake_until,
            "pet_until": self.pet_until,
            "timer_until": self.timer_until,
            "sound_until": self._sound_until,
            "sound_name": self._sound_name,
            "phase_until": self._phase_until,
            "expr_t": self._expr_t,
            "expr_name": self._expr_name,
            "rng_version": version,
            "rng_state": list(state),
            "rng_gauss": gauss,
            "sensors": {
                "pack_v": sensors.pack_v,
                "servo_median_v": sensors.servo_median_v,
                "knee_c": sensors.knee_c,
                "idle_s": sensors.idle_s,
                "posture": sensors.posture,
                "bearing_rad": sensors.bearing_rad,
                "elevation_rad": sensors.elevation_rad,
                "attention": sensors.attention,
                "face_close": sensors.face_close,
            },
        }

    def import_state(self, saved):
        """Restore export_state(). The box and the blend rate stay as constructed."""
        for name in (
            "t", "valence", "arousal", "curiosity", "sociability", "energy",
            "antenna_left", "antenna_right", "eye_brightness", "blink",
            "expression", "intent", "priority", "reason", "assistant_phase",
            "carry", "reminder", "night_light", "asked_home", "help_me",
            "fallen", "fall_at", "knee_hot", "on_dock", "low_latched",
            "face_on", "face_close", "bearing", "elevation", "attention",
            "glance_sign", "glance_phase", "greet_until", "wake_until",
            "pet_until", "timer_until",
        ):
            setattr(self, name, saved[name])
        self.head = {name: float(saved["head"][name]) for name in HEAD_JOINTS}
        self._sound_until = saved["sound_until"]
        self._sound_name = saved["sound_name"]
        self._phase_until = saved["phase_until"]
        self._expr_t = saved["expr_t"]
        self._expr_name = saved["expr_name"]
        self._last_phase = saved["assistant_phase"]
        gauss = saved["rng_gauss"]
        self.rng.setstate((saved["rng_version"], tuple(saved["rng_state"]), gauss))
        raw = saved["sensors"]
        self._last_sensors = Sensors(
            pack_v=raw["pack_v"],
            servo_median_v=raw["servo_median_v"],
            knee_c=raw["knee_c"],
            idle_s=raw["idle_s"],
            posture=raw["posture"],
            bearing_rad=raw["bearing_rad"],
            elevation_rad=raw["elevation_rad"],
            attention=raw["attention"],
            face_close=raw["face_close"],
        )

    def clear_assistant(self):
        """Drop a held assistant pose so a reminder or a timer can show."""
        self.assistant_phase = None
        self._phase_until = -1.0

    def show_assistant(self, phase):
        if phase not in PHASE_EXPRESSION:
            raise ValueError("unknown assistant phase")
        if phase != self._last_phase:
            self._enter_phase(phase)
            self._last_phase = phase
        self.assistant_phase = phase
        self._phase_until = self.t + ASSISTANT_HOLD_S
        # No new readings. The last pack, knee, and posture stay in force.
        return self.step(0.05)

    def _enter_phase(self, phase):
        if phase == "listening":
            self.arousal = _clamp(self.arousal + 0.12, 0.0, 1.0)
            self.sociability = _clamp(self.sociability + 0.08, 0.0, 1.0)
        elif phase == "refused":
            self.valence = _clamp(self.valence - 0.15, -1.0, 1.0)

    def step(self, dt, sensors=None, events=None):
        if self._walk_thread_id is not None and threading.get_ident() == self._walk_thread_id:
            raise RuntimeError("personality stays off the walk thread")
        if dt < 0:
            raise ValueError("dt must be >= 0")
        dt = float(dt)
        if sensors is None:
            sensors = self._last_sensors
        else:
            sensors = self._hold_readings(sensors)
        self._last_sensors = sensors
        self.t += dt
        # A reading can still say "face" on the tick the face is lost.
        # Apply the reading first so the event wins.
        self._apply_sensors(sensors)
        self._apply_events(list(events or []))
        self._decay_mood(dt, sensors)
        choice = self._arbitrate(sensors)
        self._follow(choice, dt)
        return self._command()

    def _apply_events(self, events):
        for name in events:
            if name == "wake_word":
                self.arousal = _clamp(self.arousal + 0.35, 0.0, 1.0)
                self.sociability = _clamp(self.sociability + 0.20, 0.0, 1.0)
                self.curiosity = _clamp(self.curiosity + 0.10, 0.0, 1.0)
                self.wake_until = self.t + WAKE_S
            elif name == "face_seen":
                self.face_on = True
                self.valence = _clamp(self.valence + 0.25, -1.0, 1.0)
                self.sociability = _clamp(self.sociability + 0.30, 0.0, 1.0)
                self.curiosity = _clamp(self.curiosity + 0.35, 0.0, 1.0)
                self.greet_until = self.t + GREET_S
            elif name == "face_lost":
                self.face_on = False
                self.face_close = False
                self.sociability = _clamp(self.sociability - 0.15, 0.0, 1.0)
            elif name in ("petted", "picked_up"):
                self.valence = _clamp(self.valence + 0.40, -1.0, 1.0)
                self.arousal = _clamp(self.arousal + 0.25, 0.0, 1.0)
                self.pet_until = self.t + PET_S
                self.help_me = False
            elif name == "timer_fired":
                self.arousal = _clamp(self.arousal + 0.30, 0.0, 1.0)
                self.timer_until = self.t + TIMER_S
            elif name == "reminder_due":
                self.carry = "pending"
                self.reminder = "search"
                self.sociability = _clamp(self.sociability + 0.20, 0.0, 1.0)
            elif name == "low_battery":
                self.low_latched = True
                self.valence = _clamp(self.valence - 0.20, -1.0, 1.0)
                self.arousal = _clamp(self.arousal - 0.15, 0.0, 1.0)
            elif name == "charging_started":
                self.on_dock = True
                self.asked_home = False
                self.low_latched = False
                self.arousal = _clamp(self.arousal - 0.20, 0.0, 1.0)
                self.valence = _clamp(self.valence + 0.10, -1.0, 1.0)
            elif name == "charging_finished":
                self.on_dock = False
                self.arousal = _clamp(self.arousal + 0.20, 0.0, 1.0)
                self.valence = _clamp(self.valence + 0.15, -1.0, 1.0)
            elif name == "idle_time":
                pass
            elif name == "fell_over":
                if not self.fallen:
                    self.fall_at = self.t
                self.fallen = True
                self.arousal = _clamp(self.arousal + 0.45, 0.0, 1.0)
            elif name == "stood_up":
                self.fallen = False
                self.fall_at = None
            elif name == "knee_heat_rest":
                self.knee_hot = True
                self.arousal = _clamp(self.arousal - 0.20, 0.0, 1.0)
            elif name == "knee_heat_cool":
                self.knee_hot = False
            else:
                raise ValueError("unknown event")

    def _apply_sensors(self, sensors):
        self.attention = sensors.attention
        self.bearing = sensors.bearing_rad
        self.elevation = sensors.elevation_rad
        self.face_close = bool(sensors.face_close and self.face_on)
        if sensors.attention == "face":
            self.face_on = True
        if sensors.pack_v is not None:
            self.energy = energy_from_pack(sensors.pack_v)
            if sensors.pack_v > HOME_PACK_V:
                self.low_latched = False
        elif sensors.servo_median_v is not None:
            v = float(sensors.servo_median_v)
            if v <= SERVO_WALK_STOP_V:
                self.energy = 0.0
            elif v < SERVO_START_MIN_V:
                span = SERVO_START_MIN_V - SERVO_WALK_STOP_V
                home_e = energy_from_pack(HOME_PACK_V)
                self.energy = (v - SERVO_WALK_STOP_V) / span * home_e
            else:
                self.energy = max(self.energy, START_ENERGY)
        if sensors.knee_c is not None:
            if float(sensors.knee_c) >= KNEE_STOP_C:
                self.knee_hot = True
            elif float(sensors.knee_c) < KNEE_RESUME_C:
                self.knee_hot = False

    def _hold_readings(self, sensors):
        """A missing voltage or knee keeps the last sample. None is not a recovery."""
        prev = self._last_sensors
        return Sensors(
            pack_v=prev.pack_v if sensors.pack_v is None else sensors.pack_v,
            servo_median_v=prev.servo_median_v if sensors.servo_median_v is None else sensors.servo_median_v,
            knee_c=prev.knee_c if sensors.knee_c is None else sensors.knee_c,
            idle_s=sensors.idle_s,
            posture=sensors.posture,
            bearing_rad=sensors.bearing_rad,
            elevation_rad=sensors.elevation_rad,
            attention=sensors.attention,
            face_close=sensors.face_close,
        )

    def _decay_mood(self, dt, sensors):
        if dt == 0:
            return
        arousal_base = AROUSAL_BASE
        if sensors.posture == "sitting" and sensors.idle_s >= NAP_IDLE_S:
            arousal_base = NAP_REST_AROUSAL
        self.valence = _decay(self.valence, VALENCE_BASE, dt, TAU_VALENCE_S)
        self.arousal = _decay(self.arousal, arousal_base, dt, TAU_AROUSAL_S)
        self.curiosity = _decay(self.curiosity, CURIOSITY_BASE, dt, TAU_CURIOSITY_S)
        self.sociability = _decay(self.sociability, SOCIABILITY_BASE, dt, TAU_SOCIABILITY_S)

    def _battery_hard(self, sensors):
        pack_hard = sensors.pack_v is not None and float(sensors.pack_v) <= PACK_WALK_STOP_V
        servo_hard = sensors.servo_median_v is not None and float(sensors.servo_median_v) <= SERVO_WALK_STOP_V
        return pack_hard or servo_hard

    def _need_home(self, sensors):
        if self.on_dock:
            return False
        if self.asked_home:
            return True
        if sensors.pack_v is not None:
            v = float(sensors.pack_v)
            return PACK_WALK_STOP_V < v <= HOME_PACK_V
        if sensors.servo_median_v is not None:
            v = float(sensors.servo_median_v)
            return SERVO_WALK_STOP_V < v < SERVO_START_MIN_V
        return self.low_latched

    def _social_choice(self):
        now = self.t
        if self.assistant_phase in PHASE_EXPRESSION and now <= self._phase_until:
            return PHASE_EXPRESSION[self.assistant_phase], "assistant " + self.assistant_phase
        if self.assistant_phase is not None and now > self._phase_until:
            self.assistant_phase = None
        if self.carry == "pending" and (self.face_close or self.face_on):
            if self.face_close:
                self.carry = "delivered"
                self.reminder = "delivered"
                return "nod", "reminder delivered"
            self.reminder = "approach"
            return "greeting", "reminder to a person"
        if now < self.timer_until:
            return "startled", "timer"
        if self.carry == "pending":
            self.reminder = "search"
            return "bored_glance", "reminder search"
        if now < self.pet_until:
            return "happy_wiggle", "petted"
        if self.face_on and now < self.greet_until:
            return "greeting", "greet"
        if now < self.wake_until:
            return "curious_tilt", "wake"
        if self.face_on and self.curiosity >= 0.55:
            return "curious_tilt", "curious look"
        if self.face_on:
            return "look_at", "face"
        return None

    def _arbitrate(self, sensors):
        if self.help_me:
            return {
                "priority": "safety",
                "intent": "sit",
                "expression": "help_me",
                "reason": "stuck, sit and wait",
                "dock_states": (),
            }
        if self.fallen:
            fresh = self.fall_at is not None and (self.t - self.fall_at) <= FALL_STARTLE_S
            name = "startled" if fresh else "settle"
            return {
                "priority": "safety",
                "intent": "sit",
                "expression": name,
                "reason": "safety fall",
                "dock_states": (),
            }
        if self.knee_hot:
            return {
                "priority": "safety",
                "intent": "sit",
                "expression": "sleepy_droop",
                "reason": "safety knee heat",
                "dock_states": (),
            }
        if self._battery_hard(sensors):
            return {
                "priority": "safety",
                "intent": "sit",
                "expression": "sleepy_droop",
                "reason": "safety battery",
                "dock_states": (),
            }
        if self._need_home(sensors):
            return {
                "priority": "needs",
                "intent": "go_home",
                "expression": "sleepy_droop",
                "reason": "need home",
                "dock_states": DOCK_HOME,
            }
        social = self._social_choice()
        if social is not None:
            name, reason = social
            intent = "none"
            if reason == "reminder to a person":
                intent = "walk_to_person"
            return {
                "priority": "social",
                "intent": intent,
                "expression": name,
                "reason": reason,
                "dock_states": (),
            }
        if self.on_dock:
            return {
                "priority": "needs",
                "intent": "nap",
                "expression": "sleepy_droop",
                "reason": "charging rest",
                "dock_states": (),
            }
        if sensors.posture == "sitting" and self.arousal < NAP_AROUSAL and sensors.idle_s >= NAP_IDLE_S:
            return {
                "priority": "idle",
                "intent": "nap",
                "expression": "sleepy_droop",
                "reason": "idle nap",
                "dock_states": (),
            }
        if sensors.posture == "sitting":
            return {
                "priority": "idle",
                "intent": "sit",
                "expression": "seated_alert",
                "reason": "idle seated",
                "dock_states": (),
            }
        if self.arousal < DROWSY_AROUSAL:
            return {
                "priority": "idle",
                "intent": "none",
                "expression": "sleepy_droop",
                "reason": "idle drowsy",
                "dock_states": (),
            }
        return {
            "priority": "idle",
            "intent": "none",
            "expression": "bored_glance",
            "reason": "idle glance",
            "dock_states": (),
        }

    def _follow(self, choice, dt):
        name = choice["expression"]
        if name != self._expr_name:
            self._expr_name = name
            self._expr_t = 0.0
        else:
            self._expr_t += dt
        ctx = {
            "glance_sign": self.glance_sign,
            "glance_phase": self.glance_phase,
            "bearing": self.bearing,
            "elevation": self.elevation,
            "arousal": self.arousal,
            "curiosity": self.curiosity,
            "valence": self.valence,
        }
        got = expressions.target(name, self._expr_t, ctx, self.box)
        head_limit = self.blend_rate * dt
        hard_limit = HEAD_RATE_RAD_S * dt
        step_limit = min(head_limit, hard_limit)
        for joint in HEAD_JOINTS:
            nxt = _slew(self.head[joint], got["head"][joint], step_limit)
            self.head[joint] = self.box.clip_joint(joint, nxt)
        ear_limit = ANTENNA_RATE * dt
        self.antenna_left = clip_antenna(_slew(self.antenna_left, got["antenna_left"], ear_limit))
        self.antenna_right = clip_antenna(_slew(self.antenna_right, got["antenna_right"], ear_limit))
        eye_target = got["eye_brightness"]
        if self.night_light:
            eye_target = max(eye_target, NIGHT_LIGHT_FLOOR)
        self.eye_brightness = _clamp(_slew(self.eye_brightness, eye_target, EYE_RATE * dt), 0.0, 1.0)
        if self.night_light and self.eye_brightness < NIGHT_LIGHT_FLOOR:
            # The bead is the existing on/off eye flag. The floor is immediate.
            self.eye_brightness = NIGHT_LIGHT_FLOOR
        self.blink = got["blink"]
        self.expression = name
        self.intent = choice["intent"]
        self.priority = choice["priority"]
        self.reason = choice["reason"]
        self._dock = choice["dock_states"]
        want = got["sound"]
        if want and want != self._sound_name:
            self._sound_name = want
            self._sound_until = self.t + SOUND_HOLD_S
        if not want:
            self._sound_name = None
        self.sound = self._sound_name if self.t <= self._sound_until else None

    def _command(self):
        return Command(
            neck_pitch=self.head["neck_pitch"],
            head_pitch=self.head["head_pitch"],
            head_yaw=self.head["head_yaw"],
            head_roll=self.head["head_roll"],
            antenna_left=self.antenna_left,
            antenna_right=self.antenna_right,
            eye_brightness=self.eye_brightness,
            eye_color="white",
            blink=self.blink,
            eye_on=self.eye_brightness > 0.05,
            sound=self.sound,
            intent=self.intent,
            expression=self.expression,
            dock_states=self._dock,
            priority=self.priority,
            reason=self.reason,
            assistant_phase=self.assistant_phase,
            mood={
                "valence": self.valence,
                "arousal": self.arousal,
                "curiosity": self.curiosity,
                "sociability": self.sociability,
            },
            energy=self.energy,
            reminder=self.reminder,
            kid_mode=self.mode == "kid",
            t=self.t,
        )
