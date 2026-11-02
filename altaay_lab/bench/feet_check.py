#!/usr/bin/env python3
"""Foot switch checks (TEST_PLAN.md section 12, D17, D9).

Uses the Runtime's own reader: mini_bdx_runtime/feet_contacts.py FeetContacts (left GPIO22,
right GPIO27, internal pull-up, get() returns [left, right] with True = contact). Our build adds
a 2.2 kOhm pull-up per foot to 3V3 (D17); the logic is the same: closed switch = LOW = contact.
The walk feeds these two values into the policy every cycle (v2_rl_walk_mujoco.py lines 154
and 167), so a flicker is an input error.

Modes:
  --open            robot hanging, nothing on the feet: both read "no contact" for --seconds
                    with no change. Catches a missing pull-up or a short to ground.
  --presses N       press the LEFT foot N times, then the RIGHT foot N times (TEST_PLAN: 200).
                    Gates: N debounced presses per foot (no missed), no press held longer than
                    --stuck-s (no stuck), the other foot never changes while one is pressed (a
                    change there means the wires are swapped or shorted: D9 pins), chatter
                    (extra raw edges) reported.
  --stand           robot standing still on the floor: both read contact for --seconds (TEST_PLAN:
                    60) with zero changes, at --rate and at the 50 Hz walk rate.
Before power (meter, not software): each foot circuit under 1 ohm closed, over 1 Mohm open,
measured at the Pi header (listed as MANUAL in every report).
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import paths, report  # noqa: E402


class Debounce:
    def __init__(self, debounce_s):
        self.d = debounce_s
        self.state = None
        self.cand = None
        self.cand_t = None
        self.raw_edges = 0
        self.last_raw = None

    def push(self, t, raw):
        """Returns +1 on a debounced press, -1 on a debounced release, 0 otherwise."""
        if self.last_raw is not None and raw != self.last_raw:
            self.raw_edges += 1
        self.last_raw = raw
        if self.state is None:
            self.state = raw
            return 0
        if raw == self.state:
            self.cand = None
            return 0
        if self.cand != raw:
            self.cand, self.cand_t = raw, t
            return 0
        if t - self.cand_t >= self.d:
            self.state, self.cand = raw, None
            return 1 if raw else -1
        return 0


def poll(fc, seconds, rate, until=None):
    """Yield (t, left, right) at about `rate` Hz."""
    t0 = time.perf_counter()
    k = 0
    while True:
        t = time.perf_counter() - t0
        if seconds and t > seconds:
            return
        left, right = fc.get()
        yield t, bool(left), bool(right)
        if until and until():
            return
        k += 1
        time.sleep(max(0.0, t0 + k / rate - time.perf_counter()))


def steady(fc, rep, item, want, seconds, rate, desc):
    n = changes = changes50 = 0
    wrong = [0, 0]
    prev = None
    last50, next50 = None, 0.0
    for t, l, r in poll(fc, seconds, rate):
        n += 1
        wrong[0] += l != want
        wrong[1] += r != want
        if prev is not None and (l, r) != prev:
            changes += 1
        prev = (l, r)
        if t >= next50:                      # what the 50 Hz walk loop would see
            if last50 is not None and (l, r) != last50:
                changes50 += 1
            last50 = (l, r)
            next50 += 0.02
    hz = n / seconds if seconds else 0
    rep.add(f"{item}.rate", "poll rate", "INFO", f"{hz:.0f} Hz ({n} samples)")
    rep.gate(item, desc, wrong == [0, 0] and changes == 0,
             f"wrong left {wrong[0]}, wrong right {wrong[1]}, changes {changes} (at 50 Hz: {changes50})",
             "0 wrong, 0 changes", "TEST_PLAN 12")


def presses(fc, rep, n, rate, debounce_s, stuck_s, timeout_s, assume_yes):
    for side, idx in (("left", 0), ("right", 1)):
        other = 1 - idx
        if not report.confirm(f"Press the robot's {side.upper()} foot {n} times (one at a time), then wait.",
                              assume_yes):
            rep.add(f"12.{side}", "not run", "INCOMPLETE")
            continue
        db = Debounce(debounce_s)
        dbo = Debounce(debounce_s)
        count = 0
        stuck = []
        press_t = None
        other_changes = 0
        last_print = 0
        state = {"count": 0}
        start = time.perf_counter()
        for t, l, r in poll(fc, timeout_s, rate, until=lambda: state["count"] >= n):
            v = (l, r)
            e = db.push(t, v[idx])
            if dbo.push(t, v[other]) != 0:
                other_changes += 1
            if e == 1:
                count += 1
                state["count"] = count
                press_t = t
            elif e == -1 and press_t is not None:
                if t - press_t > stuck_s:
                    stuck.append(round(t - press_t, 2))
                press_t = None
            if t - last_print > 2.0:
                print(f"{side}: {count} presses", flush=True)
                last_print = t
        # wait for the last release (or note a stuck switch)
        tail_end = time.perf_counter() + max(stuck_s, 0.5)
        while press_t is not None and time.perf_counter() < tail_end:
            l, r = fc.get()
            if db.push(time.perf_counter() - start, (l, r)[idx]) == -1:
                press_t = None
            time.sleep(1.0 / rate)
        if press_t is not None:
            stuck.append("held at the end")
        chatter = max(0, db.raw_edges - 2 * count)
        rep.gate(f"12.{side}.count", f"{side} foot: debounced presses (no missed)", count == n, count, n, "TEST_PLAN 12")
        rep.gate(f"12.{side}.stuck", f"{side} foot: no stuck reading (> {stuck_s} s)", not stuck, stuck or "none",
                 "none", "TEST_PLAN 12")
        rep.gate(f"12.{side}.other", f"other foot did not change while pressing {side} (wiring D9)",
                 other_changes == 0, other_changes, "0", "feet_contacts.py pins D22 left, D27 right")
        rep.add(f"12.{side}.chatter", f"{side} foot: extra raw edges (switch bounce)", "PASS" if chatter == 0 else "WARN",
                chatter, f"0 (debounce {debounce_s * 1e3:.0f} ms)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--open", action="store_true")
    m.add_argument("--presses", type=int, metavar="N")
    m.add_argument("--stand", action="store_true")
    ap.add_argument("--seconds", type=float, default=None, help="open: 10, stand: 60")
    ap.add_argument("--rate", type=float, default=500.0, help="poll rate in Hz")
    ap.add_argument("--debounce-ms", type=float, default=20.0)
    ap.add_argument("--stuck-s", type=float, default=3.0)
    ap.add_argument("--timeout", type=float, default=600.0, help="presses: give up after this many seconds per foot")
    ap.add_argument("--runtime")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rt = paths.find_runtime(a.runtime)
    paths.use_runtime(rt)
    from mini_bdx_runtime.feet_contacts import FeetContacts  # noqa: E402  (Runtime, unmodified)
    rep = report.Report("feet_check", "12", "Foot switches")
    rep.add("12.meter", "before power: each foot circuit < 1 ohm closed, > 1 Mohm open, at the Pi header",
            "MANUAL", None, None, "TEST_PLAN 12")
    fc = FeetContacts()
    try:
        if a.open:
            if report.confirm("Robot hanging, nothing touching the feet?", a.yes):
                steady(fc, rep, "12.open", False, a.seconds or 10.0, a.rate, "hanging: both feet read no contact")
        elif a.stand:
            if report.confirm("Robot standing still on the floor?", a.yes):
                steady(fc, rep, "12.stand", True, a.seconds or 60.0, a.rate,
                       "standing still: both feet read contact without a flicker")
        else:
            presses(fc, rep, a.presses, a.rate, a.debounce_ms / 1e3, a.stuck_s, a.timeout, a.yes)
    finally:
        fc.stop()
    if not any(i["status"] in ("PASS", "FAIL") for i in rep.items):
        rep.add("12", "nothing measured", "INCOMPLETE")
    return rep.finish(paths.out_dir(a.out, "feet"))


if __name__ == "__main__":
    sys.exit(main())
