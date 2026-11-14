"""D16 battery guard: rules on synthetic and sim-derived sag profiles, then the real walk loop."""
import json
import math
import os
import random
import subprocess

import pytest

import battery_guard as bg
from conftest import BENCH, DATA, IDS, ONNX, PY, item, last_report, needs_libs, needs_walk
from fake_sts3215 import SYNC_WRITE, VoltageProfile


def feed(guard, seconds, fn, period=0.5, standing_after_stop=True, offset=0.0):
    t = 0.0
    while t <= seconds and guard.state != bg.HARD_STOPPED:
        v = fn(t)
        volts = None if v is None else {i: bg.quantize(x + (offset if guard.state != bg.WALKING else 0.0))
                                        for i, x in v.items()}
        for e in guard.update(t, volts):
            if e["event"] == "walk_stop" and standing_after_stop:
                guard.set_state(bg.STANDING)
        t += period
    return guard.events


def gait(level, t, rng):
    """14 servos: level minus chain drop, a 1.85 Hz gait ripple and knee-peak dips at the ankles."""
    out = {}
    for i in IDS:
        drop = 0.05 * (i % 10)                      # further down the chain, lower
        ripple = 0.25 * math.sin(2 * math.pi * 1.85 * t + i)
        dip = -1.2 if (i in (14, 24) and rng.random() < 0.15) else 0.0
        out[i] = level - drop + ripple + dip
    return out


def test_pack_floor_stops_the_walk_before_the_regulator_chart_ends():
    """D65: 10.0 V pack is the first cited i7C row. 9.6 V is still below that row."""
    g = bg.BatteryGuard()
    assert g.pack_allows_walk(10.0)
    assert not g.pack_allows_walk(9.6)
    assert not g.pack_allows_walk(9.9)
    held = {i: 12.0 for i in IDS}
    ev = g.update(1.0, held, pack_v=9.9)
    assert [e["event"] for e in ev] == ["walk_stop"]
    assert g.state == bg.STOPPING
    ok, med = bg.BatteryGuard().check_start(held, pack_v=9.9)
    assert not ok and med == 12.0
    ok, med = bg.BatteryGuard().check_start(held, pack_v=10.0)
    assert ok and med == 12.0


def test_healthy_pack_never_trips():
    rng = random.Random(3)
    g = bg.BatteryGuard()
    assert feed(g, 600, lambda t: gait(7.0, t, rng)) == []


def test_short_deep_dips_do_not_trip():
    """Ankle dips to 4.5 V and a median dip to 5.0 V for one sample: debounce holds."""
    g = bg.BatteryGuard()
    def fn(t):
        v = {i: 6.6 for i in IDS}
        if int(t * 2) % 7 == 0:
            v.update({i: 4.5 for i in IDS[:8]})      # one sample with most servos low
        return v
    assert feed(g, 300, fn) == []


def test_slow_discharge_walk_stop_then_hard_stop():
    """7.1 V to 5.0 V median over 20 min while walking; standing recovers +0.5 V (estimate)."""
    rng = random.Random(1)
    g = bg.BatteryGuard()
    ev = feed(g, 1200, lambda t: gait(7.1 - 2.1 * t / 1200, t, rng), offset=0.5)
    names = [e["event"] for e in ev]
    assert names == ["walk_stop", "hard_stop"], ev
    ws, hs = ev
    # median crosses 6.0 V around t = (7.1 - 6.0 - 0.2) / 2.1 * 1200 = 514 s (chain drop ~0.2 V)
    assert 450 < ws["t"] < 600
    assert hs["t"] > ws["t"] + 100 and hs["state"] == bg.STANDING


def test_lost_reads_while_walking_stop_the_walk():
    g = bg.BatteryGuard()
    ev = feed(g, 30, lambda t: {i: 7.0 for i in IDS} if t < 10 else None)
    assert ev and ev[0]["event"] == "walk_stop" and "no valid voltage" in ev[0]["reason"]
    assert 14.4 <= ev[0]["t"] <= 15.1           # 5 s after the last valid read at 9.5 s


def test_implausible_readings_are_dropped():
    g = bg.BatteryGuard()
    ev = feed(g, 30, lambda t: {i: (0.0 if i % 2 else 25.5) for i in IDS} if int(t) % 3 == 0 else
              {i: 7.0 for i in IDS})
    assert all(e["event"] != "walk_stop" or "no valid" in e["reason"] for e in ev)
    assert g.dropped > 0


def test_start_check():
    g = bg.BatteryGuard()
    assert g.check_start({i: 7.2 for i in IDS})[0]
    assert not g.check_start({i: 6.7 for i in IDS})[0]
    assert not g.check_start({20: 7.2})[0]                 # too few servos answered


@pytest.mark.parametrize("case,expect", [("full_typical", "none"), ("nominal_typical", "none"),
                                         ("nominal_highside", "walk_stop"), ("low_typical", "hard_stop"),
                                         ("discharge", "hard_stop")])
def test_replay_sim_profiles(case, expect, tmp_path):
    """Sim pass only: lab ngspice model, star wiring (D15), 50 Hz servo voltage traces."""
    rc = bg.main(["--replay", str(DATA / f"sim_star_{case}.csv"), "--expect", expect, "--out", str(tmp_path)])
    assert rc == 0


def test_discharge_walk_stop_lands_near_3_55_volt_per_cell():
    """D16: stop walking at about 3.5 V per cell under load. In the sim discharge each 6 s step
    has one cell OCV; the walk stop must fall in the 3.6 or 3.55 V step."""
    g, trace, stopped_at = bg.replay(str(DATA / "sim_star_discharge.csv"), bg.GuardConfig())
    cells = [4.0, 3.9, 3.8, 3.7, 3.6, 3.55, 3.5, 3.45, 3.4, 3.35, 3.3, 3.25, 3.2]
    step = int(stopped_at // 6.0)
    assert cells[step] in (3.6, 3.55), (stopped_at, cells[step])
    hard = [e for e in g.events if e["event"] == "hard_stop"][0]
    assert cells[int(hard["t"] // 6.0)] in (3.45, 3.4, 3.35, 3.3)


def _walk_args(bus, duck_config, *extra):
    return ["--onnx_model_path", ONNX, "--duck_config_path", duck_config, "--serial_port", bus.path,
            "--no-commands", "--dry-run"] + list(extra)


@needs_walk
def test_walk_refuses_to_start_on_a_low_battery(make_bus, run, duck_config):
    bus = make_bus(reg85=0, volts=6.5)
    r, out = run("walk_with_guard.py", *_walk_args(bus, duck_config, "--max-seconds", "3"))
    assert r.returncode == 4, r.stdout[-2000:]
    assert all(s.mem[40] == 0 for s in bus.servos.values())          # torque never turned on
    rep = last_report(out, "walk_guard")
    assert item(rep, "11.start")["status"] == "FAIL"


@needs_walk
def test_walk_with_guard_full_sequence_on_sim_discharge(make_bus, run, duck_config, tmp_path):
    """Real Runtime walk loop + real policy + real rustypot/pypot on the simulated bus. Servo
    voltages follow the sim discharge profile 8x faster than recorded. Expected: walk stop,
    zero command, freeze in double support, blend to the standing pose, hard stop, torque off,
    power off command."""
    bus = make_bus(reg85=0, volts=7.2)
    prof = VoltageProfile(str(DATA / "sim_star_discharge.csv"), speed=8.0)
    flag = tmp_path / "poweroff_called"
    bus.set_profile(prof, delay_s=7.0)     # start-up (onnx load, turn_on) takes about 5 to 6 s
    r, out = run("walk_with_guard.py", *_walk_args(bus, duck_config, "--max-seconds", "40",
                                                    "--walk-stop-hold", "1.0", "--hard-stop-hold", "0.5",
                                                    "--walking-floor-v", "4.0", "--period", "0.1",
                                                    "--settle-s", "0.5", "--blend-s", "0.5",
                                                    "--poweroff-cmd", f"touch {flag}"),
                 env={"ODM_FAKE_FEET": "11"}, timeout=240)
    rep = last_report(out, "walk_guard")
    names = [e["event"] for e in rep["data"]["events"]]
    assert names == ["walk_stop", "hard_stop"], (names, r.stdout[-3000:])
    phases = [p[1] for p in rep["data"]["stop_log"]]
    assert phases == ["settle", "wait_double_support", "freeze", "standing"], rep["data"]["stop_log"]
    assert rep["data"]["stop_log"][2][2] == "both feet on the ground"
    assert r.returncode == 6
    assert all(s.mem[40] == 0 for s in bus.servos.values())          # torque off on all 14
    assert all(s.mem[21] == 2 for s in bus.servos.values())          # low gains first (HWI.low_torque_kps)
    assert not flag.exists()                                          # --dry-run: printed, not run
    assert "would run: touch" in r.stdout


@needs_walk
def test_rustypot_panic_after_checksum_error_is_caught(make_bus, run, duck_config):
    """UPSTREAM_ISSUES.md G10: a corrupted status packet makes rustypot return early, the rest of
    the sync read is still arriving, and the next send's flush-then-assert panics. With wire
    timing on, the fake reproduces it; walk_with_guard turns torque off through pypot (exit 3).
    The pass condition is the read-back: a sync write sent while the bus still babbles can sit
    unprocessed or be lost (VERIFICATION.md E8), so the guard must read register 40 back and
    write again until all 14 read 0, and only then report the stop as done."""
    bus = make_bus(reg85=0, volts=7.2, wire_time=True)
    bus.log_on = False
    import threading
    import time as _t

    def corrupt_later():
        _t.sleep(9.0)                     # after start-up (turn_on takes about 5 s)
        bus.fault(20).corrupt_next = 3
        bus.babble(1.5)
    threading.Thread(target=corrupt_later, daemon=True).start()
    r, out = run("walk_with_guard.py", *_walk_args(bus, duck_config, "--max-seconds", "12"), timeout=120)
    rep = last_report(out, "walk_guard")
    crash = [i for i in rep["items"] if i["item"] == "11.bus"]
    if not crash:
        pytest.skip(f"no panic this run (timing race); errors {item(rep, '11.errors')['measured']}")
    assert "PanicException" in crash[0]["desc"], crash
    assert "pypot low kp + torque off sent" in crash[0]["measured"], crash[0]["measured"]
    tq = item(rep, "11.torque_off")
    assert tq["status"] == "PASS", (tq, crash[0]["measured"], r.stdout[-2000:])
    assert tq["measured"] == {str(i): 0 for i in IDS}, tq
    assert r.returncode == 3
    on = {i: (s.mem[40], s.mem[21]) for i, s in bus.servos.items() if s.mem[40] != 0}
    assert not on, (on, crash[0]["measured"], bus.counts)


def keeps_torque(servo):
    """This fake servo ignores torque off: register 40 stays 1 after any write to it."""
    write = servo.write

    def stuck(addr, data, now):
        write(addr, data, now)
        if addr <= 40 < addr + len(data):
            servo.mem[40] = 1
    servo.write = stuck


def lose_next_torque_write(bus):
    """The fake drops the next sync write to register 40, as a write lost on a noisy bus."""
    lost, handle = [], bus._handle

    def dropping(pkt, t_rx):
        if not lost and pkt[4] == SYNC_WRITE and pkt[5] == 40:
            lost.append(bytes(pkt))
            return
        handle(pkt, t_rx)
    bus._handle = dropping
    return lost


HARD_STOP = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
from odm_bench import bus, joints, walkhooks


class PanicException(BaseException):
    """Stand-in for the pyo3 PanicException: after a G10 panic every rustypot call panics."""


class DeadRustypot:
    def set_kps(self, ids, kps):
        raise PanicException("rustypot mutex poisoned")


class HWI:
    joints = dict(joints.JOINTS)
    low_torque_kps = [2.0] * 14
    io = DeadRustypot()

    def turn_off(self):
        raise PanicException("rustypot mutex poisoned")


class NoExpression:
    antennas = eyes = projector = False


class Feet:
    def stop(self):
        pass


cls = walkhooks.build_walk_class(object)
walk = cls.__new__(cls)               # no RLWalk start-up: only what hard_stop uses
walk.hwi, walk.duck_config, walk.feet_contacts = HWI(), NoExpression(), Feet()
io = bus.open_pypot(sys.argv[1], sync_read=True)
done = walk.hard_stop(io, low_gain_s=0.1, confirm_tries=4, retry_wait_s=0.1)
print(json.dumps(dict(done=done, check=walk.torque_check)))
'''


def _hard_stop(bus):
    """walkhooks.hard_stop with a dead rustypot and the real pypot on the fake bus, in a subprocess."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", ODM_PYPOT_TIMEOUT="0.2")
    r = subprocess.run([PY, "-c", HARD_STOP, bus.path, str(BENCH)], capture_output=True, text=True, env=env,
                       timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1]), r


@needs_libs
def test_hard_stop_writes_torque_off_again_until_it_reads_back(make_bus):
    """E8 failure mode without the timing race: the first torque off sync write is lost. The
    read-back sees register 40 = 1, writes again, and confirms 0 on all 14."""
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.mem[40] = 1
    lost = lose_next_torque_write(bus)
    res, r = _hard_stop(bus)
    chk = res["check"]
    assert lost, "the fake did not drop a torque off write"
    assert chk["ok"] and chk["reads"] >= 2, res
    assert chk["readback"] == {str(i): 0 for i in IDS}, chk
    assert all(s.mem[40] == 0 for s in bus.servos.values())
    assert all(s.mem[21] == 2 for s in bus.servos.values())          # low gains went out first
    assert "TORQUE OFF NOT CONFIRMED" not in r.stdout + r.stderr


@needs_libs
def test_hard_stop_never_claims_torque_off_it_cannot_read_back(make_bus):
    """ID 23 keeps torque and ID 31 never answers: both are named, loudly, and ok is False."""
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.mem[40] = 1
    keeps_torque(bus.servos[23])
    bus.fault(31).drop = True
    res, r = _hard_stop(bus)
    chk = res["check"]
    assert not chk["ok"], res
    assert chk["still_on"] == [23] and chk["no_answer"] == [31] and chk["reads"] == 4, chk
    assert "TORQUE OFF NOT CONFIRMED" in r.stderr and "still on [23], no answer [31]" in r.stderr, r.stderr
    assert {i for i, s in bus.servos.items() if s.mem[40]} == {23}


@needs_walk
def test_walk_battery_hard_stop_with_a_servo_that_keeps_torque_exits_10(make_bus, run, duck_config):
    """The real walk loop: the pack falls under the walking floor, the guard hard stops, but ID 31
    keeps torque. walk_with_guard must not report a safe stop: 11.torque_off FAIL, exit 10."""
    bus = make_bus(reg85=0, volts=7.2)
    bus.set_profile(VoltageProfile(rows=[(0.0, {i: 7.2 for i in IDS}), (0.5, {i: 5.0 for i in IDS})]), delay_s=7.0)
    keeps_torque(bus.servos[31])
    r, out = run("walk_with_guard.py", *_walk_args(bus, duck_config, "--max-seconds", "40", "--period", "0.1",
                                                    "--poweroff-cmd", "true"), timeout=240)
    rep = last_report(out, "walk_guard")
    assert [e["event"] for e in rep["data"]["events"]] == ["hard_stop"], (rep["data"]["events"], r.stdout[-3000:])
    assert r.returncode == 10, r.stdout[-3000:]
    tq = item(rep, "11.torque_off")
    assert tq["status"] == "FAIL" and tq["measured"] == {**{str(i): 0 for i in IDS}, "31": 1}, tq
    assert "TORQUE OFF NOT CONFIRMED" in r.stdout and "still on [31]" in r.stdout
    assert {i for i, s in bus.servos.items() if s.mem[40]} == {31}
