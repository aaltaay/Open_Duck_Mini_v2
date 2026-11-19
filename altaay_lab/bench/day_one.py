#!/usr/bin/env python3
"""Day-one bench: one pass, one report file per step.

Steps, in order:
  bus       servo scan against the 14 joint ids (TEST_PLAN 8.1, SOFTWARE.md section 2)
  limits    angle-limit registers against software/servo_limits.json (TEST_PLAN 19.1)
  voltage   meter prompts for the 12.0 V rail and the 5 V rail, then each servo
  camera    a frame from the camera, or the mock frame
  imu       still reads, no jump (TEST_PLAN 10.1)
  eyes      GPIO24 and GPIO23 on then off (netlist)
  antennas  hardware PWM overlay, 1 ms to 2 ms, then pulses off
  speaker   a short tone, amp shutdown low again (D48)
  mic       both slots, under the clip line (TEST_PLAN 17.4)
  charge    body charge pins open when not on the cloth (TEST_PLAN section 2)

  python3 day_one.py --mock --out /tmp/odm_dayone
  python3 day_one.py --port /dev/ttyACM0

--mock runs with bench/mock_hw.py. No adapter, no Pi, no Runtime import.
The first line of a mock run says "mock hardware".
Exit 0 when every step passes, 1 on a FAIL, 2 when a step is INCOMPLETE and none failed.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(LAB, "software"))

from odm_bench import joints, report, sts3215  # noqa: E402
from odm_bench.paths import out_dir, stamp  # noqa: E402

# Cited, netlist domain SERVO_12V0: i7C at 12.0 V, plus or minus 4 percent.
BEC_SET_V = 12.0
BEC_LO_V = 11.52
BEC_HI_V = 12.48
# Cited, netlist domain 5V and part_limits pololu_4892, 4 percent of 5.00 V.
RAIL5_LO_V = 4.80
RAIL5_HI_V = 5.20
# Cited, TEST_PLAN section 2.
INSULATION_OHM = 1.0e6
# Cited, imu_check.py glitch gates (TEST_PLAN 10.1).
ACC_LIM = 0.5
GYRO_LIM = 0.1
# Cited, TEST_PLAN 17.4.
CLIP = 0.99
# Cited, SOFTWARE.md section 4: level accel z is about +9.81, x and y near 0.
LEVEL_Z = 8.0
LEVEL_XY = 1.5

STEPS = ("bus", "limits", "voltage", "camera", "imu", "eyes", "antennas", "speaker", "mic", "charge")

# Cited pin map. day-one prints these so a wiring miss is a failed identity check.
PINS = {
    "eye_left": 24,
    "eye_right": 23,
    "antenna_right_pwm0": 12,
    "antenna_left_pwm1": 13,
    "amp_sd": 16,
    "i2s_bclk": 18,
    "i2s_lrc": 19,
    "i2s_mic": 20,
    "i2s_din": 21,
    "charge_stat": 5,
    "charge_en": 6,
}


def _save(rep, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("%s_%s.json" % (rep.script, stamp()))
    rep.save(str(path))
    print(rep.render())
    print("report: %s" % path)
    print("STEP %s %s" % (rep.script, rep.overall()))
    return path


def _median(xs):
    ys = sorted(xs)
    n = len(ys)
    if n == 0:
        return None
    if n % 2:
        return ys[n // 2]
    return 0.5 * (ys[n // 2 - 1] + ys[n // 2])


def step_bus(hw, rep):
    found = list(hw.servo_ids())
    want = list(joints.IDS)
    rep.gate("bus.count", "14 joint servos answer", len(found) == len(want) and set(found) == set(want),
             sorted(found), sorted(want), "SOFTWARE.md section 2, TEST_PLAN 8.1")
    extra = sorted(set(found) - set(want))
    missing = sorted(set(want) - set(found))
    rep.gate("bus.ids", "ids match the joint map, none extra", not extra and not missing,
             {"found": sorted(found), "missing": missing, "extra": extra},
             "ids " + ",".join(str(i) for i in want), "joints.py from the Runtime HWI and WIRING.md section 2")
    if hw.name == "mock hardware":
        rep.add("bus.link", "servo bus stand-in", "INFO", "mock hardware",
                "CH343 1a86:55d3 on a Pi", "TEST_PLAN 6; this run has no adapter")
    return rep


def step_limits(hw, rep):
    import set_angle_limits as lim
    table = lim.load_limits()
    bad = []
    outside = []
    for joint, spec in table.items():
        sid = spec["id"]
        want = (spec["raw_soft"][0], spec["raw_soft"][1])
        try:
            got = (hw.read_reg(sid, "min_angle_limit"), hw.read_reg(sid, "max_angle_limit"))
            pos = hw.read_reg(sid, "present_position")
        except KeyError:
            bad.append({"joint": joint, "id": sid, "error": "no servo"})
            continue
        if got != want:
            bad.append({"joint": joint, "id": sid, "read": list(got), "raw_soft": list(want)})
        if pos < got[0] or pos > got[1]:
            outside.append({"joint": joint, "id": sid, "position": pos, "window": list(got)})
    rep.gate("limits.registers", "registers 9 and 11 equal servo_limits.json raw_soft",
             not bad, bad or "14 servos", "raw_soft, zero offset",
             "TEST_PLAN 19.1, servo_limits.json label calc")
    rep.gate("limits.position", "present position is inside the programmed window",
             not outside, outside or "inside", "min_angle_limit to max_angle_limit",
             "read only, no goal write")
    # The json stores raw_soft. Recomputing with set_angle_limits.registers can
    # differ by one encoder step (0.088 deg, CALIBRATION.md). That is INFO.
    drift = []
    for joint, spec in table.items():
        lo, hi = lim.registers(spec["soft_lo_deg"], spec["soft_hi_deg"], 0.0)
        if [lo, hi] != spec["raw_soft"]:
            drift.append({"joint": joint, "calc": [lo, hi], "raw_soft": spec["raw_soft"]})
    rep.add("limits.calc", "raw_soft against the inward rounding in set_angle_limits.py",
            "INFO", drift or "match", "one encoder step is 0.088 deg",
            "calc only; the hardware gate is raw_soft")
    return rep


def step_voltage(hw, rep):
    meters = hw.meters()
    bec = meters.get("bec_v")
    rail = meters.get("rail_5v")
    if bec is None:
        rep.add("voltage.bec", "servo rail meter", "INCOMPLETE", None,
                "%s to %s V" % (BEC_LO_V, BEC_HI_V), "netlist SERVO_12V0")
    else:
        rep.gate("voltage.bec", "servo rail at the 12.0 V set point",
                 BEC_LO_V <= bec <= BEC_HI_V, bec, "%s to %s V" % (BEC_LO_V, BEC_HI_V),
                 "cited, netlist SERVO_12V0, i7C 12.0 V plus or minus 4 percent")
    if rail is None:
        rep.add("voltage.5v", "5 V rail meter", "INCOMPLETE", None,
                "%s to %s V" % (RAIL5_LO_V, RAIL5_HI_V), "netlist domain 5V")
    else:
        rep.gate("voltage.5v", "5 V regulator output",
                 RAIL5_LO_V <= rail <= RAIL5_HI_V, rail, "%s to %s V" % (RAIL5_LO_V, RAIL5_HI_V),
                 "cited, netlist domain 5V, Pololu D30V30F5 4 percent")
    bad = []
    for sid in hw.servo_ids():
        try:
            raw = hw.read_reg(sid, "present_voltage")
        except KeyError:
            bad.append({"id": sid, "error": "no read"})
            continue
        volts = raw * sts3215.VOLT_LSB
        if volts < BEC_LO_V or volts > BEC_HI_V:
            bad.append({"id": sid, "raw": raw, "volts": volts})
    rep.gate("voltage.servos", "each present voltage is inside the rail window",
             not bad, bad or "14 in window", "%s to %s V" % (BEC_LO_V, BEC_HI_V),
             "cited, Present Voltage 0.1 V per LSB (SOFTWARE.md section 3) and SERVO_12V0")
    return rep


def step_camera(hw, rep):
    frame = hw.camera_frame()
    if frame is None:
        present = os.path.exists("/dev/video0")
        rep.add("camera.frame", "camera frame", "INCOMPLETE",
                "device node only" if present else "no frame",
                "non-empty frame", "netlist CSI_LINK; this path did not read a frame")
    else:
        rep.gate("camera.frame", "camera returned a frame", len(frame) > 0,
                 len(frame), "non-empty", "netlist CSI_LINK, Camera Module 3")
    rep.add("camera.rate", "frame rate on this duck", "INFO", "BLOCKER",
            "not published", "SOFTWARE.md section 11")
    return rep


def step_imu(hw, rep, n):
    samples = hw.imu_samples(n)
    if len(samples) < n:
        rep.add("imu.count", "still reads", "INCOMPLETE", len(samples), n, "TEST_PLAN 10.1")
        return rep
    acc = [s[1] for s in samples]
    gyro = [s[0] for s in samples]
    med_a = tuple(_median([a[i] for a in acc]) for i in range(3))
    med_g = tuple(_median([g[i] for g in gyro]) for i in range(3))
    glitches = 0
    for g, a in samples:
        if any(abs(a[i] - med_a[i]) > ACC_LIM for i in range(3)):
            glitches += 1
        elif any(abs(g[i] - med_g[i]) > GYRO_LIM for i in range(3)):
            glitches += 1
    rep.gate("imu.glitch", "no still-read jump", glitches == 0, glitches, "0",
             "TEST_PLAN 10.1, imu_check.py gates 0.5 m/s^2 and 0.1 rad/s")
    level = med_a[2] > LEVEL_Z and abs(med_a[0]) < LEVEL_XY and abs(med_a[1]) < LEVEL_XY
    rep.gate("imu.level", "level reading is +z up", level,
             {"accel": [round(v, 3) for v in med_a]},
             "z > 8, |x| and |y| < 1.5 m/s^2", "SOFTWARE.md section 4, imu_check.py level step")
    return rep


def step_eyes(hw, rep):
    log = hw.eye_cycle()
    if not log:
        rep.add("eyes.pins", "left GPIO24 and right GPIO23", "INCOMPLETE", None,
                "GPIO24 and GPIO23", "live GPIO was not driven; use --mock or RPi.GPIO")
        return rep
    pins = {gpio for gpio, _level in log}
    want = {PINS["eye_left"], PINS["eye_right"]}
    rep.gate("eyes.pins", "left GPIO24 and right GPIO23", pins == want, sorted(pins), sorted(want),
             "cited, netlist EYE_L and EYE_R")
    high = {gpio for gpio, level in log if level}
    low = {gpio for gpio, level in log if not level}
    rep.gate("eyes.cycle", "each eye went on and then off", want <= high and want <= low,
             log, "on then off", "read-back of the day-one driver, not a brightness")
    rep.add("eyes.current", "bead current at 3.3 V through 100 ohm", "INFO", "BLOCKER",
            "no warm-white datasheet", "SOFTWARE.md section 12")
    return rep


def step_antennas(hw, rep, chip_root):
    import hw_pwm
    try:
        _antennas(hw, rep, chip_root, hw_pwm)
    except OSError as exc:
        rep.add("antennas.pulse", "hardware PWM chip", "FAIL", str(exc),
                "/sys/class/pwm/pwmchip0",
                "live mode writes that device; a folder of files is not a pass")
    return rep


def _antennas(hw, rep, chip_root, hw_pwm):
    chip = hw_pwm.Chip(chip_root)
    # Neutral, then both ends, then stop. Signs match antennas.py.
    plan = (("right", hw_pwm.RIGHT_GPIO, hw_pwm.RIGHT_SIGN),
            ("left", hw_pwm.LEFT_GPIO, hw_pwm.LEFT_SIGN))
    duties = []
    for side, gpio, sign in plan:
        out = hw_pwm.PWMOut(gpio, frequency=50, duty_cycle=hw_pwm.command_to_duty(0, sign), chip_root=chip_root)
        for command in (-1, 0, 1):
            out.duty_cycle = hw_pwm.command_to_duty(command, sign)
            ns = int(chip.read(hw_pwm.CHANNEL[gpio], "duty_cycle"))
            duties.append({"side": side, "command": command, "duty": out.duty_cycle, "ns": ns})
        out.deinit()
    span_ok = all(hw_pwm.DUTY_MIN <= row["duty"] <= hw_pwm.DUTY_MAX for row in duties)
    ns_ok = all(hw_pwm.duty_to_ns(hw_pwm.DUTY_MIN) <= row["ns"] <= hw_pwm.duty_to_ns(hw_pwm.DUTY_MAX) for row in duties)
    rep.gate("antennas.pulse", "every pulse is inside the antennas.py 1 ms to 2 ms clamp",
             span_ok and ns_ok, duties, "duty %s to %s" % (hw_pwm.DUTY_MIN, hw_pwm.DUTY_MAX),
             "cited, antennas.py value_to_duty_cycle and netlist PWM_3V3")
    period_ok = all(chip.read(i, "period") == str(hw_pwm.PERIOD_NS) for i in (0, 1))
    rep.gate("antennas.period", "both channels are 20 ms", period_ok,
             [chip.read(0, "period"), chip.read(1, "period")], str(hw_pwm.PERIOD_NS),
             "cited, 50 Hz")
    idle = chip.read(0, "enable") == "0" and chip.read(1, "enable") == "0"
    rep.gate("antennas.idle", "pulses stopped after the move", idle,
             [chip.read(0, "enable"), chip.read(1, "enable")], "enable 0",
             "PI_SETUP.md 4c")
    pins_ok = hw_pwm.CHANNEL[12] == 0 and hw_pwm.CHANNEL[13] == 1
    rep.gate("antennas.pins", "GPIO12 is PWM0 and GPIO13 is PWM1", pins_ok,
             hw_pwm.CHANNEL, "12 -> 0, 13 -> 1", "cited, netlist ANT_R and ANT_L")
    rep.add("antennas.runtime", "Runtime antennas.py", "INFO",
            "unchanged; overlay software/hw_pwm.py",
            "D6", "STATE.md question 10, software/ANTENNAS_PWM.md")
    rep.add("antennas.speed", "SG90 speed", "INFO", "BLOCKER", "not published",
            "software/personality/limits.py")
    return rep


def step_speaker(hw, rep):
    tone = hw.speaker_tone()
    if not tone.get("samples"):
        rep.add("speaker.clip", "tone samples", "INCOMPLETE", None, "a short tone",
                "live I2S playback is not wired in this script; use --mock")
        return rep
    full = (1 << 31) - 1
    peak = max(abs(s) for s in tone["samples"]) / full if tone["samples"] else 1.0
    rep.gate("speaker.clip", "tone peak under 99 percent of full scale", peak < CLIP,
             round(peak, 4), "under 0.99", "cited, TEST_PLAN 17.4")
    rep.gate("speaker.sd", "amp shutdown is low after the tone", tone["sd_after"] == 0,
             tone["sd_after"], "0", "cited, netlist AMP_SD, D48")
    rep.gate("speaker.rate", "sample rate is 48 kHz", tone["rate"] == 48000, tone["rate"], "48000",
             "cited, SOFTWARE.md section 11")
    rep.add("speaker.pins", "I2S and shutdown pins", "INFO",
            {"bclk": PINS["i2s_bclk"], "lrc": PINS["i2s_lrc"], "din": PINS["i2s_din"], "sd": PINS["amp_sd"]},
            "netlist", "cited, I2S_BCLK GPIO18, I2S_LRC GPIO19, I2S_DIN GPIO21, AMP_SD GPIO16")
    rep.add("speaker.spl", "sound pressure", "INFO", "not measured", "no gate",
            "a heard tone on the Pi is a person check; this step checks the samples")
    return rep


def step_mic(hw, rep):
    cap = hw.mic_capture()
    if not cap.get("left") and not cap.get("right"):
        rep.add("mic.slots", "left and right slots", "INCOMPLETE", None, "both slots",
                "live I2S capture is not wired in this script; use --mock")
        return rep
    full = (1 << 31) - 1
    left, right = cap["left"], cap["right"]
    both = any(left) and any(right)
    peak = 0.0
    for sample in list(left) + list(right):
        peak = max(peak, abs(sample) / full)
    rep.gate("mic.slots", "left and right slots both have a sample", both,
             {"left_peak": max(left) if left else None, "right_peak": max(right) if right else None},
             "both nonzero", "cited, netlist I2S_MIC, D47 two mics")
    rep.gate("mic.clip", "capture peak under 99 percent of full scale", peak < CLIP,
             round(peak, 4), "under 0.99", "cited, TEST_PLAN 17.4")
    rep.gate("mic.rate", "sample rate is 48 kHz", cap["rate"] == 48000, cap["rate"], "48000",
             "cited, SOFTWARE.md section 11")
    rep.add("mic.latency", "time from the mic to a sample", "INFO", "BLOCKER", "not published",
            "SOFTWARE.md section 11")
    return rep


def step_charge(hw, rep):
    pairs = hw.charge_pairs()
    if not pairs:
        rep.add("charge.open", "opposite pins when not on the cloth", "INCOMPLETE", None,
                "over 1e6 ohm", "pass --charge-ohm from the meter, or --mock")
        return rep
    shorted = {}
    for pair, ohms in pairs.items():
        if ohms is None or ohms < INSULATION_OHM:
            shorted["%s-%s" % pair] = ohms
    rep.gate("charge.open", "opposite pins read over 1 Mohm when not on the cloth",
             not shorted, shorted or "open", "over 1e6 ohm",
             "cited, TEST_PLAN section 2, different nets")
    rep.gate("charge.pins", "status GPIO5 and enable GPIO6",
             PINS["charge_stat"] == 5 and PINS["charge_en"] == 6,
             {"stat": PINS["charge_stat"], "en": PINS["charge_en"]},
             "GPIO5 pin 29, GPIO6 pin 31", "cited, netlist STAT_GPIO and PI_EN")
    rep.add("charge.loop", "pin-on-cloth ohms", "INFO", "BLOCKER",
            "no cited loop limit for the BQ24133 cloth path",
            "TEST_PLAN 20.1 was the earlier charger; D61 is not edited")
    rep.add("charge.state", "dock charge_state while no charger program is running", "INFO",
            "NONE", "NONE", "software/dock/autodock/autodock_base.py returns NONE")
    return rep


RUNNERS = {
    "bus": step_bus,
    "limits": step_limits,
    "voltage": step_voltage,
    "camera": step_camera,
    "eyes": step_eyes,
    "speaker": step_speaker,
    "mic": step_mic,
    "charge": step_charge,
}


def chip_root_for(mock, folder):
    """Mock runs use a directory of files. Live runs use the PWM device."""
    if mock:
        return folder / "pwmchip0"
    return None


def combine(reports):
    """FAIL wins over INCOMPLETE. Exit 1, then 2, then 0.

    Report.exit_code uses 1 for FAIL and 2 for INCOMPLETE, so a numeric
    maximum would hide a failure behind an incomplete step.
    """
    statuses = [rep.overall() for rep in reports]
    if "FAIL" in statuses:
        return 1, "FAIL"
    if "INCOMPLETE" in statuses:
        return 2, "INCOMPLETE"
    return 0, "PASS"


def run_steps(hw, folder, steps, imu_reads, chip_root):
    reports = []
    print("day one bench")
    print("hardware: %s" % hw.name)
    for name in steps:
        rep = report.Report("dayone_%s" % name, "day-one", "day one %s" % name)
        if name == "imu":
            step_imu(hw, rep, imu_reads)
        elif name == "antennas":
            try:
                step_antennas(hw, rep, chip_root)
            except OSError as exc:
                rep.add("antennas.pulse", "hardware PWM chip", "FAIL", str(exc),
                        "/sys/class/pwm/pwmchip0",
                        "live mode writes that device; a folder of files is not a pass")
        else:
            RUNNERS[name](hw, rep)
        _save(rep, folder)
        reports.append(rep)
    code, overall = combine(reports)
    summary = {
        "hardware": hw.name,
        "overall": overall,
        "steps": [{"step": r.script, "overall": r.overall()} for r in reports],
    }
    path = folder / ("dayone_summary_%s.json" % stamp())
    path.write_text(json.dumps(summary, indent=1) + "\n")
    print("OVERALL: %s" % overall)
    print("report: %s" % path)
    return code, summary


def _live(port, bec, rail, charge_ohm):
    """Real adapter. Meter values come from the flags. Sensors that need a Pi
    tool fall through to INCOMPLETE inside the step if the tool is missing.
    """
    from odm_bench import bus

    class Live:
        name = "live"

        def __init__(self):
            self.io = bus.open_pypot(port)
            self._bec = bec
            self._rail = rail

        def servo_ids(self):
            return bus.scan(self.io)

        def read_reg(self, sid, name):
            return bus.read_reg(self.io, sid, name)

        def meters(self):
            return {"bec_v": self._bec, "rail_5v": self._rail}

        def camera_frame(self):
            # A device node is not a frame. The mock path returns bytes.
            return None

        def imu_samples(self, n):
            return []

        def eye_cycle(self):
            return []

        def speaker_tone(self):
            return {"rate": 0, "samples": [], "sd_after": 1}

        def mic_capture(self):
            return {"rate": 0, "left": [], "right": []}

        def charge_pairs(self):
            if charge_ohm is None:
                return {}
            from mock_hw import CHARGE_PAIRS
            return {pair: charge_ohm for pair in CHARGE_PAIRS}

    return Live()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mock", action="store_true", help="mock hardware, no adapter and no Pi")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--out", default=None)
    ap.add_argument("--steps", default=",".join(STEPS))
    ap.add_argument("--imu-reads", type=int, default=50)
    ap.add_argument("--bec-volts", type=float, default=None, help="meter on the servo rail, volts")
    ap.add_argument("--rail-5v", type=float, default=None, help="meter on the 5 V rail, volts")
    ap.add_argument("--charge-ohm", type=float, default=None, help="meter, opposite charge pins, ohms")
    args = ap.parse_args(argv)
    steps = tuple(s.strip() for s in args.steps.split(",") if s.strip())
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        ap.error("unknown step %s" % ",".join(unknown))
    folder = out_dir(args.out, "dayone")
    chip = chip_root_for(args.mock, folder)
    if args.mock:
        from mock_hw import MockHardware
        hw = MockHardware()
        if args.bec_volts is not None:
            hw.bec_v = args.bec_volts
        if args.rail_5v is not None:
            hw.rail_5v = args.rail_5v
        if args.charge_ohm is not None:
            hw.charge_ohm = args.charge_ohm
    else:
        hw = _live(args.port, args.bec_volts, args.rail_5v, args.charge_ohm)
    code, _summary = run_steps(hw, folder, steps, args.imu_reads, chip)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print("FAIL  %s" % exc)
        sys.exit(1)
