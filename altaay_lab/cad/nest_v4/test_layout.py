"""No heading can bridge the v4 strip. Calc only."""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from altaay_lab.cad.nest_v4 import layout as LY


def test_strip_wider_than_diagonals():
    assert LY.strip_clears_plates()


def test_no_short_at_any_heading():
    # 5 deg steps, 4 mm depth steps, both plates, print 0.3 mm fat.
    shorts = 0
    yaw = 0.0
    while yaw < 2.0 * math.pi + 1e-9:
        tx = -0.70
        while tx < 0.40:
            kind, _, _ = LY.classify(tx, yaw, grow=LY.GROW)
            if kind == "short":
                shorts += 1
            tx += 0.004
        yaw += math.radians(5.0)
    assert shorts == 0, shorts


def test_room_window():
    kind, seat, bump = LY.classify(-0.27, math.pi, grow=LY.GROW)
    assert kind == "ok" and seat != bump


if __name__ == "__main__":
    test_strip_wider_than_diagonals()
    test_no_short_at_any_heading()
    test_room_window()
    print("ok")
