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
WORK_LONG = 640


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


def _exposure(img):
    """Scale the 95th percentile toward mid white.

    Stand-in for the module's auto exposure. Sim pass only when the frame
    is rendered. The brief does not give the libcamera loop.
    """
    bright = float(np.percentile(img, 95))
    scale = 200.0 / max(bright, 12.0)
    return np.clip(img.astype(np.float32) * scale, 0, 255)


def _scores(img):
    """Yellow score and chromaticity. A gain scales the score, so cuts are relative."""
    r = img[:, :, 0]
    g = img[:, :, 1]
    b = img[:, :, 2]
    s = r + g + b + 1.0
    rn = r / s
    gn = g / s
    bn = b / s
    score = (r + g) * 0.5 - b
    val = (r + g + b) / 3.0
    warm = (score > 22.0) & (rn > bn + 0.08) & (rn > 0.34) & (rn + 0.08 > gn)
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
    for gap in (8.0, 16.0, 28.0, 44.0):
        gold = warm & (score >= top - gap)
        disc = _best_disc(gold, h, w)
        if disc is None:
            continue
        if best is None or disc[0] > best[0]:
            best = disc
            best_gold = gold
        # A real disc sits on the yellow peak. The ring is a step below it.
        med = float(np.median(score[disc[2], disc[1]]))
        if med >= top - 18.0 and disc[3] < 0.55 * w:
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


def _ring(pale, u, v, radius_px, h, w):
    """Pale cloth on both sides of the disc, out where the ring sits.

    The ring's outer radius is 4.7 times the disc radius (235 / 50, CAD
    check only). A floor disc is foreshortened, so the vertical test is
    loose. The wall cut removes the far side. Left and right should remain.
    """
    if radius_px < 2.0:
        return 0.0, False
    r_in = 1.5 * radius_px
    r_out = 5.2 * radius_px
    yy, xx = np.ogrid[:h, :w]
    dx = xx - u
    dy = (yy - v) / 0.55
    rho = np.hypot(dx, dy)
    band = pale & (rho > r_in) & (rho < r_out)
    outer = pale & (rho >= r_out)
    left = int(band[:, : int(max(0, math.floor(u)))].sum()) if u > 1 else 0
    right = int(band[:, int(min(w - 1, math.ceil(u))):].sum()) if u < w - 1 else 0
    band_n = int(band.sum())
    band_frac = float(band.mean()) if band.size else 0.0
    outer_frac = float(outer.mean()) if outer.size else 0.0
    # The ring is pale cloth in that annulus, not a yellow cast on the whole floor.
    both = left >= 8 and right >= 8 and band_frac > 0.01 and band_frac > outer_frac * 2.2
    frac = 0.0
    if band_n > 0:
        frac = min(left, right) / float(band_n)
    return frac, bool(both)


def _hazards(val, h, w):
    """Dark band as a cliff edge, dark compact blob as an obstacle.

    The floor model is not a drop. This is the pixel test only.
    """
    dark = val < 48.0
    cliff = False
    y1 = int(h * 0.45)
    x0 = int(w * 0.28)
    x1 = int(w * 0.72)
    region = dark[y1:, x0:x1]
    if region.size:
        row = region.mean(axis=1)
        # A dark band across the middle of the lower frame. A mark at the side is not this.
        cliff = bool(np.any(row > 0.55))
    obstacle = False
    obstacle_u = None
    # Ignore a full-width band. That is the cliff test, not a blob.
    body = dark.copy()
    # Wall fixtures sit above the floor. An obstacle is a blob on the floor,
    # in the bottom of the frame.
    body[: int(h * 0.62), :] = False
    for xs, ys, n in _blobs(body, 36):
        bw = int(xs.max() - xs.min()) + 1
        bh = int(ys.max() - ys.min()) + 1
        if bw > 0.55 * w:
            continue
        aspect = bw / float(max(bh, 1))
        if not 0.25 <= aspect <= 3.0:
            continue
        extent = n / float(bw * bh)
        if extent < 0.35:
            continue
        obstacle = True
        obstacle_u = float(xs.mean())
        break
    return cliff, obstacle, obstacle_u


def find_nest(img, fx, fy, cx, cy):
    """One frame in, one estimate out. img is HxWx3 RGB uint8.

    range is not in this dict. sun_in_trunk turns the pixel width into metres.
    """
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    img, fx, fy, cx, cy, stride = _bin(np.asarray(img), float(fx), float(fy), float(cx), float(cy))
    h, w = img.shape[:2]
    shown = _exposure(img)
    score, warm, val = _scores(shown)
    disc, gold = _pick_disc(score, warm, h, w)
    pale = warm if gold is None else (warm & ~gold)
    cliff, obstacle, obstacle_u = _hazards(val, h, w)
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
        "obstacle_u": None if obstacle_u is None else obstacle_u * stride,
        "stride": stride,
        "work_w": w,
        "work_h": h,
    }
    if disc is None:
        return out
    _, xs, ys, bw, bh, clipped, x0, y0, x1, y1 = disc
    u = float(xs.mean())
    v = float(ys.mean())
    frac, ring = _ring(pale, u, v, bw / 2.0, h, w)
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
    out.update(
        {
            "seen": True,
            "clipped": bool(clipped),
            "u": u * stride,
            "v": v * stride,
            "width_px": None if width is None else width * stride,
            "ring_width_px": None if ring_w is None else ring_w * stride,
            "ring": bool(ring),
            "ring_frac": round(float(frac), 3),
            "occluded": bool(clipped or not ring),
            "box": (x0 * stride, y0 * stride, x1 * stride, y1 * stride),
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
