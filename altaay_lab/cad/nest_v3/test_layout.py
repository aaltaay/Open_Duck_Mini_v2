"""Pad window for nest v3. Calc only. No MuJoCo."""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from altaay_lab.cad.nest_v3 import layout as LY


def test_centre_of_window_charges():
    tx = 0.5 * (LY.TX_LO + LY.TX_HI)
    kind, seat, bump = LY.classify(tx, math.pi, grow=0.0003)
    assert kind == "ok", (kind, seat, bump)
    assert seat != bump


def test_facing_wall_has_a_window():
    # A placed 180 deg sit near x = -0.12 is the one the probe charged.
    kind, seat, bump = LY.classify(-0.12, 0.0, grow=0.0003)
    assert kind == "ok", (kind, seat, bump)


def test_no_dash_in_note():
    text = open(os.path.join(os.path.dirname(__file__), "NEST_V3.md"), encoding="utf-8").read()
    assert "\u2014" not in text and "\u2013" not in text


if __name__ == "__main__":
    test_centre_of_window_charges()
    test_facing_wall_has_a_window()
    test_no_dash_in_note()
    print("ok")
