# FMEA: charger, pack, rail, and the faults that drop the duck

Written 2026-11-13. Scores are judgment on the design as it stands. They are not a measured failure rate. RPN is severity times occurrence times detection, each from 1 to 10. That product is the classic form in SAE J1739 (https://www.sae.org/standards/content/j1739_202101/). The 2019 AIAG-VDA FMEA handbook ranks work by action priority instead of RPN (https://www.aiag.org/store/publications/details?ProductCode=FMEAAV-1). This table keeps RPN because the playbook asked for it.

Severity is the effect if the fault happens. Occurrence is how available the fault is in this design, not a field rate. Detection is whether the duck, as designed, notices before the harm. A script in this folder is not detection.

The physics behind the rows is `altaay_lab/test/fault_inject.py`. Temperatures are sim pass only. Currents and divider fractions are calc only. Nothing here was run on a cell, a board, or a servo.

## Scale

| Score | Severity | Occurrence | Detection |
|---|---|---|---|
| 2 | Nuisance, duck stops safely | Needs two failed parts | A bench test is written and would catch it before use |
| 4 | Mission lost, no fire | A single part can fail this way | A log would show it after the fact |
| 6 | Duck falls, or charge never finishes | The design allows it in normal use some of the time | Noticed only after damage |
| 8 | Cell damage or a hot contact | It is the normal path today | The product has no check |
| 10 | Fire, vent, or a shock a person can touch | It happens on every use | No one would see it |

## Ranked table

| Rank | Id | S | O | D | RPN | Fault |
|---|---|---|---|---|---|---|
| 1 | ntc_open_short | 8 | 4 | 8 | 256 | Pack NTC open or short, and the charger IC does not see it |
| 2 | fall | 7 | 6 | 6 | 252 | Fall, get-up miss, structure under the lab margin |
| 3 | cable_chafe | 8 | 4 | 7 | 224 | Cable chafe to about 1 ohm, 15 A fuse rating not exceeded |
| 4 | limp_sit_slip | 6 | 7 | 5 | 210 | Limp sit slips or unloads the wells |
| 5 | pack_no_trip | 9 | 3 | 7 | 189 | A hard short, and no 3S protector part is on the bill |
| 6 | camera_dock_miss | 5 | 9 | 4 | 180 | Camera misses the cloth at the sit |
| 7 | charger_stuck_on | 8 | 3 | 6 | 144 | Charger stays at 1 A past the end of charge |
| 8 | rail_on_while_docked | 6 | 4 | 5 | 120 | Servo rail turns on while the duck is still on the mat |
| 9 | pack_nuisance_trip | 5 | 6 | 4 | 120 | Walk peak sits inside the 13 A to 21 A watch band |
| 10 | pi_brownout | 7 | 3 | 5 | 105 | 5 V rail sags when the BEC output falls under 6 V |
| 11 | bec_failure | 7 | 3 | 4 | 84 | BEC output collapses, or the pass element shorts |

Top 5 by RPN: NTC window, fall, cable chafe, limp sit, missing pack protector.

## 1. NTC open or short (RPN 256)

The pack bead is Adafruit 372, 10 kOhm at 25 C (cited, CHARGER_BOARD.md). The LM393 window is 10.0 kOhm over 28.0 kOhm on the cold side and 10.0 kOhm over 2.80 kOhm on the hot side. The NTC is the bottom resistor.

Calc only, from `fault_inject.py`:

| Bead | Fraction of the reference | LM393 inhibits charge |
|---|---|---|
| Open | 1.00 | yes |
| 0 C, 31.77 kOhm | 0.761 | yes |
| 25 C, 10 kOhm | 0.50 | no, charge allowed |
| 60 C, 2.472 kOhm | 0.198 | yes |
| Short | 0.00 | yes |

D65 wires the bead to the BQ24133 TS pin. The bias is 2.87 kOhm from VREF, and 12.7 kOhm to ground in parallel with the bead. Calc only: the fraction is 0.760 at 0 C, 0.661 at 25 C, and 0.419 at 60 C. An open bead is 0.816 and a short is 0. Both are outside the cited TS window, so the chip stops charge. The old fixed divider (10.0 kOhm over 15.0 kOhm, fraction 0.60) is superseded. The LM393 still watches the same node. Detection is the chip's own pin. The resistor order codes are BLOCKER.

What would lower it: a bench record of the bead open, the bead shorted, and charge current at zero both times (TEST_PLAN 20.5 style), plus a second inhibit that does not depend on one comparator.

## 2. Fall (RPN 252)

Get-up through the sit still misses 48 of 296 down-ramp front rests (sim pass only, twin/sit/getup/VIA_SIT_EVAL.md). Structure on the print that would be made is under the lab margin on several parts (FEA pass only). A home will produce falls. The duck does not yet get up on hardware, and several printed parts are the ones a fall loads.

The electrical twin's fall traces are not in this repo (BLOCKER). The injected current in the fault script is the older 2S shove: 20 A for 13 ms (the published band was 19.5 A to 20.6 A). Calc only: that pulse trips a 17 A / 8 ms threshold and does not trip a 21 A threshold. It is not a 3S fall measurement.

## 3. Cable chafe (RPN 224)

A nick that leaves about 1 ohm from the 12.6 V pack to ground does not exceed the 15 A fuse rating. Calc only, path 0.0998 ohm (3 x 15 mOhm cells, BMS 25 mOhm max, fuse 6 mOhm, XT30 2 mOhm, switch 13 mOhm, wires 8.8 mOhm):

| Nick | Current | Heat in the nick | Over 15 A |
|---|---|---|---|
| 1.0 ohm | 11.46 A | 131.3 W | no |
| 0.10 ohm | 63.06 A | 397.7 W | yes |
| 0.05 ohm | 84.11 A | 353.7 W | yes |
| 0.01 ohm | 114.75 A | 131.7 W | yes |

The 131 W figure is calc only. The thermal twin has no nick node, so the local temperature is BLOCKER. The fuse opening time is BLOCKER until a fuse curve is applied. The knee loop life test is TEST_PLAN 19.7 and has not been run.

## 4. Limp sit slip (RPN 210)

Unpowered friction is not on the Feetech sheet (BLOCKER). The filed sit (sim pass only, twin/sit/rail_off_sit.json) says:

| Case | Wells stay loaded | Lateral slide |
|---|---|---|
| Training friction 0.068 Nm, floor 0.8 | yes for 20 s | 0.05 mm, inside the 8.5 mm stripe |
| Joint friction and damping at 0, floor 0.8 | no, seat force 0 N | 0.27 mm |
| Joint friction and floor friction at 0 | no, run blows up at 2.27 s | 7.47 mm in y, 28.97 mm in x |

The 8.5 mm margin is calc only: (20 mm stripe minus 3 mm well) / 2. When the rail returns on the training-friction sit, seat force falls to 0 N before the stand ramp (sim pass only). The wells open at the moment the duck tries to leave. Sole friction on felt is BLOCKER. TEST_PLAN 19.5 is the measurement.

## 5. Pack protector missing (RPN 189)

D65 puts BatterySpace PCM-L04S30-566 on the bill: 30 A continuous discharge and a trip of 120 A to 160 A (cited). The Tenergy 32175 numbers do not move to a 3S pack. The new board sits in the rear pocket on body_back (CAD check only, D65). The old slot does not hold it. A short above 15 A is still supposed to open the fuse. The 16 A walk peak is under 120 A, so this board is not the nuisance-trip case in row 9.

## 6. Camera dock miss (RPN 180)

The recorded sit sees 0 of 13 disc samples and 0 of 27 ring samples (CAD check only, twin/camera/CAMERA_TWIN.md). The specification rule in `fault_inject.py` refuses charge when the sample count is 0. That rule holds in the test. The product has no nest-vision program and no charge program (MISSING). Occurrence is high because the geometry already misses. Severity stays at mission loss, not a shock, only while the mat stays dark. TEST_PLAN 20.5 is what keeps the mat dark.

## 7. Charger stuck on (RPN 144)

Planned charge is 1.00 A. Loss at 12.6 V and efficiency 0.929 is 0.963 W (calc only, BQ24133_HEAT.md). A 6 hour sit with the rail cut, central corner, 25 C room: cells 28.36 C, trunk wall 26.57 C, knee reading 25.0 C (sim pass only). That matches the cut-rail row already in BQ24133_HEAT.md. Cells stay inside 0 C to 60 C. The wall stays under 49 C.

The timer on the board note is 6.35 h (calc only, 68 nF times 5.6 min/nF). Heat at 0.963 W is not the hazard. The hazard is current that does not fall through 0.10 A, or a timer that does not stop the chip. This thermal model does not integrate cell voltage. Over-voltage is BLOCKER here.

## 8. Servo rail on while docked (RPN 120)

The pick holds the Pololu 2815 off while the nest is present (circuitry/SERVO_RAIL.md). The nest is not wired to the switch input, so a rail that comes on anyway is pack voltage, 12.6 V or less, not the 15 V nest.

Termination is 0.10 A (cited, one tenth of the 1.00 A fast-charge setting). Fourteen servos at the C001 idle of 21 mA are 0.294 A (calc only). That already blocks termination. The C018 running no-load current is 180 mA at 12 V (cited). Fourteen of those are 2.52 A (calc only). Torque-off current for the C018 is BLOCKER. The 180 mA row is an upper bound if the servos are powered and free, not the limp sit.

Sim pass only, central, 25 C, 6 h, charger 0.963 W:

| Case | Cells | Knee reading | BEC case | Trunk wall |
|---|---|---|---|---|
| Rail cut | 28.36 C | 25.0 C | (no servo current) | 26.57 C |
| 21 mA each, 12.6 V | 29.91 C | 29.25 C | 33.22 C | 27.61 C |
| 180 mA each, 12.0 V | 40.0 C | 51.71 C | 59.25 C | 34.33 C |

The 21 mA row matches the pack-fed sit already published (cells 29.91 C, knee 29.25 C). Heat in these three rows stays inside the cell window and under the 49 C wall edge. The fault is still real: charge current never falls through 0.10 A, so the charge does not finish. A hot-spot claim beyond this shell model is BLOCKER.

## 9. Nuisance trip (RPN 120)

Run C pack peak is 15.57 A at a 0.40 m/s command (sim pass only). The STS12 0.15 m/s walk peaks at 9.527 A (sim pass only). The watch band 13 A to 21 A is calc only from a cited 17 A plus or minus 4 A. It is not a 3S datasheet.

Calc only, if the peak is held for 20 ms: 15.57 A trips a 13 A / 8 ms threshold and does not trip 17 A or 21 A. 9.527 A trips none of those. The duration of the real peak was not in the summary, so a trip/no-trip of the actual pulse is BLOCKER. The risk is a protector whose low edge sits on a normal walk.

## 10. Pi brownout (RPN 105)

TEST_PLAN 4.3 checks the 5 V regulator from 6.0 V in. The STS12 typical walk minimum bus is 11.371 V and minimum BEC output is 11.035 V (sim pass only). Both are above 6.0 V, so that walk does not enter the untested input. An injected bus of 5.4 V is below 6.0 V and is the brownout case. The Pi under-voltage warning voltage was not opened for this playbook (BLOCKER). Do not treat 6.0 V as the Pi's own threshold. It is the lowest input the bench plan already names.

## 11. BEC failure (RPN 84)

On the STS12 walk a 12.0 V setpoint does not regulate. Input minimum is 11.335 V typical and 11.223 V high-side (sim pass only), and regulation needs 12.3 V (12.0 plus the 0.30 V dropout assumption). A shorted pass element leaves the walk in the dropout state it is already in. An open output puts the servos at 0 V. The netlist puts the Pi on that same switch, so the Pi goes with them.

The hot number people might quote by mistake: if the same current were buck-regulated at 12.0 V and efficiency 0.85, the loss is 10.173 W and the case is 171.9 C at 40 min in a 25 C room (sim pass only). That walk does not enter that regime. The dropout loss on the walk is 1.441 W and the case is 60.7 C (sim pass only, central, 25 C). Castle publishes no efficiency and no case limit. Both the 0.85 and the 0.30 V drop stay BLOCKER until TEST_PLAN 4.1 replaces them.

## 12. Limb breaker not yet in the harness (specified, RPN not reduced)

Three TI TPS259827ONRGE parts are now in the netlist (EFL, EFR, EFN) and in verify/part_limits.yaml. Cited, SLVSFE7: input 2.7 V to 24 V, RILIM 182 ohm gives 7.77 A to 8.54 A at 25 C and 7.23 A to 9.07 A from -40 C to 125 C. Fast trip is 210 percent of ILIM, typical. ITIMER 600 nF is a candidate. The short blanking corner is 150 ms and the long corner is 557 ms (calc only, from the cited 1.4 uA to 2.8 uA and 0.7 V to 1.3 V).

They are not in series. Cable EF is a no-route record from SPV to each input. The live SP1 to SP5 feeds still leave SPV. A 1 ohm nick on those feeds is still the row 3 fault. This row does not lower that RPN.

Whether a normal walk stays under 7.23 A for longer than the blanking is BLOCKER. The 100 ms figure is a moving average, not a pulse width (problems/KNEE_HEAT_CHAFE.md, problems/RUNC_JOINT_CURRENT.md). The Pi pin for power-good is BLOCKER. Nothing bought.

## 13. Rest rule (specified, not running)

Walk until the hottest Present Temperature is 55 C, drop torque, sit until it is 45 C, then walk again. That is the chosen heat fix in problems/KNEE_HEAT_CHAFE.md. On the run C 0.15 m/s typical current, after every 0.1 s bin is integrated, the guard walks 14.0 percent of 90 min at 25 C and 9.0 percent at 32 C (sim pass only, problems/RUNC_JOINT_CURRENT.md). The case peaks are 50.31 C and 51.01 C (sim pass only). Both are over the cited PLA 49 C edge and under the cited PETG 62 C point at 1.8 MPa.

The rule is not the code on the Pi. A sim share is not a hardware pass. The C018 operating temperature is still the C001 sheet (BLOCKER).

## 14. PETG knee-to-ankle sheets (specified, slicer still PLA)

The eight knee-to-ankle sheets are the PETG row in verify/part_limits.yaml. Cited HDT is 69 C at 0.45 MPa and 62 C at 1.8 MPa (Bambu PETG HF TDS). The case under the guard is about 50 C to 52 C (sim pass only). That is under 62 C and over the PLA 49 C edge, which is why the material and the rest rule are a pair. Creep at the structure-twin stress, about 4.3 MPa, is BLOCKER. D22 still prints those sheets on the PLA profile. This row does not change the slicer. Nothing bought.
