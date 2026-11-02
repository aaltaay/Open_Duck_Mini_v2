#!/usr/bin/env python3
"""Upstream issue Mini #17 (UPSTREAM_ISSUES.md G12): does the head of the roll_motor_bottom
servo screw hit roll_to_pitch when the hip roll joint moves?

  python3 check_hip_roll_screw.py [--head-d 4.0] [--head-k 1.6] [--steps 41]

Read only: loads the URDF (mini_bdx/robots/open_duck_mini_v2, upstream b23317a), the instance
transforms in altaay_lab/audit/assembly.json and the upstream print STLs (print/, 730c14b). The
screw axes come from altaay_lab/audit/sites.json: 2 clearance holes per side, 2.5 mm through the
1.4 mm roll_motor_bottom plate (flat face, no recess), into STS3215 case pilots 1.67 mm.

The screw head is not in the CAD. It is modelled as a cylinder on the flat face: diameter --head-d
and height --head-k. Defaults 4.0 x 1.6 mm are the ISO 7045 M2 / ISO 7049 ST2.2 pan head
(the Feetech bag screw type is not published, HARDWARE_AUDIT B2). The joint is swept over its
URDF limits and the clearance from the head to every mesh that moves with the joint is printed.
"""
import argparse, json, os

import numpy as np
import trimesh
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
URDF = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "robot.urdf")
UDIR = os.path.dirname(URDF)
PDIR = os.path.join(REPO, "print")
AUDIT = os.path.join(REPO, "altaay_lab", "audit")
SIDES = {"left": ("left_hip_roll", "hip_roll_assembly", "left_roll_to_pitch_assembly"),
         "right": ("right_hip_roll", "hip_roll_assembly_2", "right_roll_to_pitch_assembly")}


def load_mesh(name):
    p = os.path.join(PDIR, name.replace("left_knee_to_ankle_", "knee_to_ankle_"))
    if os.path.exists(p) and not name.startswith("wj-") and "palonier" not in name:
        return trimesh.load(p), "print/" + os.path.basename(p)
    m = trimesh.load(os.path.join(UDIR, name))
    m.apply_scale(1000.0)
    return m, "urdf/" + name


def link_T(u, link, cfg):
    u.update_cfg(cfg)
    T = np.array(u.get_transform(frame_to=link), float)
    T[:3, 3] *= 1000.0
    return T


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--head-d", type=float, default=4.0)
    ap.add_argument("--head-k", type=float, default=1.6)
    ap.add_argument("--steps", type=int, default=41)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    A = json.load(open(os.path.join(AUDIT, "assembly.json")))
    S = json.load(open(os.path.join(AUDIT, "sites.json")))
    u = yourdfpy.URDF.load(URDF, load_meshes=False, build_scene_graph=True)
    out = {}
    for side, (joint, parent, child) in SIDES.items():
        jl = u.joint_map[joint].limit
        lo, hi = float(jl.lower), float(jl.upper)
        zero = {j: 0.0 for j in u.actuated_joint_names}
        T0 = link_T(u, child, zero)
        # screw axes through roll_motor_bottom of this side (zero pose, mm)
        heads = []
        for s in S:
            for t0, t1, m, kind, d, i in s["segs"]:
                if m == "roll_motor_bottom" and abs(d - 2.5) < 0.1 and A["inst"][i]["link"] == parent:
                    o, ax = np.array(s["o"]), np.array(s["ax"])
                    face = o + ax * t0           # flat outer face where the head sits
                    cyl = trimesh.creation.cylinder(radius=a.head_d / 2, height=a.head_k, sections=72)
                    # cylinder axis along -ax, from the face outwards
                    R = trimesh.geometry.align_vectors([0, 0, 1], -ax)
                    cyl.apply_transform(R)
                    cyl.apply_translation(face - ax * a.head_k / 2)
                    heads.append(dict(face=face.round(2).tolist(), axis=ax.tolist(), mesh=cyl))
        for h in heads:
            h["pts"] = np.vstack([h["mesh"].sample(6000, seed=7), h["mesh"].vertices])
        # meshes that move with the joint
        movers = []
        for k, inst in enumerate(A["inst"]):
            if inst["link"] == child:
                m, label = load_mesh(inst["mesh"])
                m.apply_transform(np.array(inst["T"]))
                movers.append((label, m))
        rows = []
        for th in np.linspace(lo, hi, a.steps):
            cfg = dict(zero)
            cfg[joint] = float(th)
            D = link_T(u, child, cfg) @ np.linalg.inv(T0)
            moved = []
            for label, m in movers:
                mm = m.copy()
                mm.apply_transform(D)
                moved.append((label, mm))
            per = []
            for h in heads:
                best = None
                for label, mm in moved:
                    if np.any(mm.bounds[0] > h["pts"].max(0) + 5) or np.any(mm.bounds[1] < h["pts"].min(0) - 5):
                        continue
                    sd = trimesh.proximity.signed_distance(mm, h["pts"])   # >0: head point inside the part
                    c = float(-sd.max())                                   # clearance, <0 is overlap depth
                    if best is None or c < best[0]:
                        best = (round(c, 2), label)
                per.append(best)
            rows.append((round(float(th), 4), round(float(np.degrees(th)), 1), per))
        res = []
        for n, h in enumerate(heads):
            vals = [(r[2][n][0], r[1], r[2][n][1]) for r in rows if r[2][n] is not None]
            w = min(vals) if vals else None
            z = [r[2][n] for r in rows if abs(r[0]) < 1e-6 and r[2][n] is not None]
            res.append(dict(face=h["face"], worst_clearance=w[0] if w else None, worst_deg=w[1] if w else None,
                            nearest=w[2] if w else None, at_zero=z[0][0] if z else None,
                            overlap_deg=[v[1] for v in vals if v[0] < 0]))
        out[side] = dict(joint=joint, range_rad=[lo, hi], head_d=a.head_d, head_k=a.head_k,
                         screws=res, sweep=[(r[0], r[1], [p if p is None else p[0] for p in r[2]]) for r in rows])
        print("%s %s range %.3f..%.3f rad (%.1f..%.1f deg), head %.1f x %.1f mm" % (
            side, joint, lo, hi, np.degrees(lo), np.degrees(hi), a.head_d, a.head_k))
        for r in rows:
            print("   %+7.3f rad %+6.1f deg  clearance per screw: %s" % (r[0], r[1], [None if p is None else p[0] for p in r[2]]))
        for n, r in enumerate(res):
            ov = r["overlap_deg"]
            print("   screw %d head face at %s: at zero %s mm, worst %s mm at %s deg (%s), overlap over %s" % (
                n + 1, r["face"], r["at_zero"], r["worst_clearance"], r["worst_deg"], r["nearest"],
                ("%+.1f..%+.1f deg" % (min(ov), max(ov))) if ov else "no angle"))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
