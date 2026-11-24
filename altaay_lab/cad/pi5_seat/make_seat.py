#!/usr/bin/env python3
"""Board seat for a Raspberry Pi 5 in the duck body. CAD check only.

Dimensions come from the official drawings named in the report. The script
writes a seat mesh, a fit report, and a picture. It does not edit the BOM.
"""

from __future__ import annotations

import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PRINT = os.path.join(ROOT, "print")

# Cited, RP-008347-DS-1, the mechanical drawing. Millimetres.
BOARD_X = 85.0
BOARD_Y = 56.0
HOLE_D = 2.7
HOLE_PITCH_X = 58.0
HOLE_INSET_X = 3.5
HOLE_PITCH_Y = 49.0
# Calc only: the drawing shows the 49 mm pitch on the 56 mm side.
HOLE_INSET_Y = (BOARD_Y - HOLE_PITCH_Y) / 2.0

# Cited, Active Cooler mechanical drawing. Height of the cooler body.
COOLER_H = 12.70
COOLER_X = 43.50
COOLER_Y = 42.50

# Seat plate. The pilot is the electronics rule in MOUNTING.md: 2.0 mm.
PLATE_T = 2.4
BOSS_H = 5.0
BOSS_D = 6.0
PILOT_D = 2.0
CLEAR_MM = 2.0

# CAD mass model cited in DECISIONS.md D66. Not a scale reading.
MASS_KG = 2.949
# Cited, Adafruit 5291 product weight, sim/mass_budget.py.
ZERO_KG = 0.010
# Head print bbox centre, used only as the old board's height band.
# The real Pi pose is the head mount. This z is the head shell centre.


def load_tris(path):
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 80)[0]
    kind = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    arr = np.frombuffer(data, dtype=kind, count=n, offset=84)
    return np.array(arr["v"], dtype=np.float64)


def tri_bounds(verts):
    return verts.min(axis=1), verts.max(axis=1)


SHELLS = (
    "body_middle_top.stl",
    "body_middle_bottom.stl",
    "body_front.stl",
    "body_back.stl",
    "trunk_top.stl",
    "head.stl",
)


def load_shells():
    out = {}
    for name in SHELLS:
        verts = load_tris(os.path.join(PRINT, name))
        tmin, tmax = tri_bounds(verts)
        flat = verts.reshape(-1, 3)
        out[name] = (verts, tmin, tmax, flat.min(axis=0), flat.max(axis=0))
    return out


def overlaps(shells, names, bmin, bmax):
    total = 0
    detail = {}
    for name in names:
        verts, tmin, tmax, _smin, _smax = shells[name]
        hit = np.all(tmax >= bmin, axis=1) & np.all(tmin <= bmax, axis=1)
        count = int(hit.sum())
        detail[name] = count
        total += count
    return total, detail


def clearance(shells, names, bmin, bmax, limit=8.0):
    """Largest margin, in 0.5 mm steps, that still misses every shell triangle."""
    best = 0.0
    pad = 0.0
    while pad <= limit + 1e-9:
        grown_min = bmin - pad
        grown_max = bmax + pad
        total, _ = overlaps(shells, names, grown_min, grown_max)
        if total:
            break
        best = pad
        pad += 0.5
    return best


def holes():
    xs = (HOLE_INSET_X, HOLE_INSET_X + HOLE_PITCH_X)
    ys = (HOLE_INSET_Y, HOLE_INSET_Y + HOLE_PITCH_Y)
    return [(x, y) for x in xs for y in ys]


def box_corners(origin, size):
    corners = []
    for ix in (0.0, 1.0):
        for iy in (0.0, 1.0):
            for iz in (0.0, 1.0):
                corners.append(origin + np.array([ix, iy, iz]) * size)
    return np.array(corners)


BODY = (
    "body_middle_top.stl",
    "body_middle_bottom.stl",
    "body_front.stl",
    "body_back.stl",
    "trunk_top.stl",
)


def search(shells):
    """Grid search. x is forward, y is left, z is up, print frame, mm.

    The USB end of the board is +x in the board frame, so the board's +x
    points toward the body front when the seat faces forward.
    """
    # Cooler on the component face, plate under the board. PCB thickness is
    # not a called-out dimension on the drawing, so it is not added.
    height = COOLER_H + PLATE_T
    best = None
    for swap in (False, True):
        size = np.array([BOARD_Y, BOARD_X, height] if swap else [BOARD_X, BOARD_Y, height])
        for x in np.arange(-70.0, 21.0, 5.0):
            for y in np.arange(-24.0, 25.0, 4.0):
                for z in np.arange(-78.0, -18.0, 4.0):
                    origin = np.array([x, y, z], dtype=float)
                    bmin = origin
                    bmax = origin + size
                    total, detail = overlaps(shells, BODY, bmin, bmax)
                    if total:
                        continue
                    gap = clearance(shells, BODY, bmin, bmax, limit=6.0)
                    if gap < CLEAR_MM:
                        continue
                    # Prefer forward (large x), then more clearance.
                    score = (float(x + size[0]), gap)
                    row = {
                        "swap": swap,
                        "origin_mm": [round(v, 2) for v in origin],
                        "size_mm": [round(v, 2) for v in size],
                        "clear_mm": gap,
                        "score": score,
                    }
                    if best is None or score > best["score"]:
                        best = row
    return best


def head_try(shells):
    """The current mount is in the head. Try the same outline there."""
    _verts, _tmin, _tmax, tmin, tmax = shells["head.stl"]
    height = COOLER_H + PLATE_T
    size = np.array([BOARD_X, BOARD_Y, height])
    # Head shell spans a wide, thin volume. Sit the box in the upper half.
    center = (tmin + tmax) / 2.0
    origin = np.array([
        center[0] - size[0] / 2.0,
        center[1] - size[1] / 2.0,
        tmax[2] - size[2] - 4.0,
    ])
    bmin = origin
    bmax = origin + size
    total, detail = overlaps(shells, ("head.stl",), bmin, bmax)
    return {
        "fits": total == 0,
        "triangle_hits": total,
        "by_shell": detail,
        "origin_mm": [round(float(v), 2) for v in origin],
        "size_mm": [round(float(v), 2) for v in size],
        "head_bbox_mm": {
            "min": [round(float(v), 1) for v in tmin],
            "max": [round(float(v), 1) for v in tmax],
            "size": [round(float(v), 1) for v in (tmax - tmin)],
        },
    }


def _box_tris(p0, p1):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    faces = [
        ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)),
        ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),
        ((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)),
        ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)),
        ((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)),
        ((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)),
    ]
    tris = []
    for a, b, c, d in faces:
        tris.append((a, b, c))
        tris.append((a, c, d))
    return tris


def write_stl(path, tris):
    buf = bytearray(b"pi5 seat" + b"\0" * 72)
    buf += struct.pack("<I", len(tris))
    for a, b, c in tris:
        buf += struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0)
    with open(path, "wb") as handle:
        handle.write(buf)


def seat_mesh(origin, swap):
    """Plate and four bosses in the print frame. Pilots are not solid."""
    ox, oy, oz = origin
    plate = np.array([BOARD_Y, BOARD_X] if swap else [BOARD_X, BOARD_Y])
    # 2 mm lip past the board on the long sides, none past the USB and MIPI edges
    # so those connectors stay reachable.
    margin = 2.0
    p0 = (ox - margin, oy - margin, oz)
    p1 = (ox + plate[0] + margin, oy + plate[1] + margin, oz + PLATE_T)
    tris = _box_tris(p0, p1)
    for hx, hy in holes():
        if swap:
            cx, cy = ox + hy, oy + hx
        else:
            cx, cy = ox + hx, oy + hy
        r = BOSS_D / 2.0
        tris.extend(_box_tris(
            (cx - r, cy - r, oz + PLATE_T),
            (cx + r, cy + r, oz + PLATE_T + BOSS_H),
        ))
    return tris


def com_shift(origin, size):
    """Fore-aft shift if the Zero's 10 g leaves the head and a new mass arrives.

    The head shell centre stands in for the old board. Pi 5 mass was not on
    the product page, so this is a sensitivity, calc only.
    """
    head = load_tris(os.path.join(PRINT, "head.stl"))
    hmin = head.reshape(-1, 3).min(axis=0)
    hmax = head.reshape(-1, 3).max(axis=0)
    old = (hmin + hmax) / 2.0
    new = origin + size / 2.0
    rows = []
    for grams in (40.0, 50.0, 60.0):
        m = grams / 1000.0
        mass = MASS_KG - ZERO_KG + m
        # Old whole-robot CoM x is taken as 0 in this sensitivity, which is
        # the ankle-axis band in MASS_BUDGET.md (0 to 1 mm ahead). The shift
        # is the change from removing the old mass and adding the new one.
        dx = (m * new[0] - ZERO_KG * old[0]) / mass
        dz = (m * new[2] - ZERO_KG * old[2]) / mass
        rows.append({
            "grams": grams,
            "label": "calc only, mass is a sensitivity because the Pi 5 weight was not read",
            "com_x_mm": round(float(dx), 3),
            "com_z_mm": round(float(dz), 3),
        })
    straight = float(np.linalg.norm(new - old))
    return {
        "old_head_centre_mm": [round(float(v), 1) for v in old],
        "new_centre_mm": [round(float(v), 1) for v in new],
        "straight_line_mm": round(straight, 1),
        "straight_line_label": "calc only, shell centres, not a routed cable",
        "mass_model_kg": MASS_KG,
        "mass_model_label": "CAD mass model, DECISIONS.md D66, not a scale",
        "rows": rows,
        "backward_margin_mm": "about 4 to 6",
        "backward_margin_label": "sim pass only, sim/ADDED_MASS_SIM.md table 7",
    }


def render(shells, origin, size, dest):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(8.2, 6.2))
    ax = fig.add_subplot(111, projection="3d")
    colors = {
        "body_middle_top.stl": "#9bb7d4",
        "body_middle_bottom.stl": "#7f9bb5",
        "body_front.stl": "#c5d4c0",
        "body_back.stl": "#d4c4b0",
        "trunk_top.stl": "#e0d28a",
    }
    for name, color in colors.items():
        verts = shells[name][0]
        step = max(1, len(verts) // 2500)
        sample = verts[::step]
        coll = Poly3DCollection(sample, alpha=0.12, facecolor=color, edgecolor="none")
        ax.add_collection3d(coll)
    board = box_corners(origin, size)
    # Draw the seat box edges.
    edges = [
        (0, 1), (0, 2), (0, 4), (3, 1), (3, 2), (3, 7),
        (5, 1), (5, 4), (5, 7), (6, 2), (6, 4), (6, 7),
    ]
    # corner order from box_corners is ix, iy, iz nested
    for a, b in edges:
        ax.plot(*board[[a, b]].T, color="#1a73e8", linewidth=2.0)
    ax.set_xlim(-110, 70)
    ax.set_ylim(-60, 60)
    ax.set_zlim(-110, 50)
    ax.set_xlabel("x forward, mm")
    ax.set_ylabel("y left, mm")
    ax.set_zlabel("z up, mm")
    ax.set_title("CAD check only: Pi 5 seat in the body")
    fig.tight_layout()
    fig.savefig(dest, dpi=110)
    plt.close(fig)


def main():
    shells = load_shells()
    head = head_try(shells)
    found = search(shells)
    if found is None:
        report = {"fits": False, "head": head, "label": "CAD check only"}
    else:
        origin = np.array(found["origin_mm"], dtype=float)
        size = np.array(found["size_mm"], dtype=float)
        tris = seat_mesh(origin, found["swap"])
        stl_path = os.path.join(HERE, "pi5_seat.stl")
        write_stl(stl_path, tris)
        png_path = os.path.join(HERE, "pi5_seat_in_body.png")
        render(shells, origin, size, png_path)
        com = com_shift(origin, size)
        # Camera is in the head. Straight line from the seat centre to the
        # head shell centre, calc only.
        report = {
            "label": "CAD check only",
            "fits_in_body": True,
            "clear_mm": found["clear_mm"],
            "clear_rule_mm": CLEAR_MM,
            "origin_mm": found["origin_mm"],
            "size_mm": found["size_mm"],
            "long_side_along_y": found["swap"],
            "head": head,
            "board_mm": [BOARD_X, BOARD_Y],
            "hole_d_mm": HOLE_D,
            "hole_pitch_mm": [HOLE_PITCH_X, HOLE_PITCH_Y],
            "hole_inset_x_mm": HOLE_INSET_X,
            "hole_inset_y_mm": HOLE_INSET_Y,
            "hole_inset_y_label": "calc only, (56 - 49) / 2",
            "holes_board_mm": [[round(a, 2), round(b, 2)] for a, b in holes()],
            "cooler_mm": [COOLER_X, COOLER_Y, COOLER_H],
            "plate_t_mm": PLATE_T,
            "boss_h_mm": BOSS_H,
            "pilot_d_mm": PILOT_D,
            "pcb_thickness": "BLOCKER, not a called-out dimension on the drawing",
            "com": com,
            "stl": "altaay_lab/cad/pi5_seat/pi5_seat.stl",
            "png": "altaay_lab/cad/pi5_seat/pi5_seat_in_body.png",
            "sources": {
                "board": "https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf",
                "cooler": "https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-mechanical-drawing.pdf",
            },
        }
    path = os.path.join(HERE, "seat_fit.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in report if k != "head"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
