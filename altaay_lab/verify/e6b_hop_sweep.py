"""E6b: is the TEST_PLAN.md section 5 hop gate enough for the section 9 walking gates, with the wiring as it is built now
(sim pass only)?

Section 9 gates (read from TEST_PLAN.md): no servo under 4.5 V at any time, and no ankle under 6.0 V for more than 10 %
of the walking time at nominal, counted in time (ngspice time steps weighted by their length; the 50 Hz phase range of
a log locked to the control loop is shown next to it). Section 5 gate: the largest hop resistance per conductor it
passes ("Gate: N mOhm per conductor").

Model: sim/power_fix.py option "ab" (the as-built network that E6 checks through sim/power_path_sim.py topology
"as_built": the option 3b network with every length and gauge from wiring/netlist.yaml, D15 star plus the D23 feeds
SP4 and SP5 where the netlist has them, data-lead grounds). Nominal pack, typical source resistances (the pack side that
TEST_PLAN 3.2 and 4.1 gate), backlash-model walk 10 to 16 s, servo hop = kit cable conductor + 2 contacts + servo board,
swept by the contact resistance and run once at exactly the section 5 gate value. Traces: the trained mass (E5) and our
build (C8, sim/added_mass_sim.py at the sim/MASS_BUDGET.md mass) when that run is there; the worse of the two counts.
Also reads the hop value section 5 quotes for "the ankle gate holds to about N mOhm" and compares it with this sweep.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e6b_hop_sweep.py   (after e5_current_budget.py and
c8_policy_mass.py; run_all.sh keeps that order)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E6b", "TEST_PLAN.md section 5 hop gate is enough for the section 9 gates, wiring as built (D15 plus the D23 feeds, "
             "netlist lengths; power path sim sweep, sim pass only)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py",
             "As-built network (sim/power_fix.py option ab = 3b with the netlist lengths and gauges and the data-lead grounds); "
             "nominal pack, typical source resistances; hop = kit cable conductor + 2 contacts + servo board; both section 9 gates "
             "(4.5 V at any time, ankle time under 6 V counted in time) per hop value and at the section 5 gate; trained mass "
             "and our build traces; the section 5 'holds to about N mOhm' figure",
             "Real BEC dropout (TEST_PLAN.md section 4), real hop resistance (section 5), the high-side pack side (sections "
             "3.2 and 4.1 gate it), regenerative braking, bus capacitance")
tp = open(V.lab("TEST_PLAN.md")).read()
sec5 = re.search(r"^## 5\..*?(?=^## )", tp, re.M | re.S)
sec9 = re.search(r"^## 9\..*?(?=^## )", tp, re.M | re.S)
s5 = sec5.group(0) if sec5 else ""
s9 = sec9.group(0) if sec9 else ""
g = re.search(r"Gate: (\d+) mOhm per conductor", s5)
if not g:
    R.not_run("TEST_PLAN.md section 5 states no 'Gate: N mOhm per conductor'")
    R.write()
    sys.exit(0)
gate = int(g.group(1)) / 1000.0
claim = re.search(r"holds to about (\d+) mOhm", s5)
ga = re.search(r"no servo under ([0-9.]+) V at any time", s9)
gb = re.search(r"no (ankle|servo) under ([0-9.]+) V for more than ([0-9.]+) %", s9)
vmin_gate = float(ga.group(1)) if ga else 4.5
ank_pct = float(gb.group(3)) if gb else 10.0
scope = gb.group(1) if gb else "ankle"          # "servo": TEST_PLAN 9 times every servo, not only the ankles
if not (ga and gb):
    R.find("WARN", "TEST_PLAN.md section 9 pass line not found; the check used 4.5 V and 10 %", where="altaay_lab/TEST_PLAN.md section 9")
traces = [("trained mass (E5)", os.path.join(V.out_dir(), "e5_current", "trace_walk_backlash.npz")),
          ("our build (C8)", os.path.join(V.out_dir(), "c8_added_mass", "added_mass", "traces", "ours", "trace_walk_backlash.npz"))]
traces = [(n, f) for n, f in traces if os.path.exists(f)]
if not traces or not traces[0][0].startswith("trained"):
    R.not_run("trace_walk_backlash.npz from E5 not found")
    R.write()
    sys.exit(0)
if len(traces) == 1:
    R.find("WARN", "our build's trace from C8 not found: only the trained-mass trace was run (our build draws more current)",
           fix="run c8_policy_mass.py before this check (run_all.sh order)")
R.inp(V.lab("sim", "power_fix.py"), V.lab("sim", "power_path_sim.py"), V.lab("wiring", "netlist.yaml"), V.lab("TEST_PLAN.md"))
os.environ["ODM_OUT"] = os.path.join(V.out_dir(), "e6b_sweep")
sys.path.insert(0, V.lab("sim"))
import power_fix as PF  # noqa: E402

on = "ab"
nl = PF.net_len()
feeds = sorted(fd["cable"] for fd in nl["feeds"].values())
R.ev("TEST_PLAN.md section 5 gate: %.0f mOhm per conductor; section 9 gates: no servo under %.1f V, %s under 6.0 V at most %.0f %% "
     "of the time; model: sim/power_fix.py option ab (as built), netlist %s sha256 %s, second feeds in the netlist: %s" % (
         gate * 1000, vmin_gate, "every servo" if scope == "servo" else "ankle", ank_pct, nl["source"]["path"], nl["source"]["sha256_10"],
         ", ".join(feeds) or "none"))
p0 = PF.params("typical", PF.OPTIONS[on])
kit = sorted({mm for v in nl["hop_mm"].values() for mm in v})
if len(kit) != 1:
    R.find("WARN", "kit hops of different cut lengths in the netlist (%s mm): the hop value below uses the first" % kit)
fixed = PF.wire(p0["kit_awg"], kit[0]) + p0["R_servo_pcb"]           # hop without its 2 contacts
points = [(0.0, "no contact resistance"), (0.005, "typical corner contacts"), (round((gate - fixed) / 2, 6), "the section 5 gate"),
          (0.020, ""), (0.030, "")]
res = {}
for rc, why in points:
    hop = fixed + 2 * rc
    worst = None
    for tn, npz in traces:
        r = PF.run("E6b %s hop %.1f mOhm %s" % (on, hop * 1000, tn), npz, *PF.WINDOW, PF.PACKS["nominal"], PF.OPTIONS[on], "typical",
                   extra=dict(R_contact=rc))
        s6 = r["servo_pct_below_6V"]
        R.ev("as built, %s, hop %.1f mOhm per conductor%s: ankle min %.2f V, under 6 V %.1f %% of the time (50 Hz by phase %.1f to "
             "%.1f %%); lowest servo %s %.2f V; knees %.1f / %.1f %%, head roll %.1f %% under 6 V%s" % (
                 tn, hop * 1000, " (%s)" % why if why else "", r["ankle_V_min"], r["ankle_pct_below_6V"],
                 r["ankle_pct_below_6V_50Hz_best_phase"], r["ankle_pct_below_6V_50Hz_worst_phase"], r["worst_servo"].replace("_", " "),
                 r["worst_servo_V_min"], s6["left_knee"], s6["right_knee"], s6["head_roll"], "" if r["complete"] else "; INCOMPLETE run"))
        if not r["complete"]:
            R.find("FAIL", "ngspice stopped early: %s, hop %.1f mOhm" % (tn, hop * 1000))
        anyk = max(s6, key=s6.get)
        if worst is None or r["ankle_pct_below_6V"] > worst["ank"]:
            worst = dict(worst or {}, ank=r["ankle_pct_below_6V"], tn=tn, amin=r["ankle_V_min"])
        if "vmin" not in worst or r["worst_servo_V_min"] < worst["vmin"]:
            worst.update(vmin=r["worst_servo_V_min"], who=r["worst_servo"], who_tn=tn)
        if "any" not in worst or s6[anyk] > worst["any"]:
            worst.update(any=s6[anyk], any_who=anyk, any_tn=tn)
    res[hop] = worst
hops = sorted(res)
ok = [h for h in hops if res[h]["ank"] <= ank_pct]
bad = [h for h in hops if res[h]["ank"] > ank_pct]
est = None
if ok and bad and max(ok) < min(bad):
    a, b = max(ok), min(bad)
    est = a + (ank_pct - res[a]["ank"]) * (b - a) / (res[b]["ank"] - res[a]["ank"])
    R.ev("hop resistance at which the worse trace reaches the %.0f %% ankle gate: about %.0f mOhm per conductor (linear between %.1f and "
         "%.1f)" % (ank_pct, est * 1000, a * 1000, b * 1000))
elif not bad:
    R.ev("the ankle gate holds over the whole sweep (to %.1f mOhm per conductor)" % (max(hops) * 1000))
at_gate = res[min(hops, key=lambda h: abs(h - gate))]
R.key("as built (%s): ankle under 6 V at a nominal pack, worse trace: %s; at the %.0f mOhm gate %.1f %% (%s), worst servo of any kind "
      "%s %.1f %%, lowest servo %.2f V" % (
          "SP4 and SP5 in the netlist" if feeds else "no second feeds in the netlist",
          ", ".join("%.0f mOhm %.1f%%" % (h * 1000, res[h]["ank"]) for h in hops), gate * 1000, at_gate["ank"], at_gate["tn"],
          at_gate["any_who"].replace("_", " "), at_gate["any"], at_gate["vmin"]))
okA = [h for h in hops if res[h]["any"] <= ank_pct]
badA = [h for h in hops if res[h]["any"] > ank_pct]
estA = None
if okA and badA and max(okA) < min(badA):
    a, b = max(okA), min(badA)
    estA = a + (ank_pct - res[a]["any"]) * (b - a) / (res[b]["any"] - res[a]["any"])
    R.ev("hop resistance at which the worst servo of any kind (knee or head roll, worse trace) reaches %.0f %% under 6 V: about %.0f mOhm "
         "per conductor (linear between %.1f and %.1f)" % (ank_pct, estA * 1000, a * 1000, b * 1000))
if scope == "servo" and at_gate["any"] > ank_pct:
    R.find("FAIL", "TEST_PLAN.md section 5 passes hops up to %.0f mOhm per conductor, but at that value the %s is under 6.0 V for %.1f %% "
           "of the walk at a nominal pack (%s, as built), over the section 9 gate of %.0f %%%s" % (
               gate * 1000, at_gate["any_who"].replace("_", " "), at_gate["any"], at_gate["any_tn"], ank_pct,
               "; about %.0f mOhm passes" % (estA * 1000) if estA else ""),
           fix="TEST_PLAN.md section 5: gate at most %d mOhm per conductor on 2S (the typical corner is %.1f), or the 3S plan "
               "(sim/POWER_FIX.md 6+3b)" % (int(estA * 1000) if estA else int(gate * 1000), (fixed + 0.010) * 1000),
           where="altaay_lab/TEST_PLAN.md sections 5 and 9")
if at_gate["ank"] > ank_pct:
    R.find("FAIL", "TEST_PLAN.md section 5 passes hops up to %.0f mOhm per conductor, but at that value the ankle is under 6.0 V "
           "for %.1f %% of the walk at a nominal pack (%s, as built), over the section 9 gate of %.0f %%%s" % (
               gate * 1000, at_gate["ank"], at_gate["tn"], ank_pct, "; about %.0f mOhm passes" % (est * 1000) if est else ""),
           fix="TEST_PLAN.md section 5: lower the gate to what section 9 needs, or change the wiring (sim/POWER_FIX.md)",
           where="altaay_lab/TEST_PLAN.md sections 5 and 9")
if scope == "ankle" and at_gate["any"] > ank_pct:
    R.find("WARN", "at the section 5 gate (%.0f mOhm) the ankles pass, but the %s is under 6.0 V for %.1f %% of the walk (%s, as built, "
           "nominal, typical pack side): with SP4/SP5 the knee and the head roll, not the ankle, are the low points, %s%s" % (
               gate * 1000, at_gate["any_who"].replace("_", " "), at_gate["any"], at_gate["any_tn"],
               "and section 9 times them too, so a hop that passes section 5 can fail the walking log"
               if re.search(r"time the knees and the head roll", s9) else "and section 9 times only the ankles",
               "; every servo under 10 %% needs about %.0f mOhm per conductor" % (estA * 1000) if estA else ""),
           fix="TEST_PLAN.md section 9: time every servo, not only the ankles (E6); if the knees join the gate, section 5 needs "
               "at most %d mOhm per conductor on 2S (the typical corner is %.1f), else the 3S plan" % (
                   int(estA * 1000) if estA else int(gate * 1000), (fixed + 0.010) * 1000),
           where="altaay_lab/TEST_PLAN.md sections 5 and 9")
if at_gate["vmin"] < vmin_gate:
    R.find("FAIL", "at the section 5 gate (%.0f mOhm) a servo goes under %.1f V at a nominal pack (%s %.2f V, %s, as built)" % (
        gate * 1000, vmin_gate, at_gate["who"].replace("_", " "), at_gate["vmin"], at_gate["who_tn"]),
        fix="TEST_PLAN.md section 5: lower the gate", where="altaay_lab/TEST_PLAN.md sections 5 and 9")
if claim and est is not None and abs(int(claim.group(1)) - est * 1000) > 10:
    R.find("WARN", "TEST_PLAN.md section 5 says the ankle gate holds to about %s mOhm per conductor; with the as-built wiring this sweep "
           "gives about %.0f mOhm (worse trace, typical pack side)" % (claim.group(1), est * 1000),
           fix="TEST_PLAN.md section 5: write 'sim: the ankle gate holds to about %.0f mOhm' (E6b, as built)" % (round(est * 100) * 10),
           where="altaay_lab/TEST_PLAN.md section 5")
elif claim:
    R.ev("TEST_PLAN.md section 5 'holds to about %s mOhm' agrees with this sweep (%s)" % (
        claim.group(1), "about %.0f mOhm" % (est * 1000) if est is not None else "no crossing in the sweep"))
if not feeds:
    R.find("WARN", "wiring/netlist.yaml has no active second feeds (SP4, SP5), but DECISIONS.md D23 builds them; this run models the "
           "star wiring without them", fix="add SP4 and SP5 to the netlist (D23)", where="altaay_lab/wiring/netlist.yaml")
R.write()
