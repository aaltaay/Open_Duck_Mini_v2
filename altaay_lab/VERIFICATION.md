# VERIFICATION: every check that runs without the robot

Generated 2026-11-06 9:09 PM ET by altaay_lab/verify/report.py from one run of `bash altaay_lab/verify/run_all.sh` (results kept outside the repo). Written by agent Q (verification) for Ahmed's Open Duck Mini v2 build. Every simulation result here is sim pass only. Nothing was bought, built or printed; no lab file was edited by these checks (each script that writes files was run on a copy or into the results folder).

## Summary
23 checks: **21 PASS, 2 FAIL, 0 NOT RUN**. 2 FAIL findings and 42 WARN findings in all (below). PASS means no FAIL finding; a PASS row can still carry WARN findings (risks, test fits, notes).

How to run (from the repo root): `bash altaay_lab/verify/run_all.sh` runs everything (this run: 5 minutes of check time on the shared 4-CPU box, sims under nice -n 10); `--quick` skips the MuJoCo, ngspice and CAD sweep runs and reuses earlier results in the same folder. Settings: VERIFY_OUT (results folder outside the repo), ODM_RUNTIME (Open_Duck_Mini_Runtime at 376de65), ODM_PLAYGROUND (Open_Duck_Playground at b9be205), ODM_TEST_PYTHON (a Python with rustypot and pypot for the bench tests). Each check also runs alone: the command is in the matrix.

Run notes:

- Run 2026-11-02 by agent SFX for the lead, the last full run for PR 6, after the C8 and E6b fixes (sim/MASS_BUDGET.md and the print/MASS_STUDY.md (c) walk re-run on today's model; TEST_PLAN.md section 5 in three bands, lead decision L3), the as-built power path re-run (sim/POWER_PATH_SIM.md) and the cable 'test fit' label (cables3d/check_cables.py; viewer data and BOM_FULL rebuilt). This page comes from one full run, 6:19 to 6:32 AM ET (VERIFY_OUT in the agent's scratch folder, ODM_TEST_PYTHON as in the integration run); C9 ran again at 6:33 AM ET after the STATE.md and START_HERE.md lines with these counts, and C4 and C6 at 6:35 AM ET and C8, E6, C7 and E6b in full at 6:36 to 6:40 AM ET after the time stamps in the agent's dated doc lines were set to the real edit times, with the same results. The input table at the end gives the time of every file read.
- Changed for this run (verify/): e6b_hop_sweep.py reads the TEST_PLAN.md section 5 bands of lead decision L3 (DECISIONS.md D23 note): at the pass gate ('Gate: 28 mOhm per conductor') every section 9 gate must hold, else FAIL; at the warn limit ('Fail: over 40 mOhm per conductor') time under 6 V over the gate is a WARN with the knee, head roll and ankle numbers, and a servo under 4.5 V a FAIL. report.py: these notes and the section 4 and 5 hardware rows. No check was loosened: C8 still compares with 0.011, and E6b's gates are those of TEST_PLAN.md section 9.
- Why the 2 FAILs of the integration run are gone. C8: its doc is current again. sim/mass_budget.py gives 2652.8 g (MASS_BUDGET.md updated; +0.9 g of wire from agent CAB's later cut changes) and the (c) walk of print/MASS_STUDY.md was re-run with mass_study.py walk on that model (the slice table of print/SLICE_SUMMARY.md, the D22 print as adopted). Against the study's run the nominal runs moved by 0.004 or less, pushes by 0.013 (0.631 to 0.618); with the study's own slice table (0.01 g more on one part) the same script gives 0.626, and the 6 seeded pushes runs span 0.614 to 0.629: run-to-run noise, 0 falls on flat ground. E6b: TEST_PLAN 5 now passes a hop only up to 28 mOhm per conductor, the largest whole value at which every servo meets section 9 in sim (our build: right knee 9.9 % under 6 V at 28 mOhm, 10.2 % at 29); at the 40 mOhm warn limit the right knee is under 6 V for 13.4 % of the walk (WARN: the walking log decides and the 3S plan is made ready).
- E6 and C7 check the robot as wired: D15 plus the D23 feeds SP4 and SP5, every length and gauge read from wiring/netlist.yaml at run time (sim/power_path_sim.py topology as_built, which runs sim/power_fix.py option ab), on the trained-mass (E5) and our-build (C8) traces; E6b sweeps the hop on the same network. sim/POWER_PATH_SIM.md 'As built' is the run on today's netlist (SP4 400 mm, SP5 430 mm): our build, nominal pack, typical corner, ankles 6.4 % and right knee 9.8 % under 6 V; Pololu 2815 RMS 5.93 A. C3 judges the cable lengths itself, by chain through floating splices with the twist take-up; cables3d.json now marks D12, S2 and S7 'test fit' (they reach, with less than the 40 mm slack), which C3 reports as WARN as before. E8 passed in this run (63 tests in 221.6 s; the race test failed 0 of 4 runs).
- Note 2026-11-03, for C8, from the twin integration (not from a verify run; history/2026-11-03_1524_duck_gym_overlay.md; sim pass only): the 0 falls and the side step of 0.24 above hold only in the duck's training physics (2 ms Euler, Newton with 1 iteration, pyramidal cone, floor friction 0.6). In the shared lab gym (overlay gym/overlays/duck) an independent copy of the loop gives these numbers to the digit on the Playground scene; there a 1 ms time step alone moves our build's side step from 0.24 to 0.48 of the command and makes the 15 N pushes case fall (13.8 s, after the 4th push, a push to the right), each of four other single solver or contact settings does the same (13.7 to 13.9 s), and the gym's frozen floor profile (1 ms, implicitfast, elliptic cone with impratio 5, floor friction 1.0) falls in 6 of 6 seeds. The push result is marginal, not a margin; the real floor friction is HARDWARE_AUDIT.md B41. The home keyframe starts the soles 12.4 to 16.9 mm inside the floor (sim/ADDED_MASS_SIM.md gym note).

## Main findings

Checks that fail, with their numbers (fixes are in the FAIL section below):

- **E6** Power path to every servo as wired now: D15 star plus the D23 ankle feeds SP4 and SP5, lengths and gauges from wiring/netlist.yaml (sim/power_path_sim.py as_built, ngspice, sim pass only): as built, nominal pack, worse of trained mass (E5) and our build (C8): lowest servo 5.57 V typical (left knee), 4.87 V high-side (head roll); servo under 6 V 11.2 % typical, 35.2 % high-side, counted in time (gate 10 %); no servo under 4.5 V at full or nominal in either corner: True
- **E6b** TEST_PLAN.md section 5 hop gate is enough for the section 9 gates, wiring as built (D15 plus the D23 feeds, netlist lengths; power path sim sweep, sim pass only): as built (SP4 and SP5 in the netlist): ankle under 6 V at a nominal pack, worse trace: 17.6 mOhm 6.4%, 27.6 mOhm 7.8%, 28.0 mOhm 7.9%, 40.0 mOhm 9.4%, 57.6 mOhm 11.0%, 77.6 mOhm 12.5%; at the 28 mOhm pass gate the ankle 7.9 % (our build (C8)), worst servo of any kind right knee 11.3 %, lowest servo 5.57 V; at the 40 mOhm warn limit knees 10.8 / 14.0 %, ankle 9.4 % (our build (C8)), lowest servo 5.46 V

Passing checks that still carry risks to measure on the bench (WARN):

- **E7**: left: the inner screw D18 keeps clears roll_to_pitch by only 0.24 mm (worst at -7.2 deg), inside normal print tolerance (and 1 more)
- **E8**: 36 tests skipped: Runtime checkout or its adafruit_bno055 dependency not found; rustypot 0.1.0 and pypot not installed; walk needs rustypot, pypot, onnxruntime, the policy and the Runtime
- **C2**: 2 wire ends on a connector this check has no rule for: 'solder leads' (and 2 more)
- **C3**: D10: 1 wire(s) reach with only 40 mm to spare (worst chain D10 PI.36>AMP.SD 220, 180 mm routed, cut 220 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) (and 6 more)
- **C4b**: 2 screws still hit with the button head, known and left as a joint range point in D19 (not fixed): F211 M3x6 ISO 7380 A2 button head vs body_middle_bottom at right_hip_yaw -30.0, -0.82 mm, -0.82 mm with the button head; F198 M3x6 ISO 7380 A2 button head vs bod (and 3 more)
- **C7**: D15 says no servo current through the adapter, but the data-lead grounds make it a parallel return path: as built 0.35 A worst 100 ms through SD2 G (adapter H5 G terminal) (DC split, 6.0 V currents); ngspice 0.15 A worst 100 ms in the adapter H3 G lead; harmle (and 2 more)
- **C8**: no doc records the walk of this model mass within 1 % (2.7881 kg): sim/ADDED_MASS_SIM.md ran 2.75 kg, print/MASS_STUDY.md (c) 2.6387 kg
- **C9**: sim/MASS_BUDGET.md models 274 screws, fasteners.json fits 324 (the screw mass, 175 g, is from the older count) (and 11 more)
- **C11**: nothing in the Runtime limits hip yaw: the policy bound keeps the walk under the onset, but a manual move, find_soft_offsets.py (Runtime issue 32 moves every joint) or a fall can still reach 21.7 to 30 deg and press the F198/F211 heads into body_middle_bottom
- **C12**: tipping, a child's bump or pull at the mast top, +x (toward the back): tips at 5.0 N (5 N gives 1.0x): a wall strap or a lower mast, Ahmed's call (and 4 more)

## Matrix

| # | Check | How it runs | Result | Evidence (numbers) | Covers | Does not cover |
|---|---|---|---|---|---|---|
| E1 | Electrical rule check of the netlist (audit/erc.py) plus mutation test | `VERIFY_OUT=<out> python3 altaay_lab/verify/e1_erc.py` | **PASS** | 0 ERROR, 0 WARN on 75 components and 171 wires; committed report and beep list current: True; injected faults caught: 10 of 10 (details below) | References, pin use, shorts between nets, voltage domains of 'in', 'bidir' and 'pwr_in' pins, ampacity of wires that carry a current in the netlist, Molex 08-70-1040 crimp gauge, 5264 connector match; committed report is current; 10 injected faults | Wires with no current in the netlist (see C7); anything not written in netlist.yaml |
| E2 | BOM.md subtotals, totals and test order total (audit/bom_totals.py on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py` | **PASS** | recompute changes nothing: build $1258.7, + expression $1387.84, + tools $1659.5, test order $228.49 (details below) | Every section subtotal, the Totals table and the test order total recomputed from the line items; Buy >= Need on every line where both count the same unit | Whether the prices are still current (read 2026-11-01); quantities themselves (C1, C4) |
| E3 | bom.json rebuilt from BOM.md (audit/bom_md_to_json.py on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py` | **PASS** | 105 rows rebuilt, identical to the committed bom.json: True (details below) | bom.json has the same rows and values as BOM.md (57 purchase lines) | BOM.md content itself |
| E4 | Exploded-view data build and its CAD count checks (viewer/make_viewer_data.py) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e4_viewer.py` | **PASS** | found in the CAD: printed parts 62/62, servos 14/14, inserts 48/48, bearings 3/3; drawn and counted: eye washers 8/8, heat shrink sleeves 42/42 (details below) | URDF zero pose with print/ STLs swapped in; printed parts, servos, inserts, bearings found vs expected; STL vs URDF frame check; BOM lines with a view mapping; eye washers drawn vs fasteners.json; heat shrink sleeves drawn vs the BOM_FULL count | Fit of parts not in the CAD beyond their boxes; anything the page shows but does not count |
| E5 | Servo current budget from the stock walk (sim/current_budget.py, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e5_current_budget.py` | **PASS** | 7 of 7 cases reproduce CURRENT_BUDGET.md; backlash walk 3.24 A mean, 4.72 A worst 100 ms; worst servo 3.33 A (details below) | 7 MuJoCo cases (stand, walk, turn, side, backlash, rough, pushes) with BEST_WALK_ONNX_2; every number of the CURRENT_BUDGET.md table (falls, mean, 1 s, 100 ms, 20 ms, 2 ms, whole-run max) and the worst single servo | Real servos (issue 48: real tracking differs); the 5 V branch and pack side (hand calculation in the doc) |
| E6 | Power path to every servo as wired now: D15 star plus the D23 ankle feeds SP4 and SP5, lengths and gauges from wiring/netlist.yaml (sim/power_path_sim.py as_built, ngspice, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py` | **FAIL (1 FAIL, 1 WARN)** | as built, nominal pack, worse of trained mass (E5) and our build (C8): lowest servo 5.57 V typical (left knee), 4.87 V high-side (head roll); servo under 6 V 11.2 % typical, 35.2 % high-side, counted in time (gate 10 %); no servo under 4.5 V at full or nominal in either corner: True (details below) | As-built network (P1 to P14 pack side, BEC, P11, SP1 to SP5, 11 kit hops, data-lead grounds) read from the netlist; full, nominal and low pack x typical and high-side resistances, fall after a push; trained mass (E5) and our build (C8); TEST_PLAN.md section 9 gates counted in time; lowest servo per chain; the as-built table of POWER_PATH_SIM.md reproduced | Real hop and contact resistance (TEST_PLAN.md section 5), BEC dropout (section 4.1), bus capacitance, regenerative braking, the servo electronics' brown-out point; the 5 V branch in detail |
| E6b | TEST_PLAN.md section 5 hop gate is enough for the section 9 gates, wiring as built (D15 plus the D23 feeds, netlist lengths; power path sim sweep, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py` | **FAIL (1 FAIL, 2 WARN)** | as built (SP4 and SP5 in the netlist): ankle under 6 V at a nominal pack, worse trace: 17.6 mOhm 6.4%, 27.6 mOhm 7.8%, 28.0 mOhm 7.9%, 40.0 mOhm 9.4%, 57.6 mOhm 11.0%, 77.6 mOhm 12.5%; at the 28 mOhm pass gate the ankle 7.9 % (our build (C8)), worst servo of any kind right knee 11.3 %, lowest servo 5.57 V; at the 40 mOhm warn limit knees 10.8 / 14.0 %, ankle 9.4 % (our build (C8)), lowest servo 5.46 V (details below) | As-built network (sim/power_fix.py option ab = 3b with the netlist lengths and gauges and the data-lead grounds); nominal pack, typical source resistances; hop = kit cable conductor + 2 contacts + servo board; both section 9 gates (4.5 V at any time, time under 6 V counted in time) per hop value, at the section 5 pass gate and at its warn limit; trained mass and our build traces; the section 5 'holds to about N mOhm' figure | Real BEC dropout (TEST_PLAN.md section 4), real hop resistance (section 5), the high-side pack side (sections 3.2 and 4.1 gate it), regenerative braking, bus capacitance |
| E7 | Hip roll servo screw head vs roll_to_pitch over the hip roll range (print/check_hip_roll_screw.py) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e7_hip_roll.py` | **PASS (0 FAIL, 2 WARN)** | outer screw overlaps the arm by 1.3 and 1.3 mm at every hip roll angle on both legs (as D18); the inner screw that stays clears it by 0.16 and 0.24 mm (details below) | Both legs, 2 screws each, 41 angles over the URDF hip roll range, M2 pan head 4.0 x 1.6 mm modelled | Real head size of the Feetech bag screw (B2), print tolerance, the other screws (C4) |
| E8 | Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests) | `VERIFY_OUT=<out> ODM_TEST_PYTHON=<python with rustypot, pypot> python3 altaay_lab/verify/e8_bench_pytest.py` | **PASS (0 FAIL, 1 WARN)** | pytest: 32 passed, 36 skipped in 28.71s (details below) | The bench agent's tests: STS3215 protocol, first-servo check, battery guard, power log, feet, IMU, thermal guard and the Runtime cross-check, against a fake STS3215 bus on a pty and fake Blinka pins | Real servos, real USB adapter timing, real GPIO (TEST_PLAN.md sections 6 to 12) |
| E9 | Joint angles the stock policy uses in the sim walk, trained mass and our build (sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/e9_joint_envelope.py` | **PASS** | in the walk (trained mass): hip yaw -5.8 to +10.3 deg (range +/-30), hip pitch -49.3 to +49.6, knee up to +90.8 (limit +90); largest policy action 0.97 (details below) | 7 current_budget.py cases on the trained model and on our build's model (C8): min and max of every joint angle, the largest policy action and motor target, after the 2 s settle and before a fall; MJCF ranges | Falls, get-up, manual moves and find_soft_offsets.py (they can reach the full joint range); real servo tracking |
| C1 | Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c1_bom_coverage.py` | **PASS** | 58 netlist parts map to BOM lines with matching part numbers (17 splices are made); BOM_FULL 242 rows vs sources: 0 FAIL (see list); heat shrink 42 pieces by the rule (42 joints in the netlist), 42 drawn (details below) | Netlist components to BOM lines (part numbers checked in the line text), netlist BOM references, counts per line vs Need; BOM_FULL rows vs CAD nodes, print/parts.csv, netlist, fasteners.json (screws, washers), wire cut sums, heat shrink by the BOM_FULL rule (this check's own count, the 3D sleeves, BOM 26); the committed BOM_FULL.md vs a fresh build from today's sources; rows with no purchase line | Whether a bought part is the right one (datasheets), prices, the spares rule, the heat shrink size at each joint |
| C2 | Connectors: every wired pin has a mating part or end treatment; crimps fit the Molex 08-70-1040 | `VERIFY_OUT=<out> python3 altaay_lab/verify/c2_connectors.py` | **PASS (0 FAIL, 3 WARN)** | 342 wire ends match their connector class; housings 7 and terminals 17 agree with BOM 21/22, CABLE_MAP, WIRING.md; 22 AWG OD 1.7 +/- 0.1 mm vs Molex 08-70-1040 insulation max 1.9 mm, gauges 22, 24, 26, 28 AWG, 3.0 A at 22 AWG (Molex catalog) (details below) | Every end of the wires on active cables vs its pin group's connector class; housing positions (one wire each, adapter V empty); housing and terminal counts vs BOM 21/22, CABLE_MAP, WIRING.md; kit cables used vs shipped; crimp insulation diameter; connector pins left open | Pin order inside each housing vs the servo port (TEST_PLAN.md section 2 polarity), crimp quality (section 1), the real part labels marked [I] in the netlist |
| C3 | Every active cable has a 3D route whose worst length plus slack fits its cut, a service loop at every joint, and a hold at every tie point | `VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py` | **PASS (0 FAIL, 7 WARN)** | 61 of 61 active cables routed in 3D (0 runs still straight placeholders); by chain (twist take-up in): 0 wires cannot reach, 8 with less than 40 mm slack; 43 of 49 joint loops (58 crossings) meet 3 x OD (43 within the Runtime head ranges); 75 tie points: 51 adhesive tie mount, 13 bundle tie, test fit, 6 existing printed feature, 3 drilled printed feature, 2 cable tie to a neighbour cable (MB3A 27, ABM1M 24); 0 open (details below) | Every active cable: route present and routed, wires and cut lengths as in the netlist, worst length over the joint ranges + 40 mm vs cut by conductor chain through floating splices, netlist joints vs 3D crossings, the loop between the ties at every crossing (bend and length storage vs 3 x OD, recomputed from the URDF), what holds every tie point, BOM lines 32 and 34 vs the tie and mount counts | Real cable stiffness and where the slack sits, connector back-shell sizes (Molex 5264 housing drawing not read), rubbing against moving parts beyond the cables3d sweep, the real flat area under each mount (TEST_PLAN.md section 1.4 test fit) |
| C4a | Every fitted screw has a BOM line, a length that line buys, and a count it covers (fasteners.json vs BOM.md) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py` | **PASS** | 324 fitted screws and 58 inserts; 0 screws name no BOM line in fasteners.json (BOM.md buys 0 of them); Need differs from the schedule on lines: none; kit 17h holds 50 per size by its line text, enough for M2x5 24 of 50, M2x6 4 of 50, M2x8 2 of 50, M2x4 2 of 50 (details below) | Every fitted screw in fasteners.json (servo case screws included): BOM line exists, size and length match the line's Item and Spec, count per line vs Need and Buy, per size for a kit (the count per size its line states, e.g. '50 each of'), screws with no line; washers and other new items | Servo and SG90 bag contents by size (B2, test order TO1 and TO6), thread engagement (fasteners agent), stock at order time |
| C4b | No screw head or tip collision over the joint ranges, except known, decided ones (fasteners sweep vs D18 and D19) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py` | **PASS (0 FAIL, 4 WARN)** | screw hits by kind: button head still hits 2; stand-in head (size not published) 26; against a CAD body the build replaces 1; D18 screws left out: 2 (details below) | Every fitted screw's head and protruding tip vs every part over each joint's URDF range and 13 joint pairs (sweep_fasteners.py results in fasteners.json); hits split into screw-limited, parts-first and static contact | Real head sizes of the bag screws (stand-in models), print tolerance, real joint stops tighter than the URDF |
| C5 | Servo IDs agree everywhere (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime code and config, bench, sim, policy order) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c5_servo_ids.py` | **PASS** | 14 joint IDs agree in 8 ID maps (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime HWI, configure_all_motors, bench): True; chains agree in netlist, WIRING.md, bench, power sim; MJCF actuator order = Runtime action order: True (details below) | 14 joint to ID pairs in 10 sources, the 3 bus chains (netlist wires, WIRING.md, bench, power sim), MJCF actuator order vs Runtime action order, Runtime checkout commit | IDs written into real servos (TEST_PLAN.md section 7.1, section 8.1 check_motors.py) |
| C6 | GPIO pins agree (netlist, WIRING.md section 3, CABLE_MAP, HARNESS_BUILD, D9, Runtime code at 376de65) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c6_gpio.py` | **PASS** | 12 Pi signals on the same GPIO and header pin in the netlist, WIRING.md, HARNESS_BUILD.md, CABLE_MAP.md, D9 and the Runtime code: True (details below) | 12 Pi signals (2 feet, 2 eyes, projector, 2 antennas, I2C SDA/SCL, 3 I2S) in 6 sources; BCM to header pin map (pinout.xyz); the far end of every netlist GPIO wire (left foot goes to the left foot switches); no GPIO used twice | Pi device tree settings (I2S overlay, PWM for the antennas), real wiring (TEST_PLAN.md sections 2 and 12) |
| C7 | Current ratings: every wire, contact and part on the servo power path as wired now (D15 plus the D23 feeds SP4 and SP5) vs the simulated currents (sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py` | **PASS (0 FAIL, 3 WARN)** | as built (SP4/SP5 in): every mean under its limit; worst 100 ms over the 26 AWG kit limit on 0 hops and over 3 A on 0 contacts; Pololu 2815 at 99 % of its 6.0 A (55 C) rating, sim RMS 5.94 A walking (6.04 A at the low pack): TEST_PLAN 4.2 heat check; adapter ground 0.35 A worst 100 ms (details below) | P11, SP1 to SP5 and the 11 kit cable hops vs gauge ampacity (erc.py table), with the as-built current split (each leg a loop through SP4/SP5) in both corners; their 5264 / Mini-SPOX contacts (3 A); return current in the SP grounds, the D15 data-lead grounds, the adapter and the USB ground; fuse, holder, BMS, Pololu 2815 (TEST_PLAN 4.2 heat check), XT30, cells, BEC, BEC leads and the P cables vs the E6 as-built ngspice currents; the netlist's written currents vs the sim | Real servo currents (CURRENT_BUDGET.md: up to 2 x sim until a bench log), temperature rise inside the body, connector wear, real contact and hop resistance (TEST_PLAN.md sections 3 to 5 and 9) |
| C8 | The stock policy walks the robot we will build (2.79 kg, sim/MASS_BUDGET.md) on flat ground (sim/added_mass_sim.py, sim pass only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c8_policy_mass.py` | **PASS (0 FAIL, 1 WARN)** | our build 2.7881 kg: 0 falls in 36 flat-ground runs; forward speed 0.66 of the command (trained mass 0.73) (details below) | Model mass vs MASS_BUDGET.md; stock copy vs CURRENT_BUDGET.md; our build in 6 flat cases nominal + 6 seeds each; tracking vs the doc that ran the same mass (ADDED_MASS_SIM.md table 1 or print/MASS_STUDY.md); a hardware test for the centre of mass margin | Rough terrain (falls for stock and ours), get-up, real servo tracking (issue 48), the real mass and centre of mass (not weighed) |
| C9 | Docs agree: numbers that appear in several docs are the same everywhere | `VERIFY_OUT=<out> python3 altaay_lab/verify/c9_docs.py` | **PASS (0 FAIL, 12 WARN)** | 0 disagreements (none); blocker table: 73 rows, 30 cleared or decided (details below) | Blocker counts and blocker status words, BOM totals and test order total, part counts, STL count, screw counts, decision range, upstream issue count, wire currents (WIRING.md vs netlist), print numbers, robot mass; 41 docs (history/ left out) | Numbers written in words or in a form the patterns do not catch; history entries; prose claims without numbers |
| C10 | Wiring sheets cover every wire of the netlist (wiring/sheets, run on a copy) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c10_sheets.py` | **PASS** | 171 of 171 active wires drawn in full on sheets 1, 2, 3, 4, 5, 6; harness sheet 5: True (details below) | Every active netlist wire drawn in full on a sheet (every sheet but the harness), every active cable on the harness sheet (sheet 5), the generator's own stop rules, committed sheets newer than netlist.yaml | Whether a drawing is easy to read; label placement (the generator prints layout warnings) |
| C11 | Hip yaw the stock policy uses (walk and turn) stays under the F198/F211 collision onset (21.7 deg) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c11_hip_yaw_envelope.py` | **PASS (0 FAIL, 1 WARN)** | largest hip yaw angle 10.3 deg (stock, turn_1.0), turn 10.3 and 10.3 deg; onset 23.3 deg; margin 13.0 deg (rule 5); policy bound 15.9 deg with the sim overshoot (details below) | Collision onset from the fastener sweep; largest /hip yaw/ in 7 sim cases (turn 1.0 rad/s included) on the trained model and our build; the policy's bound (default + 0.25 x tanh action) checked on 6000 random inputs; clamps in the Runtime code | Real servo overshoot, falls, manual moves, find_soft_offsets.py, other policies or a wider command range |
| C12 | The charging dock: parts, fits, screws, wiring, routes, BOM against the model (twin/dock, CAD check only) | `VERIFY_OUT=<out> python3 altaay_lab/verify/c12_dock.py` | **PASS (0 FAIL, 5 WARN)** | dock: 96 components, 41 screws OK, 18 wires routed (self-check PASS), BOM Need matches the model (details below) | Printed parts, interferences and the paddle motion, every screw, the gate ERC, every wire's 3D route and cut, sheet 7, BOM Need against the fasteners, the assembly and the gate board | Real fits (printing tolerance), spring and switch tolerances (BT1, BT5), the sim of the walk (section 12.1 is sim pass only) |

## FAIL findings and proposed fixes

Each line: what is wrong, with the numbers, then the proposed fix and the file it belongs to. The files belong to other agents or to the lead; nothing here was changed by agent Q.

### E6 Power path to every servo as wired now: D15 star plus the D23 ankle feeds SP4 and SP5, lengths and gauges from wiring/netlist.yaml (sim/power_path_sim.py as_built, ngspice, sim pass only)
- sim, typical corner, nominal pack: a servo is under 6.0 V for 11.2 % of the walk counted in time (our build (C8); for the ankles, 50 Hz samples locked to the control loop read 0.0 to 18.7 % by phase); TEST_PLAN.md section 9 passes only under 10 % **Fix:** the wiring misses TEST_PLAN 9 with the expected resistances: sim/POWER_FIX.md options (6+3b passes) (altaay_lab/sim/POWER_FIX.md)

### E6b TEST_PLAN.md section 5 hop gate is enough for the section 9 gates, wiring as built (D15 plus the D23 feeds, netlist lengths; power path sim sweep, sim pass only)
- TEST_PLAN.md section 5 passes hops up to 28 mOhm per conductor, but at that value the right knee is under 6.0 V for 11.3 % of the walk at a nominal pack (our build (C8), as built), over the section 9 gate of 10 %; about 23 mOhm passes **Fix:** TEST_PLAN.md section 5: gate at most 23 mOhm per conductor on 2S (the typical corner is 27.6), or the 3S plan (sim/POWER_FIX.md 6+3b) (altaay_lab/TEST_PLAN.md sections 5 and 9)

## WARN findings (risks, test fits, notes)

### E6
- sim, high-side corner, nominal pack: a servo is under 6.0 V for 35.2 % of the walk counted in time (our build (C8); for the ankles, 50 Hz samples locked to the control loop read 11.4 to 37.0 % by phase); TEST_PLAN.md section 9 passes only under 10 % Proposed: known: the high-side corner; the bench gates TEST_PLAN.md 3.2 (pack side), 4.1 (BEC dropout) and 5 (hop resistance) keep the robot out of it; the 3S plan (sim/POWER_FIX.md option 6+3b, held by D23) passes it

### E6b
- TEST_PLAN.md section 5 warn band (over 28 up to 40 mOhm per conductor): at 40 mOhm the knees are under 6.0 V for 10.8 / 14.0 % of the walk (left / right), the head roll 11.0 % and the ankles 9.4 % (our build (C8), as built, nominal pack, typical pack side), over the section 9 gate of 10 %; lowest servo 5.46 V, above 4.5 V. A hop in this band goes on to the walking log, which decides (lead decision L3) Proposed: if section 5 reads in the warn band: make the 3S plan (sim/POWER_FIX.md option 6) ready for Ahmed before the walking log (TEST_PLAN.md sections 5 and 9, DECISIONS.md D23 note L3)
- TEST_PLAN.md section 5 says the ankle gate holds to about 60 mOhm per conductor; with the as-built wiring this sweep gives about 47 mOhm (worse trace, typical pack side) Proposed: TEST_PLAN.md section 5: write 'sim: the ankle gate holds to about 50 mOhm' (E6b, as built)

### E7
- left: the inner screw D18 keeps clears roll_to_pitch by only 0.24 mm (worst at -7.2 deg), inside normal print tolerance Proposed: add to the first-leg check (print/PRINT_PLAN.md left-leg check, D18): sweep hip roll by hand with the inner screw fitted and look for rubbing on roll_to_pitch
- right: the inner screw D18 keeps clears roll_to_pitch by only 0.16 mm (worst at -11.0 deg), inside normal print tolerance Proposed: add to the first-leg check (print/PRINT_PLAN.md left-leg check, D18): sweep hip roll by hand with the inner screw fitted and look for rubbing on roll_to_pitch

### E8
- 36 tests skipped: Runtime checkout or its adafruit_bno055 dependency not found; rustypot 0.1.0 and pypot not installed; walk needs rustypot, pypot, onnxruntime, the policy and the Runtime Proposed: run with ODM_TEST_PYTHON set to a Python that has the Runtime's pinned packages

### C2
- 2 wire ends on a connector this check has no rule for: 'solder leads'
- 2 wire ends on a connector this check has no rule for: 'solder, in heat shrink on the DC3 lead'
- 15 wire ends on a connector this check has no rule for: '0.1 in pads, solder (no header)'

### C3
- D10: 1 wire(s) reach with only 40 mm to spare (worst chain D10 PI.36>AMP.SD 220, 180 mm routed, cut 220 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut PI.36 -> AMP.SD 230 mm (the chain then has the 2 x 20 mm slack), or keep the cut and test fit it (TEST_PLAN.md 1.4)
- DC3: 1 wire(s) reach with only 0 mm to spare (worst chain DC3 WK1.K>SW1.ON 0, 0 mm routed, cut 0 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: cut WK1.K -> SW1.ON 40 mm (the chain then has the 2 x 20 mm slack), or keep the cut and test fit it (TEST_PLAN.md 1.4)
- S2: 3 wire(s) reach with only 18 mm to spare (worst chain S2 SV20.BUS1.D>SV21.BUS2.D 150, 132 mm routed, cut 150 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2
- S7: 3 wire(s) reach with only 17 mm to spare (worst chain S7 SV10.BUS1.D>SV11.BUS2.D 150, 133 mm routed, cut 150 mm), under the 2 x 20 mm service slack: a test fit decides (CABLE_MAP length rule) Proposed: kit cable length is fixed: test fit at both joint limits (B17, TEST_PLAN.md 1.4); contingency X1/X2
- 6 of 49 joint loops cannot reach 3 x OD over the full URDF range inside the route room: SP4 at left_hip_pitch: free 30 mm between the ties, bend R 22.6 mm, length storage R 5.8 mm (loop 30 mm over a 6.6 mm closest tie-to-tie chord), worst 1.7 x OD, needs 3 x OD (10.2 mm); S11 at neck_pitch: free 19 mm between the ties, bend R 42.6 mm, length storage R 6.8 mm (loop 25 mm over a 13.1 mm closest tie-to-tie chord), worst 2.6 x OD, needs 3 x OD (7.8 mm); D3 at neck_pitch: free 26 mm between the ties, bend R 59.1 mm, length storage R 9.9 mm (loop 32 mm over a 19.8 mm closest tie-to-tie chord), worst 2.9 x OD, needs 3 x OD (10.4 mm); D1 at neck_pitch: free 26 mm between the ties, bend R 58.9 mm, length storage R 10.2 mm (loop 32 mm over a 20.3 mm closest tie-to-tie chord), worst 2.9 x OD, needs 3 x OD (10.5 mm); D2 at neck_pitch: free 26 mm between the ties, bend R 58.9 mm, length storage R 10.1 mm (loop 32 mm over a 20.2 mm closest tie-to-tie chord), worst 2.9 x OD, needs 3 x OD (10.4 mm); P13 at neck_pitch: free 27 mm between the ties, bend R 61.4 mm, length storage R 10.7 mm (loop 33 mm over a 21.3 mm closest tie-to-tie chord), worst 3.0 x OD, needs 3 x OD (10.8 mm) Proposed: turn the joint through its whole range by hand with the loop dressed and look for a kink or a pull at the ties (TEST_PLAN.md section 1.4); 0 of them meet the rule within the Runtime head ranges
- 13 loop ends have no retention item within 8 mm on the same link: SP4 main at left_hip_yaw 2 mm; SP4 main at left_hip_roll 70 mm; SP4 main at left_hip_roll 98 mm; SP4 main at left_hip_pitch 152 mm; SP4 main at left_knee 219 mm; SP5 main at right_hip_yaw+right_hip_roll 35 mm; SP5 main at right_hip_pitch 92 mm; SP5 main at right_hip_pitch 141 mm; SP5 main at right_knee 189 mm; SP5 main at right_knee 260 mm Proposed: re-run cables3d/seats_ties.py
- 9 tie points are a tie round the bundle only (no printed feature, mount, hole pair or anchored neighbour fits; D25: no new printed parts, no STL change): T016 D2,P13,D13,D22 on neck_yaw_assembly; T017 D2,D3,D4,P13,D13,D22 on neck_yaw_assembly; T023 D1,D3,D4 on neck_pitch_assembly; T024 D1 on neck_yaw_assembly; T026 D2,D3,D4,D22 on head_assembly; T034 D3,SP4 on knee_and_ankle_assembly_2; T045 D4,SP5 on knee_and_ankle_assembly_3; T085 S13 on neck_yaw_assembly; T089 SP5 on trunk_assembly Proposed: check each at both joint limits at the TEST_PLAN.md 1.4 test fit; a drilled tie-hole pair or a printed anchor only if the bundle reaches a moving part

### C4b
- 2 screws still hit with the button head, known and left as a joint range point in D19 (not fixed): F211 M3x6 ISO 7380 A2 button head vs body_middle_bottom at right_hip_yaw -30.0, -0.82 mm, -0.82 mm with the button head; F198 M3x6 ISO 7380 A2 button head vs body_middle_bottom at left_hip_yaw 26.7, -0.82 mm, -0.82 mm with the button head (outside the walk: F198: hits from left_hip_yaw +23.3 deg, the sim walk uses -5.3 to +10.3 deg (E9); F211: hits from right_hip_yaw -23.3 deg, the sim walk uses -6.0 to +5.9 deg (E9), see C11) Proposed: see C11: nothing in the Runtime limits hip yaw; decide the limit before the first powered joint sweep (TEST_PLAN.md 8.3)
- 26 servo case or bag screws overlap a part with the stand-in head model (real head size not published): F162 SG90 bag horn screw vs antenna at zero pose (static) 0.0, -0.78 mm; F163 SG90 bag horn screw vs antenna at zero pose (static) 0.0, -0.78 mm; F262 PA2.0 self-tapping (factory) vs neck_left_sheet at zero pose (static) 0.0, -0.22 mm; F263 PA2.0 self-tapping (factory) vs neck_left_sheet at zero pose (static) 0.0, -0.22 mm; F266 PA2.0 self-tapping (factory) vs head_roll_mount at zero pose (static) 0.0, -0.22 mm; F267 PA2.0 self-tapping (factory) vs head_roll_mount at zero pose (static) 0.0, -0.22 mm Proposed: measure the factory and bag screw heads on the first servo and the SG90 pack (test orders TO1 and TO6, B2)
- 1 screws touch a CAD body the build replaces (keep the real part clear when placing it): F123 M2.5x6 DIN 912 A2 vs bms at zero pose (static) 0.0, -0.34 mm
- 162 screws touch a part at the zero pose by up to 0.08 mm (static contact: head seated against a face; under the 0.1 mm modelling resolution)

### C7
- D15 says no servo current through the adapter, but the data-lead grounds make it a parallel return path: as built 0.35 A worst 100 ms through SD2 G (adapter H5 G terminal) (DC split, 6.0 V currents); ngspice 0.15 A worst 100 ms in the adapter H3 G lead; harmless against the adapter's MAX:6A header marking and the 3 A contacts Proposed: if it must be zero, drop the GND wire of one adapter socket lead (keep one ground reference) or state in WIRING.md section 2 that some return current flows through SD1, SD2 and the adapter ground
- main switch Pololu 2815: as-built sim pack RMS 5.94 A while walking (our build (C8), walk, backlash, pack nominal, high-side R), 99 % of its 6.0 A continuous rating at 55 C (Pololu: 12 V, 22 C ambient, still air; 16 A at 150 C; https://www.pololu.com/product/2815, read 2026-11-02 1:32 AM ET); 6.04 A at the low pack. 6.0 A is a heat point, not a limit: the board on foam tape inside the body runs warmer than Pololu's test (sim pass only) Proposed: TEST_PLAN.md 4.2 heat check: 10 minutes at 6.0 A (TE4) on its seat with the foam tape, board under 50 C; over 50 C fit a second 2815 in parallel below the first (sim/POWER_FIX.md)
- falls with every allowance stacked reach about 17 A for 20 ms (CURRENT_BUDGET.md), the bottom of the Tenergy trip band (22 +/- 5 A after 8 +/- 4 ms): a fall at a low pack can open the BMS (sim pass only; known) Proposed: keep TEST_PLAN.md section 3.3 (pulse test) and log BMS cut-outs in section 9

### C8
- no doc records the walk of this model mass within 1 % (2.7881 kg): sim/ADDED_MASS_SIM.md ran 2.75 kg, print/MASS_STUDY.md (c) 2.6387 kg Proposed: re-run sim/added_mass_sim.py and update sim/ADDED_MASS_SIM.md table 1

### C9
- sim/MASS_BUDGET.md models 274 screws, fasteners.json fits 324 (the screw mass, 175 g, is from the older count) Proposed: re-run sim/mass_budget.py on fasteners.json when it is final
- DECISIONS.md line 3 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: DECISIONS.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- GAPS.md line 67 says 'D1 to D12', DECISIONS.md goes to D59 (dated section)
- START_HERE.md line 4 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: START_HERE.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- START_HERE.md line 17 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: START_HERE.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- START_HERE.md line 57 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: START_HERE.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- START_HERE.md line 120 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: START_HERE.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- STATE.md line 50 says 'D1 to D25', DECISIONS.md goes to D59: the work in that file did not look at D26 to D59 Proposed: STATE.md: check D26 to D59 against it, then write 'D1 to D59' (or date the statement)
- UPSTREAM_ISSUES.md line 7 says 'D1 to D12', DECISIONS.md goes to D59: the work in that file did not look at D13 to D59 Proposed: UPSTREAM_ISSUES.md: check D13 to D59 against it, then write 'D1 to D59' (or date the statement)
- UPSTREAM_ISSUES.md line 364 says 'D1 to D12', DECISIONS.md goes to D59: the work in that file did not look at D13 to D59 Proposed: UPSTREAM_ISSUES.md: check D13 to D59 against it, then write 'D1 to D59' (or date the statement)
- README.md line 3 gives the robot mass as 2.1 kg (sim mass, trained model); the build is 2.79 kg by sim/MASS_BUDGET.md Proposed: README.md line 3: after '2.1 kg (sim mass)' add ' (the lab build is about 2.79 kg by the mass budget, sim/MASS_BUDGET.md, not weighed)'
- START_HERE.md line 9 gives the robot mass as 2.11 kg (sim mass, trained model); the build is 2.79 kg by sim/MASS_BUDGET.md Proposed: START_HERE.md line 9: after 'about 2.11 kg (sim mass)' add ' (the lab build is about 2.79 kg by the mass budget, sim/MASS_BUDGET.md, not weighed)'

### C11
- nothing in the Runtime limits hip yaw: the policy bound keeps the walk under the onset, but a manual move, find_soft_offsets.py (Runtime issue 32 moves every joint) or a fall can still reach 21.7 to 30 deg and press the F198/F211 heads into body_middle_bottom Proposed: DECISIONS.md: record the hip yaw limit (for example the STS3215 angle limit registers set to about +/-20 deg of travel for IDs 10 and 20 in configure_motor.py, or a clip in the walk script), or relieve body_middle_bottom at the two heads

### C12
- tipping, a child's bump or pull at the mast top, +x (toward the back): tips at 5.0 N (5 N gives 1.0x): a wall strap or a lower mast, Ahmed's call
- tipping, a child's bump or pull at the mast top, -x (toward the seat): tips at 9.8 N (5 N gives 1.97x): a wall strap or a lower mast, Ahmed's call
- tipping, a child's bump or pull at the mast top, +y: tips at 6.1 N (5 N gives 1.22x): a wall strap or a lower mast, Ahmed's call
- tipping, a child's bump or pull at the mast top, -y: tips at 6.0 N (5 N gives 1.2x): a wall strap or a lower mast, Ahmed's call
- dock BOM line K5 has no price (BLOCKER)

## Hardware-only tests that remain

No check above replaces these; each needs the parts or the robot. Order and pass/fail values are in TEST_PLAN.md.

| Test | Where | What the checks above say about it |
|---|---|---|
| Every made cable: crimp pull, connector fit, heat shrink (34 sleeves, 2 x OD on the splices) and twist lay, length, joint loops and the 75 tie points at both limits of every joint it crosses (the test fit) | TEST_PLAN.md section 1 (1.3, 1.4) | C1 (sleeve count), C2 (end treatments), C3 (lengths with the twist take-up, 43 loops at 3 x OD, what holds each tie point, the 2 foot jumpers) |
| Continuity and polarity of every wire, no short between nets | TEST_PLAN.md section 2 (audit/continuity_checklist.csv) | E1 |
| Cells, holder drop at 10 A, BMS trip, first charge | TEST_PLAN.md section 3 | C7 (BMS margin on falls) |
| BEC set point, input sweep and the 0.30 V dropout pass, Pololu 2815 at 5 A and 10 minutes at 6 A, 5 V regulator, fuse holder | TEST_PLAN.md section 4 | E6 (BEC dropout 0.3 V assumed), C7 (Pololu 2815 at 99 % of its 6 A point as built, sim RMS 5.93 A) |
| Kelvin resistance of one servo hop: pass to 28 mOhm per conductor, warn over 28 up to 40, fail over 40 (lead decision L3) | TEST_PLAN.md section 5 | E6b (as built: at the 28 mOhm pass gate every servo meets section 9 in sim, right knee 9.9 %; at the 40 mOhm warn limit the right knee is under 6 V for 13.4 % of the walk; the ankles alone hold to about 60 mOhm) |
| Adapter enumerates with H1 unpowered and drives one servo | TEST_PLAN.md section 6 | C7 (ground return through the adapter) |
| First servo: registers 41 to 86, register 85 = 0, firmware, speed, thermal hold | TEST_PLAN.md section 7 | E8 (bench scripts on a fake bus) |
| Weigh the robot and find its centre of mass; staged power-up; all 14 IDs answer | TEST_PLAN.md section 8 (8.0 is the mass step) | C8 (backward margin 4 to 6 mm), C5 (IDs) |
| Walking log: every servo voltage and current, time under 6 V of every servo counted in time (ankles, knees, head roll at 10 %), checksum errors, forward speed | TEST_PLAN.md section 9 | E6, E6b (sim), E8 (bench/power_log.py on the fake bus: own timer in the loop's idle time, time count matches an exact share) |
| IMU: 1000 still reads, tilt signs | TEST_PLAN.md section 10 | none (no sim check of B20) |
| Battery cut-off at servo Present Voltage 6.0 V; exit code 10 when torque off is not confirmed | TEST_PLAN.md section 11 | E8 (battery guard and torque read-back on the fake bus) |
| Foot switches: under 1 ohm closed, 200 presses, 60 s still | TEST_PLAN.md section 12 | C6 (pins), C3 (jumper length) |
| Coupon prints: insert bores, foot_top wall, left eye pilot, TPU sole | print/PRINT_PLAN.md coupon session (B14, B15, B16, B26) | none |
| Screw head fits the CAD cannot settle: servo bag split, horn gap, M2x5 heads, hip roll inner screw rub | HARDWARE_AUDIT.md B2, B6, B21; D18 first-leg check | E7, C4a, C4b |
| Hip yaw kept under 21.7 deg outside the walk (manual moves, find_soft_offsets.py, falls): F198/F211 heads | TEST_PLAN.md 8.2a (+/-20 deg, robot hanging, hip yaw held by hand) | C11 (walk and turn reach 10.5 deg; nothing in the Runtime limits it) |
| Head yaw kept within +/-45 deg for manual moves; the neck bundle loop turned once to the full +/-160 deg at the test fit | TEST_PLAN.md 8.2b and 1.4 (D25) | C3 (neck loops meet 3 x OD over +/-160 deg in CAD), E9 (head yaw the policy uses in the sim walk) |
| Ankle plugs and the SP4/SP5 feeds at the foot_side apex | TEST_PLAN.md 1.5 (HARDWARE_AUDIT B33) | C3 (the SP4/SP5 routes touch foot_side in CAD) |

## Details per check

### E1 Electrical rule check of the netlist (audit/erc.py) plus mutation test: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e1_erc.py`. Finished 2026-11-07 02:02 UTC, 5 s.
- erc.py on wiring/netlist.yaml: 0 ERROR, 0 WARN, 8 INFO (exit 0)
- Components 75, pins 297, cables 65 (4 removed), wires 171.
- committed audit/ERC_REPORT.md current: True; audit/continuity_checklist.csv current: True
- mutation test: 10 of 10 injected faults caught
- extended domain rule (pwr_in pins, independent of erc.py): 26 wire ends on pwr_in pins, 0 over their domain
- INFO: M1 caught: S2 V conductor moved to the ID 21 DATA pin (short SERVO_7V2 to BUS_DATA) (expected ERROR in 'shorts'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M2 caught: SP1 V wire made 16 AWG on an 08-70-1040 terminal (expected ERROR in 'crimps'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M3 caught: wire added to the empty adapter H3 V position (nc pin, D15) (expected ERROR in 'pin use'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M4 caught: pin name typo SV22.BUS3.G (expected ERROR in 'references'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M5 caught: P13 mean current 12 A on 20 AWG (limit 11 A) (expected ERROR in 'ampacity'; got {'ERROR': 1, 'WARN': 0, 'INFO': 8})
- INFO: M6 caught: switched pack (8.4 V) on BNO055 VIN (3.3 V, dir pwr_in) (expected ERROR in 'domains'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M7 caught: switched pack (8.4 V) on GPIO22 (dir in) (expected ERROR in 'domains'; got {'ERROR': 1, 'WARN': 0, 'INFO': 4})
- INFO: M8 caught: 5264 plug on a 2.54 mm header pin group (expected ERROR in 'connector match'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})
- INFO: M9 caught: misspelt wire key 'guage' (expected WARN in 'schema'; got {'ERROR': 0, 'WARN': 1, 'INFO': 0})
- INFO: M10 caught: wire left on removed cable S14 (expected ERROR in 'references'; got {'ERROR': 1, 'WARN': 0, 'INFO': 0})

### E2 BOM.md subtotals, totals and test order total (audit/bom_totals.py on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py`. Finished 2026-11-07 02:09 UTC, 0 s.
- bom_totals.py: {Robot: 848.14, Fasteners and mechanical: 73.75, Cables, connectors, wire: 282.84, Print material: 53.97, Expression (optional upstream): 129.14, Tools (one-time): 271.66} build 1258.7 with expression 1387.84 with tools 1659.5 test order 228.49
- BOM.md copy unchanged after the recompute: every subtotal and total in BOM.md matches its lines
- Buy >= Need checked on 89 countable lines (Need and Buy in the same unit)

### E3 bom.json rebuilt from BOM.md (audit/bom_md_to_json.py on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e2_bom_scripts.py`. Finished 2026-11-07 02:09 UTC, 0 s.
- bom_md_to_json.py: 105 rows written to bom.json; committed bom.json 105 rows, rebuilt 105 rows
- rebuilt bom.json is identical to the committed one

### E4 Exploded-view data build and its CAD count checks (viewer/make_viewer_data.py): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e4_viewer.py`. Finished 2026-11-07 02:02 UTC, 30 s.
- printed parts 62 / 62 over 44 STLs; servos 14 / 14; inserts 48 / 48; bearings 3 / 3
- BOM lines 105 (cad 12, placeholder 19, filament 2, not modelled 72); count mismatches none
- STL vs URDF frame check: 37 parts, worst 0.012 mm; assembly.json match True; unmapped meshes none
- faces of the print STLs that moved against the URDF mesh (one face per axis: printed features the lab added, mm, + = grown): {'body_front': {'-x': 7.974}, 'body_middle_bottom': {'-x': 2.0, '+z': 0.35}, 'body_middle_top': {'+x': 2.0}}
- screws drawn 324 (324 screws from altaay_lab/fasteners/fasteners.json, 62 with the length from the drawing, not yet chosen (not drawn: 37 screws left out or not fitted; inserts are drawn from the CAD bores, 58 insert rows in fasteners.json of which 10 left out)); cables drawn 93 (93 cables from altaay_lab/cables3d/cables3d.json)
- washers drawn 8 (BOM_FULL row F21, 8 pcs), fasteners.json fits 8; heat shrink sleeves drawn 42 (42 with a netlist joint), BOM_FULL counts 42
- GLB 4.71 MB, 739 nodes (output kept in the scratch folder, not in git)

### E5 Servo current budget from the stock walk (sim/current_budget.py, sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e5_current_budget.py`. Finished 2026-11-07 02:03 UTC, 7 s.
- Stand, zero command: falls none; mean 0.19, 100 ms 0.23, 20 ms 0.24, 2 ms 0.24 A
- Walk forward 0.15 m/s: falls none; mean 2.22, 100 ms 3.08, 20 ms 4.02, 2 ms 4.97 A
- Turn 1.0 rad/s: falls none; mean 2.38, 100 ms 3.21, 20 ms 5.39, 2 ms 6.40 A
- Walk sideways 0.2 m/s: falls none; mean 2.25, 100 ms 3.81, 20 ms 5.92, 2 ms 7.19 A
- Walk forward, backlash model: falls none; mean 3.24, 100 ms 4.72, 20 ms 6.77, 2 ms 8.30 A
- Walk forward, rough terrain, backlash model: falls 0.28 s; mean 2.65, 100 ms 3.92, 20 ms 6.15, 2 ms 7.80 A
- Walk forward with pushes: falls 10.68 s; mean 1.89, 100 ms 3.59, 20 ms 5.26, 2 ms 6.27 A
- worst single servo, backlash walk: left_knee 3.33 A peak; highest RMS right_knee 1.46 A (doc: 3.35 A peak knee, 1.45 A RMS)

### E6 Power path to every servo as wired now: D15 star plus the D23 ankle feeds SP4 and SP5, lengths and gauges from wiring/netlist.yaml (sim/power_path_sim.py as_built, ngspice, sim pass only): FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e6_power_path.py`. Finished 2026-11-07 02:04 UTC, 44 s.
- netlist read by the model: altaay_lab/wiring/netlist.yaml sha256 293658e198, modified 2026-11-06 22:48 UTC
- netlist values used: P1 16 AWG 120 mm; P2 16 AWG 120 mm; P6 16 AWG 150 mm; P7 16 AWG 310 mm (30 + 90 + 90 + 40 + 60); P8 16 AWG 150 mm; P14 16 AWG 140 mm; P9 16 AWG 90 mm; P10 16 AWG 150 mm; P11 16 AWG 100 mm plus the BEC leads (as shipped); P13 20 AWG 550 mm; SP1 V 22 AWG 160 mm, G 22 AWG 140 mm + tail 22 AWG 30 mm; SP2 V 22 AWG 150 mm, G 22 AWG 130 mm + tail 22 AWG 30 mm; SP3 V 22 AWG 180 mm, G 22 AWG 160 mm + tail 22 AWG 30 mm; SP4 to left ankle BUS1: V 22 AWG 420 mm, G 22 AWG 420 mm; SP5 to right ankle BUS1: V 22 AWG 450 mm, G 22 AWG 450 mm; kit hops S2 150, S3 150, S4 150, S5 150, S7 150, S8 150, S9 150, S10 150, S11 150, S12 150, S13 150 mm; SD1 G stem 22 AWG 45 mm, a 22 AWG 120 mm, b 22 AWG 140 mm; SD2 G 22 AWG 140 mm
- active netlist cables on SERVO_7V2/VSW/PACK_P/PACK_F/CELL_N: DC1, P1, P10, P11, P13, P2, P4, P6, P7, P9, S10, S11, S12, S13, S2, S3, S4, S5, S7, S8, S9, SP1, SP2, SP3, SP4, SP5; in the model: 25; outside the servo path: P4 (charger, carries current only while charging)
- trained mass (E5), walk, backlash, pack full, high-side R: lowest left knee 5.90 V; ankle under 6 V 0.0 % of the time (50 Hz samples, by phase: 0.0 to 0.0 %); any servo under 4.5 V 0 ms; pack 5.22 A mean, 5.54 A RMS, 11.2 A max; BEC out 9.2 A max; complete True; left leg: lowest left knee 5.90 V, most time under 6 V left knee 0.3 %; right leg: lowest right knee 6.17 V, most time under 6 V right hip yaw 0.0 %; neck and head: lowest head roll 5.97 V, most time under 6 V neck pitch 0.0 %
- trained mass (E5), walk, backlash, pack full, typical R: lowest left knee 6.51 V; ankle under 6 V 0.0 % of the time (50 Hz samples, by phase: 0.0 to 0.0 %); any servo under 4.5 V 0 ms; pack 5.12 A mean, 5.44 A RMS, 11.3 A max; BEC out 9.3 A max; complete True; left leg: lowest left knee 6.51 V, most time under 6 V left hip yaw 0.0 %; right leg: lowest right knee 6.68 V, most time under 6 V right hip yaw 0.0 %; neck and head: lowest head roll 6.71 V, most time under 6 V neck pitch 0.0 %
- trained mass (E5), walk, backlash, pack nominal, high-side R: lowest head roll 4.87 V; ankle under 6 V 20.0 % of the time (50 Hz samples, by phase: 11.0 to 34.0 %); any servo under 4.5 V 0 ms; pack 5.50 A mean, 5.77 A RMS, 10.7 A max; BEC out 8.7 A max; complete True; left leg: lowest left knee 5.03 V, most time under 6 V left knee 28.2 %; right leg: lowest right knee 5.01 V, most time under 6 V right knee 28.3 %; neck and head: lowest head roll 4.87 V, most time under 6 V head roll 33.2 %
- trained mass (E5), walk, backlash, pack nominal, typical R: lowest left knee 5.57 V; ankle under 6 V 5.2 % of the time (50 Hz samples, by phase: 0.0 to 15.0 %); any servo under 4.5 V 0 ms; pack 5.47 A mean, 5.74 A RMS, 11.1 A max; BEC out 9.1 A max; complete True; left leg: lowest left knee 5.57 V, most time under 6 V left knee 6.1 %; right leg: lowest right knee 5.69 V, most time under 6 V right knee 8.4 %; neck and head: lowest head roll 5.63 V, most time under 6 V head roll 5.4 %
- trained mass (E5), walk, backlash, pack low, high-side R: lowest head roll 4.19 V; ankle under 6 V 100.0 % of the time (50 Hz samples, by phase: 100.0 to 100.0 %); any servo under 4.5 V 130 ms; pack 5.67 A mean, 5.91 A RMS, 10.4 A max; BEC out 8.4 A max; complete True; left leg: lowest left knee 4.33 V, most time under 6 V left hip yaw 100.0 %; right leg: lowest right knee 4.24 V, most time under 6 V right hip yaw 100.0 %; neck and head: lowest head roll 4.19 V, most time under 6 V neck pitch 100.0 %
- trained mass (E5), walk, backlash, pack low, typical R: lowest right knee 4.81 V; ankle under 6 V 100.0 % of the time (50 Hz samples, by phase: 99.7 to 100.0 %); any servo under 4.5 V 0 ms; pack 5.64 A mean, 5.89 A RMS, 10.7 A max; BEC out 8.7 A max; complete True; left leg: lowest left knee 4.84 V, most time under 6 V left hip roll 100.0 %; right leg: lowest right knee 4.81 V, most time under 6 V right hip pitch 100.0 %; neck and head: lowest head roll 4.85 V, most time under 6 V head pitch 100.0 %
- trained mass (E5), fall after a push, pack low, high-side R: lowest head roll 3.98 V; ankle under 6 V 97.4 % of the time (50 Hz samples, by phase: 96.7 to 98.7 %); any servo under 4.5 V 38 ms; pack 4.23 A mean, 4.50 A RMS, 11.6 A max; BEC out 9.4 A max; complete True; left leg: lowest left hip pitch 4.04 V, most time under 6 V left hip pitch 98.7 %; right leg: lowest right hip roll 4.56 V, most time under 6 V right hip pitch 98.2 %; neck and head: lowest head roll 3.98 V, most time under 6 V head roll 100.0 %
- our build (C8), walk, backlash, pack full, high-side R: lowest left knee 5.93 V; ankle under 6 V 0.0 % of the time (50 Hz samples, by phase: 0.0 to 0.0 %); any servo under 4.5 V 0 ms; pack 5.42 A mean, 5.74 A RMS, 11.0 A max; BEC out 9.0 A max; complete True; left leg: lowest left knee 5.93 V, most time under 6 V left knee 0.4 %; right leg: lowest right knee 6.17 V, most time under 6 V right hip yaw 0.0 %; neck and head: lowest head roll 5.96 V, most time under 6 V head roll 0.1 %
- our build (C8), walk, backlash, pack full, typical R: lowest left knee 6.53 V; ankle under 6 V 0.0 % of the time (50 Hz samples, by phase: 0.0 to 0.0 %); any servo under 4.5 V 0 ms; pack 5.32 A mean, 5.63 A RMS, 11.1 A max; BEC out 9.1 A max; complete True; left leg: lowest left knee 6.53 V, most time under 6 V left hip yaw 0.0 %; right leg: lowest right knee 6.69 V, most time under 6 V right hip yaw 0.0 %; neck and head: lowest head roll 6.63 V, most time under 6 V neck pitch 0.0 %
- our build (C8), walk, backlash, pack nominal, high-side R: lowest head roll 4.87 V; ankle under 6 V 21.7 % of the time (50 Hz samples, by phase: 11.4 to 37.0 %); any servo under 4.5 V 0 ms; pack 5.68 A mean, 5.94 A RMS, 10.5 A max; BEC out 8.5 A max; complete True; left leg: lowest left knee 5.08 V, most time under 6 V left knee 31.7 %; right leg: lowest right knee 5.07 V, most time under 6 V right knee 32.2 %; neck and head: lowest head roll 4.87 V, most time under 6 V head roll 35.2 %
- our build (C8), walk, backlash, pack nominal, typical R: lowest left knee 5.60 V; ankle under 6 V 7.8 % of the time (50 Hz samples, by phase: 0.0 to 18.7 %); any servo under 4.5 V 0 ms; pack 5.66 A mean, 5.93 A RMS, 10.9 A max; BEC out 8.9 A max; complete True; left leg: lowest left knee 5.60 V, most time under 6 V left knee 8.0 %; right leg: lowest right knee 5.72 V, most time under 6 V right knee 11.2 %; neck and head: lowest head roll 5.68 V, most time under 6 V head roll 7.4 %
- our build (C8), walk, backlash, pack low, high-side R: lowest head roll 4.10 V; ankle under 6 V 100.0 % of the time (50 Hz samples, by phase: 100.0 to 100.0 %); any servo under 4.5 V 215 ms; pack 5.81 A mean, 6.03 A RMS, 10.3 A max; BEC out 8.3 A max; complete True; left leg: lowest left knee 4.38 V, most time under 6 V left hip yaw 100.0 %; right leg: lowest right knee 4.24 V, most time under 6 V right hip yaw 100.0 %; neck and head: lowest head roll 4.10 V, most time under 6 V neck pitch 100.0 %
- our build (C8), walk, backlash, pack low, typical R: lowest right knee 4.83 V; ankle under 6 V 100.0 % of the time (50 Hz samples, by phase: 100.0 to 100.0 %); any servo under 4.5 V 0 ms; pack 5.80 A mean, 6.04 A RMS, 10.5 A max; BEC out 8.5 A max; complete True; left leg: lowest left knee 4.88 V, most time under 6 V left hip yaw 100.0 %; right leg: lowest right knee 4.83 V, most time under 6 V right hip yaw 100.0 %; neck and head: lowest head roll 4.86 V, most time under 6 V neck pitch 100.0 %
- TEST_PLAN.md section 9 gates: no servo under 4.5 V at any time (full and nominal pack); no servo under 6.0 V for more than 10 % of the walking time at nominal, counted in time: as the plan says
- gate check, typical corner: lowest servo at full or nominal left knee 5.57 V (trained mass (E5), nominal); servo time under 6 V at nominal 11.2 % (our build (C8); ankle minimum 5.71 V)
- gate check, high-side corner: lowest servo at full or nominal head roll 4.87 V (our build (C8), nominal); servo time under 6 V at nominal 35.2 % (our build (C8); ankle minimum 5.35 V)
- documented as-built row, nominal, typical, trained mass: lowest servo 5.57 V, ankle 5.2 % (doc) vs 5.57 V, 5.2 % (run)
- documented as-built row, nominal, high-side, trained mass: lowest servo 4.87 V, ankle 20.0 % (doc) vs 4.87 V, 20.0 % (run)

### E6b TEST_PLAN.md section 5 hop gate is enough for the section 9 gates, wiring as built (D15 plus the D23 feeds, netlist lengths; power path sim sweep, sim pass only): FAIL
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e6b_hop_sweep.py`. Finished 2026-11-07 02:05 UTC, 42 s.
- TEST_PLAN.md section 5 pass gate: 28 mOhm per conductor, warn band to 40 mOhm (fail over it); section 9 gates: no servo under 4.5 V, every servo under 6.0 V at most 10 % of the time; model: sim/power_fix.py option ab (as built), netlist altaay_lab/wiring/netlist.yaml sha256 293658e198, second feeds in the netlist: SP4, SP5
- as built, trained mass (E5), hop 17.6 mOhm per conductor (no contact resistance): ankle min 5.72 V, under 6 V 3.9 % of the time (50 Hz by phase 0.0 to 13.0 %); lowest servo left knee 5.65 V; knees 4.1 / 5.6 %, head roll 3.4 % under 6 V
- as built, our build (C8), hop 17.6 mOhm per conductor (no contact resistance): ankle min 5.75 V, under 6 V 6.4 % of the time (50 Hz by phase 0.0 to 18.7 %); lowest servo left knee 5.68 V; knees 5.6 / 8.3 %, head roll 4.5 % under 6 V
- as built, trained mass (E5), hop 27.6 mOhm per conductor (typical corner contacts): ankle min 5.69 V, under 6 V 5.2 % of the time (50 Hz by phase 0.0 to 15.0 %); lowest servo left knee 5.57 V; knees 6.1 / 8.4 %, head roll 5.4 % under 6 V
- as built, our build (C8), hop 27.6 mOhm per conductor (typical corner contacts): ankle min 5.71 V, under 6 V 7.8 % of the time (50 Hz by phase 0.0 to 18.7 %); lowest servo left knee 5.60 V; knees 8.0 / 11.2 %, head roll 7.4 % under 6 V
- as built, trained mass (E5), hop 28.0 mOhm per conductor (the section 5 pass gate): ankle min 5.69 V, under 6 V 5.3 % of the time (50 Hz by phase 0.0 to 15.0 %); lowest servo left knee 5.57 V; knees 6.1 / 8.5 %, head roll 5.5 % under 6 V
- as built, our build (C8), hop 28.0 mOhm per conductor (the section 5 pass gate): ankle min 5.71 V, under 6 V 7.9 % of the time (50 Hz by phase 0.0 to 18.7 %); lowest servo left knee 5.59 V; knees 8.1 / 11.3 %, head roll 7.5 % under 6 V
- as built, trained mass (E5), hop 40.0 mOhm per conductor (the section 5 warn limit): ankle min 5.66 V, under 6 V 6.7 % of the time (50 Hz by phase 0.0 to 17.0 %); lowest servo head roll 5.46 V; knees 8.8 / 11.5 %, head roll 8.4 % under 6 V
- as built, our build (C8), hop 40.0 mOhm per conductor (the section 5 warn limit): ankle min 5.68 V, under 6 V 9.4 % of the time (50 Hz by phase 0.0 to 18.7 %); lowest servo left knee 5.51 V; knees 10.8 / 14.0 %, head roll 11.0 % under 6 V
- as built, trained mass (E5), hop 57.6 mOhm per conductor: ankle min 5.61 V, under 6 V 8.7 % of the time (50 Hz by phase 0.0 to 18.3 %); lowest servo head roll 5.20 V; knees 13.2 / 15.0 %, head roll 13.0 % under 6 V
- as built, our build (C8), hop 57.6 mOhm per conductor: ankle min 5.64 V, under 6 V 11.0 % of the time (50 Hz by phase 2.7 to 19.3 %); lowest servo head roll 5.25 V; knees 13.8 / 17.3 %, head roll 16.3 % under 6 V
- as built, trained mass (E5), hop 77.6 mOhm per conductor: ankle min 5.56 V, under 6 V 10.4 % of the time (50 Hz by phase 1.0 to 23.0 %); lowest servo head roll 4.97 V; knees 17.9 / 18.3 %, head roll 19.5 % under 6 V
- as built, our build (C8), hop 77.6 mOhm per conductor: ankle min 5.59 V, under 6 V 12.5 % of the time (50 Hz by phase 3.7 to 21.3 %); lowest servo head roll 4.95 V; knees 17.5 / 21.2 %, head roll 22.4 % under 6 V
- hop resistance at which the worse trace reaches the 10 % ankle gate: about 47 mOhm per conductor (linear between 40.0 and 57.6)
- hop resistance at which the worst servo of any kind (knee or head roll, worse trace) reaches 10 % under 6 V: about 23 mOhm per conductor (linear between 17.6 and 27.6)

### E7 Hip roll servo screw head vs roll_to_pitch over the hip roll range (print/check_hip_roll_screw.py): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e7_hip_roll.py`. Finished 2026-11-07 02:07 UTC, 91 s.
- left: range -8.0..25.0 deg; screw at y +45.2: worst -1.30 mm at -8.0 deg, overlap over 41 of 41 angles; screw at y +24.7: worst 0.24 mm at -7.2 deg, overlap over 0 of 41 angles
- left: the colliding screw is the outer one, as D18 says (overlap 1.30 mm)
- right: range -25.0..8.0 deg; screw at y -24.8: worst 0.16 mm at -11.0 deg, overlap over 0 of 41 angles; screw at y -45.3: worst -1.30 mm at -25.0 deg, overlap over 41 of 41 angles
- right: the colliding screw is the outer one, as D18 says (overlap 1.30 mm)

### E8 Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests): PASS
Command: `VERIFY_OUT=<out> ODM_TEST_PYTHON=<python with rustypot, pypot> python3 altaay_lab/verify/e8_bench_pytest.py`. Finished 2026-11-07 02:08 UTC, 30 s.
- test python /usr/local/bin/python3: rustypot, pypot, onnxruntime, pytest importable: False
- pytest: 32 passed, 36 skipped in 28.71s (exit 0)

### E9 Joint angles the stock policy uses in the sim walk, trained mass and our build (sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/e9_joint_envelope.py`. Finished 2026-11-07 02:07 UTC, 10 s.
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
- ours left_hip_yaw: -5.3 to +10.3 deg (MJCF range -30.0 to +30.0)
- ours left_hip_roll: -4.1 to +9.2 deg (MJCF range -25.0 to +25.0)
- ours left_hip_pitch: -48.8 to -30.3 deg (MJCF range -70.0 to +30.0)
- ours left_knee: +67.6 to +89.1 deg (MJCF range -90.0 to +90.0)
- ours left_ankle: -46.8 to -27.2 deg (MJCF range -90.0 to +90.0)
- ours neck_pitch: +7.3 to +12.4 deg (MJCF range -20.0 to +65.0)
- ours head_pitch: -10.3 to +5.4 deg (MJCF range -45.0 to +45.0)
- ours head_yaw: -13.1 to +7.4 deg (MJCF range -160.0 to +160.0)
- ours head_roll: -7.6 to +3.0 deg (MJCF range -30.0 to +30.0)
- ours right_hip_yaw: -6.0 to +5.9 deg (MJCF range -30.0 to +30.0)
- ours right_hip_roll: -12.7 to +3.0 deg (MJCF range -25.0 to +25.0)
- ours right_hip_pitch: +32.9 to +49.9 deg (MJCF range -30.0 to +70.0)
- ours right_knee: +68.4 to +90.9 deg (MJCF range -90.0 to +90.0)
- ours right_ankle: -46.3 to -26.9 deg (MJCF range -90.0 to +90.0)

### C1 Every netlist part maps to a BOM line, and every BOM_FULL quantity matches its source (CAD, netlist, fasteners): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c1_bom_coverage.py`. Finished 2026-11-07 02:02 UTC, 0 s.
- inline parts on cables: XT30U on P13 (line 12)
- netlist: 75 components, 17 splices (made from wire and heat shrink, BOM 26), 58 mapped to BOM lines, unmapped none
- 'BOM xx' references in the netlist text: 32, to missing lines: none
- line DK5 is bought by length or weight (Need 1 set): its 2 parts are cut from it, no piece count
- line E10 is bought by length or weight (Need 0.3 m): its 3 parts are cut from it, no piece count
- components per BOM line vs Need: 36 lines, mismatches none
- BOM_FULL.md: 242 rows, generated 2026-11-07 01:51 UTC
- printed rows: 45 rows, 64 pieces; CAD printed nodes 62 (+ 2 antenna rods)
- horns in CAD {'horn_drive': 14, 'horn_idle': 14}, inserts 48, bearings 3
- cables: BOM_FULL 61 rows, netlist 61 active cables
- wire per gauge and colour: 16 BOM_FULL rows checked against the netlist cut sums, 0 differ
- washers in fasteners.json: 8 under 4 fitted screws; fresh BOM_FULL line 17l row: F21 8 pcs
- fitted screws in fasteners.json: 324; BOM_FULL screw rows 12 (section Fasteners)
- committed BOM_FULL.md vs a fresh build from today's sources (E4, 2026-11-07 02:02 UTC): 0 quantities differ, 0 rows gone, 0 new
- heat shrink: the rule gives 42 sleeves (4 XT30 cups, 2 caps, 19 lead joints, 17 splices; the 58 splice ends sit in those splices); fresh BOM_FULL 42 pieces; the 3D view draws 42 sleeve nodes for 42 joints; BOM 26 buys 1 x 180 = 180 pieces
- purchase status from the fresh build (E4): {'printed': 45, 'bought': 99, 'in kit': 24, 'made': 48, 'tool': 26}
- BOM.md lines used by a BOM_FULL row: 105 of 105 (unused: none)

### C2 Connectors: every wired pin has a mating part or end treatment; crimps fit the Molex 08-70-1040: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c2_connectors.py`. Finished 2026-11-07 02:02 UTC, 0 s.
- 171 wires on active cables, 342 wire ends, every end treatment checked against its pin group (23 classes)
- made-lead housings (Molex 50-37-5033): 7, SV10 bus2 3 pos, SV14 bus1 2 pos, SV20 bus2 3 pos, SV24 bus1 2 pos, SV30 bus2 3 pos, U2 h3 2 pos, U2 h5 2 pos; crimp terminals (08-70-1040): 17
- housings: netlist 7, BOM 21 Need 7 (Buy 10), CABLE_MAP 7, WIRING.md 7
- terminals: netlist 17, BOM 22 Need 17 (Buy 30), CABLE_MAP 17, WIRING.md 17
- mating parts and end treatment supplies on a BOM line: 9 of 9 (5264 socket, made lead: 21, 5264 socket, made lead terminal: 22, 5264 socket, kit cable: 1, XT30 cup: 12, USB-C and micro-USB: 20, camera FPC: E7,E7r, crimp tool: T3, splices and solder joints: heat shrink: 26,T10, solder joints: solder: 30)
- kit cables used 11 (S10, S11, S12, S13, S2, S3, S4, S5, S7, S8, S9) of 12 shipped (one per servo, BOM line 1)
- crimp ends by gauge: {'22 AWG': 17}
- 08-70-1040 data from CABLE_MAP.md: wire 22, 24, 26, 28 AWG, insulation 1.90 mm max, current 22: 3.0, 24: 2.5, 26: 2.0, 28: 1.5 A by AWG; sources https://www.rcscomponents.kiev.ua/datasheets/mx5263-datasheet.pdf, https://static.chipdip.ru/lib/750/DOC031750234.pdf (read 2026-11-02 1:29 AM ET; 2026-11-02 1:45 AM ET)
- 22 AWG silicone OD 1.7 +/- 0.1 mm vs 08-70-1040 insulation max 1.90 mm (Molex): fits, 0.1 mm left at the top of the tolerance
- crimped wires with a netlist current: 10 checked against the terminal current for their gauge, 0 over; 7 have no per-wire current in the netlist (the servo chain currents through these contacts are checked by C7 from the sim)
- connector pins not wired and not marked nc: none

### C3 Every active cable has a 3D route whose worst length plus slack fits its cut, a service loop at every joint, and a hold at every tie point: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c3_cables3d.py`. Finished 2026-11-07 02:07 UTC, 6 s.
- cables3d.json 2026-11-02 04:50 UTC (checked 2026-11-07 01:48 UTC): 61 cables, 143 cable ends, 75 retention items; netlist 61 active cables
- series pieces summed: P7 XT30.M+ -> F1.IN = XT30-JFI 30 + JFI-F1 90 = 120 mm (inline splice JFI, not routed in 3D); P7 F1.OUT -> DK7.VIN = F1-JFO 90 + JFO-DK7 40 = 130 mm (inline splice JFO, not routed in 3D)
- floating splices (judged by chain): G, J5, JFI, JFO, JG, JG10, JG20, JG30, JGD, JSN, VSW, YD3, YG3; fixed: JBN the BEC output leads end there (lead length not published); JBP the BEC output leads end there (lead length not published); SPG seated on the belly (MOUNTING.md, servo power splices: cable tie or foam tape); SPV seated on the belly (MOUNTING.md, servo power splices: cable tie or foam tape)
- twist (D25, NASA-STD-8739.4A 7.2.16 to 7.2.18): 15 made multi-wire cables twisted (D10 x1.028, D14 x1.028, D15 x1.028, D16 x1.024, D19 x1.024, D2 x1.024, D21 x1.024, D3 x1.024, D4 x1.024, D6 x1.019, P13 x1.019, SD1 x1.019 branch b, SP3 x1.019, SP4 x1.019, SP5 x1.019); 19 not, with the reason in the netlist; chain lengths below carry the take-up at the shortest lay
- length by chain: 158 wires in 166 chains (4 chains with an unpublished cut skipped: BEC leads); 0 chains cannot reach (worst routed over the summed cut); 8 wires reach but with less than the 40 mm service slack (test fit); 150 have the full slack
- wires short of the slack alone that pass by chain (their splice floats): SP1 JG20.S>SV20.BUS2.G cut 30, route 25, chain margin 18 mm; SP2 JG10.S>SV10.BUS2.G cut 30, route 25, chain margin 11 mm; SP3 JG30.S>SV30.BUS2.G cut 30, route 24, chain margin 22 mm; SD1 U2.H3.D>YD3.S cut 30, route 26, chain margin 7 mm; SD1 U2.H3.G>YG3.S cut 45, route 26, chain margin 22 mm; SD1 YG3.S>JG30.S cut 140, route 103, chain margin 22 mm
- service loops (recomputed from the route and robot.urdf, 61 samples per joint, 21 x 21 for a two-joint loop): 58 crossings in 49 loops (9 loops span two crossings); 43 loops meet 3 x OD in both models over the full URDF range, 43 within the Runtime head ranges ({'head_pitch': (-0.78, 0.3), 'head_yaw': (-0.5, 0.5), 'head_roll': (-0.5, 0.5)} from ../upstream/Open_Duck_Mini_Runtime/mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py)
- two-crossing loops (no tie on the short link between them): SP5 right_hip_yaw+right_hip_roll: free 33 mm, bend R 34.1, storage R 10.8 mm (loop 33 over a 21.7 mm chord), needs 10.2; P13 head_pitch+head_yaw: free 41 mm, bend R 11.6, storage R 17.8 mm (loop 83 over a 25.6 mm chord), needs 10.8; D1 head_pitch+head_yaw: free 40 mm, bend R 11.3, storage R 17.3 mm (loop 82 over a 23.9 mm chord), needs 10.5; D2 head_pitch+head_yaw: free 42 mm, bend R 11.7, storage R 18.0 mm (loop 84 over a 26.2 mm chord), needs 10.4; D3 head_yaw+head_pitch: free 46 mm, bend R 12.9, storage R 19.8 mm (loop 87 over a 31.9 mm chord), needs 10.4; D4 head_yaw+head_pitch: free 46 mm, bend R 12.9, storage R 19.8 mm (loop 87 over a 31.9 mm chord), needs 10.4; D13 head_pitch+head_yaw: free 41 mm, bend R 11.5, storage R 17.8 mm (loop 83 over a 25.7 mm chord), needs 4.5; S12 head_pitch+head_yaw: free 40 mm, bend R 11.3, storage R 17.5 mm (loop 81 over a 25.6 mm chord), needs 7.8; D22 head_pitch+head_yaw: free 42 mm, bend R 11.7, storage R 18.0 mm (loop 84 over a 26.2 mm chord), needs 4.5
- head yaw loops: P13 head_pitch+head_yaw: full URDF range bend R 11.6, storage R 17.8; Runtime ranges bend R 32.3, storage R 17.9; needs 10.8 mm (meets); D1 head_pitch+head_yaw: full URDF range bend R 11.3, storage R 17.3; Runtime ranges bend R 31.5, storage R 17.8; needs 10.5 mm (meets); D2 head_pitch+head_yaw: full URDF range bend R 11.7, storage R 18.0; Runtime ranges bend R 32.6, storage R 18.0; needs 10.4 mm (meets); D3 head_yaw+head_pitch: full URDF range bend R 12.9, storage R 19.8; Runtime ranges bend R 36.1, storage R 20.7; needs 10.4 mm (meets); D4 head_yaw+head_pitch: full URDF range bend R 12.9, storage R 19.8; Runtime ranges bend R 36.0, storage R 20.6; needs 10.4 mm (meets); D13 head_pitch+head_yaw: full URDF range bend R 11.5, storage R 17.8; Runtime ranges bend R 32.1, storage R 17.8; needs 4.5 mm (meets); S12 head_pitch+head_yaw: full URDF range bend R 11.3, storage R 17.5; Runtime ranges bend R 31.6, storage R 17.4; needs 7.8 mm (meets); D22 head_pitch+head_yaw: full URDF range bend R 11.7, storage R 18.0; Runtime ranges bend R 32.6, storage R 18.0; needs 4.5 mm (meets)
- retention: 75 tie points: 51 adhesive tie mount, 13 bundle tie, test fit, 6 existing printed feature, 3 drilled printed feature, 2 cable tie to a neighbour cable; stick-on mounts by fit (exact-ray flat patch, cables3d): MB3A 19 x 19 mm (BOM 34) 27, ABM1M-AT-C 12.7 x 12.7 mm (BOM 34b) 24, of them on an STS3215 case 0; no fit 0; drilled tie-hole pairs 3; tied to a neighbour 2; bundle tie, test fit 9; open 0; 15 tie points share the anchor of a nearby one (one anchor per spot, one tie round both)
- drilled tie-hole pairs (D25 ii; 4.0 mm, the BOM T14 bit; edge distance and web >= 1.6 mm; walls 1.6 to 12 mm; screws, inserts and empty holes >= 1.6 mm off; 1.5 mm free behind the wall; >= 1 mm from moving parts; print/PRINT_PLAN.md After printing): T014 D1,D2,D3,D4,P13,D13,D22 on neck_right_sheet: 2 x 4.0 mm, 12.1 mm apart, walls 5.8/5.8 mm, 18 mm from the cable line, strap path about 47 mm, 6.2 mm from moving parts over the sweep; T072 S5 on shin_right_sheet: 2 x 4.0 mm, 7.0 mm apart, walls 3.8/3.8 mm, 9 mm from the cable line, strap path about 22 mm, 2.9 mm from moving parts over the sweep; T084 S12 on neck_right_sheet: 2 x 4.0 mm, 7.0 mm apart, walls 1.9/1.9 mm, 20 mm from the cable line, strap path about 19 mm, 6.0 mm from moving parts over the sweep
- tied to a neighbour cable (D25 i): T079 S9 to SP5 (held by T047); T082 S11 to D3 (held by T014)
- BOM line 32 Need: 75 along the cables (cables3d.json retention, file of 2026-11-02 4:31 AM ET: 27 through line 34 MB3A mounts, 24 through line 34b ABM1M-AT-C mounts (D59); 3 thro; line 34 Need: 27 (cables3d.json retention, file of 2026-11-02 4:31 AM ET: the spots where a flat 19 x 19 mm patch with 4.8 mm free hei; line 34b Need: 24 (cables3d.json retention, file of 2026-11-02 4:31 AM ET; D59 sit: 23 to 24, +3 from line 34, -2 where the cuts took t
- route changes tried and not kept (cuts would not fit with the slack): T026: route change tried and not kept: the MB3A patch is on the underside of head_bot_sheet, 28.6 mm below the bundle, so the bundle drops under the head floor and back; the worst routes of D2, D3 and D4 grow by 83 to 84 mm and D2 (cut 550 mm) and D3 (cut 900 mm) would reach with 18 to 25 mm less than the 40 mm slack; T089: route change tried and not kept: the MB3A patch is on the outer -y face of body_middle_bottom, 33.9 mm away; the SP5 worst route grows from 377 to 440 mm, 448 mm with the twist take-up, past the 430 mm cut
- cables3d's own check field: {'pass with notes': 43, 'pass': 15, 'test fit': 3}

### C4a Every fitted screw has a BOM line, a length that line buys, and a count it covers (fasteners.json vs BOM.md): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py`. Finished 2026-11-07 02:07 UTC, 0 s.
- fasteners.json: 419 records, 361 screws, 324 fitted (left out: {'LEAVE OUT (D38 screw cut)': 19, 'LEAVE OUT (D42 uniform pattern)': 2, 'LEAVE OUT (D39 screw cut)': 3, 'LEAVE OUT (D18)': 2, 'NOT FITTED': 11}), 58 inserts
- line 1 (STS3215 servo bag (18 screws per servo, B2)): 115 screws, {'M2x6 self-tapping pan head': 42, 'PA2.0 self-tapping (factory)': 56, 'M3x6 machine screw (Feetech rocker screw)': 14, 'PA3.0x5 self-tapping, washer head (Feetech idle screw)': 3}
- line 14 (SG90 bag): 6 screws, {'SG90 bag horn screw': 2, 'SG90 bag mounting screw': 4}
- line 17a M3x8 SHCS: schedule 18 (18 M3x8 DIN 912 A2); BOM Need 18, Buy 33 each
- line 17b M3x10 SHCS: schedule 12 (12 M3x10 DIN 912 A2); BOM Need 12, Buy 14 each
- line 17c M3x12 SHCS: schedule 2 (2 M3x12 DIN 912 A2); BOM Need 2, Buy 3 each
- line 17d M3x6 SHCS: schedule 78 (78 M3x6 DIN 912 A2); BOM Need 78, Buy 100 100
- line 17e M3x5 SHCS: schedule 28 (28 M3x5 DIN 912 A2); BOM Need 28, Buy 33 each
- line 17f M2.5x6 SHCS: schedule 13 (13 M2.5x6 DIN 912 A2); BOM Need 13, Buy 20 each
- line 17g M2.5x8 SHCS: schedule 4 (4 M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers); BOM Need 4, Buy 10 each
- line 17h M2 self-tapping kit: schedule 32 (2 M2x8 self-tapping pan head, 24 M2x5 self-tapping pan head, 2 M2x4 self-tapping pan head, 4 M2x6 self-tapping pan head); BOM Need 32 (M2x5 24, M2x6 4, M2x4 2, M2x8 2; D38: 2 camera screws out; D47: 4 M2x6 for the two mic boards), Buy 1 kit
- line 17h kit, count per size from the line text ('50 each of M2x4, M2x5, M2x6, M2x8 and M2.6x6, x8, x10, x12'; '50 pcs of each size'): M2x5 24 of 50, M2x6 4 of 50, M2x8 2 of 50, M2x4 2 of 50
- line 17i M2.5x10 SHCS: schedule 4 (4 M2.5x10 DIN 912 A2); BOM Need 4, Buy 5 each
- line 17j M3x6 button head: schedule 10 (10 M3x6 ISO 7380 A2 button head); BOM Need 10, Buy 12 each
- line 17k M2.5x5 SHCS: schedule 2 (2 M2.5x5 DIN 912 A2); BOM Need 2, Buy 5 each
- inserts: 48 in fasteners.json, BOM 16 Need 48

### C4b No screw head or tip collision over the joint ranges, except known, decided ones (fasteners sweep vs D18 and D19): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py`. Finished 2026-11-07 02:07 UTC, 0 s.
- sweep: 37 steps per joint, 13 joint pairs, 489 hit rows; fitted screws by status {'NEAR': 81, 'PARTS COLLIDE FIRST': 85, 'CONTACT': 117, 'HIT': 29, 'CLEAR': 12}
- screws named in a DECIDED entry of DECISIONS.md: F002 (D19), F010 (D19), F196 (D19), F198 (D19), F200 (D19), F209 (D19), F211 (D19), F213 (D19), F247 (D19), F254 (D19)
- hit rows on fitted screws by class: {'parts collide first': 272, 'static contact': 162, 'static overlap': 27, 'screw': 2}
- screw-limited and static-overlap hits by screw: button head still hits 2; stand-in head (size not published) 26; against a CAD body the build replaces 1
- parts collide before the screw: 272 rows; static contact under 0.1 mm at the zero pose: 162 rows
- collision onset vs the sim walk envelope: F198: hits from left_hip_yaw +23.3 deg, the sim walk uses -5.3 to +10.3 deg (E9); F211: hits from right_hip_yaw -23.3 deg, the sim walk uses -6.0 to +5.9 deg (E9)
- D18 screws marked in fasteners.json: 2 (F124, F136)

### C5 Servo IDs agree everywhere (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime code and config, bench, sim, policy order): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c5_servo_ids.py`. Finished 2026-11-07 02:02 UTC, 0 s.
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
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c6_gpio.py`. Finished 2026-11-07 02:02 UTC, 0 s.
- Runtime 376de65 / Pi hardware: left foot GPIO22, right foot GPIO27, left eye GPIO24, right eye GPIO23, projector GPIO25, left antenna GPIO13, right antenna GPIO12, I2C SDA GPIO2, I2C SCL GPIO3, I2S BCLK GPIO18, I2S LRC GPIO19, I2S DIN GPIO21
- netlist: 12 of 12 functions on the Runtime GPIO and the right header pin
- WIRING.md: 12 of 12 functions on the Runtime GPIO and the right header pin
- D9: 7 of 7 functions on the Runtime GPIO and the right header pin
- CABLE_MAP.md: 7 of 7 functions on the Runtime GPIO and the right header pin
- HARNESS_BUILD.md: 12 of 12 functions on the Runtime GPIO and the right header pin
- netlist header pins used for signals: 3 I2C SDA, 5 I2C SCL, 12 I2S BCLK, 13 right foot, 15 left foot, 16 right eye, 18 left eye, 22 projector, 32 right antenna, 33 left antenna, 35 I2S LRC, 40 I2S DIN

### C7 Current ratings: every wire, contact and part on the servo power path as wired now (D15 plus the D23 feeds SP4 and SP5) vs the simulated currents (sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py`. Finished 2026-11-07 02:04 UTC, 1 s.
- traces: walk_backlash, walk_rough_backlash, walk_pushes, walk_side_0.2, turn_1.0 (E5 run); servo supply current = positive electrical power / 6.0 V + 0.05 A quiescent (an upper estimate; on the 7.4 V basis of CURRENT_BUDGET.md the currents are 0.81 x these); split over the as-built network (sim/power_fix.py option ab, netlist altaay_lab/wiring/netlist.yaml sha256 293658e198), both corners, the worse counts
- P11 (BEC splice JB+ to SPV, 16 AWG; the BEC leads are in part D) (16 AWG): mean 4.70 A, worst 100 ms 6.52 A, 20 ms 9.05 A, 2 ms 10.93 A; limit 22.0 A (16 AWG); worst 100 ms in walk_backlash, typical corner
- SP1 (22 AWG): mean 0.85 A, worst 100 ms 1.65 A, 20 ms 2.61 A, 2 ms 3.36 A; limit 7.0 A (22 AWG); worst 100 ms in walk_pushes, typical corner
- S2 (kit cable, assumed 26 AWG): mean 0.78 A, worst 100 ms 1.49 A, 20 ms 2.47 A, 2 ms 3.16 A; limit 2.2 A (26 AWG); worst 100 ms in walk_pushes, typical corner
- S3 (kit cable, assumed 26 AWG): mean 0.58 A, worst 100 ms 1.14 A, 20 ms 2.14 A, 2 ms 2.72 A; limit 2.2 A (26 AWG); worst 100 ms in walk_backlash, typical corner
- S4 (kit cable, assumed 26 AWG): mean 0.39 A, worst 100 ms 0.77 A, 20 ms 1.37 A, 2 ms 1.63 A; limit 2.2 A (26 AWG); worst 100 ms in walk_backlash, typical corner
- S5 (kit cable, assumed 26 AWG): mean 0.84 A, worst 100 ms 1.58 A, 20 ms 2.89 A, 2 ms 3.53 A; limit 2.2 A (26 AWG); worst 100 ms in walk_backlash, high-side corner
- SP4 (second feed, left ankle) (22 AWG): mean 1.15 A, worst 100 ms 1.97 A, 20 ms 3.41 A, 2 ms 4.33 A; limit 7.0 A (22 AWG); worst 100 ms in walk_backlash, high-side corner
- SP2 (22 AWG): mean 0.85 A, worst 100 ms 2.23 A, 20 ms 3.33 A, 2 ms 4.10 A; limit 7.0 A (22 AWG); worst 100 ms in walk_side_0.2, typical corner
- S7 (kit cable, assumed 26 AWG): mean 0.78 A, worst 100 ms 2.12 A, 20 ms 3.20 A, 2 ms 3.95 A; limit 2.2 A (26 AWG); worst 100 ms in walk_side_0.2, typical corner
- S8 (kit cable, assumed 26 AWG): mean 0.60 A, worst 100 ms 1.27 A, 20 ms 2.11 A, 2 ms 2.69 A; limit 2.2 A (26 AWG); worst 100 ms in walk_rough_backlash, typical corner
- S9 (kit cable, assumed 26 AWG): mean 0.44 A, worst 100 ms 0.83 A, 20 ms 1.38 A, 2 ms 1.55 A; limit 2.2 A (26 AWG); worst 100 ms in walk_rough_backlash, typical corner
- S10 (kit cable, assumed 26 AWG): mean 0.87 A, worst 100 ms 1.78 A, 20 ms 2.66 A, 2 ms 3.26 A; limit 2.2 A (26 AWG); worst 100 ms in walk_rough_backlash, high-side corner
- SP5 (second feed, right ankle) (22 AWG): mean 1.17 A, worst 100 ms 2.10 A, 20 ms 3.34 A, 2 ms 4.02 A; limit 7.0 A (22 AWG); worst 100 ms in walk_rough_backlash, high-side corner
- SP3 (22 AWG): mean 0.85 A, worst 100 ms 1.52 A, 20 ms 2.88 A, 2 ms 3.76 A; limit 7.0 A (22 AWG); worst 100 ms in turn_1.0, typical corner
- S11 (kit cable, assumed 26 AWG): mean 0.76 A, worst 100 ms 1.44 A, 20 ms 2.80 A, 2 ms 3.67 A; limit 2.2 A (26 AWG); worst 100 ms in turn_1.0, high-side corner
- S12 (kit cable, assumed 26 AWG): mean 0.46 A, worst 100 ms 1.09 A, 20 ms 2.36 A, 2 ms 3.12 A; limit 2.2 A (26 AWG); worst 100 ms in walk_backlash, typical corner
- S13 (kit cable, assumed 26 AWG): mean 0.19 A, worst 100 ms 0.61 A, 20 ms 1.32 A, 2 ms 1.46 A; limit 2.2 A (26 AWG); worst 100 ms in walk_pushes, typical corner
- ground network, P11 G (BEC splice JB- to SPG): walk_backlash typical 4.61 A mean (98 % of all servo return current), worst over cases and corners 4.61 A mean, 6.41 A worst 100 ms, 10.75 A max
- ground network, SP1 G (SPG to JG20): walk_backlash typical 0.84 A mean (18 % of all servo return current), worst over cases and corners 0.84 A mean, 1.41 A worst 100 ms, 2.56 A max
- ground network, SP1 G tail (JG20 to ID 20): walk_backlash typical 0.85 A mean (18 % of all servo return current), worst over cases and corners 0.85 A mean, 1.65 A worst 100 ms, 3.40 A max
- ground network, SP4 G (SPG to ID 24 BUS 1): walk_backlash typical 1.07 A mean (23 % of all servo return current), worst over cases and corners 1.15 A mean, 1.97 A worst 100 ms, 4.32 A max
- ground network, SP2 G (SPG to JG10): walk_backlash typical 0.83 A mean (18 % of all servo return current), worst over cases and corners 0.83 A mean, 1.90 A worst 100 ms, 3.48 A max
- ground network, SP2 G tail (JG10 to ID 10): walk_backlash typical 0.85 A mean (18 % of all servo return current), worst over cases and corners 0.85 A mean, 2.24 A worst 100 ms, 4.12 A max
- ground network, SP5 G (SPG to ID 14 BUS 1): walk_backlash typical 1.08 A mean (23 % of all servo return current), worst over cases and corners 1.17 A mean, 2.10 A worst 100 ms, 4.02 A max
- ground network, SP3 G (SPG to JG30): walk_backlash typical 0.79 A mean (17 % of all servo return current), worst over cases and corners 0.79 A mean, 1.22 A worst 100 ms, 2.98 A max
- ground network, SP3 G tail (JG30 to ID 30): walk_backlash typical 0.85 A mean (18 % of all servo return current), worst over cases and corners 0.85 A mean, 1.52 A worst 100 ms, 3.76 A max
- ground network, SD1 branch a G (YG3 to JG20): walk_backlash typical 0.16 A mean (3 % of all servo return current), worst over cases and corners 0.16 A mean, 0.35 A worst 100 ms, 0.88 A max
- ground network, SD1 branch b G (YG3 to JG30): walk_backlash typical 0.15 A mean (3 % of all servo return current), worst over cases and corners 0.15 A mean, 0.33 A worst 100 ms, 1.06 A max
- ground network, SD1 stem G (adapter H3 G terminal): walk_backlash typical 0.09 A mean (2 % of all servo return current), worst over cases and corners 0.10 A mean, 0.26 A worst 100 ms, 0.54 A max
- ground network, SD2 G (adapter H5 G terminal): walk_backlash typical 0.07 A mean (2 % of all servo return current), worst over cases and corners 0.11 A mean, 0.35 A worst 100 ms, 0.66 A max
- ground network, adapter ground copper H3 G side: walk_backlash typical 0.09 A mean (2 % of all servo return current), worst over cases and corners 0.10 A mean, 0.26 A worst 100 ms, 0.54 A max
- ground network, adapter ground copper H5 G side: walk_backlash typical 0.07 A mean (2 % of all servo return current), worst over cases and corners 0.11 A mean, 0.35 A worst 100 ms, 0.66 A max
- ground network, USB cable ground (adapter to Pi): walk_backlash typical 0.09 A mean (2 % of all servo return current), worst over cases and corners 0.09 A mean, 0.12 A worst 100 ms, 0.20 A max
- ground network, P12 G (Pi pin 6 to regulator): walk_backlash typical 0.09 A mean (2 % of all servo return current), worst over cases and corners 0.09 A mean, 0.12 A worst 100 ms, 0.20 A max
- E6 ngspice probes (as built, worst case): adapter H3 G 0.05 A RMS, 0.15 A worst 100 ms; H5 G 0.08 A RMS, 0.12 A worst 100 ms; USB ground 0.07 A RMS, 0.10 A worst 100 ms (trained mass (E5), fall after a push, pack low, high-side R)
- E6 ngspice as-built cases (trained mass (E5) and our build (C8)): walking at full and nominal pack: pack mean up to 5.68 A, RMS up to 5.94 A (our build (C8), walk, backlash, pack nominal, high-side R), worst 100 ms 7.04 A; at the low pack (6.6 V, past the battery guard) RMS up to 6.04 A (our build (C8), walk, backlash, pack low, typical R); any case 2 ms max 11.60 A (trained mass (E5), fall after a push, pack low, high-side R); BEC out RMS up to 4.54 A, max 9.43 A; BEC input (P10) RMS 5.10 A; 5 V branch (P13) RMS 0.89 A
- fuse 15 A ATO (F1): 5.94 A (RMS vs 75% of rating ([I] Littelfuse derating rule of thumb, not read this session)) vs 11.25 A, margin 47%
- fuse holder 20 A (F1): 5.94 A (RMS) vs 20.00 A, margin 70%
- BMS working current (Tenergy 10 A): 5.94 A (RMS) vs 10.00 A, margin 41%
- BMS over-current trip, lowest of 22 +/- 5 A: 11.60 A (2 ms max, any case) vs 17.00 A, margin 32%
- main switch Pololu 2815, 6.0 A continuous at 55 C: 5.94 A (RMS walking) vs 6.00 A, margin 1%
- main switch Pololu 2815, 16 A continuous at 150 C: 11.60 A (2 ms max, any case) vs 16.00 A, margin 27%
- XT30U 15 A: 5.94 A (RMS) vs 15.00 A, margin 60%
- cells 30 A continuous each: 11.60 A (2 ms max) vs 45.00 A, margin 74%
- BEC 20 A peak: 9.43 A (2 ms max, any case) vs 20.00 A, margin 53%
- BEC 15 A continuous (with 5 mph air): 4.54 A (RMS walking) vs 15.00 A, margin 70%
- BEC output leads, 5 A per 3-pin lead, 2 leads: 2.27 A (RMS per lead, equal split as the netlist; 2 ms max 4.72 A) vs 5.00 A, margin 55%
- TEST_PLAN.md 4.2 has the 10-minute 6.0 A heat check of the 2815 (board under 50 C): True
- P1 (16 AWG, PACK.B+ to BMS.B+): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P2 (16 AWG, PACK.B- to BMS.B-): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P6 (16 AWG, BMS.P+ to XT30.F+): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P8 (16 AWG, BMS.P- to XT30.F-): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P7 (16 AWG, XT30.M+ to JFI.S): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P14 (16 AWG, XT30.M- to G.S): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P9 (16 AWG, SW1.VOUT to VSW.S): as built 5.68 A mean, 7.04 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 5.66, i_peak_a 7.04
- P10 (16 AWG, VSW.S to U1.IN+): as built 4.79 A mean, 6.25 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 4.77, i_peak_a 6.23
- P11 (16 AWG, JBP.S to SPV.S): as built 4.27 A mean, 5.59 A worst 100 ms (walking, ngspice); limit 22.0 A; netlist writes i_mean_a 4.25, i_peak_a 5.56
- P13 (20 AWG, VSW.S to U3.VIN): as built 0.89 A mean, 0.91 A worst 100 ms (walking, ngspice); limit 11.0 A; netlist writes i_mean_a 0.48, i_peak_a 1.91
- stacked fall estimate (CURRENT_BUDGET.md): about 17 A for about 20 ms vs BMS trip 17 to 27 A after 4 to 12 ms
- adapter U2: 5 wires, 0 on a power net (D15: none)
- cross-check, E6 ngspice worst 100 ms (actual bus voltage) vs this split (6.0 V currents): SP1 1.54 vs 1.65 A, SP4 1.56 vs 1.97 A, SP2 1.13 vs 2.23 A, SP5 1.58 vs 2.10 A, SP3 1.55 vs 1.52 A

### C8 The stock policy walks the robot we will build (2.79 kg, sim/MASS_BUDGET.md) on flat ground (sim/added_mass_sim.py, sim pass only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c8_policy_mass.py`. Finished 2026-11-07 02:09 UTC, 0 s.
- model mass: stock 2.1071 kg (trained 2.107 kg), ours 2.7881 kg (MASS_BUDGET.md 2.79 kg)
- stock copy reproduces the CURRENT_BUDGET.md bus means in 7 of 7 cases
- ours, Stand, zero command: falls none; tracking - (doc -); seeds fell not run (stand)
- ours, Walk forward 0.15 m/s: falls none; tracking 0.66 (doc -); seeds fell 0 of 6
- ours, Turn 1.0 rad/s: falls none; tracking 0.79 (doc -); seeds fell 0 of 6
- ours, Walk sideways 0.2 m/s: falls none; tracking 0.22 (doc -); seeds fell 0 of 6
- ours, Walk forward, backlash model: falls none; tracking 0.90 (doc -); seeds fell 0 of 6
- ours, Walk forward, 15 N pushes every 3 s: falls none; tracking 0.62 (doc -); seeds fell 0 of 6
- rough terrain, start raised 23 mm: stock falls [9.14], ours falls [4.88] (not a flat-ground case; ADDED_MASS_SIM.md finding 4)

### C9 Docs agree: numbers that appear in several docs are the same everywhere: PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c9_docs.py`. Finished 2026-11-07 02:09 UTC, 1 s.
- HARDWARE_AUDIT.md section 6: 73 blockers; cleared or decided 30; test print 7; open 29 (22 assembly or bench, 7 waiting on parts: B8, B33, B38, B42, B43, B53, B72)
- blocker count mentions checked: 12
- 'Bnn cleared' mentions outside HARDWARE_AUDIT.md: 9
- BOM.md: build 1258.70, with expression 1387.84, with tools 1659.50; test order 228.49
- totals quoted as current outside BOM.md: 5 checked
- part counts (viewer run E4): printed parts 62/62, servos 14/14, inserts 48/48, bearings 3/3
- print/ STL files: 44
- screws: HARDWARE_AUDIT B1 ?; BOM.md screw lines 17a/b/c/d/e/f/g/i/h/j/k Need 203; fasteners.json 203 to buy (17x lines and no line) of 324 fitted; MASS_BUDGET.md model 274
- decisions: DECISIONS.md last is D59
- upstream items: UPSTREAM_ISSUES.md total 137
- WIRING.md section 4 currents vs netlist: 42 values compared
- STATE.md print numbers (46.8, 17.6, 1360.4, 17.6, 119.9, 1407.2, 35.1, 126.9) found in print/PRINT_PLAN.md, SLICE_SUMMARY.md or PRINT_CHECK.md: 8 of 8
- print/PRINT_PLAN.md PLA: coupon session 46.8 g + full print (220 bed) 1360.4 g = 1407.2 g (table total 1407.2 g); BOM 27 need 1407 g

### C10 Wiring sheets cover every wire of the netlist (wiring/sheets, run on a copy): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c10_sheets.py`. Finished 2026-11-07 02:07 UTC, 15 s.
- make_sheets.py on a copy: exit 0; sheet 1: 1_power.png 929109 bytes, svg 596508 bytes, full 53, stubs 0, crossings 49; sheet 2: 2_servo_bus.png 840085 bytes, svg 526249 bytes, full 48, stubs 7, crossings 2; sheet 3: 3_pi_sensors.png 800599 bytes, svg 468379 bytes, full 17, stubs 16, crossings 1; sheet 4: 4_head_expression.png 698826 bytes, svg 463514 bytes, full 37, stubs 0, crossings 72; sheet 5: 5_harness.png 931970 bytes, svg 618335 bytes, full 0, stubs 0, crossings 10; sheet 6: 6_touch_cliff.png 562241 bytes, svg 359093 bytes, full 19, stubs 0, crossings 25
- sheets built: 1 1_power (full 53, stubs 0), 2 2_servo_bus (full 48, stubs 7), 3 3_pi_sensors (full 17, stubs 16), 4 4_head_expression (full 37, stubs 0), 5 5_harness (full 0, stubs 0), 6 6_touch_cliff (full 19, stubs 0); active wires drawn in full: 171 of 171
- committed sheet SVGs: 7, older than netlist.yaml: none

### C11 Hip yaw the stock policy uses (walk and turn) stays under the F198/F211 collision onset (21.7 deg): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c11_hip_yaw_envelope.py`. Finished 2026-11-07 02:07 UTC, 0 s.
- collision onset: FASTENERS.md 23.3, 23.3 deg; fasteners.json sweep F198 left_hip_yaw from 23.3 deg, F211 right_hip_yaw from 23.3 deg; used 23.3 deg
- ours, turn_1.0: largest |hip yaw| 10.3 deg (largest |target| 8.9 deg; largest |action| 0.61 left, 0.50 right)
- ours, walk_backlash: largest |hip yaw| 5.6 deg (largest |target| 4.5 deg; largest |action| 0.30 left, 0.33 right)
- ours, walk_forward_0.15: largest |hip yaw| 5.7 deg (largest |target| 4.3 deg; largest |action| 0.27 left, 0.32 right)
- ours, walk_pushes: largest |hip yaw| 5.7 deg (largest |target| 5.2 deg; largest |action| 0.35 left, 0.33 right)
- ours, walk_side_0.2: largest |hip yaw| 5.7 deg (largest |target| 4.7 deg; largest |action| 0.27 left, 0.34 right)
- stock, turn_1.0: largest |hip yaw| 10.3 deg (largest |target| 9.0 deg; largest |action| 0.62 left, 0.49 right)
- stock, walk_backlash: largest |hip yaw| 5.6 deg (largest |target| 4.7 deg; largest |action| 0.30 left, 0.34 right)
- stock, walk_forward_0.15: largest |hip yaw| 5.6 deg (largest |target| 4.5 deg; largest |action| 0.27 left, 0.33 right)
- stock, walk_pushes: largest |hip yaw| 5.6 deg (largest |target| 5.3 deg; largest |action| 0.36 left, 0.33 right)
- stock, walk_side_0.2: largest |hip yaw| 5.6 deg (largest |target| 4.8 deg; largest |action| 0.26 left, 0.35 right)
- the joint passes its commanded target by up to 1.4 deg in the sim (dynamics)
- worst over 10 runs: 10.3 deg (stock, turn_1.0); turn 1.0 rad/s: stock 10.3 deg, ours 10.3 deg; margin to the 23.3 deg onset: 13.0 deg
- policy output on 6000 random observations (scale 1, 3, 10): largest |action| 1.0000 (bounded by 1, as a tanh output is); hip yaw target bound = default 0.2 deg + 0.25 x 1 rad = 14.5 deg
- the stock policy cannot command more than 14.5 deg of hip yaw (15.9 deg with the sim overshoot), 7.4 deg under the onset
- Runtime 376de65: motor target = init_pos + action x action_scale at line 290; live clip of the targets: none; commented-out clip at lines [292]; servo angle limit registers set by configure_motor.py or the HWI: False

### C12 The charging dock: parts, fits, screws, wiring, routes, BOM against the model (twin/dock, CAD check only): PASS
Command: `VERIFY_OUT=<out> python3 altaay_lab/verify/c12_dock.py`. Finished 2026-11-07 02:07 UTC, 13 s.
- fail-closed tests (test_dock_checks.py): 3 passed in 1.05s
- printed kinds 18, prints 21; not watertight or off the bed: none
- components 96 (dock), 96 (docked); interferences 0; paddle motion poses with a hit 0 of 9
- fasteners: 41 screws, 18 nuts, 20 inserts; not OK: none
- fasteners seated on their host parts in the dock state: all
- fasteners seated on their host parts in the docked state: all
- tipping, walk-in push on the paddle, +x: 3.42x about [218.0, -130.0] (target 3x)
- tipping, seated duck at the seat's back corner, its weight off-centre, with the paddle push: 16.62x about [218.0, -130.0] (target 3x)
- tipping, seated duck, its CG at the sim's worst lateral error (x -63, y 21): 14.73x about [218.0, -130.0] (target 3x)
- tipping, seated duck's whole weight at the seat's outer back corner (an extreme: its CG cannot sit there): 119.3x about [-109.0, 16.0] (target 3x)
- dock_erc.py: dock ERC: 0 ERROR, 0 WARN | INFO NTC window (10 k B3950, 10 k from 2.495 V): on from 43.2 C (0.793 V) down to 3.7 C (1.833 V); open reads 2.50 V, short 0 V: both off | INFO pack window through the duck's 100 k (charger off): on from 5.05 V to 9.23 V; charger on (direct): off above 8.59 V; a coin or nothing reads 0 V | INFO wake one-shot 1.1 x R17 x C4 = 110 ms
- route result against the live inputs (fingerprint of parts, fasteners, netlist, terminals, design sources; diameters from the netlist gauges): current
- wire to wire (centre lines at least the sum of the radii apart, outside shared terminal zones): no overlap
- route check per state: rest (push 0.0 mm, yaw 0.0 deg) PASS, docked (push 12.43 mm, yaw -3.18 deg) PASS, full_travel (push 40.0 mm, yaw 0.0 deg) PASS, full_travel_yaw_plus (push 40.0 mm, yaw 10.0 deg) PASS, full_travel_yaw_minus (push 40.0 mm, yaw -10.0 deg) PASS, rest_yaw_plus (push 0.0 mm, yaw 10.0 deg) PASS, rest_yaw_minus (push 0.0 mm, yaw -10.0 deg) PASS
- wires 18, routed 18, self-check PASS; cuts short of the rule: none
- sheet 7: sheet 7: 7_dock.png 566915 bytes, svg 356487 bytes, full 18 of 18, crossings 23
- dock_bom.py: CHECK PASS
- viewer dock scene not built in this output folder (make_viewer_data.py --scene dock --out VERIFY_OUT/viewer_dock): not compared

## Inputs read (sha256, first 10 hex, and file time)

| File | sha256 | Modified |
|---|---|---|
| BEST_WALK_ONNX_2.onnx | 3c606f9381 | 2026-11-06 22:47 UTC |
| altaay_lab/BOM.md | 219e25c3fe | 2026-11-07 02:09 UTC |
| altaay_lab/BOM_FULL.md | b5a50bc34a | 2026-11-07 01:51 UTC |
| altaay_lab/CABLE_MAP.md | 7fea207424 | 2026-11-06 22:47 UTC |
| altaay_lab/DECISIONS.md | 9cb8646e92 | 2026-11-07 01:24 UTC |
| altaay_lab/GAPS.md | 452dc537d6 | 2026-11-06 22:47 UTC |
| altaay_lab/HARDWARE_AUDIT.md | 2990727628 | 2026-11-06 22:47 UTC |
| altaay_lab/HARNESS_BUILD.md | 4dca489a43 | 2026-11-06 22:47 UTC |
| altaay_lab/MOUNTING.md | 438eb4972c | 2026-11-07 01:41 UTC |
| altaay_lab/POWER.md | 1dcf50658c | 2026-11-06 22:47 UTC |
| altaay_lab/PRINT_CHECK.md | e58193e049 | 2026-11-07 02:09 UTC |
| altaay_lab/README.md | c6d6ba51fc | 2026-11-06 22:47 UTC |
| altaay_lab/REFERENCES.md | 5f2b55fea3 | 2026-11-06 22:47 UTC |
| altaay_lab/SERVO_DEEP_DIVE.md | a691edab2c | 2026-11-06 22:47 UTC |
| altaay_lab/SERVO_UPGRADE_OPTIONS.md | ad7a2b18bc | 2026-11-06 22:47 UTC |
| altaay_lab/SOURCING_2026-11-02.md | 49aca9c97a | 2026-11-06 22:47 UTC |
| altaay_lab/START_HERE.md | 800ccc6b36 | 2026-11-07 02:09 UTC |
| altaay_lab/STATE.md | b27c8ed5c5 | 2026-11-07 02:02 UTC |
| altaay_lab/TEST_PLAN.md | 9509403f1f | 2026-11-07 02:03 UTC |
| altaay_lab/UPSTREAM_ISSUES.md | 684a28bb66 | 2026-11-06 22:47 UTC |
| altaay_lab/V1_PLAN.md | de78d52e82 | 2026-11-06 22:47 UTC |
| altaay_lab/WIRING.md | bbcbc910db | 2026-11-06 22:47 UTC |
| altaay_lab/audit/ERC_REPORT.md | cebb6e855f | 2026-11-06 22:47 UTC |
| altaay_lab/audit/assembly.json | 04cf4dc484 | 2026-11-07 01:29 UTC |
| altaay_lab/audit/bom_md_to_json.py | 5eacb7950e | 2026-11-06 22:47 UTC |
| altaay_lab/audit/bom_totals.py | 6421478207 | 2026-11-06 22:47 UTC |
| altaay_lab/audit/continuity_checklist.csv | 17be8bf47d | 2026-11-06 22:47 UTC |
| altaay_lab/audit/erc.py | 4a1406f408 | 2026-11-06 22:47 UTC |
| altaay_lab/audit/placements.json | 3c3a4774dc | 2026-11-06 22:47 UTC |
| altaay_lab/audit/sites.json | 9d275f3609 | 2026-11-07 01:29 UTC |
| altaay_lab/bench/odm_bench/joints.py | 266c4a84c3 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/conftest.py | b536072a74 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/fake_sts3215.py | 1b9afd70eb | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_battery_guard.py | 227a7d8506 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_crosscheck.py | 085ffbaf9a | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_feet_check.py | 2263e58494 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_first_servo_check.py | b157bb2cd3 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_imu_check.py | f7b6a309b9 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_power_log.py | b2bc48289d | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_protocol.py | 3e5298a2b2 | 2026-11-06 22:47 UTC |
| altaay_lab/bench/tests/test_set_angle_limits.py | 3dea97aaac | 2026-11-07 00:03 UTC |
| altaay_lab/bench/tests/test_thermal_guard.py | fb682126c4 | 2026-11-06 22:47 UTC |
| altaay_lab/bom.json | 290220b2e6 | 2026-11-07 02:09 UTC |
| altaay_lab/cables3d/CABLES_3D.md | f9c65a5f5a | 2026-11-06 22:47 UTC |
| altaay_lab/cables3d/VIEWER_NOTE.md | 60d8b20adb | 2026-11-06 22:47 UTC |
| altaay_lab/cables3d/cables3d.json | 4299251b8c | 2026-11-07 01:48 UTC |
| altaay_lab/fasteners/FASTENERS.md | 37551dea29 | 2026-11-07 01:34 UTC |
| altaay_lab/fasteners/VIEWER_NOTE.md | af30b4f52d | 2026-11-06 22:47 UTC |
| altaay_lab/fasteners/fasteners.json | bc7e1f8599 | 2026-11-07 01:34 UTC |
| altaay_lab/print/MASS_STUDY.md | 124f3a7700 | 2026-11-07 02:09 UTC |
| altaay_lab/print/PRINT_PLAN.md | 053137566d | 2026-11-07 02:09 UTC |
| altaay_lab/print/SLICE_SUMMARY.md | a079c3872d | 2026-11-07 02:09 UTC |
| altaay_lab/print/check_hip_roll_screw.py | c299d6623a | 2026-11-06 22:48 UTC |
| altaay_lab/print/parts.csv | b81eb93bcd | 2026-11-07 01:18 UTC |
| altaay_lab/sim/ADDED_MASS_SIM.md | a53b14d97c | 2026-11-06 22:48 UTC |
| altaay_lab/sim/CURRENT_BUDGET.md | ebe9bdcd0f | 2026-11-06 22:48 UTC |
| altaay_lab/sim/MASS_BUDGET.md | 92555b4182 | 2026-11-07 02:09 UTC |
| altaay_lab/sim/POWER_FIX.md | 4c97d67170 | 2026-11-06 22:48 UTC |
| altaay_lab/sim/POWER_PATH_SIM.md | a3de464d0f | 2026-11-06 22:48 UTC |
| altaay_lab/sim/RUNTIME_THERMAL.md | e247e0e023 | 2026-11-06 22:48 UTC |
| altaay_lab/sim/SIM_WALK.md | b83d1a4a3c | 2026-11-06 22:48 UTC |
| altaay_lab/sim/added_mass_sim.py | a5667b4b87 | 2026-11-06 22:48 UTC |
| altaay_lab/sim/current_budget.py | cebc433639 | 2026-11-06 22:48 UTC |
| altaay_lab/sim/mass_budget.py | ad28b7adb1 | 2026-11-07 01:24 UTC |
| altaay_lab/sim/power_fix.py | f0efa7c757 | 2026-11-06 22:48 UTC |
| altaay_lab/sim/power_path_sim.py | 5b3e2cf515 | 2026-11-06 22:48 UTC |
| altaay_lab/software/CALIBRATION.md | eaa400a741 | 2026-11-07 01:23 UTC |
| altaay_lab/software/PI_SETUP.md | 1bf944b894 | 2026-11-06 22:48 UTC |
| altaay_lab/software/SOFTWARE.md | d92bbb5f81 | 2026-11-06 22:48 UTC |
| altaay_lab/software/duck_config.altaay.json | 249171e913 | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_assembly.py | 4f33cc8392 | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_bom.py | 9909189935 | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_fasteners.py | 54658e2e6e | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_netlist.yaml | e3be0f4ae5 | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_parts.py | 701d24fad7 | 2026-11-06 22:48 UTC |
| altaay_lab/twin/dock/dock_routes.py | 12dee20372 | 2026-11-06 22:48 UTC |
| altaay_lab/viewer/MISSING_3D.md | 6b3241dde5 | 2026-11-06 22:48 UTC |
| altaay_lab/viewer/README.md | f44d43d1e9 | 2026-11-06 22:48 UTC |
| altaay_lab/viewer/make_viewer_data.py | 81a75d4615 | 2026-11-07 00:55 UTC |
| altaay_lab/wiring/netlist.yaml | 293658e198 | 2026-11-06 22:48 UTC |
| altaay_lab/wiring/sheets/make_sheets.py | 0675dcd0a3 | 2026-11-06 22:48 UTC |
| altaay_lab/wiring/sheets/sheetlib.py | 603ae4ea42 | 2026-11-06 22:48 UTC |
| mini_bdx/robots/open_duck_mini_v2/robot.urdf | bd3186bc85 | 2026-11-07 01:28 UTC |
