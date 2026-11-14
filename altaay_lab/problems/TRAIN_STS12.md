# 12 V walk retrain config

Written 2026-11-12 ET. The trainer is the existing playground runner. This file is the config for a 12 V STS3215 on three P45B cells, with the third cell's 70 g in the trunk. A shipping policy was not produced. Nothing was spent. No GPU was started.

Labels: cited, calc only, sim pass only, BLOCKER.

## What is trained

The runner is Open_Duck_Playground at b9be205, `playground/open_duck_mini_v2/runner.py`, task `flat_terrain_backlash`, env joystick, imitation reward left on. That is the scene the sheet walk uses. The step count is the runner default, 150,000,000. The README at that pin also lists a 300,000,000 step command. The network and the 8,192 envs are the Berkeley joystick PPO config that the runner loads (cited, `brax_ppo_config("BerkeleyHumanoidJoystickFlatTerrain")`: 8,192 envs, unroll 20, network 512, 256, 128, and 150,000,000 steps on that name). The command rate limit stays 5.24 rad/s, the same clip the eval loop already uses.

`problems/train_sts12.py --write` rebuilds `problems/train_sts12.json`. `--apply` writes it into a checkout of that pin. The checkout is not stored here.

## Actuator (calc only)

Sheet, Feetech ST-3215-C018 page, read 2026-11-12: stall 30 kg.cm at 12 V (2.942 Nm), stall current 2.7 A, no-load 0.222 s/60 deg (4.717 rad/s), no-load current 180 mA. The trained no-load speed is 5.646 rad/s. The ratio is 0.835.

Damping and friction are scaled the same way `problems/sts12.py` scales them (sheet stall over 3.23, then 5.646 / 4.717). Realized no-load at 12 V is 4.697 rad/s, because the friction term is scaled with the damping. The 4.717 figure is the sheet target that ratio is built from. The training joint uses that same scale, so it matches the sheet-walk actuator.

## Bus (calc only)

The playground step has no supply voltage. The training torque is constant. The voltage is one DC point of the existing 3S bus (`twin/electromech/power_net.py`, three P45B cells, dropout 0.3 V). Superseded: that solve used a BEC set point of 16 V. The live set point is 12.0 V (D63). The numbers below are the 16 V solve and are kept. They were not recomputed. Do not retrain. The dropout is the unpublished assumption the twin already uses. Every servo draws the sheet no-load current, 0.180 A, at charge 0 mAh. That is not a walking current.

Lowest port on that solve is the head roll, 11.692 V. The knees are 11.735 V and 11.734 V. The MJCF class is one number, so every joint uses 11.692 V. Torque limit 2.8665 Nm. Backlash position gain 15.1846. Damping 0.6106. Friction 0.0741 Nm.

A walking current still sags. That sag is the em_twin sheet walk. Run C is now in problems/retrain_sts12/ (sim pass only). The 0.088 m/s old-policy result in problems/FIT3.md is superseded by that run and is kept.

## Mass

The trunk is the build trunk from `sim/mass_budget.py`, then the 70 g cell at the rear seat in `problems/sts12_mass.py`. Holder stays 0 g. Trunk 1.0654 kg to 1.1354 kg. Centre of mass from -56.48 mm to -62.40 mm in x. Those are the same figures as problems/FIT3.md. The other links are the same budget, with no extra mass.

## Smoke (sim pass only)

This machine has no GPU. The smoke is the same length as the earlier CPU smoke: 8 envs, 480 steps, unroll 5, 4 evals. JAX CPU. MuJoCo 3.17.0. Threads were left at the machine's 4 cores. Checkpoints were not stored.

The process finished. It is not a gait.

- Wall time 618.2 s. The first eval is at 198.5 s. From that eval to the last is 418.6 s.
- Rewards at steps 0, 160, 320, 480: 16.03, 16.99, 15.33, 13.17. All finite. They did not climb.
- 480 / 418.6 = 1.147 steps per second.

A 150,000,000 step run at 1.147 steps per second is 36,327 hours (calc only). The full config's 8,192 envs were not run. They do not fit this machine. BLOCKER for an 8,192-env CPU rate. 36,327 hours is the measured 8-env rate applied to the full step count.

## If a GPU is used later

Not started. Nothing was bought. No account was opened. Hours are the published 4090 note already used in COMPLETE_DUCK_AUDIT.md: 1.5 to 3 hours for a 150,000,000 to 300,000,000 step command (https://note.com/big_buddha0794/n/nccdcb712a715, cited there 2026-11-11). This config asks for 150,000,000 steps. The cost uses that whole hour range. Storage, tax, and a failed restart are outside the hourly rate.

| Option | Hourly price | 1.5 h | 3 h | Source |
|---|---|---|---|---|
| RunPod RTX 4090, Community Cloud | $0.34 | $0.51 | $1.02 | https://www.runpod.io/pricing , read 2026-11-12 |
| RunPod RTX 4090, Secure Cloud | $0.89 | $1.34 | $2.67 | same page |
| Vast.ai RTX 4090, marketplace low | $0.13 | $0.20 | $0.39 | https://computetick.com/provider/vast , checked 12 Nov 2026 23:17 UTC |

The dollar columns are calc only from the cited hourly price and the cited hour range. The Vast figure is a marketplace low and can be interrupted. The 4090 note is not a lab log.

## BLOCKER

- 480 steps are not a gait. Do not put the result on the duck.
- No new policy, so there is no new fall time, body speed, or knee voltage. The 60 s sheet walk of the old policy stays in problems/FIT3.md (sim pass only): no fall, about 0.088 m/s and 0.084 m/s.
- The playground pin does not step the bus. Training voltage is one DC point.
- A full run on this machine is not feasible. A GPU run was not started.
