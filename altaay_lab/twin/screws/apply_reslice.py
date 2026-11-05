"""Put the re-slice numbers (reslice.py) into the print docs, BOM line 27 and the mass budget row. Plates are moved by
the part deltas (calc), not re-sliced. Prints every edit and miss."""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
P = lambda *a: os.path.join(LAB, *a)
OUT = "/home/user/v1_out/screws"
log = []
OLD = {"body_front": (57.87, 4.03, 0.00), "body_middle_bottom": (103.09, 8.61, 14.13), "body_middle_top": (74.43, 6.61, 8.22)}
NEW = {}
pj = json.load(open(os.path.join(OUT, "slice_p", "parts.json")))
for k in OLD:
    d = pj[k + ".stl"]
    NEW[k] = (round(d["g"], 2), round(d["s"] / 3600, 2), round(d.get("g_support", 0.0), 2))
assert set(NEW) == set(OLD), ("missing part results", NEW)
cj = json.load(open(os.path.join(OUT, "slice_c", "coupons.json")))
s1 = [p for p in cj["session"] if any(k.startswith(("C1", "K1")) for k in p.get("per_object_g", {}))][0]
s1g = round(s1.get("g", s1.get("grams", 0)), 1)
s1h = round(s1.get("s", s1.get("seconds", 0)) / 3600, 2) if "s" in s1 or "seconds" in s1 else round(s1.get("h", 0), 2)
dg = {k: round(NEW[k][0] - OLD[k][0], 2) for k in OLD}
dh = {k: round(NEW[k][1] - OLD[k][1], 2) for k in OLD}
ds = {k: round(NEW[k][2] - OLD[k][2], 2) for k in OLD}
DG, DH, DS = round(sum(dg.values()), 1), round(sum(dh.values()), 2), round(sum(ds.values()), 1)
dS1g, dS1h = round(s1g - 41.2, 1), round(s1h - 4.14, 2)
log.append("parts new %s; deltas g %s h %s support %s; S1 %.1f g %.2f h" % (NEW, dg, dh, ds, s1g, s1h))
f1 = lambda x: ("%.1f" % x)
f2 = lambda x: ("%.2f" % x)
robot_g, robot_h = 1245.1 + DG, 106.7 + DH
full_g, full_h = 1347.8 + DG, 118.6 + DH
tot_g, tot_h = round(s1g + full_g, 1), 125.0 + DH + dS1g * 0 + dS1h
gate_g = 1450 + (tot_g - 1389.0)


def edit(f, old, new, count=0):
    p = P(f)
    s = open(p).read()
    n = s.count(old)
    if n:
        open(p, "w").write(s.replace(old, new) if count == 0 else s.replace(old, new, count))
    log.append("%s %s: %s -> %s (%d)" % ("edit" if n else "MISS", f, old[:50], new[:50], n))


# SLICE_SUMMARY per part rows and totals
for k, lab in (("body_front", "light (base)"), ("body_middle_bottom", "rings (base + 8 insert rings)"), ("body_middle_top", "rings (base + 8 insert rings)")):
    g0, h0, s0 = OLD[k]
    g1, h1, s1_ = NEW[k]
    edit("print/SLICE_SUMMARY.md", "| %s.stl | 1 | PLA | %s | %.2f | %.2f | %.2f | %.1f | %.2f |" % (k, lab, g0, h0, s0, g0, h0),
         "| %s.stl | 1 | PLA | %s | %.2f | %.2f | %.2f | %.1f | %.2f |" % (k, lab, g1, h1, s1_, g1, h1))
edit("print/SLICE_SUMMARY.md", "| Total | 52 | 1280.3 | 111.1 | 89.8 |", "| Total | 52 | %s | %s | %s |" % (f1(1280.3 + DG), f1(111.1 + DH), f1(89.8 + DS)))
for plate, parts in (("P220-02_PLA_base", ["body_front"]), ("P220-04_PLA_base_rings", ["body_middle_bottom"]), ("P220-05_PLA_base_rings", ["body_middle_top"]),
                     ("P256-02_PLA_base", ["body_front"]), ("P256-03_PLA_base_rings", ["body_middle_bottom"]), ("P256-04_PLA_base_rings", ["body_middle_top"])):
    for f in ("print/SLICE_SUMMARY.md", "print/PRINT_PLAN.md"):
        s = open(P(f)).read()
        for m in list(re.finditer(r"\| %s \| ([^|]*)\| ([\d.]+) \| ([\d.]+) \|" % re.escape(plate), s))[:1]:   # main table only, not the S1 gate fallback
            g, h = float(m.group(2)), float(m.group(3))
            g2, h2 = g + sum(dg[x] for x in parts), h + sum(dh[x] for x in parts)
            old = m.group(0)
            new = "| %s | %s| %s | %s |" % (plate, m.group(1), f1(g2), f2(h2))
            s = s.replace(old, new)
            log.append("plate %s %s: %s %s -> %.1f %.2f" % (f, plate, g, h, g2, h2))
        open(P(f), "w").write(s)
for f in ("print/SLICE_SUMMARY.md", "print/PRINT_PLAN.md"):
    s = open(P(f)).read()
    for m in re.finditer(r"\| Total \| (\d+) jobs \| ([\d.]+) \| ([\d.]+) \|", s):
        g, h = float(m.group(2)), float(m.group(3))
        s = s.replace(m.group(0), "| Total | %s jobs | %s | %s |" % (m.group(1), f1(g + DG), f1(h + DH)))
        log.append("plates total %s: %s %s -> %.1f %.1f" % (f, g, h, g + DG, h + DH))
    open(P(f), "w").write(s)
# coupon session S1, robot set, full print, filament and BOM 27
for f in ("print/PRINT_PLAN.md", "print/SLICE_SUMMARY.md", "STATE.md", "START_HERE.md", "README.md", "BOM.md", "PRINT_CHECK.md"):
    if not os.path.exists(P(f)):
        continue
    for o, n in (("41.2 g", "%s g" % f1(s1g)), ("4.14 h", "%s h" % f2(s1h)), ("1245.1 g and 106.7 h", "%s g and %s h" % (f1(robot_g), f1(robot_h))),
                 ("1347.8 g PLA", "%s g PLA" % f1(full_g)), ("1389.0 g PLA", "%s g PLA" % f1(tot_g)), ("1389.0", f1(tot_g)),
                 ("need 1389 g", "need %d g" % round(tot_g)), ("1389 g PLA", "%d g PLA" % round(tot_g)), ("about 611 g left", "about %d g left" % (2000 - round(tot_g))),
                 ("1450 g if the gate fails", "%d g if the gate fails" % round(gate_g)), ("robot set 1245 g", "robot set %d g" % round(robot_g)),
                 ("11 coupons, ", "17 coupons, "), ("one PLA plate with 11 test pieces", "one PLA plate with 17 test pieces"),
                 ("1.14 h over the 3 hour target", "%s h over the 3 hour target" % f2(s1h - 3)), ("about 6.3 h, ", "about %s h, " % f1(6.3 + dS1h))):
        s = open(P(f)).read()
        if o in s:
            edit(f, o, n)
for f in ("print/PRINT_PLAN.md", "STATE.md", "print/SLICE_SUMMARY.md"):
    s = open(P(f)).read()
    for o in re.findall(r"118\.6 h", s):
        pass
    if "118.6 h" in s:
        edit(f, "118.6 h", "%s h" % f1(full_h))
    if "| 125.0 |" in s:
        edit(f, "| 125.0 |", "| %s |" % f1(tot_h))
edit("print/PRINT_PLAN.md", "V1 screws job (D38, proposed for session S1, not yet in its grams and hours: slice them with slice.py first):",
     "V1 screws job (D38, in session S1 since 2026-11-04, sliced with slice.py and the D22 profile: K1a %.2f g, K1b %.2f g, K2a %.2f g, K2b %.2f g, K3 %.2f g, K4 %.2f g):" % tuple(
         cj["coupons"][k + ".stl"]["g"] for k in ("K1a_body_middle_top", "K1b_body_front", "K2a_body_middle_bottom", "K2b_body_back", "K3_cable_clip", "K4_tie_bridge")))
edit("print/PRINT_PLAN.md", "their slice numbers here and in SLICE_SUMMARY.md are from before the change.",
     "re-sliced 2026-11-04 with slice.py (D22): body_front %.2f g %.2f h, body_middle_top %.2f g %.2f h, body_middle_bottom %.2f g %.2f h; the plates holding them are moved by these part deltas (calc), not re-sliced; the S1 gate fallback numbers are from before the change. body_middle_bottom now gets 7 insert rings: the bore of F075 (unused since D38) is clear (CAD check) but slice.py no longer classifies it next to the lip root, so it has no solid ring; re-slice with it if F075 comes back." % (
         NEW["body_front"][0], NEW["body_front"][1], NEW["body_middle_top"][0], NEW["body_middle_top"][1], NEW["body_middle_bottom"][0], NEW["body_middle_bottom"][1]))
s = open(P("print/SLICE_SUMMARY.md")).read()
note = ("\nV1 screws job, 2026-11-04 (D38): body_front, body_middle_top and body_middle_bottom re-sliced with `slice.py parts --only` (D22 light profile) after the tongue, groove, lips and ribs; "
        "the coupon session re-sliced with K1a to K4 added (S1 %.1f g, %.2f h). Plates holding the 3 parts are moved by the part deltas (calc), not re-sliced; the before columns and the S1 gate fallback are from before.\n" % (s1g, s1h))
if "V1 screws job, 2026-11-04 (D38)" not in s:
    s = s.replace("\n## ", note + "\n## ", 1)
    open(P("print/SLICE_SUMMARY.md"), "w").write(s)
# mass budget row: the sliced on-robot delta replaces the CAD volume estimate of the lips
onrobot = round(sum((NEW[k][0] - NEW[k][2]) - (OLD[k][0] - OLD[k][2]) for k in OLD), 1)
mb = P("sim", "MASS_BUDGET.md")
s = open(mb).read()
m = re.search(r"(\| D38 screw cut \(V1 screws job\)[^\n]*?\| )([+-][\d.]+)( \| calc only: screws ([\d.]+) g)", s)
if m:
    screws = float(m.group(4))
    new_d = -(screws + 3.5) + onrobot
    s = s.replace(m.group(0), m.group(1) + "%+.1f" % new_d + m.group(3))
    s = s.replace("lips at 1.20 g/cm3 (PRINT_CHECK.md Overture PLA); the body_front groove is not taken off (re-slice in phase 2).",
                  "the 3 changed parts at their re-sliced grams less support (slice.py, D22): %+.1f g on the robot." % onrobot)
    open(mb, "w").write(s)
    log.append("MASS_BUDGET D38 row %+.1f (parts on robot %+.1f)" % (new_d, onrobot))
else:
    log.append("MISS MASS_BUDGET D38 row")
print("\n".join(log))
print("OLD totals: robot PLA 1245.1 g 106.7 h; full print 220 PLA 1347.8 g 118.6 h; with coupons 1389.0 g 125.0 h; S1 41.2 g 4.14 h")
print("NEW totals: robot PLA %.1f g %.1f h; full print 220 PLA %.1f g %.1f h; with coupons %.1f g %.1f h; S1 %.1f g %.2f h" % (robot_g, robot_h, full_g, full_h, tot_g, tot_h, s1g, s1h))
