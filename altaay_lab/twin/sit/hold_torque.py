"""Hold a few joints at the sit, with every other joint at zero friction.

Kt is 1.090 Nm/A from the C018 stall line (problems/STS12.md, calc only).
The question is whether two or three servos, under 0.10 A together, keep the
seat down if gear friction and floor friction are both zero. Sim pass only.

  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/twin/sit/hold_torque.py --out <scratch>
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sit_sim as S  # noqa: E402

SEAT = "sit_seat_trunk_assembly_1_collision"
KT = 1.090
I_TERM = 0.10
SETS = [
    ("two_hip_rolls", ("left_hip_roll", "right_hip_roll")),
    ("two_hip_pitches", ("left_hip_pitch", "right_hip_pitch")),
    ("two_knees", ("left_knee", "right_knee")),
    ("neck_and_head", ("neck_pitch", "head_pitch")),
    ("hip_pitches_and_ankle", ("left_hip_pitch", "right_hip_pitch", "left_ankle")),
]


def seat_n(md, dd):
    import mujoco as m
    f = 0.0
    for i in range(dd.ncon):
        c = dd.contact[i]
        w = np.zeros(6)
        m.mj_contactForce(md, dd, i, w)
        if w[0] <= 0:
            continue
        names = [m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "" for g in (c.geom1, c.geom2)]
        if SEAT in names:
            f += float(w[0])
    return f


def run_set(md, names):
    import mujoco as m
    floor = [g for g in range(md.ngeom) if (m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "") == "floor"]
    saved_floor = [md.geom_friction[g].copy() for g in floor]
    saved = (md.dof_frictionloss.copy(), md.dof_damping.copy(), md.actuator_gainprm.copy(), md.actuator_biasprm.copy())
    dd, *_ = S.enter(md, pins_on=False)
    q = np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i, 0]]] for i in range(md.nu)])
    md.dof_frictionloss[6:] = 0.0
    md.dof_damping[6:] = 0.0
    for g in range(md.ngeom):
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or ""
        if nm == "floor":
            md.geom_friction[g] = [0.0, 0.0, 0.0]
    dd.qpos[:] = qpos_hold = dd.qpos.copy()
    dd.qvel[:] = 0
    m.mj_forward(md, dd)
    S.torque(md, False)
    hold = []
    cmd = {}
    for i in range(md.nu):
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_ACTUATOR, i)
        if nm not in names:
            continue
        dof = md.jnt_dofadr[md.actuator_trnid[i, 0]]
        tau = float(dd.qfrc_bias[dof])
        md.actuator_gainprm[i, 0] = 0.0
        md.actuator_biasprm[i, 0] = tau
        md.actuator_biasprm[i, 1] = 0.0
        md.actuator_biasprm[i, 2] = 0.0
        hold.append(i)
        cmd[nm] = tau
    dd.qpos[:] = qpos_hold
    dd.qvel[:] = 0
    step = md.opt.timestep
    min_f = 1e9
    on = total = 0
    peak = {m.mj_id2name(md, m.mjtObj.mjOBJ_ACTUATOR, i): 0.0 for i in hold}
    ref = None
    max_dy = 0.0
    blew = False
    for i in range(int(8.0 / step)):
        m.mj_step(md, dd)
        if not np.isfinite(dd.qpos).all() or float(np.linalg.norm(dd.qvel)) > 40:
            blew = True
            break
        for ix in hold:
            nm = m.mj_id2name(md, m.mjtObj.mjOBJ_ACTUATOR, ix)
            peak[nm] = max(peak[nm], abs(float(dd.actuator_force[ix])))
        if i == int(1.0 / step):
            ref = dd.qpos[1]
        if i > int(1.0 / step):
            total += 1
            f = seat_n(md, dd)
            if f > 0.2:
                on += 1
            min_f = min(min_f, f)
            if ref is not None:
                max_dy = max(max_dy, abs(float(dd.qpos[1] - ref)) * 1000.0)
    i_a = {k: round(v / KT, 4) for k, v in peak.items()}
    total_i = float(sum(i_a.values()))
    md.dof_frictionloss[:], md.dof_damping[:], md.actuator_gainprm[:], md.actuator_biasprm[:] = saved
    for g, fr in zip(floor, saved_floor):
        md.geom_friction[g] = fr
    return dict(
        joints=list(names), blew=blew,
        min_seat_N=None if min_f > 1e8 else round(min_f, 3),
        seat_steps_over_0p2N=on, seat_steps=total,
        dy_mm=round(max_dy, 2),
        peak_torque_Nm={k: round(v, 4) for k, v in peak.items()},
        current_A=i_a, current_sum_A=round(total_i, 4),
        under_0p10A=total_i < I_TERM,
        seat_held=(not blew) and total > 0 and on == total and min_f > 0.2,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    md = S.model(args.out, mu=0.8)
    rows = []
    for name, joints in SETS:
        row = run_set(md, joints)
        row["name"] = name
        rows.append(row)
        print(name, "held", row["seat_held"], "I", row["current_sum_A"], "under", row["under_0p10A"],
              "seat", row["min_seat_N"], flush=True)
    doc = dict(
        label="sim pass only for the seat, calc only for the current",
        kt_Nm_per_A=KT,
        kt_note="2.942 Nm / 2.7 A from the C018 stall line, problems/STS12.md",
        friction="joint friction, joint damping, and floor friction set to 0 after the sit",
        term_A=I_TERM,
        rows=rows,
    )
    path = os.path.join(HERE, "hold_torque.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
