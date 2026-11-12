# Electronics and printing

## Compute

The computer is the Pi Zero 2 W (D7). The bill price is row pi_zero2w_adafruit, read 2026-11-01, out of stock then, and still out of stock at that seller on 2026-11-11 (history of the parts gap). It was not re-opened tonight.

A cheaper board that runs the existing runtime was not opened. Row pi_cheaper_runtime is BLOCKER. The camera, the GPIO map, and the walk stack are already on this Pi. A new computer is a new design, and this study does not start one. There is no compute cut.

## One board instead of the BEC, the adapter, and the charger

The power path is already three catalog pieces plus the charger schematic:

- Castle CC BEC Pro, row bec_pro. POWER.md already compared other bucks and kept this one. That comparison is not redone.
- Waveshare bus adapter, row adapter_a, data only.
- The in-body charger, PR 40, schematic only. No board has been built.

A single board that merges those three was not drawn and was not quoted. Rows merged_board_qty1, merged_board_qty100, and merged_board_qty1000 are BLOCKER. A saving is not claimed. The schematic that does exist should be the one a board house quotes, not a new circuit.

## Print versus a mold

Print plan total on a 220 mm bed: 1407.2 g PLA and 126.9 h (print/PRINT_PLAN.md, slicer estimate, not a printed part). Two 1 kg spools cover that (row pla_two_spools). No spool price at 100 or at 1000 was opened, so a volume filament price is BLOCKER. Using tonight's unit price times 100 or times 1000 would be the qty-1 price, not a discount.

PR 43 already tried to take plastic out. The kept topology did not cut print mass. One foot carve made the pair heavier. There is no print-mass cut waiting in that work.

Injection molds: Protolabs help page, opened tonight, prices start around the figure in row mold_start, depending on geometry. That is not a quote for these parts. 49 files sit under print/ (counted this session). They are not 49 tools. Left and right may share a tool, and the page's starting price is the bottom of a range.

Bound, calc only, in score.json: if each of those 49 files needed its own tool at the starting price, and the molded plastic were free, the tool cost would match two spools per duck at 1221.7 ducks. Plastic is not free, and 49 is not the tool count, so this is not a saving and not a quote. It is enough to say:

- At one duck, a mold is the wrong tool. The cash is two spools.
- At 100 ducks, the starting price of a handful of tools already passes the filament cash, and this duck is more than a handful of parts. Molding the set does not win at 100 on this bound.
- At 1000 ducks, a real quote could go either way once tools are shared and the plastic price is known. Both of those are BLOCKER. No saving is entered.

Volume prices at 100 and at 1000 for servos are BLOCKER on every page opened (SERVO.md). The same is true for the merged board. The only 100-and-1000 statement that is a number is the mold bound above, and it is a bound, not a price list.
