# 2026-11-12 6:23 PM ET: one splice choice, pack bead, charger watts

G, VSW, SPV, and SPG now say WAGO 221 in the netlist part text. The order bill follows that text, so those four are on the wago line and off the solder line. The other splices stay solder. check_order.py passes. Nothing was bought. The WAGO page was not opened, so that line is BLOCKER and not in the total.

The pack bead RT1 is on cable NT, plug JNT, housing 0022012027. The chip has no THERM pin. The divider is the one already written: 10.0 kOhm bias, cold 10.0 over 28.0, hot 10.0 over 2.80. The old SENSE wire from the splice to the bead is out of the netlist so the two nets are not tied. Cut length is BLOCKER. BAY.md names the valley and gives no length.

Cable CE is STAT and enable to Pi pins 29 and 31. Cut length is BLOCKER. cables3d has no route, and the charger has no seat. D13's 542 mm worst route is a different wire.

The thermal table ran 1.9 W and 3.2 W. That is about 9.1 V and 9.2 V at 1.00 A (calc only). The board heat at the 9.5 V input is 2.30 W and 3.50 W (calc only). The table was not re-run. The board pair is the right heat for 9.5 V. The table is the right record of the sim that was run.
