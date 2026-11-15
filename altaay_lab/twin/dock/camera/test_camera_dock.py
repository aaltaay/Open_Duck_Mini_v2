"""Geometry checks for the camera dock. No MuJoCo. Calc only."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from altaay_lab.twin.dock.camera import camera_dock as CD


def test_centered_sit_meets():
    # Facing the room, seat centre on the sun. One well on each pole.
    s = CD.score_wells(CD.SEAT_X, 0.0, math.pi)
    assert s["contacts_meet"], s
    assert s["seat_offset_mm"] < 1.0


def test_far_sit_misses():
    s = CD.score_wells(-1.2, 0.4, math.pi)
    assert not s["contacts_meet"]
    # Past the foil in y. The stripe polarity repeats, so the field bound has to count.
    side = CD.score_wells(CD.SEAT_X, 0.5, math.pi)
    assert not side["contacts_meet"], side


def test_square_depth():
    fx, fy, cx, cy, hfov = CD.intrinsics()
    assert 39.0 < hfov < 43.0
    half = CD.MARK_M / 2.0
    obj = np.array([[half, half, 0.0], [-half, half, 0.0], [-half, -half, 0.0], [half, -half, 0.0]])
    t = np.array([0.03, -0.02, 1.15])
    r = np.eye(3)
    corners = []
    for p in obj:
        pc = r @ p + t
        corners.append((fx * pc[0] / pc[2] + cx, fy * pc[1] / pc[2] + cy))
    got = CD.solve_square(np.array(corners))
    assert got is not None
    rm, tt, err = got
    assert abs(tt[2] - 1.15) < 0.03
    assert err < 1.0
    assert abs(np.linalg.det(rm) - 1.0) < 1e-6


def test_no_dash():
    text = open(os.path.join(os.path.dirname(__file__), "CAMERA_DOCK.md"), encoding="utf-8").read()
    assert "\u2014" not in text and "\u2013" not in text


if __name__ == "__main__":
    test_centered_sit_meets()
    test_far_sit_misses()
    test_square_depth()
    test_no_dash()
    print("ok")
