"""E6: the power path to every servo as the robot is wired now (sim pass only): D15 star (BEC -> P11 -> belly splices ->
SP1, SP2, SP3) plus the D23 second feeds SP4 and SP5 into BUS 1 of the ankle servos, with every length and gauge read
from wiring/netlist.yaml (sim/power_path_sim.py topology "as_built", which runs sim/power_fix.py option "ab", the
option 3b network with the netlist values and the D15 data-lead grounds).

Runs both resistance corners (typical, high-side) at the full, nominal and low pack, plus the fall after a push, on the
E5 traces (trained mass), and the walking cases again on our build's traces (C8, sim/added_mass_sim.py at the
sim/MASS_BUDGET.md mass) when C8 has run in the same output folder. Then:
  - the model covers every active netlist cable on the servo power path (a new power cable would be missed otherwise);
  - TEST_PLAN.md section 9 gates, read from that section: no servo under 4.5 V at any time (full and nominal pack), no
    ankle under 6.0 V for more than 10 % of the walking time at nominal, counted in time (ngspice time steps weighted
    by their length, not 50 Hz samples locked to the control loop; the 50 Hz phase range is shown next to it).
    The worse of the two traces counts. A gate missed in the typical corner is a FAIL (the wiring misses its own gate
    with the expected resistances); missed only in the high-side corner it is a WARN (TEST_PLAN 3.2, 4.1 and 5 are
    the bench gates that keep the robot out of that corner);
  - the lowest servo of each chain is named: with SP4/SP5 the leg's low point moves from the ankle to the knee, and the
    neck chain has no second feed, so a gate that names only the ankles no longer watches the lowest servo (WARN);
  - the as-built table in sim/POWER_PATH_SIM.md is reproduced (nominal pack, trained mass, both corners).
The earlier "star" topology (D15 as modelled at the decision: 20 AWG SP leads, no SP4/SP5) is history and not checked.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e6_power_path.py   (after e5_current_budget.py;
after c8_policy_mass.py as well to include our build)
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

ANK = ("left_ankle", "right_ankle")
GROUPS = (("left leg", lambda n: n.startswith("left_")), ("right leg", lambda n: n.startswith("right_")),
          ("neck and head", lambda n: not (n.startswith("left_") or n.startswith("right_"))))
# active netlist cables on the servo power path that the as_built model reads (sim/power_path_sim.py netlist_lengths)
MODEL_CABLES = {"P1", "P2", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "SP1", "SP2", "SP3", "SP4", "SP5",
                "SD1", "SD2", "S2", "S3", "S4", "S5", "S7", "S8", "S9", "S10", "S11", "S12", "S13"}
POWER_NETS = ("SERVO_7V2", "VSW", "PACK_P", "PACK_F", "CELL_N")
NOT_SERVO_PATH = {"P3": "BMS cell sense only", "P4": "charger, carries current only while charging", "P5": "charger",
                  "P15": "2815 control switch, under 0.1 mA", "P16": "2815 control ground, under 1 mA",
                  "P17": "5 V from the Pi header to the head devices (5 V branch after the regulator)"}


def gates_from_test_plan():
    """section 9 pass line: (V never, dip V, dip %, counted in time, scope 'ankle' or 'servo'), or None when not found"""
    tp = open(V.lab("TEST_PLAN.md"), encoding="utf-8").read()
    sec = re.search(r"^## 9\..*?(?=^## )", tp, re.M | re.S)
    s = sec.group(0) if sec else ""
    a = re.search(r"no servo under ([0-9.]+) V at any time", s)
    b = re.search(r"no (ankle|servo) under ([0-9.]+) V for more than ([0-9.]+) %", s)
    timed = "counted in time" in s
    return (float(a.group(1)), float(b.group(2)), float(b.group(3)), timed, b.group(1)) if a and b else None


def knees_timed():
    """TEST_PLAN.md section 9 also times the knees and the head roll (the bullet proposed with the as-built check)"""
    tp = open(V.lab("TEST_PLAN.md"), encoding="utf-8").read()
    sec = re.search(r"^## 9\..*?(?=^## )", tp, re.M | re.S)
    return bool(sec and re.search(r"time the knees and the head roll", sec.group(0)))


def run_sim(od, traces, env_extra):
    js = os.path.join(od, "power_path_sim.json")
    if not (os.environ.get("VERIFY_REUSE") == "1" and os.path.exists(js)):
        os.makedirs(od, exist_ok=True)
        env = dict(os.environ, ODM_TRACES=traces, ODM_OUT=od, ODM_TOPOS="as_built", PYTHONDONTWRITEBYTECODE="1", **env_extra)
        p = subprocess.run(["nice", "-n", "10", sys.executable, V.lab("sim", "power_path_sim.py")], env=env,
                           capture_output=True, text=True, timeout=7200)
        open(os.path.join(od, "stdout.txt"), "w").write(p.stdout + p.stderr)
        if p.returncode != 0 or not os.path.exists(js):
            return None, "power_path_sim.py failed (exit %d): %s" % (p.returncode, (p.stdout + p.stderr)[-600:])
    return json.load(open(js)), None


def group_line(c):
    out = []
    for g, f in GROUPS:
        ks = [k for k in c["servo_V_min"] if f(k)]
        lo = min(ks, key=lambda k: c["servo_V_min"][k])
        hi = max(ks, key=lambda k: c["servo_pct_below_6V"][k])
        out.append("%s: lowest %s %.2f V, most time under 6 V %s %.1f %%" % (g, lo.replace("_", " "), c["servo_V_min"][lo],
                                                                              hi.replace("_", " "), c["servo_pct_below_6V"][hi]))
    return "; ".join(out)


def doc_rows():
    """as-built table rows of sim/POWER_PATH_SIM.md keyed by (pack and corner, trace)"""
    rows = {}
    for t in V.md_tables(V.lab("sim", "POWER_PATH_SIM.md")):
        if t["header"][:2] == ["Pack, corner", "Trace"]:
            for r in t["rows"]:
                rows[(r["Pack, corner"], r["Trace"])] = r
    return rows


def main():
    R = V.Result("E6", "Power path to every servo as wired now: D15 star plus the D23 ankle feeds SP4 and SP5, lengths and gauges "
                 "from wiring/netlist.yaml (sim/power_path_sim.py as_built, ngspice, sim pass only)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py",
                 "As-built network (P1 to P14 pack side, BEC, P11, SP1 to SP5, 11 kit hops, data-lead grounds) read from the "
                 "netlist; full, nominal and low pack x typical and high-side resistances, fall after a push; trained mass (E5) "
                 "and our build (C8); TEST_PLAN.md section 9 gates counted in time; lowest servo per chain; the as-built table "
                 "of POWER_PATH_SIM.md reproduced",
                 "Real hop and contact resistance (TEST_PLAN.md section 5), BEC dropout (section 4.1), bus capacitance, "
                 "regenerative braking, the servo electronics' brown-out point; the 5 V branch in detail")
    od = os.path.join(V.out_dir(), "e6_power")
    tr = os.path.join(V.out_dir(), "e5_current")
    ours = os.path.join(V.out_dir(), "c8_added_mass", "added_mass", "traces", "ours")
    R.inp(V.lab("sim", "power_path_sim.py"), V.lab("sim", "power_fix.py"), V.lab("sim", "POWER_PATH_SIM.md"),
          V.lab("wiring", "netlist.yaml"), V.lab("TEST_PLAN.md"))
    need = [os.path.join(tr, "trace_walk_backlash.npz"), os.path.join(tr, "trace_walk_pushes.npz")]
    if not all(os.path.exists(p) for p in need):
        R.not_run("traces from E5 not found in %s (run e5_current_budget.py first)" % tr)
        return R.write()
    runs = []
    d, err = run_sim(os.path.join(od, "trained"), tr, dict(ODM_TRACE_LABEL="trained mass (E5)"))
    if err:
        R.not_run(err)
        return R.write()
    runs.append(("trained mass (E5)", d))
    if os.path.exists(os.path.join(ours, "trace_walk_backlash.npz")):
        d2, err = run_sim(os.path.join(od, "ours"), ours, dict(ODM_FALL="0", ODM_TRACE_LABEL="our build (C8)"))
        if err:
            R.find("WARN", "our build's run failed: %s" % err)
        else:
            runs.append(("our build (C8)", d2))
    else:
        R.find("WARN", "our build's traces (C8) not found in this output folder: only the trained mass was run (our 2.65 kg build "
               "draws more current: about 0.15 A more pack RMS in the as-built sim)",
               fix="run c8_policy_mass.py before e6_power_path.py (verify/run_all.sh order)", where="altaay_lab/verify/run_all.sh")
    # ---------------------------------------------------------------- model inputs and coverage
    d = runs[0][1]
    R.ev("netlist read by the model: %s sha256 %s, modified %s" % (d["netlist"]["path"], d["netlist"]["sha256_10"], d["netlist"]["mtime_utc"]))
    R.ev("netlist values used: %s" % d["netlist_values"])
    net = V.load_netlist()
    act = {c["id"] for c in net["cables"] if c.get("status") == "active"}
    on_power = sorted({w["cable"] for w in net["wires"] if w["cable"] in act and w["net"] in POWER_NETS})
    missing = [c for c in on_power if c not in MODEL_CABLES and c not in NOT_SERVO_PATH]
    R.ev("active netlist cables on %s: %s; in the model: %d; outside the servo path: %s" % (
        "/".join(POWER_NETS), ", ".join(on_power), len([c for c in on_power if c in MODEL_CABLES]),
        ", ".join("%s (%s)" % (c, NOT_SERVO_PATH[c]) for c in on_power if c in NOT_SERVO_PATH)))
    gone = sorted(c for c in MODEL_CABLES if c not in act)
    if missing:
        R.find("FAIL", "active power cables in wiring/netlist.yaml that the as-built model does not contain: %s" % ", ".join(missing),
               fix="add them to sim/power_path_sim.py netlist_lengths() and sim/power_fix.py netlist_as_built(), then re-run",
               where="altaay_lab/sim/power_path_sim.py")
    if gone:
        R.find("FAIL", "cables the as-built model expects are not active in the netlist: %s" % ", ".join(gone),
               fix="re-check the netlist change, then update the model", where="altaay_lab/sim/power_path_sim.py")
    # ---------------------------------------------------------------- evidence per case
    for tn, dd in runs:
        for c in dd["cases"]:
            R.ev("%s, %s: lowest %s %.2f V; ankle under 6 V %.1f %% of the time (50 Hz samples, by phase: %.1f to %.1f %%); "
                 "any servo under 4.5 V %.0f ms; pack %.2f A mean, %.2f A RMS, %.1f A max; BEC out %.1f A max; complete %s; %s" % (
                     tn, c["label"].replace("as_built: ", ""), c["worst_servo"].replace("_", " "), c["worst_servo_V_min"],
                     c["ankle_pct_below_6V"], c["ankle_pct_below_6V_50Hz_best_phase"], c["ankle_pct_below_6V_50Hz_worst_phase"],
                     c["any_servo_ms_below_4V5"], c["pack_A_mean"], c["pack_A_rms"], c["pack_A_max"], c["bec_out_A_max"], c["complete"],
                     group_line(c)))
            if not c["complete"]:
                R.find("FAIL", "%s, %s: ngspice stopped at %.0f ms of %.0f ms" % (tn, c["label"], c["window_ms"],
                                                                                 1000 * (c["window_s"][1] - c["window_s"][0])),
                       fix="look at the ngspice output in VERIFY_OUT/e6_power", where="altaay_lab/sim/power_fix.py")
    # ---------------------------------------------------------------- TEST_PLAN.md section 9 gates
    g = gates_from_test_plan()
    if not g:
        R.find("WARN", "TEST_PLAN.md section 9: pass line not found ('no servo under X V at any time', 'no ankle under Y V for more "
               "than Z %'); the check used 4.5 V, 6.0 V and 10 %", fix="keep the pass line wording or update this check",
               where="altaay_lab/TEST_PLAN.md section 9")
        g = (4.5, 6.0, 10.0, False, "ankle")
    vmin_gate, ank_v, ank_pct, timed, scope = g
    metric = "ankle_pct_below_6V" if scope == "ankle" else "any_servo_pct_below_6V"
    who = "an ankle" if scope == "ankle" else "a servo"
    R.ev("TEST_PLAN.md section 9 gates: no servo under %.1f V at any time (full and nominal pack); no %s under %.1f V for more "
         "than %.0f %% of the walking time at nominal, counted in time: %s" % (vmin_gate, scope, ank_v, ank_pct, "as the plan says" if timed
                                                                              else "the plan does not say 'counted in time'"))
    if ank_v != 6.0:
        R.find("WARN", "TEST_PLAN.md section 9 ankle gate is %.1f V; the sim counts time under 6.0 V" % ank_v,
               fix="update this check and sim/power_fix.py run() to the new threshold")
    verdict = {}
    for corner in ("typical", "high-side"):
        rows = [(tn, c) for tn, dd in runs for c in dd["cases"] if c["label"].endswith("%s R" % corner) and "walk" in c["label"]]
        fullnom = [(tn, c) for tn, c in rows if ("pack full" in c["label"] or "pack nominal" in c["label"])]
        nom = [(tn, c) for tn, c in rows if "pack nominal" in c["label"]]
        lo = min(fullnom, key=lambda x: x[1]["worst_servo_V_min"])
        an = max(nom, key=lambda x: x[1][metric])
        verdict[corner] = dict(vmin=lo, ank=an)
        sev = "FAIL" if corner == "typical" else "WARN"
        fixtxt = ("the wiring misses TEST_PLAN 9 with the expected resistances: sim/POWER_FIX.md options (6+3b passes)"
                  if corner == "typical" else
                  "known: the high-side corner; the bench gates TEST_PLAN.md 3.2 (pack side), 4.1 (BEC dropout) and 5 (hop "
                  "resistance) keep the robot out of it; the 3S plan (sim/POWER_FIX.md option 6+3b, held by D23) passes it")
        R.ev("gate check, %s corner: lowest servo at full or nominal %s %.2f V (%s, %s); %s time under 6 V at nominal %.1f %% "
             "(%s; ankle minimum %.2f V)" % (corner, lo[1]["worst_servo"].replace("_", " "), lo[1]["worst_servo_V_min"], lo[0],
                                             lo[1]["label"].split("pack ")[1].split(",")[0], scope, an[1][metric], an[0],
                                             an[1]["ankle_V_min"]))
        if lo[1]["worst_servo_V_min"] < vmin_gate:
            R.find(sev, "sim, %s corner: %s %.2f V at a %s pack (%s), under the TEST_PLAN.md section 9 limit of %.1f V at any time" % (
                corner, lo[1]["worst_servo"].replace("_", " "), lo[1]["worst_servo_V_min"], lo[1]["label"].split("pack ")[1].split(",")[0],
                lo[0], vmin_gate), fix=fixtxt, where="altaay_lab/sim/POWER_FIX.md" if corner == "typical" else None)
        if an[1][metric] > ank_pct:
            R.find(sev, "sim, %s corner, nominal pack: %s is under 6.0 V for %.1f %% of the walk counted in time (%s; "
                   "for the ankles, 50 Hz samples locked to the control loop read %.1f to %.1f %% by phase); TEST_PLAN.md section 9 "
                   "passes only under %.0f %%" % (corner, who, an[1][metric], an[0], an[1]["ankle_pct_below_6V_50Hz_best_phase"],
                                                 an[1]["ankle_pct_below_6V_50Hz_worst_phase"], ank_pct),
                   fix=fixtxt, where="altaay_lab/sim/POWER_FIX.md" if corner == "typical" else None)
    # ---------------------------------------------------------------- the lowest servo is not an ankle any more
    lows = []
    for tn, dd in runs:
        for c in dd["cases"]:
            if "pack nominal" not in c["label"]:
                continue
            for gname, f in GROUPS[:2]:
                ks = [k for k in c["servo_V_min"] if f(k)]
                lo = min(ks, key=lambda k: c["servo_V_min"][k])
                worst6 = max(ks, key=lambda k: c["servo_pct_below_6V"][k])
                ank = [k for k in ks if k.endswith("ankle")][0]
                if lo != ank or worst6 != ank:
                    lows.append((tn, c["label"].split(", ")[-1], gname, lo, c["servo_V_min"][lo], worst6, c["servo_pct_below_6V"][worst6],
                                 c["servo_pct_below_6V"][ank]))
    if lows and scope == "ankle":
        typ = [x for x in lows if x[1].startswith("typical")]
        worst_typ = max(typ, key=lambda x: x[6]) if typ else max(lows, key=lambda x: x[6])
        neck = max(((tn, c) for tn, dd in runs for c in dd["cases"] if "pack nominal" in c["label"] and c["label"].endswith("typical R")),
                   key=lambda x: x[1]["servo_pct_below_6V"]["head_roll"])
        R.find("INFO" if knees_timed() else "WARN",
               "with SP4/SP5 the ankle is no longer the lowest leg servo: at a nominal pack the %s is (typical corner, %s: "
               "%s %.2f V minimum, %s %.1f %% of the time under 6.0 V, ankle %.1f %%); the neck chain has no second feed (head roll "
               "%.2f V, %.1f %% under 6.0 V, typical, %s). TEST_PLAN.md section 9 %s" % (
                   worst_typ[3].split("_", 1)[1], worst_typ[0], worst_typ[3].replace("_", " "), worst_typ[4],
                   worst_typ[5].replace("_", " "), worst_typ[6], worst_typ[7], neck[1]["servo_V_min"]["head_roll"],
                   neck[1]["servo_pct_below_6V"]["head_roll"], neck[0],
                   "times the knees and the head roll too" if knees_timed() else "times only the ankles"),
               fix="TEST_PLAN.md section 9: time every servo under 6.0 V (the log has all 14), and pass on the knees and the head roll "
                   "as on the ankles; sim/POWER_PATH_SIM.md 'As built' has the numbers", where="altaay_lab/TEST_PLAN.md section 9")
    # ---------------------------------------------------------------- documented as-built table reproduced
    rows = doc_rows()
    if not rows:
        R.find("FAIL", "sim/POWER_PATH_SIM.md has no as-built table (header 'Pack, corner | Trace | ...')",
               fix="write the as-built section from this run", where="altaay_lab/sim/POWER_PATH_SIM.md")
    else:
        for corner in ("typical", "high-side"):
            c = [x for x in runs[0][1]["cases"] if x["label"] == "as_built: walk, backlash, pack nominal, %s R" % corner][0]
            r = rows.get(("nominal (7.4 V), %s" % corner, "trained mass (E5)"))
            if not r:
                R.find("FAIL", "sim/POWER_PATH_SIM.md as-built table: no row 'nominal (7.4 V), %s' for the trained mass" % corner,
                       where="altaay_lab/sim/POWER_PATH_SIM.md")
                continue
            dv = V.num(r["Lowest servo: min (mean)"].split(" V")[0].split()[-1])
            da = V.num(r["Ankle time under 6.0 V"])
            ok = dv is not None and da is not None and abs(dv - c["worst_servo_V_min"]) <= 0.02 and abs(da - c["ankle_pct_below_6V"]) <= 0.3
            R.ev("documented as-built row, nominal, %s, trained mass: lowest servo %s V, ankle %s %% (doc) vs %.2f V, %.1f %% (run)%s" % (
                corner, dv, da, c["worst_servo_V_min"], c["ankle_pct_below_6V"], "" if ok else ": DIFFERS"))
            if not ok:
                R.find("FAIL", "sim/POWER_PATH_SIM.md as-built row (nominal, %s, trained mass) not reproduced: doc %s V, %s %%; run "
                       "%.2f V, %.1f %%" % (corner, dv, da, c["worst_servo_V_min"], c["ankle_pct_below_6V"]),
                       fix="re-run sim/power_path_sim.py (as_built) and update the as-built section", where="altaay_lab/sim/POWER_PATH_SIM.md")
    t, h = verdict["typical"], verdict["high-side"]
    R.key("as built, nominal pack, worse of %s: lowest servo %.2f V typical (%s), %.2f V high-side (%s); %s under 6 V %.1f %% "
          "typical, %.1f %% high-side, counted in time (gate %.0f %%); no servo under %.1f V at full or nominal in either corner: %s" % (
              " and ".join(tn for tn, _ in runs), t["vmin"][1]["worst_servo_V_min"], t["vmin"][1]["worst_servo"].replace("_", " "),
              h["vmin"][1]["worst_servo_V_min"], h["vmin"][1]["worst_servo"].replace("_", " "), scope, t["ank"][1][metric],
              h["ank"][1][metric], ank_pct, vmin_gate,
              min(t["vmin"][1]["worst_servo_V_min"], h["vmin"][1]["worst_servo_V_min"]) >= vmin_gate))
    return R.write()


if __name__ == "__main__":
    main()
