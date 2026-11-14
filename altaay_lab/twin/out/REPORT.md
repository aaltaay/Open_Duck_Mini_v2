# One duck, one run

Command: `make twin`

Same command, short: `python3 -m altaay_lab.twin.run_twin --short`

This is a simulation. Nothing here was measured on a servo, a cell, or a board.

It walked (sim pass only).
The clock on this run is 45.00 minutes (sim pass only). It stops at the 10 V pack cutoff or at 45 minutes, whichever comes first.
It covered 16.17 m along the path, and ended 1.48 m from the start (sim pass only).
The command is a room circuit: 6 s forward at 0.20 m/s, then a 2.2 s turn, four times around. An earlier run with the forward command held fixed logged 17.29 m of path and only 1.34 m from the start in 2 minutes, because the heading drifts and the path folds into a curve. That was not a room.
Mean speed along the path was 0.006 m/s (sim pass only, path divided by time).
Battery at the end was 74.5 percent of the 4.50 Ah nameplate, 1148 mAh used (sim pass only for the coulomb count, cited for the nameplate).
The pack did not reach the 10.0 V walk cutoff in this run (cited cutoff, sim pass only for the voltage).
Pack voltage in the logged stats was 12.09 V mean and 11.78 V minimum (sim pass only).
Pack peak 12.31 A is this 0.20 m/s room loop on the held 12.0 V rail (sim pass only). The 15.837 A in eval_table_bec12.md is a different case: the 0.40 m/s piece of a speed sequence, and that table still drops the regulator by 0.3 V instead of holding 12.0 V. The same table's 0.15 m/s typical peak is 8.956 A. Both peaks are sim pass only. Neither was measured on a pack.
Hottest reading was the right knee at 62.4 C (sim pass only). The limit on that reading is the 60 C operating line on the servo page used by the thermal model, and the 55.0 C rest in the limits file.
The 55 C rest is inside the walk, not a replay. At 55 C the walk command goes to zero and the policy stands. It rested 1 time. Walking was 2 percent of the bins (sim pass only).
Turning the motor gains fully off tips this walk model over in a few seconds, and the knee joints only reach 90 deg, so the 147 deg sit from the sit study does not fit. The rest is therefore a powered stand. Holding the body up keeps the knee near 55 C, so it does not cool to 45 C and does not start walking again. That limit is sim pass only.
Dock: BLOCKER. The nest sim does not use a camera. It drives on the true pose plus noise. A seat in that sim is not a dock. The mechanical sim used the run C policy and a 12 V rail. It sat (sim pass only). The aim offset table has no 12 V row, so that offset stayed at the 7.2 V measurement. Finding the nest by camera was not simulated.
Charge: the NTC gate is open at a cell temperature of 28.9 C (calc only, bead beta and the BQ24133 divider). Time to put the used 1148 mAh back at 1.006 A is 1.14 hours (calc only).
Limits this run touched: hottest reading 62.4 C crossed the 60 C operating line; hottest reading reached the 55.0 C rest.

## Numbers

| What | Value | Label |
|---|---|---|
| walked | yes | sim pass only |
| duration | 45.00 min | sim pass only |
| path | 16.17 m | sim pass only |
| net travel | 1.48 m | sim pass only |
| rests | 1 | sim pass only |
| body speed | 0.003 m/s | sim pass only |
| duck mass | 2.808 kg | CAD mass model |
| battery left | 74.5 percent | sim pass only |
| nameplate | 4.50 Ah | cited |
| pack mean | 12.09 V | sim pass only |
| pack minimum | 11.78 V | sim pass only |
| pack mean current | 1.53 A | sim pass only |
| pack peak current | 12.31 A | sim pass only |
| servo rail set point | 12.0 V | cited |
| regulator efficiency used | 0.94 | cited |
| walk cutoff | 10.0 V | cited |
| hottest part | right knee | sim pass only |
| hottest reading | 62.4 C | sim pass only |
| rest stop | 55 C | limits file |
| rest resume | 45 C | limits file |
| cell temperature | 28.9 C | sim pass only |
| dock | BLOCKER | BLOCKER |
| charge current | 1.006 A | cited |
| time to replace what was used | 1.14 h | calc only |
| NTC allows charge | yes | calc only |
| fuse | 15 A | cited |
| thermal step | 0.1 s | sim pass only |
| scenario length asked | 45.00 min | the command |

## What this twin does not model

- A camera finding the nest. That is BLOCKER. The nest program uses the true pose plus noise.
- A pack-voltage sensor on the Pi. The 10 V stop is in the guard, and this sim passes the modeled pack voltage in. The Pi still has no sensor (BLOCKER).
- Winding resistance of the C018 as a measured number. The heat model still uses the assumed split from the older sheet.
- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).
- Felt, dirt, and a measured well contact.
- The turn-offset table at 12 V. The dock uses the 7.2 V aim offset with a 12 V rail.
- Hardware. Every temperature, speed, and current above that says sim pass only is a model output.

