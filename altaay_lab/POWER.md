# POWER: servo regulator, fuse and battery path (lab change D3)

Decision (Ahmed, 2026-11-01 1:09 PM ET, answers D3): add a regulator so the servos never see more than 7.4 V.
Prices and stock checked 2026-11-01 (America/New_York). Nothing bought.
Update 2026-11-01 about 6:25 PM ET (DECISIONS.md D8, D10): current sizing now comes from the sim current budget (sim/CURRENT_BUDGET.md, sim pass only) instead of estimates; BMS is now the Tenergy 32175; a Pololu 2815 MOSFET switch carries the main current and the stock panel switch only controls it. Sections 2, 5, 6 and 7 below.

## 1. Requirement
- Input: 2S Li-ion, 6.0 V (empty) to 8.4 V (full).
- Output: 7.2 to 7.4 V, never above 7.4 V (STS3215 C001 rating 6 to 7.4 V; Feetech excludes over-voltage from warranty).
- Load: 14x STS3215 C001 on one bus. Since D15 the servo power goes from the BEC to belly splices and one lead per chain; the Waveshare adapter only carries data.
- Below about 7.3 to 7.5 V of pack voltage the output may simply follow the input. That is acceptable (servos still in their 6 V minimum range).

## 2. Current sizing (sim pass only, sim/CURRENT_BUDGET.md)
Servo bus current at 7.4 V from the stock walk policy in the upstream MuJoCo model, converted with the BAM motor model the actuators were fitted from (worst of three kt values, statistics after the first 2 s):

| Case | Mean | Worst 1 s | Worst 100 ms | Worst 2 ms |
|---|---|---|---|---|
| Stand still | 0.19 A | 0.22 A | 0.24 A | 0.24 A |
| Walk forward 0.15 m/s | 2.15 A | 2.25 A | 3.15 A | 5.06 A |
| Turn 1.0 rad/s | 2.35 A | 2.54 A | 3.56 A | 7.63 A |
| Walk, backlash model | 3.19 A | 3.41 A | 4.78 A | 8.61 A |
| Fall (push run) | | | 6.55 A | 10.61 A |

Re-run without the upstream accelerometer bias (sim/SIM_WALK.md note): within 5% of the table above. ngspice power-path model (sim/POWER_PATH_SIM.md): pack 5.1 to 5.7 A mean, 10 to 11 A peak while walking.
Pack side at 7.4 V (regulator efficiency 0.85 assumed): walking about 4.2 A mean (at most 6.6 A with a 150 mA per servo electronics allowance), worst 100 ms about 7.5 A (at most 9.9 A), falls up to about 17 A for 20 ms with every allowance stacked at a low pack. The old estimate (4 to 8 A out walking, 15 to 20 A peaks) was high by about 2 x for walking.
Real servos may draw more than the model (gear friction, issue #48). Until a bench log of Present Current exists, parts keep at least 2 x margin on the sim walking numbers.
Stall case unchanged: 14 x 2.67 A = 37 A if every servo jams; the BMS over-current trip (17 to 27 A) and the fuse cover it.

## 3. Candidates checked
| Part | Output | Current | Price, seller | Verdict |
|---|---|---|---|---|
| Castle Creations CC BEC Pro, P/N 010-0004-01 (UPC 899598001717) | adjustable 4.8 to 12.5 V (default 5.1 V), set to 7.2 V | 20 A peak; 15 A continuous at 2S to 4S (16 V) input, rated with 5 mph airflow | $54.95, castlecreations.com (Olathe, KS); store shows available | CHOSEN |
| Pololu D42V110F7 (#5674) | fixed 7.57 V +/-3% (up to about 7.8 V) | 7 to 14 A | $69.95, pololu.com (Las Vegas, NV) | Rejected: above 7.4 V, cannot be trimmed down |
| Pololu D42V110F6 (#5673) | fixed 6 V | about 11 A | pololu.com | Fallback only: complies but servos run slower than the 7.4 V sim |
| Pololu D24V150F7 (#2883) | fixed 7.5 V +/-4% | 15 A | $79.95, listed "Rationed" | Rejected: above 7.4 V |
| Pololu D36V50F7, D42V55F7 | fixed 7.5 V | 5 A class | pololu.com | Rejected: above 7.4 V, too small |
| Pololu custom voltage | any | any | needs contacting Pololu | Not done (no messages allowed) |
| Castle CC BEC 2.0 WP, 010-0153-00 | 6.25 to 8.5 V adjustable | 9 A continuous, 15 A peak | $56.95, castlecreations.com | Backup. Minimum input voltage not verified for 2S. |

Why the CC BEC Pro:
- It is the only US brand, US sold, full-spec part found that can be set at or below 7.4 V and still delivers about 15 A continuous and 20 A peaks.
- 7.2 V gives 0.2 V margin under the 7.4 V cap for setpoint tolerance and transients (Castle does not publish setpoint accuracy, so measure it).
- Castle warranty: one year from date of purchase (user guide P/N 095-0047-00 and product pages). Castle also has a non-warranty replacement program.
- Size 43 x 33 x 24 mm, 29 g without wires (user guide).
- Origin: current Castle pages say "Assembled in the Philippines", designed in Olathe, Kansas. The 2009 guide says components from USA, Mexico and China.

Limits and how we handle them:
- The 15 A continuous rating assumes 5 mph airflow. Inside the duck there is none. Our 4 to 8 A walking load leaves about 2x margin. Mount it against the body wall with an air gap and check its temperature after 10 minutes of walking.
- Output comes on two 3-pin servo leads, each good for 5 A continuous (Castle guide). Cut both, join red to red and black to black, and run 16 AWG to the adapter screw terminal.
- Setting 7.2 V needs the Castle Link V4 USB Programming Kit (011-0173-00, $29.95, Windows 10 or later, Castle Link 2 software, "compatible with ALL Castle Linkable devices"). We do not have a Windows PC on the box. The CC BEC Pro is powered at 5 V or more while it is programmed.
- Dropout below the setpoint: not published by Castle. Expected behavior for a buck is that the output tracks the input minus a small drop. Not verified. Measure the output with the pack at 7.0 V and 6.5 V on a bench supply.
- Stock: castlecreations.com store data says available on 2026-11-01, but an older Castle page said "temporarily out of stock". Not verified until checkout.

## 4. Fuse
- Fuse: Littelfuse ATO 15 A, 32 V, P/N 0287015.PXCN (current part; replaces 0257015.PXPV). About $0.45 each (DigiKey shows about EUR 0.39; DigiKey blocks our fetches, so the US price is not verified).
- Holder: Littelfuse FHAC0001ZXJ, inline ATO holder, 20 A, 32 V, 16 AWG leads. $7.74 at Newark (stock not verified).
- Place it right after BMS P+, before the switch, so it protects the BMS, the switch and the whole harness.
- Why 15 A: walking continuous pack current is about 5 to 9 A; ATO fuses carry 110% indefinitely and open at 135% only after 0.75 to 600 s, so 20 A bursts lasting a fraction of a second pass. A sustained jam (above about 20 A) or a short opens it. 15 A also matches the XT30 rating (15 A) and stays under the BMS 20 A claim.

- With the Tenergy BMS (D10, over-current detect 22 +/- 5 A) the BMS opens first on a hard over-current; the 15 A fuse is the backup for a BMS MOSFET that fails short and protects the 16 AWG harness. 20 ms fall peaks (sim, at most about 17 A) are far below the fuse's opening time at that current.

## 5. BMS and holder (issue #51)
Issue #51 (https://github.com/apirrone/Open_Duck_Mini/issues/51) asks whether the spring 2x18650 holder and thin wires bottleneck 14 servos, and about 8.4 V on 7.4 V servos.
- Cells: Molicel P30B is rated 30 A continuous. Not a bottleneck.
- BMS (D10, 2026-11-01 about 6:20 PM ET): Tenergy P/N 32175 2S protection board, https://power.tenergy.com/protection-circuit-module-pcb-for-7-2v-7-4v-2s-li-ion-battery-pack-working-10a-cutoff-22a-ntc , $22.99, "in stock" 2026-11-01. Spec table on that page: over-charge detect 4.280 +/- 0.025 V, over-discharge about 2.40 +/- 0.05 V (exact rows in the sourcing check, BOM.md line 8), rated operational current 10 A or less, over-current detection 22 +/- 5 A, main loop resistance 25 mOhm max, 10 uA max own consumption, 10k 3380 NTC, size 34 x 16 x 4.5 mm. The page shows no cell balancing ("/" in the balance rows), so keep the two cells matched (same batch) and check the cell voltages at each charge for the first 10 charges. Fits the measured upstream BMS envelope 17.75 x 47.2 x 5.33 mm (MOUNTING.md). Replaces the JZK 8 A board (no datasheet) and the AITRIP 20 A board (does not fit).
- Holder: spring contacts have no published current rating. Measure the drop across the holder at 10 A on the bench. If it is over about 0.3 V, or the springs get warm, replace it with a spot-welded 2S pack with nickel strip and 16 AWG leads. The sim walking mean (about 4 A) is well under that test current.
- Wires: 16 AWG silicone on every power run (WIRING.md).
- Over-voltage: solved by the regulator above.

## 6. Main switch (D8, clears B22)
- The body_back cutout only fits the small stock panel slide switch, and no switch that small has a published 15 A DC rating. So the switch no longer carries the current.
- Pololu 2815 Big MOSFET Slide Switch with Reverse Voltage Protection, HP (https://www.pololu.com/product/2815, $8.49, status "Rationed (Active and Preferred)", backorders allowed, US made in Las Vegas): 4.5 to 32 V operating, 13 mOhm at 4.5 V and 8.6 mOhm at 10 V (combined MOSFET resistance), 6.0 A heats the MOSFETs to 55 C and 16 A to 150 C (at 12 V, 22 C ambient, still air), 90 A maximum, 0.8 x 1.0 x 0.16 in, 2.7 g.
- Control: Pololu: "To use an alternate SPST switch to control the MOSFETs, set the on-board slide switch to the off position and connect the alternate switch between ground and the switch control terminal". The stock panel switch does that, so it carries microamps.
- Order: after the fuse, before the bus node, so the fuse also protects the switch. Charging is wired on BMS P+/P- before the XT30 and works with the robot off.
- Heat at the sim walking mean (about 4.2 A at the pack): about 0.2 W in the MOSFETs, well under the 55 C point. Mount it on the battery bay front wall with foam tape (MOUNTING.md), not touching the BEC.

## 7. 5 V branch (D4, D8)
- The HENGE UBEC (no datasheet) is replaced by an in-stock Pololu 5 V step-down (BOM line 9), mounted on the head floor below the Pi.
- It is fed from the switched pack bus through the neck with a 20 AWG pair (P13). At 12 W peak this is about 1.9 A at 7.4 V in the neck, instead of 2.4 A at 5 V, and voltage drop in the neck wires no longer reaches the Pi directly.
- Loads on the Pi 5 V rail: Pi Zero 2 W, 2 x SG90 antenna servos, MAX98357A amp, camera. Peak about 2.4 A (CABLE_MAP.md P13), typical about 0.6 A.

## 8. Servo power distribution (D15, 2026-11-01 6:48 PM ET)
- Parts check: the Waveshare Bus Servo Adapter (A) schematic marks "MAX:6A" next to servo header H3, all servo current would pass its screw terminal and an AO4407 MOSFET, and Waveshare specifies 9 to 12.6 V input (we supply 7.2 V). The ngspice model shows BEC output peaks of 8.3 to 9.1 A while walking.
- So the servo power bypasses the adapter: BEC output (both leads joined) -> 16 AWG -> V+ and GND splices in the belly -> SP1 (left leg, ID 20), SP2 (right leg, ID 10), SP3 (neck, ID 30), 22 AWG because the Molex 08-70-1040 terminal takes 22 to 28 AWG. The adapter feeds only DATA and GND; H1 is not connected; its logic runs from USB VBUS (schematic). Bench check in TEST_PLAN.md section 6.
- Effect in the power sim at a nominal pack: worst ankle 5.04 V minimum (typical corner) instead of 4.78 V, head servos at 5.0 V or more in both resistance corners.
- Note 2026-11-03 (sim pass only): those are open-loop replay dips of the D15 star before the D23 feeds (as wired now: sim/POWER_PATH_SIM.md 'As built'); the closed-loop twin (twin/electromech/ELECTROMECH_TWIN.md) finds smaller dips and a slower walk at a nominal pack instead (TEST_PLAN 9).

## 9. BEC at low input (D16)
- Castle does not publish the CC BEC Pro minimum input voltage, and Motion RC lists "16V to 40V" while Castle's table rates it at 2S to 4S. Its behavior below the 7.2 V setpoint (pass-through, or shut-off) is not verified.
- TEST_PLAN.md section 4 sweeps the input from 8.4 V down to 6.5 V on the bench before assembly. If it shuts off, use the Pololu D42V110F6 (6 V fixed, about 11 A, section 3) and accept slower servos.
- Battery: the Tenergy board cuts only at 2.40 V per cell (P30B minimum 2.5 V), so the software stops walking at about 3.5 V per cell under load and shuts down at servo Present Voltage 6.0 V (TEST_PLAN.md section 11).

## 10. The Pi 3.3 V rail after the V1 freeze (2026-11-06 ET, D51, D54; calc only)
The new I2C parts draw from the Pi 3V3 pins 1 and 17 (the touch boards and the ToF have their own regulators, fed 3.3 V).

| load | current | source |
|---|---|---|
| BNO055 (normal power, fusion running) | 12.3 mA | [I] Bosch BNO055 datasheet BST-BNO055-DS000 (the figure is not re-read in this session: check) |
| 2 x SPH0645LM4H mics | 2 x 0.6 mA | [R] Knowles SPH0645LM4H-B Rev B (COMPANION.md 11.2) |
| 2 x MPR121 boards | 2 x 0.03 mA chip at 16 ms sampling, plus each board's regulator and the IRQ LED when touched (about 1 mA, not published) | [R] NXP MPR121 rev 4 via the expression study; LED: BLOCKER (board, not published) |
| VL53L4CD cliff ToF | 22 mA typ, 24 mA max while ranging; VCSEL peak 40 mA; plus the board's power LED (cut the LED jumper to save it) | [R] ST DS13812 Rev 3 Table 12; [R] Adafruit guide (LED jumper) |
| foot pull-ups R4, R5 | 2 x 1.5 mA with both feet down | D17 |
| I2C pull-ups (Pi 1.8 k and 4 x 10 k in parallel, about 1.05 k) | up to 3.2 mA while a line is low | calc only |
| total | about 45 mA typical, about 62 mA with the ToF peak | calc only |

The Pi Zero 2 W 3.3 V pin current limit is not in its product brief: BLOCKER (read the Raspberry Pi documentation, or measure the rail with the parts on, TEST_PLAN). If the rail is short, the touch boards and the ToF take 5 V on their Vin instead (both accept 3 to 5 V and shift the I2C levels themselves), which moves about 25 mA from the 3.3 V rail to the U3 5 V branch (3.4 A rating). The 5 V branch total moves by under 0.1 A either way (calc only).

## 11. 3S pack, BEC set to 12.0 V (2026-11-13, D63)

Supersedes the 7.2 V set point in sections 1 and 3 for the 3S rail. Supersedes the 16 V pass-through used in the first 3S walks. Sections 1 to 9 stay as the 2S record. Do not delete them.

- Set point 12.0 V. Cited output range 4.8 V to 12.5 V (section 3) and 4.9 V to 12.5 V (Castle chart, twin/battery/BATTERY_STUDY.md). 16 V is outside both. 12.0 V is inside both.
- Pack domain about 9.0 V to 12.6 V (3 times 3.0 V to 3 times 4.2 V, calc only). The P45B cut-off is 2.5 V per cell, so 7.5 V is the sheet floor. The domain starts at 9.0 V. U3 VIN uses this domain. The Pololu D30V30F5 input cited in the netlist is 5 V to 45 V, so 9.0 V to 12.6 V is inside it.
- When the pack is under 12 V the BEC cannot hold 12.0 V. The minimum input and the behavior below the set point are not published (BLOCKER). The sim still uses a 0.3 V dropout assumption. In that model the output regulates only when the BEC input is at least 12.3 V (calc only, 12.0 + 0.3). A full pack is 12.6 V, so only the top of the charge regulates. The rest of the discharge is pass-through in the sim, or a shut-off on the real part. Do not treat 12.0 V as held for the whole walk.
- The 2S protection board and the 2S charger are still the parts drawn in the netlist. They do not cover 12.6 V. That open item is problems/STS12.md. D61 was not edited.
- Any power-design change has to pass `python3 altaay_lab/verify/check_power_limits.py` before it is used in a sim.
