"""Three-day accelerated soak of the autonomy loop. Sim pass only.

Dock misses are draws from the 40 gold-dome camera results (38 charging,
twin/dock/camera/SEAT_CONTACTS.md). The walk current and the cell curve are
the published models named in plant.py. A face finder and a floor plan are
BLOCKER, so people in this soak are a script.

From the repo root:
  python3 -m altaay_lab.software.autonomy.soak
"""

from __future__ import annotations

import json
import os

from .plant import CHARGE_A, WALK_PACK_A, HomePlant
from .supervisor import Supervisor, MeasuredOutcomes
from .video import write_day

# Set points for the script, not a measured home.
FACE_EVERY_S = 50.0 * 60.0
FACE_LEN_S = 20.0
REMIND_AT_S = 90.0 * 60.0
REMIND_DUE_S = 100.0 * 60.0
TICK_S = 10.0
DAY_S = 86400.0


def _script(plant, sup, state):
    events = []
    t = plant.t
    plant.attention = "none"
    plant.face_close = False
    plant.bearing = None
    slot = int(t // FACE_EVERY_S)
    if slot != state["slot"]:
        state["slot"] = slot
        events.append("face_seen")
        sup.assistant.handle("hello")
    if (t % FACE_EVERY_S) < FACE_LEN_S:
        plant.attention = "face"
        plant.bearing = 0.4
        if (t % FACE_EVERY_S) > FACE_LEN_S - 4.0:
            plant.face_close = True
    if not state["reminded"] and t >= REMIND_AT_S:
        sup.assistant.handle("remind me to stretch")
        state["reminded"] = True
    if not state["due"] and t >= REMIND_DUE_S:
        events.append("reminder_due")
        state["due"] = True
    if REMIND_DUE_S <= t < REMIND_DUE_S + 20.0:
        plant.attention = "face"
        plant.bearing = 0.3
        plant.face_close = t > REMIND_DUE_S + 8.0
    return events


def run(days=3.0, seed=1, tick_s=TICK_S):
    horizon = float(days) * DAY_S
    outcomes = MeasuredOutcomes(seed)
    plant = HomePlant()
    sup = Supervisor(seed=seed, outcomes=outcomes)
    state = {"slot": -1, "reminded": False, "due": False, "restarted": False}
    day = []
    kept = []
    last_sample = -1e9
    t = 0.0
    while t < horizon - 1e-6:
        if not state["restarted"] and t >= DAY_S:
            kept.extend(sup.log_rows)
            snap = sup.snapshot(plant)
            sup = Supervisor(seed=seed, outcomes=outcomes)
            sup.restore(plant, snap)
            sup._log(plant, "restart")
            state["restarted"] = True
        dt = min(tick_s, horizon - t)
        events = _script(plant, sup, state)
        row = sup.step(plant, t, dt, events)
        t = plant.t
        if row["t"] <= DAY_S and row["t"] - last_sample >= 30.0:
            day.append({
                "t": row["t"],
                "mode": row["mode"],
                "expression": row["expression"],
                "pack_v": row["pack_v"],
                "knee_c": row["knee_c"],
                "camera": row["camera"],
            })
            last_sample = row["t"]
    kept.extend(sup.log_rows)
    misses = [
        {"t": row["t"], "seed": row.get("seed"), "reason": row.get("reason")}
        for row in kept
        if row.get("kind") == "dock_result" and not row.get("ok")
    ]
    summary = sup.summary(plant)
    summary.update({
        "dock_misses": misses,
        "days": days,
        "seed": seed,
        "tick_s": tick_s,
        "restarted_after_day": state["restarted"],
        "hours_awake_label": "sim pass only",
        "dock_rate_cited": "38 of 40 charging, sim pass only, SEAT_CONTACTS.md",
        "getup_cited": "112 of 112 flat, sim pass only, VIA_SIT_EVAL.md",
        "walk_current_label": "sim pass only, FIT3.md mean 5.144 A. Held-rail mean is BLOCKER.",
        "charge_current_label": "calc only, netlist 1.006 A",
        "spontaneous_falls": "0. Cited flat walks in HOLD12 and the 40 camera docks report no fall. A daily fall rate is BLOCKER, so none is invented.",
        "min_pack_v": plant.min_pack_v,
        "walk_pack_a": WALK_PACK_A,
        "charge_a": CHARGE_A,
    })
    return summary, day, sup


def main(argv=None):
    summary, day, _sup = run(days=3.0, seed=1)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    out_dir = os.path.join(root, "altaay_lab", "twin", "out")
    os.makedirs(out_dir, exist_ok=True)
    video_dir = os.path.join(out_dir, "videos")
    os.makedirs(video_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, "autonomy_soak.json")
    video_path = os.path.join(video_dir, "autonomy_day.mp4")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1, sort_keys=True)
        handle.write("\n")
    write_day(day, video_path)
    summary["summary_file"] = "altaay_lab/twin/out/autonomy_soak.json"
    summary["video_file"] = "altaay_lab/twin/out/videos/autonomy_day.mp4"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
