# HARDWARE_AUDIT

Last updated: 2026-11-01 2:52 PM ET (blocker pass). Question answered: "Every bracket, every washer, every item accounted for?"

Answer: every printed part, insert bore, screw hole, bearing seat and servo pocket in the upstream STLs (commit 730c14b) was measured on the box. Every item below is either measured from CAD/STL geometry or confirmed by a cited source. Anything that could not be verified is a BLOCKER with exactly what is needed to clear it (section 6). Nothing is labelled "inferred" as a final answer.

- Brackets: there are no metal brackets. All brackets are printed parts (52 prints, PRINT_CHECK.md).
- Washers: 0. No washer seats exist in the STLs; every screw seats on a flat printed face, a recess or a servo horn.
- Nuts: 0. No nut traps or hex pockets exist in the STLs.
- Inserts: 58 M3 heat-set.
- Screws: 193 to buy (189 counted per hole in section 1 plus 4 M2x4 for the camera), 84 that ship in the STS3215 bags, 6 that ship in the SG90 bags. 0 holes left without an anchor (B4, B5 cleared).
- Bearings: 3 x 6804 (20x32x7).

Method: assembly rebuilt from the URDF (Open_Duck_Mini b23317a, mini_bdx/robots/open_duck_mini_v2) and the print STLs; every cylindrical hole found by ray casting along its axis through all parts it passes (clearance, seat, anchor, pilot depth). Scripts and data: altaay_lab/audit/.

## 1. Fasteners and mechanical
Spares: 10 to 20%, or the pack minimum. "Included" = ships with a component.

| Item | Spec | Where (measured) | Need | Included | Buy | Source | US seller, pack, price | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|
| M3 heat-set insert | 5.7 mm long, 4.0 mm hole, D1 4.6 | body_middle_bottom 8, body_middle_top 8, head 12, leg_spacer 4x4=16, trunk_bottom 6, foot_bottom_pla 2x2=4, foot_top 2x2=4 | 58 | 0 | 100 | bore 3.9 to 4.2 measured; CNC Kitchen hole spec | CNC Kitchen USA, 100 pcs, $10.90 | Yes | Yes |
| M3x8 SHCS | DIN 912 A2 | into inserts where clamp + engagement fits 8 mm | 44 | 0 | 52 | screws2.json | Bolt Depot 6379, $0.06 each, $3.12 | Yes | Yes |
| M3x10 SHCS | DIN 912 A2 | into inserts with thicker clamp | 12 | 0 | 14 | screws2.json | Bolt Depot 6380, $0.84 | Yes | Yes |
| M3x12 SHCS | DIN 912 A2 | into inserts, thickest clamp | 2 | 0 | 3 | screws2.json | Bolt Depot 6381, $0.18 | Yes | Yes |
| M3x6 SHCS | DIN 912 A2 | printed parts to servo horns (drive and idle) | 88 | 0 | 100 | screws2.json | Bolt Depot 6378, $3.83 per 100 | Yes | Yes |
| M3x5 SHCS | DIN 912 A2 | horn sites where 6 mm bottoms out | 12 | 0 | 14 | screws2.json | Bolt Depot 6377, $0.70 | Yes | Yes |
| M3x6 horn centre screw | Feetech | horn to servo output, 1 per servo | 14 | 14 (servo bag) | 0 | Feetech accessory bag | n/a | n/a | BLOCKER-lite: bag split |
| M2 self-tapping (servo case) | Feetech | printed parts to servo case pilots | 66 | 66 (servo bag) | 0 | Feetech accessory bag | n/a | n/a | BLOCKER B2: the 18-screw bag split by size is not published (Seeed page lists 18 screws only); test order |
| M2x5 self-tapping | pan head, 304, METALLIXITY M2/M2.6 kit (M2x4, M2x5, M2x6, M2x8) | 2 servo sites where kit screws are too long | 2 | 0 | kit | screws2.json | Amazon B0FS13B75Y, 400 pcs, $9.49, ships from Amazon | Yes | Price yes; head fit on test order (B21) |
| M2x4 self-tapping | same kit | Camera Module 3 to head.stl: 4 blind pilots 1.65 mm, 3.1 mm deep, on 20.9 x 12.5 mm | 4 | 0 | kit | head.stl measured; Raspberry Pi Camera Module 3 drawing 21 x 12.5 mm | same kit | Yes | Pattern yes; length on test order (PCB thickness not published, B9) |
| M2.5x6 SHCS | DIN 912 A2 | Pi 4, adapter 4, BNO055 4, charger 1, speaker stand 4 (the head board.stl is the Pi footprint, B7) | 17 | 0 | 20 | MOUNTING.md | Bolt Depot 6370, $0.09 each, $1.80 | Yes | Yes |
| M2.5x8 SHCS | DIN 912 A2 | eyes 4 per side | 8 | 0 | 10 | sites_head.json | Bolt Depot 6371, $0.90 | Yes | Yes |
| M2.5x10 SHCS | DIN 912 A2 | battery_pack_lid to body_back | 4 | 0 | 5 | screws2.json | Bolt Depot 6372, $0.10 each, $0.50 | Yes | Yes: head sits proud on the lid face, clamp 5.2, engagement 4.8, no part within 1 mm of the head (B3) |
| roll_to_pitch screws | M2x6 self-tapping (STS3215 bag type) | 4 clearance 2.5 holes onto servo case pilots 1.67 mm, 4.6 mm deep | 4 | 4 (servo bag) | 0 | GLB ray cast, B4 | n/a | n/a | Geometry yes; bag count depends on B2 |
| Antenna screws | SG90 bag screws | holder to SG90 horn 2 (clearance 2.7 in 5.05 recess); SG90 tabs to head 4 (pilots 27.5 mm apart vs SG90 tab holes 27.6 mm) | 6 | 6 (SG90 bags) | 0 | GLB ray cast, B5 | n/a | n/a | Geometry yes; bag screw sizes on the test order (SG90 pack) |
| Ball bearing | 6804ZZ 20x32x7 | trunk_bottom 2 seats, head 1 seat, all 32.19 mm | 3 | 0 | 10 (pack) | CAD bearing model 19.99/32.19/7.0 | Motoforti 10-pack, $7.74 | Yes | Yes (Amazon showed 1 left, 2026-11-01) |
| Threadlocker | Loctite 243 | metal to metal horn screws only (not into PLA) | 1 | 0 | 1 | Loctite TDS | Amazon, $9.90 | Yes | Yes |

Screw total: 44 + 12 + 2 + 88 + 12 + 2 + 17 + 8 + 4 = 189 bought-type screws, plus 4 M2x4 for the camera = 193; plus 14 + 66 + 4 = 84 from the STS3215 bags; plus 6 from the SG90 bags; 0 holes without an anchor.

## 2. Printed parts
Full per-STL measurements are in PRINT_CHECK.md. Totals: PLA 15% 50 parts, 1304.0 g, 127.7 h; TPU 40% 2 parts, 35.0 g, 3.9 h. Filament bought: 2 kg PLA, 1 kg TPU.

| STL | Qty | | STL | Qty |
|---|---|---|---|---|
| battery_pack_lid | 1 | | left_antenna_holder / right_antenna_holder | 1 / 1 |
| body_back | 1 | | left_cache / right_cache | 1 / 1 |
| body_front | 1 | | left_eye / right_eye | 1 / 1 |
| body_middle_bottom | 1 | | left_roll_to_pitch / right_roll_to_pitch | 1 / 1 |
| body_middle_top | 1 | | leg_spacer | 4 |
| bulb | 2 (guide says 1, CAD has 2) | | neck_left_sheet / neck_right_sheet | 1 / 1 |
| flash_light_module | 1 | | roll_motor_bottom | 2 |
| flash_reflector_interface | 1 | | roll_motor_top | 2 |
| foot_bottom_pla | 2 | | speaker_interface | 1 |
| foot_bottom_tpu (TPU) | 2 | | speaker_stand | 1 |
| foot_side | 2 | | trunk_bottom | 1 |
| foot_top | 2 | | trunk_top | 1 |
| head | 1 | | knee_to_ankle_left_sheet | 4 |
| head_bot_sheet | 1 | | knee_to_ankle_right_sheet | 4 |
| head_pitch_to_yaw | 1 | | head_roll_mount | 1 |
| head_yaw_to_roll | 1 | | | |

## 3. Electronics and modules
Every module, its mount and screw: MOUNTING.md. Every buy line with link and price: BOM.md.

## 4. Cables, connectors, crimps
Every cable as a row (ends, part numbers, route, length, source, tool): CABLE_MAP.md. Connectors bought: 10 Molex 50-37-5033 housings, 30 Molex 08-70-1040 terminals (the one made bus lead, left ankle to neck pitch, needs 2 and 6; the Y-lead is dropped, B19), 10 XT30U pairs (1 used).

## 5. Tools
BOM.md, section "Tools (one-time)": Pinecil V2, insert tips, Engineer PA-09, Bondhus 12192 hex keys (2.0 mm for M2.5, 2.5 mm for M3 DIN 912), Klein 11057 stripper, Castle Link V4.

## 6. BLOCKERS (status after the 2026-11-01 blocker pass)
Rule: an item is CLEARED only when it was measured from the upstream CAD (print STLs at 730c14b, Tnkr GLB of the upstream assembly) or confirmed by a cited source read on 2026-11-01. Everything else stays OPEN. Items that only a real part can settle are on the "Needs test order" list (section 7, priced in BOM.md).

Totals: 10 cleared (B3, B4, B5, B7, B9, B19, B23, B25, B27, B29). 19 open, of which 13 are on the test order (B2, B6, B8, B10, B13, B14, B15, B16, B17, B18, B20, B21, B26) and 6 need a decision or a source that does not exist yet (B1, B11, B12, B22, B24, B28).

| # | Blocker | Status | How verified, or what is still needed |
|---|---|---|---|
| B1 | Upstream Onshape BOM export (fastener list) | OPEN | No public export found. Upstream issue #33 (TODO list, 2025-10-16) still lists "Complete screws information in the docs" (https://github.com/apirrone/Open_Duck_Mini/issues/33). The per-hole count in section 1 replaces it for ordering. Clearing needs an upstream fastener list. |
| B2 | STS3215 bag contents by size (18 screws) | OPEN, test order 1 | Seeed p-6338 lists 18 screws without sizes. Needs one servo opened and counted. |
| B3 | battery_pack_lid recess 4.0 vs M2.5 head 4.5 | CLEARED | Measured in the GLB: the M2.5x10 DIN 912 head sits proud on the lid face, clamp 5.2 mm, engagement 4.8 mm into the body_back pilot, no part within 1 mm of the head envelope. No STL edit and no low-head screw needed. Keep M2.5x10 (Bolt Depot 6372). |
| B4 | roll_to_pitch: 4 clearance holes, no anchor | CLEARED | Ray cast through the GLB assembly: each hole lands on an STS3215 case pilot 1.67 mm, 4.6 mm deep. Screw: M2x6 self-tapping, the servo bag type. |
| B5 | Antenna holder holes and 39.2 mm pilot spacing | CLEARED | The 39.2 mm figure was wrong. Head tab pilots measure 27.5 mm apart; SG90 tab holes 27.6 mm (GLB sg90 model). The 2 holder holes (clearance 2.7 in a 5.05 recess) land on the SG90 horn. Screws from the SG90 bags; their sizes are confirmed on the test order (SG90 pack). |
| B6 | Horn to case gap and pilot depth at the 2 M2x5 sites | OPEN, test order 1 and 4 | Real servo plus M2x5 from the METALLIXITY kit. |
| B7 | Second board.stl in the head | CLEARED | There is one board. The head board.stl is the Pi footprint (same 4 holes as the Pi Zero 2 W on 58 x 23 mm), the adapter is on trunk_top; upstream bom.csv lists one adapter. M2.5x6 count drops from 21 to 17. |
| B8 | Speaker retention and size; projector LED retention | OPEN, test order 7 and 10 | CAD speaker_top envelope 38.5 x 38.7 x 15 mm; speaker_interface has no clip or screw. Upstream ANGEEK B086JH2BTD (40 mm, 4 ohm, 3 W) is not sold on amazon.com; US equivalent uxcell B07M5K17SK (40 x 40 x 20 mm per listing). Retention needs the real speaker in a printed speaker_interface. Projector: the flash_reflector_interface seat tapers to 20.0 mm (measured); retention of the LED needs the real reflector. |
| B9 | Camera not in CAD | CLEARED (part and mount); screw length on test order 8 | head.stl has 4 blind pilots 1.65 mm, 3.1 mm deep, on 20.9 x 12.5 mm. Raspberry Pi Camera Module 3 mechanical drawing (datasheets.raspberrypi.com): 25 x 24 mm board, 4 x 2.2 mm holes 2 mm from the edges, 21 x 12.5 mm pattern, which matches. Part: Adafruit 5657 ($29.25, in stock) with Adafruit 3157 Pi Zero camera cable 150 mm ($5.95). PCB thickness is not published, so M2x4 vs M2x3 is a test-order item. |
| B10 | STS3215 connector positions not modelled | OPEN, test order 1 | Tnkr (upstream assembly docs) states both bus ports sit side by side in a slot in the bottom case, plugs from below. Exact position still needs a real servo. |
| B11 | Seats not in CAD | OPEN (narrowed) | Foot switches CLEARED: foot_top has 2 slots per foot measuring 6.4 x 19.8 mm, which equals the Omron SS datasheet body (19.8 x 6.4 x 10.2, https://omronfs.omron.com/en_US/ecb/products/pdf/en-ss.pdf); upstream says press fit (issue #14, docs/assembly_guide.md). Tnkr gives placements for the XT30 (left of the holder, standing), UBEC (head floor, right half), amp (head floor right of the speaker stand). Still open: CC BEC Pro (33 x 47 x 22 mm per Castle page) and the fuse holder have no seat; needs a lab placement and a CAD clearance check. |
| B12 | BMS fit | OPEN (decision) | Measured free envelope at the CAD BMS position: 17.75 x 47.2 x 5.33 mm. AITRIP 48 x 20 x 3.4 does NOT fit (2.25 mm too wide, 0.78 mm too long). Tnkr's HX-2S-JH20 (46.7 x 23 x 3.15 per listing) does not fit either. Upstream JZK B09VGH38Y5 (41 x 16 x 3.5, $6.89 for 5, ships from Amazon) fits if shifted about 1 mm toward body_back, but is rated 8 A working, 10 A peak, under the lab's 15 A fuse. Decision: JZK with a 7.5 A or 10 A fuse, or find a 15 A board no larger than 17.75 x 47.2 x 5.33. |
| B13 | BNO055 2472 hole spacing | OPEN, test order 5 | Sources disagree (Adafruit text 20 x 12, Eagle 21.59 x 15.24, CAD 21.9 x 14.9). Calipers on the real board. |
| B14 | Left eye pilot 2.2 vs right 2.05 | OPEN, test order 11 | Test print left_eye, try an M2.5x8. |
| B15 | Insert bore depth 5.8 vs 6.7 | OPEN, test order 12 | One insert in one printed part. |
| B16 | foot_top insert wall 1.5 mm | OPEN, test order 12 | Print with 4 perimeters, pull test. |
| B17 | Kit servo cable lengths on 10 hops | OPEN, test order 1 | Test fit at joint limits. |
| B18 | USB cable 50 cm vs 502.6 mm rule | OPEN, test order 3 | Test fit through the neck. |
| B19 | Neck chain join | CLEARED | Tnkr wiring (upstream assembly docs, "as in the creator's wiring diagram"): no splitter; adapter socket 1 to left hip yaw, socket 2 to right hip yaw; the neck chain starts from the left ankle's free bus port and runs up to neck pitch, head pitch, head yaw, head roll. Every STS3215 has 2 ports in parallel. Made lead left ankle to neck pitch: polyline 336.4 + 45.2 + 40 + 68.1 (6.81 rad) = 489.7, cut 490 mm, 2 housings and 6 terminals. Y-lead S1Y dropped. |
| B20 | IMU axis signs | OPEN, test order 5 | Tilt test with scripts/calibrate_imu.py. |
| B21 | M2x5 head fit | OPEN, test order 1 and 4 | Test fit. |
| B22 | 15 A switch that fits the body_back cutout | OPEN | The cutout holds a body of 23.4 x 7.4 x 16.8 mm. No 15 A DC switch found in that size with a datasheet and US seller. Pololu 2815 is 6 A continuous at 55 C. Tnkr uses a small SPDT slide switch on P+. Options: a switch on a lower-current line (for example a fused, switched UBEC branch plus a separate servo cut-off) or a body_back edit. Needs a decision. |
| B23 | LED type and resistor | CLEARED | Upstream bom.csv: 1 W LED beads. Tnkr (m7): two 1 W eye LEDs on GPIO27 and GPIO22, each through a 100 ohm resistor. Parts: uxcell 1 W warm white 10 pcs B07DHB13J4 ($6.89), SparkFun PRT-14493 100 ohm 20-pack ($1.50). |
| B24 | Pi Zero 2 W stock | OPEN | Out of stock online at Adafruit 2026-11-01; Micro Center is in-store only, which fails "ships to USA". Recheck at order time. |
| B25 | microSD model | CLEARED | SanDisk Ultra 32 GB SDSQUAR-032G-GN6MA, https://www.amazon.com/dp/B073JWXGNT, $21.25, in stock. |
| B26 | TPU hardness | OPEN, test order 13 | Upstream states no hardness (no issue mentions TPU). Print foot_bottom_tpu in 95A and check grip and fit. |
| B27 | Holder mid tap for the BMS balance lead | CLEARED | Tnkr m1 and m2: the holder strip makes the series link, the MID take-off goes to BMS BM with a 24 to 26 AWG lead. Solder P3 to the strap. |
| B28 | Lead lengths | OPEN (narrowed) | SG90: 250 +/- 5 mm (Miuzei B072V529YD listing): D8 fits (rule 173.2), D9 needs about 20 mm of 26 AWG extension (rule 268.0). Fuse holder FHAC0001ZXJ: 89.5 mm leads (Littelfuse product page). Still unpublished: holder, UBEC and BEC Pro leads; extensions are covered by the bought wire, so this has no cost impact. |
| B29 | Order minimums | CLEARED | Bolt Depot: "Do you have a minimum order? No" (service page). Mouser: no minimum order value for stocked parts (Ordering Options help page, read via search index, direct fetch 403). DigiKey and Newark: qty 1 allowed on every line used (pricing tables). CNC Kitchen, Adafruit, SparkFun, Seeed, Amazon: pack products, no minimum. Shipping excluded by the owner. |

## 7. Needs test order
Parts that only a real part can settle. Full list with prices and links in BOM.md, section "Needs test order". All 15 lines are BOM lines (buy them first), so the build total does not change, except the servo price break (1 at $20.00 now, 13 at $19.00 later is $267.00 vs $266.00).
