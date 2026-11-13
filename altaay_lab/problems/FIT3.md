# Third cell, 60 s, and the 3S parts

The voltage budget is already in problems/VOLTAGE_BUDGET.md (pull request 66). Short form, sim pass only: at the typical left-knee minimum of 5.785 V the pack current is 17.899 A and the bus current is 15.147 A. From the 8.347 V open circuit that is 0.495 V in the cells, 1.257 V on the pack path, 0.067 V of copper into the BEC, 0.300 V of dropout, and 0.443 V of harness. Holder, fuse, and XT30 are 0.322 V with no measured part. Dropout and the 0.85 efficiency are unpublished. Zeroing those still falls. The knee port does not include a winding drop.

This file adds the third cell's mass, a 60 s walk, and a fit check. The nest stays the striped felt mat (cad/nest_v2 on the lab branch, D62). No new mat is drawn. Nothing was bought. No retrain.

## Why the body speed is about 0.09 m/s

The 0.15 m/s figure is the command. The policy does not walk at 0.15 m/s even on a stiff bus. The 12 V sheet no-load speed is 0.222 s/60 deg, which is 4.717 rad/s (calc only). The model the policy was trained against has a no-load speed of 5.646 rad/s (the same 0.068 Nm and 0.56 used in the servo file). The ratio is 0.835 (calc only).

The sheet mode raises damping so the no-load speed matches 4.717 rad/s. With that damping, the 70 g cell, and a 0.15 m/s command, the 60 s body speed is 0.088 m/s typical and 0.084 m/s high-side (sim pass only). The same mass and the same 12 V torque scale, with the damping left at the trained no-load speed, walks at 0.122 m/s over 20 s (sim pass only). The extra damping is the change that cuts the speed. The 70 g cell moves the trunk centre of mass from -56.5 mm to -62.4 mm (calc only, on the 1.065 kg trunk). The 20 s walk without that mass, in problems/STS12.md, was 0.093 m/s. The cell is a few millimetres per second. The damping is the rest.

Commanding 0.088 m/s, the speed the 0.15 command actually produced, is a different gait. Over 60 s the body then makes 0.016 m/s typical and 0.017 m/s high-side, track 0.191 and 0.201 (sim pass only). The 0.09 m/s number is an output, not a command that gets the same walk back.

## 60 s with the cell in the trunk

Added mass is 70.0 g, the P45B maximum (cited, twin/battery/BAY.md). The 25 g holder stays out. That file already removed it. The seat is the rear cell below, at x -152.5 mm, y 1.4 mm, z 31.5 mm. Sim pass only. Both corners, backlash, sheet servo, 3S pack, BEC set point 16 V so the servos see the pack minus the 0.3 V dropout.

| Command | Corner | Fall | Body speed | Track | Knee mins | Pack peak | 100 ms peak |
|---|---|---|---|---|---|---|---|
| 0.15 m/s | typical | none in 60 s | 0.088 m/s | 0.589 | 10.779 V, 10.730 V | 9.026 A | 6.751 A |
| 0.15 m/s | high-side | none in 60 s | 0.084 m/s | 0.557 | 10.436 V, 10.382 V | 8.664 A | 6.564 A |
| 0.088 m/s | typical | none in 60 s | 0.016 m/s | 0.191 | 10.745 V, 10.707 V | 9.534 A | 6.424 A |
| 0.088 m/s | high-side | none in 60 s | 0.017 m/s | 0.201 | 10.408 V, 10.368 V | 9.058 A | 6.296 A |

Mean pack current at 0.15 m/s is 5.144 A typical and 5.104 A high-side.

## Bay

The grown pocket holds two 22.2 mm sleeves (twin/battery/BAY.md). A third sleeve does not fit inside that shell: the part is 40 mm deep in x and a sleeve is 22.2 mm.

The check in problems/bay3.py keeps the two cells on their axes and puts the third 19.41 mm behind them (calc only, sleeve pitch 22.2 mm), axis x -152.51 mm, y 1.42 mm. The shell grows a 2.5 mm blister. CAD check only. print/body_back.stl is not changed.

| Check | Result |
|---|---|
| Watertight | yes |
| Three sleeves against the plastic | 0 mm3 each |
| New overlap with other parts | none (the BMS and body_middle_bottom overlaps are already in the unedited shell) |
| Fasteners within 30 mm of the rear axis | none |
| Back wall | 2.5 mm |
| Cap above and below the part of the cavity that sticks out past the old shell | 2.5 mm each |
| How far the back moves | 12.36 mm, from x -154.0 mm to -166.36 mm |
| Mesh volume | 89439.7 mm3 to 83502.9 mm3 |

No screw moves (D42). The cavity is the battery bay, extended (D39). The plastic grams of that volume change are not converted here. The walk mass is the 70 g cell only.

## Charger, protection, nest window

The nest stays the striped felt mat. Its charger is still the MCP73213, and the contact window is still above 8.70 V and at or under 10.0 V (cited, circuitry/CHARGER_BOARD.md, and the same window in the nest v2 note). A 3S pack charges to 12.6 V (3 x 4.20, calc only). That window does not cover it. The mat shape is not redrawn. The supply and the TVS would have to change, because a 10.0 V standoff conducts above 10 V.

Charger IC, cited, TI BQ24133 datasheet (https://www.ti.com/lit/ds/symlink/bq24133.pdf): CELL tied to VREF regulates 12.6 V for 3 cells. Charge current up to 2.5 A with a 10 milliohm sense. Input operating range 4.5 V to 17 V. The EVM note (https://www.ti.com/lit/ug/sluu476/sluu476.pdf) says the supply should sit about 1 V above the battery regulation, so about 13.6 V for 12.6 V, and the operating top is 17 V. That band does not overlap 8.70 V to 10.0 V. The chip is 5.5 mm by 3.5 mm. Whether a board built on it fits the nest pocket's 70 mm by 26 mm by 14 mm keep-out was not checked.

Protection board, the 3S part already named in sim/POWER_FIX.md, re-read 2026-11-12 (https://power.tenergy.com/protection-circuit-module-pcb-for-11-1v-3s-li-ion-battery-pack-working-9a-cutoff-17a/): Tenergy P/N 32007, working 9 A, over-current 17 +/- 4 A, main loop at most 30 milliohm, 50 x 16 x 3.5 mm, $23.99. The 2S board on the bill is the Tenergy 32175. The 100 ms pack current above is 6.8 A or less, inside the 9 A line. The tallest sample is 9.534 A, above 9 A and under the 13 A low end of the trip. The page does not give a weight.

## Cost and weight

Cited or calc only. Not a bill change. Not a purchase.

| Piece | Change | Weight |
|---|---|---|
| One more P45B | +$9.99 (BOM line 6, out of stock 2026-11-04). The in-stock P50B on that line is $11.99 and the same sleeve class | +70.0 g, cited maximum |
| 14 servos, C001 at $19.00 (10 or more, BOM line 1) against one-unit C018 listings of $15.99 to $29.99 | from $42.14 less to $153.86 more (calc only, 14 times the gap). No matched quantity quote | 0 g at the nominal 55 g on both sheets |
| BMS, 32175 at $22.99 to 32007 at $23.99 | +$1.00 (calc only) | not on the 32007 page |
| BQ24133RGYR | $3.12 at quantity 1 (LCSC lists $3.1246, read 2026-11-12, https://www.lcsc.com/product-image/C44478.html). The MCP73213 price was not on the bill lines opened, so this is the new chip, not a swap delta | the package is 5.5 x 3.5 mm. Board grams not opened |

The shell volume drops 5936.8 mm3 in the check (calc only). That plastic is not in the 60 s walk, and the print file was not changed.
