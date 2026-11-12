#!/usr/bin/env python3
"""Step pictures for the plug guide. Plain shapes, large type."""
import os

from PIL import Image, ImageDraw, ImageFont

import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "steps")


def font_file(name):
    out = subprocess.check_output(["fc-list", name, "file"], text=True)
    for line in out.splitlines():
        path = line.split(":", 1)[0].strip()
        if path.lower().endswith(".ttf"):
            return path
    raise SystemExit("font not found: " + name)

W, H = 1600, 1000
BG = (255, 252, 245)
INK = (28, 32, 38)
MUTED = (70, 78, 88)
RED = (180, 40, 40)
BLUE = (30, 90, 160)
GREEN = (20, 120, 70)
YELLOW = (196, 145, 20)
ORANGE = (210, 110, 20)
BROWN = (120, 72, 40)


def fonts():
    regular = font_file("Inter:style=Regular")
    bold = font_file("Inter:style=Bold")
    return (ImageFont.truetype(bold, 46),
            ImageFont.truetype(regular, 30),
            ImageFont.truetype(bold, 28))


def wrap(draw, text, font, width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def canvas(title, subtitle):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    title_f, body, label = fonts()
    d.text((48, 28), title, font=title_f, fill=INK)
    y = 96
    for line in wrap(d, subtitle, body, W - 96):
        d.text((48, y), line, font=body, fill=MUTED)
        y += 38
    return im, d, y + 16, label, body


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    im.save(path, "PNG", optimize=True)
    if os.path.getsize(path) > 5 * 1024 * 1024:
        raise SystemExit("too big: " + name)
    return path


def box(d, xy, fill, outline=INK, width=4):
    d.rounded_rectangle(xy, radius=16, fill=fill, outline=outline, width=width)


def center_text(d, xy, text, font, fill=INK):
    x0, y0, x1, y1 = xy
    lines = text.split("\n")
    h = sum(font.size + 6 for _ in lines)
    y = (y0 + y1) / 2 - h / 2
    for line in lines:
        tw = d.textlength(line, font=font)
        d.text(((x0 + x1) / 2 - tw / 2, y), line, font=font, fill=fill)
        y += font.size + 6


def step01():
    im, d, y, label, body = canvas(
        "Step 1. Four plugs",
        "Each plug has a bump or a latch. That side always faces the way the picture shows. If it will not go in, turn it. Do not force it.")
    items = [
        (80, "XT30", "Shell shape\nplus and minus\ncannot swap"),
        (460, "Servo plug", "Latch on top\n3 holes\npins 1 2 3"),
        (840, "KK plug", "Ramp on the\nleft side\npin 1 at left"),
        (1220, "Lever", "Orange lever\nlift, insert,\npush down"),
    ]
    for x, name, note in items:
        box(d, (x, y, x + 300, y + 280), (255, 255, 255))
        center_text(d, (x, y + 20, x + 300, y + 120), name, label)
        center_text(d, (x + 10, y + 130, x + 290, y + 260), note, body)
    d.text((48, 860), "These four are the only plugs you make. The camera ribbon and the USB lead are bought whole.", font=body, fill=INK)
    save(im, "01_four_plugs.png")


def step02():
    im, d, y, label, body = canvas(
        "Step 2. Pack to the protection board",
        "Three pads. Match the color to the printed name. Red is plus. Black is minus. Yellow is the middle tap.")
    pads = [(220, RED, "B+", "red"), (640, YELLOW, "B1", "yellow"), (1060, INK, "B-", "black")]
    for x, color, name, word in pads:
        box(d, (x, y + 40, x + 280, y + 220), (255, 255, 255))
        d.rectangle((x + 90, y + 70, x + 190, y + 110), fill=color, outline=INK, width=3)
        center_text(d, (x, y + 120, x + 280, y + 200), name + "\n" + word, label)
    d.text((48, 820), "Solder each lead on its own pad. Do not let a bare end touch another pad.", font=body, fill=INK)
    save(im, "02_pack_to_bms.png")


def step03():
    im, d, y, label, body = canvas(
        "Step 3. Battery plug",
        "The XT30 shell only fits one way. Red goes in the plus cup. Black goes in the minus cup. The pack side is the socket.")
    box(d, (180, y + 30, 700, y + 360), (255, 255, 255))
    d.ellipse((260, y + 80, 420, y + 240), outline=RED, width=10)
    d.text((300, y + 130), "+", font=label, fill=RED)
    d.ellipse((460, y + 80, 620, y + 240), outline=INK, width=10)
    d.text((500, y + 130), "-", font=label, fill=INK)
    d.text((250, y + 270), "socket on the pack", font=body, fill=MUTED)
    box(d, (860, y + 30, 1460, y + 360), (255, 255, 255))
    d.text((920, y + 80), "Plug", font=label, fill=INK)
    for i, line in enumerate(["Red in the plus cup", "Black in the minus cup", "Tug each wire once"]):
        d.text((920, y + 160 + i * 50), line, font=body, fill=INK)
    save(im, "03_xt30.png")


def step04():
    im, d, y, label, body = canvas(
        "Step 4. Fuse in the red line",
        "The fuse sits in the red wire only, after the battery plug and before the switch board. Black does not go through the fuse.")
    d.line((120, y + 160, 1480, y + 160), fill=RED, width=16)
    box(d, (620, y + 70, 980, y + 250), (255, 255, 255))
    center_text(d, (620, y + 90, 980, y + 230), "15 A blade\nin the holder", label)
    d.text((120, y + 200), "from the plug", font=body, fill=MUTED)
    d.text((1180, y + 200), "to the switch", font=body, fill=MUTED)
    save(im, "04_fuse.png")


def step05():
    im, d, y, label, body = canvas(
        "Step 5. The button",
        "Two thin wires. White on one small hole of the switch board. Black on the other. The other ends go to the two lugs of the button.")
    box(d, (160, y + 40, 560, y + 320), (255, 255, 255))
    center_text(d, (160, y + 60, 560, y + 160), "Switch board", label)
    d.rectangle((250, y + 190, 330, y + 250), fill=(255, 255, 255), outline=INK, width=4)
    d.rectangle((390, y + 190, 470, y + 250), fill=INK)
    d.text((230, y + 270), "white", font=body, fill=INK)
    d.text((390, y + 270), "black", font=body, fill=INK)
    box(d, (980, y + 40, 1420, y + 320), (255, 255, 255))
    center_text(d, (980, y + 80, 1420, y + 280), "Button\ntwo lugs\nwhite and black", label)
    d.line((560, y + 200, 980, y + 180), fill=YELLOW, width=8)
    d.line((560, y + 240, 980, y + 240), fill=INK, width=8)
    save(im, "05_button.png")


def step06():
    im, d, y, label, body = canvas(
        "Step 6. The levers",
        "Red wires only in a red group. Black wires only in a black group. Lift the orange lever, push the bare copper in, push the lever down.")
    groups = [
        (60, "Ground", "221-415", "4 black wires"),
        (440, "Switched plus", "221-413", "3 red wires"),
        (820, "Servo plus", "221-415 + 221-413", "6 red wires"),
        (1200, "Servo ground", "221-415 + 221-413", "6 black wires"),
    ]
    for x, name, part, note in groups:
        box(d, (x, y + 10, x + 360, y + 300), (255, 255, 255))
        center_text(d, (x, y + 30, x + 360, y + 280), name + "\n" + part + "\n" + note, label)
    d.text((48, 860), "Strip 11 mm. If you see insulation inside the clear body, pull it out and strip again.", font=body, fill=INK)
    save(im, "06_levers.png")


def step07():
    im, d, y, label, body = canvas(
        "Step 7. The BEC",
        "Input red joins the switched plus lever. Input black joins the ground lever. Both output reds join together. Both output blacks join together. Tape the third wire on each output lead.")
    rows = [
        (RED, "Input red goes to the switched plus lever"),
        (INK, "Input black goes to the ground lever"),
        (RED, "Output reds join, then one red to servo plus"),
        (INK, "Output blacks join, then one black to servo ground"),
    ]
    for i, (color, text) in enumerate(rows):
        yy = y + 20 + i * 110
        d.rectangle((80, yy, 140, yy + 50), fill=color, outline=INK, width=3)
        d.text((170, yy + 6), text, font=label, fill=INK)
    save(im, "07_bec.png")


def step08():
    im, d, y, label, body = canvas(
        "Step 8. Servo plugs",
        "Latch on top. Feetech numbers pin 1 ground, pin 2 plus, pin 3 signal. Which hole is pin 1: match a kit cable, then the meter. This card does not measure that side.")
    # three holes
    box(d, (80, y + 20, 760, y + 340), (255, 255, 255))
    d.text((110, y + 40), "Power plug", font=label, fill=INK)
    cols = [(180, INK, "black"), (360, RED, "red"), (540, YELLOW, "yellow")]
    for x, color, name in cols:
        d.rounded_rectangle((x, y + 120, x + 120, y + 240), radius=12, fill=(255, 255, 255), outline=color, width=8)
        d.text((x, y + 260), name, font=body, fill=INK)
    box(d, (840, y + 20, 1520, y + 340), (255, 255, 255))
    d.text((870, y + 40), "Data plug on the adapter", font=label, fill=INK)
    d.rounded_rectangle((940, y + 120, 1060, y + 240), radius=12, outline=YELLOW, width=8)
    d.rounded_rectangle((1120, y + 120, 1240, y + 240), radius=12, outline=MUTED, width=8)
    d.line((1140, y + 140, 1220, y + 220), fill=MUTED, width=6)
    d.line((1220, y + 140, 1140, y + 220), fill=MUTED, width=6)
    d.rounded_rectangle((1300, y + 120, 1420, y + 240), radius=12, outline=INK, width=8)
    d.text((900, y + 260), "signal", font=body, fill=INK)
    d.text((1100, y + 260), "empty", font=body, fill=MUTED)
    d.text((1280, y + 260), "ground", font=body, fill=INK)
    d.text((48, 800), "Ankle feeds SP4 and SP5 use the power picture, and the signal hole stays empty.", font=body, fill=INK)
    d.text((48, 860), "Which side is pin 1: match a kit cable, then the meter. This card does not measure that side.", font=body, fill=INK)
    save(im, "08_servo_plugs.png")


def step09():
    im, d, y, label, body = canvas(
        "Step 9. Kit cables, one hop",
        "Each kit cable is already made. Write the cable name on both ends before you plug it in. Latch up. One hop at a time, from the hip toward the foot, and the same up the neck.")
    box(d, (120, y + 40, 520, y + 280), (230, 236, 240))
    center_text(d, (120, y + 40, 520, y + 280), "servo\nBUS 1", label)
    box(d, (1080, y + 40, 1480, y + 280), (230, 236, 240))
    center_text(d, (1080, y + 40, 1480, y + 280), "next servo\nBUS 2", label)
    d.line((520, y + 160, 1080, y + 160), fill=INK, width=10)
    box(d, (700, y + 110, 900, y + 210), (255, 230, 120))
    center_text(d, (700, y + 110, 900, y + 210), "S2", label)
    d.text((48, 820), "The same label goes on the other end. Left leg, right leg, then neck.", font=body, fill=INK)
    save(im, "09_kit_hop.png")


def step10():
    im, d, y, label, body = canvas(
        "Step 10. Head power plug",
        "Cable P13 is the long red and black pair up the neck. An XT30 sits at the neck base so the head unplugs. Do not mate this plug with the battery plug. The battery plug is the short one in the bay.")
    d.line((80, y + 140, 1520, y + 140), fill=RED, width=14)
    d.line((80, y + 190, 1520, y + 190), fill=INK, width=14)
    box(d, (680, y + 60, 920, y + 280), (255, 255, 255))
    center_text(d, (680, y + 80, 920, y + 250), "XT30\nat the\nneck", label)
    d.text((80, y + 240), "body", font=body, fill=MUTED)
    d.text((1360, y + 240), "head", font=body, fill=MUTED)
    save(im, "10_neck_xt30.png")


def step11():
    im, d, y, label, body = canvas(
        "Step 11. The Pi",
        "The square pad is pin 1. The 5-pin plug covers pins 1, 3, 5, 7 and 9. The hole over pin 7 is empty. Thick red and black are soldered, not crimped. The old assembly picture swaps the eyes. Use this sheet.")
    # header dots
    ox, oy = 80, y + 20
    for col in range(10):
        for row in range(2):
            n = col * 2 + 1 + row
            x = ox + col * 70
            yy = oy + row * 70
            fill = (255, 255, 255)
            if n == 1:
                fill = RED
            d.ellipse((x, yy, x + 36, yy + 36), fill=fill, outline=INK, width=3)
            d.text((x + 40, yy), str(n), font=body, fill=MUTED)
    d.text((80, y + 200), "Pins 1 to 20 only, the corner. Pin 1 is the filled dot. Empty plug hole sits on pin 7.", font=body, fill=INK)
    d.text((80, y + 280), "Solder: pin 2 red, pin 4 red, pin 6 black, pin 14 black.", font=body, fill=INK)
    d.text((80, y + 340), "Plug wires: pin 1 red, pin 3 blue, pin 5 yellow, pin 9 black.", font=body, fill=INK)
    save(im, "11_pi.png")


def step12():
    im, d, y, label, body = canvas(
        "Step 12. Camera ribbon and USB",
        "Do not cut these. Push the ribbon into the Pi camera socket and into the camera. Push the USB plug into the Pi socket marked USB, not the one marked PWR. The other end is the adapter.")
    box(d, (100, y + 40, 720, y + 300), (255, 255, 255))
    center_text(d, (100, y + 60, 720, y + 280), "Flat white ribbon\n300 mm\nbought cable", label)
    box(d, (860, y + 40, 1480, y + 300), (255, 255, 255))
    center_text(d, (860, y + 60, 1480, y + 280), "USB lead\nPi USB port\nto the adapter", label)
    note = "Which face of the ribbon touches the contacts is BLOCKER until that sheet is opened. Read the card in the bag. Do not guess."
    yy = 780
    for line in wrap(d, note, body, W - 96):
        d.text((48, yy), line, font=body, fill=INK)
        yy += 40
    save(im, "12_camera_usb.png")


def step13():
    im, d, y, label, body = canvas(
        "Step 13. Eyes",
        "One 3-pin plug. Position 1 is pin 16, white, right eye. Position 2 is pin 18, yellow, left eye. Position 3 is pin 20, black, ground. The ramp faces pin 1 of the plug.")
    box(d, (360, y + 20, 1240, y + 280), (255, 255, 255))
    holes = [(480, "1 white\npin 16"), (760, "2 yellow\npin 18"), (1040, "3 black\npin 20")]
    for x, name in holes:
        d.rounded_rectangle((x, y + 70, x + 140, y + 170), radius=12, outline=INK, width=6)
        d.text((x - 10, y + 190), name, font=body, fill=INK)
    d.text((48, 820), "Other black eye wires join the black wire. They do not get their own pin.", font=body, fill=INK)
    save(im, "13_eyes.png")


def step14():
    im, d, y, label, body = canvas(
        "Step 14. Feet",
        "Left foot signal is green, on pin 15. Right foot signal is white, on pin 13. Both grounds join the black wire already on pin 9. Do not add a second ground pin.")
    box(d, (120, y + 40, 700, y + 300), (230, 245, 230))
    center_text(d, (120, y + 40, 700, y + 300), "Left foot\ngreen\npin 15", label, fill=GREEN)
    box(d, (900, y + 40, 1480, y + 300), (245, 245, 245))
    center_text(d, (900, y + 40, 1480, y + 300), "Right foot\nwhite\npin 13", label)
    save(im, "14_feet.png")


def step15():
    im, d, y, label, body = canvas(
        "Step 15. Meter, before any battery",
        "Use the ohms setting, not the beep. Touch the probe tips together first and subtract that reading. One wire at a time. A good wire reads under 1 ohm after that subtraction.")
    box(d, (80, y + 20, 520, y + 280), (255, 255, 255))
    center_text(d, (80, y + 40, 520, y + 250), "Ohms\nnot beep", label)
    d.line((560, y + 90, 920, y + 90), fill=RED, width=8)
    d.line((560, y + 170, 920, y + 170), fill=INK, width=8)
    d.text((640, y + 200), "two probes, one wire", font=body, fill=MUTED)
    box(d, (960, y + 20, 1500, y + 280), (255, 255, 255))
    center_text(d, (960, y + 40, 1500, y + 250), "Same wire\nboth ends\nunder 1 ohm", label)
    d.text((48, 820), "Plus must not read through to ground. If it does, stop.", font=body, fill=INK)
    save(im, "15_meter.png")


def step16():
    im, d, y, label, body = canvas(
        "Step 16. Charger plug, and the wells",
        "Blue on pin 29. Green on pin 31. That is the 2-pin plug. The 3.3 V and the ground join the red and black wires of the 5-pin plug. The five gold wells have no plug yet. Leave them open.")
    box(d, (80, y + 30, 760, y + 300), (255, 255, 255))
    center_text(d, (80, y + 50, 760, y + 270), "2-pin plug\n1 blue = pin 29\n2 green = pin 31", label)
    box(d, (860, y + 30, 1520, y + 300), (255, 230, 230))
    center_text(d, (860, y + 50, 1520, y + 270), "Five wells\ndo not connect\nno plug yet", label, fill=RED)
    save(im, "16_charger_wells.png")


def main():
    for fn in (step01, step02, step03, step04, step05, step06, step07, step08,
               step09, step10, step11, step12, step13, step14, step15, step16):
        fn()
    print("steps", len(os.listdir(OUT)))


if __name__ == "__main__":
    main()
