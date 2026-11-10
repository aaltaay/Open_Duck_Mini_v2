#!/usr/bin/env python3
"""Adapter check and first servo bench test (TEST_PLAN.md sections 6 and 7, D1, D2, G1, G3).

One servo alone on the adapter, powered from the bench supply through its own lead (D15),
adapter on the Pi USB with H1 unpowered and the jumper on B. Library and calls as the Runtime
configure scripts: pypot FeetechSTS3215IO(port) at 1 Mbaud (scripts/configure_motor.py).

Steps (--steps, default "6,7.1,7.2"):
  6     adapter: the port exists, its USB ID is the CH343 (1a86:55d3, Waveshare schematic), and
        exactly one servo answers a ping scan of IDs 0 to 253.
  7.1   factory dump (registers 0 to 86, kept as JSON), then with --configure ID the Runtime's
        own scripts/configure_motor.py --port P --id ID (run as a subprocess, unmodified),
        then read back 41, 44, 46, 84, 85, 86, firmware, P/D/I, mode, voltage limits.
        Gates: 85 = 0 (G1); 41 = 0, 44 = 0, 46 = 0 (G1 action 2); P/D/I = 32/0/0 (configure).
        Firmware is written down (INFO); compare all 14 later with power_log.py --idle (G3).
  7.2   no-load speed: a 2 rad step (-1 to +1 rad) and a 1.5 Hz 0.4 rad sine, servo free to
        turn. Gate: peak speed >= 4.8 rad/s at 7.4 V supply (TEST_PLAN "about 5 rad/s or more";
        firmware limit 3400 steps/s = 5.215 rad/s, BAM; 4.8 = 92% of it, lab choice). Under
        4.0 rad/s is the issue #48 signature (2.7 rad/s): check register 85 and the label.
  7.3   thermal hold (D2): --thermal with the load rig on (1.5 Nm by D2) at 7.2 V: hold the
        position, read temperature, voltage, current, load and status every --thermal-period s
        for --thermal-seconds; read Max Temperature Limit (13) once.
        Gate: max temperature <= limit - 10 C. If the servo unloads itself (status overload or
        current bits, or torque enable reads 0) the run is INCOMPLETE: 1.5 Nm needs about
        2.0 A at the C001 stall ratio (1.91 Nm at 2.5 A), the same as the factory protection
        current (register 28 = 310 x 6.5 mA = 2.0 A for register 35 = 200 x 10 ms = 2 s).
  7.4   note only: the 2 A for 2 s torque cut is the servo protecting itself, not a fault.
Exit: 0 pass, 1 fail, 2 incomplete.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import bus, joints, paths, report, sts3215  # noqa: E402

CH343 = ("1a86", "55d3")     # WCH ch343ser_linux driver/ch343.c id table (CH343 chip)
FIRMWARE_SPEED_LIMIT = 3400 * 2 * math.pi / 4096   # 5.215 rad/s, BAM commit 5b0486e
SPEED_PASS, SPEED_ISSUE48 = 4.8, 4.0
STALL_A_PER_NM = 2.5 / 1.91  # C001 datasheet ratio (SERVO_DEEP_DIVE.md section 2)


def usb_id(port):
    """Return (vendor, product) for a tty, read from sysfs (no extra package)."""
    try:
        dev = os.path.realpath(f"/sys/class/tty/{os.path.basename(os.path.realpath(port))}/device")
    except OSError:
        return None
    d = dev
    for _ in range(6):
        v, p = os.path.join(d, "idVendor"), os.path.join(d, "idProduct")
        if os.path.exists(v) and os.path.exists(p):
            return open(v).read().strip(), open(p).read().strip()
        d = os.path.dirname(d)
    return None


def step6(a, rep, io):
    rep.gate("6.port", "serial port exists", os.path.exists(a.port), a.port, "present", "TEST_PLAN 6")
    uid = usb_id(a.port)
    if uid is None:
        rep.add("6.usb", "USB vendor:product of the port", "WARN", "not a USB tty (fake bus or other)",
                "1a86:55d3 (CH343)", "Waveshare adapter schematic; WCH driver id table")
    else:
        rep.add("6.usb", "USB vendor:product of the port", "PASS" if uid == CH343 else "WARN", ":".join(uid),
                "1a86:55d3 (CH343)", "Waveshare adapter schematic; WCH driver id table")
    found = bus.scan(io, range(254)) if not a.ids else [i for i in a.ids if bus.ping(io, i)]
    rep.gate("6.servo", "exactly one servo answers (servo alone on the bench)", len(found) == 1, found, "1 servo",
             "TEST_PLAN 6")
    return found


def dump(io, sid):
    regs, raw = {}, {}
    for start, n in sts3215.DUMP_BLOCKS:
        try:
            data = bus.read_block(io, sid, start, n)
            raw[start] = data.hex()
            regs.update(sts3215.parse_block(start, data))
        except Exception:  # noqa: BLE001 - read the block one register at a time
            for name, (addr, size) in sts3215.REG.items():
                if start <= addr < start + n and name not in regs:
                    try:
                        regs[name] = bus.read_reg(io, sid, name)
                    except Exception as e:  # noqa: BLE001
                        regs[name] = f"error: {e}"
    return regs, raw


def run_configure(a, rep):
    rt = paths.find_runtime(a.runtime)
    script = rt / "scripts" / "configure_motor.py"
    cmd = [sys.executable, str(script), "--port", a.port, "--id", str(a.configure)]
    print("running the Runtime configure script:", " ".join(cmd), flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(cmd, cwd=str(rt / "scripts"), capture_output=True, text=True, env=env, timeout=600)
    tail = (r.stdout + r.stderr).strip().splitlines()[-8:]
    rep.gate("7.1.configure", "Runtime scripts/configure_motor.py ran", r.returncode == 0, " | ".join(tail),
             "exit 0", "configure_motor.py at 376de65")
    return r.returncode == 0


CONFIG_VALUES = (("mode", 0), ("maximum_acceleration", 0), ("acceleration", 0), ("P_coefficient", 32),
                 ("I_coefficient", 0), ("D_coefficient", 0))      # configure_motor.py lines 63 to 69
REG_OF = dict(mode="mode", maximum_acceleration="maximum_acceleration", acceleration="acceleration",
              P_coefficient="p_coefficient", I_coefficient="i_coefficient", D_coefficient="d_coefficient")


def fix_config(io, sid, rep, tries=3):
    """Write configure_motor.py's values again with the same pypot setters (drained flush), read
    each back, then lock the EEPROM as configure_all_motors.py does (set_lock 1)."""
    io.set_lock({sid: 0})
    bad = []
    for name, val in CONFIG_VALUES:
        ok = False
        for _ in range(tries):
            getattr(io, f"set_{name}")({sid: val})
            if bus.read_reg(io, sid, REG_OF[name]) == val:
                ok = True
                break
        if not ok:
            bad.append(name)
    io.set_lock({sid: 1})
    rep.gate("7.1.fix", "configure values written again and read back (configure_motor.py values)", not bad,
             bad or "all read back", "all read back", "first_servo_check.py --fix-config")
    rep.add("7.1.persist", "power-cycle the servo, then run --steps 7.1 again: 85 must still read 0", "MANUAL",
            None, None, "EEPROM lock register 55")


def step71(a, rep, io, sid):
    before, raw = dump(io, sid)
    rep.data["factory_dump"] = dict(id=sid, registers=before, raw=raw)
    rep.add("7.1.factory", "factory register dump kept in this report (G1: keep the factory dump)", "INFO",
            {k: before.get(k) for k in ("firmware_major", "firmware_minor", "maximum_acceleration",
                                        "acceleration", "max_voltage_limit", "p_coefficient", "d_coefficient")})
    if a.configure is not None:
        if not run_configure(a, rep):
            return sid
        io.flush()
        sid = a.configure
    after, raw2 = dump(io, sid)
    if a.fix_config and (after.get("maximum_acceleration") != 0 or
                         (after.get("p_coefficient"), after.get("d_coefficient"), after.get("i_coefficient")) != (32, 0, 0)
                         or after.get("acceleration") != 0):
        rep.add("7.1.lost", "configure values did not all stick (lost sync writes?)", "WARN",
                {k: after.get(k) for k in ("maximum_acceleration", "acceleration", "p_coefficient", "d_coefficient",
                                           "i_coefficient")}, None, "SOFTWARE.md section 3, pypot output flush")
        fix_config(io, sid, rep)
        after, raw2 = dump(io, sid)
    rep.data["after_configure"] = dict(id=sid, registers=after, raw=raw2)
    fw = (after.get("firmware_major"), after.get("firmware_minor"))
    rep.add("7.1.fw", "firmware major.minor (write it down; all 14 must match, G3)", "INFO", f"{fw[0]}.{fw[1]}")
    rep.gate("7.1.r85", "register 85 (maximum acceleration) = 0", after.get("maximum_acceleration") == 0,
             after.get("maximum_acceleration"), "0", "UPSTREAM_ISSUES.md G1")
    for item, name in (("7.1.r41", "acceleration"), ("7.1.r44", "goal_time"), ("7.1.r46", "goal_speed")):
        rep.gate(item, f"register {sts3215.REG[name][0]} ({name}) = 0", after.get(name) == 0, after.get(name), "0",
                 "UPSTREAM_ISSUES.md G1 action 2")
    rep.add("7.1.r84", "register 84 (maximum velocity, pypot name)", "INFO", after.get("maximum_velocity"))
    r86 = after.get("acceleration_multiplier")
    rep.add("7.1.r86", "register 86 (acceleration multiplier on newer firmware)", "INFO", r86)
    pid = (after.get("p_coefficient"), after.get("d_coefficient"), after.get("i_coefficient"))
    rep.add("7.1.pid", "P/D/I after configure", "PASS" if pid == (32, 0, 0) else ("WARN" if a.configure is None else "FAIL"),
            pid, "32/0/0", "configure_motor.py lines 67 to 69")
    rep.gate("7.1.id", "servo ID", sid == (a.configure if a.configure is not None else sid), sid,
             a.configure, "joint map: rustypot_position_hwi.py")
    vmax = after.get("max_voltage_limit")
    if isinstance(vmax, int):
        rep.add("7.1.r14", "Max Voltage Limit (register 14)", "PASS" if vmax >= 75 else "WARN", f"{vmax / 10:.1f} V",
                ">= 7.5 V (BEC 7.2 V +/- 0.1 V, TEST_PLAN 4.1)", "G4 outside evidence: 80 on new units")
    vmin = after.get("min_voltage_limit")
    if isinstance(vmin, int):
        rep.add("7.1.r15", "Min Voltage Limit (register 15): the servo's own cut", "INFO", f"{vmin / 10:.1f} V",
                "below the 6.0 V guard hard stop (D16)")
    return sid


def track(io, sid, goal_fn, seconds, rate=200.0):
    """Stream goal positions (deg) and sample present position (deg) as fast as the bus allows."""
    t0 = time.perf_counter()
    ts, pos, goals = [], [], []
    last_goal = None
    while True:
        t = time.perf_counter() - t0
        if t > seconds:
            break
        g = goal_fn(t)
        if g != last_goal:
            io.set_goal_position({sid: g})
            last_goal = g
        try:
            p = io.get_present_position([sid])
        except Exception:  # noqa: BLE001 - a dropped read is counted by the error counter
            p = None
        if p:
            ts.append(time.perf_counter() - t0)       # stamp after the read: the time the position belongs to
            pos.append(p[0]); goals.append(g)
        time.sleep(max(0.0, 1.0 / rate - (time.perf_counter() - t0 - t)))
    return ts, pos, goals


def peak_speed(ts, pos_deg, window_s=0.03):
    """Largest mean speed over any window of at least window_s (short windows are read noise)."""
    best = 0.0
    j = 0
    for k in range(len(ts)):
        while j + 1 < k and ts[k] - ts[j + 1] >= window_s:
            j += 1
        dt = ts[k] - ts[j]
        if dt >= window_s:
            best = max(best, abs(math.radians(pos_deg[k] - pos_deg[j])) / dt)
    return best


def step72(a, rep, io, sid):
    v = bus.read_reg(io, sid, "present_voltage") / 10.0
    rep.add("7.2.supply", "supply at the servo (Present Voltage)", "PASS" if abs(v - 7.4) <= 0.2 else "WARN",
            f"{v:.1f} V", "7.4 +/- 0.2 V", "TEST_PLAN 7.2")
    io.enable_torque([sid])
    io.set_goal_position({sid: -57.3})
    time.sleep(1.5)
    ts, pos, _ = track(io, sid, lambda t: 57.3, 1.5)
    sp = peak_speed(ts, pos)
    st = "PASS" if sp >= SPEED_PASS else ("WARN" if sp >= SPEED_ISSUE48 else "FAIL")
    rep.add("7.2.step", "2 rad step: peak no-load speed", st, f"{sp:.2f} rad/s ({len(ts)} samples)",
            f">= {SPEED_PASS} rad/s (firmware limit {FIRMWARE_SPEED_LIMIT:.3f})", "TEST_PLAN 7.2, SERVO_DEEP_DIVE 6")
    amp = 0.4
    ts2, pos2, g2 = track(io, sid, lambda t: round(math.degrees(amp * math.sin(2 * math.pi * 1.5 * t)), 2), 4.0, 100.0)
    if len(pos2) > 20:
        half = len(pos2) // 2
        rng_meas = (max(pos2[half:]) - min(pos2[half:])) / 2
        ratio = math.radians(rng_meas) / amp
        rep.add("7.2.sine", "1.5 Hz 0.4 rad sine: amplitude ratio (second half)", "INFO", f"{ratio:.2f}",
                "compare with sim (issue #48: 0.31 to 0.49 on hardware)", "SERVO_DEEP_DIVE.md section 5")
    io.set_goal_position({sid: 0.0})
    rep.data["step"] = dict(t=ts, pos_deg=pos)
    return sp


def step73(a, rep, io, sid):
    limit = bus.read_reg(io, sid, "max_temperature_limit")
    rep.add("7.3.limit", "Max Temperature Limit (register 13)", "INFO", f"{limit} C", None, "D2")
    v = bus.read_reg(io, sid, "present_voltage") / 10.0
    rep.add("7.3.supply", "supply at the servo", "PASS" if abs(v - 7.2) <= 0.2 else "WARN", f"{v:.1f} V",
            "7.2 +/- 0.2 V", "D2")
    pos = io.get_present_position([sid])[0]
    io.enable_torque([sid])
    io.set_goal_position({sid: pos})
    log, t0 = [], time.monotonic()
    tripped = None
    while True:
        t = time.monotonic() - t0
        blk = bus.read_block(io, sid, 56, 15)            # 56..70 like the Feetech SDK FeedBack
        r = sts3215.parse_block(56, blk)
        te = bus.read_reg(io, sid, "torque_enable")
        row = dict(t=round(t, 1), temp=r["present_temperature"], volts=r["present_voltage"] / 10,
                   amps=round(abs(sts3215.current_a(r["present_current"])), 3), load=r["present_load"] & 0x3FF,
                   status=r["status"], torque=te)
        log.append(row)
        print(f"t {row['t']:6.1f} s  temp {row['temp']} C  {row['volts']:.1f} V  {row['amps']:.2f} A  "
              f"load {row['load']}  status {sts3215.status_text(row['status'])}", flush=True)
        if tripped is None and (te == 0 or row["status"] & 0x28):
            tripped = row["t"]
            break
        if t >= a.thermal_seconds:
            break
        time.sleep(max(0.0, a.thermal_period - (time.monotonic() - t0 - t)))
    rep.data["thermal_log"] = log
    tmax = max(r["temp"] for r in log)
    amps = [r["amps"] for r in log[1:]] or [0.0]
    mean_a = sum(amps) / len(amps)
    est_nm = mean_a / STALL_A_PER_NM
    rep.add("7.3.load", "mean current and torque estimate (C001 stall ratio)",
            "PASS" if est_nm >= 0.8 * a.thermal_nm else "WARN", f"{mean_a:.2f} A ~ {est_nm:.2f} Nm",
            f">= 80% of {a.thermal_nm} Nm (load really applied)", "SERVO_DEEP_DIVE section 2")
    if tripped is not None:
        rep.add("7.3.hold", "servo unloaded itself during the hold (protection)", "INCOMPLETE",
                f"at {tripped} s, status {sts3215.status_text(log[-1]['status'])}",
                "full hold time", "TEST_PLAN 7.4; registers 28 and 35")
    elif log[-1]["t"] < a.thermal_seconds:
        rep.add("7.3.hold", "hold shorter than asked", "INCOMPLETE", f"{log[-1]['t']} s", f"{a.thermal_seconds} s")
    rep.gate("7.3.temp", "max temperature at least 10 C under the servo limit", tmax <= limit - 10,
             f"{tmax} C", f"<= {limit - 10} C", "D2")
    return tmax


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--configure", type=int, help="run the Runtime configure_motor.py with this ID (7.1)")
    ap.add_argument("--id", type=int, help="test this ID (default: the one servo the scan finds)")
    ap.add_argument("--angle-limits", action="store_true",
                    help="after the other steps, write the D59 angle limits of this ID (software/servo_limits.json, zero offset) and read them back")
    ap.add_argument("--fix-config", action="store_true",
                    help="if the read-back after configuring is wrong, write configure_motor.py's values again "
                         "(same pypot setters) and verify each one")
    ap.add_argument("--ids", type=lambda s: [int(x) for x in s.split(",")], help="ping only these IDs in step 6")
    ap.add_argument("--steps", default="6,7.1,7.2", help="comma list from 6,7.1,7.2,7.3")
    ap.add_argument("--thermal", action="store_true", help="also run 7.3 (needs the load rig)")
    ap.add_argument("--thermal-seconds", type=float, default=600.0)
    ap.add_argument("--thermal-period", type=float, default=10.0)
    ap.add_argument("--thermal-nm", type=float, default=1.5, help="load rig torque (D2: 1.5 Nm)")
    ap.add_argument("--runtime", help="Runtime checkout (for configure_motor.py)")
    ap.add_argument("--yes", action="store_true", help="do not ask for the bench set-up confirmations")
    ap.add_argument("--out", help="log folder (default ODM_BENCH_OUT or ~/odm_bench_logs)")
    a = ap.parse_args(argv)
    steps = set(a.steps.split(","))
    if a.thermal:
        steps.add("7.3")
    out = paths.out_dir(a.out, "first_servo")
    rep = report.Report("first_servo_check", "6, 7", "Adapter and first servo")
    rep.add("7.0", "bench supply 7.4 V, 3 A limit, servo alone, own power lead (D15); H1 unpowered, jumper B",
            "MANUAL", None, None, "TEST_PLAN 6 and 7")
    if not report.confirm("Bench set up as above, servo horn free to turn +/- 1.5 rad?", a.yes):
        rep.add("7.0.confirm", "operator did not confirm the set-up", "INCOMPLETE")
        return rep.finish(out)
    errors = bus.BusErrors()
    io = bus.open_pypot(a.port, sync_read=False, errors=errors)   # configure_motor.py: FeetechSTS3215IO(port)
    sid = a.id
    if "6" in steps:
        found = step6(a, rep, io)
        if sid is None and len(found) == 1:
            sid = found[0]
        rep.add("6.scan", "ping scan timeouts (expected: IDs with no servo)", "INFO", errors.count("timeout"))
        errors.reset()
    if sid is None:
        found = bus.scan(io, [joints.FACTORY_ID] + list(range(254)))
        sid = found[0] if found else None
    if sid is None:
        rep.add("7.id", "no servo found", "INCOMPLETE")
        return rep.finish(out)
    if "7.1" in steps:
        sid = step71(a, rep, io, sid)
    if "7.2" in steps:
        step72(a, rep, io, sid)
    if "7.3" in steps:
        if report.confirm(f"Load rig on ({a.thermal_nm} Nm), supply at 7.2 V, ready for "
                          f"{a.thermal_seconds:.0f} s hold?", a.yes):
            step73(a, rep, io, sid)
        else:
            rep.add("7.3", "thermal hold not run (no confirmation)", "INCOMPLETE")
    if a.angle_limits and sid is not None:
        # D59: the angle limit registers to the software limits (zero offset until the joint is calibrated, TEST_PLAN 19.1),
        # written last: 7.2 and 7.3 need the servo's whole range for their steps and sine
        import set_angle_limits as SAL
        rows = SAL.table(SAL.load_limits(), {}, ids=[sid], zero_offsets=True)
        if not rows:
            rep.add("7.1.limits", "angle limits: ID %d is not a joint in software/servo_limits.json" % sid, "FAIL")
        else:
            ok = SAL.write_rows(io, rows)
            rep.gate("7.1.limits", "angle limit registers 9 and 11 read back the software limits (D59, zero offset)", ok,
                     "%s" % rows[0].get("read_back"), "%s" % [rows[0]["min_raw"], rows[0]["max_raw"]], "D59")
    rep.add("7.4", "servo cuts torque after more than 2 A for 2 s by default: protection, not a fault", "MANUAL",
            None, None, "TEST_PLAN 7.4")
    try:
        io.disable_torque([sid])
    except Exception:  # noqa: BLE001
        pass
    rep.add("bus", "bus errors during the test", "INFO", errors.snapshot())
    return rep.finish(out)


if __name__ == "__main__":
    sys.exit(main())
