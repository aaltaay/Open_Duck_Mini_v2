#!/usr/bin/env python3
"""cross_probe.py: straight walks over the 2 mm mat edge, zero turn and zero lateral command. sim pass only.
Which forward command and which retry gets a 6.0 V duck over the edge, and does it cost falls at 7.2 V?
Start: trunk 0.60 m before the sun centre, lateral +/-60 mm, heading aimed at the sun centre +/-6 deg (so no walk clips the
side of the round mat, which ../edge_probe.py allowed), 20 s limit. Ends when both soles are wholly on the mat (truth).
20 seeds x mat friction 0.6 / 0.8 / 1.0 x 6.0 / 7.2 V = 120 walks per variant.
  PYTHONDONTWRITEBYTECODE=1 python3 cross_probe.py [variant ...]   -> cross_probe.json (variants are merged into the file)
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v2lib as L  # noqa: E402
N = L.N

# variant: forward command far from the edge, forward command in the edge zone, retry rule
#   retry None; "pause": on a stall stand 1 s and go again; "back": on a stall step back 1.5 s, stand 0.5 s, go again;
#   "boost": on a stall raise the forward command to vx_retry
#   "wiggle": on a stall keep walking and add a turn command wz for 1 s, the sign alternates (this breaks the zero-turn rule)
#   "turnonly": on a stall a turn command alone for 1 s, no forward command, the sign alternates
#   "side": on a stall a left side-step command 0.2 alone for 0.8 s (there is no right side-step)
VAR = {
    "v0.15": dict(vx=0.15),
    "v0.20": dict(vx=0.20),
    "v0.25": dict(vx=0.25),
    "v0.30": dict(vx=0.30),
    "v0.15_pause": dict(vx=0.15, retry="pause"),
    "v0.15_back": dict(vx=0.15, retry="back"),
    "v0.15_boost0.25": dict(vx=0.15, retry="boost", vx_retry=0.25),
    "v0.15_boost0.30": dict(vx=0.15, retry="boost", vx_retry=0.30),
    "v0.15_boost0.18": dict(vx=0.15, retry="boost", vx_retry=0.18),
    "v0.20_back": dict(vx=0.20, retry="back"),
    "v0.20_pause": dict(vx=0.20, retry="pause"),
    "v0.17": dict(vx=0.17),
    "v0.18": dict(vx=0.18),
    "v0.15_wiggle0.3": dict(vx=0.15, retry="wiggle", wz=0.3),
    "v0.15_wiggle0.6": dict(vx=0.15, retry="wiggle", wz=0.6),
    "v0.15_side": dict(vx=0.15, retry="side"),
    "v0.15_turnonly0.6": dict(vx=0.15, retry="turnonly", wz=0.6),
    "v0.10": dict(vx=0.10),
    "v0.12": dict(vx=0.12),
}
STALL_T, STALL_D = 1.5, 0.015          # a stall: less than 15 mm of trunk travel in 1.5 s


def job(a):
    name, seed, volt, mu = a
    v = VAR[name]
    rng = np.random.default_rng(300 + seed)
    y0 = rng.uniform(-0.06, 0.06)
    yaw = np.arctan2(-y0, 0.60) + np.radians(rng.uniform(-6, 6))      # aimed at the sun centre, +/-6 deg off
    s = N.Sim(seed=seed, x0=-0.60, y0=y0, yaw0=yaw, mu_mat=mu, mu_floor=0.6, volt=volt, wall=False)
    for _ in range(50):
        s.step((0, 0, 0))
    if s.fallen:
        return dict(var=name, seed=seed, volt=volt, mu=mu, start_artefact=True)
    p0 = s.trunk_pose()[0].copy()
    hist = []
    t_touch = t_on = None
    retries = 0
    vx = v["vx"]
    mode, t_mode = "go", s.t
    t0 = s.t
    while s.t - t0 < 20.0 and not s.fallen:
        if mode == "go":
            cmd = (vx, 0, 0)
        elif mode == "pause":
            cmd = (0, 0, 0)
            if s.t - t_mode > 1.0:
                mode, t_mode, hist = "go", s.t, []
        elif mode in ("wiggle", "turnonly", "side"):
            sg = 1 if retries % 2 else -1
            cmd = (vx, 0, sg * v["wz"]) if mode == "wiggle" else (0, 0, sg * v["wz"]) if mode == "turnonly" else (0, 0.2, 0)
            if s.t - t_mode > (0.8 if mode == "side" else 1.0):
                mode, t_mode, hist = "go", s.t, []
        elif mode == "back":
            cmd = (-0.15, 0, 0) if s.t - t_mode < 1.5 else (0, 0, 0)
            if s.t - t_mode > 2.0:
                mode, t_mode, hist = "go", s.t, []
        s.step(cmd)
        p = s.trunk_pose()[0]
        fs = L.feet_state(s, 0.005)
        if t_touch is None and fs != ["off", "off"]:
            t_touch = s.t
        if fs == ["on", "on"]:
            t_on = s.t
            break
        if p[0] > 0.10:
            break
        if mode == "go":
            hist.append((s.t, p[0], p[1]))
            while hist and s.t - hist[0][0] > STALL_T:
                hist.pop(0)
            if v.get("retry") and s.t - t_mode > STALL_T and np.hypot(p[0] - hist[0][1], p[1] - hist[0][2]) < STALL_D:
                retries += 1
                if v["retry"] == "boost":
                    vx = v["vx_retry"]
                    t_mode, hist = s.t, []
                else:
                    mode, t_mode = v["retry"], s.t
    p = s.trunk_pose()[0]
    d = L.N.wrap(p[2] - p0[2])
    e = np.array([[np.cos(p0[2]), np.sin(p0[2])], [-np.sin(p0[2]), np.cos(p0[2])]]) @ (p[:2] - p0[:2])
    # 1 s more straight on the mat: does it stay up after the crossing?
    if t_on is not None:
        for _ in range(50):
            s.step((0.15, 0, 0))
    return dict(var=name, seed=seed, volt=volt, mu=mu, start_artefact=False, fell=bool(s.fallen), crossed=bool(t_on is not None and not s.fallen),
                t_to_edge_s=(round(t_touch - t0, 2) if t_touch else None), edge_s=(round(t_on - t_touch, 2) if t_on and t_touch else None),
                total_s=(round(t_on - t0, 2) if t_on else None), retries=retries, fwd_mm=round(float(e[0]) * 1000, 1), left_mm=round(float(e[1]) * 1000, 1),
                yaw_deg=round(float(np.degrees(d)), 2), edge_touches=len(s.events["edge"]))


def summary(R):
    S = []
    for name in VAR:
        for v in (6.0, 7.2):
            rr = [r for r in R if r["var"] == name and r["volt"] == v and not r["start_artefact"]]
            if not rr:
                continue
            ok = [r for r in rr if r["crossed"]]
            es = [r["edge_s"] for r in ok]
            S.append(dict(var=name, volt=v, n=len(rr), crossed=len(ok), falls=sum(r["fell"] for r in rr), not_over_in_20s=sum((not r["crossed"]) and not r["fell"] for r in rr),
                          edge_s_mean=round(float(np.mean(es)), 2) if es else None, edge_s_p95=round(float(np.percentile(es, 95)), 2) if es else None,
                          edge_s_max=round(float(np.max(es)), 2) if es else None, slower_than_6s=sum(e > 6 for e in es), retries_mean=round(float(np.mean([r["retries"] for r in rr])), 2),
                          left_mm=[round(float(np.mean([r["left_mm"] for r in ok])), 1), round(float(np.std([r["left_mm"] for r in ok])), 1)] if ok else None,
                          yaw_deg=[round(float(np.mean([r["yaw_deg"] for r in ok])), 2), round(float(np.std([r["yaw_deg"] for r in ok])), 2)] if ok else None,
                          fwd_mm=round(float(np.mean([r["fwd_mm"] for r in ok])), 1) if ok else None))
    return S


if __name__ == "__main__":
    names = sys.argv[1:] or list(VAR)
    path = os.path.join(HERE, "cross_probe.json")
    R = json.load(open(path))["runs"] if os.path.exists(path) else []
    R = [r for r in R if r["var"] not in names]
    a, b = map(int, os.environ.get("SEEDS", "0:20").split(":"))             # more seeds can be added later for a variant
    volts = [float(x) for x in os.environ.get("VOLTS", "6.0,7.2").split(",")]
    if a > 0:
        R = json.load(open(path))["runs"]
        R = [r for r in R if not (r["var"] in names and r["volt"] in volts and a <= r["seed"] < b)]
    J = [(nm, sd, v, mu) for nm in names for v in volts for mu in (0.6, 0.8, 1.0) for sd in range(a, b)]
    with Pool(int(os.environ.get("JOBS", "4")), maxtasksperchild=20) as p:
        R += p.map(job, J, chunksize=2)
    S = summary(R)
    for r in S:
        print(r)
    json.dump(dict(label="sim pass only", stall_rule="less than 15 mm of trunk travel in 1.5 s", summary=S, runs=R), open(path, "w"), indent=1)
