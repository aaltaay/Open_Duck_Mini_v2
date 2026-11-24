# Disc and ring dock

2026-11-24. Simulation only. One head camera. The walk is the run D policy. The score after the sit is the gold-dome charge test from camera_dock.py (force, both stripe poles, heading under 25 deg). This is not a hardware dock and it is not the 38 of 40 card batch.

cad/nest_v2 was not edited. D61 was not edited. No bill file was edited.

## What the camera is

Standard Camera Module 3. Cited from the product brief, June 2024, RP-008151-DS-1: 66 deg and 41 deg (page 5), still 4608 by 2592 (page 3), focal length 4.74 mm (page 5). On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is the measured seat. The entrance pupil is still unmarked (BLOCKER).

The render is 320 by 556. Height is the 66 deg axis, so the width is 41 deg (calc only). That is about an 8 times bin of the still, full field, not a centre crop. The 1080p crop question stays BLOCKER.

Light is one of four rooms (day, warm, dim, cool), with an 8 percent flicker on the lamp (set point). Every frame gets read noise. Motion blur is a short box whose length is the gyro rate and the head-pitch rate times a 10 ms shutter. The 10 ms is a set point. The brief does not state a shutter. A previous frame is mixed in at 12 percent when that shift is more than 2 px, which stands in for blur between captures.

The walk leaves the head level, and the crouch puts the disc on the bottom edge. While docking, the head-pitch target is -0.35 rad, which is -20 deg, inside the -22 deg software stop (servo_limits.json). The other joints stay on the policy.

## What the camera looks at

The cloth is the nest CAD sun and ring, painted in the sim and not colliding: a 100 mm disc and a pale ring from radius 82 mm to 235 mm, cut 56 mm from the wall (CAD check only). The stripe paint is turned off in this scene because it is the same yellow as the disc. The wells still score on the stripe rule. The mat files in cad/nest_v2 are unchanged.

The finder is software/perception/nest_find.py. A fix is the disc width through the pinhole, then the head-joint chain into the trunk. The true sun is not an input on the camera path. It is the input on the privileged path, and it is the score after the sit on both paths.

## Batch

Eight starts. Four rooms. Three of the eight have a felt card on part of the ring. Three have a dark floor patch and a dark box off to the side. One try each. Limit 32 s. Same controller both ways. Sim pass only.

| Seed | Room | Cover | Side hazard | Camera | Privileged |
|---|---|---|---|---|---|
| 1 | day | no | no | docked, 17.8 s, yaw err 21.4 deg | docked, 16.2 s, yaw err 24.9 deg |
| 2 | warm | no | yes | timeout | heading, yaw err 38.5 deg |
| 3 | dim | yes | no | docked, 17.2 s, yaw err 1.7 deg | docked, 17.5 s, yaw err 6.3 deg |
| 4 | cool | no | no | heading, yaw err 27.6 deg | heading, yaw err 30.6 deg |
| 5 | day | yes | yes | timeout | heading, yaw err 34.3 deg |
| 6 | warm | no | no | timeout | docked, 18.6 s, yaw err 9.1 deg |
| 7 | dim | no | yes | timeout | heading, yaw err 37.5 deg |
| 8 | cool | yes | no | no marker | docked, 24.4 s, yaw err 19.1 deg |

Camera charging: 2 of 8. Privileged charging: 4 of 8. Sim pass only.

On the two camera docks the median range error against the true sun, while the disc was in frame, was -8 mm and -7 mm (sim pass only). Seed 1 saw the disc on 0.300 of frames. Seed 3, with the felt card on the ring, still docked. A new disc fix waits 0.10 s before the controller uses it. An obstacle on the image right gets a left yaw. A creep stops when the frame says cliff.

The earlier gold-dome batch is 38 of 40 charging (sim pass only, SEAT_CONTACTS.md). That run used the wall card and the room card, other starts, and two retries. It is not this controller.

## Frame time

Perception only. The MuJoCo render is not in this number. It is not a Pi.

| | Value | Label |
|---|---|---|
| Median of the eight episode medians | 6.04 ms | measured on this x86 host, reported at 2400 MHz |
| Warm-room episodes | 14.23 ms and 15.26 ms | measured on this x86 host |
| Fastest episode median | 3.63 ms | measured on this x86 host |

Pi 5, 2 GB, is a 2.4 GHz quad Cortex-A76 (cited, software/pi_fit/BOARDS.md, the product page). The clocks match this host's reported 2400 MHz, so a same-work-per-clock copy of 6.04 ms is calc only and is a floor, not a Pi time. This Xeon core does more work per clock than an A76. A factor of 4 is an assumption, not a cited benchmark: 6.04 times 4 is 24.2 ms (calc only). A measured frame on a Pi 5 is BLOCKER. 24.2 ms is on the autonomy thread, not the 50 Hz walk thread (AUTONOMY.md).

## Where it misses

- Warm light. Seeds 2 and 6 almost never kept a fix (saw fraction 0.006 and 0.002). The lamp pulls the floor toward the cloth, and the yellow peak is no longer the disc. The privileged path does not use color, and seed 6 docked.
- A start that is not already facing the nest. Seeds 5, 7, and 8 spin. The disc does not stay in frame long enough to walk in. Seed 8 saw nothing. The privileged path still knows the sun: seeds 6 and 8 docked, and 5 and 7 sat with the heading short.
- The half turn. Four privileged sits and the camera sit on seed 4 missed the 25 deg heading gate (yaw error 27.6 to 38.5 deg). The gait's yaw dies if the turn starts too close to the wall, so the turn starts at 0.42 m of trunk-to-sun (set point). It does not always finish.
- Dim-room flags. Seed 3 docked and also marked a cliff on 87 frames and an obstacle on 83 frames (sim pass only). The flag is not a reliable stop in that light. The side hazard is not on the walk line.
- Day seed 1 marked an obstacle on 27 frames and still docked. Same caution.

## A printed mark, study only

A mark would help the two misses the cloth cannot cover: a warm lamp, and a search that starts facing away. The nest CAD's wall card is 40 mm and is not approved (NEST_V2.md). The old mast carried three AprilTags (dock BOM K13). Neither is on the mat this loop uses. A high-contrast printed mark on the wall, not on the felt, would stay a different color from the floor under a warm lamp and would be visible while the duck turns. This file does not add it. nest_v2 stays as approved.

## Pictures

Both are sim. The video is the seed 1 camera dock, third person beside the head camera, with the disc box when the finder has it. 980 by 420, 14.3 s, 95794 bytes.

- twin/dock/camera/disc_dock_sim.mp4
- twin/dock/camera/disc_dock_result.png
- twin/dock/camera/disc_batch.json

Nothing here is a hardware pass.
