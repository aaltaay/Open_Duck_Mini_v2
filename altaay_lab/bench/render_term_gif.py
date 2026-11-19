#!/usr/bin/env python3
"""Draw a terminal-style GIF of a mock day-one bench run.

The frames are the script's own stdout, with a 'mock hardware' label.
Output stays under 5 MB. This file is the recorder. The GIF is not
committed (lab rule: heavy files stay out of git).
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def capture(imu_reads):
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            [sys.executable, str(HERE / "day_one.py"), "--mock", "--out", tmp, "--imu-reads", str(imu_reads)],
            capture_output=True, text=True, check=False,
        )
    text = r.stdout
    if r.returncode != 0:
        text += "\n" + r.stderr
    return r.returncode, text


def render(text, dest, cols=76, rows=22):
    from PIL import Image, ImageDraw, ImageFont

    font_path = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"
    try:
        font = ImageFont.truetype(font_path, 14)
    except OSError:
        font = ImageFont.load_default()
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    bbox = probe.textbbox((0, 0), "M", font=font)
    cw = max(1, bbox[2] - bbox[0])
    ch = max(1, bbox[3] - bbox[1])
    pad = 8
    header = ch + 12
    small_w = cols * cw + pad * 2
    small_h = header + rows * (ch + 3) + pad
    lines = text.splitlines() or ["(no output)"]
    starts = list(range(0, max(1, len(lines) - rows + 1), 3))
    last = max(0, len(lines) - rows)
    if not starts or starts[-1] != last:
        starts.append(last)
    frames = []
    for start in starts:
        img = Image.new("RGB", (small_w, small_h), (20, 24, 28))
        draw = ImageDraw.Draw(img)
        draw.text((pad, 6), "mock hardware", fill=(240, 190, 80), font=font)
        y = header
        for line in lines[start:start + rows]:
            if "FAIL" in line:
                color = (220, 90, 90)
            elif "PASS" in line or line.startswith("OK"):
                color = (120, 200, 140)
            else:
                color = (220, 224, 220)
            draw.text((pad, y), line[:cols], fill=color, font=font)
            y += ch + 3
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=16))
    frames[0].save(
        dest, save_all=True, append_images=frames[1:], duration=140, loop=0, optimize=True,
    )
    return dest.stat().st_size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--imu-reads", type=int, default=8)
    args = ap.parse_args(argv)
    code, text = capture(args.imu_reads)
    if "mock hardware" not in text:
        print(text)
        raise SystemExit("capture was not labeled mock hardware")
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = render(text, dest)
    print("wrote %s (%d bytes), bench exit %d" % (dest, size, code))
    if size > 5_000_000:
        raise SystemExit("gif is over 5 MB")
    return code


if __name__ == "__main__":
    sys.exit(main())
