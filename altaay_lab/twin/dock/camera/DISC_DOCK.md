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

## Batch

Forty starts. The poses are the card dock's two lists of twenty (camera_dock.py). Each start is one of the four rooms, in rotation. A felt card covers part of the ring when the seed is a multiple of 3 (13 starts). A dark floor patch and a dark box sit off to the side when the seed is even (20 starts). Limit 50 s. First try plus two retries, the same cap as the card batch (`retries < 2`). A start counts once, on the first charge. Same controller both ways. Sim pass only. Every row is disc_batch.json.

Camera charging: 24 of 40. Privileged charging: 19 of 40.

All 24 camera charges happened on the first attempt. The other 16 failed all three attempts, so the two retries did not add a dock.

Camera by room: day 4 of 10, warm 7 of 10, dim 6 of 10, cool 7 of 10. Starts whose heading was at least 70 deg off the nest: 6 of 11 camera docks, including 150 deg, 160 deg, and -150 deg. Cover on the ring: 7 of 13. Side hazard: 14 of 20.

Camera misses: sat_off 7, heading 4, sat 2, fell 1, timeout 1, missed_line 1. Privileged misses: fell 7, heading 5, missed_line 5, timeout 3, sat_off 1. The privileged path falls more. The true sun keeps a walk going after the camera has already lost the disc.

The previous published camera batch was 2 of 8, one try, on a different set of eight starts. Privileged on that set was 4 of 8 (sim pass only). This 40 is not that 8, and it is not the 38 of 40 card dock. The card dock used the wall card and the room card.

Dim light, camera path: the cliff flag was 0 frames on all 10 dim starts. The obstacle flag was not cleared. Those 10 starts raised it on 0 to 40 frames (sim pass only). Across all 40 camera episodes the median obstacle count was 46 frames.

## Frame time

Perception only, around find_nest. The MuJoCo render is not in this number. The call sits on the autonomy thread, not inside the 50 Hz walk step. It is not a Pi.

| | Value | Label |
|---|---|---|
| Median of the 40 camera episode medians | 11.37 ms | measured on this x86 host, reported at 2400 MHz |
| Ten warm-room episode medians | 15.99 ms to 18.63 ms | measured on this x86 host |
| Fastest episode median | 7.84 ms | measured on this x86 host |

Pi 5, 2 GB, is a 2.4 GHz quad Cortex-A76 (cited, software/pi_fit/BOARDS.md, the product page). The clocks match this host's reported 2400 MHz, so a same-work-per-clock copy of 11.37 ms is calc only and is a floor, not a Pi time. This Xeon core does more work per clock than an A76. A factor of 4 is an assumption, not a cited benchmark: 11.37 times 4 is 45.5 ms (calc only). A measured frame on a Pi 5 is BLOCKER.

## A printed mark, study only

The warm room and the facing-away starts both dock some of the time now, and both still miss. A wall mark would still be a different sensor, not a fix for the cloth. The nest CAD's wall card is 40 mm and is not approved (NEST_V2.md). The old mast carried three AprilTags (dock BOM K13). Neither is on the mat this loop uses. This file does not add a mark. nest_v2 stays as approved.

## Pictures

Both are sim. The video is one camera dock that starts facing away (heading 150 deg, cool room, side hazard). It opens in the search with no disc, then the head camera shows the disc box, then the half turn. Third person is beside the head camera. Labeled SIM. 980 by 420, 38.1 s, 278923 bytes.

- twin/dock/camera/disc_dock_sim.mp4
- twin/dock/camera/disc_dock_result.png
- twin/dock/camera/disc_batch.json

Nothing here is a hardware pass.
