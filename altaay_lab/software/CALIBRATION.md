# Joint zero calibration (D59)

The A1b sit and stand needs every leg joint zero right to 0.5 deg or better, and the two legs matched to 0.5 deg. On the repo
sim model with the final sit and stand path the stand-up worked 20 / 20 / 20 of 20 times at 0 / 0.5 / 1.0 deg (1 sigma per leg
joint), and 20 / 20 / 19 of 20 on 20 held-out seeds (sim pass only; twin/sit/SIT.md section 5). Commanding into a stop
with a 1 deg error drove the knees to 2.9 to 3.2 N m in the study, which is why the software stays 3 deg inside every
hard stop (software/servo_limits.json).

Nothing here is bought. Tools: the robot, its bus adapter, a flat table, the digital calipers (TEST_PLAN.md section 0,
TE3), and the bench scripts in altaay_lab/bench.

## 1. What the offset is

The Runtime adds `joints_offsets` (radians, duck config) to every goal and takes it off every reading
([U] Open_Duck_Mini_Runtime 376de65, mini_bdx_runtime/rustypot_position_hwi.py lines 111, 120 and 142):

    servo angle = joint angle + offset          raw = 2048 + servo angle x 4096 / 2 pi   (4096 steps, 0.088 deg each)

So at a known joint angle q_ref, read the raw position r and the offset is

    offset = (r - 2048) x 2 pi / 4096 - q_ref

The servo's own offset register (31) stays 0: the lab keeps the offsets in the config (bench/set_angle_limits.py).

## 2. The references: the D59 hard stops

Each leg joint now has a hard stop whose angle is set by the CAD (twin/sit/sit_sweep.py checks that the parts touch
there and not before; CAD check only). A stop is a better reference than "the joint at zero by eye": it is the same
part on both legs, and the reading does not depend on how the joint is held.

| Joint | Reference | q_ref (left; right) | Contact radius about the axis | 0.2 mm at the contact is |
|---|---|---|---|---|
| knee | TPU knee bumper on the shin spacer onto the knee servo case | +150; +150 deg | 27.8 mm | 0.41 deg |
| ankle | shin clamp block onto the TPU ankle pads on the foot plates | -95; -95 deg | 38.4 mm | 0.30 deg |
| hip roll | printed lug on roll_to_pitch onto roll_motor_bottom (outward) | -8; +8 deg | 22.5 mm | 0.51 deg |
| hip pitch | thigh cover onto the TPU hip pad on roll_to_pitch (back) | -75; +75 deg | 40.8 mm | 0.28 deg |
| neck pitch | the stock neck sheets' back edges onto the TPU faces of the neck stop block on trunk_top (back) | +25 deg | 41.1 mm | 0.28 deg |
| head pitch | the TPU face of the hook on head_pitch_to_yaw's left arm onto the left neck sheet's front edge (forward) | -25 deg | 29.3 mm | 0.39 deg |
| hip yaw | no stop: the toe and heel gap method, step 4 | 0; 0 deg | | |

Contact radii: calc from twin/sit/sit_cad.json (pad centre, or the lug region centre) and the joint axes of robot.urdf.
The last column is the angle a 0.2 mm print or seating error at the contact makes (calc). The reading itself is one
encoder step, 0.088 deg. The real repeatability of a press onto each stop is not known: **BLOCKER**, measured in step 3
(5 presses per joint; pass: the spread of the 5 readings is 0.3 deg or less).

## 3. Procedure (leg joints)

Do this after the leg is built and the horns are on (TEST_PLAN.md 19.2), with the robot on its back on the table and
the bus powered from the bench supply (TEST_PLAN.md section 7 limits).

1. Coarse zeros first, as upstream: `scripts/find_soft_offsets.py` at 376de65 (each joint torque off, set to its zero
   by eye, offset read). Put the offsets in the duck config. Then write the angle limits with them:
   `python3 bench/set_angle_limits.py --port /dev/ttyACM0 --write` (it refuses a range that wraps).
2. Torque off the joint under test only (the others hold). Press the joint gently onto its D59 stop by hand: just
   until it stops moving, no squeeze of the TPU. Read Present Position (register 56) five times, lifting off the stop
   and pressing again each time. Use the median r.
3. offset = (r - 2048) x 2 pi / 4096 - q_ref (section 1, q_ref from the table; the right hip roll and hip pitch
   references are mirrored). Write down all five readings: their spread is the repeatability (pass 0.3 deg or less).
4. Hip yaw (no stop): both legs at the new zeros of the other joints, knees straight (0 deg), feet on the table. With the
   calipers, measure the gap between the inner edges of the two foot_bottom plates at the toe and at the heel. A hip yaw
   error e of one leg turns its foot by e: over the foot length L (about 100 mm, CAD) the toe and heel gaps differ by
   L x e (0.5 deg is 0.87 mm, calc). Turn the offsets until toe and heel gaps agree within 0.4 mm, split equally
   between the legs.
5. Put the new offsets in the duck config and write the angle limits again (step 1 command): the limits follow the
   offsets.
6. Check, all joints together: with torque off, let the duck settle into the A1b sit (TEST_PLAN.md 19.4). Read every leg
   joint: knee and ankle of both legs must read their stop angle within 0.5 deg, and left minus right (mirrored) within
   0.5 deg. Then the stand: in the stock init pose on the table, the IMU trunk roll within 0.5 deg of level (a
   mismatch of the leg zeros tilts the trunk).

## 4. Pass

- Every leg joint offset from a stop reference with a 5-press spread of 0.3 deg or less.
- Step 6: each joint reads its stop within 0.5 deg; left and right agree within 0.5 deg; trunk roll within 0.5 deg.
- If a stop reads more than 1 deg off after a print, measure the part (its contact face against the STL) before
  changing the offset: a print error is fixed in the part, not hidden in the offset.

Head joints (neck pitch, head pitch) use the same steps 2 and 3 with their TPU faces (the neck pads on the block, the head pad on the hook; a TPU face gives under the press, so press to the same light touch each time); head yaw and head roll keep the
upstream method (no D59 stop, no sit role).
