# Voltage budget at the knee dip

Sim pass only for the walk. The split is the as-built solver at the sample where the left knee is lowest. Copper and the ohm times ampere products are calc only. Assumptions are named. Nothing was bought.

Run: `python3 altaay_lab/problems/volt_budget.py`

The question used 5 A and 0.096 ohm. This sample is not that current.

## The sample

Backlash walk, sheet servo, P45B pack, command 0.15 m/s. Typical corner, t = 3.182 s, which is also the peak. The walk falls at 3.56 s.

| Node | Volts |
|---|---|
| Two-cell open circuit | 8.347 |
| Pack terminal | 7.852 |
| Switched bus | 6.595 |
| BEC input | 6.528 |
| BEC output | 6.228 |
| Left knee port | 5.785 |
| Right knee port | 5.889 |

Peak pack current on this walk, up to the fall: 17.899 A. Peak bus current, the BEC output: 15.147 A. Both are that same sample. The left knee itself draws 1.968 A, under the sheet stall of 2.5 A at 7.4 V (cited). The 15.147 A is the sum of the 14 servos. The port voltage does not include a drop inside the servo. The winding drop is how 5.785 V becomes torque. It is not another volt in this table.

High-side, t = 3.022 s, fall at 3.42 s: pack 17.676 A, bus 14.944 A, left knee 5.269 V, right knee 5.244 V.

## Where the typical 1.615 V below 7.4 V goes

7.4 V is the sheet rating. It is not a node. The open circuit is 8.347 V. From that open circuit down to the left knee is 2.562 V. The part of that which sits below 7.4 V is 1.615 V.

| Step | Drop | What it is |
|---|---|---|
| Open circuit to pack terminal | 0.495 V | The discharge figure at 17.899 A. That is 13.8 milliohm per cell (calc only, 0.495 / 2 / 17.899). The sheet's 15 milliohm pulse at 5 A is 0.150 V for the pack (calc only). The 0.18 V figure is the 5 A case. This sample is 17.9 A. |
| Pack terminal to switched bus | 1.257 V | 70.2 milliohm at 17.899 A. The pieces below add to 70.3 milliohm. |
| P10, bus to BEC input | 0.067 V | Netlist copper. |
| BEC input to BEC output | 0.300 V | The dropout constant. Castle publishes none. The input is 6.528 V, under 7.2 + 0.3, so the 7.2 V set point is not holding. |
| BEC output to the left knee | 0.443 V | Harness. SP1 current is 3.995 A, not 5 A. The 0.096 ohm chain at 5 A (0.48 V, calc only) is the same order as this 0.443 V. It is not the whole dip. |

Pack-path 70.3 milliohm, typical corner, at 17.899 A:

| Piece | milliohm | Volts at 17.899 A | Source |
|---|---|---|---|
| P1, P2, P6, P7, P8, P9, P14 copper | 14.2 | 0.255 | netlist cuts, copper table |
| BMS | 25 | 0.448 | cited Tenergy ceiling, used as the value |
| Switch, Pololu 2815 | 13 | 0.233 | cited maximum at a 4.5 V gate |
| Holder | 10 | 0.179 | ASSUMPTION, the bench pass limit, no measured holder |
| Fuse | 6 | 0.107 | ASSUMPTION |
| Two XT30 contacts | 2 | 0.036 | ASSUMPTION, 1 milliohm each |

Holder, fuse, and XT30 are 0.322 V with no measured part. The BMS line is a cited maximum, so a lower real board would give back part of the 0.448 V. The switch line is a cited maximum at a low gate, so part of the 0.233 V can be high. The BEC dropout is 0.300 V with no Castle number. BEC efficiency 0.85 is unpublished. It raises the pack current above the 15.147 A bus: about 2.7 A, which is about 0.19 V on this 70 milliohm path (calc only). That 0.19 V is current from an assumption.

Each leg hop is 0.0276 ohm. Of that, 24 AWG copper at 150 mm is 0.0126 ohm and the two contacts plus the board pass are 0.015 ohm. The 24 AWG kit gauge is unpublished. The 5 milliohm contact is an assumption. Those contact ohms are tenths of a volt along the chain at 2 A, not the volt and a half.

## Does zeroing the unmeasured drops stop the fall

Holder, fuse, and XT30 set to 0.1 milliohm, BEC dropout set to 0, BEC efficiency set to 1. Same sheet walk, 20 s budget. Sim pass only.

| Corner | Fall | Peak pack current | Lowest bus |
|---|---|---|---|
| typical | 3.60 s | 18.501 A | 6.864 V |
| high-side | 3.54 s | 17.692 A | 6.926 V |

The fall remains. Those assumptions are real volts in the budget, and they are not the whole fall. The 15 to 18 A peak is still there. Fourteen times the 2.5 A sheet stall is 35 A, so 15 A is inside that sum. It is many servos near stall on one sample, which the policy is asking for. It is not a current above the sheet.
