"""Wiring sheet 7: the charging dock, generated from twin/dock/dock_netlist.yaml with the sheet library of make_sheets.py.

Writes 7_dock.svg and 7_dock.png next to this script (or into ODM_SHEETS_OUT). Stops with an error if any dock wire is not drawn in full.
Usage: python3 altaay_lab/wiring/sheets/make_dock_sheet.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
os.environ["ODM_NETLIST"] = os.path.join(LAB, "twin", "dock", "dock_netlist.yaml")
sys.path.insert(0, HERE)
import sheetlib as L  # noqa: E402
from sheetlib import Sheet, Book  # noqa: E402

BAND_PWR, BAND_IO, BAND_DUCK = "#fde4e1", "#e2ecf8", "#e3f1e6"


def sheet_dock(book):
    sh = Sheet(book, 7, "7_dock", "CHARGING DOCK",
               "The dock's own wiring (D43, D45, D50): adapter, fuse, the 2815 gate switch, the MCP73213 charger board, the gate board "
               "and the seat switch, to the six paddle pins. No microcontroller, no Wi-Fi.")
    sh.block("AD", 14, 34, 62, 66, "wall adapter", band=BAND_PWR, tsize=8.2, sub=["GSM36U09-P1J", "9 V 4 A, 1.5 m cord", "plug into J1 (mated)"], subsize=6.4)
    sh.block("J1", 74, 34, 112, 76, "DC jack", band=BAND_PWR, tsize=8.2, sub=["PJ-005A 5 A", "tray rear wall"], subsize=6.2,
             pins=[("TIP", "R", 49.0, "TIP"), ("SLV", "R", 66.0, "SLV"), ("SHN", "D", 93.0, "SHN")])
    sh.block("FD", 134, 38, 172, 60, "5 A fuse", band=BAND_PWR, tsize=8.2, sub=["FHAC0001ZXJ"], subsize=6.2,
             pins=[("IN", "L", 49.0, "IN"), ("OUT", "R", 49.0, "OUT")])
    sh.block("SWG", 196, 36, 252, 92, "gate switch", band=BAND_PWR, tsize=8.2, sub=["Pololu 2815", "slide OFF"], subsize=6.2,
             pins=[("VIN", "L", 49.0, "VIN", 2, 4.0), ("GND", "L", 80.0, "GND"), ("VOUT", "R", 54.0, "VOUT", 3, 4.0), ("CTRL", "D", 230.0, "CTRL")])
    sh.block("CH", 276, 36, 334, 96, "charger", band=BAND_PWR, tsize=8.2, sub=["MCP73213EV", "1.0 A, 8.40 V"], subsize=6.2,
             pins=[("VDD", "L", 52.0, "VDD"), ("VSS", "L", 72.0, "VSS"), ("VBATP", "R", 60.0, "VBAT+", 2, 4.0), ("VBATN", "R", 82.0, "VBAT-"),
                   ("STAT", "D", 300.0, "STAT")])
    sh.block("PADDLE", 356, 36, 404, 150, "paddle pins", band=BAND_DUCK, tsize=8.2, sub=["6 x Mill-Max 0933", "to the chest strips"], subsize=6.2,
             pins=[("CHG", "L", 60.0, "CHG+"), ("SNS", "L", 80.0, "SENSE"), ("GND_L", "L", 104.0, "GND L", 2, 4.0), ("SYS_L", "L", 128.0, "SYS L", 2, 4.0),
                   ("GND_R", "D", 372.0, "GND R"), ("SYS_R", "D", 392.0, "SYS R")])
    sh.block("GATE", 140, 160, 330, 232, "gate board", band=BAND_IO, tsize=8.2,
             sub=["Perma-Proto half: 2 x LM393 (NTC window, pin-voltage window), TL431, NE555 one-shot, 2 x 2N3904",
                  "parts and nets: dock_netlist.yaml gate_board"], subsize=6.2, sub_y=200.0,
             pins=[("GND", "U", 156.0, "GND", 4, 4.0), ("V9", "U", 190.0, "+9V"), ("VSYS", "U", 218.0, "VSYS"), ("STAT", "U", 300.0, "STAT"),
                   ("CHGS", "U", 316.0, "CHGS"), ("SNS", "R", 172.0, "SENSE"), ("Q1C", "L", 196.0, "Q1 C")])
    sh.block("MS", 22, 168, 78, 214, "seat switch", band=BAND_IO, tsize=8.2, sub=["Omron D2F-01L"], subsize=6.2,
             pins=[("C", "R", 182.0, "COM"), ("NC", "R", 190.0, "NC"), ("NO", "R", 198.0, "NO")])
    # power in
    sh.w("J1.TIP", "FD.IN", lab=122)
    sh.w("FD.OUT", "SWG.VIN", 184.0, sb=0, lab=178)
    sh.w("SWG.VIN", "GATE.V9", 184.0, 112.0, 190.0, sa=1, lab=("y", 112.0))
    sh.w("J1.SLV", "GATE.GND", 124.0, 140.0, 150.0, sb=0, lab=("y", 140.0))
    sh.w("SWG.GND", "GATE.GND", 188.0, 132.0, 154.0, sb=1, lab=("y", 132.0))
    # gated 9 V and the charger
    sh.w("SWG.VOUT", "CH.VDD", 262.0, sa=0, lab=268)
    sh.w("SWG.VOUT", "GATE.VSYS", 258.0, 118.0, 218.0, sa=1, lab=("y", 118.0))
    sh.w("CH.VSS", "GATE.GND", 268.0, 126.0, 158.0, sb=2, lab=("y", 126.0))
    sh.w("CH.STAT", "GATE.STAT", lab=("y", 130.0))
    sh.w("CH.VBATP", "GATE.CHGS", 342.0, 136.0, 316.0, sa=1, lab=("y", 136.0))
    # seat switch
    sh.w("SWG.CTRL", "MS.C", 104.0, 100.0, 182.0, lab=("y", 104.0))
    sh.w("MS.NO", "GATE.Q1C", 110.0, 196.0, lab=120)
    # paddle cable KP1 and jumpers KP2
    sh.w("CH.VBATP", "PADDLE.CHG", 346.0, 60.0, sa=0, lab=350)
    sh.w("GATE.SNS", "PADDLE.SNS", 344.0, 80.0, lab=("y", 150.0))
    sh.w("GATE.GND", "PADDLE.GND_L", 144.0, 340.0, 104.0, sa=3, sb=0, lab=("y", 144.0))
    sh.w("SWG.VOUT", "PADDLE.SYS_L", 254.0, 152.0, 348.0, 128.0, sa=2, sb=0, lab=("y", 152.0))
    sh.w("PADDLE.GND_L", "PADDLE.GND_R", 350.0, 158.0, 372.0, sa=1, lab="none")
    sh.w("PADDLE.SYS_L", "PADDLE.SYS_R", 352.0, 156.0, 392.0, sa=1, lab="none")
    sh.legend()
    sh.notes_box(152, 249, 262, 287, [
        "Gate: on only with the seat switch closed (a seated duck), the NTC window 3.7 to 43.2 C on SENSE and the pin-voltage "
        "window 5.05 to 9.23 V (8.59 V with the charger on) on CHG+ (dock_erc.py, calc only). Then the 2815 feeds the charger and the SYS pins.",
        "STAT done edge: Q3 inverts it, the NE555 makes a 110 ms pulse onto SENSE through D2 and 1 k (wakes a shut-down duck). "
        "The duck side of the strips is netlist.yaml (DKP, DK2, F2, RT1, WK1, DK6, DK7).",
    ])
    return sh


def main():
    book = Book()
    book.n_sheets = 1
    book.complete = True
    sh = None
    for p in (1, 2):
        book.pass_no = p
        sh = sheet_dock(book)
        n_full = len({r["w"]["n"] for r in sh.routes if r["kind"] == "full"})
        sh.frame(); sh.heading(); sh.title_block(n_full, 0, len(book.net.active_wires)); sh.finish()
        if p == 1:
            book.terms[sh.no] = {k: (v["x"], v["y"]) for k, v in sh.T.items()}
            for r in sh.routes:
                if r["kind"] == "full":
                    book.full[r["w"]["n"]].append(sh.no)
            L.plt.close(sh.fig)
    drawn = {r["w"]["n"] for r in sh.routes if r["kind"] == "full"}
    missing = [w for w in book.net.active_wires if w["n"] not in drawn]
    if missing:
        raise SystemExit("dock wires not drawn: " + ", ".join("%s-%s" % (w["from"], w["to"]) for w in missing))
    svg, png = sh.save(os.environ.get("ODM_SHEETS_OUT", HERE))
    print("sheet 7: %s %d bytes, svg %d bytes, full %d of %d, crossings %d" % (os.path.basename(png), os.path.getsize(png), os.path.getsize(svg),
                                                                            len(drawn), len(book.net.active_wires), sh.n_cross))
    for w_ in sh.warn:
        print("  WARN", w_)


if __name__ == "__main__":
    main()
