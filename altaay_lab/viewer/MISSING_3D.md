# MISSING_3D: what the exploded 3D view draws

2026-11-02 about 5:15 AM ET (agent INT, integration pass): rows Eye screw washers, Cables, Cable ties and tie mounts, Mini-SPOX, Splices, Foam, Kapton and No body from the viewer run of 10:14 UTC (make_viewer_data.py --write-bom, after blueprint/make_scene_extras.py ran again with agent PRT's generator edits: the two 0.3 mm washers per eye screw, no D9 sleeves, the SP4 and SP5 housings and crimps; cables3d.json of the D25 pass, retention of 4:31 AM ET). BOM_FULL.md row ids of that run.

2026-11-02 about 2:10 AM ET (agent PRT): rows Inserts, Screws, Eye screw washers, Mini-SPOX, Kit cable plugs, XT30, USB, Splices, Heat shrink, Foam, Kapton and No body from the viewer run of 07:04 UTC (make_viewer_data.py --write-bom: BOM_FULL.md row ids of that run, scene_extras.json with the 16 eye washers, cables3d.json of 04:50 UTC, netlist.yaml of 1:59 AM ET); in those rows Before is the viewer run of 06:05 UTC. Earlier: 2026-11-01 10:15 PM ET. Viewer runs of make_viewer_data.py at 9:42 PM ET (before) and 10:15 PM ET (now: fasteners.json, cables3d.json of 03:10 UTC, scene_extras.json). Rows Screws, washers, Cables and ties refreshed 2026-11-02 about 1:08 AM ET from the viewer run of 06:05 UTC (agent NL2). Rows: BOM_FULL.md of 03:07 UTC. Data: viewer/scene_extras.json (166 items) from blueprint/make_scene_extras.py; check: blueprint/check_scene_extras.py, blueprint/coverage.json.

| Item | BOM_FULL row | In robot | Before | Now | 3D data from | Gap left |
|---|---|---|---|---|---|---|
| Printed parts | P01 to P37 | 52 + 2 rods | 54 | 54 | URDF, print/ | none |
| STS3215 servos, horns; SG90 servos | S01 to S17 | 14, 28; 2 | yes | yes | URDF | none |
| Inserts, bearings | F21, F22 | 58, 3 | yes | yes | audit/sites.json, URDF | none |
| Boards and parts with a CAD body | E01 to E04, E07, E09, E11, E12 | 9 | yes | yes | URDF | none |
| BEC, fuse holder, 2815, Tenergy BMS, 5 V reg, camera, 4 foot switches, power splice box, USB coil | E03, E06, E08, E10, E13, E16, E22 | 13 boxes | yes | yes | placements.json, viewer seats | none |
| XT30, amp, speaker, 3 LED beads | E05, E18, E20, E21 | 6 boxes | tray | seated | cables3d.json terminals | none |
| Screws | F01 to F19 | 355 | 0 | 355 | fasteners.json | 62 (56 Feetech case screws PA2.0, 6 SG90 bag screws) drawn at the drawing length: their length is not chosen. The 8 eye screws are drawn 0.6 mm out of their seat, heads on the washer stack (fasteners/VIEWER_NOTE.md) |
| Eye screw washers, two 0.3 mm per screw | F20 (BOM 17l) | 16 | 8 discs | 16 discs | scene_extras.json (blueprint/make_scene_extras.py writes two 0.3 mm discs per screw stacked on the fasteners.json axis, D21 note) | none |
| Cables | C01 to C47 | 47 | 0 | 47 (62 runs) | cables3d.json | none; cables3d.json marks D12, S2 and S7 fail: fixed-length parts that fit taut, test fits (C3 WARN) |
| Cable ties, tie mounts | K02, K09, K10 | 75 ties; 32 MB3A and 23 ABM1M-AT-C mounts | 0 | 75 | cables3d.json retention (D25) | none: 6 stock holes, 3 drilled tie-hole pairs and 2 ties to a neighbour cable need no other part; 9 bundle ties are checked at the TEST_PLAN 1.4 test fit (HARDWARE_AUDIT B35) |
| Mini-SPOX housings and crimp terminals | C49, C50 | 7, 17 | 0 | 7, 17 | scene_extras | size UNVERIFIED (Molex drawing not reachable) |
| Kit cable 5264 plugs | C37 to C47 (C48) | 22 | 0 | 22 | scene_extras | size UNVERIFIED |
| XT30 halves, cup heat shrink | E05, C51 | 2, 4 | 1 mated box | 2, 4 | scene_extras | mated placeholder still drawn too |
| USB plugs, camera FPC ends | C23, C34 | 2, 2 | 0 | 2, 2 | scene_extras | sizes UNVERIFIED |
| Pi 2 x 20 header | E11 | 1 | 0 | 1 | scene_extras | no BOM line if the bare board is bought (D7) |
| Amp speaker terminal block | E20 | 1 | 0 | 1 | scene_extras | size UNVERIFIED |
| Solder joints at pads, pins, holes, lugs, tabs, terminals | K01 | 64 | 0 | 64 | scene_extras (netlist ends at cables3d terminals) | pad spacing [I] on BMS, charger, U3, BNO055, amp, foot switches, LEDs, speaker |
| Splices | C51 | 15 | 13 | 15 | scene_extras (13); JFI and JFO placed by make_viewer_data.py step 10f on the routed P7 runs | power_splice box still drawn too; the 7 splices that sit on a cables3d.json seat follow it at every run (the scene_extras.json of this run already sits on the seats); YD3 and YG3 are drawn side by side at the one cables3d seat Y.SD1, while the build puts YG3 about 15 mm past YD3 (HARNESS_BUILD.md) |
| Resistors 100 ohm, 2.2 kOhm | E19, E17 | 3, 2 | 0 | 3, 2 | scene_extras | body size UNVERIFIED |
| Heat shrink on splices, cups, lead joints | C51 | 34 | 27 | 34 | scene_extras (24); 10 placed by make_viewer_data.py step 10f from cables3d.json: splices JFI and JFO, the 2 cell holder lead joints of P1 and P2, and at each eye and the projector the 26 AWG wire to resistor lead and to LED cathode joints | none: BOM_FULL counts one sleeve per joint by the rule in viewer/bom_full.py (15 splices, 13 lead joints, 4 XT30 cups, 2 caps); the 3 D9 lead extension sleeves are gone (D9 reaches without an extension). Positions of the 10 are drawing conventions, written on each node |
| Foam tape pads | K12 | 6 | 0 | 6 | scene_extras (MOUNTING.md faces) | none: all 6 seats on their tape within 0.04 mm (table below) |
| Eye glass discs, projector reflector | E23, E24 | 2, 1 | 0 | 2, 1 | scene_extras (measured seats) | reflector height (test order 10) |
| microSD card, ATO 15 A fuse | E15, E14 | 1, 1 | 0 | 1, 1 | scene_extras | fuse size UNVERIFIED |
| SG90 horns (SG90 bag) | S17 | 2 | 0 | 2 | scene_extras | not in CAD; size UNVERIFIED |
| Kapton wrap on the BMS | K15 | 1 | 0 | 1 | scene_extras | none |
| Retention not decided | none | 3 | 0 | 0 | MOUNTING.md | power splices (tie or tape), speaker (B8), LED beads (no doc) |
| No body in the robot | E25, K11, K13, K14, C48, C52 to C64, tools | | | | | controller off robot; threadlocker, flux and alcohol; kit cable and wire stock drawn as plugs and tubes |

Seat-fit table refreshed 2026-11-02 about 12:05 AM ET from audit/placements.json (seat fixes applied 2026-11-01) and blueprint/coverage.json foam_fit (scene_extras run 04:08 UTC): every taped part now sits on its 1.1 mm VHB 4950 tape within 0.04 mm. blueprint/check_scene_extras.py, run again 2026-11-02 about 5:12 AM ET on the regenerated file: 1 of 177 items embedded (the P3 joint, as before).

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
