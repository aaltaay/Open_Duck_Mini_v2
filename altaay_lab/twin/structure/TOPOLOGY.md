# Structure margin and topology pass (sim pass only, FEA pass only)

Written 2026-11-12 12:22 AM ET. This extends twin/structure/STRUCTURE_TWIN.md. It does not replace that file's 2026-11-03 numbers, and it does not install anything into print/.

Labels: sim pass only means a MuJoCo load. FEA pass only means the linear tetrahedron solver in st_fea.py. CAD check only means a mesh clearance or a hole ray. Calc only means a scale applied to an FEA number. BLOCKER means the number is not known. Hot PLA strength and the fall contact stiffness are guesses, as in the 2026-11-03 twin.

## What changed in the check

TetGen 0.8.4 stops in recoversubfaces on the current print STLs (edges shorter than 0.05 mm). The element, the assembler, the pyamg solver, the 1 mm stress average, and the failure index are the ones in st_fea.py. The tets are a grid (ST_VOXEL_MM) of points inside the STL, with screw holes and the 7 mm horn hub left open. Pitch: roll 0.9 mm, shin and thigh and neck 0.75 to 0.8 mm, head 1.0 mm, foot and hip 1.1 to 1.3 mm.

Loads are a new run of st_loads.py and st_falls.py (30 Newton iterations, the same cases). The instrumented build_budget sum in this session was 2.808 kg (sim pass only, not weighed). The 2026-11-03 study was 2.653 kg, so these safety factors are not a replay of that table. Soft falls are the 11 files with time constant 0.0158 s and damping ratio 0.2. There were 10 in the older table.

## Margins before this pass

FEA pass only, on those new loads, room-temperature PLA, current print STLs (roll_to_pitch is already 3 walls, D38). Walking margin 2. Soft-fall margin 1.2.

| Part | Walk SF | Soft-fall worst SF | Soft falls under 1.2 |
|---|---|---|---|
| roll_to_pitch | 1.43 | 0.54 | 7 of 11 |
| shin_left_sheet (knee drive eye) | 0.79 | 0.46 | 7 of 11 |
| thigh sheets | 1.78 | 0.70 | 3 of 11 |
| neck sheets | 5.20 | 0.38 | 11 of 11 |
| head_roll_mount | 52.49 | 1.03 | 2 of 11 |
| foot_top | 3.86 | 2.76 | 0 of 11 |
| hip roll stage | 16.74 | 2.33 | 0 of 11 |

The 2026-11-03 tetgen study, for comparison only (2 walls on roll, 2.653 kg): roll walk 1.48 to 1.63 and soft falls 7 to 8 of 10 under 1.2 (worst 0.42 to 0.48); knee sheet eye walk 1.63. This voxel run on the current shin is lower than that 1.63 (the shin is now shin_left_sheet, D59, and the mass is higher).

## Geometry that was checked

Scripts: topology/margin_geom.py. STLs: topology/stl/. Clearance is CAD check only, at least 1.5 mm to the servo and, for roll_to_pitch, to the thigh sheets over the hip pitch range. Horn screw axes were ray-checked after the union: the holes stay open (D39). No screw was added (D42 unchanged).

A rib along link y on roll_to_pitch was tried and dropped. That part prints with layers along link y, and the rib root failed in interlayer tension (walk SF fell from 1.43 to 1.25). The kept change thickens the 5 mm ear wall in x only, about 2.6 mm outboard and about 4 mm inboard. Clearance to the hip pitch servo: 2.02 mm left, 1.93 mm right.

The knee drive plates (knee_to_ankle_left_sheet, knee_to_ankle_right_sheet, shin_left_sheet) get a stack of 2.2 mm slides, 6.6 mm proud of the head face, inside a 32 mm radius of the drive eye. One slide longer than the 3.3 mm plate left a gap and did not help (shin walk stayed 0.81). The stack is one solid, 9.9 to 10.5 mm thick at the old weak spot, and the hub and the four screw holes stay open. Clearance to the servo: 13.9 to 19.2 mm.

A pad on the idle sheet's far end (the thigh's real weak spot, y about -37 mm) came within 1.46 mm of the knee servo. It was not kept.

Neck sheets grow 8 mm on the face that points away from the head pitch servo. Thickness at the weak spot goes from 3.45 mm to 11.5 mm. Clearance: 3.45 mm left, 2.14 mm right.

A 2.5 mm slab on head_roll_mount cleared the servo by 3.3 mm. The re-FEA soft-fall worst went from 1.03 to 0.97, so that slab is not in topology/stl/.

## Margins after the kept geometry

FEA pass only, same loads, same voxel pitches, room-temperature PLA.

| Part | Walk SF before | Walk SF after | Soft worst before | Soft worst after | Soft falls under 1.2 after |
|---|---|---|---|---|---|
| roll_to_pitch | 1.43 | 2.23 | 0.54 | 0.78 | 3 of 11 |
| shin drive eye | 0.79 | 1.30 | 0.46 | 0.87 | 3 of 11 |
| thigh sheets | 1.78 | 1.71 | 0.70 | 0.94 | 2 of 11 |
| neck sheets | 5.20 | 11.85 | 0.38 | 0.99 | 6 of 11 |
| head_roll_mount | 52.49 | 52.49 (no STL change) | 1.03 | 1.03 | 2 of 11 |
| foot_top | 3.86 | 3.86 | 2.76 | 2.76 | 0 of 11 |
| hip roll stage | 16.74 | 16.74 | 2.33 | 2.33 | 0 of 11 |

Walking margin of 2: met on roll_to_pitch (2.23), the neck (11.85), the head (52), the foot (3.86), and the hip roll stage (16.74). Not met on the shin eye (1.30) or the thigh sheets (1.71). The thigh number barely moved because the peak is the far end of the idle sheet, and that pad did not clear the knee servo.

Soft-fall margin of 1.2: met on the foot and the hip roll stage. Not met on roll_to_pitch (worst 0.78, 3 of 11), the shin (0.87, 3 of 11), the thigh (0.94, 2 of 11), the neck (0.99, 6 of 11), or the head (1.03, 2 of 11). The neck and the roll wall are close to the servo already (2.0 to 2.1 mm). Another 2 mm of thickness does not fit. On the ear wall the stress scaled about as 1/thickness, not 1/thickness squared, so the inboard pad barely moved the outer-fiber peak (soft worst 0.75 with the outboard pad only, 0.78 with both faces).

Mid and hard contact levels still put these parts under 1.2. That stiffness is a guess. The 1.2 check above is the soft level only.

Hot PLA is not a new FEA. These safety factors are room temperature. The 2026-11-03 twin cited a 0.62 strength factor at 50 C (a guess). Calc only: roll walking 2.23 times 0.62 is 1.38, under 2. Hot strength above that guess remains a BLOCKER, as in that file.

## Print cost of the kept STLs

PrusaSlicer 2.7.2 through print/slice.py (st_slice_proposals.py proposed). Model grams, not weighed. Quantity is parts.csv.

| STL | Qty | Base g | Proposed g | Robot delta g | Robot delta h |
|---|---|---|---|---|---|
| left_roll_to_pitch.stl | 1 | 24.24 | 26.04 | +1.80 | +0.29 |
| right_roll_to_pitch.stl | 1 | 24.23 | 29.18 | +4.95 | +0.59 |
| knee_to_ankle_left_sheet.stl | 2 | 6.50 | 10.57 | +8.14 | +1.05 |
| knee_to_ankle_right_sheet.stl | 2 | 5.87 | 9.93 | +8.12 | +1.03 |
| shin_left_sheet.stl | 2 | 10.38 | 14.12 | +7.48 | +1.02 |
| neck_left_sheet.stl | 1 | 7.30 | 15.75 | +8.45 | +0.88 |
| neck_right_sheet.stl | 1 | 6.48 | 15.31 | +8.83 | +0.90 |
| Sum | | | | +47.77 | +5.76 |

The pads add mass. They are loaded material. This is not a saving.

## Topology pass

carve.py takes the same unit-load field and drops interior tets whose upper-bound von Mises, from the peak of each load component on the walk and the soft falls, is under 3.8 MPa (8 percent of 47.1 MPa), and which sit more than 2.4 mm inside the surface. On foot_top the solid volume went from 37847 to 30130 mm3 (CAD check only).

Re-FEA of that STL (FEA pass only, pitch 1.1 mm): walk SF 7.50, soft-fall worst 5.80, 0 of 11 under 1.2. The margin holds.

PrusaSlicer on the carved STL: 21.87 g and 1.98 h become 33.00 g and 4.11 h per part. Times 2 is +22.26 g and +4.27 h. The slicer prints a wall around each pocket. The 15 percent gyroid was already the unloaded interior, so cutting it out of the STL adds walls instead of removing print time. The carved foot is not a proposed swap. topology/stl_topo/foot_top.stl is the check, not an install.

No grams and no hours were saved. The margin geometry adds 47.77 g and 5.76 h. The topology cut on the foot adds a further 22.26 g and 4.27 h if it were printed, so it is left out.

## Proposed swaps, not installed

Copy later, over print/, only if a later job accepts the margins above. Do not copy topology/stl_topo/foot_top.stl.

- topology/stl/left_roll_to_pitch.stl
- topology/stl/right_roll_to_pitch.stl
- topology/stl/knee_to_ankle_left_sheet.stl
- topology/stl/knee_to_ankle_right_sheet.stl
- topology/stl/shin_left_sheet.stl
- topology/stl/neck_left_sheet.stl
- topology/stl/neck_right_sheet.stl

Images of the added material (red) are in topology/img/final_*.png.
