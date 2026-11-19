"""One dock-camera frame for the fit check.

The size is the render size in twin/dock/camera/camera_dock.py (400 by 695).
The picture is a gray room, one dark square, and a yellow patch. That is the
shape detect() looks for. It is not a photograph and not a MuJoCo frame.
"""

from __future__ import annotations


def dock_frame(np):
    img = np.full((695, 400, 3), 140, dtype=np.uint8)
    y0, x0, side = 180, 140, 90
    img[y0 : y0 + side, x0 : x0 + side] = (18, 18, 18)
    img[y0 + 8 : y0 + 32, x0 + 18 : x0 + 70] = (220, 190, 40)
    return img
