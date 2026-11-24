"""Self-test of the walk guards and one supervisor step.

A bundle can ask this check to fail. That is how the rollback test simulates
a bad update. The real guard objects still run when the bundle does not ask
to fail. This is measured in emulation. It does not move a servo.
"""

from __future__ import annotations

import json
import os
import sys


class ProbePlant:
    """Enough of a plant for one supervisor step. No pack model."""

    def __init__(self):
        self.v_pack = 12.0
        self.knee_c = 22.0
        self.q_mAh = 10.0
        self.idle_s = 0.0
        self.posture = "standing"
        self.bearing = 0.0
        self.attention = "none"
        self.face_close = False
        self.fallen = False
        self.t = 0.0
        self.min_pack_v = 12.0
        self.at_floor = False
        self.motion = "sit"

    def advance(self, motion, dt):
        self.t += float(dt)
        self.motion = motion


def _repo_on_path():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


def _battery_guard():
    _repo_on_path()
    lab = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bench = os.path.join(lab, "bench")
    if bench not in sys.path:
        sys.path.insert(0, bench)
    import battery_guard as bg
    return bg


def walk_self_test():
    _repo_on_path()
    from altaay_lab.software.knee_heat import KneeHeatGuard
    from altaay_lab.software.personality.limits import KNEE_STOP_C, PACK_WALK_STOP_V
    if PACK_WALK_STOP_V != 10.0 or KNEE_STOP_C != 55.0:
        return False, "walk limits moved"
    guard = KneeHeatGuard()
    decision = guard.update(0.0, {13: 22.0, 23: 22.0}, "walking")
    if decision.torque != "allow" or guard.latched:
        return False, "walk guard latched while cool"
    bg = _battery_guard()
    battery = bg.BatteryGuard(bg.GuardConfig(), state=bg.STANDING)
    if battery is None:
        return False, "walk battery guard missing"
    return True, "walk ok"


def supervisor_self_test():
    _repo_on_path()
    from altaay_lab.software.autonomy.supervisor import Supervisor
    plant = ProbePlant()
    sup = Supervisor(seed=1)
    row = sup.step(plant, 0.0, 0.2, events=[])
    if not row or not row.get("mode"):
        return False, "supervisor returned no mode"
    return True, "supervisor ok"


def health_request(slot_dir):
    file_path = os.path.join(slot_dir, "payload", "health_request.json")
    if not os.path.isfile(file_path):
        return {}
    with open(file_path, encoding="utf-8") as handle:
        body = json.load(handle)
    if not isinstance(body, dict):
        return {}
    return body


def run_self_test(slot_dir):
    """Return (ok, failures). failures names walk, supervisor, or both."""
    request = health_request(slot_dir)
    failures = []
    if request.get("walk") == "fail":
        failures.append("walk")
    else:
        ok, _detail = walk_self_test()
        if not ok:
            failures.append("walk")
    if request.get("supervisor") == "fail":
        failures.append("supervisor")
    else:
        ok, _detail = supervisor_self_test()
        if not ok:
            failures.append("supervisor")
    return (not failures), failures
