"""power_log.py (TEST_PLAN 8.1 inventory and 9 walking log) on the simulated bus.

The walking log reads Present Voltage on its own timer, only in the walk loop's sleep, and counts
the time under 6.0 V by phase of the control cycle (odm_bench/vsampler.py). The first tests drive
that code with a virtual clock and a synthetic voltage whose exact time share is known; the last
ones run the real Runtime walk loop on the simulated bus.
"""
import bisect
import random

import power_log as pl
from conftest import DATA, IDS, ONNX, item, last_report, needs_libs, needs_walk
from fake_sts3215 import VoltageProfile
from odm_bench import report, vsampler


@needs_libs
def test_idle_inventory_pass(make_bus, run):
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.mem[22] = 0                                 # configured: P 32, D 0, I 0
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "2")
    rep = last_report(out, "power_log")
    assert r.returncode == 0, r.stdout[-3000:]
    for k in ("8.1.ids", "8.1.fw", "8.1.r85", "8.1.pid", "9.v4.5", "9.checksum"):
        assert item(rep, k)["status"] == "PASS", item(rep, k)
    assert int(item(rep, "9.samples")["measured"].split(" / ")[0]) >= 80


@needs_libs
def test_idle_inventory_catches_reg85_firmware_and_missing(make_bus, run):
    bus = make_bus(ids=[i for i in IDS if i != 33], reg85=0, volts=7.2)
    bus.servos[24].mem[85] = 50
    bus.servos[13].mem[0], bus.servos[13].mem[1] = 3, 9
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "1")
    rep = last_report(out, "power_log")
    assert r.returncode == 1
    assert item(rep, "8.1.ids")["status"] == "FAIL" and "33" in item(rep, "8.1.ids")["measured"]
    assert item(rep, "8.1.r85")["measured"] == [24]
    assert item(rep, "8.1.fw")["status"] == "FAIL"


@needs_libs
def test_checksum_errors_fail_the_log(make_bus, run):
    bus = make_bus(reg85=0, volts=7.2)
    bus.fault(31).corrupt_next = 5
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "1")
    rep = last_report(out, "power_log")
    assert item(rep, "9.checksum")["status"] == "FAIL"
    assert item(rep, "9.checksum")["measured"] >= 1


# ---------------------------------------------------------------- virtual clock: exact answers
class VClock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += max(0.0, s)


class FixedTimer(vsampler.SlotTimer):
    """A plain fixed-period timer (no random time in the slot): what TEST_PLAN 9's 'every 27 ms' reads as."""

    def __init__(self, period_s, offset):
        super().__init__(period_s, 0)
        self.offset = offset

    def start(self, t0):
        self.t0, self.k = float(t0), 0
        self.due = self.t0 + self.offset * self.period_s

    def advance(self):
        self.k += 1
        self.due = self.t0 + (self.k + self.offset) * self.period_s


def virtual_walk(seconds=120.0, period_s=0.020, busy_s=0.006, dip_s=0.004, dip_cycles=None, gait=27,
                 cost_s=0.003, latch_s=0.0003, write_delay_s=0.0005, jitter_s=0.0005, sample_period_s=0.027,
                 seed=27, timer=None, per_cycle_at=None):
    """The Runtime loop on a virtual clock: each cycle spends busy_s (its two reads, the policy step,
    the goal write), then calls the scheduler in place of time.sleep(period - took), as walkhooks
    does. Both ankles read 5.6 V for dip_s after each goal write reaches them (write_delay_s after
    the write call returns), in the cycles of the gait listed in dip_cycles (all if None), else 6.6 V.
    A read costs cost_s and latches the voltage latch_s after it starts.
    per_cycle_at: also take the old once-per-cycle reading, at this time after the cycle start.
    Returns (timer rows, per-cycle rows, stats, exact share of the time under 6 V)."""
    c = VClock()
    rng = random.Random(seed)
    st = dict(state="walk", last_write=None, prev_write=None, cycle=0)
    arrivals, t_arr = [], []

    def on(cyc):
        return dip_cycles is None or (cyc % gait) in dip_cycles

    def volts(t):
        k = bisect.bisect_right(t_arr, t) - 1
        if k < 0:
            return 6.6
        return 5.6 if on(arrivals[k][1]) and t - arrivals[k][0] < dip_s else 6.6

    def row(status, state, phase, room, v=None):
        r = dict(status=status, state=state, phase_ms="" if phase is None else f"{phase * 1e3:.4f}",
                 room_ms="" if room is None else f"{room * 1e3:.4f}", failed="")
        for i in IDS:                     # the ankles dip; the other 12 servos hold 6.6 V
            r[f"v_{i}"] = "" if v is None else f"{v if i in (24, 14) else 6.6:.1f}"
        return r

    rows, per_cycle = [], []

    def read(end_by):
        v = volts(c.t + latch_s)
        c.t += cost_s
        return v

    def on_slot(rec):
        rows.append(row(rec["status"], rec["state"], rec.get("phase"), rec.get("room"), rec.get("result")))

    task = vsampler.TimedRead("v", read, period_s=sample_period_s, seed=seed, margin_s=0.001, first_cost_s=cost_s,
                              on_slot=on_slot, clock=c.now)
    if timer is not None:
        task.timer = timer
    sch = vsampler.IdleScheduler([task], clock=c.now, sleep=c.sleep, ctx=lambda: dict(st))
    sch.start(0.0)
    while c.t < seconds:
        t_cycle = c.t
        c.t += busy_s + rng.uniform(-jitter_s, jitter_s)
        st["prev_write"], st["last_write"] = st["last_write"], c.t
        st["cycle"] += 1
        arrivals.append((c.t + write_delay_s, st["cycle"]))
        t_arr.append(c.t + write_delay_s)
        if per_cycle_at is not None and st["prev_write"] is not None:
            t_s = t_cycle + per_cycle_at
            lw = c.t if t_s >= c.t else st["prev_write"]
            per_cycle.append(row("cycle", "walk", t_s - lw, None, volts(t_s)))
        rows.append(dict(t_s=f"{c.t:.6f}", status="write", state="walk"))
        sch.idle(max(0.0, period_s - (c.t - t_cycle)))
    # exact share of the time under 6 V between the first and the last goal write (the span the
    # time count weighs): each dip lasts dip_s or until the next write arrives
    a, b = t_arr[0] - write_delay_s, t_arr[-1] - write_delay_s
    under = sum(max(0.0, min(t1 + dip_s, t2, b) - max(t1, a)) for (t1, cyc), (t2, _) in zip(arrivals, arrivals[1:])
                if on(cyc))
    return rows, per_cycle, task.stats(), under / (b - a)


def test_time_count_matches_the_exact_share_at_any_coverage():
    """A dip locked to the goal writes (4 ms of every 20.2 ms cycle: 19.8 % of the time). The
    Runtime's busy part grows from 4 to 10 ms, so the timer reads 60 % down to 30 % of the walk.
    The phase-weighted count stays within 1 point of the exact share; the share of readings (U)
    does not, which is why it is not the gate value. When the busy part is so long that the read
    part of the cycle ends inside the dip, the count can only come out high."""
    u_err = []
    for busy in (0.004, 0.007, 0.010):
        rows, _, st, exact = virtual_walk(period_s=0.0202, busy_s=busy)
        d = vsampler.time_count(rows, [24])[24]
        assert abs(exact - 0.198) < 0.002, exact
        assert abs(d["time_frac"] - exact) <= 0.01, (busy, d["time_frac"], exact, st)
        assert d["walk_frac"] <= exact + 0.01                   # L: never above the true share
        u_err.append(d["sampled_frac"] - exact)                 # U: too high when the busy part is unread
        assert st["overruns"] == 0 and st["read"] + st["busy"] + st["own"] + st["room"] == st["slots"]
        assert vsampler.recovery_ok(d)
    assert min(u_err) > 0.05 and u_err[-1] > 0.2, u_err
    rows, _, st, exact = virtual_walk(period_s=0.0202, busy_s=0.0135)    # reads end 2.7 ms after the write
    d = vsampler.time_count(rows, [24])[24]
    assert d["walk_frac"] <= exact + 0.01 and d["time_frac"] >= exact, (d["time_frac"], exact)


def test_the_phase_locked_old_count_is_fooled_and_the_timer_is_not():
    """The old log read once per control cycle, at the cycle start, before the Runtime's reads:
    always 14 ms after the last goal write here, long after the 4 ms dip. It counts 0 % for an
    exact 19.8 %. Read 1 to 2 ms after the write instead, it counts 100 %. The timer counts 19.8 %."""
    rows, early, _, exact = virtual_walk(period_s=0.0202, per_cycle_at=0.0)
    old = sum(float(r["v_24"]) < 6.0 for r in early) / len(early)
    assert old == 0.0 and abs(exact - 0.198) < 0.002
    _, late, _, _ = virtual_walk(period_s=0.0202, per_cycle_at=0.0075)     # 1 to 2 ms after the write
    assert sum(float(r["v_24"]) < 6.0 for r in late) / len(late) > 0.95
    d = vsampler.time_count(rows, [24])[24]
    assert abs(d["time_frac"] - exact) <= 0.01
    rep = report.Report("t", "9", "t")
    pl.analyze(early, "nominal", rep, min_samples=50)
    assert item({"items": rep.items}, "9.time6")["status"] == "INCOMPLETE"   # a phase sample cannot score
    assert item({"items": rep.items}, "9.coverage")["status"] == "WARN"


def test_a_fixed_27_ms_timer_locks_to_the_gait_and_the_random_timer_does_not():
    """27 ms is exactly 1/20 of the 540 ms gait (27 control cycles of 20.0 ms): a fixed 27 ms
    timer reads the same 20 points of every step cycle. With the dip only in 9 of the 27 cycles
    (exact 6.67 %), its count depends on when it starts: 0 to 10 %. One read at a random time in
    each 27 ms slot stays within 1.5 points of the exact share on every seed."""
    fixed = []
    for offset in (0.1, 0.3, 0.5, 0.7, 0.9):
        rows, _, _, exact = virtual_walk(seconds=60, period_s=0.020, busy_s=0.004, dip_cycles=range(9), jitter_s=0.0,
                                         cost_s=0.002, timer=FixedTimer(0.027, offset))
        fixed.append(vsampler.time_count(rows, [24])[24]["time_frac"])
    assert abs(exact - 9 / 27 * 0.2) < 0.002, exact
    assert max(fixed) - min(fixed) > 0.08 and min(fixed) < 0.01, fixed
    rand = []
    for seed in (1, 2, 3, 4, 5):
        rows, _, _, exact = virtual_walk(seconds=60, period_s=0.020, busy_s=0.004, dip_cycles=range(9), jitter_s=0.0,
                                         cost_s=0.002, seed=seed)
        rand.append(vsampler.time_count(rows, [24])[24]["time_frac"])
    assert all(abs(x - exact) <= 0.015 for x in rand), (rand, exact)
    assert abs(sum(rand) / len(rand) - exact) <= 0.006, (rand, exact)


def test_scheduler_reads_only_in_the_sleep_and_records_a_late_read():
    """A read starts only if its expected time plus the margin ends before the sleep would end.
    One read that takes far longer than the ones before it ends late; it is counted, not hidden."""
    c = VClock()
    times = []
    durations = iter([0.002] * 30 + [0.015] + [0.002] * 500)

    def read(end_by):
        times.append((c.t, end_by))
        c.t += next(durations)
        return 7.0
    task = vsampler.TimedRead("v", read, period_s=0.027, seed=3, margin_s=0.001, first_cost_s=0.004, clock=c.now)
    sch = vsampler.IdleScheduler([task], clock=c.now, sleep=c.sleep, ctx=lambda: dict(state="walk", last_write=c.t))
    sch.start(0.0)
    sleeps = []
    while c.t < 10.0:
        c.t += 0.006                                  # busy part of the cycle
        start = c.t
        sch.idle(0.014)
        sleeps.append((start, start + 0.014, c.t))
    st = task.stats()
    assert st["read"] > 100 and st["busy"] > 0 and st["room"] > 0
    assert st["overruns"] <= 1 and st["overrun_max_ms"] <= 13.0, st
    late = [(a, b, e) for a, b, e in sleeps if e > b + 1e-9]
    assert len(late) == st["overruns"]
    for t_start, end_by in times:                     # every read was given the end of its sleep
        assert any(a <= t_start < b and end_by <= b for a, b, _ in sleeps)


def _rows(volts_by_id, n=400, phase=None, busy_every=0):
    """Synthetic log rows: n readings; with busy_every, one more unread slot (18 ms after the write,
    in the Runtime's busy part) after every busy_every readings."""
    rows = []
    for k in range(n):
        r = {"t_s": f"{k * 0.027:.3f}", "status": "read", "state": "walk", "failed": "",
             "phase_ms": "" if phase is None else f"{phase(k):.3f}", "room_ms": "" if phase is None else "12.0"}
        for i in IDS:
            r[f"v_{i}"] = f"{volts_by_id(i, k):.1f}"
            r[f"i_{i}"] = "0.5"
        rows.append(r)
        if busy_every and k % busy_every == 0:
            rows.append({"t_s": f"{k * 0.027 + 0.01:.3f}", "status": "busy", "state": "walk", "failed": "",
                         "phase_ms": "18.0", "room_ms": ""})
    return rows


def _status(rows, pack="nominal", **kw):
    rep = report.Report("t", "9", "t")
    pl.analyze(rows, pack, rep, **kw)
    return {i["item"]: i["status"] for i in rep.items}, rep


def test_analyze_gates():
    # right ankle under 6.0 V in 20 % of the readings, never under 4.5 V: FAIL at nominal
    st, _ = _status(_rows(lambda i, k: 5.8 if (i == 14 and k % 5 == 0) else 6.6))
    assert st["9.v4.5"] == "PASS" and st["9.time6"] == "FAIL"
    st, _ = _status(_rows(lambda i, k: 4.4 if (i == 24 and k == 7) else 7.0), "full")
    assert st["9.v4.5"] == "FAIL" and st["9.time6"] == "INFO"
    st, _ = _status(_rows(lambda i, k: 7.0))
    assert st["9.time6"] == "PASS" and st["9.wiring"] == "PASS"
    st, _ = _status(_rows(lambda i, k: 7.0, n=100))                   # too few readings to score
    assert st["9.time6"] == "INCOMPLETE"
    # TEST_PLAN 9 times every servo: a knee, the head roll or a hip over 10 % fails it, by ID
    for sid in (13, 33, 21):
        st, rep = _status(_rows(lambda i, k, sid=sid: 5.8 if (i == sid and k % 8 == 0) else 6.6))
        t6 = [x for x in rep.items if x["item"] == "9.time6"][0]
        assert st["9.time6"] == "FAIL" and str(sid) in t6["measured"]["over_10"], t6
    # 5 % under 6 V, but all of it in the last third of the sampled window: not recovering
    late = _rows(lambda i, k: 5.8 if (i == 24 and k % 20 == 0) else 6.6, phase=lambda k: 11.0 if k % 20 == 0 else 2.0,
                 busy_every=3)
    st, rep = _status(late)
    assert st["9.recovery"] == "WARN" and st["9.time6"] == "INCOMPLETE", rep.items
    # the same readings spread over the cycle (the dips early): recovering, and it passes
    early = _rows(lambda i, k: 5.8 if (i == 24 and k % 20 == 0) else 6.6,
                  phase=lambda k: 1.0 if k % 20 == 0 else 2.0 + (k % 10), busy_every=3)
    st, rep = _status(early)
    assert st["9.recovery"] == "PASS" and st["9.time6"] == "PASS", rep.items
    # the wiring check uses the sim corner of the wiring built (--feeds): 25 % passes the star corner only
    worse = _rows(lambda i, k: 5.8 if (i == 14 and k % 4 == 0) else 6.6)
    assert _status(worse, feeds="d23")[0]["9.wiring"] == "FAIL"
    assert _status(worse, feeds="none")[0]["9.wiring"] == "PASS"
    # as built, the head roll (high-side corner 33.4 %) and the knees (30.9 %) are compared too
    head = _rows(lambda i, k: 5.8 if (i == 33 and k % 2 == 0) else 6.6)
    st, rep = _status(head, feeds="d23")
    w = [x for x in rep.items if x["item"] == "9.wiring"][0]
    assert st["9.wiring"] == "FAIL" and "head_roll_pct" in w["desc"], w


def test_analyze_cli_on_a_saved_csv(tmp_path):
    """--analyze re-scores a saved walking log without hardware."""
    rows, _, _, exact = virtual_walk(seconds=30, period_s=0.0202)
    p = tmp_path / "log.csv"
    cols = pl.HEADER
    with open(p, "w") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(r.get(c, "") for c in cols) + "\n")
    rc = pl.main(["--analyze", str(p), "--pack", "nominal", "--out", str(tmp_path)])
    rep = last_report(tmp_path, "power_log")
    a = item(rep, "9.time6")
    assert rc == 1 and a["status"] == "FAIL" and set(a["measured"]["over_10"]) == {"24", "14"}, a
    assert abs(a["measured"]["left_ankle"]["time_pct"] - 100 * exact) <= 1.5, (a, exact)
    assert a["measured"]["left_knee"]["time_pct"] == 0.0


# ---------------------------------------------------------------- the real walk loop
def _walk(bus, duck_config, *extra):
    return ["--walk", "--onnx_model_path", ONNX, "--duck_config_path", duck_config, "--serial_port", bus.path,
            "--no-commands"] + list(extra)


def _exact_share(bus, sid, rep, dip_s):
    """Exact share of the logged walk with servo `sid` in its dip, from the fake's goal-write times."""
    t0 = rep["data"]["walk_t0_monotonic"]
    rows = pl.load_csv(rep["data"]["csv"])
    a, b = t0 + float(rows[0]["t_s"]), t0 + float(rows[-1]["t_s"])
    g = bus.servos[sid].goal_times
    dip = sum(max(0.0, min(t1 + dip_s, t2, b) - max(t1, a)) for t1, t2 in zip(g, g[1:]))
    return dip / (b - a)


@needs_walk
def test_walking_log_counts_a_write_locked_dip_in_time(make_bus, run, duck_config):
    """The real walk loop on the wire-timed simulated bus. Both ankles drop to 5.6 V for 4 ms after
    every goal write, about 20 % of the time. The old once-per-cycle log reads at the cycle start
    and never sees the dip; the timer log counts it in time, never reads past the next cycle (or
    says so), and fails the gate."""
    bus = make_bus(reg85=0, volts=6.6, wire_time=True)
    bus.log_on = False
    for i in (24, 14):
        bus.servos[i].goal_dip = (1.0, 0.004)
    r, out = run("power_log.py", *_walk(bus, duck_config, "--seconds", "12", "--pack", "nominal", "--no-guard",
                                        "--min-samples", "100"), timeout=240)
    rep = last_report(out, "power_log")
    exact = _exact_share(bus, 24, rep, 0.004)
    a = item(rep, "9.time6")
    assert 0.15 < exact < 0.25, exact
    assert a["status"] == "FAIL", (a, r.stdout[-3000:])
    for side in ("left_ankle", "right_ankle"):
        got = a["measured"][side]["time_pct"] / 100
        assert abs(got - exact) <= 0.07, (side, got, exact, item(rep, "9.profile"))
        assert a["measured"][side]["walk_pct"] / 100 <= exact + 0.04
    smp = rep["data"]["sampler"]
    assert smp["read"] + smp["busy"] + smp["own"] + smp["room"] == smp["slots"] and smp["read"] >= 100
    assert item(rep, "9.delay")["status"] in ("PASS", "WARN") and smp["overruns"] <= 0.05 * smp["read"], smp
    assert item(rep, "9.checksum")["status"] == "PASS" and item(rep, "9.recovery")["status"] == "PASS"
    assert item(rep, "9.speed")["status"] == "MANUAL"
    bus2 = make_bus(reg85=0, volts=6.6, wire_time=True)
    bus2.log_on = False
    for i in (24, 14):
        bus2.servos[i].goal_dip = (1.0, 0.004)
    r2, out2 = run("power_log.py", *_walk(bus2, duck_config, "--seconds", "8", "--pack", "nominal", "--no-guard",
                                          "--sampler", "cycle"), timeout=240)
    rep2 = last_report(out2, "power_log")
    a2 = item(rep2, "9.time6")
    assert a2["status"] == "INCOMPLETE", a2
    assert a2["measured"]["left_ankle"]["sampled_pct"] < 2.0, a2     # fooled: about 20 % in time


@needs_walk
def test_walking_log_on_sim_nominal_profile(make_bus, run, duck_config):
    """Sim pass only: servo voltages replay the star-wiring ngspice traces at a nominal pack
    (typical corner) while the real walk loop runs. The sim predicts the TEST_PLAN 9 ankle gate
    fails (21 % of the time under 6.0 V); no servo under 4.5 V; not worse than the star high-side
    corner (--feeds none: this trace has no second feeds)."""
    bus = make_bus(reg85=0, volts=7.2)
    bus.set_profile(VoltageProfile(str(DATA / "sim_star_nominal_typical.csv")), delay_s=6.0)
    r, out = run("power_log.py", *_walk(bus, duck_config, "--seconds", "6", "--pack", "nominal", "--no-guard",
                                        "--feeds", "none", "--min-samples", "50"), timeout=180)
    rep = last_report(out, "power_log")
    assert item(rep, "9.v4.5")["status"] == "PASS", r.stdout[-3000:]
    assert item(rep, "9.time6")["status"] == "FAIL"
    assert item(rep, "9.wiring")["status"] == "PASS"
    assert item(rep, "9.checksum")["status"] == "PASS"
    assert int(item(rep, "9.samples")["measured"].split(" / ")[0]) >= 60


@needs_walk
def test_walking_log_hard_stop_with_a_servo_that_keeps_torque_exits_10(make_bus, run, duck_config):
    """The guard runs on the timer readings (no extra reads). The pack falls under the walking
    floor, the guard hard stops, but ID 31 keeps torque: power_log must exit 10, not 6."""
    from test_battery_guard import keeps_torque
    bus = make_bus(reg85=0, volts=7.2)
    bus.set_profile(VoltageProfile(rows=[(0.0, {i: 7.2 for i in IDS}), (0.5, {i: 5.0 for i in IDS})]), delay_s=7.0)
    keeps_torque(bus.servos[31])
    r, out = run("power_log.py", *_walk(bus, duck_config, "--seconds", "40", "--pack", "nominal", "--period", "0.1"),
                 timeout=240)
    rep = last_report(out, "power_log")
    assert r.returncode == 10, r.stdout[-3000:]
    assert item(rep, "9.guard")["status"] == "FAIL"
    tq = item(rep, "9.torque_off")
    assert tq["status"] == "FAIL" and tq["measured"]["31"] == 1, tq
