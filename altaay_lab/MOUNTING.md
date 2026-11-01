# MOUNTING

Last updated: 2026-11-01 2:35 PM ET. Measured on the upstream assembly (URDF meshes + print STLs, STL commit 730c14b) with trimesh: for each modelled board, rays were cast down each hole to find the printed part under it, the pilot diameter, and where the pilot starts and ends below the board top face ("engagement window"). Scripts: audit/screws2.py, audit/sites.py; data: audit/screws2.json, audit/screws_head.json.

Screw rule: choose the length so the thread end stays inside the pilot (length less than the window far end) and engages at least 3 mm (length minus window near end). All electronics pilots are 2.0 mm printed holes, which an M2.5 machine screw self-taps into (no insert, no nut, no washer; no nut traps or washer seats exist in the STLs).

| Component | Printed part it mounts to | Holes (CAD) | Pilot | Engagement window below board top (mm) | Screw | Engagement | Orientation | Status |
|---|---|---|---|---|---|---|---|---|
| Raspberry Pi Zero 2 W | head.stl | 4, clearance 2.6 in CAD; real board 2.75 on 58 x 23 mm (Raspberry Pi product brief RP-008359-DS-1) | 2.0 plastic | 1.4 to 6.4 | M2.5x6 DIN 912 A2, 4 pcs | 4.6 | flat, components side up, in head | verified CAD; real 65 x 30 vs CAD 65.9 x 31.25 OK |
| Waveshare Bus Servo Adapter (A) | trunk_top.stl, on 4 bosses 5 mm high (standoffs printed in) | 4 at 2.5, board 42.02 x 33.02 x 1.6 (Waveshare wiki 42 x 33, 2.5 holes) | 2.0 plastic | 1.6 to 6.6 | M2.5x6, 4 pcs | 4.4 | flat, USB-C toward the neck opening | verified |
| Second board.stl copy | head.stl | 4 at 2.5 | 2.0 plastic | 1.6 to 6.6 | M2.5x6, 4 pcs if used | 4.4 | flat | BLOCKER: upstream BOM has one adapter; identity of the head copy unknown. Needed: upstream Onshape BOM export or assembly guide photo |
| BNO055 (Adafruit 2472) | trunk_top.stl | 4 at 2.5; CAD board 20 x 27 x 3.0 | 2.0 plastic | 3.0 to 8.0 with the 3.0 CAD board; 1.6 to 6.6 with the real 1.6 PCB | M2.5x6, 4 pcs (M2.5x8 would reach 8.0 and bottom out with a 1.6 PCB) | 4.4 | flat, chip up; board x (20 mm edge) along robot +X (forward), 27 mm edge along +Y (left), z up. Centre at (-87.1, 0, 43.3) mm in the trunk frame | BLOCKER-lite: hole spacing. Adafruit 2472 page says holes 20 x 12 mm apart; Adafruit Eagle file 21.59 x 15.24; CAD 21.9 x 14.9. Needed: calipers on the real board before printing trunk_top, or test print |
| USB-C 2S charger | body_back.stl | 2 at 2.5 (14.4 pitch); only 1 has a pilot under it | 2.0 plastic | 2.1 to 6.9 | M2.5x6, 1 pc | 3.9 | USB-C facing out of the body_back opening | 2nd hole has no pilot (ray hits holder.stl at 5.2 mm); 1 screw plus the USB-C cutout hold it |
| Power switch | body_back.stl cutout | 2 at 1.8 aimed at no printed part | none | none | none: snap-in rocker held by the cutout | n/a | rocker face outward through body_back | verified contact 0.00 mm; BLOCKER: the 15 A rated replacement must fit the 23.4 x 7.4 x 16.8 mm body |
| 2S BMS (40.6 x 15.85 x 3.6 CAD) | between body_back and battery_pack_lid | none | none | n/a | none: sandwiched | n/a | flat on the battery bay | FLAG: CAD overlaps body_back 0.80 mm and lid 0.63 mm. Real AITRIP board size not verified. Needed: measure the board; if thicker than about 2.2 mm the lid will not close |
| 2x18650 holder (76 x 41 x 20 CAD) | body_back battery bay, closed by battery_pack_lid | none | none | n/a | none: captive | n/a | cells along Y | verified: 0.14 mm overlap with body_back (press), 0.62 mm gap to lid |
| battery_pack_lid | body_back.stl | 4 clearance 2.5 in a 4.0 head recess | 2.0 plastic | 2.1 to 15.3 (2 holes) and 2.1 to 20.1 (2 holes) | M2.5x10 DIN 912, 4 pcs | 7.9 | n/a | BLOCKER: no standard M2.5 head fits a 4.0 recess (DIN 912 head 4.5, ISO 7380 4.7, ISO 14583 pan 4.5). Fix: open the recess to 4.8 mm in a STL edit, or accept the head sitting proud |
| Speaker | speaker_stand.stl and speaker_interface.stl, stand screwed to head.stl | stand: 4 clearance 2.7 | 2.0 plastic in head | 3.0 to 8.0 | M2.5x6, 4 pcs (stand to head) | 3.0 | facing forward | BLOCKER: how the speaker itself is held in speaker_interface (press or glue) and the speaker size are not in the CAD |
| Eyes (left_eye, right_eye, bulb x2) | head.stl: screw passes bulb (2.0 mm, clearance 2.7) then head wall (3.0 mm, clearance 2.7) into the eye | 4 per side (8 total), at y = +/-27.5 and +/-52.5, z = 126.9 and 151.9 mm | right_eye 2.05, left_eye 2.2 | 5.0 to 8.0 below the bulb face (pilot 3.0 mm long, open at the far end) | M2.5x8 DIN 912 A2, 8 pcs | 3.0, tip ends flush with the eye front face | facing forward | BLOCKER: left pilot 2.2 vs right 2.05 (a 2.2 pilot leaves about 0.15 mm thread depth per side for M2.5). Needed: test print of left_eye; if loose, use 2.05 or an M2.5 thread-forming screw. LED seat not modelled |
| Projector LED | flash_light_module.stl + flash_reflector_interface.stl | none found | none | n/a | none found | n/a | forward | BLOCKER: retention method not in CAD |
| Antenna servos (SG90 x2, 32.6 x 13 x 30.97 CAD) | head.stl antenna pockets; antenna holders on the horns | holders: 2 clearance 2.7 in 5.05 recess, no anchor | none | n/a | not determinable | n/a | output shaft up | BLOCKER: holder pilot spacing 39.2 mm does not match SG90 tab spacing; SG90 tab screws and horn screw not specified. Needed: upstream photo or Onshape mate |
| Castle CC BEC Pro | not in CAD | | | | | | | BLOCKER: no feature. Needed: choose a place (for example double-sided foam on trunk_top) and check clearance with the BEC's published size |
| HENGE UBEC 5 V | not in CAD | | | | | | | BLOCKER: as BEC |
| Fuse holder FHAC0001ZXJ | not in CAD | | | | | | | BLOCKER: inline on P7, needs space in body_back |
| XT30 pair | not in CAD | | | | | | | BLOCKER: inline between BMS and fuse |
| MAX98357A amp | not in CAD | | | | | | | BLOCKER |
| Foot switches SS-10 | not in CAD (foot_top, foot_side, foot_bottom have no SS-10 seat found) | | | | | | | BLOCKER: needed: upstream foot assembly detail |
| Camera | not in CAD | | | | | | | BLOCKER: not integrated upstream |

## IMU axes (BNO055)
- Board lies flat in trunk_top; local x to robot +X (forward, toward the eyes), local y to +Y, local z to +Z (up). URDF +X is forward; the battery sits at x about -126 mm (back).
- Runtime imu.py (Open_Duck_Mini_Runtime 376de65, lines 19 to 55) sets axis_remap (Y, X, Z) with signs (-, +, +) and imu_upside_down false. Verify on hardware with scripts/calibrate_imu.py and a tilt test (pitch nose down should read the sign the policy expects). Sign is a BLOCKER-lite until tested.

## Screw count from this file
M2.5x6: Pi 4 + adapter 4 + head board 4 + BNO055 4 + charger 1 + speaker stand 4 = 21 (BOM buys 25).
M2.5x8: eyes 8 (BOM buys 10). M2.5x10: lid 4 (BOM buys 5).
