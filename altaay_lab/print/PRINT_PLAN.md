# PRINT_PLAN: Open Duck Mini v2 stock build

Last updated: 2026-11-03 about 5:00 PM ET (structure twin integration for the lead, twin/structure/STRUCTURE_TWIN.md, sim pass only, FEA pass only: step 2 check 7, the proof loads, and a record-only 20 kg hang on C2aL in step 1). Earlier: 2026-11-02 about 5:10 AM ET (agent INT, integration pass: After printing step 5, the D25 cable tie holes, from agent CAB; the T14 and T15 bits named in steps 3 and 4; the T1 washers come with test order TO17). Earlier: 2026-11-02 about 1:50 AM ET (agent PRT, DECISIONS.md D21 note: T1 now tests the real eye screw stack, two 0.3 mm washers on the printed bulb T1b and head wall T1w, 5.6 mm; S1 sliced again with 11 pieces). Earlier: 2026-11-02 about 12:20 AM ET (DECISIONS.md D22: the light print profile is the default, light coupons C2aL, C2bL and C3L join session S1 as the gate, every plate packed and sliced again; D24: drill step 4 for the projector leads). Earlier: 2026-11-01 10:55 PM ET (D19 to D21). Nothing has been printed. Nothing is printed until Ahmed approves (lab rule 4: slice summary first, then Ahmed's OK).

All grams and hours are PrusaSlicer 2.7.2 estimates made on the box for a generic 0.4 mm printer at moderate speeds (config/printer_generic.ini). They are not printed results. The real printer is not known yet; a faster printer takes fewer hours, grams change little. Material settings are maker-typical values from the Overture pages, not lab tested.

## What Ahmed approves

| Step | What | PLA g | TPU g | Hours |
|---|---|---|---|---|
| 1. Coupon session | S1: one PLA plate with 17 test pieces, C1, C2a, C2b, C3, C4 and T1 with its stack pieces T1b and T1w, plus the light copies C2aL, C2bL and C3L, the D22 gate (4.69 h). S2: one TPU foot sole (2.19 h) | 46.8 | 17.6 | 6.9 |
| 2 and 3. Full print, 220 bed | 18 jobs: left leg first (5 plates), then 13 plates. All remaining robot parts plus 10 spares | 1360.4 | 17.6 | 119.9 |
| 2 and 3. Full print, 256 bed | Same parts in 17 jobs | 1353.6 | 17.6 | 119.6 |
| Total (220 bed) | | 1407.2 | 35.1 | 126.9 |
| If the D22 gate fails (220 bed) | The 3 "base + rings" plates print with 4 walls and no rings instead (step 3) | +61.5 | | +4.1 |

- Ask 1: approve step 1 (coupon session) now. Ask 2: approve steps 2 and 3 after the coupon tests pass (or with the fixes they call for), including the D22 gate: C2aL, C2bL and C3L must pass the same tests as C2a, C2b and C3.
- Profile: the light profile of DECISIONS.md D22 (print/MASS_STUDY.md variant c): 2 walls unless a rule needs more, solid rings round the insert bores and the body_back pilots, the head, neck chain, G6 thin parts, frame parts, eyes, speaker stand and all spares at their settings before D22.
- Before D22 (the package as published on 2026-11-01; `slice.py --set heavy` reproduces its 15 plates within 0.1 g and 0.04 h each): coupon session 27.8 g PLA, 18.2 g TPU, 5.0 h; full print on a 220 bed 15 jobs, 1474.5 g PLA, 18.1 g TPU, 126.4 h; total 1502.3 g PLA, 36.3 g TPU, 131.4 h. D22 saves 118.3 g of PLA and 7.0 h in all and adds 3 jobs (more profiles, one plate each).
- The robot set alone (44 STLs, 62 parts since the D59 sit parts, no coupons, no spares) is PLA 1260.0 g and 108.5 h, TPU 73.5 g and 9.0 h (SLICE_SUMMARY.md totals; at D22, with 36 STLs then: PLA 1257.7 g and 108.0 h, TPU 35.1 g and 4.4 h; before D22: PLA 1372.7 g and 114.4 h, TPU 36.3 g and 4.5 h; old PRINT_CHECK: PLA 1304.0 g and 127.7 h, TPU 35.0 g and 3.9 h). Details: SLICE_SUMMARY.md.
- D38 (2026-11-05, a lead call under Ahmed's delegation; D26 option P1, twin/knee/KNEE_TWIN.md section 5): left and right roll_to_pitch print with 3 walls and fit (wall3+fit in parts.csv, their profile before D22): slice.py parts, 2026-11-05, 24.82 g and 2.31 h (left), 24.82 g and 2.33 h (right), +3.6 g and +0.22 h each. The totals here add these changes; the plates were not re-planned: run slice.py plates before slicing for print.
- Filament: 1400 g PLA of the 2 kg bought (about 600 g left for failed prints; 1461 g if the gate fails), 35 g TPU of the 1 kg bought.
- Optional, not in the totals: 2 antenna rods (in the CAD, not in print/), PLA, 1.8 g, 0.2 h.
- Session S1 is 4.69 h, 1.69 h over the 3 hour target, because of the 3 light coupons (+8.4 g, +0.86 h) and the T1 stack pieces T1b and T1w (+5.0 g, +0.54 h; T1w alone slices to 31 min: it stands 35 mm tall on its edge, as the wall prints in the head). S2 adds 2.19 h because TPU must print slowly; run it right after S1 or overnight.

## Files in this folder

| File | What it is |
|---|---|
| config/printer_generic.ini | Generic printer for estimates only: 0.4 mm nozzle, 1.75 mm, 220 x 220 bed, Marlin 2. Use your own printer profile when printing. |
| config/bed_256.ini | Bed override for 256 x 256 printers. |
| config/pla_print.ini, config/filament_easy_pla.ini | PLA print and filament settings (base for every PLA part): the light profile of D22, 2 walls. |
| config/tpu_print.ini, config/filament_tpu95a.ini | TPU print and filament settings (foot_bottom_tpu only), 2 walls. |
| config/ovr_insert.ini, ovr_neck.ini, ovr_wall3.ini, ovr_fit.ini | Per-part overrides, loaded after the base files (see below). |
| config/mod_ring.ini | Settings of the solid rings (100 % infill modifiers round insert bores and screw pilots, see below). |
| config/pla_print_heavy.ini, config/tpu_print_heavy.ini | The base files before D22 (3 walls), kept for the package before D22 (`slice.py --set heavy`). |
| parts.csv | Every STL: quantity, material, profile (light, rings or heavy, with the reason), overrides, rings, the overrides before D22 ("heavy"), print up direction, left leg count, spares. |
| make_coupons.py | Cuts the test coupons from the real upstream STLs into a folder you name (never into the repo) and re-measures the feature in each; adds the light copies C2aL, C2bL and C3L (D22 gate) and the T1 stack pieces T1b and T1w, and checks the stack against fasteners/fasteners.json (D21 note). |
| slice.py | Slices parts (with their rings), coupons, plates and the optional antenna; writes G-code, 3MF and JSON to a folder you name; builds SLICE_SUMMARY.md. `--set heavy` slices the package as it was before D22. |
| MASS_STUDY.md, mass_study.py, config_light/ | The mass study behind D22 and its input configs (config_light/ is the study's copy of the light files, unchanged). |
| check_hip_roll_screw.py | Upstream issue 17 (G12) check: sweeps hip roll and measures the screw head clearance. |
| joint_risk.py | Upstream Runtime issue 32 (G6) table: joint range, mass that swings, thinnest part at each joint. |
| SLICE_SUMMARY.md | All slice numbers: the light profile against the settings before D22, per part, plate, coupon and fallback. |

How to run (outputs stay outside the repo, for example in the box scratch folder):

```bash
cd altaay_lab/print
python3 make_coupons.py /tmp/odm_coupons
nice -n 10 python3 slice.py parts    --out /tmp/odm_slice
nice -n 10 python3 slice.py coupons  --out /tmp/odm_slice --coupons /tmp/odm_coupons
nice -n 10 python3 slice.py plates   --out /tmp/odm_slice --bed 220     # and again with --bed 256
nice -n 10 python3 slice.py optional --out /tmp/odm_slice
nice -n 10 python3 slice.py parts    --out /tmp/odm_heavy --set heavy   # before D22, for the "before" columns
nice -n 10 python3 slice.py plates   --out /tmp/odm_heavy --set heavy --bed 220   # optional, before D22
python3 slice.py summary  --out /tmp/odm_slice --before /tmp/odm_heavy --md SLICE_SUMMARY.md
```

Needs PrusaSlicer 2.7.2 (CLI) and Python with trimesh, numpy, shapely, manifold3d, yourdfpy. Every plate is written as a PrusaSlicer 3MF (plates_220/<plate>.3mf, and session/S1_PLA_coupons.3mf for the coupons) with each part's own settings and its rings as modifiers, so it opens in the PrusaSlicer GUI ready to slice for your printer. In another slicer, add the rings by hand: a cylinder modifier with 100 % infill at each hole; slice.py writes every ring's axis, centre, diameter and length to holes.json in its output folder. The .ini files were tested with the CLI only, not imported in the GUI.

## Settings (any slicer)

| Setting | PLA (Overture Easy PLA) | TPU (Overture TPU 95A) | Why |
|---|---|---|---|
| Layer height, first layer | 0.20, 0.20 mm | 0.20, 0.20 mm | Standard for a 0.4 mm nozzle |
| Walls (perimeters) | 2 (about 0.86 mm), more on the parts listed below | 2 | Upstream default (D22, MASS_STUDY.md); the parts that need more get an override or solid rings |
| Solid rings | 100 % infill cylinder round each insert bore (2.0 mm solid) and listed screw pilot (1.5 mm), 0.6 mm past each end | None | The insert and pilot rules at each hole instead of extra walls on the whole part (D22) |
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

Since D22 (DECISIONS.md, MASS_STUDY.md variant c) every part prints at the base (2 walls, PLA 15 %, TPU 40 %) unless a rule needs more. parts.csv names each part's profile and the reason: light (base, fit kept where listed), rings (base plus solid rings) or heavy (the settings it had before D22). All spares are heavy.

| Override | Settings | Parts | Why (one line) |
|---|---|---|---|
| insert | 4 walls | head, trunk_bottom; the S1 gate fallback of the 10 insert ring parts | 4 walls put about 1.67 mm of solid plastic round each 4.0 mm insert bore (CNC Kitchen minimum 1.6 mm). The head keeps them because in the sim its mass is the forward counterweight; trunk_bottom because both legs hang from it. |
| neck | 5 walls, 40% infill | neck_left_sheet, neck_right_sheet, head_pitch_to_yaw, head_yaw_to_roll, head_roll_mount | Upstream issue 33 says a neck part breaks often (part not named); walls carry most of the bending load, so 5 walls (most of these parts become solid) and 40% infill. |
| wall3 | 3 walls | knee_to_ankle_left_sheet, knee_to_ankle_right_sheet, left and right roll_to_pitch (D38), roll_motor_bottom, left and right antenna_holder, left_eye, right_eye, speaker_stand, trunk_top | The walls these parts had before D22: the thinnest parts at their joints (G6), the eyes and speaker_stand with their screw pilots (T1 tests the eye profile), and trunk_top, which holds the 2 hip yaw servos and the neck pitch servo. |
| fit | Outer wall printed first, outer wall at 25 mm/s | trunk_bottom (bearing seats), head_yaw_to_roll, head_roll_mount, left and right roll_to_pitch, roll_motor_top, trunk_top, knee_to_ankle sheets | The wall that touches the 6804 bearing (0.19 mm clearance) or the STS3215 (0.00 to 0.10 mm CAD interference) is laid at its CAD position, not pushed into the hole by the inner walls. |
| rings (modifiers, config/mod_ring.ini) | 100 % infill cylinder round each hole: 2.0 mm solid round an insert bore, 1.5 mm round a screw pilot | Insert bores: body_middle_bottom 8, body_middle_top 8, foot_top 2 each, foot_bottom_pla 2 each, leg_spacer 4 each. Pilots: body_back 5 | The insert and pilot rules at each hole without walls on the whole part: at least as much plastic within the rule distance of every ringed hole as before (MASS_STUDY.md Table 1). The insert ring parts wait for the S1 gate. |

trunk_bottom uses insert+fit; head_yaw_to_roll and head_roll_mount use neck+fit; trunk_top, the knee sheets and roll_to_pitch (D38) use wall3+fit. Each plate below uses one profile only, so any slicer can print it with one setting; rings ride with their part as modifiers in the plate's 3MF. The 10 parts with insert rings print on plates of their own ("base + rings"), so the S1 gate changes whole plates, never parts inside a plate.

## Print order

### Step 1: coupon session (about 6.8 h, 46.8 g PLA plus 17.6 g TPU)

S1, one PLA plate, 4.69 h, 46.8 g. Every coupon keeps the profile of the part it comes from (per-object settings and ring modifiers in the 3MF; in another slicer set them by hand). The light copies C2aL, C2bL and C3L are the D22 gate: they print next to C2a, C2b and C3, which keep 4 walls (the fallback profile). T1b and T1w are the two printed layers the eye screws pass in the robot (bulb 2.0 mm, head wall 3.0 mm); with two 0.3 mm washers from BOM 17l under each head they make the real 5.6 mm stack for T1 (DECISIONS.md D21 note):

| ID | Cut from (upstream STL) | What it tests | Profile | g | min |
|---|---|---|---|---|---|
| C1 | trunk_bottom, the end lobe with one seat (y above 14 mm) | One 6804 seat, 32.19 mm, 5.8 mm deep, on its 26.19 mm lip, with the real ring wall (PRINT_CHECK flag 7) | insert+fit | 5.5 | 28 |
| C2a | foot_top, top 21.45 mm of the part, x 12 to 48 | Insert boss with the 1.5 mm wall (B16) and one Omron SS-10 slot 6.4 x 19.8 mm (B11), with 4 walls (the D22 fallback) | insert | 6.3 | 38 |
| C2aL | the same cut as C2a | D22 gate: the C2a tests in the light profile of foot_top (2 walls, 15 %, a 2.0 mm solid ring round the bore). After the pass/fail tests: hang 20 kg (196 N) from the C2aL screw for 10 s (a luggage scale or a bucket of water) and record whether the insert moved. The largest fall pull on a leg_spacer insert, in the same 2.0 mm ring design, is 189 N over all four contact levels (twin/structure/STRUCTURE_TWIN.md section 3.2, sim pass only, FEA pass only); the published pull-out data (1354 to 1552 N) are for walled bores, not these rings | base + 1 insert ring | 4.2 | 27 |
| C2b | foot_top, top 10.85 mm, x below -36.2 | The second 1.5 mm insert boss (second sample), with 4 walls | insert | 2.1 | 14 |
| C2bL | the same cut as C2b | D22 gate: the second boss in the light profile | base + 1 insert ring | 1.8 | 12 |
| C3 | foot_bottom_pla, 18 mm slice round one bore | The shallowest insert bore: blind 4.0 x 5.8 mm cylinder plus a drill point cone (tip at 6.93 mm, 1.06 mm floor), no pilot below (B15, flag 5), with 4 walls | insert | 2.7 | 13 |
| C3L | the same cut as C3 | D22 gate: the blind bore in the light profile of foot_bottom_pla | base + 1 insert ring | 2.3 | 12 |
| C4 | head_yaw_to_roll, right arm, full height | The only servo pocket undersize across the servo: ledge to arm 34.90 mm for a 35.00 mm STS3215 body (flag 6). Also tests the neck profile | neck+fit | 9.4 | 61 |
| T1 | left_eye, whole part | Left eye pilots 2.2 mm (right eye 2.05) for M2.5x8 (B14), driven through the real 5.6 mm stack (T1b, T1w and two 0.3 mm washers): 2.4 mm engaged, 0.6 mm to the blind pilot floor (D21 note); eye glass disc seat; the eye profile (3 walls) | wall3 | 1.8 | 11 |
| T1b | bulb, whole part | The first layer under the eye screw heads: 2.0 mm, 4 clearance holes of 2.7 mm. A spare bulb if it passes (the plates still print the robot's 2) | base | 2.0 | 10 |
| T1w | head, the front wall behind the left eye cut to the eye's 35 x 35 mm outline | The second layer: 3.0 mm wall with the 25 mm eye opening and the 4 clearance holes of 2.7 mm, on its edge so the holes print horizontal as in the head | insert | 3.0 | 31 |

S2, TPU, 2.19 h, 17.6 g: T2 foot_bottom_tpu whole, Overture TPU 95A at 40% and 2 walls (B26, D22). If it passes it is the left leg sole.

Recess fit tests (D20), no new coupon: C4 already holds 4 of the 24 neck chain 5.5 mm recesses (M3 heads to the drive horn) and 4 of the 4.0 mm recesses (M2 pan heads to the servo case). Try a DIN 912 M3 head in a 5.5 mm recess (expected not to drop in), open one to 6.0 mm and try again, and try a servo-bag M2 head and a kit M2x5 head in a 4.0 mm recess. T1 also checks that the eye pilots are blind, 3.0 mm deep (D21), and T1w that the head's horizontal 2.7 mm eye screw holes print at size.

Each coupon is cut from the upstream STL with a box (make_coupons.py), keeps the part's print orientation, and is re-measured after the cut: C1 seat 32.18 mm and lip 26.18 mm; C2a and C2b bore 4.0 mm, pilot 2.0 mm, thinnest wall 1.50 mm, C2a slot 6.40 x 19.80 mm; C3 bore 4.0 mm, cylinder 5.77 mm deep; C2aL, C2bL and C3L are the same cuts and measure the same; C4 ledge to arm 34.90 mm, 4 recesses of 5.50 mm and 4 of 4.00 mm; T1 four pilots 2.19 mm, blind, 3.0 mm deep with a 1.3 mm front skin; T1b four holes of 2.70 mm, 2.00 mm thick; T1w four holes of 2.70 mm, the 24.98 mm eye opening, 3.00 mm thick. With the 0.6 mm of washers in fasteners/fasteners.json the T1 stack is 5.60 mm, the robot's: the M2.5x8 engages 2.40 mm and stops 0.60 mm short of the pilot floor (make_coupons.py manifest t1_stack).

Pass or fail, physical tests (tools: Pinecil with insert tip, calipers, 2.0 and 2.5 mm hex keys, a 5 kg weight or luggage scale, one STS3215 from test order TO1, one 6804ZZ, CNC Kitchen M3x5.7 inserts, M3x8 and M3x10, M2.5x8, Omron SS-10; for the recess and eye tests also an M3x5 DIN 912, the 6.0 mm HSS bit and T-handle (test order TO16), a kit M2x5 (TO4) and 8 of the 0.3 mm washers from BOM 17l, two per eye screw, from test order TO17, the BelMetric order):

| ID | PASS when all are true | If it fails |
|---|---|---|
| C1 | Seat measures 32.10 to 32.25 mm at 2 angles 90 degrees apart. The 6804ZZ goes in by thumb (no hammer, no heat), sits flat on the lip, does not rock when pushed sideways at its top edge, and comes out with finger pressure (slip fit by design, 0.19 mm). | Tight: see "Hole size" below, reprint C1 before trunk_bottom and head. Loose (rocks): Ahmed decides (retaining compound or a smaller hole). |
| C2a, C2b | Insert goes in straight and ends flush (straight edge, no lip over 0.1 mm). The 1.5 mm side wall has no crack or bulge over 0.2 mm. An M3x10 threads in by hand; tightened with the short arm of a 2.5 mm key, the insert does not spin. 5 kg hung from the screw for 10 s: no movement. C2a: the SS-10 presses in by thumb, stays in when shaken upside down, and its lever still clicks. | B16 stays open; tell Ahmed before printing foot_top. Switch loose or too tight: note it, B11 stays open. |
| C2aL, C2bL, C3L (D22 gate) | Every test of the 4-wall twin (C2a, C2b, C3), side by side with it: insert flush, side wall and bed face with no crack or bulge over 0.2 mm, the M3 screw threads in by hand, no spin with the short arm of a 2.5 mm key, 5 kg for 10 s; on C2aL also the SS-10 slot. | If a light coupon fails a test that its twin passes, the 10 insert ring parts (body_middle_bottom, body_middle_top, foot_top x2, foot_bottom_pla x2, leg_spacer x4) keep 4 walls: set their parts.csv overrides to insert and clear their rings (the heavy column), and print the 3 "base + rings" plates with the fallback profile (step 3): +61.5 g, +4.1 h on a 220 bed, about +61.7 g on the robot (MASS_STUDY.md). Everything else in D22 stands. If the twin fails too, its own row applies. |
| C3 | Insert reaches flush without pushing harder than on C2a, sits flush to 0.1 mm proud at most, no bulge or crack on the bed face over the bore, an M3x8 threads the full insert length by hand, 5 kg for 10 s: no movement. | B15 stays open (plastic blocks the bore); tell Ahmed before printing foot_bottom_pla. |
| C4 | Calipers: ledge to arm gap at the ledge (CAD 34.90; the G-code makes 35.00, see "Servo pockets"). The STS3215 case slides in end first between ledge and arm with firm thumb pressure, no tools, no rattle. Up to 0.2 mm tight: light sanding of the arm underside is expected (flag 6); note it. Recess fit (D20): after one 5.5 mm recess is opened to 6.0 mm (see "After printing"), a DIN 912 M3x5 head drops in and sits flat; a servo-bag M2 head and a kit M2x5 head drop into the 4.0 mm recesses and sit flat. | More than 0.2 mm tight, or the support scar needs more than light sanding: hold the head parts; try a 0.15 mm support gap or 0.1 mm layers on head_yaw_to_roll and reprint C4. The M3 head will not seat even at 6.0 mm: tell Ahmed before the neck parts are drilled (B32). An M2 head will not seat: open that recess to 4.5 mm and note it (B21). |
| T1, T1b, T1w | Depth rod: each eye pilot is blind, about 3.0 mm deep (D21). Calipers: T1b 2.0 mm and T1w 3.0 mm thick next to a hole. An M2.5 screw passes every hole of T1b and T1w by hand without threading. Stack as in the robot at each pilot: two 0.3 mm washers (BOM 17l) under the M2.5x8 head, then T1b, T1w and the eye, 5.6 mm in all (edges and holes lined up). The M2.5x8 then cuts its own thread in the eye and needs clear torque, snugs firmly with the short arm of a 2.0 mm key without stripping, engages 2.4 mm and stops 0.6 mm short of the floor; the eye does not move when pulled with 4 screws in, and the front skin shows no bulge or crack over a pilot. Never drive a bare M2.5x8 to the floor: it would push through the 1.3 mm skin. The eye glass disc (29.6 x 1.85 mm seat) drops in and stays when tipped. | A pilot strips: B14 stays open; options for Ahmed are an M2.5 thread-forming screw or a 2.05 mm pilot (CAD change). A T1w hole binds: open it with the 2.7 mm bit (BOM T12) by hand and note it; the same 8 holes in the head then need the bit (an after-printing step). The stack measures over 5.7 mm: less than 2.3 mm of thread, note it for Ahmed. |
| T2 | No missing layers, no blobs over 0.5 mm, lies flat on a table (no corner up over 0.5 mm). Length 101.9 and width 40.7 mm within 0.3 mm. An M3 passes both 3.4 mm holes and its head sinks fully into the 6.5 mm counterbores. Screwed to foot_bottom_pla (or to C3 for one hole) it pulls flat, gap under 0.3 mm at the edges. Grip, record only (no upstream number): on the lab floor with 1 kg on it, tilt until it slides, note the angle next to a PLA part. | Print fails: check that the TPU was dried and the printer can feed TPU at 25 mm/s (Bowden extruders may need retraction off). Fit fails: B26 stays open. |

V1 screws job (D38, in session S1 since 2026-11-04, sliced with slice.py and the D22 profile: K1a 1.03 g, K1b 2.20 g, K2a 0.96 g, K2b 0.79 g, K3 0.25 g, K4 0.40 g): coupons K1a and K1b (tongue and groove), K2a and K2b (back lip and ribs), K3 (cable clip, snap) and K4 (tie bridge) from altaay_lab/twin/screws/stl/, tests in TEST_PLAN.md section 14. body_front.stl, body_middle_top.stl and body_middle_bottom.stl in print/ now carry the groove, the tongue and the back lips and ribs (+0.74 and +4.87 cm3; body_middle_bottom adds 812 mm2 of supported overhang): re-sliced 2026-11-04 with slice.py (D22): body_front 58.05 g 4.06 h, body_middle_top 75.24 g 6.75 h, body_middle_bottom 107.45 g 9.38 h; the plates holding them are moved by these part deltas (calc), not re-sliced; the S1 gate fallback numbers are from before the change. body_middle_bottom now gets 7 insert rings: the bore of F075 (unused since D38) is clear (CAD check) but slice.py no longer classifies it next to the lip root, so it has no solid ring; re-slice with it if F075 comes back.

### Step 2: left leg, for the servo fit tests (5 plates, 16.7 h, 182.8 g; the TPU sole comes from S2)

Numbers below are for a 220 bed; on a 256 bed the same plates slice within 0.1 g and 0.01 h. L1-2 is a "base + rings" plate: print it after the S1 gate passes; if the gate fails, print it with the insert profile and no rings (60.0 g, 5.60 h).

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| L1-1 | base | foot_side, left_cache | 71.0 | 6.10 |
| L1-2 | base + rings | foot_top, foot_bottom_pla, leg_spacer x2 | 48.2 | 4.58 |
| L1-3 | fit | left_roll_to_pitch (wall3+fit, D38), roll_motor_top | 32.0 | 3.05 |
| L1-4 | wall3 | roll_motor_bottom | 8.7 | 0.72 |
| L1-5 | wall3+fit | knee_to_ankle_left_sheet x2, knee_to_ankle_right_sheet x2 | 26.5 | 2.50 |

Checks on the left leg (one STS3215 from TO1 is enough, moved from pocket to pocket):
1. Every servo pocket (hip roll in roll_motor_bottom and roll_motor_top, hip pitch in left_roll_to_pitch, knee and ankle between the knee sheets): the servo goes in by hand, no tools, no rattle. Note any face that needed sanding and how much. In CAD (net across the servo): roll_to_pitch and roll_motor_top 0.00 mm (line to line), knee sheet tabs 0.01 mm tight, roll_motor_bottom 0.22 mm clear.
2. Upstream issue 17 (G12), roll_motor_bottom screw head against left_roll_to_pitch. CAD result first (check_hip_roll_screw.py): roll_motor_bottom holds the hip roll servo with 2 servo-bag M2 screws through a 1.4 mm plate, heads on a flat face. The outer screw head sits 0.31 mm from the roll_to_pitch arm; an M2 pan head (ISO 7045, 4.0 x 1.6 mm, the bag screw type is not published, B2) overlaps the arm by 1.3 mm at every hip roll angle from -25 to +25 degrees (URDF limits), on both legs. The inner screw clears by 0.24 to 0.32 mm (left) and 0.16 to 0.27 mm (right).
   - Test: fit roll_motor_bottom to the servo with both screws fully seated. With the horn screws not yet in, hold left_roll_to_pitch on the hip roll horns and turn it by hand from -25 to +25 degrees about the configured zero and back (or, fully assembled, step the powered servo slowly through the same range).
   - PASS: the full range with no rubbing, no clicks and no new marks on roll_to_pitch, both screws seated.
   - FAIL (expected for the outer screw from the CAD): stop, do not force it. Note which screw and at what angle. Options for Ahmed before the right leg is assembled: leave the outer screw out (the CAD has no room for any head there), or a CAD change (a relief in roll_to_pitch or a countersink in roll_motor_bottom). No STL is changed in this package.
3. Inserts in leg_spacer and foot_top go in as on C2 and C3; the SS-10 switches press into foot_top.
4. T2 sole screws onto foot_bottom_pla and the foot assembles (B26 fit).
5. Hip pitch screw heads against left_roll_to_pitch (D19, B31). CAD result first (fasteners/FASTENERS.md findings 2 and 5): a DIN 912 head at the 4 knee_to_ankle_right_sheet to idle horn screws (F196, F198, F200, F247) overlaps left_roll_to_pitch by 1.19 mm at every hip pitch angle, and the one at F002 (thigh plate to leg_spacer) is hit from +18.9 deg; M3x6 ISO 7380 button heads (BOM 17j) clear by +0.16 mm and +1.16 mm in CAD.
   - Test: fit the 5 button heads, then turn the thigh against left_roll_to_pitch by hand through the full hip pitch range (URDF -70 to +30 deg) and back.
   - PASS: no rubbing, no clicks and no new marks on roll_to_pitch.
   - FAIL: stop, note which screw and at what angle; relieve roll_to_pitch locally (CAD change) before the right leg is printed (D19).
6. The light leg parts (D22, MASS_STUDY.md recommendation 5): foot_top, foot_side, foot_bottom_pla, leg_spacer, left_roll_to_pitch, roll_motor_top and left_cache print with 2 walls. In the checks above and the first bench tests, look for cracks, a split along a layer or a part that flexes visibly; if one does, reprint that STL in its heavy profile (parts.csv heavy column) before the right leg.
7. Structure twin proof loads (twin/structure/STRUCTURE_TWIN.md P7, HARDWARE_AUDIT B42 and B43; FEA pass only on sim pass only loads: these two parts are the weakest under walking and pushes). (a) The spare knee_to_ankle_left_sheet (parts.csv has one; it is on plate P220-12 of step 3, P256-11 on a 256 bed, with the right leg's sheets): fix its ankle end to the TO1 servo case with its 2 M2x5 case screws, as in the shin (the other 2 of the case's 4 pass the right sheet, fasteners/fasteners.json), and clamp the case; screw the TO1 servo's horn, taken off the servo, to the knee eye with the 4 M3x6; bolt a lever to the horn and hang 4.4 kg at 200 mm (8.6 N m, the push recovery peak in sim) for 10 s. PASS: no crack, whitening or set round the eye. (b) Only if a spare roll_to_pitch is printed (STRUCTURE_TWIN.md P6): hold it by its hip pitch servo pocket (the TO1 servo case in place, clamped) and hang 13.3 kg (130 N, the push peak on the idle horn ear) on the idle horn ear, across the hip roll axis, for 10 s. PASS: no crack along the layers or in the skin at the ends of the wall between the two horn ears. If (a) or (b) fails: hold the right leg; Ahmed chooses among STRUCTURE_TWIN.md P1 to P3 (DECISIONS.md D26).

### Step 3: the rest, plates for a 220 bed (13 plates)

"+ 1 spare" marks the spare set (G5, G6 below). Plates are packed by the part outline plus its supports, each under 14 h except the head. "base + rings" plates hold the 10 parts with insert rings and wait for the S1 gate; body_back carries its 5 pilot rings on a base plate.

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| P220-01 | base | head_bot_sheet | 56.9 | 3.83 |
| P220-02 | base | body_front, foot_side, battery_pack_lid, right_cache, speaker_interface, flash_light_module, bulb x2 | 157.5 | 12.48 |
| P220-03 | base | body_back (5 pilot rings), flash_reflector_interface | 80.7 | 6.67 |
| P220-04 | base + rings | body_middle_bottom, foot_top, foot_bottom_pla, leg_spacer x2 | 151.5 | 13.26 |
| P220-05 | base + rings | body_middle_top | 74.4 | 6.61 |
| P220-06 | fit | right_roll_to_pitch, roll_motor_top | 28.3 | 2.86 |
| P220-07 | insert | head | 262.0 | 21.92 |
| P220-08 | insert+fit | trunk_bottom | 42.0 | 3.53 |
| P220-09 | neck | head_pitch_to_yaw + 1 spare, neck_right_sheet + 1 spare, neck_left_sheet + 1 spare | 61.1 | 6.11 |
| P220-10 | neck+fit | head_yaw_to_roll + 1 spare, head_roll_mount + 1 spare | 89.6 | 8.56 |
| P220-11 | wall3 | speaker_stand, right_eye, roll_motor_bottom + 1 spare, left_antenna_holder + 1 spare, right_antenna_holder + 1 spare | 46.1 | 4.03 |
| P220-12 | wall3+fit | trunk_top, knee_to_ankle_left_sheet x2 + 1 spare, knee_to_ankle_right_sheet x2 + 1 spare | 114.8 | 9.87 |
| P220-13 | TPU | foot_bottom_tpu (second sole) | 17.6 | 2.19 |

Plates for a 256 bed (12 plates after the same 5 left leg plates):

| Plate | Profile | Parts | g | h |
|---|---|---|---|---|
| P256-01 | base | head_bot_sheet, right_cache, speaker_interface, flash_light_module, bulb x2, flash_reflector_interface | 131.2 | 10.44 |
| P256-02 | base | body_front, body_back (5 pilot rings), foot_side, battery_pack_lid | 164.0 | 12.70 |
| P256-03 | base + rings | body_middle_bottom, foot_top, foot_bottom_pla, leg_spacer x2 | 151.7 | 13.18 |
| P256-04 | base + rings | body_middle_top | 74.4 | 6.61 |
| P256-05 | fit | right_roll_to_pitch, roll_motor_top | 28.3 | 2.86 |
| P256-06 | insert | head | 262.0 | 21.92 |
| P256-07 | insert+fit | trunk_bottom | 42.0 | 3.53 |
| P256-08 | neck | head_pitch_to_yaw + 1 spare, neck_right_sheet + 1 spare, neck_left_sheet + 1 spare | 61.2 | 6.09 |
| P256-09 | neck+fit | head_yaw_to_roll + 1 spare, head_roll_mount + 1 spare | 89.6 | 8.53 |
| P256-10 | wall3 | speaker_stand, right_eye, roll_motor_bottom + 1 spare, left_antenna_holder + 1 spare, right_antenna_holder + 1 spare | 46.1 | 4.04 |
| P256-11 | wall3+fit | trunk_top, knee_to_ankle_left_sheet x2 + 1 spare, knee_to_ankle_right_sheet x2 + 1 spare | 114.7 | 9.87 |
| P256-12 | TPU | foot_bottom_tpu (second sole) | 17.6 | 2.19 |

S1 gate fallback: if a light coupon fails, print the "base + rings" plates (same parts, same places) with the insert profile (4 walls) and no rings. The plates still fit and show no path conflicts; one goes over the 14 h plate target.

220 bed (with L1 above):

| Plate | Fallback profile | g | h | Change g | Change h |
|---|---|---|---|---|---|
| L1-2 | insert, no rings | 60.0 | 5.60 | +11.7 | +1.02 |
| P220-04 | insert, no rings | 176.7 | 15.19 | +25.2 | +1.93 |
| P220-05 | insert, no rings | 99.0 | 7.76 | +24.5 | +1.15 |

256 bed (with its L1 plate):

| Plate | Fallback profile | g | h | Change g | Change h |
|---|---|---|---|---|---|
| L1-2 | insert, no rings | 60.2 | 5.61 | +11.8 | +1.04 |
| P256-03 | insert, no rings | 176.3 | 15.06 | +24.5 | +1.88 |
| P256-04 | insert, no rings | 99.0 | 7.76 | +24.5 | +1.15 |

With the fallback the full print is 18 jobs, 1409.3 g PLA and 122.7 h on a 220 bed (17 jobs, 1409.1 g, 122.8 h on a 256 bed).

Suggested order inside step 3: trunk_bottom first (C1 rule applies), then the neck plates (C4 rule applies), then the rest, the head last (longest job, 21.9 h); the "base + rings" plates only after the S1 gate. Every plate was sliced as one job and checked: inside the bed, no path conflicts.

### After printing: drill steps (D20, B32, D24, D25, D34)

Hand tools only (BOM T11 to T14): turn the bit slowly in the T-handle, or by hand, and blow the chips out.
1. Neck chain recesses, 24 in all, 5.5 to 6.0 mm (6.0 mm HSS bit, T11): head_pitch_to_yaw 16 (recesses 2.0 mm deep), head_yaw_to_roll 4 (4.0 mm deep), head_roll_mount 4 (5.0 mm deep); the spare set too. Stop as soon as the bit starts to cut the recess floor: the point would cut a cone into the floor under the head. Check each with a DIN 912 M3 head: it drops in and sits flat. Try it on coupon C4 first.
2. battery_pack_lid: the 4 clearance holes, 2.5 to 2.7 mm (2.7 mm HSS bit, T12), straight through, so the M2.5x10 screws pass freely and the lid clamps instead of threading.
3. 4.0 mm M2 head recesses (trunk_top, head_yaw_to_roll, roll_to_pitch): only if the C4 test showed a head that does not drop in; then open them to 4.5 mm (fasteners/FASTENERS.md finding 12; the 4.5 mm bit is BOM T15, the coupon C4 contingency).
4. Projector lead hole (D24, cable D7): drill a 4.0 mm hole through the printed head at the marked point for the D7 projector leads. The stock head.stl has no passage for them (cables3d/CABLES_3D.md); the STL stays stock. Do it before the projector parts are fitted. Where, measured on head.stl [L]:
   - Left side wall of the head (the robot's left, the side that carries flash_light_module). The hole is horizontal, square to the head's centre plane; the outer face leans 20 degrees inward toward the top, so the bit meets it at an angle.
   - Centre 34.8 mm above the bottom face of the head (head upright on a flat table; the face that takes head_bot_sheet) and 36.5 mm behind the front face (where the eyes sit). That is 24.6 mm below the top face.
   - Check with the parts: flash_light_module lies on this sloped face with its back face 2.5 mm in front of the hole centre (0.5 mm from the hole edge), and the hole centre is level with the module's 4 mm lead channel. Inside, the hole clips the round column over the front-left head insert (insert axis 3.5 mm behind the hole centre); the insert bore ends 18.8 mm below the hole and is not touched.
   - Plastic to cut: 3.2 to 6.0 mm (4.3 mm at the centre). Start it with the 2.7 mm bit (T12) so the larger bit does not walk on the slope, open it to 4.0 mm by hand, and deburr both ends so the leads are not cut.
   - CAD point: head.stl frame (83.5, 84.7, 144.5) mm; URDF world (64.5, 84.8, 209.3) mm at the zero pose; axis along y.
   - The 4.0 mm bit is BOM T14 (a 4.0 mm HSS jobber); it fits the T13 T-handle (1/16 to 1/4 in).
5. Cable tie holes (D25; cables3d/cables3d.json retention; HARNESS_BUILD.md 'Drilled tie holes'): three pairs of 4.0 mm holes with the T14 bit, each pair square to its face, deburred on both sides. The tie goes in through one hole, behind the wall and out of the other, then round the bundle. Each pair was checked in CAD with exact rays at the zero pose [L]: at least 1.6 mm of plastic round each hole and between the two, a wall of 1.6 to 12 mm, every screw, insert and empty hole at least 1.6 mm off, 1.5 mm free behind the wall, and the strap at least 1 mm from moving parts over the joint sweep. Coordinates are in each part's own STL frame (print/<part>.stl), mm.
   - T014, neck_right_sheet (holds D1, D2, D3, D4, P13 at the neck pitch loop end): two holes 12.1 mm apart through the -y face (wall 5.8 mm). Centres (26.8, -21.8, 44.7) and (14.8, -21.8, 46.4): 8.6 mm from the +x end and 10.2 mm from the -x end, 27.4 and 25.7 mm from the +z end. URDF world at the zero pose: (7.8, -21.7, 109.6) and (-4.2, -21.7, 111.2). Strap 6.2 mm from moving parts.
   - T084, the same neck_right_sheet (holds S12): two holes 7.0 mm apart through the -y face (wall 1.9 mm). Centres (22.6, -21.8, 66.7) and (15.6, -21.8, 66.4): 12.8 mm from the +x end and 11.0 mm from the -x end, 5.4 and 5.7 mm from the +z end. World (3.6, -21.7, 131.6) and (-3.4, -21.7, 131.3). Strap 6.0 mm from moving parts.
   - T072, knee_to_ankle_right_sheet of the left leg only (link knee_and_ankle_assembly_2, between the left knee and the left ankle; holds S5): two holes 7.0 mm apart through the -y face (wall 3.8 mm). Centres (-17.8, 68.2, -159.0) and (-10.9, 68.2, -158.1): 13.6 mm from the -x end and 10.2 mm from the +x end, 26.3 and 25.4 mm from the +z end. World (-36.8, 68.1, -94.1) and (-29.9, 68.1, -93.2). Strap 2.9 mm from moving parts. The right leg's copy gets no holes.

6. Camera pilots (D34, lead note; HARDWARE_AUDIT B60): drill the 4 camera pilots in head.stl from 3.2 to 4.5 mm deep with a 1/16 in (1.59 mm) bit by hand (tape flag at 4.5 mm from the boss face). The pilot stays 1.65 mm across; 1.7 mm of material stays behind the bottom (twin/complete3d/camera_seat.json, CAD check only). The 4 M2x5 from BOM 17h then engage 4.0 mm at a 1.0 mm PCB. The bit is not in the tool lines: needs Ahmed's OK.
## Orientation and supports per part

Up direction is the upstream STL axis that points up (same as PRINT_CHECK). Support grams are per part, light profile (D22).

| STL | Up | Footprint mm | Height mm | Support g | Note |
|---|---|---|---|---|---|
| battery_pack_lid | -x | 86.4 x 51.4 | 7.5 | 0.06 | |
| body_back | -x | 125.0 x 110.0 | 40.0 | 8.08 | Support under the inner ceiling; 42 degree inner walls print without support |
| body_front | +x | 143.0 x 110.0 | 10.0 | 0.00 | |
| body_middle_bottom | +z | 150.0 x 110.0 | 86.2 | 14.13 | 8 insert bores are horizontal in this orientation (they print fine, small holes bridge) |
| body_middle_top | +x | 110.0 x 56.8 | 150.0 | 8.22 | Tall: 4 of its insert bores open on the bed face |
| bulb | -x | 35.0 x 35.0 | 2.0 | 0.00 | |
| flash_light_module | +x | 41.0 x 31.5 | 28.0 | 0.32 | |
| flash_reflector_interface | +x | 23.0 x 23.0 | 12.7 | 0.05 | |
| foot_bottom_pla | -z | 93.0 x 27.7 | 8.0 | 0.37 | Blind bores open upward |
| foot_bottom_tpu | -z | 101.9 x 40.7 | 8.0 | 0.00 | No supports in TPU |
| foot_side | +y | 103.5 x 46.0 | 12.0 | 0.70 | |
| foot_top | -y | 103.5 x 46.0 | 34.9 | 0.92 | Insert bores open upward; SS-10 slots are vertical windows, 6.4 mm bridge on top |
| head | -z | 199.8 x 197.3 | 59.4 | 29.55 | Top face on the bed. Sloped back (12.5 degrees) and the horizontal bearing seat sit on support |
| head_bot_sheet | +z | 193.8 x 191.6 | 3.0 | 0.10 | Large thin plate |
| head_pitch_to_yaw | +x | 72.0 x 44.9 | 32.0 | 1.43 | |
| head_roll_mount | +z | 64.7 x 40.0 | 15.1 | 0.40 | |
| head_yaw_to_roll | +z | 87.9 x 80.0 | 42.2 | 1.83 | Support under the top arm (servo pocket ceiling) |
| knee_to_ankle_left_sheet | -y | 70.6 x 30.7 | 8.4 | 0.19 | |
| knee_to_ankle_right_sheet | +y | 70.6 x 30.7 | 7.2 | 0.17 | |
| left_antenna_holder | vector (0.263, -0.935, -0.236) | 41.2 x 25.8 | 10.1 | 0.05 | See note 1 |
| left_cache | -z | 90.0 x 40.0 | 152.6 | 1.99 | Tallest part |
| left_eye | +x | 35.0 x 35.0 | 4.3 | 0.00 | Pilots open on the bed face |
| left_roll_to_pitch | -z | 86.1 x 46.9 | 30.7 | 1.30 | |
| leg_spacer | -y | 28.1 x 10.0 | 36.9 | 0.16 | 2 insert bores open on the bed face |
| neck_left_sheet | -y | 58.0 x 30.7 | 7.1 | 0.17 | |
| neck_right_sheet | +y | 58.0 x 30.7 | 5.8 | 0.18 | |
| right_antenna_holder | vector (0.263, 0.935, -0.236) | 41.2 x 25.8 | 10.1 | 0.05 | See note 1 |
| right_cache | -z | 90.0 x 40.0 | 152.6 | 1.99 | |
| right_eye | +x | 40.0 x 40.0 | 8.4 | 0.01 | Pilots open on the bed face |
| right_roll_to_pitch | -z | 86.1 x 46.9 | 30.7 | 1.31 | |
| roll_motor_bottom | +x | 31.4 x 30.7 | 32.0 | 0.60 | |
| roll_motor_top | -z | 38.0 x 28.7 | 20.0 | 0.41 | |
| speaker_interface | vector (-0.263, -0.935, 0.236) | 37.8 x 37.8 | 6.2 | 0.00 | Laid flat, see note 2 |
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
9. 180 mm beds (for example Prusa Mini, Bambu A1 mini) fail: the head (199.8 x 197.3, 202.3 x 196.8 with supports and skirt) and head_bot_sheet (193.8 x 191.6). Everything else fits; the largest other print is body_middle_bottom at 159.6 x 109.6 mm with supports and skirt. The S1 coupon plate as generated is a 114 x 209 mm block; on a 180 bed lay the 11 coupons out again (they fit easily).
10. Supports came out of the slicer as planned: snug supports reach at most 3 mm past any part outline, the plates were packed with that margin, and no plate shows a path conflict.

## Upstream issues in the print phase (UPSTREAM_ISSUES.md G5, G6, G12)

G5, a neck part breaks often (Mini issue 33, part not named). The 5 neck and head chain parts print with the neck override (5 walls, 40% infill) and one spare set is in the plates. C4 tests the setting on head_yaw_to_roll first. Mass: the neck chain goes from 58.2 g (the 3-wall base used before D22) to 71.3 g (+13.0 g, model only), and D22 keeps it there; every neck part still weighs less than the same part solid. head_pitch_to_yaw is the one neck part with its own URDF link: the URDF mass (16.9 g) equals the solid part, the print is 15.1 g.

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

Spares in the plates (one each, 10 parts, 104.6 g, 9.8 h; all heavy, D22):
- neck_left_sheet, neck_right_sheet, head_pitch_to_yaw, head_yaw_to_roll, head_roll_mount: the three joints with the most travel times swinging mass (head_yaw, neck_pitch, head_pitch) all load these parts, the head is the heaviest swinging mass (about 0.45 kg), and head_pitch_to_yaw is the thinnest of them (4.0 mm). Same set as G5.
- knee_to_ankle_left_sheet and knee_to_ankle_right_sheet: the thinnest leg plates (3.85 and 3.90 mm), on hip pitch, knee and ankle; knee and ankle can travel 90 degrees.
- roll_motor_bottom: the thinnest hip part (2.97 mm), on hip yaw (414 g swings) and hip roll, where the G12 screw head pushes.
- left_antenna_holder and right_antenna_holder: the thinnest parts on the robot (2.0 mm) and they stick out of the head top, so they are hit first if the head swings into the body.
- Not spared: left_cache and right_cache (3.5 mm, but covers, 57 g and 5.0 h each at 2 walls; reprint only if one breaks).

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
| PLA (Overture Easy PLA) | 1407 g: coupon session 46.8 g (includes the left eye and a spare bulb) plus plates 1360.4 g (the rest of the robot set and 104.6 g of spares) | 2 x 1 kg (BOM line 27) | about 611 g (31%) for failed prints; a second head (262 g) still fits. 1450 g if the D22 gate fails |
| TPU (Overture TPU 95A) | 35.1 g: two soles (one in S2) | 1 x 1 kg (BOM line 28) | about 965 g |

BOM line 27: need 1400 g sliced (1384 g before the T1 stack pieces, 1502 g before D22): still 2 spools. BOM line 28 says 36 g; the light soles need 35.1 g.

## Not verified

- Every gram and hour is a slicer estimate on a generic printer; nothing has been printed or weighed.
- Temperatures, speeds and densities are maker-typical (Overture pages and TDS, read 2026-11-01), not lab tested.
- All coupon results (seat fit, insert seating, switch fit, servo fit, eye pilots and the eye screw stack, TPU grip and fit) are open until the coupons are printed.
- G12 assumes an ISO M2 pan head 4.0 x 1.6 mm; the Feetech bag screw head size is not published (B2). Any head over 0.31 mm tall hits at the outer screw.
- The 6.7 mm bore depth in PRINT_CHECK flag 5 and HARDWARE_AUDIT B15 was not found in any STL: every M3 insert bore is 5.8 mm deep (6.0 mm for 4 head bores); what differs is what lies beyond (see PRINT_CHECK flag 5).
- The SG90 torque is the Tower Pro figure; the TPU small-strain modulus is not published.
- The .ini files were used with the PrusaSlicer CLI; importing them into the GUI or another slicer was not tried. The coupon 3MF was sliced with the CLI only.
- Support removal on the head back slope and inside the head bearing seat is untested.
- The solid rings (D22) are untested in print: the S1 gate tests the insert rings on C2aL, C2bL and C3L; the 5 body_back pilot rings have no coupon (MASS_STUDY.md Table 1: 1.11 against 1.00 before D22). The rings exist only as PrusaSlicer modifiers in the 3MF.
- The 2-wall body shells, caches and leg parts are weaker in a fall than the parts before D22 (MASS_STUDY.md risks): keep the first walks tethered (sim/ADDED_MASS_SIM.md finding 3).
- The D24 projector lead hole position is measured on head.stl only; mark it against the real flash_light_module before drilling.

## V1 track 2 additions (2026-11-04)
- D30 button plate: print altaay_lab/twin/assembly/button_plate_d30.stl (535 mm3, about 0.6 g) with the base profile, flange down. Fit check: the plug goes into the body_back switch cutout with about 0.25 mm a side, the NKK MB2011SS1W01 bushing through the 6.4 mm hole, nut on the outside (TEST_PLAN 13).
- D29 was reverted (D33): the side lamp parts (flash_light_module, flash_reflector_interface) and the D24 lead hole stay exactly as above.

## V1 sit additions (2026-11-06 ET, D59; twin/sit/SIT.md)
- New STLs: shin_left_sheet and shin_right_sheet (3 walls and fit, as the knee_to_ankle sheets; one spare each), shin_spacer (insert rings, as leg_spacer), and the TPU parts knee_bumper (2), ankle_pad (4), hip_pad (2) on the sole profile, sit_seat and sit_bumper at 10 % infill (config/ovr_sparse.ini; the seat prints on its sloped glue face, parts.csv `up`). knee_to_ankle_left/right_sheet and leg_spacer are the thigh parts only now (2 each). Grams and hours: SLICE_SUMMARY.md D59 rows.
- The plates of this plan were laid out before D59 and are not re-run: put the shin sheets with the thigh sheets (wall3+fit job), shin_spacer with the leg_spacer rings job, and the TPU parts with the soles (session S2 or after it).
- Left-leg check 8 (before the right leg prints): TEST_PLAN.md 19.2 (the clamp block counterbores take the M2 screws and the driver, the moved heel screw, the knee bumper at 150, the ankle pads at -95, the lugs at their stops).
- The spare shin_right_sheet is the coupon of TEST_PLAN.md 19.6 (joggled sheet strength): print it with the first leg.
- 2026-11-07 ET (the stop redesign, twin/sit/SIT.md section 4): three more STLs, neck_stop (PLA, 5 walls 40 %, the neck profile, 14.8 g, 1.46 h; stands on its base, the sloped pad pockets face up and front), neck_pad x2 and head_pad (TPU, the sole profile, 0.2 and 0.6 g); head_pitch_to_yaw carries the head hook on its left arm (24.0 g, 2.53 h, same job and orientation, supports under the foot); neck_left_sheet and neck_right_sheet are the stock parts again (7.5 and 6.7 g). Robot set 47 STLs, 66 parts, 1354.0 g and 119.7 h (print/SLICE_SUMMARY.md).
- 2026-11-10 ET (design round 2, twin/sit/SIT.md section 4): the 25 changed and new STLs sliced again. Two more TPU files, roll_pad_left and roll_pad_right (the sole profile, 0.11 g each, printed on their flat end: the faces follow the servo case corner); head_pad is 12 x 6.1 x 10 mm now (0.93 g); neck_stop has a 4 mm foot behind its pillars and its pads low on the sheets' edges (14.7 g, 1.38 h); head_pitch_to_yaw's doubler covers the arm's whole outer face (24.75 g, 2.65 h); left and right roll_to_pitch carry a 14 mm wide lug with a pad pocket (25.8 g each). Robot set 49 STLs, 68 parts, 1355.5 g and 119.9 h (print/SLICE_SUMMARY.md).
