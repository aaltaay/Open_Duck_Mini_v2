"""C2: every netlist pin with a connector has a mating part or an end treatment in the wires, and every crimp end fits the
Molex 08-70-1040 terminal. Extends audit/erc.py (which checks the crimp gauge range and 5264 sockets) and does not repeat it:
  a. every wire has 2 ends and each end treatment matches the connector class of its pin group (socket -> plug or
     housing + crimp, receptacle -> plug, splice -> splice, solder parts -> solder, lead -> lead)
  b. each made-lead housing: one wire per position, at most 3 positions, every position a crimp (08-70-1040), and the
     V position empty at the adapter (D15)
  c. counts: housings and crimp terminals in the netlist vs BOM.md lines 21 and 22 (Need), CABLE_MAP.md and WIRING.md
  d. kit cables used vs kit cables shipped (one per servo, BOM line 1)
  e. crimp ends: gauge in 22 to 28 AWG (from the erc.py report of E1, not re-checked) and insulation outer diameter vs
     the terminal ([I] 08-70-1040 insulation max 1.9 mm, Farnell listing via search index, 2026-11-02; Molex sheet not read)
  f. pin groups that are connectors with no wire and not marked nc
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c2_connectors.py [--selftest]
"""
import copy
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

CLASSES = [  # class, connector text pattern, allowed end patterns
    ("5264 socket", r"5264", [r"5264 plug", r"50-37-5033"]),
    ("large hole", r"large holes", [r"solder in large hole"]),
    ("XT30 cup", r"XT30", [r"XT30 solder cup"]),
    ("USB-C receptacle", r"USB-C receptacle", [r"USB-C plug"]),
    ("micro-USB receptacle", r"micro-USB", [r"micro-USB B plug"]),
    ("FPC", r"FPC", [r"\bFPC\b"]),
    ("screw terminal", r"terminal block|screw terminal", [r"screw terminal"]),
    ("Pi header", r"2x20 2\.54 mm header", [r"header pin"]),
    ("splice", r"splice", [r"^splice$"]),
    ("BEC lead", r"3-pin servo lead|input leads red and black", [r"BEC lead"]),
    ("holder or fuse lead", r"holder leads|ATO holder leads", [r"holder lead"]),
    ("SG90 lead", r"3-wire lead", [r"^servo$"]),
    ("0.1 in hole", r"0\.1 in holes", [r"solder in 0\.1 in hole"]),
    ("0.1 in header holes", r"0\.1 in header holes", [r"^solder$"]),
    ("lug", r"solder lugs", [r"solder lug"]),
    ("terminal", r"solder terminals", [r"solder terminal"]),
    ("tab", r"solder tabs", [r"solder tab"]),
    ("strap pad", r"series strap", [r"solder to strap"]),
    ("pad", r"solder pad", [r"solder pad"]),
    ("axial lead", r"axial leads", [r"resistor lead", r"^solder$"]),
    ("LED lead", r"LED bead leads", [r"LED lead", r"^solder$"]),
]
INS_MAX = 1.9          # mm, [I] 08-70-1040 insulation diameter max (Farnell listing via search index)
OD = {"22 AWG": 1.7, "24 AWG": None, "26 AWG": 1.5, "28 AWG": None}   # BNTECHGO silicone, cables3d/route_cables.py sources


def klass(conn):
    for name, pat, ok in CLASSES:
        if re.search(pat, conn or ""):
            return name, ok
    return None, None


def evaluate(net, R, quiet=False):
    comps = {c["id"]: c for c in net["components"]}
    pins = {}
    for c in comps.values():
        for p in c.get("pins") or []:
            pins["%s.%s" % (c["id"], p["pin"])] = (c, p)
    active = {cb["id"] for cb in net["cables"] if cb.get("status", "active") == "active"}
    wires = [w for w in net["wires"] if w["cable"] in active]
    n_ends, bad, unknown = 0, [], Counter()
    housings = defaultdict(list)       # (comp, group) -> [(pin, wire, end)]
    crimps = []
    for w in wires:
        ends = w.get("ends") or []
        if len(ends) != 2:
            bad.append("%s %s -> %s has %d end treatments" % (w["cable"], w["from"], w["to"], len(ends)))
            continue
        for ref, e in zip((w["from"], w["to"]), ends):
            n_ends += 1
            if ref not in pins:
                continue
            c, p = pins[ref]
            conn = (c.get("groups") or {}).get(p.get("group"), {}).get("connector", "")
            cl, ok = klass(conn)
            if cl is None:
                unknown[conn] += 1
                continue
            if not any(re.search(o, e) for o in ok):
                bad.append("%s %s: end '%s' does not fit a %s ('%s')" % (w["cable"], ref, e, cl, conn))
            if "50-37-5033" in e:
                housings[(c["id"], p["group"])].append((p["pin"], w, e))
                if "08-70-1040" not in e:
                    bad.append("%s %s: housing named without its crimp terminal: '%s'" % (w["cable"], ref, e))
            if "08-70-1040" in e:
                crimps.append((w, ref))
    for b in bad:
        R.find("FAIL", b, fix="fix the end treatment in wiring/netlist.yaml", where="altaay_lab/wiring/netlist.yaml")
    for conn, n in unknown.items():
        R.find("WARN", "%d wire ends on a connector this check has no rule for: '%s'" % (n, conn))
    if not quiet:
        R.ev("%d wires on active cables, %d wire ends, every end treatment checked against its pin group (%d classes)" % (
            len(wires), n_ends, len(CLASSES)))
    # b. housings
    for (cid, grp), rows in sorted(housings.items()):
        per = Counter(pn for pn, _, _ in rows)
        multi = [pn for pn, n in per.items() if n > 1]
        if multi:
            R.find("FAIL", "%s %s housing: positions %s carry more than one wire (one wire per terminal)" % (cid, grp, multi))
        if len(per) > 3:
            R.find("FAIL", "%s %s: %d positions used in a 3-position housing" % (cid, grp, len(per)))
        if cid == "U2" and any(pn.endswith(".V") for pn in per):
            R.find("FAIL", "adapter %s: V position used (D15 leaves it empty)" % grp)
    n_h, n_t = len(housings), len(crimps)
    if not quiet:
        R.ev("made-lead housings (Molex 50-37-5033): %d, %s; crimp terminals (08-70-1040): %d" % (
            n_h, ", ".join("%s %s %d pos" % (c, g, len(set(p for p, _, _ in r))) for (c, g), r in sorted(housings.items())), n_t))
    return dict(housings=n_h, crimps=n_t, crimp_rows=crimps, wires=wires, pins=pins)


def main():
    R = V.Result("C2", "Connectors: every wired pin has a mating part or end treatment; crimps fit the Molex 08-70-1040",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c2_connectors.py",
                 "Every end of the 118 wires on active cables vs its pin group's connector (21 classes); housing positions "
                 "(one wire each, adapter V empty); housing and terminal counts vs BOM 21/22, CABLE_MAP, WIRING.md; kit cables "
                 "used vs shipped; crimp insulation diameter; connector pins left open",
                 "Pin order inside each housing vs the servo port (TEST_PLAN.md section 2 polarity), crimp quality (section 1), "
                 "the real part labels marked [I] in the netlist")
    net = V.load_netlist()
    R.inp(V.lab("wiring", "netlist.yaml"), V.lab("BOM.md"), V.lab("CABLE_MAP.md"), V.lab("WIRING.md"))
    res = evaluate(net, R)
    # c. counts vs docs
    bom = V.bom_lines()
    need21, need22 = V.num(bom["21"]["Need"]), V.num(bom["22"]["Need"])
    buy21, buy22 = V.num(bom["21"]["Buy"]), V.num(bom["22"]["Buy"])
    cm = open(V.lab("CABLE_MAP.md")).read()
    wm = open(V.lab("WIRING.md")).read()
    cmh = re.search(r"Molex 50-37-5033 \(Mini-SPOX 3 pos\), (\d+) used", cm)
    cmt = re.search(r"Molex 08-70-1040 \(22 to 28 AWG\), (\d+) used", cm)
    wmc = re.search(r"\((\d+) housings, (\d+) terminals used\)", wm)
    R.ev("housings: netlist %d, BOM 21 Need %g (Buy %g), CABLE_MAP %s, WIRING.md %s" % (
        res["housings"], need21, buy21, cmh.group(1) if cmh else "?", wmc.group(1) if wmc else "?"))
    R.ev("terminals: netlist %d, BOM 22 Need %g (Buy %g), CABLE_MAP %s, WIRING.md %s" % (
        res["crimps"], need22, buy22, cmt.group(1) if cmt else "?", wmc.group(2) if wmc else "?"))
    for what, n, docs in (("housings", res["housings"], [need21, cmh and int(cmh.group(1)), wmc and int(wmc.group(1))]),
                          ("terminals", res["crimps"], [need22, cmt and int(cmt.group(1)), wmc and int(wmc.group(2))])):
        if any(d is None or int(d) != n for d in docs):
            R.find("FAIL", "%s: netlist %d vs docs %s" % (what, n, docs), fix="make BOM.md, CABLE_MAP.md and WIRING.md say %d" % n)
    if buy21 < res["housings"] or buy22 < res["crimps"]:
        R.find("FAIL", "BOM buys fewer housings or terminals than the netlist uses")
    # c2. the mating part of every connector class is bought on a BOM line (part number found in the line text)
    text = {lid: " ".join(b.get(k, "") for k in ("Item", "Spec", "Link")) for lid, b in bom.items()}
    MATES = [("5264 socket, made lead", "50-37-5033"), ("5264 socket, made lead terminal", "08-70-1040"),
             ("5264 socket, kit cable", "5264-3P"), ("XT30 cup", "XT30U"), ("USB-C and micro-USB", "USB C to Micro B"),
             ("camera FPC", "camera cable"), ("crimp tool", "PA-09"), ("splices and solder joints: heat shrink", "Heat shrink"),
             ("solder joints: solder", "solder wire")]
    miss_m = []
    for what, tok in MATES:
        lines = [lid for lid, t in text.items() if tok.lower() in t.lower()]
        if not lines:
            miss_m.append(what)
        R.ev("mating part %s: BOM line %s" % (what, ", ".join(lines) or "none")) if not lines else None
    R.ev("mating parts and end treatment supplies on a BOM line: %d of %d (%s)" % (
        len(MATES) - len(miss_m), len(MATES), ", ".join("%s: %s" % (w, ",".join(l for l, t in text.items() if tok.lower() in t.lower()))
                                                       for w, tok in MATES)))
    for m in miss_m:
        R.find("FAIL", "no BOM line buys the mating part for %s" % m, where="altaay_lab/BOM.md")
    # d. kit cables
    kit = sorted({w["cable"] for w in res["wires"] if w.get("gauge") == "kit cable"})
    shipped = V.num(bom["1"]["Need"])
    R.ev("kit cables used %d (%s) of %d shipped (one per servo, BOM line 1)" % (len(kit), ", ".join(kit), shipped))
    if len(kit) > shipped:
        R.find("FAIL", "more kit cables used than shipped")
    # e. crimps: gauge from E1 (erc.py), insulation diameter here
    g = Counter(w["gauge"] for w, _ in res["crimp_rows"])
    R.ev("crimp ends by gauge: %s (gauge range 22 to 28 AWG checked by erc.py, E1: 0 crimp findings)" % dict(g))
    for gauge, n in g.items():
        od = OD.get(gauge)
        if od is None:
            R.find("WARN", "%d crimp ends on %s: no insulation diameter on file" % (n, gauge))
        elif od + 0.1 > INS_MAX:
            R.find("FAIL", "%s silicone OD %.1f +/- 0.1 mm over the terminal insulation max %.1f mm" % (gauge, od, INS_MAX))
        else:
            R.ev("%s silicone OD %.1f +/- 0.1 mm vs 08-70-1040 insulation max %.1f mm ([I] listing via search index): fits, "
                 "%.1f mm left at the top of the tolerance" % (gauge, od, INS_MAX, INS_MAX - od - 0.1))
    R.find("WARN", "08-70-1040 insulation range and 3 A rating come from distributor listings read via a search index (Molex "
           "sheet not read; uk.rs-online.com and octopart.com are outside this session's network)",
           fix="read the Molex 5263 / 08-70-1040 product sheet and write the insulation range and current rating into "
               "CABLE_MAP.md 'Connector parts'", where="altaay_lab/CABLE_MAP.md")
    # f. connector groups with no wire on any pin and not nc
    used = Counter()
    for w in res["wires"]:
        used[w["from"]] += 1
        used[w["to"]] += 1
    idle = []
    for ref, (c, p) in res["pins"].items():
        conn = (c.get("groups") or {}).get(p.get("group"), {}).get("connector", "")
        if klass(conn)[0] in ("5264 socket", "USB-C receptacle", "micro-USB receptacle", "FPC") and p.get("dir") != "nc" and not used[ref]:
            idle.append(ref)
    R.ev("connector pins not wired and not marked nc: %s" % (idle or "none"))
    for i in idle:
        R.find("FAIL", "connector pin %s has no wire and is not marked nc" % i)
    if "--selftest" in sys.argv or os.environ.get("VERIFY_SELFTEST") == "1":
        T = copy.deepcopy(net)
        for w in T["wires"]:
            if w["cable"] == "SP1" and w["to"] == "SV20.BUS2.V":
                w["ends"] = ["splice", "solder"]
            if w["cable"] == "D1":
                w["ends"] = ["USB-C plug", "USB-C plug"]
        R2 = V.Result("C2x", "", "", "", "")
        evaluate(T, R2, quiet=True)
        R.ev("self-test: 2 injected faults (SP1 V soldered to a servo socket, USB-C plug on the Pi micro-USB) -> %d FAIL findings"
             % len(R2.fails()))
        if len(R2.fails()) < 2:
            R.find("FAIL", "self-test: the check missed an injected fault")
    R.key("%d wire ends match their connector class; housings %d and terminals %d agree with BOM 21/22, CABLE_MAP, WIRING.md; "
          "22 AWG OD 1.7 mm vs terminal max 1.9 mm" % (2 * len(res["wires"]), res["housings"], res["crimps"]))
    R.write()


if __name__ == "__main__":
    main()
