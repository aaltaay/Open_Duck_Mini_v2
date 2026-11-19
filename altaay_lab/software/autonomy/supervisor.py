"""One autonomy loop for a day at home.

It ties together the personality layer, the camera dock states, the battery
guard, the knee heat guard, fall get-up, idle and nap, and the assistant.
The 50 Hz walk thread is not this loop. Call step() from the other thread in
the same process. The Runtime is not imported (D6).

On a low pack the duck starts a camera-dock episode. Outcomes are drawn from
the 40 measured gold-dome sits (38 charging). A miss is tried again until
RETRY_CAP retries are used, then the duck sits and shows help_me. A fall uses
the flat-floor get-up result, 112 of 112 (sim pass only, VIA_SIT_EVAL.md).
Two failed get-ups also sit and wait. A pet or a pickup clears the wait.

Nothing here is a hardware pass.
"""

from __future__ import annotations

import json
import os
import sys

from altaay_lab.software.companion.assistant import Assistant
from altaay_lab.software.personality.engine import Personality, Sensors
from altaay_lab.software.personality.limits import (
    KNEE_RESUME_C,
    KNEE_STOP_C,
    PACK_WALK_STOP_V,
)

from .camera_states import MEASURED, RETRY_CAP, state_at
from .plant import CHARGE_A, RAIL_V, WALK_PACK_A

# Cited joint ids, SOFTWARE.md section 2.
SERVO_IDS = (10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 30, 31, 32, 33)

# sim pass only, VIA_SIT_EVAL.md: rolls are first still at 20.3 to 21.9 s.
GETUP_S = 21.9
GETUP_TRIES = 2

# Flat floor only. sim pass only, VIA_SIT_EVAL.md: flat 112 of 112.
GETUP_FLAT_OK = 112
GETUP_FLAT_N = 112

# Set point. How long a nap lasts before the duck stands again. Not a measurement.
NAP_HOLD_S = 15.0 * 60.0
# Set point. After a nap, do not sit straight back down. Longer than the 8 s arousal time.
WAKE_AFTER_NAP_S = 60.0

NOT_AWAKE = ("nap", "charge")


def _load_guards():
    """Import the bench guards without baking a machine path into this file."""
    lab = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bench = os.path.join(lab, "bench")
    soft = os.path.join(lab, "software")
    for folder in (bench, soft):
        if folder not in sys.path:
            sys.path.insert(0, folder)
    import battery_guard as bg
    import knee_heat as kh
    return bg, kh


class MeasuredOutcomes:
    """Draws from the published 40 dock rows and the flat get-up count."""

    def __init__(self, seed=1):
        import random
        self.rng = random.Random(seed)

    def dock(self):
        return dict(self.rng.choice(MEASURED))

    def getup(self):
        # 112 of 112 on flat. A ramp rate is not used for this home floor.
        return self.rng.randrange(GETUP_FLAT_N) < GETUP_FLAT_OK


class Supervisor:
    def __init__(self, seed=1, outcomes=None, log_path=None, personality=None):
        bg, kh = _load_guards()
        self._bg = bg
        self._kh = kh
        self.personality = personality if personality is not None else Personality(seed=seed, mode="kid")
        self.assistant = Assistant(mode="kid", cloud="off", personality=self.personality)
        self.battery = bg.BatteryGuard(bg.GuardConfig(), state=bg.STANDING)
        self.knee = kh.KneeHeatGuard()
        self.outcomes = outcomes if outcomes is not None else MeasuredOutcomes(seed)
        self.log_path = log_path
        self.log_rows = []
        self.mode = "wander"
        self.motion = "stand"
        self.episode = None
        self.episode_left = 0.0
        self.episode_spent = 0.0
        self.dock_attempts = 0
        self.dock_success = 0
        self.dock_fails = 0
        self.falls = 0
        self.stuck_events = 0
        self.stuck = False
        self.on_nest = False
        self.getup_fails = 0
        self.getup_left = 0.0
        self.awake_s = 0.0
        self.min_pack_v = None
        self.nap_end = None
        self.wake_until = 0.0
        self._fall_open = False
        self._stood_pending = False
        self._charge_announced = False
        self._finish_pending = False
        self._help_counted = False
        self.t = 0.0

    def latest_command(self):
        return self.personality._command().as_dict()

    def step(self, plant, t, dt, events=None):
        events = list(events or [])
        self.t = float(t)
        if self._stood_pending:
            events.append("stood_up")
            self._stood_pending = False
            self._fall_open = False
        if self._finish_pending:
            events.append("charging_finished")
            self._finish_pending = False
            self._charge_announced = False
        if plant.fallen and not self._fall_open:
            events.append("fell_over")
            self.falls += 1
            self._fall_open = True
            self.getup_left = GETUP_S
            self._log(plant, "fall")
        if "petted" in events or "picked_up" in events:
            self._clear_stuck()

        if self.stuck:
            self.personality.help_me = True
        if self.on_nest and not self._charge_announced and plant.q_mAh > 0.0:
            events.append("charging_started")
            self._charge_announced = True

        sens = self._sensors(plant)
        self._guards(t, sens)
        cmd = self.personality.step(dt, sens, events)
        motion, mode = self._choose(plant, sens, cmd, t)
        self._run(plant, t, dt, motion, mode)
        self.t = plant.t
        if self.min_pack_v is None or plant.v_pack < self.min_pack_v:
            self.min_pack_v = plant.v_pack
        row = self._row(plant, cmd)
        if not self.log_rows or self.log_rows[-1]["mode"] != row["mode"] or self.log_rows[-1].get("camera") != row["camera"]:
            self._write(row)
        return row

    def _sensors(self, plant):
        return Sensors(
            pack_v=plant.v_pack,
            servo_median_v=RAIL_V,
            knee_c=plant.knee_c,
            idle_s=plant.idle_s,
            posture=plant.posture if plant.posture in ("standing", "walking", "sitting") else "standing",
            bearing_rad=plant.bearing,
            attention=plant.attention if plant.attention in ("none", "face", "sound") else "none",
            face_close=plant.face_close,
        )

    def _guards(self, t, sens):
        bg = self._bg
        walking = self.motion in ("walk", "stand", "getup") and not self.knee.latched
        self.battery.set_state(bg.WALKING if walking else bg.STANDING)
        volts = {sid: RAIL_V for sid in SERVO_IDS}
        self.battery.update(t, volts, sens.pack_v)
        cool = sens.knee_c is not None and sens.knee_c < KNEE_RESUME_C
        force_off = self.mode in ("nap", "charge", "stuck", "sit") or (
            self.mode == "knee_rest" and not cool
        )
        if self.knee.latched and cool and self.mode == "knee_rest":
            posture = "walking"
        elif force_off:
            posture = "sitting"
        else:
            posture = "walking"
        temps = {13: sens.knee_c, 23: sens.knee_c}
        self.knee.update(t, temps, posture)

    def _choose(self, plant, sens, cmd, t):
        pack = sens.pack_v
        if self.stuck:
            return "sit", "stuck"
        if plant.fallen or self.personality.fallen:
            if self.getup_fails >= GETUP_TRIES:
                self._become_stuck(plant, "getup")
                return "sit", "stuck"
            return "getup", "getup"
        if pack is not None and pack <= PACK_WALK_STOP_V and not self.on_nest:
            self._abort_dock(plant, "pack_at_walk_stop")
            self._become_stuck(plant, "pack")
            return "sit", "stuck"
        if plant.at_floor and not self.on_nest:
            self._become_stuck(plant, "pack_floor")
            return "sit", "stuck"
        hot = self.knee.latched or (sens.knee_c is not None and sens.knee_c >= KNEE_STOP_C and self.mode == "knee_rest")
        if self.knee.latched:
            if self.on_nest and plant.q_mAh > 0.0:
                return "charge", "charge"
            return "sit", "knee_rest"
        if self.on_nest and plant.q_mAh > 0.0:
            return "charge", "charge"
        if self.episode is not None or cmd.intent == "go_home" or self.personality.asked_home:
            return "walk", "dock"
        if hot:
            return "sit", "knee_rest"
        if cmd.intent == "nap" and t < self.wake_until:
            return "walk", "wander"
        if cmd.intent == "nap":
            return "sit", "nap"
        if cmd.priority == "social":
            if cmd.intent == "walk_to_person":
                return "walk", "social"
            return "stand", "social"
        if cmd.reason == "idle drowsy" and t >= self.wake_until:
            return "sit", "sit"
        if cmd.intent == "sit":
            return "sit", "sit"
        return "walk", "wander"

    def _run(self, plant, t, dt, motion, mode):
        if mode == "dock" and self.episode is None:
            self._begin_episode(plant)
        if mode == "nap" and self.nap_end is None:
            self.nap_end = t + NAP_HOLD_S
        if mode != "nap":
            self.nap_end = None
        left = float(dt)
        now = float(t)
        while left > 1e-9:
            slice_dt = left
            if mode == "dock" and self.episode is not None:
                slice_dt = min(slice_dt, max(self.episode_left, 0.0))
            if mode == "getup":
                slice_dt = min(slice_dt, max(self.getup_left, 0.0))
            if mode == "nap" and self.nap_end is not None:
                slice_dt = min(slice_dt, max(0.0, self.nap_end - now))
            if slice_dt <= 1e-12:
                break
            plant.advance(motion, slice_dt)
            if mode not in NOT_AWAKE:
                self.awake_s += slice_dt
            if mode == "dock" and self.episode is not None:
                self.episode_left -= slice_dt
                self.episode_spent += slice_dt
                if self.episode_left <= 1e-9:
                    self._finish_episode(plant)
                    if self.stuck:
                        mode, motion = "stuck", "sit"
                    elif self.on_nest:
                        mode, motion = "charge", "charge"
                    else:
                        mode, motion = "dock", "walk"
                        self._begin_episode(plant)
            if mode == "getup":
                self.getup_left -= slice_dt
                if self.getup_left <= 1e-9:
                    self._finish_getup(plant)
                    if self.stuck:
                        mode, motion = "stuck", "sit"
                    elif plant.fallen:
                        mode, motion = "getup", "getup"
                        self.getup_left = GETUP_S
                    else:
                        mode, motion = "wander", "walk"
            if mode == "nap" and self.nap_end is not None and now + slice_dt >= self.nap_end - 1e-9:
                self.wake_until = now + slice_dt + WAKE_AFTER_NAP_S
                mode, motion = "wander", "walk"
                self.nap_end = None
            if mode == "charge" and plant.q_mAh <= 1e-9:
                self.on_nest = False
                self._finish_pending = True
                mode, motion = "wander", "walk"
            now += slice_dt
            left -= slice_dt
        self.mode = mode
        self.motion = motion

    def _begin_episode(self, plant):
        self.episode = self.outcomes.dock()
        self.episode_left = float(self.episode["t_s"])
        self.episode_spent = 0.0
        self.dock_attempts += 1
        self._log(plant, "dock_attempt")

    def _finish_episode(self, plant):
        ep = self.episode
        self.episode = None
        self.episode_left = 0.0
        ok = bool(ep["charging"]) and not ep.get("fell")
        if ok:
            self.dock_success += 1
            self.dock_fails = 0
            self.on_nest = True
            self._charge_announced = False
        else:
            self.dock_fails += 1
            if self.dock_fails > RETRY_CAP:
                self._become_stuck(plant, "dock")
        self._log(plant, "dock_result", extra={"ok": ok, "seed": ep["seed"], "reason": ep["reason"]})

    def _finish_getup(self, plant):
        ok = bool(self.outcomes.getup())
        if ok:
            plant.fallen = False
            self._stood_pending = True
            self.getup_fails = 0
            self.getup_left = 0.0
            self._log(plant, "stood_up")
        else:
            self.getup_fails += 1
            self._log(plant, "getup_miss")
            if self.getup_fails >= GETUP_TRIES:
                self._become_stuck(plant, "getup")
                self.getup_left = 0.0
            else:
                self.getup_left = GETUP_S

    def _abort_dock(self, plant, why):
        if self.episode is None:
            return
        ep = self.episode
        self.episode = None
        self.episode_left = 0.0
        self.dock_fails += 1
        self._log(plant, "dock_abort", extra={"why": why, "seed": ep["seed"]})

    def _become_stuck(self, plant, why):
        was = self.stuck
        self.stuck = True
        self.personality.help_me = True
        if not was:
            self.stuck_events += 1
            self._help_counted = True
            self._log(plant, "stuck", extra={"why": why})

    def _clear_stuck(self):
        self.stuck = False
        self.dock_fails = 0
        self.getup_fails = 0
        self.personality.help_me = False
        self._help_counted = False

    def _row(self, plant, cmd):
        camera = None
        if self.mode == "dock" and self.episode is not None:
            camera = state_at(self.episode, self.episode_spent)
        return {
            "t": round(plant.t, 3),
            "mode": self.mode,
            "motion": self.motion,
            "expression": cmd.expression,
            "intent": cmd.intent,
            "pack_v": round(plant.v_pack, 4),
            "knee_c": round(plant.knee_c, 3),
            "q_mAh": round(plant.q_mAh, 3),
            "camera": camera,
            "awake_s": round(self.awake_s, 3),
            "dock_attempts": self.dock_attempts,
            "dock_success": self.dock_success,
            "falls": self.falls,
            "stuck_events": self.stuck_events,
        }

    def _log(self, plant, kind, extra=None):
        row = {
            "t": round(plant.t, 3),
            "kind": kind,
            "mode": self.mode,
            "pack_v": round(plant.v_pack, 4),
            "knee_c": round(plant.knee_c, 3),
        }
        if self.episode is not None:
            row["camera"] = state_at(self.episode, self.episode_spent)
            row["seed"] = self.episode["seed"]
        if extra:
            row.update(extra)
        self._write(row)

    def _write(self, row):
        self.log_rows.append(row)
        if not self.log_path:
            return
        folder = os.path.dirname(self.log_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def snapshot(self, plant):
        ep = None if self.episode is None else dict(self.episode)
        return {
            "supervisor": {
                "mode": self.mode,
                "motion": self.motion,
                "episode": ep,
                "episode_left": self.episode_left,
                "episode_spent": self.episode_spent,
                "dock_attempts": self.dock_attempts,
                "dock_success": self.dock_success,
                "dock_fails": self.dock_fails,
                "falls": self.falls,
                "stuck_events": self.stuck_events,
                "stuck": self.stuck,
                "on_nest": self.on_nest,
                "getup_fails": self.getup_fails,
                "getup_left": self.getup_left,
                "awake_s": self.awake_s,
                "min_pack_v": self.min_pack_v,
                "nap_end": self.nap_end,
                "wake_until": self.wake_until,
                "fall_open": self._fall_open,
                "stood_pending": self._stood_pending,
                "charge_announced": self._charge_announced,
                "finish_pending": self._finish_pending,
                "t": self.t,
            },
            "plant": plant.snapshot(),
            "personality": self.personality.export_state(),
            "knee_latched": self.knee.latched,
            "knee_n_hot": {str(k): v for k, v in self.knee.n_hot.items()},
            "knee_n_below": {str(k): v for k, v in self.knee.n_below.items()},
            "log_count": len(self.log_rows),
        }

    def restore(self, plant, saved):
        raw = saved["supervisor"]
        for name in (
            "mode", "motion", "episode_left", "episode_spent", "dock_attempts",
            "dock_success", "dock_fails", "falls", "stuck_events", "stuck",
            "on_nest", "getup_fails", "getup_left", "awake_s", "min_pack_v",
            "nap_end", "wake_until", "t",
        ):
            setattr(self, name, raw[name])
        self.episode = None if raw["episode"] is None else dict(raw["episode"])
        self._fall_open = raw["fall_open"]
        self._stood_pending = raw["stood_pending"]
        self._charge_announced = raw["charge_announced"]
        self._finish_pending = raw["finish_pending"]
        self.knee.latched = bool(saved["knee_latched"])
        self.knee.n_hot = {int(k): v for k, v in saved.get("knee_n_hot", {}).items()}
        self.knee.n_below = {int(k): v for k, v in saved.get("knee_n_below", {}).items()}
        plant.restore(saved["plant"])
        self.personality.import_state(saved["personality"])

    def summary(self, plant):
        return {
            "label": "sim pass only",
            "hours_awake": self.awake_s / 3600.0,
            "dock_attempts": self.dock_attempts,
            "dock_success": self.dock_success,
            "falls": self.falls,
            "stuck_events": self.stuck_events,
            "min_pack_v": None if self.min_pack_v is None else self.min_pack_v,
            "pack_v": plant.v_pack,
            "q_mAh": plant.q_mAh,
            "charge_a": CHARGE_A,
            "walk_pack_a": WALK_PACK_A,
            "min_pack_v_plant": plant.min_pack_v,
        }
