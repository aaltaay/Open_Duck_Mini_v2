"""E6b: is the TEST_PLAN.md section 5 hop gate enough for the section 9 walking gate (no ankle under 6.0 V for more than
10 % of the walk at a nominal pack)? Sim pass only.

Uses sim/power_fix.py (agent PW; imported unchanged, its output folder pointed at VERIFY_OUT), which rebuilds the D15
star wiring as the netlist builds it and adds the D23 second feeds (its option 3b). The wiring modelled follows
wiring/netlist.yaml: option 3b when the cables SP4 and SP5 are active there, else option 1 (the star as built without
them). Nominal pack, typical source resistances (the pack side that TEST_PLAN 3.2 and 4.1 now gate), backlash-model
walk 10 to 16 s, servo hop = kit cable conductor + 2 contacts + servo board, swept by the contact resistance and run
once at exactly the section 5 gate value. Traces: the trained mass (E5) and our build (C8, sim/added_mass_sim.py at
the sim/MASS_BUDGET.md mass) when that run is there; the worse of the two counts.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e6b_hop_sweep.py   (after e5_current_budget.py and
c8_policy_mass.py; run_all.sh keeps that order)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E6b", "TEST_PLAN.md section 5 hop gate is enough for the section 9 ankle gate, wiring as in the netlist "
             "(power path sim sweep, sim pass only)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py",
             "Star wiring as built (22 AWG SP leads, P11 60 mm) plus the D23 second feeds when the netlist has SP4 and SP5; "
             "nominal pack, typical source resistances; hop = kit cable conductor + 2 contacts + servo board; ankle time "
             "under 6 V (time weighted) per hop value and at the section 5 gate; trained mass and our build traces",
             "Real BEC dropout (TEST_PLAN.md section 4), real hop resistance (section 5), the high-side pack side (sections "
             "3.2 and 4.1 gate it), regenerative braking, bus capacitance")
tp = open(V.lab("TEST_PLAN.md")).read()
sec5 = re.search(r"^## 5\..*?(?=^## )", tp, re.M | re.S)
g = re.search(r"Gate: (\d+) mOhm per conductor", sec5.group(0) if sec5 else "")
if not g:
    R.not_run("TEST_PLAN.md section 5 states no 'Gate: N mOhm per conductor'")
    R.write()
    sys.exit(0)
gate = int(g.group(1)) / 1000.0
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
net = V.load_netlist()
active = {c["id"] for c in net["cables"] if c.get("status") == "active"}
feeds = {"SP4", "SP5"} <= active
on = "3b" if feeds else "1"
R.inp(V.lab("sim", "power_fix.py"), V.lab("sim", "power_path_sim.py"), V.lab("wiring", "netlist.yaml"), V.lab("TEST_PLAN.md"))
os.environ["ODM_OUT"] = os.path.join(V.out_dir(), "e6b_sweep")
sys.path.insert(0, V.lab("sim"))
import power_fix as PF  # noqa: E402

R.ev("TEST_PLAN.md section 5 gate: %.0f mOhm per conductor; netlist SP4 and SP5 active: %s, so the model is power_fix.py option %s (%s)"
     % (gate * 1000, feeds, on, PF.OPTIONS[on]["desc"]))
p0 = PF.params("typical", PF.OPTIONS[on])
fixed = PF.wire(p0["kit_awg"], PF.L["kit"]) + p0["R_servo_pcb"]           # hop without its 2 contacts
points = [(0.0, "no contact resistance"), (0.005, "typical corner contacts"), (round((gate - fixed) / 2, 6), "the section 5 gate"),
          (0.020, ""), (0.030, "")]
res = {}
for rc, why in points:
    hop = fixed + 2 * rc
    worst = None
    for tn, npz in traces:
        r = PF.run("E6b %s hop %.1f mOhm %s" % (on, hop * 1000, tn), npz, *PF.WINDOW, PF.PACKS["nominal"], PF.OPTIONS[on], "typical",
                   extra=dict(R_contact=rc))
        R.ev("option %s, %s, hop %.1f mOhm per conductor%s: ankle min %.2f V, under 6 V %.1f %% of the walk (worst 50 Hz phase %s %%)" % (
            on, tn, hop * 1000, " (%s)" % why if why else "", r["ankle_V_min"], r["ankle_pct_below_6V"],
            r.get("ankle_pct_below_6V_50Hz_worst_phase", "-")))
        if worst is None or r["ankle_pct_below_6V"] > worst[0]:
            worst = (r["ankle_pct_below_6V"], tn, r["ankle_V_min"])
    res[hop] = worst
hops = sorted(res)
ok = [h for h in hops if res[h][0] <= 10.0]
bad = [h for h in hops if res[h][0] > 10.0]
est = None
if ok and bad and max(ok) < min(bad):
    a, b = max(ok), min(bad)
    est = a + (10.0 - res[a][0]) * (b - a) / (res[b][0] - res[a][0])
    R.ev("hop resistance at which the worse trace reaches the 10 %% gate: about %.0f mOhm per conductor (linear between %.1f and %.1f)"
         % (est * 1000, a * 1000, b * 1000))
at_gate = res[min(hops, key=lambda h: abs(h - gate))]
R.key("option %s (%s): ankle under 6 V at a nominal pack, worse trace: %s; at the %.0f mOhm gate %.1f %% (%s)" % (
    on, "SP4 and SP5 in the netlist" if feeds else "no second feeds in the netlist",
    ", ".join("%.0f mOhm %.1f%%" % (h * 1000, res[h][0]) for h in hops), gate * 1000, at_gate[0], at_gate[1]))
if at_gate[0] > 10.0:
    R.find("FAIL", "TEST_PLAN.md section 5 passes hops up to %.0f mOhm per conductor, but at that value the ankle is under 6.0 V "
           "for %.1f %% of the walk at a nominal pack (%s, option %s), over the section 9 gate of 10 %%%s" % (
               gate * 1000, at_gate[0], at_gate[1], on, "; about %.0f mOhm passes" % (est * 1000) if est else ""),
           fix="TEST_PLAN.md section 5: lower the gate to what section 9 needs, or change the wiring (sim/POWER_FIX.md)",
           where="altaay_lab/TEST_PLAN.md sections 5 and 9")
if not feeds:
    R.find("WARN", "wiring/netlist.yaml has no active SP4 and SP5, but DECISIONS.md D23 builds them; this run models the star "
           "wiring without the second feeds", fix="add SP4 and SP5 to the netlist (D23)", where="altaay_lab/wiring/netlist.yaml")
R.write()
