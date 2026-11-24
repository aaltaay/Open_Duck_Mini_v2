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

## Round 4, the turn gate

The run D gait's yaw dies near a right angle. A pure yaw command does not restart it once the feet have settled. The old turn left the crouch on a 22 s timeout, so the duck sat there: yaw about 70 to 110 deg, trunk x about -0.45 to -0.52, short of the foil.

The crouch now waits until two things are true. The IMU yaw since the turn started is within 0.18 rad of 3.10 rad, and the disc is behind the nose (a fresh fix with sun_fwd under -0.02 m, or the last fix carried by the IMU to a bearing past 2.2 rad). If the yaw moves less than 0.08 rad in 1 s, the loop pauses for 0.25 s and then takes one forward step with the yaw on, up to three times. If 16 s still is not enough, it takes one 0.55 s step toward the last disc bearing and tries the turn once more, then gives up and the episode walks out and searches again.

That removed the right-angle sits. Finishing the half turn is not the same as facing the room. A 180 deg turn that starts while the duck is beside the centre line faces away from the nest. The leftover angle is the offset, atan of lateral position over range. The heading misses this round sit on the foil with yaw error 25 to 42 deg and trunk y about 0.11 to 0.18 m. Camera heading misses went from 4 to 14. Camera sat_off went from 9 to 1.

Seed 36 in the previous batch had contacts_meet true, stored yaw error 12.9 deg, stripe margin 3.74 mm, and charging false. contacts_meet is the well circle on a stripe. Charging also needs the well geom itself to press at least 0.294 N on both a plus stripe and a minus stripe (30 grams, the gold-contact floor used in camera_dock.py). A 3.74 mm graze can pass the circle test and still not press the gold hard enough. That is a real contact gap, not a mislabeled heading. This round seed 36 did not sit. It timed out at x=-0.581 m with yaw error 159.1 deg.

Seed 9 last round fell at true x 0.053 m. This round it did not fall. It sat at x=-0.182 m with yaw error 37.0 deg. Four other camera starts still reached the wall (true x about 0.10 m, seeds 7, 10, 30, 32). The side step that keeps the yaw alive also walks toward the wall, and a long turn carries them onto it.

## Batch

Same 40 starts. Limit 70 s. Sim pass only. This is the batch after the full-field hazard split.

Camera charging: 20 of 40. Privileged charging: 19 of 40.

Before this gate, on the same 40: camera 29 of 40, privileged 25 of 40.

| | Before the gate | With the gate |
|---|---|---|
| Camera charging | 29 of 40 | 20 of 40 |
| Privileged charging | 25 of 40 | 19 of 40 |
| Camera sat_off | 9 | 1 |
| Camera heading | 1 | 14 |
| Camera fell | 1 | 4 |
| Camera timeout | 0 | 1 |
| Day, camera | 8 of 10 | 5 of 10 |
| Warm, camera | 7 of 10 | 4 of 10 |
| Dim, camera | 7 of 10 | 6 of 10 |
| Cool, camera | 7 of 10 | 5 of 10 |

The gate did what it was asked. It also lowered the charge count, because a finished half turn from an offset faces the nest's opposite, not the room. This is not 34 of 40, and it is not the 38 of 40 card dock.

## Frame time

Perception only, around find_nest, on the autonomy thread. The MuJoCo render is not in this number. Hazard flags use the full field. This table is the 40-episode batch after that split. It is not a Pi.

| | Value | Label |
|---|---|---|
| Median of the 40 camera episode medians | 3.38 ms | measured on this x86 host, reported at 2400 MHz |
| Ten warm-room episode medians | 4.47 ms to 5.68 ms | measured on this x86 host |
| Fastest episode median | 2.27 ms | measured on this x86 host |

The previous full-frame median, before the stride-2 bin, was 11.37 ms on the same host. Pi 5, 2 GB, is a 2.4 GHz quad Cortex-A76 (cited, software/pi_fit/BOARDS.md). A factor of 4 is an assumption, not a cited benchmark: 3.38 times 4 is 13.5 ms (calc only). A measured frame on a Pi 5 is BLOCKER.

## A printed mark, study only

The nest CAD's wall card is 40 mm and is not approved (NEST_V2.md). This file does not add a mark. nest_v2 stays as approved.

## Pictures

Both are sim, labeled SIM. The video is seed 3. Before the gate this start sat near yaw 70 deg and trunk x=-0.46 m. The crouch now waits, the turn finishes, and the sit docks (yaw error 3.9 deg on that recording, sim pass only). Third person is beside the head camera. 980 by 420, 14.0 s, 90723 bytes.

- twin/dock/camera/disc_dock_sim.mp4
- twin/dock/camera/disc_dock_result.png
- twin/dock/camera/disc_batch.json

Nothing here is a hardware pass.
