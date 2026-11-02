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

RUN_NOTES = [  # dated observations that a single run cannot show (agent SFX, last fixes for PR 6, 2026-11-02)
    "Run 2026-11-02 by agent SFX for the lead, the last full run for PR 6, after the C8 and E6b fixes (sim/MASS_BUDGET.md and "
    "the print/MASS_STUDY.md (c) walk re-run on today's model; TEST_PLAN.md section 5 in three bands, lead decision L3), the "
    "as-built power path re-run (sim/POWER_PATH_SIM.md) and the cable 'test fit' label (cables3d/check_cables.py; viewer data "
    "and BOM_FULL rebuilt). This page comes from one full run, 6:19 to 6:32 AM ET (VERIFY_OUT in the agent's scratch folder, "
    "ODM_TEST_PYTHON as in the integration run); C9 ran again at 6:33 AM ET after the STATE.md and START_HERE.md lines with "
    "these counts, and C4 and C6 at 6:35 AM ET and C8, E6, C7 and E6b in full at 6:36 to 6:40 AM ET after the time stamps in "
    "the agent's dated doc lines were set to the real edit times, with the same results. The input table at the end gives "
    "the time of every file read.",
    "Changed for this run (verify/): e6b_hop_sweep.py reads the TEST_PLAN.md section 5 bands of lead decision L3 (DECISIONS.md "
    "D23 note): at the pass gate ('Gate: 28 mOhm per conductor') every section 9 gate must hold, else FAIL; at the warn limit "
    "('Fail: over 40 mOhm per conductor') time under 6 V over the gate is a WARN with the knee, head roll and ankle numbers, "
    "and a servo under 4.5 V a FAIL. report.py: these notes and the section 4 and 5 hardware rows. No check was loosened: C8 "
    "still compares with 0.011, and E6b's gates are those of TEST_PLAN.md section 9.",
    "Why the 2 FAILs of the integration run are gone. C8: its doc is current again. sim/mass_budget.py gives 2652.8 g "
    "(MASS_BUDGET.md updated; +0.9 g of wire from agent CAB's later cut changes) and the (c) walk of print/MASS_STUDY.md was "
    "re-run with mass_study.py walk on that model (the slice table of print/SLICE_SUMMARY.md, the D22 print as adopted). "
    "Against the study's run the nominal runs moved by 0.004 or less, pushes by 0.013 (0.631 to 0.618); with the study's own "
    "slice table (0.01 g more on one part) the same script gives 0.626, and the 6 seeded pushes runs span 0.614 to 0.629: "
    "run-to-run noise, 0 falls on flat ground. E6b: TEST_PLAN 5 now passes a hop only up to 28 mOhm per conductor, the largest "
    "whole value at which every servo meets section 9 in sim (our build: right knee 9.9 % under 6 V at 28 mOhm, 10.2 % at 29); "
    "at the 40 mOhm warn limit the right knee is under 6 V for 13.4 % of the walk (WARN: the walking log decides and the 3S "
    "plan is made ready).",
    "E6 and C7 check the robot as wired: D15 plus the D23 feeds SP4 and SP5, every length and gauge read from "
    "wiring/netlist.yaml at run time (sim/power_path_sim.py topology as_built, which runs sim/power_fix.py option ab), on the "
    "trained-mass (E5) and our-build (C8) traces; E6b sweeps the hop on the same network. sim/POWER_PATH_SIM.md 'As built' is "
    "the run on today's netlist (SP4 400 mm, SP5 430 mm): our build, nominal pack, typical corner, ankles 6.4 % and right "
    "knee 9.8 % under 6 V; Pololu 2815 RMS 5.93 A. C3 judges the cable lengths itself, by chain through floating splices with "
    "the twist take-up; cables3d.json now marks D12, S2 and S7 'test fit' (they reach, with less than the 40 mm slack), which "
    "C3 reports as WARN as before. E8 passed in this run (63 tests in 221.6 s; the race test failed 0 of 4 runs).",
]

HARDWARE = [
    ("Every made cable: crimp pull, connector fit, heat shrink (34 sleeves, 2 x OD on the splices) and twist lay, length, joint "
     "loops and the 75 tie points at both limits of every joint it crosses (the test fit)",
     "TEST_PLAN.md section 1 (1.3, 1.4)", "C1 (sleeve count), C2 (end treatments), C3 (lengths with the twist take-up, 43 loops "
     "at 3 x OD, what holds each tie point, the 2 foot jumpers)"),
    ("Continuity and polarity of every wire, no short between nets", "TEST_PLAN.md section 2 (audit/continuity_checklist.csv)", "E1"),
    ("Cells, holder drop at 10 A, BMS trip, first charge", "TEST_PLAN.md section 3", "C7 (BMS margin on falls)"),
    ("BEC set point, input sweep and the 0.30 V dropout pass, Pololu 2815 at 5 A and 10 minutes at 6 A, 5 V regulator, fuse holder",
     "TEST_PLAN.md section 4", "E6 (BEC dropout 0.3 V assumed), C7 (Pololu 2815 at 99 % of its 6 A point as built, sim RMS 5.93 A)"),
    ("Kelvin resistance of one servo hop: pass to 28 mOhm per conductor, warn over 28 up to 40, fail over 40 (lead decision L3)", "TEST_PLAN.md section 5",
     "E6b (as built: at the 28 mOhm pass gate every servo meets section 9 in sim, right knee 9.9 %; at the 40 mOhm warn limit the right knee is under 6 V for 13.4 % of the walk; the ankles alone hold to about 60 mOhm)"),
    ("Adapter enumerates with H1 unpowered and drives one servo", "TEST_PLAN.md section 6", "C7 (ground return through the adapter)"),
    ("First servo: registers 41 to 86, register 85 = 0, firmware, speed, thermal hold", "TEST_PLAN.md section 7", "E8 (bench scripts on a fake bus)"),
    ("Weigh the robot and find its centre of mass; staged power-up; all 14 IDs answer", "TEST_PLAN.md section 8 (8.0 is the mass step)",
     "C8 (backward margin 4 to 6 mm), C5 (IDs)"),
    ("Walking log: every servo voltage and current, time under 6 V of every servo counted in time (ankles, knees, head roll at 10 %), checksum errors, forward speed",
     "TEST_PLAN.md section 9", "E6, E6b (sim), E8 (bench/power_log.py on the fake bus: own timer in the loop's idle time, time count matches an exact share)"),
    ("IMU: 1000 still reads, tilt signs", "TEST_PLAN.md section 10", "none (no sim check of B20)"),
    ("Battery cut-off at servo Present Voltage 6.0 V; exit code 10 when torque off is not confirmed", "TEST_PLAN.md section 11",
     "E8 (battery guard and torque read-back on the fake bus)"),
    ("Foot switches: under 1 ohm closed, 200 presses, 60 s still", "TEST_PLAN.md section 12", "C6 (pins), C3 (jumper length)"),
    ("Coupon prints: insert bores, foot_top wall, left eye pilot, TPU sole", "print/PRINT_PLAN.md coupon session (B14, B15, B16, B26)", "none"),
    ("Screw head fits the CAD cannot settle: servo bag split, horn gap, M2x5 heads, hip roll inner screw rub",
     "HARDWARE_AUDIT.md B2, B6, B21; D18 first-leg check", "E7, C4a, C4b"),
    ("Hip yaw kept under 21.7 deg outside the walk (manual moves, find_soft_offsets.py, falls): F198/F211 heads",
     "TEST_PLAN.md 8.2a (+/-20 deg, robot hanging, hip yaw held by hand)", "C11 (walk and turn reach 10.5 deg; nothing in the Runtime limits it)"),
    ("Head yaw kept within +/-45 deg for manual moves; the neck bundle loop turned once to the full +/-160 deg at the test fit",
     "TEST_PLAN.md 8.2b and 1.4 (D25)", "C3 (neck loops meet 3 x OD over +/-160 deg in CAD), E9 (head yaw the policy uses in the sim walk)"),
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
