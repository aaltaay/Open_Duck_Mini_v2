#!/usr/bin/env python3
"""Walking voltage log (TEST_PLAN.md section 9) and the idle bus inventory (section 8.1).

--walk     runs the stock walk (Runtime RLWalk, unmodified, odm_bench/walkhooks.py) and reads
           registers 62 to 70 of the 14 servos with ONE pypot SYNC READ (Present Voltage 62,
           Temperature 63, Status 65, Present Current 69-70) on its own timer: one read at a
           random time inside each --sample-period-ms slot (default 27 ms, odm_bench/vsampler.py),
           run only inside the walk loop's own end-of-cycle sleep and only if it ends before the
           next cycle, so a read never delays a control read or write. The ankles (IDs 24, 14),
           knees (23, 13) and head roll (33) are asked first. The D16 battery guard and the
           temperature guard run on the same readings (no extra bus traffic) unless --no-guard.
           --sampler cycle is the old log, kept for comparison only: one read per control cycle
           before the Runtime's reads. It delays every control write by one read and always reads
           at the same point of the 20 ms cycle, so it cannot score the 9.time6 gate.
--idle     no walking: the same read at --rate for --seconds, plus the inventory: all 14 IDs
           answer, firmware major.minor equal on all (UPSTREAM_ISSUES.md G3), register 85 = 0
           (G1), P/I/D as configure_all_motors.py writes them (32/0/0).
--analyze  re-run the gates on a saved CSV.

Counting in time (TEST_PLAN 9 "counted in time", odm_bench/vsampler.py time_count): the goal
write times (logged in memory, written to the CSV at the end) give each 1 ms bin of the time since
the last goal write its exact share of the walking time; the readings in the bin give its share
under 6.0 V; the time under 6.0 V is the sum over the bins. The bins the timer cannot read (the
Runtime's two reads, policy step and goal write at the end of each cycle) take the share of the
last bins read: the servo current peaks just after the goal write, so the voltage is recovering
there and the fill is high, not low; 9.recovery checks that on the last third of each cycle's
sampled window, for every servo. Also given: U = readings under / readings and L = readings under
/ slots (unsampled time counted as above 6.0 V, never above the true share).
Gates (TEST_PLAN 9): no servo under 4.5 V in any reading; at a nominal pack no servo under 6.0 V
for more than 10 % of the walking time counted that way (9.time6; the lowest as built are the
ankles 24 and 14, the knees 23 and 13 and the head roll 33, shown by name), with 9.recovery
holding and at least --min-samples readings of every servo; no checksum errors (pypot or
rustypot); no sampler read still running when the next control cycle was due (9.delay). Then the
comparison with the lab power sim for the wiring built (--feeds d23: D15 plus the second feeds
SP4 and SP5, sim/POWER_PATH_SIM.md "As built"; --feeds none: D15 star, sim/POWER_FIX.md option 1;
sim pass only): FAIL "stop and fix the wiring" if the worst ankle, knee or head roll is longer
under 6.0 V, or the worst ankle or any servo lower, than the high-side corner at a nominal pack.
Also reported: the share of the walk the timer could read (9.coverage), the time under 6.0 V
of every servo (9.under6), the median servo voltage and its lowest 5 s mean (9.median_v),
the control loop timing (9.loop) and the sampler's read times (9.sampler).
Exit codes: 0 pass, 1 a check failed, 2 incomplete, 3 walk loop crash (G10), 6 battery hard
stop, 7 thermal warn stop, 8 thermal stop, 10 torque off not confirmed after a stop (takes the
place of 3, 6, 7 or 8).
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import bus, joints, paths, report, sts3215, thermal, vsampler, walkhooks  # noqa: E402
import battery_guard as bg  # noqa: E402

BLOCK_ADDR, BLOCK_LEN = 62, 9          # 62..70 in one read; the Feetech SCServo SDK FeedBack reads 56..70 at once
FIRST = [joints.ANKLES["left_ankle"], joints.ANKLES["right_ankle"], joints.JOINTS["left_knee"],
         joints.JOINTS["right_knee"], joints.JOINTS["head_roll"]]   # the lowest servos as built answer first
ORDER = FIRST + [i for i in joints.IDS if i not in FIRST]
SIM_REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "data", "sim_power_fix_reference.json")
HEADER = (["t_s", "slot", "status", "state", "cycle", "phase_ms", "room_ms", "read_ms", "left_ms", "failed"] +
          [f"v_{i}" for i in joints.IDS] + [f"i_{i}" for i in joints.IDS] + [f"temp_{i}" for i in joints.IDS] +
          ["status_or"])
WALK_STATES = ("walk", "idle", "")     # rows that count as walking time (paused and stop phases do not)
NAMED = {"left_ankle": FIRST[0], "right_ankle": FIRST[1], "left_knee": FIRST[2], "right_knee": FIRST[3],
         "head_roll": FIRST[4]}                    # the lowest servos as built (sim/POWER_PATH_SIM.md)
# When each servo reads its register, in ms after the read starts (bus model at 1 Mbaud, 10 us per
# byte, packet sizes as in timing_budget.py; servo latch instant UNVERIFIED): a read started right
# after the goal write waits for the write's 50 bytes (sync write 8 + 14 x 3), then the request
# (8 + 14 bytes) goes out and the servos answer in ORDER, 6 + BLOCK_LEN bytes each.
WRITE_MS = (8 + 14 * 3) * 0.01
LATCH_MS = {sid: (8 + len(ORDER) + k * (6 + BLOCK_LEN)) * 0.01 for k, sid in enumerate(ORDER)}
GATE_FRAC = 0.10                       # TEST_PLAN 9: 10 % of the walking time
USB_GUESS_S = 0.002                    # first read-time guess per read before any read is timed (USB UNVERIFIED)


def decode(block):
    v = block[0] * sts3215.VOLT_LSB
    temp = block[1]
    status = block[3]
    cur = sts3215.current_a(sts3215.le(block, 7, 2))
    return v, cur, temp, status


def _num(x, fmt="{:.3f}"):
    return "" if x is None else fmt.format(x)


def _ms(s):
    return None if s is None else s * 1e3


class LogFile:
    """One CSV row per timer slot (read or skipped), per control cycle (--sampler cycle) or per
    idle-mode sample; keeps the latest readings for the guards."""

    def __init__(self, path):
        self.f = open(path, "w")
        self.f.write(",".join(HEADER) + "\n")
        self.path = path
        self.rows = 0
        self.latest = None          # {id: volts} of the latest reading, for the guards
        self.latest_temp = {}
        self.latest_seq = 0
        self.read_ms = []

    def write(self, t, slot, status, state="", cycle=None, phase_ms=None, room_ms=None, read_ms=None,
              left_ms=None, got=None, failed=()):
        vs, cs, ts, st = [], [], [], 0
        volts, temps = {}, {}
        for i in joints.IDS:
            if got and i in got:
                v, c, tmp, s = decode(got[i])
                volts[i], temps[i] = v, tmp
                vs.append(f"{v:.1f}"); cs.append(f"{c:.4f}"); ts.append(str(tmp)); st |= s
            else:
                vs.append(""); cs.append(""); ts.append("")
        if volts:
            self.latest, self.latest_temp = volts, temps
            self.latest_seq += 1
        if read_ms is not None:
            self.read_ms.append(read_ms)
        self.f.write(",".join([f"{t:.4f}", str(slot), status, state or "", "" if cycle is None else str(cycle),
                               _num(phase_ms), _num(room_ms), _num(read_ms), _num(left_ms),
                               " ".join(map(str, failed))] + vs + cs + ts + [str(st) if volts else ""]) + "\n")
        self.rows += 1
        if self.rows % 50 == 0:
            self.f.flush()

    def close(self):
        self.f.close()


class TimerLog:
    """read() and on_slot() of the vsampler.TimedRead that makes the walking log."""

    def __init__(self, io, lg, errors):
        self.io, self.lg, self.errors = io, lg, errors
        self.walk = None

    def read(self, end_by):
        return bus.sync_read_block(self.io, ORDER, BLOCK_ADDR, BLOCK_LEN, self.errors, end_by=end_by)

    def on_slot(self, rec):
        t0 = getattr(self.walk, "t0_monotonic", None) or 0.0
        if rec["status"] == "read":
            res = rec.get("result")
            got, failed = res if res else ({}, list(ORDER))
            self.lg.write(rec["t_read"] - t0, rec["slot"], "read", rec["state"], rec["cycle"], _ms(rec.get("phase")),
                          _ms(rec.get("room")), _ms(rec["read_s"]), _ms(rec["left_s"]), got, failed)
        else:
            self.lg.write(rec["due"] - t0, rec["slot"], rec["status"], rec["state"], rec["cycle"],
                          _ms(rec.get("phase")), _ms(rec.get("room")))


class CycleHook:
    """--sampler cycle (comparison only): one read per control cycle, before the Runtime's reads."""

    def __init__(self, lg, io, errors, decimate=1):
        self.lg, self.io, self.errors, self.decimate = lg, io, errors, max(1, decimate)
        self.n = 0

    def on_cycle(self, walk, t, paused):
        if paused:
            return
        self.n += 1
        if (self.n - 1) % self.decimate:
            return
        t0 = time.monotonic()
        got, failed = bus.sync_read_block(self.io, ORDER, BLOCK_ADDR, BLOCK_LEN, self.errors)
        rms = (time.monotonic() - t0) * 1e3
        lw = walk.last_write_t
        self.lg.write(t, walk.cycles, "cycle", walk.walk_state()["state"], walk.cycles,
                      None if lw is None else (t0 - lw) * 1e3, None, rms, None, got, failed)


class StopAfter:
    def __init__(self, max_seconds):
        self.max_seconds = max_seconds

    def on_cycle(self, walk, t, paused):
        if self.max_seconds and t >= self.max_seconds:
            raise walkhooks.WalkStop("timeout", f"{self.max_seconds} s logged")


class SharedReader:
    """Gives the guards the power logger's latest reading (no extra bus read): (volts, temps)."""

    def __init__(self, logger):
        self.logger = logger
        self.last_duration_s = None
        self.reads = self.failures = 0
        self._seen = 0

    def read(self):
        self.reads += 1
        if self.logger.latest_seq == self._seen or not self.logger.latest:
            self.failures += 1
            return None, {}
        self._seen = self.logger.latest_seq
        return dict(self.logger.latest), dict(self.logger.latest_temp)


# ---------------------------------------------------------------- analysis
def load_csv(path):
    with open(path) as fh:
        head = fh.readline().strip().split(",")
        rows = [dict(zip(head, ln.rstrip("\n").split(","))) for ln in fh if ln.strip()]
    return rows


def _f(x):
    return vsampler._f(x)


def _pct(x, nd=1):
    return None if x is None else round(100.0 * x, nd)


def load_sim_ref(path=SIM_REF):
    try:
        return json.load(open(path))["cases"]
    except (OSError, ValueError, KeyError):
        return None


def _median_record(reads):
    """Per reading the median of the servo voltages (at least 7 servos), its mean over the sampled
    time and its lowest 5 s mean (TEST_PLAN 9 record line)."""
    pts = []
    for r in reads:
        vs = [_f(r.get(f"v_{i}")) for i in joints.IDS]
        vs = [v for v in vs if v is not None]
        t = _f(r.get("t_s"))
        if len(vs) >= 7 and t is not None:
            pts.append((t, statistics.median(vs)))
    if not pts:
        return None
    pts.sort()
    mean = sum(m for _, m in pts) / len(pts)
    lows, j, acc = [], 0, 0.0
    for k, (t, m) in enumerate(pts):
        acc += m
        while pts[j][0] < t - 5.0:
            acc -= pts[j][1]
            j += 1
        if t - pts[0][0] >= 5.0:
            lows.append(acc / (k - j + 1))
    return dict(mean=round(mean, 3), lowest_5s_mean=round(min(lows), 3) if lows else None, readings=len(pts))


def analyze(rows, pack, rep, feeds="d23", min_samples=300, sim_ref_path=SIM_REF, rate_hz=None):
    statuses = {r.get("status", "read") for r in rows}
    phase_locked = "cycle" in statuses
    sel = [r for r in rows if r.get("state", "") in WALK_STATES and r.get("status") != "write"]
    reads = [r for r in sel if r.get("status", "read") in ("read", "cycle")]
    rep.add("9.samples", "readings while walking / timer slots while walking", "INFO" if reads else "INCOMPLETE",
            f"{len(reads)} / {len(sel)}")
    if not reads:
        return
    cnt = vsampler.time_count(rows, joints.IDS, 6.0, states=WALK_STATES, latch_ms=LATCH_MS, after_ms=WRITE_MS)
    allv = [(v, i) for r in reads for i in joints.IDS for v in [_f(r.get(f"v_{i}"))] if v is not None]
    vmin, vmin_id = min(allv) if allv else (None, None)
    rep.gate("9.v4.5", "no servo under 4.5 V in any reading", vmin is not None and vmin >= 4.5,
             f"{vmin} V (ID {vmin_id})", ">= 4.5 V", "TEST_PLAN 9")
    by_status = {s: sum(1 for r in sel if r.get("status", "read") == s) for s in ("read", "busy", "own", "room", "cycle")}
    cov = by_status["read"] / len(sel) if sel and not phase_locked else None
    if phase_locked:
        rep.add("9.coverage", "one read per control cycle (--sampler cycle): a phase sample, not a time sample",
                "WARN", by_status["cycle"], None, "software/SOFTWARE.md section 6")
    else:
        rep.add("9.coverage", "share of the walking time the timer read (the rest: the Runtime's own bus and "
                "policy time, or too close to the next cycle)", "INFO",
                dict(share=round(cov, 3), **{k: v for k, v in by_status.items() if k != "cycle"}), None,
                "odm_bench/vsampler.py")
    rep.add("9.under6", "time under 6.0 V per servo, % of the walking time counted in time (L: unsampled time "
            "counted as above 6.0 V; U: % of the readings)", "INFO",
            {str(i): f"{_pct(d['time_frac'])} (L {_pct(d['walk_frac'])}, U {_pct(d['sampled_frac'])})"
             for i, d in cnt.items()}, None, "vsampler.time_count")
    full_cover = cov is not None and cov >= 0.999
    rec = {i: (True if full_cover else vsampler.recovery_ok(d)) for i, d in cnt.items() if d["sampled"]}
    meas = {name: dict(id=i, time_pct=_pct(cnt[i]["time_frac"]), walk_pct=_pct(cnt[i]["walk_frac"]),
                       sampled_pct=_pct(cnt[i]["sampled_frac"]), readings=cnt[i]["sampled"], min_v=cnt[i]["v_min"],
                       unread_ms_bins=len(cnt[i]["filled_bins"]), fill_pct=_pct(cnt[i]["fill_frac"]))
            for name, i in NAMED.items()}
    over = {str(i): _pct(d["time_frac"]) for i, d in cnt.items() if d["time_frac"] is not None and d["time_frac"] > GATE_FRAC}
    over_sure = {k: v for k, v in over.items() if cnt[int(k)]["sampled"] >= min_samples}
    if not phase_locked and not full_cover:
        bad = [i for i, v in rec.items() if v is False]
        unknown = [i for i, v in rec.items() if v is None]
        shown = list(NAMED.values()) + [i for i in bad if i not in NAMED.values()]
        rep.add("9.recovery", "readings in the last third of each cycle's sampled window are not more often under "
                "6.0 V than all readings, for every servo (else the unread end of the cycle may dip and its fill is "
                "not high)", "WARN" if bad else ("INCOMPLETE" if unknown else "PASS"),
                {str(i): dict(late_pct=_pct(cnt[i]["late_frac"]), late_readings=cnt[i]["late"],
                              all_pct=_pct(cnt[i]["sampled_frac"])) for i in shown if i in cnt},
                "late <= all + 2 standard errors", "vsampler.recovery_ok")
    if not phase_locked:
        rep.add("9.profile", "per 1 ms after the goal write (last bin: 20 ms or more): [% of the walking time, "
                "readings, % of them under 6.0 V], ankles, knees and head roll", "INFO",
                {name: {f"{b:g}": [_pct(w), nr, _pct(u, 0)] for b, w, nr, u in cnt[i]["bins"] if w or nr}
                 for name, i in NAMED.items()})
    worst_t = max((d["time_frac"] for d in cnt.values() if d["time_frac"] is not None), default=None)
    if pack == "nominal":
        why = ""
        few = [i for i in joints.IDS if cnt[i]["sampled"] < min_samples]
        if phase_locked:
            status, why = "INCOMPLETE", ": read once per control cycle at one point of the cycle, not in time " \
                                        "(use --sampler timer)"
        elif over_sure:
            status, why = "FAIL", f": over 10 % {over_sure}"
        elif few:
            status, why = "INCOMPLETE", f": fewer than {min_samples} readings of servo(s) {few}"
        elif not all(rec.get(i) for i in joints.IDS):
            status, why = "INCOMPLETE", ": the voltage is not recovering at the end of the sampled window (9.recovery)"
        else:
            status = "PASS"
        rep.add("9.time6", "no servo under 6.0 V for more than 10% of the walking time, counted in time (nominal "
                "pack; ankles, knees and head roll shown)" + why, status, dict(meas, over_10=over or "none"),
                "time_pct <= 10 % on every servo", "TEST_PLAN 9")
    else:
        rep.add("9.time6", f"time under 6.0 V ({pack} pack, the gate applies at nominal)", "INFO",
                dict(meas, over_10=over or "none"))
    failed_rows = sum(1 for r in reads if r.get("failed"))
    rep.add("9.missing", "readings where at least one servo did not answer", "PASS" if not failed_rows else "WARN",
            failed_rows, "0")
    if phase_locked or "busy" not in statuses and "room" not in statuses and "own" not in statuses:
        ts = [_f(r["t_s"]) for r in reads if _f(r.get("t_s")) is not None]
        if rate_hz and len(ts) > 1 and ts[-1] > ts[0]:
            hz = (len(ts) - 1) / (ts[-1] - ts[0])
            rep.add("9.rate", "achieved log rate", "PASS" if hz >= 0.9 * rate_hz else "WARN", f"{hz:.1f} Hz",
                    f">= {0.9 * rate_hz:.0f} Hz ({rate_hz:g} Hz asked)")
    cur = [sum(abs(_f(r.get(f"i_{i}")) or 0.0) for i in joints.IDS) for r in reads]
    if cur:
        rep.add("9.current", "sum of the 14 servo currents over the sampled time: mean / max (sign of register 69 "
                "UNVERIFIED, magnitudes used)", "INFO", f"{sum(cur) / len(cur):.2f} / {max(cur):.2f} A",
                None, "sim/CURRENT_BUDGET.md bus mean 3.19 A (sim pass only)")
    med = _median_record(reads)
    if med:
        rep.add("9.median_v", "median servo voltage: mean over the sampled time, lowest 5 s mean (record; a pass "
                "line once the 3S pack is decided)", "INFO", med, ">= 7.0 V (record)", "TEST_PLAN 9")
    sim = load_sim_ref(sim_ref_path)
    if sim and pack in ("nominal", "full"):
        ref = (sim.get(pack) or {}).get(feeds)
        got = _group_values(cnt, vmin)
        if ref:
            rep.add("9.sim", f"vs the sim typical corner ({pack} pack, feeds {feeds}, sim pass only): measured / sim",
                    "INFO", {k: f"{got.get(k)} / {v}" for k, v in ref["typical"].items() if v is not None}, None,
                    "tests/data/sim_power_fix_reference.json")
        else:
            rep.add("9.sim", f"no sim number for the {pack} pack with feeds {feeds}", "INFO")
        high = (ref or {}).get("high_side") if pack == "nominal" else None
        if high:
            if phase_locked:
                rep.add("9.wiring", "not worse than the high-side sim corner: needs a time count (--sampler timer)",
                        "INCOMPLETE")
            else:
                worse = _worse_than(got, high)
                rep.gate("9.wiring", "not worse than the high-side sim corner (else stop and fix the wiring)"
                         + (f": worse in {sorted(worse)}" if worse else ""), not worse,
                         {k: got.get(k) for k in high}, {k: v for k, v in high.items() if v is not None},
                         f"TEST_PLAN 9, sim/POWER_PATH_SIM.md feeds {feeds}, sim pass only")


def _group_values(cnt, vmin):
    """Worst of each group, in the reference file's terms (V and % of the walking time)."""
    def worst(ids, key, fn):
        vals = [cnt[i][key] for i in ids if cnt[i][key] is not None]
        return fn(vals) if vals else None
    ank, knees = list(joints.ANKLES.values()), [NAMED["left_knee"], NAMED["right_knee"]]
    out = dict(ankle_min=worst(ank, "v_min", min), lowest_v=vmin)
    for k, ids in (("ankle_pct", ank), ("knee_pct", knees), ("head_roll_pct", [NAMED["head_roll"]])):
        w = worst(ids, "time_frac", max)
        out[k] = _pct(w)
    return out


def _worse_than(got, ref):
    """Names of the quantities where the measured value is worse than the reference."""
    bad = []
    for k, v in ref.items():
        g = got.get(k)
        if v is None or g is None:
            continue
        if (k.endswith("_min") or k == "lowest_v") and g < v:
            bad.append(k)
        elif k.endswith("_pct") and g > v:
            bad.append(k)
    return bad


def checksum_gate(rep, errors_snapshot):
    cks = sum(v for k, v in errors_snapshot.items() if "checksum" in k)
    rep.gate("9.checksum", "no bus checksum errors (pypot and rustypot)", cks == 0, cks, "0", "TEST_PLAN 9")
    other = {k: v for k, v in errors_snapshot.items() if "checksum" not in k}
    rep.add("9.errors", "other bus errors", "PASS" if not other else "WARN", other or "none")


def sampler_items(rep, task):
    st = task.stats()
    rep.add("9.sampler", "timer reads: slots, read / skipped (busy: the Runtime's own time; own: during the "
            "previous read; room: too close to the next cycle), read times", "INFO", st, None,
            "odm_bench/vsampler.py")
    rep.add("9.delay", "no timer read still running when the next control cycle was due (a read never delays a "
            "control write; WARN, not FAIL: timing evidence, not a robot fault)",
            "PASS" if st["overruns"] == 0 else "WARN", f"{st['overruns']} reads, max {st['overrun_max_ms']} ms late",
            "0", "software/SOFTWARE.md section 6")
    return st


# ---------------------------------------------------------------- idle inventory (8.1)
def inventory(io, rep, errors):
    found, info = [], {}
    for i in joints.IDS:
        if bus.ping(io, i):
            found.append(i)
    missing = [i for i in joints.IDS if i not in found]
    rep.gate("8.1.ids", "all 14 servos answer with the Runtime IDs", not missing,
             f"{len(found)} of 14" + (f", missing {missing}" if missing else ""), "IDs 10-14, 20-24, 30-33",
             "rustypot_position_hwi.py lines 14 to 31")
    for i in found:
        try:
            info[i] = dict(fw=tuple(bus.read_block(io, i, 0, 2)), r85=bus.read_reg(io, i, "maximum_acceleration"),
                           r41=bus.read_reg(io, i, "acceleration"), p=bus.read_reg(io, i, "p_coefficient"),
                           d=bus.read_reg(io, i, "d_coefficient"), i=bus.read_reg(io, i, "i_coefficient"),
                           vmax=bus.read_reg(io, i, "max_voltage_limit"))
        except Exception as e:  # noqa: BLE001
            errors.add("pypot", "inventory_read", i, repr(e))
    if info:
        fws = {i: f"{d['fw'][0]}.{d['fw'][1]}" for i, d in info.items()}
        rep.gate("8.1.fw", "same firmware on every servo", len(set(fws.values())) == 1,
                 sorted(set(fws.values())), "one version", "UPSTREAM_ISSUES.md G3")
        bad85 = [i for i, d in info.items() if d["r85"] != 0]
        rep.gate("8.1.r85", "register 85 (max acceleration) = 0 on every servo", not bad85,
                 bad85 or "all 0", "0", "UPSTREAM_ISSUES.md G1")
        badpid = [i for i, d in info.items() if (d["p"], d["i"], d["d"]) != (32, 0, 0) or d["r41"] != 0]
        rep.add("8.1.pid", "P/I/D = 32/0/0 and register 41 = 0 (configure_all_motors.py values)",
                "PASS" if not badpid else "WARN", badpid or "all match", "32/0/0, 41 = 0",
                "configure_all_motors.py lines 27 to 37; the walk then writes its own P at start")
        rep.data["inventory"] = {str(k): v for k, v in info.items()}
    return found


def run_idle(a):
    out = paths.out_dir(a.out, "power_log")
    rep = report.Report("power_log", "8.1, 9", "Bus inventory and idle voltage/current log")
    errors = bus.BusErrors()
    io = bus.open_pypot(a.port, sync_read=True, errors=errors)
    found = inventory(io, rep, errors)
    path = out / f"power_idle_{paths.stamp()}.csv"
    lg = LogFile(path)
    t0 = time.monotonic()
    k = 0
    while found and time.monotonic() - t0 < a.seconds:
        ts = time.monotonic()
        got, failed = bus.sync_read_block(io, ORDER, BLOCK_ADDR, BLOCK_LEN, errors)
        lg.write(ts - t0, k, "read", "idle", None, read_ms=(time.monotonic() - ts) * 1e3, got=got, failed=failed)
        k += 1
        time.sleep(max(0.0, t0 + k / a.rate - time.monotonic()))
    lg.close()
    rows = load_csv(path)
    analyze(rows, "idle", rep, feeds=a.feeds, min_samples=a.min_samples, rate_hz=a.rate)
    checksum_gate(rep, errors.snapshot())
    rep.data["csv"] = str(path)
    return rep.finish(out)


def first_cost_s(n=len(ORDER), length=BLOCK_LEN):
    """Read-time guess before any read is timed: wire time at 1 Mbaud (10 us per byte, SYNC READ
    request 8 + n bytes, replies n x (6 + length), timing_budget.py) plus USB_GUESS_S."""
    return (8 + n + n * (6 + length)) * 10e-6 + USB_GUESS_S


def run_walk(a):
    out = paths.out_dir(a.out, "power_log")
    rep = report.Report("power_log", "9", f"Walking voltage log ({a.pack} pack, {a.sampler} sampler)")
    if a.pack_ocv:
        rep.add("9.pack", "pack open-circuit voltage before the walk (meter)", "INFO", f"{a.pack_ocv} V",
                ">= 8.3 V full, about 7.4 V nominal", "TEST_PLAN 9")
    errors = bus.BusErrors()
    io = bus.open_pypot(a.serial_port, sync_read=True, errors=errors)        # before rustypot
    path = out / f"power_walk_{a.pack}_{paths.stamp()}.csv"
    lg = LogFile(path)
    hooks = [StopAfter(a.seconds)]
    tasks, tl = [], None
    if a.sampler == "timer":
        tl = TimerLog(io, lg, errors)
        tasks.append(vsampler.TimedRead("voltage", tl.read, period_s=a.sample_period_ms / 1e3, seed=a.sample_seed,
                                        margin_s=a.sample_margin_ms / 1e3, first_cost_s=first_cost_s(),
                                        on_slot=tl.on_slot))
    else:
        hooks.append(CycleHook(lg, io, errors, a.decimate))
    guard = tg = None
    if not a.no_guard:
        cfg = bg.config_from_args(a)
        guard = bg.BatteryGuard(cfg)
        limits, fallback = thermal.read_limits(io, joints.IDS, bus, errors)
        tg = thermal.ThermalGuard(limits)
        rep.add("T.limits", "Max Temperature Limit (register 13) per servo", "INFO",
                {str(k): v for k, v in limits.items()}, None, "thermal guard runs on the logged temperatures")
        from walk_with_guard import GuardHook  # noqa: E402
        st_ = paths.stamp()
        glog = open(out / f"power_walk_guard_{st_}.csv", "w")
        glog.write("t_s,cycle,median_v,guard_state,stop_phase,paused,read_ms,event," +
                   ",".join(f"v_{i}" for i in joints.IDS) + "\n")
        tlog = open(out / f"power_walk_thermal_{st_}.csv", "w")
        tlog.write("t_s,hottest_id,joint,temp_c,limit_c,warn_c,stop_c,margin_to_warn_c\n")
        hooks.append(GuardHook(guard, SharedReader(lg), glog, thermal_guard=tg, thermal_log=tlog, quiet=True))
    walk, rt = walkhooks.make_walk(a, hooks, errors, idle_tasks=tasks)
    if tl is not None:
        tl.walk = walk
    code = 0
    try:
        walk.run()
    except walkhooks.WalkStop as e:
        rep.add("9.end", f"logging ended: {e.reason}", "INFO")
        if e.kind == "hard_stop":
            rep.add("9.guard", "battery guard hard stop during the log", "FAIL", walk.hard_stop(io))
            code = 6
        elif e.kind in ("sink_off", "thermal_stop"):
            rep.add("9.thermal", f"temperature guard {e.kind} during the log", "FAIL",
                    walk.hard_stop(io, low_gain_s=2.0 if e.kind == "sink_off" else 0.5))
            code = 7 if e.kind == "sink_off" else 8
    except BaseException as e:  # noqa: BLE001 - rustypot panic
        if isinstance(e, KeyboardInterrupt):
            raise
        rep.add("9.crash", f"walk loop crashed: {type(e).__name__}: {e}", "FAIL", walk.hard_stop(io, 0.5),
                None, "UPSTREAM_ISSUES.md G10")
        code = 3
    if walk.torque_check is not None and not walkhooks.report_torque_check(rep, "9.torque_off", walk.torque_check):
        code = walkhooks.EXIT_TORQUE_ON          # 10: a hard stop could not confirm torque off
    t0 = walk.t0_monotonic or 0.0
    for t, state in walk.write_log or ():        # goal write times: the exact time per phase bin
        lg.write(t - t0, "", "write", state)
    lg.close()
    rows = load_csv(path)
    analyze(rows, a.pack, rep, feeds=a.feeds, min_samples=a.min_samples,
            rate_hz=a.control_freq / a.decimate if a.sampler == "cycle" else None)
    checksum_gate(rep, errors.snapshot())
    st = walk.loop_stats()
    rep.add("9.loop", "control loop while logging", "PASS" if st.get("over_budget_frac", 1) <= 0.05 else "WARN",
            st, "<= 5% of cycles over 21 ms", "lab advisory limit")
    smp = sampler_items(rep, tasks[0]) if tasks else None
    if lg.read_ms:
        rs = sorted(lg.read_ms)
        rep.add("9.read_ms", "log read time (mean / max ms)", "INFO",
                f"{sum(rs) / len(rs):.2f} / {rs[-1]:.2f}")
    if guard:
        rep.add("9.guard_events", "battery guard events", "INFO", guard.events or "none")
        rep.add("9.thermal_events", "temperature guard events", "INFO", tg.events or "none")
        rep.add("9.temp_max", "hottest reading per servo", "INFO", {str(k): v for k, v in sorted(tg.max_seen.items())})
        if walk.stop_log:
            rep.add("9.stop", "walk stop sequence", "INFO", walk.stop_log)
    rep.add("9.speed", "forward distance in 20 s, tape measure, at full and at nominal charge (a drop of more "
            "than 15 % means the servo voltage limits the walk)", "MANUAL", None, None, "TEST_PLAN 9")
    rep.data.update(csv=str(path), runtime=dict(dir=str(rt), commit=paths.runtime_commit(rt)), loop=st,
                    sampler=smp, sampler_mode=a.sampler, feeds=a.feeds, walk_t0_monotonic=walk.t0_monotonic,
                    read_order=ORDER)
    rc = rep.finish(out)
    return code or rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--walk", action="store_true")
    m.add_argument("--idle", action="store_true")
    m.add_argument("--analyze", metavar="CSV")
    ap.add_argument("--port", default="/dev/ttyACM0", help="idle mode port (walk mode: --serial_port)")
    ap.add_argument("--seconds", type=float, default=60.0, help="how long to log (TEST_PLAN 9: 60 s)")
    ap.add_argument("--rate", type=float, default=50.0, help="idle mode sample rate")
    ap.add_argument("--pack", choices=("full", "nominal", "idle"), default="nominal")
    ap.add_argument("--pack-ocv", type=float, help="pack voltage measured with the meter before the walk")
    ap.add_argument("--feeds", choices=("d23", "none"), default="d23",
                    help="wiring for the sim comparison: d23 = second feeds SP4 and SP5 fitted, none = D15 star")
    ap.add_argument("--sampler", choices=("timer", "cycle"), default="timer",
                    help="timer (default): own timer, idle time only; cycle: the old per-cycle read (comparison)")
    ap.add_argument("--sample-period-ms", type=float, default=27.0, help="timer slot (one read at a random time in each)")
    ap.add_argument("--sample-seed", type=int, default=27, help="random seed of the read times (written in the report)")
    ap.add_argument("--sample-margin-ms", type=float, default=1.0,
                    help="a read starts only if its longest recent time plus this ends before the next cycle")
    ap.add_argument("--min-samples", type=int, default=300, help="readings of every servo needed to score 9.time6")
    ap.add_argument("--decimate", type=int, default=1, help="--sampler cycle only: log every Nth cycle")
    ap.add_argument("--no-guard", action="store_true", help="do not run the D16 guard on the readings")
    ap.add_argument("--out", help="log folder (default ODM_BENCH_OUT or ~/odm_bench_logs)")
    walkhooks.common_walk_args(ap, onnx_required=False)
    bg.add_guard_args(ap)
    a = ap.parse_args(argv)
    if a.walk:
        if not a.onnx_model_path:
            ap.error("--walk needs --onnx_model_path")
        return run_walk(a)
    if a.idle:
        return run_idle(a)
    rep = report.Report("power_log", "9", f"Walking voltage log analysis of {os.path.basename(a.analyze)}")
    analyze(load_csv(a.analyze), a.pack, rep, feeds=a.feeds, min_samples=a.min_samples)
    return rep.finish(paths.out_dir(a.out, "power_log") if a.out else None)


if __name__ == "__main__":
    sys.exit(main())
