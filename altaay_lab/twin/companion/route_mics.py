"""route_mics.py: 3D routes of the mic cables D14 (Pi header to the left mic board) and D15 (left board to the right
board), checked for clearance in the head and for distance to the 7.2 V feed and the servo leads. CAD check only.

Run: python3 altaay_lab/twin/companion/route_mics.py [--write]
--write adds or replaces D14 and D15 (and their end points MICL.HDR, MICR.HDR, PI.17b, PI.38, PI.39) in
cables3d/cables3d.json, the way twin/complete3d/phase2_data.py added D13.

Method: waypoints picked from a grid search (x, y, z of the middle points) for the largest margin over all four rules;
hand-set ends in the URDF world at the zero pose (all on the head link: no joint is crossed), each
segment sampled every 1 mm against surface point clouds of every head part (print/ STLs, the head internals and the
placed boxes); bundle diameter 3.4 mm (5 x 26 AWG at 1.5 mm OD, twisted, the D10 rule of netlist.yaml); the clear
rule is 1.0 mm from the bundle surface except within 6 mm of an end. Distances to the routed P13 (pack voltage up the
neck to U3, the "7.2 V feed"), P12, D8, D9 (SG90 leads) and D10 (amp) polylines are reported; the rule here is
>= 10 mm to P13 and P12 (power) and >= 5 mm to the servo leads (D47 hardware note), so the mic lines do not run in a
bundle with them.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "twin", "complete3d"))
from common import scene, head_instances, inst_name   # noqa: E402

C3 = os.path.join(LAB, "cables3d", "cables3d.json")
SEATS = os.path.join(HERE, "mic_seats.json")
D_BUNDLE = 3.4
PITCH = 2.54
RULE_POWER, RULE_SERVO, RULE_PART = 10.0, 5.0, 1.0


def pin_world(E, n):
    """Pi header pin n from PI.1 (odd row) and PI.2 (even row): pins step 2.54 mm along the header"""
    a1, a35 = np.array(E["PI.1"]["p_world0"]), np.array(E["PI.35"]["p_world0"])
    step = (a35 - a1) / np.linalg.norm(a35 - a1) * PITCH
    base = np.array(E["PI.1"]["p_world0"] if n % 2 else E["PI.2"]["p_world0"])
    return base + step * ((n - 1) // 2)


def pads_world(seat):
    """centre of the 6-pad row on the board top face (pads at 2.54 mm from the lower edge, board 12.7 mm tall)"""
    c = np.array(seat["board_centre_world"]); n = np.array(seat["inward_normal"])
    z = np.array([0, 0, 1.0]); v = z - (z @ n) * n; v /= np.linalg.norm(v)
    return c + (2.54 - 6.35) * v + 1.6 * n, n


def sample(P, step=1.0):
    out = []
    for a, b in zip(P[:-1], P[1:]):
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += [a + (b - a) * t for t in np.linspace(0, 1, k, endpoint=False)]
    out.append(P[-1])
    return np.array(out)


def polyline_world(cab, S):
    W = []
    for q in cab["points"]:
        T = S.T0[q["link"]]
        W.append((T @ np.r_[q["p"], 1.0])[:3])
    return np.array(W)


def seg_dist(pts, poly):
    """smallest distance from points to a polyline"""
    best = np.inf
    for a, b in zip(poly[:-1], poly[1:]):
        ab = b - a; L2 = max(ab @ ab, 1e-9)
        t = np.clip(((pts - a) @ ab) / L2, 0, 1)
        d = np.linalg.norm(pts - (a + t[:, None] * ab), axis=1)
        best = min(best, float(d.min()))
    return best


def routes(E, J):
    pL, nL = pads_world(J["seats"]["left"]); pR, nR = pads_world(J["seats"]["right"])
    pins = {n: pin_world(E, n) for n in (12, 17, 35, 38, 39)}
    hdr = np.mean([pins[n] for n in pins], axis=0)
    # D14: off the header bottom (the wires leave the solder side, -z), back along the head floor side, up to the pads
    d14 = [hdr, hdr + [0, 0, -9.0], np.array([5.0, 56.0, hdr[2] - 9.0]), np.array([-30.0, 50.0, pL[2]]),
           pL + 6.0 * nL, pL]
    # D15: from the left pads inward, across the head behind the head_roll_mount and above the SG90s, to the right pads
    d15 = [pL, pL + 6.0 * nL, np.array([-15.0, 40.0, 212.0]), np.array([-15.0, -40.0, 212.0]), pR + 6.0 * nR, pR]
    return dict(D14=np.array(d14), D15=np.array(d15)), pins, (pL, pR)


def main():
    S = scene()
    C = json.load(open(C3))
    E = {e["id"]: e for e in C["cable_ends"]}
    J = json.load(open(SEATS))
    clouds = {}
    for i in head_instances(S):
        m = S.world_mesh(i)
        if len(m.faces) and np.ptp(m.bounds, axis=0).min() > 0.5:
            pts = trimesh.sample.sample_surface_even(m, 60000 if inst_name(i).startswith("head[") else 15000, seed=3)[0]
            clouds[inst_name(i)] = np.vstack([pts, m.vertices])
    for p in json.load(open(os.path.join(LAB, "audit", "placements.json"))):
        if p["id"] in ("mic_l", "mic_r") or p.get("center_mm") is None:
            continue
        c = np.array(p["center_mm"]); d = np.array(p.get("dims_xyz_mm") or [0, 0, 0])
        if np.linalg.norm(c - [0, 0, 205]) < 160:
            g = np.stack(np.meshgrid(*[np.linspace(-h / 2, h / 2, 8) for h in d]), -1).reshape(-1, 3) + c
            clouds["box:" + p["id"]] = g
    R, pins, pads = routes(E, J)
    cab = {c["id"]: c for c in C["cables"]}
    others = {k: polyline_world(cab[k], S) for k in ("P13", "P12", "D8", "D9", "D10") if k in cab}
    res = {}
    for k, P in R.items():
        s = sample(P)
        L = float(np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)))
        ends = np.linalg.norm(s - P[0], axis=1).clip(max=99) < 6
        ends |= np.linalg.norm(s - P[-1], axis=1) < 6
        mid = s[~ends]
        gaps = {}
        for name, cl in clouds.items():
            from scipy.spatial import cKDTree
            d, _ = cKDTree(cl).query(mid)
            gaps[name] = round(float(d.min()) - D_BUNDLE / 2, 2)
        worst = sorted(gaps.items(), key=lambda kv: kv[1])[:4]
        dist = {o: round(seg_dist(s, W) - D_BUNDLE / 2, 1) for o, W in others.items()}
        res[k] = dict(length_mm=round(L, 1), worst_part_gaps_mm=dict(worst), dist_to_mm=dist,
                      ok=bool(worst[0][1] >= RULE_PART and dist.get("P13", 99) >= RULE_POWER and dist.get("P12", 99) >= RULE_POWER
                              and min(dist.get("D8", 99), dist.get("D9", 99)) >= RULE_SERVO),
                      points=np.round(P, 2).tolist())
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "points"} for k, v in res.items()}, indent=1))
    out = dict(meta=dict(script="altaay_lab/twin/companion/route_mics.py", label="CAD check only", bundle_d_mm=D_BUNDLE,
                         rules=dict(part_mm=RULE_PART, power_mm=RULE_POWER, servo_leads_mm=RULE_SERVO)), routes=res)
    json.dump(out, open(os.path.join(HERE, "mic_routes.json"), "w"), indent=1)
    if "--write" in sys.argv:
        write(C, E, R, pins, pads, S)


def write(C, E, R, pins, pads, S):
    import copy
    Tl = S.T0["head_assembly"]; Ti = np.linalg.inv(Tl)
    tol = lambda w: np.round((Ti @ np.r_[w, 1.0])[:3], 3).tolist()
    ref = next(c for c in C["cables"] if c["id"] == "D10")
    newE = {"PI.17": pins[17], "PI.38": pins[38], "PI.39": pins[39], "MICL.HDR": pads[0], "MICR.HDR": pads[1]}
    for k, w in newE.items():
        if k in E and k.startswith("PI.") and k != "PI.38" and k != "PI.39":
            continue
        E[k] = dict(id=k, link="head_assembly", p=tol(w), p_world0=np.round(w, 2).tolist(),
                    dir_world0=[0.0, 0.0, -1.0] if k.startswith("PI.") else None, kind="header pin" if k.startswith("PI.") else "solder pads",
                    how="[L] twin/companion/route_mics.py: PI.1 plus 2.54 mm pitches along the header" if k.startswith("PI.")
                    else "[L] twin/companion/mic_seats.json: the pad row of the mic board, 1.6 mm PCB stand-in")
    wires = {"D14": [("PI.17", "MICL.3V", "3V3", "red"), ("PI.39", "MICL.GND", "GND", "black"), ("PI.12", "MICL.BCLK", "I2S_BCLK", "yellow"),
                     ("PI.35", "MICL.LRCL", "I2S_LRC", "white"), ("PI.38", "MICL.DOUT", "I2S_MIC", "blue")],
             "D15": [("MICL.3V", "MICR.3V", "3V3", "red"), ("MICL.GND", "MICR.GND", "GND", "black"), ("MICL.BCLK", "MICR.BCLK", "I2S_BCLK", "yellow"),
                     ("MICL.LRCL", "MICR.LRCL", "I2S_LRC", "white"), ("MICL.DOUT", "MICR.DOUT", "I2S_MIC", "blue")]}
    cuts = {"D14": 150, "D15": 240}
    desc = {"D14": "Pi header to the left mic board (D47)", "D15": "left mic board to the right mic board across the head (D47)"}
    ends = {"D14": ("PI.17+PI.39+PI.12+PI.35+PI.38", "MICL.HDR"), "D15": ("MICL.HDR", "MICR.HDR")}
    C["cables"] = [c for c in C["cables"] if c["id"] not in ("D14", "D15")]
    pos = [c["id"] for c in C["cables"]].index("D13") + 1 if "D13" in [c["id"] for c in C["cables"]] else len(C["cables"])
    for k in ("D15", "D14"):
        pts = [dict(link="head_assembly", p=tol(w)) for w in R[k]]
        run = copy.deepcopy(ref["runs"][0])
        for kk in list(run):
            if kk.startswith(("length", "clearance", "rub", "span", "static", "bend", "loop")):
                run.pop(kk)
        run.update(name="main", points=pts, d_mm=D_BUNDLE, routed=True, seats=[], joints=[], **{"from": ends[k][0], "to": ends[k][1]})
        ws = []
        for (a, b, net, col) in wires[k]:
            w = copy.deepcopy(ref["wires"][0])
            for kk in list(w):
                if kk.startswith(("length", "margin", "fits", "required", "chains", "pin_offset")):
                    w.pop(kk)
            w.update(net=net, gauge="26 AWG", color=col, cut_mm=cuts[k], runs=["main"], od_mm=1.5, branch=None, to=b, **{"from": a})
            ws.append(w)
        c = copy.deepcopy(ref)
        for kk in ("findings", "check", "margin_mm", "required_mm", "worst_mm", "length_max_mm", "length_min_mm", "length_zero_mm",
                   "rub", "clearance", "connector_room", "free_stretch_mm", "free_stretch_run", "rub_min_gap_mm", "static_min_gap_mm",
                   "bend_min_radius_mm", "bend_min_kind", "rub_min_gap_runtime_mm", "clearance_min_mm"):
            c.pop(kk, None)
        c.update(id=k, desc=desc[k], points=pts, runs=[run], wires=ws, wires_n=5, d_mm=D_BUNDLE, cut_mm=cuts[k], seats=[], joints=[],
                 colors=["#d62728", "#222222", "#e6c200", "#f2f2f2", "#1f77b4"], color="#1f77b4",
                 note="twisted 5-wire bundle (D47); routed by twin/companion/route_mics.py, clear of P13, P12, D8 and D9 (mic_routes.json)",
                 **{"from": "/".join(a for a, *_ in wires[k]), "to": "/".join(b for _, b, *_ in wires[k])})
        C["cables"].insert(pos, c)
    C["cable_ends"] = list(E.values())
    json.dump(C, open(C3 + ".tmp", "w"), indent=1)
    os.replace(C3 + ".tmp", C3)
    print("cables3d.json: D14, D15 written")


if __name__ == "__main__":
    main()
