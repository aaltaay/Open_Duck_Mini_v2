# BOM_FULL: every part in the robot

Generated 2026-11-05 01:28 UTC by altaay_lab/viewer/make_viewer_data.py --write-bom (module viewer/bom_full.py). Do not edit by hand: change the sources (CAD, print/parts.csv, wiring/netlist.yaml, fasteners/fasteners.json, BOM.md) and re-run.

One row per distinct item that goes into the robot or is used to build it. Qty is what the robot uses (measured in the CAD, the netlist or the fastener schedule). The Line column is the BOM.md purchase line that supplies it, so prices and links live in one place (BOM.md). The exploded 3D view shows every row that is modelled (tab "Every part").

Status: bought = a BOM.md line buys it and covers the quantity; in kit = ships with another bought item; printed = from the filament lines; made = made from wire and connectors; tool = used to build; SHORT = the line buys less than the robot uses; MISSING = no purchase line; CHECK = counts disagree.

| Section | Rows | Pieces | Status |
|---|---|---|---|
| Printed parts | 37 | 54 | printed 37 |
| Servos | 17 | 44 | bought 15, in kit 2 |
| Electronics and power | 18 | 23 | bought 18 |
| Expression (head) | 7 | 12 | bought 7 |
| Fasteners | 22 | 374 | bought 13, in kit 9 |
| Cables | 48 | 48 | bought 2, in kit 11, made 35 |
| Connectors and wire | 17 | 69 | bought 16, in kit 1 |
| Consumables and other | 12 | 130 | bought 12 |
| Tools | 22 |  | tool 22 |
| **All** | 200 | 754 | bought 83, in kit 23, printed 37, made 35, tool 22 |

## Needs action (0)

None: every row is covered by a purchase line, a kit, the filament or the tool list.

## Printed parts

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P01 | Battery pack lid | print/battery_pack_lid.stl, PLA, light (base), 13.6 g, 1.01 h each | 1 | Trunk | 27 | Amazon | printed | 2 walls 15 % (upstream default): a lid whose screws thread into body_back; no rule asks for more |
| P02 | Body back | print/body_back.stl, PLA, rings (base + 5 pilot rings), 78.4 g, 6.46 h each | 1 | Trunk | 27 | Amazon | printed | 2 walls 15 % plus a 1.5 mm solid ring round each of its 5 screw pilots (lid and electronics screws): the pilot rule at each hole instead of 3 walls on the whole shell; no coupon |
| P03 | Body front | print/body_front.stl, PLA, light (base), 57.9 g, 4.03 h each | 1 | Trunk | 27 | Amazon | printed | 2 walls 15 % (upstream default): no rule asks for more |
| P04 | Body middle bottom | print/body_middle_bottom.stl, PLA, rings (base + 8 insert rings), 103.1 g, 8.61 h each | 1 | Trunk | 27 | Amazon | printed | 2 walls 15 % plus a 2.0 mm solid ring round each of its 8 insert bores (horizontal in this orientation): the insert rule at each bore; waits for the S1 gate (C2aL C2bL C3L): if a light coupon fails it prints with 4 walls (insert) and no rings |
| P05 | Body middle top | print/body_middle_top.stl, PLA, rings (base + 8 insert rings), 74.4 g, 6.61 h each | 1 | Trunk | 27 | Amazon | printed | 2 walls 15 % plus a 2.0 mm solid ring round each of its 8 insert bores: the insert rule at each bore; waits for the S1 gate (C2aL C2bL C3L): if a light coupon fails it prints with 4 walls (insert) and no rings |
| P06 | Eye bulb | print/bulb.stl, PLA, light (base), 2.0 g, 0.17 h each | 2 | Head 2 | 27 | Amazon | printed | 2 walls 15 % (upstream default); guide says x1 but the CAD has 2 (issue #26) |
| P07 | Flash light module | print/flash_light_module.stl, PLA, light (base), 8.4 g, 0.80 h each | 1 | Head | 27 | Amazon | printed | 2 walls 15 % (upstream default); its 4.0 mm hole is a 14.6 mm light channel and not an insert bore |
| P08 | Flash reflector interface | print/flash_reflector_interface.stl, PLA, light (base), 2.3 g, 0.24 h each | 1 | Head | 27 | Amazon | printed | 2 walls 15 % (upstream default): no rule asks for more |
| P09 | Foot bottom plate | print/foot_bottom_pla.stl, PLA, rings (base + 2 insert rings), 9.8 g, 0.78 h each | 2 | Left foot, Right foot | 27 | Amazon | printed | 2 walls 15 % plus a 2.0 mm solid ring round each of its 2 blind insert bores 5.8 mm (C3): the insert rule at each bore; waits for the S1 gate (C2aL C2bL C3L): if a light coupon fails it prints with 4 walls (insert) and no rings |
| P10 | Foot sole (TPU) | print/foot_bottom_tpu.stl, TPU, light (base), 17.6 g, 2.18 h each | 2 | Left foot, Right foot | 28 | Amazon | printed | TPU 2 walls 40 % (upstream infill; B26): no strength rule for the sole; coupon T2 is the left leg sole and checks fit |
| P11 | Foot side | print/foot_side.stl, PLA, light (base), 13.7 g, 1.14 h each | 2 | Left foot, Right foot | 27 | Amazon | printed | 2 walls 15 % (upstream default): no rule asks for more |
| P12 | Foot top | print/foot_top.stl, PLA, rings (base + 2 insert rings), 24.0 g, 2.09 h each | 2 | Left foot, Right foot | 27 | Amazon | printed | 2 walls 15 % plus a 2.0 mm solid ring round each of its 2 insert bores (the 1.5 mm bore wall of B16 prints solid either way): the insert rule at each bore; waits for the S1 gate (C2aL C2bL C3L): if a light coupon fails it prints with 4 walls (insert) and no rings |
| P13 | Head shell | print/head.stl, PLA, heavy (insert), 262.0 g, 21.96 h each | 1 | Head | 27 | Amazon | printed | 4 walls (insert) as before D22: 12 insert bores and a bearing seat (horizontal in this orientation); in the sim its mass is the forward counterweight (a light head costs one step of backward margin; MASS_STUDY.md option d) |
| P14 | Head bot sheet | print/head_bot_sheet.stl, PLA, light (base), 56.9 g, 3.83 h each | 1 | Head | 27 | Amazon | printed | 2 walls 15 % (upstream default): a 3 mm floor sheet |
| P15 | Head pitch to yaw | print/head_pitch_to_yaw.stl, PLA, heavy (neck), 16.6 g, 1.73 h each | 1 (+1 spare) | Neck | 27 | Amazon | printed | 5 walls 40 % (neck) as before D22: neck chain (G5); thinnest part at head_pitch and head_yaw (G6) |
| P16 | Head roll mount | print/head_roll_mount.stl, PLA, heavy (neck+fit), 15.7 g, 1.42 h each | 1 (+1 spare) | Head | 27 | Amazon | printed | 5 walls 40 % and fit (neck+fit) as before D22: neck chain (G5); servo pocket line to line (0.00 mm net) |
| P17 | Head yaw to roll | print/head_yaw_to_roll.stl, PLA, heavy (neck+fit), 29.1 g, 2.81 h each | 1 (+1 spare) | Neck | 27 | Amazon | printed | 5 walls 40 % and fit (neck+fit) as before D22: neck chain (G5); servo pocket 0.10 mm undersize (C4) |
| P18 | Knee to ankle left sheet | print/knee_to_ankle_left_sheet.stl, PLA, heavy (wall3+fit), 7.0 g, 0.64 h each | 4 (+1 spare) | Left shin, Left thigh, Right shin, Right thigh | 27 | Amazon | printed | 3 walls and fit (wall3+fit) as before D22: thinnest leg plate (G6); servo tabs line to line (0.01 mm) |
| P19 | Knee to ankle right sheet | print/knee_to_ankle_right_sheet.stl, PLA, heavy (wall3+fit), 6.3 g, 0.60 h each | 4 (+1 spare) | Left shin, Left thigh, Right shin, Right thigh | 27 | Amazon | printed | 3 walls and fit (wall3+fit) as before D22: thinnest leg plate (G6); servo tabs line to line (0.01 mm) |
| P20 | Left antenna holder | print/left_antenna_holder.stl, PLA, heavy (wall3), 3.6 g, 0.28 h each | 1 (+1 spare) | Head | 27 | Amazon | printed | 3 walls (wall3) as before D22: thinnest part (2.0 mm); first hit if the head swings (G6) |
| P21 | Left leg cover | print/left_cache.stl, PLA, light (base), 57.3 g, 4.95 h each | 1 | Left thigh | 27 | Amazon | printed | 2 walls 15 % (upstream default): a cover (PRINT_PLAN.md G6: not spared) |
| P22 | Left eye | print/left_eye.stl, PLA, heavy (wall3), 1.8 g, 0.18 h each | 1 | Head | 27 | Amazon | printed | 3 walls (wall3) as before D22: 4 screw pilots; whole-part test print T1 (B14) in this profile |
| P23 | Left roll to pitch | print/left_roll_to_pitch.stl, PLA, light (fit), 21.2 g, 2.09 h each | 1 | Left hip bracket | 27 | Amazon | printed | 2 walls 15 % with fit: servo pocket line to line (0.10 mm face overlap); G12 check; no rule asks for more walls |
| P24 | Leg spacer | print/leg_spacer.stl, PLA, rings (base + 4 insert rings), 7.2 g, 0.85 h each | 4 | Left shin, Left thigh, Right shin, Right thigh | 27 | Amazon | printed | 2 walls 15 % plus a 2.0 mm solid ring round each of its 4 insert bores (2 per end): the insert rule at each bore; waits for the S1 gate (C2aL C2bL C3L): if a light coupon fails it prints with 4 walls (insert) and no rings |
| P25 | Neck left sheet | print/neck_left_sheet.stl, PLA, heavy (neck), 7.5 g, 0.70 h each | 1 (+1 spare) | Neck | 27 | Amazon | printed | 5 walls 40 % (neck) as before D22: neck chain (G5); thin sheet at neck_pitch and head_pitch (G6) |
| P26 | Neck right sheet | print/neck_right_sheet.stl, PLA, heavy (neck), 6.5 g, 0.61 h each | 1 (+1 spare) | Neck | 27 | Amazon | printed | 5 walls 40 % (neck) as before D22: neck chain (G5); thin sheet at neck_pitch and head_pitch (G6) |
| P27 | Right antenna holder | print/right_antenna_holder.stl, PLA, heavy (wall3), 3.6 g, 0.28 h each | 1 (+1 spare) | Head | 27 | Amazon | printed | 3 walls (wall3) as before D22: thinnest part (2.0 mm); first hit if the head swings (G6) |
| P28 | Right leg cover | print/right_cache.stl, PLA, light (base), 57.2 g, 4.95 h each | 1 | Right thigh | 27 | Amazon | printed | 2 walls 15 % (upstream default): a cover (PRINT_PLAN.md G6: not spared) |
| P29 | Right eye | print/right_eye.stl, PLA, heavy (wall3), 4.6 g, 0.38 h each | 1 | Head | 27 | Amazon | printed | 3 walls (wall3) as before D22: 4 screw pilots |
| P30 | Right roll to pitch | print/right_roll_to_pitch.stl, PLA, light (fit), 21.2 g, 2.12 h each | 1 | Right hip bracket | 27 | Amazon | printed | 2 walls 15 % with fit: servo pocket line to line (0.10 mm face overlap); G12 check; no rule asks for more walls |
| P31 | Roll motor bottom | print/roll_motor_bottom.stl, PLA, heavy (wall3), 8.8 g, 0.72 h each | 2 (+1 spare) | Left hip, Right hip | 27 | Amazon | printed | 3 walls (wall3) as before D22: thinnest hip part (2.97 mm median) at hip yaw and hip roll; G12 screw (G6) |
| P32 | Roll motor top | print/roll_motor_top.stl, PLA, light (fit), 7.1 g, 0.73 h each | 2 | Left hip, Right hip | 27 | Amazon | printed | 2 walls 15 % with fit: servo pocket line to line (0.01 mm); no rule asks for more walls |
| P33 | Speaker interface | print/speaker_interface.stl, PLA, light (base), 2.3 g, 0.22 h each | 1 | Head | 27 | Amazon | printed | 2 walls 15 % (upstream default); laid flat (PRINT_CHECK had it on a 48 mm2 edge) |
| P34 | Speaker stand | print/speaker_stand.stl, PLA, heavy (wall3), 10.1 g, 1.16 h each | 1 | Head | 27 | Amazon | printed | 3 walls (wall3) as before D22: 2 screw pilots |
| P35 | Trunk bottom frame | print/trunk_bottom.stl, PLA, heavy (insert+fit), 42.0 g, 3.54 h each | 1 | Trunk | 27 | Amazon | printed | 4 walls and fit (insert+fit) as before D22: frame part; both legs hang from its 2 hip yaw 6804 seats 32.19 mm (C1); 6 insert bores |
| P36 | Trunk top frame | print/trunk_top.stl, PLA, heavy (wall3+fit), 75.1 g, 6.14 h each | 1 | Trunk | 27 | Amazon | printed | 3 walls and fit (wall3+fit) as before D22: frame part that holds the 2 hip yaw servos and the neck pitch servo; 3 servo pockets line to line (0.10 mm face overlap) |
| P37 | Antenna rod (optional) | URDF antenna.stl, PLA, 1.8 g for 2 (print/PRINT_PLAN.md optional part) | 2 | Head 2 | 27 | Amazon | printed | In the CAD but not in print/: export from the URDF mesh (PRINT_PLAN.md) |

## Servos

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| S01 | Feetech STS3215 C001, ID 10, right hip yaw | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Trunk | 1 | Seeed Studio | bought |  |
| S02 | Feetech STS3215 C001, ID 11, right hip roll | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Right hip | 1 | Seeed Studio | bought |  |
| S03 | Feetech STS3215 C001, ID 12, right hip pitch | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Right hip bracket | 1 | Seeed Studio | bought |  |
| S04 | Feetech STS3215 C001, ID 13, right knee | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Right thigh | 1 | Seeed Studio | bought |  |
| S05 | Feetech STS3215 C001, ID 14, right ankle | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Right shin | 1 | Seeed Studio | bought |  |
| S06 | Feetech STS3215 C001, ID 20, left hip yaw | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Trunk | 1 | Seeed Studio | bought |  |
| S07 | Feetech STS3215 C001, ID 21, left hip roll | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Left hip | 1 | Seeed Studio | bought |  |
| S08 | Feetech STS3215 C001, ID 22, left hip pitch | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Left hip bracket | 1 | Seeed Studio | bought |  |
| S09 | Feetech STS3215 C001, ID 23, left knee | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Left thigh | 1 | Seeed Studio | bought |  |
| S10 | Feetech STS3215 C001, ID 24, left ankle | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Left shin | 1 | Seeed Studio | bought |  |
| S11 | Feetech STS3215 C001, ID 30, neck pitch | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Trunk | 1 | Seeed Studio | bought |  |
| S12 | Feetech STS3215 C001, ID 31, head pitch | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Neck | 1 | Seeed Studio | bought |  |
| S13 | Feetech STS3215 C001, ID 32, head yaw | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Neck | 1 | Seeed Studio | bought |  |
| S14 | Feetech STS3215 C001, ID 33, head roll | 7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1) | 1 | Head | 1 | Seeed Studio | bought |  |
| S15 | Servo horn, drive side | comes with each STS3215 (BOM line 1) | 14 | Head, Left hip, Left hip bracket, Left shin, Left thigh, Neck 2, Right hip, Right hip bracket, Right shin, Right thigh, Trunk 3 | 1 | Seeed Studio | in kit |  |
| S16 | Servo horn, idle side | comes with each STS3215 (BOM line 1) | 14 | Head, Left hip, Left hip bracket, Left shin, Left thigh, Neck 2, Right hip, Right hip bracket, Right shin, Right thigh, Trunk 3 | 1 | Seeed Studio | in kit |  |
| S17 | SG90-class antenna servo | Miuzei 9 g, lead 250 mm; tab and horn screws from its bag | 2 | Head 2 | 14 | Amazon (Miuzei) | bought |  |

## Electronics and power

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| E01 | Li-ion cell, Molicel INR18650-P30B | 18650, 3.0 Ah, 2 in series | 2 | Trunk 2 | 6 | 18650 Battery Store | bought |  |
| E02 | 2 x 18650 series holder with leads | holder leads used for P1 and P2 if 120 mm or longer | 1 | Trunk | 7 | Amazon | bought |  |
| E03 | 2S protection board (BMS) | Tenergy P/N 32175 2S protection board (board marking RYD-02S-032) | 1 | Trunk 2 | 8 | Tenergy (Fremont, CA) | bought |  |
| E04 | USB-C 2S charge board | USB-C 2S charger board, Adeept B0BJTW4QBR (BOM 11) | 1 | Trunk | 11 | Amazon (Adeept) | bought |  |
| E05 | XT30U connector pair (mated) | Amass XT30U pair (BOM 12), female on the pack side, male on the robot side | 1 | Trunk | 12 | Amazon | bought |  |
| E06 | Main power switch, Pololu 2815 | Pololu 2813 Big Pushbutton Power Switch with Reverse Voltage Protection, HP (D30, was the 2815 slide switch; same size and MOSFET ratings; button on A and B, GPIO26 on OFF) | 1 | Trunk | 10 | Pololu (Las Vegas, NV) | bought |  |
| E07 | Control switch (panel slide switch) | stock panel switch in the body_back cutout (CAD power_switch.stl, upstream Amazon B0CH3JCQM5; BOM 10b) | 1 | Trunk | 10b | myMectronic (DigiKey stock) | bought |  |
| E08 | Servo regulator, Castle CC BEC Pro at 7.2 V | Castle Creations CC BEC Pro, P/N 010-0004-01, set to 7.2 V | 1 | Trunk | L1 | Castle Creations; also Horizon Hobby CSE010000401 and Motion RC | bought |  |
| E09 | Servo bus adapter, Waveshare (A) | Waveshare Bus Servo Adapter (A), SKU 25514 | 1 | Trunk | 2 | Waveshare | bought |  |
| E10 | 5 V regulator, Pololu D30V30F5 | Pololu D30V30F5 5 V 3.4 A step-down regulator (item 4892) | 1 | Head | 9 | Pololu (Las Vegas, NV) | bought |  |
| E11 | Raspberry Pi Zero 2 W | Raspberry Pi Zero 2 W | 1 | Head | 3 | Adafruit 5291 | bought |  |
| E12 | IMU, Adafruit BNO055 2472 | Adafruit BNO055 breakout 2472 | 1 | Trunk | 5 | Adafruit 2472 | bought |  |
| E13 | Inline fuse holder, Littelfuse FHAC0001ZXJ | ATO 20 A holder, 16 AWG leads | 1 | Trunk | L3 | Newark 56P4171 | bought |  |
| E14 | Fuse, Littelfuse 0287015.PXCN ATO 15 A | sits in the L3 holder | 1 | battery bay | L4 | DigiKey | bought |  |
| E15 | microSD card, SanDisk Ultra 32 GB | in the Pi | 1 | head | 4 | Amazon | bought |  |
| E16 | Foot contact switch, Omron SS-01 (SS-10 fallback) | Omron SS-01 (SS-10 fallback) microswitch, left foot, slot 1 | 4 | Left foot 2, Right foot 2 | 13 | DigiKey | bought |  |
| E17 | Foot switch pull-up, 2.2 kOhm 1/4 W | 2.2 kOhm 5 % 1/4 W resistor, Adafruit 2782 (BOM 13b), left foot pull-up | 2 | head | 13b | Adafruit 2782 | bought |  |
| E25 | Game controller, Xbox Wireless (Bluetooth) | off-robot: the Runtime drives the walk from it | 1 |  | 15 | Microsoft Store (also Walmart, Best Buy) | bought |  |

## Expression (head)

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| E18 | 1 W LED bead (2 eyes, 1 projector) | 1 W LED bead (BOM E3), left eye | 3 | Head 3 | E3 | Amazon (uxcell) | bought |  |
| E19 | LED resistor, 100 ohm 1/4 W | 100 ohm 1/4 W resistor (BOM E3b), left eye | 3 | head | E3b | SparkFun PRT-14493 | bought |  |
| E20 | I2S amplifier, Adafruit MAX98357A | Adafruit MAX98357A I2S amplifier 3006 | 1 | Head | E2 | Adafruit | bought |  |
| E21 | Speaker, Same Sky CMS0361KLX | Same Sky CMS0361KLX speaker, 36.1 mm square, 14.5 mm deep, 8 ohm, 2 W | 1 | Head 3 | E1 | DigiKey 102-1304-ND | bought |  |
| E22 | Raspberry Pi Camera Module 3 | Raspberry Pi Camera Module 3, Adafruit 5657 | 1 | Head | E6 | Adafruit 5657 | bought |  |
| E23 | Eye glass disc, 29.6 x 1.85 mm | one per eye (not modelled) | 2 |  | E4 | Amazon (FINGERINSPIRE) | bought |  |
| E24 | Projector reflector, Aurorad S5 20 x 15 mm | in flash_reflector_interface (not modelled) | 1 |  | E5 | Amazon (Aurorad) | bought |  |

## Fasteners

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| F01 | M2.5x10 DIN 912 A2 | plastic pilot 2.0, M2.5_din912 head | 3 | Trunk 3 | 17i | Bolt Depot | bought | head d 4.5 does not fit the 4.00 recess: it sits on the part face, 3.0 mm higher; -1.25 mm vs head_bot_sheet (neck_pitch+head_pitch (57.9, 0.0)) |
| F02 | M2.5x5 DIN 912 A2 | plastic pilot 2.12 (speaker stand), M2.5_din912 head | 2 | Head 2 | 17k | BelMetric (US) | bought | found here, not in audit/screws2.py or MOUNTING.md (B8 says no screw): pilot axis 20.7 deg off the clearance hole axis, pilot centre 0.00 mm off it; 0.10 mm vs speaker_interface (zero pose (static) 0.0) |
| F03 | M2.5x6 DIN 912 A2 | plastic pilot 2.0, M2.5_din912 head | 11 | Head 4, Trunk 7 | 17f | Bolt Depot | bought | -0.00 mm vs speaker_stand (zero pose (static) 0.0) |
| F04 | M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers | plastic pilot (eye), M2.5_din912 head | 4 | Head 4 | 17g | Bolt Depot | bought | eye pilot is blind (3.0 mm deep, 1.5 mm front skin, ray cast): M2.5x8 alone reaches the floor (0.0 mm); with two 0.3 mm washers (0.6 mm): 2.4 mm of thread, 0.6 mm to the floor; 0.62 mm vs bulb (zero pose (static) 0.0) |
| F05 | M2x4 self-tapping pan head | servo pilot, M2_pan_selftap head | 2 | Head 2 | 17h | Amazon (ships from Amazon) | in kit | 0.02 mm vs head_roll_mount (zero pose (static) 0.0) |
| F06 | M2x5 self-tapping pan head | servo pilot, M2_pan_selftap head | 24 | Head 4, Left hip bracket 3, Left shin 2, Left thigh 2, Neck 2, Right hip bracket 3, Right shin 2, Right thigh 2, Trunk 4 | 17h | Amazon (ships from Amazon) | in kit | 0.02 mm vs head_roll_mount (zero pose (static) 0.0) |
| F07 | M2x6 self-tapping pan head | servo pilot, M2_pan_selftap head | 38 | Left hip 5, Left hip bracket 2, Left shin 2, Neck 6, Right hip 5, Right hip bracket 2, Right shin 2, Trunk 14 | 1 | Seeed Studio | in kit | -0.08 mm vs right_roll_to_pitch (zero pose (static) 0.0) |
| F07b | M2x6 machine screw, socket or pan head, A2 (D32) | the two STS3250 knee cases into the thighs: the aluminium case is tapped 4-M2.0 (SERVO_UPGRADE_OPTIONS.md F9), so the servo bag's self-tapping screws do not fit; thread depth not published | 4 | Left thigh 2, Right thigh 2 | 1 | BLOCKER: seller and price not read; length checked on the first unit (TEST_PLAN 15) | - | - |
| F08 | M2x8 self-tapping pan head | servo pilot, M2_pan_selftap head | 2 | Trunk 2 | 17h | Amazon (ships from Amazon) | in kit | -0.05 mm vs trunk_top (zero pose (static) 0.0) |
| F09 | M3x10 DIN 912 A2 | M3 insert, M3_din912 head | 12 | Left foot 2, Left thigh 2, Right foot 2, Right thigh 2, Trunk 4 | 17b | Bolt Depot | bought | 0.02 mm vs left_cache (zero pose (static) 0.0) |
| F10 | M3x12 DIN 912 A2 | M3 insert, M3_din912 head | 2 | Trunk 2 | 17c | Bolt Depot | bought | -0.08 mm vs trunk_top (zero pose (static) 0.0) |
| F11 | M3x5 DIN 912 A2 | horn(drive), M3_din912 head | 28 | Neck 28 | 17e | Bolt Depot | bought | -0.07 mm vs head_yaw_to_roll (zero pose (static) 0.0) |
| F12 | M3x6 DIN 912 A2 | M3 insert, M3_din912 head | 78 | Head 4, Left foot 8, Left hip 4, Left hip bracket 8, Left shin 12, Left thigh 5, Right foot 8, Right hip 4, Right hip bracket 8, Right shin 12, Right thigh 5 | 17d | Bolt Depot | bought | -0.16 mm vs body_middle_bottom (left_hip_yaw+left_hip_roll (30.0, 25.0)) |
| F13 | M3x6 ISO 7380 A2 button head | M3 insert, M3_iso7380 head | 10 | Left thigh 5, Right thigh 5 | 17j | BelMetric (US: "Stocked in the USA", since 1976, +1-978-649-6201) | bought | DIN 912 head is hit by roll_to_pitch (-0.19 mm); ISO 7380 head (k 1.65) clears it in the sweep, see FASTENERS.md section 3; 0.02 mm vs knee_to_ankle_right_sheet (zero pose (static) 0.0) |
| F14 | M3x6 machine screw (Feetech rocker screw) | servo output shaft, M3_horn_centre head | 14 | Left foot 1, Left hip 1, Left hip bracket 1, Left shin 1, Left thigh 1, Neck 4, Right foot 1, Right hip 1, Right hip bracket 1, Right shin 1, Right thigh 1 | 1 | Seeed Studio | in kit | comes with servo: M3x6 rocker screw per the Feetech datasheet; output shaft thread not modelled; Loctite 243: metal to metal [U] docs/assembly_guide.md (b23317a): trunk_bottom to trunk_top 2 x M3x10; foot_bottom_tpu to foot_bottom_pla 2 x M3x6; servo case screws are the plastic screws that come with the motors; Loctite 243 on metal to metal motor screws; -0.03 mm vs drive_palonier (zero pose (static) 0.0) |
| F15 | M3x8 DIN 912 A2 | M3 insert, M3_din912 head | 17 | Head 3, Left foot 2, Right foot 2, Trunk 10 | 17a | Bolt Depot | bought | 0.02 mm vs body_front (zero pose (static) 0.0) |
| F16 | PA2.0 self-tapping (factory) | servo case (factory), M2_case_factory head | 56 | Head 4, Left hip 4, Left hip bracket 4, Left shin 4, Left thigh 4, Neck 8, Right hip 4, Right hip bracket 4, Right shin 4, Right thigh 4, Trunk 12 | 1 | Seeed Studio | in kit | comes with servo, fitted at the factory: do not remove; length and head not published; -0.00 mm vs wj-wk00-0122topcabinetcase_95 (zero pose (static) 0.0); length from the drawing, not yet chosen |
| F17 | PA3.0x5 self-tapping, washer head (Feetech idle screw) | servo idle boss pilot 2.67, PA3_idle head | 3 | Head 1, Trunk 2 | 1 | Seeed Studio | in kit | FIT: nothing is screwed to this idle horn and 17.9 mm is free beyond it, so the PA3.0x5 screw from the bag keeps it on the boss (Feetech drawing); 0.02 mm vs wj-wk00-0124bottomcase_45 (zero pose (static) 0.0) |
| F18 | SG90 bag horn screw | SG90 output shaft (not modelled), SG90_screw head | 2 | Head 2 | 14 | Amazon (Miuzei) | in kit | NONE anchor resolved: the hole is on the antenna joint axis (0.04 mm); the screw goes from the outer face through the holder into the SG90 output shaft, which sg90.stl does not model; first solid surface 2.0 mm below the seat; size not published [I] https://www.rapidonline.com/rapid-pro-sg90-mini-servo-37-1330 ("Supplied complete with control horns and mounting screws"; sizes not published); -0.78 mm vs antenna (zero pose (static) 0.0); length from the drawing, not yet chosen |
| F19 | SG90 bag mounting screw | plastic pilot 1.55 (SG90 tab), SG90_screw head | 4 | Head 4 | 14 | Amazon (Miuzei) | in kit | SG90 bag screw (BOM 14), size not published; head pilot axis is 20.7 deg off the SG90 tab axis in the CAD; -0.80 mm vs body_back (neck_pitch 65.0); length from the drawing, not yet chosen |
| F20 | M2.5 flat washer, small series | two M2.5 flat washers, ISO 7092 A4 HV200, 2.7 x 5.0 x 0.3 mm (BelMetric WFHV2.5X5SSA4, BOM 17l): a 0.6 mm stack under each eye screw head (D21 note) | 8 | Head 8 | 17l | BelMetric (US) | bought | 2 under each of the 4 screw heads that have one (M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers) |
| F21 | M3 heat-set insert, CNC Kitchen M3 x 5.7 | D1 4.6 mm into a 4.0 mm bore | 47 | Head 7, Left foot 4, Left shin 4, Left thigh 4, Right foot 4, Right shin 4, Right thigh 4, Trunk 16 | 16 | CNC Kitchen USA | bought |  |
| F22 | Ball bearing 6804ZZ 20 x 32 x 7 | press into the 32.19 mm seats | 3 | Head, Trunk 2 | 18 | Amazon | bought |  |

## Cables

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| C01 | P1: holder + to BMS B+ | 1 wire, 16 AWG x1, cut 120 mm | 1 cable | battery_bay | L5, 26 | Amazon | made | pass: worst 56.3 mm vs cut 120 mm |
| C02 | P2: holder - to BMS B- | 1 wire, 16 AWG x1, cut 120 mm | 1 cable | battery_bay | L5, 26 | Amazon | made | pass: worst 56.3 mm vs cut 120 mm |
| C03 | P3: holder series strap to BMS B1 | 1 wire, 26 AWG x1, cut 140 mm | 1 cable | battery_bay | 25, 26 | Amazon | made | pass: worst 98.7 mm vs cut 140 mm |
| C04 | P4: BMS P+ to charger B+ | 1 wire, 20 AWG x1, cut 130 mm | 1 cable | battery_bay | 23, 26 | Amazon | made | pass: worst 10.7 mm vs cut 130 mm |
| C05 | P5: BMS P- to charger B- | 1 wire, 20 AWG x1, cut 130 mm | 1 cable | battery_bay | 23, 26 | Amazon | made | pass: worst 10.7 mm vs cut 130 mm |
| C06 | P6: BMS P+ to XT30U female + | 1 wire, 16 AWG x1, cut 150 mm | 1 cable | battery_bay | L5, 12, 26 | Amazon | made | pass: worst 100.2 mm vs cut 150 mm |
| C07 | P8: BMS P- to XT30U female - | 1 wire, 16 AWG x1, cut 150 mm | 1 cable | battery_bay | L5, 12, 26 | Amazon | made | pass: worst 100.2 mm vs cut 150 mm |
| C08 | P7: XT30U male + to fuse holder to Pololu 2815 VIN (the holder leads) | 4 wires, 16 AWG x4, cut 30/40/90 mm | 1 cable | battery_bay | L5, 12, 26 | Amazon | made | pass: worst 51.7 mm vs cut 130 mm |
| C09 | P14: XT30U male - to splice G | 1 wire, 16 AWG x1, cut 140 mm | 1 cable | battery_bay | L5, 12, 26 | Amazon | made | pass: worst 44.7 mm vs cut 140 mm |
| C10 | P9: 2815 VOUT to splice VSW | 1 wire, 16 AWG x1, cut 90 mm | 1 cable | battery_bay | L5, 26 | Amazon | made | pass: worst 10.1 mm vs cut 90 mm |
| C11 | P16: splice G to 2815 GND (control ground) | 1 wire, 20 AWG x1, cut 90 mm | 1 cable | battery_bay | 23, 26 | Amazon | made | pass: worst 10.6 mm vs cut 90 mm |
| C12 | P15: 2813 A and B to the momentary button (D30; was the 2815 SW pad pair to the panel switch) | 2 wires, 26 AWG x2, cut 150 mm | 1 cable | battery_bay | 25, 26 | Amazon | made | pass: worst 58.1 mm vs cut 150 mm |
| C13 | P10: splices VSW and G to the BEC input leads | 2 wires, 16 AWG x2, cut 150 mm | 1 cable | battery_bay, belly | L5, 26 | Amazon | made | pass: worst 58.0 mm vs cut 150 mm |
| C14 | P11: both BEC output leads joined (JB+ JB-) to the belly power splices SPV and SPG | 6 wires, BEC lead x4, 16 AWG x2, cut 100 mm | 1 cable | belly | L1, L5, 26 | Castle Creations; also Horizon Hobby CSE010000401 and Motion RC | made | pass: worst 8.3 mm vs cut 100 mm |
| C15 | SP1: power pair SPV and SPG to ID 20 BUS 2 (V and G) | 3 wires, 22 AWG x3, cut 30/140/160 mm | 1 cable | belly, trunk_bottom | 24, 21, 22, 26 | Amazon | made | pass: worst 86.6 mm vs cut 150 mm |
| C16 | SP2: power pair SPV and SPG to ID 10 BUS 2 (V and G) | 3 wires, 22 AWG x3, cut 30/130/150 mm | 1 cable | belly, trunk_bottom | 24, 21, 22, 26 | Amazon | made | pass: worst 84.6 mm vs cut 150 mm |
| C17 | SP3: power pair SPV and SPG to ID 30 BUS 2 (V and G) | 3 wires, 22 AWG x3, cut 30/160/180 mm | 1 cable | belly, trunk_top | 24, 21, 22, 26 | Amazon | made | pass: worst 91.7 mm vs cut 180 mm |
| C18 | SP4: power pair SPV and SPG to ID 24 BUS 1 (V and G), left leg | 2 wires, 22 AWG x2, cut 420 mm | 1 cable | belly, trunk_bottom, left_leg (crosses left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee) | 24, 21, 22, 26 | Amazon | made | pass: worst 363.5 mm vs cut 400 mm |
| C19 | SP5: power pair SPV and SPG to ID 14 BUS 1 (V and G), right leg | 2 wires, 22 AWG x2, cut 450 mm | 1 cable | belly, trunk_bottom, right_leg (crosses right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee) | 24, 21, 22, 26 | Amazon | made | pass: worst 392.8 mm vs cut 430 mm |
| C20 | P13: splices VSW and G up the neck to U3 VIN and GND on the head floor | 2 wires, 20 AWG x2, cut 550 mm | 1 cable | battery_bay, trunk_top, neck, head (crosses neck_pitch, head_pitch, head_yaw, head_roll) | 23, 26 | Amazon | made | pass: worst 441.1 mm vs cut 550 mm |
| C21 | P12: U3 VOUT and GND to Pi pin 2 and pin 6 | 2 wires, 20 AWG x2, cut 130 mm | 1 cable | head | 23, 26 | Amazon | made | pass: worst 33.7 mm vs cut 130 mm |
| C22 | P17: Pi pin 4 and pin 14 to splices J5 and JG | 2 wires, 20 AWG x2, cut 90 mm | 1 cable | head | 23, 26 | Amazon | made | pass: worst 28.9 mm vs cut 90 mm |
| C23 | D1: Pi micro-USB data port to adapter USB-C | 1 wire, USB 2.0 cable x1, cut 900 mm | 1 cable | head, neck, trunk_top, belly (crosses neck_pitch, head_pitch, head_yaw, head_roll) | 20 | Adafruit | bought | pass: worst 523.0 mm vs cut 900 mm |
| C24 | D2: Pi to BNO055 (3V3, GND, SDA, SCL) | 4 wires, 26 AWG x4, cut 550 mm | 1 cable | head, neck, trunk_top (crosses neck_pitch, head_pitch, head_yaw, head_roll) | 25, 26 | Amazon | made | pass: worst 439.3 mm vs cut 550 mm |
| C25 | D3: Pi to left foot switches, with pull-up R4 at the header | 6 wires, resistor lead x2, 26 AWG x4, cut 110/900 mm | 1 cable | head, neck, trunk_top, trunk_bottom, left_leg (crosses neck_pitch, head_pitch, head_yaw, head_roll, left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle) | 25, 26 | Amazon | made | pass: worst 770.4 mm vs cut 900 mm |
| C26 | D4: Pi to right foot switches, with pull-up R5 at the header | 6 wires, resistor lead x2, 26 AWG x4, cut 110/950 mm | 1 cable | head, neck, trunk_top, trunk_bottom, right_leg (crosses neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle) | 25, 26 | Amazon | made | pass: worst 767.1 mm vs cut 950 mm |
| C27 | D5: Pi to left eye LED and resistor | 3 wires, 26 AWG x2, resistor lead x1, cut 150 mm | 1 cable | head | 25, 26 | Amazon | made | pass: worst 59.6 mm vs cut 150 mm |
| C28 | D6: Pi to right eye LED and resistor | 3 wires, 26 AWG x2, resistor lead x1, cut 230 mm | 1 cable | head | 25, 26 | Amazon | made | pass: worst 123.4 mm vs cut 230 mm |
| C29 | D7: Pi to projector LED and resistor | 3 wires, 26 AWG x2, resistor lead x1, cut 160 mm | 1 cable | head | 25, 26 | Amazon | made | pass: worst 38.5 mm vs cut 160 mm |
| C30 | D8: left antenna SG90 lead to Pi pin 33 and splices J5 and JG | 3 wires, SG90 lead x3, cut 250 mm | 1 cable | head | 14, 26 | Amazon (Miuzei) | made | pass: worst 117.5 mm vs cut 250 mm |
| C31 | D9: right antenna SG90 lead to Pi pin 32 and splices J5 and JG | 3 wires, SG90 lead x3, cut 250 mm | 1 cable | head | 14, 26 | Amazon (Miuzei) | made | pass: worst 169.9 mm vs cut 250 mm |
| C32 | D10: Pi and splices to MAX98357A | 5 wires, 26 AWG x5, cut 210/220 mm | 1 cable | head | 25, 26 | Amazon | made | pass: worst 149.0 mm vs cut 220 mm |
| C33 | D11: MAX98357A to speaker | 2 wires, 26 AWG x2, cut 120 mm | 1 cable | head | 25, 26 | Amazon | made | pass: worst 73.0 mm vs cut 120 mm |
| C34 | D12: Pi CSI to Camera Module 3 | 1 wire, FPC ribbon x1, cut 300 mm | 1 cable | head | E7 | X-On Electronics | bought | pass: worst 227.3 mm vs cut 300 mm |
| C35 | D13: Pi GPIO26 (pin 37) to the 2813 OFF input (D30; gpio-poweroff) | 1 wire, 26 AWG x1, cut 590 mm | 1 cable | head, neck, trunk_top, battery_bay (crosses neck_pitch, head_pitch, head_yaw, head_roll) | 25, 26 | Amazon | made | pass: worst 542.5 mm vs cut 590 mm |
| C36 | SD1: adapter H3 data lead: DATA and GND only (V position empty), data Y at YD3 to ID 20 and ID 30, GND Y at YG3 into the SP1 and SP3 grounds | 6 wires, 22 AWG x6, cut 30/45/120/130/140/170 mm | 1 cable | trunk_top, trunk_bottom | 24, 21, 22, 26 | Amazon | made | pass: worst 26.0 mm vs cut 170 mm |
| C37 | SD2: adapter H5 data lead: DATA and GND only, to ID 10 (DATA) and JG10 (GND) | 2 wires, 22 AWG x2, cut 140/150 mm | 1 cable | trunk_top, trunk_bottom | 24, 21, 22, 26 | Amazon | made | pass: worst 66.2 mm vs cut 150 mm |
| C38 | S2: kit cable ID 20 BUS 1 to ID 21 BUS 2 | 3 wires, kit cable x3, cut 150 mm | 1 cable | trunk_bottom, left_leg (crosses left_hip_yaw) | 1 | Seeed Studio | in kit | test fit: worst 131.8 mm vs cut 150 mm |
| C39 | S3: kit cable ID 21 to ID 22 | 3 wires, kit cable x3, cut 150 mm | 1 cable | left_leg (crosses left_hip_roll) | 1 | Seeed Studio | in kit | pass: worst 88.0 mm vs cut 150 mm |
| C40 | S4: kit cable ID 22 to ID 23 | 3 wires, kit cable x3, cut 150 mm | 1 cable | left_leg (crosses left_hip_pitch) | 1 | Seeed Studio | in kit | pass: worst 95.8 mm vs cut 150 mm |
| C41 | S5: kit cable ID 23 BUS 1 to ID 24 BUS 2 | 3 wires, kit cable x3, cut 150 mm | 1 cable | left_leg (crosses left_knee) | 1 | Seeed Studio | in kit | pass: worst 109.8 mm vs cut 150 mm |
| C42 | S7: kit cable ID 10 to ID 11 | 3 wires, kit cable x3, cut 150 mm | 1 cable | trunk_bottom, right_leg (crosses right_hip_yaw) | 1 | Seeed Studio | in kit | test fit: worst 133.4 mm vs cut 150 mm |
| C43 | S8: kit cable ID 11 to ID 12 | 3 wires, kit cable x3, cut 150 mm | 1 cable | right_leg (crosses right_hip_roll) | 1 | Seeed Studio | in kit | pass: worst 103.9 mm vs cut 150 mm |
| C44 | S9: kit cable ID 12 to ID 13 | 3 wires, kit cable x3, cut 150 mm | 1 cable | right_leg (crosses right_hip_pitch) | 1 | Seeed Studio | in kit | pass: worst 102.6 mm vs cut 150 mm |
| C45 | S10: kit cable ID 13 to ID 14 | 3 wires, kit cable x3, cut 150 mm | 1 cable | right_leg (crosses right_knee) | 1 | Seeed Studio | in kit | pass: worst 108.9 mm vs cut 150 mm |
| C46 | S11: kit cable ID 30 BUS 1 to ID 31 BUS 2 | 3 wires, kit cable x3, cut 150 mm | 1 cable | trunk_top, neck (crosses neck_pitch) | 1 | Seeed Studio | in kit | pass: worst 98.4 mm vs cut 150 mm |
| C47 | S12: kit cable ID 31 to ID 32 | 3 wires, kit cable x3, cut 150 mm | 1 cable | neck (crosses head_pitch, head_yaw) | 1 | Seeed Studio | in kit | pass: worst 89.7 mm vs cut 150 mm |
| C48 | S13: kit cable ID 32 to ID 33 | 3 wires, kit cable x3, cut 150 mm | 1 cable | neck, head (crosses head_roll) | 1 | Seeed Studio | in kit | pass: worst 106.9 mm vs cut 150 mm |

## Connectors and wire

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| C49 | Servo kit cable, 15 cm 5264-3P | one ships with each STS3215 (14 in all) | 11 |  | 1 | Seeed Studio | in kit | 11 used, 3 spare |
| C50 | Mini-SPOX housing, Molex 50-37-5033 | 3 pos 2.5 mm, mates the servo sockets | 7 |  | 21 | Newark 57H1785 | bought |  |
| C51 | Mini-SPOX crimp terminal, Molex 08-70-1040 | 22 to 28 AWG | 17 |  | 22 | Newark 54H5573 | bought |  |
| C52 | Heat shrink pieces (splices and solder joints) | one sleeve per joint: 15 splices, 10 wire to lead, 3 lead to lead, 4 XT30 solder cups, 2 caps on cut lead wires | 34 |  | 26 | Amazon | bought | one sleeve per splice; one per solder joint outside a splice where a wire meets a part's flying lead or two flying leads meet (holder, BEC, resistor and LED leads); one over each XT30 solder cup (HARNESS_BUILD 'heat shrink over the cup'); one cap on each cut lead wire the netlist says to insulate. None on board pads, holes, header pins, plugs, sockets and screw terminals; switch terminals, lugs and tabs get one only if copper shows (HARNESS_BUILD 'heat shrink if bare'), not counted (wiring/netlist.yaml). The 3D view draws 34 of the 34. The 2 holder lead joints (hs-P1-PACK-Bp, hs-P2-PACK-Bn) go away if the holder leads reach the BMS (120 mm or longer, netlist PACK note). |
| C53 | Wire 16 AWG black | silicone stranded; sum of netlist cut lengths | 0.66 m |  | L5 | Amazon | bought |  |
| C54 | Wire 16 AWG red | silicone stranded; sum of netlist cut lengths | 0.68 m |  | L5 | Amazon | bought |  |
| C55 | Wire 20 AWG black | silicone stranded; sum of netlist cut lengths | 0.99 m |  | 23 | Amazon | bought |  |
| C56 | Wire 20 AWG red | silicone stranded; sum of netlist cut lengths | 0.9 m |  | 23 | Amazon | bought |  |
| C57 | Wire 22 AWG black | silicone stranded; sum of netlist cut lengths | 1.84 m |  | 24 | Amazon | bought |  |
| C58 | Wire 22 AWG red | silicone stranded; sum of netlist cut lengths | 1.36 m |  | 24 | Amazon | bought |  |
| C59 | Wire 22 AWG yellow | silicone stranded; sum of netlist cut lengths | 0.48 m |  | 24 | Amazon | bought |  |
| C60 | Wire 26 AWG black | silicone stranded; sum of netlist cut lengths | 3.65 m |  | 25 | Amazon | bought |  |
| C61 | Wire 26 AWG blue | silicone stranded; sum of netlist cut lengths | 1.14 m |  | 25 | Amazon | bought |  |
| C62 | Wire 26 AWG green | silicone stranded; sum of netlist cut lengths | 1.39 m |  | 25 | Amazon | bought |  |
| C63 | Wire 26 AWG red | silicone stranded; sum of netlist cut lengths | 0.89 m |  | 25 | Amazon | bought |  |
| C64 | Wire 26 AWG white | silicone stranded; sum of netlist cut lengths | 1.66 m |  | 25 | Amazon | bought |  |
| C65 | Wire 26 AWG yellow | silicone stranded; sum of netlist cut lengths | 1.05 m |  | 25 | Amazon | bought |  |

## Consumables and other

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| K01 | Solder wire, rosin core | about 146 solder joints and splice ends in the netlist | 1 |  | 30 | Adafruit 1886 | bought | wiring/netlist.yaml wire ends: splices, pads, cups, header holes |
| K02 | Cable ties, small nylon | about 100 mm | 75 |  | 32 | Home Depot | bought | MOUNTING.md: cable tie at the servo power splices and the USB slack coil; 75 placed along the cables in the 3D view, one per retention item (55 adhesive tie mount, 9 cable tie, 2 cable tie to a neighbour cable, 3 drilled printed feature, 6 existing printed feature), 69 at gaps |
| K09 | Adhesive tie mount MB3A | placed along the cables (altaay_lab/cables3d) | 32 |  | 34 | Standard Electric Supply (US) | bought | 32 at places where the CAD has no feature |
| K10 | Adhesive tie mount ABM1M-AT-C | placed along the cables (altaay_lab/cables3d) | 23 |  | 34b | Hisco (Houston, TX) | bought | 23 at places where the CAD has no feature |
| K11 | Main power switch: replaced (D30) | Pololu 2815 Big MOSFET Slide Switch with Reverse Voltage Protection, HP: 4.5 to 32 V, 6 A at 55 C and 16 A at 150 C MOSFET temperature, 90 A max, 0.8 x 1.0 x 0.16 in; on-board slide set OFF, controlled by line 10b | 0 |  | 10r | Pololu (Las Vegas, NV) | bought |  |
| K12 | Control switch: replaced (D30) | Stock panel slide switch in the body_back cutout (CAD power_switch.stl: flange 23.4 x 7.4, body 15.7 x 7.4, actuator 5.4 x 3.8 mm), switches only the Pololu 2815 control pin (microamps) | 0 |  | 10b-old | see Verified | bought |  |
| K13 | Threadlocker | Loctite 243, 6 mL, P/N 1330799 | 1 |  | 19 | Amazon | bought |  |
| K14 | Foam mounting tape | 3M VHB 4950, 3/4 in x 5 yd, 1.1 mm (45 mil) acrylic foam, for the BEC Pro, fuse holder, Pololu 2813 (D30), 5 V regulator, amp, the eye LED rings, the side lamp module, its reflector interface and E5 (D33), the D30 button plate flange (MOUNTING.md; twin/assembly/ASSEMBLY_TWIN.md item 1) | 0.4 m |  | 29 | Zoro (3M) | bought |  |
| K15 | Flux pen (optional, recommended for 16 AWG) | Chip Quik CQ4LF no-clean liquid flux pen, 10 mL, for leaded and lead-free solder, classification printed as "INM0", shelf life over 24 months (page) | 1 |  | 31 | Adafruit 3468 | bought |  |
| K16 | Isopropyl alcohol | Techspray 1610-P, 99.8 % anhydrous isopropyl alcohol, no denaturant, ACS reagent grade, 1 pint bottle, flammable (flash point 53 C), shelf life 1825 days (page). Wipe each line 34 and 34b mount spot and each line 29 VHB tape spot with a clean cloth or paper towel wetted with it, then let it dry before the adhesive goes on; 3M's VHB surface preparation bulletin calls for a 50:50 isopropyl alcohol and water wipe on most surfaces and 3M also lists 70:30 (read via search index; 3m.com refuses curl), so a 70 % pharmacy rubbing alcohol also works | 1 bottle (55 mount spots of lines 34 and 34b plus the line 29 tape spots) |  | 35 | TestEquity (Moorpark, CA) | bought |  |
| K17 | Polyimide (Kapton) tape | Adafruit 3057 polyimide tape, 10 mm wide, 33 m roll, stable from about -269 C to +400 C (page); thickness and dielectric strength not stated (UNVERIFIED). Wraps the Tenergy BMS, 34 x 16 x 4.5 mm (MOUNTING.md: "wrap in kapton tape before it goes in") | about 0.2 m (2 turns of 77 mm around the 34 x 4.5 mm section to cover the 16 mm width, calculated) |  | 33 | Adafruit 3057 | bought |  |
| K18 | Camera cable, replaced (D34) | Pi Zero camera cable 150 mm, Adafruit 3157: 77 mm short of the flat strip route (B61) | 0 |  | E7r | Adafruit 3157 | bought |  |

## Tools

| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |
|---|---|---|---|---|---|---|---|---|
| K03 | USB-C PD supply for the soldering iron | powers the Pinecil V2 (BOM T1) | 1 |  | T6 | Amazon (ships from and sold by Amazon.com) | tool | BOM.md T1: needs a USB-C PD supply |
| K04 | USB-C supply to charge the robot | feeds the USB-C 2S charge board (BOM 11) | 1 |  | T7 | Amazon (ships from and sold by Amazon.com) | tool | netlist CHG: USB-C input |
| K05 | Multimeter with continuity beep | TEST_PLAN.md section 0 | 1 |  | TE1 | Home Depot | tool | TEST_PLAN.md section 0, sections 2 to 12 |
| K06 | Bench DC supply with current limit | TEST_PLAN.md section 0: first power always current limited | 1 |  | TE2 | Siglent Technologies America (North Plains, OR) | tool | TEST_PLAN.md sections 4, 5, 7, 8 |
| K07 | Digital calipers | TEST_PLAN.md section 0 | 1 |  | TE3 | Penn Tool Co. (Maplewood, NJ) | tool | TEST_PLAN.md section 0 and the coupon checks |
| K08 | Load for the regulator tests | TEST_PLAN.md section 4 and 5 input sweeps | 1 |  | TE4 | Siglent Technologies America (North Plains, OR) | tool | TEST_PLAN.md sections 4 and 5 |
| K19 | Soldering iron | Pine64 Pinecil V2 (needs a USB-C PD 20 V 3.25 A supply: lines T6 and T6b) | 1 |  | T1 | Pine64 | tool |  |
| K20 | Insert tips | Pinecil threaded insert tips set and adapter | 1 |  | T2 | Pine64 | tool |  |
| K21 | Crimper | Engineer PA-09 (Mini-SPOX 5263 and JST XH per DigiKey chart) | 1 |  | T3 | Amazon | tool |  |
| K22 | Hex keys | Bondhus 12192 hex L-keys 1.5 to 6 mm, 7 pc (2.0 mm for M2.5, 2.5 mm for M3 SHCS) | 1 |  | T4 | Crawford Tool | tool |  |
| K23 | Wire stripper | Klein 11057, 22 to 32 AWG stranded | 1 |  | T5 | Home Depot | tool |  |
| K24 | BEC programmer | Castle Link V4 011-0173-00 (needs Windows 10 PC) | 1 |  | L2 | Castle Creations | tool |  |
| K25 | USB-C to USB-C cable, 5 A | Adafruit 4199, USB 3.1 Gen 4 with E-Mark, 1 m; Adafruit: it "includes an EMARK chip ... you can use this for high current (5A) charging". The 3.2 A short tip draw at 20 V is above 3 A, so the cable needs the 5 A e-marker | 1 |  | T6b | Adafruit 4199 | tool |  |
| K26 | USB-A to USB-C cable | Amazon Basics USB-A to USB-C, USB 2.0, USB-IF certified, 3 ft, maximum current 3 A, 15 W at 5 V (page). An A to C cable carries the resistor that tells the board it may draw 5 V (Adafruit on its A to C cable: "The cable has built in resistors to force it to 5V power", https://www.adafruit.com/product/4474), so it works whether or not the Adeept board has USB-C CC pull-down resistors (its listing does not say) | 1 |  | T7b | Amazon (ships from and sold by Amazon.com) | tool |  |
| K27 | microSD card reader (optional, often on hand) | Adafruit 5212 USB Type C microSD card reader/writer, mass storage, no driver (page); USB-C plug, so the PC needs a USB-C port | 1 |  | T8 | Adafruit 5212 | tool |  |
| K28 | Wire stripper 12 to 20 AWG | Klein 11055, "Strips, cuts, loops 10-18 AWG solid and 12-20 AWG stranded wire" (page); covers the 16 AWG and 20 AWG runs that T5 (22 to 32 AWG) cannot | 1 |  | T9 | Home Depot | tool |  |
| K29 | Heat gun | Wagner Furno 300, dual temperature, corded, 10 A, 20 cu ft/min, minimum temperature 750 F, 2 year limited warranty (page specs); for the adhesive lined 3:1 heat shrink (line 26); shrink each joint before it goes near printed PLA | 1 |  | T10 | Home Depot | tool |  |
| K30 | Drill bit 6.0 mm | HSS jobber, black oxide, 118 deg point, round shank, 70 mm flutes, Qualtech DWDMM6.00; opens the 24 neck chain screw recesses from 5.5 to 6.0 mm after printing and on coupon C4 (D20, print/PRINT_PLAN.md "After printing") | 1 |  | T11 | Drills and Cutters (Doral, FL) | tool |  |
| K31 | Drill bit 2.7 mm | HSS jobber, black oxide, 118 deg point, round shank, Qualtech DWDMM2.70; opens the 4 battery_pack_lid clearance holes from 2.5 to 2.7 mm (D20) | 1 |  | T12 | Drills and Cutters (Doral, FL) | tool |  |
| K32 | Hand holder for T11, T12, T14 and T15 | Qualtech DWTD328 T-handle tap wrench for 1/16 to 1/4 in taps, carbon steel; turns the bits by hand, slowly, so the cut in PLA stays controlled (no power tool) | 1 |  | T13 | Drills and Cutters (Doral, FL) | tool |  |
| K33 | Drill bit 4.0 mm | HSS jobber, black oxide, 118 deg point, round shank, 75 mm long, 54 mm flutes, Qualtech DWDMM4.00; drills the 4.0 mm lead hole for the projector LED (D7) through the printed head wall (D24) and the three D25 cable tie-hole pairs (two in neck_right_sheet, one in the left leg's knee_to_ankle_right_sheet) (print/PRINT_PLAN.md "After printing" steps 4 and 5); turned in the T13 holder | 1 |  | T14 | Drills and Cutters (Doral, FL) | tool |  |
| K34 | Drill bit 4.5 mm (contingency) | HSS jobber, black oxide, 118 deg point, round shank, 80 mm long, 56 mm flutes, Qualtech DWDMM4.50; opens the M2 screw recesses only if coupon C4 shows a servo-bag screw head that does not fit (D20 coupon gate) | 1 |  | T15 | Drills and Cutters (Doral, FL) | tool |  |

## BOM.md lines and the rows that use them

Every purchase line is used by at least one row.
