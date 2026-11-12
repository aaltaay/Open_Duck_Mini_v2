# HANDOVER: the nest charging dock, status for the next agent

Written 2026-11-11 7:38 PM ET (America/New_York). The owner (Ahmed) is pausing the project. This file is meant to be
enough on its own to pick the nest dock up again. The index of every file is README.md in this folder.

Labels on every number: **sim pass only** (a MuJoCo run), **calc only** (arithmetic), **CAD check only** (measured on
the meshes). Nothing ran on hardware. Nothing was built. Nothing was bought.

## 1. What is decided

- **DECISIONS.md D61** (Ahmed, 2026-11-11 ET): the nest charging dock replaces the feet-contact dock (D58).
- The concept: a felt mat about 2 mm thick against the wall, a 10 cm golden cloth disc in the middle (the sun, plus),
  a 32 mm felt gap, a pale gold cloth ring (minus), a soft rim at the wall for the plug and the electronics, sun centre
  190 mm from the wall (calc only; NATURAL_DOCK_IDEAS.md section 6 A).
- Duck side: four spring pins under the body, 2 in the seat block (plus), 2 in the belly bumper (minus), the pairs
  130 mm apart (sim pass only; sim/NEST_SIM.md). Nothing in the feet.
- Sequence: walk on, turn 180 deg on the spot, sit facing the room (the D59 alert sit, torque off), later stand and
  walk straight out. No tags or markers: camera only (untested, BLOCKER).
- Electrical direction: D50's four nets become two, awake while docked is kept, the charger (MCP73213) moves from the
  dock into the duck (D61). Not designed yet.
- Runner-up kept on record: the pond rug (NATURAL_DOCK_IDEAS.md section 6 B).

**Nothing beyond D61 is decided.** The CAD look is not approved. No walk retrain is approved. No purchase is approved.

## 2. What is done

| Work | Where | State |
|---|---|---|
| Concept study, 19 ideas, sketches | NATURAL_DOCK_IDEAS.md | done, in D61 |
| Striped mat study (why feet and stripes were dropped) | stripes/STRIPE_MAT_STUDY.md | done, in D61 |
| Sequence sim, 540 runs, steering walk-on | sim/NEST_SIM.md | done, in D61 |
| Sequence sim re-run, line up and cross straight, 540 runs | sim/v2/NEST_SIM_V2.md | done AFTER D61; result in section 3 below |
| CAD of the duck pins, the mat and the rim, with checks and renders | cad/NEST_CAD.md | drawn, checks pass, NOT installed, look NOT approved |
| All scripts, raw results and clips archived in the repo | this folder, README.md | moved, syntax-checked, not re-run after the move |

## 3. The v2 sim result, stated plainly

The fix D61 names first, "line up before the mat and cross the edge straight with no yaw command", **did NOT work
overall**. The old steering controller is still the better one. All numbers sim pass only, from
sim/v2/NEST_SIM_V2.md section 3 (same 540 seeds, old against new).

| sim pass only | Old (steering) | New (straight crossing) |
|---|---|---|
| Charge at the first sit, all 540 runs | 93.1 % (503) | 84.3 % (455) |
| Charge within 3 sits, all 540 runs | 94.1 % (508) | 91.3 % (493) |
| Falls, all runs | 29 | 13 |
| Falls at 6.0 V, of 270 | 0 | 3 |
| Falls at 7.2 V, of 270 | 29 | 10 |
| First sit at 6.0 V, of 270 | 97.4 % (263) | 79.6 % (215) |
| First sit at 7.2 V, of 270 | 88.9 % (240) | 88.9 % (240) |
| Within 3 sits at 6.0 V, of 270 | 98.9 % (267) | 86.7 % (234) |
| Within 3 sits at 7.2 V, of 270 | 89.3 % (241) | 95.9 % (259) |
| First-sit misses | 8 | 71 |
| Runs with a part inside the wall plane or the rim, all 540 runs | 0 | 9 |
| of those: reached a sit / fell / never sat, no fall | 0 / 0 / 0 | 5 / 3 / 1 |
| Closest to the wall, all 540 runs, worst (negative: beyond the wall plane) | 23.5 mm | -300.3 mm (a fallen duck); -105.9 mm on its feet |
| Closest to the rim, all 540 runs, worst | 9.5 mm | -55.2 mm (a fallen duck); -3.0 mm on its feet |

In words:
- **6.0 V got worse**: 215 against 263 of 270 at the first sit, and 3 falls where there were none (sim pass only).
- **7.2 V is a wash at the first sit** (240 of 270 both times) and **better within 3 sits** (259 against 241 of 270)
  (sim pass only).
- **Trips happen even when walking straight.** The 10 falls left at 7.2 V happen with zero turn and zero lateral
  command. Steering on the edge is not the only cause. Going straight removes about two thirds of the 7.2 V falls
  (10.7 % to 3.7 %), not all of them (sim pass only; section 3, "How to read the falls").
- **The price is accuracy.** With no steering allowed across the edge the duck arrives off to the side and cannot
  side-step right to repair it: sideways landing scatter 22.3 mm to 36.1 mm (1 sigma, sim pass only).
- The earlier "80 of 80 straight crossings" at 7.2 V was too small a sample to see a 3 % rate (sim pass only; the v2
  report's own reading).
- **Conclusion: this is not a controller matter. It points to a walk retrain**: lift the toes over a small edge
  (2 mm), and add a right side-step (sim/v2/NEST_SIM_V2.md sections 5 and plain summary item 7). A retrain needs GPU
  spend and the owner's OK. Neither is given.

**D61 is now partly contradicted and is kept as written** (decision records are not edited):
- D61 BLOCKER (a) says the straight crossing is "the fix to try first" with "no result yet". The result is above: it
  did not work overall.
- D61 quotes "straight crossings with no steering at 7.2 V: 80 of 80". The larger samples give 5 falls in 180 walks
  (probe) and 10 in 270 runs (matrix) (sim pass only; NEST_SIM_V2.md sections 2.4 and 3).
- D61's "head 23.5 mm from the wall, a foot 9.5 mm from the rim" and "No part touched the wall or the rim in 511
  runs" covered only the 511 runs that reached a sit. Counted over all 540 runs of that controller the worst values
  are the same, 23.5 mm and 9.5 mm, with 0 runs inside the wall plane or the rim (its 29 fallen runs lie 273.7 mm or
  more from the wall). With the straight crossing the all-run count is 9 of 540 (sim pass only; corrected
  2026-11-11 ET after a review finding; sim/v2/NEST_SIM_V2.md section 3 and sim/nest_results.json).
- D61 says "no CAD yet". The CAD now exists (section 4), not installed.
- The sim behind D61 used a rim 72 mm deep; the CAD rim is 50 mm deep and 30 mm high (CAD check only;
  cad/NEST_CAD.md sections 2.3 and 4.4). D61 says the nest is about 49 cm across; the CAD felt is 451 x 534 mm
  (CAD check only; cad/NEST_CAD.md section 2.2).
A new decision entry by the owner is the way to settle these. Do not edit D61.

## 4. CAD status

- **Drawn. All checks A to H pass** (cad/nest_checks.json; CAD check only, calc only, sim pass only as marked in
  cad/NEST_CAD.md section 4).
- **NOT installed.** Not in print/, not in the URDF, not in the netlist, not in the BOM, not in the 3D viewer. The
  repo's robot is unchanged by this archive.
- **The owner was shown the renders (cad/renders/) and has NOT yet said the look is approved.** Ask before anything
  lands.
- The mat is about 47 cm across the gold ring (ring outer radius 235 mm); the felt under it is 451 x 534 mm
  (CAD check only; cad/NEST_CAD.md section 2.2).
- The mat edge is two steps of 1 mm, 20 mm apart (CAD check only). **Not simulated yet**: every sim so far used one
  2 mm rise (cad/NEST_CAD.md BLOCKER 5).
- Duck side: the seat block, the bumper and body_middle_bottom are changed, two PLA pin carriers and a gauge are new,
  no new screw on the duck; 14.4 g added (calc only; the charger board is not counted). Bumper pins stand 7.5 mm
  proud, seat pins 3.0 mm (CAD check only). With these pins all four touched in 22 of 22 sits (sim pass only;
  cad/NEST_CAD.md check C2).
- **The spring pin part was chosen from search results only** (a QA Technology 100-40 series probe in a 100-SDN250S
  socket). The data sheet could not be opened. Socket diameter, lengths, tip style, current rating and whether that
  socket fits that probe are all unverified. **BLOCKER** (cad/NEST_CAD.md section 3 and BLOCKER 1). Price: BLOCKER,
  not recorded here.
- The gate board in the rim and the charger board in the duck are not designed; the CAD only keeps room
  (cad/NEST_CAD.md BLOCKERs 3 and 4).
- The STEP files are faceted, not analytic CAD. Four large ones were left out of the repo (README.md names them).

## 5. The repo landing plan (from cad/NEST_CAD.md section 7; nothing below is done)

A. **New folder for the nest CAD** (the report proposes altaay_lab/twin/nest/): the CAD scripts and records, a pytest
   file, a new verify entry (c13_nest.py) with a row in VERIFICATION.md. Items 1 to 3.
B. **Duck parts**: replace print/sit_seat.stl, print/sit_bumper.stl and print/body_middle_bottom.stl (best through the
   builders in twin/sit/sit_cad.py), add the two carriers and the gauge to print/, add two fixed links to robot.urdf
   and robot.xml, update print/parts.csv and the print docs, close the 6 mm chest lead hole in print/body_front.stl
   and re-run the hole audit. Items 4 to 10.
C. **Wiring and placed parts**: wiring/netlist.yaml (chest pad J9 and DK2 out, pin pairs, splices JNP and JNM and
   leads NP1 to NP3, NM1 to NM3 in; four nets become two), then the generated wiring docs, cables3d, audit placements,
   the BOM files, MOUNTING.md, a nest fasteners record. Items 11 to 16.
D. **The 3D viewer**: swap the wall dock for the nest. viewer/make_viewer_data.py, a new viewer/nest_scene.py,
   viewer/index.html (scenes Duck, Nest, Nested), the viewer test and README; then retire twin/dock/ and check C12 in
   favour of C13. Items 17 to 21. Retiring files needs the owner's ask (rule: delete nothing).
E. **Records**: SIT.md section 1, STATE.md, V1_PLAN.md, TEST_PLAN.md, GAPS.md; and outside this repo the dock course
   of the shared lab gym (overlay gym/overlays/duck) and the dock behaviour code. Items 22 to 24.

Order that makes sense: the owner's approval of the look first, then the pin data sheet, then B and C together (they
share the pin positions), then D, then E.

## 6. Open problems, ranked

1. **Owner approval of the CAD look.** He has seen the renders and has not answered. Nothing lands before he does.
2. **Mat edge trips.** 13 falls of 540 with the straight crossing, 29 with steering (sim pass only). Untested ideas,
   cheapest first:
   - a mixed controller: the old steering at 6.0 V and the straight crossing at 7.2 V. Expected from the two tables:
     about 503 of 540 at the first sit and about 522 of 540 within 3 sits (calc only, not run; NEST_SIM_V2.md
     section 5);
   - at 7.2 V aim 10 to 20 mm right at the staging point, so the leftover error falls on the side the duck can repair
     (30 mm was tried in a small sweep and dropped; NEST_SIM_V2.md section 2.3);
   - the CAD's edge of two 1 mm steps, or a tapered edge, in the sim (a change to the mat height field in
     sim/nestlib.py; not run);
   - a walk retrain for toe lift over a small edge and a right side-step. **Needs GPU spend and the owner's OK.**
   - a real felt edge on the bench (the sim mat is rigid).
3. **Camera-only nest finding, and sensing after the turn.** Both untested. Every sim uses a pose stand-in (true pose
   plus noise), and the first sit is blind (D61 BLOCKERs c and d).
4. **The pin data sheet and pin-on-cloth contact tests.** Read the real catalog and put the numbers in
   cad/nestcad_lib.py `PIN`; bench test contact resistance, wear and snagging of a round tip on conductive cloth
   (cad/NEST_CAD.md BLOCKERs 1 and 2). Buying samples needs the owner's OK.
5. **Electrical redo.** The charger board into the duck (part, seat, heat), the two-net "is it the duck" safety gate
   board in the rim (the box keeps 70 x 26 x 14 mm, CAD check only), and a heat re-check: about 1.9 to 3.2 W of new
   heat in the trunk while charging (calc only; D61) with the thermal twin not re-run.
6. **Head-to-wall margin.** Worst run 23.5 mm with the old controller over all 540 runs (sim pass only). The v2 run
   put the head beyond the wall plane in 8 of 540 runs: 4 that reached a sit (0 to 4 mm), 1 that never sat (105.9 mm,
   on its feet) and 3 fallen ducks (sim pass only). The wall check is geometry only: the sim does not push the head
   back. Moving the sun from 190 to 215 mm from the wall would give
   48.5 mm (calc only, needs a re-run; cad/NEST_CAD.md section 4.4). One number to change: `WALL_X` in
   cad/nestcad_lib.py. The 190 mm is in the owner-approved concept, so ask.
7. **Landing the CAD** into print/, the URDF, the netlist and the BOM, and swapping the old wall dock for the nest in
   the 3D viewer (section 5 above).
8. **Records that still mention the D58 foot pads**: altaay_lab/TEST_PLAN.md (the knee loop flex test names the
   feet-dock pad wires) and altaay_lab/twin/sit/SIT.md (says the duck charges on the feet-dock pads). Also the script
   issues in README.md ("Known script issues").

## 7. The owner's standing rules, in short

- Buy nothing without his OK.
- Send no emails, messages or public posts without his ask. That includes GitHub issues.
- Delete nothing. No force-push.
- A label on every number (sim pass only, calc only, CAD check only), a source, or the word BLOCKER.
- No em dashes.
- History: one new file per entry in altaay_lab/history/, with the real US Eastern time (`TZ=America/New_York date`).
  Never edit an old entry.
- Merge only after the Codex review finishes.
- Replies to him: short, plain, one question at a time.
- Public repo: no local absolute paths, no private repo names, no prices beyond the BOM, no secrets.

## 8. Where to start

1. Read this file, then DECISIONS.md D61, then sim/v2/NEST_SIM_V2.md (plain summary) and cad/NEST_CAD.md (plain
   summary, sections 6 and 7).
2. Ask the owner one question: is the look in cad/renders/ approved?
3. While waiting, the cheapest useful sim work is the mixed controller and the two 1 mm stepped edge (problem 2). Both
   need only the scripts in sim/ and sim/v2/ and about 1 hour on 4 cores per 540-run matrix (sim/v2/NEST_SIM_V2.md
   section 7). Re-run recipe: README.md.

## 9. Sim follow-up, 2026-11-11 ET (does not replace sections 1 to 6)

The mixed controller, the CAD edge, a taper, a rightward aim, and a 215 mm wall were run. Full write-up:
sim/v3/NEST_SIM_V3.md. All of this is sim pass only unless a line says calc only. Nothing was built or bought.
The approved sun distance is still 190 mm. The 215 mm run is a study only. D61 was not edited.

Short version, same 540 seeds:

| sim pass only | First sit | Within 3 sits | Falls | Worst head to wall, all runs |
|---|---|---|---|---|
| Old steering (section 3) | 503 of 540 | 508 of 540 | 29 | 23.5 mm |
| Straight crossing (section 3) | 455 of 540 | 493 of 540 | 13 | -300.3 mm |
| Mixed: steering at 6.0 V, straight at 7.2 V | 503 of 540 | 526 of 540 | 10 | 8.4 mm |
| Mixed, two 1 mm steps | 524 of 540 | 536 of 540 | 0 | 33.4 mm |
| Mixed, 20 mm ramp | 519 of 540 | 539 of 540 | 0 | 24.3 mm |
| Two steps, and aim 20 mm right at 7.2 V | 531 of 540 | 540 of 540 | 0 | 9.6 mm |
| That combo, sun 215 mm from the wall (study) | 531 of 540 | 538 of 540 | 0 | 47.4 mm |

The calc-only guess for the mix was about 503 and about 522. The re-run gave 503 and 526. The 522 added the 6.0 V
first-sit count (263) to the 7.2 V within-3 count (259). The within-3 column at 6.0 V is 267, and 267 + 259 = 526
(calc only on the two archived tables; the re-run matched those tables seed by seed).

What helped: the two 1 mm steps. Falls went from 10 to 0 and the first sit from 503 to 524. Aiming 20 mm right at
7.2 V then took that 7.2 V first sit from 256 to 263 of 270, and every 7.2 V run charged within 3 sits, at the cost
of the worst head gap (33.4 mm down to 9.6 mm). Putting the sun 215 mm from the wall, on that combo, put the worst
head gap at 47.4 mm and the worst foot-to-rim gap at 34.9 mm, with 0 runs inside either, and the first-sit count
stayed 531 of 540.

What did not help: the mix does not beat the old controller on the first sit (both 503). Aiming 10 mm right did not
change the charge count on a 45-run 7.2 V sweep. The ramp is a little worse than the two steps on the first sit
(519 against 524). Moving the wall did not buy more first sits, and 2 runs that had charged within 3 sits at 190 mm
did not at 215 mm.
