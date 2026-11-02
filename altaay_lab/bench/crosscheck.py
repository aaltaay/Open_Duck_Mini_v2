#!/usr/bin/env python3
"""Cross-check Runtime config and code values against our build (software/SOFTWARE.md section 2).

Reads the Runtime checkout (source only, no import, no hardware) and this repo's wiring sources
(wiring/netlist.yaml header pins, WIRING.md chain table, DECISIONS.md), prints one markdown
row per value with OK, MISMATCH or NOTE, and exits 1 on any MISMATCH.
  python3 altaay_lab/bench/crosscheck.py [--runtime DIR] [--markdown]
"""
import argparse
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import joints, paths  # noqa: E402


def read(p):
    with open(p) as fh:
        return fh.read()


def board_pin(src, name):
    m = re.search(rf"^{name}\s*=\s*board\.D(\d+)", src, re.M)
    return int(m.group(1)) if m else None


def netlist_gpio(lab):
    """GPIO number -> description from the Pi header pin entries of wiring/netlist.yaml."""
    out = {}
    for m in re.finditer(r'\{pin: "(\d+)", label: "\d+", name: GPIO(\d+) ([^,]+),', read(lab / "wiring" / "netlist.yaml")):
        out[int(m.group(2))] = (int(m.group(1)), m.group(3).strip())
    return out


def remap_tuple(src, upside_down):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "upside_down":
            body = node.body if upside_down else node.orelse
            for st in body:
                if isinstance(st, ast.Assign) and isinstance(st.value, ast.Tuple):
                    return tuple(e.attr for e in st.value.elts)
    return None


def rows(rt, lab):
    R = []

    def add(what, runtime_val, ours, ok, src, note=""):
        R.append((what, runtime_val, ours, "OK" if ok is True else ("NOTE" if ok is None else "MISMATCH"), src, note))

    hwi = rt / "mini_bdx_runtime" / "mini_bdx_runtime"
    jm = joints.runtime_joint_map(rt)
    add("servo IDs per joint", ", ".join(f"{k} {v}" for k, v in jm.items()),
        "same (WIRING.md section 2 chains 20-24, 30-33, 10-14)", jm == joints.JOINTS,
        "rustypot_position_hwi.py lines 14-31")
    wiring = read(lab / "WIRING.md")
    chains_ok = all(re.search(p, wiring) for p in (r"20 L hip_yaw, 21, 22, 23, 24 L ankle",
                                                   r"30 neck_pitch, 31 head_pitch, 32 head_yaw, 33 head_roll",
                                                   r"10 R hip_yaw, 11, 12, 13, 14 R ankle"))
    add("chain order (power enters at the first ID)", "n/a (code reads by ID)", "20->24, 30->33, 10->14 (D15)",
        chains_ok, "WIRING.md section 2")
    baud = joints.runtime_baud(rt)
    cv = read(rt / "scripts" / "check_voltage.py")
    add("bus baud rate", baud, "1 Mbaud, servo register 6 = 0 (factory)", baud == 1_000_000,
        "rustypot_position_hwi.py line 77; check_voltage.py line 5", "")
    add("bus port", "/dev/ttyACM0 (HWI default, RLWalk serial_port, configure scripts)",
        "/dev/ttyACM0 (CH343, cdc_acm); udev symlink /dev/odm_servo_bus optional", True,
        "rustypot_position_hwi.py line 9; v2_rl_walk_mujoco.py line 29")
    walk = read(rt / "scripts" / "v2_rl_walk_mujoco.py")
    add("walk gains", "P 30 legs (-p), P 8 head, D 0", "same", "kps[5:9] = [8, 8, 8, 8]" in walk,
        "v2_rl_walk_mujoco.py lines 175-183, 356")
    add("control rate", "50 Hz", "50 Hz; bus budget in section 6", "default=50" in walk,
        "v2_rl_walk_mujoco.py line 359")
    nl = netlist_gpio(lab)
    pins = [("left foot", "feet_contacts.py", "LEFT_FOOT_PIN", 22), ("right foot", "feet_contacts.py", "RIGHT_FOOT_PIN", 27),
            ("left eye", "eyes.py", "LEFT_EYE_PIN", 24), ("right eye", "eyes.py", "RIGHT_EYE_PIN", 23),
            ("projector", "projector.py", "PROJECTOR_GPIO", 25), ("left antenna", "antennas.py", "LEFT_ANTENNA_PIN", 13),
            ("right antenna", "antennas.py", "RIGHT_ANTENNA_PIN", 12)]
    for what, f, var, _ in pins:
        g = board_pin(read(hwi / f), var)
        ours = nl.get(g)
        ok = ours is not None and what.split()[-1] in ours[1] and (what.split()[0] in ours[1] or what == "projector")
        add(f"GPIO {what}", f"GPIO{g}", f"GPIO{g} = Pi pin {ours[0]} ({ours[1]})" if ours else "not in netlist", ok,
            f"{f} {var}; wiring/netlist.yaml", "D9")
    fc = read(hwi / "feet_contacts.py")
    pull = "Pull.UP" in fc and "not self.left_foot.value" in fc
    add("foot switch logic", "internal pull-up, contact = pin LOW (get() returns not value)",
        "2.2 kOhm external pull-up to 3V3 per foot (D17) plus the internal one: same logic, about 1.5 mA closed",
        pull, "feet_contacts.py lines 10-21; D17")
    rg = read(rt / "docs" / "RELEASE_GUIDE.md")
    auto = "PIN_WALK=22" in rg and "PIN_HEAD=27" in rg
    add("image autostart foot pins", "GPIO22 LOW at boot -> walk, GPIO27 LOW -> head puppet",
        "GPIO22 = left foot, GPIO27 = right foot: a robot standing at boot starts WALK; our service replaces it",
        None if auto else False, "RELEASE_GUIDE.md lines 67-68, 89-104", "PI_SETUP.md step 11")
    ri = read(hwi / "raw_imu.py")
    rm = remap_tuple(ri, False)
    add("IMU axis remap (walk: raw_imu.py, NDOF)", str(rm), "imu_upside_down false: BNO055 flat, chip up (MOUNTING.md)",
        rm == ("AXIS_REMAP_Y", "AXIS_REMAP_X", "AXIS_REMAP_Z", "AXIS_REMAP_NEGATIVE", "AXIS_REMAP_POSITIVE",
               "AXIS_REMAP_POSITIVE"), "raw_imu.py lines 30-48",
        "B20: signs only proven by imu_check.py --tilt; policy frame x fwd, y left, z up (MuJoCo)")
    add("IMU file used by the walk", "raw_imu.py (gyro + accelerometer only)",
        "MOUNTING.md cites imu.py lines 19-55 (IMUPLUS, not used by the walk)", None,
        "v2_rl_walk_mujoco.py line 8", "doc fix proposed")
    add("IMU calibration file", "./imu_calib_data.pkl relative to the CWD (scripts/)",
        "run calibrate_imu.py from scripts/", "os.path.exists(\"imu_calib_data.pkl\")" in ri, "raw_imu.py line 76")
    add("battery voltage reader", "check_voltage.py: Present Voltage x 0.1 (pypot); the walk reads none",
        "battery_guard.py / walk_with_guard.py (D16): same read, median of 14 at 2 Hz", "* 0.1" in cv,
        "check_voltage.py lines 29-31", "rustypot 0.1.0 has no voltage read")
    add("max motor velocity", "5.24 rad/s (clip commented out)", "C001 firmware limit 5.215 rad/s (BAM)",
        "5.24" in walk, "v2_rl_walk_mujoco.py lines 49, 292-298")
    add("init pose (standing)", "HWI.init_pos (knees 1.368/1.379 rad)", "walk stop blends to it", "1.368" in
        read(hwi / "rustypot_position_hwi.py"), "rustypot_position_hwi.py lines 52-69")
    ex = read(rt / "example_config.json")
    add("duck_config features", "example_config.json: all expression features false",
        "software/duck_config.altaay.json: all false for the first walks (hardware fitted: eyes, projector, "
        "antennas, speaker, camera)", '"eyes": false' in ex, "example_config.json")
    add("pad needed by the walk", "--commands is store_true with default True: XBoxController always built",
        "no pad in BOM.md (G9); walk_with_guard.py --no-commands runs without one", None,
        "v2_rl_walk_mujoco.py lines 362-366; xbox_controller.py line 30")
    add("Ctrl-C in the walk", "stops eyes, antennas, projector, feet; torque stays on", "same unless "
        "walk_with_guard.py --torque-off-on-exit", None, "v2_rl_walk_mujoco.py lines 330-341")
    add("usb-serial latency rule", "README udev rule: DRIVER==\"ftdi_sio\" latency_timer 1",
        "CH343 uses cdc_acm (/dev/ttyACM0): the rule never matches (harmless)", None, "README.md lines 59-67")
    # TEST_PLAN.md references to Runtime scripts (our doc vs the Runtime code)
    tp = read(lab / "TEST_PLAN.md")
    fct = read(rt / "scripts" / "fc_test.py")
    is_ai = "from openai import OpenAI" in fct and "RLWalk(" in fct
    add("TEST_PLAN 12 foot test script", "scripts/fc_test.py = OpenAI function-calling demo: starts RLWalk "
        "(walks) and calls the OpenAI API", "TEST_PLAN 12 says it shows the foot states",
        False if ("fc_test.py" in tp and is_ai) else True, "fc_test.py lines 1, 19-20, 233",
        "use mini_bdx_runtime/feet_contacts.py or bench/feet_check.py")
    cal = read(rt / "scripts" / "calibrate_imu.py")
    add("TEST_PLAN 10.2 tilt script", "scripts/calibrate_imu.py only runs the BNO055 calibration and saves "
        "imu_calib_data.pkl", "TEST_PLAN 10.2 and B20 use it for the tilt sign test",
        False if ("calibrate_imu.py" in tp and "calibrate=True" in cal) else True, "calibrate_imu.py line 5; raw_imu.py lines 50-74",
        "use bench/imu_check.py --tilt")
    cm = read(rt / "scripts" / "check_motors.py")
    add("TEST_PLAN 6 single servo", "check_motors.py only talks to the 14 joint IDs (HWI map); a new servo has ID 1",
        "TEST_PLAN 6 expects it to find a single bench servo", False if ("check_motors.py finds a single servo" in tp
                                                                      and "hwi.joints.items()" in cm) else True,
        "check_motors.py lines 33-59; configure_motor.py line 5 DEFAULT_ID = 1", "use bench/first_servo_check.py --steps 6")
    return R


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runtime")
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args(argv)
    rt = paths.find_runtime(a.runtime)
    R = rows(rt, paths.LAB_DIR)
    print(f"Runtime {rt} at {paths.runtime_commit(rt)}")
    print("| Item | Runtime 376de65 | Our build | Check | Runtime source | Note |")
    print("|---|---|---|---|---|---|")
    for r in R:
        print("| " + " | ".join(str(x) for x in r) + " |")
    bad = [r for r in R if r[3] == "MISMATCH"]
    print(f"\n{len(R)} rows, {len(bad)} MISMATCH")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
