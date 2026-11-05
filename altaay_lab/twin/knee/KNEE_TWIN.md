# Knee twin: STS3250 knees (D32), sim pass only, FEA pass only, calc only

Written 2026-11-04 and 2026-11-05 (US Eastern) by the V1 knee agent for the duck lead. Nothing was bought, posted or printed. Every number below is from MuJoCo (sim pass only), from the structure twin's FEA scaled linearly (FEA pass only, calc only) or from a cited sheet. Raw outputs are not in git (lab rule 9): /home/user/v1_out/knee on the box.

Ahmed, 2026-11-04 6:18 PM ET: "yes, put STS3250s on both knees" (DECISIONS.md D32, recorded by the lead). Both knee servos become Feetech STS3250 (OpenELAB STS3250-C002, $73.99 each, SERVO_UPGRADE_OPTIONS.md option A). The other 12 stay STS3215 C001. Pack, BEC, fuse and BMS stay.

## 1. Answer

- **Heat: fixed across the band.** In all six STS3250 sessions (continuous at 25 and 32 C in both models, 50/50 at 32 C, the low end, the damping stand-in) no knee reaches the 70 C cut. The hottest knee reads 47 to 58 C at the high end and 63 C with the C001's damping, at a 32 C room. The C001 knees cut after 5.5 to 16.4 walking minutes. Tolerance: the worst case (32 C room, continuous) keeps 7 C to the cut but is 3 C over the STS3250's 60 C operating range [F5], so walk_with_guard.py stays on; at 25 C the knee stays at or under 51 C.
- **Saturation: gone.** The knee sits at its limit 0.00 to 0.03 % of walking time, against 21 to 22 % (backlash model) and 2.4 to 3.9 % (plain) with C001 knees.
- **Pack:** walking 4.2 to 4.8 A against 4.3 to 5.7 A. With the track 1b guard: 0 trips at 17 A (0 of 252 replays per band end; worst 14.76 A held 4 ms).
- **RISK: the stock policy walks badly on them; the fix is the retrain.** With the knee damping the published torque-speed line implies (1.00 Nm s/rad, against the C001's 0.56) the stock policy walks 0.023 to 0.038 m/s against 0.063 to 0.096 and falls in 4 of 5 backlash sessions after 15 to 20 walking minutes, no protection active; the 20 s walk covers 0.28 m against 1.35 m. With 0.56 as the stand-in it walks 0.086 m/s (90 %), 1.32 m, no fall. Only the bench BAM fit can say which it is. Fix: the retrain on run2_sts3250 (ready, CPU test passed) with the bench values; until then do not walk the stock policy on STS3250 knees.
- **Falls and get-ups:** the same pushes topple it, one fewer (20 N standing, to the left). Get-ups 29 of 29 at 7.2 V; 27 of 29 at 6.0 V (two ramp poses), against 29 of 29.
- **Structure:** the knee parts improve (the knee torque peak falls 15 to 26 %); roll_to_pitch drops from 1.48 to 1.45 walking and 1.08 to 1.04 in push; the D26 option P1 brings it to 1.81 / 1.20, still under 2 (D26 open). Section 5.

## 2. The STS3250 model (servo_sts3250.py)

Published numbers, Feetech STS3250 product specification A/0, 2024-01-16 [F5] (the file SERVO_UPGRADE_OPTIONS.md cites, sha256 92926b05...):

| Item | STS3250 [F5] | C001 [F1] (today) |
|---|---|---|
| Typical and rated voltage | 12 V; rated input 6 to 12 V (the FTServo wiki says 9 to 12.6 V [F9]: conflict) | 7.4 V; 4 to 7.4 V |
| Stall | 50 kg.cm (4.90 Nm), 4.2 A at 12 V; 2.94 Nm, 2.52 A at 7.2 V (linear) | 19.5 kg.cm (1.91 Nm), 2.5 A at 7.4 V |
| No load | 0.133 s/60 deg (7.87 rad/s) at 12 V; 4.72 rad/s at 7.2 V (linear); no-load current 280 mA | 0.192 s/60 deg (5.45 rad/s) at 7.4 V |
| Kt, terminal R | 11 kg.cm/A, 1.2 ohm | 8 kg.cm/A, 2.5 ohm |
| Rated | 16 kg.cm, 1.4 A | 5 kg.cm, 0.65 A |
| Gear, backlash, motor | 1/345, 0.5 deg or less, coreless | 1/345 |
| Protections (7-11) | over 80 % stall 2 s; over 3.8 A 2 s; over 14 V or under 4 V; over 70 C torque off | over 2 A 2 s; 70 C |
| Case, mass | 45.22 x 24.72 x 35 mm, aluminium, 74.5 g | same outline, PA+GF, 55 g |
| Operating temperature | -20 to 60 C | |

How it enters the twin. The twin's C001 is the BAM identification (3.23 Nm at 7.4 V, where its sheet says 1.91 Nm), so the STS3250 is the twin's C001 times the ratio of the two Feetech sheets at the same volts, not the STS3250 sheet itself:

| Quantity (twin frame, 7.4 V) | Ratio of the sheets | C001 twin | STS3250, low end | STS3250, high end |
|---|---|---|---|---|
| Torque limit | x 1.581 (50/12 against 19.5/7.4 kg.cm per V) | 3.23 Nm (3.14 at 7.2 V) | 5.107 Nm (4.969 at 7.2 V) | same |
| No-load speed | x 0.890 | 5.65 rad/s | 5.03 rad/s (4.89 at 7.2 V; sheet 4.72) | same |
| Torque per amp kt | published 1.375, stall line 1.526 | 1.148 Nm/A | 1.579 | 1.752 |
| Winding R | published 0.480, stall line 0.965 | 2.5 ohm | 1.200 | 2.413 |
| Loop R, duty cap | | 2.630 ohm, 1.0 | 1.330 ohm, 0.582 | 2.539 ohm, 1.0 |
| Back-EMF ke | from the stall and no-load speed | 1.148 V s/rad | 0.795 | 1.367 |
| Joint damping kt ke / R + fv | from the published torque-speed line | 0.56 Nm s/rad | 1.0025 | 1.0025 |
| Copper per Nm^2 | | 1 | 0.254 | 0.414 |
| Heat factor | Robo9 [R3] | 1 | 1 (C001 thermal values, ASSUMPTION) | 1.111 |

- BAM has one constant for torque per amp and back-EMF. The STS3250 sheet does not fit one constant (its no-load speed is high for its stall line: a coreless motor), so the model splits them: torque = (kt / R) u - (kt ke / R) w, motor current (u - ke w) / R.
- Robo9's STS3250 test [R3] (2 kg on 100 mm, 20 kg.cm, 12 V, 25 C room, 40 to 70 C in 8 min) is the only measured STS3250 heat curve. With the C001 thermal values, the high end reaches 70 C at 718 s instead of 480 s, so its heat is x 1.111 to match. The low end would read only 52.7 C at 8 minutes: the published Kt and R are optimistic, and the high end is the one the verdict rests on. ASSUMPTION: the 20 kg.cm held all through the swing.
- ASSUMPTION stand-ins (C001 values): frictionloss 0.068 Nm, viscous friction 0.059 Nm s/rad, armature 0.027 kg m2, the servo's heat capacity, case area and sensor share, the firmware error gain 0.166.
- The damping axis. The derived 1.0025 Nm s/rad (the slope of the published torque-speed line is 1.78 x the C001's) is not a measured BAM value. The variant `sts3250_high_d0.56` keeps the C001's 0.56 as the brief's stand-in; it is run next to the derived value wherever the walk depends on it.
- +19.5 g per knee at the knee axis point in the thigh (the knee servo's body); the servo's own centre is about 12.5 mm away, 3e-6 kg m2 of knee inertia, negligible.
- BLOCKER: a bench BAM identification of one STS3250 at 7.2 V (bam/feetech/record.py pendulum), with a TO1-style heat hold of the same unit. It settles kt, R, the damping and register 21.

## 3. Walk, power path and heat in one loop (the live twin, sim pass only)

The live twin of the shared lab gym (overlay gym/overlays/duck, twin_live, option `knee`), our 2.65 kg build plus 39 g at the knees, the stock BEST_WALK_ONNX_2 with the runtime handling, the as-built network from a full pack, the thermal twin's central set, the C001 and STS3250 protections, start seed none in every run. Before (C001) = the live twin's 2026-11-03 records (TWIN_LIVE.md section 5); the new option leaves the default bitwise unchanged (a 20 s session against the base code: largest difference 0.0 over every 1 s bin). After sessions stop at 50 minutes of session time (a cap set after a container restart) or at the battery guard's walk stop or a fall.

| Model, session, room | Knee | Walk min to the 70 C cut | Peak knee reading | Walking min, end | Knee at its limit, walking | Speed m/s | Pack A, walking |
|---|---|---|---|---|---|---|---|
| backlash, 50/50, 32 C | c001 | no cut | 70 C | 11.93, fall, no protection active | 22.46 % | 0.067 | 5.686 |
| backlash, 50/50, 32 C | sts3250_high | no cut | 49 C | 15.0, fall, no protection active | 0.01 % | 0.0344 | 4.536 |
| backlash, continuous, 25 C | c001 | 7.8 | 71 C | 7.98, fall, heat cut | 20.99 % | 0.0922 | 5.526 |
| backlash, continuous, 25 C | sts3250_high | no cut | 51 C | 19.44, fall, no protection active | 0.01 % | 0.0378 | 4.718 |
| backlash, continuous, 32 C | c001 | 5.5 | 71 C | 5.48, fall, heat cut | 20.54 % | 0.096 | 5.485 |
| backlash, continuous, 32 C | sts3250_low | no cut | 48 C | 19.91, fall, no protection active | 0.03 % | 0.0381 | 4.665 |
| backlash, continuous, 32 C | sts3250_high | no cut | 58 C | 16.4, fall, no protection active | 0.01 % | 0.0314 | 4.843 |
| backlash, continuous, 32 C | sts3250_high_d0.56 | no cut | 63 C | 24.57, battery walk stop | 0.0 % | 0.0862 | 4.616 |
| plain, continuous, 25 C | c001 | 16.4 | 71 C | 16.76, fall, heat cut | 3.47 % | 0.0629 | 4.466 |
| plain, continuous, 25 C | sts3250_high | no cut | 47 C | 27.86, battery walk stop | 0.0 % | 0.0227 | 4.234 |

C001 rows: TWIN_LIVE.md section 5 (no guard). The knee current while walking falls from 1.07 to 1.23 A RMS (C001) to 0.71 to 0.88 A. With the derived damping (1.00) the stock policy walks a third to two fifths as fast and falls in 4 of 5 backlash sessions after 15 to 20 walking minutes; with the C001's 0.56 as a stand-in it walks 0.086 m/s at 32 C and reaches the battery stop.

## 4. Falls, pushes, get-ups and the pack with the track 1b guard (sim pass only)

The track 1b set (v1_elec fix_runs.py: 29 fall-stop shoves, 9 policy-on-the-floor runs, the 24-push ladder, a 20 s walk) with the chosen fix rtg+clip+cap:10, at 7.2 V, our mass plus 39 g. The guard is twin/knee/knee_budget.py for STS3250 knees: bus_budget.py with the knees' own torque limit and current law (with the C001 law it would over-predict a held knee 2.3 to 3.5 x and cut its torque for nothing). The pack current is bus_events.py through the as-built network, both corners, full and nominal pack, with the STS3250 law on the knees.

| | C001 knees (before) | STS3250 high end | STS3250 low end | STS3250, damping 0.56 stand-in |
|---|---|---|---|---|
| Falls: shoves / floor / ladder | 28 of 29 / 8 of 9 / 10 of 24 | 28 of 29 / 8 of 9 / 9 of 24 | same as high | 28 of 29 / not run / 8 of 24 |
| Push that changes | | the 20 N standing push to the left no longer topples it | same | |
| Walk 20 s at 0.15 m/s (plain model) | 1.353 m | **0.277 m** | 0.277 m | 1.321 m |
| Guard steps that cut (shoves / floor / ladder / walk) | 7 / 22 / 22 / 0 | 0 / 5 / 15 / 0 | 0 / 5 / 10 / 0 | |
| Servo bus held 4 ms, worst of shoves / floor / ladder | 9.56 / 9.47 / 10.06 A | 8.66 / 9.40 / 9.69 A | 8.08 / 9.41 / 9.58 A | |
| Pack peak, held 4 ms: floor runs | 16.60, 15.89 A | 14.77, 14.08 A | 13.97, 13.47 A | |
| Pack peak, held 4 ms: shoves and ladder | 14.54, 14.14 A | 15.17, 14.76 A | 13.38, 12.99 A | |
| Over 17 A, boards that trip (17 A after 4 ms) | 0 ms, 0 of 252 replays | 0 ms, 0 of 252 | 0 ms, 0 of 252 | |

- The C001 column reproduces ELECTRICAL_TWIN.md track 1b to the digit (15.89 A floor, 14.14 A ladder): the replay is the same.
- The 1b guard still holds with STS3250 knees: 0 trips at 17 A. The stronger knees raise the push peak by 0.6 A (14.76 A held 4 ms) and lower the floor case by 1.8 A.
- Get-ups (the library's programs, every rest pose of our build, floor friction 1.0): C001 back 19 of 19 at 7.2 V and 19 of 19 at 6.0 V, side 10 of 10 at both. STS3250: back 19 of 19 at 7.2 V but **17 of 19 at 6.0 V** (ramp_10_up and ramp_20_up), side 10 of 10 at both. The stored front program does not load in either run (a ValueError in optimize.py, the same in both): not compared.

## 5. Structure (structure twin load cases re-run, FEA pass only, calc only)

knee_structure.py re-runs the structure twin's own walk cases (stand, forward 0.15, turn 1.0, side 0.2, backlash; 30 solver iterations) and its walk_pushes case with STS3250 knees, and scales the FEA factors of STRUCTURE_TWIN.md with the peak joint loads (linear elastic). Push recovery cannot be scaled from walk_pushes: there the C001 duck falls in 4 of 4 seeds and the STS3250 duck in 0 of 4, so the C001 peaks are floor hits. The push factors use the gym ladder pushes that neither duck falls in instead.

| Walking peak (5 cases) | C001 | STS3250 | Ratio |
|---|---|---|---|
| Knee torque M_axis | 4.28 Nm | 3.19 Nm | 0.75 |
| Knee bending M_bend | 3.77 Nm | 3.98 Nm | 1.06 |
| Knee axial force | 18.4 N | 23.6 N | 1.29 |
| Hip roll bending | 4.23 Nm | 3.46 Nm | 0.82 |
| Hip roll radial force | 60.7 N | 61.8 N | 1.02 |

Push recovery (the gym ladder and shove cases that neither duck falls in, 15 cases, peaks before any fall): knee torque x 0.74, knee bending x 0.69, hip roll bending x 1.04, hip roll radial force x 0.81 (high end); with the 0.56 damping stand-in x 0.85, 1.03, 0.98, 0.83.

| Part (FEA factor, STRUCTURE_TWIN.md) | Walk: before, after | Push: before, after (high end) | Push after, damping 0.56 | Walk after at 50 C (x 0.62) |
|---|---|---|---|---|
| Shin, knee sheet eye (level 2) | 1.63, 2.02 | 1.07, 1.47 | 1.21 | 1.25 |
| Shin, knee sheet eye (level 1) | 1.56, 1.93 | 1.04, 1.42 | 1.18 | 1.20 |
| Shin, P3 knee sheets 5 walls 40 % (level 1) | 1.82, 2.25 | 1.20, 1.64 | 1.36 | 1.40 |
| Thigh, knee servo case holder (level 1) | 2.70, 2.56 | 1.74, 2.35 | 1.69 | 1.59 |
| roll_to_pitch (lowest of levels 1 to 3) | 1.48, 1.45 | 1.08, 1.04 | 1.10 | 0.90 |
| roll_to_pitch, P1 back to 3 walls (level 1) | 1.84, 1.81 | 1.25, 1.20 | 1.27 | 1.12 |

- The knee parts get no worse: the knee torque peak falls 25 % walking and 15 to 26 % in push recovery, because the stronger knee no longer saturates and swings. Only the knee bending walking (x 1.06) and the hip roll loads move up a little.
- **roll_to_pitch drops further below 2** (walk 1.48 to 1.45, push 1.08 to 1.04 at the high end). Fix, the D26 option P1 (back to 3 walls 15 %, +3.6 g and +0.22 h per part), checked with the STS3250 loads: **1.81 walking, 1.20 in push**, above today's 1.48 / 1.08. It still does not reach 2 (as STRUCTURE_TWIN.md found for every print setting); D26 stays open for Ahmed. The knee sheet eye needs no P2 for this swap (walking 2.02 at level 2).
- The thigh's servo holder takes the aluminium case (M2 machine screws): its factor stays over 2 walking (2.56). The hot case still applies (knee sheets 54 to 66 C with C001 heat in the thermal twin); with the cooler STS3250 knee they should run cooler, not quantified (anticipated item 9).

## 6. Runtime settings for the real-code job (STS3250 against the STS3215 C001)

| Item | C001 today | STS3250 | Source | What the runtime does |
|---|---|---|---|---|
| Protocol, bus | Feetech STS half-duplex TTL serial | the same: half duplex asynchronous serial, 8 bit, 1 stop, no parity; 5264-3P GND, Vcc, signal; 1 ms position update | [F5] 7-1, 7-2, 6-7, 12 | nothing: same bus, cable and connector |
| IDs | 23 left knee, 13 right knee | 0 to 253, settable | [F5] 7-3 | write 23 and 13 as today |
| Baud | 1 Mbps | 38400 bps to 1 Mbps, factory 1 Mbps | [F5] 7-4 | nothing |
| Position | 4096 steps, 2048 centre | 4096 steps (0.088 deg), centre 2048 | [F5] 7-6 to 7-8 | nothing: rustypot's 4096-step conversion fits |
| Model number | 777 (pypot's only Feetech entry) | not published | | BLOCKER: read it on the unit; if not 777, pypot (configure_motor.py, check_voltage.py) falls back to 1024 steps and its "go to 0" sends raw 512: add the number to pypot's table or zero with the Feetech tool (SERVO_UPGRADE_OPTIONS.md [U3]) |
| Register 21, position P | factory 32 (BAM); the runtime writes 30 to all leg servos | factory value not published | [F10] | for the C001's stiffness at P 30: **11 (published Kt and R) to 19 (stall line)**; BLOCKER until the bench BAM fit. The runtime writes one P to all 10 leg servos today: it needs a per-ID P (13 and 23), in the duck's walkhooks wrapper |
| 16 Max torque, 48 Torque Limit | 1000 | 1000 (48 takes 16 at power on) | [F10] | keep 1000; register 48 is not the structure fix (section 5) |
| 28 Protection current | factory 310 (2.0 A) | table default 511 (3.3 A); the sheet says 3.8 A; Robo9 reports 4.85 A | [F10], [F5], [R3] | read it on the unit; the twin uses 3.8 A. The knee stall current at 7.2 V is 2.8 to 3.1 A in the twin, so none of the three trips |
| 38, 35, 36, 34 timers and overload | 2 s, 2 s, 80 %, 20 % | 2 s, 2 s, 80 % (sheet), 20 % (table) | [F5], [F10] | leave factory |
| 19 Unload condition, 20 LED alarm | 44 (factory read) | model-specific, not published | [F10] | read on the unit; overheat and over-current must be on, as on the C001 |
| 13 Max temperature | 70 C | 70 C (over 70 C torque off) | [F5], [F10] | keep 70; walk_with_guard.py keeps its 55 C warn and 62 C stop |
| 15 Min input voltage | 40 (4.0 V) | table default 40; the table says high-voltage models "should raise it"; sheet 4 V | [F10], [F5] | keep 40: a unit set near 9 V (the wiki's range) would cut the knees on our 7.2 V bus. Read it on arrival |
| 14 Max input voltage | | 14 V cut | [F5] | nothing on 7.2 V |
| Target guard (track 1b) | bus_budget.py | twin/knee/knee_budget.py (the same guard, the knees' own limit and law) | this job | the real-code job (track 3) runs knee_budget.load() in place of bus_budget for D32 |
| Case screws | M2 self-tapping in plastic | M2 machine thread in aluminium, depth not published | [F9] | BOM_FULL F07, 4 screws; check the depth on the unit |

## 7. Training option (shared lab gym, overlay gym/overlays/duck, train/)

- Flag `knee_servo` (default "sts3215", upstream) and preset `run2_sts3250` = run2 plus STS3250 knees: knee torque limit x 1.5812, knee damping 1.0025 Nm s/rad, kp unchanged (register 21 sets the trained stiffness), +19.5 g per knee at the knee axis point of the thigh, the knee_heat reward and metric x 0.4144 (the high end's copper per Nm^2). The voltage randomization scales the knees with the rest.
- Scene check: knee forcerange 5.1073 Nm, damping 1.0025, thighs 0.16545 and 0.16565 kg (+19.5 g), robot 2.69176 kg, kp 13.37; run2 itself unchanged (3.23 Nm, 0.56, 2.65276 kg, the same scene cache name).
- CPU test (smoke_test.py --only train --train-preset run2_sts3250, 8 envs): 3 of 3 PASS: 480 env steps, 5 evals, 612 s; ONNX against the JAX policy 3.6e-7; the same ONNX interface as the stock policy. Eval reward 17.72 at the first eval and 13.3 at the last; the three middle evals print nan (item 11 of section 8).
- The RunPod retrain waits on Ahmed's key. It should train on the bench BAM values once they exist; until then run2_sts3250 is the high end of the band. No GPU was used and nothing was spent.

## 8. Anticipated problems no job covers yet, each with the check that settles it

1. The stock policy on STS3250 knees depends on the unmeasured damping (section 3). Check: bench BAM fit, then the run2_sts3250 retrain and eval_policy.py --suite full in the gym before the first walk.
2. 7.2 V operation (sheet 6 to 12 V, wiki 9 to 12.6 V) and register 15. Check: one unit at 7.2 V, read register 15, hold a stall.
3. The runtime writes one P to all leg servos; the knees need their own (11 to 19). Check: track 3 writes and reads back register 21 on IDs 13 and 23.
4. The 1b guard must use knee_budget.py; bus_budget.py over-predicts a held knee 2.3 to 3.5 x and would cut its torque in pushes. Check: track 3 runs knee_budget.load() in the real code.
5. Model number and pypot: configure_motor.py "go to 0" may send raw 512. Check: read the model number; dry-run configure_motor.py with the servo off the robot.
6. At a 32 C room the knee reads 58 to 63 C, over the sheet's 60 C range. Check: the unit's heat hold and the first walking logs, with walk_with_guard.py on.
7. Robo9 burnt one STS3250 motor in repeated 100 % load tests. Check: knee current through a get-up and a stall on the bench unit; register 28.
8. Two ramp get-ups fail at 6.0 V. Check: re-tune the back program for STS3250 knees (getup optimize.py) after the BAM fit; evaluate.py at 6.0 V.
9. The aluminium case may warm the printed thigh holder. Check: a thermocouple on the thigh sheet next to the knee servo during the unit hold.
10. The twin's backlash model is the C001's; the STS3250 has 0.5 deg or less [F5], 0.43 deg measured [R3]. Check: the BAM fit with backlash.
11. The training smoke's three middle evals print nan. Check: smoke_test.py --only train --train-preset run2 (stock) shows the same, before the GPU run.
12. A second servo model on each leg chain: the far-servo signal check of track 1b was done with C001s. Check: the bus edge at 1 Mbps with an STS3250 at ID 23.
13. OpenELAB ships from China, 8 to 15 business days, single source (lab rule 6). Check: BOM flag and a second seller before the order.

## 9. BLOCKERs

1. Bench BAM identification of one STS3250 at 7.2 V: kt, R, friction, damping, armature, register 21. It decides the damping axis, on which the stock policy's walk depends (section 3 and 4).
2. 7.2 V operation: the sheet says 6 to 12 V, the FTServo wiki 9 to 12.6 V. Hold one unit at 7.2 V, read register 15 and the stall.
3. STS3250 heat: thermal resistance and time constant (a TO1-style hold at 1.1 A, the C001's 1.5 A torque by the Kt ratio). The twin uses the C001 values (low end) and the Robo9 calibration (high end).
4. Factory registers 19, 21, 22, 28 and the model number, read on the unit.
5. The M2 thread depth of the aluminium case.

## 10. Files, how to run, outputs

| File | What it is |
|---|---|
| servo_sts3250.py | the model, the band, the Robo9 calibration, firmware_P(), apply_knees() for any compiled MuJoCo model; `python3 servo_sts3250.py` writes out/model.json |
| knee_budget.py | the track 1b guard with STS3250 knees (bus_budget.py loaded by path, not edited) |
| knee_structure.py | the structure twin's load cases with STS3250 knees, and the scaled factors (out/structure.json) |
| out/model.json, out/structure.json, out/results.json | small summaries of the runs above |

Gym side (the shared lab gym, overlay gym/overlays/duck, v1_knee/, with DUCK_REPO set to this repo): knee_runs.py sessions, pushes, pack, getup; knee_tables.py for the tables. Every sim ran under the lab's RAM cap (train/ramcap.py, 3000 MB), at most 2 at once.

## Sources

- [F1] Feetech ST-3215-C001 specification, as in twin/thermal/twin_thermal.py PARAMS [F1] and SERVO_UPGRADE_OPTIONS.md [F2].
- [F5] Feetech STS3250 specification A/0, 2024-01-16: SERVO_UPGRADE_OPTIONS.md [F5].
- [F9] FTServo wiki ST-3250-C001 page (input 9 to 12.6 V) and drawings: SERVO_UPGRADE_OPTIONS.md [F9].
- [F10] FTServo wiki STS memory table (registers 13 to 48, defaults 70, 40, 1000, 511, 200, 80, 20): SERVO_UPGRADE_OPTIONS.md [F10], read 2026-11-02.
- [R3] Robo9, "Feetech STS3250 smart actuator: evaluation of accuracy, torque and backlash", https://robonine.com/feetech-sts3250-smart-actuator-evaluation-of-accuracy-torque-and-backlash/ (published 2025-11-28, modified 2026-02-08, read 2026-11-03): section 3.3 heat test, protections (4.85 A), 77.6 RPM no load at 12 V.
- [B1] BAM and the MJCF class sts3215: twin/electromech/servo_sts3215.py.
- Lab files: SERVO_UPGRADE_OPTIONS.md, twin/thermal/THERMAL_TWIN.md, twin/structure/STRUCTURE_TWIN.md (P1 to P3, factors), twin/electrical/ELECTRICAL_TWIN.md (track 1b), sim/ADDED_MASS_SIM.md.
