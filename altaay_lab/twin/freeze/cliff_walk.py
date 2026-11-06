#!/usr/bin/env python3
"""cliff_walk.py: does the robot's own swing foot enter the cliff ToF field of view while it walks? Sim pass only.

Run: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/twin/freeze/cliff_walk.py
Writes cliff_walk.json here. Needs ODM_PLAYGROUND (Open_Duck_Playground b9be205), as verify/e9_joint_envelope.py.

The joint grid in cliff_seat.py is wider than any walk (it finds the foot in the cone only when a leg is swung 35 deg
or more forward with the knee near straight). This runs the 7 stock walk cases of sim/current_budget.py (stand, walk,
turn, side, backlash, rough, pushes; BEST_WALK_ONNX_2), the same loop as VERIFICATION E9, and at every 50 Hz control
step puts the leg mesh vertices into the trunk frame and tests them against the cliff_seat.py cone (14 deg half
angle, 400 mm long). It also logs the cone hit with the floor plane in the trunk frame, so the trunk pitch the walk
really has is seen in the slant range (the trigger is 250 mm).
"""
import contextlib
import io as _io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "verify"))
sys.path.insert(0, HERE)
import vlib as V  # noqa: E402
import cliff_seat as CS  # noqa: E402


def main():
    os.environ.update(ODM_PLAYGROUND=V.PLAYGROUND, ODM_OUT=os.path.join(V.out_dir(), "cliff_walk"),
                      ODM_ONNX=os.path.join(V.REPO, "BEST_WALK_ONNX_2.onnx"), ODM_SCRATCH=os.path.join(V.out_dir(), "cliff_walk"))
    os.makedirs(os.environ["ODM_OUT"], exist_ok=True)
    sys.path.insert(0, V.lab("sim"))
    import current_budget as CB
    import mujoco
    MI = CB.MI
    cone = CS.cone(CS.APEX_N, 400.0)
    apex = CS.O + CS.N * CS.APEX_N
    out = {}
    for label, scene, sch, dur, pushes in CB.CASES:
        with contextlib.redirect_stdout(_io.StringIO()):
            m = MI.MjInfer(str(CB.ROOT / "xmls" / scene), CB.REF, CB.ONNX, standing=False)
        _ga = m.get_accelerometer
        m.get_accelerometer = lambda d, _ga=_ga: np.array(_ga(d), dtype=float) - np.array([1.3, 0, 0])
        model, data = m.model, m.data
        trunk = model.body("trunk_assembly").id
        legs = [g for g in range(model.ngeom) if model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH
                and any(s in model.body(model.geom_bodyid[g]).name for s in ("foot", "knee", "leg", "hip", "ankle", "roll", "pitch"))
                and not model.body(model.geom_bodyid[g]).name.startswith(("neck", "head"))]
        fallen, counter, steps, hits, slant = False, 0, 0, [], []
        for k in range(int(dur / m.sim_dt)):
            t = (k + 1) * m.sim_dt
            data.xfrc_applied[:] = 0
            for (t0, t1, f) in (pushes or []):
                if t0 <= t < t1:
                    data.xfrc_applied[trunk, :3] = f
            mujoco.mj_step(model, data)
            counter += 1
            if counter % m.decimation:
                continue
            m.commands = sch(t)
            m.imitation_i = (m.imitation_i + 1.0 * m.phase_frequency_factor) % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(data, m.commands)
            action = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = action.copy()
            m.motor_targets = m.default_actuator + action * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - m.max_motor_velocity * (m.sim_dt * m.decimation),
                                          m.prev_motor_targets + m.max_motor_velocity * (m.sim_dt * m.decimation))
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            Rt = data.xmat[trunk].reshape(3, 3)
            pt = data.xpos[trunk]
            if pt[2] < 0.10 or Rt[2, 2] < 0.5:
                fallen = True
            if t <= 2.0 or fallen:
                continue
            steps += 1
            for g in legs:
                mid = model.geom_dataid[g]
                a0, nv = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
                P = model.mesh_vert[a0:a0 + nv:3] @ data.geom_xmat[g].reshape(3, 3).T + data.geom_xpos[g]
                L = (P - pt) @ Rt * 1000.0                     # trunk frame, mm
                L = L[L[:, 0] > 30.0]
                if len(L) and cone.contains(L).any():
                    hits.append(dict(t=round(t, 2), body=model.body(model.geom_bodyid[g]).name))
                    break
            # slant range to the floor (z = 0 in the world) along the beam centre
            aw = pt + Rt @ (apex / 1000.0)
            dw = Rt @ CS.N
            if dw[2] < -1e-3:
                slant.append(float(-aw[2] / dw[2] * 1000.0))
        out[label] = dict(steps=steps, fell=fallen, foot_in_cone_steps=len(hits), first_hits=hits[:5],
                          slant_mm=[round(min(slant), 1), round(float(np.median(slant)), 1), round(max(slant), 1)] if slant else None)
        print(label, out[label], flush=True)
    J = dict(script="altaay_lab/twin/freeze/cliff_walk.py", label="sim pass only", cone_half_deg=14.0, trigger_mm=250,
             cases=out, foot_in_cone_any=any(v["foot_in_cone_steps"] for v in out.values()),
             slant_max_mm=max(v["slant_mm"][2] for v in out.values() if v["slant_mm"] and not v["fell"]),
             slant_max_cases_that_fell_mm={k: v["slant_mm"][2] for k, v in out.items() if v["fell"] and v["slant_mm"]},
             note="slant_max_mm is over the cases that walk to the end; in walk_pushes the trunk tips before the fall is "
                  "flagged and the beam reads past 250 mm: the arbiter's fall rule (D56, trunk tilt) acts there, not the cliff rule")
    with open(os.path.join(HERE, "cliff_walk.json"), "w") as fh:
        json.dump(J, fh, indent=1)
        fh.write("\n")


if __name__ == "__main__":
    main()
