# PRINT_CHECK

Last updated: 2026-11-01 2:15 PM ET. Every number below was measured on the box from the upstream STL files with trimesh and PrusaSlicer. Nothing has been printed.

## Source
- Repo: apirrone/Open_Duck_Mini, folder print/.
- STL commit: 730c14bc50e4e60c4a983f57fd739e015510cc76 (730c14b, 2025-04-19 10:41:49 +0200, "adding missing stl files").
- Later commits under print/ (374bc37 2025-12-29 stand files, cf8ec64 2025-11-14 Jaime mods README) do not change the robot STLs listed here.
- Upstream print settings: docs/print_guide.md says all parts PLA at 15% infill, foot_bottom_tpu in TPU at 40% infill. The guide lists bulb x1, but the CAD assembly uses 2 (issue #26), so 2 are counted.

## Method
- Slicer: PrusaSlicer CLI on the box, 256x256 bed, 0.2 mm layers, 0.4 mm nozzle, 2 perimeters, auto supports at a 45 degree threshold, density PLA 1.24 and TPU 1.21 g/cm3. Grams and hours are slicer estimates, not printed results.
- Orientation: the flat face with the largest area and least overhang, chosen by trying all 6 axis directions; the axis listed is the one pointing up.
- Overhang: area of downward faces steeper than 45 degrees from vertical in that orientation.
- Wall: ray thickness sampled over the surface; p1 is the 1st percentile, median is typical wall.
- Inserts: blind or through bores 3.9 to 4.2 mm matched to insert sites in the assembly; wall = distance from bore edge to the nearest outer surface.
- Bearing seat: bores 32.0 to 32.4 mm. CAD bearing model is 20x32x7 (6804). Seat 32.19 mm gives 0.19 mm diametral clearance on a 32.00 bearing (slip fit, print tolerance check needed). Shaft 19.99 mm in a 20.00 bore.
- Servo pockets: the STS3215 CAD body from the assembly placed in each pocket; "max pen" is the largest interference in mm (0.10 at most). Datasheet check: Feetech STS3215 C001 datasheet (https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf, and the Feetech product page) gives 45.2 x 24.7 x 35 mm. The CAD case (3 parts, wj-wk00-0122/0123/0124) measures 45.22 x 24.72 x 35.70 mm: length and width match within 0.02 mm, height is 0.70 mm over the datasheet figure (the CAD includes the output boss). Pockets are therefore checked against a body at least as large as the datasheet servo.

## Per STL
| STL | Qty | Material/infill | Orientation | Footprint mm | Height mm | Bed fit | Overhang>45 mm2 | Wall p1/median mm | Inserts | Min insert wall | Bearing seat/shaft | Servo pocket | g each | h each | g total | h total | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| battery_pack_lid.stl | 1 | PLA 15% | -x up | 86.4x51.4 | 7.5 | 180:Y 220:Y 256:Y | 31 | 1.09/5.00 | 0 | - | 0/0 | none | 14.12 | 1.55 | 14.12 | 1.55 | ok |
| body_back.stl | 1 | PLA 15% | -x up | 125.0x110.0 | 40.0 | 180:Y 220:Y 256:Y | 9688 | 0.83/3.00 | 0 | - | 0/0 | none | 93.80 | 8.50 | 93.80 | 8.50 | ok |
| body_front.stl | 1 | PLA 15% | +x up | 143.0x110.0 | 10.0 | 180:Y 220:Y 256:Y | 0 | 3.00/10.00 | 0 | - | 0/0 | none | 59.82 | 6.08 | 59.82 | 6.08 | ok |
| body_middle_bottom.stl | 1 | PLA 15% | +z up | 150.0x110.0 | 86.2 | 180:Y 220:Y 256:Y | 6143 | 1.82/3.00 | 8 | 2.0 | 0/0 | none | 121.66 | 11.65 | 121.66 | 11.65 | ok |
| body_middle_top.stl | 1 | PLA 15% | +x up | 110.0x56.8 | 150.0 | 180:Y 220:Y 256:Y | 439 | 1.67/3.00 | 8 | 1.99 | 0/0 | none | 90.17 | 7.05 | 90.17 | 7.05 | ok |
| bulb.stl | 2 | PLA 15% | -x up | 35.0x35.0 | 2.0 | 180:Y 220:Y 256:Y | 0 | 0.50/2.00 | 0 | - | 0/0 | none | 2.12 | 0.27 | 4.24 | 0.54 | guide x1, CAD has 2 |
| flash_light_module.stl | 1 | PLA 15% | +x up | 41.0x31.5 | 28.0 | 180:Y 220:Y 256:Y | 152 | 0.75/8.40 | 0 | - | 0/0 | none | 9.66 | 1.04 | 9.66 | 1.04 | ok |
| flash_reflector_interface.stl | 1 | PLA 15% | +x up | 23.0x23.0 | 12.7 | 180:Y 220:Y 256:Y | 136 | 1.00/2.79 | 0 | - | 0/0 | none | 2.51 | 0.26 | 2.51 | 0.26 | ok |
| foot_bottom_pla.stl | 2 | PLA 15% | -z up | 93.0x27.7 | 8.0 | 180:Y 220:Y 256:Y | 355 | 0.55/8.00 | 2 | 8.35 | 0/0 | none | 9.99 | 1.07 | 19.98 | 2.14 | ok |
| foot_bottom_tpu.stl | 2 | TPU 40% | -z up | 101.9x40.7 | 8.0 | 180:Y 220:Y 256:Y | 63 | 0.27/7.55 | 0 | - | 0/0 | none | 17.49 | 1.94 | 34.98 | 3.87 | ok |
| foot_side.stl | 2 | PLA 15% | +y up | 103.5x46.0 | 12.0 | 180:Y 220:Y 256:Y | 1068 | 1.50/7.71 | 0 | - | 0/0 | none | 15.42 | 1.57 | 30.84 | 3.13 | ok |
| foot_top.stl | 2 | PLA 15% | -y up | 103.5x46.0 | 34.9 | 180:Y 220:Y 256:Y | 1126 | 0.95/7.71 | 2 | 1.5 | 0/0 | none | 24.80 | 2.31 | 49.60 | 4.61 | insert wall 1.5<1.6 |
| head.stl | 1 | PLA 15% | -z up | 199.8x197.3 | 59.4 | 180:N 220:Y 256:Y | 12468 | 1.42/3.00 | 12 | 1.99 | 1/0 | none | 240.36 | 22.78 | 240.36 | 22.78 | no 180 bed |
| head_bot_sheet.stl | 1 | PLA 15% | +z up | 193.8x191.6 | 3.0 | 180:N 220:Y 256:Y | 201 | 0.22/3.00 | 0 | - | 0/0 | none | 58.90 | 7.06 | 58.90 | 7.06 | no 180 bed |
| head_pitch_to_yaw.stl | 1 | PLA 15% | +x up | 72.0x44.9 | 32.0 | 180:Y 220:Y 256:Y | 620 | 0.80/4.00 | 0 | - | 0/0 | none | 17.78 | 2.01 | 17.78 | 2.01 | ok |
| head_roll_mount.stl | 1 | PLA 15% | +z up | 64.7x40.0 | 15.1 | 180:Y 220:Y 256:Y | 1146 | 1.00/4.00 | 0 | - | 0/0 | yes, max pen 0.01 | 12.82 | 1.38 | 12.82 | 1.38 | ok |
| head_yaw_to_roll.stl | 1 | PLA 15% | +z up | 88.0x80.0 | 42.2 | 180:Y 220:Y 256:Y | 498 | 1.33/7.45 | 0 | - | 0/0 | yes, max pen 0.10 | 22.81 | 2.39 | 22.81 | 2.39 | ok |
| knee_to_ankle_left_sheet.stl | 4 | PLA 15% | -y up | 70.6x30.7 | 8.4 | 180:Y 220:Y 256:Y | 303 | 1.50/3.90 | 0 | - | 0/0 | none | 7.13 | 0.86 | 28.52 | 3.44 | ok |
| knee_to_ankle_right_sheet.stl | 4 | PLA 15% | +y up | 70.6x30.7 | 7.2 | 180:Y 220:Y 256:Y | 190 | 0.86/3.85 | 0 | - | 0/0 | none | 6.53 | 0.81 | 26.12 | 3.24 | ok |
| left_antenna_holder.stl | 1 | PLA 15% | +z up | 41.2x25.6 | 10.1 | 180:Y 220:Y 256:Y | 655 | 1.99/2.00 | 0 | - | 0/0 | none | 5.68 | 0.57 | 5.68 | 0.57 | ok |
| left_cache.stl | 1 | PLA 15% | -z up | 90.0x40.0 | 152.6 | 180:Y 220:Y 256:Y | 759 | 0.60/3.50 | 0 | - | 0/0 | none | 61.25 | 5.68 | 61.25 | 5.68 | ok |
| left_eye.stl | 1 | PLA 15% | +x up | 35.0x35.0 | 4.3 | 180:Y 220:Y 256:Y | 15 | 0.50/2.71 | 0 | - | 0/0 | none | 1.92 | 0.23 | 1.92 | 0.23 | ok |
| left_roll_to_pitch.stl | 1 | PLA 15% | -z up | 86.1x46.9 | 30.7 | 180:Y 220:Y 256:Y | 736 | 0.77/5.00 | 0 | - | 0/0 | yes, max pen 0.10 | 25.90 | 2.56 | 25.90 | 2.56 | ok |
| leg_spacer.stl | 4 | PLA 15% | -y up | 28.1x10.0 | 36.9 | 180:Y 220:Y 256:Y | 68 | 2.24/6.97 | 4 | 2.22 | 0/0 | none | 6.82 | 0.94 | 27.28 | 3.76 | ok |
| neck_left_sheet.stl | 1 | PLA 15% | -y up | 58.0x30.7 | 7.1 | 180:Y 220:Y 256:Y | 197 | 0.50/7.05 | 0 | - | 0/0 | yes, max pen 0.00 | 6.08 | 0.70 | 6.08 | 0.70 | ok |
| neck_right_sheet.stl | 1 | PLA 15% | +y up | 58.0x30.7 | 5.8 | 180:Y 220:Y 256:Y | 283 | 0.52/5.85 | 0 | - | 0/0 | yes, max pen 0.00 | 5.71 | 0.67 | 5.71 | 0.67 | ok |
| right_antenna_holder.stl | 1 | PLA 15% | +z up | 41.2x25.6 | 10.1 | 180:Y 220:Y 256:Y | 654 | 1.99/2.00 | 0 | - | 0/0 | none | 5.67 | 0.57 | 5.67 | 0.57 | ok |
| right_cache.stl | 1 | PLA 15% | -z up | 90.0x40.0 | 152.6 | 180:Y 220:Y 256:Y | 759 | 0.45/3.50 | 0 | - | 0/0 | none | 61.27 | 5.67 | 61.27 | 5.67 | ok |
| right_eye.stl | 1 | PLA 15% | +x up | 40.0x40.0 | 8.4 | 180:Y 220:Y 256:Y | 13 | 2.06/4.50 | 0 | - | 0/0 | none | 4.37 | 0.46 | 4.37 | 0.46 | ok |
| right_roll_to_pitch.stl | 1 | PLA 15% | -z up | 86.1x46.9 | 30.7 | 180:Y 220:Y 256:Y | 736 | 0.82/5.00 | 0 | - | 0/0 | yes, max pen 0.10 | 25.86 | 2.56 | 25.86 | 2.56 | ok |
| roll_motor_bottom.stl | 2 | PLA 15% | +x up | 31.4x30.7 | 32.0 | 180:Y 220:Y 256:Y | 292 | 1.50/2.97 | 0 | - | 0/0 | yes, max pen -0.00 | 8.02 | 0.68 | 16.04 | 1.37 | ok |
| roll_motor_top.stl | 2 | PLA 15% | -z up | 38.0x28.7 | 20.0 | 180:Y 220:Y 256:Y | 533 | 0.33/7.74 | 0 | - | 0/0 | yes, max pen 0.01 | 8.27 | 0.90 | 16.54 | 1.80 | ok |
| speaker_interface.stl | 1 | PLA 15% | -x up | 37.6x6.2 | 37.6 | 180:Y 220:Y 256:Y | 93 | 1.15/1.50 | 0 | - | 0/0 | none | 4.56 | 0.61 | 4.56 | 0.61 | ok |
| speaker_stand.stl | 1 | PLA 15% | -z up | 51.4x46.0 | 47.4 | 180:Y 220:Y 256:Y | 340 | 1.50/3.00 | 0 | - | 0/0 | none | 12.35 | 1.39 | 12.35 | 1.39 | ok |
| trunk_bottom.stl | 1 | PLA 15% | +z up | 108.0x54.4 | 73.7 | 180:Y 220:Y 256:Y | 149 | 1.06/25.26 | 6 | 3.63 | 2/0 | none | 42.35 | 3.50 | 42.35 | 3.50 | ok |
| trunk_top.stl | 1 | PLA 15% | +z up | 125.5x100.7 | 41.0 | 180:Y 220:Y 256:Y | 4338 | 1.56/9.18 | 0 | - | 0/0 | yes, max pen 0.10 | 77.48 | 6.72 | 77.48 | 6.72 | ok |

- PLA 15%: 50 parts, 1304.0 g, 127.7 h
- TPU 40%: 2 parts, 35.0 g, 3.9 h
## Totals
| Material | Parts | Grams | Hours |
|---|---|---|---|
| PLA 15% | 50 | 1304.0 | 127.7 |
| TPU 40% | 2 | 35.0 | 3.9 |
| Total | 52 | 1339.0 | 131.6 |

Filament to buy: 1304 g PLA plus 15% for failed prints is 1.5 kg, so 2 x 1 kg PLA. TPU 35 g, so 1 x 1 kg (smallest common spool).

## Printer fit
- 180x180 bed (for example Prusa Mini, Bambu A1 mini): fails head.stl (199.8x197.3) and head_bot_sheet.stl (193.8x191.6). Everything else fits.
- 220x220 and 256x256 beds: all 38 STLs fit.

## Flags
1. foot_top.stl: insert wall 1.5 mm, below the 1.6 mm minimum CNC Kitchen gives for M3 inserts. Use 4 perimeters on that part or accept and test pull-out. BLOCKER-lite: test one printed foot_top.
2. head.stl and head_bot_sheet.stl need a bed of at least 200x198 mm.
3. Thin features under 0.8 mm (p1 wall): head_bot_sheet 0.22, foot_bottom_tpu 0.27, roll_motor_top 0.33, right_cache 0.45, bulb 0.50, left_eye 0.50, neck_left_sheet 0.50, neck_right_sheet 0.52, foot_bottom_pla 0.55, left_cache 0.60. These are chamfers and edges at the 1st percentile, not structural walls (medians are 2 to 8 mm), but a 0.4 mm nozzle will drop features under 0.4 mm.
4. Large support areas (overhang over 1000 mm2): head 12468, body_back 9688, body_middle_bottom 6143, trunk_top 4338, head_roll_mount 1146, foot_top 1126, foot_side 1068. Plan support material and time.
5. Insert bore depth: some blind bores are 5.8 mm deep for a 5.7 mm insert (0.1 mm margin) where others are 6.7 mm. Check molten plastic pushed ahead of the insert does not block the bore.
6. Servo pockets: maximum CAD interference 0.10 mm (head_yaw_to_roll, roll_to_pitch L/R, trunk_top). A 0.10 mm overlap may need light sanding on a real print.
7. Bearing seats: 3 seats at 32.19 mm (2 in trunk_bottom, depth 5.8 with a 26.19 lip; 1 in head, depth 7.0). If the printer prints holes undersize by more than 0.19 mm, the 6804 will not drop in.
