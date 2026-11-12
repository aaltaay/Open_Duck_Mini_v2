# Thermal twin: servo heat, electronics heat and the printed parts (sim pass only)

Written 2026-11-03 between about 2:05 and 3:20 PM ET by the thermal twin agent (sub-agent of the lead Claude Code agent, branch claude/digital-twin). Nothing was bought, printed, sent or deleted, and no other lab file was edited. Every result here is sim pass only: no servo, board or print has been measured. Source tags in square brackets point to the Sources list at the end. ASSUMPTION marks a value with no published source; every one is swept.

## Update 2026-11-11 ET: 60 C operating range, P45B cells, charger in the trunk (sim pass only)

The 2026-11-03 answer below uses a 70 C cut and a P30B cell. The STS3215 sheet (A/1, 2023-06-23) has both an operating range of -20 C to 60 C (item 1-2) and a torque-off above 70 C (item 7-11). The P45B sheet (version 1.2) charges from 0 C to 60 C and discharges from -40 C to 60 C. This update is gate_p45b.py and gate_p45b.json. The torque cut was left off so the time the reading crosses 60 C and 70 C could be read. A 200 C reading in the pessimistic corner is that choice, not a physical temperature.

Charger heat is the D61 band, calc only: 1.9 W at a 7.2 V pack and 3.2 W at a 6.0 V pack, MCP73213 linear, 1.0 A. It is added in the trunk. The charger board has no seat, so the PLA number for it is the trunk wall node, not a gap to a placed board. Cell mass 70 g, diameter 21.55 mm, height 70.15 mm, DC resistance 15 mOhm, all from the P45B sheet. Specific heat is not on that sheet: the old 18650 range is kept and is a GUESS. Half the can facing the bay air is the same assumption as the first run. BEC efficiency 0.85 is a GUESS (Castle publishes none), including at idle.

Docked sit, torque off, idle 21 mA per servo (the sheet), charge current 1.0 A, 6 hours. Sim pass only.

| Charger | Corner | Room | Cells at 6 h | Trunk wall | Hottest knee reading | BEC case |
|---|---|---|---|---|---|---|
| 1.9 W | central | 25 C | 31.1 C | 28.2 C | 26.7 C | 40.9 C |
| 1.9 W | central | 32 C | 37.9 C | 35.1 C | 33.6 C | 47.6 C |
| 1.9 W | high | 25 C | 32.7 C | 28.7 C | 27.8 C | 46.9 C |
| 1.9 W | high | 32 C | 39.5 C | 35.6 C | 34.7 C | 53.8 C |
| 3.2 W | central | 25 C | 33.2 C | 29.5 C | 26.7 C | 43.6 C |
| 3.2 W | central | 32 C | 39.9 C | 36.4 C | 33.6 C | 50.4 C |
| 3.2 W | high | 25 C | 35.3 C | 30.3 C | 27.8 C | 50.8 C |
| 3.2 W | high | 32 C | 42.0 C | 37.1 C | 34.7 C | 57.7 C |

None of those cells leave 0 C to 60 C. None of those servo readings leave -20 C to 60 C. The trunk wall stays under the 49 to 57 C heat-deflection band already cited below. On this model the 1.9 to 3.2 W charger can stay in the trunk during a sit.

Walk, central corner, currents from the P45B session of the trained actuator (out/p45b_sheet/session_bam_backlash_typical.csv). The sheet-stall servo does not complete a walk (ELECTROMECH_TWIN.md update), so this walk heat is not that servo. Friction heat is not in the bins and is omitted, which makes the knee slightly cool. The right knee reading reaches 60 C at 3.3 minutes in a 25 C room and 2.5 minutes at 32 C, and 70 C at 4.5 and 3.5 minutes. If the torque stays on for the session, the right knee body reaches 94.7 C (25 C room) and 101.6 C (32 C). That is the temperature the knee sheets touch, and it is above the softening band. Cells in that central walk reach 48.3 C and 55.0 C, inside the 60 C discharge limit. The pessimistic corner crosses 60 C at 0.5 minutes, and at 32 C the cells reach 62.1 C at 36 minutes if the walk is not cut. The older P30B session file gives the same 3.3 and 2.5 minutes to 60 C, so the minute is not an artifact of which session file is used.

## Answer in plain words

- **Do the knees overheat in a normal session? In continuous walking, probably yes.** In the central parameter set the hotter knee reaches the STS3215's 70 C torque cut after about **10 minutes of continuous walking** in the plain sim model and **4 minutes** in the backlash model at a 25 C room (7 and 3 minutes at 32 C), well inside the 23 to 32 minutes a full charge lasts. When it cuts, the knee drops its torque and the duck falls.
- **Stand and walk 50/50 is marginal; stand 75 %, walk 25 % is safe in sim.** 50/50 in the plain model peaks at 61 C (25 C room) and 68 C (32 C room) with no cut; the backlash 50/50 cuts after 13 and 8 minutes. The 25/75 duty peaks at 50 to 66 C and never cuts (central set). A software thermal guard with rests (walk until the hottest reading is 55 C, rest until 45 to 50 C) prevents every cut in the central set and leaves 12 to 38 walking minutes in 90 at 25 C.
- **Confidence: medium that continuous walking reaches the cut within a charge, low on the minute count.** The time constant and the body-to-air resistance come from physics on the measured case and agree with the only published STS3215 temperature curve [R1]. The heat input is the BAM sim model, which the closed-loop electromech twin reproduces (right knee 1.45 A RMS against 1.44 A here; on its full-charge sessions the twin gives the knee cut at 4.3 min backlash and 10.3 min plain) but which real robots may not follow (upstream issue 48). The corners span "no cut" (every optimistic value at once) to "cut within about a minute of walking" (every pessimistic value at once). The one-at-a-time sweep shows the answer turns mostly on the current, the walking air speed and where the sensor sits.
- **The winding is much hotter than the reading.** At the cut the winding is about 107 to 132 C in the central set. Feetech publishes no winding limit; the Faulhaber motors of the same size allow 125 C [M1].
- **The Feetech protections do not save the walk.** In every walk trace the over-current timer (more than 2.0 A for 2 s) and the overload timer (more than 80 % duty for 2 s) never come close (longest runs 0.06 s and 0.11 s). The first protection to act is the 70 C cut, which unloads the joint (factory unload condition 44 includes the temperature bit [F3]).
- **Electronics in the closed trunk:** 6 to 9 W while walking, 60 % of it the CC BEC Pro at the lab's assumed 85 % efficiency. At the battery stop, over a 25 and a 32 C room: trunk air 38 to 48 C, cells 44 to 56 C (P30B discharge limit 60 C), BEC case 98 to 122 C (75 to 83 C at 25 C if it is 92 % efficient; Castle publishes no efficiency and no thermal data), Pololu 2815 MOSFETs 59 to 83 C, BMS 49 to 67 C. The TEST_PLAN 4.2 board gate (under 50 C after 10 minutes at 6 A) is predicted to fail (about 55 C).
- **PLA:** the eight knee-to-ankle sheets hold the knee and ankle cases and take the knee horns. They see 54 to 66 C in continuous and 50/50 walking (47 to 55 C at 25/75), above the PLA heat deflection temperature (49 to 57 C) and near its glass transition (55 to 60 C). The parts on the hot electronics (the belly floor under the BEC, the battery_pack_lid under the 2815 and against the BMS) also reach the softening range.
- **BLOCKERS still open:** the STS3215 thermal resistance, time constant, sensor position and winding limit (TO1 measures the first three), the BEC Pro efficiency (TEST_PLAN 4.1), the Pi Zero 2 W chip-to-air resistance (walking log).

## Files (altaay_lab/twin/thermal/)

| File | What it is |
|---|---|
| THERMAL_TWIN.md | This file. |
| twin_thermal.py | The twin: heat per servo from the walk traces, two-node servo model, trunk and head enclosures, cells, hot spots, sessions, corners, sweeps, mitigations, tables and figure; re-runs on the twin/electromech session CSVs (section 3.6). |
| geometry.py, geometry.json | Measured on the CAD meshes: outer case area of each servo and how close the printed parts are, the printed parts that touch each case and horn, the trunk and head skin areas and walls, the seats of the electronics. |
| fit_robo9.py, fit_robo9.json | The model against the published STS3215 temperature curves: fitted time constant, the physics time constant, and the sensor share w. |
| to1_predict.py, to1_predict.json | Predicted bench curves for TO1 (TEST_PLAN 7.3) and the 4.1 and 4.2 heat checks. |
| tables.md, results_summary.json | Every result table and the summary numbers (generated). |
| twin_thermal.png | Right knee reading and winding against time; trunk air, cells and head air. |

Heavy outputs (full traces) stayed in the session scratch folder (twinTH), not in git.

## 1. Thermal data found for the STS3215

Searched 2026-11-03: LeRobot (huggingface/lerobot) and SO-ARM100 issues, other GitHub issues naming the STS3215, the Open Duck repositories, Feetech and FTServo pages, Waveshare, third-party bench tests, papers on the Hugging Face paper index and arXiv. Not readable from this session: feetech.cn (connection reset), zhihu.com (403), blog.csdn.net (521), poppy.discourse.group (502), a Dynamixel knee-heat paper host (DNS), the Open Duck Discord, and an X teardown thread of the STS3215 (images).

| Tag | Source | Servo | Conditions | Measured |
|---|---|---|---|---|
| R1 | Robo9 bench test (article and SO-ARM100 issue 134) | STS3215 C018, 12 V, 1:345, same PA+GF case and 55 g as our C001 | 1 kg on a 15 cm lever (15 kg.cm) held still, arm sideways, 12 V | internal reading 25, 30, 35, 40, 45, 48 C at 0, 2, 4, 6, 8, 10 min, then 48 C to 60 min (chart) |
| R1 | same | C018 | +-90 deg oscillation, acceleration 5, then 2 | 48 to 60 C in 40 to 50 min, flat for 20 min; at the lower acceleration on to 71 C after about 40 more min; "at 71 C the motor exhibits issues"; the author saw no shutdown, later wrote that the protection "kicks in around 70 C" |
| R1 | same | C018 | lifting 1.5 kg on a 10 cm lever, repeated | +15 C after 10 min; 2 kg tripped the overload protection; at 35 kg.cm stall the servo dropped to about 20 % torque |
| R2 | Robo9 servo comparison (2026-06) | STS3215 (12 V class), STS3235, STS3250, HLS3930M, HLS3950M | 50 % load held 2 min, 12 V | STS3215: 22 kg.cm at 0.75 A; internal 31 to 41 C, thermal camera 30 to 33.5 C. STS3235 31 to 36 C. STS3250 30 to 55 C (camera 30 to 54 C), 35 kg.cm at 1.6 A. Repeated 100 % load tests burnt one STS3215 controller board and one STS3250 motor |
| R3 | phosphobot issue 241 (2025-08-08) | SO-100 gripper STS3215 | gripper held closed on an object | "holding a single object for just 30s to a minute already raises temp to 50 C"; one servo went over 70 C and was damaged |
| F1 | Feetech ST-3215-C001 specification A/1 (2023-06-23) | C001 | data sheet | operating -20 to 60 C; "more than 70 C, turn off torque output"; rated 0.65 A at 5 kg.cm; stall 2.5 A at 7.4 V; 2.5 ohm; idle 21 mA; core motor; PA+GF case; 55 g; life test over 100,000 cycles at 1/5 of the stall torque. No thermal resistance, no time constant, no winding class, no sensor position |
| F2, F3 | FTServo STS memory table; factory register read of STS3215 units | STS series | registers | 13 = 70 C; 19 = 44 (unload on temperature, current and overload); 28 = 310 x 6.5 mA = 2.0 A; 38 = 2 s; 36 = 80 % for 35 = 2 s, then 34 = 20 % torque; status and protection clear when the condition clears |
| F4 | Feetech product note (2020) | STS3215 | text | overheat protection "detect the current motor temperature"; feedback "internal working temperature" |
| R4 | Disney Research, Olaf (arXiv 2512.16705) | neck actuators (not STS3215) | in a costume | a first-order model fitted on 20 min of the actuator's own readings predicted a 10 min run within 1.87 C; without a thermal reward a neck actuator reached 100 C within 40 s; fitted ambient inside the costume 43.9 C |
| M1 | Faulhaber 1724 SR, 2224 SR, 2232 SR data sheets | DC motors 17 to 22 mm, 27 to 62 g | data sheet | winding to housing 6.9 to 10 K/W; housing to air with a plastic flange 19 to 27 K/W; winding time constant 7.2 to 12 s; housing 310 to 500 s; winding at most 125 C |
| - | LeRobot issues (search) | | | no temperature logs; issue 1319 asks how to read servo health, with no data |
| - | Open Duck Mini, Runtime, Playground issues (GitHub search 2026-11-03) | | | 0 issues with temperature, heat, hot or overheat |

What the data allow: no published curve has a known heat input, so the thermal resistance cannot be fitted. Two things can be: the time constant of the servo body, and (with the C018's stall line) the sensor share w. Section 2.4.

## 2. Model

### 2.1 Heat per servo
From the per-servo torque and speed traces of the stock policy on our 2.65 kg build (the verification run of 2026-11-02 6:36 AM ET, sim/added_mass_sim.py traces, statistics after 2 s), with the BAM motor model of sim/current_budget.py [B1]: applied volts u = F R / kt capped at the servo's mean volts (7.07 V at a full pack, sim/POWER_PATH_SIM.md 'As built'), current I = (u - kt w) / R; the kt of the three (1.148, 1.21164, 1.28) that gives the highest copper loss, as sim/runtime_thermal.py.
- Winding copper: I_rms^2 x 2.5 ohm [F1] x (1 + 0.00393 x (T_winding - 25)) [E1].
- Board: I_rms^2 x (R_BAM - 2.5 ohm), where R_BAM - 2.5 ohm is 0.13 to 0.43 ohm (the data sheet stall line gives 0.46 ohm).
- Friction in the gears: frictionloss 0.068 Nm x mean |w| plus (0.56 - kt^2/R) x mean w^2 (the MJCF class [U1]).
- Idle electronics: 21 mA x the servo volts [F1].
- Nominal pack: the full-pack heat times the square of the closed-loop current ratio of twin/electromech (out/states_<walk>.json: right knee 1.454 to 1.327 A in the backlash walk, the robot walks slower).

| Servo (full pack) | plain walk: I rms, total heat | backlash walk: I rms, total heat | standing |
|---|---|---|---|
| right knee | 1.19 A, 4.09 W (winding 3.52) | 1.44 A, 5.95 W (winding 5.17) | 0.48 A, 0.76 W |
| left knee | 1.08 A, 3.46 W | 1.38 A, 5.52 W | 0.59 A, 1.07 W |
| ankles | 0.74 to 0.76 A, 1.75 to 1.82 W | 0.78 to 0.81 A, 1.93 to 2.08 W | 0.15 to 0.19 W |
| hip pitch | 0.56 to 0.65 A, 1.10 to 1.42 W | 0.65 to 0.77 A, 1.45 to 1.95 W | 0.16 to 0.17 W |
| head pitch, yaw, roll | 0.46 to 0.59 A, 0.78 to 1.17 W | 0.51 to 0.70 A, 0.93 to 1.55 W | 0.15 to 0.17 W |
| hip roll, hip yaw, neck pitch | 0.18 to 0.38 A, 0.25 to 0.56 W | 0.23 to 0.53 A, 0.32 to 0.97 W | 0.15 to 0.53 W |

The Feetech rated point (0.65 A, 5 kg.cm) loses 1.06 W in the winding. Full table: tables.md.

### 2.2 Two nodes per servo
- Winding node C_w (winding and armature) and body node C_b (case, gears, PCB, motor can). R_wc between them. Body to air: h x A_eff with h = natural convection (Churchill and Chu on the side faces, Lloyd and Moran on the top and bottom) combined with forced convection (laminar plate, n = 3 mixing) plus radiation [H1][E4][E5], recomputed from the temperatures every 10 s.
- A_eff from geometry.json: outer case area 6690 mm2 (the three case meshes, rays that leave the case), with the share of that area that has a printed part within 2 mm (knee 8 %, hip pitch 32 %, hip roll 40 %, hip yaw 41 %) or 2 to 10 mm (knee 27 %) kept at a_contact and a_mid of a free face.
- The reading: T_sensor = T_b + w (T_w - T_b). The 70 C cut acts on the reading; after a cut the servo carries no torque (idle heat only).
- Servos in the trunk (hip yaws, neck pitch) see the trunk air, the head roll the head air; their heat goes into that air.

| Parameter | low | central | high | Source |
|---|---|---|---|---|
| total heat capacity C_b + C_w (J/K) | 36.5 | 33.4 | 30.9 | case plastic 8.37 cm3 (measured) x PA+GF density and specific heat [E2][E3], the rest of the 55 g [F1] at 0.375 to 0.49 J/gK [E2]; glass share 0 to 40 % and the lead mass 0 to 4 g are ASSUMPTION |
| winding node C_w (J/K) | 4.0 | 2.5 | 1.5 | Faulhaber class tau_w1 / Rth1 = 0.7 to 1.7 J/K [M1]; iron armature up to 4 (ASSUMPTION) |
| winding to body R_wc (K/W) | 6.9 | 10 | 15 | Rth1 6.9 to 10 [M1] plus can to case 0 to 5 (ASSUMPTION) |
| sensor share w | 0 | 0.1 | 0.3 | 0.03 to 0.19 from the two Robo9 tests (2.4); swept |
| a_mid / a_contact | 0.90 / 0.85 | 0.70 / 0.75 | 0.50 / 0.55 | ASSUMPTION (a 2 to 10 mm air gap conducts 2.6 to 13 W/m2K plus radiation; a touching 2 to 4 mm PLA plate adds 0.015 to 0.03 m2K/W) |
| walking air speed at a leg servo (m/s) | 0.5 | 0.2 | 0 | ASSUMPTION (walk 0.10 to 0.15 m/s plus leg swing) |
| emissivity | 0.97 | 0.93 | 0.90 | plastics 0.90 to 0.97 [E5] |
| current factor | 1.0 | 1.0 | 1.25 | ASSUMPTION: the data-sheet stall torque per amp (0.765 Nm/A) is 0.6 x the BAM kt, gear friction rising with load that BAM m1 lacks [B2]; CURRENT_BUDGET.md asks for up to 2 x |
| kt | lowest loss | highest loss | highest loss | 1.148 to 1.28 (sim/current_budget.py) |

Resulting body-to-air resistance of a knee on the walking robot: 7.1 (low) to 9.2 K/W (central); a bare servo on a bench in still air: 11.2 to 11.6 K/W. Body time constant about 4.5 to 6.5 minutes.

### 2.3 Trunk, head and electronics
- Trunk: air node and wall node. Skin measured on the seven shell parts (body_front, body_back, body_middle_bottom, body_middle_top, trunk_bottom, trunk_top, battery_pack_lid; rays that leave the shell group): outer 104,450 mm2, inner faces 156,536 mm2 (this count includes mating faces and ribs, so the convective inner area is taken as the outer skin times 0.8 to 1.5), wall median 3.0 mm (area-weighted mean 7.0 mm in the high corner), PLA 0.13 W/mK [P1]. Wall heat capacity: 406 g of printed PLA (print/SLICE_SUMMARY.md, minus supports) x 1.2 to 1.8 J/gK [P1][P4]. Head: outer 97,729 mm2, inner 86,809 mm2, wall 3.0 mm, 289 g.
- Outside: natural convection and radiation on the skin, plus the walking speed (0.13 m/s). Inside: natural convection to the walls (x 0.7 to 1.3, ASSUMPTION); 60 % of each part's heat goes to the air and 40 % by radiation straight to the walls (ASSUMPTION). No air exchange through the leg and neck openings (conservative).
- Losses from the as-built power path (sim/POWER_PATH_SIM.md 'As built', backlash walk, our build: pack RMS 5.61 A full and 5.91 A nominal, BEC out 4.18 A at 7.20 V), scaled by the servo power for the other walks: cells 2 x I^2 x 17 mOhm [C1]; holder contacts 10 to 30 mOhm, BMS 15 to 25 mOhm (25 max, Tenergy), fuse 6 mOhm, XT30 2 mOhm, wires 8.8 mOhm [L1]; Pololu 2815 on resistance on a straight line between 13 mOhm at a 4.5 V gate and 8.6 mOhm at 10 V [S1], times 1.0 to 1.3 hot (ASSUMPTION); BEC loss = output x (1 / efficiency - 1) with 0.80 to 0.92 (0.85 the lab's ASSUMPTION; Castle publishes none); logic boards 0.15 W (ASSUMPTION).
- Cells: own node, 2 x 47 g [C1] x 0.81 to 0.97 J/gK [C2], half of the can area to the bay air and walls.
- Hot spots (steady offsets above the trunk air): BEC case from its 47 x 33 x 22 mm size [S4] with the taped face closed, emissivity 0.1 to 0.9 (ASSUMPTION: case finish not published); Pololu 2815 board to air from Pololu's own point (6 A heats the MOSFETs to 55 C in 22 C still air [S1]: 82 to 107 K/W); fuse holder from its 50 x 17.2 x 17.2 mm body; BMS 15 to 50 K/W (ASSUMPTION; two 2 mm PLA walls give t/(kA) = 28 K/W per face, the four 16 AWG leads take heat out).
- Head: the 5 V branch, 3 W typical and 5 W conservative [L1], all ends as heat in the head; the D30V30F5 regulator at 94 to 97 % [S2]; the Pi Zero 2 W draws 350 mA typical [S3].

### 2.4 Fit against the published curves (fit_robo9.py)
- Static hold curve [R1]: first-order fit gives a time constant of **316 s** (231 to 435 s within 0.5 K of the best fit), a rise of 25.2 K, RMS error 1.57 K. The physics time constant of a bare servo body in still air (heat capacity from the masses, convection and radiation on the measured case) is **358 to 408 s**: inside the fitted band. With the heat chosen to hit the 48 C plateau, the two-node model follows the chart points with 2.0 to 2.4 K RMS error. The oscillation curve gives a longer and poorly bounded constant (863 to over 3600 s): its heat input changed during the run.
- Sensor share w: the two-minute test [R2] rises +10 C inside. With the C018 data-sheet 1.0 ohm, even w = 1 cannot reach +10 C, so that reading is rejected. With the C018 stall line (12 V / 2.7 A = 4.44 ohm loop) the two-minute test gives **w = 0.03 to 0.19**, and the static plateau then needs a hold current of 0.50 to 0.60 A, which matches the comparison test's 0.75 A at 22 kg.cm scaled to 15 kg.cm (0.51 A). Both tests agree under this reading.
- Not fitted: the thermal resistance (no published heat input), R_wc and the motor mass (no teardown seen), and anything specific to the 7.4 V C001.
- Confidence: medium on the body-to-air resistance and the time constant (physics and the one curve agree); low on w and R_wc; low on the heat input of the real robot.

## 3. Results: servos (sim pass only)

### 3.1 Knee: time to the 70 C cut, or the peak reading in 90 minutes
Worse of the two knees. Minutes from a cold start. The D16 battery stop for our 2.65 kg build (sim/runtime_thermal.py discharge model, typical corner): plain walk 31.7 min, backlash 22.7, mixed 31.6, 50/50 49.3, 25/75 66.9, 50/50 backlash 38.2, 25/75 backlash 56.5.

| Session | Pack | 25 C room: low / central / high | 32 C room: low / central / high |
|---|---|---|---|
| continuous walk, plain model | full | 53 C / **10 min** / 1.2 min | 60 C / **7 min** / 0.9 min |
| continuous walk, plain model | nominal | 50 C / **14 min** / 1.6 min | 57 C / **8 min** / 1.1 min |
| continuous walk, backlash model | full | 68 C / **4 min** / 0.6 min | 10 min / **3 min** / 0.5 min |
| continuous walk, backlash model | nominal | 60 C / **6 min** / 0.8 min | 68 C / **4 min** / 0.6 min |
| mixed walking (1/2 forward, 1/4 turn, 1/4 side) | full | 54 C / **9 min** / 1.2 min | 61 C / **6 min** / 0.8 min |
| stand and walk 50/50 (60 s each) | full | 46 C / **61 C** / 2.6 min | 53 C / **68 C** / 0.9 min |
| stand and walk 50/50 | nominal | 44 C / 58 C / 2.8 min | 51 C / 65 C / 2.5 min |
| stand 75 %, walk 25 % (30 s walk, 90 s stand) | full | 42 C / **50 C** / 6.4 min | 48 C / **57 C** / 4.3 min |
| stand and walk 50/50, backlash | full | 54 C / **13 min** / 0.6 min | 61 C / **8 min** / 0.5 min |
| stand 75 %, walk 25 %, backlash | full | 47 C / **59 C** / 2.3 min | 54 C / **66 C** / 0.5 min |

A temperature means no cut (the peak reading); minutes mean the cut. The winding at the cut: 107 to 132 C (central). Full table, with the readings at the battery stop: tables.md.

### 3.2 Every servo (central, full pack)
Only the knees reach the cut. Peak readings of the others: ankles 34 to 58 C, hip pitch 32 to 58 C, hip yaw (in the trunk air) 37 to 61 C, neck pitch 37 to 60 C, head roll (in the head) 39 to 56 C, head pitch and yaw 31 to 53 C, hip roll 31 to 44 C (tables.md).

### 3.3 Steady state if walking never stopped (no cut)
| Walk, room | right knee: body / winding / reading, central | low corner |
|---|---|---|
| plain, 25 C | 75 / 124 / 80 C | 53 / 76 / 53 C |
| plain, 32 C | 82 / 132 / 87 C | 60 / 83 / 60 C |
| backlash, 25 C | 103 / 188 / 112 C | 68 / 105 / 68 C |
| backlash, 32 C | 110 / 196 / 119 C | 75 / 113 / 75 C |

In the high corner the copper's resistance rise feeds the heat and the steady values run away; the cut acts within 1 to 2 minutes there.

### 3.4 What the answer turns on (one parameter at a time from central; right knee, full pack, 25 C)
| Parameter | low value: plain / backlash / 50-50 | high value: plain / backlash / 50-50 |
|---|---|---|
| current factor | 1.0: 10 min / 4 min / 61 C | 1.25: 4 min / 2 min / cut at 9 min |
| kt choice | lowest loss: 69 C / 6 min / 54 C | highest loss: 10 min / 4 min / 61 C |
| walking air speed | 0.5 m/s: 70 C / 5 min / 56 C | 0: 8 min / 4 min / 64 C |
| sensor share w | 0: 13 min / 5 min / 57 C | 0.3: 6 min / 3 min / 69 C |
| R_wc | 6.9: 12 min / 5 min / 59 C | 15: 8 min / 4 min / 64 C |
| mounting (a_mid, a_contact) | 0.9: 11 min / 4 min / 59 C | 0.5: 9 min / 4 min / 63 C |
| C_w | 4.0: 10 / 5 min / 60 C | 1.5: 9 / 4 min / 62 C |
| heat capacity (glass share, metal cp) | no change over the range (9 to 10 min / 4 to 5 min / 61 C) | |
| emissivity | no change over the range | |

The plain walk sits at the edge: about 10 % less heat or a 0.5 m/s air speed keeps the reading just under 70 C. The backlash walk cuts at every single-parameter change. 50/50 stays under the cut in every single-parameter change except the 1.25 current factor.

### 3.5 Feetech protections in the walk traces
| Check (full pack, worst servo) | plain walk | backlash walk | limit |
|---|---|---|---|
| longest run over 2.0 A (register 28 = 310) | 0.018 s (left knee) | 0.06 s (left knee) | 2 s (register 38) |
| longest run over 80 % duty (register 36) | 0.056 s (left knee); 0.072 s at a nominal pack | 0.10 s (right knee); 0.11 s at a nominal pack | 2 s (register 35) |
| highest 2 s mean current | 1.05 A | 1.31 A | |

So neither timer trips while walking, at full or nominal pack. A hot winding has more resistance and less torque, so the policy will push the duty higher as the knee heats; the twin does not model that loop (the electromech twin can).

### 3.6 Re-run on the closed-loop electromech sessions
twin/electromech landed three full-charge sessions at 3:13 to 3:14 PM ET (out/session_<walk>_<corner>.csv, 5 s bins: the walk, the servos and the power network solved together, the pack running down from full to past the D16 stop). The twin re-ran on their winding RMS currents per bin (friction and idle from the open-loop trace of the same walk):

| Session (electromech) | length | knee mean winding RMS (left / right) | central: knee cut, 25 / 32 C room | low corner | high corner |
|---|---|---|---|---|---|
| backlash walk, typical power path | 26.5 min | 1.27 / 1.36 A | **4.3 / 3.3 min** | 11.6 / 6.6 min | 0.6 / 0.5 min |
| backlash walk, high-side power path | 26.6 min | 1.24 / 1.33 A | **4.7 / 3.6 min** | no cut (68 C) / 7.5 min | 0.7 / 0.5 min |
| plain walk, typical power path | 33.8 min | 1.02 / 1.13 A | **10.3 / 6.8 min** | no cut (55 / 62 C) | 1.3 / 0.9 min |

The closed loop confirms the open-loop answer: the cut comes in the first minutes, while the pack is still near full and the currents are highest. (The low corner cuts here in the backlash walk because the electromech currents are one kt model, not the lowest-loss kt the open-loop low corner picks.)

## 4. Results: electronics in the body (sim pass only)

Trunk losses while walking, central corner, full pack: plain walk 6.1 W (BEC 3.9), backlash walk 8.8 W (BEC 5.3, cells 1.07, holder 0.63, BMS 0.63, Pololu 2815 0.37, wires 0.28, fuse 0.19, BEC leads 0.08, XT30 0.06, logic 0.15). Head: 3.1 W (5 V branch and regulator; 5.2 W in the high corner).

At the D16 battery stop, central corner, full pack:

| Session, room | trunk air | cells | BEC case | Pololu 2815 MOSFETs | BMS | fuse holder | head air | 5 V regulator |
|---|---|---|---|---|---|---|---|---|
| continuous plain walk, 25 C | 38 C | 44 C | 98 C | 59 C | 49 C | 41 C | 34 C | 51 C |
| continuous backlash walk, 25 C | 41 C | 49 C | 116 C | 76 C | 60 C | 46 C | 34 C | 51 C |
| continuous backlash walk, 32 C | 48 C | 56 C | 122 C | 83 C | 67 C | 53 C | 41 C | 57 C |
| stand and walk 50/50, 32 C | 42 C | 48 C | 101 C | 63 C | 54 C | 45 C | 41 C | 57 C |
| stand 75 %, walk 25 %, 32 C | 40 C | 44 C | 100 C | 61 C | 52 C | 43 C | 41 C | 57 C |

- The high corner (every pessimistic value at once) puts the trunk air at 58 to 74 C and the cells at 71 to 92 C in continuous walking; it is a bound, not a forecast.
- BEC case against its unpublished efficiency, at 41 C trunk air (continuous backlash walk, 30.1 W out): 80 %: 122 to 172 C; 85 %: 103 to 140 C; 90 %: 83 to 109 C; 92 %: 75 to 97 C; 95 %: 64 to 78 C (emissivity 0.9 to 0.1).
- Pololu 2815 in the robot: 0.37 W at full pack (5.61 A, 11.9 mOhm), 0.45 W at nominal; 82 to 107 K/W from Pololu's own data point, so 35 to 42 K over the trunk air. It stays far under its 150 C limit; the 50 C bench gate is the issue (below).
- Pi Zero 2 W: the head air is 34 C (25 C room) and 41 C (32 C room); the chip's rise over its air is not published (BLOCKER). The Pi throttles from 80 C [S3]: log it in the walking log.

Bench gates, predicted (to1_predict.json; 22 C room, still air):
- TEST_PLAN 4.1 (BEC, 10 min at 5 A out, no airflow, case under 60 C): 54 C at 92 % efficiency (pass), 94 C at 85 % (fail), 146 C at 80 %. So this gate measures the efficiency the twin needs.
- TEST_PLAN 4.2 (Pololu 2815, 10 min at 6.0 A on its seat, board under 50 C): 50 to 59 C after 10 min, steady 63 C (at a 7.4 V gate the on resistance is 1.24 x the 10 V value; Pololu's own point is 55 C at 12 V). Expected to fail; the second 2815 below the seat (TEST_PLAN 4.2 fallback) halves the current per board and quarters its heat.

## 5. Printed parts and heat

PLA data: heat deflection temperature 49 C (ASTM D648, SD3D PLA [P1]), 55 C at 0.45 MPa (Ingeo 4043D, the common filament resin [P2]), 57 C at 0.45 MPa and 54 C at 1.8 MPa (Bambu PLA Basic [P3]); glass transition 55 to 60 C [P2], 57 C [P1], 60 C [P3]; Vicat softening 66.2 C for our Overture Easy PLA [P5], whose data sheet gives no HDT or Tg. Above the HDT a loaded PLA part is expected to creep; the rate for this filament is not published. PETG for comparison: glass transition 66 C, HDT 69 C at 0.45 MPa and 62 C at 1.8 MPa (Bambu PETG HF [P6]).

Printed parts touching the servo cases (geometry.json, gap under 0.3 mm), and the peak servo body temperature in the central corner, full pack (the PLA at a touching face sees about this):

| Servo | printed parts on the case (mm2) | horn faces on printed parts (mm2) | plain walk 25 / 32 C | backlash walk 25 / 32 C | 50/50 25 / 32 C | 25/75 25 / 32 C |
|---|---|---|---|---|---|---|
| knees | knee_to_ankle_left_sheet 437, knee_to_ankle_right_sheet 356 | drive horn 210 and idle horn 96 on the shank sheets | 65 to 66 C (at the cut) | 64 C (at the cut) | 54 to 57 / 61 to 64 C | 47 to 48 / 54 to 55 C |
| ankles | the same two sheet types (the shank pair) | foot_top 192, foot_side 173 | 45 to 46 / 52 to 53 | 47 to 49 / 54 to 56 | 38 / 45 | 33 / 40 |
| hip pitch | left/right_roll_to_pitch 2393 to 2440 | the thigh sheets 209 to 211, 96 to 113 | 38 to 42 / 45 to 49 | 43 to 49 / 50 to 56 | 34 to 36 / 41 to 43 | 31 to 32 / 38 to 39 |
| hip yaw (in the trunk) | trunk_top 2933 to 3017 | roll_motor_top 263 | 45 / 52 | 52 to 54 / 58 to 60 | 40 / 46 | 37 / 44 |
| neck pitch (in the trunk) | trunk_top 2049 | neck sheets 188 to 204 | 45 / 52 | 53 / 59 | 40 / 46 | 37 / 44 |
| hip roll | roll_motor_bottom 1542, roll_motor_top 958 | roll_to_pitch 182 to 190 | 30 to 32 / 37 to 39 | 34 to 36 / 41 to 43 | 32 to 33 / 38 to 40 | 32 to 33 / 39 to 40 |
| head pitch, yaw, roll | neck sheets 292 to 384, head_yaw_to_roll 986, head_roll_mount 1323 | head_pitch_to_yaw 186 to 222, head_yaw_to_roll 258 | 38 to 46 / 45 to 53 | 44 to 49 / 51 to 56 | 33 to 42 / 40 to 48 | 31 to 39 / 38 to 46 |

Electronics seats (geometry.json from audit/placements.json): the BEC sits on the body_middle_bottom floor through 1.1 mm VHB foam (1858 mm2 within 1.5 mm); the Pololu 2815 (353 mm2) and the fuse holder (745 mm2) on the battery_pack_lid through the same tape; the BMS is pressed against the lid (0.08 mm) and body_back (864 mm2 within 1.5 mm).

What it means:
1. The eight knee-to-ankle sheets (4 per leg: the thigh pair clamps the knee case, the shank pair clamps the ankle case and takes the knee horns) are the most exposed PLA. In every walking session except 25/75 at 25 C they reach or pass the HDT range, and in continuous walking they sit near the glass transition until the knee cuts. Expect loosening of the case screws and creep at the horn screws over many sessions, not a sudden break (no creep data for this filament).
2. trunk_top (hip yaw and neck pitch cases) and roll_to_pitch (hip pitch) reach 50 to 61 C in the backlash walk at a warm room: at the HDT edge.
3. The belly floor under the BEC (98 to 116 C case, central) and the battery_pack_lid under the 2815 (59 to 76 C) and against the BMS (49 to 60 C) see local temperatures in or above the softening range. The lid holds the battery holder in place.
4. Hip roll, head and neck parts stay under 56 C in the central corner.

## 6. Options (not decided; each with its cost and its effect in the twin)

Central corner, full pack, right knee unless noted (tables.md, Mitigations).

| Option | Cost | Effect in the twin | Notes |
|---|---|---|---|
| Thermal guard with cool-down rests: stand when the hottest reading reaches 55 C (limit minus 15), walk again at 45 C | $0, software (bench/walk_with_guard.py stops at 55 C today and does not restart) | no cut in any session; walking minutes in 90: plain 23 (25 C room) and 3 (32 C), backlash 12 and 2 | standing still costs the knee 0.8 to 1.1 W, so at 32 C it barely cools to 45 C |
| The same, walk again at 50 C | $0 | plain 33 and 13 min, backlash 18 and 6 min | the winding still reaches 92 to 113 C |
| The same with torque-off rests (robot on a stand or sitting) | $0 plus a stand | plain 38 and 25 min, backlash 24 and 16 min | the Runtime has no sit pose (bench/odm_bench/thermal.py notes); needs a stand |
| Duty limit: plan sessions as stand 75 %, walk 25 % | $0 | no cut: peaks 50 / 57 C (plain), 59 / 66 C (backlash) | 50/50 is marginal (61 / 68 C plain; the backlash 50/50 cuts) |
| Clip-on aluminium heat sinks on the free faces of the knee cases | not sourced (UNVERIFIED), a few grams per knee | +30 % effective area (ASSUMPTION): plain 25 C no cut (68 C), backlash still cuts at 5 min | must clear the moving sheets at both limits; check on the first leg |
| Trunk vents and a small 5 V fan | fan not sourced (UNVERIFIED); drill steps like D24 | 0.3 W/K exchange (ASSUMPTION): trunk air 7 to 8 K lower, cells 5 K lower at the battery stop; no effect on the knees | the fan adds about 0.5 to 1 W to the 5 V branch (UNVERIFIED) |
| PETG for the parts that touch servo cases or hot electronics (8 knee-to-ankle sheets 53 g, roll_to_pitch x2 42 g, trunk_top 75 g, neck sheets 14 g; battery_pack_lid 14 g) | about one PLA-spool price (BOM line 27 is $29.98 for 2 kg PLA; PETG price not sourced) and reprint time | +12 to 20 K to the softening point at the contacts (PETG HDT 69 C against PLA 49 to 57 C) | a new filament profile and coupons; stiffness changes go to the twin/structure job |
| Second Pololu 2815 in parallel | $8.49 (BOM line 10) | each board 0.09 to 0.11 W: MOSFETs about 10 K over the trunk air instead of 35 to 42 K | the TEST_PLAN 4.2 fallback; 40.8 mm free below the seat |
| BEC cooling or a regulator with published efficiency | not sourced | at 92 % the BEC case falls from 116 to about 83 C; vents and the fan cut the trunk air | TEST_PLAN 4.1 measures the efficiency first |
| Retrain with a thermal reward (Disney's Olaf approach [R4]) | GPU time, no hardware | not modelled; Olaf's reward kept a neck actuator under its limit at a small tracking cost | needs this twin's servo model in the training loop |
| 3S pack (D23, held) | per D23 | the pack current falls by about a third for the same power: pack-side heat (cells, holder, BMS, fuse, switch, wires: 3.2 W in the backlash walk) falls by about half | no direct effect on the servos |
| STS3250 knees (SERVO_UPGRADE_OPTIONS.md option A) | 3 x $73.99 plus a BAM identification and a retrain | 0.25 to 0.41 x the copper loss per Nm (0.8 to 2.4 W at the knee); with the C001's thermal values that stays under the cut, but the STS3250's own thermal values are not published | Robo9 [R2] found the STS3250 the thermal outlier (+25 C in 2 minutes at 50 % load) and burnt one motor in repeated 100 % tests: test one unit first |

## 7. Proposed text for files owned by others

TEST_PLAN.md section 7, replace item 3 with:
"3. Thermal (D2; twin/thermal/THERMAL_TWIN.md). Horn fixed against a rigid stop, 7.2 V, room temperature written down. Read registers 13 (Max Temperature Limit) and 19 (Unload Condition) once. Log Present Temperature (63), Present Current (69), Present Load (60) and Present Voltage (62) every 2 s; if a thermocouple is at hand, tape it to the largest free face of the case and log it too. Step A: command past the stop so that Present Current reads 0.9 A and hold until the reading rises less than 0.5 C in 5 minutes (twin, central: about 57 C after 30 minutes, time constant about 6 minutes, about 12 K/W; twin/thermal/to1_predict.json). Step B: 1.2 A until the reading is 60 C or 15 minutes have passed (twin: 70 C at about 9 minutes). Do not hold 1.5 A: the twin puts the 70 C cut at about 4 minutes (1 to 5). From step A: the stall loop resistance R = Present Load x Present Voltage / Present Current (about 2.8 ohm cold), whose rise gives the winding temperature (copper +0.393 % per C); thermal resistance = (reading at the end - room) / (current^2 x R + 0.15 W); time constant = time to 63 % of the rise; the winding estimate, the reading and the thermocouple together give where the sensor sits. Put the three values into twin/thermal/twin_thermal.py and re-run it. Pass: the re-run twin keeps every knee at least 10 C under the 70 C cut through a full charge of the session the lab runs first (proposed: stand and walk 50/50 at a 32 C room). If it does not pass: the thermal guard with rests or a duty limit (THERMAL_TWIN.md section 6), then SERVO_UPGRADE_OPTIONS.md."

TEST_PLAN.md section 4.1, add after the 10 minute heat check: "Log the case temperature every 30 s and the input and output volts and amps at 5 A, and compute the efficiency. Twin prediction (twin/thermal/to1_predict.json): the 60 C gate passes only at about 92 % or better (54 C after 10 minutes); at the 85 % the power sim assumes the case reaches about 94 C. The measured efficiency replaces the assumption in sim/power_path_sim.py and twin/thermal."

TEST_PLAN.md section 4.2, add: "Log the board temperature every 30 s. Twin prediction: 50 to 59 C after 10 minutes at 6.0 A with a 7.4 V input, steady about 63 C (Pololu's own point is 55 C at 12 V; a lower gate voltage raises the on resistance), so expect the 50 C gate to fail and the second 2815 to be needed."

TEST_PLAN.md section 9, add: "Temperatures: log Present Temperature of all 14 servos (register 63, in the sync read with register 62), the BNO055 temperature (trunk air near trunk_top) and the Pi chip (vcgencmd measure_temp) through the walking log; write down the room temperature. Run inside bench/walk_with_guard.py (warn at the limit minus 15 C). Twin, central: the hotter knee reads 55 C (the guard warn) after about 5 minutes and reaches the 70 C cut after about 10 minutes of continuous plain walking at 25 C; the backlash model about 3 and 4 minutes; stand and walk 50/50 reaches 55 C after about 11 minutes and never 70 C. A first thermal session: 60 s walk, 60 s stand, guard on, one full charge; pass: no servo over 60 C, BNO055 under 45 C."

STATE.md, add under 'Done' (or 'Numbers now'):
"- Thermal twin (twin/thermal/THERMAL_TWIN.md, sim pass only): with the stock walk on our 2.65 kg build, the hotter knee reaches the STS3215's 70 C torque cut after about 10 minutes of continuous walking (plain sim model) or 4 minutes (backlash model) at a 25 C room, 7 and 3 minutes at 32 C; stand and walk 50/50 (plain model) peaks at 61 to 68 C and 25/75 at 50 to 66 C with no cut, while the backlash 50/50 cuts after 8 to 13 minutes. A thermal guard with rests prevents every cut in sim (central set). Confidence medium that continuous walking cuts within a charge, low on the minutes: the STS3215 thermal data are still a BLOCKER (TO1 measures them). Trunk while walking 6 to 9 W; trunk air 38 to 48 C, cells 44 to 56 C, CC BEC Pro case 98 to 122 C at the assumed 85 % efficiency. The knee-to-ankle sheets see 54 to 66 C in continuous and 50/50 walking (PLA HDT 49 to 57 C)."

HARDWARE_AUDIT.md section 6, add three rows:
"| B36 | STS3215 thermal data: thermal resistance, time constant, sensor position, winding limit (none published) | OPEN, test order 1 (TEST_PLAN 7.3 revised) | twin/thermal/THERMAL_TWIN.md bounds them from physics on the measured case, the Faulhaber size class and the only published curve (Robo9, C018): central corner, the hotter knee reaches the 70 C cut after about 10 minutes (plain model) or 4 minutes (backlash model) of continuous walking at 25 C; 50/50 (plain model) and 25/75 do not cut, the backlash 50/50 cuts after 8 to 13 minutes. The TO1 hold at 0.9 and 1.2 A gives the values the twin needs; re-run the twin and decide the duty, the guard or SERVO_UPGRADE_OPTIONS.md. Sim pass only. |
| B37 | Trunk electronics heat in the closed body: CC BEC Pro efficiency and case cooling not published | OPEN, test order (TEST_PLAN 4.1, 4.2) and the walking log | Twin, central: 6 to 9 W in the trunk while walking, 60 % of it the BEC at the assumed 85 %; BEC case 98 to 122 C, trunk air 38 to 48 C, cells 44 to 56 C (P30B discharge limit 60 C), Pololu 2815 59 to 83 C; the 4.2 gate (board under 50 C) is expected to fail. Measure the BEC efficiency (4.1) and log the BNO055 temperature in TEST_PLAN 9. Sim pass only. |
| B38 | PLA at the servo cases and the hot electronics | OPEN, after B36 and B37, before the full print | PLA HDT 49 to 57 C, Tg 55 to 60 C (Overture Easy PLA gives only Vicat 66.2 C). Twin, central: the eight knee-to-ankle sheets see 54 to 66 C in continuous and 50/50 walking (47 to 55 C at 25/75), trunk_top and roll_to_pitch up to 61 C, the belly floor under the BEC and the battery_pack_lid at the 2815 and the BMS above 50 C. Option: PETG (HDT 69 C) for those parts (THERMAL_TWIN.md section 6). Sim pass only. |"

Optional, for the owners of DECISIONS.md and SERVO_UPGRADE_OPTIONS.md:
- DECISIONS.md D2 note: "2026-11-03, twin/thermal: the 1.5 A hold of TEST_PLAN 7.3 reaches the 70 C cut in about 4 minutes in the twin, so it cannot settle; the proposed TEST_PLAN 7.3 holds 0.9 A to settle and 1.2 A to 60 C, and the pass rule becomes the re-run twin (THERMAL_TWIN.md section 7)."
- SERVO_UPGRADE_OPTIONS.md option A, add a caution: "Robo9's comparison (2026-06) found the STS3250 the thermal outlier at 50 % load, 30 to 55 C in two minutes, and burnt one STS3250 motor in repeated 100 % load tests (twin/thermal/THERMAL_TWIN.md source R2). Hold the first unit at its walking current before buying more."

## 8. Limits

- Sim pass only. The heat comes from the BAM model of the stock walk; real servos track worse (issue 48) and may draw more or less. The closed-loop electromech twin agrees with the open-loop currents at a full pack (right knee 1.454 against 1.44 A, backlash), gives the lower nominal-pack currents used here, and its full-charge sessions give the same cut times (section 3.6). Neither twin models the real servos' worse tracking.
- The motor inside the STS3215 was not seen: C_w, R_wc and w are bounded, not measured. The case area comes from the URDF case meshes.
- Iron and brush losses are only in the BAM friction terms. A hot winding loses torque, and the closed-loop effect of that on the gait is not modelled.
- Enclosure: no air exchange through the leg and neck openings (conservative); infill treated as solid PLA; one air node for the whole trunk (the battery bay may run hotter than the average).
- The BEC case, BMS and fuse figures depend on unpublished parts data (efficiency, case finish, contact resistances); they are ranges.
- Duty cycles alternate 60 s or 30 s bouts; longer bouts make the peaks higher.
- New cells at 23 C; the cells' own temperature does not change their resistance here.

## Sources

Lab files: [L1] sim/POWER_PATH_SIM.md 'As built' and its run JSON (pack 5.61 / 5.91 A RMS, BEC 4.18 A at 7.20 V; the parameter table: BMS 25 mOhm max, fuse 6 mOhm, holder 10 to 30 mOhm, BEC 0.85, 5 V branch 3 W typical and 5 W conservative); sim/RUNTIME_THERMAL.md and sim/runtime_thermal.py (discharge model, kt values, copper loss method); sim/CURRENT_BUDGET.md; print/SLICE_SUMMARY.md (part masses); audit/assembly.json and audit/placements.json; MOUNTING.md; TEST_PLAN.md 4.1, 4.2, 7.3, 9; DECISIONS.md D2, D23; bench/odm_bench/thermal.py and bench/walk_with_guard.py; twin/electromech/out/states_backlash.json and states_plain.json (closed-loop winding currents per pack state).

- [F1] Feetech ST-3215-C001 product specification, edition A/1, 2023-06-23 (the lab's copy): https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf
- [F2] FTServo wiki, STS memory table (registers 13, 19, 28, 34 to 38, 60, 63, 65, 69; 4.6 Configuring protection): https://ftservo.github.io/ftservo-wiki/en/reference/parameter/memory-sts/
- [F3] Factory register read of two STS3215 units, firmware 3.10 (register 19 = 44, 28 = 310, 34 = 20, 35 = 200, 36 = 80): https://raw.githubusercontent.com/commanderfun/STS3215/main/REGISTER_REFERENCE.md
- [F4] Feetech, 2020 new product STS3215 evaluation: https://www.feetechrc.com/2020-05-13_56655.html
- [F5] Feetech ST-3215-C018 values as used in SERVO_UPGRADE_OPTIONS.md (12 V, 30 kg.cm, 2.7 A, 1.0 ohm, 11 kg.cm/A).
- [R1] Robo9, Testing of Feetech STS3215 Servomotor (C018), charts chart-1 and chart-2: https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/ ; the same rows in https://github.com/TheRobotStudio/SO-ARM100/issues/134
- [R2] Robo9, Practical Comparison of Smart Serial Servo Motors for Robotics (2026-06): https://robonine.com/smart-serial-servo-motor-comparison-robotics/
- [R3] phospho-app/phosphobot issue 241: https://github.com/phospho-app/phosphobot/issues/241
- [R4] Disney Research, Olaf: Bringing an Animated Character to Life in the Physical World, arXiv 2512.16705: https://arxiv.org/abs/2512.16705
- [M1] Faulhaber DC-Micromotors 1724 SR, 2224 SR, 2232 SR data sheets: https://www.faulhaber.com/fileadmin/Import/Media/EN_1724_SR_DFF.pdf , .../EN_2224_SR_DFF.pdf , .../EN_2232_SR_DFF.pdf
- [B1] BAM m1.json (kt 1.21164, R 2.6762): https://raw.githubusercontent.com/Rhoban/bam/b1769a6707e18e77fd656ea76a63588e0195bcc3/params/feetech_sts3215_7_4V/m1.json ; BAM Feetech actuator (kt start value "docs says 8 kg.cm / A"): https://raw.githubusercontent.com/Rhoban/bam/main/bam/feetech/actuator.py
- [B2] Extended Friction Models for the Physics Simulation of Servo Actuators (BAM paper, load-dependent friction), arXiv 2410.08650: https://arxiv.org/abs/2410.08650
- [U1] Open_Duck_Playground b9be205, open_duck_mini_v2.xml class sts3215 (damping 0.56, frictionloss 0.068, forcerange 3.23).
- [E1] Engineering ToolBox, resistivity and temperature coefficients (copper 3.93e-3 1/K): https://www.engineeringtoolbox.com/resistivity-conductivity-d_418.html
- [E2] Engineering ToolBox, specific heat of solids (copper 385, brass 375, iron 449, steel 490, nylon-6 1600, glass 670 to 840 J/kgK): https://www.engineeringtoolbox.com/specific-heat-capacity-d_391.html
- [E3] Engineering ToolBox, density of solids (nylon 6 1.12 to 1.17, glass 2.4 to 2.8): https://www.engineeringtoolbox.com/density-solids-d_1265.html
- [E4] Engineering ToolBox, air properties: https://www.engineeringtoolbox.com/air-properties-viscosity-conductivity-heat-capacity-d_1509.html
- [E5] Engineering ToolBox, emissivity (plastics 0.90 to 0.97): https://www.engineeringtoolbox.com/emissivity-coefficients-d_447.html
- [H1] Standard correlations as collected in Incropera, DeWitt, Bergman and Lavine, Fundamentals of Heat and Mass Transfer, chapters 7 and 9: Churchill and Chu (1975) vertical plate, Lloyd and Moran (1974) horizontal plates, laminar flat plate Nu = 0.664 Re^0.5 Pr^(1/3), mixed convection with n = 3.
- [P1] SD3D PLA data sheet (Tg 57 C DSC, HDT 49 C ASTM D648, cp 1800 J/kgK, k 0.13 W/mK): https://3dp.seas.harvard.edu/files/2023/01/PLAMDS.pdf
- [P2] NatureWorks Ingeo 4043D (Tg 55 to 60 C, HDT 55 C at 0.45 MPa): https://cdn.shopify.com/s/files/1/1223/5992/files/PLA_4043D_TDS.pdf
- [P3] Bambu PLA Basic technical data sheet (Tg 60 C; HDT 54 C at 1.8 MPa, 57 C at 0.45 MPa): https://cdn.shopify.com/s/files/1/0380/5149/files/Bambu_PLA_Basic_Technical_Data_Sheet.pdf
- [P4] Lower bound of the PLA specific heat, 1.2 J/gK: a measured value for 3D-printed PLA reported in an AIP conference paper (2020), found through a search index and not read in full (UNVERIFIED).
- [P5] Overture Easy PLA TDS v5.1 (Vicat 66.2 C, melt 149 C): https://overture3d.com/cdn/shop/files/OVERTURE__EASY_PLA_TDS_EN_V5.1_f2df1ff7-e3da-4ae4-8c69-7e90319c05c1.pdf
- [P6] Bambu PETG HF technical data sheet V1.0 (Tg 66 C; HDT 62 C at 1.8 MPa, 69 C at 0.45 MPa), copy at https://botland.com.pl/img/art/inne/25540_karta_produktu.pdf
- [C1] Molicel INR-18650-P30B data sheet (DC impedance 17 mOhm at 50 % SOC, discharge -40 to 60 C, 47 g): https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf
- [C2] 18650 LiCoO2 cell specific heat 814 to 972 J/kgK, as reported for J. Electrochem. Soc. (2015) through a search index; full text not read (UNVERIFIED). Abstract of the same group's method: https://ecs.confex.com/ecs/imlb2016/webprogram/Paper79364.html
- [S1] Pololu 2815 product page (13 mOhm at 4.5 V, 8.6 mOhm at 10 V; 6 A at 55 C, 16 A at 150 C; 12 V, 22 C, still air): https://www.pololu.com/product/2815
- [S2] Pololu D30V30F5 product page, efficiency graph: https://www.pololu.com/product/4892
- [S3] Raspberry Pi documentation: power supplies (Zero 2 W 350 mA typical bare-board active) and config.txt overclocking (throttling from 80 C, limit 85 C): https://github.com/raspberrypi/documentation (master: documentation/asciidoc/computers/raspberry-pi/power-supplies.adoc, documentation/asciidoc/computers/config_txt/overclocking.adoc)
- [S4] Castle CC BEC Pro: Horizon Hobby CSE010000401 (47 x 33 x 22 mm, 40 g): https://www.horizonhobby.com/product/castle-creations-cc-bec-pro-20a-max-output-12s-max-switching-regulator/CSE010000401.html ; Motion RC 010-0004-01 (input 16 to 40 V, 15 A at 16 V in, 20 A peak): https://motionrc.com/products/castle-creations-20a-bec-pro-010-0004-01

## How to run

From the repo root, with the traces of sim/added_mass_sim.py for our build in <scratch>/traces/ours (and stock):
```
python3 altaay_lab/twin/thermal/geometry.py            # about 2 minutes; writes geometry.json
TWIN_SCRATCH=<scratch> python3 altaay_lab/twin/thermal/fit_robo9.py
TWIN_SCRATCH=<scratch> python3 altaay_lab/twin/thermal/to1_predict.py
TWIN_SCRATCH=<scratch> python3 altaay_lab/twin/thermal/twin_thermal.py   # about 10 minutes
```
Options: TWIN_TRACES (trace folder), TWIN_EM_CSV (twin/electromech/out; the nominal-pack currents and the session re-run come from there), TWIN_GEOM (another geometry.json).
