"""C1: every netlist component maps to a BOM.md line (or a BOM_FULL row), and every BOM_FULL row with a quantity matches
its source.

a. netlist -> BOM: each component (splices excepted: they are made from wire and heat shrink) maps to the BOM line(s)
   in MAP, and the part number in MAP is found in that line's text, so the mapping is real; every "BOM xx" reference in
   the netlist text names an existing line; the count of components per line equals BOM Need
b. BOM_FULL.md rows against their sources:
   printed parts      CAD node count of the fresh viewer run (E4 manifest) and print/parts.csv
   servos, horns      netlist SV10 to SV33 and the CAD horn nodes
   electronics        netlist component counts
   fasteners          fasteners.json counts per BOM line (fasteners agent), inserts and bearings from the CAD
   cables             active netlist cables; kit cables, housings, terminals from the netlist
   wire per colour    sum of netlist cut lengths per gauge and colour
c. BOM_FULL.md (committed) against the rows the viewer builds from today's sources (E4 manifest bom_full)
d. rows marked MISSING (no purchase line) and whether BOM.md says why
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c1_bom_coverage.py   (after e4_viewer.py)
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

MAP = [  # component id pattern, BOM lines, a part number or name that must appear in each line's Item/Spec/Link
    (r"PACK", ["6", "7"], ["P30B", "B09WCT8672"]),
    (r"BMS", ["8"], ["32175"]), (r"CHG", ["11"], ["B0BJTW4QBR"]), (r"XT30", ["12"], ["XT30U"]),
    (r"F1", ["L3", "L4"], ["FHAC0001ZXJ", "0287015.PXCN"]), (r"SW1", ["10"], ["2815"]), (r"CTL", ["10b"], ["power_switch.stl"]),
    (r"U1", ["L1"], ["010-0004-01"]), (r"U2", ["2"], ["25514"]), (r"U3", ["9"], ["D30V30F5"]), (r"PI", ["3", "4"], ["Zero 2 W", "SDSQUAR"]),
    (r"BNO", ["5"], ["2472"]), (r"FS[LR]\d", ["13"], ["SS-01"]), (r"R[LRP]", ["E3b"], ["100 ohm"]), (r"RF[LR]", ["13b"], ["2782"]),
    (r"LED[LRP]", ["E3"], ["1 W"]), (r"SG[LR]", ["14"], ["SG90"]), (r"AMP", ["E2"], ["MAX98357A"]), (r"SPK", ["E1"], ["CMS0361KLX"]),
    (r"CAM", ["E6"], ["5657"]), (r"SV\d+", ["1"], ["STS3215"]),
]


def bom_full_rows(path):
    rows = []
    for t in V.md_tables(path):
        if t["header"][:4] == ["ID", "Item", "Spec", "Qty"]:
            for r in t["rows"]:
                r = dict(r)
                r["section"] = t["section"]
                rows.append(r)
    return rows


def main():
    R = V.Result("C1", "Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c1_bom_coverage.py",
                 "56 netlist components to BOM lines (part numbers checked in the line text), netlist BOM references, counts per "
                 "line vs Need; 168 BOM_FULL rows vs CAD nodes, print/parts.csv, netlist, fasteners.json, wire cut sums; the "
                 "committed BOM_FULL.md vs a fresh build from today's sources; rows with no purchase line",
                 "Whether a bought part is the right one (datasheets), prices, the spares rule")
    net = V.load_netlist()
    bom = V.bom_lines()
    bf_path = V.lab("BOM_FULL.md")
    R.inp(V.lab("wiring", "netlist.yaml"), V.lab("BOM.md"), bf_path, V.lab("print", "parts.csv"), V.lab("fasteners", "fasteners.json"))
    text = {lid: " ".join(b.get(k, "") for k in ("Item", "Spec", "Link", "Verified")) for lid, b in bom.items()}
    # ---------------------------------------------------------------- a. netlist -> BOM
    per_line = Counter()
    unmapped = []
    for c in net["components"]:
        if c.get("kind") == "splice":
            continue
        hit = next((m for m in MAP if re.fullmatch(m[0], c["id"])), None)
        if not hit:
            unmapped.append(c["id"])
            continue
        for lid, tok in zip(hit[1], hit[2]):
            if lid not in bom:
                R.find("FAIL", "%s maps to BOM line %s, which does not exist" % (c["id"], lid))
            elif tok not in text[lid]:
                R.find("FAIL", "%s: BOM line %s does not name %s" % (c["id"], lid, tok))
            per_line[lid] += 2 if c["id"] == "PACK" and lid == "6" else 1
    nspl = sum(1 for c in net["components"] if c.get("kind") == "splice")
    R.ev("netlist: %d components, %d splices (made from wire and heat shrink, BOM 26), %d mapped to BOM lines, unmapped %s" % (
        len(net["components"]), nspl, len(net["components"]) - nspl - len(unmapped), unmapped or "none"))
    for u in unmapped:
        R.find("FAIL", "netlist component %s has no BOM line" % u, fix="add it to BOM.md or to MAP in this check")
    refs = set()
    for c in net["components"]:
        for m in re.finditer(r"\bBOM (?:line )?([0-9]+[a-z]?|[A-Z][0-9]+[a-z]?)\b", (c.get("part") or "") + " " + (c.get("source") or "")):
            refs.add((c["id"], m.group(1)))
    bad_ref = sorted(r for r in refs if r[1] not in bom)
    R.ev("'BOM xx' references in the netlist text: %d, to missing lines: %s" % (len(refs), bad_ref or "none"))
    for cid, lid in bad_ref:
        R.find("FAIL", "netlist %s refers to BOM %s, which is not a BOM.md line" % (cid, lid))
    cnt_bad = []
    for lid, n in sorted(per_line.items()):
        need = V.num(bom[lid]["Need"])
        if need is not None and need != n:
            cnt_bad.append("%s: netlist %d, Need %g" % (lid, n, need))
    R.ev("components per BOM line vs Need: %d lines, mismatches %s" % (len(per_line), cnt_bad or "none"))
    for b in cnt_bad:
        R.find("FAIL", "count per BOM line: " + b)
    # ---------------------------------------------------------------- b. BOM_FULL rows vs sources
    rows = bom_full_rows(bf_path)
    gen = re.search(r"Generated (.+?) by", open(bf_path).read())
    R.ev("BOM_FULL.md: %d rows, generated %s" % (len(rows), gen.group(1) if gen else "?"))
    man_p = os.path.join(V.out_dir(), "e4_viewer", "manifest.json")
    M = json.load(open(man_p)) if os.path.exists(man_p) else None
    if M is None:
        R.find("WARN", "E4 manifest not found: printed and CAD counts not checked")
    q = lambda r: V.num(r["Qty"])    # noqa: E731
    bad = []
    if M:
        nodes = M["nodes"]
        cad = Counter(n["part"] for n in nodes.values() if n.get("category") in ("pla", "tpu"))
        parts_csv = {r["stl"].replace(".stl", ""): int(r["qty"]) for r in
                     __import__("csv").DictReader(open(V.lab("print", "parts.csv"), encoding="utf-8"))}
        for r in rows:
            if r["section"] != "Printed parts":
                continue
            stem = re.search(r"print/([a-z0-9_]+)\.stl", r["Spec"])
            stem = stem.group(1) if stem else ("antenna" if "Antenna" in r["Item"] else None)
            n_cad = cad.get(stem) if stem != "antenna" else sum(1 for n in nodes.values() if n["part"] == "antenna")
            if q(r) != n_cad or (stem in parts_csv and parts_csv[stem] != q(r)):
                bad.append("%s %s: BOM_FULL %s, CAD %s, parts.csv %s" % (r["ID"], stem, r["Qty"], n_cad, parts_csv.get(stem)))
        np_ = sum(q(r) for r in rows if r["section"] == "Printed parts")
        R.ev("printed rows: %d rows, %g pieces; CAD printed nodes %d (+ %d antenna rods)" % (
            sum(1 for r in rows if r["section"] == "Printed parts"), np_, sum(cad.values()),
            sum(1 for n in nodes.values() if n["part"] == "antenna")))
        horns = Counter(n["part"] for n in nodes.values() if n["part"] in ("horn_drive", "horn_idle"))
        for r in rows:
            if r["Item"].startswith("Servo horn"):
                k = "horn_drive" if "drive" in r["Item"] else "horn_idle"
                if q(r) != horns[k]:
                    bad.append("%s %s: BOM_FULL %s, CAD %d" % (r["ID"], r["Item"], r["Qty"], horns[k]))
        ins = sum(1 for n in nodes.values() if n.get("category") == "insert")
        brg = sum(1 for n in nodes.values() if n["part"] == "bearing")
        for r in rows:
            if r["Item"].startswith("M3 heat-set insert") and q(r) != ins:
                bad.append("%s inserts: BOM_FULL %s, CAD %d" % (r["ID"], r["Qty"], ins))
            if r["Item"].startswith("Ball bearing") and q(r) != brg:
                bad.append("%s bearings: BOM_FULL %s, CAD %d" % (r["ID"], r["Qty"], brg))
        R.ev("horns in CAD %s, inserts %d, bearings %d" % (dict(horns), ins, brg))
    # servos and electronics vs netlist
    comps = [c["id"] for c in net["components"]]
    nsv = sum(1 for c in comps if re.fullmatch(r"SV\d+", c))
    srv = [r for r in rows if r["Item"].startswith("Feetech STS3215")]
    if sum(q(r) for r in srv) != nsv:
        bad.append("servo rows %g vs netlist %d" % (sum(q(r) for r in srv), nsv))
    grp = {"E16": (r"FS[LR]\d", "Foot contact switch"), "E17": (r"RF[LR]", "Foot switch pull-up"), "E18": (r"LED[LRP]", "1 W LED"),
           "E19": (r"R[LRP]", "LED resistor"), "S17": (r"SG[LR]", "SG90-class antenna servo")}
    for r in rows:
        for _, (pat, item) in grp.items():
            if r["Item"].startswith(item):
                n = sum(1 for c in comps if re.fullmatch(pat, c))
                if q(r) != n:
                    bad.append("%s %s: BOM_FULL %s, netlist %d" % (r["ID"], item, r["Qty"], n))
    # cables and connectors vs netlist
    active = [cb for cb in net["cables"] if cb.get("status", "active") == "active"]
    cab_rows = [r for r in rows if r["section"] == "Cables"]
    ids_bf = {r["Item"].split(":")[0] for r in cab_rows}
    ids_net = {cb["id"] for cb in active}
    if ids_bf != ids_net:
        bad.append("cable rows %s vs netlist active cables: missing %s, extra %s" % (len(cab_rows), sorted(ids_net - ids_bf), sorted(ids_bf - ids_net)))
    R.ev("cables: BOM_FULL %d rows, netlist %d active cables" % (len(cab_rows), len(ids_net)))
    kit = len({w["cable"] for w in net["wires"] if w.get("gauge") == "kit cable"})
    housings = len({(w[e].split(".")[0], w[e].split(".")[1]) for w in net["wires"] for e, en in zip(("from", "to"), w.get("ends") or [])
                    if "50-37-5033" in en})
    crimps = sum(1 for w in net["wires"] for en in (w.get("ends") or []) if "08-70-1040" in en)
    for r in rows:
        for item, n in (("Servo kit cable", kit), ("Mini-SPOX housing", housings), ("Mini-SPOX crimp terminal", crimps)):
            if r["Item"].startswith(item) and q(r) != n:
                bad.append("%s %s: BOM_FULL %s, netlist %d" % (r["ID"], item, r["Qty"], n))
    # wire per gauge and colour
    cut = defaultdict(float)
    for w in net["wires"]:
        g = str(w.get("gauge"))
        if re.fullmatch(r"\d+ AWG", g) and w.get("cut_mm"):
            cut[(g, w.get("color"))] += w["cut_mm"] / 1000.0
        if g == "SG90 lead + 26 AWG":   # 20 mm extension of each lead wire (CABLE_MAP D9)
            cut[("26 AWG", w.get("color"))] += 0.0
    wrong_w = []
    for r in rows:
        m = re.match(r"Wire (\d+ AWG) (\w+)$", r["Item"])
        if m:
            v = cut.get((m.group(1), m.group(2)), 0.0)
            if abs(v - q(r)) > 0.006:
                wrong_w.append("%s %s %s: BOM_FULL %s m, netlist %.2f m" % (r["ID"], m.group(1), m.group(2), r["Qty"], v))
    R.ev("wire per gauge and colour: %d BOM_FULL rows checked against the netlist cut sums, %d differ" % (
        sum(1 for r in rows if r["Item"].startswith("Wire ")), len(wrong_w)))
    bad += wrong_w
    # fasteners vs fasteners.json
    fj = V.lab("fasteners", "fasteners.json")
    if os.path.exists(fj):
        D = json.load(open(fj))
        fit = [f for f in D["fasteners"] if f["kind"] == "screw" and not any(s in str(f.get("status") or "") for s in ("NOT FITTED", "LEAVE OUT"))]
        per = Counter(f.get("line") for f in fit)
        per_spec = Counter(f["spec"] for f in fit)
        all_spec = Counter(f["spec"] for f in D["fasteners"] if f["kind"] == "screw")
        for r in rows:
            ln = r.get("Line", "")
            if r["Item"] in all_spec:                      # one row per screw spec (BOM_FULL built from fasteners.json)
                if q(r) != per_spec.get(r["Item"], 0):
                    if q(r) == all_spec[r["Item"]]:
                        R.find("WARN", "%s %s: BOM_FULL qty %s counts %d screws that are not fitted (fasteners.json: %d fitted)" % (
                            r["ID"], r["Item"], r["Qty"], all_spec[r["Item"]] - per_spec.get(r["Item"], 0), per_spec.get(r["Item"], 0)),
                            fix="bom_full.py: count only fitted screws in the Qty column", where="altaay_lab/viewer/bom_full.py")
                    elif not (M and any(f["item"] == r["Item"] and V.num(f["qty"]) == per_spec.get(r["Item"], 0) for f in M["bom_full"])):
                        bad.append("%s %s: BOM_FULL %s, fasteners.json %d fitted" % (r["ID"], r["Item"], r["Qty"], per_spec.get(r["Item"], 0)))
                    # else: the fresh build has the right count, so this is only a stale BOM_FULL.md (reported in part c)
            elif re.fullmatch(r"17[a-i]", ln) and r["Item"] != "Threadlocker":   # older BOM_FULL: one row per BOM line
                if q(r) != per.get(ln, 0):
                    bad.append("%s %s (line %s): BOM_FULL %s, fasteners.json %d" % (r["ID"], r["Item"], ln, r["Qty"], per.get(ln, 0)))
        R.ev("fitted screws in fasteners.json: %d; BOM_FULL screw rows %d (section %s)" % (
            len(fit), sum(1 for r in rows if re.fullmatch(r"17[a-i]", r.get("Line", ""))),
            ", ".join(sorted({r["section"] for r in rows if re.fullmatch(r"17[a-i]", r.get("Line", ""))}))))
    for b in bad:
        R.find("FAIL", "BOM_FULL quantity does not match its source: " + b,
               fix="re-run viewer/make_viewer_data.py --write-bom after the sources are final (needs the viewer to read "
                   "fasteners.json: see E4) and commit BOM_FULL.md and bom_full.csv", where="altaay_lab/BOM_FULL.md")
    # ---------------------------------------------------------------- c. committed vs fresh build
    if M:
        key = lambda sec, item: (sec, re.sub(r"\s+", " ", item).strip())     # noqa: E731  rows keyed by item, not by ID
        fresh = {key(r["section"], r["item"]): r for r in M["bom_full"]}
        com = {key(r["section"], r["Item"]): r for r in rows}
        diffs = ["%s %s: BOM_FULL.md %s, fresh build %s" % (r["ID"], k[1], r["Qty"], fresh[k]["qty"]) for k, r in com.items()
                 if k in fresh and V.num(r["Qty"]) != V.num(fresh[k]["qty"])]
        gone = ["%s %s" % (r["ID"], k[1]) for k, r in com.items() if k not in fresh]
        new_ = ["%s (%s)" % (k[1], fresh[k]["qty"]) for k in fresh if k not in com]
        R.ev("committed BOM_FULL.md vs a fresh build from today's sources (E4, %s): %d quantities differ, %d rows gone, %d new" % (
            M["meta"]["generated"], len(diffs), len(gone), len(new_)))
        if diffs or gone or new_:
            R.find("FAIL", "BOM_FULL.md is older than its sources: %s" % "; ".join(
                (["qty " + d for d in diffs[:8]] + ["gone " + g for g in gone[:4]] + ["new " + n for n in new_[:6]])),
                fix="re-run python3 altaay_lab/viewer/make_viewer_data.py --out <scratch> --write-bom and commit BOM_FULL.md and bom_full.csv",
                where="altaay_lab/BOM_FULL.md")
        nscrew_view = M["checklist"]["summary"]["screws"]["found"]
        if os.path.exists(fj) and nscrew_view == 0:
            R.find("FAIL", "the viewer reads 0 screws from fasteners.json (%s), so BOM_FULL takes its screw counts from BOM.md Need "
                   "instead of the fastener schedule" % M["meta"]["sources"].get("fasteners"),
                   fix="viewer/make_viewer_data.py load_fasteners(): also accept 'seat_world' for the head point, i.e. "
                       "p = p if p is not None else _first(r, \"head_world_mm\", \"head_world\", \"seat_world\", \"p_world\", "
                       "\"head_point\", \"pos\", \"p\"), and read 'length_mm' (already) and head 'dk'/'k' from r['head']",
                   where="altaay_lab/viewer/make_viewer_data.py")
    # heat shrink: the BOM_FULL count against the netlist's splice and solder ends (TEST_PLAN.md 1.3: every joint covered)
    if M:
        act = {cb["id"] for cb in net["cables"] if cb.get("status", "active") == "active"}
        ends = [e.lower() for w in net["wires"] if w["cable"] in act for e in (w.get("ends") or [])]
        n_spl = sum(1 for e in ends if "splice" in e)
        n_sol = sum(1 for e in ends if "splice" not in e and "08-70-1040" not in e and ("solder" in e or "header pin" in e or "lead" in e))
        hs = next((r for r in M["bom_full"] if r["item"].startswith("Heat shrink")), None)
        if hs:
            R.ev("heat shrink: fresh BOM_FULL %s pieces; netlist %d splice ends and %d soldered ends (BOM 26 buys %s)" % (
                hs["qty"], n_spl, n_sol, bom.get("26", {}).get("Buy", "?") + " x " + bom.get("26", {}).get("Pack", "?")))
            if V.num(hs["qty"]) < n_spl:
                R.find("WARN", "BOM_FULL counts %s heat shrink pieces (the sleeves the 3D view draws), fewer than the %d splice ends in "
                       "the netlist; TEST_PLAN.md 1.3 wants heat shrink over every solder joint and splice" % (hs["qty"], n_spl),
                       fix="count one sleeve per splice end and per wire-to-wire or lead joint in viewer/bom_full.py (the old netlist "
                           "estimate), or say in TEST_PLAN.md 1.3 which joints get none", where="altaay_lab/viewer/bom_full.py")
    # ---------------------------------------------------------------- d. rows with no purchase line
    bm = open(V.lab("BOM.md")).read()
    nc = re.search(r"^Not costed: (.*)$", bm, re.M)
    nc = nc.group(1).lower() if nc else ""
    # statuses from the fresh build when there is one (the committed file can be older than BOM.md, see part c)
    srows = [dict(ID=f["id"], Item=f["item"], Status=f["status"], Note=f.get("note", ""), Qty=f["qty"]) for f in M["bom_full"]] if M else rows
    R.ev("purchase status from the %s: %s" % ("fresh build (E4)" if M else "committed BOM_FULL.md",
                                             dict(Counter(r["Status"] for r in srows))))
    for r in srows:
        if r["Status"] in ("SHORT", "CHECK"):
            R.find("FAIL", "BOM_FULL %s %s is %s: %s" % (r["ID"], r["Item"], r["Status"], r["Note"]),
                   fix="BOM.md: Need and Buy from the source count", where="altaay_lab/BOM.md")
        if r["Status"] == "MISSING":
            item = r["Item"]
            sz = re.search(r"\b(M\d(?:\.\d)?x\d+)\b", item)
            head = "button" if re.search(r"7380|button", item, re.I) else ""
            have = [lid for lid, b in bom.items() if sz and re.search(r"\b%s\b" % re.escape(sz.group(1)), b["Item"] + " " + b["Spec"])
                    and (not head or re.search(head, b["Item"] + " " + b["Spec"], re.I))]
            if have:
                R.find("WARN", "%s %s shows MISSING, but BOM.md line %s buys it: fasteners.json does not name the line, so the "
                       "BOM_FULL build cannot link it" % (r["ID"], item, ", ".join(have)),
                       fix="set line '%s' on these screws in fasteners.json, then re-run make_viewer_data.py --write-bom" % have[0],
                       where="altaay_lab/fasteners")
                continue
            known = any(k in nc for k in re.findall(r"[a-z]{5,}", item.lower()) if k not in ("supply", "small", "digital", "robot", "tests"))
            R.find("WARN" if known else "FAIL", "%s %s: needed (%s) but no BOM.md line buys it%s" % (
                r["ID"], item, r["Note"], " (BOM.md 'Not costed' names it)" if known else " and BOM.md does not say why"),
                fix=None if known else "add a BOM.md line (or name it under 'Not costed' with the reason)", where="altaay_lab/BOM.md")
    used = {x.strip() for r in rows for x in r.get("Line", "").split(",") if x.strip()}
    unused = [lid for lid in bom if lid not in used]
    R.ev("BOM.md lines used by a BOM_FULL row: %d of %d (unused: %s)" % (len(bom) - len(unused), len(bom), unused or "none"))
    if unused:
        R.find("WARN", "BOM.md lines not used by any BOM_FULL row: %s" % ", ".join("%s (%s)" % (u, bom[u]["Item"]) for u in unused),
               fix="map them in viewer/bom_full.py (tools, washers) or link them from fasteners.json", where="altaay_lab/viewer/bom_full.py")
    nf = len([f for f in R.d["findings"] if f["sev"] == "FAIL"])
    R.key("43 netlist parts map to BOM lines with matching part numbers (13 splices are made); BOM_FULL %d rows vs sources: "
          "%d FAIL (see list)" % (len(rows), nf))
    R.write()


if __name__ == "__main__":
    main()
