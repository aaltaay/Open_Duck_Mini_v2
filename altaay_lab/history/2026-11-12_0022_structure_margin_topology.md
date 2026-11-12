# Structure margin and topology pass

2026-11-12 12:22 AM ET. Branch cursor/structure-margin-topology-a99f. Folder twin/structure/ only. Nothing installed into print/.

The 2026-11-03 structure twin left roll_to_pitch at walking safety factor 1.48 to 1.63 and the knee sheet eye at 1.63, with soft falls under 1.2 on roll_to_pitch in 7 of 10. This pass re-ran the same solver on a voxel mesh (TetGen does not recover the current STLs) and on a new load set from st_loads.py and st_falls.py. The build in that run summed to 2.808 kg (sim pass only, not weighed).

Kept geometry, FEA pass only, room temperature: roll_to_pitch walk 1.43 to 2.23, soft worst 0.54 to 0.78 (3 of 11 still under 1.2). Shin eye walk 0.79 to 1.30, soft 0.46 to 0.87. Thigh walk 1.78 to 1.71, soft 0.70 to 0.94 (the far-end pad hit the knee servo at 1.46 mm and was not kept). Neck walk 5.20 to 11.85, soft 0.38 to 0.99. Head pad was not kept (soft 1.03 to 0.97). Foot and hip roll already met both margins.

PrusaSlicer 2.7.2: the kept STLs add 47.77 g and 5.76 h. A foot interior carve kept the margin (walk 7.50, soft worst 5.80) and made the print heavier (+22.26 g and +4.27 h for the pair) because the slicer walls the pockets. It is not a swap. No print mass or print time was saved.

Hot PLA and the fall contact stiffness stay guesses. Detail: twin/structure/TOPOLOGY.md.
