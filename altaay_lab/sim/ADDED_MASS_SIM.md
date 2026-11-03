# Added-mass walk: the stock policy on the robot we will build (sim pass only)

Written 2026-11-01 9:58 PM ET by agent M (simulation). Script: sim/added_mass_sim.py (imports sim/current_budget.py and sim/mass_budget.py, both unchanged in use). Regenerate with
`ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_SCRATCH=<scratch folder> nice -n 10 python3 altaay_lab/sim/added_mass_sim.py all`
(about 15 minutes on one idle CPU, 40 on the shared box; results in ODM_SCRATCH/added_mass/results_*.json, the model copies in ODM_SCRATCH/added_mass/models/, traces for sim/runtime_thermal.py; figures sim/added_mass_*.png).

Mass note (2026-11-02, agent NL2): the results below are for the 2.77 kg build of that run. Since D22 and the netlist final pass the build is 2.65 kg (2651.9 g, +26 % over the trained 2107.1 g; sim/MASS_BUDGET.md); print/MASS_STUDY.md ran the same walking cases on it (variant c).

Gym note (2026-11-03, from the duck port to the shared lab gym, overlay gym/overlays/duck; history/2026-11-03_1524_duck_gym_overlay.md; applied by the twin integration agent; sim pass only): the side step and push results below hold only in the duck's training physics (2 ms Euler, Newton with 1 iteration, pyramidal cone, floor friction 0.6). For our 2.65 kg build (the VERIFICATION.md C8 model; this file's runs are the 2.77 kg build), on the same Playground scene, a 1 ms time step alone (the policy still at 50 Hz) moves the side step from 0.24 to 0.48 of the command, so the finding that the side step halves with our mass (Answer and finding 1) goes away, and it makes our build fall in the 15 N push case (13.8 s, after the 4th push, a push to the right); each of four other single solver or contact settings does the same (13.7 to 13.9 s), and the gym's frozen floor profile (1 ms, implicitfast, elliptic cone with impratio 5, floor friction 1.0) falls in 6 of 6 seeds. So "our build in 0 of 7" under pushes (Answer, finding 3) is a marginal result, not a margin; the real floor friction is HARDWARE_AUDIT B41. Also: the home keyframe starts the soles 12.4 to 16.9 mm inside the floor (MuJoCo contact depth at the key, both feet; checked again 2026-11-03 on the Playground scene at b9be205, MuJoCo 3.17.0), not the 10.7 mm this file says; a start lifted to 1 mm above the floor changes no flat-ground result.

## Answer
- **On flat ground the stock BEST_WALK_ONNX_2 still walks the robot we will build** (2.77 kg, +31 % over the trained 2.11 kg, sim/MASS_BUDGET.md): no fall in standing, walking forward, turning, sideways and the backlash-model walk, in the nominal run and in 6 seeded runs per case (sim pass only) [L].
- It walks **slower and leans further forward** [L]: speed tracking falls from 0.73 to 0.67 of the command walking forward (seed means), 0.82 to 0.79 turning, 0.95 to 0.88 in the backlash model, and **the side step halves (0.46 to 0.23)**. Mean torso pitch rises by 1 to 2 degrees (nose down); roll stays at 2 to 3.5 degrees RMS.
- **Pushes**: under the current_budget.py push case (15 N for 0.1 s every 3 s, alternating left and right) the trained mass falls in 7 of 7 runs and our build in 0 of 7: the same impulse changes a heavier robot's speed less. In a sweep of single 0.1 s pushes [L] (table 8): sideways our build takes 18 N with at most 1 fall in 8 where the trained mass falls in 4 of 8; **pushes toward the back are the weak direction for both**: the trained mass falls in 4 of 8 runs already at 9 N, our build in 4 of 8 at 12 N, and both fall nearly always from 15 N; pushes forward (from behind) give our build isolated falls from 12 N (1 or 2 in 8) where the trained mass has none up to 18 N.
  - Note 2026-11-03 (twin/structure/STRUCTURE_TWIN.md sections 1.1 and 7, applied by the structure twin integration agent; sim pass only): these push results use the upstream solver setting, 1 Newton iteration, the setting the policy was trained with (history/2026-11-03_1524_duck_gym_overlay.md). With converged contact forces (2 or more iterations; the twin's loads use 30), our 2.65 kg build (this file's runs are the 2.77 kg build) falls in 4 of 4 runs of the 15 N push case, at the 4th or 5th push (with 1 iteration in none), and single 0.1 s pushes while walking forward topple it in 1 to 4 of 8 gait phases from 15 N sideways and from 12 N forward or back. Walking forward, tracking moves from 0.70 to 0.73 of the command. With 1 iteration the forward walk also logs unconverged ground force spikes of 133 to 194 N, which vanish with 10, 30 or 100 iterations. The shared lab gym (overlay gym/overlays/duck) found the same push result with its own physics profile (history/2026-11-03_1524_duck_gym_overlay.md).
- **Rough terrain**: the current_budget.py rough-terrain case does not walk at all (stock and ours): at the upstream home pose the soles start up to 20.6 mm inside the 0 to 10 mm heightfield, the robot is thrown over at 0.28 s and lies on its back for the rest of the run (part of it sinks through the heightfield). With the start raised 23 mm: the trained mass falls in 4 of 7 runs and ours in 6 of 7, mostly within 3 to 13 s [L]. The stock policy is weak on this terrain and our mass makes it worse. First walks: flat floor.
- **Current** [L]: servo bus mean while walking -2 to +7 % (2.22 to 2.37 A forward, 3.24 to 3.42 A backlash model, sideways 2.25 to 2.20 A), worst 100 ms +1 to +8 %, standing +79 % (0.19 to 0.34 A). Knee RMS current +2 to +7 % walking. No servo stays above 2 A or above 80 % output for 2 s, so the C001 self-protection would not trip (table 5). sim/CURRENT_BUDGET.md, sim/POWER_PATH_SIM.md and the parts sized from them keep their margins.
- **Margins on our build** [L] (tables 6 and 7):
  - Trunk mass +10 % to +60 % (up to 0.59 kg more, 3.36 kg in all): no fall on flat ground; forward speed falls steadily from 0.101 to 0.064 m/s and the turn rate from 0.79 to 0.65 rad/s at +60 %. Mass is not the limit.
  - Trunk centre of mass forward up to +30 mm (whole robot +10.7 mm): no fall; the torso leans 8.7 degrees forward walking (10.3 in the backlash model) and the bus current rises 23 %.
  - **Trunk centre of mass backward: the narrow side.** With our trunk centre of mass moved 10 or 12.5 mm back (whole robot 3.6 or 4.4 mm) none of 16 runs falls. From 15 mm back (whole robot 5.3 mm) the robot tips over backwards within the first 1.3 s while still standing: 1 of 4 runs at 15 mm, 2 of 4 at 17.5 mm, 3 of 4 at 20 and 30 mm. The upstream start drop (soles 10.7 mm inside the floor) helps tip it: with the start raised 12 mm, 15 and 17.5 mm back never fall (16 runs) and 20 mm back falls in 2 of 4. So the whole-robot centre of mass can sit only about 4 mm (hard start) to 6 mm (gentle start) further back than our estimate, 7 to 9 mm behind the trained model, before the stock policy falls backwards; forward there is more than 10 mm [L] (table 7).
- Bottom line for the build: **no print-blocking and no build-blocking finding from the walk**; walk on flat floors first, expect about 0.1 m/s and a weak side step, and check the real centre of mass before the first walk (finding 2).

## What ran
- Model copies: every body inertial of the Playground MJCF (open_duck_mini_v2.xml and open_duck_mini_v2_backlash.xml at b9be205) replaced by the sum of its parts in sim/mass_budget.py, which holds the lab-only parts at their audit/placements.json seats; those seats are also drawn as visual boxes with no mass or collision of their own (sim/added_mass_lab_parts.png). "stock" writes the trained inertials back unchanged and reproduces sim/CURRENT_BUDGET.md to the last digit (bus means 0.19, 2.22, 2.38, 2.25, 3.24, 2.65, 1.89 A; fall at 10.68 s with pushes) [L].
- Control loop: upstream MjInfer unmodified, BEST_WALK_ONNX_2, 50 Hz, motor speed limit 5.24 rad/s, accelerometer bias removed (sim/SIM_WALK.md note), MuJoCo 3.17.0 [L]; the run function is current_budget.run with extra logging (base pose 50 Hz).
- Cases: the 7 cases of current_budget.py (first 2 s standing, then the command) plus the rough-terrain walk with the start raised 23 mm. Seeds 1 to 6: joint start angles plus U(-0.03, 0.03) rad (the qpos0 jitter range of training, randomize.py lines 78 to 86) and, on rough terrain, a random start within 2 m.
- Margin sweep: trunk mass and inertia x1.1 to x1.6; trunk centre of mass moved -30 to +30 mm in x. Push sweep: one push of 0.1 s on the trunk at t = 6 s plus 8 phase offsets over the 0.54 s gait period [U] (Playground data/polynomial_coefficients.pkl, period 0.54 s for all 240 commands), forces 6 to 24 N, 4 directions, walking forward at 0.15 m/s; a run counts as a fall if the robot falls before the run ends at 10 s.
- Tracking = measured speed in the robot's heading frame over t = 4 s to the end, divided by the command. Torso pitch and roll from the base orientation (pitch positive = nose down). Fall = trunk under 0.10 m or tilted more than 60 degrees.

## Table 1: nominal runs

| Case | Model | Falls (s) | Tracking (measured / command) | vx m/s | vy m/s | yaw rate rad/s | Torso pitch mean +- rms (deg) | Roll rms (deg) | Max abs pitch, roll (deg) |
|---|---|---|---|---|---|---|---|---|---|
| Stand, zero command | stock | none |  | -0.000 | +0.000 | -0.00 | -1.9 +- 0.1 | 0.0 | 2, 5 |
| Stand, zero command | ours | none |  | -0.000 | +0.000 | -0.00 | -1.2 +- 0.1 | 0.0 | 1, 5 |
| Walk forward 0.15 m/s | stock | none | 0.73 | +0.110 | +0.006 | +0.00 | +1.6 +- 0.6 | 2.7 | 3, 5 |
| Walk forward 0.15 m/s | ours | none | 0.67 | +0.101 | +0.001 | +0.00 | +2.8 +- 0.6 | 2.5 | 4, 4 |
| Turn 1.0 rad/s | stock | none | 0.82 | +0.011 | +0.059 | +0.82 | +1.1 +- 0.5 | 2.3 | 2, 3 |
| Turn 1.0 rad/s | ours | none | 0.79 | +0.014 | +0.053 | +0.79 | +2.2 +- 0.5 | 2.2 | 3, 3 |
| Walk sideways 0.2 m/s | stock | none | 0.47 | +0.008 | +0.094 | +0.00 | +0.8 +- 0.5 | 1.8 | 2, 4 |
| Walk sideways 0.2 m/s | ours | none | 0.23 | +0.009 | +0.045 | -0.00 | +1.0 +- 0.8 | 2.1 | 3, 4 |
| Walk forward, backlash model | stock | none | 0.95 | +0.141 | +0.015 | -0.01 | +2.1 +- 0.7 | 3.5 | 4, 6 |
| Walk forward, backlash model | ours | none | 0.88 | +0.132 | +0.007 | +0.00 | +4.1 +- 0.7 | 3.2 | 6, 6 |
| Walk forward, 15 N pushes every 3 s | stock | fell at 10.68 | - | - | - | - | - | - | - |
| Walk forward, 15 N pushes every 3 s | ours | none | 0.62 | +0.092 | +0.001 | +0.01 | +3.1 +- 0.9 | 3.2 | 8, 12 |
| Rough terrain, backlash, upstream start | stock | fell at 0.28 | - | - | - | - | - | - | - |
| Rough terrain, backlash, upstream start | ours | fell at 0.3 | - | - | - | - | - | - | - |
| Rough terrain, backlash, start raised 23 mm | stock | fell at 9.14 | - | - | - | - | - | - | - |
| Rough terrain, backlash, start raised 23 mm | ours | fell at 4.3 | - | - | - | - | - | - | - |

## Table 2: seeded runs (6 per case)

| Case | Model | Runs that fell | First fall (s) | Tracking mean (min to max), runs that did not fall |
|---|---|---|---|---|
| Walk forward 0.15 m/s | stock | 0 of 6 | - | 0.73 (0.73 to 0.74) |
| Walk forward 0.15 m/s | ours | 0 of 6 | - | 0.67 (0.67 to 0.67) |
| Turn 1.0 rad/s | stock | 0 of 6 | - | 0.82 (0.82 to 0.82) |
| Turn 1.0 rad/s | ours | 0 of 6 | - | 0.79 (0.78 to 0.80) |
| Walk sideways 0.2 m/s | stock | 0 of 6 | - | 0.46 (0.42 to 0.47) |
| Walk sideways 0.2 m/s | ours | 0 of 6 | - | 0.23 (0.22 to 0.25) |
| Walk forward, backlash model | stock | 0 of 6 | - | 0.95 (0.95 to 0.95) |
| Walk forward, backlash model | ours | 0 of 6 | - | 0.88 (0.88 to 0.88) |
| Walk forward, 15 N pushes every 3 s | stock | 6 of 6 | 20.0, 22.8, 14.3, 14.1, 22.7, 20.0 |  |
| Walk forward, 15 N pushes every 3 s | ours | 0 of 6 | - | 0.60 (0.59 to 0.62) |
| Rough terrain, backlash, start raised 23 mm | stock | 3 of 6 | 8.0, 5.7, 6.4 | 0.85 (0.84 to 0.86) |
| Rough terrain, backlash, start raised 23 mm | ours | 5 of 6 | 3.3, 6.2, 13.0, 6.7, 6.6 | 0.80 (0.80 to 0.80) |

## Table 3: current budget, servo bus at 7.4 V (A), BAM kt 1.148 (as sim/CURRENT_BUDGET.md)

| Case | Model | Mean | Max 1 s | Max 100 ms | Max 20 ms | Max 2 ms | Whole run max | Note |
|---|---|---|---|---|---|---|---|---|
| Stand, zero command | stock | 0.19 | 0.22 | 0.23 | 0.24 | 0.24 | 3.15 |  |
| Stand, zero command | ours | 0.34 | 0.37 | 0.40 | 0.40 | 0.40 | 3.15 |  |
| Walk forward 0.15 m/s | stock | 2.22 | 2.31 | 3.08 | 4.02 | 4.97 | 4.97 |  |
| Walk forward 0.15 m/s | ours | 2.37 | 2.48 | 3.33 | 4.24 | 5.26 | 5.26 |  |
| Turn 1.0 rad/s | stock | 2.38 | 2.52 | 3.21 | 5.39 | 6.40 | 6.40 |  |
| Turn 1.0 rad/s | ours | 2.55 | 2.71 | 3.45 | 5.68 | 6.63 | 6.63 |  |
| Walk sideways 0.2 m/s | stock | 2.25 | 2.46 | 3.81 | 5.92 | 7.19 | 7.19 |  |
| Walk sideways 0.2 m/s | ours | 2.20 | 2.43 | 3.83 | 6.64 | 7.54 | 7.54 |  |
| Walk forward, backlash model | stock | 3.24 | 3.44 | 4.72 | 6.77 | 8.30 | 8.30 |  |
| Walk forward, backlash model | ours | 3.42 | 3.62 | 4.97 | 6.92 | 8.31 | 8.31 |  |
| Walk forward, 15 N pushes every 3 s | stock | 1.89 | 2.36 | 3.59 | 5.26 | 6.27 | 6.27 | fell at 10.68 s: includes the robot lying on the floor |
| Walk forward, 15 N pushes every 3 s | ours | 2.35 | 2.48 | 3.37 | 5.65 | 6.53 | 6.53 |  |
| Rough terrain, backlash, upstream start | stock | 2.65 | 2.96 | 3.92 | 6.15 | 7.80 | 13.61 | fell at 0.28 s: includes the robot lying on the floor |
| Rough terrain, backlash, upstream start | ours | 2.68 | 2.96 | 4.64 | 7.71 | 8.84 | 15.82 | fell at 0.3 s: includes the robot lying on the floor |
| Rough terrain, backlash, start raised 23 mm | stock | 2.66 | 3.34 | 5.62 | 6.41 | 8.03 | 8.03 | fell at 9.14 s: includes the robot lying on the floor |
| Rough terrain, backlash, start raised 23 mm | ours | 2.75 | 4.42 | 8.57 | 15.27 | 17.86 | 17.86 | fell at 4.3 s: includes the robot lying on the floor |

## Table 4: joint torque, RMS / peak (Nm) / time at the 3.23 Nm limit

| Joint | forward stock | forward ours | backlash stock | backlash ours |
|---|---|---|---|---|
| left_hip_yaw | 0.34 / 0.81 / 0 % | 0.33 / 0.77 / 0 % | 0.35 / 0.88 / 0 % | 0.38 / 1.17 / 0 % |
| left_hip_roll | 0.51 / 0.95 / 0 % | 0.51 / 1.26 / 0 % | 0.79 / 1.63 / 0 % | 0.80 / 2.02 / 0 % |
| left_hip_pitch | 1.06 / 2.36 / 0 % | 1.06 / 2.36 / 0 % | 1.28 / 3.23 / 0 % | 1.29 / 3.23 / 0 % |
| left_knee | 1.63 / 3.17 / 0 % | 1.67 / 3.11 / 0 % | 2.06 / 3.23 / 14 % | 2.07 / 3.23 / 18 % |
| left_ankle | 1.06 / 2.96 / 0 % | 1.11 / 3.17 / 0 % | 1.10 / 3.23 / 0 % | 1.18 / 3.23 / 1 % |
| right_hip_yaw | 0.28 / 0.60 / 0 % | 0.28 / 0.64 / 0 % | 0.47 / 1.23 / 0 % | 0.47 / 0.97 / 0 % |
| right_hip_roll | 0.53 / 1.31 / 0 % | 0.56 / 1.43 / 0 % | 0.64 / 1.74 / 0 % | 0.67 / 1.90 / 0 % |
| right_hip_pitch | 0.96 / 2.34 / 0 % | 0.95 / 2.36 / 0 % | 1.08 / 2.76 / 0 % | 1.10 / 2.81 / 0 % |
| right_knee | 1.78 / 3.23 / 3 % | 1.79 / 3.23 / 1 % | 2.18 / 3.23 / 22 % | 2.19 / 3.23 / 23 % |
| right_ankle | 1.01 / 2.35 / 0 % | 1.08 / 2.53 / 0 % | 1.11 / 2.85 / 0 % | 1.20 / 3.03 / 0 % |
| neck_pitch | 0.26 / 0.41 / 0 % | 0.28 / 0.51 / 0 % | 0.37 / 0.75 / 0 % | 0.40 / 0.73 / 0 % |
| head_pitch | 0.89 / 1.60 / 0 % | 0.87 / 1.54 / 0 % | 1.07 / 2.13 / 0 % | 1.03 / 2.19 / 0 % |
| head_yaw | 0.88 / 2.03 / 0 % | 0.90 / 2.10 / 0 % | 1.02 / 3.15 / 0 % | 1.05 / 3.21 / 0 % |
| head_roll | 0.73 / 1.46 / 0 % | 0.71 / 1.39 / 0 % | 0.83 / 1.78 / 0 % | 0.81 / 1.75 / 0 % |

## Table 5: servo self-protection checks
Feetech C001 spec item 7-11 [I] (https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf): torque off after more than 2 A for 2 s, or more than 80 % of stall for 2 s, or above 70 C. Per cell: longest continuous time above 2 A / longest continuous time above 80 % output / highest 2 s mean of |I|.

| Case | Model | Knee L | Knee R | Worst other joint |
|---|---|---|---|---|
| Walk forward 0.15 m/s | stock | 0.01 s / 0.03 s / 0.88 A | 0.01 s / 0.04 s / 1.03 A | left_hip_pitch: 0.00 s / 0.00 s / 0.59 A |
| Walk forward 0.15 m/s | ours | 0.03 s / 0.05 s / 0.91 A | 0.01 s / 0.04 s / 1.05 A | right_ankle: 0.00 s / 0.00 s / 0.63 A |
| Turn 1.0 rad/s | stock | 0.01 s / 0.04 s / 0.88 A | 0.02 s / 0.04 s / 1.12 A | left_ankle: 0.01 s / 0.05 s / 0.74 A |
| Turn 1.0 rad/s | ours | 0.03 s / 0.06 s / 0.93 A | 0.02 s / 0.07 s / 1.20 A | left_ankle: 0.01 s / 0.05 s / 0.77 A |
| Walk sideways 0.2 m/s | stock | 0.02 s / 0.04 s / 0.75 A | 0.05 s / 0.05 s / 1.03 A | left_hip_roll: 0.00 s / 0.04 s / 0.72 A |
| Walk sideways 0.2 m/s | ours | 0.04 s / 0.06 s / 0.77 A | 0.06 s / 0.05 s / 0.96 A | left_hip_roll: 0.01 s / 0.01 s / 0.71 A |
| Walk forward, backlash model | stock | 0.05 s / 0.07 s / 1.25 A | 0.04 s / 0.07 s / 1.34 A | left_hip_pitch: 0.01 s / 0.03 s / 0.69 A |
| Walk forward, backlash model | ours | 0.07 s / 0.08 s / 1.25 A | 0.08 s / 0.10 s / 1.33 A | left_hip_pitch: 0.01 s / 0.03 s / 0.71 A |
| Walk forward, 15 N pushes every 3 s | stock | 0.05 s / 0.06 s / 0.96 A | 0.04 s / 0.08 s / 1.08 A | right_hip_pitch: 0.01 s / 0.01 s / 0.61 A |
| Walk forward, 15 N pushes every 3 s | ours | 0.04 s / 0.07 s / 0.99 A | 0.03 s / 0.06 s / 1.11 A | right_ankle: 0.00 s / 0.00 s / 0.64 A |

## Table 6: margin sweep on our build (cell: falls, tracking, mean pitch deg, bus mean A)

| Variant | Walk forward 0.15 m/s | Turn 1.0 rad/s | Walk sideways 0.2 m/s | Walk forward, backlash model | Walk forward, 15 N pushes every 3 s | Rough terrain, backlash, start raised 23 mm |
|---|---|---|---|---|---|---|
| ours (no change) | ok, 0.67, +2.8, 2.37 | ok, 0.79, +2.2, 2.55 | ok, 0.23, +1.0, 2.20 | ok, 0.88, +4.1, 3.42 | ok, 0.62, +3.1, 2.35 | fell at 4.3 s |
| ours, trunk+10% | ok, 0.63, +2.7, 2.37 | ok, 0.77, +2.2, 2.56 | ok, 0.21, +1.1, 2.21 | ok, 0.88, +4.1, 3.44 | ok, 0.62, +2.8, 2.35 | fell at 4.36 s |
| ours, trunk+20% | ok, 0.58, +2.6, 2.39 | ok, 0.74, +2.1, 2.56 | ok, 0.20, +1.0, 2.21 | ok, 0.87, +4.0, 3.46 | ok, 0.60, +2.8, 2.38 | fell at 4.18 s |
| ours, trunk+30% | ok, 0.53, +2.5, 2.40 | ok, 0.72, +2.0, 2.57 | ok, 0.18, +1.0, 2.23 | ok, 0.86, +4.1, 3.48 | ok, 0.57, +2.7, 2.40 | fell at 4.16 s |
| ours, trunk+40% | ok, 0.46, +2.3, 2.40 | ok, 0.68, +1.8, 2.57 | ok, 0.17, +1.0, 2.23 | ok, 0.85, +4.1, 3.50 | ok, 0.54, +2.6, 2.41 | fell at 4.16 s |
| ours, trunk+50% | ok, 0.44, +2.2, 2.44 | ok, 0.68, +1.8, 2.60 | ok, 0.17, +1.0, 2.25 | ok, 0.85, +3.9, 3.51 | ok, 0.50, +2.5, 2.44 | fell at 4.3 s |
| ours, trunk+60% | ok, 0.43, +2.1, 2.49 | ok, 0.65, +1.6, 2.61 | ok, 0.16, +0.9, 2.28 | ok, 0.82, +4.1, 3.52 | ok, 0.48, +2.4, 2.48 | fell at 4.4 s |
| ours, trunkCoM-30mm | fell at 0.78 s (start) | fell at 0.78 s (start) | fell at 0.78 s (start) | ok, 0.49, -1.7, 3.04 | fell at 0.78 s (start) | fell at 3.74 s |
| ours, trunkCoM-20mm | fell at 0.9 s (start) | fell at 0.9 s (start) | fell at 0.9 s (start) | ok, 0.72, -2.0, 3.16 | fell at 0.9 s (start) | fell at 3.72 s |
| ours, trunkCoM-17.5mm | fell at 0.96 s (start) | fell at 0.96 s (start) | fell at 0.96 s (start) | ok, 0.81, -2.2, 3.19 | fell at 0.96 s (start) | fell at 3.86 s |
| ours, trunkCoM-15mm | fell at 1.04 s | fell at 1.04 s | fell at 1.04 s | ok, 0.89, -2.1, 3.23 | fell at 1.04 s | fell at 3.82 s |
| ours, trunkCoM-12.5mm | ok, 0.57, +0.5, 2.25 | ok, 0.77, +0.6, 2.43 | ok, 0.20, -0.1, 2.10 | ok, 0.97, -1.4, 3.26 | ok, 0.58, +0.6, 2.23 | fell at 3.86 s |
| ours, trunkCoM-10mm | ok, 0.58, +0.9, 2.27 | ok, 0.77, +0.9, 2.46 | ok, 0.20, +0.1, 2.10 | ok, 0.99, -0.3, 3.27 | ok, 0.59, +0.9, 2.25 | fell at 3.88 s |
| ours, trunkCoM-5mm | ok, 0.63, +1.7, 2.29 | ok, 0.78, +1.5, 2.51 | ok, 0.21, +0.6, 2.16 | ok, 0.92, +2.5, 3.36 | ok, 0.61, +1.9, 2.28 | fell at 4.06 s |
| ours, trunkCoM+5mm | ok, 0.67, +3.8, 2.43 | ok, 0.78, +2.8, 2.59 | ok, 0.24, +1.5, 2.24 | ok, 0.84, +5.2, 3.48 | ok, 0.59, +4.0, 2.40 | fell at 17.56 s |
| ours, trunkCoM+10mm | ok, 0.62, +4.3, 2.48 | ok, 0.78, +3.5, 2.61 | ok, 0.29, +2.1, 2.34 | ok, 0.83, +5.9, 3.56 | fell at 26.12 s | fell at 1.96 s |
| ours, trunkCoM+20mm | ok, 0.64, +6.8, 2.67 | ok, 0.76, +4.8, 2.71 | ok, 0.34, +3.5, 2.53 | ok, 0.87, +8.0, 3.82 | ok, 0.69, +6.3, 2.72 | fell at 1.5 s |
| ours, trunkCoM+30mm | ok, 0.61, +8.7, 2.92 | ok, 0.73, +6.2, 2.83 | ok, 0.36, +5.9, 2.75 | ok, 0.91, +10.3, 4.15 | ok, 0.74, +8.4, 3.11 | fell at 5.82 s |

## Table 7: backward centre of mass, standing and walking, upstream start and a start raised 12 mm
First fall time in s for the nominal run and seeds 1 to 3 ("none" = no fall). The soles start 10.7 mm inside the floor at the upstream home pose, so the first 0.1 s is a drop.

| Trunk CoM shift from our build | Whole robot CoM shift | stand, upstream start | walk_forward, upstream start | stand, start raised 12 mm | walk_forward, start raised 12 mm |
|---|---|---|---|---|---|
| -10 mm | -3.6 mm | none, none, none, none | none, none, none, none | none, none, none, none | none, none, none, none |
| -12.5 mm | -4.4 mm | none, none, none, none | none, none, none, none | none, none, none, none | none, none, none, none |
| -15 mm | -5.3 mm | 1.04, none, none, none | 1.04, none, none, none | none, none, none, none | none, none, none, none |
| -17.5 mm | -6.2 mm | 0.96, 1.20, none, none | 0.96, 1.20, none, none | none, none, none, none | none, none, none, none |
| -20 mm | -7.1 mm | 0.90, 0.98, none, 1.28 | 0.90, 0.98, none, 1.28 | 1.72, none, none, 1.18 | 1.72, none, none, 1.18 |
| -30 mm | -10.7 mm | 0.78, 0.80, none, 0.92 | 0.78, 0.80, none, 0.92 | 0.86, 0.88, none, 0.84 | 0.86, 0.88, none, 0.84 |

## Table 8: push sweep (falls out of 8 gait phases)

| Push | Model | 6 N | 9 N | 12 N | 15 N | 18 N | 21 N | 24 N |
|---|---|---|---|---|---|---|---|---|
| left | stock | 0/8 | 0/8 | 0/8 | 2/8 | 4/8 | 5/8 | 6/8 |
| left | ours | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 4/8 | 3/8 |
| right | stock | 0/8 | 0/8 | 0/8 | 2/8 | 4/8 | 5/8 | 6/8 |
| right | ours | 0/8 | 0/8 | 0/8 | 0/8 | 1/8 | 4/8 | 4/8 |
| forward | stock | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 5/8 | 7/8 |
| forward | ours | 0/8 | 0/8 | 1/8 | 2/8 | 1/8 | 2/8 | 5/8 |
| back | stock | 0/8 | 4/8 | 6/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| back | ours | 0/8 | 0/8 | 4/8 | 7/8 | 8/8 | 8/8 | 8/8 |

## Findings for the build
1. Note: the stock policy walks our build on flat ground in simulation, slower (0.10 m/s forward for a 0.15 m/s command) and with half the side-step speed. Plan the first walks on a flat floor and do not judge the build by side stepping.
2. Build check (not blocking): the backward centre-of-mass margin is small: about 4 to 6 mm of whole-robot centre of mass behind our estimate (table 7), against an estimate uncertainty of about 1 to 2 mm from the UNVERIFIED parts (the holder alone is uncertain by 25 g at x = -133 mm, about 1 mm) and an unknown amount from where each servo's motor really sits. Weigh the robot and find its centre of mass before the first walk (proposed TEST_PLAN.md step below). If it is more than 4 mm behind the estimate, move rear parts forward (the BEC Pro and the USB slack coil are the heaviest movable ones) before walking, and start every walk from a gentle stand, not a drop.
3. Note: the 15 N push case of CURRENT_BUDGET.md falls with the trained mass (7 of 7 runs) and never with ours; a 0.1 s push toward the back topples the trained mass from 9 N and our build from 12 N. Keep a hand or a tether behind the robot during the first walks.
4. Note: rough terrain (0 to 10 mm heightfield) topples the stock policy in 4 of 7 runs even at the trained mass and 6 of 7 with ours. Not a build blocker; it limits where the first walks happen.
5. Note: our mass changes walking power by only 7 % and walk time by 6 % (sim/RUNTIME_THERMAL.md); the power parts keep their margins.

## Proposed text for files owned by others
- sim/CURRENT_BUDGET.md, rough-terrain row: replace "| at 0.28 s (start drop only) |" with "| at 0.28 s, then lies on its back for the rest of the run: not a walk (sim/ADDED_MASS_SIM.md) |" and add under the table: "Note 2026-11-01 (sim/ADDED_MASS_SIM.md): in the rough-terrain case the upstream home pose starts the soles up to 20.6 mm inside the heightfield; the robot is thrown over at 0.28 s and never walks, so that row is a fallen robot's current, not a walking current. With the start raised 23 mm the robot walks until it falls (4 of 7 runs within 30 s at the trained mass): bus mean 2.7 A, worst 100 ms 5.6 A (trained mass)."
- sim/SIM_WALK.md, add a note: "Note 2026-11-01 (sim/ADDED_MASS_SIM.md): the upstream home keyframe (base z 0.15 m) starts both soles 10.7 mm inside the floor, so every run begins with a pop of the trunk to 0.167 m in the first 0.1 s. It does not cause falls on flat ground with the trained mass, but on the rough heightfield it throws the robot over at 0.28 s."
- TEST_PLAN.md section 8, add a step before step 1: "0. Weigh the assembled robot and find its centre of mass at the home pose: robot powered and holding the pose, both toes on one kitchen scale and both heels on a second one (centre of mass x from the load split and the contact spacing), or the trunk balanced on an edge. Expected from sim/MASS_BUDGET.md: 2.77 +/- 0.05 kg, centre of mass 0 to 1 mm ahead of the ankle servo axes (3 mm in the trained model). If it is more than 4 mm behind the ankle axes, move rear parts forward before walking (sim/ADDED_MASS_SIM.md table 7)."
- START_HERE.md, after "about 2.11 kg (sim mass)", and README.md, after "2.1 kg (sim mass)": add " (the lab build is about 2.77 kg by the mass budget, sim/MASS_BUDGET.md, not weighed)".

## Limits
- Sim pass only, with the BAM servo model (no gear friction beyond the model, issue 48). The real servos may track worse than the sim, which would cut the speed margins found here.
- The mass and centre of mass of our build are estimates (sim/MASS_BUDGET.md: 193 g UNVERIFIED, about 40 g uncertainty on the total) until the robot is weighed.
- Per-part mass distribution is uniform over each CAD mesh, the same assumption as the trained model; a servo's motor sits off its geometric centre.
- Seeds vary only the start; terrain friction, servo gains and sensor noise are as upstream.
