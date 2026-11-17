"""Nest v3 pad geometry. Calc only. No sim.

The belly is split front to back, not left to right. The camera dock lands
with a wide scatter along the wall, and this walk does not side-step. It does
walk forward. So the insulating strip runs parallel to the wall, and the two
halves are the whole seat (rear) and the whole bumper (front).

Rear pad is the wall side of the strip (plus). Front pad is the room side
(minus). A duck that sits the other way round swaps the halves. The bridge
sorts the polarity.
"""
import math

# CAD, metres. sit_cad.json bbox.
SEAT = (-0.126, -0.094, -0.040, 0.040)   # x0, x1, y0, y1
BUMP = (0.008, 0.032, -0.030, 0.030)
# Strip centre and width. Pads are the sim slabs, not endless half-planes.
# Front pad is the room side, from the mat edge to the strip. Rear pad is
# the wall side, from the strip to the mat edge.
XS = -0.200
W = 0.024
PAD_X0 = -0.247
PAD_X1 = 0.184
# Trunk x that keeps both halves on the real pads at +/-14 deg, metal 0.3 mm
# fat, at least 4 mm of each half on its pad. Calc only. The earlier band
# (-292 to -197 mm) ran past the front pad; the bumper there is off the copper.
TX_LO = -0.235
TX_HI = -0.187
TX_CMD_LO = -0.230
TX_CMD_HI = -0.192
NEED_M = 0.004


def _span(tx, yaw, box, which, grow):
    x0, x1, y0, y1 = box
    if which == "seat":
        x1 = x1 + grow
    else:
        x0 = x0 - grow
    y0 = y0 - grow
    y1 = y1 + grow
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [tx + c * bx - s * by for bx in (x0, x1) for by in (y0, y1)]
    return min(pts), max(pts)


def _overlap(tx, yaw, box, which, grow, xs, w):
    lo, hi = _span(tx, yaw, box, which, grow)
    front_a, front_b = PAD_X0, xs - w / 2.0
    rear_a, rear_b = xs + w / 2.0, PAD_X1
    def hit(a, b):
        return max(0.0, min(hi, b) - max(lo, a))
    front = hit(front_a, front_b)
    rear = hit(rear_a, rear_b)
    if front > 0.001 and rear > 0.001:
        return "short", 0.0
    if rear >= NEED_M and front < 0.001:
        return "rear", rear
    if front >= NEED_M and rear < 0.001:
        return "front", front
    return "thin", max(front, rear)


def classify(tx, yaw, grow=0.0, xs=XS, w=W):
    """'ok', 'short', or 'miss'. Rear pad is plus, front pad is minus."""
    seat, _ = _overlap(tx, yaw, SEAT, "seat", grow, xs, w)
    bump, _ = _overlap(tx, yaw, BUMP, "bump", grow, xs, w)
    if seat == "short" or bump == "short":
        return "short", seat, bump
    if seat in ("rear", "front") and bump in ("rear", "front") and seat != bump:
        return "ok", seat, bump
    return "miss", seat, bump
