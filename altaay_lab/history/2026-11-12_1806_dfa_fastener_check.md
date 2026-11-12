# DFA fastener check

2026-11-12 6:06 PM ET. Counted the CAD schedule in altaay_lab/fasteners/fasteners.json. altaay_lab/cad/fasteners/ is not in the tree.

Fitted screws 324, inserts 48, nuts 0, washers 8 (CAD check only). 37 screws are already left out. The screws twin, D39, and D42 had already taken the cuts their checks allow. This pass does not draw a new snap, clip, hinge, or twist-lock. Servo horns and case clamps stay. PR 43 and PR 46 meshes are unchanged, so the solver was not re-run. Print filament 1361.4 g and 120.6 h, same after (calc only, slicer estimate, not weighed). Builder still turns 268 screws. Fastening minutes and weighed mass are BLOCKER. Tool-free and one-tool are not met: two hex keys, plus the cross-head drivers from D36. Detail: altaay_lab/cad/dfa/DFA.md.
