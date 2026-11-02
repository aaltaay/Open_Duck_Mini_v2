#!/usr/bin/env python3
"""Software battery cut-off (DECISIONS.md D16, TEST_PLAN.md section 11).

The Tenergy BMS cuts only at 2.40 V per cell, below the Molicel P30B 2.5 V minimum (D16), and
the stock build has no pack voltage sense. The guard reads servo Present Voltage (register 62,
0.1 V steps) of all 14 servos at a low rate and decides on the MEDIAN of the 14 readings, so a
single ankle dipping during a knee peak does not stop the robot.

Rules (defaults; every number is a flag):
  walk stop    while walking: 5 s mean of the median <= 6.0 V. The lab power sim (star wiring,
               typical corner, sim pass only) puts that at about 3.57 V per cell open circuit,
               i.e. about 7.0 V pack terminal under walking load = D16 "about 3.5 V per cell
               under load". Then: zero command, step in place 1 s, freeze when both feet read
               contact, blend to the standing pose (walk_with_guard.py does the moves).
  hard stop    when standing (after a walk stop, or in --monitor standing mode): 3 s mean of the
               median <= 6.0 V = D16 "hard stop at servo Present Voltage 6.0 V (about 3.3 V per
               cell)". Also while walking if the 2 s mean falls to 5.4 V (sim: about 3.3 V per cell
               under walking load) because the voltage dropped faster than the walk stop could act.
               Then: low gains, torque off, power off the Pi.
  start check  refuse to start walking if the idle median is under 6.8 V (rest model: pack minus
               the 0.3 V BEC dropout assumed in sim/POWER_PATH_SIM.md, about 3.55 V per cell).
  lost reads   5 s without a valid reading while walking -> walk stop (fail safe).
Readings outside 3.0 to 9.0 V are dropped as implausible (counted).

Why not D16 literally ("hard stop at 6.0 V") while walking: the sim median reads 6.0 V while
walking at about 3.57 V per cell, which is where the walk stop should act; a torque-off there
would drop a walking robot. At light load 6.0 V is about 3.2 to 3.3 V per cell, D16's intent.
The thresholds depend on the real path resistance (TEST_PLAN sections 4 and 5): re-check them
with --monitor and a bench supply before trusting them (SOFTWARE.md section 5).

Modes:
  --replay CSV      run the rules on a voltage profile (t_s, v_<id> columns, as in
                    tests/data/sim_star_*.csv) and print the events (no hardware)
  --monitor         read the servos with pypot (check_voltage.py's calls) at --period and run
                    the rules; with --act a hard stop disables torque; --poweroff-cmd runs at a
                    hard stop (default: print only)
"""
import argparse
import os
import statistics
import subprocess
import sys
import time
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import joints, paths, report  # noqa: E402

WALKING, STOPPING, STANDING, HARD_STOPPED = "walking", "stopping", "standing", "hard_stopped"


class GuardConfig:
    def __init__(self, **kw):
        self.period_s = 0.5
        self.walk_stop_v = 6.0
        self.walk_stop_hold_s = 5.0
        self.hard_stop_v = 6.0
        self.hard_stop_hold_s = 3.0
        self.walking_floor_v = 5.4
        self.walking_floor_hold_s = 2.0
        self.start_min_v = 6.8
        self.lost_reads_s = 5.0
        self.v_min_plausible = 3.0
        self.v_max_plausible = 9.0
        self.min_servos = 7          # a sample needs at least half the servos to answer
        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError(f"unknown guard option {k}")
            setattr(self, k, v)

    def as_dict(self):
        return dict(vars(self))


class Window:
    """Mean of the last `hold_s` of samples; full only when it spans hold_s."""

    def __init__(self, hold_s, period_s):
        self.n = max(1, int(round(hold_s / period_s)))
        self.q = deque(maxlen=self.n)

    def push(self, v):
        self.q.append(v)

    def clear(self):
        self.q.clear()

    def full(self):
        return len(self.q) == self.n

    def mean(self):
        return sum(self.q) / len(self.q) if self.q else None


class BatteryGuard:
    """Pure decision logic. Feed one sample per period; it returns new events.

    update(t, volts) where volts is {servo_id: volts} or None for a failed read.
    Events are dicts: {"t", "event", "reason", "value"}; event in
    walk_stop, hard_stop, warn_lost_reads, sample_dropped.
    The caller sets the motion state with set_state() (walk_with_guard.py does).
    """

    def __init__(self, cfg=None, state=WALKING):
        self.cfg = cfg or GuardConfig()
        c = self.cfg
        self.state = state
        self.w_walk = Window(c.walk_stop_hold_s, c.period_s)
        self.w_hard = Window(c.hard_stop_hold_s, c.period_s)
        self.w_floor = Window(c.walking_floor_hold_s, c.period_s)
        self.last_valid_t = None
        self.t_start = None
        self.events = []
        self.samples = 0
        self.dropped = 0
        self.last_median = None
        self.last_min = None
        self.lost_warned = False

    def set_state(self, state):
        if state != self.state:
            self.state = state
            self.w_hard.clear()          # the standing level is measured fresh after a stop

    def _event(self, t, name, reason, value=None):
        e = dict(t=round(t, 3), event=name, reason=reason, value=None if value is None else round(value, 3),
                 state=self.state)
        self.events.append(e)
        return e

    def median_of(self, volts):
        c = self.cfg
        good = [v for v in (volts or {}).values() if v is not None and c.v_min_plausible <= v <= c.v_max_plausible]
        bad = len(volts or {}) - len(good)
        if bad:
            self.dropped += bad
        if len(good) < c.min_servos:
            return None, good
        return statistics.median(good), good

    def check_start(self, volts):
        """True if walking may start; idle reading before torque-on."""
        med, _ = self.median_of(volts)
        return med is not None and med >= self.cfg.start_min_v, med

    def update(self, t, volts):
        c = self.cfg
        new = []
        if self.t_start is None:
            self.t_start = t
        if self.state == HARD_STOPPED:
            return new
        med, good = self.median_of(volts)
        if med is None:
            ref = self.last_valid_t if self.last_valid_t is not None else self.t_start
            if t - ref >= c.lost_reads_s:
                if self.state == WALKING:
                    new.append(self._event(t, "walk_stop", f"no valid voltage reading for {t - ref:.1f} s"))
                    self.state = STOPPING
                elif not self.lost_warned:
                    new.append(self._event(t, "warn_lost_reads", f"no valid voltage reading for {t - ref:.1f} s"))
                    self.lost_warned = True
            return new
        self.samples += 1
        self.lost_warned = False
        self.last_valid_t = t
        self.last_median, self.last_min = med, min(good)
        self.w_walk.push(med); self.w_hard.push(med); self.w_floor.push(med)
        if self.state in (WALKING, STOPPING):
            if self.w_floor.full() and self.w_floor.mean() <= c.walking_floor_v:
                new.append(self._event(t, "hard_stop", f"{self.state}: {c.walking_floor_hold_s:g} s mean of the servo "
                                       f"median <= {c.walking_floor_v} V", self.w_floor.mean()))
                self.state = HARD_STOPPED
            elif self.state == WALKING and self.w_walk.full() and self.w_walk.mean() <= c.walk_stop_v:
                new.append(self._event(t, "walk_stop", f"walking: {c.walk_stop_hold_s:g} s mean of the servo median "
                                       f"<= {c.walk_stop_v} V", self.w_walk.mean()))
                self.state = STOPPING
        elif self.state == STANDING:
            if self.w_hard.full() and self.w_hard.mean() <= c.hard_stop_v:
                new.append(self._event(t, "hard_stop", f"standing: {c.hard_stop_hold_s:g} s mean of the servo median "
                                       f"<= {c.hard_stop_v} V", self.w_hard.mean()))
                self.state = HARD_STOPPED
        return new


# ---------------------------------------------------------------- profiles and replay
def load_profile(path):
    """CSV with t_s and v_<id> columns (comment lines start with #). Returns (t list, {id: list})."""
    with open(path) as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    cols = lines[0].strip().split(",")
    vid = [(k, int(c[2:])) for k, c in enumerate(cols) if c.startswith("v_")]
    t, v = [], {i: [] for _, i in vid}
    for ln in lines[1:]:
        f = ln.strip().split(",")
        if len(f) < len(cols):
            continue
        t.append(float(f[0]))
        for k, i in vid:
            v[i].append(float(f[k]))
    return t, v


def quantize(v):
    """Register 62 holds whole 0.1 V steps; floor is the conservative assumption (UNVERIFIED)."""
    import math
    return math.floor(v * 10.0 + 1e-6) / 10.0


def replay(path, cfg, standing_offset=0.5, quant=True, sample_offset=0.0):
    """Sample the profile at cfg.period_s and run the guard. After a walk stop the walking-load
    profile no longer applies; `standing_offset` (V) models the voltage recovery when the load
    drops to standing (estimate, UNVERIFIED; the real guard measures it)."""
    t, v = load_profile(path)
    g = BatteryGuard(cfg)
    k = 0
    tt = t[0] + sample_offset
    stopped_at = None
    trace = []
    while tt <= t[-1]:
        while k + 1 < len(t) and t[k + 1] <= tt:
            k += 1
        volts = {}
        for i, col in v.items():
            x = col[k]
            if g.state != WALKING:
                x += standing_offset
            volts[i] = quantize(x) if quant else x
        ev = g.update(tt, volts)
        for e in ev:
            if e["event"] == "walk_stop":
                stopped_at = tt
                g.set_state(STANDING)
        trace.append((tt, g.last_median, g.state))
        if g.state == HARD_STOPPED:
            break
        tt += cfg.period_s
    return g, trace, stopped_at


# ---------------------------------------------------------------- bench monitor (hardware)
class VoltageReader:
    """Reads Present Voltage of the 14 servos with pypot, as Runtime check_voltage.py does
    (FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=True), get_present_voltage(ids), x 0.1).
    Uses our per-ID sync read so one silent servo does not blank the other 13."""

    def __init__(self, io, ids=None, errors=None):
        from odm_bench import bus
        self.bus = bus
        self.io = io
        self.ids = list(ids or joints.IDS)
        self.errors = errors
        self.reads = 0
        self.failures = 0
        self.last_duration_s = None

    def read(self):
        t0 = time.perf_counter()
        self.reads += 1
        try:
            got, failed = self.bus.sync_read_block(self.io, self.ids, 62, 1, self.errors)
        except Exception as e:      # noqa: BLE001 - any bus error is a failed sample
            self.failures += 1
            if self.errors is not None:
                self.errors.add("pypot", "voltage_read_exception", None, repr(e))
            return None
        finally:
            self.last_duration_s = time.perf_counter() - t0
        if not got:
            self.failures += 1
            return None
        return {i: d[0] * 0.1 for i, d in got.items()}


def run_monitor(a):
    from odm_bench import bus
    rep = report.Report("battery_guard", "11", "Battery guard bench monitor")
    out = paths.out_dir(a.out, "battery_guard")
    errors = bus.BusErrors()
    io = bus.open_pypot(a.port, sync_read=True, errors=errors)
    reader = VoltageReader(io, errors=errors)
    cfg = config_from_args(a)
    g = BatteryGuard(cfg, state=WALKING if a.state == "walking" else STANDING)
    log = open(out / f"guard_monitor_{paths.stamp()}.csv", "w")
    log.write("t_s,median_v,min_v,state,event\n")
    print(f"monitoring {a.port} every {cfg.period_s} s as '{g.state}'; Ctrl-C to stop")
    t0 = time.monotonic()
    first = None
    try:
        while True:
            t = time.monotonic() - t0
            volts = reader.read()
            if first is None and volts:
                ok, med = g.check_start(volts)
                first = med
                rep.add("11.start", "start check: idle servo median", "PASS" if ok else "WARN", med,
                        f">= {cfg.start_min_v} V", "battery_guard.py start rule")
            ev = g.update(t, volts)
            names = ";".join(e["event"] for e in ev)
            log.write(f"{t:.2f},{g.last_median},{g.last_min},{g.state},{names}\n"); log.flush()
            print(f"t {t:7.1f}s  median {g.last_median}  min {g.last_min}  state {g.state}  {names}")
            for e in ev:
                rep.add(f"11.{e['event']}", e["reason"], "INFO", e["value"], None, f"t {e['t']} s")
                if e["event"] == "walk_stop" and a.state == "walking":
                    g.set_state(STANDING)
                if e["event"] == "hard_stop":
                    if a.act:
                        io.disable_torque(joints.IDS)
                        print("torque disabled on all 14 servos (pypot disable_torque)")
                    if a.poweroff_cmd:
                        print(f"running: {a.poweroff_cmd}")
                        subprocess.run(a.poweroff_cmd, shell=True, check=False)
            if g.state == HARD_STOPPED or (a.seconds and t >= a.seconds):
                break
            time.sleep(max(0.0, cfg.period_s - (time.monotonic() - t0 - t)))
    except KeyboardInterrupt:
        pass
    log.close()
    rep.add("11.reads", "voltage reads (failed)", "INFO", f"{reader.reads} ({reader.failures})")
    rep.add("11.bus", "bus errors", "INFO", errors.snapshot())
    rep.data["events"] = g.events
    rep.data["config"] = cfg.as_dict()
    return rep.finish(out, "battery_guard_monitor")


def config_from_args(a):
    return GuardConfig(period_s=a.period, walk_stop_v=a.walk_stop_v, walk_stop_hold_s=a.walk_stop_hold,
                       hard_stop_v=a.hard_stop_v, hard_stop_hold_s=a.hard_stop_hold,
                       walking_floor_v=a.walking_floor_v, start_min_v=a.start_min_v,
                       lost_reads_s=a.lost_reads)


def add_guard_args(ap):
    d = GuardConfig()
    g = ap.add_argument_group("guard thresholds (D16; see the module help)")
    g.add_argument("--period", type=float, default=d.period_s, help="seconds between voltage reads (default 0.5)")
    g.add_argument("--walk-stop-v", type=float, default=d.walk_stop_v)
    g.add_argument("--walk-stop-hold", type=float, default=d.walk_stop_hold_s)
    g.add_argument("--hard-stop-v", type=float, default=d.hard_stop_v)
    g.add_argument("--hard-stop-hold", type=float, default=d.hard_stop_hold_s)
    g.add_argument("--walking-floor-v", type=float, default=d.walking_floor_v)
    g.add_argument("--start-min-v", type=float, default=d.start_min_v)
    g.add_argument("--lost-reads", type=float, default=d.lost_reads_s)
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--replay", metavar="CSV", help="run the rules on a voltage profile (no hardware)")
    m.add_argument("--monitor", action="store_true", help="read the servos and run the rules (bench)")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--state", choices=("walking", "standing"), default="standing",
                    help="monitor: which rules apply (bench supply sweeps: try both)")
    ap.add_argument("--act", action="store_true", help="monitor: disable torque at a hard stop")
    ap.add_argument("--poweroff-cmd", default="", help="monitor: command run at a hard stop")
    ap.add_argument("--seconds", type=float, default=0, help="monitor: stop after this many seconds")
    ap.add_argument("--standing-offset", type=float, default=0.5,
                    help="replay: volts added after a walk stop (load drops; estimate)")
    ap.add_argument("--expect", choices=("none", "walk_stop", "hard_stop"),
                    help="replay: PASS if this is the last event (tests and what-if runs)")
    ap.add_argument("--out", help="log folder (default ODM_BENCH_OUT or ~/odm_bench_logs)")
    add_guard_args(ap)
    a = ap.parse_args(argv)
    if a.monitor:
        return run_monitor(a)
    cfg = config_from_args(a)
    g, trace, stopped_at = replay(a.replay, cfg, a.standing_offset)
    rep = report.Report("battery_guard", "11", f"Battery guard replay of {os.path.basename(a.replay)}")
    for e in g.events:
        rep.add(f"11.{e['event']}", e["reason"], "INFO", e["value"], None, f"t {e['t']} s")
    meds = [m for _, m, _ in trace if m is not None]
    rep.add("11.median", "servo median over the replay (min / max)", "INFO",
            f"{min(meds):.2f} / {max(meds):.2f} V" if meds else None)
    last = g.events[-1]["event"] if g.events else "none"
    if a.expect:
        rep.gate("11.expect", "last guard event matches the expectation", last == a.expect, last, a.expect)
    rep.data["events"] = g.events
    rep.data["config"] = cfg.as_dict()
    return rep.finish(paths.out_dir(a.out, "battery_guard") if a.out else None)


if __name__ == "__main__":
    sys.exit(main())
