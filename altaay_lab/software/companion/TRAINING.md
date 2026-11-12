# Training

Written 2026-11-12 ET. A shipping policy was not produced. Nothing was spent. No GPU was started.

Labels: cited, calc only, sim pass only, BLOCKER.

## What was already true

TWIN_CHECKLIST.md, Training: NOT RUN. No GPU policy run. The earlier CPU smoke of preset run2_sts3250, in the shared lab gym (overlay gym/overlays/duck), was 480 env steps, 5 evals, 612 s, 8 envs (twin/knee/KNEE_TWIN.md, sim pass only). That smoke is not a policy. The stock policy still falls on the STS3250 knee model in sim (same file).

COMPLETE_DUCK_AUDIT.md, Training scope and cost, is the paid-run note. It waits for Ahmed's OK. This file does not repeat the dollar figures. The hour range there is cited from a public timing note, then calc only for the bill. Storage, tax, and a failed restart are outside that note.

## This session

The shared lab gym trainer was not launched. This machine ran the upstream playground the gym notes already pin: Open_Duck_Playground b9be205, task flat_terrain, Joystick, imitation reward left on (USE_IMITATION_REWARD is true in that pin), reference-motion polynomial present (DATASETS.md has the sha256).

The upstream default is 8,192 envs and 150,000,000 steps (cited, locomotion config used by runner.py at that pin, and runner.py's own default). The README at that pin also lists a 300,000,000 step command. Neither fits a free CPU box. The smoke uses the same step count as the earlier gym smoke: 8 envs, 480 env steps, unroll 5, 5 evals. Threads held to one. JAX CPU. MuJoCo 3.17.0.

The network is the upstream PPO network named for the Berkeley joystick config: hidden sizes (512, 256, 128). It was not redesigned.

Dock walk-on, turn, and sit are the existing states APPROACH, STEER_DOCK, and ACTIVATE_CHARGER (software/dock). They were not trained. A new reward for that behavior: details held for later.

Session log (sim pass only). The process finished. It is not a gait.

- Wall time: 148.5 s for 480 env steps, 8 envs, 5 evals. The trainer's own clock at the last eval was 80.0 s. The rest is startup, including the first eval at 27.6 s.
- Episode reward at steps 0, 120, 240, 360, 480: 11.75, 12.15, 11.65, 12.00, 11.20. All five finite. No nan in those rewards. They did not climb. 480 steps is a smoke.
- Shipping policy: no.
- Checkpoint: not stored. A weight file from 480 steps is not a gait, and a large file does not belong in the repo.

## What the paid GPU run would do

Not started. Needs Ahmed's OK. The scope is the four runs already named in COMPLETE_DUCK_AUDIT.md:

| Run | What | Gate already written |
|---|---|---|
| A | Walk at the build mass, small terrain, knee heat | The key the earlier note was waiting on. Not executed |
| B | STS3250 knees, preset run2_sts3250 | Bench BAM test (TEST_PLAN.md 15) and the opened sheet. The stock policy falls on this model in sim |
| C | Creep, turns that match both ways, a right side-step, a 2 mm edge | An OK. The nest sims are sim pass only |
| D | The 48 down-ramp front rests, if they do not fit in C | Same OK. Length of a get-up-only run is BLOCKER until a preset says so |

The command length those runs point at is the upstream 150,000,000 to 300,000,000 step range above (cited, the pin). The hours and the dollar calc stay in COMPLETE_DUCK_AUDIT.md. Calc only. Awaits Ahmed's OK.

## BLOCKER

- This smoke is not an eval in the shared lab gym (overlay gym/overlays/duck). The gym trainer was not launched.
- 480 steps do not make a gait. Do not put the result on the duck.
- Run B still waits on the bench BAM test.
- A trained dock policy was not started.
- The three middle evals of the earlier gym smoke printed nan (KNEE_TWIN.md section 8, item 11). Watch the same if that preset is run again.
