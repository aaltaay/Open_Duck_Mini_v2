# Shin drive eye margin

2026-11-12 9:06 AM ET. Follows 2026-11-12_0627_twin_checklist_prs_34_43.md and the topology pass.

The servo-facing face of the drive eye is 2.02 mm from the knee servo (CAD check only). This session re-ran the structure-twin load scripts. The build is 2.808 kg (sim pass only). MuJoCo 4.0.1. Soft falls are 9 files: two rough seeds did not hit a printed part. On that set the stock eye is walk 0.58 and soft worst 0.54 (FEA pass only). The topology file's 1.30 is not this session.

PETG, PLA-CF, and ASA miss on every shape. PA6-CF on the stock eye is 1.26 and 0.92. A head-side web with a head recess, in PA6-CF, is walk 2.81, push 2.10, and soft worst 1.61, 0 of 9 under 1.2 (FEA pass only). The idle sheet has to be PA6-CF as well. The spacer does not govern. Bunting FFM003006010 does not fit. No new screw. The recessed web is 15.43 g and 1.74 h per part (PrusaSlicer 2.7.2) against 10.38 g and 1.09 h. Nothing was copied into print/. Hot and wet tensile of PA6-CF are BLOCKER. Detail: twin/structure/shin_eye/SHIN_EYE.md.

The structure row this replaces, from the checklist as it stood after PRs 34 to 43, was: the topology voxel pass, FEA pass only, room temperature, build 2.808 kg. Walking margin of 2 on the kept geometry: roll_to_pitch 2.41, neck 11.85, head 52.49, foot 3.86, hip roll stage 16.74. Not met on the shin drive eye, 1.30, or the thigh sheets, 1.71. Before that geometry, roll_to_pitch 1.43 and the shin eye 0.79. Soft-fall margin of 1.2 not met on roll_to_pitch (worst 0.78, 3 of 11), the shin (0.87, 3 of 11), the thigh (0.94, 2 of 11), the neck (0.99, 6 of 11), or the head (1.03, 2 of 11). Those topology numbers stay in TOPOLOGY.md. This entry does not overwrite them.
