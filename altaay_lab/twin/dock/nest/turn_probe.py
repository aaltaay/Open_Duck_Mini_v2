#!/usr/bin/env python3
"""turn_probe.py: how far does the duck drift while it turns on the spot? sim pass only.
The repo walk loop (sim/added_mass_sim.py run(): the stock BEST_WALK_ONNX_2 policy, unmodified MjInfer) on the repo's
sit model (twin/sit/sit_model.py, 2.8078 kg, built into a scratch folder; the repo is only read).
Open-loop schedule: 3 s forward at 0.15, 1.5 s zero command, then a constant turn command. From the log: where the trunk
origin is, relative to where the turn began, at the moment the heading has changed by 45, 90, 135 and 180 deg.

  PYTHONDONTWRITEBYTECODE=1 python3 turn_probe.py <scratch>/model
Writes turn_probe.json.
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))  # altaay_lab, relative to this file
T_FWD, T_STOP, T_TURN = 3.0, 1.5, 34.0


def job(a):
    wz, seed = a
    sys.path.insert(0, os.path.join(LAB, "twin", "sit"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    os.environ.setdefault("ODM_SCRATCH", os.path.join(OUT, "am_scratch"))
    import importlib
    import sit_model as SM
    AM = importlib.import_module("added_mass_sim")
    d = os.path.join(OUT, "sit")
    A = SM.assets(d)
    ga = lambda: A  # noqa: E731
    AM.CB.base.get_assets = ga
    sys.modules["playground.open_duck_mini_v2.base"].get_assets = ga
    AM._get_assets = ga
    t0 = T_FWD + T_STOP
    sched = lambda t: [0.15, 0, 0, 0, 0, 0, 0] if t < T_FWD else ([0, 0, 0, 0, 0, 0, 0] if t < t0 else [0, 0, wz, 0, 0, 0, 0])  # noqa: E731
    res = AM.run(d, "scene_flat_terrain.xml", sched, t0 + T_TURN, seed=seed)
    lg = res["log"]
    t, x, y, yaw = lg[:, 0], lg[:, 1], lg[:, 2], np.unwrap(lg[:, 4])
    i0 = int(np.searchsorted(t, t0))
    c, s = np.cos(yaw[i0]), np.sin(yaw[i0])
    out = dict(wz=wz, seed=seed, falls=res["falls"], fell_in_turn=bool([f for f in res["falls"] if f >= t0]), marks={})
    dy = np.degrees(yaw - yaw[i0])
    for ang in (45, 90, 135, 180):
        idx = np.where(np.abs(dy[i0:]) >= ang)[0]
        if not len(idx) or (res["falls"] and t[i0 + idx[0]] > res["falls"][0]):
            out["marks"][str(ang)] = None
            continue
        i = i0 + int(idx[0])
        dx_, dy_ = x[i] - x[i0], y[i] - y[i0]
        out["marks"][str(ang)] = dict(t_s=round(float(t[i] - t0), 2), fwd_mm=round(float((dx_ * c + dy_ * s) * 1000), 1),
                                      left_mm=round(float((-dx_ * s + dy_ * c) * 1000), 1), dist_mm=round(float(np.hypot(dx_, dy_) * 1000), 1))
    out["yaw_rate_deg_s"] = round(float(dy[-1] / T_TURN), 2) if not out["fell_in_turn"] else None
    return out


if __name__ == "__main__":
    J = [(wz, s) for wz in (1.0, -1.0, 0.5, -0.5) for s in range(10)]
    with Pool(8) as p:
        R = p.map(job, J)
    S = {}
    for wz in (1.0, -1.0, 0.5, -0.5):
        rows = [r for r in R if r["wz"] == wz]
        s = dict(n=len(rows), fell_in_turn=sum(r["fell_in_turn"] for r in rows),
                 yaw_rate_deg_s=[r["yaw_rate_deg_s"] for r in rows])
        for ang in ("45", "90", "135", "180"):
            m_ = [r["marks"][ang] for r in rows if r["marks"][ang]]
            if m_:
                f = np.array([q["fwd_mm"] for q in m_]); l_ = np.array([q["left_mm"] for q in m_]); dd = np.array([q["dist_mm"] for q in m_])
                s[ang] = dict(reached=len(m_), time_s_mean=round(float(np.mean([q["t_s"] for q in m_])), 1),
                              fwd_mm_mean=round(float(f.mean()), 1), fwd_mm_sd=round(float(f.std()), 1),
                              left_mm_mean=round(float(l_.mean()), 1), left_mm_sd=round(float(l_.std()), 1),
                              dist_mm_mean=round(float(dd.mean()), 1), dist_mm_max=round(float(dd.max()), 1),
                              scatter_about_mean_mm_max=round(float(np.hypot(f - f.mean(), l_ - l_.mean()).max()), 1))
            else:
                s[ang] = dict(reached=0)
        S[str(wz)] = s
        print(wz, json.dumps(s))
    json.dump(dict(label="sim pass only", model="repo sit model 2.8078 kg, stock walk policy, default floor (mu 0.6), 10 seeds per command, open loop",
                   summary=S, runs=R), open(os.path.join(HERE, "turn_probe.json"), "w"), indent=1)
