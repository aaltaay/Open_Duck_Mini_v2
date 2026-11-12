# 2026-11-11 11:23 PM ET: a felt dent unloads the nest pin, it does not add stroke

The 11:13 PM contact twin said a local dent in the felt could add pin stroke, up to the 2 mm stack, and checked that the spring would not bottom. That sign is wrong. This entry corrects it. The earlier file is kept as written.

The sit check defines compression as proud length minus the distance down to the cloth (`comp = Lp - s` in twin/dock/nest/cad/pins_sit_check.py). The soles and the seat hold the body. The tip extends into a dent, so the spring compression falls by the dent depth (calc only).

On a rigid mat the least bumper pin has 1.85 mm of compression (sim pass only). A 0.2 mm dent leaves 1.65 mm and 0.66 N. A 2.0 mm dent opens that contact by 0.15 mm. The dent is somewhere between those two depths (BLOCKER), so whether that pin stays down is BLOCKER. The seat pins still touch even at a 2.0 mm dent (1.0 mm of stroke, 0.56 N, calc only). If only one bumper pin lifts, the charge stays closed on the one-minus-pin row. If the dent is deeper than both bumper pins in that sit, the charge opens.

No hardware. The nest sims were not re-run.
