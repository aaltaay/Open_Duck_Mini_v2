# Camera field on the installed head

Written 2026-11-11 11:12 PM ET. This is the camera cone from the complete-duck audit, step 2. It extends the measured Camera Module 3 seat in twin/complete3d/camera_seat.json. It does not move that seat, the screws, or the cable.

The field is a rectangular pyramid, not a round cone. The audit calls it the cone. The angles are the standard module's, from the brief cited below. Every number is labeled: cited from that brief, CAD check only, calc only, sim pass only, or BLOCKER. No frame was taken with a real camera. This file is not a pass of TEST_PLAN.md 20.9.

Script: `python3 altaay_lab/twin/complete3d/camera_cone.py`
Numbers: twin/complete3d/camera_cone.json
Figures: twin/camera/figs/

## 1. The module on the bill

BOM line E6 is the Raspberry Pi Camera Module 3, standard, with the infrared cut filter (Adafruit 5657). It is not the wide module. The brief opened for this file is Raspberry Pi Ltd, Camera Module 3 product brief, June 2024, RP-008151-DS-1:

https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf

| Item | Number | Where in the brief | Label |
|---|---|---|---|
| Sensor | Sony IMX708 | page 3 | cited |
| Sensor size | 7.4 mm diagonal | page 3 | cited |
| Pixel size | 1.4 um by 1.4 um | page 3 | cited |
| Pixel count | 4608 by 2592 | page 3, "horizontal/vertical" | cited |
| Focal length | 4.74 mm | page 5, standard column | cited |
| Diagonal field | 75 degrees | page 5, standard column | cited |
| Horizontal field | 66 degrees | page 5, and the bottom view on page 4 | cited |
| Vertical field | 41 degrees | page 5, and the side view on page 4 | cited |
| Focal ratio | F1.8 | page 5 | cited |
| Focus | 10 cm to infinity | page 5 | cited |
| Infrared cut | fitted on the standard module | page 3 and page 5 | cited |
| Board | 25 by 23.862 by 11.5 mm | page 3 and the page 4 drawing. Tolerance note on page 4: 0.2 mm | cited |
| Lens diameter | 5.75 mm | page 4 | cited |
| Board thickness callout | 1.12 mm on the side view | page 4 | cited. Read here as the board thickness. The seat file still uses a 1.0 mm stand-in and was not re-run |

Page 4 draws the 66 degree angle across the 25 mm edge and the 41 degree angle across the 23.862 mm edge.

Active area from the pixel count and the pixel size (calc only): 6.451 mm by 3.629 mm, diagonal 7.402 mm. That matches the brief's 7.4 mm diagonal.

A pinhole at 4.74 mm over that active area (calc only) is 68.5 degrees by 41.9 degrees, diagonal 76.0 degrees. The cone in this file uses the brief's 66 and 41, which is the smaller field. The corner of a 66 by 41 rectangle is 73.7 degrees (calc only). The brief states 75 degrees and rounds the three angles to whole degrees.

## 2. Which way it points on the head

CAD check only, on the seat already measured.

At the URDF zero pose the lens opening centre is (99.0, 0.1, 217.9) mm and the lens axis is world +x (camera_seat.json). The soles of the zero pose sit at z = -196.2 mm. Dropping the whole zero pose so those soles rest on z = 0 puts the opening at (99.0, 0.1, 414.1) mm. The axis stays level. The forward toe is at x = 29.3 mm, 69.7 mm behind the lens.

The 21 mm hole pitch is the 25 mm edge minus the two 2 mm margins. That pitch was measured along world z (camera_seat.json, twin/complete3d/COMPLETE3D.md). So on this head:

- The brief's horizontal axis, 66 degrees, 4608 pixels, is up and down.
- The brief's vertical axis, 41 degrees, 2592 pixels, is left and right.

The module is turned 90 degrees from the page 4 drawing, where the ribbon edge is the bottom of a landscape frame. Here the ribbon leaves toward world -y (the seat's D12 end). Image "up" in the brief points to the duck's left, not to the sky.

The head opening is 7.74 mm across, the wall is 2.5 mm, and the PCB front face is 3.2 mm behind the inner wall (camera_seat.json, CAD check only). From a pupil on the PCB front face the inner rim clears a 50.4 degree half angle (calc only), wider than the 33 degree half of the 66 degree field. The shell does not clip the brief's field. If the 11.5 mm overall depth includes the 1.12 mm board, the lens front is 4.7 mm outside the outer wall (calc only). The rays below start at the measured opening centre, not at that proud point.

BLOCKER: the brief does not mark the entrance pupil. A 5 mm shift along the axis changes an angle by under 1 degree at 0.3 m (calc only). It does not change the level-head miss at 0.3 m, which is about 21 degrees, not 1.

The seat file's board height is 24.0 mm. The drawing says 23.862 mm. The difference is 0.14 mm, inside the 0.2 mm note. The seat was not moved.

## 3. Standing, and the head pitch the walk can command

Body: URDF zero, soles on the floor, neck at 0. CAD check only. This is not the walking crouch. cliff_seat.py records a standing pose with the floor 166.8 mm under the trunk origin. This zero pose has the trunk origin 196.2 mm above the floor, 29 mm higher. That crouched pose was not rebuilt here.

The stock walk schedule writes head pitch 0 for the whole run (sim/run_stock_walk.py). The policy's own head motion during a walk was not re-run. BLOCKER for that trace.

Head pitch that was swept, on this tall body (CAD check only):

| Pitch | Why this angle | Camera height, mm | Look, deg | First floor the field sees, mm ahead of the toe |
|---|---|---|---|---|
| 0 | the walk schedule | 414.1 | 0 | 707 |
| -22 | software soft stop, servo_limits.json | 372.9 | -22 | 347 |
| -25 | printed forward stop | 366.9 | -25 | 316 |
| +17.2 | Runtime gamepad upper end, +0.3 rad (cables3d/route_cables.py) | 440.3 | +17 | 1602 |
| +36 | software soft stop, looking up | 459.9 | +36 | none. The lower ray is 3 degrees above the floor |

The Runtime gamepad also asks for -0.78 rad, which is -44.7 degrees. The printed stop is -25 degrees, so the head cannot go there.

In every row the body blocks 0 floor cells that are already inside the field (CAD check only, the grids in the figures). The beak and the chest do not cut this field. The blind spot is the angle. The feet, and the floor for about 250 mm ahead of the toe, are outside the field at every pitch above, including the forward stop. At the forward stop the first visible floor is still 316 mm ahead of the toe.

## 4. Walking up to the nest

The sun is the 100 mm gold disc. The ring is pale gold from radius 82 mm to 235 mm, cut on the wall side (56 mm from the wall, wall 190 mm past the sun). Those sizes are the nest CAD (twin/dock/nest/cad/NEST_CAD.md, CAD check only). The duck faces the sun. Range is the horizontal distance from the lens opening to the sun centre. "Seen" means the sample is inside the 66 by 41 rectangle, the body is not in the way, and the slant is past the 10 cm focus limit. The disc has 13 samples (centre and 12 on the rim). The ring has 27 samples after the wall cut.

Level head, on the centre line (CAD check only). Pixel counts are calc only, from the brief's angles and 4608 by 2592. "Across" is the left-right axis (2592 pixels). "Near to far" is the up-down axis (4608 pixels), foreshortened because the disc lies on the floor.

| Range | Toe to sun | Disc | Ring | Across, still, px | Near to far, still, px | Across if 1080p keeps the full field, px |
|---|---|---|---|---|---|---|
| 0.30 m | 370 mm | 0 of 13, below the field | 0 of 27 | 1196, not on the sensor | 634, not on the sensor | 499, not on the sensor |
| 0.50 m | 570 mm | 0 of 13, below the field | 0 of 27 | 722, not on the sensor | 394, not on the sensor | 301, not on the sensor |
| 0.75 m | 820 mm | 13 of 13 | 22 of 27 | 482 | 226 | 201 |
| 1.0 m | 1070 mm | 13 of 13 | 27 of 27 | 362 | 142 | 151 |
| 1.5 m | 1570 mm | 13 of 13 | 27 of 27 | 241 | 69 | 101 |
| 2.0 m | 2070 mm | 13 of 13 | 27 of 27 | 181 | 40 | 75 |

The level-head disc centre crosses into the field at 0.64 m in front of the lens, 0.71 m in front of the toe (calc only from the 414.1 mm height and 33 degrees). At 0.75 m the near outer ring is still partly below the field, which is why 5 of 27 ring samples miss. From 1.0 m the whole disc and the whole ring are in, and nothing on the duck hides them.

Head at the -25 degree stop, on the centre line (CAD check only):

| Range | Toe to sun | Disc | Ring | Across, still, px | Near to far, still, px |
|---|---|---|---|---|---|
| 0.30 m | 387 mm | 13 of 13 | 13 of 27 | 845 | 655 |
| 0.50 m | 587 mm | 13 of 13 | 23 of 27 | 594 | 383 |
| 0.75 m to 2.0 m | 837 mm to 2087 mm | 13 of 13 | 27 of 27 | 433 down to 184 | 211 down to 36 |

At 0.30 m with the head down, the disc is in the field and the ring is not. The ring is 470 mm across, and the left-right field is only 41 degrees. The sides of the ring fall outside. Every slant in both tables is past 100 mm, so the 10 cm focus limit is not what hides the close disc. The angle is.

A sun 250 mm to the side (the start box in twin/dock/DOCK_TWIN.md, not a nest start): at 0.30 m and 0.50 m the disc centre is outside the 41 degree field even with the head down (lateral angle 40 degrees and 27 degrees). At 1.0 m the disc is fully in and the ring is 22 of 27. At 2.0 m the disc and the ring are fully in. Same at pitch 0 and at -25 degrees for those two longer ranges.

BLOCKER: the brief lists 1080p50 and does not say whether that mode keeps the full field or crops the centre. The 1080p column above is the full-field case (pixels times 1080/2592). A centre crop would keep the still's pixel size and shrink the field. No dock program chooses a mode yet.

twin/dock/DOCK_TWIN.md section 4.1 put a camera at this seat with 66 degrees horizontal and 40.1 degrees vertical, 768 by 432. That is the brief read as a landscape frame. The installed board has the wide axis vertical. That sim camera is not this field.

## 5. Sitting on the nest

The pose is twin/sit/sit_pose.json (sim pass only): neck +25 degrees, head pitch -25 degrees, head yaw about 0, trunk 2.8 degrees nose up. The two neck angles cancel. The lens looks forward at +2.8 degrees, 286 mm above the floor (CAD check only on that pose).

The sun was placed under the seat contact, at (-125, -1, 0) mm, and 45 mm either way along the heading (the nest CAD's landing window is 45 mm, calc only in that file). The camera is at x = 43 mm and looks toward +x, so the sun is behind the lens. 0 of 13 disc samples and 0 of 27 ring samples are in the field, in all three placements. The first floor the field sees is 507 mm ahead of the toe, and the ring does not reach that far in front of a duck sitting on the sun.

While it sits facing the room, this camera does not see the gold disc or the ring. Finding the nest has to happen on the way in. After the turn, this head does not watch the cloth.

## 6. Score, in the shape of TEST_PLAN.md 20.9

Section 20.9 asks for 10 of 10 at about 1 m and about 2 m, lights on and lights dim, a low pack and a full pack: the duck reaches the sit, the charge path connects, no fall, no wall touch, no tag, and no person placing it. The pose stand-in in the nest sim does not count. Neither does this geometry.

| Set | What 20.9 requires | What this field shows | Score |
|---|---|---|---|
| about 1 m, lights on, low pack | 10 of 10 sit and charge, no fall, no wall touch | disc and ring are inside the field if the head is level and the duck faces the sun (CAD check only). No walk, no light, no pack | NOT RUN |
| about 1 m, lights dim, low pack | the same | the brief has no light model. Same geometry as the row above | NOT RUN. Light is BLOCKER |
| about 1 m, lights on, full pack | the same | pack voltage is not in this field | NOT RUN |
| about 1 m, lights dim, full pack | the same | light and pack are both absent | NOT RUN |
| about 2 m, lights on, low pack | the same | disc and ring are inside the field on the same terms as 1 m, and the disc covers 181 by 40 pixels in the still (calc only) | NOT RUN |
| about 2 m, lights dim, low pack | the same | no light model | NOT RUN. Light is BLOCKER |
| about 2 m, lights on, full pack | the same | no pack | NOT RUN |
| about 2 m, lights dim, full pack | the same | no light, no pack | NOT RUN |

Geometry at the two distances 20.9 names, on axis, level head: the target is in the field. That is not 10 sits. A tag is not required for the target to fall inside the field. This file does not find the nest, and it does not drive the duck.

## 7. What is still open

- BLOCKER: no real frame, and no rendered frame through this lens. Room light, exposure, and the look of the gold cloth are not measured.
- BLOCKER: the entrance pupil is not on the brief.
- BLOCKER: the stock policy's head pitch and the walking crouch were not re-run. The schedule commands pitch 0. The body used here is the tall zero pose.
- BLOCKER: 1080p crop or scale is not stated.
- The seat's 1.0 mm board stand-in was not updated to the 1.12 mm callout. The cone does not use the screw length.

## 8. Proposed checklist row

Not written into TWIN_CHECKLIST.md. That file is owned elsewhere.

Camera and perception. Pass line unchanged: a camera model, with the lens and the light from the Camera Module 3 brief, finds the nest with no tags, and the same model is what the dock program will run. Status: GAP. This file is the geometry only. Result: the standard module's 66 by 41 degree field is on the measured seat, with the 66 degree axis up and down (CAD check only, brief in section 1). A level head on the URDF zero sees the disc and the ring from 1 m and from 2 m, and does not see them at 0.3 m or 0.5 m. The forward stop brings the disc in at 0.3 m and still misses most of the ring. The recorded sit does not see the cloth (CAD check only, on a pose that is sim pass only). Next: frames, scored as TEST_PLAN.md 20.9. Until those frames exist the row stays GAP.

## 9. Figures

All six are CAD check only except the pixel chart, which is calc only, and the sit floor, which is CAD check only on a sim pass only pose.

- twin/camera/figs/side_cone.png. Level head and the -25 degree stop. The 0.3 m and 0.5 m marks sit in front of the level-head lower ray.
- twin/camera/figs/top_cone.png. The 41 degree left-right field. Grey rings are the 0.3 m and 0.5 m nests, which are below the up-down field at pitch 0.
- twin/camera/figs/floor_stand.png. Level head. Yellow starts about 740 mm forward. Nothing orange: the body is not in the way.
- twin/camera/figs/floor_down.png. Forward stop. Yellow starts about 350 mm forward. The feet stay in the dark band.
- twin/camera/figs/floor_sit.png. Recorded sit. Yellow starts about 540 mm forward. The nest is behind the camera, off the left of this plot.
- twin/camera/figs/pixels_range.png. Disc pixels against range. Left of the dotted line the disc is below the field, so those pixels are not recorded.
