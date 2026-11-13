# When the duck breaks, and what gets hot

Written 2026-11-12. No servo, board, cell, or print was measured. The shared lab gym (overlay gym/overlays/duck) was not used. No new part is drawn here. The fixes at the end are ones already in the lab.

The 25 C check of this run matches the published thermal file: right knee reading crosses 60 C at 3.33 minutes, and the body reaches 94.67 C if torque is left on for 40 minutes (sim pass only, same model as twin/thermal/gate_p45b.json). Rooms below are 22 C and 32 C.

## Short answer

On the bought STS3215, the trained gait falls at 3.46 to 3.56 seconds (sim pass only, twin/electromech/ELECTROMECH_TWIN.md). That is the first failure. Heat and gear wear do not get a long walk on that gait.

If the actuators could hold the sim loads, the first printed part past its failure index is the shin drive eye on the current print (walk safety factor 0.79, FEA pass only, twin/structure/TOPOLOGY.md).

What gets hot, in the closed-shell model, on the trained-actuator walk: the right knee reading crosses the 60 C operating line at 3.7 minutes in a 22 C room and at 2.5 minutes in a 32 C room (sim pass only). The BEC case is hotter than that reading (109 C and 117 C). The winding number is higher still, and it sits on the guessed 2.5 J/K node. Do not read it as measured copper. With the existing 55 C guard and torque off between bouts, the reading stays at 55 C, and the duck can walk 29 minutes of each 90 at 22 C, or 17 minutes of each 90 at 32 C (sim pass only).

Charging while sitting, at 2.30 W or 3.50 W in the trunk, leaves the cells under 41 C (sim pass only). The charger die temperature inside the trunk is BLOCKER.

## 1. Heat map

Tool: twin/thermal/twin_thermal.py, with the P45B constants already set in gate_p45b.py. Closed shell: that model has no vent term, and this run did not add one. Central corner. Walk current is the existing P45B backlash session. Friction heat is omitted there, so the knee is slightly cool, as the knee heat study already says.

Charger watts are calc only, from circuitry/CHARGER_BOARD.md: 2.30 W at a 7.2 V pack and 3.50 W at a 6.0 V pack, 9.5 V in, 1.00 A. The older 1.9 W to 3.2 W band was not used.

The Pi chip temperature is BLOCKER. The thermal twin already says the chip-to-air rise is not published. Head air below is the 5 V branch node (3 W, the corner used by gate_p45b.py), not the chip. The Pi throttle line cited in that twin is 80 C.

### Unguarded backlash walk, 40 minutes, servo internal reading

Sim pass only. Only the two knees cross 60 C.

| Servo | 22 C room | 32 C room |
|---|---|---|
| left hip yaw | 42.5 | 52.4 |
| left hip roll | 31.3 | 41.3 |
| left hip pitch | 45.6 | 55.7 |
| left knee | 89.3 | 99.6 |
| left ankle | 42.6 | 52.7 |
| neck pitch | 43.5 | 53.3 |
| head pitch | 39.4 | 49.4 |
| head yaw | 38.9 | 48.9 |
| head roll | 44.7 | 54.6 |
| right hip yaw | 43.0 | 52.8 |
| right hip roll | 30.3 | 40.3 |
| right hip pitch | 38.1 | 48.1 |
| right knee | 99.3 | 109.5 |
| right ankle | 43.0 | 53.1 |

Right knee, same run: body 91.7 C and 101.6 C, winding node 169 C and 181 C. Time to a 60 C reading: 3.7 minutes at 22 C, 2.5 minutes at 32 C. Time to a 70 C reading: 5.0 and 3.5 minutes. The 32 C pair matches gate_p45b.json. The 94.7 C body remains the torque-left-on case. With the sheet torque-off at 70 C, the knee heat study puts the case near 63 C. This run did not repeat that cut.

Other closed-shell nodes, same unguarded walk:

| Node | 22 C room | 32 C room | Label |
|---|---|---|---|
| BEC case | 109 C | 117 C | sim pass only. Castle publishes no case limit: BLOCKER for a pass line |
| cells | 46.8 C | 56.4 C | sim pass only. Under the 60 C discharge line on the P45B sheet in this 40 minutes |
| head air | 31.0 C | 41.0 C | sim pass only. Not the Pi chip |
| trunk wall | 29.4 C | 39.2 C | sim pass only. Average wall, not the spot under the BEC |

The hottest resolved case is the BEC. The first limit the servo sheet actually states is the knee reading at 60 C, then torque off at 70 C (cited datasheet, STS3215 item 1-2 and item 7-11).

### Idle and charging while sitting

Six hours, or three hours for torque-on idle. End temperature. Sim pass only. Torque-off idle is the home idle in software/knee_heat.py. Torque-on idle uses the published stand watts in twin/thermal/tables.md, and trunk current from twin_thermal.electrical_point (calc only scale of those watts).

| Use | Room | Right knee reading | BEC case | Cells | Trunk wall | Head air |
|---|---|---|---|---|---|---|
| torque off | 22 C | 24.6 | 33.6 | 24.1 | 23.3 | 30.2 |
| torque off | 32 C | 34.5 | 43.3 | 34.0 | 33.2 | 40.1 |
| torque on | 22 C | 34.0 | 60.9 | 32.3 | 25.5 | 30.2 |
| torque on | 32 C | 43.9 | 70.1 | 41.8 | 35.3 | 40.1 |
| charge, 2.30 W | 22 C | 24.6 | 39.3 | 29.3 | 26.1 | 30.2 |
| charge, 2.30 W | 32 C | 34.5 | 48.9 | 39.0 | 35.9 | 40.1 |
| charge, 3.50 W | 22 C | 24.6 | 41.9 | 31.3 | 27.4 | 30.2 |
| charge, 3.50 W | 32 C | 34.5 | 51.5 | 40.9 | 37.2 | 40.1 |

Cells stay inside 0 C to 60 C on the P45B sheet in every sit above. Trunk wall stays under the 49 C to 57 C PLA heat-deflection band already cited in the thermal twin.

The charger die is a separate question. The chip sheet's 62 C/W is the standard board, not this trunk (circuitry/CHARGER_BOARD.md). On that board, 2.30 W is a 143 C rise and 3.50 W is a 217 C rise (calc only). The die regulates at 110 C (cited datasheet), so it will not sit at 2.30 W or 3.50 W. In-trunk thermal resistance is BLOCKER. The shell temperatures above are the upper bound if the current stayed at 1 A.

The earlier closed-loop twin sat near 48 C to 50 C on a torque-on stand in a 32 C room (sim pass only, knee heat study). This reconstruction of the published stand watts sits at 44 C. Both are sim. The 45 C restart in the guard can fail to arrive on the hotter of those two stands. Torque off is the rest that cools, which is what the guard already does.

### Duty cycle limit

Guard already in software/knee_heat.py: stop the walk at 55 C, torque off, walk again only under 45 C. This run holds the first 4 minutes of the backlash log steady (right knee 1.45 A), the same window as the knee heat study.

| Room | Walking minutes in 90 | Share | Knee reading peak | Knee body peak | BEC case peak |
|---|---|---|---|---|---|
| 22 C | 29.2 | 32 percent | 55.2 C | 50.4 C | 108 C |
| 32 C | 17.0 | 19 percent | 55.2 C | 51.3 C | 114 C |

The 0.2 C over 55 C is the 1 second step. The 32 C walking time matches the knee study's 17 minutes. The 22 C time is longer than that study's 26 minutes at 25 C, in the expected direction.

Unguarded, the duty limit is the time to 60 C: 3.7 minutes at 22 C and 2.5 minutes at 32 C (sim pass only).

The guard caps the knee reading. It does not cap the BEC case. The BEC is still near 110 C during the guarded walk.

Figures: heat_walk.png, heat_modes.png.

## 2. Stress of the printed parts

Walking and soft-fall numbers for the load path are the current-print voxel FEA in twin/structure/TOPOLOGY.md (FEA pass only, room-temperature PLA, walk margin 2, soft-fall margin 1.2). Hard floor in that file is the sentence that mid and hard contact still leave these parts under 1.2. A new hard-floor digit for this mesh was not published. The 2026-11-03 mid-contact table is an older mesh and an older mass. It is not copied here as the current digit.

A fall from a standing pose onto a hard floor is that mid contact (STRUCTURE_TWIN.md: edge or corner on tile or concrete). This note did not run a new fall.

Picked up by one foot, hanging straight down: the ankle carries (2.806 kg minus the 78 g foot) times 9.81, which is 26.8 N (calc only, masses from sim/MASS_BUDGET.md). The published walking axial peak at the left ankle is 27 N (sim pass only, STRUCTURE_TWIN.md). Radial walking peaks are 74 N, and the walking moments are several newton-metres. A straight hang does not exceed those walking peaks. The walking safety factor still governs. A sideways carry, leg stuck out as a beam, was not in the published load set: BLOCKER.

A child squeezing the shell: no grip-force table was opened for this note. The squeeze stress is BLOCKER for every part.

Figure: stress_sf.png.

### Parts with a published FEA factor

| Part | Walk SF | Soft-fall worst | Hard floor | Straight hang |
|---|---|---|---|---|
| shin_left_sheet, drive eye | 0.79 | 0.46 | under 1.2, digit BLOCKER | walking SF governs |
| left and right roll_to_pitch | 1.43 | 0.54 | under 1.2, digit BLOCKER | walking SF governs |
| thigh sheets | 1.78 | 0.70 | under 1.2, digit BLOCKER | walking SF governs |
| neck_left_sheet, neck_right_sheet | 5.20 | 0.38 | under 1.2, digit BLOCKER | walking SF governs |
| head_roll_mount | 52.5 | 1.03 | under 1.2, digit BLOCKER | walking SF governs |
| foot_top | 3.86 | 2.76, 0 of 11 under 1.2 | no new digit in TOPOLOGY.md. The 2026-11-03 mesh, different mass, mid SF 0.49 | walking SF governs |
| roll_motor_top, roll_motor_bottom | 16.7 | 2.33 | soft is 0 of 11 under 1.2 | walking SF governs |

Shin eye study, later FEA, stock idle sheet (shin_right_sheet) in PLA: walk 1.70, soft fall 0.80 (FEA pass only, twin/structure/shin_eye/SHIN_EYE.md). The spacer does not govern in that study. leg_spacer and shin_spacer have no separate factor: BLOCKER for a spacer-only number.

Knee and ankle case screws, older FEA: walking safety factor 1.6 on the ankle sheet (FEA pass only, STRUCTURE_TWIN.md). That is under the margin of 2.

### Body and head shells

STRUCTURE_TWIN.md section 6, hand calc, Roark clamped plate, already published: a wall hit of 400 N to 900 N is 31 MPa to 115 MPa, and a hard-floor hit of 1300 N to 2800 N is 102 MPa to 359 MPa. Strength used there is 47.1 MPa. Safety factor on the hard-floor band is 0.13 to 0.46 (calc only, 47.1 divided by that band). The soft band is 0.41 to 1.52, so it crosses 1. This is the group result for the body shell and the head shell, not a separate mesh of each file.

Shell files covered by that group result: body_front, body_back, body_middle_top, body_middle_bottom, trunk_top, trunk_bottom, head, head_bot_sheet.

battery_pack_lid is in the thermal shell list and was not given its own stress in that hand calc. Its number is BLOCKER.

### Printed parts with no published stress for these four loads

No joint-load FEA and no hand-calc digit. Walking, hard-floor, hang, and squeeze are BLOCKER for a stress number. A straight hang does not load them as a joint.

ankle_pad, bulb, flash_light_module, flash_reflector_interface, foot_bottom_pla, foot_bottom_tpu, foot_side, head_pad, head_pitch_to_yaw, head_yaw_to_roll, hip_pad, knee_bumper, left_antenna_holder, left_cache, left_eye, neck_pad, neck_stop, right_antenna_holder, right_cache, right_eye, roll_pad_left, roll_pad_right, sit_bumper, sit_seat, speaker_interface, speaker_stand.

foot_side and foot_bottom_pla are supports in the foot study. The published factor is foot_top. Their own factor was not published.

The antenna hit on the head is already BLOCKER in the holes twin. It is not modelled here.

No hole was opened or closed. D39 and D42 are unchanged.

## 3. Life, hours or cycles to a first failure

| Item | To a first failure | Label |
|---|---|---|
| Trained gait on the bought STS3215 | 3.5 seconds, the duck falls | sim pass only, ELECTROMECH_TWIN.md, 3.46 s to 3.56 s |
| Shin drive eye, current PLA, sim walking peak | the peak itself (safety factor 0.79, past the failure index) | FEA pass only. This peak is above the bought servo's stall, so the fall above happens first |
| Roll to pitch, thigh, neck, on a soft fall | one fall, worst safety factor 0.38 to 0.70 | FEA pass only, TOPOLOGY.md |
| Body or head shell on a hard floor | one hit in the published 102 MPa to 359 MPa band | hand calc already in STRUCTURE_TWIN.md, safety factor calc only |
| STS3215 gears at the life-test torque | at least 100,000 cycles, which is 15 hours of the 0.54 s gait | cited datasheet (over 100,000 cycles at 1/5 stall, about 0.38 Nm) and calc only for the hours (100,000 / 6667) |
| STS3215 gears at the sim knee torque | BLOCKER | sim RMS 2.19 Nm is above the 1.91 Nm stall. The sheet life test does not cover it. No gear-life exponent was added |
| Servo bearings, and the 6804ZZ | BLOCKER | no life rating was opened |
| PLA fatigue, older mesh, design curve | 0.02 h to 0.5 h on the knee sheet, 0.04 h to 0.7 h on roll_to_pitch | cited Ezeh and Susmel 2018 curve, already applied in STRUCTURE_TWIN.md. The same file's best-case endurance (35.8 MPa) says those spots last. The life between the two is still BLOCKER there |
| PLA fatigue, current shin eye | not a fatigue life. The walking peak is already past the failure index | FEA pass only |
| PETG fatigue cycles | BLOCKER | no S-N curve for this filament is in the lab. Static factors in the shin eye study miss the margins in PETG |
| PA6-CF fatigue cycles | BLOCKER | no S-N curve in the lab. Static factor on the recommended web is below |
| Flush pin, clean lab | 100,000 mates, and 10 years of one dock a day is 3,650 mates | cited Mill-Max line, already in twin/dock/flush/FLUSH_CONTACTS.md. Dirt and felt are BLOCKER there |
| Felt wear | BLOCKER | twin/contact/CONTACT_TWIN.md has no cycle count |
| P45B to 80 percent | BLOCKER | the version 1.2 sheet opened for the battery study does not state cycle life |
| Cable flex | BLOCKER for a cycle life | the knee loop is already checked at 11.0 mm against 10.4 mm (CAD check only, SIT.md). Bends per walking hour are 6,667 (calc only, the 0.54 s gait). No flex-life number for this wire was opened |

PA6-CF on the shin eye study's recommended web, static only: segment walk 2.85, push 2.48, soft fall 1.61, 0 of 9 under 1.2 (FEA pass only). Hot tensile and wet tensile remain BLOCKER in that file. PETG, PLA, PLA-CF, and ASA miss the margins on every shape that study ran.

The first thing that breaks, on the duck as printed with the bought knees, is the walk: it falls at about 3.5 seconds. The first printed part the FEA puts past its limit, on the loads of the trained actuator, is the shin drive eye.

## 4. Fixes for the weakest three

These three are already written up. Nothing new is added.

1. The 3.5 second fall. The electromech twin already ran the same sheet model at a flat 7.4 V: it does not fall in 20 seconds, and it walks at 0.64 of the command. The fall on the pack is the sag on the first steps. That file is the record. This note does not add a supply.

2. The shin drive eye at walk safety factor 0.79. The shin eye study already recommends the web sheet in Bambu PA6-CF, idle sheet in the same material, spacer left in PLA, existing M3x6 horn screws. Segment walk safety factor 2.85 (FEA pass only). The STL stays out of print/ until a dry coupon at about 60 C exists. That coupon is still BLOCKER there. Holes and screws are unchanged (D39, D42).

3. A hard-floor fall, parts under 1.2, and the topology pass already says another 2 mm does not fit. The structure twin's existing proposal for the first walks is a soft floor, a tether, and a spare roll part. This note does not add a shell.

The heat limit has a fix that is already in the tree: software/knee_heat.py, stop at 55 C, torque off, restart under 45 C. It holds the knee reading. It does not pull the BEC case down. No fan or heat sink is added here.

## Open BLOCKERs

- Pi chip temperature in the head.
- Charger die temperature in the closed trunk. The 62 C/W figure is the standard board.
- BEC case limit. Castle publishes none.
- Hard-floor safety factor digit on the current mesh. The published line is only "under 1.2".
- Stress for the printed parts listed as having none, and any child-squeeze load.
- Sideways pickup, leg used as a beam.
- PLA strength at 60 C, and the creep rate. Already BLOCKER in the structure twin.
- PLA fatigue life between the design curve and the best-case endurance. Already BLOCKER there.
- PETG and PA6-CF cycle life. PA6-CF hot and wet tensile. Already BLOCKER in the shin eye study.
- Servo gear life at a torque the life test does not cover. Servo bearing life. 6804ZZ life.
- Felt wear. Dirt on the flush pins. Already BLOCKER in those studies.
- P45B cycles to 80 percent on the sheet this lab opened.
- Cable flex life.
- A completed walk at sheet stall. The duck falls, so that load history does not exist.

## What was reused

- twin/thermal/twin_thermal.py and gate_p45b.py for every temperature in section 1.
- twin/thermal/KNEE_HEAT_STUDY.md for the 4 minute current window, the 55 C cap, and the torque-off rest.
- software/knee_heat.py for the 55 C and 45 C lines.
- circuitry/CHARGER_BOARD.md for 2.30 W and 3.50 W.
- twin/structure/TOPOLOGY.md and twin/structure/STRUCTURE_TWIN.md for the safety factors and the shell hand calc.
- twin/structure/shin_eye/SHIN_EYE.md for the PA6-CF web and the idle sheet.
- twin/electromech/ELECTROMECH_TWIN.md for the 3.5 second fall.
- STS3215 sheet life line, P45B temperature window, and the Mill-Max mate line already cited in the flush study.
