"""Per-subsystem wiring sheets for the altaay-lab Open Duck Mini v2, generated from wiring/netlist.yaml.

Writes, next to this script:
  1_power.svg/.png         pack, BMS, charger, XT30, fuse with its lead splices, Pololu 2815 and panel switch, BEC,
                           belly splices, the first-servo power feeds and the 5 V branch to the head regulator
  2_servo_bus.svg/.png     adapter (data only, D15), the 3 chains in ID order, kit cables and made leads,
                           power injection points, the ankle second feeds SP4 SP5 (D23)
  3_pi_sensors.svg/.png    Pi header with every wire leaving it, BNO055, foot switches with pull-ups, USB
  4_head_expression.svg/.png  eye and projector LEDs with resistors, antenna SG90s, amplifier and speaker, camera
  5_harness.svg/.png       where each cable runs through the body (regions, joints crossed)
  WIRING_SHEETS.md         index, coverage table, how to regenerate
Stops with an error if any active netlist wire is not drawn in full on sheets 1 to 4, or any active cable is
missing from sheet 5. Layout warnings (overlaps, labels too long) are printed; --strict turns them into errors.
Usage: python3 wiring/sheets/make_sheets.py [--strict]
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheetlib as L  # noqa: E402
from sheetlib import Sheet, Book, INK, GREY, TS, W as W_  # noqa: E402

OUTDIR = os.environ.get("ODM_SHEETS_OUT", L.HERE)
BAND_PWR, BAND_HEAD, BAND_BUS, BAND_IO = "#fde4e1", "#efe4f7", "#e3f1e6", "#e2ecf8"


def P(net, ref):
    return net.pin(ref)


def plab(net, cid, pin):
    """Printable pin label from the netlist (the text the sheet shows next to the terminal)."""
    return net.pin(f"{cid}.{pin}")["label"]


def cref(net, cid):
    return net.comp(cid)["ref"]


# ================================================================== sheet 1: power
def xref_text(book, sh, ref, prefix=""):
    """'SD1 b from YD3, sheet 2 C2' for the wires at ref that are drawn on another sheet."""
    parts = []
    for w, far in book.other_wires(ref, sh):
        far_c = sh.net.comp(far.split(".")[0])
        name = far_c["ref"] if far_c["kind"] == "splice" else f"{far_c['ref']} {far.split('.', 1)[1]}"
        br = (" " + L.BRANCH[w["branch"]]) if w.get("branch") else ""
        parts.append(f"{w['cable']}{br} from {name}, {book.term_where(far, sh.no)}")
    return prefix + "; ".join(parts)


def sheet_power(book):
    sh = Sheet(book, 1, "1_power", "POWER",
               "Pack to BMS, charger, XT30 disconnect, 15 A fuse, Pololu 2815 switch, splices VSW and G, "
               "BEC to the servo feeds, and the 5 V branch up the neck to U3 and the Pi.")
    yP, yN, s = 48.0, 100.0, 7.0          # BMS P+ and P- rows, slot pitch
    yA, yB = yP - s / 2, yN + s / 2       # + line (P6, P7) and - line (P8, P14)

    sh.region(12, 30, 408, 112, "BATTERY BAY", "body_back, seen from behind")
    sh.block("PACK", 14, 36, 40, 108, "pack", band=BAND_PWR,
             sub=["2S, 2x Molicel", "INR18650-P30B", "holder", "B09WCT8672", "6.0 to 8.4 V"],
             pins=[("B+", "R", yP, "+"), ("MID", "R", 74, "strap"), ("B-", "R", yN, "-")])
    sh.block("BMS", 78, 36, 106, 108, "BMS", band=BAND_PWR, sub_y=57,
             sub=["Tenergy", "P/N 32175", "10 A working", "OC 22 +/- 5 A"],
             pins=[("B+", "L", yP, "B+"), ("B1", "L", 74, "B1"), ("B-", "L", yN, "B-"),
                   ("P+", "R", yP, "P+", 4, s), ("T", "R", 74, "T"), ("P-", "R", yN, "P-", 4, s)])
    sh.nc_note(109.5, 79.2, "T: NTC, open [I]")
    sh.w("PACK.B+", "BMS.B+")
    sh.w("PACK.MID", "BMS.B1")
    sh.w("PACK.B-", "BMS.B-")
    sh.block("CHG", 140, 58, 168, 88, "charger", band=BAND_PWR, tsize=8.6, sub_y=71.5,
             sub=["USB-C 2S", "B0BJTW4QBR"],
             pins=[("B+", "U", 154, "B+"), ("B-", "D", 154, "B-"), ("USB", "R", 79.5, "USB-C in")])
    sh.w("BMS.P+", "CHG.B+", 154, sa=2, lab=124)
    sh.w("BMS.P-", "CHG.B-", 154, sa=1, lab=124)
    sh.block("XT30", 184, 36, 206, 108, "XT30U", band=BAND_PWR, tsize=8.8, sub_y=60,
             sub=["F: pack", "M: robot", "mated", "15 A"],
             pins=[("F+", "L", yA, "F+"), ("F-", "L", yB, "F-"), ("M+", "R", yA, "M+"), ("M-", "R", yB, "M-")])
    sh.w("BMS.P+", "XT30.F+", sa=1, lab=124)
    sh.w("BMS.P-", "XT30.F-", sa=2, lab=124)
    # P7: each fuse holder lead (90 mm as shipped) is lengthened with 16 AWG red at splice JFI or JFO (cables3d)
    yF = 78.0                              # fuse lead row, below the + line so each P7 piece has room for its label
    sh.splice("JFI", 243, yA, lab_dx=0, lab_dy=-3.4, ha="center")
    sh.splice("JFO", 270, yA, lab_dx=0, lab_dy=-3.4, ha="center")
    sh.block("F1", 247, 66, 265, 90, "15 A", band=BAND_PWR, tsize=8.6, sub_y=83.0,
             sub=["ATO, holder", "FHAC0001ZXJ"], subsize=6.4,
             pins=[("IN", "L", yF, "1"), ("OUT", "R", yF, "2")])
    sh.w("XT30.M+", "JFI.S")
    sh.w("JFI.S", "F1.IN", ("y", yF), lab=("y", 61.5))
    sh.w("F1.OUT", "JFO.S", 270, lab=("y", 61.5))
    sh.block("SW1", 312, 36, 346, 94, "Pololu 2815", band=BAND_PWR, tsize=8.6, sub_y=85.5,
             sub=["MOSFET switch HP", "slide switch: OFF"], subsize=6.8,
             pins=[("VIN", "L", yA, plab(sh.net, "SW1", "VIN"), 2, 4.0), ("SW", "L", 66, plab(sh.net, "SW1", "SW")),
                   ("GND_SW", "L", 73, plab(sh.net, "SW1", "GND_SW")), ("ON", "L", 80, plab(sh.net, "SW1", "ON")),
                   ("VOUT", "R", yA, plab(sh.net, "SW1", "VOUT")), ("GND", "R", 64, plab(sh.net, "SW1", "GND"), 3, 4.0)])
    # D50: DK7 (Pololu 5383 ideal diode) between JFO and SW1 VIN; DK6 (SYS) joins SW1 VIN from the dock region below
    sh.block("DK7", 280, 38, 302, 58, "DK7 5383", band=BAND_PWR, tsize=7.0,
             pins=[("VIN", "L", yA, "VIN"), ("VOUT", "R", yA, "VOUT"), ("GND", "D", 291, "GND")])
    sh.w("JFO.S", "DK7.VIN")
    sh.w("DK7.VOUT", "SW1.VIN", 306, lab="none")
    sh.w("DK7.GND", "SW1.GND", ("y", 104.0), 352, sb=1, lab="none")
    sh.block("CTL", 212, 52, 236, 76, "panel sw.", band=BAND_PWR, tsize=8.0, sub_y=61.4,
             sub=["stock switch", "in body_back"], subsize=6.6,
             pins=[("2", "D", 220, "2"), ("1", "D", 228, "1")])
    sh.w("SW1.SW", "CTL.1", 292, 94)
    sh.w("SW1.GND_SW", "CTL.2", 298, 99)
    xG, xV = 350.0, 392.0
    sh.splice("VSW", xV, yA, lab_dx=0, lab_dy=-3.4, ha="center")
    sh.splice("G", xG, yB, lab_dx=-2.2, lab_dy=3.4, ha="right")
    sh.w("SW1.VOUT", "VSW.S")
    sh.w("XT30.M-", "G.S", lab=278)
    sh.w("G.S", "SW1.GND", ("y", 64.0), lab=("y", 84.0))

    # ---------------- band 2: head (U3, Pi) and belly (BEC)
    sh.region(12, 124, 224, 180, "HEAD", "head floor, 5 V branch (D4, D8)")
    sh.region(296, 124, 408, 180, "BELLY", "servo regulator (D3, D15)")
    # ---------------- dock contacts (D43, D50): chest pad, charge path, SENSE, SYS
    sh.region(226, 124, 294, 180, "DOCK", "chest pad and charge path (D43, D50)")
    sh.block("DKP", 228, 134, 244, 176, "pad", band=BAND_PWR, tsize=7.0,
             pins=[("CHG", "R", 140, "CHG+"), ("SNS", "R", 150, "SENSE", 2, 3.0), ("GND", "R", 160, "GND", 2, 3.0), ("SYS", "R", 170, "SYS")])
    sh.block("DK2", 252, 134, 266, 146, "DK2", band=BAND_PWR, tsize=6.6,
             pins=[("VIN", "L", 140, "VIN"), ("VOUT", "R", 140, "VOUT"), ("GND", "D", 259, "G")])
    sh.block("F2", 272, 134, 286, 146, "F2 5 A", band=BAND_PWR, tsize=6.6, pins=[("IN", "L", 140, "1"), ("OUT", "R", 140, "2")])
    sh.block("RT1", 252, 148, 266, 156, "RT1 NTC", band=BAND_PWR, tsize=6.2, pins=[("1", "L", 152, "1"), ("2", "R", 152, "2")])
    sh.block("WK1", 272, 148, 286, 156, "WK1 wake", band=BAND_PWR, tsize=6.2, pins=[("A", "L", 152, "A"), ("K", "R", 152, "K")])
    sh.block("DK6", 252, 164, 266, 176, "DK6", band=BAND_PWR, tsize=6.6,
             pins=[("VIN", "L", 170, "VIN"), ("VOUT", "R", 170, "VOUT"), ("GND", "D", 259, "G")])
    sh.w("DKP.CHG", "DK2.VIN")
    sh.w("DKP.GND", "DK2.GND", 248, 158.0, 259, lab="none")
    sh.w("DK2.VOUT", "F2.IN")
    sh.w("F2.OUT", "BMS.P+", 290, 120.0, 110, sb=3, lab="none")
    sh.w("DKP.GND", "BMS.P-", 246, 178.5, 112, sa=1, sb=3, lab="none")
    sh.w("DKP.SNS", "RT1.1", 248.5, lab="none")
    sh.w("RT1.2", "BMS.P-", 268, 179.5, 114, sb=0, lab="none")
    sh.w("DKP.SNS", "WK1.A", 249, 157.5, 270, sa=1, lab="none")
    sh.w("WK1.K", "SW1.ON", 288, 108.0, 308, lab="none")
    sh.w("DKP.SYS", "DK6.VIN")
    sh.w("DK6.VOUT", "SW1.VIN", 292, 118.0, 309, sb=1, lab="none")
    sh.w("DK6.GND", "SW1.GND", 181.0, 354, sb=2, lab="none")
    sh.block("U1", 372, 130, 406, 174, "BEC Pro", band=BAND_PWR, tsize=8.6, sub_y=145,
             sub=["Castle CC", "set to 7.2 V"], subsize=6.8,
             pins=[(p_, side, pos, plab(sh.net, "U1", p_) if side != "D" else "")
                   for p_, side, pos in (("IN-", "U", 386), ("IN+", "U", 400), ("OUT1+", "L", 140), ("OUT2+", "L", 147),
                                         ("OUT1-", "L", 156), ("OUT2-", "L", 163), ("OUT1S", "D", 380),
                                         ("OUT2S", "D", 388), ("LINK", "D", 398))])
    sh.nc_note(389, 181.6, "3rd wires insulated [I], Link Port unused", ha="center")
    sh.w("G.S", "U1.IN-", ("x", 386), lab=368)
    sh.w("VSW.S", "U1.IN+", ("x", 400), lab=("y", 84.0))
    sh.block("U3", 120, 132, 158, 170, "D30V30F5", band=BAND_HEAD, tsize=8.6, sub_y=162.5,
             sub=["Pololu 4892", "5 V step-down"], subsize=6.8,
             pins=[("GND.1", "U", 131, "GND"), ("VIN", "U", 147, "VIN"),
                   ("VOUT", "L", 146, "VOUT"), ("GND.2", "L", 160, "GND"),
                   ("EN", "R", 148, "EN"), ("PG", "R", 155, "PG")])
    sh.w("G.S", "U3.GND.1", ("y", 116.0), 131, lab=230)
    sh.w("VSW.S", "U3.VIN", ("y", 120.0), 147, lab=300)
    notes = {}
    for p_ in (1, 3, 4, 5):
        notes[p_] = book.pin_where(f"PI.{p_}", sh.no)
    pi_partial(sh, 18, 146, [1, 2, 3], pitch=7.0, notes=notes, w_name=23.0)
    sh.w("U3.VOUT", "PI.2", lab=100)
    sh.w("U3.GND.2", "PI.6", lab=100)
    sh.splice("JBP", 322, 143.5, lab_dx=2.4, lab_dy=0.0)
    sh.splice("JBN", 322, 159.5, lab_dx=2.4, lab_dy=0.0)
    for out, js in (("U1.OUT1+", "JBP.S"), ("U1.OUT2+", "JBP.S"), ("U1.OUT1-", "JBN.S"), ("U1.OUT2-", "JBN.S")):
        sh.w(out, js, 322, lab=347)

    # ---------------- band 3: servo feeds (D15)
    sh.region(12, 183, 408, 247, "TRUNK", "first servo of each chain, made-lead housing on BUS 2 (D15)")
    xSV, ySV, xSG, ySG = 300.0, 197.0, 316.0, 236.0
    sh.splice("SPV", xSV, ySV, lab_dx=2.2, lab_dy=-2.8)
    sh.splice("SPG", xSG, ySG, lab_dx=-2.2, lab_dy=-2.8, ha="right")
    sh.w("JBP.S", "SPV.S", ("x", 310), ("y", ySV), lab=("y", 170.0))
    sh.w("JBN.S", "SPG.S", ("x", xSG), lab=("y", 205.0))
    groups = [("SV30", "JG30", 68.0), ("SV20", "JG20", 160.0), ("SV10", "JG10", 252.0)]
    for sv, jg, bx in groups:
        first_servo_group(book, sh, sv, jg, bx)
    # SPV to V from above: farther chain on the higher level
    sh.w("SPV.S", "SV30.BUS2.V", ("y", 191.0), ("x", 68 - 12), lab=130)
    sh.w("SPV.S", "SV20.BUS2.V", ("x", 160 - 12), lab=220)
    sh.w("SPV.S", "SV10.BUS2.V", ("y", 202.0), ("x", 252 - 12), lab=270)
    # SPG to the ground splices from below: farther chain on the lower level
    sh.w("SPG.S", "JG10.S", ("x", 252 - 40), lab=290)
    sh.w("SPG.S", "JG20.S", ("y", 240.0), ("x", 160 - 40), lab=184)
    sh.w("SPG.S", "JG30.S", ("x", 322.0), ("y", 244.0), ("x", 68 - 40), lab=96)
    # D23: the second feeds leave SPV and SPG too; they are drawn in full on sheet 2 next to the ankle servos
    ankle = [(w, w["to"]) for w in sh.net.active_wires if w["from"] in ("SPV.S", "SPG.S") and w["to"].startswith(("SV24", "SV14"))]
    cabs = sorted({w["cable"] for w, _ in ankle})
    far = {c: next(t for w, t in ankle if w["cable"] == c) for c in cabs}
    sh.lines(330, 191.0, ["+ second feeds (D23) from SPV and SPG, V and G only:"] +
             [f"{c} to ID {far[c][2:4]} BUS 1 ({book.term_where(far[c], sh.no)})" for c in cabs], 6.4, GREY)
    sh.legend()
    sh.notes_box(152, 249, 270, 287, [
        "All grounds are common and return to BMS P- (splice G, P14, XT30, P8). B- and P- are separate nodes on "
        "the Tenergy board: nothing but the cell goes on B-.",
        f"Power on: XT30 in, panel switch {cref(sh.net, 'CTL')} closed. The 2815 slide switch stays OFF. Not an "
        "emergency cutoff (Pololu): unplug the XT30.",
        "P7: the fuse holder leads (90 mm as shipped) get 16 AWG red extensions at JFI and JFO. P13 runs up the "
        "neck through 4 joints (sheet 5).",
        "Not checked on the parts [I]: U3 pin order, charger pad labels, which 2 panel switch lugs close when ON.",
    ])
    return sh


def pi_header(sh, x, y, rows, pitch=9.0, notes=None, wire_pins=None, slots=None, title="U4  Pi header (part)",
              w_name=17.0, gap=5.0):
    """Raspberry Pi 40-pin header rows (row r holds pins 2r-1 and 2r): odd pins on the left edge, even pins on the
    right edge, physical pin numbers and BCM names (pinout.xyz). Rows that do not follow each other get a break."""
    net = sh.net
    slots = slots or {}
    ypos, yy, prev = {}, y, None
    for r in rows:
        if prev is not None:
            yy += pitch + (gap if r != prev + 1 else 0)
        ypos[r] = yy
        prev = r
    x0, x1 = x, x + 2 * w_name + 16
    ytop, ybot = y - 5.5, yy + 5.5
    sh.rect(x0, ytop - 6.2, x1, ybot, fc="white", ec=INK, lw=0.9, z=8, r=1.2)
    sh.rect(x0 + 0.35, ytop - 5.85, x1 - 0.35, ytop, fc=BAND_IO, ec="none", lw=0, z=8.5, r=0.9)
    sh.text((x0 + x1) / 2, ytop - 2.9, title, 8.6, True, INK, ha="center", z=31)
    sh.blocks.append((x0, ytop - 6.2, x1, ybot, "PI"))
    prev = None
    for r in rows:
        yr = ypos[r]
        if prev is not None and r != prev + 1:
            yb = yr - pitch / 2 - gap / 2
            for xa, xb in ((x0 + 3, x1 - 3),):
                zig = [(xa, yb)]
                n = 14
                for k in range(1, n + 1):
                    zig.append((xa + (xb - xa) * k / n, yb + (0.9 if k % 2 else -0.9)))
                sh.line(zig, L.LIGHT, 0.6, z=12)
            sh.text((x0 + x1) / 2, yb + 2.6, f"pins {2 * prev + 1} to {2 * r - 2} not used", 6.0, False, L.LIGHT,
                    ha="center", z=31)
        prev = r
        for p, side in ((2 * r - 1, "L"), (2 * r, "R")):
            ref = f"PI.{p}"
            used = ref in net.pins
            xd = (x0 + x1) / 2 + (-2.6 if side == "L" else 2.6)
            if p == 1:
                sh.rect(xd - 1.0, yr - 1.0, xd + 1.0, yr + 1.0, fc=INK, ec=INK, lw=0.6, z=12)
            else:
                sh.ax.add_patch(L.Circle((xd, yr), 1.05, fc=INK if used else "white", ec=INK, lw=0.6, zorder=12))
            sh.text(xd + (-2.2 if side == "L" else 2.2), yr, str(p), 7.0, used, INK if used else L.LIGHT,
                    ha="right" if side == "L" else "left", z=31)
            name = L.PI_NAMES[p]
            nx = x0 + 1.8 if side == "L" else x1 - 1.8
            sh.text(nx, yr, name, TS, used, INK if used else L.LIGHT, ha="left" if side == "L" else "right", z=31)
            note = (notes or {}).get(p)
            if note:
                sh.text(nx + (tw_name(name) + 1.2 if side == "L" else -tw_name(name) - 1.2), yr + 0.1, note, 6.4,
                        False, GREY, ha="left" if side == "L" else "right", z=31, italic=True)
            if used and (wire_pins is None or p in wire_pins) and not note:
                n = slots.get(p, 1)
                pt = 2.6 if n == 3 else 3.0
                ext = max(2.2, (n - 1) * pt + 2.2)
                xe = x0 if side == "L" else x1
                xo = xe - 1.6 if side == "L" else xe + 1.6
                sh.rect(min(xe, xo), yr - ext / 2, max(xe, xo), yr + ext / 2, fc="#3c4a55", ec=INK, lw=0.6, z=12)
                sh.term(ref, xo, yr, side, n, pt)
    return x0, x1, ypos


def pi_partial(sh, x, y, rows, pitch=7.0, notes=None, wire_pins=None, w_name=17.0):
    return pi_header(sh, x, y, rows, pitch=pitch, notes=notes, wire_pins=wire_pins, w_name=w_name)[:2]


def resistor_v(sh, cid, x, ytop, ybot, label, side_note="L"):
    """Small vertical resistor with a terminal at each end (top pin 2, bottom pin 1 unless swapped)."""
    net = sh.net
    yc = (ytop + ybot) / 2
    h = min(6.0, ybot - ytop - 2.0)
    sh.rect(x - 1.3, yc - h / 2, x + 1.3, yc + h / 2, fc="white", ec=INK, lw=0.8, z=14)
    sh.line([(x, ytop), (x, yc - h / 2)], "#8a8a8a", 0.9, z=13)
    sh.line([(x, yc + h / 2), (x, ybot)], "#8a8a8a", 0.9, z=13)
    sh.blocks.append((x - 1.3, yc - h / 2, x + 1.3, yc + h / 2, cid))
    sh.text(x + (-2.2 if side_note == "L" else 2.2), yc, label, 6.6, True, INK, ha="right" if side_note == "L" else "left",
            z=31, free=True)


def tw_name(s):
    return L.tw(s, TS, True)


def first_servo_group(book, sh, sv, jg, bx0):
    """Made-lead housing on BUS 2 of the first servo of a chain with its ground splice (power sheet view).
    The data wire and the data ground are drawn on sheet 2; here they are cross-referenced."""
    by0 = 204.0
    yD, yV, yG = by0 + 12.0, by0 + 18.0, by0 + 24.0
    sh.block(sv, bx0, by0, bx0 + 36, by0 + 29, f"ID {sv[2:]}  BUS 2", band=BAND_BUS, tsize=8.4, title_ref=False,
             sub=[sh.net.joint_of(sv)], subsize=7.0, sub_y=by0 + 8.6)
    sh.rect(bx0 - 3.2, yD - 2.7, bx0, yG + 2.7, fc="#eef0f2", ec=INK, lw=0.7, z=11)
    for yy, nm in ((yD, "D"), (yV, "V"), (yG, "G")):
        sh.text(bx0 + 1.5, yy, nm, TS, True, INK, z=31)
    sh.term(f"{sv}.BUS2.V", bx0 - 3.2, yV, "L")
    sh.term(f"{sv}.BUS2.G", bx0 - 3.2, yG, "L")
    sh.text(bx0 + 5.0, yD, xref_text(book, sh, f"{sv}.BUS2.D"), 6.2, False, GREY, z=31, italic=True)
    sh.splice(jg, bx0 - 40, yG, lab_dx=-2.0, lab_dy=-2.8, ha="right")
    gref = xref_text(book, sh, f"{jg}.S")
    sh.text(bx0 - 40, yG - 6.6, "+ " + gref, 6.2, False, GREY, ha="center", free=True, italic=True)
    sh.w(f"{jg}.S", f"{sv}.BUS2.G", ("x", bx0 - 3.2), lab=bx0 - 21)


# ================================================================== sheet 2: servo bus
def servo(sh, sv, x0, y0, flip=False, w=22.0, h=33.0, pitch=7.5):
    """STS3215 block: BUS 2 housing on the left edge (in), BUS 1 on the right edge (out), cavities D V G.
    A cavity whose pin is nc gets a cross (a free port is all crosses; the ankle BUS 1 has D empty, D23)."""
    net = sh.net
    c = net.comp(sv)
    pins = c["pins"]
    sh.block(sv, x0, y0, x0 + w, y0 + h, f"ID {sv[2:]}", band=BAND_BUS, tsize=9.2, title_ref=False,
             sub=[net.joint_of(sv), c["region"]], subsize=6.6, sub_y=y0 + 9.6)
    order = ("G", "V", "D") if flip else ("D", "V", "G")
    ys = {nm: y0 + 12.0 + pitch * i for i, nm in enumerate(order)}
    for side, port in (("L", "BUS2"), ("R", "BUS1")):
        xe = x0 if side == "L" else x0 + w
        xo = xe - 2.6 if side == "L" else xe + 2.6
        free = all(p["dir"] == "nc" for p in pins if p["pin"].startswith(port))
        sh.rect(min(xe, xo), ys[order[0]] - 3.0, max(xe, xo), ys[order[2]] + 3.0,
                fc="white" if free else "#eef0f2", ec=L.LIGHT if free else INK, lw=0.7, z=11,
                ls=(0, (2, 1.5)) if free else "-")
        for nm in order:
            ref = f"{sv}.{port}.{nm}"
            if free or net.pin(ref)["dir"] == "nc":
                sh._cross(xo + (1.2 if side == "R" else -1.2), ys[nm], 0.8)
            else:
                sh.term(ref, xo, ys[nm], side)
        lab = "BUS 2" if port == "BUS2" else ("BUS 1 free" if free else "BUS 1")
        sh.text(xe + (-1.3 if side == "L" else 1.3), ys[order[0]] - 4.6, lab, 6.2, True,
                L.LIGHT if free else GREY, ha="right" if side == "L" else "left", z=31)
    for nm in order:
        sh.text(x0 + 1.3, ys[nm], nm, 7.0, True, INK, z=31)
        sh.text(x0 + w - 1.3, ys[nm], nm, 7.0, True, INK, ha="right", z=31)
    return ys


def sheet_servo_bus(book):
    sh = Sheet(book, 2, "2_servo_bus", "SERVO BUS",
               "Adapter U2 gives DATA and GND only (D15). Three chains in ID order: kit cables between servos, made "
               "leads into BUS 2 of the first servo, power from the belly splices; second feeds into the ankle BUS 1 (D23).")
    X0, PITCH = 158.0, 50.0
    rows = [("NECK CHAIN", "trunk_top to head", ["SV30", "SV31", "SV32", "SV33"], ["S11", "S12", "S13"],
             46.0, True, (37, 84)),
            ("LEFT LEG CHAIN", "trunk_bottom and left_leg", ["SV20", "SV21", "SV22", "SV23", "SV24"],
             ["S2", "S3", "S4", "S5"], 110.0, False, (101, 157)),
            ("RIGHT LEG CHAIN", "trunk_bottom and right_leg", ["SV10", "SV11", "SV12", "SV13", "SV14"],
             ["S7", "S8", "S9", "S10"], 188.0, False, (179, 234))]
    yf = {}
    for name, sub, ids, kits, y0, flip, (ry0, ry1) in rows:
        sh.region(X0 - 48, ry0, 408, ry1, name, sub)
        prev = None
        for i, sv in enumerate(ids):
            ys = servo(sh, sv, X0 + i * PITCH, y0, flip=flip)
            if i == 0:
                yf[sv] = ys
            if prev:
                for nm in ("D", "V", "G"):
                    sh.w(f"{prev}.BUS1.{nm}", f"{sv}.BUS2.{nm}", lab=X0 + i * PITCH - 14.0)
            prev = sv
    yA, yB, yC = yf["SV30"], yf["SV20"], yf["SV10"]
    # ---------------- adapter and the made data leads (D15)
    ax0, ax1, ay0, ay1 = 16.0, 54.0, 160.0, 224.0
    sh.block("U2", ax0, ay0, ax1, ay1, "adapter", band=BAND_BUS, tsize=8.8, sub_y=ay0 + 9.0,
             sub=["Waveshare Bus", "Servo Adapter (A)"], subsize=6.2,
             pins=[("H3.D", "R", 180, "1 D"), ("H3.V", "R", 186, "2 V"), ("H3.G", "R", 192, "3 G"),
                   ("H5.D", "R", yC["D"], "1 D"), ("H5.V", "R", yC["V"], "2 V"), ("H5.G", "R", yC["G"], "3 G"),
                   ("DC+", "L", 184, "DC+"), ("DC-", "L", 190, "DC-"), ("JACK", "L", 200, "jack"),
                   ("JMP", "L", 207, "A/B"), ("USB", "D", 30, "USB-C")])
    sh.text(ax1 - 1.6, 175.6, "H3", 6.4, True, GREY, ha="right", z=31)
    sh.text(ax1 - 1.6, yC["D"] - 4.4, "H5", 6.4, True, GREY, ha="right", z=31)
    sh.lines(ax0, 147.5, ["H1 (DC+ DC-) and the jack: not connected (D15).",
                          "Jumper on B (USB). Logic from USB VBUS."], 6.6, GREY)
    sh.splice("YD3", 93, 160, lab_dx=-2.0, lab_dy=-2.8, ha="right")
    sh.splice("YG3", 95, 172, lab_dx=2.2, lab_dy=3.0)
    sh.w("U2.H3.D", "YD3.S", 93, lab=74)
    sh.w("U2.H3.G", "YG3.S", 95, lab=75)
    J = X0 - 40.0
    sh.splice("JG30", J, yA["G"], lab_dx=2.0, lab_dy=-4.0)
    sh.splice("JG20", J, yB["G"], lab_dx=-2.0, lab_dy=3.2, ha="right")
    sh.splice("JG10", J, yC["G"], lab_dx=-2.0, lab_dy=3.2, ha="right")
    for jg, sv in (("JG30", "SV30"), ("JG20", "SV20"), ("JG10", "SV10")):
        sh.w(f"{jg}.S", f"{sv}.BUS2.G", lab=J + 18.5)
    sh.w("YG3.S", "JG30.S", ("x", 70), ("y", yA["G"]), lab=92)
    sh.w("YD3.S", "SV30.BUS2.D", ("x", 86), ("y", yA["D"]), lab=128)
    sh.w("YD3.S", "SV20.BUS2.D", ("x", 100), ("y", yB["D"]), lab=128)
    sh.w("YG3.S", "JG20.S", ("x", 108), ("y", yB["G"]), lab=("y", 154.0))
    sh.w("U2.H5.D", "SV10.BUS2.D", lab=82)
    sh.w("U2.H5.G", "JG10.S", lab=82)
    # power injection at the first servo of each chain: stubs to the belly splices on sheet 1
    for sv, ys in (("SV30", yA), ("SV20", yB), ("SV10", yC)):
        sh.stub(f"{sv}.BUS2.V", "SPV.S", X0 - 4.4, ys["V"], "L", far="from SPV, 7.2 V")
    sh.stub("JG30.S", "SPG.S", J - 4.0, yA["G"] - 9.0, "L", ("y", yA["G"] - 9.0), far="from SPG, GND")
    sh.stub("JG20.S", "SPG.S", J + 4.0, yB["G"] + 14.0, "R", ("y", yB["G"] + 14.0), far="from SPG, GND")
    sh.stub("JG10.S", "SPG.S", J + 4.0, yC["G"] + 10.0, "R", ("y", yC["G"] + 10.0), far="from SPG, GND")
    sh.stub("U2.USB", "PI.USB", 36.0, 243.0, "R", ("y", 243.0), far="to Pi USB port")
    # D23: second feeds SP4 (ID 24) and SP5 (ID 14) from the belly splices into the ankle BUS 1, data cavity empty.
    # Both ankle housings have V above G, so one hop is unavoidable where SP5 G passes SP5 V.
    xa = X0 + 4 * PITCH + 22.0 + 2.6          # BUS 1 terminals of ID 24 and ID 14
    xGl, xVl, ySPV, ySPG = xa + 6.4, xa + 15.4, 166.0, 173.0
    sh.splice("SPV", xVl, ySPV, lab_dx=2.2, lab_dy=0.0)
    sh.splice("SPG", xGl, ySPG, lab_dx=-2.2, lab_dy=0.0, ha="right")
    sh.w("SV24.BUS1.V", "SPV.S", xVl, lab=("y", 148.0))
    sh.w("SV24.BUS1.G", "SPG.S", xGl, lab=("y", 155.5))
    sh.w("SV14.BUS1.V", "SPV.S", xVl, lab=("y", 186.0))
    sh.w("SV14.BUS1.G", "SPG.S", xGl, lab=("y", 190.0))
    sh.lines(xGl - 9.0, 163.2, [f"SPV, SPG: the belly splices ({book.term_where('SPV.S', sh.no)}): P11 in, SP1 to SP3 out.",
                                "SP4 and SP5 carry V and G only (D23); the ankle BUS 1 data cavity stays empty."],
             6.4, GREY, ha="right")
    sh.legend()
    sh.notes_box(152, 249, 270, 287, [
        "Housing cavities, Feetech numbering (STS3215 sheet 6-7): 1 GND, 2 Vcc, 3 signal, V in the middle. Waveshare "
        "counts its sockets from the other end (1 D, 2 V, 3 G). Copy a kit cable housing, then check with a meter. "
        "The neck row is drawn with G on top only to keep the drawing clean.",
        "kit = the 150 mm 5264-3P cable shipped with each STS3215, 1:1, gauge not published (as shipped). In on "
        "BUS 2, out on BUS 1 (Tnkr).",
    ])
    return sh


# ================================================================== sheet 3: Pi and sensors
def foot_switch(sh, cid, x0, y0, n_com=1, n_no=1):
    sh.block(cid, x0, y0, x0 + 26, y0 + 14, "SS-01", band=BAND_IO, tsize=8.4,
             pins=[("COM", "L", y0 + 10, "COM", n_com, 3.0), ("NO", "R", y0 + 10, "NO", n_no, 3.0),
                   ("NC", "D", x0 + 13, "NC")])


def sheet_pi(book):
    sh = Sheet(book, 3, "3_pi_sensors", "PI AND SENSORS",
               "Raspberry Pi header with every wire that leaves it, BNO055 IMU, foot switches with their pull-ups, "
               "and the USB cable to the servo adapter. Expression wires continue on sheet 4.")
    hx = 200.0
    x0, x1, yp = pi_header(sh, hx, 50.0, list(range(1, 21)), pitch=9.0,
                           slots={9: 3, 13: 2, 15: 2, 17: 2, 20: 3}, title="U4  Pi Zero 2 W header")
    sh.text((x0 + x1) / 2, yp[20] + 9.2, "pin 1: square pad, SD card end", 6.4, False, GREY, ha="center", free=True)
    # ---------------- BNO055
    sh.block("BNO", 24, 40, 66, 84, "BNO055", band=BAND_IO,
             pins=[("VIN", "R", yp[1], "VIN"), ("SDA", "R", yp[2], "SDA"), ("SCL", "R", yp[3], "SCL"),
                   ("GND", "R", 77.0, "GND"), ("3VO", "L", 56.0, "3VO"), ("RST", "L", 64.0, "RST")])
    sh.lines(24, 30.5, ["U7 Adafruit 2472 on trunk_top; D2 runs up the neck (sheet 5).",
                        "Pin order on the board not checked [I]."], 6.6, GREY)
    sh.w("PI.1", "BNO.VIN", lab=130)
    sh.w("PI.3", "BNO.SDA", lab=130)
    sh.w("PI.5", "BNO.SCL", lab=130)
    sh.w("PI.9", "BNO.GND", 100, sa=0, lab=84)
    # ---------------- foot switches (D17) and pull-ups at the header
    sh.region(38, 106, 82, 180, "RIGHT FOOT")
    sh.region(38, 182, 82, 248.5, "LEFT FOOT")
    foot_switch(sh, "FSR1", 46, 116, 2, 2)
    foot_switch(sh, "FSR2", 46, 160)
    foot_switch(sh, "FSL1", 46, 188, 2, 2)
    foot_switch(sh, "FSL2", 46, 230)            # 2 mm lower than FSR2's spacing so the 110 mm jumper label fits its run
    sh.w("PI.9", "FSL1.COM", 28, sa=1, sb=0, lab=("y", 150.0))
    sh.w("PI.9", "FSR1.COM", 36, sa=2, sb=0, lab=("y", 106.6))
    sh.w("PI.13", "FSR1.NO", 84, sa=0, sb=0, lab=132)
    sh.w("PI.15", "FSL1.NO", 92, sa=0, sb=0, lab=132)
    for a, b, x, lab in (("FSR1.COM", "FSR2.COM", 40, 149.0), ("FSR1.NO", "FSR2.NO", 80, 149.0),
                         ("FSL1.COM", "FSL2.COM", 40, 219.8), ("FSL1.NO", "FSL2.NO", 80, 219.8)):
        sh.w(a, b, x, sa=1, lab=("y", lab))
    # R5 (pin 13 to pin 17) and R4 (pin 15 to pin 17), 2.2 kOhm, soldered at the header
    resistor_v(sh, "RFR", 177.0, 115.0, 121.0, "R5")
    sh.term("RFR.2", 177.0, 115.0, "U")
    sh.term("RFR.1", 177.0, 121.0, "D")
    resistor_v(sh, "RFL", 188.0, 115.6, 119.4, "R4", side_note="L")
    sh.term("RFL.2", 188.0, 115.6, "U")
    sh.term("RFL.1", 188.0, 119.4, "D")
    sh.w("RFR.2", "PI.13", 105.5, sb=1, lab="none")
    sh.w("RFR.1", "PI.17", 123.5, sb=1, lab="none")
    sh.w("RFL.2", "PI.15", 114.5, sb=1, lab="none")
    sh.w("RFL.1", "PI.17", 120.5, sb=0, lab="none")
    sh.lines(150, 130.5, ["R5: D4 pull-up, R4: D3 pull-up, 2.2 kOhm,", "resistor leads soldered at the header, 0 mm (D17)"],
             6.6, INK)
    # ---------------- stubs to the expression sheet and the power sheet
    sh.stub("PI.33", "SGL.SIG", 194.0, yp[17], "L", far="to M1 signal, left antenna")
    sh.stub("PI.35", "AMP.LRC", 150.0, yp[18], "L", far="to U8 LRC")
    A, B = 256.0, 306.0
    for p_, far_ref, col, txt in ((2, "U3.VOUT", A, "from U3 VOUT"), (4, "J5.S", B, "to splice J5"),
                                  (6, "U3.GND.2", A, "from U3 GND"), (12, "AMP.BCLK", A, "to U8 BCLK"),
                                  (14, "JG.S", B, "to splice JG"), (16, "RR.1", A, "to R2, right eye"),
                                  (18, "RL.1", B, "to R1, left eye"), (22, "RP.1", B, "to R3, projector"),
                                  (32, "SGR.SIG", A, "to M2 signal, right antenna"), (40, "AMP.DIN", A, "to U8 DIN")):
        sh.stub(f"PI.{p_}", far_ref, col, yp[(p_ + 1) // 2], "R", far=txt)
    sh.stub_group("PI.20", ["LEDL.K", "LEDR.K", "LEDP.K"], A, "R", far="from the 3 LED cathodes")
    # ---------------- Pi ports and the USB cable to the adapter
    sh.block("PI", 318, 150, 358, 178, "ports", band=BAND_IO, title_ref=True,
             pins=[("USB", "R", 158.0, "USB"), ("PWR", "R", 165.0, "PWR IN"), ("CSI", "D", 330.0, "CSI")])
    sh.nc_note(360, 171.0, "PWR IN empty [I]")
    sh.stub("PI.CSI", "CAM.CSI", 326.0, 197.0, "L", ("y", 197.0), far="to U9 camera")
    sh.block("U2", 372, 202, 406, 226, "adapter", band=BAND_BUS, tsize=8.4,
             sub=["bus side:", "sheet 2"], subsize=6.4, sub_y=215,
             pins=[("USB", "U", 389.0, "USB-C")])
    sh.w("PI.USB", "U2.USB", 389.0, lab=("y", 180.0))
    sh.legend()
    sh.notes_box(152, 249, 270, 287, [
        "Pins follow the Runtime code at 376de65 (D9): eyes and antennas are swapped compared with the upstream "
        "assembly_guide table.",
        "GND pins 6, 9, 14, 20, 25, 30, 34, 39 are one net (pinout.xyz). Pins 9 and 20 take 3 wires each: twist "
        "and tin first [I].",
        "Feet: internal pull-up plus R4, R5 to 3V3; pressed = low, about 1.5 mA closed (D17).",
    ])
    return sh


# ================================================================== sheet 4: head expression
def resistor_h(sh, cid, x0, y, label, below=False):
    """Horizontal resistor: pin 1 on the left, pin 2 on the right."""
    sh.rect(x0, y - 2.2, x0 + 12, y + 2.2, fc="white", ec=INK, lw=0.9, z=14)
    sh.blocks.append((x0, y - 2.2, x0 + 12, y + 2.2, cid))
    sh.text(x0 + 6, y + (4.8 if below else -4.6), label, 6.8, True, INK, ha="center", free=True)
    sh.term(f"{cid}.1", x0 - 1.0, y, "L")
    sh.term(f"{cid}.2", x0 + 13.0, y, "R")
    sh.line([(x0 - 1.0, y), (x0, y)], "#8a8a8a", 0.9, z=13)
    sh.line([(x0 + 12, y), (x0 + 13.0, y)], "#8a8a8a", 0.9, z=13)


def led_h(sh, cid, x0, y, label, below=False):
    """LED: anode + on the left, cathode - on the right."""
    c = x0 + 7
    sh.ax.add_patch(L.Polygon([(c - 2.6, y - 2.8), (c - 2.6, y + 2.8), (c + 2.2, y)], closed=True, fc="#fff8d6",
                              ec=INK, lw=0.9, zorder=14))
    sh.line([(c + 2.2, y - 2.9), (c + 2.2, y + 2.9)], INK, 1.0, z=14)
    for dx in (0.0, 1.6):
        sh.line([(c + 0.4 + dx, y - 3.3), (c + 1.8 + dx, y - 5.0)], INK, 0.6, z=14)
    sh.line([(x0, y), (c - 2.6, y)], "#8a8a8a", 0.9, z=13)
    sh.line([(c + 2.2, y), (x0 + 14, y)], "#8a8a8a", 0.9, z=13)
    sh.text(x0 - 0.5, y - 3.2, "+", 7.0, True, INK, ha="center", z=31)
    sh.text(x0 + 14.5, y - 3.2, "-", 7.0, True, INK, ha="center", z=31)
    sh.blocks.append((c - 2.6, y - 2.9, c + 2.2, y + 2.9, cid))
    sh.text(c - 4.6, y + (5.0 if below else -4.8), label, 6.8, True, INK, ha="center", free=True)
    sh.term(f"{cid}.A", x0 - 1.0, y, "L")
    sh.term(f"{cid}.K", x0 + 15.0, y, "R")


def sheet_head(book):
    sh = Sheet(book, 4, "4_head_expression", "HEAD EXPRESSION",
               "Eye and projector LEDs with their resistors, antenna SG90s, I2S amplifier and speaker, camera. "
               "Splices J5 (5 V) and JG (GND) are drawn next to their loads; P17 feeds them from Pi pins 4 and 14.")
    rows = [2, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20]
    notes = {p_: book.pin_where(f"PI.{p_}", sh.no) for p_ in (3, 13, 15)}
    x0, x1, yp = pi_header(sh, 138, 46.0, rows, pitch=10.0, notes=notes, slots={20: 3, 12: 2, 35: 2}, gap=4.0,
                           title="U4  Pi header (part)", w_name=23.0)
    sh.T["PI.20"]["pitch"] = 4.0
    y = {p_: yp[(p_ + 1) // 2] for p_ in (4, 12, 14, 16, 17, 18, 20, 22, 32, 33, 35, 36, 37, 38, 39, 40)}
    # ---------------- LED loops (D13): pin -> 100 ohm -> LED -> cathode back to pin 20
    net = sh.net
    resistor_h(sh, "RL", 236, y[18], cref(net, "RL"))
    led_h(sh, "LEDL", 256, y[18], cref(net, "LEDL"))
    resistor_h(sh, "RR", 284, y[16], cref(net, "RR"))
    led_h(sh, "LEDR", 304, y[16], cref(net, "LEDR"))
    resistor_h(sh, "RP", 236, y[22], cref(net, "RP"), below=True)
    led_h(sh, "LEDP", 256, y[22], cref(net, "LEDP"), below=True)
    sh.w("PI.18", "RL.1", lab=218)
    sh.w("PI.16", "RR.1", lab=246)
    sh.w("PI.22", "RP.1", lab=218)
    for a, b in (("RL.2", "LEDL.A"), ("RR.2", "LEDR.A"), ("RP.2", "LEDP.A")):
        sh.w(a, b, lab="none")
    sh.w("LEDL.K", "PI.20", 277.0, y[20] - 4.0, sb=0, lab=218)
    sh.w("LEDR.K", "PI.20", 325.0, y[20], sb=1, lab=301)
    sh.w("LEDP.K", "PI.20", 277.0, y[20] + 4.0, sb=2, lab=218)
    sh.lines(240, y[22] + 10.0, [f"{cref(net, 'LEDL')} left eye, {cref(net, 'LEDR')} right eye, {cref(net, 'LEDP')} "
                                 "projector: 1 W LED beads (BOM E3).",
                                 f"{cref(net, 'RL')} to {cref(net, 'RP')}: 100 ohm 1/4 W. Joints D5, D6, D7: resistor "
                                 "lead to LED +, 0 mm,", "heat shrink [I]."], 6.4, GREY)
    # ---------------- loads at the bottom: SGL, SGR, AMP, speaker; JG above SGR, J5 below SGR
    yT, yB = 196.0, 222.0
    sh.block("SGL", 30, yT, 66, yB, "SG90", band=BAND_HEAD, tsize=8.4, sub=["left antenna"], subsize=6.4,
             sub_y=yT + 9.4, pins=[("GND", "U", 46, "-"), ("SIG", "L", yT + 16, "signal"), ("VCC", "D", 46, "+")])
    sh.block("SGR", 122, yT, 158, yB, "SG90", band=BAND_HEAD, tsize=8.4, sub=["right antenna"], subsize=6.4,
             sub_y=yT + 9.4, pins=[("GND", "U", 140, "-"), ("SIG", "R", yT + 16, "signal"), ("VCC", "D", 140, "+")])
    sh.block("AMP", 252, yT - 4, 306, yB + 4, "MAX98357A", band=BAND_HEAD, tsize=8.0,
             pins=[("GND", "U", 260, "GND"), ("DIN", "U", 273, "DIN"), ("BCLK", "U", 286, "BCLK"),
                   ("LRC", "U", 299, "LRC"), ("VIN", "D", 260, "Vin"), ("GAIN", "D", 278, "GAIN"),
                   ("SD", "D", 292, "SD"), ("SPK+", "R", yT + 5, "+"), ("SPK-", "R", yT + 15, "-")])
    sh.block("SPK", 364, yT - 2, 392, yB + 2, "speaker", band=BAND_HEAD, tsize=8.0,
             sub=["8 ohm 2 W"], subsize=6.4, sub_y=yT + 19,
             pins=[("+", "L", yT + 5, "+"), ("-", "L", yT + 15, "-")])
    sh.w("AMP.SPK+", "SPK.+", lab=335)
    sh.w("AMP.SPK-", "SPK.-", lab=335)
    xP, xB, xL, xV = 336.0, 344.0, 350.0, 402.0
    sh.splice("JG", 140, 182.0, lab_dx=-2.0, lab_dy=-2.8, ha="right")
    sh.splice("J5", 140, 236.0, lab_dx=-2.0, lab_dy=2.8, ha="right")
    sh.w("PI.14", "JG.S", xP, 177.0, 140, lab=("y", 150.0))
    sh.w("PI.4", "J5.S", xV, 244.0, 140, lab=("y", 150.0))
    sh.w("PI.12", "AMP.BCLK", xB, 186.0, 286, lab=("y", 150.0))
    sh.w("PI.40", "AMP.DIN", 273, lab=232)
    sh.w("JG.S", "SGL.GND", ("x", 46), lab=92)
    sh.w("JG.S", "SGR.GND", lab=("tag", 140, 189.0, 0.0))
    sh.w("JG.S", "AMP.GND", ("x", 260), lab=236)
    sh.w("J5.S", "SGL.VCC", ("x", 46), lab=92)
    sh.w("J5.S", "SGR.VCC", lab=("tag", 140, 229.5, 0.0))
    sh.w("J5.S", "AMP.VIN", ("x", 260), lab=200)
    sh.w("PI.32", "SGR.SIG", 206, lab=182)
    sh.w("PI.33", "SGL.SIG", 20, lab=86)
    sh.w("PI.35", "AMP.LRC", 128, 30.0, xL, 190.0, 299, lab=262)
    # ---------------- I2S mics (D47): MICL on D14 to the header, MICR on D15 from MICL; SEL bridged on each board
    mp = [("3V", "3V"), ("GND", "GND"), ("BCLK", "BCLK"), ("LRCL", "LRCL"), ("DOUT", "DOUT")]
    ym = [97.0 + 6.0 * k for k in range(5)]
    sh.block("MICR", 22, 88, 58, 128, "mic R", band=BAND_HEAD, tsize=7.6, sub=["SEL to 3V", "right slot"], subsize=6.0,
             sub_y=112.0, pins=[(p_, "R", ym[k], t) for k, (p_, t) in enumerate(mp)])
    sh.block("MICL", 76, 88, 112, 128, "mic L", band=BAND_HEAD, tsize=7.6, sub=["SEL to GND", "left slot"], subsize=6.0,
             sub_y=112.0, pins=[(p_, "R", ym[k], t, 2, 2.0) for k, (p_, t) in enumerate(mp)])
    for k, (p_, _t) in enumerate(mp):
        sh.w(f"MICL.{p_}", f"MICR.{p_}", 114.0 + 1.6 * k, 85.5 - 1.2 * k, 60.5 + 2.4 * k, sa=1, lab="none" if k else 90)
    sh.w("MICL.3V", "PI.17", 123.0, lab="none")
    sh.w("MICL.LRCL", "PI.35", 125.0, sb=1, lab="none")
    sh.w("MICL.GND", "PI.39", 131.0, lab="none")
    sh.w("MICL.BCLK", "PI.12", 133.0, 174.0, 212.0, sb=1, lab="none")
    sh.w("MICL.DOUT", "PI.38", 135.0, 172.5, 209.0, lab=("y", 150.0))
    # D13: Pi GPIO26 (pin 37) to the Pololu 2813 OFF input (D30)
    sh.block("SW1", 22, 150, 58, 166, "2813 (part)", band=BAND_IO, tsize=7.0, pins=[("OFF", "R", y[37], "OFF")])
    sh.w("PI.37", "SW1.OFF", lab=96)
    # D48: GPIO16 to the amp SD pin (amp off while the duck listens)
    sh.w("PI.36", "AMP.SD", 215.0, 231.0, lab="none")
    # camera on the CSI port
    sh.block("PI", 90, 60, 124, 80, "CSI", band=BAND_IO, tsize=8.4, pins=[("CSI", "L", 72, "FPC")])
    sh.block("CAM", 20, 60, 50, 80, "camera", band=BAND_HEAD, tsize=8.0, pins=[("CSI", "R", 72, "FPC")])
    sh.w("PI.CSI", "CAM.CSI")
    sh.legend()
    sh.notes_box(152, 249, 270, 287, [
        "D13: each LED through 100 ohm, about 3 mA. Upstream issue 34: no 1 W LED straight on a GPIO.",
        "SG90 lead colours (orange, red, brown) are [I] in the netlist: check the lead. MAX98357A GAIN "
        "not connected (SD: D48, GPIO16). Terminal order of U8 on the board not checked [I].",
    ])
    return sh


# ================================================================== sheet 5: harness overview
JAB = {"neck_pitch": "NP", "head_pitch": "HP", "head_yaw": "HY", "head_roll": "HR",
       "left_hip_yaw": "LHY", "left_hip_roll": "LHR", "left_hip_pitch": "LHP", "left_knee": "LK", "left_ankle": "LA",
       "right_hip_yaw": "RHY", "right_hip_roll": "RHR", "right_hip_pitch": "RHP", "right_knee": "RK",
       "right_ankle": "RA"}
FAM_COL = {"p": "#c62828", "d": "#1f6fd1", "s": "#2e7d32"}


def fam(cid):
    return "s" if cid.startswith("S") and not cid.startswith(("SP", "SD")) else ("p" if cid.startswith(("P", "SP")) else "d")


def chip(sh, x, y, cid, size=6.6):
    w_ = L.tw(cid, size, True) + 2.0
    sh.rect(x - w_ / 2, y - 1.8, x + w_ / 2, y + 1.8, fc=FAM_COL[fam(cid)], ec="white", lw=0.4, z=52, r=0.6)
    sh.text(x, y + 0.1, cid, size, True, "white", ha="center", z=53)
    sh.drawn_cables.add(cid)
    return w_


def tag(sh, x0, y0, x1, y1, text, size=6.6):
    sh.rect(x0, y0, x1, y1, fc="#ffffff", ec="#6f7c86", lw=0.6, z=30, r=0.8)
    sh.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.1, text, size, True, INK, ha="center", z=31)


def joint_line(sh, x0, x1, y, name, side="L", short=False):
    sh.line([(x0, y), (x1, y)], "#7b3fa0", 0.8, z=25, ls=(0, (3, 2)))
    txt = JAB[name] if short else f"{name} ({JAB[name]})"
    if side == "L":
        sh.text(x0 - 1.5, y, txt, 6.2, True, "#7b3fa0", ha="right", z=31, free=True)
    else:
        sh.text(x1 + 1.5, y, txt, 6.2, True, "#7b3fa0", z=31, free=True)


def cable_ends_text(net, cid):
    ws = [w for w in net.active_wires if w["cable"] == cid]
    ref = lambda r: net.comp(r.split(".")[0])["ref"]
    froms, tos, order = set(), set(), []
    for w in ws:
        for k in ("from", "to"):
            rr = ref(w[k])
            if rr not in order:
                order.append(rr)
        froms.add(ref(w["from"]))
        tos.add(ref(w["to"]))
    start = [r for r in order if r in froms and r not in tos]
    end = [r for r in order if r in tos and r not in froms]
    via = [r for r in order if r in froms and r in tos]
    if not start or not end:
        return f"{order[0]} to " + ", ".join(order[1:]) + f", back to {order[0]}"
    txt = ", ".join(start) + " to " + ", ".join(end)
    if via:
        txt += " via " + ", ".join(via)
    return txt


def wire_text(ws):
    counts = collections.OrderedDict()
    for w in ws:
        g = "kit" if w["gauge"] == "kit cable" else w["gauge"]
        counts[g] = counts.get(g, 0) + 1
    return ", ".join(f"{g} x{n}" for g, n in counts.items())


def sheet_harness(book):
    sh = Sheet(book, 5, "5_harness", "HARNESS OVERVIEW",
               "Where each cable runs, seen from behind (robot left on the left), not to scale: body regions, the "
               "joints a cable crosses, and every active cable id with its wire, cut length and joints.")
    sh.drawn_cables = set()
    net = sh.net
    R = {"head": (64, 30, 200, 60), "neck": (84, 70, 172, 106), "trunk_top": (16, 114, 238, 134),
         "battery_bay": (36, 144, 124, 170), "belly": (132, 144, 220, 170), "trunk_bottom": (16, 180, 238, 194),
         "left_leg": (16, 204, 112, 246), "right_leg": (146, 204, 238, 246)}
    NAMES = {"head": "HEAD", "neck": "NECK", "trunk_top": "TRUNK_TOP", "battery_bay": "BATTERY BAY",
             "belly": "BELLY", "trunk_bottom": "TRUNK_BOTTOM", "left_leg": "LEFT LEG", "right_leg": "RIGHT LEG"}
    TX = {"trunk_top": 34.0, "trunk_bottom": 80.0, "left_leg": 34.0, "right_leg": 150.0}
    for k, (a, b, c, d) in R.items():
        sh.region(a, b, c, d, NAMES[k], tx=TX.get(k))
    # joints: head and neck (labels on the left), legs (short labels in the gap between the legs)
    joint_line(sh, 84, 172, 65.0, "head_roll")
    joint_line(sh, 84, 172, 83.0, "head_yaw")
    joint_line(sh, 84, 172, 90.0, "head_pitch")
    joint_line(sh, 84, 172, 110.0, "neck_pitch")
    leg_j = (("hip_yaw", 199.0), ("hip_roll", 211.5), ("hip_pitch", 221.5), ("knee", 231.5), ("ankle", 241.0))
    for side, (a, b, c, d) in (("left", R["left_leg"]), ("right", R["right_leg"])):
        for jn, yy in leg_j:
            joint_line(sh, a, c, yy, f"{side}_{jn}", side="R" if side == "left" else "L", short=True)
    # tags
    tag(sh, 98, 36, 146, 41, "U4 Pi (header, USB, CSI)")
    tag(sh, 106, 46, 118, 51, "U3")
    tag(sh, 150, 52, 166, 57, "ID 33")
    tag(sh, 150, 73, 166, 78, "ID 32")
    tag(sh, 150, 95, 166, 100, "ID 31")
    tag(sh, 150, 119, 166, 124, "ID 30")
    tag(sh, 111, 119, 125, 124, "BNO055", 6.0)
    tag(sh, 176, 119, 214, 124, "U2 adapter, YD3 YG3")
    tag(sh, 94, 151, 122, 156, "SW1 VSW G")
    tag(sh, 136, 151, 178, 156, "U1 BEC, JB, SPV SPG")
    tag(sh, 184, 159, 214, 164, "D1 slack coil")
    tag(sh, 46, 185, 76, 190, "ID 20, JG20")
    tag(sh, 184, 185, 214, 190, "ID 10, JG10")
    for side, x0 in (("L", 50), ("R", 176)):
        ids = (21, 22, 23, 24) if side == "L" else (11, 12, 13, 14)
        for k, yy in enumerate((204.6, 214.6, 224.6, 234.2)):
            tag(sh, x0, yy, x0 + 16, yy + 4.0, f"ID {ids[k]}", 6.0)
    tag(sh, 22, 242.4, 50, 245.8, "SL1 SL2", 5.6)
    tag(sh, 206, 242.4, 234, 245.8, "SR1 SR2", 5.6)
    # lanes through the neck
    xD3, xP13, xD2, xD1, xD4, xS = 100.0, 112.0, 118.0, 130.0, 138.0, 158.0
    sh.lane("P13", [(xP13, 51), (xP13, 151)], "p")
    sh.lane("D2", [(xD2, 41), (xD2, 119)], "d")
    sh.lane("D3", [(xD3, 41), (xD3, 128), (26, 128), (26, 242.4)], "d")
    sh.lane("D4", [(xD4, 41), (xD4, 116), (230, 116), (230, 242.4)], "d")
    sh.lane("D1", [(xD1, 41), (xD1, 128), (195, 128), (195, 124)], "d")
    sh.line([(208, 124), (208, 159)], FAM_COL["d"], 1.4, z=21, ls=(0, (2, 1.5)))
    sh.lane("S13", [(xS, 73), (xS, 57)], "s")
    sh.lane("S12", [(xS, 95), (xS, 78)], "s")
    sh.lane("S11", [(xS, 119), (xS, 100)], "s")
    sh.lane("SD1", [(180, 124), (180, 138), (66, 138), (66, 185)], "d")
    sh.lane("SD2", [(206, 124), (206, 140), (222, 140), (222, 176), (204, 176), (204, 185)], "d")
    sh.lane("SP3", [(164, 151), (164, 124)], "p")
    sh.lane("SP1", [(146, 156), (146, 174), (56, 174), (56, 185)], "p")
    sh.lane("SP2", [(170, 156), (170, 178), (194, 178), (194, 185)], "p")
    sh.lane("P10", [(122, 153.5), (136, 153.5)], "p")
    # D23 second feeds: belly splices to the ankle servos, crossing hip yaw, hip roll, hip pitch and knee
    sh.lane("SP4", [(142, 156), (142, 172), (32, 172), (32, 236.2), (50, 236.2)], "p")
    sh.lane("SP5", [(160, 156), (160, 176), (148, 176), (148, 236.2), (176, 236.2)], "p")
    sh.lane("S2", [(58, 190), (58, 204.6)], "s")
    sh.lane("S7", [(184, 190), (184, 204.6)], "s")
    for cid, x, y0, y1 in (("S3", 58, 208.6, 214.6), ("S4", 58, 218.6, 224.6), ("S5", 58, 228.6, 234.2),
                           ("S8", 184, 208.6, 214.6), ("S9", 184, 218.6, 224.6), ("S10", 184, 228.6, 234.2)):
        sh.lane(cid, [(x, y0), (x, y1)], "s")
    # chips: neck bundle inside the neck, kit cables on the joint they cross
    for cid, x, y in (("D3", xD3, 100.5), ("P13", xP13, 100.5), ("D2", xD2, 100.5), ("D1", xD1, 100.5),
                      ("D4", xD4, 100.5), ("P13", xP13, 147.6), ("D3", 26, 158.0), ("D4", 230, 158.0),
                      ("D2", xD2, 116.0), ("D1", 160, 128.0), ("S13", xS, 65.0), ("S12", xS, 86.5),
                      ("S11", xS, 110.0), ("SD1", 100, 138.0), ("SD2", 222, 158.0), ("SP3", 164, 140.0),
                      ("SP1", 100, 174.0), ("SP2", 182, 178.0), ("P10", 129, 153.5), ("S2", 58, 199.0),
                      ("S7", 184, 199.0), ("S3", 58, 211.5), ("S4", 58, 221.5), ("S5", 58, 231.5),
                      ("S8", 184, 211.5), ("S9", 184, 221.5), ("S10", 184, 231.5), ("D3", 26, 222.0),
                      ("D4", 230, 222.0), ("SP4", 122, 172.0), ("SP4", 32, 216.5), ("SP5", 148, 216.5)):
        chip(sh, x, y, cid)
    # local cables (one region, no joint crossed)
    local = collections.defaultdict(list)
    for cid in net.active:
        c = net.cables[cid]
        if len(c["regions"]) == 1 and not c["joints"]:
            local[c["regions"][0]].append(cid)
    spots = {"head": (66, 46.5, 96), "battery_bay": (38, 156.5, 92), "belly": (148, 164.5, 182)}
    for reg, cids in local.items():
        x, y, xmax = spots[reg]
        sh.text(x, y - 4.4, "local:", 6.0, True, GREY, z=31)
        xx = x
        for cid in cids:
            wch = L.tw(cid, 6.0, True) + 2.0
            if xx + wch > xmax:
                xx, y = x, y + 4.4
            chip(sh, xx + wch / 2, y, cid, 6.0)
            xx += wch + 1.0
    # ---------------- cable table
    X0 = 246.0
    cx = {"id": X0, "run": X0 + 11, "wire": X0 + 75, "cut": X0 + 110, "joints": X0 + 128}
    y0 = 34.0
    for k, hname in (("id", "ID"), ("run", "run (from, to, via)"), ("wire", "wire"), ("cut", "cut mm"),
                     ("joints", "joints crossed")):
        sh.text(cx[k], y0, hname, 6.8, True, GREY, z=31)
    sh.line([(X0 - 1, y0 + 2.0), (W_ - 11, y0 + 2.0)], "#90a4ae", 0.5, z=30)
    order = sorted(net.active, key=lambda c: (["P", "SP", "SD", "D", "S"].index(
        "SP" if c.startswith("SP") else "SD" if c.startswith("SD") else c[0]), int("".join(ch for ch in c if ch.isdigit()))))
    pitch = 4.2
    for i, cid in enumerate(order):
        yy = y0 + 5.2 + i * pitch
        if i % 2 == 0:
            sh.rect(X0 - 1, yy - pitch / 2, W_ - 11, yy + pitch / 2, fc="#f3f5f7", ec="none", lw=0, z=29)
        ws = [w for w in net.active_wires if w["cable"] == cid]
        cuts = sorted({int(w["cut_mm"]) for w in ws if w["cut_mm"] not in (None, 0)})
        cut_t = "/".join(str(c) for c in cuts) if len(cuts) <= 3 else f"{cuts[0]} to {cuts[-1]}"
        if any(w["cut_mm"] is None for w in ws):
            cut_t = (cut_t + ", leads" if cut_t else "as shipped")
        jt = " ".join(JAB[j] for j in net.cables[cid]["joints"]) or "none"
        chip(sh, X0 + 4.5, yy, cid, 6.0)
        sh.text(cx["run"], yy, cable_ends_text(net, cid), 6.0, False, INK, z=31)
        sh.text(cx["wire"], yy, wire_text(ws), 6.0, False, INK, z=31)
        sh.text(cx["cut"], yy, cut_t, 6.0, False, INK, z=31)
        sh.text(cx["joints"], yy, jt, 6.0, False, "#7b3fa0", z=31)
        sh.table_cables = getattr(sh, "table_cables", set()) | {cid}
    yy = y0 + 5.2 + len(order) * pitch + 1.0
    rem = [c for c, cb in net.cables.items() if cb["status"] != "active"]
    sh.text(X0, yy, "Removed (D15), not drawn: " + ", ".join(rem), 6.0, False, "#b3261e", z=31)
    sh.text(X0, yy + 3.4, "Joints: NP neck_pitch, HP head_pitch, HY head_yaw, HR head_roll; L or R then HY HR HP K A:",
            6.0, False, "#7b3fa0", z=31)
    sh.text(X0, yy + 6.4, "hip yaw, hip roll, hip pitch, knee, ankle. Per-wire detail: sheets 1 to 4; routes: CABLE_MAP.md.",
            6.0, False, "#7b3fa0", z=31)
    sh.legend()
    sh.notes_box(152, 249, 270, 287, [
        "Lanes: red power, blue data and signal, green kit servo cables. A chip on a dashed joint line marks the "
        "joint that cable crosses. Local cables stay inside one region and cross no joint.",
        "D1 slack (Adafruit 3878, 0.9 m) is coiled in the belly (dashed). Kit hops S2 to S12 need a test fit at both "
        "joint limits (CABLE_MAP.md, B17).",
    ])
    missing = sorted(set(net.active) - sh.drawn_cables)
    if missing:
        raise SystemExit(f"sheet 5: active cables not drawn on the harness map: {missing}")
    if set(net.active) - sh.table_cables:
        raise SystemExit(f"sheet 5: active cables missing from the table: {sorted(set(net.active) - sh.table_cables)}")
    sh.tb_extra = (f"Cables shown: {len(sh.drawn_cables & set(net.active))} of {len(net.active)} active "
                   f"(all {len(net.active_wires)} wires, as cables)")
    return sh


# ================================================================== main
BUILDERS = [sheet_power, sheet_servo_bus, sheet_pi, sheet_head, sheet_harness]


def build(book):
    sheets = []
    for b in BUILDERS:
        sh = b(book)
        n_full = len({r["w"]["n"] for r in sh.routes if r["kind"] == "full"})
        n_stub = len({r["w"]["n"] for r in sh.routes if r["kind"] == "stub"})
        sh.frame()
        sh.heading()
        sh.title_block(n_full, n_stub, len(book.net.active_wires), extra=getattr(sh, "tb_extra", None))
        sh.finish()
        sheets.append(sh)
    return sheets


def check_coverage(book, sheets):
    net = book.net
    full = collections.defaultdict(list)
    for sh in sheets:
        if sh.no > 4:
            continue
        for r in sh.routes:
            if r["kind"] == "full" and sh.no not in full[r["w"]["n"]]:
                full[r["w"]["n"]].append(sh.no)
    missing = [w for w in net.active_wires if w["n"] not in full]
    if missing:
        lines = [f"  row {w['n']}: {w['cable']} {w['from']} - {w['to']}" for w in missing]
        raise SystemExit("active netlist wires not drawn in full on any of sheets 1 to 4:\n" + "\n".join(lines))
    return full


def write_md(book, sheets, full, sizes, n_warn):
    net = book.net
    n_all = len(net.active_wires)
    r = lambda cid: cref(net, cid)
    titles = {1: ("Power", f"pack {r('PACK')}, BMS {r('BMS')}, charger {r('CHG')}, XT30 {r('XT30')}, fuse {r('F1')} with "
                  f"the lead splices {r('JFI')} {r('JFO')}, Pololu 2815 {r('SW1')} and panel switch {r('CTL')}, splices "
                  f"VSW and G, BEC {r('U1')} with JB+ JB-, belly splices SPV SPG, the first-servo power feeds SP1 to "
                  "SP3 with JG20 JG30 JG10 (SP4 SP5 cross-referenced to sheet 2), and the 5 V branch P13 up the neck to "
                  "U3 and P12 to Pi pins 2 and 6"),
              2: ("Servo bus", "adapter U2 (DATA and GND only, D15), Y splices YD3 YG3, made leads SD1 SD2 and the SP "
                  "tails, the 3 chains in ID order (neck 30 to 33, left leg 20 to 24, right leg 10 to 14) with every "
                  "kit cable conductor, power injection at BUS 2 of IDs 30, 20, 10, and the second feeds SP4 SP5 from "
                  "SPV SPG into BUS 1 of IDs 24 and 14 (D23)"),
              3: ("Pi and sensors", "the 40-pin header with every wire that leaves it (sensor wires in full, the rest "
                  "as flagged stubs), BNO055 U7, foot switches SR1 SR2 SL1 SL2 with jumpers and pull-ups R4 R5, "
                  "USB cable D1 to the adapter"),
              4: ("Head expression", f"eye and projector LEDs {r('LEDL')} to {r('LEDP')} with {r('RL')} to {r('RP')}, "
                  f"antenna SG90s {r('SGL')} {r('SGR')}, MAX98357A {r('AMP')} and speaker {r('SPK')}, camera {r('CAM')}, "
                  "splices J5 and JG fed by P17"),
              5: ("Harness overview", "body regions and joints, a lane per cable that leaves its region, local cables "
                  "per region, and a table of all active cables (run, wire, cut length, joints crossed)")}
    out = []
    out.append("# WIRING_SHEETS: per-subsystem wiring drawings")
    out.append("")
    out.append(f"Generated by `wiring/sheets/make_sheets.py` on {book.date} (TZ=America/New_York date) from "
               f"`wiring/netlist.yaml` rev {net.rev} (sha256 {net.sha}). Do not edit by hand: change netlist.yaml "
               "and run the generator again. Owner: wiring drawings agent (W).")
    out.append("")
    out.append("These five sheets redraw the wiring one subsystem per sheet: blocks with their real terminal names, "
               "connectors with their pin order, orthogonal wires in the insulation colour, and a label on every wire "
               "(cable id, gauge, cut length, colour code). Every wire is looked up in the netlist by its two end pins "
               "and drawn from one placed terminal to the other, so a sheet cannot show a connection the netlist does "
               "not have.")
    out.append("")
    out.append("## Sheets")
    out.append("")
    out.append("| Sheet | Files | Shows | Crossings (hops) |")
    out.append("|---|---|---|---|")
    for sh in sheets:
        t, d = titles[sh.no]
        out.append(f"| {sh.no} {t} | [{sh.key}.svg]({sh.key}.svg), [{sh.key}.png]({sh.key}.png) "
                   f"({sizes[sh.no][1] // 1000} kB) | {d} | {sh.n_cross} |")
    out.append("")
    out.append("All sheets are A3 landscape (420 x 297 mm) with a zone grid (columns 1 to 8, rows A to F). A flag "
               "or note such as \"sheet 4, zone E3\" points to where the far end of that wire is drawn. PNGs are "
               "200 dpi; the SVGs carry the text as outlines so they look the same on any phone or browser (the "
               "SVG text is therefore not searchable). Print on A3 or tabloid at 100 %: wire labels are 7.4 pt and "
               "the smallest notes 6 pt. On Letter (fit to page, 66 %) that becomes about 5 pt and 4 pt: fine for an "
               "overview, use A3 or the phone at the bench.")
    out.append("")
    out.append("## Coverage")
    out.append("")
    out.append(f"The netlist has {n_all} active wires (one row per conductor in `wires`) on {len(net.active)} active "
               "cables. A wire counts as drawn on a sheet only when it is drawn in full, terminal to terminal. A stub "
               "is the start of a wire that is drawn in full on another sheet; it ends in a flag that carries the "
               "wire label and the sheet and zone of the far end. The generator stops with an error if any active "
               "wire is not drawn in full on at least one of sheets 1 to 4, or if any active cable is missing from "
               "sheet 5.")
    out.append("")
    out.append("| Sheet | Wires drawn in full / wires in the netlist | Share | Stubs (drawn in full elsewhere) | Cables touched |")
    out.append("|---|---|---|---|---|")
    for sh in sheets:
        if sh.no > 4:
            continue
        cabs = {r["w"]["cable"] for r in sh.routes if r["kind"] in ("full", "stub")}
        out.append(f"| {sh.no} {titles[sh.no][0]} | {sh.n_full} / {n_all} | {100 * sh.n_full / n_all:.0f} % | "
                   f"{sh.n_stub} | {len(cabs)} |")
    union = len(full)
    out.append(f"| Sheets 1 to 4 together | {union} / {n_all} | {100 * union / n_all:.0f} % | | "
               f"{len({w['cable'] for w in net.active_wires if w['n'] in full})} / {len(net.active)} |")
    sh5 = [s_ for s_ in sheets if s_.no == 5][0]
    out.append(f"| 5 Harness overview | {n_all} / {n_all} as cables | 100 % | | "
               f"{len(sh5.drawn_cables & set(net.active))} / {len(net.active)} (lane or local chip, and the table) |")
    out.append("")
    out.append("Some wires are drawn in full on two sheets on purpose: the SP1 to SP3 tails (JG to the first servo G) "
               "appear on sheets 1 and 2.")
    out.append("")
    out.append("### Where each cable is drawn in full")
    out.append("")
    out.append("| Cable | Wires | Sheets |")
    out.append("|---|---|---|")
    order = sorted(net.active, key=lambda c: (["P", "SP", "SD", "D", "S"].index(
        "SP" if c.startswith("SP") else "SD" if c.startswith("SD") else c[0]), int("".join(ch for ch in c if ch.isdigit()))))
    for cid in order:
        ws = [w for w in net.active_wires if w["cable"] == cid]
        shs = sorted({x for w in ws for x in full[w["n"]]})
        out.append(f"| {cid} | {len(ws)} | {', '.join(str(x) for x in shs)} |")
    out.append("")
    out.append("## How to regenerate")
    out.append("")
    out.append("```")
    out.append("python3 altaay_lab/wiring/sheets/make_sheets.py            # writes the 5 SVG + PNG and this file")
    out.append("python3 altaay_lab/wiring/sheets/make_sheets.py --strict   # also fails on any layout warning")
    out.append("```")
    out.append("")
    out.append("Needs Python 3 with matplotlib, PyYAML and Pillow, and the Carlito font (Debian/Ubuntu package "
               "fonts-crosextra-carlito). `ODM_NETLIST=path` points the generator at another netlist. Layout lives in "
               "`make_sheets.py` (one function per sheet); drawing rules and checks live in `sheetlib.py`: the run "
               "stops on an unknown pin pair, a diagonal segment, a wire leaving a terminal the wrong way, a slot used "
               "twice, a stub whose wire is not drawn in full elsewhere, or a dash in any drawing text. Layout warnings "
               "(labels on other wires, wires through blocks, overlaps) are printed; `--strict` turns them into errors. "
               f"This run printed {n_warn} layout warning(s).")
    out.append("")
    out.append("## Conventions on the sheets")
    out.append("")
    out.append("- Seen from behind: robot left is on the left (netlist meta).")
    out.append("- Wire colour = insulation colour from the netlist, with the IEC 60757 code in the label (RD, BK, YE, "
               "WH, GN, BU, OG, BN). Grey with white dashes = colour not set by the netlist (kit servo cables, fuse "
               "holder leads). Thin grey = bare resistor lead (0 mm wires in the netlist).")
    out.append("- Line weight follows the gauge. Label = cable id (as in CABLE_MAP.md), branch when the netlist has "
               "one, gauge, cut length (\"as shipped\" when the netlist has none), colour code.")
    out.append("- Splices are black dots; a hop is a crossing with no contact; a cross marks a pin that is not "
               "connected (nc in the netlist).")
    out.append("- Resistor leads that are soldered straight to a pin carry one tag per resistor instead of a label "
               "on each 0 mm lead.")
    out.append("- The servo housings are drawn D V G with V in the middle. The neck row on sheet 2 is drawn G V D "
               "only to keep the Y splices from crossing. The netlist numbers the servo pins as the Feetech sheet "
               "does (1 GND, 2 Vcc, 3 signal); the Waveshare adapter counts from the other end (1 D, 2 V, 3 G).")
    out.append("")
    out.append("## Netlist questions")
    out.append("")
    q = []
    clash = sorted(c["ref"] for c in net.comps.values() if c["ref"] in net.cables)
    if clash:
        q.append(f"Component refs {', '.join(clash)} are also cable ids ({', '.join(clash)} in `cables`): rename them "
                 "so a label is never ambiguous.")
    q.append("Terminal order on the board is marked [I] (not checked) for BNO055, MAX98357A, D30V30F5 and the "
             "charger pads, and the panel switch lugs are [I]. The sheets draw these blocks in the order that keeps "
             "the wires straight and say so on the sheet; check the order on the parts.")
    out.append("Open:")
    out.append("")
    for i, x in enumerate(q):
        out.append(f"{i + 1}. {x}")
    out.append("")
    out.append("Answered in the netlist pass of 2026-11-02: the LED refs are LED1 to LED3 and the panel switch is SW2; "
               "the servo BUS pins carry the Feetech pin numbers (STS3215 sheet item 6-7), and the build sheets say "
               "to copy a kit cable housing and check with a meter; SW1 and U1 pins have printable labels (SW, GND, "
               "IN+, IN-, 1+, 1-, 2+, 2-); the BEC output lead and kit cable gauges are not published, so they stay "
               "as shipped (no AWG in the netlist).")
    out.append("")
    out.append("## Relation to the older drawings")
    out.append("")
    out.append("These sheets cover what `wiring/odm_v2_wiring_pictorial` (A2), `wiring/odm_v2_schematic` (A3) and "
               "`wiring/odm_v2_harness` (A3) show, from the same netlist, and add per-wire labels, pin order, "
               "cross-sheet references and a hard coverage check per wire. WIRING.md marks those three and their "
               "generators superseded; they are not regenerated and do not show the changes from 2026-11-02 on.")
    out.append("")
    text = "\n".join(out) + "\n"
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("dash in WIRING_SHEETS.md")
    open(os.path.join(OUTDIR, "WIRING_SHEETS.md"), "w", encoding="utf-8").write(text)


def main():
    strict = "--strict" in sys.argv
    book = Book()
    book.n_sheets = 5
    book.complete = len(BUILDERS) == 5
    for p in (1, 2):
        book.pass_no = p
        sheets = build(book)
        if p == 1:
            for s in sheets:
                book.terms[s.no] = {k: (v["x"], v["y"]) for k, v in s.T.items()}
                for r in s.routes:
                    if r["kind"] == "full" and s.no not in book.full[r["w"]["n"]]:
                        book.full[r["w"]["n"]].append(s.no)
                L.plt.close(s.fig)
    full = check_coverage(book, sheets)
    n_warn, sizes = 0, {}
    for s in sheets:
        svg, png = s.save(OUTDIR)
        sizes[s.no] = (os.path.getsize(svg), os.path.getsize(png))
        print(f"sheet {s.no}: {os.path.basename(png)} {sizes[s.no][1]} bytes, svg {sizes[s.no][0]} bytes, "
              f"full {s.n_full}, stubs {s.n_stub}, crossings {s.n_cross}")
        for w_ in s.warn:
            print("  WARN", w_)
        n_warn += len(s.warn)
        if sizes[s.no][1] >= 1_000_000:
            raise SystemExit(f"{png} is {sizes[s.no][1]} bytes, over 1 MB")
    write_md(book, sheets, full, sizes, n_warn)
    print(f"coverage: {len(full)} of {len(book.net.active_wires)} active wires drawn in full on sheets 1 to 4")
    if strict and n_warn:
        raise SystemExit(f"{n_warn} layout warning(s) with --strict")


if __name__ == "__main__":
    main()
