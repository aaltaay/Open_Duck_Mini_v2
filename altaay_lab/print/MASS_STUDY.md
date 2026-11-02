# MASS_STUDY: the lightest print settings that keep every strength and fit rule

Status: adopted as DECISIONS.md D22 (variant c, gated by the light coupons C2aL, C2bL and C3L in session S1). print/config/ and print/parts.csv now hold variant (c); the settings of variant (b) stay reachable as config/*_heavy.ini and the parts.csv "heavy" column (`slice.py --set heavy`). config_light/ is kept unchanged as this study's input, and mass_study.py still reproduces every table below. The new plates and totals are in PRINT_PLAN.md and SLICE_SUMMARY.md.

Written 2026-11-02 by agent PM (print mass) for the lead, who decides whether to adopt it. Nothing has been printed or weighed. Grams and hours are PrusaSlicer 2.7.2 estimates made on the box for the generic printer of config/printer_generic.ini [L]; robot mass, centre of mass and walking come from the sim agent's code and are **sim pass only**. Script: print/mass_study.py. Proposed configs: print/config_light/ (copies; print/config/ and parts.csv are unchanged). G-code, 3MF and oriented STLs stay in the scratch folder, never in the repo.

Tags: [L] lab file, script or slicer output on this box; [U] upstream file; [I] internet source with its URL.

## Answer

| Robot set, 36 STLs, 52 parts | Filament g | On the robot g | Print hours | Whole robot g (sim pass only) | Over the trained 2107.1 g |
|---|---|---|---|---|---|
| (a) upstream defaults | 1178.1 | 1090.5 | 102.0 | 2538.7 | +20.5 % |
| (b) current settings | 1409.0 | 1318.7 | 118.9 | 2766.9 | +31.3 % |
| **(c) lightest safe, proposed** | **1280.3** | **1190.4** | **111.1** | **2638.7** | **+25.2 %** |
| (d) = (c) with a light head, not proposed | 1231.6 | 1141.8 | 107.6 | 2590.0 | +22.9 % |

All numbers [L] (mass_study.py tables and budget). Filament grams include support and skirt; "on the robot" is filament less support, the way sim/mass_budget.py counts a printed part.

- **(c) wins back 128.2 g** against today (b), 48 % of the 267.4 g by which the parts the trained CAD also has outweigh it (sim/MASS_BUDGET.md table 3) [L]. Where (sim pass only) [L]: trunk -49.5 g, each thigh -21.7 g, each foot -10.7 g, each hip pitch link -3.6 g, each shin -1.7 g, head -1.6 g, each hip roll link -0.8 g, neck chain 0 g. The feet end 2.7 g over the trained model (13.4 g today), the thighs 20.9 g (42.6 g today).
- **Centre of mass** (home pose, trunk frame, sim pass only) [L]: today (-28.1, 0.5, 47.0) mm, (c) (-27.6, 0.4, 49.8) mm, trained (-25.6, -0.6, 44.0) mm. (c) moves it **0.5 mm forward** and 2.9 mm up, because the mass comes off the trunk shells behind it and the legs below it. It sits 2.3 mm ahead of the foot sites (today 1.7 mm, trained 4.2 mm), about 1.0 mm ahead of the ankle servo axes.
- **Walking** (sim pass only, the sim agent's cases, 6 seeds, rough terrain 18) [L]: (c) is as good as today or better in every case: forward 0.70 of the command (today 0.67, trained 0.73), turn 0.81 (0.79), backlash model 0.90 (0.88), 15 N pushes no falls in either; rough terrain falls about as often as today (16 of 18 seeds against 18 of 18, mean first fall 11.6 s against 11.4 s); the backward centre of mass margin is unchanged. **The side step stays at 0.24 (today 0.23, trained 0.46)**: no print setting brings it back; even (a) gives 0.25. The (c) walk numbers are the re-run on today's 2652.8 g model (Walking section, re-run 2026-11-02 6:02 AM ET).
- **Why the head stays heavy**: of the parts we could lighten, the head is the one that sits well ahead of the robot centre of mass (51 mm), so lightening it moves the centre of mass back. (d), the light head (2 walls with 21 rings, 48.7 g less), meets every strength and fit rule, but in the sim it costs one step of the backward margin test (about 0.9 mm) and falls sooner on rough terrain (mean first fall 7.7 s) [L]. The backward margin is the narrow side (sim/ADDED_MASS_SIM.md), so (c) keeps the head at today's 4 walls.
- **What stays heavy**: the head (above); the 5 neck chain parts (5 walls, 40 %, upstream issue 33, G5); the G6 thinnest parts at 3 walls (knee sheets, roll_motor_bottom, antenna holders); the frame, trunk_top and trunk_bottom, as today (both legs and the neck hang from them; light versions would save only 13.1 g); the eyes and speaker_stand (screw pilots, tested profile, under 1 g). All spares keep today's settings.
- **What changes**: every other part prints at the upstream default of 2 walls and 15 %, and the parts with M3 inserts or screw pilots get a **solid ring round each such hole** (a PrusaSlicer infill modifier) instead of extra walls on the whole part. The G-code puts as much plastic within the rule distance of every ringed hole as today's walls do (Table 1).
- **Risk**: the rings are new and untested in print, and 2-wall body shells and caches are weaker in a fall than today's near-solid ones. Gate: print light copies of coupons C2a, C2b and C3 next to the current ones in session S1 (+8.4 g, +0.9 h); adopt the 10 light insert parts only if they pass the same tests, otherwise those keep 4 walls (+61.7 g) and the rest of (c) still stands.

## The variants

All variants use the same printer, filament, layer height (0.20 mm), top and bottom layers (5 and 4), gyroid infill, supports (snug, below 40 degrees), speeds, densities (PLA 1.20, TPU 1.216 g/cm3) and orientation (parts.csv "up"). They differ only in walls, infill and rings.

| Variant | What | Files |
|---|---|---|
| (a) upstream defaults | docs/print_guide.md: "All the parts are printed in standard PLA with 15% infill, except for foot_bottom_tpu.stl, which is to be printed in TPU at 40% infill" [U]. The guide says nothing about walls, so the slicer default of 2. Every Prusa 0.20 mm print profile bundled with PrusaSlicer 2.7.2 resolves to 2 walls, 5 top and 4 bottom layers and 15 % infill [L] (/usr/share/PrusaSlicer/profiles/PrusaResearch.ini, config_version 1.11.12, "[print:*common*] perimeters = 2"; checked 0.20mm QUALITY and SPEED @MK3, QUALITY and SPEED @MK4 0.4, SPEED and STRUCTURAL @MK4IS 0.4, QUALITY @MINI). The CLI's built-in fallback is 3 walls, but that fallback also means 0.3 mm layers and 20 % stars infill, which no printer profile ships [L] (prusa-slicer --help-fff). The old PRINT_CHECK run also used 2 walls. No per-part overrides. | config_light/pla_print.ini and tpu_print.ini (2 walls; otherwise identical to config/) |
| (b) current | config/ with the parts.csv overrides: 3 walls base, insert 4 walls, neck 5 walls and 40 %, fit outer wall first at 25 mm/s. Built exactly as slice.py builds it; it reproduces SLICE_SUMMARY.md to 0.01 g per part and in total (1409.0 g, 118.9 h) [L]. | config/, parts.csv |
| (c) lightest safe | (a), plus each lab override only where its stated reason needs it, applied locally where the reason is local (rings); plus the head kept at 4 walls on the sim evidence below. Per part in config_light/parts_light.csv with the reason. | config_light/ |
| (d) light head | (c) with the head at 2 walls and 21 rings (12 inserts, 8 pilots, 1 seat). Reported, not proposed. | mass_study.py D_PARTS |

### Rings: local reinforcement instead of whole-part walls

The insert rule (4 walls give about 1.67 mm of solid plastic round each 4.0 mm bore; lab minimum 1.6 mm from CNC Kitchen, PRINT_CHECK.md flag 1; ovr_insert.ini) and the pilot rule (3 walls give a solid ring round each 2.0 mm screw pilot, config/pla_print.ini) are about the plastic next to a hole, but today they set the walls of the whole part: 4 walls cost body_middle_top 24.6 g and foot_top 8.6 g each against 2 walls [L]. In (c) each such hole gets a modifier cylinder, coaxial with the hole and 0.6 mm longer at each end, with 100 % infill inside: insert bores 2.0 mm of solid plastic, screw pilots 1.5 mm, 6804 seats 2.0 mm (config_light/mod_ring.ini). A cylinder modifier round a hole with more walls or 100 % infill is the usual way to make one area of a print solid [I] (Prusa modifier tutorial and Prusa forum, Sources).

- Which holes: found in each print-oriented STL by sections every 0.2 mm (mass_study.py holes). The counts match the audit [L]: 58 insert bores (head 12, body_middle_bottom 8, horizontal in its print orientation, body_middle_top 8, trunk_bottom 6, leg_spacer 4 per part, foot_top 2 per part, foot_bottom_pla 2 per part; PRINT_CHECK.md), the screw pilots of head (8), trunk_top (8), body_back (5), the eyes (4 each) and speaker_stand (2) (audit/sites.json, sites_head.json), and the 32.18 mm seats of the head (1) and trunk_bottom (2). flash_light_module's 4.0 mm hole is a 14.6 mm light channel, not an insert bore, and gets no ring. In (c) the rings go on body_middle_bottom, body_middle_top, body_back, foot_top, foot_bottom_pla and leg_spacer (45 holes per robot: 40 insert bores and 5 pilots); the head, trunk_top, trunk_bottom, eyes and speaker_stand keep whole-part walls.
- Walls stay whole: a ring set to the base 15 % gives the same grams as no ring (body_middle_top 74.060 g both; body_middle_bottom 102.33 against 102.35 g) [L], so PrusaSlicer adds no walls at the ring edge; only the infill inside the ring changes.
- Cost: 0.3 to 0.9 g per part on the robot (body_middle_bottom 0.86 g for 8 rings) [L], against 1.4 to 24.6 g for today's whole-part walls on the same parts.

**Table 1: does the plastic next to each ringed hole meet the rule?** [L] (mass_study.py rings). Filament laid in the band from 0.15 mm off the hole wall out to the rule distance (insert 1.6 mm, pilot 1.27 mm, seat 1.67 mm), divided by the part material in that band (mesh sampled). Lines count where their centre lies, so a solid band reads a little over 1; 15 % infill in the band pulls it under 1.

| Part | Holes | (a) 2 walls | (b) today | Rings ((c); head: (d)) |
|---|---|---|---|---|
| body_middle_top | 8 inserts | 0.95 | 1.09 | 1.09 |
| body_middle_bottom | 8 inserts | 1.00 | 1.06 | 1.07 |
| body_back | 5 pilots | 0.89 | 1.00 | 1.11 |
| foot_top | 2 inserts | 0.88 | 1.12 | 1.19 |
| foot_bottom_pla | 2 inserts | 0.76 | 1.10 | 1.15 |
| leg_spacer | 4 inserts | 0.86 | 1.14 | 1.16 |
| head, option (d) | 12 inserts | 0.98 | 1.11 | 1.11 |
| head, option (d) | 8 pilots | 1.02 | 1.05 | 1.06 |
| head, option (d) | 1 seat | 1.00 | 1.02 | 1.07 |

The rings put at least as much plastic next to every hole as (b). (a) leaves sparse infill inside the rule distance of foot_bottom_pla, leg_spacer, foot_top, body_back and body_middle_top. The extrusion type labels are kept in rings_check.json, but they cannot settle this alone: in the head seat ring PrusaSlicer labels the infill of the large 100 % region "Internal infill" although it is dense (solidity 1.07), while regions under 70 mm2 are labelled "Solid infill" (solid_infill_below_area = 70, config/pla_print.ini).

## Table 2: per part, (a), (b) and (c)

Grams are per part (filament, then on the robot), hours per part. Trained model g: the trained model's own part masses from sim/MASS_BUDGET.md table 4 (thigh / shin where a part is on both links; the right leg links are mirror copies, table 2). The trunk and head fits are not unique, so those parts have no trained mass of their own ("-") [L]. Option (d) differs only in the head: 213.38 g, 183.80 g on the robot, 18.42 h [L].

| STL | Qty | Trained model g [L] | (a) g | (a) on robot g | (a) h | (b) g | (b) on robot g | (b) h | (c) g | (c) on robot g | (c) h | (c) settings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| battery_pack_lid.stl | 1 | - | 13.64 | 13.58 | 1.01 | 14.05 | 13.99 | 1.04 | 13.64 | 13.58 | 1.01 | base |
| body_back.stl | 1 | - | 78.01 | 70.03 | 6.37 | 88.06 | 79.93 | 6.94 | 78.43 | 70.35 | 6.46 | base, rings 5 pilot |
| body_front.stl | 1 | - | 57.87 | 57.87 | 4.03 | 60.33 | 60.33 | 4.22 | 57.87 | 57.87 | 4.03 | base |
| body_middle_bottom.stl | 1 | - | 102.23 | 88.10 | 8.56 | 116.52 | 101.78 | 9.53 | 103.09 | 88.96 | 8.61 | base, rings 8 insert |
| body_middle_top.stl | 1 | - | 74.08 | 65.86 | 6.56 | 98.95 | 90.47 | 7.76 | 74.43 | 66.21 | 6.61 | base, rings 8 insert |
| bulb.stl | 2 | - | 2.04 | 2.04 | 0.17 | 2.05 | 2.05 | 0.17 | 2.04 | 2.04 | 0.17 | base |
| flash_light_module.stl | 1 | - | 8.40 | 8.08 | 0.80 | 9.13 | 8.81 | 0.87 | 8.40 | 8.08 | 0.80 | base |
| flash_reflector_interface.stl | 1 | - | 2.32 | 2.27 | 0.24 | 2.57 | 2.51 | 0.25 | 2.32 | 2.27 | 0.24 | base |
| foot_bottom_pla.stl | 2 | 19.0 | 9.53 | 9.16 | 0.75 | 10.89 | 10.52 | 0.85 | 9.84 | 9.47 | 0.78 | base, rings 2 insert |
| foot_bottom_tpu.stl | 2 | 19.0 | 17.57 | 17.57 | 2.18 | 18.15 | 18.15 | 2.25 | 17.57 | 17.57 | 2.18 | base |
| foot_side.stl | 2 | 13.9 | 13.68 | 12.98 | 1.14 | 14.87 | 14.14 | 1.23 | 13.68 | 12.98 | 1.14 | base |
| foot_top.stl | 2 | 23.4 | 22.98 | 22.37 | 1.95 | 31.63 | 31.00 | 2.69 | 23.98 | 23.06 | 2.09 | base, rings 2 insert |
| head.stl | 1 | - | 211.73 | 182.18 | 18.32 | 262.01 | 232.46 | 21.96 | 262.01 | 232.46 | 21.96 | insert |
| head_bot_sheet.stl | 1 | - | 56.89 | 56.79 | 3.83 | 57.52 | 57.40 | 3.88 | 56.89 | 56.79 | 3.83 | base |
| head_pitch_to_yaw.stl | 1 | 16.9 | 13.49 | 12.07 | 1.43 | 16.57 | 15.14 | 1.73 | 16.57 | 15.14 | 1.73 | neck |
| head_roll_mount.stl | 1 | - | 11.57 | 11.30 | 0.99 | 15.74 | 15.34 | 1.42 | 15.74 | 15.34 | 1.42 | neck+fit |
| head_yaw_to_roll.stl | 1 | 36.5 | 19.64 | 17.81 | 1.85 | 29.05 | 27.22 | 2.81 | 29.05 | 27.22 | 2.81 | neck+fit |
| knee_to_ankle_left_sheet.stl | 4 | 4.1 / 4.4 | 6.43 | 6.27 | 0.58 | 6.98 | 6.79 | 0.64 | 6.98 | 6.79 | 0.64 | wall3+fit |
| knee_to_ankle_right_sheet.stl | 4 | 3.3 / 3.5 | 5.87 | 5.72 | 0.54 | 6.32 | 6.15 | 0.60 | 6.32 | 6.15 | 0.60 | wall3+fit |
| left_antenna_holder.stl | 1 | - | 3.56 | 3.51 | 0.27 | 3.57 | 3.52 | 0.28 | 3.57 | 3.52 | 0.28 | wall3 |
| left_cache.stl | 1 | 51.6 | 57.26 | 55.27 | 4.95 | 77.34 | 75.35 | 5.97 | 57.26 | 55.27 | 4.95 | base |
| left_eye.stl | 1 | - | 1.85 | 1.85 | 0.17 | 1.80 | 1.80 | 0.18 | 1.80 | 1.80 | 0.18 | wall3 |
| left_roll_to_pitch.stl | 1 | 20.5 | 21.24 | 19.95 | 1.94 | 24.82 | 23.53 | 2.31 | 21.24 | 19.95 | 2.09 | fit |
| leg_spacer.stl | 4 | 8.9 / 8.7 | 6.34 | 6.18 | 0.77 | 8.83 | 8.67 | 1.00 | 7.17 | 7.01 | 0.85 | base, rings 4 insert |
| neck_left_sheet.stl | 1 | 6.0 | 5.46 | 5.32 | 0.48 | 7.49 | 7.32 | 0.70 | 7.49 | 7.32 | 0.70 | neck |
| neck_right_sheet.stl | 1 | 5.1 | 5.08 | 4.93 | 0.46 | 6.55 | 6.37 | 0.61 | 6.55 | 6.37 | 0.61 | neck |
| right_antenna_holder.stl | 1 | - | 3.56 | 3.51 | 0.27 | 3.57 | 3.52 | 0.28 | 3.57 | 3.52 | 0.28 | wall3 |
| right_cache.stl | 1 | 51.6 | 57.21 | 55.22 | 4.95 | 77.32 | 75.33 | 6.03 | 57.21 | 55.22 | 4.95 | base |
| right_eye.stl | 1 | - | 4.15 | 4.15 | 0.36 | 4.56 | 4.55 | 0.38 | 4.56 | 4.55 | 0.38 | wall3 |
| right_roll_to_pitch.stl | 1 | 20.5 | 21.20 | 19.89 | 1.97 | 24.82 | 23.52 | 2.33 | 21.20 | 19.89 | 2.12 | fit |
| roll_motor_bottom.stl | 2 | 5.5 | 7.08 | 6.48 | 0.64 | 8.75 | 8.15 | 0.72 | 8.75 | 8.15 | 0.72 | wall3 |
| roll_motor_top.stl | 2 | 7.6 | 7.14 | 6.73 | 0.69 | 8.00 | 7.52 | 0.80 | 7.14 | 6.73 | 0.73 | fit |
| speaker_interface.stl | 1 | - | 2.33 | 2.33 | 0.22 | 2.33 | 2.33 | 0.22 | 2.33 | 2.33 | 0.22 | base |
| speaker_stand.stl | 1 | - | 9.86 | 7.42 | 1.11 | 10.11 | 7.64 | 1.16 | 10.11 | 7.64 | 1.16 | wall3 |
| trunk_bottom.stl | 1 | - | 33.58 | 33.30 | 2.83 | 41.99 | 41.71 | 3.54 | 41.99 | 41.71 | 3.54 | insert+fit |
| trunk_top.stl | 1 | - | 67.33 | 60.55 | 5.43 | 75.08 | 67.29 | 6.14 | 75.08 | 67.29 | 6.14 | wall3+fit |

| Material | Parts | (a) g | (a) on robot g | (a) h | (b) g | (b) on robot g | (b) h | (c) g | (c) on robot g | (c) h |
|---|---|---|---|---|---|---|---|---|---|---|
| PLA | 50 | 1143.0 | 1055.3 | 97.6 | 1372.7 | 1282.4 | 114.4 | 1245.1 | 1155.3 | 106.7 |
| TPU | 2 | 35.1 | 35.1 | 4.4 | 36.3 | 36.3 | 4.5 | 35.1 | 35.1 | 4.4 |
| all | 52 | 1178.1 | 1090.5 | 102.0 | 1409.0 | 1318.7 | 118.9 | 1280.3 | 1190.4 | 111.1 |

(c) settings: "base" is config_light/pla_print.ini (2 walls, 15 %; TPU 2 walls, 40 %); wall3, neck, fit and insert are the override files in config_light/; rings are config_light/mod_ring.ini. Without rings, (c) would be 1351.9 g, 1261.7 g on the robot and 115.6 h (the ring parts keeping their (b) settings): 57.0 g of the win; the rings carry the other 71.3 g [L].

## What each part gets in (c), and why

| Group | Parts (qty) | (c) settings | Reason |
|---|---|---|---|
| Head, unchanged | head (1) | insert (4 walls) | Sim evidence (walking section): the light head of (d) costs one step of backward margin and falls sooner on rough terrain [L]; it also keeps the shell's fall strength |
| Neck chain, unchanged | head_pitch_to_yaw, head_roll_mount, head_yaw_to_roll, neck_left_sheet, neck_right_sheet (5) | neck (5 walls, 40 %), fit where today | Upstream Mini issue 33: a neck part breaks often (UPSTREAM_ISSUES.md G5); Runtime issue 32 broke a head part (G6) [L]. These print close to solid already (head_pitch_to_yaw 15.1 g against 16.3 g solid) [L] |
| G6 thinnest parts, unchanged | knee_to_ankle_left_sheet (4), knee_to_ankle_right_sheet (4), roll_motor_bottom (2), left and right antenna_holder (2) | 3 walls (wall3), fit on the knee sheets | PRINT_PLAN.md G6 table: thinnest walls at their joints (3.90, 3.85, 2.97, 2.0 mm), all spared [L] |
| Frame, unchanged | trunk_top (1), trunk_bottom (1) | as today (3 walls + fit; 4 walls + fit) | Judgment: trunk_top holds the two hip yaw servos (cases at x -33.4, y +-35 mm) and the neck pitch servo, and trunk_bottom the two 6804 bearings under the hip yaw servos (x -19, y +-35 mm; trunk frame, URDF) [L], so both legs and the neck hang from these two parts; coupon C1 is in this profile. Light versions with rings: trunk_top 67.52 g (60.74 on the robot), trunk_bottom 35.39 g (35.13), 13.1 g less in all [L] |
| Small parts with screw pilots, unchanged | left_eye, right_eye, speaker_stand (3) | 3 walls (wall3) | Pilot rule; coupon T1 tests the eye profile; 0.57 g in all against 2 walls [L] |
| Rings | body_middle_bottom (1), body_middle_top (1), body_back (1), foot_top (2), foot_bottom_pla (2), leg_spacer (4) | 2 walls, 15 %, rings | Insert and pilot rules kept at each hole (Table 1); nothing else asks for more walls |
| Upstream default | left_cache, right_cache (2), body_front, head_bot_sheet, battery_pack_lid, foot_side (2), bulb (2), flash_light_module, flash_reflector_interface, speaker_interface, foot_bottom_tpu (2, TPU 40 %) | 2 walls, 15 % | No stated reason for more. The caches are covers (PRINT_PLAN.md G6: not spared "but covers") [L] |
| Upstream default, fit kept | left_roll_to_pitch, right_roll_to_pitch, roll_motor_top (2) | 2 walls, 15 %, fit | Servo pocket fit kept (outer wall first, 25 mm/s); no stated reason for more walls |

The biggest single wins on the robot are body_middle_top (-24.3 g), the two caches (-20.1 g each), body_middle_bottom (-12.8 g), body_back (-9.6 g), foot_top (-7.9 g each), roll_to_pitch (-3.6 g each) and leg_spacer (-1.7 g each) [L].

For the big leg parts (a) lands close to the trained masses: left_cache 55.3 g against 51.6 g, roll_to_pitch 20.0 g against 20.5 g, foot_top 22.4 g against 23.4 g, foot_side 13.0 g against 13.9 g [L] (Table 2, MASS_BUDGET.md table 4). This is consistent with the trained model having been built from parts printed at the upstream defaults, but the fit cannot prove it.

## Table 3: per link and whole robot (sim pass only)

Method copied, not edited: mass_study.py imports sim/mass_budget.py unchanged and replaces only the slice table that build_budget() reads (per part: filament g and support g, exactly the SLICE_SUMMARY.md columns it uses). Check [L]: with the SLICE_SUMMARY.md table it gives 2766.9 g, as in MASS_BUDGET.md; the home-pose centre of mass comes out at x -28.12 mm against -28.2 mm there, which is the seat fix committed after that run (aa7263e moved the BEC Pro 7 mm toward +x: 33.6 g x 7 mm / 2767 g = 0.08 mm). All variants below use today's inputs.

| Link (MJCF body) | Trained g [U] | (b) g | (c) g | (c) - (b) g | (c) - trained g | (b) printed g | (c) printed g |
|---|---|---|---|---|---|---|---|
| trunk | 698.5 | 984.5 | 935.0 | -49.5 | +236.5 | 455.5 | 406.0 |
| L hip roll link | 66.5 | 77.5 | 76.7 | -0.8 | +10.2 | 15.7 | 14.9 |
| L hip pitch link | 75.2 | 88.6 | 85.1 | -3.6 | +9.9 | 23.5 | 19.9 |
| L thigh (knee servo) | 124.1 | 166.7 | 145.0 | -21.7 | +20.9 | 97.0 | 75.2 |
| L shin (ankle servo) | 72.6 | 91.2 | 89.5 | -1.7 | +16.9 | 21.6 | 19.9 |
| L foot | 75.2 | 88.6 | 77.9 | -10.7 | +2.7 | 73.8 | 63.1 |
| neck pitch link | 66.2 | 82.8 | 82.8 | +0.0 | +16.6 | 13.7 | 13.7 |
| head pitch link | 16.9 | 33.5 | 33.5 | +0.0 | +16.6 | 15.1 | 15.1 |
| head yaw link | 91.8 | 92.0 | 92.0 | +0.0 | +0.2 | 27.2 | 27.2 |
| head | 406.6 | 548.6 | 547.0 | -1.6 | +140.4 | 344.0 | 342.4 |
| R hip roll link | 66.5 | 77.5 | 76.7 | -0.8 | +10.2 | 15.7 | 14.9 |
| R hip pitch link | 75.2 | 88.6 | 85.0 | -3.6 | +9.8 | 23.5 | 19.9 |
| R thigh (knee servo) | 124.1 | 166.8 | 145.0 | -21.8 | +20.9 | 96.9 | 75.2 |
| R shin (ankle servo) | 72.6 | 91.2 | 89.5 | -1.7 | +16.9 | 21.6 | 19.9 |
| R foot | 75.2 | 88.6 | 77.9 | -10.7 | +2.7 | 73.8 | 63.1 |
| total | 2107.1 | 2766.9 | 2638.7 | -128.2 | +531.5 | 1318.7 | 1190.4 |

| Variant | Robot g | vs trained | Home pose CoM mm (trunk frame) | CoM - trained mm | CoM - (b) mm | Zero pose CoM mm |
|---|---|---|---|---|---|---|
| trained | 2107.1 | - | [-25.6, -0.6, 44.0] | - | - | [-22.7, -0.7, 39.7] |
| (a) upstream defaults | 2538.7 | +20.5 % | [-28.7, 0.4, 46.2] | [-3.0, 1.0, 2.3] | [-0.5, -0.1, -0.8] | [-25.6, 0.3, 42.5] |
| (b) current | 2766.9 | +31.3 % | [-28.1, 0.5, 47.0] | [-2.5, 1.1, 3.0] | [0.0, 0.0, 0.0] | [-25.2, 0.4, 43.3] |
| (c) lightest safe, proposed | 2638.7 | +25.2 % | [-27.6, 0.4, 49.8] | [-1.9, 1.0, 5.9] | [0.5, -0.1, 2.9] | [-24.6, 0.3, 46.2] |
| (d) light head option | 2590.0 | +22.9 % | [-28.4, 0.4, 46.8] | [-2.8, 1.0, 2.8] | [-0.3, -0.1, -0.2] | [-25.4, 0.3, 43.1] |
| (c) without rings | 2709.9 | +28.6 % | [-28.1, 0.5, 48.3] | [-2.5, 1.1, 4.3] | [-0.0, -0.0, 1.3] | [-25.2, 0.4, 44.5] |

Inertia about the link centre of mass (principal, kg m2 x 1e-4) [L]: trunk trained 16.76, 29.27, 34.45; (b) 21.49, 37.31, 44.19; (c) 19.54, 34.83, 41.20, so the trunk excess falls from about 28 % to 17 to 20 %. Head trained 10.73, 16.87, 24.53; (b) 15.20, 20.66, 32.26; (c) 15.10, 20.58, 32.09 (unchanged); (d) 13.36, 18.35, 28.49.

Where the centre of mass moves (home pose, sim pass only) [L]: with the light head of (d), the head loses 50.3 g at x +22.7 mm, 51 mm ahead of the robot centre of mass, which pulls it 0.9 mm back, while the lighter trunk shells (-49.5 g at x -55.7 mm) and thighs push it 0.6 mm forward: net 0.3 mm back. With the head kept, (c) keeps only the forward push: 0.5 mm forward.

## Walking with the (c) robot (sim pass only)

mass_study.py walk imports sim/added_mass_sim.py unchanged (write_variant, run, gait_stats; policy BEST_WALK_ONNX_2, the same cases, seeds and fall rule) and writes model copies for (a), (b), (c) and (d) in the scratch folder. Check [L]: the trained model and (b) reproduce ADDED_MASS_SIM.md tables 1 and 2 on flat ground (trained: forward 0.73, turn 0.82, side 0.46, pushes 6 of 6 fall; ours: forward 0.67, side 0.23, pushes 0 of 6). Rough terrain for (b) moved after the BEC Pro seat fix (nominal fall at 8.64 s against 4.3 s there; seeds 6 of 6 against 5 of 6), which shows how sensitive that case is; 18 seeds are used below for that reason. Model names: stock = trained, ours_b = (b), light_c = (c), light_d = (d), upstream_a = (a).

Re-run 2026-11-02 5:59 to 6:02 AM ET by agent SFX (sim pass only): the (c) column of the two tables below, the (c) rows of the backward margin table and the (c) rough terrain seeds come from `mass_study.py walk` run again on today's model: the (c) slice table of print/SLICE_SUMMARY.md (the D22 print as adopted) and today's netlist, 2652.8 g (sim/MASS_BUDGET.md; 2638.7 g in this study: +14.1 g of wire from the netlist final pass and agent CAB's later cut changes). Why: VERIFICATION.md C8 compares its own walk of the build model with this column; after the cut changes its 15 N pushes run tracked 0.618 against the 0.63 here, past the check's 0.011. Run-to-run change of the nominal runs against the study: forward -0.004, turn -0.004, side -0.001, backlash -0.003, pushes -0.013 (0.631 to 0.618). The same script with the study's own slice table (left_roll_to_pitch support 1.29 against 1.30 g, 0.01 g) gives 0.626 for pushes and 0.237 for side, and the 6 seeded pushes runs span 0.614 to 0.629 (0.617 to 0.638 in the study): a single run moves by up to about 0.01 from tiny model changes, which is run-to-run noise, not a change in the walk. No run fell on flat ground (35 runs). Rough terrain stays chaotic: 16 of 18 seeds fall (18 of 18 in the study), mean first fall 11.6 s (11.3 s); the nominal run falls at 6.86 s (25.78 s). The backward margin runs fall at the same steps as before (fall times within 0.08 s). The trained, (b), (d) and (a) columns and tables 1 to 3 stay the study's run at its inputs.

| Case (nominal run) | trained (stock) | (b) today | (c) proposed | (d) light head | (a) upstream |
| --- | --- | --- | --- | --- | --- |
| walk_side_0.2 | 0.47, pitch +0.8 deg | 0.23, pitch +1.0 deg | 0.24, pitch +0.9 deg | 0.25, pitch +0.7 deg | 0.25, pitch +0.6 deg |
| walk_forward_0.15 | 0.73, pitch +1.6 deg | 0.67, pitch +2.9 deg | 0.70, pitch +2.6 deg | 0.67, pitch +2.1 deg | 0.67, pitch +1.8 deg |
| turn_1.0 | 0.82, pitch +1.1 deg | 0.78, pitch +2.2 deg | 0.81, pitch +2.0 deg | 0.80, pitch +1.7 deg | 0.80, pitch +1.5 deg |
| walk_backlash | 0.95, pitch +2.1 deg | 0.88, pitch +4.2 deg | 0.90, pitch +3.7 deg | 0.92, pitch +3.0 deg | 0.94, pitch +2.6 deg |
| walk_pushes | fell at 10.68 s | 0.60, pitch +3.0 deg | 0.62, pitch +2.9 deg | 0.59, pitch +2.4 deg | 0.61, pitch +2.1 deg |
| walk_rough_backlash_raised_start | fell at 9.14 s | fell at 8.64 s | fell at 6.86 s | fell at 7.22 s | - |

Tracking is measured speed over command. Torso pitch is positive nose down.

| Case (seeds 1 to 6) | Model | Runs that fell | First fall (s) | Tracking mean (min to max), runs that did not fall |
| --- | --- | --- | --- | --- |
| walk_side_0.2 | trained (stock) | 0 of 6 | - | 0.46 (0.42 to 0.47) |
| walk_side_0.2 | (b) today | 0 of 6 | - | 0.23 (0.23 to 0.24) |
| walk_side_0.2 | (c) proposed | 0 of 6 | - | 0.24 (0.24 to 0.25) |
| walk_side_0.2 | (d) light head | 0 of 6 | - | 0.24 (0.23 to 0.25) |
| walk_side_0.2 | (a) upstream | 0 of 6 | - | 0.25 (0.23 to 0.26) |
| walk_forward_0.15 | trained (stock) | 0 of 6 | - | 0.73 (0.73 to 0.74) |
| walk_forward_0.15 | (b) today | 0 of 6 | - | 0.67 (0.67 to 0.67) |
| walk_forward_0.15 | (c) proposed | 0 of 6 | - | 0.70 (0.70 to 0.70) |
| walk_forward_0.15 | (d) light head | 0 of 6 | - | 0.68 (0.67 to 0.68) |
| walk_forward_0.15 | (a) upstream | 0 of 6 | - | 0.67 (0.67 to 0.68) |
| turn_1.0 | trained (stock) | 0 of 6 | - | 0.82 (0.82 to 0.82) |
| turn_1.0 | (b) today | 0 of 6 | - | 0.79 (0.79 to 0.79) |
| turn_1.0 | (c) proposed | 0 of 6 | - | 0.81 (0.80 to 0.81) |
| turn_1.0 | (d) light head | 0 of 6 | - | 0.79 (0.79 to 0.80) |
| turn_1.0 | (a) upstream | 0 of 6 | - | 0.80 (0.79 to 0.80) |
| walk_backlash | trained (stock) | 0 of 6 | - | 0.95 (0.95 to 0.95) |
| walk_backlash | (b) today | 0 of 6 | - | 0.88 (0.87 to 0.88) |
| walk_backlash | (c) proposed | 0 of 6 | - | 0.90 (0.90 to 0.90) |
| walk_backlash | (d) light head | 0 of 6 | - | 0.92 (0.92 to 0.92) |
| walk_backlash | (a) upstream | 0 of 6 | - | 0.93 (0.93 to 0.94) |
| walk_pushes | trained (stock) | 6 of 6 | 20.0, 22.8, 14.3, 14.1, 22.7, 20.0 | - |
| walk_pushes | (b) today | 0 of 6 | - | 0.60 (0.59 to 0.61) |
| walk_pushes | (c) proposed | 0 of 6 | - | 0.62 (0.61 to 0.63) |
| walk_pushes | (d) light head | 0 of 6 | - | 0.60 (0.58 to 0.61) |
| walk_pushes | (a) upstream | 0 of 6 | - | 0.60 (0.58 to 0.61) |
| walk_rough_backlash_raised_start | trained (stock) | 10 of 18 | 8.0, 5.7, 6.4, 22.2, 5.5, 5.1, 4.0, 23.8, 13.2, 6.7 | 0.85 (0.82 to 0.87) |
| walk_rough_backlash_raised_start | (b) today | 18 of 18 | 14.9, 6.3, 8.7, 12.0, 11.5, 6.5, 25.5, 6.6, 16.2, 6.7, 14.7, 4.5, 4.7, 24.7, 4.2, 16.2, 13.8, 7.1 | - |
| walk_rough_backlash_raised_start | (c) proposed | 16 of 18 | 8.3, 6.6, 8.0, 17.8, 13.0, 6.5, 29.0, 15.5, 4.7, 9.3, 4.3, 4.8, 4.3, 4.2, 6.2, 7.0 | 0.83 (0.82 to 0.84) |
| walk_rough_backlash_raised_start | (d) light head | 17 of 18 | 2.4, 6.9, 8.5, 9.1, 4.8, 6.6, 4.6, 6.1, 17.9, 4.6, 5.8, 4.3, 5.0, 5.4, 4.0, 7.8, 5.3 | 0.82 (0.82 to 0.82) |

Mean first fall, counting a run that does not fall as 30 s: trained 18.9 s, (b) 11.4 s, (c) 11.6 s, (d) 7.7 s; against (b), (c) falls later in 5 seeds, earlier in 7 and within 0.5 s in 6; (d) falls earlier in 10 and later in 3 [L].

**Backward margin** (the sim agent's test, sim/ADDED_MASS_SIM.md table 7): trunk centre of mass moved back in steps, stand 10 s and walk forward 12 s, runs with no seed and seeds 1 to 3, from the upstream start (soles 10.7 mm in the floor) and from a start raised 12 mm [L].

| Model | Trunk CoM moved mm | Robot CoM moved mm | Robot CoM ahead of the foot sites mm | Stand, upstream start: falls (s), runs none, 1, 2, 3 | Walk, upstream start | Stand, start raised 12 mm | Walk, start raised 12 mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (b) today | -10.0 | -3.6 | -1.8 | none, none, none, none | none, none, none, none | - | - |
| (b) today | -12.5 | -4.4 | -2.7 | none, none, none, none | none, none, none, none | none, none, none, none | none, none, none, none |
| (b) today | -15.0 | -5.3 | -3.6 | 1.06, none, none, none | 1.06, none, none, none | none, none, none, none | none, none, none, none |
| (b) today | -17.5 | -6.2 | -4.5 | 0.98, 1.24, none, none | 0.98, 1.24, none, none | none, none, none, none | none, none, none, none |
| (b) today | -20.0 | -7.1 | -5.4 | 0.92, 1.00, none, 1.56 | 0.92, 1.00, none, 1.56 | none, none, none, 1.20 | none, none, none, 1.20 |
| (b) today | -25.0 | -8.9 | -7.2 | - | - | 0.96, 1.02, none, 0.96 | 0.96, 1.02, none, 0.96 |
| (c) proposed | -10.0 | -3.5 | -1.4 | none, none, none, none | none, none, none, none | - | - |
| (c) proposed | -12.5 | -4.4 | -2.3 | none, none, none, none | none, none, none, none | none, none, none, none | none, none, none, none |
| (c) proposed | -15.0 | -5.3 | -3.2 | 1.22, none, none, none | 1.22, none, none, none | none, none, none, none | none, none, none, none |
| (c) proposed | -17.5 | -6.2 | -4.1 | 1.04, 1.24, none, none | 1.04, 1.24, none, none | none, none, none, none | none, none, none, none |
| (c) proposed | -20.0 | -7.1 | -5.0 | 0.94, 1.02, none, none | 0.94, 1.02, none, none | none, none, none, 1.22 | none, none, none, 1.22 |
| (c) proposed | -25.0 | -8.9 | -6.7 | - | - | 1.00, 1.04, none, 0.98 | 1.00, 1.04, none, 0.98 |
| (d) light head | -10.0 | -3.6 | -2.1 | none, none, none, none | none, none, none, none | - | - |
| (d) light head | -12.5 | -4.5 | -3.1 | 1.24, none, none, none | 1.24, none, none, none | none, none, none, none | none, none, none, none |
| (d) light head | -15.0 | -5.4 | -4.0 | 1.06, 1.24, none, none | 1.06, 1.24, none, none | none, none, none, none | none, none, none, none |
| (d) light head | -17.5 | -6.3 | -4.9 | 0.96, 1.02, none, none | 0.96, 1.02, none, none | none, none, none, 1.38 | none, none, none, 1.38 |
| (d) light head | -20.0 | -7.2 | -5.8 | 0.90, 0.92, none, 1.10 | 0.90, 0.92, none, 1.10 | 1.08, 1.28, none, 1.12 | 1.08, 1.28, none, 1.12 |
| (d) light head | -25.0 | -9.0 | -7.6 | - | - | 0.90, 0.92, none, 0.90 | 0.90, 0.92, none, 0.90 |

Measured from each robot's own estimate, the whole-robot centre of mass can move back 4.4 mm without a fall and falls from 5.3 mm (upstream start), or 6.2 mm and 7.1 mm (gentle start), in both (b) and (c); (d) falls one step earlier (3.6 and 4.5 mm; 5.4 and 6.3 mm) [L]. ADDED_MASS_SIM.md gives 4 to 6 mm for (b); the small differences come from the BEC Pro seat fix.

What this means for the build (sim pass only):
1. (c) keeps today's margins and walks a little better on flat ground: forward 0.70 against 0.67, turn 0.81 against 0.79, backlash 0.90 against 0.88, push tracking 0.62 against 0.60, torso 0.3 degrees less nose down.
2. The side step does not come back with print mass: 0.23 today, 0.24 to 0.25 for (c), (d) and even (a), against 0.46 trained. In the sim agent's sweep the side step follows the trunk centre of mass x (0.20 at 10 mm back, 0.29 at 10 mm forward; ADDED_MASS_SIM.md table 6) [L], so its lever is where mass sits, not how the prints are filled.
3. Rough terrain stays as bad as today: every seed of (b) and 16 of 18 of (c) fall, against 10 of 18 trained.

## Recommendation

1. Adopt config_light/ for the 29 parts it changes (20 STLs), after the coupon gate in step 2. New totals: 1280.3 g filament, 111.1 h for the robot set; robot about 2.64 kg [L].
2. Coupon gate in session S1: print C2a, C2b and C3 twice, in today's insert profile and in the light profile with rings (mass_study.py coupons: C2a 4.24 g 27 min, C2b 1.84 g 12 min, C3 2.33 g 12 min, so +8.4 g and +0.9 h sliced one by one) [L], and run the same pass tests on both (PRINT_PLAN.md step 1: insert flush, no crack or bulge over 0.2 mm, M3 threads by hand, no spin with the short arm of a 2.5 mm key, 5 kg for 10 s). If the light ones pass, print the 10 insert ring parts light; if not, those keep 4 walls (+61.7 g; robot about 2.70 kg) and everything else in (c) stands.
3. Keep heavy: the head, the neck chain, the G6 thin parts, trunk_top and trunk_bottom, the eyes and speaker_stand, and every spare (all at today's settings).
4. Back to the upstream defaults: the caches, body_front, head_bot_sheet, battery_pack_lid, foot_side, bulbs, flash parts, speaker_interface, the TPU soles, and (with the fit override kept) roll_to_pitch and roll_motor_top.
5. The left leg is printed first anyway (PRINT_PLAN.md step 2); with (c) it is also the first check of the light leg parts (foot_top, foot_side, foot_bottom_pla, leg_spacer, roll_to_pitch, roll_motor_top, cache). If one cracks in the bench tests, reprint that STL in today's profile.
6. If adopted, the plates in PRINT_PLAN.md must be packed and sliced again (the ring parts need their 3MF; mass_study.py writes one per part in the scratch folder). PLA for the whole job drops by about 119 g (127.6 g less in the robot set, +8.4 g of light coupons), to about 1383 g of the 2 kg bought (per-part sums, not plates) [L].
7. The weighing step the sim agent proposed (before the first walk, TEST_PLAN.md) then expects 2.64 +- 0.05 kg and the centre of mass about 1 mm ahead of the ankle servo axes [L].
8. Do not lighten the head (option (d)) unless a measured centre of mass shows room at the back.

## Risks and what closes them

- **Rings are untested in print.** The slicer puts as much plastic next to each hole as 4 walls do (Table 1), but a solid infill zone is not the same structure as 4 wall loops, and a Prusa forum user reports a weak boundary between a 100 % region and normal infill [I]. Closed by the coupon gate (step 2) for the inserts. The 5 body_back pilots (lid and electronics screws) have no coupon; their ring reads 1.11 against 1.00 today.
- **Body shells and caches at 2 walls** (body shells 3.0 mm median wall, caches 3.5 mm) lose the walls that carry most of the load: added walls give more breaking force per metre of filament than added infill [I] (HackSpace, Sources). They are how the upstream guide's defaults print them, and no upstream issue or PR reports one of them breaking (UPSTREAM_ISSUES.md: only a neck part, G5, and an unnamed head part during calibration, G6) [L]. But our robot is still 25.2 % heavier than the trained one, so falls hit harder than on upstream builds. Keep the first walks tethered (sim/ADDED_MASS_SIM.md finding 3 already says so) [L].
- **Leg parts at 2 walls** (foot_top, foot_side, foot_bottom_pla, leg_spacer, roll_to_pitch, roll_motor_top): the same servos limit the working loads on upstream builds and ours (3.23 Nm limit, ADDED_MASS_SIM.md table 4) [L]; the extra mass shows mainly in falls. Step 5 is the check. Keeping all six at today's settings would cost 35.7 g (Table 2, (b) less (c) on the robot, all quantities) [L].
- **Centre of mass 2.9 mm higher.** The sim shows no cost in any case run, but the sim agent's sweeps did not vary height, and the weighing step (recommendation 7) gives the mass and the fore-aft position only, not the height.
- **Rings exist only as PrusaSlicer modifiers.** Another slicer needs them redrawn by hand (positions and sizes in holes.json, written by mass_study.py holes; or in the PrusaSlicer GUI: right click the part, Add modifier, Cylinder, infill 100 %).

## Not verified

- Every gram and hour is a slicer estimate on a generic printer; nothing printed or weighed. Ring strength is not tested.
- The trained per-part masses exist only for the legs and the neck (MASS_BUDGET.md table 4); the trunk and head fits are not unique.
- The sim inherits MASS_BUDGET.md's limits (193 g UNVERIFIED, about 40 g uncertainty, uniform density per part) and ADDED_MASS_SIM.md's (BAM servo model, seeds vary the start only). The uniform density hides that rings put a little more of a part's mass round its holes.
- CNC Kitchen's own insert table could not be reread: cnckitchen.store and cnckitchenus.store are outside this session's allowed network domains. The 1.6 mm figure is the one PRINT_CHECK.md flag 1 recorded; a DigiKey tutorial gives the same 1.6 mm [I].

## Sources

- [L] print/SLICE_SUMMARY.md, print/PRINT_PLAN.md, print/parts.csv, print/config/*.ini, PRINT_CHECK.md (flags 1, 5), audit/sites.json, audit/sites_head.json, audit/insert_walls.json, audit/placements.json, sim/MASS_BUDGET.md (tables 2, 3, 4), sim/ADDED_MASS_SIM.md (tables 1, 2, 4, 6, 7), UPSTREAM_ISSUES.md (G5, G6), mini_bdx/robots/open_duck_mini_v2/robot.urdf.
- [L] /usr/share/PrusaSlicer/profiles/PrusaResearch.ini (config_version 1.11.12, bundled with PrusaSlicer 2.7.2 on the box) and prusa-slicer --help-fff.
- [U] docs/print_guide.md (infill per material).
- [I] Prusa blog, "Model with PrusaSlicer modifier meshes" tutorial: https://blog.prusa3d.com/model-with-prusaslicer-modifier-meshes-tutorial_30438/ (search result text; page not opened here).
- [I] Prusa Knowledge Base, Modifiers: https://help.prusa3d.com/article/modifiers_1767 (search result text).
- [I] Prusa forum, "Tricking slicer to make 100% fill in certain areas?": https://forum.prusa3d.com/forum/prusaslicer/tricking-slicer-to-make-100-fill-in-certain-areas (a cylinder modifier round a screw hole with more walls or 100 % infill; search result text).
- [I] Prusa forum, "Infill modifier creates breaking point": https://forum.prusa3d.com/forum/prusaslicer/infill-modifier-creates-breaking-point/ (a user reports a weak boundary between a 100 % infill region and normal infill; search result text).
- [I] DigiKey Maker.io, "Intro to FreeCAD part 4: how to use heat-set inserts": https://www.digikey.de/en/maker/tutorials/2025/intro-to-freecad-part-4-how-to-use-heat-set-inserts (a minimum of 1.6 mm round the hole for an M3 insert; search result text).
- [I] Raspberry Pi HackSpace, "Experiments with strong 3D prints": https://hackspace.raspberrypi.com/articles/experiments-with-strong-3d-prints (extra perimeters gave more added breaking force per metre of filament than extra infill; search result text).

## Reproduce

```bash
cd altaay_lab/print
OUT=/tmp/odm_mass_study                     # outside the repo
python3 make_coupons.py $OUT/coupons
nice -n 10 python3 mass_study.py holes  --out $OUT
for v in a b c d; do nice -n 10 python3 mass_study.py slice --out $OUT --variant $v; done
nice -n 10 python3 mass_study.py rings   --out $OUT
nice -n 10 python3 mass_study.py coupons --out $OUT --coupons $OUT/coupons
export ODM_PLAYGROUND=<Open_Duck_Playground at b9be205>
nice -n 10 python3 mass_study.py budget --out $OUT
C=walk_forward_0.15,turn_1.0,walk_side_0.2,walk_backlash,walk_pushes
nice -n 10 python3 mass_study.py walk --out $OUT --models stock,ours_b,light_c,light_d,upstream_a --cases $C --seeds 6
nice -n 10 python3 mass_study.py walk --out $OUT --models stock,ours_b,light_c,light_d --cases walk_rough_backlash_raised_start --seeds 18
nice -n 10 python3 mass_study.py walk --out $OUT --mode comback --models ours_b,light_c,light_d --dx=-10,-12.5,-15,-17.5,-20
nice -n 10 python3 mass_study.py walk --out $OUT --mode comback --models ours_b,light_c,light_d --dx=-12.5,-15,-17.5,-20,-25 --start_dz 0.012
nice -n 10 python3 mass_study.py tables --out $OUT
```
About 15 minutes of slicing and 20 of sim on the shared box. Needs PrusaSlicer 2.7.2 (CLI), trimesh, numpy, shapely, manifold3d, yourdfpy, mujoco and the Playground clone, like slice.py and sim/mass_budget.py.
