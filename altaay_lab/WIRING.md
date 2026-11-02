# WIRING: Open Duck Mini v2, altaay-lab build

Last updated: 2026-11-01 (America/New_York). Follows the wiring decisions D8 to D13, D15 and D17 in DECISIONS.md (D15, 6:48 PM ET, replaced D14; D17, 7:24 PM ET).

Source of truth: wiring/netlist.yaml (every part, pin, wire, colour, cut length and expected current; schema at the top of the file). The drawings are generated from it and stop with an error if a netlist cable is missing:
- wiring/odm_v2_wiring_pictorial.svg and .png (make_pictorial.py, A2): every wire drawn terminal to terminal in its colour, parts drawn with their real connectors and printed labels, placed by body region.
- wiring/odm_v2_schematic.svg and .png (make_schematic.py, A3): electrical schematic with the Pi header table.
- wiring/odm_v2_harness.svg and .png (make_harness.py, A3): routing by body region, joints crossed, cut list.

Superseded: wiring/make_wiring.py and wiring/odm_v2_wiring.png and .svg (old block diagram with the AITRIP BMS, an unrated switch, the head chain on adapter port 1 and the upstream GPIO table). Kept for history. Do not wire from them.

Tags used below:
- [U] upstream (Open_Duck_Mini docs/assembly_guide.md, Runtime code at 376de65, Tnkr guide).
- [L] lab decision: D3 (Ahmed, servo regulator, fuse, 16 AWG) and D8 to D13, D15, D17 (made under Ahmed's delegation, DECISIONS.md).
- [I] inferred by us, not stated upstream or by a vendor. Check on the real build.

All drawings show the robot seen from behind: robot left is on the left.

## 1. Power path

| Step | From | To | Cable | Part, connector | Tag |
|---|---|---|---|---|---|
| 1 | Cell 1 - / series strap / cell 2 + | 2x Molicel INR18650-P30B in series | holder | 2S spring holder B09WCT8672 | [U] holder, [L] cells |
| 2 | Holder + / series strap (MID) / holder - | BMS B+ / B1 / B- | P1 16 AWG, P3 26 AWG, P2 16 AWG | solder | [L] (B27: MID from the strap) |
| 3 | BMS: Tenergy P/N 32175 (board RYD-02S-032). 10 A working, over-current detect 22 +/- 5 A, loop 25 mOhm max, 34 x 16 x 4.5 mm, no balancing | | | pads from the Tenergy product image: B-, B1 (mid tap), B+, P-, P+, T (NTC output) | [L] D10 |
| 4 | BMS P+ / P- | USB-C charger B+ / B- | P4 / P5 20 AWG | Adeept B0BJTW4QBR, solder | [U] |
| 5 | BMS P+ / P- | XT30U female + / - | P6 / P8 16 AWG | Amass XT30U, solder cups | [U] |
| 6 | XT30U male + | fuse holder lead 1, lead 2 to 2815 VIN | P7 (the 2 holder leads, 16 AWG, 90 mm each) | Littelfuse 0287015.PXCN 15 A ATO in FHAC0001ZXJ (50 x 17.2 x 17.2 mm) | [L] D3 |
| 7 | XT30U male - | splice G | P14 16 AWG | solder splice, heat shrink | [L] |
| 8 | Pololu 2815 VOUT | splice VSW (switched pack, 6.0 to 8.4 V) | P9 16 AWG | solder in the large hole | [L] D8 |
| 9 | 2815 SW pad + its GND pad (pair marked with a switch symbol) | stock panel switch in the body_back cutout | P15 26 AWG x2 | solder lugs; use the 2 lugs that close when ON [I] | [L] D8 |
| 10 | splice G | 2815 GND (large hole) | P16 20 AWG | control ground only [I] | [L] |
| 11 | VSW / G | Castle CC BEC Pro input red / black | P10 16 AWG x2 | solder to the BEC leads | [L] D3 |
| 12 | BEC output: both 3-pin leads cut, reds joined (JB+), blacks joined (JB-) | belly power splices SPV / SPG | P11 16 AWG x2, 60 mm | solder, adhesive heat shrink; third wires insulated [I] | [L] D15 |
| 13 | SPV / SPG | first servo of each chain, BUS 2 V and G | SP1 (ID 20), SP2 (ID 10), SP3 (ID 30), 22 AWG pairs | Molex 50-37-5033 + 08-70-1040 (22 to 28 AWG) | [L] D15 |
| 14 | VSW / G | Pololu D30V30F5 VIN / GND on the head floor | P13 20 AWG x2, up the neck | solder | [L] D4, D8 |
| 15 | D30V30F5 VOUT / GND | Pi pin 2 (5 V) / pin 6 (GND) | P12 20 AWG x2 | solder to the header | [L] D8 |
| 16 | Pi pin 4 (5 V) / pin 14 (GND) | head splices J5 / JG, then both SG90 and the MAX98357A | P17 20 AWG x2 | solder splices | [L] D8, [I] pin 14 |

Grounds: every ground is common and returns to BMS P- (splice G, P14, XT30, P8). B- and P- are separate nodes on the Tenergy board: nothing but the cell goes on B- [L].

BMS T pad: NTC output. Left unconnected and insulated; that it may be left open is [I] (Tenergy does not say).

Battery cut-off: the Tenergy over-discharge cut is 2.40 V per cell, below the P30B 2.5 V minimum. The robot must stop in software when the servo Present Voltage reads about 6.0 V (about 3.3 V per cell loaded) [L].

Main switch: the 2815 carries the pack current; its on-board slide switch stays OFF and the stock panel switch pulls the SW pad to GND (Pololu: "connect the alternate switch between ground and the switch control terminal"). It carries about 84 uA at 8.4 V (100 kOhm in the Pololu schematic) [I]. ON pin not connected. Pololu warns it is not an emergency cutoff: the XT30 is the disconnect. Ratings: 6 A with the MOSFETs at 55 C, 16 A at 150 C, 90 A max (12 V, 22 C, still air), 20.3 x 22.9 mm, no mounting holes (the four 2.18 mm holes are power connections). Solder 16 AWG into the large holes (Pololu: use them above 5 A).

Charging: the charger sits on BMS P+/P- ahead of the XT30, so it charges with the switch OFF or the XT30 open.

BEC: set to 7.2 V with Castle Link V4 through the BEC Link Port (supplied 2-wire jumper, BEC powered at 5 V or more) (Castle guide 095-0047-00). Below about 7.3 V of pack the output follows the input (dropout not published, measure it).

5 V regulator (D4, D8): Pololu D30V30F5 (#4892), on the head floor below the Pi. The neck carries pack voltage at lower current, so the neck drop does not reach the Pi. Picked from Pololu step-downs in stock on pololu.com on 2026-11-01 (numbers read from the Pololu product graphs: typical, room temperature, still air):

| Part | Stock shown on pololu.com | At 6.0 V in | Verdict |
|---|---|---|---|
| D30V30F5 (#4892) | 505 in stock | about 3.8 A continuous, dropout 0.28 V at 2.5 A (0.34 V at 3 A); 17.8 x 20.3 x 9 mm | chosen |
| D24V22F5 (#2858) | 78 in stock | about 2.4 A continuous | rejected: under 2.5 A |
| D36V28F5 (#3782) | 168 in stock | dropout 1.22 V at 2.5 A, so about 4.8 V out | rejected: dropout |
| D36V50F5 (#4091) | 368 in stock | dropout 0.89 V at 2.5 A, 25.4 x 25.4 mm | rejected: little margin, size |
| S13V30F5 (#4082) | 231 in stock | buck-boost, about 3.6 A, no dropout | backup |

## 2. Servo bus (D15: servo power bypasses the adapter)

Why: the adapter schematic marks "MAX:6A" at the servo header (all servo current would pass its screw terminal and an AO4407 MOSFET), its input spec is 9 to 12.6 V, and the lead's ngspice power-path sim (sim pass only) shows BEC output peaks of 8.3 to 9.1 A while walking.

| Chain | Power (V, G) | Data (D) and its GND | Then kit cables | Tag |
|---|---|---|---|---|
| Left leg: 20 L hip_yaw, 21, 22, 23, 24 L ankle | SP1 from SPV/SPG to ID 20 BUS 2 | adapter H3 D through the data Y splice YD3 (SD1 branch a); H3 G through YG3, joined to the SP1 ground at JG20 | S2, S3, S4, S5 | [L] D15, [U] IDs |
| Neck: 30 neck_pitch, 31 head_pitch, 32 head_yaw, 33 head_roll | SP3 to ID 30 BUS 2 | H3 D through YD3 (SD1 branch b); H3 G through YG3, joined at JG30 | S11, S12, S13 | [L] D15, [U] IDs |
| Right leg: 10 R hip_yaw, 11, 12, 13, 14 R ankle | SP2 to ID 10 BUS 2 | adapter H5 D (SD2); H5 G joined at JG10 | S7, S8, S9, S10 | [L] D15, [U] IDs |

- Adapter: H3 and H5 get a Molex 50-37-5033 housing with only D and G (V position empty). H1 screw terminal NOT connected. Jumper on B (USB). Its 3.3 V logic runs from USB VBUS through diodes (Waveshare schematic). Bench check: the adapter must enumerate and drive the bus with H1 unpowered.
- H3 and H5 are in parallel and the board does not print which socket is which [I], so either socket can take either lead.
- Each first-servo housing has one wire per terminal; the two grounds are spliced before the housing (JG20, JG30, JG10).
- Ports: in on BUS 2, out on BUS 1 (Tnkr). The last servo of each chain (24, 33, 14) has BUS 1 free. Kit cable: 5264-3P, 150 mm, 1:1. S1, S6 and S14 are gone.
- Bus data and bus power share the servo ground; the data line is 3.3 V logic from the adapter buffers.

## 3. Raspberry Pi Zero 2 W header (D9: wired to the Runtime code at 376de65)

Eyes and antennas are swapped compared with the upstream assembly_guide pin table. We follow the code: eyes.py LEFT_EYE_PIN = D24, RIGHT_EYE_PIN = D23; antennas.py LEFT = D13, RIGHT = D12; feet_contacts.py left D22, right D27 with pull-up; projector.py D25.

| Pi pin | Signal | Goes to | Cable | Tag |
|---|---|---|---|---|
| 1 | 3V3 | BNO055 VIN | D2 | [U] |
| 2 | 5V in | U3 VOUT | P12 | [L] |
| 3 | GPIO2 SDA | BNO055 SDA | D2 | [U] |
| 4 | 5V out | splice J5 (SG90 x2 +, amp Vin) | P17 | [L] |
| 5 | GPIO3 SCL | BNO055 SCL | D2 | [U] |
| 6 | GND | U3 GND | P12 | [L] |
| 9 | GND | BNO055 GND, left and right foot COM | D2, D3, D4 | [U] (3 x 26 AWG: twist and tin [I]) |
| 12 | GPIO18 | MAX98357A BCLK | D10 | [U] |
| 13 | GPIO27 | right foot NO (2 x Omron SS-01, SS-10 fallback, in parallel); R5 2.2 kOhm to pin 17 | D4 | [U] code, [L] D17 |
| 14 | GND | splice JG (SG90 x2 -, amp GND) | P17 | [I] (pin 6 holds the U3 ground) |
| 15 | GPIO22 | left foot NO (2 x Omron SS-01, SS-10 fallback, in parallel); R4 2.2 kOhm to pin 17 | D3 | [U] code, [L] D17 |
| 17 | 3V3 | R4 and R5, 2.2 kOhm pull-ups, leads soldered at the header (17 to 15, 17 to 13) | D3, D4 | [L] D17 |
| 16 | GPIO23 | right eye: 100 ohm, then LED + | D6 | [U] code |
| 18 | GPIO24 | left eye: 100 ohm, then LED + | D5 | [U] code |
| 20 | GND | the 3 LED cathodes | D5, D6, D7 | [I] |
| 22 | GPIO25 | projector: 100 ohm (added by D13), then LED + | D7 | [U] code, [L] D13 |
| 32 | GPIO12 | right antenna SG90 signal | D9 | [U] code |
| 33 | GPIO13 | left antenna SG90 signal | D8 | [U] code |
| 35 | GPIO19 | MAX98357A LRC | D10 | [U] |
| 40 | GPIO21 | MAX98357A DIN | D10 | [U] |
| USB port | OTG data | adapter USB-C, /dev/ttyACM0 at 1 Mbaud | D1 (Adafruit 3878, 0.9 m, slack coiled in the belly) | [U], [L] cable |
| CSI | camera | Camera Module 3 (Adafruit 5657) | D12 (Adafruit 3157, 150 mm) | [U] |

- GND pins 6, 9, 14, 20, 25, 30, 34, 39 are one net and 5 V pins 2 and 4 are tied to the Pi power input (pinout.xyz). Leave the PWR IN port empty [I].
- LEDs (D13): eyes as upstream, GPIO through 100 ohm, about 3 mA, dim but inside GPIO limits; the projector gets the same 100 ohm (upstream issue 34 warns about 1 W LEDs straight on GPIO). Brighter LEDs with MOSFET drivers are a later step.
- Feet (D17, 7:24 PM ET): the Runtime puts feet_contacts into the policy observation (scripts/v2_rl_walk_mujoco.py lines 154 and 167), so contact reliability matters for walking. Omron SS datasheet: SS-01 gold alloy crossbar contacts, 0.1 A, minimum load 5 VDC 1 mA; SS-10 silver contacts, minimum load 5 VDC 160 mA; same housing. Use SS-01 where in stock at order time, SS-10 as the fallback. Either way add one 2.2 kOhm pull-up per foot (Adafruit 2782, BOM 13b) from pin 17 (3V3) to the foot input, so a closed foot carries about 1.5 mA (3.3 V / 2.2 kOhm) instead of about 60 uA from the internal pull-up.
- BNO055 3VO and RST, MAX98357A GAIN and SD: not connected [U]. Speaker: Same Sky CMS0361KLX, 8 ohm, 2 W, on the amp + and - (D11).
- IMU and the BEC: the walk script (scripts/v2_rl_walk_mujoco.py) uses raw_imu.py, which sets NDOF mode, and the policy reads only the raw gyro and accelerometer, so the BEC near the IMU does not affect the policy inputs [U code].

## 4. Wire gauges and expected current (sim pass only, sim/CURRENT_BUDGET.md, pack at 7.4 V)

| Run | Mean | Worst 100 ms | Fall, 20 ms | Gauge |
|---|---|---|---|---|
| Pack path P1, P2, P6, P7, P8, P14, P9 | 4.2 A | 7.5 A | up to 17 A | 16 AWG |
| BEC input P10 | 3.75 A | 5.62 A | 14.6 A | 16 AWG |
| BEC output P11 (bus current) | 3.19 A | 4.78 A | 12.5 A | 16 AWG; ngspice: 8.3 to 9.1 A peaks |
| SP1, SP2, SP3 | not simulated per branch | | | 22 AWG (terminal limit) |
| 5 V feed P13 (neck) | 0.48 A | 1.91 A | | 20 AWG |
| 5 V out P12 | 0.6 A | 2.4 A | | 20 AWG |
| P17 to the SG90s and amp | | 1.9 A [I] | | 20 AWG |
| Control P15, P16 | under 1 mA | | | 26 AWG, 20 AWG |
| Foot pull-ups R4, R5 (D17) | 1.5 mA per closed foot | | | resistor leads at the header |
| Data D2 to D12, SD1, SD2 | mA | | | 26 AWG, 22 AWG |

Real servos may draw up to 2 x the sim numbers until a bench log exists (CURRENT_BUDGET.md). Insulation colours: netlist.yaml (lab plan [I] where the part does not ship with leads).

## 5. Parts set by the wiring decisions (BOM.md has the buy lines and prices)

- Tenergy P/N 32175 2S protection board (D10).
- Pololu 2815 Big MOSFET Slide Switch HP (D8); the stock panel switch only controls it.
- Pololu D30V30F5 5 V step-down, #4892 (D4, D8). BOM line 9 still shows the HENGE UBEC: update it.
- Castle Creations CC BEC Pro 010-0004-01 at 7.2 V, Castle Link V4 011-0173-00 (D3).
- Littelfuse FHAC0001ZXJ holder and 0287015.PXCN 15 A ATO fuse (D3).
- Adafruit 3878 USB cable, 0.9 m (D1); Same Sky CMS0361KLX speaker (D11).
- Omron SS-01 foot switches, SS-10 as the fallback (D17); 2 x 2.2 kOhm 1/4 W, Adafruit 2782 (BOM 13b).
- 22 AWG wire for SP1 to SP3 and SD1, SD2; Molex 50-37-5033 housings and 08-70-1040 terminals (5 housings, 13 terminals used).

## 6. Checks before power on

1. Program the BEC to 7.2 V and measure it with no load.
2. Check U3 gives 5 V with no load before connecting the Pi; then 2.5 A at 6.0 V in on a bench supply.
3. Adapter with H1 unpowered: it enumerates as /dev/ttyACM0 and reads every servo ID.
4. 2815 slide switch OFF; the robot is off with the panel switch open; the panel switch lugs that close are the ones used.
5. Measure the drop across the spring holder at 10 A (issue #51); replace with a welded pack if over about 0.3 V.
6. Nothing on BMS B- except the cell; T pad insulated.
7. Feet (D17): fit SS-01 if it was in stock, else SS-10; with R4 and R5 a closed foot carries about 1.5 mA. Check both feet read reliably (feet_contacts.py prints them) over a long stand and walk.
8. If you run code other than Runtime 376de65, check the eye, antenna and foot pins against it.
