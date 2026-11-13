# BQ24133 charger board

Schematic only. No board has been built, and no electrical measurement of this circuit exists. The arithmetic is in `circuitry/check_bq24133.py` (calc only). The drawing is `circuitry/bq24133_board.kicad_sch`, one box per part in `circuitry/bq24133_board.yaml`.

This is the 3S board. `circuitry/CHARGER_BOARD.md` stays the 2S MCP73213 record. Nothing in that file was removed. This file does not edit `wiring/netlist.yaml`. The servo rail while docked is `circuitry/SERVO_RAIL.md`. The mat is not redrawn.

## Sources

| What | Document | Where |
|---|---|---|
| Charger | TI BQ24133, SLUSAF7D, September 2020 | https://www.ti.com/lit/ds/symlink/bq24133.pdf |
| Input FET example | The same sheet, section 10.2.2.5, names NexFET CSD17313 as the EVM Q1 | That section. The CSD17313 sheet was not opened. |
| Switch the servos use | Pololu 2815 | https://www.pololu.com/product/2815 |
| Window comparator | TI LM393BIDR, SLCS005AH, April 2025. Offset 4 mV and bias 50 nA were the numbers copied when that sheet was opened. | circuitry/CHARGER_BOARD.md |
| Pack NTC | Adafruit 372, 10 kOhm at 25 C, lookup 31.77 kOhm at 0 C and 2.472 kOhm at 60 C | circuitry/CHARGER_BOARD.md |
| Contact TVS | Littelfuse SMAJ16A, standoff 16.0 V, clamp 26.0 V at 15.4 A | problems/NEST3.md |
| Cell | Molicel P45B, version 1.2, charge 0 C to 60 C | circuitry/CHARGER_BOARD.md |

## What the chip is set to

CELL is tied to VREF. The regulation table says that is 3 cells, 12.6 V, measured on SRN (cited). VREF is the 3.3 V reference (cited, the VREF pin). A 1 µF ceramic sits from VREF to AGND (cited, that pin).

Fast charge uses I = VISET / (20 x Rsr), and KISET is 5 A/V when Rsr is 10 milliohm (cited). The divider is 154 kOhm over 10.0 kOhm from 3.3 V, so VISET is 0.2012 V and the current is 1.006 A (calc only). 0.2012 V is inside the 0.12 V to 0.5 V ISET range (cited). The sense voltage at 1.006 A and 10 milliohm is 10.06 mV (calc only). The accuracy table prints ±8 percent at 20 mV and ±25 percent at 5 mV. It does not print a 10 mV row, so a single percent at 1.006 A is BLOCKER. Disable is ISET falling through 40 mV. Enable is ISET rising through 120 mV (cited). 0.2012 V is above 120 mV.

Input current uses KDPM of 2.5 A/V when the adapter sense is 20 milliohm (cited). The divider is 31.6 kOhm over 10.0 kOhm from 3.3 V, so VACSET is 0.793 V and the limit is 1.983 A (calc only). That is above the 1.006 A charge and below the 2.5 A fast-charge maximum.

OVPSET uses the 1.6 V reference, 1.55 V to 1.65 V (cited). The divider is 102 kOhm over 10.0 kOhm from the fused nest. At 18.0 V the pin is 1.607 V (calc only). The 1.6 V trip is 17.92 V at the input (calc only). The 1.55 V trip is 17.36 V and the 1.65 V trip is 18.48 V (calc only). All three are under the 20 V PVCC absolute maximum. The 16.0 V top of the NEST3 window is under 17.36 V, so a supply inside that window does not open the input FETs. The 1 µs deglitch against a 26.0 V clamp is still the open item NEST3 already states. This divider does not close that microsecond.

The safety timer is 5.6 min/nF (cited). 68 nF is 380.8 min, which is 6.35 h (calc only). The precharge timer is 30 min (cited). Pulling TTC low would disable termination, so TTC is the capacitor, not a short.

Table 10-2 at 1 A gives 6.8 µH and 10 µF. The resonant frequency of that pair is 19.3 kHz (calc only), inside the 15 kHz to 25 kHz range the sheet asks for. Ripple at 15.0 V in, 12.6 V out, 1.6 MHz, and 6.8 µH is 0.185 A (calc only). The saturation current has to clear 1.006 A plus half of that ripple, 1.099 A (calc only). No inductor order code was opened. BLOCKER for the part number. The 6.8 µH value is the cited one.

PVCC wants at least 10 µF (cited, the PVCC pin). Section 10.2.2.2 suggests 20 µF for a 2.5 A charge, 25 V, X5R or X7R. This board fits 20 µF as two 10 µF parts, which also covers the 1 A case. The output capacitor is the table's 10 µF, 25 V. AVCC is 1 µF and a 10 ohm resistor from the fused adapter node, before the input FETs (cited, the AVCC pin says the resistor comes from the input side; 10 ohm is also inside the 4.7 ohm to 30 ohm range in Figure 10-2). Section 9.3.10 says AVCC has to be 300 mV above SRN before the adapter FETs turn on. Tying AVCC to the system node, which those FETs isolate from the adapter, cannot make that difference, so the resistor does not land there. REGN is 1 µF (cited). Bootstrap is 0.047 µF from SW to BTST (cited). The 0.1 µF filters on ACP, ACN, SRP, and SRN are the ones those pins name. Capacitor order codes were not opened. BLOCKER for the catalog numbers. The values above are the cited ones.

TS is held at 0.60 of VREF by 10.0 kOhm over 15.0 kOhm (calc only). Cold suspend is above 72.5 percent of VREF at the low end of that threshold, and the hot cutoff is below 45.2 percent at the high end of that threshold (cited, VLTF 72.5 to 74.5 percent, VTCO 44.2 to 45.2 percent). 0.60 sits between 0.488 and 0.725, so the chip's own TS window stays open. The pack window is still the Adafruit 372 and the LM393 dividers from the 2S board: 10.0 kOhm over 28.0 kOhm cold, 10.0 kOhm over 2.80 kOhm hot. Those trips are 2.60 C and 56.61 C nominal (calc only, already in CHARGER_BOARD.md). The comparator outputs pull ISET to ground outside that window. The LM393 low voltage against the 40 mV disable threshold was not copied from SLCS005AH. BLOCKER for that one comparison.

The input FETs are the sheet's common-source pair. ACDRV goes through 4 kOhm to both gates. CMSRC goes through 4 kOhm to the common source (cited, those two pins). Q1 is the CSD17313 the sheet names. Q2 is the same N-channel example. The CSD17313 sheet was not opened, so its on resistance is BLOCKER. Q3, the BATFET, is a P-channel from the pack to the charger system node, gate through 1 kOhm from BATDRV (cited, that pin). The sheet does not name a Q3 order code. BLOCKER for that part number. The charger system node is not the servo bus. SERVO_RAIL.md is why.

SMAJ16A stays on the fused contact node, as NEST3 already has it. Its 26.0 V clamp is under the 30 V AVCC rating and over the 20 V PVCC rating. The ACFET is what opens PVCC. The 1 µs gap stays BLOCKER.

## BOM lines

No prices. An order code that was not opened is marked BLOCKER. The electrical value is still the one in the column.

| Ref | Part | Qty | Cited | Order code |
|---|---|---|---|---|
| U1 | TI BQ24133, 24-pin VQFN | 1 | SLUSAF7D | BQ24133. The RGY package is the thermal table's package. A tape suffix was not chosen. |
| Q1, Q2 | N-channel ACFET and RBFET | 2 | SLUSAF7D section 10.2.2.5 names CSD17313 as Q1 | CSD17313 for Q1. Q2 uses the same example. The CSD17313 sheet was not opened. BLOCKER for on resistance. |
| Q3 | P-channel BATFET | 1 | BATDRV pin: P-channel, source at the system node, drain at the pack, 1 kOhm from BATDRV | Order code not in the sheet. BLOCKER. |
| L1 | 6.8 µH | 1 | Table 10-2, 1 A column | Order code not opened. BLOCKER. Saturation above 1.099 A (calc only). |
| RSNS | 10 milliohm | 1 | KISET condition, Rsr = 10 milliohm | Order code not opened. BLOCKER. |
| RAC | 20 milliohm | 1 | KDPM condition, Rsense = 20 milliohm | Order code not opened. BLOCKER. |
| CPV1, CPV2 | 10 µF, 25 V, X5R or X7R | 2 | PVCC pin, at least 10 µF. Section 10.2.2.2 suggests 20 µF at 2.5 A. | Order code not opened. BLOCKER. |
| COUT | 10 µF, 25 V, X5R or X7R | 1 | Table 10-2, 1 A column | Order code not opened. BLOCKER. |
| CAV, CREG, CVRF | 1 µF ceramic | 3 | AVCC, REGN, and VREF pins | Order code not opened. BLOCKER. |
| CBT | 0.047 µF | 1 | BTST pin | Order code not opened. BLOCKER. |
| CACP, CACD, CSRP, CSRD | 0.1 µF | 4 | ACP, ACN, SRP, SRN pins | Order code not opened. BLOCKER. |
| CTTC | 68 nF | 1 | TTC pin, 5.6 min/nF. 6.35 h (calc only). | Order code not opened. BLOCKER. |
| RAV | 10 ohm | 1 | AVCC pin | Order code not opened. BLOCKER. |
| RACDRV, RCMS | 4.00 kOhm | 2 | ACDRV and CMSRC pins | Order code not opened. BLOCKER. |
| RBAT | 1.00 kOhm | 1 | BATDRV pin | Order code not opened. BLOCKER. |
| RIH, RIL | 154 kOhm, 10.0 kOhm | 1 each | ISET divider, 1.006 A (calc only) | Order code not opened. BLOCKER. |
| RAH, RAL | 31.6 kOhm, 10.0 kOhm | 1 each | ACSET divider, 1.983 A (calc only) | Order code not opened. BLOCKER. |
| ROH, ROL | 102 kOhm, 10.0 kOhm | 1 each | OVPSET divider, 17.92 V trip (calc only) | Order code not opened. BLOCKER. |
| RTS, RTB | 10.0 kOhm, 15.0 kOhm | 1 each | TS held at 0.60 of VREF (calc only) | Order code not opened. BLOCKER. |
| RST | 10 kOhm | 1 | STAT pin, 10 kOhm pullup | Order code not opened. BLOCKER. |
| U2, U3 | TI LM393BIDR | 2 | SLCS005AH, already opened for the 2S window | U2 is the pack window. U3 channel A holds the 2815 ON pin low. |
| NTC | Adafruit 372 | 1 | CHARGER_BOARD.md | The bead already chosen there. |
| RB, RCT, RCB, RHT, RHB | 10.0 kOhm, 10.0, 28.0, 10.0, 2.80 kOhm | 1 each | The 2S window, trips 2.60 C and 56.61 C (calc only) | Same values as CHARGER_BOARD.md. |
| TL, RTLF | TL431, 4.99 kOhm | 1 each | The 2S reference. The TL431 sheet was not opened. | 2.495 V and the minimum cathode current stay BLOCKER, as in that note. The trip ratios do not need the absolute voltage. |
| RVT, RVB, RVP | 12.1 kOhm, 10.0 kOhm, 200 kOhm | 1 each | ON threshold, 1.789 V docked and 0.336 V with VREF asleep (calc only) | Order code not opened. BLOCKER. |
| RNT, RNB | 100 kOhm, 20.0 kOhm | 1 each | Nest tap, nest voltage divided by 6 (calc only) | Order code not opened. BLOCKER. |
| RON | 10 kOhm | 1 | GPIO to the 2815 ON pin | Order code not opened. BLOCKER. The ON pin current is BLOCKER in SERVO_RAIL.md. |
| TVS | Littelfuse SMAJ16A | 1 | problems/NEST3.md | Same part that note already uses. |
| F1 | 5 A ATO fuse, the existing holder | 1 | CHARGER_BOARD.md | Same fuse the 2S board already names. |
| JON | wire to Pololu 2815 ON | 1 | SERVO_RAIL.md | The 2815 is already the robot switch. This board does not add a second power switch. |
