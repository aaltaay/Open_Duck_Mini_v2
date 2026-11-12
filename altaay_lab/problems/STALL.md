# The sheet-stall walk falls

Sim pass only for every walk below. The datasheet lines are cited from the STS3215 C001 sheet as already copied in twin/electromech/servo_sts3215.py. The comparison of the model to those lines is calc only. Nothing was bought. The electromechanical twin was not rewritten. Every walk is `em_twin.run()` on the P45B pack, servo mode `sheet`, our build.

Run: `python3 altaay_lab/problems/stall_walk.py`

## The model is the sheet, at 7.4 V

Mode `sheet` scales the trained torque cap (3.23 Nm) down to the sheet stall, and scales damping and friction by the same factor so the no-load speed stays the BAM speed. That scale is 1.912 / 3.23 (calc only).

| | Model | Sheet |
|---|---|---|
| 7.4 V stall | 1.912 Nm | 1.912 Nm (19.5 kg.cm) |
| 7.4 V no-load | 5.646 rad/s | 5.454 rad/s |
| 7.4 V stall current | 2.5 A | 2.5 A |
| 6.0 V stall | 1.551 Nm | 1.618 Nm (16.5 kg.cm) |
| 6.0 V no-load | 4.555 rad/s | 4.400 rad/s |
| 6.0 V stall current | 2.027 A | 2.0 A |

The 7.4 V stall matches. The no-load speed is 3.5 percent fast (calc only, 5.646 / 5.454). The twin already treats the sheet speed band as plus or minus 10 percent. The 6.0 V stall is 4 percent low because the model scales the 7.4 V stall by 6.0 / 7.4, and the sheet's 16.5 kg.cm is not that ratio. Neither gap is the fall. The position gain is not on the sheet. Mode `sheet` scales the trained gain with the stall. That scale is a guess already named in the servo file.

## The fall, reproduced

Stored file twin/electromech/out/p45b_sheet/sheet_20s.json: backlash typical 3.52 s, high-side 3.46 s, plain 3.56 s, and flat 7.4 V no fall with track 0.64. This pass, same call, MuJoCo 3.17.0:

| Case | Fall | Knee volts, min / mean | Knee time on the cap |
|---|---|---|---|
| Backlash, typical, command 0.15 m/s | 3.56 s | 6.21 V / 6.95 V and 6.25 V / 6.96 V | 0.22 and 0.22 |
| Backlash, high-side, command 0.15 m/s | 3.42 s | 5.51 V / 6.76 V and 5.58 V / 6.80 V | 0.23 and 0.20 |
| Plain, typical, command 0.15 m/s | 3.56 s | 6.41 V / 7.01 V and 6.45 V / 7.02 V | 0.16 and 0.16 |
| Backlash, every servo held at 7.4 V, 12 s | none | 7.40 V | 0.26 and 0.38 |

The command starts at 2.0 s. The fall is the first steps. At 6.21 V the sheet cap is 1.912 times 6.21 / 7.4 = 1.60 Nm (calc only). At a flat 7.4 V the cap is still hit, more often, and the duck walks (track 0.645 of the 0.15 m/s command, sim pass only). The trained 3.23 Nm actuator on this same bus does not fall (the electromechanical twin, already published). The fall needs both: the sheet cap, and the sag that pulls the knees to about 6.2 V on the typical corner and about 5.5 V on the high-side corner.

## What was tried

Same policy. No new gait file and no new servo.

| Change | Result | Label |
|---|---|---|
| Sheet torque cap, trained gain left unscaled | Falls at 7.6 s. Knees on the cap 0.49 and 0.52 of the time. | sim pass only |
| Command 0.10 m/s, typical | Falls at 5.16 s | sim pass only |
| Command 0.09 m/s, typical, 20 s budget | Falls at 7.56 s | sim pass only |
| Command 0.08 m/s, typical, 20 s budget | Falls at 18.14 s | sim pass only |
| Command 0.07 m/s, typical | No fall in 20 s. Forward speed 0.035 m/s. Track 0.499. | sim pass only |
| Command 0.07 m/s, high-side | Falls at 5.24 s | sim pass only |
| Command 0.06 m/s, typical | No fall in 20 s. Forward speed 0.019 m/s. | sim pass only |
| Command 0.05 m/s, typical | No fall in 20 s. Forward speed 0.0007 m/s. That is not a walk. | sim pass only |

Raising the gain to the trained value does not keep the duck up. Slowing the command delays the fall on the typical corner and does not survive the high-side corner at any speed that is still a walk. Holding every servo at 7.4 V does keep it up, and the as-built bus does not do that.

## What this does not close

The bought servo on this policy still falls. Do not quote the trained-actuator walk as that servo. The retrain is the training row. It is NOT RUN, and it stays BLOCKER until Ahmed says yes. A bench stall and a gain measurement are already TEST_PLAN.md 7.5 and 15. This pass did not change the torque cap, because the 7.4 V stall already matches the sheet.
