"""Phase 2 of the V1 screws job (D36, D38): apply the screw cut and the parts to the shared files.
Run once from anywhere: python3 apply_phase2.py. Prints what it changed; asserts each old text is found."""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.dirname(LAB)
P = lambda *a: os.path.join(LAB, *a)
log = []


def sub(path, old, new, count=1, regex=False):
    s = open(path).read()
    if regex:
        s2, n = re.subn(old, new, s, count=count)
    else:
        n = s.count(old)
        s2 = s.replace(old, new, count if count else -1)
    if n == 0:
        log.append("NOT FOUND in %s: %s" % (os.path.relpath(path, REPO), old[:80]))
        return False
    open(path, "w").write(s2)
    log.append("edit %s: %s" % (os.path.relpath(path, REPO), old[:60].replace("\n", " ")))
    return True


# ---- 1. D38: the back shell keeps 7 screws; rerun the twin --------------------------------------------
tw = os.path.join(HERE, "screws_twin.py")
sub(tw, '''                    if p == "body_back":
                        J["needs_ahmed_ok"]''', '''                    if p == "body_back":   # D38 (lead, 2026-11-04): the back shell keeps 7 of its 8 screws
                        one = min(r["id"] for r in fit if r["into"] == "body_middle_bottom")
                        kept = [r["id"] for r in fit if r["id"] != one]
                        nb = len(kept)
                        for lv in ("soft", "mid"):
                            F2[lv]["after_screws"] = round(nb * bearing / SHELL_HIT_N[lv], 2)
                            for dn in ("y", "z_up", "z_down"):
                                F2[lv]["after_with_lip_" + dn] = round((nb * bearing + lipcap.get(dn, 0)) / SHELL_HIT_N[lv], 2)
                        why = "D38: the back shell keeps 7 screws (%s out) with the lips and ribs on body_middle_bottom; " % one + why
                    if False:
                        J["needs_ahmed_ok"]''')
subprocess.run([sys.executable, tw], cwd=HERE, check=True, stdout=subprocess.DEVNULL)
cut = json.load(open(os.path.join(HERE, "data", "phase2_fasteners.json")))
summ = json.load(open(os.path.join(HERE, "data", "summary.json")))
log.append("cut: %d screws, %d inserts, %d washers; fitted %d -> %d" % (len(cut["screws_cut"]), len(cut["inserts_cut"]), cut["washers_cut"], summ["fitted_before"], summ["fitted_after"]))

# ---- 2. fasteners: the cut is applied by report_fasteners.py (so a regeneration keeps it) --------------
rf = P("fasteners", "report_fasteners.py")
sub(rf, '''    screws = [r for r in R if r["kind"] == "screw"]
    inserts = [r for r in R if r["kind"] == "insert"]''', '''    # ---- D38 (V1 screws job, twin/screws/SCREWS_TWIN.md): screws, their inserts and washers left out
    cutf = os.path.join(LAB, "twin", "screws", "data", "phase2_fasteners.json")
    if os.path.exists(cutf):
        C38 = json.load(open(cutf))
        for r in R:
            if r["id"] in C38["screws_cut"] or r["id"] in C38["inserts_cut"]:
                r["status"], r["leave_out"] = "LEAVE OUT (D38 screw cut)", True
                note = "D38: left out by the V1 screw cut (twin/screws/data/phase2_fasteners.json); hole kept"
                if note not in r.get("notes", []):
                    r["notes"] = r.get("notes", []) + [note]
    screws = [r for r in R if r["kind"] == "screw"]
    inserts = [r for r in R if r["kind"] == "insert" and not r.get("leave_out")]''')
for f in (rf, P("fasteners", "render_fasteners.py")):
    s = open(f).read()
    s = s.replace('r.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)")', 'not str(r.get("status") or "").startswith(("NOT FITTED", "LEAVE OUT"))')
    s = s.replace('r.get("status") in ("NOT FITTED", "LEAVE OUT (D18)")', 'str(r.get("status") or "").startswith(("NOT FITTED", "LEAVE OUT"))')
    s = s.replace('not (r.get("status") == "LEAVE OUT (D18)")', 'not str(r.get("status") or "").startswith("LEAVE OUT")')
    open(f, "w").write(s)

# ---- 3. BOM.md --------------------------------------------------------------------------------------------
bom = P("BOM.md")
need = {"16": ("58", "48"), "17a": ("28", "18"), "17f": ("17", "11"), "17g": ("8", "4"), "17i": ("4", "3"),
        "17k": ("4", "2"), "17l": ("16", "8"), "17h": ("30", "28"), "12": ("1", "2")}
L = open(bom).read().split("\n")
for i, l in enumerate(L):
    c = l.split(" | ")
    if len(c) > 4 and c[0].startswith("| ") and c[0][2:] in need:
        o, n = need[c[0][2:]]
        if c[3] == o:
            c[3] = n
            L[i] = " | ".join(c)
            log.append("BOM %s need %s -> %s" % (c[0][2:], o, n))
        else:
            log.append("BOM %s need is %s, expected %s: NOT changed" % (c[0][2:], c[3], o))
s = "\n".join(L)
s = s.replace("4 x M2x5 for the camera (pilots drilled to 4.5 mm, D34)", "2 x M2x5 for the camera (the diagonal pair, D38; pilots drilled to 4.5 mm, D34)")
s = s.replace("| 12 | XT30 pair | Amass XT30U, 10 pairs |", "| 12 | XT30 pair | Amass XT30U, 10 pairs; 15 A continuous, 30 A peak ([I] https://shop.pimoroni.com/products/amass-xt30-connector, search text); 2 pairs used: the battery disconnect and the P13 service plug at the neck base (X3a, D36: 2.21 A peak) |")
old10b = [l for l in s.split("\n") if l.startswith("| 10b | ")][0]
new10b = ("| 10b | Control button (D30, D38) | NKK MB2011LS1W01-BB momentary pushbutton, MB2000 series (same 1/4-40 threaded bushing with keyway and 13 mm body as the "
          "MB2011SS1W01 the D30 plate was drawn for: NKK MB2000 drawing, https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/923/MB2000Bushing.pdf, via search index), "
          "solder lug terminals (code 01), L plunger with its snap-on cap BB (the S plunger takes screw-on caps; NKK codes via search index); across the 2813 A and B pins "
          "(cable P15); held in the body_back cutout by the printed plate twin/assembly/button_plate_d30.stl, unchanged | 1 | 1 | 1 | 10.37 | Newark (941 in stock, search index) | "
          "https://www.electronicsdatasheets.com/parts/nkk-switches/MB2011LS1W01-BB | Yes | Yes: $10.37 at 1 (Newark via electronicsdatasheets.com, search index 2026-11-04); "
          "replaces MB2011SS1W01 (0 in stock, $8.16). Snap-on cap height not read: check it clears the body_back opening at the first fit |")
s = s.replace(old10b, new10b)
row22 = [l for l in s.split("\n") if l.startswith("| 22 | ")][0]
s = s.replace(row22, row22 + "\n| 22b | KK 254 crimp terminal (X1, D36) | Molex 08-50-0114, KK 254 2759 series, 22 to 30 AWG, 3 A ([I] https://www.datasheets.com/molex/08-50-0114, search text; 4 A on Octopart); the 27 Pi header ends (D2 to D10, P12, P17) crimped instead of soldered, so the Pi unplugs | 27 | 30 | each | 2.55 | Octopart (lowest listed) | https://octopart.com/part/molex/08-50-0114 | Yes | Yes: $0.085 each (Octopart, search index 2026-11-04) |\n| 22c | KK 254 crimp housings (X1, D36) | Molex KK 254 1-row housings (2695 series), one per Pi header cable, widths from the pin map in wiring/netlist.yaml (11 cables) | 11 | 11 | each | 0.00 | BLOCKER | BLOCKER: price not read (no listing found for 22-01-3027 in this session) | Yes | BLOCKER: price |")
row26 = [l for l in s.split("\n") if l.startswith("| 26 | ")][0]
s = s.replace(row26, row26 + "\n| 26b | Lever splices (X4, D36) | WAGO 221 pocket pack: 3 each of 221-412, 221-413 and 221-415 (24 to 12 AWG, 20 A, 600 V: [I] https://core-electronics.com.au/wago-snap-action-solderless-connection-5-conductor-221-415.html, search text); splice G uses one 221-415 (4 wires), VSW one 221-413 (3 wires), in the battery bay | 2 | 1 | 9 | 13.25 | eBay | https://www.ebay.com/p/2255633067 | Yes | Yes: $13.25 with free shipping (eBay, search index 2026-11-04); outline not read: the 3D job checks the battery bay space |")
rowT15 = [l for l in s.split("\n") if l.startswith("| T15 | ")][0]
s = s.replace(rowT15, rowT15 + "\n| T16 | Screwdriver PH 0 (D36) | Wera 2050 PH 0 x 60 mm, blade 3.0 mm, for the cross-head screws (twin/assembly/ASSEMBLY_TWIN.md item 2, B53) | 1 | 1 | 1 | 7.91 | Haus of Tools | https://hausoftools.com/products/wera-05118022001-2050-precision-phillips-electronics-screwdriver-ph-0-x-60-mm | Yes | Yes (D36) |\n| T17 | Screwdriver PH 1 (D36) | Wera 2050 PH 1 x 80 mm, blade 4.0 mm | 1 | 1 | 1 | 9.76 | Haus of Tools | https://www.hausoftools.com/products/wera-05118024001-2050-ph-screwdriver-for-phillips-screws-for-electronic-applications-ph-1-x-80-mm | Yes | Yes (D36) |\n| T18 | Bit PH 0 x 25 mm (D36) | Wera 851/1 Z PH 0 x 25 mm, 1/4 in hex, for the six screws with 35.6 to 58.5 mm free | 1 | 1 | 1 | 1.95 | Jensen Tools | https://www.jensentools.com/product/873SC5651-05056500001 | Yes | Yes (D36) |\n| T19 | Drill bit 1/16 in (D36) | Hyper Tough 3 piece 1/16 in HSS roll forged bits, AU00040K; the camera pilots (print/PRINT_PLAN.md After printing) | 1 | 1 | 3 | 1.98 | Walmart | https://www.walmart.com/ip/Hyper-Tough-3-Piece-1-16-inch-Hss-Roll-Forged-Drill-Bits-Hss-Material-AU00040K/516905753 | Yes | Yes: $1.98 for 3 (Walmart, search index 2026-11-04) |")
for b in ("- Wera 2050 PH 0 x 60 mm, blade 3.0 mm: $7.91, https://hausoftools.com/products/wera-05118022001-2050-precision-phillips-electronics-screwdriver-ph-0-x-60-mm\n",
          "- Wera 2050 PH 1 x 80 mm, blade 4.0 mm: $9.76, https://www.hausoftools.com/products/wera-05118024001-2050-ph-screwdriver-for-phillips-screws-for-electronic-applications-ph-1-x-80-mm\n",
          "- Wera 851/1 Z PH 0 x 25 mm bit, 1/4 in hex (six screws with 35.6 to 58.5 mm free): $1.95, https://www.jensentools.com/product/873SC5651-05056500001\n"):
    s = s.replace(b, "")
s = s.replace("The BOM has no screwdriver for the 95 cross-head screws (twin/assembly/ASSEMBLY_TWIN.md item 2, HARDWARE_AUDIT B53). Proposed, nothing bought:",
              "The three Wera tools are tool lines T16 to T18 since D36 (2026-11-04). Still only proposed, nothing bought:")
tot = {"Subtotal: $623.53": "Subtotal: $625.74", "Subtotal: $267.04": "Subtotal: $282.84", "Subtotal: $250.06": "Subtotal: $271.66",
       "| Robot | 623.53 |": "| Robot | 625.74 |", "| Cables, connectors, wire | 267.04 |": "| Cables, connectors, wire | 282.84 |",
       "| Tools (one-time) | 250.06 |": "| Tools (one-time) | 271.66 |",
       "| Build total (robot + fasteners + cables + filament) | 1018.29 |": "| Build total (robot + fasteners + cables + filament) | 1036.30 |",
       "| Build + expression pack | 1097.68 |": "| Build + expression pack | 1115.69 |",
       "| Build + expression + tools | 1347.74 |": "| Build + expression + tools | 1387.35 |"}
for o, n in tot.items():
    if o in s:
        s = s.replace(o, n); log.append("BOM total %s -> %s" % (o, n))
    else:
        log.append("BOM total NOT FOUND: " + o)
s = s.replace("\n## Totals", "\nChange 2026-11-04 about 8:50 PM ET (V1 screws job phase 2, D36 and D38, twin/screws/SCREWS_TWIN.md): Need from the screw cut: 16 58 to 48, 17a 28 to 18, 17f 17 to 11, 17g 8 to 4, 17i 4 to 3, 17k 4 to 2, 17h 30 to 28, 17l 16 to 8 (Buy and $ kept: the packs already bought cover the new need); new lines 22b and 22c (KK 254, X1), 26b (WAGO 221, X4), 12 Need 2 (XT30U in P13, X3a), T16 to T18 (the Wera tools, from 'Needs Ahmed's OK'), T19 (1/16 in drill); 10b NKK MB2011LS1W01-BB in place of the out-of-stock MB2011SS1W01 (+$2.21). Robot +$2.21, cables +$15.80, tools +$21.60.\n\n## Totals", 1)
open(bom, "w").write(s)
for f in ("STATE.md", "START_HERE.md", "README.md"):
    for o, n in (("$1,018.29", "$1,036.30"), ("$1,097.68", "$1,115.69"), ("$1,347.74", "$1,387.35")):
        if os.path.exists(P(f)) and o in open(P(f)).read():
            sub(P(f), o, n, count=0)

# ---- 4. MOUNTING.md ------------------------------------------------------------------------------------------
mt = P("MOUNTING.md")
sub(mt, "| M2.5x6 DIN 912 A2, 4 pcs | 4.6 |", "| M2.5x6 DIN 912 A2, 2 pcs (the diagonal pair, D38; the other 2 holes stay empty) | 4.6 |")
sub(mt, "| M2.5x10 DIN 912, 4 pcs |", "| M2.5x10 DIN 912, 3 pcs (D38: F027 out, hole kept) |")
sub(mt, "M2.5x8: eyes 8, each with two 0.3 mm M2.5 washers (BOM buys 10 screws, line 17g, and 48 washers, line 17l; D21 note). M2.5x10: lid 4 (BOM buys 5; drill the lid holes to 2.7 mm, D20).",
    "M2.5x8: eyes 4 since D38 (2 per eye, the diagonal pair), each with two 0.3 mm M2.5 washers (8 washers; BOM line 17g, line 17l; D21 note). M2.5x10: lid 3 since D38 (drill the lid holes to 2.7 mm, D20). D38 also: Pi, servo adapter, camera, speaker stand and speaker interface on their 2 diagonal screws; head_bot_sheet on 3 of 8; body_front on 4 of 8 with the tongue and groove; body_back on 7 of 8 with the lips (twin/screws/SCREWS_TWIN.md). Every unused hole stays, so a screw can go back.")
sub(mt, "8 x M3x8 body_back screws out", "7 x M3x8 body_back screws out (D38)")
sub(mt, "the 4 lid screws", "the 3 lid screws (D38)")

# ---- 5. sim/MASS_BUDGET.md: the cut as a delta row (the sim owner re-runs mass_budget.py) ---------------------
mb = P("sim", "MASS_BUDGET.md")
s = open(mb).read()
mass = {k: float(v) for k, v in re.findall(r"\b(M[0-9.]+x[0-9]+) ([0-9]+\.[0-9]+) g", s)}
spec_n = {"M3x8": 10, "M2.5x6": 6, "M2.5x8": 4, "M2.5x5": 2, "M2.5x10": 1, "M2x5": 2}
got = {k: mass.get(k) for k in spec_n}
known = sum(spec_n[k] * v for k, v in got.items() if v)
miss = [k for k, v in got.items() if not v]
d_ins = 10 * 0.35
lips = (736 + 4872) / 1000 * 1.20
row = ("| D38 screw cut (V1 screws job): -25 screws (%s), -10 inserts (0.35 g each, the INSERT_G source), -8 washers; +5.6 cm3 PLA in the tongue, lips and ribs | %+.1f | "
       "calc only: screws %.2f g from the screw_mass sizes%s; washers not counted (no washer mass in this budget: BLOCKER); lips at 1.20 g/cm3 (PRINT_CHECK.md Overture PLA); "
       "the body_front groove is not taken off (re-slice in phase 2). Not yet in 'Our build': the sim owner re-runs sim/mass_budget.py |") % (
    ", ".join("%d x %s" % (n, k) for k, n in spec_n.items()), -(known + d_ins) + lips, known,
    (" (no size for %s: BLOCKER)" % ", ".join(miss)) if miss else "")
anchor = [l for l in s.split("\n") if l.startswith("| D30: printed button plate")]
if anchor:
    s = s.replace(anchor[0], anchor[0] + "\n" + row)
    open(mb, "w").write(s)
    log.append("MASS_BUDGET row: " + row[:160])
else:
    log.append("MASS_BUDGET anchor NOT FOUND")

# ---- 6. netlist and harness generator: X1, X3a, X4 ---------------------------------------------------------
nl = P("wiring", "netlist.yaml")
s = open(nl).read()
for sp, way in (("G", "221-415 (4 wires)"), ("VSW", "221-413 (3 wires)")):
    m = re.search(r"\n  - id: %s\n(    .*\n)+?    groups:\n      s: \{connector: \"([^\"]*)\"" % sp, s)
    if m:
        s = s[:m.start(2)] + "WAGO %s lever splice (X4, D36)" % way + s[m.end(2):]
        log.append("netlist splice %s -> WAGO %s" % (sp, way))
    else:
        log.append("netlist splice %s NOT FOUND" % sp)
s = s.replace('  - {id: P13, status: active, desc: splices VSW and G up the neck to U3 VIN and GND on the head floor,',
              '  - {id: P13, status: active, inline: "XT30U pair (BOM 12) at the neck base on trunk_top, on a straight run 20 mm or more from the neck_pitch loop end; solder cups and heat shrink both halves; the head comes off by unplugging it (X3a, D36)", desc: splices VSW and G up the neck to U3 VIN and GND on the head floor,')
open(nl, "w").write(s)
hb = P("wiring", "make_harness_build.py")
sub(hb, '''    if "splice" in k:
        sp = pin.split(".")[0]''', '''    if "lever splice" in k:
        sp = pin.split(".")[0]
        return ("strip 11 mm and push it fully into the WAGO lever splice %s (lever up, insert, lever down), then tug-test "
                "(X4, D36; no solder, no heat shrink)" % sp)
    if "splice" in k:
        sp = pin.split(".")[0]''')
sub(hb, '''    if "header" in k:
        return "solder at the Pi header (pin %s)" % pin.split(".")[-1]''', '''    if "header" in k:
        return ("crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin %s "
                "until it clicks, then tug-test (X1, D36: the Pi unplugs)" % pin.split(".")[-1])''')
open(os.path.join(HERE, "data", "apply_phase2_log.txt"), "w").write("\n".join(log) + "\n")

# ---- 7. new print STLs ------------------------------------------------------------------------------------------
for src, dst in (("body_front_groove.stl", "body_front.stl"), ("body_middle_top_lip.stl", "body_middle_top.stl"),
                 ("body_middle_bottom_lip.stl", "body_middle_bottom.stl")):
    shutil.copyfile(os.path.join(HERE, "stl", src), os.path.join(REPO, "print", dst))
    log.append("print/%s <- twin/screws/stl/%s" % (dst, src))
print("\n".join(log))
