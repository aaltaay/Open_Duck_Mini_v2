# Limp sit on nest v2, then the rail comes back on

2026-11-13 ET. The servo rail is held at 0 V while the duck is docked (circuitry/SERVO_RAIL.md). The servos go limp. This note asks whether the seated nest v2 pose stays put, whether the wells stay on the foil, and how the duck stands when the rail returns.

Nothing was run on hardware. The mat is not redrawn. D61 was not edited.

## What the sheet does not give

The C001 page (idle 21 mA, no friction torque) and the C018 page (no-load 180 mA at 12 V, no friction torque) do not print an unpowered backdrive torque or a gear friction. That number is BLOCKER. TEST_PLAN 19.5 is still the bench measurement. The training model uses frictionloss 0.068 Nm and damping 0.56. Those are the Playground joint class, not the sheet.

Sole friction on felt is still BLOCKER. The floor in this sim is the sit model's 0.8, not a felt coupon.

## The run

`python3 altaay_lab/twin/sit/rail_off_sit.py --out <scratch>`, after `sit_model.py` has built that scratch from the Playground pin b9be205. MuJoCo 4.0.1. The path down is the D59 sit with the foot-pin springs off, because nest v2 has no pins. The seat contact is the collision geom of sit_seat. Sim pass only. Numbers are in rail_off_sit.json.

The wells are 3 mm on 20 mm stripes (cad/nest_v2, the mat note). Centered, the well can move (20 - 3) / 2 = 8.5 mm across a stripe before it leaves the foil (calc only). The stripes run in x, toward the wall, so y is the direction that changes stripes.

| Case | Time | Body up | Seat force, minimum | Steps with the seat over 0.2 N | Slide x, y | Head pitch, roll |
|---|---|---|---|---|---|---|
| Training friction, floor 0.8 | 20 s | 0.999 | 0.825 N | 8999 of 8999 | 0.48 mm, 0.05 mm | 2.4 deg, 0.0 deg |
| Joint friction and damping at 0, floor 0.8 | 20 s | 1.0 | 0.0 N | 0 of 8999 | 0.40 mm, 0.27 mm | 2.93 deg, 30.3 deg |
| Joint friction and floor friction at 0 | 2.27 s, then unstable | -0.96 | 0.0 N | 107 of 541 | 28.97 mm, 7.47 mm | 67.4 deg, 0.88 deg |

With the training friction the seat stays down for the whole 20 s, the lateral slide is 0.05 mm, and that is inside the 8.5 mm stripe margin. Trunk pitch ends at 2.58 deg. The nest v2 pose file is 2.79 deg. The body does not fall.

With the joint friction removed, the body still does not fall in 20 s on the 0.8 floor, and the slide stays under 8.5 mm, but the seat force is 0 N on every step after the settle and the head rolls 30.3 deg. The wells are not on the mat. The feet are what hold the duck. That is not a seated charge.

With the floor friction removed as well, the seat is already leaving by 2.27 s and the step then goes unstable. That run is not a 20 s measurement. It does show that joint stops alone, with no friction, do not hold the sit.

So a sheet-backed claim that the limp duck stays seated is BLOCKER. The only 20 s hold of the wells uses a friction the sheet does not print, on a floor that is not the felt.

## Standing back up

The order is: the commands match the pose the duck is already in, the rail turns on, one second passes with no new command, then the stand ramp runs. The soft limits sit 3 deg inside the hard stops, so the command is 3.02 deg off the measured joint on the worst axis (sim pass only).

On the training-friction sit, that one second keeps the body up (1.0) and the drift is 1.23 mm, and the seat force falls to 0 N. The wells open when the rail comes on, before the stand ramp. The ramp then reaches a trunk height of 0.199 m with the up component 0.985 and the pitch 10.09 deg (sim pass only). The duck does not fall in that sequence. The contacts do not stay seated through the moment the rail returns.

The Pi has to write those sit commands before the rail turns on. The next note is why the Pi cannot take that current from the pack.
