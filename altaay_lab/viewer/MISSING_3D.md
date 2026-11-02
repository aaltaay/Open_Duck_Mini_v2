# MISSING_3D: what the exploded 3D view draws

2026-11-01 10:15 PM ET. Viewer runs of make_viewer_data.py at 9:42 PM ET (before) and 10:15 PM ET (now: fasteners.json, cables3d.json of 03:10 UTC, scene_extras.json). Rows: BOM_FULL.md of 03:07 UTC. Data: viewer/scene_extras.json (166 items) from blueprint/make_scene_extras.py; check: blueprint/check_scene_extras.py, blueprint/coverage.json.

| Item | BOM_FULL row | In robot | Before | Now | 3D data from | Gap left |
|---|---|---|---|---|---|---|
| Printed parts | P01 to P37 | 52 + 2 rods | 54 | 54 | URDF, print/ | none |
| STS3215 servos, horns; SG90 servos | S01 to S17 | 14, 28; 2 | yes | yes | URDF | none |
| Inserts, bearings | F17, F18 | 58, 3 | yes | yes | audit/sites.json, URDF | none |
| Boards and parts with a CAD body | E01 to E04, E07, E09, E11, E12 | 9 | yes | yes | URDF | none |
| BEC, fuse holder, 2815, Tenergy BMS, 5 V reg, camera, 4 foot switches, power splice box, USB coil | E03, E06, E08, E10, E13, E16, E22 | 13 boxes | yes | yes | placements.json, viewer seats | none |
| XT30, amp, speaker, 3 LED beads | E05, E18, E20, E21 | 6 boxes | tray | seated | cables3d.json terminals | none |
| Screws | F01 to F16 | 355 | 0 | 293 | fasteners.json | 62 skipped: 56 Feetech case screws PA2.0 and 6 SG90 bag screws have length_mm null (draw_length_mm is set); they also have no BOM_FULL row |
| Eye screw washers M2.5 x 0.5 | F04 | 8 | 0 | 8 | scene_extras (fasteners.json seats) | no BOM.md line; OD UNVERIFIED |
| Cables | C01 to C45 | 45 | 0 | 45 (57 runs) | cables3d.json | none |
| Cable ties, tie mounts, guides | K02 | not counted | 0 | 0 | cables3d.json retention | retention list empty in cables3d v1 |
| Mini-SPOX housings and crimp terminals | C47, C48 | 5, 13 | 0 | 5, 13 | scene_extras | size UNVERIFIED (Molex drawing not reachable) |
| Kit cable 5264 plugs | C35 to C45 (C46) | 22 | 0 | 22 | scene_extras | size UNVERIFIED |
| XT30 halves, cup heat shrink | E05, C49 | 2, 4 | 1 mated box | 2, 4 | scene_extras | mated placeholder still drawn too |
| USB plugs, camera FPC ends | C21, C32 | 2, 2 | 0 | 2, 2 | scene_extras | sizes UNVERIFIED |
| Pi 2 x 20 header | E11 | 1 | 0 | 1 | scene_extras | no BOM line if the bare board is bought (D7) |
| Amp speaker terminal block | E20 | 1 | 0 | 1 | scene_extras | size UNVERIFIED |
| Solder joints at pads, pins, holes, lugs, tabs, terminals | K01 | 64 | 0 | 64 | scene_extras (netlist ends at cables3d terminals) | pad spacing [I] on BMS, charger, U3, BNO055, amp, foot switches, LEDs, speaker |
| Splices | C49 | 13 | 1 box | 13 | scene_extras | power_splice box still drawn too |
| Resistors 100 ohm, 2.2 kOhm | E19, E17 | 3, 2 | 0 | 3, 2 | scene_extras | body size UNVERIFIED |
| Heat shrink on splices, cups, inline joints | C49 | 27 | 0 | 27 | scene_extras | BOM_FULL counts 137 (1 per splice end and per bare pad) |
| Foam tape pads | K10 | 6 | 0 | 6 | scene_extras (MOUNTING.md faces) | none: all 6 seats on their tape within 0.04 mm (table below) |
| Eye glass discs, projector reflector | E23, E24 | 2, 1 | 0 | 2, 1 | scene_extras (measured seats) | reflector height (test order 10) |
| microSD card, ATO 15 A fuse | E15, E14 | 1, 1 | 0 | 1, 1 | scene_extras | fuse size UNVERIFIED |
| SG90 horns (SG90 bag) | S17 | 2 | 0 | 2 | scene_extras | not in CAD; size UNVERIFIED |
| Kapton wrap on the BMS | K12 | 1 | 0 | 1 | scene_extras | none |
| Retention not decided | none | 3 | 0 | 0 | MOUNTING.md | power splices (tie or tape), speaker (B8), LED beads (no doc) |
| No body in the robot | E25, K09, K11, C46, C50 to C62, tools | | | | | controller off robot; threadlocker and flux; kit cable and wire stock drawn as plugs and tubes |

Seat-fit table refreshed 2026-11-02 about 12:05 AM ET from audit/placements.json (seat fixes applied 2026-11-01) and blueprint/coverage.json foam_fit (scene_extras run 04:08 UTC): every taped part now sits on its 1.1 mm VHB 4950 tape within 0.04 mm. blueprint/check_scene_extras.py, run 2026-11-01 about 11:58 PM ET: 1 of 166 items embedded (the P3 joint).

| Seat vs mounting surface (1.1 mm VHB 4950) | Surface | Box to surface | After tape | Seat now (zero pose, mm) |
|---|---|---|---|---|
| bec_pro | body_middle_bottom floor | 1.09 mm | 0.01 overlap | (-64.5, -0.5, -9.8): 2.8 mm lower and 7 mm to +x, where the floor slopes up behind x -81 |
| fuse_holder | battery_pack_lid | 1.11 mm | 0.01 gap | (-103.9, -20.0, 25.0): 0.9 mm to -x |
| mosfet_switch | battery_pack_lid | 1.06 mm | 0.04 overlap | (-110.9, 24.0, 36.5): 2.4 mm to -x |
| usb_slack | body_middle_bottom side wall | 1.11 mm | 0.01 gap | (-76.5, 45.9, 22.5): 1.9 mm to +y |
| reg_5v | head_bot_sheet | 1.11 mm | 0.01 gap | (40.6, 54.4, 182.6): 0.6 mm up |
| amp | head_bot_sheet | 1.11 mm | 0.01 gap | (62.0, -68.0, 180.1): 0.6 mm up (cables3d terminals) |
| P3 joint on the holder strap (PACK.MID) | holder face pressed on body_back | 0 | no room: still inside the holder | open: choose another strap access point |
| Projector reflector (15 mm tall) | 10.2 mm seat | | 4.8 mm proud | open: check on test order 10 |
