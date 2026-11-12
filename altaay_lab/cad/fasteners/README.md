# Fastener audit

This folder measures the screws, inserts, nuts, and washers already drawn for the duck and the nest. It does not add a screw, a hole, or a mount. Nothing here is copied into `print/`.

What it reuses:

- `fasteners/fasteners.json` and `fasteners/FASTENERS.md` (every robot screw already scheduled)
- `twin/assembly/BUILD_ORDER.md` and `twin/assembly/asm_geom_summary.json` (the existing build order and its tool cast)
- `twin/holes/data/sym_checks.json` and `twin/holes/HOLES_TWIN.md` (D39 and D42 on the installed set)
- `twin/dock/nest/cad/nest_parts.py` (the nest screws already chosen there)
- `twin/structure/topology/stl/` and `twin/structure/shin_eye/stl/` (the pads already drawn)
- `twin/structure/shin_eye/eye_geom.py` (the head recess already drawn for the shin)
- `docs/assembly_guide.md` and BOM 19 (Loctite 243 on metal into the motor metal)
- RLS installation guide TTD01_03, issue 03, 6 Dec 2023 (the torque table, and the depth line that keeps it from applying here)

Files:

| File | What it is |
|---|---|
| `schedule.json` | Every robot screw, and the nest joints. One row per screw. |
| `SCHEDULE.md` | How to read that file. Torque, threadlocker, washers. |
| `CHECKS.md` | D39, D42, the later CAD, wires, tools. |
| `ASSEMBLY.md` | The existing build order, the lines that are wrong, the nest steps. |
| `PROPOSED_EDITS.md` | Exact edits for files this folder does not own. Not applied. |
| `audit.py` | The measurements. Run it again to refresh the JSON. |
| `nest_lid_screws.png` | The nest lid as drawn. Calc only. |
| `installed_screw_checks.png` | Counts from `fasteners.json` and `BUILD_ORDER.md`. CAD check only. |
| `findings.json` | The same measurements, including the head-recess rows. |

Labels: **cad** is a measurement on a mesh or on `fasteners.json`. **calc** is arithmetic on those numbers. **cited** is a page. A sim is not in this folder. None of these numbers are a hardware test.

## Problems found

1. `BUILD_ORDER.md` still says M2x6 for F127 and F129. `fasteners.json` says M2x12 (cad). D59 already lengthened them for the neck stop.
2. `BUILD_ORDER.md` still says M2x4 for the camera. The fitted screws F344 and F347 are M2x5 (cad, D34).
3. `BUILD_ORDER.md` still drives screws that are left out: adapter F120 and F121, Pi F112 and F113, right eye F177 and F180, camera F345 and F346, speaker interface F352 and F355, speaker stand F107 and F110 (cad).
4. Six fitted screws are not in that order: mic F356 to F359, cliff F360 and F361 (cad).
5. Nest lid screws sit 4.0 mm off the tray centre. Mirror error about that centre is 8.0 mm (calc). D42 asks for the part centre. The file's own comment says 6 mm; the code says 14 mm on the room side.
6. Nest lid M3x6 engages 4.0 mm. The insert rule already used on the robot is 4.5 mm. M3x8 bottoms in the 5.8 mm bore (calc). No stock length meets the rule. The nest file already chose M3x6.
7. The chest hole is open in `print/body_front.stl` (cad). Its wires go away with the wall dock (`NEST_CAD.md`).
8. Topology knee, shin, and neck pads, and the shin taper and web without a recess, put solid material where the existing screw heads sit (cad). The stock `print/` STLs are open on the control screws. The shin counterbore STLs are open again. Roll-to-pitch pads miss the screw heads.
9. At the zero pose, F255 overlaps cable S10 by 0.59 mm and F249 overlaps cable D3 by 0.09 mm, on the head-cylinder model (cad). Not a sweep.
10. The 24 head-recess clashes and the 89 short engagements are already in `FASTENERS.md`. Still true. No new length is proposed.

## Open items

Each line is a BLOCKER. This audit does not close it.

- Charger board: no outline, no holes, no seat (`CHARGER_BOARD.md`). No mount is proposed here.
- Nest ring lug: named in `NEST_CAD.md`, no BOM line, no catalog part chosen here.
- Jack wrench: the nut comes with PJ-005A. The wrench size is not in the repo.
- Terminal engagement: the lug thickness is not in the CAD, so NT1 and NT2 have no engagement number.
- Copying a no-recess topology or shin STL into `print/` would bury the existing horn screws (cad). Do not copy them.
- Chest hole stays open until the STL owner fills the cut `chest_hole.py` already defines.
- Wall card: `CLOSEUP.md` names no fastener. None is added here.
- Flush wells and nest pin pockets are two layouts. Neither is in `print/`. Do not cut both.
- Build torque: the cited TTD01_03 table does not meet its own depth line on these joints. No torque is set.
- Pull-out of inserts and of self-tappers, bag screw sizes, and the camera board thickness stay the open items already in `FASTENERS.md` and the screws twin. Not re-tested here.
- Hot and wet PA6-CF stay the open item already in the shin study. Not re-tested here.

![Nest lid screws as drawn](nest_lid_screws.png)

![Installed screw checks](installed_screw_checks.png)
