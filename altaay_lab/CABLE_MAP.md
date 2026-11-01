# CABLE_MAP

Last updated: 2026-11-01 2:25 PM ET. One row per cable. Routes measured on the upstream URDF/STL assembly (STL commit 730c14b) on the box: the route is a polyline through the centres of the parts the cable passes and the joint axes it crosses (script: audit/cables.py, data: audit/cables.json). Nothing has been built.

## Length rule (lab design rule, not a measurement)
Cut length = route polyline + 2 x 22.6 mm (connector position tolerance at each end, half of the STS3215 45.2 mm case length, because connector positions on the servo are not modelled in the CAD) + 2 x 20 mm service slack + 10 mm per radian of joint range crossed (joint ranges from the URDF limits).
Lower bound = straight distance minus 45.2 mm (connectors at the nearest corners). A cable shorter than the lower bound cannot fit; one longer than the rule length always fits; in between needs a test fit.

For parts not in the CAD (UBEC, BEC Pro, fuse holder, XT30, amplifier, LEDs' exact seats), the nearest modelled part is used as the reference point and the row is marked BLOCKER.

## Connector parts
| Use | Housing | Terminal | Wire | Tool |
|---|---|---|---|---|
| STS3215 bus (servo and adapter H3/H5 sockets are 5264-type 2.5 mm 3-pin) | Molex 50-37-5033 (Mini-SPOX 3 pos) | Molex 08-70-1040 (5263, 22 to 28 AWG) | 22 AWG | Engineer PA-09 (listed for Molex 5263 in the PA-09/PA-20 chart, https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2194/PA-09_PA-20_Compatibility_Chart_5-4-17.pdf) |
| Battery disconnect | Amass XT30U male and female | solder cups | 16 AWG | soldering iron |
| Everything else | none, solder to through-holes or tabs, heat shrink over each joint | | | Pinecil V2 |

## A. Servo bus (14 servos, 3 chains, 2 adapter sockets)
Waveshare Bus Servo Adapter (A) schematic (https://files.waveshare.com/wiki/Bus-Servo-Adapter-(A)/Bus%20Servo%20Adapter%20(A)-Sch.pdf): only H3 and H5 are servo sockets, in parallel. Three chains need one made Y-lead (S1Y).

Kit cable = the 15 cm 3-pin cable shipped with each STS3215 (14 shipped, 12 used, 2 spare). Cable spec from the Feetech STS3215 spec sheet (https://www.mantech.co.za/Datasheets/Products/STS3215-200620A.pdf): 5264-3P, 15 cm, pinout GND, VCC, signal. The same sheet says "No Accessories", so whether every seller ships the cable is a BLOCKER-lite: confirm on the Seeed order (the Seeed page does not state it).

| ID | From | To | Signal / power | Gauge | Ends | Route (parts passed, joints crossed) | Polyline | Straight | Joint range rad | Lower bound | Rule length | Source | Fit vs 150 mm kit cable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1Y | Adapter H3 | Y splice, then ID 20 L hip yaw and ID 30 neck pitch | bus V+ 7.2 V, GND, data | 22 AWG | 3x 50-37-5033 + 9x 08-70-1040, solder splice in heat shrink 10 mm from H3 | trunk_top to trunk_bottom servo bay (L hip yaw) and to the neck servo on trunk_top, no joints | 63.8 (to 20), 87.3 (to 30) | 63.8, 87.3 | 0 | 18.6, 42.1 | 149.0 (leg 150), 172.5 (leg 175) | MAKE | n/a (made: legs 150 and 175 mm, 975 mm of 22 AWG) |
| S2 | ID 20 L hip yaw | ID 21 L hip roll | bus | kit | 5264 both ends | through hip yaw horn and roll_motor_top/bottom, crosses left_hip_yaw | 56.6 | 54.3 | 1.05 | 9.1 | 152.3 | kit | BLOCKER test fit (rule 2.3 mm over) |
| S3 | ID 21 | ID 22 L hip pitch | bus | kit | 5264 | roll_motor_bottom to left_roll_to_pitch, crosses left_hip_roll | 82.3 | 56.2 | 0.87 | 11.0 | 176.2 | kit | BLOCKER test fit |
| S4 | ID 22 | ID 23 L knee | bus | kit | 5264 | left_roll_to_pitch, leg_spacer, knee sheets, crosses left_hip_pitch | 92.1 | 67.3 | 1.75 | 22.1 | 194.8 | kit | BLOCKER test fit |
| S5 | ID 23 | ID 24 L ankle | bus | kit | 5264 | knee_to_ankle sheets, crosses left_knee | 92.1 | 78.7 | 3.14 | 33.5 | 208.7 | kit | BLOCKER test fit |
| S6 | Adapter H5 | ID 10 R hip yaw | bus | kit | 5264 | trunk_top to trunk_bottom, no joints | 63.8 | 63.8 | 0 | 18.6 | 149.0 | kit | fits (1.0 mm margin) |
| S7 | ID 10 | ID 11 R hip roll | bus | kit | 5264 | as S2 mirrored | 56.6 | 54.3 | 1.05 | 9.1 | 152.3 | kit | BLOCKER test fit |
| S8 | ID 11 | ID 12 R hip pitch | bus | kit | 5264 | as S3 mirrored | 82.3 | 56.2 | 0.87 | 11.0 | 176.2 | kit | BLOCKER test fit |
| S9 | ID 12 | ID 13 R knee | bus | kit | 5264 | as S4 mirrored | 91.6 | 67.3 | 1.75 | 22.1 | 194.3 | kit | BLOCKER test fit |
| S10 | ID 13 | ID 14 R ankle | bus | kit | 5264 | as S5 mirrored | 92.1 | 78.7 | 3.14 | 33.5 | 208.7 | kit | BLOCKER test fit |
| S11 | ID 30 neck pitch | ID 31 head pitch | bus | kit | 5264 | neck sheets, head_pitch_to_yaw, crosses neck_pitch | 80.0 | 66.0 | 1.48 | 20.8 | 180.0 | kit | BLOCKER test fit |
| S12 | ID 31 | ID 32 head yaw | bus | kit | 5264 | head_pitch_to_yaw to head_yaw_to_roll, crosses head_pitch and head_yaw | 106.3 | 51.6 | 7.16 | 6.4 | 263.1 | kit | BLOCKER test fit (113 mm over rule) |
| S13 | ID 32 | ID 33 head roll | bus | kit | 5264 | head_yaw_to_roll to head_roll_mount, crosses head yaw | 51.6 | 49.6 | 1.05 | 4.4 | 147.3 | kit | fits (2.7 mm margin) |

Result: 2 hops fit by rule, 10 need a test fit (every lower bound is 42 mm or less, so none is ruled out). The upstream BOM lists no extension cables. Contingency X1/X2 in BOM.md (made Mini-SPOX leads, 200 mm for legs and 270 mm for S12). Clear the BLOCKER by test-fitting the kit cables on the first printed leg and neck with each joint at both limits.

## B. Power
| ID | From | To | Power | Gauge | Ends | Route | Polyline | Rule length / cut | Source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 2S holder + lead | BMS B+ pad | pack 6.0 to 8.4 V, up to 20 A burst | 16 AWG | solder both | inside body_back battery bay | 30.2 | 115.4 / 120 | holder lead if 120 mm or more, else make | holder lead length not verified |
| P2 | 2S holder - lead | BMS B- pad | pack return | 16 AWG | solder | same | 30.2 | 115.4 / 120 | as P1 | |
| P3 | holder series strap (cell 1 - / cell 2 +) | BMS BM pad | balance sense, under 0.1 A | 26 AWG | solder | same | 30.2 | 115.4 / 120 | make | BLOCKER: holder B09WCT8672 has no mid tap lead listed; solder to its series strap or pick a holder with one |
| P4 | BMS P+ | USB-C charger board B+ | charge, up to 2 A (seller) | 20 AWG | solder | body_back | 39.4 | 124.6 / 130 | make | |
| P5 | BMS P- | charger B- | charge return | 20 AWG | solder | body_back | 39.4 | 124.6 / 130 | make | |
| P6 | BMS P+ | XT30U female (pack side) | pack + | 16 AWG | solder, XT30 cup | body_back toward switch | part of 79.4 BMS to switch | 164.6 total BMS to switch | make | XT30 not in CAD: split 165 mm between P6 and P7, BLOCKER on exact split |
| P7 | XT30U male | fuse holder FHAC0001ZXJ in, fuse out to switch terminal 1 | pack + fused 15 A | 16 AWG (holder leads 16 AWG) | XT30 cup, solder to switch | body_back | rest of 79.4 | rest of 164.6 | fuse holder leads ship with it, length not verified | BLOCKER: fuse holder lead length |
| P8 | BMS P- | XT30U female, then common ground node | pack - | 16 AWG | solder, XT30 | body_back | 79.4 | 164.6 / 170 | make | |
| P9 | switch terminal 2 | pack bus node (splice) | switched + | 16 AWG | solder, heat shrink | body_back to trunk | 51.9 (switch to adapter) | 137.1 / 140 | make | |
| P10 | pack bus node | Castle CC BEC Pro input | switched + and GND | 16 AWG | solder to BEC input leads | trunk | not in CAD | BLOCKER | BEC input leads ship with BEC | BEC Pro not in CAD; input lead gauge and length not published |
| P11 | CC BEC Pro output (both 3-pin leads joined) | Adapter H1 screw terminal + / - | servo 7.2 V, up to 15 A | 16 AWG | bare wire in screw terminal, ferrule optional | trunk_top | reference switch to adapter 51.9 | 137.1 / 140 if extended | BEC leads ship (cut and join) | BLOCKER: BEC position |
| P12 | pack bus node | HENGE UBEC input | 2 A max | 20 AWG | solder | trunk | not in CAD | BLOCKER | UBEC leads ship, length not verified | |
| P13 | UBEC 5 V out | Pi Zero 2 W pin 2 (5 V) and pin 6 (GND), 2 wires | 5 V, about 2.4 A peak (Pi 0.5 A + 2 SG90 + amp) | 20 AWG red and black | solder to Pi header through-holes | trunk, through neck to head (Pi is in head), crosses 4 neck joints | 354.0 (Pi to switch, UBEC reference) | 536.1 / 550 each | make | BLOCKER: UBEC position. Drop over 1.1 m of 20 AWG at 2.4 A about 0.08 V |

## C. Data and signal
Pi Zero 2 W mounts in head.stl (MOUNTING.md). Pin numbers from upstream docs/assembly_guide.md; Runtime code differs for eyes and antennas (WIRING.md section 3).

| ID | From | To | Signal | Gauge | Ends | Route | Polyline | Rule length / cut | Source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Pi micro-USB OTG port | Adapter USB-C | USB 2.0, /dev/ttyACM0 | cable | Micro-B to USB-C | head through neck to trunk_top, 4 neck joints 9.69 rad | 320.5 | 502.6 vs 500 cable | BUY (QJJ 50 cm) | BLOCKER test fit: rule is 2.6 mm over 50 cm, lower bound 163.7. Contingency X3: 1 m |
| D2 | Pi pins 1 (3V3), 9 (GND), 3 (SDA), 5 (SCL), 4 wires | BNO055 2472 VIN, GND, SDA, SCL | I2C 3.3 V | 26 AWG, 4 colours | solder both ends | head, neck, trunk_top | 329.3 | 511.4 / 550 each | make | |
| D3 | Pi pin 15 (GPIO22) and pin 9 (GND) | left foot Omron SS-10 COM / NO | contact, 3.3 V pull-up | 26 AWG x2 | solder both | head, neck, trunk, left leg, crosses 4 neck + 5 leg joints 19.64 rad | 602.4 | 884.0 / 900 each | make | BLOCKER: SS-10 seat not in CAD |
| D4 | Pi pin 13 (GPIO27) and pin 9 | right foot SS-10 | contact | 26 AWG x2 | solder | as D3 mirrored | 632.4 | 914.0 / 950 each | make | as D3 |
| D5 | Pi pin 16 (GPIO23) / GND | left eye LED + resistor | LED | 26 AWG x2 | solder | inside head | 94.8 (Manhattan, no joint) | 134.8 / 150 | make | LED and resistor BLOCKER |
| D6 | Pi pin 18 (GPIO24) / GND | right eye LED | LED | 26 AWG x2 | solder | inside head | 176.8 | 216.8 / 230 | make | as D5 |
| D7 | Pi pin 22 (GPIO25) / GND | projector LED in flash_light_module | LED | 26 AWG x2 | solder | inside head | 112.4 | 152.4 / 160 | make | as D5 |
| D8 | Pi pins 32 (GPIO12), 2 (5 V), 6 (GND) | left antenna SG90 | PWM 5 V | SG90 lead + 26 AWG if needed | SG90 3-pin female, solder at Pi | inside head | 133.2 | 173.2 / 180 | SG90 lead ships | BLOCKER: Miuzei SG90 lead length not verified |
| D9 | Pi pins 33 (GPIO13), 2, 6 | right antenna SG90 | PWM 5 V | as D8 | as D8 | inside head | 228.0 | 268.0 / 270 | as D8 | as D8 |
| D10 | Pi pins 35 (LRC), 12 (BCLK), 40 (DIN), 2 (5 V), 6 (GND) | MAX98357A 3006 | I2S + power | 26 AWG x5 | solder | inside head | 149.5 (Pi to speaker_interface) | 189.5 / 200 | make | BLOCKER: amplifier seat not in CAD |
| D11 | MAX98357A + / - | speaker | audio | 26 AWG x2 | solder (amp screw terminal or pads) | inside head | not in CAD | BLOCKER | make | speaker model BLOCKER |
| D12 | Pi CSI | camera | MIPI CSI | 22-pin mini CSI ribbon | ZIF | head | not in CAD | BLOCKER | not chosen | camera absent upstream |

## Wire totals (cut lengths summed, with 10% spare)
| Gauge | Rows | Sum | With spare | Bought |
|---|---|---|---|---|
| 16 AWG | P1, P2, P6 to P9, P11 | about 1.1 m | 1.2 m | 50 ft (BOM L5) |
| 20 AWG | P4, P5, P13 (P12 if extended) | 1.36 m | 1.5 m | 50 ft (BOM 23) |
| 22 AWG | S1Y | 0.98 m | 1.1 m | 150 ft (BOM 24) |
| 26 AWG | P3, D2 to D7, D10 | 8.2 m | 9.0 m | 175 ft (BOM 25) |

## Ships with a component vs made vs bought
- Ships: 14 kit servo cables (12 used), SG90 leads, BEC Pro input and output leads, UBEC leads, fuse holder leads, holder leads.
- Bought: D1 USB cable.
- Made: S1Y, P1 to P9, P13, D2 to D7, D10, D11 (plus X1/X2 leads if a test fit fails).
