#!/usr/bin/env python3
"""Walking voltage log at 50 Hz (TEST_PLAN.md section 9) and the idle bus inventory (section 8.1).

--walk     runs the stock walk (Runtime RLWalk, unmodified, odm_bench/walkhooks.py) and in every
           control cycle reads registers 62 to 70 of the 14 servos with ONE pypot SYNC READ
           (Present Voltage 62, Temperature 63, Status 65, Present Current 69-70), before the
           Runtime's own reads of that cycle. The D16 battery guard runs on the same readings
           (no extra bus traffic) unless --no-guard.
--idle     no walking: the same read at --rate for --seconds, plus the inventory: all 14 IDs
           answer, firmware major.minor equal on all (UPSTREAM_ISSUES.md G3), register 85 = 0
           (G1), P/I/D as configure_all_motors.py writes them (32/0/0).
--analyze  re-run the gates on a saved CSV.

Gates (TEST_PLAN 9): no servo under 4.5 V at any time; at a nominal pack no ankle (IDs 24, 14)
under 6.0 V for more than 10% of the samples; no checksum errors (pypot or rustypot). Then the
comparison with the lab power sim (tests/data/sim_profiles_summary.json, star wiring = D15,
sim pass only): FAIL "stop and fix the wiring" if the worst ankle is lower, or longer under
6.0 V, than the high-side corner at the same pack state.
Also reported: achieved log rate and loop over-budget fraction (the read costs time inside the
20 ms cycle; SOFTWARE.md section 6 has the bus budget). If the loop runs late, use --decimate 2.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import bus, joints, paths, report, sts3215, thermal, walkhooks  # noqa: E402
import battery_guard as bg  # noqa: E402

BLOCK_ADDR, BLOCK_LEN = 62, 9          # 62..70 in one read; the Feetech SCServo SDK FeedBack reads 56..70 at once
SIM_SUMMARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "data", "sim_profiles_summary.json")
HEADER = (["t_s", "cycle", "loop_ms", "read_ms", "failed"] + [f"v_{i}" for i in joints.IDS] +
          [f"i_{i}" for i in joints.IDS] + [f"temp_{i}" for i in joints.IDS] + ["status_or"])


def decode(block):
    v = block[0] * sts3215.VOLT_LSB
    temp = block[1]
    status = block[3]
    cur = sts3215.current_a(sts3215.le(block, 7, 2))
    return v, cur, temp, status


class PowerLogger:
    def __init__(self, io, path, errors, decimate=1):
        self.io, self.errors, self.decimate = io, errors, max(1, decimate)
        self.f = open(path, "w")
        self.f.write(",".join(HEADER) + "\n")
        self.path = path
        self.rows = 0
        self.n = 0
        self.last_t = None
        self.latest = None          # {id: volts} of the latest sample, for the guards
        self.latest_temp = {}
        self.latest_cycle = -1
        self.read_ms = []

    def sample(self, t, cycle):
        self.n += 1
        if (self.n - 1) % self.decimate:
            return
        t0 = time.perf_counter()
        got, failed = bus.sync_read_block(self.io, joints.IDS, BLOCK_ADDR, BLOCK_LEN, self.errors)
        rms = (time.perf_counter() - t0) * 1e3
        self.read_ms.append(rms)
        loop_ms = "" if self.last_t is None else f"{(t - self.last_t) * 1e3:.2f}"
        self.last_t = t
        vs, cs, ts, st = [], [], [], 0
        volts, temps = {}, {}
        for i in joints.IDS:
            if i in got:
                v, c, tmp, s = decode(got[i])
                volts[i], temps[i] = v, tmp
                vs.append(f"{v:.1f}"); cs.append(f"{c:.4f}"); ts.append(str(tmp)); st |= s
            else:
                vs.append(""); cs.append(""); ts.append("")
        self.latest, self.latest_temp, self.latest_cycle = volts, temps, cycle
        self.f.write(",".join([f"{t:.4f}", str(cycle), loop_ms, f"{rms:.2f}", " ".join(map(str, failed))] +
                              vs + cs + ts + [str(st)]) + "\n")
        self.rows += 1
        if self.rows % 50 == 0:
            self.f.flush()

    def close(self):
        self.f.close()


class PowerHook:
    def __init__(self, logger, max_seconds):
        self.logger, self.max_seconds = logger, max_seconds

    def on_cycle(self, walk, t, paused):
        if self.max_seconds and t >= self.max_seconds:
            raise walkhooks.WalkStop("timeout", f"{self.max_seconds} s logged")
        if not paused:
            self.logger.sample(t, walk.cycles)


class SharedReader:
    """Gives the guards the power logger's latest reading (no extra bus read): (volts, temps)."""

    def __init__(self, logger):
        self.logger = logger
        self.last_duration_s = None
        self.reads = self.failures = 0
        self._seen = -1

    def read(self):
        self.reads += 1
        if self.logger.latest_cycle == self._seen or not self.logger.latest:
            self.failures += 1
            return None, {}
        self._seen = self.logger.latest_cycle
        return dict(self.logger.latest), dict(self.logger.latest_temp)


# ---------------------------------------------------------------- analysis
def load_csv(path):
    with open(path) as fh:
        head = fh.readline().strip().split(",")
        rows = [dict(zip(head, ln.rstrip("\n").split(","))) for ln in fh if ln.strip()]
    return rows


def _f(x):
    return float(x) if x not in ("", None) else None


def analyze(rows, pack, rep, sim_summary_path=SIM_SUMMARY, rate_hz=50.0):
    n = len(rows)
    rep.add("9.samples", "samples logged", "INFO" if n else "INCOMPLETE", n)
    if not n:
        return
    allv = [(_f(r[f"v_{i}"]), i) for r in rows for i in joints.IDS if _f(r[f"v_{i}"]) is not None]
    vmin, vmin_id = min(allv) if allv else (None, None)
    rep.gate("9.v4.5", "no servo under 4.5 V at any time", vmin is not None and vmin >= 4.5,
             f"{vmin} V (ID {vmin_id})", ">= 4.5 V", "TEST_PLAN 9")
    frac = {}
    amin = {}
    for name, i in joints.ANKLES.items():
        col = [_f(r[f"v_{i}"]) for r in rows if _f(r[f"v_{i}"]) is not None]
        frac[name] = sum(v < 6.0 for v in col) / len(col) if col else None
        amin[name] = min(col) if col else None
    worst = max((v for v in frac.values() if v is not None), default=None)
    if pack == "nominal":
        rep.gate("9.ankle", "no ankle under 6.0 V for more than 10% of the walk (nominal pack)",
                 worst is not None and worst <= 0.10, {k: round(v, 3) for k, v in frac.items() if v is not None},
                 "<= 0.10", "TEST_PLAN 9")
    else:
        rep.add("9.ankle", f"ankle time under 6.0 V ({pack} pack, gate applies at nominal)", "INFO",
                {k: round(v, 3) for k, v in frac.items() if v is not None})
    failed_rows = sum(1 for r in rows if r.get("failed"))
    rep.add("9.missing", "samples where at least one servo did not answer", "PASS" if not failed_rows else "WARN",
            failed_rows, "0")
    ts = [_f(r["t_s"]) for r in rows]
    if n > 1 and ts[-1] > ts[0]:
        hz = (n - 1) / (ts[-1] - ts[0])
        rep.add("9.rate", "achieved log rate", "PASS" if hz >= 0.9 * rate_hz else "WARN", f"{hz:.1f} Hz",
                f">= {0.9 * rate_hz:.0f} Hz (50 Hz asked)", "TEST_PLAN 9")
    cur = [sum(_f(r[f"i_{i}"]) or 0.0 for i in joints.IDS) for r in rows]
    if cur:
        rep.add("9.current", "sum of the 14 servo currents: mean / max (sign of register 69 UNVERIFIED, magnitudes used)",
                "INFO", f"{sum(abs(c) for c in cur) / len(cur):.2f} / {max(abs(c) for c in cur):.2f} A",
                None, "sim/CURRENT_BUDGET.md bus mean 3.19 A (sim pass only)")
    # comparison with the sim (star wiring)
    try:
        sim = json.load(open(sim_summary_path))["cases"]
    except (OSError, ValueError, KeyError):
        sim = None
    if sim and pack in ("nominal", "full"):
        typ = sim.get(f"{pack}_typical")
        high = sim.get(f"{pack}_highside") if pack == "nominal" else None
        ank_min = min(v for v in amin.values() if v is not None)
        rep.add("9.sim", "worst ankle min vs sim typical corner (star wiring, sim pass only)", "INFO",
                f"{ank_min} V vs {typ['ankle_min']} V", None, "tests/data/sim_profiles_summary.json")
        if high:
            sim_frac = max(high["left_ankle_frac_below_6"], high["right_ankle_frac_below_6"])
            ok = ank_min >= high["ankle_min"] and (worst or 0) <= sim_frac
            rep.gate("9.wiring", "not worse than the high-side sim corner (else stop and fix the wiring)", ok,
                     f"min {ank_min} V, under 6 V {worst:.2f}", f"min >= {high['ankle_min']} V, under 6 V <= {sim_frac}",
                     "TEST_PLAN 9, sim pass only")


def checksum_gate(rep, errors_snapshot):
    cks = sum(v for k, v in errors_snapshot.items() if "checksum" in k)
    rep.gate("9.checksum", "no bus checksum errors (pypot and rustypot)", cks == 0, cks, "0", "TEST_PLAN 9")
    other = {k: v for k, v in errors_snapshot.items() if "checksum" not in k}
    rep.add("9.errors", "other bus errors", "PASS" if not other else "WARN", other or "none")


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
    lg = PowerLogger(io, path, errors)
    t0 = time.monotonic()
    k = 0
    while found and time.monotonic() - t0 < a.seconds:
        lg.sample(time.monotonic() - t0, k)
        k += 1
        time.sleep(max(0.0, t0 + k / a.rate - time.monotonic()))
    lg.close()
    rows = load_csv(path)
    analyze(rows, "idle", rep, rate_hz=a.rate)
    checksum_gate(rep, errors.snapshot())
    rep.data["csv"] = str(path)
    return rep.finish(out)


def run_walk(a):
    out = paths.out_dir(a.out, "power_log")
    rep = report.Report("power_log", "9", f"Walking voltage log ({a.pack} pack)")
    if a.pack_ocv:
        rep.add("9.pack", "pack open-circuit voltage before the walk (meter)", "INFO", f"{a.pack_ocv} V",
                ">= 8.3 V full, about 7.4 V nominal", "TEST_PLAN 9")
    errors = bus.BusErrors()
    io = bus.open_pypot(a.serial_port, sync_read=True, errors=errors)        # before rustypot
    path = out / f"power_walk_{a.pack}_{paths.stamp()}.csv"
    lg = PowerLogger(io, path, errors, a.decimate)
    hooks = [PowerHook(lg, a.seconds)]
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
    walk, rt = walkhooks.make_walk(a, hooks, errors)
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
    lg.close()
    rows = load_csv(path)
    analyze(rows, a.pack, rep, rate_hz=a.control_freq / a.decimate)
    checksum_gate(rep, errors.snapshot())
    st = walk.loop_stats()
    rep.add("9.loop", "control loop with logging", "PASS" if st.get("over_budget_frac", 1) <= 0.05 else "WARN",
            st, "<= 5% of cycles over 21 ms", "lab advisory limit")
    if lg.read_ms:
        rep.add("9.read_ms", "log read time per cycle (mean / max ms)", "INFO",
                f"{sum(lg.read_ms) / len(lg.read_ms):.2f} / {max(lg.read_ms):.2f}")
    if guard:
        rep.add("9.guard_events", "battery guard events", "INFO", guard.events or "none")
        rep.add("9.thermal_events", "temperature guard events", "INFO", tg.events or "none")
        rep.add("9.temp_max", "hottest reading per servo", "INFO", {str(k): v for k, v in sorted(tg.max_seen.items())})
        if walk.stop_log:
            rep.add("9.stop", "walk stop sequence", "INFO", walk.stop_log)
    rep.data.update(csv=str(path), runtime=dict(dir=str(rt), commit=paths.runtime_commit(rt)), loop=st)
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
    ap.add_argument("--decimate", type=int, default=1, help="log every Nth cycle (if the loop runs late)")
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
    analyze(load_csv(a.analyze), a.pack, rep)
    return rep.finish(paths.out_dir(a.out, "power_log") if a.out else None)


if __name__ == "__main__":
    sys.exit(main())
