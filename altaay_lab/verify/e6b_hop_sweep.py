"""E6b: what hop resistance would pass the TEST_PLAN.md section 9 walking gate (no ankle under 6.0 V for more than 10%
of the walk at a nominal pack)? Runs the star model of sim/power_path_sim.py (unchanged, imported from a copy of its
source with the D15 power leads at 22 AWG as built) at a nominal pack, typical source resistances, for a few servo hop
resistances, including an ideal hop (no cable, no contact, no board resistance). Sim pass only.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e6b_hop_sweep.py   (after e5_current_budget.py)
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E6b", "TEST_PLAN.md section 5 hop gate (40 mOhm) is enough for the section 9 ankle gate (power path sim sweep, sim pass only)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py",
             "Star wiring with 22 AWG leads, nominal pack, typical source resistances; hop = kit or made lead conductor + "
             "2 contacts + servo board; ankle time under 6 V and minimum voltage per hop value",
             "Real BEC dropout (TEST_PLAN.md section 4), real hop resistance (section 5), regenerative braking, bus capacitance")
tr = os.path.join(V.out_dir(), "e5_current")
wb = os.path.join(tr, "trace_walk_backlash.npz")
if not os.path.exists(wb):
    R.not_run("trace_walk_backlash.npz from E5 not found")
    R.write()
    sys.exit(0)
src = open(V.lab("sim", "power_path_sim.py")).read()
old = 'bL = wire(20, 150) + p["R_contact"]; bN = wire(20, 180) + p["R_contact"]'
src = src.replace(old, old.replace("wire(20,", "wire(22,"))
mod = types.ModuleType("pps_sweep")
os.environ.update(ODM_TRACES=tr, ODM_OUT=os.path.join(V.out_dir(), "e6b_sweep"))
exec(compile(src, "power_path_sim_sweep", "exec"), mod.__dict__)
TYP = dict(R_cell=0.015, R_holder=0.010, R_adapter=0.005, topology="star")
CASES = [  # label, overrides (hop = CU[kit_awg] x 0.15 m + 2 R_contact + R_servo_pcb)
    ("typical corner (24 AWG kit cable, 5 mOhm contacts)", dict(TYP, R_contact=0.005, kit_awg=24)),
    ("22 AWG made leads (contingency X1/X2), 5 mOhm contacts", dict(TYP, R_contact=0.005, kit_awg=22)),
    ("20 AWG leads, 2 mOhm contacts, 2 mOhm board", dict(TYP, R_contact=0.002, kit_awg=20, R_servo_pcb=0.002)),
    ("ideal hop (0 ohm)", dict(TYP, R_contact=0.0, kit_awg=0, R_servo_pcb=0.0)),
]
ANK = ("left_ankle", "right_ankle")
mod.CU[0] = 0.0          # pseudo gauge 0: a hop conductor with no resistance (ideal case only; other wires keep their gauge)
res = []
for lab_, over in CASES:
    p = dict(mod.P, **over)
    hop = mod.wire(p["kit_awg"], 150) + 2 * p["R_contact"] + p["R_servo_pcb"]
    c = mod.run_case("sweep: " + lab_, wb, 10.0, 16.0, 3.7, over=over)
    a6 = max(c["servo_ms_below_6V"][a] for a in ANK) / c["window_ms"] * 100.0
    res.append((lab_, hop, a6, c))
    R.ev("%s: hop %.1f mOhm per conductor; worst %s %.2f V; ankles under 6 V %.1f%% of the walk; BEC out mean %.2f V" % (
        lab_, hop * 1000, c["worst_servo"], c["worst_servo_V_min"], a6, c["bec_out_V_mean"]))
ideal = res[-1]
R.key("ankle under 6 V at a nominal pack: %s; section 5 passes hops up to 40 mOhm" % ", ".join(
    "%.0f mOhm %.0f%%" % (r[1] * 1000, r[2]) for r in res))
gate5 = 0.040
est = None
if ideal[2] > 10.0:
    R.find("WARN", "even an ideal hop leaves an ankle under 6.0 V for %.0f%% of the walk at a nominal pack (BEC in dropout, "
           "bus mean %.2f V): the TEST_PLAN.md section 9 gate (10%%) cannot pass at nominal with this power source in the sim"
           % (ideal[2], ideal[3]["bec_out_V_mean"]),
           fix="TEST_PLAN.md section 9: state the ankle gate at full charge (8.3 V or more) and keep the nominal log as a "
               "measurement only, or plan a source that does not drop out (buck-boost) before the walking log; section 5: "
               "the 40 mOhm hop gate does not protect the section 9 gate (typical corner already over 10%)",
           where="altaay_lab/TEST_PLAN.md sections 5 and 9")
else:
    ok = [r for r in res if r[2] <= 10.0]
    bad = [r for r in res if r[2] > 10.0]
    if ok and bad:   # linear estimate between the largest passing and the smallest failing hop
        a, b = max(ok, key=lambda r: r[1]), min(bad, key=lambda r: r[1])
        est = a[1] + (10.0 - a[2]) * (b[1] - a[1]) / (b[2] - a[2])
        R.ev("hop resistance at which the sim reaches the 10%% gate: about %.0f mOhm per conductor (linear between %.1f and %.1f mOhm)"
             % (est * 1000, a[1] * 1000, b[1] * 1000))
    R.ev("largest hop in the sweep that passes the 10%% gate: %.1f mOhm" % (max(r[1] for r in ok) * 1000))
    worst_ok = max(r[1] for r in ok)
    typ = res[0]
    if worst_ok < gate5:
        R.find("FAIL", "TEST_PLAN.md section 5 lets a hop of up to 40 mOhm per conductor pass, but in the sim even the typical "
               "corner (%.1f mOhm) leaves an ankle under 6.0 V for %.0f%% of the walk at a nominal pack, over the section 9 "
               "gate of 10%%; the 22 AWG made leads of contingency X1/X2 only reach %.0f%%; only about %.0f mOhm per conductor or "
               "less passes" % (typ[1] * 1000, typ[2], res[1][2], (est if est is not None else 0.011) * 1000),
               fix="TEST_PLAN.md: make the section 5 gate the hop value the section 9 gate needs (about 10 mOhm per conductor "
                   "in the sim), or say in section 9 that the nominal-pack ankle gate is expected to fail with the stock kit "
                   "cables and what is done then (options to try in the sim first: a second power feed into the free BUS 1 port of "
                   "ID 24 and ID 14 at the chain ends, or a source that does not drop out); the stop rule in section 9 (worse than the high-side corner) does not match its 10% pass line",
               where="altaay_lab/TEST_PLAN.md sections 5 and 9")
R.write()
