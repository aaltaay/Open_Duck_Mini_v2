# Camera dock

Simulation only. The run D policy walks. The nest pose in the loop is the head camera. The true pose is the score after the sit. This is not a hardware dock, and it is not a charge.

Camera: Raspberry Pi Camera Module 3 standard, product brief June 2024, RP-008151-DS-1, page 5. Cited: 66 deg and 41 deg, focal length 4.74 mm. On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is camera_seat.json, lens opening, CAD check only. The entrance pupil is still unmarked (BLOCKER). A 5 mm shift along the axis is under 1 deg at 0.3 m (calc only, that note).

Mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER.

Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.

The walk up to the mat uses the image. The half turn uses the gyro from the moment the mark is centred, because the mark then leaves the frame. That is why the heading at the sit is often 50 to 75 deg off facing the room (sim pass only). A meet at that heading is the well test at the pose that happened. It is not the 46 deg window, which is the heading where every stripe phase works.

Batch: 4 of 10 docks put one well fully on plus and one fully on minus (sim pass only). Rate 0.40.
On the docks that met, the seat centre was a median 143.2 mm from the sun and at most 169.9 mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least 0.44 mm (calc only on the scored pose).
Time to dock, median 21.6 s, max 22.1 s (sim pass only).
Failures: missed_line 2, no_marker 1, sat_off_stripes 3.

A meet is geometry. The well circle lies inside one foil stripe, and the two poles both occur. Contact resistance on foil, with dust, is still BLOCKER. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.

| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |
|---|---|---|---|---|---|---|---|
| 1 | -1.05 0.00 0 | 1.00 | docked | 21.5 | 145.5 | 65.6 | 2.64 |
| 2 | -1.20 0.22 -20 | 0.70 | docked | 21.5 | 140.9 | 76.6 | 0.44 |
| 3 | -0.90 -0.26 28 | 1.20 | missed_line | 19.2 | 417.3 | 171.5 | None |
| 4 | -1.40 0.10 12 | 0.50 | docked | 22.1 | 137.1 | 64.6 | 0.98 |
| 5 | -1.10 -0.16 -32 | 1.30 | sat_off_stripes | 22.7 | 193.0 | 72.1 | 0.48 |
| 6 | -0.85 0.28 18 | 0.80 | no_marker | 16.0 | 951.5 | 46.5 | None |
| 7 | -1.30 -0.30 8 | 0.60 | docked | 21.6 | 169.9 | 53.4 | 3.1 |
| 8 | -1.15 0.06 150 | 1.00 | sat_off_stripes | 28.0 | 173.5 | 60.4 | 0.8 |
| 9 | -1.50 0.34 -24 | 0.45 | missed_line | 21.8 | 425.7 | 164.7 | None |
| 10 | -1.00 -0.08 6 | 1.10 | sat_off_stripes | 21.3 | 161.1 | 67.5 | 3.71 |

The 12 V rail is the sheet law at a held 12.0 V (sts12.py, cited stall 30 kg.cm at 12 V). The old 7.2 V aim-offset table is not in this loop.
