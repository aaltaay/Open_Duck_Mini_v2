#!/usr/bin/env python3
"""MATCH check for altaay_lab/bom/order/ORDER.csv.

Fails if a current-design part is missing from the bill, or if the bill names
a part the current design does not have. Also checks buy counts, the dollar
columns, and the grand total printed in ORDER.md.

The current design is the lab files plus the picks already written down:
belly flush contacts, nest at 190 mm, the 40 mm wall card, the MCP73213
charger, PA6-CF shin sheets, the topology gram deltas, and STS3215 servos.
This script does not choose new parts. Exclusions cite the file that already
retired that part.

Run from the repo root:
  python3 altaay_lab/bom/order/check_order.py
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(LAB)
ORDER_CSV = os.path.join(HERE, "ORDER.csv")
ORDER_MD = os.path.join(HERE, "ORDER.md")

# Still in wiring/netlist.yaml. Retired by circuitry/CHARGER_BOARD.md,
# DECISIONS.md D61, or twin/dock/flush/FLUSH_CONTACTS.md. Not bought.
EXCLUDED = {
    "NL:CHG": "CHARGER_BOARD.md replaces the Adeept board with MCP73213",
    "NL:DKP": "D61 and FLUSH_CONTACTS.md: the chest pad is not the contact",
    "NL:DK2": "CHARGER_BOARD.md: the P-FET replaces the charge ideal diode",
    "NL:WK1": "CHARGER_BOARD.md: the old wake branch is not on the two-wire nest",
    "NL:JSN": "CHARGER_BOARD.md: the SENSE splice goes away with the four-net dock",
}

# Splices whose netlist part text says solder, including G and VSW.
# BOM.md line 26b names WAGO for G and VSW, and the netlist text does not.
# This order follows the netlist text and does not buy both.
SOLDER_SPLICES = [
    "NL:JFI", "NL:JFO", "NL:VSW", "NL:G", "NL:JBP", "NL:JBN",
    "NL:SPV", "NL:SPG", "NL:YD3", "NL:YG3", "NL:JG20", "NL:JG30",
    "NL:JG10", "NL:J5", "NL:JG", "NL:JGD",
]

# Parts the netlist does not list as components, already named in BOM.md,
# NEST_CAD.md, FLUSH_CONTACTS.md, CHARGER_BOARD.md, SHIN_EYE.md, or CLOSEUP.md.
ADDITIONS = [
    "FL:PLA", "FL:TPU", "FL:PA6-CF",
    "FS:16", "FS:17a", "FS:17b", "FS:17c", "FS:17d", "FS:17e", "FS:17f",
    "FS:17g", "FS:17h", "FS:17i", "FS:17j", "FS:17k", "FS:17l", "FS:17m",
    "FS:bag-sts", "FS:bag-sg90", "FS:factory",
    "NX:weld", "NX:sd", "NX:usb", "NX:spox-h", "NX:spox-t", "NX:kk-term", "NX:kk-h",
    "NX:well-route",
    "NX:wire16", "NX:wire20", "NX:wire22", "NX:wire26",
    "NX:heatshrink", "NX:solder", "NX:flux", "NX:kapton", "NX:vhb",
    "NX:tie", "NX:mount", "NX:mount-small", "NX:alcohol", "NX:loctite",
    "NX:bearing", "NX:glass", "NX:reflector", "NX:cam-cable",
    "NX:controller",
    "NX:felt-1", "NX:felt-2", "NX:sun-cloth", "NX:ring-cloth", "NX:feed-foil",
    "NX:wall-card", "NX:pin", "NX:gold-well", "NX:jack", "NX:foam",
    "NX:nest-pla", "NX:pcb", "NX:asm", "NX:adapter", "NX:gate", "NX:nozzle",
    "TL:T1", "TL:T2", "TL:T3", "TL:T4", "TL:T5", "TL:T6", "TL:T6b", "TL:T7b",
    "TL:T8", "TL:T9", "TL:T10", "TL:T11", "TL:T12", "TL:T13", "TL:T14",
    "TL:T15", "TL:T16", "TL:T17", "TL:T18", "TL:T19", "TL:L2",
]

# buy_qty must be at least this. Pack lines use pack_covers instead when set.
BUY_FLOOR = {
    "servo": 14,
    "pi": 1,
    "cell": 2,
    "imu": 1,
    "tof": 1,
    "bms": 1,
    "reg5": 1,
    "sw": 1,
    "bec": 1,
    "dk6": 1,
    "dk7": 1,
    "ntc": 1,
    "mic": 2,
    "touch": 2,
    "cam": 1,
    "foil": 1,
    "usb": 1,
    "flux": 1,
    "r2k2": 1,
    "usbc": 1,
    "r100": 1,
    "pinecil": 1,
    "tips": 1,
    "pa6": 1,
    "mcp": 1,
    "smaj": 1,
    "dmp": 1,
    "fs17a": 20,
    "fs17b": 12,
    "fs17c": 2,
    "fs17e": 28,
    "fs17f": 13,
    "fs17g": 4,
    "fs17i": 4,
    "fs17j": 14,
    "fs17k": 2,
    "fs17l": 8,
    "fs17m": 2,
    "gold-well": 5,
    "wall-card": 1,
    "foot": 4,
    "button": 1,
    "adapter-usb": 1,
    "xt30": 1,
    "holder": 2,
    "fuse15": 1,
    "fuse5": 1,
}

PACK_FLOOR = {
    "fs16": 54,   # 48 duck inserts plus 6 nest inserts, NEST_CAD.md section 5
    "fs17d": 78,  # pack of 100, fasteners.json
    "fs17h": 24,  # largest M2 size in the fitted count (M2x5)
    "xt30": 2,
}

SHIN = {"PR:shin_left_sheet.stl", "PR:shin_right_sheet.stl"}
PA6_LINE = "pa6"
PLA_LINE = "pla"
TPU_LINE = "tpu"

CITED = "cited, checked 2026-11-12"


def rel(*parts):
    return os.path.join("altaay_lab", *parts)


def fail(msg):
    print("FAIL: " + msg)
    return 1


def ids_in(path, prefix):
    out = []
    for m in re.finditer(r"^  - id: (\S+)", open(path, encoding="utf-8").read(), re.M):
        out.append(prefix + m.group(1))
    return out


def num(s):
    s = (s or "").strip()
    if s == "":
        return None
    return float(s)


def main():
    errors = 0
    nl_path = os.path.join(LAB, "wiring", "netlist.yaml")
    cb_path = os.path.join(LAB, "circuitry", "charger_board.yaml")
    parts_path = os.path.join(LAB, "print", "parts.csv")
    fast_path = os.path.join(LAB, "fasteners", "fasteners.json")

    required = []
    for tok in ids_in(nl_path, "NL:"):
        if tok not in EXCLUDED:
            required.append(tok)
    required.extend(ids_in(cb_path, "CB:"))
    required.extend(ADDITIONS)
    stl_mat = {}
    import csv as _csv
    with open(parts_path, encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            tok = "PR:" + row["stl"]
            required.append(tok)
            stl_mat[tok] = row["material"]
    required_set = set(required)
    if len(required) != len(required_set):
        errors += fail("duplicate id in the required set")

    with open(ORDER_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        errors += fail("ORDER.csv has no rows")
        print("%d FAIL" % errors)
        return 1

    covered = []
    by_id = {}
    suppliers = []
    total = 0.0
    by_supplier = {}
    for i, row in enumerate(rows, 1):
        lid = row["line_id"].strip()
        if lid in by_id:
            errors += fail("duplicate line_id %s" % lid)
        by_id[lid] = row
        suppliers.append(row["supplier"].strip())
        maps = [t.strip() for t in row["maps_to"].split(";") if t.strip()]
        if not maps:
            errors += fail("line %s has no maps_to" % lid)
        for t in maps:
            if t in EXCLUDED:
                errors += fail("line %s buys excluded %s (%s)" % (lid, t, EXCLUDED[t]))
            covered.append(t)
        label = row["price_label"].strip()
        blocker = row["blocker"].strip()
        stock = row["stock"].strip().lower()
        buy = num(row["buy_qty"])
        unit = num(row["unit_price_usd"])
        line = num(row["line_usd"])
        url = row["url"].strip()
        if label not in (CITED, "BLOCKER"):
            errors += fail("line %s price_label must be the cited label or BLOCKER" % lid)
        if label == CITED and not url:
            errors += fail("line %s is cited and has no url" % lid)
        if label == "BLOCKER" and unit is not None:
            errors += fail("line %s has a unit price but price_label BLOCKER" % lid)
        # A proposed pick has a live price and stays in the total. The note
        # says it is not yet verified against a coupon.
        proposed = blocker == "proposed pick, not yet verified"
        out = stock == "out of stock" or (blocker != "" and not proposed)
        if out:
            if line is not None:
                errors += fail("line %s is not in the total but line_usd is set" % lid)
        else:
            if buy is None or unit is None or line is None:
                errors += fail("line %s is in the total but qty, price, or line is blank" % lid)
            elif abs(line - round(buy * unit, 2)) > 0.001:
                errors += fail("line %s line_usd is not buy times unit" % lid)
            else:
                total += line
                sup = row["supplier"].strip()
                by_supplier[sup] = by_supplier.get(sup, 0.0) + line
        if lid in BUY_FLOOR:
            if buy is None or buy + 1e-9 < BUY_FLOOR[lid]:
                errors += fail("line %s buy_qty below %s" % (lid, BUY_FLOOR[lid]))
        if lid in PACK_FLOOR:
            pack = num(row["pack_covers"])
            if pack is None or pack + 1e-9 < PACK_FLOOR[lid]:
                errors += fail("line %s pack_covers below %s" % (lid, PACK_FLOOR[lid]))
        if "\u2014" in "".join(row.values()) or "\u2013" in "".join(row.values()):
            errors += fail("line %s has a dash that is not a hyphen" % lid)

    # suppliers stay in blocks
    seen = set()
    last = None
    for s in suppliers:
        if s != last:
            if s in seen:
                errors += fail("supplier %s is not in one block" % s)
            seen.add(s)
            last = s

    covered_set = set(covered)
    missing = sorted(required_set - covered_set)
    extra = sorted(covered_set - required_set)
    for t in missing:
        errors += fail("missing from the bill: %s" % t)
    for t in extra:
        errors += fail("on the bill but not in the current design: %s" % t)

    solder_row = by_id.get("solder")
    if solder_row:
        got = set(t.strip() for t in solder_row["maps_to"].split(";"))
        for t in SOLDER_SPLICES:
            if t not in got:
                errors += fail("solder line does not cover %s" % t)
    else:
        errors += fail("no solder line")

    # shin sheets are PA6-CF, other print rows keep parts.csv material
    def maps_of(lid):
        row = by_id.get(lid)
        if not row:
            return set()
        return set(t.strip() for t in row["maps_to"].split(";") if t.strip())

    pa6 = maps_of(PA6_LINE)
    pla = maps_of(PLA_LINE)
    tpu = maps_of(TPU_LINE)
    for tok, mat in stl_mat.items():
        if tok in SHIN:
            if tok not in pa6 or tok in pla or tok in tpu:
                errors += fail("%s must be on the PA6-CF line only" % tok)
        elif mat == "TPU":
            if tok not in tpu:
                errors += fail("%s must be on the TPU line" % tok)
        elif mat == "PLA":
            if tok not in pla:
                errors += fail("%s must be on the PLA line" % tok)
        else:
            errors += fail("unknown material for %s" % tok)

    # fasteners.json: no nuts and no standoffs to buy. Bag and factory screws
    # are inside the servo and SG90 lines, not a third fastener order.
    import json
    data = json.load(open(fast_path, encoding="utf-8"))
    nuts = [x for x in data["fasteners"] if x.get("kind") == "nut"]
    stands = [x for x in data["fasteners"] if x.get("kind") == "standoff"]
    if nuts:
        errors += fail("fasteners.json has nuts; the bill has no nut line")
    if stands:
        errors += fail("fasteners.json has standoffs to buy")

    text = open(ORDER_CSV, encoding="utf-8").read() + open(ORDER_MD, encoding="utf-8").read()
    if "\u2014" in text or "\u2013" in text:
        errors += fail("order files contain an em dash or an en dash")
    if re.search(r"#\d+", text):
        errors += fail("order files put a hash before a number")
    if "STS3250" in open(ORDER_CSV, encoding="utf-8").read():
        errors += fail("STS3250 is not the current servo pick")

    md = open(ORDER_MD, encoding="utf-8").read()
    m = re.search(r"Grand total of lines that can be bought today: \$([0-9]+\.[0-9]{2})", md)
    if not m:
        errors += fail("ORDER.md has no grand total line")
    elif abs(float(m.group(1)) - round(total, 2)) > 0.001:
        errors += fail("ORDER.md grand total %s, csv sum %.2f" % (m.group(1), total))
    for sup, amt in sorted(by_supplier.items()):
        pat = re.escape(sup) + r": \$([0-9]+\.[0-9]{2})"
        sm = re.search(pat, md)
        if not sm:
            errors += fail("ORDER.md has no total for %s" % sup)
        elif abs(float(sm.group(1)) - round(amt, 2)) > 0.001:
            errors += fail("ORDER.md %s is %s, csv is %.2f" % (sup, sm.group(1), amt))

    print("required %d, csv rows %d, buy-today total %.2f" % (len(required_set), len(rows), total))
    if errors:
        print("%d FAIL" % errors)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
