"""unit tests of the section helpers of sit_stress.py: python3 -m pytest altaay_lab/twin/sit/test_sit_stress.py"""
import os
import sys

import numpy as np
from shapely.geometry import Point, Polygon, box

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sit_stress as SS  # noqa: E402


def test_rectangle_polar():
    b, h = 30.0, 10.0
    A, c, J, r = SS.area_polar(box(5.0, -2.0, 5.0 + b, -2.0 + h))     # off the origin: the centroid must be found
    assert abs(A - b * h) < 1e-9
    assert np.allclose(c, (20.0, 3.0))
    assert abs(J - b * h * (b * b + h * h) / 12.0) < 1e-6
    assert abs(r - np.hypot(b, h) / 2) < 1e-9


def test_square_from_corners_not_vertex_average():
    A, c, J, r = SS.area_polar(box(0, 0, 1, 1))
    assert abs(J - 1.0 / 6.0) < 1e-12                                   # the vertex average would give 0.5


def test_annulus_polar():
    ro, ri = 10.0, 4.0
    ring = Polygon(Point(3.0, 7.0).buffer(ro, 512).exterior.coords, [Point(3.0, 7.0).buffer(ri, 512).exterior.coords])
    A, c, J, r = SS.area_polar(ring)
    assert abs(A - np.pi * (ro ** 2 - ri ** 2)) / A < 1e-3
    assert np.allclose(c, (3.0, 7.0), atol=1e-6)
    assert abs(J - np.pi / 2 * (ro ** 4 - ri ** 4)) / J < 2e-3
    assert abs(r - ro) < 1e-3


def test_face_region_of_a_thin_plate():
    import trimesh
    m = trimesh.creation.box((20.0, 0.5, 8.0))                           # a 0.5 mm shell facing y
    A, c, J, r = SS.area_polar(SS.face_region(m, 1))
    assert abs(A - 160.0) < 1e-6
    assert abs(J - 160.0 * (400.0 + 64.0) / 12.0) < 1e-4
