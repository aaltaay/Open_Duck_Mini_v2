# Structure twin: do the printed parts, inserts and screws hold walking, pushes and falls? (sim pass only, FEA pass only)

Later pass, 2026-11-12: twin/structure/TOPOLOGY.md. It keeps this file's 2026-11-03 numbers as they are, and adds a voxel-mesh re-run on the current parts plus proposed STLs under twin/structure/topology/. Those STLs are not installed in print/.

Written 2026-11-03 by the structure twin sub-agent (Claude Code) for the lead agent, branch claude/digital-twin, folder twin/structure/ only. Nothing was printed, bought, sent, deleted or committed. Loads are **sim pass only** (MuJoCo 3.17.0, stock BEST_WALK_ONNX_2 on our 2652.8 g build with the D22 print profile). Stresses are **FEA pass only** (linear tetrahedra, as-printed zones, room-temperature PLA unless the hot case says otherwise). Times are US Eastern.

Tags: [L] lab file or script on this box; [U] upstream file; [I] internet source. Several hosts could not be opened from this session (eprints.whiterose.ac.uk, www.cnckitchen.com, www.mdpi.com, www.sculpteo.com, wiki.overture3d.com, overture3d.com): those [I] values are **search result text**, marked "(search text)". They need those hosts allowed to be read in full.

## Answer in plain words

- **Walking, the stock policy, flat floor, room temperature: two printed parts are under the lab margin of 2** (FEA pass only, on sim pass only loads; the mesh check is in section 2.4):
  - **roll_to_pitch** (both legs, D22 light profile, 2 walls 15 %): SF **1.48 to 1.63** walking and **1.08 to 1.21** in push recovery over mesh levels 1 to 3 (1.60 / 1.11, 1.48 / 1.08, 1.63 / 1.21). The maker's interlayer value (39.4 against 22 MPa) raises only level 1 (1.83 / 1.25): at levels 2 and 3 the weak spot is in-plane. Weak spot: the side wall that joins the two hip roll horn ears, loaded by the idle-horn force (90 N walking, 130 N push); at level 1 the shear across its layers in the middle of the wall (y -0.3 mm in the link frame); at levels 2 and 3 the in-plane stress in the skin at the ends of the wall (y -14 to -15 mm; in push at level 3 the other end, y +13 mm).
  - **knee_to_ankle_left_sheet of the shin** (the plate on the knee drive horn, both legs, 3 walls 15 %): SF **1.63** walking, **1.07** push at mesh level 2 (1.56 / 1.04 at level 1), in-plane. Weak spot: the eye round the knee horn, in the 2.5 to 3 mm of plastic between a horn screw hole and the eye edge (level 2) and where the eye joins the plate (level 1). The knee torque drives it: walking peak 4.4 N m, push 6.9 to 8.6 N m.
  - The same sheet on the thigh (the hip pitch horn eye) holds 2.70 walking but 1.74 in push. Over 2 in both (level 1): foot_top 5.5 / 4.4, the neck sheets 5.4 / 3.6, the hip roll stage 12.9 / 9.6, head_roll_mount 48 / 27.
  - Our 2652.8 g build raises the walking peaks by 19 % (median; 0 to 60 %) over the trained mass, the sole force from 68.6 to 77.7 N.
- **Falls** (section 1.3; the contact stiffness is not known, so it is a range): when a printed wall is hit in its middle ("soft", 0.14 to 0.34 MN/m) the hit part sees 400 to 900 N and the head 15 to 71 g; on an edge on a hard floor ("mid", 1.35 to 3.2 MN/m) 1300 to 2800 N and 54 to 196 g. At "soft", under the 1.2 fall margin: roll_to_pitch in 7 of the 10 falls, the neck sheets in 9, head_roll_mount in 5, the thigh sheet in 4, the shin sheet in 2 (a side fall and a rough terrain fall); at "mid" nearly every printed load path is under 1.2. A flat-plate hand calc puts a wall hit at 31 to 115 MPa in the body shell and 25 to 90 MPa in the head (strength 47.1 MPa). Inserts hold at the soft level (lowest 2.0: the two trunk_top to trunk_bottom screws, an upper bound); at mid that bound drops to 0.6 and head_roll_mount to 1.95 in pull-out and 1.3 sideways.
- **Fasteners (the PLA side):** walking keeps every horn and case screw over 2 except the **ankle servo case screws** (SF 1.6: the 2 mm screw bearing on the 2.0 mm sheet). Push recovery drops the knee drive horn screws (1.2 to 1.6) and the knee and ankle case screws (1.1 to 1.9) under 2. Inserts: walking SF 12 or more, pull-out SF over 80. Self-tapping screws in printed pilots: SF 8 or more in falls (computed; no test data, BLOCKER).
- **Fatigue** (6667 gait cycles per hour per leg, 666,700 in 100 hours): the cited design curve (P_s 95 %) allows a cycle maximum of only 5.8 MPa in-plane and 2.7 MPa across the layers for 100 hours. roll_to_pitch (0.04 to 0.7 h), the knee sheet eye (0.02 to 0.5 h), the thigh sheet (2 to 11 h), foot_top (50 h in the side step) and the neck sheets (28 h in the turn) do not last 100 hours on it. On the best-case print data (35.8 MPa endurance threshold) every weak spot lasts, the knee sheet and roll_to_pitch with a ratio of only 1.2. The real life is between: **BLOCKER**, bench fatigue test P7.
- **Hot case (thermal twin):** the knee sheets run at 54 to 66 C and roll_to_pitch up to 61 C. At 50 C printed PLA keeps about 0.62 of its strength (cited), so the walking SF become about **1.0** for both and push about 0.7 (walking / push: knee sheet 1.02 / 0.67, roll_to_pitch 0.93 to 1.02 / 0.68 to 0.76); at 60 C the strength is a BLOCKER and the modulus is about a quarter. Standing, both hold 3.4 to 4.3 MPa, 2 to 10 x the heat deflection test stress: **creep is expected above about 50 C** (rate: BLOCKER). PETG (HDT 69 C) keeps its lower strength to about 60 C (ASSUMPTION): 1.18 (knee sheet) and 1.07 to 1.32 (roll_to_pitch) walking, so it stops the loss with heat but does not reach 2.
- **What the print settings can do (FEA, mesh level 1, against 1.60 / 1.11 and 1.56 / 1.04 there; none decided):** printing roll_to_pitch in another orientation makes it worse (1.00 / 0.78 with the hip roll axis vertical, 1.10 / 0.79 with the ear wall flat), so the current -z up stays. Its profile before D22, 3 walls, gives 1.84 / 1.25 for +7.2 g and +0.44 h (both legs); 4 or 6 walls with 40 % infill add little (1.87 / 1.28, 1.90 / 1.29) for +18.9 to +27.7 g. Knee sheets with 5 walls 40 %: 1.82 / 1.20 for +9.4 g and +1.1 h (all 8). No print setting tested reaches 2; a CAD change of the knee sheet eye could (P2: a hand scaling, not modelled).
- **Sim finding for the sim owner:** with converged contact forces (2 or more solver iterations instead of the upstream 1), our build falls in every 15 N push run (4 of 4) and in 1 to 4 of 8 single pushes from 15 N sideways and 12 N fore and aft; with the upstream setting it falls in none (sim/ADDED_MASS_SIM.md). The shared lab gym found the same with its own physics profile (history/2026-11-03_1524_duck_gym_overlay.md). The walk itself changes little (tracking 0.70 to 0.73).
- **Proposals, none decided (section 6):** roll_to_pitch back to 3 walls (P1); a CAD change of the knee sheet eye (P2) or 5 walls 40 % as a stopgap (P3); bench load and fatigue checks on the left leg before the right leg prints (P7); PETG for the hot parts only if the thermal guard cannot keep them under about 50 C (P5); first walks on a soft floor with a tether, and spare roll_to_pitch parts (P6).

## Files

| File | What it is |
|---|---|
| STRUCTURE_TWIN.md | This file. |
| tables.md | All tables, written by st_finalize.py. |
| st_sim.py | Instrumented MuJoCo model of our build (force and torque sensors at all 14 joints, accelerometers at every link centre of mass, optional printed-part collision for falls) and the control loop of sim/added_mass_sim.py with logging, state snapshots and a changeable time step. |
| st_loads.py | Walking, standing and push-recovery runs, solver check, rainflow counting, the same walks at the trained mass. |
| st_falls.py | Fall runs with the contact stiffness sweep. |
| st_interfaces.py | Joint loads split onto the drive horn, idle horn (or 6804 bearing) and servo case screw groups (fasteners.json positions). |
| st_fea.py | FEA core: TetGen mesh, as-printed zones, materials, RBE3 loads, tied members, AMG solver, failure index in each part's print frame. |
| st_fea_run.py | The FEA studies: unit loads, superposition over every sim sample, weak spot (also with the maker Z and PETG strengths), insert loads, stress histories for fatigue; and the checks: mesh convergence (conv), stress averaging radius (avgcheck), the knee sheet alone (sheetlocal). |
| st_report.py | Load, fall, fastener, fatigue, FEA and hot-case tables (used by st_finalize.py). |
| st_finalize.py | Writes tables.md and the generated tables of this file (between the <!-- KEY --> markers) from the scratch outputs. |
| st_slice_proposals.py | PrusaSlicer 2.7.2 grams and hours of the proposed print changes (uses print/slice.py unchanged). |

Heavy outputs (time series, meshes, G-code) are in the session scratch folder twinST (loads/, falls/, fea/, fea_conv/, slice_prop/), never in git. Tools: Python venv in that folder with scikit-fem 12.0.2, meshio 5.3.5, tetgen 0.8.4 (TetGen), pyamg 5.4.1 (installed with pip), plus the box's MuJoCo 3.17.0, trimesh 5.2.0, numpy 2.5.3, scipy 1.18.1, manifold3d 3.5.4, PrusaSlicer 2.7.2. scikit-fem and meshio were installed but the final solver is the numpy assembly in st_fea.py (linear tetrahedra), solved with pyamg; gmsh 4.15.2 installed but does not run here (no libGLU).

## 1. Loads (sim pass only)

### 1.1 Model and method
- Model: the Playground MJCF (b9be205) with every inertial replaced by our build (sim/mass_budget.py build_budget, 2652.8 g, unchanged) through sim/added_mass_sim.py write_variant (unchanged). In each child link a site at the joint origin (z = joint axis) carries a MuJoCo force and torque sensor: the full 6D load of the parent on the child (it passes in series through the servo case, its bearings, the horns and the screws). Check: standing, the ankle sensor reads 14.27 N, which is the 15.04 N ground force less the 0.77 N foot [L].
- Control loop: the one of sim/added_mass_sim.py (upstream MjInfer unchanged, 50 Hz policy, accelerometer bias removed, 5.24 rad/s speed limit), copied into st_sim.Sim with logging at every 2 ms step.
- **Solver: 30 Newton iterations instead of the upstream 1.** With 1 iteration the contact and joint forces are not converged: the forward walk logs ground force spikes of 133 to 194 N and knee axis torques of 13 to 21 N m (over the 3.23 N m actuator limit) that vanish with 10, 30 or 100 iterations (the three agree to 0.1 %). Walking speed changes from 0.70 to 0.73 of the command. All loads below use 30 iterations; dt 2 ms against 1 ms changes the peaks by 3 to 6 % [L] (st_loads.py check).
- Axis torque: the sensor torque about the joint axis is what the horn carries: the actuator torque less the joint damping and friction and the armature (reflected rotor and gear inertia, 0.027 kg m2) times the joint acceleration. In hard decelerations it exceeds the 3.23 N m actuator limit (knee up to 4.4 N m walking, 8.6 N m in push recovery at a knee angle of 84 deg, not at the joint limit). That is how a geared servo's output sees a stop [L].
- Cases: stand (20 s), walk forward 0.15 m/s (30 s), turn 1.0 rad/s (20 s), side step 0.2 m/s (20 s), walk with the backlash model (30 s), each nominal and seeds 1 to 3 (16 walking runs, 368 s, no fall). Push recovery: the 15 N case of sim/current_budget.py (0.1 s every 3 s, left and right) for seeds 0 to 3, and single 0.1 s pushes on the trunk at 8 gait phases while walking forward: left 9, 12, 15, 18 N, right 9, 12, 15 N, forward 9, 12, 15 N, back 9, 12 N (100 runs). Push statistics start 0.5 s before the push and stop 1 s before a fall (18 of 100 runs fell).
- Cycle count: the gait period is 0.54 s [U] (Playground reference motion), so **6667 load cycles per hour per leg** while walking, 666,700 in 100 hours. Rainflow (ASTM E1049 three-point, st_loads.rainflow) of the bending moments counts 10,000 to 36,000 cycles per hour over 25 % of the largest range (2 to 5 per gait cycle: heel strike, double support, swing).

### 1.2 Table 1: joint loads, walking and push recovery (peak, with the 99.9th percentile of walking in brackets)

Child link frame at the joint origin, z = joint axis. F radial = force across the axis, F axial = along it, M axis = torque about the axis (the horn torque), M bend = moment across the axis at the joint origin.

| joint | stand F rad N / M bend Nm | walk F radial N (p99.9) | walk F axial N | walk M axis Nm (p99.9) | walk M bend Nm (p99.9) | push F radial N | push F axial N | push M axis Nm | push M bend Nm | walk M bend cycles per h (rainflow, over 25 % of max range) |
|---|---|---|---|---|---|---|---|---|---|---|
| left_hip_yaw | 1 / 0.70 | 27 (20) | 61 | 0.75 (0.46) | 2.68 (2.55) | 40 | 94 | 0.94 | 4.35 | 36329 |
| left_hip_roll | 11 / 0.47 | 69 (54) | 13 | 2.12 (2.03) | 3.62 (2.81) | 105 | 33 | 2.37 | 5.21 | 10731 |
| left_hip_pitch | 12 / 0.46 | 67 (56) | 24 | 1.56 (1.30) | 5.42 (3.68) | 102 | 40 | 1.92 | 7.47 | 19241 |
| left_knee | 13 / 0.38 | 72 (62) | 26 | 4.36 (4.21) | 4.09 (3.28) | 112 | 40 | 6.87 | 5.86 | 16981 |
| left_ankle | 14 / 0.24 | 74 (66) | 27 | 2.70 (2.63) | 2.62 (2.35) | 118 | 40 | 4.03 | 3.05 | 16790 |
| neck_pitch | 7 / 0.11 | 22 (21) | 15 | 0.97 (0.88) | 2.22 (2.14) | 32 | 17 | 1.52 | 2.51 | 17695 |
| head_pitch | 7 / 0.13 | 20 (19) | 14 | 0.40 (0.39) | 1.25 (1.21) | 28 | 16 | 0.72 | 1.39 | 21300 |
| head_yaw | 1 / 0.13 | 16 (15) | 18 | 0.31 (0.31) | 0.39 (0.37) | 19 | 26 | 0.58 | 0.44 | 14722 |
| head_roll | 5 / 0.11 | 18 (18) | 7 | 0.38 (0.36) | 0.63 (0.59) | 25 | 13 | 0.32 | 0.96 | 20405 |
| right_hip_yaw | 2 / 0.75 | 14 (13) | 56 | 0.87 (0.82) | 3.97 (3.27) | 47 | 87 | 0.88 | 4.01 | 24875 |
| right_hip_roll | 7 / 0.20 | 59 (57) | 10 | 3.30 (2.83) | 4.33 (4.11) | 96 | 34 | 2.29 | 5.73 | 10305 |
| right_hip_pitch | 8 / 0.15 | 62 (59) | 17 | 2.37 (2.16) | 3.08 (2.81) | 93 | 39 | 2.98 | 6.83 | 29962 |
| right_knee | 9 / 0.38 | 69 (66) | 17 | 2.89 (2.33) | 2.37 (2.29) | 101 | 39 | 8.63 | 2.84 | 33620 |
| right_ankle | 10 / 0.33 | 73 (71) | 17 | 2.18 (2.00) | 1.88 (1.81) | 107 | 39 | 4.32 | 2.05 | 20909 |

Standing (zero command): the largest are the ankle force 14 N, the knee torque 0.69 N m and the hip yaw bending 0.75 N m.

Against the mass the policy was trained for: the same 16 walking runs with the stock inertials (sim/mass_budget.py model_inertials, through the same write_variant) give lower peaks; our 2652.8 g build raises the 56 walking peaks of Table 1 by 0 to 60 % (median 19 %; the leg joints 9 to 60 %, median 20 %): the left knee axis torque 3.83 to 4.36 N m, the right knee 2.05 to 2.89 N m, the left hip pitch bending 4.26 to 5.42 N m, and the peak sole force 68.6 to 77.7 N (+13 %) [L] (st_loads.py trained). The smallest change is the neck pitch axis torque (+0.3 %), the largest the right hip roll axial force (+60 %, 6.2 to 10.0 N).

### 1.3 Falls and the contact stiffness

The upstream MJCF lets only the two TPU soles touch the floor: a fallen robot sinks through it. For falls (st_falls.py) every printed part mesh (convex hull) also touches the floor but not the robot itself. Each fall first runs at the lab settings until the first printed-part contact; then it is replayed from 0.1 s before that contact with a 0.1 ms step and a stiffer contact on the printed parts, so every stiffness starts from the same state. Falls: standing, a 60 N push of 0.1 s back, forward, left, right (40 N does not topple it); standing with every servo torque off; and the rough terrain walk of print/MASS_STUDY.md (start raised 23 mm), seeds 1 to 6 (5 of 6 fell; seed 1 did not in 30 s). Impact speeds of the first printed part: 1.1 to 1.75 m/s downward (trunk), 1.5 m/s (head, torque off).

MuJoCo contact is soft: the default (time constant 0.02 s) behaves like a spring of about 2.6 kN/m per kg of effective mass. The contact level is the stated stiffness: each run's K eff = peak contact force / penetration at that peak, for the printed body hit hardest.

| Level | solref (time constant, damping ratio) | K eff measured (MN/m) | What it represents |
|---|---|---|---|
| MuJoCo default | 0.02 s, 1.0 | 0.27 to 3.7 (pen. under 0.2 mm, so the ratio is noisy) | the lab's sim; damped, no bounce, force limited by the damping |
| soft | 0.0158 s, 0.2 | 0.14 to 0.34 | a hit on the middle of a printed wall: a clamped circular plate of the D22 2-wall shell (3.0 mm, faces 0.86 mm) gives 0.13 to 1.2 MN/m for a 45 to 15 mm free span, the 4-wall head 0.17 to 2.2 MN/m (Timoshenko plate formula, w = P a^2 / (16 pi D)); the shin segment FEA gives 0.044 MN/m across the knee horn |
| mid | 0.005 s, 0.2 | 1.35 to 3.2 | an edge or corner of a shell on a hard floor (tile, concrete) |
| hard | 0.00289 s, 0.2 | 4.2 to 16 | a stiff corner on concrete: an upper bound |

Damping ratio 0.2 gives a restitution of about 0.5 (ASSUMPTION, range 0.3 to 0.7; damping ratio 1 shown in the scratch tables gives the same order). Uncertainty: the elastic peak force goes with the square root of the stiffness, so the soft to mid range (10 x in stiffness) is a factor of 2.9 to 3.4 in force in these runs. The rigid-body model also ignores the compliance between the hit and the joints (PLA parts, gear backlash), so the joint loads at "mid" and "hard" are upper bounds. A carpet or a mat is below "soft".

| fall | contact level | printed part body hit hardest | peak contact N | K eff (MN/m) | head g | trunk g | head_roll joint F N | neck_pitch M bend Nm | hip pitch M bend Nm | knee M axis Nm | ankle F N |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rough_seed2 | MuJoCo default | trunk_assembly | 256 | 2.12 | 8 | 11 | 64 | 1.9 | 1.4 | 0.9 | 24 |
| rough_seed2 | soft | trunk_assembly | 633 | 0.32 | 23 | 27 | 147 | 4.8 | 2.0 | 2.0 | 33 |
| rough_seed2 | mid | trunk_assembly | 1905 | 3.01 | 66 | 84 | 444 | 14.5 | 9.3 | 5.8 | 167 |
| rough_seed2 | hard | trunk_assembly | 3241 | 8.07 | 112 | 143 | 682 | 24.6 | 24.9 | 16.2 | 460 |
| rough_seed3 | MuJoCo default | trunk_assembly | 256 | 2.32 | 8 | 11 | 71 | 2.0 | 4.9 | 0.9 | 20 |
| rough_seed3 | soft | trunk_assembly | 539 | 0.34 | 20 | 23 | 112 | 4.0 | 6.4 | 1.6 | 49 |
| rough_seed3 | mid | trunk_assembly | 1967 | 3.10 | 69 | 86 | 565 | 15.4 | 52.2 | 10.3 | 311 |
| rough_seed3 | hard | trunk_assembly | 2670 | 15.99 | 89 | 117 | 811 | 23.5 | 48.5 | 30.7 | 920 |
| rough_seed4 | MuJoCo default | trunk_assembly | 256 | 1.35 | 8 | 11 | 62 | 1.8 | 1.0 | 0.9 | 18 |
| rough_seed4 | soft | trunk_assembly | 595 | 0.31 | 21 | 26 | 176 | 4.1 | 1.5 | 1.9 | 21 |
| rough_seed4 | mid | trunk_assembly | 1580 | 3.03 | 54 | 69 | 485 | 9.5 | 4.2 | 5.1 | 74 |
| rough_seed4 | hard | trunk_assembly | 2662 | 8.56 | 93 | 116 | 688 | 14.3 | 9.0 | 8.6 | 146 |
| rough_seed5 | MuJoCo default | trunk_assembly | 190 | 3.72 | 9 | 9 | 65 | 2.5 | 3.5 | 2.0 | 47 |
| rough_seed5 | soft | trunk_assembly | 397 | 0.33 | 15 | 17 | 144 | 5.8 | 8.0 | 5.3 | 127 |
| rough_seed5 | mid | trunk_assembly | 1293 | 2.97 | 56 | 55 | 525 | 14.8 | 33.3 | 18.5 | 562 |
| rough_seed5 | hard | trunk_assembly | 2315 | 9.75 | 90 | 99 | 918 | 41.7 | 97.8 | 57.0 | 1660 |
| rough_seed6 | MuJoCo default | trunk_assembly | 203 | 2.01 | 7 | 9 | 60 | 2.4 | 4.4 | 1.4 | 28 |
| rough_seed6 | soft | trunk_assembly | 453 | 0.33 | 15 | 19 | 128 | 5.7 | 17.9 | 7.0 | 271 |
| rough_seed6 | mid | trunk_assembly | 1696 | 3.02 | 125 | 123 | 671 | 58.2 | 205.2 | 70.4 | 3061 |
| rough_seed6 | hard | head_assembly | 2870 | 6.04 | 291 | 252 | 1918 | 164.1 | 341.8 | 190.6 | 6575 |
| stand_push_back | MuJoCo default | trunk_assembly | 292 | 1.96 | 11 | 13 | 112 | 4.9 | 5.0 | 3.0 | 34 |
| stand_push_back | soft | trunk_assembly | 581 | 0.33 | 24 | 25 | 287 | 12.9 | 10.9 | 3.0 | 34 |
| stand_push_back | mid | trunk_assembly | 1774 | 3.20 | 80 | 75 | 925 | 35.1 | 33.9 | 7.4 | 77 |
| stand_push_back | hard | trunk_assembly | 2990 | 9.70 | 136 | 127 | 1565 | 58.2 | 61.6 | 12.9 | 133 |
| stand_push_forward | MuJoCo default | head_assembly | 381 | 0.27 | 30 | 20 | 228 | 10.9 | 2.0 | 4.7 | 44 |
| stand_push_forward | soft | head_assembly | 888 | 0.16 | 71 | 45 | 511 | 18.4 | 5.5 | 3.1 | 85 |
| stand_push_forward | mid | head_assembly | 2432 | 1.35 | 196 | 128 | 1422 | 85.6 | 15.8 | 10.1 | 248 |
| stand_push_forward | hard | trunk_assembly | 3320 | 9.60 | 278 | 209 | 1882 | 147.1 | 83.4 | 35.9 | 1267 |
| stand_push_left | MuJoCo default | trunk_assembly | 327 | 1.60 | 12 | 14 | 79 | 3.1 | 13.9 | 2.0 | 14 |
| stand_push_left | soft | trunk_assembly | 804 | 0.29 | 27 | 34 | 290 | 11.6 | 38.7 | 4.3 | 32 |
| stand_push_left | mid | trunk_assembly | 2552 | 2.88 | 78 | 109 | 761 | 27.1 | 127.6 | 13.6 | 103 |
| stand_push_left | hard | trunk_assembly | 4366 | 8.46 | 135 | 187 | 1332 | 45.9 | 208.2 | 23.4 | 173 |
| stand_push_right | MuJoCo default | trunk_assembly | 361 | 3.29 | 16 | 15 | 119 | 2.4 | 5.0 | 1.7 | 14 |
| stand_push_right | soft | trunk_assembly | 870 | 0.32 | 49 | 37 | 387 | 10.9 | 12.9 | 3.9 | 176 |
| stand_push_right | mid | trunk_assembly | 2775 | 3.22 | 152 | 117 | 1165 | 39.9 | 40.1 | 12.0 | 622 |
| stand_push_right | hard | trunk_assembly | 4768 | 9.75 | 258 | 201 | 1975 | 61.3 | 74.4 | 20.5 | 917 |
| stand_torque_off | MuJoCo default | head_assembly | 163 | 0.89 | 13 | 7 | 93 | 4.2 | 1.2 | 0.9 | 26 |
| stand_torque_off | soft | head_assembly | 420 | 0.14 | 33 | 18 | 250 | 9.9 | 1.3 | 1.0 | 55 |
| stand_torque_off | mid | head_assembly | 1316 | 1.48 | 102 | 55 | 775 | 29.9 | 3.0 | 3.1 | 156 |
| stand_torque_off | hard | head_assembly | 2169 | 4.24 | 174 | 85 | 1260 | 47.5 | 4.7 | 4.9 | 245 |

## 2. Ranking and FEA (FEA pass only)

### 2.1 Ranking
Every joint's load was carried to the parts at both its ends (st_interfaces.py): the horn ears of the child, the servo case holder of the parent. The FEA was run on every leg and neck stage that carries a joint load from one servo to the next (seven studies: the shin and thigh segments, roll_to_pitch, the hip roll stage, foot_top, the neck sheets and head_roll_mount), and the ranking comes from the FEA (Table 3). The trunk and head shells carry only inertial loads in walking and are judged for falls by a hand calculation (section 6, W8). The two weakest:
- Knee sheet eye neck (shin): in-plane bending of the 24.7 mm wide, 3.6 mm thick neck by the knee torque gives 2.7 MPa per N m (beam). The FEA of the sheet alone under a unit knee torque (st_fea_run.py sheetlocal, section 2.4) gives 7.5 MPa per N m at the neck at mesh level 1 and 4.9 to 5.0 at levels 2 and 3 (1 mm averages; raw element values 7.8, 5.4 and 5.3): a stress concentration of about 2 from the eye, its 7 mm hub hole and the 4 horn screw holes, with only 2.5 mm of plastic between a screw hole and the eye edge. Level 1 reads the neck 1.5 x high; at levels 2 and 3 the highest stress of the sheet is instead in the bottom skin beside the eye (x = +-10.2 mm, 5.4 to 5.6 MPa per N m), the spot that also governs the 5-wall proposal. At the walking peak the knee torque gives about 80 % of the stress at the neck and the axial force most of the rest [L] (unit-load split at the weak spot).
- roll_to_pitch: the weak spot is the wall at x 27 to 32 mm that joins the two hip roll horn ears (5 mm thick, printed upright: print z = link y). The idle-horn force (90 N walking, 130 N push, from the two-support split of the hip roll bending moment) drives it. At level 1 the 1 mm average gives 13.8 MPa of shear across the layers in the middle of the wall at the walking peak (24.3 MPa von Mises); at levels 2 and 3 the governing stress is in-plane, in the bottom skin at the end of the wall (31.7 and 28.9 MPa von Mises). The raw element peak at level 1 (19.6 MPa of interlayer tension) was a single-element spike (section 2.2).

### 2.2 FEA method
- Geometry: the print STLs (print/*.stl, mm) in their URDF link frame. The parts of a leg segment (the two knee sheets and the leg_spacer) are meshed one by one and tied where they touch (springs of 20 kN/mm between surface nodes closer than 0.45 mm: the bonded M3 insert joints and the 0.2 mm spacer gap that the screws close; ASSUMPTION). Elements within 2 mm of a tie are not counted in the peak (a node-to-node tie is not a real contact); the joint is judged by its insert loads instead.
- Mesh: TetGen linear tetrahedra (tetgen 0.8.4). Levels: 1 (radius-edge 2.0, dihedral over 10 deg, volume under 5 mm3), 2 (1.6, 15 deg, 1 mm3), 3 (1.4, 18 deg, 0.3 mm3). The STL triangles (holes with many facets) set the surface size. Screening at level 1; convergence on the two weakest: roll_to_pitch at levels 1 to 3, the shin segment at levels 1 and 2 and its knee sheet alone at levels 1 to 3 (section 2.4). foot_top is the exception: its STL has a 0.003 mm edge and 310 needle triangles, so TetGen made 70 % of its tets smaller than 1e-4 mm3 and the CG solver stalled at a relative residual of 2e-2 (a first foot run, discarded); its STL edges under 0.01 mm are collapsed first (manifold3d 3.5.4 simplify; volume change -0.004 %), after which it solves like the others. The logged unit solve of every study and level reached a relative residual under 1e-8 (27 to 110 CG iterations; section 2.4 and tables.md).
- As-printed zones (each element, in the print frame of its own part, z = parts.csv "up"): walls = within n beads of a side face (2 walls 0.86 mm, 3 walls 1.27 mm, 4 walls 1.67 mm, 5 walls 2.09 mm; print/config/ovr_insert.ini: 0.45 + (n - 1) x 0.41 mm); top skin 1.0 mm (5 layers) under an up-facing face; bottom skin 0.8 mm (4 layers); solid rings of mod_ring.ini (insert bore + 4.0 mm); the rest gyroid infill (15 %, the neck parts 40 %). D22 profile per part from print/parts.csv: roll_to_pitch, roll_motor_top, foot_top, foot_side 2 walls 15 % (rings on foot_top, foot_bottom_pla, leg_spacer); knee sheets, roll_motor_bottom 3 walls; neck parts 5 walls 40 %.
- Effective properties: solid zones isotropic, E 2641 MPa (Overture PLA TDS v5.1, X-Y, 100 % infill specimens, 0.4 mm nozzle, search text; the lab read 2650 MPa in PRINT_PLAN.md), nu 0.35 (ASSUMPTION, 0.30 to 0.40). Gyroid infill: E = E_s rho^2.12 (Gibson and Ashby power law [I] Gibson & Ashby, Cellular Solids, 2nd ed. 1997; exponent 2.12 measured for gyroid lattices [I] Doyle et al. 2025, Adv. Eng. Mater., doi 10.1002/adem.202402495, search text), 47 MPa at 15 %, 379 MPa at 40 %, nu 0.30; nearly isotropic [I] Bean, Lopez-Anido and Vel 2022, Appl. Sci. 12(4):2180 (Zener ratio 0.95 to 1.25, search text). The layer direction enters through the failure criterion, not the stiffness (a z modulus of 0.7 x changes the force-driven stresses little; not run).
- Strengths (room temperature): in-plane X 47.1 MPa (Overture PLA TDS v5.1, X-Y tensile, search text); interlayer Z design 22 MPa (the conservative static reference for printed PLA of [I] Ezeh & Susmel 2019, Mater. Design Process. Commun. 1(2):e45, doi 10.1002/mdp2.45, search text), with the maker's Z 39.4 MPa shown as the upper value (Overture Easy PLA listing extracted from the maker TDS, 3dfilamentprofiles.com/filament/details/7100, search text); interlayer shear S = Z (ASSUMPTION). Infill: 0.3 rho^1.5 X (Gibson and Ashby plastic collapse of open cells), 0.82 MPa at 15 %. The SF with the maker Z (39.4 MPa) and with PETG strengths (section 5) are found over the whole part, since the weak spot can move; for an in-plane weak spot they follow exactly (the maker Z changes nothing, PETG scales by 34 / 47.1), and a run made before that evaluation shows the value at the PLA weak spot as "at most".
- Failure index per element: solid zones max(von Mises / X, sqrt((max(s_zz, 0) / Z)^2 + (tau_z / S)^2)) in the part's print frame; infill von Mises / infill strength. SF = 1 / peak FI. The peak leaves out elements within 1 mm of loaded or fixed nodes (point-like boundary conditions).
- **Stress averaging over 1 mm:** the failure index is taken on the element stress tensor averaged (by volume) over the elements of the same part and the same zone class (solid or infill) whose centres lie within 1.0 mm (at most the 32 nearest). Reason: linear tetrahedra give one stress per element, and the 0.86 to 2.1 mm wall bands and the 56 x softer infill cut through elements, so single elements carry spikes. On roll_to_pitch at level 1 the raw element peak (19.6 MPa across the layers at the walking peak, SF 0.96) was such a spike: under the unit load that drives it, the interlayer stress of the elements round it changes sign (50 to 66 % of the same sign within 0.5 to 2 mm), and its 0.5 and 1 mm averages are 1/17 and 1/40 of it. On the knee sheet the field is smooth (100 % of the same sign, the 1 mm average is 0.87 to 0.93 of the peak). (These two diagnostics ran in the session scratch folder and are not kept here; the avgcheck below is.) 1 mm is about two 0.45 mm beads and five 0.2 mm layers, the scale of the printed structure; for notched printed PLA the Theory of Critical Distances uses a material length [I] Ezeh & Susmel 2020, Int. J. Fatigue 136:105583, doi 10.1016/j.ijfatigue.2020.105583 (search text), whose value for this filament is not known (ASSUMPTION: 1 mm). Checked at level 1 with 0.5 and 1.5 mm (st_fea_run.py avgcheck, section 2.4): roll_to_pitch walking 1.50 and 1.61 against 1.60, the shin 1.45 and 1.56 against 1.56; the walking and push verdicts do not change, the count of soft falls under 1.2 does (roll_to_pitch 7 at 0.5 and 1 mm, 6 at 1.5 mm; the shin 3, 2 and 0). At level 1 the elements at most weak spots are about 3 mm across, so the average reaches only the small elements (round holes and thin features, where the spikes were); at the levels 2 and 3 of the convergence check it covers the weak spots too. The raw element peak is listed beside every result.
- Supports: the part is fixed where it holds the next servo (nodes within 0.3 mm of that servo's case meshes, and its case screw holes): a rigid, bonded PA+GF servo case (ASSUMPTION). Loads: at the horn screw holes (hole walls and the face annuli under the heads, RBE3: statically equal, no added stiffness), with the two-support split of st_interfaces.py: the drive horn gets its share of the radial force, the full axial force and the full axis torque; the idle horn (or the hip yaw 6804 bearing boss) its share of the radial force. Six unit loads are solved per study; every sim sample is a linear combination, so the peak over each whole history and the stress history at the weak spot (fatigue) come from the same solves. Solver: pyamg smoothed aggregation with CG, relative residual under 1e-8; the reaction at the supports equals the applied unit load [L].

### 2.3 Table 3: safety factor per part (room temperature, SF = 1 / failure index, lab margin 2 walking and push, 1.2 falls)

<!-- FEA_TABLE -->
| study | parts | SF walk | SF push | SF walk / push, maker Z 39.4 MPa | SF walk / push, PETG | falls soft: worst SF (falls under 1.2 of 10) | falls mid | falls MuJoCo default | weak spot at the walking peak (link frame) | SF walk, raw element peak | nodes / tets |
|---|---|---|---|---|---|---|---|---|---|---|---|
| roll_to_pitch | left_roll_to_pitch | 1.60 | 1.11 | 1.83 / 1.25 | 1.32 / 0.90 | 0.48 (7 of 10) | 0.12 (10 of 10) | 0.76 (2 of 10) | left_roll_to_pitch, wall, interlayer (von Mises 24.3, s_zz -9.6, tau_z 13.8 MPa) at [31.7, -0.3, 18.4] mm; walk_side_0.2_s1 | 0.96 | 56085 / 224606 |
| shin_segment | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet, leg_spacer | 1.56 | 1.04 | 1.56 / 1.04 | 1.13 / 0.75 | 1.12 (2 of 10) | 0.37 (7 of 10) | 2.26 (0 of 10) | knee_to_ankle_left_sheet, wall, in-plane (von Mises 30.1, s_zz 1.2, tau_z 0.2 MPa) at [-11.3, -7.0, -1.4] mm; walk_side_0.2_s3 | 1.45 | 86629 / 351295 |
| thigh_segment | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet, leg_spacer | 2.70 | 1.74 | 2.70 / 1.74 | 1.95 / 1.26 | 0.73 (4 of 10) | 0.23 (9 of 10) | 1.31 (0 of 10) | knee_to_ankle_left_sheet, bottom skin, in-plane (von Mises 17.4, s_zz -0.2, tau_z 0.9 MPa) at [-11.7, -12.7, -3.4] mm; walk_side_0.2_s1 | 2.33 | 87266 / 354102 |
| hip_roll_stage | roll_motor_top, roll_motor_bottom | 12.93 | 9.59 | at most 15.97 / at most 11.42 | at most 11.53 / at most 8.24 | 1.84 (0 of 10) | 0.55 (5 of 10) | 4.05 (0 of 10) | roll_motor_top, wall, interlayer (von Mises 2.9, s_zz -0.1, tau_z 1.7 MPa) at [3.7, -0.1, -5.6] mm; walk_side_0.2_s1 | 11.95 | 27677 / 105708 |
| foot | foot_top | 5.47 | 4.42 | 6.66 / 4.51 | 4.81 / 3.25 | 1.53 (0 of 10) | 0.49 (2 of 10) | 7.73 (0 of 10) | foot_top, top skin, interlayer (von Mises 7.1, s_zz 1.2, tau_z 3.8 MPa) at [-13.3, -15.5, -0.9] mm; walk_side_0.2_s0 | 4.56 | 39425 / 161381 |
| neck_sheets | neck_left_sheet, neck_right_sheet | 5.39 | 3.59 | 5.39 / 3.59 | 3.89 / 2.59 | 0.41 (9 of 10) | 0.13 (10 of 10) | 1.02 (2 of 10) | neck_left_sheet, wall, in-plane (von Mises 8.7, s_zz 1.4, tau_z 0.6 MPa) at [12.1, 10.2, -0.8] mm; turn_1.0_s3 | 3.68 | 22802 / 87252 |
| head_roll_mount | head_roll_mount | 47.77 | 27.09 | at most 85.56 / at most 44.64 | at most 49.95 / at most 28.32 | 0.79 (5 of 10) | 0.26 (10 of 10) | 2.05 (0 of 10) | head_roll_mount, wall, interlayer (von Mises 0.4, s_zz 0.4, tau_z 0.1 MPa) at [28.6, 18.7, -1.9] mm; walk_backlash_s1 | 30.32 | 17982 / 67404 |
<!-- /FEA_TABLE -->

Fall columns: the worst of the 10 falls at that contact level and how many of the 10 are under the 1.2 fall margin. Mesh level 1 for all rows (the screening); the two weakest parts at levels 2 and 3 are in section 2.4.

### 2.4 Mesh convergence

<!-- CONV_TABLE -->
| study | mesh level | nodes | tets | SF walk (1 mm average) | SF push | falls soft | SF walk, raw element peak | walking weak spot (link frame mm) | largest unit-load displacement mm | CG (last unit load) |
|---|---|---|---|---|---|---|---|---|---|---|
| roll_to_pitch | 1 | 56085 | 224606 | 1.60 | 1.11 | 0.48 (7 of 10) | 0.96 | [31.7, -0.3, 18.4] | 0.1057 | 104 iterations, relative residual 9.6e-09 |
| roll_to_pitch | 2 | 92884 | 414757 | 1.48 | 1.08 | 0.47 (7 of 10) | 0.78 | [30.4, -15.0, 19.7] | 0.1041 | 83 iterations, relative residual 8.9e-09 |
| roll_to_pitch | 3 | 103960 | 468863 | 1.63 | 1.21 | 0.42 (8 of 10) | 0.78 | [31.6, -14.4, 18.5] | 0.1059 | 76 iterations, relative residual 8.4e-09 |
| shin_segment | 1 | 86629 | 351295 | 1.56 | 1.04 | 1.12 (2 of 10) | 1.45 | [-11.3, -7.0, -1.4] | 0.1697 | 82 iterations, relative residual 8.7e-09 |
| shin_segment | 2 | 136008 | 610488 | 1.63 | 1.07 | 1.06 (2 of 10) | 1.39 | [10.2, 0.2, -3.7] | 0.1562 | 80 iterations, relative residual 9.8e-09 |

| study (mesh level 1) | stress averaging | SF walk | SF push | falls soft | falls mid | walking weak spot (elements inside the radius there) |
|---|---|---|---|---|---|---|
| roll_to_pitch | raw element | 0.96 | 0.66 | 0.41 (9 of 10) | 0.12 (10 of 10) | [27.6, -7.5, 32.7] (1) |
| roll_to_pitch | 0.5 mm | 1.50 | 1.03 | 0.48 (7 of 10) | 0.12 (10 of 10) | [27.5, -0.6, 30.9] (1) |
| roll_to_pitch | 1 mm | 1.61 | 1.11 | 0.48 (7 of 10) | 0.12 (10 of 10) | [31.7, -0.3, 18.4] (1) |
| roll_to_pitch | 1.5 mm | 1.61 | 1.11 | 0.48 (6 of 10) | 0.12 (10 of 10) | [31.7, -0.3, 18.4] (1) |
| shin_segment | raw element | 1.45 | 0.97 | 0.52 (3 of 10) | 0.17 (8 of 10) | [-11.8, -9.7, -0.4] (1) |
| shin_segment | 0.5 mm | 1.45 | 0.97 | 1.01 (3 of 10) | 0.32 (8 of 10) | [-11.8, -9.7, -0.4] (1) |
| shin_segment | 1 mm | 1.56 | 1.04 | 1.12 (2 of 10) | 0.37 (7 of 10) | [-11.3, -7.0, -1.4] (2) |
| shin_segment | 1.5 mm | 1.56 | 1.04 | 1.24 (0 of 10) | 0.40 (7 of 10) | [-11.3, -7.0, -1.4] (2) |

| mesh level | nodes | tets | neck: raw von Mises MPa per N m (where) | neck: 1 mm average | whole sheet: raw peak (where) | whole sheet: 1 mm average peak (where) | largest displacement mm per N m |
|---|---|---|---|---|---|---|---|
| 1 | 16493 | 62616 | 7.84 at [-11.42, -12.07, -3.65] | 7.47 | 7.84 at [-11.42, -12.07, -3.65] | 7.47 at [-11.42, -12.07, -3.65] | 0.194 |
| 2 | 25162 | 107698 | 5.36 at [-11.69, -7.35, -0.36] | 4.93 | 6.59 at [10.16, 0.83, -3.7] | 5.45 at [10.25, 0.22, -3.69] | 0.179 |
| 3 | 37749 | 172175 | 5.34 at [-12.0, -9.14, -0.25] | 4.97 | 6.78 at [-10.22, 0.48, -3.69] | 5.64 at [-10.25, 0.45, -3.66] | 0.191 |
<!-- /CONV_TABLE -->

Tables: the mesh levels of the two weakest studies; the stress averaging radius at level 1; the knee sheet alone under a unit knee torque (st_fea_run.py sheetlocal). Reading:
- **roll_to_pitch:** walking SF 1.60, 1.48 and 1.63 at levels 1, 2 and 3 (56,085, 92,884 and 103,960 nodes), push 1.11, 1.08 and 1.21: within 10 % of each other. The weak spot stays in the ear wall (x 30 to 32 mm) but moves: shear across the layers in the middle of the wall at level 1, in-plane stress in the bottom skin at the end of the wall (y -14 to -15 mm) at levels 2 and 3. The largest unit-load displacement changes by under 2 % (0.104 to 0.106 mm). The raw element peak does not settle (0.96, 0.78, 0.78): single elements where the 0.86 mm wall band meets the infill, which the 1 mm average removes once the elements are small enough to have neighbours within 1 mm (at level 1 most weak-spot elements have none, second table). Level 3 has only 12 % more nodes than level 2, because the STL facets already set the element size in the thin walls; a finer surface mesh was not tried.
- **Shin segment:** 1.56 / 1.04 at level 1 and 1.63 / 1.07 at level 2 (136,008 nodes); the weak spot moves from the neck where the eye joins the plate (level 1) to the bottom skin beside a horn screw (level 2). The knee sheet alone: the neck stress per N m of knee torque is 7.5, 4.9 and 5.0 MPa at levels 1, 2 and 3 (1 mm averages), so level 1 reads the neck 1.5 x high; the highest stress of the sheet settles at 5.4 to 5.6 MPa per N m beside the horn screws at levels 2 and 3, where the full model puts its level 2 weak spot.
- **Verdict:** the walking and push SF of both weak parts are known to about 10 % of the mesh. The other parts were screened at level 1 only (Table 3).

## 3. Fasteners and inserts

Lab margin: SF 2.0 on walking and on push recovery (service loads, repeated thousands of times per hour, with FDM strength scatter, creep of the clamped plastic and no preload credit) and 1.2 on falls (rare accidental loads, first hit only; a part may crack but should not separate). Capacities:
- **Horn screws** (M3 into the aluminium horn; the PLA part is clamped under the head): PLA bearing of the 3.0 mm shank on the hole wall, d x t x 47.1 MPa (ASSUMPTION: bearing strength at least the TDS tensile strength; t = the clamped PLA thickness, fasteners.json "near"); head pull-through: the smaller of the plug shear pi dk t x 12.7 MPa (0.577 x 22 MPa) and the head bearing pi/4 (dk^2 - 3.3^2) x 47.1 MPa. Preload friction is not counted (PLA creeps). The thread in the horn (2.2 to 2.4 mm in aluminium) is not checked: the horn alloy is not published (BLOCKER, not PLA).
- **Servo case screws** (M2 self-tapping into the STS3215 PA+GF case, through the printed bracket): PLA bearing of the 2.0 mm screw on the bracket hole, d x t x 47.1 MPa. Loads are an RBE3 split over the case screws only (the pocket also holds the servo, so this is an upper bound). Pull-out from the PA+GF pilots: no data (BLOCKER).
- **Heat-set inserts** (M3, CNC Kitchen M3 x 5.7, BOM 16): pull-out 1354 to 1552 N for M3 inserts in FDM PLA over 3 wall thicknesses and 3 infill patterns, 27 specimens [I] "Mechanical Performance of Heat-Set Threaded Inserts in FDM-Printed PLA Components", Eng. Proc. 157(1):40, 2026 (search text); about 1400 N for CNC Kitchen M3 inserts in PLA, 4.0 to 4.2 mm holes [I] CNC Kitchen, "Are our heat-set insert datasheets wrong?" (search text, secondary summaries); torque-out about 3.5 N m in PLA [I] CNC Kitchen, "Threaded inserts for 3D prints, cheap vs expensive" (search text). Sideways: no test found: knurl 4.6 x 5.7 mm bearing at 47.1 MPa = 1235 N, half of it (618 N) used as the low value (ASSUMPTION). The D22 rings (2.0 mm solid) are not the tested walls; the S1 gate tests 5 kg (49 N) only.
- **Self-tapping screws in printed pilots** (M2.5 and M2, electronics, eyes, lid, speaker, camera): no published pull-out test for these sizes in printed PLA pilots was found (searches listed in Sources): BLOCKER for test data. Computed: thread strip 0.6 pi d L x tau with tau 12.7 to 27.2 MPa (0.577 x 22 or 47.1 MPa), L = the engagement of fasteners.json.

### 3.1 Table 5: horn and servo case screws (per screw, worst of each set; N / SF)

| screw group | n | printed part | PLA t mm | PLA bearing cap. N | walk N / SF | push N / SF | fall soft N / SF | fall mid N / SF | under the margin |
|---|---|---|---|---|---|---|---|---|---|
| left_hip_yaw drive horn | 4 | roll_motor_top | 2.9 | 404 | 36 / 11.2 | 41 / 9.8 | 253 / 1.6 | 846 / 0.5 | fall mid |
| left_hip_roll drive horn | 4 | left_roll_to_pitch | 3.0 | 417 | 78 / 5.3 | 88 / 4.7 | 429 / 1.0 | 1407 / 0.3 | fall soft, fall mid |
| left_hip_roll idle horn | 4 | left_roll_to_pitch | 3.0 | 431 | 25 / 17.5 | 35 / 12.2 | 75 / 5.8 | 240 / 1.8 | none |
| left_hip_pitch drive horn | 4 | knee_to_ankle_left_sheet | 2.9 | 410 | 67 / 6.2 | 84 / 4.9 | 363 / 1.1 | 1110 / 0.4 | fall soft, fall mid |
| left_hip_pitch idle horn | 4 | knee_to_ankle_right_sheet | 3.1 | 438 | 37 / 11.9 | 51 / 8.6 | 103 / 4.3 | 361 / 1.2 | none |
| left_knee drive horn | 4 | knee_to_ankle_left_sheet | 2.9 | 410 | 168 / 2.4 | 258 / 1.6 | 208 / 2.0 | 642 / 0.6 | push, fall mid |
| left_knee idle horn | 4 | knee_to_ankle_right_sheet | 3.1 | 438 | 28 / 15.8 | 40 / 11.0 | 81 / 5.4 | 252 / 1.7 | none |
| left_ankle drive horn | 4 | foot_top | 3.0 | 417 | 101 / 4.1 | 155 / 2.7 | 128 / 3.3 | 384 / 1.1 | fall mid |
| left_ankle idle horn | 4 | foot_side | 3.0 | 431 | 18 / 24.2 | 21 / 20.8 | 42 / 10.4 | 129 / 3.3 | none |
| neck_pitch drive horn | 4 | neck_left_sheet | 2.0 | 283 | 44 / 6.4 | 64 / 4.4 | 691 / 0.4 | 2211 / 0.1 | fall soft, fall mid |
| neck_pitch idle horn | 4 | neck_right_sheet | 2.0 | 290 | 15 / 19.2 | 17 / 17.0 | 125 / 2.3 | 582 / 0.5 | fall mid |
| head_pitch drive horn | 4 | head_pitch_to_yaw | 1.9 | 276 | 18 / 15.7 | 30 / 9.3 | 1045 / 0.3 | 3110 / 0.1 | fall soft, fall mid |
| head_pitch idle horn | 4 | head_pitch_to_yaw | 2.0 | 290 | 8 / 34.2 | 9 / 30.7 | 131 / 2.2 | 575 / 0.5 | fall mid |
| head_yaw drive horn | 4 | head_pitch_to_yaw | 2.0 | 290 | 14 / 20.5 | 24 / 11.9 | 818 / 0.4 | 3746 / 0.1 | fall soft, fall mid |
| head_yaw idle horn | 4 | head_pitch_to_yaw | 2.1 | 304 | 3 / 114.9 | 3 / 101.5 | 341 / 0.9 | 996 / 0.3 | fall soft, fall mid |
| head_roll drive horn | 4 | head_yaw_to_roll | 1.8 | 254 | 16 / 15.6 | 15 / 17.2 | 674 / 0.4 | 1725 / 0.1 | fall soft, fall mid |
| right_hip_yaw drive horn | 4 | roll_motor_top | 2.9 | 404 | 45 / 9.1 | 47 / 8.6 | 1003 / 0.4 | 3322 / 0.1 | fall soft, fall mid |
| right_hip_roll drive horn | 4 | right_roll_to_pitch | 3.0 | 417 | 125 / 3.3 | 88 / 4.8 | 286 / 1.5 | 972 / 0.4 | fall mid |
| right_hip_roll idle horn | 4 | right_roll_to_pitch | 3.0 | 431 | 29 / 14.7 | 39 / 11.1 | 242 / 1.8 | 858 / 0.5 | fall mid |
| right_hip_pitch drive horn | 4 | knee_to_ankle_right_sheet | 2.9 | 410 | 88 / 4.6 | 122 / 3.4 | 356 / 1.1 | 1809 / 0.2 | fall soft, fall mid |
| right_hip_pitch idle horn | 4 | knee_to_ankle_left_sheet | 3.1 | 438 | 21 / 20.9 | 46 / 9.4 | 263 / 1.7 | 1393 / 0.3 | fall mid |
| right_knee drive horn | 4 | knee_to_ankle_left_sheet | 2.9 | 410 | 113 / 3.6 | 340 / 1.2 | 303 / 1.4 | 3364 / 0.1 | push, fall mid |
| right_knee idle horn | 4 | knee_to_ankle_right_sheet | 3.1 | 438 | 16 / 27.2 | 19 / 22.7 | 35 / 12.6 | 292 / 1.5 | none |
| right_ankle drive horn | 4 | foot_top | 3.0 | 417 | 85 / 4.9 | 172 / 2.4 | 313 / 1.3 | 3559 / 0.1 | fall mid |
| right_ankle idle horn | 4 | foot_side | 3.0 | 431 | 13 / 33.8 | 14 / 31.1 | 48 / 9.1 | 443 / 1.0 | fall mid |
| left_hip_yaw servo case screws | 8 | trunk_top | 2.8 | 264 | 18 / 14.4 | 21 / 12.4 | 168 / 1.6 | 541 / 0.5 | fall mid |
| left_hip_roll servo case screws | 6 | roll_motor_bottom, roll_motor_top | 3.0 | 283 | 36 / 7.8 | 39 / 7.3 | 217 / 1.3 | 713 / 0.4 | fall mid |
| left_hip_pitch servo case screws | 5 | left_roll_to_pitch | 3.1 | 288 | 74 / 3.9 | 116 / 2.5 | 314 / 0.9 | 995 / 0.3 | fall soft, fall mid |
| left_knee servo case screws | 4 | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet | 2.0 | 188 | 92 / 2.1 | 99 / 1.9 | 159 / 1.2 | 481 / 0.4 | push, fall soft, fall mid |
| left_ankle servo case screws | 4 | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet | 2.0 | 188 | 117 / 1.6 | 125 / 1.5 | 167 / 1.1 | 508 / 0.4 | walk, push, fall soft, fall mid |
| neck_pitch servo case screws | 4 | trunk_top | 3.7 | 345 | 61 / 5.6 | 70 / 4.9 | 662 / 0.5 | 2114 / 0.2 | fall soft, fall mid |
| head_pitch servo case screws | 4 | neck_left_sheet, neck_right_sheet | 1.9 | 174 | 36 / 4.9 | 43 / 4.0 | 583 / 0.3 | 1828 / 0.1 | fall soft, fall mid |
| head_yaw servo case screws | 4 | head_yaw_to_roll | 3.2 | 301 | 17 / 18.0 | 23 / 13.0 | 767 / 0.4 | 3473 / 0.1 | fall soft, fall mid |
| head_roll servo case screws | 4 | head_roll_mount | 1.0 | 94 | 16 / 6.1 | 23 / 4.2 | 1106 / 0.1 | 3527 / 0.0 | fall soft, fall mid |
| right_hip_yaw servo case screws | 8 | trunk_top | 2.8 | 264 | 25 / 10.7 | 21 / 12.8 | 365 / 0.7 | 1206 / 0.2 | fall soft, fall mid |
| right_hip_roll servo case screws | 6 | roll_motor_bottom, roll_motor_top | 3.0 | 283 | 51 / 5.5 | 42 / 6.8 | 261 / 1.1 | 871 / 0.3 | fall soft, fall mid |
| right_hip_pitch servo case screws | 5 | right_roll_to_pitch | 3.0 | 283 | 84 / 3.4 | 92 / 3.1 | 689 / 0.4 | 2246 / 0.1 | fall soft, fall mid |
| right_knee servo case screws | 4 | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet | 2.0 | 188 | 64 / 3.0 | 167 / 1.1 | 248 / 0.8 | 1599 / 0.1 | push, fall soft, fall mid |
| right_ankle servo case screws | 4 | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet | 2.0 | 188 | 61 / 3.1 | 174 / 1.1 | 200 / 0.9 | 775 / 0.2 | push, fall soft, fall mid |

Shear only (bearing of the shank on the PLA hole). Screw tension at the horn groups stays under 25 N walking and push in model A (axial force in full on one group) against a pull-through capacity of 395 to 705 N; model B (each horn group also takes half the bending moment as a group moment, a stiff-plate bound) gives up to 200 N walking and 280 N push at the hip pitch horns, still over 2. Case screw pull (along the screw axis) is at most 32 N walking and 55 N push.

### 3.2 Inserts and self-tapping screws

| Joint | n | Load path | Walk per insert or screw N (pull / shear) | Push N | Fall soft N | Fall mid N | Capacity N | SF walk / push / soft / mid | Under the margin |
|---|---|---|---|---|---|---|---|---|---|
| leg_spacer inserts (shin, from the FEA tie forces; both ends summed) | 4 per spacer | the spacer ties the two knee sheets | 15 / 15 | 16 / 22 | 189 / 184 (worst of all fall levels) | (in the soft column) | pull 1354 to 1552, sideways 618 to 1235 | 90 / 85 / 7.2 (pull), 3.4 (side) | none |
| head_roll_mount to head (M3x6, 4.1 mm in the insert, BELOW RULE in FASTENERS.md) | 4 | head roll drive horn share through the servo case and head_roll_mount (RBE3 over the 4 screws) | 7 / 4 | 14 / 4 | 229 / 139 | 694 / 468 | pull 1354, sideways 618 | 190 / 94 / 5.9 / 1.95 (pull); 4.4 / 1.3 (side) | none (hard level: pull 1.15, side 0.76) |
| trunk_top to trunk_bottom (M3x12) | 2 | upper bound: both hip yaw 6804 bearing loads through these 2 screws | - / 53 | - / 50 | - / 313 | - / 1035 | sideways 618 to 1235 | 11.7 / 12.4 / 2.0 / 0.6 | fall mid (bound) |
| foot_side to foot_top (M3x10) | 2 | the ankle idle horn share (foot_side carries the idle horn) | - / 36 | - / 41 | - / 83 | - / 259 | sideways 618 to 1235 | 17 / 15 / 7.4 / 2.4 | none |

Self-tapping screws in printed pilots (inertial pull of the part they hold; walking accelerations are 1 to 3 g and give under 2 N per screw; falls use the worst head and trunk accelerations of the 10 falls: soft 71 g head, 45 g trunk; mid 196 g head, 128 g trunk):

| Screws | Holds (mass) | Engagement mm | Strip capacity N (12.7 to 27.2 MPa shear) | Fall soft N / SF | Fall mid N / SF |
|---|---|---|---|---|---|
| 4 x M2.5x10, battery_pack_lid to body_back | 2 P30B, holder, BMS (122 g) | 5.1 | 305 to 654 | 13 / 23 | 38 / 8.0 |
| 4 x M2.5x6, speaker_stand to head | speaker, interface, stand (38.8 g) | 3.0 | 180 to 385 | 7 / 27 | 19 / 9.7 |
| 4 x M2.5x5, speaker_interface to speaker_stand | speaker and interface (31.1 g) | 2.8 | 168 to 359 | 5 / 31 | 15 / 11 |
| 4 x M2.5x8, eye with two 0.3 mm washers | eye, glass, bulb, LED (9.0 g, right eye) | 2.4 | 144 to 308 | 2 / 92 | 4.3 / 33 |
| 4 x M2.5x6, Pi Zero 2 W to head | Pi, header, card (12.6 g) | 4.6 | 275 to 590 | 2 / 126 | 6.1 / 45 |
| 4 x M2.5x6, adapter to trunk_top | adapter (16 g) | 4.4 | 263 to 563 | 2 / 149 | 5.0 / 52 |
| 1 x M2.5x6, charger to body_back | charger (8.5 g) | 3.9 | 233 to 500 | 4 / 62 | 11 / 22 |
| 4 x M2x4, camera to head | Camera Module 3 (4 g, UNVERIFIED mass) | 3.0 | 144 to 308 | 1 / 207 | 1.9 / 75 |

Masses from sim/mass_budget.py [L]. The battery is the one that matters: in a forward fall its 122 g pulls on the lid screws; in a backward fall the lid is pressed against the floor instead.

## 4. Fatigue

Load cycles: the gait period is 0.54 s, so each leg sees **6667 load cycles per hour** of walking, **666,700 in 100 hours**. The rainflow count of the stress history at each weak spot (ASTM E1049, st_loads.rainflow; walking cases and seeds of section 1, 250 Hz) has 2 to 5 cycles per gait cycle (heel strike, double support, swing).

Fatigue data, two bounds (no mean S-N curve for this filament and these settings was found: BLOCKER):
- **Lower bound, the design curve** of [I] Ezeh & Susmel 2018 for 3D-printed PLA, probability of survival over 95 %: negative inverse slope k = 5.5, endurance limit at 2e6 cycles = 10 % of the static strength, with the maximum stress of each cycle as the reference stress (their mean stress rule). Static strength: 47.1 MPa in-plane, 22 MPa across the layers. Miner sum over the rainflow cycles.
- **Upper bound, best-case print data**: rotating bending of FFF PLA with the best parameter set of [I] Gomez-Gras et al. 2018, Mater. Des. 140:278-285, doi 10.1016/j.matdes.2017.11.072 (search text): 35.8 MPa "can be considered as a lower threshold of the endurance limit for this kind of specimens" (stress amplitude, fully reversed, so also the cycle maximum; in-plane).

<!-- FATIGUE_TABLE -->
| FEA study | walk case | max von Mises MPa | max interlayer tension MPa | max interlayer shear MPa | largest von Mises amplitude MPa | life h, design curve (P_s 95 %) | limit | under 100 h (design curve) | best case: cycle maximum under 35.8 MPa in-plane and 16.7 MPa across the layers (ratio) |
|---|---|---|---|---|---|---|---|---|---|
| roll_to_pitch | walk_forward_0.15 | 23.65 | 2.06 | 13.45 | 11.81 | 0.0414 | interlayer shear | yes | yes (1.24) |
| roll_to_pitch | turn_1.0 | 12.66 | 2.52 | 7.23 | 6.29 | 0.652 | interlayer shear | yes | yes (2.31) |
| roll_to_pitch | walk_side_0.2 | 24.29 | 2.01 | 13.76 | 12.11 | 0.114 | interlayer shear | yes | yes (1.22) |
| roll_to_pitch | walk_backlash | 19.04 | 2.20 | 10.80 | 9.51 | 0.258 | interlayer shear | yes | yes (1.55) |
| shin_segment | walk_forward_0.15 | 14.99 | 0.58 | - | 7.49 | 0.395 | in-plane (von Mises) | yes | yes (2.39) |
| shin_segment | turn_1.0 | 25.11 | 1.08 | - | 12.56 | 0.0539 | in-plane (von Mises) | yes | yes (1.43) |
| shin_segment | walk_side_0.2 | 30.13 | 1.24 | - | 15.04 | 0.0201 | in-plane (von Mises) | yes | yes (1.19) |
| shin_segment | walk_backlash | 15.35 | 0.46 | - | 7.67 | 0.497 | in-plane (von Mises) | yes | yes (2.33) |
| thigh_segment | walk_forward_0.15 | 12.84 | 0.75 | - | 6.39 | 2.37 | in-plane (von Mises) | yes | yes (2.79) |
| thigh_segment | turn_1.0 | 9.28 | 1.14 | - | 4.63 | 11 | in-plane (von Mises) | yes | yes (3.86) |
| thigh_segment | walk_side_0.2 | 17.44 | 0.69 | - | 8.70 | 4.32 | in-plane (von Mises) | yes | yes (2.05) |
| thigh_segment | walk_backlash | 11.76 | 0.56 | - | 5.86 | 10.2 | in-plane (von Mises) | yes | yes (3.04) |
| hip_roll_stage | walk_forward_0.15 | 1.67 | 0.10 | - | 0.82 | 1.9e+05 | in-plane (von Mises) | no | yes (21.43) |
| hip_roll_stage | turn_1.0 | 1.23 | 0.10 | - | 0.60 | 1.69e+06 | in-plane (von Mises) | no | yes (29.06) |
| hip_roll_stage | walk_side_0.2 | 2.95 | 0.08 | - | 1.47 | 4.6e+04 | in-plane (von Mises) | no | yes (12.14) |
| hip_roll_stage | walk_backlash | 1.53 | 0.09 | - | 0.75 | 1.92e+06 | in-plane (von Mises) | no | yes (23.36) |
| foot | walk_forward_0.15 | 2.75 | 1.07 | 1.47 | 1.37 | 1.83e+03 | interlayer shear | no | yes (11.38) |
| foot | turn_1.0 | 5.29 | 0.83 | 2.88 | 2.64 | 145 | interlayer shear | no | yes (5.81) |
| foot | walk_side_0.2 | 7.07 | 1.66 | 3.85 | 3.53 | 49.7 | interlayer shear | yes | yes (4.34) |
| foot | walk_backlash | 2.99 | 1.14 | 1.58 | 1.49 | 892 | interlayer shear | no | yes (10.61) |
| neck_sheets | walk_forward_0.15 | 5.55 | 0.93 | - | 2.76 | 204 | in-plane (von Mises) | no | yes (6.46) |
| neck_sheets | turn_1.0 | 8.73 | 1.37 | - | 4.36 | 27.8 | in-plane (von Mises) | yes | yes (4.10) |
| neck_sheets | walk_side_0.2 | 4.01 | 0.64 | - | 2.00 | 1.15e+03 | in-plane (von Mises) | no | yes (8.93) |
| neck_sheets | walk_backlash | 4.29 | 0.73 | - | 2.10 | 659 | in-plane (von Mises) | no | yes (8.35) |
| head_roll_mount | walk_forward_0.15 | 0.30 | 0.40 | - | 0.14 | 2.81e+06 | interlayer tension | no | yes (42.06) |
| head_roll_mount | turn_1.0 | 0.26 | 0.34 | - | 0.12 | 8.55e+06 | interlayer tension | no | yes (49.70) |
| head_roll_mount | walk_side_0.2 | 0.29 | 0.37 | - | 0.14 | 5.03e+06 | interlayer tension | no | yes (44.70) |
| head_roll_mount | walk_backlash | 0.35 | 0.44 | - | 0.17 | 1.08e+06 | interlayer tension | no | yes (37.90) |
<!-- /FATIGUE_TABLE -->

Reading (mesh level 1, the stress history at each study's walking weak spot; every row uses von Mises and interlayer tension, and the roll_to_pitch and foot rows also their interlayer shear history (the runs made after that history was added); the shear is a magnitude, so a reversal counts as two cycles, which is conservative):
- **Design curve:** for the 666,700 cycles of 100 hours it allows a cycle maximum of 5.8 MPa in-plane and 2.7 MPa across the layers (10 % of 47.1 and 22 MPa at 2e6 cycles, slope 5.5). roll_to_pitch (0.04 to 0.7 h), the knee sheet eye of the shin (0.02 to 0.5 h), the thigh sheet (2 to 11 h), foot_top (50 h in the side step, 145 h or more in the other walks) and the neck sheets (28 h in the turn, 200 h or more in the other walks) do not last 100 hours of walking on it; the hip roll stage and head_roll_mount last over 10,000 hours.
- **Best-case data:** every weak spot stays under the 35.8 MPa threshold (cycle maximum against the threshold, as in the maximum-stress rule of the design curve; across the layers the threshold is scaled by 22 / 47.1 to 16.7 MPa, ASSUMPTION). The least room: the knee sheet eye in the side step (30.1 MPa, ratio 1.19) and roll_to_pitch in the side step (13.8 MPa of interlayer shear, ratio 1.22). The largest von Mises amplitude is 15 MPa (the knee sheet eye).
- The two bounds bracket the life from minutes to no failure, so the life is not known: **BLOCKER**, to be closed by a bench fatigue test of a printed knee sheet and roll_to_pitch (P7). No upstream issue reports these parts breaking on 2.1 kg builds with the same servos (UPSTREAM_ISSUES.md: only a neck part, G5, and an unnamed head part, G6), which points to the upper side for the cool parts; our build's walking peaks are 19 % higher (section 1.2) and heat (section 5) moves it down.

## 5. Hot case (thermal twin coupling)

Input from twin/thermal/THERMAL_TWIN.md (central set, sim pass only): the eight knee-to-ankle sheets reach 54 to 66 C in continuous and 50/50 walking and 47 to 55 C at 25/75; trunk_top and roll_to_pitch up to 61 C; the belly floor under the BEC and the battery_pack_lid at the Pololu 2815 and BMS above 50 C. PLA heat deflection temperature 49 to 57 C, glass transition 55 to 60 C (that doc's [P1] to [P3]); Overture Easy PLA publishes only Vicat 66.2 C [P5].

Retention of printed PLA properties against room temperature (cited):

| Temperature | Strength | Modulus | Source |
|---|---|---|---|
| up to 40 C | about 1.0 (stiffness held) | about 1.0 | [I] Grasso et al. 2018, Rapid Prototyping J. 24(8):1337-1346, doi 10.1108/RPJ-04-2017-0055 (search text: stiffness held below 40 C) |
| 50 C | **0.62** (compression stress about 80, 60 and 50 MPa at 25, 37 and 50 C) | **0.84** (about 16 % down from 40 to 50 C, printed PLA) | strength: [I] Slavkovic et al. 2024, Polymers 16(11):1526, doi 10.3390/polym16111526 (search text; DMTA Tg 65 C); modulus: Grasso et al. 2018 (search text) |
| 60 C | **BLOCKER** (no tensile or compression strength at 60 C found for printed PLA) | **0.25** (about 1400 MPa at 30 C, 350 MPa at 60 C) | modulus: Grasso et al. 2018 as cited in a search result (not read in full) |
| 65 C and over | BLOCKER | BLOCKER (at and above Tg the modulus drops by orders of magnitude) | thermal twin [P1] to [P3] |

What it does to the verdicts (the linear FEA stresses come from forces, so a uniform modulus loss leaves them unchanged; the SF scale with the strength, the deflections with 1 / modulus):

| Part | Temperature (thermal twin) | SF walk / push at room T | at 50 C | at 60 C | Deflection under the same load |
|---|---|---|---|---|---|
| knee_to_ankle_left_sheet of the shin (knee horn eye; level 2) | 54 to 66 C | 1.63 / 1.07 | **1.02 / 0.67** | BLOCKER (strength), under 1.02 | x 1.2 at 50 C, x 4 at 60 C |
| roll_to_pitch ear wall (levels 1 to 3) | up to 61 C | 1.48 to 1.63 / 1.08 to 1.21 (Z 22 MPa); 1.48 to 1.83 / 1.08 to 1.25 (Z 39.4) | **0.93 to 1.02 / 0.68 to 0.76**; 0.93 to 1.14 / 0.68 to 0.78 | BLOCKER | x 1.2, x 4 |
| knee_to_ankle_left_sheet of the thigh (hip pitch horn eye; level 1) | 54 to 66 C | 2.70 / 1.74 | 1.69 / 1.09 | BLOCKER | x 1.2, x 4 |
| hip roll stage (roll_motor_top and bottom; level 1) | not listed by the thermal twin | 12.9 / 9.6 | - | - | - |

Creep under the standing load (the robot stands most of a 25/75 session): the stress held at each weak spot while standing, from the same FEA (stand case, nominal and 3 seeds): knee sheet eye of the shin 4.3 MPa (von Mises), roll_to_pitch ear wall 3.4 MPa (von Mises; 1.9 MPa of interlayer shear, and the layers there are in compression while standing), the thigh sheet 1.0 MPa, foot_top and the hip roll stage 0.3 and 0.6 MPa, the neck sheets 0.3 MPa, head_roll_mount 0.1 MPa (mesh level 1, 1 mm averages at each walking weak spot, the largest over the 4 standing runs). The heat deflection test bends a bar at 0.45 MPa or 1.8 MPa and records the temperature where it moves 0.25 mm (ASTM D648); the knee sheets and roll_to_pitch hold 2 to 10 x those stresses at temperatures at or above their HDT. So **creep is expected at the knee sheets and roll_to_pitch above about 50 C**: the horn screws lose their clamp, the knee and ankle cases loosen in the sheets (the thermal twin's finding 1 says the same). The creep rate is a **BLOCKER**: no creep data for this filament; the printed-PLA creep studies found (Part I of the ScienceDirect 2023 creep study of printed PLA by build and raster direction; the 2025 heat-treatment creep study; the 2022 short-term creep study of AM polymers, all search text) show that temperature and load dominate but give no number usable here.

PETG check (the verdicts change, so the option is checked): Bambu PETG HF TDS V1.0 [I] (search text; copy at botland.com.pl, the thermal twin's [P6]): tensile 34 +- 4 MPa X-Y and 23 +- 4 MPa Z, modulus 1810 MPa X-Y, HDT 69 C at 0.45 MPa and 62 C at 1.8 MPa, Tg 66 C. At room temperature PETG is weaker than this PLA in-plane (34 against 47.1 MPa) and about equal across the layers (23 against the 22 MPa design value); its advantage is that it keeps those values to about 60 C (ASSUMPTION: under its 1.8 MPa HDT of 62 C; no PETG hot strength data found, BLOCKER for an exact value).

| Part | PLA room T (walk / push) | PLA 50 C | PETG to about 60 C (ASSUMPTION) |
|---|---|---|---|
| knee sheet eye of the shin (in-plane; level 2) | 1.63 / 1.07 | 1.02 / 0.67 | 1.18 / 0.77 |
| roll_to_pitch ear wall (levels 1 to 3) | 1.48 to 1.63 / 1.08 to 1.21 | 0.93 to 1.02 / 0.68 to 0.76 | 1.07 to 1.32 / 0.78 to 0.90 |
| knee sheet eye of the thigh (in-plane; level 1) | 2.70 / 1.74 | 1.69 / 1.09 | 1.95 / 1.26 |

PETG SF: the failure index of section 2.2 with X 34, Z 23 and S 23 MPa, over the whole part (the weak spot can move; for an in-plane weak spot it is the PLA SF x 34 / 47.1).

So PETG does not bring the two weak parts to the walking margin of 2; it only stops the loss with temperature (and at 66 C it is at its own Tg). It turns the hot walking verdicts from about 1.0 back to about 1.1 to 1.3, and in push from about 0.7 to about 0.8. Stiffness: PETG is 0.69 x as stiff as PLA (1810 against 2641 MPa), so the same loads bend the sheets 1.46 x more. Mass: PETG 1.27 g/cm3 (PrusaSlicer Generic PETG, /usr/share/PrusaSlicer/profiles/PrusaResearch.ini line 7810 [L]) against 1.20 g/cm3: +5.8 % on those parts (knee sheets +3.0 g for all 8, roll_to_pitch +2.3 g for both). PETG also needs its own print settings and coupon tests (no PETG profile in print/config/).

## 6. Weak list and proposals (none decided)

Weak list (room temperature unless stated; lab margin 2 walking and push, 1.2 falls; the FEA mesh level is stated where it matters):

| # | Part or joint | Case under the margin | SF | Why |
|---|---|---|---|---|
| W1 | roll_to_pitch, both legs (D22 light, 2 walls 15 %) | walking, push, falls | walk 1.48 to 1.63, push 1.08 to 1.21 (mesh levels 1 to 3; the maker Z raises only level 1, to 1.83 / 1.25); soft falls: 7 to 8 of 10 under 1.2 (worst 0.42 to 0.48); at 50 C walk 0.93 to 1.02 | the side wall between the two hip roll horn ears, bent by the idle-horn force (90 N walking, 130 N push). At level 1 the shear across its layers governs (the wall is printed upright, print z = link y); at levels 2 and 3 the in-plane stress in the skin at the ends of the wall |
| W2 | knee_to_ankle_left_sheet of the shin (the plate on the knee drive horn; both legs) | walking, push, side falls | walk 1.63, push 1.07 (level 2; level 1: 1.56 / 1.04); soft falls: 2 of 10 under 1.2 (1.06, a side fall and a rough terrain fall), 0 to 3 with the averaging radius; at 50 C walk 1.02 | the eye round the knee horn: 2.5 to 3 mm of plastic between a horn screw hole and the eye edge, and the neck where the eye joins the plate; the knee torque (4.4 N m walking, 6.9 to 8.6 N m push) gives about 80 % of the stress |
| W3 | the knee sheets and roll_to_pitch, hot | walking at 54 to 66 C (sheets) and up to 61 C (roll_to_pitch) | about 1.0 walking at 50 C (W1 0.93 to 1.02, W2 1.02), 0.67 to 0.76 in push; BLOCKER at 60 C | strength 0.62 at 50 C (cited); the standing stress (3.4 to 4.3 MPa) is 2 to 10 x the HDT test stress, so creep: the horn and case screws lose their clamp |
| W4 | the same sheet on the thigh (knee_to_ankle_left_sheet at the hip pitch drive horn) | push, falls | walk 2.70, push 1.74 (level 1); soft falls: 4 of 10 under 1.2 (worst 0.73); at 50 C 1.69 / 1.09 | the same eye, loaded by the hip pitch torque and bending |
| W5 | knee and ankle servo case screws (M2 through the 2.0 mm sheets) | walking (left ankle), push (knee, ankle) | walk 1.6, push 1.1 to 1.9 | PLA bearing of a 2 mm screw in a 2 mm plate; the split over the screws ignores the pocket, which also holds the servo, so this is an upper bound |
| W6 | knee drive horn screws (M3 through the sheet eye) | push | 1.2 to 1.6 | the knee torque spikes in push recovery (6.9 to 8.6 N m) |
| W7 | the neck sheets, head_roll_mount, the neck and head horn and case screws, the trunk frame inserts | falls | neck sheets: soft 9 of 10 under 1.2 (worst 0.41); head_roll_mount: 5 of 10 (0.79); most neck and head horn and case screws under 1.2 at soft (Table 5); trunk_top to trunk_bottom M3x12 0.6 at mid (an upper bound) | the head inertia: 15 to 71 g at soft, 54 to 196 g at mid; the rigid model is an upper bound at mid |
| W8 | the trunk and head shells (D22 2-wall body, 4-wall head) | falls on a hard floor | hand calc: 31 to 115 MPa (body) and 25 to 90 MPa (head) for 400 to 900 N on a wall; 102 to 359 MPa for 1300 to 2800 N; strength 47.1 MPa | a hit in the middle of a wall bends it (Roark Table 11.2 case 16: clamped circular plate, free span 30 mm, load radius 5 to 10 mm, solid 3.0 and 3.4 mm walls as the lower bound; a curved shell carries part of it by membrane action, and at 900 N the deflection is 0.8 of the thickness, so these are bounds, not FEA) |

Proposals (none decided; FEA pass only; grams and hours from PrusaSlicer 2.7.2 with the lab configs, st_slice_proposals.py):

| # | Proposal | For | Effect | Mass | Print time | Notes |
|---|---|---|---|---|---|---|
| P1 | roll_to_pitch back to 3 walls 15 % (its profile before D22, the parts.csv heavy column, which PRINT_PLAN step 2 check 6 already allows after a crack) | W1 | walk 1.84, push 1.25 at level 1 (against 1.60 / 1.11); soft falls 5 of 10 under 1.2; at 50 C 1.15 / 0.78 | +3.6 g per part, +7.2 g both legs | +0.22 h per part, +0.44 h | the cheapest gain. 4 walls 40 % (1.87 / 1.28, +18.9 g, +1.68 h) and 6 walls 40 % (1.90 / 1.29, +27.7 g, +1.84 h) add little. Other orientations are worse (+x up 1.00 / 0.78, +y up 1.10 / 0.79, with 6 to 8 g of support per part instead of 1.3 g): keep -z up |
| P2 | CAD: a thicker and wider knee sheet eye (knee_to_ankle_left_sheet; the hip pitch eye of the thigh is the same part); the same idea for the roll_to_pitch ear wall (not scaled here) | W2, W4, W6 | not modelled. Scaling the level 1 split at the weak spot (80 % in-plane from the knee torque, going with 1 / t; the rest out of plane, 1 / t^2): an eye about 4.2 to 4.6 mm thick (now 3.6) reaches 2 walking, about 6 mm reaches 2 in push. Needs its own FEA | about +0.5 to +1 g per sheet (ASSUMPTION until the CAD exists) | about +0.1 h per sheet | longer horn screws (M3x8 for M3x6) and a check of the spacer and horn fit: for the CAD owner |
| P3 | knee sheets 5 walls 40 % (all 8, as a stopgap without CAD) | W2, W4 | walk 1.82, push 1.20 (level 1, shin); at 50 C 1.14 / 0.75 | +9.4 g | +1.08 h | does not reach 2; the weak spot moves to the bottom skin by the horn screws |
| P4 | knee and ankle case screws: no change, look | W5 | the bearing load is an upper bound | 0 | 0 | after the bench check (P7) and after the first hours of walking, look for oval case screw holes in the sheets |
| P5 | PETG for the knee sheets and roll_to_pitch, only if the thermal guard cannot keep them under about 50 C | W3 | walk / push about 1.18 / 0.77 (knee sheet) and 1.07 to 1.32 / 0.78 to 0.90 (roll_to_pitch) up to about 60 C (ASSUMPTION) | +3.0 g (8 sheets), +2.3 g (both roll_to_pitch) | needs a PETG profile and coupons first (none in print/config/) | weaker than this PLA at room temperature in-plane (34 against 47.1 MPa); 1.46 x the deflection |
| P6 | first walks on a soft floor (foam mat or carpet) with a tether; spare roll_to_pitch parts | W1, W7, W8 | a mat is below the "soft" contact level of section 1.3 | spares: both roll_to_pitch, 42.5 g with supports (49.6 g with P1; the right part is the mirror, sliced as the left) | 4.2 h (4.6 h with P1) | parts.csv already has a spare of each knee sheet |
| P7 | bench checks before the right leg prints (proposed PRINT_PLAN step 2 check 7) | W1, W2, the fatigue BLOCKER | static proof loads at the push peaks: the spare knee sheet eye at 8.6 N m, a spare roll_to_pitch (P6) at 130 N on the idle horn ear. Fatigue needs a rig (a crank turning a spare horn through a spring to 4.4 N m at 1 to 2 Hz for 20,000 cycles): not in the lab; until then the inspection schedule of the first walks (proposed TEST_PLAN 9.0) | 0 | 0 (the spare sheet is in parts.csv; the spare roll_to_pitch is P6) | weights: 4.4 kg on a 200 mm lever (8.6 N m), 13.3 kg (130 N). The servo cannot load it: its limit is about 3.2 N m |
| P8 | for the sim owner: the solver iterations (1 against 2 or more) change the push result | sim | section 1.1 and section 7 | - | - | proposed text for sim/ADDED_MASS_SIM.md in the lead report |

FEA of the print changes (same loads and supports as the baseline, mesh level 1; compare with the baseline at level 1, 1.60 / 1.11 and 1.56 / 1.04, which moved by under 10 % with the mesh, section 2.4; generated):

<!-- PROPOSALS_FEA_TABLE -->
| change (same loads and supports) | SF walk | SF push | falls soft: worst (under 1.2 of 10) | falls mid | weak spot (link frame) | SF walk / push at 50 C | design-curve life h (worst walking case) | grams and print hours, both legs (PrusaSlicer 2.7.2) |
|---|---|---|---|---|---|---|---|---|
| roll_to_pitch printed with +x up (hip roll axis vertical) | 1.00 | 0.78 | 0.41 (7 of 10) | 0.10 (10 of 10) | left_roll_to_pitch, wall, interlayer at [31.8, -13.6, 18.5] mm | 0.63 / 0.48 | 0.00903 | +0.5 g, +1.20 h (support 8.2 g per part instead of 1.3 g) |
| roll_to_pitch printed with +y up (the wall between the horn ears flat) | 1.10 | 0.79 | 0.22 (9 of 10) | 0.07 (10 of 10) | left_roll_to_pitch, wall, interlayer at [24.7, -14.7, 36.4] mm | 0.69 / 0.49 | 0.0138 | +0.7 g, +1.21 h (support 6.2 g per part instead of 1.3 g) |
| roll_to_pitch 3 walls 15 % (its profile before D22) | 1.84 | 1.25 | 0.60 (5 of 10) | 0.15 (10 of 10) | left_roll_to_pitch, wall, interlayer at [28.6, -2.2, 21.1] mm | 1.15 / 0.78 | 0.402 | +7.2 g, +0.44 h |
| roll_to_pitch 4 walls 40 % | 1.87 | 1.28 | 0.63 (4 of 10) | 0.17 (10 of 10) | left_roll_to_pitch, wall, interlayer at [28.6, -2.2, 21.1] mm | 1.17 / 0.80 | 0.273 | +18.9 g, +1.68 h |
| roll_to_pitch 6 walls 40 % (the 5 mm walls print solid) | 1.90 | 1.29 | 0.63 (5 of 10) | 0.17 (10 of 10) | left_roll_to_pitch, wall, interlayer at [28.6, -2.2, 21.1] mm | 1.19 / 0.81 | 0.26 | +27.7 g, +1.84 h |
| knee sheets 5 walls 40 % (all 8) | 1.82 | 1.20 | 1.11 (1 of 10) | 0.36 (6 of 10) | knee_to_ankle_left_sheet, bottom skin, in-plane at [10.3, 0.1, -3.7] mm | 1.14 / 0.75 | 0.0562 | +9.4 g, +1.08 h |
<!-- /PROPOSALS_FEA_TABLE -->

What the print profile can do here: roll_to_pitch gains 15 % from 2 to 3 walls and almost nothing after that, because the stress sits in the wall itself and 3 walls already make its outer 1.27 mm solid; the knee sheet gains 17 % from 3 to 5 walls 40 %. The orientation of roll_to_pitch is not a lever (both other orientations put the layers across the bending stress of the ear wall). The lever left for both parts is the CAD (P2 and the roll_to_pitch ear wall).

## 7. Limits, ASSUMPTIONS and BLOCKERS

- **Sim pass only.** Loads come from MuJoCo with the BAM servo model (no gear friction beyond the model, upstream issue 48), the stock policy and our mass model (sim/MASS_BUDGET.md: about 40 g uncertain, uniform density per part). Real servos may track worse; the knee torques are set by the servo limit and the armature, which the model has.
- **Solver setting changes the push answer.** With the upstream 1 Newton iteration the 15 N pushes never topple our build; with 2 or more iterations they always do (4 of 4 at the 4th or 5th push) and single pushes from 15 N sideways or 12 N fore-aft topple 1 to 4 of 8 phases. This study uses the converged setting; the sim owner should look at it (proposed text in the lead report).
- **Contact stiffness of falls is not known:** stated as a range (section 1.3). The rigid-body model overstates the joint loads of a hard hit (no part compliance between the hit and the joints).
- **FEA pass only, linear elastic,** small strain, no contact (bonded ties), no preload, no plasticity: peak stresses at notches are linear peaks. Supports are a rigid bonded servo case; real cases flex and the pocket fit (0.00 to 0.10 mm) is not modelled.
- **Zones are geometric,** from the distance to the surface and the face normal, not from the G-code; walls and skins of the slicer may differ near small features.
- **Mesh:** the screening is at mesh level 1, whose elements (about 3 mm) are coarser than the 0.86 mm walls of the 2-wall parts. roll_to_pitch (levels 1 to 3) and the shin (levels 1 and 2, the knee sheet alone to level 3) moved by under 10 % (section 2.4); the other parts were run at level 1 only and carry that uncertainty. foot_top was meshed from its STL with the edges under 0.01 mm collapsed (volume -0.004 %).
- **Strengths:** X 47.1 MPa and E 2641 MPa are maker values for 100 % infill bars (search text); Z is the conservative 22 MPa (with the maker Z 39.4 MPa roll_to_pitch rises from 1.60 to 1.83 walking at level 1; at levels 2 and 3 its weak spot is in-plane and the Z value no longer sets it); S = Z is an ASSUMPTION; bearing = tensile strength is an ASSUMPTION. ASSUMPTION ranges: nu 0.30 to 0.40; restitution 0.3 to 0.7; insert sideways capacity 618 to 1235 N; self-tapping strip shear 12.7 to 27.2 MPa.
- **Fatigue:** the cited design curve (P_s 95 %) with the 22 MPa interlayer reference compounds two conservative choices, and the best-case bound is for other print settings in rotating bending; mean S-N data for this filament and these print settings: BLOCKER. The stress histories are at mesh level 1.
- **Hot properties:** strength at 60 C and above, creep rates, and PETG hot strength: BLOCKER (section 5).
- **BLOCKERS:** STS3215 horn alloy (thread check of the M3 horn screws); pull-out of the M2 case screws from the PA+GF pilots; pull-out data for M2 and M2.5 self-tapping screws in printed PLA pilots; insert sideways strength; PLA strength at 60 to 66 C; PLA and PETG creep at 50 to 65 C; mean fatigue curve; the real floor of the first walks.
- **Not modelled:** the trunk shells, the head shell and the caches as hit parts (their contact stiffness is a hand calc), the neck chain parts other than the neck sheets and head_roll_mount, the antenna holders, the TPU sole; the right leg (mirror loads, same parts; the right knee peaks are in the load table).

## 8. Sources

Lab and upstream [L], [U]: sim/added_mass_sim.py, sim/current_budget.py, sim/mass_budget.py (all imported unchanged), sim/ADDED_MASS_SIM.md, sim/MASS_BUDGET.md, print/MASS_STUDY.md, print/PRINT_PLAN.md, print/parts.csv, print/config/*.ini, print/slice.py (imported unchanged), fasteners/fasteners.json and FASTENERS.md, MOUNTING.md, audit/sites.json, DECISIONS.md D18 to D22, twin/thermal/THERMAL_TWIN.md, mini_bdx/robots/open_duck_mini_v2/robot.urdf (b23317a), print/*.stl (730c14b), Open_Duck_Playground b9be205 (MJCF, MjInfer, reference motion, gait period 0.54 s), /usr/share/PrusaSlicer/profiles/PrusaResearch.ini (Generic PETG 1.27 g/cm3).

Internet [I] (search result text unless noted; the hosts could not be opened from this session):
- Overture PLA TDS v5.1 (Young's modulus 2641 +- 328 MPa, tensile 47.1 +- 1.2 MPa X-Y, 100 % infill, 0.4 mm nozzle): https://wiki.overture3d.com/pla_tds.pdf ; Overture Easy PLA values extracted from the maker TDS (tensile 44.3 MPa X-Y, 39.4 MPa Z, modulus 2650 MPa): https://3dfilamentprofiles.com/filament/details/7100
- Ezeh O.H., Susmel L. (2018), On the fatigue strength of 3D-printed polylactide (PLA), Procedia Structural Integrity 9: 29-36, doi 10.1016/j.prostr.2018.06.007 (design curve for P_s over 95 %: negative inverse slope 5.5, endurance limit at 2e6 cycles 10 % of the UTS, maximum stress of the cycle as the reference stress): https://www.sciencedirect.com/science/article/pii/S2452321618300076
- Ezeh O.H., Susmel L. (2020), On the notch fatigue strength of additively manufactured polylactide (PLA), International Journal of Fatigue 136: 105583, doi 10.1016/j.ijfatigue.2020.105583 (printed PLA treated as linear elastic, isotropic and homogeneous; Theory of Critical Distances for notches; no material length for this filament): https://eprints.whiterose.ac.uk/158161/
- Gomez-Gras G., Jerez-Mesa R., Travieso-Rodriguez J.A., Lluma-Fuentes J. (2018), Fatigue performance of fused filament fabrication PLA specimens, Materials & Design 140: 278-285, doi 10.1016/j.matdes.2017.11.072 (rotating bending, Taguchi L27 over layer height, fill density, nozzle and speed; "35.8 MPa can be considered as a lower threshold of the endurance limit for this kind of specimens"): https://recercat.cat/handle/2117/113144
- Ezeh O.H., Susmel L. (2019), Reference strength values to design against static and fatigue loading polylactide additively manufactured with in-fill level equal to 100 %, Material Design & Processing Communications 1(2): e45, doi 10.1002/mdp2.45 (conservative static reference 22 MPa): https://onlinelibrary.wiley.com/doi/full/10.1002/mdp2.45
- Gibson L.J., Ashby M.F. (1997), Cellular Solids, 2nd ed., Cambridge University Press (E*/Es = C (rho*/rho_s)^n; open-cell plastic collapse 0.3 (rho*/rho_s)^1.5).
- Doyle et al. (2025), On the Rigidity and Mechanical Behavior of Triply Periodic Minimal Surfaces-Based Lattices, Advanced Engineering Materials, doi 10.1002/adem.202402495 (gyroid n = 2.12): https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/adem.202402495
- Bean P., Lopez-Anido R.A., Vel S. (2022), Numerical Modeling and Experimental Investigation of Effective Elastic Properties of the 3D Printed Gyroid Infill, Applied Sciences 12(4): 2180, doi 10.3390/app12042180 (gyroid nearly isotropic): https://digitalcommons.library.umaine.edu/cie_facpub/8/
- Mechanical Performance of Heat-Set Threaded Inserts in FDM-Printed PLA Components, Engineering Proceedings 157(1): 40 (2026) (M3 inserts in FDM PLA, 3 wall thicknesses x 3 infill patterns, 27 specimens, mean peak pull-out 1353.6 +- 7.5 to 1551.5 +- 20.4 N): https://www.mdpi.com/2673-4591/157/1/40
- CNC Kitchen, Are Our Heat-Set Insert Datasheets Wrong? (M3 inserts in PLA about 1400 N, strength falls between 4.1 and 4.2 mm holes; secondary summaries): https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong
- CNC Kitchen, Threaded Inserts for 3D Prints, Cheap vs Expensive (M3 torque-out about 3.5 N m in PLA; pull-out 181, 157 and 39 kg by insert brand): https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive
- CNC Kitchen, Helicoils vs Threaded Inserts vs Embedded Nuts (direct screw 118 kg, insert 119 kg pull-out; torque-out 1 N m against 3 N m; PETG): https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment
- Searched without a usable number (self-tapping pull-out in printed PLA pilots): Evaluation of the Screw Pull Out Forces of PLA Parts Manufactured by FDM (ResearchGate 373549622, optimum 1993 N, screw size not in the text found); Experimental Comparison of Fastener Implementation Approaches in FDM, Applied Sciences 14(12): 5172, doi 10.3390/app14125172.
- Grasso M., Azzouz L., Ruiz-Hincapie P., Zarrelli M., Ren G. (2018), Effect of temperature on the mechanical properties of 3D-printed PLA tensile specimens, Rapid Prototyping Journal 24(8): 1337-1346, doi 10.1108/RPJ-04-2017-0055: https://www.emerald.com/insight/content/doi/10.1108/rpj-04-2017-0055/full/html
- Slavkovic V. et al. (2024), Thermo-Mechanical Behavior and Strain Rate Sensitivity of 3D-Printed Polylactic Acid (PLA) below Glass Transition Temperature (Tg), Polymers 16(11): 1526, doi 10.3390/polym16111526 (compression at 25, 37, 50 C; DMTA Tg 65 C): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11174730/
- Bambu Lab PETG HF technical data sheet V1.0 (tensile 34 +- 4 MPa X-Y, 23 +- 4 MPa Z, modulus 1810 MPa X-Y, HDT 69 C at 0.45 MPa): https://botland.com.pl/img/art/inne/25540_karta_produktu.pdf
- Printed PLA creep (no usable number here): Numerical and experimental investigation on creep response of 3D printed PLA samples, Part I (ScienceDirect, 2023), https://www.sciencedirect.com/science/article/abs/pii/S1751616123003788 ; Enhancing the creep resistance of 3D-printed PLA at varied operating temperatures by heat treatment (ScienceDirect, 2025), https://www.sciencedirect.com/science/article/abs/pii/S0997753825002475
- Young W.C., Budynas R.G. (2002), Roark's Formulas for Stress and Strain, 7th ed., McGraw-Hill, Table 11.2 case 16 (circular plate, fixed edge, load on a small central circle: centre stress 3W / (2 pi t^2) (1 + nu) ln(a / r0'), with the equivalent radius r0' = sqrt(1.6 r0^2 + t^2) - 0.675 t when r0 < 0.5 t).
- Timoshenko S., Woinowsky-Krieger S. (1959), Theory of Plates and Shells, 2nd ed., McGraw-Hill (clamped circular plate under a central load, w = P a^2 / (16 pi D)).
- ASTM E1049-85, Standard Practices for Cycle Counting in Fatigue Analysis (rainflow); ASTM D648 (deflection temperature under flexural load, 0.455 and 1.82 MPa).
- MuJoCo 3.17 documentation: solver parameters (solref time constant and damping ratio, solimp) and the force and torque sensors: https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters

## 9. Reproduce

```bash
export ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_SCRATCH=<scratch folder>
python3 -m venv --system-site-packages $ODM_SCRATCH/venv && $ODM_SCRATCH/venv/bin/pip install scikit-fem==12.0.2 meshio==5.3.5 tetgen==0.8.4 pyamg==5.4.1
PY=$ODM_SCRATCH/venv/bin/python; cd <repo>
nice -n 10 $PY altaay_lab/twin/structure/st_loads.py check     # solver iterations and time step
nice -n 10 $PY altaay_lab/twin/structure/st_loads.py walk      # about 1 min
nice -n 10 $PY altaay_lab/twin/structure/st_loads.py push; nice -n 10 $PY altaay_lab/twin/structure/st_loads.py push2
nice -n 10 $PY altaay_lab/twin/structure/st_loads.py trained   # the same walks with the trained inertials
nice -n 10 $PY altaay_lab/twin/structure/st_falls.py          # about 10 min
nice -n 10 $PY altaay_lab/twin/structure/st_interfaces.py
for s in shin_segment thigh_segment roll_to_pitch hip_roll_stage foot neck_sheets head_roll_mount \
         roll_to_pitch_upx roll_to_pitch_upy roll_to_pitch_w3 roll_to_pitch_w4i40 roll_to_pitch_w6i40 shin_segment_w5i40; do
  OMP_NUM_THREADS=1 nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py $s 1; done     # 4 to 18 min each on a shared 4-core box
nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py conv roll_to_pitch 1 2 3              # mesh convergence (level 3: the longest run)
nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py conv shin_segment 2
for s in roll_to_pitch shin_segment; do nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py avgcheck $s; done
nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py sheetlocal
python3 altaay_lab/twin/structure/st_slice_proposals.py                                     # PrusaSlicer 2.7.2 grams and hours
$PY altaay_lab/twin/structure/st_finalize.py     # writes tables.md and the generated tables of this file
```
