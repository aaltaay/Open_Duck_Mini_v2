# Charge heat at 2.30 W and 3.50 W

2026-11-12 ET. The docked sit in `THERMAL_TWIN.md` used 1.9 W and 3.2 W. Those rows stay in `gate_p45b.json`. This note is the same sit at the reconciled board heat.

Calc only, from `circuitry/CHARGER_BOARD.md`: at 9.5 V in and 1.00 A, a 7.2 V pack is (9.5 - 7.2) x 1.00 = 2.30 W, and a 6.0 V pack is (9.5 - 6.0) x 1.00 = 3.50 W. That is the heat if the current stays at 1.00 A. The chip will not hold that current once the die reaches 110 C (cited, DS20002190C, the block-diagram label already in the charger note). The shell table is the forced-current case. It is an upper bound on the trunk if the die folds back, which is the same reading as the open life note (PR 49).

PR 49 ran the central corner at 22 C and 32 C and is not merged. This run uses the same model. A check of the published 3.2 W, central, 32 C row comes back at cell 40.40 C and wall 36.84 C, the same as `gate_p45b.json`. The life note's 3.50 W central row comes back at 22 C as cell 31.30 C, wall 27.41 C, knee 24.60 C, BEC 41.90 C, and at 32 C as cell 40.87 C and wall 37.15 C. Those match the life note's 31.3 C, 27.4 C, 24.6 C, 41.9 C, 40.9 C, and 37.2 C.

Nothing here was measured on a board, a cell, or a piece of felt.

## Where the heat is

The 2.30 W and 3.50 W are the MCP73213 in the duck (D61, and nest v2). The nest is the mat the duck sits on while that charge runs. The cord pocket does not hold this chip. The gate board that would sit in the pocket is not designed, so its heat is BLOCKER. The mat copper already in nest v2 is 0.15 W at 2.0 A (calc only). That is not this chip.

## Duck, charging, torque off, 6 hours

Sim pass only. Same trunk model as `gate_p45b.py`: idle 21 mA per servo, charge current 1.0 A, central and high corners, 25 C and 32 C rooms. The knee column does not move with the charger watts. The knees are outside the trunk, and the same idle equilibrium is already in the 1.9 W and 3.2 W table. The BEC does move, because it sits in the trunk air.

The die column is not from that model. It is calc only: room plus 62 C/W times the watts. 62 C/W is the sheet's 4-layer JEDEC board in open air (cited, temperature specifications). It is not the closed trunk. Do not add that rise on top of the trunk air. The 62 C/W path already ends at room air, and this board is not the JEDEC board.

| Charger | Corner | Room | Cells | Trunk air | Trunk wall | Knee reading | BEC case | Die, JEDEC board |
|---|---|---|---|---|---|---|---|---|
| 2.30 W | central | 25 C | 32.21 C | 33.87 C | 29.03 C | 27.57 C | 42.16 C | 167.6 C |
| 2.30 W | central | 32 C | 38.97 C | 40.75 C | 35.89 C | 34.48 C | 48.88 C | 174.6 C |
| 2.30 W | high | 25 C | 33.94 C | 37.27 C | 29.6 C | 27.81 C | 48.5 C | 167.6 C |
| 2.30 W | high | 32 C | 40.65 C | 44.16 C | 36.46 C | 34.72 C | 55.36 C | 174.6 C |
| 3.50 W | central | 25 C | 34.17 C | 36.54 C | 30.33 C | 27.57 C | 44.77 C | 242.0 C |
| 3.50 W | central | 32 C | 40.87 C | 43.38 C | 37.15 C | 34.48 C | 51.45 C | 249.0 C |
| 3.50 W | high | 25 C | 36.35 C | 40.93 C | 31.09 C | 27.81 C | 52.15 C | 242.0 C |
| 3.50 W | high | 32 C | 42.99 C | 47.79 C | 37.91 C | 34.72 C | 58.98 C | 249.0 C |

Shell columns are sim pass only. The die column is calc only.

## Does it cross a cited limit?

| Part | Hottest number in the table | Cited limit | Crosses? |
|---|---|---|---|
| Cells | 42.99 C | 0 C to 60 C charge, P45B version 1.2 | No |
| Servo reading | 34.72 C | -20 C to 60 C, STS3215 A/1 item 1-2 | No |
| Trunk air, as an ambient for the chip | 47.79 C | -40 C to +85 C, industrial order code | No |
| Trunk wall, the model's PLA | 37.91 C | PLA heat deflection 49 C to 57 C, glass transition 55 C to 60 C (THERMAL_TWIN.md [P1] to [P3]) | No |
| Same wall if it were PETG | 37.91 C | PETG heat deflection 62 C at 1.8 MPa and 69 C at 0.45 MPa, glass transition 66 C (THERMAL_TWIN.md [P6]) | No |
| Charger die on the JEDEC board, current forced at 1.00 A | 167.6 C to 249.0 C | 110 C thermal regulation, 150 C typical shutdown (DS20002190C) | Yes. Every row crosses both. |
| Charger die in the closed trunk | BLOCKER | the same 110 C and 150 C | No trunk temperature. The only cited resistance already crosses, and it is not this trunk. |
| Felt | BLOCKER | wool felt type I, -80 F to +200 F, which is -62.22 C to 93.33 C (Superior Felt wool-felt specs, all type I) | No felt temperature. The grade is not named, and the posed sit puts the TPU seat on the felt. That seat is not a node. |
| PLA or PETG touching the package | BLOCKER | the PLA and PETG bands above | No seat, so no gap and no local temperature. |

On the cited 62 C/W board the die reaches 110 C at 1.371 W in a 25 C room and at 1.258 W in a 32 C room (calc only, (110 - room) / 62). Both are under 2.30 W. It reaches the 150 C shutdown at 2.016 W and 1.903 W (calc only, (150 - room) / 62). Both are under 2.30 W. So a forced 1.00 A at 9.5 V does not sit at either watt on that board. The foldback currents for a 110 C die are already in `CHARGER_BOARD.md`. They were not re-derived here.

The wall bound, which is the outside of the one-node shell, stays at or under 37.91 C. That is under the 93.33 C top of the wool type I range. It is a bound on the shell, not a measurement of the felt, and this mat is not identified as that felt.

Castle publishes no BEC case limit. The hottest BEC in this table is 58.98 C. A pass for that case is BLOCKER. The life note already says the walking BEC is hotter than this sit.

## What this does not close

- In-trunk thermal resistance. BLOCKER, as the charger note already says.
- A seat for the board. The wall number is not the plastic against the package.
- Felt grade, felt conductivity, and the TPU seat. BLOCKER.
- The walk. Continuous walking still leaves 60 C. This sit does not change that.
- The 6 hour timer under foldback. Still the open calc in the charger note.
