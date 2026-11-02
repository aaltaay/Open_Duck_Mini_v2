"""Rebuild altaay_lab/bom.json from the tables in altaay_lab/BOM.md (BOM.md is the source of truth).

Reads every table that has the BOM header (| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |)
under a "## <section>" heading and writes one JSON row per line with the same keys the older bom.py used.
Also prints the section subtotals so they can be checked against the Totals table in BOM.md.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "..", "BOM.md")
OUT = os.path.join(HERE, "..", "bom.json")
KEYS = ["i", "item", "spec", "need", "buy", "pack", "line", "sup", "link", "ships", "ver"]

def cells(row):
    return [c.strip() for c in row.strip().strip("|").split(" | ")]

rows, sec, in_tab = [], None, False
for line in open(MD, encoding="utf-8"):
    if line.startswith("## "):
        sec = line[3:].strip(); in_tab = False; continue
    if line.startswith("| # | Item | Spec |"):
        in_tab = True; continue
    if in_tab and line.startswith("|---"):
        continue
    if in_tab and line.startswith("|"):
        c = cells(line)
        if len(c) != len(KEYS):
            sys.exit(f"bad row in {sec}: {line[:80]}")
        d = dict(zip(KEYS, c)); d["sec"] = sec; rows.append(d); continue
    in_tab = False

tot = {}
for r in rows:
    try:
        tot[r["sec"]] = round(tot.get(r["sec"], 0.0) + float(r["line"]), 2)
    except ValueError:
        sys.exit(f"line price is not a number: {r['i']} {r['line']}")
json.dump(rows, open(OUT, "w"), indent=0)
print(len(rows), "rows written to bom.json")
for k, v in tot.items():
    print(f"{k}: {v:.2f}")
