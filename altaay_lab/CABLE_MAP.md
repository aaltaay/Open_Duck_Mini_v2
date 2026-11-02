# CABLE_MAP

Last updated: 2026-11-02 (America/New_York), wiring decisions D8 to D13, D15, D17 and D23 (D15 replaced D14). One row per cable. The conductor-level data (from pin, to pin, net, gauge, colour, cut length, expected current) is in wiring/netlist.yaml, which is the source of truth; this file and the drawings (wiring/sheets/WIRING_SHEETS.md) follow it. Nothing has been built.

Routes were measured on the upstream URDF/STL assembly (STL commit 730c14b): the route is a polyline through the centres of the parts the cable passes and the joint axes it crosses (audit/cables.py, audit/cables.json). Parts not in the CAD use the centres in audit/placements.json (BEC, fuse holder, Pololu 2815, BMS; MOUNTING.md, D11). The 3D routes, seats, ties and the worst length over the joint ranges of every cable are in cables3d/CABLES_3D.md; the cut lengths changed on 2026-11-02 come from there.

## Length rule (lab design rule, not a measurement)
Cut length = route polyline + 2 x 22.6 mm (connector position tolerance at each end, half of the STS3215 45.2 mm case length) + 2 x 20 mm service slack + 10 mm per radian of joint range crossed (URDF limits).
Lower bound = straight distance minus 45.2 mm. A cable shorter than the lower bound cannot fit; one longer than the rule length always fits; in between needs a test fit.
cables3d check (2026-11-02): cut of a conductor chain >= worst 3D routed length over the joint ranges + 20 mm slack per fixed end, chained through inline splices. A solder splice that no part holds (VSW, G, JFI, JFO, YD3, YG3, JG20, JG10, JG30, J5, JG) floats along the bundle at build time, so the wires joined there are judged together, fixed end to fixed end; SPV and SPG are seated on the belly and JBP, JBN are where the BEC leads end, so they are fixed ends. verify/c3_cables3d.py judges lengths the same way. Cuts marked "3D" below follow it.

## Connector parts
| Use | Housing | Terminal | Wire | Tool |
|---|---|---|---|---|
| STS3215 bus made leads: SP1 to SP3 at the servo, SP4 and SP5 at the ankle BUS 1 (V and G only, D23), SD1 and SD2 at both ends (5264-type 2.5 mm 3-pin sockets on servos and adapter) | Molex 50-37-5033 (Mini-SPOX 3 pos), 7 used | Molex 08-70-1040 (22 to 28 AWG), 17 used, one wire per terminal | 22 AWG | Engineer PA-09 (Molex 5263 in the PA-09/PA-20 chart) |
| Battery disconnect | Amass XT30U male and female | solder cups | 16 AWG | soldering iron |
| Pi header | 2x20 2.54 mm header (pre-soldered or fitted) | solder to the pins; R4, R5 resistor leads go straight onto pins 17-15 and 17-13 (D17) | 20 and 26 AWG | Pinecil V2 |
| Pololu 2815 | large holes (power) and 0.1 in holes (SW pad pair) | solder | 16 AWG, 26 AWG | Pinecil V2 |
| Splices G, VSW, JFI, JFO, JB+, JB-, SPV, SPG, J5, JG, YD3, YG3, JG20, JG30, JG10 | none: solder splice in adhesive heat shrink (YD3, YG3 may be 3-way crimp splices) | | | Pinecil V2 |
| Everything else | none, solder to pads, tabs or holes, heat shrink over each joint | | | Pinecil V2 |

Molex 08-70-1040 terminal data (Molex documents read through distributor copies; molex.com, mouser.com, digikey.com and newark.com were not reachable from this session): wire 22, 24, 26 and 28 AWG; wire insulation diameter 1.90 mm max; current 3.0 A on 22 AWG (2.5 A on 24, 2.0 A on 26, 1.5 A on 28 AWG); contact resistance 20 mOhm max; voltage 250 V; -40 to +105 C; phosphor bronze, tin plated; terminal 7.00 mm long, crimp section 3.50 mm; Molex hand tool 63828-1900. Sources: Molex catalog page MX01 B-101, "2.50mm (.098") Pitch SPOX Wire-to-Board Crimp Terminal 5263" (https://www.rcscomponents.kiev.ua/datasheets/mx5263-datasheet.pdf, read 2026-11-02 1:29 AM ET; its ordering table gives one wire range and insulation entry for 08-70-1039, reel, and 08-70-1040, bag); Molex part sheet 0008701039 generated 10/30/2020: "Packaging Alternative 08701040 (Loose)", "Wire Insulation Diameter 1.90mm max.", "Wire Size AWG 22, 24, 26, 28" (https://static.chipdip.ru/lib/750/DOC031750234.pdf, read 2026-11-02 1:29 AM ET). The 22 AWG silicone wire is 1.7 +/- 0.1 mm (BNTECHGO listing, read 2026-11-02 1:45 AM ET), so 0.1 mm under the maximum at the top of its tolerance. verify/c2_connectors.py checks the netlist against these values.

Splice tails (solder splice in adhesive heat shrink, BOM 26): a splice that no part holds floats along the bundle, so its tail is judged with the leads it joins (length rule below). A 22 AWG tail into a crimp terminal needs at least 15 mm: 3.5 mm inside the terminal crimp section, a lap of 3 to 6 wire diameters (NASA-STD-8739.4A Change 4, 19.4.1 c) and a 15 mm sleeve cut from a 3.5 in (89 mm) Wirefy kit piece (BOM 26 listing: 7 sizes 3/32 to 3/4 in, precut 3.5 in; https://www.amazon.com/dp/B084GDLSCK, read 2026-11-02 1:31 AM ET) that reaches 2 x OD = 3.4 mm onto the insulation (19.2.6). The JG20, JG10 and JG30 tails are 30 mm, so the stiff sleeve sits past the bend at the plug exit (7.2.36); YG3 sits 15 mm past YD3 so the two SD1 sleeves do not overlap (7.2.35).

## A. Servo bus (D15: power from the BEC splices, data from the adapter)
Waveshare Bus Servo Adapter (A) schematic (https://files.waveshare.com/wiki/Bus-Servo-Adapter-(A)/Bus%20Servo%20Adapter%20(A)-Sch.pdf): H3 and H5 are the servo sockets, in parallel, pin 1 DATA, pin 2 V, pin 3 GND (printed D V G on the board). D15: no servo current through the adapter. H3 and H5 carry only DATA and GND (V position empty), H1 is not connected, the jumper is on B (USB).

Every STS3215 has 2 bus ports in parallel. Tnkr: the incoming cable goes into BUS 2, the next leaves from BUS 1. ID 33 has BUS 1 free; ID 24 and ID 14 take SP4 and SP5 on BUS 1 (D23).

Kit cable = the 15 cm 3-pin cable shipped with each STS3215 (14 shipped, 11 used, 3 spare). Cable spec from the Feetech STS3215 sheet (https://www.mantech.co.za/Datasheets/Products/STS3215-200620A.pdf, item 6-7): 5264-3P, 15 cm, pin 1 GND, pin 2 Vcc, pin 3 signal; no gauge given, so it stays as shipped. Waveshare numbers its sockets from the other end (1 D, 2 V, 3 G): copy a kit cable housing for every made lead and check it with a meter. The same sheet says "No Accessories", so confirm on the Seeed order that each servo ships with one (BLOCKER-lite).

| ID | From | To | Conductors | Gauge | Ends | Route (joints crossed) | Polyline | Rule length | Cut | Source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SP1 | splices SPV, SPG (belly) | ID 20 L hip yaw BUS 2 V and G | V, G (G spliced with SD1 at JG20, 20 mm tail) | 22 AWG x2 | solder splice; 50-37-5033 + 08-70-1040 | belly to trunk_bottom, no joints | not measured | not measured | 150 (G 130 + 30) | [L] D15 | feeds the left leg; GND tail 30 mm (splice tails above) |
| SP2 | SPV, SPG | ID 10 R hip yaw BUS 2 V and G | V, G (G joins SD2 at JG10) | 22 AWG x2 | as SP1 | belly to trunk_bottom | not measured | not measured | 150 (G 130 + 30) | [L] D15 | feeds the right leg; GND tail 30 mm |
| SP3 | SPV, SPG | ID 30 neck pitch BUS 2 V and G | V, G (G joins SD1 at JG30) | 22 AWG x2 | as SP1 | belly to trunk_top | not measured | not measured | 180 (G 160 + 30) | [L] D15 | feeds the neck chain; GND tail 30 mm |
| SP4 | SPV, SPG | ID 24 L ankle BUS 1 V and G | V, G (data cavity empty) | 22 AWG x2 | solder splice; 50-37-5033 + 08-70-1040 | belly, trunk_bottom, left leg; crosses left hip yaw, hip roll, hip pitch, knee | 286.5 (3D, zero pose) | worst 348 (3D) | 390 (3D) | [L] D23 | second feed of the left leg |
| SP5 | SPV, SPG | ID 14 R ankle BUS 1 V and G | V, G (data cavity empty) | 22 AWG x2 | as SP4 | as SP4, right leg | 319.3 (3D, zero pose) | worst 377 (3D) | 420 (3D) | [L] D23 | second feed of the right leg |
| SD1 | adapter H3 (D, G) | ID 20 D and JG20 (branch a); ID 30 D and JG30 (branch b) | D, G; data Y at YD3, ground Y at YG3 next to the adapter | 22 AWG x2 | 50-37-5033 with 2 terminals at H3; splices; 50-37-5033 at the servos | trunk_top to trunk_bottom, no joints | adapter to ID 20 63.8, to ID 30 87.3 | a 149.0, b 172.5 | stem D 30, stem G 45 (YG3 staggered 15 mm past YD3), a 130 (G 120), b 170 (3D; G 140) | [L] D15 | stem and branch lengths [I]; b D 170 since the SP3 tail moved JG30 3 mm back |
| SD2 | adapter H5 (D, G) | ID 10 D and JG10 | D, G | 22 AWG x2 | 50-37-5033 at H5 and at ID 10 | trunk_top to trunk_bottom | 63.8 | 149.0 | 150 (G 140) | [L] D15 | |
| S2 | ID 20 BUS 1 | ID 21 L hip roll BUS 2 | kit | kit | 5264 | crosses left_hip_yaw | 56.6 | 152.3 | kit 150 | [U] | BLOCKER test fit (rule 2.3 mm over) |
| S3 | ID 21 | ID 22 L hip pitch | kit | kit | 5264 | crosses left_hip_roll | 82.3 | 176.2 | kit 150 | [U] | BLOCKER test fit |
| S4 | ID 22 | ID 23 L knee | kit | kit | 5264 | crosses left_hip_pitch | 92.1 | 194.8 | kit 150 | [U] | BLOCKER test fit |
| S5 | ID 23 BUS 1 | ID 24 L ankle BUS 2 | kit | kit | 5264 | crosses left_knee | 92.1 | 208.7 | kit 150 | [U] | BLOCKER test fit |
| S7 | ID 10 | ID 11 R hip roll | kit | kit | 5264 | crosses right_hip_yaw | 56.6 | 152.3 | kit 150 | [U] | BLOCKER test fit |
| S8 | ID 11 | ID 12 R hip pitch | kit | kit | 5264 | crosses right_hip_roll | 82.3 | 176.2 | kit 150 | [U] | BLOCKER test fit |
| S9 | ID 12 | ID 13 R knee | kit | kit | 5264 | crosses right_hip_pitch | 91.6 | 194.3 | kit 150 | [U] | BLOCKER test fit |
| S10 | ID 13 | ID 14 R ankle | kit | kit | 5264 | crosses right_knee | 92.1 | 208.7 | kit 150 | [U] | BLOCKER test fit |
| S11 | ID 30 BUS 1 | ID 31 head pitch BUS 2 | kit | kit | 5264 | crosses neck_pitch | 80.0 | 180.0 | kit 150 | [U] | BLOCKER test fit |
| S12 | ID 31 | ID 32 head yaw | kit | kit | 5264 | crosses head_pitch and head_yaw | 106.3 | 263.1 | kit 150 | [U] | BLOCKER test fit (113 mm over rule); contingency X1/X2 made lead 270 mm |
| S13 | ID 32 | ID 33 head roll | kit | kit | 5264 | crosses head_roll (cables.json) | 51.6 | 147.3 | kit 150 | [U] | fits (2.7 mm margin) |

Removed: S1 (kit, H3 to ID 20) and S6 (kit, H5 to ID 10) are replaced by the made first leads SP1 + SD1 and SP2 + SD2; S14 (left ankle to neck) and the D14 Y-lead S14Y were dropped by D15. The left ankle's second port takes SP4 (D23).

Result: 1 kit hop fits by rule (S13), 10 need a test fit (test order 1, B17). Every lower bound is 42 mm or less, so none is ruled out. In 3D every kit hop reaches taut; S2 and S7 miss the 40 mm slack by 22 and 23 mm (cables3d). Contingency X1/X2 in BOM.md (made Mini-SPOX leads, 200 mm for legs and 270 mm for S12).

## B. Power
| ID | From | To | Conductors | Gauge | Ends | Route | Polyline | Rule / cut | Current (mean, worst 100 ms) | Source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | holder + lead | BMS B+ | 1 | 16 AWG red | holder lead, solder pad | battery bay | 30.1 | 115.3 / 120 | 4.2 A, 7.5 A (falls up to 17 A) | [L] placements | use the holder lead if 120 mm or longer |
| P2 | holder - lead | BMS B- | 1 | 16 AWG black | as P1 | battery bay | 30.1 | 115.3 / 120 | as P1 | [L] | |
| P3 | holder series strap | BMS B1 | 1 | 26 AWG yellow [I] | solder | battery bay | 30.1 | 115.3 / 140 (3D) | sense only | [L] B27 | |
| P4 | BMS P+ | charger B+ | 1 | 20 AWG red | solder pads | battery bay | 39.4 | 124.6 / 130 | 2 A while charging (seller) | [U] | |
| P5 | BMS P- | charger B- | 1 | 20 AWG black | solder pads | battery bay | 39.4 | 124.6 / 130 | as P4 | [U] | |
| P6 | BMS P+ | XT30U female + | 1 | 16 AWG red | solder pad, XT30 cup | battery bay | 23.5 (BMS to fuse) | 108.7 / 150 (3D) | 4.2 A, 7.5 A | [L] | XT30 seated left of the holder as Tnkr places it (cables3d) |
| P8 | BMS P- | XT30U female - | 1 | 16 AWG black | as P6 | battery bay | 23.5 | 108.7 / 150 (3D) | as P6 | [L] | |
| P7 | XT30U male + | fuse holder lead 1; lead 2 to 2815 VIN | 4: the holder leads (90 mm each) and 16 AWG red extensions at splices JFI (30) and JFO (40) | 16 AWG | XT30 cup, splices, solder in the 2815 large hole | battery bay | 42.0 (fuse to 2815) | 127.2 / line 30 + 90, load 90 + 40 (3D) | as P6 | [L] D3 | the holder leads alone are short of both chains (cables3d); the JFI extension is 30 mm so both splice sleeves fit |
| P14 | XT30U male - | splice G | 1 | 16 AWG black | XT30 cup, splice | battery bay | 52.1 (BMS to 2815) | 137.3 / 140 | as P6 | [L] | |
| P9 | 2815 VOUT | splice VSW | 1 | 16 AWG red | large hole, splice | battery bay | 0 (splice at the 2815) | 85.2 / 90 | as P6 | [L] D8 | |
| P16 | splice G | 2815 GND (large hole) | 1 | 20 AWG black | splice, large hole | battery bay | 0 | 85.2 / 90 | under 1 mA | [I] | control ground only |
| P15 | 2815 SW pad and its GND pad | stock panel switch, 2 lugs | 2 | 26 AWG white, black [I] | 0.1 in holes, solder lugs | battery bay | 62.1 (2815 to power_switch.stl) | 147.3 / 150 | about 84 uA | [L] D8 | |
| P10 | splices VSW, G | BEC input red, black | 2 | 16 AWG red, black | splice, BEC leads | battery bay to belly | 61.1 (2815 to BEC) | 146.3 / 150 | 3.75 A, 5.62 A (falls 14.6 A) | [L] D3 | BEC input leads ship (length not published): shorten P10 by their length |
| P11 | BEC outputs, both 3-pin leads joined (JB+, JB-) | belly splices SPV, SPG | 2 | 16 AWG red, black (BEC leads as shipped) | splices | belly | not measured | 100 (3D) | 3.19 A, 4.78 A (falls 12.5 A; ngspice 8.3 to 9.1 A peaks) | [L] D15 | third wires insulated [I] |
| P13 | splices VSW, G | U3 D30V30F5 VIN, GND (head floor) | 2 | 20 AWG red, black | splice, U3 holes | battery bay, trunk_top, neck, head; crosses neck_pitch, head_pitch, head_yaw, head_roll (9.69 rad) | 349.7 (2815 to Pi) | 531.7 / 550 each | 0.48 A, 1.91 A (0.55 A, 2.21 A at 6.4 V pack) | [L] D8 | drop about 0.09 V at 2.5 A over 2 x 0.55 m [I] |
| P12 | U3 VOUT, GND | Pi pin 2 (5 V), pin 6 (GND) | 2 | 20 AWG red, black | U3 holes, Pi header | head | 44.3 (U3 under the Pi) | 129.5 / 130 each | 0.6 A, 2.4 A | [L] D8 | U3 exact spot on the floor not fixed |
| P17 | Pi pin 4 (5 V), pin 14 (GND) | head splices J5, JG | 2 | 20 AWG red, black | Pi header, splice | head | 0 | 85.2 / 90 each | peak 1.9 A [I] | [L] D8, [I] pin 14 | feeds both SG90 and the amp |

## C. Data and signal
Pi Zero 2 W hangs from the upper inner wall of head.stl, components down (MOUNTING.md). Pins follow the Runtime code at 376de65 (D9), not the assembly_guide table (eyes and antennas swapped there).

| ID | From | To | Signal | Gauge | Ends | Route | Polyline | Rule length / cut | Source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Pi micro-USB data port (USB) | adapter USB-C | USB 2.0, /dev/ttyACM0 | Adafruit 3878, 0.9 m | micro-B to USB-C | head, neck, trunk_top; 4 neck joints | 320.5 | 502.6 / 900 cable | [L] parts check | coil the slack in the belly (B18 cleared by the longer cable) |
| D2 | Pi pins 1, 9, 3, 5 | BNO055 VIN, GND, SDA, SCL | I2C 3.3 V | 26 AWG x4 (red, black, blue, yellow [I]) | solder | head, neck, trunk_top; 4 neck joints | 329.3 | 511.4 / 550 each | [U] | |
| D3 | Pi pin 15 (GPIO22), pin 9 (GND); R4 2.2 kOhm from pin 17 to pin 15 at the header (D17) | left foot, 2 x Omron SS-01 (SS-10 fallback) in parallel (COM to COM, NO to NO, Tnkr m11) | contact, about 1.5 mA closed | 26 AWG x2 (green, black [I]) + 110 mm jumpers (3D) | solder | head to left foot: 4 neck + 5 leg joints, 19.64 rad | 602.4 | 884.0 / 900 each | [U] code (D9) | Seat: 2 slots 6.4 x 19.8 mm in foot_top, 50 mm apart |
| D4 | Pi pin 13 (GPIO27), pin 9; R5 2.2 kOhm from pin 17 to pin 13 at the header (D17) | right foot, 2 x Omron SS-01 (SS-10 fallback) in parallel | contact, about 1.5 mA closed | 26 AWG x2 (white, black [I]) + 110 mm jumpers (3D) | solder | as D3 mirrored | 632.4 | 914.0 / 950 each | [U] code (D9) | |
| D5 | Pi pin 18 (GPIO24), pin 20 (GND) | left eye: 100 ohm in series, then LED + | LED, about 3 mA | 26 AWG x2 | solder, resistor inline at the LED [I] | inside head | 94.8 | 134.8 / 150 | [U] code, [L] D13 | |
| D6 | Pi pin 16 (GPIO23), pin 20 | right eye: 100 ohm, LED | LED | 26 AWG x2 | as D5 | inside head | 176.8 | 216.8 / 230 | [U] code, [L] D13 | |
| D7 | Pi pin 22 (GPIO25), pin 20 | projector: 100 ohm (added by D13), LED | LED | 26 AWG x2 | as D5 | inside head, through the 4 mm hole drilled in the head wall (D24) | 112.4 | 152.4 / 160 | [U], [L] D13 | upstream issue 34: no 1 W LED straight on GPIO |
| D8 | left antenna SG90 lead | Pi pin 33 (GPIO13), splices J5 and JG | PWM 5 V | SG90 lead | servo lead, solder at the Pi end | inside head | 133.2 | 173.2 / lead 250 | [U] code (D9) | fits |
| D9 | right antenna SG90 lead | Pi pin 32 (GPIO12), splices J5 and JG | PWM 5 V | SG90 lead | as D8 | inside head | 228.0 | 268.0 / lead 250 | [U] code (D9) | fits without an extension: 170 mm worst in 3D |
| D10 | Pi pins 35 (LRC), 12 (BCLK), 40 (DIN); splices J5 (Vin), JG (GND) | MAX98357A | I2S, 5 V | 26 AWG x5 | solder | inside head | 149.5 | 189.5 / LRC, BCLK 210, DIN 220 (3D), Vin, GND 220 (3D) | [U] | GAIN and SD not connected |
| D11 | MAX98357A + and - | speaker Same Sky CMS0361KLX (8 ohm, 2 W) | audio | 26 AWG x2 | amp terminal block, solder tabs | inside head | about 40 | 80 / 120 (3D) | [L] parts check | |
| D12 | Pi CSI | Camera Module 3 | MIPI CSI | Adafruit 3157 cable 150 mm | FPC | inside head | 3D worst 127 | 150 cable | [U] BOM E7 | 23 mm spare, under the 40 mm slack: test fit (TO9). Proposal, BOM E7 not changed: Adafruit 5818, the Raspberry Pi Standard-Mini camera cable, 200 mm, 22-pin 0.5 mm to 15-pin 1 mm, $2.70, in stock (https://www.adafruit.com/product/5818, read 2026-11-02 1:46 AM ET; Raspberry Pi MPN SC1892, listed for the Pi 5, Zero and CM4 by https://www.kiwi-electronics.com/en/raspberry-pi-camera-cable-standard-mini-200mm-11588, read 1:46 AM ET): 73 mm spare |

## Wire totals (cut lengths from netlist.yaml, with 10% spare)
| Gauge | Rows | Sum | With spare | Bought |
|---|---|---|---|---|
| 16 AWG | P1, P2, P6, P8, P9, P10, P11, P14, P7 extensions (P7 holder leads ship) | 1.33 m | 1.46 m | 50 ft (BOM L5) |
| 20 AWG | P4, P5, P12, P13, P16, P17 | 1.89 m | 2.08 m | 50 ft (BOM 23) |
| 22 AWG | SP1 to SP5, SD1, SD2 | 3.48 m | 3.83 m | 150 ft (BOM 24) |
| 26 AWG | P3, P15, D2 to D7, D10, D11 | 9.14 m | 10.05 m | 175 ft (BOM 25) |

## Ships with a component vs made vs bought
- Ships: 11 of the 14 kit servo cables (3 spare), SG90 leads, BEC input and output leads, fuse holder leads (P7, lengthened at JFI and JFO), holder leads (P1, P2 if long enough). Their gauges are not published: as shipped.
- Bought: D1 (Adafruit 3878, 0.9 m), D12 (Adafruit 3157).
- Made: SP1 to SP5, SD1, SD2, P1 to P17 (P7 only its two extensions), D2 to D11.
