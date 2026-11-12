# Knee heat study: is 3.3 minutes and 94.7 C real?

Written 2026-11-11 9:58 PM ET. Calc only, except numbers marked sim pass only (they come from logs already in the repo) or CAD check only. No policy was trained. The walking policy was not re-run: that needs the public playground pin, and a new gait would also need a retrain (paid GPU, Ahmed's OK). The shared lab gym (overlay gym/overlays/duck) was not used.

## Plain words

The 3.3 minute and 94.7 C figures are real outputs of the thermal model. An independent integration of the same two-node equations on the same walk log reproduces them. They are not a measured knee.

**The 94.7 C body is OVERSTATED** as a temperature the knee would reach. It is the temperature only if two things are both true: the sheet's torque-off above 70 C is switched off, and the motor current is held frozen while the copper resistance rises. With the torque-off left on, the case is about 63 C when the internal reading hits 70 C, and it peaks near 64 C. It does not go on to 95 C.

**The 3.3 minutes to a 60 C reading is the short end of the same model.** Read as the time for every walk, it is OVERSTATED by about 1.5 to 2.5 times, not by ten times.

- Same log, copper resistance left at the 25 C value: 4.6 minutes (calc only).
- Same log, current falling as a hot winding would when the voltage is already at the cap: 6.4 minutes, and the reading never reaches 70 C (calc only).
- The softer plain walk, using the copper already published for that walk: about 6 to 8 minutes to 60 C, and about 9 to 10 minutes to 70 C (calc only). That 9 to 10 minutes is the old "10 minutes."

Continuous walking in this model still crosses the 60 C operating range inside about 8 minutes in every one of those cases. The rated current, 0.65 A, does not: the case settles near 40 C (calc only). So the alarm is early, and the 95 C case is not the protected servo, but a long continuous walk of this gait does leave 60 C.

The old 10 minute line and the new 3.3 minute line are not a disagreement about the same question. The 10 minutes was the plain walk reaching the 70 C torque cut. The 3.3 minutes is the backlash walk reaching the 60 C operating line. The backlash walk's time to 70 C stayed at about 4 to 4.5 minutes (old 4 and 4.3, this log 4.5).

## What was checked

- The walk log is `twin/electromech/out/p45b_sheet/session_bam_backlash_typical.csv` (sim pass only). It is the trained actuator on the P45B pack, backlash model, typical corner. It is not the sheet-stall servo. That servo falls at 3.5 s (ELECTROMECH_TWIN.md, sim pass only) and has no 3 minute walk.
- Right knee is servo id 13. Over the first 4 minutes the motor current is 1.45 A RMS (sim pass only, this log). Over the whole 42.8 minute log it is 1.38 A RMS. Stall current on the sheet is 2.5 A. This walk is not a stall.
- Copper uses 2.5 ohm, STS3215 sheet A/1 item 5-10, opened this session: https://files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf
- The thermal mass and the loss to air are the central corner of THERMAL_TWIN.md. The mass is a recipe (cited plastics and metals, glass share GUESS). The loss to air is a convection correlation (GUESS as applied to this case). The only published STS3215 temperature curve (Robo9) agrees with the time constant, not with a known heat input, so it does not by itself prove the minutes.

## Part 1. The hand check

### Current and copper (the log is sim pass only, the watts below are calc only)

| Window | Right knee current | Copper, I squared times 2.5 ohm | Driver, I squared times 0.13 ohm |
|---|---|---|---|
| First 4 minutes | 1.45 A RMS | 5.24 W | 0.27 W |
| Whole 42.8 minute log | 1.38 A RMS | 4.75 W | 0.25 W |

The 0.13 ohm is the gap between the BAM loop (2.63 ohm, the resistance the log's own copper column uses) and the 2.5 ohm sheet terminal resistance. The sheet's stall line is 7.4 V / 2.5 A = 2.96 ohm, so the sheet itself leaves 0.46 ohm outside the 2.5 ohm figure. Using 0.13 ohm instead of 0.46 ohm understates driver heat by about 0.7 W at 1.45 A. That is about 13 percent of the copper. It does not make a 3 minute result into a 10 minute result.

Rated point on the same sheet: 0.65 A at 5 kg.cm, copper 1.06 W. The walk is 2.2 times the rated current and about 5 times the rated copper. Life test on the sheet is 1/5 of stall torque, about 3.9 kg.cm (0.38 Nm). The sim knee RMS torque is 2.19 Nm (sim pass only, sim/ADDED_MASS_SIM.md, backlash, our build). That torque is above the sheet stall of 19.5 kg.cm (1.91 Nm). The bought servo cannot produce the torque this heat is based on.

Gearbox loss is not in the new thermal run. The older thermal twin put about 0.36 W of friction on this knee (the gap between 5.95 W total and 5.17 W of winding at 1.44 A). Putting 0.36 W back moves 3.22 minutes to 3.04 minutes (calc only). The omission makes the knee slightly cool, as THERMAL_TWIN.md already says. Feetech does not publish gearbox efficiency. A guessed 40 percent loss on a few watts of mechanical power would be another watt or so (GUESS). That would heat the knee more, not less. It is not the source of a too-hot headline.

Idle electronics are 21 mA (sheet item 5-6), about 0.15 W. Small next to 5 W.

### Thermal mass and loss to air

Central corner, recomputed from the published recipe:

- Heat capacity 33.4 J/K for the 55 g servo. Case plastic about 11.5 g, the rest of the metal and gears about 41 g. Glass share and whether the lead is inside the 55 g are GUESS. The Faulhaber motors of this size (1724, 2224, 2232) have a housing time constant of 310 to 500 s. With this heat capacity and a body-to-air resistance near 10 K/W, the time constant is about 5 to 6 minutes. That matches the Robo9 fit of 316 s (231 to 435 s) on a bare servo. The time constant is the part of the model that has a check. The watts do not.
- Effective case area 0.0060 m2 (geometry.json, CAD check only: outer case 6690 mm2, knee exposure about 0.90 after the central mounting factors).
- Loss to air at a 40 C rise and 0.2 m/s of walking air: about 18 W/m2K, so about 9.5 K/W (calc only). The 0.2 m/s is GUESS. Still air on a bench is about 11 to 13 K/W in the same correlation. THERMAL_TWIN.md's bare-servo figure is 11.2 to 11.6 K/W.

A single lump, 5.2 W into 33 J/K and 9.5 K/W, starting at 25 C, would reach a 60 C body in roughly 5 minutes and settle near 75 C. The published 3.3 minutes is faster than that lump because the internal reading is not the case. The model puts the sensor 10 percent of the way from the case to the winding (w = 0.1, a fit range 0.03 to 0.19 on a different servo, GUESS for this one). The winding node is only 2.5 J/K (GUESS, Faulhaber class). It heats in seconds, and the reading follows it.

### Reproducing 3.3 minutes and 94.7 C

Same equations as gate_p45b.py, right knee, 25 C room, central corner, friction left out, current held fixed while resistance rises (calc only):

| Event | This integration | Published in gate_p45b.json |
|---|---|---|
| Reading crosses 60 C | 3.22 min. Case 53 C. Winding 121 C | 3.33 min (first 10 s sample after the crossing) |
| Reading crosses 70 C | 4.47 min. Case 63 C. Winding 134 C | 4.50 min (same 10 s grid) |
| Case, torque left on for 40 min | 94.67 C. Reading 102 C. Winding 172 C | 94.67 C case, 102.36 C reading, 172.41 C winding |
| Case, torque off when the reading hits 70 C | peaks at 64 C | not what that file reports |

The 94.67 C match is exact. The 0.1 minute gap on the clock is the log grid: the thermal run records every 10 s, and 3.22 minutes falls between 190 s and 200 s, so the file says 3.33 minutes. There is no units bug in the integrator.

At 32 C the same run crosses 60 C at 2.5 minutes in the published file. That shift is the warmer start. It is not a different current.

### What the 94.7 C run assumes, and what changes if you drop it

| Assumption | Time to a 60 C reading | Hottest case | Label |
|---|---|---|---|
| As published: current frozen, resistance rises, no torque-off | 3.22 min | 94.7 C | calc only |
| Resistance held at the 25 C value, no torque-off | 4.55 min | 73.6 C | calc only |
| Current falls as 1/R (voltage already at the cap), no torque-off | 6.42 min | 64.3 C. Reading peaks at 68 C | calc only |
| Published run, but torque off at a 70 C reading (the sheet) | 3.22 min | 64 C | calc only |
| Plain-walk copper from THERMAL_TWIN.md (1.19 A, winding 3.52 W), resistance rises | 5.8 min | 76 C | calc only |
| Same plain copper, resistance held cold | 8.4 min | 64 C. Reading peaks at 68 C | calc only |
| Rated 0.65 A, resistance rises | never | about 41 C | calc only |
| Standing 0.48 A (THERMAL_TWIN.md) | never | about 34 C | calc only |
| Sheet stall, 2.5 A, held | 0.7 to 1.0 min | runs away if you never cut torque | calc only. This is not the walk |

The fixed-current resistance rise is the step that builds 94.7 C and a 172 C winding. A hot winding really does have more resistance (copper, 0.393 percent per C, Engineering ToolBox, the source already in THERMAL_TWIN.md). If the servo is still inside its voltage and the torque demand holds the current up, the watts rise. If the servo is already against the voltage cap, the current falls and the watts fall. The knees sit on the torque limit 19 to 31 percent of the time (ELECTROMECH_TWIN.md, sim pass only), so both happen. The published run uses only the rising side. The live twin found the other side: a hot winding drew less current, and the cut came later (STATE.md). Using only the rising side overstates the late temperature. It moves the 60 C clock from about 4.6 minutes to 3.2 minutes. It is not the whole of the 3.3 minute claim.

### Bugs, in plain words

- Not a stall used as a walk. The log is 1.45 A, not 2.5 A.
- Not a wrong room. The 25 C run starts at 25 C. The 32 C run is a second case.
- Not a missing decimal or a mm/m error. The case area, the 2.5 ohm, and the 33 J/K reproduce 94.67 C.
- The 70 C torque-off is in the model and was turned up to 200 C on purpose, so the clock could be read. The 94.7 C sentence is what that choice produces. It is labeled "if the torque stays on" in THERMAL_TWIN.md. It is still the wrong number for a servo that follows item 7-11.
- Friction heat is missing. That makes the result slightly cool (about 0.2 minutes).
- The reading is not the case. At the 60 C reading the case is 53 C. The knee sheets touch the case. At the moment of the torque-off the case is 63 C, which is still above the PLA heat-deflection band of 49 to 57 C cited in THERMAL_TWIN.md. Throwing out 94.7 C does not make the plastic cold. It puts the sheets near 63 C instead of 95 C.
- The winding temperatures (121 C at the 60 C reading, 172 C at the end) sit on the guessed 2.5 J/K node. Feetech publishes no winding limit. Do not quote 172 C as a measured copper temperature.

### What changed between the 10 minute result and the 3.3 minute result

| | Before PR 33 (2026-11-03) | After PR 33 (this log) |
|---|---|---|
| Walk | Plain model, about 1.19 A, and backlash, about 1.44 A | Backlash P45B session, 1.45 A in the first 4 minutes |
| Clock | Time to the 70 C torque cut | Time to the 60 C operating range, torque-off disabled |
| Plain, 25 C, to 70 C | 10 minutes | not re-run; the old copper still gives about 9 minutes (calc only) |
| Backlash, 25 C, to 70 C | 4 minutes open-loop, 4.3 minutes on the closed-loop session | 4.5 minutes |
| Backlash, 25 C, to 60 C | not the headline | 3.3 minutes |
| Friction | included | omitted (slightly cool) |
| Pack | P30B in the old electronics section | P45B cells in the trunk. The knee current is the servo current, not the cell |

PR 33 did not find a new, much larger knee current. It started quoting the 60 C line on the backlash walk. The 10 versus 3.3 is that change of question, plus the backlash walk being hotter than the plain walk (1.44 A against 1.19 A, copper about 1.5 times).

### Public reports

Searched 2026-11-11: GitHub issues in apirrone/Open_Duck_Mini, Open_Duck_Mini_Runtime, and Open_Duck_Playground for temperature, overheat, and heat. No hits. The STS3215 issues that do exist are issue 48 (the spec question), issue 52 (12 V knees, no temperature), and issue 21 (12 V servos, feet trembling, no temperature). Nobody has posted a 60 C or a 95 C knee on this robot. That is an absence, not a measurement. Few builders, and short walks would not show a 10 minute effect.

- Robo9, STS3215 C018, 12 V, and the same rows in TheRobotStudio/SO-ARM100 issue 134: https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/ . A 15 kg.cm hold (1.47 Nm) went from about 25 C to 48 C in 10 minutes and then sat there for an hour. It did not reach 60 C. Oscillating, already at 48 C, it took about 50 minutes more to reach 60 C. That is a lighter torque than this sim walk, on the 12 V servo, and it is the only curve with a clock. It does not look like 60 C in 3 minutes.
- Robo9's later comparison, https://robonine.com/smart-serial-servo-motor-comparison-robotics/ : STS3215 at 22 kg.cm and 0.75 A, internal 31 to 41 C in 2 minutes. STS3250 at 35 kg.cm and 1.6 A, 30 to 55 C in 2 minutes. Repeated full-load tests burnt one STS3215 board and one STS3250 motor. The two loads are not equal, so this does not say the STS3250 runs hotter at the same torque.
- phospho-app/phosphobot issue 241: a gripper held closed reached 50 C in 30 to 60 seconds, and one servo went over 70 C and was damaged. That is a hard hold. In this model a 2.5 A stall reaches 60 C in about a minute (calc only). The walk is not that hold.

The public moderate-load curve (48 C plateau) and this model's 5 W walk can both be true, because 5 W is several times the heat that fits a 23 C plateau into a 10 K/W case. The open question is whether a real duck knee draws 1.45 A. Nothing in the issues answers that. TEST_PLAN 7.3 is still the measurement.

## Part 2. Why the sim knee is hot

The heat is I squared R, and the current is high because the walk asks the knee for more torque than the datasheet servo can stall at. The pieces:

| Source | Number | Share of the heat | Label |
|---|---|---|---|
| Walking current | 1.45 A RMS, first 4 minutes | 5.2 W copper | sim pass only log, calc only watts |
| Rated current | 0.65 A | 1.06 W. The walk is about 5 times this | sheet |
| Standing, torque on | 0.48 A, 0.69 Nm at the knee | 0.58 W copper, case settles near 34 C. About one tenth of the walking copper | 0.48 A from THERMAL_TWIN.md, 0.69 Nm from STRUCTURE_TWIN.md, both sim pass only |
| Stall | 2.5 A, 1.91 Nm | not the walk | sheet |
| Robot mass | trained 2.107 kg, walk model 2.65 kg, later budget 2.72 kg and 2.81 kg with the sit parts | right knee actuator RMS 2.18 Nm at the trained mass, 2.19 Nm at our build. Time on the 3.23 Nm stop 22 percent against 23 percent | sim pass only, ADDED_MASS_SIM.md and MASS_BUDGET.md |
| Crouch | thigh and shin 78.7 mm each in the repo MJCF | see below | CAD check only for the length. Torque is the sim number above |
| Gear ratio | 1:345 | already inside the sheet Kt. It does not add a second copper term | sheet item 6-10 |
| Bus voltage | BEC near 7.2 V, knee near 7.1 V at a full pack | the hot minutes are at a full pack. Copper falls as the pack sags (5.6 W at full to 4.6 W nominal on the right knee) | ELECTROMECH_TWIN.md, sim pass only |
| Position gain | 17.11 in the backlash model, 13.37 in the plain model | backlash knee 1.44 A and 2.19 Nm RMS, plain forward knee 1.19 A and 1.79 Nm RMS. Copper ratio about 1.5 | SERVO_UPGRADE_OPTIONS.md and ADDED_MASS_SIM.md, sim pass only |

Mass is not the cause. The knee is already on the torque stop for about a quarter of the backlash walk. Another 0.5 kg barely moves the RMS torque. Cutting the duck back to 2.107 kg would not make this knee cool.

The crouch is real, and it is the small term. A static hold of 0.69 Nm on one planted leg is a moment arm of 53 mm if the leg holds half of 2.65 kg, or 27 mm if it holds all of it (calc only). The thigh is 79 mm, so that is a bent knee, not a straight one. On equal links with the hip and ankle on one vertical line, that arm is about 40 to 85 degrees of knee bend (calc only, that geometry assumption). The repo MJCF with the trunk fixed, so the body weight does not load the joint, gives only 0.03 to 0.11 Nm at the knee across that bend (sim pass only, this CAD, mass 2.06 kg). The 0.69 Nm is the body, not the shin.

Walking RMS torque is 2.19 Nm, about 3 times the stand. Copper scales like torque squared when speed is ignored, and the current ratio matches that: (1.45 / 0.48) squared is about 9. About nine tenths of the walking copper is the moving gait, not the weight held still.

The gait is hot because the position loop is stiff and the tracking error is large. The closed loop holds the knee 7.4 to 8.8 degrees RMS off the target (ELECTROMECH_TWIN.md, sim pass only). A gain of 17.11 times 8 degrees is 2.4 Nm, which is the whole RMS torque and close to the 3.23 Nm stop. The loop turns a few degrees of miss into a near-limit torque. The softer identification (gain 13.37) is the plain walk, and that walk draws 1.19 A instead of 1.44 A. The servo is not fighting a second servo. It is fighting its own target.

The sheet Kt is 7.8 kg.cm/A (0.765 Nm/A). The sim actuator is about 1.21 Nm/A. For the same 2.19 Nm the sheet motor would want 2.9 A, and its stall is 1.91 Nm at 2.5 A, so it cannot. That is why the sheet-stall walk falls at 3.5 s. The 1.45 A heat belongs to the trained actuator. Quoting it as the servo on the bill mixes two motors.

## Part 3. Fixes, ranked

Heat reduction is for a continuous walk unless the row says it only shortens the walk. Cost class uses the bill that already exists: none, the knee servos already on the bill, or a new part. No new prices.

| Rank | Option | Heat | Cost class | Effort | Risk | Number |
|---|---|---|---|---|---|---|
| 1 | Torque off between walks, and stop the walk when the reading hits 55 C | Does not lower the watts while walking. It keeps the reading at the cap | none | small, software. The sit already drops torque | A warm room cools slower. The walk still cannot be continuous | calc only, this log's 1.45 A held steady: in 90 minutes, torque-off rests give 26 walking minutes at 25 C and 17 at 32 C, peak reading 55 C. Torque-on rests give 19 and 9 minutes. The live twin, sim pass only, found a torque-on stand at 32 C settling near 48 to 50 C, so a 45 C restart may never come. Torque-off is the rest that cools |
| 2 | STS3250 knees (decision D32) | 0.24 to 0.41 times the copper per newton-metre squared, sheet against sheet | the two knee servos already named on the bill | bench of one unit, then a retrain. The retrain is not run here | Stock policy falls (4 of 5 backlash sessions, KNEE_TWIN.md, sim pass only). The 1.2 ohm and the stall line disagree. One public full-load test burnt a motor | Opened sheet A/0, 2024-01-16: https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772424007467984928587.pdf . Rated input 6 to 12 V, so 7.2 V is inside this sheet. Stall 50 kg.cm at 4.2 A and 12 V, Kt 11 kg.cm/A, terminal resistance 1.2 ohm. 12 V / 4.2 A is 2.86 ohm, not 1.2 ohm. Operating range -20 to 60 C, torque off above 70 C, aluminium case, 74.5 g, gear 1:345. At 7.2 V, scaling the stall line gives 30 kg.cm and 2.5 A (calc only). Knee twin, sim pass only: no 70 C cut, knee 47 to 63 C, and 63 C is 3 C over 60 C at 32 C. Current while walking 0.71 to 0.88 A against 1.07 to 1.23 A on the C001 in that same sim |
| 3 | Softer position gain, the plain identification (13.37 against 17.11) | About 0.68 times the copper. Time to 60 C from about 3 to 5 minutes to about 6 to 8 minutes | none | a register change and a bench walk. Not a retrain unless the walk falls | The policy was trained with a gain. Softening it can worsen the walk. Not tested as a heat fix on hardware | calc only from the published plain copper. The two gains are already in SERVO_UPGRADE_OPTIONS.md |
| 4 | Clip-on heat sink, about 30 percent more case area | Backlash walk still climbs. Reading peaks near 92 C if torque stays on | a small part, not sourced | fit against the moving sheets | Clearance at both knee limits | calc only, same 1.45 A, area times 1.3. THERMAL_TWIN.md already had the plain walk staying under the cut at 25 C with this area, and the backlash walk still cutting |
| 5 | Passive spring sized for the 0.69 Nm stand | About a tenth of the walking copper, if that 0.69 Nm is the mean and the spring does not fight the swing | a new part | design and a retrain if the gait changes | It can push the swing the wrong way | calc only: sqrt(2.19 squared minus 0.69 squared) is 2.08 Nm, copper ratio 0.90. The waveform was not in this repo, so the tenth is a bound, not a measured saving |
| 6 | Straighter knees, less crouch | The stand is the small term. Zeroing it leaves about nine tenths of the copper if the dynamic torque stays | none in parts | a new gait. That is a retrain | The stock policy may fall. Not estimated as a free change | BLOCKER for a new walk. No playground re-run in this session |
| 7 | Cut mass back toward 2.107 kg | About 1 percent on this knee | print and part choices already studied | large for a 1 percent knee effect | none thermal | sim pass only, ADDED_MASS_SIM.md, 2.18 Nm against 2.19 Nm |
| 8 | Extra gearing or a linkage with more advantage | A 1.5 times reduction would be about 2.3 times less copper if the torque scales and the speed still fits | a new part | CAD and a retrain | The 1:345 rotor already limits faster walks (the speed study). Slower is the wrong way if the duck is already slow | BLOCKER for a geared walk. Estimate only |
| 9 | 12 V STS3215 (C018 or C047) or STS3235 on this 2S pack | Less copper per newton-metre at 12 V, but at 7.2 V the no-load speed falls to about 2.8 rad/s | a pack change if they are to be fast | bay, BEC, retrain | Too slow on the bus we have | SERVO_UPGRADE_OPTIONS.md, from the C018 sheet. Not re-opened this session |
| 10 | Vents and a trunk fan | No effect on the knee. The knee is outside the trunk | a fan, not sourced | drill and wiring | none for this question | THERMAL_TWIN.md section 6, sim pass only |

The 12 V STS3215 numbers above are the ones already in SERVO_UPGRADE_OPTIONS.md. This session opened the C001 sheet and the STS3250 sheet, not the C018 PDF.

## Recommendation

Do these two, in this order.

1. **Treat continuous walking as a short bout, and drop torque when the duck is not walking.** This needs no parts and no GPU. A guard that stops at a 55 C reading and a torque-off rest keeps the reading at the cap in the calc above (17 to 26 walking minutes in a 90 minute session). The 94.7 C body is not the number to design to. The number to design to is a 60 C reading in a few minutes of continuous backlash walking, and a case near 63 C if the sheet's torque-off is what actually stops it. The knee sheets still see a temperature in the PLA softening band. That is a real limit on long walks. It is not a 95 C case.

2. **Keep the STS3250 as the hardware path for a long walk, and do not walk the stock policy on it.** The opened sheet is 0.24 to 0.41 times the C001 copper per newton-metre squared, and 7.2 V is inside its 6 to 12 V rated input. The knee twin already shows the stock policy falling, and a warm room still touching 63 C. A retrain is required before that swap is a walking duck, and a retrain needs Ahmed's OK and paid GPU. Before any pair is bought, one unit should be held at a known current (TEST_PLAN 15 and 7.3). The sheet's 1.2 ohm and its 4.2 A stall do not describe the same resistance, and a public full-load test burnt one motor. This study does not buy that unit.

The softer gain is the check to make on the first C001, before spending GPU. The lab already has the two numbers: 1.19 A against 1.44 A. If a bench walk at the softer gain still stands, the clock roughly doubles for nothing. If it falls, the gain is not a free fix and the retrain remains the path.

Springs, a lighter duck, a heat sink, and a new linkage do not move this knee enough to come before those two. Mass in particular is the wrong suspect.

## What was not run

BLOCKER: a new walking simulation with a different crouch, a spring, a softer gain on the stock policy, or a new linkage. The policy loop is the public playground at the pinned commit, it is not in this repo, and a new gait needs a retrain. The shared lab gym was not used. No result here is from a fresh policy run.

What did run: the hand integration above (calc only), and a static pose on the repo MJCF (sim pass only, trunk fixed, mass 2.06 kg). The static pose does not carry body weight on the knee. The 0.69 Nm stand remains the structure twin's number.

## Sources opened this session

- STS3215 sheet A/1, 2023-06-23, Seeed copy: https://files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf . Operating -20 to 60 C (item 1-2). Torque off above 70 C (item 7-11). Terminal resistance 2.5 ohm, Kt 7.8 kg.cm/A, stall 19.5 kg.cm at 2.5 A and 7.4 V, rated 5 kg.cm at 0.65 A, idle 21 mA, gear 1:345, 55 g, PA+GF, core motor. No thermal resistance, no time constant, no winding class.
- STS3250 sheet A/0, 2024-01-16: https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772424007467984928587.pdf . Numbers in the table above.
- Robo9 STS3215 test and SO-ARM100 issue 134, Robo9 comparison, phosphobot issue 241. Links in the public-reports section.
- GitHub issue search of the three upstream repos, 2026-11-11, no heat hits. Issue 48, issue 52, and issue 21 are the STS3215 threads, and none of them gives a temperature.
