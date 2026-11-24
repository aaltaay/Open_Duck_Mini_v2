"""Day-one bench and the ear PWM overlay. No hardware and no Runtime.

Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/tests -v
"""

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
BENCH = os.path.join(LAB, "bench")
SOFT = os.path.join(LAB, "software")
sys.path.insert(0, BENCH)
sys.path.insert(0, SOFT)

import day_one  # noqa: E402
import hw_pwm  # noqa: E402
from mock_hw import MockBus, MockHardware  # noqa: E402


def _item(rep, name):
    for row in rep.items:
        if row["item"] == name:
            return row
    raise KeyError(name)


class MockBench(unittest.TestCase):
    def test_all_steps_pass_and_write_reports(self):
        hw = MockHardware()
        self.assertEqual(hw.name, "mock hardware")
        with tempfile.TemporaryDirectory() as tmp:
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                code, summary = day_one.run_steps(
                    hw, __import__("pathlib").Path(tmp), day_one.STEPS, 20, os.path.join(tmp, "pwm"))
            self.assertEqual(code, 0)
            self.assertEqual(summary["overall"], "PASS")
            self.assertEqual(summary["hardware"], "mock hardware")
            names = os.listdir(tmp)
            for step in day_one.STEPS:
                self.assertTrue(any(n.startswith("dayone_%s_" % step) for n in names), names)
            self.assertTrue(any(n.startswith("dayone_summary_") for n in names))

    def test_missing_servo_fails_the_bus_step(self):
        hw = MockHardware(bus=MockBus(ids=[20, 21, 22]))
        rep = day_one.report.Report("bus", "day-one", "bus")
        day_one.step_bus(hw, rep)
        self.assertEqual(rep.overall(), "FAIL")
        self.assertEqual(_item(rep, "bus.count")["status"], "FAIL")

    def test_old_7v2_rail_fails_the_12v_window(self):
        hw = MockHardware(bec_v=7.2)
        rep = day_one.report.Report("voltage", "day-one", "voltage")
        day_one.step_voltage(hw, rep)
        self.assertEqual(_item(rep, "voltage.bec")["status"], "FAIL")
        self.assertEqual(_item(rep, "voltage.bec")["measured"], 7.2)

    def test_limit_mismatch_fails(self):
        bus = MockBus()
        bus.servos[23]["min_angle_limit"] = 0
        bus.servos[23]["max_angle_limit"] = 4095
        hw = MockHardware(bus=bus)
        rep = day_one.report.Report("limits", "day-one", "limits")
        day_one.step_limits(hw, rep)
        self.assertEqual(_item(rep, "limits.registers")["status"], "FAIL")

    def test_shorted_charge_pins_fail(self):
        hw = MockHardware(charge_ohm=10)
        rep = day_one.report.Report("charge", "day-one", "charge")
        day_one.step_charge(hw, rep)
        self.assertEqual(_item(rep, "charge.open")["status"], "FAIL")

    def test_imu_glitch_fails(self):
        hw = MockHardware(imu_n_glitch=3)
        rep = day_one.report.Report("imu", "day-one", "imu")
        day_one.step_imu(hw, rep, 10)
        self.assertEqual(_item(rep, "imu.glitch")["status"], "FAIL")

    def test_cli_mock_prints_the_label(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, os.path.join(BENCH, "day_one.py"), "--mock", "--out", tmp, "--imu-reads", "8"],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("hardware: mock hardware", r.stdout)
        self.assertIn("OVERALL: PASS", r.stdout)
        self.assertIn("STEP dayone_bus PASS", r.stdout)


class ReviewFixes(unittest.TestCase):
    def test_fail_wins_over_incomplete(self):
        failed = day_one.report.Report("voltage", "day-one", "voltage")
        failed.add("voltage.bec", "rail", "FAIL", 7.2, "11.52 to 12.48 V")
        missing = day_one.report.Report("camera", "day-one", "camera")
        missing.add("camera.frame", "frame", "INCOMPLETE", None, "a frame")
        code, overall = day_one.combine([failed, missing])
        self.assertEqual((code, overall), (1, "FAIL"))

    def test_live_pwm_chip_is_not_a_folder_of_files(self):
        self.assertIsNone(day_one.chip_root_for(False, __import__("pathlib").Path("/tmp")))
        hw = MockHardware()
        rep = day_one.report.Report("antennas", "day-one", "antennas")
        day_one.step_antennas(hw, rep, None)
        self.assertEqual(rep.overall(), "FAIL")
        self.assertFalse(os.path.exists("/sys/class/pwm/pwmchip0"))

    def test_unreadable_sudoers_is_checked_through_priv(self):
        import stat
        import subprocess
        script = os.path.join(SOFT, "install_pi.sh")
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            install = ["bash", script, "--mock", "--prefix", tmp]
            first = subprocess.run(install, capture_output=True, text=True, check=False, env=env)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            sudoers = os.path.join(tmp, "etc", "sudoers.d", "odm-poweroff")
            os.chmod(sudoers, 0)
            helper = os.path.join(tmp, "asroot")
            with open(helper, "w", encoding="utf-8") as fh:
                fh.write(
                    "#!/bin/bash\n"
                    "dest=$1\n"
                    "shift\n"
                    "old=\n"
                    "if [ -e \"$dest\" ]; then old=$(stat -c %a \"$dest\"); chmod u+r \"$dest\"; fi\n"
                    "\"$@\"\n"
                    "rc=$?\n"
                    "if [ -n \"$old\" ]; then chmod \"$old\" \"$dest\"; fi\n"
                    "exit $rc\n"
                )
            os.chmod(helper, stat.S_IRWXU)
            env["ODM_PRIV_SH"] = helper
            second = subprocess.run(install, capture_output=True, text=True, check=False, env=env)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("poweroff sudoers", second.stdout)
            self.assertEqual(os.stat(sudoers).st_mode & 0o777, 0)


class EarPwm(unittest.TestCase):
    def test_commands_stay_inside_the_cited_clamp(self):
        for value in (-1, -0.5, 0, 0.5, 1):
            for sign in (hw_pwm.LEFT_SIGN, hw_pwm.RIGHT_SIGN):
                duty = hw_pwm.command_to_duty(value, sign)
                self.assertGreaterEqual(duty, hw_pwm.DUTY_MIN)
                self.assertLessEqual(duty, hw_pwm.DUTY_MAX)
                ns = hw_pwm.duty_to_ns(duty)
                self.assertGreaterEqual(ns, hw_pwm.duty_to_ns(hw_pwm.DUTY_MIN))
                self.assertLessEqual(ns, hw_pwm.duty_to_ns(hw_pwm.DUTY_MAX))
        # Cited antennas.py ends: -1 clamps up to 3277, +1 is 6553, 0 is 4915.
        self.assertEqual(hw_pwm.value_to_duty_cycle(-1), 3277)
        self.assertEqual(hw_pwm.value_to_duty_cycle(1), 6553)
        self.assertEqual(hw_pwm.value_to_duty_cycle(0), 4915)

    def test_overlay_writes_sysfs_and_then_idles(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = hw_pwm.PWMOut(12, frequency=50, duty_cycle=4915, chip_root=tmp)
            self.assertEqual(out.duty_cycle, 4915)
            chip = hw_pwm.Chip(tmp)
            self.assertEqual(chip.read(0, "period"), str(hw_pwm.PERIOD_NS))
            self.assertEqual(chip.read(0, "enable"), "1")
            self.assertEqual(int(chip.read(0, "duty_cycle")), hw_pwm.duty_to_ns(4915))
            out.deinit()
            self.assertEqual(chip.read(0, "enable"), "0")

    def test_sysfs_path_is_not_created(self):
        missing = "/sys/class/pwm/pwmchip0"
        if os.path.exists(missing):
            self.skipTest("this machine has a PWM chip")
        with self.assertRaises(FileNotFoundError):
            hw_pwm.Chip(missing).export(0)
        self.assertFalse(os.path.exists(missing))

    def test_refuses_a_duty_outside_the_clamp(self):
        with self.assertRaises(ValueError):
            hw_pwm.duty_to_ns(1000)
        with self.assertRaises(ValueError):
            hw_pwm.command_to_duty(1.1, 1)

    def test_patch_replaces_pwmio_without_a_runtime_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            module = type("pwmio", (), {})()

            class _Old:
                pass

            module.PWMOut = _Old
            hw_pwm.patch(module, chip_root=tmp)

            class Pin:
                def __init__(self, n):
                    self.id = n

            ear = module.PWMOut(Pin(13), frequency=50, duty_cycle=4915)
            self.assertEqual(ear.gpio, 13)
            ear.deinit()
            self.assertEqual(hw_pwm.Chip(tmp).read(1, "enable"), "0")


class InstallScript(unittest.TestCase):
    def test_mock_install_is_idempotent_and_checks(self):
        import subprocess
        script = os.path.join(SOFT, "install_pi.sh")
        with tempfile.TemporaryDirectory() as tmp:
            cmd = ["bash", script, "--mock", "--prefix", tmp]
            first = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("OVERALL: PASS", first.stdout)
            self.assertIn("installed", first.stdout)
            stamp = os.path.join(tmp, "var", "lib", "odm", "installed.json")
            with open(stamp) as fh:
                body = json.load(fh)
            self.assertEqual(body["components"], [
                "runtime", "policy", "personality", "dock", "knee_heat",
                "battery_guard", "walk_service", "antennas_overlay",
                "setup", "updates", "status_page", "owner_services",
            ])
            self.assertTrue(body["mock"])
            unit_path = os.path.join(tmp, "etc", "systemd", "system", "odm-walk-guard.service")
            with open(unit_path, encoding="utf-8") as fh:
                unit = fh.read()
            self.assertIn("--knee-heat", unit)
            self.assertIn("ODM_HW_PWM=1", unit)
            cfg_path = os.path.join(tmp, "boot", "firmware", "config.txt")
            with open(cfg_path, encoding="utf-8") as fh:
                cfg = fh.read()
            self.assertIn("dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4", cfg)
            self.assertIn("dtoverlay=i2c-gpio,bus=1", cfg)
            before = _tree(tmp)
            second = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("unchanged install tree", second.stdout)
            self.assertEqual(before, _tree(tmp))


def _tree(root):
    rows = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as fh:
                rows.append((os.path.relpath(path, root), fh.read()))
    return sorted(rows)


if __name__ == "__main__":
    unittest.main()
