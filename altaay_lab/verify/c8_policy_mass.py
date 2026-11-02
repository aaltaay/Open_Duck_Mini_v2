"""C8: the stock policy still walks with the mass of the robot we will build (sim pass only).

Re-runs sim/added_mass_sim.py (agent M; unchanged, run into the output folder, steps "cases" and "seeds" only, so it
writes nothing into the repo) and checks:
  - the model mass equals sim/MASS_BUDGET.md ("Our build", read from the file) and
    the stock copy equals the trained 2.107 kg
  - the stock copy reproduces sim/CURRENT_BUDGET.md (bus means)
  - our build: no fall on flat ground in the nominal runs (stand, forward, turn, sideways, backlash, pushes) and in the
    seeded runs; tracking as written in the doc whose walk ran this mass within 1 % of the robot: sim/ADDED_MASS_SIM.md
    table 1 (its 2.77 kg build, before D22) or print/MASS_STUDY.md "Walking with the (c) robot" (the D22 build, 2.64 kg);
    if neither did, a WARN says so
  - the margins that sim/ADDED_MASS_SIM.md reports (backward centre of mass) have a hardware test in TEST_PLAN.md
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c8_policy_mass.py
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

FLAT = ["stand_in_place", "walk_forward_0.15", "turn_1.0", "walk_side_0.2", "walk_backlash", "walk_pushes"]
DOCNAME = {"stand_in_place": "Stand, zero command", "walk_forward_0.15": "Walk forward 0.15 m/s", "turn_1.0": "Turn 1.0 rad/s",
           "walk_side_0.2": "Walk sideways 0.2 m/s", "walk_backlash": "Walk forward, backlash model",
           "walk_pushes": "Walk forward, 15 N pushes every 3 s"}
CB_MEAN = {"stand_in_place": 0.19, "walk_forward_0.15": 2.22, "turn_1.0": 2.38, "walk_side_0.2": 2.25, "walk_backlash": 3.24,
           "walk_rough_backlash": 2.65, "walk_pushes": 1.89}


def doc_mass_kg():
    """build mass in sim/MASS_BUDGET.md ('Our build: **x kg**'), as text, or None"""
    p = V.lab("sim", "MASS_BUDGET.md")
    m = re.search(r"Our build: \*\*([0-9.]+) kg\*\*", open(p).read()) if os.path.exists(p) else None
    return m.group(1) if m else None


def main():
    mb_kg = doc_mass_kg()
    R = V.Result("C8", "The stock policy walks the robot we will build (%s kg, sim/MASS_BUDGET.md) on flat ground (sim/added_mass_sim.py, "
                 "sim pass only)" % (mb_kg or "?"),
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c8_policy_mass.py",
                 "Model mass vs MASS_BUDGET.md; stock copy vs CURRENT_BUDGET.md; our build in 6 flat cases nominal + 6 seeds "
                 "each; tracking vs the doc that ran the same mass (ADDED_MASS_SIM.md table 1 or print/MASS_STUDY.md); a hardware "
                 "test for the centre of mass margin",
                 "Rough terrain (falls for stock and ours), get-up, real servo tracking (issue 48), the real mass and centre "
                 "of mass (not weighed)")
    script = V.lab("sim", "added_mass_sim.py")
    doc = V.lab("sim", "ADDED_MASS_SIM.md")
    if not (os.path.exists(script) and os.path.exists(doc)):
        R.not_run("sim/added_mass_sim.py or sim/ADDED_MASS_SIM.md not found (sim agent output not landed)")
        R.write()
        return
    study = V.lab("print", "MASS_STUDY.md")
    R.inp(script, doc, V.lab("sim", "MASS_BUDGET.md"), V.lab("sim", "mass_budget.py"), V.lab("TEST_PLAN.md"),
          *([study] if os.path.exists(study) else []))
    scr = os.path.join(V.out_dir(), "c8_added_mass")
    os.makedirs(scr, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "ODM_OUT"}
    env.update(ODM_PLAYGROUND=V.PLAYGROUND, ODM_SCRATCH=scr)
    logs = ""
    for step in ("cases", "seeds"):
        f = os.path.join(scr, "added_mass", "results_%s.json" % step)
        if os.environ.get("VERIFY_REUSE") == "1" and os.path.exists(f):
            continue
        p = subprocess.run(["nice", "-n", "10", sys.executable, script, step], env=env, cwd=V.REPO,
                           capture_output=True, text=True, timeout=7200)
        logs += p.stdout + p.stderr
        open(os.path.join(scr, "stdout_%s.txt" % step), "w").write(p.stdout + p.stderr)
        if p.returncode != 0:
            R.not_run("added_mass_sim.py %s failed (exit %d): %s" % (step, p.returncode, (p.stdout + p.stderr)[-400:]))
            R.write()
            return
    if not logs:
        logs = "".join(open(os.path.join(scr, f)).read() for f in os.listdir(scr) if f.startswith("stdout_"))
    m_st = re.search(r"stock total mass ([0-9.]+) kg", logs)
    m_ou = re.search(r"ours total mass ([0-9.]+) kg", logs)
    mb = open(V.lab("sim", "MASS_BUDGET.md")).read()
    mb_total = re.search(r"Our build: \*\*([0-9.]+) kg\*\*", mb)
    if m_st and m_ou:
        R.ev("model mass: stock %.4f kg (trained 2.107 kg), ours %.4f kg (MASS_BUDGET.md %s kg)" % (
            float(m_st.group(1)), float(m_ou.group(1)), mb_total.group(1) if mb_total else "?"))
        if abs(float(m_st.group(1)) - 2.107) > 0.001:
            R.find("FAIL", "stock copy mass %.4f kg differs from the trained 2.107 kg" % float(m_st.group(1)))
        if not mb_total or abs(float(m_ou.group(1)) - float(mb_total.group(1))) > 0.006:
            R.find("FAIL", "model mass %s kg differs from MASS_BUDGET.md" % m_ou.group(1))
    cases = json.load(open(os.path.join(scr, "added_mass", "results_cases.json")))
    seeds = json.load(open(os.path.join(scr, "added_mass", "results_seeds.json")))
    kt = "1.148"
    bad = [c for c, v in CB_MEAN.items() if abs(cases["stock"][c]["per_kt"][kt]["bus_A_mean"] - v) > 0.005]
    R.ev("stock copy reproduces the CURRENT_BUDGET.md bus means in %d of %d cases" % (len(CB_MEAN) - len(bad), len(CB_MEAN)))
    if bad:
        R.find("FAIL", "stock copy differs from CURRENT_BUDGET.md in %s" % bad)
    # the doc whose walk ran this model mass: ADDED_MASS_SIM.md (its own build mass) or MASS_STUDY.md variant (c)
    ours_kg = float(m_ou.group(1)) if m_ou else None
    am = re.search(r"robot we will build\*\* \(([0-9.]+) kg", open(doc).read())
    am_kg = float(am.group(1)) if am else None
    ms_txt = open(study).read() if os.path.exists(study) else ""
    ms = re.search(r"^\| \(c\)[^|]*\| ([0-9.]+) \| \+", ms_txt, re.M)
    ms_kg = float(ms.group(1)) / 1000.0 if ms else None
    ref = {}          # case key -> documented tracking
    tol = max(0.006, 0.01 * (ours_kg or 0))      # a doc run within 1 % of the robot mass counts as this mass (stated below)
    if ours_kg is not None and am_kg is not None and abs(ours_kg - am_kg) <= tol:
        tab = [t for t in V.md_tables(doc) if t["header"][:4] == ["Case", "Model", "Falls (s)", "Tracking (measured / command)"]]
        drow = {(r["Case"], r["Model"]): r for r in (tab[0]["rows"] if tab else [])}
        ref = {c: drow.get((DOCNAME[c], "ours"), {}).get("Tracking (measured / command)") for c in FLAT}
        R.ev("tracking compared with sim/ADDED_MASS_SIM.md table 1 (its build %.2f kg; this model %.4f kg)" % (am_kg, ours_kg))
    elif ours_kg is not None and ms_kg is not None and abs(ours_kg - ms_kg) <= tol:
        tab = [t for t in V.md_tables(study) if t["header"][:4] == ["Case (nominal run)", "trained (stock)", "(b) today", "(c) proposed"]]
        ref = {r["Case (nominal run)"]: r["(c) proposed"] for r in (tab[0]["rows"] if tab else [])}
        R.ev("tracking compared with print/MASS_STUDY.md variant (c), the D22 build: %.4f kg there, %.4f kg in this model (%+.1f g, "
             "%+.1f %% of the robot, within the 1 %% the doc choice allows); sim/ADDED_MASS_SIM.md table 1 is its %.2f kg build "
             "(before D22) and is not compared" % (ms_kg, ours_kg, (ours_kg - ms_kg) * 1000, (ours_kg - ms_kg) / ours_kg * 100, am_kg or 0))
    else:
        R.find("WARN", "no doc records the walk of this model mass within 1 %% (%s kg): sim/ADDED_MASS_SIM.md ran %s kg, print/MASS_STUDY.md (c) %s kg"
               % (m_ou.group(1) if m_ou else "?", am_kg, "%.4f" % ms_kg if ms_kg else "?"),
               fix="re-run sim/added_mass_sim.py and update sim/ADDED_MASS_SIM.md table 1", where="altaay_lab/sim/ADDED_MASS_SIM.md")
    for c in FLAT:
        o = cases["ours"][c]
        fl = o["falls"]
        g = o["gait"]
        tr = g.get("track_lin") if c not in ("turn_1.0",) else g.get("track_yaw", None)
        tr = tr if tr is not None else g.get("track_lin")
        sd = seeds["ours"].get(c)
        dcell = ref.get(c) or ""
        dtr = V.num(dcell) if not re.search(r"fell", dcell) else None
        R.ev("ours, %s: falls %s; tracking %s (doc %s); seeds fell %s" % (
            DOCNAME[c], fl or "none", "%.2f" % tr if tr is not None else "-", dcell or "-",
            "%d of %d" % (sd["n_fell"], sd["n"]) if sd else "not run (stand)"))
        if fl:
            R.find("FAIL", "our build falls on flat ground: %s at %s s" % (DOCNAME[c], fl),
                   fix="see sim/ADDED_MASS_SIM.md; do not walk the build before this is understood")
        if sd and sd["n_fell"]:
            R.find("FAIL", "our build falls in %d of %d seeded runs: %s" % (sd["n_fell"], sd["n"], DOCNAME[c]))
        if dtr is not None and tr is not None and abs(dtr - tr) > 0.011:
            R.find("FAIL", "%s tracking %.2f differs from the doc that ran this mass (%.2f)" % (DOCNAME[c], tr, dtr),
                   fix="re-run the walk and update the doc's table", where="altaay_lab/sim/ADDED_MASS_SIM.md or print/MASS_STUDY.md")
    nfall = sum(1 for c in FLAT if cases["ours"][c]["falls"]) + sum(seeds["ours"][c]["n_fell"] for c in FLAT if c in seeds["ours"])
    nrun = len(FLAT) + sum(seeds["ours"][c]["n"] for c in FLAT if c in seeds["ours"])
    R.key("our build %s kg: %d falls in %d flat-ground runs; forward speed %.2f of the command (trained mass %.2f)" % (
        m_ou.group(1) if m_ou else "?", nfall, nrun, cases["ours"]["walk_forward_0.15"]["gait"]["track_lin"],
        cases["stock"]["walk_forward_0.15"]["gait"]["track_lin"]))
    rough = [(n, cases[n]["walk_rough_backlash_raised_start"]["falls"]) for n in ("stock", "ours")]
    R.ev("rough terrain, start raised 23 mm: stock falls %s, ours falls %s (not a flat-ground case; ADDED_MASS_SIM.md finding 4)" % (
        rough[0][1] or "none", rough[1][1] or "none"))
    tp = open(V.lab("TEST_PLAN.md")).read()
    if not re.search(r"centre of mass|center of mass|weigh", tp, re.I):
        R.find("WARN", "the walk margin to a backward centre of mass is only about 4 to 6 mm (ADDED_MASS_SIM.md table 7, finding 2) "
               "and TEST_PLAN.md has no step that weighs the robot or finds its centre of mass",
               fix="add the step proposed in sim/ADDED_MASS_SIM.md ('Proposed text', TEST_PLAN.md section 8 step 0: weigh the robot "
                   "and find its centre of mass at the home pose; expected %s +/- 0.05 kg by sim/MASS_BUDGET.md, about 1 mm ahead "
                   "of the ankle axes)" % (mb_kg or "?"),
               where="altaay_lab/TEST_PLAN.md section 8")
    R.write()


if __name__ == "__main__":
    main()
