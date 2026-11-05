# Screw twin: fewer screws and a faster build (calc only, CAD check only)

Written 2026-11-05 by the V1 screws agent for the lead, phase 1 (analysis and designs). Folder twin/screws/ only; nothing in fasteners.json, print/, BOM.md, MOUNTING.md, viewer/, sim/ or the docs was changed. Nothing was printed, bought or sent. Ahmed's ask (2026-11-04 6:36 PM ET): cut the screws where it is safe, magnets only if safe, about 90 % fewer; and (6:40 PM ET) cable management and a fast human build.

## Answer in plain words

- **Counts (fasteners.json, 355 screw rows, 342 fitted):** (a) servo internal or servo kit screws we cannot change: 86 listed, 75 fitted (56 factory case screws, 14 horn centre screws, 3 of 14 idle boss screws, 2 SG90 horn screws). (b) original design screws joining printed parts or boards: 261 listed, 259 fitted (2 left out by D18). (c) screws we added: 8 (4 camera, 4 SG90 tab), plus the 16 eye washers (D21).
- **Safe cut: 342 to 313 screws (29 fewer, 8.5 % of all, 10.9 % of b and c), 58 to 44 inserts, 16 to 8 washers.** By area: body front 8 to 4, back 13 to 7, head 52 to 35, trunk inside 74 to 72, neck and legs unchanged.
- **The 90 % target cannot be met safely.** 90 % of 342 is 308 screws. Even if every cover and board screw went, that would be 65 screws (19 %). The rest is load path:
  - 75 are inside the servos or their kits;
  - 168 hold the horns and servo cases of the leg and neck chain, where 34 of the 39 screw groups are already under the lab margin today (STRUCTURE_TWIN.md table 5: 34 under 1.2 at the mid fall level, 20 at the soft level, 6 under 2 in push, 1 in walking). They need more screws, not fewer;
  - 34 more hold the frame, the leg segments, the soles and the head on the neck. Together: 75 + 168 + 34 + 65 = 342.
- **Assembly hours** (cited per operation times; the rest is listed as BLOCKER): fastening 0.81 h to 0.72 h; cables 5.79 h to 5.47 h; total 6.6 h to 6.2 h. Not in that total: heat-set inserts (58 to 44), part handling, routing, labels and tests. The 8 h dwell of the stick-on mounts before the ties can be loaded goes away. Soldering is the long pole: 153 solder ends at 120 s is 5.1 h. Screws are under 1 h.
- **Needs Ahmed's OK:** the back shell going to 3 screws (one fall case gets worse, section 2); KK 254 crimp parts (X1, X3); WAGO lever splices (X4); an XT30U pair in P13 (X3a). No magnet is proposed.

## Phase 2 (2026-11-04, D36 and D38, applied)

- D38: the back shell keeps 7 of 8 screws (F075 out) with its lips and ribs, so the cut is 342 to 317 fitted screws (25 fewer, 7.3 %), 58 to 48 inserts, 16 to 8 washers. Applied in fasteners.json through report_fasteners.py (status LEAVE OUT (D38 screw cut), ids in data/phase2_fasteners.json), BOM.md, MOUNTING.md, the viewer.
- The back lips are now clipped to body_middle_bottom's own height (the first cut stood 46 mm above it): side capacity 2925 N per side, up 2261 N, 812 mm2 added overhang.
- D36: Wera tools and the 1/16 in bit on tool lines T16 to T19; KK 254 (22b, 22c; housing price BLOCKER), WAGO 221 pocket pack (26b), XT30U in P13 (line 12 Need 2). X3b not taken.
- 10b: NKK MB2011LS1W01-BB (Newark 941 in stock, $10.37, search index); same MB2000 bushing and body, so the D30 plate is unchanged.
- Time (cited per operation): fastening 0.81 to 0.73 h; cables 5.79 to 5.51 h; total 6.6 to 6.2 h; insert time BLOCKER.

## Files

| File | What |
|---|---|
| geom_joints.py | World-frame joint geometry (lab Scene, read only): contact faces split into axial and lateral by side, part centre of mass. Writes data/geom_joints.json. |
| screws_twin.py | Classes a, b, c; per joint: role, loads, capacity, safe minimum, kept screws; fastening time by build step. Writes data/classification.csv (every screw and insert), joints.json and joints.csv, assembly_steps.csv, summary.json, phase2_fasteners.json. |
| mesh_designs.py | Printed shear features for the shells, with checks; coupons K1 to K3. Writes data/lips.json and the STLs. |
| cables_twin.py | Cable operations, times before and after, the 5 slowest steps, changes X1 to X7, coupon K4. Writes data/cable_ops.csv, cable_steps.csv, cable_changes.json. |
| stl/ | body_front_groove.stl, body_middle_top_lip.stl, body_middle_bottom_lip.stl (new parts, in their print/ STL frame); coupons K1a, K1b, K2a, K2b, K3_cable_clip, K4_tie_bridge. Largest file 2.3 MB. |

Run order: `geom_joints.py`, `mesh_designs.py`, `screws_twin.py`, `cables_twin.py`. Wrap the mesh runs with the lab ramcap.py (peak 0.25 to 0.33 GB measured).

## 1. Method and safety rules (calc only)

Lab margin (STRUCTURE_TWIN.md section 3): SF 2 in walking and push, 1.2 in falls ("a part may crack but should not separate"). Loads and capacities come from the structure twin:
- walking 1 to 3 g; the worst of its 10 falls is 45 g trunk and 71 g head at the soft level, 128 g and 196 g at the mid level;
- shell hit upper bound: 900 N soft, 2800 N mid;
- PLA X 47.1 MPa, Z 22 MPa, shear 12.7 to 27.2 MPa;
- insert pull-out 1354 N; self-tapping strip capacities from its table 3.2;
- masses from sim/MASS_BUDGET.md.

- **Servo chain** (horn screws, servo case screws): table 5 as it stands. A group under any margin keeps every screw. The 5 groups that pass (idle horns of left ankle, left hip roll, left hip pitch, left and right knee) keep them too: the mirror group on the other side fails, and both sides are built the same.
- **Other structural joints** keep all, because a margin is already short there or the joint is not modelled (BLOCKER for any cut). These are the leg segment stack (caches, leg_spacer), feet, soles, trunk_top and body_middle_bottom to trunk_bottom (no lateral key: 0 mm2), and head_roll_mount (side SF 0.76 at mid). Also kept: the IMU at 4 (the policy reads its gyro and accelerometer and the fall rule its NDOF orientation, WIRING.md), the charger at 1 (the plug forces), and the SG90 tabs (antenna torque not modelled).
- **Covers and boards**, check F1 (no separation): one screw takes the whole inertial pull of the part and what rides on it, at the mid fall level. The count then comes from geometry. A stiff board or bracket on 4 seats keeps its 2 diagonal screws: it rests on the other 2 seats and cannot rock. A thin plate, lid or shell keeps 3, the largest triangle round its centre of mass.
- **Shells**, check F2 (bearing): the whole shell hit goes through one shell joint in shear, an upper bound.

| Joint | Before | After | F1 SF at mid, one screw | Note |
|---|---|---|---|---|
| body_front (solid 10 mm plate) | 8 M3x8 + 8 inserts | 4 (2 corners top, 2 bottom) | 9.1 | tongue on body_middle_top carries the shear (section 2) |
| body_back with battery (214 g) | 8 M3x8 + 8 inserts | 3 | 2.4 | lips and ribs on body_middle_bottom; Ahmed's OK (section 2) |
| battery_pack_lid (136 g with cells) | 4 M2.5x10 | 3 | 1.8 | battery retention: 3 points |
| head_bot_sheet (61 g) | 8 M3x8 + 8 inserts | 3 | 3.7 | edges captured on 4 sides (1044 mm2 lateral contact) |
| speaker_stand, speaker_interface | 4 + 4 | 2 + 2 | 2.4, 2.8 | listen test for buzz |
| Pi Zero 2 W, servo adapter, camera | 4, 4, 4 | 2, 2, 2 | 11.4, 13.1, 18.7 | |
| eyes (bulb to eye, 2 sides) | 8 M2.5x8 + 16 washers | 4 + 8 washers | 8.3 | |

Screw ids that go: data/phase2_fasteners.json; holes and empty insert bores stay in the parts, so any screw can come back.

## 2. Printed part changes (CAD check only, calc only)

Today the shells meet the middle parts face to face, with 35 to 65 mm2 of lateral contact, so side and vertical fall shear goes through the screws in bearing (F2 SF 1.21 at mid with 8). Cut to 3 or 4 with nothing else, F2 at mid drops to 0.45 or 0.61. mesh_designs.py adds shear features that carry this by bearing.

| New part | Feature | Fit (min gap) | Thickness | Printability | Capacity N |
|---|---|---|---|---|---|
| body_middle_top_lip | 3.0 mm tongue, 2.0 mm high, U along the outer skin of its front face (that face is the top of its print, so it grows straight up) | 0.25 to the grooved body_front | 3.1 mm | no new overhang | side 1732, vertical 3564 each way (root at a layer plane, Z 22 MPa) |
| body_front_groove | 3.5 mm groove, 2.25 mm deep, in its back face (print bed face) | 0.25 | the 10 mm plate keeps 7.75 mm | groove roofs are 3.5 mm bridges, 467 mm2 (counted as overhang by the PRINT_CHECK.md rule) | |
| body_middle_bottom_lip | back: 2 side lips (vertical plates) and 6 bottom ribs 4 x 4 mm, each on a root that thickens its inner wall in 45 deg steps | 0.25 to body_back, 0.46 to the lid, 0.30 to body_middle_top, over 10 mm to everything else in the trunk | 3.2 mm | adds 1155 mm2 of overhang to a part that already prints on 6143 mm2 of supports (rib undersides cannot avoid it) | side 5227, upward 2261 |

Not possible: no lip on body_middle_top's back face (its print bed: a lip would hang under the bed), and none on body_back's or body_front's rim (also bed faces). On body_middle_bottom's front rim no 3 mm band fits with the screw and part keep-outs (mesh_designs.py: none fits), so the front side shear rests on the body_middle_top legs and 4 screws.

F2 at the mid level after the change (8 screws today: 1.21 in every direction):
- body_front with 4 screws: side 1.22, vertical 1.88;
- body_back with 3 screws: side 2.32, upward 1.26, downward 0.45;
- at the soft level every direction is 1.41 or more.

The one case under 1.2 is a downward push on the back shell, which only an upside-down landing gives. In it a screw hole may crack, but F1 keeps the shell on. Only the full 8 screws give 1.2 there. **Ahmed decides:** back shell at 3 screws (5 fewer, this case at 0.45) or at 8.

Snap: the cable clip K3 (two arms 0.9 x 12 mm, 0.4 mm barbs) strains 0.375 %. The allowed strain is 0.535 %: the linear limit 47.1 / 2641 MPa, halved by the lab margin, then 60 % of that for repeated use. Formula eps = 1.5 t y / L^2 ([I] https://www.fictiv.com/articles/how-to-design-snap-fit-components, search text, Bayer method). It prints flat, so the arms bend in the layer plane.

**Coupons, proposed for session S1** (print tolerance is the weak point):
- K1a and K1b: 30 mm of tongue and groove. Push fit by hand, no rock, 10 on and off cycles.
- K2a and K2b: back lip and 2 ribs. Same tests, plus the rib undersides printed without sag.
- K3: the cable clip. Snap over a 6 mm dowel 10 times; after 24 h on it at 50 C the opening must not have grown.
- K4: the tie bridge. A 2.5 mm tie passes, and holds a 20 N hand pull.

If a fit is tight, rerun mesh_designs.py with C 0.35.

## 3. Build steps and time (calc only)

Per operation times (search text, the full pages could not be fetched from this session: dfma.com and apriori.com need allowing in the network settings):
- screw 8 to 12 s, snap or press fit 2 to 4 s ([I] https://dfma.com/resources/assembly-cost-estimating.asp);
- solder one wire end 120 s, cable tie 5 s, heat shrink 8.6 s per inch ([I] aPriori cost model guide 2019 R2, process defaults);
- crimp 90 s: calc, 0.75 x the 120 s solder time ([I] Smiths Interconnect HG tech note: crimp and poke about 25 % faster than solder);
- adhesive mount dwell 8 h ([I] Panduit mount selection guide, acrylic tape).

Washers, mount placement, plugs and lever splices use the snap and press class: a lab mapping, as DFA does.

**BLOCKER, with the check that closes each:**
- heat-set insert time (time 10 inserts on the S1 coupons);
- part handling;
- cable routing (time the left leg at the TEST_PLAN 1.4 test fit);
- labels;
- tie-hole drilling;
- continuity tests;
- the extra time of in-robot work.

Slowest mechanical steps:
- before: neck 36 screws (6.0 min), head internals 30 screws and 16 washers (5.8), trunk 26 (4.3), each shin and thigh 16 (2.7), and the 58 inserts (BLOCKER);
- fixed: head internals to 3.4 min, head closing 2.7 to 1.8, shells 2.7 to 1.3, 14 fewer inserts;
- the neck and trunk are servo chain and frame: no safe cut.

## 4. Cable work for a fast build (item 7, calc only)

Counted from HARNESS_BUILD.md (124 wires, 47 cables) and cables3d.json:
- 153 solder ends, 27 of them at the Pi header and 52 at the 15 splices;
- 17 crimps into 7 housings, 84 plugs and 34 sleeves;
- 75 ties: 55 on stick-on mounts, 6 in stock holes, 3 in drilled pairs, 2 to a neighbour cable, 9 bundle ties.

5 slowest cable steps, mid times, and their fix:
1. Battery bay solder joints, 54 min: X5 (bench piece on a length board); X4 takes 7 ends out.
2. Pi header joints on the head floor, 54 min: X1.
3. Belly power star splices, 48 min: X5.
4. Pi, IMU and feet solder, 40 min: X1 covers the Pi end.
5. Head expression solder, 38 min: X1 and X5.

| Change | What | Time |
|---|---|---|
| X1 | Pi header pins get crimped KK 254 terminals in 1-row housings (11 cables); R4 and R5 go inline in D3 and D4. Peak 2.4 A (P12) and 1.9 A (P17) against the 3 A rating used here. | -8.8 min; Pi and head unplug |
| X2 | 55 stick-on mounts become printed tie bridges (K4) on the same spots; the 3D job places them. | -2.8 min, -8 h dwell |
| X3a | Inline XT30U plug in P13 at the neck base (20 AWG, peak 2.21 A), so the head comes off unplugged. | +6 min |
| X3b (optional) | Inline KK 254 plugs in D3 and D4 at each hip (12 conductors), so a leg comes off without pulling cables through the neck. | +36 min |
| X4 | Battery bay splices G and VSW as WAGO 221 lever splices (24 to 12 AWG, 20 A). | -13.8 min |
| X5, X6, X7 | Bench pieces on a length board; a label at both ends and one colour per bus; build order legs, trunk, neck, head, plugging while both ends are open. | no cited credit |

Cables 5.79 h to 5.47 h (6.07 h with X3b). What the cable checks need is kept: no route or cut length moves, the D25 loops stay 3 x OD, and the first tie after each connector stays. The joint motion job re-checks the X2 bridges and X3 housings over the joint limits. Phase 2 data: data/cable_changes.json.

## 5. Magnets

None proposed:
- the lid carries the battery (136 g pulls 170 N on it at the mid level);
- head_bot_sheet would need 118 N;
- the shells carry fall shear;
- the trunk covers sit near the BNO055, which runs in NDOF mode (WIRING.md), and the fall rule reads its fused orientation (twin/electrical/fix/bus_budget.py).

A magnet on a true no-load cover would first need a field check at the IMU. That is a BLOCKER: no magnet data has been read.

## 6. Anticipated problems and their checks

| Problem | Check |
|---|---|
| PLA creep of lips, tongue and clips when warm (PLA keeps 0.62 of its strength at 50 C, STRUCTURE_TWIN.md 5; creep rate BLOCKER) | the lips carry load only in a hit, and the clip arms rest unstrained on a 6 mm bundle; K3 24 h at 50 C; re-check the shell fit after the TEST_PLAN 8 thermal walk |
| Wear from service: the lid's 3 M2.5 screws re-thread the PLA pilots each time | thread the lid pilot 10 times on a coupon, then a pull test; if it strips, M2.5 inserts (new part, Ahmed's OK) |
| Rattles: boards on 2 screws, shells on 3 or 4, the speaker on 2 | tap test; IMU accelerometer spectrum on the bench walk against the full-screw build; buzz test at full volume. Fix: put a screw back (every hole kept) |
| Magnet near the IMU or compass | no magnets (section 5) |
| A part coming loose in a fall | F1 SF 1.8 to 18.7 with one screw at the mid level. Drop check of the closed trunk on each face from the standing height of the trunk centre (BLOCKER: height to read from the URDF in phase 2). Watch the back shell's downward case |
| Print tolerance of the new fits | coupons K1, K2 before the parts print |
| More support on body_middle_bottom (+1155 mm2) | re-slice in phase 2 (print job) |
| KK 254 housings or lever splices loosen with vibration | tug test after the TEST_PLAN 8 walk |
| Adapter board on 2 screws flexes while 7 servo plugs go in | support the board by hand while plugging; if it flexes, keep 3 |

## 7. Phase 2, file by file (for the lead)

- **fasteners/fasteners.json:** drop the 29 screws, 14 inserts and 8 washers in data/phase2_fasteners.json. Then rerun report_fasteners.py, sweep_fasteners.py and render_fasteners.py (FASTENERS.md, the PNGs).
- **BOM.md:**
  - 16 inserts 58 to 44;
  - 17a M3x8 28 to 14; 17f M2.5x6 17 to 11; 17g M2.5x8 8 to 4; 17i M2.5x10 4 to 3; 17k M2.5x5 4 to 2;
  - 17h M2x4 6 to 4; 17l washers 16 to 8;
  - new lines once Ahmed agrees: KK 254 terminals and housings, WAGO 221-415 and 221-413, an XT30U pair.
- **print/:** body_front, body_middle_top and body_middle_bottom from stl/ once K1 and K2 pass. Re-slice body_middle_bottom. make_coupons.py gets K1 to K4 in S1. The ring modifiers of the unused insert bores can go.
- **MOUNTING.md:** screw counts for the eyes, lid, Pi, adapter, camera and speaker.
- **sim/MASS_BUDGET.md:** minus 29 screws, 14 inserts and 8 washers; plus 5.6 cm3 of PLA in the lips and tongue (sim owner).
- **viewer/ and blueprint/make_scene_extras.py:** regenerate from fasteners.json (the washers).
- **wiring/netlist.yaml and HARNESS_BUILD.md:** X1, X3, X4, X6 (wiring owner).
- **cables3d/:** X2 bridges and X3 housings (3D job), then the joint motion check.
- **TEST_PLAN.md:** coupon tests K1 to K4; the drop check; the tap, buzz and IMU checks.
- **DECISIONS.md:** the back shell choice and the new parts.

## 8. Limits

Calc only and CAD check only: no print, no bench test.
- Shell loads are an upper bound, because the structure twin does not model the shells as hit parts.
- Bearing is taken as the tensile strength (structure twin ASSUMPTION).
- The linear snap limit is an ASSUMPTION.
- Self-tapping strip is taken at the low end.
- Times are cost-model defaults, not a time study of this robot.
- The KK 254 price, the XT30U rating, the WAGO outline, the insert time and the magnet data are BLOCKERS.
## Addendum, D39 (2026-11-04 10:12 PM ET, track 2e: twin/holes)

- Every hole without a screw is closed in the printed STLs (twin/holes/close_holes.py; list in twin/holes/data/close_report.json). "Any screw can come back" no longer holds: a screw comes back only with a reprint (the pre-D39 STLs are in git at 0b1cab5).
- Back shell: 4 seats under the lower ears on body_middle_bottom fill the lip gap to 0.25 mm (433, 419, 433, 419 N, root shear at 12.7 MPa). F2 down at mid: 1.06 at 7 screws before, 1.67 at 7, 1.52 at 6 (F076 out). Side 1.95, up 1.72 at 6. F1 2.4 (one screw). Largest rim gap between screws 90 mm (unchanged).
- Left eye: F178 and F183 out, F179 and F182 back (same F1 8.3, same 35.4 mm diagonal).
- SG90 tabs: the stall torque (0.177 N m, 6.4 N per screw with 2) passes on one screw (the pocket stops the case within 0.25 deg), but the antenna hit (G6) is not modelled: 2 per SG90 stay (BLOCKER for a cut).

## Addendum, D42 (2026-11-04 11:01 PM ET, track 2f: twin/holes)

- The screws left on a part form a uniform pattern (DECISIONS.md D42): body_front keeps its 4 corners (F067, F068, F071, F072), the battery lid all 4 (F017, F018, F027, F028), head_bot_sheet 4 mirrored corners (F083, F084, F089, F090). joints.json keeps the D38 kept lists; the D42 sets and checks are in twin/holes/data/sym_checks.json.
