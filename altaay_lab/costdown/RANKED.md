# Ranked cuts

Order is by what to do, not by the raw dollar size. Prices are the row ids in COSTS.csv. A cut that fails the knee or the pack is listed so its size is on the record. It is not a recommendation.

| Order | Action | Quality | Money | Take it? |
|---|---|---|---|---|
| 1 | Keep the two STS3250 knees. Do not swap them back to C001 | C001 stall at 7.2 V is 1.86 Nm (calc only). Sim knee RMS is 2.19 Nm and the peak is 3.23 Nm (sim pass only). The sheet STS3250 stall at 7.2 V is 2.94 Nm, so the RMS fits and the peak still saturates. Nothing else opened fits the case and the bus and gets closer. Heat at 2.19 Nm still crosses 60 C in a few minutes (SERVO.md). The guard from PR 37 stays on | The reverse swap is row save_drop_sts3250_knees. Taking it spends that quality. The live pair is also above the bill (row knee_pair_live_vs_bill) | Keep the knees. Do not take the cut |
| 2 | Buy one Waveshare 7.4 V unit and compare backlash to a C001 before any of the 12 body servos move | Page table matches the C001 torque, current, speed, and Kt. Backlash and life were not on the page (BLOCKER). Same STS bus, so no new software if the unit matches | Row save_waveshare_12, twelve body servos. Knees stay STS3250. No 100 or 1000 price (BLOCKER) | Only after one unit matches. Not a fleet change tonight |
| 3 | Keep two P45B cells. If they are still sold out, buy two P50B | Score 81.22 versus 81.99 (BATTERY.md). Lead is 0.77, under the 5 point bar, so not a clear win. P50B has more Wh and was in stock. 50S is the same cell price with less current headroom. M50 and VTC6 miss the current. LiPo and LiFePO4 are BLOCKER | P50B costs more per cell (rows p45b_cell, p50b_cell). It is not a cut. It is the in-stock alternate the battery study already named | Keep P45B. P50B only if P45B will not ship |
| 4 | Do not change the Pi, the BEC, or the adapter, and do not start a merged board | The runtime, the camera, and the GPIO map are on this Pi. POWER.md already kept the BEC. A merged board was not quoted | Rows pi_cheaper_runtime and merged_board_qty1 are BLOCKER. No saving | No cut |
| 5 | Keep printing. Do not order molds for a 100 or a 1000 build on this bound | PR 43 did not cut print mass. A mold quote for these parts does not exist | Two spools per duck at the qty-1 price (row pla_two_spools). The 49-file bound meets that filament at 1221.7 ducks only if plastic is free (calc only, score.json). Real plastic and the real tool count are BLOCKER | No cut at 1 or at 100. At 1000, wait for a quote |

## What is not a cut

- A weaker servo on the neck or the hip yaw. The cheap catalog servos miss the peak or cost more (SERVO.md).
- A 3S pack so a 12 V servo can run. The battery study already closed a bigger bay.
- A custom motor or a custom computer. Not designed here.
- Sodium-ion, LFP, silicon-anode, or solid-state. No cell in this can at a price was opened (FUTURE.md).

## Open BLOCKER rows

- Servo prices at 100 and at 1000, every brand opened.
- Waveshare backlash and life.
- STS3250 sheet resistance: 1.2 ohm versus the stall line. The heat clock depends on which one is real.
- Joint speed at the same moment as the peak. The heat log has no speed column.
- P45B and P50B cycle life. 40T mass and resistance. LG M50 price. Any LiPo that fits. Any LiFePO4 sheet.
- Spot-weld strip, sleeve, and weld, already BLOCKER in the battery study. Not priced again.
- A board-house quote for the existing charger schematic, and any merged board.
- Filament at 100 and at 1000, and a mold quote for these parts.
- `altaay_lab/bom/order/` was not in the tree.
