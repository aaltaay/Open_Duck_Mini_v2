"""C10: the wiring sheets (altaay_lab/wiring/sheets, sheets agent) cover every wire of the netlist.

Runs a copy of the sheets generator in the results folder (it writes its SVG and PNG next to itself, so it is never
run in the repo), then, in the same copy, builds the sheets again without saving and lists every active netlist wire
that no sheet draws in full, and every active cable missing from the harness sheet. Also checks that the committed
sheets are not older than netlist.yaml.
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c10_sheets.py
"""
import glob
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

DRIVER = r'''
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
import make_sheets as M
import sheetlib as L
book = M.Book()
book.n_sheets = len(M.BUILDERS)
book.complete = True
for p in (1, 2):
    book.pass_no = p
    sheets = M.build(book)
    if p == 1:
        for s in sheets:
            book.terms[s.no] = {k: (v["x"], v["y"]) for k, v in s.T.items()}
            for r in s.routes:
                if r["kind"] == "full" and s.no not in book.full[r["w"]["n"]]:
                    book.full[r["w"]["n"]].append(s.no)
            L.plt.close(s.fig)
out = dict(sheets=[], full={}, stub={}, cables={})
for s in sheets:
    out["sheets"].append(dict(no=s.no, key=s.key, n_full=getattr(s, "n_full", None), n_stub=getattr(s, "n_stub", None),
                              warn=len(getattr(s, "warn", []))))
    for r in s.routes:
        w = r["w"]
        k = "%s|%s|%s" % (w["cable"], w["from"], w["to"])
        out["full" if r["kind"] == "full" else "stub"].setdefault(k, []).append(s.no)
    for c in getattr(s, "cables_drawn", []) or []:
        out["cables"].setdefault(c, []).append(s.no)
json.dump(out, open(sys.argv[2], "w"))
'''


def main():
    R = V.Result("C10", "Wiring sheets cover every wire of the netlist (wiring/sheets, run on a copy)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c10_sheets.py",
                 "Every active netlist wire drawn in full on a sheet (every sheet but the harness), every active cable on the harness sheet "
                 "(sheet 5), the generator's own stop rules, committed sheets newer than netlist.yaml",
                 "Whether a drawing is easy to read; label placement (the generator prints layout warnings)")
    src = V.lab("wiring", "sheets")
    if not os.path.exists(os.path.join(src, "make_sheets.py")):
        R.not_run("altaay_lab/wiring/sheets/make_sheets.py not found (sheets agent output not landed)")
        R.write()
        return
    R.inp(os.path.join(src, "make_sheets.py"), os.path.join(src, "sheetlib.py"), V.lab("wiring", "netlist.yaml"))
    cp = os.path.join(V.out_dir(), "c10_sheets", "wiring", "sheets")
    shutil.rmtree(os.path.dirname(os.path.dirname(cp)), ignore_errors=True)
    os.makedirs(cp)
    for f in glob.glob(os.path.join(src, "*.py")):
        shutil.copy(f, cp)
    env = dict(os.environ, ODM_NETLIST=V.lab("wiring", "netlist.yaml"), MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(["nice", "-n", "10", sys.executable, "-B", os.path.join(cp, "make_sheets.py")], cwd=cp, env=env,
                       capture_output=True, text=True, timeout=1800)
    log = p.stdout + p.stderr
    open(os.path.join(V.out_dir(), "c10_make_sheets.txt"), "w").write(log)
    lines = [ln for ln in log.splitlines() if ln.startswith("sheet ")]
    R.ev("make_sheets.py on a copy: exit %d; %s" % (p.returncode, "; ".join(lines) or log[-300:]))
    if p.returncode != 0:
        R.find("FAIL", "the sheets generator stops: %s" % log.strip().splitlines()[-1][:300] if log.strip() else "no output",
               fix="see the sheets agent's coverage rule (make_sheets.py docstring)", where="altaay_lab/wiring/sheets")
    drv = os.path.join(V.out_dir(), "c10_driver.py")
    open(drv, "w").write(DRIVER)
    js = os.path.join(V.out_dir(), "c10_cover.json")
    q = subprocess.run(["nice", "-n", "10", sys.executable, "-B", drv, os.path.join(cp, "make_sheets.py"), js], cwd=cp, env=env,
                       capture_output=True, text=True, timeout=1800)
    if q.returncode != 0 or not os.path.exists(js):
        R.find("WARN", "coverage pass could not read the sheets' routes: %s" % (q.stdout + q.stderr)[-300:])
    else:
        cov = json.load(open(js))
        net = V.load_netlist()
        active = {cb["id"] for cb in net["cables"] if cb.get("status", "active") == "active"}
        wires = ["%s|%s|%s" % (w["cable"], w["from"], w["to"]) for w in net["wires"] if w["cable"] in active]
        full = {k for k, v in cov["full"].items() if any(n != 5 for n in v)}   # every sheet but the harness overview (5)
        miss = [w for w in wires if w not in full]
        nos = sorted(s["no"] for s in cov["sheets"])
        R.ev("sheets built: %s; active wires drawn in full: %d of %d" % (", ".join("%d %s (full %s, stubs %s)" % (
            s["no"], s["key"], s["n_full"], s["n_stub"]) for s in cov["sheets"]), len(wires) - len(miss), len(wires)))
        R.key("%d of %d active wires drawn in full on sheets %s; harness sheet 5: %s" % (len(wires) - len(miss), len(wires),
                                                                                    ", ".join(str(n) for n in nos), 5 in nos))
        if miss:
            cabs = sorted({m.split("|")[0] for m in miss}, key=lambda c: (c[0], int("".join(ch for ch in c if ch.isdigit()) or 0)))
            R.find("FAIL", "%d of %d active wires are not drawn in full on any sheet (cables %s)" % (len(miss), len(wires), ", ".join(cabs)),
                   fix="draw them (sheets 4 and 5 are not built yet)" if max(nos or [0]) < 5 else "draw them",
                   where="altaay_lab/wiring/sheets")
        if 5 not in nos:
            R.find("FAIL", "no harness sheet (sheet 5) yet: cable routes by region are not drawn", where="altaay_lab/wiring/sheets")
    # committed sheets vs netlist time
    net_t = os.path.getmtime(V.lab("wiring", "netlist.yaml"))
    # sheet 7 (the dock) is drawn from twin/dock/dock_netlist.yaml by make_dock_sheet.py, not from netlist.yaml
    dock_t = os.path.getmtime(V.lab("twin", "dock", "dock_netlist.yaml"))
    old = [os.path.basename(f) for f in glob.glob(os.path.join(src, "*.svg"))
           if os.path.getmtime(f) < (dock_t if os.path.basename(f).startswith("7_") else net_t)]
    R.ev("committed sheet SVGs: %d, older than netlist.yaml: %s" % (len(glob.glob(os.path.join(src, "*.svg"))), old or "none"))
    for o in old:
        R.find("FAIL", "%s is older than its netlist" % o, fix="re-run wiring/sheets/make_sheets.py (sheet 7: make_dock_sheet.py)", where="altaay_lab/wiring/sheets")
    R.write()


if __name__ == "__main__":
    main()
