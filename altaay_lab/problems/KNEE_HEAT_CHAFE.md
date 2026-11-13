# Knee heat and the 1 ohm chafe

Written 2026-11-13. The thermal runs use the existing twin (`altaay_lab/twin/thermal/twin_thermal.py` through `gate_p45b.py`). CPU only. Nothing was bought. No policy was retrained.

PR 83 and PR 84 were open, so this note does not edit `test/FMEA.md`, `wiring/netlist.yaml`, or `verify/part_limits.yaml`. D61 was not edited. The script and the JSON sit next to this file: `altaay_lab/problems/knee_heat_chafe.py` and `altaay_lab/problems/knee_heat_chafe_results.json`.

Every temperature below is sim pass only. Currents taken from a log or an eval table stay sim pass only. Arithmetic on those currents, and the fuse windows, are calc only. A datasheet figure is cited. Anything missing is BLOCKER.

## Sanity check

The three headline numbers were re-run on the twin before any fix was scored.

| Claim | What this run produced | Verdict |
|---|---|---|
| Right knee reaches 60 C in about 3.3 min | Reading crosses 60 C at 3.33 min (sim pass only) | The clock is a real output of the old backlash log. It is the fast side of that model, and it is not run C |
| Body or servo peak about 95 C | Body 94.67 C and reading 102.36 C with the torque cut set to 200 C (sim pass only) | That peak is the cut-disabled run. With the sheet's 70 C torque-off left on, the same log peaks at a 70.02 C reading and a 63.61 C body |
| About 77 C with the 12 V servo | Body 76.74 C, reading crosses 60 C at 4.83 min, cut set to 200 C, idle omitted (sim pass only) | That 76.74 C matches the playbook. With the C001 idle added and the 70 C cut on, the body peaks at 65.06 C |

The 3.33 min and the 94.67 C body are the central corner, 25 C room, 40 min, on `session_bam_backlash_typical.csv`. The loop resistance in that rerun is 2.63 ohm, the BAM value `gate_p45b.py` uses when the file name does not contain "sheet" (winding 2.5 ohm, board 0.13 ohm). That is the path that prints 94.67 C. Right-knee motor current in the first 4 min of that log is 1.447 A RMS (sim pass only). The whole log is 1.378 A RMS. Pack bin maximum is 5.648 A. That is the trained-actuator backlash session the thermal note already used. Run C is a different walk: at a 0.15 m/s command the pack peak is 8.956 A, and at 0.40 m/s it is 15.599 A with a 100 ms moving-average maximum of 13.081 A (sim pass only, `eval_table_bec12.md`). That 100 ms figure is an average, not a pulse width. There is no run C per-servo current trace. BLOCKER for a run C knee amp. The 12 V rows below scale the old log by Kt. They are not run C.

Why the 95 C figure is the wrong design temperature:

- The STS3215 C001 sheet (A/1, item 7-11, cited in `THERMAL_TWIN.md`) turns torque off above 70 C. The 94.67 C run sets that cut to 200 C so the clock can be read. With the cut restored, the body stops at 63.61 C (sim pass only, this run).
- The same run holds motor current fixed while copper resistance rises. The knee study already showed that this is the hot side. A hot winding that is against the voltage cap draws less current.
- The 1.447 A belongs to the trained actuator. The C001 stall is 1.91 Nm at 2.5 A (cited, 19.5 kg.cm). The sim knee torque that produced this heat is above that stall (knee study, sim pass only). The bought C001 cannot hold the torque this 95 C is based on.

The 12 V number has the same cut issue. Kt of the C001 stall line is 0.7649 Nm/A (calc only, 19.5 kg.cm times 0.0980665, divided by 2.5 A). The C018 page gives 1.0896 Nm/A (`problems/sts12.json`, from the Feetech page). Current scale is 0.702. Winding resistance used here is 3.753 ohm, the C018 stall line of 4.444 ohm times the C001 winding share 2.5/2.96. The C018 page does not print a separate winding resistance. That split is an assumption. With the idle term left off, body 76.74 C and 4.83 min to a 60 C reading, which is the playbook figure exactly. That playbook row omitted the electronics idle. `gate_p45b.run_walk` adds it. The design rows below do too: 0.021 A times 11.576 V is 0.243 W per servo (calc only, C001 idle). With that term on and the cut still off, the body is 78.91 C and the reading crosses 60 C at 4.67 min (sim pass only). With the cut at 70 C and the idle on, the body peaks at 65.06 C at 25 C and 65.31 C at 32 C (sim pass only).

The 49 C edge is a cited HDT, and it is the low end of the band. SD3D PLA is 49 C (ASTM D648, `THERMAL_TWIN.md` [P1]). Ingeo 4043D is 55 C at 0.45 MPa. Bambu PLA Basic is 57 C at 0.45 MPa and 54 C at 1.8 MPa. The lab spool, Overture Easy PLA, publishes Vicat 66.2 C and no HDT. On the 12 V shape with the idle included, the knee case crosses 49 C at 3.5 min (sim pass only), while the reading crosses 60 C at 4.67 min. The sheets touch the case. A 60 C reading is already a case that has passed the 49 C edge.

The C018 product page opened in `problems/STS12.md` prints voltage, stall, speed, current, and weight. It does not print an operating temperature. The 60 C and 70 C lines used below are the C001 sheet. Applying them to the C018 is BLOCKER until that page or its PDF is opened for temperature.

## What was compared

Home duty used here: the duck walks, then sits with torque off. Two schedules were run for 90 min on the Kt-scaled 12 V shape, central corner, torque cut at 70 C.

- Fixed bouts: 90 s walk, 6 min sit, repeat (20 percent walking).
- Guard: keep walking until the hottest reading is 55 C, then sit with torque off until the reading is 45 C. A tighter guard stops at 50 C and resumes at 42 C.

Passive cooling and a lower current were run on a continuous 40 min walk so they can be compared with the cut-on baseline (body 65.06 C, reading reaches 60 C at 4.67 min). Walking bins include the 0.243 W idle.

| Option | Room | Right knee reading | Right knee case | Cells | Trunk wall | Walk share |
|---|---|---|---|---|---|---|
| Continuous, cut at 70 C | 25 C | 70.02 C at the cut | 65.06 C | 43.65 C | 29.59 C | 1.00 |
| Continuous, cut at 70 C | 32 C | 70.03 C | 65.31 C | 50.44 C | 36.51 C | 1.00 |
| 90 s walk, 6 min sit | 25 C | 48.71 C | 45.55 C | 32.50 C | 27.27 C | 0.20 |
| 90 s walk, 6 min sit | 32 C | 55.76 C | 52.51 C | 39.35 C | 34.20 C | 0.20 |
| Guard 55 C / 45 C | 25 C | 55.04 C | 51.68 C | 37.24 C | 28.15 C | 0.388 |
| Guard 55 C / 45 C | 32 C | 55.05 C | 52.12 C | 39.09 C | 34.16 C | 0.201 |
| Guard 50 C / 42 C | 25 C | 50.06 C | 47.06 C | 35.11 C | 27.74 C | 0.305 |
| Knee area times 1.3, continuous | 25 C | 70.00 C | 64.86 C | 43.65 C | 29.59 C | 1.00 |
| Knee area times 1.8, continuous | 25 C | 61.62 C | 56.66 C | 43.65 C | 29.59 C | 1.00 |
| Trunk vents, continuous | 25 C | 70.02 C | 65.06 C | 38.53 C | 28.78 C | 1.00 |
| Current times 0.70, continuous | 25 C | 52.99 C | 50.93 C | 34.85 C | 27.87 C | 1.00 |
| Current times 0.55, continuous | 25 C | 42.86 C | 41.67 C | 31.44 C | 27.19 C | 1.00 |

All of those temperatures are sim pass only. The area factors and the vent conductance (0.3 W/K, inner convection times 3) are the twin's existing assumptions. Friction heat is omitted, which makes the knee slightly cool. Walks and rests both use the C001 idle of 21 mA. The C018 torque-off current is BLOCKER.

Vents do not move the knee. The case stays 65.06 C. They do cool the cells (43.65 C to 38.53 C) and the BEC case estimate (61.94 C to 57.07 C). The knee is outside the trunk.

A 30 percent area increase, the twin's clip-on sink, moves the 60 C reading from 4.67 min to 5.33 min and the cut still stops the body near 65 C. An 80 percent increase, a larger plate than the case, leaves a continuous walk at a 61.62 C reading and a 56.66 C case. That reading is over the 60 C operating line. A plate with no added air area does not cool the case in this one-node model. Aluminum conducts so well that the plastic face of a thin plate sits at the case temperature. The useful spreader is one that adds area to the air, and the leg has little room for it. The guarded runs with the 30 percent sink stay at a 51.36 C and 51.66 C case, the same band as the guard alone, because the guard already caps the reading.

Cutting the current to 0.70 of the scaled shape, with the idle left on, reaches a 52.99 C reading and a 50.93 C case. The case crosses 49 C at 11.5 min (sim pass only). It does not clear the PLA edge. The earlier 48.59 C case omitted the 0.243 W idle, and that omission was what put it under 49 C. The 0.70 scale still assumes torque and current move together and that the duck still stands. A gait that does this is BLOCKER. It needs a retrain, and this session does not use a paid GPU. The 0.55 scale stays cooler (case 41.67 C) and is the same open gait question.

## Cited material limits

The case temperature is what the knee sheets see. Changing filament does not change the sim temperature. It changes the limit that temperature is compared with.

| Material | HDT | Source |
|---|---|---|
| PLA, low edge | 49 C, ASTM D648 | SD3D PLA, `THERMAL_TWIN.md` [P1] |
| PLA, the band already used | 49 C to 57 C at 0.45 MPa, Tg 55 C to 60 C | same note, [P1] to [P3] |
| Lab spool | Vicat 66.2 C, no HDT | Overture Easy PLA TDS v5.1, [P5] |
| PETG | 69 C at 0.45 MPa, 62 C at 1.8 MPa, Tg 66 C | Bambu PETG HF TDS V1.0, [P6], https://botland.com.pl/img/art/inne/25540_karta_produktu.pdf |
| ASA | 100 C at 0.45 MPa, 92 C at 1.8 MPa, ISO 75 | Bambu ASA TDS V3.0, https://wiki.bambulab.com/filament-acc/abs-asa-pc/6eaf4c432d1d4014a1975e55a55ed00b.pdf |
| PA-CF (PAHT-CF; Bambu's current PA-CF) | 194 C at 0.45 MPa, 170 C at 1.8 MPa, ISO 75 | Bambu PAHT-CF TDS V3.0, https://wiki.bambulab.com/filament-acc/asacf-pahtcf/65f1b18a6d6142d794a1a6a00f1496ef.pdf |

The knee-sheet standing stress in the structure twin is about 4.3 MPa, above both HDT test stresses. Creep rate at that stress is BLOCKER for every filament in the table. The HDT comparison below is the cited temperature, not a creep clearance.

P45B discharge is 0 C to 60 C (cited, version 1.2). The trunk wall on these runs stays at or under 35.93 C, inside the PLA band, so the body shell can stay PLA. Feetech publishes no winding limit. The Faulhaber motors of this size allow 125 C (`THERMAL_TWIN.md` [M1]). That 125 C is a comparison, not a limit for this servo.

## Chosen heat fix

Use the 55 C / 45 C guard, and print the eight knee-to-ankle sheets in PETG.

The guard is a behavior-layer rest. Walk until the hottest Present Temperature is 55 C, drop torque, sit until it is 45 C, then walk again. No new gait and no new part in the power path. In 90 min the sim walks 34.9 min at 25 C (share 0.388) and 18.1 min at 32 C (share 0.201). Those minutes are calc only from the sim share times 90.

Resulting temperatures, sim pass only, central corner, cut at 70 C, Kt-scaled shape:

| Part | 25 C room | 32 C room | Limit used |
|---|---|---|---|
| Right knee reading | 55.04 C | 55.05 C | 60 C, C001 sheet. C018's own range is BLOCKER |
| Right knee case, the sheet face | 51.68 C | 52.12 C | PETG 62 C at 1.8 MPa (cited). Over the PLA 49 C edge |
| Left knee case | 48.82 C | 50.05 C | PETG 62 C. 48.82 C is under the PLA 49 C edge by a small margin |
| Other servo cases | under 49 C | under 49 C | PLA 49 C |
| Cells | 37.24 C | 39.09 C | 60 C, P45B sheet |
| Trunk wall | 28.15 C | 34.16 C | PLA 49 C. The shell stays PLA |
| Right knee winding | 96.98 C | 96.56 C | No Feetech limit (BLOCKER). Under the 125 C Faulhaber comparison |
| BEC case estimate | 58.99 C | 62.61 C | Castle publishes no case limit (BLOCKER) |

The BEC figure is the twin's steady case formula on the air at the end of the run, using the walk-mean loss of 1.441 W (calc only, dropout 0.30 V). The continuous run of that same loss, with the idle on, is 61.94 C at 25 C (sim pass only). The playbook's 60.7 C is the idle-off loss on the older session. Dropout 0.30 V remains an assumption.

PLA knee sheets fail this guard: the case is 51.68 C at 25 C. PETG's 62 C HDT at 1.8 MPa covers 52.12 C. ASA at 92 C and PAHT-CF at 170 C also cover it, with more room, and they ask for a hotter chamber or a dried nylon. PETG is the filament that clears this duty without that process. A continuous walk still reaches a 65.06 C case, which is over PETG's 62 C, so the material swap without the guard does not clear the knee. The guard without the material swap does not clear PLA.

The fixed 90 s / 6 min schedule also stays under the servo's 60 C line, and at 25 C the case is 45.55 C, under the PLA edge. At 32 C the case is 52.51 C, so a warm room still wants PETG. The guard is the one to ship because it walks longer when the room is cool (34.9 min against 18 min in the same 90) and it follows the sensor the servo already has.

## Chafe calc

Path resistance, calc only: 3 times 15 mOhm, plus BMS 25 mOhm max, fuse 6 mOhm, XT30 2 mOhm, switch 13 mOhm, wires 8.8 mOhm. Sum 0.0998 ohm.

At 12.6 V and a 1.00 ohm nick: current 12.6 / 1.0998 = 11.46 A. Heat in the nick 11.46 squared times 1.00 = 131.3 W. Both match the playbook. 11.46 A is under the 15 A fuse rating. A 0.10 ohm nick is 63.06 A and does exceed it.

A nick on a servo lead after the BEC does not see 12.6 V. At 11.0 V and 1.05 ohm the current is 10.48 A (calc only), still under 15 A. The "never trips" conclusion holds for both voltages. Local temperature at the nick is BLOCKER. The twin has no nick node.

## Fuse curve

The fuse on the bill is Littelfuse 0287015.PXCN, the ATOF 0287 family, 15 A, 32 V. Time-current windows below are cited from the ATOF datasheet for a fuse of 3 A to 40 A:

https://www.littelfuse.com/assetdocs/littelfuse_datasheet_287_atof_r2.7.pdf

| Percent of rating | Opening time |
|---|---|
| 110 | 360,000 s minimum, no maximum. It holds |
| 135 | 0.750 s to 600 s |
| 160 | 0.250 s to 50 s |
| 200 | 0.150 s to 5 s |
| 350 | 0.080 s to 0.500 s |
| 600 | 0.100 s maximum for 1 A to 30 A |

11.46 A is 76.4 percent of 15 A (calc only). That is under the 110 percent row, so the 15 A fuse holds it. The walk peaks do not open it either: 15.599 A is 104 percent and 13.081 A is 87 percent, both under 110 percent (calc only, on sim pass only peaks).

A smaller fuse on the whole pack does not separate the two currents, because the chafe is the lower one.

| Fuse | 11.46 A chafe | 15.599 A pack peak | 13.081 A for 100 ms |
|---|---|---|---|
| 15 A | 76 percent, holds | 104 percent, holds | 87 percent, holds |
| 10 A | 115 percent, between the hold row and the 135 percent row. Not required to open | 156 percent, required to open. Window is not the 100 ms peak | 131 percent, not yet the 135 percent row |
| 7.5 A | 153 percent, required to open. The cited ceiling on a current under 160 percent is the 135 percent maximum, 600 s | 208 percent, between the 200 percent row (minimum 0.150 s) and the 350 percent row | 174 percent, minimum on the 160 percent row is 0.250 s, so a lone 100 ms pulse is shorter than that minimum |
| 5 A on the pack | 229 percent, between 200 percent (maximum 5 s) and 350 percent (maximum 0.5 s) | 312 percent, in that same span. A pack fuse this small sits on the jog | 262 percent, same span |

A slow-blow part moves the wrong way. The chafe is a smaller current than the jog peak. Extra delay gives the nick more time at 131.3 W and does not create a rating that opens at 11.46 A while ignoring 15.6 A.

Per-branch blade fuses do separate the currents. The old 100 ms feed peaks in `WIRES.md` are 1.64 A, 1.98 A, 2.21 A, 2.11 A, and 1.52 A (sim pass only, the 7.4 V budget). Scaling each by 13.081 / 7.04 = 1.858 (calc only) gives a right-leg sum of peaks of 8.027 A. That sum overstates a simultaneous current. On the old log the right-leg supply, summed inside each 5 s bin, peaks at 1.808 A (sim pass only). A 7.5 A ATOF on that leg would hold 8.027 A (107 percent, under the 110 percent row) and would be required to open at 11.46 A, with a clear time that the sheet does not cap below 600 s. Five minutes at 131.3 W is a bad clear. The 22 AWG Mini-SPOX contact is cited at 3.0 A (`CABLE_MAP.md`). The scaled single-feed peaks run from 2.82 A to 4.11 A, so a 0.40 m/s jog may already sit on that 3.0 A contact. That contact check is BLOCKER until a run C branch current exists. The scale is not that current.

Servo Present Current does not see this nick. The nick is a path from the supply wire to ground. The current does not pass through the servo's sensor. A Pi that only polls Present Current stays blind. A pack or branch sensor would see it. The duck does not have a branch current sensor today.

## Chosen chafe protection

Three TI TPS259827ONRGE parts, one per limb, wired ahead of the split so both feeds of a leg share one device. Left limb ahead of SP1 and SP4, right limb ahead of SP2 and SP5, neck ahead of SP3. Circuit-breaker variant, no overvoltage lockout. The 16.9 V lockout variant (TPS259824ONRGE) would also stay closed at 12.6 V, since its rising threshold is 16.32 V minimum. The no-lockout part does not depend on that.

Cited from SLVSFE7, https://www.ti.com/lit/ds/symlink/tps25982.pdf :

- Input 2.7 V to 24 V. The pack, 9.0 V to 12.6 V, is inside that.
- RILIM of 182 ohm: ILIM 7.77 A to 8.54 A at 25 C, and 7.23 A to 9.07 A from -40 C to 125 C.
- Fast-trip threshold 210 percent of ILIM, typical. At the hot maximum that is 19.0 A (calc only). The 11.46 A nick is under it, so the nick uses the blanking timer. A hard short on that limb, the 63 A row, is over it and uses the 400 ns typical short-circuit path.
- On resistance 2.7 mohm typical. Drop at 8 A is 21.6 mV (calc only).
- ITIMER open is a 0 s blanking. A capacitor to ground sets the time from the discharge current, 1.4 uA to 2.8 uA, and the voltage delta, 0.7 V to 1.3 V.

The 11.46 A nick is above 9.07 A, so every part in the cited window starts the timer. The conservative leg bound of 8.027 A overlaps 7.23 A to 9.07 A, so a simultaneous sum of the two feed peaks can also start the timer. With C in nF, t in ms is C times dV divided by I in uA (calc only from the cited pin current and delta). At 600 nF the short corner is 150 ms and the long corner is 557 ms. A nick that stays then opens by 557 ms. Energy in the nick over that long corner is 131.3 W times 0.557 s = 73 J (calc only). The nick temperature for those 73 J is still BLOCKER.

The 13.081 A figure is the maximum of a 50-sample moving average (`em_twin.py` convolves the pack current with `ones(50)/50`). It is an average, not the time the current stays high. A branch can sit above 7.23 A for longer than 150 ms and still post that average. Whether a normal walk trips the breaker is BLOCKER until a branch-current trace gives the time above 7.23 A. The 600 nF value is a candidate capacitor, not a clearance of the jog.

The datasheet warns that a large ITIMER capacitor can look like a short during startup. The equation for the maximum capacitor did not extract cleanly from the PDF text. Whether 600 nF is under that limit is BLOCKER.

PR 84 has not merged, so the part is not added to the netlist or to `part_limits.yaml`. When that change is in, the netlist wants three TPS259827ONRGE records, RILIM 182 ohm, ITIMER 600 nF, PG brought to a Pi input. The Pi pin is not chosen here (BLOCKER). F1, the 15 A ATOF, stays. It is the pack fuse for a hard short (0.10 ohm is 63 A, which is past the 350 percent row). A nick on the main 16 AWG ahead of these three devices still misses F1 at 11.46 A. The moving chafe is the knee loop, which is downstream of the leg device. The bay lead is the residual.

`part_limits.yaml` would gain one record: TPS259827ONRGE, input 2.7 V to 24 V, ILIM at 182 ohm as cited above, source the TI PDF. That file is not edited in this change.

## FMEA scores

PR 83 has not merged, so `test/FMEA.md` is not edited. The scores below use the same 1 to 10 scale as that file. They are judgment, not a measured rate.

Cable chafe, as that file scores it today: S 8, O 4, D 7, RPN 224. The physics (11.46 A, fuse holds) is confirmed here.

Projected score once the three eFuses are on the bill and PG is wired to the Pi: S 6 (a limb drops and the duck can fall), O 4 (a nick can still happen), D 3 (PG is a check the product can read). RPN 72. Until PG is wired, detection stays weak and the score stays closer to the old 224. The bay-lead nick ahead of the three devices is not covered, so that path keeps the old score.

Knee heat is not a row in that FMEA. Proposed row for the design as it stands, continuous walk, cut disabled in the headline: S 6 (the walk ends or the PLA creeps; the cut is not a fire by itself), O 6 (a home session can walk straight through), D 6 (Present Temperature is there, and nothing in the behavior stops the walk before the case passes 49 C). RPN 216.

Projected score with the guard in the behavior and the knee sheets in PETG: S 6, O 2 (the hot path is a guard that was left out), D 2 (the guard is the check). RPN 24. The C018 temperature rating and the creep rate stay BLOCKER, so this RPN is not a hardware pass.

## Open BLOCKERs

- No run C per-servo current. The 12 V temperatures are the old log scaled by Kt.
- C018 operating temperature and torque-off current are not on the page that was opened.
- C018 winding resistance is not printed. The 3.753 ohm split is an assumption.
- BEC dropout 0.30 V, and Castle publishes no case limit.
- Feetech publishes no winding limit.
- Creep rate of the knee sheets at about 4.3 MPa is above the HDT test stress.
- Nick temperature. The twin has no nick node. The 73 J figure is energy, not a temperature.
- Whether 600 nF is under the TPS25982 startup limit on ITIMER.
- Time a walking branch stays above 7.23 A. The 13.081 A figure is a 50-sample moving average, not that duration, so a nuisance trip on the jog is still open.
- Which Pi pin reads PG.
- Run C branch current against the 3.0 A Mini-SPOX contact. The scaled feed peaks are a calc, not that trace.
- A 1 ohm nick on the main pack lead, ahead of the three limb devices, still sits under the 15 A fuse.
