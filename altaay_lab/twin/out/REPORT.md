# One duck, one run

Command: `make twin`

Same command, short: `python3 -m altaay_lab.twin.run_twin --short`

This is a simulation. Nothing here was measured on a servo, a cell, or a board.

It walked until the pack cutoff at 2527.62 s (sim pass only).
The clock on this run is 42.13 minutes (sim pass only). It stops at the 10 V pack cutoff or at 45 minutes, whichever comes first.
It covered 247.73 m along the path, and ended 1.32 m from the start (sim pass only).
The command is a room circuit: 6 s forward at 0.20 m/s, then a 2.2 s turn, four times around. An earlier run with the forward command held fixed logged 17.29 m of path and only 1.34 m from the start in 2 minutes, because the heading drifts and the path folds into a curve. That was not a room.
Mean speed along the path was 0.098 m/s (sim pass only, path divided by time).
Battery at the end was 29.9 percent of the 4.50 Ah nameplate, 3154 mAh used (sim pass only for the coulomb count, cited for the nameplate).
The pack hit the 10.0 V walk cutoff at 2527.6 s (sim pass only for the clock, cited for the cutoff).
Pack voltage in the logged stats was 11.32 V mean and 10.00 V minimum (sim pass only).
Pack peak 17.48 A is this 0.20 m/s room loop on the held 12.0 V rail, counting steps whose pack voltage stayed between 8 V and 13.2 V (sim pass only). The 15.837 A in eval_table_bec12.md is a different case: the 0.40 m/s piece of a speed sequence, and that table still drops the regulator by 0.3 V instead of holding 12.0 V. The same table's 0.15 m/s typical peak is 8.956 A. Both peaks are sim pass only. Neither was measured on a pack. No solver step left the 8 V to 13.2 V window.
Hottest reading was the right knee at 55.0 C (sim pass only). The limit on that reading is the 60 C operating line on the servo page used by the thermal model, and the 55.0 C rest in the limits file.
The 55 C rest is inside the walk. At 55 C the command goes to zero and the policy stands. Folding to the sit from a walk tips this model, so the session does not fold. It rested 3 times. Upright walking is the figure in the table (sim pass only).
The rest check reached a right knee of 147 deg, then torque off. Stance current was 0.47 A, the 20 deg crouch was 0.42 A, and torque off was 0.000 A (sim pass only). From a 55 C start, torque off reached 45 C in 3.51 min. The powered stand reached 45 C in 4.11 min. Both clocks are sim pass only, on the cited 1.0 ohm.
Knee high stop used here is 147 deg, the register soft stop. The CAD bumper is 150 deg (software/servo_limits.json, CAD check only). The walk model was compiled at 90 deg, and this run raises that stop before the sit.
Dock: BLOCKER. The nest sim does not use a camera. It drives on the true pose plus noise. A seat in that sim is not a dock. The mechanical sim used the run C policy and a 12 V rail. It sat (sim pass only). The aim offset table has no 12 V row, so that offset stayed at the 7.2 V measurement. Finding the nest by camera was not simulated.
Charge: the NTC gate is open at a cell temperature of 56.7 C (calc only, bead beta and the BQ24133 divider). Time to put the used 3154 mAh back at 1.006 A is 3.13 hours (calc only).
Limits this run touched: pack current 17.48 A crossed the 15.0 A fuse; pack fell to 10.00 V, under the 10.0 V walk cutoff; hottest reading reached the 55.0 C rest.

## Numbers

| What | Value | Label |
|---|---|---|
| walked | yes | sim pass only |
| duration | 42.13 min | sim pass only |
| path | 247.73 m | sim pass only |
| net travel | 1.32 m | sim pass only |
| rests | 3 | sim pass only |
| body speed | 0.069 m/s | sim pass only |
| duck mass | 2.949 kg | CAD mass model |
| battery left | 29.9 percent | sim pass only |
| nameplate | 4.50 Ah | cited |
| pack mean | 11.32 V | sim pass only |
| pack minimum | 10.00 V | sim pass only |
| pack mean current | 4.49 A | sim pass only |
| pack peak current | 17.48 A | sim pass only |
| servo rail set point | 12.0 V | cited |
| regulator efficiency used | 0.94 | cited |
| walk cutoff | 10.0 V | cited |
| hottest part | right knee | sim pass only |
| hottest reading | 55.0 C | sim pass only |
| rest stop | 55 C | limits file |
| rest resume | 45 C | limits file |
| cell temperature | 56.7 C | sim pass only |
| dock | BLOCKER | BLOCKER |
| charge current | 1.006 A | cited |
| time to replace what was used | 3.13 h | calc only |
| NTC allows charge | yes | calc only |
| fuse | 15 A | cited |
| thermal step | 0.1 s | sim pass only |
| scenario length asked | 45.00 min | the command |
| walking minutes | 30.07 min | sim pass only |
| terminal resistance | 1.0 ohm | cited |
| knee high stop | 147 deg | CAD check only |
| sit knee reached | 147 deg | sim pass only |
| torque-off cool from 55 C | reached 45 C in 3.51 min | sim pass only |
| powered-stand cool from 55 C | reached 45 C in 4.11 min | sim pass only |

## What this twin does not model

- A camera finding the nest. That is BLOCKER. The nest program uses the true pose plus noise.
- A pack-voltage sensor on the Pi. The 10 V stop is in the guard, and this sim passes the modeled pack voltage in. The Pi still has no sensor (BLOCKER).
- A bench measurement of the C018 terminal resistance. The heat uses the 1.0 ohm printed in specification A/0 item 5-10. The stall line 12 V / 2.7 A is 4.444 ohm on the same sheet, and the old 3.753 ohm figure was that stall line times the C001 winding share. The audit is altaay_lab/twin/thermal/HEAT_AUDIT.md.
- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).
- Felt, dirt, and a measured well contact.
- The turn-offset table at 12 V. The dock uses the 7.2 V aim offset with a 12 V rail.
- Hardware. Every temperature, speed, and current above that says sim pass only is a model output.

The duck mass is the whole robot. The trunk body alone is 1.207 kg. The stock Open Duck Mini model is 2.107 kg. MuJoCo loads 2.949 kg, and the parts rollup is 2.949 kg. The rollup includes three P45B cells at the cited 70 g, the i7C at the cited 75 g, the 3S protection board, the BQ24133 board, and three limb breakers. The protection-board grams are the cited size times 1.2 g/cm3 (calc only). The BQ24133 assembled grams and the breaker package grams are not on a datasheet.

## What was compared

Each row replays this run's walking current for 45 min. The rest is the measured stance current, the measured crouch current, or torque off. Sim pass only. Mass is the change from the C018 knees. No new part is on the bill.

| Option | Walking minutes | Knee peak C | Added mass g | Kind |
|---|---|---|---|---|
| cited 1.0 ohm, powered stand | 33.1 | 55.0 | 0 | this run |
| cited 1.0 ohm, torque-off sit | 33.7 | 55.0 | 0 | sit check |
| old stall-line 4.444 ohm, torque-off sit | 6.0 | 55.1 | 0 | comparison |
| old stall-line 4.444 ohm, powered stand | 1.1 | 55.0 | 0 | the 3 percent run |
| knee current times 0.70 | 45.0 | 42.8 | 0 | retrain |
| 20 deg knee crouch, torque on | 33.2 | 55.0 | 0 | stance |
| knee area times 1.3 | 45.0 | 51.7 | 0 | heatsink |
| knee area times 1.8 | 45.0 | 45.1 | 0 | heatsink |
| STS3250 knees, cited 1.2 ohm | 26.0 | 55.0 | 39 | servo swap |
| gear ratio times 1.5 | 45.0 | 41.4 | 0 | not a catalog part |

Chosen: the cited 1.0 ohm terminal resistance, and a stand with the command at zero when the reading reaches 55 C. This session's upright walking is 30.1 min with the knee at 55.0 C, and it adds no mass. The 45 min replay of the walking current, resting at the measured stance current, walks 33.1 min with the knee at 55.0 C. A separate check folds to 147 deg from a settled stand and turns the gains off. Folding from a walk tips this model, so that fold is not the session rest. The heatsink rows assume extra case area. The servo swap and the gear row are studies. No decision entry. A lower knee current would need a retrain, and this session did not run one.

