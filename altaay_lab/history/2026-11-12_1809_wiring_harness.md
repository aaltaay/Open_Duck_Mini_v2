# 2026-11-12 6:09 PM ET: wiring harness plugs

The harness folder is `altaay_lab/wiring/harness/`. It names a plug or a solder end for every active wire in `wiring/netlist.yaml`, using the connector families already on the bill: XT30, Mini-SPOX 50-37-5033 with 08-70-1040, KK 254 08-50-0114, and WAGO 221.

The Molex 2759 sheet says 08-50-0114 is brass, 22 to 30 AWG, 2.5 A, insulation 1.57 mm maximum. The 20 AWG Pi power wires (P12, P17) stay soldered to the header, which is what `docs/assembly_guide.md` already does. A 5-pin KK housing 0022012057 covers the IMU wires. A 3-pin 0022012037 covers the eye wires. BOM line 22c had named 22-01-3027, which the 2695 series chart does not list. The chart number for the 2-circuit friction-ramp housing is 0022012027.

WAGO 221 is 24 to 12 AWG and 5 ports maximum, from the 221-413 and 221-415 sheets. The servo plus node and the servo ground node have 6 wires, so each uses one 221-415 and one 221-413. With ground and switched plus, that is the pocket pack already on BOM line 26b. No new board. No new screw. No new hole.

Charger STAT and EN (PR 40) get the 2-pin housing on Pi pins 29 and 31. Their cut length is BLOCKER. The five flush wells (PR 41) have no far plug, because that file did not choose a diode. They stay open. Wi-Fi and Bluetooth have no wire (PR 37). The camera stays the bought ribbon (PR 38).

Open BLOCKER lines are listed at the end of `wiring/harness/WIRES.md`. The kit cable gauge, the BEC lead gauge, the XT30 amp rating, the 26 AWG insulation fit, the charger cut, and the well far ends are the ones that still have no number.
