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
