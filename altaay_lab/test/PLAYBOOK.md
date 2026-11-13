# Test playbook

Written 2026-11-13. This is the master list of how the duck is tested, from a unit check to a week in a home. It builds on TEST_PLAN.md, VERIFICATION.md, TWIN_CHECKLIST.md, and DEFINITION_OF_DONE.md. It does not replace them and it does not close a gate.

A sim pass only, a calc only, or a CAD check only result is evidence. DEFINITION_OF_DONE.md says those labels do not pass a gate. Nothing in this folder was measured on a servo, a cell, a board, or a printed part.

Read the results in `altaay_lab/test/results/`. The traceability matrix is `TRACEABILITY.md`. The FMEA is `FMEA.md`. Characterization is `CHARACTERIZATION.md`. Wear coupons are `WEAR_COUPONS.md`.

## How to run what does not need hardware

From the repo root:

```
python3 altaay_lab/test/bec12_heat.py
python3 altaay_lab/test/fault_inject.py
python3 altaay_lab/test/check_bench.py --self-test
python3 altaay_lab/circuitry/check_bq24133.py
python3 altaay_lab/circuitry/check_charger.py
python3 altaay_lab/circuitry/check_awake_load.py
```

The existing full matrix is `bash altaay_lab/verify/run_all.sh`. That run needs MuJoCo, ngspice, and the CAD inputs. This session did not re-run it. The last recorded result is VERIFICATION.md (2026-11-10: 21 PASS, 2 FAIL). The two FAILs are the as-built power path against the section 9 voltage gates (E6, E6b), sim pass only.

GitHub Actions workflow: `.github/workflows/test-playbook.yml`. It runs the commands above. It does not run `verify/part_limits.yaml` or `verify/check_power_limits.py`. Those files, and the workflow that calls them, belong to the power-limits change. This playbook only points at them.

## Labels

| Label | Means |
|---|---|
| sim pass only | A model ran. Not a measurement. |
| calc only | Arithmetic on cited or assumed inputs. |
| CAD check only | A geometry check. Not a printed part. |
| FEA pass only | A structural model on sim loads. |
| cited | A number from a document that was opened, named in the source file. |
| BLOCKER | The number or the part does not exist yet. |
| NEEDS HARDWARE | The procedure is written. The parts or the duck are not here. |

## Status of the pyramid

Counts: 2 DONE, 6 SIM ONLY, 6 NEEDS HARDWARE, 3 MISSING. Seventeen levels. DONE means the check exists and has a recorded result, not that a Definition of Done gate passed.

| # | Level | Status | Owner gate | Where |
|---|---|---|---|---|
| 1 | Unit and design-rule checks | DONE | Gate 1, gate 8 in part | verify/run_all.sh, VERIFICATION.md |
| 2 | Datasheet part-limit checks | MISSING | Gate 1 | verify/part_limits.yaml (other change, not this one) |
| 3 | Software-in-the-loop and sim-in-the-loop | SIM ONLY | Gate 0 | twin/, sim/, bench tests on a fake bus |
| 4 | Processor and hardware-in-the-loop | NEEDS HARDWARE | Gate 2 | bench/, TEST_PLAN 6 to 12 |
| 5 | Sim-to-real golden characterization | NEEDS HARDWARE | Gate 0 | test/CHARACTERIZATION.md |
| 6 | Regression and golden tests | SIM ONLY | Gate 2 | verify/, test/check_bench.py |
| 7 | Fault injection and FMEA | SIM ONLY | Gate 5 | test/FMEA.md, test/fault_inject.py |
| 8 | DFM, DFA, and tolerance stack | SIM ONLY | Gate 8 | cad/dfa/, twin/holes/ |
| 9 | Thermal, stress, fatigue | SIM ONLY | Gate 0 thermal, gate 4 | twin/thermal/, twin/structure/, test/bec12_heat.py |
| 10 | Wear and life | NEEDS HARDWARE | Gate 4 | test/WEAR_COUPONS.md, TEST_PLAN 19.7 and 20.4 |
| 11 | Battery and charging safety | NEEDS HARDWARE | Gate 5 | TEST_PLAN 3 and 20, COMPLIANCE_FIRST_PASS.md |
| 12 | EMC and FCC pre-compliance | NEEDS HARDWARE | Gate 6 | COMPLIANCE_FIRST_PASS.md |
| 13 | Product safety, IEC 62368-1 | MISSING | Gate 6 | Named below. The text was not applied. |
| 14 | Multi-day home use | NEEDS HARDWARE | Gate 7 | No field log |
| 15 | Build and user documents | MISSING | Gate 8 | twin/assembly/BUILD_ORDER.md exists in part. No user guide. |
| 16 | CI merge gates | SIM ONLY | Gate 1 | .github/workflows/test-playbook.yml |
| 17 | Requirement traceability | DONE | All gates | test/TRACEABILITY.md |

## 1. Unit and design-rule checks

Purpose. Catch a broken netlist, a BOM total that does not add up, a cable that does not reach, a GPIO or a servo ID that disagrees with itself.

What it catches. Schematic and document drift. It does not catch a real crimp, a real hop resistance, or a real servo.

Script. `bash altaay_lab/verify/run_all.sh`. One script per check lives in `altaay_lab/verify/`. E1 includes a mutation test: 10 of 10 injected netlist faults were caught on the recorded run.

Pass. The check's own gate in VERIFICATION.md. A WARN is a risk to measure, not a fail of the script. The recorded E6 and E6b FAILs mean the as-built 2S sim misses the TEST_PLAN section 9 voltage gates. That is a design finding, sim pass only, not a broken checker.

Owner gate. Gate 1 in part (the files agree with themselves). Gate 2 is the hardware those checks do not replace.

Status. DONE for the harness. Recorded 2026-11-10: 21 PASS, 2 FAIL, 0 NOT RUN. Not re-run this session.

## 2. Datasheet part-limit checks

Purpose. Catch a design number that is outside the part's own sheet: voltage, current, temperature, torque.

What it catches. A 14.7 V rail on a servo whose page stops at 14 V. A charge outside 0 C to 60 C. A stall the walk asks for that the sheet does not have.

Script. Not in this change. The power-limits change adds `altaay_lab/verify/part_limits.yaml` and `altaay_lab/verify/check_power_limits.py`, plus the workflow that runs them. Do not add a second copy. Until that change is on `altaay-lab`, this level has no machine check in the tree this playbook was written from.

Pass. Every limit in the yaml is inside the cited sheet, or the row is an explicit exception with a decision number. A missing sheet is BLOCKER, not a pass.

Owner gate. Gate 1.

Status. MISSING as an automated gate in this change. Prose checks exist in PARTS_AUDIT.md, circuitry/, and the thermal window in bec12_heat.json. Those prose checks are not this gate.

## 3. Software-in-the-loop and sim-in-the-loop

Purpose. Run the same decisions the duck will make, against a model of the plant, before a processor or a servo exists. The shape follows the usual split: model-in-the-loop, then software-in-the-loop, then processor-in-the-loop, then hardware-in-the-loop. MathWorks describes that split for SIL, PIL, and HIL (https://www.mathworks.com/help/ecoder/ug/software-and-processor-in-the-loop-sil-and-pil-simulations.html and https://www.mathworks.com/discovery/hardware-in-the-loop-hil.html). This repo is not a generated-code PIL setup. The analogue is: policy and guards in Python against MuJoCo and the power net.

What it catches. A gait that falls, a guard that never trips, a dock pose that misses. It does not catch a servo that does not match the sheet.

Scripts. `altaay_lab/sim/`, `altaay_lab/twin/electromech/`, `altaay_lab/twin/sit/`, `altaay_lab/problems/sts12.py`, `altaay_lab/bench/tests/` on a fake bus (verify/e8). Run C is problems/retrain_sts12/SUMMARY.md (sim pass only): 60 s, no fall, up to 0.252 m/s typical at a 0.40 m/s command. Not a run. A 0.10 m/s command stands still.

Pass. The test named in the twin row. A sim pass is not gate 0.

Owner gate. Gate 0 software and electrical, as evidence only.

Status. SIM ONLY.

## 4. Processor and hardware-in-the-loop

Purpose. The binary that will run on the Pi, on the real bus, with supplies standing in for the pack, then with the pack.

What it catches. Register 85, firmware, USB enumeration, brownout of the Pi, a guard that does not turn torque off. The simulated bus does not catch those.

Procedure. TEST_PLAN sections 6 to 12. Scripts in `altaay_lab/bench/`. First power from a current-limited bench supply, never the pack. Log in a new history file.

Pass. The pass line in that section. Sim predictions in the section are not the pass.

Owner gate. Gate 2.

Status. NEEDS HARDWARE. E8 recorded 32 pytest passes on a fake bus, with skips when the Runtime packages are absent. That is not this level.

## 5. Sim-to-real golden characterization

Purpose. Lock the twin to measured traces so later sims are about the duck that will be built. The open locks, in order, are the 12 V servo, the BEC setpoint and dropout, the pack, seat friction, and sole friction on felt. Well resistance is the contact lock.

What it catches. A twin that is confident and wrong. The STS12 walk used a 16 V setpoint. A 12.0 V setpoint on that same walk does not regulate (input minimum 11.335 V typical, sim pass only; 12.3 V is required, calc only). Quoting a regulated 12.0 V bus for that walk is the mistake this level exists to stop.

Procedure and file format. `altaay_lab/test/CHARACTERIZATION.md` and `altaay_lab/test/records/characterization_template.csv`.

Pass. Each CHAR row status is PASS, and the named twin is re-run on the measured number. The playbook bands (10 percent on the stall line, 0.10 V on the no-load BEC, factor of 2 on seat torque) are written in that file. They are not datasheet tolerances unless the sheet column says cited.

Owner gate. Gate 0.

Status. NEEDS HARDWARE. The format and the bands are written. Every measured cell is empty.

## 6. Regression and golden tests

Purpose. A later edit does not silently move a gate. Sim golden tests are the verify scripts. Bench golden tests are a filled record compared with a prediction.

What it catches. A netlist edit that breaks E1. A bench log that does not match the twin by more than the stated band. A 2S hop scored with the 3S rule, or the reverse.

Script. `python3 altaay_lab/test/check_bench.py --self-test`. A real log: `python3 altaay_lab/test/check_bench.py RECORD.yaml --predict altaay_lab/test/records/predictions/bec12_case.yaml` or `--gates`.

Pass. Self-test PASS means the checker works. A measured record PASSes the compare only when every filled value is inside `tol_abs` and every filled id is in the prediction. A measured record that matches nothing is a fail. `--gates` exits nonzero when a measured hop or walk row is FAIL. The compare band is an investigate band. It is not gate 2. Hop gates: 2S pass at most 28 mOhm, warn through 40, fail over 40; 3S pass at most 100 mOhm (TEST_PLAN section 5). Walk log: 2S uses 4.5 V and 10 percent under 6.0 V. 3S hard-fails under 4.0 V (the C018 page floor) and otherwise compares to the twin. Do not score a 12 V log with the 6.0 V gate.

Templates, all status not_run: `altaay_lab/test/records/templates/`. Schema: `altaay_lab/test/records/schema.yaml`.

Owner gate. Gate 2, once a record is measured. Until then the checker is a tool, not a pass.

Status. SIM ONLY for the checker and the verify suite. Bench golden records are NEEDS HARDWARE. The level is SIM ONLY because the only executed check is the self-test.

This session: self-test PASS.

## 7. Fault injection and FMEA

Purpose. Name how the duck fails, score it, and run the cases the thermal and electrical models can run.

What it catches. A bead fault the charger IC cannot see. A 1 ohm chafe the 15 A fuse does not clear. A rail that blocks charge termination. It does not catch a fault the model does not contain (a nick temperature, a cell over-voltage).

Script. `python3 altaay_lab/test/fault_inject.py`. Scores and the ranked list: `altaay_lab/test/FMEA.md`. Results: `altaay_lab/test/results/fault_inject.json`.

Pass. The script exits 0 and the specification checks inside it hold (open NTC inhibits, a camera miss does not enable charge, 21 mA of idle blocks 0.10 A termination, zero friction is not a seated charge). A passing script is not a safe duck.

Owner gate. Gate 5, as the list of tests. The gate passes only when the hardware rows in TEST_PLAN 20 pass.

Status. SIM ONLY.

This session, top 5 by RPN: NTC open or short 256, fall 252, cable chafe 224, limp sit slip 210, missing 3S pack protector 189. Full table in FMEA.md.

## 8. DFM, DFA, and tolerance stack

Purpose. A second person can assemble the duck, and a stack of print and part tolerances still lands the well on the foil.

What it catches. A screw the driver cannot reach. A pattern that is not uniform. A 8.5 mm stripe margin eaten by print error. It does not catch a press fit that was never printed.

Where. `altaay_lab/cad/dfa/DFA.md` and `altaay_lab/cad/dfa/CUTS.md` (CAD check only: fitted screws 310, builder-turned 254). `altaay_lab/twin/holes/HOLES_TWIN.md`. `altaay_lab/twin/assembly/BUILD_ORDER.md`.

Pass. D39 (no empty hole) and D42 (one pattern) on the duck that will be built, including nest v2, and a written stack for the well-to-stripe gap. The 8.5 mm figure is calc only, (20 mm stripe minus 3 mm well) / 2. A print tolerance is not assumed here. Measure it on a coupon. Do not close the stack with a guessed plus or minus 0.2 mm.

Owner gate. Gate 8 mechanical, and gate 0 screws.

Status. SIM ONLY. The files are CAD check only. Nothing is installed. Nest v2 is not in the fastener schedule.

## 9. Thermal, stress, fatigue

Purpose. See whether a continuous walk, a charge, or a fall load leaves the sheet windows, and whether a part's fatigue life is known.

What it catches. A knee that leaves 60 C. A BEC case with no published limit. A shin eye under the margin. It does not catch the real winding temperature. The winding node in the thermal model is a guess.

Scripts. Existing: `altaay_lab/twin/thermal/twin_thermal.py`, `gate_p45b.py`, `gate_bq24133.py`. This playbook: `python3 altaay_lab/test/bec12_heat.py`. Structure: `altaay_lab/twin/structure/STRUCTURE_TWIN.md` (FEA pass only). Life note: `altaay_lab/twin/life/LIFE.md`.

Pass. Sensor reading inside the servo operating range, minus 20 C to 60 C (cited sheet). Torque off above 70 C is the sheet's own cut, not a license to run at 69 C. Cells inside the sheet window for the mode (charge 0 C to 60 C, discharge minus 40 C to 60 C). Trunk wall under the 49 C PLA edge the thermal twin already uses. A BEC case number is reported, not passed: Castle publishes no case limit (BLOCKER).

Owner gate. Gate 0 thermal. Gate 2 thermal is the bench hold (TEST_PLAN 7.3), which this model does not replace.

Status. SIM ONLY.

### Results this session

Confirmation of the existing session (`session_bam_backlash_typical.csv`, pack near 8.2 V, not the 12 V gait). Central corner. Sim pass only. Friction heat omitted, so the knee is slightly cool.

| Room | Right knee reading reaches 60 C | Reaches 70 C | Reading max | Body max | Cells max | Wall max |
|---|---|---|---|---|---|---|
| 25 C | 3.33 min | 4.5 min | 102.36 C | 94.67 C | 49.66 C | 32.32 C |
| 32 C | 2.5 min | 3.5 min | 109.52 C | 101.63 C | 56.38 C | 39.17 C |

The 3.33 min and the 94.67 C body match the published thermal note (3.3 min, body near 94.7 C). Cells stay under 60 C in these 40 minutes. The knee reading does not. The body is what the PLA touches, and it is above the 49 C edge.

12.0 V setpoint on a current shape scaled from that session onto the C018 stall line (Kt 0.7649 Nm/A over 1.0896 Nm/A, calc only) and onto the STS12 mean pack current. Not run C. Not a closed-loop 12 V trace. Three cells via the same 3/2 mass scale `gate_bq24133.py` already uses. Sim pass only.

The walk does not hold 12.0 V. Typical BEC input minimum 11.335 V (sim pass only). Loss is I times 0.30 V. The 0.30 V is the lab assumption (BLOCKER). Mean BEC current 4.804 A after a 3 W, 0.955 efficient 5 V branch (calc only). Dropout loss 1.441 W.

| Case | Room | BEC loss | BEC case at 40 min | Knee reading to 60 C | Knee reading max | Knee body max | Cells max | Wall max |
|---|---|---|---|---|---|---|---|---|
| Dropout, central | 25 C | 1.441 W | 60.7 C | 4.83 min | 81.76 C | 76.74 C | 43.18 C | 29.0 C |
| Dropout, central | 32 C | 1.441 W | 67.24 C | 3.5 min | 88.84 C | 83.68 C | 49.97 C | 35.93 C |

Continuous walking still leaves the 60 C operating line, at 4.83 min in a 25 C room on this scaled shape, and at 3.33 min on the unscaled session. The body at 76.74 C is still above the 49 C PLA edge. Cells and the average wall stay inside their windows in the central rows. The winding node peaked at 127.72 C in the 25 C central dropout case. That node is a guess. Do not read it as measured copper.

The high corner stacks every pessimistic parameter (cf 1.25 and the hot thermal set). Its knee reading is about 200 C. THERMAL_TWIN.md already says a 200 C reading in that corner is the stack, not a temperature to quote. It is stored in the json and it is not the result above.

Resistive pack heating uses the session RMS current, scaled to the STS12 RMS. Converter loss still uses the mean current. If the same current were buck-regulated at 12.0 V and efficiency 0.85, the loss would be 10.173 W and the case 171.9 C (sim pass only, central, 25 C). This walk does not enter that regime. The older 2S session, if scored as a regulated buck at 0.85, has a mean loss of 4.76 W (calc only from that file's mean 6.649 V and 4.056 A). That is the family of the old hot BEC case. It is not the 12 V dropout number.

## 10. Wear and life

Purpose. A contact, a felt, a cloth, and a knee loop that survive a count written before the test.

What it catches. A well that cuts the foil, a felt that goes slick, a wire that breaks at 150 deg. It does not catch a one-cycle sit.

Procedure. `altaay_lab/test/WEAR_COUPONS.md`. Counts written now: wells 10,000, felt 10,000, cloth 10,000 if a cloth sample is still in question, knee loop 1,000,000 (already TEST_PLAN 19.7). Five hundred cycles remain the first look (TEST_PLAN 20.4), not the life.

Pass. The stop lines in WEAR_COUPONS.md, then the named sim re-run. The catalog 500,000 cycles are in a socket, not on foil.

Owner gate. Gate 4.

Status. NEEDS HARDWARE. The counts are written. No cycle has been run.

## 11. Battery and charging safety

Purpose. The pack and the charger do not become the hazard. Shipping a lithium battery in the US follows 49 CFR 173.185, which points at a pack shown to meet UN 38.3 (the lab already retrieved that rule: https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-173/subpart-E/section-173.185). UN 38.3 itself is section 38.3 of the UN Manual of Tests and Criteria (https://unece.org/transport/dangerous-goods).

What it catches. A charge below 0 C or above the bench limit, a gate that stays on for a coin or a wet cloth, a pack with no test summary. It does not catch those things in simulation.

Standards named, text not opened this session, so this playbook does not claim compliance:

| Document | What it is about | Catalog |
|---|---|---|
| UL 2054 | Household and commercial batteries | https://www.ul.com/services/battery-safety-testing |
| IEC 62133-2 | Secondary lithium cells and batteries, portable | https://webstore.iec.ch/en/publication/32662 |
| UN 38.3 | Transport tests | https://unece.org/transport/dangerous-goods |

Procedure. TEST_PLAN section 3 for the pack and the BMS, section 20.5 for the two-wire gate, section 20.8 for charge temperatures (cells 0 C to 45 C on the bench, charger case under 70 C, nearest PLA under 45 C). The cell sheet allows charge to 60 C. The bench limit is tighter on purpose.

Pass. The lines in those sections, plus a UN 38.3 summary for the pack that would be shipped. The pack is not built.

Owner gate. Gate 5.

Status. NEEDS HARDWARE. `check_bq24133.py` (49 checks, 0 failed this session), `check_charger.py` (41 checks, 0 failed), and `check_awake_load.py` (7 checks, 0 failed) are calc only on the drawings. They are not this gate.

## 12. EMC and FCC pre-compliance

Purpose. The Pi's radio in this body, and the duck as an unintentional radiator, before any sale or shipment.

What it catches. A host that hides the module label, a cable that changes the radio, a camera that was approved alone and is now in a robot. It does not certify the duck.

Rule already opened by the lab: 47 CFR 15.212 (https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-B/section-15.212). The grant was not read. The Pi brief's own mark is for the board.

Pass. The host check and the unintentional-radiator check named in COMPLIANCE_FIRST_PASS.md, and a label on the outside if the module id is hidden. A pre-compliance scan is not that pass. It is the cheap look before a lab.

Owner gate. Gate 6 electrical and mechanical.

Status. NEEDS HARDWARE. No scan has been run. No chamber is assumed.

## 13. Product safety, IEC 62368-1

Purpose. Hazard-based safety for audio, video, and information equipment, which is the usual place a reviewer starts for a powered product with a radio and a battery pack in a home. Catalog: IEC 62368-1 (https://webstore.iec.ch/en/publication/27412). The text was not opened. Which edition applies, and whether a toy rule or a different household rule is the one a reviewer would pick, is uncertain. COMPLIANCE_FIRST_PASS.md already says no charging-mat standard was opened.

What it would catch, if the text is applied later: accessible voltage on the cloth, a hot surface, a battery compartment, instructions. This playbook does not invent those test setups.

Pass. A named edition, a clause list, and results. None of that exists.

Owner gate. Gate 6 thermal and electrical.

Status. MISSING.

## 14. Multi-day home use

Purpose. The finished duck lives in a home, gets up, docks itself, and does not surprise the people there.

What it catches. A screw that loosens, a print that cracks on the real floor, a dock that works once and not on Thursday, a camera that stays on. A 60 s sim does not catch those.

Procedure. Gate 7 in DEFINITION_OF_DONE.md. Several days, the home's actual floor, falls, get-up through the sit (D60), logs of cells, servos, and PLA, and a return to the nest without a person placing the duck. Camera: a cue when it is on, no face library, no upload by default.

Pass. The four clauses of gate 7. No numeric substitute is written here, because the first unit's log is what the second unit will be compared to.

Owner gate. Gate 7.

Status. NEEDS HARDWARE. Not started.

## 15. Build and user documents

Purpose. Someone who did not design the duck can build a second one and live with it.

What it catches. A step that exists only in a designer's head. A charge instruction that contradicts the gate. A missing cue for the camera.

Where. `altaay_lab/twin/assembly/BUILD_ORDER.md`, `altaay_lab/fasteners/`, `altaay_lab/HARNESS_BUILD.md`, `altaay_lab/wiring/sheets/`. User guide: no file.

Pass. Gate 8. A second unit, built from the documents, passes gates 2 to 7. The heat log matches the first unit inside a band written before that build. The band cannot be written until the first log exists.

Owner gate. Gate 8.

Status. MISSING for the user guide and for a second unit. The build order is a partial CAD check only, and the nest is not in it.

## 16. CI merge gates

Purpose. A pull request cannot merge while a CPU check that this repo can run is red.

What it catches. A thermal script that no longer matches the published sit. A bench checker that scores 6.0 V rules on a 12 V log. A charger drawing whose arithmetic moved.

Workflow. `.github/workflows/test-playbook.yml` on pull requests and on pushes to `altaay-lab`. It installs numpy and pyyaml and runs bec12_heat.py, fault_inject.py, check_bench.py --self-test, check_bq24133.py, check_charger.py, and check_awake_load.py.

It does not run verify/run_all.sh (that job needs MuJoCo, ngspice, and CAD, and it is a separate decision). It does not run the part-limits checker. When that other workflow exists, both are merge gates. Neither one is a hardware gate.

Pass. The job is green, and bec12_heat.py still satisfies its own sanity checks (confirmation knee near 3.3 min, dropout loss between 0.8 W and 2.2 W, dropout case under 80 C in the central 25 C row, regulating hypothetical hotter than dropout).

Owner gate. Gate 1, as a file check. Not gate 2.

Status. SIM ONLY. The workflow file is in the tree. A green run on a fork's default runner is still sim and calc only.

## 17. Requirement traceability

Purpose. Every Definition of Done clause points at a test, and every test points at a clause. This is the right-hand side of a V: requirements on one side, verification on the other. The shape is the one in the NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (https://www.nasa.gov/reference/systems-engineering-handbook/) and in ISO/IEC/IEEE 15288:2015 (https://www.iso.org/standard/63711.html). Those documents are the pattern. They are not a claim that this project follows them.

The same idea shows up in other fields. ISO 26262 uses a V for road vehicles (https://www.iso.org/standard/68383.html). DO-178C uses objectives and verification for airborne software (https://www.rtca.org/do-178/). The duck is not a car and not an aircraft. The links are there so the pyramid has a public source, not so those standards can be quoted as met. FMEA method: IEC 60812 (https://webstore.iec.ch/en/publication/26359) and SAE J1739, with the RPN note in FMEA.md.

What it catches. A gate with no test, or a test with no gate.

Script. The matrix is `altaay_lab/test/TRACEABILITY.md`. It is maintained by hand when a gate or a test is added. There is no generator.

Pass. Every clause in DEFINITION_OF_DONE.md has a row, and the status column matches that file. A filled matrix does not pass the gates.

Owner gate. All of them, as a map.

Status. DONE for the matrix. Every gate in it is still GAP.

## What still needs hardware

1. Every CHAR row in CHARACTERIZATION.md: 12 V servo stall and speed, BEC dropout and efficiency, pack resistance, seat friction, sole mu on felt, well ohms.
2. TEST_PLAN sections 1 to 20 on the real parts. The bench templates are blank on purpose.
3. Wear counts in WEAR_COUPONS.md.
4. A 3S protector part, then its trip test. The 2S Tenergy band is not that test.
5. Charge-gate bench (TEST_PLAN 20.5) and charger-in-the-duck temperatures (20.8).
6. Camera on the real mat (20.9). The sit geometry sees none of the cloth.
7. UN 38.3 summary before any pack is shipped. UL 2054 and IEC 62133-2 text, if a reviewer requires them.
8. FCC host check. IEC 62368-1 clause list, after someone opens the text and decides it applies.
9. Days of home use, a user guide, and a second unit.
10. The part-limits CI files, from the other change, once they land.

## This session, short

| Check | Result |
|---|---|
| bec12_heat.py | Exit 0. Confirmation knee 60 C at 3.33 min. 12 V dropout case 60.7 C. Scaled knee still leaves 60 C at 4.83 min. |
| fault_inject.py | Exit 0. Top RPN 256, 252, 224, 210, 189. Cut-rail sit reproduced cells 28.36 C. |
| check_bench.py --self-test | PASS |
| check_bq24133.py | 49 checks, 0 failed |
| check_charger.py | 41 checks, 0 failed |
| check_awake_load.py | 7 checks, 0 failed |
| verify/run_all.sh | Not re-run. Last record stands. |
