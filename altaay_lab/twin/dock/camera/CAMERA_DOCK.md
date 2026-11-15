# Camera dock

Simulation only. The run D policy walks. The nest pose in the loop is the head camera. The true pose is the score after the sit. This is not a hardware dock, and it is not a charge.

Camera: Raspberry Pi Camera Module 3 standard, product brief June 2024, RP-008151-DS-1, page 5. Cited: 66 deg and 41 deg, focal length 4.74 mm. On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is camera_seat.json, lens opening, CAD check only. The entrance pupil is still unmarked (BLOCKER). A 5 mm shift along the axis is under 1 deg at 0.3 m (calc only, that note).

Wall mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. Room mark: 120 mm black square, red felt patch, at x = -2.20 m, centre 280 mm up, on the centre line, facing the duck. The duck walks to the wall mark, turns, and finishes the heading on the room mark so the mark stays in view. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). Both squares fit on that one sheet (calc only, 80 mm plus 120 mm). The red sheet is 0.65 USD (OnlineFabricStore, 9 by 12 inch red felt, page price shown 2026-11-15, cited). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER. The stripe stays 20 mm foil and a 5 mm gap, because a coin can bridge a narrower gap (NEST_V2.md blocker 2).

Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The detector then scales the frame so the 95th percentile is mid white, which stands in for the module's auto exposure. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.

Batch: 14 of 20 docks put one well fully on plus and one fully on minus (sim pass only). Rate 0.70.
On the docks that met, the seat centre was a median 113.4 mm from the sun and at most 215.4 mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least 2.69 mm (calc only on the scored pose).
Time to dock, median 29.8 s, max 54.8 s (sim pass only).
Failures: timeout 6.
A timeout is a turn that lost the room mark, or a stop short of the foil. This policy does not walk backward, so that short stop is not walked back onto the mat. When the camera says the wells are off, the duck stays standing, steps toward the room mark, turns back to the wall, and approaches again. That retry is capped at two.

A meet is geometry. The well circle lies inside one foil stripe, and the two poles both occur. Contact resistance on foil, with dust, is still BLOCKER. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.

| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |
|---|---|---|---|---|---|---|---|
| 1 | -1.05 0.00 0 | 1.00 | docked | 22.3 | 157.5 | 9.0 | 3.04 |
| 2 | -1.20 0.22 -20 | 0.70 | timeout | 65.0 | 415.6 | 165.9 | None |
| 3 | -0.90 -0.26 28 | 1.20 | docked | 23.3 | 52.4 | 14.8 | 5.79 |
| 4 | -1.40 0.10 12 | 0.50 | docked | 22.2 | 209.3 | 8.4 | 2.96 |
| 5 | -1.10 -0.16 -32 | 1.30 | docked | 22.4 | 120.7 | 7.3 | 6.85 |
| 6 | -0.85 0.28 18 | 0.80 | timeout | 65.0 | 404.6 | 175.3 | None |
| 7 | -1.30 -0.30 8 | 0.60 | docked | 25.4 | 32.8 | 12.4 | 2.77 |
| 8 | -1.15 0.06 150 | 1.00 | docked | 35.2 | 121.6 | 10.1 | 2.81 |
| 9 | -1.50 0.34 -24 | 0.45 | timeout | 65.0 | 225.9 | 51.0 | 6.31 |
| 10 | -1.00 -0.08 6 | 1.10 | docked | 26.5 | 91.1 | 10.3 | 6.2 |
| 11 | -1.25 -0.20 40 | 0.90 | docked | 46.5 | 106.1 | 11.3 | 7.39 |
| 12 | -0.95 0.14 -15 | 1.25 | timeout | 65.0 | 233.3 | 150.6 | None |
| 13 | -1.45 -0.05 160 | 0.65 | docked | 33.6 | 92.6 | 6.7 | 2.69 |
| 14 | -1.10 0.32 -45 | 0.55 | timeout | 65.0 | 129.6 | 74.7 | None |
| 15 | -1.35 0.00 90 | 1.05 | docked | 54.8 | 215.4 | 19.2 | 3.45 |
| 16 | -0.88 -0.18 22 | 0.75 | docked | 19.6 | 78.1 | 7.4 | 4.56 |
| 17 | -1.55 0.16 -90 | 1.15 | docked | 33.0 | 200.1 | 7.7 | 6.62 |
| 18 | -1.18 -0.28 12 | 0.48 | timeout | 65.0 | 250.3 | 13.1 | None |
| 19 | -1.02 0.08 -160 | 0.85 | docked | 34.6 | 125.6 | 10.1 | 4.78 |
| 20 | -1.32 -0.12 35 | 1.00 | docked | 48.8 | 98.6 | 7.8 | 6.45 |

The 12 V rail is the sheet law at a held 12.0 V (sts12.py, cited stall 30 kg.cm at 12 V). The old 7.2 V aim-offset table is not in this loop.
