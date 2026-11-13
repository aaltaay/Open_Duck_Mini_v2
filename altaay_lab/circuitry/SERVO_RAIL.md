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

The slide switch stays off. While the nest is present, an LM393B open collector holds ON at the low level, so the 2815 output is off. The servos are on that output. They see 0 V. 0 V is under 14 V. Servo current on the pack is 0, so the charger sense can fall through 0.10 A and current termination can occur. The sit already rests on the mechanical stops. Unpowered friction is still not on the Feetech sheet. That BLOCKER stays. Opening the rail does not close it.

When the duck is off the mat, the clamp releases. The Pi may then drive ON through 10 kOhm. 3.3 V is above the page's approximately 1 V, and it is under the 30 V pin maximum. The pack reaches the same 2815 through DK7, at 12.6 V or less, which is under 14 V. DK6 may still bring the nest to the 2815 input. The servos are on the output, and the output is held off for the whole time the nest divider says the mat is there.

The ON pin's input current is not printed on the page that was read. Whether 10 kOhm from 3.3 V still sits above about 1 V after that current is BLOCKER. The LM393 low level was not the number copied when SLCS005AH was opened (the copied numbers are 4 mV offset and 50 nA bias). Whether that low level is under the page's approximately 1 V is BLOCKER. The wire is still the open collector to the ON pin.

The limp pose and the stand are in twin/sit/RAIL_OFF_SIT.md. The Pi and the camera are on this same switch in the netlist, so this cut turns them off too. If they stay on from the pack, their current blocks the 0.10 A termination. That sum and the fix are in circuitry/AWAKE_LOAD.md.

The divider arithmetic is calc only, and circuitry/check_bq24133.py checks it. The nest is divided by 100 kOhm over 20.0 kOhm, so the tap is the nest voltage divided by 6. The threshold is 12.1 kOhm from the BQ24133 VREF (3.3 V, cited) to the node, 10.0 kOhm to ground, and 200 kOhm from the pack so the node does not collapse to 0 V when VREF sleeps. At 15.0 V on the nest and 12.6 V on the pack the threshold is 1.789 V and the tap is 2.50 V, so the clamp is on. The tap crosses 1.789 V at 10.73 V on the nest. At 0 V on the nest and 12.6 V on the pack the threshold is 0.336 V and the tap is 0 V, so the clamp is off. A measured release on the real contacts is BLOCKER. The 15.0 V supply, the 13.6 V to 16.0 V window, and the mat are unchanged.
