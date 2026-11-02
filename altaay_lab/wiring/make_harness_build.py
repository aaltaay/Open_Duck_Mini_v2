"""Write altaay_lab/HARNESS_BUILD.md: the cable-by-cable build sheet for the harness.

Everything comes from wiring/netlist.yaml (wires, gauges, colours, cut lengths, end treatments), the continuity
checklist (audit/continuity_checklist.csv) and, when it exists, altaay_lab/cables3d/cables3d.json (how each cable
seats on the printed brackets and which ties hold it). Re-run after any netlist or cables3d change:
    python3 altaay_lab/wiring/make_harness_build.py
"""
import csv
import json
import os
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
    ("2. Belly servo power (D15)", ["P11", "SP1", "SP2", "SP3"]),
    ("3. Servo data leads and kit cables", ["SD1", "SD2", "S2", "S3", "S4", "S5", "S7", "S8", "S9", "S10", "S11", "S12", "S13"]),
    ("4. Power up the neck to the head", ["P13", "P12", "P17"]),
    ("5. Pi, IMU and feet", ["D1", "D2", "D3", "D4"]),
    ("6. Head expression", ["D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"]),
]


def end_step(e, pin, splices):
    k = (e or "").lower()
    if "50-37-5033" in k:
        empty = " (V position left empty)" if "empty" in k else ""
        return ("crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing "
                "until it clicks%s. Copy the position order of a servo kit cable housing exactly, then tug-test" % empty)
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
    if "pad" in k or "terminal" in k or "lug" in k or "tab" in k or "cup" in k:
        return "tin and solder to %s, heat shrink if bare" % pin
    if "screw terminal" in k:
        return "screw terminal %s" % pin
    if "holder lead" in k or "bec lead" in k or "sg90 lead" in k or "led lead" in k or "resistor lead" in k:
        return "use the part's own lead (%s), solder joint covered with heat shrink" % e
    if "usb" in k or "fpc" in k:
        return "bought cable end (%s), plug in" % e
    if "servo" in k:
        return "servo socket"
    return e or "?"


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
                        "%s %s%s" % (s.get("kind", "?"), s.get("part", ""), (" (" + str(s.get("note")) + ")") if s.get("note") else "") for s in seats))
                ts = ties_by_cable.get(cid, [])
                if ts:
                    L.append("Ties: " + "; ".join("%s on %s%s" % (t.get("kind", "tie"), t.get("part", "?"), " (GAP: no CAD feature)" if t.get("gap") else "") for t in ts))
                chk = c3r.get("check") or c3r.get("result")
                if chk:
                    L.append("Reach check: %s, worst routed %s mm, cut %s mm." % (chk, c3r.get("length_max_mm") or c3r.get("worst_mm"), c3r.get("cut_mm")))
                L.append("")
    sp_rows = ["| Splice | Where | Cables that meet there |", "|---|---|---|"]
    for sp, cabs in sorted(splices.items()):
        sp_rows.append("| %s | %s | %s |" % (sp, comps[sp].get("region", ""), ", ".join(sorted(set(cabs)))))
    L += ["## Splices", "", "Every splice is soldered and covered with adhesive heat shrink. Make each one after all its cables are cut and labelled.", ""] + sp_rows + [""]
    L += ["Coverage: %d active cables, %d wires, all from the netlist." % (len(cables), n_wires), ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("wrote", OUT, len(cables), "cables", n_wires, "wires", "(missing from groups: %s)" % missing if missing else "")


if __name__ == "__main__":
    main()
