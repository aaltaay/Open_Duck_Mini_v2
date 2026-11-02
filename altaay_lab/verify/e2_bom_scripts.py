"""E2 and E3: run audit/bom_totals.py and audit/bom_md_to_json.py on a copy of BOM.md (never on the real one) and
compare what they produce with the committed BOM.md and bom.json. Also checks every line's arithmetic that the
scripts do not: Buy >= Need on every line where Need and Buy count the same unit.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e2_bom_scripts.py
"""
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

OUT = os.path.join(V.out_dir(), "e2_bom")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "audit"))
for f in ("BOM.md", "bom.json"):
    shutil.copy(V.lab(f), os.path.join(OUT, f))
for f in ("bom_totals.py", "bom_md_to_json.py"):
    shutil.copy(V.lab("audit", f), os.path.join(OUT, "audit", f))

# ------------------------------------------------------------------------------------------- E2 totals
R2 = V.Result("E2", "BOM.md subtotals, totals and test order total (audit/bom_totals.py on a copy)",
              "VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py",
              "Every section subtotal, the Totals table and the test order total recomputed from the line items; "
              "Buy >= Need on every line where both count the same unit",
              "Whether the prices are still current (read 2026-11-01); quantities themselves (C1, C4)")
R2.inp(V.lab("BOM.md"), V.lab("audit", "bom_totals.py"))
p = subprocess.run([sys.executable, "-I", os.path.join(OUT, "audit", "bom_totals.py")], cwd=OUT, capture_output=True,
                   text=True, timeout=120)
if p.returncode != 0:
    R2.not_run("bom_totals.py failed: " + (p.stdout + p.stderr)[-300:])
else:
    R2.ev("bom_totals.py: " + p.stdout.strip().replace("'", ""))
    mt = re.search(r"build ([0-9.]+) with expression ([0-9.]+) with tools ([0-9.]+) test order ([0-9.]+)", p.stdout)
    if mt:
        R2.key("recompute changes nothing: build $%s, + expression $%s, + tools $%s, test order $%s" % mt.groups())
    a, b = open(V.lab("BOM.md"), encoding="utf-8").read(), open(os.path.join(OUT, "BOM.md"), encoding="utf-8").read()
    if a == b:
        R2.ev("BOM.md copy unchanged after the recompute: every subtotal and total in BOM.md matches its lines")
    else:
        import difflib
        diff = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
        R2.find("FAIL", "bom_totals.py changes %d lines of BOM.md: %s" % (len(diff), " / ".join(diff[:6])),
                fix="run python3 altaay_lab/audit/bom_totals.py then audit/bom_md_to_json.py and commit", where="altaay_lab/BOM.md")
    # arithmetic the script does not do
    lines = V.bom_lines(V.lab("BOM.md"))
    n_chk, n_price = 0, 0
    for lid, r in lines.items():
        need, buy, pack = V.num(r["Need"]), V.num(r["Buy"]), (r["Pack"] or "").strip().lower()
        unit_need = re.sub(r"[0-9.\s]", "", r["Need"] or "")
        # Buy >= Need only when Need and Buy count the same unit (pieces; a pack of n counts n)
        if need is not None and buy is not None and unit_need == "":
            if re.fullmatch(r"\d+", pack) and float(pack) > 1 and buy < float(pack):
                cap = buy * float(pack)
            elif re.fullmatch(r"(\d+) pairs?", pack):
                cap = buy * float(re.match(r"\d+", pack).group(0))
            elif pack in ("kit",):
                cap = None
            else:
                cap = buy
            if cap is not None:
                n_chk += 1
                if cap < need:
                    R2.find("FAIL", "line %s %s: buys %g but needs %g" % (lid, r["Item"], cap, need),
                            fix="raise Buy on BOM.md line %s" % lid, where="altaay_lab/BOM.md")
    R2.ev("Buy >= Need checked on %d countable lines (Need and Buy in the same unit)" % n_chk)
R2.write()

# ------------------------------------------------------------------------------------------- E3 json
R3 = V.Result("E3", "bom.json rebuilt from BOM.md (audit/bom_md_to_json.py on a copy)",
              "VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py",
              "bom.json has the same rows and values as BOM.md (57 purchase lines)", "BOM.md content itself")
R3.inp(V.lab("BOM.md"), V.lab("bom.json"), V.lab("audit", "bom_md_to_json.py"))
p = subprocess.run([sys.executable, "-I", os.path.join(OUT, "audit", "bom_md_to_json.py")], cwd=OUT, capture_output=True,
                   text=True, timeout=120)
if p.returncode != 0:
    R3.not_run("bom_md_to_json.py failed: " + (p.stdout + p.stderr)[-300:])
else:
    a = json.load(open(V.lab("bom.json")))
    b = json.load(open(os.path.join(OUT, "bom.json")))
    R3.ev("bom_md_to_json.py: %s; committed bom.json %d rows, rebuilt %d rows" % (p.stdout.splitlines()[0], len(a), len(b)))
    R3.key("%d rows rebuilt, identical to the committed bom.json: %s" % (len(b), a == b))
    if a == b:
        R3.ev("rebuilt bom.json is identical to the committed one")
    else:
        da = {r["i"]: r for r in a}
        db = {r["i"]: r for r in b}
        diff = sorted(set(da) ^ set(db)) + [k for k in da if k in db and da[k] != db[k]]
        R3.find("FAIL", "committed bom.json differs from BOM.md on lines %s" % diff[:12],
                fix="run python3 altaay_lab/audit/bom_md_to_json.py and commit bom.json", where="altaay_lab/bom.json")
R3.write()
