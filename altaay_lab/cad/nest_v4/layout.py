"""Nest v4 pads. Calc only.

The plates are the full depth of the seat and the bumper, and 40 mm wide.
A 56 mm felt strip is wider than either plate's diagonal, including 0.3 mm
of print growth on every edge, so one half cannot touch both pads at any
heading. Rear pad is plus (wall side). Front pad is minus (room side).
"""
import math

# Metal rectangles in the body, metres. x0, x1, y0, y1.
# Inner edges stay on the CAD gap (seat front -94 mm, bumper back +8 mm).
SEAT = (-0.126, -0.094, -0.020, 0.020)
BUMP = (0.008, 0.032, -0.020, 0.020)
XS = -0.230
W = 0.056
# Trunk x for a room-facing sit, +/-14 deg, metal 0.3 mm fat, 4 mm on the pad.
# The band covers the depth this walk actually sits at after the turn.
TX_LO = -0.324
TX_HI = -0.231
TX_CMD_LO = -0.310
TX_CMD_HI = -0.245
NEED_M = 0.004
GROW = 0.0003


def _diag(box, grow=GROW):
    dx = (box[1] - box[0]) + 2.0 * grow
    dy = (box[3] - box[2]) + 2.0 * grow
    return math.hypot(dx, dy)


def _corners(tx, yaw, box, which, grow):
    x0, x1, y0, y1 = box
    if which == "seat":
        x1 += grow
    else:
        x0 -= grow
    y0 -= grow
    y1 += grow
    c, s = math.cos(yaw), math.sin(yaw)
    pts = []
    for bx in (x0, x1):
        for by in (y0, y1):
            pts.append(tx + c * bx - s * by)
    return min(pts), max(pts)


def _one(tx, yaw, box, which, grow=GROW, xs=XS, w=W, need=NEED_M):
    lo, hi = _corners(tx, yaw, box, which, grow)
    if lo < xs - w / 2.0 and hi > xs + w / 2.0:
        return "short", hi - lo
    rear = max(0.0, hi - max(lo, xs + w / 2.0))
    front = max(0.0, min(hi, xs - w / 2.0) - lo)
    if rear >= need and front < 0.001:
        return "rear", rear
    if front >= need and rear < 0.001:
        return "front", front
    return "thin", max(rear, front)


def classify(tx, yaw, grow=0.0, xs=XS, w=W):
    seat, _ = _one(tx, yaw, SEAT, "seat", grow, xs, w)
    bump, _ = _one(tx, yaw, BUMP, "bump", grow, xs, w)
    if seat == "short" or bump == "short":
        return "short", seat, bump
    if seat in ("rear", "front") and bump in ("rear", "front") and seat != bump:
        return "ok", seat, bump
    return "miss", seat, bump


def strip_clears_plates():
    """The strip is wider than either fat diagonal. Calc only."""
    return W > _diag(SEAT) and W > _diag(BUMP)
