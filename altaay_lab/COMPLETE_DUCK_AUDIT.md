# Complete duck audit

Written 2026-11-11 10:24 PM ET. Audit and plan only. This file reads the repo. It does not install the nest, does not edit twin/dock/nest/, and does not edit STATE.md or DECISIONS.md.

Labels: sim pass only, calc only, CAD check only, a cited source, or BLOCKER. A sim in the files below is not a result on hardware.

## Note 2026-11-12 4:23 AM ET

The sections below were written on 2026-11-11 and are left as written. These later pull requests have since covered part of the gaps. None of them installs the nest into print/, the netlist, or the bill.

- PR 36, parts. PARTS_AUDIT.md and PROPOSED_BOM_CHANGES.md name the probe as QA Technology 100-PRP4030S, tip 30, 1.40 mm, from the opened catalog. The one-click order is still not ready. Felt, the gold cloth, the weld, and several other lines still have no orderable part number.
- PR 37, software and communications. software/SOFTWARE.md lists the programs and a link table for the servo bus, I2C, I2S, CSI, USB, Wi-Fi, and Bluetooth. Line E3 stays NOT ORDERABLE. twin/thermal/EFFICIENCY.md records the efficiency figures already in the sims. software/knee_heat.py warns and stops the walk on two readings at or above 55 C, and turns torque off when idle or sitting (simulated tests only).
- PR 38, camera. twin/camera/CAMERA_TWIN.md and twin/complete3d/camera_cone.py place the module brief's field on the measured head seat (CAD check only). TEST_PLAN.md 20.9 has not been run.
- PR 39, contact twin. twin/contact/CONTACT_TWIN.md. Pin force and the cloth loop are calc only. Felt grade, dent depth, cloth life, and sole friction stay BLOCKER.
- PR 40, charger board. altaay_lab/circuitry/CHARGER_BOARD.md and charger_board.yaml are a schematic from the opened MCP73213 sheet. The robot netlist and the bill are unchanged.
- PR 41, flush contacts. Still open. The direction on that pull request is five flush gold wells in the seat. That study is not on altaay-lab.
- PR 42, nest sim. twin/dock/nest/sim/v3/NEST_SIM_V3.md. A mixed walk-in on two 1 mm steps, sim pass only. The sun distance in the CAD stays 190 mm.
- PR 43, structure. twin/structure/TOPOLOGY.md. In that FEA pass, roll_to_pitch meets the walking margin of 2 and the shin eye stays under 2 (FEA pass only). Soft falls stay under 1.2 on several parts. print/ is unchanged, and the interior carve did not save print mass.

## What the files show

The walking duck already has one installed model. The print set, the cable routes, the fastener schedule, the netlist, and the viewer describe that duck, and the verify scripts check those files against each other. The nest (mat, gold disc, pale gold ring, spring pins, charger in the body) is drawn under twin/dock/nest/ and is not in that model. twin/dock/nest/cad/NEST_CAD.md says the CAD is not installed in print/, the URDF, the netlist, the bill, or the viewer. That part of the picture is right.

The nest install is the missing piece of the one model. It is not the last open piece of a one-to-one twin. TWIN_CHECKLIST.md already records open rows for structure, heat, the sheet-stall walk, the bill, the camera, the felt, the pin contact, get-up, and the knee policy. DEFINITION_OF_DONE.md gate 0 also records no topology study. Those gaps stay open after the nest is drawn into the model. This audit points at the files that already hold the work, and it marks only the holes.

Another agent is writing twin/dock/nest/. This plan waits for that work to land on altaay-lab before step 1. This run does not start step 1. Step 1 changes the print set, the netlist, and the bill. It is not a docs-only edit, and it must not touch the nest folder while that agent is writing it.

## Work already in the repo (do not build it again)

The one model of the walking duck is the set of files below. Later steps extend these files and the scripts that generate or check them. They do not add a second duck, a second cable list, a second screw list, or a second viewer.

| Already done | Where | What a new file would duplicate |
|---|---|---|
| Every printed part, with material, walls, infill, rings, print-up, grams, and hours | print/parts.csv, print/PRINT_PLAN.md, print/SLICE_SUMMARY.md, print/slice.py | A new print plan or a new slicer config |
| Light profile that removes mass and keeps the hole rules | print/MASS_STUDY.md, DECISIONS.md D22 | Another mass study |
| Coupon and full-print steps | print/PRINT_PLAN.md | A second coupon plan |
| Every purchase line | BOM.md, bom.json, audit/bom_md_to_json.py | A second bill |
| One row per part in the robot, tied to a purchase line | BOM_FULL.md, viewer/bom_full.py, viewer/make_viewer_data.py | A hand-written parts list |
| Orderability of each line | PARTS_AUDIT.md | A second parts audit |
| Every cable id, route, cut length, gauge, colour, connector, and crimp | CABLE_MAP.md, cables3d/CABLES_3D.md, cables3d/cables3d.json, HARNESS_BUILD.md | A second cable map |
| Every pin and wire | wiring/netlist.yaml (rev 2026-11-06) | A second netlist |
| Current wiring sheets, generated from the netlist | wiring/sheets/WIRING_SHEETS.md, wiring/sheets/make_sheets.py (sheets 1 to 6), wiring/sheets/make_dock_sheet.py (sheet 7, the earlier dock) | Hand-drawn sheets, or a new drawing set |
| Power tree as wired, ankle feeds, current budget | POWER.md, sim/POWER_PATH_SIM.md, sim/POWER_FIX.md, sim/CURRENT_BUDGET.md | A second power sim |
| Electrical twin, including bus timing and the shove current | twin/electrical/ELECTRICAL_TWIN.md | A second electrical twin |
| Servo, pack, and walk in one loop | twin/electromech/ELECTROMECH_TWIN.md | A second electromechanical loop |
| Heat, including the later P45B sit with the charger watts | twin/thermal/THERMAL_TWIN.md, twin/thermal/gate_p45b.py | A second thermal model |
| Strength, falls, and print-setting proposals P1 to P8 | twin/structure/STRUCTURE_TWIN.md, twin/structure/st_slice_proposals.py | A second FEA stack. Those proposals are not a topology study |
| Screws, inserts, washers, reach, hole rules D39 and D42 | fasteners/FASTENERS.md, fasteners/fasteners.json, MOUNTING.md, twin/screws/SCREWS_TWIN.md, twin/holes/HOLES_TWIN.md, twin/assembly/BUILD_ORDER.md | A second fastener schedule or a second build order |
| Viewer of printed parts, bought parts, cables, and screws | viewer/, twin/complete3d/COMPLETE3D.md | A second viewer. viewer/MISSING_3D.md is the older gap list for that viewer |
| Old dock scene in the viewer | viewer/dock_scene.py (reads twin/dock/, the wall and paddle dock) | A third dock viewer. Extend this script for the nest after step 1 |
| Sit, stops, torque-off rest, get-up through the sit | twin/sit/SIT.md, twin/sit/getup/, software/servo_limits.json, software/CALIBRATION.md | A second sit |
| STS3250 knee study and the retrain preset | twin/knee/KNEE_TWIN.md | A second knee model |
| Seats for mics, speaker, touch, cliff cone, ears | twin/freeze/FREEZE.md, twin/companion/COMPANION.md | A second head design. D57 already says no colour eyes |
| Pack bay and charge notes | twin/battery/ | A second bay |
| Nest concept, sims, and CAD archive | twin/dock/nest/ (read only here) | A second nest design. Step 1 consumes this archive. It does not redraw it |
| Walk code, guards, Pi setup | software/SOFTWARE.md, software/PI_SETUP.md, bench/ | A second runtime. D6 keeps the Runtime unmodified |
| Old dock behaviour port | software/dock/ | A camera nest stack copied from that port. The port targets the earlier dock |
| Checks that need no robot | verify/, VERIFICATION.md, TEST_PLAN.md | A second verify suite. New checks extend verify/ |

V1_PLAN.md tracks 3, 4, 5, 6, and 7 are the named leftovers (real code in the loop, joint motion, vibration, standing gains, electrical leftovers). Track 2e was still marked running in that file. This audit does not restart those tracks. Step 6 and step 8 below are the parts of them that gate 0 still lacks.

## Wiring

Exists. wiring/netlist.yaml is the source for every pin and conductor of the walking duck: gauge, colour, cut length, ends (connector and crimp), net, and the currents the power sims wrote. CABLE_MAP.md, cables3d/, and HARNESS_BUILD.md are the route, the 3D path, and the build sheet. The sheets are generated. Lengths that miss the slack rule are already marked test fit in the sit cable pass (twin/sit/SIT.md). Kit-cable gauge is unpublished (netlist meta, BLOCKER). Molex drawings were not opened (PARTS_AUDIT.md, BLOCKER).

Missing. The nest pin leads NP1, NP2, NP3, NM1, NM2, and NM3 are dimensioned in twin/dock/nest/cad/NEST_CAD.md (calc only, CAD check only) and are not in the netlist. The two-net change is not in the netlist. The charger board has no wires because it has no seat.

One-to-one check. The existing chain: netlist, then cables3d check, then verify C3 and the electrical rule check, then TEST_PLAN.md section 1 on a built harness. A cable is one-to-one when the cut length, gauge, colour, crimp, and both pins match the netlist and the harness reaches with the slack rule.

Effort. Step 1, one writer, extending the netlist and the cable scripts. No new cable map.

Blockers. Nest folder still being written. Pin tip not chosen, so the socket end is not a real part. Charger board undesigned. Look of the CAD not approved (twin/dock/nest/HANDOVER.md).

## Every part

Exists. BOM.md is the purchase list. BOM_FULL.md is one row per installed item. PARTS_AUDIT.md is the line-by-line order check. Fasteners, mounts, and the viewer cover the walking duck's solids.

Missing. PARTS_AUDIT.md says a one-click of today's bill misses the nest and still buys the old chest pad (line DK1). The spring pin has no complete part number. The tip drawn at about 2.3 mm is not on the opened QA Technology 100-40 catalog (round tips on that page are 0.91 mm and 1.40 mm). Felt, gold cloth, pale gold cloth, foil, rim foam, and the gate board have no part numbers. Line 7 (the weld), line 17m, line 22c, line 11, line 14, and lines E3, E4, and E5 have no manufacturer part number. The Pi and the P45B were out of stock at the sellers that page opened. Almost every other line is STOCK NOT REOPENED.

One-to-one check. PARTS_AUDIT.md already states it: exact manufacturer part number, quantity, distributor, and a live page, and every twin solid is one of those lines. verify/c1_bom_coverage.py is the script to extend, not replace.

Effort. Step 7, one writer, after the nest lines exist. No second bill.

Blockers. Live stock was not reopened this session. Tip code, cloth, felt, weld, and charger board are BLOCKER in PARTS_AUDIT.md. DK1 stays until a decision says otherwise. This plan does not edit DECISIONS.md.

## Topology

Exists. twin/structure/STRUCTURE_TWIN.md is an FEA of the leg and neck stages on sim loads (sim pass only, FEA pass only), plus proposals P1 to P8 that change walls and print settings. st_slice_proposals.py reports grams and hours for those proposals. D38 put roll_to_pitch back to 3 walls. That is extra material at a weak section, which is the opposite of deleting unloaded material.

Missing. DEFINITION_OF_DONE.md states the gap in one sentence: no topology study is in the repo. V1_PLAN.md asks for an optimized design. That sentence is not a study. No file removes material that carries no load and then re-runs the structure twin.

One-to-one check. After a topology pass, the same structure twin is re-run on the same loads, including the nest mass once step 1 has landed it, and every part still meets the margins that twin already uses (2 walking, 1.2 in a fall). The print files and the mass budget are regenerated from the existing slice script.

Effort. Step 8, one writer, extending st_slice_proposals.py and the structure report. No new solver.

Blockers. D26 is open. The current FEA is under the walking margin on roll_to_pitch and the knee sheet eye (TWIN_CHECKLIST.md structure row). Nest mass is not in that model. Contact stiffness and hot PLA are already marked as guesses in that row.

## Efficiency

Exists. The power path sim and the current budget are the electrical energy of the walk (sim pass only). The P45B electromechanical loop reports pack current and run time (sim pass only, and the sheet-stall walk falls). D22 is the print-mass cut that kept the hole rules. The thermal model uses a BEC efficiency of 0.85 (TWIN_CHECKLIST.md thermal row).

Missing. Castle publishes no CC BEC Pro efficiency (that row's guess). No file sets a cost-of-transport target or a gait that was trained to use less energy. Softer standing gains are named as an untried lever in V1_PLAN.md track 6. The temperature guard already drops to low gains before torque-off (software/SOFTWARE.md section 5). That is a runtime behaviour, not a trained efficiency policy.

One-to-one check. A bench measurement of BEC input and output power replaces 0.85. The walking voltage and current log (TEST_PLAN.md section 9) is the check on the duck. Until that log exists, efficiency numbers stay sim pass only or calc only.

Effort. Step 9, one writer, a short section in the thermal twin that lists the efficiencies already in use and which ones are unpublished. No new walk.

Blockers. BEC efficiency unpublished. Sheet-stall walk falls, so an efficiency number from the trained-actuator session is not the servo on the bill.

## 3D printing and colours

Exists. print/parts.csv names every STL the slicer uses, with material (PLA or TPU), profile, overrides, and the reason. PRINT_PLAN.md and SLICE_SUMMARY.md hold the PrusaSlicer 2.7.2 grams and hours (slicer estimates, not printed results). BOM lines 27 and 28 are black PLA and black TPU. The PLA line says any in-stock colour works. Wire colours are per conductor in the netlist. The nest gold and pale gold are cloth colours in the nest CAD, with no part number.

Missing. There is no table that assigns a filament colour to each printed part beyond "black, and any in-stock colour works." The nest parts are not in parts.csv. Eye colour is the dim warm white bead (D57), not a filament colour.

One-to-one check. After step 1, slice.py is run on the same parts.csv, and the grams and hours in PRINT_PLAN.md are that run. Colour is one-to-one when each part's row names the spool on the bill and a photo of the printed part matches it. Nothing is printed until the twin gate and an OK, which is already the lab rule.

Effort. The print rows of the nest are part of step 1. A colour column on parts.csv is a few lines in that same step if the spool stays the black lines already on the bill. No new slicer.

Blockers. The real printer is unknown (the plan says a bed of at least 220 by 220 mm). Nest STL files are in the archive and are not the print set. Look not approved.

## Lights

Exists. Eyes and the projector are GPIO loads in the netlist, with 100 ohm resistors (DECISIONS.md D13: about 3 mA at the eyes, cited there). SOFTWARE.md section 2 matches the Runtime pins. D57 keeps one dim warm white bead per eye. The bulbs, eye discs, and reflector are on the bill (lines with no manufacturer part number: E3, E4, E5).

Missing. No lamp datasheet, no beam, no driver beyond the resistor, no optical model. Colour eyes were considered and deferred (D57).

One-to-one check. The part on E3 matches the bead in the eye, the netlist resistor, and a bench photo at the GPIO. TEST_PLAN can use the existing eye GPIO. A new driver is out of scope while D57 stands.

Effort. Step 3, one writer, extending PARTS_AUDIT.md line E3 and the eye paragraph in software/SOFTWARE.md. No new lamp circuit.

Blockers. E3, E4, and E5 are NOT ORDERABLE (PARTS_AUDIT.md).

## Field of view

Exists. The cliff sensor cone is in twin/freeze/FREEZE.md: beam 52 degrees down, an 18 degree window, floor spot 93 to 178 mm ahead of the toe, and no foot in that cone on the stock walk (CAD check only, sim pass only). The head camera seat is measured in twin/complete3d/COMPLETE3D.md (CAD check only). The bill names Camera Module 3, standard, with the IR cut.

Missing. No file places a camera cone on that seat. The nest sims use true pose plus noise (sim pass only). What the lens sees of the mat, the floor, or a person is unwritten.

Cited source, not a duck result. The Camera Module 3 product brief gives the standard variant 75 degrees diagonal, 66 degrees horizontal, and 41 degrees vertical (https://pip-assets.raspberrypi.com/categories/786-raspberry-pi-camera-module-3/documents/RP-008151-DS-1-camera-module-3-product-brief.pdf, opened 2026-11-11). The wide variant on the same page is 120, 102, and 67 degrees. The bill's standard module is the first set. Those angles are not yet a cone on the head.

One-to-one check. Put that cone on the existing camera seat, say which nest features and which floor region fall inside it at the approach distances TEST_PLAN.md 20.9 already names, then compare with frames from the real camera. Until the frames exist, the cone is CAD check only.

Effort. Step 2, one writer, extending the camera seat script in twin/complete3d/. No new camera twin folder.

Blockers. Head pitch during the approach is not a recorded pose for this cone. Room light and exposure are unmeasured (TWIN_CHECKLIST.md camera row).

## Communications

Exists. Servo bus 1 Mbaud, 8N1, half duplex, /dev/ttyACM0 (software/SOFTWARE.md section 2, cited from the Runtime). The bus is the USB adapter. The Pi UART is unused: pins 8 and 10 (software/PI_SETUP.md). Byte times for the 50 Hz loop are in section 6 of that file (calc only, simulated bus). I2C stays at 100 kHz (software/PI_SETUP.md). I2S, CSI, and USB are domains in the netlist. SPI is not in the walking netlist. D57 leaves GPIO10 free for a deferred colour eye. The Pi product brief lists 2.4 GHz Wi-Fi and Bluetooth 4.2 (PARTS_AUDIT.md). D46 says those radios are not used for docking. The companion notes describe a home server with a 300 ms command lifetime (twin/companion/COMPANION.md, calc only).

Missing. No single table. Servo turnaround is unpublished (twin/electrical/ELECTRICAL_TWIN.md, BLOCKER). USB round trip and Pi CPU time are UNVERIFIED (SOFTWARE.md section 8). Wi-Fi and Bluetooth latency are unmeasured.

One-to-one check. One table in SOFTWARE.md, each bus pointing at the netlist pins and at a number that is either the byte timing (calc only) or a scope or log on the bench. A bus with no number stays BLOCKER.

Effort. Step 4, one writer, that table only. No new protocol code.

Blockers. Turnaround time, USB latency, and radio latency.

## Circuitry

Exists. The netlist is the schematic source: cells, BMS, fuse, switch, BEC, 5 V regulator, servo power, and the logic rails. The current drawings are wiring/sheets/, regenerated from that netlist by make_sheets.py. WIRING.md says the older odm_v2 schematic, harness, and pictorial files, and make_schematic.py, make_harness.py, make_wiring.py, and make_pictorial.py, are kept and are not the drawings to build from. WIRING.md section 1 still names P30B cells in a holder. The netlist rev note names the P45B pack. The electrical twin checked the netlist tree for trips, regeneration, and the far-servo ground (sim pass only, calc only) and did not add a bulk capacitor for the walking duck. There is no separate decoupling map for the Pi, the IMU, the touch boards, the BEC, or the switch. Protection and the software cut are D8, D16, and the guards in SOFTWARE.md.

Missing. The in-duck charger, the two nest nets, the safety gate, and the decoupling for that charger. The MCP73213 datasheet was not opened (BLOCKER). Old dock capacitors live on twin/dock/DOCK_BOM_FULL.md and belong to the earlier dock.

One-to-one check. The charger sheet is opened, the nets are added to wiring/netlist.yaml, the existing rule check and the electrical twin are re-run, and the sheet's capacitors are the ones on the board. A hand sketch that the scripts do not read is not the schematic.

Effort. Step 5, one writer, after step 1, extending twin/electrical and the netlist. No second schematic tool.

Blockers. Datasheet not opened. Charger has no seat (NEST_CAD.md). Gate board not designed.

## Software

Exists. software/SOFTWARE.md is the map. On the Pi: the Runtime walk loop at 50 Hz, the ONNX policy, the IMU thread, the eye blink, and the lab guards. The temperature guard warns at the servo limit minus 15 C, which is 55 C when the limit is the factory 70 C, and it stops at the limit minus 8 C, then turns torque off (SOFTWARE.md section 5, simulated bus). The sit is a different torque-off: the duck rests on the printed stops (D59). Limits are software/servo_limits.json. Boot and install are software/PI_SETUP.md. The old dock port is software/dock/. Bench tests of these hooks passed on a simulated bus (SOFTWARE.md section 7).

Missing. Nest vision. A charge program for the charger inside the body. An update program after the install apt commands. V1 track 3 (the Runtime run against the twin) is not started. Ear PWM still needs a Runtime file change that D6 has not allowed (D53).

One-to-one check. The same files that will run on the Pi run against the twin, including a camera frame in and a dock pose out, a charge state, the 55 C warn, and the torque-off sit. Simulated-bus tests stay labeled that way.

Effort. Step 6, one writer, extending SOFTWARE.md so the missing programs are a list with the file that will hold each one. Vision code waits until step 2 has a cone and a scored task. No fork of the Runtime.

Blockers. Camera model missing. Charger circuit missing. D6 limits Runtime edits.

## Training

Exists. Presets are described for a walk at the build mass and for STS3250 knees (run2_sts3250) in the shared lab gym (overlay gym/overlays/duck). A CPU smoke of that knee preset passed: 480 env steps, 5 evals, 612 s, 8 envs (twin/knee/KNEE_TWIN.md, sim pass only). That smoke is not a trained policy. Get-up through the sit was searched, not trained: 248 of 296 cases raise, and 48 down-ramp front rests still fail (sim pass only, twin/sit/getup/VIA_SIT_EVAL.md).

Missing. No GPU run has been executed. The stock policy falls on the STS3250 model in sim (knee twin, sim pass only). The nest sims ask for toe lift over a 2 mm edge and a right side-step (sim pass only). Standing gains softer than the trained walk are the untried track 6 lever, and the knee file already says the knee P on the real servo is lower than the one P the Runtime writes to every leg (calc only, BLOCKER until a bench BAM test).

One-to-one check. An eval in the shared lab gym (overlay gym/overlays/duck) on the installed model: the knees that will be bought, the mass the bill builds, a 2 mm edge, a right side-step, and the 48 get-up rests. A passing eval is sim pass only until the duck walks.

Effort. Step 10, one writer, and only after an OK. The writer uses the presets already named. This run starts no GPU.

Blockers. No RunPod key in the environment that wrote the earlier notes. STS3250 datasheet not opened. Bench BAM test not run. Nest edge training needs an OK of its own. GPU hours below are a cited range, not a lab log.

## Ordered build plan

One source of truth stays the files in the table above. Each step has one writer. Each step extends those files. No step creates a parallel model. Step 1 waits until the agent now writing twin/dock/nest/ has finished and that work is on altaay-lab. This run stops at the plan.

1. Nest into the installed model. One writer. After the nest agent has merged, and after the look is approved and the pin tip code is chosen from the opened catalog. Read twin/dock/nest/ and do not edit it. Land the mat, the gold disc, the pale gold ring, the rim, the pin carriers, and the changed seat, bumper, and body floor into print/parts.csv and the print STL set. Add the pin leads already dimensioned in NEST_CAD.md to wiring/netlist.yaml, then regenerate the sheets with wiring/sheets/make_sheets.py and re-run the cables3d check. Do not regenerate the superseded odm_v2 drawings. The charger-board connection is a BLOCKER row in that netlist until the charger sheet is opened. Add bill lines only when PARTS_AUDIT.md has a real part number. Extend viewer/dock_scene.py and viewer/make_viewer_data.py so the nest draws in the existing viewer. Keep the old dock scene in place. Regenerate BOM_FULL.md with the existing writer script.
2. Camera cone. One writer. Extend twin/complete3d/ camera seat work with the standard-module angles cited above, on the installed head, and write what falls inside the cone. Score it the way TEST_PLAN.md 20.9 is already written.
3. Lights. One writer. Close line E3 with a real part or leave it BLOCKER in PARTS_AUDIT.md. Record D57 in software/SOFTWARE.md as the colour decision. No colour eyes, no new driver.
4. Communications table. One writer. Append one table to software/SOFTWARE.md pointing at the netlist, the 1 Mbaud loop, the 100 kHz I2C, I2S, CSI, USB, and the radios. Unpublished times stay BLOCKER.
5. Charger circuitry. One writer, after step 1. Open the MCP73213 sheet. Add the two nest nets, protection, fusing, and the sheet's decoupling to wiring/netlist.yaml. Re-run audit/erc.py and the electrical twin. If the sheet is still unread, stop.
6. Software list. One writer. Extend software/SOFTWARE.md with every program: boot, walk loop, policy, guards (55 C warn and the torque-off sit), nest vision, charge, updates. Point vision and charge at the files from steps 2 and 5. Do not edit the Runtime.
7. Bill match. One writer, after steps 1 and 3. Extend PARTS_AUDIT.md and verify/c1_bom_coverage.py until every installed solid is one orderable line. Leave DK1 until a decision retires it.
8. Topology. One writer, after step 1 so the nest mass is in the model. Extend twin/structure/st_slice_proposals.py. Re-run the existing structure twin. D26 stays a decision. No new solver.
9. Efficiency note. One writer. A short section in twin/thermal/ that lists BEC efficiency, gait energy, and the D22 mass cut, each pointing at the file that already holds it. Unpublished figures stay BLOCKER. No new walk.
10. Training. One writer, after the OK in the next section. Use the existing presets in the shared lab gym (overlay gym/overlays/duck). Do not write a new trainer.

## Training scope and cost (needs an OK)

No GPU is started from this audit.

Runs the files already ask for:

| Run | What it is | Where it is named | Gate before a GPU |
|---|---|---|---|
| A | Walk at the build mass, small terrain, knee heat | stage 0 notes in STATE.md | The key the earlier note was waiting on. This run was already asked. It has not been executed |
| B | STS3250 knees, with the knee P the knee file calculates, in the same walk | twin/knee/KNEE_TWIN.md preset run2_sts3250 | Bench BAM test (TEST_PLAN.md 15) and an opened STS3250 sheet. The stock policy falls on this model in sim |
| C | Creep, turns that match both ways, a right side-step, and a 2 mm edge | V1_PLAN.md track 10, and twin/dock/nest/sim/v2/NEST_SIM_V2.md | An OK for this spend. The nest sims are sim pass only |
| D | The 48 down-ramp front rests, if they do not fit inside run C | twin/sit/getup/VIA_SIT_EVAL.md, DECISIONS.md D60 | Same OK. Length of a get-up-only run is BLOCKER |

Softer gains are not a fifth full run. The temperature guard already sinks to low gains, and the knee file treats the lower knee P as part of run B. Track 6's standing-gain lever is a runtime check after that policy exists.

Step count, cited. The upstream playground's current listed command is 300,000,000 steps (https://github.com/apirrone/Open_Duck_Playground, the training section, read 2026-11-11). A published timing note for that 150 to 300 million step command says 1.5 to 3 hours on an RTX 4090 (https://note.com/big_buddha0794/n/nccdcb712a715, read 2026-11-11). That note is not a lab log. This repo's only training timing is the CPU smoke above, which is 480 steps and does not scale to a policy.

Hours, if that note holds and runs A, B, and C are each one such command: 4.5 to 9 GPU hours. Run D, if it needs its own command of the same length, adds 1.5 to 3 hours. A shorter get-up run is possible and is BLOCKER until the gym preset says so. Range used here: 4.5 to 12 GPU hours.

Price, cited. RunPod's pricing page, opened 2026-11-11, lists the RTX 4090 at $0.34 per hour on Community Cloud and $0.89 per hour on Secure Cloud (https://www.runpod.io/pricing). Calc only from those rates and the hour range above: 4.5 hours is $1.53 and $4.01, and 12 hours is $4.08 and $10.68. Rough range about $2 to $11. Storage, tax, and a failed restart are outside that page's hourly rate. This needs an OK before any pod is started. The earlier cap written in STATE.md covered the stage 0 ask only, and that run was not executed.

## This run

Step 1 was not started. The nest folder is still being written, and step 1 is an install into the print set, the netlist, and the bill. TWIN_CHECKLIST.md now has rows for lights, field of view, communications, circuitry, software, and training.
