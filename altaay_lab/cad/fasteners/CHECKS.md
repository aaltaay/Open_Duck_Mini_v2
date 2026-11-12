# Hole, interference, and tool checks

Labels: cad is a measurement, calc is arithmetic, cited is a page or a file this audit did not re-run.

## D39 and D42 on the installed set

D39: a printed hole with no job is closed. D42: the screws left on a part are mirror-symmetric about the part centre, or a diagonal pair through the centre.

`twin/holes/data/sym_checks.json` (cited) lists 7 part groups that are not one pattern: both `foot_side`, both `roll_to_pitch`, `trunk_top`, and both `roll_motor_bottom`. `HOLES_TWIN.md` (cited) says the first five carry more than one joint and each joint is uniform, and each `roll_motor_bottom` keeps only the inner screw (D18). This audit measured that inner pair at y 24.749 mm and y -24.751 mm (cad). They mirror across the robot centre.

A shin sheet fails as one cloud of 8 screws (max miss 11.03 mm, cad) and passes once split by anchor: the insert pair, the case-pilot pair, and the 4 horn screws each mirror at 0.0 mm (cad). That is the same "one joint at a time" reading the holes twin already uses. It is not a new D42 failure.

Empty stacks already classified in `fasteners.json` (cad, counted again): 127 grille holes, 82 PCB holes, closed D39 caps, 3 bearing seats, 18 servo pilots with nothing on them (the holes twin leaves bought servo faces alone), 4 holes of the head `board.stl` copy with no pilots, 2 panel-switch holes (the switch is held by the cutout, as that note says), 1 charger hole with no pilot, and 1 stack still marked UNUSED. The charger hole and the UNUSED stack are printed holes whose note does not name a screw. They were already in that file. This audit does not close them.

The chest lead hole is a separate check. On `print/body_front.stl`, the wall point from `twin/dock/chest_hole.py` (mid-wall, y 0, z 38 in the world) is not solid, and a point 8 mm to the side in the same wall is solid (cad). The hole is open. `NEST_CAD.md` section 5 already says that hole loses its wires when the wall dock goes, so D39 would close it. This audit does not edit the STL.

## Later CAD

### Topology pads (the pass called PR 43)

STLs in `twin/structure/topology/stl/`. Not in `print/`. No new screw, which matches `TOPOLOGY.md`.

Shank holes stay open: 0 of 8 samples solid on the screws checked (cad).

Head side, at the DIN 912 M3 knurl radius (2.84 mm), the stock `print/` STL is open on the control screws F203, F197, F228, and F187 (cad). The proposed pads are not:

| STL | What is solid on the head side of the old seat | Label |
|---|---|---|
| `knee_to_ankle_left_sheet` and the right-hand twin | F197, F199, F201 solid from 0.3 mm to 6.3 mm. F248 solid from 1.1 mm to 1.9 mm. Case screws F099 and F100 stay open. | cad |
| `shin_left_sheet` | F203, F205, F207 solid from 0.3 mm to 6.3 mm. F250 solid from 1.1 mm to 1.9 mm. | cad |
| `neck_left_sheet` and `neck_right_sheet` | Horn screws and the case screws F148, F149, F055, F056 solid from 0.3 mm to 7.9 mm. F259 is a short band at 1.9 mm. | cad |
| `left_roll_to_pitch` and `right_roll_to_pitch` | No screw in the head test is solid. The ear pads miss the screw heads. | cad |

An M3 head is up to 3.0 mm tall (cited, the DIN 912 k max already in `fasteners.json`). Material from 0.3 mm to 6.3 mm sits in that head. The existing M3x6 cannot land on the old seat. The shank hole is open, so a longer screw could pass, but this audit does not add a length. The existing recess is the one already drawn for the shin. See below.

### Shin eye, PA6-CF (the pass called PR 46)

`twin/structure/shin_eye/stl/`. Not in `print/`.

`shin_left_sheet_taper.stl` and `shin_left_sheet_web.stl` match the topology shin: drive heads buried, shank open (cad).

`shin_left_sheet_web_cbore.stl`, `shin_left_sheet_taper_cbore.stl`, and `shin_left_sheet_collar_cbore.stl` leave F203, F205, F207, and F250 open on the head side (cad). That recess is the one `eye_geom.py` already cuts at 5.8 mm so the existing M3x6 still fits. Use those files, not the ones without the recess. Do not copy any of them into `print/` while the shin study's hot and wet PA6-CF note is still open. This audit does not change that note.

### Belly flush wells (the pass called PR 41)

`twin/dock/flush/FLUSH_CONTACTS.md` draws five wells and no screw. It says it does not copy the nest CAD. The nest CAD puts pin pockets in the same seat and bumper. Cutting both into one part is two layouts. This audit does not draw a third. The installed `print/` set has neither cut. D39: a well that is a contact has a job, but only after one layout is the one that gets printed. D42: five wells on a line through the centre, as that study writes them, are a mirror pair plus the centre well. That is a note on the study, not a screw group.

### Charger board (the pass called PR 40)

`circuitry/CHARGER_BOARD.md` says the board outline, the layer count, and the seat are not in that pass. There is no hole pattern and no screw. This audit does not design a seat or a screw for it. The existing blocker in that file and in `NEST_CAD.md` (no seat) still stands.

### Wall card (the pass called PR 47)

`twin/dock/closeup/CLOSEUP.md` is a 40 mm square, felt or printed, no electronics, centre 350 mm off the floor. It names no screw, no insert, and no nut. This audit does not add one. The duck screws do not move. The rim in the nest CAD is 30 mm high (cited, `nestcad_lib.py`), so the card sits well above the rim (calc: the card's bottom is 330 mm up, the rim top is 30 mm). How the card stays on the wall is not specified. That is an open item, not a new clip.

### Nest

See `SCHEDULE.md` for the six screws and the jack nut. Duck fasteners: the nearest trunk screw in the nest's own check is F027 at 12.7 mm (cited, `NEST_CAD.md` check A, not re-run). No new duck screw.

Lid pattern: calc, in `SCHEDULE.md`. Terminals pass D42. The jack hole has a job (the jack). Feedthroughs, wells, slots, and slits are the jobs `NEST_CAD.md` check H already names. This audit did not find an empty nest hole beyond that list.

## Wires (cad, zero pose only)

The first pass used cable vertices and subtracted the head radius from the distance to the axis end. That is a spherical cap, and it missed the middle of a segment. Codex review on PR 53. This pass samples each run every 0.25 mm and measures a finite head cylinder and a finite shank cylinder, with flat ends. The link transforms still match `seat_world` within 0.001 mm. Not a joint sweep. No screw-to-wire limit is set here, and no wire is moved.

| Screw | Cable | Gap | What the cable is |
|---|---|---|---|
| F118 | D19 | -1.58 mm | BNO055 to the body touch board |
| F115 | DC4 | -1.55 mm | chest SYS lead, the wall dock |
| F054 | DC2 | -0.96 mm | chest GND lead, the wall dock |
| F027 | P1 | -0.90 mm | holder plus to the BMS |
| F255 | S10 | -0.22 mm | kit cable ID 13 to ID 14 |
| F052 | DC3 | -0.07 mm | chest SENSE lead, the wall dock |
| F249 | D3 | +0.13 mm | Pi to the left foot switches. Clears. The old -0.09 mm was the cap, not the cylinder. |

DC2, DC3 and DC4 are the chest-dock leads `NEST_CAD.md` already removes. F027, F118 and F255 are on the duck harness. Dressing them is for the cable file. Not done here.

## Nest lid proposal (not applied)

`lid_check.py` reads the existing `box_profile`. BX0+6 has 0.0 mm of lid (cad). The room-side axes stay at x 158, where the lid is 2.0 mm thick and the button head has 3.15 mm of flat top inboard of the chamfer. The wall-side axes move to x 174.9, the mirror about the tray centre (mirror error 0.0 mm, calc). y moves from 84 to 62 so a 4 mm radius post clears the jack stand-in already in `nest_parts.py` by about 2 mm (cad). The drawn post at (158, 84) enters that stand-in by 3.0 mm. Nearest terminal after the move is 37.22 mm (calc).

A longer insert does not raise engagement: the M3x6 only reaches 4.0 mm, and the insert is already 5.7 mm (calc). A deeper bore with the same M3x6 is still 4.0 mm. M3x8 (BOM 17a, already on the bill) into a bore deepened from 5.8 mm to 6.3 mm engages 5.7 mm and stays 0.3 mm off the floor (calc). The socket head is 1.35 mm taller than the button. The published 2.85 mm over the button heads would leave 1.50 mm (calc, that 2.85 mm was not re-measured). Detail is `PROPOSED_EDITS.md`. The nest STL is not regenerated.

## Tool access

`twin/assembly/asm_geom_summary.json` (cited, not re-run): 286 driven screws, 0 tool-path violations, 115 clear even with every part present. The 56 factory case screws are not in `BUILD_ORDER.md` because they are already in the servos. That is correct.

`BUILD_ORDER.md` now matches `fasteners.json` on F127, F129 (M2x12), F344 and F347 (M2x5). The 12 left-out screws are no longer in a drive count. F356 to F359 and F360, F361 are in the order, on PH0 and hex 2.0. A re-run of `audit.py` finds no missing fitted screw and no length mismatch (cad). Those six were not in the 286-screw cast.

Nest tools: hex 2.0 and hex 2.5, both already in BOM T4. Drive the terminal screws before the lid, and the lid screws before the felt sleeve (`NEST_CAD.md` already has the sleeve over the screw heads). The jack nut is reached from the end wall before the left bolster covers it. The wrench size is not in the repo.
