# 2026-11-12 6:27 PM ET: the pack bead pulls the enable line down

DS20002190C Table 3-1, page 13, was opened. The DFN-10 pins are VDD, VBAT, NC, STAT, VSS, PROG, and the exposed pad. There is no thermistor pin.

Cable NW ties the bead plug to the parts already on the bill. RBIAS is 10.0 kOhm from CU3. The cold divider is 10.0 kOhm over 28.0 kOhm into CU2 INA+. The hot divider is 10.0 kOhm over 2.80 kOhm into CU2 INB-. Both open collectors pull CQEN's gate down. That is the enable path. These are the same parts as the charger bill, not a second set. The bead lead length is still BLOCKER.
