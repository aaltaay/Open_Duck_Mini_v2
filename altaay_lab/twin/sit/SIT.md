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
| left/right_roll_to_pitch | printed lug onto roll_motor_bottom at hip roll -8 deg (outward), carved so it touches only at the stop | 1.07 cm3 |
| hip_pad (new, TPU) | 22 x 6 x 1.5 mm on roll_to_pitch where the thigh cover lands at hip pitch -75 deg | 2 per robot |
| neck_stop (new, PLA) | the neck back stop at +25 deg (2026-11-07, in place of the first pass's lugs on the neck sheets): a block on trunk_top behind the neck, two pillars (x -42 to -23, y 15 to 23.4 and its mirror, z 85.8 to 126) joined by a bar over the cable lane (|y| under 15, z 100 to 108), a flange lobe round each hip yaw servo screw (F127, F129: M2x6 to M2x12, the head seat 6 mm higher on the flange, the same thread engagement in the servo case, a 4.6 mm counterbore open above for the driver, the stock trunk_top recess under it); each pillar's front face is 65 deg from the horizontal, 1.6 mm behind the stock sheet's back edge line at +25 deg, with a pocket 2.5 mm deep for the pad; carved by the neck link, the yoke and the head floor over the neck range at head -25, -5, 15 and 39 deg (0.8 mm clear), kept off the hip yaw servo cable windows and the S2 and S7 lane behind them and under the body shell's roof outside the neck opening; an exact mirror by construction | 13.3 cm3, 14.8 g (5 walls 40 %) |
| neck_pad (new, TPU) | 10 x 6 x 3 mm in the pockets, its face on the sheet's back edge line from r 36 to 46 mm (centre r 41.1) at +25 deg: the sheet is loaded in its plane | 2 per robot, 0.23 g each |
| neck_left/right_sheet | stock again: the first pass's lugs removed; print and URDF files byte for byte the base files (the builder restores them) | 7.5 and 6.7 g |
| head_pitch_to_yaw | the head forward stop at -25 deg (2026-11-07, in place of the lug on the servo top at r 14 mm): a hook on the left arm, the side without the neck cables: a 4 mm doubler on the arm's outer face (y 23.2 to 27.2, z 146 to 170.5, the stock horn screw counterbores run through it), a drop outboard of the left neck sheet to z 128 and a foot forward under the head floor's swept path (z 128 to 147, x to 38) with the pad pocket; carved by the neck link over head -25 to 45 deg, by the head floor and shell over yaw -105 to 79 and roll +-27 deg, by the trunk's front top over the neck and head ranges together, and by the yoke's hole keep-outs; F222 and the horn screws untouched | 3.7 cm3 added, 24.0 g |
| head_pad (new, TPU) | 12 x 6.1 x 6 mm (a 6 mm face: half the stiffness of 3 mm) in the hook's pocket, its face on the left sheet's front edge (x 16.4, z 125 to 137) at head -25 deg, r 29.3 mm | 1 per robot, 0.56 g |
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
- The get-up through the sit (D60; getup/GETUP_VIA_SIT.md, its programs copied to getup/programs/): 26 states, the
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
mm pillar root carries at SF 2.6 (bending, across the layers; calc). **Status (2026-11-07): the method is in the scripts, and the load, shove, push and stand-up runs on the final model
(the neck stop block and the head hook built, section 1), the stress table on them and the stop results below are done.**

**Head and neck stop redesign (built 2026-11-07; section 1 has the parts).** Targets: SF 1.5 for the 12 N head shove
forward and back, torque off and on, and at the neck stall; the structure margins elsewhere. The first pass's lugs
(the neck lug's root the stock sheet's edge at r 20.5 mm, the head lug at r 14 mm on the servo case) are gone: the neck
back stop is two TPU faces on a printed block on trunk_top (F127 and F129 lengthened to M2x12), the stock neck sheets'
back edges on them at r 41.1 mm (the lever of the pad's normal 38.1 mm: the face is 65 deg from the horizontal, so
0.37 of the pad force runs along the face into the pocket wall), K 1757 N m/rad; the head forward stop is a TPU face
in a hook on the left arm of head_pitch_to_yaw, the left sheet's front edge on it at r 29.3 mm (lever 25.0 mm, slide
0.52), K 272 N m/rad with the 6 mm face. The pad radii in sitlib.STOP_STACK are the builders' (sit_cad.json pad_r_mm,
checked by sit_stress.py stack_check within 0.05 mm; the sim's K uses them, the stiffer and so the conservative choice;
the stress rows turn the torque into the pad force on the normal's lever).

Loads on the final model (sit_stress.json, calc from the sim's omega record): neck service 5.6 N m (omega 0.76 rad/s,
I 0.030 kg m2; the sim's own limit peak 6.1), the 12 N back shove with the torque on 8.6 N m (omega 1.07; the sim 8.7),
torque off 1.6 N m (the free head does not reach the back stop fast: the sustained load sizes it), the stall 2.0 N m;
head service 0.97 N m (omega 0.30), the 12 N forward shove with the torque off **7.4 N m** (omega 2.49 rad/s: the free
head whips onto the stop; the sim's compliant limit shows 3.1), torque on 0.71 N m, the stall 2.0 N m; hip roll service
**13.0 N m** (omega 0.54 rad/s on a rigid PLA lug, K 17150 N m/rad; the sim 23.9).

| Head and neck stop case (the weakest row) | SF | Against 1.5 |
|---|---|---|
| head stop, 12 N shove forward on the head, torque off | 0.34 (head hook root face on the arm (shear across the layers, est)) | **below 1.5** |
| head stop, 12 N shove forward on the head, torque on | 3.60 (head hook root face on the arm (shear across the layers, est)) | pass |
| neck stop, 12 N shove back on the head, torque off | 7.09 (neck block screw F127 or F129 (pull-out, one screw)) | pass |
| neck stop, 12 N shove back on the head, torque on | 1.35 (neck block screw F127 or F129 (pull-out, one screw)) | **below 1.5** |
| neck stop at a servo stall (one face) | 5.84 (neck block screw F127 or F129 (pull-out, one screw)) | pass |
| roll stop lug, service (the legs fall onto the stops at the torque-off) | 0.39 (root bending across the layers, F 741 N) | **below 2.0** |
| roll stop lug, fall / abuse / stall | 0.20 / 0.60 / 1.97 | **below 1.2 / 1.2 / 2.0** |

**Neck stop block: passes on the structure.** Service: pad bearing SF 4.1, the sheet's back edge 19, the pocket wall 6.0,
the pillar base (M 4138 N mm on W 566 mm3, across the layers: the block prints standing) 2.9; the 12 N back shove with
the torque on: pillar base 1.88, pad 2.65, pocket wall 3.9; the stall and the torque-off shove 5.8 or more. The one
open row is the screw: 241 N pull on one M2x12 at service (SF 2.07 against the 500 N estimate), **482 N at the fall
load (SF 1.04 against 1.2) and 370 N at the back shove with the torque on (SF 1.35 against 1.5)**, so the pull test of
TEST_PLAN.md 19.8 has to show 580 N or more per screw, or the block gets a third screw or a longer flange (the tip
pivot at x -42, the screw lever 14.7 mm). **BLOCKER until the pull test.**

**Head hook: BLOCKER on the free forward shove and the stall (calc).** With the torque on, every row passes (SF 126 at
the shove). With the torque off, the 12 N forward shove puts 7.4 N m on the stop: the hook's root face on the arm (the
doubler's 132 mm2 face, in shear across the layers, est; M 7727 N mm) is at **SF 0.34** and the arm with its doubler,
level with the root (118 mm2 net, W 357 mm3, bending across the layers), at **SF 0.86** against 1.5; at the neck servo
stall the root face is at SF 1.25 against 2.0. Fix, not built (a CAD change restarts the sweep, the cable check, the
slice, the mass and every sim): a root over the arm's whole height with a fillet (area x2, polar modulus x4) and the
face 6 to 10 mm thick (K 272 to 160 N m/rad, the impact torque x0.78), or a through-screw root; the free 12 N shove is
the ABUSE case for this part (a torque-off head whipped by hand), so SF 1.2 on it would do if the lead accepts that.

**Hip roll stop lug: BLOCKER on the energy loads (calc).** The first pass's lug (1.07 cm3 on roll_to_pitch, PLA on
PLA, root 96 mm2, W 157 mm3, arm 10.3 mm) was sized on the hard-limit artefact and the old table had it at SF 0.2 by
that; by the energy method the legs falling onto the stops at the torque-off (omega 0.54 rad/s) make 13.0 N m on a
rigid stack, 741 N at r 17.5 mm: root bending SF 0.39 at service, 0.20 at the fall load, 0.60 abuse, 1.97 at the stall.
Fix, not built: a 3 mm TPU face in a pocket on the lug (K to about 1100 N m/rad, the impact torque x0.25) and the root
doubled (W 157 to 400 mm3), which the calc puts at SF 2 or more at service; or the stop on the trunk side at a larger
radius. Until then the hip roll stop is a soft limit in software (the Runtime holds -8 deg) and the torque-off sit
leans on it.

sit_stress.py (sit_stress.json), STRUCTURE_TWIN.md allowables (PLA 47.1 MPa in-plane, 22 MPa across the layers, 12.7
MPa shear across the layers; TPU 95A bearing 10 MPa est; SF 2.0 service, 1.2 falls and abuse, 1.5 the shove and stall
targets of the head and neck stops). Service is the energy peak at the designed end over the load runs (the 17 push
cases with the compliant stops at 0.5 ms) and the stand-up; fall is 2 x service; abuse the ABUSE push cases (8dirs_F12,
mat_mu0.4_F8); stall the servo pressing into its stop at stall torque; the shove rows the 12 N head shoves. Every row:

| Item | Case | Load | SF | Need |
|---|---|---|---|---|
| shin_spacer (beam between the sheets) | service | F 146.0 N at r 24.1 mm; M 1489 N mm; W 278 mm3 (layers along the beam: in-plane) | 8.78 | 2.0 |
| knee bumper pad (bearing) | service | TPU 95A on VHB 4950, 0.37 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 26.85 | 2.0 |
| spacer inserts (sideways) | service | 4 inserts per spacer, 36.5 N each against 618 N | 16.93 | 2.0 |
| shin sheet horn zone at the joggle | service | R per sheet 79.9 N x 9.0 mm = 719 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 4.05 | 2.0 |
| shin_spacer (beam between the sheets) | fall | F 292.0 N at r 24.1 mm; M 2978 N mm; W 278 mm3 (layers along the beam: in-plane) | 4.39 | 1.2 |
| knee bumper pad (bearing) | fall | TPU 95A on VHB 4950, 0.74 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 13.43 | 1.2 |
| spacer inserts (sideways) | fall | 4 inserts per spacer, 73.0 N each against 618 N | 8.47 | 1.2 |
| shin sheet horn zone at the joggle | fall | R per sheet 152.9 N x 9.0 mm = 1376 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 2.11 | 1.2 |
| shin_spacer (beam between the sheets) | stall | F 152.0 N at r 24.1 mm; M 1550 N mm; W 278 mm3 (layers along the beam: in-plane) | 8.43 | 2.0 |
| knee bumper pad (bearing) | stall | TPU 95A on VHB 4950, 0.39 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 25.79 | 2.0 |
| spacer inserts (sideways) | stall | 4 inserts per spacer, 38.0 N each against 618 N | 16.26 | 2.0 |
| shin sheet horn zone at the joggle | stall | R per sheet 82.9 N x 9.0 mm = 746 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 3.90 | 2.0 |
| shin_spacer (beam between the sheets) | abuse | F 188.5 N at r 24.1 mm; M 1923 N mm; W 278 mm3 (layers along the beam: in-plane) | 6.80 | 1.2 |
| knee bumper pad (bearing) | abuse | TPU 95A on VHB 4950, 0.48 MPa over 392 mm2; 10 MPa used as a TPU compressive working value (est) | 20.79 | 1.2 |
| spacer inserts (sideways) | abuse | 4 inserts per spacer, 47.1 N each against 618 N | 13.11 | 1.2 |
| shin sheet horn zone at the joggle | abuse | R per sheet 101.1 N x 9.0 mm = 910 N mm on a 25 x 3.85 mm section (bending in the layers: the sheet prints flat) | 3.20 | 1.2 |
| shin sheet neck, knee torque (FEA scale) | service | 5.0 MPa per N m (STRUCTURE_TWIN.md, sheetlocal levels 2 and 3) x 3.52 N m | 2.67 | 2.0 |
| shin sheet neck, knee torque (FEA scale) | fall | 5.0 MPa per N m (STRUCTURE_TWIN.md, sheetlocal levels 2 and 3) x 7.05 N m | 1.34 | 1.2 |
| ankle pad (bearing, per pad) | service | 2 pads, 42.1 N each over 45 mm2 | 10.70 | 2.0 |
| foot plate pad seat (bearing) | service | PLA seat under the pad, across the layers (conservative) | 23.54 | 2.0 |
| ankle pad (bearing, per pad) | fall | 2 pads, 84.1 N each over 45 mm2 | 5.35 | 1.2 |
| foot plate pad seat (bearing) | fall | PLA seat under the pad, across the layers (conservative) | 11.77 | 1.2 |
| ankle pad (bearing, per pad) | stall | 2 pads, 31.4 N each over 45 mm2 | 14.33 | 2.0 |
| foot plate pad seat (bearing) | stall | PLA seat under the pad, across the layers (conservative) | 31.53 | 2.0 |
| ankle pad (bearing, per pad) | abuse | 2 pads, 26.6 N each over 45 mm2 | 16.93 | 1.2 |
| foot plate pad seat (bearing) | abuse | PLA seat under the pad, across the layers (conservative) | 37.26 | 1.2 |
| roll stop lug | service | F 740.8 N at r 17.5 mm; root 96 mm2, W 157 mm3, arm 10.3 mm (across the layers, conservative) | 0.39 | 2.0 |
| roll stop lug | fall | F 1481.7 N at r 17.5 mm; root 96 mm2, W 157 mm3, arm 10.3 mm (across the layers, conservative) | 0.20 | 1.2 |
| roll stop lug | stall | F 146.8 N at r 17.5 mm; root 96 mm2, W 157 mm3, arm 10.3 mm (across the layers, conservative) | 1.97 | 2.0 |
| roll stop lug | abuse | F 481.3 N at r 17.5 mm; root 96 mm2, W 157 mm3, arm 10.3 mm (across the layers, conservative) | 0.60 | 1.2 |
| neck pad (TPU bearing) | service | F 147.7 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 4.06 | 2.0 |
| neck sheet back edge (in-plane bearing) | service | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 19.29 | 2.0 |
| neck pad pocket wall (the slide, across the layers) | service | 0.37 of F along the face = 55.3 N on the 6.0 x 2.5 mm pocket wall | 5.97 | 2.0 |
| neck pillar base (bending, across the layers) | service | M 4138 N mm on W 566 mm3 plus 62.4 N on 191 mm2 (the block prints standing: the base is a layer plane) | 2.88 | 2.0 |
| neck block screw F127 or F129 (pull-out, one screw) | service | tip moment 3545 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 241.2 N against 500 N est | 2.07 | 2.0 |
| neck pad (TPU bearing) | fall | F 295.5 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 2.03 | 1.2 |
| neck sheet back edge (in-plane bearing) | fall | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 9.64 | 1.2 |
| neck pad pocket wall (the slide, across the layers) | fall | 0.37 of F along the face = 110.5 N on the 6.0 x 2.5 mm pocket wall | 2.99 | 1.2 |
| neck pillar base (bending, across the layers) | fall | M 8276 N mm on W 566 mm3 plus 124.9 N on 191 mm2 (the block prints standing: the base is a layer plane) | 1.44 | 1.2 |
| neck block screw F127 or F129 (pull-out, one screw) | fall | tip moment 7090 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 482.3 N against 500 N est | 1.04 | 1.2 |
| neck pad (TPU bearing) | stall | F 53.5 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 11.22 | 2.0 |
| neck sheet back edge (in-plane bearing) | stall | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 53.31 | 2.0 |
| neck pad pocket wall (the slide, across the layers) | stall | 0.37 of F along the face = 20.0 N on the 6.0 x 2.5 mm pocket wall | 16.50 | 2.0 |
| neck pillar base (bending, across the layers) | stall | M 1497 N mm on W 566 mm3 plus 22.6 N on 191 mm2 (the block prints standing: the base is a layer plane) | 7.96 | 2.0 |
| neck block screw F127 or F129 (pull-out, one screw) | stall | tip moment 1283 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 87.3 N against 500 N est | 5.73 | 2.0 |
| neck pad (TPU bearing) | abuse | F 51.8 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 11.58 | 1.2 |
| neck sheet back edge (in-plane bearing) | abuse | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 55.01 | 1.2 |
| neck pad pocket wall (the slide, across the layers) | abuse | 0.37 of F along the face = 19.4 N on the 6.0 x 2.5 mm pocket wall | 17.03 | 1.2 |
| neck pillar base (bending, across the layers) | abuse | M 1451 N mm on W 566 mm3 plus 21.9 N on 191 mm2 (the block prints standing: the base is a layer plane) | 8.21 | 1.2 |
| neck block screw F127 or F129 (pull-out, one screw) | abuse | tip moment 1243 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 84.6 N against 500 N est | 5.91 | 1.2 |
| head pad (TPU bearing) | service | F 38.8 N at r 25.0 mm over 73 mm2 | 18.87 | 2.0 |
| neck sheet front edge (in-plane bearing) | service | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 91.79 | 2.0 |
| head pad pocket wall (the slide, across the layers) | service | 0.52 of F along the face = 20.3 N on the 6.1 x 2.5 mm pocket wall | 16.52 | 2.0 |
| head hook root face on the arm (shear across the layers, est) | service | the doubler's face on the arm, 132 mm2, carries M 1012 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 2.62 | 2.0 |
| yoke left arm with the doubler, level with the root (bending across the layers) | service | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 1086 N mm (lever 28.0 mm) | 6.53 | 2.0 |
| head hook foot plate at x 13 (bending, in the plate) | service | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 277 N mm (lever 7.1 mm); the plate prints flat | 30.07 | 2.0 |
| head pad (TPU bearing) | fall | F 77.6 N at r 25.0 mm over 73 mm2 | 9.44 | 1.2 |
| neck sheet front edge (in-plane bearing) | fall | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 45.90 | 1.2 |
| head pad pocket wall (the slide, across the layers) | fall | 0.52 of F along the face = 40.6 N on the 6.1 x 2.5 mm pocket wall | 8.26 | 1.2 |
| head hook root face on the arm (shear across the layers, est) | fall | the doubler's face on the arm, 132 mm2, carries M 2024 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 1.31 | 1.2 |
| yoke left arm with the doubler, level with the root (bending across the layers) | fall | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 2171 N mm (lever 28.0 mm) | 3.27 | 1.2 |
| head hook foot plate at x 13 (bending, in the plate) | fall | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 554 N mm (lever 7.1 mm); the plate prints flat | 15.04 | 1.2 |
| head pad (TPU bearing) | stall | F 81.2 N at r 25.0 mm over 73 mm2 | 9.01 | 2.0 |
| neck sheet front edge (in-plane bearing) | stall | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 43.84 | 2.0 |
| head pad pocket wall (the slide, across the layers) | stall | 0.52 of F along the face = 42.5 N on the 6.1 x 2.5 mm pocket wall | 7.89 | 2.0 |
| head hook root face on the arm (shear across the layers, est) | stall | the doubler's face on the arm, 132 mm2, carries M 2119 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 1.25 | 2.0 |
| yoke left arm with the doubler, level with the root (bending across the layers) | stall | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 2273 N mm (lever 28.0 mm) | 3.12 | 2.0 |
| head hook foot plate at x 13 (bending, in the plate) | stall | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 580 N mm (lever 7.1 mm); the plate prints flat | 14.36 | 2.0 |
| head pad (TPU bearing) | abuse | F 36.6 N at r 25.0 mm over 73 mm2 | 20.00 | 1.2 |
| neck sheet front edge (in-plane bearing) | abuse | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 97.31 | 1.2 |
| head pad pocket wall (the slide, across the layers) | abuse | 0.52 of F along the face = 19.2 N on the 6.1 x 2.5 mm pocket wall | 17.52 | 1.2 |
| head hook root face on the arm (shear across the layers, est) | abuse | the doubler's face on the arm, 132 mm2, carries M 955 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 2.78 | 1.2 |
| yoke left arm with the doubler, level with the root (bending across the layers) | abuse | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 1024 N mm (lever 28.0 mm) | 6.92 | 1.2 |
| head hook foot plate at x 13 (bending, in the plate) | abuse | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 261 N mm (lever 7.1 mm); the plate prints flat | 31.88 | 1.2 |
| head pad (TPU bearing) | shove | F 296.1 N at r 25.0 mm over 73 mm2 | 2.47 | 1.5 |
| neck sheet front edge (in-plane bearing) | head stop, 12 N shove forward on the head, torque off | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 12.02 | 1.5 |
| head pad pocket wall (the slide, across the layers) | head stop, 12 N shove forward on the head, torque off | 0.52 of F along the face = 155.0 N on the 6.1 x 2.5 mm pocket wall | 2.16 | 1.5 |
| head hook root face on the arm (shear across the layers, est) | head stop, 12 N shove forward on the head, torque off | the doubler's face on the arm, 132 mm2, carries M 7727 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 0.34 | 1.5 |
| yoke left arm with the doubler, level with the root (bending across the layers) | head stop, 12 N shove forward on the head, torque off | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 8288 N mm (lever 28.0 mm) | 0.86 | 1.5 |
| head hook foot plate at x 13 (bending, in the plate) | head stop, 12 N shove forward on the head, torque off | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 2114 N mm (lever 7.1 mm); the plate prints flat | 3.94 | 1.5 |
| head pad (TPU bearing) | shove | F 28.3 N at r 25.0 mm over 73 mm2 | 25.85 | 1.5 |
| neck sheet front edge (in-plane bearing) | head stop, 12 N shove forward on the head, torque on | the stock left sheet's 6.3 mm front edge over the 12 mm pad, the load in the sheet's plane | 125.76 | 1.5 |
| head pad pocket wall (the slide, across the layers) | head stop, 12 N shove forward on the head, torque on | 0.52 of F along the face = 14.8 N on the 6.1 x 2.5 mm pocket wall | 22.64 | 1.5 |
| head hook root face on the arm (shear across the layers, est) | head stop, 12 N shove forward on the head, torque on | the doubler's face on the arm, 132 mm2, carries M 739 N mm (lever 26.1 mm) in shear: Jp 4916 mm4, r 22.1 mm | 3.60 | 1.5 |
| yoke left arm with the doubler, level with the root (bending across the layers) | head stop, 12 N shove forward on the head, torque on | the composite section at z 159.9: net 118 mm2, W 357 mm3, M 792 N mm (lever 28.0 mm) | 8.95 | 1.5 |
| head hook foot plate at x 13 (bending, in the plate) | head stop, 12 N shove forward on the head, torque on | the 4 mm plate outboard of the sheet: 94 mm2, W 240 mm3, M 202 N mm (lever 7.1 mm); the plate prints flat | 41.20 | 1.5 |
| neck pad (TPU bearing) | neck stop, 12 N shove back on the head, torque off | F 43.2 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 13.89 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop, 12 N shove back on the head, torque off | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 65.98 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop, 12 N shove back on the head, torque off | 0.37 of F along the face = 16.2 N on the 6.0 x 2.5 mm pocket wall | 20.43 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop, 12 N shove back on the head, torque off | M 1210 N mm on W 566 mm3 plus 18.3 N on 191 mm2 (the block prints standing: the base is a layer plane) | 9.85 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop, 12 N shove back on the head, torque off | tip moment 1036 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 70.5 N against 500 N est | 7.09 | 1.5 |
| neck pad (TPU bearing) | neck stop, 12 N shove back on the head, torque on | F 226.7 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 2.65 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop, 12 N shove back on the head, torque on | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 12.57 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop, 12 N shove back on the head, torque on | 0.37 of F along the face = 84.8 N on the 6.0 x 2.5 mm pocket wall | 3.89 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop, 12 N shove back on the head, torque on | M 6350 N mm on W 566 mm3 plus 95.8 N on 191 mm2 (the block prints standing: the base is a layer plane) | 1.88 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop, 12 N shove back on the head, torque on | tip moment 5440 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 370.1 N against 500 N est | 1.35 | 1.5 |
| neck pad (TPU bearing) | neck stop at a servo stall (one face) | F 52.5 N on the 38.1 mm lever of the pad's normal (pad centre r 41.1) over 60 mm2 (one face) | 11.44 | 1.5 |
| neck sheet back edge (in-plane bearing) | neck stop at a servo stall (one face) | the stock sheet's 6.0 mm back edge over the 10 mm pad, the load in the sheet's plane | 54.32 | 1.5 |
| neck pad pocket wall (the slide, across the layers) | neck stop at a servo stall (one face) | 0.37 of F along the face = 19.6 N on the 6.0 x 2.5 mm pocket wall | 16.82 | 1.5 |
| neck pillar base (bending, across the layers) | neck stop at a servo stall (one face) | M 1470 N mm on W 566 mm3 plus 22.2 N on 191 mm2 (the block prints standing: the base is a layer plane) | 8.11 | 1.5 |
| neck block screw F127 or F129 (pull-out, one screw) | neck stop at a servo stall (one face) | tip moment 1259 N mm about the pillar's back edge (x -42.0), screw lever 14.7 mm: 85.6 N against 500 N est | 5.84 | 1.5 |

The joggled sheet itself is **BLOCKER** until the printed coupon test (TEST_PLAN.md 19.6).

## 5. Sim (sim pass only)

sit_sim.py on the repo model (sit_model.py: the Playground MJCF at b9be205, the masses of sim/mass_budget.py with the sit
parts, 2.806 kg (2.788 kg in the first pass), the URDF ranges, the software limits as actuator ranges, the repo meshes; the seat and the bumper collide
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

Nothing else of the test changed (the success rule, the seeds, the zero error model, the gain randomization). Peak
torques in the sit and stand on the final model: knee 1.73, neck 0.93, head pitch 0.80 N m (the first pass 1.72 / 0.93
/ 0.80). Every sim in this section and 5a was run again on the final model (sit_sim.json, sit_balance.json,
inputs key 0d016c83312deae5); the first pass's numbers are kept where they differ.

| Test | Study (A1b) | Repo model now |
|---|---|---|
| Push, torque off on the pads, 17 cases | 0 falls; 4 pads made at the end in 17 | **0 falls; 4 pads made at the end in 16 of 17** (first pass 17 of 17, drift up to 13.0 mm): the 12 N push from 8 directions in turn (8dirs_F12, an ABUSE case) ends 8.1 mm off its start with the CHG+ pad on one contact (the rule wants two or more on every pad), the charge would wait for a re-seat, not a fall; 5 cases lift a pad on the way and make it again; drift up to 16.0 mm; trunk pitch -0.6 to 2.8 deg |
| Head shove 12 N, 0.2 and 1.0 s, forward and back, torque off and on | - | the body held: 0 falls in 8; free: tips over in 8 of 8 (section 5a) |
| Stock walk, 10 seeds, forward 0.15 m/s | 0.0956 against 0.1004 m/s before the sit, 0 falls | **0.1001 against 0.1029 m/s** (first pass 0.0998), 0 and 0 falls |

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
| CoM inside the support, to the nearest edge | 75.9 mm (left sole - seat) | 75.5 mm (zero +1 deg left, -1 deg right) |
| Tip angle forward / back / left / right | 31.8 / 30.3 / 30.3 / 30.5 deg | 31.7 / 30.1 / 30.1 / 30.3 deg |
| Static push at head height that tips it (rigid robot, calc), 8 directions from forward | 8.2 / 11.7 / 10.9 / 7.8 / 7.9 / 7.9 / 11.2 / 11.6 N | 8.1 / 11.5 / 10.7 / 7.7 / 7.8 / 7.7 / 11.0 / 11.3 N |
| Sim push at the head CoM, ramped 2 N/s, torque off (neck and head free) | 4.4 / 4.9 / 8.9 / 6.5 / 6.4 / 6.6 / 7.3 / 5.0 N | 4.3 / 4.8 / 6.2 / 6.1 / 6.3 / 5.8 / 6.3 / 4.9 N |

(Final model, 2.806 kg, CoM 129.8 mm up at the sit; the first pass, 2.788 kg: nominal margin 76.0 mm, tips 32.2 / 30.4 /
30.4 / 30.6 deg, worst 74.9 mm and 29.7 deg, sim push 4.3 N forward at worst: the block and the hook moved nothing
that matters here.)

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
own loop check passes at 150 deg (D3 and SP4: free 22 to 29 mm, bend R 11.0 mm against 10.4); 6 more loops grown the same
way: S10 at the right knee, D4 and S9 at the right hip pitch, SP5 at the right hip yaw and roll, D1 and P13 at the head. Stick-on mounts on changed parts checked with the cables3d test (seats_ties.py: 5 x 5 rays, 0.4 mm,
15 deg, room above) and placed again with its search where the cuts or the lugs took the patch: T030, T035 and T044 take
the small ABM1M mount; T046, T047, T048 and T071 a tie round the bundle at the test fit (D25). check_cables.py and C3: PASS (0 FAIL).
Run again on the final CAD (2026-11-07): 58 cables pass, 43 with notes, every rub note the base already had (P13, D1 and
D2 touch head_pitch_to_yaw under head yaw at the full URDF range, -2.2 mm, on the right arm, the side without the hook;
SP3, D3, D4 and the dock cables as before). The neck stop block's first cut rubbed S2 and S7 by 1.2 mm where they come
up through the hip yaw servo cable windows in trunk_top and run back at y 30 to 33, z 82 to 89: the block now stops at
|y| 23.4 behind the windows (only the screw lobes reach y 29, in front of them), and no cable touches the block, the
neck pads, the hook or the head pad through the full URDF range. The trunk-side neck loops (P13, D1, D13, SD1) lie on
trunk_top at z 89 in the lane between the pillars (|y| under 15, the bar over them at z 100 to 108).
Still under 3 x OD: SP4 at hip pitch (as before the sit), and the neck loops (D1, D2, D3, P13, S11) by storage radius
only: the neck range is smaller now (+65 to +25 deg), so C3's loop length at the farthest pose is shorter; the cable is
not. Knee loop flex test to 150 deg: TEST_PLAN.md 19.7.

## 7. Print, mass, BOM

- Sliced again (slice.py parts --only, D22 light profile, PrusaSlicer 2.7.2, this box): print/SLICE_SUMMARY.md and
  PRINT_CHECK.md (sit_print.py). Robot set 47 STLs, 66 parts, 1354.0 g, 119.7 h (the first pass: 44 STLs, 62 parts,
  1333.5 g, 117.5 h); D59 adds 73.7 g of filament (TPU 39.4 g) and 8.6 h to the base set. The neck stop block is 14.8 g
  (5 walls 40 %, the neck profile), the hook adds 5.4 g to head_pitch_to_yaw (24.0 g), the three pads 1.0 g.
- Mass: 2806.4 g against 2749.0 g (+57.4 g; the first pass 2788.1 g; sim/MASS_BUDGET.md V1 sit section). More than 5 g
  moved, so the walk was run again (section 5).
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
- The neck stop block hangs on two M2x12 self-tapping screws (F127, F129) whose pull-out strength in the STS3215 case is
  not published: sit_stress.py takes 500 N (est) and the final model puts 482 N on one screw at the fall load (SF 1.04
  against 1.2) and 370 N at the 12 N back shove with the torque on (SF 1.35 against 1.5): the pull test of TEST_PLAN.md
  19.8 has to show 580 N or more, else a third screw or a longer flange; the two screws are in no bag or kit (BOM 17m;
  nothing bought).
- The head hook misses the 12 N forward shove with the torque off (7.4 N m by the energy method: root face SF 0.34, the
  arm with its doubler 0.86 against 1.5) and the stall (root 1.25 against 2.0); the torque-on rows pass. Fix proposed in
  section 4 (a taller root with a fillet, a 10 mm face, or a through-screw root), not built: calc only.
- The hip roll stop lug misses the energy loads (13.0 N m, 741 N at r 17.5 mm: SF 0.39 service, 0.20 fall, 0.60 abuse):
  it needs a TPU face and a doubled root, or a stop on the trunk side (section 4), not built: calc only.
- The get-up through the sit (D60, getup/GETUP_VIA_SIT.md, sim pass only) holds the hip pitch servos at their torque
  limit through its sit-up (3.14 N m at 7.2 V, 2.62 N m at 6.0 V) and the rise holds the neck at its limit; the thermal
  and stall margins of those holds are not checked (TEST_PLAN.md 19.9).
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
    python3 altaay_lab/print/slice.py parts --out <S>/slice --only <the 20 STLs>; python3 altaay_lab/twin/sit/sit_print.py --slice <S>/slice --write
    python3 altaay_lab/twin/sit/sit_cables.py --write; python3 altaay_lab/cables3d/route_cables.py --scratch <S>/c3d --grid-only; python3 altaay_lab/cables3d/check_cables.py --scratch <S>/c3d
    python3 altaay_lab/twin/sit/sit_model.py --out <S>/model; ODM_BEFORE_MODEL=<C8 'ours' model of the base> python3 altaay_lab/twin/sit/sit_sim.py --out <S>/model push|up|walk|summary
    python3 altaay_lab/twin/sit/sit_sim.py --out <S>/model up --seed0 100; ... shove; ... loads   held-out seeds, head shoves, stop loads
    python3 altaay_lab/twin/sit/sit_stress.py --sim <S>/model/sit_sim_loads.json,<S>/model/sit_sim_shove.json --model <S>/model/sit --write
    python3 altaay_lab/twin/sit/sit_pose.py --out <S>/model settle|check; python3 altaay_lab/twin/sit/sit_pose.py render --img <folder>
    python3 altaay_lab/twin/sit/sit_balance.py --out <S>/model --write                 the balance gate
