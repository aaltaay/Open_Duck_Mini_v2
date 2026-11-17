"""Repeating bands: no heading can bridge a strip. Calc only."""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from altaay_lab.cad.nest_v5 import layout as LY


def test_strip_wider_than_diagonals():
    assert LY.strip_clears_plates()


def test_no_short_anywhere():
    shorts = 0
    yaw = 0.0
    while yaw < 2.0 * math.pi + 1e-9:
        tx = -0.80
        while tx < 0.30:
            kind, _, _ = LY.classify(tx, yaw, grow=LY.GROW)
            if kind == "short":
                shorts += 1
            tx += 0.008
        yaw += math.radians(10.0)
    assert shorts == 0, shorts


def test_coverage_beats_half():
    frac, ok, n = LY.covered_fraction()
    # 130 mm pitch, +/-14 deg, both facings, 0.3 mm fat. Calc only.
    assert frac > 0.60, (frac, ok, n)


def test_slabs_match_the_period():
    slabs = LY.slabs()
    assert slabs
    assert any(k == "plus" for *_, k in slabs)
    assert any(k == "minus" for *_, k in slabs)
    # No two copper slabs overlap, and a felt gap between opposite poles
    # is at least the strip width when both are fully on the mat.
    copper = [(a, b, k) for _, a, b, k in slabs if k != "felt"]
    copper.sort()
    for (a1, b1, k1), (a2, b2, k2) in zip(copper, copper[1:]):
        assert b1 <= a2 + 1e-9
        if k1 != k2 and a1 > LY.X0 + 0.001 and b2 < LY.X1 - 0.001:
            assert a2 - b1 >= LY.W - 0.002


if __name__ == "__main__":
    test_strip_wider_than_diagonals()
    test_no_short_anywhere()
    test_coverage_beats_half()
    test_slabs_match_the_period()
    frac, ok, n = LY.covered_fraction()
    print("ok", round(100 * frac, 1), ok, n)
