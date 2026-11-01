"""Draws altaay_lab/wiring/odm_v2_wiring.svg and .png with schemdraw.
Solid = taken from upstream docs/code. Dashed = lab change or inferred (see WIRING.md)."""
import os
import schemdraw
import schemdraw.elements as elm
import schemdraw.flow as flow

schemdraw.config(fontsize=9, font="DejaVu Sans", lw=1.4)
PACK, SERVO, V5, SIG, BUS = "#c62828", "#ef6c00", "#6a1b9a", "#1565c0", "#2e7d32"

S = 1.45
def P(p):
    return (p[0] * S, p[1] * S)

def box(d, x, y, w, h, text, color="black", dashed=False, fill="white"):
    x, y, w, h = x * S, y * S, w * S, h * S
    b = flow.Box(w=w, h=h).at((x, y)).anchor("center").label(text, fontsize=8).color(color).fill(fill)
    if dashed:
        b.linestyle("--")
    d += b
    return b

def wire(d, pts, color, label=None, dashed=False, loc="top", ofst=0.15, lw=1.6, li=0):
    for i in range(len(pts) - 1):
        ln = elm.Line().at(P(pts[i])).to(P(pts[i + 1])).color(color).linewidth(lw)
        if dashed:
            ln.linestyle("--")
        if label and i == li:
            ln.label(label, loc=loc, fontsize=7.5, ofst=ofst)
        d += ln

with schemdraw.Drawing(show=False) as d:
    d.config(unit=1)
    # Title
    d += elm.Label().at(P((0, 10.6))).label("Open Duck Mini v2 wiring, altaay-lab (2026-11-01). Solid = upstream. Dashed = lab change or inferred.", fontsize=12, halign="left")
    d += elm.Label().at(P((0, 10.0))).label("Red = pack 6.0 to 8.4 V, Orange = servo bus 7.2 V (regulated), Purple = 5 V, Blue = GPIO / I2C / I2S, Green = USB and servo data", fontsize=9, halign="left")

    # ---- Power chain ----
    box(d, 1.6, 6.5, 3.0, 1.9, "2S pack\n2x Molicel P30B 18650\nseries, 6.0 to 8.4 V\nholder B09WCT8672\n(issue #51: measure drop)", PACK)
    box(d, 5.6, 6.5, 2.8, 1.9, "2S BMS 20 A (claim)\nAITRIP B08NSTF8CT\nB+ / BM / B-\nP+ / P-", PACK)
    wire(d, [(3.1, 6.9), (4.2, 6.9)], PACK, "B+ 16 AWG")
    wire(d, [(3.1, 6.1), (4.2, 6.1)], PACK, "B- 16 AWG", loc="bottom")
    wire(d, [(1.6, 7.45), (1.6, 7.75), (5.0, 7.75), (5.0, 7.45)], PACK, "BM mid-tap 22 AWG", lw=1.0, li=1)
    box(d, 5.6, 9.0, 2.8, 1.0, "USB-C 2S charger\n(B0BJTW4QBR) on P+/P-", PACK)
    wire(d, [(5.6, 8.5), (5.6, 7.45)], PACK, lw=1.0)
    box(d, 8.9, 6.5, 1.6, 1.0, "XT30U\npair", PACK)
    wire(d, [(7.0, 6.5), (8.1, 6.5)], PACK, "P+ 16 AWG")
    box(d, 11.6, 6.5, 2.6, 1.4, "FUSE 15 A ATO\nLittelfuse 0287015.PXCN\nholder FHAC0001ZXJ", PACK, dashed=True, fill="#ffebee")
    wire(d, [(9.7, 6.5), (10.3, 6.5)], PACK)
    box(d, 14.6, 6.5, 2.2, 1.4, "Power switch\nmust be >= 15 A DC\n(stock model unrated)", PACK)
    wire(d, [(12.9, 6.5), (13.5, 6.5)], PACK, "16 AWG")
    wire(d, [(15.7, 6.5), (16.8, 6.5)], PACK, "16 AWG")
    d += elm.Dot().at(P((16.8, 6.5))).color(PACK)
    d += elm.Label().at(P((16.8, 5.95))).label("pack bus\n6.0 to 8.4 V", fontsize=7.5, color=PACK)

    # Servo buck
    box(d, 19.6, 8.0, 3.4, 1.9, "SERVO BUCK (lab change)\nCastle CC BEC Pro\nP/N 010-0004-01\nset to 7.2 V via Castle Link V4\n15 A cont, 20 A peak", SERVO, dashed=True, fill="#fff3e0")
    wire(d, [(16.8, 6.5), (16.8, 8.0), (17.9, 8.0)], PACK, "16 AWG in", dashed=True)
    # 5 V UBEC
    box(d, 19.6, 4.3, 3.4, 1.5, "5 V regulator (stock)\nHENGE 4A UBEC 5V\n(backup Pololu D36V28F5)", V5)
    wire(d, [(16.8, 6.5), (16.8, 4.3), (17.9, 4.3)], PACK, "20 AWG in", loc="bottom")

    # Waveshare adapter
    box(d, 25.6, 8.0, 3.4, 1.9, "Waveshare Bus Servo\nAdapter (A), SKU 25514\njumper on B (USB)\nscrew terminal power in\n/dev/ttyACM0 1 Mbaud", BUS)
    wire(d, [(21.3, 8.0), (23.9, 8.0)], SERVO, "7.2 V, 16 AWG to screw term.", dashed=True, ofst=0.1)
    d += elm.Label().at(P((22.6, 7.35))).label("both BEC leads joined\n(each 3-pin lead <= 5 A)", fontsize=7, color=SERVO)

    # Pi
    box(d, 26.2, 0.6, 3.6, 2.6, "Raspberry Pi Zero 2 W\n40-pin header\n(BCM GPIO numbers)", SIG, fill="#e3f2fd")
    wire(d, [(21.3, 4.3), (25.2, 4.3), (25.2, 1.9)], V5, "5 V to pin 2/4, GND pin 6 (feed point inferred)", ofst=0.1)
    wire(d, [(26.8, 1.9), (26.8, 7.05)], BUS, "USB: Pi micro-USB OTG to adapter USB-C", loc="bottom", ofst=0.1)

    # ---- Servo chains ----
    def chain(y, ids_names, color, start_x, dashed=False, title=""):
        x = start_x
        prev = None
        for sid, nm in ids_names:
            box(d, x, y, 1.9, 0.95, f"ID {sid}\n{nm}", color, dashed=dashed, fill="#fff8e1")
            if prev is not None:
                wire(d, [(prev + 0.95, y), (x - 0.95, y)], SERVO, dashed=dashed, lw=1.2)
            prev = x
            x += 2.3
        d.add(elm.Label().at(P((start_x - 1.0, y + 0.75))).label(title, fontsize=8, halign="left"))
    left = [(20, "L hip_yaw"), (21, "L hip_roll"), (22, "L hip_pitch"), (23, "L knee"), (24, "L ankle")]
    head = [(30, "neck_pitch"), (31, "head_pitch"), (32, "head_yaw"), (33, "head_roll")]
    right = [(10, "R hip_yaw"), (11, "R hip_roll"), (12, "R hip_pitch"), (13, "R knee"), (14, "R ankle")]
    chain(9.0, head, SERVO, 31.6, dashed=True, title="Head chain (bus port 1, branch point inferred)")
    chain(7.2, left, SERVO, 31.6, title="Left leg (adapter bus port 1)")
    chain(5.4, right, SERVO, 31.6, title="Right leg (adapter bus port 2)")
    wire(d, [(27.3, 8.3), (29.6, 8.3), (29.6, 7.2), (30.65, 7.2)], SERVO, "port 1", lw=1.6)
    wire(d, [(29.6, 8.3), (29.6, 9.0), (30.65, 9.0)], SERVO, dashed=True, lw=1.4)
    wire(d, [(27.3, 7.7), (29.0, 7.7), (29.0, 5.4), (30.65, 5.4)], SERVO, "port 2", lw=1.6)
    d += elm.Label().at(P((36.2, 4.35))).label("STS3215 C001 7.4 V 1:345 x14, 3-wire bus (V+, GND, half-duplex data), cables ship with servos", fontsize=7.5)

    # ---- GPIO peripherals ----
    per = [
        (2.6, "BNO055 (Adafruit 4646): VIN pin 1 (3V3), GND pin 9, SDA pin 3 (GPIO2), SCL pin 5 (GPIO3); 3VO, RST not connected", False),
        (1.5, "Foot switches Omron SS-10: Left pin 15 (GPIO22), Right pin 13 (GPIO27), GND pin 9", False),
        (0.2, "Eye LEDs: table Left pin 16 (GPIO23), Right pin 18 (GPIO24); eyes.py swaps (L=D24, R=D23)\nProjector LED pin 22 (GPIO25); common cathode GND pin 6", False),
        (-1.2, "Antenna SG90 x2: PWM pin 32 (GPIO12), pin 33 (GPIO13); antennas.py has L=D13, R=D12\n5 V pin 2, GND pin 6 (servo current comes from the Pi 5 V rail)", False),
        (-2.6, "MAX98357A I2S amp (Adafruit 3006): LRC pin 35 (GPIO19), BCLK pin 12 (GPIO18), DIN pin 40 (GPIO21)\nVIN pin 2 (5V), GND pin 6; GAIN, SD not connected; 8 ohm speaker", False),
        (-3.8, "Camera: Raspberry Pi camera on CSI (picamzero). Mic: in upstream diagram, model not stated", True),
    ]
    for i, (y, txt, dsh) in enumerate(per):
        h = 1.05 if "\n" in txt else 0.7
        b = flow.Box(w=17.0 * S, h=h * S).at(P((9.5, y))).anchor("center").label(txt, fontsize=8).color(SIG)
        if dsh:
            b.linestyle("--")
        d += b
        xv = 19.0 + 0.5 * i
        yp = 1.5 - 0.35 * i
        wire(d, [(18.0, y), (xv, y), (xv, yp), (24.4, yp)], SIG, lw=1.0, dashed=dsh)

    # notes
    notes = ("Notes: fuse sits right after BMS P+ (before switch), protecting BMS and 16 AWG harness.  BEC Pro output is set to 7.2 V; below about 7.3 to 7.5 V pack voltage\n"
             "the output tracks the input (not verified for BEC Pro).  Use the adapter screw terminal, not the 5.5x2.1 barrel, for servo power.  Common ground: all GND tied at BMS P-.\n"
             "GPIO pins from upstream docs/assembly_guide.md; code in Open_Duck_Mini_Runtime differs on eyes and antennas (left/right swapped). Head chain branch point and 5 V feed point inferred.")
    d += elm.Label().at(P((0, -4.7))).label(notes, fontsize=8, halign="left", valign="top")
    here = os.path.dirname(os.path.abspath(__file__))  # this wiring/ folder, wherever the repo is cloned
    d.save(os.path.join(here, "odm_v2_wiring.svg"))
    d.save(os.path.join(here, "odm_v2_wiring.png"), dpi=140)
