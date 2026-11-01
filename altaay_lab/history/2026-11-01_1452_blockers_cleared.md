# Blocker pass: 10 of 29 cleared, test order list added

- When: 2026-11-01 2:52 PM (America/New_York)
- Source: this commit
- Written: 2026-11-01 by Legged Robots, Grok Bot agent of Ahmed Altaay

- Rule followed: no guesses. A blocker is cleared only if measured from the upstream CAD (print STLs 730c14b, Tnkr GLB of the upstream assembly) or confirmed by a cited supplier, datasheet or upstream source read 2026-11-01.
- Cleared: B3 (lid head sits proud, measured), B4 (roll_to_pitch onto servo case pilots), B5 (antenna pilots 27.5 mm vs SG90 27.6 mm), B7 (one board; head board.stl is the Pi footprint), B9 (Camera Module 3 pattern matches head pilots), B19 (no Y-lead; neck chain off the left ankle, made lead 490 mm), B23 (1 W LED with 100 ohm), B25 (SanDisk microSD chosen), B27 (MID lead from the holder strap), B29 (order minimums).
- Still open: B1, B2, B6, B8, B10, B11 (narrowed), B12 (decision: JZK fits but 8 A), B13 to B18, B20, B21, B22 (no fitting 15 A switch), B24 (Pi Zero 2 W out of stock), B26, B28 (narrowed).
- New "Needs test order" section in BOM.md: 15 lines, $199.78, all already BOM lines. Nothing bought.
- Totals: build $716.65, with expression $796.62, with tools $935.29 (shipping excluded).
- Files: HARDWARE_AUDIT.md (section 6 rewritten, section 7 added), BOM.md, MOUNTING.md, CABLE_MAP.md, GAPS.md (A12), WIRING.md (Y-lead and B27 lines).
