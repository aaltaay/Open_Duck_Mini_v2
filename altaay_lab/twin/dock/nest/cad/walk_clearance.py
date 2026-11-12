#!/usr/bin/env python3
"""walk_clearance.py: how high the four pin tips are above the floor while the duck stands, walks and turns.
sim pass only (the walk), CAD check only (the tip positions from duck_pins.json).

The repo walk loop (altaay_lab/sim/added_mass_sim.py run(): stock BEST_WALK_ONNX_2, unmodified MjInfer) on the repo's sit
model (twin/sit/sit_model.py, built into a scratch folder: python3 altaay_lab/twin/sit/sit_model.py --out <scratch>/model),
the method of dock/natural/turn_probe.py. The pins are not in the sim model: the tip heights are computed from the
logged trunk pose (plunger free, fully out). Flat floor, no mat.

  PYTHONDONTWRITEBYTECODE=1 python3 walk_clearance.py <scratch>/model
Writes walk_clearance.json.
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))  # altaay_lab, relative to this file
SEG = [("stand", 2.0, [0, 0, 0]), ("walk forward 0.15", 6.0, [0.15, 0, 0]), ("stop", 2.0, [0, 0, 0]), ("turn left 1.0", 6.0, [0, 0, 1.0]),
       ("stop 2", 2.0, [0, 0, 0]), ("turn right 1.0", 6.0, [0, 0, -1.0]), ("stop 3", 2.0, [0, 0, 0])]


def seg_at(t):
    a = 0.0
    for nm, d, c in SEG:
        if t < a + d:
            return nm, c
        a += d
    return SEG[-1][0], SEG[-1][2]


def job(a):
    out, seed = a
    sys.path.insert(0, os.path.join(LAB, "twin", "sit"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    os.environ.setdefault("ODM_SCRATCH", os.path.join(out, "am_scratch"))
    import importlib
    import sit_model as SM
    AM = importlib.import_module("added_mass_sim")
    d = os.path.join(out, "sit")
    A = SM.assets(d)
    ga = lambda: A  # noqa: E731
    AM.CB.base.get_assets = ga
    sys.modules["playground.open_duck_mini_v2.base"].get_assets = ga
    AM._get_assets = ga
    sched = lambda t: list(seg_at(t)[1]) + [0, 0, 0, 0]  # noqa: E731
    res = AM.run(d, "scene_flat_terrain.xml", sched, sum(s[1] for s in SEG), seed=seed)
    return seed, res["falls"], res["log"]


def main():
    from scipy.spatial.transform import Rotation
    out = sys.argv[1]
    P = json.load(open(os.path.join(HERE, "duck_pins.json")))
    tips = {k: np.array(v["tip_free_trunk_mm"]) / 1000.0 for k, v in P["pins"].items()}
    faces = {k: np.array(v["block_face_trunk_mm"]) / 1000.0 for k, v in P["pins"].items()}
    with Pool(4) as p:
        R = p.map(job, [(out, s) for s in (None, 1, 2, 3)])
    rows = {}
    falls = {}
    for seed, fl, lg in R:
        falls[str(seed)] = fl
        t = lg[:, 0]
        Rm = Rotation.from_euler("ZYX", lg[:, 4:7]).as_matrix()
        for nm, _, _ in SEG:
            sel = np.array([seg_at(x)[0] == nm for x in t]) & (t > 1.0) & (lg[:, 10] == 0)
            if not sel.any():
                continue
            r_ = rows.setdefault(nm, dict(tip={k: [] for k in tips}, face={k: [] for k in tips}, trunk_z=[], pitch=[], roll=[]))
            for k in tips:
                r_["tip"][k].append(float((lg[sel, 3] + Rm[sel, 2, :] @ tips[k]).min() * 1000))
                r_["face"][k].append(float((lg[sel, 3] + Rm[sel, 2, :] @ faces[k]).min() * 1000))
            r_["trunk_z"].append([float(lg[sel, 3].min() * 1000), float(lg[sel, 3].max() * 1000)])
            r_["pitch"].append([float(np.degrees(lg[sel, 5]).min()), float(np.degrees(lg[sel, 5]).max())])
            r_["roll"].append([float(np.degrees(lg[sel, 6]).min()), float(np.degrees(lg[sel, 6]).max())])
    S = {}
    for nm, r_ in rows.items():
        S[nm] = dict(tip_min_mm={k: round(min(v), 1) for k, v in r_["tip"].items()}, block_face_min_mm={k: round(min(v), 1) for k, v in r_["face"].items()},
                     trunk_z_mm=[round(min(a for a, _ in r_["trunk_z"]), 1), round(max(b for _, b in r_["trunk_z"]), 1)],
                     pitch_deg=[round(min(a for a, _ in r_["pitch"]), 1), round(max(b for _, b in r_["pitch"]), 1)],
                     roll_deg=[round(min(a for a, _ in r_["roll"]), 1), round(max(b for _, b in r_["roll"]), 1)], runs=len(r_["trunk_z"]))
    low = min(min(v["tip_min_mm"].values()) for v in S.values())
    json.dump(dict(label="sim pass only (trunk pose of the stock walk on a flat floor, 4 runs); CAD check only (tip positions, plunger free)",
                   schedule=[(a, b) for a, b, _ in SEG], falls=falls, segments=S, lowest_tip_any_segment_mm=round(low, 1)),
              open(os.path.join(HERE, "walk_clearance.json"), "w"), indent=1)
    for k, v in S.items():
        print("%-20s tips %s  trunk z %s pitch %s roll %s" % (k, v["tip_min_mm"], v["trunk_z_mm"], v["pitch_deg"], v["roll_deg"]))
    print("falls", falls, "lowest tip", low)


if __name__ == "__main__":
    main()
