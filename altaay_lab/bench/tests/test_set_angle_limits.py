"""set_angle_limits.py (D59): the angle limit registers from software/servo_limits.json and the zero offsets."""
import json
import math

import pytest

from conftest import BENCH, LAB, needs_libs

import importlib.util

_spec = importlib.util.spec_from_file_location("set_angle_limits", str(BENCH / "set_angle_limits.py"))
SAL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SAL)


def test_every_joint_has_registers_inside_the_wrap():
    rows = SAL.table(SAL.load_limits(), {}, zero_offsets=True)
    assert len(rows) == 14
    for r in rows:
        assert 0 < r["min_raw"] < r["max_raw"] < 4095, r
        # inward rounding: the register never allows a goal past the software limit
        assert 2048 + math.radians(r["soft_deg"][0]) * SAL.STEPS <= r["min_raw"]
        assert r["max_raw"] <= 2048 + math.radians(r["soft_deg"][1]) * SAL.STEPS


def test_knee_span_is_wider_than_the_stock_range_and_misses_the_wrap():
    L = SAL.load_limits()
    for jn in ("left_knee", "right_knee"):
        v = L[jn]
        assert v["soft_hi_deg"] == pytest.approx(v["hard_hi_deg"] - 3.0)
        assert v["hard_hi_deg"] >= 150.0 - 1e-6                    # the fold of D59
        lo, hi = SAL.registers(v["soft_lo_deg"], v["soft_hi_deg"], 0.0)
        assert hi > 2048 + math.radians(90.0) * SAL.STEPS          # past the stock 90 deg
        assert 4095 - hi > 300                                     # about 26 deg or more to the wrap


def test_offsets_shift_the_registers_and_a_wrapping_range_is_refused():
    v = SAL.load_limits()["left_knee"]
    lo0, hi0 = SAL.registers(v["soft_lo_deg"], v["soft_hi_deg"], 0.0)
    lo1, hi1 = SAL.registers(v["soft_lo_deg"], v["soft_hi_deg"], math.radians(5.0))
    assert lo1 - lo0 == pytest.approx(5.0 * 4096 / 360, abs=1)
    with pytest.raises(ValueError):
        SAL.registers(v["soft_lo_deg"], v["soft_hi_deg"], math.radians(40.0))


def test_soft_limits_are_three_degrees_inside_every_hard_stop():
    for jn, v in SAL.load_limits().items():
        assert v["soft_lo_deg"] == pytest.approx(v["hard_lo_deg"] + 3.0, abs=0.011), jn
        assert v["soft_hi_deg"] == pytest.approx(v["hard_hi_deg"] - 3.0, abs=0.011), jn


@needs_libs
def test_write_and_read_back_on_the_simulated_bus(make_bus, run):
    bus = make_bus(ids=[23, 13], reg85=0, volts=7.4)
    r, out = run("set_angle_limits.py", "--port", bus.path, "--write", "--ids", "23,13", "--zero-offsets")
    assert r.returncode == 0, r.stdout[-2000:]
    rows = {x["id"]: x for x in SAL.table(SAL.load_limits(), {}, [23, 13], zero_offsets=True)}
    for sid in (23, 13):
        m = bus.servos[sid].mem
        assert (m[9] | m[10] << 8, m[11] | m[12] << 8) == (rows[sid]["min_raw"], rows[sid]["max_raw"])
        assert m[55] == 1                                          # locked again
