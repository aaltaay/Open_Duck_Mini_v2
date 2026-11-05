"""phase2_docs.py: V1 "everything in 3D" phase 2, the doc edits. Run after phase2_data.py and cables3d/check_cables.py.
Numbers come from cables3d.json, d12_ribbon.json and $C3D_OUT/phase2_data_out.json. Each edit is asserted and skips when
it is already in place. Plain words; no em or en dashes.
"""
import datetime
import json
import os
import re
from zoneinfo import ZoneInfo

from common import CABLES3D, HERE, LAB, OUT

LOG = []
NOW = datetime.datetime.now(ZoneInfo("America/New_York"))
STAMP = NOW.strftime("%Y-%m-%d about %I:%M %p ET").replace(" 0", " ")
BIT = ("1/16 in (1.59 mm) HSS drill bit, not in the tool lines: Hyper Tough 3-piece $1.98 at Walmart "
       "(https://www.walmart.com/ip/Hyper-Tough-3-Piece-1-16-inch-Hss-Roll-Forged-Drill-Bits-Hss-Material-AU00040K/516905753) or "
       "EazyPower $1.95 each at Zoro (https://www.zoro.com/eazypower-drill-bit-hss-116-in-79763/i/G7628266/), both read via search "
       "index 2026-11-04; needs Ahmed's OK")


def P(*a):
    return os.path.join(LAB, *a)


def edit(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    if new in t and old not in t:
        return False
    assert t.count(old) == count, "%s: %d x %r" % (path, t.count(old), old[:80])
    open(path, "w", encoding="utf-8").write(t.replace(old, new))
    LOG.append("%s: %s" % (os.path.relpath(path, LAB), old[:60].strip()))
    return True


def line_of(path, start):
    for ln in open(path, encoding="utf-8").read().split("\n"):
        if ln.startswith(start):
            return ln
    raise AssertionError("%s: no line starting %r" % (path, start))


def main():
    c3 = json.load(open(CABLES3D))
    C = {c["id"]: c for c in c3["cables"]}
    rib = json.load(open(os.path.join(HERE, "d12_ribbon.json")))
    o = json.load(open(os.path.join(OUT, "phase2_data_out.json")))
    L12, loop = rib["centerline_mm"], rib["slack_loop_300"] or {}
    R, spare = loop.get("radius_mm"), 300.0 - rib["centerline_mm"]
    d13 = C["D13"]
    w13 = d13["wires"][0]
    cut13, chk13 = w13["cut_mm"], d13.get("check")
    worst13 = w13.get("length_max_mm") or d13.get("worst_mm")
    runs = sum(len(c.get("runs") or [1]) for c in c3["cables"])
    ncab = len(c3["cables"])
    sp = {k: C[k].get("check") for k in ("SP1", "SP2", "SP4", "SP5")}
    # ------------------------------------------------------------------ BOM.md
    bom = P("BOM.md")
    t = open(bom).read()
    if "| TO9 | Raspberry Pi Camera Cable Standard-Mini 300 mm" not in t:
        e7 = line_of(bom, "| E7 |")
        cells = [c.strip() for c in e7.strip().strip("|").split("|")]
        new = list(cells)
        new[1] = "Camera cable (D34)"
        new[2] = ("Raspberry Pi Camera Cable Standard-Mini 300 mm, 22-pin 0.5 mm (Pi Zero) to 15-pin 1 mm (camera); flat strip route "
                  "%.1f mm, %.1f mm spare in one gentle loop of radius %g mm (twin/complete3d/COMPLETE3D.md section 9)" % (L12, spare, R))
        new[6], new[7], new[8] = "2.94", "X-On Electronics", "https://www.xonelec.com/mpn/raspberrypi/rpicameracablestandardmini300mm"
        new[-1] = ("Price US$2.94 via search index 2026-11-04, stock not verified; same part at Pakronics, RPI-SC1129, A$3.52 "
                   "(https://www.pakronics.com.au/products/raspberry-pi-camera-cable-standard-mini-300mm-rpi-sc1129); width and thickness "
                   "BLOCKER until the TO9 caliper check (B61)")
        old = list(cells)
        old[0], old[1] = "E7r", "Camera cable, replaced (D34)"
        old[2] = "Pi Zero camera cable 150 mm, Adafruit 3157: 77 mm short of the flat strip route (B61)"
        old[3], old[4], old[6] = "0", "0", "0.00"
        old[-1] = "replaced (D34), quantity 0"
        edit(bom, e7, "| " + " | ".join(new) + " |\n| " + " | ".join(old) + " |")
        edit(bom, "Used: 22 x M2x5 and 2 x M2x8 at servo case pilots, 2 x M2x4 at head_roll_mount and 4 x M2x4 for the camera (FASTENERS.md section 4)",
             "Used: 22 x M2x5 and 2 x M2x8 at servo case pilots, 4 x M2x5 for the camera (pilots drilled to 4.5 mm, D34) and 2 x M2x4 at "
             "head_roll_mount (FASTENERS.md section 4)")
        edit(bom, "| 30 (M2x5 22, M2x4 6, M2x8 2) |", "| 30 (M2x5 26, M2x4 2, M2x8 2) |")
        to9 = line_of(bom, "| TO9 |")
        edit(bom, to9, "| TO9 | Raspberry Pi Camera Cable Standard-Mini 300 mm, X-On Electronics (D34) | 1 | 2.94 | E7 | Flat strip route and "
                       "gentle loop fit, both ZIF ends seated, caliper width and thickness (TEST_PLAN 13, B61) |")
        to8 = line_of(bom, "| TO8 |")
        edit(bom, to8, to8.replace("Screw length on the 3.1 mm pilots (B9)",
                                   "PCB thickness (caliper) for the M2x5 in the pilots drilled to 4.5 mm (B9, B60)"))
        t = open(bom).read()
        m = re.search(r"Test order total: \$([0-9.]+)\.", t)
        edit(bom, m.group(0), "Test order total: $%.2f." % (float(m.group(1)) - 5.95 + 2.94))
        # scope and category totals: E7 moves from 5.95 to 2.94
        lines = t.split("\n")
        k7 = next(i for i, ln in enumerate(lines) if ln.startswith("| E7 |"))
        head = next(lines[i] for i in range(k7, -1, -1) if lines[i].startswith("#")).lower()
        expr = "xpression" in head
        for ln in lines:
            m = re.match(r"^\| ([^|]+?) \| ([0-9]+\.[0-9]{2}) \|\s*$", ln)
            if not m:
                continue
            name = m.group(1).lower()
            scope = name.startswith("build")
            hit = (scope and (("expression" in name) or not expr)) or (not scope and (name in head or head.strip("# ").startswith(name)))
            if hit:
                edit(bom, ln, "| %s | %.2f |" % (m.group(1), float(m.group(2)) - 3.01))
        LOG.append("BOM.md: E7 section heading %r, expression scope only: %s" % (head[:60], expr))
    # ------------------------------------------------------------------ HARDWARE_AUDIT.md
    ha = P("HARDWARE_AUDIT.md")
    if "| B60 |" not in open(ha).read():
        b59 = line_of(ha, "| B59 |")
        rows = [
            "| B60 | Camera screws: M2x4 engages 3.0 mm in the 3.2 mm pilots, under the 4.0 mm rule | DECIDED (D34 lead note), checked on TO8 | "
            "M2x5 from BOM 17h with the 4 pilots drilled to 4.5 mm (print/PRINT_PLAN.md After printing step 6): 4.0 mm engaged at a 1.0 mm PCB, "
            "0.5 mm to the bottom, 1.7 mm of material left (twin/complete3d/camera_seat.json, CAD check only). PCB thickness on TO8 (B9). "
            "Needs a %s. |" % BIT,
            "| B61 | Camera ribbon D12 as a flat strip needs %.1f mm; the 150 and 200 mm cables are short | DECIDED (D34), checked on TO9 | "
            "300 mm Raspberry Pi Standard-Mini cable (BOM E7, $2.94); %.1f mm spare in one gentle loop of radius %g mm, %.2f mm clear "
            "(twin/complete3d/d12_ribbon.json, CAD check only). FPC width, thickness and bend rule BLOCKER until the caliper check on TO9. |" % (
                L12, spare, R, loop.get("clr_exact_min_mm") or 0.0),
            "| B62 | OFF wire (Pi GPIO26 to the 2813 OFF input, D30) had no cable entry | OPEN (assembly and bench check, TEST_PLAN 13) | "
            "Cable D13 in the netlist, CABLE_MAP.md and cables3d.json on the P13 route: worst %.0f mm, cut %d mm, check %s (calc only). The 2813 "
            "OFF pad position is a BLOCKER (Pololu 2813 drawing not read in this session). |" % (worst13 or 0, cut13, chk13),
            "| B63 | roll_to_pitch mount text said 4 x M2x6 | CLEARED (CAD check: 2 holes per part) | The CAD has 2 pilots per roll_to_pitch "
            "(fasteners.json F029 to F032 into the servo bottom case, no empty hole there); the viewer mount text now says 2. |",
            "| B64 | 3D twin gaps: camera off its seat, D12 drawn as a tube, D10 fan-out and SP lead-ins missing, head_board ghost, "
            "no x-ray or labels | CLEARED (twin, CAD check) | Fixed in phase 2 of the V1 3D track (twin/complete3d/COMPLETE3D.md section 9); "
            "viewer files regenerated. |"]
        edit(ha, b59, b59 + "\n" + "\n".join(rows))
        old = "Totals after the V1 assembly twin (track 2, 2026-11-04 evening): 22 of 59 cleared or decided"
        edit(ha, old, "Totals after the V1 3D track (2026-11-04 night): 26 of 64 cleared or decided, 6 waiting on the parts check; B60 to B64 "
                      "new (B60 and B61 decided by D34; B63 and B64 cleared, CAD check; B62 open, an assembly and bench check).\n\n"
                      "Totals after the V1 assembly twin (track 2, 2026-11-04 evening): 22 of the then 59 rows cleared or decided")
    # ------------------------------------------------------------------ STATE.md, START_HERE.md
    st = P("STATE.md")
    s = open(st).read()
    if "V1 3D track phase 2" not in s:
        edit(st, "## Done (2026-11-01 evening into 2026-11-03)\n", "## Done (2026-11-01 evening into 2026-11-03)\n\n"
             "- %s, V1 3D track phase 2 (twin/complete3d/COMPLETE3D.md section 9, CAD check only): the camera is seated on its measured "
             "pilots with 4 x M2x5 in pilots drilled to 4.5 mm (D34); D12 is the 300 mm flat strip, route %.1f mm, %.1f mm spare in one "
             "gentle loop (D34); new cable D13, the OFF wire (D30), cut %d mm, check %s; the D10 fan-out is drawn; SP1, SP2, SP4 and SP5 "
             "reach their splice bodies; the head_board ghost is gone; the viewer has an x-ray switch and part and cable labels; "
             "HARDWARE_AUDIT B60 to B64.\n" % (STAMP, L12, spare, cut13, chk13))
        edit(st, "- 2026-11-04 V1 track 2: 22 of 59 cleared or decided; B53 to B59 new (HARDWARE_AUDIT.md).",
             "- 2026-11-04 V1 3D track: 26 of 64 cleared or decided; B60 to B64 new (HARDWARE_AUDIT.md).\n"
             "- 2026-11-04 V1 track 2: 22 of the then 59 rows cleared or decided; B53 to B59 new (HARDWARE_AUDIT.md).")
        s = open(st).read()
        m = re.search(r"- Blockers: 22 of 59 cleared or decided[^\n]*", s)
        edit(st, m.group(0), m.group(0).replace("22 of 59", "26 of 64").replace("19 assembly or bench checks", "20 assembly or bench checks"))
    sh = P("START_HERE.md")
    s = open(sh).read()
    if "B60 to B64" not in s:
        m = re.search(r"- Blockers: 22 of 59 cleared or decided \(V1 track 2: B53 to B59 new;", s)
        edit(sh, m.group(0), "- Blockers: 26 of 64 cleared or decided (V1 3D track: B60 to B64 new, twin/complete3d/COMPLETE3D.md; "
                             "V1 track 2: B53 to B59 new;")
    for f in (st, sh):
        s = open(f).read()
        s2 = re.sub(r"\b47 cables\b", "%d cables" % ncab, s)
        s2 = re.sub(r"\b62 runs\b", "%d runs" % runs, s2)
        if s2 != s:
            open(f, "w").write(s2)
            LOG.append("%s: cable and run counts" % os.path.basename(f))
    # ------------------------------------------------------------------ TEST_PLAN.md section 13
    tp = P("TEST_PLAN.md")
    s = open(tp).read()
    if "Camera ribbon loop fit (D34" not in s:
        a = s.index("## 13. Assembly checks")
        b = s.find("\n## ", a + 5)
        b = len(s) if b < 0 else b
        sec = s[a:b]
        nums = [int(x) for x in re.findall(r"(?m)^13\.(\d+)\b", sec)] + [int(x) for x in re.findall(r"(?m)^\| 13\.(\d+) ", sec)]
        n = max(nums) if nums else 0
        add = ("\n13.%d Camera ribbon loop fit (D34, B61): seat the 300 mm Standard-Mini cable in the Pi Zero 22-pin and the Camera Module 3 "
               "15-pin connectors, lay it on the strip route of twin/complete3d/d12_ribbon.json (bends 3 mm or more, folds flat and not "
               "creased) with the %.1f mm spare in one gentle loop of about %g mm radius, then close the head. Caliper the strip width and "
               "thickness at both ends and write them into COMPLETE3D.md. Pass: nothing taut or pinched, and the camera gives an image after "
               "20 head pitch, yaw and roll sweeps.\n"
               "13.%d OFF wire (D30, cable D13, B62): with dtoverlay=gpio-poweroff,gpiopin=26 in config.txt, run sudo poweroff on the Pi. "
               "Pass: after the Pi halts the 2813 switches the robot off (Pi and servo bus dark, pack current under 1 mA on the meter), "
               "and the button turns it on again. Check the D13 run on the P13 route at both neck joint limits first (TEST_PLAN 1.4).\n" % (
                   n + 1, spare, R, n + 2))
        open(tp, "w").write(s[:b].rstrip("\n") + "\n" + add + s[b:])
        LOG.append("TEST_PLAN.md: 13.%d and 13.%d" % (n + 1, n + 2))
    # ------------------------------------------------------------------ print/PRINT_PLAN.md After printing
    pp = P("print", "PRINT_PLAN.md")
    s = open(pp).read()
    if "Camera pilots (D34" not in s:
        h = "### After printing: drill steps (D20, B32, D24, D25)"
        a = s.index(h)
        b = s.find("\n## ", a + 5)
        sec = s[a:b]
        nums = [int(x) for x in re.findall(r"(?m)^(\d+)\. ", sec)]
        n = max(nums) + 1 if nums else 6
        last = list(re.finditer(r"(?m)^\d+\. [^\n]*(\n(?!\d+\. |#|\n)[^\n]*)*", sec))[-1] if nums else None
        step = ("%d. Camera pilots (D34, lead note; HARDWARE_AUDIT B60): drill the 4 camera pilots in head.stl from 3.2 to 4.5 mm deep with a "
                "1/16 in (1.59 mm) bit by hand (tape flag at 4.5 mm from the boss face). The pilot stays 1.65 mm across; 1.7 mm of material "
                "stays behind the bottom (twin/complete3d/camera_seat.json, CAD check only). The 4 M2x5 from BOM 17h then engage 4.0 mm at a "
                "1.0 mm PCB. The bit is not in the tool lines: needs Ahmed's OK." % n)
        if last:
            pos = a + last.end()
            s = s[:pos] + "\n" + step + s[pos:]
        else:
            s = s[:b] + "\n" + step + "\n" + s[b:]
        s = s.replace(h, "### After printing: drill steps (D20, B32, D24, D25, D34)")
        open(pp, "w").write(s)
        LOG.append("print/PRINT_PLAN.md: After printing step %d" % n)
    # ------------------------------------------------------------------ CABLE_MAP.md
    cm = P("CABLE_MAP.md")
    s = open(cm).read()
    if "| D13 |" not in s:
        d12 = line_of(cm, "| D12 |")
        edit(cm, d12, "| D12 | Pi CSI (22-pin 0.5 mm) | Camera Module 3 (15-pin 1 mm) | MIPI CSI | Raspberry Pi Standard-Mini camera cable "
                      "300 mm (D34) | FPC, flat strip | inside head | flat strip %.1f (no twist, CAD check) | 300 cable | [I] BOM E7 | %.1f mm "
                      "spare in one gentle loop of radius %g mm; fit on TO9 (TEST_PLAN 13); width and thickness BLOCKER (B61) |\n"
                      "| D13 | Pi GPIO26 (header pin 37) | 2813 OFF (D30) | 1 | 26 AWG blue [I] | header socket, 0.1 in hole | head, neck, "
                      "trunk_top, battery bay on the P13 route; crosses neck_pitch, head_pitch, head_yaw, head_roll | %.1f (3D, zero pose) | "
                      "%.1f / %d | logic signal | [L] D30 | OFF wire, dtoverlay=gpio-poweroff,gpiopin=26; 2813 OFF pad position BLOCKER (B62) |" % (
                          L12, spare, R, o["D13_zero_mm"], (worst13 or 0) + 40.0, cut13))
        p15 = line_of(cm, "| P15 |")
        cells = [c.strip() for c in p15.strip().strip("|").split("|")]
        cells[1], cells[2] = "2813 button pads (D30; the netlist still names the 2815 SW and GND_SW pads)", "momentary button (BOM 10b) in the body_back plate"
        edit(cm, p15, "| " + " | ".join(cells) + " |")
    # ------------------------------------------------------------------ fasteners/FASTENERS.md
    fm = P("fasteners", "FASTENERS.md")
    s = open(fm).read()
    if "M2x5 self-tapping pan head | camera PCB" not in s:
        row = line_of(fm, "| 4 | M2x4 self-tapping pan head | camera PCB (not in CAD) -> head |")
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        cells[1] = "M2x5 self-tapping pan head"
        cells[2] = "camera PCB (not in CAD) -> head"
        cells[3] = "plastic pilot 1.65 (camera), drilled to 4.5 mm (D34)"
        cells[4] = "1.0-5.5, 5.5"
        cells[5] = "4.0 / 4.0"
        cells[6] = "OK"
        edit(fm, row, "| " + " | ".join(cells) + " |")
        s = open(fm).read()
        m = re.search(r"OK (\d+), BELOW RULE (\d+), BOTTOMS 4", s)
        if m:
            edit(fm, m.group(0), "OK %d, BELOW RULE %s, BOTTOMS 0" % (int(m.group(1)) + 4, m.group(2)))
        m = re.search(r"17\. \*\*note \(B9 open\)\*\*: Camera:[^\n]*", s)
        if m:
            edit(fm, m.group(0), m.group(0) + " D34 (lead note): M2x5 from the same kit with the pilots drilled to 4.5 mm: 4.0 mm engaged, "
                                             "0.5 mm to the bottom (HARDWARE_AUDIT B60).")
    # ------------------------------------------------------------------ sim/MASS_BUDGET.md
    mb = P("sim", "MASS_BUDGET.md")
    s = open(mb).read()
    if "camera FPC cable 300 mm" not in s:
        row = line_of(mb, "| camera FPC cable 150 mm |")
        edit(mb, row, "| camera FPC cable 300 mm (D34) | wire | head | 1 | 1.34 | 1.34 | no | fpc | [L] twin/complete3d: 300 x 16 x 0.2 mm at "
                      "the fpc density of this file (1.4 g/cm3), was 0.70 g for 150 mm |")
        m = re.search(r"\n## Every item\n", s)
        note = ("\nV1 3D track, %s (calc only): the D34 camera cable adds 0.64 g (row above) and the new OFF wire D13 (26 AWG, cut %d mm, "
                "rides the P13 route) adds about the 26 AWG grams per metre of this file times %.2f m; together under 0.1 %% of the robot. "
                "The tables keep the V1 track 2 totals until the next mass run.\n" % (STAMP, cut13, cut13 / 1000.0))
        s = open(mb).read()
        open(mb, "w").write(s.replace("\n## Every item\n", note + "\n## Every item\n", 1))
        LOG.append("sim/MASS_BUDGET.md: camera cable row and note")
    print("\n".join(LOG))
    print(json.dumps(dict(L12=L12, spare=spare, R=R, cut13=cut13, chk13=chk13, worst13=worst13, ncab=ncab, runs=runs, sp=sp,
                          d12=C["D12"].get("check"))))


if __name__ == "__main__":
    main()
