# 2026-11-11 7:38 PM ET: the nest dock work is archived in the repo with a handover; the project is paused

Labels: sim pass only (MuJoCo, the repo's sit model and the stock walk), calc only (arithmetic), CAD check only
(measured on the meshes). Nothing ran on hardware, nothing built, nothing bought.

- Ahmed is pausing the project and asked for every piece of untracked nest dock work to be pushed, so a fresh agent
  can pick it up. This entry is that archive. Nothing is installed by it: print/, the URDF, the netlist, the BOM and
  the viewer are unchanged.
- New in twin/dock/nest/: the scripts and raw results of the concept study, the first sequence sim and the stripe
  study (beside their reports), three clips, sim/v2/ (the straight-crossing re-run), cad/ (the nest CAD with its
  checks, renders, STL, STEP and GLB) and superseded_feet_dock_d58/ (the feet-contact dock study behind D58 and the
  first concept sketches, record only). HANDOVER.md is the status for the next agent; README.md is the index.
- Cleaning for the public repo: local folder paths removed from every text file, script paths made relative to each
  script or set by an environment variable, prices replaced by "price: BLOCKER, not recorded here". The scripts pass
  a syntax check (56 of 56) and were NOT re-run after the move. Four large STEP files were left out to keep the
  archive small; cad/step_export.py makes them again from the STLs (named in README.md).
- The re-run that the 5:03 PM entry called "in progress" is finished (sim pass only; sim/v2/NEST_SIM_V2.md section 3):
  "line up before the mat, then cross the edge straight" did NOT work overall. Charge at the first sit 84.3 %
  (455 of 540) against 93.1 % (503); within 3 sits 91.3 % (493) against 94.1 % (508); falls 13 against 29. At 6.0 V
  it is worse (215 against 263 of 270 at the first sit, 3 falls against 0). At 7.2 V the first sit is the same
  (240 of 270) and 3 sits is better (259 against 241). The 10 falls left at 7.2 V happen while walking straight.
- Wall and rim (sim pass only; corrected in this pull request after a review finding, before merge): over all 540
  runs the straight crossing had 9 runs with a part inside the wall plane or the rim (5 that reached a sit, 3 fallen
  ducks, 1 that never sat and did not fall), against 0 of 540 with the steering walk-on (worst 23.5 mm to the wall,
  9.5 mm to the rim). The first summaries counted only the runs that reached a sit. sim/analyze.py and
  sim/v2/compare.py are fixed; their summaries were made again from the archived run files, no MuJoCo run repeated.
  D61's "23.5 mm, 9.5 mm" covered only the 511 runs that reached a sit; the all-run worst values are the same.
- What that means: the mat edge trips are not only a steering matter. The report points to a walk retrain (toe lift
  over a small edge, a right side-step), which needs GPU spend and Ahmed's OK. Neither is given.
- D61 is partly contradicted by this (it names the straight crossing as the fix to try first, and quotes 80 of 80
  straight crossings at 7.2 V; the larger samples give 5 falls in 180 walks and 10 in 270 runs, sim pass only). D61
  and the 5:03 PM entry are kept as written. HANDOVER.md and STATE.md say so.
- CAD status (cad/NEST_CAD.md): drawn, checks A to H pass, not installed. Ahmed was shown the renders and has NOT yet
  said the look is approved. The mat edge is two 1 mm steps (CAD check only), not simulated yet. The spring pin part
  was chosen from search results only; its data sheet is unverified: BLOCKER.
- Known script issues recorded in README.md: twin/sit/sit_sim.py and sit_contacts.py toggle floor contact at run
  time, which has no effect in MuJoCo 3.17 (not re-tested in this job; the numbers it touches are not worked out:
  BLOCKER); the superseded feet harness had the mat in the world body, so its stagger numbers are off.
- STATE.md: the Nest dock section is rewritten (paused, the v2 result, the CAD archived and not installed, the ranked
  open problems).
