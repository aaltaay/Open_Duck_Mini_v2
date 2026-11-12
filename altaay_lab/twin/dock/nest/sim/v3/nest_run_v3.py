#!/usr/bin/env python3
"""nest_run_v3.py: mixed walk-in on the nest, and the edge and wall studies. sim pass only.

6.0 V uses the original steering walk-on (../nest_run.py). 7.2 V uses "line up, then cross the edge straight"
(../v2/nest_run_v2.py). Same seeds as the 540-run matrix (3 pose noise levels x 2 voltages x 3 mat frictions).

The world comes from ../nestlib.py. Two study switches, both off unless set here:

  NEST_EDGE     one (default, the archived 2 mm step) | steps (two 1 mm steps, 20 mm apart) | taper
  NEST_WALL_X   sun-to-wall distance in metres. Default 0.190. A study run may set 0.215.
                This does not change the approved 190 mm in any design record.
  AIM_MM        at 7.2 V only, aim this many millimetres to the right at the staging point.
                0 leaves the v2 default (no extra aim).
  ONLY_VOLT     if set (6.0 or 7.2), run only that voltage. Used for the small aim sweep.

  PYTHONDONTWRITEBYTECODE=1 python3 nest_run_v3.py N_PER_CELL [tag]
Writes nest_runs_<tag>.json in this folder. Use a new tag: the command overwrites that file.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
V2 = os.path.join(SIM, "v2")
sys.path.insert(0, V2)
sys.path.insert(0, SIM)

import nest_run as NR  # noqa: E402
import nest_run_v2 as R2  # noqa: E402

N = NR.N


def world_from_cfg(cfg):
    """apply this run's edge and wall before the model is built. Workers call this themselves."""
    os.environ["NEST_EDGE"] = cfg.get("edge", "one")
    N.WALL_X = float(cfg.get("wall_x", 0.190))


def job(cfg):
    world_from_cfg(cfg)
    try:
        if cfg["volt"] < 6.6:
            return NR.Run(cfg).go()
        c = dict(cfg)
        aim = float(cfg.get("aim_mm") or 0.0)
        if aim:
            v2 = dict(c.get("v2") or {})
            v2["aim_left"] = {"6.0": 0.0, "7.2": -aim / 1000.0}
            c["v2"] = v2
        return R2.Run2(c).go()
    except Exception as e:
        import traceback
        return dict(cfg=cfg, error=repr(e), tb=traceback.format_exc())


def configs(n, edge, wall_x, aim_mm, only_volt):
    J = []
    for c in NR.configs(n):
        if only_volt is not None and abs(c["volt"] - only_volt) > 0.05:
            continue
        c = dict(c)
        c["edge"] = edge
        c["wall_x"] = wall_x
        c["aim_mm"] = aim_mm
        J.append(c)
    return J


def run_all(J, path, meta):
    t = time.time()
    R = []
    with Pool(int(os.environ.get("JOBS", "4")), maxtasksperchild=6) as p:
        for i, r in enumerate(p.imap_unordered(job, J, chunksize=1)):
            R.append(r)
            if (i + 1) % 20 == 0:
                print(i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: r["cfg"]["seed"])
    doc = dict(label="sim pass only", controller="mixed: old steering at 6.0 V, straight crossing at 7.2 V",
               note="Study only. The approved sun-to-wall distance stays 190 mm. Nothing here is a hardware result.",
               params_v2_default=R2.P, **meta, runs=R)
    json.dump(doc, open(path, "w"))
    print("wrote", len(R), "runs", "%.0f s" % (time.time() - t), path)
    return R


if __name__ == "__main__":
    n = int(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else "mix"
    edge = os.environ.get("NEST_EDGE", "one")
    wall_x = float(os.environ.get("NEST_WALL_X", "0.190"))
    aim_mm = float(os.environ.get("AIM_MM", "0"))
    only = os.environ.get("ONLY_VOLT")
    only_volt = float(only) if only else None
    if edge not in N.EDGE_MODES:
        raise SystemExit("NEST_EDGE must be one, steps or taper")
    meta = dict(edge=edge, wall_x_m=wall_x, aim_mm_right_at_7v2=aim_mm, only_volt=only_volt,
                cell_m=N.HF_CELL, tread_m=N.TREAD if edge != "one" else 0.0)
    J = configs(n, edge, wall_x, aim_mm, only_volt)
    run_all(J, os.path.join(HERE, "nest_runs_%s.json" % tag), meta)
