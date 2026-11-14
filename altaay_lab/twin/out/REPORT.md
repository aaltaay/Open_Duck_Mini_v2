# One duck, one run

Command: `make twin`

Same command, short: `python3 -m altaay_lab.twin.run_twin --short`

This is a simulation. Nothing here was measured on a servo, a cell, or a board.

It walked (sim pass only).
The clock on this run is 2.00 minutes (sim pass only).
It covered 17.29 m along the path, and ended 1.34 m from the start (sim pass only).
Body speed was 0.123 m/s at a 0.15 m/s command (sim pass only).
Battery at the end was 96.3 percent of the 4.50 Ah nameplate, 167 mAh used (sim pass only for the coulomb count, cited for the nameplate).
Pack voltage at the end of the logged stats was 12.16 V, minimum 11.87 V (sim pass only). The walk cutoff is 10.0 V (cited).
Hottest reading was the right knee at 55.0 C (sim pass only). The limit on that reading is the 60 C operating line on the servo page used by the thermal model, and the 55.0 C rest in the limits file.
The heat model spent 56 percent of the run walking. The remainder is the torque-off rest (sim pass only). That rest is not the code on the Pi.
Dock: BLOCKER. The nest sim does not use a camera. It drives on the true pose plus noise. A seat in that sim is not a dock. The mechanical sim at 7.2 V, stock policy, sat (sim pass only). That voltage is the sim's own table, not the 12 V rail.
Charge: the NTC gate is open at a cell temperature of 25.6 C (calc only, bead beta and the BQ24133 divider). Time to put the used 167 mAh back at 1.006 A is 0.17 hours (calc only).
Limits this run touched: hottest reading reached the 55.0 C rest.

## Numbers

| What | Value | Label |
|---|---|---|
| walked | yes | sim pass only |
| duration | 2.00 min | sim pass only |
| path | 17.29 m | sim pass only |
| net travel | 1.34 m | sim pass only |
| body speed | 0.123 m/s | sim pass only |
| battery left | 96.3 percent | sim pass only |
| nameplate | 4.50 Ah | cited |
| pack mean | 12.16 V | sim pass only |
| pack minimum | 11.87 V | sim pass only |
| pack mean current | 5.02 A | sim pass only |
| pack peak current | 9.69 A | sim pass only |
| servo rail set point | 12.0 V | cited |
| regulator efficiency used | 0.94 | cited |
| walk cutoff | 10.0 V | cited |
| hottest part | right knee | sim pass only |
| hottest reading | 55.0 C | sim pass only |
| rest stop | 55 C | limits file |
| rest resume | 45 C | limits file |
| cell temperature | 25.6 C | sim pass only |
| dock | BLOCKER | BLOCKER |
| charge current | 1.006 A | cited |
| time to replace what was used | 0.17 h | calc only |
| NTC allows charge | yes | calc only |
| fuse | 15 A | cited |
| thermal step | 0.1 s | sim pass only |
| scenario length asked | 2.00 min | the command |

## What this twin does not model

- A camera finding the nest. That is BLOCKER. The nest program uses the true pose plus noise.
- The policy pausing inside MuJoCo at 55 C. The rest rule is applied when the heat model replays the current bins. The two are not one closed loop.
- A pack-voltage sensor on the Pi. The 10 V stop is in the guard, and this sim passes the modeled pack voltage in. The Pi still has no sensor (BLOCKER).
- Winding resistance of the C018 as a measured number. The heat model still uses the assumed split from the older sheet.
- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).
- Felt, dirt, a measured well, and a whole-duck mass. Mass of the walking body is the existing added-mass model (GAP in the parts file).
- Joint angle limits from the parts file. They are not in the netlist, the limits file, or the order (GAP).
- Hardware. Every temperature, speed, and current above that says sim pass only is a model output.

