# Docked and awake, charger in the trunk

2026-11-24 ET. Sim pass only for the shell. Calc only for the watts. Nothing was measured on a board.

The duck is awake and the servo rail is off (circuitry/SERVO_RAIL.md). The head keeps the 5 V load already in the thermal model. Servo current is 0. The heat added in the trunk is the BQ24133 converter loss at 1.006 A (calc only, the netlist current).

Efficiency is 0.929, the Figure 10-4 chart read at 1.00 A, 15 V in, 3 cells (cited, SLUSAF7D, the same read as BQ24133_HEAT.md). The chart has no 1.006 A point. Loss is pack voltage times 1.006 A times (1/0.929 - 1).

| Pack | Loss (calc only) |
|---|---|
| 10.8 V | 0.830 W |
| 12.6 V | 0.969 W |

This is not the 1.9 W to 3.2 W MCP73213 band. That chip regulates 8.40 V and trips near 13 V. It is not on this 3S pack. circuitry/NEST_TWO_NET.md.

Six hours, torque off, servos off, head load on. Sim pass only.

| Pack | Corner | Room | Cells | Trunk air | Trunk wall | Knee reading |
|---|---|---|---|---|---|---|
| 10.8 V | central | 25 C | 28.14 C | 28.29 C | 26.41 C | 25.0 C |
| 10.8 V | central | 32 C | 35.02 C | 35.24 C | 33.35 C | 32.0 C |
| 10.8 V | high | 25 C | 28.86 C | 29.58 C | 26.61 C | 25.0 C |
| 10.8 V | high | 32 C | 35.72 C | 36.53 C | 33.55 C | 32.0 C |
| 12.6 V | central | 25 C | 28.39 C | 28.65 C | 26.58 C | 25.0 C |
| 12.6 V | central | 32 C | 35.26 C | 35.60 C | 33.51 C | 32.0 C |
| 12.6 V | high | 25 C | 29.17 C | 30.08 C | 26.80 C | 25.0 C |
| 12.6 V | high | 32 C | 36.01 C | 37.03 C | 33.74 C | 32.0 C |

Hottest cell 36.01 C. Hottest trunk wall 33.74 C. Both at 0.969 W, high corner, 32 C room. Cells stay under 60 C. The wall stays under 49 C. The knee reading is the room, because the servos are off.

The die upper bound puts every converter watt on the cited 35.7 C/W board, in the trunk air. The hottest of those is 71.61 C (37.03 C air plus 35.7 times 0.969 W, calc only). That is under 120 C and under 150 C, and it is still an upper bound. The inductor and the sense resistor are outside the package. Felt temperature is BLOCKER. In-trunk theta is BLOCKER. The charger board still has no measured seat.

Source: twin/thermal/gate_docked_awake.py and gate_docked_awake.json.
