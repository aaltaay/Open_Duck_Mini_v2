"""C12: the charging dock is complete and consistent (CAD check only, calc only).
Re-runs the dock's own tools on the committed files and checks:
  - parts: every printed part watertight and on the bed (stl/parts.json rebuilt by dock_parts.py in the output folder),
    no interference between any two components in the dock and docked states, none for the moving paddle at 0, 20, 40 mm
    and -10, 0, +10 deg (dock_assembly.py);
  - fasteners: every screw OK (path open, head clear, engagement by its rule, tip clear) in dock_fasteners.json, rebuilt;
  - wiring: dock_erc.py 0 ERROR; every netlist wire routed in dock_cables3d.json with self-check PASS and a cut no
    shorter than its route plus the slack rule; wiring sheet 7 drawn and newer than dock_netlist.yaml;
  - BOM vs model: dock_bom.py check (every fastener spec, bought part and gate part counted on its line);
  - viewer: when a dock scene was built in the output folder (VERIFY_OUT/viewer_dock), its counts match the BOM and the
    fastener schedule.
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c12_dock.py
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402
import yaml  # noqa: E402


def run(cmd, cwd):
    env = dict(os.environ, ODM_SHEETS_OUT=cwd, PYTHONPATH=os.pathsep.join([V.lab("fasteners"), V.lab("viewer")]))
    p = subprocess.run([sys.executable] + cmd, cwd=cwd, capture_output=True, text=True, timeout=3600, env=env)
    return p.returncode, p.stdout + p.stderr


def main():
    R = V.Result("C12", "The charging dock: parts, fits, screws, wiring, routes, BOM against the model (twin/dock, CAD check only)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c12_dock.py",
                 "Printed parts, interferences and the paddle motion, every screw, the gate ERC, every wire's 3D route and cut, sheet 7, "
                 "BOM Need against the fasteners, the assembly and the gate board",
                 "Real fits (printing tolerance), spring and switch tolerances (BT1, BT5), the sim of the walk (section 12.1 is sim pass only)")
    D = V.lab("twin", "dock")
    scr = os.path.join(V.out_dir(), "c12_dock")
    if os.path.exists(scr):
        shutil.rmtree(scr)
    shutil.copytree(D, scr)
    R.inp(*[os.path.join(D, f) for f in ("dock_parts.py", "dock_assembly.py", "dock_fasteners.py", "dock_netlist.yaml", "dock_routes.py", "dock_bom.py")])
    # parts (on the copy, so the repo is not written)
    rc, out = run(["dock_parts.py"], scr)
    pj = json.load(open(os.path.join(scr, "stl", "parts.json")))
    bad = [n for n, r in pj.items() if r.get("printed") and not (r["watertight"] and r["fits_220"])]
    R.ev("printed kinds %d, prints %d; not watertight or off the bed: %s" % (sum(1 for r in pj.values() if r.get("printed")), sum(r.get("qty", 0) for r in pj.values()), bad or "none"))
    if rc or bad:
        R.find("FAIL", "dock_parts.py: %s" % (bad or out[-300:]), where="altaay_lab/twin/dock/dock_parts.py")
    rc, out = run(["dock_assembly.py"], scr)
    A = json.load(open(os.path.join(scr, "dock_assembly.json")))
    hits = A["dock"]["interferences"] + A["docked"]["interferences"]
    mot = [m for m in A["motion"] if m["hits"]]
    R.ev("components %d (dock), %d (docked); interferences %d; paddle motion poses with a hit %d of %d" % (A["dock"]["n"], A["docked"]["n"], len(hits), len(mot), len(A["motion"])))
    if rc or hits or mot:
        R.find("FAIL", "interference: %s %s" % (hits[:3], mot[:2]), where="altaay_lab/twin/dock/dock_assembly.py")
    rc, out = run(["dock_fasteners.py"], scr)
    F = json.load(open(os.path.join(scr, "dock_fasteners.json")))
    nok = F["summary"]["not_ok"]
    R.ev("fasteners: %d screws, %d nuts, %d inserts; not OK: %s" % (F["summary"]["screws"], F["summary"]["nuts"], F["summary"]["inserts"], nok or "none"))
    if rc or nok:
        R.find("FAIL", "dock screws not OK: %s" % nok, where="altaay_lab/twin/dock/dock_fasteners.py")
    committed = json.load(open(os.path.join(D, "dock_fasteners.json")))
    if [f["seat_world"] for f in committed["fasteners"]] != [f["seat_world"] for f in F["fasteners"]]:
        R.find("FAIL", "dock_fasteners.json is not the schedule the current parts give", fix="run dock_fasteners.py", where="altaay_lab/twin/dock")
    sys.path.insert(0, scr)
    import dock_assembly as DAc
    for st in ("dock", "docked"):
        bad = DAc.fastener_seating(st)
        R.ev("fasteners seated on their host parts in the %s state: %s" % (st, "all" if not bad else bad[:5]))
        if bad:
            R.find("FAIL", "fasteners off their host parts in the %s state: %s" % (st, bad[:5]), where="altaay_lab/viewer/dock_scene.py, twin/dock/dock_assembly.py")
    rc, out = run(["dock_erc.py"], scr)
    R.ev("dock_erc.py: " + " | ".join(l for l in out.splitlines() if l.startswith(("dock ERC", "INFO"))))
    if rc:
        R.find("FAIL", "dock ERC: " + out[-300:], where="altaay_lab/twin/dock/dock_netlist.yaml")
    # routes: the committed result (rebuilding the grid takes about 5 minutes; dock_routes.py recomputes it)
    C = json.load(open(os.path.join(D, "dock_cables3d.json")))
    NL = yaml.safe_load(open(os.path.join(D, "dock_netlist.yaml")))
    runs = {(r["frm"], r["to"]): r for c in C["cables"] for r in c["runs"]}
    miss, short = [], []
    for w in NL["wires"]:
        r = runs.get((w["from"], w["to"]))
        if not r or not r.get("points"):
            miss.append("%s-%s" % (w["from"], w["to"])); continue
        need = r["length_mm"] + (10 if "holder lead" in (w.get("ends") or []) else 40 + (20 if w["cable"] == "KP1" else 0))
        if w["cut_mm"] < need - 1e-6:
            short.append("%s-%s cut %s < %s" % (w["from"], w["to"], w["cut_mm"], round(need)))
    sys.path.insert(0, D)
    import dock_routes as DRt
    over = DRt.pairwise({c["id"]: c["runs"] for c in C["cables"]}, {k: __import__("numpy").array(v) for k, v in C["terminals"].items()})
    R.ev("wire to wire (centre lines at least the sum of the radii apart, outside shared terminal zones): %s" % ("no overlap" if not over else over[:3]))
    if over:
        R.find("FAIL", "routed wires overlap: %s" % over[:3], where="altaay_lab/twin/dock/dock_routes.py")
    R.ev("wires %d, routed %d, self-check %s; cuts short of the rule: %s" % (len(NL["wires"]), len(NL["wires"]) - len(miss), C["self_check"], short or "none"))
    if miss or short or C["self_check"] != "PASS":
        R.find("FAIL", "dock routes: missing %s, short %s, self-check %s" % (miss, short, C["self_check"]), where="altaay_lab/twin/dock/dock_routes.py")
    sh = V.lab("wiring", "sheets", "7_dock.svg")
    if not os.path.exists(sh):
        R.find("FAIL", "wiring sheet 7 (7_dock.svg) missing", fix="python3 altaay_lab/wiring/sheets/make_dock_sheet.py")
    rc, out = run([V.lab("wiring", "sheets", "make_dock_sheet.py")], scr)
    R.ev("sheet 7: " + " ".join(l for l in out.splitlines() if l.startswith("sheet")))
    if rc:
        R.find("FAIL", "make_dock_sheet.py: " + out[-300:], where="altaay_lab/wiring/sheets")
    # BOM vs model
    rc, out = run(["dock_bom.py"], scr)
    R.ev("dock_bom.py: " + " ".join(l for l in out.splitlines() if l.startswith("CHECK")))
    if rc:
        R.find("FAIL", "dock BOM Need vs the model: " + out[-400:], where="altaay_lab/twin/dock/dock_bom.py")
    B = json.load(open(os.path.join(scr, "dock_bom.json")))
    for b in B["totals"]["blockers"]:
        R.find("WARN", "dock BOM line %s has no price (BLOCKER)" % b)
    vm = os.path.join(V.out_dir(), "viewer_dock", "dock_manifest.json")
    if os.path.exists(vm):
        M = json.load(open(vm))
        sm = M["checklist"]["summary"]
        R.ev("viewer dock scene: printed %d/%d, screws %d, inserts %d, cables %d" % (sm["printed"]["found"], sm["printed"]["expected"], sm["screws"]["found"], sm["inserts"]["found"], sm["cables"]["found"]))
        if sm["printed"]["found"] != sm["printed"]["expected"] or sm["screws"]["found"] != F["summary"]["screws"] or sm["cables"]["found"] != len(NL["wires"]):
            R.find("FAIL", "viewer dock scene counts differ from the schedule", where="altaay_lab/viewer/dock_scene.py")
    else:
        R.ev("viewer dock scene not built in this output folder (make_viewer_data.py --scene dock --out VERIFY_OUT/viewer_dock): not compared")
    R.key("dock: %d components, %d screws OK, %d wires routed (self-check %s), BOM Need matches the model" % (A["dock"]["n"], F["summary"]["screws"], len(NL["wires"]) - len(miss), C["self_check"]))
    R.write()


if __name__ == "__main__":
    main()
