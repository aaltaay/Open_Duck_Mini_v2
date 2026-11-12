# Red team: the duck and the twin

2026-11-12 ET. A hostile read of the lab files, PRs 34 to 47, and one rescore of seats those sims already stored. Nothing was printed, bought, or run on a servo. A sim pass only number is not a duck. A calc only number is not a new physics run.

This pass reused `twin/dock/nest/sim/nestlib.py` (`score_nest` and its zone constants), `twin/dock/blind/score.py` (the flush box), `twin/dock/blind/blind_runs_b190.json`, and `twin/dock/closeup/close_marker.json`. The script is `altaay_lab/redteam/rescore_runs.py`. It matched the published blind counts (35 and 380 of 540, 0 falls) with 0 mismatches against the stored pin flag. The blind moved-nest counts use that same pin rule (calc only). The card column is the seat centre only. It is a proxy, not a pin hit and not a bound on a charge.

The checklist already marks the twins FAIL or GAP. This file does not re-try those rows. It asks which quoted number still looks like a pass, and what a house does to it.

## Odds

Duckie works at home only if every line below becomes true. None of them is true on hardware.

1. The servo that will be bought has to walk, or a policy trained on a measured servo has to walk. On the sheet stall, the walk falls at 3.46 s to 3.56 s (sim pass only, `twin/electromech/ELECTROMECH_TWIN.md`).
2. Something other than the true pose has to put the pins on the cloth. With a pose only while the sun is inside the camera rectangle, the old pin rule passes in 35 of 540 (sim pass only, `twin/dock/blind/BLIND_WALK.md`).
3. The floor has to be no worse than the steps that policy can cross, or the policy has to be retrained. A 7 mm edge was 0 of 6 crossed and 6 of 6 fell (sim pass only, the feet study). The nest run that quotes 0 falls uses two 1 mm rigid steps.
4. The printed legs have to outlast the design-curve hour, or the uninstalled web has to be printed in a material that still holds near 60 C and when it is wet. Both are open (`twin/structure/STRUCTURE_TWIN.md`, `twin/structure/shin_eye/SHIN_EYE.md`).
5. The charger, the cell sensor, the two-wire gate, and the nest have to be one circuit, and the bench tests already written have to pass. They have not been run.
6. A moved mat, a stair, a spill, a pet, or a dropped pad has to have a behavior. The files do not contain those behaviors.

If line 1 is false, there is no walker. If line 2 is false, there is no dock. The rest decide whether that walker lasts a season in a house. Confidence: high that the files say this. This is not a hardware forecast.

## Findings

Severity: critical means the product does not do the thing the number is standing in for. High means a house hits it. Medium means it shows up over a season, or the handler is already known to be missing.

### 1. The bought servo does not walk this policy

- Severity: critical.
- Confidence: high. The fall times are the electromechanical twin's own runs.
- Owner: `twin/electromech` and `twin/knee`.

Evidence. With the sheet stall (19.5 kg.cm at 7.4 V, cited on the STS3215 sheet) on the as-built bus, the backlash walk falls at 3.52 s (typical) and 3.46 s (high-side), and the plain walk at 3.56 s (sim pass only, `ELECTROMECH_TWIN.md`). From 4 s to 20 s the speed is about 0.04 of the command. The same sheet model held at a flat 7.4 V does not fall in 20 s. The trained-actuator session, no fall, 42.9 minutes to 3.30 V per cell, is not that servo. The heat study says the sim knee RMS torque is 2.19 Nm, above the sheet stall of 1.91 Nm (sim pass only, `sim/ADDED_MASS_SIM.md`, quoted in `twin/thermal/KNEE_HEAT_STUDY.md`). The bought servo cannot produce the torque that walk asks for.

The stock policy on the STS3250 model falls in 4 of 5 backlash sessions (sim pass only, `twin/knee/KNEE_TWIN.md`). The opened STS3250 sheet's 1.2 ohm line and the stall current disagree: 12 V / 4.2 A is 2.86 ohm (calc only, `KNEE_HEAT_STUDY.md`). That disagreement is BLOCKER until a bench or a corrected sheet picks one.

Fix. Do not quote the trained-actuator walk as the servo on the bill. The next step is already written: a bench stall and a gain measurement (`TEST_PLAN.md` 7.5 and 15) before another closed-loop claim. The retrain stays the training row, which is NOT RUN. No new actuator model.

### 2. The dock number that looks good is the wrong test, and the wall card dies when the mat moves

- Severity: critical.
- Confidence: high for the counts this pass recomputed. Medium for a real camera, because no detector exists.
- Owner: `twin/dock/closeup` for the recommendation, `twin/dock/nest/sim` for the wall contact, `twin/camera` for the finder.

Evidence. Three tests are in the files. They are not the same dock.

| What | First sit | Label |
|---|---|---|
| True pose, old pin rule, two 1 mm steps, 20 mm aim at 7.2 V | 531 of 540, 0 falls | sim pass only, `twin/dock/nest/sim/v3/NEST_SIM_V3.md` |
| Camera rectangle, then dead reckoning, old pin rule | 35 of 540, 0 falls | sim pass only, `BLIND_WALK.md`. This rescore matched it |
| Same blind run, flush box +/-254 mm by +/-161 mm | 380 of 540 | sim pass only for the seats, calc only for the box. This rescore matched it |
| Wall card, old pin rule | 501 of 540, 1 fall | sim pass only, `twin/dock/closeup/CLOSEUP.md` |
| Wall card, flush box | 533 of 540 | sim pass only, same file |

The flush box is 508 mm along the wall and 322 mm deep. The sun the pins have to hit is a 50 mm radius disc, and a seat pin counts only inside 47 mm (`nestlib.py`, `RC` 0.050 m minus the 3 mm tip margin). The blind cloud's median seat radius is 130 mm (sim pass only, the blind report; this rescore: 129.7 mm). A seat in that box is not a charge.

The wall does not stop the body. In `nestlib.scene_xml` the wall and the rim are `contype="2"` and `conaffinity="0"`. The floor, which does push, is `contype="1"`. The blind report already says the sim does not push the duck back, and that 140 of 540 runs have a part past the wall plane (sim pass only). This rescore of the stored minimum clearance finds 131 of 540 negative (calc only on that field). The two cuts are close and not the same. Of the 380 flush-box first sits, 119 have a negative stored clearance. Of the 35 pin hits, 0 do. A fall count of 0 includes ducks that occupy the wall. The card file does not store clearance, so this pass cannot say the same of its 533.

The card is still the true pose plus the nest noise schedule, and only while a single point is inside the field rectangle (`CLOSEUP.md`). There is no frame, no detector, and no light. The entrance pupil is BLOCKER (`twin/camera/CAMERA_TWIN.md`). The recorded sit sees 0 of 13 disc samples (CAD check only, that file). D61 already says finding is by camera only, with no tags or markers. The close-up note calls the card a plain square and still a mark, and recommends it.

Moved cloth, same stored seats, duck not told (calc only, `rescore.json`):

| Shift of the sun | Blind, old pins | Blind, flush box | Card centre inside 47 mm (proxy) | Card, flush box |
|---|---|---|---|---|
| None | 35 of 540 | 380 of 540 | 494 of 540 | 533 of 540 |
| 50 mm along the wall | 65 | 389 | 257 | 533 |
| 100 mm along the wall | 65 | 387 | 6 | 533 |
| 100 mm into the room | 2 | 382 | 2 | 527 |
| 50 mm toward the wall | 74 | 350 | 178 | 533 |

The card file does not store the four pin tips. `seat_xy` in `twin/dock/nest/sim/nest_run.py` is the midpoint of the two seat pins. `score_nest` needs only one of those pins on the sun, plus a bumper pin on the ring and no bridge. The 47 mm column is the seat centre. It is a proxy. It is not a pin hit, and a centre outside 47 mm does not rule a miss in or out. Unmoved, 494 centres sit inside 47 mm, against 501 stored pin hits. The other 7 pin hits have centres from 47.36 mm to 53.82 mm (calc only, this rescore). A centre inside 47 mm also does not prove the bumper is on the ring. A 100 mm slide of the cloth leaves 6 centres inside 47 mm and does not move the flush headline. That 6 is not a charge count. The pin counts that do use `score_nest` are the blind column, because that file stores the four tips. Those move between 2 and 74 of 540 because the misses are a 130 mm cloud: a wrong sun can catch a different slice. None of those slices is a dock. The flush box stays between 350 and 416 in every shift this pass tried. It does not notice a moved nest.

The sim's own low corner, which is not a measured carpet: at 6.0 V and friction 0.6 the old pin rule is 0 of 90, and the flush box is 64 of 90 (calc only on the stored sits). The best cell, 7.2 V and friction 1.0, is 13 of 90 on the pins.

Fix. Stop quoting 380, 531, or 533 as a charge rate. The blind report already names the old pin rule as the nest's own test. Do not adopt the wall card. A mark on the wall is not the cloth, and D61 already refused marks. Before the next 540, give the wall and the rim the floor geom's `contype` of 1 in the existing `scene_xml`, and drop any run whose stored clearance is negative from the fall count. The finder that would replace the true pose is already the camera row's next step, `TEST_PLAN.md` 20.9. It is NOT RUN.

### 3. A house floor is not two 1 mm steps, and a stair is not a missed ramp

- Severity: high.
- Confidence: high that the nest sim never ran these floors. Low on the exact fall rate: the step counts are 6 and 20 runs.
- Owner: `twin/dock/nest/sim` for the floor, `twin/freeze` for the cliff, `twin/sit/getup` for the falls already missed.

Evidence. Nest sim v3, two 1 mm rigid steps: 0 falls in 540 (sim pass only, `NEST_SIM_V3.md`). The mat in every nest run is rigid. Felt friction is BLOCKER (`TWIN_CHECKLIST.md`, felt row).

The feet-contact dock was superseded (D61). The walk result was not. On a hard floor, a 7 mm edge: 0 of 6 crossed and 6 of 6 fell. A 2 mm mat on a floor that sinks 5 mm: 20 of 20 fell (sim pass only, `twin/dock/nest/superseded_feet_dock_d58/feet/deep/DEEP_ANALYSIS.md`). That file already says a real carpet lets a mat sink, and that the 5 mm sink is a model, not a measurement. A rug, a threshold, or a nest laid on carpet is that case. The nest run that quotes 0 falls does not include it.

Stair climbing is exempt (`GAPS.md` B7). Walking off a stair is not. The freeze row is GAP: there is no behavior twin of a cliff (`twin/freeze/FREEZE.md`). The cliff board's datasheet was not opened (`PARTS_AUDIT.md`). Get-up through the sit raises 248 of 296 cases and misses all 48 front rests on a down ramp (sim pass only, `twin/sit/getup/VIA_SIT_EVAL.md`). A stair is a larger drop than that ramp, and it is not in the 296.

Fix. Do not quote the 1 mm run as a home floor. The feet study already named the fix it had: retrain on 2 to 10 mm steps, or keep the approach on a hard board. The training row is NOT RUN, and this pass did not start a paid run. The cliff check is already in `TEST_PLAN.md` (a 40 mm step). The get-up misses stay on the retrain list the sit row already names.

### 4. The part that clears the margin is not the part that will be printed, and six months is past the design-curve hour

- Severity: high.
- Confidence: high on the safety factors, which are the structure files' own FEA. Medium on life: the two cited fatigue bounds disagree, and the lab already marked that BLOCKER.
- Owner: `twin/structure`.

Evidence. The stock print shin eye, voxel pitch 0.75 mm, is walk 0.80 and soft worst 0.47 (FEA pass only, `twin/structure/shin_eye/SHIN_EYE.md`). The topology file's stock number is 0.79. The collar is walk 1.30 against a walking margin of 2. The margin is not met on the print set.

The recessed web in PA6-CF, drive sheet at 4430 MPa, is walk 2.85, push 2.48, soft worst 1.61 at 0.75 mm, and 2.81, 2.10, 1.61 at 0.8 mm (FEA pass only, same file). Those two pitches agree. Mesh pitch is not how that pass was bought. The flattering mesh was the older one: TetGen on the old shin plate, walk 1.56 to 1.63, against the voxel eye near 0.8 (FEA pass only, same file). Do not cite the TetGen number.

What does break the 2.85 is the sheet the shin file already opened. The cited Bambu comparison drops humid flexural strength from 151 MPa to 95 MPa. The file scales 2.85 to 1.79 and 1.61 to 1.01 and says that scale is not a tensile result. Both would miss. Hot tensile and wet tensile of PA6-CF are BLOCKER. Saturated water absorption on that sheet is 2.35 percent (cited there). A house is not a dry annealed bar. The web is not in `print/`. Whether the printer has a hardened nozzle and a 45 to 60 C chamber is BLOCKER. Nest mass is not in the model. The other parts are unchanged: thigh sheets walk 1.71, and soft falls stay under 1.2 on roll, shin, thigh, neck, and head (FEA pass only, `twin/structure/TOPOLOGY.md` as read by the checklist).

Fatigue, same structure twin: 6667 gait cycles per hour per leg. On the cited design curve (Ezeh and Susmel 2018, P_s 95 percent) the knee sheet eye lasts 0.02 to 0.5 h and roll_to_pitch 0.04 to 0.7 h (FEA pass only). On the best-case print data neither fails, at a ratio of 1.2. The life is the gap between those bounds: BLOCKER.

Calc only, on top of that hour: 10 minutes of walking a day for 180 days is 30 hours. That is 60 times the long end of the knee-eye design-curve life. This is not a claim that the part snaps on day 30. It is the open life, counted out to six months. The best-case bound still exists. Nobody has measured which bound this filament is on.

The knee sheets see 54 to 66 C in a continuous walk (sim pass only, the thermal twin, quoted in the structure twin). At 50 C that file keeps about 0.62 of the strength (cited) and the walking safety factor falls to about 1.0 (calc only there). Creep above about 50 C is BLOCKER in that file.

Fix. Do not copy the web STL into `print/`. The shin file already says that, and it already names the coupon: a dry sheet at about 60 C, then the wet question. The fatigue rig is already proposal P7 in `STRUCTURE_TWIN.md`. No new lattice.

### 5. A walk leaves 60 C, and the cell's temperature stop is a drawing

- Severity: high.
- Confidence: high that the walk clock and the missing netlist wires are in the files. Medium on the trunk temperature at the board's own watts, because that re-run was not done. This pass did not invent a new thermal model.
- Owner: `twin/thermal` for the re-run, `circuitry` for the board, `wiring` for the netlist.

Evidence. In the heat study's own cases, a continuous walk still crosses a 60 C reading inside about 8 minutes (calc only, `KNEE_HEAT_STUDY.md`). With the sheet's torque-off left on, the case peaks near 64 C (calc only). That is inside the PLA heat-deflection band of 49 to 57 C cited in `twin/thermal/THERMAL_TWIN.md`. The 94.7 C body is the same run with torque-off switched off and with current held frozen while copper resistance rises. The study already says do not quote 94.7 C as the knee the duck will build. This pass agrees.

The 55 C stop is `software/knee_heat.py`. The checks are unit tests with no servo (`software/SOFTWARE.md`). The log behind the minutes is the trained actuator, 1.45 A RMS on the right knee for the first 4 minutes (sim pass only), not the sheet-stall servo that falls at 3.5 s. A held 2.5 A stall reaches a 60 C reading in 0.7 to 1.0 min if nothing cuts it (calc only, the heat study). That is not the walk. It is what a knee does when the policy asks for a torque the servo does not have.

Docked charge, the model that was run: 1.9 W to 3.2 W, torque off, 6 hours. Hottest cell 42.4 C, trunk wall 37.6 C, BEC case 58.1 C, high corner, 32 C room (sim pass only, `THERMAL_TWIN.md`). Cells in that table stay inside 0 C to 60 C. The trunk wall stays under the 49 to 57 C band. The BEC case at 58.1 C does not. BEC efficiency 0.85 is an assumption. Castle publishes none. That 0.85 is BLOCKER (`TWIN_CHECKLIST.md`, thermal row).

The board's own arithmetic, not re-run in the twin: at the D61 9.5 V figure, 2.30 W at a 7.2 V pack and 3.50 W at a 6.0 V pack if the current stays 1.00 A (calc only, `circuitry/CHARGER_BOARD.md`). Both are above the 1.9 W to 3.2 W the twin ran. In-trunk thermal resistance is BLOCKER. The 62 C/W figure is the sheet's JEDEC board (cited, DS20002190C), not the closed trunk.

The chip has no THERM pin (cited, that datasheet). The block diagram labels die regulation at 110 C (cited there). The cell sheet allows charge only from 0 C to 60 C (cited, P45B version 1.2). A die limit of 110 C is not a cell limit. The NTC window in the charger note, worst corners 1.33 C and 58.36 C (calc only), uses parts whose sheets are partly unopened (TL431 is BLOCKER in that file). GPIO5 and GPIO6 are not in `wiring/netlist.yaml`. The board has no seat. The electrical twin was not re-run on it.

There is no balancer. AN231, cited in the charger note, says a series pack should have balancing considered. The BMS discharge cut used in the lab notes is 2.40 V per cell, below the cell sheet's 2.5 V floor (`GAPS.md`). The compliance note says that BMS number was not re-read on a Tenergy sheet in that session. A blanket, a dog against the shell, or a carpet under the belly is not a case in the thermal twin.

Fix. Do not freeze the charger in the trunk. The charger note already says to re-run the existing thermal twin at 2.30 W and 3.50 W, and to merge the board into the netlist only after the seat exists and the unopened parts are read. The knee guard stays a software stop until `TEST_PLAN.md` 7.3 measures a servo. No new charger chip.

### 6. Live cloth, a dropped pad, a child, a pet

- Severity: high.
- Confidence: high that the tests are unrun and the handler is missing. Medium on how a real pad drop feels, because that hanging test was not done.
- Owner: `twin/dock/nest/stripes` for the gate, `software` for the pad and the image, `twin/sit` for the short leads.

Evidence. The cloth is open on the floor while it is the supply. `COMPLIANCE_FIRST_PASS.md` already says a hand, a pet, a spill, or a piece of metal can touch it, and that the duck does not cover all of it. The two-wire gate is not a circuit. `TEST_PLAN.md` 20.5 (water, metal, a skin stand-in) is not run. Pull-out by hand, and a coin across the poles, is 20.3, not run. The signature behavior is described in the stripe study (calc only) and is not code (`DEFINITION_OF_DONE.md`, gate 5).

The STS3215 sheet marks ASTM F963 as No (cited in the compliance note). The standard text was not opened. This pass does not apply a small-parts gauge. The antenna is a 150 mm rod, 1.8 mm across, with a 3.8 mm tip bead (`GAPS.md`, measured). The proposed probe tip is 1.40 mm (cited, the catalog, `PARTS_AUDIT.md`). A part that comes off in a hand is an untested swallow hazard. The pull-out test is the one already written.

The setup note cites the upstream README: Y head mode can break the head (`software/PI_SETUP.md`). Not re-tested here. The upstream image unit uses `Restart=always`. The lab unit is `Restart=no`, so a guard stop stays a stop (same file). A duck left on the image restarts the walk. On a stop, servos keep their last targets (same file, citing the upstream Ctrl-C path).

`UPSTREAM_ISSUES.md` G9: the walk needs a gamepad, and nothing stops the robot if the pad drops. The upstream note it quotes says connection loss can take a while to detect. The hanging test named there is not done. Bluetooth latency is BLOCKER (`software/SOFTWARE.md` section 11). Wi-Fi is not the dock (D46) and its latency is BLOCKER too, so a remote stop over Wi-Fi is not a handler that exists.

A dog and a spill into the shell are not named tests. The shell is the printed body. The pack behind screws is D45, and nothing is built. The knee kit leads are 24 mm and 25 mm short of the 40 mm slack rule (CAD check only, `twin/sit/SIT.md`). A snag or a chew meets that short lead first. One dirty well opens the charge, and dirt is BLOCKER (`twin/dock/flush/FLUSH_CONTACTS.md`).

Fix. Do not leave a mat powered until `TEST_PLAN.md` 20.5 passes. The compliance note already says that. Use the lab unit, not the image unit, which `PI_SETUP.md` already tells the installer to disable. Run the pad-drop test G9 already names, with the robot hanging. A hit from a pet uses the same post-hit look already in `TEST_PLAN.md` section 9 (knee eyes, roll_to_pitch, the shell). Lengthen the knee leads to the slack rule the sit file already uses. No new cover, no new radio stop.

### 7. The camera and the microphones have no privacy behavior, and the radio is on

- Severity: medium.
- Confidence: high that the programs are unwritten. The legal host check is uncertain in the compliance note, and this pass did not open the grant.
- Owner: `software`, with the radio label staying where `COMPLIANCE_FIRST_PASS.md` already put it.

Evidence. Nest vision has no file (BLOCKER, software row). Gate 7 asks for a cue when the camera is on, no stored face library, and no upload by default. Not written (`DEFINITION_OF_DONE.md`). "No face library" is true because the finder does not exist, not because a program refuses one.

D49 keeps the duck listening. The freeze row has mic seats and no hearing twin (`twin/freeze/FREEZE.md`). Wi-Fi is on the Pi (cited, the product brief, in the software link table). D46 says it is not used for docking. The setup note records the upstream image's shared login and says the hotspot fallback can stay. This file does not repeat those strings. A camera and a microphone on a known login are the privacy problem. `PI_SETUP.md` already says a manual install sets its own user and its own Wi-Fi.

The camera brief's FCC line is for the camera as sold, not for this body (compliance note). The Pi's grant was not read. Whether this host is inside the module approval is uncertain there.

Fix. Put the cue, the "camera on" behavior, and "do not keep a face library" into the program list that `software/SOFTWARE.md` section 10 already is, and do it before a nest-vision file exists. Follow the manual-install password step already in `PI_SETUP.md`. Do not add a second radio. The outside label waits on the grant, which the compliance note already says was not read.

### 8. After six months: one chain, a weld with no name, and leads that start short

- Severity: medium.
- Confidence: high that the parts and the tests are missing. Medium on the month a connector actually fails, because no cycle test has been run.
- Owner: `wiring` for the harness, `twin/battery` for the weld, `twin/sit` for the leads, `twin/structure` for the inserts.

Evidence. The neck chain hangs off the left ankle through one made lead (G10, `CABLE_MAP.md`). A checksum error can panic the walk. The lab catch of that panic is on a simulated bus (`software/SOFTWARE.md`). G10's pull-test and the count of errors per servo are not done.

The weld has no part number (battery row, NOT ORDERABLE). No balancer, so the weak cell ends the discharge earlier as the pack ages (AN231, cited in the charger note). Insert pull-out is BLOCKER in the screws row. Self-tapping strength in printed pilots has no coupon.

The servo warranty on the motor and the gears is 6 months, and there is no duty curve (`GAPS.md` B2). `TEST_PLAN.md` 7.3 is the measurement, not run. The sole-strip note counts about 6,700 bends and scuffs per walking hour (calc only, `FLUSH_CONTACTS.md`). The knee wire sees the gait too. No wire life number: BLOCKER. The pin catalog's 500,000 cycles are in a socket, not on cloth (cited in `DEFINITION_OF_DONE.md`). The 500-cycle first look is `TEST_PLAN.md` 20.4, not run.

Fix. Do the G10 actions already listed: strain-relieve that lead, power off before unplugging, count checksums on the bench. Bring the knee leads up to the slack rule in `SIT.md`. Source the weld before calling the pack a part, which the battery row already says. Do not publish a six-month life until P7 and 7.3 and 20.4 have numbers. No new connector family.

## What this pass did not break

The PA6-CF web's two voxel pitches agree (2.85 and 2.81, FEA pass only). Pitch is not a hidden pass on that shape. The accelerometer +1.3 that `UPSTREAM_ISSUES.md` G7 flagged is subtracted in `twin/dock/nest/sim/nestlib.py`, `sim/added_mass_sim.py`, and `sim/current_budget.py` before `get_obs`. The dock comparison in finding 2 is not that bias. This pass did not re-run `sim/run_stock_walk.py`, so the older walk-speed note G7 names was not re-checked.

The docked-charge table that was run does keep the cells inside 0 C to 60 C at 1.9 W to 3.2 W (sim pass only). This pass does not claim those cells are already over the limit. It claims the board's own watts were not the watts in that table, and the cell sensor is not in the netlist.

## How to rerun the rescore

From the repo root: `python3 altaay_lab/redteam/rescore_runs.py`

It only reads the two run files and writes `altaay_lab/redteam/rescore.json`. Calc only. It does not start MuJoCo.
