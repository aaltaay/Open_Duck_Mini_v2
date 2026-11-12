#!/usr/bin/env python3
"""sweep.py: small sweeps of the v2 walk-in settings. sim pass only.
Each setting runs the same subset of the main matrix: seeds k = 0..2 of every cell (54 runs) plus every seed that fell in
the original 540 (29 runs, all 7.2 V). The run stops before the turn (the walk-in is what the settings change).
  PYTHONDONTWRITEBYTECODE=1 python3 sweep.py NAME    -> sweep_NAME.json      (NAME is a key of SWEEPS)
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nest_run_v2 as R2  # noqa: E402

NR = R2.NR
V6 = lambda vx, rt="none", **k: dict(vx_cross={"6.0": vx, "7.2": 0.15}, retry={"6.0": rt, "7.2": "none"}, **k)  # noqa: E731
F_ = dict(stage_d=0.03, tol_yaw=4.0, aim_left={"6.0": -0.05, "7.2": -0.03}, fine_rounds=8, vx_cross={"6.0": 0.15, "7.2": 0.15}, retry={"6.0": "boost", "7.2": "none"}, vx_retry=0.18)
SWEEPS = {
    # candidates for the final setting: toes close to the edge, aim right (drift allowance), 6.0 V retry = boost to 0.18
    "final": [dict(F_, **x) for x in (dict(), dict(max_gap=0.060))],
    "stage2": [V6(0.18, stage_d=d, tol_yaw=4.0) for d in (0.25, 0.35)],
    # 6.0 V only, seeds k = 0..4 of the 9 cells at 6.0 V (45 runs): which forward command or retry gets the duck over the edge
    "cross6": [V6(0.15), V6(0.18), V6(0.18, "back"), V6(0.15, "wiggle")],
    # 7.2 V only (the 29 that fell and k = 0..2): the trained 0.15 against 0.30
    "cross7": [dict(vx_cross={"6.0": 0.15, "7.2": 0.15}), dict(vx_cross={"6.0": 0.15, "7.2": 0.30})],
    # staging distance (toes to the mat edge) and heading tolerance; crossing at 0.18 (6.0 V) and 0.15 (7.2 V)
    "stage": [V6(0.18, stage_d=d, tol_yaw=t) for d, t in ((0.03, 4.0), (0.08, 4.0), (0.16, 4.0), (0.08, 8.0))],
}


def subset():
    old = json.load(open(os.path.join(R2.L.PARENT, "nest_runs_main.json")))["runs"]
    fell = {r["cfg"]["seed"] for r in old if r.get("fell")}
    return [c for c in NR.configs(30) if c["k"] < 3 or c["seed"] in fell], fell


def summarize(rr, fell):
    ok = [r for r in rr if "pre_turn" in r]
    e = np.array([np.array(r["pre_turn"]["truth"][:2]) - np.array(r["pre_turn"]["target"]) for r in ok]) * 1000
    out = {}
    for nm, sel in (("all", lambda r: True), ("6.0 V", lambda r: r["cfg"]["volt"] == 6.0), ("7.2 V", lambda r: r["cfg"]["volt"] == 7.2),
                    ("the 29 that fell before", lambda r: r["cfg"]["seed"] in fell)):
        q = [r for r in rr if sel(r)]
        qo = [i for i, r in enumerate(ok) if sel(r)]
        ee = e[qo] if qo else np.zeros((0, 2))
        st = [r["stage"] for r in q if "stage" in r]
        out[nm] = dict(n=len(q), crashed=sum("error" in r for r in q), falls=sum(bool(r.get("fell")) for r in q),
                       falls_by_stage={k: sum(r.get("fall_stage") == k for r in q) for k in sorted({str(r.get("fall_stage")) for r in q if r.get("fell")})},
                       not_across=sum(("cross" in r and not r["cross"]["done"] and not r["fell"]) for r in q),
                       reached_turn_spot=len(qo),
                       runs_steering_on_edge=sum(bool(r.get("steer_on_edge_steps")) for r in q),
                       cross_retries=sum(r["cross"]["retries"] for r in q if "cross" in r),
                       stage_turn_moves_mean=round(float(np.mean([s["rounds"] for s in st])), 2) if st else None,
                       stage_toe_gap_mm=[round(float(np.min([s["toe_to_edge_mm"] for s in st])), 1), round(float(np.mean([s["toe_to_edge_mm"] for s in st])), 1)] if st else None,
                       turn_spot_err_x_mm=[round(float(ee[:, 0].mean()), 1), round(float(ee[:, 0].std()), 1)] if len(ee) else None,
                       turn_spot_err_y_mm=[round(float(ee[:, 1].mean()), 1), round(float(ee[:, 1].std()), 1)] if len(ee) else None,
                       turn_spot_err_rms_mm=round(float(np.sqrt((ee ** 2).sum(1).mean())), 1) if len(ee) else None,
                       turn_spot_err_max_mm=round(float(np.hypot(ee[:, 0], ee[:, 1]).max()), 1) if len(ee) else None,
                       heading_at_turn_spot_deg=[round(float(np.degrees(np.mean([ok[i]["pre_turn"]["truth"][2] for i in qo]))), 1),
                                                 round(float(np.degrees(np.std([ok[i]["pre_turn"]["truth"][2] for i in qo]))), 1)] if qo else None,
                       fine_rounds_mean=round(float(np.mean([ok[i]["fine_rounds"] for i in qo])), 2) if qo else None,
                       time_to_turn_start_s=round(float(np.mean([ok[i]["t_total_s"] for i in qo])), 1) if qo else None,
                       edge_cross_s=[round(float(np.mean([r["edge_cross_s"] for r in q if "edge_cross_s" in r])), 2),
                                     round(float(np.max([r["edge_cross_s"] for r in q if "edge_cross_s" in r])), 2),
                                     sum(r["edge_cross_s"] > 6 for r in q if "edge_cross_s" in r)] if any("edge_cross_s" in r for r in q) else None)
    return out


if __name__ == "__main__":
    name = sys.argv[1]
    base, fell = subset()
    if name == "cross6":
        base = [c for c in NR.configs(5) if c["volt"] == 6.0]
    if name == "final":
        base = [c for c in NR.configs(30) if (c["k"] < 5 and c["volt"] == 6.0) or (c["volt"] == 7.2 and (c["k"] < 3 or c["seed"] in fell))]
    if name == "cross7":
        base = [c for c in base if c["volt"] == 7.2]
    J = [dict(c, v2=v, stop_after="fine", trace=False) for v in SWEEPS[name] for c in base]
    path = os.path.join(HERE, "sweep_%s.json" % name)
    R = R2.run_all(J, path)
    S = []
    for v in SWEEPS[name]:
        key = json.dumps(v, sort_keys=True)
        rr = [r for r in R if json.dumps(r["cfg"].get("v2", {}), sort_keys=True) == key]
        S.append(dict(setting=v, result=summarize(rr, fell)))
        print(key)
        for k, x in S[-1]["result"].items():
            print("   ", k, x)
    d = json.load(open(path))
    d["summary"] = S
    d["subset"] = "seeds k = 0..2 of each of the 18 cells and the 29 seeds that fell in the original; stopped before the turn"
    json.dump(d, open(path, "w"))
