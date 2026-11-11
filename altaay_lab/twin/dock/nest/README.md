# twin/dock/nest: the nest charging dock (DECISIONS.md D61)

Added 2026-11-11 ET. Concept evidence only: sketches, sims and arithmetic. No CAD yet, nothing built, nothing bought,
nothing ran on hardware. The decision record, with every open BLOCKER, is DECISIONS.md D61. It replaces D58 (the
feet-contact dock).

## The concept in short

- A felt mat about 2 mm thick against the wall, with a 10 cm golden cloth disc (the sun, plus), a 32 mm felt gap and a
  pale gold cloth ring (minus). A soft rim at the wall holds the plug and the electronics. Sun centre 190 mm from the
  wall (concept values, calc only; NATURAL_DOCK_IDEAS.md section 6 A).
- On the duck: four spring pins under the body, 2 in the seat block (plus) and 2 in the belly bumper (minus), the pairs
  130 mm apart (sim pass only). Nothing in the feet.
- The duck walks on, turns 180 deg on the spot, sits facing the room (the D59 alert sit, torque off), and later stands
  and walks straight out.
- No tags or markers. Finding the nest is by camera only: untested, BLOCKER.

## Files

| File | What | Label |
|---|---|---|
| NATURAL_DOCK_IDEAS.md | The concept study: 19 ideas, scores, the pick (A, nest with a sun), the runner-up (B, pond rug), the wireless look (C) | sim pass only, calc only |
| T1_sit_contacts.png | What touches the floor in the sit, and with what force | sim pass only |
| A1_nest_sun_side_top.png, A2_nest_sun_approach.png, A3_nest_sun_technical.png | The pick: feel sketches and the technical view | sketches; numbers as marked on them |
| B1_pond_rug_side_top.png, B2_pond_rug_approach.png, B3_pond_rug_technical.png | The runner-up, kept on record | same |
| C1_plain_nest_side_top.png, C2_plain_nest_approach.png, C3_plain_nest_technical.png | The wireless variant, not taken | same; coil numbers calc only |
| sim/NEST_SIM.md | The full sequence in MuJoCo: walk on, turn, sit, torque off, stand, walk off. 540 runs | sim pass only |
| sim/F1_pin_landing.png, sim/F2_run_traces.png, sim/F3_success.png | Where the pins land, run traces, success by pose noise | sim pass only |
| stripes/STRIPE_MAT_STUDY.md | The striped mat and two-zone mat study, with the finding that the sit soles are not flat. Why the feet route was dropped | sim pass only, calc only, CAD check only |
| stripes/F1_pattern_poses.png, stripes/F2_coverage.png, stripes/F3_circuit_2net.png, stripes/F4_mat_wall_top.png | Its figures. F3 is the 2-net circuit the nest inherits | calc only |

## Headline numbers (all from the files above)

- First sit ends charging in 93.1 % of 540 runs (503); 94.1 % (508) within 3 sits. Of the 511 runs that reached the
  sit, 98.4 % (503) charge at the first sit (sim pass only; sim/NEST_SIM.md section 2.1).
- 29 falls, all at 7.2 V, all while steering across the 2 mm mat edge (10.7 % of the 270 runs at 7.2 V; 0 at 6.0 V).
  Straight crossings at 7.2 V: 80 of 80. No fall in the turn, the sit, the stand-up or the walk-off (sim pass only;
  section 2.2).
- The seat pins may land within 45 mm of the sun centre at any heading (calc only; NATURAL_DOCK_IDEAS.md section 6 A).
- Closest approach in 511 runs: head 23.5 mm from the wall, a foot 9.5 mm from the rim, no collision (sim pass only;
  sim/NEST_SIM.md section 2.3).
- The pose in the sim is a stand-in (true pose plus noise), not a camera.

## What is not here

- The scripts, JSON results and the two video clips the reports name are kept outside the repo. The runs cannot be
  repeated from the repo alone: BLOCKER for a re-run.
- The earlier studies the reports cite by name (DOCK_RESEARCH, FEET_DOCK, DEEP_ANALYSIS) are not in the repo.
  DOCK_TWIN.md and DOCK_INTERFACE.md are one folder up.
- The re-run of the walk-on with a straight crossing of the mat edge (the fix to try for the 29 falls) was in progress
  on 2026-11-11 and is not in these files.
- The reports use two more labels: "est" (an estimate with no source in hand) and "index" (a web fact read from search
  results only). Treat both as BLOCKER until sourced.
- The old wall and paddle dock files one folder up (twin/dock/) stay until the nest CAD job replaces them.
