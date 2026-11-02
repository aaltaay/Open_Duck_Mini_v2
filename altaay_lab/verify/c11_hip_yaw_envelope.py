"""C11: screws F198 and F211 (fastener schedule) hit body_middle_bottom once |hip yaw| passes their collision onset
(21.7 deg in altaay_lab/fasteners/FASTENERS.md). Does the stock policy stay under it, with margin, when it walks and turns?

Evidence, each from its own source:
  onset      the hip yaw sweep rows of F198 and F211 in fasteners/fasteners.json (smallest |angle| with an overlap) and
             the 21.7 deg FASTENERS.md states
  sim        E9: largest |hip yaw| over the 7 current_budget.py cases (walk, turn 1.0 rad/s, side step, backlash, rough,
             pushes) on the trained model and on our build's model, after the 2 s settle and before a fall
  policy     bound by construction: hip yaw target = default pose + action_scale x action (Runtime
             scripts/v2_rl_walk_mujoco.py line 290, action_scale 0.25); |action| <= 1 if the exported policy ends in tanh,
             tested here by feeding 6000 random observations (scale 1, 3 and 10) to BEST_WALK_ONNX_2.onnx
  runtime    clamps on the hip yaw target in the Runtime at 376de65 (motor target clip, servo angle limit registers)
PASS when the walk and the turn stay under the onset by at least MARGIN_DEG. The policy bound and the Runtime clamps are
reported as context (they say what happens outside the simulated cases).
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c11_hip_yaw_envelope.py   (after e9_joint_envelope.py)
"""
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

MARGIN_DEG = 5.0
SCREWS = ("F198", "F211")


def main():
    R = V.Result("C11", "Hip yaw the stock policy uses (walk and turn) stays under the F198/F211 collision onset (21.7 deg)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c11_hip_yaw_envelope.py",
                 "Collision onset from the fastener sweep; largest |hip yaw| in 7 sim cases (turn 1.0 rad/s included) on the "
                 "trained model and our build; the policy's bound (default + 0.25 x tanh action) checked on 6000 random "
                 "inputs; clamps in the Runtime code",
                 "Real servo overshoot, falls, manual moves, find_soft_offsets.py, other policies or a wider command range")
    fj, envp = V.lab("fasteners", "fasteners.json"), os.path.join(V.out_dir(), "e9_envelope.json")
    if not os.path.exists(envp):
        R.not_run("E9 envelope not found (run e9_joint_envelope.py first)")
        R.write()
        return
    R.inp(fj, V.lab("fasteners", "FASTENERS.md"), os.path.join(V.REPO, "BEST_WALK_ONNX_2.onnx"))
    # ---------------------------------------------------------------- onset
    onset = 21.7
    doc = re.findall(r"from (?:left|right)_hip_yaw -?(\d+\.\d) deg on", open(V.lab("fasteners", "FASTENERS.md")).read())
    if doc:
        onset = min(float(x) for x in doc)
    sweep_onsets = []
    if os.path.exists(fj):
        D = json.load(open(fj))
        for h in (D.get("sweep") or {}).get("hits", []):
            if h["id"] in SCREWS and "hip_yaw" in h["where"] and "+" not in h["where"] and h.get("angles"):
                sweep_onsets.append((h["id"], h["where"], min(abs(a) for a in h["angles"])))
    if sweep_onsets:
        onset = min(onset, min(o[2] for o in sweep_onsets))
    R.ev("collision onset: FASTENERS.md %s deg; fasteners.json sweep %s; used %.1f deg" % (
        ", ".join(doc) or "?", ", ".join("%s %s from %.1f deg" % o for o in sweep_onsets) or "no single-joint rows", onset))
    # ---------------------------------------------------------------- sim envelope (E9)
    E0 = json.load(open(envp))
    rows = []
    for model in ("stock", "ours"):
        for case, c in (E0.get(model) or {}).items():
            if case == "stand_in_place" or c["lo_deg"]["left_hip_yaw"] is None:
                continue
            m = max(abs(c["lo_deg"][j]) for j in ("left_hip_yaw", "right_hip_yaw"))
            m = max(m, max(abs(c["hi_deg"][j]) for j in ("left_hip_yaw", "right_hip_yaw")))
            rows.append((m, model, case, c["action_abs_max"]["left_hip_yaw"], c["action_abs_max"]["right_hip_yaw"],
                         c["target_abs_max_deg"]["left_hip_yaw"], c["target_abs_max_deg"]["right_hip_yaw"]))
    if not rows:
        R.not_run("E9 envelope has no walking case")
        R.write()
        return
    for m, model, case, al, ar, tl, tr in sorted(rows, key=lambda r: (r[1], r[2])):
        R.ev("%s, %s: largest |hip yaw| %.1f deg (largest |target| %.1f deg; largest |action| %.2f left, %.2f right)" % (
            model, case, m, max(tl, tr), al, ar))
    worst = max(rows)
    turn = [r for r in rows if r[2] == "turn_1.0"]
    over = max(r[0] - max(r[5], r[6]) for r in rows)
    R.ev("the joint passes its commanded target by up to %.1f deg in the sim (dynamics)" % over)
    R.ev("worst over %d runs: %.1f deg (%s, %s); turn 1.0 rad/s: %s; margin to the %.1f deg onset: %.1f deg" % (
        len(rows), worst[0], worst[1], worst[2], ", ".join("%s %.1f deg" % (r[1], r[0]) for r in turn) or "not run", onset,
        onset - worst[0]))
    if not turn:
        R.find("FAIL", "the turn case is missing from the envelope", fix="re-run e9_joint_envelope.py")
    if onset - worst[0] < MARGIN_DEG:
        R.find("FAIL", "hip yaw reaches %.1f deg in %s (%s), within %.1f deg of the %.1f deg collision onset (margin rule %.0f deg)" % (
            worst[0], worst[2], worst[1], onset - worst[0], onset, MARGIN_DEG),
            fix="limit hip yaw in the Runtime (clip the motor target) and record it in DECISIONS.md, or relieve body_middle_bottom")
    # ---------------------------------------------------------------- policy bound
    bound_txt = "not tested"
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(os.path.join(V.REPO, "BEST_WALK_ONNX_2.onnx"), providers=["CPUExecutionProvider"])
        inp = sess.get_inputs()[0]
        n = int(inp.shape[1])
        rng = np.random.default_rng(0)
        amax = 0.0
        for scale in (1.0, 3.0, 10.0):
            x = (rng.standard_normal((2000, n)) * scale).astype(np.float32)
            y = np.concatenate([sess.run(None, {inp.name: x[i:i + 1]})[0] for i in range(len(x))])
            amax = max(amax, float(np.abs(y).max()))
        c = next(iter(E0["stock"].values()))
        scale_a = c["action_scale"]
        dflt = max(abs(c["default_deg"]["left_hip_yaw"]), abs(c["default_deg"]["right_hip_yaw"]))
        bound = dflt + np.degrees(scale_a * min(1.0, amax) if amax <= 1.0 + 1e-6 else scale_a * amax)
        bound_txt = "%.1f deg with the sim overshoot" % (bound + over)
        R.ev("policy output on 6000 random observations (scale 1, 3, 10): largest |action| %.4f%s; hip yaw target bound = default "
             "%.1f deg + %.2f x %s rad = %.1f deg" % (amax, " (bounded by 1, as a tanh output is)" if amax <= 1.0 + 1e-6 else "",
                                                     dflt, scale_a, "1" if amax <= 1.0 + 1e-6 else "%.2f" % amax, bound))
        if bound + over < onset:
            R.ev("the stock policy cannot command more than %.1f deg of hip yaw (%.1f deg with the sim overshoot), %.1f deg under "
                 "the onset" % (bound, bound + over, onset - bound - over))
        else:
            R.find("WARN", "the policy can command up to %.1f deg of hip yaw (%.1f deg with the sim overshoot), past the %.1f deg "
                   "onset" % (bound, bound + over, onset))
    except Exception as e:                    # noqa: BLE001
        R.find("WARN", "policy bound not tested: %s" % e)
    # ---------------------------------------------------------------- Runtime clamps
    walk = os.path.join(V.RUNTIME, "scripts", "v2_rl_walk_mujoco.py")
    if os.path.exists(walk):
        src = open(walk).read().splitlines()
        tgt = [i + 1 for i, ln in enumerate(src) if "self.motor_targets = self.init_pos + action * self.action_scale" in ln]
        clip_live = [i + 1 for i, ln in enumerate(src) if "np.clip(" in ln and "motor_targets" in ln and not ln.strip().startswith("#")]
        clip_off = [i + 1 for i, ln in enumerate(src) if "np.clip(" in ln and ln.strip().startswith("#")]
        conf = open(os.path.join(V.RUNTIME, "scripts", "configure_motor.py")).read()
        lim = re.search(r"angle_limit|min_angle|max_angle|set_angle", conf + open(os.path.join(V.RUNTIME, "mini_bdx_runtime",
                                                                                           "mini_bdx_runtime", "rustypot_position_hwi.py")).read())
        R.ev("Runtime 376de65: motor target = init_pos + action x action_scale at line %s; live clip of the targets: %s; "
             "commented-out clip at lines %s; servo angle limit registers set by configure_motor.py or the HWI: %s" % (
                 ",".join(map(str, tgt)) or "?", clip_live or "none", clip_off or "none", bool(lim)))
        if not clip_live and not lim:
            R.find("WARN", "nothing in the Runtime limits hip yaw: the policy bound keeps the walk under the onset, but a manual "
                   "move, find_soft_offsets.py (Runtime issue 32 moves every joint) or a fall can still reach 21.7 to 30 deg and "
                   "press the F198/F211 heads into body_middle_bottom",
                   fix="DECISIONS.md: record the hip yaw limit (for example the STS3215 angle limit registers set to about "
                       "+/-20 deg of travel for IDs 10 and 20 in configure_motor.py, or a clip in the walk script), or relieve "
                       "body_middle_bottom at the two heads", where="altaay_lab/DECISIONS.md")
    R.key("largest hip yaw angle %.1f deg (%s, %s), turn %s deg; onset %.1f deg; margin %.1f deg (rule %.0f); policy bound "
          "%s" % (
        worst[0], worst[1], worst[2], " and ".join("%.1f" % r[0] for r in turn) or "-", onset, onset - worst[0], MARGIN_DEG,
        bound_txt))
    R.write()


if __name__ == "__main__":
    main()
