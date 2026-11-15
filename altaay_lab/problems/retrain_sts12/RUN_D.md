# Run D: knee current retrain (2026-11-14)

Every number is sim pass only unless marked calc only or cited. Nothing here is proven on hardware.

Run C stays in this folder. It is superseded as the current walk. The run C policy, reward file, and tables are kept.

A 2026-11-12 jog attempt was also called run D. That one failed (no flight, slower than run C). This file is the knee-current retrain.

## Training

- Pipeline: same as run C. Open_Duck_Playground b9be205 runner, flat_terrain_backlash, joystick env, PPO config BerkeleyHumanoidJoystickFlatTerrain (8,192 envs), jax 0.7.0, mujoco 3.3.4, brax 0.12.4. Warm start from the run C final checkpoint. 300,000,000 steps (final 300,482,560).
- Model (apply_runD.py, model_runD.json): mass from sim/mass_budget.py as merged on altaay-lab, MuJoCo loaded total 2.9491 kg, equal to the rollup (CAD mass model). No extra 70 g cell. The budget already has three P45B cells, so the old train_sts12.py +70 g would double count. Actuator from train_sts12.actuators() at the held 12.0 V rail (BEC_HOLD=1): lowest port 11.900 V, forcerange 2.9175 Nm, kp 15.4546 on the backlash scene (calc only). Knee range -90 to 147 deg.
- Rewards (joystick_runD.py, REWARD_CHANGES.md): run C plus knee_current -0.5 (sum over both knees of (absolute torque / Kt + 0.180 A) squared, Kt 1.0896 Nm/A from the C018 sheet) and pack_hinge -0.02 (square of the sum of absolute torque / Kt + 14 times 0.180 A, above 13 A). Command range unchanged [-0.15, 0.40]. The 13 A hinge is a reward threshold. The fuse stays 15 A (cited).
- Trainer eval reward 205 at step 0, 288 at 193M, 225 at the final step (noisy, same late dip as run C). Knee cost per eval episode 1363 to 611 (sim pass only).
- Policy: sts12_runD_policy.onnx, the final 300,482,560 export, 101 in, 14 out, same format as run C. Sha256 7a0be46af5b8061ee7b85aaca4050772da4fbd29303fffad76a93d59225dfb1e (the file). Intermediate 60 s sweeps of 214M, 258M, and 279M were within a few percent of the final.

## Power set points

Checked against verify/part_limits.yaml and wiring/netlist.yaml. Run D does not add a set point.

| Set point | Value | Limit file | Netlist | Label |
|---|---|---|---|---|
| Servo regulator | 12.0 V | servo_reg output 8 V to 24 V | U1 set to 12.0 V | cited |
| Servo domain | 11.52 V to 12.48 V | 12.0 V plus or minus 4 percent | SERVO_12V0 | cited |
| Lowest training port | 11.900 V | inside 11.52 V to 12.48 V | wire drop under the held rail, not a new set point | calc only |
| Pack window | 9.0 V to 12.6 V | 3S P45B | PACK_9V0_12V6 | cited |
| Walk stop | 10.0 V | walk_pack_min_v 10.0 | PACK walk_stop_v 10.0 | cited |
| Pack fuse | 15 A | fuse i_fuse_a 15 | Littelfuse 0287015, fuse_a 15 | cited |
| Regulator current row | 16.5 A at 10 V in, 12 V out | i_out_12v_at_10vin_a 16.5 | U1 ratings | cited |
| Reward hinge | 13 A | under the 15 A fuse | not in the netlist | the reward |

## Comparison sessions

Filed under eval/. These are the comparison runs. The live `make twin` report is altaay_lab/twin/out/REPORT.md.

The merged twin report before this change (30.07 walking minutes, 17.48 A pack peak) was the stock BEST_WALK_ONNX_2 policy. `make twin` set ODM_ONNX inside walk(), after parts_truth had imported added_mass_sim. That import setdefaulted ODM_ONNX to BEST_WALK_ONNX_2, and current_budget froze the path. Those two figures are the stock policy and are superseded.

| What | Stock (what the merged report ran) | Run C | Run D | Label |
|---|---|---|---|---|
| Walking minutes | 30.09 | 24.21 | 41.18 | sim pass only |
| Session length | 42.13 min (10 V cutoff) | 45.00 min (clock) | 41.18 min (10 V cutoff) | sim pass only |
| 55 C rests | 3 | 4 | 0 | sim pass only |
| Path | 248.16 m | 217.02 m | 381.31 m | sim pass only |
| Body speed (report) | 0.069 m/s | 0.066 m/s | 0.132 m/s | sim pass only |
| Right knee RMS while walking | 1.51 A | 1.62 A | 0.88 A | sim pass only |
| Hottest reading | right knee 55.0 C (rest stop) | right knee 55.0 C (rest stop) | left hip yaw 47.1 C | sim pass only |
| Knee peak, 45 min replay | 55.0 C | 55.0 C | 38.4 C | sim pass only |
| Pack peak current | 16.81 A | 15.65 A | 13.65 A | sim pass only |
| Time at or above 15 A | 0.080 s | 0.008 s | 0.000 s | sim pass only |
| Pack mean current | 4.49 A | 4.00 A | 4.93 A | sim pass only |
| Battery left at end | 29.9 percent | 33.3 percent | 24.8 percent | sim pass only |
| Cell temperature end | 43.2 C | 42.3 C | 44.3 C | sim pass only |
| Falls | 0 | 0 | 0 | sim pass only |
| Dock sim seat | did not sit | did not sit | did not sit | sim pass only, camera BLOCKER |
| Sit check (fold from settled stand to 147 deg, torque off) | reached | reached | reached | sim pass only |

Twin noise: two stock runs of the same code gave 17.48 A vs 16.81 A pack peak and "sat" vs "did not sit" on the dock, so treat about 1 A and the dock line as noise. The 17.48 A figure is the one in the merged report.

## 60 s constant command sweep

eval/sweep.py, same twin settings. The sweep json records the export name 2026_11_14_201938_300482560.onnx. That export is the file filed here as sts12_runD_policy.onnx (final step 300,482,560).

| Cmd m/s | C speed | D speed | C knee RMS L/R A | D knee RMS L/R A | C pack peak A | D pack peak A | C pack mean A | D pack mean A | falls C/D |
|---|---|---|---|---|---|---|---|---|---|
| 0.10 | 0.000 | 0.091 | 0.84 / 0.72 | 0.73 / 0.80 | 1.9 | 7.3 | 1.57 | 3.62 | 0 / 0 |
| 0.15 | 0.119 | 0.131 | 1.47 / 1.54 | 0.88 / 0.87 | 9.0 | 9.3 | 4.67 | 4.22 | 0 / 0 |
| 0.20 | 0.164 | 0.170 | 1.63 / 1.69 | 0.94 / 0.92 | 11.6 | 10.5 | 6.27 | 5.03 | 0 / 0 |
| 0.25 | 0.193 | 0.200 | 1.71 / 1.73 | 1.01 / 0.99 | 13.2 | 11.0 | 7.30 | 5.71 | 0 / 0 |
| 0.30 | 0.220 | 0.221 | 1.76 / 1.78 | 1.05 / 1.07 | 17.7 | 11.2 | 8.18 | 6.26 | 0 / 0 |

All sim pass only. The 0.10 dead zone is gone in run D (it walks at 0.091 m/s). Knee current moved partly to the ankles and hip roll (ankles 0.84 to 1.04 A at 0.20), so no servo is above about 1.05 A RMS at 0.20 m/s.

## make twin rerun

`make twin` after the policy pin (sim pass only, twin/out/REPORT.md). The loader recorded sts12_runD_policy.onnx on every call.

| What | This rerun | Filed run D session | Label |
|---|---|---|---|
| Walking minutes | 41.48 | 41.18 | sim pass only |
| Rests | 0 | 0 | sim pass only |
| Knee peak | 38.4 C | 38.4 C | sim pass only |
| Hottest reading | left hip yaw 47.1 C | left hip yaw 47.1 C | sim pass only |
| Right knee RMS | 0.88 A | 0.88 A | sim pass only |
| Pack peak | 13.81 A | 13.65 A | sim pass only |
| Time at or above 15 A | 0.000 s | 0.000 s | sim pass only |
| Body speed | 0.130 m/s | 0.132 m/s | sim pass only |
| Path | 379.05 m | 381.31 m | sim pass only |
| Battery left | 24.2 percent | 24.8 percent | sim pass only |
| Dock sim seat | did not sit | did not sit | sim pass only, camera BLOCKER |

The pack peak moved 0.16 A. That is inside the about 1 A twin noise named above. The knee stays well under 55 C. The peak stays under the 15 A fuse.

## Not done

- Fold-to-sit from a walk and sit-to-stand were not trained. They need a new task with a sit command and a reference motion.
- No hardware. The knee heat model is still calibrated to one published bench curve.
- Camera docking is still BLOCKER.
