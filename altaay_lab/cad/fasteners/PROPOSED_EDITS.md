# Proposed edits

This folder does not own the files below, so none of these edits are applied. Each one uses a screw, an insert, a tool, or a recess that is already in the repo. No new part is specified.

## `twin/assembly/BUILD_ORDER.md`

Step 73, replace the whole line with:

`73. 4 x M2 self-tapping pan head: trunk_top into wj-wk00-0124bottomcase_45, PH0 (F057, F058, F125 are M2x6; F127 is M2x12 through the neck stop block, D59)`

Step 75, replace the whole line with:

`75. 4 x M2 self-tapping pan head: trunk_top into wj-wk00-0124bottomcase_45, PH0 (F059, F060, F131 are M2x6; F129 is M2x12 through the neck stop block, D59)`

Step 80, replace the whole line with:

`80. JOIN 2 x M2.5x6 DIN 912 A2: board into trunk_top, hex2.0 (F119, F122; F120 and F121 out)`

Step 99, replace the whole line with:

`99. JOIN 2 x M2.5x6 DIN 912 A2: raspberrypizerow into head, hex2.0 (F111, F114; F112 and F113 out)`

Step 100, replace the whole line with:

`100. JOIN 2 x M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers: bulb into right_eye, hex2.0 (F176, F181; F177 and F180 out)`

Step 102, replace the whole line with:

`102. JOIN 2 x M2x5 self-tapping pan head: camera PCB into head, PH0 (F344, F347; F345 and F346 out; D34 length is M2x5)`

Step 105, replace the whole line with:

`105. JOIN 2 x M2.5x5 DIN 912 A2: speaker_interface into speaker_stand, hex2.0 (F353, F354; F352 and F355 out)`

Step 106, replace the whole line with:

`106. JOIN 2 x M2.5x6 DIN 912 A2: speaker_stand into head, hex2.0 (F108, F109; F107 and F110 out)`

Insert before step 77:

`76b. JOIN 2 x M2.5x6 DIN 912 A2: tof_cliff into body_front, hex2.0, from the back of the board (F360, F361). Drive these while body_front is in the hand.`

Insert after step 99:

`99b. JOIN 4 x M2x6 self-tapping pan head: mic boards into head, PH0 (F356, F357, F358, F359). Drive these before head_bot_sheet.`

## `twin/dock/nest/cad/nest_parts.py`

The comment on `LID_POSTS` says 6 mm inside the corners. The room-side numbers are `BX0 + 14.0`. The wall-side numbers are already `BX1 - 6.0`. Measured: the pattern centre is 4.0 mm toward the wall of the tray centre, and the mirror error about the tray centre is 8.0 mm (calc).

Replace:

`LID_POSTS = [(BX0 + 14.0, 84.0), (BX0 + 14.0, -84.0), (BX1 - 6.0, 84.0), (BX1 - 6.0, -84.0)]      # 6 mm inside the lid's four corners`

with:

`LID_POSTS = [(BX0 + 6.0, 84.0), (BX0 + 6.0, -84.0), (BX1 - 6.0, 84.0), (BX1 - 6.0, -84.0)]      # 6 mm inside the lid's four corners`

Then regenerate the tray and the lid with the existing `nest_parts.py`. Do not hand-edit the STL. The terminal posts stay at y +25 and -25 mm. A lid post at y 84 mm is 59 mm away from a terminal in y (calc), so this one-number change does not land on a terminal. This audit did not regenerate the mesh.

## Topology and shin STLs

Do not copy these into `print/`:

- `twin/structure/topology/stl/knee_to_ankle_left_sheet.stl`
- `twin/structure/topology/stl/knee_to_ankle_right_sheet.stl`
- `twin/structure/topology/stl/shin_left_sheet.stl`
- `twin/structure/topology/stl/neck_left_sheet.stl`
- `twin/structure/topology/stl/neck_right_sheet.stl`
- `twin/structure/shin_eye/stl/shin_left_sheet_taper.stl`
- `twin/structure/shin_eye/stl/shin_left_sheet_web.stl`

On those files the existing horn-screw heads are inside solid material (cad, `CHECKS.md`). The shank holes are open.

The recess that clears the shin drive screws is already in `twin/structure/shin_eye/eye_geom.py` (`HEAD_D = 5.8`) and in the `*_cbore.stl` files. Measured: F203, F205, F207, and F250 are open on those counterbored meshes (cad). For the knee and neck STLs, the same function is the one to run before anyone copies them. This audit does not add a new recess diameter. The roll-to-pitch pads do not cover a screw head, so they do not need that cut for the screws.

## `print/body_front.stl`

The 6.0 mm chest hole from `twin/dock/chest_hole.py` is open in the current STL (cad). `NEST_CAD.md` section 5 already says to close it when the wall dock's wires are gone. Fill that hole. Do not add a screw there. This audit does not edit the STL.

## Not proposed

- No charger-board mount and no charger screw. `CHARGER_BOARD.md` has no outline and no hole pattern. Picking a hole pattern would be a new design.
- No wall-card screw or clip. `CLOSEUP.md` does not name one.
- No flush-well cut into the nest seat. The flush study is a different layout and it adds no screw.
- No new screw length for the 89 BELOW RULE rows. `FASTENERS.md` already says the bore is too shallow for a longer stock screw.
- No torque value. The cited table does not apply (`SCHEDULE.md`).
- No catalog ring lug. `NEST_CAD.md` names an M3 ring lug and the BOM has no line for it. This audit does not choose one.
- No nest rows added to `fasteners.json` until that nest is the installed model. Until then, `schedule.json` in this folder is the record.
