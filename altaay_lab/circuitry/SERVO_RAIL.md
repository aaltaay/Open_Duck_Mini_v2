# Docked servo rail

2026-11-13 ET. The nest supply stays 15.0 V. The mat in problems/NEST3.md is not redrawn: 20 mm stripes, 5 mm felt gaps, five wells 3 mm across with centres 12 mm apart. D61 was not edited.

The unfixed dock puts that 15.0 V on the servo bus through DK6. The 3S walk sets the BEC to 16 V, so the BEC is in dropout and the servos see 15.0 - 0.3 = 14.7 V (calc only, twin/thermal/BQ24133_HEAT.md). The C018 page range used in the 12 V study is 4 V to 14 V. 14.7 V is outside that page.

Three cited ways to get the servos back inside that page. One is the pick.

## Drop the nest to 13.6 V

The EVM note says the supply should sit about 1 V above the battery regulation, so 13.6 V at the chip at the end of charge (cited, problems/NEST3.md). 13.6 V is under 14 V, so a perfect wire from that supply to a servo would be inside the page.

It is not a perfect wire. NEST3 set the supply at 15.0 V so the round trip can drop 1.4 V, which is 1.4 ohm at 1.00 A (calc only), before the chip input is 13.6 V. A supply set at 13.6 V has none of that drop left. Contact resistance was not measured (BLOCKER, the contact twin). The adapter tolerance is not published (BLOCKER, NEST3). The gap from 13.6 V up to the 14 V page is 0.4 V (calc only). That 0.4 V is not enough to hold both ends once those two open items move the rail. This option is not the pick. The mat would not have changed, and it does not change with the option below either.

## BATFET, so the servos see only the pack

SLUSAF7D: when a qualified adapter is present, the system is connected to the adapter. Otherwise the system is connected to the battery. BATFET is the P-channel between the battery and that system node, and it turns off once the adapter is above the pack. Servos wired to that system node see the adapter while the duck is docked. That is the 15 V rail again. The drop in the input FETs is not a number, because the CSD17313 sheet named in section 10.2.2.5 was not opened (BLOCKER). It is not shown to bring 15 V under 14 V.

Wiring the servos straight to the pack, and not to that system node, does stay under 14 V. Three cells at 4.2 V are 12.6 V, which is 1.4 V under 14 V (calc only). The charge then cannot finish on current. Precharge and termination are one tenth of the fast-charge current (cited, ISET pin). At 1.00 A that tenth is 0.10 A. Fourteen servos at the 21 mA sheet idle are 0.294 A (calc only, 14 x 0.021). 0.294 A does not fall through 0.10 A, so the current termination never sees an empty pack. The sheet's note that the system can be tied to the battery is in the 1-cell discussion. It is not stated for three cells. This option is not the pick.

## Cut the servo rail while docked

This is the pick. The switch that already feeds the servos is the Pololu 2815 (item 2815, https://www.pololu.com/product/2815, read 2026-11-13). The page's opening sentence for this item: a high-side MOSFET that can deliver continuous currents up to around 16 A at 4.5 V to 40 V. 15.0 V on its input is inside that range. The comparison table on the same page: combined on resistance 13 milliohm maximum at a 4.5 V gate, and 8.6 milliohm maximum at 10 V.

The same page, "Using the MOSFET Slide Switch": if the physical slide switch is in the off position, the ON pin controls the MOSFETs. Driving ON low, or leaving it disconnected, leaves the switch off. Driving ON beyond approximately 1 V turns the switch on. The ON pin maximum is 30 V, independent of the input voltage.

The servos are on the switch output. While that output is off they see 0 V, which is under 14 V, and their current on the pack is 0, so the charger sense can fall through 0.10 A. The sit rests on the mechanical stops. Unpowered friction is still not on the Feetech sheet. The bench and the zero-friction holding-torque runs are in twin/sit/FRICTION_HOLD.md. That BLOCKER stays until the bench is measured.

The nest does not connect to the switch input. DK6 is not on SW1.VIN. The only feed is the pack through DK7, at 12.6 V or less. Turning the switch on while the duck is still on the mat cannot put the 15.0 V nest on the servos.

The Pi drives the ON pin, and a hardware interlock forces it off during charge. Dock detect turns on a P-channel FET (onsemi FDME910PZT, VGS absolute maximum ±8 V, threshold -0.4 V to -1.5 V, sheet opened). That FET raises the gate of an N-channel clamp (onsemi 2N7002, VGS absolute maximum ±20 V, threshold 1.0 V to 2.5 V at 250 µA, continuous drain 115 mA, sheet opened). The clamp shorts ON to ground. A second 2N7002, gated by the Pi end-charge line, pulls that gate back down, so the clamp releases. The Pi rail-request line still has to drive ON through 10 kOhm above about 1 V. Charge ends at the same moment: the end-charge line also turns a 2N7002 across ISET, and ISET below 40 mV disables the charger (cited).

| Dock | Pi end-charge | Pi rail request | Clamp | Rail |
|---|---|---|---|---|
| no | no | no | off | off |
| no | no | yes | off | on, pack |
| no | yes | no | off | off |
| no | yes | yes | off | on, pack |
| yes | no | no | on | off, charge continues |
| yes | no | yes | on | off, the request loses to the clamp |
| yes | yes | no | off | off, charge already disabled |
| yes | yes | yes | off | on, pack, duck still seated |

The rail is on only when the Pi requests it and either the nest is gone or the Pi has ended the charge. `check_bq24133.py` checks that table. The Pi writes the sit commands, raises end-charge, then raises the rail request, and only then runs the stand. The mat can still be touching. The 2N7002 on-resistance at a 3.3 V gate was not on the pages opened. BLOCKER for that ohm. The fight through 10 kOhm stays under 1 V if that resistance is under 4.3 kOhm (calc only, 3.3 x R / (R + 10000) < 1). The opened threshold says 3.3 V is above 2.5 V, and 0.33 mA is inside the 115 mA continuous rating.

The ON pin's input current is not printed on the page that was read. Whether 10 kOhm from 3.3 V still sits above about 1 V after that current is BLOCKER. The LM393 low level was not the number copied when SLCS005AH was opened (the copied numbers are 4 mV offset and 50 nA bias). Whether that low level is under the page's approximately 1 V is BLOCKER. The wire is still the open collector to the ON pin.

The limp pose and the stand are in twin/sit/RAIL_OFF_SIT.md. The Pi and the camera are on this same switch in the netlist, so this cut turns them off too. If they stay on from the pack, their current blocks the 0.10 A termination. That sum and the fix are in circuitry/AWAKE_LOAD.md.

The divider arithmetic is calc only, and circuitry/check_bq24133.py checks it. The nest is divided by 100 kOhm over 20.0 kOhm, so the tap is the nest voltage divided by 6. The threshold is 12.1 kOhm from the BQ24133 VREF (3.3 V, cited) to the node, 10.0 kOhm to ground, and 200 kOhm from the pack so the node does not collapse to 0 V when VREF sleeps. At 15.0 V on the nest and 12.6 V on the pack the threshold is 1.789 V and the tap is 2.50 V. The LM393B output sinks when the inverting input is above the other input, and it is high impedance the other way (SLCS005AH section 7.2.2.1). The nest tap is the inverting input and the threshold is the other input, so 2.50 V above 1.789 V pulls the dock flag low and the clamp FET can turn on. The tap crosses 1.789 V at 10.73 V on the nest. At 0 V on the nest and 12.6 V on the pack the threshold is 0.336 V and the tap is 0 V, so the flag releases and the clamp stays off unless something else drives it. The Pi end-charge line can release the clamp while the flag is still low. A measured release on the real contacts is BLOCKER. The 15.0 V supply, the 13.6 V to 16.0 V window, and the mat are unchanged.
