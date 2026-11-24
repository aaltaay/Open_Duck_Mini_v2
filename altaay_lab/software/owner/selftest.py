"""Self-test of the walk guards and one supervisor step.

The candidate slot must contain payload/slot_entry.py. That file is what the
services run after the pointer moves. A bundle can also ask the check to fail.
This is measured in emulation. It does not move a servo.
"""

from __future__ import annotations

import hashlib
import importlib.util
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


def slot_entry_path(slot_dir):
    return os.path.join(slot_dir, "payload", "slot_entry.py")


def load_slot_entry(slot_dir):
    """Load the signed slot's entry module. None if the slot has no code."""
    path = slot_entry_path(slot_dir)
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256(path.encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location("odm_slot_%s" % digest, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def active_entry(state):
    """The entry module for the slot the pointer names, or None."""
    from . import store
    slot = store.read_current(state)
    if not slot:
        return None
    try:
        return load_slot_entry(store.slot_path(state, slot))
    except Exception:
        return None


def run_self_test(slot_dir):
    """Return (ok, failures). failures names walk, supervisor, or both.

    The slot entry is called first, so the candidate code runs. The checkout
    guards still run too, unless the bundle asked that check to fail.
    A slot with no entry fails both checks.
    """
    request = health_request(slot_dir)
    try:
        module = load_slot_entry(slot_dir)
    except Exception:
        module = None
    if module is None or not hasattr(module, "walk_ok") or not hasattr(module, "supervisor_ok"):
        return False, ["walk", "supervisor"]
    try:
        slot_walk = bool(module.walk_ok())
        slot_supervisor = bool(module.supervisor_ok())
    except Exception:
        return False, ["walk", "supervisor"]
    failures = []
    if request.get("walk") == "fail" or not slot_walk:
        failures.append("walk")
    else:
        ok, _detail = walk_self_test()
        if not ok:
            failures.append("walk")
    if request.get("supervisor") == "fail" or not slot_supervisor:
        failures.append("supervisor")
    else:
        ok, _detail = supervisor_self_test()
        if not ok:
            failures.append("supervisor")
    return (not failures), failures
