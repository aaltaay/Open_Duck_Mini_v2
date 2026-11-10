"""unit tests of the loop index bookkeeping of sit_cables.py and check_cables.py:
python3 -m pytest altaay_lab/twin/sit/test_sit_cables.py"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "cables3d"))
import route_cables as RC  # noqa: E402
import sit_cables as SC  # noqa: E402
import check_cables as CC  # noqa: E402

PAR = {"B": ("A", "j1"), "C": ("B", "j2")}         # A -j1- B -j2- C


class FakeScene:
    T0 = {k: np.eye(4) for k in "ABC"}


def pt(link, x):
    return {"link": link, "p": [float(x), 0.0, 0.0]}


def data_with(points, spans, joints, ties=None):
    lp = {"span": [spans[0][0], spans[-1][1]], "spans": [list(s) for s in spans], "joints": joints}
    if ties:
        lp["ties_at_mm"] = list(ties)
    return {"cables": [{"id": "X", "runs": [{"name": "main", "points": points, "service_loops": [lp]}]}]}


@pytest.fixture(autouse=True)
def rev():
    old = dict(RC.REV)
    RC.REV.clear()
    RC.REV.update({"j1": (-1, 1), "j2": (-1, 1)})
    yield
    RC.REV.clear()
    RC.REV.update(old)


def test_insert_before_the_crossing_moves_the_span_and_the_ties():
    d = data_with([pt("A", 0), pt("A", 10), pt("B", 20), pt("B", 30)], [[1, 2]], ["j1"], ties=[5.0, 25.0])
    SC.tag_points(d, FakeScene)
    r = d["cables"][0]["runs"][0]
    r["points"].insert(1, pt("A", 4))                    # a waypoint before the crossing (the neck lane's case)
    r["points"][1]["p"][1] = 3.0                           # off the line: the route grows there
    SC.remap_loops(d, PAR, FakeScene)
    lp = r["service_loops"][0]
    assert lp["spans"] == [[2, 3]] and lp["span"] == [2, 3]
    assert lp["ties_at_mm"][1] > 25.0                      # the far tie keeps its place on the cable: further along now
    assert "_i" not in r["points"][0] and "_acc" not in r


def test_jog_point_inside_the_crossing_keeps_the_pair_on_the_joint():
    d = data_with([pt("A", 0), pt("B", 10), pt("B", 20)], [[0, 1]], ["j1"])
    SC.tag_points(d, FakeScene)
    r = d["cables"][0]["runs"][0]
    r["points"].insert(1, pt("B", 5))                    # move_points' jog: on the far link, before its first point
    SC.remap_loops(d, PAR, FakeScene)
    assert r["service_loops"][0]["spans"] == [[0, 1]]    # A -> the jog point is the crossing now


def test_a_base_span_off_its_crossing_is_found_nearby():
    d = data_with([pt("A", 0), pt("A", 5), pt("A", 9), pt("B", 20)], [[1, 2]], ["j1"])   # the SP4 / SP5 base case
    SC.tag_points(d, FakeScene)
    log = {}
    SC.remap_loops(d, PAR, FakeScene, log)
    assert d["cables"][0]["runs"][0]["service_loops"][0]["spans"] == [[2, 3]]
    assert log["loop_spans_fixed"]


def test_a_span_with_no_crossing_nearby_stops_the_run():
    d = data_with([pt("A", x) for x in range(8)] + [pt("B", 20)], [[0, 1]], ["j1"])
    SC.tag_points(d, FakeScene)
    with pytest.raises(SystemExit):
        SC.remap_loops(d, PAR, FakeScene)


def test_check_loop_spans_flags_a_stationary_span():
    good = data_with([pt("A", 0), pt("B", 10), pt("C", 20)], [[0, 1], [1, 2]], ["j1", "j2"])
    assert CC.check_loop_spans(PAR, good) == []
    bad = data_with([pt("A", 0), pt("A", 5), pt("B", 10)], [[0, 1]], ["j1"])
    assert len(CC.check_loop_spans(PAR, bad)) == 1
