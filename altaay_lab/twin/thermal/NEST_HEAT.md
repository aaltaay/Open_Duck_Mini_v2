# Nest charge heat, docked and awake

Sim pass only for the shell. The charger watts are calc only: 0.969 W at 1.006 A into 12.6 V, efficiency 0.929.
The 1.00 A chart row in BQ24133_HEAT.md is 0.963 W. This row uses the board's 1.006 A.
Servos idle at 12.0 V, torque off, rail on. Head heat is the corner P5V already in the thermal twin.
Two steering diodes carry that nest current. Their heat uses the cited 0.50 V maximum, which is specified at 5 A, so it is an upper bound here.
Three cells. Nothing here was measured on a board.

| Corner | Room | Nest A | Diode W | Cells | Trunk air | Trunk wall | Knee reading | Head air |
|---|---|---|---|---|---|---|---|---|
| central | 25 C | 1.373 | 1.373 | 32.41 C | 34.28 C | 29.26 C | 29.07 C | 33.41 C |
| central | 32 C | 1.373 | 1.373 | 39.17 C | 41.15 C | 36.11 C | 35.94 C | 40.31 C |
| high | 25 C | 1.514 | 1.514 | 34.40 C | 38.22 C | 30.04 C | 29.45 C | 40.93 C |
| high | 32 C | 1.514 | 1.514 | 41.10 C | 45.09 C | 36.89 C | 36.31 C | 47.79 C |

Hottest cell 41.10 C against the cited 0 C to 60 C charge window. Inside.
Hottest knee reading 36.31 C against the cited -20 C to 60 C operating range. Inside.
Hottest trunk wall 36.89 C against the cited PLA heat-deflection low end of 49 C. Inside.
Die upper bound at the hottest trunk air: 45.1 C plus 35.7 C/W times 0.969 W = 79.7 C. Thermal regulation is 120 C and shutdown is 150 C (cited).
That bound puts every converter watt in the package, which the sheet does not. It is an upper bound, not a measured junction. The bound stays under 120 C.

Felt temperature is not a node. BLOCKER. In-trunk theta of the package is not the 35.7 C/W board. BLOCKER for a confirmed junction.
A 25 W Pi 5 is not in this head. The corner P5V is 3 W or 5 W. The 5 V, 5 A supply is pull request 111, not this charger.
