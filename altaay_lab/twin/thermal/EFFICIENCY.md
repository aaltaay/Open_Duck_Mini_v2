# Efficiency

Written 2026-11-11 ET. No new walk was run for this note. Each number is copied from the file named on its row, or is arithmetic on those copied numbers. Arithmetic is calc only. A sim result stays sim pass only. A figure nobody published is BLOCKER.

There is no cost-of-transport target in the repo, and no gait that was trained to use less energy. Softer standing gains are still the untried lever in V1_PLAN.md track 6.

## BEC efficiency

The Castle CC BEC Pro has no published efficiency. The twins use 0.85 as an assumption. That number is not a measurement.

| What | Number | Label | Source |
|---|---|---|---|
| Value the power sim and the thermal twin use | 0.85 | assumption, not a measurement. BLOCKER until a bench log replaces it | sim/CURRENT_BUDGET.md (pack current formula). twin/thermal/THERMAL_TWIN.md (0.85, and the line that Castle publishes none). twin/electromech/ELECTROMECH_TWIN.md (the BEC row, 0.85) |
| Band the thermal twin also runs | 0.80 to 0.92, with 0.85 in the middle | same assumption, the edges of that band | twin/thermal/THERMAL_TWIN.md |
| What the bench will record | input and output volts and amps at 5 A, then efficiency | not run. BLOCKER (B37, TEST_PLAN.md 4.1) | twin/thermal/THERMAL_TWIN.md, the TEST_PLAN 4.1 note |

At the assumed 0.85 the thermal twin puts the BEC case at 98 to 122 C at the battery stop (sim pass only, twin/thermal/THERMAL_TWIN.md). That case temperature is the twin's, not a measured case.

## Gait energy

These are the published walk results. They are not a meter on the duck.

| What | Number | Label | Source |
|---|---|---|---|
| Pack draw, plain model and backlash model | about 22 W and about 31 W | sim pass only | sim/CURRENT_BUDGET.md, the battery paragraph |
| Time that draw would empty the 2 x P30B pack in that same paragraph | about 40 to 60 minutes, from about 21.6 Wh | sim pass only, and that paragraph's pack is the P30B, not the later P45B | sim/CURRENT_BUDGET.md |
| As-built pack current, this build at 2.65 kg, nominal and full | 5.3 to 5.7 A mean | sim pass only | sim/CURRENT_BUDGET.md, the as-built sentence |
| Later P45B session, trained actuator, backlash, typical | 42.9 minutes to 3.30 V per cell open circuit, no fall | sim pass only. A different session from the 22 W and 31 W lines | history/2026-11-11_2136_thermal_stationary_rms.md |

The sheet-stall walk falls at a few seconds (twin/electromech/ELECTROMECH_TWIN.md, sim pass only). The watts above are the trained actuator in those sims, not a log from the servo on the bill.

Energy per metre, calc only, from the 22 W and 31 W lines and the speeds in the next section. Not one session:

| Model | Power | Speed | Joules per metre |
|---|---|---|---|
| plain | 22 W | 0.101 m/s | 22 / 0.101 = 218 |
| backlash | 31 W | 0.132 m/s | 31 / 0.132 = 235 |

## Cost of transport

No file states a cost of transport. The figure here is calc only:

cost of transport = pack power / (mass x 9.81 x speed)

| Input | Number | Label | Source |
|---|---|---|---|
| Pack power | 22 W plain, 31 W backlash | sim pass only | sim/CURRENT_BUDGET.md |
| Forward speed at a 0.15 m/s command, the "ours" rows | 0.101 m/s plain, 0.132 m/s backlash | sim pass only | sim/ADDED_MASS_SIM.md, the walk table |
| Mass used in the division | 2.65 kg | the build named with the as-built currents in sim/CURRENT_BUDGET.md. The speed rows are that file's heavier build as it stood when they were run. The two files are not one session | sim/CURRENT_BUDGET.md and sim/ADDED_MASS_SIM.md |

| Model | Division | Cost of transport |
|---|---|---|
| plain | 22 / (2.65 x 9.81 x 0.101) = 22 / 2.626 | 8.38 |
| backlash | 31 / (2.65 x 9.81 x 0.132) = 31 / 3.432 | 9.03 |

Both are calc only. They are not a target, and they are not a measurement. A target does not exist: BLOCKER for a target.

## D22 mass cut

| What | Number | Label | Source |
|---|---|---|---|
| Printed mass the light profile wins back | 128.2 g (2766.9 g down to 2638.7 g in that study's whole-robot column) | the study's own subtraction of two slicer totals. Not weighed | print/MASS_STUDY.md, the sentence that variant (c) wins back 128.2 g, and the total row of that table |
| Where it comes off | trunk 49.5 g, each thigh 21.7 g, each foot 10.7 g, and the smaller links in that sentence | same study, slicer estimates | print/MASS_STUDY.md |

Later parts (the knee servos, the P45B pack, the sit) moved the mass budget after D22. Those later totals are sim/MASS_BUDGET.md. They are not the D22 cut. D22's own cut is the 128.2 g above.
