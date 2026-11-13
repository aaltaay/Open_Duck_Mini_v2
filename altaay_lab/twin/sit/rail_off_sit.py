"""Limp nest-v2 sit, then the servo rail comes on before the stand.

The Feetech sheets used here do not print an unpowered backdrive torque. The
training joint friction (frictionloss 0.068 Nm, damping 0.56) is not that
number. This run also sets both to 0. Floor friction 0.8 is the sit model's
floor, not a felt measurement. Sim pass only.

  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/twin/sit/rail_off_sit.py --out <scratch>
Writes rail_off_sit.json next to this file.
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
STRIPE_MM = 20.0
WELL_MM = 3.0
MARGIN_MM = (STRIPE_MM - WELL_MM) / 2.0


def seat_force(md, dd):
    import mujoco as m
    f = 0.0
    p = np.zeros(3)
    for i in range(dd.ncon):
        c = dd.contact[i]
        w = np.zeros(6)
        m.mj_contactForce(md, dd, i, w)
        if w[0] <= 0:
            continue
        names = [m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "" for g in (c.geom1, c.geom2)]
        if SEAT in names:
            f += float(w[0])
            p += float(w[0]) * np.array(c.pos)
    return f, (None if f <= 0 else p / f)


def qdeg(md, dd, name):
    import mujoco as m
    i = m.mj_name2id(md, m.mjtObj.mjOBJ_ACTUATOR, name)
    j = md.actuator_trnid[i, 0]
    return float(np.degrees(dd.qpos[md.jnt_qposadr[j]]))


def hold(md, dd, seconds, settle=2.0):
    import mujoco as m
    step = md.opt.timestep
    n = int(seconds / step)
    n0 = int(settle / step)
    ref = seat0 = None
    max_dx = max_dy = 0.0
    min_f = 1e9
    on = total = 0
    head0 = qdeg(md, dd, "head_pitch")
    roll0 = qdeg(md, dd, "head_roll")
    max_dhead = max_droll = 0.0
    blew = False
    t_ok = 0.0
    for i in range(n):
        m.mj_step(md, dd)
        if (not np.isfinite(dd.qpos).all()) or float(np.linalg.norm(dd.qvel)) > 50:
            blew = True
            break
        t_ok = (i + 1) * step
        f, p = seat_force(md, dd)
        max_dhead = max(max_dhead, abs(qdeg(md, dd, "head_pitch") - head0))
        max_droll = max(max_droll, abs(qdeg(md, dd, "head_roll") - roll0))
        if i == n0:
            ref = dd.qpos[0:2].copy()
            seat0 = None if p is None else p.copy()
        if i > n0 and ref is not None:
            total += 1
            if f > 0.2:
                on += 1
            min_f = min(min_f, f)
            d = (dd.qpos[0:2] - ref) * 1000.0
            max_dx = max(max_dx, abs(float(d[0])))
            max_dy = max(max_dy, abs(float(d[1])))
            if seat0 is not None and p is not None:
                ds = (p - seat0) * 1000.0
                max_dx = max(max_dx, abs(float(ds[0])))
                max_dy = max(max_dy, abs(float(ds[1])))
    ts = S.trunk_state(md, dd)
    return dict(
        seconds=round(t_ok, 2), blew=blew, up=round(ts["up"], 3), pitch_deg=round(ts["pitch"], 2),
        dx_mm=round(max_dx, 2), dy_mm=round(max_dy, 2),
        min_seat_N=None if min_f > 1e8 else round(min_f, 3),
        seat_steps_over_0p2N=on, seat_steps=total,
        head_pitch_move_deg=round(max_dhead, 2), head_roll_move_deg=round(max_droll, 2),
        lateral_inside_8p5mm=max_dy < MARGIN_MM and not blew,
    )


def rail_then_stand(md, dd):
    import mujoco as m
    q = np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i, 0]]] for i in range(md.nu)])
    lo, hi = md.actuator_ctrlrange[:, 0], md.actuator_ctrlrange[:, 1]
    c = np.clip(q, lo, hi)
    yank = float(np.degrees(np.max(np.abs(c - q))))
    dd.ctrl[:] = c
    xy0 = dd.qpos[0:2].copy()
    S.torque(md, True)
    step = md.opt.timestep
    min_f = 1e9
    max_d = 0.0
    for _ in range(int(1.0 / step)):
        m.mj_step(md, dd)
        f, _p = seat_force(md, dd)
        min_f = min(min_f, f)
        max_d = max(max_d, float(np.linalg.norm((dd.qpos[0:2] - xy0) * 1000.0)))
    held = S.trunk_state(md, dd)
    c = S.ramp(md, dd, c, S.targets(md, *S.STAND), 3.0, None)
    for _ in range(int(1.0 / step)):
        m.mj_step(md, dd)
    ts = S.trunk_state(md, dd)
    return dict(
        yank_deg=round(yank, 2),
        hold_before_ramp_drift_mm=round(max_d, 2),
        hold_before_ramp_min_seat_N=round(min_f, 3),
        hold_before_ramp_up=round(held["up"], 3),
        stood_up=round(ts["up"], 3), stood_z_m=round(ts["z"], 3), stood_pitch_deg=round(ts["pitch"], 2),
    )


def case(out, name, mu, fric, damp, seconds, dt=None, stand=False):
    md = S.model(out, mu=mu)
    saved = (md.dof_frictionloss.copy(), md.dof_damping.copy(), float(md.opt.timestep))
    if dt:
        md.opt.timestep = dt
    dd, _SF, _pins, _tr, _cb = S.enter(md, pins_on=False)
    S.torque(md, False)
    if fric is not None:
        md.dof_frictionloss[6:] = fric
    if damp is not None:
        md.dof_damping[6:] = damp
    row = hold(md, dd, seconds)
    row["name"] = name
    row["mu"] = mu
    row["frictionloss"] = None if fric is None else fric
    row["damping"] = None if damp is None else damp
    if stand and not row["blew"]:
        md.dof_frictionloss[:], md.dof_damping[:] = saved[0], saved[1]
        row["undock"] = rail_then_stand(md, dd)
    md.dof_frictionloss[:], md.dof_damping[:], md.opt.timestep = saved
    print(name, row["blew"], "dx", row["dx_mm"], "dy", row["dy_mm"], "seat", row["min_seat_N"],
          "head", row["head_pitch_move_deg"], row["head_roll_move_deg"], flush=True)
    return row


def main():
    import mujoco as m
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    md = S.model(args.out, mu=0.8)
    rows = [
        case(args.out, "training_friction_mu_0.8", 0.8, None, None, 20.0, stand=True),
        case(args.out, "zero_joint_friction_mu_0.8", 0.8, 0.0, 0.0, 20.0),
        case(args.out, "zero_joint_and_floor_friction", 0.0, 0.0, 0.0, 5.0, dt=0.0005),
    ]
    doc = dict(
        label="sim pass only",
        mujoco=m.__version__,
        model_frictionloss_Nm=float(md.dof_frictionloss[6]),
        model_damping=float(md.dof_damping[6]),
        sheet_backdrive="BLOCKER. The C001 and C018 pages used in this lab do not print an unpowered backdrive or gear friction.",
        floor_mu_note="0.8 is the sit model floor. Sole friction on felt is BLOCKER.",
        stripe_margin_mm=MARGIN_MM,
        stripe_margin_note="calc only, (20 mm stripe - 3 mm well) / 2, wells centered. Stripes run in x, so y is the crossing direction.",
        pins="off. Nest v2 has no foot pins. The sit is the D59 path onto the floor.",
        rows=rows,
    )
    path = os.path.join(HERE, "rail_off_sit.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
