# Camera dock

Simulation only. The run D policy walks. The nest pose in the loop is the head camera. The true pose is the score after the sit. This is not a hardware dock, and it is not a charge.

Camera: Raspberry Pi Camera Module 3 standard, product brief June 2024, RP-008151-DS-1, page 5. Cited: 66 deg and 41 deg, focal length 4.74 mm. On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is camera_seat.json, lens opening, CAD check only. The entrance pupil is still unmarked (BLOCKER). A 5 mm shift along the axis is under 1 deg at 0.3 m (calc only, that note).

Wall mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. Room mark: 120 mm black square, red felt patch, at x = -2.20 m, centre 280 mm up, on the centre line, facing the duck. The duck walks to the wall mark, turns, and finishes the heading on the room mark so the mark stays in view. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). Both squares fit on that one sheet (calc only, 80 mm plus 120 mm). The red sheet is 0.65 USD (OnlineFabricStore, 9 by 12 inch red felt, page price shown 2026-11-15, cited). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER. The stripe stays 20 mm foil and a 5 mm gap, because a coin can bridge a narrower gap (NEST_V2.md blocker 2).

Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The detector then scales the frame so the 95th percentile is mid white, which stands in for the module's auto exposure. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.

Geometry: 20 of 20 docks put one well fully on plus and one fully on minus (sim pass only). Rate 1.00.
Charging: 0 of 20. A charge needs that geometry, at least 0.294 N (30 grams, Samtec gold guideline, 23 Sep 2022, cited) on one well of each pole, and the BQ24133 input still inside 4.5 V to 17 V after the contact drop (parts.yaml, the chip sheet). The resistance model is in the charge section below.
On the docks that met, the seat centre was a median 154.6 mm from the sun and at most 253.4 mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least 2.77 mm (calc only on the scored pose).
Time to dock, median 33.5 s, max 53.5 s (sim pass only).
No failure in this batch.
A timeout is a turn that lost the room mark, or a stop short of the foil. This policy does not walk backward, so that short stop is not walked back onto the mat. When the camera says the wells are off, the duck stays standing, steps toward the room mark, turns back to the wall, and approaches again. That retry is capped at two.

A geometric meet is one well circle inside a plus stripe and one inside a minus stripe. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.
Charge model, assumption on the pair: the foil is copper tape (BOM), and no gold-on-copper force curve was found. Clean gold is a few milliohms under 10 grams when held still (Mroczkowski, Connector Supplier, 7 Apr 2009, cited). This note uses 5 milliohms at 10 grams, scaling as 1/sqrt(force), then times 5 for dust and fuzz. The 5 milliohms and the dust factor are assumptions. The wire is 0.038 ohm for both poles (NEST_V2.md, calc only). The nest supply is 15 V and the chip window is 4.5 V to 17 V (parts.yaml, BQ24133 sheet).
The seat face and the bumper are collision boxes on the CAD bbox, and the wells are flush in that face. A dock charges only when both poles see at least 0.294 N on the well itself. The face around a well is not counted as well force. Why the wells read what they read, and why the mat was left alone, is SEAT_WELLS.md.

| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |
|---|---|---|---|---|---|---|---|
| 1 | -1.05 0.00 0 | 1.00 | docked | 29.4 | 174.0 | 6.3 | 2.91 |
| 2 | -1.20 0.22 -20 | 0.70 | docked | 34.6 | 222.9 | 4.6 | 7.03 |
| 3 | -0.90 -0.26 28 | 1.20 | docked | 23.8 | 38.4 | 12.2 | 3.11 |
| 4 | -1.40 0.10 12 | 0.50 | docked | 30.9 | 168.3 | 8.6 | 2.77 |
| 5 | -1.10 -0.16 -32 | 1.30 | docked | 21.7 | 134.7 | 12.5 | 4.12 |
| 6 | -0.85 0.28 18 | 0.80 | docked | 53.5 | 236.9 | 7.4 | 6.65 |
| 7 | -1.30 -0.30 8 | 0.60 | docked | 27.1 | 54.6 | 11.0 | 3.17 |
| 8 | -1.15 0.06 150 | 1.00 | docked | 37.3 | 101.6 | 11.1 | 3.81 |
| 9 | -1.50 0.34 -24 | 0.45 | docked | 36.1 | 253.4 | 5.3 | 5.75 |
| 10 | -1.00 -0.08 6 | 1.10 | docked | 27.8 | 148.9 | 6.8 | 5.28 |
| 11 | -1.25 -0.20 40 | 0.90 | docked | 53.1 | 73.9 | 9.2 | 7.04 |
| 12 | -0.95 0.14 -15 | 1.25 | docked | 24.5 | 228.4 | 6.3 | 3.73 |
| 13 | -1.45 -0.05 160 | 0.65 | docked | 41.0 | 114.5 | 8.7 | 7.37 |
| 14 | -1.10 0.32 -45 | 0.55 | docked | 32.9 | 250.9 | 1.4 | 5.44 |
| 15 | -1.35 0.00 90 | 1.05 | docked | 44.3 | 148.7 | 8.9 | 7.67 |
| 16 | -0.88 -0.18 22 | 0.75 | docked | 19.7 | 82.2 | 8.7 | 6.35 |
| 17 | -1.55 0.16 -90 | 1.15 | docked | 34.0 | 220.7 | 4.9 | 5.62 |
| 18 | -1.18 -0.28 12 | 0.48 | docked | 24.9 | 109.2 | 13.9 | 4.43 |
| 19 | -1.02 0.08 -160 | 0.85 | docked | 34.1 | 160.3 | 8.3 | 3.57 |
| 20 | -1.32 -0.12 35 | 1.00 | docked | 48.1 | 169.9 | 8.2 | 3.74 |

The 12 V rail is the sheet law at a held 12.0 V (sts12.py, cited stall 30 kg.cm at 12 V). The old 7.2 V aim-offset table is not in this loop.

## Second set, 20 new starts

Geometry: 19 of 20 (sim pass only). Rate 0.95. Median time 31.8 s. Median seat-to-sun 175.1 mm. Charging: 0 of 20.
The one miss never sees a mark. With the seat face in the model every well force is 0 N. The reason is SEAT_WELLS.md.

| Seed | Result | Time s | Yaw err deg | Charging | Well force N |
|---|---|---|---|---|---|
| 21 | docked | 23.3 | 8.6 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 22 | docked | 31.0 | 4.8 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 23 | docked | 21.6 | 11.5 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 24 | docked | 28.1 | 7.1 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 25 | docked | 36.2 | 7.9 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 26 | docked | 31.3 | 10.3 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 27 | docked | 31.8 | 1.0 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 28 | docked | 39.0 | 10.3 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 29 | docked | 32.4 | 6.3 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 30 | docked | 26.5 | 7.6 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 31 | docked | 36.4 | 9.3 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 32 | no_marker | 28.0 | 102.3 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 33 | docked | 36.4 | 9.0 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 34 | docked | 33.1 | 8.9 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 35 | docked | 23.9 | 8.5 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 36 | docked | 35.1 | 3.4 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 37 | docked | 41.3 | 11.0 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 38 | docked | 37.3 | 8.1 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 39 | docked | 26.5 | 7.4 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
| 40 | docked | 30.8 | 4.1 | False | [0.0, 0.0, 0.0, 0.0, 0.0] |
