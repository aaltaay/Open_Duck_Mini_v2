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
# Strip centre and width. The room-facing stop window is computed below.
XS = -0.200
W = 0.024
# Trunk x that keeps both halves on opposite pads at +/-14 deg, with the
# metal 0.3 mm fat and at least 8 mm of each half on its pad. Calc only.
TX_LO = -0.292
TX_HI = -0.197
# Sit when the camera's trunk depth is inside this band. It is the geometric
# window, pulled 8 mm in from the deep end so a small deep error still lands.
TX_CMD_LO = -0.284
TX_CMD_HI = -0.205
NEED_M = 0.008


def _overlap(tx, yaw, box, which, grow, xs, w):
    x0, x1, y0, y1 = box
    if which == "seat":
        x1 = x1 + grow
    else:
        x0 = x0 - grow
    c, s = math.cos(yaw), math.sin(yaw)
    votes = []
    for by in (y0, 0.0, y1):
        wxs = [tx + c * bx - s * by for bx in (x0, x1)]
        lo, hi = min(wxs), max(wxs)
        rear = hi - max(lo, xs + w / 2.0)
        front = min(hi, xs - w / 2.0) - lo
        if rear > 0.001 and front > 0.001:
            return "short", 0.0
        if rear >= front:
            votes.append(("rear", max(0.0, rear)))
        else:
            votes.append(("front", max(0.0, front)))
    pols = set(v[0] for v in votes)
    if len(pols) != 1:
        return "short", 0.0
    ov = min(v[1] for v in votes)
    if ov < NEED_M:
        return "thin", ov
    return votes[0][0], ov


def classify(tx, yaw, grow=0.0, xs=XS, w=W):
    """'ok', 'short', or 'miss'. Rear pad is plus, front pad is minus."""
    seat, _ = _overlap(tx, yaw, SEAT, "seat", grow, xs, w)
    bump, _ = _overlap(tx, yaw, BUMP, "bump", grow, xs, w)
    if seat == "short" or bump == "short":
        return "short", seat, bump
    if seat in ("rear", "front") and bump in ("rear", "front") and seat != bump:
        return "ok", seat, bump
    return "miss", seat, bump
