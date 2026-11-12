#!/usr/bin/env python3
"""edge_control.py: are the walk-on falls caused by the mat edge? sim pass only.
Re-runs every run of nest_runs_main.json that fell, same seed and settings, with the mat taken away (flat floor, the same
wall, rim and controller). If the fall goes away, the 2 mm edge was the cause.
  PYTHONDONTWRITEBYTECODE=1 python3 edge_control.py    -> edge_control.json
"""
import json
import os
import sys
from multiprocessing import Pool

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nest_run as NR  # noqa: E402

if __name__ == "__main__":
    R = json.load(open(os.path.join(HERE, "nest_runs_main.json")))["runs"]
    F = [r for r in R if r.get("fell") and r.get("fall_stage") not in ("walk_off", "walk_off_stand")]
    J = [dict(r["cfg"], mat=False, trace=False) for r in F]
    with Pool(4, maxtasksperchild=6) as p:
        Q = p.map(NR.job, J, chunksize=1)
    out = [dict(cfg=q["cfg"], fell=q.get("fell"), fall_stage=q.get("fall_stage"), reached_sit=bool(q.get("sits")), error=q.get("error")) for q in Q]
    S = dict(runs_that_fell_with_the_mat=len(F), fell_again_without_the_mat=sum(bool(o["fell"]) for o in out), reached_the_sit_without_the_mat=sum(o["reached_sit"] for o in out))
    print(S)
    json.dump(dict(label="sim pass only", summary=S, runs=out), open(os.path.join(HERE, "edge_control.json"), "w"), indent=1)
