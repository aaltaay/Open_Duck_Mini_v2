# GETUP_SIT: fall get-up with the A1b sit changes (PR 28)

_Copied into the repo from the read-only fall get-up retest (2026-11-07 ET, sim pass only). The code, runs.jsonl, static.json, probes and traces it names stayed in the scratch results folder, not in the repo._


Date 2026-11-07 (UTC on the box, about 03:55 to 05:00, with one container restart). Written by a Claude Code sub-agent for the duck lead. Read-only test job:
nothing was committed or pushed to either repo; the three worktrees made for it were removed at the end. Labels: **sim pass only** (MuJoCo in the
shared lab gym (overlay gym/overlays/duck)), **calc only** (program targets against limits, kinematics), **CAD check only** (exact-mesh contact sweep).
Nothing here is a hardware result.

## Answer

**No. With the sit PR's stops and software limits, Duckie does not get up after a fall with the stored programs: 0 of 296 cases
in sim (sim pass only), against 254 of 296 for the base model run the same way.** The 296 cases are the 74 library rest poses x
7.2 and 6.0 V x floor friction 1.0 and 0.6, each on the course where it fell (flat floor, obstacles, up and down ramps), STS3250
knees (D32), targets clamped to the angle-limit registers.

Two causes, each enough on its own (section 3):
1. **The designed neck back stop (+25 deg) and head forward stop (-25 deg).** The back program, which the side and front programs
   end in, pushes the head on the floor with the neck back at +61 deg and holds the bridge with the head tipped forward to
   -43 deg. The PR model with only these two stops put back to the base ranges (no software clamp) gets up in 258 of 296.
2. **The software limits at two CAD contacts** that the PR writes into servo_limits.json: knee -25.5 deg (the thigh cover meets
   the shin at -28.5) and ankle +46 (the shin meets foot_side at +49). The back program needs the knee at -88 and the ankle at +81.
   With the clamps on and the neck and head stops removed: 0 of 296; the knee clamp alone 0 of 174, the ankle clamp alone 0 of
   296. The head yaw clamp (-105 / +79 against the rolls' +-152 and +133) and the hip clamps change almost nothing: the rolls
   still roll.

Not causes: the +39 g (base with the sit masses: 257 of 296); the seat and the bumper (no rest pose changed, no load in any
roll, and with their collision off on the 72 front cases, the only runs where they touch the floor, the same 35 of 72 with no case
changed); the other new stops (knee 150, ankle -95, hip pitch -75, hip roll -8 outward: no program target passes them).

**The deeper finding (CAD check only):** the knee, ankle and head yaw contacts are not new. The base CAD at d6179ae has the same
knee contact at -28.5 deg, ankle contacts at +49.5 / -67 deg, head yaw contacts at -108 / +82 deg and a head-on-trunk contact at
neck +37.5 deg (head pitch 0). So the stored programs were never possible on the printed duck: the GETUP.md and KNEE_TWIN.md
successes rest on the Playground MJCF ranges (knee and ankle +-90 deg). The base model with its own CAD contacts as software
limits gets up in 0 of 296. The sit does not break a get-up that works on hardware; it adds two blockers (neck, head)
to three that were already there (GETUP.md section 9 had this as a BLOCKER: "Real joint stops ... until checked on the printed leg").

**Fix:** no program that respects the PR's limits was found (a quick fold-to-squat probe and two short searches; section 4).
Ranked by how little they touch the sit design: (1) a new back get-up inside the limits, software only, not found yet (BLOCKER;
the sit's own rise from a squat works in the shared lab gym (overlay gym/overlays/duck), so a fall-to-squat entry would complete it); (2) relieve the knee and ankle CAD
contacts and retune the neck and head into the sit stops: the retune failed, so not a fix yet; (3) move the neck stop to about +65
and the head stop to about -45, plus those reliefs and the head-on-trunk relief: restores the stored programs (64 of 76 on our rests;
258 of 296 with the base ranges) but removes the alert sit's head rest.

## 0. What was tested

| item | value | source |
|---|---|---|
| sit PR model | aaltaay/open_duck_mini_v2 claude/v1-sit at **758f2975631cbaa63edbe607ab8c4661d1c6f31d** (a detached worktree) | git |
| branch moved during the job | to b5843bf (the sit and stand path leans the trunk forward: sitlib.PATH_A1B; sit_sim.py, sit_stress.py), then to 740cbfa (sit_sweep.py records the swept path, sit_pose.json, sit_balance.json). Between 758f297 and 740cbfa these are byte-identical (git diff --quiet): software/servo_limits.json, mini_bdx/robots/open_duck_mini_v2/ (robot.urdf, robot.xml, every mesh), print/, sim/mass_budget.py, twin/sit/sit_model.py and twin/sit/SIT.md; sit_sweep.json keeps the same "stops" and "hard_stops". So the stop ranges, software limits, parts and masses did not change, the static check of section 1 is the same for b5843bf and 740cbfa (same inputs), and every sim number here was run on 758f297 | git |
| base model | origin/altaay-lab at **d6179ae452def94f8ad46dfcc58cb4e3d8095ae6** (PR 27 merged; worktree the scratch results folder (not in the repo)) | git |
| the shared lab gym (overlay gym/overlays/duck) | the shared lab gym (overlay gym/overlays/duck) at **961a5b4496409a2ace04df81cba2ab66b37f3de8** (a detached worktree) | git |
| programs | the stored GETUP programs: back_final.json (r7, family back), side_final.json (r10, family side), front_final.json (r9, family front_roll); also back_v72.json (r5) in the static check | GETUP.md section 10; copies of the 2026-11-03 scratch files |
| fall library | the 74 rest poses of falls/poses.json (back 39, side 17, front 18; both masses' falls) | GETUP.md section 2 |

**Models** (all in the shared lab gym (overlay gym/overlays/duck) get-up pipeline: the collision duck of getup/getup_robot.py with its 38 shell geoms and self-collision,
frozen physics floor_v1 at 1 ms, servos at the supply voltage, BAM mode; code in code/sitgym.py):
- **base**: the Playground MJCF ranges and meshes, per-body inertials from the base worktree's sim/mass_budget.py build_budget()
  (2.749 kg; the shared lab gym (overlay gym/overlays/duck)'s own 'ours' is 2.6528 kg from an older budget, duck_inertials.json).
- **sit**: the model altaay_lab/twin/sit/sit_model.py writes from the PR (run read-only into scratch): robot.urdf hard stops as
  joint ranges with the compliant stop stiffness of sitlib.STOP_STACK, software/servo_limits.json as actuator ctrlrange, the repo
  meshes of the 19 changed or new parts, seat and bumper colliding with the floor, sit masses 2.7881 kg (SIT.md section 7:
  2788.1 g). the shared lab gym (overlay gym/overlays/duck) shells add the joggled shin sheets and the longer shin spacer.
- Both get the STS3250 knees as KNEE_TWIN.md section 4 ran them (v1_knee/knee_swap.py prepare(), "sts3250_high", +19.5 g each):
  2.788 kg base, 2.827 kg sit. The C001 knees as a check (section 2.4).
- **Clamp**: every 20 ms the target (program plus the ankle IMU loop) is clipped to ctrlrange before it is sent, and MuJoCo clamps
  it again: the angle-limit registers 9 and 11 clamp a goal the same way (servo_limits.json "registers").
- **Start**: each library rest pose, joints clipped into the model's joint range (none needed it), lifted if it penetrates (28
  ramp_10_down cases by 0.5 mm, the same on both models), then re-settled on the model with the servos holding the fall targets
  (clamped) until at rest (falls.py rule), at the case's voltage and friction. Then the stored program, the GETUP success rule
  (upright and still 2 s on the soles only, no joint more than 1 deg past its range).

Check of the pipeline: the shared lab gym (overlay gym/overlays/duck)'s own model with C001 knees reproduces GETUP.md on the reference case (stand_push_back ours,
7.2 V: up at 10.32 s, as back_final.json records). Over our build's 38 rests at mu 1.0 and 0.6, both voltages, the shared lab gym (overlay gym/overlays/duck) 'ours' model with C001 knees gets back 76 of 76 and side 40
of 40 (GETUP.md section 5: 19 of 19 and 10 of 10 in every one of these four conditions) and front 18 of 36 (GETUP.md: 13 of 36; the
re-settle of each start at the case's voltage and friction moves a few front ramp cases). The base model with STS3250 knees on the
same 38 rests at mu 1.0: back 19 of 19 at 7.2 V and 17 of 19 at 6.0 V (ramp_5_up s2 and ramp_10_up s1 miss), side 10 of 10 and
9 of 10; KNEE_TWIN.md section 4 has back 19 and 17 (ramp_10_up and ramp_20_up miss) and side 10 and 10 on the shared lab gym (overlay gym/overlays/duck)'s 2.6528 kg model.

## 1. Static check (calc only)

code/static_check.py, output static.json. Every stored program's commanded targets at 50 Hz (open loop; the ankle IMU loop adds up
to +-0.35 rad to both ankles from the bridge on, listed apart), from every library rest pose of its class, against:
- the six designed stops (sitlib.STOPS; right side mirrored for hip roll and hip pitch),
- every hard stop of servo_limits.json (the designed ones plus the CAD contacts of sit_sweep.py hard_stops),
- the software limits (3 deg inside each hard stop).

Phases (back program, GETUP.md section 4): B1 knees swing back (0.65 s), B2 neck and head set (1.06 s), B3 head push (0.69 s),
B4 throw (0.15 s), B5 into the bridge (0.31 s), B6 bridge hold (0.4 s), B7 head to neutral (0.8 s), B8 stance chain to standing,
B9 final stand. Side: S1 head yaw pre-set, S2 head yaw swing (the roll), S3 yaw back to 0, then B1 to B9. Front: F1 set neck,
head and legs, F2 yaw to +133, F3 swing to -88 (the roll), F4 yaw back, then B1 to B9.

**Violations** (left joint shown; the right is the same by mirror; deg past the limit at worst, time outside the limit, phases;
every pose of the class has it unless the pose count says less):

| program | joint | limit (what it is) | worst past it | time outside | phases | poses |
|---|---|---|---|---|---|---|
| back (39 poses) | neck pitch | **+25 designed stop** (neck lugs); program +61 | 35.9 deg | 1.68 s | B2, B3, B4, B5 | 39 |
| back | head pitch | **-25 designed stop** (head lug); program -43 | 18.0 deg | 1.56 s | B2 to B7 | 39 |
| back | knee | -28.5 hard (CAD: cache onto shin); program -88 | 59.5 deg | 5.80 s | B1 to B8 | 39 |
| back | ankle | +49 hard (CAD: shin onto foot_side); program up to +80.7 | 31.7 deg | 3.56 s | B4 to B8 | 39 |
| back | knee | software -25.5 | 62.5 deg | 5.86 s | B1 to B8 | 39 |
| back | ankle | software +46 | 34.7 deg | 3.66 s | B4 to B8 | 39 |
| back | neck pitch | software +22 (and -17: the bridge head at -18) | 38.9 deg | 2.62 s | B1 to B7 | 39 |
| back | head pitch | software -22 | 21.0 deg | 1.72 s | B2 to B7 | 39 |
| side (17 poses) | all of the back program's rows above | same | same | same | B1 to B8 | 17 |
| side | head yaw | -108 / +82 hard (CAD: head_pitch_to_yaw onto the yaw servo); program +-152 | 70.2 deg (right side down, +152) | 0.28 to 0.38 s | S2, S3 | 17 |
| side | head yaw | software -105 / +79 | 73.2 deg | 0.30 to 0.38 s | S2, S3 | 17 |
| side | hip roll | software -5 / +5 (outward) | 0.7 to 1.2 deg | 1.52 to 1.62 s | S1 to B1 (the legs are held at the rest pose) | 5 |
| front (18 poses) | all of the back program's rows above | same | same | same | B1 to B8 | 18 |
| front | head yaw | +82 hard (CAD); program +133 | 50.6 deg | 0.54 s | F2, F3 | 18 |
| front | head yaw | software +79 | 53.6 deg | 0.56 s | F2, F3 | 18 |
| front | neck pitch | software -17 (program -18 in F1 to F4) | 1.0 deg | 5.36 to 5.44 s (with the back rows) | F1 to F4 | 18 |
| front | hip roll | software -5 / +5 (rest pose) | 1.8 to 2.0 deg | 0.10 to 0.14 s | F1 | 3 |

back_v72.json (r5, the 7.2 V variant of GETUP.md option A): the same rows (neck 34.8 deg past +25 for 2.44 to 2.48 s, head 18.0
past -25, knee 59.5 past -28.5, ankle 31.7 past +49).

Within the limits: the knee fold stop (150; the program targets bend the knee forward to +78 at most, the base sim reaches +85),
the ankle sit stop (-95; targets down to -45, the base sim reaches -61), the hip pitch back stop (-75; the chain targets -70), the hip roll outward stop (-8; no target past it, the outward
software limit -5 is passed by 0.7 to 2.0 deg only where a program holds a rest pose's hip roll), hip yaw and head roll.

**Rest poses** (calc only): no library rest pose has a joint past a hard stop. 8 are past the hip roll software limit (outward,
by up to 2.0 deg: ramp_10_down ours s3 -6.8 deg, ramp_20_down stock s2 +7.0 deg), inside the -8 stop. Seat and bumper clearance to
the floor at the 74 library rest poses (sit model kinematics, mj_geomDistance): back rests seat 26.0 mm at least (median 33.3),
bumper 141 mm or more; side rests seat 48 mm, bumper 108 mm; front rests bumper 3.1 mm at least (median 14.1), seat 123 mm.
Nothing touches at rest.

**What the sim showed of the same programs on the base model** (sim pass only, all 296 base runs, actual joint angles): knee to
-91, ankle to +91, neck to +59, head pitch to -46, head yaw -95 to +117, left hip roll to -8.

### 1.1 The CAD contacts are on the base too (CAD check only)

code/cad_base_stops.py runs the sit branch's own sit_sweep.hard_stops() (exact meshes, manifold3d; each joint moved alone from the
zero pose, 2 deg steps then 0.5 deg back) on sitlib.scene_base(): robot.urdf and every print/ STL as at d6179ae. Output
cad_base_stops.json; the sit side is the branch's sit_sweep.json.

| joint | base CAD (d6179ae) first contact | sit CAD (758f297) | stored programs need |
|---|---|---|---|
| knee | **-28.5** (left_cache onto leg_spacer); no contact up to +90 | -28.5 (cache onto shin_left_sheet); +118.5 at ankle 0 (coupled, SIT.md section 2) | -88 (B1 to B8) |
| ankle | **-67** and **+49.5** (knee_to_ankle sheet onto foot_top) | +49 (shin onto foot_side); -95 designed | +81 (B8), -61 |
| neck pitch | **+37.5** (body_back onto head_bot_sheet, head pitch 0) | swept only to the +25 stop | +61 (B3, head -3) |
| head pitch | +39 (body_middle_top onto head) | +39; -25 designed | -43 (B5 to B7) |
| head yaw | **-108 / +82** (head_pitch_to_yaw onto servo_bottom) | -108 / +82 | +-152 (side), +133 (front) |
| hip pitch (left) | +13.5 (servo_mid onto leg_spacer) | +13.5; -75 designed | -70 to -24 |
| hip yaw (left) | -24 / +24.5 | -24 / +24.5 (+23.3 screw first) | 0.1 |

Single-joint sweeps from the zero pose: a pose-dependent contact (the neck one, which moves with head pitch) can sit a few degrees
elsewhere in the program's pose. The knee, ankle and head yaw contacts are between parts on the two sides of that joint only, so
they hold in any pose.

## 2. Sim retest (sim pass only)

### 2.1 Before and after

Every rest pose of the library on its own course, STS3250 knees, targets clamped (sim pass only; runs.jsonl):

| pose class (rest poses) | V | floor mu | base d6179ae | sit 758f297 |
|---|---|---|---|---|
| back (39) | 7.2 | 1.0 | 39 of 39 | 0 of 39 |
| back (39) | 7.2 | 0.6 | 39 of 39 | 0 of 39 |
| back (39) | 6 | 1.0 | 35 of 39 | 0 of 39 |
| back (39) | 6 | 0.6 | 39 of 39 | 0 of 39 |
| side (17) | 7.2 | 1.0 | 17 of 17 | 0 of 17 |
| side (17) | 7.2 | 0.6 | 17 of 17 | 0 of 17 |
| side (17) | 6 | 1.0 | 16 of 17 | 0 of 17 |
| side (17) | 6 | 0.6 | 17 of 17 | 0 of 17 |
| front (18) | 7.2 | 1.0 | 11 of 18 | 0 of 18 |
| front (18) | 7.2 | 0.6 | 8 of 18 | 0 of 18 |
| front (18) | 6 | 1.0 | 5 of 18 | 0 of 18 |
| front (18) | 6 | 0.6 | 11 of 18 | 0 of 18 |
| **all** | both | both | **254 of 296** | **0 of 296** |

Split by terrain (base -> sit, of the cases in the cell; flat = duck/arena, push_arena, duck/ice; obstacles = bumps, thresholds,
duck/edge_3mm; ramps up = ramp_5_up, ramp_10_up, ramp_20_up; ramps down = ramp_10_down, ramp_20_down):

| class, terrain (rest poses) | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 |
|---|---|---|---|---|
| back, flat (12) | 12 -> 0 of 12 | 12 -> 0 of 12 | 12 -> 0 of 12 | 12 -> 0 of 12 |
| back, obstacles (12) | 12 -> 0 of 12 | 12 -> 0 of 12 | 11 -> 0 of 12 | 12 -> 0 of 12 |
| back, ramps up (15) | 15 -> 0 of 15 | 15 -> 0 of 15 | 12 -> 0 of 15 | 15 -> 0 of 15 |
| side, flat (10) | 10 -> 0 of 10 | 10 -> 0 of 10 | 9 -> 0 of 10 | 10 -> 0 of 10 |
| side, obstacles (4) | 4 -> 0 of 4 | 4 -> 0 of 4 | 4 -> 0 of 4 | 4 -> 0 of 4 |
| side, ramps up (3) | 3 -> 0 of 3 | 3 -> 0 of 3 | 3 -> 0 of 3 | 3 -> 0 of 3 |
| front, flat (6) | 6 -> 0 of 6 | 6 -> 0 of 6 | 5 -> 0 of 6 | 6 -> 0 of 6 |
| front, ramps down (12) | 5 -> 0 of 12 | 2 -> 0 of 12 | 0 -> 0 of 12 | 5 -> 0 of 12 |

Baselines in the brief, for comparison (they used the shared lab gym (overlay gym/overlays/duck)'s 2.6528 kg 'ours' model and only our build's 38 rest poses):
GETUP.md section 5 (C001): back 114 of 114 and side 60 of 60 over six conditions, front 22 of 54. KNEE_TWIN.md section 4
(STS3250, mu 1.0): back 19 of 19 at 7.2 V, 17 of 19 at 6.0 V (ramp_10_up and ramp_20_up fail), side 10 of 10. The base model here
has the same weak corner, 6.0 V on mu 1.0: 35 of 39 back poses (misses bumps stock s2, ramp_5_up stock s2 and ours s2, ramp_10_up
ours s1; all lie back at 109 deg at the end, the throw falls short) and 16 of 17 side (push_series ours s2).

How the sit runs end: every back and side run lies on its back at the end (tilt 109 to 111 deg, best tilt median 97 and 93): the
throw never lifts the trunk. The side roll still turns the duck onto its back in 68 of 68, the front roll in 55 of 72 (base 59 of
72; section 2.3). The front runs end on the back (median tilt 110) or, on the down ramps, on the front.

### 2.2 What each change does (ablations, same 296 cases)

| set | what changes | back | side | front | all | cases |
|---|---|---|---|---|---|---|
| base_sts3250_high | base model (d6179ae), STS3250 knees | 152 of 156 | 67 of 68 | 35 of 72 | 254 of 296 | all 296 |
| base_sitmass_sts3250_high | base + the sit masses (+39.1 g): mass alone | 156 of 156 | 68 of 68 | 33 of 72 | 257 of 296 | all 296 |
| base_cad_sts3250_high | base + its own CAD contacts as software limits (3 deg inside) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_noclamp+nhfree_sts3250_high | sit, no software clamp, neck and head stops at the base ranges | 155 of 156 | 68 of 68 | 35 of 72 | 258 of 296 | all 296 |
| sit_noclamp_sts3250_high | sit, no software clamp (designed stops only) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit+nhfree_sts3250_high | sit, software clamp, neck and head stops at the base ranges (CAD clamps only) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_clamp-ankle+nhfree_sts3250_high | as above, ankle clamp only | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_clamp-knee+nhfree_sts3250_high | as above, knee clamp only | 0 of 100 | 0 of 44 | 0 of 30 | 0 of 174 | our build's 38 rests at mu 1.0, both V, plus 98 others (a first full run cut by the restart) |
| sit_clamp-yaw+nhfree_sts3250_high | as above, head yaw clamp only | 84 of 84 | 36 of 36 | 18 of 39 | 138 of 159 | 159 of the 296 (cut by the restart); without the clamp the same 159: 139 |
| sit_clamp-hip+nhfree_sts3250_high | as above, hip clamps only | 37 of 38 | 20 of 20 | 9 of 18 | 66 of 76 | our build's 38 rests, mu 1.0, both V |
| sit_noclamp+nhfree+noparts_sts3250_high | sit, no clamp, neck and head free, seat and bumper collision off | 4 of 4 | not run | 35 of 72 | 39 of 76 | the 72 front cases (+4 back); without the change the same 35 of 72 |
| sit_sts3250_high | **sit PR model as built (all of it)** | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| gym_ours_c001 | the shared lab gym (overlay gym/overlays/duck) 'ours' model (2.6528 kg), C001 knees: the GETUP.md reference | 76 of 76 | 40 of 40 | 18 of 36 | 134 of 152 | our build's 38 rests, mu 1.0 and 0.6, both V |
| sit_c001 | sit PR model, C001 knees | 0 of 38 | 0 of 20 | 0 of 18 | 0 of 76 | our build's 38 rests, mu 1.0, both V |


Moved-stop sensitivity (the neck back stop and the head forward stop moved, the software limit 3 deg inside each; knee, ankle and
head yaw at the URDF ranges, i.e. the CAD contacts relieved; our build's 38 rests, mu 1.0, 7.2 and 6.0 V; same 76 cases: base
63, the sit with no clamp and both stops at the base ranges 66):

| neck back stop | head forward stop | success |
|---|---|---|
| +65 (base range) | -45 (base range) | 64 of 76 |
| +45 | -45 | 7 of 76 |
| +37.5 (the base CAD's head-on-trunk contact) | -45 | 0 of 76 |
| +25 (PR) | -25 (PR) | 0 of 76 (sit_noclamp, no software clamp) |
| +65 | -35 | 33 of 76 |
| +65 | -30 | 0 of 76 |

Retune inside the sit's neck and head limits (retune_cma.py, probes/retune_nh1*): CMA-ES over the back program's 27 values plus
the bridge head (programs.HEAD_C), the neck kept in -17..22 and the head in -22..36 deg, on the PR model with only the neck and
head clamped, 8 back cases (both masses' rests, 7.2 and 6.0 V, mu 1.0 and 0.6), population 12, sigma 0.08. The stored program
clipped into the limits scores 4.14 of 10 (0 of 8 up); after 10 generations (stopped by the container restart at 10 of 12) the
best is 4.73, 0 of 8 up in every generation. No retune inside the neck and head stops was found.

### 2.3 Rest poses, rolls and contact (sim pass only)

- **Rest poses:** re-settled on the sit model, all 296 starts keep their class; the tilt at rest moves by 0.4 deg at most (median
  0.02); neither the seat nor the bumper touches the floor at rest in any case. The seat and bumper do not change the rest poses.
- **Rolls:** the side roll puts the duck on its back in 68 of 68 on base and sit alike; the seat and bumper carry no load in any
  roll (0 N in every run). The front roll: 59 of 72 base, 59 of 72 with the designed stops only, 58 of 72 with the CAD clamps
  (head yaw clamped to +79), 55 of 72 with the full PR; all misses are ramp_20_down rests. So the software clamp (head yaw, and the neck held at -17 instead of
  -18 in F1) costs at most 4 front rolls, all on the 20 deg down ramp, and the parts block no roll.
- **Bumper loads:** after a failed roll or throw on the down ramps the duck drops nose first onto the belly bumper: peaks of 290 N (sit)
  and 331 N (sit, no clamp) in 10 and 11 front runs, all on ramp_10_down or ramp_20_down, at the shared lab gym (overlay gym/overlays/duck)'s soft default contact
  (solref 0.02). The seat never touched the floor in a sit run with the clamp. The seat and bumper against the robot's own shells (sit_selfseat) was not run (restart, time).
- **The shared lab gym (overlay gym/overlays/duck) collision model and the sit:** the shared lab gym (overlay gym/overlays/duck) collides each shell as its convex hull. The cut thigh cover (left_cache, right_cache)
  hull fills the cut, so in the shared lab gym (overlay gym/overlays/duck) the A1b fold stops at knee 132.6 deg against the foot hull (target 147). The sit's exact-mesh
  sweep has it clear (SIT.md section 3). This does not touch the stored programs (knee at most +85) but it does matter for any
  get-up through the sit (section 4): with the cache hulls out of self-collision, the sit branch's own sit-down and rise path
  (sit_sim.py DOWN, SIT, UP, STAND) stands up in the shared lab gym (overlay gym/overlays/duck) from a squat 4 of 4 (7.2 and 6.0 V, mu 1.0 and 0.6), then reaches the
  walk's home key; with them in, 0 of 4 (it tips back from pitch -27 deg).

### 2.4 Knees, mass, reproduction

- C001 against STS3250: the PR model with C001 knees: 0 of 76 (our 38 rests, mu 1.0, both V), as with STS3250. The knee servo
  type does not change the answer. The base model with C001 knees was not run (time).
- Mass: section 2.2 (base_sitmass 257 of 296 against 254).
- Reproduction of the earlier numbers: section 0.

### 2.5 The front program's ValueError (root cause, not fixed)

v1_knee/knee_runs.py getup_job (lines 165 and 166) loads opt/front_final.json and takes `famname = J.get("family", fam)`. The file
has no "family" key (its keys: score, succ, n, x, gen, names, details), so the family falls back to the file prefix, "front".
But front_final.json is the r9 **front_roll** program (it is front_roll_r9_best.json: same x, same names ["n", "hp", "f", "k",
"T0", "yaw1", "T1", "yaw2", "T2", "T3"], gen 9; GETUP.md line 401 calls it "front roll (family front_roll)"). FAMILIES["front"]
is the r1 squat family (19 values: 3 keyframes x 6 + Tp); its builder _front_build (getup/optimize.py line 30) unpacks
`f, k, a, n, hp, T = x[6 * i:6 * i + 6]`, and for i = 1 the 10-value vector gives 4 values: `ValueError: not enough values to
unpack (expected 6, got 4)`. Reproduced here. The same happens in both knee runs because it is the file, not the model. Fix (not
applied): map front to "front_roll" in getup_job, or write "family" into the stored best files (optimize.py run() does not). The
runs here build front with the front_roll family, so the front program loads and runs.

## 3. The failures the sit causes, and their causes

Every failure of the PR model (296 of 296) has the same immediate cause: the back program's throw never happens, so the duck
stays on its back (the side and front programs roll onto the back first and then run the same back program; their rolls still
work, section 2.3). Ablations on the same cases (section 2.2) split it as follows. Each of the first three is enough alone.

| # | cause | kind | evidence (sim pass only unless marked) | caused by the sit? |
|---|---|---|---|---|
| 1 | **neck back stop +25 deg** (neck lugs onto trunk_top). B3 needs +61 (the head pushes on the floor and tips the trunk toward level); B2 +34; B4 +50 | designed stop | PR model with no software clamp: 0 of 296; the same with the neck and head stops back at the base ranges: 258 of 296 (base 254). Neck stop moved, head at -45 (our 38 rests, mu 1.0, both V): at +65 64 of 76, +45 7 of 76, +37.5 0 of 76 | **yes**, new with the sit |
| 2 | **head forward stop -25 deg** (head lug onto the neck). B5 to B7 hold the bridge with the head at -43 (programs.HEAD_C, so the CoM sits over the feet), B2 and B4 -31 | designed stop | together with 1 in the 0 of 296 above; head stop moved with the neck at +65: -45 64 of 76, -35 33 of 76, -30 0 of 76 | **yes**, new with the sit |
| 3 | **knee software limit -25.5** (CAD contact -28.5: thigh cover onto the shin spacer). B1 to B8 need -41 to -88 (the backward bridge) | software clamp at a CAD contact | knee clamp alone (neck and head free): 0 of 123 | the clamp is new (servo_limits.json); the contact is on the base CAD too (section 1.1) |
| 4 | **ankle software limit +46** (CAD contact +49: shin onto foot_side). B4 to B8 need +54 to +81 (the bridge stance on the toes) | software clamp at a CAD contact | ankle clamp alone: 0 of 296 | the clamp is new; the base CAD contact is +49.5 |
| 5 | head yaw software limits -105 / +79 (CAD -108 / +82). The side swing needs +-152, the front +133 | software clamp at a CAD contact | yaw clamp alone: 138 of 159 against 139 of the same 159 without it (lost 2, won 1, all ramp_20_down); the side roll still rolls 36 of 36 | not a cause in sim: the rolls work with 79 / 105 deg of yaw |
| 6 | hip software limits (hip yaw -21 / +20.3, hip roll outward -5, hip pitch +10.5) | software clamp | hip clamps alone (our 38 rests, mu 1.0): 66 of 76, the same 66 as without them (no case changes) | no |
| 7 | +39 g (2.7881 against 2.749 kg, plus the two STS3250 knees on both) | mass | base with the sit masses: 257 of 296 (base 254; lost 6, won 9, all on ramp_20_down or at 6.0 V) | no |
| 8 | seat and bumper | parts, contact | no rest pose changed, no load in any roll; designed stops removed, parts on: 258 of 296; seat and bumper collision off on the 72 front cases (the only runs where they touch): the same 35 of 72, no case changes | no |

The base itself (CAD check only plus sim pass only): with its own CAD contacts as software limits (knee -25.5, ankle -64 / +46.5,
neck +34.5, head pitch +36, head yaw -105 / +79, hip pitch +10.5, 3 deg inside each contact as D59 does), the base model gets up
in 0 of 296. Causes 3 and 4 are therefore not caused by the sit: they come from the base CAD, which the stored programs
never respected because the shared lab gym (overlay gym/overlays/duck) model's knee and ankle ranges are the Playground's +-90 deg. The sit's own contribution is causes 1
and 2, and the fact that it writes 3 to 5 into the servos (which is right: the knee and ankle cases would otherwise be driven into
the cache and the foot).

## 4. Fixes, ranked by how little they touch the sit design

Ranked from the least to the most change to the sit design. "Works" means in sim (sim pass only) on the cases named.

| rank | fix | touches | what it needs | status |
|---|---|---|---|---|
| 1 | **A new get-up program inside the PR's software limits** (software only) | nothing | a strategy that does not bend the knees backward: the stored back bridge needs the knees at -88 deg and the knee stops at -28.5 in both CADs (GETUP.md section 3: lying back, the soles reach flat under the trunk only with the knees bent backward), and the throw needs the neck at +61 and the head at -43. The sit gives new forward ranges (knee fold to +147, ankle to -92, hip pitch to -72) and a tested rise from the squat (below) | **not found: BLOCKER.** Tried: a direct fold to the squat from the 38 rests of our build, 0 of 38 (the trunk stays at its rest pitch: back -116 to -120, front +67 to +87 deg nose down); a 4-generation CMA-ES of two free keyframes into the squat from 4 front rests, 0 (pitch at the squat stuck at 63 deg nose down; probes/vsit_*) |
| 2 | Relieve the knee and ankle CAD contacts, and retune the program's neck and head use into the sit's stops | the thigh covers (left_cache, right_cache) and the shin spacer for the knee to about -91; the shin sheets and foot_side for the ankle to about +94 (the program's +81 plus the ankle IMU loop: +91 in the base sim); the designed stops stay | a back program that gets up with neck at most +22 and head at least -22 | **does not work yet:** the retune inside the neck and head limits found 0 of 8 in 10 generations (section 2.2). Knee and ankle relief alone: 0 of 296 while the neck and head stops stay (sit_noclamp) |
| 3 | Move the sit's neck back stop to about +65 and its head forward stop to about -45, plus the reliefs of 2 and of the head-on-trunk contact | the neck lugs and the head lug (the alert sit's torque-off head rest), body_back or head_bot_sheet for the neck past +61 (base CAD contact +37.5 at head pitch 0), and the parts of 2 | the stored programs as they are | **works for the stored programs:** 64 of 76 (our rests, mu 1.0, both V) at +65 / -45; with the stops at the base ranges and no clamp on all 296 cases 258 of 296 (base 254). Smaller moves fail: +45 7 of 76, +37.5 0, head -35 33 of 76, -30 0. It undoes the A1b head rest and cuts four printed parts |

Not needed: any head yaw change (the side roll rolls 36 of 36 with the yaw clamped to -105 / +79, the front roll 34 of 39 against 33
of the same 39 without the clamp), any hip change (hip clamps alone change no case), anything for the seat, the bumper or the mass.

Proposal 1 is the one to work on. What is in hand for it: the sit branch's own rise path (sit_sim.py UP and STAND, then the walk's
home key) stands the duck up in the shared lab gym (overlay gym/overlays/duck) physics from a torque-on squat 4 of 4 (7.2 and 6.0 V, mu 1.0 and 0.6; probes/
sit_rise_check_sit_xcache.json) once the cut thigh-cover hulls are out of self-collision (with them in: 0 of 4, the fold stops at
knee 132.6 deg on the hull). So a fall-to-squat entry, if one exists, would complete a get-up that respects every PR limit; finding
it needs a longer search than this job ran (or a learned get-up policy, GETUP.md section 8, now with the real ranges). The other
route the stored programs used, the side and front rolls onto the back, still works under the PR limits (section 2.3), so only the
back get-up itself is missing.

## 5. BLOCKERs

- **No get-up program exists for the PR's limits** (and none for the base CAD's either). Section 4, fix 1. Until one is found and
  verified, the robot as designed cannot get up after a fall in sim. Needs a real search (or a learned policy) for a strategy that
  does not use the backward knee.
- **Real joint stops on the printed parts:** the knee -28.5, ankle +49.5 / -67, neck +37.5 (head pitch 0) and head yaw -108 / +82
  contacts are CAD check only (single-joint sweeps from the zero pose, the sit branch's sweep code); nobody has bent a printed leg
  or neck to them. They replace GETUP.md section 9's first BLOCKER, but they need the printed-part check too.
- **The shared lab gym (overlay gym/overlays/duck) collision model for anything that folds through the sit:** convex hulls of the cut thigh covers fill the cuts (section
  2.3). A get-up that passes through the A1b fold needs the exact meshes or a decomposition of the cut covers; I took the cache
  hulls out of self-collision for the probes, which is optimistic where the cover really meets the foot.
- **The sit branch's stand-up in the shared lab gym (overlay gym/overlays/duck):** sit_sim.py runs the sit and rise on its own scene (soles, seat, bumper colliding;
  pin forces on the dock pads). In the shared lab gym (overlay gym/overlays/duck) get-up physics the rise works from a squat only with the cache hulls out (4 of 4); not
  checked from the torque-off sit on the seat (my squat had the seat and bumper unloaded).
- **Servo goal clamping:** modelled as the angle-limit registers clipping the goal (servo_limits.json "registers"); the firmware's
  own behaviour at a goal outside the limits is not measured here (the bench check is set_angle_limits.py's, SIT.md section 2).
- The electromech twin's BLOCKER 1 (does the firmware compensate bus voltage) still stands for every 6.0 V number (GETUP.md
  section 9).
- Shell contact model (coarse hulls, PLA friction taken as the shared lab gym (overlay gym/overlays/duck) floor value), as GETUP.md section 9.
- Not run because of the container restart and time: the seat and bumper with self-contact (sit_selfseat), the base model with
  C001 knees, and generations 10 and 11 of the neck and head retune. The head forward stop at -40 and the neck stop at +55 were not run in the sensitivity table.
- Nothing ran on hardware. Every result is sim pass only, calc only or CAD check only as labelled.

## 6. Files and commands

Outputs in the scratch results folder (not in the repo): this file; static.json (step 1); cad_base_stops.json (section 1.1); runs.jsonl (one line
per sim case of every set, sim pass only); probes/ (the via-sit probes and searches, the retune search); code/ (every script).
The 1 ms state traces (npz per case, about 21 MB per set) stay in the session scratch folder
the session scratch folder (not in the repo)

Commands (from the session scratch folder (not in the repo); every sim under the shared lab gym (overlay gym/overlays/duck)'s
train/ramcap.py --cap-mb 3000, at most 2 at once; DUCK_REPO is the sit worktree for the sit models, the base worktree otherwise):
```
ODM_PLAYGROUND=the scratch results folder (not in the repo) python3 the scratch results folder (not in the repo) --out model
python3 code/inertials.py the scratch results folder (not in the repo) inertials_base.json     # and the sit worktree into inertials_sit.json
python3 code/static_check.py the scratch results folder (not in the repo)                        # step 1, calc only
TMPDIR=tmp python3 code/cad_base_stops.py base cad/base_stops.json              # section 1.1, CAD check only
code/queue.sh base:sts3250_high sit:sts3250_high sit_noclamp:sts3250_high ...   # sitgym.py per set, one result file per case
python3 code/analyze.py runs <set> <set> ...; code/fail_summary.py; code/roll_check.py; code/rest_compare.py; code/pairdiff.py
python3 code/retune_cma.py --model sit_clamp-neck-head --tag nh1 --cases <8 back cases>
python3 code/via_sit.py --model sit_xcache; python3 code/sit_rise_check.py sit_xcache; python3 code/vsit_cma.py ...
```
Set names: base, base_sitmass, base_cad, sit, sit_noclamp, sit_clamp-<groups> (software limits only on knee, ankle, neck, head,
yaw, roll, hip), and flags +nhfree (neck and head pitch at the base ranges), +nh<neck>_<head> (the two stops moved there, the
software limit 3 deg inside), +noparts, +selfseat, +xcache; then _<knee>.
