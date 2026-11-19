"""Pin the walk process to one core and raise its priority.

The service sets ODM_WALK_CPU. When that variable is empty this does nothing,
so a bench run without the variable is unchanged. SCHED_FIFO is requested
only when ODM_WALK_FIFO=1. A permission error is recorded and is not fatal:
systemd can still apply CPUAffinity from the unit file.
"""

from __future__ import annotations

import os


def apply_from_env():
    raw = os.environ.get("ODM_WALK_CPU", "").strip()
    if raw == "":
        return {"pinned": False}
    cpu = int(raw)
    os.sched_setaffinity(0, {cpu})
    note = {"pinned": True, "cpu": cpu, "fifo": False, "nice": None}
    nice_raw = os.environ.get("ODM_WALK_NICE", "").strip()
    if nice_raw != "":
        nice = int(nice_raw)
        try:
            os.setpriority(os.PRIO_PROCESS, 0, nice)
            note["nice"] = nice
        except OSError as exc:
            note["nice_error"] = exc.errno
    if os.environ.get("ODM_WALK_FIFO", "").strip() == "1":
        try:
            os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(10))
            note["fifo"] = True
        except (OSError, PermissionError) as exc:
            note["fifo_error"] = getattr(exc, "errno", None)
    return note
