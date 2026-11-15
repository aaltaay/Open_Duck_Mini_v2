# Camera dock

Simulation only. The run D policy walks. The nest pose in the loop is the head camera. The true pose is the score after the sit. This is not a hardware dock, and it is not a charge.

Camera: Raspberry Pi Camera Module 3 standard, product brief June 2024, RP-008151-DS-1, page 5. Cited: 66 deg and 41 deg, focal length 4.74 mm. On this head the 66 deg axis is up and down (CAMERA_TWIN.md). The mount is camera_seat.json, lens opening, CAD check only. The entrance pupil is still unmarked (BLOCKER). A 5 mm shift along the axis is under 1 deg at 0.3 m (calc only, that note).

Wall mark: 80 mm black felt square, gold-foil patch toward the top, centre 350 mm up on the wall centre line. That is the nest v2 card station. The drawn card is 40 mm. At 1.5 m a 40 mm square is about 11 px on a 320-wide frame of this lens (calc only). 80 mm is what this detector keeps after blur. Room mark: 120 mm black square, red felt patch, at x = -2.20 m, centre 280 mm up, on the centre line, facing the duck. The duck walks to the wall mark, turns, and finishes the heading on the room mark so the mark stays in view. The black sheet is the Grainear 9 by 12 inch black felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). Both squares fit on that one sheet (calc only, 80 mm plus 120 mm). The red sheet is 0.65 USD (OnlineFabricStore, 9 by 12 inch red felt, page price shown 2026-11-15, cited). The gold patch is cut from the stripe foil. Foil dollars are still BLOCKER (cad/nest_v2/BOM.md). The mat felt grade is still BLOCKER. The stripe stays 20 mm foil and a 5 mm gap, because a coin can bridge a narrower gap (NEST_V2.md blocker 2).

Noise in every frame: exposure gain drawn with the light level, gaussian read noise of 3 counts, and a 3-tap blur while the body is moving. The detector then scales the frame so the 95th percentile is mid white, which stands in for the module's auto exposure. The controller uses the fix 0.10 s late. Light is a per-seed scale on the room lamp, from 0.45 to 1.30 in this batch.

Geometry: 19 of 20 docks put one well fully on plus and one fully on minus (sim pass only). Rate 0.95.
Charging: 0 of 20. A charge needs that geometry, at least 0.294 N (30 grams, Samtec gold guideline, 23 Sep 2022, cited) on one well of each pole, and the BQ24133 input still inside 4.5 V to 17 V after the contact drop (parts.yaml, the chip sheet). The resistance model is in the charge section below.
On the docks that met, the seat centre was a median 149.5 mm from the sun and at most 256.1 mm (sim pass only). That distance is the alignment error. Stripe margin, the smallest clearance of a connected well inside its 20 mm foil, was at least 2.67 mm (calc only on the scored pose).
Time to dock, median 32.9 s, max 53.5 s (sim pass only).
Failures: fell 1.
A timeout is a turn that lost the room mark, or a stop short of the foil. This policy does not walk backward, so that short stop is not walked back onto the mat. When the camera says the wells are off, the duck stays standing, steps toward the room mark, turns back to the wall, and approaches again. That retry is capped at two.

A geometric meet is one well circle inside a plus stripe and one inside a minus stripe. The sit is the recorded cute sit, knee clamped to 147 deg, then the gains go to zero.
Charge model, assumption on the pair: the foil is copper tape (BOM), and no gold-on-copper force curve was found. Clean gold is a few milliohms under 10 grams when held still (Mroczkowski, Connector Supplier, 7 Apr 2009, cited). This note uses 5 milliohms at 10 grams, scaling as 1/sqrt(force), then times 5 for dust and fuzz. The 5 milliohms and the dust factor are assumptions. The wire is 0.038 ohm for both poles (NEST_V2.md, calc only). The nest supply is 15 V and the chip window is 4.5 V to 17 V (parts.yaml, BQ24133 sheet).
In this walk model the gold wells are not collision shapes. After the sit the MuJoCo contacts are the two foot soles on the mat. No contact falls inside 6 mm of a well, so every well force is 0 N, under the 0.294 N floor, and the charger path is open. The lamp in the video stays dark for that reason. This is not a measurement of a real seat.

| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |
|---|---|---|---|---|---|---|---|
| 1 | -1.05 0.00 0 | 1.00 | docked | 29.4 | 174.7 | 6.2 | 3.06 |
| 2 | -1.20 0.22 -20 | 0.70 | fell | 27.5 | 233.4 | 179.0 | 5.0 |
| 3 | -0.90 -0.26 28 | 1.20 | docked | 24.4 | 4.0 | 13.3 | 6.28 |
| 4 | -1.40 0.10 12 | 0.50 | docked | 30.9 | 169.7 | 8.1 | 4.67 |
| 5 | -1.10 -0.16 -32 | 1.30 | docked | 21.7 | 138.1 | 12.5 | 4.0 |
| 6 | -0.85 0.28 18 | 0.80 | docked | 53.5 | 240.2 | 7.2 | 3.43 |
| 7 | -1.30 -0.30 8 | 0.60 | docked | 26.6 | 27.8 | 11.8 | 5.67 |
| 8 | -1.15 0.06 150 | 1.00 | docked | 37.3 | 101.9 | 11.1 | 3.69 |
| 9 | -1.50 0.34 -24 | 0.45 | docked | 36.1 | 256.1 | 5.2 | 3.63 |
| 10 | -1.00 -0.08 6 | 1.10 | docked | 27.8 | 149.5 | 6.9 | 4.89 |
| 11 | -1.25 -0.20 40 | 0.90 | docked | 53.1 | 76.3 | 9.2 | 7.02 |
| 12 | -0.95 0.14 -15 | 1.25 | docked | 24.5 | 231.8 | 6.1 | 3.22 |
| 13 | -1.45 -0.05 160 | 0.65 | docked | 41.0 | 116.6 | 8.8 | 7.42 |
| 14 | -1.10 0.32 -45 | 0.55 | docked | 32.9 | 253.4 | 1.3 | 2.67 |
| 15 | -1.35 0.00 90 | 1.05 | docked | 44.3 | 147.8 | 9.1 | 7.3 |
| 16 | -0.88 -0.18 22 | 0.75 | docked | 19.7 | 85.7 | 8.7 | 6.41 |
| 17 | -1.55 0.16 -90 | 1.15 | docked | 34.0 | 224.1 | 4.7 | 7.23 |
| 18 | -1.18 -0.28 12 | 0.48 | docked | 24.3 | 83.2 | 9.8 | 5.85 |
| 19 | -1.02 0.08 -160 | 0.85 | docked | 34.1 | 161.1 | 8.4 | 4.02 |
| 20 | -1.32 -0.12 35 | 1.00 | docked | 48.1 | 172.5 | 8.2 | 3.44 |

The 12 V rail is the sheet law at a held 12.0 V (sts12.py, cited stall 30 kg.cm at 12 V). The old 7.2 V aim-offset table is not in this loop.

## Second set, 20 new starts

Geometry: 19 of 20 (sim pass only). Rate 0.95. Median time 32.4 s, max 45.9 s. Median seat-to-sun 192.3 mm, at most 266.9 mm. Stripe margin at least 0.78 mm.
Charging: 0 of 20. Same force result: the wells are not pressed.
Failures: no_marker 1.
Seed 32 never sees a mark. The search yaw also walks sideways, and from that offset both marks sit outside the 41 deg field.

| Seed | Start x y yaw | Light | Result | Time s | Seat to sun mm | Yaw err deg | Margin mm |
|---|---|---|---|---|---|---|---|
| 21 | -1.12 -0.04 8 | 0.90 | docked | 23.3 | 141.9 | 8.7 | 7.51 |
| 22 | -1.28 0.18 -12 | 0.75 | docked | 34.0 | 216.8 | 4.5 | 5.78 |
| 23 | -0.98 -0.22 24 | 1.15 | docked | 22.2 | 38.1 | 12.6 | 5.33 |
| 24 | -1.42 0.08 -8 | 0.55 | docked | 28.1 | 222.7 | 6.9 | 5.67 |
| 25 | -1.06 0.12 140 | 1.00 | docked | 36.2 | 197.2 | 7.5 | 3.76 |
| 26 | -1.22 -0.30 16 | 0.65 | docked | 31.3 | 59.7 | 10.4 | 5.48 |
| 27 | -0.92 0.20 -28 | 1.20 | docked | 31.8 | 231.1 | 1.0 | 4.58 |
| 28 | -1.48 -0.10 70 | 0.85 | docked | 45.9 | 196.2 | 7.1 | 3.74 |
| 29 | -1.16 0.28 -40 | 0.50 | docked | 32.4 | 266.9 | 6.2 | 0.78 |
| 30 | -1.34 -0.16 4 | 1.05 | docked | 26.5 | 152.8 | 7.7 | 7.61 |
| 31 | -1.00 0.00 -150 | 0.80 | docked | 36.4 | 92.8 | 9.3 | 7.14 |
| 32 | -1.38 0.22 32 | 0.70 | no_marker | 28.0 | 1704.8 | 102.3 | None |
| 33 | -1.10 -0.08 110 | 1.10 | docked | 36.4 | 119.8 | 9.0 | 5.45 |
| 34 | -1.26 0.06 -6 | 0.60 | docked | 33.1 | 205.8 | 8.9 | 2.59 |
| 35 | -0.96 -0.14 20 | 1.25 | docked | 23.9 | 117.2 | 8.6 | 3.21 |
| 36 | -1.52 0.14 -70 | 0.45 | docked | 35.1 | 225.1 | 3.3 | 5.49 |
| 37 | -1.18 -0.24 48 | 0.95 | docked | 41.3 | 116.0 | 11.1 | 3.07 |
| 38 | -1.08 0.16 175 | 0.85 | docked | 37.3 | 176.1 | 7.9 | 4.71 |
| 39 | -1.30 -0.02 -18 | 1.00 | docked | 26.5 | 192.3 | 7.2 | 7.08 |
| 40 | -1.44 0.26 10 | 0.72 | docked | 30.8 | 219.8 | 4.0 | 4.7 |

