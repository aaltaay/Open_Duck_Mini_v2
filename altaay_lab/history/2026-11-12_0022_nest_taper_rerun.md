# 2026-11-12 12:22 AM ET: the nest ramp was re-run after a review finding

Labels: sim pass only (MuJoCo 3.17.0, the repo sit model, the stock walk policy). Nothing ran on hardware.
The approved sun distance stays 190 mm. DECISIONS.md was not edited.

- A review on the nest sim v3 pull request found that the 20 mm ramp stored its fraction as a height-field sample.
  Sample 0 sits 1 mm under the floor and sample 1 is 2 mm above it, so the outer third of that ramp was under the
  floor and the foot only climbed about the inner 13 mm. The fraction is now a physical height (share of the 2 mm)
  and then converted to a sample. sim/nestlib.py.
- The 540-run ramp matrix was re-run on the same seeds (sim pass only; sim/v3/nest_runs_taper.json). 0 falls.
  First sit 523 of 540 (270 of 270 at 6.0 V, 253 of 270 at 7.2 V). Within 3 sits 539 of 540. Worst head-to-wall
  26.2 mm, worst foot-to-rim 18.0 mm, 0 runs inside either. The two 1 mm steps remain one run better on the first
  sit (524 of 540). The earlier 519 and 24.3 mm figures are replaced by this re-run.
- The other v3 matrices were not re-run. They do not use the ramp.
