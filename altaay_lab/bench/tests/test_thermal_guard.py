"""Servo temperature guard: rules, then the real walk loop with a rising knee temperature."""
import time

from conftest import IDS, ONNX, item, last_report, needs_walk
from odm_bench import thermal

LIM = {i: 70 for i in IDS}


def ramp(g, sid, t0, c0, rate, seconds, period=0.5, others=40.0):
    """Feed staggered-like samples: every servo each period, `sid` rising at `rate` C/s."""
    t, ev = t0, []
    while t <= t0 + seconds:
        temps = {i: others for i in IDS}
        temps[sid] = round(c0 + rate * (t - t0))
        ev += g.update(t, temps)
        t += period
    return ev


def test_rising_knee_warns_then_stops():
    g = thermal.ThermalGuard(LIM)
    ev = ramp(g, 23, 0.0, 40.0, 1.0, 40.0)
    assert [e["event"] for e in ev] == ["thermal_warn", "thermal_stop"]
    warn, stop = ev
    assert warn["servo"] == 23 and warn["threshold_c"] == 55 and warn["temp_c"] >= 55
    assert stop["threshold_c"] == 62 and stop["temp_c"] >= 62
    assert 15.0 <= warn["t"] <= 16.0          # 55 C reached at 15 s, confirmed on the next read
    assert g.hottest()[0] == 23


def test_single_spike_is_ignored_and_implausible_dropped():
    g = thermal.ThermalGuard(LIM)
    for k in range(20):
        temps = {i: 45 for i in IDS}
        if k == 7:
            temps[13] = 95                     # one bad read
        if k == 9:
            temps[24] = 200                    # outside 0 to 120 C
        assert g.update(k * 0.5, temps) == []
    assert g.dropped == 1


def test_thresholds_follow_each_servo_limit():
    lim = {**LIM, 13: 60}
    g = thermal.ThermalGuard(lim)
    assert g.warn[13] == 45 and g.stop[13] == 52 and g.warn[14] == 55
    ev = ramp(g, 13, 0.0, 40.0, 1.0, 20.0)
    assert ev[0]["event"] == "thermal_warn" and ev[0]["threshold_c"] == 45
    ok, hot = thermal.ThermalGuard(LIM).check_start({i: 50 for i in IDS} | {22: 56})
    assert not ok and hot == {22: 56}


def _walk(bus, duck_config, *extra):
    return ["--onnx_model_path", ONNX, "--duck_config_path", duck_config, "--serial_port", bus.path,
            "--no-commands", "--dry-run", "--settle-s", "0.5", "--blend-s", "0.5"] + list(extra)


def knee_profile(start_s, c0, rate):
    t_start = time.monotonic() + start_s
    return lambda now: c0 if now < t_start else c0 + rate * (now - t_start)


@needs_walk
def test_walk_thermal_warn_stands_sinks_and_turns_torque_off(make_bus, run, duck_config):
    """Left knee (ID 23) from 50 C, +1 C/s once walking: warn at 55 C (limit 70 - 15), stand,
    sink with low gains, torque off. Exit 7; hottest servo logged each second."""
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.temp_profile = lambda now: 38.0
    bus.servos[23].temp_profile = knee_profile(6.0, 50.0, 1.0)
    r, out = run("walk_with_guard.py", *_walk(bus, duck_config, "--max-seconds", "40"), timeout=200)
    rep = last_report(out, "walk_guard")
    assert r.returncode == 7, r.stdout[-3000:]
    tev = rep["data"]["thermal_events"]
    assert [e["event"] for e in tev] == ["thermal_warn"], tev
    assert tev[0]["servo"] == 23 and tev[0]["threshold_c"] == 55
    phases = [p[1] for p in rep["data"]["stop_log"]]
    assert phases[:4] == ["settle", "wait_double_support", "freeze", "standing"] and phases[-1] == "sink_off", phases
    assert all(s.mem[40] == 0 for s in bus.servos.values())
    assert item(rep, "T.limits")["measured"]["23"] == 70
    tlogs = sorted((out / "walk_guard").glob("thermal_*.csv"))
    rows = tlogs[-1].read_text().strip().splitlines()[1:]
    assert len(rows) >= 4 and all(r.split(",")[1] == "23" for r in rows[-3:])     # hottest each second


@needs_walk
def test_walk_fast_rise_hits_the_thermal_stop(make_bus, run, duck_config):
    """Right knee (ID 13) with its own limit 65 C (warn 50, stop 57), rising 5 C/s: the stop
    (torque off, exit 8) comes during the stand sequence."""
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.temp_profile = lambda now: 38.0
    bus.servos[13].mem[13] = 65
    bus.servos[13].temp_profile = knee_profile(6.0, 48.0, 5.0)
    r, out = run("walk_with_guard.py", *_walk(bus, duck_config, "--max-seconds", "40"), timeout=200)
    rep = last_report(out, "walk_guard")
    assert r.returncode == 8, r.stdout[-3000:]
    names = [e["event"] for e in rep["data"]["thermal_events"]]
    assert names == ["thermal_warn", "thermal_stop"], names
    assert rep["data"]["thermal_events"][1]["threshold_c"] == 57
    assert all(s.mem[40] == 0 for s in bus.servos.values())


@needs_walk
def test_too_hot_to_start(make_bus, run, duck_config):
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.temp_profile = lambda now: 40.0
    bus.servos[23].temp_profile = lambda now: 58.0
    r, out = run("walk_with_guard.py", *_walk(bus, duck_config, "--max-seconds", "5"))
    assert r.returncode == 9, r.stdout[-2000:]
    assert all(s.mem[40] == 0 for s in bus.servos.values())
    assert item(last_report(out, "walk_guard"), "T.start")["status"] == "FAIL"
