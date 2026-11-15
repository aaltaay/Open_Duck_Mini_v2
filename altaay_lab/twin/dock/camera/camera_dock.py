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

The mark is an 80 mm black felt square with a gold-foil patch, on the wall at
the nest v2 card station (centre 350 mm up, on the centre line). The drawn
card is 40 mm. At a 1.5 m start that square is about 11 px wide on a 320-wide
frame of this lens (calc only), which is too small once blur is added. 80 mm
is the size this detector holds. Felt price is in CAMERA_DOCK.md.

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
    margins = []
    for wx, wy in wells:
        labs = [band(wy - WELL_R), band(wy), band(wy + WELL_R)]
        on_field = FIELD_X0 < wx < FIELD_X1
        if labs[0] == labs[1] == labs[2] and labs[0] in ("P", "M") and on_field:
            hits.append(labs[0])
            # clearance to the edge of this 20 mm conductor
            k = math.floor(wy / PERIOD)
            a = k * PERIOD
            b = a + STRIPE
            margins.append(min(wy - WELL_R - a, b - (wy + WELL_R)) * 1000.0)
        elif "P" in labs and "M" in labs:
            hits.append("short")
        else:
            hits.append("miss")
    n_p = hits.count("P")
    n_m = hits.count("M")
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
        stripe_margin_mm=round(min(margins), 2) if margins else None,
        align_mm=round(sun, 1),
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
    """Black square plus the gold patch. Returns 4 image corners TL TR BR BL, or None."""
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
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
    gold = (rr > 100) & (bb < 110) & (gg > 60) & (np.abs(rr - gg) < 80) & (gg > bb + 15)
    if int(gold.sum()) < 6:
        return None
    gy, gx = np.where(gold)
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
    return quad


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
  <geom name="mat_low" type="box" pos="-0.0415 0 0.0005" size="0.2255 0.300 0.0005" rgba="0.55 0.42 0.28 1" contype="1" conaffinity="0" priority="2" friction="0.8 0.01 0.001"/>
  <geom name="mat_top" type="box" pos="-0.0315 0 0.0015" size="0.2155 0.280 0.0005" rgba="0.62 0.48 0.30 1" contype="1" conaffinity="0" priority="3" friction="0.8 0.01 0.001"/>
  %s
</worldbody>
</mujoco>
""" % (
        MARK_FACE_X, MARK_Z, half, half,
        MARK_FACE_X - 0.0004, MARK_Z + GOLD_UP,
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
        self.last_dist = 9.0
        self.gyro0 = 0.0

    def close(self):
        for ren in (self.ren, self.ren3):
            if ren is not None and hasattr(ren, "close"):
                ren.close()

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
        quad = detect(noisy)
        self.last_quad = quad
        est = None
        if quad is not None:
            solved = solve_square(quad)
            if solved is not None:
                rm, t, err = solved
                rm_mj, t_mj = marker_in_mj(rm, t)
                r_ct, p_ct = self._rel_cam()
                # Marker origin in the trunk frame. The chain is the joints.
                # The square's yaw is not observable at this size, so the
                # translation is the measurement the walk uses.
                p = r_ct @ t_mj + p_ct
                dist = math.hypot(float(p[0]), float(p[1]))
                fx, _, _, _, _ = intrinsics()
                width = 0.5 * (
                    float(np.linalg.norm(quad[0] - quad[1])) + float(np.linalg.norm(quad[3] - quad[2]))
                )
                dist_px = MARK_M * fx / max(width, 1.0)
                agree = abs(dist - dist_px) / max(dist_px, 1e-3) < 0.40 and err < 3.0
                if agree and 0.22 < dist < 2.2 and abs(float(p[2])) < 0.55 and float(p[0]) > 0.08:
                    est = (float(p[0]), float(p[1]), float(p[2]), float(err))
                    self.saw = True
                    self.seen_t = self.t
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
        got = [e for (t, e) in self.est_q if e is not None and t <= self.t and self.t - t < 0.35]
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
        if not self.sitting and (up < 0.45 or z < 0.07):
            self.fallen = True
        if self.sitting and up < 0.30:
            self.fallen = True
        return est

    def go_pose(self, target, seconds):
        """Policy off. Cosine ramp of the position targets, then the gains stay on."""
        self.sitting = True
        c0 = self.data.ctrl.copy()
        n = max(1, int(round(seconds / self.model.opt.timestep)))
        for i in range(n):
            s = 0.5 - 0.5 * math.cos(math.pi * (i + 1) / n)
            self.data.ctrl[:] = c0 * (1 - s) + target * s
            self.mujoco.mj_step(self.model, self.data)
            if (i + 1) % 10 == 0:
                self.t += CTRL_DT
                self._integrate_gyro()
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


def run_one(seed, x0, y0, yaw0, light=1.0, record=False, limit_s=48.0):
    sim = DockSim(seed=seed, light=light, record=record)
    try:
        _place(sim, x0, y0, yaw0)
        # Horizontal range from the trunk to the wall mark. The mark is at
        # x = 0.188. The lineup is in front of the mat. The sit spot faces
        # the room, with the seat near the sun.
        range_line = 0.70
        range_sit = 0.36
        mode = "search"
        t_mode = 0.0
        spin = 1.0
        imu_lock = None
        reason = "timeout"
        k = 0
        while sim.t < limit_s and not sim.fallen:
            blur = False
            capture = (k % 4 == 0)
            cmd = (0.0, 0.0, 0.0)
            est = sim.latest()
            if mode == "search":
                cmd = (0.0, 0.0, 0.70 * spin)
                if est is not None and abs(math.atan2(est[1], est[0])) < 0.35:
                    mode, t_mode = "approach", sim.t
                elif sim.t - t_mode > 8.0:
                    spin = -1.0
                if sim.t > 16.0 and est is None:
                    reason = "no_marker"
                    break
            elif mode == "approach":
                if est is None:
                    blind = sim.t - getattr(sim, "seen_t", 0.0)
                    cmd = (0.08, 0.0, 0.0) if blind < 1.0 else (0.0, 0.0, 0.45 * spin)
                    if blind > 4.0:
                        reason = "lost_marker"
                        break
                else:
                    dist = math.hypot(est[0], est[1])
                    cmd = _cmd_mark(est, range_line, slow=False)
                    if dist < range_line + 0.06 and abs(est[1]) < 0.07 and abs(math.atan2(est[1], est[0])) < 0.22:
                        mode, t_mode = "onto", sim.t
                    if dist < 0.28:
                        reason = "too_close"
                        break
            elif mode == "onto":
                close_enough = getattr(sim, "last_dist", 9.0) < 0.55
                if est is None:
                    cmd = (0.05, 0.0, 0.0)
                    if close_enough and sim.t - sim.seen_t > 0.8:
                        mode, t_mode = "turn", sim.t
                        imu_lock = sim.imu_yaw
                else:
                    dist = math.hypot(est[0], est[1])
                    cmd = _cmd_mark(est, range_sit, slow=True, y_goal=0.09)
                    bearing = abs(math.atan2(est[1] - 0.09, est[0]))
                    if dist < 0.46 and 0.02 < est[1] < 0.16 and bearing < 0.28:
                        mode, t_mode = "turn", sim.t
                        imu_lock = sim.imu_yaw
                if sim.t - t_mode > 16.0:
                    reason = "missed_line"
                    break
            elif mode == "turn":
                # Face the room. The mark was ahead, so a half turn uses the
                # gyro from the moment the mark was centred. A pure yaw command
                # on this policy walks a leftward arc. The small vx and vy
                # oppose that arc. Tuned on one centred sim pass. The image
                # is not used once the turn starts.
                turned = wrap(sim.imu_yaw - imu_lock)
                # Stop short of a full half turn so wrap does not flip the sign
                # at exactly pi. 2.9 rad still faces the room.
                err = wrap(2.85 - turned)
                hist = getattr(sim, "_turn_hist", [])
                hist.append((sim.t, turned))
                sim._turn_hist = hist
                recent = [a for a in hist if sim.t - a[0] < 0.45]
                stalled = len(recent) >= 8 and abs(recent[-1][1] - recent[0][1]) < 0.06
                if abs(err) < 0.22 or (stalled and abs(turned) > 2.15):
                    mode, t_mode = "settle", sim.t
                else:
                    wz = float(np.clip(1.2 * err, -0.50, 0.50))
                    # A left turn on this policy drifts to +y. vy opposes that.
                    cmd = (0.02, -0.06 if wz >= 0 else 0.06, wz)
                if sim.t - t_mode > 9.0:
                    mode = "sit"
                    break
            elif mode == "settle":
                cmd = (0.0, 0.0, 0.0)
                if sim.t - t_mode > 0.6:
                    mode = "sit"
            if mode == "sit":
                break
            speed = math.hypot(sim.data.qvel[0], sim.data.qvel[1])
            blur = speed > 0.12 or abs(sim.data.qvel[5]) > 0.7
            sim.step_policy(cmd, capture=capture, blur=blur)
            k += 1
            if os.environ.get("CAM_DOCK_DEBUG") and k % 25 == 0:
                tp = sim.true_pose()
                print("t=%.1f %s cmd %s true %.2f %.2f %.0f est %s" % (
                    sim.t, mode, tuple(round(c, 2) for c in cmd), tp[0], tp[1], math.degrees(tp[2]),
                    None if est is None else tuple(round(v, 3) for v in est[:3])), flush=True)
        if sim.fallen:
            reason = "fell"
        sat = False
        if not sim.fallen and mode == "sit":
            target = _sit_targets(sim.model, sim.m)
            sim.go_pose(target, 3.2)
            sim.torque_off(1.6)
            if sim.fallen:
                reason = "fell"
            else:
                sat = True
                reason = "sat"
        x, y, yaw, z, up = sim.true_pose()
        scored = score_wells(x, y, yaw)
        ok = bool(sat and scored["contacts_meet"] and not sim.fallen)
        if ok:
            reason = "docked"
        elif sat and not scored["contacts_meet"]:
            reason = "sat_off_stripes"
        out = dict(
            seed=int(seed),
            start=[round(x0, 3), round(y0, 3), round(math.degrees(yaw0), 1)],
            light=round(float(light), 2),
            gain=round(float(sim.gain), 2),
            ok=ok,
            reason=reason,
            t_s=round(sim.t, 2),
            fell=bool(sim.fallen),
            saw=bool(sim.saw),
            sat=bool(sat),
            true=[round(x, 3), round(y, 3), round(math.degrees(yaw), 1), round(z, 3)],
            **scored,
        )
        frames = list(sim.frames) if record else []
        return out, frames
    finally:
        sim.close()


STARTS = [
    # metres and degrees. Varied room positions, headings, and light.
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
]


def batch(n=10, record=False, limit_s=48.0):
    rows = []
    success_frames = None
    fail_frames = None
    for seed, x, y, yaw_deg, light in STARTS[:n]:
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
        _place(sim, -1.10, 0.04, 0.0)
        for _ in range(8):
            sim.step_policy((0.0, 0.0, 0.0), capture=False)
        est = sim._capture(False)
        if est is None:
            return dict(ran=True, ok=False, camera="short", note="the short check did not see the mark")
        rt = sim.data.xmat[sim.trunk].reshape(3, 3)
        pt = sim.data.xpos[sim.trunk]
        truth = rt.T @ (np.array([MARK_FACE_X, 0.0, MARK_Z]) - pt)
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
    a("Mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER.")
    a("")
    a("Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.")
    a("")
    rate = summary["rate"]
    a("Batch: %d of %d docks put one well fully on plus and one fully on minus (sim pass only). Rate %.2f." % (summary["ok"], summary["n"], rate if rate is not None else 0))
    if summary["align_mm_median"] is not None:
        a("On the docks that met, the seat centre was a median %.1f mm from the sun and at most %.1f mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least %.2f mm (calc only on the scored pose)." % (
            summary["align_mm_median"], summary["align_mm_max"], summary["margin_mm_min"] or 0))
        a("Time to dock, median %.1f s, max %.1f s (sim pass only)." % (summary["time_s_median"], summary["time_s_max"]))
    if summary["failures"]:
        bits = ", ".join("%s %d" % (k, v) for k, v in sorted(summary["failures"].items()))
        a("Failures: %s." % bits)
    else:
        a("No failure in this batch.")
    a("")
    a("A meet is geometry. The well circle lies inside one foil stripe, and the two poles both occur. Contact resistance on foil, with dust, is still BLOCKER. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.")
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
