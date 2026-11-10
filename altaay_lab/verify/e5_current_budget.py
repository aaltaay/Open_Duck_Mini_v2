"""E5: re-run sim/current_budget.py (MuJoCo walk of the stock policy, sim pass only) and compare every number in the
sim/CURRENT_BUDGET.md result table with the fresh run. Saves the traces for E6 (power path) and C7 (wire currents).

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e5_current_budget.py
Runs under nice -n 10 (shared machine). Needs ODM_PLAYGROUND (Open_Duck_Playground at b9be205).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E5", "Servo current budget from the stock walk (sim/current_budget.py, sim pass only)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e5_current_budget.py",
             "7 MuJoCo cases (stand, walk, turn, side, backlash, rough, pushes) with BEST_WALK_ONNX_2; every number of the "
             "CURRENT_BUDGET.md table (falls, mean, 1 s, 100 ms, 20 ms, 2 ms, whole-run max) and the worst single servo",
             "Real servos (issue 48: real tracking differs); the 5 V branch and pack side (hand calculation in the doc)")
od = os.path.join(V.out_dir(), "e5_current")
os.makedirs(od, exist_ok=True)
onnx = os.path.join(V.REPO, "BEST_WALK_ONNX_2.onnx")
R.inp(V.lab("sim", "current_budget.py"), V.lab("sim", "CURRENT_BUDGET.md"), onnx)
if not os.path.isdir(os.path.join(V.PLAYGROUND, "playground", "open_duck_mini_v2")):
    R.not_run("Open_Duck_Playground not found at %s (set ODM_PLAYGROUND)" % V.PLAYGROUND)
    R.write()
    sys.exit(0)
js = os.path.join(od, "current_budget.json")
if os.environ.get("VERIFY_REUSE") == "1" and os.path.exists(js):
    R.ev("reused <out>/%s from an earlier run in this output folder (VERIFY_REUSE=1)" % os.path.relpath(js, V.out_dir()))
else:
    env = dict(os.environ, ODM_PLAYGROUND=V.PLAYGROUND, ODM_ONNX=onnx, ODM_OUT=od, ODM_SAVE_TRACES="1")
    p = subprocess.run(["nice", "-n", "10", sys.executable, V.lab("sim", "current_budget.py")], env=env,
                       capture_output=True, text=True, timeout=7200)
    open(os.path.join(od, "stdout.txt"), "w").write(p.stdout + p.stderr)
    if p.returncode != 0 or not os.path.exists(js):
        R.not_run("current_budget.py failed (exit %d): %s" % (p.returncode, (p.stdout + p.stderr)[-400:]))
        R.write()
        sys.exit(0)
res = {r["label"]: r for r in json.load(open(js))}
KT = "1.148"
DOC = {"stand_in_place": "Stand, zero command", "walk_forward_0.15": "Walk forward 0.15 m/s", "turn_1.0": "Turn 1.0 rad/s",
       "walk_side_0.2": "Walk sideways 0.2 m/s", "walk_backlash": "Walk forward, backlash model",
       "walk_rough_backlash": "Walk forward, rough terrain, backlash model", "walk_pushes": "Walk forward with pushes"}
tab = [t for t in V.md_tables(V.lab("sim", "CURRENT_BUDGET.md")) if t["header"][:3] == ["Case", "Falls", "Mean"]]
if not tab:
    R.find("FAIL", "result table not found in sim/CURRENT_BUDGET.md")
    R.write()
    sys.exit(0)
doc = {r["Case"]: r for r in tab[0]["rows"]}
cols = [("Mean", lambda k, s: k["bus_A_mean"]), ("Max 1 s avg", lambda k, s: k["bus_A_max_window"]["1s"]),
        ("Max 100 ms avg", lambda k, s: k["bus_A_max_window"]["100ms"]), ("Max 20 ms avg", lambda k, s: k["bus_A_max_window"]["20ms"]),
        ("Max 2 ms", lambda k, s: k["bus_A_max_window"]["raw_2ms"]), ("Whole run max", lambda k, s: s["bus_A_max_including_start"][KT])]
worst = 0.0
for lab_, name in DOC.items():
    if lab_ not in res or name not in doc:
        R.find("FAIL", "case %s missing (%s)" % (lab_, "run" if lab_ not in res else "doc"))
        continue
    s, k, d = res[lab_], res[lab_]["per_kt"][KT], doc[name]
    falls = "none" if not s["falls"] else ", ".join("%.2f s" % f for f in s["falls"])
    diffs = []
    for col, fn in cols:
        a, b = fn(k, s), V.num(d[col])
        if b is None or abs(a - b) > max(0.02, 0.02 * abs(b)):
            diffs.append("%s doc %s run %.2f" % (col, d[col], a))
    doc_falls = d["Falls"]
    fall_ok = (doc_falls == "none") == (not s["falls"])
    R.ev("%s: falls %s; mean %.2f, 100 ms %.2f, 20 ms %.2f, 2 ms %.2f A%s" % (
        name, falls, k["bus_A_mean"], k["bus_A_max_window"]["100ms"], k["bus_A_max_window"]["20ms"],
        k["bus_A_max_window"]["raw_2ms"], "" if not diffs else " (differs: " + "; ".join(diffs) + ")"))
    if diffs or not fall_ok:
        R.find("FAIL", "%s: fresh run differs from CURRENT_BUDGET.md: %s%s" % (name, "; ".join(diffs),
               "" if fall_ok else "; falls doc '%s' run '%s'" % (doc_falls, falls)),
               fix="re-run sim/current_budget.py and update the table in sim/CURRENT_BUDGET.md", where="altaay_lab/sim/CURRENT_BUDGET.md")
    if lab_ != "stand_in_place":
        worst = max(worst, max(k["servo_A_max"].values()))
bk = res["walk_backlash"]["per_kt"][KT]
R.key("%d of %d cases reproduce CURRENT_BUDGET.md; backlash walk %.2f A mean, %.2f A worst 100 ms; worst servo %.2f A" % (
    len(DOC) - len([f for f in R.d["findings"] if f["sev"] == "FAIL"]), len(DOC), bk["bus_A_mean"], bk["bus_A_max_window"]["100ms"],
    max(bk["servo_A_max"].values())))
j = max(bk["servo_A_max"], key=bk["servo_A_max"].get)
jr = max(bk["servo_A_rms"], key=bk["servo_A_rms"].get)
R.ev("worst single servo, backlash walk: %s %.2f A peak; highest RMS %s %.2f A (doc: 3.35 A peak knee, 1.45 A RMS)" % (
    j, bk["servo_A_max"][j], jr, bk["servo_A_rms"][jr]))
if abs(bk["servo_A_max"][j] - 3.35) > 0.07 or abs(bk["servo_A_rms"][jr] - 1.45) > 0.03 or "knee" not in j:
    R.find("FAIL", "worst single servo differs from the doc (3.35 A peak knee, 1.45 A RMS)",
           fix="update sim/CURRENT_BUDGET.md", where="altaay_lab/sim/CURRENT_BUDGET.md")
R.write()
