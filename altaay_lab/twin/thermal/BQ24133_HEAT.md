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

Sim pass only for the shell. Same trunk model as gate_p45b.py. The model hardcodes two cans, so mass and can height are scaled by 3/2 and the cell node is three P45B cans. Servo idle is 21 mA (the STS3215 sheet). Cell I2R is three times 15 milliohm. The BEC loss is 0.3 V times the idle current.

The docked path is not the pack. D50 and D61 feed the awake servo bus from the nest through DK6. The nest is 15.0 V. The BEC setpoint in the 3S walk was 16 V, so it cannot regulate 15 V down. The servos then see 15.0 - 0.3 = 14.7 V (calc only). Superseded 2026-11-13: the live BEC set point is 12.0 V (D63). 16 V is outside the cited output range. The 14.7 V table below stays as the unfixed path. The C018 page range used in the 12 V study is 4 V to 14 V. 14.7 V is outside that page. Rows that put the idle at the pack voltage are a different configuration. They do not clear this gate. The pick that takes the servos off that rail is circuitry/SERVO_RAIL.md. The cut-rail sit is the last section of this note.

The 2S check, before the three-cell scale, still matches gate_p45b.json: 3.2 W, central, 32 C, cell 40.40 C, wall 36.84 C.

### Docked path: 1.00 A into a 12.6 V pack, servos at 14.7 V

Charger loss is still 0.963 W. The extra heat is the higher idle.

| Corner | Room | Cells | Trunk air | Trunk wall | Knee reading |
|---|---|---|---|---|---|
| central | 25 C | 30.14 C | 31.17 C | 27.76 C | 29.88 C |
| central | 32 C | 36.96 C | 38.08 C | 34.66 C | 36.73 C |
| high | 25 C | 31.32 C | 33.52 C | 28.14 C | 30.33 C |
| high | 32 C | 38.10 C | 40.44 C | 35.04 C | 37.17 C |

Shell numbers are sim pass only. Cells stay under 60 C. The knee reading stays under 60 C. The wall stays under the 49 C PLA edge. None of that clears the gate, because 14.7 V is still outside the 4 V to 14 V page.

### Pack-fed comparison, not the dock. 1.00 A at 12.6 V, servos at 12.6 V.

| Corner | Room | Cells | Trunk air | Trunk wall | Knee reading |
|---|---|---|---|---|---|
| central | 25 C | 29.91 C | 30.85 C | 27.61 C | 29.25 C |
| central | 32 C | 36.73 C | 37.76 C | 34.51 C | 36.12 C |
| high | 25 C | 31.04 C | 33.09 C | 27.97 C | 29.65 C |
| high | 32 C | 37.83 C | 40.01 C | 34.88 C | 36.5 C |

At 10.8 V on the pack-fed rows the loss is 0.825 W. The hottest of those is the high corner at 32 C: cells 37.31 C, wall 34.55 C, knee 35.92 C.

### Die temperature is an upper bound, not a confirmed crossing

Figure 10-4 is an EVM efficiency. The loss includes the external inductor and the sense resistor. RθJA applies to heat inside the package. Putting all 0.963 W, or all 2.517 W, on 35.7 C/W overstates the junction. Those figures are upper bounds only.

The cited in-package piece is the MOSFET conduction (SLUSAF7D: high side 80 milliohm typical and 150 milliohm max, low side 95 and 160). Duty is 12.6 / 15.0 = 0.84 (calc only). At 1.00 A that is 0.082 W typical and 0.152 W max. At 2.50 A it is 0.515 W typical and 0.948 W max. On 35.7 C/W the 0.948 W rise is 33.8 C (calc only). Switching loss inside the die is not separated on the sheet. BLOCKER for a die temperature.

So the 2.50 A case does not have a confirmed 120 C crossing. The upper bound, with every converter watt in the die and the nest-fed trunk air, is 136.72 C at the high corner and 32 C. That is above 120 C and below 150 C, and it is not the junction. The FET-only rise stays under 120 C. Which one the die does is not known.

Felt temperature is still BLOCKER. The mat has no grade. The docked wall, 35.04 C, is under the wool type I top of 93.3 C, and this mat is not identified as that felt.

## 2S fallback, if the pack stays two cells

The forced 1.00 A on the MCP73213 at 9.5 V is 2.30 W at 7.2 V and 3.50 W at 6.0 V. On the cited 62 C/W board that is 167.6 C to 249.0 C (calc only). Every one of those crosses 150 C shutdown. That is the same result as the earlier sit note.

Three ways to fix that, and which one is small enough to also finish the charge:

1. Current limit. On 62 C/W at a 32 C room, 150 C allows 1.903 W. At a 6.0 V pack the drop is 3.5 V, so the current is 0.544 A (calc only, 1.903 / 3.5). 4.5 Ah divided by (150 - 32) / 62 / 3.5 is 8.28 h (calc only). The A6S timer is 5.4 h to 6.6 h (cited). The current that stays under shutdown does not finish inside the timer. Holding 110 C instead of 150 C cuts the current to 0.359 A and takes longer. A resistor change alone does not do both.

2. Copper pour. 3.50 W stays under 150 C at 32 C only if theta is 33.7 C/W or less (calc only, (150 - 32) / 3.50). The only theta the MCP73213 sheet gives is 62 C/W. It does not publish a pour that reaches 33.7 C/W. A pour is not a cited fix.

3. The same BQ24133, with CELL floating. The sheet says a floating CELL pin is 2 cells at 8.4 V. Figure 10-4 has no 9.5 V, 2-cell trace. The nearest is AVCC = 12 V, 2 cells, 0.916 at 1.00 A (chart read). Loss at 8.4 V and 1.00 A is 0.770 W (calc only). Assigning all of that to the die on 35.7 C/W in a 32 C room is an upper bound of 59.5 C. At 85 percent, which is worse than that trace, the same upper bound is 84.9 C. Both upper bounds are under 120 C and under 150 C, so this chip at 1.00 A does not cross those two lines even if every converter watt is inside the package.

The smallest fix that stays under 150 C and can still charge at 1.00 A is this chip with CELL floating. It is the charger the 3S plan already names. The mat does not change.

## Cut rail, the dock this note now uses

circuitry/SERVO_RAIL.md holds the Pololu 2815 off while the nest is present. Servo current in this sit is 0. Servo voltage is 0 V, which is under the 14 V page. Charger loss is still 0.963 W at 1.00 A into 12.6 V. The BEC is not in dropout on an idle current, because the rail is open. Sim pass only.

| Corner | Room | Cells | Trunk air | Trunk wall | Knee reading |
|---|---|---|---|---|---|
| central | 25 C | 28.36 C | 28.63 C | 26.57 C | 25.0 C |
| central | 32 C | 35.23 C | 35.58 C | 33.51 C | 32.0 C |
| high | 25 C | 29.14 C | 30.06 C | 26.79 C | 25.0 C |
| high | 32 C | 35.98 C | 37.00 C | 33.73 C | 32.0 C |

The knee reading is the room, because the servos are off and the sheet idle is not flowing. Cells stay under 60 C. The wall stays under 49 C. The die upper bound at the high corner and 32 C is 71.38 C, under 120 C, and it is still an upper bound. Felt grade is still BLOCKER. Unpowered friction on the sit is still the open item in the sit study. It is not cleared by opening the rail.
