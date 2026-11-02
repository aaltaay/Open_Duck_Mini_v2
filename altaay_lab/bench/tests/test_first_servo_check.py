"""first_servo_check.py (TEST_PLAN 6 and 7) against one simulated factory servo."""
from conftest import item, last_report, needs_libs, needs_runtime


@needs_libs
def test_factory_servo_fails_register_85_and_speed(make_bus, run):
    bus = make_bus(ids=[1], reg85=50, volts=7.4)
    r, out = run("first_servo_check.py", "--port", bus.path, "--steps", "6,7.1,7.2", "--ids", "1,20", "--yes")
    rep = last_report(out, "first_servo")
    assert r.returncode == 1, r.stdout[-3000:]
    assert item(rep, "6.servo")["status"] == "PASS"
    assert item(rep, "7.1.r85")["status"] == "FAIL"               # factory 50, G1
    assert item(rep, "7.1.fw")["measured"] == "3.10"
    assert item(rep, "7.2.step")["status"] == "FAIL"              # ramp limited, like issue #48
    assert rep["data"]["factory_dump"]["registers"]["maximum_acceleration"] == 50


@needs_libs
@needs_runtime
def test_configure_with_runtime_script_then_pass(make_bus, run):
    """Runs the Runtime's own configure_motor.py. Its sync writes can be lost to pypot's output
    flush (SOFTWARE.md section 3); --fix-config writes the same values again and reads them back."""
    bus = make_bus(ids=[1], reg85=50, volts=7.4)
    r, out = run("first_servo_check.py", "--port", bus.path, "--configure", "20", "--fix-config", "--ids", "1,20", "--yes")
    rep = last_report(out, "first_servo")
    assert item(rep, "7.1.configure")["status"] == "PASS", item(rep, "7.1.configure")
    lost = [i for i in rep["items"] if i["item"] == "7.1.lost"]
    print("configure_motor.py writes lost on this run:", lost[0]["measured"] if lost else "none")
    assert item(rep, "7.1.r85")["status"] == "PASS"
    assert item(rep, "7.1.id")["measured"] == 20
    assert item(rep, "7.1.pid")["measured"] == [32, 0, 0]
    assert item(rep, "7.2.step")["status"] == "PASS", item(rep, "7.2.step")
    assert r.returncode == 0, r.stdout[-3000:]
    assert 20 in bus.servos and 1 not in bus.servos


@needs_libs
def test_thermal_hold_pass_fail_and_protection(make_bus, run):
    # 1.0 Nm: about 1.3 A, steady state 25 + 15 x 1.3^2 = 51 C < 70 - 10
    bus = make_bus(ids=[20], reg85=0, volts=7.2)
    s = bus.servos[20]
    s.ext_torque_nm, s.tau = 1.0, 1.0
    r, out = run("first_servo_check.py", "--port", bus.path, "--id", "20", "--steps", "7.3", "--thermal-seconds", "4",
                 "--thermal-period", "0.5", "--thermal-nm", "1.0", "--yes")
    rep = last_report(out, "first_servo")
    assert item(rep, "7.3.temp")["status"] == "PASS", r.stdout[-2000:]
    assert item(rep, "7.3.load")["status"] == "PASS"
    # 1.5 Nm (D2) with the factory protection current 2.0 A for 2 s: the servo unloads itself
    bus2 = make_bus(ids=[21], reg85=0, volts=7.2)
    bus2.servos[21].ext_torque_nm = 1.6
    r2, out2 = run("first_servo_check.py", "--port", bus2.path, "--id", "21", "--steps", "7.3",
                   "--thermal-seconds", "5", "--thermal-period", "0.5", "--yes")
    rep2 = last_report(out2, "first_servo")
    assert item(rep2, "7.3.hold")["status"] == "INCOMPLETE", r2.stdout[-2000:]
    assert r2.returncode == 2


@needs_libs
def test_full_id_scan_finds_the_one_servo(make_bus, run):
    bus = make_bus(ids=[7], reg85=0, volts=7.4)
    r, out = run("first_servo_check.py", "--port", bus.path, "--steps", "6", "--yes",
                 env={"ODM_PYPOT_TIMEOUT": "0.01"})
    rep = last_report(out, "first_servo")
    assert item(rep, "6.servo")["measured"] == [7]
    assert item(rep, "6.scan")["measured"] == 253
