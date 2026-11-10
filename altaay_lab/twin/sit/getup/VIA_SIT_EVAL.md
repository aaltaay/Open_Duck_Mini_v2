# VIA_SIT_EVAL: the get-up through the sit (D60) on the merged sit model (aad3a9a)

Date 2026-11-10 ET. Written by a Claude Code sub-agent for the duck lead. Labels: **sim pass only** (MuJoCo in the shared lab
gym (overlay gym/overlays/duck)), **calc only** (motor current and duty from the sim torque). Nothing here ran on hardware.

The programs of GETUP_VIA_SIT.md (searched on the sit branch at b56ea56) are now a get-up family of the shared lab gym
(overlay gym/overlays/duck), folder getup/via_sit there. That family builds this repo's sit model with
twin/sit/sit_model.py at run time (the gym copies nothing of this repo) and pins it by the hashes of the model files; the
stand-up waypoints are read from twin/sit/sitlib.py (PATH_A1B with LEAN). This file is the re-run of the full 296 cases on
the merged model: this repo at **aad3a9a** (PR 28 merged: the round-2 stops, the TPU stop compliance, 2.8078 kg), STS3250
knees (D32), every target clipped to software/servo_limits.json, the GETUP success rule judged after the program ends (below). One result file per case (a
restart loses nothing); the per-case summary is via_sit_runs.jsonl here. Programs: programs/chain_v3r.json (the whole
program), hand_I.json (the tuck), roll_back3.json (the roll's search best: its parameters and a one-line training summary).

## Answer

**248 of 296 (sim pass only), the same as the search's 248 of 296: back 156 of 156, side 68 of 68, front 24 of 72.** Case
by case nothing changed: the same eval on the search's b56ea56 model gives 248 too, with 0 of 296 cases different from the
merged model and 0 of 296 different from the search's own runs (the port reproduces the search). The 48 failures are every
front rest on a down ramp, all at the tuck, as before: the trunk stays 74.7 to 75.9 deg (ramp_10_down) or 84.2 to 86.0 deg
(ramp_20_down) from upright with the head on the ramp. That still needs training (GETUP_VIA_SIT.md section 4; D60).

| fall class (cases) | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 | all | search (b56ea56) |
|---|---|---|---|---|---|---|
| back (39 per cell) | 39 | 39 | 39 | 39 | **156 of 156** | 156 of 156 |
| side (17) | 17 | 17 | 17 | 17 | **68 of 68** | 68 of 68 |
| front (18) | 6 | 6 | 6 | 6 | **24 of 72** | 24 of 72 |
| **all** | 62 | 62 | 62 | 62 | **248 of 296** | 248 of 296 |

| class, terrain (cases per cell) | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 |
|---|---|---|---|---|
| back, flat (12) | 12 of 12 | 12 of 12 | 12 of 12 | 12 of 12 |
| back, obstacles (12) | 12 of 12 | 12 of 12 | 12 of 12 | 12 of 12 |
| back, ramps up (15) | 15 of 15 | 15 of 15 | 15 of 15 | 15 of 15 |
| side, flat (10) | 10 of 10 | 10 of 10 | 10 of 10 | 10 of 10 |
| side, obstacles (4) | 4 of 4 | 4 of 4 | 4 of 4 | 4 of 4 |
| side, ramps up (3) | 3 of 3 | 3 of 3 | 3 of 3 | 3 of 3 |
| front, flat (6) | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |
| front, ramps down (12) | 0 of 12 | 0 of 12 | 0 of 12 | 0 of 12 |

By terrain: flat 112 of 112, obstacles 64 of 64, ramps up 72 of 72, ramps down 0 of 48. The 2 s upright and still window
starts at the program end: 18.1 s after the program starts for the front cases, 24.8 s (median, at most 26.2 s) with a roll
and its retry stage; the duck is first upright and still for 2 s earlier, at 13.7 to 13.8 s (front) and 20.3 to 21.9 s (rolls),
in the stand before the home key. After the roll every side and back case lies on its front at 85.6 to 87.2 deg; the IMU
retry rolled again in 7 of the 224 side and back cases and held in the other 217.

**The success rule (2026-11-10, after review):** upright (tilt under 15 deg, height at least 0.85 of the stance), still and on the soles alone for 2 s, counted only after the program has ended (the walk's home key reached; 2.5 s of hold follow) and reset by any break of any condition, so a duck that leaves the pose in the hold is not up; no joint more than 1 deg past its range. The search's evaluator used the get-up library's earlier rule (the 2 s window may start before the program ends, and once found only a tilt over 30 deg clears it), which could count a duck that came up during the rise and then lost the pose in the move to the home key. Both rules are reported per case (success, success_legacy_rule): on both models every case gives the same result under both, 248 of 296, so the search's count did not rest on the flaw. The gym library's own rule is unchanged for its other results.

## Servo torque margins (sim pass only; current and duty calc only)

Over the 248 successes. Torque limit at the supply voltage: 3.14 N m at 7.2 V, 2.62 N m at 6.0 V (STS3215); the STS3250
knees 4.97 and 4.14 N m. Current and duty by the gym get-up library's servo law (applied volts from the torque, motor
current from the volts and speed; the STS3250 knees with their own model); the Feetech protections need 2 s over the
line (over-current 2.0 A, the STS3250 knees 3.8 A; overload 80 % duty).

| joint | peak torque / limit | longest at the limit (0.98 or more), s | peak current, A | longest over the over-current line, s | longest over 80 % duty, s | max 2 s mean current, A |
|---|---|---|---|---|---|---|
| hip pitch | 1.00 | 1.08 at 6.0 V (0.32 at 7.2 V) | 2.46 | 0.77 | 1.14 | 1.47 |
| knee | 0.89 | 0 | 1.49 | 0 | 0.02 | 0.77 |
| ankle | 1.00 | 0.12 | 2.21 | 0.005 | 0.22 | 0.61 |
| neck pitch | 1.00 | 0.36 | 2.44 | 0.16 | 0.45 | 0.91 |
| head pitch | 1.00 | 0.02 | 2.17 | 0.02 | 0.24 | 0.91 |
| head yaw | 1.00 | 0.56 | 3.00 | 0.06 | 0.58 | 0.95 |
| hip yaw | 0.64 | 0 | 1.59 | 0 | 0 | 0.53 |
| hip roll | 0.58 | 0 | 1.52 | 0 | 0 | 0.93 |
| head roll | 0.53 | 0 | 1.37 | 0 | 0 | 0.58 |

The same as on the search's model within 0.08 s (hip pitch there: 1.01 s at the limit, 0.70 s over 2.0 A, 1.06 s over 80 %
duty). So the margins did not change with the merge: the hip pitch servos still sit at their torque limit through the
sit-up and the neck, head and ankle touch theirs in short peaks; no servo stays over a protection line for 2 s in sim (the
nearest: hip pitch over 80 % duty for 1.14 s, about 0.9 s short of the trip). Heat and stall on the real servo stay the
bench test of TEST_PLAN.md 19.9.

## Stops and the head rule (sim pass only)

Over the 248 successes: no joint goes past its hard stop by more than 0.30 deg (right hip roll; neck 0.28, knees 0.13: the
compliant stops' give), well inside the GETUP rule's 1 deg. Every program target is clipped to the software limits before
it is sent; the clip holds back the stored side swing's head yaw (-152 to the -105 deg limit), the -19 deg neck hold of the
tuck and rise (to -17) and up to 0.2 deg of hip roll. Measured joints go up to 3.3 deg past the software limits where they
rest on their hard stops (legs and neck at the sit, 3 deg out by design) and the head yaw overshoots its swing by 5.1 deg,
inside the hard stops. The head rule of SIT.md section 3 (with the neck above about +15 deg keep head pitch below +30 deg):
the neck runs -20.3 to +25.2 deg, the head pitch -24.6 to +17.4 deg, and the head pitch is at most +16.9 deg while the neck is
above +15 deg; 0 of 296 cases break the rule. In one failed down-ramp case the head goes 1.6 deg past its -25 deg stop (it
fails anyway). Seat peak 52 N, bumper peak 68 N on the floor (the search: 52 and 70).

## BLOCKERs

- Nothing ran on hardware.
- The hip pitch hold at the torque limit through the sit-up: thermal and stall margins on a real STS3215 (TEST_PLAN.md 19.9).
- The down-ramp front rests (48 of 296): training (D60, track 10).
- The roll keyframes' cross-leg contact on the exact meshes: SIT.md section 3 swept them (26 states, none of the new parts
  touches); the gym keeps the cut thigh covers out of self-collision as the search did.
- The rest poses are the gym library's (falls of the stock walk); a real fall ends elsewhere.
