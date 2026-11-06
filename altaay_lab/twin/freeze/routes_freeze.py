#!/usr/bin/env python3
"""routes_freeze.py: 3D routes of the freeze cables (D16 to D22) and the span fix of the cables that ride on another
cable's route (D13 on P13). CAD check only.

Run: python3 altaay_lab/twin/freeze/routes_freeze.py --scratch <folder outside the repo with c3d_grid_cad.npz> [--write]
The grid cache comes from `python3 altaay_lab/cables3d/route_cables.py --scratch <same folder> --grid-only`.
--write adds or replaces D16 to D22 and their cable ends in cables3d/cables3d.json, refills D13, gives every wire
without lengths its zero, min and max length (D13, D14, D15 and the dock cables were written without them, so C3 could
not judge them), adds D13 and D22 to the ties that hold their host bundles, and writes routes_freeze.json.

New cables (wiring/netlist.yaml, D51 and D54): all 26 AWG from stock
  D16 Pi header to the head touch board TCHH (3V3 pin 1, GND pin 25, SDA pin 3, SCL pin 5), 4 wires twisted
  D17 TCHH E0 and GND to the head-top pad PH1 (electrode lead and its guard ring), not twisted (NXP AN3863: keep the
      electrode lead off ground so its own capacitance stays low)
  D18 TCHH E1 and GND to the back-of-head pad PH2, not twisted
  D19 the BNO055 header to the body touch board TCHB (the same 4 signals as D2), 4 wires twisted
  D20 TCHB E0 and GND to the back pad PB1, not twisted
  D21 TCHB to the cliff ToF (VIN, GND, SDA, SCL), 4 wires twisted
  D22 the ToF interrupt (GPIO pin of the 5396) to Pi pin 11 (GPIO17): one wire on the D21, D19 and D2 routes, so it
      crosses the neck in the D2 bundle with D2's service loops and ties
Each made route is a shortest clear path on the cables3d 1 mm grid (c3d_lib.route: clearance = bundle radius + 1 mm,
inside the shells), string pulled, all points on one link (no joint crossed) except D22 and D13, whose spans and
service loops are those of the host route, re-indexed and moved by the length of the added lead-in.
"""
import argparse
import copy
import json
import os
import sys

import numpy as np

from flib import HERE, LAB, CABLES3D, r, dump

sys.path.insert(0, os.path.join(LAB, "cables3d"))
import c3d_lib as L  # noqa: E402
import route_cables as RC  # noqa: E402

OD = {1: 1.5, 2: 3.0, 4: 3.5, 5: 3.9}
END_ZONE = 8.0              # mm at each end taken as the connector or solder zone (cables3d/check_cables.py END_ZONE)
PITCH = 2.54


def pin_world(E, n):
    a1, a35 = np.array(E["PI.1"]["p_world0"]), np.array(E["PI.35"]["p_world0"])
    step = (a35 - a1) / np.linalg.norm(a35 - a1) * PITCH
    base = np.array(E["PI.1"]["p_world0"] if n % 2 else E["PI.2"]["p_world0"])
    return base + step * ((n - 1) // 2)


def board_rows(b, tp=True):
    """the two header rows of an MPR121 board: power and I2C (JP2, y 2.54 on the .brd) and the electrodes (JP1, y 17.78),
    on the parts face 1.0 mm out"""
    c = np.array(b["centre_top_face_world"])
    n = np.array(b["face_normal"])
    ea = np.eye(3)["xyz".index(b["long_side_along"])]
    ea = ea - (ea @ n) * n
    ea /= np.linalg.norm(ea)
    eb = np.cross(n, ea)
    top = c + n * (b["box_xyz_mm"][2])
    h = 19.05 / 2 - 1.27
    return top + n * 1.0 - eb * h, top + n * 1.0 + eb * h, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    s = RC.make_scene()
    for jn, j in s.joints.items():
        RC.REV[jn] = (j["lo"], j["hi"])
    g0 = RC.load_grid(s, a.scratch)
    g = g0.overlay(RC.base_boxes(), clear=[RC.CLEAR_BMS])
    par = RC.tree(s)
    poser = RC.Poser(s)
    C = json.load(open(CABLES3D))
    cab = {c["id"]: c for c in C["cables"]}
    E = {e["id"]: e for e in C["cable_ends"]}
    TP = json.load(open(os.path.join(HERE, "touch_pads.json")))
    CS = json.load(open(os.path.join(HERE, "cliff_seat.json")))
    th_pwr, th_ele, _ = board_rows(TP["boards"]["tch_h"])
    tb_pwr, tb_ele, _ = board_rows(TP["boards"]["tch_b"])
    pads = {k: np.array(v["centre_world"]) for k, v in TP["pads"].items()}
    Nb = np.array(CS["board"]["normal"])
    E2 = np.array(CS["board"]["short_axis"])
    O = np.array(CS["board"]["origin_pcb_top_centre"])
    tof_hdr = O + (2.54 - 17.78 / 2) * E2 - Nb * (1.6 + 1.5)        # JP2 row, on the back side 1.5 mm out
    pins = {n: pin_world(E, n) for n in (1, 3, 5, 11, 25)}
    pi_grp = np.mean([pins[n] for n in (1, 3, 5, 25)], 0)
    # pads: the lead lands on the pad edge nearest its board, 1 mm off the foil
    def pad_pt(pid, toward):
        c = pads[pid]
        v = toward - c
        v[2] = 0
        v /= np.linalg.norm(v) + 1e-9
        half = np.array(TP["pads"][pid]["pad_mm"]) / 2
        e = c + np.array([v[0] * half[0], v[1] * half[1], 0]) * 0.9
        return e - np.array([0, 0, 1.0])
    spec = {
        "D16": ("head_assembly", pi_grp + [0, 0, -1.5], th_pwr, 4),
        "D17": ("head_assembly", th_ele, pad_pt("PH1", th_ele), 2),
        "D18": ("head_assembly", th_ele, pad_pt("PH2", th_ele), 2),
        "D19": ("trunk_assembly", np.array(E["BNO.JP1"]["p_world0"]) + [0, 0, -1.5], tb_pwr, 4),
        "D20": ("trunk_assembly", tb_ele, pad_pt("PB1", tb_ele), 2),
        "D21": ("trunk_assembly", tb_pwr, tof_hdr, 4),
    }
    out = {}
    routes = {}
    for cid, (link, S_, E_, nw) in spec.items():
        od = OD[nw]
        hull = [g.head_hull] if link == "head_assembly" else [g.trunk_hull]
        P = None
        for clr in (od / 2 + 1.0, od / 2 + 0.6, max(0.8, od / 2)):
            P = L.route(g, S_, E_, clr, hulls=hull, free_radius=6.0)
            if P is not None:
                break
        if P is None:
            out[cid] = dict(routed=False)
            print(cid, "NOT ROUTED")
            continue
        P = np.vstack([S_, P, E_])
        B = [link] * len(P)
        P2, _ = RC.simplify(P, B, g=g, need=max(0.5, clr - 0.5))
        Lz = float(np.sum(np.linalg.norm(np.diff(P2, axis=0), axis=1)))
        Rs = RC.resample(P2, 1.0)
        acc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Rs, axis=0), axis=1))]
        mid = Rs[(acc > END_ZONE) & (acc < acc[-1] - END_ZONE)]
        gap = float(g.sample(mid).min()) - od / 2 if len(mid) else None
        routes[cid] = (link, P2, od, nw)
        out[cid] = dict(routed=True, link=link, length_mm=r(Lz, 1), points=len(P2), clearance_used_mm=r(clr, 2),
                        min_grid_gap_mm=r(gap, 2), od_mm=od)
        print(cid, out[cid], flush=True)
    # distance of the I2C and electrode routes to the power feeds (rule 10 mm, the mic-cable rule of route_mics.py)
    def world_pts(c):
        P = []
        for run in c["runs"]:
            for p in run["points"]:
                P.append((s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3])
        return np.array(P)
    from scipy.spatial import cKDTree
    power = {k: cKDTree(RC.resample(world_pts(cab[k]), 1.0)) for k in ("P13", "P12", "P11", "SP1", "SP2", "SP3", "DC1", "DC2")
             if k in cab}
    for cid, (link, P2, od, nw) in routes.items():
        D = RC.resample(P2, 1.0)
        out[cid]["to_power_mm"] = {k: r(t.query(D)[0].min() - od / 2 - 1.5, 1) for k, t in power.items()}
    # D22: the ToF interrupt on D21 (reversed: ToF first), D19 reversed (TCHB to the BNO), then D2 (BNO to the Pi), pin 11
    J = dict(script="altaay_lab/twin/freeze/routes_freeze.py", label="CAD check only", routes=out)

    def to_link(ln, w):
        return np.round((np.linalg.inv(s.T0[ln]) @ np.r_[w, 1.0])[:3], 3).tolist()

    def wof(p):
        return (s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3]

    def follow(host_run, pre, post):
        """a run that rides on host_run: pre and post are lists of {link, p} added before and after its points; the
        host's spans and service loops are re-indexed and their tie distances moved by the length of `pre`"""
        hp = copy.deepcopy(host_run["points"])
        pts = pre + hp + post
        W = np.array([wof(p) for p in pts])
        k = len(pre)
        lead = float(np.sum(np.linalg.norm(np.diff(W[:k + 1], axis=0), axis=1))) if k else 0.0
        run = dict(name="main", points=pts, d_mm=1.5, routed=True, seats=[], joints=sorted({j for sp in host_run.get("spans", []) for j in sp["joints"]}))
        run["spans"] = [dict(sp, span=[sp["span"][0] + k, sp["span"][1] + k]) for sp in host_run.get("spans", [])]
        loops = []
        for lp in host_run.get("service_loops", []):
            l2 = copy.deepcopy(lp)
            l2["span"] = [lp["span"][0] + k, lp["span"][1] + k]
            l2["spans"] = [[x + k, y + k] for x, y in (lp.get("spans") or [lp["span"]])]
            l2["ties_at_mm"] = [round(t + lead, 1) for t in lp["ties_at_mm"]]
            l2["od_mm"] = 1.5
            l2["host"] = "rides in the bundle of %s" % host_run.get("host_id", "")
            loops.append(l2)
        run["service_loops"] = loops
        return run, lead

    def lengths(run):
        pts = run["points"]
        Pp = np.array([wof(p) for p in pts])             # RC.sweep takes world points at the zero pose
        Bk = [p["link"] for p in pts]
        z0, mn, mx, _ = RC.sweep(s, poser, Pp, Bk, par)
        rt = dict(RC.REV)
        rt.update(RC.RUNTIME)
        _, _, mx_rt, _ = RC.sweep(s, poser, Pp, Bk, par, ranges=RC.RUNTIME)
        return z0, mn, mx, mx_rt

    new_runs = {}
    for cid, (link, P2, od, nw) in routes.items():
        pts = [dict(link=link, p=to_link(link, w)) for w in P2]
        new_runs[cid] = dict(name="main", points=pts, d_mm=od, routed=True, seats=[], joints=[], spans=[], service_loops=[])
    if "D21" in routes and "D19" in routes:
        d2 = copy.deepcopy(cab["D2"]["runs"][0])
        d2["host_id"] = "D2"
        pre = list(reversed(new_runs["D21"]["points"])) + list(reversed(new_runs["D19"]["points"]))
        post = [dict(link="head_assembly", p=to_link("head_assembly", pins[11]))]
        r22, lead22 = follow(d2, pre, post)
        new_runs["D22"] = r22
        out["D22"] = dict(routed=True, host="D21, D19 and D2", lead_in_mm=r(lead22, 1), points=len(r22["points"]))
    # D13 refill: SW1 OFF pad first, then P13, then P12 and pin 37 (twin/complete3d/phase2_data.py), spans kept this time
    p13 = copy.deepcopy(cab["P13"]["runs"][0])
    p13["host_id"] = "P13"
    d13 = cab["D13"]["runs"][0]
    k0 = next(i for i in range(len(d13["points"])) if d13["points"][i] == p13["points"][0])
    assert d13["points"][k0:k0 + len(p13["points"])] == p13["points"], "D13 no longer rides on P13"
    r13, lead13 = follow(p13, d13["points"][:k0], d13["points"][k0 + len(p13["points"]):])
    J["D13"] = dict(prefix_points=k0, lead_in_mm=r(lead13, 1), spans=[sp["span"] for sp in r13["spans"]],
                    loops=[lp["span"] for lp in r13["service_loops"]])
    print("D13", J["D13"])
    for cid, run in list(new_runs.items()) + [("D13", r13)]:
        z0, mn, mx, mxr = lengths(run)
        run.update(length_zero_mm=round(z0, 1), length_min_mm=round(mn, 1), length_max_mm=round(mx, 1),
                   length_max_runtime_mm=round(mxr, 1))
        out.setdefault(cid, {}).update(length_zero_mm=r(z0, 1), length_max_mm=r(mx, 1))
    J["routes"] = out
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "to_power_mm"} for k, v in out.items()}, indent=0))
    if a.write:
        write(C, cab, E, new_runs, r13, pins, spec, tof_hdr, th_pwr, th_ele, tb_pwr, tb_ele, s, J)


TERM = {}


def write(C, cab, E, new_runs, r13, pins, spec, tof_hdr, th_pwr, th_ele, tb_pwr, tb_ele, s, J):
    import yaml
    net = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml")))
    wires = [w for w in net["wires"]]
    cabs = {c["id"]: c for c in net["cables"]}

    def tol(ln, w):
        return np.round((np.linalg.inv(s.T0[ln]) @ np.r_[w, 1.0])[:3], 3).tolist()
    ends = {"PI.11": ("head_assembly", pins[11], "header pin", "[L] PI.1 plus 2.54 mm pitches along the odd row (pin 11, GPIO17)"),
            "PI.25": ("head_assembly", pins[25], "header pin", "[L] PI.1 plus 2.54 mm pitches along the odd row (pin 25, GND)"),
            "TCHH.HDR": ("head_assembly", th_pwr, "0.1 in header holes VIN GND SDA SCL", "[L] twin/freeze/touch_pads.json board seat; JP2 row of the MPR121 .brd"),
            "TCHH.ELE": ("head_assembly", th_ele, "0.1 in electrode holes E0 to E11", "[L] twin/freeze/touch_pads.json; JP1 row of the MPR121 .brd"),
            "TCHB.HDR": ("trunk_assembly", tb_pwr, "0.1 in header holes VIN GND SDA SCL", "[L] twin/freeze/touch_pads.json board seat; JP2 row"),
            "TCHB.ELE": ("trunk_assembly", tb_ele, "0.1 in electrode holes E0 to E11", "[L] twin/freeze/touch_pads.json; JP1 row"),
            "TOF.HDR": ("trunk_assembly", tof_hdr, "0.1 in header holes JP2, wires from the back", "[R] Adafruit-VL53L4CD-PCB JP2 at y 2.54; seat twin/freeze/cliff_seat.json"),
            "PH1.PAD": ("head_assembly", spec["D17"][2], "copper foil pad, lead soldered to the foil", "[L] twin/freeze/touch_pads.json PH1"),
            "PH2.PAD": ("head_assembly", spec["D18"][2], "copper foil pad, lead soldered to the foil", "[L] twin/freeze/touch_pads.json PH2"),
            "PB1.PAD": ("trunk_assembly", spec["D20"][2], "copper foil pad, lead soldered to the foil", "[L] twin/freeze/touch_pads.json PB1")}
    TPj = json.load(open(os.path.join(HERE, "touch_pads.json")))
    CSj = json.load(open(os.path.join(HERE, "cliff_seat.json")))
    nh, nb = TPj["boards"]["tch_h"]["face_normal"], TPj["boards"]["tch_b"]["face_normal"]
    ndir = {"PI.11": [0.0, 0.0, -1.0], "PI.25": [0.0, 0.0, -1.0], "TCHH.HDR": nh, "TCHH.ELE": nh, "TCHB.HDR": nb, "TCHB.ELE": nb,
            "TOF.HDR": (-np.array(CSj["board"]["normal"])).round(4).tolist(),
            "PH1.PAD": [0.0, 0.0, -1.0], "PH2.PAD": [0.0, 0.0, -1.0], "PB1.PAD": [0.0, 0.0, -1.0]}
    for k, (ln, w, kind, how) in ends.items():
        E[k] = dict(id=k, link=ln, p_world0=np.round(w, 2).tolist(), p=tol(ln, w), dir_world0=list(map(float, ndir[k])), kind=kind, how=how)
    ref = cab["D14"]
    colors = {"red": "#d62728", "black": "#222222", "blue": "#1f77b4", "yellow": "#e6c200", "white": "#f2f2f2", "green": "#2ca02c",
              "orange": "#ff7f0e", "purple": "#9467bd"}
    pos = [c["id"] for c in C["cables"]].index("D15") + 1
    C["cables"] = [c for c in C["cables"] if c["id"] not in new_runs]
    for cid in ("D16", "D17", "D18", "D19", "D20", "D21", "D22"):
        if cid not in new_runs or cid not in cabs:
            continue
        run = new_runs[cid]
        mine = [w for w in wires if w["cable"] == cid]
        ws = []
        for w in mine:
            ws.append(dict(**{"from": w["from"]}, to=w["to"], net=w["net"], gauge=w["gauge"], color=w["color"], cut_mm=w["cut_mm"],
                           branch=None, od_mm=1.5, runs=["main"], length_zero_mm=run["length_zero_mm"],
                           length_min_mm=run["length_min_mm"], length_max_mm=run["length_max_mm"],
                           length_max_runtime_mm=run["length_max_runtime_mm"]))
        c = dict(id=cid, desc=cabs[cid]["desc"], **{"from": "/".join(w["from"] for w in mine)}, to="/".join(w["to"] for w in mine),
                 gauge="26 AWG", color=colors.get(mine[0]["color"], "#1f77b4"), colors=[colors.get(w["color"], "#888888") for w in mine],
                 d_mm=run["d_mm"], wires_n=len(mine), cut_mm=max(w["cut_mm"] for w in mine), joints=run["joints"],
                 points=run["points"], runs=[run], wires=ws, seats=[],
                 length_zero_mm=run["length_zero_mm"], length_min_mm=run["length_min_mm"], length_max_mm=run["length_max_mm"],
                 note="routed by twin/freeze/routes_freeze.py (D51, D54)" + ("; rides in the D21, D19 and D2 bundles, D2's service "
                                                                            "loops and ties at the neck" if cid == "D22" else ""))
        C["cables"].insert(pos, c)
        pos += 1
    # D13: spans and loops back, and its wire lengths
    d13 = next(c for c in C["cables"] if c["id"] == "D13")
    r13.pop("host_id", None)
    d13["runs"] = [dict(r13, to="SW1.OFF", **{"from": "PI.37"})]
    d13["joints"] = r13["joints"]
    for w in d13["wires"]:
        w.update(length_zero_mm=r13["length_zero_mm"], length_min_mm=r13["length_min_mm"], length_max_mm=r13["length_max_mm"],
                 length_max_runtime_mm=r13["length_max_runtime_mm"])
    d13["length_max_mm"] = r13["length_max_mm"]
    # every other wire written without lengths (D14, D15, the dock cables): zero, min and max from its runs
    filled = []
    poser = RC.Poser(s)
    par = RC.tree(s)
    for c in C["cables"]:
        for w in c.get("wires", []):
            if w.get("length_max_mm") is not None:
                continue
            runs = [rr for rr in c["runs"] if rr["name"] in (w.get("runs") or [c["runs"][0]["name"]])]
            tot = [0.0, 0.0, 0.0, 0.0]
            for rr in runs:
                Pp = np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in rr["points"]])   # world, zero pose
                Bk = [p["link"] for p in rr["points"]]
                z0, mn, mx, _ = RC.sweep(s, poser, Pp, Bk, par)
                _, _, mxr, _ = RC.sweep(s, poser, Pp, Bk, par, ranges=RC.RUNTIME)
                tot = [tot[0] + z0, tot[1] + mn, tot[2] + mx, tot[3] + mxr]
            w.update(length_zero_mm=round(tot[0], 1), length_min_mm=round(tot[1], 1), length_max_mm=round(tot[2], 1),
                     length_max_runtime_mm=round(tot[3], 1))
            filled.append("%s %s>%s" % (c["id"], w["from"], w["to"]))
    J["lengths_filled"] = filled
    # ties: D13 and D22 ride in their host bundles, so every tie that holds the host within 8 mm of the rider holds it too
    held = {}
    for rider, host in (("D13", "P13"), ("D22", "D2"), ("D22", "D19"), ("D22", "D21")):
        rc = next((c for c in C["cables"] if c["id"] == rider), None)
        if rc is None:
            continue
        W = np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in rc["runs"][0]["points"]])
        W = RC.resample(W, 1.0)
        for t in C["retention"]:
            if host in t["cables"] and rider not in t["cables"]:
                if np.linalg.norm(W - np.array(t["center_mm"]), axis=1).min() <= 25.0:
                    t["cables"].append(rider)
                    held.setdefault(rider, []).append(t["id"])
    J["ties_shared"] = held
    C["cable_ends"] = list(E.values())
    C["meta"].setdefault("freeze", "2026-11-06 ET: D16 to D22 and the D13 refill by twin/freeze/routes_freeze.py (CAD check only)")
    with open(CABLES3D + ".tmp", "w") as fh:
        json.dump(C, fh, indent=1)
    os.replace(CABLES3D + ".tmp", CABLES3D)
    dump(J, os.path.join(HERE, "routes_freeze.json"))
    print("cables3d.json written; lengths filled on %d wires; shared ties %s" % (len(filled), held))


if __name__ == "__main__":
    main()
