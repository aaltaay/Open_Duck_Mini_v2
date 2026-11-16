"""Command box for the head, the ears, and the eyes.

The head box is the overlap of two limits that are already written down:

- Joystick ranges the walk was trained with, in radians. Cited from
  Open_Duck_Playground pin b9be205, playground/open_duck_mini_v2/mujoco_infer.py
  (NECK_PITCH_RANGE, HEAD_PITCH_RANGE, HEAD_YAW_RANGE, HEAD_ROLL_RANGE). The
  same four ranges are in problems/retrain_sts12/joystick_runD.py.
- Soft stops in software/servo_limits.json. That file's own label is calc
  (hard stop moved 3 deg toward zero, D59).

A command uses the tighter end of each pair. The walk loop also clips target
speed at 5.24 rad/s (cited, the same mujoco_infer.py, max_motor_velocity).

Ears: the Runtime antenna value is -1 to 1 (cited, COMPANION.md, antennas.py
at Runtime 376de65). The SG90 speed is still BLOCKER.

Pack and guard numbers used by the engine are cited in the names below.
HOME_PACK_V is a set point, 0.8 V above the cited 10.0 V pack walk stop, so
a trip still leaves room to walk.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

# Cited, playground b9be205 mujoco_infer.py and joystick_runD.py.
JOYSTICK_RAD = {
    "neck_pitch": (-0.34, 1.1),
    "head_pitch": (-0.78, 0.78),
    "head_yaw": (-1.5, 1.5),
    "head_roll": (-0.5, 0.5),
}

# Cited, mujoco_infer.py max_motor_velocity. The walk clips at this speed.
HEAD_RATE_RAD_S = 5.24

# Cited, COMPANION.md: Runtime antenna value -1 to 1.
ANTENNA_LO = -1.0
ANTENNA_HI = 1.0

# Cited, D66 / battery_guard.py pack walk cutoff and the 3S window.
PACK_FULL_V = 12.6
PACK_LOW_V = 9.0
PACK_WALK_STOP_V = 10.0

# Set point. 0.8 V above the cited 10.0 V stop. Not a measurement.
HOME_PACK_V = 10.8

# Cited, battery_guard.py defaults (SOFTWARE.md section 5).
SERVO_WALK_STOP_V = 6.0
SERVO_START_MIN_V = 6.8

# Cited, software/knee_heat.py set points (SOFTWARE.md section 5).
KNEE_STOP_C = 55.0
KNEE_RESUME_C = 45.0

# Existing dock state machine. software/dock, not a new policy.
DOCK_HOME = ("APPROACH", "STEER_DOCK", "ACTIVATE_CHARGER")

HEAD_JOINTS = ("neck_pitch", "head_pitch", "head_yaw", "head_roll")

_LIMITS_PATH = Path(__file__).resolve().parents[1] / "servo_limits.json"


class Span:
    def __init__(self, lo, hi):
        if lo > hi:
            raise ValueError("empty span")
        self.lo = float(lo)
        self.hi = float(hi)

    def clip(self, value):
        v = float(value)
        if v < self.lo:
            return self.lo
        if v > self.hi:
            return self.hi
        return v

    def holds(self, value, eps=1e-9):
        return self.lo - eps <= float(value) <= self.hi + eps


class CommandBox:
    def __init__(self, joints):
        self.joints = joints

    def clip_joint(self, name, value):
        return self.joints[name].clip(value)

    def holds_joint(self, name, value):
        return self.joints[name].holds(value)


def _soft_rad(row):
    return math.radians(float(row["soft_lo_deg"])), math.radians(float(row["soft_hi_deg"]))


def load_box(path=None):
    raw = json.loads((path or _LIMITS_PATH).read_text(encoding="utf-8"))
    joints = {}
    for name, joy in JOYSTICK_RAD.items():
        soft_lo, soft_hi = _soft_rad(raw["joints"][name])
        lo = max(joy[0], soft_lo)
        hi = min(joy[1], soft_hi)
        joints[name] = Span(lo, hi)
    return CommandBox(joints)


def clip_antenna(value):
    v = float(value)
    if v < ANTENNA_LO:
        return ANTENNA_LO
    if v > ANTENNA_HI:
        return ANTENNA_HI
    return v


def energy_from_pack(pack_v):
    """0 at the cited walk stop, 1 at the cited full pack. Calc only."""
    span = PACK_FULL_V - PACK_WALK_STOP_V
    return min(1.0, max(0.0, (float(pack_v) - PACK_WALK_STOP_V) / span))
