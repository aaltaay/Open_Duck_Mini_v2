"""Find the nest cloth in one head-camera frame.

The target is the 100 mm golden cloth disc and the pale gold ring
(radius 82 mm to 235 mm, cut on the wall side). Those sizes are the nest
CAD (twin/dock/nest/cad/nestcad_lib.py, CAD check only). The files in
cad/nest_v2 are not read and not written.

The frame is RGB, y down, and it keeps the full field of the standard
Camera Module 3: 66 deg on the long image axis and 41 deg on the short one
(product brief June 2024, RP-008151-DS-1, page 5, cited). On this head the
long axis is up and down (twin/camera/CAMERA_TWIN.md).

A still is 4608 by 2592 (cited, same brief, page 3). This function bins any
longer side above 640 so a full still does not run at full size. The bin
keeps the whole field. Whether a 1080p mode crops that field is still
BLOCKER (CAMERA_TWIN.md).

No world pose. The trunk numbers come from the image and from the camera
chain the caller passes in (the head joints).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

# CAD check only, nestcad_lib.py. Metres.
SUN_D_M = 0.100
SUN_R_M = 0.050
RING_R0_M = 0.082
RING_R1_M = 0.235

# Set point. Longer than this, the frame is binned. Not a camera mode.
# 360 keeps the dock frame (556 tall) at stride 2. The unit stills are shorter
# and stay full size.
WORK_LONG = 360


def intrinsics(w, h, fov_up_deg=66.0):
    """Pixels per radian. Height is the 66 deg axis. Calc only."""
    fy = (h / 2.0) / math.tan(math.radians(fov_up_deg) / 2.0)
    hfov = 2.0 * math.atan(math.tan(math.radians(fov_up_deg) / 2.0) * (w / float(h)))
    fx = (w / 2.0) / math.tan(hfov / 2.0)
    return fx, fy, (w - 1) / 2.0, (h - 1) / 2.0, math.degrees(hfov)


def _bin(img, fx, fy, cx, cy):
    h, w = img.shape[:2]
    long = max(h, w)
    if long <= WORK_LONG:
        return img, fx, fy, cx, cy, 1
    stride = int(math.ceil(long / float(WORK_LONG)))
    img = np.ascontiguousarray(img[::stride, ::stride])
    return img, fx / stride, fy / stride, cx / stride, cy / stride, stride


def _white_balance(img):
    """Gray-world balance. A global lamp color divides out. Calc only on the means."""
    x = img.astype(np.float32)
    mean = x[::4, ::4].reshape(-1, 3).mean(axis=0)
    scale = float(np.mean(mean)) / np.maximum(mean, 6.0)
    return np.clip(x * scale.reshape(1, 1, 3), 0, 255)


def _exposure(img):
    """Scale the 95th percentile toward mid white.

    Stand-in for the module's auto exposure. Sim pass only when the frame
    is rendered. The brief does not give the libcamera loop.
    """
    bright = float(np.percentile(img, 95))
    scale = 200.0 / max(bright, 12.0)
    return np.clip(img.astype(np.float32) * scale, 0, 255)


def _scores(img):
    """Chromaticity after white balance. A gain and a lamp color both drop out.

    The score is red-minus-blue share, not raw RGB. Green felt stays out
    because its green share is above its red share.
    """
    r = img[:, :, 0]
    g = img[:, :, 1]
    b = img[:, :, 2]
    s = r + g + b + 1.0
    rn = r / s
    gn = g / s
    bn = b / s
    # Yellow, not the red charge lamp: red and green shares stay close,
    # and both beat blue. Chromaticity, so a gain does not move the cut.
    score = (rn + gn) * 0.5 - bn
    val = (r + g + b) / 3.0
    warm = (score > 0.05) & (gn > 0.24) & (rn > 0.26) & (np.abs(rn - gn) < 0.16) & (val > 28.0)
    return score, warm, val


def _pick_disc(score, warm, h, w):
    """Tightest yellow cut that still looks like a disc.

    The disc is the peak. The ring is the same hue and dimmer, and a warm
    lamp pulls the floor up, so one global cut merges them. Trying a few
    gaps under the warm peak keeps the disc when the ring touches it.
    """
    n = int(warm.sum())
    if n < 40:
        return None, None
    top = float(np.percentile(score[warm], 90))
    best = None
    best_gold = None
    # Chromaticity lives near 0 to 0.5, so the gaps are shares, not RGB counts.
    for gap in (0.03, 0.07, 0.14, 0.24):
        gold = warm & (score >= top - gap)
        disc = _best_disc(gold, h, w)
        if disc is None:
            continue
        if best is None or disc[0] > best[0]:
            best = disc
            best_gold = gold
        # A real disc sits on the yellow peak. The ring is a step below it.
        med = float(np.median(score[disc[2], disc[1]]))
        if med >= top - 0.05 and disc[3] < 0.55 * w:
            return disc, gold
    return best, best_gold


def _blobs(mask, min_n):
    if int(mask.sum()) < min_n:
        return []
    lab, n = ndimage.label(mask)
    if n <= 0:
        return []
    counts = np.bincount(lab.ravel())
    out = []
    for i in range(1, n + 1):
        if counts[i] < min_n:
            continue
        ys, xs = np.nonzero(lab == i)
        out.append((xs, ys, int(counts[i])))
    return out


def _best_disc(gold, h, w):
    best = None
    for xs, ys, n in _blobs(gold, 24):
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        bw = x1 - x0 + 1
        bh = y1 - y0 + 1
        # On the 320-wide dock frame a real disc is about 30 px at 1.5 m
        # (calc only). A smaller peak is a ring chip or a specular speck.
        min_w = 16 if w >= 280 else 8
        if bw < min_w or bh < 3:
            continue
        if bw > 0.72 * w:
            continue
        # A flat disc on the floor is a wide ellipse. At 2 m the vertical
        # axis is about a fifth of the left-right axis (calc only, camera
        # height near 0.38 m).
        aspect = bw / float(bh)
        if not 0.22 <= aspect <= 6.5:
            continue
        extent = n / float(bw * bh)
        if extent < 0.55:
            continue
        edge = x0 <= 1 or x1 >= w - 2
        if edge:
            continue
        # The close disc leaves through the bottom of the frame. The left-right
        # width is then not the diameter.
        clipped = y1 >= h - 2
        score = extent * min(bw, bh)
        if best is None or score > best[0]:
            best = (score, xs, ys, bw, bh, clipped, x0, y0, x1, y1)
    return best


def _ring_side(val, score, band, outer):
    """One side of the cloth against the floor just outside it.

    Value catches a warm lamp, which washes the pale ring to gray after
    the white balance. Chromaticity catches day and dim light, where the
    cloth and the floor have almost the same brightness. Either step is
    enough. The cuts are set points from stills of the four rooms.
    """
    if int(band.sum()) < 12 or int(outer.sum()) < 12:
        return False, 0.0
    dv = float(val[band].mean()) - float(val[outer].mean())
    dc = float(score[band].mean()) - float(score[outer].mean())
    ok = dv >= 5.0 or dc >= 0.018
    return ok, max(dv, 0.0)


def _ring_angle(band):
    """Major-axis angle of the ring, radians, 0 when it lies left to right.

    A circle on the floor, seen by the pitched head, is wide left to right
    when the duck faces the disc. A yaw tilts that axis. None if the band
    is too thin to fit.
    """
    ys, xs = np.nonzero(band)
    if xs.size < 40:
        return None
    x = xs.astype(np.float64) - float(xs.mean())
    y = ys.astype(np.float64) - float(ys.mean())
    mxx = float((x * x).mean())
    myy = float((y * y).mean())
    mxy = float((x * y).mean())
    return 0.5 * math.atan2(2.0 * mxy, mxx - myy)


def _ring_geom(val, score, u, v, radius_px, h, w):
    """The disc sits inside a local ring of cloth.

    The comparison is a tight annulus around the disc against the floor
    just outside that annulus, and only inside a window around the disc.
    The rest of the frame (wall, window, lamp) is not the floor. A yellow
    floor blob has no step at this radius.
    """
    if radius_px < 2.0:
        return 0.0, False, False, None
    r = float(radius_px)
    rad = int(9.0 * r) + 2
    x0 = max(0, int(u) - rad)
    x1 = min(w, int(u) + rad + 1)
    y0 = max(0, int(v) - rad)
    y1 = min(h, int(v) + rad + 1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return 0.0, False, False, None
    val_c = val[y0:y1, x0:x1]
    score_c = score[y0:y1, x0:x1]
    hc, wc = val_c.shape
    uc = float(u) - x0
    vc = float(v) - y0
    yy, xx = np.ogrid[:hc, :wc]
    rho = np.hypot(xx - uc, (yy - vc) / 0.55)
    band = (rho > 2.0 * r) & (rho < 4.4 * r)
    outer = (rho > 5.2 * r) & (rho < 8.5 * r)
    left_ok, left_gap = _ring_side(val_c, score_c, band & (xx < uc), outer & (xx < uc))
    right_ok, right_gap = _ring_side(val_c, score_c, band & (xx > uc), outer & (xx > uc))
    full = left_ok and right_ok
    partial = left_ok or right_ok
    gap = max(left_gap, right_gap)
    frac = 0.0
    if gap > 0.0 and (left_ok and right_ok):
        frac = min(left_gap, right_gap) / max(gap, 1.0)
    elif partial:
        frac = 0.5
    # The annulus above is only where we look. The angle comes from the
    # cloth pixels inside it. The annulus itself is axis-aligned, so its
    # own shape is not a yaw.
    cloth = np.zeros_like(band)
    if int(outer.sum()) >= 12:
        floor_c = float(score_c[outer].mean())
        floor_v = float(val_c[outer].mean())
        cloth = band & ((score_c > floor_c + 0.012) | (val_c > floor_v + 4.0))
    return frac, bool(full), bool(partial), _ring_angle(cloth)


def _hazards(val, h, w):
    """A thin dark edge is a cliff. A compact dark blob on the floor is an obstacle.

    Cuts are relative to the frame median, so a dim room that auto-exposure
    has lifted does not paint the whole floor as a cliff. The floor model is
    not a drop. This is the pixel test only.
    """
    med = float(np.median(val))
    dark = val < max(20.0, 0.40 * med)
    cliff = False
    y1 = int(h * 0.55)
    x0 = int(w * 0.30)
    x1 = int(w * 0.70)
    region = dark[y1:, x0:x1]
    if region.size:
        row = region.mean(axis=1)
        dark_rows = row > 0.62
        n_dark = int(dark_rows.sum())
        # A real edge is a few rows. A dim lower half is not.
        if 0 < n_dark <= max(3, int(0.14 * len(row))):
            idx = int(np.argmax(dark_rows))
            above = val[max(0, y1 + idx - 8): y1 + idx, x0:x1]
            if above.size and float(above.mean()) > 0.72 * med:
                cliff = True
    obstacle = False
    obstacle_u = None
    body = dark.copy()
    body[: int(h * 0.62), :] = False
    for xs, ys, n in _blobs(body, 48):
        bw = int(xs.max() - xs.min()) + 1
        bh = int(ys.max() - ys.min()) + 1
        if bw > 0.45 * w or bh < 8:
            continue
        aspect = bw / float(max(bh, 1))
        if not 0.35 <= aspect <= 2.6:
            continue
        extent = n / float(bw * bh)
        if extent < 0.45:
            continue
        if float(val[ys, xs].mean()) > 0.32 * med:
            continue
        obstacle = True
        obstacle_u = float(xs.mean())
        break
    return cliff, obstacle, obstacle_u


def find_nest(img, fx, fy, cx, cy, roi=None):
    """One frame in, one estimate out. img is HxWx3 RGB uint8.

    range is not in this dict. sun_in_trunk turns the pixel width into metres.
    roi is (u, v, radius) in the same pixels as img. After a fix, the caller
    passes the last disc so the next frame skips the rest of the picture.
    A miss clears it. The crop is not a camera mode.
    """
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    img = np.asarray(img)
    # Hazards use the whole field. The window is only for the disc.
    full = img
    full_fx, full_fy, full_cx, full_cy = float(fx), float(fy), float(cx), float(cy)
    ox = oy = 0
    if roi is not None:
        ru, rv, rad = roi
        h0, w0 = img.shape[:2]
        x0 = max(0, int(ru - rad))
        y0 = max(0, int(rv - rad))
        x1 = min(w0, int(ru + rad))
        y1 = min(h0, int(rv + rad))
        if x1 - x0 > 48 and y1 - y0 > 48:
            img = img[y0:y1, x0:x1]
            cx = float(cx) - x0
            cy = float(cy) - y0
            ox, oy = x0, y0
    img, fx, fy, cx, cy, stride = _bin(img, float(fx), float(fy), float(cx), float(cy))
    h, w = img.shape[:2]
    shown = _exposure(_white_balance(img))
    score, warm, val = _scores(shown)
    disc, gold = _pick_disc(score, warm, h, w)
    pale = warm
    if disc is not None:
        keep = pale.copy()
        keep[disc[2], disc[1]] = False
        pale = keep
    if ox or oy:
        haz, _, _, _, _, haz_stride = _bin(full, full_fx, full_fy, full_cx, full_cy)
        haz_shown = _exposure(_white_balance(haz))
        _, _, haz_val = _scores(haz_shown)
        hh, hw = haz_val.shape
        cliff, obstacle, obstacle_u = _hazards(haz_val, hh, hw)
        haz_ox, haz_oy, stride_h = 0, 0, haz_stride
    else:
        cliff, obstacle, obstacle_u = _hazards(val, h, w)
        haz_ox, haz_oy, stride_h = ox, oy, stride
    out = {
        "seen": False,
        "clipped": False,
        "u": None,
        "v": None,
        "width_px": None,
        "ring": False,
        "ring_frac": 0.0,
        "occluded": False,
        "cliff": cliff,
        "obstacle": obstacle,
        "obstacle_u": None if obstacle_u is None else obstacle_u * stride_h + haz_ox,
        "stride": stride,
        "work_w": w,
        "work_h": h,
    }
    if disc is None:
        return out
    _, xs, ys, bw, bh, clipped, x0, y0, x1, y1 = disc
    u = float(xs.mean())
    v = float(ys.mean())
    # A dark chip of the nest (the charger pad, the disc shadow) is not a
    # side hazard. A real obstacle sits away from the disc.
    if ox or oy:
        nest_u = None if obstacle_u is None else (obstacle_u * stride_h + haz_ox - ox) / max(stride, 1)
    else:
        nest_u = obstacle_u
    if nest_u is not None and abs(float(nest_u) - u) < 1.15 * max(float(bw), 8.0):
        obstacle = False
        obstacle_u = None
        out["obstacle"] = False
        out["obstacle_u"] = None
    frac, ring, partial, ring_yaw = _ring_geom(val, score, u, v, bw / 2.0, h, w)
    ring_w = None
    y_a = max(0, int(y0) - int(bh))
    y_b = min(h, int(y1) + int(bh) + 1)
    cols = np.where(pale[y_a:y_b].any(axis=0))[0]
    if len(cols) > 8:
        span = int(cols[-1] - cols[0] + 1)
        if bw * 1.8 < span < w * 0.92:
            ring_w = span
    # A clipped disc hides part of the width. Do not turn that into a range.
    width = float(bw) if not clipped else None
    # Disc inside a ring, and a pinhole size a nest at 0.25 m to 1.8 m would have.
    # Farther than 1.8 m the disc is a chip of the cloth (about half the real
    # width) and the range comes out near 2 m. Those chips are not the disc.
    # A pale span that is the floor, not the ring, is ignored.
    depth = SUN_D_M * float(fx) / max(float(bw), 1.0)
    size_ok = 0.25 <= depth <= 1.8
    if ring_w is not None:
        ratio = ring_w / max(float(bw), 1.0)
        if not 2.0 <= ratio <= 6.8:
            ring_w = None
    if not (partial and size_ok):
        return out
    out.update(
        {
            "seen": True,
            "clipped": bool(clipped),
            "u": u * stride + ox,
            "v": v * stride + oy,
            "width_px": None if width is None else width * stride,
            "ring_yaw": None if ring_yaw is None else round(float(ring_yaw), 4),
            "ring_width_px": None if ring_w is None else ring_w * stride,
            "ring": bool(ring),
            "ring_frac": round(float(frac), 3),
            "occluded": bool(clipped or not ring),
            "box": (x0 * stride + ox, y0 * stride + oy, x1 * stride + ox, y1 * stride + oy),
        }
    )
    return out


def sun_in_trunk(u, v, width_px, fx, fy, cx, cy, r_cam_trunk, p_cam_trunk, ring_width_px=None):
    """Disc centre in the trunk frame, metres.

    The left-right pixel width is the disc diameter at the optical depth
    (calc only). r_cam_trunk maps camera axes (x right, y up, z back) into
    the trunk. p_cam_trunk is the lens opening in the trunk, from the head
    joints, not from the nest.
    """
    if width_px is None or width_px < 1.5 or fx <= 1.0:
        return None
    # The ring's outer diameter is 470 mm (CAD check only). It is a wider
    # ruler than the disc when the pale cloth is actually in frame.
    depth = SUN_D_M * float(fx) / float(width_px)
    if ring_width_px and ring_width_px > float(width_px) * 1.8 and ring_width_px < float(fx) * 1.4:
        other = (RING_R1_M * 2.0) * float(fx) / float(ring_width_px)
        # Use the ring only when it agrees. A wide pale floor is not the ring.
        if abs(other - depth) / depth < 0.08:
            depth = 0.5 * (depth + other)
    if depth < 0.12 or depth > 4.0:
        return None
    x = depth * (float(u) - float(cx)) / float(fx)
    y = depth * (float(cy) - float(v)) / float(fy)
    p_cam = np.array([x, y, -depth], dtype=float)
    r = np.asarray(r_cam_trunk, dtype=float).reshape(3, 3)
    p = np.asarray(p_cam_trunk, dtype=float).reshape(3)
    trunk = r @ p_cam + p
    return {
        "sun_fwd": float(trunk[0]),
        "sun_left": float(trunk[1]),
        "sun_up": float(trunk[2]),
        "depth_m": float(depth),
    }
