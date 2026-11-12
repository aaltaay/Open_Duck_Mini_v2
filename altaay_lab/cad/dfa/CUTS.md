# Screw cuts

2026-11-12. Follows the DFA check (PR 52) and the fastener schedule in altaay_lab/cad/fasteners/. That schedule counts the same file: 361 screw rows, 324 fitted, 37 left out. Nest joints in that folder are not part of the 324, and this note does not add or remove them. print/ is not edited.

The target is under 200 fitted screws. The package that passes the checks removes 14. Fitted screws go from 324 to 310. Screws the builder turns go from 268 to 254. Under 200 is not met. The screws that would have to go next are the horn screws, the case clamps, and the shell and frame screws. The checks below say those stay.

Labels: CAD check only is a count or a mesh bound. Calc only is arithmetic on a cited load and the K3 section. Cited is a lab file or a page named in the sentence. BLOCKER means the number is not known, so that cut is not in the package.

## The gap, line by line

324 fitted minus 268 builder-turned is 56. That 56 is one schedule line, not a mix of leftovers from other joints.

| Supply | Fitted | Who turns it |
|---|---|---|
| Buy lines (BOM 17, including 10 button heads and 2 M2x12 whose supply string still says NEW LINE or NEW LENGTH) | 205 | builder |
| Servo bag (horn centre screws, fitted idle screws, M2 case screws from the bag) | 57 | builder |
| Ear-servo bag | 6 | builder |
| Factory case screws, already in the servo | 56 | not the builder |
| Sum | 324 | 268 builder |

205 + 57 + 6 = 268. 268 + 56 = 324. CAD check only, from fasteners.json, the same split cad/fasteners/schedule.json repeats.

The 56 factory screws are PA2.0, servo top case into servo bottom case, status FACTORY. There are 14 servos and 4 of these screws on each (head pitch, head roll, head yaw, neck pitch, and both ankles, knees, hip pitches, hip rolls, and hip yaws). 14 x 4 = 56. No other line has a factory screw. On every other line the builder count equals the fitted count.

| Fitted | Factory | Builder turns | Supply | Spec | Joint |
|---|---|---|---|---|---|
| 56 | 56 | 0 | factory | PA2.0 self-tapping (factory) | servo top case -> servo bottom case |
| 14 | 0 | 14 | bag | M3x6 machine screw (Feetech rocker screw) | drive horn -> servo output shaft |
| 8 | 0 | 8 | buy | M3x6 DIN 912 A2 | foot_side -> passive_palonier |
| 8 | 0 | 8 | buy | M3x6 DIN 912 A2 | foot_top -> drive_palonier |
| 8 | 0 | 8 | buy | M3x5 DIN 912 A2 | head_pitch_to_yaw -> drive_palonier |
| 8 | 0 | 8 | buy | M3x5 DIN 912 A2 | head_pitch_to_yaw -> passive_palonier |
| 8 | 0 | 8 | buy | M3x6 DIN 912 A2 | roll_motor_top -> drive_palonier |
| 8 | 0 | 8 | buy | M3x6 DIN 912 A2 | shin_left_sheet -> drive_palonier |
| 8 | 0 | 8 | buy | M3x6 DIN 912 A2 | shin_right_sheet -> passive_palonier |
| 6 | 0 | 6 | bag | M2x6 self-tapping pan head | trunk_top -> wj-wk00-0122topcabinetcase_95 |
| 6 | 0 | 6 | bag | M2x6 self-tapping pan head | trunk_top -> wj-wk00-0124bottomcase_45 |
| 4 | 0 | 4 | sg90 | SG90 bag mounting screw | SG90 tab -> head |
| 4 | 0 | 4 | buy | M2.5x10 DIN 912 A2 | battery_pack_lid -> body_back |
| 4 | 0 | 4 | buy | M2.5x6 DIN 912 A2 | bno055 -> trunk_top |
| 4 | 0 | 4 | buy | M3x8 DIN 912 A2 | body_back -> body_middle_top |
| 4 | 0 | 4 | buy | M3x10 DIN 912 A2 | body_middle_bottom -> trunk_bottom |
| 4 | 0 | 4 | buy | M3x8 DIN 912 A2 | foot_bottom_tpu -> foot_bottom_pla |
| 4 | 0 | 4 | buy | M3x10 DIN 912 A2 | foot_side -> foot_top |
| 4 | 0 | 4 | buy | M3x8 DIN 912 A2 | head_bot_sheet -> head |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | head_roll_mount -> head |
| 4 | 0 | 4 | buy | M3x5 DIN 912 A2 | head_yaw_to_roll -> drive_palonier |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | knee_to_ankle_left_sheet -> drive_palonier |
| 4 | 0 | 4 | buy | M3x6 ISO 7380 A2 button head | knee_to_ankle_left_sheet -> passive_palonier |
| 4 | 0 | 4 | buy | M2x5 self-tapping pan head | knee_to_ankle_left_sheet -> wj-wk00-0122topcabinetcase_95 |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | knee_to_ankle_right_sheet -> drive_palonier |
| 4 | 0 | 4 | buy | M3x6 ISO 7380 A2 button head | knee_to_ankle_right_sheet -> passive_palonier |
| 4 | 0 | 4 | bag | M2x6 self-tapping pan head | knee_to_ankle_right_sheet -> wj-wk00-0124bottomcase_45 |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | left_roll_to_pitch -> drive_palonier |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | left_roll_to_pitch -> passive_palonier |
| 4 | 0 | 4 | buy | M3x5 DIN 912 A2 | neck_left_sheet -> drive_palonier |
| 4 | 0 | 4 | buy | M3x5 DIN 912 A2 | neck_right_sheet -> passive_palonier |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | right_roll_to_pitch -> drive_palonier |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | right_roll_to_pitch -> passive_palonier |
| 4 | 0 | 4 | bag | M2x6 self-tapping pan head | roll_motor_top -> wj-wk00-0122topcabinetcase_95 |
| 4 | 0 | 4 | bag | M2x6 self-tapping pan head | roll_motor_top -> wj-wk00-0124bottomcase_45 |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | shin_left_sheet -> shin_spacer |
| 4 | 0 | 4 | buy | M2x5 self-tapping pan head | shin_left_sheet -> wj-wk00-0122topcabinetcase_95 |
| 4 | 0 | 4 | buy | M3x6 DIN 912 A2 | shin_right_sheet -> shin_spacer |
| 4 | 0 | 4 | bag | M2x6 self-tapping pan head | shin_right_sheet -> wj-wk00-0124bottomcase_45 |
| 4 | 0 | 4 | buy | M2x5 self-tapping pan head | trunk_top -> wj-wk00-0122topcabinetcase_95 |
| 3 | 0 | 3 | bag | PA3.0x5 self-tapping, washer head (Feetech idle screw) | idle horn -> servo bottom case boss |
| 3 | 0 | 3 | buy | M2x5 self-tapping pan head | left_roll_to_pitch -> wj-wk00-0122topcabinetcase_95 |
| 3 | 0 | 3 | buy | M2x5 self-tapping pan head | right_roll_to_pitch -> wj-wk00-0122topcabinetcase_95 |
| 2 | 0 | 2 | buy | M2x5 self-tapping pan head | Camera Module 3 PCB (BOM E6) -> head |
| 2 | 0 | 2 | buy | M2x6 self-tapping pan head | I2S mic board, left (BOM E8, D47) -> head |
| 2 | 0 | 2 | buy | M2x6 self-tapping pan head | I2S mic board, right (BOM E8, D47) -> head |
| 2 | 0 | 2 | buy | M2.5x6 DIN 912 A2 | board -> trunk_top |
| 2 | 0 | 2 | buy | M3x8 DIN 912 A2 | body_back -> body_middle_bottom |
| 2 | 0 | 2 | buy | M3x8 DIN 912 A2 | body_front -> body_middle_bottom |
| 2 | 0 | 2 | buy | M3x8 DIN 912 A2 | body_front -> body_middle_top |
| 2 | 0 | 2 | buy | M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers | bulb -> left_eye |
| 2 | 0 | 2 | buy | M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers | bulb -> right_eye |
| 2 | 0 | 2 | buy | M2x4 self-tapping pan head | head_roll_mount -> wj-wk00-0122topcabinetcase_95 |
| 2 | 0 | 2 | buy | M2x5 self-tapping pan head | head_roll_mount -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | buy | M2x5 self-tapping pan head | head_yaw_to_roll -> wj-wk00-0122topcabinetcase_95 |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | head_yaw_to_roll -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | buy | M3x10 DIN 912 A2 | left_cache -> leg_spacer |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | left_roll_to_pitch -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | neck_left_sheet -> wj-wk00-0122topcabinetcase_95 |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | neck_right_sheet -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | buy | M2x12 self-tapping pan head | neck_stop -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | buy | M2.5x6 DIN 912 A2 | raspberrypizerow -> head |
| 2 | 0 | 2 | buy | M3x10 DIN 912 A2 | right_cache -> leg_spacer |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | right_roll_to_pitch -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | bag | M2x6 self-tapping pan head | roll_motor_bottom -> wj-wk00-0124bottomcase_45 |
| 2 | 0 | 2 | buy | M2.5x5 DIN 912 A2 | speaker_interface -> speaker_stand |
| 2 | 0 | 2 | buy | M2.5x6 DIN 912 A2 | speaker_stand -> head |
| 2 | 0 | 2 | buy | M2.5x6 DIN 912 A2 | tof_cliff -> body_front |
| 2 | 0 | 2 | buy | M3x12 DIN 912 A2 | trunk_top -> trunk_bottom |
| 2 | 0 | 2 | buy | M2x8 self-tapping pan head | trunk_top -> wj-wk00-0124bottomcase_45 |
| 1 | 0 | 1 | buy | M3x6 DIN 912 A2 | knee_to_ankle_left_sheet -> leg_spacer |
| 1 | 0 | 1 | buy | M3x6 ISO 7380 A2 button head | knee_to_ankle_left_sheet -> leg_spacer |
| 1 | 0 | 1 | buy | M3x6 DIN 912 A2 | knee_to_ankle_right_sheet -> leg_spacer |
| 1 | 0 | 1 | buy | M3x6 ISO 7380 A2 button head | knee_to_ankle_right_sheet -> leg_spacer |
| 1 | 0 | 1 | sg90 | SG90 bag horn screw | left_antenna_holder -> SG90 output shaft |
| 1 | 0 | 1 | sg90 | SG90 bag horn screw | right_antenna_holder -> SG90 output shaft |
| 1 | 0 | 1 | buy | M2.5x6 DIN 912 A2 | usb_c_charger -> body_back |

Sum of the fitted column is 324. Sum of the factory column is 56. Sum of the builder column is 268.

## What a cut has to clear

The clip is the K3 cable clip already drawn (twin/screws/mesh_designs.py and lips.json): arm 0.9 mm thick, 12 mm long, barb overlap 0.4 mm. Strain is 1.5 x 0.9 x 0.4 / 12 squared = 0.375 percent. The service limit already used there is 0.535 percent. Changing only the barb width does not change that strain. The formula is the cantilever on the Fictiv page opened for DFA.md (https://www.fictiv.com/articles/how-to-design-snap-fit-components).

One clip has to hold the whole part, the same one-fastener rule as the screws twin. The load is the mid fall, 196 g on the head and 128 g on the trunk (cited, SCREWS_TWIN.md). SF 1.2. Walk at 3 g and SF 2 is the smaller number on every row below, so the fall sets the clip. Shear uses 12.7 MPa, the low end of the range in STRUCTURE_TWIN.md (0.577 x 22 MPa). One barb at width b and overlap 0.4 mm holds b x 0.4 x 12.7 N.

The arm bends in the layer plane, which is the Fictiv note for a printed cantilever. The barb width is then the print-up height. parts.csv names that axis. A clip is not used when the required width is taller than that print-up extent (CAD check only).

A clip comes off the same way it goes on: the Fictiv note says a return angle equal to the lead angle uses one force both ways. The parts stay separate, so the speaker still drops into the cage (ASSEMBLY_TWIN.md). They are not merged.

## Package: 14 screws

These pass the force calc and the print-up bound with 0.3 mm to spare (the hip-head margin in D19). Rank is screws saved. The effort is the same on each row: the K3 section, barb width only. A minimum under 5 mm is printed at the stock 5 mm when the part is tall enough.

| Rank | Joint | Screws now | After | Saved | Barb used mm | Print-up extent mm | STL |
|---|---|---|---|---|---|---|---|
| 1 | Mics, both | 4 | 0 | 4 | 5.0 | 59.4 (-z -> z) | head.stl |
| 2 | Adapter | 2 | 0 | 2 | 5.0 | 41.0 (+z -> z) | trunk_top.stl |
| 3 | Cliff board | 2 | 0 | 2 | 5.0 | 18.0 (-x -> x) | body_front.stl |
| 4 | Pi | 2 | 0 | 2 | 5.7 | 59.4 (-z -> z) | head.stl |
| 5 | Speaker interface to stand | 2 | 0 | 2 | 14.1 | 27.8 (vec:-0.2631 -0.9354 0.2362 -> y) | speaker_interface.stl |
| 6 | Speaker stand to head | 2 | 0 | 2 | 17.6 | 47.4 (-z -> z) | speaker_stand.stl |
| | Sum | 14 | 0 | 14 | | | |

Fitted screws 324 - 14 = 310. Builder-turned screws 268 - 14 = 254. Washers stay 8 (the eye screws stay). Inserts stay 48. These joints use pilots, not the heat-set inserts.

Per row, calc only unless noted:

- Mics, both. Mass 0.4 g (COMPANION.md 0.4 g each, product page). Required 0.9 N, so the minimum barb is 0.2 mm. Printed width 5.0 mm. Print-up extent 59.4 mm on head.stl, axis -z -> z, bounds 199.8 x 197.3 x 59.4 mm (CAD check only). Printed at the stock 5 mm.
- Adapter. Mass 16 g (STRUCTURE_TWIN.md 16 g, clip on trunk_top). Required 24.1 N, so the minimum barb is 4.7 mm. Printed width 5.0 mm. Print-up extent 41.0 mm on trunk_top.stl, axis +z -> z, bounds 125.5 x 100.7 x 41.0 mm (CAD check only). Printed at the stock 5 mm.
- Cliff board. Mass 1.8 g (FREEZE.md 1.8 g). Required 2.7 N, so the minimum barb is 0.5 mm. Printed width 5.0 mm. Print-up extent 18.0 mm on body_front.stl, axis -x -> x, bounds 18.0 x 110.0 x 143.0 mm (CAD check only). Printed at the stock 5 mm.
- Pi. Mass 12.6 g (STRUCTURE_TWIN.md 12.6 g, clip on the head). Required 29.1 N, so the minimum barb is 5.7 mm. Printed width 5.7 mm. Print-up extent 59.4 mm on head.stl, axis -z -> z, bounds 199.8 x 197.3 x 59.4 mm (CAD check only). Wider than 5 mm, same arm thickness and length.
- Speaker interface to stand. Mass 31.1 g (STRUCTURE_TWIN.md 31.1 g). Required 71.8 N, so the minimum barb is 14.1 mm. Printed width 14.1 mm. Print-up extent 27.8 mm on speaker_interface.stl, axis vec:-0.2631 -0.9354 0.2362 -> y, bounds 40.3 x 27.8 x 39.3 mm (CAD check only). Wider than 5 mm, same arm thickness and length.
- Speaker stand to head. Mass 38.8 g (STRUCTURE_TWIN.md 38.8 g). Required 89.5 N, so the minimum barb is 17.6 mm. Printed width 17.6 mm. Print-up extent 47.4 mm on speaker_stand.stl, axis -z -> z, bounds 51.4 x 46.0 x 47.4 mm (CAD check only). Wider than 5 mm, same arm thickness and length.

The cliff board keeps the printed standoffs from D54. The clip only holds the board down. The 25.4 x 17.8 mm board (cited, FREEZE.md) is wider than a 5 mm clip.

The mic board is 16.7 x 12.7 mm (cited, COMPANION.md). A 5 mm clip fits that edge. The arm sits on the head. The 0.4 g is each board, and each board gets its own clip.

Neighbour clash of the new clip against the next part is not swept. That sweep is the CAD check still open before anyone edits an STL. It is not a reason these 14 fail the force check.

## Checked, and not in the 14

| Idea | Screws it would touch | Result | Check |
|---|---|---|---|
| Eye clips | 4, and 8 washers | Minimum barb 4.1 mm, print-up extent 4.3 mm. Gap 0.2 mm, under the 0.3 mm margin. Screws stay. | CAD check only, fails |
| Battery lid clip | 4 | Print-up extent 7.5 mm, required barb 40.3 mm. Does not fit. Screws stay. | CAD check only, fails |
| Head bottom sheet clip | 4 | Print-up extent 3.0 mm, required barb 27.7 mm. Does not fit. Screws stay. | CAD check only, fails |
| Body shells | 10 (back 6, front 4) | Mid shell hit 2800 N (cited, SCREWS_TWIN.md). SF 1.2 needs about 660 mm of barb. The lips already carry shear. The screws stay. | calc only, fails |
| Horn screws, 4 down to 2 | 50 if every 4-hole horn lost 2 | Halving the screw count is taken as doubling the peak. Foot walk 3.86 becomes 1.93, under 2. Hip-roll soft fall 2.33 becomes 1.17, under 1.2. Roll, shin, thigh, neck, and head are already under a margin (PR 43, FEA pass only). PR 46 keeps four drive screws on each shin. Not cut. | calc only, fails |
| Servo case clamps | 68 | docs/assembly_guide.md says to fit the plastic screws that come with the servos. Pull-out of those M2 screws from the case is already a BLOCKER (STRUCTURE_TWIN.md). Not cut. | BLOCKER |
| Ear screws | 6 | Antenna impact is not modelled (screws twin). | BLOCKER |
| IMU, 4 screws | 4 | The screws twin keeps all 4. Not a clip. | cited |
| Charger, 1 screw | 1 | Inertial load is small. The plug force is not in the schedule. | BLOCKER |
| Camera, 2 screws | 2 | STRUCTURE_TWIN.md marks the 4 g mass UNVERIFIED. | BLOCKER |
| Heat-set insert swapped for a captive nut | 0 | The screw stays. Nuts would rise from 0. CNC Kitchen comparison is already cited in STRUCTURE_TWIN.md. Not a screw cut. | cited |
| Merge speaker interface and stand | 2 | The speaker is caged between them (ASSEMBLY_TWIN.md). Merging closes the cage. The clip keeps both parts. | CAD check only |
| Merge foot side and foot top | 4 | Those faces are the supports in the PR 43 foot study. A merge needs that study again. Not run. Not in the package. | FEA pass only, not run |
| Cache screws into the spacer | 4 | The screw also ties the knee sheet (screws twin). The spacer is in the thigh study. Not cut. | FEA pass only, not run |

Even if the failed horn cut (50) and a rough half of the case clamps (34) were added to the 14, fitted screws would be 324 - 14 - 50 - 34 = 226. Still over 200. Crossing under 200 would also drop shell screws or the frame and spacer screws. Those are the joints that hold the legs and the trunk. They are not in this package.

## CAD edits, not applied

No file under print/ changes. No row in fasteners.json changes. When a later job does the STL work, the edits are:

- head.stl: stock K3 section, barb 5.0 mm, at each mic board (F356, F357, F358, F359). Close those pilots.
- trunk_top.stl: K3 section, barb 5.0 mm, at the adapter (F119, F122). Close those pilots.
- body_front.stl: K3 section, barb 5.0 mm, holding the cliff board (F360, F361). Keep the D54 standoffs. Close only the two screw pilots.
- head.stl: K3 section, barb 5.7 mm, at the Pi pilots (F111, F114). Close those pilots.
- speaker_interface.stl: K3 section, barb 14.1 mm. Close the stand pilots for F353 and F354. The two parts stay separate.
- speaker_stand.stl: K3 section, barb 17.6 mm. Close the head pilots for F108 and F109.

D42: a joint with no screws left is a uniform pattern. The holes close with the STL edit, which is D39.

## Open items

- Under 200 fitted screws: not met. 310 is the package. The next 110 are blocked by the checks above.
- Neighbour clash of each new clip: not swept. CAD check still open before an STL edit.
- Coupon K3 has not been printed (screws twin). The strain number is calc only.
- Camera mass: BLOCKER (UNVERIFIED in STRUCTURE_TWIN.md).
- Charger plug force: BLOCKER.
- Ear impact: BLOCKER.
- M2 pull-out from the servo case: BLOCKER (STRUCTURE_TWIN.md).
- Hot tensile of the printed arms: BLOCKER, already in TOPOLOGY.md. These clips are not on those arms.

