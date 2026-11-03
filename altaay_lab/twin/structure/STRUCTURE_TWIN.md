# Structure twin: do the printed parts, inserts and screws hold walking, pushes and falls? (sim pass only, FEA pass only)

Written 2026-11-03 by the structure twin sub-agent (Claude Code) for the lead agent, branch claude/digital-twin, folder twin/structure/ only. Nothing was printed, bought, sent, deleted or committed. Loads are **sim pass only** (MuJoCo 3.17.0, stock BEST_WALK_ONNX_2 on our 2652.8 g build with the D22 print profile). Stresses are **FEA pass only** (linear tetrahedra, as-printed zones, room-temperature PLA unless the hot case says otherwise). Times are US Eastern.

Tags: [L] lab file or script on this box; [U] upstream file; [I] internet source. Several hosts could not be opened from this session (eprints.whiterose.ac.uk, www.cnckitchen.com, www.mdpi.com, www.sculpteo.com, wiki.overture3d.com, overture3d.com): those [I] values are **search result text**, marked "(search text)". They need those hosts allowed to be read in full.

## Answer in plain words

- **Walking, the stock policy, flat floor:** two printed parts fall under the lab margin of 2 at the walking peaks (the side step and turn steps), at room temperature:
  - **roll_to_pitch** (both legs, D22 light profile, 2 walls 15 %): SF **0.96** (interlayer design value 22 MPa) to about **1.7** (maker Z value 39.4 MPa). Weak spot: the side wall that joins the two hip roll horn ears, bent by the idle-horn force along the print z axis, so the bending stress pulls the layers apart. Push recovery: 0.66 to 1.2.
  - **knee_to_ankle_left_sheet of the shin** (the plate that takes the knee drive horn; 3 walls, its profile before D22): SF **1.45** (in-plane, 47.1 MPa). Weak spot: the neck between the horn eye and the plate, 3.4 to 3.9 mm thick, driven by the knee torque (6.2 MPa per N m there; walking peak 4.4 N m, push peak 6.9 to 8.6 N m). Push recovery: 0.97.
  - The thigh segment (hip pitch horns to the knee servo) holds 2.3 walking, 1.5 push; the hip roll stage (roll_motor_top and bottom) holds 8.7 to 12.
- **Falls:** with a contact stiffness that a printed shell on a hard floor can have (0.14 to 3.2 MN/m, the "soft" to "mid" levels below), the part that hits sees 400 to 900 N (soft) up to 1300 to 2800 N (mid), the head 15 to 71 g (soft) up to 54 to 196 g (mid). roll_to_pitch fails at the soft level in 9 of 10 falls; the knee sheets in side falls; the neck chain and head mounts carry 100 to 230 N per insert (soft) and 470 to 700 N (mid).
- **Fasteners (PLA side):** walking keeps every horn and case screw over 2 except the **ankle servo case screws** (SF 1.6, PLA bearing in the 2.0 mm sheet). Push recovery drops the knee drive horn screws (1.2 to 1.6) and the knee and ankle case screws (1.1 to 1.9) under 2. Inserts are far from their pull-out data in walking (SF over 80); in falls the head mount inserts hold 5.9 (soft) and 2.0 (mid).
- **Fatigue (cited design curve, P_s 95 %):** the roll_to_pitch side wall and the knee sheet neck would not last 100 hours of walking (6667 load cycles per hour per leg); with that curve they last minutes. Those lives are lower bounds: no upstream issue reports these parts breaking on 2.1 kg builds with the same servos, so the curve and the peak stress are both conservative. The exact life is a BLOCKER until a bench fatigue test (proposal P7).
- **Hot case (thermal twin):** the knee sheets run at 54 to 66 C and roll_to_pitch up to 61 C. At 50 C printed PLA keeps about 0.62 of its strength and 0.84 of its modulus; at 60 C the modulus is about 0.25 and the strength is a BLOCKER. The knee sheet walking SF becomes about 0.9 at 50 C. PETG (HDT 69 C) keeps its lower room-temperature strength (34 MPa X-Y, 23 MPa Z) to about 60 C (ASSUMPTION) and gives SF 1.0 (knee sheet) and 1.0 (roll_to_pitch) at any of these temperatures.
- **Sim finding for the sim owner:** with converged contact forces (2 or more solver iterations instead of the upstream 1), our build falls in every 15 N push run (4 of 4) and in 2 to 4 of 8 single pushes from 15 N sideways, 12 N backward and forward; with the upstream setting it falls in none (sim/ADDED_MASS_SIM.md). The walk itself does not change much (tracking 0.70 to 0.73).
- **Proposals, none decided (section 6):** reprint roll_to_pitch with the hip roll axis vertical (P1), thicken or reinforce the knee sheet eye (P2, CAD) or 5 walls 40 % as a stopgap (P3), a bench load and fatigue check on the coupon session (P7), PETG for the hot parts if the thermal guard is not adopted (P5), a soft floor and tether for first walks (P6).

## Files

| File | What it is |
|---|---|
| STRUCTURE_TWIN.md | This file. |
| tables.md | All tables, written by st_report.py. |
| st_sim.py | Instrumented MuJoCo model of our build (force and torque sensors at all 14 joints, accelerometers at every link centre of mass, optional printed-part collision for falls) and the control loop of sim/added_mass_sim.py with logging, state snapshots and a changeable time step. |
| st_loads.py | Walking, standing and push-recovery runs, solver check, rainflow counting. |
| st_falls.py | Fall runs with the contact stiffness sweep. |
| st_interfaces.py | Joint loads split onto the drive horn, idle horn (or 6804 bearing) and servo case screw groups (fasteners.json positions). |
| st_fea.py | FEA core: TetGen mesh, as-printed zones, materials, RBE3 loads, tied members, AMG solver, failure index in each part's print frame. |
| st_fea_run.py | The FEA studies: unit loads, superposition over every sim sample, weak spot, insert loads, stress histories for fatigue. |
| st_report.py | Load, fall, fastener, fatigue, FEA and hot-case tables. |
| st_finalize.py | Writes tables.md from the scratch outputs (FEA summary with the maker Z, 50 C and PETG columns, mesh convergence). |
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
Every joint's load was carried to the parts at both its ends (st_interfaces.py): the horn ears of the child, the servo case holder of the parent. The FEA was run on every leg and neck stage that carries a joint load from one servo to the next (seven studies: the shin and thigh segments, roll_to_pitch, the hip roll stage, foot_top, the neck sheets and head_roll_mount), and the ranking comes from the FEA (Table 3). The trunk and head shells carry only inertial loads in walking and are judged for falls by a hand calculation (section 6, W8). Hand checks of the two weakest:
- Knee sheet eye neck (shin): in-plane bending of the 24.7 mm wide, 3.6 mm thick neck by the knee torque gives 2.7 MPa per N m (beam); the FEA gives 5.3 to 6.8 MPa per N m, converged (section 2.4): a stress concentration of 2 to 2.5 from the eye, its 7 mm hub hole and the 4 horn screw holes, with only 2.5 mm of plastic between a screw hole and the eye edge. At the walking peak the knee torque gives about 80 % of the stress there and the axial force most of the rest [L] (unit-load split at the weak spot).
- roll_to_pitch: the weak spot is the wall at x 27 to 32 mm that joins the two hip roll horn ears (5 mm thick, printed upright: print z = link y). The idle-horn force (90 N walking, 130 N push, from the two-support split of the hip roll bending moment) drives it; the 1 mm average gives 13.7 MPa of interlayer shear at the walking peak (24.3 MPa von Mises). The raw element peak at level 1 (19.6 MPa of interlayer tension) was a single-element spike (section 2.2).

### 2.2 FEA method
- Geometry: the print STLs (print/*.stl, mm) in their URDF link frame. The parts of a leg segment (the two knee sheets and the leg_spacer) are meshed one by one and tied where they touch (springs of 20 kN/mm between surface nodes closer than 0.45 mm: the bonded M3 insert joints and the 0.2 mm spacer gap that the screws close; ASSUMPTION). Elements within 2 mm of a tie are not counted in the peak (a node-to-node tie is not a real contact); the joint is judged by its insert loads instead.
- Mesh: TetGen linear tetrahedra (tetgen 0.8.4). Levels: 1 (radius-edge 2.0, dihedral over 10 deg, volume under 5 mm3), 2 (1.6, 15 deg, 1 mm3), 3 (1.4, 18 deg, 0.3 mm3). The STL triangles (holes with many facets) set the surface size. Screening at level 1; convergence on the two weakest at levels 1 to 3 (section 2.4).
- As-printed zones (each element, in the print frame of its own part, z = parts.csv "up"): walls = within n beads of a side face (2 walls 0.86 mm, 3 walls 1.27 mm, 4 walls 1.67 mm, 5 walls 2.09 mm; print/config/ovr_insert.ini: 0.45 + (n - 1) x 0.41 mm); top skin 1.0 mm (5 layers) under an up-facing face; bottom skin 0.8 mm (4 layers); solid rings of mod_ring.ini (insert bore + 4.0 mm); the rest gyroid infill (15 %, the neck parts 40 %). D22 profile per part from print/parts.csv: roll_to_pitch, roll_motor_top, foot_top, foot_side 2 walls 15 % (rings on foot_top, foot_bottom_pla, leg_spacer); knee sheets, roll_motor_bottom 3 walls; neck parts 5 walls 40 %.
- Effective properties: solid zones isotropic, E 2641 MPa (Overture PLA TDS v5.1, X-Y, 100 % infill specimens, 0.4 mm nozzle, search text; the lab read 2650 MPa in PRINT_PLAN.md), nu 0.35 (ASSUMPTION, 0.30 to 0.40). Gyroid infill: E = E_s rho^2.12 (Gibson and Ashby power law [I] Gibson & Ashby, Cellular Solids, 2nd ed. 1997; exponent 2.12 measured for gyroid lattices [I] Doyle et al. 2025, Adv. Eng. Mater., doi 10.1002/adem.202402495, search text), 47 MPa at 15 %, 379 MPa at 40 %, nu 0.30; nearly isotropic [I] Bean, Lopez-Anido and Vel 2022, Appl. Sci. 12(4):2180 (Zener ratio 0.95 to 1.25, search text). The layer direction enters through the failure criterion, not the stiffness (a z modulus of 0.7 x changes the force-driven stresses little; not run).
- Strengths (room temperature): in-plane X 47.1 MPa (Overture PLA TDS v5.1, X-Y tensile, search text); interlayer Z design 22 MPa (the conservative static reference for printed PLA of [I] Ezeh & Susmel 2019, Mater. Design Process. Commun. 1(2):e45, doi 10.1002/mdp2.45, search text), with the maker's Z 39.4 MPa shown as the upper value (Overture Easy PLA listing extracted from the maker TDS, 3dfilamentprofiles.com/filament/details/7100, search text); interlayer shear S = Z (ASSUMPTION). Infill: 0.3 rho^1.5 X (Gibson and Ashby plastic collapse of open cells), 0.82 MPa at 15 %.
- Failure index per element: solid zones max(von Mises / X, sqrt((max(s_zz, 0) / Z)^2 + (tau_z / S)^2)) in the part's print frame; infill von Mises / infill strength. SF = 1 / peak FI. The peak leaves out elements within 1 mm of loaded or fixed nodes (point-like boundary conditions).
- **Stress averaging over 1 mm:** the failure index is taken on the element stress tensor averaged (by volume) over the elements of the same part and the same zone class (solid or infill) whose centres lie within 1.0 mm (at most the 32 nearest). Reason: linear tetrahedra give one stress per element, and the 0.86 to 2.1 mm wall bands and the 56 x softer infill cut through elements, so single elements carry spikes. On roll_to_pitch at level 1 the raw element peak (19.6 MPa across the layers at the walking peak, SF 0.96) was such a spike: the interlayer stress of the elements round it changes sign (50 to 66 % same sign within 0.5 to 2 mm) and its 1 mm average is a twentieth of it. On the knee sheet the field is smooth (100 % same sign, the 1 mm average is 0.87 to 0.93 of the peak). 1 mm is about two 0.45 mm beads and five 0.2 mm layers, the scale of the printed structure; for notched printed PLA the Theory of Critical Distances uses a material length [I] Ezeh & Susmel 2020, Int. J. Fatigue 136:105583, doi 10.1016/j.ijfatigue.2020.105583 (search text), whose value for this filament is not known (ASSUMPTION: 1 mm; 0.5 and 1.5 mm checked, same verdicts). The raw element peak is listed beside every result.
- Supports: the part is fixed where it holds the next servo (nodes within 0.3 mm of that servo's case meshes, and its case screw holes): a rigid, bonded PA+GF servo case (ASSUMPTION). Loads: at the horn screw holes (hole walls and the face annuli under the heads, RBE3: statically equal, no added stiffness), with the two-support split of st_interfaces.py: the drive horn gets its share of the radial force, the full axial force and the full axis torque; the idle horn (or the hip yaw 6804 bearing boss) its share of the radial force. Six unit loads are solved per study; every sim sample is a linear combination, so the peak over each whole history and the stress history at the weak spot (fatigue) come from the same solves. Solver: pyamg smoothed aggregation with CG, relative residual under 1e-8; the reaction at the supports equals the applied unit load [L].

### 2.3 Table 3: safety factor per part (room temperature, SF = 1 / failure index, lab margin 2 walking and push, 1.2 falls)

FEA_TABLE

Fall columns: the worst of the 10 falls at that contact level. The "interlayer" parts would move up by 39.4 / 22 = 1.79 with the maker's Z value; the in-plane ones do not change.

### 2.4 Mesh convergence

CONV_TABLE

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
- **Upper bound, best-case print data**: rotating bending of FFF PLA with the best parameter set of [I] Gomez-Gras et al. 2018, Mater. Des. 140:278-285, doi 10.1016/j.matdes.2017.11.072 (search text): 35.8 MPa "can be considered as a lower threshold of the endurance limit for this kind of specimens" (stress amplitude, fully reversed, in-plane).

FATIGUE_TABLE

Reading: with the design curve the weak spots do not last 100 hours of walking; with the best-case data none of them fails (every walking stress amplitude is under 35.8 MPa, and the in-plane peaks are at most RANGE_NOTE). The two bounds bracket a factor of about 10 in stress for a given life, so the life is not known: **BLOCKER**, to be closed by a bench fatigue test of a printed knee sheet and roll_to_pitch (P7). No upstream issue reports these parts breaking on 2.1 kg builds with the same servos (UPSTREAM_ISSUES.md: only a neck part, G5, and an unnamed head part, G6), which points to the upper side for the cool parts; heat (section 5) moves it down.

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
| knee_to_ankle_left_sheet of the shin (knee horn eye) | 54 to 66 C | 1.56 / 1.04 | **0.98 / 0.65** | BLOCKER (strength), under 0.98 | x 1.2 at 50 C, x 4 at 60 C |
| roll_to_pitch wall between the horn ears | up to 61 C | 1.60 / 1.11 (Z 22 MPa); 1.94 / 1.34 (Z 39.4) | **1.00 / 0.69**; 1.21 / 0.84 | BLOCKER | x 1.2, x 4 |
| knee_to_ankle_left_sheet of the thigh (hip pitch horn eye) | 54 to 66 C | 2.70 / 1.74 | 1.69 / 1.09 | BLOCKER | x 1.2, x 4 |
| hip roll stage (roll_motor_top and bottom) | not listed by the thermal twin | [[HIP_W]] / [[HIP_P]] | - | - | - |

Creep under the standing load (the robot stands most of a 25/75 session): the stress held at each weak spot while standing, from the same FEA (stand case, nominal and 3 seeds): knee sheet eye of the shin 4.2 MPa (in-plane), roll_to_pitch wall 3.3 MPa (von Mises; the layers there are in compression while standing), thigh sheet [[THIGH_STAND]] MPa, neck sheets 0.2 MPa, head_roll_mount 0.1 MPa (1 mm averages at each walking weak spot). The heat deflection test bends a bar at 0.45 MPa or 1.8 MPa and records the temperature where it moves 0.25 mm (ASTM D648); the knee sheets and roll_to_pitch hold 2 to 10 x those stresses at temperatures at or above their HDT. So **creep is expected at the knee sheets and roll_to_pitch above about 50 C**: the horn screws lose their clamp, the knee and ankle cases loosen in the sheets (the thermal twin's finding 1 says the same). The creep rate is a **BLOCKER**: no creep data for this filament; the printed-PLA creep studies found (Part I of the ScienceDirect 2023 creep study of printed PLA by build and raster direction; the 2025 heat-treatment creep study; the 2022 short-term creep study of AM polymers, all search text) show that temperature and load dominate but give no number usable here.

PETG check (the verdicts change, so the option is checked): Bambu PETG HF TDS V1.0 [I] (search text; copy at botland.com.pl, the thermal twin's [P6]): tensile 34 +- 4 MPa X-Y and 23 +- 4 MPa Z, modulus 1810 MPa X-Y, HDT 69 C at 0.45 MPa and 62 C at 1.8 MPa, Tg 66 C. At room temperature PETG is weaker than this PLA in-plane (34 against 47.1 MPa) and about equal across the layers (23 against the 22 MPa design value); its advantage is that it keeps those values to about 60 C (ASSUMPTION: under its 1.8 MPa HDT of 62 C; no PETG hot strength data found, BLOCKER for an exact value).

| Part | PLA room T (walk / push) | PLA 50 C | PETG to about 60 C (ASSUMPTION) |
|---|---|---|---|
| knee sheet eye of the shin (in-plane) | 1.56 / 1.04 | 0.98 / 0.65 | 1.13 / 0.75 |
| roll_to_pitch wall (interlayer shear with Z 22; in-plane with Z 39.4) | 1.60 / 1.11 | 1.00 / 0.69 | 1.40 / 0.97 |
| knee sheet eye of the thigh (in-plane) | 2.70 / 1.74 | 1.69 / 1.09 | 1.95 / 1.26 |

PETG SF at the same weak spot: 1 / max(von Mises / 34, sqrt((max(s_zz, 0) / 23)^2 + (tau_z / 23)^2)).

So PETG does not bring the two weak parts to the walking margin of 2; it only stops the loss with temperature (and at 66 C it is at its own Tg). It does turn the hot verdicts from about 1.0 back to 1.1 to 1.4. Stiffness: PETG is 0.69 x as stiff as PLA (1810 against 2641 MPa), so the same loads bend the sheets 1.46 x more. Mass: PETG 1.27 g/cm3 (PrusaSlicer Generic PETG, /usr/share/PrusaSlicer/profiles/PrusaResearch.ini line 7810 [L]) against 1.20 g/cm3: +5.8 % on those parts (knee sheets +3.0 g for all 8, roll_to_pitch +2.3 g for both). PETG also needs its own print settings and coupon tests (no PETG profile in print/config/).

## 6. Weak list and proposals (none decided)

Weak list (room temperature unless stated; lab margin 2 walking and push, 1.2 falls):

| # | Part or joint | Case under the margin | SF | Why |
|---|---|---|---|---|
| W1 | roll_to_pitch, both legs (D22 light, 2 walls 15 %) | walking, push, falls | walk 0.78 to 0.96 (Z 22 MPa; 1.4 to 1.7 with Z 39.4), push 0.54 to 0.66, falls under 1 in 9 of 10 at the soft level | the side wall between the two hip roll horn ears is printed upright (print z = link y); the idle-horn force (90 N walking, 130 N push) bends it across the layers |
| W2 | knee_to_ankle_left_sheet of the shin (the plate on the knee drive horn; also the right leg's twin) | walking, push, side falls | walk 1.45, push 0.97, side falls 0.52 to 0.86 (soft) | the eye round the knee horn: 3.4 to 3.9 mm plate, 2.5 mm of plastic between a horn screw hole and the eye edge; the knee torque gives 5.3 to 6.8 MPa per N m there (converged) |
| W3 | the same sheets, hot | walking at 54 to 66 C | 0.90 at 50 C; BLOCKER at 60 C | strength 0.62 at 50 C; creep under the 4.3 MPa standing stress above the HDT |
| W4 | knee and ankle servo case screws (M2 through the 2.0 mm sheet) | walking (ankle), push (knee, ankle) | walk 1.6 (left ankle), push 1.1 to 1.9 | PLA bearing of the 2 mm screw in a 2 mm plate; RBE3 over the screws only (the case pocket also holds, so an upper bound) |
| W5 | knee drive horn screws (M3 through the sheet eye) | push | 1.2 to 1.6 | knee torque spikes in push recovery (6.9 to 8.6 N m) |
| W6 | thigh segment (left sheet at the spacer, interlayer) | push | 1.47 | bending of the sheet-spacer frame |
| W7 | neck chain, head mount, hip yaw stage, trunk frame inserts | falls at the mid level | 0.1 to 1.2 | head inertia 54 to 196 g; the rigid model is an upper bound at this level |

Proposals (each with its cost; none decided; the FEA results are FEA pass only):

PROPOSALS_TABLE

What a lighter or heavier profile does here: more walls barely help an interlayer failure (W1: the walls are already where the bending stress is; their layers are what fails) and help an in-plane failure only through the solid skin and ring area; the print orientation (P1) and the CAD (P2) are the levers.

## 7. Limits, ASSUMPTIONS and BLOCKERS

- **Sim pass only.** Loads come from MuJoCo with the BAM servo model (no gear friction beyond the model, upstream issue 48), the stock policy and our mass model (sim/MASS_BUDGET.md: about 40 g uncertain, uniform density per part). Real servos may track worse; the knee torques are set by the servo limit and the armature, which the model has.
- **Solver setting changes the push answer.** With the upstream 1 Newton iteration the 15 N pushes never topple our build; with 2 or more iterations they always do (4 of 4 at the 4th or 5th push) and single pushes from 15 N sideways or 12 N fore-aft topple 1 to 4 of 8 phases. This study uses the converged setting; the sim owner should look at it (proposed text in the lead report).
- **Contact stiffness of falls is not known:** stated as a range (section 1.3). The rigid-body model overstates the joint loads of a hard hit (no part compliance between the hit and the joints).
- **FEA pass only, linear elastic,** small strain, no contact (bonded ties), no preload, no plasticity: peak stresses at notches are linear peaks. Supports are a rigid bonded servo case; real cases flex and the pocket fit (0.00 to 0.10 mm) is not modelled.
- **Zones are geometric,** from the distance to the surface and the face normal, not from the G-code; walls and skins of the slicer may differ near small features.
- **Strengths:** X 47.1 MPa and E 2641 MPa are maker values for 100 % infill bars (search text); Z is the conservative 22 MPa (the maker Z 39.4 MPa would raise the interlayer SF by 1.79); S = Z is an ASSUMPTION; bearing = tensile strength is an ASSUMPTION. ASSUMPTION ranges: nu 0.30 to 0.40; restitution 0.3 to 0.7; insert sideways capacity 618 to 1235 N; self-tapping strip shear 12.7 to 27.2 MPa.
- **Fatigue:** the cited design curve (P_s 95 %) with the 22 MPa interlayer reference compounds two conservative choices; mean S-N data for this filament and these print settings: BLOCKER.
- **Hot properties:** strength at 60 C and above, creep rates, and PETG hot strength: BLOCKER (section 5).
- **BLOCKERS:** STS3215 horn alloy (thread check of the M3 horn screws); pull-out of the M2 case screws from the PA+GF pilots; pull-out data for M2 and M2.5 self-tapping screws in printed PLA pilots; insert sideways strength; PLA strength at 60 to 66 C; PLA and PETG creep at 50 to 65 C; mean fatigue curve; the real floor of the first walks.
- **Not modelled:** the trunk shells, the head shell and the caches as hit parts (their contact stiffness is a hand calc), the neck chain parts other than the neck sheets and head_roll_mount, the antenna holders, the TPU sole; the right leg (mirror loads, same parts; the right knee peaks are in the load table).

## 8. Sources

Lab and upstream [L], [U]: sim/added_mass_sim.py, sim/current_budget.py, sim/mass_budget.py (all imported unchanged), sim/ADDED_MASS_SIM.md, sim/MASS_BUDGET.md, print/MASS_STUDY.md, print/PRINT_PLAN.md, print/parts.csv, print/config/*.ini, print/slice.py (imported unchanged), fasteners/fasteners.json and FASTENERS.md, MOUNTING.md, audit/sites.json, DECISIONS.md D18 to D22, twin/thermal/THERMAL_TWIN.md, mini_bdx/robots/open_duck_mini_v2/robot.urdf (b23317a), print/*.stl (730c14b), Open_Duck_Playground b9be205 (MJCF, MjInfer, reference motion, gait period 0.54 s), /usr/share/PrusaSlicer/profiles/PrusaResearch.ini (Generic PETG 1.27 g/cm3).

Internet [I] (search result text unless noted; the hosts could not be opened from this session):
- Overture PLA TDS v5.1 (Young's modulus 2641 +- 328 MPa, tensile 47.1 +- 1.2 MPa X-Y, 100 % infill, 0.4 mm nozzle): https://wiki.overture3d.com/pla_tds.pdf ; Overture Easy PLA values extracted from the maker TDS (tensile 44.3 MPa X-Y, 39.4 MPa Z, modulus 2650 MPa): https://3dfilamentprofiles.com/filament/details/7100
- Ezeh O.H., Susmel L. (2018), On the fatigue strength of 3D-printed polylactide (PLA), Procedia Structural Integrity 9: 29-36, doi 10.1016/j.prostr.2018.06.007 (design curve for P_s over 95 %: negative inverse slope 5.5, endurance limit at 2e6 cycles 10 % of the UTS, maximum stress of the cycle as the reference stress): https://www.sciencedirect.com/science/article/pii/S2452321618300076
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
nice -n 10 $PY altaay_lab/twin/structure/st_falls.py          # about 10 min
nice -n 10 $PY altaay_lab/twin/structure/st_interfaces.py
for s in shin_segment thigh_segment roll_to_pitch hip_roll_stage foot neck_sheets head_roll_mount roll_to_pitch_upx roll_to_pitch_w4i40 shin_segment_w5i40; do
  nice -n 10 $PY altaay_lab/twin/structure/st_fea_run.py $s 1; done    # 3 to 11 min each on a shared box
nice -n 10 $PY altaay_lab/twin/structure/st_slice_proposals.py
$PY altaay_lab/twin/structure/st_report.py all > altaay_lab/twin/structure/tables.md
```
