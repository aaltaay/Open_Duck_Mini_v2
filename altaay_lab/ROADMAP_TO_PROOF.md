# Roadmap to proof

Written 2026-11-24, 1:10 PM ET. This is the ranked list of what is still open between the files on `altaay-lab` and a duck we can prove: it walks, it finds the nest v2 mat with the camera only, it sits and charges, it lives at home for days, it is useful, it can be sold at a fair price, and there is one digital twin of that same duck.

Nothing in this file was bought, printed, or measured on a part. A sim pass only number is a model. A calc only number is arithmetic. A CAD check only number is a measurement on a mesh. A cited number comes from a page or a lab file named here. Measured in emulation means a program was run under a stand-in of the board, not on the board. BLOCKER means the number or the part is not known. Those labels do not pass a gate. DEFINITION_OF_DONE.md says so, and this file follows that rule.

D61 is not edited. The bill files are not edited. The chart is `altaay_lab/docs/images/roadmap_gates.png`.

## How to read the rank

Rank 1 is the measurement that makes the rest of the claims true or false. Later ranks are real gaps. They wait on rank 1, on a part, or on a track that is already owned elsewhere. Four tracks are already in flight and are not started again here: the Pi 5 2 GB seat, the nest charging electronics, camera-only nest docking, and owner setup with updates. Their gaps stay on this list because they are not proven.

## Gates 0 to 8

All nine gates are open. Files exist for the early gates. A file is not a pass.

| Gate | What a pass is | Status | What is on file | What is missing |
|---|---|---|---|---|
| 0 | The twin and the one-click bill are the same duck, line by line, and the duck is not printed or fully ordered before that | OPEN | `make twin` loads the run D walk. 41.48 walking minutes, knee peak 38.4 C, pack peak 13.81 A, 0.000 s at or above 15 A (sim pass only, TWIN_CHECKLIST.md and twin/out/REPORT.md). No checklist row is PASS | Nest v2 is not in the print set, the netlist, or the viewer. The bill still cannot be ordered as this duck |
| 1 | Every part matches a datasheet that was opened | OPEN | P45B sheet, STS3215 C001 sheet, camera brief, and the MCP73213 sheet were opened (cited, PARTS_AUDIT.md and circuitry/CHARGER_BOARD.md). The C018 page that was opened does not print a separate winding resistance (redteam/VERDICT_2026-11-13.md) | Servo torque in the twin, charger dropout, felt, foil, wells, and the weld are not datasheet facts for the duck that will be built |
| 2 | TEST_PLAN.md numbers are measured on the parts | OPEN | The plan is written. Bench scripts have been run on a simulated bus (software/SOFTWARE.md). That is not this gate | No cable, cell, servo, board, or printed part has been measured |
| 3 | Ten sits at a low pack and ten at a full pack, camera only, on the real mat, no fall, charge current flows | OPEN | Nest sims and a camera-dock sim exist (sim pass only). They use a pose stand-in or a drawn mark. Do not quote 380 of 540, 533 of 540, or 38 of 40 as a charge rate | No real camera, no real mat, no real sit |
| 4 | Pins or wells, cloth, knee wires, and sit screws survive a cycle count written down before the test | OPEN | TEST_PLAN.md 19.7 and 20.4 name the tests. The pin catalog's 500,000 cycles are in a socket, not on cloth (cited, PARTS_AUDIT.md). Nest v2 dropped the springs | No cycle has been run. A life number is BLOCKER |
| 5 | Charger, pack, and mat are safe on the bench, and a shipped pack has a UN 38.3 summary | OPEN | COMPLIANCE_FIRST_PASS.md and compliance/COMPLIANCE.md say why the tests exist. They are not the pass | The pack is not built. The mat gate is not a board. Cells, charger case, and the nearest plastic have no charge log |
| 6 | The paperwork and the lab tests the compliance map names, before any sale | OPEN | The Covered List note was read (cited, compliance/FCC_COVERED_ROBOT.md). It is not a ruling on this duck | No host radio check, no unintentional-radiator check, no transport summary. Which UL or IEC document applies was not opened: BLOCKER |
| 7 | Several days of real walking, sitting, docking, and get-up, on the home floor, with the camera cue and no face library | OPEN | software/autonomy/ is a supervisor. It calls sim counts. It says it does not pass this gate | No day on a floor. Fall recovery on a real robot is GAP. Privacy behavior is not written as a pass |
| 8 | A second person builds a second duck from the documents, and it passes the same tests | OPEN | docs/OWNERS_MANUAL.md and docs/BUILD_GUIDE.md exist. Both say the duck has not been built | No first unit, so no second unit. The nest is not in the build order |

## Ranked gaps

### 1. The servo in the twin is not a servo we have measured

(a) The current walk is run D on a 12 V STS3215, held at a 12.0 V rail (sim pass only, TWIN_CHECKLIST.md). An older closed loop with the sheet stall on the as-built 2S bus falls at about 3.5 s (sim pass only, problems/STALL.md). A corrected heat step on a different log reaches a 55 C reading at 1.16 min at 1.551 A RMS (sim pass only, redteam/VERDICT_2026-11-13.md). The only cited clock for this servo family, an oscillation on a bench that is not this walk, took on the order of 40 to 50 minutes to climb from about 48 C to 60 C (cited, twin/thermal/THERMAL_TWIN.md). Run D's own knee peaks at 38.4 C and rests 0 times (sim pass only). The winding used for heat, 3.753 ohm, is an assumed split, not a measurement (calc only, and BLOCKER as a C018 fact, same verdict). Register behavior, backlash on our unit, and rotor inertia are BLOCKER.

(b) Bench measurement. TEST_PLAN.md sections 6 and 7, on one 12 V unit, at the 12.0 V rail this walk uses. Log Present Temperature, current, and voltage until 55 C or 30 minutes, at a current near the logged knee, and write the cold resistance. That one log tells us which clock to believe. It does not by itself pass gate 2 for the whole duck.

(c) Yes. The smallest set is in "Minimal first purchase" below. Do not buy fourteen servos for this row.

(d) Nothing in software makes this number true. The scripts that will log the servo already exist (bench/first_servo_check.py, TEST_PLAN.md 7). They can be pointed at 12.0 V in the test notes when the unit is on the bench. Do not retune the thermal twin until that log exists.

(e) Depends on Ahmed saying yes to this coupon, and on a current-limited supply. Gates 2, 3, 5, and 7 depend on this row. A walk retrain that ignores the measured stall is a new model, not a proof.

### 2. There is not one installed duck

(a) The print set, the netlist, the viewer, and the fastener schedule describe the walking duck. Nest v2 (the striped felt mat and five seat wells, D62, altaay_lab/cad/nest_v2/) is the nest we mean, and it is not installed. The 3S pack, the BQ24133 charger, and the 12.0 V rail are in later notes. The netlist still carries older dock parts. check_power_limits.py prints the 2S protector and the 2S charger as open next to a 3S domain (redteam/VERDICT_2026-11-13.md). TWIN_CHECKLIST.md: no row is PASS. Fitted screws in the unaudited-for-nest schedule are 310, builder-turned 254 (CAD check only). Nest v2 adds no screw and is not in that schedule. VERIFICATION.md on 2026-11-10 still fails the 2S power path: a servo under 6.0 V for 11.1 percent of a nominal walk (sim pass only). That fail is the 2S model. It is not a 12 V result, and it is not a pass.

(b) CAD check only can install one model. Gate 0 still needs the bench and the bill. A sim of the installed model is evidence. It is not the gate.

(c) No parts for the file merge. Printing the installed set is not allowed before gate 0.

(d) Diff the print set, the netlist, the viewer, and the bill against nest v2 and the 3S rail, and list every line that disagrees. Do not copy a proposed shin web into print/ (gap 7). Do not edit D61. The charging-electronics track owns the board. This row is the merge after that board has a seat, not a second schematic.

(e) Depends on gap 4 for the charger seat, and on the camera track not changing the mat. Gate 0 cannot pass before this row. Gate 8 cannot pass before this row, because a second builder has to build the same files.

### 3. The duck does not find the nest with the camera

(a) D61 requires camera only, no tags. That finding is untested (BLOCKER). The head cone is on the seat (CAD check only, twin/camera/CAMERA_TWIN.md). A level head sees the disc at about 1 m and about 2 m, and the recorded sit sees none of the cloth (CAD check only). Room light and exposure are BLOCKER. Nest v3's best walk-in is a mixed controller on two 1 mm steps: first sit 524 of 540, 0 falls (sim pass only, twin/dock/nest/sim/v3/NEST_SIM_V3.md). The mat in that run is rigid and the pose is a stand-in. A later camera-dock batch with proud wells scores 38 of 40 charging (sim pass only, twin/out/REPORT.md). The flush face in that note is 0 of 40 (sim pass only). Nest v5 did not treat 38 of 40 as an approval (history/2026-11-16_2200_nest_v5.md). None of these is gate 3.

(b) Full robot test. TEST_PLAN.md 20.9: about 1 m and about 2 m, lights on and lights dim, low pack and full pack, 10 of 10 in each set, no tag and no pose handed in. A perception twin on frames can come first. It does not close the gate.

(c) The camera and the Pi are on the full bill, not in the first purchase. A camera coupon without the walk does not prove a dock. The first purchase does not include them.

(d) The camera-only docking track owns the finder. Do not start a second detector here. What this list adds is the pass line: frames scored the way TEST_PLAN.md 20.9 is already written, and no quote of a seat count as a charge rate.

(e) Depends on gap 1 if the walk that approaches the mat uses the servo model, on gap 5 for the real mat edge, and on gap 17 for a contact that means "charging." Gate 3 stays open until the full robot test.

### 4. The mat does not yet charge the duck safely

(a) The charger that the 3S notes name is the BQ24133 board (ORDER.md, D65). It has no seat and no gerber (BLOCKER, ORDER.md). The MCP73213 file is the 2S record. GPIO wires for status and enable are not in the netlist (TWIN_CHECKLIST.md). In-trunk thermal resistance is BLOCKER. On the cited 62 C/W board the die crosses 110 C and 150 C if 1.00 A is forced (calc only, CHARGE_WATTS.md). That board is not the trunk. The two-wire gate that refuses water, metal, and a skin stand-in is not designed (TEST_PLAN.md 20.5). A coin across the stripes, dirt on the gold, and what happens when the duck stands up are open. The duck must not stand on a live mat. That behavior is described and is not code (DEFINITION_OF_DONE.md gate 5).

(b) Bench measurement for the gate and the temperatures (TEST_PLAN.md 20.5 and 20.8). Certification only after those pass, if a chosen standard asks for a lab (gate 6, and the standard itself is BLOCKER).

(c) Not in the first purchase. The board is not designed, so there is no part number to buy. Buying a charger chip before the seat exists repeats the "eval board in the trunk" problem PARTS_AUDIT.md already names.

(d) The nest charging electronics track owns the board, the seat, and the gate. Do not draw a second charger here. Software that can be written after the netlist exists, and not before: turn the signature off, wait until the mat is back at the probe, then stand.

(e) Depends on gap 2 for the netlist merge, and on gap 17 for contact ohms. Gates 3, 5, and 7 wait on this row.

### 5. The walk on file is not a home floor

(a) Run D walks a flat room circuit in sim: 41.48 minutes, path speed 0.152 m/s (sim pass only, twin/out/REPORT.md). The stock policy, in the shared lab gym, walks only on flat ground. It fails a 5 degree up ramp (0 of 40), trips a 13 mm threshold (0 of 10), and our heavier build trips a 3 mm edge (0 of 5) while the trained mass passes 5 of 5 (sim pass only, STATE.md). A feet study records 0 of 6 crossings on a 7 mm edge and 20 of 20 falls on a 2 mm mat over a 5 mm sink (sim pass only, problems/PROBLEMS.md). Those runs are not run D, and they are not the two 1 mm steps. Fold-to-sit from a walk and sit-to-stand are not trained (TWIN_CHECKLIST.md). Run D's nest sim did not sit (same file).

(b) Sim first, on the real mat shape and on small edges, with the run D policy, in the shared lab gym. Then a full robot test: tethered crossings of the real felt edge (TEST_PLAN.md 20.6) and a walking log (TEST_PLAN.md 9). A passing sim does not close gate 3 or gate 7.

(c) No parts for the sim. The felt edge test needs the mat coupon in gap 17, after a grade exists.

(d) Score run D on a 2 mm step, on two 1 mm steps, and on a soft contact, and publish the fall count with the policy name. Do not start a paid training run from this file. Get-up misses and the mat edge can share one later training scope. Ahmed's OK is still required before any rented training.

(e) Depends on gap 1 before anyone treats a new gait as the one to print. Gap 3 and gap 8 depend on a walk that can reach the mat and the floor without a fall the policy cannot explain.

### 6. A day of walking is a heat model we should not believe yet

(a) Two sims disagree in kind. The corrected high-current log reaches 55 C in 1.16 min (sim pass only, verdict above). Run D at 0.88 A RMS in the knee peaks at 38.4 C and never rests (sim pass only). Continuous walking in the older heat study still leaves the 60 C operating line inside about 8 minutes (sim pass only and calc only, KNEE_HEAT_STUDY.md). The 94.7 C body is the same family of run with the torque-off switched off. The verdict says do not quote it. Castle efficiency 0.85 and dropout 0.30 V are assumptions (BLOCKER). The adopted regulator is no longer that Castle unit (gap 16). The 55 C guard is a software stop in unit tests. It has not run on a servo. Cell specific heat in the sit model is an old 18650 range, not the P45B sheet (TWIN_CHECKLIST.md).

(b) Bench measurement of one servo (gap 1) replaces the clock. A full robot test over days, with the log kept, is gate 7. Charge temperatures are gate 5 and need the seated charger (gap 4).

(c) The servo, the meter, and the supply in the first purchase. Not the whole duck.

(d) Stop quoting a single heat clock as the duck. Keep both clocks labeled with the policy and the current. Do not add another thermal step size until the bench log is the input. Callers that still default to a 0.5 s thermal step were not all re-audited (verdict). Treat a clock that was not regenerated after a bin-width check as untrusted.

(e) Depends on gap 1. Gate 5 and gate 7 depend on this row. Gap 7 (the plastic) depends on the same temperature log.

### 7. The leg we would print does not clear the strength bar

(a) The structure twin's walking margin is 2, and the fall margin is 1.2. On the print that is in the slicer, the shin eye is under that walking margin (FEA pass only, twin/structure/shin_eye/SHIN_EYE.md). A recessed web in PA6-CF, not in print/, is walk 2.85 and soft worst 1.61 at 0.75 mm (FEA pass only). Hot tensile and wet tensile of that filament are BLOCKER. The lab printer's nozzle and chamber are BLOCKER. Fatigue on the cited design curve is 0.02 h to 0.5 h at the knee eye (FEA pass only, problems/PROBLEMS.md). Which bound this filament sits on is BLOCKER. Nest mass is not in that model. D26 is still open. Soft falls put several parts under 1.2 (FEA pass only, TOPOLOGY.md).

(b) A coupon: dry tensile of the sheet that will be printed, at about 60 C, then the structure twin re-run with that number. A full robot test is looking at the eyes after real falls (TEST_PLAN.md 9). Certification is not this row.

(c) Not the first purchase. A PA6-CF coupon needs a printer that can run it. The printer is BLOCKER, so buying a spool before the process is known does not prove the margin. Filament for the full duck is already on the order and is not this coupon.

(d) Do not copy the web STL into print/. Re-run is allowed only after a coupon number exists, or as a labeled study that does not become the duck. The topology pass on file did not save a print mass we can claim (COMPLETE_DUCK_AUDIT.md).

(e) Depends on naming the printer (gap 26) before PA6-CF is the material. Gate 0 mechanical, gate 4, and gate 7 wait on a part that survives the falls the duck will actually have.

### 8. Get-up is not proven on the real stops

(a) The searched program, roll onto the belly, sit up into the sit, then the sit's stand, raises 248 of 296 cases on the merged sit model (sim pass only, twin/sit/getup/VIA_SIT_EVAL.md). Every back and side case in that set gets up. 0 of 48 front rests on a down ramp get up. The autonomy note's 112 of 112 is the flat-floor slice (sim pass only, software/autonomy/AUTONOMY.md). It is not the full set. Hip pitch sits at its torque limit through the sit-up (sim pass only). Unpowered friction is not on the Feetech sheet (BLOCKER, TEST_PLAN.md 19.5). With the torque off, about 4.3 N forward at the head tips the sit model (sim pass only, STATE.md). Older programs ask for knee and ankle angles the printed parts cannot reach. Those results do not count (GETUP_SIT.md).

(b) Sim on the CAD stops for the 48 ramp misses, then a full robot test: five get-ups at the low bus voltage, temperatures and currents logged (TEST_PLAN.md 19.9). Friction is a bench measurement first (TEST_PLAN.md 19.5), then the sim is re-run with that number.

(c) The one servo in the first purchase can host the friction lever and a single-joint hold. It cannot get up. The full test needs the duck.

(d) Keep the 48 misses on the training list. Do not call the flat 112 a get-up. One limits table, from the CAD contacts, used by the sim and by the Pi (gap 19). No paid training from this file.

(e) Depends on gap 1 for the torque the real servo can hold for about 1 s. Gate 7 requires this get-up on the home floor.

### 9. The bill is not one duck, and several lines cannot be bought

(a) A one-click of the current bill misses nest v2 and can still name parts the nest no longer uses (PARTS_AUDIT.md). Buy-today total on the order is $1,246.70 (calc only, bom/order/ORDER.md, 2026-11-14). Per-duck parts, tools and full spools removed, are $1,000.19 (calc only, same file). BOM.md's own rollup is a different sum, $1,303.35 (calc only, TWIN_CHECKLIST.md). Felt, foil, the five wells, the weld, the gate board, and the charger gerber have no orderable part (BLOCKER). The Pi Zero 2 W and the P45B were out of stock at the sellers opened on 2026-11-11 (cited, PARTS_AUDIT.md). Stock was not reopened for this roadmap: live stock is BLOCKER. Line 17m, the Pi-header housings, the eye bead, and the antenna servos still lack a closed part number (PARTS_AUDIT.md).

(b) A cited live page for each line, then a diff against the installed twin (gap 2). That is the gate 0 bill. It is not a purchase.

(c) Do not place this order. The first purchase is the four lines below, and only after a yes. Reopening a stock page is research, not a buy.

(d) A checklist of BLOCKER lines, each with the file that must name the part, is already PARTS_AUDIT.md plus ORDER.md. Keep them. Do not add prices to a new bill in this pass.

(e) Depends on gap 2, gap 4, and gap 17 before the nest lines exist. Gate 8's second unit buys this bill after every later change, not today's bill.

### 10. The computer seat is still the Pi Zero, and the useful stack does not fit it

(a) The body is laid out for the Pi Zero 2 W, 65 mm by 30 mm (cited, software/pi_fit/BOARDS.md). Bookworm Lite on that board does not leave enough RAM for the stack the lab wants (software/pi_fit/FIT.md). An idle stand-in of aarch64 Python under qemu-user was 29.1 MiB (measured in emulation). How much of that is the translator is BLOCKER. A Pi 5 with 2 GB is 85 mm by 56 mm and does not drop into the Zero seat (cited, same board note). The cited price for that Pi 5 is $77.50 (cited, Raspberry Pi price note of 1 Oct 2026, software/pi_fit/BOARDS.md). Nothing has walked on either board.

(b) CAD check only for a new seat, then a bench measurement: the real stack's free RAM, the 50 Hz loop, and the camera, on the board that will ship. A full robot test is the walk with that load. This roadmap does not do the seat.

(c) Not the first purchase. A Pi with no seat does not prove the walk. The seat track owns the redesign.

(d) The Pi 5 2 GB seat track owns the geometry. Do not draw a second seat here. Software that is already honest: FIT.md's memory map. Leave it.

(e) Depends on the seat existing before owner setup (gap 11) is run on hardware. Usefulness (gap 12) and gate 7 depend on a board that can hold the walk and the camera at once.

### 11. An owner cannot set the duck up, and cannot update it, on a real unit

(a) software/DAY_ONE.md and software/PI_SETUP.md describe an install. The day-one path has a mock. The mock is not a Pi. software/SOFTWARE.md section 10: updates after the install apt commands are not written. The Runtime stays unmodified (D6). Ears on hardware PWM are still an open question (D53, software/ANTENNAS_PWM.md).

(b) Bench measurement on the board from gap 10: a blank card to a walking idle, then an update that does not lose calibration. Gate 8 is a second person doing that from the manual, with no developer in the room.

(c) The board is not in the first purchase. A microSD is on the full bill and is useless until the board and the seat exist.

(d) The owner-setup and update track owns this. Do not write a second installer. The pass line to add, when that track asks, is: the mock is not the pass, and an update has a written rollback.

(e) Depends on gap 10. Gate 7 and gate 8 depend on it. A duck that cannot be updated cannot be left in a home for days.

### 12. Useful behavior is a demo

(a) The companion rank is written (software/companion/USEFULNESS.md). Voice timing next to the walk is BLOCKER. A person finder is BLOCKER. Reminders run in the demo with no model. Follow, play, and pet check are not designed as a behavior the duck does. The autonomy supervisor wanders and greets from the personality engine (software/autonomy/AUTONOMY.md). It has not run on a duck. Mail and calendar are a mock with no key, which is correct for this public repo, and they are not a product.

(b) Full robot test: a person at home uses the first two jobs (answer, and a reminder) on one day, offline, while the walk loop keeps its 50 Hz. A sim of the state machine does not close this.

(c) No extra parts in the first purchase. Mics are already on the full bill (TEST_PLAN.md 17) and are not useful until the board fits (gap 10).

(d) Keep the demo. Do not add a cloud key. Do not add a face library (gap 18). A latency budget beside the walk can be written as BLOCKER lines until a Pi measurement exists.

(e) Depends on gap 10 and gap 11. Gate 7's "usable at home" is this row plus docking and get-up. A fair price (gap 23) depends on a person wanting the behavior, not only on the parts sum.

### 13. The pack cannot be built, left on charge, or shipped

(a) The cell on the sheet is the P45B (cited, PARTS_AUDIT.md). The count on the current bill is three (ORDER.md). The weld, the sleeve, and the fish paper have no part number (BLOCKER). Weld resistance is not in the model. The protection board named on the order is a 3S part in that file, and the netlist's older 2S board is still the one the wiring drawings generate (gap 2). There is no UN 38.3 test summary, because there is no pack (gate 5). Charge window on the cell sheet is 0 C to 60 C (cited). The bench limit in TEST_PLAN.md 20.8 is tighter: cells 0 C to 45 C. No charge has been run.

(b) Bench measurement: cell match, weld drop, protector trip, and one full charge with the temperatures in TEST_PLAN.md 20.8. Certification: the UN 38.3 summary for the pack that will ship, before any shipment (cited rule, 49 CFR 173.185, as named in DEFINITION_OF_DONE.md).

(c) Not the first purchase. Three cells at the illumn figure on the bill are $8.99 each (cited, BOM.md line 6). Three times $8.99 is $26.97 (calc only). Cells without a weld procedure do not prove the pack, and a bench supply stands in for the pack on the servo test.

(d) Do not model a weld resistance. Leave it BLOCKER. Do not resize the bay: the opened sheet's maximum already fits the sleeved pack on file (CAD check only, PARTS_AUDIT.md).

(e) Depends on gap 4 for the charger and on gap 9 for a part number. Gates 5 and 6 wait on the summary before a sale or a shipment.

### 14. A sale is not cleared

(a) compliance/COMPLIANCE.md and compliance/FCC_COVERED_ROBOT.md are research notes, not legal advice, and not a pass of gate 6. The finished duck may fall in the Covered List robot class. The model mass used in that note is 2.81 kg, which is 6.19 lb (calc only). The line in the notice is 4.4 lb (cited). The duck has not been weighed, so the scale result is BLOCKER. Wi-Fi speed in kbps was not on the brief lines that were read (BLOCKER). Whether the Pi's own grant covers this body is BLOCKER (47 CFR 15.212, as named in DEFINITION_OF_DONE.md). Marketplace legal names for several brands were not opened (BLOCKER, COMPLIANCE.md). No agency filing exists.

(b) Certification: the host check, the unintentional-radiator check, and a lawyer's reading of the Covered List, before any sale. A scale reading of a built duck is the mass input. It is not the certificate.

(c) No lab fee is cited. A fee page was not opened (BLOCKER, COMPLIANCE.md). Do not buy a test slot from this roadmap.

(d) Keep the notes. Do not write "the duck is allowed" or "the duck is banned." The open items are already listed in those files. Weighing is gate 2's mass step, after a duck exists.

(e) Depends on gates 2, 5, and 7, because the unit that is tested has to be the unit that is sold. Gap 23 (price) waits on this, because a price that ignores a failed radio check is not a price we can charge.

### 15. Nothing has a wear number

(a) Gate 4 needs a cycle count chosen before the test. The knee loop test on file is 1 million cycles (TEST_PLAN.md 19.7). It has not been run. The cloth look in TEST_PLAN.md 20.4 is 500 sits, and it is a first look, not a life. Nest v2's wells replace the spring pins, so the pin catalog's 500,000 cycles do not apply (cited, the catalog is a socket). Screw insert pull-out time is BLOCKER (TWIN_CHECKLIST.md). A worn contact that still charges without a hot spot is unmeasured.

(b) Bench measurement on coupons first (wire loop, well on foil, insert). A full robot test is the same cycle count on the refitted duck, with the dock program unchanged (gate 4 software).

(c) Not the first purchase. The well coupon waits on a felt grade and a foil part (gap 17). The knee loop waits on printed leg parts, which wait on gate 0.

(d) Write the cycle count into the test record before any coupon starts, so the number is not chosen after the result. Do not use 500,000 from the pin catalog as the cloth life.

(e) Depends on gap 7 for the plastic, gap 17 for the contact, and gap 1 for a wire that is worth cycling. Gate 7's "several days" is a short sample of this row, not a substitute.

### 16. The regulator and the protector are paper

(a) The rail the walk holds is 12.0 V (cited, the power-limit check). The part on the order for that rail is the TDK-Lambda I7C2W020A120V-0F1-R at $86.34 (cited, DigiKey, read 2026-11-14, ORDER.md). Castle at $54.95 is superseded (same file). What the shipping regulator does below its set point, and its efficiency, are not a bench log (BLOCKER until measured). The verdict's 0.30 V and 0.85 figures are the old Castle assumptions. Do not copy them onto the TDK part. Limb current during a real walk, as time above the breaker limit rather than a short average, is BLOCKER (verdict, top measurements). The breaker parts are not in series with the live feeds (CAD check only, verdict).

(b) Bench measurement: input swept from a full 3S pack down through the walk window, at a few amps, recording whether the output holds, follows, or shuts off. Then one limb current on a walking duck. The second of those is a full robot test.

(c) Not the first purchase. The regulator is the second electrical buy, after gap 1 says the servo is worth powering. Price $86.34 is cited, not a new quote. Stock was not reopened: BLOCKER.

(d) Do not run another dropout sim with 0.30 V and call it the TDK part. The power-limit check already guards the set point. Leave it.

(e) Depends on gap 1, because a regulator test at the wrong current answers the wrong question. Gap 6's day-long heat depends on the measured loss, not on 0.85.

### 17. Felt, foil, and the five wells are not a material

(a) No felt grade is named (BLOCKER, TWIN_CHECKLIST.md). Sole friction on felt is BLOCKER. The nest sims that quote fall counts use a rigid mat. Ten percent of a 2.0 mm stack is 0.2 mm (calc only, CONTACT_TWIN.md). Dent depth is BLOCKER. Well resistance with dust was not measured (BLOCKER). One grey cloth page that was opened is not the gold pair (PARTS_AUDIT.md). Gold and pale gold have no part number (BLOCKER).

(b) Bench measurement on a named coupon: friction, thickness under the sit load, and four-wire ohms of one well pair at the charge current, clean and then with dust (the intent of TEST_PLAN.md 20.1, retargeted from springs to wells). Then put those numbers into the sim and re-run the edge. The sim re-run is not the gate.

(c) Not the first purchase. There is no part number, so a price would be a guess. Do not buy unnamed felt.

(d) Do not tune the walk against the rigid mat and call it felt. The camera track and the charging track need this coupon before a dock rate is quoted.

(e) Depends on someone naming a grade that a page can sell (gap 9). Gaps 3, 4, and 5 wait on the numbers. Gate 0's materials line waits on it.

### 18. The camera can be on without a person being able to tell, and the radios are unmeasured

(a) Gate 6 and gate 7 ask for a cue when the camera is active, no stored face library, and no upload by default. COMPLIANCE_FIRST_PASS.md states why. The software pass is GAP. Nest finding that keeps a face library would fail the gate even if the dock worked. Wi-Fi and Bluetooth latencies are BLOCKER (software/SOFTWARE.md section 11). Nothing in that table was measured on a Pi. The servo bus 3.18 ms is calc only (14 servos, 318 bytes at 1 Mbaud) and is not a Pi measurement. USB round trip is BLOCKER.

(b) Full robot test for the cue, with a reviewer able to see that the camera is on. Bench measurement on the Pi for the bus times. Certification is the radio check in gap 14, which is separate from privacy.

(c) No parts beyond the board in gap 10.

(d) Do not add a face library. A one-line cue design can be written by the owner-setup track. Do not invent a latency. Leave unpublished times as BLOCKER.

(e) Depends on gap 10 for any Pi measurement, and on gap 3 so the cue wraps the real finder, not a stand-in.

### 19. Limits, cables, and calibration are not one measured duck

(a) Sit stops are 3 degrees inside the CAD contacts (CAD check only, software/servo_limits.json). The sim models used by older get-up runs are wider than the printed parts. Knee and ankle leads are short of the slack rule (CAD check only, twin/sit/SIT.md). Insert time is BLOCKER. A walking voltage log on the real bus has not been run. IMU sign, foot switches, and the battery cutoff exist as scripts. They have not been run on the parts (TEST_PLAN.md 8 to 12).

(b) Bench measurement: TEST_PLAN.md 1, 8, 9, 10, 11, and 19.1. CAD check only can regenerate one limits table now. It does not pass gate 2.

(c) The full harness is the later order, not the first purchase. The one servo supports 19.1 for a single joint only.

(d) Generate the limits from the CAD contacts and stop quoting results that use the wider ranges. Do not lengthen cables in a file and call the test fit closed.

(e) Depends on gap 2 if the nest moves a cable, and on gap 1 for the first joint. Gate 2 is this list plus the power parts.

### 20. Cliff, touch, and hearing have seats and no behavior

(a) Seats are in the CAD (CAD check only, twin/freeze/FREEZE.md). There is no closed-loop twin of a person, a cliff, or a sound. The VL53L4CD sheet was not opened (BLOCKER, PARTS_AUDIT.md). Touch capacitance and the speaker corner are calc only. Cliff distance in sim is not that sensor.

(b) Bench measurement: the cone on the real floor (TEST_PLAN.md 18), a touch that a person can feel, and a recording of the mics with the fans and the servos running (TEST_PLAN.md 17). A sim that includes the sensor model can come first. It is not the gate.

(c) The boards are on the full bill (cliff line $14.95, cited, BOM.md as named in STATE.md). They are not the first purchase. A cliff test without a walking duck does not prove the spot on the floor.

(d) Do not count the seat checks as behavior. Opening the VL53L4CD sheet is research and would clear a BLOCKER in the freeze row. It is not a substitute for the floor test.

(e) Depends on the head geometry staying put (gap 10 if the board moves the head). Gate 7's home use is safer with a cliff that matches the floor. It is not a substitute for get-up.

### 21. The eye lamp is not a part

(a) D57 keeps one dim warm white bead per eye. Two sheets that were opened do not close line E3 (TWIN_CHECKLIST.md). Fit in the 8.0 mm hole is BLOCKER. There is no candela and no beam. Colour eyes stay off (D57).

(b) A cited part that fits the hole and lights from the GPIO, then a bench photo at that GPIO. Not a certification.

(c) Not the first purchase. No part number, so no price.

(d) Do not add colour eyes. Leave E3 as a named gap until a sheet fits.

(e) Depends on nothing in the walk. Gate 1 and the owner's cue for "the eyes are on" wait on it. It does not block gap 1.

### 22. A second builder has manuals and no passing duck to copy

(a) The owner's manual and the build guide exist and say the duck has not been built (docs/OWNERS_MANUAL.md). The fastener schedule and BUILD_ORDER.md cover the walking duck, not nest v2 (TWIN_CHECKLIST.md). A heat band for a second unit is not written, because the first unit has no passing log. The bill for the second unit has to be the final bill (gap 9).

(b) Full robot test of a second unit, built by someone who did not design it, against the same gates. The band for the heat log has to be written before that build.

(c) The second unit is a later order of the final bill. It is not the first purchase.

(d) Keep the manuals honest. When gap 2 lands, add the nest steps to the existing build order. Do not write a second assembly guide.

(e) Depends on gates 2 through 7 on the first unit. This is gate 8.

### 23. A fair price is not a number we can charge

(a) The parts sum that leaves tools and full spools out is $1,000.19 (calc only, ORDER.md). Shipping and tax are not in it. Nest grams are not sliced, so filament for the nest is BLOCKER. Labor, yield, a failed print, the certification in gap 14, and a margin are not in any file. A sale price was not chosen. Calling $1,000.19 the price of the product would be wrong. It is a parts rollup.

(b) After gate 6, a cited price that includes the parts, the one-time tools spread over a stated count of ducks, and the costs above. Until then the fair-price claim is BLOCKER.

(c) No purchase. This row is a sum, not a cart.

(d) Do not publish a retail price. The order file already separates buy-today from per-duck parts. Leave the missing lines as BLOCKER rather than filling them with a guess.

(e) Depends on gap 9, gap 14, and gap 12. A low parts sum is not a fair price if the duck does not do the job, or if it cannot be sold.

### 24. The walk code has no license file we can point a buyer at

(a) The Runtime and the Playground, at the pins this lab uses, have no LICENSE file (cited, software/companion/USEFULNESS.md and GAPS.md B12). D6 keeps them unmodified and not republished. The dock port that is ours names Apache-2.0 (software/dock/THIRD_PARTY.md). A product someone else builds (gate 8) and a product we sell (gate 6) both need a reading of what those missing files allow. No message has been sent upstream (GAPS.md).

(b) A cited license file at the pin, or a written grant. That is not a bench test. It is a gate 8 and gate 6 document.

(c) No parts.

(d) Do not add a LICENSE file to someone else's pin. Do not republish the Runtime. Record the gap, which GAPS.md B12 already does.

(e) Depends on nothing mechanical. It blocks a clean sale and a second builder who is not the lab. It does not block gap 1.

### 25. The twin can print a confident table that is the wrong duck

(a) This is how earlier clocks went wrong: a thermal step that skipped bins, a fall time stored as a list, a mass edit that never reached the file the simulator loaded, and a walk that logged the stock policy because the path was frozen before run D was selected (redteam/VERDICT_2026-11-13.md, twin/out/REPORT.md). The stock-policy clocks from that mistake are superseded. They are not deleted. Nest scripts that toggle floor contact at run time have no effect in MuJoCo 3.17, and the numbers that touches are BLOCKER (twin/dock/nest/HANDOVER.md). The one-command rerun is the current walk. It is still sim pass only.

(b) Sim, with the policy file name and a hash in the report, which the current report does. A bench log (gap 1) is the check that the model is the hardware. A sim pass does not close that.

(c) No parts.

(d) Any new sim that quotes a dock rate or a heat clock names the policy hash, the contact model, and the step size. Do not re-quote superseded clocks. Do not edit D61 to "fix" an old sentence. A later decision already records the nest (D62) and the walk (the checklist names D66 for run D).

(e) Depends on nothing. Every other sim gap depends on this habit. Gate 0's "one twin" fails if two commands load two ducks.

### 26. The printer and the hot process are unknown

(a) The package wants a bed of at least 220 mm by 220 mm (START_HERE.md). Which printer will run it is not in the files (BLOCKER). PA6-CF wants a hardened nozzle and a chamber. Whether the lab printer has them is BLOCKER (SHIN_EYE.md). Slice times on file are slicer estimates, not printed hours. The full print on a 220 mm bed is 18 jobs and 119.9 h in the older plan (slicer estimate, STATE.md). That estimate is not a printed result, and it is not the nest.

(b) A coupon print, after gate 0 and after Ahmed says yes. The coupon is the exception DEFINITION_OF_DONE.md allows. It is not the product. The first purchase in this file is the servo coupon, not the plastic coupon, because the servo answers more of the open model.

(c) No printer is purchased here. No filament is purchased here.

(d) Leave the slicer numbers labeled as estimates. Do not start S1 from this roadmap.

(e) Depends on gate 0 for a full print, and on gap 7 before the shin sheets change material. Coupons that gate 0 names can be asked for earlier. This servo coupon is the one this roadmap asks for first.

### 27. Old sentences still describe a duck we are not building

(a) D61 is kept as written. It still says the straight crossing has no result, quotes 80 of 80, and says there is no CAD. Later sims contradicted the straight crossing (HANDOVER.md). D62 is the nest we mean. TEST_PLAN.md section 20 still tells the builder to land four spring pins. The sit section still says charging is section 20 through those pins. A reader who stops at D61 or at section 20 will build the superseded contact. STATE.md and START_HERE.md still lead with the 2S, 7.2 V, Pi Zero story in their older paragraphs. Later paragraphs and the checklist are the current duck. The contradiction is the gap.

(b) A documentation pass that points, and does not rewrite a decision. Proof is a person who was not in the room building from the manuals and landing on nest v2, the 12 V servo, and the 3S pack. That is gate 8, and it is not met by this file.

(c) No parts.

(d) This roadmap is the pointer. GAPS.md section D points here. Do not edit D61. Do not silent-edit TEST_PLAN.md in a drive-by. The owner of that file should add a dated note that section 20's springs are superseded by D62, when that owner is free.

(e) Depends on nothing. It blocks every later builder. It does not block the servo measurement.

## What can be done now, with no parts

These do not pass a gate. They stop the next person quoting the wrong duck.

1. Score the run D policy on the two 1 mm steps and on one soft contact. Publish falls, sits, and the policy hash (gap 5).
2. List every print, netlist, viewer, and bill line that is not nest v2 plus the 3S rail (gap 2). Do not install them in this pass if the charger seat is still moving.
3. One limits table generated from the CAD contacts, and a list of sim results that still use the wider ranges (gap 19).
4. Open the VL53L4CD sheet and attach the cite to the freeze row (gap 20). That is research.
5. Keep heat clocks paired with the current that produced them (gap 6).
6. Leave face storage out (gap 18).

Do not start a paid training run. Do not print. Do not order the full bill.

## Minimal first purchase

This is the smallest set that can run the rank 1 test. It is a list, not an order. Nothing was added to a cart. Shipping and tax are not included, the same rule as the bill. Stock was not reopened on 2026-11-24, so "in stock today" is BLOCKER. The prices are the cited prices from the dates below.

| Line | Part | Qty | Price | Cite |
|---|---|---|---|---|
| 1 | Waveshare ST-3215-C018, SKU 22414, the 12 V servo | 1 | $21.99 | Single-unit price, Waveshare page, read 2026-11-12, problems/NEST3.md. Four or more are $20.63 on that same page. This buy is one |
| 2 | Waveshare Bus Servo Adapter (A), SKU 25514 | 1 | $4.99 | BOM.md line 2 |
| 3 | SparkFun digital multimeter, TOL-12966 | 1 | $21.50 | BOM.md TE1 budget option, page read 2026-11-01. 10 A current range. No accuracy figure on that page |
| 4 | Siglent SPD1168X bench supply, 0 to 16 V, 0 to 8 A, current limit | 1 | $305.00 | BOM.md TE2, page read 2026-11-01, in stock on that date |

Total: $21.99 + $4.99 + $21.50 + $305.00 = $353.48 (calc only).

If a current-limited supply that covers 0 to 15 V and at least 3 A is already on the bench, do not buy line 4. The remaining total is $48.48 (calc only). TEST_PLAN.md forbids first power from an unlimited supply. A USB-C phone brick is not that supply. The 65 W brick on the tool list is $18.89 (cited, BOM.md T6, read 2026-11-01) and is a fixed-profile charger for a soldering iron, not a current-limited bench supply. It is not a substitute for line 4.

What this set can prove: one servo answers on the bus (TEST_PLAN.md 6), stall and no-load behavior, cold resistance against the 3.753 ohm assumption, and a temperature log near the knee current (TEST_PLAN.md 7, at 12.0 V). Those replace the clocks in gaps 1 and 6.

What this set cannot prove: a walk, a dock, a charge, felt, a pack, a day at home, a radio check, or a second duck. The SparkFun meter is not a four-wire milliohm meter. It does not close the 0.15 ohm contact test.

Left out on purpose:

- Electronic load, Siglent SDL1020X-E, $574.00 (cited, BOM.md TE4, read 2026-11-01). The stalled servo is the load for this test.
- Klein MM420, $69.97 (cited, BOM.md TE1, read 2026-11-01). Better accuracy. Not required to see a few ohms and a few amps.
- Calipers, $83.95 (cited, BOM.md TE3, read 2026-11-01). Coupons of plastic, not this servo.
- TDK-Lambda regulator, $86.34 (cited, gap 16). Second electrical buy.
- Three P45B cells, $26.97 for three at $8.99 (cited and calc only, gap 13). No weld, so not a pack.
- Pi 5, 2 GB, $77.50 (cited, gap 10). No seat yet.
- The full test-equipment set TE1 to TE4 is $1,032.92 (calc only, BOM.md). It answers later rows. It is not the first buy.
- The older test-order total of $228.49 (calc only, BOM.md) buys toward a full build. It is not this coupon.

## Dependency order

1. Ahmed says yes or no to the four-line coupon. Until yes, no purchase.
2. The servo log lands in a new history file. The thermal twin and the stall model are updated from that log, or the log shows the model is the wrong one.
3. In parallel, and with no parts: the run D edge score, the one-duck diff, and the limits table.
4. The charging track seats the board. The camera track scores frames. The seat track finishes the Pi 5 2 GB geometry. The setup track finishes install and update. This roadmap does not do those four.
5. Felt grade, well ohms, and the mat-edge re-sim (gaps 17 and 5).
6. Gate 0's file merge, then the one-click bill with live pages.
7. Coupon prints the gate 0 rows name, then the full print, only after gate 0.
8. Bench gates 1 and 2, then the tethered mat, then gate 3 on the real camera.
9. Charge safety (gate 5), wear (gate 4), then days at home (gate 7).
10. Certification (gate 6) and a price (gap 23) before any sale.
11. A second person builds a second duck (gate 8).

## Parallel tracks, not duplicated here

- Pi 5 2 GB board seat: gap 10.
- Nest charging electronics: gap 4, and the charger half of gap 2.
- Camera-only nest docking: gap 3.
- Owner setup and updates: gap 11, and the cue in gap 18.

## Sources

DEFINITION_OF_DONE.md, TWIN_CHECKLIST.md, GAPS.md, STATE.md, TEST_PLAN.md, VERIFICATION.md, HARDWARE_AUDIT.md as cited from STATE.md, PARTS_AUDIT.md, bom/order/ORDER.md, BOM.md for prices only, twin/dock/nest/HANDOVER.md, twin/out/REPORT.md, redteam/VERDICT_2026-11-13.md, problems/PROBLEMS.md, problems/NEST3.md, software/pi_fit/BOARDS.md, software/companion/USEFULNESS.md, software/autonomy/AUTONOMY.md, software/SOFTWARE.md, compliance/COMPLIANCE.md, compliance/FCC_COVERED_ROBOT.md, docs/OWNERS_MANUAL.md.
