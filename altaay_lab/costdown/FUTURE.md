# Later chemistries

No new cell was designed. The question is when a cited chemistry shows up in this can, at a price, and what is already true in the duck so a later pack can drop in.

## What was opened

Sodium-ion. CATL's own news page of 2026-06-22 (https://www.catl.com/en/news/6861.html) is a grid storage system, not a 21700 cell. It says cumulative shipments of that system are expected to reach 1 GWh by the end of 2026, with global deliveries to begin in June 2027. No price per Wh for a cell this size is on that page. A 21700 sodium-ion cell at a store price was not opened. When it reaches this size and this price: BLOCKER.

LFP in this can. No LiFePO4 cylindrical sheet was opened tonight. The charger on the duck is set to 8.40 V for a 4.2 V Li-ion cell (PR 40, cited chip table). An LFP cell does not use that voltage. The exact LFP charge voltage is BLOCKER until a sheet is opened, and the conclusion does not need the exact number: this charger is the wrong setpoint for a different chemistry.

Silicon-anode. The battery study already found pouch silicon cells and no cylindrical cell for this bay. No 21700 silicon-anode cell with a price was opened tonight. When it reaches this size and this price: BLOCKER. The LG M50 sheet that was opened is a graphite cell with a 4.20 V charge. It is not treated as a new silicon generation.

Solid-state. No retail cell in a 21700 can was opened. When it reaches this size and this price: BLOCKER.

## What to leave alone so a later pack can swap

These are already in the design. They are listed so a later change does not undo them.

1. The bay is a 21700 cavity (grown free space 25.7 x 44.3 x 83.5 mm, BATTERY_STUDY.md, CAD check only). A later cell has to be that can or smaller. Do not shrink the bay back to an 18650.
2. The cells are a spot-welded pair with an XT30, taken out with the back shell and a screwdriver (D45, not a tool-free slide). Do not glue the cells in.
3. The charger is a separate board, set to 8.40 V and 1.00 A (PR 40). A later chemistry that is still a 4.2 V Li-ion 21700 can keep that board. A sodium-ion, LFP, or solid-state cell with a different full voltage keeps the shell and replaces that one board. Do not print the charger into a shell.
4. The servo bus is regulated to 7.2 V by the BEC. A 2S pack whose nominal voltage sits well under 7.2 V will not hold that setpoint. The P45B nominal is 3.6 V per cell, 7.2 V for the pack (cited sheet). A chemistry near 3.1 or 3.2 V per cell is a board change and a bus check, not a silent swap.
5. Keep the pack under 100 Wh so the FAA carry limit opened in BATTERY.md still covers it. Two of these cells are about 32 to 36 Wh (calc only).

Nothing in the opened pages says a cheaper chemistry in this can is for sale now. The cost-down is not a chemistry change.
