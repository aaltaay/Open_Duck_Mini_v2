"""Recompute the subtotals, the Totals table and the test order total in altaay_lab/BOM.md from its line items.
Only numbers are rewritten; all other text stays. Run after any BOM.md edit, then audit/bom_md_to_json.py.
"""
import os, re

MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "BOM.md")
SECS = ["Robot", "Fasteners and mechanical", "Cables, connectors, wire", "Print material",
        "Expression (optional upstream)", "Tools (one-time)"]

s = open(MD, encoding="utf-8").read()
out, sec, tot, in_tab = [], None, {}, False
for line in s.split("\n"):
    if line.startswith("## "):
        sec = line[3:].strip(); in_tab = False
    if line.startswith("| # | Item | Spec |"):
        in_tab = True; tot.setdefault(sec, 0.0)
    elif in_tab and line.startswith("|") and not line.startswith("|---"):
        c = [x.strip() for x in line.strip().strip("|").split(" | ")]
        tot[sec] = round(tot[sec] + float(c[6]), 2)
    elif in_tab and not line.startswith("|"):
        in_tab = False
    if line.startswith("Subtotal: $") and sec in tot:
        line = f"Subtotal: ${tot[sec]:.2f}"
    out.append(line)
s = "\n".join(out)
core = sum(tot[k] for k in SECS[:4]); expr = tot[SECS[4]]; tools = tot[SECS[5]]
rows = {k: f"{tot[k]:.2f}" for k in SECS}
rows["Build total (robot + fasteners + cables + filament)"] = f"{core:.2f}"
rows["Build + expression pack"] = f"{core + expr:.2f}"
rows["Build + expression + tools"] = f"{core + expr + tools:.2f}"
L = s.split("\n")
for i, line in enumerate(L):
    m = re.match(r"\| (.+?) \| [0-9.]+ \|$", line)
    if m and m.group(1) in rows:
        L[i] = f"| {m.group(1)} | {rows[m.group(1)]} |"
s = "\n".join(L)
to = sum(float([x.strip() for x in l.strip().strip("|").split(" | ")][3]) for l in s.split("\n") if re.match(r"\| TO\d+ \|", l))
s = re.sub(r"Test order total: \$[0-9.]+\.", f"Test order total: ${to:.2f}.", s)
open(MD, "w", encoding="utf-8").write(s)
print({k: tot[k] for k in SECS}, "build", round(core, 2), "with expression", round(core + expr, 2),
      "with tools", round(core + expr + tools, 2), "test order", round(to, 2))
