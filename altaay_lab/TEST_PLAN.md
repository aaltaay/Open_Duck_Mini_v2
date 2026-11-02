# TEST_PLAN: electrical and mechanical checks before and at first power-up

Written 2026-11-01 6:55 PM ET by the Claude Code agent (DECISIONS.md D8 to D15). Nothing has been built or bought; this is the plan for when parts arrive. Every step has a pass/fail value. Where a number comes from a simulation, the test is there to replace the simulated value with a measured one (sim/CURRENT_BUDGET.md, sim/POWER_PATH_SIM.md, both sim pass only).

Rules: never connect or disconnect a cable with power on (upstream issue 49: bus errors; Bulk Man style warning applies to every robot). First power always from a current-limited bench supply, never the pack. Log every measured value in a new history/ file.

## 0. Equipment
| Item | Why | Status |
|---|---|---|
| Digital multimeter with continuity beep and 10 A range | every step below | not in the BOM yet (BOM.md "Not costed") |
| Bench DC supply, 0 to 15 V, at least 5 A, current limit | staged power-up, BEC and regulator tests, Kelvin resistance | not in the BOM yet |
| Digital calipers | coupon checks (print/PRINT_PLAN.md), connector fit | not in the BOM yet |
| Windows 10 PC with Castle Link V4 (BOM L2) | set the BEC to 7.2 V; also the Feetech tool for servo firmware | Ahmed's PC |
| Power resistors or an electronic load, about 1 ohm 50 W | BEC and holder load tests | not in the BOM yet |

## 1. Before any power: mechanical checks of every made cable
For each made lead in CABLE_MAP.md (P rows, the servo first leads SP1 to SP3, the data Y, D rows):
1. Crimp pull: each Molex 08-70-1040 terminal holds when pulled by hand along the wire (no slip) and sits latched in the housing (a light push on the wire does not move it back). Fail: redo the crimp.
2. Connector fit: plug every made lead into the real servo port and adapter socket it goes to; it must seat fully and latch. Fail: wrong housing or terminal.
3. Heat shrink covers every solder joint and splice with no copper showing.
4. Length: route each cable on the printed parts with every joint it crosses at both limits (CABLE_MAP length rule). Fail: tension at a limit.

## 2. Before any power: continuity and polarity, every wire
Use the generated checklist audit/continuity_checklist.csv (one row per wire, from wiring/netlist.yaml by audit/erc.py; the netlist passes the electrical rule check with 0 errors, audit/ERC_REPORT.md): for every wire, beep from its "from" pin to its "to" pin, and check there is no beep to the pins listed in its last column.
- Pass: continuity under 1 ohm for every wire; no continuity (over 1 Mohm) between any two different nets on the same connector (V+, GND, DATA on every 3-pin servo lead; P+ and P- everywhere).
- Polarity: on every servo lead the pin order matches the STS3215 port (GND, VCC, DATA per the Feetech sheet); on the BEC output, red is +; on the XT30, + to +.
- Pack bus to ground with the switch ON and nothing powered: over 1 kohm after the capacitors charge from the meter (no short).
- Adapter H1 screw terminal: not connected to anything (D15).

## 3. Battery, holder and BMS (bench, robot not connected)
1. Cells: both P30B within 0.05 V of each other before they go in (the Tenergy board does not balance).
2. Holder drop: 10 A through the holder (bench supply in current limit into a 1 ohm load, or a load test), measure across the holder contacts. Pass: under 0.3 V total and no contact gets warm in 30 s (POWER.md). This replaces the 10 to 30 mOhm holder value in the power sim.
3. BMS: P+ to P- equals the pack voltage; P- side opens when the pack is shorted through a 15 A fuse and a 0.5 ohm resistor for under 1 s (over-current detect 22 +/- 5 A after 8 +/- 4 ms per Tenergy). If no load is available, skip and rely on the fuse.
4. Charge once with the USB-C charger and the robot off: both cells end within 0.05 V of each other and at no more than 4.20 V each.

## 4. Power parts one at a time (bench supply)
1. Castle CC BEC Pro: program 7.2 V with Castle Link. No load: 7.20 V +/- 0.10 V. Input sweep 8.4, 7.6, 7.2, 7.0, 6.5 V at 2 A load: write down the output each time. This measures the dropout the power sim assumed (0.3 V). 10 minutes at 5 A on the bench, no airflow: case under 60 C.
2. Pololu 2815: on-board slide OFF, control switch wired. Switch on: VOUT within 0.1 V of VIN at 5 A. Switch off: VOUT 0 V.
3. 5 V regulator: input 6.0 and 8.4 V; output 5.00 +/- 0.15 V at no load and at 2.4 A for 1 minute.
4. Fuse holder: fuse fitted, under 10 mOhm across the holder (Kelvin method below).

## 5. Kelvin resistance of one servo hop (decides D15 follow-up)
Pass 2.0 A from the bench supply through the V+ conductor of one kit cable hop, servo board to servo board (cable plus both contacts plus one servo board pass-through), and measure the voltage across it with the meter leads on the servo pins, not on the supply leads. R = V / 2.0 A. Repeat for GND.
- Power sim corners: typical about 35 mOhm per conductor per hop, high-side about 65 mOhm.
- Gate: if a hop is over 40 mOhm per conductor, plan 22 AWG made leads for the leg hops (BOM contingency X1/X2) before the full assembly.

## 6. Servo bus adapter (USB only, D15)
Waveshare adapter on the Pi USB, H1 not powered, jumper on B. Pass: /dev/ttyACM0 appears; scripts/check_motors.py finds a single servo powered from the bench supply through its own power lead. This confirms the adapter logic runs from USB VBUS (schematic) with the servo power bypassing it.

## 7. First servo (test order TO1)
Bench supply at 7.4 V, limit 3 A, servo alone.
1. configure_motor.py with the ID it will have; then read back registers 41, 44, 46, 84, 85, 86 and the firmware version. Pass: 85 = 0 (UPSTREAM_ISSUES.md G1), firmware written down.
2. No-load speed: a 2 rad step and a 1.5 Hz 0.4 rad sine (SERVO_DEEP_DIVE.md section 6). Pass: about 5 rad/s or more at 7.4 V.
3. Thermal (D2): hold 1.5 Nm for 10 minutes at 7.2 V, read Present Temperature every 10 s. Pass: at least 10 C under the servo's Max Temperature Limit register.
4. Note: the servo cuts its torque after more than 2 A for 2 s by default (Feetech spec via the parts check). Do not mistake this for a fault.

## 8. Staged power-up of the assembled robot (bench supply in place of the pack, at the XT30)
1. 7.4 V, limit 1 A, torque off: idle current under 0.6 A (Pi plus 14 x 6 mA servo idle). All 14 servos answer check_motors.py with the right IDs.
2. Limit 3 A, torque on, robot hanging, holding the zero pose: under 1.5 A.
3. find_soft_offsets.py with the robot hanging (Runtime issue 32: it moves every joint at once).
4. Limit 8 A: a short walk with the robot hanging.

## 9. Walking log on the floor (validates the power sim)
Pack at full charge (8.3 V or more) and again at nominal (about 7.4 V open circuit). Log Present Voltage and Present Current of all 14 servos at 50 Hz for 60 s of walking, plus any bus checksum errors.
- Pass: no servo under 4.5 V at any time; no ankle under 6.0 V for more than 10% of the walk at nominal; no checksum errors.
- Compare with sim/POWER_PATH_SIM.md (Y/star wiring, typical corner: worst ankle 5.0 V minimum, under 6 V about 20% of the time at nominal). If the real numbers are worse than the high-side corner, stop and fix the wiring before more walking.

## 10. IMU
1. 1000 reads with the robot still: no single read jumps (UPSTREAM_ISSUES.md G2; if it does, move the BNO055 to software I2C, dtoverlay=i2c-gpio).
2. Tilt test with scripts/calibrate_imu.py: pitch nose down gives the sign the policy expects (B20).

## 11. Battery cut-off (software, needed because the BMS cuts only at 2.40 V per cell)
- Stop walking and go to the dock (later lab step) at about 3.5 V per cell under load, about 7.0 V at the pack. In this range the BEC is in dropout, so servo Present Voltage reads about the pack voltage minus the path drop.
- Hard stop (torque off, shut down the Pi) at servo Present Voltage 6.0 V, about 3.3 V per cell. The Molicel P30B minimum is 2.5 V; the Tenergy board would only cut at 2.40 V.
- For the docking step, add a pack voltage and current monitor on the pack line (later, not in the stock build).

## 12. Foot switches (D17)
- Before power: each foot circuit (2 switches in parallel) reads under 1 ohm closed and open over 1 Mohm, at the Pi header.
- Powered, robot hanging: scripts/fc_test.py (Runtime) shows each foot change state on every press; 200 presses per foot with no missed or stuck reading.
- On the floor, standing still: both feet read "contact" for 60 s without a flicker. A flicker here goes straight into the policy observation.
