# BQ24133 heat on the 3S sit

2026-11-12 ET. The fall-fix notes (PRs 67, 71, 72) put three P45B cells and a TI BQ24133 in the duck, with the nest supply at 15.0 V. The mat stays nest v2. D61 was not edited.

The planned charge current is 1.00 A. That is the current problems/NEST3.md uses for the 15.0 V drop. The datasheet fast-charge range is 0.6 A to 2.5 A (cited, SLUSAF7D). 2.5 A is the maximum, not the planned current.

Nothing here was measured on a board.

## Loss, from Figure 10-4

Datasheet SLUSAF7D, September 2020, https://www.ti.com/lit/ds/symlink/bq24133.pdf.

Figure 10-4, chart read, black trace, AVCC = 15 V, 3 cells:

| Current | Efficiency |
|---|---|
| 1.00 A | 0.929 |
| 2.50 A | 0.926 |

The trace does not print the battery voltage. The same efficiency is used at 10.8 V (3 times 3.6 V) and at 12.6 V (CELL tied to VREF, cited). Loss is Vbat times current times (1/efficiency - 1), calc only. A measured efficiency already includes the converter loss, so the 15 mA switching supply current on the DC table is not added again.

| Current | Pack | Loss |
|---|---|---|
| 1.00 A | 10.8 V | 0.825 W |
| 1.00 A | 12.6 V | 0.963 W |
| 2.50 A | 12.6 V | 2.517 W |

RθJA is 35.7 C/W (cited, thermal information). Thermal regulation is 120 C. Thermal shutdown is 150 C, and the charger stays off until the junction falls below 130 C (cited). Absolute maximum junction is 155 C. Recommended free air is -40 C to 85 C. ψJB is 31.2 C/W (cited). The 35.7 C/W figure points at SPRA953. It is not a measurement in this trunk.

## Sit, 6 hours, torque off, three cells

Sim pass only. Same trunk model as gate_p45b.py. The model hardcodes two cans, so mass and can height are scaled by 3/2 and the cell node is three P45B cans. Servo idle is 21 mA at the pack voltage of the row (the STS3215 sheet idle). The BEC loss is 0.3 V times that idle current, because the 16 V setpoint in problems/FIT3.md is above the pack. Cell I2R is three times 15 milliohm.

A 15 V nest feeding a BEC that is already in dropout would put about 14.7 V on the servos. The C018 page range used in the 12 V study is 4 V to 14 V. 14.7 V is outside that page, so it is not a row here.

The 2S check, before the three-cell scale, still matches gate_p45b.json: 3.2 W, central, 32 C, cell 40.40 C, wall 36.84 C.

### Planned 1.00 A at 12.6 V (0.963 W). This is the hotter of the two planned packs.

| Corner | Room | Cells | Trunk air | Trunk wall | Knee reading | Die, 35.7 C/W in room air | Die, 35.7 C/W in the trunk air |
|---|---|---|---|---|---|---|---|
| central | 25 C | 29.91 C | 30.85 C | 27.61 C | 29.25 C | 59.38 C | 65.23 C |
| central | 32 C | 36.73 C | 37.76 C | 34.51 C | 36.12 C | 66.38 C | 72.14 C |
| high | 25 C | 31.04 C | 33.09 C | 27.97 C | 29.65 C | 59.38 C | 67.47 C |
| high | 32 C | 37.83 C | 40.01 C | 34.88 C | 36.5 C | 66.38 C | 74.38 C |

Shell columns are sim pass only. Die columns are calc only. The trunk-air die uses the sheet's 35.7 C/W on the model's trunk air. The sheet did not measure that board in a closed trunk.

At 10.8 V the loss is 0.825 W. The hottest of those eight rows is the high corner at 32 C: cells 37.31 C, wall 34.55 C, knee 35.92 C, trunk-air die 68.64 C. All below the 12.6 V row.

### Does the planned 1.00 A cross a cited limit?

| Part | Hottest planned number | Cited limit | Crosses? |
|---|---|---|---|
| Cells | 37.83 C | 0 C to 60 C charge, P45B version 1.2 | No |
| Servo reading | 36.5 C | -20 C to 60 C, STS3215 A/1 item 1-2 | No |
| Trunk air | 40.01 C | -40 C to 85 C free air, BQ24133 | No |
| Trunk wall, the model's PLA | 34.88 C | PLA heat deflection 49 C to 57 C | No |
| Same wall if it were PETG | 34.88 C | PETG heat deflection 62 C at 1.8 MPa | No |
| Die on the cited board, in room air | 66.38 C | 120 C regulation, 150 C shutdown | No |
| Die if 35.7 C/W still holds in the trunk air | 74.38 C | 120 C and 150 C | No |
| Board copper, from ψJB | 44.3 C | PLA 49 C, if the PLA touches that copper | No |

Board copper is the trunk-air die minus ψJB times the loss: 74.38 - 31.2 x 0.963 = 44.3 C (calc only). That is the sheet's junction-to-board parameter, not a thermocouple on the PLA. Felt temperature is still BLOCKER. The mat has no grade. The wall bound, 34.88 C, is under the wool type I top of 93.3 C, and this mat is not identified as that felt.

### Chip maximum, 2.50 A at 12.6 V (2.517 W). Not the planned current.

Hottest row, high corner, 32 C: cells 47.38 C, wall 37.55 C, knee 36.5 C, die in room air 121.87 C, die in trunk air 136.32 C (sim pass only for the shell, calc only for the die).

Cells, the knee, and the wall stay inside the limits above. The die crosses 120 C regulation on the cited board at 32 C (121.87 C) and in the trunk air (125.41 C to 136.32 C). It does not cross 150 C shutdown. Board copper at that row is 136.32 - 31.2 times 2.517 = 57.8 C (calc only), which is over the 49 C PLA edge and under the 62 C PETG edge.

## 2S fallback, if the pack stays two cells

The forced 1.00 A on the MCP73213 at 9.5 V is 2.30 W at 7.2 V and 3.50 W at 6.0 V. On the cited 62 C/W board that is 167.6 C to 249.0 C (calc only). Every one of those crosses 150 C shutdown. That is the same result as the earlier sit note.

Three ways to fix that, and which one is small enough to also finish the charge:

1. Current limit. On 62 C/W at a 32 C room, 150 C allows 1.903 W. At a 6.0 V pack the drop is 3.5 V, so the current is 0.544 A (calc only, 1.903 / 3.5). 4.5 Ah divided by (150 - 32) / 62 / 3.5 is 8.28 h (calc only). The A6S timer is 5.4 h to 6.6 h (cited). The current that stays under shutdown does not finish inside the timer. Holding 110 C instead of 150 C cuts the current to 0.359 A and takes longer. A resistor change alone does not do both.

2. Copper pour. 3.50 W stays under 150 C at 32 C only if theta is 33.7 C/W or less (calc only, (150 - 32) / 3.50). The only theta the MCP73213 sheet gives is 62 C/W. It does not publish a pour that reaches 33.7 C/W. A pour is not a cited fix.

3. The same BQ24133, with CELL floating. The sheet says a floating CELL pin is 2 cells at 8.4 V. Figure 10-4 has no 9.5 V, 2-cell trace. The nearest is AVCC = 12 V, 2 cells, 0.916 at 1.00 A (chart read). Loss at 8.4 V and 1.00 A is 0.770 W (calc only). On 35.7 C/W in a 32 C room the junction is 59.5 C. Even at 85 percent, which is worse than that trace, the loss is 1.482 W and the junction is 84.9 C. Both are under 120 C and under 150 C.

The smallest fix that stays under 150 C and can still charge at 1.00 A is this chip with CELL floating. It is the charger the 3S plan already names. The mat does not change.
