# Run C reward and command changes (Open_Duck_Playground b9be205, joystick.py)

The weights below are the training config. The exp() line is calc only. Walk speeds are sim pass only in SUMMARY.md and eval_table.md.

On top of the PR 74 config (12 V STS3215 actuator, 3S bus point, 70 g cell in the trunk, backlash scene, 150,000,000 steps, 8,192 envs, unchanged runner).

| Setting | Upstream / PR 74 | Run 1 (stood still) | Run C (walks) |
|---|---|---|---|
| lin_vel_x command range | [-0.15, 0.15] | [-0.15, 0.40] | [-0.15, 0.40] |
| tracking_lin_vel weight | 2.5 | 2.5 | 7.5 |
| tracking_sigma | 0.01 | 0.01 | 0.03 |
| feet_air_time weight | not used | not used | 5.0 (existing rewards.reward_feet_air_time, wired into the reward dict) |
| action_rate weight | -0.5 | -1.0 | -0.5 |
| stand_still weight | -0.2 | -0.2 | -0.1 |
| torques, alive, imitation, tracking_ang_vel | -1e-3, 20, 1.0, 6.0 | same | same |

Why: with sigma 0.01, a 0.25 to 0.40 m/s command gives almost zero tracking reward to any reachable speed (exp(-(0.4-0.15)^2/0.01) = 0.002, calc only), so most of the widened range taught nothing, and standing scored nearly as well as walking against the alive term. Run 1 and a partial run B ([-0.15, 0.30], action_rate -0.5, stopped at 65M) both learned to stand.

The patched file is joystick_runC.py in this folder.

## Run D (2026-11-14)

Superseded as the current training config by the rows below. Run C is kept. The patched file is joystick_runD.py.

On top of run C. Command range stays [-0.15, 0.40]. The new costs use the ST-3215-C018 sheet values in train_sts12.json: stall 2.942 Nm / 2.7 A gives Kt 1.0896 Nm/A (calc only), no-load current 0.180 A (cited). Knee index is left 3 and right 12.

| Setting | Run C | Run D |
|---|---|---|
| knee_current weight | not used | -0.5, sum over both knees of (absolute torque / Kt + 0.180 A) squared |
| pack_hinge weight | not used | -0.02, square of (sum of absolute torque / Kt + 14 times 0.180 A) above 13 A |

The 13 A hinge is a reward threshold. It is not a change to the 15 A fuse.
