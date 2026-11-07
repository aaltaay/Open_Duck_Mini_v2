#!/usr/bin/env python3
"""sit_sweep.py: the full mesh collision sweep of the A1b sit (D59). CAD check only.

Run: python3 altaay_lab/twin/sit/sit_sweep.py [--walk walk_joints.json] [--quick]
Writes altaay_lab/twin/sit/sit_sweep.json.

Inputs are read now from the repo (never a cache): robot.urdf (the joint ranges and the parts each link carries) and
the print/ STLs through cables3d/c3d_lib.Scene, with every servo case filled solid (c3d_lib.SERVO_INNER), as the v1
study did. Exact meshes: manifold3d intersection volumes and gaps, no voxels.

States:
  path      the A1b sit and stand path (sitlib.PATH_A1B) at 1 deg steps of the largest joint move, both legs, with the
            head forward waypoints at the software limits; the torque-off settle onto the stops (knee 150, ankle -95,
            hip roll at its outward stop, hip yaw +/-6 deg) and the calibration band (every leg joint +/-3 deg at the sit)
  stops     every stop: just inside (clear) and 0.5 deg past it (touch, on the named parts only)
  walk      the stock walk envelope: from a walk joint log (--walk, sit_sim.py walk output) when given, else the E9 'ours'
            ranges (VERIFICATION.md E9) as a grid of corners, both legs, with the inward roll and yaw that bring the shins
            together
A pair counts when its overlap is more than BASE_TOL mm3 over the same pair at the zero pose (horns seated in their
pockets and screw-on faces touch there by design).
"""
import argparse
import itertools
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sitlib as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_TOL = 2.0
SKIP = {"usb_c_charger", "power_switch", "bms", "bno055", "board", "cell", "holder", "raspberrypizerow", "sg90",
        "left_eye", "right_eye", "bulb", "flash_light_module", "flash_reflector_interface", "speaker_stand",
        "speaker_interface"}
LEG_L = ["hip_roll_assembly", "left_roll_to_pitch_assembly", "knee_and_ankle_assembly", "knee_and_ankle_assembly_2", "foot_assembly"]
LEG_R = ["hip_roll_assembly_2", "right_roll_to_pitch_assembly", "knee_and_ankle_assembly_3", "knee_and_ankle_assembly_4", "foot_assembly_2"]
HEAD = ["neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly", "head_assembly"]
TR = "trunk_assembly"
E9_OURS = dict(left_hip_yaw=(-5.4, 10.4), left_hip_roll=(-4.6, 9.3), left_hip_pitch=(-48.8, -30.3), left_knee=(67.6, 90.7),
               left_ankle=(-46.7, -27.4), right_hip_yaw=(-5.9, 5.9), right_hip_roll=(-13.1, 3.4),
               right_hip_pitch=(33.3, 49.8), right_knee=(68.4, 91.0), right_ankle=(-46.2, -26.7), neck_pitch=(7.3, 12.4),
               head_pitch=(-10.3, 5.3))
# which link pairs can meet (the rest are far apart in every state)
PAIRS = ([(a, b) for leg in (LEG_L, LEG_R) for a, b in itertools.combinations(leg, 2)] +
         [(TR, b) for b in LEG_L[1:] + LEG_R[1:]] +
         [(a, b) for a in LEG_L[2:] for b in LEG_R[2:]] +
         [(TR, b) for b in HEAD] + [(a, b) for a, b in itertools.combinations(HEAD, 2)])


class Model:
    def __init__(self):
        self.S = L.scene(fresh=True)
        S = self.S
        self.parts = {}            # link -> [(name, manifold world zero pose)]
        for i in S.inst:
            if i["key"] in SKIP:
                continue
            m = S.world_mesh(i)
            M = L.to_man(m)
            nm = "%s#%d" % (i["key"], i["idx"])
            self.parts.setdefault(i["link"], []).append((nm, M))
            if i["key"] == "servo_bottom":
                T = S.T0[i["link"]] @ i["T"]
                (x0, x1), (y0, y1), (z0, z1) = L.c3d_lib.SERVO_INNER
                b = L.box((x0, y0, z0), (x1, y1, z1))
                b.apply_transform(T)
                self.parts[i["link"]].append(("servo_fill#%d" % i["idx"], L.to_man(b)))
        self.bb = {ln: [L.bbox_of(M) for _, M in ps] for ln, ps in self.parts.items()}
        self.base = {}

    def overlaps(self, cfg, pairs=PAIRS, gap=False):
        S = self.S
        Tl = S.link_T(cfg)
        Tr = {ln: Tl[ln] @ np.linalg.inv(S.T0[ln]) for ln in self.parts}
        posed = {}

        def get(ln):
            if ln not in posed:
                posed[ln] = [(nm, L.xform(M, Tr[ln])) for nm, M in self.parts[ln]]
            return posed[ln]
        out = {}
        for a, b in pairs:
            if a not in self.parts or b not in self.parts:
                continue
            A, B = get(a), get(b)
            for na, MA in A:
                ba = L.bbox_of(MA, 1.0)
                for nb, MB in B:
                    bb = L.bbox_of(MB, 1.0)
                    if np.any(ba[1] < bb[0]) or np.any(bb[1] < ba[0]):
                        continue
                    v = (MA ^ MB).volume()
                    g = MA.min_gap(MB, 3.0) if gap and v <= 1e-6 else (0.0 if v > 1e-6 else None)
                    if v > 1e-6 or (g is not None and g < 3.0):
                        out[(na, nb)] = (v, g)
        return out

    def baseline(self):
        if not self.base:
            self.base = {k: v for k, (v, g) in self.overlaps({}).items()}
        return self.base

    def new_hits(self, cfg, pairs=PAIRS):
        b = self.baseline()
        return {k: v for k, (v, g) in self.overlaps(cfg, pairs).items() if v > b.get(k, 0.0) + BASE_TOL}


def stem(n):
    return n.split("#")[0]


def cfg_full(h, k, a, neck=0.0, head=0.0, roll=0.0, yaw=0.0):
    c = L.cfg_left(h=h, k=k, a=a, roll=roll, yaw=yaw)
    c["neck_pitch"], c["head_pitch"] = np.radians(neck), np.radians(head)
    return c


def soft_path():
    """the sit path with the head forward waypoints at the software limits (3 deg inside the CAD stops)"""
    P = []
    for (h, k, a, n, hd) in L.PATH_A1B:
        P.append((h, k, a, max(n, -19.0), max(hd, L.STOPS["head_fwd"]["stop"] + 3.0)))
    out = []
    for p0, p1 in zip(P[:-1], P[1:]):
        n = max(1, int(np.ceil(max(abs(np.array(p1) - np.array(p0))))))
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(tuple(np.array(p0) * (1 - s) + np.array(p1) * s))
    out.append(P[-1])
    return out


def path_states():
    st = [("path", cfg_full(*p), p) for p in soft_path()]
    for y in (-6.0, 0.0, 6.0):
        for r in (0.0, L.STOPS["hip_roll_out"]["stop"]):
            st.append(("settle", cfg_full(-60, 150, -95, 25, -25, roll=r, yaw=y), (-60, 150, -95, 25, -25, r, y)))
    for dh, dk, da in itertools.product((-3, 3), (-3, 0), (-3, 3)):
        st.append(("calibration", cfg_full(-60 + dh, 147 + dk, -92 + da, 25, -25), (-60 + dh, 147 + dk, -92 + da)))
    for h in (-75.0, -70.0, -65.0):
        st.append(("hip_back", cfg_full(h, 150, -95, 25, -25), (h, 150, -95)))
    return st


def walk_states(walk_json=None):
    if walk_json:
        W = json.load(open(walk_json))
        rows = W["samples"]
        return [("walk", {k: np.radians(v) for k, v in r.items()}, None) for r in rows]
    st = []
    E = E9_OURS
    for hy, hr, hp, kn, an in itertools.product((0, 1), (0, 1), (0, 1), (0, 1), (0, 1)):
        c = {}
        for side in ("left", "right"):
            for j, pick in (("hip_yaw", hy), ("hip_roll", hr), ("hip_pitch", hp), ("knee", kn), ("ankle", an)):
                lo, hi = E["%s_%s" % (side, j)]
                # pick 0 = the end that brings the legs together (inward roll, toe-in yaw) for roll and yaw
                if side == "right" and j in ("hip_roll", "hip_yaw"):
                    v = (lo, hi)[1 - pick]
                else:
                    v = (lo, hi)[pick]
                c["%s_%s" % (side, j)] = np.radians(v)
        c["neck_pitch"], c["head_pitch"] = np.radians(E["neck_pitch"][1]), np.radians(E["head_pitch"][0])
        st.append(("walk_grid", c, None))
    return st


def stop_checks(Mo):
    """each stop touches only at the stop: clear 0.5 deg inside, touch 0.5 deg past (on the parts that make the stop)"""
    D = np.radians
    out = {}
    specs = {
        "knee_fold": ("left_knee", ("knee_and_ankle_assembly", "knee_and_ankle_assembly_2"), ("knee_bumper",), dict(left_hip_pitch=D(-60))),
        "ankle_sit": ("left_ankle", ("knee_and_ankle_assembly_2", "foot_assembly"), ("ankle_pad",), {}),
        "hip_roll_out": ("left_hip_roll", ("hip_roll_assembly", "left_roll_to_pitch_assembly"), ("left_roll_to_pitch", "roll_motor_bottom"), {}),
        "hip_pitch_back": ("left_hip_pitch", ("left_roll_to_pitch_assembly", "knee_and_ankle_assembly"), ("hip_pad",), {}),
        "neck_back": ("neck_pitch", (TR, "neck_pitch_assembly"), ("neck_left_sheet", "neck_right_sheet"), {}),
        "head_fwd": ("head_pitch", ("neck_pitch_assembly", "head_pitch_to_yaw"), ("head_pitch_to_yaw",), {}),
    }
    for name, (jn, pair, makers, extra) in specs.items():
        st = L.STOPS[name]["stop"]
        sgn = 1.0 if L.STOPS[name]["side"] == "hi" else -1.0
        res = {}
        for tag, a in (("inside", st - sgn * 0.5), ("at", st), ("past", st + sgn * 0.5)):
            c = dict(extra)
            c[jn] = D(a)
            hits = Mo.new_hits(c, [pair])
            hits_any = {"%s|%s" % (stem(x), stem(y)): round(v, 2) for (x, y), v in Mo.overlaps(c, [pair]).items()
                        if v[0] > Mo.baseline().get((x, y), 0.0) + 0.05 for v in [v]} if False else None
            ov = Mo.overlaps(c, [pair])
            b = Mo.baseline()
            new = {"%s|%s" % (stem(x), stem(y)): round(v - b.get((x, y), 0.0), 2) for (x, y), (v, g) in ov.items()
                   if v - b.get((x, y), 0.0) > 0.02}
            res[tag] = dict(angle=a, new_overlap_mm3=new)
        touch = res["past"]["new_overlap_mm3"]
        ok = (not res["inside"]["new_overlap_mm3"]) and bool(touch) and all(any(m in k for m in makers) for k in touch)
        out[name] = dict(joint=jn, stop=st, ok=ok, **res)
    return out


HS_JOINTS = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
             "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]


def subtree_pairs(S, jn):
    """link pairs across the joint: the joint's child subtree against every other link it can meet"""
    u = S.u
    child = S.joints[jn]["child"]
    sub = {child}
    grow = True
    while grow:
        grow = False
        for j in u.robot.joints:
            if j.parent in sub and j.child not in sub:
                sub.add(j.child)
                grow = True
    return [(a, b) for a, b in PAIRS if (a in sub) != (b in sub)]


def hard_stops(Mo, log=print):
    """first CAD contact of each joint moved alone from the zero pose, in each direction, within its URDF range:
    2 deg steps, then 0.5 deg back from the first hit (screw heads are in the fastener sweep, not here)"""
    S = Mo.S
    out = {}
    for jn in HS_JOINTS:
        lo, hi = np.degrees(S.joints[jn]["lo"]), np.degrees(S.joints[jn]["hi"])
        pairs = subtree_pairs(S, jn)
        res = {}
        for side, end in (("lo", lo), ("hi", hi)):
            sgn = -1.0 if side == "lo" else 1.0
            a, hit = 0.0, None
            while abs(a) < abs(end) - 1e-9:
                a = sgn * min(abs(a) + 2.0, abs(end))
                h = Mo.new_hits({jn: np.radians(a)}, pairs)
                if h:
                    b = a - sgn * 2.0
                    while abs(b) < abs(a) - 1e-9:
                        b2 = b + sgn * 0.5
                        if Mo.new_hits({jn: np.radians(b2)}, pairs):
                            break
                        b = b2
                    hit = round(b, 1)
                    who = sorted(h.items(), key=lambda x: -x[1])[0]
                    res[side + "_by"] = "%s|%s" % (stem(who[0][0]), stem(who[0][1]))
                    break
            res[side] = hit
        out[jn] = res
        log("hard stop %s: %s" % (jn, res))
    return out


def run(walk_json=None, quick=False, log=print):
    t0 = time.time()
    Mo = Model()
    Mo.baseline()
    log("model and baseline %.0f s" % (time.time() - t0))
    report = dict(generated_by="altaay_lab/twin/sit/sit_sweep.py", label="CAD check only", base_tol_mm3=BASE_TOL,
                  inputs=dict(urdf="mini_bdx/robots/open_duck_mini_v2/robot.urdf", stls="print/*.stl", walk=walk_json or "E9 ours grid"))
    report["stops"] = stop_checks(Mo)
    log("stops %.0f s" % (time.time() - t0))
    report["hard_stops"] = hard_stops(Mo, log)
    log("hard stops %.0f s" % (time.time() - t0))
    for group, states in (("path", path_states()), ("walk", walk_states(walk_json))):
        if quick:
            states = states[::4]
        worst = {}
        for tag, c, p in states:
            for (a, b), v in Mo.new_hits(c).items():
                k = "%s|%s" % (stem(a), stem(b))
                if v > worst.get(k, (0,))[0]:
                    worst[k] = (round(v, 2), tag, [round(x, 1) for x in p] if p else None)
        report[group] = dict(states=len(states), new_overlaps={k: dict(mm3=v[0], state=v[1], pose=v[2]) for k, v in sorted(worst.items(), key=lambda x: -x[1][0])})
        log("%s: %d states, %d pairs with new overlap (%.0f s)" % (group, len(states), len(worst), time.time() - t0))
    L.dump(report, os.path.join(HERE, "sit_sweep.json"))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--walk", default=None)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    R = run(a.walk, a.quick)
    print(json.dumps({k: R[k] for k in ("stops",)}, indent=1)[:4000])
    for g in ("path", "walk"):
        print(g, json.dumps(R[g]["new_overlaps"], indent=0)[:3000])
