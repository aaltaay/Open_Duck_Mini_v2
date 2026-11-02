# Current budget from the stock walk (sim pass only)

Run 2026-11-01 (America/New_York) in this session's container. Script: sim/current_budget.py. Outputs (JSON and a trace plot) were written to the session scratch folder only, not to git and not yet to F:. Regenerate with:
`ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_ONNX=<BEST_WALK_ONNX_2.onnx> ODM_OUT=<folder> python3 sim/current_budget.py`

Why: POWER.md section 2 sized the BMS, fuse, switch and regulator from estimates (4 to 8 A walking, 15 to 20 A peaks). This replaces the estimates with numbers from the same model the policy was trained on.

## Method
- Same control loop as sim/run_stock_walk.py: upstream MjInfer unmodified, BEST_WALK_ONNX_2, 50 Hz control, motor speed limit 5.24 rad/s, MuJoCo 3.17.0, onnxruntime 1.31.1.
- Every servo's actuator torque F and joint speed w logged at the physics rate (500 Hz).
- Torque to current with the BAM DC motor model the MJCF actuators come from (SERVO_DEEP_DIVE.md E3): forcerange = vin x kt / R = 3.23 Nm at vin 7.4 V, damping = kt^2 / R + fv = 0.56. Applied voltage u = F x R / kt, motor current I = (u - kt x w) / R, power P = u x I. Check: at stall this gives 7.4 / R = 2.67 A, the same as the Feetech stall current class (2.5 to 2.7 A).
- kt for the current MJCF is not published, so three values with kt / R fixed were run: 1.148, 1.21164 (BAM m1.json) and 1.28. The table uses 1.148, which gives the highest current.
- Bus current = sum of positive servo power / 7.4 V (no credit for braking power shared between servos, so it is conservative).
- Statistics start after the first 2 s of each run (the drop onto the floor at start). The whole-run maximum is listed separately.
- Pushes: 15 N for 0.1 s on the trunk every 3 s, left and right in turn.

## Result: servo bus current at 7.4 V (A)
Re-run 2026-11-01 6:41 PM ET with the upstream +1.3 accelerometer bias removed (it is in the upstream sim loop only, not in training or on the robot; SIM_WALK.md note). The first run (with the bias) gave the same picture within about 5%: backlash walk mean 3.19 A, worst 100 ms 4.78 A.
| Case | Falls | Mean | Max 1 s avg | Max 100 ms avg | Max 20 ms avg | Max 2 ms | Whole run max |
|---|---|---|---|---|---|---|---|
| Stand, zero command | none | 0.19 | 0.22 | 0.23 | 0.24 | 0.24 | 3.15 |
| Walk forward 0.15 m/s | none | 2.22 | 2.31 | 3.08 | 4.02 | 4.97 | 4.97 |
| Turn 1.0 rad/s | none | 2.38 | 2.52 | 3.21 | 5.39 | 6.40 | 6.40 |
| Walk sideways 0.2 m/s | none | 2.25 | 2.46 | 3.81 | 5.92 | 7.19 | 7.19 |
| Walk forward, backlash model | none | 3.24 | 3.44 | 4.72 | 6.77 | 8.30 | 8.30 |
| Walk forward, rough terrain, backlash model | at 0.28 s (start drop only) | 2.65 | 2.96 | 3.92 | 6.15 | 7.80 | 13.61 |
| Walk forward with pushes | at 10.68 s | 1.89 | 2.36 | 3.59 | 5.26 | 6.27 | 6.27 |

Highest single servo current while walking: 3.35 A peak (knee, backlash model), 1.45 A RMS. The knees sit at the torque limit 15 to 21% of the time in the backlash model, under 4% in the plain model.

## Pack side
The hand calculation below uses the first run (within 5% of the re-run). The ngspice model in sim/POWER_PATH_SIM.md is the better pack number because it includes every series resistance, BEC dropout and the 5 V branch: about 5.1 to 5.7 A mean, 10 to 11 A peak, 5.4 to 5.8 A RMS while walking.
Pack current = bus power / (0.85 x pack voltage) + 5 V branch + servo electronics allowance. 0.85 is an assumed regulator efficiency (Castle does not publish one).

| Item | At 7.4 V pack | At 6.4 V pack |
|---|---|---|
| Servos, walking mean (backlash model, 3.19 A bus) | 3.75 A | 4.34 A |
| Servos, worst 100 ms while walking (4.78 A bus) | 5.62 A | 6.50 A |
| Servos, fall or start drop, worst 20 ms (9.0 to 12.5 A bus) | 10.6 to 14.6 A | 12.3 to 16.9 A |
| 5 V branch (Pi, 2 x SG90, amp): typical 3 W, peak 12 W | 0.48 A, peak 1.91 A | 0.55 A, peak 2.21 A |
| Servo electronics: Feetech spec (2020, machine-translated copy via the parts check) gives idle 6 mA at 7.4 V, so 14 servos draw about 0.08 A; the earlier 14 x 0.15 A allowance was the 150 mA no-load running current and is an upper bound | 0.10 A (2.40 A upper bound) | 0.11 A (2.78 A upper bound) |

- Walking mean: about 4.2 A without the allowance, at most 6.6 A with it (7.4 V pack); 4.9 to 7.7 A near empty.
- Walking worst 100 ms: about 7.5 A, at most 9.9 A with every allowance stacked.
- Falls: up to about 17 A for about 20 ms with everything stacked at a low pack.

## What this means for the parts (decisions in DECISIONS.md, D8)
- BMS: Tenergy 32175 (10 A working, over-current detect 22 +/- 5 A after 8 +/- 4 ms) covers the sim walking numbers; a fall at a low pack with every allowance stacked can reach the bottom of its trip band (17 A). Builders upstream report BMS cut-outs with 10 A class boards (issue 33 TODO, third-party log, UPSTREAM_ISSUES.md G4), so this is checked on the bench with current pulses and in the walking log (TEST_PLAN.md sections 3 and 9).
- Fuse: 15 A ATO stays (D3). It carries 16.5 A indefinitely and needs seconds at 20 A to open, so 20 ms fall peaks do not blow it.
- Switch: Pololu 2815 runs about 6 A with the MOSFETs at 55 C (Pololu table, 12 V, 22 C still air); the walking mean sits below that.
- Servo regulator: the Castle CC BEC Pro (15 A continuous with airflow, 20 A peak) runs at about 3.2 A mean and 4.8 A peaks while walking, so airflow is not needed.
- Battery: 2 x P30B, 3.0 Ah at 7.2 V nominal, about 21.6 Wh. Walking draws about 22 W (plain model) to 31 W (backlash model) from the pack, so about 40 to 60 minutes of continuous walking. Sim pass only, not measured.

## Limits
- Sim pass only. Real servos have gear friction and backlash beyond the model, and issue #48 reports real servos tracking worse than sim. Treat the real current as possibly up to 2 x these numbers until a bench test logs Present Current on the real robot.
- Servo idle current 6 mA (Feetech spec via the parts check, not re-measured); measure it on the first servo (test order TO1). The servo cuts its own torque after more than 2 A for 2 s by default.
- The ngspice power-path model (sim/POWER_PATH_SIM.md) uses these traces to find the voltage at every servo.
- Flat floor, rough terrain and pushes only. No get-up, no stairs (the duck is exempt from stairs).
