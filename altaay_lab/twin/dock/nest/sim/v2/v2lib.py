"""v2lib.py: helpers shared by the v2 scripts. sim pass only.
Imports the original harness (../nestlib.py, ../nest_run.py) read only. Nothing in the parent folder is changed."""
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
sys.path.insert(0, PARENT)
import nestlib as N  # noqa: E402

# sole extent seen from the trunk origin while walking (measured on the floor at 7.2 V, sim pass only):
# toe up to 41 mm ahead, heel up to 107 mm behind, outer sole edges 93 mm left and 111 mm right
TOE, HEEL, HALF_L, HALF_R = 0.041, 0.107, 0.093, 0.111


def sole_points(s):
    """world xy of the hull points of both soles (truth)"""
    dd = s.data
    out = []
    for g, V, bn in s.hull:
        if g in s.soles:
            out.append((V @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g])[:, :2])
    return out


def feet_state(s, margin=0.0):
    """truth, per foot: 'off' (whole sole off the mat), 'on' (whole sole on the mat, `margin` inside), else 'edge'"""
    st = []
    for P in sole_points(s):
        r = np.hypot(P[:, 0], P[:, 1])
        inside = (r < N.MAT_R - margin) & (P[:, 0] < N.WALL_X - N.MAT_BACK)
        # the archived edge is one 5 mm cell outside the upper felt. The stepped and tapered edges add a 20 mm tread,
        # so a sole on that tread is on the edge too. NEST_EDGE unset keeps the old test.
        extra = N.TREAD if os.environ.get("NEST_EDGE", "one") in ("steps", "taper") else 0.005
        outside = r > N.MAT_R + extra
        st.append("on" if inside.all() else "off" if outside.all() else "edge")
    return st


def edge_x(y):
    """x of the mat edge on the room side at lateral position y"""
    return -float(np.sqrt(max(N.MAT_R ** 2 - y * y, 0.0)))


def feet_on_by_pose(x, y, yaw, margin):
    """the controller's own test from a pose estimate: both heels at least `margin` inside the mat outline"""
    c, sn = np.cos(yaw), np.sin(yaw)
    for w in (HALF_L, -HALF_R):
        hx, hy = x - c * HEEL - sn * w, y - sn * HEEL + c * w
        if np.hypot(hx, hy) > N.MAT_R - margin:
            return False
    return True
