# Duck ported to the shared lab gym, overlay gym/overlays/duck; checks against this repo's own sim (sim pass only)

- When: 2026-11-03 3:24 PM (America/New_York)
- Source: work by a Claude Code sub-agent for the duck lead (the lead commits). Nothing else in this repo was changed by this job. The port, its physics comparison and its course results are in the shared lab gym, overlay gym/overlays/duck.
- Written: 2026-11-03 by the Claude Code agent

## What was ported
- The duck at the trained mass (2.1071 kg) and at our build (2.6528 kg: the per-body inertials of sim/mass_budget.py build_budget() at commit 1e9888f, the same numbers sim/added_mass_sim.py writes into its model copy), with the stock BEST_WALK_ONNX_2 50 Hz loop, to the shared lab gym, overlay gym/overlays/duck.
- The MJCF, meshes and policy are fetched at run time from the pins in START_HERE.md (Open_Duck_Playground b9be205, Open_Duck_Mini 981750b) and checked by sha256; none of them is copied. sim/mass_budget.py was run read only, from the agent's scratch folder.

## Checks against this repo's own sim (Playground scene at b9be205, MuJoCo 3.17.0, public files only; sim pass only)
- A new, independent copy of the control loop (no upstream Python imported, no pickle loaded) gives this repo's numbers to the digit on the Playground scene: VERIFICATION.md C8 (our build: forward 0.70, turn 0.81, side 0.24, backlash 0.90, pushes 0.62; 0 falls in 36 flat runs) and sim/ADDED_MASS_SIM.md tables 1 and 2 for the trained mass (push case fall at 10.68 s; seeded falls at 20.0, 22.8, 14.3, 14.1, 22.7 and 20.0 s).
- On the same scene, a 1 ms time step alone (the policy still at 50 Hz) moves our build's side step from 0.24 to 0.48 of the command and makes our build fall in the 15 N push case (13.8 s, after the 4th push, a push to the right). Each of four other single solver or contact settings changes the push result the same way (falls at 13.7 to 13.9 s); only the start pose does not. So sim/ADDED_MASS_SIM.md finding 1 (the side step halves with our mass) and the 0 of 7 falls under pushes depend on the 2 ms, 1 solver iteration numerics the policy was trained with: they are marginal results, not margins. Proposed for the sim owner: a dated note in sim/ADDED_MASS_SIM.md and in VERIFICATION.md C8.
- Upstream training detail: common/randomize.py writes its floor friction randomization to geom 0 (line 22, lines 41 to 45), which in the compiled training scene is an unnamed visual mesh of trunk_assembly (contype 0); the floor is geom 46. The policy was trained at floor mu 0.6 only (scene_flat_terrain.xml line 36).
- The home keyframe starts the soles 12.4 to 16.9 mm inside the floor (MuJoCo contact depth at the key, both feet); sim/ADDED_MASS_SIM.md says 10.7 mm. A start lifted to 1 mm above the floor changes no flat-ground result (0.70, 0.81, 0.23, 0.90, 0.63 for our build).
- Control loop (public code): the Runtime (scripts/v2_rl_walk_mujoco.py at 376de65) builds the observation before the phase step (lines 253 to 270), as training does (joystick.py lines 325 to 343 and 437); the Playground MjInfer loop that this repo's sims copy steps the phase first (mujoco_infer.py lines 175 to 201), one 20 ms step ahead, and clips the motor targets to 5.24 rad/s, which the Runtime does not (lines 292 to 298 commented out).
- BLOCKER for an exact training match: the MuJoCo, MJX and mujoco_playground versions used to train BEST_WALK_ONNX_2 are not recorded upstream (pyproject.toml pins no MuJoCo version, playground>=0.0.3).

## Open
- Sim owner: the dated notes above (side step and pushes depend on the 2 ms, 1 iteration numerics; sole depth 12 to 17 mm at the home key).
- Everything else about this job: the shared lab gym, overlay gym/overlays/duck.
