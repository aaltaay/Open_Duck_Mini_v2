# Nest two-net charge path

2026-11-24 ET. Schematic and netlist for the dock Ahmed approved: nest v2, gold domes on the seat, 38 of 40 camera docks charging (sim pass only, twin/dock/camera/SEAT_CONTACTS.md). Nothing was built or bought. D61 was not edited.

The live pack is 3S (D65). The charger in the duck is the TI BQ24133 already in wiring/netlist.yaml, set to 1.006 A (calc only, the ISET divider, the same number software/autonomy uses). The MCP73213 stays the 2S record in circuitry/CHARGER_BOARD.md. It is not installed on this pack. The check is altaay_lab/circuitry/check_nest_setpoints.py.

## Why the MCP73213 does not move onto this pack

Cited, Microchip DS20002190C, as opened in circuitry/CHARGER_BOARD.md:

| Limit | Cited value | This pack |
|---|---|---|
| Regulation, option A6S | 8.40 V | 12.6 V, three cells at 4.2 V (cited, P45B version 1.2, and D65) |
| Characterized input | from 8.70 V, recommended up to 13.0 V | nest 15.0 V (calc only placement inside the 3S window below) |
| Input over-voltage | 13 V typical, 12.8 V to 13.2 V | 15.0 V is above that trip |
| Absolute maximum VDD | 18.0 V | 15.0 V is under it, and still above the over-voltage trip |
| Fast charge at 1.10 kOhm | 1000 mA typical, 900 mA to 1100 mA | 1.006 A would sit in that band (calc only) and is not a reason to use the chip |

A part that regulates 8.40 V cannot finish a 12.6 V charge. A 15.0 V nest sits above the 13 V over-voltage trip. The chip is not the in-duck charger for this netlist. circuitry/CHARGER_BOARD.md is unchanged as the 2S record.

## The two nets

D50 used four chest nets (CHG+, SENSE, GND, SYS). The mat has two conductors, plus and minus (cad/nest_v2). The duck side is five gold domes, 1.5 mm radius, 0.9 mm proud (sim pass only, SEAT_CONTACTS.md). A dome can land on either stripe, so each dome is steered.

```
adapter 15.0 V
  -- 5 A fuse -- RXEF185 -- Pololu 2815 (rim, reverse protected, ON from the signature)
  -- SMAJ16A to mat ground
  -- two foil buses

each gold dome JNW.n -- wire WELL_n -- BR1.Dn
              -- SS33 to NEST+ (cathode at P)
              -- SS33 from NEST- (anode at N)
RSIG 4.99 kOhm across BR1.P and BR1.N
NEST+ -- F2 5 A -- BQ24133 PVCC
BQ24133 pack pins -- BMS P+ / P- only
NEST- -- BMS P-

fused pack -- DK7 -- Pololu 2815 servo switch -- servo rail
fused pack -- J5IN (5 V interface, pack domain, not tied to U3 in this change)
```

Awake while docked is kept as a rule. The servo rail stays off while the nest is present (circuitry/SERVO_RAIL.md), so the servos never see 15.0 V. The Pi stays a pack-domain load. J5IN is the fused pack ahead of the servo switch, domain PACK_9V0_12V6, the same domain U3.VIN already uses. This change does not move cable P13 and does not put the nest on the 5 V pin. The 5 V seat can tie U3.VIN to J5IN, and drop the VSW feed, without changing the 5 V output net or the nest voltage. Until that tie, the active neck wire is still P13 from VSW.

DK6 no longer feeds the servo switch. Those wires are status superseded in wiring/netlist.yaml. DK7 stays.

## Set points, each one against a cited limit

Charge current 1.006 A is calc only (154 kOhm over 10.0 kOhm from 3.3 V, circuitry/BQ24133_BOARD.md). Nest voltage 15.0 V is the point chosen inside the window below (calc only, problems/NEST3.md).

| Set point | Cited limit | Result |
|---|---|---|
| 1.006 A | BQ24133 fast charge 0.6 A to 2.5 A (SLUSAF7D) | inside |
| 1.006 A | P45B maximum charge 13.5 A, standard charge 4.5 A (version 1.2) | under both |
| 12.6 V | P45B charge voltage 4.2 V per cell, times 3 (calc only) | equal |
| 12.6 V | PCM-L04S30-566 charge voltage 12.6 V, charge current 20 A (D65) | voltage matches, current under 20 A |
| 1.006 A | Littelfuse 0287005.PXCN, 5 A, 32 V, the charge fuse already in the netlist | under the fuse, under 32 V |
| 1.006 A | Vishay SS33, IF(AV) 3.0 A, VRRM 30 V, VF 0.50 V max at 3.0 A (document 88751, 23 Apr 2020) | under 3.0 A. One dome may carry the pole |
| 15.0 V | BQ24133 recommended input 4.5 V to 17 V, PVCC absolute max 20 V, AVCC absolute max 30 V | inside |
| 15.0 V to 16.0 V | SMAJ16A standoff 16.0 V, clamp 26.0 V at 15.4 A (problems/NEST3.md) | 15.0 V does not conduct the TVS. 26.0 V is under SS33 30 V and under the Pololu 2815 40 V |
| Window at the chip | above 13.6 V (12.6 V plus the 1 V the EVM note asks for) and at or under 16.0 V | the stacked bound below |

Stacked drop at 1.006 A, calc only, using cited maximums together. This is a bound, not a measurement.

| Drop | Number | Source |
|---|---|---|
| Two SS33 | 1.00 V | 2 times 0.50 V, the cited maximum at 3.0 A, used as an upper bound at 1.006 A |
| RXEF185 | 0.121 V | RMAX 0.12 ohm as supplied, times 1.006 A |
| Rim switch | 0.013 V | Pololu 2815, 13 milliohm maximum at a 4.5 V gate, times 1.006 A |
| Mat wire | 0.038 V | 0.038 ohm, calc only, NEST_V2.md, times 1.006 A |
| Two contacts | 0.200 V | the bench ceiling of 0.10 V each (BENCH_CONTACT.md). Not a measurement |

15.0 minus that sum is 13.628 V (calc only). That is 0.028 V over 13.6 V and under 16.0 V. Contact resistance on this foil is still BLOCKER. If a contact is over the 0.10 V ceiling, this bound does not hold.

RXEF185 hold current is 1.85 A at 20 C and 1.17 A at 60 C (cited rerating). 1.006 A is under 1.17 A, so the PTC holds through the P45B charge limit of 60 C. At 70 C the hold is 1.00 A, under 1.006 A. The duck does not charge at 70 C (cell sheet). Trip current is 3.70 A, above 1.006 A, so a normal charge does not trip it.

## Protections

**Reverse polarity.** Each dome uses two Vishay SS33 diodes, so a dome on either stripe still feeds NEST+ and NEST- the right way. The sheet lists polarity protection as an application. VRRM 30 V is above the 26.0 V clamp. The rim switch is a second Pololu 2815, which the product page describes as a high-side MOSFET with reverse voltage protection, 4.5 V to 40 V (circuitry/SERVO_RAIL.md, page read 2026-11-13). A reversed adapter does not reach the mat. The BQ24133 RBFET is the pack-side reverse block already in circuitry/BQ24133_BOARD.md. The CSD17313 on-resistance was not opened. That BLOCKER stays.

**Short.** Littelfuse 0287005.PXCN, 5 A, is in series on the rim and the duck still has F2, 5 A, ahead of the charger. A sustained short above 5 A opens the fuse. The BQ24133 input limit is 1.983 A (calc only, the ACSET divider). That limit is inside the charger. It does not see a short across the mat. The fuse and the PTC do.

**Wet mat and a coin.** The rim supply stays off until the duck presents 4.99 kOhm, 1 percent, across the two nets. The mat biases that resistor from 15.0 V through 47.5 kOhm, 1 percent. The divider is 1.426 V nominal (calc only). With 1 percent on both resistors the ends are 1.400 V and 1.452 V (calc only). The LM393BIDR window is 1.20 V to 1.65 V, so the corners stay inside, and a 4 mV offset (cited, SLCS005AH, the number already copied in CHARGER_BOARD.md) does not push them out. An open mat sits near 15 V. A coin sits near 0 V. Both are outside the window, so the 2815 ON pin is held low and the mat stays dark. A wet film that is not 4.99 kOhm stays dark for the same reason. The ON pin current of the 2815 was not on the page that was read (BLOCKER, same as SERVO_RAIL.md). The wet resistance of this felt was not measured (BLOCKER). A leak that appears after the gate has already turned on, and that keeps the total under the 1.17 A hold at 60 C, does not open the PTC. That residual is BLOCKER until the felt is measured.

The LM393 low level against the 2815's about 1 V off threshold was not copied from the comparator sheet. BLOCKER, same as SERVO_RAIL.md.

## Heat

The installed charger loss at 1.006 A is in twin/thermal/DOCKED_AWAKE.md (sim pass only for the shell, calc only for the watts). It is not the 1.9 W to 3.2 W MCP73213 band. That band was a 2S linear charger. This pack does not use that charger.

## 5 V rail

U3 stays the Pololu D30V30F5. Its input domain stays PACK_9V0_12V6. Its output net stays 5V. Cable P13 is unchanged. J5IN is the only new node on that domain. A later 5 V 5 A regulator can replace U3 if its input accepts the pack window and its output stays on net 5V. This file does not set a 5 A budget and does not move the neck wire.

## Files

| File | What it is |
|---|---|
| circuitry/NEST_TWO_NET.md | This note |
| circuitry/nest_two_net.yaml | The same nets, one block per part |
| circuitry/check_nest_setpoints.py | The arithmetic. Run from the repo root |
| wiring/netlist.yaml | Duck side and the superseded chest wires. Cable NEST is status nest so the older sheets do not have to be redrawn |
