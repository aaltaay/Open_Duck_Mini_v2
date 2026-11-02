"""E9: joint angles the stock policy actually uses in the sim walk (sim pass only), so collisions found by the CAD
sweeps (C4b, C11, E7) can be placed inside or outside the walking envelope.

Same control loop as sim/current_budget.py (imported unchanged for the upstream MjInfer and its stubs), the same 7
cases, logging every joint angle and every policy action at 50 Hz after the 2 s settle and before any fall. Runs the
trained model ("stock") and, when C8 has written it, the model of the robot we will build ("ours",
<out>/c8_added_mass/added_mass/models/ours, made by sim/added_mass_sim.py). Writes <out>/e9_envelope.json.
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e9_joint_envelope.py   (after c8_policy_mass.py)
"""
import contextlib
import io as _io
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402


def run_case(CB, MI, mujoco, scene_path, sch, dur, pushes):
    with contextlib.redirect_stdout(_io.StringIO()):            # upstream MjInfer prints its joint lists
        m = MI.MjInfer(scene_path, CB.REF, CB.ONNX, standing=False)
    _ga = m.get_accelerometer
    m.get_accelerometer = lambda d, _ga=_ga: np.array(_ga(d), dtype=float) - np.array([1.3, 0, 0])
    model, data = m.model, m.data
    names = list(m.actuator_names)
    qa = [model.jnt_qposadr[model.joint(n).id] for n in names]
    fb = m._floating_base_qpos_addr
    trunk = model.body("trunk_assembly").id
    lo, hi = np.full(len(names), np.inf), np.full(len(names), -np.inf)
    amax, tmax = np.zeros(len(names)), np.zeros(len(names))
    fallen, counter = False, 0
    for k in range(int(dur / m.sim_dt)):
        t = (k + 1) * m.sim_dt
        data.xfrc_applied[:] = 0
        for (t0, t1, f) in (pushes or []):
            if t0 <= t < t1:
                data.xfrc_applied[trunk, :3] = f
        mujoco.mj_step(model, data)
        counter += 1
        if counter % m.decimation == 0:
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
            pos, quat = data.qpos[fb:fb + 3], data.qpos[fb + 3:fb + 7]
            Rm = np.zeros(9)
            mujoco.mju_quat2Mat(Rm, quat)
            if pos[2] < 0.10 or Rm[8] < 0.5:
                fallen = True
            if t > 2.0 and not fallen:
                q = data.qpos[qa]
                lo, hi = np.minimum(lo, q), np.maximum(hi, q)
                amax = np.maximum(amax, np.abs(np.asarray(action, float)))
                tmax = np.maximum(tmax, np.abs(np.asarray(m.motor_targets, float)))
    jr = {n: [float(model.jnt_range[model.joint(n).id][0]), float(model.jnt_range[model.joint(n).id][1])] for n in names}
    deg = lambda v: round(float(np.degrees(v)), 1) if np.isfinite(v) else None   # noqa: E731
    return dict(lo_deg={n: deg(v) for n, v in zip(names, lo)}, hi_deg={n: deg(v) for n, v in zip(names, hi)},
                action_abs_max={n: round(float(v), 3) for n, v in zip(names, amax)},
                target_abs_max_deg={n: deg(v) for n, v in zip(names, tmax)}, fell=fallen, action_scale=float(m.action_scale),
                default_deg={n: deg(v) for n, v in zip(names, m.default_actuator)},
                range_deg={n: [deg(a), deg(b)] for n, (a, b) in jr.items()})


def main():
    R = V.Result("E9", "Joint angles the stock policy uses in the sim walk, trained mass and our build (sim pass only)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/e9_joint_envelope.py",
                 "7 current_budget.py cases on the trained model and on our build's model (C8): min and max of every joint "
                 "angle, the largest policy action and motor target, after the 2 s settle and before a fall; MJCF ranges",
                 "Falls, get-up, manual moves and find_soft_offsets.py (they can reach the full joint range); real servo tracking")
    od = os.path.join(V.out_dir(), "e9_envelope")
    os.makedirs(od, exist_ok=True)
    js = os.path.join(V.out_dir(), "e9_envelope.json")
    ours_dir = os.path.join(V.out_dir(), "c8_added_mass", "added_mass", "models", "ours")
    reuse = os.environ.get("VERIFY_REUSE") == "1" and os.path.exists(js) and "stock" in json.load(open(js))
    if not reuse:
        os.environ.update(ODM_PLAYGROUND=V.PLAYGROUND, ODM_OUT=od, ODM_ONNX=os.path.join(V.REPO, "BEST_WALK_ONNX_2.onnx"),
                          ODM_SCRATCH=os.path.join(V.out_dir(), "c8_added_mass"))
        sys.path.insert(0, V.lab("sim"))
        try:
            import current_budget as CB          # unchanged lab file: upstream MjInfer import and stubs
        except Exception as e:                    # noqa: BLE001
            R.not_run("could not import sim/current_budget.py: %s" % e)
            R.write()
            return
        import mujoco
        MI = CB.MI
        out = {"stock": {}}
        for label, scene, sch, dur, pushes in CB.CASES:
            out["stock"][label] = run_case(CB, MI, mujoco, str(CB.ROOT / "xmls" / scene), sch, dur, pushes)
        if os.path.isdir(ours_dir):
            with contextlib.redirect_stdout(_io.StringIO()):
                import added_mass_sim as AMS     # unchanged lab file (agent M): its asset loader reads a model folder
            AMS._ASSET_DIR[0] = ours_dir
            out["ours"] = {}
            for label, scene, sch, dur, pushes in CB.CASES:
                out["ours"][label] = run_case(CB, MI, mujoco, os.path.join(ours_dir, scene), sch, dur, pushes)
        else:
            out["ours_missing"] = "C8 model folder not found: %s" % ours_dir
        json.dump(out, open(js, "w"), indent=1)
    env = json.load(open(js))
    if "ours" not in env:
        R.find("WARN", "our build's model was not run (%s)" % env.get("ours_missing", "?"))
    for model in ("stock", "ours"):
        if model not in env:
            continue
        E = env[model]
        walk = [k for k in E if k != "stand_in_place" and E[k]["lo_deg"]["left_hip_yaw"] is not None]
        names = list(E[walk[0]]["lo_deg"])

        def rng(n):
            return (min(E[k]["lo_deg"][n] for k in walk), max(E[k]["hi_deg"][n] for k in walk))
        if model == "stock":
            R.key("in the walk (trained mass): hip yaw %+.1f to %+.1f deg (range +/-30), hip pitch %+.1f to %+.1f, knee up to %+.1f "
                  "(limit +90); largest policy action %.2f" % (
                      min(rng("left_hip_yaw")[0], rng("right_hip_yaw")[0]), max(rng("left_hip_yaw")[1], rng("right_hip_yaw")[1]),
                      min(rng("left_hip_pitch")[0], rng("right_hip_pitch")[0]), max(rng("left_hip_pitch")[1], rng("right_hip_pitch")[1]),
                      max(rng("left_knee")[1], rng("right_knee")[1]), max(max(E[k]["action_abs_max"].values()) for k in walk)))
        R.ev("%s model, cases %s" % (model, ", ".join(walk)))
        for n in names:
            lo, hi = rng(n)
            rg = E[walk[0]]["range_deg"][n]
            R.ev("%s %s: %+.1f to %+.1f deg (MJCF range %+.1f to %+.1f)" % (model, n, lo, hi, rg[0], rg[1]))
    R.write()


if __name__ == "__main__":
    main()
