"""E6: re-run sim/power_path_sim.py (ngspice, sim pass only) for the wiring that is built (D15 "star": servo power from
the BEC splices, one power lead per chain), on the traces E5 saved, and compare with the documented result (D15 and
the lead's re-run: worst ankle 5.04 V, typical corner, nominal pack). Then evaluate the TEST_PLAN.md section 9 gates
on the sim and re-run the two nominal cases with the power leads at the gauge the netlist builds (22 AWG; the sim
script models 20 AWG for the star leads).

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e6_power_path.py   (after e5_current_budget.py)
"""
import json
import os
import subprocess
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E6", "Power path to every servo, built wiring D15 (sim/power_path_sim.py star, ngspice, sim pass only)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py",
             "7 star cases (full, nominal, low pack x typical and high-side resistance, fall after a push); documented worst "
             "ankle 5.04 V; TEST_PLAN.md section 9 gates on the sim; the same run with 22 AWG power leads as in the netlist",
             "Real hop resistance (TEST_PLAN.md section 5), BEC dropout (section 4), bus capacitance; the 5 V branch in detail")
od = os.path.join(V.out_dir(), "e6_power")
tr = os.path.join(V.out_dir(), "e5_current")
os.makedirs(od, exist_ok=True)
R.inp(V.lab("sim", "power_path_sim.py"), V.lab("sim", "POWER_PATH_SIM.md"), V.lab("wiring", "netlist.yaml"))
need = [os.path.join(tr, "trace_walk_backlash.npz"), os.path.join(tr, "trace_walk_pushes.npz")]
if not all(os.path.exists(p) for p in need):
    R.not_run("traces from E5 not found in %s (run e5_current_budget.py first)" % tr)
    R.write()
    sys.exit(0)
js = os.path.join(od, "power_path_sim.json")
env = dict(os.environ, ODM_TRACES=tr, ODM_OUT=od, ODM_TOPOS="star")
if not (os.environ.get("VERIFY_REUSE") == "1" and os.path.exists(js)):
    p = subprocess.run(["nice", "-n", "10", sys.executable, V.lab("sim", "power_path_sim.py")], env=env,
                       capture_output=True, text=True, timeout=7200)
    open(os.path.join(od, "stdout.txt"), "w").write(p.stdout + p.stderr)
    if p.returncode != 0 or not os.path.exists(js):
        R.not_run("power_path_sim.py failed (exit %d): %s" % (p.returncode, (p.stdout + p.stderr)[-400:]))
        R.write()
        sys.exit(0)
cases = {c["label"]: c for c in json.load(open(js))["cases"]}
ANK = ("left_ankle", "right_ankle")
for lab_, c in cases.items():
    a6 = max(c["servo_ms_below_6V"][a] for a in ANK) / c["window_ms"] * 100.0
    w45 = max(c["servo_ms_below_4V5"].values())
    R.ev("%s: worst %s %.2f V min; pack %.1f A mean, %.1f A max; BEC out %.1f A max; ankles under 6 V %.0f%% of the time; "
         "longest time of any servo under 4.5 V %.0f ms" % (lab_.replace("star: ", ""), c["worst_servo"], c["worst_servo_V_min"],
                                                          c["pack_A_mean"], c["pack_A_max"], c["bec_out_A_max"], a6, w45))
key = "star: walk, backlash, pack nominal, typical R"
if key not in cases:
    R.find("FAIL", "case '%s' missing" % key)
else:
    c = cases[key]
    if abs(c["worst_servo_V_min"] - 5.04) > 0.02 or c["worst_servo"] not in ANK:
        R.find("FAIL", "documented worst ankle 5.04 V (typical, nominal) not reproduced: %s %.3f V" % (c["worst_servo"], c["worst_servo_V_min"]),
               fix="re-run sim/power_path_sim.py and update D15 and sim/POWER_PATH_SIM.md", where="altaay_lab/DECISIONS.md D15")
    else:
        R.ev("documented result reproduced: worst %s %.3f V (D15: 5.04 V)" % (c["worst_servo"], c["worst_servo_V_min"]))
        hs = cases.get("star: walk, backlash, pack nominal, high-side R")
        R.key("worst ankle %.2f V at a nominal pack, typical corner (D15: 5.04 V), %.2f V high-side; ankle under 6 V %.0f%% of the "
              "walk (typical)" % (c["worst_servo_V_min"], hs["worst_servo_V_min"] if hs else float("nan"),
                                   max(c["servo_ms_below_6V"][a] for a in ANK) / c["window_ms"] * 100.0))
    # TEST_PLAN.md section 9 gates, applied to the sim at a nominal pack
    for lab_ in (key, "star: walk, backlash, pack nominal, high-side R"):
        c = cases.get(lab_)
        if not c:
            continue
        a6 = max(c["servo_ms_below_6V"][a] for a in ANK) / c["window_ms"] * 100.0
        low = {k: v for k, v in c["servo_V_min"].items() if v < 4.5}
        corner = "typical" if "typical" in lab_ else "high-side"
        if a6 > 10.0:
            R.find("WARN", "sim, %s corner, nominal pack: an ankle is under 6.0 V for %.0f%% of the walk; TEST_PLAN.md section 9 "
                   "passes only under 10%%" % (corner, a6),
                   fix="known (POWER_PATH_SIM.md item 4, D15 follow-up): measure the hop resistance first (TEST_PLAN.md section 5); "
                       "if over 40 mOhm, 22 AWG made leg leads (BOM contingency X1/X2)")
        if low:
            R.find("WARN", "sim, %s corner, nominal pack: %s under 4.5 V (TEST_PLAN.md section 9 fails on any servo under 4.5 V)" % (
                corner, ", ".join("%s %.2f V" % kv for kv in sorted(low.items(), key=lambda kv: kv[1]))),
                fix="same gate as above; the high-side corner is the reason the hop resistance is measured before assembly")
    if "star" not in open(V.lab("sim", "POWER_PATH_SIM.md")).read().lower():
        R.find("WARN", "sim/POWER_PATH_SIM.md has no row for the star wiring that is built (D15); its tables show only the "
               "Tnkr and Y-lead wirings", fix="add the star rows (this run, or the lead's) to the results table in "
               "sim/POWER_PATH_SIM.md", where="altaay_lab/sim/POWER_PATH_SIM.md")

# the same model with the star power leads at 22 AWG, as wiring/netlist.yaml builds SP1 to SP3
src = open(V.lab("sim", "power_path_sim.py")).read()
old = 'bL = wire(20, 150) + p["R_contact"]; bN = wire(20, 180) + p["R_contact"]'
net = V.load_netlist()
spg = sorted({w["gauge"] for w in net["wires"] if w["cable"] in ("SP1", "SP2", "SP3")})
R.ev("netlist SP1 to SP3 gauge: %s; sim star leads: %s" % (spg, "20 AWG" if old in src else "not found"))
if old in src and spg == ["22 AWG"]:
    R.find("WARN", "sim/power_path_sim.py models the D15 power leads as 20 AWG; netlist.yaml, WIRING.md and D15 build them in 22 AWG",
           fix="in sim/power_path_sim.py build(): use wire(22, 150) and wire(22, 180) for bL and bN (and fix the comment on "
               "topology 'star'), then re-run", where="altaay_lab/sim/power_path_sim.py")
    mod = types.ModuleType("pps22")
    os.environ.update(ODM_TRACES=tr, ODM_OUT=os.path.join(od, "awg22"))
    exec(compile(src.replace(old, old.replace("wire(20,", "wire(22,")), "power_path_sim_22awg", "exec"), mod.__dict__)
    TYP = dict(R_contact=0.005, kit_awg=24, R_cell=0.015, R_holder=0.010, R_adapter=0.005)
    wb = need[0]
    for corner, over in (("typical", dict(TYP, topology="star")), ("high-side", dict(topology="star"))):
        c22 = mod.run_case("star 22 AWG: walk, backlash, pack nominal, %s R" % corner, wb, 10.0, 16.0, 3.7, over=over)
        c20 = cases.get("star: walk, backlash, pack nominal, %s R" % corner)
        a6 = max(c22["servo_ms_below_6V"][a] for a in ANK) / c22["window_ms"] * 100.0
        R.ev("22 AWG leads, nominal, %s: worst %s %.3f V (20 AWG: %.3f V); ankles under 6 V %.0f%%" % (
            corner, c22["worst_servo"], c22["worst_servo_V_min"], c20["worst_servo_V_min"] if c20 else float("nan"), a6))
R.write()
