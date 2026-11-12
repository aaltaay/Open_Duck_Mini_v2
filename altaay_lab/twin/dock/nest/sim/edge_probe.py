#!/usr/bin/env python3
"""edge_probe.py: does the 2 mm mat edge trip the stock walk? sim pass only.
Straight walks at command 0.15 from the room over the mat edge (inbound, 12 s), and from the mat centre out over the edge
(outbound, 10 s), heading +/-10 deg, lateral +/-80 mm. The edge is one height-field cell wide: run once per cell size with
NEST_CELL=0.005 (2 mm over 5 mm, the main runs) and NEST_CELL=0.0025 (2 mm over 2.5 mm, closer to a square step).
10 seeds x 6.0 / 7.2 V x mat friction 0.6 / 1.0 per direction.
  NEST_CELL=0.005 PYTHONDONTWRITEBYTECODE=1 python3 edge_probe.py   -> edge_probe_<cell>.json
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestlib as N  # noqa: E402


def job(a):
    way, seed, volt, mu = a
    rng = np.random.default_rng(300 + seed)
    yaw = np.radians(rng.uniform(-10, 10))
    y0 = rng.uniform(-0.08, 0.08)
    if way == "in":
        s = N.Sim(seed=seed, x0=-0.60, y0=y0, yaw0=yaw, mu_mat=mu, mu_floor=0.6, volt=volt, wall=False)
        T = 12.0
    else:
        s = N.Sim(seed=seed, x0=0.0, y0=y0 * 0.5, yaw0=np.pi + yaw, mu_mat=mu, mu_floor=0.6, volt=volt, wall=False)
        T = 10.0
    for _ in range(50):
        s.step((0, 0, 0))
    start_fall = s.fallen
    t_in = t_out = None
    for _ in range(int(T * 50)):
        s.step((0.15, 0, 0))
        p, _, _ = s.trunk_pose()
        r = float(np.hypot(p[0], p[1]))
        lo, hi = (0.17, 0.33)
        if way == "in":
            if t_in is None and r < hi: t_in = s.t
            if t_in is not None and t_out is None and r < lo: t_out = s.t
        else:
            if t_in is None and r > lo: t_in = s.t
            if t_in is not None and t_out is None and r > hi: t_out = s.t
        if s.fallen:
            break
    p, _, _ = s.trunk_pose()
    return dict(way=way, seed=seed, volt=volt, mu=mu, start_artefact=bool(start_fall), fell=bool(s.fallen and not start_fall), crossed=bool(t_out is not None and not s.fallen),
                cross_s=(round(t_out - t_in, 2) if t_out else None), end=[float(p[0]), float(p[1])], edge_touches=len(s.events["edge"]))


if __name__ == "__main__":
    J = [(w, sd, v, mu) for w in ("in", "out") for v in (6.0, 7.2) for mu in (0.6, 1.0) for sd in range(10)]
    with Pool(int(os.environ.get("JOBS", "4"))) as p:
        R = p.map(job, J)
    S = []
    for w in ("in", "out"):
        for v in (6.0, 7.2):
            rr = [r for r in R if r["way"] == w and r["volt"] == v and not r["start_artefact"]]
            cs = [r["cross_s"] for r in rr if r["cross_s"]]
            row = dict(way=w, volt=v, n=len(rr), crossed=sum(r["crossed"] for r in rr), falls=sum(r["fell"] for r in rr),
                       cross_160mm_s=[round(float(np.mean(cs)), 2), round(float(np.max(cs)), 2)] if cs else None,
                       edge_touches_mean=round(float(np.mean([r["edge_touches"] for r in rr])), 1))
            S.append(row)
            print(row)
    json.dump(dict(label="sim pass only", cell_m=N.HF_CELL, edge="2 mm rise over one cell", summary=S, runs=R),
              open(os.path.join(HERE, "edge_probe_%s.json" % ("%g" % (N.HF_CELL * 1000)).replace(".", "p")), "w"), indent=1)
