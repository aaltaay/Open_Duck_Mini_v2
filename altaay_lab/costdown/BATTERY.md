# Battery

The pack on the bill is two Molicel P45B cells in series. twin/battery/BATTERY_STUDY.md already compared P45B, P50B, P42A, P60B, Samsung 50S, Samsung 40T, and Murata VTC6, and kept the P45B unless another cell clearly won. This note adds a score with written weights, an LG sheet, and the cells that still have no price. It does not reopen the DeWalt pack.

## Load (what the pack has to do)

Walk, from the existing P45B backlash session CSV (sim pass only, 5 s bins, 514 bins, 2570 s, no fall flag in the file):

- Mean pack power 39.84 W, mean current 5.40 A, mean voltage 7.38 V.
- The 5 s bin max is 5.65 A. That is not the short peak. Short peaks stay the earlier figures: walking peaks about 10.5 to 11.3 A, and a stacked fall near 17 A (sim/CURRENT_BUDGET.md, sim pass only). The score uses 20.6 A, the shove figure already in BATTERY_STUDY.md section 8.
- Energy over that 42.8 minute log is 28.4 Wh (calc only, mean power times time). Nominal pack energy is 32.4 Wh (2 times 16.2 Wh, cited sheet). The stop comes before the cells are empty, which matches the 42.9 minute session already written up.

Stand: the walk log has no stand section. sim/ADDED_MASS_SIM.md table 3, our build, stand, mean servo bus 0.34 A (sim pass only). A new pack-watt figure for idle was not computed. Idle pack watts beyond that bus current are BLOCKER for this note.

Charge: the charger is 1.00 A typical (cited, circuitry/CHARGER_BOARD.md, MCP73213). 4.5 Ah at 1 A is 4.5 h before taper (calc only). The cell's own standard charge is 4.5 A and 1.5 h (P45B sheet, this session). 1 A is 0.22 C (calc only).

## Cells

| Cell | What was opened tonight | Continuous current used in the score | Pack Wh | Pack mass | Gate |
|---|---|---|---|---|---|
| P45B | Store page, sold out. Sheet version 1.2 re-opened: 4.5 Ah typical, 16.2 Wh, 3.6 V, 70 g, 45 A with an 80 C cut, 15 mOhm at 50 percent SOC, charge 0 to 60 C, discharge -40 to 60 C. Cycle life is not on that one-page sheet | 45 A, cited sheet | 32.4 | 140 g | Pass |
| P50B | Store page, in stock, title 5000 mAh and 60 A. Sheet numbers are the 2026-11-04 read: 18.0 Wh, 71 g, 12.8 mOhm. Not re-opened tonight. Cycle life still unread | 60 A, store title plus the earlier sheet | 36.0 | 142 g | Pass |
| Samsung 50S | Store page, in stock, title 5000 mAh and 25 A. The specification file was not re-opened. The earlier read also has 45 A with an 80 C cut. The score uses 25 A, the rating without that cut, as the battery study did | 25 A, store title | 36.0 | 144 g, earlier read | Pass, least headroom |
| Samsung 40T | Store page, sold out, title 4000 mAh and 35 A. Mass and resistance still unread (BLOCKER, already in the battery study) | 35 A, store title only | 28.8, earlier read | BLOCKER | No. Missing mass |
| VTC6 | Store page, in stock, title 3000 mAh and 15 A. Earlier Murata read: 3.12 Ah, 46.6 g. The 30 A figure with a temperature cut stays disputed there | 15 A, store title | 22.5 | 93 g | No. Under 20.6 A |
| LG INR21700-M50 | Sheet opened (13 pages). 18.20 Wh nominal, 3.63 V, 68 g plus or minus 1 g, diameter up to 21.10 mm, height up to 70.15 mm, max discharge 1.5 C (7.275 A) from 5 to 45 C, charge 4.20 V, cycle life at least 80 percent after 500 cycles. Store URL returned 404. Price BLOCKER | 7.275 A, cited sheet | 36.4 | 136 g | No. Under the walk mean, and no price |
| 2S LiPo | No pack with a size inside the grown bay was opened | BLOCKER | BLOCKER | BLOCKER | No |
| LiFePO4 | No sheet opened. The duck charger regulates at 8.40 V (cited, PR 40). A LiFePO4 charge voltage was not opened, so it is not scored | BLOCKER | BLOCKER | BLOCKER | No |

Fit: the grown bay free space is 25.7 x 44.3 x 83.5 mm (BATTERY_STUDY.md section 9, CAD check only). A 21700 can at 21.55 x 70.15 mm is the cell that bay was cut for. The M50 can is inside that. An 18650 is smaller and needs the old holder. A pouch with no drawing does not get a fit.

Shipping: FAA PackSafe, opened tonight, lithium-ion batteries limited to 100 Wh each. Every pack in the table is 22 to 36 Wh (calc only, two cells). Spares, if carried loose, are carry-on only on that page. None of these packs is over the limit.

Safety for a toy: every cell that was scored is a metal can. A pouch was not opened, so no point gap for LiPo is invented. The duck's BMS and the 70 C servo cut are unchanged. Cycle life is known only for the M50 (500 cycles to 80 percent). P45B and P50B cycle life remain BLOCKER, as the battery study already said. That weight does not pick a winner among the Molicel cells, because both score 0 there.

## How the score works

Weights, chosen here and written down so the pick can be checked. They follow D45 (simple, cheap, reliable together) and the toy use (a cell a child is near):

| Weight | Points | Rule |
|---|---|---|
| Safety | 25 | Full marks for a metal-can Li-ion on the existing BMS. No split was earned tonight |
| Peak headroom | 20 | Full marks at twice 20.6 A. Score is the fraction of that, capped at 1 |
| Runtime | 15 | Pack Wh divided by the best Wh in the table (M50, 36.4), times 15 |
| Mass | 10 | Lightest cell that also passes the 20.6 A gate is full marks. Heavier cells score in proportion. Missing mass is 0 |
| Cycle life | 10 | Full marks only with a sheet number. Unread is 0 |
| Cost per Wh | 10 | Cheapest priced cell in the table is full marks. Missing price is 0 |
| Shipping | 5 | Full marks under 100 Wh |

A cell under 20.6 A, or with a BLOCKER on price or mass, does not win. A lead under 5 points is not a clear win. That is the same bar the battery study used when it kept the P45B.

Points from build_costs.py (score.json):

| Cell | Safety | Peak | Runtime | Mass | Cycle | Cost | Ship | Total | Wins? |
|---|---|---|---|---|---|---|---|---|---|
| P45B | 25 | 20.00 | 13.35 | 10.00 | 0 | 7.87 | 5 | 81.22 | The pick |
| P50B | 25 | 20.00 | 14.84 | 9.86 | 0 | 7.29 | 5 | 81.99 | Leads by 0.77. Not a clear win. In stock |
| 50S | 25 | 12.14 | 14.84 | 9.72 | 0 | 8.75 | 5 | 75.45 | Same cell price as the P45B, less headroom |
| 40T | 25 | 16.99 | 11.87 | 0 | 0 | 10.00 | 5 | 68.86 | Cheapest per Wh, mass BLOCKER, sold out |
| VTC6 | 25 | 7.28 | 9.26 | 10.00 | 0 | 6.82 | 5 | 63.36 | 15 A, under the bar |
| M50 | 25 | 3.53 | 15.00 | 10.00 | 10 | 0 | 5 | 68.53 | 7.3 A, and no price |

## Pick

Keep the two P45B cells. The P50B scores a little higher and is the one that was in stock tonight, at a higher cell price (rows p45b_cell and p50b_cell). It fits the same can. It is the alternate if the P45B is still sold out, which is the battery study's own fallback, not a new pack. The 50S does not save money and has the least headroom of the cells that pass the gate. The M50's cycle life is the only one on a sheet, and its current is too low for this walk. LiPo and LiFePO4 stay BLOCKER until a part that fits, and that the 8.40 V charger can charge, is opened.
