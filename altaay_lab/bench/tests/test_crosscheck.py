"""Runtime source vs our build. Known mismatches are listed on purpose: when a lab doc is fixed
(proposed edits in the agent report), this test fails and the list must be updated."""
import crosscheck
from conftest import LAB, RUNTIME, needs_runtime
from odm_bench import joints

KNOWN_MISMATCH = {"TEST_PLAN 12 foot test script", "TEST_PLAN 10.2 tilt script", "TEST_PLAN 6 single servo"}


@needs_runtime
def test_crosscheck_rows():
    rows = crosscheck.rows(RUNTIME, LAB)
    bad = {r[0] for r in rows if r[3] == "MISMATCH"}
    assert bad == KNOWN_MISMATCH, bad
    ok = {r[0] for r in rows if r[3] == "OK"}
    for must in ("servo IDs per joint", "bus baud rate", "GPIO left foot", "GPIO right foot", "foot switch logic",
                 "IMU axis remap (walk: raw_imu.py, NDOF)", "battery voltage reader"):
        assert must in ok, must


@needs_runtime
def test_joint_map_and_baud_parse():
    assert joints.runtime_joint_map(RUNTIME) == joints.JOINTS
    assert joints.runtime_baud(RUNTIME) == joints.BAUD
