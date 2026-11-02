# Power path circuit simulation (ngspice, sim pass only)

Run 2026-11-01 (America/New_York) in this session's container with ngspice 42. Star rows and D23 rows added 2026-11-02 from sim/POWER_FIX.md (agent PW). Script: sim/power_path_sim.py. Inputs: per-servo traces from sim/current_budget.py (backlash model walk and the push run, accelerometer bias removed, see SIM_WALK.md note). Outputs (JSON) stayed in the session scratch folder, not in git and not yet on F:.

Why: the lab rule is that electricity is checked before parts are bought or printed. A block diagram cannot show how far the voltage falls at the last servo of a daisy chain during a knee current peak. This model can.

## What is modelled
- 2 cells (OCV per case) with internal resistance, spring holder contacts, Tenergy BMS on the low side, P1/P2/P6/P7/P8/P9/P10/P11/P13 at their CABLE_MAP lengths and gauges, XT30 contacts, the 15 A ATO fuse, the Pololu 2815 switch, the Castle CC BEC Pro (behavioral: 7.2 V, or input minus dropout when the input is too low; input current from output power and efficiency), its two output leads in parallel, the adapter board, then both servo daisy chains hop by hop (kit cable conductor, two connector contacts, the servo board between its two ports) with separate return conductors, and the 5 V branch through the neck to the regulator in the head.
- Each servo is a voltage-limited H-bridge driving the BAM motor model: applied voltage is the policy's command capped at the local bus voltage, motor current (u - kt w) / R, supply current u x I / V_bus, no credit for braking energy, plus a quiescent current. When the bus sags the servo saturates and loses torque, as a real one would.
- Two resistance corners, because several values are not published:

| Parameter | High-side corner | Typical corner | Source |
|---|---|---|---|
| Cell resistance | 20 mOhm | 15 mOhm | ASSUMPTION (P30B datasheet not read in this session) |
| Holder contacts, total | 30 mOhm | 10 mOhm | 30 mOhm = the bench pass limit in POWER.md |
| BMS main loop | 25 mOhm | 25 mOhm | Tenergy spec table (max) |
| Pololu 2815 | 13 mOhm | 13 mOhm | Pololu table (max at 4.5 V gate) |
| Fuse, XT30 contact | 6 mOhm, 1 mOhm | same | ASSUMPTION |
| BEC dropout, efficiency | 0.3 V, 0.85 | same | ASSUMPTION (Castle publishes neither) |
| Mini-SPOX/5264 contact | 20 mOhm | 5 mOhm | ASSUMPTION |
| Kit servo cable conductor | 26 AWG, 150 mm | 24 AWG, 150 mm | ASSUMPTION (Feetech does not publish the gauge) |
| Servo board pass-through | 5 mOhm | 5 mOhm | ASSUMPTION |
| Servo quiescent | 0.05 A | 0.05 A | ASSUMPTION (0.15 A run as an upper bound, see CURRENT_BUDGET.md) |
| 5 V branch | 5 W | 5 W | average with margin (typical 3 W, peak 12 W) |

## Results (6 s of walking, backlash model)
| Case | Bus mean | BEC out mean | Pack current mean / max / RMS | Worst servo: min, mean | Time below 6 V | Time below 4.5 V |
|---|---|---|---|---|---|---|
| Tnkr wiring, full pack (8.4 V OCV), typical | 7.91 V | 7.20 V | 5.2 / 11.2 / 5.5 A | head roll 5.25 V, 6.46 V | 0.49 s | 0 |
| Tnkr wiring, nominal (7.4 V), typical | 6.88 V | 6.56 V | 5.5 / 10.9 / 5.8 A | head roll 4.26 V, 5.80 V | 3.83 s | 0.03 s |
| Tnkr wiring, nominal, high-side | 6.71 V | 6.39 V | 5.6 / 10.2 / 5.8 A | head roll 2.01 V, 4.60 V | 5.94 s | 2.45 s |
| Y-lead at adapter, full, typical | 7.92 V | 7.20 V | 5.1 / 11.0 / 5.4 A | left ankle 5.77 V, 6.81 V | 0.06 s | 0 |
| Y-lead at adapter, nominal, typical | 6.88 V | 6.57 V | 5.4 / 10.7 / 5.7 A | right ankle 4.78 V, 6.18 V | 1.53 s | 0 |
| Y-lead at adapter, nominal, high-side | 6.72 V | 6.41 V | 5.4 / 10.2 / 5.7 A | right ankle 2.92 V, 5.57 V | 4.27 s | 0.48 s |
| Y-lead at adapter, low (6.6 V), typical | 6.07 V | 5.75 V | 5.6 / 10.4 / 5.8 A | right ankle 4.02 V, 5.37 V | 6.0 s | 0.22 s |
| Y-lead at adapter, fall after a push, low, high-side (3 s) | 6.07 V | 5.76 V | 4.3 / 11.1 / 4.5 A | left ankle 2.68 V, 5.15 V | 3.0 s | 0.44 s |
| Star (D15 as built, 22 AWG power leads), full (8.4 V), typical | 7.92 V | 7.20 V | 5.1 / 11.1 / 5.4 A | left ankle 5.99 V, 6.89 V | 0.00 s | 0.00 s |
| Star (D15 as built, 22 AWG power leads), full (8.4 V), high-side | 7.75 V | 7.17 V | 5.2 / 10.6 / 5.5 A | right ankle 4.40 V, 6.48 V | 0.84 s | 0.00 s |
| Star (D15 as built, 22 AWG power leads), nominal (7.4 V), typical | 6.88 V | 6.57 V | 5.4 / 10.8 / 5.7 A | right ankle 5.03 V, 6.25 V | 1.21 s | 0.00 s |
| Star (D15 as built, 22 AWG power leads), nominal (7.4 V), high-side | 6.72 V | 6.41 V | 5.4 / 10.2 / 5.7 A | right ankle 3.44 V, 5.72 V | 3.69 s | 0.32 s |
| Star (D15 as built, 22 AWG power leads), low (6.6 V), typical | 6.07 V | 5.75 V | 5.6 / 10.5 / 5.8 A | right ankle 4.23 V, 5.44 V | 6.00 s | 0.10 s |
| Star (D15 as built, 22 AWG power leads), low (6.6 V), high-side | 5.90 V | 5.58 V | 5.6 / 10.0 / 5.8 A | right ankle 2.71 V, 4.91 V | 6.00 s | 1.19 s |
| Star (D15 as built, 22 AWG power leads), fall after a push, low (6.6 V), high-side (3 s) | 6.07 V | 5.76 V | 4.2 / 11.1 / 4.5 A | left ankle 3.07 V, 5.28 V | 3.00 s | 0.29 s |

Star rows: sim/POWER_FIX.md (2026-11-02), same 6 s window and trained-mass trace as the rows above.

D23 rows (second feeds SP4 and SP5), from the sim/POWER_FIX.md options table: walk 10 to 16 s, worse of the trained-mass trace and the 2.77 kg build model of that run (before D22), time under 6.0 V counted as time. Row 6+3b is the 3S pack that D23 holds until the TEST_PLAN 9 walking log.

| # | Change | Worst ankle minimum (V): nominal typ / high; low typ / high | Ankle time under 6.0 V (%): nominal typ / high; low typ / high | Cost (new purchases) | Added mass, where | Verdict |
|---|---|---|---|---|---|---|
| 1 | Baseline: D15 star as built (SP leads 22 AWG) | 5.03 / 3.44; 4.23 / 2.71 | 23.9 / 67.0; 100 / 100 | $0 | 0 | fails |
| 3b | Second feed into each ankle's free BUS 1 port | 5.72 / 5.35; 4.96 / 4.57 | 5.8 / 20.5; 100 / 100 | $0 (BOM spares) | +11.7 g, belly to ankle | typical corner only; build now |
| 6+3b | 6 + 3b | 6.89 / 6.78; 6.89 / 6.78 | 0 / 0; 0 / 0 | as 6 | as 6, plus 11.7 g on the legs | **passes with margin: recommended (D22)** |

In the 6+3b row "(D22)" is POWER_FIX.md's proposal number; the decision that holds it is D23 (D22 is the light print profile).

With the Y-lead, the head roll servo never goes below 4.5 V at a nominal pack in either corner (it does for 2.45 s out of 6 s on the Tnkr wiring at high-side resistances). One run (Tnkr, low pack, high-side) stopped after 2.8 s in ngspice; its numbers are left out of the table.

## What this means (decisions in DECISIONS.md)
1. Parts are fine on current: pack RMS about 5.8 A, peaks about 11 A, switch about 0.4 W. Tenergy (10 A working, 22 +/- 5 A trip), the 15 A fuse and 16 AWG all have margin.
2. The BEC only regulates near full charge. Under load the pack sags about 0.8 V (cells, holder, BMS, wires, switch), so from mid-charge down the BEC passes its input through and the servos see about 6.4 to 6.6 V at nominal and 5.6 to 5.8 V at 3.3 V per cell. The policy was trained for 7.4 V. Stop walking and charge at about 3.5 V per cell under load (about 7.0 V at the pack). In that range the servo Present Voltage tracks the pack, so check_voltage.py works as a battery reading there; above about 7.5 V it only shows 7.2 V.
3. D14: the neck chain gets its own Y-lead from the adapter. Hanging it off the left ankle (Tnkr wiring) puts the 4 neck servos behind 5 leg hops that carry the left leg's knee peaks. (Superseded by D15, the star wiring as built: star rows above.)
4. Superseded by sim/POWER_FIX.md: the 22 AWG leg leads do not fix it (19 to 22 %); a second feed into each ankle's free BUS 1 port does in the typical corner (6 %), and only a regulated bus plus that feed passes both corners (3S pack, held by D23 until the TEST_PLAN 9 walking log). Earlier text: the leg chains sag at their far end (ankles) during knee peaks, 25% of the time below 6 V in the typical corner, 71% in the high-side corner; the gate is the TEST_PLAN.md hop measurement and walking log.
5. A lower-resistance pack (spot-welded 2S with 16 AWG leads instead of the spring holder) raises every number above by about 0.1 to 0.2 V at walking current. The bench holder test in POWER.md decides it.

## Limits
- Sim pass only. Resistances in the table are partly assumptions; the two corners bracket them. The servo electronics, brown-out threshold and the real BEC dropout are not published.
- Servo loads come from the sim model of the servo, which issue #48 shows can differ from real servos (register 85, firmware, see UPSTREAM_ISSUES.md G1).
- No capacitance on the bus (servo boards and the adapter have some); real dips will be a little shorter than here.
