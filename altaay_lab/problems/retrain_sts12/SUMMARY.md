# 12 V STS3215, 3S, walk to jog retrain (2026-11-12 ET)

Superseded 2026-11-14 as the current walk by run D (RUN_D.md). Run C is kept. The policy, the reward file, and the tables below stay.

All numbers are sim pass only unless marked calc only or cited. Nothing here is proven on hardware.

- Trainer: Open_Duck_Playground b9be205 runner, flat_terrain_backlash, joystick, 150,000,000 steps, 8,192 envs, PR 74 actuator, bus and mass patch (train_sts12.py --apply). Stack: jax 0.7.0, mujoco 3.3.4, brax 0.12.4 (pip resolved to 2025-08-06).
- GPU: one RTX 4090, about 105,000 to 138,000 steps per second, 150,000,000 steps in about 20 minutes plus 5 to 8 minutes of compile (sim pass only for the step rate and the wall time).
- Run 1 (Ahmed's first ask, range to 0.40, action_rate -1.0): finished, final eval reward about 201, but the policy stands still (0.0 m/s at every command). Fail.
- Run C (reward changes in REWARD_CHANGES.md): finished. Eval reward 13 -> 296 at 140M -> 226 at 151M (noisy). Policy walks.
- Policy: sts12_runC_policy.onnx (same 101 in, 14 out format as BEST_WALK_ONNX_2). ONNX matches the checkpoint to 5e-7.

## em_twin sheet walk, 60 s, 12 V sheet servo, 3S P45B, BEC 16 V, 70 g cell (problems/FIT3.md setup)

Superseded 2026-11-13: this section's BEC set point is 16 V. The live set point is 12.0 V. The 16 V table stays in eval_table.md. The 12.0 V table is eval_table_bec12.md.

See eval_table.md. Every figure in that table is sim pass only. Short form, sim pass only: no fall in 60 s at any command on either corner. At a 0.40 m/s command the body reaches 0.252 m/s typical (the table records 0.2516 m/s) and 0.240 m/s high-side (the table records 0.2399 m/s). A 0.10 m/s command stands still (dead zone, body speed about 0 on both corners). No flight phase at any speed, so this is not a run. At a 0.15 m/s command run C is 0.108 m/s typical and 0.104 m/s high-side (sim pass only). The old policy on this rig at that command is 0.088 m/s typical and 0.083 m/s high-side (sim pass only). FIT3 records 0.088 m/s and 0.084 m/s for that old policy (sim pass only). Run C supersedes the old policy as the walk filed on 2026-11-12. Superseded 2026-11-14: run D is the current walk (RUN_D.md). The old numbers stay in FIT3.

Watch items, sim pass only: pack peak 15.6 A at the 0.40 m/s command (the table records 15.57 A typical and 15.069 A high-side) and a 100 ms peak of 13.0 A typical (the table records 13.011 A). That peak sits inside the 13 A to 21 A trip band (calc only, 17 A plus or minus 4 A, cited in problems/FIT3.md). Knee minimum 9.31 V (sim pass only; high-side at 0.40 m/s, the table records 9.307 V and 9.323 V). Roll RMS is about 3.5 deg at 0.15 m/s (the table records 3.502 deg typical) against 2.9 deg for the old policy in the earlier sheet walk.
