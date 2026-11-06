# V1 freeze pass (Duckie, Open Duck Mini v2)

Written 2026-11-06 ET (America/New_York), for the design freeze. Labels: CAD check only for geometry, calc only for
estimates, sim pass only for MuJoCo runs. Nothing was bought, printed or posted. Sources are cited per line; BLOCKER
means a number that no source read here gives. Decisions: DECISIONS.md D51 to D57.

## 1. Results in one screen

| item | result | label | evidence |
|---|---|---|---|
| Mic seats into print/head.stl | done: print/head.stl now carries the D47 seats (2 bosses, a port tube and a 1.2 mm port per side). The two meshes differ only inside the seat zones (+310.0 mm3, -24.5 mm3; 0.0023 mm3 outside, float32 noise) and by 0.0 mm3 within 3 mm of either ear servo, so the PR 25 ear mount is unchanged (ear_mount.py gives the same numbers on the new file). 3.1 MB | CAD check only | head_freeze.json |
| C1, 17 FAILs | cleared at the cause: the netlist named STS3215 on the knees (now STS3250-C002, line 1b, D32), BOM_FULL wrote every servo as an STS3215 on line 1 (it now takes the model from the netlist), the CTL part was the old panel switch (now the NKK button, D30, D38), the check's own map still named the 2815 and power_switch.stl, and the P13 XT30U service plug (X3a, D36) is written on its cable, not as a component, so the check now also counts inline parts on their BOM line. No check was loosened: every line keeps a part number test, the servo map tests the model the netlist names | calc only | verify/c1_bom_coverage.py, viewer/bom_full.py, wiring/netlist.yaml |
| C3, D13 service loop | cleared at the cause: twin/complete3d/phase2_data.py copied the P13 route for D13 and dropped its spans, so C3 saw no free span at the 4 joints. routes_freeze.py rebuilds D13 on P13 with P13's spans and loops re-indexed (1 lead-in point, 20.9 mm) and gives D13, D14, D15 and D10's SD wire their lengths, which the writers left out, so C3 now judges them too. D13 then reaches with 47.5 mm to spare (542.5 mm worst, cut 590). The dock splices JGD and JSN joined check_cables.py INLINE (a C3 WARN) | CAD check only | routes_freeze.json, cables3d.json |
| E4, body_middle bounds 2 mm | the print STLs are right: body_middle_top grew 2.0 mm at +x (the D38 tongue) and body_middle_bottom 2.0 mm at -x (the D38 lips). The check compared whole bounding boxes, so a printed feature read as a frame error. It now tests the frame (on each axis one face must agree within 0.05 mm: a shift or a turn moves both) and lists the faces that grew | CAD check only | viewer/make_viewer_data.py, verify/e4_viewer.py |
| E4, 16 washers drawn, 8 counted | 8 is right: 4 eye screws are fitted since D38 and D39, 2 washers each (D21 note); blueprint/make_scene_extras.py drew washers under the left-out screws too. It now skips them | calc only | viewer/scene_extras.json |
| Test order $228.49 or $231.50 | $228.49 is right: it is the sum of TO1 to TO17. STATE.md and START_HERE.md kept the total from before commit 068176b (D34), when TO9 went from the $5.95 150 mm cable to the $2.94 300 mm one (-$3.01). Fixed there, and C9 now also reads the "test order (..., 17 lines, $X)" form, which it missed | calc only | BOM.md, verify/c9_docs.py |
| Speaker stand pilots "20.7 deg off" (B8, finding 19) | the same artefact as the ear pilots: on the mesh the 2 fitted pilots are 0.01 deg off the screw axis, 2.04 mm, through 4.5 mm of stand wall; the M2.5x5 engages 3.4 mm. feat3d reads every bore along a mesh axis and the speaker axis is 20.7 deg off the head y axis | CAD check only | speaker_pilots.json, fasteners.json F352 to F355 |
| Touch (D51) | 2 x MPR121: TCHH 0x5A on the head roof, TCHB 0x5B on the left inner wall of body_middle_top; pads PH1 head top 30 x 30, PH2 back of the head 20 x 30, PB1 back 17 x 34 mm with guard rings; palm 3.6 to 11.9 pF, two fingertips 1.1 to 2.5 pF against 0.01 pF resolution; no cheek pad fits on both sides | CAD check only, calc only | touch_pads.json |
| Speaker duct (D52) | duct 33.0 mm bore, 1.9 mm wall, 12.0 mm, 1.0 mm foam gap; 36 outer grille holes closed flush (0.03 mm), 91 open (286 mm2); Helmholtz corner 4.1 kHz; 30.8 mm to the right mic board, 53 mm to the ear servo, 2.0 mm to the interface screw heads | CAD check only, calc only | speaker_duct.json |
| Ears on hardware PWM (D53) | config, netlist and WIRING.md notes; the Runtime change is Ahmed's call (D6) | n/a | software/PI_SETUP.md 4c |
| Cliff ToF (D54) | seated in body_front on 4 standoffs, 2 diagonal M2.5x6, beam 52 deg down; floor spot 93 to 178 mm ahead of the toe; flat slant 209 mm, trigger 250 mm; no foot in the field of view while walking, walking slant 190 to 216 mm | CAD check only, sim pass only | cliff_seat.json, cliff_walk.json |
| Being picked up (D55), one arbiter (D56), no colour eyes (D57) | design written | n/a | twin/companion/COMPANION.md sections 13 to 15 |

## 2. Checks, before and after (VERIFY_OUT outside the repo, this box, 2026-11-06 ET)

| check | before (altaay-lab 1473799) | after |
|---|---|---|
| E1 | PASS | PASS (75 components, 171 wires, 0 ERROR, 0 WARN, 10 of 10 faults caught) |
| E2 | PASS | PASS (build $1,191.50, with expression $1,320.64, with tools $1,592.30, test order $228.49) |
| E3 | PASS | PASS |
| E4 | FAIL (2: bounds, washers) | PASS (0 WARN) |
| C1 | FAIL (17) | PASS |
| C3 | FAIL (1: D13) | PASS (7 WARN, as before plus D10's SD wire at 40 mm slack now judged) |
| C4a, C4b | PASS, PASS | PASS, PASS (324 fitted screws with the 2 ToF screws) |
| C6 | PASS | PASS |
| C9 | PASS (it missed 2 stale test order totals) | PASS (catches them now; 10 WARN, as before) |
| C10 | PASS | PASS (171 of 171 wires on sheets 1 to 4 and 6, harness sheet 5) |
| viewer load test | n/a | STATE loaded, ERRORS none |

## 3. Cliff ToF seat (D54)

- Board: Adafruit 5396, 25.4 x 17.78 mm, holes at the 4 corners 2.54 mm in [R the board file]. PCB top-face centre at
  (35.0, 0, -1.0) mm (URDF world), sensor normal (0.616, 0, -0.788), 52 deg below horizontal.
- 4 standoffs 5.0 mm, 3.3 mm high (the STEMMA QT sockets are 3.0 mm over the PCB), on a 3.0 mm floor that grows from
  the inner face; 2 x M2.5x6 DIN 912 (17f) from the back of the board into 2.0 mm pilots, on the diagonal pair through
  the board centre (D42); the other 2 holes rest on solid standoffs (D39). 4.4 mm engaged (MOUNTING.md electronics
  rule, 3 mm or more; the 2 x d rule is not met, as for the BNO055 and the Pi).
- Window on the field of view (14 deg half angle from a 2.5 mm disk): on the front face z -31.1 to -6.8 mm, y +/-7.1;
  6.8 mm under the D50 pad, 39 mm under the 6 mm lead hole, 4.0 mm over the bottom edge; 1.7 mm of wall over the
  board's upper end; 4.75 mm or more of wall round the pocket.
- Height: the sensor is 165 mm and the window centre 150 mm above the floor in the standing pose (chest.py of the
  perception study: floor 166.8 mm under the trunk origin). The study asked for about 140 mm; the 17.8 mm board tilted
  38 deg to the 10 mm wall must sit higher so the cone clears the bottom rim. The spot moves 4 mm further ahead.
- Beam (calc only, trunk level): centre 130 mm ahead of the toe, spot 93 to 178 mm; slant 209 mm on a flat floor,
  197 to 226 mm at +/-5 deg pitch, 438 mm over a 180 mm step; the 250 mm trigger trips on a drop of 32 mm or more.
  Stop margin at 0.1 m/s: 0.93 s to the near edge of the spot, under the Runtime's 1 s walk stop, so the cliff stop
  is the quicker freeze of perception study 4.2.
- Walk (sim pass only, 7 stock cases): no leg vertex in the field of view; the slant stays 190 to 216 mm in the 5
  cases that walk to the end. In walk_pushes the trunk tips before the fall is flagged and the slant reaches 428 mm:
  there the fall rule of the arbiter (D56) acts. A kinematic grid wider than the walk finds the foot in the cone only
  with a leg swung 35 deg or more forward and the knee near straight (a kick).
- Address: 0x29 [R adafruit_vl53l4cd.py, address=41; ST DS13812: 0x52 8-bit]. Current 22 mA typ, 24 mA max, peak 40 mA
  [R DS13812 Rev 3 Table 12]: the perception study's 40 mA guess is cleared.
- Print: body_front now prints with its front face on the bed (parts.csv up -x); re-slice 59.91 g, 4.38 h, support
  0.62 g in the window.

## 4. Touch (D51)

- Pads (copper foil on the inner shell, no air gap, guard ring 3 mm wide 3 mm outside each; NXP AN3863 3.3, 3.6, 3.7
  as read in the expression study): every ray of a 1 mm grid over each footprint meets the shell from inside; wall
  3.0 mm under PH1 and PB1, 3.0 to 5.5 mm under PH2 (the back slope); 4.1 mm or more from every cable and 3 mm or more
  from every part.
- Capacitance through the wall (calc only, C = e0 er A / d, er 2.9 to 4.2): palm PH1 8.2 to 11.9 pF, PH2 5.6 to 8.0 pF,
  PB1 3.6 to 5.1 pF (the 2-wall body shell at about 66 %); two fingertips 1.1 to 2.5 pF. Bench coupon: TEST_PLAN 18.2.
- Boards on VHB 4950: TCHH on the head roof at (-35, 35, 223) mm, 12.5 deg tilt, 13.1 mm from parts, 8.4 mm from the
  pad rings; TCHB on the left inner wall of body_middle_top at (-88, 52, 74) mm, 9.5 mm from parts. A seat under the
  trunk_top plate beside the BNO055 was searched first: no 33 x 19 mm flat patch is free there.
- Cheeks: searched on both side walls forward of the mic seats (x 40 to 88, z 188 to 212 mm, 91 places): every place
  has an opening or a wall outside 1.6 to 4.5 mm under the footprint on at least one side. Not placed.
- Bus: one software I2C bus 1 (D28): BNO055 0x28, ToF 0x29, MPR121 0x5A and 0x5B, no clash as long as the BNO055 ADR
  stays low. Pull-ups: the Pi's 1.8 k and 10 k on each of 4 boards make about 1.05 k, 2.8 mA at VOL 0.4 V, inside the
  3 mA standard-mode sink (calc only; board pull-ups on the MPR121 and BNO055 boards: [I], the VL53L4CD 10 k [R guide]).

## 5. Wires (D51, D54; netlist, cables3d, sheet 6)

| cable | wires | route | cut | note |
|---|---|---|---|---|
| D16 | 4, twisted | 89.4 mm in the head | 140 | 3.4 mm from P12 (the 5 V feed to the Pi): a test fit item |
| D17, D18 | 2 each | 42 mm along the head roof | 90 | electrode lead and guard ground not twisted (AN3863) |
| D19 | 4, twisted | 57.2 mm | 100 | runs against P11 (the 16 AWG BEC output) and 4.4 mm from P13: power and I2C in one bundle there; RISK, keep them apart at the test fit (TEST_PLAN 1.4) |
| D20 | 2 | 37.6 mm | 80 | |
| D21 | 4, twisted | 148.8 mm | 200 | 9.7 mm from SP1 |
| D22 | 1 | 577.6 mm, 649.4 mm worst over the neck joints, in the D21, D19 and D2 bundles | 690 | D2's 3 service loops and ties |

## 6. Mass and power (calc only)

- Mass: about +18.6 g (ToF 1.8 g, MPR121 boards about 6 g: BLOCKER, foil 1.9 g, wire 6.8 g, tape 0.5 g, PLA +1.6 g net);
  sim/MASS_BUDGET.md.
- 3.3 V rail: about 45 mA typical, 62 mA with the ToF peak (POWER.md section 10); the Pi Zero 2 W pin limit: BLOCKER.

## 7. BLOCKERs

1. MPR121 board mass and its IRQ and power LED current (not published).
2. The Pi Zero 2 W 3.3 V pin current limit (not in the product brief).
3. The 6-pin order on the 5396 header and the MPR121 header [I]: read it on the boards.
4. Ahmed's own words for D51 to D55: CLEARED 2026-11-06 by the full dock job (DECISIONS.md now quotes his messages; D52 and D53 came from the expression study he asked for).
5. The duct gain and the touch thresholds: bench (TEST_PLAN 18).
6. The runtime ear PWM change (D6) and the arbiter and pick-up code: not written (D47: hardware first).

## 8. Files

Scripts and results here: flib.py, head_freeze.py, speaker_duct.py, speaker_pilots.py, touch_pads.py, cliff_seat.py,
cliff_walk.py, routes_freeze.py, render_freeze.py and their JSON. Pictures are made with
`python3 altaay_lab/twin/freeze/render_freeze.py --out <folder outside the repo>` (not in git).
