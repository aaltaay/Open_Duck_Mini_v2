"""Geometry of the belly inserts. No MuJoCo. Calc only."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from altaay_lab.twin.dock.camera import belly_contact as B


def test_inserts_do_not_bridge():
    rep = B.pick_report()
    for row in rep["rows"]:
        assert row["short"] == 0, row
    # Wider than the 5 mm gap would be a short. The fat print at 20 deg stays under it.
    assert rep["extent_20_print_high_mm"] < 5.0


def test_two_inserts_miss_the_gap():
    # A pair locked one period apart cannot cover the felt gap. Under 80 percent.
    nom = B.pick_report()["rows"][0]
    assert nom["ok_frac"] < 0.80
    assert nom["ok_frac"] > 0.50


def test_no_dash():
    path = os.path.join(os.path.dirname(__file__), "BELLY_CONTACT.md")
    text = open(path, encoding="utf-8").read()
    assert "\u2014" not in text and "\u2013" not in text


if __name__ == "__main__":
    test_inserts_do_not_bridge()
    test_two_inserts_miss_the_gap()
    test_no_dash()
    print("ok")
