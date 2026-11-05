# PRINT_CHECK

## Note 2026-11-04 11:01 PM ET: D42 uniform screw patterns and flush caps

15 STLs in print/ rebuilt from their pre-D39 STLs (twin/holes/close_holes.py, twin/holes/HOLES_TWIN.md addendum): body_front (F071 open again, F069 closed), body_back (F027 pilot open again), head_bot_sheet and head (F084, F090 open again, F088 closed), battery_pack_lid back to its pre-D39 STL, and every plug cap fitted to the part surface (the back shell ear dimples are gone). Each output is watertight, same bounds, no overlap with any part; plug ends flush within 0.05 mm except the cases listed in the addendum (flash_light_module 522 to 525 still OPEN: a conical recess at one end). CAD check only.

## Note 2026-11-04 10:12 PM ET: D39 closed holes

16 STLs in print/ have every hole without a screw closed (twin/holes/close_holes.py, list in twin/holes/data/close_report.json): battery_pack_lid, body_back, body_front, body_middle_bottom (with the 4 ear seats), body_middle_top, bulb, flash_light_module, head, head_bot_sheet, left_eye, leg_spacer, neck_right_sheet, right_eye, speaker_interface, speaker_stand, trunk_top. Each is watertight, in its print/ frame, with the same bounds; plugs never stand proud of the old surface. The tables below are from the 730c14b STLs and are not recomputed; grams and hours of the D22 profile are in print/SLICE_SUMMARY.md.

Last updated: 2026-11-01 7:24 PM ET (print package, see the dated note). Every number below was measured on the box from the upstream STL files with trimesh and PrusaSlicer. Nothing has been printed.

## Note 2026-11-01 7:24 PM ET: print package (altaay_lab/print/)
- Grams and hours in the table and totals are now the final print settings (print/config, print/parts.csv), not the 2:15 PM run. Old against new per part: print/SLICE_SUMMARY.md. The plan, coupons and Ahmed's approval block: print/PRINT_PLAN.md.
- Settings changed: 3 walls (was 2), supports in snug style below 40 degrees (was 45, grid), Overture densities PLA 1.20 and TPU 1.216 (were 1.24 and 1.21), real speeds (TPU 25 mm/s). Overrides: 4 walls on the 7 insert parts (flag 1), outer wall first on the tight-fit parts (flags 6 and 7), 5 walls and 40% infill on the 5 neck chain parts (upstream issue 33, flag 10).
- Orientation changed: speaker_interface lies flat (flag 8). The antenna holders and speaker_interface had their axis given in a turned frame (flag 9).
- Measured again: servo pockets across the servo (flag 6), insert bore depths (flag 5), roll_motor_bottom screw head against roll_to_pitch over the hip roll range (flag 11), knee sheet servo tabs (Servo pocket column, was "none").
- Geometry columns (footprint, overhang, walls, inserts, seats) are unchanged except speaker_interface.

## Source
- Repo: apirrone/Open_Duck_Mini, folder print/.
- STL commit: 730c14bc50e4e60c4a983f57fd739e015510cc76 (730c14b, 2025-04-19 10:41:49 +0200, "adding missing stl files").
- Later commits under print/ (374bc37 2025-12-29 stand files, cf8ec64 2025-11-14 Jaime mods README) do not change the robot STLs listed here.
- Upstream print settings: docs/print_guide.md says all parts PLA at 15% infill, foot_bottom_tpu in TPU at 40% infill. The guide lists bulb x1, but the CAD assembly uses 2 (issue #26), so 2 are counted.

## Method
- Slicer (2:15 PM run, kept for comparison): PrusaSlicer CLI on the box, 256x256 bed, 0.2 mm layers, 0.4 mm nozzle, 2 perimeters, auto supports at a 45 degree threshold, density PLA 1.24 and TPU 1.21 g/cm3. Reproduced at 6:10 PM: PrusaSlicer 2.7.2 defaults plus those values, 5 top and 4 bottom layers and gyroid 15% give the old grams to 0.01 g.
- Slicer (7:24 PM, numbers in the table now): PrusaSlicer 2.7.2 CLI with print/config/printer_generic.ini (generic 0.4 mm printer, 220 bed, moderate speeds), pla_print.ini or tpu_print.ini, the Overture filament files and the overrides in print/parts.csv. Grams include supports and skirt. Grams and hours are slicer estimates, not printed results.
- Orientation: the flat face with the largest area and least overhang, chosen by trying all 6 axis directions; the axis listed is the one pointing up. For the 2 antenna holders and speaker_interface the axis is in a turned ("aligned") frame, not the STL frame (flag 9).
- Overhang: area of downward faces steeper than 45 degrees from vertical in that orientation.
- Wall: ray thickness sampled over the surface; p1 is the 1st percentile, median is typical wall.
- Inserts: blind or through bores 3.9 to 4.2 mm matched to insert sites in the assembly; wall = distance from bore edge to the nearest outer surface.
- Bearing seat: bores 32.0 to 32.4 mm. CAD bearing model is 20x32x7 (6804). Seat 32.19 mm gives 0.19 mm diametral clearance on a 32.00 bearing (slip fit, print tolerance check needed). Shaft 19.99 mm in a 20.00 bore.
- Servo pockets: the STS3215 CAD body from the assembly placed in each pocket; "max pen" is the largest interference in mm (0.10 at most). Datasheet check: Feetech STS3215 C001 datasheet (https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf, and the Feetech product page) gives 45.2 x 24.7 x 35 mm. The CAD case (3 parts, wj-wk00-0122/0123/0124) measures 45.22 x 24.72 x 35.70 mm: length and width match within 0.02 mm, height is 0.70 mm over the datasheet figure (the CAD includes the output boss). Pockets are therefore checked against a body at least as large as the datasheet servo.

## Per STL
| STL | Qty | Material/infill | Orientation | Footprint mm | Height mm | Bed fit | Overhang>45 mm2 | Wall p1/median mm | Inserts | Min insert wall | Bearing seat/shaft | Servo pocket | g each | h each | g total | h total | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| battery_pack_lid.stl | 1 | PLA 15% | -x up | 86.4x51.4 | 7.5 | 180:Y 220:Y 256:Y | 31 | 1.09/5.00 | 0 | - | 0/0 | none | 14.05 | 1.04 | 14.05 | 1.04 | ok |
| body_back.stl | 1 | PLA 15% | -x up | 125.0x110.0 | 40.0 | 180:Y 220:Y 256:Y | 9688 | 0.83/3.00 | 0 | - | 0/0 | none | 88.06 | 6.94 | 88.06 | 6.94 | ok |
| body_front.stl | 1 | PLA 15% | +x up | 143.0x110.0 | 10.0 | 180:Y 220:Y 256:Y | 0 | 3.00/10.00 | 0 | - | 0/0 | none | 60.33 | 4.22 | 60.33 | 4.22 | ok |
| body_middle_bottom.stl | 1 | PLA 15%, 4 walls | +z up | 150.0x110.0 | 86.2 | 180:Y 220:Y 256:Y | 6143 | 1.82/3.00 | 8 | 2.0 | 0/0 | none | 116.52 | 9.53 | 116.52 | 9.53 | 4 walls |
| body_middle_top.stl | 1 | PLA 15%, 4 walls | +x up | 110.0x56.8 | 150.0 | 180:Y 220:Y 256:Y | 439 | 1.67/3.00 | 8 | 1.99 | 0/0 | none | 98.95 | 7.76 | 98.95 | 7.76 | 4 walls |
| bulb.stl | 2 | PLA 15% | -x up | 35.0x35.0 | 2.0 | 180:Y 220:Y 256:Y | 0 | 0.50/2.00 | 0 | - | 0/0 | none | 2.05 | 0.17 | 4.10 | 0.34 | guide x1, CAD has 2 |
| flash_light_module.stl | 1 | PLA 15% | +x up | 41.0x31.5 | 28.0 | 180:Y 220:Y 256:Y | 152 | 0.75/8.40 | 0 | - | 0/0 | none | 9.13 | 0.87 | 9.13 | 0.87 | ok |
| flash_reflector_interface.stl | 1 | PLA 15% | +x up | 23.0x23.0 | 12.7 | 180:Y 220:Y 256:Y | 136 | 1.00/2.79 | 0 | - | 0/0 | none | 2.57 | 0.25 | 2.57 | 0.25 | ok |
| foot_bottom_pla.stl | 2 | PLA 15%, 4 walls | -z up | 93.0x27.7 | 8.0 | 180:Y 220:Y 256:Y | 355 | 0.55/8.00 | 2 | 8.35 | 0/0 | none | 10.89 | 0.85 | 21.78 | 1.70 | 4 walls; blind bore, coupon C3 |
| foot_bottom_tpu.stl | 2 | TPU 40% | -z up | 101.9x40.7 | 8.0 | 180:Y 220:Y 256:Y | 63 | 0.27/7.55 | 0 | - | 0/0 | none | 18.15 | 2.25 | 36.30 | 4.50 | test print T2 (B26) |
| foot_side.stl | 2 | PLA 15% | +y up | 103.5x46.0 | 12.0 | 180:Y 220:Y 256:Y | 1068 | 1.50/7.71 | 0 | - | 0/0 | none | 14.87 | 1.23 | 29.74 | 2.46 | ok |
| foot_top.stl | 2 | PLA 15%, 4 walls | -y up | 103.5x46.0 | 34.9 | 180:Y 220:Y 256:Y | 1126 | 0.95/7.71 | 2 | 1.5 | 0/0 | none | 31.63 | 2.69 | 63.26 | 5.39 | insert wall 1.5<1.6; 4 walls; coupon C2 |
| head.stl | 1 | PLA 15%, 4 walls | -z up | 199.8x197.3 | 59.4 | 180:N 220:Y 256:Y | 12468 | 1.42/3.00 | 12 | 1.99 | 1/0 | none | 262.01 | 21.96 | 262.01 | 21.96 | no 180 bed; 4 walls |
| head_bot_sheet.stl | 1 | PLA 15% | +z up | 193.8x191.6 | 3.0 | 180:N 220:Y 256:Y | 201 | 0.22/3.00 | 0 | - | 0/0 | none | 57.52 | 3.88 | 57.52 | 3.88 | no 180 bed |
| head_pitch_to_yaw.stl | 1 | PLA 40%, 5 walls | +x up | 72.0x44.9 | 32.0 | 180:Y 220:Y 256:Y | 620 | 0.80/4.00 | 0 | - | 0/0 | none | 16.57 | 1.73 | 16.57 | 1.73 | neck override, spare (G5, G6) |
| head_roll_mount.stl | 1 | PLA 40%, 5 walls | +z up | 64.7x40.0 | 15.1 | 180:Y 220:Y 256:Y | 1146 | 1.00/4.00 | 0 | - | 0/0 | yes, max pen 0.01 | 15.74 | 1.42 | 15.74 | 1.42 | outer wall first; neck override, spare (G5, G6) |
| head_yaw_to_roll.stl | 1 | PLA 40%, 5 walls | +z up | 88.0x80.0 | 42.2 | 180:Y 220:Y 256:Y | 498 | 1.33/7.45 | 0 | - | 0/0 | yes, max pen 0.10 | 29.04 | 2.81 | 29.04 | 2.81 | outer wall first; neck override, spare (G5, G6); pocket -0.10, coupon C4 |
| knee_to_ankle_left_sheet.stl | 4 | PLA 15% | -y up | 70.6x30.7 | 8.4 | 180:Y 220:Y 256:Y | 303 | 1.50/3.90 | 0 | - | 0/0 | yes, max pen 0.01 (tabs) | 6.98 | 0.64 | 27.92 | 2.58 | outer wall first; spare (G6) |
| knee_to_ankle_right_sheet.stl | 4 | PLA 15% | +y up | 70.6x30.7 | 7.2 | 180:Y 220:Y 256:Y | 190 | 0.86/3.85 | 0 | - | 0/0 | yes, max pen 0.01 (tabs) | 6.32 | 0.60 | 25.28 | 2.40 | outer wall first; spare (G6) |
| left_antenna_holder.stl | 1 | PLA 15% | +z up (aligned frame, flag 9) | 41.2x25.6 | 10.1 | 180:Y 220:Y 256:Y | 655 | 1.99/2.00 | 0 | - | 0/0 | none | 3.57 | 0.28 | 3.57 | 0.28 | spare (G6) |
| left_cache.stl | 1 | PLA 15% | -z up | 90.0x40.0 | 152.6 | 180:Y 220:Y 256:Y | 759 | 0.60/3.50 | 0 | - | 0/0 | none | 77.34 | 5.97 | 77.34 | 5.97 | ok |
| left_eye.stl | 1 | PLA 15% | +x up | 35.0x35.0 | 4.3 | 180:Y 220:Y 256:Y | 15 | 0.50/2.71 | 0 | - | 0/0 | none | 1.80 | 0.18 | 1.80 | 0.18 | test print T1 (B14) |
| left_roll_to_pitch.stl | 1 | PLA 15% | -z up | 86.1x46.9 | 30.7 | 180:Y 220:Y 256:Y | 736 | 0.77/5.00 | 0 | - | 0/0 | yes, max pen 0.10 | 24.82 | 2.31 | 24.82 | 2.31 | outer wall first; G12 screw head |
| leg_spacer.stl | 4 | PLA 15%, 4 walls | -y up | 28.1x10.0 | 36.9 | 180:Y 220:Y 256:Y | 68 | 2.24/6.97 | 4 | 2.22 | 0/0 | none | 8.83 | 1.00 | 35.32 | 3.98 | 4 walls |
| neck_left_sheet.stl | 1 | PLA 40%, 5 walls | -y up | 58.0x30.7 | 7.1 | 180:Y 220:Y 256:Y | 197 | 0.50/7.05 | 0 | - | 0/0 | yes, max pen 0.00 | 7.49 | 0.70 | 7.49 | 0.70 | neck override, spare (G5, G6) |
| neck_right_sheet.stl | 1 | PLA 40%, 5 walls | +y up | 58.0x30.7 | 5.8 | 180:Y 220:Y 256:Y | 283 | 0.52/5.85 | 0 | - | 0/0 | yes, max pen 0.00 | 6.55 | 0.61 | 6.55 | 0.61 | neck override, spare (G5, G6) |
| right_antenna_holder.stl | 1 | PLA 15% | +z up (aligned frame, flag 9) | 41.2x25.6 | 10.1 | 180:Y 220:Y 256:Y | 654 | 1.99/2.00 | 0 | - | 0/0 | none | 3.57 | 0.28 | 3.57 | 0.28 | spare (G6) |
| right_cache.stl | 1 | PLA 15% | -z up | 90.0x40.0 | 152.6 | 180:Y 220:Y 256:Y | 759 | 0.45/3.50 | 0 | - | 0/0 | none | 77.32 | 6.03 | 77.32 | 6.03 | ok |
| right_eye.stl | 1 | PLA 15% | +x up | 40.0x40.0 | 8.4 | 180:Y 220:Y 256:Y | 13 | 2.06/4.50 | 0 | - | 0/0 | none | 4.56 | 0.38 | 4.56 | 0.38 | ok |
| right_roll_to_pitch.stl | 1 | PLA 15% | -z up | 86.1x46.9 | 30.7 | 180:Y 220:Y 256:Y | 736 | 0.82/5.00 | 0 | - | 0/0 | yes, max pen 0.10 | 24.82 | 2.33 | 24.82 | 2.33 | outer wall first; G12 screw head |
| roll_motor_bottom.stl | 2 | PLA 15% | +x up | 31.4x30.7 | 32.0 | 180:Y 220:Y 256:Y | 292 | 1.50/2.97 | 0 | - | 0/0 | yes, max pen -0.00 | 8.75 | 0.72 | 17.50 | 1.43 | spare (G6); G12 screw head |
| roll_motor_top.stl | 2 | PLA 15% | -z up | 38.0x28.7 | 20.0 | 180:Y 220:Y 256:Y | 533 | 0.33/7.74 | 0 | - | 0/0 | yes, max pen 0.01 | 8.00 | 0.80 | 16.00 | 1.60 | outer wall first |
| speaker_interface.stl | 1 | PLA 15% | flat (vector, see flag 8) | 37.8x37.8 | 6.2 | 180:Y 220:Y 256:Y | 13 | 1.15/1.50 | 0 | - | 0/0 | none | 2.33 | 0.22 | 2.33 | 0.22 | laid flat |
| speaker_stand.stl | 1 | PLA 15% | -z up | 51.4x46.0 | 47.4 | 180:Y 220:Y 256:Y | 340 | 1.50/3.00 | 0 | - | 0/0 | none | 10.11 | 1.16 | 10.11 | 1.16 | ok |
| trunk_bottom.stl | 1 | PLA 15%, 4 walls | +z up | 108.0x54.4 | 73.7 | 180:Y 220:Y 256:Y | 149 | 1.06/25.26 | 6 | 3.63 | 2/0 | none | 41.99 | 3.54 | 41.99 | 3.54 | 4 walls; outer wall first; seat coupon C1 |
| trunk_top.stl | 1 | PLA 15% | +z up | 125.5x100.7 | 41.0 | 180:Y 220:Y 256:Y | 4338 | 1.56/9.18 | 0 | - | 0/0 | yes, max pen 0.10 | 75.08 | 6.14 | 75.08 | 6.14 | outer wall first |

- PLA: 50 parts, 1372.7 g, 114.4 h (2:15 PM run: 1304.0 g, 127.7 h)
- TPU 40%: 2 parts, 36.3 g, 4.5 h (2:15 PM run: 35.0 g, 3.9 h)
## Totals
| Material | Parts | Grams | Hours | 2:15 PM run grams | 2:15 PM run hours |
|---|---|---|---|---|---|
| PLA (15%, insert parts 4 walls, neck parts 40%) | 50 | 1372.7 | 114.4 | 1304.0 | 127.7 |
| TPU 40% | 2 | 36.3 | 4.5 | 35.0 | 3.9 |
| Total | 52 | 1409.0 | 118.9 | 1339.0 | 131.6 |

Support material is 90.4 g of the 1409.0 g. Spares (one set, flag 10): 10 PLA parts, 104.6 g, 9.8 h. Coupon session: 27.8 g PLA and 18.2 g TPU, 5.0 h (print/PRINT_PLAN.md).

Filament to buy: PLA needed with coupons and spares is 1502 g; plus 15% for failed prints is 1.73 kg, so still 2 x 1 kg PLA. TPU 36 g, so 1 x 1 kg (smallest common spool).

## Printer fit
- 180x180 bed (for example Prusa Mini, Bambu A1 mini): fails head.stl (199.8x197.3; 202.3x196.8 with its supports and skirt) and head_bot_sheet.stl (193.8x191.6). Everything else fits (largest other print: body_middle_bottom, 159.6x111.2 with supports and skirt).
- 220x220 and 256x256 beds: all 36 STLs fit (this line said 38 before; print/ has 36 robot STLs, 52 parts, as the table shows); every plate in print/PRINT_PLAN.md was sliced as one job and checked inside the bed.

## Flags
1. foot_top.stl: insert wall 1.5 mm, below the 1.6 mm minimum CNC Kitchen gives for M3 inserts. Use 4 perimeters on that part or accept and test pull-out. BLOCKER-lite: test one printed foot_top. 7:24 PM: done in the package: all 7 insert parts print with 4 walls (about 1.67 mm solid round each bore; the 1.5 mm wall is filled completely), and coupon C2 (2 bosses cut from foot_top) carries the pull test.
2. head.stl and head_bot_sheet.stl need a bed of at least 200x198 mm. 7:24 PM: the head with its snug supports and skirt needs 202.3x196.8 mm; it fits a 220 bed. Organic supports would push it past 220 (that is why the base support style is snug).
3. Thin features under 0.8 mm (p1 wall): head_bot_sheet 0.22, foot_bottom_tpu 0.27, roll_motor_top 0.33, right_cache 0.45, bulb 0.50, left_eye 0.50, neck_left_sheet 0.50, neck_right_sheet 0.52, foot_bottom_pla 0.55, left_cache 0.60. These are chamfers and edges at the 1st percentile, not structural walls (medians are 2 to 8 mm), but a 0.4 mm nozzle will drop features under 0.4 mm. 7:24 PM: with the Arachne wall generator (min feature 0.1 mm, min bead 0.34 mm) these edges print, slightly thicker than CAD; nothing to do.
4. Large support areas (overhang over 1000 mm2): head 12468, body_back 9688, body_middle_bottom 6143, trunk_top 4338, head_roll_mount 1146, foot_top 1126, foot_side 1068. Plan support material and time. 7:24 PM: sliced support grams: head 29.55, body_middle_bottom 14.74, body_middle_top 8.48, body_back 8.13, trunk_top 7.79, all parts 90.4 g (old settings 208.1 g).
5. Insert bore depth: some blind bores are 5.8 mm deep for a 5.7 mm insert (0.1 mm margin) where others are 6.7 mm. Check molten plastic pushed ahead of the insert does not block the bore. 7:24 PM, measured again in every STL: every M3 insert bore is a 4.0 mm cylinder 5.8 mm deep, except 4 in head at 6.0 mm. No bore is 6.7 mm deep (that figure was not found in any STL). What differs is what lies beyond: foot_bottom_pla (2 per part) is blind, the cylinder ends in a drill point cone with its tip at 6.93 mm and a 1.06 mm floor; the 4 head bores at 6.0 mm are blind with a cone to 7.04 mm; all others run on into a 2.0 to 3.2 mm pilot where displaced plastic can go. So foot_bottom_pla is the shallowest blind bore: coupon C3.
6. Servo pockets: maximum CAD interference 0.10 mm (head_yaw_to_roll, roll_to_pitch L/R, trunk_top). A 0.10 mm overlap may need light sanding on a real print. 7:24 PM, measured across each pocket (pocket width minus servo width, ray cast in the assembly): only head_yaw_to_roll is undersize across the servo, -0.10 mm from the floor ledge to the top arm (34.90 mm for a 35.00 mm body) in a band about 1 mm wide; roll_to_pitch L/R, trunk_top, roll_motor_top, head_roll_mount and the knee sheet tabs are line to line (0.00 to -0.02 mm), the 0.10 mm being one face overlapping while the opposite face has 0.1 to 0.2 mm gap. With 0.2 mm layers the sliced head_yaw_to_roll gap is 35.00 mm. Coupon C4 checks it; the left leg checks the others.
7. Bearing seats: 3 seats at 32.19 mm (2 in trunk_bottom, depth 5.8 with a 26.19 lip; 1 in head, depth 7.0). If the printer prints holes undersize by more than 0.19 mm, the 6804 will not drop in. 7:24 PM: the trunk_bottom seats print vertical (lip on the bed): coupon C1 checks fit and sets the hole compensation rule. The head seat prints horizontal and fills with support: check the 6804 after support removal.
8. speaker_interface: the old orientation stood it on a 48 mm2 edge, 37.6 mm tall. It now lies flat (bed contact 1122 mm2): 2.33 g, 0.22 h, no support.
9. left_antenna_holder, right_antenna_holder and speaker_interface are not square to the STL axes. The 2:15 PM audit measured them in a turned frame (largest face down), so their axis in this table is in that frame. print/parts.csv gives the up direction as a vector in the STL frame.
10. Upstream issues (altaay_lab/UPSTREAM_ISSUES.md G5, G6): a neck part breaks often (issue 33) and the offset script drives all joints to zero at once (Runtime issue 32). The 5 neck chain parts print with 5 walls and 40% infill (+13.0 g over the base profile), and one spare set of 10 parts is in the plates: the 5 neck chain parts, the 2 knee sheets, roll_motor_bottom and the 2 antenna holders (reasons in print/PRINT_PLAN.md).
11. Upstream issue 17 (UPSTREAM_ISSUES.md G12), measured: roll_motor_bottom holds the hip roll servo with 2 servo-bag M2 screws through a 1.4 mm plate, heads on a flat face. The outer screw head sits 0.31 mm from the roll_to_pitch arm; an ISO M2 pan head (4.0 x 1.6 mm, bag screw size not published, B2) overlaps the arm by 1.3 mm at every hip roll angle from -25 to +25 degrees, on both legs. The inner screw clears by 0.16 to 0.32 mm. Pass or fail check on the left leg before the right leg is assembled (print/check_hip_roll_screw.py, print/PRINT_PLAN.md step 2). No STL changed.
12. Optional, not in the totals: the antenna rods (mini_bdx/robots/open_duck_mini_v2/antenna.stl, qty 2) are in the CAD but not in print/ or the guide. Each is a 150 mm rod, 1.8 mm diameter, with a 3.8 mm bead at the tip; PLA flat 0.89 g and 6 min each (print/PRINT_PLAN.md).
