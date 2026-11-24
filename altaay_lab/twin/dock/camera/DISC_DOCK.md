# Disc and ring dock

2026-11-24. Simulation only. One head camera. The walk is the run D policy. The score after the sit is the gold-dome charge test from camera_dock.py (force, both stripe poles, heading under 25 deg). This is not a hardware dock and it is not the 38 of 40 card batch.

cad/nest_v2 was not edited. D61 was not edited. No bill file was edited.

## What the camera is

Standard Camera Module 3. Cited from the product brief, June 2024, RP-008151-DS-1: 66 deg and 41 deg (page 5), still 4608 by 2592 (page 3), focal length 4.74 mm (page 5). On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is the measured seat. The entrance pupil is still unmarked (BLOCKER).

The render is 320 by 556. Height is the 66 deg axis, so the width is 41 deg (calc only). That is about an 8 times bin of the still, full field, not a centre crop. The 1080p crop question stays BLOCKER.

Light is one of four rooms (day, warm, dim, cool), with an 8 percent flicker on the lamp (set point). Every frame gets read noise. Motion blur is a short box whose length is the gyro rate and the head-pitch rate times a 10 ms shutter. The 10 ms is a set point. The brief does not state a shutter. A previous frame is mixed in at 12 percent when that shift is more than 2 px, which stands in for blur between captures.

The walk leaves the head level, and the crouch puts the disc on the bottom edge. While docking, the head-pitch target is -0.35 rad, which is -20 deg, inside the -22 deg software stop (servo_limits.json). Head yaw stays a policy command during the walk. For the standing search only, the head-yaw actuator sweeps inside the software stops (-105 deg to +79 deg, same file). It is not driven while the body is also yawing. That pair tips the duck, and the gait then stops turning.

## What the camera looks at

The cloth is the nest CAD sun and ring, painted in the sim and not colliding: a 100 mm disc and a pale ring from radius 82 mm to 235 mm, cut 56 mm from the wall (CAD check only). The stripe paint is turned off in this scene because it is the same yellow as the disc. The wells still score on the stripe rule. The mat files in cad/nest_v2 are unchanged.

The finder is software/perception/nest_find.py. A fix is the disc width through the pinhole, then the head-joint chain into the trunk. The true sun is not an input on the camera path. It is the input on the privileged path, and it is the score after the sit on both paths.

## What changed after the 2 of 8 batch

Three camera misses from that batch, all still sim, all on this controller. nest_v2 was not touched.

Search. With no fix, the duck stands and sweeps the head inside the software stops, then turns the body at a rate the gait follows. A glimpse is kept for 6 s as a bearing in the trunk, and the walk goes toward that bearing. Forcing the head-yaw actuator during the body turn was dropped. It tipped the duck and the body stopped yawing.

Warm light. The frame is gray-world balanced, then scored in chromaticity (red and green shares against blue), not raw RGB. The disc has to sit in a local ring that is either brighter or more yellow than the floor just outside it. A width that would put the nest past 1.8 m is rejected. Those readings were a chip of the disc, about half the real width, and the range came out near 2 m.

Half turn. Both paths use the same loop. The turn is 3.10 rad of IMU yaw at 0.45 rad/s, with a side step that is eased off after 2.0 rad, then a short pure yaw with no side step. The side step is what walks the seat onto the foil. Leaving it on for the whole turn walks into the wall. The turn starts at 0.40 m of trunk-to-sun (set point), and only once the last bearing is near the centre line. A start with the disc still off to the right used to finish outside 25 deg.

## Round 3, same 40 starts

The twin has one head camera (onboard). Belly parts in this tree are contact metal, not a view, and there is no back-of-head camera. The final look uses the head, pitched down, while the duck still faces the disc.

Before the half turn, at the same 0.40 m gate, the loop spends up to 1.5 s on the disc centroid (lateral) and the ring ellipse angle (yaw, and only when that angle agrees with the centroid). Then it turns and crouches. A failed sit restores the walk gains, stands, and walks forward. After the half turn, forward faces the room, so that walk leaves the wall. The camera searches again and repeats the approach and the line-up. Two retries, inside the episode. Restarting the same pose from scratch was deterministic, and those retries added no docks.

Walking forward stays on below the sit gate. The old 0.14 m/s floor kept going after the duck was already inside 0.40 m, and that is what put privileged runs through the wall. The stop is now at 0.34 m, inside the gate, so the turn can still start.

The finder bins any frame whose long side is over 360 (the dock frame is 556 tall, so stride 2) and, after a fix, searches only a window around the last disc. The ring test is a window around the disc, not the whole picture.

## Batch

Same 40 poses, same rooms, same 13 covers, same 20 side hazards. Limit 70 s so a second sit has time. Sim pass only. Rows are disc_batch.json.

Camera charging: 29 of 40. Privileged charging: 25 of 40.

Before this round, on the same 40: camera 24 of 40, privileged 19 of 40.

| | Before | After |
|---|---|---|
| Camera charging | 24 of 40 | 29 of 40 |
| Privileged charging | 19 of 40 | 25 of 40 |
| Camera sat_off | 7 | 9 |
| Camera heading | 4 | 1 |
| Camera fell | 1 | 1 |
| Camera other misses | sat 2, timeout 1, missed_line 1 | none of those |
| Privileged fell | 7 | 1 |
| Day room, camera | 4 of 10 | 8 of 10 |
| Warm room, camera | 7 of 10 | 7 of 10 |
| Dim room, camera | 6 of 10 | 7 of 10 |
| Cool room, camera | 7 of 10 | 7 of 10 |

27 of the 29 camera docks were the first sit. Two were the second sit: seed 5 (day, the old sat_off at x=-0.90) and seed 14 (warm). The old batch's retries were a fresh copy of the same start, and none of them docked.

Day was the weak room because two sits were only a few centimetres short of the foil with the heading already inside 25 deg (seeds 33 and 37), one turn started off the line (seed 9), and two barely held the disc (seeds 5 and 29, saw fraction 0.004 and 0.013). The line-up at the 0.40 m gate and the second sit took day from 4 of 10 to 8 of 10. Seed 9 still walks onto the wall and falls (one camera fall, true x=0.053). Seed 29 still sits off on the second try.

The remaining camera misses are 9 sat_off, 1 heading, and 1 fall. The heading row is seed 36: contacts meet, the stored yaw error is 12.9 deg, and charging stayed false. Most sat_off poses are still facing the nest area but a half-turn short (yaw about 70 to 110 deg, trunk x about -0.45 to -0.52). Privileged misses: missed_line 5, heading 3, sat_off 3, timeout 3, fell 1. The wall falls went from 7 to 1 because the forward speed now stops inside the sit distance.

Starts at least 70 deg off the nest: 10 of 11 camera docks. Cover: 8 of 13. Side hazard: 14 of 20.

This is not the 2 of 8 batch, and it is not the 38 of 40 card dock.

## Turn-gate study, not this controller

PR 120 held the crouch until the IMU had turned a fixed 3.10 rad and the disc was behind the nose. On the same 40 starts that run charged 20 of 40 camera and 19 of 40 privileged (sim pass only). Camera sat_off went from 9 to 1, heading from 1 to 14, falls from 1 to 4, and one start timed out. The 14 heading misses sat on the foil with yaw about 137 to 155 deg. A finished half turn that starts while the duck is beside the centre line faces away from the sun, not along the room axis. The leftover angle matches atan of lateral position over range.

A follow-up, not merged, set the turn target to pi plus that atan(lateral/range) and eased the side step after it had pointed at the wall for 3.2 s. Same 40 starts: camera 24 of 40, privileged 13 of 40 (sim pass only). Camera misses were sat_off 12, heading 3, fell 1. By room, camera was day 6 of 10, warm 6 of 10, dim 5 of 10, cool 7 of 10. The median frame was 3.17 ms on this x86 host. In a four-seed probe, seeds 1, 2, and 7 docked (seed 2 had been a heading miss, seed 7 a wall fall). Seed 9 stayed a heading miss at 25.9 deg. The full 40 was 24, under the 29 of this controller, and the privileged count fell to 13 with 15 timeouts. That controller was reverted. The batch in this file is the 29 of 40 controller from before the gate.

## Back-in study, not this controller

The idea was to line up at 0.7 to 0.9 m, half-turn there, and walk backward onto the foil. The run D policy does not walk backward, so that controller was not built and the 40 starts were not re-run. The batch above is still 29 of 40 camera.

Open floor, body yaw about 180 deg, seed 1 room, 3.0 s, sim pass only. Trunk forward is the nose direction. Positive command 0.12 m/s moved the trunk 0.265 m forward and did not fall. Negative commands barely moved:

| Command vx | Trunk forward in 3.0 s | Fell |
|---|---|---|
| +0.12 m/s | +0.265 m | no |
| -0.06 m/s | -0.008 m | no |
| -0.10 m/s | -0.010 m | no |
| -0.14 m/s | -0.013 m | no |
| -0.18 m/s | -0.016 m | no |

A seat at about 0.25 m after a turn at 0.80 m needs roughly half a metre of backward travel. At about 0.005 m/s that does not happen. Adding a yaw-rate command did not start the reverse either (-0.009 m in 3.0 s at vx -0.10 m/s and wz 0.15 rad/s, no fall).

Head yaw soft stops are -105.0 deg and +79.0 deg (cited, software/servo_limits.json). The horizontal field is 41 deg (calc from the cited 66 deg vertical field). The wider stop plus half of that field reaches about 125 deg off the nose (calc only). Straight behind is 180 deg. With the body facing the room at 0.80 m, head pitch -0.35 rad, and the head yaw joint at -104.9 deg, the finder did not see the disc (sim pass only). A standing hold of that stop with the look-down pitch tipped the duck at 1.04 s. The +79 deg stop did not see the disc either. There is no back-in video, because the gait does not reverse.

## Frame time

Perception only, around find_nest. The MuJoCo render is not in this number. The call sits on the autonomy thread, not inside the 50 Hz walk step. It is not a Pi.

| | Before | After | Label |
|---|---|---|---|
| Median of the 40 camera episode medians | 11.37 ms | 2.62 ms | measured on this x86 host, reported at 2400 MHz |
| Ten warm-room episode medians | 15.99 ms to 18.63 ms | 4.22 ms to 4.63 ms | measured on this x86 host |
| Fastest episode median | 7.84 ms | 2.24 ms | measured on this x86 host |

The cut is the stride-2 bin and the window around the last disc. Hazard flags are read from the full field, not that window. One day episode after that split measured 3.51 ms (sim pass only). The 2.62 ms median is the 40-episode batch before the split.

Pi 5, 2 GB, is a 2.4 GHz quad Cortex-A76 (cited, software/pi_fit/BOARDS.md, the product page). A factor of 4 is an assumption, not a cited benchmark: 2.62 times 4 is 10.5 ms (calc only). A measured frame on a Pi 5 is BLOCKER.

## A printed mark, study only

The nest CAD's wall card is 40 mm and is not approved (NEST_V2.md). This file does not add a mark. nest_v2 stays as approved.

## Pictures

Both are sim, labeled SIM. The video is seed 5, a day start. The first sit misses. The duck stands, walks out into the room, searches again, and the second sit docks (yaw error 6.0 deg on that recording, sim pass only). Third person is beside the head camera. 980 by 420, 56.0 s, 268655 bytes.

- twin/dock/camera/disc_dock_sim.mp4
- twin/dock/camera/disc_dock_result.png
- twin/dock/camera/disc_batch.json

Nothing here is a hardware pass.
