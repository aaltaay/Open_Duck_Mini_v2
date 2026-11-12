# Cost-down

Written 2026-11-12 evening ET. Nothing was bought. No policy was trained. This study did not run the shared lab gym (overlay gym/overlays/duck). It reuses the walk log and the thermal model already in the tree.

Every dollar is in COSTS.csv. Other files name a row id when they mean a price. A number is sim pass only, calc only, or cited. If it is none of those, it is marked BLOCKER.

`altaay_lab/bom/order/` was not in the tree, so order quantities are the bill's, not a newer order folder.

## What was reused

- SERVO_UPGRADE_OPTIONS.md and DECISIONS.md D32: STS3250 on the two knees, STS3215 C001 on the other 12, same case, 2S pack kept.
- twin/knee/KNEE_TWIN.md: the knee swap already run in sim.
- twin/thermal/KNEE_HEAT_STUDY.md and PR 34: the 94.7 C body is the run with torque-off switched off. PR 37 is the software guard that stops a hot servo. This study does not replace that guard.
- twin/battery/BATTERY_STUDY.md and D44: 2S1P Molicel P45B, P50B as the in-stock alternate. The DeWalt pack stays rejected there.
- circuitry/CHARGER_BOARD.md and PR 40: MCP73213-A6SI/MF set to 8.40 V and 1.00 A for this 2S pack. D61 was not edited.
- PR 36: the parts-gap note. P45B was sold out then. It was sold out again on the store page opened tonight.
- PR 43 and twin/structure: the topology pass did not cut print mass. A foot carve made the print heavier.
- twin/thermal/twin_thermal.py and gate_p45b.py: the heat rerun calls those functions. It does not edit them.

## Files

| File | What it is |
|---|---|
| COSTS.csv | Every price, and the calc rows that are only arithmetic on those prices |
| SERVO.md | Servo comparison, mixed fleet, heat rerun |
| BATTERY.md | Load, cells, weights, score |
| FUTURE.md | Sodium-ion, LFP, silicon-anode, solid-state, and what to leave swappable |
| ELECTRONICS.md | Pi, a merged board, print versus a mold |
| RANKED.md | Cuts in order, with the quality effect |
| knee_heat_rerun.py | Calls the existing thermal model |
| knee_heat_results.json | That run |
| build_costs.py | Writes COSTS.csv and score.json |
| score.json | Score points only. No prices |
