"""imu_check.py (TEST_PLAN 10) with the Runtime raw_imu set-up on a byte-level fake BNO055."""
import json

import pytest

from conftest import item, last_report, needs_runtime


def _imu(run, *args, cfg=None):
    return run("imu_check.py", *args, "--yes", "--upside-down", "false",
               env={"ODM_FAKE_IMU": json.dumps(cfg or {})})


@needs_runtime
def test_clean_imu_passes_1000_reads(run):
    r, out = _imu(run, "--reads", "1000", "--rate", "1000")
    rep = last_report(out, "imu")
    assert r.returncode == 0, r.stdout[-2000:]
    assert item(rep, "10.1")["status"] == "PASS"
    assert item(rep, "10.cfg")["measured"]["axis_remap"] == [1, 0, 2, 1, 0, 0]   # Runtime (Y, X, Z; -, +, +)


@needs_runtime
def test_g2_bit_flip_glitches_fail(run):
    """G2: top bit of the first byte flipped on some reads (1.28 m/s^2 or 0.14 rad/s jumps)."""
    r, out = _imu(run, "--reads", "1000", "--rate", "1000", cfg={"glitch_every": 37})
    rep = last_report(out, "imu")
    assert r.returncode == 1
    meas = item(rep, "10.1")["measured"]
    assert meas.startswith("54 glitches") or meas.startswith("5"), meas
    assert item(rep, "10.1.fix")["status"] == "INFO"


@needs_runtime
def test_i2c_errors_fail(run):
    r, out = _imu(run, "--reads", "300", "--rate", "1000", cfg={"oserror_every": 50})
    rep = last_report(out, "imu")
    assert item(rep, "10.1")["status"] == "FAIL"


STEPS_OK = {
    "level": {},
    "nose_down": {"pitch_deg": 25},
    "right_down": {"roll_deg": 25},
    "pitch_motion": {"rate": [0, 1.0, 0]},
    "roll_motion": {"rate": [1.0, 0, 0]},
    "yaw_motion": {"rate": [0, 0, 1.0]},
}


@needs_runtime
@pytest.mark.parametrize("step", list(STEPS_OK))
def test_tilt_signs_runtime_mounting(run, step):
    r, out = _imu(run, "--tilt-step", step, "--seconds", "0.3", cfg=STEPS_OK[step])
    rep = last_report(out, "imu")
    assert item(rep, f"10.2.{step}")["status"] == "PASS", item(rep, f"10.2.{step}")


@needs_runtime
@pytest.mark.parametrize("mount,step", [("rot180z", "nose_down"), ("rot180z", "right_down"),
                                        ("flip_x", "level"), ("rot90z", "nose_down")])
def test_tilt_catches_a_wrong_mounting(run, mount, step):
    cfg = dict(STEPS_OK[step], mount=mount)
    r, out = _imu(run, "--tilt-step", step, "--seconds", "0.3", cfg=cfg)
    rep = last_report(out, "imu")
    assert item(rep, f"10.2.{step}")["status"] == "FAIL"


@needs_runtime
def test_upside_down_board_needs_imu_upside_down_true(run):
    cfg = {"mount": "flip_x", "pitch_deg": 25}
    r, out = run("imu_check.py", "--tilt-step", "nose_down", "--seconds", "0.3", "--yes", "--upside-down", "true",
                 env={"ODM_FAKE_IMU": json.dumps(cfg)})
    rep = last_report(out, "imu")
    assert item(rep, "10.2.nose_down")["status"] == "PASS"
    assert item(rep, "10.cfg")["measured"]["axis_remap"] == [1, 0, 2, 1, 1, 1]
