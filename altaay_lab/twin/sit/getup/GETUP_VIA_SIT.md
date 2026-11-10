# GETUP_VIA_SIT: a get-up through the sit, inside the real joint limits (PR 28)

_Copied into the repo from the get-up search job (2026-11-07 ET, sim pass only), local paths removed. The code, runs, CMA logs and traces it names stayed in the scratch results folder; the programs are in programs/ (chain_v3r.json, hand_I.json, roll_back3.json). The port into the shared lab gym (overlay gym/overlays/duck) and the re-evaluation on the merged sit model (aad3a9a) are in VIA_SIT_EVAL.md: 248 of 296 again, case by case the same. This search judged success with the gym get-up library's earlier rule (the 2 s still window could start before the program ended); VIA_SIT_EVAL.md counts it only after the program ends, with any break resetting it, and no case changes._

Date 2026-11-07 (UTC on the box, about 06:00 to 07:54). Written by a Claude Code sub-agent for the duck lead. Read-only search
job on the gym side: nothing committed or pushed to either repo; the two worktrees made for it were removed at the end.
Labels: **sim pass only** (MuJoCo in the shared lab gym, overlay gym/overlays/duck), **calc only** (kinematics, limits),
**CAD check only** (exact-mesh overlap sweep). Nothing here is a hardware result. Every number cites its file; "BLOCKER"
where there is none.

## Answer

**Yes, in sim: a get-up through the sit that keeps every joint target inside software/servo_limits.json gets Duckie up in
248 of 296 cases (sim pass only; the base model's stored programs 254 of 296, the sit model with them 0 of 296). Back
156 of 156, side 68 of 68, front 24 of 72: every flat, obstacle and up-ramp case stands up; every front rest on a down ramp
(48 cases) does not.** Without the one IMU-conditioned retry of the roll it is 244 of 296. The neck and head stops do not move, the knee and ankle contacts are not relieved, the cut thigh
covers are out of the gym's self-collision as GETUP_SIT's probe had them (checked on the tuck path against the exact
meshes: no overlap).

The program (programs/chain_v3r.json; section 6 spells it out):
1. **Roll onto the belly** (back and side rests): the stored rolls go the other way (the side roll puts the duck on its back,
   17 of 17 here, as GETUP_SIT found), so a back-to-front roll was searched: an asymmetric leg scissor with a head yaw swing,
   CMA-ES over 26 keyframe values, 24 of 24 training cases after a retrain on mu 0.6 and 6.0 V (section 1.3). Side rests use
   the stored side swing onto the back first, then the same roll.
2. **Tuck, the missing middle** (section 2): a hand-designed flat-foot sit-up. Squat on the soles (hip +10, knee 135, ankle
   on its -92 limit), then fold the hip to -55 with the knee and ankle held: the ankle's stop locks the leg block, so the
   hip torque lifts the trunk instead of swinging the legs, and the duck rocks back onto its seat and settles level; then
   the sit entry (-60, 147, -92). Nine other orders fail (direct fold, kneel then hip extension, feet forward with the knee
   at 147, head swings): the trunk stays 54 to 69 deg nose down on its head. 15 of 15 flat front rests reach the sit (tilt
   0.1 to 0.6 deg, h 0.077 m, all the weight on the soles); the 40 x 16 CMA-ES over the tuck keyframes adds nothing.
3. **The sit's own stand-up** (b56ea56 path): 4 of 4 from the squat in the gym with the cache hulls out, 0 of 4 with them in
   (section 1.1); chained after the tuck it stands up in every case the tuck reaches.

**What fails:** the down ramps (section 4). Lying head-down a 10 or 20 deg slope, no squat in the sit's hip range gets the
weight off the head, and the sit-up swings the legs: 0 of 48 by hand, by CMA-ES (40 x 16 on 12 flat and ramp cases), with
the hip pitch limit moved to +40, and with the neck and head at the base ranges plus a head push. **No small geometry change
unlocks it; it needs training or a turn across the slope** (BLOCKER). The 4 roll misses of a single open-loop
attempt (mu 0.6) are taken by one retry when the IMU still reads back or side (chain_v3r: 224 of 224 side and back cases).

Hardware: nothing. The sit-up loads the hip pitch servos to their torque limit at both voltages and the neck to its limit
through the rise (section 5).

## 0. What was tested

| item | value | source |
|---|---|---|
| sit PR model | this repo's claude/v1-sit at **b56ea563e6ce29aa5657ed72e27c7a84a60b4562** (a detached worktree) | git |
| model files | altaay_lab/twin/sit/sit_model.py run read-only into scratch from b56ea56: open_duck_mini_v2.xml, scene_flat_terrain.xml, joints_properties.xml and sit_model.json are byte-identical (cmp) to the retest's 758f297 model; the per-body inertials of sim/mass_budget.py are identical (2.7881 kg). So the stops, software limits, parts and masses are those of GETUP_SIT; only the stand-up path changed (b5843bf LEAN, b56ea56 hip roll and yaw to 0 while seated) | code/kin_probe.py run log; inertials_sit.json |
| software limits | altaay_lab/software/servo_limits.json (3 deg inside every hard stop): hip pitch -72 to 10.5, knee -25.5 to 147, ankle -92 to 46, hip roll -5 to 22 (outward to inward), hip yaw -21 to 20.3, neck pitch -17 to 22, head pitch -22 to 36, head yaw -105 to 79, head roll -27 to 27 (left side; the right mirrors) | servo_limits.json "soft_lo_deg", "soft_hi_deg" |
| the shared lab gym (overlay gym/overlays/duck) | at **961a5b4496409a2ace04df81cba2ab66b37f3de8** (a detached worktree), the same commit as GETUP_SIT | git |
| pipeline | GETUP_SIT's code/sitgym.py (copied, the gym path changed): the collision duck of getup/getup_robot.py (38 shell hulls, self-collision), frozen physics minto_floor_v1 at 1 ms, STS3250 knees (D32), servos at the supply voltage (BAM), every target clipped to the software limits before it is sent (the angle-limit registers), MuJoCo clamps again; start = the library rest pose re-settled on this model (falls.py rule); success = the GETUP rule (upright, still 2 s, soles only, no joint more than 1 deg past its range) | code/sitgym.py, code/viasit2.py |
| collision model of the fold | **sit_xcache**: the two cut thigh covers (left_cache, right_cache) do not self-collide (their convex hulls fill the sit's cuts: GETUP_SIT section 2.3); everything else collides. Checked for this job's tuck path with the sit branch's exact-mesh sweep, section 2.3 | code/cad_tuck_check.py |
| fall library | the 74 rest poses of falls/poses.json (back 39, side 17, front 18; both masses), the 296 cases = 74 x 7.2 / 6.0 V x floor mu 1.0 (gym) / 0.6, each on its own course | GETUP.md section 2, GETUP_SIT section 0 |
| stand-up path | sit_sim.py rise() at b56ea56: 0.3 s hold, 1.0 s to the sit target (hip -60, knee 147, ankle -92) with hip roll and yaw 0, then sitlib.PATH_A1B back to STAND at 1.5 s per waypoint: (-60, 147, -92), (-43, 130, -82), (-39, 110, -67), (-18, 75, -49), (-5, 40, -29), (-15, 5, 0), neck -19 and head -22 throughout, then STAND with the head at 0 (1.5 s), 1.0 s hold, then the walk's home key (1.5 s), where the GETUP rule is judged | sit_sim.py lines 47 to 54 and 325 to 349; sitlib.py PATH_A1B and LEAN; code/viasit2.py rise_frames |

Runs: every sim under the gym's train/ramcap.py --cap-mb 3000, at most two sims at once (another agent ran sims on the box), one
result file per case, finished cases skipped on restart (no restart happened during this job). Scratch:
the session scratch folder (not in the repo).

## 1. Reproduction of the two halves (sim pass only)

### 1.1 The sit's stand-up from the seated pose

code/sit_rise_check2.py: from the home key, STAND, the sit-down (PATH_A1B[1:6] with LEAN at the study's ramp times), 1.5 s at the
sit with the neck at the software limit (+22) and 1.5 s more, then rise() as above and the home key; duck/arena.

| model | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 | file |
|---|---|---|---|---|---|
| sit_xcache (cache hulls out of self-collision) | up (final tilt 0.2 deg) | up (0.2) | up (1.1) | up (1.1) | repro/sit_rise_check_sit_xcache.json |
| sit (cache hulls in) | not up: tips back (final tilt 112) | 112 | 113 | 112 | repro/sit_rise_check_sit.json |

With the cache hulls out: **4 of 4**, the trunk tilt in the rise stays under 16.1 deg at 7.2 V and 18.7 at 6.0 V (the LEAN
waypoints lean it forward on purpose), peak servo load 0.76 of the limit at 7.2 V and 0.91 at 6.0 V, no joint past its range; at
the sit the legs read (-60, 150, -93) deg (the knee and ankle rest on their compliant hard stops 3 deg past the clamped targets),
the soles carry 27.7 N and the seat and bumper 0 (torque on). With the cache hulls in: 0 of 4, the fold stops on the hull and the
duck tips back from pitch -27 deg at the sit with 20 N on the seat, as GETUP_SIT section 2.3 found on the old path. So the new
path (LEAN, roll and yaw to 0) stands up in the gym as the old one did; the gym needs the hull exclusion either way.

### 1.2 The rolls

code/roll_check2.py, every side (17) and back (39) rest pose at 7.2 V, mu 1.0, on its own course, the body class 1.3 to 1.5 s
after the swing (gravity in the base frame, common.classify):

| swing | from the side (17) | from the back (39) |
|---|---|---|
| stored side program's swing (side_final.json: head yaw -6 then -152 deg, clamped to -105, mirrored by the side down), legs held | **back 17** | back 21, side 18 |
| the same swing mirrored | side 14, back 3 | back 25, side 14 |
| stored front program's swing (front_final.json: legs set to (-25, 54, -45), neck -18, head -13, yaw +133 clamped to +79 then -88) | side 17 | **side 38**, back 1 |
| the same mirrored | side 17 | side 38, back 1 |
| legs folded flat (-72, 147, -92) then the front swing | back 10, side 7 | side 22, back 12, front 5 |
| legs folded flat then the front swing mirrored | side 11, back 6 | back 15, **front 13**, side 11 |

So the stored rolls do what GETUP_SIT section 2.3 says: the side roll puts the duck **on its back** (17 of 17 here, 68 of 68
there), the front roll (from the front) on its back too (55 of 72 there). Neither puts it on its belly, which is where the tuck
starts, so the brief's "back and side to front still work" is not what the stored rolls do: a side-to-front and a
back-to-front roll had to be found (section 3). What the stored swings do give: from the back, the front program's swing
puts the duck on its **side** in 38 of 39.

### 1.3 Rolls onto the front (searched, sim pass only)

code/cma_search.py --family roll: three keyframes, the first two with each leg free (hip pitch, knee, ankle), neck and head
pitch and a head yaw, the third symmetric with the yaw at 0; 26 values, every target inside the software limits; CMA-ES
(getup/cmaes.py) maximizing the mean over the training cases of 2 x gravity-x in the base frame 1.3 to 1.5 s after the
swing (+1 lying on the front) plus 1 if the class is front; population 16.

- **Side to front, direct** (cma/roll_side1*): 17 side rests, 7.2 V, mu 1.0, from the folded-legs mirrored swing: 2 of 17 on
  the front at generation 0, 4 of 17 at generation 9, stopped there (the side rest barely moves under any swing: gravity-x
  stays at -0.1 in 13 of 17). Not used.
- **Back to front** (cma/roll_back1*): 16 back rests (flat, obstacles, every up ramp, both masses), 7.2 V, mu 1.0, from the
  folded-legs mirrored swing (13 of 39 in section 1.2): 13 of 16 at generation 3, **16 of 16 at generation 15** (f 2.98 of 3),
  stopped at 21. The roll it found is a leg scissor with a head swing: 0.4 s to left leg (-69, 30, -32), right leg (-33,
  115, -75), neck +15, head -14, head yaw -74; 0.9 s to left (-49, 135, -41), right (-59, 71, -56), neck -2, head +4, yaw +74;
  0.8 s to both legs (-39, 114, -56), neck +4, head -16, yaw 0 (cma/roll_back1_best.json, left-leg convention, degrees).
- **Side to front, through the back:** the stored side swing (legs held, mirrored by the side down, onto the back) and then
  the back-to-front roll above, unmirrored. Chained in programs/chain_v1.json.

- **Retrains on mixed conditions** (the first chained grid, chain_v1, failed 51 of 224 side and back cases at the roll, 32 of
  them at mu 0.6: the roll had only seen mu 1.0): roll_back2 on 16 cases (10 back, 6 side through the stored swing; mu 0.6
  and 6.0 V in the set), from the roll_back1 best: 16 of 16 at generation 10, stopped at 11 (chain_v2: 213 of 296, the mu
  1.0 cases regressed). roll_back3 on 24 cases (12 back, 12 side, half at mu 1.0, both voltages, flat, obstacles and up
  ramps), from the roll_back2 best, sigma 0.1: **24 of 24 at generation 7**, stopped at 10; this is the roll of the final
  program programs/chain_v3.json: 0.7 s to left leg (-71, 85, -64), right leg (-31, -4, -86), neck +22, head -14, yaw -78;
  1.3 s to left (-46, 99, 7), right (-67, 109, -31), neck +3, head -14, yaw +73; 0.5 s to both (-45, 75, -60), neck +19,
  head +6, yaw 0 (cma/roll_back3_best.json).

## 2. The missing middle: front rest pose to the seated pose

### 2.1 Why the earlier probe stuck at 63 deg (calc only)

The duck's knee bends backward: at the sit (hip -60, knee 147, ankle -92) the thigh runs back and down from the hip, the shin
comes forward horizontally 39 mm below the hip, the foot lies flat under the ankle 10 mm in front of the hip, the knee is the
rearmost point and the whole-body CoM sits 6 mm behind the ankle (code/kin_probe.py on the sit model: hip x -0.035, knee -0.103,
ankle -0.025, CoM -0.019 m in the base frame, trunk upright). With both soles flat on the floor the trunk pitch is fixed by the
leg angles: **pitch (nose down) = 5 + hip + knee + ankle** deg (fits the sit 0, the home key 2, the squat below 60 against 56 to
60 measured). Folding straight to the sit from a front rest (GETUP_SIT's probe) leaves hip + knee + ankle = -5 while the trunk
is at 63 to 70 deg nose down, so the feet are up behind and the duck rests on its head and toes; nothing in the sit's ranges
rotates the body about its feet from there (the neck has 39 deg and the head 58 deg of stroke, the beak lifts the trunk front by
about 50 mm at most).

### 2.2 The hand-designed sequences (sim pass only)

code/hand_tuck.py, programs in hand/seq*.json, results hand/hand_*.json. Every sequence ends with the sit entry (-60, 147, -92)
over 0.6 s and a 0.8 s hold; the rise is chained in seq3 only. Cases: the 15 front rest poses that stay "front" when settled
on the flat arena (the 3 ramp_20_down stock rests roll onto their left side there: repro/front_flat_settle.json), 7.2 V, mu
1.0; seq4 the 12 down-ramp rests on their ramps.

| round | sequence | keyframes (hip, knee, ankle, neck, head; T s) then the sit entry | cases | at the sit: mean tilt deg | sit reached | stood up (with the rise) | what fails |
|---|---|---|---|---|---|---|---|
| seq1 | A_direct | (-60, 147, -92, -19, -22; 1) | 15 front rests, flat arena, 7.2 V | 68.7 | 0 of 15 | not run | trunk stays nose down (tilt 68 to 69), head on the floor (11 to 11 N) in 15 |
| seq1 | B_kneel_hipext | (-72, 147, -92, -19, -22; 0.8); (10, 147, -92, -19, -22; 0.8); (10, 147, -92, -19, -22; 0.4) | 15 front rests, flat arena, 7.2 V | 63.2 | 0 of 15 | not run | trunk stays nose down (tilt 63 to 64), head on the floor (10 to 10 N) in 15 |
| seq1 | C_feetfwd_fold | (10, 147, -92, -19, -22; 0.8); (10, 147, -92, -19, -22; 0.4) | 15 front rests, flat arena, 7.2 V | 56.6 | 0 of 15 | not run | trunk stays nose down (tilt 56 to 57), head on the floor (4 to 5 N) in 15 |
| seq1 | D_feetfwd_a60 | (10, 147, -60, -19, -22; 0.8); (10, 147, -60, -19, -22; 0.4) | 15 front rests, flat arena, 7.2 V | 54.3 | 0 of 15 | not run | trunk stays nose down (tilt 43 to 64), head on the floor (2 to 12 N) in 15 |
| seq1 | E_feetfwd_k120 | (10, 120, -70, -19, -22; 0.8); (10, 120, -70, -19, -22; 0.4) | 15 front rests, flat arena, 7.2 V | 63.9 | 0 of 15 | not run | trunk stays nose down (tilt 64 to 64), head on the floor (10 to 10 N) in 15 |
| seq1 | F_feetfwd_headback | (10, 147, -92, -17, -22; 0.8); (10, 147, -92, 22, 36; 0.15); (10, 147, -92, 22, 36; 0.3) | 15 front rests, flat arena, 7.2 V | 57.3 | 0 of 15 | not run | trunk stays nose down (tilt 54 to 64), head on the floor (4 to 7 N) in 15 |
| seq1 | G_kneel_hipext_headback | (-72, 147, -92, -17, -22; 0.8); (10, 147, -92, 22, 36; 0.6); (10, 147, -92, 22, 36; 0.4) | 15 front rests, flat arena, 7.2 V | 67.4 | 0 of 15 | not run | trunk stays nose down (tilt 67 to 67), head on the floor (11 to 11 N) in 15 |
| seq1 | H_legs_back_then_fold | (-72, 60, -40, -19, -22; 0.6); (-72, 147, -92, -19, -22; 0.5); (10, 147, -92, -19, -22; 0.6); (10, 147, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 63.1 | 0 of 15 | not run | trunk stays nose down (tilt 63 to 63), head on the floor (10 to 10 N) in 15 |
| seq2 | I_squat_situp | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.5 | 15 of 15 | not run | none |
| seq2 | J_squat_situp_k130 | (10, 130, -92, -19, -22; 0.8); (10, 130, -92, -19, -22; 0.3); (-50, 130, -92, -19, -22; 1); (-50, 130, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.7 | 15 of 15 | not run | none |
| seq2 | K_squat_situp_fast | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 0.5); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 4.1 | 15 of 15 | not run | none |
| seq2 | L_situp_headback | (10, 135, -92, 22, 36; 0.8); (10, 135, -92, 22, 36; 0.3); (-55, 135, -92, 22, 36; 1); (-55, 135, -92, 22, 36; 0.3) | 15 front rests, flat arena, 7.2 V | 68.6 | 0 of 15 | not run | trunk stays nose down (tilt 69 to 69), head on the floor (11 to 11 N) in 15 |
| seq2 | M_situp_to60 | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-60, 135, -92, -19, -22; 1); (-60, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.5 | 15 of 15 | not run | none |
| seq2 | N_squat_h0 | (0, 135, -92, -19, -22; 0.8); (0, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.3 | 15 of 15 | not run | none |
| seq2 | O_situp_slow | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 2); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.1 | 15 of 15 | not run | none |
| seq2 | P_situp_headfwd0 | (10, 135, -92, 0, 0; 0.8); (10, 135, -92, 0, 0; 0.3); (-55, 135, -92, 0, 0; 1); (-55, 135, -92, 0, 0; 0.3) | 15 front rests, flat arena, 7.2 V | 68.7 | 0 of 15 | not run | trunk stays nose down (tilt 69 to 69), head on the floor (11 to 11 N) in 15 |
| seq3_rise | I_squat_situp | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.5 | 15 of 15 | 15 of 15 | none |
| seq3_rise | N_squat_h0 | (0, 135, -92, -19, -22; 0.8); (0, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.3 | 15 of 15 | 15 of 15 | none |
| seq3_rise | O_situp_slow | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 2); (-55, 135, -92, -19, -22; 0.3) | 15 front rests, flat arena, 7.2 V | 0.1 | 15 of 15 | 15 of 15 | none |
| seq4_ramps | I_k135 | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 79.8 | 0 of 12 | not run | trunk stays nose down (tilt 75 to 85), head on the floor (12 to 14 N) in 12 |
| seq4_ramps | Q_k125 | (10, 125, -92, -19, -22; 0.8); (10, 125, -92, -19, -22; 0.3); (-55, 125, -92, -19, -22; 1); (-55, 125, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 81.7 | 0 of 12 | not run | trunk stays nose down (tilt 76 to 87), head on the floor (12 to 14 N) in 12 |
| seq4_ramps | R_k115 | (10, 115, -92, -19, -22; 0.8); (10, 115, -92, -19, -22; 0.3); (-55, 115, -92, -19, -22; 1); (-55, 115, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 82.9 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 87), head on the floor (13 to 14 N) in 12 |
| seq4_ramps | S_k105 | (10, 105, -92, -19, -22; 0.8); (10, 105, -92, -19, -22; 0.3); (-55, 105, -92, -19, -22; 1); (-55, 105, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 82.8 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 87), head on the floor (13 to 14 N) in 12 |
| seq4_ramps | T_k115_h-65 | (10, 115, -92, -19, -22; 0.8); (10, 115, -92, -19, -22; 0.3); (-65, 115, -92, -19, -22; 1); (-65, 115, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 83.0 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 87), head on the floor (13 to 14 N) in 12 |
| seq4_ramps | U_k125_slow | (10, 125, -92, -19, -22; 1.2); (10, 125, -92, -19, -22; 0.4); (-55, 125, -92, -19, -22; 1.5); (-55, 125, -92, -19, -22; 0.3) | 12 down-ramp front rests on their ramps, 7.2 V | 81.7 | 0 of 12 | not run | trunk stays nose down (tilt 76 to 87), head on the floor (12 to 14 N) in 12 |
| seq5_hip40 | I_h10 | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | the 12 down-ramp cases, hip pitch limit moved to +40 (model sit_xcache+hip40) | 79.8 | 0 of 12 | not run | trunk stays nose down (tilt 75 to 85), head on the floor (12 to 14 N) in 12 |
| seq5_hip40 | V_h20 | (20, 135, -92, -19, -22; 0.8); (20, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | the 12 down-ramp cases, hip pitch limit moved to +40 (model sit_xcache+hip40) | 80.2 | 0 of 12 | not run | trunk stays nose down (tilt 76 to 85), head on the floor (12 to 14 N) in 12 |
| seq5_hip40 | W_h30 | (30, 135, -92, -19, -22; 0.8); (30, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | the 12 down-ramp cases, hip pitch limit moved to +40 (model sit_xcache+hip40) | 79.6 | 0 of 12 | not run | trunk stays nose down (tilt 74 to 85), head on the floor (12 to 14 N) in 12 |
| seq5_hip40 | X_h30_k120 | (30, 120, -92, -19, -22; 0.8); (30, 120, -92, -19, -22; 0.3); (-55, 120, -92, -19, -22; 1); (-55, 120, -92, -19, -22; 0.3) | the 12 down-ramp cases, hip pitch limit moved to +40 (model sit_xcache+hip40) | 83.0 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 88), head on the floor (13 to 14 N) in 12 |
| seq5_hip40 | Y_h40 | (40, 135, -92, -19, -22; 0.8); (40, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | the 12 down-ramp cases, hip pitch limit moved to +40 (model sit_xcache+hip40) | 79.6 | 0 of 12 | not run | trunk stays nose down (tilt 74 to 85), head on the floor (12 to 14 N) in 12 |
| seq6_nhfree | I_nh_sit | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -19, -22; 0.3); (-55, 135, -92, -19, -22; 1); (-55, 135, -92, -19, -22; 0.3) | the 12 down-ramp cases, neck and head pitch at the base ranges (sit_xcache+nhfree) | 78.3 | 0 of 12 | not run | trunk stays nose down (tilt 73 to 83), head on the floor (12 to 14 N) in 12 |
| seq6_nhfree | Z1_headpush | (10, 135, -92, -20, -45; 0.8); (10, 135, -92, -20, -45; 0.3); (-55, 135, -92, -20, -45; 1); (-55, 135, -92, -20, -45; 0.3) | the 12 down-ramp cases, neck and head pitch at the base ranges (sit_xcache+nhfree) | 77.0 | 0 of 12 | not run | trunk stays nose down (tilt 72 to 82), head on the floor (12 to 14 N) in 12 |
| seq6_nhfree | Z2_headpush_late | (10, 135, -92, -19, -22; 0.8); (10, 135, -92, -20, -45; 0.3); (-55, 135, -92, -20, -45; 1); (-55, 135, -92, -19, -22; 0.5) | the 12 down-ramp cases, neck and head pitch at the base ranges (sit_xcache+nhfree) | 78.2 | 0 of 12 | not run | trunk stays nose down (tilt 73 to 83), head on the floor (12 to 14 N) in 12 |
| seq6_nhfree | Z3_headback | (10, 135, -92, 65, 45; 0.8); (10, 135, -92, 65, 45; 0.3); (-55, 135, -92, 65, 45; 1); (-55, 135, -92, -19, -22; 0.5) | the 12 down-ramp cases, neck and head pitch at the base ranges (sit_xcache+nhfree) | 81.7 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 86), head on the floor (13 to 14 N) in 12 |
| seq6_nhfree | Z4_push_then_back | (10, 135, -92, -20, -45; 0.8); (10, 135, -92, -20, -45; 0.3); (-55, 135, -92, 65, 45; 0.6); (-55, 135, -92, -19, -22; 0.5) | the 12 down-ramp cases, neck and head pitch at the base ranges (sit_xcache+nhfree) | 81.8 | 0 of 12 | not run | trunk stays nose down (tilt 78 to 86), head on the floor (13 to 14 N) in 12 |

**What works (seq2 I, seq3): the flat-foot sit-up.** (1) Squat: hip +10, knee 135, ankle -92 over 0.8 s and hold 0.3 s. The duck
rises off its head onto its soles, trunk 56 to 60 deg nose down, h 0.058 m, the soles carry the whole weight (the knee stays
under the 140 deg where the folded foot meets the belly at hip +10: targeting 147 there jams the foot into the trunk and locks
the hip, seq1 C). (2) Sit-up: hip to -55 over 1.0 s with the knee and ankle held. The ankle sits on its -92 software limit
(hard stop -95), so the leg block cannot rotate under the hip torque and the trunk rises instead: pitch 56 -> 19 -> -19 (a
rock back onto the seat, 8 N) -> 0. (3) The sit entry closes the knee to 147 and the hip to -60: tilt 0.1 to 0.6 deg, h 0.076
to 0.078 m, soles 27.7 N, seat and bumper 0, the legs at (-59, 150, -92). Then the rise. seq2 D (ankle -60 in the squat) shows
the trap: the ankle target moving to -92 during the sit-up rotates the foot, the heel lifts, the body pitches as a whole on its
toes and falls back onto its head.

### 2.3 Exact-mesh check of the tuck path (CAD check only)

code/cad_tuck_check.py runs the sit branch's own sit_sweep.Model.new_hits (exact meshes, manifold3d, every pair over 2 mm3 past
its zero-pose overlap) on 33 states along the path: the front rest's legs (-45, 75, -40), the squat, the sit-up, the sit, at 5
deg steps. **0 states with a new overlap** (repro/cad_tuck_path_hand_I.json). So taking the cut thigh covers out of the gym's
self-collision hides no real contact on this path; the gym's other hulls (the thigh and shin sheets, the foot) stay in.

### 2.4 The tuck on the 72 front cases (sim pass only)

code/grid296.py with programs/hand_I.json, every front rest on its own course, 7.2 and 6.0 V, mu 1.0 and 0.6 (runs/front72_handI):

| front rests on | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 |
|---|---|---|---|---|
| flat (6: duck/arena x 5, duck/ice) | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |
| ramp_10_down (6) | 0 of 6 | 0 of 6 | 0 of 6 | 0 of 6 |
| ramp_20_down (6) | 0 of 6 | 0 of 6 | 0 of 6 | 0 of 6 |

Flat: 24 of 24 stand up (upright and still 13.7 to 13.8 s after the program starts, final tilt 0.2 to 1.1 deg), peak servo
load in the chain: hip pitch 1.0 of the limit (the sit-up, both voltages), neck 1.0 (holding the head at -19 / -22 through the
rise, as SIT.md section 5 saw), head 0.92, knee 0.79, ankle 0.33; seat and bumper peaks 51 N (the rock back onto the seat at
the end of the sit-up); no joint past its range. Down ramps: 0 of 48, all at the tuck. Lying head-down the slope the squat
never gets the weight onto the soles (the head keeps 13 to 17 N on the ramp, trunk 80 to 95 deg from the vertical) and the
sit-up swings the legs instead of the trunk; the duck ends on its head and soles at 75 deg (ramp_10_down) or 85 deg
(ramp_20_down). Smaller knee angles in the squat (125, 115, 105), a hip of -65 and a slower sit-up (seq4) change nothing
(tilt 78 to 87). The base model's stored programs got 12 of these 48 (GETUP_SIT).

### 2.5 CMA-ES over the tuck keyframes (sim pass only)

code/cma_search.py --family tuck: 4 free keyframes (hip pitch, knee, ankle, neck pitch, head pitch, duration) plus the sit
entry time, 25 values, bounds the software limits and 0.15 to 1.5 s; CMA-ES **40 generations x 16**, sigma 0.2, started from
hand_I; objective (no rise, for speed) viasit2.tuck_score: 3 x (1 - tilt at the sit / 90) + 2 x the share of the weight on the
soles, seat and bumper + 1 x the height term + 1 x stillness, 7 for a seated duck. Training set cases_tuck_train12.txt: 12
front cases, flat first (2: stand_push_forward ours 7.2 V mu 1.0, walk_push_forward stock 6.0 V mu 0.6) and the down ramps
(6 ramp_10_down, 4 ramp_20_down, both masses, 7.2 and 6.0 V, mu 1.0 and 0.6, each on its ramp); 75 to 95 s per generation.

Result (cma/tuck1.jsonl, cma/tuck1_best.json): the best mean 3.94 at generation 16 (hand_I scores 3.46), never a seated duck
on a ramp: the two flat cases sit (tilt 0.0 and 0.1 deg), the ten ramp cases end at tilt 72 to 74 (ramp_10_down) and 82 to
85 (ramp_20_down) with the head on the ramp, exactly where hand_I leaves them. The best vector moves the squat to (2, 124,
-48) then (9, 69, 29) then (4, 132, -75) and the sit-up to (-21, 122, -92), which changes nothing on the slopes. The flat
cases are solved by hand_I already, so hand_I stays the program; the CMA adds no case. The search ran the 40 x 16 the brief
asked for and found nothing for the down ramps: on a down slope the front rest has the head downhill of the feet at 80 to
100 deg, every squat in the sit's hip range (at most +10.5 deg) leaves the CoM downhill of the soles, and the sit's ranges
hold no motion that pushes the body uphill off its head (section 4).

## 3. Chained evaluation on the 296-case grid

code/grid296.py with programs/chain_v3r.json (section 6 lists it): every rest pose of the library re-settled on the sit model on
its own course, 7.2 and 6.0 V, mu 1.0 and 0.6, STS3250 knees, targets clipped to the software limits, the GETUP success rule.
Runs: runs/front72_handI (the 72 front cases; the tuck is the same in chain_v3r) and runs/sideback224_chain_v3r (the 224 side
and back cases); one line per case in runs.jsonl. The base and sit-only columns are GETUP_SIT's runs.jsonl (sets
base_sts3250_high and sit_sts3250_high), the same 296 cases.

| pose class (rest poses) | V | floor mu | base d6179ae | sit 758f297 (stored programs) | sit b56ea56, via the sit (this job) |
|---|---|---|---|---|---|
| back (39) | 7.2 | 1.0 | 39 of 39 | 0 of 39 | 39 of 39 |
| back (39) | 7.2 | 0.6 | 39 of 39 | 0 of 39 | 39 of 39 |
| back (39) | 6 | 1.0 | 35 of 39 | 0 of 39 | 39 of 39 |
| back (39) | 6 | 0.6 | 39 of 39 | 0 of 39 | 39 of 39 |
| side (17) | 7.2 | 1.0 | 17 of 17 | 0 of 17 | 17 of 17 |
| side (17) | 7.2 | 0.6 | 17 of 17 | 0 of 17 | 17 of 17 |
| side (17) | 6 | 1.0 | 16 of 17 | 0 of 17 | 17 of 17 |
| side (17) | 6 | 0.6 | 17 of 17 | 0 of 17 | 17 of 17 |
| front (18) | 7.2 | 1.0 | 11 of 18 | 0 of 18 | 6 of 18 |
| front (18) | 7.2 | 0.6 | 8 of 18 | 0 of 18 | 6 of 18 |
| front (18) | 6 | 1.0 | 5 of 18 | 0 of 18 | 6 of 18 |
| front (18) | 6 | 0.6 | 11 of 18 | 0 of 18 | 6 of 18 |
| **all** | both | both | **254 of 296** | **0 of 296** | **248 of 296** |

Split by terrain (base -> sit stored -> via the sit, of the cases in the cell):

| class, terrain (rest poses) | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 |
|---|---|---|---|---|
| back, flat (12) | 12 -> 0 -> 12 of 12 | 12 -> 0 -> 12 of 12 | 12 -> 0 -> 12 of 12 | 12 -> 0 -> 12 of 12 |
| back, obstacles (12) | 12 -> 0 -> 12 of 12 | 12 -> 0 -> 12 of 12 | 11 -> 0 -> 12 of 12 | 12 -> 0 -> 12 of 12 |
| back, ramps up (15) | 15 -> 0 -> 15 of 15 | 15 -> 0 -> 15 of 15 | 12 -> 0 -> 15 of 15 | 15 -> 0 -> 15 of 15 |
| side, flat (10) | 10 -> 0 -> 10 of 10 | 10 -> 0 -> 10 of 10 | 9 -> 0 -> 10 of 10 | 10 -> 0 -> 10 of 10 |
| side, obstacles (4) | 4 -> 0 -> 4 of 4 | 4 -> 0 -> 4 of 4 | 4 -> 0 -> 4 of 4 | 4 -> 0 -> 4 of 4 |
| side, ramps up (3) | 3 -> 0 -> 3 of 3 | 3 -> 0 -> 3 of 3 | 3 -> 0 -> 3 of 3 | 3 -> 0 -> 3 of 3 |
| front, flat (6) | 6 -> 0 -> 6 of 6 | 6 -> 0 -> 6 of 6 | 5 -> 0 -> 6 of 6 | 6 -> 0 -> 6 of 6 |
| front, ramps down (12) | 5 -> 0 -> 0 of 12 | 2 -> 0 -> 0 of 12 | 0 -> 0 -> 0 of 12 | 5 -> 0 -> 0 of 12 |

Failures by class and first failing stage (this job's runs):

- front: tuck: 48

**248 of 296** (sim pass only) against the base model's 254 of 296 with the stored programs (Playground ranges, knee at -88)
and the sit model's 0 of 296 with them. Back 156 of 156, side 68 of 68, front 24 of 72. By terrain: flat 88 of 88 (the base
83), obstacles 64 of 64 (base 63), ramps up 72 of 72 (base 69), ramps down 0 of 48 (base 12). Without the retry stage
(chain_v3, tables_chain_v3_noretry.md, runs.jsonl set sideback224_chain_v3): 244 of 296, the 4 misses all at the roll at mu
0.6 (ramp_5_up stock s3 at both voltages and duck/edge_3mm ours s2 end on the back, stand_push_left stock s1 on its side);
the retry (the back roll again when the IMU reads back, the stored swing then the back roll when it reads side, a hold when
it reads front) takes all 4 and changes no other case. Time from the program start to upright and still: 13.7 to 13.8 s for
the front cases; with a roll 16.4 s median and 17.8 s at most without the retry stage, 20.4 and 21.9 s with it (the retry
stage holds its full 4.1 s even when the duck is already on its front; a runtime that skips it keeps the chain_v3 times).
Peak servo use over the side and back successes of chain_v3: hip pitch 1.0 of the limit (the sit-up), ankle 1.0 and head
yaw 1.0 (the roll's leg scissor and head swing), neck 1.0 (holding the head through the rise), head 0.98, knee 0.76. Seat
peak 52 N, bumper 48 N, no self-contact of the seat or bumper, no joint past its range in any success. After the roll every
success lies on its front at 85 to 86 deg (the roll leaves the legs at (-45, 75, -60), near the library's front rests). The
earlier chains for the record: chain_v1 (the roll trained at mu 1.0 only) 197 of 296, chain_v2 (16 mixed cases) 213 of 296,
chain_v3 244, all in runs.jsonl.

## 4. What fails and why; the smallest unlock

What fails in the final program (sim pass only, runs/sideback224_chain_v3r, runs/sideback224_chain_v3 and runs/front72_handI; the tables of section 3):

1. **Front rests on the down ramps: 0 of 48, all at the tuck.** Head downhill of the feet at 80 to 100 deg from the vertical,
   the squat never gets the weight off the head (12 to 17 N stay on it), and the sit-up swings the legs under the body
   instead of lifting the trunk; it ends on its head and soles at 75 deg (ramp_10_down) or 85 deg (ramp_20_down). This is
   geometry, not a stop: with the feet flat, trunk pitch = 5 + hip + knee + ankle, and on a slope the sit's legs put the CoM
   downhill of the soles whatever the knee (seq4: knee 105 to 135, hip -65, slow sit-up, 0 of 12). Tested unlocks (hand/
   hand_seq5_hip40.json, hand_seq6_nhfree.json, 12 cases each): the hip pitch forward limit moved from +10.5 to +20, +30 and
   +40 deg (the thigh spacer contact at 13.5 relieved): 0 of 12 each, tilt 75 and 85 unchanged, the hip reaches +30 in the
   squat and the sit-up still swings the legs; the neck and head pitch stops at the base ranges (-20 to +65, -45 to +45) with
   a head push (neck -20, head -45) in the squat and the sit-up, a head throw back (+65, +45), or the push then the throw: 0 of
   12 each (tilt 77 to 86). The 40 x 16 CMA on the tuck keyframes (section 2.5) found nothing either. The base model's stored
   programs, with the Playground ranges, got 12 of these 48 (GETUP_SIT); they need the knee at -88. **No small geometry
   change found that unlocks the down ramps; what is left is a learned get-up (GETUP.md section 8) or a program that
   first turns the body across the slope, which no keyframe here does.**
2. **Side and back rests that the roll leaves on the side or on the back** (4 of 224: 3 back rests end on the back, 1 side rest on its side, all four at mu 0.6). The roll is open loop: one
   leg scissor and head swing from whatever the rest pose is; the cases it misses are ramp_5_up stock s3 at 7.2 and 6.0 V mu 0.6 (ends on the back, pitch -96), duck/edge_3mm ours s2 at 7.2 V mu 0.6 (on the back, -91), stand_push_left stock s1 at 7.2 V mu 0.6 (the stored swing leaves it on its right side, pitch -142). A second attempt when the
   IMU still reads side or back (chain_v3r, programs/chain_v3r.json, runs/sideback224_chain_v3r) takes all 4 and changes no other case: 224 of 224.
3. No failure at the tuck or the rise in a side or back case of chain_v3 (chain_v2 had two tucks that failed from a roll that ended with the head at 89 to 90 deg, and one rise that fell on ramp_5_up at 6.0 V; chain_v3's roll ends at 85 to 86 deg and those cases pass).

Where the brief's three unlock candidates stand: a different tuck order (tried, section 2.2: nine orders before the one that
works; the one that works is the flat-foot sit-up); a small stop move (the hip +40 and the neck and head base ranges above:
no gain on the ramps; nothing else is near a stop in the chain: peak joint use in the successes is hip pitch -60 to +10,
knee 30 to 150, ankle -93 to 7, neck -19 to +22, head -22 to +6, head yaw -78 to +73, all inside the software limits with
the knee and ankle resting on their compliant stops 3 deg past the clamp at the sit); a trunk or head motion (the head push
and throw above: nothing on the ramps); training (the remaining route for the down ramps).

## 5. BLOCKERs

- **Nothing ran on hardware.** Every number is sim pass only, calc only or CAD check only as labelled; GETUP_SIT section 5's
  BLOCKERs stand (the CAD contacts on the printed parts, the firmware's goal clamping, the 6.0 V compensation, the shell
  contact model).
- **The sit-up loads the hip pitch servos to their limit** (ratio 1.0 of 3.14 N m at 7.2 V, 2.62 at 6.0 V, both voltages, in
  every success: section 2.4) and the neck to its limit while the head is held at -19 / -22 through the rise (as SIT.md
  section 5 saw). Thermal and stall margin of the STS3215 under that: not checked here (the electromech twin's BLOCKER).
- **The gym collision model of the fold:** the cut thigh covers are out of self-collision (sit_xcache). The exact-mesh sweep
  clears the tuck path (section 2.3) but not the rolls (asymmetric leg poses such as left (-71, 85, -64) with right (-31, -4,
  -86), head yaw -78: the sweep code moves both legs together); the roll's leg poses are inside every single-joint range and
  the covers touch only the shin and foot of their own leg, so a cross-leg contact is not expected, but it is not swept:
  BLOCKER until sit_sweep.py is run on the roll's keyframes.
- **The rest poses are the gym's** (74 falls of the stock walk); a real fall ends elsewhere. The roll and the tuck are open
  loop from the rest; the IMU picks the side for the stored side swing only.
- **Seat and bumper loads:** 51 N peak on each in the sit-up's rock back (section 2.4) and up to 48 N on the bumper
  in the rolls, at the gym's soft default contact; the TPU parts' strength under that: not checked (sit_stress.py has the
  stop loads only).
- **The head and neck stops do not move** in this program (the brief's rule); the tuck and the rise hold the head at -19 /
  -22 inside the sit's software limits throughout.
- Not run: a retry of the roll when the IMU still reads side or back; the CMA tuck on the ramps with a longer horizon or a
  turn; the 296 grid with the C001 knees; the seat and bumper against the robot's own shells (sit_selfseat).

## 6. Files and commands

Outputs in the scratch results folder (not in the repo, except this file and programs/): this file; PROGRESS.md; tables.md (section 3's tables, code/tables.py);
runs.jsonl (one line per sim case of the final sets front72_handI and sideback224_chain_v3r, and of chain_v1, v2 and v3); tables_chain_v3_noretry.md;
programs/ (hand_I.json the tuck, chain_v3r.json the whole program, chain_v3 without the retry, chain_v1 and v2, the case lists); cma/ (every search:
roll_side1, roll_back1, roll_back2, roll_back3, tuck1: per-generation jsonl and the best); hand/ (every hand sequence and
its results, hand_table.md); repro/ (sit_rise_check_sit_xcache.json, sit_rise_check_sit.json, front_flat_settle.json,
cad_tuck_path_hand_I.json); code/ (every script). The 1 ms state traces (npz per case) stay in the session scratch folder
the session scratch folder (not in the repo).

The program (programs/chain_v3r.json, degrees and seconds, left-leg convention, the right leg mirrored unless given):
- front rest: tuck hand_I = (10, 135, -92; 0.8 s) hold 0.3 s; (-55, 135, -92; 1.0 s) hold 0.3 s; sit entry (-60, 147, -92; 0.6 s)
  hold 0.8 s; neck -19, head -22 throughout; then rise() of sit_sim.py b56ea56 and the home key.
- back rest: roll_back3 (three keyframes above), then the tuck.
- side rest: the stored side swing (head yaw -6 then -152 deg clamped to -105, mirrored by the side down, 0.65 + 0.19 + 0.62 s,
  legs held) onto the back, then roll_back3 unmirrored, then the tuck.
- retry (back and side rests, one stage of 4.1 s after the roll, built from gravity in the base frame at its start, as the
  stored side program picks its side): back -> roll_back3 again; side -> the stored swing then roll_back3; front -> hold.
Every target is clipped to servo_limits.json before it is sent; the clip is what the angle-limit registers do.

Commands (from the scratch folder; every sim under the gym's train/ramcap.py --cap-mb 3000; DUCK_REPO the duck worktree,
GYM the gym worktree: code/env.sh):
```
ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 -B altaay_lab/twin/sit/sit_model.py --out model   # in the duck worktree
python3 -B code/kin_probe.py                                   # section 2.1, calc only
python3 -B code/sit_rise_check2.py sit_xcache|sit              # section 1.1
python3 -B code/front_flat_settle.py; python3 -B code/roll_check2.py cases_sideback_72.txt r1; python3 code/roll_summary.py r1   # 1.2
python3 -B code/hand_tuck.py hand/seqN.json CASES TAG [--flat] [--rise]; python3 code/hand_table.py                           # 2.2
nice python3 -B code/cad_tuck_check.py cad/tuck_path_hand_I.json                                                              # 2.3, CAD check only
python3 -B code/cma_search.py --family tuck --cases cases_tuck_train12.txt --tag tuck1 --gens 40 --pop 16 --x0 programs/hand_I.json   # 2.5
python3 -B code/cma_search.py --family roll --cases cases_back_train16.txt --tag roll_back1 --gens 40 --pop 16 --x0 "[...]"            # 1.3
ROLL_PREFIX=side_stored python3 -B code/cma_search.py --family roll --cases cases_roll_train24.txt --tag roll_back3 --x0 cma/roll_back2_best.json
python3 -B code/grid296.py programs/chain_v3r.json cases_sideback_224.txt sideback224_chain_v3r; ... programs/hand_I.json cases_front_all72.txt front72_handI
python3 -B code/tables.py front72_handI sideback224_chain_v3r > tables.md; python3 code/export_runs.py runs.jsonl front72_handI sideback224_chain_v3r
```
Model flags of sitgym.py used here: sit_xcache (the cut thigh covers out of self-collision), +hip<deg> (the hip pitch forward
limit moved, this job), +nhfree (neck and head pitch at the base ranges, from GETUP_SIT).
