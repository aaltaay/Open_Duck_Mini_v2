# GAPS

Written 2026-11-24 ET. This is the ranked roadmap from the tree as it stands after the merged autonomy supervisor, the day-one install, the voice pipeline, the build guide, the owner's manual, and the Pi Zero 2 W memory check.

The previous page is kept, unchanged, in [history/2026-11-24_1310_gaps_before_roadmap.md](history/2026-11-24_1310_gaps_before_roadmap.md). It stops in the 2026-11-01 notes. Do not treat it as the current duck.

This page does not edit D61. It does not change the bill. It does not redesign the head for a new computer. That redesign is already in progress elsewhere. Ahmed's choice for the computer is a Raspberry Pi 5 with 2 GB.

## How to read a row

**Missing** is the hole. **Why** is the product reason. **Closer** is who can take the next step:

- **Software or sim now.** The next useful step is a file or a simulation on machines already in use. Finishing that step does not pass a gate.
- **Needs hardware.** The pass is a measurement on a part, a coupon, or a duck. The plan for that measurement is already [TEST_PLAN.md](TEST_PLAN.md).
- **Needs a decision.** Ahmed, or a lawyer he chooses, has to pick. The tree can prepare the page. It cannot pick.
- **Needs money.** A part, a lab test, or a quote that is not approved. Buy nothing from this page.
- **In progress.** The Pi 5 head and power redesign. This roadmap does not do that work.

**Size** is the next step, not a calendar:

- **Small.** One module, or one rerun of a sim that already exists.
- **Medium.** Several files in one subsystem.
- **Large.** The print set, the netlist, and the twin together, or a new trained behavior.

A number is **sim pass only**, **calc only**, **CAD check only**, **cited**, **measured in emulation**, or **BLOCKER**. A sim is not a duck. Gates 0 to 8 in [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) are open. Nothing in this repo has been printed, welded, bought as a full order, or run on a robot.

[HARDWARE_AUDIT.md](HARDWARE_AUDIT.md) section 6 remains the older blocker table. This page does not renumber it. The rows below are the holes between this tree and a duck someone can sell.

The picture is [docs/images/gaps_by_area.png](docs/images/gaps_by_area.png). The counts in that picture are the 42 rows on this page.

## Verdict

Duckie is not a finished product and it is not sellable. The mission is a home robot that walks, finds a nest with the camera only, charges, lives there for days, does something a person keeps, and sells at a fair price, with one digital twin of the duck that would ship.

What the tree actually has is a strong pile of studies. `make twin` loads run D and, in simulation, walks a flat room until the pack cutoff ([twin/out/REPORT.md](twin/out/REPORT.md), sim pass only). A separate camera-dock batch charges on gold domes in 38 of 40 sits (sim pass only, [twin/dock/camera/CAMERA_DOCK.md](twin/dock/camera/CAMERA_DOCK.md)). An autonomy loop can replay that batch for three simulated days ([software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md)). Voice, a personality, a build guide, and an owner's manual exist and have not run on a duck. The Pi Zero 2 W does not have the memory for the stack (measured in emulation, [software/pi_fit/FIT.md](software/pi_fit/FIT.md)).

The same tree still contains more than one duck. The install boots the stock walk policy. The approved nest text and the dome geometry disagree. The charger has no seat. The print that would be made misses the structure margin. No bill is one cart. No lawyer has cleared a sale.

## What is already in the tree

These are not open rows. They are here so a later edit does not "fix" work that landed.

- Run D is the walk `make twin` loads (D66). 41.48 walking minutes, 0 rests, knee peak 38.4 C, pack peak 13.81 A (sim pass only, [twin/out/REPORT.md](twin/out/REPORT.md)). Run C is kept and is not the current walk.
- Nest v2 is the mat D62 approved. Nest v3 charged 15 of 40 and is not the mat (D67, sim pass only). Nest v5 charged 25 of 40 with 4 falls and is a study, not an approval (sim pass only, [cad/nest_v5/NEST_V5.md](cad/nest_v5/NEST_V5.md)).
- The autonomy supervisor, the day-one install, the voice pipeline, the personality layer, the build guide, and the owner's manual are in the tree. Each file says it has not run on a robot.
- Stairs stay exempt. See B7 below. Docking and get-up are not exempt.
- The straight-wire ranking is a study. D64 kept a regulator. D65 names the buck-boost that is supposed to hold 12.0 V. That part is not measured on a pack.

## Where the 42 rows sit on the gates

| Gate | What is still open | Rows |
|---|---|---|
| 0. One twin, one bill | The files do not describe one duck | TW1, TW3, TW6, EL1, EL3, ME1, MF1 |
| 1. Datasheets | Servo heat, stall, charger seat, printed stops | TW4, TW6, ME3 |
| 2. Bench | The plan exists. No part has been measured | SW9, EL4, ME7 |
| 3. Camera dock and charge | The 38 of 40 batch is not a mark-free camera, and it is not hardware | SW2, SW3, ME1 |
| 4. Wear | No life number for cloth, wires, or screws | ME7, TW5 |
| 5. Charger, pack, mat | The gate is undesigned and the pack has no transport summary | EL2, CS3, CS4 |
| 6. Certification basics | Counsel, content, the radio label | CS1, CS2, CS5 |
| 7. Days at home | Get-up, cliff, a real floor, a real camera | SW5, SW10, PB2 |
| 8. A second builder | The guide exists. Nobody has built the first duck | MF4, SW1 |

## Count

This table is the chart. Software or sim now: 19. Needs hardware: 10. Needs a decision: 10. Needs money: 2. In progress: 1.

| Area | Software or sim now | Needs hardware | Needs a decision | Needs money | In progress |
|---|---:|---:|---:|---:|---:|
| Software | 8 | 1 | 1 | 0 | 0 |
| Twin and sim | 3 | 3 | 1 | 0 | 0 |
| Electrical | 4 | 1 | 0 | 1 | 0 |
| Mechanical and CAD | 1 | 2 | 3 | 0 | 1 |
| Manufacturing and cost | 2 | 1 | 1 | 0 | 0 |
| Compliance and safety | 1 | 1 | 3 | 1 | 0 |
| Product and business | 0 | 1 | 1 | 0 | 0 |

## Rank across the groups

The order below is the order that protects a buyer. A cheap sim that leaves a false dock rate in place is behind a true one.

1. One duck in the files: the policy, the nest geometry, the charger, the computer, and one cart (SW1, TW1, ME1, ME4, EL1, MF1).
2. A dock that matches the camera-only decision (SW3, SW2).
3. A walk that has been asked to cross a home floor, and a servo that has been measured (TW2, TW6, TW4).
4. Structure that holds, and heat that is a log rather than a model (TW3, TW4).
5. A charger and a mat that are safe when a child, a coin, or a spill is present (EL2, CS4, CS3).
6. Get-up, cliff, and a day that is not a replay (SW5, SW10, PB2).
7. A sale a lawyer can stand behind, and a price that includes the duck a person would actually receive (CS1, CS2, CS6, PB1, MF2).

## Software

### SW1. The install boots the stock walk

**Missing.** [software/install_pi.sh](software/install_pi.sh) copies `BEST_WALK_ONNX_2.onnx`. [software/SOFTWARE.md](software/SOFTWARE.md) still says the lab has not trained a policy. D66 says run D is the walk, and `make twin` loads `sts12_runD_policy.onnx`.

**Why.** A duck flashed from the install script is not the duck the twin scores. One digital twin includes the file that boots.

**Closer.** Software or sim now.

**Size.** Small. Point the install, the setup check, and the day-one walk at run D. Leave the Runtime untouched (D6).

**Builds on.** D66, [problems/retrain_sts12/RUN_D.md](problems/retrain_sts12/RUN_D.md), [software/DAY_ONE.md](software/DAY_ONE.md), [software/PI_SETUP.md](software/PI_SETUP.md).

### SW2. The three-day soak replays a batch

**Missing.** The supervisor does not run the camera. A dock episode is one row from the gold-dome batch: 38 of 40 charging (sim pass only, [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md)). The soak, seed 1, reports 23.211 hours awake, 24 dock attempts, 20 successes, 0 falls (sim pass only). Falls were not drawn, because the cited walks did not report one.

**Why.** "Runs for days" and "docks with the camera" are the mission. A replay of 40 seeds is not either one. Gate 7 stays open.

**Closer.** Software or sim now, for calling the detector. The pass is hardware (SW9).

**Size.** Medium.

**Builds on.** [software/autonomy/supervisor.py](software/autonomy/supervisor.py), [twin/dock/camera/camera_dock.py](twin/dock/camera/camera_dock.py), [twin/dock/camera/SEAT_CONTACTS.md](twin/dock/camera/SEAT_CONTACTS.md).

### SW3. The charging number uses marks

**Missing.** The 38 of 40 result uses an 80 mm wall card and a room mark ([twin/dock/camera/CAMERA_DOCK.md](twin/dock/camera/CAMERA_DOCK.md), sim pass only). D61 prefers no tags. D62 keeps finding on the camera only. The owner's manual says leave the card off. A mark-free run of this detector is not in the file. Seed 32 never sees a mark.

**Why.** The number a reader will quote is not the product Ahmed asked for. Shipping the card would be a different product, and it needs his yes.

**Closer.** Software or sim now. Rerun the same 40 seeds with both marks removed. If that rate collapses, the next decision is his.

**Size.** Medium.

**Builds on.** [twin/dock/camera/CAMERA_DOCK.md](twin/dock/camera/CAMERA_DOCK.md), [twin/dock/closeup/CLOSEUP.md](twin/dock/closeup/CLOSEUP.md), [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md), D61, D62.

### SW4. Privacy is a sentence, not a behavior

**Missing.** Gate 7 asks for a cue when the camera is on, no stored face library, and no upload by default. The manual states the intent. The autonomy loop does not enforce it. A person finder and a follow behavior are BLOCKER ([software/companion/USEFULNESS.md](software/companion/USEFULNESS.md)).

**Why.** A home camera that can walk is a trust product. The useful jobs that exist today are a timer, a reminder, the clock, weather, and a short hello.

**Closer.** Software or sim now, for the cue and the refusal. Follow is a later model and then hardware.

**Size.** Small for the cue and the refusal. Large for follow.

**Builds on.** [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md), [software/companion/USEFULNESS.md](software/companion/USEFULNESS.md), [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md).

### SW5. Get-up still misses a class of falls

**Missing.** Get-up through the sit raises 248 of 296 cases and misses all 48 front rests on a down ramp (sim pass only, [twin/sit/getup/VIA_SIT_EVAL.md](twin/sit/getup/VIA_SIT_EVAL.md)). The supervisor uses the flat-floor program, 112 of 112 (sim pass only). Fold-to-sit and sit-to-stand are not trained (D66). The one-twin session does not fold when hot, because folding tips the model (sim pass only, [twin/out/REPORT.md](twin/out/REPORT.md)).

**Why.** A home robot that stays on its back is not finished. Gate 7 names this get-up.

**Closer.** Software or sim now, for a search inside the printed stops. A new training run is money, and it waits on Ahmed.

**Size.** Medium for the search. Large if the search fails.

**Builds on.** D60, [twin/sit/getup/GETUP_VIA_SIT.md](twin/sit/getup/GETUP_VIA_SIT.md), [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md).

### SW6. Two limit tables

**Missing.** [software/servo_limits.json](software/servo_limits.json) holds the sit stops. Older sim ranges still ask for knee and ankle angles the printed parts cannot reach ([TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). The walk model was compiled at 90 deg and the twin raises the stop before the sit. The CAD bumper is 150 deg and the register soft stop used in the report is 147 deg (CAD check only and the report's own label).

**Why.** A policy that commands an angle the plastic cannot reach will grind a servo or skip the motion. Gate 1 is this row.

**Closer.** Software or sim now.

**Size.** Medium. One table generated from the CAD contacts, loaded by the current sims.

**Builds on.** [software/servo_limits.json](software/servo_limits.json), [twin/sit/SIT.md](twin/sit/SIT.md), [software/CALIBRATION.md](software/CALIBRATION.md).

### SW7. The ears still wait on a yes

**Missing.** The ear overlay is written. [software/ANTENNAS_PWM.md](software/ANTENNAS_PWM.md) asks whether it may stay, with `antennas.py` left as the upstream file (D6). There is no answer on this page.

**Why.** The companion's ears are part of looking alive. The two SG90s are also the lab-rule gap B10a.

**Closer.** Needs a decision.

**Size.** Small once he answers. No purchase.

**Builds on.** [software/ANTENNAS_PWM.md](software/ANTENNAS_PWM.md), [software/hw_pwm.py](software/hw_pwm.py), D53, D6.

### SW8. Charge control and updates are not a product

**Missing.** The supervisor can hold a sit while a cell model fills. There is no program for the BQ24133, no update path, and no log a reviewer can pull off a real duck. [TWIN_CHECKLIST.md](TWIN_CHECKLIST.md) still marks nest vision, charge control, and updates as missing from the shipping software. Voice latency on the Pi is BLOCKER ([software/companion/LATENCY.md](software/companion/LATENCY.md) was measured on a desktop).

**Why.** A dock that does not know it is charging, and a robot that cannot be updated, does not run for days in a home.

**Closer.** Software or sim now, for a charge-state machine that follows the chip note. The pass is hardware. Voice timing waits on the Pi 5 image (ME4).

**Size.** Medium.

**Builds on.** [twin/thermal/BQ24133_HEAT.md](twin/thermal/BQ24133_HEAT.md), [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md), [software/SOFTWARE.md](software/SOFTWARE.md).

### SW9. Day one has never seen a part

**Missing.** [software/DAY_ONE.md](software/DAY_ONE.md) runs on mock hardware in CI. Camera frame rate, eye current, SG90 speed, mic latency, and contact ohms are BLOCKER. [TEST_PLAN.md](TEST_PLAN.md) is the full bench list. None of it has been run on a part.

**Why.** Gate 2 is this list. Every speed, temperature, and current in the twin hangs on it.

**Closer.** Needs hardware. The coupon and the test order also need his yes, which is money.

**Size.** Large. It is the whole bench, after parts exist.

**Builds on.** [software/DAY_ONE.md](software/DAY_ONE.md), [bench/day_one.py](bench/day_one.py), [TEST_PLAN.md](TEST_PLAN.md).

### SW10. Cliff, touch, and pickup are seats only

**Missing.** The sensors are in the CAD (D51, D54, D55) and in wiring sheet 6. There is no behavior twin of touch, cliff, or hearing ([TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). The supervisor does not hold the walk when the floor ends. The VL53L4CD sheet was not opened (BLOCKER, [PARTS_AUDIT.md](PARTS_AUDIT.md)). Stairs are exempt. Walking off a drop is not.

**Why.** A home has table edges, stairs, and people who pick the duck up. The legs pinch. The manual already says it is not a toy to carry.

**Closer.** Software or sim now, using the range the freeze note already states. A datasheet pass and a bench check are hardware.

**Size.** Medium.

**Builds on.** [twin/freeze/FREEZE.md](twin/freeze/FREEZE.md), [software/autonomy/supervisor.py](software/autonomy/supervisor.py), [redteam/REDTEAM.md](redteam/REDTEAM.md).

## Twin and sim

### TW1. One command is not one duck

**Missing.** `make twin` loads run D for the walk. The dock lines in [twin/out/REPORT.md](twin/out/REPORT.md) are the separate 40-seed batch. The checklist row is still FAIL, and it says camera dock is BLOCKER ([TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). Nest v2 is not in `print/`, the URDF, the viewer, or the bill. [twin/dock/nest/HANDOVER.md](twin/dock/nest/HANDOVER.md) is the 2026-11-11 pause note. D62, D65, D66, and D67 came after it.

**Why.** The mission asks for one digital twin. A stitched report can hide which policy sat on which mat.

**Closer.** Software or sim now, for one session that walks and docks. Installing geometry waits on ME1.

**Size.** Large.

**Builds on.** [twin/out/REPORT.md](twin/out/REPORT.md), [TWIN_CHECKLIST.md](TWIN_CHECKLIST.md), [cad/nest_v2/NEST_V2.md](cad/nest_v2/NEST_V2.md).

### TW2. Run D has not been asked to cross a home floor

**Missing.** The run D sweep is flat constant commands (sim pass only, [problems/retrain_sts12/RUN_D.md](problems/retrain_sts12/RUN_D.md)). The terrain note in [STATE.md](STATE.md) is the stock policy in the shared lab gym: it fails a 5 deg up ramp, 0 of 40, and this build trips a 3 mm edge, 0 of 5 (sim pass only). Those numbers are not a run D result. The nest edge that caused falls in the November dock sims has not been rescored with run D inside `make twin`.

**Why.** A flat-room walk is not a home. Rugs, thresholds, and the mat edge are the floor the duck has to live on.

**Closer.** Software or sim now.

**Size.** Medium. Score the policy that ships, on the edges and ramps already defined.

**Builds on.** [problems/retrain_sts12/RUN_D.md](problems/retrain_sts12/RUN_D.md), the terrain paragraph in [STATE.md](STATE.md), [twin/dock/nest/sim/v3/NEST_SIM_V3.md](twin/dock/nest/sim/v3/NEST_SIM_V3.md).

### TW3. The print that would be made misses the margin

**Missing.** The shin eye in the print set is under the lab margin. A recessed web in PA6-CF clears in FEA and is not in `print/` (FEA pass only, [twin/structure/shin_eye/SHIN_EYE.md](twin/structure/shin_eye/SHIN_EYE.md)). Hot tensile and wet tensile are BLOCKER. The lab printer's nozzle and chamber are BLOCKER. The red team ranks that eye as the first printed part past its index if the sim loads are reached. Nest mass is not in the structure model. D26 is open.

**Why.** A duck that cracks on a normal walk does not reach a customer, and a second unit will crack the same way.

**Closer.** Needs hardware for the dry coupon at about 60 C, after Ahmed says yes. Copying the web into `print/` before that coupon is the wrong next step.

**Size.** Medium for the coupon. Large for a material change.

**Builds on.** [twin/structure/STRUCTURE_TWIN.md](twin/structure/STRUCTURE_TWIN.md), [twin/structure/shin_eye/SHIN_EYE.md](twin/structure/shin_eye/SHIN_EYE.md), D26.

### TW4. The heat clock is a model

**Missing.** The run D session peaks the knee at 38.4 C with 0 rests (sim pass only, [twin/out/REPORT.md](twin/out/REPORT.md)), on an assumed winding resistance. The earlier heat study still leaves 60 C inside about 8 minutes of continuous walking (sim pass only and calc only, [twin/thermal/KNEE_HEAT_STUDY.md](twin/thermal/KNEE_HEAT_STUDY.md)). The red team says the one-minute knee is not a hardware time: the cited Robo9 oscillation on this servo family took on the order of 40 to 50 minutes ([redteam/VERDICT_2026-11-13.md](redteam/VERDICT_2026-11-13.md)). The charger die in the trunk is BLOCKER. Cell specific heat in the model is a guess.

**Why.** If the knee is hot in a minute, the duck spends its life sitting. If the model is pessimistic, the rests are theater. Gate 1 and gate 7 both need the log.

**Closer.** Needs hardware. [TEST_PLAN.md](TEST_PLAN.md) 7.3 is the measurement. Another sim will not settle it.

**Size.** Small on the bench, once one servo and a supply exist. Large as a product claim until then.

**Builds on.** [twin/thermal/THERMAL_TWIN.md](twin/thermal/THERMAL_TWIN.md), [twin/thermal/KNEE_HEAT_STUDY.md](twin/thermal/KNEE_HEAT_STUDY.md), [redteam/VERDICT_2026-11-13.md](redteam/VERDICT_2026-11-13.md).

### TW5. Felt, friction, and contact force are assumptions

**Missing.** No felt grade. Sole friction on felt is BLOCKER. The camera-dock charge model uses 5 milliohms at 10 grams and a dust factor of 5, and both are assumptions ([twin/dock/camera/CAMERA_DOCK.md](twin/dock/camera/CAMERA_DOCK.md)). Well resistance was not measured. The nest sim mat in the older runs is rigid.

**Why.** The dock either charges or it burns a contact. Gate 3 and gate 4 are this measurement.

**Closer.** Needs a decision to buy the coupon in [TEST_PLAN.md](TEST_PLAN.md) 20.1 to 20.4 (a few contacts, a scrap of cloth, a scrap of felt). That is the only buy the definition allows before gate 0.

**Size.** Small once he says yes.

**Builds on.** [twin/contact/CONTACT_TWIN.md](twin/contact/CONTACT_TWIN.md), [PARTS_AUDIT.md](PARTS_AUDIT.md), D62.

### TW6. Every walk uses a servo the bench has not seen

**Missing.** Stall torque, speed, backlash, winding resistance, and rotor inertia of the units we would buy are not measured. The sheet and the trained actuator have disagreed before, and that disagreement was large enough to drop the old walk in a few seconds (sim pass only, [problems/STALL.md](problems/STALL.md)). Run D walks in sim on the sheet law at a held 12.0 V. Bench stall is BLOCKER ([TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). Firmware behavior as the bus sags is unpublished.

**Why.** If the real servo is weaker or hotter than the sheet law, the 41.48 minute walk is a fiction. This is the first measurement in the red team's list.

**Closer.** Needs hardware. [TEST_PLAN.md](TEST_PLAN.md) 7.5 and 15.

**Size.** Small for one servo. It gates every other walk claim.

**Builds on.** [problems/retrain_sts12/RUN_D.md](problems/retrain_sts12/RUN_D.md), [SERVO_DEEP_DIVE.md](SERVO_DEEP_DIVE.md), [redteam/VERDICT_2026-11-13.md](redteam/VERDICT_2026-11-13.md).

### TW7. Old ducks are still easy to quote

**Missing.** The tree still holds the 2S sheet-stall fall, the 7.2 V rail, the 16 V set point, the spring-pin nest, and the stock-policy walk that `make twin` used to load. The files mark them superseded. A summary can still ship the old number, which is how the 30.07 minute walk stayed in a report after run D existed.

**Why.** One digital twin means one current result. The others are history.

**Closer.** Software or sim now. A banner on each live report, and no new prose that quotes a superseded clock as the duck.

**Size.** Medium. It is discipline across the live pages, not a new physics run.

**Builds on.** [TWIN_CHECKLIST.md](TWIN_CHECKLIST.md), [problems/PROBLEMS.md](problems/PROBLEMS.md), D63, D65, D66.

## Electrical

### EL1. The charger has no seat

**Missing.** The BQ24133 is the 3S charger in the notes. It is not seated in the body. In-trunk thermal resistance is BLOCKER. Whether a limp sit stays down with the servo rail off is BLOCKER ([TWIN_CHECKLIST.md](TWIN_CHECKLIST.md), [twin/sit/RAIL_OFF_SIT.md](twin/sit/RAIL_OFF_SIT.md)). The MCP73213 file is the 2S record only.

**Why.** The mission puts the charger inside the duck. Heat, service, and the sit all move when that board has a place.

**Closer.** Software or sim now, for a seated study in the CAD and the netlist. The temperature pass is hardware. Do not edit the bill in that study.

**Size.** Large.

**Builds on.** [twin/thermal/BQ24133_HEAT.md](twin/thermal/BQ24133_HEAT.md), [circuitry/BQ24133_BOARD.md](circuitry/BQ24133_BOARD.md), [circuitry/CHARGER_BOARD.md](circuitry/CHARGER_BOARD.md), D61, D65.

### EL2. The mat can be left live

**Missing.** The two-wire gate that refuses water, metal, and a skin stand-in, and that drops power when the duck stands, is not a circuit. The owner's manual says not to leave the mat powered until that gate is real. The sense board is not in the netlist ([cad/nest_v5/NEST_V5.md](cad/nest_v5/NEST_V5.md) still lists it as BLOCKER on the v5 study).

**Why.** A felt mat on a floor, with a supply behind it, is the hazard a child meets. Gate 5 is this circuit.

**Closer.** Software or sim now, for the schematic and the behavior. The pass is CS4.

**Size.** Large.

**Builds on.** [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md), [TEST_PLAN.md](TEST_PLAN.md) 20.5, [circuitry/SERVO_RAIL.md](circuitry/SERVO_RAIL.md).

### EL3. The pack cannot be ordered or shipped

**Missing.** The files say three Molicel P45B cells. The weld has no part number (BLOCKER, [TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). The cells were out of stock the last time the pages were opened. There is no UN 38.3 test summary, because there is no pack. The bay fit is CAD check only.

**Why.** Gate 0 forbids the full order before the twin matches the bill. Gate 5 forbids shipping a lithium pack that has not been shown to meet the transport rule ([COMPLIANCE_FIRST_PASS.md](COMPLIANCE_FIRST_PASS.md), 49 CFR 173.185, cited there).

**Closer.** Needs money, after he says yes, and only once the weld has a part number and the cells are actually for sale. A sourcing check of live pages is allowed before any purchase.

**Size.** Medium to name the weld. Large to have a pack that can travel.

**Builds on.** [twin/battery/BAY.md](twin/battery/BAY.md), [bom/order/ORDER.md](bom/order/ORDER.md), [PARTS_AUDIT.md](PARTS_AUDIT.md).

### EL4. The 12.0 V rail is a citation, not a sweep

**Missing.** D65 picks the TDK-Lambda buck-boost and cites an efficiency band. The sim holds 12.0 V. What that part does from a full pack at 12.6 V down to the 9.0 V floor, at walking current, is not measured. The earlier Castle dropout of 0.30 V was an assumption and is one reason the part changed ([redteam/VERDICT_2026-11-13.md](redteam/VERDICT_2026-11-13.md)).

**Why.** Most of a 3S discharge sits under 12.6 V. If the rail sags or shuts off, every walk and heat result moves.

**Closer.** Needs hardware. One supply sweep, the red team's second measurement, now on the part D65 names.

**Size.** Small on the bench.

**Builds on.** D63, D64, D65, [verify/check_power_limits.py](verify/check_power_limits.py), [POWER.md](POWER.md).

### EL5. The netlist still carries a retired dock

**Missing.** [bom/order/ORDER.md](bom/order/ORDER.md) says the netlist still contains the chest pad and the Adeept board, and that the order script excludes them by citation. The nest supply, the two-net sense path, and the seated charger are not the wiring a builder opens when they open the old dock sheet. [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) already says not to wire from `wiring/sheets/7_dock.svg`.

**Why.** Gate 0 says the netlist is the duck that will be built. A retired part in the file is how the wrong duck gets built.

**Closer.** Software or sim now. Mark the retired ids in the netlist study. Do not edit the bill. Do not edit D61.

**Size.** Medium.

**Builds on.** [wiring/netlist.yaml](wiring/netlist.yaml), [bom/order/ORDER.md](bom/order/ORDER.md), [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md).

### EL6. The limb breakers have no harness route

**Missing.** D65 already puts the three TPS259827 breakers in series with the servo feeds. SP1 and SP4 leave EFL.OUT, SP2 and SP5 leave EFR.OUT, and SP3 leaves EFN.OUT. Cable EF ties each breaker input to the servo splice (cited, [wiring/netlist.yaml](wiring/netlist.yaml)). What is still missing is the body of that cable: EF is marked `no_route`, with no cut length and no 3D polyline. The 2026-11-13 red team line that said the breakers were off the live feeds is the older reading. A trip check against a real limb current is still BLOCKER ([problems/KNEE_HEAT_CHAFE.md](problems/KNEE_HEAT_CHAFE.md), [test/FMEA.md](test/FMEA.md)).

**Why.** A breaker that exists only as a net name can be left out of the harness a person builds. The leg is protected when the wire is drawn and a walk shows whether the blanking window nuisance-trips.

**Closer.** Software or sim now, for the 3D route and the cut lengths. The trip check is hardware.

**Size.** Medium.

**Builds on.** [wiring/netlist.yaml](wiring/netlist.yaml) cable EF, [problems/KNEE_HEAT_CHAFE.md](problems/KNEE_HEAT_CHAFE.md), [test/FMEA.md](test/FMEA.md). [redteam/VERDICT_2026-11-13.md](redteam/VERDICT_2026-11-13.md) is the older series claim.

## Mechanical and CAD

### ME1. The approved nest and the charging geometry are not the same shape

**Missing.** D62 writes a flush striped field and five gold wells. The later dome study charges 38 of 40 with wells standing 0.9 mm proud, and 0 of 40 with the flush face (sim pass only, [twin/dock/camera/SEAT_CONTACTS.md](twin/dock/camera/SEAT_CONTACTS.md), [twin/dock/camera/SEAT_WELLS.md](twin/dock/camera/SEAT_WELLS.md)). The build guide tells a builder to leave the domes. The nest v2 mesh the guide points at still shows the flush wells. None of this is in `print/`. D62 was not edited, and it should not be edited in place.

**Why.** Installing the wrong contact makes a duck that sits and does not charge. Installing the domes without a new decision contradicts the recorded approval.

**Closer.** Needs a decision. Ask him to confirm the 0.9 mm domes, or to keep the flush field. After that, the CAD install is large and it is software.

**Size.** Small for the question. Large for the install into `print/`, the URDF, and the viewer.

**Builds on.** D62, [cad/nest_v2/NEST_V2.md](cad/nest_v2/NEST_V2.md), [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md), [twin/dock/camera/SEAT_CONTACTS.md](twin/dock/camera/SEAT_CONTACTS.md).

### ME2. Hundreds of screws, and no assembly

**Missing.** Fitted screws are 310 and builder-turned screws are 254 (CAD check only, [TWIN_CHECKLIST.md](TWIN_CHECKLIST.md)). The aim under 200 is not met. Horns, case clamps, and shells stay. Insert pull-out time and strength are BLOCKER. Nothing has been assembled, so reachability is a CAD check only.

**Why.** A fair price includes the hours. A second builder inherits this stack. Gate 8 feels this before it feels the policy.

**Closer.** Needs a decision on which joints may lose a screw. Paper cuts already ran and did not reach the aim ([cad/dfa/CUTS.md](cad/dfa/CUTS.md)).

**Size.** Medium for another cut, after he picks. The proof is a built leg.

**Builds on.** [cad/dfa/DFA.md](cad/dfa/DFA.md), [twin/assembly/BUILD_ORDER.md](twin/assembly/BUILD_ORDER.md), [fasteners/fasteners.json](fasteners/fasteners.json).

### ME3. The printed stops are not measured on a servo

**Missing.** The limit file and the CAD contacts exist. Gate 1 says they are not done until a real servo is driven into them and the angle read back matches ([DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md), [TEST_PLAN.md](TEST_PLAN.md) 19.1). The servo sheet names a full turn of the sensor and no mechanical stop. The plastic is the stop.

**Why.** SW6 can make the files agree. Only a servo proves the plastic is where the file says.

**Closer.** Needs hardware.

**Size.** Small, on the first leg, after a print exists.

**Builds on.** [software/servo_limits.json](software/servo_limits.json), [twin/sit/SIT.md](twin/sit/SIT.md), [TEST_PLAN.md](TEST_PLAN.md) 19.

### ME4. The Pi 5 does not fit the head that is drawn

**Missing.** The head is laid out for a Pi Zero 2 W, 65 mm by 30 mm (cited, [software/pi_fit/BOARDS.md](software/pi_fit/BOARDS.md)). A Pi 5 is 85 mm by 56 mm (cited, the same note). It does not drop into that seat. The stack does not fit the Zero's published Bookworm Lite memory map: at the cited 417 MiB Linux can see, the emulation spilled 108.4 MiB of swap; a 512 MiB cap peaked at 467.0 MiB with almost no swap (measured in emulation, [software/pi_fit/FIT.md](software/pi_fit/FIT.md)). Power, the camera cable, the GPIO map, and the mass move with the board. The bill and the install still name the Zero. D7 still names the Zero.

**Why.** Without a computer that can hold the walk and the voice, the companion features are a desktop demo. This is the compute half of "useful."

**Closer.** In progress. Ahmed has chosen the Pi 5 with 2 GB. Another redesign owns the head, the feed, and the install. This page does not start a second one. When that work lands, SW1 and the memory check have to be rerun on that image. The USB servo round trip is still BLOCKER.

**Size.** Large. It touches the head solids, the 5 V budget, and the software pin.

**Builds on.** [software/pi_fit/FIT.md](software/pi_fit/FIT.md), [software/pi_fit/BOARDS.md](software/pi_fit/BOARDS.md), [software/companion/LATENCY.md](software/companion/LATENCY.md).

### ME5. The structure decision is still open

**Missing.** D26 (the roll-to-pitch and the knee sheet eye) is not decided. The topology pass did not land in `print/`. The foot carve is not a mass saving. Nest mass is not in that model ([twin/structure/shin_eye/SHIN_EYE.md](twin/structure/shin_eye/SHIN_EYE.md)).

**Why.** TW3 cannot close while the material and the shape are undecided. Printing the right leg before D26 repeats a known weak section.

**Closer.** Needs a decision.

**Size.** Medium to rerun the structure twin after he picks. Do not copy the web STL in ahead of the coupon.

**Builds on.** D26, [twin/structure/STRUCTURE_TWIN.md](twin/structure/STRUCTURE_TWIN.md), [HARDWARE_AUDIT.md](HARDWARE_AUDIT.md) B42 and B43.

### ME6. Cables are short or rubbing in CAD

**Missing.** On the sit model, knee kit leads and ankle feeds come up 17 to 25 mm short of the slack rule (CAD check only, the sit notes in [STATE.md](STATE.md) and [twin/sit/SIT.md](twin/sit/SIT.md)). The camera ribbon needs a twist or another path, and the neck route rubs (CAD check only, [HARDWARE_AUDIT.md](HARDWARE_AUDIT.md) B61 and B62). Those are test-fit BLOCKERs, and the route can be redrawn before any plastic exists.

**Why.** A taut lead at a joint is the first thing that fails in a week of sitting and standing. Gate 4's knee-wire life starts here.

**Closer.** Software or sim now, for a route that passes the slack rule and the clearance check on the mesh. The built leg still has to be fitted.

**Size.** Medium.

**Builds on.** [twin/sit/SIT.md](twin/sit/SIT.md), [cables3d/](cables3d/), [HARDWARE_AUDIT.md](HARDWARE_AUDIT.md) B61 and B62.

### ME7. Nothing has a life number

**Missing.** Pins or wells on cloth, the cloth, the knee-loop wires, and the screws that carry repeated sit loads have no cycle count written down and then run. The 500,000-cycle figure in the old pin catalog is a socket, not cloth (cited in [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md)). [TEST_PLAN.md](TEST_PLAN.md) 20.4 is a 500-cycle first look and it has not been run. Servo gear life is a 6 month warranty on the motor and the gears, with no duty curve (the old B2 note, kept below).

**Why.** Gate 4 is wear. A product that charges every day wears the contact every day.

**Closer.** Needs hardware, after TW5's coupon and after ME1 picks the contact.

**Size.** Medium on the bench. It does not pass a multi-month life claim.

**Builds on.** [TEST_PLAN.md](TEST_PLAN.md) 19.7 and 20.4, [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 4, [SERVO_DEEP_DIVE.md](SERVO_DEEP_DIVE.md).

## Manufacturing and cost

### MF1. There is no one-click bill

**Missing.** [BOM.md](BOM.md) says its Totals table is the older rollup, and the paragraph under that table describes a different sum from the table. [bom/order/ORDER.md](bom/order/ORDER.md) says it is the live cart and that the BOM rollup is not that cart. Felt, foil, and the weld are BLOCKER. The nest parts are not a matched set on one page. Gate 0's rule is one order, exact part numbers, live stock, and nothing the design no longer uses.

**Why.** Two carts means the next person buys the wrong duck. This page does not edit either file. A later job has to make them one cart, after ME1 and ME4 settle.

**Closer.** Software or sim now, for a reconciliation that leaves unsourced lines as BLOCKER instead of a price. Placing the order is money, and it waits on gate 0.

**Size.** Medium.

**Builds on.** [BOM.md](BOM.md), [bom/order/ORDER.md](bom/order/ORDER.md), [PARTS_AUDIT.md](PARTS_AUDIT.md). Do not change the bill as a side effect of a doc pass.

### MF2. A parts cart is not a price

**Missing.** No labor, yield, returns, support, warranty, certification, shipping, or channel sits on top of the parts. The print time in [print/PRINT_PLAN.md](print/PRINT_PLAN.md) is a slicer estimate and has never been run. Fastening time in the older notes is a cited operation-time estimate on an older screw count, not a clocking of this duck. [costdown/RANKED.md](costdown/RANKED.md) says the knees, the cells, the computer, and the regulator are the wrong places to save money, and that a mold is not justified on the bound that exists.

**Why.** "Sells at a fair price" needs a price a buyer pays and a cost that survives a failed print. The parts floor is already a home-robot sum, before any of those adders, and before the Pi 5 move in ME4.

**Closer.** Software or sim now, for a one-page stack that uses only figures already in the bill files and labels every missing adder BLOCKER. A real mold quote, a cert quote, and a timed build are money.

**Size.** Small for the honest stack. Large for a price that can be printed on a box.

**Builds on.** [costdown/RANKED.md](costdown/RANKED.md), [costdown/VOLUME.md](costdown/VOLUME.md), [BOM.md](BOM.md), [bom/order/ORDER.md](bom/order/ORDER.md).

### MF3. Nobody has chosen the kind of product this is

**Missing.** One printed duck, a kit, a short run, and a molded product are different factories. [costdown/RANKED.md](costdown/RANKED.md) says not to order molds for 100 or 1000 on the current bound. Servo prices at 100 and at 1000, filament at those quantities, and a mold quote are BLOCKER. The only path that exists is a printed one-off, and it has not been printed.

**Why.** A fair price for a kit is a different promise from a fair price for a finished toy. The build guide is written for a second person with a printer. A store shelf is a different machine.

**Closer.** Needs a decision.

**Size.** Small to write the choice down. The factory work is money.

**Builds on.** [costdown/VOLUME.md](costdown/VOLUME.md), [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md), [print/PRINT_PLAN.md](print/PRINT_PLAN.md).

### MF4. A second person cannot build one yet

**Missing.** [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) and [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md) exist. Both say the duck has not been built. The guide still tells the builder the computer is a Pi Zero 2 W. The install it points at boots the stock policy (SW1). Gate 8 passes when someone who did not design the duck builds a second unit and that unit passes the same tests. Nobody has built the first.

**Why.** Documents that describe a duck the files no longer mean are how a second unit goes wrong. The pages are a start. They are not the gate.

**Closer.** Needs hardware for the gate. Correcting the computer line and the policy line is software, and it should follow ME4 and SW1 rather than invent a third story.

**Size.** Large. It is a build, then a second build.

**Builds on.** [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md), [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md), [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 8.

## Compliance and safety

This is not legal advice. The notes below say what the lab files already opened. A lawyer applies them.

### CS1. A sale may be barred before the duck walks

**Missing.** The 28 July 2026 Covered List notice adds foreign-produced advanced robotic devices. On the elements the lab could read, this duck matches the robot class except a stated radio speed, which is BLOCKER, and except a statute footnote, which is BLOCKER ([compliance/FCC_COVERED_ROBOT.md](compliance/FCC_COVERED_ROBOT.md)). The mass used there is 2.81 kg from the mass budget, which is 6.19 lb (calc only, 2.81 times 2.2046). The line in the notice is 4.4 lb (cited). A scale weight does not exist. If the finished duck is covered equipment, 47 CFR 2.903 bars a new authorization and 47 CFR 2.803 bars marketing a radio device without one (cited in that note). Whether the Pi's own grant covers this body is BLOCKER. A Department of War conditional-approval path is BLOCKER. This is not an FCC ruling.

**Why.** A product that cannot be authorized cannot be sold, however good the walk is. This sits above every sim.

**Closer.** Needs a decision. Counsel, not another simulation. A scale weight is hardware and still will not answer the legal question by itself.

**Size.** Small to hire the reading. The outcome can stop the product.

**Builds on.** [compliance/FCC_COVERED_ROBOT.md](compliance/FCC_COVERED_ROBOT.md), [compliance/COMPLIANCE.md](compliance/COMPLIANCE.md), [COMPLIANCE_FIRST_PASS.md](COMPLIANCE_FIRST_PASS.md).

### CS2. Domestic content is a few percent

**Missing.** The worksheet's domestic share is 5.23 percent (calc only, [compliance/DOMESTIC_CONTENT.md](compliance/DOMESTIC_CONTENT.md)). The test it applies for a 2026 delivery is above 65 percent (cited). Unknown origin counts as foreign. US assembly labor does not count as a component. The duck is not sold in quantity, so the COTS path is not met on this record. A reading that counts unknown servos as domestic is in that file and is not the rule the worksheet uses.

**Why.** "Assembled here" does not, on the pages that were opened, take a foreign parts list off the Covered List. CS1 and CS2 are one problem.

**Closer.** Needs a decision. US-made subassemblies, a different product, or counsel. New US actuators would be a different robot and real money.

**Size.** Large if the answer is new actuators. Small if the answer is "do not sell until counsel speaks."

**Builds on.** [compliance/DOMESTIC_CONTENT.md](compliance/DOMESTIC_CONTENT.md), [compliance/DOMESTIC_ROWS.csv](compliance/DOMESTIC_ROWS.csv).

### CS3. The pack has no transport summary

**Missing.** A lithium battery that is shipped has to be a type shown to meet UN 38.3. 49 CFR 173.185 is the US shipping rule the definition cites. The pack is not built. There is no summary. There is no lab report number.

**Why.** Even a kit that includes cells is a shipment. Gate 5 will not pass on a drawing.

**Closer.** Needs money. A test house, after the pack design is frozen (EL3). His yes comes first.

**Size.** Large. It is an external test, not a script.

**Builds on.** [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 5, [COMPLIANCE_FIRST_PASS.md](COMPLIANCE_FIRST_PASS.md), [twin/battery/BAY.md](twin/battery/BAY.md).

### CS4. Charge safety is unmeasured

**Missing.** During a full charge with the charger in the duck, the bench limits are cells at 0 C to 45 C, charger case under 70 C, and the nearest PLA under 45 C ([TEST_PLAN.md](TEST_PLAN.md) 20.8). Not run. Coin-bridge, pull-out, water, metal, and a skin stand-in are [TEST_PLAN.md](TEST_PLAN.md) 20.3 and 20.5. Not run. The duck standing on a live mat is described and is not code (EL2).

**Why.** This is the hazard in the living room. A sim of 1.9 W to 3.2 W, or of the later 2.30 W and 3.50 W sit, does not pass the gate. Those figures are calc only or sim pass only, and the die temperature in the trunk is BLOCKER.

**Closer.** Needs hardware, after EL1 and EL2 exist as a build.

**Size.** Medium on the bench. It is a gate, not a subplot.

**Builds on.** [TEST_PLAN.md](TEST_PLAN.md) section 20, [twin/thermal/CHARGE_WATTS.md](twin/thermal/CHARGE_WATTS.md), [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 5.

### CS5. The body has no radio label, and the camera cue is not code

**Missing.** 47 CFR 15.212, as the definition uses it, wants the radio identity on the outside when the module's own mark is hidden. The FCC id was not read from the grant (BLOCKER). The camera-on cue is SW4. Together they are the gate 6 software and mechanical lines.

**Why.** A reviewer, and a person in the room, have to be able to tell what the duck is and when it is looking.

**Closer.** Software or sim now for the cue (that is SW4). The label text needs CS1 before anyone engraves it.

**Size.** Small for a placeholder label location in CAD, after counsel names the id.

**Builds on.** [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 6, [compliance/COMPLIANCE.md](compliance/COMPLIANCE.md), SW4.

### CS6. The walk code has no license file

**Missing.** The Runtime and the Playground, at the pins this lab uses, have no LICENSE file ([software/companion/USEFULNESS.md](software/companion/USEFULNESS.md)). D6 says use them unmodified and do not republish them. Nobody has asked the author, because D6 also said not to send that message until Ahmed asks.

**Why.** A product that ships that walk, or a kit that tells a buyer to clone it, needs an answer the author has given. Silence is not a grant.

**Closer.** Needs a decision. He asks, or he does not ship that code. Do not write to the upstream project from this page.

**Size.** Small for the question. The answer can change what is legal to sell.

**Builds on.** D6, [software/companion/USEFULNESS.md](software/companion/USEFULNESS.md), the old B12 note below.

## Product and business

### PB1. There is no buyer and no price

**Missing.** No customer interview, no channel, and no price a person would pay. The jobs the software can do without a cloud key are a timer, a reminder, the clock, weather, and a short hello ([docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md)). Mail and calendar are adult mode, off unless a key is set outside the repo. Follow, play, and "look at you" are not built (SW4). The parts carts are a floor under a retail price, and they do not agree with each other (MF1, MF2).

**Why.** A fair price is a price for a job someone wants. The tree has not named that person.

**Closer.** Needs a decision. Who is it for: a kit builder, a desktop companion that happens to walk, or a store product. The devil's advocate section is the argument against assuming the answer.

**Size.** Small to choose. The evidence he might want (five conversations with likely buyers) costs nothing but time and is still his to do.

**Builds on.** [software/companion/USEFULNESS.md](software/companion/USEFULNESS.md), [docs/OWNERS_MANUAL.md](docs/OWNERS_MANUAL.md), [costdown/RANKED.md](costdown/RANKED.md).

### PB2. "Days" is a simulated replay

**Missing.** Gate 7 is several days of real walking, sitting, docking, and falling on the floor the home has, with the duck getting up, coming back to charge, and leaving again, with a log. The longest run in the tree is the autonomy soak: 23.211 hours awake across three simulated days, 0 falls, minimum pack 10.665 V (sim pass only, [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md)). The walk clock in the one twin is 41.48 minutes to the 10.0 V cutoff (sim pass only). A home fall rate is BLOCKER. Charge on a real board is BLOCKER. A live camera is BLOCKER.

**Why.** This is the sentence on the box. The evidence is a drawing of a trace, and the file says so.

**Closer.** Needs hardware. SW2 and SW5 can make the sim less flattering before that. They do not pass the gate.

**Size.** Large. It is the life test.

**Builds on.** [software/autonomy/AUTONOMY.md](software/autonomy/AUTONOMY.md), [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) gate 7, [twin/out/REPORT.md](twin/out/REPORT.md).

## Why Duckie might not sell

This is the argument against the product, written so a hopeful sim cannot talk over it. It uses the sources already in the tree. It is not a market study, and it is not legal advice.

1. **The job people keep is the easy part, and the duck spent its effort on the hard part.** The AIBO posts coded in the usefulness note talk about life-like motion and company. The Eilik pages in that note describe an offline desk toy that does not follow you and does not become an assistant. One owner's note on Loona, cited there, calls it fun to borrow. Reachy Mini's readme leads with talk and a hand follow. Duckie's working jobs are a timer and a hello. The walk, the nest, and the fall recovery are the expensive, fragile half, and they are the half that is still sim pass only.

2. **The dock story a buyer hears is not the dock the files scored.** Camera only, no tags, is the decision. The 38 of 40 charging result uses marks. Flush wells, which D62 wrote down, charged 0 of 40 in the later study (sim pass only). A buyer who wants a mat with two stickers is buying a different product from the one Ahmed described. A buyer who wants no stickers is buying a result that has not been produced.

3. **It may not be legal to sell, on a reading the lab has already written down.** The model is over the 4.4 lb line in the Covered List notice, the parts list does not clear the content worksheet, and the radio authorization for this body is BLOCKER (CS1, CS2). A charming walk does not answer that. Counsel might find a path. The tree does not contain one.

4. **The price will not look like a toy.** The published carts are parts only, they disagree, and the adders (print failures, 254 builder-turned screws, a lithium test, support, a computer that does not fit the head) are all still in front of us. [costdown/RANKED.md](costdown/RANKED.md) already refused the obvious cuts because they break the knee or the pack. A fair price for what the duck does today, which is not yet a walk on a rug, may be a price no one pays. A fair price for a finished walking companion may be a price that only a kit audience pays, and that audience is PB1, which is empty.

5. **Homes are hostile to this shape.** Stairs are exempt because the legs cannot climb a normal rise (B7). The stock policy, in the shared lab gym, already fails a small ramp and a 3 mm edge (sim pass only, [STATE.md](STATE.md)). Run D has not been shown those floors (TW2). Pets, cables, and socks are not in the sim. A duck that needs a clear flat room is a demo, not a roommate.

6. **It may spend its life on the charger.** If the heat model that leaves 60 C in minutes is anywhere near the hardware, the duck rests more than it walks (TW4). If the structure eye is as weak as the FEA on the print that would be made, it cracks (TW3). A companion that sits on a mat, warm, is a charging statue with a camera. People have cheaper statues.

7. **Trust is the product, and the product is not there yet.** A walking camera, a homemade lithium pack, and legs that pinch are three reasons to say no. The manual is honest about the pinch and the pack. Honesty is required. It also shrinks the buyer to an adult who will read a page. The camera-on cue is not code (SW4).

8. **One digital twin is the right rule, and breaking it is how a demo lies.** The install, the bill, the nest text, the dome sim, and the Pi seat are five ducks. Any video from today is a video of a duck that will not ship. Buyers of a kit will build the duck the guide names. Right now that guide names the Zero and a nest mesh that does not match the charging sim (MF4, ME1, ME4).

9. **The fallback product does not need this robot.** If the walk slips, what remains is a desktop companion that talks and keeps a timer. That product does not need 14 servos, a nest, or a Covered List question. Ahmed should decide whether the walk is the product. If it is, the rows above are the work. If it is not, most of this tree is a research project, and the thing to sell is smaller.

## IDs older pages still cite

The old page used these ids. They still mean what the citations say.

### B2. Servo life

No continuous-duty curve. Motor and gear warranty on the sheet the old page used is 6 months. Still open. The measurement is TW4 and TW6. [TEST_PLAN.md](TEST_PLAN.md) 7.3 has not been run.

### B6. Get-up

The 2026-11-03 scripted get-up, and the later note that those joint angles do not fit the printed parts, are history. The current result is 248 of 296 through the sit, with 48 front rests on down ramps missed (sim pass only). The open work is SW5.

### B7. Stairs remain exempt

Ahmed, 2026-11-01. The legs cannot climb the lab stair. The geometry correction in the archived page still supports the exemption: the rise is about the whole straight leg. Docking and get-up are not exempt. Walking off a drop is SW10.

### B10a. The ear servos are not bus servos

The two SG90 antennas are PWM hobby servos. They stay because the stock build kept them. A bus-servo swap was deferred. SW7 is the open question on how the ears are driven. The parts themselves are still this gap.

### B12. No upstream license

Still true. The open work is CS6. Do not write to the upstream author unless Ahmed asks.

## Top 10 next actions

Each of these can start with no purchase. None of them passes a gate by itself. None of them edits D61 or the bill. None of them starts a second Pi 5 redesign.

1. Point the Pi install, the setup check, and the day-one walk at the run D policy. Leave the Runtime unmodified.
2. Re-run the 40-seed camera dock with the wall card and the room mark removed. Publish that rate beside the 38 of 40.
3. Produce one `make twin` report that contains that dock, the run D walk, the pack, and the heat.
4. Score run D on a 2 mm edge, a 3 mm threshold, and a 5 degree ramp.
5. Search a get-up for the 48 down-ramp front rests, inside the printed stops, before any new training run.
6. Generate one joint-limit table from the CAD contacts and load it from the current sims.
7. Make the autonomy supervisor call the camera detector. Stop replaying the published seeds as if they were a new day.
8. Add a camera-on cue and a refusal of any stored face library to that loop, and log both.
9. Draw the mat safety gate and a seated BQ24133 in a netlist study. Mark the retired dock parts. Do not edit the bill. Do not edit D61.
10. Hold the walk when the cliff range already in the freeze note says the floor is gone, and when a pickup is detected. Wire it into the supervisor. Do not buy a sensor to do this.
