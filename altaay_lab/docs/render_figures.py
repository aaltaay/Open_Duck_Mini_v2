#!/usr/bin/env python3
"""Render small figures for the build guide and the owner's manual.

Reads the nest v2 STL meshes already in the repo and draws:
  images/nest_mat_top.png   top view of the mat meshes (CAD check only)
  images/gold_domes.png     flush well mesh, plus the cited 0.9 mm dome
  images/owners_page.png    first page of OWNERS_MANUAL.md

Does not write into cad/nest_v2/renders/. Does not change a mesh.
"""
import os
import struct

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
STL = os.path.join(LAB, "cad", "nest_v2", "stl")
OUT = os.path.join(HERE, "images")


def load_stl(path):
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"\x00" not in data[:80]:
        raise SystemExit("ASCII STL is not expected: %s" % path)
    count = struct.unpack_from("<I", data, 80)[0]
    need = 84 + count * 50
    if need != len(data):
        raise SystemExit("STL size mismatch %s: %d bytes, count %d" % (path, len(data), count))
    tris = []
    off = 84
    for _ in range(count):
        nums = struct.unpack_from("<12fH", data, off)
        verts = [(nums[3], nums[4], nums[5]), (nums[6], nums[7], nums[8]), (nums[9], nums[10], nums[11])]
        tris.append(verts)
        off += 50
    return tris


def font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def bounds_xy(groups):
    xs, ys = [], []
    for tris in groups:
        for tri in tris:
            for x, y, _z in tri:
                xs.append(x)
                ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def project(mapper, tri):
    return [mapper(x, y) for x, y, _z in tri]


def fill_tri(draw, pts, color):
    draw.polygon(pts, fill=color)


def render_mat():
    order = [
        ("felt_base.stl", (214, 196, 168)),
        ("felt_top.stl", (196, 176, 146)),
        ("stripe_minus.stl", (212, 184, 120)),
        ("stripe_plus.stl", (176, 112, 62)),
        ("cord_pocket.stl", (96, 108, 112)),
        ("cord_cap.stl", (70, 78, 84)),
    ]
    loaded = [(color, load_stl(os.path.join(STL, name))) for name, color in order]
    xmin, xmax, ymin, ymax = bounds_xy([tris for _c, tris in loaded])
    width, height = 1100, 820
    pad = 70
    span_x = xmax - xmin or 1.0
    span_y = ymax - ymin or 1.0
    scale = min((width - 2 * pad) / span_x, (height - 2 * pad - 40) / span_y)

    def mapper(x, y):
        # Wall is +x in the nest frame. Put the wall at the top of the page.
        px = pad + (y - ymin) * scale
        py = pad + (xmax - x) * scale
        return (px, py)

    im = Image.new("RGB", (width, height), (251, 248, 240))
    draw = ImageDraw.Draw(im)
    for color, tris in loaded:
        for tri in tris:
            fill_tri(draw, project(mapper, tri), color)
    title = font(22)
    small = font(16)
    draw.text((24, 18), "Nest v2 mat, from the STL meshes", fill=(40, 36, 32), font=title)
    draw.text((24, height - 58), "CAD check only. Wall at the top. Copper is plus, pale gold is minus.", fill=(40, 36, 32), font=small)
    draw.text((24, height - 34), "Not a hardware photo. Nest v3 to v5 are not this mat.", fill=(40, 36, 32), font=small)
    path = os.path.join(OUT, "nest_mat_top.png")
    im.save(path, optimize=True)
    return path


def render_domes():
    wells = load_stl(os.path.join(STL, "seat_wells.stl"))
    width, height = 1100, 720
    im = Image.new("RGB", (width, height), (251, 248, 240))
    draw = ImageDraw.Draw(im)
    title = font(22)
    small = font(16)
    draw.text((24, 16), "Duck-side contact: gold domes", fill=(40, 36, 32), font=title)

    xmin, xmax, ymin, ymax = bounds_xy([wells])
    pad_l, pad_t = 40, 70
    box_w, box_h = 480, 280
    span_x = xmax - xmin or 1.0
    span_y = ymax - ymin or 1.0
    scale = min((box_w - 20) / span_x, (box_h - 20) / span_y)

    def mapper(x, y):
        px = pad_l + 10 + (x - xmin) * scale
        py = pad_t + 10 + (ymax - y) * scale
        return (px, py)

    draw.rounded_rectangle((pad_l, pad_t, pad_l + box_w, pad_t + box_h), radius=8, outline=(80, 70, 60), width=2)
    for tri in wells:
        fill_tri(draw, project(mapper, tri), (186, 148, 64))
    draw.text((pad_l, pad_t + box_h + 12), "Left: seat_wells.stl, flush mesh.", fill=(40, 36, 32), font=small)
    draw.text((pad_l, pad_t + box_h + 34), "CAD check only. This mesh is not proud.", fill=(40, 36, 32), font=small)

    # Side view of one dome. 1.5 mm radius, 0.9 mm proud. Scale 80 px per mm.
    ox, oy = 700, 360
    ppm = 80.0
    radius = 1.5 * ppm
    proud = 0.9 * ppm
    seat_y = oy
    draw.line((620, seat_y, 1040, seat_y), fill=(90, 70, 50), width=4)
    draw.text((620, seat_y + 10), "seat face", fill=(40, 36, 32), font=small)
    # Spherical cap standing proud. Centre of the sphere is proud - radius below? 
    # A cap of height h on radius R has the sphere centre at (h - R) relative to the top,
    # or the base of the cap is on the seat and the crown is h above the seat.
    # Centre z = h - R relative to the seat plane if the cap sits on the plane
    # and the crown is at +h. For h=0.9 and R=1.5, centre is 0.6 mm below the seat.
    # The part above the seat is the cap.
    cx = 820
    cz = seat_y + (1.5 - 0.9) * ppm  # image y grows down, so centre is below the seat line
    # Draw the cap as a chord: pie above the seat line.
    bbox = (cx - radius, cz - radius, cx + radius, cz + radius)
    # Full circle in gold, then cover the part below the seat with the background.
    draw.ellipse(bbox, fill=(198, 154, 52), outline=(120, 84, 24))
    draw.rectangle((cx - radius - 2, seat_y, cx + radius + 2, cz + radius + 4), fill=(251, 248, 240))
    draw.line((620, seat_y, 1040, seat_y), fill=(90, 70, 50), width=4)
    crown = seat_y - proud
    draw.line((cx, seat_y, cx, crown), fill=(40, 36, 32), width=2)
    draw.text((cx + 8, (seat_y + crown) / 2 - 10), "0.9 mm proud", fill=(40, 36, 32), font=small)
    draw.text((620, 80), "Right: one dome, side view.", fill=(40, 36, 32), font=small)
    draw.text((620, 104), "1.5 mm radius, 0.9 mm proud.", fill=(40, 36, 32), font=small)
    draw.text((620, 128), "Cited size from SEAT_CONTACTS.md.", fill=(40, 36, 32), font=small)
    draw.text((620, 152), "Sim choice. Not a new mesh.", fill=(40, 36, 32), font=small)
    draw.text((24, height - 36), "Five domes, 12 mm apart. Flush wells charged 0 of 40. These domes charged 38 of 40. Sim pass only.", fill=(40, 36, 32), font=small)
    path = os.path.join(OUT, "gold_domes.png")
    im.save(path, optimize=True)
    return path


def render_page():
    src = os.path.join(HERE, "OWNERS_MANUAL.md")
    lines = open(src, encoding="utf-8").read().splitlines()
    width, height = 1240, 1754
    im = Image.new("RGB", (width, height), (252, 250, 245))
    draw = ImageDraw.Draw(im)
    draw.rectangle((36, 36, width - 36, height - 36), outline=(180, 170, 155), width=2)
    body = font(22)
    head = font(32)
    foot = font(16)
    y = 64
    bottom = height - 96

    def room_for(gap):
        return y + gap <= bottom

    draw.text((64, y), "Duckie owner's manual", fill=(30, 28, 24), font=head)
    y += 52
    draw.line((64, y, width - 64, y), fill=(180, 170, 155), width=2)
    y += 24
    max_w = width - 128
    shown = 0
    stop = False
    for line in lines:
        if stop:
            break
        if line.startswith("# "):
            continue
        if line.startswith("A picture of the first page"):
            continue
        text = line.replace("**", "").replace("`", "")
        heading = False
        if text.startswith("#"):
            heading = True
            text = text.lstrip("#").strip()
        while "](" in text and "[" in text:
            start = text.find("[")
            mid = text.find("](", start)
            end = text.find(")", mid)
            if start < 0 or mid < 0 or end < 0:
                break
            text = text[:start] + text[start + 1:mid] + text[end + 1:]
        if text.startswith("|"):
            text = text.replace("|", "  ").strip()
        use = head if heading else body
        gap = 40 if heading else 30
        words = text.split()
        if not words:
            if room_for(16):
                y += 16
            else:
                stop = True
            continue
        buf = ""
        for word in words:
            trial = word if not buf else buf + " " + word
            if draw.textlength(trial, font=use) <= max_w:
                buf = trial
                continue
            if not room_for(gap):
                stop = True
                buf = ""
                break
            draw.text((64, y), buf, fill=(30, 28, 24), font=use)
            y += gap
            shown += 1
            buf = word
        if stop:
            break
        if buf:
            if not room_for(gap):
                break
            draw.text((64, y), buf, fill=(30, 28, 24), font=use)
            y += gap
            shown += 1
    draw.text((64, height - 64), "Rendered page. Not a certification. The rest of the book is OWNERS_MANUAL.md.", fill=(80, 70, 60), font=foot)
    path = os.path.join(OUT, "owners_page.png")
    im.save(path, optimize=True)
    if shown < 8:
        raise SystemExit("page render is too short")
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = [render_mat(), render_domes(), render_page()]
    total = 0
    for path in paths:
        size = os.path.getsize(path)
        total += size
        print("%s %d" % (os.path.relpath(path, LAB), size))
    print("total_bytes %d" % total)
    if total > 5 * 1024 * 1024:
        raise SystemExit("PNG total over 5 MB")


if __name__ == "__main__":
    main()
