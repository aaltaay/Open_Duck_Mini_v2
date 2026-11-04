# V1 plan

Written 2026-11-04 4:21 PM ET (America/New_York) by the lead. The lead keeps this file; the status column changes at each merge.

Ahmed, 2026-11-04 about 4:08 PM ET: "Now let's do this as a version 1, forget about the wheel. Forget about chasing a human and that's fine. Do make sure that our design works, is optimized, and there are no missing pieces: electronics, cables, spin, power, electricity, heat test, vibration. I guess all of the good stuff. I need a true digital twin so we're not surprised when we start printing. The designs also need to be optimized so every component is accounted for: how it's going to attach to each other, all of it, please."
Then: "But don't waste my tokens, please." "Each one needs to have some serious outcome or find serious gaps." "Or start one by one to make sure we're not just doing a wrong motion here." "And have a plan in case we don't finish today."
Then, about 5:05 PM ET, after track 1: "Also, why do we have the LED on the side? Put it in the eyeglass disc." "Well, dude, just continue all of them, dude. Don't leave leftover branches, and make sure: if you see bad signals or bad spikes, we got to fix that, not just detect them. Anticipate any possible problems, please, please, please." "continue through all the tests dont stop." He listed the scope again: electronics, cables, spin, power, electricity, heat test, vibration.

V1 scope: the stock walking duck on legs, indoors, our 2.65 kg build. No wheels, no human pace work. The dock stays a later lab step (DECISIONS.md D5). Nothing is printed or bought. "Spin" is read as joint rotation: what each joint hits as it turns, and what the cables do.

## How it runs
- One track at a time, one agent per track. Track 1 was the pilot. Since "continue through all the tests dont stop" (about 5:05 PM ET) the tracks run back to back: each starts as soon as the one before is merged.
- A track must end with serious outcomes: FAIL or RISK items with numbers and a fix, or "checked, nothing serious" with the evidence. Full detail only for FAIL and RISK.
- Fix, not just detect: every FAIL or RISK gets a fix that the twin runs again and shows working, with the numbers before and after. A bench check alone is not a fix. Where a number is not published, the fix must hold at the worst cited value, and the bench check stays. A fix that needs a part names the part and its price and waits for Ahmed's OK; nothing is bought.
- Anticipate: each track ends with the problems in its area that no track covers yet, each with the check that settles it. The lead keeps them in the list at the end of this file.
- Branches: every V1 track pushes to one reused branch, claude/v1-elec in both repos, restarted from the base after each merge, so the tracks leave no new branches. Cloud sessions cannot delete remote branches (the git proxy refuses), so the older merged branches wait for Ahmed.
- If a track finds nothing serious after its first pass, it stops and says so.
- Each finished track is merged the same day (PR, then merge), with its history entry and its own lines in STATE.md, HARDWARE_AUDIT.md and TEST_PLAN.md. Nothing finished stays only on the box.

## Tracks, in order
| # | track | the question | status |
|---|---|---|---|
| 1 | electrical | Does the power system trip, over-volt or drop out? Power-on inrush and the summed get-up and fall peaks against the BMS limits, regeneration at a full 8.4 V pack and with the BMS open, the servo bus signal with the ground offset at the far servo; one quick pass over the 5 V side, protection, grounding and charging. | done 2026-11-04 (twin/electrical/ELECTRICAL_TWIN.md): 0 FAIL, 2 RISK with $0 fixes. B47: a hard 60 N shove of the standing duck draws 19.5 to 20.6 A, so a BMS at the low end of its 22 +/- 5 A band trips (TEST_PLAN 3.3 pass line 21 A). B49: left switched on after the battery hard stop, the cells pass 2.5 V in 1.2 to 4.4 hours (switch-off rule, TEST_PLAN 11). B48: power-on data not published (TEST_PLAN 3.5). Regeneration and the far servo signal are OK. Sim pass only and calc only. |
| 1b | electrical fixes | Fix what track 1 found, in the twin: B47 (the shove spike), B49 (the drain after the hard stop), B48 (power-on, fixed for the worst cited case), the far servo ground margin, and the bus signal edges at the real baud rate and cable lengths. What happens to the Pi and its microSD if the BMS trips anyway? | running |
| 2 | assembly | Is every part held by something? Can every screw be driven in some order? Can the cells, the microSD and the Pi be serviced? Does the mass model count every piece (342 screws fitted, 274 modelled; the D25 ties not counted)? Ahmed's LED ask: the third LED (the projector lamp in the upstream flash_light_module, D24) sits outside the head's side wall; the move into an eyeglass disc (fit, mount, wire, light), and viewer labels that say which LED is which. | next |
| 3 | real code in the loop | Does the robot's own runtime code, run unchanged against the sim (simulated servo bus and IMU), stand and walk? Ids, signs, units, IMU orientation (B20), the start pose, loop timing, faults. Runs the track 1b spike fix in the real code. | not started |
| 4 | joint motion | Where do the real parts hit each other through each joint's turn, the walk, the get-up (knees -88 deg, hips -68 deg) and falls? What do the cables do through that motion? | not started |
| 5 | vibration (lean) | Does walking vibration push the IMU outside what the policy was trained on? Does the head ring on the neck chain? Does a servo chatter at hold? Which screws and connectors loosen? | not started |
| 6 | heat (lean) | The twin's reading for every bench heat test, and the one lever not tried yet: lower holding gains while standing. The main heat result is already known (the live twin). | not started |

## If we do not finish today
- This file is the plan, and it is merged, so it survives the box.
- Finished tracks are merged the same day, so their work survives too. A track still running when the box stops starts again from its question above.
- To resume in a new session: clone this repo (branch altaay-lab) and the shared lab repo (main), read this file and STATE.md, and start the first track that is not done.

## Anticipated problems not yet covered
The lead adds each track's list here, with the track that settles each one.
- none yet
