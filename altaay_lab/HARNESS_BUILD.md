# Harness build sheet

Generated 2026-11-05 01:42 UTC by altaay_lab/wiring/make_harness_build.py from wiring/netlist.yaml and cables3d/cables3d.json. Do not edit by hand.

How to use it:
- Build in the order below, one cable at a time. Cut every wire to the length shown; lengths include the end allowance used in the netlist.
- Label both ends of every cable with its ID before installing (a marker on a short piece of heat shrink works).
- Test each finished cable with its continuity lines (beep and no-short checks) before it goes into the robot (TEST_PLAN.md section 2).
- Never plug or unplug anything with power on (upstream issue 49).
- Tools and stock: crimper BOM T3, stripper T5, iron T1, heat shrink 26, wire L5 (16 AWG), 23 (20 AWG), 24 (22 AWG), 25 (26 AWG), Mini-SPOX housings 21 and terminals 22, XT30U 12, solder and cable ties (BOM_FULL.md K01, K02).
- Seats and ties: where a cable passes or is tied to a printed part. From altaay_lab/cables3d (3D routing, sim pass only).

## 1. Battery bay power

### P1: holder + to BMS B+

Regions: battery_bay. Crosses joints: none. use the holder lead if 120 mm or longer

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PACK.B+ (BT1 pack + (cell 2 +)) | BMS.B+ (U5 cell stack +) | 16 AWG | red | 120 | use the part's own lead (holder lead), solder joint covered with heat shrink | tin and solder to BMS.B+, heat shrink if bare |

Test: PACK.B+ to BMS.B+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PACK.B-

Seats on the brackets, end to end: channel body_back; edge body_back; edge body_back; channel body_back; channel battery_pack_lid; edge body_back; none (free air); edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back; edge body_back
Reach check (cables3d, by conductor chain): pass with notes, worst routed 56.3 mm, cut 120 mm.

### P2: holder - to BMS B-

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PACK.B- (BT1 pack - (cell 1 -)) | BMS.B- (U5 cell stack -) | 16 AWG | black | 120 | use the part's own lead (holder lead), solder joint covered with heat shrink | tin and solder to BMS.B-, heat shrink if bare |

Test: PACK.B- to BMS.B-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PACK.B+

Seats on the brackets, end to end: channel body_back; edge body_back; edge body_back; channel body_back; channel battery_pack_lid; edge body_back; none (free air); edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back; edge body_back
Reach check (cables3d, by conductor chain): pass with notes, worst routed 56.3 mm, cut 120 mm.

### P3: holder series strap to BMS B1

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PACK.MID (BT1 series strap (cell 1 + / cell 2 -)) | BMS.B1 (U5 mid tap (called BM in the brief)) | 26 AWG | yellow | 140 | solder to strap | tin and solder to BMS.B1, heat shrink if bare |

Test: PACK.MID to BMS.B1: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge body_back; channel battery_pack_lid; none (free air); edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; channel body_back
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T001 stick-on mount ABM1M-AT-C (BOM 34b) on battery_pack_lid, 2 mm from the cable line; T002 stick-on mount MB3A (BOM 34) on battery_pack_lid, 16 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 98.7 mm, cut 140 mm.

### P4: BMS P+ to charger B+

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P+ (U5 pack output + (charge and discharge)) | CHG.B+ (U6 charge output +) | 20 AWG | red | 130 | tin and solder to BMS.P+, heat shrink if bare | tin and solder to CHG.B+, heat shrink if bare |

Test: BMS.P+ to CHG.B+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P- BMS.T

Seats on the brackets, end to end: channel body_back; edge body_back
Reach check (cables3d, by conductor chain): pass, worst routed 10.7 mm, cut 130 mm.

### P5: BMS P- to charger B-

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P- (U5 pack output - (charge and discharge)) | CHG.B- (U6 charge output -) | 20 AWG | black | 130 | tin and solder to BMS.P-, heat shrink if bare | tin and solder to CHG.B-, heat shrink if bare |

Test: BMS.P- to CHG.B-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P+ BMS.T

Seats on the brackets, end to end: channel body_back; edge body_back
Reach check (cables3d, by conductor chain): pass, worst routed 10.7 mm, cut 130 mm.

### P6: BMS P+ to XT30U female +

Regions: battery_bay. Crosses joints: none. BLOCKER-lite: XT30 spot from Tnkr only

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P+ (U5 pack output + (charge and discharge)) | XT30.F+ (J1 pack side +) | 16 AWG | red | 150 | tin and solder to BMS.P+, heat shrink if bare | solder into the XT30U cup, heat shrink over the cup |

Test: BMS.P+ to XT30.F+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P- BMS.T

Seats on the brackets, end to end: channel body_back; none (free air); edge body_back; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T003 stick-on mount MB3A (BOM 34) on battery_pack_lid, 15 mm from the cable line; T004 stick-on mount MB3A (BOM 34) on battery_pack_lid, 3 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 100.2 mm, cut 150 mm.

### P8: BMS P- to XT30U female -

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P- (U5 pack output - (charge and discharge)) | XT30.F- (J1 pack side -) | 16 AWG | black | 150 | tin and solder to BMS.P-, heat shrink if bare | solder into the XT30U cup, heat shrink over the cup |

Test: BMS.P- to XT30.F-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P+ BMS.T

Seats on the brackets, end to end: channel body_back; none (free air); edge body_back; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T003 stick-on mount MB3A (BOM 34) on battery_pack_lid, 15 mm from the cable line; T004 stick-on mount MB3A (BOM 34) on battery_pack_lid, 3 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 100.2 mm, cut 150 mm.

### P7: XT30U male + to fuse holder to Pololu 2815 VIN (the holder leads)

Regions: battery_bay. Crosses joints: none. holder leads ship at 90 mm, short of both chains (cables3d: line 92, load 124 mm): each gets a 16 AWG red extension at splice JFI or JFO

Twist: none (the two made pieces (XT30 to JFI, JFO to the 2815) are in series through the fuse holder, not a pair).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | XT30.M+ (J1 robot side +) | JFI.S (JFI splice) | 16 AWG | red | 30 | solder into the XT30U cup, heat shrink over the cup | join at splice JFI with P7, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | JFI.S (JFI splice) | F1.IN (F1 line side (from XT30)) | 16 AWG | holder lead | 90 | join at splice JFI with P7, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (holder lead), solder joint covered with heat shrink |
| 3 | F1.OUT (F1 load side (to 2815 VIN)) | JFO.S (JFO splice) | 16 AWG | holder lead | 90 | use the part's own lead (holder lead), solder joint covered with heat shrink | join at splice JFO with P7, solder, cover with adhesive heat shrink (BOM 26) |
| 4 | JFO.S (JFO splice) | SW1.VIN (SW1 fused pack in) | 16 AWG | red | 40 | join at splice JFO with P7, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole VIN |

Test: XT30.M+ to JFI.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to XT30.M-; JFI.S to F1.IN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); F1.OUT to JFO.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to F1.IN; JFO.S to SW1.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: channel body_back; none (free air); edge body_back; edge trunk_top; none (free air); edge body_middle_bottom; edge body_middle_bottom; edge body_middle_bottom
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T002 stick-on mount MB3A (BOM 34) on battery_pack_lid, 16 mm from the cable line; T006 stick-on mount ABM1M-AT-C (BOM 34b) on battery_pack_lid, 13 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 84.3 mm, cut 130 mm.

### P14: XT30U male - to splice G

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | XT30.M- (J1 robot side -) | G.S (G splice) | 16 AWG | black | 140 | solder into the XT30U cup, heat shrink over the cup | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) |

Test: XT30.M- to G.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to XT30.M+

Seats on the brackets, end to end: channel body_back; none (free air); edge body_back
Reach check (cables3d, by conductor chain): pass with notes, worst routed 44.7 mm, cut 140 mm.

### P9: 2815 VOUT to splice VSW

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SW1.VOUT (SW1 switched pack out) | VSW.S (VSW splice) | 16 AWG | red | 90 | solder into the board hole VOUT | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) |

Test: SW1.VOUT to VSW.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.VIN SW1.GND

Reach check (cables3d, by conductor chain): pass, worst routed 10.1 mm, cut 90 mm.

### P16: splice G to 2815 GND (control ground)

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | G.S (G splice) | SW1.GND (SW1 ground (large hole)) | 20 AWG | black | 90 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole GND |

Test: G.S to SW1.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Reach check (cables3d, by conductor chain): pass, worst routed 10.6 mm, cut 90 mm.

### P15: 2813 A and B to the momentary button (D30; was the 2815 SW pad pair to the panel switch)

Regions: battery_bay. Crosses joints: none. 

Twist: none (a 58 mm run leaves 18 mm after the 2 x 20 mm untwisted ends, under one 35 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SW1.SW (SW1 switch control terminal (pad pair marked with a switch symbol)) | CTL.1 (SW2 contact) | 26 AWG | white | 150 | solder into the board hole SW | tin and solder to CTL.1, heat shrink if bare |
| 2 | SW1.GND_SW (SW1 GND pad next to SW (pad pair marked with a switch symbol)) | CTL.2 (SW2 contact) | 26 AWG | black | 150 | solder into the board hole GND_SW | tin and solder to CTL.2, heat shrink if bare |

Test: SW1.SW to CTL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.GND_SW SW1.ON; SW1.GND_SW to CTL.2: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.SW SW1.ON

Seats on the brackets, end to end: none (free air); edge trunk_top; edge trunk_top; edge trunk_top
Reach check (cables3d, by conductor chain): pass with notes, worst routed 58.1 mm, cut 150 mm.

### P10: splices VSW and G to the BEC input leads

Regions: battery_bay, belly. Crosses joints: none. the BEC input leads ship (length not published): cut P10 shorter by their length

Twist: none (a 54 mm run leaves 14 mm after the 2 x 20 mm untwisted ends, under one 70 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | VSW.S (VSW splice) | U1.IN+ (U1 input + (red lead)) | 16 AWG | red | 150 | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (solder to BEC lead), solder joint covered with heat shrink |
| 2 | G.S (G splice) | U1.IN- (U1 input - (black lead)) | 16 AWG | black | 150 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (solder to BEC lead), solder joint covered with heat shrink |

Test: VSW.S to U1.IN+: under 1 ohm, read in ohms (TEST_PLAN.md section 2); G.S to U1.IN-: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air)
Reach check (cables3d, by conductor chain): pass, worst routed 58.0 mm, cut 150 mm.

## 2. Belly servo power (D15, D23)

### P11: both BEC output leads joined (JB+ JB-) to the belly power splices SPV and SPG

Regions: belly. Crosses joints: none. BEC output leads ship (gauge and length not published: as shipped); ngspice power-path sim (lead, sim pass only): BEC output peaks 8.3 to 9.1 A while walking

Twist: none (a 55 mm run leaves 15 mm after the 2 x 20 mm untwisted ends, under one 100 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U1.OUT1+ (U1 output lead 1 + (red)) | JBP.S (JB+ splice) | BEC lead | red | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | U1.OUT2+ (U1 output lead 2 + (red)) | JBP.S (JB+ splice) | BEC lead | red | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | U1.OUT1- (U1 output lead 1 - (black)) | JBN.S (JB- splice) | BEC lead | black | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 4 | U1.OUT2- (U1 output lead 2 - (black)) | JBN.S (JB- splice) | BEC lead | black | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 5 | JBP.S (JB+ splice) | SPV.S (SPV splice) | 16 AWG | red | 100 | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) |
| 6 | JBN.S (JB- splice) | SPG.S (SPG splice) | 16 AWG | black | 100 | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) |

Test: U1.OUT1+ to JBP.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT1- U1.OUT1S; U1.OUT2+ to JBP.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT2- U1.OUT2S; U1.OUT1- to JBN.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT1+ U1.OUT1S; U1.OUT2- to JBN.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT2+ U1.OUT2S; JBP.S to SPV.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JBN.S to SPG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 55.0 mm, cut 100 mm.

### SP1: power pair SPV and SPG to ID 20 BUS 2 (V and G)

Regions: belly, trunk_bottom. Crosses joints: none. 22 AWG because the 08-70-1040 terminal takes 22 to 28 AWG; GND joins SD1 at JG20 before the housing

Twist: none (a 71 mm run leaves 31 mm after the 2 x 20 mm untwisted ends, under one 40 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV20.BUS2.V (ID20 supply, pin 2) | 22 AWG | red | 160 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG20.S (JG20 splice) | 22 AWG | black | 140 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG20.S (JG20 splice) | SV20.BUS2.G (ID20 ground, pin 1) | 22 AWG | black | 30 | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV20.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG20.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG20.S to SV20.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; channel trunk_top; none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T007 stick-on mount MB3A (BOM 34) on trunk_top, 13 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 111.6 mm, cut 150 mm.

### SP2: power pair SPV and SPG to ID 10 BUS 2 (V and G)

Regions: belly, trunk_bottom. Crosses joints: none. GND joins SD2 at JG10

Twist: none (a 69 mm run leaves 29 mm after the 2 x 20 mm untwisted ends, under one 40 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV10.BUS2.V (ID10 supply, pin 2) | 22 AWG | red | 150 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG10.S (JG10 splice) | 22 AWG | black | 130 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG10.S (JG10 splice) | SV10.BUS2.G (ID10 ground, pin 1) | 22 AWG | black | 30 | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV10.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG10.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG10.S to SV10.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; channel trunk_top; edge trunk_top; none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T008 stick-on mount MB3A (BOM 34) on trunk_top, 14 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 109.2 mm, cut 150 mm.

### SP3: power pair SPV and SPG to ID 30 BUS 2 (V and G)

Regions: belly, trunk_top. Crosses joints: none. GND joins SD1 at JG30

Twist: all wires twisted together, one full turn every 40 mm (allowed 27 to 54 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV30.BUS2.V (ID30 supply, pin 2) | 22 AWG | red | 180 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG30.S (JG30 splice) | 22 AWG | black | 160 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG30.S (JG30 splice) | SV30.BUS2.G (ID30 ground, pin 1) | 22 AWG | black | 30 | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV30.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG30.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG30.S to SV30.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge trunk_bottom; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge trunk_top; edge trunk_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T009 stick-on mount MB3A (BOM 34) on trunk_bottom, 10 mm from the cable line; T010 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_bottom, 8 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 115.3 mm, cut 180 mm.

### SP4: power pair SPV and SPG to ID 24 BUS 1 (V and G), left leg

Regions: belly, trunk_bottom, left_leg. Crosses joints: left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee. service loop at every leg joint; ties in cables3d.json retention

Twist: all wires twisted together, one full turn every 40 mm (allowed 27 to 54 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV24.BUS1.V (ID24 supply, pin 2) | 22 AWG | red | 420 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | SV24.BUS1.G (ID24 ground, pin 1) | 22 AWG | black | 420 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV24.BUS1.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to SV24.BUS1.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; none (free air); edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; none (free air); edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T029 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_bottom, 13 mm from the cable line; T030 stick-on mount MB3A (BOM 34) on left_roll_to_pitch, 15 mm from the cable line; T032 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 10 mm from the cable line; T033 through the hole in knee_to_ankle_right_sheet; T034 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T069 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_top, 13 mm from the cable line; T073 through the hole in knee_to_ankle_right_sheet; T088 stick-on mount MB3A (BOM 34) on trunk_top, 16 mm from the cable line
Joint loops: left_hip_yaw: leave 35 mm between T088 and T069 (14 mm more than the straight run at the zero pose); left_hip_roll: leave 38 mm between T029 and T030 (9 mm more than the straight run at the zero pose); left_hip_pitch: leave 47 mm between T030 and T032 (17 mm more than the straight run at the zero pose); left_knee: leave 42 mm between T033 and T034 (20 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 363.5 mm, cut 400 mm.

### SP5: power pair SPV and SPG to ID 14 BUS 1 (V and G), right leg

Regions: belly, trunk_bottom, right_leg. Crosses joints: right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee. service loop at every leg joint; ties in cables3d.json retention

Twist: all wires twisted together, one full turn every 40 mm (allowed 27 to 54 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV14.BUS1.V (ID14 supply, pin 2) | 22 AWG | red | 450 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | SV14.BUS1.G (ID14 ground, pin 1) | 22 AWG | black | 450 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV14.BUS1.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to SV14.BUS1.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; channel right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; none (free air); edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_side
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T043 stick-on mount ABM1M-AT-C (BOM 34b) on right_roll_to_pitch, 13 mm from the cable line; T044 stick-on mount MB3A (BOM 34) on right_roll_to_pitch, 17 mm from the cable line; T045 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T046 stick-on mount MB3A (BOM 34) on knee_to_ankle_left_sheet, 19 mm from the cable line; T047 stick-on mount ABM1M-AT-C (BOM 34b) on right_cache, 16 mm from the cable line; T048 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 16 mm from the cable line; T081 through the hole in knee_to_ankle_right_sheet; T089 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4)
Joint loops: right_hip_yaw+right_hip_roll: leave 48 mm between T089 and T043 (24 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; right_hip_pitch: leave 47 mm between T044 and T045 (15 mm more than the straight run at the zero pose); right_knee: leave 85 mm between T047 and T048 (19 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 392.8 mm, cut 430 mm.

## 3. Servo data leads and kit cables

### SD1: adapter H3 data lead: DATA and GND only (V position empty), data Y at YD3 to ID 20 and ID 30, GND Y at YG3 into the SP1 and SP3 grounds

Regions: trunk_top, trunk_bottom. Crosses joints: none. branch a rule 149.0 (adapter to ID 20), branch b rule 172.5 (adapter to ID 30); housing Molex 50-37-5033 with 2 terminals at H3

Twist: the wires of branch b twisted together, one full turn every 40 mm (allowed 27 to 54 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U2.H3.D (U2 bus data (H3 pin 1)) | YD3.S (YD3 splice) | 22 AWG | yellow | 30 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | U2.H3.G (U2 ground (H3 pin 3)) | YG3.S (YG3 splice) | 22 AWG | black | 45 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | YD3.S (YD3 splice) | SV20.BUS2.D (ID20 data, pin 3) | 22 AWG | yellow | 130 | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 4 | YG3.S (YG3 splice) | JG20.S (JG20 splice) | 22 AWG | black | 120 | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) |
| 5 | YD3.S (YD3 splice) | SV30.BUS2.D (ID30 data, pin 3) | 22 AWG | yellow | 170 | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 6 | YG3.S (YG3 splice) | JG30.S (JG30 splice) | 22 AWG | black | 140 | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) |

Test: U2.H3.D to YD3.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H3.V U2.H3.G; U2.H3.G to YG3.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H3.D U2.H3.V; YD3.S to SV20.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YG3.S to JG20.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YD3.S to SV30.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YG3.S to JG30.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; edge trunk_top; none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T012 stick-on mount MB3A (BOM 34) on trunk_top, 3 mm from the cable line; T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 124.7 mm, cut 170 mm.

### SD2: adapter H5 data lead: DATA and GND only, to ID 10 (DATA) and JG10 (GND)

Regions: trunk_top, trunk_bottom. Crosses joints: none. 

Twist: none (a 66 mm run leaves 26 mm after the 2 x 20 mm untwisted ends, under one 40 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U2.H5.D (U2 bus data (H5 pin 1)) | SV10.BUS2.D (ID10 data, pin 3) | 22 AWG | yellow | 150 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | U2.H5.G (U2 ground (H5 pin 3)) | JG10.S (JG10 splice) | 22 AWG | black | 140 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) |

Test: U2.H5.D to SV10.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H5.V U2.H5.G; U2.H5.G to JG10.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H5.D U2.H5.V

Seats on the brackets, end to end: none (free air); edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T066 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 90.8 mm, cut 150 mm.

### S2: kit cable ID 20 BUS 1 to ID 21 BUS 2

Regions: trunk_bottom, left_leg. Crosses joints: left_hip_yaw. BLOCKER test fit (rule 2.3 mm over 150)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV20.BUS1.D (ID20 data, pin 3) | SV21.BUS2.D (ID21 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV20.BUS1.V (ID20 supply, pin 2) | SV21.BUS2.V (ID21 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV20.BUS1.G (ID20 ground, pin 1) | SV21.BUS2.G (ID21 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV20.BUS1.D to SV21.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.V SV20.BUS1.G; SV20.BUS1.V to SV21.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.D SV20.BUS1.G; SV20.BUS1.G to SV21.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.D SV20.BUS1.V

Seats on the brackets, end to end: channel trunk_top; none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top; none (free air); edge trunk_top; edge left_roll_to_pitch
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T067 stick-on mount MB3A (BOM 34) on body_middle_top, 11 mm from the cable line; T068 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 11 mm from the cable line; T069 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_top, 13 mm from the cable line
Joint loops: left_hip_yaw: leave 29 mm between T068 and T069 (13 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): test fit, worst routed 131.8 mm, cut 150 mm.

### S3: kit cable ID 21 to ID 22

Regions: left_leg. Crosses joints: left_hip_roll. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV21.BUS1.D (ID21 data, pin 3) | SV22.BUS2.D (ID22 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV21.BUS1.V (ID21 supply, pin 2) | SV22.BUS2.V (ID22 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV21.BUS1.G (ID21 ground, pin 1) | SV22.BUS2.G (ID22 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV21.BUS1.D to SV22.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.V SV21.BUS1.G; SV21.BUS1.V to SV22.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.D SV21.BUS1.G; SV21.BUS1.G to SV22.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.D SV21.BUS1.V

Seats on the brackets, end to end: none (free air); edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; edge left_roll_to_pitch; none (free air); edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T070 stick-on mount ABM1M-AT-C (BOM 34b) on left_roll_to_pitch, 11 mm from the cable line
Joint loops: left_hip_roll: leave 38 mm between the plug and T070 (4 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 88.0 mm, cut 150 mm.

### S4: kit cable ID 22 to ID 23

Regions: left_leg. Crosses joints: left_hip_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV22.BUS1.D (ID22 data, pin 3) | SV23.BUS2.D (ID23 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV22.BUS1.V (ID22 supply, pin 2) | SV23.BUS2.V (ID23 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV22.BUS1.G (ID22 ground, pin 1) | SV23.BUS2.G (ID23 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV22.BUS1.D to SV23.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.V SV22.BUS1.G; SV22.BUS1.V to SV23.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.D SV22.BUS1.G; SV22.BUS1.G to SV23.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.D SV22.BUS1.V

Seats on the brackets, end to end: none (free air); edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T030 stick-on mount MB3A (BOM 34) on left_roll_to_pitch, 15 mm from the cable line; T033 through the hole in knee_to_ankle_right_sheet; T071 stick-on mount MB3A (BOM 34) on knee_to_ankle_right_sheet, 17 mm from the cable line
Joint loops: left_hip_pitch: leave 36 mm between T030 and T071 (16 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 95.8 mm, cut 150 mm.

### S5: kit cable ID 23 BUS 1 to ID 24 BUS 2

Regions: left_leg. Crosses joints: left_knee. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV23.BUS1.D (ID23 data, pin 3) | SV24.BUS2.D (ID24 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV23.BUS1.V (ID23 supply, pin 2) | SV24.BUS2.V (ID24 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV23.BUS1.G (ID23 ground, pin 1) | SV24.BUS2.G (ID24 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV23.BUS1.D to SV24.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.V SV23.BUS1.G; SV23.BUS1.V to SV24.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.D SV23.BUS1.G; SV23.BUS1.G to SV24.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.D SV23.BUS1.V

Seats on the brackets, end to end: none (free air); edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge knee_to_ankle_right_sheet; edge foot_side
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T072 through the drilled tie-hole pair in knee_to_ankle_right_sheet (4.0 mm holes 7.0 mm apart, print/PRINT_PLAN.md After printing), 9 mm from the cable line; T073 through the hole in knee_to_ankle_right_sheet
Joint loops: left_knee: leave 46 mm between the plug and T072 (20 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 109.8 mm, cut 150 mm.

### S7: kit cable ID 10 to ID 11

Regions: trunk_bottom, right_leg. Crosses joints: right_hip_yaw. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV10.BUS1.D (ID10 data, pin 3) | SV11.BUS2.D (ID11 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV10.BUS1.V (ID10 supply, pin 2) | SV11.BUS2.V (ID11 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV10.BUS1.G (ID10 ground, pin 1) | SV11.BUS2.G (ID11 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV10.BUS1.D to SV11.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.V SV10.BUS1.G; SV10.BUS1.V to SV11.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.D SV10.BUS1.G; SV10.BUS1.G to SV11.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.D SV10.BUS1.V

Seats on the brackets, end to end: channel trunk_top; none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge right_roll_to_pitch
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T042 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_top, 15 mm from the cable line; T074 stick-on mount MB3A (BOM 34) on trunk_top, 15 mm from the cable line; T075 stick-on mount MB3A (BOM 34) on body_middle_bottom, 17 mm from the cable line
Joint loops: right_hip_yaw: leave 30 mm between T075 and T042 (14 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): test fit, worst routed 133.4 mm, cut 150 mm.

### S8: kit cable ID 11 to ID 12

Regions: right_leg. Crosses joints: right_hip_roll. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV11.BUS1.D (ID11 data, pin 3) | SV12.BUS2.D (ID12 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV11.BUS1.V (ID11 supply, pin 2) | SV12.BUS2.V (ID12 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV11.BUS1.G (ID11 ground, pin 1) | SV12.BUS2.G (ID12 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV11.BUS1.D to SV12.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.V SV11.BUS1.G; SV11.BUS1.V to SV12.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.D SV11.BUS1.G; SV11.BUS1.G to SV12.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.D SV11.BUS1.V

Seats on the brackets, end to end: none (free air); edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; channel right_roll_to_pitch; none (free air); edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T044 stick-on mount MB3A (BOM 34) on right_roll_to_pitch, 17 mm from the cable line; T077 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_bottom, 7 mm from the cable line
Joint loops: right_hip_roll: leave 31 mm between T077 and T044 (9 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 103.9 mm, cut 150 mm.

### S9: kit cable ID 12 to ID 13

Regions: right_leg. Crosses joints: right_hip_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV12.BUS1.D (ID12 data, pin 3) | SV13.BUS2.D (ID13 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV12.BUS1.V (ID12 supply, pin 2) | SV13.BUS2.V (ID13 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV12.BUS1.G (ID12 ground, pin 1) | SV13.BUS2.G (ID13 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV12.BUS1.D to SV13.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.V SV12.BUS1.G; SV12.BUS1.V to SV13.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.D SV12.BUS1.G; SV12.BUS1.G to SV13.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.D SV12.BUS1.V

Seats on the brackets, end to end: none (free air); edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T046 stick-on mount MB3A (BOM 34) on knee_to_ankle_left_sheet, 19 mm from the cable line; T079 tied to cable SP5, which T047 holds
Joint loops: right_hip_pitch: leave 35 mm between the plug and T046 (16 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 102.6 mm, cut 150 mm.

### S10: kit cable ID 13 to ID 14

Regions: right_leg. Crosses joints: right_knee. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV13.BUS1.D (ID13 data, pin 3) | SV14.BUS2.D (ID14 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV13.BUS1.V (ID13 supply, pin 2) | SV14.BUS2.V (ID14 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV13.BUS1.G (ID13 ground, pin 1) | SV14.BUS2.G (ID14 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV13.BUS1.D to SV14.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.V SV13.BUS1.G; SV13.BUS1.V to SV14.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.D SV13.BUS1.G; SV13.BUS1.G to SV14.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.D SV13.BUS1.V

Seats on the brackets, end to end: none (free air); edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge knee_to_ankle_right_sheet; edge foot_side
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T048 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 16 mm from the cable line; T081 through the hole in knee_to_ankle_right_sheet
Joint loops: right_knee: leave 39 mm between the plug and T048 (18 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 108.9 mm, cut 150 mm.

### S11: kit cable ID 30 BUS 1 to ID 31 BUS 2

Regions: trunk_top, neck. Crosses joints: neck_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV30.BUS1.D (ID30 data, pin 3) | SV31.BUS2.D (ID31 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV30.BUS1.V (ID30 supply, pin 2) | SV31.BUS2.V (ID31 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV30.BUS1.G (ID30 ground, pin 1) | SV31.BUS2.G (ID31 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV30.BUS1.D to SV31.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.V SV30.BUS1.G; SV30.BUS1.V to SV31.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.D SV30.BUS1.G; SV30.BUS1.G to SV31.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.D SV30.BUS1.V

Seats on the brackets, end to end: none (free air); edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T082 tied to cable D3, which T014 holds; T083 through the hole in neck_right_sheet
Joint loops: neck_pitch: leave 34 mm between the plug and T082 (15 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 98.4 mm, cut 150 mm.

### S12: kit cable ID 31 to ID 32

Regions: neck. Crosses joints: head_pitch, head_yaw. BLOCKER test fit (113 mm over 150); contingency X1/X2 made lead 270 mm

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV31.BUS1.D (ID31 data, pin 3) | SV32.BUS2.D (ID32 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV31.BUS1.V (ID31 supply, pin 2) | SV32.BUS2.V (ID32 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV31.BUS1.G (ID31 ground, pin 1) | SV32.BUS2.G (ID32 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV31.BUS1.D to SV32.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.V SV31.BUS1.G; SV31.BUS1.V to SV32.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.D SV31.BUS1.G; SV31.BUS1.G to SV32.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.D SV31.BUS1.V

Seats on the brackets, end to end: none (free air); edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T084 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 7.0 mm apart, print/PRINT_PLAN.md After printing), 20 mm from the cable line
Joint loops: head_pitch+head_yaw: leave 81 mm between T084 and the plug (41 mm more than the straight run at the zero pose), one loop over both joints: no tie between them
Reach check (cables3d, by conductor chain): pass with notes, worst routed 89.7 mm, cut 150 mm.

### S13: kit cable ID 32 to ID 33

Regions: neck, head. Crosses joints: head_roll. fits (2.7 mm margin)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV32.BUS1.D (ID32 data, pin 3) | SV33.BUS2.D (ID33 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV32.BUS1.V (ID32 supply, pin 2) | SV33.BUS2.V (ID33 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV32.BUS1.G (ID32 ground, pin 1) | SV33.BUS2.G (ID33 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV32.BUS1.D to SV33.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.V SV32.BUS1.G; SV32.BUS1.V to SV33.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.D SV32.BUS1.G; SV32.BUS1.G to SV33.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.D SV32.BUS1.V

Seats on the brackets, end to end: none (free air); edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T085 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T086 stick-on mount MB3A (BOM 34) on head_bot_sheet, 17 mm from the cable line; T087 stick-on mount MB3A (BOM 34) on head_bot_sheet, 17 mm from the cable line
Joint loops: head_roll: leave 24 mm between T085 and T086 (7 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 106.9 mm, cut 150 mm.

## 4. Power up the neck to the head

### P13: splices VSW and G up the neck to U3 VIN and GND on the head floor

Regions: battery_bay, trunk_top, neck, head. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. drop about 0.09 V at 2.5 A over 2 x 0.55 m of 20 AWG [I]

Inline plug: XT30U pair (BOM 12) at the neck base on trunk_top, on a straight run 20 mm or more from the neck_pitch loop end; solder cups and heat shrink both halves; the head comes off by unplugging it (X3a, D36)

Twist: all wires twisted together, one full turn every 45 mm (allowed 29 to 58 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | VSW.S (VSW splice) | U3.VIN (U3 input from VSW) | 20 AWG | red | 550 | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole VIN |
| 2 | G.S (G splice) | U3.GND.1 (U3 ground (input side)) | 20 AWG | black | 550 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole 1 |

Test: VSW.S to U3.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); G.S to U3.GND.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none (free air); edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T011 stick-on mount ABM1M-AT-C (BOM 34b) on battery_pack_lid, 24 mm from the cable line; T012 stick-on mount MB3A (BOM 34) on trunk_top, 3 mm from the cable line; T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line; T014 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 12.1 mm apart, print/PRINT_PLAN.md After printing), 18 mm from the cable line; T016 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T017 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T018 stick-on mount MB3A (BOM 34) on head_bot_sheet, 15 mm from the cable line; T038 through the hole in neck_right_sheet
Joint loops: neck_pitch: leave 42 mm between T013 and T014 (15 mm more than the straight run at the zero pose); head_pitch+head_yaw: leave 82 mm between T038 and T016 (42 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; head_roll: leave 41 mm between T017 and T018 (18 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 441.1 mm, cut 550 mm.

### P12: U3 VOUT and GND to Pi pin 2 and pin 6

Regions: head. Crosses joints: none. exact spot of U3 on the floor not fixed

Twist: none (a 31 mm run leaves 0 mm after the 2 x 20 mm untwisted ends, under one 45 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U3.VOUT (U3 5 V out) | PI.2 (U4 5V) | 20 AWG | red | 130 | solder into the board hole VOUT | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 2 until it clicks, then tug-test (X1, D36: the Pi unplugs) |
| 2 | U3.GND.2 (U3 ground (output side)) | PI.6 (U4 GND) | 20 AWG | black | 130 | solder into the board hole 2 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 6 until it clicks, then tug-test (X1, D36: the Pi unplugs) |

Test: U3.VOUT to PI.2: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U3.VIN U3.GND.1 U3.GND.2 U3.EN U3.PG; U3.GND.2 to PI.6: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U3.VIN U3.GND.1 U3.VOUT U3.EN U3.PG

Reach check (cables3d, by conductor chain): pass, worst routed 33.7 mm, cut 130 mm.

### P17: Pi pin 4 and pin 14 to splices J5 and JG

Regions: head. Crosses joints: none. 

Twist: none (a 16 mm run leaves 0 mm after the 2 x 20 mm untwisted ends, under one 45 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.4 (U4 5V) | J5.S (J5 splice) | 20 AWG | red | 90 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 4 until it clicks, then tug-test (X1, D36: the Pi unplugs) | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | PI.14 (U4 GND) | JG.S (JG splice) | 20 AWG | black | 90 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 14 until it clicks, then tug-test (X1, D36: the Pi unplugs) | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: PI.4 to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.5 PI.6 PI.9; PI.14 to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6

Reach check (cables3d, by conductor chain): pass, worst routed 28.9 mm, cut 90 mm.

## 5. Pi, IMU and feet

### D1: Pi micro-USB data port to adapter USB-C

Regions: head, neck, trunk_top, belly. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. coil the slack in the belly

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.USB (U4 micro-USB OTG data port) | U2.USB (U2 USB-C to the CH343P serial bridge) | USB 2.0 cable | black jacket | 900 | bought cable end (micro-USB B plug), plug in | bought cable end (USB-C plug), plug in |

Test: PI.USB to U2.USB: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none (free air); edge body_middle_top; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line; T014 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 12.1 mm apart, print/PRINT_PLAN.md After printing), 18 mm from the cable line; T020 stick-on mount MB3A (BOM 34) on body_middle_bottom, 15 mm from the cable line; T021 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 12 mm from the cable line; T023 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T024 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T025 stick-on mount MB3A (BOM 34) on trunk_top, 14 mm from the cable line; T038 through the hole in neck_right_sheet
Joint loops: neck_pitch: leave 41 mm between T013 and T014 (15 mm more than the straight run at the zero pose); head_pitch+head_yaw: leave 80 mm between T023 and T024 (42 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; head_roll: leave 42 mm between T024 and the plug (15 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 523.0 mm, cut 900 mm.

### D2: Pi to BNO055 (3V3, GND, SDA, SCL)

Regions: head, neck, trunk_top. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. 

Twist: all wires twisted together, one full turn every 40 mm (allowed 28 to 55 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 2.4 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.1 (U4 3V3) | BNO.VIN (U7 supply) | 26 AWG | red | 550 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 1 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 2 | PI.9 (U4 GND) | BNO.GND (U7 ground) | 26 AWG | black | 550 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 9 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 3 | PI.3 (U4 GPIO2 SDA) | BNO.SDA (U7 I2C data) | 26 AWG | blue | 550 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 3 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 4 | PI.5 (U4 GPIO3 SCL) | BNO.SCL (U7 I2C clock) | 26 AWG | yellow | 550 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 5 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |

Test: PI.1 to BNO.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.2 PI.3 PI.4 PI.5 PI.6 PI.9; PI.9 to BNO.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.3 to BNO.SDA: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.4 PI.5 PI.6 PI.9; PI.5 to BNO.SCL: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.6 PI.9

Seats on the brackets, end to end: none (free air); edge trunk_bottom; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none (free air); edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T010 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_bottom, 8 mm from the cable line; T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line; T014 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 12.1 mm apart, print/PRINT_PLAN.md After printing), 18 mm from the cable line; T016 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T017 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T025 stick-on mount MB3A (BOM 34) on trunk_top, 14 mm from the cable line; T026 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T038 through the hole in neck_right_sheet
Joint loops: neck_pitch: leave 41 mm between T013 and T014 (15 mm more than the straight run at the zero pose); head_pitch+head_yaw: leave 79 mm between T038 and T016 (42 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; head_roll: leave 39 mm between T017 and T026 (15 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 439.3 mm, cut 550 mm.

### D3: Pi to left foot switches, with pull-up R4 at the header

Regions: head, neck, trunk_top, trunk_bottom, left_leg. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll, left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle. 

Twist: all wires twisted together, one full turn every 40 mm (allowed 28 to 55 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 2.4 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.17 (U4 3V3) | RFL.1 (R4 3V3 side (Pi pin 17)) | resistor lead | none | 0 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 17 until it clicks, then tug-test (X1, D36: the Pi unplugs) | use the part's own lead (resistor lead), solder joint covered with heat shrink |
| 2 | RFL.2 (R4 input side (Pi pin 15)) | PI.15 (U4 GPIO22 left foot) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 15 until it clicks, then tug-test (X1, D36: the Pi unplugs) |
| 3 | PI.15 (U4 GPIO22 left foot) | FSL1.NO (SL1 normally open) | 26 AWG | green | 900 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 15 until it clicks, then tug-test (X1, D36: the Pi unplugs) | tin and solder to FSL1.NO, heat shrink if bare |
| 4 | PI.9 (U4 GND) | FSL1.COM (SL1 common) | 26 AWG | black | 900 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 9 until it clicks, then tug-test (X1, D36: the Pi unplugs) | tin and solder to FSL1.COM, heat shrink if bare |
| 5 | FSL1.NO (SL1 normally open) | FSL2.NO (SL2 normally open) | 26 AWG | green | 110 | tin and solder to FSL1.NO, heat shrink if bare | tin and solder to FSL2.NO, heat shrink if bare |
| 6 | FSL1.COM (SL1 common) | FSL2.COM (SL2 common) | 26 AWG | black | 110 | tin and solder to FSL1.COM, heat shrink if bare | tin and solder to FSL2.COM, heat shrink if bare |

Test: PI.17 to RFL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RFL.2 to PI.15: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RFL.1; PI.15 to FSL1.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.9 to FSL1.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; FSL1.NO to FSL2.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSL1.COM FSL1.NC; FSL1.COM to FSL2.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSL1.NO FSL1.NC

Seats on the brackets, end to end: none (free air); edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none (free air); edge body_middle_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_bottom; edge trunk_bottom; edge roll_motor_bottom; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; none (free air); edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; none (free air); edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_top; channel foot_top; channel foot_top; edge foot_top; edge foot_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line; T014 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 12.1 mm apart, print/PRINT_PLAN.md After printing), 18 mm from the cable line; T017 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T023 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T026 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T027 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_bottom, 10 mm from the cable line; T028 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_bottom, 18 mm from the cable line; T029 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_bottom, 13 mm from the cable line; T030 stick-on mount MB3A (BOM 34) on left_roll_to_pitch, 15 mm from the cable line; T032 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 10 mm from the cable line; T033 through the hole in knee_to_ankle_right_sheet; T034 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T035 stick-on mount MB3A (BOM 34) on knee_to_ankle_right_sheet, 15 mm from the cable line; T036 through the hole in knee_to_ankle_right_sheet; T037 stick-on mount MB3A (BOM 34) on foot_bottom_pla, 14 mm from the cable line; T038 through the hole in neck_right_sheet
Joint loops: head_roll: leave 39 mm between T026 and T017 (15 mm more than the straight run at the zero pose); head_yaw+head_pitch: leave 79 mm between T017 and T023 (41 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; neck_pitch: leave 41 mm between T014 and T013 (15 mm more than the straight run at the zero pose); left_hip_yaw: leave 38 mm between T027 and T028 (9 mm more than the straight run at the zero pose); left_hip_roll: leave 39 mm between T029 and T030 (9 mm more than the straight run at the zero pose); left_hip_pitch: leave 47 mm between T030 and T032 (17 mm more than the straight run at the zero pose); left_knee: leave 42 mm between T033 and T034 (20 mm more than the straight run at the zero pose); left_ankle: leave 65 mm between T036 and the plug (23 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 774.2 mm, cut 900 mm.

### D4: Pi to right foot switches, with pull-up R5 at the header

Regions: head, neck, trunk_top, trunk_bottom, right_leg. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle. 

Twist: all wires twisted together, one full turn every 40 mm (allowed 28 to 55 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 2.4 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.17 (U4 3V3) | RFR.1 (R5 3V3 side (Pi pin 17)) | resistor lead | none | 0 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 17 until it clicks, then tug-test (X1, D36: the Pi unplugs) | use the part's own lead (resistor lead), solder joint covered with heat shrink |
| 2 | RFR.2 (R5 input side (Pi pin 13)) | PI.13 (U4 GPIO27 right foot) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 13 until it clicks, then tug-test (X1, D36: the Pi unplugs) |
| 3 | PI.13 (U4 GPIO27 right foot) | FSR1.NO (SR1 normally open) | 26 AWG | white | 950 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 13 until it clicks, then tug-test (X1, D36: the Pi unplugs) | tin and solder to FSR1.NO, heat shrink if bare |
| 4 | PI.9 (U4 GND) | FSR1.COM (SR1 common) | 26 AWG | black | 950 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 9 until it clicks, then tug-test (X1, D36: the Pi unplugs) | tin and solder to FSR1.COM, heat shrink if bare |
| 5 | FSR1.NO (SR1 normally open) | FSR2.NO (SR2 normally open) | 26 AWG | white | 110 | tin and solder to FSR1.NO, heat shrink if bare | tin and solder to FSR2.NO, heat shrink if bare |
| 6 | FSR1.COM (SR1 common) | FSR2.COM (SR2 common) | 26 AWG | black | 110 | tin and solder to FSR1.COM, heat shrink if bare | tin and solder to FSR2.COM, heat shrink if bare |

Test: PI.17 to RFR.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RFR.2 to PI.13: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RFR.1; PI.13 to FSR1.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.9 to FSR1.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; FSR1.NO to FSR2.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSR1.COM FSR1.NC; FSR1.COM to FSR2.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSR1.NO FSR1.NC

Seats on the brackets, end to end: none (free air); edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none (free air); edge body_middle_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge roll_motor_top; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; channel right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; none (free air); edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; none (free air); edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_top; channel foot_top; channel foot_top; edge foot_top; edge foot_top
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T013 stick-on mount ABM1M-AT-C (BOM 34b) on trunk_top, 18 mm from the cable line; T014 through the drilled tie-hole pair in neck_right_sheet (4.0 mm holes 12.1 mm apart, print/PRINT_PLAN.md After printing), 18 mm from the cable line; T017 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T023 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T026 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T038 through the hole in neck_right_sheet; T041 stick-on mount MB3A (BOM 34) on body_middle_top, 17 mm from the cable line; T042 stick-on mount ABM1M-AT-C (BOM 34b) on roll_motor_top, 15 mm from the cable line; T043 stick-on mount ABM1M-AT-C (BOM 34b) on right_roll_to_pitch, 13 mm from the cable line; T044 stick-on mount MB3A (BOM 34) on right_roll_to_pitch, 17 mm from the cable line; T045 around the bundle only (bundle tie, test fit: check it at both joint limits, TEST_PLAN 1.4); T046 stick-on mount MB3A (BOM 34) on knee_to_ankle_left_sheet, 19 mm from the cable line; T047 stick-on mount ABM1M-AT-C (BOM 34b) on right_cache, 16 mm from the cable line; T048 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 16 mm from the cable line; T049 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 3 mm from the cable line; T050 stick-on mount ABM1M-AT-C (BOM 34b) on knee_to_ankle_right_sheet, 16 mm from the cable line; T051 stick-on mount MB3A (BOM 34) on foot_bottom_pla, 14 mm from the cable line
Joint loops: head_roll: leave 39 mm between T026 and T017 (15 mm more than the straight run at the zero pose); head_yaw+head_pitch: leave 79 mm between T017 and T023 (41 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; neck_pitch: leave 61 mm between T014 and T013 (15 mm more than the straight run at the zero pose); right_hip_yaw: leave 35 mm between T041 and T042 (8 mm more than the straight run at the zero pose); right_hip_roll: leave 33 mm between T042 and T043 (7 mm more than the straight run at the zero pose); right_hip_pitch: leave 48 mm between T044 and T045 (15 mm more than the straight run at the zero pose); right_knee: leave 86 mm between T047 and T048 (19 mm more than the straight run at the zero pose); right_ankle: leave 57 mm between T050 and the plug (23 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 769.6 mm, cut 950 mm.

## 6. Head expression

### D5: Pi to left eye LED and resistor

Regions: head. Crosses joints: none. 

Twist: none (a 58 mm run leaves 18 mm after the 2 x 20 mm untwisted ends, under one 35 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.18 (U4 GPIO24 left eye) | RL.1 (R1 GPIO side) | 26 AWG | yellow | 150 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 18 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 2 | RL.2 (R1 LED side) | LEDL.A (LED1 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDL.K (LED1 cathode) | PI.20 (U4 GND) | 26 AWG | black | 150 | solder | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 20 until it clicks, then tug-test (X1, D36: the Pi unplugs) |

Test: PI.18 to RL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RL.2 to LEDL.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RL.1; LEDL.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDL.A

Seats on the brackets, end to end: none (free air)
Reach check (cables3d, by conductor chain): pass, worst routed 59.6 mm, cut 150 mm.

### D6: Pi to right eye LED and resistor

Regions: head. Crosses joints: none. 

Twist: all wires twisted together, one full turn every 35 mm (allowed 24 to 48 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 1.9 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.16 (U4 GPIO23 right eye) | RR.1 (R2 GPIO side) | 26 AWG | white | 230 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 16 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 2 | RR.2 (R2 LED side) | LEDR.A (LED2 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDR.K (LED2 cathode) | PI.20 (U4 GND) | 26 AWG | black | 230 | solder | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 20 until it clicks, then tug-test (X1, D36: the Pi unplugs) |

Test: PI.16 to RR.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RR.2 to LEDR.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RR.1; LEDR.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDR.A

Seats on the brackets, end to end: none (free air); edge head_roll_mount
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T052 stick-on mount MB3A (BOM 34) on head, 21 mm from the cable line; T053 stick-on mount MB3A (BOM 34) on head, 21 mm from the cable line
Reach check (cables3d, by conductor chain): pass, worst routed 123.4 mm, cut 230 mm.

### D7: Pi to projector LED and resistor

Regions: head. Crosses joints: none. runs inside the head and through the 4 mm hole drilled in the head wall (D24): cables3d 78 mm worst, the 160 mm cut passes

Twist: none (a 38 mm run leaves 0 mm after the 2 x 20 mm untwisted ends, under one 35 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.22 (U4 GPIO25 projector) | RP.1 (R3 GPIO side) | 26 AWG | green | 160 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 22 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 2 | RP.2 (R3 LED side) | LEDP.A (LED3 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDP.K (LED3 cathode) | PI.20 (U4 GND) | 26 AWG | black | 160 | solder | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 20 until it clicks, then tug-test (X1, D36: the Pi unplugs) |

Test: PI.22 to RP.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RP.2 to LEDP.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RP.1; LEDP.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDP.A

Seats on the brackets, end to end: none (free air); edge head; channel head; channel head; hole flash_light_module; hole flash_reflector_interface
Reach check (cables3d, by conductor chain): pass, worst routed 77.5 mm, cut 160 mm.

### D8: left antenna SG90 lead to Pi pin 33 and splices J5 and JG

Regions: head. Crosses joints: none. lead 250 mm fits

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SGL.SIG (M1 PWM in) | PI.33 (U4 GPIO13 left antenna PWM) | SG90 lead | orange | 250 | servo socket | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 33 until it clicks, then tug-test (X1, D36: the Pi unplugs) |
| 2 | SGL.VCC (M1 supply) | J5.S (J5 splice) | SG90 lead | red | 250 | servo socket | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | SGL.GND (M1 ground) | JG.S (JG splice) | SG90 lead | brown | 250 | servo socket | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: SGL.SIG to PI.33: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.VCC SGL.GND; SGL.VCC to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.SIG SGL.GND; SGL.GND to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.SIG SGL.VCC

Seats on the brackets, end to end: none (free air)
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T054 stick-on mount MB3A (BOM 34) on head_bot_sheet, 23 mm from the cable line; T055 stick-on mount MB3A (BOM 34) on head, 23 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 117.5 mm, cut 250 mm.

### D9: right antenna SG90 lead to Pi pin 32 and splices J5 and JG

Regions: head. Crosses joints: none. lead 250 mm reaches without an extension: cables3d 170 mm worst, 210 mm with the slack (the 228 mm polyline runs through part centres)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SGR.SIG (M2 PWM in) | PI.32 (U4 GPIO12 right antenna PWM) | SG90 lead | orange | 250 | servo socket | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 32 until it clicks, then tug-test (X1, D36: the Pi unplugs) |
| 2 | SGR.VCC (M2 supply) | J5.S (J5 splice) | SG90 lead | red | 250 | servo socket | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | SGR.GND (M2 ground) | JG.S (JG splice) | SG90 lead | brown | 250 | servo socket | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: SGR.SIG to PI.32: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.VCC SGR.GND; SGR.VCC to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.SIG SGR.GND; SGR.GND to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.SIG SGR.VCC

Seats on the brackets, end to end: none (free air); edge head
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T056 stick-on mount MB3A (BOM 34) on head, 24 mm from the cable line; T057 stick-on mount MB3A (BOM 34) on head, 7 mm from the cable line; T063 stick-on mount ABM1M-AT-C (BOM 34b) on head, 13 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 169.9 mm, cut 250 mm.

### D10: Pi and splices to MAX98357A

Regions: head. Crosses joints: none. 

Twist: all wires twisted together, one full turn every 45 mm (allowed 31 to 62 mm, 8 to 16 x the bundle OD, NASA-STD-8739.4A 7.2.16 to 7.2.18), the same direction along the whole run, 20 mm untwisted at each end for the joint. Twist before the ends are made; the cut lengths already carry the take-up (up to 2.8 %).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.35 (U4 GPIO19 I2S LRC) | AMP.LRC (U8 I2S frame) | 26 AWG | white | 220 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 35 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 2 | PI.12 (U4 GPIO18 I2S BCLK) | AMP.BCLK (U8 I2S bit clock) | 26 AWG | yellow | 210 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 12 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 3 | PI.40 (U4 GPIO21 I2S DIN) | AMP.DIN (U8 I2S data) | 26 AWG | green | 220 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 40 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder |
| 4 | J5.S (J5 splice) | AMP.VIN (U8 supply) | 26 AWG | red | 220 | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) | solder |
| 5 | JG.S (JG splice) | AMP.GND (U8 ground) | 26 AWG | black | 220 | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) | solder |

Test: PI.35 to AMP.LRC: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.12 to AMP.BCLK: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.40 to AMP.DIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; J5.S to AMP.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG.S to AMP.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge head_roll_mount; edge head_bot_sheet
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T060 stick-on mount MB3A (BOM 34) on head, 16 mm from the cable line; T062 stick-on mount MB3A (BOM 34) on head_bot_sheet, 4 mm from the cable line; T063 stick-on mount ABM1M-AT-C (BOM 34b) on head, 13 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 149.0 mm, cut 220 mm.

### D11: MAX98357A to speaker

Regions: head. Crosses joints: none. 

Twist: none (a 73 mm run leaves 33 mm after the 2 x 20 mm untwisted ends, under one 35 mm lay).

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | AMP.SPK+ (U8 speaker +) | SPK.+ (LS1 speaker +) | 26 AWG | red | 120 | screw terminal AMP.SPK+ | tin and solder to SPK.+, heat shrink if bare |
| 2 | AMP.SPK- (U8 speaker -) | SPK.- (LS1 speaker -) | 26 AWG | black | 120 | screw terminal AMP.SPK- | tin and solder to SPK.-, heat shrink if bare |

Test: AMP.SPK+ to SPK.+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to AMP.SPK-; AMP.SPK- to SPK.-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to AMP.SPK+

Seats on the brackets, end to end: none (free air); edge head_bot_sheet; edge head_bot_sheet
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T062 stick-on mount MB3A (BOM 34) on head_bot_sheet, 4 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 73.0 mm, cut 120 mm.

### D12: Pi CSI to Camera Module 3

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.CSI (U4 camera connector) | CAM.CSI (U9 camera ribbon) | FPC ribbon | white ribbon | 300 | bought cable end (22-pin FPC), plug in | bought cable end (15-pin FPC), plug in |

Test: PI.CSI to CAM.CSI: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none (free air); edge head_roll_mount; edge head
Ties (one 2.5 x 100 mm cable tie each, BOM 32): T063 stick-on mount ABM1M-AT-C (BOM 34b) on head, 13 mm from the cable line; T064 stick-on mount ABM1M-AT-C (BOM 34b) on head, 15 mm from the cable line
Reach check (cables3d, by conductor chain): pass with notes, worst routed 227.3 mm, cut 300 mm.

## 7. Other

### D13: Pi GPIO26 (pin 37) to the 2813 OFF input (D30; gpio-poweroff)

Regions: head, neck, trunk_top, battery_bay. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.37 (U4 GPIO26 to the 2813 OFF input (D30)) | SW1.OFF (SW1 logic OFF input (D30)) | 26 AWG | blue | 590 | crimp a Molex 08-50-0114 KK 254 terminal (BOM 22b) and push it into this cable's KK 254 housing (BOM 22c) at Pi pin 37 until it clicks, then tug-test (X1, D36: the Pi unplugs) | solder into the board hole OFF |

Joint loops: neck_pitch: leave 42 mm between T013 and T014 (15 mm more than the straight run at the zero pose); head_pitch+head_yaw: leave 82 mm between T038 and T016 (42 mm more than the straight run at the zero pose), one loop over both joints: no tie between them; head_roll: leave 41 mm between T017 and T018 (18 mm more than the straight run at the zero pose)
Reach check (cables3d, by conductor chain): pass with notes, worst routed 542.5 mm, cut 590 mm.

## Splices

Every splice is soldered and covered with adhesive heat shrink. Make each one after all its cables are cut and labelled.

- Lap splice: strip and tin each end, lay the conductors side by side over 3 to 6 wire diameters (NASA-STD-8739.4A 19.4.1 c), solder, then slide on a 15 mm piece of the 3:1 adhesive heat shrink (cut from a 3.5 in BOM 26 kit piece, the smallest size that passes over the wires) so it covers the joint and reaches at least 2 x the wire OD onto the insulation at both ends (19.2.6), and shrink it (BOM T10).
- Keep each splice on a straight run, out of bends and away from joints (7.2.36). The JG20, JG10 and JG30 tails are 30 mm so the sleeve sits past the bend at the servo plug. YD3 and YG3 are staggered: YG3 sits 15 mm past YD3 (7.2.35).
- A splice that no part holds floats: it sits where the wire lengths put it. Lengths are checked fixed end to fixed end through it (CABLE_MAP.md length rule).

| Splice | Where | Cables that meet there |
|---|---|---|
| G | battery_bay | P10, P13, P14, P16 |
| J5 | head | D10, D8, D9, P17 |
| JBN | belly | P11 |
| JBP | belly | P11 |
| JFI | battery_bay | P7 |
| JFO | battery_bay | P7 |
| JG | head | D10, D8, D9, P17 |
| JG10 | trunk_bottom | SD2, SP2 |
| JG20 | trunk_bottom | SD1, SP1 |
| JG30 | trunk_top | SD1, SP3 |
| SPG | belly | P11, SP1, SP2, SP3, SP4, SP5 |
| SPV | belly | P11, SP1, SP2, SP3, SP4, SP5 |
| VSW | battery_bay | P10, P13, P9 |
| YD3 | trunk_top | SD1 |
| YG3 | trunk_top | SD1 |

## Drilled tie holes (D25 ii)

Drilled after printing, before the harness goes in (print/PRINT_PLAN.md After printing): two 4.0 mm holes with the BOM T14 bit, square to the face, one each side of the bundle; deburr both sides. The tie goes in through one hole, behind the wall and out of the other, then round the bundle. Each pair was checked in the CAD (exact rays, zero pose): at least 1.6 mm of plastic round each hole and between them, wall 1.6 to 12 mm, every screw, insert and empty hole at least 1.6 mm off, 1.5 mm free behind the wall, and the strap at least 1 mm from moving parts over the joint sweep.

| Tie | Cables | Part | Holes apart mm | Wall mm | From the cable line mm | Hole centres in the part STL frame mm |
|---|---|---|---|---|---|---|
| T014 | D1, D2, D3, D4, P13 | neck_right_sheet | 12.1 | 5.8 and 5.8 | 18.1 | [26.8, -21.8, 44.7]; [14.8, -21.8, 46.4] |
| T072 | S5 | knee_to_ankle_right_sheet | 7.0 | 3.8 and 3.8 | 9.2 | [-17.8, 68.2, -159.0]; [-10.9, 68.2, -158.1] |
| T084 | S12 | neck_right_sheet | 7.0 | 1.9 and 1.9 | 19.8 | [22.6, -21.8, 66.7]; [15.6, -21.8, 66.4] |

## Bundle ties checked at the test fit (D25)

No printed feature, stick-on mount, tie-hole pair or anchored neighbour cable fits at these points, and D25 adds no printed parts and no STL change. Put a line 32 tie round the bundle only, then at the TEST_PLAN.md 1.4 test fit turn every joint the cable crosses to both limits and check the bundle stays clear of moving parts. Only if it reaches a moving part: a drilled tie-hole pair or a printed anchor there (report it first).

- T016 (D2, P13 on neck_yaw_assembly)
- T017 (D2, D3, D4, P13 on neck_yaw_assembly)
- T023 (D1, D3, D4 on neck_pitch_assembly)
- T024 (D1 on neck_yaw_assembly)
- T026 (D2, D3, D4 on head_assembly): route change tried and not kept: the MB3A patch is on the underside of head_bot_sheet, 28.6 mm below the bundle, so the bundle drops under the head floor and back; the worst routes of D2, D3 and D4 grow by 83 to 84 mm and D2 (cut 550 mm) and D3 (cut 900 mm) would reach with 18 to 25 mm less than the 40 mm slack
- T034 (D3, SP4 on knee_and_ankle_assembly_2)
- T045 (D4, SP5 on knee_and_ankle_assembly_3)
- T085 (S13 on neck_yaw_assembly)
- T089 (SP5 on trunk_assembly): route change tried and not kept: the MB3A patch is on the outer -y face of body_middle_bottom, 33.9 mm away; the SP5 worst route grows from 377 to 440 mm, 448 mm with the twist take-up, past the 430 mm cut

Coverage: 48 active cables, 125 wires, all from the netlist.
