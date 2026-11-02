"""Build altaay_lab/VERIFICATION.md from the result files of run_all.sh (one JSON per check in VERIFY_OUT).

Usage: VERIFY_OUT=<results folder> python3 altaay_lab/verify/report.py [--write altaay_lab/VERIFICATION.md]
Without --write it prints the page.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

ORDER = ["E1", "E2", "E3", "E4", "E5", "E6", "E6b", "E7", "E8", "E9", "C1", "C2", "C3", "C4a", "C4b", "C5", "C6", "C7", "C8", "C9", "C10", "C11"]

RUN_NOTES = [  # dated observations that a single run cannot show (agent NL2, final docs pass, 2026-11-02)
    "Re-run 2026-11-02 by agent NL2 (final docs pass) for the lead. A first full run, 12:46 to 12:54 AM ET, after the netlist final "
    "pass (agent NL1) and the D22 print profile (agent PP), gave 19 PASS, 2 FAIL (C3, C4a), 1 NOT RUN (C8). After the fixes in the "
    "next note and a viewer rebuild (make_viewer_data.py --write-bom, 1:05 AM ET), this page comes from a second full run, 1:05 to "
    "1:16 AM ET. The input table at the end gives the time of every file read.",
    "Fixed between the two runs, on the lead's ask: sim/mass_budget.py had no position for the new splices JFI and JFO (C8 stopped "
    "on KeyError 'JFI'); they now sit at the fuse holder seat and sim/MASS_BUDGET.md is re-run (2651.9 g). cables3d/cables3d.json "
    "took its cut lengths from the netlist without re-routing (the P7 holder leads and their extensions summed), then check_cables.py "
    "and make_report.py. fasteners/fasteners.json has two 0.3 mm eye washers per screw (DECISIONS.md D21 note) and its BOM summary "
    "names lines 17j to 17l (C4a).",
    "Checks changed in this pass (verify/): c9 reads BOM line 27's PLA need from print/PRINT_PLAN.md (it was hard-coded to the "
    "1474.5 + 27.8 g of the plan before D22) and the build mass from sim/MASS_BUDGET.md, compares only whole-set STL counts, and "
    "checks the robot mass only in START_HERE.md and README.md, as its docstring says. c8 reads the build mass and compares tracking "
    "with the walk run within 1 % of it (print/MASS_STUDY.md variant c, 13 g lighter). e6b models the wiring the netlist builds "
    "(sim/power_fix.py option 3b with SP4 and SP5) on the trained-mass and our-build traces and reads the gate from TEST_PLAN.md "
    "section 5; it now runs after c8. c3 sums the netlist pieces joined at a splice that the 3D record does not route (P7 at JFI and "
    "JFO). e1 takes its counts from the netlist.",
    "Still modelled without the D23 feeds: E6 and C7 run the star wiring of sim/power_path_sim.py (they reproduce the star rows of "
    "POWER_PATH_SIM.md); sim/POWER_FIX.md has the D23 numbers (Pololu 2815 at 99 to 101 % of 6 A, first-servo contacts halved). E8 "
    "passed in this run (56 tests); the old flaky panic test now reads Torque Enable back (bench/odm_bench/walkhooks.py), and one "
    "pass does not prove the flake is gone. The one FAIL left, C3, is two 20 mm ground tails (JG10 and JG30 to the first servo) "
    "that route 21 mm; cables3d's own chain check passes them because those splices float along the lead.",
]

HARDWARE = [
    ("Every made cable: crimp pull, connector fit, heat shrink, length at both limits of every joint it crosses",
     "TEST_PLAN.md section 1", "C2 (end treatments), C3 (lengths, loops, the 2 foot jumpers)"),
    ("Continuity and polarity of every wire, no short between nets", "TEST_PLAN.md section 2 (audit/continuity_checklist.csv)", "E1"),
    ("Cells, holder drop at 10 A, BMS trip, first charge", "TEST_PLAN.md section 3", "C7 (BMS margin on falls)"),
    ("BEC set point, input sweep and the 0.30 V dropout pass, Pololu 2815 at 5 A and 10 minutes at 6 A, 5 V regulator, fuse holder",
     "TEST_PLAN.md section 4", "E6 (BEC dropout 0.3 V assumed), C7 (2815 near its 6 A rating; 99 to 101 % with D23, sim/POWER_FIX.md)"),
    ("Kelvin resistance of one servo hop", "TEST_PLAN.md section 5", "E6b (the 40 mOhm gate with the D23 second feeds)"),
    ("Adapter enumerates with H1 unpowered and drives one servo", "TEST_PLAN.md section 6", "C7 (ground return through the adapter)"),
    ("First servo: registers 41 to 86, register 85 = 0, firmware, speed, thermal hold", "TEST_PLAN.md section 7", "E8 (bench scripts on a fake bus)"),
    ("Weigh the robot and find its centre of mass; staged power-up; all 14 IDs answer", "TEST_PLAN.md section 8 (8.0 is the mass step)",
     "C8 (backward margin 4 to 6 mm), C5 (IDs)"),
    ("Walking log: every servo voltage and current, ankle time under 6 V counted in time, checksum errors, forward speed",
     "TEST_PLAN.md section 9", "E6, E6b (bench/power_log.py reads in phase with the control loop: it needs its own timer first)"),
    ("IMU: 1000 still reads, tilt signs", "TEST_PLAN.md section 10", "none (no sim check of B20)"),
    ("Battery cut-off at servo Present Voltage 6.0 V; exit code 10 when torque off is not confirmed", "TEST_PLAN.md section 11",
     "E8 (battery guard and torque read-back on the fake bus)"),
    ("Foot switches: under 1 ohm closed, 200 presses, 60 s still", "TEST_PLAN.md section 12", "C6 (pins), C3 (jumper length)"),
    ("Coupon prints: insert bores, foot_top wall, left eye pilot, TPU sole", "print/PRINT_PLAN.md coupon session (B14, B15, B16, B26)", "none"),
    ("Screw head fits the CAD cannot settle: servo bag split, horn gap, M2x5 heads, hip roll inner screw rub",
     "HARDWARE_AUDIT.md B2, B6, B21; D18 first-leg check", "E7, C4a, C4b"),
    ("Hip yaw kept under 21.7 deg outside the walk (manual moves, find_soft_offsets.py, falls): F198/F211 heads",
     "TEST_PLAN.md 8.2a (+/-20 deg, robot hanging, hip yaw held by hand)", "C11 (walk and turn reach 10.4 deg; nothing in the Runtime limits it)"),
    ("Ankle plugs and the SP4/SP5 feeds at the foot_side apex", "TEST_PLAN.md 1.5 (HARDWARE_AUDIT B33)", "C3 (the SP4/SP5 routes touch foot_side in CAD)"),
]


def esc(s):
    return str(s).replace("|", "/").replace("\n", " ")


def main():
    out = V.out_dir()
    res = {}
    for p in glob.glob(os.path.join(out, "*.json")):
        try:
            d = json.load(open(p))
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("id") in ORDER:
            res[d["id"]] = d
    now = datetime.now(ZoneInfo("America/New_York"))
    stamp = now.strftime("%Y-%m-%d %-I:%M %p ET")
    st = {k: sum(1 for r in res.values() if r["status"] == k) for k in ("PASS", "FAIL", "NOT RUN")}
    nf = sum(1 for r in res.values() for f in r["findings"] if f["sev"] == "FAIL")
    nw = sum(1 for r in res.values() for f in r["findings"] if f["sev"] == "WARN")
    L = ["# VERIFICATION: every check that runs without the robot", "",
         "Generated %s by altaay_lab/verify/report.py from one run of `bash altaay_lab/verify/run_all.sh` (results kept outside "
         "the repo). Written by agent Q (verification) for Ahmed's Open Duck Mini v2 build. Every simulation result here is sim "
         "pass only. Nothing was bought, built or printed; no lab file was edited by these checks (each script that writes "
         "files was run on a copy or into the results folder)." % stamp, "",
         "## Summary",
         "%d checks: **%d PASS, %d FAIL, %d NOT RUN**. %d FAIL findings and %d WARN findings in all (below). PASS means no FAIL "
         "finding; a PASS row can still carry WARN findings (risks, test fits, notes)." % (len(res), st["PASS"], st["FAIL"], st["NOT RUN"], nf, nw),
         "",
         "How to run (from the repo root): `bash altaay_lab/verify/run_all.sh` runs everything (this run: %.0f minutes of check "
         "time on the shared 4-CPU box, sims under nice -n 10); `--quick`" % (sum(r.get("seconds", 0) for r in res.values()) / 60.0) + " skips the MuJoCo, ngspice and CAD sweep runs and reuses earlier results "
         "in the same folder. Settings: VERIFY_OUT (results folder outside the repo), ODM_RUNTIME (Open_Duck_Mini_Runtime at "
         "376de65), ODM_PLAYGROUND (Open_Duck_Playground at b9be205), ODM_TEST_PYTHON (a Python with rustypot and pypot for the "
         "bench tests). Each check also runs alone: the command is in the matrix.", "",
         "Run notes:", ""] + ["- " + n for n in RUN_NOTES] + ["",
         "## Main findings", "",
         "Checks that fail, with their numbers (fixes are in the FAIL section below):", ""]
    for cid in ORDER:
        r = res.get(cid)
        if r and r["status"] == "FAIL":
            L.append("- **%s** %s: %s" % (cid, r["title"], r.get("key") or "; ".join(r["evidence"][:2])))
    L += ["", "Passing checks that still carry risks to measure on the bench (WARN):", ""]
    for cid in ORDER:
        r = res.get(cid)
        if r and r["status"] == "PASS" and any(f["sev"] == "WARN" for f in r["findings"]):
            w = [f["text"] for f in r["findings"] if f["sev"] == "WARN"]
            L.append("- **%s**: %s%s" % (cid, w[0][:260], " (and %d more)" % (len(w) - 1) if len(w) > 1 else ""))
    L += ["", "## Matrix", "",
          "| # | Check | How it runs | Result | Evidence (numbers) | Covers | Does not cover |", "|---|---|---|---|---|---|---|"]
    for cid in ORDER:
        r = res.get(cid)
        if not r:
            L.append("| %s | (no result file) | | NOT RUN (the check did not write a result) | | | |" % cid)
            continue
        n = {s: sum(1 for f in r["findings"] if f["sev"] == s) for s in ("FAIL", "WARN")}
        result = r["status"] if r["status"] != "NOT RUN" else "NOT RUN (%s)" % r["reason"]
        if r["status"] != "NOT RUN" and (n["FAIL"] or n["WARN"]):
            result += " (%d FAIL, %d WARN)" % (n["FAIL"], n["WARN"])
        ev = r.get("key") or "; ".join(r["evidence"][:3])
        if len(r["evidence"]) > 1:
            ev += " (details below)"
        L.append("| %s | %s | `%s` | **%s** | %s | %s | %s |" % (cid, esc(r["title"]), esc(r["command"]), esc(result), esc(ev),
                                                               esc(r["covers"]), esc(r["not_covers"])))
    L += ["", "## FAIL findings and proposed fixes", "",
          "Each line: what is wrong, with the numbers, then the proposed fix and the file it belongs to. The files belong to other "
          "agents or to the lead; nothing here was changed by agent Q.", ""]
    for cid in ORDER:
        r = res.get(cid)
        if not r:
            continue
        fl = [f for f in r["findings"] if f["sev"] == "FAIL"]
        if not fl:
            continue
        L.append("### %s %s" % (cid, r["title"]))
        for f in fl:
            L.append("- %s%s%s" % (f["text"], (" **Fix:** " + f["fix"]) if f.get("fix") else "",
                                   (" (" + f["where"] + ")") if f.get("where") else ""))
        L.append("")
    L += ["## WARN findings (risks, test fits, notes)", ""]
    for cid in ORDER:
        r = res.get(cid)
        if not r:
            continue
        wl = [f for f in r["findings"] if f["sev"] == "WARN"]
        if not wl:
            continue
        L.append("### %s" % cid)
        for f in wl:
            L.append("- %s%s" % (f["text"], (" Proposed: " + f["fix"]) if f.get("fix") else ""))
        L.append("")
    L += ["## Hardware-only tests that remain", "",
          "No check above replaces these; each needs the parts or the robot. Order and pass/fail values are in TEST_PLAN.md.", "",
          "| Test | Where | What the checks above say about it |", "|---|---|---|"]
    for t, w, c in HARDWARE:
        L.append("| %s | %s | %s |" % (t, w, c))
    L += ["", "## Details per check", ""]
    for cid in ORDER:
        r = res.get(cid)
        if not r:
            continue
        L.append("### %s %s: %s" % (cid, r["title"], r["status"] if r["status"] != "NOT RUN" else "NOT RUN (%s)" % r["reason"]))
        L.append("Command: `%s`. Finished %s, %.0f s." % (r["command"], r.get("finished_utc", "?"), r.get("seconds", 0)))
        for e in r["evidence"]:
            L.append("- %s" % e)
        info = [f for f in r["findings"] if f["sev"] == "INFO"]
        for f in info:
            L.append("- INFO: %s" % f["text"])
        L.append("")
    L += ["## Inputs read (sha256, first 10 hex, and file time)", "", "| File | sha256 | Modified |", "|---|---|---|"]
    seen = {}
    for r in res.values():
        for k, v in r.get("inputs", {}).items():
            seen[k] = v
    for k in sorted(seen):
        L.append("| %s | %s | %s |" % (k, seen[k]["sha"], seen[k]["mtime"]))
    L.append("")
    text = "\n".join(L)
    text = text.replace(chr(0x2014), ", ").replace(chr(0x2013), "-")
    if "--write" in sys.argv:
        dst = sys.argv[sys.argv.index("--write") + 1]
        open(dst, "w", encoding="utf-8").write(text)
        print("wrote %s: %d PASS, %d FAIL, %d NOT RUN" % (dst, st["PASS"], st["FAIL"], st["NOT RUN"]))
    else:
        print(text)


if __name__ == "__main__":
    main()
