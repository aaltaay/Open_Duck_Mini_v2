# WIRING: Open Duck Mini v2, altaay-lab build

Last updated: 2026-11-01 (America/New_York). Diagram: wiring/odm_v2_wiring.svg and wiring/odm_v2_wiring.png (drawn by wiring/make_wiring.py with schemdraw 0.23).

Tags used below:
- [U] taken from upstream (Open_Duck_Mini docs/assembly_guide.md pin table, docs/open_duck_mini_v2_wiring_diagram.png, docs/wiring.png, Runtime code, Playground MJCF).
- [L] lab change decided by Ahmed (D3, 2026-11-01 1:09 PM ET): servo buck regulator, fuse, 16 AWG harness.
- [I] inferred by us, not stated upstream. Check on the real build.

## 1. Power path

| Step | From | To | Wire | Connector or part | Tag |
|---|---|---|---|---|---|
| 1 | Cell 1 (+) | Cell 2 (-) in series, 2x Molicel INR18650-P30B | holder internal | 2x18650 holder B09WCT8672 (spring contacts) | [U] holder type, [I] model |
| 2 | Pack + / mid / - | BMS B+ / BM / B- | 16 AWG (B+, B-), 22 AWG (BM) | solder | [U] topology, [I] gauge |
| 3 | BMS P+ / P- | USB-C 2S charge board | 22 AWG | solder | [U] |
| 4 | BMS P+ / P- | XT30U pair (pack side) | 16 AWG | Amass XT30U | [I] (lets the pack be removed) |
| 5 | XT30 + | Inline fuse, 15 A ATO | 16 AWG (holder leads are 16 AWG) | Littelfuse FHAC0001ZXJ holder plus 0287015.PXCN 15 A fuse | [L] |
| 6 | Fuse out | Power switch | 16 AWG | switch must be rated 15 A DC or more; the stock rocker (B0CH3JCQM5) has no published rating | [U] switch, [L] rating |
| 7 | Switch out | pack bus node (6.0 to 8.4 V) | 16 AWG | solder splice with heat shrink | [U] |
| 8a | pack bus | Castle CC BEC Pro input | 16 AWG | solder to BEC input leads (input lead gauge not published) | [L] |
| 8b | CC BEC Pro output, 7.2 V | Waveshare Bus Servo Adapter (A) green screw terminal | 16 AWG | both BEC 3-pin output leads cut and joined, red to +, black to - (Castle: each 3-pin lead is good for 5 A continuous; above 10 A replace the connectors) | [L] |
| 9 | pack bus | HENGE 4A UBEC 5 V input | 20 AWG | solder | [U] |
| 10 | UBEC 5 V out | Pi Zero 2 W pin 2 or 4 (5 V), GND pin 6 | 20 AWG | 2-pin Dupont or solder to header | [U] UBEC to Pi, [I] feed point (could also be micro-USB PWR) |
| 11 | Pi micro-USB (OTG data port) | Adapter USB-C | short cable, 15 cm | micro-USB to USB-C (BOM line 22) | [U] (/dev/ttyACM0, 1 Mbaud) |
| 12 | Adapter servo ports | servo chains (section 2) | Feetech 3-wire cables that ship with the servos | 3-pin bus connector | [U] |

Grounds: all grounds are common and return to BMS P-. The Pi, the BNO055, the UBEC and the servo bus share ground [U].

Why the screw terminal and not the barrel jack: the stock build feeds the adapter through a 5.5x2.1 mm barrel plug (BOM line 12). Common 5.5x2.1 jacks are rated about 5 A, well below walking peaks. Use the green screw terminal the Waveshare wiki lists as the other power input [I].

Adapter jumper: Waveshare says the jumper goes on B for USB control (Pi over USB) and on A for UART. Upstream uses USB, so B [U wiki].

Adapter voltage: the Waveshare wiki lists 9 to 12.6 V input and says "input voltage must match servo voltage". The board passes the supply to the bus. Upstream runs it at 2S (6.0 to 8.4 V), so 7.2 V is inside what upstream already does. Logic power on the board is from USB (not verified on the schematic).

Regulator behavior: the CC BEC Pro is set to 7.2 V. When the pack falls below about 7.3 to 7.5 V the buck runs out of headroom and the output follows the input minus a small drop. That is fine for the servos (6.0 V minimum is still in range). The exact dropout of the CC BEC Pro is not published (not verified). The BMS cuts at its own low-voltage threshold (seller spec only).

## 2. Servo bus (14x Feetech STS3215 C001, 7.4 V, 1:345)

IDs are from the Runtime and assembly guide [U]. Order inside each chain follows the joint order from the body outwards [U for legs].

| Adapter port | Chain order (ID, joint) | Tag |
|---|---|---|
| Port 1 | 20 left_hip_yaw, 21 left_hip_roll, 22 left_hip_pitch, 23 left_knee, 24 left_ankle | [U] |
| Port 1 (branch) | 30 neck_pitch, 31 head_pitch, 32 head_yaw, 33 head_roll | [U] IDs, [I] branch point (upstream diagram draws the neck chain with a dashed line joining near the left leg) |
| Port 2 | 10 right_hip_yaw, 11 right_hip_roll, 12 right_hip_pitch, 13 right_knee, 14 right_ankle | [U] |

The bus is electrically one shared line (V+, GND, half-duplex data), so the branch point does not matter for the protocol. It does matter for current: port 1 carries 9 servos. Keep the cable from the adapter to servo 20 and to servo 30 as short as the CAD allows, and measure the voltage at servo 24 and 33 under load [I].

## 3. Raspberry Pi Zero 2 W header (physical pin, BCM GPIO)

| Device | Signal | Pi pin | Tag | Note |
|---|---|---|---|---|
| BNO055 (Adafruit 4646) | VIN | pin 1 (3V3) | [U] | |
| BNO055 | GND | pin 9 | [U] | |
| BNO055 | SDA | pin 3 (GPIO2) | [U] | I2C1 |
| BNO055 | SCL | pin 5 (GPIO3) | [U] | I2C1 |
| BNO055 | 3VO, RST | not connected | [U] | |
| Left foot switch (Omron SS-10) | signal | pin 15 (GPIO22) | [U] | feet_contacts.py: left D22 (match) |
| Right foot switch | signal | pin 13 (GPIO27) | [U] | feet_contacts.py: right D27 (match) |
| Foot switches | GND | pin 9 | [U] | |
| Left eye LED | anode | pin 16 (GPIO23) | [U] table | eyes.py has LEFT_EYE = D24 (swapped vs table) |
| Right eye LED | anode | pin 18 (GPIO24) | [U] table | eyes.py has RIGHT_EYE = D23 (swapped vs table) |
| Projector LED | anode | pin 22 (GPIO25) | [U] | projector code D25 (match) |
| Eyes and projector | common cathode | pin 6 (GND) | [U] | series resistor value not stated upstream [I] |
| Left antenna SG90 | PWM | pin 32 (GPIO12) | [U] table | antennas.py has LEFT = D13 (swapped vs table) |
| Right antenna SG90 | PWM | pin 33 (GPIO13) | [U] table | antennas.py has RIGHT = D12 (swapped vs table) |
| Antennas | 5 V, GND | pin 2, pin 6 | [U] | SG90 current comes from the Pi 5 V rail, so the UBEC must cover it |
| MAX98357A (Adafruit 3006) | LRC | pin 35 (GPIO19) | [U] | I2S |
| MAX98357A | BCLK | pin 12 (GPIO18) | [U] | |
| MAX98357A | DIN | pin 40 (GPIO21) | [U] | |
| MAX98357A | VIN, GND | pin 2 (5V), pin 6 | [U] | GAIN and SD not connected |
| Speaker 8 ohm | + / - | MAX98357A out | [U] | |
| Camera | CSI | Pi Zero camera connector (22-pin mini CSI) | [U] picamzero in Runtime, [I] cable | not integrated upstream |
| Microphone | not stated | not stated | [U] shown in diagram only | model and interface unknown |

Eyes and antennas: wire to the code, not the table, or swap the pin numbers in eyes.py and antennas.py. Either way the left and right sides will be swapped if you mix them [U code vs table].

## 4. Wire gauge summary

| Run | Max current | Gauge | Part |
|---|---|---|---|
| Pack, BMS, XT30, fuse, switch, BEC input | about 11 A continuous at 10 A out, 20 A bursts | 16 AWG silicone | BNTECHGO SW16A252008F25C2 (Amazon B01MCRY7OT) [L] |
| BEC output to adapter | 15 A continuous max (BEC rating, with airflow) | 16 AWG | same [L] |
| BMS balance lead | under 0.1 A | 22 AWG | any [I] |
| UBEC in and out | about 1 to 2 A | 20 AWG | any [I] |
| Servo bus | up to about 5 A per chain while walking | cables shipped with STS3215 | Feetech [U] |
| GPIO, I2C, I2S | mA | 26 AWG Dupont | any [I] |

## 5. Lab change parts (see BOM.md, "Lab change" table)

- Castle Creations CC BEC Pro, P/N 010-0004-01, set to 7.2 V.
- Castle Link V4 USB Programming Kit, P/N 011-0173-00 (Windows 10+ PC, Castle Link 2 software) to set the voltage.
- Littelfuse FHAC0001ZXJ inline ATO holder, 20 A, 32 V, 16 AWG leads.
- Littelfuse 0287015.PXCN, ATO 15 A, 32 V.
- BNTECHGO 16 AWG silicone wire, red and black, 25 ft each.

## 6. Open checks before power on

1. Program the BEC to 7.2 V and measure it with no load before connecting the adapter.
2. Measure the drop across the spring holder at a 10 A load (issue #51). If it is above about 0.3 V, replace the holder with a spot-welded 2S pack.
3. Confirm the switch is rated for 15 A DC.
4. Confirm eye and antenna pin mapping against the Runtime code you run.
5. Confirm the head chain branch point on the CAD.
