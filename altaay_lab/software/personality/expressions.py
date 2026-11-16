"""Named head motions.

Each one returns a target inside the command box. The engine slews toward
that target. Times and amplitudes here are set points, not measurements.
Eyes stay white (D57). Ear targets stay in the cited -1 to 1 antenna value.
"""

from __future__ import annotations

import math

NAMES = (
    "curious_tilt",
    "happy_wiggle",
    "sleepy_droop",
    "startled",
    "look_at",
    "nod",
    "shake",
    "greeting",
    "bored_glance",
    "seated_alert",
    "settle",
)

BLINKS = ("steady", "slow", "double", "off")


def _clip_head(box, pose):
    return {name: box.clip_joint(name, pose[name]) for name in pose}


def _zero():
    return {"neck_pitch": 0.0, "head_pitch": 0.0, "head_yaw": 0.0, "head_roll": 0.0}


def target(name, t, ctx, box):
    """Target pose, ear pair, brightness, blink, and an optional sound name."""
    if name not in NAMES:
        raise ValueError("unknown expression")
    t = float(t)
    sign = 1.0 if ctx["glance_sign"] >= 0 else -1.0
    phase = float(ctx["glance_phase"])
    bearing = 0.0 if ctx["bearing"] is None else float(ctx["bearing"])
    elevation = 0.0 if ctx["elevation"] is None else float(ctx["elevation"])
    arousal = min(1.0, max(0.0, float(ctx["arousal"])))
    curiosity = min(1.0, max(0.0, float(ctx["curiosity"])))
    valence = min(1.0, max(-1.0, float(ctx["valence"])))
    j = box.joints
    pose = _zero()
    ears = (0.0, 0.0)
    eye = 0.55
    blink = "steady"
    sound = None

    if name == "curious_tilt":
        pose["head_roll"] = sign * 0.55 * max(abs(j["head_roll"].lo), j["head_roll"].hi) * (0.35 + 0.65 * curiosity)
        pose["neck_pitch"] = 0.40 * j["neck_pitch"].hi * (0.4 + 0.6 * arousal)
        pose["head_yaw"] = bearing if ctx["bearing"] is not None else sign * 0.22 * j["head_yaw"].hi
        pose["head_pitch"] = 0.12 * j["head_pitch"].hi
        ears = (0.7, 0.7)
        eye = 0.85
        blink = "steady"
    elif name == "happy_wiggle":
        w = math.sin(2.0 * math.pi * 1.5 * t)
        gain = 0.25 + 0.75 * max(0.0, valence)
        pose["head_yaw"] = 0.28 * j["head_yaw"].hi * w * gain
        pose["head_roll"] = 0.22 * j["head_roll"].hi * math.sin(2.0 * math.pi * 1.5 * t + 0.7) * gain
        pose["neck_pitch"] = 0.25 * j["neck_pitch"].hi
        ears = (0.9, 0.9)
        eye = 0.95
        blink = "steady"
    elif name == "sleepy_droop":
        pose["neck_pitch"] = 0.72 * j["neck_pitch"].lo
        pose["head_pitch"] = 0.50 * j["head_pitch"].lo
        pose["head_roll"] = sign * 0.08 * abs(j["head_roll"].lo)
        pose["head_yaw"] = 0.04 * math.sin(0.5 * t)
        ears = (-0.75, -0.75)
        eye = 0.18
        blink = "slow"
    elif name == "startled":
        fade = math.exp(-2.5 * t)
        pose["head_pitch"] = 0.65 * j["head_pitch"].hi * fade
        pose["head_roll"] = sign * 0.35 * j["head_roll"].hi * fade
        pose["neck_pitch"] = 0.30 * j["neck_pitch"].hi * fade
        ears = (1.0, 1.0)
        eye = 1.0
        blink = "double"
        sound = "peep" if t < 0.35 else None
    elif name == "look_at":
        pose["head_yaw"] = bearing
        pose["head_pitch"] = elevation
        pose["neck_pitch"] = 0.22 * j["neck_pitch"].hi
        ears = (0.45, 0.45)
        eye = 0.8
        blink = "steady"
    elif name == "nod":
        pose["head_pitch"] = -0.42 * abs(j["head_pitch"].lo) * (0.55 + 0.45 * math.sin(2.0 * math.pi * 1.1 * t))
        pose["neck_pitch"] = 0.12 * j["neck_pitch"].hi
        ears = (0.55, 0.55)
        eye = 0.85
        blink = "steady"
    elif name == "shake":
        amp = 0.35 * min(abs(j["head_yaw"].lo), j["head_yaw"].hi)
        pose["head_yaw"] = amp * math.sin(2.0 * math.pi * 2.0 * t + 1.1)
        pose["head_roll"] = 0.12 * j["head_roll"].hi * math.sin(2.0 * math.pi * 2.0 * t)
        ears = (0.2, 0.2)
        eye = 0.7
        blink = "double"
    elif name == "greeting":
        pose["head_pitch"] = -0.28 * abs(j["head_pitch"].lo) * (0.5 + 0.5 * math.sin(2.0 * math.pi * 1.0 * t))
        pose["head_yaw"] = 0.55 * bearing
        pose["neck_pitch"] = 0.35 * j["neck_pitch"].hi
        ears = (0.95, 0.95)
        eye = 1.0
        blink = "double"
        sound = "peep" if t < 0.25 else None
    elif name == "bored_glance":
        amp = 0.50 * min(abs(j["head_yaw"].lo), j["head_yaw"].hi)
        pose["head_yaw"] = amp * math.sin(2.0 * math.pi * 0.12 * t + phase)
        pose["head_roll"] = sign * 0.12 * j["head_roll"].hi
        pose["neck_pitch"] = 0.18 * j["neck_pitch"].hi
        ears = (-0.15, -0.15)
        eye = 0.45
        blink = "slow"
    elif name == "seated_alert":
        # Head up, small look. The sit itself is D59. This is only the head.
        amp = 0.22 * min(abs(j["head_yaw"].lo), j["head_yaw"].hi)
        pose["neck_pitch"] = 0.55 * j["neck_pitch"].hi
        pose["head_pitch"] = 0.18 * j["head_pitch"].hi
        pose["head_yaw"] = amp * math.sin(2.0 * math.pi * 0.10 * t + phase)
        ears = (0.35, 0.35)
        eye = 0.55
        blink = "slow"
    elif name == "settle":
        ears = (0.0, 0.0)
        eye = 0.5
        blink = "steady"

    pose = _clip_head(box, pose)
    return {
        "head": pose,
        "antenna_left": ears[0],
        "antenna_right": ears[1],
        "eye_brightness": eye,
        "blink": blink,
        "sound": sound,
    }
