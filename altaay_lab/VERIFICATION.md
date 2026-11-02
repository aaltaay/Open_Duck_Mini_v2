# VERIFICATION: every check that runs without the robot

Generated 2026-11-01 11:09 PM ET by altaay_lab/verify/report.py from one run of `bash altaay_lab/verify/run_all.sh` (results kept outside the repo). Written by agent Q (verification) for Ahmed's Open Duck Mini v2 build. Every simulation result here is sim pass only. Nothing was bought, built or printed; no lab file was edited by these checks (each script that writes files was run on a copy or into the results folder).

## Summary
22 checks: **17 PASS, 5 FAIL, 0 NOT RUN**. 18 FAIL findings and 59 WARN findings in all (below). PASS means no FAIL finding; a PASS row can still carry WARN findings (risks, test fits, notes).

How to run (from the repo root): `bash altaay_lab/verify/run_all.sh` runs everything (this run: 14 minutes of check time on the shared 4-CPU box, sims under nice -n 10); `--quick` skips the MuJoCo, ngspice and CAD sweep runs and reuses earlier results in the same folder. Settings: VERIFY_OUT (results folder outside the repo), ODM_RUNTIME (Open_Duck_Mini_Runtime at 376de65), ODM_PLAYGROUND (Open_Duck_Playground at b9be205), ODM_TEST_PYTHON (a Python with rustypot and pypot for the bench tests). Each check also runs alone: the command is in the matrix.

Run notes:

- Bench test test_rustypot_panic_after_checksum_error_is_caught, 2026-11-01: inside the full suite it passed at about 10:20 PM ET and failed at 10:29 PM and 10:44 PM ET (machine load 7 to 9 on 4 CPUs); run alone it passed 6 of 6 (10:33 PM and in E8). Both failures are the same: after the rustypot panic the pypot fallback reported 'low kp + torque off (attempt 1)' but all 14 fake servos kept torque on and their P gain at 30, so neither sync write landed and nothing read them back.
- Other agents were still writing while these checks ran (BOM.md, HARDWARE_AUDIT.md, DECISIONS.md, cables3d): the full run went from 10:35 to 10:47 PM ET, and the quick checks (E1 to E4, C1 to C6, C9, C10) and E9, C11 were run again from 11:04 to 11:12 PM ET on the files committed by then. The cable routes were still being reworked (the seats moved after the tape fix). The input table at the end gives the time of every file read.

## Main findings

Checks that fail, with their numbers (fixes are in the FAIL section below):

- **E6b** TEST_PLAN.md section 5 hop gate (40 mOhm) is enough for the section 9 ankle gate (power path sim sweep, sim pass only): ankle under 6 V at a nominal pack: 28 mOhm 22%, 23 mOhm 19%, 11 mOhm 10%, 0 mOhm 2%; section 5 passes hops up to 40 mOhm
- **E8** Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests): pytest: 1 failed, 52 passed in 147.05s (0:02:27)
- **C1** Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners): 43 netlist parts map to BOM lines with matching part numbers (13 splices are made); BOM_FULL 188 rows vs sources: 2 FAIL (see list)
- **C3** Every active cable has a 3D route whose worst length plus slack fits its cut, and a service loop at every joint: 45 of 45 active cables routed in 3D (0 runs still straight placeholders); 6 wires too short before slack, 25 with less than 40 mm slack; 42 of 42 joint loops under 3 x OD
- **C9** Docs agree: numbers that appear in several docs are the same everywhere: 11 disagreements (blocker counts 1, test print count 1, blocker status words 5, stale BOM blocker bullets 3, screw count 1); blocker table: 32 rows, 19 cleared or decided

Passing checks that still carry risks to measure on the bench (WARN):

- **E1**: M6 NOT caught: switched pack (8.4 V) on BNO055 VIN (3.3 V, dir pwr_in) (expected ERROR in 'domains'; got {'ERROR': 0, 'WARN': 0, 'INFO': 1})
- **E4**: viewer warning: BOM line 17j (M3x6 button head) has no view mapping (and 2 more)
- **E6**: sim, typical corner, nominal pack: an ankle is under 6.0 V for 21% of the walk; TEST_PLAN.md section 9 passes only under 10% (and 4 more)
- **E7**: left: the inner screw D18 keeps clears roll_to_pitch by only 0.24 mm (worst at -25.0 deg), inside normal print tolerance (and 1 more)
- **C2**: 08-70-1040 insulation range and 3 A rating come from distributor listings read via a search index (Molex sheet not read; uk.rs-online.com and octopart.com are outside this session's network)
- **C4a**: 4 x M2.5x5 DIN 912 A2: fasteners.json names no BOM line, BOM.md line 17k buys it (Need 4, Buy 5) (and 2 more)
- **C4b**: 2 screws still hit with the button head, known and left as a joint range point in D19 (not fixed): F211 M3x6 ISO 7380 A2 button head vs body_middle_bottom at right_hip_yaw -28.3, -1.49 mm, -0.82 mm with the button head; F198 M3x6 ISO 7380 A2 button head vs bod (and 4 more)
- **C7**: kit cable hops over the 26 AWG chassis limit (2.2 A) in the worst 100 ms (means are under it): S2 3.28 A, S3 2.97 A, S4 2.28 A, S7 3.91 A, S8 2.98 A, S9 2.62 A. The kit cable gauge is not published; 26 AWG is the smallest plausible (erc.py KIT_AWG) (and 5 more)
- **C11**: nothing in the Runtime limits hip yaw: the policy bound keeps the walk under the onset, but a manual move, find_soft_offsets.py (Runtime issue 32 moves every joint) or a fall can still reach 21.7 to 30 deg and press the F198/F211 heads into body_middle_bottom

## Matrix

| # | Check | How it runs | Result | Evidence (numbers) | Covers | Does not cover |
|---|---|---|---|---|---|---|
| E1 | Electrical rule check of the netlist (audit/erc.py) plus mutation test | `VERIFY_OUT=<out> python3 altaay_lab/verify/e1_erc.py` | **PASS (0 FAIL, 1 WARN)** | 0 ERROR, 0 WARN on 56 components and 118 wires; committed report and beep list current: True; injected faults caught: 9 of 10 (missed: pack voltage on a pwr_in pin) (details below) | References, pin use, shorts between nets, voltage domains of 'in' and 'bidir' pins, ampacity of wires that carry a current in the netlist, Molex 08-70-1040 crimp gauge, 5264 connector match; committed report is current; 10 injected faults | Wires with no current in the netlist (SP1 to SP3, kit cables: see C7); pwr_in pins in the domain rule (see mutation M6); anything not written in netlist.yaml |
| E2 | BOM.md subtotals, totals and test order total (audit/bom_totals.py on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py` | **PASS** | recompute changes nothing: build $890.19, + expression $972.59, + tools $1220.76, test order $226.46 (details below) | Every section subtotal, the Totals table and the test order total recomputed from the line items; Buy >= Need on every line where both count the same unit | Whether the prices are still current (read 2026-11-01); quantities themselves (C1, C4) |
| E3 | bom.json rebuilt from BOM.md (audit/bom_md_to_json.py on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py` | **PASS** | 78 rows rebuilt, identical to the committed bom.json: True (details below) | bom.json has the same rows and values as BOM.md (57 purchase lines) | BOM.md content itself |
| E4 | Exploded-view data build and its CAD count checks (viewer/make_viewer_data.py) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e4_viewer.py` | **PASS (0 FAIL, 3 WARN)** | found in the CAD: printed parts 52/52, servos 14/14, inserts 58/58, bearings 3/3 (details below) | URDF zero pose with print/ STLs swapped in; printed parts, servos, inserts, bearings found vs expected; STL vs URDF frame check; BOM lines with a view mapping | Fit of parts not in the CAD beyond their boxes; anything the page shows but does not count |
| E5 | Servo current budget from the stock walk (sim/current_budget.py, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e5_current_budget.py` | **PASS** | 7 of 7 cases reproduce CURRENT_BUDGET.md; backlash walk 3.24 A mean, 4.72 A worst 100 ms; worst servo 3.33 A (details below) | 7 MuJoCo cases (stand, walk, turn, side, backlash, rough, pushes) with BEST_WALK_ONNX_2; every number of the CURRENT_BUDGET.md table (falls, mean, 1 s, 100 ms, 20 ms, 2 ms, whole-run max) and the worst single servo | Real servos (issue 48: real tracking differs); the 5 V branch and pack side (hand calculation in the doc) |
| E6 | Power path to every servo, built wiring D15 (sim/power_path_sim.py star, ngspice, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py` | **PASS (0 FAIL, 5 WARN)** | worst ankle 5.04 V at a nominal pack, typical corner (D15: 5.04 V), 3.44 V high-side; ankle under 6 V 21% of the walk (typical) (details below) | 7 star cases (full, nominal, low pack x typical and high-side resistance, fall after a push); documented worst ankle 5.04 V; TEST_PLAN.md section 9 gates on the sim; the same run with 22 AWG power leads as in the netlist | Real hop resistance (TEST_PLAN.md section 5), BEC dropout (section 4), bus capacitance; the 5 V branch in detail |
| E6b | TEST_PLAN.md section 5 hop gate (40 mOhm) is enough for the section 9 ankle gate (power path sim sweep, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py` | **FAIL (1 FAIL, 0 WARN)** | ankle under 6 V at a nominal pack: 28 mOhm 22%, 23 mOhm 19%, 11 mOhm 10%, 0 mOhm 2%; section 5 passes hops up to 40 mOhm (details below) | Star wiring with 22 AWG leads, nominal pack, typical source resistances; hop = kit or made lead conductor + 2 contacts + servo board; ankle time under 6 V and minimum voltage per hop value | Real BEC dropout (TEST_PLAN.md section 4), real hop resistance (section 5), regenerative braking, bus capacitance |
| E7 | Hip roll servo screw head vs roll_to_pitch over the hip roll range (print/check_hip_roll_screw.py) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e7_hip_roll.py` | **PASS (0 FAIL, 2 WARN)** | outer screw overlaps the arm by 1.3 and 1.3 mm at every hip roll angle on both legs (as D18); the inner screw that stays clears it by 0.16 and 0.24 mm (details below) | Both legs, 2 screws each, 41 angles over the URDF hip roll range, M2 pan head 4.0 x 1.6 mm modelled | Real head size of the Feetech bag screw (B2), print tolerance, the other screws (C4) |
| E8 | Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests) | `VERIFY_OUT=<out> ODM_TEST_PYTHON=<python with rustypot, pypot> python3 altaay_lab/verify/e8_bench_pytest.py` | **FAIL (1 FAIL, 0 WARN)** | pytest: 1 failed, 52 passed in 147.05s (0:02:27) (details below) | The bench agent's tests: STS3215 protocol, first-servo check, battery guard, power log, feet, IMU, thermal guard and the Runtime cross-check, against a fake STS3215 bus on a pty and fake Blinka pins | Real servos, real USB adapter timing, real GPIO (TEST_PLAN.md sections 6 to 12) |
| E9 | Joint angles the stock policy uses in the sim walk, trained mass and our build (sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e9_joint_envelope.py` | **PASS** | in the walk (trained mass): hip yaw -5.8 to +10.3 deg (range +/-30), hip pitch -49.3 to +49.6, knee up to +90.8 (limit +90); largest policy action 0.97 (details below) | 7 current_budget.py cases on the trained model and on our build's model (C8): min and max of every joint angle, the largest policy action and motor target, after the 2 s settle and before a fall; MJCF ranges | Falls, get-up, manual moves and find_soft_offsets.py (they can reach the full joint range); real servo tracking |
| C1 | Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c1_bom_coverage.py` | **FAIL (2 FAIL, 6 WARN)** | 43 netlist parts map to BOM lines with matching part numbers (13 splices are made); BOM_FULL 188 rows vs sources: 2 FAIL (see list) (details below) | 56 netlist components to BOM lines (part numbers checked in the line text), netlist BOM references, counts per line vs Need; 168 BOM_FULL rows vs CAD nodes, print/parts.csv, netlist, fasteners.json, wire cut sums; the committed BOM_FULL.md vs a fresh build from today's sources; rows with no purchase line | Whether a bought part is the right one (datasheets), prices, the spares rule |
| C2 | Connectors: every wired pin has a mating part or end treatment; crimps fit the Molex 08-70-1040 | `VERIFY_OUT=<out> python3 altaay_lab/verify/c2_connectors.py` | **PASS (0 FAIL, 1 WARN)** | 236 wire ends match their connector class; housings 5 and terminals 13 agree with BOM 21/22, CABLE_MAP, WIRING.md; 22 AWG OD 1.7 mm vs terminal max 1.9 mm (details below) | Every end of the 118 wires on active cables vs its pin group's connector (21 classes); housing positions (one wire each, adapter V empty); housing and terminal counts vs BOM 21/22, CABLE_MAP, WIRING.md; kit cables used vs shipped; crimp insulation diameter; connector pins left open | Pin order inside each housing vs the servo port (TEST_PLAN.md section 2 polarity), crimp quality (section 1), the real part labels marked [I] in the netlist |
| C3 | Every active cable has a 3D route whose worst length plus slack fits its cut, and a service loop at every joint | `VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py` | **FAIL (3 FAIL, 16 WARN)** | 45 of 45 active cables routed in 3D (0 runs still straight placeholders); 6 wires too short before slack, 25 with less than 40 mm slack; 42 of 42 joint loops under 3 x OD (details below) | 45 active cables: route present and routed, wires and cut lengths as in the netlist, worst length over the joint ranges + 40 mm vs cut, netlist joints vs 3D crossings, loop radius at every crossing vs 3 x OD, ties | Real cable stiffness and where the slack sits, connector back-shell sizes (Molex drawing not reached), rubbing against moving parts beyond the cables3d sweep (TEST_PLAN.md section 1.4 test fit) |
| C4a | Every fitted screw has a BOM line, a length that line buys, and a count it covers (fasteners.json vs BOM.md) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py` | **PASS (0 FAIL, 3 WARN)** | 342 fitted screws and 58 inserts; 14 screws name no BOM line in fasteners.json (BOM.md buys 14 of them); Need differs from the schedule on lines: none; kit 17h holds an unstated count per size (details below) | Every fitted screw in fasteners.json (servo case screws included): BOM line exists, size and length match the line's Item and Spec, count per line vs Need and Buy, screws with no line; washers and other new items | Servo and SG90 bag contents by size (B2, test order TO1 and TO6), thread engagement (fasteners agent), stock at order time |
| C4b | No screw head or tip collision over the joint ranges, except known, decided ones (fasteners sweep vs D18 and D19) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py` | **PASS (0 FAIL, 5 WARN)** | screw hits by kind: button head fixes it 2; button head, under 0.3 mm 6; button head still hits 2; stand-in head (size not published) 26; against a CAD body the build replaces 1; D18 screws left out: 2 (details below) | Every fitted screw's head and protruding tip vs every part over each joint's URDF range and 13 joint pairs (sweep_fasteners.py results in fasteners.json); hits split into screw-limited, parts-first and static contact | Real head sizes of the bag screws (stand-in models), print tolerance, real joint stops tighter than the URDF |
| C5 | Servo IDs agree everywhere (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime code and config, bench, sim, policy order) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c5_servo_ids.py` | **PASS** | 14 joint IDs agree in 8 ID maps (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime HWI, configure_all_motors, bench): True; chains agree in netlist, WIRING.md, bench, power sim; MJCF actuator order = Runtime action order: True (details below) | 14 joint to ID pairs in 10 sources, the 3 bus chains (netlist wires, WIRING.md, bench, power sim), MJCF actuator order vs Runtime action order, Runtime checkout commit | IDs written into real servos (TEST_PLAN.md section 7.1, section 8.1 check_motors.py) |
| C6 | GPIO pins agree (netlist, WIRING.md section 3, CABLE_MAP, HARNESS_BUILD, D9, Runtime code at 376de65) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c6_gpio.py` | **PASS** | 12 Pi signals on the same GPIO and header pin in the netlist, WIRING.md, HARNESS_BUILD.md, CABLE_MAP.md, D9 and the Runtime code: True (details below) | 12 Pi signals (2 feet, 2 eyes, projector, 2 antennas, I2C SDA/SCL, 3 I2S) in 6 sources; BCM to header pin map (pinout.xyz); the far end of every netlist GPIO wire (left foot goes to the left foot switches); no GPIO used twice | Pi device tree settings (I2S overlay, PWM for the antennas), real wiring (TEST_PLAN.md sections 2 and 12) |
| C7 | Current ratings: every wire, contact and power part vs the simulated currents (sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py` | **PASS (0 FAIL, 6 WARN)** | every mean current under its limit; worst-100 ms peaks over the 26 AWG kit cable limit on 6 hops and over 3 A on 4 contacts; 2815 switch at 97% of 6 A; 10% of a leg's return current flows through the adapter (details below) | SP1 to SP3 and 11 kit cable hops vs gauge ampacity (erc.py table); chain current through the 5264 / Mini-SPOX contacts (3 A); return current in the D15 data-lead grounds and the adapter; fuse, BMS, switch, BEC, BEC leads, XT30, cells vs pack and BEC currents (E6 ngspice, CURRENT_BUDGET.md falls) | Real servo currents (CURRENT_BUDGET.md: up to 2 x sim until a bench log), temperature rise inside the body, connector wear, contact resistance (TEST_PLAN.md sections 3 to 5 and 9) |
| C8 | The stock policy walks the robot we will build (2.77 kg) on flat ground (sim/added_mass_sim.py, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c8_policy_mass.py` | **PASS** | our build 2.7669 kg: 0 falls in 36 flat-ground runs; forward speed 0.67 of the command (trained mass 0.73) (details below) | Model mass vs MASS_BUDGET.md; stock copy vs CURRENT_BUDGET.md; our build in 6 flat cases nominal + 6 seeds each; tracking vs ADDED_MASS_SIM.md table 1; a hardware test for the centre of mass margin | Rough terrain (falls for stock and ours), get-up, real servo tracking (issue 48), the real mass and centre of mass (not weighed) |
| C9 | Docs agree: numbers that appear in several docs are the same everywhere | `VERIFY_OUT=<out> python3 altaay_lab/verify/c9_docs.py` | **FAIL (11 FAIL, 10 WARN)** | 11 disagreements (blocker counts 1, test print count 1, blocker status words 5, stale BOM blocker bullets 3, screw count 1); blocker table: 32 rows, 19 cleared or decided (details below) | Blocker counts and blocker status words, BOM totals and test order total, part counts, STL count, screw counts, decision range, upstream issue count, wire currents (WIRING.md vs netlist), print numbers, robot mass; 38 docs (history/ left out) | Numbers written in words or in a form the patterns do not catch; history entries; prose claims without numbers |
| C10 | Wiring sheets cover every wire of the netlist (wiring/sheets, run on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c10_sheets.py` | **PASS** | 118 of 118 active wires drawn in full on sheets 1, 2, 3, 4, 5; harness sheet 5: True (details below) | Every active netlist wire drawn in full on a sheet (sheets 1 to 4), every active cable on the harness sheet (sheet 5), the generator's own stop rules, committed sheets newer than netlist.yaml | Whether a drawing is easy to read; label placement (the generator prints layout warnings) |
| C11 | Hip yaw the stock policy uses (walk and turn) stays under the F198/F211 collision onset (21.7 deg) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c11_hip_yaw_envelope.py` | **PASS (0 FAIL, 1 WARN)** | largest hip yaw angle 10.4 deg (ours, turn_1.0), turn 10.3 and 10.4 deg; onset 21.7 deg; margin 11.3 deg (rule 5); policy bound 16.0 deg with the sim overshoot (details below) | Collision onset from the fastener sweep; largest /hip yaw/ in 7 sim cases (turn 1.0 rad/s included) on the trained model and our build; the policy's bound (default + 0.25 x tanh action) checked on 6000 random inputs; clamps in the Runtime code | Real servo overshoot, falls, manual moves, find_soft_offsets.py, other policies or a wider command range |

## FAIL findings and proposed fixes

Each line: what is wrong, with the numbers, then the proposed fix and the file it belongs to. The files belong to other agents or to the lead; nothing here was changed by agent Q.

### E6b TEST_PLAN.md section 5 hop gate (40 mOhm) is enough for the section 9 ankle gate (power path sim sweep, sim pass only)
- TEST_PLAN.md section 5 lets a hop of up to 40 mOhm per conductor pass, but in the sim even the typical corner (27.6 mOhm) leaves an ankle under 6.0 V for 22% of the walk at a nominal pack, over the section 9 gate of 10%; the 22 AWG made leads of contingency X1/X2 only reach 19%; only about 10 mOhm per conductor or less passes **Fix:** TEST_PLAN.md: make the section 5 gate the hop value the section 9 gate needs (about 10 mOhm per conductor in the sim), or say in section 9 that the nominal-pack ankle gate is expected to fail with the stock kit cables and what is done then (options to try in the sim first: a second power feed into the free BUS 1 port of ID 24 and ID 14 at the chain ends, or a source that does not drop out); the stop rule in section 9 (worse than the high-side corner) does not match its 10% pass line (altaay_lab/TEST_PLAN.md sections 5 and 9)

### E8 Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests)
- test_rustypot_panic_after_checksum_error_is_caught failed in 1 of 4 runs: after a rustypot panic the pypot fallback reports 'torque off (attempt 1)' but the fake servos keep torque enabled (register 40 = 1): the sync write can be lost while the bus still carries garbage, and nothing reads it back **Fix:** bench/odm_bench/walkhooks.py hard_stop(): after pypot_io._set_torque_enable(...), read register 40 back from every servo and break only when all read 0; otherwise retry (the 5 attempts), and report the ids still on (altaay_lab/bench/odm_bench/walkhooks.py)

### C1 Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners)
- BOM_FULL.md is older than its sources: qty K02 Cable ties, small nylon: BOM_FULL.md 1, fresh build 10; gone K11 Gap: no printed surface within 15 mm; new M3x6 button head (10); new M2.5x5 SHCS (4); new M2.5 flat washer, small series (8); new Drill bit 6.0 mm (1); new Drill bit 2.7 mm (1); new Hand holder for T11 and T12 (1) **Fix:** re-run python3 altaay_lab/viewer/make_viewer_data.py --out <scratch> --write-bom and commit BOM_FULL.md and bom_full.csv (altaay_lab/BOM_FULL.md)
- K09 Adhesive tie mount: needed (95 at places where the CAD has no feature) but no BOM.md line buys it and BOM.md does not say why **Fix:** add a BOM.md line (or name it under 'Not costed' with the reason) (altaay_lab/BOM.md)

### C3 Every active cable has a 3D route whose worst length plus slack fits its cut, and a service loop at every joint
- D3: 2 wire(s) cannot reach: FSL1.COM -> FSL2.COM, FSL1.NO -> FSL2.NO; worst routed length 54 mm over the joint ranges, cut 40 mm, too short by 14 mm before any slack **Fix:** wiring/netlist.yaml D3: cut_mm 40 -> 100 on FSL1.COM -> FSL2.COM and FSL1.NO -> FSL2.NO (worst 54 mm + 2 x 20 mm slack), and the same in CABLE_MAP.md (altaay_lab/wiring/netlist.yaml)
- D4: 2 wire(s) cannot reach: FSR1.COM -> FSR2.COM, FSR1.NO -> FSR2.NO; worst routed length 54 mm over the joint ranges, cut 40 mm, too short by 14 mm before any slack **Fix:** wiring/netlist.yaml D4: cut_mm 40 -> 100 on FSR1.COM -> FSR2.COM and FSR1.NO -> FSR2.NO (worst 54 mm + 2 x 20 mm slack), and the same in CABLE_MAP.md (altaay_lab/wiring/netlist.yaml)
- D7: 2 wire(s) cannot reach: LEDP.K -> PI.20, PI.22 -> RP.1; worst routed length 178 mm over the joint ranges, cut 160 mm, too short by 18 mm before any slack **Fix:** wiring/netlist.yaml D7: cut_mm 160 -> 220 on LEDP.K -> PI.20 and PI.22 -> RP.1 (worst 178 mm + 2 x 20 mm slack), and the same in CABLE_MAP.md (altaay_lab/wiring/netlist.yaml)

### C9 Docs agree: numbers that appear in several docs are the same everywhere
- STATE.md line 6 says '18 of 30 cleared or decided', HARDWARE_AUDIT.md has 19 of 32 cleared or decided **Fix:** STATE.md line 6: '18 of 30 cleared or decided' -> '19 of 32 cleared or decided' (altaay_lab/STATE.md)
- STATE.md line 6 says test print blockers 4, HARDWARE_AUDIT.md has 5: '4 settled by the coupon' **Fix:** STATE.md line 6: '4 settled by the coupon' -> '5 settled by the coupon' (altaay_lab/STATE.md)
- BOM.md line 63 says 'B18 cleared', HARDWARE_AUDIT.md has B18 OPEN, test order 3 **Fix:** make BOM.md line 63 match HARDWARE_AUDIT.md (B18: OPEN), or clear B18 in HARDWARE_AUDIT.md with its evidence (altaay_lab/BOM.md)
- BOM.md line 91 says 'B8 cleared on paper', HARDWARE_AUDIT.md has B8 OPEN, test order 7 and 10 **Fix:** make BOM.md line 91 match HARDWARE_AUDIT.md (B8: OPEN), or clear B8 in HARDWARE_AUDIT.md with its evidence (altaay_lab/BOM.md)
- BOM.md line 170 says 'B18 cleared on paper', HARDWARE_AUDIT.md has B18 OPEN, test order 3 **Fix:** make BOM.md line 170 match HARDWARE_AUDIT.md (B18: OPEN), or clear B18 in HARDWARE_AUDIT.md with its evidence (altaay_lab/BOM.md)
- BOM.md line 201 says 'B18 cleared on paper', HARDWARE_AUDIT.md has B18 OPEN, test order 3 **Fix:** make BOM.md line 201 match HARDWARE_AUDIT.md (B18: OPEN), or clear B18 in HARDWARE_AUDIT.md with its evidence (altaay_lab/BOM.md)
- CABLE_MAP.md line 77 says 'B18 cleared', HARDWARE_AUDIT.md has B18 OPEN, test order 3 **Fix:** make CABLE_MAP.md line 77 match HARDWARE_AUDIT.md (B18: OPEN), or clear B18 in HARDWARE_AUDIT.md with its evidence (altaay_lab/CABLE_MAP.md)
- BOM.md 'BLOCKERS that affect this BOM' still lists '3 Compute: B24, out of stock online 2026-11-01.', but B24 is DECIDED in HARDWARE_AUDIT.md **Fix:** BOM.md: drop the bullet '3 Compute: B24, out of stock online 2026-11-01.' (or rewrite it to the current status) (altaay_lab/BOM.md)
- BOM.md 'BLOCKERS that affect this BOM' still lists '8 2S BMS: B12, JZK fits but is rated 8 A; decide the fuse or find a 15 A board that fits', but B12 is CLEARED in HARDWARE_AUDIT.md **Fix:** BOM.md: drop the bullet '8 2S BMS: B12, JZK fits but is rated 8 A; decide the fuse ' (or rewrite it to the current status) (altaay_lab/BOM.md)
- BOM.md 'BLOCKERS that affect this BOM' still lists '10 Power switch: B22, no fitting 15 A part; $6.00 placeholder.', but B22 is CLEARED in HARDWARE_AUDIT.md **Fix:** BOM.md: drop the bullet '10 Power switch: B22, no fitting 15 A part; $6.00 placehol' (or rewrite it to the current status) (altaay_lab/BOM.md)
- HARDWARE_AUDIT.md B1 says 189 screws by size, the BOM.md screw lines (17a to 17k) need 221 **Fix:** HARDWARE_AUDIT.md B1: write the count of the final fastener schedule (fasteners/fasteners.json) and the same in BOM.md (altaay_lab/HARDWARE_AUDIT.md B1)

## WARN findings (risks, test fits, notes)

### E1
- M6 NOT caught: switched pack (8.4 V) on BNO055 VIN (3.3 V, dir pwr_in) (expected ERROR in 'domains'; got {'ERROR': 0, 'WARN': 0, 'INFO': 1}) Proposed: audit/erc.py check 4: treat pwr_in like in and bidir, i.e. `if p.get("dir") in ("in", "bidir", "pwr_in") and ...`

### E4
- viewer warning: BOM line 17j (M3x6 button head) has no view mapping
- viewer warning: BOM line 17k (M2.5x5 SHCS) has no view mapping
- viewer warning: BOM line 17l (M2.5 flat washer, small series) has no view mapping

### E6
- sim, typical corner, nominal pack: an ankle is under 6.0 V for 21% of the walk; TEST_PLAN.md section 9 passes only under 10% Proposed: known (POWER_PATH_SIM.md item 4, D15 follow-up): measure the hop resistance first (TEST_PLAN.md section 5); if over 40 mOhm, 22 AWG made leg leads (BOM contingency X1/X2)
- sim, high-side corner, nominal pack: an ankle is under 6.0 V for 63% of the walk; TEST_PLAN.md section 9 passes only under 10% Proposed: known (POWER_PATH_SIM.md item 4, D15 follow-up): measure the hop resistance first (TEST_PLAN.md section 5); if over 40 mOhm, 22 AWG made leg leads (BOM contingency X1/X2)
- sim, high-side corner, nominal pack: right_ankle 3.44 V, right_knee 3.62 V, left_ankle 3.85 V, left_knee 3.98 V, right_hip_pitch 4.15 V, left_hip_pitch 4.39 V under 4.5 V (TEST_PLAN.md section 9 fails on any servo under 4.5 V) Proposed: same gate as above; the high-side corner is the reason the hop resistance is measured before assembly
- sim/POWER_PATH_SIM.md has no row for the star wiring that is built (D15); its tables show only the Tnkr and Y-lead wirings Proposed: add the star rows (this run, or the lead's) to the results table in sim/POWER_PATH_SIM.md
- sim/power_path_sim.py models the D15 power leads as 20 AWG; netlist.yaml, WIRING.md and D15 build them in 22 AWG Proposed: in sim/power_path_sim.py build(): use wire(22, 150) and wire(22, 180) for bL and bN (and fix the comment on topology 'star'), then re-run

### E7
- left: the inner screw D18 keeps clears roll_to_pitch by only 0.24 mm (worst at -25.0 deg), inside normal print tolerance Proposed: add to the first-leg check (print/PRINT_PLAN.md left-leg check, D18): sweep hip roll by hand with the inner screw fitted and look for rubbing on roll_to_pitch
- right: the inner screw D18 keeps clears roll_to_pitch by only 0.16 mm (worst at -10.0 deg), inside normal print tolerance Proposed: add to the first-leg check (print/PRINT_PLAN.md left-leg check, D18): sweep hip roll by hand with the inner screw fitted and look for rubbing on roll_to_pitch

### C1
- F07 M2x6 self-tapping pan head: BOM_FULL qty 44 counts 2 screws that are not fitted (fasteners.json: 42 fitted) Proposed: bom_full.py: count only fitted screws in the Qty column
- F17 PA3.0x5 self-tapping, washer head (Feetech idle screw): BOM_FULL qty 14 counts 11 screws that are not fitted (fasteners.json: 3 fitted) Proposed: bom_full.py: count only fitted screws in the Qty column
- BOM_FULL counts 27 heat shrink pieces (the sleeves the 3D view draws), fewer than the 44 splice ends in the netlist; TEST_PLAN.md 1.3 wants heat shrink over every solder joint and splice Proposed: count one sleeve per splice end and per wire-to-wire or lead joint in viewer/bom_full.py (the old netlist estimate), or say in TEST_PLAN.md 1.3 which joints get none
- F02 M2.5x5 DIN 912 A2 shows MISSING, but BOM.md line 17k buys it: fasteners.json does not name the line, so the BOM_FULL build cannot link it Proposed: set line '17k' on these screws in fasteners.json, then re-run make_viewer_data.py --write-bom
- F13 M3x6 ISO 7380 A2 button head shows MISSING, but BOM.md line 17j buys it: fasteners.json does not name the line, so the BOM_FULL build cannot link it Proposed: set line '17j' on these screws in fasteners.json, then re-run make_viewer_data.py --write-bom
- BOM.md lines not used by any BOM_FULL row: 17j (M3x6 button head), 17k (M2.5x5 SHCS), 17l (M2.5 flat washer, small series), T11 (Drill bit 6.0 mm), T12 (Drill bit 2.7 mm), T13 (Hand holder for T11 and T12) Proposed: map them in viewer/bom_full.py (tools, washers) or link them from fasteners.json

### C2
- 08-70-1040 insulation range and 3 A rating come from distributor listings read via a search index (Molex sheet not read; uk.rs-online.com and octopart.com are outside this session's network) Proposed: read the Molex 5263 / 08-70-1040 product sheet and write the insulation range and current rating into CABLE_MAP.md 'Connector parts'

### C3
- D10: 3 wire(s) reach with only 29 mm to spare (worst PI.40 -> AMP.DIN 171 mm, cut 200 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 220 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- D11: 2 wire(s) reach with only 32 mm to spare (worst AMP.SPK+ -> SPK.+ 68 mm, cut 100 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 110 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- D12: 1 wire(s) reach with only 24 mm to spare (worst PI.CSI -> CAM.CSI 126 mm, cut 150 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 170 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- P11: 2 wire(s) reach with only 6 mm to spare (worst JBN.S -> SPG.S 54 mm, cut 60 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 100 mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack
- P3: 1 wire(s) reach with only 23 mm to spare (worst PACK.MID -> BMS.B1 97 mm, cut 120 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 140 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- P6: 1 wire(s) reach with only 14 mm to spare (worst BMS.P+ -> XT30.F+ 96 mm, cut 110 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 140 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- P7: 2 wire(s) reach with only 9 mm to spare (worst F1.OUT -> SW1.VIN 81 mm, cut 90 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 130 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- P8: 1 wire(s) reach with only 14 mm to spare (worst BMS.P- -> XT30.F- 96 mm, cut 110 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 140 mm, or keep the cut and test fit it (TEST_PLAN.md 1.4)
- S2: 3 wire(s) reach with only 22 mm to spare (worst SV20.BUS1.D -> SV21.BUS2.D 128 mm, cut 150 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2
- S7: 3 wire(s) reach with only 33 mm to spare (worst SV10.BUS1.D -> SV11.BUS2.D 117 mm, cut 150 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2
- SD1: 3 wire(s) reach with only 2 mm to spare (worst U2.H3.D -> YD3.S 28 mm, cut 30 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 70 mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack
- SP1: 1 wire(s) reach with only 1 mm to spare (worst JG20.S -> SV20.BUS2.G 19 mm, cut 20 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 60 mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack
- SP2: 1 wire(s) reach with only 1 mm to spare (worst JG10.S -> SV10.BUS2.G 19 mm, cut 20 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 60 mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack
- SP3: 1 wire(s) reach with only 1 mm to spare (worst JG30.S -> SV30.BUS2.G 19 mm, cut 20 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut it 60 mm, or state in CABLE_MAP.md that short splice tails inside one part need no service slack
- 42 of 42 joint crossings store their length change in a loop tighter than 3 x OD: the routes tie the cable to both links close to each joint axis (spans 0.2 to 2.9 mm at the shortest pose). Worst: S8 at right_hip_roll 1.0 to 6.5 mm, loop R 1.2 mm = 0.5 x OD; D3 at left_hip_roll 2.8 to 8.2 mm, loop R 1.8 mm = 0.5 x OD; S3 at left_hip_roll 2.2 to 6.8 mm, loop R 1.5 mm = 0.6 x OD; D4 at right_hip_roll 2.7 to 10.8 mm, loop R 2.2 mm = 0.6 x OD; S7 at right_hip_yaw 2.2 to 8.4 mm, loop R 1.7 mm = 0.7 x OD Proposed: place the ties at each joint far enough from the axis that the loop radius reaches 3 x OD, and check every loop at both joint limits on the first leg (TEST_PLAN.md section 1.4)
- 106 retention points have no printed surface to hold a tie mount (T001 for P3; T002 for P3; T003 for P6,P8; T004 for P6,P8; T005 for P7; T006 for P7; T007 for SP1; T008 for D3,SP1) Proposed: decide each (tie to a neighbour cable, a printed clip, or move the route) before the harness is built

### C4a
- 4 x M2.5x5 DIN 912 A2: fasteners.json names no BOM line, BOM.md line 17k buys it (Need 4, Buy 5) Proposed: fasteners.json: set line '17k' on these screws
- 10 x M3x6 ISO 7380 A2 button head: fasteners.json names no BOM line, BOM.md line 17j buys it (Need 10, Buy 12) Proposed: fasteners.json: set line '17j' on these screws
- line 17h is a kit: how many of each size it holds is not in BOM.md, so 30 screws ({'M2x8 self-tapping pan head': 2, 'M2x5 self-tapping pan head': 22, 'M2x4 self-tapping pan head': 6}) cannot be checked against it Proposed: write the kit's count per size into BOM.md line 17h

### C4b
- 2 screws still hit with the button head, known and left as a joint range point in D19 (not fixed): F211 M3x6 ISO 7380 A2 button head vs body_middle_bottom at right_hip_yaw -28.3, -1.49 mm, -0.82 mm with the button head; F198 M3x6 ISO 7380 A2 button head vs body_middle_bottom at left_hip_yaw 25.0, -1.47 mm, -0.82 mm with the button head (outside the walk: F198: hits from left_hip_yaw +21.7 deg, the sim walk uses -5.3 to +10.4 deg (E9); F211: hits from right_hip_yaw -21.7 deg, the sim walk uses -6.3 to +6.2 deg (E9), see C11) Proposed: see C11: nothing in the Runtime limits hip yaw; decide the limit before the first powered joint sweep (TEST_PLAN.md 8.3)
- 8 screws clear only because of the M3x6 ISO 7380 button head (decision: D19; BOM line: 17j); 6 of them by less than 0.3 mm: F196 M3x6 ISO 7380 A2 button head vs left_roll_to_pitch at left_hip_pitch -70.0, -1.19 mm, 0.16 mm with the button head; F200 M3x6 ISO 7380 A2 button head vs left_roll_to_pitch at left_hip_pitch -25.6, -1.19 mm, 0.16 mm with the button head; F209 M3x6 ISO 7380 A2 button head vs right_roll_to_pitch at right_hip_pitch -30.0, -1.19 mm, 0.16 mm with the button head; F213 M3x6 ISO 7380 A2 button head vs right_roll_to_pitch at right_hip_pitch -30.0, -1.19 mm, 0.16 mm with the button head; F247 M3x6 ISO 7380 A2 button head vs left_roll_to_pitch at left_hip_pitch -70.0, -1.19 mm, 0.16 mm with the button head; F254 M3x6 ISO 7380 A2 button head vs right_roll_to_pitch at right_hip_pitch -27.2, -1.19 mm, 0.16 mm with the button head Proposed: record the button-head change as a decision (DECISIONS.md D19) with the BOM line, and add the rub check to the first-leg check (print/PRINT_PLAN.md)
- 26 servo case or bag screws overlap a part with the stand-in head model (real head size not published): F162 SG90 bag horn screw vs antenna at zero pose (static) 0.0, -0.78 mm; F163 SG90 bag horn screw vs antenna at zero pose (static) 0.0, -0.78 mm; F262 PA2.0 self-tapping (factory) vs neck_left_sheet at zero pose (static) 0.0, -0.22 mm; F263 PA2.0 self-tapping (factory) vs neck_left_sheet at zero pose (static) 0.0, -0.22 mm; F266 PA2.0 self-tapping (factory) vs head_roll_mount at zero pose (static) 0.0, -0.22 mm; F267 PA2.0 self-tapping (factory) vs head_roll_mount at zero pose (static) 0.0, -0.22 mm Proposed: measure the factory and bag screw heads on the first servo and the SG90 pack (test orders TO1 and TO6, B2)
- 1 screws touch a CAD body the build replaces (keep the real part clear when placing it): F123 M2.5x6 DIN 912 A2 vs bms at zero pose (static) 0.0, -0.34 mm
- 160 screws touch a part at the zero pose by up to 0.08 mm (static contact: head seated against a face; under the 0.1 mm modelling resolution)

### C7
- kit cable hops over the 26 AWG chassis limit (2.2 A) in the worst 100 ms (means are under it): S2 3.28 A, S3 2.97 A, S4 2.28 A, S7 3.91 A, S8 2.98 A, S9 2.62 A. The kit cable gauge is not published; 26 AWG is the smallest plausible (erc.py KIT_AWG) Proposed: measure one hop (TEST_PLAN.md section 5) and the kit wire gauge on the first servo (TO1); if it is 26 AWG, use 22 AWG made leads for the first two hops of each leg (BOM contingency X1/X2)
- worst 20 ms over 2 x the 26 AWG limit (erc.py rule): S2 5.62 A, S3 5.27 A, S7 5.68 A, S8 5.09 A
- chain current through one 5264 / Mini-SPOX contact over its 3 A rating ([I] distributor listings) in the worst 100 ms (means 1.8 to 1.9 A): SP1 3.35 A, S2 3.28 A, SP2 4.03 A, S7 3.91 A Proposed: read the Molex 08-70-1040 / 50-37-5033 sheet for the 3-circuit and short-time rating; log Present Current of the first servo of each leg in TEST_PLAN.md section 9
- D15 says no servo current through the adapter, but the data-lead grounds make it a parallel return path: 0.18 A mean, 0.35 A worst 100 ms through the adapter ground between H3 and H5 (typical contacts, sim) Proposed: harmless for the ratings (22 AWG, 3 A contacts); if it should be zero, drop the GND wire of one adapter socket lead (keep one ground reference) or state in WIRING.md section 2 that some return current flows through SD1, SD2 and the adapter ground
- main switch Pololu 2815, 6 A at 55 C MOSFETs: 5.84 A against 6.00 A, 3% margin (sim pass only) Proposed: bench check: TEST_PLAN.md section 4.2 (2815 at 5 A) and the section 9 walking log; the 2815 is rated 6 A with the MOSFETs at 55 C in still air at 22 C, inside the body it runs warmer
- falls with every allowance stacked reach about 17 A for 20 ms (CURRENT_BUDGET.md), the bottom of the Tenergy trip band (22 +/- 5 A after 8 +/- 4 ms): a fall at a low pack can open the BMS (sim pass only; known) Proposed: keep TEST_PLAN.md section 3.3 (pulse test) and log BMS cut-outs in section 9

### C9
- sim/MASS_BUDGET.md models 274 screws, fasteners.json fits 342 (the screw mass, 175 g, is from the older count) Proposed: re-run sim/mass_budget.py on fasteners.json when it is final
- GAPS.md line 65 says 'D1 to D12', DECISIONS.md goes to D21 (dated section)
- START_HERE.md line 4 says 'D1 to D18', DECISIONS.md goes to D21: the work in that file did not look at D19 to D21 Proposed: START_HERE.md: check D19 to D21 against it, then write 'D1 to D21' (or date the statement)
- START_HERE.md line 17 says 'D1 to D18', DECISIONS.md goes to D21: the work in that file did not look at D19 to D21 Proposed: START_HERE.md: check D19 to D21 against it, then write 'D1 to D21' (or date the statement)
- START_HERE.md line 106 says 'D1 to D18', DECISIONS.md goes to D21: the work in that file did not look at D19 to D21 Proposed: START_HERE.md: check D19 to D21 against it, then write 'D1 to D21' (or date the statement)
- STATE.md line 7 says 'D1 to D18', DECISIONS.md goes to D21: the work in that file did not look at D19 to D21 Proposed: STATE.md: check D19 to D21 against it, then write 'D1 to D21' (or date the statement)
- UPSTREAM_ISSUES.md line 7 says 'D1 to D12', DECISIONS.md goes to D21: the work in that file did not look at D13 to D21 Proposed: UPSTREAM_ISSUES.md: check D13 to D21 against it, then write 'D1 to D21' (or date the statement)
- UPSTREAM_ISSUES.md line 364 says 'D1 to D12', DECISIONS.md goes to D21: the work in that file did not look at D13 to D21 Proposed: UPSTREAM_ISSUES.md: check D13 to D21 against it, then write 'D1 to D21' (or date the statement)
- README.md line 3 gives the robot mass as 2.1 kg (sim mass, trained model); the build is 2.77 kg by sim/MASS_BUDGET.md Proposed: README.md line 3: after '2.1 kg (sim mass)' add ' (the lab build is about 2.77 kg by the mass budget, sim/MASS_BUDGET.md, not weighed)'
- START_HERE.md line 9 gives the robot mass as 2.11 kg (sim mass, trained model); the build is 2.77 kg by sim/MASS_BUDGET.md Proposed: START_HERE.md line 9: after 'about 2.11 kg (sim mass)' add ' (the lab build is about 2.77 kg by the mass budget, sim/MASS_BUDGET.md, not weighed)'

### C11
- nothing in the Runtime limits hip yaw: the policy bound keeps the walk under the onset, but a manual move, find_soft_offsets.py (Runtime issue 32 moves every joint) or a fall can still reach 21.7 to 30 deg and press the F198/F211 heads into body_middle_bottom Proposed: DECISIONS.md: record the hip yaw limit (for example the STS3215 angle limit registers set to about +/-20 deg of travel for IDs 10 and 20 in configure_motor.py, or a clip in the walk script), or relieve body_middle_bottom at the two heads

## Hardware-only tests that remain

No check above replaces these; each needs the parts or the robot. Order and pass/fail values are in TEST_PLAN.md.

| Test | Where | What the checks above say about it |
|---|---|---|
| Every made cable: crimp pull, connector fit, heat shrink, length at both limits of every joint it crosses | TEST_PLAN.md section 1 | C2 (end treatments), C3 (lengths, loops, the 2 foot jumpers) |
| Continuity and polarity of every wire, no short between nets | TEST_PLAN.md section 2 (audit/continuity_checklist.csv) | E1 |
| Cells, holder drop at 10 A, BMS trip, first charge | TEST_PLAN.md section 3 | C7 (BMS margin on falls) |
| BEC set point and input sweep (dropout), Pololu 2815 at 5 A, 5 V regulator, fuse holder | TEST_PLAN.md section 4 | E6 (BEC dropout 0.3 V assumed), C7 (2815 at 97% of its 6 A rating) |
| Kelvin resistance of one servo hop | TEST_PLAN.md section 5 | E6b (the sim needs about 10 mOhm per conductor for the section 9 gate) |
| Adapter enumerates with H1 unpowered and drives one servo | TEST_PLAN.md section 6 | C7 (ground return through the adapter) |
| First servo: registers 41 to 86, register 85 = 0, firmware, speed, thermal hold | TEST_PLAN.md section 7 | E8 (bench scripts on a fake bus) |
| Weigh the robot and find its centre of mass; staged power-up; all 14 IDs answer | TEST_PLAN.md section 8 (8.0 is the mass step) | C8 (backward margin 4 to 6 mm), C5 (IDs) |
| Walking log: every servo voltage and current at 50 Hz, checksum errors | TEST_PLAN.md section 9 | E6, E6b (sim predicts the ankle gate fails at nominal) |
| IMU: 1000 still reads, tilt signs | TEST_PLAN.md section 10 | none (no sim check of B20) |
| Battery cut-off at servo Present Voltage 6.0 V | TEST_PLAN.md section 11 | E8 (battery guard on the fake bus) |
| Foot switches: under 1 ohm closed, 200 presses, 60 s still | TEST_PLAN.md section 12 | C6 (pins), C3 (jumper length) |
| Coupon prints: insert bores, foot_top wall, left eye pilot, TPU sole | print/PRINT_PLAN.md coupon session (B14, B15, B16, B26) | none |
| Screw head fits the CAD cannot settle: servo bag split, horn gap, M2x5 heads, hip roll inner screw rub | HARDWARE_AUDIT.md B2, B6, B21; D18 first-leg check | E7, C4a, C4b |
| Hip yaw kept under 21.7 deg outside the walk (manual moves, find_soft_offsets.py, falls): F198/F211 heads | not in TEST_PLAN.md yet (proposed with C11) | C11 (walk and turn reach 10.4 deg; nothing in the Runtime limits it) |

## Details per check

### E1 Electrical rule check of the netlist (audit/erc.py) plus mutation test: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e1_erc.py`. Finished 2026-11-02 04:04 UTC, 9 s.
- erc.py on wiring/netlist.yaml: 0 ERROR, 0 WARN, 5 INFO (exit 0)
- Components 56, pins 224, cables 49 (4 removed), wires 118.
- committed audit/ERC_REPORT.md current: True; audit/continuity_checklist.csv current: True
- mutation test: 9 of 10 injected faults caught
- extended domain rule (pwr_in pins, not in erc.py): 11 wire ends on pwr_in pins, 0 over their domain
- INFO: M1 caught: S2 V conductor moved to the ID 21 DATA pin (short SERVO_7V2 to BUS_DATA) (expected ERROR in 'shorts'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M2 caught: SP1 V wire made 16 AWG on an 08-70-1040 terminal (expected ERROR in 'crimps'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M3 caught: wire added to the empty adapter H3 V position (nc pin, D15) (expected ERROR in 'pin use'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M4 caught: pin name typo SV22.BUS3.G (expected ERROR in 'references'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M5 caught: P13 mean current 12 A on 20 AWG (limit 11 A) (expected ERROR in 'ampacity'; got {'ERROR': 1, 'WARN': 0, 'INFO': 5})
- INFO: M7 caught: switched pack (8.4 V) on GPIO22 (dir in) (expected ERROR in 'domains'; got {'ERROR': 1, 'WARN': 0, 'INFO': 4})
- INFO: M8 caught: 5264 plug on a 2.54 mm header pin group (expected ERROR in 'connector match'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M9 caught: misspelt wire key 'guage' (expected WARN in 'schema'; got {'ERROR': 0, 'WARN': 1, 'INFO': 0})
- INFO: M10 caught: wire left on removed cable S14 (expected ERROR in 'references'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})

### E2 BOM.md subtotals, totals and test order total (audit/bom_totals.py on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py`. Finished 2026-11-02 04:04 UTC, 0 s.
- bom_totals.py: {Robot: 623.53, Fasteners and mechanical: 90.39, Cables, connectors, wire: 122.3, Print material: 53.97, Expression (optional upstream): 82.4, Tools (one-time): 248.17} build 890.19 with expression 972.59 with tools 1220.76 test order 226.46
- BOM.md copy unchanged after the recompute: every subtotal and total in BOM.md matches its lines
- Buy >= Need checked on 67 countable lines (Need and Buy in the same unit)

### E3 bom.json rebuilt from BOM.md (audit/bom_md_to_json.py on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py`. Finished 2026-11-02 04:04 UTC, 0 s.
- bom_md_to_json.py: 78 rows written to bom.json; committed bom.json 78 rows, rebuilt 78 rows
- rebuilt bom.json is identical to the committed one

### E4 Exploded-view data build and its CAD count checks (viewer/make_viewer_data.py): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e4_viewer.py`. Finished 2026-11-02 04:06 UTC, 72 s.
- printed parts 52 / 52 over 36 STLs; servos 14 / 14; inserts 58 / 58; bearings 3 / 3
- BOM lines 78 (cad 11, placeholder 11, filament 2, not modelled 54); count mismatches none
- STL vs URDF frame check: 29 parts, worst 0.028 mm; assembly.json match True; unmapped meshes none
- screws drawn 355 (355 screws from altaay_lab/fasteners/fasteners.json, 62 with the length from the drawing, not yet chosen (skipped: insert 58)); cables drawn 58 (58 cables from altaay_lab/cables3d/cables3d.json)
- GLB 3.80 MB, 734 nodes (output kept in the scratch folder, not in git)

### E5 Servo current budget from the stock walk (sim/current_budget.py, sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e5_current_budget.py`. Finished 2026-11-02 03:36 UTC, 18 s.
- Stand, zero command: falls none; mean 0.19, 100 ms 0.23, 20 ms 0.24, 2 ms 0.24 A
- Walk forward 0.15 m/s: falls none; mean 2.22, 100 ms 3.08, 20 ms 4.02, 2 ms 4.97 A
- Turn 1.0 rad/s: falls none; mean 2.38, 100 ms 3.21, 20 ms 5.39, 2 ms 6.40 A
- Walk sideways 0.2 m/s: falls none; mean 2.25, 100 ms 3.81, 20 ms 5.92, 2 ms 7.19 A
- Walk forward, backlash model: falls none; mean 3.24, 100 ms 4.72, 20 ms 6.77, 2 ms 8.30 A
- Walk forward, rough terrain, backlash model: falls 0.28 s; mean 2.65, 100 ms 3.92, 20 ms 6.15, 2 ms 7.80 A
- Walk forward with pushes: falls 10.68 s; mean 1.89, 100 ms 3.59, 20 ms 5.26, 2 ms 6.27 A
- worst single servo, backlash walk: left_knee 3.33 A peak; highest RMS right_knee 1.46 A (doc: 3.35 A peak knee, 1.45 A RMS)

### E6 Power path to every servo, built wiring D15 (sim/power_path_sim.py star, ngspice, sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py`. Finished 2026-11-02 03:37 UTC, 33 s.
- walk, backlash, pack full, high-side R: worst right_ankle 4.40 V min; pack 5.2 A mean, 10.6 A max; BEC out 8.6 A max; ankles under 6 V 15% of the time; longest time of any servo under 4.5 V 3 ms
- walk, backlash, pack full, typical R: worst left_ankle 5.99 V min; pack 5.1 A mean, 11.1 A max; BEC out 9.1 A max; ankles under 6 V 0% of the time; longest time of any servo under 4.5 V 0 ms
- walk, backlash, pack nominal, high-side R: worst right_ankle 3.44 V min; pack 5.4 A mean, 10.2 A max; BEC out 8.3 A max; ankles under 6 V 63% of the time; longest time of any servo under 4.5 V 324 ms
- walk, backlash, pack nominal, typical R: worst right_ankle 5.04 V min; pack 5.4 A mean, 10.8 A max; BEC out 8.8 A max; ankles under 6 V 21% of the time; longest time of any servo under 4.5 V 0 ms
- walk, backlash, pack low, high-side R: worst right_ankle 2.71 V min; pack 5.6 A mean, 10.0 A max; BEC out 8.0 A max; ankles under 6 V 100% of the time; longest time of any servo under 4.5 V 1238 ms
- walk, backlash, pack low, typical R: worst right_ankle 4.23 V min; pack 5.6 A mean, 10.5 A max; BEC out 8.5 A max; ankles under 6 V 100% of the time; longest time of any servo under 4.5 V 102 ms
- fall after a push, pack low, high-side R: worst left_ankle 3.07 V min; pack 4.2 A mean, 11.1 A max; BEC out 9.0 A max; ankles under 6 V 100% of the time; longest time of any servo under 4.5 V 286 ms
- documented result reproduced: worst right_ankle 5.036 V (D15: 5.04 V)
- netlist SP1 to SP3 gauge: ['22 AWG']; sim star leads: 20 AWG
- 22 AWG leads, nominal, typical: worst right_ankle 4.995 V (20 AWG: 5.036 V); ankles under 6 V 22%
- 22 AWG leads, nominal, high-side: worst right_ankle 3.410 V (20 AWG: 3.440 V); ankles under 6 V 63%

### E6b TEST_PLAN.md section 5 hop gate (40 mOhm) is enough for the section 9 ankle gate (power path sim sweep, sim pass only): FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py`. Finished 2026-11-02 03:37 UTC, 16 s.
- typical corner (24 AWG kit cable, 5 mOhm contacts): hop 27.6 mOhm per conductor; worst right_ankle 5.00 V; ankles under 6 V 22.3% of the walk; BEC out mean 6.57 V
- 22 AWG made leads (contingency X1/X2), 5 mOhm contacts: hop 22.9 mOhm per conductor; worst right_ankle 5.17 V; ankles under 6 V 18.5% of the walk; BEC out mean 6.57 V
- 20 AWG leads, 2 mOhm contacts, 2 mOhm board: hop 11.0 mOhm per conductor; worst left_ankle 5.50 V; ankles under 6 V 10.4% of the walk; BEC out mean 6.56 V
- ideal hop (0 ohm): hop 0.0 mOhm per conductor; worst left_ankle 5.78 V; ankles under 6 V 2.2% of the walk; BEC out mean 6.56 V
- hop resistance at which the sim reaches the 10% gate: about 10 mOhm per conductor (linear between 0.0 and 11.0 mOhm)
- largest hop in the sweep that passes the 10% gate: 0.0 mOhm

### E7 Hip roll servo screw head vs roll_to_pitch over the hip roll range (print/check_hip_roll_screw.py): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e7_hip_roll.py`. Finished 2026-11-02 03:44 UTC, 176 s.
- left: range -25.0..25.0 deg; screw at y +45.2: worst -1.30 mm at -25.0 deg, overlap over 41 of 41 angles; screw at y +24.7: worst 0.24 mm at -25.0 deg, overlap over 0 of 41 angles
- left: the colliding screw is the outer one, as D18 says (overlap 1.30 mm)
- right: range -25.0..25.0 deg; screw at y -24.8: worst 0.16 mm at -10.0 deg, overlap over 0 of 41 angles; screw at y -45.3: worst -1.30 mm at -25.0 deg, overlap over 41 of 41 angles
- right: the colliding screw is the outer one, as D18 says (overlap 1.30 mm)

### E8 Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests): FAIL
Command: `VERIFY_OUT=<out> ODM_TEST_PYTHON=<python with rustypot, pypot> python3 altaay_lab/verify/e8_bench_pytest.py`. Finished 2026-11-02 03:47 UTC, 181 s.
- test python /tmp/claude-0/-home-user/44fe65d1-0499-57ea-a6b6-5fd56643a22c/scratchpad/agentS/venv311/bin/python: rustypot, pypot, onnxruntime, pytest importable: True
- pytest: 1 failed, 52 passed in 147.05s (0:02:27) (exit 1)
- race test test_rustypot_panic_after_checksum_error_is_caught: 1 failed of 4 runs (the suite run plus 3 alone)

### E9 Joint angles the stock policy uses in the sim walk, trained mass and our build (sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e9_joint_envelope.py`. Finished 2026-11-02 04:03 UTC, 58 s.
- stock model, cases walk_forward_0.15, turn_1.0, walk_side_0.2, walk_backlash, walk_pushes
- stock left_hip_yaw: -5.3 to +10.3 deg (MJCF range -30.0 to +30.0)
- stock left_hip_roll: -6.0 to +11.2 deg (MJCF range -25.0 to +25.0)
- stock left_hip_pitch: -49.3 to -30.1 deg (MJCF range -70.0 to +30.0)
- stock left_knee: +67.4 to +90.0 deg (MJCF range -90.0 to +90.0)
- stock left_ankle: -46.8 to -27.8 deg (MJCF range -90.0 to +90.0)
- stock neck_pitch: +5.6 to +12.5 deg (MJCF range -20.0 to +65.0)
- stock head_pitch: -10.0 to +7.1 deg (MJCF range -45.0 to +45.0)
- stock head_yaw: -13.1 to +8.2 deg (MJCF range -160.0 to +160.0)
- stock head_roll: -7.7 to +3.1 deg (MJCF range -30.0 to +30.0)
- stock right_hip_yaw: -5.8 to +5.9 deg (MJCF range -30.0 to +30.0)
- stock right_hip_roll: -12.2 to +3.6 deg (MJCF range -25.0 to +25.0)
- stock right_hip_pitch: +32.9 to +49.6 deg (MJCF range -30.0 to +70.0)
- stock right_knee: +67.8 to +90.8 deg (MJCF range -90.0 to +90.0)
- stock right_ankle: -45.9 to -27.2 deg (MJCF range -90.0 to +90.0)
- ours model, cases walk_forward_0.15, turn_1.0, walk_side_0.2, walk_backlash, walk_pushes
- ours left_hip_yaw: -5.2 to +10.4 deg (MJCF range -30.0 to +30.0)
- ours left_hip_roll: -4.3 to +10.1 deg (MJCF range -25.0 to +25.0)
- ours left_hip_pitch: -48.8 to -30.3 deg (MJCF range -70.0 to +30.0)
- ours left_knee: +67.3 to +90.7 deg (MJCF range -90.0 to +90.0)
- ours left_ankle: -47.0 to -27.6 deg (MJCF range -90.0 to +90.0)
- ours neck_pitch: +6.1 to +12.4 deg (MJCF range -20.0 to +65.0)
- ours head_pitch: -10.3 to +5.4 deg (MJCF range -45.0 to +45.0)
- ours head_yaw: -13.1 to +7.4 deg (MJCF range -160.0 to +160.0)
- ours head_roll: -7.6 to +3.1 deg (MJCF range -30.0 to +30.0)
- ours right_hip_yaw: -6.3 to +6.2 deg (MJCF range -30.0 to +30.0)
- ours right_hip_roll: -13.4 to +3.0 deg (MJCF range -25.0 to +25.0)
- ours right_hip_pitch: +33.3 to +49.9 deg (MJCF range -30.0 to +70.0)
- ours right_knee: +68.2 to +91.0 deg (MJCF range -90.0 to +90.0)
- ours right_ankle: -46.2 to -26.8 deg (MJCF range -90.0 to +90.0)

### C1 Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners): FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c1_bom_coverage.py`. Finished 2026-11-02 04:06 UTC, 1 s.
- netlist: 56 components, 13 splices (made from wire and heat shrink, BOM 26), 43 mapped to BOM lines, unmapped none
- 'BOM xx' references in the netlist text: 22, to missing lines: none
- components per BOM line vs Need: 24 lines, mismatches none
- BOM_FULL.md: 188 rows, generated 2026-11-02 03:49 UTC
- printed rows: 37 rows, 54 pieces; CAD printed nodes 52 (+ 2 antenna rods)
- horns in CAD {'horn_drive': 14, 'horn_idle': 14}, inserts 58, bearings 3
- cables: BOM_FULL 45 rows, netlist 45 active cables
- wire per gauge and colour: 15 BOM_FULL rows checked against the netlist cut sums, 0 differ
- fitted screws in fasteners.json: 342; BOM_FULL screw rows 11 (section Fasteners)
- committed BOM_FULL.md vs a fresh build from today's sources (E4, 2026-11-02 04:06 UTC): 1 quantities differ, 1 rows gone, 6 new
- heat shrink: fresh BOM_FULL 27 pieces; netlist 44 splice ends and 101 soldered ends (BOM 26 buys 1 x 180)
- purchase status from the fresh build (E4): {'printed': 38, 'bought': 77, 'in kit': 23, 'MISSING': 3, 'made': 32, 'tool': 20}
- BOM.md lines used by a BOM_FULL row: 72 of 78 (unused: ['17j', '17k', '17l', 'T11', 'T12', 'T13'])

### C2 Connectors: every wired pin has a mating part or end treatment; crimps fit the Molex 08-70-1040: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c2_connectors.py`. Finished 2026-11-02 04:04 UTC, 0 s.
- 118 wires on active cables, 236 wire ends, every end treatment checked against its pin group (21 classes)
- made-lead housings (Molex 50-37-5033): 5, SV10 bus2 3 pos, SV20 bus2 3 pos, SV30 bus2 3 pos, U2 h3 2 pos, U2 h5 2 pos; crimp terminals (08-70-1040): 13
- housings: netlist 5, BOM 21 Need 5 (Buy 10), CABLE_MAP 5, WIRING.md 5
- terminals: netlist 13, BOM 22 Need 13 (Buy 30), CABLE_MAP 13, WIRING.md 13
- mating parts and end treatment supplies on a BOM line: 9 of 9 (5264 socket, made lead: 21, 5264 socket, made lead terminal: 22, 5264 socket, kit cable: 1, XT30 cup: 12, USB-C and micro-USB: 20, camera FPC: E7, crimp tool: T3, splices and solder joints: heat shrink: 26,T10, solder joints: solder: 30)
- kit cables used 11 (S10, S11, S12, S13, S2, S3, S4, S5, S7, S8, S9) of 14 shipped (one per servo, BOM line 1)
- crimp ends by gauge: {'22 AWG': 13} (gauge range 22 to 28 AWG checked by erc.py, E1: 0 crimp findings)
- 22 AWG silicone OD 1.7 +/- 0.1 mm vs 08-70-1040 insulation max 1.9 mm ([I] listing via search index): fits, 0.1 mm left at the top of the tolerance
- connector pins not wired and not marked nc: none

### C3 Every active cable has a 3D route whose worst length plus slack fits its cut, and a service loop at every joint: FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py`. Finished 2026-11-02 04:09 UTC, 0 s.
- cables3d.json 2026-11-02 04:05 UTC: 45 cables, 100 cable ends, 111 retention items; netlist 45 active cables
- length: 107 wires checked; 6 cannot reach (worst routed length over the cut); 25 reach but with less than the 40 mm service slack of the CABLE_MAP rule (test fit); 76 have the full slack
- joint crossings: 42 free spans; 42 with a loop radius under 3 x OD (all the span's length change stored in one arc at the shortest pose)
- retention: 111 items ({'adhesive tie mount': 98, 'existing printed feature': 5, 'cable tie': 8}), 106 with no CAD feature to hold them
- cables3d's own check field: {'pass with notes': 23, 'fail': 14, 'pass': 8}

### C4a Every fitted screw has a BOM line, a length that line buys, and a count it covers (fasteners.json vs BOM.md): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py`. Finished 2026-11-02 04:08 UTC, 0 s.
- fasteners.json: 413 records, 355 screws, 342 fitted (left out: {'LEAVE OUT (D18)': 2, 'NOT FITTED': 11}), 58 inserts
- line 1 (STS3215 servo bag (18 screws per servo, B2)): 115 screws, {'M2x6 self-tapping pan head': 42, 'PA2.0 self-tapping (factory)': 56, 'M3x6 machine screw (Feetech rocker screw)': 14, 'PA3.0x5 self-tapping, washer head (Feetech idle screw)': 3}
- line 14 (SG90 bag): 6 screws, {'SG90 bag horn screw': 2, 'SG90 bag mounting screw': 4}
- line 17a M3x8 SHCS: schedule 28 (28 M3x8 DIN 912 A2); BOM Need 28, Buy 33 each
- line 17b M3x10 SHCS: schedule 12 (12 M3x10 DIN 912 A2); BOM Need 12, Buy 14 each
- line 17c M3x12 SHCS: schedule 2 (2 M3x12 DIN 912 A2); BOM Need 2, Buy 3 each
- line 17d M3x6 SHCS: schedule 78 (78 M3x6 DIN 912 A2); BOM Need 78, Buy 100 100
- line 17e M3x5 SHCS: schedule 28 (28 M3x5 DIN 912 A2); BOM Need 28, Buy 33 each
- line 17f M2.5x6 SHCS: schedule 17 (17 M2.5x6 DIN 912 A2); BOM Need 17, Buy 20 each
- line 17g M2.5x8 SHCS: schedule 8 (8 M2.5x8 DIN 912 A2 + 0.5 mm washer); BOM Need 8, Buy 10 each
- line 17h M2 self-tapping kit: schedule 30 (2 M2x8 self-tapping pan head, 22 M2x5 self-tapping pan head, 6 M2x4 self-tapping pan head); BOM Need 30 (M2x5 22, M2x4 6, M2x8 2), Buy 1 kit
- line 17i M2.5x10 SHCS: schedule 4 (4 M2.5x10 DIN 912 A2); BOM Need 4, Buy 5 each
- inserts: 58 in fasteners.json, BOM 16 Need 58

### C4b No screw head or tip collision over the joint ranges, except known, decided ones (fasteners sweep vs D18 and D19): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py`. Finished 2026-11-02 04:08 UTC, 0 s.
- sweep: 37 steps per joint, 13 joint pairs, 345 hit rows; fitted screws by status {'NEAR': 105, 'HIT': 37, 'PARTS COLLIDE FIRST': 52, 'CONTACT': 138, 'CLEAR': 10}
- screws named in a DECIDED entry of DECISIONS.md: F002 (D19), F010 (D19), F196 (D19), F198 (D19), F200 (D19), F209 (D19), F211 (D19), F213 (D19), F247 (D19), F254 (D19)
- hit rows on fitted screws by class: {'screw': 12, 'parts collide first': 134, 'static contact': 160, 'static overlap': 35}
- screw-limited and static-overlap hits by screw: button head fixes it 2; button head, under 0.3 mm 6; button head still hits 2; stand-in head (size not published) 26; against a CAD body the build replaces 1
- parts collide before the screw: 134 rows; static contact under 0.1 mm at the zero pose: 160 rows
- collision onset vs the sim walk envelope: F198: hits from left_hip_yaw +21.7 deg, the sim walk uses -5.3 to +10.4 deg (E9); F211: hits from right_hip_yaw -21.7 deg, the sim walk uses -6.3 to +6.2 deg (E9)
- D18 screws marked in fasteners.json: 2 (F124, F136)

### C5 Servo IDs agree everywhere (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime code and config, bench, sim, policy order): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c5_servo_ids.py`. Finished 2026-11-02 04:04 UTC, 0 s.
- Runtime at 376de65 (pin 376de65): left_hip_yaw 20, left_hip_roll 21, left_hip_pitch 22, left_knee 23, left_ankle 24, neck_pitch 30, head_pitch 31, head_yaw 32, head_roll 33, right_hip_yaw 10, right_hip_roll 11, right_hip_pitch 12, right_knee 13, right_ankle 14
- netlist: 14 of 14 joints match
- WIRING.md: 8 of 14 joints named, all match (the others appear only as IDs in the chain list)
- CABLE_MAP.md: 14 of 14 joints match
- viewer: 14 of 14 joints match
- BOM_FULL.md: 14 of 14 joints match
- runtime configure_all_motors: 14 of 14 joints match
- bench joints.py: 14 of 14 joints match
- netlist chains: SP1 [20, 21, 22, 23, 24], SP2 [10, 11, 12, 13, 14], SP3 [30, 31, 32, 33]
- wiring chains: SP1 [20, 21, 22, 23, 24], SP2 [10, 11, 12, 13, 14], SP3 [30, 31, 32, 33]
- bench CHAINS match the netlist: True
- power sim chain order matches the netlist chains: True
- policy action order: MJCF actuators == Runtime self.joints order == init_pos order: True
- software/duck_config.altaay.json: 14 joint offsets, names match the Runtime

### C6 GPIO pins agree (netlist, WIRING.md section 3, CABLE_MAP, HARNESS_BUILD, D9, Runtime code at 376de65): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c6_gpio.py`. Finished 2026-11-02 04:04 UTC, 0 s.
- Runtime 376de65 / Pi hardware: left foot GPIO22, right foot GPIO27, left eye GPIO24, right eye GPIO23, projector GPIO25, left antenna GPIO13, right antenna GPIO12, I2C SDA GPIO2, I2C SCL GPIO3, I2S BCLK GPIO18, I2S LRC GPIO19, I2S DIN GPIO21
- netlist: 12 of 12 functions on the Runtime GPIO and the right header pin
- WIRING.md: 12 of 12 functions on the Runtime GPIO and the right header pin
- D9: 7 of 7 functions on the Runtime GPIO and the right header pin
- CABLE_MAP.md: 7 of 7 functions on the Runtime GPIO and the right header pin
- HARNESS_BUILD.md: 12 of 12 functions on the Runtime GPIO and the right header pin
- netlist header pins used for signals: 3 I2C SDA, 5 I2C SCL, 12 I2S BCLK, 13 right foot, 15 left foot, 16 right eye, 18 left eye, 22 projector, 32 right antenna, 33 left antenna, 35 I2S LRC, 40 I2S DIN

### C7 Current ratings: every wire, contact and power part vs the simulated currents (sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py`. Finished 2026-11-02 03:37 UTC, 0 s.
- traces: walk_backlash, walk_rough_backlash, walk_pushes, walk_side_0.2, turn_1.0 (E5 run); servo supply current = positive electrical power / 6.0 V + 0.05 A quiescent (an upper estimate; on the 7.4 V basis of CURRENT_BUDGET.md the currents are 0.81 x these)
- SP1 (22 AWG): mean 1.92 A, worst 100 ms 3.35 A, 20 ms 5.67 A, 2 ms 7.08 A; limit 7.0 A (22 AWG)
- S2 (kit cable, assumed 26 AWG): mean 1.84 A, worst 100 ms 3.28 A, 20 ms 5.62 A, 2 ms 7.01 A; limit 2.2 A (26 AWG)
- S3 (kit cable, assumed 26 AWG): mean 1.65 A, worst 100 ms 2.97 A, 20 ms 5.27 A, 2 ms 6.59 A; limit 2.2 A (26 AWG)
- S4 (kit cable, assumed 26 AWG): mean 1.30 A, worst 100 ms 2.28 A, 20 ms 4.15 A, 2 ms 5.17 A; limit 2.2 A (26 AWG)
- S5 (kit cable, assumed 26 AWG): mean 0.40 A, worst 100 ms 1.32 A, 20 ms 2.47 A, 2 ms 2.89 A; limit 2.2 A (26 AWG)
- SP3 (22 AWG): mean 0.85 A, worst 100 ms 1.52 A, 20 ms 2.88 A, 2 ms 3.76 A; limit 7.0 A (22 AWG)
- S11 (kit cable, assumed 26 AWG): mean 0.76 A, worst 100 ms 1.44 A, 20 ms 2.80 A, 2 ms 3.67 A; limit 2.2 A (26 AWG)
- S12 (kit cable, assumed 26 AWG): mean 0.46 A, worst 100 ms 1.09 A, 20 ms 2.36 A, 2 ms 3.12 A; limit 2.2 A (26 AWG)
- S13 (kit cable, assumed 26 AWG): mean 0.19 A, worst 100 ms 0.61 A, 20 ms 1.32 A, 2 ms 1.46 A; limit 2.2 A (26 AWG)
- SP2 (22 AWG): mean 1.93 A, worst 100 ms 4.03 A, 20 ms 5.84 A, 2 ms 7.40 A; limit 7.0 A (22 AWG)
- S7 (kit cable, assumed 26 AWG): mean 1.83 A, worst 100 ms 3.91 A, 20 ms 5.68 A, 2 ms 7.26 A; limit 2.2 A (26 AWG)
- S8 (kit cable, assumed 26 AWG): mean 1.68 A, worst 100 ms 2.98 A, 20 ms 5.09 A, 2 ms 6.36 A; limit 2.2 A (26 AWG)
- S9 (kit cable, assumed 26 AWG): mean 1.42 A, worst 100 ms 2.62 A, 20 ms 4.37 A, 2 ms 5.21 A; limit 2.2 A (26 AWG)
- S10 (kit cable, assumed 26 AWG): mean 0.30 A, worst 100 ms 0.99 A, 20 ms 1.67 A, 2 ms 2.34 A; limit 2.2 A (26 AWG)
- D15 ground network, SP1 G: mean 1.75 A, worst 100 ms 2.78 A (walk_backlash; 71% of a left-leg return goes this way)
- D15 ground network, SP2 G: mean 1.86 A, worst 100 ms 2.72 A (walk_backlash; 10% of a left-leg return goes this way)
- D15 ground network, SP3 G: mean 1.09 A, worst 100 ms 1.50 A (walk_backlash; 19% of a left-leg return goes this way)
- D15 ground network, SD1 a G: mean 0.34 A, worst 100 ms 0.61 A (walk_backlash; 29% of a left-leg return goes this way)
- D15 ground network, SD1 b G: mean 0.30 A, worst 100 ms 0.59 A (walk_backlash; 19% of a left-leg return goes this way)
- D15 ground network, SD1 stem G (adapter H3 G terminal): mean 0.18 A, worst 100 ms 0.35 A (walk_backlash; 10% of a left-leg return goes this way)
- D15 ground network, SD2 G (adapter H5 G terminal): mean 0.18 A, worst 100 ms 0.35 A (walk_backlash; 10% of a left-leg return goes this way)
- D15 ground network, adapter ground copper H3 G to H5 G: mean 0.18 A, worst 100 ms 0.35 A (walk_backlash; 10% of a left-leg return goes this way)
- ngspice star cases (E6): pack mean up to 5.61 A, RMS up to 5.84 A, max (2 ms) 11.11 A; BEC out mean up to 4.14 A, max 9.14 A
- fuse 15 A ATO (F1): 5.84 A (RMS vs 75% of rating ([I] Littelfuse derating rule of thumb, not read this session)) vs 11.25 A, margin 48%
- fuse holder 20 A (F1): 5.84 A (RMS) vs 20.00 A, margin 71%
- BMS working current (Tenergy 10 A): 5.84 A (RMS) vs 10.00 A, margin 42%
- BMS over-current trip, lowest of 22 +/- 5 A: 11.11 A (2 ms max) vs 17.00 A, margin 35%
- main switch Pololu 2815, 6 A at 55 C MOSFETs: 5.84 A (RMS) vs 6.00 A, margin 3%
- main switch Pololu 2815, 16 A at 150 C: 11.11 A (2 ms max) vs 16.00 A, margin 31%
- XT30U 15 A: 5.84 A (RMS) vs 15.00 A, margin 61%
- cells 30 A continuous each: 11.11 A (2 ms max) vs 30.00 A, margin 63%
- BEC 20 A peak: 9.14 A (2 ms max) vs 20.00 A, margin 54%
- BEC 15 A continuous (with 5 mph air): 4.14 A (mean) vs 15.00 A, margin 72%
- BEC output leads, 5 A per 3-pin lead, 2 leads: 2.07 A (mean per lead; 2 ms max 4.57 A) vs 5.00 A, margin 59%
- stacked fall estimate (CURRENT_BUDGET.md): about 17 A for about 20 ms vs BMS trip 17 to 27 A after 4 to 12 ms
- adapter U2: 5 wires, 0 on a power net (D15: none)

### C8 The stock policy walks the robot we will build (2.77 kg) on flat ground (sim/added_mass_sim.py, sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c8_policy_mass.py`. Finished 2026-11-02 03:41 UTC, 214 s.
- model mass: stock 2.1071 kg (trained 2.107 kg), ours 2.7669 kg (MASS_BUDGET.md 2.77 kg)
- stock copy reproduces the CURRENT_BUDGET.md bus means in 7 of 7 cases
- ours, Stand, zero command: falls none; tracking - (doc -); seeds fell not run (stand)
- ours, Walk forward 0.15 m/s: falls none; tracking 0.67 (doc 0.67); seeds fell 0 of 6
- ours, Turn 1.0 rad/s: falls none; tracking 0.78 (doc 0.79); seeds fell 0 of 6
- ours, Walk sideways 0.2 m/s: falls none; tracking 0.23 (doc 0.23); seeds fell 0 of 6
- ours, Walk forward, backlash model: falls none; tracking 0.88 (doc 0.88); seeds fell 0 of 6
- ours, Walk forward, 15 N pushes every 3 s: falls none; tracking 0.61 (doc 0.62); seeds fell 0 of 6
- rough terrain, start raised 23 mm: stock falls [9.14], ours falls [4.58] (not a flat-ground case; ADDED_MASS_SIM.md finding 4)

### C9 Docs agree: numbers that appear in several docs are the same everywhere: FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c9_docs.py`. Finished 2026-11-02 04:09 UTC, 2 s.
- HARDWARE_AUDIT.md section 6: 32 blockers; cleared or decided 19; test print 5; open 8 (6 assembly or bench, 2 waiting on parts: B8, B18)
- blocker count mentions checked: 10
- 'Bnn cleared' mentions outside HARDWARE_AUDIT.md: 10
- BOM.md: build 890.19, with expression 972.59, with tools 1220.76; test order 226.46
- totals quoted as current outside BOM.md: 0 checked
- part counts (viewer run E4): printed parts 52/52, servos 14/14, inserts 58/58, bearings 3/3
- print/ STL files: 36
- screws: HARDWARE_AUDIT B1 189; BOM.md screw lines 17a/b/c/d/e/f/g/i/h/j/k Need 221; fasteners.json 221 bought (17x lines and no line) of 342 fitted; MASS_BUDGET.md model 274
- decisions: DECISIONS.md last is D21
- upstream items: UPSTREAM_ISSUES.md total 137
- WIRING.md section 4 currents vs netlist: 32 values compared
- STATE.md print numbers (5.0, 27.8, 18.2, 126.4, 1474.5, 18.1, 1372.7, 114.4) found in print/PRINT_PLAN.md, SLICE_SUMMARY.md or PRINT_CHECK.md: 8 of 8

### C10 Wiring sheets cover every wire of the netlist (wiring/sheets, run on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c10_sheets.py`. Finished 2026-11-02 04:06 UTC, 34 s.
- make_sheets.py on a copy: exit 0; sheet 1: 1_power.png 802903 bytes, svg 497972 bytes, full 35, stubs 0, crossings 1; sheet 2: 2_servo_bus.png 782690 bytes, svg 494876 bytes, full 44, stubs 7, crossings 1; sheet 3: 3_pi_sensors.png 801838 bytes, svg 467598 bytes, full 17, stubs 16, crossings 1; sheet 4: 4_head_expression.png 620552 bytes, svg 390537 bytes, full 25, stubs 0, crossings 6; sheet 5: 5_harness.png 856260 bytes, svg 531172 bytes, full 0, stubs 0, crossings 6
- sheets built: 1 1_power (full 35, stubs 0), 2 2_servo_bus (full 44, stubs 7), 3 3_pi_sensors (full 17, stubs 16), 4 4_head_expression (full 25, stubs 0), 5 5_harness (full 0, stubs 0); active wires drawn in full: 118 of 118
- committed sheet SVGs: 5, older than netlist.yaml: none

### C11 Hip yaw the stock policy uses (walk and turn) stays under the F198/F211 collision onset (21.7 deg): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c11_hip_yaw_envelope.py`. Finished 2026-11-02 04:08 UTC, 1 s.
- collision onset: FASTENERS.md 21.7, 21.7 deg; fasteners.json sweep F198 left_hip_yaw from 21.7 deg, F211 right_hip_yaw from 21.7 deg; used 21.7 deg
- ours, turn_1.0: largest |hip yaw| 10.4 deg (largest |target| 8.9 deg; largest |action| 0.61 left, 0.50 right)
- ours, walk_backlash: largest |hip yaw| 5.6 deg (largest |target| 4.5 deg; largest |action| 0.28 left, 0.33 right)
- ours, walk_forward_0.15: largest |hip yaw| 5.6 deg (largest |target| 4.3 deg; largest |action| 0.28 left, 0.31 right)
- ours, walk_pushes: largest |hip yaw| 5.6 deg (largest |target| 5.1 deg; largest |action| 0.35 left, 0.31 right)
- ours, walk_side_0.2: largest |hip yaw| 5.6 deg (largest |target| 4.7 deg; largest |action| 0.27 left, 0.34 right)
- stock, turn_1.0: largest |hip yaw| 10.3 deg (largest |target| 9.0 deg; largest |action| 0.62 left, 0.49 right)
- stock, walk_backlash: largest |hip yaw| 5.6 deg (largest |target| 4.7 deg; largest |action| 0.30 left, 0.34 right)
- stock, walk_forward_0.15: largest |hip yaw| 5.6 deg (largest |target| 4.5 deg; largest |action| 0.27 left, 0.33 right)
- stock, walk_pushes: largest |hip yaw| 5.6 deg (largest |target| 5.3 deg; largest |action| 0.36 left, 0.33 right)
- stock, walk_side_0.2: largest |hip yaw| 5.6 deg (largest |target| 4.8 deg; largest |action| 0.26 left, 0.35 right)
- the joint passes its commanded target by up to 1.5 deg in the sim (dynamics)
- worst over 10 runs: 10.4 deg (ours, turn_1.0); turn 1.0 rad/s: stock 10.3 deg, ours 10.4 deg; margin to the 21.7 deg onset: 11.3 deg
- policy output on 6000 random observations (scale 1, 3, 10): largest |action| 1.0000 (bounded by 1, as a tanh output is); hip yaw target bound = default 0.2 deg + 0.25 x 1 rad = 14.5 deg
- the stock policy cannot command more than 14.5 deg of hip yaw (16.0 deg with the sim overshoot), 5.7 deg under the onset
- Runtime 376de65: motor target = init_pos + action x action_scale at line 290; live clip of the targets: none; commented-out clip at lines [292]; servo angle limit registers set by configure_motor.py or the HWI: False

## Inputs read (sha256, first 10 hex, and file time)

| File | sha256 | Modified |
|---|---|---|
| BEST_WALK_ONNX_2.onnx | 3c606f9381 | 2026-11-01 22:31 UTC |
| altaay_lab/BOM.md | 4ae5209d91 | 2026-11-02 03:58 UTC |
| altaay_lab/BOM_FULL.md | abbe83b638 | 2026-11-02 03:49 UTC |
| altaay_lab/CABLE_MAP.md | 82b6ee7f45 | 2026-11-02 00:28 UTC |
| altaay_lab/DECISIONS.md | 50cc6254fc | 2026-11-02 03:50 UTC |
| altaay_lab/GAPS.md | da0dbbc6f1 | 2026-11-02 00:32 UTC |
| altaay_lab/HARDWARE_AUDIT.md | 531652d2b0 | 2026-11-02 03:56 UTC |
| altaay_lab/HARNESS_BUILD.md | 9f9e7203a7 | 2026-11-02 03:49 UTC |
| altaay_lab/MOUNTING.md | feb6951425 | 2026-11-02 03:53 UTC |
| altaay_lab/POWER.md | 7fb8347366 | 2026-11-01 23:58 UTC |
| altaay_lab/PRINT_CHECK.md | fa081ab8c4 | 2026-11-02 00:28 UTC |
| altaay_lab/README.md | 9135e1a007 | 2026-11-01 22:32 UTC |
| altaay_lab/REFERENCES.md | 5f2b55fea3 | 2026-11-01 22:32 UTC |
| altaay_lab/SERVO_DEEP_DIVE.md | a691edab2c | 2026-11-01 23:58 UTC |
| altaay_lab/SERVO_UPGRADE_OPTIONS.md | 9e2c4241d7 | 2026-11-02 03:53 UTC |
| altaay_lab/SOURCING_2026-11-02.md | 49aca9c97a | 2026-11-02 02:44 UTC |
| altaay_lab/START_HERE.md | a4d2a24b3d | 2026-11-02 03:57 UTC |
| altaay_lab/STATE.md | 5e2d37fe35 | 2026-11-02 00:32 UTC |
| altaay_lab/TEST_PLAN.md | 95b71d2585 | 2026-11-02 03:57 UTC |
| altaay_lab/UPSTREAM_ISSUES.md | 684a28bb66 | 2026-11-01 23:38 UTC |
| altaay_lab/WIRING.md | b2823a5c0e | 2026-11-02 00:28 UTC |
| altaay_lab/audit/ERC_REPORT.md | 48604c09e2 | 2026-11-02 03:49 UTC |
| altaay_lab/audit/assembly.json | c6abbf8060 | 2026-11-01 22:32 UTC |
| altaay_lab/audit/bom_md_to_json.py | 5eacb7950e | 2026-11-01 23:28 UTC |
| altaay_lab/audit/bom_totals.py | 6421478207 | 2026-11-02 00:24 UTC |
| altaay_lab/audit/continuity_checklist.csv | d956c6e507 | 2026-11-02 03:49 UTC |
| altaay_lab/audit/erc.py | 8691d4dd1e | 2026-11-02 03:13 UTC |
| altaay_lab/audit/placements.json | 3d1fffdbfe | 2026-11-02 03:53 UTC |
| altaay_lab/audit/sites.json | 634ba3278a | 2026-11-01 22:32 UTC |
| altaay_lab/bench/odm_bench/joints.py | 266c4a84c3 | 2026-11-02 02:26 UTC |
| altaay_lab/bench/tests/conftest.py | fdc9914545 | 2026-11-02 02:50 UTC |
| altaay_lab/bench/tests/fake_sts3215.py | b97fcc0cef | 2026-11-02 03:11 UTC |
| altaay_lab/bench/tests/test_battery_guard.py | ab7038eb4c | 2026-11-02 03:00 UTC |
| altaay_lab/bench/tests/test_crosscheck.py | 81d8308ac8 | 2026-11-02 03:04 UTC |
| altaay_lab/bench/tests/test_feet_check.py | 2263e58494 | 2026-11-02 03:29 UTC |
| altaay_lab/bench/tests/test_first_servo_check.py | b157bb2cd3 | 2026-11-02 02:55 UTC |
| altaay_lab/bench/tests/test_imu_check.py | 28193f99da | 2026-11-02 03:02 UTC |
| altaay_lab/bench/tests/test_power_log.py | 2f319ab758 | 2026-11-02 03:02 UTC |
| altaay_lab/bench/tests/test_protocol.py | 3e5298a2b2 | 2026-11-02 02:47 UTC |
| altaay_lab/bench/tests/test_thermal_guard.py | fb682126c4 | 2026-11-02 03:12 UTC |
| altaay_lab/bom.json | 9cfad29f7a | 2026-11-02 03:58 UTC |
| altaay_lab/cables3d/CABLES_3D.md | 8cb80498f5 | 2026-11-02 04:07 UTC |
| altaay_lab/cables3d/VIEWER_NOTE.md | 4557d84de7 | 2026-11-02 03:53 UTC |
| altaay_lab/cables3d/cables3d.json | e0bfe6ad02 | 2026-11-02 04:07 UTC |
| altaay_lab/fasteners/FASTENERS.md | ea55c7ccd7 | 2026-11-02 03:24 UTC |
| altaay_lab/fasteners/VIEWER_NOTE.md | af30b4f52d | 2026-11-02 03:05 UTC |
| altaay_lab/fasteners/fasteners.json | 699d4b8fdc | 2026-11-02 03:24 UTC |
| altaay_lab/print/MASS_STUDY.md | 537840e439 | 2026-11-02 04:00 UTC |
| altaay_lab/print/PRINT_PLAN.md | ba1851332d | 2026-11-02 03:56 UTC |
| altaay_lab/print/SLICE_SUMMARY.md | 4cc65d8bd9 | 2026-11-02 00:28 UTC |
| altaay_lab/print/check_hip_roll_screw.py | c299d6623a | 2026-11-01 23:47 UTC |
| altaay_lab/print/parts.csv | 0b3ecec74d | 2026-11-01 23:53 UTC |
| altaay_lab/sim/ADDED_MASS_SIM.md | c24b78cc74 | 2026-11-02 02:59 UTC |
| altaay_lab/sim/CURRENT_BUDGET.md | 681e49233d | 2026-11-01 23:58 UTC |
| altaay_lab/sim/MASS_BUDGET.md | a6979cf1fd | 2026-11-02 02:59 UTC |
| altaay_lab/sim/POWER_PATH_SIM.md | 29d25b0c90 | 2026-11-01 23:45 UTC |
| altaay_lab/sim/RUNTIME_THERMAL.md | 3a33998dd7 | 2026-11-02 02:52 UTC |
| altaay_lab/sim/SIM_WALK.md | b83d1a4a3c | 2026-11-01 23:58 UTC |
| altaay_lab/sim/added_mass_sim.py | a5667b4b87 | 2026-11-02 02:38 UTC |
| altaay_lab/sim/current_budget.py | cebc433639 | 2026-11-01 23:40 UTC |
| altaay_lab/sim/mass_budget.py | 6d4bc561de | 2026-11-02 02:35 UTC |
| altaay_lab/sim/power_path_sim.py | ee3542021f | 2026-11-02 02:24 UTC |
| altaay_lab/software/PI_SETUP.md | 25059e8925 | 2026-11-02 03:20 UTC |
| altaay_lab/software/SOFTWARE.md | 22cecbb3f6 | 2026-11-02 03:32 UTC |
| altaay_lab/software/duck_config.altaay.json | 249171e913 | 2026-11-02 02:38 UTC |
| altaay_lab/viewer/MISSING_3D.md | aa05ca83cd | 2026-11-02 03:16 UTC |
| altaay_lab/viewer/README.md | 193884c458 | 2026-11-01 23:47 UTC |
| altaay_lab/viewer/make_viewer_data.py | 40803d703a | 2026-11-02 03:53 UTC |
| altaay_lab/wiring/netlist.yaml | 99aa6391fc | 2026-11-02 00:26 UTC |
| altaay_lab/wiring/sheets/make_sheets.py | 87c4f4bfd0 | 2026-11-02 03:58 UTC |
| altaay_lab/wiring/sheets/sheetlib.py | 603ae4ea42 | 2026-11-02 03:57 UTC |
