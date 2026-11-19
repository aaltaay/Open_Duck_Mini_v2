"""Camera dock states for the gold-dome nest.

The mode names are the ones in twin/dock/camera/camera_dock.py (search, approach,
about, turn, fine, backoff, sit). No AprilTag states. nest_v2 is the mat.
nest v3, v4, and v5 are studies and are not used here.

The 40 outcomes are the gold-dome camera batch: 20 of 20 charging, then 18 of 20,
together 38 of 40 (sim pass only, twin/dock/camera/SEAT_CONTACTS.md and
CAMERA_DOCK.md). Seed 32 never sees a mark. Seed 29 sits on one well only.
The retry cap of two is the same `retries < 2` test in that file.
"""

from __future__ import annotations

# Success path in run_one. about and backoff are inside a retry, which the
# measured time already includes.
SUCCESS_PATH = ("search", "approach", "turn", "fine", "sit")

# Same cap as camera_dock.py: two retries after the first try.
RETRY_CAP = 2

# seed, seconds, charging, reason. Times are the published t_s (sim pass only).
_RAW = (
    (1, 29.4, True, "docked"),
    (2, 34.6, True, "docked"),
    (3, 23.8, True, "docked"),
    (4, 30.9, True, "docked"),
    (5, 21.7, True, "docked"),
    (6, 53.5, True, "docked"),
    (7, 27.1, True, "docked"),
    (8, 37.3, True, "docked"),
    (9, 36.1, True, "docked"),
    (10, 27.8, True, "docked"),
    (11, 53.1, True, "docked"),
    (12, 24.5, True, "docked"),
    (13, 41.0, True, "docked"),
    (14, 32.9, True, "docked"),
    (15, 44.3, True, "docked"),
    (16, 19.7, True, "docked"),
    (17, 34.0, True, "docked"),
    (18, 24.9, True, "docked"),
    (19, 34.1, True, "docked"),
    (20, 48.1, True, "docked"),
    (21, 23.3, True, "docked"),
    (22, 31.0, True, "docked"),
    (23, 21.6, True, "docked"),
    (24, 28.1, True, "docked"),
    (25, 36.2, True, "docked"),
    (26, 31.3, True, "docked"),
    (27, 31.8, True, "docked"),
    (28, 39.0, True, "docked"),
    (29, 32.4, False, "one_well"),
    (30, 26.5, True, "docked"),
    (31, 36.4, True, "docked"),
    (32, 28.0, False, "no_marker"),
    (33, 36.4, True, "docked"),
    (34, 33.1, True, "docked"),
    (35, 23.9, True, "docked"),
    (36, 35.1, True, "docked"),
    (37, 41.3, True, "docked"),
    (38, 37.3, True, "docked"),
    (39, 26.5, True, "docked"),
    (40, 30.8, True, "docked"),
)

MEASURED = tuple(
    {"seed": seed, "t_s": t_s, "charging": charging, "reason": reason, "fell": False}
    for seed, t_s, charging, reason in _RAW
)


def charging_count():
    return sum(1 for row in MEASURED if row["charging"])


def state_at(episode, spent_s):
    """Which camera state this moment of a measured episode is in.

    The papers publish the total time, not a time per state. Equal shares of
    that total are calc only. A no_marker episode stays in search.
    """
    if episode["reason"] == "no_marker":
        return "search"
    total = float(episode["t_s"])
    if total <= 0.0:
        return "sit"
    frac = min(0.999999, max(0.0, float(spent_s) / total))
    index = min(len(SUCCESS_PATH) - 1, int(frac * len(SUCCESS_PATH)))
    return SUCCESS_PATH[index]
