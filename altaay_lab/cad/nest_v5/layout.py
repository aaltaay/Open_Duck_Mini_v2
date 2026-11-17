"""Nest v5 pads. Calc only.

The same 40 mm plates as nest v4, repeated along depth. Each period is a
74 mm copper band and a 56 mm felt strip. 74 + 56 = 130 mm, the distance
between the plate centres (CAD check only). The empty gap between the
plates is 102 mm. A 102 mm pitch would leave a 46 mm band, which is tight
for a 32 mm plate once the heading smears it, so the pitch follows the
centres.

A 56 mm strip is wider than either plate's fat diagonal (0.3 mm of growth
on every edge). A plate shorter than the strip cannot reach both sides of
it, so it cannot touch two bands. That is the short-circuit proof.
"""
import math

SEAT = (-0.126, -0.094, -0.020, 0.020)
BUMP = (0.008, 0.032, -0.020, 0.020)
# Period is one band plus one strip. Polarity flips every period.
T = 0.130
W = 0.056
# World x where a period's band begins. Chosen so 28 of 32 recorded v4 sits
# land on opposite bands (calc only, those trunk positions).
PHASE = 0.115
# Same walking height as the other mats. Room edge extended so the plates
# are not off the copper at the depths this walk sits.
X0 = -0.550
X1 = 0.184
NEED_M = 0.004
GROW = 0.0003


def _diag(box, grow=GROW):
    dx = (box[1] - box[0]) + 2.0 * grow
    dy = (box[3] - box[2]) + 2.0 * grow
    return math.hypot(dx, dy)


def strip_clears_plates():
    return W > _diag(SEAT) and W > _diag(BUMP)


def _corners(tx, yaw, box, which, grow):
    x0, x1, y0, y1 = box
    if which == "seat":
        x1 += grow
    else:
        x0 -= grow
    y0 -= grow
    y1 += grow
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [tx + c * bx - s * by for bx in (x0, x1) for by in (y0, y1)]
    return min(pts), max(pts)


def slabs():
    """(name, x0, x1, kind) clipped to the mat. kind is plus, minus, or felt."""
    k0 = int(math.floor((X0 - PHASE) / T)) - 1
    k1 = int(math.ceil((X1 - PHASE) / T)) + 1
    out = []
    n_p = n_m = n_f = 0
    for k in range(k0, k1 + 1):
        start = PHASE + k * T
        band0, band1 = start, start + (T - W)
        felt0, felt1 = band1, start + T
        kind = "plus" if (k % 2 == 0) else "minus"
        for a, b, tag in ((band0, band1, kind), (felt0, felt1, "felt")):
            lo, hi = max(a, X0), min(b, X1)
            if hi - lo < 0.004:
                continue
            if tag == "plus":
                name = "pad_p%d" % n_p
                n_p += 1
            elif tag == "minus":
                name = "pad_m%d" % n_m
                n_m += 1
            else:
                name = "pad_felt%d" % n_f
                n_f += 1
            out.append((name, lo, hi, tag))
    return out


def _lengths(lo, hi):
    """Overlap length on plus and on minus, inside the mat only."""
    acc = {"plus": 0.0, "minus": 0.0}
    step = 0.0004
    x = lo
    while x <= hi + 1e-12:
        if X0 <= x <= X1:
            rel = x - PHASE
            k = math.floor(rel / T)
            p = rel - k * T
            if 0.0 <= p < (T - W):
                acc["plus" if (k % 2 == 0) else "minus"] += step
        x += step
    return acc


def _poles(lo, hi):
    acc = _lengths(lo, hi)
    return {k for k, v in acc.items() if v >= NEED_M}


def plate(tx, yaw, which, grow=0.0):
    """(pole or None, fraction of the plate's depth on that pole)."""
    box = SEAT if which == "seat" else BUMP
    lo, hi = _corners(tx, yaw, box, which, grow)
    span = max(hi - lo, 1e-6)
    acc = _lengths(lo, hi)
    hits = {k for k, v in acc.items() if v >= NEED_M}
    if len(hits) != 1:
        return None, 0.0
    pole = next(iter(hits))
    return pole, acc[pole] / span


def classify(tx, yaw, grow=0.0):
    def one(box, which):
        lo, hi = _corners(tx, yaw, box, which, grow)
        # A span shorter than every strip cannot touch two bands.
        return _poles(lo, hi), hi - lo
    sp, ss = one(SEAT, "seat")
    bp, bs = one(BUMP, "bump")
    if len(sp) > 1 or len(bp) > 1 or ss >= W or bs >= W:
        return "short", ",".join(sorted(sp)) or "none", ",".join(sorted(bp)) or "none"
    if len(sp) == 1 and len(bp) == 1 and sp != bp:
        return "ok", next(iter(sp)), next(iter(bp))
    return "miss", ",".join(sorted(sp)) or "none", ",".join(sorted(bp)) or "none"


def covered_fraction(yaw_max_deg=14, x0=-0.50, x1=-0.15, dx=0.002):
    """Share of depth and heading, both facings, that lands on opposite bands."""
    yaws = []
    step = 2.0
    a = -float(yaw_max_deg)
    while a <= float(yaw_max_deg) + 1e-9:
        yaws.append(math.pi + math.radians(a))
        yaws.append(math.radians(a))
        a += step
    ok = n = 0
    tx = x0
    while tx <= x1 + 1e-12:
        for yaw in yaws:
            n += 1
            if classify(tx, yaw, grow=GROW)[0] == "ok":
                ok += 1
        tx += dx
    return ok / float(n), ok, n
