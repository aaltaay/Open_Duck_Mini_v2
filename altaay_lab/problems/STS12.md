# 12 V STS3215 on a 3S pack

Sim pass only for the walks. Calc only for the bay width and the stall conversion. Cited for the sheet, the cell, and the prices. Nothing was bought. The policy was not retrained. The walk uses the current body mass, so the extra cell's 70 g is not in the fall time.

Run: `python3 altaay_lab/problems/sts12.py`

D23 already held a 3S pack until a real walking log, and it named a 3S BMS and a 3S charger. That note was about 18650 cells in the old bay. This file asks a later question: the 12 V STS3215, and whether the P45B cells already on the bill fit the grown bay in 3S.

## The sheet

ST-3215-C018, Feetech product page, read 2026-11-12 (https://www.feetech.cn/en/525603):

| Line | Value |
|---|---|
| Stall torque | 30 kg.cm at 12 V, which is 2.942 Nm (calc only, 30 x 0.0980665) |
| Stall current | 2.7 A at 12 V |
| No-load speed | 0.222 s/60 deg at 12 V, which is 4.717 rad/s (calc only) |
| No-load current | 180 mA at 12 V |
| Weight | 55 +/- 1 g |
| Operating range printed on that page | 4 V to 14 V |

The stall line is 12 / 2.7 = 4.444 ohm, and Kt is 2.942 / 2.7 = 1.090 Nm/A (calc only). The same page's wiki copy says the attached PDF prints 12.0 V as both the minimum and the maximum, while the page prints 4 V to 14 V (https://ftservo.github.io/ftservo-wiki/en/products/models/st-3215-c018/main/, checked there 2026-10-02). This walk uses the page range. It does not cut the servo off below 12 V. Waveshare's table for the same stall and speed prints 6 V to 12.6 V (https://docs.waveshare.com/ST3215_Servo).

The model is the existing sheet mode. Torque scale is 2.942 / 3.23 = 0.911 at 12 V. Damping is raised by 1.197 so the no-load speed is the 4.717 rad/s above, not the faster trained speed. The two solver sources each carry 1.5 P45B cells, so the string is 3S. The BEC set point is 16 V, so the output is the pack minus the 0.3 V dropout assumption. A 7.2 V BEC would put this servo back on the voltage that falls.

## The walk

Same backlash walk, command 0.15 m/s, both corners, 20 s budget, stop on a fall.

| Corner | Fall | Left knee min | Right knee min | Peak pack current |
|---|---|---|---|---|
| typical | none in 20 s | 10.886 V | 10.728 V | 9.527 A |
| high-side | none in 20 s | 10.515 V | 10.417 V | 9.019 A |

Typical forward speed 0.093 m/s, track 0.622. High-side 0.087 m/s, track 0.579. The command is 0.15 m/s. Pack terminal mean is 12.25 V on both corners. Lowest BEC output is 11.035 V typical and 10.923 V high-side.

Those knee volts are inside the page's 4 V to 14 V and inside the Waveshare 6 V to 12.6 V. They are outside a PDF that allows only 12.0 V. If that PDF is the one that governs, this pass is outside it.

## Fit

The grown bay (twin/battery/BAY.md) is a section for two 22.2 mm sleeve circles, centres 21.55 mm apart, outer span 43.75 mm (calc only, 21.55 + 22.2). The cut runs from y -20.7 mm to y 23.55 mm. The +y wall has 2.25 mm of material left. The charger screw pilot ends 1.0 mm from the -y wall. A third 22.2 mm circle does not fit that section. This is a reading of the published cut, not a new mesh.

The cells are the P45B already on the bill: 21.40 mm diameter, 70.00 mm long, 70.0 g max (cited, BAY.md from the Molicel sheet). Three of them in the drawn two-cell sleeve do not fit. The in-stock alternate P50B is 21.55 x 70.15 mm max and does not fit either.

## What changes on the charger and the protection

The MCP73213-A6SI/MF regulates 8.40 V (cited, circuitry/CHARGER_BOARD.md from DS20002190C). Three P45B cells charge to 12.6 V (3 x 4.20, calc only). That option does not do 12.6 V.

The nest window is 8.70 V to 10.0 V, because the specs start 0.3 V above 8.40 V and SMAJ10A stands off at 10.0 V. D61's about 9.5 V sits in that window. A 12.6 V charge needs an input above 12.6 V, so the adapter, the TVS, and the PACK_OR top all change. DK6 conducts while the nest is above the pack. A 12.6 V pack is above a 9.5 V nest, so that split no longer holds.

The Tenergy 32175 is a 2S board for 7.2 V and 7.4 V (BOM line 8). A 3S pack needs a 3S protection board. The 25 milliohm ceiling and the 22 A trip belong to the 2S board. They do not come along.

The Castle BEC is set to 7.2 V in the network. The walk above does not use that set point.

## Cost and weight

Not a bill change. Listings, not a purchase.

The extra cell is one more P45B. BOM line 6 is $9.99, out of stock on 2026-11-04. The in-stock P50B on that same line is $11.99 and the same size class. Added cell mass is 70.0 g max for the P45B (cited).

The 7.4 V servo on the bill is $19.00 each at 10 or more (BOM line 1, Seeed, 2026-11-01). The 12 V C018 was not found at that quantity. One-unit listings read 2026-11-12: $15.99 (WowRobo), $25.00 (ZennixTek), $26.00 (AIFITLAB), $29.99 (BABSCO). For 14 servos against the $19.00 line, that is from $42.14 less to $153.86 more (calc only, 14 times the gap). A matched 10-up quote is missing, so the servo delta is that range.

C018 weight is 55 +/- 1 g (cited, the Feetech page). The AIFITLAB table lists the 7.4 V C001 at the same 55 +/- 1 g. Nominal servo mass change is 0 g on that table.

A 3S charger and a 3S protection board are not on the bill. Their price and their grams are open. With the cell and the servos at the nominal sheets, the added mass that is known is the 70 g cell.
