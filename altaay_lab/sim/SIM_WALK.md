# Sim walk check: stock BEST_WALK_ONNX_2 policy in MuJoCo

Run on the lab box 2026-11-01 (America/New_York). Video: /workspace/odm_share/odm_v2_stock_walk.mp4 (box copy only, 26 s, 960x544, 50 fps, not committed). Stills: sim/odm_v2_stock_walk_still_8s.png (walking forward), sim/odm_v2_stock_walk_still_17s_turn.png (turning).

## What ran
- Policy: Open_Duck_Mini BEST_WALK_ONNX_2.onnx (repo commit 981750b, 2025-04-02). Input obs [1, 101], output 14 actions.
- Model: Open_Duck_Playground playground/open_duck_mini_v2/xmls/scene_flat_terrain.xml at pin b9be205. The MJCF and mujoco_infer files were last changed 2025-03-31, before the policy date, so the pair matches.
- Reference motion: playground/open_duck_mini_v2/data/polynomial_coefficients.pkl (upstream default).
- Engine: MuJoCo 3.17.0, onnxruntime 1.31.1, Python 3.13, headless EGL.
- Script: sim/run_stock_walk.py. It imports upstream MjInfer and MJInferBase unmodified and copies the body of MjInfer.run() line for line (phase update, get_obs, OnnxInfer, action history, motor_targets = default + 0.25 x action, motor speed limit 5.24 rad/s, data.ctrl). sim_dt 0.002 s, decimation 10, so 50 Hz control.
- Differences from upstream, all outside the control loop: no interactive viewer (offscreen renderer instead), commands come from a fixed schedule instead of keyboard keys, and two training-only modules (base.py needs jax and mujoco_playground, common/utils.py needs jax) are replaced by small stubs. The stub get_assets reads the same xmls and assets folders. The low-pass filter that the stub replaces is commented out upstream, so it is never used.

## Command schedule
0 to 2 s stand (all zero), 2 to 14 s forward 0.15 m/s (the upstream max, COMMANDS_RANGE_X), 14 to 20 s turn left 1.0 rad/s (upstream max), 20 to 26 s forward 0.15 m/s.

## Result
- Falls: none. Trunk height stayed 0.154 to 0.169 m, trunk up-vector z stayed at 0.992 or more (under 8 degrees tilt).
- Forward speed: 0.097 m/s measured (4 to 14 s) and 0.096 m/s (22 to 26 s), about 65% of the 0.15 m/s command.
- Heading drift while walking straight: about 4 degrees over 10 s, drifting slightly left.
- Turning: 275 degrees in 6 s, about 0.81 rad/s for a 1.0 rad/s command. It moved 7 cm while turning.
- Distance: 2.7 m walked path, 1.32 m net.

## Battery and actuator assumption
The MJCF has no voltage. Each joint is a position actuator (kp 13.37, forcerange 3.23 Nm, damping 0.56, frictionloss 0.068, armature 0.027) fitted with BAM, whose STS3215 model uses vin = 7.4 V (bam/feetech/actuator.py). So the sim assumes a constant 7.4 V supply, no sag. Our 7.2 V regulator setting is close to that. A full 8.4 V pack (stock build) would make real servos faster and stronger than the sim. Below about 7.3 V the pack voltage reaches the servos directly, so real servos will be slower than the sim near the end of a charge. Flat floor only, no backlash variant, no sensor noise.

## Note 2026-11-01 6:44 PM ET: accelerometer bias in the upstream sim loop
Upstream MjInfer.get_obs (playground/open_duck_mini_v2/mujoco_infer.py line 74, pin b9be205) adds +1.3 to accelerometer x. Training does not (joystick.py line 502 uses accelerometer.at[0].set(...) without keeping the result, so it does nothing) and the robot runtime does not. The run above copied the upstream loop, so it included the bias. A re-run with the bias removed (sim/current_budget.py, default since this date) walks forward, turns and sidesteps with no falls in all flat and rough cases; servo currents change by less than 5% (sim/CURRENT_BUDGET.md). Forward speed was not re-measured. Source: upstream Playground PR 24 and the code at the pins (UPSTREAM_ISSUES.md G7).
