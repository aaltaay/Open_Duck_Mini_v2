#!/usr/bin/env python3
"""sit_soles.py: where the soles are, how flat they lie and what load they carry in the D59 alert sit, torque off.
sim pass only (MuJoCo, the repo's own sit model built by twin/sit/sit_model.py into a scratch folder; the repo is only
read). No dock pins under the feet (a striped mat has none): pins_on=False.

  PYTHONDONTWRITEBYTECODE=1 python3 sit_soles.py <scratch>/model
Writes sit_soles.json next to this file.
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
REPO_SIT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")), "twin", "sit")  # altaay_lab/twin/sit, relative to this file
sys.path.insert(0, REPO_SIT)
import mujoco as m  # noqa: E402
import sit_sim as S  # noqa: E402

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))


def bottom_ids(md, dd):
    """vertex ids of each sole's bottom face, taken while standing flat (within 0.5 mm of the lowest)"""
    ids = []
    for j in range(2):
        V = S.sole_world(md, dd, j)
        ids.append(np.where(V[:, 2] < V[:, 2].min() + 0.0005)[0])
    return ids


def sole_state(md, dd, ids):
    """per sole: the flat bottom face (the 4 lowest collision vertices found while standing) in the world.
    Axes from the foot body frame (as sit_sim.sole_frames): f forward along the sole, l to the robot's left.
    roll_deg > 0: the left edge of the sole is higher than its right edge. pitch_deg > 0: toe higher than heel."""
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    Rt = dd.xmat[tr].reshape(3, 3)
    head = np.arctan2(Rt[1, 0], Rt[0, 0])
    SF = sole_state.SF
    out = []
    for j in range(2):
        bi, c, f, l_ = SF[j]
        R = dd.xmat[bi].reshape(3, 3)
        fw, lw = R @ f, R @ l_
        o = dd.xpos[bi] + R @ c                      # centre of the bottom face
        V = S.sole_world(md, dd, j)[ids[j]]
        yaw = np.arctan2(fw[1], fw[0])
        roll = np.degrees(np.arcsin(np.clip(lw[2], -1, 1)))
        pitch = np.degrees(np.arcsin(np.clip(fw[2], -1, 1)))
        # the two long edges of the 15.8 mm flat face (print/foot_bottom_tpu.stl), 84.8 mm long, heights at their ends
        edges = {}
        for nm, sgn in (("left_edge", 1), ("right_edge", -1)):
            e = [o + fw * a * 0.0424 + lw * sgn * 0.0079 for a in (-1, 1)]
            edges[nm + "_z_heel_toe_mm"] = [round(float(p[2] * 1000), 2) for p in e]
        out.append(dict(centre_mm=(o[:2] * 1000).round(2).tolist(), centre_z_mm=round(float(o[2] * 1000), 2),
                        z_min_mm=round(float(V[:, 2].min() * 1000), 2), z_max_mm=round(float(V[:, 2].max() * 1000), 2),
                        roll_deg=round(float(roll), 2), pitch_deg=round(float(pitch), 2),
                        yaw_deg=round(float(np.degrees(yaw)), 2), yaw_rel_trunk_deg=round(float(np.degrees(yaw - head)), 2), **edges))
    f = np.array([np.cos(head), np.sin(head)])
    l_ = np.array([-f[1], f[0]])
    cL, cR = np.array(out[0]["centre_mm"]), np.array(out[1]["centre_mm"])
    tp = dd.xpos[tr][:2] * 1000
    return dict(soles=out, trunk_xy_mm=tp.round(2).tolist(), trunk_heading_deg=round(float(np.degrees(head)), 2),
                stance_width_mm=round(float((cL - cR) @ l_), 1), stagger_mm=round(float((cL - cR) @ f), 1),
                sole_centre_fwd_of_trunk_mm=[round(float((cL - tp) @ f), 1), round(float((cR - tp) @ f), 1)])


def contact_forces(md, dd):
    F = {}
    for i in range(dd.ncon):
        c = dd.contact[i]
        w = np.zeros(6)
        m.mj_contactForce(md, dd, i, w)
        for g in (c.geom1, c.geom2):
            n = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
            if n == "floor":
                continue
            F[n] = F.get(n, 0.0) + float(w[0])
    return {k: round(v, 2) for k, v in F.items() if v > 0.005}


def footprint(md, dd):
    """extent of every robot mesh vertex in the trunk heading frame (mm): the room the sitting duck needs"""
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    Rt = dd.xmat[tr].reshape(3, 3)
    head = np.arctan2(Rt[1, 0], Rt[0, 0])
    f = np.array([np.cos(head), np.sin(head)])
    l_ = np.array([-f[1], f[0]])
    tp = dd.xpos[tr][:2]
    lo, hi = np.array([9e9, 9e9]), -np.array([9e9, 9e9])
    for g in range(md.ngeom):
        if md.geom_type[g] != m.mjtGeom.mjGEOM_MESH:
            continue
        mid = md.geom_dataid[g]
        a, n = md.mesh_vertadr[mid], md.mesh_vertnum[mid]
        V = md.mesh_vert[a:a + n] @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g]
        P = np.c_[(V[:, :2] - tp) @ f, (V[:, :2] - tp) @ l_]
        lo, hi = np.minimum(lo, P.min(0)), np.maximum(hi, P.max(0))
    return dict(back_mm=round(float(lo[0] * 1000), 1), front_mm=round(float(hi[0] * 1000), 1),
                right_mm=round(float(lo[1] * 1000), 1), left_mm=round(float(hi[1] * 1000), 1))


def run(name, mu=0.8, err=0.0, mirror=False, fric=None):
    md = S.model(OUT, mu)
    saved = md.dof_frictionloss.copy()
    if fric is not None:
        md.dof_frictionloss[6:] = fric
    off = None
    if err:
        off = np.full(md.nu, np.radians(err))
        if mirror:
            for i in range(md.nu):
                if md.actuator(i).name.startswith("right"):
                    off[i] = -off[i]
    dd, c0 = S.stance_start(md)
    ids = bottom_ids(md, dd)
    sole_state.SF = S.sole_frames(md, dd)
    stand = sole_state(md, dd, ids)
    stand["contact_N"] = contact_forces(md, dd)
    # the sit path, as sit_sim.enter but with no dock pins
    c = c0
    for (h, k, a, n, hd), T in S.DOWN:
        c = S.ramp(md, dd, c, S.targets(md, h, k, a, n, hd, off=off), T)
    c = S.ramp(md, dd, c, S.targets(md, *S.SIT, off=off), 1.5)
    for _ in range(int(0.5 / md.opt.timestep)):
        m.mj_step(md, dd)
    S.torque(md, False)
    for _ in range(int(10.0 / md.opt.timestep)):
        m.mj_step(md, dd)
    acc, n = {}, int(2.0 / md.opt.timestep)             # contact forces: the mean over 2 more seconds at rest
    for _ in range(n):
        m.mj_step(md, dd)
        for k, v in contact_forces(md, dd).items():
            acc[k] = acc.get(k, 0.0) + v
    sit = sole_state(md, dd, ids)
    sit["contact_N"] = {k: round(v / n, 2) for k, v in acc.items()}
    sit["speed_m_s"] = round(float(np.linalg.norm(dd.qvel[:3])), 5)
    sit["footprint_trunk_frame"] = footprint(md, dd)
    ts = S.trunk_state(md, dd)
    sit["trunk"] = {k: round(v, 3) for k, v in ts.items()}
    slip = [float(np.linalg.norm(np.array(sit["soles"][j]["centre_mm"]) - np.array(stand["soles"][j]["centre_mm"]))) for j in range(2)]
    S.torque(md, True)
    md.dof_frictionloss[:] = saved
    r = dict(name=name, mu=mu, err_deg=err, mirror=mirror, fric=fric, stand=stand, sit=sit,
             sole_move_stand_to_sit_mm=[round(s, 1) for s in slip], weight_N=round(float(md.body_subtreemass[1] * 9.81), 2))
    s = sit
    print(name, "width %.1f stagger %.1f" % (s["stance_width_mm"], s["stagger_mm"]),
          "roll", [x["roll_deg"] for x in s["soles"]], "pitch", [x["pitch_deg"] for x in s["soles"]], "yaw rel", [x["yaw_rel_trunk_deg"] for x in s["soles"]],
          "F", s["contact_N"], "move", r["sole_move_stand_to_sit_mm"], flush=True)
    return r


if __name__ == "__main__":
    cases = [("nominal mu0.8", {}), ("mu 0.4", dict(mu=0.4)), ("zero +1 deg", dict(err=1.0)), ("zero -1 deg", dict(err=-1.0)),
             ("zero +1 L / -1 R", dict(err=1.0, mirror=True)), ("zero -1 L / +1 R", dict(err=-1.0, mirror=True)),
             ("joint friction 0.2", dict(fric=0.2)), ("joint friction 0.02", dict(fric=0.02))]
    R = [run(n, **o) for n, o in cases]
    json.dump(dict(label="sim pass only", model="twin/sit/sit_model.py round-2 model, no dock pins under the feet",
                   cases=R), open(os.path.join(HERE, "sit_soles.json"), "w"), indent=1)
