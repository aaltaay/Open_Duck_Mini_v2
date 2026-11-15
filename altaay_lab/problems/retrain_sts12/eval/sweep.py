#!/usr/bin/env python3
"""Constant-command 60 s em_twin walks with the same settings as run_twin.walk():
mass ours (2.949 kg), held 12.0 V rail, 3S P45B, sheet servo, guard act, typical corner.
usage: ODM_ONNX=<onnx> ODM_PLAYGROUND=<pin> python sweep.py <repo_tree> <out.json> [dur]
Sim pass only."""
import json, os, sys, tempfile, multiprocessing as mp
TREE = sys.argv[1]; OUT = sys.argv[2]; DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
CMDS = [0.10, 0.15, 0.20, 0.25, 0.30]

def one(c):
    LAB = os.path.join(TREE, "altaay_lab")
    sys.path.insert(0, TREE)
    onnx = os.environ.get("ODM_ONNX")
    if not onnx or not os.path.isfile(onnx):
        raise SystemExit("Set ODM_ONNX to the policy file before starting this sweep")
    scratch = tempfile.mkdtemp(prefix="sweep_")
    os.environ["TWIN_EM_SCRATCH"] = scratch
    os.environ["ODM_SCRATCH"] = os.path.join(scratch, "models")
    os.environ["ODM_OUT"] = os.path.join(scratch, "cb_out")
    from altaay_lab.twin import parts_truth as PT
    parts = PT.load()
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    import sts12  # noqa
    import em_twin as ET
    # current_budget freezes ONNX at import. Assign the requested file after that import.
    ET.CB.ONNX = os.path.realpath(onnx)
    if os.path.realpath(ET.CB.ONNX) != os.path.realpath(onnx):
        raise SystemExit("sweep did not bind the requested policy")
    extra = dict(BEC_V=float(parts["regulator"]["v_set"]), BEC_EFF=float(parts["regulator"]["eff_used"]),
                 BEC_HOLD=1 if parts["regulator"]["holds"] else 0)
    r = ET.run(mass="ours", walk="backlash", cmd=(c, 0.0, 0.0), dur=DUR, supply="net", corner="typical", extra=extra,
               cell="p45b3", q0=0.0, servo_mode="sheet", guard="act", keep_full=False, bin_s=0.1, stop_on_fall=False,
               t_stats=4.0, label="sweep %.2f" % c, pack_floor=True)
    names = r["names"]; im = r["servo"]["Im_rms"]
    kl, kr = names.index("left_knee"), names.index("right_knee")
    return dict(cmd=c, falls=r["falls"], vx=r["gait"]["vx"], pitch_rms_deg=r["gait"]["pitch_rms_deg"], roll_rms_deg=r["gait"]["roll_rms_deg"],
                knee_rms_A=[im[kl], im[kr]], all_rms_A=dict(zip(names, im)), pack=r.get("pack"), onnx=os.path.basename(os.environ["ODM_ONNX"]))

if __name__ == "__main__":
    with mp.get_context("spawn").Pool(len(CMDS)) as p:
        rows = p.map(one, CMDS)
    json.dump(dict(label="sim pass only", dur_s=DUR, rows=rows), open(OUT, "w"), indent=1)
    for row in rows:
        print(row["cmd"], row["falls"], row["vx"], row["knee_rms_A"], (row["pack"] or {}).get("i_max"))
