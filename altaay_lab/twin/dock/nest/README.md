# twin/dock/nest: the nest charging dock (DECISIONS.md D61)

Added 2026-11-11 ET. Updated 2026-11-11 7:38 PM ET: the whole working folder of the nest dock is now archived here
(scripts, raw results, clips, the CAD and the straight-crossing re-run), because the project is paused.

**Start with HANDOVER.md** (in this folder): what is decided, what is done, what failed, and the ranked open problems.

**This is an archive of work in progress. Nothing here is installed.** The CAD in cad/ is NOT in print/, NOT in the
URDF, NOT in the netlist, NOT in the BOM and NOT in the 3D viewer. Those still show the old wall and paddle dock.
Nothing was built, nothing was bought, nothing ran on hardware. The decision record, with its open BLOCKERs, is
DECISIONS.md D61. It replaces D58 (the feet-contact dock).

**The scripts were moved here from a working folder outside the repo and were NOT re-run after the move.** Their
hard-coded local paths were replaced by paths relative to each script (or the environment variables below). Every
script passes `python -m py_compile` (56 of 56, syntax only), and three shared modules were imported once to confirm
the new paths resolve (ducklib.py, sim/nestlib.py, cad/nestcad_lib.py). One exception, 2026-11-11 ET: after a review
finding, sim/analyze.py and sim/v2/compare.py were fixed and run once on the archived run files to make their
summaries again (sim/nest_results.json, sim/v2/compare.json, compare_table.md, compare.log). No MuJoCo run was
repeated and no other result file was made again.

## The concept in short

- A felt mat about 2 mm thick against the wall, with a 10 cm golden cloth disc (the sun, plus), a 32 mm felt gap and a
  pale gold cloth ring (minus). A soft rim at the wall holds the plug and the electronics. Sun centre 190 mm from the
  wall (concept values, calc only; NATURAL_DOCK_IDEAS.md section 6 A).
- On the duck: four spring pins under the body, 2 in the seat block (plus) and 2 in the belly bumper (minus), the pairs
  130 mm apart (sim pass only). Nothing in the feet.
- The duck walks on, turns 180 deg on the spot, sits facing the room (the D59 alert sit, torque off), and later stands
  and walks straight out.
- No tags or markers. Finding the nest is by camera only: untested, BLOCKER.

## Layout

| Folder | What | State |
|---|---|---|
| (this folder) | The concept study, its sketches, its scripts and data | D61 evidence |
| sim/ | The first sequence sim: 540 runs with the steering walk-on | D61 evidence |
| sim/v2/ | The re-run with "line up, then cross the edge straight". Finished after D61 was written | new; it contradicts D61's first fix |
| cad/ | The nest CAD: duck pins, mat, rim, checks, renders, STL, STEP, GLB | drawn, checks pass, NOT installed, look NOT yet approved by the owner |
| stripes/ | The striped mat study (why the feet and stripe route was dropped) | D61 evidence |
| superseded_feet_dock_d58/ | The feet-contact dock study behind D58, and the first concept sketches | SUPERSEDED by D61, record only |

## Files: this folder (the concept study)

| File | What | Label |
|---|---|---|
| HANDOVER.md | Status for the next agent | as marked in it |
| NATURAL_DOCK_IDEAS.md | The concept study: 19 ideas, scores, the pick (A, nest with a sun), the runner-up (B, pond rug), the wireless look (C) | sim pass only, calc only |
| T1_sit_contacts.png | What touches the floor in the sit, and with what force | sim pass only |
| A1_nest_sun_side_top.png, A2_nest_sun_approach.png, A3_nest_sun_technical.png | The pick: feel sketches and the technical view | sketches; numbers as marked on them |
| B1_pond_rug_side_top.png, B2_pond_rug_approach.png, B3_pond_rug_technical.png | The runner-up, kept on record | same |
| C1_plain_nest_side_top.png, C2_plain_nest_approach.png, C3_plain_nest_technical.png | The wireless variant, not taken | same; coil numbers calc only |
| sit_contacts.py, sit_contacts.json | What touches the floor in the D59 sit, where and how hard. Needs a scratch folder as its first argument. Known issue below | sim pass only |
| turn_probe.py, turn_probe.json | How far the duck drifts while it turns on the spot. Needs a scratch folder as its first argument | sim pass only |
| coverage.py, coverage.json | How forgiving each contact layout is, coil coupling against offset, the wireless power budget | calc only |
| ducklib.py, duck_outline.json | Draws the real duck outline for the sketches | sim pass only pose |
| figs.py | Makes the A, B, C and T1 sketches | sketches |

## Files: sim/ (the first 540 runs)

| File | What | Label |
|---|---|---|
| NEST_SIM.md | The report: walk on, turn, sit, torque off, stand, walk off | sim pass only |
| F1_pin_landing.png, F2_run_traces.png, F3_success.png | Where the pins land, run traces, success by pose noise | sim pass only |
| nestlib.py | The shared harness: the world (floor, wall, rim, mat), the 50 Hz walk loop, pins, sit and stand moves, zone scoring | sim pass only |
| nest_run.py, nest_runs_main.json | The Monte Carlo and every one of the 540 runs | sim pass only |
| analyze.py, nest_results.json | The tables | sim pass only |
| calib.py, calib.json, calib_turn.json | Pin positions on the trunk; the turn, stop and sit shifts | sim pass only |
| burst_probe.py, burst_probe.json | How small a move the stock walk can make | sim pass only |
| pins_effect.py, pins_effect.json | The sit with and without pins, on both mat contact models | sim pass only |
| edge_probe.py, edge_probe_2p5.json, edge_probe_5.json, edge_probe_10.json, edge_probe_20.json | Straight walks over the mat edge, four edge shapes | sim pass only |
| edge_control.py, edge_control.json | The 29 fallen runs again without the mat | sim pass only |
| figs.py | Makes F1 to F3 | sim pass only |
| render.py, render.json, run_good.mp4, run_failed.mp4 | Clips of one good run and one edge trip | sim pass only |

## Files: sim/v2/ (the straight-crossing re-run)

| File | What | Label |
|---|---|---|
| NEST_SIM_V2.md | The report. Read its plain summary first | sim pass only |
| V2_compare.png | Old against new, one figure | sim pass only |
| nest_run_v2.py, nest_runs_v2.json, nest_run_v2.log | The new walk-in and its 540 runs; the rest of the sequence is imported from sim/ | sim pass only |
| v2lib.py | Sole outline helpers ("is a foot on the edge") | sim pass only |
| compare.py, compare.json, compare_table.md, compare.log | Old against new, and every run that did not charge at the first sit | sim pass only |
| cross_probe.py, cross_probe.json, cross_probe.log, cross_probe2.log, cross_probe3.log, cross_probe4.log | Straight edge crossings: forward commands and retries | sim pass only |
| sweep.py, sweep_print.py, sweep_stage.json, sweep_stage2.json, sweep_cross6.json, sweep_cross7.json, sweep_final.json and their logs | The small sweeps of the walk-in settings | sim pass only |
| render_v2.py, render_v2.json, run_v2_pass.mp4 | Clip of one 7.2 V run that fell before and docks now | sim pass only |

## Files: cad/ (drawn, not installed)

| File | What | Label |
|---|---|---|
| NEST_CAD.md | The report. Section 6 is its BLOCKER list, section 7 is the file by file plan to land it in the repo (not done) | CAD check only, calc only, sim pass only |
| nestcad_lib.py | Shared numbers (pin, proud heights, mat and rim sizes), frames, helpers. `NEST_REPO` overrides the repo root | CAD check only |
| duck_pins.py, duck_pins.json | The duck parts: changed seat block, bumper and body_middle_bottom, two pin carriers, the gauge | CAD check only, calc only |
| nest_parts.py, nest_parts.json | The mat and rim parts | CAD check only, calc only |
| nest_assembly.py, nest_assembly.json, nest_assembly.glb, nest_assembly_new_parts.stl | The duck in its sit on the mat against the wall | CAD check only |
| nest_checks.py, nest_checks.json | Checks A to H. All passed when last run in the working folder | CAD check only, calc only |
| walk_clearance.py, walk_clearance.json | Pin tip heights while standing, walking, turning | sim pass only |
| pins_sit_check.py, pins_sit_check.json | The sit with the chosen pins, 22 sits. Imports ../sim/nestlib.py | sim pass only |
| nest_render.py, renders/ (8 PNG) | The renders the owner was shown | CAD check only |
| step_export.py | Mesh to faceted STEP. Needs OCP (pip package cadquery-ocp) and `NEST_OCP` | CAD check only |
| stl/ (19 STL) | One STL per part, the master files | CAD check only |
| step/ (14 STEP) | The same parts as faceted STEP, less the five named below | CAD check only |

STEP files not in the repo (dropped to keep the archive under about 40 MB; all four can be made again from stl/ with
step_export.py): sit_seat.step, sit_bumper.step, body_middle_bottom_feedthroughs.step, nest_box_tray.step. A STEP of
the whole body_middle_bottom was never made (NEST_CAD.md BLOCKER 12).

## Files: stripes/

| File | What | Label |
|---|---|---|
| STRIPE_MAT_STUDY.md | The striped mat and two-zone mat study, with the finding that the sit soles are not flat | sim pass only, calc only, CAD check only |
| F1_pattern_poses.png, F2_coverage.png, F3_circuit_2net.png, F4_mat_wall_top.png | Its figures. F3 is the 2-net circuit the nest inherits | calc only |
| sit_soles.py, sit_soles.json | Where the soles are and how flat they lie in the sit. Needs a scratch folder as its first argument | sim pass only |
| stripe_cov.py, stripe_cov.json, stripe_search.json, stripe_search_rows.json, stripe_map_S2.json, twozone.json, designs.json, final.log | Does a duck sitting anywhere on a striped mat always touch plus and minus | calc only |
| figs.py | Makes F1 to F4 | calc only |

## Files: superseded_feet_dock_d58/ (record only)

| File | What | Label |
|---|---|---|
| concepts/CONCEPTS.md, C1 to C5 PNG, draw_concepts.py | The first dock sketches of 2026-11-06 | the study's own labels |
| feet/FEET_DOCK.md, F1 to F6 PNG | The feet-contact dock study behind D58 | sim pass only, calc, est |
| feet/stance.py, sit.py, sit2.py, sit3.py, therm.py, geo.py, draw.py and stance.json, sit.json, therm.json | Stance scan, lowest sit, current and heat, the figures | sim pass only, calc |
| feet/deep/DEEP_ANALYSIS.md, D1 to D4 PNG | The failure by failure analysis | sim pass only, calc, est |
| feet/deep/harness.py, dock.py, rest.py, nest.py, rise.py, rollback.py, push.py, lowkp.py, footmass.py, mattrip.py, sitgeo.py, stats.py, render.py, figs.py | Its scripts | sim pass only |
| feet/deep/res_*.json (10 files), main.log, grid.log (empty) | Its raw results | sim pass only |

## Headline numbers

- First sim, steering walk-on (sim pass only; sim/NEST_SIM.md section 2.1 and 2.2): the first sit ends charging in
  93.1 % of 540 runs (503); 94.1 % (508) within 3 sits. 29 falls, all at 7.2 V, all while steering across the 2 mm
  mat edge.
- Re-run, line up and cross straight (sim pass only; sim/v2/NEST_SIM_V2.md section 3): the first sit ends charging in
  84.3 % of 540 runs (455); 91.3 % (493) within 3 sits. 13 falls (3 at 6.0 V, 10 at 7.2 V), all while walking
  straight over the edge. **The fix did not work overall.** HANDOVER.md has the detail.
- Wall and rim, over all 540 runs of each controller (sim pass only; sim/v2/NEST_SIM_V2.md section 3, corrected
  2026-11-11 ET): steering walk-on, worst 23.5 mm to the wall and 9.5 mm to the rim, 0 runs inside. Straight
  crossing, 9 runs with a part inside the wall plane or the rim (5 that reached a sit, 3 fallen ducks, 1 that never
  sat). The first versions of sim/analyze.py and sim/v2/compare.py counted only the runs that reached a sit; both are
  fixed and their summaries were made again from the archived run files (no MuJoCo run repeated).
- The seat pins may land within 45 mm of the sun centre at any heading up to 134 deg either side of facing the room
  (calc only; cad/NEST_CAD.md section 2.2).
- CAD: all checks A to H pass; 14.4 g added to the duck (calc only; cad/NEST_CAD.md section 4).
- The pose in the sims is a stand-in (true pose plus noise), not a camera.

## How to re-run the 540-run matrix

Not re-run after the move: treat the steps as the recipe that worked in the working folder (sim/NEST_SIM.md section 6,
sim/v2/NEST_SIM_V2.md section 7). Needs Python with mujoco, numpy and scipy, and whatever altaay_lab/sim/added_mass_sim.py needs
to run the repo's walk policy file (BEST_WALK_ONNX_2.onnx). Use a scratch folder outside the repo. From the repo root:

```
export PYTHONDONTWRITEBYTECODE=1
export NEST_SCRATCH=<scratch folder outside the repo>
python3 altaay_lab/twin/sit/sit_model.py --out $NEST_SCRATCH/model
cd altaay_lab/twin/dock/nest/sim
python3 calib.py pins && python3 calib.py turn && python3 burst_probe.py
python3 nest_run.py 30 main && python3 analyze.py main && python3 figs.py main     # the first matrix, 540 runs
cd v2
python3 nest_run_v2.py 30 v2 && python3 compare.py v2                              # the straight-crossing matrix, 540 runs
```

- `30` is the number of seeds per cell: 3 pose noise levels x 2 voltages x 3 mat frictions x 30 seeds = 540 runs
  (calc only on the matrix definition in sim/NEST_SIM.md).
- Each matrix took about 1 hour on 4 cores (sim/v2/NEST_SIM_V2.md section 7; `JOBS` sets the worker count, default 4).
- **Both commands overwrite the result file with the same tag** (`nest_runs_main.json`, `nest_runs_v2.json`). Use
  another tag to keep the archived results, for example `python3 nest_run.py 30 rerun`.
- If `NEST_SCRATCH` is not set, the harness uses a folder named nestsim in the system temp folder.
- The other commands (edge probes, sweeps, renders, the CAD chain) are in the three reports' file sections.

Environment variables the scripts read: `NEST_SCRATCH` (sim scratch folder), `NEST_REPO` (repo root, cad only),
`NEST_OCP` (folder with OCP, STEP export only), `NEST_CELL` (mat edge cell size in m), `JOBS`, `SEEDS`, `VOLTS`,
`LEAD_DEG`, `MUJOCO_GL=egl` (renders), `FEET_SCRATCH` (the superseded feet scripts only).

## Known script issues

1. **Floor contact toggled at run time has no effect.** `altaay_lab/twin/sit/sit_sim.py` and `sit_contacts.py` (this
   folder) set `geom_contype` and `geom_conaffinity` on the model after it is loaded, to switch floor contact for some
   geoms. In MuJoCo 3.17 that run-time change does not take effect, so those geoms keep the contact setting of the
   model as built. Source: found during this work and passed on by the owner's brief for this archive; not re-tested
   in this job, and which reported numbers it touches is not worked out: BLOCKER. `stripes/sit_soles.py` follows the
   same sit harness and should be checked for the same pattern. The fix is to set the contact bits in the model XML
   (`sim/nestlib.py` sets them in its scene XML) and re-run.
2. **The old feet harness had the mat in the world body.** `superseded_feet_dock_d58/feet/deep/harness.py` (used by
   `dock.py`) puts the mat geom in the world body, so the foot stagger numbers of DEEP_ANALYSIS.md are off. Do not
   reuse them. The study is superseded anyway.
3. **The feet scripts cannot run from the repo.** They load a model folder (the lab's `ours_b` added-mass model with
   the Playground assets) that is not in the repo, from `FEET_SCRATCH`. BLOCKER for a re-run. Several of them read and
   write their JSON by bare file name, so they must be run from their own folder.
4. **The reports still speak in the working folder's terms.** Where a report or a docstring says `dock/natural/`, read
   this folder. Where an older copy note says the scripts are kept outside the repo, that is out of date.
5. **Forward commands above 0.15** (the v2 run uses 0.18 at 6.0 V) are outside what the earlier work used; the sim
   result for them may not carry to the robot (sim/v2/NEST_SIM_V2.md section 6, item 6).

## What is not here

- The earlier wall-dock research the reports cite by name (DOCK_RESEARCH) is not in the repo. DOCK_TWIN.md and
  DOCK_INTERFACE.md are one folder up.
- A third-party source clone and the old wall dock working files that sat beside this work are not archived (the old
  wall dock is already in twin/dock/).
- Four STEP files (named above).
- The reports use more labels than the repo's three: "est" (an estimate with no source in hand), "index" (a web fact
  read from search results only) and "calc". Treat "est" and "index" as BLOCKER until sourced.
- No prices: the repo rule is no prices beyond the BOM, so each one reads "price: BLOCKER, not recorded here".
- The old wall and paddle dock files one folder up (twin/dock/) stay until the nest CAD is landed (cad/NEST_CAD.md
  section 7).
