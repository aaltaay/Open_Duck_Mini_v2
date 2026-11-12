# DFA: fastener count

2026-11-12. This pass counts the CAD schedule and checks each joint against patterns already in the lab or on a page opened for this note. It does not draw a new latch, clip, hinge, or twist-lock. It does not edit print/, the fastener schedule, or the structure meshes.

altaay_lab/cad/fasteners/ is not in the tree. The count is altaay_lab/fasteners/fasteners.json (361 screw rows, 58 insert rows). The screws twin, D39, and D42 already removed what their checks allowed. This note builds on that. It does not repeat their cuts as if they were still available.

Labels: CAD check only is a count or a fit read from that schedule or from parts.csv. Cited is a page or a lab file named in the sentence. Calc only is arithmetic on those. FEA pass only is a safety factor from PR 43 or PR 46, not a new solve. BLOCKER means the number was not measured here.

## Before and after

| Item | Before | After | Label |
|---|---|---|---|
| Screws fitted | 324 | 324 | CAD check only |
| Screws left out on purpose | 37 | 37 | CAD check only |
| Screw rows in the schedule | 361 | 361 | CAD check only |
| Inserts fitted | 48 | 48 | CAD check only |
| Inserts left out | 10 | 10 | CAD check only |
| Nuts | 0 | 0 | CAD check only (no nut rows). FASTENERS.md cites a feat3d run with 0 hex pockets (cited, not re-run) |
| Washers on the eye screws | 8 | 8 | CAD check only (4 screws, 2 washers each in the spec string) |
| Printed parts | 68 | 68 | CAD check only (parts.csv qty sum, 49 STL files) |
| Print filament, slicer estimate | 1361.4 g | 1361.4 g | calc only: SLICE_SUMMARY.md part-row total 1355.5 g plus the freeze prose +5.88 g in that same file. Not weighed |
| Print time, slicer estimate | 120.6 h | 120.6 h | calc only: 119.9 h plus the freeze prose +0.74 h. Not a timed print |
| Fastener and STL change | 0 | 0 | CAD check only. Mass change from this pass is 0 |
| Weighed robot mass | BLOCKER | BLOCKER | not weighed |
| Builder screws to turn | 268 | 268 | CAD check only (324 fitted minus 56 factory) |
| Fastening minutes | BLOCKER | BLOCKER | operation count is unchanged, so the time does not change, but the seconds per screw were not re-measured |
| Full assembly minutes | BLOCKER | BLOCKER | insert time, handling, routing, and tests are BLOCKER in the screws twin |

The 324 fitted screws split the same way FASTENERS.md section 1 does: 205 to buy, 57 from the servo bag, 56 factory, 6 from the ear-servo bag (CAD check only). 205 + 57 + 56 + 6 = 324. Twelve of the 205 still carry a supply string of NEW LINE or NEW LENGTH in the JSON (the 10 button heads and the 2 M2x12 screws). Section 2 of that file counts them on BOM 17j and 17m. The fitted total does not change.

By job (CAD check only), same before and after:

| Job | Screws |
|---|---|
| Factory, inside the servo | 56 |
| Horns and shaft screws | 117 |
| Servo case clamps | 68 |
| Printed structure and frame | 40 |
| Covers, boards, eyes | 37 |
| Ear servos | 6 |
| Sum | 324 |

Figure: dfa_before_after.png.

## What was checked, and not used

Each idea below is a published pattern or a pattern already drawn in this repo. None of them removes a screw that is still fitted.

Snap fit. The Fictiv cantilever note (opened for this file, https://www.fictiv.com/articles/how-to-design-snap-fit-components) gives strain = 1.5 t Y / (L squared Q), with Q = 1 for a simple case. That is the formula already used for coupon K3 (twin/screws/data/lips.json): arms 0.9 mm by 12 mm, 0.4 mm barb, strain 0.375 percent, service limit 0.535 percent. K3 snaps a 6 mm cable bundle. It is not a cover retainer. Its coupon has not been run (twin/screws/SCREWS_TWIN.md). The same page says a snap should not stay bent in service (creep) and that repeated use needs an S-N curve, which this lab does not have. A new cover snap is not drawn.

Captive nuts. STRUCTURE_TWIN.md already cites the CNC Kitchen comparison of screws, heat-set inserts, and embedded nuts. A nut would replace an insert. The screw stays. Nuts would rise from 0. That is not a smaller fastener count. Nothing is added to the buy list.

Twist-lock. The schedule has no twist-lock row (CAD check only). The lab files do not contain a twist-lock pattern to copy. One is not drawn.

Fewer, larger screws. Horn screws are M3 into the four holes of the servo horn (FASTENERS.md, 2.4 mm of thread, which meets that joint's rule). A larger screw does not fit those holes. The lid and the head plate stay on the uniform set from D42. Not used.

Merged parts. The speaker sits in a cage made by speaker_stand and speaker_interface (twin/assembly/ASSEMBLY_TWIN.md). Joining those two STLs would close the cage. The leg sheets, the foot plates, and the hip-roll motor shells have to open to take a servo. They are not merged.

Horn screws, one size. Each horn keeps four screws. The length and the head are set by the stack, not by a free choice. Counts here are CAD check only.

| Spec | On horns or the D19 sites | All fitted of this spec | Why it stays |
|---|---|---|---|
| M3x6 DIN 912 | 64 | 78 | Leg, hip-roll, and shin horns. Head height 3.0 mm (ISO 4762, cited in sim/mass_budget.py). The other fitted M3x6 screws are structure, frame, and case-adjacent joints, not a second horn size. |
| M3x5 DIN 912 | 28 | 28 | Neck and head-pitch horns. FASTENERS.md: the short stack engages 2.4 mm, which is the rule, and a longer screw bottoms. |
| M3x6 ISO 7380 button | 10 | 10 | D19, all 10 sites (idle horns and the two spacer screws F002 and F010). A DIN 912 head hits the hip part. Button head height 1.65 mm max, socket 2 mm nominal (ISO 7380-1 table 1, https://westfieldfasteners.co.uk/Standards/ScrewBolt-SHBtn-M.html, opened for this file). |

Those three cannot collapse to one screw without a new horn or a collision. Not changed. PR 46 keeps the four M3x6 drive screws on the shin.

Printed clips. Same as the snap row. The only clip geometry in the repo is K3, for a cable, coupon not run.

Living hinge. The Fictiv page opened here describes cantilever, annular, and torsion snaps. It does not give a living-hinge pattern, and it says fatigue needs an S-N curve. No living hinge is added. Battery and shell service stays on the screws already fitted.

Tongue and groove on the body shells is already in the printed parts (D38, screws twin). The screws that remain on those shells are the ones D38 and D42 kept. This pass does not cut them again.

## Tools

Tool-free assembly is not met. One-tool assembly is not met.

Socket sizes, cited:

- M3 DIN 912 uses a 2.5 mm hex (ISO 4762, sim/mass_budget.py, https://www.fasteners.eu/standards/DIN/912/).
- M2.5 DIN 912 uses a 2.0 mm hex (same source).
- M3 ISO 7380 uses a 2 mm hex nominal (Westfield table opened above).

That is two hex keys for the screws this design chooses. D36 already adds cross-head drivers for the M2 pan heads. The ear-servo bag screw size is not published (FASTENERS.md, F162 and F163). The driver for that pair is BLOCKER.

## FEA check (PR 43 and PR 46)

No STL in those studies is in the edit list, because the edit list is empty. st_fea.py was not re-run. An unchanged mesh is not a new result. The pitches below are the ones to reuse if a later job does change a part.

PR 43 (twin/structure/TOPOLOGY.md), FEA pass only, room-temperature PLA, voxel pitches: roll 0.9 mm, shin and thigh and neck 0.75 to 0.8 mm, head 1.0 mm, foot and hip 1.1 to 1.3 mm. Walking safety factor, then soft-fall worst, after the kept pads:

| Part | Walk | Soft worst | Soft falls under 1.2 | This pass |
|---|---|---|---|---|
| roll_to_pitch | 2.41 | 0.78 | 3 of 11 | STL not changed |
| shin drive eye | 1.30 | 0.87 | 3 of 11 | STL not changed. Horn screws stay four |
| thigh sheets | 1.71 | 0.94 | 2 of 11 | STL not changed |
| neck sheets | 11.85 | 0.99 | 6 of 11 | STL not changed |
| head_roll_mount | 52.49 | 1.03 | 2 of 11 | STL not changed |
| foot_top | 3.86 | 2.76 | 0 of 11 | STL not changed |
| hip roll stage | 16.74 | 2.33 | 0 of 11 | STL not changed |

Those factors are not hardware. Hot PLA strength and the fall contact stiffness stay guesses, as in that file.

PR 46 (twin/structure/shin_eye/SHIN_EYE.md) re-ran the shin at 0.75 mm so it matches the topology walk (stock 0.80, collar 1.30, FEA pass only). The recommendation, not installed in print/, is the recessed web in PA6-CF: walk 2.85, push 2.48, soft worst 1.61, 0 of 9 under 1.2, at 0.75 mm with the drive sheet at the PA6-CF modulus (FEA pass only). Hot tensile and wet tensile are BLOCKER there. This pass does not copy that STL and does not remove F203, F205, F207, or F250 (or the matching four on the other leg).

## CAD edits

None.

No line in print/. No line in altaay_lab/fasteners/fasteners.json. No hole opened or closed. D39 and D42 are unchanged. The shin horn pattern is unchanged.

## Joints

Every fitted screw is in one row. Qty is the fitted count, both sides included when the part name is shared. After equals before on every row.

| Qty | Joint | Spec | Decision |
|---|---|---|---|
| 56 | servo top case -> servo bottom case (servo case (factory)) | PA2.0 self-tapping (factory) | Factory screws inside the servo. The builder does not fit them. |
| 14 | drive horn -> servo output shaft (servo output shaft) | M3x6 machine screw (Feetech rocker screw) | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | foot_side -> passive_palonier (horn(passive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | foot_top -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | head_pitch_to_yaw -> drive_palonier (horn(drive)) | M3x5 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | head_pitch_to_yaw -> passive_palonier (horn(passive)) | M3x5 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | roll_motor_top -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 8 | shin_left_sheet -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load. PR 46 keeps four drive-horn screws on each shin (eight fitted). D42 unchanged. |
| 8 | shin_right_sheet -> passive_palonier (horn(passive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 6 | trunk_top -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 6 | trunk_top -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | SG90 tab -> head (plastic pilot 1.55 (SG90 tab)) | SG90 bag mounting screw | Screws twin keeps the ear screws. Antenna impact is not modelled, so a cut is BLOCKER. |
| 4 | battery_pack_lid -> body_back (plastic pilot 2.0) | M2.5x10 DIN 912 A2 | Screws twin: a thin plate keeps a 3-point set. D42 rejected a non-uniform 3, so the fitted uniform set stays. |
| 4 | bno055 -> trunk_top (plastic pilot 2.0) | M2.5x6 DIN 912 A2 | Four screws. The screws twin keeps the IMU at 4. |
| 4 | body_back -> body_middle_top (M3 insert) | M3x8 DIN 912 A2 | D38 kept these screws because a 3-screw back shell fails the downward fall check. Six stay fitted. Not cut further. |
| 4 | body_middle_bottom -> trunk_bottom (M3 insert) | M3x10 DIN 912 A2 | Frame joint. The screws twin kept the trunk stack (no lateral key). Not a PR 43 mesh member. STL not changed. |
| 4 | foot_bottom_tpu -> foot_bottom_pla (M3 insert) | M3x8 DIN 912 A2 | Foot joint. PR 43 fixes foot_bottom_pla and foot_side when it loads foot_top. STL not changed. Solver not re-run. |
| 4 | foot_side -> foot_top (M3 insert) | M3x10 DIN 912 A2 | Foot joint. PR 43 fixes foot_bottom_pla and foot_side when it loads foot_top. STL not changed. Solver not re-run. |
| 4 | head_bot_sheet -> head (M3 insert) | M3x8 DIN 912 A2 | Screws twin: a thin plate keeps a 3-point set. D42 rejected a non-uniform 3, so the fitted uniform set stays. |
| 4 | head_roll_mount -> head (M3 insert) | M3x6 DIN 912 A2 | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 4 | head_yaw_to_roll -> drive_palonier (horn(drive)) | M3x5 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | knee_to_ankle_left_sheet -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | knee_to_ankle_left_sheet -> passive_palonier (horn(passive)) | M3x6 ISO 7380 A2 button head | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | knee_to_ankle_left_sheet -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | knee_to_ankle_right_sheet -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | knee_to_ankle_right_sheet -> passive_palonier (horn(passive)) | M3x6 ISO 7380 A2 button head | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | knee_to_ankle_right_sheet -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | left_roll_to_pitch -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | left_roll_to_pitch -> passive_palonier (horn(passive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | neck_left_sheet -> drive_palonier (horn(drive)) | M3x5 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | neck_right_sheet -> passive_palonier (horn(passive)) | M3x5 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | right_roll_to_pitch -> drive_palonier (horn(drive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | right_roll_to_pitch -> passive_palonier (horn(passive)) | M3x6 DIN 912 A2 | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 4 | roll_motor_top -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | roll_motor_top -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | shin_left_sheet -> shin_spacer (M3 insert) | M3x6 DIN 912 A2 | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 4 | shin_left_sheet -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | shin_right_sheet -> shin_spacer (M3 insert) | M3x6 DIN 912 A2 | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 4 | shin_right_sheet -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 4 | trunk_top -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 3 | idle horn -> servo bottom case boss (servo idle boss pilot 2.67) | PA3.0x5 self-tapping, washer head (Feetech idle screw) | Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed. |
| 3 | left_roll_to_pitch -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 3 | right_roll_to_pitch -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | Camera Module 3 PCB (BOM E6) -> head (plastic pilot 1.65 (camera), drilled from 3.2 to 4.5 mm deep (D34)) | M2x5 self-tapping pan head | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | I2S mic board, left (BOM E8, D47) -> head (printed boss 5.0 mm, 3.5 mm high, pilot 1.65 x 5.6 mm (twin/companion/mic_seat.py, D47)) | M2x6 self-tapping pan head | A mirror pair or a diagonal pair already (D42). No new clip is drawn. |
| 2 | I2S mic board, right (BOM E8, D47) -> head (printed boss 5.0 mm, 3.5 mm high, pilot 1.65 x 5.6 mm (twin/companion/mic_seat.py, D47)) | M2x6 self-tapping pan head | A mirror pair or a diagonal pair already (D42). No new clip is drawn. |
| 2 | board -> trunk_top (plastic pilot 2.0) | M2.5x6 DIN 912 A2 | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | body_back -> body_middle_bottom (M3 insert) | M3x8 DIN 912 A2 | D38 kept these screws because a 3-screw back shell fails the downward fall check. Six stay fitted. Not cut further. |
| 2 | body_front -> body_middle_bottom (M3 insert) | M3x8 DIN 912 A2 | Screws twin: a thin plate keeps a 3-point set. D42 rejected a non-uniform 3, so the fitted uniform set stays. |
| 2 | body_front -> body_middle_top (M3 insert) | M3x8 DIN 912 A2 | Screws twin: a thin plate keeps a 3-point set. D42 rejected a non-uniform 3, so the fitted uniform set stays. |
| 2 | bulb -> left_eye (plastic pilot (eye)) | M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | bulb -> right_eye (plastic pilot (eye)) | M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | head_roll_mount -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x4 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | head_roll_mount -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | head_yaw_to_roll -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x5 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | head_yaw_to_roll -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | left_cache -> leg_spacer (M3 insert) | M3x10 DIN 912 A2 | Screws twin keeps the cache with the leg stack. leg_spacer is in the thigh study. STL not changed. |
| 2 | left_roll_to_pitch -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | neck_left_sheet -> wj-wk00-0122topcabinetcase_95 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | neck_right_sheet -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | neck_stop -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x12 self-tapping pan head | Two case screws, lengthened to hold the neck stop. Servo clamp stays screwed. |
| 2 | raspberrypizerow -> head (plastic pilot 2.0) | M2.5x6 DIN 912 A2 | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | right_cache -> leg_spacer (M3 insert) | M3x10 DIN 912 A2 | Screws twin keeps the cache with the leg stack. leg_spacer is in the thigh study. STL not changed. |
| 2 | right_roll_to_pitch -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | roll_motor_bottom -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x6 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 2 | speaker_interface -> speaker_stand (plastic pilot 2.12 (speaker stand)) | M2.5x5 DIN 912 A2 | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | speaker_stand -> head (plastic pilot 2.0) | M2.5x6 DIN 912 A2 | Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run. |
| 2 | tof_cliff -> body_front (plastic pilot 2.0 (printed standoff)) | M2.5x6 DIN 912 A2 | A mirror pair or a diagonal pair already (D42). No new clip is drawn. |
| 2 | trunk_top -> trunk_bottom (M3 insert) | M3x12 DIN 912 A2 | Frame joint. The screws twin kept the trunk stack (no lateral key). Not a PR 43 mesh member. STL not changed. |
| 2 | trunk_top -> wj-wk00-0124bottomcase_45 (servo pilot) | M2x8 self-tapping pan head | Clamps the servo case. The reaction stays screwed. |
| 1 | knee_to_ankle_left_sheet -> leg_spacer (M3 insert) | M3x6 DIN 912 A2 | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 1 | knee_to_ankle_left_sheet -> leg_spacer (M3 insert) | M3x6 ISO 7380 A2 button head | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 1 | knee_to_ankle_right_sheet -> leg_spacer (M3 insert) | M3x6 DIN 912 A2 | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 1 | knee_to_ankle_right_sheet -> leg_spacer (M3 insert) | M3x6 ISO 7380 A2 button head | Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run. |
| 1 | left_antenna_holder -> SG90 output shaft (SG90 output shaft (not modelled)) | SG90 bag horn screw | Screws twin keeps the ear screws. Antenna impact is not modelled, so a cut is BLOCKER. |
| 1 | right_antenna_holder -> SG90 output shaft (SG90 output shaft (not modelled)) | SG90 bag horn screw | Screws twin keeps the ear screws. Antenna impact is not modelled, so a cut is BLOCKER. |
| 1 | usb_c_charger -> body_back (plastic pilot 2.0) | M2.5x6 DIN 912 A2 | One screw. The screws twin keeps it for the plug force. |

## Open items

- Full assembly minutes: BLOCKER. The screws twin lists insert time, part handling, cable routing, labels, and tests as unmeasured. This pass does not invent those minutes.
- Seconds per screw: BLOCKER as a fresh cite. twin/screws/SCREWS_TWIN.md quotes 8 to 12 s from https://dfma.com/resources/assembly-cost-estimating.asp and says that page was not fetched. It was not opened here either. The builder still turns 268 screws (CAD check only), the same set, so the fastening time does not move.
- Ear-servo bag screw size, and the driver that fits it: BLOCKER (FASTENERS.md on F162 and F163).
- Weighed robot mass: BLOCKER.
- Hot tensile of the printed arms, and of PA6-CF at the knee temperature: BLOCKER, already recorded in TOPOLOGY.md and SHIN_EYE.md. This pass does not treat those safety factors as a bench result.

