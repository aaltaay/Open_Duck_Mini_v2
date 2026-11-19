# Autonomy supervisor

Written 2026-11-19 ET. One loop that lets the duck decide what to do. It does not pass gate 7. A sim is not days of home use. Nothing here ran on a duck.

The loop lives in software/autonomy/supervisor.py. It calls the personality engine, the assistant, the battery guard, and the knee heat guard. It does not edit the Runtime (D6) and it does not run on the 50 Hz walk thread. On the Pi it belongs in that same process, on the other thread, because the servo port is exclusive (SOFTWARE.md section 3).

## What it does

When the pack is above the home line the duck wanders, greets, and carries a reminder. Those choices are the personality engine. A hello still goes through the assistant.

When the pack is at or under 10.8 V and still above the 10.0 V walk stop, the duck starts a camera dock. The states are the ones in twin/dock/camera/camera_dock.py: search, approach, turn, fine, sit. No tags. The mat is nest v2. Nest v3, v4, and v5 are not used. D61 was not edited.

A dock episode is one row from the gold-dome batch: 38 of 40 charging (sim pass only, twin/dock/camera/SEAT_CONTACTS.md). Seed 32 never sees a mark. Seed 29 sits on one well. The papers' own retry cap is two (`retries < 2` in camera_dock.py). After two retries the duck sits and shows help_me: head up, ears opposed, eyes bright white. A pet or a pickup clears the wait.

A fall runs the flat-floor get-up, 112 of 112 (sim pass only, twin/sit/getup/VIA_SIT_EVAL.md). The program time used here is 21.9 s, the long end of the roll window in that note (sim pass only). Two misses sit and show the same help pose. A pet or a pickup clears the wait and arms a full get-up interval if the duck is still down. A hot knee, or a pack at or under the 10.0 V walk stop, holds that fall. The duck sits with the torque off and does not spend walking current until the knee is cool and the pack is above the stop. A daily fall rate on a home floor is BLOCKER. The cited flat walks and the 40 camera docks do not report a fall, so the soak does not invent one.

A hot knee (55 C stop, 45 C to walk again) sits with the torque off. A quiet sit can nap. A nap lasts 15 minutes (a set point), then the duck stands. Charge holds the body on the nest until the cell model is full. The head may still look at a person. The feet do not walk off the contacts.

Logs are JSON lines. snapshot() and restore() keep the episode, the pack, the mood, the knee confirm counts, and the measured dock draws, so a new process continues the same sequence.

## Power

| Number | Value | Label |
|---|---|---|
| Pack window | 9.0 V to 12.6 V | cited, netlist PACK_9V0_12V6 |
| Walk stop | 10.0 V | cited, D65, netlist walk_stop_v |
| Home | 10.8 V | set point, 0.8 V above the walk stop (personality) |
| Servo rail in this soak | 12.0 V | cited set point. Sag is not replayed. A long-run servo median is BLOCKER. |
| Charge | 1.006 A | calc only, BQ24133 ISET divider, netlist. Inside the cited 0.6 A to 2.5 A chip window and under the cited 13.5 A cell maximum. |
| Walk pack current | 5.144 A | sim pass only, problems/FIT3.md mean at 0.15 m/s, typical. That walk used a 16 V set point that is superseded. A mean on the held 12.0 V rail is BLOCKER. This is the only published mean. The held-rail 10 s peak is 9.261 A (sim pass only, problems/HOLD12_WALK.md). |

The soak stops the model at the 9.0 V netlist floor. It does not add a new cutoff.

## Three-day soak

Seed 1. Tick 10 s. The supervisor is restored from its snapshot at the end of day 1 and then continues. Sim pass only.

| Result | Value |
|---|---|
| Hours awake | 23.211 |
| Dock attempts | 24 |
| Dock successes | 20 |
| Falls | 0 |
| Stuck events | 0 |
| Minimum pack voltage | 10.665 V |

Awake means not napping and not charging. The 4 misses are draws of the published seeds 32 and 29 (two of each). They are not a new dock rate. No three misses landed in a row, so this seed never showed help_me. The unit tests do.

The picture is altaay_lab/twin/out/videos/autonomy_day.mp4. It is the first simulated day, 36 s, 1280 by 720, 422170 bytes. The caption says SIM and sim pass only. The duck and the stripes are a drawing of that trace, not a MuJoCo frame and not the CAD.

## Still open

- A live camera on the Pi. BLOCKER.
- Charge on a real board. BLOCKER.
- A mean pack current on the held 12.0 V rail. BLOCKER.
- How fast the knee cools. The soak reuses the heat-up time constant. BLOCKER.
- A fall rate for a real floor. BLOCKER.
- Gate 7. Not passed.
