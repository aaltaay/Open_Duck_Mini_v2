# 3S nest window, the 9 A pulse, and one servo price

The mat is not redrawn. Stripes stay 20 mm with 5 mm felt gaps. The five wells stay 3 mm across and 12 mm apart (cad/nest_v2 on the lab branch). Nothing was bought. No retrain.

## Supply, TVS, and the contact window

The 2S window is above 8.70 V and at or under 10.0 V, because the MCP73213 specs start 0.3 V above 8.40 V and SMAJ10A stands off at 10.0 V (cited, circuitry/CHARGER_BOARD.md). A 3S pack charges to 12.6 V. That window does not cover it.

The charger IC is the TI BQ24133 (cited, https://www.ti.com/lit/ds/symlink/bq24133.pdf). CELL tied to VREF regulates 12.6 V. The operating input is 4.5 V to 17 V. Section 8.1 rates AVCC, ACP, ACN, ACDRV, CMSRC, and STAT to 30 V, and rates PVCC to 20 V. The EVM note (cited, https://www.ti.com/lit/ug/sluu476/sluu476.pdf) says the supply should sit about 1 V above the battery regulation, so 13.6 V at the end of charge (calc only, 12.6 + 1.0).

The TVS on the contacts stays in the Littelfuse SMAJ series the 2S board already uses. SMAJ16A (cited, the series table and https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smaj/smaj16a): standoff 16.0 V, breakdown 17.8 V to 19.7 V at 1 mA, clamp 26.0 V at 15.4 A. That 26.0 V is under the 30 V rating of AVCC. It is over the 20 V rating of PVCC. The old board's test was a clamp under every pin of the MCP73213. The same test fails here. No row of that SMAJ table has a standoff at or above 13.6 V and a clamp at or under 20 V (SMAJ12A clamps at 19.9 V but stands off at only 12.0 V). A different SMAJ does not fix PVCC and still finish a 12.6 V charge.

PVCC is the charger input after the input FETs. The datasheet's own disconnect is the N-channel ACFET and RBFET, common source, driven by ACDRV. OVPSET rising through 1.6 V (1.55 V to 1.65 V) turns that pair off and stops the charge. The deglitch is 1 µs typical. The divider is set so 1.6 V on OVPSET is 18 V at the input (calc only). The low trip is 17.44 V and the high trip is 18.56 V (calc only, 1.55 / 1.6 x 18 and 1.65 / 1.6 x 18). Both are under 20 V. The 16.0 V top of the supply window is under 17.44 V, so a supply inside the window does not open the FETs. The 2S P-FET stays on during a positive surge, so it is not this disconnect. The MOSFET part number is not chosen. During that 1 µs the datasheet does not show PVCC staying under 20 V if the contact node is already at the 26 V clamp. That microsecond is not closed.

The contact window is above 13.6 V and at or under 16.0 V. The supply picked inside it is 15.0 V: 1.4 V over 13.6 V, and 1.0 V under the standoff (calc only). At 1.00 A the round trip can drop 1.4 ohm before the chip input is 13.6 V (calc only, 1.4 V / 1.00 A). The mat copper at 2.0 A was 0.038 ohm (calc only, the nest v2 note). That is inside 1.4 ohm. The adapter tolerance is still not published. If the adapter sits above 16.0 V, SMAJ16A conducts. That is the same kind of open item the 2S window already has.

## Spacing and touch, geometry unchanged

The stripe gap is 5 mm of felt. The wells are 3 mm with centres 12 mm apart, so the edge gap is 9 mm (calc only, 12 - 3).

IPC-2221B Table 6-1, column B2 (external conductors, uncoated, up to 3050 m), is 0.10 mm for 0 V to 15 V and 0.10 mm for 16 V to 30 V. That figure is the one printed by the published reproductions of the table (https://www.smpspowersupply.com/ipc2221pcbclearance.html and https://www.atlaspcb.com/tools/conductor-spacing-calculator/). The IPC document itself was not the copy opened here. At the 16.0 V top of this window the requirement is 0.10 mm. The 5 mm felt gap is 50 times that, and the 9 mm well gap is 90 times that (calc only).

IEC 62368-1 steady-state ES1 for DC is 60 V (cited, DigiKey's reading of clause 5, https://www.digikey.co.uk/en/articles/how-to-design-protection-circuits-compliant-for-standard-iec-62368-1, and the Mean Well summary of Table 4, https://expo.meanwell.com/upload/data/SafetyNews/EN/Safety_IEC62368-1ES.pdf). The standard says the voltage limit or the current limit is enough. 15.0 V and 12.6 V are under 60 V, so the voltage rule holds. The charge current is 1.00 A on the existing board and up to 2.5 A on this chip, which is above the 2 mA ES1 current figure. The voltage rule is the one that is met. The IEC book was not purchased.

A coin can still bridge the 5 mm gap. That short is unchanged because the geometry is unchanged. It stays the open item the nest v2 note already has. Spacing is not what fails it.

## The 9 A working rating

Tenergy P/N 32007 (cited, https://power.tenergy.com/protection-circuit-module-pcb-for-11-1v-3s-li-ion-battery-pack-working-9a-cutoff-17a/): continuous discharge 9 A, over-current detect 17 +/- 4 A, delay 10 +/- 5 ms. The low trip is 13 A (calc only, 17 - 4).

The 9.534 A sample is one physics step of the 0.088 m/s walk. The same 60 s runs, counted at every 2 ms step (sim pass only):

| Command | Corner | Samples at or above 9 A | Longest run | Time at or above 9 A | Peak | 60 s mean |
|---|---|---|---|---|---|---|
| 0.15 m/s | typical | 1 | 2 ms | 2 ms | 9.026 A | 5.144 A |
| 0.15 m/s | high-side | 0 | none | 0 | 8.664 A | 5.104 A |
| 0.088 m/s | typical | 32 | 6 ms | 64 ms | 9.534 A | 3.634 A |
| 0.088 m/s | high-side | 4 | 2 ms | 8 ms | 9.058 A | 3.649 A |

None of those peaks reach 13 A, so the over-current detector does not start. The longest time above 9 A is 6 ms. The 100 ms current on that walk was 6.424 A, and on the 0.15 m/s walks it was 6.751 A and 6.564 A, all under 9 A (sim pass only, problems/FIT3.md). The 9 A line is the continuous rating. These walks sit near 5 A or 3.6 A for the minute, with a few milliseconds up around 9.5 A. That is inside the continuous rating and under the trip. A larger board is not required for this pulse.

## One servo price

The listing is the Waveshare 12 V option, SKU 22414, 30 kg.cm at 12 V, not the 7.4 V option on the same page (cited, https://www.waveshare.com/st3215-servo.htm?sku=22414, read 2026-11-12). The price break is $21.99 at one, and $20.63 at four or more. Fourteen servos use the four-or-more price.

14 times $20.63 is $288.82. Fourteen of the 7.4 V servos at the bill's $19.00 (10 or more, BOM line 1) are $266.00. The delta is $22.82 per duck (calc only). The page did not print a stock count.

## What a retrain would buy back

Not run. A paid GPU run waits on Ahmed.

The policy was trained on servos whose no-load speed is 5.646 rad/s. The 12 V sheet is 4.717 rad/s, which is 0.835 of that (calc only). With the sheet damping, a 0.15 m/s command walks at 0.088 m/s over 60 s (sim pass only). The same policy, the same 70 g, and the same 12 V torque, with the damping left at the trained speed, walks at 0.122 m/s over 20 s (sim pass only). The difference is 0.034 m/s (calc only). That is what this policy loses to the slower sheet. It is not a retrained speed. The two windows are 60 s and 20 s.

Asking the same policy for 0.088 m/s does not get 0.088 m/s back. It picks a different gait and the body makes 0.016 m/s. A retrain would teach gaits the 4.717 rad/s servo can finish, instead of a 0.15 m/s gait the servo only partly finishes. The 0.034 m/s is the gap that retraining is aimed at. The speed after a retrain was not measured.

The heat of the BQ24133 at the 1.00 A used above, and the 2S fallback, is in twin/thermal/BQ24133_HEAT.md. The mat is still this one.
