"""Compressed-day picture of the autonomy soak. Sim pass only.

720p, labeled SIM. The duck and the nest are drawings. They are not the CAD
and not a MuJoCo frame. The trace is the supervisor's first simulated day.
"""

from __future__ import annotations

import os
import subprocess

W, H = 1280, 720
FPS = 20
SECONDS = 36

MODE_COLOR = {
    "wander": (70, 130, 180),
    "social": (60, 150, 90),
    "dock": (200, 140, 40),
    "charge": (40, 160, 90),
    "nap": (90, 90, 140),
    "knee_rest": (180, 90, 60),
    "sit": (120, 110, 90),
    "getup": (160, 80, 80),
    "stuck": (180, 40, 40),
}


def _font(size):
    from PIL import ImageFont
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    )
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _at(samples, t):
    if not samples:
        return {"t": 0, "mode": "wander", "expression": "settle", "pack_v": 12.5, "knee_c": 22.0, "camera": None}
    if t <= samples[0]["t"]:
        return samples[0]
    if t >= samples[-1]["t"]:
        return samples[-1]
    lo, hi = 0, len(samples) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if samples[mid]["t"] <= t:
            lo = mid
        else:
            hi = mid
    return samples[lo]


def _clock(t):
    t = int(t)
    h = (t // 3600) % 24
    m = (t % 3600) // 60
    return "%02d:%02d" % (h, m)


def write_day(samples, path):
    from PIL import Image, ImageDraw
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frames = FPS * SECONDS
    span = 86400.0
    font = _font(36)
    small = _font(28)
    badge = _font(54)
    raw = subprocess.Popen(
        [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "28", "-preset", "veryfast", "-movflags", "+faststart",
            path,
        ],
        stdin=subprocess.PIPE,
    )
    try:
        for i in range(frames):
            t = span * (i / max(1, frames - 1))
            row = _at(samples, t)
            image = Image.new("RGB", (W, H), (244, 239, 228))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 460, W, H), fill=(196, 176, 140))
            # Gold-dome nest, nest v2 stripes. A drawing, not the CAD.
            for k, x in enumerate(range(980, 1220, 28)):
                color = (212, 168, 48) if k % 2 == 0 else (232, 214, 160)
                draw.rectangle((x, 500, x + 22, 640), fill=color)
            draw.rectangle((1040, 470, 1160, 508), fill=(40, 40, 40))
            draw.text((1052, 476), "NEST", fill=(230, 190, 70), font=small)
            mode = row["mode"]
            if mode in ("dock", "charge"):
                dx = 1080
            elif mode == "stuck":
                dx = 640
            elif mode == "nap":
                dx = 280
            elif mode == "social":
                dx = 420
            else:
                dx = 220 + int(180 * (0.5 + 0.5 * ((i // 8) % 2)))
            dy = 430 if mode != "nap" else 470
            body = MODE_COLOR.get(mode, (80, 80, 80))
            draw.ellipse((dx - 46, dy - 30, dx + 46, dy + 50), fill=body)
            draw.ellipse((dx - 28, dy - 78, dx + 28, dy - 22), fill=(250, 248, 240))
            # Eyes stay white. Help is the bright pair.
            eye = (255, 255, 255)
            r = 8 if row["expression"] == "help_me" else 5
            draw.ellipse((dx - 16, dy - 62, dx - 16 + r, dy - 62 + r), fill=eye, outline=(20, 20, 20))
            draw.ellipse((dx + 6, dy - 62, dx + 6 + r, dy - 62 + r), fill=eye, outline=(20, 20, 20))
            if row["expression"] == "help_me":
                draw.line((dx - 34, dy - 90, dx - 8, dy - 78), fill=(180, 40, 40), width=4)
                draw.line((dx + 34, dy - 90, dx + 8, dy - 78), fill=(180, 40, 40), width=4)
            draw.rectangle((0, 0, 220, 78), fill=(170, 30, 30))
            draw.text((18, 8), "SIM", fill=(255, 255, 255), font=badge)
            draw.text((24, 88), "sim pass only", fill=(80, 40, 30), font=small)
            draw.text((24, 124), "compressed day", fill=(80, 40, 30), font=small)
            draw.text((24, 168), _clock(t), fill=(30, 30, 30), font=font)
            cam = row["camera"] or ""
            line = "%s  %s" % (mode, row["expression"])
            if cam:
                line = "%s  %s" % (line, cam)
            draw.text((24, 640), line, fill=(20, 20, 20), font=font)
            draw.text((24, 680), "pack %.2f V   knee %.0f C" % (row["pack_v"], row["knee_c"]), fill=(20, 20, 20), font=small)
            raw.stdin.write(image.tobytes())
    finally:
        raw.stdin.close()
        code = raw.wait()
    if code != 0:
        raise RuntimeError("ffmpeg exited %s" % code)
    return path
