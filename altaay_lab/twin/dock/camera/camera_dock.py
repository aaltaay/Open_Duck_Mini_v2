#!/usr/bin/env python3
"""Camera-only dock on the nest v2 mat. Sim pass only.

The duck walks with the run D policy. Joystick commands are vx, vy, and yaw
rate. The nest pose in that loop comes from one rendered frame of the head
camera. The true pose is used only after the sit, to score the wells.

The camera is the standard Camera Module 3 (BOM E6). The field angles are the
product brief, June 2024, RP-008151-DS-1, page 5: 66 deg on the long sensor
axis and 41 deg on the short one. On this head the long axis is up and down
(altaay_lab/twin/camera/CAMERA_TWIN.md). The mount is the measured seat on
head_assembly (altaay_lab/twin/complete3d/camera_seat.json).

Two marks. An 80 mm black felt square with a gold-foil patch is on the wall
at the nest v2 card station (centre 350 mm up, on the centre line). The drawn
card is 40 mm. At a 1.5 m start that square is about 11 px wide on a 320-wide
frame of this lens (calc only), which is too small once blur is added. 80 mm
is the size this detector holds. A 120 mm square with a red felt patch stands
on the room side of the sun, so the turn ends with a mark still in frame.
Felt prices are in cad/nest_v2/BOM.md. The stripe pitch is unchanged.

Nothing here is a hardware dock. Contact resistance is still BLOCKER.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
POLICY_REL = "altaay_lab/problems/retrain_sts12/sts12_runD_policy.onnx"

# Camera Module 3 standard, brief page 5. Cited.
FOV_UP_DEG = 66.0
FOV_SIDE_DEG = 41.0
# Lens opening in the head_assembly frame, metres. CAD check only.
# camera_seat.json T_cam_link is the PCB front. The opening is 4.2 mm further
# along the lens axis (opening x 99.0 mm, PCB front x 94.8 mm).
CAM_POS = (0.02404, -0.0025, -0.05705)
# Image right, then image up, in the head_assembly frame. See CAMERA_TWIN.md.
CAM_XYAXES = (0.0, -1.0, 0.0, 1.0, 0.0, 0.0)

# Nest v2 frame, metres. Sun at the origin, wall at +x, room at smaller x.
WALL_X = 0.190
MARK_Z = 0.350
MARK_M = 0.080
MARK_FACE_X = WALL_X - 0.002
GOLD_UP = 0.014
# Second mark, room side of the sun, facing the room. The duck turns to it
# first, then backs toward the wall while this mark stays in frame. 120 mm
# so it is still about 30 px at the sit (calc only, 41 deg field, 400 px).
MARK2_X = -2.20
MARK2_Z = 0.28
MARK2_M = 0.120
SIT_X = -0.11
GOAL_RANGE = SIT_X - MARK2_X
# Foil field, nest_v2.py. Calc only there.
FIELD_X0, FIELD_X1 = -0.180, 0.180
PERIOD = 0.025
STRIPE = 0.020
WELLS_Y = (-0.024, -0.012, 0.0, 0.012, 0.024)
WELL_R = 0.0015
SEAT_X = -0.108
# Render size. Height / width matches tan(33 deg) / tan(20.5 deg), so a 66 deg
# vertical field gives a 41 deg horizontal field. Calc only.
IMG_W = 400
IMG_H = 695

# Joystick limits the run D task was trained with (lin_vel_x up to 0.40).
VX_MAX, VY_MAX, WZ_MAX = 0.22, 0.14, 0.80
LAT_S = 0.10
CTRL_DT = 0.02


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def intrinsics(w=IMG_W, h=IMG_H):
    """Pixels per radian from the brief's 66 deg up-down field. Calc only."""
    fy = (h / 2.0) / math.tan(math.radians(FOV_UP_DEG) / 2.0)
    hfov = 2.0 * math.atan(math.tan(math.radians(FOV_UP_DEG) / 2.0) * (w / float(h)))
    fx = (w / 2.0) / math.tan(hfov / 2.0)
    return fx, fy, (w - 1) / 2.0, (h - 1) / 2.0, math.degrees(hfov)


def band(y):
    """Conductor polarity at world y. Same rule as draw_flush.band. Calc only."""
    p = float(np.mod(y, PERIOD))
    if p >= STRIPE:
        return "G"
    k = int(math.floor(float(y) / PERIOD))
    return "P" if k % 2 == 0 else "M"


def well_world(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for ly in WELLS_Y:
        out.append((x + c * SEAT_X - s * ly, y + s * SEAT_X + c * ly))
    return out


def score_wells(x, y, yaw):
    """True pose in, contact geometry out. Scoring only. Sim pose, calc on the stripes."""
    wells = well_world(x, y, yaw)
    hits = []
    plus_m, minus_m = [], []
    for wx, wy in wells:
        labs = [band(wy - WELL_R), band(wy), band(wy + WELL_R)]
        # The whole 3 mm well, not only its centre, and not past the foil in y.
        on_field = (FIELD_X0 + WELL_R < wx < FIELD_X1 - WELL_R) and abs(wy) + WELL_R < 0.280
        if labs[0] == labs[1] == labs[2] and labs[0] in ("P", "M") and on_field:
            hits.append(labs[0])
            # clearance to the edge of this 20 mm conductor
            k = math.floor(wy / PERIOD)
            a = k * PERIOD
            b = a + STRIPE
            clear = min(wy - WELL_R - a, b - (wy + WELL_R)) * 1000.0
            (plus_m if labs[0] == "P" else minus_m).append(clear)
        elif "P" in labs and "M" in labs:
            hits.append("short")
        else:
            hits.append("miss")
    n_p = hits.count("P")
    n_m = hits.count("M")
    # The pair margin is the weaker of the best plus well and the best minus well.
    # A well that only grazes a stripe does not set this.
    pair = min(max(plus_m), max(minus_m)) if plus_m and minus_m else None
    c, s = math.cos(yaw), math.sin(yaw)
    seat = (x + c * SEAT_X, y + s * SEAT_X)
    sun = math.hypot(seat[0], seat[1]) * 1000.0
    yaw_err = abs(math.degrees(wrap(yaw - math.pi)))
    return dict(
        contacts_meet=bool(n_p >= 1 and n_m >= 1 and "short" not in hits),
        plus=n_p,
        minus=n_m,
        seat_offset_mm=round(sun, 1),
        seat_x_mm=round(seat[0] * 1000.0, 1),
        seat_y_mm=round(seat[1] * 1000.0, 1),
        yaw_err_deg=round(yaw_err, 1),
        stripe_margin_mm=round(pair, 2) if pair is not None else None,
        align_mm=round(sun, 1),
    )


# Samtec plating note, 23 Sep 2022: gold contacts, about 30 to 40 grams of
# normal force. 30 grams is the floor used here.
F_MIN_N = 0.030 * 9.80665
# Mroczkowski, Connector Supplier, 7 Apr 2009: clean gold can be a few
# milliohms under 10 grams when the contact is held still. Five milliohms is
# the middle of "a few" (assumption). The nest foil is copper tape, not gold.
# No gold-on-copper force curve was found, so this gold figure is used for
# that pair and marked as an assumption.
R_REF_OHM = 0.005
F_REF_N = 0.010 * 9.80665
# Dust and fuzz. Stated assumption, not a measurement. Multiplies the clean resistance.
DUST_DERATE = 5.0
# Both poles of 22 AWG, NEST_V2.md, calc only from the cited 52.96 mohm/m.
R_WIRE_OHM = 0.038
# BQ24133 board, parts.yaml, from the chip sheet. Nest supply 15 V, input
# window 4.5 V to 17 V, charge current 1.006 A.
V_NEST = 15.0
I_SET_A = 1.006
V_IN_MIN = 4.5
V_IN_MAX = 17.0


def r_of_force(fn):
    """Ohms for one well. None if the force is under the gold floor."""
    if fn < F_MIN_N:
        return None
    clean = R_REF_OHM * math.sqrt(F_REF_N / fn)
    return DUST_DERATE * clean


def _parallel(rs):
    if not rs:
        return None
    return 1.0 / sum(1.0 / r for r in rs)


def well_forces(sim, x, y, yaw):
    """Normal force, newtons, on each well from MuJoCo contacts. Sim pass only.

    A contact counts for a well when its point is inside 6 mm of that well.
    The 6 mm is the 3 mm well plus a 3 mm pad. Contacts on the feet, away
    from the wells, are not counted.
    """
    wells = well_world(x, y, yaw)
    forces = [0.0] * len(wells)
    mj = sim.mujoco
    for i in range(sim.data.ncon):
        con = sim.data.contact[i]
        fr = np.zeros(6)
        mj.mj_contactForce(sim.model, sim.data, i, fr)
        fn = float(fr[0])
        if fn <= 0.0:
            continue
        px, py = float(con.pos[0]), float(con.pos[1])
        for k, (wx, wy) in enumerate(wells):
            if (px - wx) ** 2 + (py - wy) ** 2 <= (0.006 ** 2):
                forces[k] += fn
    return forces


def score_charge(sim, x, y, yaw, geom):
    """Geometry plus force plus the charger window. Not a hardware charge."""
    forces = well_forces(sim, x, y, yaw) if sim is not None else [0.0] * 5
    wells = well_world(x, y, yaw)
    plus_r, minus_r = [], []
    rows = []
    for fn, (wx, wy) in zip(forces, wells):
        pol = band(wy)
        on = (FIELD_X0 + WELL_R < wx < FIELD_X1 - WELL_R) and abs(wy) + WELL_R < 0.280
        rr = r_of_force(fn) if on and pol in ("P", "M") else None
        if rr is not None and pol == "P":
            plus_r.append(rr)
        if rr is not None and pol == "M":
            minus_r.append(rr)
        rows.append(dict(n=round(fn, 3), pol=pol if on else "off", ohm=None if rr is None else round(rr, 4)))
    rp, rm = _parallel(plus_r), _parallel(minus_r)
    r_contact = None if rp is None or rm is None else rp + rm
    r_series = None if r_contact is None else r_contact + R_WIRE_OHM
    v_chip = None if r_series is None else V_NEST - I_SET_A * r_series
    charging = bool(
        geom
        and r_series is not None
        and V_IN_MIN <= v_chip <= V_IN_MAX
    )
    i_a = I_SET_A if charging else 0.0
    heat = None if r_contact is None else (i_a ** 2) * r_contact
    return dict(
        charging=charging,
        well_force_n=[round(f, 3) for f in forces],
        wells=rows,
        r_contact_ohm=None if r_contact is None else round(r_contact, 4),
        r_series_ohm=None if r_series is None else round(r_series, 4),
        v_charger=None if v_chip is None else round(v_chip, 3),
        i_charge_a=round(i_a, 3),
        heat_w=None if heat is None else round(heat, 4),
        f_min_n=round(F_MIN_N, 3),
    )


def _hull(pts):
    pts = np.unique(np.round(pts, 3), axis=0)
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1], float)


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    v = b - a
    n = np.linalg.norm(v) + 1e-9
    d = np.abs((pts[:, 0] - a[0]) * v[1] - (pts[:, 1] - a[1]) * v[0]) / n
    i = int(np.argmax(d))
    if d[i] <= eps:
        return np.stack([a, b])
    left = _rdp(pts[: i + 1], eps)
    right = _rdp(pts[i:], eps)
    return np.vstack([left[:-1], right])


def _quad(pts):
    h = _hull(pts)
    if len(h) < 4:
        return None
    for eps in (1.2, 2.0, 3.2, 5.0):
        closed = np.vstack([h, h[:1]])
        simp = _rdp(closed, eps)
        if len(simp) >= 2 and np.allclose(simp[0], simp[-1]):
            simp = simp[:-1]
        if len(simp) == 4:
            return simp
    # min-area rectangle fallback
    best = None
    for ang in np.linspace(0, math.pi / 2, 90, endpoint=False):
        ca, sa = math.cos(ang), math.sin(ang)
        u = pts[:, 0] * ca + pts[:, 1] * sa
        v = -pts[:, 0] * sa + pts[:, 1] * ca
        area = (u.max() - u.min()) * (v.max() - v.min())
        if best is None or area < best[0]:
            best = (area, ca, sa, u.min(), u.max(), v.min(), v.max())
    _, ca, sa, umin, umax, vmin, vmax = best
    corners = []
    for u, v in ((umin, vmin), (umax, vmin), (umax, vmax), (umin, vmax)):
        corners.append((u * ca - v * sa, u * sa + v * ca))
    return np.array(corners, float)


def _components(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(xs) > 20000:
        return []
    h, w = mask.shape
    parent = {}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    idx = -np.ones((h, w), np.int32)
    for n, (y, x) in enumerate(zip(ys, xs)):
        idx[y, x] = n
        parent[n] = n
    for n, (y, x) in enumerate(zip(ys, xs)):
        for dy in (0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx <= 0:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and idx[ny, nx] >= 0:
                    a, b = find(n), find(int(idx[ny, nx]))
                    if a != b:
                        parent[b] = a
    groups = {}
    for n in range(len(xs)):
        groups.setdefault(find(n), []).append(n)
    out = []
    for ids in groups.values():
        if len(ids) < 40:
            continue
        out.append((xs[ids].astype(float), ys[ids].astype(float)))
    return out


def detect(img):
    """Black square plus a coloured patch. Returns (corners, kind) or None.

    kind is "gold" for the wall card and "red" for the room-side card.
    Corners are TL TR BR BL.
    """
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    # Auto exposure. The module meters the frame; this scales the 95th
    # percentile to a mid white so a dim room does not hide the foil patch.
    # Sim pass only. The Camera Module 3 brief (RP-008151-DS-1) is the sensor,
    # and the exposure loop is the libcamera default on that module.
    scale = 210.0 / max(float(np.percentile(img, 95)), 15.0)
    img = np.clip(img.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    r = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 2].astype(np.int16)
    dark = (r < 55) & (g < 55) & (b < 55)
    best = None
    for xs, ys in _components(dark):
        w = xs.max() - xs.min() + 1
        h = ys.max() - ys.min() + 1
        if w < 10 or h < 10:
            continue
        aspect = w / float(h)
        if not 0.65 <= aspect <= 1.45:
            continue
        fill = len(xs) / float(w * h)
        if fill < 0.45:
            continue
        if xs.min() <= 1 or ys.min() <= 1 or xs.max() >= img.shape[1] - 2 or ys.max() >= img.shape[0] - 2:
            continue
        score = fill * min(w, h)
        if best is None or score > best[0]:
            best = (score, xs, ys)
    if best is None:
        return None
    _, xs, ys = best
    pts = np.stack([xs, ys], 1)
    quad = _quad(pts)
    if quad is None or len(quad) != 4:
        return None
    x0, x1 = xs.min() - 2, xs.max() + 2
    y0, y1 = ys.min() - 2, ys.max() + 2
    sub = (slice(int(y0), int(y1) + 1), slice(int(x0), int(x1) + 1))
    rr, gg, bb = r[sub], g[sub], b[sub]
    # Gold foil is yellow (R and G both high). The room patch is red (R well above G and B).
    # A bright red patch used to pass the old gold test once the room light lifted G.
    gold = (rr > 150) & (gg > 120) & (bb < 110) & (np.abs(rr.astype(int) - gg.astype(int)) < 55) & (gg > bb + 35)
    red = (rr > 120) & (rr > gg + 45) & (rr > bb + 45) & (gg < 150) & (bb < 130)
    n_red = int(red.sum())
    n_gold = int(gold.sum())
    # Gold wins a tie. A few red-looking pixels on the foil used to label the
    # wall card as the room mark, and the duck then turned the wrong way.
    if n_gold >= 6 and n_gold >= n_red:
        kind = "gold"
        gy, gx = np.where(gold)
    elif n_red >= 8 and n_red > n_gold:
        kind = "red"
        gy, gx = np.where(red)
    else:
        return None
    gcen = np.array([gx.mean() + x0, gy.mean() + y0])
    cen = pts.mean(0)
    rel = quad - cen
    order = np.argsort(np.arctan2(rel[:, 1], rel[:, 0]))
    quad = quad[order]
    mids = np.array([(quad[i] + quad[(i + 1) % 4]) / 2 for i in range(4)])
    i = int(np.argmin(np.linalg.norm(mids - gcen, axis=1)))
    quad = np.roll(quad, -i, axis=0)
    if quad[0, 0] > quad[1, 0]:
        quad = quad[[1, 0, 3, 2]]
    # gold belongs near the top edge, which is the smaller image row
    if gcen[1] > cen[1] + 2:
        quad = quad[[3, 2, 1, 0]]
        if quad[0, 0] > quad[1, 0]:
            quad = quad[[1, 0, 3, 2]]
    return quad, kind


def solve_square(corners, half=MARK_M / 2.0):
    """Planar homography of a known square. Returns R, t of the square in the
    OpenCV camera (x right, y down, z forward), or None."""
    fx, fy, cx, cy, _ = intrinsics()
    obj = np.array([[half, half, 0.0], [-half, half, 0.0], [-half, -half, 0.0], [half, -half, 0.0]])
    x = (corners[:, 0] - cx) / fx
    y = (corners[:, 1] - cy) / fy
    rows = []
    for k in range(4):
        rows.append([obj[k, 0], obj[k, 1], 1, 0, 0, 0, -x[k] * obj[k, 0], -x[k] * obj[k, 1], -x[k]])
        rows.append([0, 0, 0, obj[k, 0], obj[k, 1], 1, -y[k] * obj[k, 0], -y[k] * obj[k, 1], -y[k]])
    _, _, vt = np.linalg.svd(np.asarray(rows, float))
    h = vt[-1].reshape(3, 3)
    h1, h2, h3 = h[:, 0], h[:, 1], h[:, 2]
    nrm = np.linalg.norm(h1)
    if nrm < 1e-9:
        return None
    best = None
    for sign in (1.0, -1.0):
        r1 = sign * h1 / nrm
        r2 = sign * h2 / nrm
        r3 = np.cross(r1, r2)
        t = sign * h3 / nrm
        rm = np.stack([r1, r2, r3], 1)
        u, _, vt2 = np.linalg.svd(rm)
        rm = u @ vt2
        if np.linalg.det(rm) < 0:
            rm = u @ np.diag([1.0, 1.0, -1.0]) @ vt2
        z = (rm @ obj.T + t.reshape(3, 1))[2]
        if z.mean() < 0.12 or z.mean() > 3.5:
            continue
        pred = []
        for p in obj:
            pc = rm @ p + t
            if pc[2] <= 1e-4:
                pred = None
                break
            pred.append((fx * pc[0] / pc[2] + cx, fy * pc[1] / pc[2] + cy))
        if pred is None:
            continue
        err = float(np.mean(np.linalg.norm(np.array(pred) - corners, axis=1)))
        if best is None or err < best[0]:
            best = (err, rm, t)
    if best is None or best[0] > 6.0:
        return None
    return best[1], best[2], best[0]


def marker_in_mj(rm_cv, t_cv):
    """OpenCV pose to the MuJoCo camera frame (x right, y up, z backward)."""
    m = np.diag([1.0, -1.0, -1.0])
    return m @ rm_cv, m @ t_cv


def trunk_from_marker(rm_mj, t_mj, r_cam_trunk, p_cam_trunk):
    """Trunk x, y, yaw, z in the nest frame. Joint chain plus the image.

    r_cam_trunk maps camera vectors into the trunk. t_mj is the marker origin
    in the MuJoCo camera. The nest pose of the mark is the design, not a measurement.
    """
    r_mark_trunk = r_cam_trunk @ rm_mj
    p_mark_trunk = r_cam_trunk @ t_mj + p_cam_trunk
    # Right-handed. Marker X is wall +Y, Y is up, Z points into the wall (+X).
    # The camera looks at the -Z face. A +Y cross +Z check gives +X.
    r_nest_mark = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    p_mark_nest = np.array([MARK_FACE_X, 0.0, MARK_Z])
    r_mark_trunk_inv = r_mark_trunk.T
    p_trunk_mark = -r_mark_trunk_inv @ p_mark_trunk
    r_nest_trunk = r_nest_mark @ r_mark_trunk_inv
    p_trunk = p_mark_nest + r_nest_mark @ p_trunk_mark
    yaw = math.atan2(r_nest_trunk[1, 0], r_nest_trunk[0, 0])
    return float(p_trunk[0]), float(p_trunk[1]), float(yaw), float(p_trunk[2])


def degrade(img, rng, gain, blur):
    """Exposure, read noise, and a short box blur. The blur stands in for motion."""
    x = img.astype(np.float32) * float(gain)
    if blur:
        x[1:-1] = 0.2 * x[:-2] + 0.6 * x[1:-1] + 0.2 * x[2:]
    x += rng.normal(0.0, 3.0, x.shape)
    return np.clip(x, 0, 255).astype(np.uint8)


def draw_quad(img, quad):
    if quad is None:
        return img
    out = img.copy()
    h, w = out.shape[:2]
    pts = np.round(quad).astype(int)
    for i in range(4):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % 4]
        n = int(max(abs(x1 - x0), abs(y1 - y0), 1))
        for t in range(n + 1):
            x = int(x0 + (x1 - x0) * t / n)
            y = int(y0 + (y1 - y0) * t / n)
            if 0 <= x < w and 0 <= y < h:
                out[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (40, 220, 60)
    return out


def _resize(img, w, h):
    ys = (np.linspace(0, img.shape[0] - 1, h)).astype(int)
    xs = (np.linspace(0, img.shape[1] - 1, w)).astype(int)
    return img[ys][:, xs]


def policy_path():
    return os.environ.get("ODM_ONNX") or os.path.join(ROOT, POLICY_REL)


def _boot():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    pg = os.environ.get("ODM_PLAYGROUND")
    if not pg or not os.path.isdir(pg):
        raise SystemExit("Set ODM_PLAYGROUND to the shared lab gym checkout at b9be205")
    os.environ.setdefault("MUJOCO_GL", "egl")
    import sts12  # noqa: F401  12 V sheet and the 3S pack
    import em_twin as ET
    import current_budget as CB
    import servo_sts3215 as SV
    return ET, CB, SV


def _scene_dir(folder):
    """A copy of the walk xml with the head camera and the nest geoms."""
    dst = os.path.join(folder, "camera_dock")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for name in os.listdir(folder):
        if name.endswith(".xml"):
            shutil.copy(os.path.join(folder, name), os.path.join(dst, name))
    import xml.etree.ElementTree as ETREE
    robot = os.path.join(dst, "open_duck_mini_v2_backlash.xml")
    tree = ETREE.parse(robot)
    found = False
    for body in tree.getroot().iter("body"):
        for old in list(body.findall("camera")):
            if old.get("name") == "onboard":
                body.remove(old)
        if body.get("name") == "head_assembly":
            cam = ETREE.SubElement(body, "camera")
            cam.set("name", "onboard")
            cam.set("pos", "%.5f %.5f %.5f" % CAM_POS)
            cam.set("xyaxes", " ".join("%.1f" % v for v in CAM_XYAXES))
            cam.set("fovy", "%.1f" % FOV_UP_DEG)
            found = True
            break
    if not found:
        raise SystemExit("head_assembly is not in the walk model")
    tree.write(robot)
    scene = os.path.join(dst, "scene_flat_terrain_backlash.xml")
    st = ETREE.parse(scene)
    for tex in st.getroot().iter("texture"):
        if tex.get("name") == "groundplane":
            tex.set("rgb1", "0.86 0.83 0.77")
            tex.set("rgb2", "0.86 0.83 0.77")
            tex.set("markrgb", "0.86 0.83 0.77")
        if tex.get("type") == "skybox":
            tex.set("rgb1", "0.93 0.94 0.96")
            tex.set("rgb2", "0.93 0.94 0.96")
    st.write(scene)
    stripes = []
    y_lim = 0.280
    k0 = int(math.floor((-y_lim) / PERIOD)) - 1
    k1 = int(math.floor(y_lim / PERIOD)) + 1
    for k in range(k0, k1 + 1):
        a, b = PERIOD * k, PERIOD * k + STRIPE
        lo, hi = max(a, -y_lim), min(b, y_lim)
        if hi - lo < 0.004:
            continue
        col = "0.90 0.72 0.20 1" if k % 2 == 0 else "0.72 0.62 0.38 1"
        cy = 0.5 * (lo + hi)
        hy = 0.5 * (hi - lo)
        stripes.append(
            '<geom type="box" pos="0.002 %.4f 0.0025" size="0.180 %.4f 0.00015" rgba="%s" contype="0" conaffinity="0"/>'
            % (cy, hy, col)
        )
    half = MARK_M / 2.0
    xml = """<mujoco model="camera_dock">
<include file="scene_flat_terrain_backlash.xml"/>
<visual><global offwidth="960" offheight="960"/></visual>
<worldbody>
  <light name="room" pos="-0.8 0.2 2.4" dir="0.25 -0.05 -1" directional="true" diffuse="0.65 0.65 0.62" specular="0.05 0.05 0.05" castshadow="false"/>
  <geom name="wall" type="box" pos="0.210 0.04 0.32" size="0.018 0.55 0.32" rgba="0.80 0.78 0.74 1" contype="0" conaffinity="0"/>
  <geom name="mark" type="box" pos="%.4f 0 %.3f" size="0.001 %.4f %.4f" rgba="0.02 0.02 0.02 1" contype="0" conaffinity="0"/>
  <geom name="mark_gold" type="box" pos="%.4f 0 %.4f" size="0.0012 0.011 0.011" rgba="0.95 0.78 0.16 1" contype="0" conaffinity="0"/>
  <geom name="mark2" type="box" pos="%.3f 0 %.3f" size="0.001 %.4f %.4f" rgba="0.02 0.02 0.02 1" contype="0" conaffinity="0"/>
  <geom name="mark2_red" type="box" pos="%.3f 0 %.4f" size="0.0012 0.016 0.016" rgba="0.85 0.08 0.08 1" contype="0" conaffinity="0"/>
  <geom name="charge_led" type="sphere" pos="-0.05 0.32 0.06" size="0.015" rgba="0.15 0.15 0.15 1" contype="0" conaffinity="0"/>
  <geom name="mat_low" type="box" pos="-0.0415 0 0.0005" size="0.2255 0.300 0.0005" rgba="0.55 0.42 0.28 1" contype="1" conaffinity="0" priority="2" friction="0.8 0.01 0.001"/>
  <geom name="mat_top" type="box" pos="-0.0315 0 0.0015" size="0.2155 0.280 0.0005" rgba="0.62 0.48 0.30 1" contype="1" conaffinity="0" priority="3" friction="0.8 0.01 0.001"/>
  %s
</worldbody>
</mujoco>
""" % (
        MARK_FACE_X, MARK_Z, half, half,
        MARK_FACE_X - 0.0004, MARK_Z + GOLD_UP,
        MARK2_X, MARK2_Z, MARK2_M / 2.0, MARK2_M / 2.0,
        MARK2_X + 0.001, MARK2_Z + 0.018,
        "\n  ".join(stripes),
    )
    open(os.path.join(dst, "scene_dock.xml"), "w").write(xml)
    return dst


def _sit_targets(model, infer):
    """The sit-study pose, clamped to the 147 deg knee stop. Same rule as run_twin.sit_path."""
    with open(os.path.join(LAB, "twin", "sit", "sit_pose.json"), encoding="utf-8") as f:
        raw = json.load(f)["joints_deg"]
    with open(os.path.join(LAB, "software", "servo_limits.json"), encoding="utf-8") as f:
        limits = json.load(f)["joints"]
    import mujoco
    ctrl = np.array(infer.default_actuator, float).copy()
    for i, name in enumerate(infer.actuator_names):
        if name not in raw:
            continue
        deg = float(raw[name])
        lim = limits.get(name) or {}
        if lim.get("soft_lo_deg") is not None:
            deg = max(deg, float(lim["soft_lo_deg"]))
        if lim.get("soft_hi_deg") is not None:
            deg = min(deg, float(lim["soft_hi_deg"]))
        if name in ("left_knee", "right_knee"):
            deg = min(deg, 147.0)
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
            aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            if jid >= 0:
                model.jnt_range[jid, 1] = max(float(model.jnt_range[jid, 1]), math.radians(147.0))
            if aid >= 0:
                model.actuator_ctrlrange[aid, 1] = max(float(model.actuator_ctrlrange[aid, 1]), math.radians(147.0))
        if "ankle" in name:
            deg = max(deg, -90.0)
        ctrl[i] = math.radians(deg)
    lo = model.actuator_ctrlrange[:, 0]
    hi = model.actuator_ctrlrange[:, 1]
    return np.clip(ctrl, lo, hi)


class DockSim:
    def __init__(self, seed=0, light=1.0, record=False):
        import contextlib
        import io
        import mujoco
        ET, CB, SV = _boot()
        self.mujoco = mujoco
        self.np = np
        folder = ET.model_folder("ours")
        scene = _scene_dir(folder)
        ET.AM._ASSET_DIR[0] = scene
        onnx = policy_path()
        if not os.path.isfile(onnx) or os.path.basename(onnx) != "sts12_runD_policy.onnx":
            raise SystemExit("the dock walk must load sts12_runD_policy.onnx")
        with contextlib.redirect_stdout(io.StringIO()):
            infer = CB.MI.MjInfer(os.path.join(scene, "scene_dock.xml"), CB.REF, onnx, standing=False)
        self.m = infer
        self.model, self.data = infer.model, infer.data
        ga = infer.get_accelerometer

        def fixed(d, _g=ga):
            a = np.array(_g(d), float)
            a[0] -= 1.3
            return a

        infer.get_accelerometer = fixed
        self.bank = SV.ServoBank(self.model, mode="sheet")
        self.bank.apply(np.full(self.model.nu, 12.0))
        self.fb = int(infer._floating_base_qpos_addr)
        self.trunk = self.model.body("trunk_assembly").id
        self.cam = self.model.cam("onboard").id
        self.rng = np.random.default_rng(seed)
        self.light = float(light)
        self.gain = float(np.clip(light * self.rng.uniform(0.85, 1.15), 0.40, 1.45))
        # room light, per seed
        lid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_LIGHT, "room")
        if lid >= 0:
            self.model.light_diffuse[lid] *= float(np.clip(light, 0.35, 1.4))
        self.model.vis.global_.offwidth = max(int(self.model.vis.global_.offwidth), 960)
        self.model.vis.global_.offheight = max(int(self.model.vis.global_.offheight), 960)
        self.ren = mujoco.Renderer(self.model, IMG_H, IMG_W)
        self.ren3 = mujoco.Renderer(self.model, 360, 640) if record else None
        self.record = record
        self.frames = []
        self.prev = None
        self.t = 0.0
        self.fallen = False
        self.sitting = False
        self.imu_yaw = 0.0
        self.est_q = []
        self.last_quad = None
        self.saw = False
        self.seen_t = -10.0
        self.seen_red = -10.0
        self.seen_gold = -10.0
        self.last_dist = 9.0
        self.gold_dist = 9.0
        self.led = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "charge_led")
        self.gyro0 = 0.0

    def close(self):
        for ren in (self.ren, self.ren3):
            if ren is not None and hasattr(ren, "close"):
                ren.close()

    def set_led(self, on):
        if getattr(self, "led", -1) < 0:
            return
        self.model.geom_rgba[self.led] = (0.15, 0.85, 0.2, 1.0) if on else (0.15, 0.15, 0.15, 1.0)

    def true_pose(self):
        p = self.data.xpos[self.trunk]
        r = self.data.xmat[self.trunk].reshape(3, 3)
        yaw = math.atan2(r[1, 0], r[0, 0])
        up = float(r[2, 2])
        return float(p[0]), float(p[1]), float(yaw), float(p[2]), up

    def _rel_cam(self):
        rt = self.data.xmat[self.trunk].reshape(3, 3)
        pt = self.data.xpos[self.trunk]
        rc = self.data.cam_xmat[self.cam].reshape(3, 3)
        pc = self.data.cam_xpos[self.cam]
        return rt.T @ rc, rt.T @ (pc - pt)

    def _capture(self, blur):
        self.ren.update_scene(self.data, camera="onboard")
        img = self.ren.render().copy()
        if blur and self.prev is not None:
            img = (0.65 * img.astype(np.float32) + 0.35 * self.prev).astype(np.uint8)
        self.prev = img.copy()
        noisy = degrade(img, self.rng, self.gain, blur)
        found = detect(noisy)
        quad = None if found is None else found[0]
        kind = None if found is None else found[1]
        self.last_quad = quad
        est = None
        if quad is not None and kind in ("red", "gold"):
            size = MARK2_M if kind == "red" else MARK_M
            solved = solve_square(quad, half=size / 2.0)
            if solved is not None:
                rm, t, err = solved
                rm_mj, t_mj = marker_in_mj(rm, t)
                r_ct, p_ct = self._rel_cam()
                p = r_ct @ t_mj + p_ct
                dist = math.hypot(float(p[0]), float(p[1]))
                fx, _, _, _, _ = intrinsics()
                width = 0.5 * (
                    float(np.linalg.norm(quad[0] - quad[1])) + float(np.linalg.norm(quad[3] - quad[2]))
                )
                dist_px = size * fx / max(width, 1.0)
                agree = abs(dist - dist_px) / max(dist_px, 1e-3) < 0.55 and err < 5.0
                if agree and 0.18 < dist < 3.3 and abs(float(p[2])) < 0.7 and float(p[0]) > 0.08:
                    est = (float(p[0]), float(p[1]), float(p[2]), float(err), kind)
                    self.saw = True
                    self.seen_t = self.t
                    if kind == "red":
                        self.seen_red = self.t
                    else:
                        self.seen_gold = self.t
                        self.gold_dist = dist
                    self.last_dist = dist
        self.est_q.append((self.t + LAT_S, est))
        if self.record and self.ren3 is not None and int(self.t / CTRL_DT) % 3 == 0:
            shown = draw_quad(noisy, quad)
            cam = self.mujoco.MjvCamera()
            cam.type = self.mujoco.mjtCamera.mjCAMERA_FREE
            p = self.data.xpos[self.trunk]
            cam.lookat[:] = [p[0], p[1], 0.12]
            cam.distance = 1.85
            cam.azimuth = 78
            cam.elevation = -16
            self.ren3.update_scene(self.data, cam)
            wide = self.ren3.render().copy()
            inset = _resize(shown, 168, 292)
            y0, x0 = wide.shape[0] - inset.shape[0] - 8, wide.shape[1] - inset.shape[1] - 8
            wide[y0:y0 + inset.shape[0], x0:x0 + inset.shape[1]] = inset
            self.frames.append(wide)
        return est

    def latest(self):
        """The newest fix that is due, and not older than 0.35 s. A stale fix is not a pose."""
        got = [e for (t, e) in self.est_q if e is not None and t <= self.t and self.t - t < 1.0]
        return got[-1] if got else None

    def _integrate_gyro(self):
        w = np.array(self.m.get_gyro(self.data), float)
        r = self.data.site_xmat[self.m.imu_site_id].reshape(3, 3)
        wz = float((r @ w)[2])
        self.imu_yaw += wz * CTRL_DT

    def step_policy(self, cmd, capture=False, blur=False):
        m = self.m
        md, dd = self.model, self.data
        for _ in range(m.decimation):
            self.mujoco.mj_step(md, dd)
        self.t += CTRL_DT
        m.commands = [float(cmd[0]), float(cmd[1]), float(cmd[2]), 0.0, 0.0, 0.0, 0.0]
        m.imitation_i = (m.imitation_i + m.phase_frequency_factor) % m.PRM.nb_steps_in_period
        ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * math.pi
        m.imitation_phase = np.array([math.cos(ph), math.sin(ph)])
        obs = m.get_obs(dd, m.commands)
        a = m.policy.infer(obs)
        m.last_last_last_action = m.last_last_action.copy()
        m.last_last_action = m.last_action.copy()
        m.last_action = a.copy()
        m.motor_targets = m.default_actuator + a * m.action_scale
        lim = m.max_motor_velocity * (m.sim_dt * m.decimation)
        m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - lim, m.prev_motor_targets + lim)
        m.prev_motor_targets = m.motor_targets.copy()
        dd.ctrl[:] = m.motor_targets
        self._integrate_gyro()
        est = None
        if capture:
            est = self._capture(blur)
        x, y, yaw, z, up = self.true_pose()
        self._check_fall(z, up)
        return est

    def _check_fall(self, z, up):
        if self.sitting:
            if up < 0.30 or z < 0.04:
                self.fallen = True
        elif up < 0.45 or z < 0.07:
            self.fallen = True

    def go_pose(self, target, seconds, sitting=True):
        """Policy off. Cosine ramp of the position targets, then the gains stay on."""
        self.sitting = sitting
        c0 = self.data.ctrl.copy()
        n = max(1, int(round(seconds / self.model.opt.timestep)))
        for i in range(n):
            s = 0.5 - 0.5 * math.cos(math.pi * (i + 1) / n)
            self.data.ctrl[:] = c0 * (1 - s) + target * s
            self.mujoco.mj_step(self.model, self.data)
            if (i + 1) % 10 == 0:
                self.t += CTRL_DT
                self._integrate_gyro()
                _, _, _, z, up = self.true_pose()
                self._check_fall(z, up)
                if self.record and int(self.t / CTRL_DT) % 3 == 0:
                    self._capture(False)

    def torque_off(self, seconds):
        self.model.actuator_gainprm[:, 0] = 0.0
        self.model.actuator_biasprm[:, 1] = 0.0
        n = max(1, int(round(seconds / self.model.opt.timestep)))
        for i in range(n):
            self.mujoco.mj_step(self.model, self.data)
            if (i + 1) % 10 == 0:
                self.t += CTRL_DT
                _, _, _, z, up = self.true_pose()
                self._check_fall(z, up)
                if self.record and int(self.t / CTRL_DT) % 3 == 0:
                    self._capture(False)


def _place(sim, x, y, yaw):
    import mujoco
    mujoco.mj_resetDataKeyframe(sim.model, sim.data, 0)
    fb = sim.fb
    sim.data.qpos[fb] = x
    sim.data.qpos[fb + 1] = y
    sim.data.qpos[fb + 2] = float(sim.data.qpos[fb + 2]) + 0.012
    sim.data.qpos[fb + 3:fb + 7] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    mujoco.mj_forward(sim.model, sim.data)
    sim.t = 0.0
    sim.imu_yaw = 0.0
    sim.gyro0 = 0.0


def _cmd_mark(est, goal_range, slow, y_goal=0.0):
    """Joystick from the mark's position in the trunk frame. x forward, y left.

    y_goal is where the mark should sit in that frame. A positive goal puts
    the duck to the right of the centre line before a left turn, which is
    the way this policy drifts.
    """
    ey = est[1] - y_goal
    bearing = math.atan2(ey, est[0])
    dist = math.hypot(est[0], est[1])
    if abs(bearing) > 0.40 and dist > goal_range + 0.08:
        return (0.0, 0.0, float(np.clip(1.4 * bearing, -WZ_MAX, WZ_MAX)))
    vmax = 0.10 if slow else VX_MAX
    vx = float(np.clip(0.9 * (dist - goal_range), -0.06, vmax))
    vy = float(np.clip(0.7 * ey, -VY_MAX, VY_MAX))
    wz = float(np.clip(1.3 * bearing, -WZ_MAX, WZ_MAX))
    if dist < goal_range + 0.02:
        vx = min(vx, 0.0)
    return (vx, vy, wz)


def pose_from_room_mark(est):
    """Trunk x, y, yaw in the nest, from the room-side mark in the trunk frame.

    The duck faces the mark, so its heading is pi plus the bearing. Calc only.
    """
    bearing = math.atan2(est[1], est[0])
    yaw = wrap(math.pi + bearing)
    c, s = math.cos(yaw), math.sin(yaw)
    tx = MARK2_X - (c * est[0] - s * est[1])
    ty = 0.0 - (s * est[0] + c * est[1])
    return tx, ty, yaw


def camera_says_ok(est):
    """True when the room mark is nearly straight ahead at the sit range.

    Facing that mark keeps the heading inside about 8 deg. At that heading the
    stripe pair still has several millimetres of foil past the well edge
    (calc only, score_wells). The policy does not walk backward, so the range
    window is wider than the heading window.
    """
    if est is None or (len(est) > 4 and est[4] != "red"):
        return False
    bearing = abs(math.atan2(est[1], est[0]))
    dist = math.hypot(est[0], est[1])
    # The sit range is about 2.09 m. A short reading means the seat is still
    # out in the room, past the foil, and this policy cannot walk backward.
    # Heading is closed first. At 2.1 m a bearing of 0.22 rad is about 0.45 m
    # of side error if the heading is already true (calc only). The foil meets
    # inside that for the headings this sit actually reaches (score_wells).
    return bearing < 0.22 and 1.75 < dist < 2.30


def _cmd_wall(est):
    """Walk forward toward the wall mark. Reverse does not move this policy."""
    bearing = math.atan2(est[1], est[0])
    dist = math.hypot(est[0], est[1])
    # Stop short of the wall. Inside about 0.39 m the square fills the frame
    # and the detector drops it, which is how the turn used to go blind.
    goal = 0.46
    if abs(bearing) > 0.40:
        return (0.0, 0.0, float(np.clip(1.4 * bearing, -WZ_MAX, WZ_MAX)))
    vx = float(np.clip(0.85 * (dist - goal), 0.0, 0.18))
    vy = float(np.clip(0.6 * est[1], -VY_MAX, VY_MAX))
    wz = float(np.clip(1.3 * bearing, -0.6, 0.6))
    return (vx, vy, wz)


def _cmd_room(est):
    """Face the room mark. Walk forward only, which moves away from the wall."""
    bearing = math.atan2(est[1], est[0])
    dist = math.hypot(est[0], est[1])
    if abs(bearing) > 0.35:
        return (0.0, 0.0, float(np.clip(1.4 * bearing, -WZ_MAX, WZ_MAX)))
    vx = 0.0
    if dist > GOAL_RANGE + 0.05:
        vx = float(np.clip(0.7 * (dist - GOAL_RANGE), 0.0, 0.12))
    # Side-step barely moves this policy and it drags the heading. Heading first.
    vy = float(np.clip(0.15 * est[1], -0.05, 0.05))
    wz = float(np.clip(1.6 * bearing, -0.55, 0.55))
    return (vx, vy, wz)


def _kind(est):
    return est[4] if est is not None and len(est) > 4 else None


def _false_room(sim, est, kind):
    """The wall card solved at the room-mark size.

    The two marks are 2.39 m apart. A red range under 1.55 m cannot be the
    room mark if the wall mark was just seen inside 1.05 m.
    """
    if kind != "red" or est is None:
        return False
    dist = math.hypot(est[0], est[1])
    return getattr(sim, "gold_dist", 9.0) < 1.05 and dist < 1.55


def run_one(seed, x0, y0, yaw0, light=1.0, record=False, limit_s=70.0):
    sim = DockSim(seed=seed, light=light, record=record)
    try:
        _place(sim, x0, y0, yaw0)
        mode = "search"
        t_mode = 0.0
        spin = 1.0
        imu_lock = 0.0
        retries = 0
        reason = "timeout"
        k = 0
        while sim.t < limit_s and not sim.fallen:
            capture = (k % 2 == 0)
            cmd = (0.0, 0.0, 0.0)
            est = sim.latest()
            kind = _kind(est)
            if kind is not None:
                sim.last_kind = kind
            if _false_room(sim, est, kind):
                kind = None
            # A good room-mark fix is a sit, even if a retry was about to spin away.
            if kind == "red" and camera_says_ok(est) and mode != "fine":
                mode, t_mode = "fine", sim.t
            if mode == "search":
                # Either mark is enough. The room mark is what the duck sees
                # once it faces away from the wall, so spinning past it was a miss.
                if kind == "gold":
                    mode, t_mode = "approach", sim.t
                    sim._stable_dist = None
                    cmd = _cmd_wall(est)
                elif kind == "red":
                    dist = math.hypot(est[0], est[1])
                    bearing = abs(math.atan2(est[1], est[0]))
                    if dist > GOAL_RANGE - 0.22 and bearing < 0.45:
                        mode, t_mode = "fine", sim.t
                        cmd = _cmd_room(est)
                    else:
                        # Too far into the room to sit. Turn to the wall and walk in.
                        mode, t_mode = "about", sim.t
                        imu_lock = sim.imu_yaw
                        cmd = (0.0, 0.0, 0.50)
                else:
                    cmd = (0.0, 0.0, 0.50 * spin)
                    if sim.t - t_mode > 6.0:
                        spin = -spin
                        t_mode = sim.t
                    if sim.t > 28.0 and not sim.saw:
                        reason = "no_marker"
                        break
            elif mode == "about":
                # Face the wall. The room mark leaves the frame; the wall mark
                # is the one to re-acquire. Still standing, no sit yet.
                turned = abs(wrap(sim.imu_yaw - imu_lock))
                if kind == "red" and est is not None and math.hypot(est[0], est[1]) > 1.5:
                    mode, t_mode = "fine", sim.t
                    cmd = (0.0, 0.0, 0.0)
                elif kind == "gold":
                    mode, t_mode = "approach", sim.t
                    sim._stable_dist = None
                    cmd = _cmd_wall(est)
                elif turned > 2.55 or sim.t - t_mode > 8.5:
                    mode, t_mode = "search", sim.t
                    cmd = (0.0, 0.0, 0.0)
                else:
                    cmd = (0.0, 0.0, 0.50)
            elif mode == "approach":
                if kind == "gold":
                    cmd = _cmd_wall(est)
                    dist = math.hypot(est[0], est[1])
                    bearing = abs(math.atan2(est[1], est[0]))
                    lateral = abs(est[1])
                    # A range that jumps long after a close reading is a bad solve.
                    # Walking on it is how the duck hits the wall.
                    prev = getattr(sim, "_stable_dist", None)
                    if prev is not None and prev < 0.85 and dist > prev + 0.35:
                        dist = prev
                        cmd = (0.0, 0.0, 0.0)
                    else:
                        sim._stable_dist = dist
                    sim._hold_cmd = cmd
                    # Turn while the wall mark is still in frame, and not so close
                    # that the yaw drift carries the body into the wall.
                    ready = bearing < 0.22 and (
                        (0.44 <= dist <= 0.52 and lateral < 0.12) or dist < 0.44
                    )
                    if ready:
                        mode, t_mode = "turn", sim.t
                        imu_lock = sim.imu_yaw
                        sim._turn_sign = 1.0
                else:
                    blind = sim.t - sim.seen_gold
                    if getattr(sim, "last_kind", None) == "gold" and getattr(sim, "gold_dist", 9) < 0.90 and blind > 0.35:
                        mode, t_mode = "turn", sim.t
                        imu_lock = sim.imu_yaw
                        sim._turn_sign = 1.0
                        cmd = (0.0, 0.0, 0.0)
                    else:
                        held = getattr(sim, "_hold_cmd", None)
                        cmd = held if (blind < 1.3 and held is not None) else (0.0, 0.0, 0.0)
                        if blind > 4.5:
                            if retries < 2:
                                retries += 1
                                mode, t_mode = "search", sim.t
                                spin = 1.0
                            else:
                                reason = "lost_marker"
                                break
                if sim.t - t_mode > 22.0 and mode == "approach":
                    reason = "missed_line"
                    break
            elif mode == "turn":
                # Hold a yaw rate the policy actually follows. Tapering it from
                # the gyro stalls the duck around 140 deg, short of the room mark.
                # The room mark is the thing that ends the turn, so it stays in view
                # for the sit. Side-step is off: it fights this yaw.
                if kind == "red":
                    mode, t_mode = "fine", sim.t
                    cmd = _cmd_room(est)
                elif sim.t - t_mode > 12.0:
                    mode, t_mode = "fine", sim.t
                else:
                    # vy negative is the drift that walks the duck toward the
                    # wall during this left turn. Without it the sit lands short.
                    cmd = (0.0, -0.08, 0.55)
            elif mode == "fine":
                if kind == "red":
                    sim._last_red = est
                    dist = math.hypot(est[0], est[1])
                    bearing = math.atan2(est[1], est[0])
                    # Once the room mark is in frame, do not keep the turn's
                    # side velocity. That drift is what walks a good pose into the wall.
                    in_box = camera_says_ok(est)
                    if in_box:
                        sim._ok_n = getattr(sim, "_ok_n", 0) + 1
                        cmd = (0.0, 0.0, 0.0)
                        sim._hold_cmd = cmd
                        if sim._ok_n >= 4:
                            mode = "sit"
                            break
                    elif dist > 2.30:
                        cmd = _cmd_room(est)
                        sim._hold_cmd = cmd
                        sim._ok_n = 0
                    elif dist < 1.75 and sim.t - t_mode > 2.5 and retries < 2:
                        retries += 1
                        mode, t_mode = "about", sim.t
                        imu_lock = sim.imu_yaw
                        cmd = (0.0, 0.0, 0.50)
                        sim._ok_n = 0
                    else:
                        # Yaw only, and hard enough that the policy does not stall
                        # short of the mark. No side velocity: that walks into the wall.
                        sgn = 1.0 if bearing >= 0.0 else -1.0
                        cmd = (0.0, 0.0, sgn * 0.50)
                        sim._hold_cmd = cmd
                        sim._ok_n = 0
                else:
                    blind = sim.t - sim.seen_red
                    held = getattr(sim, "_hold_cmd", None)
                    # Keep turning. A stop here leaves the room mark just outside
                    # the 41 deg field, and the heading never closes.
                    if blind < 0.4 and held is not None:
                        cmd = held
                    else:
                        cmd = (0.0, 0.0, 0.55)
                    last = getattr(sim, "_last_red", None)
                    if last is not None and camera_says_ok(last) and blind < 1.4:
                        mode = "sit"
                        break
                if sim.t - t_mode > 10.0 and mode == "fine" and kind != "red":
                    last = getattr(sim, "_last_red", None)
                    if last is not None and camera_says_ok(last):
                        mode = "sit"
                        break
                    if retries < 2:
                        retries += 1
                        # Still standing. Step toward the room mark, then
                        # face the wall and approach again.
                        mode, t_mode = "backoff", sim.t
                    else:
                        reason = "not_lined"
                        break
            elif mode == "backoff":
                if kind == "red":
                    cmd = (0.12, 0.0, float(np.clip(1.2 * math.atan2(est[1], est[0]), -0.45, 0.45)))
                else:
                    cmd = (0.12, 0.0, 0.25 * spin)
                if sim.t - t_mode > 1.8:
                    mode, t_mode = "about", sim.t
                    imu_lock = sim.imu_yaw
            if mode == "sit":
                break
            # A pure yaw command stalls this policy around a right angle, in
            # the search. One short step restarts the gait. Not during the
            # turn: that step walks into the wall.
            if mode in ("search", "about") and abs(cmd[2]) >= 0.40 and cmd[0] < 0.05:
                if sim.t - getattr(sim, "_spin_t", -10.0) > 1.2:
                    moved = abs(wrap(sim.imu_yaw - getattr(sim, "_spin_yaw", sim.imu_yaw)))
                    if moved < 0.10 and getattr(sim, "_kicks", 0) < 4:
                        sim._kick_until = sim.t + 0.40
                        sim._kicks = getattr(sim, "_kicks", 0) + 1
                    sim._spin_t = sim.t
                    sim._spin_yaw = sim.imu_yaw
                if sim.t < getattr(sim, "_kick_until", 0.0):
                    cmd = (0.12, 0.0, 0.0)
            else:
                sim._spin_t = sim.t
                sim._spin_yaw = sim.imu_yaw
            # If the turn's yaw stalls, drop the side step. That side step is
            # what walks a stuck duck into the wall.
            if mode == "turn" and abs(cmd[2]) >= 0.40:
                if sim.t - getattr(sim, "_turn_t", -10.0) > 2.0:
                    moved = abs(wrap(sim.imu_yaw - getattr(sim, "_turn_yaw", sim.imu_yaw)))
                    if moved < 0.05:
                        sim._turn_plain_until = sim.t + 0.8
                    sim._turn_t = sim.t
                    sim._turn_yaw = sim.imu_yaw
                if sim.t < getattr(sim, "_turn_plain_until", 0.0):
                    cmd = (0.0, 0.0, 0.55 if cmd[2] >= 0.0 else -0.55)
            speed = math.hypot(sim.data.qvel[0], sim.data.qvel[1])
            sim.step_policy(cmd, capture=capture, blur=speed > 0.15)
            k += 1
            if os.environ.get("CAM_DOCK_DEBUG") and k % 25 == 0:
                tp = sim.true_pose()
                print("t=%.1f %s %s cmd %s true %.2f %.2f %.0f est %s" % (
                    sim.t, mode, kind, tuple(round(c, 2) for c in cmd), tp[0], tp[1], math.degrees(tp[2]),
                    None if est is None else tuple(round(v, 3) for v in est[:3])), flush=True)
        sat = False
        if sim.fallen:
            reason = "fell"
        elif mode == "sit":
            target = _sit_targets(sim.model, sim.m)
            sim.go_pose(target, 3.0, sitting=True)
            sim.torque_off(1.2)
            if sim.fallen:
                reason = "fell"
            else:
                sat = True
                # The pre-sit gate already used the camera. Standing up from a
                # good sit because the head moved is what threw away meets.
                reason = "sat"
        x, y, yaw, z, up = sim.true_pose()
        scored = score_wells(x, y, yaw)
        heading = abs(math.degrees(wrap(yaw - math.pi)))
        ok = bool(sat and scored["contacts_meet"] and not sim.fallen and heading < 20.0)
        elec = score_charge(sim, x, y, yaw, ok)
        if elec["charging"] and record:
            sim.set_led(True)
            for _ in range(6):
                sim._capture(False)
        if ok:
            reason = "docked"
        elif sat and not ok:
            reason = "sat_off_stripes" if not scored["contacts_meet"] else "heading"
        out = dict(
            seed=int(seed),
            start=[round(x0, 3), round(y0, 3), round(math.degrees(yaw0), 1)],
            light=round(float(light), 2),
            gain=round(float(sim.gain), 2),
            ok=ok,
            reason=reason,
            retries=int(retries),
            t_s=round(sim.t, 2),
            fell=bool(sim.fallen),
            saw=bool(sim.saw),
            sat=bool(sat),
            true=[round(x, 3), round(y, 3), round(math.degrees(yaw), 1), round(z, 3)],
            **scored,
            **elec,
        )
        frames = list(sim.frames) if record else []
        return out, frames
    finally:
        sim.close()


STARTS = [
    # metres and degrees. Varied room positions, headings, and light. 20 seeds.
    (1, -1.05, 0.00, 0.0, 1.00),
    (2, -1.20, 0.22, -20.0, 0.70),
    (3, -0.90, -0.26, 28.0, 1.20),
    (4, -1.40, 0.10, 12.0, 0.50),
    (5, -1.10, -0.16, -32.0, 1.30),
    (6, -0.85, 0.28, 18.0, 0.80),
    (7, -1.30, -0.30, 8.0, 0.60),
    (8, -1.15, 0.06, 150.0, 1.00),
    (9, -1.50, 0.34, -24.0, 0.45),
    (10, -1.00, -0.08, 6.0, 1.10),
    (11, -1.25, -0.20, 40.0, 0.90),
    (12, -0.95, 0.14, -15.0, 1.25),
    (13, -1.45, -0.05, 160.0, 0.65),
    (14, -1.10, 0.32, -45.0, 0.55),
    (15, -1.35, 0.00, 90.0, 1.05),
    (16, -0.88, -0.18, 22.0, 0.75),
    (17, -1.55, 0.16, -90.0, 1.15),
    (18, -1.18, -0.28, 12.0, 0.48),
    (19, -1.02, 0.08, -160.0, 0.85),
    (20, -1.32, -0.12, 35.0, 1.00),
]


# A second set, not a copy of the first 20. Same room, different starts.
STARTS_NEW = [
    (21, -1.12, -0.04, 8.0, 0.90),
    (22, -1.28, 0.18, -12.0, 0.75),
    (23, -0.98, -0.22, 24.0, 1.15),
    (24, -1.42, 0.08, -8.0, 0.55),
    (25, -1.06, 0.12, 140.0, 1.00),
    (26, -1.22, -0.30, 16.0, 0.65),
    (27, -0.92, 0.20, -28.0, 1.20),
    (28, -1.48, -0.10, 70.0, 0.85),
    (29, -1.16, 0.28, -40.0, 0.50),
    (30, -1.34, -0.16, 4.0, 1.05),
    (31, -1.00, 0.00, -150.0, 0.80),
    (32, -1.38, 0.22, 32.0, 0.70),
    (33, -1.10, -0.08, 110.0, 1.10),
    (34, -1.26, 0.06, -6.0, 0.60),
    (35, -0.96, -0.14, 20.0, 1.25),
    (36, -1.52, 0.14, -70.0, 0.45),
    (37, -1.18, -0.24, 48.0, 0.95),
    (38, -1.08, 0.16, 175.0, 0.85),
    (39, -1.30, -0.02, -18.0, 1.00),
    (40, -1.44, 0.26, 10.0, 0.72),
]


def batch(n=20, record=False, limit_s=70.0, starts=None):
    rows = []
    success_frames = None
    fail_frames = None
    for seed, x, y, yaw_deg, light in list(starts or STARTS)[:n]:
        want = record and (success_frames is None or fail_frames is None)
        row, frames = run_one(seed, x, y, math.radians(yaw_deg), light, record=want, limit_s=limit_s)
        rows.append(row)
        print("seed %d %s t=%.1f align=%s" % (seed, row["reason"], row["t_s"], row["align_mm"]), flush=True)
        if record and frames:
            if row["ok"] and success_frames is None:
                success_frames = frames
            elif (not row["ok"]) and fail_frames is None:
                fail_frames = frames
    return rows, success_frames, fail_frames


def summarize(rows):
    n = len(rows)
    ok = [r for r in rows if r["ok"]]
    charged = [r for r in rows if r.get("charging")]
    fails = {}
    for r in rows:
        if not r["ok"]:
            fails[r["reason"]] = fails.get(r["reason"], 0) + 1
    aligns = [r["align_mm"] for r in ok]
    times = [r["t_s"] for r in ok]
    margins = [r["stripe_margin_mm"] for r in ok if r["stripe_margin_mm"] is not None]
    return dict(
        n=n,
        ok=len(ok),
        rate=round(len(ok) / n, 3) if n else None,
        charge_n=len(charged),
        charge_rate=round(len(charged) / n, 3) if n else None,
        align_mm_median=round(float(np.median(aligns)), 1) if aligns else None,
        align_mm_max=round(float(np.max(aligns)), 1) if aligns else None,
        margin_mm_min=round(float(np.min(margins)), 2) if margins else None,
        time_s_median=round(float(np.median(times)), 1) if times else None,
        time_s_max=round(float(np.max(times)), 1) if times else None,
        failures=fails,
    )


def write_video(frames, path, fps=8):
    if not frames:
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = frames[0].shape[:2]
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "%dx%d" % (w, h), "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28",
        "-preset", "veryfast", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fr in frames:
        proc.stdin.write(np.ascontiguousarray(fr).tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0 or not os.path.isfile(path):
        raise SystemExit("video encode failed")
    if os.path.getsize(path) > 5_000_000:
        raise SystemExit("video over 5 MB: " + os.path.basename(path))
    return path


def walk_video(path, seconds=8.0):
    """A short third-person clip of run D walking. Sim pass only."""
    sim = DockSim(seed=1, light=1.0, record=True)
    try:
        # Face away from the nest so the clip is the walk, not the wall.
        _place(sim, -0.4, 0.0, math.pi)
        k = 0
        while sim.t < seconds and not sim.fallen:
            cmd = (0.0, 0.0, 0.0) if sim.t < 0.8 else (0.20, 0.0, 0.0)
            sim.step_policy(cmd, capture=True, blur=False)
            k += 1
        return write_video(sim.frames, path, fps=10)
    finally:
        sim.close()


def short_check():
    """One frame, marker in view. CI safe. Not a dock rate."""
    sim = DockSim(seed=0, light=1.0, record=False)
    try:
        _place(sim, -1.15, 0.02, math.pi)
        for _ in range(8):
            sim.step_policy((0.0, 0.0, 0.0), capture=False)
        est = sim._capture(False)
        if est is None:
            return dict(ran=True, ok=False, camera="short", note="the short check did not see the mark")
        rt = sim.data.xmat[sim.trunk].reshape(3, 3)
        pt = sim.data.xpos[sim.trunk]
        truth = rt.T @ (np.array([MARK2_X, 0.0, MARK2_Z]) - pt)
        dx = (est[0] - truth[0]) * 1000.0
        dy = (est[1] - truth[1]) * 1000.0
        bear = abs(math.degrees(math.atan2(est[1], est[0]) - math.atan2(truth[1], truth[0])))
        ok = math.hypot(dx, dy) < 80.0 and bear < 8.0
        return dict(
            ran=True, ok=ok, camera="short",
            err_mm=round(math.hypot(dx, dy), 1),
            yaw_err_deg=round(bear, 2),
            note="short check, one frame, marker in view, body-frame error",
        )
    finally:
        sim.close()


def _no_dash(text):
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("camera dock text has a dash that is not a hyphen")
    return text


def write_note(path, rows, summary):
    lines = []
    a = lines.append
    a("# Camera dock")
    a("")
    a("Simulation only. The run D policy walks. The nest pose in the loop is the head camera. The true pose is the score after the sit. This is not a hardware dock, and it is not a charge.")
    a("")
    a("Camera: Raspberry Pi Camera Module 3 standard, product brief June 2024, RP-008151-DS-1, page 5. Cited: 66 deg and 41 deg, focal length 4.74 mm. On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is camera_seat.json, lens opening, CAD check only. The entrance pupil is still unmarked (BLOCKER). A 5 mm shift along the axis is under 1 deg at 0.3 m (calc only, that note).")
    a("")
    a("Wall mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. Room mark: 120 mm black square, red felt patch, at x = -2.20 m, centre 280 mm up, on the centre line, facing the duck. The duck walks to the wall mark, turns, and finishes the heading on the room mark so the mark stays in view. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). Both squares fit on that one sheet (calc only, 80 mm plus 120 mm). The red sheet is 0.65 USD (OnlineFabricStore, 9 by 12 inch red felt, page price shown 2026-11-15, cited). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER. The stripe stays 20 mm foil and a 5 mm gap, because a coin can bridge a narrower gap (NEST_V2.md blocker 2).")
    a("")
    a("Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The detector then scales the frame so the 95th percentile is mid white, which stands in for the module's auto exposure. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.")
    a("")
    rate = summary["rate"]
    a("Geometry: %d of %d docks put one well fully on plus and one fully on minus (sim pass only). Rate %.2f." % (summary["ok"], summary["n"], rate if rate is not None else 0))
    a("Charging: %d of %d. A charge needs that geometry, at least 0.294 N (30 grams, Samtec gold guideline, 23 Sep 2022, cited) on one well of each pole, and the BQ24133 input still inside 4.5 V to 17 V after the contact drop (parts.yaml, the chip sheet). The resistance model is in the charge section below." % (summary.get("charge_n") or 0, summary["n"]))
    if summary["align_mm_median"] is not None:
        a("On the docks that met, the seat centre was a median %.1f mm from the sun and at most %.1f mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least %.2f mm (calc only on the scored pose)." % (
            summary["align_mm_median"], summary["align_mm_max"], summary["margin_mm_min"] or 0))
        a("Time to dock, median %.1f s, max %.1f s (sim pass only)." % (summary["time_s_median"], summary["time_s_max"]))
    if summary["failures"]:
        bits = ", ".join("%s %d" % (k, v) for k, v in sorted(summary["failures"].items()))
        a("Failures: %s." % bits)
    else:
        a("No failure in this batch.")
    a("A timeout is a turn that lost the room mark, or a stop short of the foil. This policy does not walk backward, so that short stop is not walked back onto the mat. When the camera says the wells are off, the duck stays standing, steps toward the room mark, turns back to the wall, and approaches again. That retry is capped at two.")
    a("")
    a("A geometric meet is one well circle inside a plus stripe and one inside a minus stripe. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.")
    a("Charge model, assumption on the pair: the foil is copper tape (BOM), and no gold-on-copper force curve was found. Clean gold is a few milliohms under 10 grams when held still (Mroczkowski, Connector Supplier, 7 Apr 2009, cited). This note uses 5 milliohms at 10 grams, scaling as 1/sqrt(force), then times 5 for dust and fuzz. The 5 milliohms and the dust factor are assumptions. The wire is 0.038 ohm for both poles (NEST_V2.md, calc only). The nest supply is 15 V and the chip window is 4.5 V to 17 V (parts.yaml, BQ24133 sheet).")
    a("In this walk model the gold wells are not collision shapes. After the sit the MuJoCo contacts are the two foot soles on the mat. No contact falls inside 6 mm of a well, so every well force is 0 N, under the 0.294 N floor, and the charger path is open. The lamp in the video stays dark for that reason. This is not a measurement of a real seat.")
    a("")
    a("| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |")
    a("|---|---|---|---|---|---|---|---|")
    for r in rows:
        a("| %d | %.2f %.2f %.0f | %.2f | %s | %.1f | %s | %s | %s |" % (
            r["seed"], r["start"][0], r["start"][1], r["start"][2], r["light"], r["reason"], r["t_s"],
            r["align_mm"], r["yaw_err_deg"], r["stripe_margin_mm"]))
    a("")
    a("The 12 V rail is the sheet law at a held 12.0 V (sts12.py, cited stall 30 kg.cm at 12 V). The old 7.2 V aim-offset table is not in this loop.")
    text = _no_dash("\n".join(lines) + "\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--short" in argv:
        row = short_check()
        print(json.dumps(row))
        return 0 if row.get("ok") else 1
    if "--walk-video" in argv:
        path = os.path.join(LAB, "twin", "out", "videos", "runD_walk.mp4")
        write = walk_video(path)
        print(write)
        return 0
    n = 10
    if "--seeds" in argv:
        n = int(argv[argv.index("--seeds") + 1])
    record = "--videos" in argv
    rows, ok_fr, bad_fr = batch(n=n, record=record)
    summary = summarize(rows)
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "batch.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=summary, rows=rows), f, indent=1)
    write_note(os.path.join(HERE, "CAMERA_DOCK.md"), rows, summary)
    vid = os.path.join(LAB, "twin", "out", "videos")
    if ok_fr:
        write_video(ok_fr, os.path.join(vid, "dock_success.mp4"))
        print("wrote dock_success.mp4", len(ok_fr))
    if bad_fr:
        write_video(bad_fr, os.path.join(vid, "dock_fail.mp4"))
        print("wrote dock_fail.mp4", len(bad_fr))
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
