# TEST_PLAN: electrical and mechanical checks before and at first power-up

Written 2026-11-01 6:55 PM ET by the Claude Code agent (DECISIONS.md D8 to D15). Nothing has been built or bought; this is the plan for when parts arrive. Every step has a pass/fail value. Where a number comes from a simulation, the test is there to replace the simulated value with a measured one (sim/CURRENT_BUDGET.md, sim/POWER_PATH_SIM.md, both sim pass only).

Updates (details in history/): 2026-11-01 about 10:10 PM ET, test equipment TE1 to TE4, 3.2 and 3.3 on the electronic load, 7.3 by current, step 8.0 (sourcing pass); about 10:55 PM ET, bench scripts named per step (software/SOFTWARE.md); 2026-11-02 about 12:05 AM ET, final docs pass: D23 bench gates in 3.2, 4.1, 4.2, 5 and 9 (sim/POWER_FIX.md), foot_side test fit 1.5, hip yaw limit 8.2a, exit code 10 in 11; about 12:35 AM ET, 8.0 weight 2.64 kg after D22 (sim/MASS_BUDGET.md).

Rules: never connect or disconnect a cable with power on (upstream issue 49: bus errors; Bulk Man style warning applies to every robot). First power always from a current-limited bench supply, never the pack. Log every measured value in a new history/ file.

## 0. Equipment
| Item | Why | Status |
|---|---|---|
| Digital multimeter with continuity beep, 10 A range and a 400 mV DC range | every step below; the "under 1 ohm" and "over 1 Mohm" passes are read as numbers on the ohms range (section 2) | BOM TE1 (Klein MM420), if not on hand |
| Bench DC supply, 0 to 15 V, 8 A, current limit | inputs in section 4, the Kelvin tests (4.4, 5), sections 6 to 8 (8.4 runs at an 8 A limit) | BOM TE2 (Siglent SPD1168X, 0 to 16 V, 0 to 8 A), if not on hand |
| Digital calipers | coupon checks (print/PRINT_PLAN.md), connector fit | BOM TE3 (iGaging 100-700-06), if not on hand |
| Windows 10 PC with Castle Link V4 (BOM L2) | set the BEC to 7.2 V; also the Feetech tool for servo firmware | Ahmed's PC |
| DC electronic load, constant current to at least 27 A and 200 W, with program steps | 3.2 and 3.3 from the pack; the load on the outputs in 4.1 to 4.3 | BOM TE4 (Siglent SDL1020X-E: 150 V, 30 A, 200 W), if not on hand |
| Two kitchen scales | mass and centre of mass, step 8.0 | not in the BOM (household) |

Which source runs each test:
- Bench supply (TE2): the inputs in 4.1 to 4.3, the 2.0 A Kelvin tests (4.4, 5) and sections 6, 7 and 8. It stops at 8 A, so it cannot run 3.2.
- Electronic load (TE4): 3.2 and 3.3 from the pack, and the load on the outputs in 4.1 to 4.3.
- Neither: sections 1, 2 and 3.1 need only the meter; 3.4 charges through the USB-C charge board (BOM 11) fed from BOM T7 and T7b; section 9 runs on the pack.

Without TE4, power resistors on a heat sink can stand in for 3.2 and 4.1 to 4.3 (2 x 1.5 ohm and 1 x 2.0 ohm, 100 W each, SOURCING_2026-11-02.md section 4, price UNVERIFIED). The current then follows V / R at each step and is read on TE1 (10 A range, 10.00 A at most). Nothing on this list replaces TE4 in 3.3.

## 1. Before any power: mechanical checks of every made cable
For each made lead in CABLE_MAP.md (P rows, the servo power leads SP1 to SP5, the data Y, D rows):
1. Crimp pull: each Molex 08-70-1040 terminal holds when pulled by hand along the wire (no slip) and sits latched in the housing (a light push on the wire does not move it back). Fail: redo the crimp.
2. Connector fit: plug every made lead into the real servo port and adapter socket it goes to; it must seat fully and latch. Fail: wrong housing or terminal.
3. Heat shrink covers every solder joint and splice with no copper showing.
4. Length: route each cable on the printed parts with every joint it crosses at both limits (CABLE_MAP length rule). Fail: tension at a limit.
5. Ankle plugs at foot_side (cables3d/CABLES_3D.md; HARDWARE_AUDIT B33): on the first printed foot_side (the left leg prints first) with the TO1 servo, plug a kit cable into BUS 2 and an SP4 housing (V and G only) into BUS 1, then turn the ankle through its range with the foot flat. In CAD the plug back sits 0.5 to 1.7 mm from the foot_side apex and the SP4/SP5 route touches foot_side. Pass: no plug body or wire presses on foot_side. Fail: a 2 mm relief at the foot_side apex (CAD change) before the other plates print.

## 2. Before any power: continuity and polarity, every wire
Use the generated checklist audit/continuity_checklist.csv (one row per wire, from wiring/netlist.yaml by audit/erc.py; the netlist passes the electrical rule check with 0 errors, audit/ERC_REPORT.md): for every wire, measure from its "from" pin to its "to" pin, and check there is no connection to the pins listed in its last column.
- Read every pass as a number in ohms, not by the beep: the TE1 meter (Klein MM420) beeps for anything under 50 ohm, so a beep cannot show "under 1 ohm" and silence cannot show "over 1 Mohm". Use the resistance setting (press SEL once from continuity), touch the probe tips together first and subtract that reading. Its lowest range, 400.0 ohm, reads in 0.1 ohm steps at +/-(1.2 % + 5 digits), about +/-0.5 ohm near zero (Klein MM420 manual, https://data.kleintools.com/sites/all/product_assets/documents/instructions/klein/MM420%20Instructions_web.pdf, read 2026-11-01 9:52 PM ET).
- Pass: under 1 ohm for every wire; over 1 Mohm between any two different nets on the same connector (V+, GND, DATA on every 3-pin servo lead; P+ and P- everywhere).
- Polarity: on every servo lead the pin order matches the STS3215 port (GND, VCC, DATA per the Feetech sheet); SP4 and SP5 carry V and G only, data cavity empty (D23); on the BEC output, red is +; on the XT30, + to +.
- Pack bus to ground with the switch ON and nothing powered: over 1 kohm after the capacitors charge from the meter (no short).
- Adapter H1 screw terminal: not connected to anything (D15).

## 3. Battery, holder and BMS (bench, robot not connected)
1. Cells: both P30B within 0.05 V of each other before they go in (the Tenergy board does not balance).
2. Holder drop: 10.0 A through the holder for 30 s, from the pack (BMS fitted, P+ and P-) into the electronic load (TE4) in constant current: 74 to 84 W at 7.4 to 8.4 V, under its 200 W. The bench supply cannot run this step (TE2 stops at 8 A). 10 A is the Tenergy board's rated operational current ("10A or less"), well under its trip. Measure across the holder contacts. Pass: under 0.10 V total (10 mOhm) and no contact gets warm in 30 s. The section 9 gate needs the typical pack side (sim/POWER_FIX.md: with a 30 mOhm holder the ankle is under 6.0 V 17.7 % of the walk at nominal even with the second feed). Also read the voltage at the Pololu 2815 output at 10 A: pack open circuit minus that reading under 0.95 V (95 mOhm cells to switch). This replaces the 10 to 30 mOhm holder value in the power sim.
3. BMS: P+ to P- equals the pack voltage. Then the over-current trip, on the electronic load (TE4) only, after step 2 passes. Tenergy spec table (BOM line 8 link, read 2026-11-01 9:57 PM ET): over-current detection 22 +/- 5 A, so 17 to 27 A; detection delay 8 +/- 4 ms; release condition "Cut load"; main loop 25 mOhm max.
   - Pack at 7.40 V or less, open circuit, so 27 A stays inside the load's 200 W input rating (200 W / 27 A = 7.41 V). Above that the load's over-power protection (OPP, 210 W) can cut the current, which would look like a BMS trip. If the pack reads higher, discharge it on TE4 at 2 A and read it again after 5 minutes off the load.
   - Circuit: P+ through the fuse holder with a 15 A fuse (L3 with L4) to TE4 +, P- to TE4 -.
   - TE4 in Program (auto test) mode, CC, 30 A range, Stop On Fail on, 7 steps: 15, 17, 19, 21, 23, 25 and 27 A. Each step: Ton 0.05 s (load on), Tdly 0.03 s (when the load reads the voltage, after the longest 12 ms detect delay), Toff 2 s (load off), pass band 1.0 to 8.5 V. The sense is inverted: a failed step means the voltage collapsed, so the BMS opened at that current.
   - Pass: the 15 A step passes and the run stops on a step from 17 to 27 A; write down that current. Fail: it trips at 15 A, or all 7 steps pass (no trip at 27 A).
   - Heat: each step lasts 50 ms. Even if the BMS never trips, the 27 A step puts about 0.9 J into its 25 mOhm loop (27 A x 27 A x 0.025 ohm x 0.05 s) and at most 10 J into the load (7.4 V x 27 A x 0.05 s), so nothing gets hot.
   - After the run: disconnect the load (the release condition) and check P+ to P- is back at the pack voltage. Read the fuse in ohms (under 1 ohm, as in section 2); if it opened, the run does not count: fit a new fuse and repeat.
   - Load specs used here, read 2026-11-01 9:53 PM ET: 30 A range, 200 W input power, OPP 210 W, 0.9 V minimum operating voltage at 30 A (SDL1000X datasheet DS0801X-E01F, https://siglentna.com/wp-content/uploads/dlm_uploads/2024/05/SDL1000X_DataSheet_DS0801X-E01F.pdf); Program steps with Ton and Toff 0.01 to 100 s, Tdly 0.01 s to Ton, the pass band in volts in CC mode, and Stop On Fail (SDL1000X user manual E02A, https://siglentna.com/wp-content/uploads/dlm_uploads/2024/06/SDL1000X_UserManual_E02A.pdf). Both are listed on https://siglentna.com/resources/documents/dc-electronic-load/; the product page in BOM TE4 is https://siglentna.com/product/sdl1020x-e/.
   - Without TE4, skip the trip test and rely on the fuse. Do not short the pack through a resistor: the current would depend on cell and contact resistances nobody has measured, so no resistor value is sure to pass 27 A, and if the BMS failed only the fuse would end the short.
4. Charge once with the USB-C charger and the robot off: both cells end within 0.05 V of each other and at no more than 4.20 V each.

## 4. Power parts one at a time (bench supply in, electronic load out)
The bench supply (TE2) feeds each part's input with its current limit on (8 A at most); the electronic load (TE4) in constant current is the load on the output.
1. Castle CC BEC Pro: program 7.2 V with Castle Link. No load: 7.20 V +/- 0.10 V. Input sweep 8.4, 7.6, 7.2, 7.0, 6.5 V at 2 A on TE4: write down the output each time. This measures the dropout the power sim assumed (0.3 V). Dropout pass: output at least input minus 0.30 V at 7.0 V in and 6 A out (sim/POWER_FIX.md: 0.6 V of dropout takes the ankle from 5.8 to 20.9 % under 6.0 V with the second feed). 10 minutes at 5 A on TE4, no airflow: case under 60 C.
2. Pololu 2815: on-board slide OFF, control switch wired. Switch on: VOUT within 0.1 V of VIN at 5 A on TE4. Switch off: VOUT 0 V. Then 10 minutes at 6.0 A (TE4), switch on its seat with the foam tape: board under 50 C. Reason: with D23 the sim pack RMS current is 5.94 to 6.05 A, 99 to 101 % of its 6 A rating at 55 C (sim/POWER_FIX.md). Over 50 C: add a second 2815 in parallel below the first (40.8 mm free below the seat in CAD).
3. 5 V regulator: input 6.0 and 8.4 V; output 5.00 +/- 0.15 V at no load and at 2.4 A on TE4 for 1 minute.
4. Fuse holder: fuse fitted, under 10 mOhm across the holder (Kelvin method below: TE2 at 2.0 A, no load).

## 5. Kelvin resistance of one servo hop (decides D15 follow-up)
Pass 2.0 A from the bench supply through the V+ conductor of one kit cable hop, servo board to servo board (cable plus both contacts plus one servo board pass-through), and measure the voltage across it with the meter leads on the servo pins, not on the supply leads. R = V / 2.0 A. Repeat for GND.
- Power sim corners: typical 27.6 mOhm per conductor per hop, high-side 65.1 mOhm (sim/POWER_FIX.md).
- Gate: 40 mOhm per conductor with the second feeds SP4/SP5 on a 2S pack (sim: the ankle gate holds to about 60 mOhm); 100 mOhm with a 3S bus (held by D23). Without the second feeds no hop value passes section 9 (15.4 % at 17.6 mOhm).
- 22 AWG made leads (BOM contingency X1/X2) cut the ankle time under 6 V by only 2 to 5 points: use them if the kit cables fail the B17 length test fit, not for voltage.

## 6. Servo bus adapter (USB only, D15)
Waveshare adapter on the Pi USB, H1 not powered, jumper on B, one servo powered from the bench supply through its own power lead. Pass: /dev/ttyACM0 appears (USB 1a86:55d3) and bench/first_servo_check.py --steps 6 finds exactly one servo (check_motors.py only addresses the 14 joint IDs; a new servo is ID 1). This confirms the adapter logic runs from USB VBUS (schematic) with the servo power bypassing it.

## 7. First servo (test order TO1)
Bench supply at 7.4 V, limit 3 A, servo alone.
1. configure_motor.py with the ID it will have; then read back registers 41, 44, 46, 84, 85, 86 and the firmware version. Pass: 85 = 0 (UPSTREAM_ISSUES.md G1), firmware written down. Use bench/first_servo_check.py --configure ID --fix-config; power-cycle and re-read register 85 (the stock configure script can lose writes, software/SOFTWARE.md section 3).
2. No-load speed: a 2 rad step and a 1.5 Hz 0.4 rad sine (SERVO_DEEP_DIVE.md section 6). Pass: about 5 rad/s or more at 7.4 V.
3. Thermal (D2): fix the servo horn against a rigid stop and command a position past it so that Present Current reads 1.5 A (the knee walking RMS current in the backlash model, sim/RUNTIME_THERMAL.md) at 7.2 V. Log Present Temperature, Present Current and Present Voltage every 10 s for 30 minutes, or until the temperature rises less than 0.5 C per minute; write down the room temperature and read the Max Temperature Limit register once. Compute the thermal resistance and time constant as in sim/RUNTIME_THERMAL.md. Pass: the predicted knee temperature after 31 minutes of continuous walking (3.7 W plain model and 5.8 W backlash model) is at least 10 C below both the Max Temperature Limit register and the 70 C over-temperature cut of the C001 spec. If the servo cuts its torque during the hold, write down when and at what temperature. If the servo unloads (2 A protection), repeat at a lower current and record the C/s rise rate.
4. Note: the servo cuts its torque after more than 2 A for 2 s by default (Feetech spec via the parts check). Do not mistake this for a fault.

## 8. Staged power-up of the assembled robot (bench supply in place of the pack, at the XT30)
0. Mass and centre of mass, before the first walk (sim/ADDED_MASS_SIM.md finding 2). Before any power, weigh the assembled robot: expected 2.64 +/- 0.05 kg with the D22 print profile (2.70 kg if the D22 coupon gate fails; sim/MASS_BUDGET.md). The centre of mass needs the robot holding its home pose, so find it once steps 1 to 3 pass and before step 4: powered at the step 2 settings (7.4 V, limit 3 A, torque on), supply leads slack, both toes on one kitchen scale and both heels on a second one (centre of mass x from the load split and the contact spacing), or the trunk balanced on an edge. Expected: about 1 mm ahead of the ankle servo axes (3 mm in the trained model; sim/MASS_BUDGET.md). If it is more than 4 mm behind the ankle axes, move rear parts forward before any walk (the BEC Pro and the USB slack coil are the heaviest movable ones; sim/ADDED_MASS_SIM.md table 7).
1. 7.4 V, limit 1 A, torque off: idle current under 0.6 A (Pi plus 14 x 6 mA servo idle). All 14 servos answer check_motors.py with the right IDs.
2. Limit 3 A, torque on, robot hanging, holding the zero pose: under 1.5 A.
2a. Hip yaw limit, before step 3 and for every manual move: keep both hip yaws within +/-20 deg. Screws F198 and F211 touch body_middle_bottom past 21.7 deg (D19); the walk uses at most 10.4 deg (VERIFICATION.md C11). Nothing in the Runtime clamps hip yaw: find_soft_offsets.py (376de65) sends every joint to zero plus its offset, and the offset is wherever the hand left the joint. So in step 3 the robot hangs and one hand holds the hip yaw, a hip yaw is turned by hand no more than 20 deg from zero, and any hip yaw offset over 0.35 rad gets the answer n.
3. find_soft_offsets.py with the robot hanging (Runtime issue 32: it moves every joint at once), with the 2a limit.
4. Limit 8 A: a short walk with the robot hanging.

## 9. Walking log on the floor (validates the power sim; decides the 3S pack held by D23)
Pack at full charge (8.3 V or more) and again at nominal (about 7.4 V open circuit), with the second feeds SP4 and SP5 fitted (D23). Log Present Voltage and Present Current of all 14 servos for 60 s of walking, plus any bus checksum errors.
- Pass: no servo under 4.5 V at any time; no ankle under 6.0 V for more than 10 % of the walking time at nominal, counted in time: read Present Voltage on a timer that is not a multiple of the 20 ms control period (for example every 27 ms), because a 50 Hz read locked to the control loop reads anywhere from 10 to 34 % for 21 to 24 % of the time (sim/POWER_FIX.md); no checksum errors.
- Record, and make it a pass line once the 3S pack is decided: median servo voltage (5 s mean) while walking at nominal, at least 7.0 V (a 2S build cannot meet it: the sim reads 6.3 to 6.6 V with the second feeds). Log the forward speed (distance in 20 s) at full and at nominal charge: a drop of more than 15 % means the servo voltage limits the walk (sim: 2S with the BEC in dropout walks at 65 to 79 % of the 7.4 V speed, a regulated 7.2 V bus at 83 to 93 %).
- Compare with sim/POWER_FIX.md option 3b (D23), nominal pack: typical corner worst ankle 5.72 V, under 6 V 5.8 % of the time (23.9 % without the second feeds); high-side 5.35 V, 20.5 %. If the real numbers are worse than the high-side corner, stop and fix the wiring before more walking. If the ankle gate fails at nominal, the 3S plan (sim/POWER_FIX.md option 6) goes to Ahmed (D23).
- Log with bench/power_log.py --walk. The 30 % and 34 % of the star replay (software/SOFTWARE.md section 8) are 50 Hz samples taken in phase with the control updates; weighted by time the same replay gives 21 % (24 % on the 2.77 kg model of that run). A 25 Hz log (--decimate 2) is also locked to the 20 ms period. power_log.py --walk reads once per control cycle, so its "% of samples" is a phase sample, not time: it needs a read on its own timer before this gate is scored (bench owner).

## 10. IMU
1. 1000 reads with the robot still: no single read jumps (UPSTREAM_ISSUES.md G2; if it does, move the BNO055 to software I2C, dtoverlay=i2c-gpio).
2. Tilt test: run scripts/calibrate_imu.py from scripts/, then bench/imu_check.py --tilt. Pass: pitch nose down gives the sign the policy expects (B20). calibrate_imu.py only calibrates and saves the offsets (software/SOFTWARE.md section 2).

## 11. Battery cut-off (software, needed because the BMS cuts only at 2.40 V per cell)
- Stop walking and go to the dock (later lab step) at about 3.5 V per cell under load, about 7.0 V at the pack. In this range the BEC is in dropout, so servo Present Voltage reads about the pack voltage minus the path drop.
- Hard stop (torque off, shut down the Pi) at servo Present Voltage 6.0 V while standing, about 3.3 V per cell at light load, or 5.4 V while walking. The Molicel P30B minimum is 2.5 V; the Tenergy board would only cut at 2.40 V.
- Implemented in bench/battery_guard.py, run inside the walk by bench/walk_with_guard.py. Walk stop rule (DECISIONS.md D16 note): the 5 s mean of the 14-servo median Present Voltage at or under 6.0 V while walking (about 3.57 V per cell, sim pass only); hard stop on the 3 s mean at or under 6.0 V standing or the 2 s mean at or under 5.4 V walking. Check it with battery_guard.py --monitor and a bench supply sweep (software/SOFTWARE.md section 9).
- Exit code 10 from bench/walk_with_guard.py (also power_log.py): after a stop, Torque Enable (register 40) did not read 0 on every servo, so torque could not be confirmed off (bench/odm_bench/walkhooks.py hard_stop). Treat the servos as live: hold the robot, switch off at the panel switch (D8: it cuts the switched pack bus) and find the cause before the next walk. The JSON report (item 11.torque_off) gives the register 40 read-back of every servo.
- For the docking step, add a pack voltage and current monitor on the pack line (later, not in the stock build).

## 12. Foot switches (D17)
- Before power: each foot circuit (2 switches in parallel) reads under 1 ohm closed and open over 1 Mohm, at the Pi header (read in ohms, as in section 2).
- Powered, robot hanging: bench/feet_check.py --presses 200 (never fc_test.py: it starts the walk and the OpenAI client) shows each foot change state on every press; 200 presses per foot with no missed or stuck reading.
- On the floor, standing still: both feet read "contact" for 60 s without a flicker. A flicker here goes straight into the policy observation.
