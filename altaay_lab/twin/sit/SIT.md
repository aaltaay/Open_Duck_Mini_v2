# SIT: the A1b alert sit in the CAD and the records (D59)

2026-11-06 ET. Ahmed approved the alert sit (option A1b of the sit study; DECISIONS.md D59) and asked for the changes for
the sitting and the new angles. This folder makes them in the real CAD, the robot description and every record. Labels:
**CAD check only** (meshes, exact booleans), **calc** (hand checks shown here), **sim pass only** (MuJoCo on the repo
model), **BLOCKER** (data missing). Nothing is printed or bought.

The duck sits on its folded legs with the head up, then lets its torque go: it rests on hard stops, a TPU seat under the
rear belly and a TPU bumper under the front. On the feet-dock pads (D58) it charges torque fully off (sim pass only).

## 1. The parts (CAD check only)

| Part | Change | Numbers |
|---|---|---|
| shin_left_sheet, shin_right_sheet (new, from knee_to_ankle_*_sheet) | the plate is joggled 9 mm away from the leg centre plane from 16 mm round the knee axis down (a solid web from 16 to 18.4 mm); the lower end keeps the stock clamp on the ankle servo case with a 9 mm slab behind it, the stock 5.0 mm M2 head recess run on through it; the stock spacer holes closed (D39), two new ones on the new spacer pattern (3.2 mm through, 6.5 mm recess 2.0 mm deep) | 13.9 and 12.2 cm3; 11.58 and 11.09 g light profile |
| shin_spacer (new) | at the sheet back edge, 54.8 mm long (stock 36.8 + 18), 2 inserts per end on one pattern (D42) at x -44, z -104 and x -39.5, z -112.9 | 11.4 cm3, 7.28 g; carries the knee bumper |
| knee_bumper (new, TPU) | 28 x 14 x 3 mm on VHB on the spacer's front face, parallel to the knee servo case face at the 150 deg fold | 2 per robot |
| knee_to_ankle_left/right_sheet (thigh pair) | front edge relieved where the shin clamp passes at the fold (knee 100 to 150 deg) | 420 and 421 mm3 off |
| left_cache, right_cache | cut where the shin, the foot (along the sit and stand path, +/-3 deg) and the hip pad pass; the right cover is the exact mirror of the left | 12.7 of 64.6 cm3 off |
| foot_top, foot_side | heel notch where the shin passes down to the -95 deg stop, a case relief past the stop (-97.5 to -94 deg, 0.3 mm), the pad seats; the heel screw F024/F026 and its insert I34/I46 moved 20 mm toward the toe (it sat where the shin's M2 clamp boss arrives past -88 deg: both 34 mm from the ankle axis), old stack closed (D39) | notches 1.27 and 1.19 cm3, case relief 0.37 and 0.05 cm3 |
| ankle_pad (new, TPU) | 6 x 7.5 x 3 mm in a pocket on each foot plate, under the shin clamp block at -95 deg | 4 per robot |
| left/right_roll_to_pitch | printed lug onto roll_motor_bottom at hip roll -8 deg (outward), 14 mm wide (round 2, 2026-11-10; the first pass's lug was 1.07 cm3 with a 96 mm2 root), carved 0.8 mm behind the case corner's path so only the TPU face touches; root 123 mm2, W 226 mm3 | 1.20 cm3 |
| roll_pad_left, roll_pad_right (new, TPU) | conformal face in the lug: the case corner's path from 0.1 mm behind the stop 3.0 mm deeper, in a 12 x 9 mm box (centre r 17.5 mm from the roll axis, 32 mm2 of the case on it at the stop); a mirror pair. The left and right roll_to_pitch STLs carry 4 closed zero-volume shells each (under 0.1 mm2, left by the boolean; the slicer drops them) | 2 per robot, 0.11 g each |
| hip_pad (new, TPU) | 22 x 6 x 1.5 mm on roll_to_pitch where the thigh cover lands at hip pitch -75 deg | 2 per robot |
| neck_stop (new, PLA) | the neck back stop at +25 deg (round 2, 2026-11-10; in place of the first pass's lugs on the neck sheets): a block on trunk_top behind the neck, two pillars (x -42 to -18, y 15 to 23.4 and its mirror, z 85.8 to 116) joined by a bar over the cable lane (|y| under 15, z 100 to 108), a flange lobe round each hip yaw servo screw (F127, F129: M2x6 to M2x12, the head seat 6 mm higher on the flange, the same thread engagement in the servo case, a 4.6 mm counterbore open above for the driver, the stock trunk_top recess under it) and a 4 mm foot behind the pillars to x -56 (|y| 15 to 22, on trunk_top's flat top face, off the F126/F128 recesses): the tip pivot of the pad load sits at its back edge, 28.7 mm behind the screws; each pillar's front face carries a pad low on the sheet's back edge (centre r 28.0 from the neck axis, z 105.7, the face 33 deg from the horizontal on the edge's lower straight run) in a pocket 2.5 mm deep, so the load's line passes in front of the pivot and the screws see no pull-out at the stop (section 4); carved by the neck link, the yoke and the head floor over the neck range at head -25, -5, 15 and 39 deg (0.8 mm clear), off the hip yaw servo cable windows and the S2 and S7 lane, under the body shell's roof outside the neck opening; an exact mirror by construction | 14.6 cm3, 14.7 g (5 walls 40 %) |
| neck_pad (new, TPU) | 10 x 6 x 3 mm in the pockets, its face on the sheet's back edge line from r 23 to 33 mm (centre r 28.0) at +25 deg: the sheet is loaded in its plane (the first cut sat at r 36 to 46, high on the pillar: the tip moment that pulled the screws) | 2 per robot, 0.23 g each |
| neck_left/right_sheet | stock again: the first pass's lugs removed; print and URDF files byte for byte the base files (the builder restores them) | 7.5 and 6.7 g |
| head_pitch_to_yaw | the head forward stop at -25 deg (round 2; in place of the lug on the servo top at r 14 mm): a hook on the left arm, the side without the neck cables: a 4 mm doubler over the arm's whole outer face (y 23.2 to 27.2, x -12 to 12, z 146 to 170.5: the root 308 mm2, the first cut's 8 mm wide doubler gave 132 and failed the free forward shove; the stock horn screw counterbores run through it), a drop outboard of the left neck sheet to z 128 and a foot forward under the head floor's swept path (z 128 to 147, x to 38) with the pad pocket; carved by the neck link over head -25 to 45 deg, by the head floor and shell over yaw -105 to 79 and roll +-27 deg, by the trunk's front top over the neck and head ranges together, and by the yoke's hole keep-outs; F222 and the horn screws untouched | 4.3 cm3 added, 24.8 g |
| head_pad (new, TPU) | 12 x 6.1 x 10 mm (a 10 mm face: 0.3 of the stiffness of 3 mm; 6 mm in the first cut) in the hook's pocket, its face on the left sheet's front edge (x 16.4, z 125 to 137) at head -25 deg, r 29.3 mm | 1 per robot, 0.93 g |
| sit_seat, sit_bumper (new, TPU, 10 % infill) | rounded blocks on VHB under the belly: seat at x -110 mm, lowest point z -66 mm, 80 mm wide; bumper at x +20 mm, lowest point z -69 mm, 60 mm wide | 22.6 and 12.2 g |

Every hole of every changed stock part is checked to be there as before (audit/feat3d.py features of the base and the
new STL; sit_cad.py refuses to write otherwise); the heel screw stack is checked to have moved exactly 20 mm. A lug or a
pad seat is cut by a keep-out round every hole of its part. Every written STL is watertight after an STL round trip.

## 2. Joint ranges and servo limits

robot.urdf, robot.xml and robot_motors.xml carry the hard stops; software/servo_limits.json (servo_limits.py) gives the
software limits 3 deg inside every hard stop, which bench/set_angle_limits.py writes into the angle limit registers (9 and
11) and the sim uses as its actuator ranges. Left side; the right mirrors hip roll and hip pitch.

| Joint | URDF before | Hard stop now (what touches) | Software | Raw (zero offset) |
|---|---|---|---|---|
| knee | -90 to 90 | -28.5 (cache onto shin, CAD contact) to **150** (knee bumper) | -25.5 to 147 | 1758 to 3721 |
| ankle | -90 to 90 | **-95** (ankle pads) to 49 (shin onto foot_side, CAD contact) | -92 to 46 | 1001 to 2571 |
| hip roll | -25 to 25 | **-8** (roll lug, outward) to 25 | -5 to 22 | 1991 to 2298 |
| hip pitch | -70 to 30 | **-75** (hip pad) to 13.5 (thigh spacer onto the hip servo, CAD contact) | -72 to 10.5 | 1229 to 2167 |
| hip yaw | -30 to 30 | -24 (CAD contact) to 23.3 (F198 head onto body_middle_bottom first) | -21 to 20.3 | 1809 to 2279 |
| neck pitch | -20 to 65 | -20 to **25** (neck pads on the block) | -17 to 22 | 1855 to 2298 |
| head pitch | -45 to 45 | **-25** (head pad on the hook) to 39 (head onto body_middle_top) | -22 to 36 | 1798 to 2458 |

The knee's -90 to +150 deg span maps to raw 1024 to 3755: it does not cross the 0/4095 encoder wrap (340 steps, 30 deg,
of margin), so no offset register is needed; set_angle_limits.py refuses a range that would wrap after the calibrated
offset. Coupling (sit_sweep.py, CAD check only): with the knee past 110 deg the foot meets the cache unless the ankle is
low enough (knee 120: ankle -5 or less; knee 150: ankle -75 or less). The A1b path keeps it (ankle -92 at knee 147); the
sequence must fold knee and ankle together, never the knee alone. Joint zeros: software/CALIBRATION.md.

## 3. Collision sweep (CAD check only)

sit_sweep.py, exact meshes (manifold3d), every servo case filled, the repo robot.urdf and print/ STLs read on every run;
a pair counts above 2 mm3 over its zero-pose overlap. Results in sit_sweep.json.

- Every designed stop: clear 0.5 deg inside, touches 0.5 deg past on its named parts only: knee 150 (bumper onto the knee
  servo case), ankle -95 (pads onto the shin clamp blocks), hip roll -8 (lug onto roll_motor_bottom), hip pitch -75
  (hip pad onto the cache), neck +25 (the neck pads onto the stock sheets' back edges; the block itself and the yoke
  touch nothing), head -25 (the head pad onto the left sheet's front edge; the hook touches nothing): 6 of 6 on the
  final CAD (2026-11-07).
- The A1b sit and stand path at 1 deg steps, both legs, the torque-off settle onto the stops and the calibration band
  (every leg joint +/-3 deg at the sit): 204 states, no new overlap.
- The stock walk envelope (VERIFICATION.md E9 'ours' ranges, corners with the inward roll and yaw): 32 states, no new
  overlap.
- The get-up through the sit (D60; getup/GETUP_VIA_SIT.md, its programs in getup/programs/, the merged-model eval in
  getup/VIA_SIT_EVAL.md): 26 states, the
  tuck keyframes (4), the roll keyframes with their asymmetric legs and head yaw swing, both sides (14), and an envelope
  of the side swing (the head yaw at both software limits with the neck and head at the corners of their sit ranges,
  8). None of the new parts touches anything in them. The envelope's two corners with the neck at +22 and the head at
  +36 deg put the stock head shell and floor into body_middle_top and body_back (0.7 to 1.5 cm3): a stock-part
  interference at a corner of the software limits that no get-up keyframe visits (the roll keyframes hold the head at
  -14 deg); reported, not a sit change.
- Fasteners: sweep_fasteners.py over the new ranges (fasteners.json, FASTENERS.md), run again on the final CAD: 361
  heads and 108 tips, the screw-limited hits are the same 5 screws as before (2 left out by D18, F198 and F211 from hip
  yaw 23.3 deg, F333 not fitted); the new ranges add "parts collide first" rows only. 22 records moved with the parts
  (sit_records.py: the 16 spacer screws and inserts, the 4 heel screw and insert rows, and F127 and F129, the hip yaw
  servo screws that hold the neck stop block: M2x6 to M2x12, the seat 6 mm higher on the block's flange, counted under
  BOM line 17m); the shin rows name the shin parts; the M2 clamp screws keep their seat; the neck sheets' rows are the
  stock ones again. The 14 sit parts are URDF instances 131 to 144, the head internals 145 to 152.

## 4. Strength (calc)

**Stop loads (D59 review, 2026-11-07): the energy method, calc only; the compliant-stop sim as a cross-check.** The raw
hard limits of the Playground model gave one-step limit forces that were artefacts (1427 N on the hip roll lug, 736 N
on the neck lug are not loads a 2.75 kg robot makes), and a compliant-stop sim's own peak force does not converge with
the step (a 0.25 ms run moved a knee peak from 15.6 to 3.0 N m). What does converge is the impact speed. So every stop
(knee, ankle, hip roll, hip pitch, neck, head) now takes the energy method as its design load (sit_stress.py
energy_peaks): the link's kinetic energy at the moment it meets the stop, 0.5 I omega^2, with omega the joint speed on
the step before the limit engages (sit_sim.py Stops, recorded on every physics step of every push, stand-up, load and
shove run), I the joint's effective inertia at the sit pose from the mass matrix, armature included (sit_model.json
stops), absorbed by the stack compliance K of sitlib.STOP_STACK (a TPU face E A / t with E 26 MPa, est; a stop with no
TPU face is the printed lug in compression, E 3500 MPa, est; the printed parts in series taken as rigid, which is the
stiffer and so the conservative case; K = k r^2 at the contact radius, checked against the CAD within 1 mm): the peak
torque is omega sqrt(I K) on top of the rest torque, F = T / r. Service takes the largest omega over the push cases past
the ABUSE ones, fall 2 x service, abuse the ABUSE cases, stall the servo stall torque plus the rest torque, the shoves
the omega over the head shove sims (12 N on the head's CoM, forward and back, 0.2 and 1.0 s, torque off and on, the
body held: free, a 12 N head shove tips the sit over in 8 of 8 cases, section 5a). One lug or face carries each load.
The same K goes into the sim's joint limits (sit_model.py compliant_stops: solreflimit and solimplimit from I and K,
damping ratio 0.1), and the sim's own peak at 0.5 ms is kept beside each energy peak as sim_over_energy, the
cross-check of the order of magnitude. Validation on single runs (model_f, 0.5 ms; calc from sit_model.json I and K): the 12 N push from 8 sides gives
omega 0.50 rad/s at the knee (energy peak 4.4 N m against the sim's 12.9), 0.31 at the ankle (1.8 against 10.6), 0.23
at the hip roll lug (5.6 against 17.0), 0.28 at the neck (4.7 against 10.0) and 0.28 at the head (4.9 against 9.6): the
sim's limit impulses are 2 to 6 x the energy peaks on these impacts. The 12 N back shove with the torque on, body held,
drives the neck onto its +25 stop at 1.07 rad/s: 17.9 N m by energy against 19.1 in the sim (within 7 %), which is the
sizing case, and the reason the stop needs a TPU face: on a rigid printed lug (K 9365 N m/rad) that energy makes 870 N
at r 20.5 mm; on a 10 x 10 x 3 mm TPU face at r 35 mm (K about 1060 N m/rad) it makes 6.0 N m, 170 N, which a 20 x 14
mm pillar root carries at SF 2.6 (bending, across the layers; calc). **Status (2026-11-10): round 2 of the stops (the neck pads low on the sheets, the head hook's doubler over the whole arm
face with a 10 mm face, the roll lug with a conformal TPU face; section 1) is built, and the load, shove, push and
stand-up runs, the stress table and the stop results below are on that model (2.8078 kg; sit_sim.json inputs key
8b6e8c92845763bd).**

**Stop redesign, round 2 (2026-11-10; section 1 has the parts).** Targets: SF 1.5 for the 12 N head shove forward and
back, torque off and on, and at the neck stall; SF 2.0 service and 1.2 falls and abuse elsewhere. The first round's
table (2026-11-07, kept in git history) had three rows below target: the neck block's screws (482 N pull at the fall
load, SF 1.04), the head hook's root under the free 12 N forward shove (SF 0.34) and the hip roll lug on the energy
loads (SF 0.39 service, 741 N on a rigid PLA stack). Round 2:

- Neck back stop: the pads sit low on the stock sheets' back edges (centre r 28.0 mm from the neck axis, the lever of
  the pad's normal 25.8 mm, the face 33 deg from the horizontal, so 0.39 of the pad force runs along it into the pocket
  wall), K 815 N m/rad. A 4 mm foot behind the pillars to x -56 puts the block's tip pivot 28.7 mm behind the screws,
  and the pad load's line passes in front of that pivot: the tip moment about it is 0 in every case and the two M2x12
  screws (F127, F129) carry **0.0 N pull-out** (calc only). The pillar above the flange (250 mm2, W 907 mm3, across the
  layers) is the weakest structure row: SF 12.5 at service, 7.7 at the 12 N back shove with the torque on.
- Head forward stop: the 4 mm doubler now covers the arm's whole outer face (root face 306 mm2, Jp 28644 mm4 about its area centroid, farthest fibre 15.3 mm; the arm with
  the doubler 166 mm2, W 649 mm3) and the TPU face is 10 mm thick (K 163 N m/rad). The free 12 N forward shove (torque
  off, the head whipped onto the stop at 2.49 rad/s) gives 5.8 N m: root face SF 2.90, the arm 1.84 against 1.5; the
  neck stall 8.29 and 5.25 against 2.0. (The root face's Jp and fibre are integrated over the face region with
  its holes since 2026-11-10; the earlier vertex average put the fibre at 23.6 mm and gave 2.02 and 5.76.)
- Hip roll stop: the lug is 14 mm wide (1.20 cm3, root 123 mm2, W 226 mm3, arm 10.3 mm), carved 0.8 mm behind the
  roll_motor_bottom case corner's path, and carries a conformal TPU face (roll_pad_left, roll_pad_right: the corner's
  path from 0.1 mm behind the stop 3.0 mm deeper, 32 mm2 of the case on it), K 85 N m/rad. Service 1.46 N m (omega
  0.57 rad/s), 83.7 N at r 17.5 mm: pad bearing SF 3.83 and lug root 4.90 at service, 1.92 and 2.45 at the fall load,
  5.50 and 7.03 abuse, 2.29 and 2.93 at the stall.

Loads on the round-2 model (sit_stress.json, calc from the sim's omega record): neck service 3.6 N m (omega 0.70 rad/s,
I 0.030 kg m2; the sim's own limit peak 8.5), the 12 N back shove with the torque on 5.9 N m (omega 1.07; the sim
6.1), torque off 1.6 N m (sustained: the free head does not reach the back stop fast), the stall 1.9 N m; head service
0.76 N m (omega 0.29), the 12 N forward shove with the torque off 5.8 N m (omega 2.49 rad/s; the sim's compliant limit
2.3), torque on 0.70 N m (the 12 N shove held on the 48.7 mm arm from the head's CoM down to the
head pitch axis, by hand: it sizes this case); hip roll service 1.42 and 1.46 N m (left and right; the sim 5.2 and 3.3). All 112 rows pass
(sit_stress.json all_ok, shove_ok, abuse_ok and stall_ok true); the closest to its target is the shin sheet neck at
the fall load, SF 1.20 against 1.2 (the FEA scale on 7.83 N m of knee torque; 1.34 in the first round).

| Head and neck stop case (the weakest row) | SF | Against |
|---|---|---|
| head stop, 12 N shove forward on the head, torque off | 1.84 (yoke left arm with the doubler, level with the root) | 1.5: pass |
| head stop, 12 N shove forward on the head, torque on | 15.21 (the same row) | 1.5: pass |
| neck stop, 12 N shove back on the head, torque off | 9.39 (neck pad, TPU bearing) | 1.5: pass |
| neck stop, 12 N shove back on the head, torque on | 2.63 (neck pad, TPU bearing) | 1.5: pass |
| neck stop at a servo stall (one face) | 7.74 (neck pad, TPU bearing) | 1.5: pass |
| head hook at a servo stall | 5.25 (yoke left arm with the doubler) | 2.0: pass |
| roll stop, service (the legs fall onto the stops at the torque-off) | 3.83 (roll stop pad, TPU bearing) | 2.0: pass |
| roll stop, fall / abuse / stall | 1.92 / 5.50 / 2.29 (roll stop pad) | 1.2 / 1.2 / 2.0: pass |
| neck block screws F127, F129 (pull-out), every case | no pull: 0.0 N design load | check only (TEST_PLAN.md 19.8) |

The screw pull test of TEST_PLAN.md 19.8 stays as a check of the assembly (the design puts no pull on the screws; a
block that rocks on its foot or a pad set off its line would). The pad stiffnesses are estimates (TPU E 26 MPa, est),
and the sim's limit peaks run 1.3 to 4.2 x the energy peaks at service (sim_over_design in sit_stress.json; 0.39 x on
the free forward head shove, where the energy method is the larger).

sit_stress.py (sit_stress.json), STRUCTURE_TWIN.md allowables (PLA 47.1 MPa in-plane, 22 MPa across the layers, 12.7
MPa shear across the layers; TPU 95A bearing 10 MPa est; SF 2.0 service, 1.2 falls and abuse, 1.5 the shove and stall
targets of the head and neck stops). Service is the energy peak at the designed end over the load runs (the 17 push
cases with the compliant stops at 0.5 ms) and the stand-up; fall is 2 x service; abuse the ABUSE push cases (8dirs_F12,
mat_mu0.4_F8); stall the servo pressing into its stop at stall torque; the shove rows the 12 N head shoves. Every row
(calc only):

| Item | Case | Load | SF | Need |
|---|---|---|---|---|
| shin_spacer (beam between the sheets) | service | F 162.1 N at r 24.1 mm; M 1654 N mm; W 278 mm3 (layers along the beam: in-plane) | 7.90 | 2.0 |
| knee bumper pad (bearing) | service | TPU 95A on VHB 4950, 0.41 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 24.18 | 2.0 |
| spacer inserts (sideways) | service | 4 inserts per spacer, 40.5 N each against 618 N | 15.25 | 2.0 |
| shin sheet horn zone at the joggle | service | R per sheet 87.9 N x 9.0 mm = 791 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 3.68 | 2.0 |
| shin_spacer (beam between the sheets) | fall | F 324.3 N at r 24.1 mm; M 3308 N mm; W 278 mm3 (layers along the beam: in-plane) | 3.95 | 1.2 |
| knee bumper pad (bearing) | fall | TPU 95A on VHB 4950, 0.83 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 12.09 | 1.2 |
| spacer inserts (sideways) | fall | 4 inserts per spacer, 81.1 N each against 618 N | 7.62 | 1.2 |
| shin sheet horn zone at the joggle | fall | R per sheet 169.0 N x 9.0 mm = 1521 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 1.91 | 1.2 |
| shin_spacer (beam between the sheets) | stall | F 152.3 N at r 24.1 mm; M 1553 N mm; W 278 mm3 (layers along the beam: in-plane) | 8.42 | 2.0 |
| knee bumper pad (bearing) | stall | TPU 95A on VHB 4950, 0.39 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 25.74 | 2.0 |
| spacer inserts (sideways) | stall | 4 inserts per spacer, 38.1 N each against 618 N | 16.23 | 2.0 |
| shin sheet horn zone at the joggle | stall | R per sheet 83.0 N x 9.0 mm = 747 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 3.89 | 2.0 |
| shin_spacer (beam between the sheets) | abuse | F 189.2 N at r 24.1 mm; M 1930 N mm; W 278 mm3 (layers along the beam: in-plane) | 6.77 | 1.2 |
| knee bumper pad (bearing) | abuse | TPU 95A on VHB 4950, 0.48 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 20.72 | 1.2 |
| spacer inserts (sideways) | abuse | 4 inserts per spacer, 47.3 N each against 618 N | 13.07 | 1.2 |
| shin sheet horn zone at the joggle | abuse | R per sheet 101.5 N x 9.0 mm = 913 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 3.19 | 1.2 |
| shin sheet neck, knee torque (FEA scale) | service | 5.0 MPa per N m (STRUCTURE_TWIN.md, sheetlocal levels 2 and 3) x 3.92 N m | 2.41 | 2.0 |
| shin sheet neck, knee torque (FEA scale) | fall | 5.0 MPa per N m (STRUCTURE_TWIN.md, sheetlocal levels 2 and 3) x 7.83 N m | 1.20 | 1.2 |
| ankle pad (bearing, per pad) | service | 2 pads, 42.4 N each over 45 mm2 | 10.61 | 2.0 |
| foot plate pad seat (bearing) | service | PLA seat under the pad, across the layers (conservative) | 23.35 | 2.0 |
| ankle pad (bearing, per pad) | fall | 2 pads, 84.8 N each over 45 mm2 | 5.31 | 1.2 |
| foot plate pad seat (bearing) | fall | PLA seat under the pad, across the layers (conservative) | 11.68 | 1.2 |
| ankle pad (bearing, per pad) | stall | 2 pads, 31.4 N each over 45 mm2 | 14.33 | 2.0 |
| foot plate pad seat (bearing) | stall | PLA seat under the pad, across the layers (conservative) | 31.53 | 2.0 |
| ankle pad (bearing, per pad) | abuse | 2 pads, 27.3 N each over 45 mm2 | 16.51 | 1.2 |
| foot plate pad seat (bearing) | abuse | PLA seat under the pad, across the layers (conservative) | 36.32 | 1.2 |
| roll stop pad (TPU bearing) | service | F 83.7 N on the 17.5 mm lever of the pad's normal (pad centre r 17.5) over the case's 32 mm2 on the face | 3.83 | 2.0 |
| roll stop lug root (bending, across the layers) | service | F 83.7 N at r 17.5 mm; root 123 mm2, W 226 mm3, arm 10.3 mm (across the layers, conservative) | 4.90 | 2.0 |
| roll stop pad (TPU bearing) | fall | F 167.4 N on the 17.5 mm lever of the pad's normal (pad centre r 17.5) over the case's 32 mm2 on the face | 1.92 | 1.2 |
| roll stop lug root (bending, across the layers) | fall | F 167.4 N at r 17.5 mm; root 123 mm2, W 226 mm3, arm 10.3 mm (across the layers, conservative) | 2.45 | 1.2 |
| roll stop pad (TPU bearing) | stall | F 139.9 N on the 17.5 mm lever of the pad's normal (pad centre r 17.5) over the case's 32 mm2 on the face | 2.29 | 2.0 |
| roll stop lug root (bending, across the layers) | stall | F 139.9 N at r 17.5 mm; root 123 mm2, W 226 mm3, arm 10.3 mm (across the layers, conservative) | 2.93 | 2.0 |
| roll stop pad (TPU bearing) | abuse | F 58.3 N on the 17.5 mm lever of the pad's normal (pad centre r 17.5) over the case's 32 mm2 on the face | 5.50 | 1.2 |
| roll stop lug root (bending, across the layers) | abuse | F 58.3 N at r 17.5 mm; root 123 mm2, W 226 mm3, arm 10.3 mm (across the layers, conservative) | 7.03 | 1.2 |
| neck pad (TPU bearing) | service | F 140.3 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 4.28 | 2.0 |
| neck sheet back edge (in-plane bearing) | service | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 20.64 | 2.0 |
| neck pad pocket wall (the slide, across the layers) | service | 0.39 of F along the face = 55.3 N on the 6.0 x 2.5 mm pocket wall | 5.97 | 2.0 |
| neck pillar base (bending, across the layers) | service | M 1262 N mm on W 1981 mm3 plus 75.9 N on 359 mm2 (the block prints standing: the base is a layer plane) | 25.93 | 2.0 |
| neck pillar above the flange (bending, across the layers) | service | M 1322 N mm on W 907 mm3 plus 75.9 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 12.49 | 2.0 |
| neck block screw F127 or F129 (pull-out, one screw) | service | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 2.0 |
| neck pad (TPU bearing) | fall | F 280.7 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 2.14 | 1.2 |
| neck sheet back edge (in-plane bearing) | fall | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 10.32 | 1.2 |
| neck pad pocket wall (the slide, across the layers) | fall | 0.39 of F along the face = 110.6 N on the 6.0 x 2.5 mm pocket wall | 2.99 | 1.2 |
| neck pillar base (bending, across the layers) | fall | M 2525 N mm on W 1981 mm3 plus 151.9 N on 359 mm2 (the block prints standing: the base is a layer plane) | 12.96 | 1.2 |
| neck pillar above the flange (bending, across the layers) | fall | M 2644 N mm on W 907 mm3 plus 151.9 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 6.25 | 1.2 |
| neck block screw F127 or F129 (pull-out, one screw) | fall | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 1.2 |
| neck pad (TPU bearing) | stall | F 79.1 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 7.59 | 2.0 |
| neck sheet back edge (in-plane bearing) | stall | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 36.63 | 2.0 |
| neck pad pocket wall (the slide, across the layers) | stall | 0.39 of F along the face = 31.1 N on the 6.0 x 2.5 mm pocket wall | 10.60 | 2.0 |
| neck pillar base (bending, across the layers) | stall | M 711 N mm on W 1981 mm3 plus 42.8 N on 359 mm2 (the block prints standing: the base is a layer plane) | 46.01 | 2.0 |
| neck pillar above the flange (bending, across the layers) | stall | M 745 N mm on W 907 mm3 plus 42.8 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 22.17 | 2.0 |
| neck block screw F127 or F129 (pull-out, one screw) | stall | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 2.0 |
| neck pad (TPU bearing) | abuse | F 54.9 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 10.93 | 1.2 |
| neck sheet back edge (in-plane bearing) | abuse | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 52.76 | 1.2 |
| neck pad pocket wall (the slide, across the layers) | abuse | 0.39 of F along the face = 21.6 N on the 6.0 x 2.5 mm pocket wall | 15.26 | 1.2 |
| neck pillar base (bending, across the layers) | abuse | M 494 N mm on W 1981 mm3 plus 29.7 N on 359 mm2 (the block prints standing: the base is a layer plane) | 66.27 | 1.2 |
| neck pillar above the flange (bending, across the layers) | abuse | M 517 N mm on W 907 mm3 plus 29.7 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 31.93 | 1.2 |
| neck block screw F127 or F129 (pull-out, one screw) | abuse | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 1.2 |
| head pad (TPU bearing) | service | F 30.2 N at r 25.0 mm over 73 mm2 | 24.24 | 2.0 |
| neck sheet front edge (in-plane bearing) | service | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 117.93 | 2.0 |
| head pad pocket wall (the slide, across the layers) | service | 0.52 of F along the face = 15.8 N on the 6.1 x 2.5 mm pocket wall | 21.23 | 2.0 |
| head hook root face on the arm (shear across the layers, est) | service | the doubler's face on the arm, 306 mm2, carries M 884 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 22.31 | 2.0 |
| yoke left arm with the doubler, level with the root (bending across the layers) | service | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 892 N mm (lever 29.5 mm) | 14.13 | 2.0 |
| head hook foot plate at x 13 (bending, in the plate) | service | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 216 N mm (lever 7.1 mm); the plate prints flat | 38.80 | 2.0 |
| head pad (TPU bearing) | fall | F 60.4 N at r 25.0 mm over 73 mm2 | 12.12 | 1.2 |
| neck sheet front edge (in-plane bearing) | fall | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 58.97 | 1.2 |
| head pad pocket wall (the slide, across the layers) | fall | 0.52 of F along the face = 31.6 N on the 6.1 x 2.5 mm pocket wall | 10.61 | 1.2 |
| head hook root face on the arm (shear across the layers, est) | fall | the doubler's face on the arm, 306 mm2, carries M 1767 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 11.15 | 1.2 |
| yoke left arm with the doubler, level with the root (bending across the layers) | fall | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 1784 N mm (lever 29.5 mm) | 7.07 | 1.2 |
| head hook foot plate at x 13 (bending, in the plate) | fall | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 431 N mm (lever 7.1 mm); the plate prints flat | 19.40 | 1.2 |
| head pad (TPU bearing) | stall | F 81.2 N at r 25.0 mm over 73 mm2 | 9.01 | 2.0 |
| neck sheet front edge (in-plane bearing) | stall | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 43.84 | 2.0 |
| head pad pocket wall (the slide, across the layers) | stall | 0.52 of F along the face = 42.5 N on the 6.1 x 2.5 mm pocket wall | 7.89 | 2.0 |
| head hook root face on the arm (shear across the layers, est) | stall | the doubler's face on the arm, 306 mm2, carries M 2377 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 8.29 | 2.0 |
| yoke left arm with the doubler, level with the root (bending across the layers) | stall | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 2399 N mm (lever 29.5 mm) | 5.25 | 2.0 |
| head hook foot plate at x 13 (bending, in the plate) | stall | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 580 N mm (lever 7.1 mm); the plate prints flat | 14.42 | 2.0 |
| head pad (TPU bearing) | abuse | F 29.5 N at r 25.0 mm over 73 mm2 | 24.80 | 1.2 |
| neck sheet front edge (in-plane bearing) | abuse | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 120.65 | 1.2 |
| head pad pocket wall (the slide, across the layers) | abuse | 0.52 of F along the face = 15.4 N on the 6.1 x 2.5 mm pocket wall | 21.72 | 1.2 |
| head hook root face on the arm (shear across the layers, est) | abuse | the doubler's face on the arm, 306 mm2, carries M 864 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 22.82 | 1.2 |
| yoke left arm with the doubler, level with the root (bending across the layers) | abuse | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 872 N mm (lever 29.5 mm) | 14.46 | 1.2 |
| head hook foot plate at x 13 (bending, in the plate) | abuse | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 211 N mm (lever 7.1 mm); the plate prints flat | 39.69 | 1.2 |
| head pad (TPU bearing) | head stop, 12 N shove forward on the head, torque off | F 232.1 N at r 25.0 mm over 73 mm2 | 3.15 | 1.5 |
| neck sheet front edge (in-plane bearing) | head stop, 12 N shove forward on the head, torque off | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 15.34 | 1.5 |
| head pad pocket wall (the slide, across the layers) | head stop, 12 N shove forward on the head, torque off | 0.52 of F along the face = 121.5 N on the 6.1 x 2.5 mm pocket wall | 2.76 | 1.5 |
| head hook root face on the arm (shear across the layers, est) | head stop, 12 N shove forward on the head, torque off | the doubler's face on the arm, 306 mm2, carries M 6793 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 2.90 | 1.5 |
| yoke left arm with the doubler, level with the root (bending across the layers) | head stop, 12 N shove forward on the head, torque off | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 6854 N mm (lever 29.5 mm) | 1.84 | 1.5 |
| head hook foot plate at x 13 (bending, in the plate) | head stop, 12 N shove forward on the head, torque off | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 1656 N mm (lever 7.1 mm); the plate prints flat | 5.05 | 1.5 |
| head pad (TPU bearing) | head stop, 12 N shove forward on the head, torque on | F 28.1 N at r 25.0 mm over 73 mm2 | 26.08 | 1.5 |
| neck sheet front edge (in-plane bearing) | head stop, 12 N shove forward on the head, torque on | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 126.89 | 1.5 |
| head pad pocket wall (the slide, across the layers) | head stop, 12 N shove forward on the head, torque on | 0.52 of F along the face = 14.7 N on the 6.1 x 2.5 mm pocket wall | 22.84 | 1.5 |
| head hook root face on the arm (shear across the layers, est) | head stop, 12 N shove forward on the head, torque on | the doubler's face on the arm, 306 mm2, carries M 821 N mm (lever 29.3 mm) in shear: Jp 28644 mm4, r 15.3 mm | 24.00 | 1.5 |
| yoke left arm with the doubler, level with the root (bending across the layers) | head stop, 12 N shove forward on the head, torque on | the composite section at z 160.4: net 166 mm2, W 649 mm3, M 829 N mm (lever 29.5 mm) | 15.21 | 1.5 |
| head hook foot plate at x 13 (bending, in the plate) | head stop, 12 N shove forward on the head, torque on | the 4 mm plate outboard of the sheet: 94 mm2, W 241 mm3, M 200 N mm (lever 7.1 mm); the plate prints flat | 41.74 | 1.5 |
| neck pad (TPU bearing) | neck stop, 12 N shove back on the head, torque off | F 63.9 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 9.39 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop, 12 N shove back on the head, torque off | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 45.35 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop, 12 N shove back on the head, torque off | 0.39 of F along the face = 25.2 N on the 6.0 x 2.5 mm pocket wall | 13.12 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop, 12 N shove back on the head, torque off | M 574 N mm on W 1981 mm3 plus 34.6 N on 359 mm2 (the block prints standing: the base is a layer plane) | 56.97 | 1.5 |
| neck pillar above the flange (bending, across the layers) | neck stop, 12 N shove back on the head, torque off | M 602 N mm on W 907 mm3 plus 34.6 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 27.45 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop, 12 N shove back on the head, torque off | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 1.5 |
| neck pad (TPU bearing) | neck stop, 12 N shove back on the head, torque on | F 228.3 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 2.63 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop, 12 N shove back on the head, torque on | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 12.69 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop, 12 N shove back on the head, torque on | 0.39 of F along the face = 89.9 N on the 6.0 x 2.5 mm pocket wall | 3.67 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop, 12 N shove back on the head, torque on | M 2053 N mm on W 1981 mm3 plus 123.5 N on 359 mm2 (the block prints standing: the base is a layer plane) | 15.94 | 1.5 |
| neck pillar above the flange (bending, across the layers) | neck stop, 12 N shove back on the head, torque on | M 2150 N mm on W 907 mm3 plus 123.5 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 7.68 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop, 12 N shove back on the head, torque on | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 1.5 |
| neck pad (TPU bearing) | neck stop at a servo stall (one face) | F 77.6 N on the 25.8 mm lever of the pad's normal (pad centre r 28.0) over 60 mm2 (one face) | 7.74 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop at a servo stall (one face) | the stock sheet's 6.1 mm back edge over the 10 mm pad, the load in the sheet's plane | 37.35 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop at a servo stall (one face) | 0.39 of F along the face = 30.5 N on the 6.0 x 2.5 mm pocket wall | 10.80 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop at a servo stall (one face) | M 698 N mm on W 1981 mm3 plus 42.0 N on 359 mm2 (the block prints standing: the base is a layer plane) | 46.92 | 1.5 |
| neck pillar above the flange (bending, across the layers) | neck stop at a servo stall (one face) | M 730 N mm on W 907 mm3 plus 42.0 N on 250 mm2 at z 89.5 (the pillar alone, over the foot and the lobes) | 22.60 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop at a servo stall (one face) | tip moment 0 N mm about the pillar's back edge (x -56.0), screw lever 28.7 mm: 0.0 N against 500 N est | no pull (0 N): check only | 1.5 |

The joggled sheet itself is **BLOCKER** until the printed coupon test (TEST_PLAN.md 19.6).

## 5. Sim (sim pass only)

sit_sim.py on the repo model (sit_model.py: the Playground MJCF at b9be205, the masses of sim/mass_budget.py with the sit
parts, 2.8078 kg with the round-2 stops (2.806 kg with the first round of the stops, 2.788 kg in the first pass), the URDF ranges, the software limits as actuator ranges, the repo meshes; the seat and the bumper collide
with the floor). The SIT_V2 study ran a scratch copy (2.767 kg, the seat and bumper as capsules). sit_sim.json holds the
numbers.

**Stand-up, 2026-11-07 (sim pass only).** First the from-scratch rerun the cache fix asked for: on the 058e070 model
20 / 18 / 14 of 20 at 0 / 0.5 / 1.0 deg, the same as reported (every case file of that run was written after the gain
and clamp fixes, so it was not a cache hit). Every failing case, classified from per-step logs (torque, joint, contact,
CoM and sole edge; scratch, not in the repo): **tip back** in all 8. Four tipped back during the sit-down at knee 40 to
75 deg (seeds 3, 5, 8, 17 at 1.0 deg: "fell in the sit"), four at the end of the stand-up at knee 40 to 5 deg (seeds 3
and 17 at 0.5 deg, 6 and 18 at 1.0 deg). No joint saturated before a fall (the 3.23 N m neck peak comes after it, when
the head strikes), no foot slid before a fall, and the model has no self-contact (the stops are joint limits; the seat
and the bumper touch the floor only). Cause: along the study path the CoM sits 14 to 27 mm in front of the heel edge
of a 103 mm sole (feet flat, calc on the model); a 1 deg zero error moves it about 3.5 mm. Leads checked: (a) the neck
peak is the fall, not the rise; (b) the rock forward onto the bumper works in every case, the falls come later; (c) the
repo and the study models put the CoM within 0.5 mm of each other at every waypoint, so not the 39 g or the shins.
Fix (the sequence design for the Runtime): the trunk leans forward at the four middle waypoints (hip pitch +15 or +16
deg: sitlib.PATH_A1B), which puts the CoM 42 to 48 mm from the heel; the sit and stand ends are unchanged. That left
3 seeds standing with their feet 20 mm apart, off the pads: the torque-off sit splays the legs onto the -8 deg hip roll
stops and the rise kept that roll. The first stand-up ramp now brings hip roll and yaw back to 0 while the seat still
carries the trunk. On the final model (compliant stops, section 4):

| Stand-up from the torque-off sit, 20 seeds each | 0 / 0.5 / 1.0 deg zero error |
|---|---|
| Study (A1b, scratch model) | 20 / 20 / 19 |
| Repo model at 058e070 (from scratch) | 20 / 18 / 14 (sheet limits 14) |
| Tuning seeds 0 to 19, final path, first-pass model (2.788 kg) | 20 / 20 / 20 (sheet limits at 1.0 deg: 20) |
| Held-out seeds 100 to 119 (never used for tuning), first-pass model | 20 / 20 / 19 (sheet limits at 1.0 deg: 19) |
| Tuning seeds 0 to 19, final model with the neck stop block and the head hook (2.806 kg) | 20 / 20 / 20 (sheet limits at 1.0 deg: 20) |
| Held-out seeds 100 to 119, final model | 20 / 20 / 19 (seed 113; sheet limits at 1.0 deg: 19, the same seed) |
| Tuning seeds 0 to 19, round-2 stops (2.8078 kg) | 20 / 20 / 20 (sheet limits at 1.0 deg: 20) |
| Held-out seeds 100 to 119, round-2 stops | 20 / 20 / 19 (seed 113 again; sheet limits at 1.0 deg: 19, the same seed) |

Nothing else of the test changed (the success rule, the seeds, the zero error model, the gain randomization). Peak
torques in the sit and stand on the round-2 model: knee 1.72, neck 0.93, head pitch 0.80 N m (the first round 1.73 /
0.93 / 0.80). Every sim in this section and 5a was run again on the round-2 model (2026-11-10; sit_sim.json inputs key
8b6e8c92845763bd, sit_balance.json); the earlier numbers are kept in brackets where they differ.

| Test | Study (A1b) | Repo model now |
|---|---|---|
| Push, torque off on the pads, 17 cases | 0 falls; 4 pads made at the end in 17 | **0 falls; 4 pads made at the end in 16 of 17** (first pass 17 of 17, drift up to 13.0 mm; first round of the stops 16 of 17, drift up to 16.0 mm): the 12 N push from 8 directions in turn (8dirs_F12, an ABUSE case) ends 5.7 mm off its start with the CHG+ pad off its contacts (the rule wants two or more on every pad; the first round had one), the charge would wait for a re-seat, not a fall; 5 cases lift a pad on the way and make it again; drift up to 5.7 mm; trunk pitch -0.8 to 2.9 deg |
| Head shove 12 N, 0.2 and 1.0 s, forward and back, torque off and on | - | the body held: 0 falls in 8; free: tips over in 8 of 8 (section 5a) |
| Stock walk, 10 seeds, forward 0.15 m/s | 0.0956 against 0.1004 m/s before the sit, 0 falls | **0.1004 against 0.1029 m/s** (first pass 0.0998, first round of the stops 0.1001), 0 and 0 falls |

**Sit pose and renders (2026-11-07).** The first sit renders drew the duck 14 deg nose up. Cause: the scratch render
tool placed the robot at the commanded angles (knee 147, ankle -92, roll 0: 3 deg short of the stops) and rotated it
until the lowest points of the seat and the soles were level; at those angles that only happens 14 deg nose up, on the
heel edge. No check, record or sim start used that placement: the stand-up starts from physics (stance, then the
sit-down), the stop sweep uses joint angles only, the docked viewer scene uses twin/dock/docked_pose.json from the shared lab
gym (overlay gym/overlays/duck) sim, and the pad checks run in the sim. Now sit_pose.py takes the pose from the sim's settled torque-off sit (trunk pitch
+2.75 deg nose up, trunk z 71.2 mm; sit_pose.json) and the renders pose robot.urdf by it; render and check fail when a
render or record differs from the sim by more than 2 deg or the seat and soles are off the floor by more than 2 mm.

### 5a. Balance gate (sim pass only for the poses and the pushes, calc only for the margins)

sit_balance.py (sit_balance.json), at the sim's settled torque-off sit, in 11 cases: nominal; zero errors +1 and -1 deg
on every joint and mirrored left and right; head and trunk mass +5 and -5 %; floor mu 0.4; off the dock. Support: the
footprint of the touching soles, seat and bumper (vertices within 3 mm of the floor: the dock's spring pins lift the toes
1 to 3 mm). Gate (CoM inside by 10 mm or more, every tip angle 8 deg or more, in every case): **PASS**.

| | Nominal | Worst case |
|---|---|---|
| CoM inside the support, to the nearest edge | 75.9 mm (left sole - seat) | 75.6 mm (zero +1 deg left, -1 deg right) |
| Tip angle forward / back / left / right | 31.9 / 30.3 / 30.3 / 30.5 deg | 31.7 / 30.1 / 30.1 / 30.2 deg |
| Static push at head height that tips it (rigid robot, calc), 8 directions from forward | 8.3 / 11.6 / 10.9 / 7.8 / 7.8 / 7.9 / 11.2 / 11.8 N | 8.1 / 11.4 / 10.7 / 7.7 / 7.7 / 7.7 / 11.0 / 11.6 N |
| Sim push at the head CoM, ramped 2 N/s, torque off (neck and head free) | 4.3 / 5.0 / 8.5 / 6.5 / 6.3 / 6.5 / 9.0 / 4.9 N | 4.3 / 4.8 / 6.9 / 5.7 / 6.2 / 5.8 / 7.7 / 4.8 N |

(Round-2 model, 2.8078 kg, CoM 129.8 mm up at the sit; the first round of the stops, 2.806 kg: nominal 75.9 mm, worst 75.5
mm, tips 31.7 / 30.1 / 30.1 / 30.3 deg at worst, sim push 4.3 N forward at worst; the first pass, 2.788 kg: nominal margin
76.0 mm, worst 74.9 mm and 29.7 deg. The stop changes moved nothing that matters here.)

The sit is well inside its footprint, but with the torque off a push on the head tips it at about 4.3 N forward in the
sim (the rigid-robot calc says 7.7 N or more), and a 12 N head shove tips it in 8 of 8 free cases (sit_sim.py shove).
The support edges are not marginal, so no seat or bumper change; the weak point is the free head with the torque off,
which the learned skill below and a powered neck while people are near address.

**A neck forward stop, evaluated and not built (2026-11-07, sim pass only; on the first-pass model, 2.788 kg).** The question was whether a stop at about
-5 deg (the walk uses neck -0.3 to +14.8 deg) would raise the tipping push by keeping the neck from folding forward.
The same settle and ramped head push (sit_balance.py, nominal case) on the sit model with the neck's forward range cut
from -20 to -5 deg (software -2): the tipping push is 4.26 N forward against 4.37 N as it is, and within 0.2 N in five
of the other seven directions (90 deg 7.56 to 7.78 N, 270 deg 6.40 to 7.29 N); the CoM margin 75.9 to 75.7 mm. So the
neck's forward fold is not what tips the sit (the push at head height does, on a 2.8 kg robot sitting 71 mm high), and
the stop would touch the sit and stand path (neck -22 deg at its four middle waypoints, sitlib.PATH_A1B, clamped to
-19 by the software limit) and the get-up through the sit (D60: its tuck keyframes hold the neck at -19). Not built;
no part, no mass. The walk envelope would have cleared it by 1.7 deg (-0.3 against a -2 deg software limit).

## 6. Cables (CAD check only)

sit_cables.py from cables3d.json at the base: the route points and ties on the shin plates moved 9 mm with the joggle (6
ties, 6 cables); the knee loops grown by sliding the shin-side loop tie T034 along the cable until verify/c3_cables3d.py's
own loop check passes at 150 deg (D3: free 29 mm, bend R 11.0 mm against 10.4; SP4, S5 and S10 pass as routed); 4 more
loops grown the same way: D4 and S9 at the right hip pitch, D1 and P13 at the head (the round-2 run; the earlier list
had S10 and SP5 too, from loop checks on the wrong segment, see below). Stick-on mounts on changed parts checked with the cables3d test (seats_ties.py: 5 x 5 rays, 0.4 mm,
15 deg, room above) and placed again with its search where the cuts or the lugs took the patch: T030, T035 and T044 take
the small ABM1M mount; T046, T047, T048 and T071 a tie round the bundle at the test fit (D25). check_cables.py and C3: PASS (0 FAIL).
Run again on the round-2 CAD (2026-11-10, CAD check only), with three fixes found on the way:
- The block's round-2 foot (x -56 to -42, |y| 15 to 22, on trunk_top) and its pillars sat on the diagonal the
  trunk-side neck loops took across trunk_top at z 89: D1 and SD1 ran 2.4 to 2.6 mm into the block, and P13, D1, D13 and
  SD1 grazed the right pillar's front corner where they drop forward (-0.4 mm). sit_cables.py now takes them round the
  block (NECK_LANE: behind the foot at x -58.5, then inside the lane, |y| under 15; forward of the pillar's front face
  before the drop) and checks every trunk segment of every cable against the block's exact mesh: the closest is now 1.0
  mm (D1). The tie mount T021 (D1) sat under the block's footprint and T012 (P13, SD1, D13) under its corner: both placed
  again on trunk_top with the cables3d search (17.0 and 5.7 mm away).
- The mount re-check took only mounts on a changed part, against that part: a new part over a mount on a stock part was
  never seen. It now also takes every mount within 30 mm of a changed or new part, against those parts. That found the
  two foot mounts T037 and T051 (D3, D4) with foot_top 1.5 mm over them since the first pass (the pad seats): placed
  again on foot_bottom_pla, 4.0 and 8.0 mm away.
- The stored run lengths were never taken again after a route edit: the joggle's 9 mm moves (round 1) and the new ranges
  (knee 150, neck +25, head -25, hip roll -8) left them stale, and C3 and check_cables.py read them. check_cables.py now
  takes every run's zero, min, max and Runtime length again from its points over the URDF ranges (route_cables.py
  sweep) and carries the change into the wires and cables; 43 runs changed.
- The service loops' point indices stayed behind when points were inserted (the joggle's jog points, the neck lane),
  so C3's loop check and the loop growth looked at a stationary segment (P13's neck crossing at points 14 and 15, its
  loop still at 13 and 14); the base had 7 loops of SP4 and SP5 one point off already. sit_cables.py now carries every
  loop's crossing pairs and tie positions along with the insertions (remap_loops; an off base span is moved to the
  nearest crossing of its joints within 3 points, logged), and check_cables.py stops when a loop span does not cross
  the joints it names (unit tests: twin/sit/test_sit_cables.py). With the loops on their crossings S10's knee loop and
  SP5's hip loop pass as routed; the neck loops of P13 and D1 are under 3 x OD by storage radius (below).
Result: 61 cables, 15 pass, 38 pass with notes, 8 at the test fit, 0 FAIL. At the test fit: S2 and S7 (as before the
sit), DC3 (no cut length, as before), and four the stale lengths hid: the knee kit leads S5 and S10 are short by 25 and
24 mm against the 40 mm slack rule (150 mm kit cables; they fit taut with 15 and 16 mm to spare; the joggle adds 18 mm
at the zero pose) and the ankle power feeds SP4 and SP5 by 17 mm each (cut 420 and 450 mm; 23 mm to spare taut);
**BLOCKER** until the test fit (a longer kit lead is a purchase; SP4 and SP5 can be cut 20 mm longer from the 22 AWG
stock, a netlist change not made here). D10 (head, base routing) is short by 1 mm on the same rule: its stored main
length was 1.4 mm under its points' length since the base. The rub notes are the base's (P13, D1 and D2 against
head_pitch_to_yaw under head yaw at the full URDF range, -2.2 mm, on the right arm, the side without the hook; SP3, D3,
D4 and the dock cables as before); SD2 passes 0.7 mm from the block (its lane run), SD1 0.5 mm from the neck link. No
cable touches the neck pads, the hook, the head pad or the roll pads through the full URDF range.
Still under 3 x OD: SP4 at hip pitch (as before the sit), and the neck loops (D1, D2, D3, P13, S11) by storage radius
only: the neck range is smaller now (+65 to +25 deg), so C3's loop length at the farthest pose is shorter; the cable is
not. Knee loop flex test to 150 deg: TEST_PLAN.md 19.7.

## 7. Print, mass, BOM

- Sliced again (slice.py parts --only, D22 light profile, PrusaSlicer 2.7.2, this box; round 2 on 2026-11-07 ET):
  print/SLICE_SUMMARY.md and PRINT_CHECK.md (sit_print.py). Robot set 49 STLs, 68 parts, 1355.5 g, 119.9 h (the first
  round of the stops: 47 STLs, 66 parts, 1354.0 g, 119.7 h; the first pass 44 STLs, 62 parts, 1333.5 g, 117.5 h); D59
  adds 75.2 g of filament (TPU 40.0 g) and 8.8 h to the base set. The neck stop block is 14.7 g (5 walls 40 %, the neck
  profile), head_pitch_to_yaw with the hook 24.8 g (16.6 g stock, support included), each roll_to_pitch with its lug
  25.8 g (24.8 g stock), the five stop pads 1.6 g (2 neck pads 0.46, the head pad 0.93, 2 roll pads 0.22).
- Mass: **2807.8 g** against 2749.0 g (+58.8 g; the first round of the stops 2806.4 g, the first pass 2788.1 g;
  sim/MASS_BUDGET.md V1 sit section). The round-2 change is +1.4 g, under 5 g, but every sim was run again on it anyway
  (section 5; sit_model.py 2.8078 kg).
- BOM: PLA need about 1439 g (still 2 x 1 kg), TPU 74.5 g (1 x 1 kg), VHB 1.2 m (1 roll of 5 yd), stick-on mounts 27
  MB3A and 24 ABM1M (buy unchanged); the two hip yaw servo screws that hold the block go from M2x6 to M2x12, which no bag
  or kit has: BOM line 17m, 2 pieces, **nothing bought**, no listing read. MOUNTING.md V1 sit section.

## 8. BLOCKERs

- Unpowered servo friction: the torque-off sit and the pushes lean on it; no datasheet value (TEST_PLAN.md 19.5).
- Calibration: the zero repeatability at the stops is not measured; the stand-up needs 0.5 deg or better, 0.25 deg to be
  sure (software/CALIBRATION.md, TEST_PLAN.md 19.3).
- Joggled sheet strength: the printed coupon test (TEST_PLAN.md 19.6); the hand checks pass but the web of a 3D print
  is not a beam.
- The sit and stand sequence in the Runtime is not written; its design is sit_sim.py DOWN, SIT and rise (sitlib.PATH_A1B,
  the trunk leaned forward in the middle, hip roll back to 0 while seated).
- Closed in round 2 (2026-11-10, calc only, section 4): the neck stop block's screw pull-out (the pads moved low on the
  sheets and the block's foot put the load's line in front of its tip pivot: 0.0 N on F127 and F129 in every case; the
  pull test of TEST_PLAN.md 19.8 stays as a check of the assembly at that 0 N design load), the head hook under the free
  12 N forward shove (root 2.90, the arm 1.84 against 1.5; the stall 8.29 and 5.25 against 2.0) and the hip roll stop
  lug on the energy loads (the conformal TPU face: pad 3.83 and root 4.90 at service, 1.92 and 2.45 at the fall load).
  The two M2x12 screws are still in no bag or kit (BOM 17m; nothing bought).
- The stop stiffnesses rest on an estimated TPU modulus (E 26 MPa, est) and the 500 N screw pull-out is an estimate; the
  pad compression and the screw seat are checked at the first assembly (TEST_PLAN.md 19.8).
- Cable lengths at the test fit (section 6, CAD check only): the knee kit leads S5 and S10 are 24 and 25 mm short of
  the 40 mm slack rule (150 mm kit cables, taut with 15 and 16 mm to spare) and the ankle power feeds SP4 and SP5 17 mm
  short (taut with 23 mm to spare); a longer kit lead is a purchase (none made), SP4 and SP5 can be cut 20 mm longer
  (a netlist change not made in this PR). D10 in the head is 1 mm short on the same rule since the base (a stale stored
  length, now taken again from its points).
- The get-up through the sit (D60, getup/GETUP_VIA_SIT.md, sim pass only) holds the hip pitch servos at their torque
  limit through its sit-up (3.14 N m at 7.2 V, 2.62 N m at 6.0 V) and the rise holds the neck at its limit; the thermal
  and stall margins of those holds are not checked (TEST_PLAN.md 19.9). Re-run on the merged model (aad3a9a, round-2
  stops, 2026-11-10; getup/VIA_SIT_EVAL.md, sim pass only): 248 of 296 again (back 156 of 156, side 68 of 68, front 24 of
  72; the 48 down-ramp front rests fail at the tuck), case by case the same as the search; the hip pitch at its limit for
  up to 1.08 s, no servo over a Feetech protection line for the 2 s it needs (longest 1.14 s over 80 % duty, calc only);
  no joint more than 0.30 deg past a hard stop, and the head rule of section 3 holds in every case (the head at most
  +16.9 deg while the neck is above +15).
- Fall get-up on the real geometry (read-only retest, 2026-11-07, sim pass only; getup/GETUP_SIT.md and tables.md): the
  stored get-up programs raise the sit model in 0 of 296 cases (the base model, run the same way, 254 of 296). The base
  cannot do it on its own CAD either: with its CAD contacts as limits (knee -28.5, ankle +49.5, head yaw -108/+82, neck
  +37.5 deg) it gets 0 of 296; the programs need knee -88, ankle +80.7, neck +61 and head -43, and their earlier successes
  rest on the sim model's +-90 deg knee and ankle ranges. The sit's own new limits are the neck +25 and head -25 stops
  (the back program's head push and throw need neck +61 and head -43). The seat, the bumper, the mass and the hip roll
  stop cause no failure. Decided (D60, 2026-11-07): the sit stays as designed; get-up will roll onto the belly, tuck
  into the sit and use its stand-up, found by a search first, else trained in the walk retrain (track 10).

## Next

Sit-down and stand-up are scripted keyframes today. The plan is to train them as a learned skill in the walk retrain
(track 10, the shared lab gym (overlay gym/overlays/duck)), with calibration error, gain variation, pushes and head jerks
in training, as the Microduck team did after a seated head-jerk tip-back on their robot. The scripted sequence stays as
the fallback and as the CAD check path. No training or GPU spend in this PR.

## 9. Commands (scratch folders outside the repo)

    python3 altaay_lab/twin/sit/sit_cad.py --write [--cache <S>/cad.pkl]     the parts (print/ and the URDF copies)
    python3 altaay_lab/twin/sit/sit_urdf.py --write                        ranges, shin meshes, the sit links and geoms
    python3 altaay_lab/twin/sit/sit_records.py --write                     audit/assembly.json, audit/sites.json, fasteners.json
    python3 altaay_lab/twin/sit/sit_sweep.py                               the collision sweep (sit_sweep.json)
    python3 altaay_lab/fasteners/sweep_fasteners.py --scratch <S>/fast; python3 altaay_lab/fasteners/report_fasteners.py
    python3 altaay_lab/twin/sit/servo_limits.py --write                    software/servo_limits.json
    python3 altaay_lab/print/slice.py parts --out <S>/slice --only <the 23 STLs>; python3 altaay_lab/twin/sit/sit_print.py --slice <S>/slice --when '<ET date and time>' --write
    python3 altaay_lab/twin/sit/sit_cables.py --write; python3 altaay_lab/cables3d/route_cables.py --scratch <S>/c3d --grid-only; python3 altaay_lab/cables3d/check_cables.py --scratch <S>/c3d
    python3 altaay_lab/twin/sit/sit_model.py --out <S>/model; ODM_BEFORE_MODEL=<C8 'ours' model of the base> python3 altaay_lab/twin/sit/sit_sim.py --out <S>/model push|up|walk|summary
    python3 altaay_lab/twin/sit/sit_sim.py --out <S>/model up --seed0 100; ... shove; ... loads   held-out seeds, head shoves, stop loads
    python3 altaay_lab/twin/sit/sit_stress.py --sim <S>/model/sit_sim_loads.json,<S>/model/sit_sim_shove.json --model <S>/model/sit --write
    python3 altaay_lab/twin/sit/sit_pose.py --out <S>/model settle|check; python3 altaay_lab/twin/sit/sit_pose.py render --img <folder>
    python3 altaay_lab/twin/sit/sit_balance.py --out <S>/model --write                 the balance gate
