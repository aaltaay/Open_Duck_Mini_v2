# 2026-11-12 6:07 PM ET: fastener audit of the duck and the nest

Measured the screws already in `fasteners/fasteners.json` and the nest screws already in `twin/dock/nest/cad/nest_parts.py`. No new screw, no new hole, no new mount. Nothing copied into `print/`. Nothing bought.

New folder: `cad/fasteners/`. `schedule.json` has all 361 robot screws (324 fitted) and the nest joints. `CHECKS.md` is the D39 and D42 pass plus the later CAD. `ASSEMBLY.md` is `BUILD_ORDER.md` with the lines that disagree. `PROPOSED_EDITS.md` lists those edits and does not apply them.

CAD check only: the link transform matches `seat_world` within 0.001 mm. Head recesses on the stock shin, knee, neck, and roll print files are open. The topology knee, shin, and neck pads, and the shin taper and web without a recess, put solid material on those heads (from 0.3 mm out to 6.3 mm or 7.9 mm). The shin counterbore files already clear the drive screws. Roll pads miss the screw heads. The chest hole is open in `print/body_front.stl`. F255 overlaps cable S10 by 0.59 mm and F249 overlaps D3 by 0.09 mm at the zero pose, head-cylinder model, not a sweep.

Calc only: nest lid screws sit 4.0 mm off the tray centre (mirror error 8.0 mm). Lid engagement is 4.0 mm against the 4.5 mm insert rule. An M3x8 bottoms in the 5.8 mm bore.

Cited: RLS TTD01_03 torque table does not apply, because its own depth line (2 x D in aluminum, or steel) is not met. Threadlocker stays Loctite 243 (BOM 19) on metal into the motor metal, as `docs/assembly_guide.md` already says.

`BUILD_ORDER.md` still says M2x6 for F127 and F129 (the file says M2x12) and M2x4 for the camera (the fitted screws are M2x5). It still drives 12 left-out screws and it omits F356 to F361.

Open items, not closed here: charger seat, nest ring lug, jack wrench size, terminal engagement, copying a no-recess STL, the chest hole, the wall card (no fastener named), flush wells versus nest pockets, build torque, and the pull-out and PA6-CF notes already in the other studies.
