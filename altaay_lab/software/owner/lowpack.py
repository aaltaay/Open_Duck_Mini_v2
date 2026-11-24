"""Power the duck off when the log says the pack is at the walk stop.

10.0 V is the cited pack walk stop (personality/limits.py). A missing voltage
does not power off. Charging does not power off. The command list is recorded
so a test can see it. --apply is refused unless the state directory is the
Pi path, so a test cannot power this machine off.
"""

from __future__ import annotations

import os

from altaay_lab.software.personality.limits import PACK_WALK_STOP_V

from . import status_data, store

# Stop motion and sensing before the supervisor, then power off.
STOP_ORDER = (
    "odm-walk.service",
    "odm-perception.service",
    "odm-voice.service",
    "odm-supervisor.service",
)
PI_STATE = "/var/lib/odm"


def latest_reading(text):
    summary = status_data.summarize(text)
    if summary["rows"] == 0 or summary["pack_v"] is None:
        return None
    return {"mode": summary["mode"], "pack_v": summary["pack_v"]}


def should_shut_down(reading):
    if not reading or reading.get("pack_v") is None:
        return False
    if reading.get("mode") == "charge":
        return False
    return float(reading["pack_v"]) <= float(PACK_WALK_STOP_V)


def plan_for(reading):
    return {
        "pack_v": reading["pack_v"],
        "poweroff": ["/usr/bin/systemctl", "poweroff"],
        "reason": "pack at or under the cited walk stop",
        "stop": [["/usr/bin/systemctl", "stop", name] for name in STOP_ORDER],
    }


def apply_plan(state, plan, runner):
    store.ensure(state)
    # The request lives in the runtime dir, which a reboot clears. The json
    # under the state dir is only a record of the last request.
    store.write_json(store.request_path(state), {
        "reason": plan["reason"],
        "pack_v": plan["pack_v"],
    }, 0o644)
    for cmd in plan["stop"]:
        runner(list(cmd))
    runner(list(plan["poweroff"]))
    store.write_json(store.path(state, store.SHUTDOWN), {
        "commands": plan["stop"] + [plan["poweroff"]],
        "pack_v": plan["pack_v"],
        "reason": plan["reason"],
    }, 0o644)


def apply_allowed(state):
    return os.path.abspath(state) == PI_STATE


def consider(state, runner, text=None):
    """Look at the log once. Return the plan if a shutdown was requested.

    A request already written this boot is not repeated. The record file
    under the state directory does not count: it survives a charge and a
    reboot, and the runtime request does not.
    """
    if os.path.isfile(store.request_path(state)):
        return None
    if text is None:
        body, _trimmed = status_data.read_tail(store.log_path(state), status_data.TAIL_BYTES)
    else:
        body = text
    reading = latest_reading(body)
    if not should_shut_down(reading):
        return None
    plan = plan_for(reading)
    apply_plan(state, plan, runner)
    return plan
