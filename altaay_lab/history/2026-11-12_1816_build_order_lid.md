# 2026-11-12 6:16 PM ET: build order lengths, and a nest lid proposal

Follows the fastener audit after it merged. `BUILD_ORDER.md` now matches `fasteners.json`. F127 and F129 are M2x12. F344 and F347 are M2x5. The 12 left-out screws are no longer in a drive count. F356 to F359 and F360, F361 are in the order, on the PH0 and hex 2.0 already used for those sizes. A re-run finds no missing fitted screw and no length mismatch (cad). The 286-screw tool cast was not re-run.

The nest STL was not edited. BX0+6 has 0.0 mm of lid because of the existing chamfer (cad). The proposal keeps x 158 on the room side and mirrors it to x 174.9. y is ±62 so the posts clear the jack stand-in already in the nest file (cad). Mirror error 0.0 mm (calc). A longer insert does not raise the 4.0 mm engagement. M3x8 (BOM 17a) into a bore deepened from 5.8 mm to 6.3 mm engages 5.7 mm and stays 0.3 mm off the floor (calc). Nothing bought.

Wire gaps were recomputed on cable segments and finite cylinders (cad). F249 clears D3 by 0.13 mm. F027 overlaps P1 by 0.90 mm. No wire was moved.

Topology STLs and the chest hole stay open. They were not edited.
