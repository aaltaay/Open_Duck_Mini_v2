# Nest finder

The function is `find_nest` in nest_find.py. It runs on one RGB frame. It does not import a simulator and it does not read a world pose.

The target is the 100 mm golden cloth disc and the pale gold ring, radius 82 mm to 235 mm. Those sizes are the nest CAD (twin/dock/nest/cad/nestcad_lib.py, CAD check only). cad/nest_v2 is not read and not written.

The field is the standard Camera Module 3: 66 deg on the long image axis and 41 deg on the short one (product brief June 2024, RP-008151-DS-1, page 5, cited). On this head the long axis is up and down (twin/camera/CAMERA_TWIN.md). A still is 4608 by 2592 (cited, page 3). Any longer side above 640 is binned, and the bin keeps the whole field. Whether 1080p crops that field is still BLOCKER.

The disc is the peak of the yellow score, `(R + G) / 2 - B`, cut relative to that peak so a gain change does not set the threshold. The ring is paler cloth on both sides of the disc, and only if that band is paler than the rest of the frame. A dark band across the middle of the lower frame is a cliff flag. A compact dark blob on the floor is an obstacle flag. Both flags are the pixels only. They are not a drop and not a map.

`sun_in_trunk` turns the disc width into metres with the pinhole (calc only) and the camera chain the caller passes in. That chain is the head joints, not the nest.

The closed loop, the batch, and the frame time are twin/dock/camera/DISC_DOCK.md.

Nothing here ran on a duck.
