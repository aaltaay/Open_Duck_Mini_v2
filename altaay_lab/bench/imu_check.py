#!/usr/bin/env python3
"""BNO055 checks: 1000-read glitch test (TEST_PLAN.md 10.1) and the tilt sign test (10.2, B20).

Set-up is the Runtime's own: raw_imu.Imu(50, upside_down=<duck_config imu_upside_down>) from
mini_bdx_runtime/raw_imu.py (NDOF mode, axis remap (Y, X, Z) with signs (-, +, +), or
(-, -, -) upside down, calibration offsets from ./imu_calib_data.pkl in the Runtime scripts/
folder). Its reader thread is not started; this script reads the same two properties the
walk reads, imu.gyro and imu.acceleration (raw_imu.py lines 127 and 128), one by one.

10.1 glitch: robot still. --reads 1000 at --rate 50 Hz. A read is a glitch when an axis is
     more than 0.5 m/s^2 (accel) or 0.1 rad/s (gyro) from the median of all reads, or a read
     raises an error or returns None. The G2 failure (UPSTREAM_ISSUES.md, Pi hardware I2C clock
     stretching) flips the top bit of the first byte: 128 LSB = 1.28 m/s^2 or 0.14 rad/s, so
     both limits catch it; the BNO055 noise at rest is far below them. Pass: 0 glitches.
     On a glitch the report prints the software I2C fix (PI_SETUP.md step 4b).
10.2 tilt: signs the policy expects, from the MuJoCo model (imu site = trunk frame, x forward,
     y left, z up; checked with mj_inverse, SOFTWARE.md section 4):
       level             accel z > +8 m/s^2, |accel x|, |accel y| < 1.5
       nose_down (hold)  accel x < -2.5 m/s^2 (about 15 deg or more)
       right_down (hold) accel y > +2.5 m/s^2
       pitch_motion      tilt the nose down while it samples: gyro y peak > +0.5 rad/s
       roll_motion       roll the right side down while it samples: gyro x peak > +0.5 rad/s
       yaw_motion        turn left (counter-clockwise seen from above): gyro z peak > +0.5 rad/s
     --tilt runs all steps with prompts; --tilt-step NAME runs one (no prompt).
     If x and z are inverted together the board is flipped: try imu_upside_down true.
"""
import argparse
import os
import pickle  # noqa: F401  (raw_imu loads imu_calib_data.pkl itself)
import statistics
import sys
import time
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import paths, report  # noqa: E402

ACC_LIM, GYRO_LIM = 0.5, 0.1
STEPS = {
    "level": "robot level and still",
    "nose_down": "tilt the nose down 20 to 30 deg and hold it",
    "right_down": "tilt the right side down 20 to 30 deg and hold it",
    "pitch_motion": "during the sampling, tilt the nose down",
    "roll_motion": "during the sampling, roll the right side down",
    "yaw_motion": "during the sampling, turn the robot to its left (counter-clockwise from above)",
}


class _NoThread:
    def __init__(self, *a, **k):
        pass

    def start(self):
        pass


def open_runtime_imu(rt, upside_down):
    """raw_imu.Imu set-up, run from scripts/ (calibration file path), without its thread."""
    paths.use_runtime(rt)
    from mini_bdx_runtime import raw_imu  # noqa: E402
    cwd = os.getcwd()
    os.chdir(rt / "scripts")
    try:
        with mock.patch.object(raw_imu, "Thread", _NoThread):
            imu = raw_imu.Imu(50, upside_down=upside_down)
    finally:
        os.chdir(cwd)
    return imu.imu, os.path.exists(rt / "scripts" / "imu_calib_data.pkl")


def read_once(dev):
    g = dev.gyro
    a = dev.acceleration
    if g is None or a is None or None in g or None in a:
        raise ValueError(f"None in read: gyro {g} accel {a}")
    return tuple(g), tuple(a)


def sample(dev, n, rate):
    out, errs = [], []
    t0 = time.perf_counter()
    for k in range(n):
        try:
            out.append((time.perf_counter() - t0,) + read_once(dev))
        except Exception as e:  # noqa: BLE001 - every failed read counts
            errs.append((k, repr(e)))
        time.sleep(max(0.0, t0 + (k + 1) / rate - time.perf_counter()))
    return out, errs


def glitch_test(dev, rep, n, rate):
    reads, errs = sample(dev, n, rate)
    rep.add("10.1.reads", "reads done (errors)", "INFO", f"{len(reads)} ({len(errs)})")
    if not reads:
        rep.add("10.1", "no IMU read succeeded", "FAIL")
        return
    med_g = [statistics.median(r[1][k] for r in reads) for k in range(3)]
    med_a = [statistics.median(r[2][k] for r in reads) for k in range(3)]
    bad = []
    for r in reads:
        dg = max(abs(r[1][k] - med_g[k]) for k in range(3))
        da = max(abs(r[2][k] - med_a[k]) for k in range(3))
        if dg > GYRO_LIM or da > ACC_LIM:
            bad.append(dict(t=round(r[0], 3), gyro=[round(x, 3) for x in r[1]], accel=[round(x, 3) for x in r[2]]))
    spread_a = max(max(r[2][k] for r in reads) - min(r[2][k] for r in reads) for k in range(3))
    rep.add("10.1.median", "median gyro (rad/s) and accel (m/s^2)", "INFO",
            dict(gyro=[round(x, 4) for x in med_g], accel=[round(x, 3) for x in med_a]))
    norm = sum(x * x for x in med_a) ** 0.5
    rep.add("10.1.g", "gravity magnitude at rest", "PASS" if 9.3 <= norm <= 10.3 else "WARN", f"{norm:.2f} m/s^2",
            "9.81 +/- 0.5")
    rep.gate("10.1", f"{n} reads with the robot still: no read jumps", not bad and not errs,
             f"{len(bad)} glitches, {len(errs)} errors, accel spread {spread_a:.3f} m/s^2",
             f"0 (limits {ACC_LIM} m/s^2, {GYRO_LIM} rad/s from the median)", "TEST_PLAN 10.1, G2")
    rep.data["glitches"] = bad[:50]
    rep.data["errors"] = errs[:50]
    if bad or errs:
        rep.add("10.1.fix", "move the BNO055 to software I2C on the same pins: PI_SETUP.md step 4b "
                "(dtparam=i2c_arm=off, dtoverlay=i2c-gpio,bus=1,i2c_gpio_sda=2,i2c_gpio_scl=3), reboot, re-run",
                "INFO", None, None, "UPSTREAM_ISSUES.md G2")


def tilt_step(dev, rep, name, seconds, rate):
    reads, errs = sample(dev, int(seconds * rate), rate)
    if not reads:
        rep.add(f"10.2.{name}", f"{name}: no reads", "FAIL", len(errs))
        return
    ax = [statistics.median(r[2][k] for r in reads) for k in range(3)]
    gx = [max((r[1][k] for r in reads), key=abs) for k in range(3)]
    meas = dict(accel=[round(x, 2) for x in ax], gyro_peak=[round(x, 2) for x in gx])
    if name == "level":
        ok = ax[2] > 8.0 and abs(ax[0]) < 1.5 and abs(ax[1]) < 1.5
        lim = "accel z > 8, |x| and |y| < 1.5 m/s^2"
    elif name == "nose_down":
        ok, lim = ax[0] < -2.5, "accel x < -2.5 m/s^2"
    elif name == "right_down":
        ok, lim = ax[1] > 2.5, "accel y > +2.5 m/s^2"
    elif name == "pitch_motion":
        ok, lim = gx[1] > 0.5, "gyro y peak > +0.5 rad/s"
    elif name == "roll_motion":
        ok, lim = gx[0] > 0.5, "gyro x peak > +0.5 rad/s"
    else:
        ok, lim = gx[2] > 0.5, "gyro z peak > +0.5 rad/s"
    rep.gate(f"10.2.{name}", STEPS[name], ok, meas, lim, "MuJoCo imu site, SOFTWARE.md section 4")
    return ax, gx


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group()
    m.add_argument("--glitch", action="store_true", help="10.1 (default)")
    m.add_argument("--tilt", action="store_true", help="10.2, all steps with prompts")
    m.add_argument("--tilt-step", choices=list(STEPS), help="10.2, one step, no prompt")
    ap.add_argument("--reads", type=int, default=1000)
    ap.add_argument("--rate", type=float, default=50.0, help="reads per second (walk rate 50)")
    ap.add_argument("--seconds", type=float, default=2.0, help="tilt step sampling time")
    ap.add_argument("--upside-down", choices=("auto", "true", "false"), default="auto",
                    help="auto: imu_upside_down from --duck_config_path")
    ap.add_argument("--duck_config_path", default=os.path.expanduser("~/duck_config.json"))
    ap.add_argument("--runtime")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rt = paths.find_runtime(a.runtime)
    up = a.upside_down
    if up == "auto":
        try:
            import json
            up = bool(json.load(open(a.duck_config_path)).get("imu_upside_down", False))
        except (OSError, ValueError):
            up = False
    else:
        up = up == "true"
    sect = "10.2" if (a.tilt or a.tilt_step) else "10.1"
    rep = report.Report("imu_check", sect, "BNO055 tilt signs" if sect == "10.2" else "BNO055 1000-read glitch test")
    dev, calib = open_runtime_imu(rt, up)
    rep.add("10.cfg", "Runtime raw_imu set-up", "INFO",
            dict(upside_down=up, axis_remap=tuple(dev.axis_remap), mode=dev.mode, calib_file=calib))
    if not calib:
        rep.add("10.calib", "imu_calib_data.pkl not in Runtime scripts/ (run calibrate_imu.py from scripts/)",
                "WARN", None, None, "raw_imu.py lines 76 to 87")
    if a.tilt_step:
        tilt_step(dev, rep, a.tilt_step, a.seconds, a.rate)
    elif a.tilt:
        for name, text in STEPS.items():
            if not report.confirm(f"{name}: {text}. Ready?", a.yes):
                rep.add(f"10.2.{name}", "skipped", "INCOMPLETE")
                continue
            tilt_step(dev, rep, name, a.seconds, a.rate)
    else:
        if report.confirm("Robot still (on the bench or hanging, not touched)?", a.yes):
            glitch_test(dev, rep, a.reads, a.rate)
        else:
            rep.add("10.1", "not run (no confirmation)", "INCOMPLETE")
    return rep.finish(paths.out_dir(a.out, "imu"))


if __name__ == "__main__":
    sys.exit(main())
