# Characterization: the measurements the twin has to match

Written 2026-11-13. Gate 0 does not pass until these rows are measured and the twin is re-run on them. A coupon is allowed only after Ahmed says yes. The coupon is not the product and it is not the one-click bill.

The blank table is `altaay_lab/test/records/characterization_template.csv`. Copy it to a new file under `altaay_lab/history/` when a measurement exists. Do not fill the template in place.

## File format

CSV, one row per quantity. Header:

```
record_id,quantity,unit,condition,twin_value,twin_label,tol_abs,pass_rule,measured,status
```

| Column | Meaning |
|---|---|
| record_id | CHAR-SERVO, CHAR-BEC, CHAR-PACK, CHAR-SIT, CHAR-SOLE, or CHAR-WELL |
| quantity | The name in the template. Do not rename it. |
| unit | The unit the number is in |
| condition | Voltage, load, temperature, and what was held still |
| twin_value | The number in the twin today. Blank if the twin has no number. |
| twin_label | cited, calc only, sim pass only, assumption BLOCKER, or BLOCKER |
| tol_abs | Absolute band written before the test. A factor-of-two rule leaves this blank and uses pass_rule. |
| pass_rule | How measured is compared to twin_value |
| measured | The bench number. Blank until the test is run. |
| status | NEEDS HARDWARE until a person writes the measured cell. Then PASS or FAIL. |

The twin matches a row only when status is PASS. A sim value in twin_value is not a match.

Time-series logs, when a row needs one, are CSV with this header:

```
t_s,v_supply,i_supply,torque_Nm,speed_rad_s,temp_C
```

One file per run. The summary row in the characterization CSV points at that file by name in the note the history entry adds. Do not commit a log over 5 MB.

## 1. 12 V servo (CHAR-SERVO)

Owner gate: DEFINITION_OF_DONE gate 0 electrical, and gate 1 electrical. Bench steps: TEST_PLAN 7 and 7.5, run at 12.0 V for the C018, not only at 7.4 V.

Setup. One servo, horn on a rigid stop for the stall points, horn free for the speed points. Bench supply at 12.0 V, current limit 4 A. Room temperature written down. Four-wire ohms at the stall point: current leads on the supply, sense leads on the servo pins.

Sheet lines the twin uses today (cited, Feetech C018 page, problems/STS12.md):

| Quantity | Sheet | Playbook band |
|---|---|---|
| Stall torque | 30 kg.cm, which is 2.942 Nm (calc only) | plus or minus 0.294 Nm |
| Stall current | 2.7 A | plus or minus 0.27 A |
| No-load speed | 0.222 s/60 deg, which is 4.717 rad/s (calc only) | plus or minus 0.472 rad/s |
| No-load current | 0.180 A | plus or minus 0.036 A |
| Terminal resistance | 12 / 2.7 = 4.444 ohm (calc only) | plus or minus 0.444 ohm |

The 10 percent and 20 percent bands are the playbook's match bands. They are not a tolerance printed on the sheet. The sheet's own speed tolerance was not copied onto the C018 line. If the stalled ohms and the stalled current disagree by the kind of gap already seen on the STS3250 sheet (1.2 ohm versus 12 V / 4.2 A), the row is FAIL and the twin does not pick one of them.

Also record the same five numbers at 7.4 V and at 6.0 V. TEST_PLAN 7.5 uses the 7.4 V and 6.0 V pair to see whether the firmware holds duty or holds current. Write both duties into the history file. The twin's servo mode stays BLOCKER until that pair exists.

Pass: every CHAR-SERVO row at 12.0 V is inside its band, and `twin/electromech` is re-run with the measured Kt, R, and the duty behavior. Fail: any row outside the band, or a re-run that is skipped.

## 2. BEC setpoint (CHAR-BEC)

Owner gate: gate 0 electrical. Bench step: TEST_PLAN 4.1, with the setpoint programmed to 12.0 V. Section 4.1 was written for 7.2 V. Keep that sheet if a 7.2 V unit is on the bench. The current duck's row is 12.0 V.

Castle Link sets 12.0 V. No-load output, input at 12.6 V or higher: 12.00 V plus or minus 0.10 V. That 0.10 V is the playbook gate. Castle publishes no setpoint tolerance (BLOCKER for calling 0.10 V a datasheet limit).

Then the input sweep at 2 A: 12.6 V, 12.3 V, 12.0 V, 11.3 V, 8.4 V. Write input, output, and current each time. Dropout is input minus output on the first point where the output falls below 12.00 V minus 0.10 V. The twin uses 0.30 V until this number replaces it. That 0.30 V is an assumption (BLOCKER).

Efficiency is output watts over input watts at 2 A and at 5 A, input 12.6 V if it is still regulating, and at the dropout point. The twin uses 0.85 until this number replaces it. Castle publishes none (BLOCKER).

The STS12 walk does not hold 12.0 V. Typical BEC input minimum is 11.335 V (sim pass only, problems/sts12.json). Regulation at 12.0 V needs 12.3 V at the input (calc only, 12.0 plus 0.30). On that walk the loss used by the thermal twin is 1.441 W and the case at 40 min is 60.7 C in a 25 C room, central corner (sim pass only, results/bec12_heat.json). A bench case temperature is compared to 60.7 C with a 15 C investigate band (`records/predictions/bec12_case.yaml`). Outside the band means the twin or the setup is wrong. It does not by itself fail the sheet window, and inside the band is not a hardware pass.

Pass: setpoint, dropout, and efficiency are written, and `bec12_heat.py` is re-run with those two numbers instead of 0.30 V and 0.85. Fail: the no-load point is outside 12.00 V plus or minus 0.10 V when the input is at least 12.3 V.

## 3. Pack (CHAR-PACK)

Owner gate: gate 0 electrical, gate 5 electrical. The cell is the Molicel P45B, three in series. The sheet DC resistance is 15 mOhm at 50 percent SOC (cited). The playbook band is plus or minus 3 mOhm. Full string, rested: 12.60 V (calc only, 3 times 4.20). Band plus or minus 0.05 V.

Log, if a discharge is run: `t_s,v_supply,i_supply` with current negative for discharge, plus cell temperature if a sensor is on the can. The twin's discharge figure is replaced by that log. Weld, sleeve, and fish-paper resistance are not in the model today (the battery row of TWIN_CHECKLIST.md). A pack measurement that skips the weld does not close the row.

The 3S protector part number is BLOCKER. Do not characterize a 2S Tenergy trip and call it this pack.

## 4. Seat friction (CHAR-SIT)

Owner gate: gate 0 sit, and the limp-sit row of the FMEA. TEST_PLAN 19.5. Torque off. A known weight on a 50 mm arm, or a kitchen scale on that arm. Least torque that starts the joint, three times each direction, each leg joint that the sit uses (knee, hip pitch, ankle).

The sim value today is 0.068 Nm (the training model, not a datasheet). Pass is within a factor of 2, which is the line already in TEST_PLAN 19.5. Then re-run `twin/sit/sit_sim.py` with the measured number. The sheet value remains BLOCKER until this row is PASS. Sole friction is a different row.

## 5. Sole on felt (CHAR-SOLE)

Owner gate: gate 0 felt, gate 3 mechanical. There is no twin value. The nest sims use a rigid mat. The sit sim uses floor friction 0.8. Other runs use 0.6 and 1.0. None of those is this mat (BLOCKER).

Coupon: the felt grade that will be bought, large enough for one foot, on a stiff board. A sole-shaped TPU coupon or the printed foot. Pull horizontally with a scale. Normal load written down. The plan's starting load is 15 N (calc only, about half of 2.7 kg times 9.8, rounded up). If the real foot load is different, write the real load and use that. mu is pull force divided by normal force. Dry, then a damp fingerprint, then household dust. Speed slow enough that the scale holds a reading.

Pass: the number is in the CSV and the sit sim and the nest sim are re-run with it. There is no pass band against 0.8. Matching 0.8 by luck is not the test.

## 6. Wells (CHAR-WELL)

Owner gate: gate 0 pin contact, gate 4 electrical, gate 5 mechanical. Nest v2 uses five gold wells on foil. Spring pins are not this row. Do not buy the spring-pin coupon as the nest contact.

Four-wire ohms at 1.0 A: one well, the foil, the return well. Ten presses. Pass line carried forward from TEST_PLAN 20.1 until a measured distribution replaces it: under 0.15 ohm, and no press more than 20 percent above the first. That 0.15 ohm was written for two pins on cloth. It is a ceiling, not a prediction. The twin has no measured well ohm (BLOCKER).

Also the coin check and the snag check in TEST_PLAN 20.2 and 20.3. A hair that bridges the two foils is a fail.

Pass: the ohms are in the CSV and the electrical twin uses them. Fail: open, a cut in the foil, or a loop over 0.15 ohm.
