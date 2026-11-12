# In-body charger board

Schematic only. No board has been built, and no electrical measurement of this circuit exists. The arithmetic is in `circuitry/check_charger.py` (calc only). A sim of the duck is not a result here.

This board is the charger D61 moves into the duck. It replaces the Adeept USB-C board (netlist U6, BOM line 11) as the charge path. It does not edit `wiring/netlist.yaml`. A later owner merges `circuitry/charger_board.yaml`.

The nest folder was read and not edited. The four spring pins, the gold disc (plus) and the pale gold ring (minus) stay as drawn in `twin/dock/nest/`. This board is what those pins feed.

## Sources opened for this board

| What | Document | Where |
|---|---|---|
| Charger | Microchip MCP73213, DS20002190C, revision C, December 2014, 34 pages | https://ww1.microchip.com/downloads/en/DeviceDoc/20002190C.pdf |
| Reference board | Microchip MCP73213 evaluation board user's guide, DS51849A, 22 July 2009 | https://ww1.microchip.com/downloads/en/DeviceDoc/51849a.pdf |
| Cell | Molicel INR21700-P45B product data sheet, version 1.2, one page. The sheet's own title line is INR-21700-P45B | https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf |
| Balance | Microchip AN231, Cell Balancing Design Guidelines, Rich DelRossi, PDF dated 19 December 2002 | http://ww1.microchip.com/downloads/en/AppNotes/00231a.pdf |
| Reverse FET | Diodes Inc. DMP2045U, DS40478 revision 4-2, July 2021 | https://www.diodes.com/assets/Datasheets/DMP2045U.pdf |
| Input TVS | Littelfuse SMAJ series, electrical table, SMAJ10A row. A revision letter was not in the text extracted from the page | https://www.littelfuse.com/assetdocs/tvs-diodes-smaj-datasheet?assetguid=13c2a823-03b8-4d1f-9ddc-9b44670aed9d |
| Pack NTC | Adafruit 372 product page, and its 10k 3950 lookup table | https://www.adafruit.com/product/372 and https://cdn-shop.adafruit.com/product-files/372/103_3950_lookuptable.txt |

The 2009 eval guide says the installed device has a 6.5 V over-voltage threshold. Revision C of the chip sheet says 13 V typical (12.8 to 13.2 V). This board follows revision C. The guide is still the reference for the external parts: 4.7 µF on the input and the output, and a resistor on PROG.

## What the chip is set to

Order code: **MCP73213-A6SI/MF**.

Table 2 of DS20002190C lists MCP73213-A6S/MF as 8.40 V regulation, 13 V input over-voltage protection, precondition current 10 percent, precondition timer 32 minutes, elapsed timer 6 hours, end of charge at 10 percent, recharge at 95 percent, precondition threshold 71.5 percent, status type 1 (on/off). The ordering key on the last pages adds **I** for the industrial range, -40 C to +85 C, and **/MF** for the 10-lead 3 mm DFN. The package-marking table prints MCP73213-A6SI/MF for that device. The eval board BOM names MCP73213-A6S/MF, which is the same option without the temperature letter written out.

There is no thermistor pin. The pins are VDD, VDD, VBAT, VBAT, NC, NC, STAT, VSS, VSS, PROG, and the exposed pad (Table 3-1). The stripe study's note that the chip has no pack-temperature input matches this sheet. Die thermal regulation is a different function, below.

## Charge current

Equation 5-1, copied from the sheet:

`IREG (mA) = 1104 x RPROG(kOhm) ^ (-0.93)`

Equation 5-2 is the inverse. Table 5-1 puts **1.10 kOhm** on the 1000 mA row (E96 and E24). The DC table says PROG = 1.1 kOhm gives 1000 mA typical, 900 to 1100 mA.

`check_charger.py` evaluates equation 5-1 at 1.10 kOhm as **1010.4 mA** (calc). That is inside 900 to 1100 mA. At 10 kOhm the same equation gives 129.7 mA, against the table's 130 mA row. At 1.00 kOhm it gives 1104 mA, and the table prints 1100 mA. The board uses one 1.10 kOhm, 1 percent, not the eval board's pair of 2.37 kOhm resistors. Those two in parallel are the guide's way to switch between about 500 mA and about 1000 mA. This duck has one current.

Chosen current: **1.00 A typical**, set by 1.10 kOhm.

Why that current, from the cell sheet (version 1.2): standard charge 4.5 A, maximum charge 13.5 A with a 70 C cut-off, charge voltage 4.2 V per cell, charge time at the standard rate 1.5 h. 1.00 A is 1.00 / 4.5 = **0.222 C** (calc). Section 6.1.1.1 of the charger sheet says the preferred fast charge is below 1C and that the cell maker's rate should be used. 0.222 C is under both the 1C preference and the P45B standard rate.

It is also the current D61 and the existing heat band already use, and it is the current the eval board calls its high setting. Termination is 10 percent, so **0.10 A** (calc, 10 percent of the 1.00 A typical). Precondition current is 10 percent as well, **0.10 A**, below the 71.5 percent threshold.

Precondition threshold for this option: 0.715 x 8.40 V = **6.006 V** (calc). The ratio range on the DC table for that row is 69 to 74 percent. The low corner used in the heat bound below is 0.69 x 8.35 V = **5.761 V** (calc, ratio minimum times VREG minimum).

## Input from the nest

D61: gold disc is plus, pale gold ring is minus. Four spring pins under the body, two in the seat block (plus) and two in the belly bumper (minus), each pair 20 mm apart, the pairs 130 mm apart.

`twin/dock/nest/cad/NEST_CAD.md` already routes those pins:

| Lead | Path | Gauge | Length |
|---|---|---|---|
| NP1, NP2 | seat pins to splice JNP | 22 AWG | 17.5 mm and 30.4 mm (calc only, CAD check only) |
| NP3 | JNP toward DK6 | 20 AWG | 62.9 mm (calc only, CAD check only) |
| NM1, NM2 | bumper pins to splice JNM | 22 AWG | 65.9 mm and 60.5 mm (calc only, CAD check only) |

This board's plus pad is JNP. Its minus pad is JNM. The pin part number is still incomplete (PARTS_AUDIT.md). Contact resistance on cloth is not measured. Both stay BLOCKER for the nest, not redesigned here.

The stripe study's contact current, calc only, is 2.0 A typical and 2.8 A peak while charging (about 1.0 A for the duck and 1.0 A for the pack, peak about 1.8 A on the duck side plus the charge). The P-FET and the 5 A fuse are sized against that 2.8 A, not against the 1.1 A chip ceiling alone, because the duck supply is taken from the same protected node.

## Protection

Order from the plus contact:

1. **Fuse.** Littelfuse 0287005.PXCN, 5 A ATO, the fuse already called F2 on the charge path. The fuse datasheet was not re-opened. The netlist already rates it 5 A, 32 V. A 5 A fuse holds 2.8 A. It is ahead of the TVS so a sustained clamp can open it. An ATO is slow. A short spike is the TVS's job, not the fuse's.
2. **TVS.** Littelfuse SMAJ10A, uni-directional, cathode on the fused plus, anode on ground. From the SMAJ table: standoff 10.0 V, breakdown 11.10 to 12.30 V at 1 mA, clamp **17.0 V** at 23.5 A, leakage 5 µA at the standoff. The same series states IEC 61000-4-2 ESD of 30 kV contact and 30 kV air. The contacts are exposed, so this diode is the ESD part as well as the surge clamp. 17.0 V is under the chip's 18.0 V absolute maximum. SMAJ11A clamps at 18.2 V, which is over 18.0 V, so it is not used.
3. **Reverse polarity.** Diodes DMP2045U-7, P-channel. Drain on the fused plus, source on the protected rail, so the body diode (cathode at the source) blocks a reversed input. Gate pulled to ground by 10 kOhm. A 4.7 V zener, cathode on the source and anode on the gate, holds VGS near the -4.5 V point where RDS(on) is specified, and under the **±8 V** gate absolute maximum. The zener candidate is onsemi MMSZ5230B. Its sheet was not opened: BLOCKER for the knee voltage at the bias current.
4. **The chip's own limits**, on the protected rail. Under-voltage lockout start 4.15 V typical (4.10 to 4.25 V). The specs apply from VREG typical + 0.3 V, so **8.70 V** for the 8.40 V option, up to 12 V in the table and 13.0 V recommended (section 3.1). Over-voltage protection 13 V typical, 12.8 to 13.2 V, hysteresis 150 mV. Absolute maximum on VDD is 18.0 V. Below about 8.70 V the part is outside the characterized window and cannot hold 8.40 V at the battery. Above 13 V it stops charging. A reversed input is not covered by that over-voltage block. Section 6.1.1.4 is reverse-discharge protection (a shorted input must not empty the pack). It is not a reverse-adapter block. The P-FET is that block. The stripe study was right that a duck sitting the wrong way round should not charge.

Design window for the nest supply, from those limits: **above 8.70 V and at or under 10.0 V** (the TVS standoff). D61's about 9.5 V (calc only in that decision) sits in the window: 0.80 V over 8.70 V, and 0.50 V under 10.0 V. At 1.00 A the round-trip drop can be up to **0.80 ohm** before the chip input falls to 8.70 V (calc: 0.80 V / 1.00 A). At the 0.10 A termination the same 0.80 ohm is only 0.08 V, so the end of charge is the easy end. Contact resistance is still unmeasured: BLOCKER. The nest adapter's tolerance is not published: BLOCKER. If the adapter sits above 10.0 V, SMAJ10A is past its standoff and will conduct.

Pass-transistor on-resistance is 350 mOhm typical, specified at VDD = 4.5 V and TJ = 105 C, not production tested. That is not the drop at 9.5 V. In current regulation the heat is (input minus battery) times current, which is equation 6-1, not I squared R.

At 2.8 A the P-FET drop, using the 45 mOhm maximum at VGS = -4.5 V, is 2.8 x 0.045 = **0.126 V**, and the heat is **0.353 W** (calc). Junction-to-ambient on that sheet is 98 C/W on the rated copper (note 6). 0.353 W is about 35 C of rise (calc). The 2.8 A figure is the stripe study's peak, calc only.

## Decoupling, from the sheet and the eval board

Chip sheet, section 3.1 and 6.1.1.3:

- VDD to VSS: minimum 1 µF. Typical applications: minimum 25 V rating.
- VBAT to VSS: minimum 1 µF, for stability with the battery unplugged. Typical applications: minimum 16 V rating.
- Table 6-1 allows X7R or X5R.

Eval board BOM, Table B-1: **C1 and C2 are both TDK C2012X5R1E475M, 4.7 µF, 25 V, X5R, 1206.** Figure 6-1 of the chip sheet is the same two-capacitor circuit with no values printed on the figure. This board uses those two parts. 4.7 µF is over the 1 µF minimum. 25 V on the output is over the 16 V minimum. Place both next to the chip, and tie the exposed pad to ground copper with vias (section 3.7 and 6.2).

Stock of that exact TDK number was not opened. If it will not order, the electrical requirement is still 4.7 µF, 25 V, X5R or X7R, 1206. That substitute is BLOCKER until a live number is opened.

## Pack NTC and the die's own thermal limit

The die limits its own current from junction temperature (section 5.9). Figure 5-1 shows the current falling as the junction gets hotter. The figure was not digitized, so this note does not read a current off that curve. The block diagram labels the thermal-regulation comparator at **110 C**. Thermal shutdown is **150 C** typical, with 10 C hysteresis (DC table). Theta JA is **62 C/W** on a 4-layer JEDEC board in natural convection (temperature specifications). That 62 C/W is not the closed trunk. In-trunk theta is BLOCKER.

The pack is a separate limit. P45B version 1.2: charge only from **0 C to 60 C**. Discharge is -40 C to 60 C. The chip cannot see that, because it has no THERM pin.

The pack sensor is the one already chosen: Adafruit 372, 10 kOhm at 25 C, B25/50 = 3950, epoxy bead. The product page was opened and said **in stock**. It did not print a piece count. The lookup table, opened, gives 31.77 kOhm at 0 C and 2.472 kOhm at 60 C.

Divider, NTC to ground, 10.0 kOhm from the reference to the NTC. The thresholds sit inward of the cell limits so a 1 percent resistor stack, the bead's own 1 percent resistance and 1 percent beta, and the comparator offset still cannot charge outside 0 C to 60 C.

The bead page says 10 kOhm ± 1 percent at 25 C and B25/50 = 3950 ± 1 percent. The comparator is a TI LM393BIDR. Sheet SLCS005AH, revised April 2025, section 5.5: input offset 4 mV maximum from -40 C to +85 C, and input bias 50 nA maximum over that range. 50 nA across 10 kOhm is 0.5 mV (calc). The error used below is 4.5 mV on a 2.5 V reference. The TL431 absolute voltage cancels between the two dividers. Its sheet is still not opened, so the same stack was also checked at 2.2 V and still stays inside the cell window (calc, a guard, not a TL431 limit).

- Cold divider: 10.0 kOhm over **28.0 kOhm**. Nominal trip **2.60 C** (calc, lookup table). Worst corner **1.33 C** (calc). That is above 0 C.
- Hot divider: 10.0 kOhm over **2.80 kOhm**. Nominal trip **56.61 C** (calc). Worst corner **58.36 C** (calc). That is below 60 C.

The old 31.6 kOhm and 2.49 kOhm pair sat on the cell limits. With 1 percent resistors alone, the hot trip resistance fell to about 2.42 kOhm, near 60.6 C, and the cold trip went slightly under 0 C. Those values are not used.

Both comparators are open collector and pull the charge-enable gate down. Cold uses the NTC on pin 2 (1IN-). Hot uses the NTC on pin 5 (2IN+) and the threshold on pin 6 (2IN-). SOIC pin numbers are Table 4-1 of SLCS005AH. Inside the window both outputs are off and the 100 kOhm pull-up enables charge.

The reference is a TL431 with ref tied to the cathode, fed from the protected rail by 4.99 kOhm. At a 2.5 V cathode and 9.5 V in, that is about 1.4 mA (calc). The TL431 sheet was not opened, so 2.495 V and the minimum cathode current are BLOCKER. The trip ratios do not need that voltage. They need the two dividers to share one rail.

LM393B supply is 2 V to 36 V (family table in the same sheet). The SMAJ10A clamp is 17.0 V, inside that range. Common mode over temperature is from the negative rail to VCC minus 2.0 V. The divider voltages are a fraction of about 2.5 V, and the supply here is the nest rail near 9.5 V, so the inputs sit inside that range.

TEST_PLAN 20.8 asks for cells at 0 C to 45 C on the bench, which is tighter than the cell sheet on purpose (COMPLIANCE_FIRST_PASS.md). This hardware window is the cell sheet, 0 C to 60 C. The Pi can stop earlier, at 45 C, by pulling GPIO6 low. That software limit is a proposal for the software owner. It is not in `software/SOFTWARE.md`.

The enable FET is a small N-channel, candidate onsemi MMBF170. Its sheet was not opened. BLOCKER: it must be on at 3.3 V and off near one diode drop. PROG current is about 1 mA (the block diagram gain is 0.001, so 1 A at the battery is 1 mA at PROG). When the FET is on, 1.10 kOhm sits from PROG to ground and the chip charges. When the FET is off, PROG is open. Standby is a PROG impedance around 200 kOhm (DC table, typical).

## Status pins and the Pi

There is one status pin, STAT, open drain (section 3.4 and section 5.11). The sheet says a pull-up can interface it to a host. Type 1, which this order code is, behaves like this (Table 5-2):

| State | STAT |
|---|---|
| Shutdown, standby, charge complete | high impedance |
| Precondition, constant current, constant voltage | low |
| Temperature fault, timer fault, precondition timer fault | high impedance (type 1). Type 2 would flash. |

Low means charging. High means not charging. A type 1 pin does not say whether "not charging" is full, a timer fault, a die temperature fault, or no input. The standard samples in Table 2 are type 1. A flashing type 2 part with the same 8.40 V and 6 hour settings was not found as a stocked order code: BLOCKER if one pin must report faults by itself. Until then the Pi treats low as charging, and uses pack voltage and time to tell full from fault. Servo voltage is already how the guard reads the pack (D16).

**GPIO5, header pin 29, input.** STAT, through 1 kOhm, with 10 kOhm to the Pi 3.3 V rail. 3.3 V / 10 kOhm = 0.33 mA (calc), under the 35 mA sink maximum. VOL is 0.5 V max at 4 mA, so a 0.33 mA low is inside that. No level-shifter IC. A pull-up to VDD (about 9.5 V) would be legal for the open-drain pin (outputs may sit up to VDD + 0.3 V) and illegal for the Pi. This board does not do that. A 1N4148 from the GPIO node up to 3.3 V clamps a fault that pulls STAT toward the nest. The duck BOM already names a 1N4148 on line DK5. That diode's sheet was not re-opened.

**GPIO6, header pin 31, open drain.** Enable. A diode lets the pin pull the gate down and does not let it drive the gate high, so it cannot fight the temperature comparators. The 100 kOhm to 3.3 V makes the default "charge" when the Pi rail is up and the cells are inside 0 C to 60 C. If 3.3 V is down, the FET is off and the chip stays in standby. D50 keeps the duck awake while docked, so 3.3 V is up during a normal charge.

GPIO5 and GPIO6 are not used in `wiring/netlist.yaml`. Used there: GPIO2, 3, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27. Header names are in `wiring/sheets/sheetlib.py`. GPIO4 is avoided because `software/PI_SETUP.md` notes that a MAX98357A overlay without `no-sdmode` claims it. GPIO14 and GPIO15 stay free for a UART. GPIO0 and GPIO1 are the ID EEPROM pins and are not used.

The three wires (STAT, EN, 3.3 V) plus ground are a proposed cable from this board up to the Pi. They are not in the netlist yet. Ground is already common.

## Heat, against the 1.9 W to 3.2 W band

If the current stayed at the 1.00 A typical, power in the chip is (nest voltage minus pack voltage) times 1.00 A.

At the D61 figure of 9.5 V (calc only in that decision):

| Pack | Power at 1.00 A | Old band |
|---|---|---|
| 7.2 V | **2.30 W** (calc) | 1.9 W |
| 6.0 V | **3.50 W** (calc) | 3.2 W |
| 8.40 V, still at 1.00 A | 1.10 W (calc) | current is tapering here, so this is not the CV case |

The old band, divided by 1.00 A and added back to the pack voltage, implies about **9.1 V** at the 7.2 V pack and about **9.2 V** at the 6.0 V pack (calc). Both are under the 9.5 V figure. So 2.30 W and 3.50 W are the same formula as the old band, at a higher input. They are **0.40 W and 0.30 W above** the band the thermal twin ran.

Which number is the heat at the D61 input: **2.30 W and 3.50 W** (calc only), because that input is 9.5 V and the current in this note is 1.00 A. (9.5 minus 7.2) times 1.00 is 2.30. (9.5 minus 6.0) times 1.00 is 3.50. The thermal table's 1.9 W and 3.2 W are the watts that table actually ran. They match about 9.1 V and 9.2 V, not 9.5 V. That table was not re-run. It is the right record of that sim. It is not the heat of this board at 9.5 V.

Equation 6-1 is the sheet's worst case: highest input, lowest precondition-exit voltage, highest current. At 9.5 V, 5.761 V, and 1.10 A that is **4.11 W** (calc). On 62 C/W that is a **255 C** rise (calc), which the die will not sit through. Section 5.9 exists for this case. The sheet's own worked example (equation 6-2) is (9.9 V - 6.0 V) x 440 mA printed as 1.58 W, and "about 98 C above room" on this package. 3.9 V x 0.440 A is 1.716 W (calc), not 1.58 W. 1.58 W x 62 C/W is 98 C (calc), which matches the sentence. The printed product and the printed power do not match. This board does not use 1.58 W. It uses equation 6-1 with the numbers above.

Current that holds a 110 C die on a 62 C/W board, at 9.5 V in (calc, block-diagram temperature, not a digitized point on Figure 5-1):

| Room | Pack 6.0 V | Pack 7.2 V | Pack 8.2 V |
|---|---|---|---|
| 25 C | 0.392 A | 0.596 A | 1.055 A |
| 32 C | 0.359 A | 0.547 A | 0.968 A |

At 32 C and a 6.0 V pack the chip is down near 0.36 A if it is holding 110 C. If all 4.5 Ah were taken at 0.359 A, the time is about **13 h** (calc: 4.5 / 0.359, plus the 0.5 h below), past the timer.

Timer for this option: 6.0 h typical, 5.4 to 6.6 h (AC table). Charge time if the current stayed at 1.00 A: the nameplate 4.5 Ah takes **4.50 h** of constant current (calc). The cell sheet's standard charge is 1.5 h at 4.5 A, and 4.5 Ah / 4.5 A is 1.0 h, so the sheet's standard charge is **0.50 h** longer than a pure constant-current fill. Adding that 0.50 h gives **5.00 h** (calc). 5.00 h is under the 5.4 h minimum timer. That 0.50 h is the standard-charge difference. It is not a measurement of the taper at 1 A. A full constant-current fill from 2.5 V per cell is also more than a duck that stopped near 6 V will put back. Both effects make 5 h a long estimate for a real dock, if the current stays near 1 A.

The open thermal point: the current will not stay at 1 A while the pack is low and the die is hot, and the trunk is not the 62 C/W board. Whether a folded-back charge of this 4.5 Ah pack finishes inside 5.4 h is BLOCKER. Figure 5-1 was not digitized. In-trunk theta was not measured.

`twin/thermal/THERMAL_TWIN.md` (update 2026-11-11) already ran the old band as constant heat in a docked sit, torque off, 1.0 A, 6 hours (sim pass only). At 1.9 W and at 3.2 W, in the central and high corners, at 25 C and 32 C rooms, the cells stayed inside 0 C to 60 C and the servos stayed inside -20 C to 60 C. The hottest cell in that table is 42.4 C (3.2 W, high corner, 32 C room). This board does not re-run that twin. Proposed: re-run it at 2.30 W and at 3.50 W, which is the 9.5 V input if the current really stays at 1 A, and also at about 1.26 W, which is (110 C - 32 C) / 62 C/W if the die is regulating (calc). The charger still has no seat, so a PLA number in that twin is a trunk-wall number, as that file already says.

## The bus, while charging, torque off (D59)

D59 is the alert sit: the duck rests on the stops with torque off. D50 keeps the electronics awake and says the pack only charges. D61 keeps that split on two wires.

```
gold disc (plus) -- JNP -- fuse -- TVS to ring -- P-FET --+-- MCP73213 VDD
                                                           |         |
                                                           |        VBAT ---- BMS P+   (pack only)
                                                           |
                                                           +-- DK6 -- 2813 input -- servo bus
ring (minus) -- JNM ------------------------------------------ ground, BMS P-, DK6 ground

fused pack -- DK7 -- 2813 input
```

DK6 is the ideal diode from the nest into the switched bus. DK7 is the ideal diode from the fused pack into the same bus. While the nest is near 9.5 V and the pack is at most 8.40 V, DK6 conducts and DK7 is off. The pack does not feed the bus. The bus does not load VBAT. The charger's end-of-charge comparator and its 6 hour timer see the pack current, which is what D50 split the wires to protect.

Torque off does not make that isolation. The diodes do. Torque off (D59) is why the duck can stay on the contacts without the servos holding it. Servo power stays on (D50). Idle is 21 mA per servo on the STS3215 sheet, as the thermal twin already uses. That idle comes from the nest through DK6, not from the cells.

The old DK2 ideal diode sat on a separate CHG+ contact. With two wires, that contact is gone. The P-FET on this board is the reverse block DK2 used to be, and it also covers the duck supply. Proposed: DK2 and the chest pad come off the nest build. DK6 and DK7 stay.

## Balance on a welded 2S

AN231, first page: "When battery packs are built with multiple cells in series, cell balancing becomes an issue." Parallel cells "will balance each other." A series string does not. The same page: the weakest cell sets the empty point, the highest cell stops the charge, and "cell balancing circuitry should be considered for optimum runtime."

This pack is two P45B cells in series, spot welded (D44). It is not a parallel pair. The P45B sheet, version 1.2, does not mention series use or balancing. It also says it is not a warranty.

The MCP73213 regulates one stack voltage. Table 3-1 has no mid-cell pin. Figure 6-1 and the eval board BOM have no balance network. This chip does not balance.

The Tenergy 32175 watches both cells (B1 is the mid tap) and its balance rows are empty (BOM line 8, POWER.md). Per-cell over-voltage and under-voltage are there. Balance is not.

So: a balancer is not required by the cell sheet that was opened, and it is not in the charger reference design. AN231 says a series pack should have balancing considered, or the weak cell ends the discharge early and the high cell ends the charge early. With the BMS in place, the dangerous case (one cell over 4.28 V, or under the discharge cut) opens the pack. The remaining case is a pack that stops charging or walking before both cells are used. That is a runtime gap, and it grows as the cells age. POWER.md already says to keep the two cells from the same batch and to check both voltages for the first 10 charges.

This board does not add a balancer. The mid tap already exists (CELL_MID to BMS B1). A bleed or a balance IC would use that tap and was not designed, because no balance-IC sheet was opened. BLOCKER for the pack owner: welded 2S, per-cell protection, no balance. Not a reason to change the 1.10 kOhm or the 8.40 V target.

## Parts

Stock is what a page showed when it was opened for this note. "Not opened" means the number is real and the live cart was not read. No prices are listed here.

| Ref | Part | Qty | Page | Stock as seen |
|---|---|---|---|---|
| U1 | Microchip MCP73213-A6SI/MF | 1 | https://www.digikey.com/en/products/detail/microchip-technology/MCP73213-A6SI-MF/2125537 | DigiKey page opened. In stock: 3,029 |
| R2 | Panasonic ERJ-3EKF1101V, 1.10 kOhm, 1 percent, 0603 | 1 | https://www.digikey.com/en/products/detail/panasonic-electronic-components/ERJ-3EKF1101V/118869 | Not opened |
| C1, C2 | TDK C2012X5R1E475M, 4.7 µF, 25 V, X5R, 1206 | 2 | eval guide Table B-1. A live distributor page was not opened | Not opened. BLOCKER if the number is no longer sold |
| F2 | Littelfuse 0287005.PXCN, 5 A ATO, in FHAC0001ZXJ | 1 | already BOM DK3 and DK4. Sheet not re-opened | Not re-opened |
| D1 | Littelfuse SMAJ10A | 1 | https://www.digikey.com/en/products/detail/littelfuse-inc/SMAJ10A/762266 | Datasheet page opened. The US stock count was not read. Not opened for quantity |
| Q1 | Diodes DMP2045U-7 | 1 | https://www.digikey.com/en/products/detail/diodes-incorporated/DMP2045U-7/4231465 and the Diodes datasheet above | Datasheet opened. The distributor text that came back did not show a quantity. Not shown |
| D2 | onsemi MMSZ5230B, 4.7 V zener | 1 | not opened | Not opened. BLOCKER until the knee is read |
| Q2 | onsemi MMBF170 | 1 | not opened | Not opened. BLOCKER for VGS(th) |
| U2 | TI LM393BIDR | 1 | https://www.ti.com/lit/ds/symlink/lm393.pdf | Sheet opened (SLCS005AH, April 2025). Distributor quantity not opened |
| U3 | TI TL431AIDBZR | 1 | not opened | Not opened. BLOCKER for 2.495 V and the minimum current |
| R1, R3, R4, R5, R6, R7, R8, R9, R10, R11 | 10 kOhm, 100 kOhm, 10 kOhm, 1 kOhm, 4.99 kOhm, 10.0 kOhm, 10.0 kOhm, 28.0 kOhm, 10.0 kOhm, 2.80 kOhm, all 1 percent 0603, ERJ-3EKF family | 1 each | family is the eval board's. Individual pages not opened | Not opened |
| D3, D4 | 1N4148 | 2 | BOM line DK5 already names one. Sheet not re-opened | Not re-opened |
| J2 / RT1 | Adafruit 372, 10 kOhm NTC, B25/50 = 3950 | 1 | https://www.adafruit.com/product/372 | Page opened. In stock. No piece count on the page |

The eval board MCP73213EV-2SOVP is the reference layout, not the part that goes in the duck. PARTS_AUDIT.md already says that. This note agrees.

The exposed pad must be soldered to copper. Board outline, layer count, and the seat in the trunk are not in this pass. NEST_CAD.md BLOCKER 3 (no seat) still stands. Mass of this board was not weighed and is not estimated here.

## Files

| File | What it is |
|---|---|
| `circuitry/CHARGER_BOARD.md` | This note |
| `circuitry/charger_board.yaml` | The board netlist, same shape as `wiring/netlist.yaml` |
| `circuitry/charger_board.kicad_sch` | KiCad schematic of the same nets. Drawing, not a fabricated board |
| `circuitry/check_charger.py` | The arithmetic. Run from the repo root: `python3 altaay_lab/circuitry/check_charger.py` |

`audit/erc.py` was run on the yaml with its output pointed outside the repo. Result: 28 components, 76 pins, 57 wires, 0 errors, 0 warnings. That run is not a change to `audit/ERC_REPORT.md`.

## Proposed edits for the owners of the other files

Not applied.

**wiring/netlist.yaml**

- Retire U6 (Adeept USB-C charger) and cables P4 and P5 as they are now.
- Add this board between JNP/JNM and BMS P+/P-. VBAT goes only to BMS P+.
- Move F2 to the board input, ahead of both the chip and DK6.
- DK6 VIN comes from the protected rail (JSYS), not from a separate SYS contact.
- Remove DKP (chest pad), DK2, the SENSE net, RT1's wire to SENSE, and the wake branch WK1. D61 has two wires.
- Keep DK6 and DK7. DK7 still blocks the nest from back-feeding the pack, and blocks the pack from running the bus while the nest is higher.
- Add three conductors to the Pi: GPIO5 pin 29 (STAT, input), GPIO6 pin 31 (enable, open drain), and pin 1 (3.3 V), with ground.
- Raise the PACK_OR domain top if the nest is 9.5 V. It is 9.2 V today. The protected rail's design top is 10.0 V because of SMAJ10A. Confirm the 2813, the BEC, and U3 against that before the domain changes.
- Do not connect PROG or STAT to the servo bus.

**BOM.md and bom.json**

- Line 11 (Adeept board) is not this charger.
- Add U1, D1, Q1, and the passives above once each live page has been opened. The 5 A fuse and the Adafruit 372 are already on the bill.
- Do not add the eval board as the in-duck charger.

**PARTS_AUDIT.md**

- The MCP73213 sheet has now been opened (DS20002190C). Dropout in the characterized table is the 0.3 V headroom: specs apply from 8.70 V for the 8.40 V option. The 6 hour timer is on the A6S option (5.4 to 6.6 h). The "missing thermistor" note is confirmed: there is no THERM pin. Die regulation at the 110 C block-diagram label is not a pack NTC.

Table 3-1 of DS20002190C, page 13, opened again on 2026-11-12 (cited datasheet). The DFN-10 pins are:

| DFN-10 | Symbol | Direction on the sheet | What the sheet says |
|---|---|---|---|
| 1, 2 | VDD | I | Battery Management Input Supply Pin |
| 3, 4 | VBAT | I/O | Battery Charge Control Output Pin |
| 5, 6 | NC | no direction | No Connection Pin |
| 7 | STAT | O | Battery Charge Status Output Pin |
| 8, 9 | VSS | no direction | Battery Management 0V Reference Pin |
| 10 | PROG | I/O | Battery Charge Current Regulation Program and Charge Control Enable Pin |
| 11 | EP | no direction | Exposed Pad Pin |

The sheet prints a dash in the direction column for NC, VSS, and EP. There is no THR pin and no thermistor input. Section 3.3 says the NC pins are no connection. The pack bead cannot land on this chip. It lands on the LM393 (CU2) and the TL431 (CU3), which pull the enable gate down. That path is cable NW in wiring/netlist.yaml.
- The in-duck part number to record is MCP73213-A6SI/MF, not the eval board.

**STATE.md**

- The electrical redo named in the nest section now has a schematic in `circuitry/`. The seat, the pin part number, and the nest supply tolerance are still open.

**DECISIONS.md**

- No new decision. D50, D59, and D61 are the rules this board follows. If the nest voltage must be held between 8.70 V and 10.0 V, that is a constraint on the gate board, for whoever owns the rim supply.

**software/SOFTWARE.md**

- Proposed, not written: GPIO5 input, low means charging. GPIO6 open drain, low stops charge. Default is charge allowed. A 45 C software stop can pull GPIO6 low inside the 0 C to 60 C hardware window. Type 1 STAT does not encode faults.

**twin/thermal**

- Proposed re-run at 2.30 W and 3.50 W, and at about 1.26 W if the die is regulating. Not run here.

**twin/dock/nest**

- No edit. The leads still end at JNP and JNM. This board is the load on those splices.

## Open blockers

1. Nest supply tolerance. The window is 8.70 V to 10.0 V. D61 says about 9.5 V, calc only. No adapter tolerance was opened.
2. Pin contact resistance on cloth, and the unfinished spring-pin part number. They belong to the nest audit. The drop budget at 1 A is 0.80 ohm round trip (calc) before the chip leaves the characterized window.
3. In-trunk thermal resistance, and Figure 5-1 not digitized. A 1 A charge that actually runs at 1 A is 2.30 W to 3.50 W, above the 1.9 W to 3.2 W twin. A die held at 110 C on a 62 C/W board is nearer 1.3 W and may miss the 6 hour timer if the pack is low for too long. Which one happens in the trunk is not known.
4. No balance on the welded 2S. Per-cell OV/UV is on the Tenergy board. AN231 says series cells should have balancing considered. No balance IC was opened.
5. Sheets not opened: TL431, MMBF170 VGS(th), MMSZ5230B knee, and a live page for C2012X5R1E475M. The comparator sheet is opened (LM393BIDR, 4 mV, 36 V).
6. No seat and no board mass. NEST_CAD.md BLOCKER 3.
7. The temperature window is inward of 0 C and 60 C after the resistor, bead, and comparator stack (worst corners 1.33 C and 58.36 C, calc). The TL431 sheet is still unread, so the reference voltage itself is not a cited number. The stack was also checked at 2.2 V and still stays inside the cell limits.
8. Type 1 STAT cannot tell a full pack from a timer fault.
