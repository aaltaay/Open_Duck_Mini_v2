# Volume prices

Written 2026-11-12 evening ET. Nothing was bought. ORDER.csv and BOM.md were read and not edited. Every line price is in VOLUME.csv. A blank price cell is BLOCKER. A number is cited or calc only.

Qty 1 for a line that this pass did not reopen is the cite already in ORDER.csv (checked 2026-11-12). Qty 100 and qty 1000 are filled only when a page printed a break that covers that buy. A single price with no table is not copied forward.

## What a duck costs, from the lines that have a price

Tools (soldering iron, tips, the 5 A cable) are one set, not one per duck. They are out of the repeat-parts sums. Out-of-stock lines stay in VOLUME.csv and out of the in-stock sum.

| Ducks | What is known | Repeat parts per duck | Lines with no price at that volume |
|---|---|---|---|
| 1 | In stock, this pass. The Pi kit is the reopened CanaKit figure, 2.00 under the ORDER.csv figure for the same kit | 730.36 including no tools. 781.29 with the one tool set (calc only) | 81 repeat lines |
| 100 | Only the three DigiKey ladders that print a 100 row, plus, on the alternate servo, the Waveshare 4-or-more tier | 2.19 on the order's own servo line. 230.53 if the 14 servos use the Waveshare tier (calc only) | 106, or 105 with that swap |
| 1,000 | No order line has a printed 1,000 price. The Waveshare page's last tier is 4 or more, with no ceiling, so 1,000 uses that tier and is not a new discount | 0.00 on the order as written. 228.34 for 14 Waveshare servos and nothing else (calc only) | 109, or 108 with that swap |

The 2.19, the 230.53, and the 228.34 are not the cost of a duck. They are the lines that had a printed break. The rest are BLOCKER.

## Does 1,000 ducks get under 380

No. Not shown. The pass line for this check is 380 per duck in parts. The Seeed servo line, which is 14 pieces, has no 100 or 1,000 price on the page opened tonight, so the order total at 1,000 is BLOCKER. Carrying the single-unit prices forward would be a guess, and it is not done.

The one in-stock duck, 781.29 with tools, is over 380. That is one duck, not a volume price.

The only multi-quantity servo tier opened tonight is the Waveshare 7.4 V unit at 16.31 for 4 or more. Fourteen of those are 228.34 (calc only). That is one line. The computer, the BEC, the cells, and the filament have no 1,000 price, so they cannot be added. 228.34 does not show a whole duck under 380.

## Servo line

The order buys 14 STS3215 from Seeed, including the knees. BOM.md line 1b is still the STS3250, and COSTS.csv has no 100 or 1,000 price for it. This file prices the order line. It does not drop line 1b from the bill.

Seeed, opened this pass: 20.00. No 10, 100, or 1,000 row. The 19.00 at 10 or more on the 2026-11-01 bill was not on the page tonight, so it is not used.

Waveshare 7.4 V, opened this pass: 16.99 at 1, 16.59 at 2, 16.39 at 3, 16.31 at 4 or more. No 100 row and no 1,000 row. The 4-or-more price is used at 100 and at 1,000 because the page prints no ceiling. Backlash was not on the page. The torque check is WAVESHARE_CHECK.md.

## DigiKey ladders opened this pass

| Line | 1 | 100 | 1,000 |
|---|---|---|---|
| MCP73213-A6SI/MF | 2.41 | 1.82 (the 100 row; a 25 row at 2.01 is also printed) | BLOCKER. No 1,000 row |
| DMP2045U-7 | 0.44 | 0.1705 | BLOCKER. The next row is a reel of 3,000, not 1,000 |
| SMAJ10A | 0.51 | 0.1975 (a 500 row at 0.14758 is also printed) | BLOCKER. The next row is a reel of 5,000 |

## Pages opened that print one price

illumn P45B, 8.99, no table. Horizon BEC, 54.95, no table. CanaKit kit, 87.95, and the bare board, 16.35, no table. MatterHackers PA6-CF, no quantity table; the qty-1 dollar stays the ORDER.csv cite.

Every other line is in VOLUME.csv. Where this pass did not open a break, qty 100 and qty 1,000 are blank.
