# PRINT_PLAN: Open Duck Mini v2 stock build

Last updated: 2026-11-01 7:29 PM ET. Nothing has been printed. Nothing is printed until Ahmed approves (lab rule 4: slice summary first, then Ahmed's OK).

All grams and hours are PrusaSlicer 2.7.2 estimates made on the box for a generic 0.4 mm printer at moderate speeds (config/printer_generic.ini). They are not printed results. The real printer is not known yet; a faster printer takes fewer hours, grams change little. Material settings are maker-typical values from the Overture pages, not lab tested.

## What Ahmed approves

| Step | What | PLA g | TPU g | Hours |
|---|---|---|---|---|
| 1. Coupon session | S1: one PLA plate with 6 test pieces (2.76 h). S2: one TPU foot sole (2.25 h) | 27.8 | 18.2 | 5.0 |
| 2 and 3. Full print, 220 bed | 15 jobs: left leg first (3 plates), then 12 plates. All remaining robot parts plus 10 spares | 1474.5 | 18.1 | 126.4 |
| 2 and 3. Full print, 256 bed | Same parts in 14 jobs | 1474.6 | 18.1 | 126.6 |
| Total (220 bed) | | 1502.3 | 36.3 | 131.4 |

- Ask 1: approve step 1 (coupon session) now. Ask 2: approve steps 2 and 3 after the coupon tests pass (or with the fixes they call for).
- The robot set alone (36 STLs, 52 parts, no coupons, no spares) is PLA 1372.7 g and 114.4 h, TPU 36.3 g and 4.5 h (old PRINT_CHECK: PLA 1304.0 g and 127.7 h, TPU 35.0 g and 3.9 h). Details: SLICE_SUMMARY.md.
- Filament: 1502 g PLA of the 2 kg bought (about 500 g left for failed prints), 36 g TPU of the 1 kg bought.
- Optional, not in the totals: 2 antenna rods (in the CAD, not in print/), PLA, 1.8 g, 0.2 h.
- Session S1 is under the 3 hour target. S2 adds 2.25 h because TPU must print slowly; run it right after S1 or overnight.

## Files in this folder

| File | What it is |
|---|---|
| config/printer_generic.ini | Generic printer for estimates only: 0.4 mm nozzle, 1.75 mm, 220 x 220 bed, Marlin 2. Use your own printer profile when printing. |
| config/bed_256.ini | Bed override for 256 x 256 printers. |
| config/pla_print.ini, config/filament_easy_pla.ini | PLA print and filament settings (base for every PLA part). |
| config/tpu_print.ini, config/filament_tpu95a.ini | TPU print and filament settings (foot_bottom_tpu only). |
| config/ovr_insert.ini, ovr_fit.ini, ovr_neck.ini | Per-part overrides, loaded after the base files (see below). |
| parts.csv | Every STL: quantity, material, overrides, print up direction, left leg count, spares, reason. |
| make_coupons.py | Cuts the test coupons from the real upstream STLs into a folder you name (never into the repo) and re-measures the feature in each. |
| slice.py | Slices parts, coupons, plates and the optional antenna; writes G-code, 3MF and JSON to a folder you name; builds SLICE_SUMMARY.md. |
| check_hip_roll_screw.py | Upstream issue 17 (G12) check: sweeps hip roll and measures the screw head clearance. |
| joint_risk.py | Upstream Runtime issue 32 (G6) table: joint range, mass that swings, thinnest part at each joint. |
| SLICE_SUMMARY.md | All slice numbers, old against new. |

How to run (outputs stay outside the repo, for example in the box scratch folder):

```bash
cd altaay_lab/print
python3 make_coupons.py /tmp/odm_coupons
python3 slice.py parts    --out /tmp/odm_slice
python3 slice.py coupons  --out /tmp/odm_slice --coupons /tmp/odm_coupons
python3 slice.py plates   --out /tmp/odm_slice --bed 220     # and again with --bed 256
python3 slice.py optional --out /tmp/odm_slice
python3 slice.py summary  --out /tmp/odm_slice --md SLICE_SUMMARY.md
```

Needs PrusaSlicer 2.7.2 (CLI) and Python with trimesh, numpy, shapely, manifold3d, yourdfpy. The coupon session plate is written as a PrusaSlicer 3MF (session/S1_PLA_coupons.3mf) with each coupon's own settings, so it opens in the PrusaSlicer GUI ready to slice for your printer. The .ini files were tested with the CLI only, not imported in the GUI.

## Settings (any slicer)

| Setting | PLA (Overture Easy PLA) | TPU (Overture TPU 95A) | Why |
|---|---|---|---|
| Layer height, first layer | 0.20, 0.20 mm | 0.20, 0.20 mm | Standard for a 0.4 mm nozzle |
| Walls (perimeters) | 3 (about 1.27 mm) | 3 | Solid ring round every 2.0 mm screw pilot; old run used 2 |
| Top / bottom layers | 5 / 4 | 5 / 4 | Same as the old run |
| Infill | 15% gyroid | 40% gyroid | Upstream docs/print_guide.md |
| Supports | Auto, snug style, below 40 degrees from the bed, none under bridges, 0.2 mm gap, 2 interface layers | None | 45 degree chamfers print fine; snug stays inside the part outline (organic pushed the head print past a 220 bed) |
| Nozzle temperature | 210 first layer, then 205 C | 230 first layer, then 225 C | Maker range PLA 190 to 220 (TDS test prints 205), TPU 210 to 240 |
| Bed temperature | 60 first layer, then 55 C | 45 first layer, then 40 C | Maker range PLA 25 to 60, TPU 35 to 50 |
| Speeds | Walls 50, outer wall 35, infill 80, solid 60, top 40, bridges 30, first layer 25 mm/s | 25 mm/s (first layer 15) | Inside the maker ranges (PLA 40 to 90 mm/s TDS, TPU 20 to 40 mm/s page) |
| Retraction | 1.5 mm at 35 mm/s (maker 1 to 3 mm) | 0.8 mm at 25 mm/s (maker: off or minimal) | Use your printer's value if it has a tuned one |
| Fan | 100% from layer 2 | 50 to 100% from layer 3 | Maker: fan on |
| Elephant foot compensation | 0.15 mm | 0.10 mm | Keeps bores that open on the bed face at size |
| Hole size compensation | 0 | 0 | CAD clearances assume nominal holes; change only after coupon C1 (below) |
| Density (for grams) | 1.20 g/cm3 | 1.216 g/cm3 | Overture TDS values |

Maker sources (read 2026-11-01): https://overture3d.com/products/overture-easy-pla-3d-printer-filament and its TDS v5.1; https://overture3d.com/products/overture-tpu and its TPU 2.0 TDS. Dry TPU at 70 C for 7 h before printing (maker page).

## Per-part overrides

| Override | Settings | Parts | Why (one line) |
|---|---|---|---|
| insert | 4 walls | body_middle_bottom, body_middle_top, foot_bottom_pla, foot_top, head, leg_spacer, trunk_bottom | 4 walls put about 1.67 mm of solid plastic round each 4.0 mm insert bore (CNC Kitchen minimum 1.6 mm), and fill the 1.5 mm foot_top wall completely (B16). |
| fit | Outer wall printed first, outer wall at 25 mm/s | trunk_bottom (bearing seats), head_yaw_to_roll, head_roll_mount, left and right roll_to_pitch, roll_motor_top, trunk_top, knee_to_ankle sheets | The wall that touches the 6804 bearing (0.19 mm clearance) or the STS3215 (0.00 to 0.10 mm CAD interference) is laid at its CAD position, not pushed into the hole by the inner walls. |
| neck | 5 walls, 40% infill | neck_left_sheet, neck_right_sheet, head_pitch_to_yaw, head_yaw_to_roll, head_roll_mount | Upstream issue 33 says a neck part breaks often (part not named); walls carry most of the bending load, so 5 walls (most of these parts become solid) and 40% infill. |

trunk_bottom uses insert+fit; head_yaw_to_roll and head_roll_mount use neck+fit. Each plate below uses one profile only, so any slicer can print it with one setting.

## Print order

### Step 1: coupon session (about 5.0 h, 27.8 g PLA plus 18.2 g TPU)

S1, one PLA plate, 2.76 h, 27.8 g. Every coupon keeps the profile of the part it comes from (per-object settings in the 3MF; in another slicer set them by hand):

| ID | Cut from (upstream STL) | What it tests | Profile | g | min |
|---|---|---|---|---|---|
| C1 | trunk_bottom, the end lobe with one seat (y above 14 mm) | One 6804 seat, 32.19 mm, 5.8 mm deep, on its 26.19 mm lip, with the real ring wall (PRINT_CHECK flag 7) | insert+fit | 5.5 | 28 |
| C2a | foot_top, top 21.45 mm of the part, x 12 to 48 | Insert boss with the 1.5 mm wall (B16) and one Omron SS-10 slot 6.4 x 19.8 mm (B11) | insert | 6.3 | 38 |
| C2b | foot_top, top 10.85 mm, x below -36.2 | The second 1.5 mm insert boss (second sample) | insert | 2.1 | 14 |
| C3 | foot_bottom_pla, 18 mm slice round one bore | The shallowest insert bore: blind 4.0 x 5.8 mm cylinder plus a drill point cone (tip at 6.93 mm, 1.06 mm floor), no pilot below (B15, flag 5) | insert | 2.7 | 13 |
| C4 | head_yaw_to_roll, right arm, full height | The only servo pocket undersize across the servo: ledge to arm 34.90 mm for a 35.00 mm STS3215 body (flag 6). Also tests the neck profile | neck+fit | 9.5 | 61 |
| T1 | left_eye, whole part | Left eye pilots 2.2 mm (right eye 2.05) for M2.5x8 (B14); eye glass disc seat | base | 1.8 | 11 |

S2, TPU, 2.25 h, 18.2 g: T2 foot_bottom_tpu whole, Overture TPU 95A at 40% (B26). If it passes it is the left leg sole.

Each coupon is cut from the upstream STL with a box (make_coupons.py), keeps the part's print orientation, and is re-measured after the cut: C1 seat 32.18 mm and lip 26.18 mm; C2a and C2b bore 4.0 mm, pilot 2.0 mm, thinnest wall 1.50 mm, C2a slot 6.40 x 19.80 mm; C3 bore 4.0 mm, cylinder 5.77 mm deep; C4 ledge to arm 34.90 mm; T1 four pilots 2.19 mm.

Pass or fail, physical tests (tools: Pinecil with insert tip, calipers, 2.0 and 2.5 mm hex keys, a 5 kg weight or luggage scale, one STS3215 from test order TO1, one 6804ZZ, CNC Kitchen M3x5.7 inserts, M3x8 and M3x10, M2.5x8, Omron SS-10):

| ID | PASS when all are true | If it fails |
|---|---|---|
| C1 | Seat measures 32.10 to 32.25 mm at 2 angles 90 degrees apart. The 6804ZZ goes in by thumb (no hammer, no heat), sits flat on the lip, does not rock when pushed sideways at its top edge, and comes out with finger pressure (slip fit by design, 0.19 mm). | Tight: see "Hole size" below, reprint C1 before trunk_bottom and head. Loose (rocks): Ahmed decides (retaining compound or a smaller hole). |
| C2a, C2b | Insert goes in straight and ends flush (straight edge, no lip over 0.1 mm). The 1.5 mm side wall has no crack or bulge over 0.2 mm. An M3x10 threads in by hand; tightened with the short arm of a 2.5 mm key, the insert does not spin. 5 kg hung from the screw for 10 s: no movement. C2a: the SS-10 presses in by thumb, stays in when shaken upside down, and its lever still clicks. | B16 stays open; tell Ahmed before printing foot_top. Switch loose or too tight: note it, B11 stays open. |
| C3 | Insert reaches flush without pushing harder than on C2a, sits flush to 0.1 mm proud at most, no bulge or crack on the bed face over the bore, an M3x8 threads the full insert length by hand, 5 kg for 10 s: no movement. | B15 stays open (plastic blocks the bore); tell Ahmed before printing foot_bottom_pla. |
| C4 | Calipers: ledge to arm gap at the ledge (CAD 34.90; the G-code makes 35.00, see "Servo pockets"). The STS3215 case slides in end first between ledge and arm with firm thumb pressure, no tools, no rattle. Up to 0.2 mm tight: light sanding of the arm underside is expected (flag 6); note it. | More than 0.2 mm tight, or the support scar needs more than light sanding: hold the head parts; try a 0.15 mm support gap or 0.1 mm layers on head_yaw_to_roll and reprint C4. |
| T1 | An M2.5x8 driven into each of the 4 pilots cuts its own thread and needs clear torque, snugs firmly with the short arm of a 2.0 mm key without stripping, and the eye does not move when pulled with 4 screws in. The eye glass disc (29.6 x 1.85 mm seat) drops in and stays when tipped. | A pilot strips: B14 stays open; options for Ahmed are an M2.5 thread-forming screw or a 2.05 mm pilot (CAD change). |
| T2 | No missing layers, no blobs over 0.5 mm, lies flat on a table (no corner up over 0.5 mm). Length 101.9 and width 40.7 mm within 0.3 mm. An M3 passes both 3.4 mm holes and its head sinks fully into the 6.5 mm counterbores. Screwed to foot_bottom_pla (or to C3 for one hole) it pulls flat, gap under 0.3 mm at the edges. Grip, record only (no upstream number): on the lab floor with 1 kg on it, tilt until it slides, note the angle next to a PLA part. | Print fails: check that the TPU was dried and the printer can feed TPU at 25 mm/s (Bowden extruders may need retraction off). Fit fails: B26 stays open. |

### Step 2: left leg, for the servo fit tests (3 plates, 19.2 h, 220.1 g; the TPU sole comes from S2)

Numbers below are for a 220 bed; on a 256 bed the same plates slice within 0.1 g and 0.03 h.

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| L1-1 | base | foot_side, left_cache, roll_motor_bottom | 100.8 | 7.92 |
| L1-2 | fit | left_roll_to_pitch, knee_to_ankle_left_sheet x2, knee_to_ankle_right_sheet x2, roll_motor_top | 59.3 | 5.62 |
| L1-3 | insert | foot_top, foot_bottom_pla, leg_spacer x2 | 60.0 | 5.61 |

Checks on the left leg (one STS3215 from TO1 is enough, moved from pocket to pocket):
1. Every servo pocket (hip roll in roll_motor_bottom and roll_motor_top, hip pitch in left_roll_to_pitch, knee and ankle between the knee sheets): the servo goes in by hand, no tools, no rattle. Note any face that needed sanding and how much. In CAD (net across the servo): roll_to_pitch and roll_motor_top 0.00 mm (line to line), knee sheet tabs 0.01 mm tight, roll_motor_bottom 0.22 mm clear.
2. Upstream issue 17 (G12), roll_motor_bottom screw head against left_roll_to_pitch. CAD result first (check_hip_roll_screw.py): roll_motor_bottom holds the hip roll servo with 2 servo-bag M2 screws through a 1.4 mm plate, heads on a flat face. The outer screw head sits 0.31 mm from the roll_to_pitch arm; an M2 pan head (ISO 7045, 4.0 x 1.6 mm, the bag screw type is not published, B2) overlaps the arm by 1.3 mm at every hip roll angle from -25 to +25 degrees (URDF limits), on both legs. The inner screw clears by 0.24 to 0.32 mm (left) and 0.16 to 0.27 mm (right).
   - Test: fit roll_motor_bottom to the servo with both screws fully seated. With the horn screws not yet in, hold left_roll_to_pitch on the hip roll horns and turn it by hand from -25 to +25 degrees about the configured zero and back (or, fully assembled, step the powered servo slowly through the same range).
   - PASS: the full range with no rubbing, no clicks and no new marks on roll_to_pitch, both screws seated.
   - FAIL (expected for the outer screw from the CAD): stop, do not force it. Note which screw and at what angle. Options for Ahmed before the right leg is assembled: leave the outer screw out (the CAD has no room for any head there), or a CAD change (a relief in roll_to_pitch or a countersink in roll_motor_bottom). No STL is changed in this package.
3. Inserts in leg_spacer and foot_top go in as on C2 and C3; the SS-10 switches press into foot_top.
4. T2 sole screws onto foot_bottom_pla and the foot assembles (B26 fit).

### Step 3: the rest, plates for a 220 bed (12 plates)

"+ 1 spare" marks the spare set (G5, G6 below). Plates are packed by the part outline plus its supports, each under 14 h except the head.

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| P220-01 | base | head_bot_sheet | 57.5 | 3.88 |
| P220-02 | base | body_front, battery_pack_lid, foot_side, right_cache, speaker_stand, speaker_interface | 179.2 | 13.83 |
| P220-03 | base | body_back, right_eye, flash_light_module, flash_reflector_interface, bulb x2, roll_motor_bottom + 1 spare, left_antenna_holder + 1 spare, right_antenna_holder + 1 spare | 139.8 | 11.31 |
| P220-04 | fit | trunk_top, right_roll_to_pitch, knee_to_ankle_left_sheet x2 + 1 spare, knee_to_ankle_right_sheet x2 + 1 spare | 139.6 | 12.23 |
| P220-05 | fit | roll_motor_top | 8.0 | 0.80 |
| P220-06 | insert | head | 262.0 | 21.88 |
| P220-07 | insert | body_middle_bottom, foot_top, foot_bottom_pla | 159.0 | 13.08 |
| P220-08 | insert | body_middle_top, leg_spacer x2 | 116.6 | 9.84 |
| P220-09 | insert+fit | trunk_bottom | 42.0 | 3.53 |
| P220-10 | neck | head_pitch_to_yaw, neck_left_sheet, neck_right_sheet, each + 1 spare | 61.1 | 6.11 |
| P220-11 | neck+fit | head_yaw_to_roll, head_roll_mount, each + 1 spare | 89.6 | 8.55 |
| P220-12 | TPU | foot_bottom_tpu (second sole) | 18.1 | 2.25 |

Plates for a 256 bed (11 plates after the same 3 left leg plates):

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| P256-01 | base | head_bot_sheet, right_cache, right_eye, speaker_interface, flash_light_module, bulb x2, roll_motor_bottom + 1 spare, left_antenna_holder | 175.7 | 13.47 |
| P256-02 | base | body_front, body_back, foot_side, battery_pack_lid, right_antenna_holder, left_antenna_holder spare | 184.3 | 13.96 |
| P256-03 | base | speaker_stand, flash_reflector_interface, right_antenna_holder spare | 16.2 | 1.66 |
| P256-04 | fit | trunk_top, right_roll_to_pitch, roll_motor_top, knee_to_ankle_left_sheet x2 + 1 spare, knee_to_ankle_right_sheet x2 + 1 spare | 148.3 | 13.16 |
| P256-05 | insert | head | 262.0 | 21.88 |
| P256-06 | insert | body_middle_bottom, foot_top, foot_bottom_pla | 158.6 | 13.02 |
| P256-07 | insert | body_middle_top, leg_spacer x2 | 116.6 | 9.84 |
| P256-08 | insert+fit | trunk_bottom | 42.0 | 3.53 |
| P256-09 | neck | head_pitch_to_yaw, neck_left_sheet, neck_right_sheet, each + 1 spare | 61.2 | 6.09 |
| P256-10 | neck+fit | head_yaw_to_roll, head_roll_mount, each + 1 spare | 89.5 | 8.53 |
| P256-11 | TPU | foot_bottom_tpu (second sole) | 18.1 | 2.25 |

Suggested order inside step 3: trunk_bottom first (C1 rule applies), then the neck plates (C4 rule applies), then the rest, the head last (longest job, 21.9 h). Every plate was sliced as one job and checked: inside the bed, no path conflicts.

## Orientation and supports per part

Up direction is the upstream STL axis that points up (same as PRINT_CHECK). Support grams are per part.

| STL | Up | Footprint mm | Height mm | Support g | Note |
|---|---|---|---|---|---|
| battery_pack_lid | -x | 86.4 x 51.4 | 7.5 | 0.06 | |
| body_back | -x | 125.0 x 110.0 | 40.0 | 8.13 | Support under the inner ceiling; 42 degree inner walls print without support |
| body_front | +x | 143.0 x 110.0 | 10.0 | 0 | |
| body_middle_bottom | +z | 150.0 x 110.0 | 86.2 | 14.74 | 8 insert bores are horizontal in this orientation (they print fine, small holes bridge) |
| body_middle_top | +x | 110.0 x 56.8 | 150.0 | 8.48 | Tall: 4 of its insert bores open on the bed face |
| bulb | -x | 35.0 x 35.0 | 2.0 | 0 | |
| flash_light_module | +x | 41.0 x 31.5 | 28.0 | 0.32 | |
| flash_reflector_interface | +x | 23.0 x 23.0 | 12.7 | 0.06 | |
| foot_bottom_pla | -z | 93.0 x 27.7 | 8.0 | 0.37 | Blind bores open upward |
| foot_bottom_tpu | -z | 101.9 x 40.7 | 8.0 | 0 | No supports in TPU |
| foot_side | +y | 103.5 x 46.0 | 12.0 | 0.73 | |
| foot_top | -y | 103.5 x 46.0 | 34.9 | 0.63 | Insert bores open upward; SS-10 slots are vertical windows, 6.4 mm bridge on top |
| head | -z | 199.8 x 197.3 | 59.4 | 29.55 | Top face on the bed. Sloped back (12.5 degrees) and the horizontal bearing seat sit on support |
| head_bot_sheet | +z | 193.8 x 191.6 | 3.0 | 0.12 | Large thin plate |
| head_pitch_to_yaw | +x | 72.0 x 44.9 | 32.0 | 1.43 | |
| head_roll_mount | +z | 64.7 x 40.0 | 15.1 | 0.40 | |
| head_yaw_to_roll | +z | 87.9 x 80.0 | 42.2 | 1.83 | Support under the top arm (servo pocket ceiling) |
| knee_to_ankle_left_sheet | -y | 70.6 x 30.7 | 8.4 | 0.19 | |
| knee_to_ankle_right_sheet | +y | 70.6 x 30.7 | 7.2 | 0.17 | |
| left_antenna_holder | vector (0.263, -0.935, -0.236) | 41.2 x 25.8 | 10.1 | 0.05 | See note 1 |
| left_cache | -z | 90.0 x 40.0 | 152.6 | 1.99 | Tallest part |
| left_eye | +x | 35.0 x 35.0 | 4.3 | 0 | Pilots open on the bed face |
| left_roll_to_pitch | -z | 86.1 x 46.9 | 30.7 | 1.29 | |
| leg_spacer | -y | 28.1 x 10.0 | 36.9 | 0.16 | 2 insert bores open on the bed face |
| neck_left_sheet | -y | 58.0 x 30.7 | 7.1 | 0.17 | |
| neck_right_sheet | +y | 58.0 x 30.7 | 5.8 | 0.18 | |
| right_antenna_holder | vector (0.263, 0.935, -0.236) | 41.2 x 25.8 | 10.1 | 0.05 | See note 1 |
| right_cache | -z | 90.0 x 40.0 | 152.6 | 1.99 | |
| right_eye | +x | 40.0 x 40.0 | 8.4 | 0.01 | Pilots open on the bed face |
| right_roll_to_pitch | -z | 86.1 x 46.9 | 30.7 | 1.30 | |
| roll_motor_bottom | +x | 31.4 x 30.7 | 32.0 | 0.60 | |
| roll_motor_top | -z | 38.0 x 28.7 | 20.0 | 0.48 | |
| speaker_interface | vector (-0.263, -0.935, 0.236) | 37.8 x 37.8 | 6.2 | 0 | Laid flat, see note 2 |
| speaker_stand | -z | 51.4 x 46.0 | 47.4 | 2.47 | |
| trunk_bottom | +z | 108.0 x 54.4 | 73.7 | 0.28 | Bearing seats vertical, lip on the bed; 4 insert bores open on the bed face |
| trunk_top | +z | 125.5 x 100.7 | 41.0 | 7.79 | |

1. The antenna holders and speaker_interface are not square to the STL axes. The old audit measured them in a turned ("aligned") frame, so their PRINT_CHECK axis does not apply to the raw STL. parts.csv gives the up direction as a vector in the raw STL frame (same orientation as before for the holders).
2. speaker_interface now lies flat (bed contact 1122 mm2): 2.33 g, 0.22 h, no support. PRINT_CHECK had it standing on a 48 mm2 edge, 37.6 mm tall; a test slice that way needed 1.86 g of support and 0.67 h.

## Anticipated issues and how each is handled

1. Elephant foot on bores at the bed. Bores that open on the bed face: trunk_bottom (4 M3 insert bores and the 26.19 mm lip), body_middle_top (4 insert bores), leg_spacer (2 insert bores per part), left_eye and right_eye (screw pilots), C1 (lip). Handled with elephant foot compensation 0.15 mm (TPU 0.10). If an insert will not start, break the bore edge by hand with a 6 mm drill bit (a light chamfer, no power tool).
2. Hole shrinkage. Printed holes usually come out a little small. Setting used: none by default (PrusaSlicer xy_size_compensation = 0), because the CAD clearances assume nominal holes. PrusaSlicer 2.7 has no hole-only setting; its xy_size_compensation moves every outline (a negative value grows holes and shrinks outer faces by the same amount). Orca Slicer and Bambu Studio have "X-Y hole compensation", which grows holes only. Rule from C1: if the seat measures under 32.10 mm, set for trunk_bottom and head only either PrusaSlicer xy_size_compensation = -(32.19 - measured) / 2, or Orca/Bambu hole compensation = +(32.19 - measured) / 2, and reprint C1 before trunk_bottom. Small holes (2.0 mm screw pilots, 4.0 mm insert bores) stay as printed: a slightly small pilot grips a self-tapping screw better, and inserts are heat set.
3. Servo pockets (flag 6). Measured across each pocket (pocket width minus servo width, ray cast in the assembly): head_yaw_to_roll is the only pocket undersize across the servo (-0.10 mm, floor ledge to top arm, a band about 1 mm wide). roll_to_pitch L and R, trunk_top, roll_motor_top, head_roll_mount and the knee sheet tabs are line to line (0.00 to -0.02 mm); the 0.10 mm in PRINT_CHECK is one face overlapping while the opposite face has 0.1 to 0.2 mm gap. The critical head_yaw_to_roll size is vertical: in the G-code the ledge top lands on the 4.2 mm layer and the arm underside on 39.2 mm, so the sliced gap is 35.00 mm (line to line); the first layer over the support can sag 0.1 to 0.2 mm. C4 tells; light sanding is the planned fix.
4. Bridges. No supports under bridges (dont_support_bridges). Bridges at 30 mm/s, fan 100%. Main ones: the 6.4 mm top of each SS-10 slot in foot_top (a 0.85 mm skin at the very top of the part, checked in C2a) and the horizontal 4.0 mm insert bores of body_middle_bottom (the top of each bore may sag slightly; the heat-set insert reforms it).
5. Thin features under 0.4 mm (flag 3: head_bot_sheet 0.22, foot_bottom_tpu 0.27, roll_motor_top 0.33 mm at the 1st percentile). The Arachne wall generator prints any feature from 0.1 mm wide (min_feature_size 25%) and widens it to 0.34 mm (min_bead_width 85%), so these edges and chamfers print, slightly thicker than CAD. Nothing to do.
6. TPU. Dry it (70 C, 7 h). 25 mm/s, retraction 0.8 mm or off on a Bowden printer, no supports, glue stick as a release layer on PEI (the TDS lists PVA glue), avoid crossing perimeters on to cut stringing. Not AMS or multi-material compatible (maker page).
7. The head (21.9 h, one job). The top face is on the bed. The sloped back (12.5 degrees) and the horizontal 6804 seat rest on support (29.6 g): expect support scars on the back slope (cosmetic) and check the 6804 in the head seat after support removal; scrape the top of the seat if tight (C1 only covers the vertical seats in trunk_bottom). The head with supports and skirt needs 202.3 x 196.8 mm of bed; it fits a 220 bed, centred, with 7.6 mm or more to spare at each edge.
8. Large flat parts. head_bot_sheet (193.8 x 191.6 x 3.0 mm) and the head can lift at the corners on an open printer. Clean bed, first layer bed 60 C. If a corner lifts, add a 4 mm brim (still fits 220); brims are not in the estimates.
9. 180 mm beds (for example Prusa Mini, Bambu A1 mini) fail: the head (199.8 x 197.3, 202.3 x 196.8 with supports and skirt) and head_bot_sheet (193.8 x 191.6). Everything else fits; the largest other print is body_middle_bottom at 159.6 x 111.2 mm with supports and skirt. The S1 coupon plate as generated is a 45 x 197 mm column; on a 180 bed lay the 6 coupons out again (they fit easily).
10. Supports came out of the slicer as planned: snug supports reach at most 3 mm past any part outline, the plates were packed with that margin, and no plate shows a path conflict.

## Upstream issues in the print phase (UPSTREAM_ISSUES.md G5, G6, G12)

G5, a neck part breaks often (Mini issue 33, part not named). The 5 neck and head chain parts print with the neck override (5 walls, 40% infill) and one spare set is in the plates. C4 tests the setting on head_yaw_to_roll first. Mass: the neck chain goes from 58.2 g (base profile) to 71.3 g (+13.0 g, model only); every neck part still weighs less than the same part solid. head_pitch_to_yaw is the one neck part with its own URDF link: the URDF mass (16.9 g) equals the solid part, the print is 15.1 g.

G6, find_soft_offsets.py drives all 14 joints to zero at once and broke a head part (Runtime issue 32). Judged from the joint ranges (URDF), the mass that swings beyond each joint (URDF link masses) and the thinnest printed part at the joint (median wall from the audit), see joint_risk.py:

| Joint | Range deg | Mass that swings g | Thinnest printed parts at the joint (median wall mm) |
|---|---|---|---|
| head_yaw | -160 to 160 | 453 | head_pitch_to_yaw 4.00, head_yaw_to_roll 7.45 |
| neck_pitch | -20 to 65 | 536 | neck_right_sheet 5.85, neck_left_sheet 7.05 (horn side), trunk_top 9.18 |
| head_pitch | -45 to 45 | 470 | head_pitch_to_yaw 4.00, neck sheets 5.85 and 7.05 |
| hip_pitch | -70 to 30 | 272 | left_cache 3.50 (a cover), knee sheets 3.85 and 3.90, roll_to_pitch 5.00 |
| knee | -90 to 90 | 148 | knee sheets 3.85 and 3.90 |
| hip_yaw | -30 to 30 | 414 | roll_motor_bottom 2.97 |
| head_roll | -30 to 30 | 361 | head_roll_mount 4.00, head_yaw_to_roll 7.45 |
| hip_roll | -25 to 25 | 347 | roll_motor_bottom 2.97, roll_to_pitch 5.00 |
| ankle | -90 to 90 | 75 | knee sheets 3.85 and 3.90 |
| antenna | -90 to 90 | 4 | antenna holder 2.00 |

Spares in the plates (one each, 10 parts, 104.6 g, 9.8 h):
- neck_left_sheet, neck_right_sheet, head_pitch_to_yaw, head_yaw_to_roll, head_roll_mount: the three joints with the most travel times swinging mass (head_yaw, neck_pitch, head_pitch) all load these parts, the head is the heaviest swinging mass (about 0.45 kg), and head_pitch_to_yaw is the thinnest of them (4.0 mm). Same set as G5.
- knee_to_ankle_left_sheet and knee_to_ankle_right_sheet: the thinnest leg plates (3.85 and 3.90 mm), on hip pitch, knee and ankle; knee and ankle can travel 90 degrees.
- roll_motor_bottom: the thinnest hip part (2.97 mm), on hip yaw (414 g swings) and hip roll, where the G12 screw head pushes.
- left_antenna_holder and right_antenna_holder: the thinnest parts on the robot (2.0 mm) and they stick out of the head top, so they are hit first if the head swings into the body.
- Not spared: left_cache and right_cache (3.5 mm, but covers, 77 g and 6 h each; reprint only if one breaks).

Offset step procedure (for the build notes, from G6 and the upstream scripts):
- Fit every horn while the servo sits at the zero the configure step drives it to (Runtime scripts/configure_motor.py ends with goal position 0; docs/configure_motors.md: "the motor will move to its zero position. You can then install the horn").
- Check each joint alone first with Runtime scripts/check_motors.py.
- Run scripts/find_soft_offsets.py (its own warning: it moves the robot to zero quickly) only with the robot hanging (feet and head clear of the stand and the table, head clear of the body), a hand on the power switch, and the spare set on the bench. A stand is not in the stock STL set; upstream mods have one (print/mods/v2_Jaimes_Mods/stand, 3MF files, not measured here).

G12, roll_motor_bottom screw head against roll_to_pitch (Mini issue 17): the CAD shows the interference (numbers in step 2). The pass or fail check is in step 2, before the right leg is assembled.

## Optional expression part: antenna rods (in the CAD, not in print/ or the print guide)

- Source: mini_bdx/robots/open_duck_mini_v2/antenna.stl (meters, x1000), qty 2 (one per antenna holder). Measured: it is a straight rod, 150.0 mm long and 1.8 mm in diameter, with a 3.8 mm collar 6.0 mm long at one end; not a flat paddle (its 3.8 x 39.4 x 146.1 mm box comes from a 15 degree tilt in the zero pose). It passes through two 1.8 mm holes in the antenna holder, 41 mm apart, and sticks out 109 mm past the second one; the 3.8 mm collar is a bead at the free tip.
- Print flat (rod along the bed). The tip bead lifts the rod 1.0 mm off the bed, so the slicer puts 0.33 g of support under it. Ream the holder holes with a 1.8 mm drill by hand if the rod does not pass (line to line in CAD).
- Slice, each: PLA 0.89 g (0.33 g of it support), 6 min; TPU 0.54 g, 4 min (no support allowed, so the lifted rod would print in the air). For 2: PLA 1.8 g, 0.19 h. Not in the totals above.
- Material. Asked for TPU 95A first so a rod survives bumps (a flexible rod bends and springs back when the robot falls or the head swings, and spares the SG90 gears). Measured shape says no: a 1.8 mm TPU rod cannot hold itself up. The TPU TDS gives no small-strain modulus (9.99 MPa at 100% strain); even at 100 MPa the 109 mm free length with its tip bead would sag about 15 mm under its own weight (about 50 mm at 30 MPa). So PLA is the choice here: sag about 0.6 mm (TDS modulus 2650 MPa), but it can snap in a fall; print 2 spare rods (minutes each). A bought rod would be a change from upstream (Ahmed's call).
- SG90 load: one PLA rod is about 0.52 g with its centre of mass 63 to 64 mm from the SG90 axis (URDF), so 0.52 g x 6.3 cm = 0.0033 kg.cm, about 0.2% of the SG90 stall torque of 1.8 kg.cm (Tower Pro SG90 page, 4.8 V; the Miuzei SG90 in the BOM is a clone, not verified); with the holder about 0.3%. The URDF link mass (4.2 g) already equals holder plus rod at solid density, so the sim includes the rods.

## Filament against the BOM

| | Needed (estimate) | BOM | Left |
|---|---|---|---|
| PLA (Overture Easy PLA) | 1502 g: coupon session 27.8 g (includes the left eye) plus plates 1474.5 g (the rest of the robot set and 104.6 g of spares) | 2 x 1 kg (BOM line 27) | about 500 g (25%) for failed prints; a second head (262 g) still fits |
| TPU (Overture TPU 95A) | 36.3 g: two soles (one in S2) | 1 x 1 kg (BOM line 28) | about 964 g |

The BOM line 27 note "need 1304 g sliced, 1.5 kg with 15% spare" is now 1502 g, 1.73 kg with 15% spare: still 2 spools. BOM.md is not edited here (not owned).

## Not verified

- Every gram and hour is a slicer estimate on a generic printer; nothing has been printed or weighed.
- Temperatures, speeds and densities are maker-typical (Overture pages and TDS, read 2026-11-01), not lab tested.
- All coupon results (seat fit, insert seating, switch fit, servo fit, eye pilots, TPU grip and fit) are open until the coupons are printed.
- G12 assumes an ISO M2 pan head 4.0 x 1.6 mm; the Feetech bag screw head size is not published (B2). Any head over 0.31 mm tall hits at the outer screw.
- The 6.7 mm bore depth in PRINT_CHECK flag 5 and HARDWARE_AUDIT B15 was not found in any STL: every M3 insert bore is 5.8 mm deep (6.0 mm for 4 head bores); what differs is what lies beyond (see PRINT_CHECK flag 5).
- The SG90 torque is the Tower Pro figure; the TPU small-strain modulus is not published.
- The .ini files were used with the PrusaSlicer CLI; importing them into the GUI or another slicer was not tried. The coupon 3MF was sliced with the CLI only.
- Support removal on the head back slope and inside the head bearing seat is untested.
