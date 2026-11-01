# HARDWARE_AUDIT

Last updated: 2026-11-01 2:45 PM ET. Question answered: "Every bracket, every washer, every item accounted for?"

Answer: every printed part, insert bore, screw hole, bearing seat and servo pocket in the upstream STLs (commit 730c14b) was measured on the box. Every item below is either measured from CAD/STL geometry or confirmed by a cited source. Anything that could not be verified is a BLOCKER with exactly what is needed to clear it (section 6). Nothing is labelled "inferred" as a final answer.

- Brackets: there are no metal brackets. All brackets are printed parts (52 prints, PRINT_CHECK.md).
- Washers: 0. No washer seats exist in the STLs; every screw seats on a flat printed face, a recess or a servo horn.
- Nuts: 0. No nut traps or hex pockets exist in the STLs.
- Inserts: 58 M3 heat-set.
- Screws: 193 to buy (counted per hole, section 1), 80 that ship in the STS3215 bags, and 6 holes with no anchor (BLOCKER).
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
| M2 self-tapping (servo case) | Feetech | printed parts to servo case pilots | 66 | 66 (servo bag) | 0 | Feetech accessory bag | n/a | n/a | BLOCKER: the 18-screw bag split by size is not published |
| M2x5 self-tapping | Type A pan washer head, 304 | 2 servo sites where kit screws are too long | 2 | 0 | 100 (pack) | screws2.json | IMSCREWS 100 pcs, $7.99 | Yes | Price yes; head fit not confirmed (B21) |
| M2.5x6 SHCS | DIN 912 A2 | Pi 4, adapter 4, head board 4, BNO055 4, charger 1, speaker stand 4 | 21 | 0 | 25 | MOUNTING.md | Bolt Depot 6370, $0.09 each, $2.25 | Yes | Yes |
| M2.5x8 SHCS | DIN 912 A2 | eyes 4 per side | 8 | 0 | 10 | sites_head.json | Bolt Depot 6371, $0.90 | Yes | Yes |
| M2.5x10 SHCS | DIN 912 A2 | battery_pack_lid to body_back | 4 | 0 | 5 | screws2.json | Bolt Depot 6372, $0.10 each, $0.50 | Yes | Price yes; head fit BLOCKER |
| roll_to_pitch screws | unknown | 4 clearance 2.5 holes with no anchor | 4 | ? | 0 | screws2.json | n/a | n/a | BLOCKER |
| Antenna holder screws | unknown | 2 clearance 2.7 in 5.05 recess, no anchor | 2 | ? | 0 | screws2.json | n/a | n/a | BLOCKER |
| Ball bearing | 6804ZZ 20x32x7 | trunk_bottom 2 seats, head 1 seat, all 32.19 mm | 3 | 0 | 10 (pack) | CAD bearing model 19.99/32.19/7.0 | Motoforti 10-pack, $7.74 | Yes | Yes (Amazon showed 1 left, 2026-11-01) |
| Threadlocker | Loctite 243 | metal to metal horn screws only (not into PLA) | 1 | 0 | 1 | Loctite TDS | Amazon, $9.90 | Yes | Yes |

Screw total: 44 + 12 + 2 + 88 + 12 + 2 + 21 + 8 + 4 = 193 bought-type screws, plus 14 + 66 = 80 from the servo bags, plus 6 BLOCKER holes.

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
Every cable as a row (ends, part numbers, route, length, source, tool): CABLE_MAP.md. Connectors bought: 10 Molex 50-37-5033 housings, 30 Molex 08-70-1040 terminals (Y-lead needs 3 and 9), 10 XT30U pairs (1 used).

## 5. Tools
BOM.md, section "Tools (one-time)": Pinecil V2, insert tips, Engineer PA-09, Bondhus 12192 hex keys (2.0 mm for M2.5, 2.5 mm for M3 DIN 912), Klein 11057 stripper, Castle Link V4.

## 6. BLOCKERS (what is needed to clear each)
| # | Blocker | Needed to verify |
|---|---|---|
| B1 | Upstream Onshape BOM export (fastener list) not available | Export from the public Onshape document, or ask upstream (not done: no posting) |
| B2 | STS3215 accessory bag contents by size (18 screws) | Open one bag on arrival and count by size |
| B3 | battery_pack_lid head recess 4.0 mm, smallest M2.5 head 4.5 | STL edit to 4.8 mm, or accept a proud head |
| B4 | roll_to_pitch: 4 clearance holes with no anchor | Upstream assembly photo or Onshape mate showing what they fasten to |
| B5 | Antenna holder: 2 clearance holes, no anchor; pilot spacing 39.2 mm does not match SG90 tabs | Same as B4, plus caliper on the SG90 tabs |
| B6 | Horn to case gap and pilot depth at the 2 M2x5 sites | Test fit with real servo |
| B7 | Second board.stl in the head: identity | Onshape BOM or upstream answer |
| B8 | Speaker retention and size; projector LED retention | Upstream photo or Onshape |
| B9 | Camera not in CAD | Upstream design or lab design |
| B10 | STS3215 connector positions not modelled | Measure a real servo; rerun cables.py with real positions |
| B11 | BEC Pro, UBEC, fuse holder, XT30, amplifier, foot switch seats not in CAD | Lab placement plus a clearance check in CAD |
| B12 | BMS overlaps body_back 0.80 mm and lid 0.63 mm in CAD | Measure the real BMS thickness |
| B13 | BNO055 2472 hole spacing (Adafruit text 20 x 12, Eagle 21.59 x 15.24, CAD 21.9 x 14.9) | Calipers on the real board |
| B14 | Left eye pilot 2.2 vs right 2.05 | Test print, check M2.5 bite |
| B15 | Insert bore depth 5.8 vs 6.7 where blind | Test insert in one printed part |
| B16 | foot_top insert wall 1.5 mm (minimum 1.6) | Print with 4 perimeters, pull test |
| B17 | Kit servo cable lengths on 10 hops (CABLE_MAP A) | Test fit on first leg and neck at joint limits |
| B18 | USB cable 50 cm vs 502.6 mm rule length (D1) | Test fit through the neck at joint limits |
| B19 | Y-lead topology for 3 chains on 2 sockets | Confirm how upstream joins the neck chain (upstream diagram draws a dashed join) |
| B20 | IMU axis signs | Tilt test with scripts/calibrate_imu.py |
| B21 | M2x5 head fit | Test fit |
| B22 | Power switch rated 15 A DC that fits the body_back cutout | Choose part, check datasheet and size |
| B23 | LED type and series resistor value | Choose LED, compute from forward voltage at 3.3 V |
| B24 | Pi Zero 2 W out of stock at Adafruit (2026-11-01) | Recheck stock or another authorized US reseller |
| B25 | microSD exact model | Choose and link |
| B26 | TPU hardness not stated upstream | Upstream answer or test 95A |
| B27 | Holder mid tap for BMS balance lead | Inspect holder; solder to series strap |
| B28 | Cable lead lengths of holder, UBEC, BEC, fuse holder, SG90 | Measure on arrival |
| B29 | Order minimums and shipping (Bolt Depot, Mouser, DigiKey, CNC Kitchen) | Check at checkout (not done: no purchase) |
