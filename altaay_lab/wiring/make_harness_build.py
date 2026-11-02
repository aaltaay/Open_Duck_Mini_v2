"""Write altaay_lab/HARNESS_BUILD.md: the cable-by-cable build sheet for the harness.

Everything comes from wiring/netlist.yaml (wires, gauges, colours, cut lengths, end treatments), the continuity
checklist (audit/continuity_checklist.csv) and, when it exists, altaay_lab/cables3d/cables3d.json (how each cable
seats on the printed brackets and which ties hold it). Re-run after any netlist or cables3d change:
    python3 altaay_lab/wiring/make_harness_build.py
"""
import csv
import json
import os
import re
import time
from collections import OrderedDict, defaultdict

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
NET = os.path.join(HERE, "netlist.yaml")
CHECK = os.path.join(LAB, "audit", "continuity_checklist.csv")
C3D = os.path.join(LAB, "cables3d", "cables3d.json")
OUT = os.path.join(LAB, "HARNESS_BUILD.md")

GROUPS = [
    ("1. Battery bay power", ["P1", "P2", "P3", "P4", "P5", "P6", "P8", "P7", "P14", "P9", "P16", "P15", "P10"]),
    ("2. Belly servo power (D15, D23)", ["P11", "SP1", "SP2", "SP3", "SP4", "SP5"]),
    ("3. Servo data leads and kit cables", ["SD1", "SD2", "S2", "S3", "S4", "S5", "S7", "S8", "S9", "S10", "S11", "S12", "S13"]),
    ("4. Power up the neck to the head", ["P13", "P12", "P17"]),
    ("5. Pi, IMU and feet", ["D1", "D2", "D3", "D4"]),
    ("6. Head expression", ["D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"]),
]


def end_step(e, pin, splices):
    k = (e or "").lower()
    if "50-37-5033" in k:
        m = re.search(r"\((\w+) position empty\)", e or "", re.I)      # V empty at the adapter (D15), DATA at the ankles (D23)
        empty = " (%s position left empty)" % m.group(1).upper() if m else ""
        return ("crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing "
                "until it clicks%s. Copy the position order of a servo kit cable housing exactly, check it with a meter, "
                "then tug-test" % empty)
    if "5264 plug" in k:
        return "kit cable plug (ships with the servo), no work"
    if "splice" in k:
        sp = pin.split(".")[0]
        others = ", ".join(sorted(set(splices.get(sp, [])) - {pin})) if sp in splices else ""
        return "join at splice %s%s, solder, cover with adhesive heat shrink (BOM 26)" % (sp, (" with " + others) if others else "")
    if "xt30" in k:
        return "solder into the XT30U cup, heat shrink over the cup"
    if "header" in k:
        return "solder at the Pi header (pin %s)" % pin.split(".")[-1]
    if "0.1 in hole" in k or "large hole" in k:
        return "solder into the board hole %s" % pin.split(".")[-1]
    # before the generic rule below: "screw terminal" contains "terminal", and "plug" contains "lug"
    if "screw terminal" in k:
        return "screw terminal %s" % pin
    if "usb" in k or "fpc" in k:
        return "bought cable end (%s), plug in" % e
    if "pad" in k or "terminal" in k or "lug" in k or "tab" in k or "cup" in k:
        return "tin and solder to %s, heat shrink if bare" % pin
    if "holder lead" in k or "bec lead" in k or "sg90 lead" in k or "led lead" in k or "resistor lead" in k:
        return "use the part's own lead (%s), solder joint covered with heat shrink" % e
    if "servo" in k:
        return "servo socket"
    return e or "?"


def tie_text(t):
    """one retention item as a build step"""
    k = t.get("kind", "tie")
    mf = t.get("mount_fit") or {}
    case = " on the servo case (pull check at the dry fit)" if mf.get("on_servo_case") else ""
    if k == "existing printed feature":
        what = "through the hole in %s" % t.get("part")
    elif k == "adhesive tie mount" and mf.get("type") == "MB3A":
        what = "stick-on mount MB3A (BOM 34) on %s%s, %.0f mm from the cable line" % (t.get("part"), case, mf.get("from_cable_mm", 0))
    elif k == "adhesive tie mount" and mf.get("type") == "ABM1M":
        what = "stick-on mount ABM1M-AT-C (BOM 34b) on %s%s, %.0f mm from the cable line" % (
            t.get("part"), case, mf.get("from_cable_mm", 0))
    elif k == "drilled printed feature":
        h = t.get("tie_holes") or {}
        what = "through the drilled tie-hole pair in %s (%s mm holes %s mm apart, print/PRINT_PLAN.md After printing), %.0f mm from the cable line" % (
            t.get("part"), h.get("hole_d_mm"), h.get("spacing_mm"), h.get("from_cable_mm") or 0)
    elif k == "cable tie to a neighbour cable":
        what = "tied to cable %s, which %s holds" % (t.get("tied_to"), t.get("anchor_tie"))
    elif t.get("hold") == "bundle tie, test fit":
        what = "around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4)"
    else:
        what = "around the bundle only"
    return "%s %s%s" % (t.get("id", "?"), what, (" (OPEN, plan: %s)" % t.get("plan", "none yet")) if t.get("open") else "")


def loop_text(x):
    """one service loop as a build step: the cable to leave between its two ties"""
    ids = x.get("tie_ids") or [None, None]
    ends = [ids[0] or "the plug", ids[1] or "the plug"]
    return "%s: leave %s mm between %s and %s (%s mm more than the straight run at the zero pose)%s%s" % (
        "+".join(x.get("joints") or []), ("%.0f" % x["loop_length_mm"]) if x.get("loop_length_mm") is not None else "?",
        ends[0], ends[1], ("%.0f" % x["dress_extra_mm"]) if x.get("dress_extra_mm") is not None else "?",
        ", one loop over both joints: no tie between them" if len(x.get("spans") or []) > 1 else "",
        "" if x.get("ok") else " (under 3 x OD over the full joint range: turn the joint by hand at the TEST_PLAN 1.4 fit)")


def twist_text(cab):
    """the twist step of a made multi-wire cable (netlist 'twist', D25)"""
    tw = cab.get("twist")
    if not isinstance(tw, dict):
        return None
    if not tw.get("lay_mm"):
        return "Twist: none (%s)." % re.sub(r"^no twist: ", "", str(tw.get("note", "no reason given")))
    return ("Twist: %s twisted together, one full turn every %s mm (allowed %s to %s mm, 8 to 16 x the bundle OD, "
            "NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, %s mm untwisted at each end for the "
            "joint. Twist before the ends are made; the cut lengths already carry the take-up (up to %.1f %%)." % (
                "the wires of %s" % tw["wires"].replace(" only", "") if str(tw.get("wires", "")).startswith("branch") else "all wires",
                tw["lay_mm"], tw["lay_range_mm"][0], tw["lay_range_mm"][1], tw.get("untwisted_ends_mm", 20),
                (float(tw.get("takeup_max", 1.0)) - 1.0) * 100.0))


def main():
    n = yaml.safe_load(open(NET, encoding="utf-8"))
    comps = {c["id"]: c for c in n["components"]}
    pin_label = {}
    for c in n["components"]:
        for p in c.get("pins", []):
            pin_label["%s.%s" % (c["id"], p["pin"])] = "%s %s" % (c.get("ref") or c["id"], p.get("name") or p.get("label") or p["pin"])
    cables = OrderedDict((c["id"], c) for c in n["cables"] if c.get("status") == "active")
    wires = defaultdict(list)
    splices = defaultdict(list)
    for w in n["wires"]:
        wires[w["cable"]].append(w)
        for side in ("from", "to"):
            sp = w[side].split(".")[0]
            if comps.get(sp, {}).get("kind") == "splice":
                splices[sp].append(w["cable"])
    checks = defaultdict(list)
    if os.path.exists(CHECK):
        for r in csv.DictReader(open(CHECK, encoding="utf-8")):
            checks[r["cable"]].append(r)
    c3 = {}
    retention = []
    if os.path.exists(C3D):
        raw = json.load(open(C3D))
        for c in (raw.get("cables", raw) if isinstance(raw, dict) else raw):
            c3[c["id"]] = c
        retention = raw.get("retention") or [] if isinstance(raw, dict) else []
    ties_by_cable = defaultdict(list)
    for r in retention:
        for cid in r.get("cables") or []:
            ties_by_cable[cid].append(r)

    listed = [cid for _, ids in GROUPS for cid in ids]
    missing = [cid for cid in cables if cid not in listed]
    groups = GROUPS + ([("7. Other", missing)] if missing else [])
    L = ["# Harness build sheet", "",
         "Generated %s by altaay_lab/wiring/make_harness_build.py from wiring/netlist.yaml%s. Do not edit by hand." % (
             time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), " and cables3d/cables3d.json" if c3 else ""), "",
         "How to use it:",
         "- Build in the order below, one cable at a time. Cut every wire to the length shown; lengths include the end allowance used in the netlist.",
         "- Label both ends of every cable with its ID before installing (a marker on a short piece of heat shrink works).",
         "- Test each finished cable with its continuity lines (beep and no-short checks) before it goes into the robot (TEST_PLAN.md section 2).",
         "- Never plug or unplug anything with power on (upstream issue 49).",
         "- Tools and stock: crimper BOM T3, stripper T5, iron T1, heat shrink 26, wire L5 (16 AWG), 23 (20 AWG), 24 (22 AWG), 25 (26 AWG), "
         "Mini-SPOX housings 21 and terminals 22, XT30U 12, solder and cable ties (BOM_FULL.md K01, K02).",
         "- Seats and ties: where a cable passes or is tied to a printed part. %s" % (
             "From altaay_lab/cables3d (3D routing, sim pass only)." if c3 else "Pending: the 3D routing (altaay_lab/cables3d) fills these in."), ""]
    n_wires = 0
    for title, ids in groups:
        L += ["## %s" % title, ""]
        for cid in ids:
            cab = cables.get(cid)
            if not cab:
                continue
            ws = wires.get(cid, [])
            n_wires += len(ws)
            joints = ", ".join(cab.get("joints") or []) or "none"
            L += ["### %s: %s" % (cid, cab["desc"]), "",
                  "Regions: %s. Crosses joints: %s. %s" % (", ".join(cab.get("regions") or []) or "?", joints, cab.get("note") or ""), ""]
            tx = twist_text(cab)
            if tx:
                L += [tx, ""]
            L += ["| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |", "|---|---|---|---|---|---|---|---|"]
            for i, w in enumerate(ws, 1):
                ends = (w.get("ends") or ["", ""]) + ["", ""]
                L.append("| %d | %s (%s) | %s (%s) | %s | %s | %s | %s | %s |" % (
                    i, w["from"], pin_label.get(w["from"], ""), w["to"], pin_label.get(w["to"], ""), w["gauge"], w.get("color", ""),
                    w.get("cut_mm") if w.get("cut_mm") is not None else "-", end_step(ends[0], w["from"], splices),
                    end_step(ends[1], w["to"], splices)))
            L.append("")
            ch = checks.get(cid, [])
            if ch:
                L.append("Test: " + "; ".join("%s to %s: %s%s" % (r["from"], r["to"], r["expect"],
                                                                  (", no short to " + r["check_no_short_to"]) if r.get("check_no_short_to") else "") for r in ch))
                L.append("")
            c3r = c3.get(cid)
            if c3r:
                seats = c3r.get("seats") or []
                if seats:
                    L.append("Seats on the brackets, end to end: " + "; ".join(
                        ("%s %s" % (s.get("kind", "?"), s.get("part")) if s.get("part") else "%s (free air)" % s.get("kind", "?"))
                        + ((" (" + str(s.get("note")) + ")") if s.get("note") else "") for s in seats))
                ts = ties_by_cable.get(cid, [])
                if ts:
                    L.append("Ties (one 2.5 x 100 mm cable tie each, BOM 32): " + "; ".join(tie_text(t) for t in ts))
                loops = [(r.get("name"), x) for r in c3r.get("runs", []) for x in r.get("service_loops", [])]
                if loops:
                    L.append("Joint loops: " + "; ".join(loop_text(x) for _, x in loops))
                chk = c3r.get("check") or c3r.get("result")
                if chk:
                    L.append("Reach check (cables3d, by conductor chain): %s, worst routed %s mm, cut %s mm." % (
                        chk, c3r.get("length_max_mm") or c3r.get("worst_mm"), c3r.get("cut_mm")))
                L.append("")
    sp_rows = ["| Splice | Where | Cables that meet there |", "|---|---|---|"]
    for sp, cabs in sorted(splices.items()):
        sp_rows.append("| %s | %s | %s |" % (sp, comps[sp].get("region", ""), ", ".join(sorted(set(cabs)))))
    L += ["## Splices", "",
          "Every splice is soldered and covered with adhesive heat shrink. Make each one after all its cables are cut and labelled.",
          "",
          "- Lap splice: strip and tin each end, lay the conductors side by side over 3 to 6 wire diameters (NASA-STD-8739.4A "
          "19.4.1 c), solder, then slide on a 15 mm piece of the 3:1 adhesive heat shrink (cut from a 3.5 in BOM 26 kit piece, "
          "the smallest size that passes over the wires) so it covers the joint and reaches at least 2 x the wire OD onto the "
          "insulation at both ends (19.2.6), and shrink it (BOM T10).",
          "- Keep each splice on a straight run, out of bends and away from joints (7.2.36). The JG20, JG10 and JG30 tails are 30 "
          "mm so the sleeve sits past the bend at the servo plug. YD3 and YG3 are staggered: YG3 sits 15 mm past YD3 (7.2.35).",
          "- A splice that no part holds floats: it sits where the wire lengths put it. Lengths are checked fixed end to fixed "
          "end through it (CABLE_MAP.md length rule).", ""] + sp_rows + [""]
    holes = [t for t in retention if t.get("kind") == "drilled printed feature"]
    if holes:
        L += ["## Drilled tie holes (D25 ii)", "",
              "Drilled after printing, before the harness goes in (print/PRINT_PLAN.md After printing): two 4.0 mm holes with the "
              "BOM T14 bit, square to the face, one each side of the bundle; deburr both sides. The tie goes in through one hole, "
              "behind the wall and out of the other, then round the bundle. Each pair was checked in the CAD (exact rays, zero "
              "pose): at least 1.6 mm of plastic round each hole and between them, wall 1.6 to 12 mm, every screw, insert and "
              "empty hole at least 1.6 mm off, 1.5 mm free behind the wall, and the strap at least 1 mm from moving parts over "
              "the joint sweep.", "",
              "| Tie | Cables | Part | Holes apart mm | Wall mm | From the cable line mm | Hole centres in the part STL frame mm |",
              "|---|---|---|---|---|---|---|"]
        for t in holes:
            h = t.get("tie_holes") or {}
            L.append("| %s | %s | %s%s | %s | %s | %s | %s |" % (
                t["id"], ", ".join(t.get("cables") or []), h.get("part"), " (mirrored copy)" if h.get("mirrored") else "",
                h.get("spacing_mm"), " and ".join(str(x) for x in h.get("wall_mm") or []), h.get("from_cable_mm"),
                "; ".join(str(x) for x in h.get("holes_stl") or [])))
        L.append("")
    case = [t for t in retention if (t.get("mount_fit") or {}).get("on_servo_case")]
    if case:
        L += ["## Stick-on mounts on a servo case (D25 iv)", "",
              "Where no printed face, hole pair or neighbour cable can hold a loop end, the mount goes on a flat face of the "
              "STS3215 case of that link, clear of the servo plugs and of moving parts: %s. Wipe with alcohol (BOM 35) and press "
              "it on, then pull on it by hand at the dry fit (TEST_PLAN.md 1.4). If it lifts, report it; the tie then goes round "
              "the bundle only." % "; ".join("%s (%s, %s)" % (t["id"], ", ".join(t["cables"]), t["part"]) for t in case), ""]
    tf = [t for t in retention if t.get("hold") == "bundle tie, test fit"]
    if tf:
        L += ["## Bundle ties checked at the test fit (D25)", "",
              "No printed feature, stick-on mount, tie-hole pair or anchored neighbour cable fits at these points, and D25 "
              "adds no printed parts and no STL change. Put a line 32 tie round the bundle only, then at the TEST_PLAN.md 1.4 "
              "test fit turn every joint the cable crosses to both limits and check the bundle stays clear of moving parts. "
              "Only if it reaches a moving part: a drilled tie-hole pair or a printed anchor there (report it first).", ""] + [
            "- %s (%s on %s)%s" % (t["id"], ", ".join(t["cables"]), t["link"],
                                   (": route change tried" + t["plan"].split("; route change tried", 1)[1]) if "; route change tried" in (t.get("plan") or "") else "")
            for t in tf] + [""]
    op = [t for t in retention if t.get("open")]
    if op:
        L += ["## Open tie points", "", "Nothing in the CAD holds these yet; each has a named plan:", ""] + [
            "- %s (%s on %s): %s" % (t["id"], ", ".join(t["cables"]), t["link"], t.get("plan", "none yet")) for t in op] + [""]
    L += ["Coverage: %d active cables, %d wires, all from the netlist." % (len(cables), n_wires), ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("wrote", OUT, len(cables), "cables", n_wires, "wires", "(missing from groups: %s)" % missing if missing else "")


if __name__ == "__main__":
    main()
