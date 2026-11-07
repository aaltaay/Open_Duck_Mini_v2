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
| neck_left/right_sheet | printed lugs onto the trunk top at neck pitch +25 deg (kept off the F233/F234 horn screw recess) | 0.46 and 0.37 cm3 |
| head_pitch_to_yaw | printed lug onto the neck at head pitch -25 deg, with a slot that keeps the F222 screw head and its hex key clear | 0.80 cm3 |
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
| neck pitch | -20 to 65 | -20 to **25** (neck lugs) | -17 to 22 | 1855 to 2298 |
| head pitch | -45 to 45 | **-25** (head lug) to 39 (head onto body_middle_top) | -22 to 36 | 1798 to 2458 |

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
  (hip pad onto the cache), neck +25 (lugs onto trunk_top), head -25 (lug onto the neck servo): 6 of 6.
- The A1b sit and stand path at 1 deg steps, both legs, the torque-off settle onto the stops and the calibration band
  (every leg joint +/-3 deg at the sit): 204 states, no new overlap.
- The stock walk envelope (VERIFICATION.md E9 'ours' ranges, corners with the inward roll and yaw): 32 states, no new
  overlap.
- Fasteners: sweep_fasteners.py over the new ranges (fasteners.json, FASTENERS.md): the screw-limited hits are the same 5
  screws as before (2 left out by D18, F198 and F211 from hip yaw 23.3 deg, F333 not fitted); the new ranges add "parts
  collide first" rows only. 20 records moved with the parts (sit_records.py: the 16 spacer screws and inserts, the 4
  heel screw and insert rows); the shin rows name the shin parts; the M2 clamp screws keep their seat.

## 4. Strength (calc)

sit_stress.py (sit_stress.json), STRUCTURE_TWIN.md allowables (PLA 47.1 MPa in-plane, 22 MPa across the layers; SF 2.0
service, 1.2 falls). Service is the largest stop torque the sims saw (sit_sim.py push and up) and the 1.57 N m knee
stand-up peak of the study; fall is 2 x service; stall is the servo pressing into its stop at stall torque (a calibration
error past the 3 deg margin).

| Item | Service SF | Fall SF | Stall SF |
|---|---|---|---|
| shin_spacer beam (knee bumper load, 1.57 N m at 24.1 mm) | 19.7 | 9.9 | 10.5 |
| shin sheet horn zone at the joggle (bending, 9 mm offset) | 8.2 | 4.5 | 4.8 |
| shin sheet neck, knee torque (STRUCTURE_TWIN FEA scale) | 6.0 | 3.0 | |
| spacer inserts sideways | 38 | 19 | 20 |
| ankle pads and their seats (bearing) | 79 | 40 | 16 |
| roll stop lug (0.96 N m) | 5.3 | 2.7 | 2.7 |
| neck stop lug (0.65 N m) | 2.8 | 1.4 | **0.95** |
| head stop lug (0.21 N m) | 37 | 19 | 4.0 |

Every service and fall case passes. Two findings:
- The neck lug cannot hold a stalled neck servo (SF 0.95 at 1.91 N m): the 3 deg software limit must hold, so the neck
  zero must be right to well under 3 deg (CALIBRATION.md); the lug's root is the neck sheet's edge (38 mm2) and cannot
  grow there without reaching the horn screw recess.
- Two push cases past the A1b tests (a 12 N shove from 8 sides; the sit sliding on a mat at mu 0.4) give limit impacts in
  the sim of 13.7 N m at the head pitch stop and 6.3 N m at a knee: the head lug's SF there is 0.56 (sim pass only and
  calc). A hard shove at the sitting duck can crack the head lug; a TPU face on it is the fix if the bench shows it.

The joggled sheet itself is **BLOCKER** until the printed coupon test (TEST_PLAN.md 19.6).

## 5. Sim (sim pass only)

sit_sim.py on the repo model (sit_model.py: the Playground MJCF at b9be205, the masses of sim/mass_budget.py with the sit
parts, 2.788 kg, the URDF ranges, the software limits as actuator ranges, the repo meshes; the seat and the bumper collide
with the floor). The SIT_V2 study ran a scratch copy (2.767 kg, the seat and bumper as capsules). sit_sim.json holds the
numbers.

| Test | Study (A1b) | Repo model now |
|---|---|---|
| Push, torque off on the pads, 17 cases | 0 falls; 4 pads made at the end in 17 | **0 falls; 4 pads made at the end in 16** (the power-off damping 0.05 case ends with CHG+ and SYS on 1 pin each); a pad lost on the way in 5 (8 and 12 N from 8 sides, damping 0.05, friction 0.02, mat mu 0.4); drift up to 16.6 mm (12 N); trunk pitch -0.7 to +2.8 deg |
| Stand up, 20 seeds: zero error 0 / 0.5 / 1.0 deg | 20 / 20 / 19 | **20 / 18 / 14** (at 1.0 deg 4 seeds fall back in the sit itself); the same 14 on the sheet torque limits |
| Peak torque in the sit and stand | knee 1.57, neck 0.88 N m | knee 1.57, neck 3.23 (the model limit, while the head swings up), head pitch 2.1 N m |
| Stock walk, 10 seeds, forward 0.15 m/s | 0.0956 against 0.1004 m/s before the sit, 0 falls | **0.0998 against 0.1029 m/s** (-3 %), turn 0.788 against 0.798 rad/s, 0 falls |

The push and walk results match the study's within a pad case and a few percent. The stand-up is more sensitive to zero
errors here than in the study: 18 of 20 at 0.5 deg (study 20) and 14 of 20 at 1.0 deg (study 19). Differences that
plausibly cause it (not separated by a run each): the printed seat and bumper are rounder at the back than the study's
capsules, the repo model is 21 g heavier and carries the joggled shins' mass further out, and the neck saturates at its
3.23 N m limit while the head swings up (0.88 N m in the study), which the head-forward waypoint feels. What follows:
the 0.5 deg calibration target of the brief is the least that works; aim at 0.25 deg (CALIBRATION.md step 3 spread), and
slow the neck in the last waypoint (Runtime sequence, not written yet).

## 6. Cables (CAD check only)

sit_cables.py from cables3d.json at the base: the route points and ties on the shin plates moved 9 mm with the joggle (6
ties, 6 cables); the knee loops grown by sliding the shin-side loop tie T034 along the cable until verify/c3_cables3d.py's
own loop check passes at 150 deg (D3 and SP4: free 22 to 29 mm, bend R 11.0 mm against 10.4); 6 more loops grown the same
way: S10 at the right knee, D4 and S9 at the right hip pitch, SP5 at the right hip yaw and roll, D1 and P13 at the head. Stick-on mounts on changed parts checked with the cables3d test (seats_ties.py: 5 x 5 rays, 0.4 mm,
15 deg, room above) and placed again with its search where the cuts or the lugs took the patch: T030, T035 and T044 take
the small ABM1M mount; T046, T047, T048 and T071 a tie round the bundle at the test fit (D25). check_cables.py and C3: PASS (0 FAIL).
Still under 3 x OD: SP4 at hip pitch (as before the sit), and the neck loops (D1, D2, D3, P13, S11) by storage radius
only: the neck range is smaller now (+65 to +25 deg), so C3's loop length at the farthest pose is shorter; the cable is
not. Knee loop flex test to 150 deg: TEST_PLAN.md 19.7.

## 7. Print, mass, BOM

- Sliced again (slice.py parts --only, D22 light profile, PrusaSlicer 2.7.2, this box): print/SLICE_SUMMARY.md and
  PRINT_CHECK.md (sit_print.py). Robot set 44 STLs, 62 parts, 1333.5 g, 117.5 h; D59 adds 46.1 g of filament (TPU 38.4 g)
  and 6.1 h.
- Mass: 2788.1 g against 2749.0 g (+39.1 g; sim/MASS_BUDGET.md V1 sit section).
- BOM: PLA need 1420 g (still 2 x 1 kg), TPU 73.5 g (1 x 1 kg), VHB 1.2 m (1 roll of 5 yd), stick-on mounts 27 MB3A and 24
  ABM1M (buy unchanged), no new screws (the moved screws are the same sizes). MOUNTING.md V1 sit section.

## 8. BLOCKERs

- Unpowered servo friction: the torque-off sit and the pushes lean on it; no datasheet value (TEST_PLAN.md 19.5).
- Calibration: the zero repeatability at the stops is not measured; the stand-up needs 0.5 deg or better, 0.25 deg to be
  sure (software/CALIBRATION.md, TEST_PLAN.md 19.3).
- Joggled sheet strength: the printed coupon test (TEST_PLAN.md 19.6); the hand checks pass but the web of a 3D print
  is not a beam.
- The sit and stand sequence in the Runtime is not written (the paths are in sitlib.PATH_A1B; the neck should move
  slower in the last waypoint, section 5).
- The neck lug cannot take a stalled servo (section 4); a hard shove at the sitting duck can crack the head lug.

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
    python3 altaay_lab/twin/sit/sit_stress.py --sim <S>/model/sit_sim_push.json,<S>/model/sit_sim_up.json --write
