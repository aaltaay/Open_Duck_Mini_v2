#!/usr/bin/env python3
"""burst_probe.py: how small a move can the stock walk make? sim pass only.
On the mat (mu 0.8), from a standing stop: one command burst of n control steps (20 ms each), then zero command for 1.2 s.
Logged: the trunk shift in the heading frame at the start of the burst, and the yaw change. 4 seeds x 3 bursts in a row x 6.0 / 7.2 V per burst.
  PYTHONDONTWRITEBYTECODE=1 python3 burst_probe.py     -> burst_probe.json
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

CMDS = {"fwd 0.15": (0.15, 0, 0), "fwd 0.10": (0.10, 0, 0), "fwd 0.05": (0.05, 0, 0), "back 0.10": (-0.10, 0, 0), "back 0.15": (-0.15, 0, 0),
        "left 0.10": (0, 0.10, 0), "left 0.20": (0, 0.20, 0), "right 0.10": (0, -0.10, 0), "right 0.20": (0, -0.20, 0),
        "yaw +0.6": (0, 0, 0.6), "yaw -0.6": (0, 0, -0.6)}
NS = (10, 20, 30, 40, 60)


def job(a):
    name, n, seed, volt = a
    s = N.Sim(seed=seed, x0=-0.42, y0=0.0, yaw0=0.0, mu_mat=0.8, volt=volt, wall=False)
    for _ in range(120):
        s.step((0.15, 0, 0))
    for _ in range(60):
        s.step((0, 0, 0))
    out = []
    for rep in range(3):
        p0, _, _ = s.trunk_pose()
        c, sn = np.cos(p0[2]), np.sin(p0[2])
        for _ in range(n):
            s.step(CMDS[name])
        for _ in range(60):
            s.step((0, 0, 0))
        p1, _, _ = s.trunk_pose()
        d = p1[:2] - p0[:2]
        out.append([float(d[0] * c + d[1] * sn) * 1000, float(-d[0] * sn + d[1] * c) * 1000, float(np.degrees(N.wrap(p1[2] - p0[2])))])
    return dict(cmd=name, n=n, seed=seed, volt=volt, fell=s.fallen, moves=out)


if __name__ == "__main__":
    J = [(c, n, sd, v) for c in CMDS for n in NS for sd in range(4) for v in (6.0, 7.2)]
    with Pool(4) as p:
        R = p.map(job, J, chunksize=4)
    S = []
    for c in CMDS:
        for n in NS:
            for v in (6.0, 7.2):
                M = np.array([m for r in R if r["cmd"] == c and r["n"] == n and r["volt"] == v for m in r["moves"]])
                row = dict(cmd=c, steps=n, secs=n * 0.02, volt=v, falls=sum(r["fell"] for r in R if r["cmd"] == c and r["n"] == n and r["volt"] == v),
                           fwd_mm=[round(float(M[:, 0].mean()), 1), round(float(M[:, 0].std()), 1)], left_mm=[round(float(M[:, 1].mean()), 1), round(float(M[:, 1].std()), 1)],
                           yaw_deg=[round(float(M[:, 2].mean()), 1), round(float(M[:, 2].std()), 1)])
                S.append(row)
                print(c, n, v, row['falls'], row['fwd_mm'], row['left_mm'], row['yaw_deg'])
    json.dump(dict(label="sim pass only", note="mean, sd over 12 bursts (4 seeds x 3 in a row)", summary=S, runs=R), open(os.path.join(HERE, "burst_probe.json"), "w"), indent=1)
