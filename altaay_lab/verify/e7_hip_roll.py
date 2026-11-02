"""E7: run print/check_hip_roll_screw.py (read only) and compare with decision D18.

D18: the outer servo-bag M2 screw in roll_motor_bottom overlaps the roll_to_pitch arm by about 1.3 mm over the whole
hip roll range on both legs, so it is left out; the inner screw stays. This check also reports the clearance of the
inner screw that stays in.
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e7_hip_roll.py
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E7", "Hip roll servo screw head vs roll_to_pitch over the hip roll range (print/check_hip_roll_screw.py)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e7_hip_roll.py",
             "Both legs, 2 screws each, 41 angles over the URDF hip roll range, M2 pan head 4.0 x 1.6 mm modelled",
             "Real head size of the Feetech bag screw (B2), print tolerance, the other screws (C4)")
js = os.path.join(V.out_dir(), "e7_hip_roll.json")
R.inp(V.lab("print", "check_hip_roll_screw.py"), V.lab("audit", "sites.json"), V.lab("audit", "assembly.json"))
p = subprocess.run(["nice", "-n", "10", sys.executable, V.lab("print", "check_hip_roll_screw.py"), "--json", js],
                   capture_output=True, text=True, timeout=3600)
if p.returncode != 0 or not os.path.exists(js):
    R.not_run("check_hip_roll_screw.py failed: " + (p.stdout + p.stderr)[-300:])
    R.write()
    sys.exit(0)
d = json.load(open(js))
for side in ("left", "right"):
    s = d[side]
    sc = s["screws"]
    over = [x for x in sc if x["overlap_deg"]]
    keep = [x for x in sc if not x["overlap_deg"]]
    R.ev("%s: range %.1f..%.1f deg; %s" % (side, *(v * 57.29578 for v in s["range_rad"]), "; ".join(
        "screw at y %+.1f: worst %.2f mm at %+.1f deg, overlap over %d of 41 angles" % (
            x["face"][1], x["worst_clearance"], x["worst_deg"], len(x["overlap_deg"])) for x in sc)))
    outer = max(sc, key=lambda x: abs(x["face"][1]))
    if outer["overlap_deg"] and all(abs(x["face"][1]) < abs(outer["face"][1]) for x in keep):
        R.ev("%s: the colliding screw is the outer one, as D18 says (overlap %.2f mm)" % (side, -outer["worst_clearance"]))
    else:
        R.find("FAIL", "%s: the colliding screw is not the outer one D18 leaves out" % side,
               fix="re-read D18 against print/check_hip_roll_screw.py output", where="altaay_lab/DECISIONS.md D18")
    if len(over) != 1:
        R.find("FAIL", "%s: %d screws collide (D18 expects exactly 1)" % (side, len(over)))
    for x in keep:
        if x["worst_clearance"] < 0.3:
            R.find("WARN", "%s: the inner screw D18 keeps clears roll_to_pitch by only %.2f mm (worst at %+.1f deg), inside "
                   "normal print tolerance" % (side, x["worst_clearance"], x["worst_deg"]),
                   fix="add to the first-leg check (print/PRINT_PLAN.md left-leg check, D18): sweep hip roll by hand with "
                       "the inner screw fitted and look for rubbing on roll_to_pitch",
                   where="altaay_lab/print/PRINT_PLAN.md")
kept = sorted(x["worst_clearance"] for side in ("left", "right") for x in d[side]["screws"] if not x["overlap_deg"])
hit = [x["worst_clearance"] for side in ("left", "right") for x in d[side]["screws"] if x["overlap_deg"]]
R.key("outer screw overlaps the arm by %s mm at every hip roll angle on both legs (as D18); the inner screw that stays clears "
      "it by %s mm" % (" and ".join("%.1f" % -h for h in hit), " and ".join("%.2f" % k for k in kept)))
R.write()
