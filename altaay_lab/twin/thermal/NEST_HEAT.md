# Nest charge heat, docked and awake

Sim pass only for the shell. The charger watts are calc only: 0.969 W at 1.006 A into 12.6 V, efficiency 0.929.
The 1.00 A chart row in BQ24133_HEAT.md is 0.963 W. This row uses the board's 1.006 A.
Servos idle at 12.0 V, torque off, rail on. Head heat is the corner P5V already in the thermal twin.
Three cells. Nothing here was measured on a board.

| Corner | Room | Cells | Trunk air | Trunk wall | Knee reading | Head air |
|---|---|---|---|---|---|---|
| central | 25 C | 30.10 C | 31.10 C | 27.73 C | 29.07 C | 33.41 C |
| central | 32 C | 36.92 C | 38.01 C | 34.63 C | 35.94 C | 40.31 C |
| high | 25 C | 31.28 C | 33.44 C | 28.11 C | 29.45 C | 40.93 C |
| high | 32 C | 38.06 C | 40.35 C | 35.01 C | 36.31 C | 47.79 C |

Hottest cell 38.06 C against the cited 0 C to 60 C charge window. Inside.
Hottest knee reading 36.31 C against the cited -20 C to 60 C operating range. Inside.
Hottest trunk wall 35.01 C against the cited PLA heat-deflection low end of 49 C. Inside.
Die upper bound at the hottest trunk air: 40.4 C plus 35.7 C/W times 0.969 W = 74.9 C. Thermal regulation is 120 C and shutdown is 150 C (cited).
That bound puts every converter watt in the package, which the sheet does not. It is an upper bound, not a measured junction. The bound stays under 120 C.

Felt temperature is not a node. BLOCKER. In-trunk theta of the package is not the 35.7 C/W board. BLOCKER for a confirmed junction.
A 25 W Pi 5 is not in this head. The corner P5V is 3 W or 5 W. The board-seat change owns that load.
