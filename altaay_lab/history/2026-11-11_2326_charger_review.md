# Charger review fixes

2026-11-11 11:26 PM ET (America/New_York).

The automatic review on the charger schematic asked for two changes. Both are in `altaay_lab/circuitry/`.

The 0 C and 60 C dividers were sitting on the cell limits. With 1 percent resistors the hot trip could land near 60.6 C. The cold divider is now 10.0 kOhm over 28.0 kOhm (nominal trip 2.60 C). The hot divider is 10.0 kOhm over 2.80 kOhm (nominal trip 56.61 C). The worst corner, with 1 percent resistors, the bead's 1 percent resistance and beta, and 4.5 mV of comparator error, is 1.33 C and 58.36 C (calc). Both stay inside 0 C to 60 C.

The comparator is now the B version, LM393BIDR. Its sheet (SLCS005AH, April 2025) gives a 4 mV maximum offset and a 36 V supply, which covers the 17 V clamp.

The KiCad file is generated from `charger_board.yaml` and now has all 28 parts, each pin labeled with its net. `check_charger.py` fails if the drawing and the yaml disagree.
