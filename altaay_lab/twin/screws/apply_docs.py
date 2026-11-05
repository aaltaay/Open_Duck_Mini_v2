"""Phase 2 doc edits of the V1 screws job (D36, D38). Prints every edit and every miss."""
import json, os, re, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
P = lambda *a: os.path.join(LAB, *a)
log = []
S = json.load(open(os.path.join(HERE, "data", "summary.json")))
CC = json.load(open(os.path.join(HERE, "data", "cable_changes.json")))
fh = S["fastening_hours"]["after"][1]
ch_b, ch_a = CC["hours"]["before"][1], CC["hours"]["after_X1_X2_X3a_X4"][1]
et = subprocess.run(["date", "+%Y-%m-%d %H%M %-I:%M %p"], env=dict(os.environ, TZ="America/New_York"), capture_output=True, text=True).stdout.split()
day, hhmm, clock = et[0], et[1], " ".join(et[2:4])


def edit(f, old, new, regex=False, count=1):
    s = open(P(f)).read()
    s2, n = (re.subn(old, new, s, count=count) if regex else (s.replace(old, new, count if count else -1), s.count(old)))
    log.append(("%s: %s" % (f, old[:70])) if n else ("MISS %s: %s" % (f, old[:70])))
    if n:
        open(P(f), "w").write(s2)


# ---- HARDWARE_AUDIT -------------------------------------------------------------------------------------------
rows = [
    "| B65 | Screw count (Ahmed: about 90 % fewer, 2026-11-04 6:36 PM ET) | DECIDED (D38) | 342 to 317 fitted screws, 58 to 48 inserts, 16 to 8 washers (twin/screws/SCREWS_TWIN.md, calc only): covers and boards keep 2 diagonal screws (Pi, servo adapter, camera, speaker stand and interface, eyes), plates 3 (lid, head_bot_sheet), body_front 4 with the tongue and groove, body_back 7 (D38). The servo chain, frame and leg stack keep every screw: 34 of their 39 groups are under the lab margin today (STRUCTURE_TWIN.md table 5). Every unused hole stays. |",
    "| B66 | Shell shear features for the cut shell screws | DECIDED (D38), TEST PRINT, coupons K1 and K2 | print/body_front.stl (3.5 mm groove), print/body_middle_top.stl (3.0 mm tongue), print/body_middle_bottom.stl (back side lips and 6 ribs): CAD fit 0.25 to 0.41 mm, walls 2.5 mm or more, +812 mm2 supported overhang on body_middle_bottom; capacity front side 1732 N, vertical 3564 N, back side 2925 N, up 2261 N (calc only). Re-slice the 3 parts. |",
    "| B67 | Printed cable clip and tie bridge (fast cable work) | DECIDED (D36), TEST PRINT, coupons K3 and K4 | K3 snap strain 0.375 % against 0.535 % allowed (calc only); K4 slot 3.0 x 1.6 mm for the 2.5 mm tie. The 55 stick-on mounts become tie bridges only after the coupons pass and the 3D job places them (X2). |",
    "| B68 | Control button 10b (NKK MB2011SS1W01) out of stock | DECIDED (D38) | NKK MB2011LS1W01-BB, same MB2000 bushing and 13 mm body as the D30 plate inputs, solder lugs, snap-on cap BB; Newark 941 in stock, $10.37 (search index). Plate unchanged (CAD check: same bushing and body). The cap height is not published in what was read: check it clears the body_back opening at the first fit (TEST_PLAN 14.7). |",
    "| B69 | Pi header plugs, P13 service plug, battery bay lever splices | DECIDED (D36) | X1: KK 254 terminals (BOM 22b, $0.085 each) in 1-row housings (22c, price BLOCKER) on the 27 Pi header ends; X3a: XT30U pair in P13 at the neck base (15 A continuous against 2.21 A peak); X4: WAGO 221-415 at G and 221-413 at VSW (20 A). No route or cut length moves. Tug test after the walk (TEST_PLAN 14.4). |",
]
s = open(P("HARDWARE_AUDIT.md")).read()
b64 = [l for l in s.split("\n") if l.startswith("| B64 |")][0]
if "| B65 |" not in s:
    s = s.replace(b64, b64 + "\n" + "\n".join(rows))
s = s.replace("342 to fit. 221 to buy", "317 to fit (D38 screw cut). 196 to buy")
s = s.replace("13 left out on purpose: 2 hip roll screws (D18) and 11 idle horn screws that stay in the bags",
              "38 left out on purpose: 2 hip roll screws (D18), 11 idle horn screws that stay in the bags and 25 by the D38 screw cut")
s = s.replace("machine screws to buy 28 + 12 + 2 + 78 + 10 + 28 + 17 + 8 + 4 + 4 = 191", "machine screws to buy 18 + 12 + 2 + 78 + 10 + 28 + 11 + 4 + 3 + 2 = 168")
s = s.replace("plus 30 kit self-tapping", "plus 28 kit self-tapping")
s = s.replace("(221 screws by size, 58 inserts); 342 screws are fitted in all", "(196 screws by size, 48 inserts); 317 screws are fitted in all")
open(P("HARDWARE_AUDIT.md"), "w").write(s)
# counts as verify/c9_docs.py counts them
blk = {}
for l in s.split("\n"):
    m = re.match(r"^\| (B\d+) \| [^|]*\| ([^|]*)\|", l)
    if m:
        blk[m.group(1)] = m.group(2).strip()
n = len(blk)
tprint = [b for b, st in blk.items() if "TEST PRINT" in st]
cleared = [b for b, st in blk.items() if st.startswith(("CLEARED", "DECIDED")) and b not in tprint]
opened = [b for b, st in blk.items() if st.startswith("OPEN")]
waiting = [b for b in opened if not re.search(r"assembly|bench", blk[b])]
log.append("blockers: %d rows, cleared %d, test print %d, open %d (waiting %d)" % (n, len(cleared), len(tprint), len(opened), len(waiting)))
tot = ("Totals after the V1 screws job (phase 2, %s about %s ET, D36 and D38): %d of %d cleared or decided, %d settled by the coupon test prints, %d waiting on the parts check; B65 to B69 new (twin/screws/SCREWS_TWIN.md)."
       % (day, clock, len(cleared), n, len(tprint), len(waiting)))
s = open(P("HARDWARE_AUDIT.md")).read()
first = [l for l in s.split("\n") if l.startswith("Totals after the V1 assembly twin")]
if first and "Totals after the V1 screws job" not in s:
    s = s.replace(first[0], tot + "\n\n" + first[0])
    open(P("HARDWARE_AUDIT.md"), "w").write(s)
    log.append("HARDWARE_AUDIT totals line")
# ---- STATE and START_HERE ----------------------------------------------------------------------------------------
for f in ("STATE.md", "START_HERE.md", "README.md"):
    if not os.path.exists(P(f)):
        continue
    t = open(P(f)).read()
    t = t.replace("V1 3D track: 26 of 64 cleared or decided", "V1 3D track: 26 of the then 64 rows cleared or decided")
    t = re.sub(r"\b26 of 64 cleared or decided", "%d of %d cleared or decided" % (len(cleared), n), t)
    t = t.replace("5 settled by the coupon test prints", "%d settled by the coupon test prints" % len(tprint))
    t = t.replace("6 waiting on the parts check", "%d waiting on the parts check" % len(waiting))
    t = t.replace("58/58 inserts", "48/48 inserts").replace("inserts 58/58", "inserts 48/48")
    t = t.replace("342 screws to fit, 221 to buy, 58 inserts, 16 washers", "317 screws to fit, 196 to buy, 48 inserts, 8 washers (D38 screw cut)")
    open(P(f), "w").write(t)
    log.append("counts in " + f)
done = ("- %s about %s ET, V1 screws job phase 2 (twin/screws/SCREWS_TWIN.md, calc only, CAD check only; D36, D38): 342 to 317 fitted screws, 58 to 48 inserts, 16 to 8 washers "
        "(fasteners.json LEAVE OUT (D38 screw cut), BOM need counts, MOUNTING.md); body_front, body_middle_top and body_middle_bottom in print/ carry the tongue, groove, lips and ribs "
        "(coupons K1 to K4 proposed for S1, TEST_PLAN 14); Pi header on KK 254 plugs (X1), P13 service plug (X3a), WAGO splices G and VSW (X4); 10b NKK MB2011LS1W01-BB; Wera tools "
        "and the 1/16 in bit on tool lines T16 to T19. Build time (cited per operation times): fastening 0.81 to %.2f h, cables %.2f to %.2f h; insert time BLOCKER.") % (day, clock, fh, ch_b, ch_a)
edit("STATE.md", "## Done (2026-11-01 evening into 2026-11-03)\n\n", "## Done (2026-11-01 evening into 2026-11-03)\n\n" + done + "\n")
# ---- TEST_PLAN section 14 ------------------------------------------------------------------------------------------
tp = """
## 14. Screw cut and fast cable checks (V1 screws job, D36 and D38; twin/screws/SCREWS_TWIN.md)

The twin numbers are calc only and CAD check only; these checks close them. Coupons are in altaay_lab/twin/screws/stl/.
1. Lip and tongue fit (coupons K1a with K1b, K2a with K2b): push fit by hand, no rock, 10 on and off cycles without whitening; K2a rib undersides printed without sag. If tight or loose, rerun twin/screws/mesh_designs.py with a new clearance C (now 0.25 mm).
2. Snap clip (coupon K3): snaps over a 6 mm dowel 10 times without whitening; after 24 h on the dowel at 50 C the opening has not grown (creep).
3. Tie bridge (coupon K4): a 2.5 mm tie passes the slot and holds a 20 N hand pull.
4. Tug test of the plugs after the section 9 walk: each KK 254 housing on the Pi header (X1), the P13 XT30U pair (X3a) and each wire in the WAGO splices G and VSW (X4), by hand; nothing moves or backs out. If one does, re-seat it and add a tie as strain relief.
5. Rattle and buzz: tap the boards held on 2 screws (Pi, servo adapter, camera) and both shells; compare the IMU accelerometer spectrum of the section 9 walk with the bench log; speaker at full volume without buzz. A rattle gets its screw back (every hole is kept).
6. Lid pilots: thread an M2.5x10 into a body_back pilot coupon 10 times, then pull by hand; if it strips, the lid gets M2.5 inserts (new part, Ahmed's OK).
7. Button 10b (MB2011LS1W01-BB) at the first fit: the snap-on cap clears the body_back opening and the plate holds it (D30).
8. Drop check of the closed trunk (shells, lid, battery): BLOCKER: height from the standing trunk centre in the URDF, to be set before the test; after it nothing separates, cracks are logged.
"""
t = open(P("TEST_PLAN.md")).read()
if "## 14. Screw cut" not in t:
    open(P("TEST_PLAN.md"), "w").write(t.rstrip("\n") + "\n" + tp)
    log.append("TEST_PLAN 14")
# ---- PRINT_PLAN: coupons and the changed STLs -------------------------------------------------------------------------
pp = ("\nV1 screws job (D38, proposed for session S1, not yet in its grams and hours: slice them with slice.py first): coupons K1a and K1b (tongue and groove), K2a and K2b (back lip and ribs), "
      "K3 (cable clip, snap) and K4 (tie bridge) from altaay_lab/twin/screws/stl/, tests in TEST_PLAN.md section 14. body_front.stl, body_middle_top.stl and body_middle_bottom.stl in print/ now carry "
      "the groove, the tongue and the back lips and ribs (+0.74 and +4.87 cm3; body_middle_bottom adds 812 mm2 of supported overhang): their slice numbers here and in SLICE_SUMMARY.md are from before the change.\n")
t = open(P("print", "PRINT_PLAN.md")).read()
k = t.find("### Step 2:")
if k > 0 and "V1 screws job (D38" not in t:
    open(P("print", "PRINT_PLAN.md"), "w").write(t[:k] + pp.lstrip("\n") + "\n" + t[k:])
    log.append("PRINT_PLAN S1 coupons")
# ---- CABLE_MAP ------------------------------------------------------------------------------------------------------------
edit("CABLE_MAP.md", "| Splices G, VSW, JFI,", "| Splices JFI,")
cm = ("| Pi header (X1, D36) | Molex KK 254 1-row crimp housings, one per cable (BOM 22c) | Molex 08-50-0114, 22 to 30 AWG, 3 A (BOM 22b) | 20 and 26 AWG | crimper: the KK 254 die fit of BOM T3 is not read (BLOCKER: check on 2 scrap ends) |\n"
      "| Splices G and VSW (X4, D36) | WAGO 221-415 (G, 4 wires) and 221-413 (VSW, 3 wires) lever splices, 24 to 12 AWG, 20 A (BOM 26b) | cage clamp, strip 11 mm | 16 and 20 AWG | none |\n"
      "| P13 service plug at the neck base (X3a, D36) | Amass XT30U pair (BOM 12), 15 A continuous, 30 A peak | solder cups | 20 AWG | Pinecil V2 |\n")
t = open(P("CABLE_MAP.md")).read()
row = [l for l in t.split("\n") if l.startswith("| Everything else |")]
if row and "(X1, D36)" not in t:
    t = t.replace(row[0], cm + row[0])
    t = t.replace("| Pi header | 2x20 2.54 mm header (pre-soldered or fitted) | solder to the pins;", "| Pi header (before X1) | 2x20 2.54 mm header (pre-soldered or fitted) | replaced by the KK 254 row below (D36); was: solder to the pins;")
    open(P("CABLE_MAP.md"), "w").write(t)
    log.append("CABLE_MAP connector rows")
# ---- SCREWS_TWIN phase 2 note -----------------------------------------------------------------------------------------------
t = open(os.path.join(HERE, "SCREWS_TWIN.md")).read()
note = ("\n## Phase 2 (%s, D36 and D38, applied)\n\n- D38: the back shell keeps 7 of 8 screws (F075 out) with its lips and ribs, so the cut is 342 to 317 fitted screws (25 fewer, 7.3 %%), 58 to 48 inserts, 16 to 8 washers. "
        "Applied in fasteners.json through report_fasteners.py (status LEAVE OUT (D38 screw cut), ids in data/phase2_fasteners.json), BOM.md, MOUNTING.md, the viewer.\n"
        "- The back lips are now clipped to body_middle_bottom's own height (the first cut stood 46 mm above it): side capacity 2925 N per side, up 2261 N, 812 mm2 added overhang.\n"
        "- D36: Wera tools and the 1/16 in bit on tool lines T16 to T19; KK 254 (22b, 22c; housing price BLOCKER), WAGO 221 pocket pack (26b), XT30U in P13 (line 12 Need 2). X3b not taken.\n"
        "- 10b: NKK MB2011LS1W01-BB (Newark 941 in stock, $10.37, search index); same MB2000 bushing and body, so the D30 plate is unchanged.\n"
        "- Time (cited per operation): fastening 0.81 to %.2f h; cables %.2f to %.2f h; total %.1f to %.1f h; insert time BLOCKER.\n") % (day, fh, ch_b, ch_a, 0.81 + ch_b, fh + ch_a)
if "## Phase 2 (" not in t:
    t = t.replace("\n## Files\n", note + "\n## Files\n", 1)
    open(os.path.join(HERE, "SCREWS_TWIN.md"), "w").write(t)
    log.append("SCREWS_TWIN phase 2 note")
# ---- history ---------------------------------------------------------------------------------------------------------------------
hist = P("history", "2026-11-04_%s_v1_screws.md" % hhmm)
open(hist, "w").write("""# V1 screws job: fewer screws, faster build (phase 1 and phase 2)

- Source: worktree branch v1-screws-local (from altaay-lab 5bd28f9, phase 2 on 52d2637); work by the V1 screws agent for the lead; Ahmed's asks of 2026-11-04 6:36 PM ET (screws, magnets, 90 %%) and 6:40 PM ET (cable management, a fast human build); D36 (Ahmed) and D38 (lead).
- Phase 1 (twin/screws/, calc only, CAD check only): classes a 75, b 259, c 8 of 342 fitted screws; safe minimum per joint against STRUCTURE_TWIN.md loads; 90 %% not reachable (the servo chain is already under the margin); tongue, groove, lips and ribs for the shells; cable operations counted and timed with cited per operation times.
- Phase 2 (%s about %s ET): fasteners.json 317 fitted, 48 inserts, 8 washers (25 screws LEAVE OUT (D38 screw cut), applied by fasteners/report_fasteners.py; render_fasteners.py and report_fasteners.py now treat any LEAVE OUT status as not fitted); print/ body_front, body_middle_top, body_middle_bottom replaced by the twin/screws/stl versions; BOM.md need counts, lines 22b, 22c, 26b, T16 to T19, 12 Need 2, 10b MB2011LS1W01-BB, totals (robot +$2.21, cables +$15.80, tools +$21.60); MOUNTING.md; sim/MASS_BUDGET.md delta row; wiring/netlist.yaml and wiring/make_harness_build.py (X1, X3a, X4), HARNESS_BUILD.md regenerated; CABLE_MAP.md; viewer/make_viewer_data.py skips the inserts of cut screws (48/48); viewer data regenerated into /home/user/v1_out/screws/viewer (duck.glb.txt, manifest.json); HARDWARE_AUDIT B65 to B69; TEST_PLAN 14; STATE.md, START_HERE.md counts.
- Not run: check_cables.py (no route or cut length changed), render_fasteners.py (PNGs show the earlier set), slice.py (the 3 changed parts and the coupons need a re-slice).
- Time: fastening 0.81 to %.2f h, cables %.2f to %.2f h (cited per operation times; insert, routing and test times BLOCKER).
""" % (day, clock, fh, ch_b, ch_a))
log.append("history " + os.path.basename(hist))
print("\n".join(log))
