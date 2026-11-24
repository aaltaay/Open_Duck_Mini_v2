# Nest finder

The function is `find_nest` in nest_find.py. It runs on one RGB frame. It does not import a simulator and it does not read a world pose.

The target is the 100 mm golden cloth disc and the pale gold ring, radius 82 mm to 235 mm. Those sizes are the nest CAD (twin/dock/nest/cad/nestcad_lib.py, CAD check only). cad/nest_v2 is not read and not written.

The field is the standard Camera Module 3: 66 deg on the long image axis and 41 deg on the short one (product brief June 2024, RP-008151-DS-1, page 5, cited). On this head the long axis is up and down (twin/camera/CAMERA_TWIN.md). A still is 4608 by 2592 (cited, page 3). Any longer side above 640 is binned, and the bin keeps the whole field. Whether 1080p crops that field is still BLOCKER.

The frame is gray-world balanced first, so a warm lamp divides out, then scored in chromaticity: red and green shares against blue, not raw RGB. The disc is the yellow peak. It has to sit in a local ring that is either brighter than the floor just outside it, or more yellow than that floor. The ring's major-axis angle is returned when the band is wide enough. Zero means the ring lies left to right, which is the yaw cue used before the half turn. A pinhole width that would put the nest past 1.8 m is rejected. Those hits were a chip of the disc. A dark blob whose centre is on the disc is not an obstacle. A thin dark band in the lower frame is still the cliff flag. Both flags are the pixels only. They are not a drop and not a map.

Any frame whose long side is over 360 is binned (set point, not a camera mode). The dock frame is 556 tall, so that bin is stride 2. After a fix, the disc search is only the window around that disc. Cliff and obstacle flags still use the full field. A miss clears the window. On the 40-start camera batch the median episode was 2.62 ms on this x86 host, down from 11.37 ms (sim pass only, twin/dock/camera/DISC_DOCK.md). One day episode after the full-field hazard split measured 3.51 ms.

`sun_in_trunk` turns the disc width into metres with the pinhole (calc only) and the camera chain the caller passes in. That chain is the head joints, not the nest.

The closed loop, the batch, and the frame time are twin/dock/camera/DISC_DOCK.md.

Nothing here ran on a duck.
