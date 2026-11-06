#!/usr/bin/env python3
"""The charging dock's bill of materials (prices read; buy nothing; no shipping, tax or tariff).

Run: python3 altaay_lab/twin/dock/dock_bom.py [--write]
Writes dock_bom.json (lines, totals with and without spares) and, with --write, the BOM table into DOCK_TWIN.md
section 7 (between the dock-bom markers) and DOCK_BOM_FULL.md (every physical item of the dock, one row each, from
dock_assembly.py, dock_fasteners.json and dock_netlist.yaml). Sources: the sourcing research of 2026-11-06 (page = the
seller page read, index = the search index only, re-read before buying) and this job's own reads (marked 2026-11-06).
Checks (exit 1): every fastener spec of dock_fasteners.json and every bought component of dock_assembly.py has a line
whose Need equals the count found; Buy >= Need.
"""
import argparse, collections, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# line, group, part, part number, need, buy, unit $, seller, url, read; unit None = BLOCKER (no price)
L = [
    ("K1", "electrical", "Charger board, MCP73213 2-cell, 8.40 V, 6 h timer, PROG via to ground for 1000 mA (U1 MCP73213-A6S/MF)", "Microchip MCP73213EV-2SOVP, DigiKey MCP73213EV-2SOVP-ND", 1, 1, 33.58, "DigiKey",
     "https://www.digikey.com/en/products/detail/microchip-technology/MCP73213EV-2SOVP/2170203", "index: $33.58 (Newark $32.88, index); A6S read in the user's guide BOM, DS51849A"),
    ("K2", "electrical", "Gate switch for CHG and SYS, MOSFET slide switch with reverse protection, HP", "Pololu 2815", 1, 1, 8.49, "Pololu", "https://www.pololu.com/product/2815", "page: $8.49"),
    ("K3", "electrical", "Seat microswitch, hinge lever, NO used (D2F-01L-D3 solder lug is the fallback)", "Omron D2F-01L", 1, 2, 1.44, "Mouser",
     "https://www.mouser.com/en/ProductDetail/Omron-Electronics/D2F-01L?qs=0w99tykdtPJyAZbwr7e4aQ%3D%3D", "index: $1.44"),
    ("K4a", "electrical", "Dual comparator, DIP-8 (NTC window, pin-voltage window)", "TI LM393P", 2, 3, 0.49, "DigiKey", "https://www.digikey.com/en/products/detail/texas-instruments/LM393P/277045", "index: $0.49"),
    ("K4b", "electrical", "555 timer, DIP-8 (110 ms wake one-shot)", "TI NE555P", 1, 2, 0.51, "DigiKey", "https://www.digikey.com/en/products/detail/texas-instruments/NE555P/277057", "index: $0.51"),
    ("K4c", "electrical", "2.50 V shunt reference, TO-92", "TI TL431AILPR", 1, 2, 0.24, "Mouser", "https://www.mouser.com/c/?q=TL431AILPR", "index: $0.24"),
    ("K4d", "electrical", "NPN, TO-92: Q1 gate driver, Q3 STAT inverter", "onsemi 2N3904BU", 2, 3, 0.28, "DigiKey", "https://www.digikey.com/en/products/detail/onsemi/2N3904BU/1413", "index: $0.28"),
    ("K4f", "electrical", "1N4148 (dock D1, D2; duck wake branch DK5)", "onsemi 1N4148", 3, 10, 0.039, "DigiKey", "https://www.digikey.com/en/products/detail/onsemi/1N4148/458603", "index: $0.039 at 10"),
    ("K4g", "electrical", "Resistor kit 1/4 W, 500 pcs: the 31 gate resistors (some values as series pairs) and the duck's DK5 10 k and 100 k", "SparkFun COM-10969", 1, 1, 9.95, "SparkFun", "https://www.sparkfun.com/products/10969", "page: $9.95 (22 k to 1 M, 1 k to 10 k ranges read 2026-11-06)"),
    ("K4h", "electrical", "Capacitor kit (100 nF x 3, 1 uF, 10 nF x 2 used; all in the kit, read 2026-11-06)", "SparkFun KIT-13698", 1, 1, 11.50, "SparkFun", "https://www.sparkfun.com/products/13698", "page: $11.50"),
    ("K4i", "electrical", "Gate board, Perma-Proto half (51 x 81 mm, 2 mounting holes 73.7 mm apart)", "Adafruit 1609", 1, 1, 4.50, "Adafruit", "https://www.adafruit.com/product/1609", "page: $4.50"),
    ("K5", "electrical", "Spring pin, press-fit into an insulator (1.600 mm hole), solder cup, 45 gf at mid stroke, 1.397 mm stroke, 6 A (4.80 A derated), 40 mOhm max", "Mill-Max 0933-0-15-20-72-14-11-0, DigiKey 54-0933-0-15-20-72-14-11-0-ND", 6, 8, None, "DigiKey",
     "https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/0933-0-15-20-72-14-11-0/26950711", "BLOCKER: price not read (digikey.com is outside this session's network; no index price); specs read on the Mill-Max data sheet. The 0932 it replaces was $1.23 (index)"),
    ("K6", "electrical", "Wall adapter 9 V 4 A 36 W, Class II, 5.5 x 2.1 mm plug centre positive", "Mean Well GSM36U09-P1J", 1, 1, 21.91, "TRC Electronics", "https://www.trcelectronics.com/products/mean-well-gsm36u09-p1j", "page: $21.91"),
    ("K6b", "electrical", "Panel DC jack, 5 A 24 V, 2.0 mm pin (mates 5.5 x 2.1), 5/16-32 bushing, nut and washer", "Same Sky PJ-005A", 1, 2, 3.07, "DigiKey",
     "https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/PJ-005A/165838", "index: $3.07 at 1 (digikey.com.br, USD); 5 A rating read on the Same Sky data sheet: the old BLOCKER (3 A needed) is closed"),
    ("K9", "electrical", "Adapter input fuse holder, inline ATO, 16 AWG leads 90 mm", "Littelfuse FHAC0001ZXJ, Newark 56P4171", 1, 1, 7.74, "Newark", "https://www.newark.com/littelfuse/fhac0001zxj/fuse-holder-in-line/dp/56P4171", "as BOM.md L3"),
    ("K9b", "electrical", "Adapter input fuse, 5 A ATO fast", "Littelfuse 0287005.PXCN", 1, 2, 0.44, "DigiKey", "https://www.digikey.com/en/products/result?keywords=0287005.PXCN", "as BOM.md DK4 (index)"),
    ("K11", "electrical", "Wire: 20 AWG red and black, 26 AWG white, yellow, blue, green (cut lengths in dock_netlist.yaml)", "BOM.md lines 23 and 25 surplus", 1, 0, 0.0, "(robot BOM)", "https://www.amazon.com/BNTECHGO-Gauge-Silicone-Wire-Temperature/dp/B01F8PO5XE", "the robot buys 50 ft of 20 AWG for 2.8 m and 175 ft of 26 AWG for 12.7 m"),
    ("K12", "electrical", "Heat shrink and solder (pin cups, jack lugs, holder leads)", "BOM.md lines 26 and 30 surplus", 1, 0, 0.0, "(robot BOM)", "https://www.amazon.com/Wirefy-180-Heat-Shrink-Tubing/dp/B084GDLSCK", "180 sleeves bought, 42 used by the robot"),
    ("K12b", "electrical", "VHB 4950 pads under the charger board, the 2815 and the fuse holder", "BOM.md line 29 surplus", 1, 0, 0.0, "(robot BOM)", "https://www.amazon.com/dp/B00D3RD9TO", "3/4 in x 5 yd; about 0.09 m used here"),
    ("K7", "mechanical", "PLA for the 18 printed dock kinds (22 prints), 1070 g sliced with the light profile", "Overture Easy PLA 1.75 mm 1 kg black, ASIN B09LCK7QJ2", 1, 1, 29.98, "Amazon", "https://www.amazon.com/dp/B09LCK7QJ2", "as BOM.md line 27; one roll plus 70 g of the 593 g the robot leaves"),
    ("K8a", "mechanical", "Guide rods: 4 mm 304 stainless, 100 mm, 10 pcs, cut to 2 x 76 mm (cheaper than the 17-4PH OnDrive GPM4000-100 at $16.89 each; slide fit checked at BT1)", "4 x 100 mm 304 stainless rod, 10 pcs", 2, 10, 1.166, "eBay", "https://www.ebay.com/p/21050690914", "index: $11.66 for 10 (whole pack in both totals)"),
    ("K8c", "mechanical", "Paddle return: constant-force spring 1.65 N, 6.4 mm drum, 4.75 x 0.08 mm, 304.8 mm", "Century Spring CF37CS", 2, 3, 2.82, "Century Spring", "https://www.centuryspring.com/shop/cf37cs", "page: $2.82 (2026-11-06)"),
    ("K8d", "mechanical", "Seat springs: music wire, OD 7.14, ID 6.12, free 23.88 mm, 0.25 N/mm", "Century Spring CC-28CS", 2, 3, 2.81, "Century Spring", "https://www.centuryspring.com/shop/cc-28cs", "page: $2.81 (2026-11-06)"),
    ("K8e", "fasteners", "M3x18 DIN 912 A2 (paddle pivot 2, drum axles 2)", "BelMetric BSH3X18SS", 4, 5, 0.13, "BelMetric", "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/", "page data: $0.13 (2026-11-06)"),
    ("K8f", "fasteners", "M3x16 DIN 912 A2 (spring channels to the mast face)", "BelMetric BSH3X16SS", 4, 5, 0.10, "BelMetric", "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/", "page data: $0.10"),
    ("K8g", "fasteners", "M3x30 DIN 912 A2 (column rib bolts)", "BelMetric BSH3X30SS", 9, 10, 0.14, "BelMetric", "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/", "page data: $0.14"),
    ("K8h", "fasteners", "M3x12 DIN 912 A2 (spine flange 4, base to column 4)", "BelMetric BSH3X12SS", 8, 10, 0.09, "BelMetric", "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/", "page data: $0.09 (2026-11-06)"),
    ("K8l", "fasteners", "M3x8 DIN 912 A2 (seat to spine 2, strip ends 2, gate board 2, bay tray 4, bay lid 4)", "BelMetric BSH3X8SS", 14, 16, 0.09, "BelMetric", "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/", "page data: $0.09 (2026-11-06)"),
    ("K8m", "fasteners", "M2x12 DIN 7985 A2 pan head (seat microswitch)", "BelMetric MSP2X12SS", 2, 3, 0.08, "BelMetric", "https://belmetric.com/m2x0-4-phillips-pan-head-stainless-coarse-din-7985/", "page data: $0.08 (2026-11-06)"),
    ("K8i", "fasteners", "M3 nylon insert lock nut DIN 985 A2 (ribs 9, channels 4, axles 2): single nuts, not a 100-pack", "BelMetric NN3SS", 15, 17, 0.09, "BelMetric", "https://belmetric.com/nylon-locking-nut-a2-stainless-din-985/", "page data: $0.09 (2026-11-06)"),
    ("K8n", "fasteners", "M2 nylon insert lock nut DIN 985 A2 (switch)", "BelMetric NN2SS", 2, 3, 0.58, "BelMetric", "https://belmetric.com/nylon-locking-nut-a2-stainless-din-985/", "page data: $0.58 (2026-11-06)"),
    ("K8o", "fasteners", "M3 heat-set inserts (20)", "BOM.md line 16 surplus (100 bought, 48 used)", 20, 0, 0.0, "(robot BOM)", "https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces", "52 left"),
    ("K8k", "mechanical", "Ballast: 1018 bar 5/16 x 2-1/2 x 12 in, cut to 2 x 120 mm (one per base pocket, 474 g each)", "Zoro Select 18F312X25-12", 1, 1, 18.85, "Zoro", "https://zoro.com/zoro-select-carbon-steel-bar-12-l-2-12-w-18f312x25-12/i/G301842078", "index: $18.85"),
    ("K10", "mechanical", "Rubber feet about 8 x 4 mm, 4-pack (seat base 4, base halves 8)", "Adafruit 550", 3, 3, 0.95, "Adafruit", "https://www.adafruit.com/product/550", "page: $0.95 per 4"),
    ("K13", "mechanical", "Three AprilTags tag36h11 (id 0 at 40 mm, ids 1 and 2 at 60 mm), printed on paper and glued", "paper", 3, 0, 0.0, "", "", "no purchase"),
]
REMOVED = [("K4e", "2N3906 PNP (wake pulse)", 0.54, "the 555 drives SENSE through D2 and R18; the PNP needed an inverter it never had"),
           ("K8b", "ServoCity 4 mm collar 2-pack", 4.99, "the printed carriage nose is the rest stop"),
           ("K8i (old)", "Foreverbolt M3 nylon nut 100-pack", 22.45, "15 single nuts at $0.09 (BelMetric) instead: $1.53 with 2 spares"),
           ("K8j", "3M 5490 PTFE tape", 43.55, "the pins carry the push; the face is only an over-travel stop (sim run with friction 0.4 on the face: section 12.1)"),
           ("K8a (old)", "OnDrive GPM4000-100 x 2", 33.78, "a 10-pack of 4 x 100 mm 304 rods at $11.66 (index)")]
DUCK = [
    ("DK1", "Chest contact pad, 100 x 76 x 0.8 mm FR4 ENIG, four strips (D50)", "OSH Park 2 layer 2 oz 0.8 mm, 3 copies", 1, 1, 58.90, "OSH Park", "https://docs.oshpark.com/services/two-layer-hhdc", "index: $5 per sq in x 11.78 sq in (3 copies; the order is the smallest buy)"),
    ("DK2", "Charge input ideal diode", "Pololu 5382", 1, 1, 3.79, "Pololu", "https://www.pololu.com/product/5382", "page: $3.79"),
    ("DK3", "Charge path fuse holder", "Littelfuse FHAC0001ZXJ", 1, 1, 7.74, "Newark", "https://www.newark.com/littelfuse/fhac0001zxj/fuse-holder-in-line/dp/56P4171", "as L3"),
    ("DK4", "Charge path fuse 5 A ATO", "Littelfuse 0287005.PXCN", 1, 2, 0.44, "DigiKey", "https://www.digikey.com/en/products/result?keywords=0287005.PXCN", "index"),
    ("DK5", "Cell NTC 10 k B3950 (Adafruit 372, $4.00) and 3.9 V zener (onsemi 1N5228B, $0.15); the 1N4148 and the 10 k and 100 k from dock K4f and K4g", "Adafruit 372 + onsemi 1N5228B", 1, 2, 4.15, "Adafruit, DigiKey", "https://www.adafruit.com/product/372", "page: $4.00 (NTC); index: $0.15 (zener)"),
    ("DK6", "Dock supply ideal diode", "Pololu 5382", 1, 1, 3.79, "Pololu", "https://www.pololu.com/product/5382", "page: $3.79"),
    ("DK7", "Pack side ideal diode, 12 A", "Pololu 5383", 1, 1, 4.95, "Pololu", "https://www.pololu.com/product/5383", "page: $4.95, in stock 2026-11-06"),
]
PACK_WHOLE = {"K4g", "K4h", "K8a", "K10", "K7", "DK1"}   # whole kits, packs and orders: Need costs the whole unit


def totals():
    need = buy = 0.0; blk = []
    for ln in L:
        line, grp, part, pn, n, b, u = ln[:7]
        if u is None:
            blk.append(line); continue
        if line in PACK_WHOLE and line == "K8a":
            need += 11.66; buy += 11.66; continue
        if line == "K10":
            need += 3 * u; buy += 3 * u; continue
        need += (u if line in PACK_WHOLE else u * n) if b else 0.0
        buy += u * b
    dn = sum(u * (1 if l in PACK_WHOLE else n) for l, _, _, n, b, u, *_ in DUCK)
    db = sum(u * b for l, _, _, n, b, u, *_ in DUCK)
    return dict(dock_need=round(need, 2), dock_buy=round(buy, 2), blockers=blk, duck_need=round(dn, 2), duck_buy=round(db, 2),
                k5_standin=dict(unit=1.23, need=round(6 * 1.23, 2), buy=round(8 * 1.23, 2), note="the 0932's index price, not the 0933's"),
                removed=round(sum(r[2] for r in REMOVED), 2))


def check():
    """Need per line against the dock's sources: fasteners, bought components, gate parts"""
    F = json.load(open(os.path.join(HERE, "dock_fasteners.json")))
    cnt = collections.Counter(f["line"] for f in F["fasteners"])
    A = json.load(open(os.path.join(HERE, "dock_assembly.json")))["dock"]["components"]
    comp = collections.Counter(c["bom"] for c in A if c["kind"] in ("bought", "board_part", "paper"))
    NL = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))
    gb = collections.Counter(p["bom"] for p in NL["gate_board"]["parts"])
    need = {l[0]: l[4] for l in L}
    bad = []
    for line, n in cnt.items():
        if line in need and need[line] != n:
            bad.append(f"{line}: need {need[line]}, fasteners.json fits {n}")
        elif line not in need and line != "K6b":
            bad.append(f"{line}: in dock_fasteners.json, no BOM line")
    expect = {"K1": comp["K1"], "K2": comp["K2"], "K3": comp["K3"], "K5": comp["K5"], "K6b": comp["K6b"], "K9": comp["K9"], "K8c": comp["K8c"],
              "K8d": comp["K8d"], "K8a": comp["K8a"], "K4i": comp["K4i"], "K13": comp["K13"],
              "K4a": gb["K4a"], "K4b": gb["K4b"], "K4c": gb["K4c"], "K4d": gb["K4d"]}
    for line, n in expect.items():
        if need[line] != n:
            bad.append(f"{line}: need {need[line]}, the assembly or gate board has {n}")
    if comp["K10"] != 4 * need["K10"]:
        bad.append(f"K10: {comp['K10']} feet in the assembly, {need['K10']} packs of 4")
    if comp["K8k"] != 2:
        bad.append("K8k: %d bars in the assembly, the line cuts 2" % comp["K8k"])
    for l in L:
        if l[5] and l[5] < l[4] and l[0] not in ("K8k", "K11", "K12", "K12b", "K8o", "K13", "K7", "K10"):
            bad.append(f"{l[0]}: buy {l[5]} < need {l[4]}")
    return bad


def md_table():
    rows = ["| Line | Part | Part number | Need | Buy | Unit $ | Buy $ | Seller | Link | Read |", "|---|---|---|---|---|---|---|---|---|---|"]
    for line, grp, part, pn, n, b, u, seller, url, read in L:
        bc = "BLOCKER" if u is None else ("%.2f" % (11.66 if line == "K8a" else u * b))
        rows.append(f"| {line} | {part} | {pn} | {n} | {b} | {'BLOCKER' if u is None else ('%.3f' % u if u < 0.1 else '%.2f' % u)} | {bc} | {seller} | {url} | {read} |")
    return "\n".join(rows)


def write_full():
    """DOCK_BOM_FULL.md: every physical item of the dock, one row per item or per spec group, with its BOM line"""
    A = json.load(open(os.path.join(HERE, "dock_assembly.json")))["dock"]["components"]
    F = json.load(open(os.path.join(HERE, "dock_fasteners.json")))["fasteners"]
    S = json.load(open(os.path.join(HERE, "stl", "slice.json")))
    NL = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))
    rows = ["# DOCK_BOM_FULL: every item of the charging dock", "",
            "Generated by twin/dock/dock_bom.py --write from dock_assembly.json, dock_fasteners.json, dock_netlist.yaml and stl/slice.json; "
            "do not edit by hand. Prices and links: DOCK_TWIN.md section 7. CAD check only, calc only.", "",
            "## Printed parts", "", "| Part | Qty | g each | h each | Line |", "|---|---|---|---|---|"]
    for n, r in S["parts"].items():
        rows.append(f"| {n} | {r['qty']} | {r['grams']} | {r['hours']} | K7 |")
    rows += ["", f"Total {S['total_g']} g, {S['total_h']} h.", "", "## Bought parts and board parts", "", "| Id | Item | Line | Mount |", "|---|---|---|---|"]
    for c in A:
        if c["kind"] != "printed":
            rows.append(f"| {c['id']} | {c['label']} | {c['bom']} | {c['mount']} |")
    gb = NL["gate_board"]["parts"]
    rows += ["", "## Gate board parts (dock_netlist.yaml)", "", "| Ref | Part | Line |", "|---|---|---|"] + [f"| {g['ref']} | {g['part']} | {g['bom']} |" for g in gb]
    cnt = collections.Counter((f["spec"], f["line"]) for f in F)
    rows += ["", "## Screws, nuts, inserts (dock_fasteners.json)", "", "| Spec | Count | Line |", "|---|---|---|"] + [f"| {k[0]} | {v} | {k[1]} |" for k, v in sorted(cnt.items())]
    rows += ["", "## Wires (dock_netlist.yaml, cut lengths from the 3D routes)", "", "| Cable | From | To | Gauge | Colour | Cut mm |", "|---|---|---|---|---|---|"]
    rows += [f"| {w['cable']} | {w['from']} | {w['to']} | {w['gauge']} | {w['color']} | {w['cut_mm']} |" for w in NL["wires"]]
    by = collections.defaultdict(int)
    for w in NL["wires"]:
        if "holder lead" not in (w.get("ends") or []):
            by[(w["gauge"], w["color"])] += w["cut_mm"]
    rows += ["", "Wire to cut, by gauge and colour (line K11): " + ", ".join("%s %s %d mm" % (g, c, v) for (g, c), v in sorted(by.items())) + "."]
    open(os.path.join(HERE, "DOCK_BOM_FULL.md"), "w").write("\n".join(rows) + "\n")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write", action="store_true"); a = ap.parse_args()
    T = totals(); bad = check()
    J = dict(lines=[dict(zip(("line", "group", "part", "pn", "need", "buy", "unit", "seller", "url", "read"), l)) for l in L],
             duck=[dict(zip(("line", "part", "pn", "need", "buy", "unit", "seller", "url", "read"), l)) for l in DUCK],
             removed=[dict(zip(("line", "part", "saved", "why"), r)) for r in REMOVED], totals=T, check=bad or "PASS",
             label="prices read 2026-11-06 or by the sourcing research the same day (page or index); buy nothing; no shipping, tax or tariff")
    json.dump(J, open(os.path.join(HERE, "dock_bom.json"), "w"), indent=1)
    print(json.dumps(T, indent=1)); print("CHECK", bad or "PASS")
    if a.write:
        p = os.path.join(HERE, "DOCK_TWIN.md"); s = open(p).read()
        t = ("<!-- dock-bom start: written by dock_bom.py -->\n" + md_table() + "\n\n" +
             "Dock station totals (read prices): **$%.2f** need only (whole kits and packs where a kit or pack is the smallest buy), **$%.2f** with spares. "
             "Not in them: K5 (BLOCKER: the 0933's price; at the 0932's $1.23 it would add $%.2f and $%.2f), shipping. "
             "Duck side (BOM.md DK1 to DK7): **$%.2f** need only, **$%.2f** with spares. Dock and duck side: **$%.2f** and **$%.2f**. "
             "Cut against the sourcing list, function kept: %s (together $%.2f).\n<!-- dock-bom end -->" % (
                 T["dock_need"], T["dock_buy"], T["k5_standin"]["need"], T["k5_standin"]["buy"], T["duck_need"], T["duck_buy"],
                 T["dock_need"] + T["duck_need"], T["dock_buy"] + T["duck_buy"],
                 "; ".join("%s %s $%.2f (%s)" % r for r in REMOVED), T["removed"]))
        s2 = re.sub(r"<!-- dock-bom start.*?<!-- dock-bom end -->", lambda m: t, s, flags=re.S)
        if "<!-- dock-bom start" not in s:
            raise SystemExit("DOCK_TWIN.md has no dock-bom markers")
        open(p, "w").write(s2)
        write_full()
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
