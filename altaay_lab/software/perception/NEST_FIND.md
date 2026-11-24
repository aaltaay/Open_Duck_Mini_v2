# Nest finder

The function is `find_nest` in nest_find.py. It runs on one RGB frame. It does not import a simulator and it does not read a world pose.

The target is the 100 mm golden cloth disc and the pale gold ring, radius 82 mm to 235 mm. Those sizes are the nest CAD (twin/dock/nest/cad/nestcad_lib.py, CAD check only). cad/nest_v2 is not read and not written.

The field is the standard Camera Module 3: 66 deg on the long image axis and 41 deg on the short one (product brief June 2024, RP-008151-DS-1, page 5, cited). On this head the long axis is up and down (twin/camera/CAMERA_TWIN.md). A still is 4608 by 2592 (cited, page 3). Any longer side above 640 is binned, and the bin keeps the whole field. Whether 1080p crops that field is still BLOCKER.

The frame is gray-world balanced first, so a warm lamp divides out, then scored in chromaticity: red and green shares against blue, not raw RGB. The disc is the yellow peak. It has to sit in a local ring that is either brighter than the floor just outside it, or more yellow than that floor. Comparing the cloth to the whole picture rejected a real disc that sat low in the frame, because the wall and the window were in the average. A pinhole width that would put the nest past 1.8 m is rejected. Those hits were a chip of the disc. A dark blob whose centre is on the disc is not an obstacle. A thin dark band in the lower frame is still the cliff flag. Both flags are the pixels only. They are not a drop and not a map.

On the 40-start camera batch the dim room raised the cliff flag on 0 frames in all 10 dim starts (sim pass only, twin/dock/camera/DISC_DOCK.md). The obstacle flag was still raised.

`sun_in_trunk` turns the disc width into metres with the pinhole (calc only) and the camera chain the caller passes in. That chain is the head joints, not the nest.

The closed loop, the batch, and the frame time are twin/dock/camera/DISC_DOCK.md.

Nothing here ran on a duck.
