# Electrical twin, V1: power-on, the BMS against falls and get-ups, regeneration and the servo bus ground (sim pass only)

Written 2026-11-04 about 4:45 PM ET by the V1 electrical track (a Claude Code agent for the lead; branch claude/v1-elec, local commits only). V1 is the stock walking duck on legs, indoors, our 2.65 kg build (2652.8 g). Every sim number here is sim pass only; hand numbers are calc only. Nothing has run on real parts.

## Answer

Two risks and one blocker; nothing fails. Regeneration and the servo bus signal are fine.

1. **RISK: a hard shove can trip the BMS.** A 60 N, 0.1 s shove to the left of the standing duck makes the stock policy saturate several servos at once while it tries to recover. The pack then draws 19.5 to 20.6 A, and more than 17 A for 4 to 13 ms (6 of 6 seeds; the same with the policy still running on the floor). The Tenergy 32175 trips at 22 +/- 5 A after 8 +/- 4 ms, so a board at the low end of its band trips. Then everything goes dark until someone cycles the panel switch, and the Pi loses power with no shutdown. A board that trips at 20 A or more trips in 0 of the 41 simulated events. Fix ($0): give the existing TEST_PLAN 3.3 trip run a pass line of 21 A or more.
2. **RISK: the cells run below their minimum if the robot is left on after a battery hard stop.** The guard powers off the Pi, but the panel switch keeps the servos, the BEC, the 5 V regulator and the halted Pi powered. That is 0.11 to 0.41 A (calc only), which takes the cells from the hard-stop point to the P30B's 2.5 V minimum in about 1.2 to 4.4 hours. The BMS only cuts at 2.40 V. Fix ($0): an operating rule and a measurement in TEST_PLAN 11.
3. **BLOCKER: inrush at power-on.** The BMS over-current function cannot trip at power-on (calc only). Tenergy publishes no threshold or delay for its short-circuit function, and Castle publishes no input capacitance for the BEC. A bench step (20 power-ons, TEST_PLAN 3.5) settles it.
4. **OK: regeneration and over-voltage.** The servo bus never takes net energy back in walking or in any of 38 falls. Only the scripted get-up throw (a later lab step) does, and it peaks at -4.06 W and 0.026 J. If the BMS has opened, falling limbs cannot pump the bus: the fastest joint in any fall or get-up, 5.37 rad/s, gives 6.17 V of back-EMF.
5. **OK: the bus signal at the far servo.** While walking, the data ground at the far knee and ankle sits 0.07 to 0.10 V above the adapter ground (typical corner) and at most 0.21 V (high-side corner). The adapter's receiver reads a low up to 0.8 V, so every bit is valid. The head roll has the largest offset: up to 0.52 V in hard falls at the TEST_PLAN 5 hop limit of 40 mOhm. Only hops worse than that limit pass 0.8 V.

## Method

- Events (the shared lab gym, overlay gym/overlays/duck; 1 ms, implicitfast, elliptic cone, floor friction 1.0):
  - Falls of the collision duck (its shells hit the floor), from the get-up fall library's own cases: 60 N standing pushes and 40 N walking pushes in four directions, plus the 15 N push series. That is 38 runs: 9 cases with the fall stop of the get-up library, the same 9 with the policy still running after the fall (the stock Runtime has no fall stop), and 5 more seeds of the four side cases. The servo is the twin's model at the BEC set point (7.2 V), logged every 1 ms: torque F and joint speed w of all 14 servos. Runner: v1_elec/fall_traces.py in that overlay.
  - Get-ups: the get-up twin's own 1 ms logs of its final back, side and front programs, our build, 7.2 V (getup/evaluate.py fine_run in that overlay).
  - Walking: the 3.4 s before the push in the walking-push runs.
- Network: each trace is replayed through the as-built network of twin/electromech/power_net.py, the one VERIFICATION.md E6, E6b and C7 check. That is D15 plus the D23 feeds, every length from wiring/netlist.yaml (sha256 0f4af5bff3), with the P30B pack from its data sheet curves at full charge and at nominal (48 % SOC), both resistance corners, plus hops of 28 and 40 mOhm per conductor (the TEST_PLAN 5 bands, typical corner). The servo law is that of sim/power_path_sim.py and the twin's replay(): commanded volts capped at the servo's own bus volts, and no credit for braking in the supply current. Script: bus_events.py; 180 runs.
- Regeneration: the signed sum of the 14 servos' electrical power u (u - kt w) / R. Negative means the servos push energy back into the bus.
- Data ground: V(servo ground) - V(adapter ground) on the resistive ground network of sim/power_fix.py minus_edges(). That network has the SP grounds and their tails, the kit hop grounds, the SP4 and SP5 grounds, the D15 data-lead grounds, the adapter copper, and the USB ground with P12 to the regulator. Each servo's return current enters at its own ground node.
- Tables: bus_tables.py writes out/summary.json from the run files.

## RISK 1: the BMS over-current band against the summed peaks

| Event (worst corner and charge) | Pack peak | Held 4 / 8 / 12 ms | Over 17 A |
|---|---|---|---|
| Walking (the 40 N push runs, before the push) | 8.64 A | under 9 A | 0 ms |
| Get-up throws, back / side / front | 11.8 A | 11.6 / 11.2 / 11.1 A | 0 ms |
| 40 N pushes while walking, fall stop | 13.2 A | 12.7 A at most | 0 ms |
| 40 N pushes while walking, policy running on the floor | 22.6 A | 12.7 A at most | 1 ms at most |
| 60 N standing pushes forward, back, right | 21.6 A (policy running) | 12.7 A at most | 1 ms at most |
| **60 N standing push to the left, 6 seeds and policy running** | **19.5 to 20.6 A** | **19.8 / 18.6 / 17.4 A** | **4 to 13 ms** |

How many of the 41 events (38 falls, 3 get-ups; worst corner and charge each) would trip a board that trips at a given current:

| Board trips at | delay 4 ms | 8 ms | 12 ms |
|---|---|---|---|
| 17 A | 7 | 7 | 2 |
| 18 A | 7 | 3 | 0 |
| 19 A | 3 | 0 | 0 |
| 20 A | 0 | 0 | 0 |
| 21 A | 0 | 0 | 0 |

- Where it comes from: the peak comes at 3.10 s, during the push (3.0 to 3.1 s), with the torso at 16 deg. The fall rule (45 deg) fires 85 ms later. The policy's recovery puts the left hip pitch, left knee, head pitch and right hip roll at their torque limits together, with 11 servos drawing 0.6 to 2.8 A each. All 7 events that trip at 17 to 18 A are this one case. A torque cut at fall detection would come too late.
- Source: Tenergy 32175 product page (BOM line 8 link, read again 2026-11-04 with curl). Over-current detection 22 +/- 5 A, delay 8 +/- 4 ms, release "Cut load". Short-circuit protection "Have", with no threshold or delay. Upstream third-party evidence: 10 A class boards cut out at high current (UPSTREAM_ISSUES.md G4).
- Consequence: the BMS opens and stays open while a load is connected, so the robot goes dark until the panel switch is cycled. The servos go limp and the Pi loses power with no shutdown. No part is damaged, and the robot was falling anyway after that shove.
- Fix ($0, the smallest): TEST_PLAN 3.3 already writes down the trip current on the TE4 load. Give it a pass line of **21 A or more** (the twin's largest 4 ms current, 19.79 A, plus 1 A). Twin result with the fix: a board that trips at 20 A or more trips in 0 of 41 events, at any delay from 4 ms. A board under 21 A gets a second board (BOM line 8, $22.99, US seller; buying needs Ahmed's OK). The other choice is to accept that a hard shove can switch the robot off.
- The rest of the chain holds this event (sim pass only, calc only). The 15 A ATO fuse sees 137 % for 13 ms, and ATO fuses open at 135 % only after 0.75 to 600 s (POWER.md section 4). The Pololu 2815 is rated 90 A maximum. The bus sum at 7.2 V is at most 17.9 A (6 seeds, before the network sag), under the CC BEC Pro's 20 A peak rating (Castle does not say for how long). The XT30U and the 16 AWG pack path carry it for 13 ms.

## RISK 2: the drain after the battery guard's poweroff

- bench/walk_with_guard.py, on a battery hard stop, drops to low gains, turns the torque off and runs `systemctl poweroff` (software/PI_SETUP.md). The panel switch stays closed, so the Pololu 2815 keeps the switched pack bus on.
- The loads that stay on:
  - 14 servos at idle, 6 mA each (Feetech 2020 copy, sim/CURRENT_BUDGET.md) to 21 mA (C001 specification A/1, twin/thermal/THERMAL_TWIN.md F1), on a bus near 6.3 V.
  - The halted Pi with its 3.3 V loads: not published. ASSUMPTION: 20 to 100 mA at 5 V.
  - With 0.85 BEC and 0.9 regulator efficiency (ASSUMPTION), that is 0.11 to 0.41 A from a 6.6 V pack (calc only).
- Charge left at the standing hard stop: the 6.0 V servo reading is about 3.2 to 3.3 V per cell open circuit (software/SOFTWARE.md section 5). At 3.30 V the P30B has 489 mAh left to 2.5 V (twin/electromech pack state "low", from the data sheet curves). So the cells pass the P30B's 2.5 V minimum after about 1.2 to 4.4 hours (calc only), and the BMS only cuts at 2.40 V.
- Fix ($0): an operating rule in TEST_PLAN 11: after a battery hard stop, switch off at the panel switch at once, and never leave the duck switched on unattended. Also a measurement: the pack current after the guard's poweroff with the panel switch still on, which settles the 0.11 to 0.41 A bound. A switch that the Pi can turn off would change D8 (the stock panel switch in the body_back cutout). That is for Ahmed, and only if the rule is not enough.

## OK and checked (one line each)

- Over-current at power-on: the worst case is an instant switch into the inputs on VSW, at most 8.4 V / 99 mOhm = 85 A (95 mOhm cells to switch, the TEST_PLAN 3.2 gate, plus P10). That decays with a time constant of 0.099 ohm x C, so it stays over 17 A for 1.6 time constants. To stay over 17 A for the 4 ms the band needs would take 25 mF on VSW (calc only). The Pololu 2815 also turns on through its 100 kOhm gate resistor R2 (Pololu schematic, read 2026-11-04), so it ramps rather than steps. The short-circuit function is BLOCKER B48.
- Charging the servo bus at power-on: the BEC's 20 A peak rating limits it. With 8 mF on the bus (ASSUMPTION, about 14 x 470 uF), that takes 2.9 ms, under the 4 ms shortest delay (calc only). B48's bench step covers it.
- Arcing at power-on: the panel switch carries only the 2815 control current, 84 uA (WIRING.md). The XT30 sees an inrush only if it is mated with the panel switch on, so mate it with the switch off (TEST_PLAN 3.5).
- What the servos do at power-on: Torque Enable (register 40, RAM) resets to 0, so they come up limp (register reference of two firmware 3.10 units, twin/thermal/THERMAL_TWIN.md F3). The Pi and the servos power up together from VSW, so the duck must be held or hanging at power-on (TEST_PLAN 8).
- Regeneration while walking: the net servo bus power is never negative. The twin's closed-loop walks (backlash and plain models, full and nominal charge, 30 s at 500 Hz) bottom out at 0.0 to 1.85 W, and the gym walk at 4.36 W. Braking servos return at most 3.1 W, which the other servos always take.
- Regeneration in falls: the net bus power is never negative in any of the 38 falls.
- Over-voltage at a full 8.4 V pack: since nothing regenerates in V1, the bus stays at the BEC set point (7.2 V; TEST_PLAN 4.1 measures it).
  - A BEC failed to pass-through gives 8.4 V (GAPS A2, the upstream build's normal state).
  - Register 14 (Max Voltage Limit) reads 140 on firmware 3.10 units and 80 on units in a third-party log (UPSTREAM_ISSUES.md G4).
  - With Unload Condition 44 (no voltage bit), a voltage error only blinks the LED. bench/first_servo_check.py reads register 14 (TEST_PLAN 7.1).
- With the BMS open while limbs move: the bus collapses and the servos go limp. Their H-bridge diodes could only feed back the back-EMF, kt x w = 1.148 x 5.37 = 6.17 V at the fastest joint of any fall or get-up, which is under the bus volts.
- A hand back-driving a limp joint: it needs over 7.7 rad/s at the output to lift the bus over 7.4 V (calc only; two 0.7 V diode drops, ASSUMPTION). A hand turning a joint against the servo's torque is plugging: it draws current and returns none.
- Get-up throws (a later lab step, not V1): -4.06 W net for 0.026 J at most. If the BEC cannot sink current, this raises the bus by an amount set by the bus capacitance, which nobody publishes. The bus is bounded near the BEC input plus one diode, about 8.9 V at a full pack (ASSUMPTION: a MOSFET buck). This is an open item for the get-up step, not numbered.
- Bus signal levels: the adapter drives the bus low through U3 (SN74LVC1G126, enabled through Q1 MMBT3906 only while TX is low) and holds it high with R5, 10 kOhm. It receives through U4 (SN74LVC1G125): VIH 2.0 V and VIL 0.8 V at VCC 3.0 to 3.6 V. Sources: the Waveshare schematic (netlist U2 source) and the TI SN74LVC1G125 data sheet, both read 2026-11-04.
- Bus signal timing: the data net is 2.13 m of conductor (netlist: SD1 330 mm, SD2 150 mm, 11 kit cables of 150 mm). The upstream wiring has 2.44 m (S1, S6 and S14 plus the same kit cables), with the same 14 receivers. So the bus has no more capacitance than the stock robot that runs it at 1 Mbaud.
- Data ground offset at the far servo, worst runs:

| Case | knees L / R | ankles L / R | head roll | runs at or over 0.8 V |
|---|---|---|---|---|
| walk, typical | 0.09 / 0.10 V | 0.07 / 0.07 V | 0.15 V | 0 of 8 |
| walk, high-side | 0.20 / 0.21 V | 0.12 / 0.11 V | 0.38 V | 0 of 8 |
| walk, hop 40 mOhm | 0.13 / 0.14 V | 0.09 / 0.09 V | 0.23 V | 0 of 8 |
| falls, typical | 0.18 / 0.18 V | 0.10 / 0.10 V | 0.47 V | 0 of 76 |
| falls, hop 40 mOhm | 0.16 / 0.18 V | 0.09 / 0.10 V | 0.52 V | 0 of 18 |
| falls, high-side (65 mOhm hops, past the TEST_PLAN 5 fail band) | 0.36 / 0.35 V | 0.16 / 0.17 V | 1.06 V | 16 of 76 |

  So the TEST_PLAN 5 fail band (over 40 mOhm) protects the data link too. The servo grounds never sit below the adapter ground by more than 0.01 V, so the adapter's lows reach every servo as lows.
- Servo under-voltage cut (4.0 V): it is reached only in the high-side corner, while the policy flails on the floor after a fall (14 of 180 runs). The lowest servo in the typical corner is 4.26 V.
- 5 V side:
  - The lowest BEC input over all events is 5.97 V at full charge and 5.04 V at nominal (high-side corner, the policy running on the floor after a 40 N push).
  - The D30V30F5 then gives about 5.0 V at the 0.6 A typical load and about 4.7 V if the 2.4 A peak load comes at the same moment: P13 drops 0.10 V, and the regulator 0.28 V at 2.5 A (Pololu graph, WIRING.md) (calc only).
  - The Pi Zero 2 W's own brown-out point was not found in a source this session (the Raspberry Pi site refused the fetch).
- Protection chain while walking: the fuse, the XT30U, the 16 AWG pack path and the BMS working current carry 5.9 A RMS (VERIFICATION.md C7). The Pololu 2815 at 99 % of its 55 C point stays the TEST_PLAN 4.2 heat check (heat track).
- Grounding: the Pi-to-servo-bus loop through the USB ground carries 0.09 A mean and 0.19 A at most (C7). It is in the ground offset model above. ESD on carpet with TPU soles: nothing known, not studied.
- Charging: the charger sits on BMS P+ and P- and charges with the robot off (WIRING.md). Nothing new.
- Completeness: every powered net has a source, a fuse and BMS upstream, a connector and a wire with a current check (VERIFICATION.md E1 and C7). No missing part was found with evidence that it is needed. V1 has no net regeneration, so no bulk capacitor or TVS is needed. The switch-on ring of the 550 mm P13 lead into the regulator's input is at most twice the 8.4 V step, 16.8 V (calc only), under its 45 V input (netlist U3).

## BLOCKERs

| # (HARDWARE_AUDIT) | Missing data | Bound used | Bench test that settles it |
|---|---|---|---|
| B47 | The real trip current and delay of our Tenergy 32175 board (22 +/- 5 A after 8 +/- 4 ms) | the band edges: 17 A after 4 ms trips in 7 of 41 events; 20 A or more in 0 | TEST_PLAN 3.3 with the 21 A pass line |
| B48 | The BMS short-circuit threshold and delay, the CC BEC Pro input capacitance and soft start, the servo input capacitance (none published), and the 2815 MOSFET gate charge (not named on its schematic) | the BMS over-current function cannot trip at power-on (calc only, above) | TEST_PLAN 3.5: 20 power-ons on the real pack, BMS never opens |
| B49 | The current drawn after the guard's poweroff with the panel switch on: the halted Pi Zero 2 W, servo idle (6 or 21 mA in the two Feetech copies), BEC and regulator quiescent | 0.11 to 0.41 A, so 1.2 to 4.4 h from the hard stop to 2.5 V per cell | TEST_PLAN 11: measure it; the operating rule meanwhile |

Not numbered, later lab step: the bus capacitance and whether the CC BEC Pro can sink current, both of which matter only for the get-up throw.

## Files

| File | What |
|---|---|
| bus_events.py | Replays F and w traces through the as-built network: the pack current against the BMS band, regeneration, the data ground offset per servo; one JSON per run set |
| bus_tables.py | The tables above from the run files; writes out/summary.json |
| out/summary.json | The summary of the 180 runs (in git, 8 kB) |

Heavy outputs (the 1 ms traces and per-run JSON) live in the session scratch folder only, not in git.

## How to run

1. Falls (in the shared lab gym, overlay gym/overlays/duck, one process, about 1 s of wall time per fall):
   - `python3 overlays/duck/v1_elec/fall_traces.py --out <dir>`
   - add `--keep-policy` for the policy running after the fall
   - add `--cases stand_push_left stand_push_right walk_push_left walk_push_right --seeds 2 3 4 5 6` for the extra seeds
2. From this folder, with ELEC_SCRATCH set to a folder outside the repo:
   - `python3 bus_events.py --hops 28 40 --out <falls.json> <dir>/*.npz`
   - the same with the get-up twin's 1 ms logs (getup/evaluate.py fine_run) for the get-ups
   - `--window 2.5 5.9` on the walking-push traces for the walk
   - about 3 to 6 minutes per run set
3. Then `python3 bus_tables.py --falls ... --getup ... --walk ... --out out/summary.json`.

## Track 1b fixes (2026-11-04 about 5:40 PM ET; sim pass only and calc only)

Written by the V1 track 1b agent (fixes, not just detection; branch claude/v1-elec, local commits only). Everything above stays as track 1 wrote it; this section corrects two twin details and gives the fixes with numbers before and after. Code: fix/ (bus_budget.py and its test, gnd_fix.py). Gym side: the shared lab gym, overlay gym/overlays/duck, v1_elec/fix_runs.py. Numbers: out/fix_summary.json.

### Two twin corrections first

1. **Servo gains as the robot runs them.** The stock runtime writes firmware P 30 to the 10 leg servos and P 8 to the 4 head servos (Open_Duck_Mini_Runtime 376de65 scripts/v2_rl_walk_mujoco.py lines 175 to 179). The trained kp is P 32 (Rhoban/bam b9e1111 bam/feetech/actuator.py lines 36 to 40), and BAM's duty is P x 0.166 x error (lines 148 to 152), so the robot's kp is the trained kp x P / 32: x 0.94 on the legs, x 0.25 on the head. Track 1 and the gym used x 1 everywhere. With the real gains the 60 N left shove holds 12.53 A on the servo bus for 4 ms instead of 17.19 A (bus sum at 7.2 V), and the 20 s walk covers 1.35 m instead of 1.78 m. Track 3 (real code in the loop) inherits this: the gym walk is not the robot's walk until the gains match.
2. **The policy on the floor.** In fall_traces.py with --keep-policy, the fall hold came back on the 19 ticks between policy steps, so the policy's targets were on for 1 ms in 20. fix_runs.py keeps the policy's last targets on. This is the worst event of all: with the real gains the pack holds 18.60 A for 4 ms and passes 17 A for 9 ms (track 1 had 1 ms), and it trips a board at the low edge of the band (17 A after 4 ms) in 10 of 36 replays. With track 1's gains it would hold 23.4 A for 4 ms on the bus alone.

### Item 1, B47: the spike. FIXED (sim pass only)

The fix is a target guard in the walk loop, fix/bus_budget.py TargetGuard, run once per 50 Hz cycle on the 14 targets:
1. The training's own target speed clip: at most 5.24 rad/s x 0.02 s = 0.105 rad per step (Open_Duck_Playground joystick.py lines 59 and 411 to 416). The stock runtime has this clip commented out (v2_rl_walk_mujoco.py lines 292 to 298), so the robot runs the policy without the clip it was trained with.
2. A bus budget: predict each servo's current from target, angle and speed with the twin's servo law, and if the sum passes 10.0 A, lower one common torque cap until it fits. Servos asking for less than the cap are untouched.
3. Optional: FallHold, the get-up library's fall stop (hold the joint angles once the torso passes 45 deg).

No servo register changes (P stays 30 and 8 in register 21; 48 Torque Limit stays 1000; 28 and 38 stay factory). Track 3 runs it in the real code: where it plugs in is in the module's docstring (the duck's own walkhooks.py wrapper of hwi.set_position_all, with the upstream files unmodified).

Candidates, all with the real gains, the same events (29 fall-stop runs, 9 policy-on-the-floor runs, a 24-push ladder of 10 to 25 N standing and 10 to 15 N walking, and a 20 s walk), servo bus sum at 7.2 V held 4 ms (the gym's quick measure; the pack numbers are further down):

| Fix | Falls, shoves / floor / ladder | Bus held 4 ms, shoves / floor / ladder | Walk 20 s | Verdict |
|---|---|---|---|---|
| none (the real gains) | 28 of 29 / 8 of 9 / 10 of 24 | 12.5 / 17.0 / 12.4 A | 1.352 m | before |
| training clip | same | 10.3 / 11.7 / 12.5 A | 1.353 m | keep |
| budget 11.5 A | same | 10.8 / 11.0 / 11.3 A | 1.352 m, 0 cuts | keep |
| clip + budget 10 A (chosen) | same, same pushes | 9.6 / 9.5 / 10.1 A | 1.353 m, 0 cuts | **chosen** |
| low-pass filter 20 Hz (runtime option; first screen) | 29 of 29 shoves | 7.0 A (shoves) | **0.12 m** | breaks the walk |
| register 48 at 800 (first screen) | as before | 10.2 A (shoves) | **1.227 m (-9 %)** | costs the walk and the get-up torque |
| standing leg gains x 0.7 (first screen) | as before | 7.9 A (shoves) | 1.352 m | weaker stance, not needed |

The guard cuts in no walking step at all, and only in 7 of the shove steps, 22 floor steps and 22 ladder steps. Every kept candidate falls in exactly the same pushes as before, so no fix makes it worse. Found on the way (for the lead, not electrical): the stock policy at our 2652.8 g is easy to topple. Standing, it goes down from 15 N for 0.1 s forward or back and from 20 N to the left, and holds 25 N to the right; walking, it goes down from 15 N forward or back; every 30 N standing push topples it (first screen).

Pack current through the as-built network (bus_events.py, both corners, full and nominal charge; worst of each set):

| Set | Before: pack peak, held 4 ms, over 17 A | After: pack peak, held 4 ms, over 17 A |
|---|---|---|
| 29 fall-stop shoves and the walk | 15.09 A, 14.57 A, 0 ms | 14.00 A, 13.61 A, 0 ms |
| 9 policy on the floor (stock runtime) | **19.62 A, 18.60 A, 9 ms** | 16.60 A, 15.89 A, 0 ms |
| 24-push ladder | (not replayed) | 14.54 A, 14.14 A, 0 ms |
| boards at 17 A after 4 ms that trip | 10 of 156 replays | 0 of 252 replays |

- The hard line holds: no window of 4 ms or more above 17 A anywhere, so a board at the low edge of its band no longer trips.
- The 15 A aim holds everywhere except the policy flailing on the floor at nominal charge (15.2 to 15.9 A in 4 of 36 replays). That replay is conservative: the torque comes from the 7.2 V sim while the BEC sits in dropout at 5.4 V, so the servo current is scaled up, where a real servo's torque would fall with its volts. With FallHold the floor case becomes the fall-stop set: 13.61 A at most.
- Get-ups: unchanged. The guard sits only in the walk loop. The get-up programs peak at 10.22 A of bus sum, so a get-up program that ran through the guard would see it act at its peak; the get-up step (later) checks that.
- The rest of the chain: the lowest servo voltage is 4.25 V (floor case, high-side corner), above the 4.0 V cut. The net bus power dips to -0.97 W in the floor runs (track 1 saw none), a small amount the other servos take.
- TEST_PLAN 3.3: with the guard the twin's worst 4 ms is 15.9 A, under the band's low edge, so any board inside its band (trip at 17 A or more) passes. The 21 A line stays only for a walk without the guard. This saves the second board ($22.99) that a 17 to 21 A board would have needed.

### Item 2: if the BMS trips anyway. RISK left, $0 fixes (calc only)

- The Tenergy 32175 releases an over-current trip on "Cut load", and a short-circuit trip on "Cut short circuit" (product page, BOM line 8, read 2026-11-04). Cycling the panel switch turns the Pololu 2815 off and removes the load, so the board releases. No charger needed. The over-discharge cut (2.40 +/- 0.05 V) releases only at 2.90 +/- 0.10 V, so that one needs the charger.
- When it trips, the switched bus goes to 0 V: the BEC and the 5 V regulator lose their input, and the Pi loses power within the hold-up of their output capacitors (not published). It is a hard power loss: no shutdown.
- The microSD: the guard writes its logs to /home/duck/odm_bench_logs on the root file system (software/odm-walk-guard.service ODM_BENCH_OUT), and journald writes too, so a write can be cut. $0 fix: the read-only root of Raspberry Pi OS (raspi-config, RPi-Distro/raspi-config bookworm aabbd96: do_overlayfs at line 3535, enable_overlayfs lines 3464 to 3495 put overlayroot=tmpfs on the kernel command line; non-interactive `sudo raspi-config nonint do_overlayfs 0`; enable_bootro at line 3519 makes the boot partition read-only), plus the walking logs on a separate small ext4 partition, written on the log's own timer with a flush each second, so a cut loses at most the last second and never the OS.
- Restart: our duck_config has "start_paused": false (software/duck_config.altaay.json line 2), and odm-walk-guard.service starts the walk 10 s after boot. After a trip from a shove the duck is on the floor, so at the next power-on the policy would start flailing there, which is the worst current case above. $0 fix: "start_paused": true, so the runtime holds the start pose until the operator presses A (v2_rl_walk_mujoco.py line 95 and lines 243 to 251). That is a software/ change for the lead.

### Item 3, B49: the drain after the hard stop. RISK left: the $0 path does not exist; the fix needs a part (calc only)

- Pololu's own page for the 2815: "If the physical switch is in the off position, the switch state can also be controlled by a digital signal ... via the ON control pin. Driving the ON pin low (or leaving it disconnected) will leave the switch off; driving the pin beyond approximately 1 V will turn the switch on." The schematic (Pololu file 0J1071) shows why: the panel switch grounds SW, which pulls the MOSFET gates on through R2 (100 kOhm); the ON pin only adds Q3, which pulls SW low too. Nothing on the board can turn it off while SW is grounded, and nothing latches. So a Pi GPIO cannot switch the duck off with the D8 wiring. Rewiring the panel switch so a GPIO could hold it off fails too: when the Pi's own 5 V dies, the pin lets go, the switch comes back on and the Pi boots again.
- The fix with a part (needs Ahmed's OK): Pololu 2813, Big Pushbutton Power Switch with Reverse Voltage Protection, HP, $8.95 (https://www.pololu.com/product/2813). It has the same size and MOSFET ratings as the 2815 (6 A at 55 C, 16 A at 150 C, 90 A max), a latch, and an OFF input: "A high pulse (> 1 V) on this pin turns off the switch (e.g. allowing the target device to shut off its own power)". Off state: under 0.2 uA (HP column). It needs a momentary pushbutton across A and B in place of the panel slide switch, so the body_back cutout needs a button that fits (track 2, assembly).
- Wiring: GPIO26 (pin 37, free in WIRING.md) to OFF, with `dtoverlay=gpio-poweroff,gpiopin=26` (active high, the default). The overlay README (raspberrypi/linux overlays README, gpio-poweroff): "The GPIO starts in an inactive state. At poweroff time it is driven active for 100ms, then inactive for 100ms, then active again." The guard already does low gains for 1 s, torque off, then systemctl poweroff (walk_with_guard.py lines 19 to 20), so the servos are off before the pulse, and the pulse comes after the file systems are unmounted.
- Anticipated: the boot level. OFF acts only above about 1 V. GPIO26 is an input with its pull-down from power-on until the overlay loads, then driven low; active_low is not used (the README says it needs a custom dt-blob and makes a reboot drive the pin), so neither a boot nor a reboot nor a walk can pulse OFF. Only poweroff and halt do. Bench check: a meter on pin 37 through 20 boots and 20 reboots, never above 0.3 V. The pull-down default is from the BCM2835 peripherals data (not read this session), which that check settles.
- Off-state drain and time to 2.5 V: the 2813 off (under 0.2 uA) plus the BMS (10 uA max, Tenergy "current consume in normal operation"), under 10.2 uA, so the 489 mAh left at the hard stop lasts more than 5 years instead of 1.2 to 4.4 hours (the cells' own self-discharge is not counted; it is not in the P30B data we hold). Until then the track 1 rule stays (TEST_PLAN 11: switch off at the panel after a hard stop).

### Item 4, B48: power-on. RISK left, bounded; the fix that holds at any capacitance is ready (calc only)

- The class worst case for the BMS, from TI's BQ2970 protector family data sheet (TI SLUSBU9I, section 4 Device Comparison Table, sections 6.6 and 6.7, read 2026-11-04 from ti.com/lit/ds/symlink/bq2970.pdf): short-circuit detection 0.3 to 0.6 V +/- 0.1 V after 250 us +/- 50 % (so 125 us at the fastest), against discharge over-current 90 to 200 mV +/- 15 mV after 8 to 48 ms +/- 20 %. The lowest short-circuit to over-current ratio in that table is 0.2 V / 0.175 V (BQ29702 at its tolerance edges), so a board whose over-current point is 17 A could see a short circuit from 19.4 A for 125 us.
- The 2815's own turn-on (schematic 0J1071): the panel switch grounds SW and the gates discharge through R2, 100 kOhm, at 84 uA or less, so VSW ramps over Q_gd / 84 uA or longer. The MOSFETs are not named, so Q_gd is not known: power-on is safe if the switched-bus capacitance stays under 19.4 A x t_rise / 8.4 V (for example 230 uF if the ramp were 0.1 ms). The CC BEC Pro's input capacitance is not published either. TEST_PLAN 3.5 stays the check.
- The over-current function can see power-on only through the BEC charging the servo bus: at the BEC's 20 A peak rating it needs more than 11 mF on the servo bus (790 uF per servo) to last 4 ms. A board that passes the 3.3 line (21 A) cannot trip on it at all.
- Ready fix if 3.5 trips or shows more than 17 A (parts, cents, needs Ahmed's OK): a soft start on the 2815, 4.7 kOhm in series with the panel switch lead (P15) and 2.2 uF from the SW pad to VOUT. Current balance at the SW node: the 2.2 uF can carry at most what the 4.7 kOhm pulls, and the SW node stays under VIN while the gates are on (above that the gates turn off), so VOUT rises at about VIN / (4.7 kOhm x 2.2 uF) = 0.81 V/ms or slower, 10 ms or more to 8.4 V, whatever the MOSFET (the gates lag behind R2, so the first fraction of a ms can run faster; calc only). The inrush is then about 0.81 A per mF on both sides of the BEC, under 17 A for up to 20 mF. The on-state gate drive stays at 0.96 x VIN. Turn-off slows to about 0.2 s (84 uA into 2.2 uF), with the MOSFETs carrying the load meanwhile, so switch off with the torque off, as the switch-off rule already says; their pulse rating is not published (not named). With the 2813 of item 3 the same idea needs its own schematic check.

### Item 5: bad signals

- (a) The far servo ground. OK after the twin correction, with a ready lead for more margin (sim pass only). With the real head gains (P 8) and the guard, the head roll offset at the 40 mOhm hop limit is 0.075 V in the fall-stop shoves (track 1: 0.527 V there with the trained head gains; same events, same network) and 0.125 V at most with the floor runs included, against the 0.8 V low threshold: 0.675 V of margin or more. The ready lead: one ground-only conductor, 22 AWG, about 650 mm, from the BEC splice along P13 to the free bus connector of the head roll (fix/gnd_fix.py, like the D23 leg feeds). It takes the head roll to 0.018 V in the shoves and 0.028 V with the floor runs, and to 0.137 V even with the trained head gains (high-side corner 0.897 to 0.186 V), and no servo ground goes below the adapter ground by more than 0.009 V. It needs no buy (BOM lines 21, 22 and 24 have spares) but it is a new wire through the neck joints, so it is a decision, and track 4 checks its motion.
- (b) The bus edges and the turnaround. OK, with one unpublished number. 1 Mbaud (rustypot_position_hwi.py line 77), 1 us per bit. On the Waveshare adapter (schematic, Bus Servo Adapter (A)) U3, the SN74LVC1G126 driver, takes the TX line itself as its input and is enabled through Q1 while TX is low, so every rising edge is driven by U3 until Q1 turns off; R5 (10 kOhm) only holds the idle high. The receiver U4 is off while TX is low and comes back when Q1 lets TXEN fall through R7 (20 kOhm). Our data net is shorter than the stock robot's (2.13 m against 2.44 m, track 1) with the same 14 servos and the same adapter, and the stock robot runs at 1 Mbaud. The STS series has no return-delay register (address 7 is reserved in the STS memory table), so the earliest a servo answers is not published: BLOCKER for the exact turnaround margin. Check: the bus error counters the guard already logs (TEST_PLAN 9).
- (c) The BNO055 on the Pi's I2C. FIX ($0): software I2C by default. The upstream IMU opens the hardware bus at its default speed (raw_imu.py line 21, busio.I2C(board.SCL, board.SDA)); the BCM2835 I2C master "does not support clock stretching at arbitrary points" (elinux.org BCM2835 datasheet errata, p35), and the BNO055 stretches the clock. A third-party build of this robot traced about 25 % bad reads, and backward falls while standing, to this, and 0 % with i2c-gpio (UPSTREAM_ISSUES.md G2). PI_SETUP.md 4b has the i2c-gpio lines but only if glitches show up; make it the default. Check: TEST_PLAN 10.1 on both buses, and the loop time with bench/timing_budget.py, since bit-banged I2C uses CPU.

### Anticipated, not covered by any track yet

1. The servo bus voltage at turn-on of the torque: the runtime turns all 14 servos on at once with low gains, then high gains (rustypot_position_hwi.py turn_on). Nobody has replayed that step. Check: the gym, the start pose from lying on the floor, through bus_events.py.
2. The BEC in dropout at nominal charge: every worst case above has the BEC input at 5.4 V. The CC BEC Pro's dropout and minimum input are not published (B37). Check: TEST_PLAN 4.1 sweep, then rerun bus_events.py with the measured dropout.
3. ESD on carpet with TPU soles into the servo bus and the Pi (track 1: not studied). Check: walk on the lab carpet with the bus error counters and the Pi's kernel log watched.
4. The 5 V rail with the antennas, the eyes and the speaker on at once while the head servos move (the expression features are off for the first walks). Check: TEST_PLAN 4.3 at the 2.4 A peak load with the regulator's output on the scope.
5. The microSD wearing out from the walking logs over months. Check: count the bytes written per session in the walking log.
6. The pushbutton switch of item 3 (if chosen) losing its state on a short pack disconnect (Pololu lists this drawback). Check: bench, a 10 ms break of the pack line while on.
