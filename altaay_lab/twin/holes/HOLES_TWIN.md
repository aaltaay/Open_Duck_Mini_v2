# Holes twin: close every hole without a screw (D39; CAD check only, calc only)

Written 2026-11-04 10:12 PM ET by the V1 holes job (track 2e). Nothing printed, bought or sent.

- Inventory: every round hole of the printed STLs (531 coaxial sites of the lab scene, fasteners.json fasteners and empty_holes matched by geometry, plus a mesh scan along off-frame axes, scan_extra.py). A hole stays open only for a fitted screw or insert, screwdriver access, a vent or grille (heat twin), light, sound, the camera lens, a bearing, the antenna rod, or when another instance of the same STL uses it (the 7 mm idle horn holes of the knee sheets and foot_side, the D18 holes of roll_motor_bottom). Bought parts (PCBs, servo cases, switch, charger) are not changed.
- Closed: 72 hole stacks in 16 STLs (data/close_report.json). Plugs: one cylinder per feature on its true axis, ends cut flush by a plane fitted to the ring just outside the hole (or square to the axis where the ring is not flat), never proud; manifold3d union; every output watertight when read back, same bounds, no overlap with any part at the zero pose.
- Stress checks (method of twin/screws; data/checks.json): back shell F2 down at the mid fall level failed at 7 screws (1.06); 4 seats under the lower ears on body_middle_bottom (433, 419, 433, 419 N, root shear 12.7 MPa) give 1.67 at 7 and 1.52 at 6, so F076 goes (side 1.95, up 1.72, F1 2.4). Left eye keeps F179 and F182. Charger stays on 1 screw (USB-C end line to line in the slot; 20 N plug force from the USB Type-C ECN on extraction force, 0.144 N m, 4 N on the slot edge). SG90 tabs stay at 2: the stall torque (0.177 N m, SG90 datasheet mirror) passes on 1, the antenna hit (G6) is not modelled (BLOCKER).
- Result: screws 317 to 316, inserts 48 to 47, washers 8. Print -6.38 g and -1.22 h (x quantity), -4.2 g printed plus -1.24 g hardware on the robot.
- Limits: the cap fit is a plane; a screw comes back only with a reprint (pre-D39 STLs in git at 0b1cab5); the seats wait for coupon K2 like the D38 lips.

Run order (scratch worktree, ramcap): inventory.py, scan_extra.py, close_holes.py, checks.py, slice_runs.sh, apply_fasteners.py <repo>.
