# Harness build sheet

Generated 2026-11-02 05:32 UTC by altaay_lab/wiring/make_harness_build.py from wiring/netlist.yaml and cables3d/cables3d.json. Do not edit by hand.

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

Seats on the brackets, end to end: channel body_back; edge body_back; edge body_back; channel body_back; channel battery_pack_lid; edge body_back; none None; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back; edge body_back
Reach check: pass with notes, worst routed 56.3 mm, cut 120 mm.

### P2: holder - to BMS B-

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PACK.B- (BT1 pack - (cell 1 -)) | BMS.B- (U5 cell stack -) | 16 AWG | black | 120 | use the part's own lead (holder lead), solder joint covered with heat shrink | tin and solder to BMS.B-, heat shrink if bare |

Test: PACK.B- to BMS.B-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PACK.B+

Seats on the brackets, end to end: channel body_back; edge body_back; edge body_back; channel body_back; channel battery_pack_lid; edge body_back; none None; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back; edge body_back
Reach check: pass with notes, worst routed 56.3 mm, cut 120 mm.

### P3: holder series strap to BMS B1

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PACK.MID (BT1 series strap (cell 1 + / cell 2 -)) | BMS.B1 (U5 mid tap (called BM in the brief)) | 26 AWG | yellow | 140 | solder to strap | tin and solder to BMS.B1, heat shrink if bare |

Test: PACK.MID to BMS.B1: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge body_back; channel battery_pack_lid; none None; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; channel body_back
Ties: adhesive tie mount on battery_pack_lid (GAP: no CAD feature); adhesive tie mount on battery_pack_lid (GAP: no CAD feature)
Reach check: fail, worst routed 98.7 mm, cut 120 mm.

### P4: BMS P+ to charger B+

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P+ (U5 pack output + (charge and discharge)) | CHG.B+ (U6 charge output +) | 20 AWG | red | 130 | tin and solder to BMS.P+, heat shrink if bare | tin and solder to CHG.B+, heat shrink if bare |

Test: BMS.P+ to CHG.B+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P- BMS.T

Seats on the brackets, end to end: channel body_back; edge body_back
Reach check: pass, worst routed 10.7 mm, cut 130 mm.

### P5: BMS P- to charger B-

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P- (U5 pack output - (charge and discharge)) | CHG.B- (U6 charge output -) | 20 AWG | black | 130 | tin and solder to BMS.P-, heat shrink if bare | tin and solder to CHG.B-, heat shrink if bare |

Test: BMS.P- to CHG.B-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P+ BMS.T

Seats on the brackets, end to end: channel body_back; edge body_back
Reach check: pass, worst routed 10.7 mm, cut 130 mm.

### P6: BMS P+ to XT30U female +

Regions: battery_bay. Crosses joints: none. BLOCKER-lite: XT30 spot from Tnkr only

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P+ (U5 pack output + (charge and discharge)) | XT30.F+ (J1 pack side +) | 16 AWG | red | 150 | tin and solder to BMS.P+, heat shrink if bare | solder into the XT30U cup, heat shrink over the cup |

Test: BMS.P+ to XT30.F+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P- BMS.T

Seats on the brackets, end to end: channel body_back; none None; edge body_back; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back
Ties: adhesive tie mount on battery_pack_lid (GAP: no CAD feature); adhesive tie mount on battery_pack_lid (GAP: no CAD feature)
Reach check: fail, worst routed 100.2 mm, cut 110 mm.

### P8: BMS P- to XT30U female -

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | BMS.P- (U5 pack output - (charge and discharge)) | XT30.F- (J1 pack side -) | 16 AWG | black | 150 | tin and solder to BMS.P-, heat shrink if bare | solder into the XT30U cup, heat shrink over the cup |

Test: BMS.P- to XT30.F-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to BMS.B- BMS.B1 BMS.B+ BMS.P+ BMS.T

Seats on the brackets, end to end: channel body_back; none None; edge body_back; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge battery_pack_lid; edge body_back; channel body_back
Ties: adhesive tie mount on battery_pack_lid (GAP: no CAD feature); adhesive tie mount on battery_pack_lid (GAP: no CAD feature)
Reach check: fail, worst routed 100.2 mm, cut 110 mm.

### P7: XT30U male + to fuse holder to Pololu 2815 VIN (the holder leads)

Regions: battery_bay. Crosses joints: none. holder leads ship at 90 mm, short of both chains (cables3d: line 92, load 124 mm): each gets a 16 AWG red extension at splice JFI or JFO

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | XT30.M+ (J1 robot side +) | JFI.S (JFI splice) | 16 AWG | red | 20 | solder into the XT30U cup, heat shrink over the cup | join at splice JFI with P7, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | JFI.S (JFI splice) | F1.IN (F1 line side (from XT30)) | 16 AWG | holder lead | 90 | join at splice JFI with P7, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (holder lead), solder joint covered with heat shrink |
| 3 | F1.OUT (F1 load side (to 2815 VIN)) | JFO.S (JFO splice) | 16 AWG | holder lead | 90 | use the part's own lead (holder lead), solder joint covered with heat shrink | join at splice JFO with P7, solder, cover with adhesive heat shrink (BOM 26) |
| 4 | JFO.S (JFO splice) | SW1.VIN (SW1 fused pack in) | 16 AWG | red | 40 | join at splice JFO with P7, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole VIN |

Test: XT30.M+ to JFI.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to XT30.M-; JFI.S to F1.IN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); F1.OUT to JFO.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to F1.IN; JFO.S to SW1.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: channel body_back; none None; edge body_back; edge trunk_top; none None; edge body_middle_bottom; edge body_middle_bottom; edge body_middle_bottom
Ties: adhesive tie mount on body_middle_bottom (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature)
Reach check: fail, worst routed 84.3 mm, cut 90 mm.

### P14: XT30U male - to splice G

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | XT30.M- (J1 robot side -) | G.S (G splice) | 16 AWG | black | 140 | solder into the XT30U cup, heat shrink over the cup | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) |

Test: XT30.M- to G.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to XT30.M+

Seats on the brackets, end to end: channel body_back; none None; edge body_back
Reach check: pass with notes, worst routed 44.7 mm, cut 140 mm.

### P9: 2815 VOUT to splice VSW

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SW1.VOUT (SW1 switched pack out) | VSW.S (VSW splice) | 16 AWG | red | 90 | solder into the board hole VOUT | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) |

Test: SW1.VOUT to VSW.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.VIN SW1.GND

Reach check: pass, worst routed 10.1 mm, cut 90 mm.

### P16: splice G to 2815 GND (control ground)

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | G.S (G splice) | SW1.GND (SW1 ground (large hole)) | 20 AWG | black | 90 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole GND |

Test: G.S to SW1.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Reach check: pass, worst routed 10.6 mm, cut 90 mm.

### P15: 2815 SW pad pair to the panel switch

Regions: battery_bay. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SW1.SW (SW1 switch control terminal (pad pair marked with a switch symbol)) | CTL.1 (SW2 contact) | 26 AWG | white | 150 | solder into the board hole SW | tin and solder to CTL.1, heat shrink if bare |
| 2 | SW1.GND_SW (SW1 GND pad next to SW (pad pair marked with a switch symbol)) | CTL.2 (SW2 contact) | 26 AWG | black | 150 | solder into the board hole GND_SW | tin and solder to CTL.2, heat shrink if bare |

Test: SW1.SW to CTL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.GND_SW SW1.ON; SW1.GND_SW to CTL.2: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SW1.SW SW1.ON

Seats on the brackets, end to end: none None; edge trunk_top; edge trunk_top; edge trunk_top
Reach check: pass with notes, worst routed 58.1 mm, cut 150 mm.

### P10: splices VSW and G to the BEC input leads

Regions: battery_bay, belly. Crosses joints: none. the BEC input leads ship (length not published): cut P10 shorter by their length

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | VSW.S (VSW splice) | U1.IN+ (U1 input + (red lead)) | 16 AWG | red | 150 | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (solder to BEC lead), solder joint covered with heat shrink |
| 2 | G.S (G splice) | U1.IN- (U1 input - (black lead)) | 16 AWG | black | 150 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | use the part's own lead (solder to BEC lead), solder joint covered with heat shrink |

Test: VSW.S to U1.IN+: under 1 ohm, read in ohms (TEST_PLAN.md section 2); G.S to U1.IN-: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None
Reach check: pass, worst routed 58.0 mm, cut 150 mm.

## 2. Belly servo power (D15, D23)

### P11: both BEC output leads joined (JB+ JB-) to the belly power splices SPV and SPG

Regions: belly. Crosses joints: none. BEC output leads ship (gauge and length not published: as shipped); ngspice power-path sim (lead, sim pass only): BEC output peaks 8.3 to 9.1 A while walking

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U1.OUT1+ (U1 output lead 1 + (red)) | JBP.S (JB+ splice) | BEC lead | red | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | U1.OUT2+ (U1 output lead 2 + (red)) | JBP.S (JB+ splice) | BEC lead | red | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | U1.OUT1- (U1 output lead 1 - (black)) | JBN.S (JB- splice) | BEC lead | black | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 4 | U1.OUT2- (U1 output lead 2 - (black)) | JBN.S (JB- splice) | BEC lead | black | - | use the part's own lead (BEC lead), solder joint covered with heat shrink | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) |
| 5 | JBP.S (JB+ splice) | SPV.S (SPV splice) | 16 AWG | red | 100 | join at splice JBP with P11, solder, cover with adhesive heat shrink (BOM 26) | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) |
| 6 | JBN.S (JB- splice) | SPG.S (SPG splice) | 16 AWG | black | 100 | join at splice JBN with P11, solder, cover with adhesive heat shrink (BOM 26) | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) |

Test: U1.OUT1+ to JBP.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT1- U1.OUT1S; U1.OUT2+ to JBP.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT2- U1.OUT2S; U1.OUT1- to JBN.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT1+ U1.OUT1S; U1.OUT2- to JBN.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U1.OUT2+ U1.OUT2S; JBP.S to SPV.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JBN.S to SPG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None
Reach check: fail, worst routed 55.0 mm, cut 60 mm.

### SP1: power pair SPV and SPG to ID 20 BUS 2 (V and G)

Regions: belly, trunk_bottom. Crosses joints: none. 22 AWG because the 08-70-1040 terminal takes 22 to 28 AWG; GND joins SD1 at JG20 before the housing

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV20.BUS2.V (ID20 supply, pin 2) | 22 AWG | red | 150 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG20.S (JG20 splice) | 22 AWG | black | 130 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG20.S (JG20 splice) | SV20.BUS2.G (ID20 ground, pin 1) | 22 AWG | black | 20 | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV20.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG20.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG20.S to SV20.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; channel trunk_top; none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top; edge trunk_top
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature)
Reach check: pass with notes, worst routed 94.5 mm, cut 150 mm.

### SP2: power pair SPV and SPG to ID 10 BUS 2 (V and G)

Regions: belly, trunk_bottom. Crosses joints: none. GND joins SD2 at JG10

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV10.BUS2.V (ID10 supply, pin 2) | 22 AWG | red | 150 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG10.S (JG10 splice) | 22 AWG | black | 130 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG10.S (JG10 splice) | SV10.BUS2.G (ID10 ground, pin 1) | 22 AWG | black | 20 | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV10.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG10.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG10.S to SV10.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; channel trunk_top; edge trunk_top; none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature)
Reach check: pass with notes, worst routed 93.2 mm, cut 150 mm.

### SP3: power pair SPV and SPG to ID 30 BUS 2 (V and G)

Regions: belly, trunk_top. Crosses joints: none. GND joins SD1 at JG30

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV30.BUS2.V (ID30 supply, pin 2) | 22 AWG | red | 180 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | JG30.S (JG30 splice) | 22 AWG | black | 160 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | JG30.S (JG30 splice) | SV30.BUS2.G (ID30 ground, pin 1) | 22 AWG | black | 20 | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV30.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to JG30.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG30.S to SV30.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge trunk_bottom; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge trunk_top; edge trunk_top
Ties: adhesive tie mount on trunk_bottom (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature)
Reach check: pass with notes, worst routed 115.4 mm, cut 180 mm.

### SP4: power pair SPV and SPG to ID 24 BUS 1 (V and G), left leg

Regions: belly, trunk_bottom, left_leg. Crosses joints: left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee. service loop at every leg joint; ties in cables3d.json retention

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV24.BUS1.V (ID24 supply, pin 2) | 22 AWG | red | 390 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | SV24.BUS1.G (ID24 ground, pin 1) | 22 AWG | black | 390 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV24.BUS1.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to SV24.BUS1.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; none None; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; none None; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side
Ties: adhesive tie mount on roll_motor_bottom (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet; adhesive tie mount on roll_motor_top (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 347.5 mm, cut 545 mm.

### SP5: power pair SPV and SPG to ID 14 BUS 1 (V and G), right leg

Regions: belly, trunk_bottom, right_leg. Crosses joints: right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee. service loop at every leg joint; ties in cables3d.json retention

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SPV.S (SPV splice) | SV14.BUS1.V (ID14 supply, pin 2) | 22 AWG | red | 420 | join at splice SPV with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | SPG.S (SPG splice) | SV14.BUS1.G (ID14 ground, pin 1) | 22 AWG | black | 420 | join at splice SPG with P11, SP1, SP2, SP3, SP4, SP5, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (DATA position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |

Test: SPV.S to SV14.BUS1.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2); SPG.S to SV14.BUS1.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; channel right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; none None; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_side
Ties: adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_left_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_left_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet; adhesive tie mount on roll_motor_top (GAP: no CAD feature); cable tie on None (GAP: no CAD feature); adhesive tie mount on roll_motor_top (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature)
Reach check: pass with notes, worst routed 376.8 mm, cut 545 mm.

## 3. Servo data leads and kit cables

### SD1: adapter H3 data lead: DATA and GND only (V position empty), data Y at YD3 to ID 20 and ID 30, GND Y at YG3 into the SP1 and SP3 grounds

Regions: trunk_top, trunk_bottom. Crosses joints: none. branch a rule 149.0 (adapter to ID 20), branch b rule 172.5 (adapter to ID 30); housing Molex 50-37-5033 with 2 terminals at H3

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U2.H3.D (U2 bus data (H3 pin 1)) | YD3.S (YD3 splice) | 22 AWG | yellow | 30 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | U2.H3.G (U2 ground (H3 pin 3)) | YG3.S (YG3 splice) | 22 AWG | black | 30 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | YD3.S (YD3 splice) | SV20.BUS2.D (ID20 data, pin 3) | 22 AWG | yellow | 130 | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 4 | YG3.S (YG3 splice) | JG20.S (JG20 splice) | 22 AWG | black | 120 | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG20 with SD1, SP1, solder, cover with adhesive heat shrink (BOM 26) |
| 5 | YD3.S (YD3 splice) | SV30.BUS2.D (ID30 data, pin 3) | 22 AWG | yellow | 160 | join at splice YD3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 6 | YG3.S (YG3 splice) | JG30.S (JG30 splice) | 22 AWG | black | 140 | join at splice YG3 with SD1, solder, cover with adhesive heat shrink (BOM 26) | join at splice JG30 with SD1, SP3, solder, cover with adhesive heat shrink (BOM 26) |

Test: U2.H3.D to YD3.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H3.V U2.H3.G; U2.H3.G to YG3.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H3.D U2.H3.V; YD3.S to SV20.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YG3.S to JG20.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YD3.S to SV30.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2); YG3.S to JG30.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: edge trunk_top; edge trunk_top; edge trunk_top; none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top; edge trunk_top; edge trunk_top; edge trunk_top
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature)
Reach check: fail, worst routed 118.7 mm, cut 150 mm.

### SD2: adapter H5 data lead: DATA and GND only, to ID 10 (DATA) and JG10 (GND)

Regions: trunk_top, trunk_bottom. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U2.H5.D (U2 bus data (H5 pin 1)) | SV10.BUS2.D (ID10 data, pin 3) | 22 AWG | yellow | 150 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks. Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test |
| 2 | U2.H5.G (U2 ground (H5 pin 3)) | JG10.S (JG10 splice) | 22 AWG | black | 140 | crimp a Molex 08-70-1040 terminal with the PA-09 crimper (BOM T3), push it into a Molex 50-37-5033 housing until it clicks (V position left empty). Copy the position order of a servo kit cable housing exactly, check it with a meter, then tug-test | join at splice JG10 with SD2, SP2, solder, cover with adhesive heat shrink (BOM 26) |

Test: U2.H5.D to SV10.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H5.V U2.H5.G; U2.H5.G to JG10.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U2.H5.D U2.H5.V

Seats on the brackets, end to end: none None; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top
Ties: cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 89.8 mm, cut 150 mm.

### S2: kit cable ID 20 BUS 1 to ID 21 BUS 2

Regions: trunk_bottom, left_leg. Crosses joints: left_hip_yaw. BLOCKER test fit (rule 2.3 mm over 150)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV20.BUS1.D (ID20 data, pin 3) | SV21.BUS2.D (ID21 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV20.BUS1.V (ID20 supply, pin 2) | SV21.BUS2.V (ID21 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV20.BUS1.G (ID20 ground, pin 1) | SV21.BUS2.G (ID21 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV20.BUS1.D to SV21.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.V SV20.BUS1.G; SV20.BUS1.V to SV21.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.D SV20.BUS1.G; SV20.BUS1.G to SV21.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV20.BUS1.D SV20.BUS1.V

Seats on the brackets, end to end: channel trunk_top; none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; channel trunk_top; none None; edge trunk_top; edge left_roll_to_pitch
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); cable tie on None (GAP: no CAD feature); adhesive tie mount on roll_motor_top (GAP: no CAD feature)
Reach check: fail, worst routed 131.8 mm, cut 150 mm.

### S3: kit cable ID 21 to ID 22

Regions: left_leg. Crosses joints: left_hip_roll. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV21.BUS1.D (ID21 data, pin 3) | SV22.BUS2.D (ID22 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV21.BUS1.V (ID21 supply, pin 2) | SV22.BUS2.V (ID22 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV21.BUS1.G (ID21 ground, pin 1) | SV22.BUS2.G (ID22 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV21.BUS1.D to SV22.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.V SV21.BUS1.G; SV21.BUS1.V to SV22.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.D SV21.BUS1.G; SV21.BUS1.G to SV22.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV21.BUS1.D SV21.BUS1.V

Seats on the brackets, end to end: none None; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; edge left_roll_to_pitch; none None; edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties: adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature)
Reach check: pass with notes, worst routed 88.0 mm, cut 150 mm.

### S4: kit cable ID 22 to ID 23

Regions: left_leg. Crosses joints: left_hip_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV22.BUS1.D (ID22 data, pin 3) | SV23.BUS2.D (ID23 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV22.BUS1.V (ID22 supply, pin 2) | SV23.BUS2.V (ID23 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV22.BUS1.G (ID22 ground, pin 1) | SV23.BUS2.G (ID23 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV22.BUS1.D to SV23.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.V SV22.BUS1.G; SV22.BUS1.V to SV23.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.D SV22.BUS1.G; SV22.BUS1.G to SV23.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV22.BUS1.D SV22.BUS1.V

Seats on the brackets, end to end: none None; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties: adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet
Reach check: pass with notes, worst routed 95.8 mm, cut 150 mm.

### S5: kit cable ID 23 BUS 1 to ID 24 BUS 2

Regions: left_leg. Crosses joints: left_knee. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV23.BUS1.D (ID23 data, pin 3) | SV24.BUS2.D (ID24 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV23.BUS1.V (ID23 supply, pin 2) | SV24.BUS2.V (ID24 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV23.BUS1.G (ID23 ground, pin 1) | SV24.BUS2.G (ID24 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV23.BUS1.D to SV24.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.V SV23.BUS1.G; SV23.BUS1.V to SV24.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.D SV23.BUS1.G; SV23.BUS1.G to SV24.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV23.BUS1.D SV23.BUS1.V

Seats on the brackets, end to end: none None; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge knee_to_ankle_right_sheet; edge foot_side
Ties: existing printed feature on knee_to_ankle_right_sheet; adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature)
Reach check: pass with notes, worst routed 109.8 mm, cut 150 mm.

### S7: kit cable ID 10 to ID 11

Regions: trunk_bottom, right_leg. Crosses joints: right_hip_yaw. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV10.BUS1.D (ID10 data, pin 3) | SV11.BUS2.D (ID11 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV10.BUS1.V (ID10 supply, pin 2) | SV11.BUS2.V (ID11 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV10.BUS1.G (ID10 ground, pin 1) | SV11.BUS2.G (ID11 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV10.BUS1.D to SV11.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.V SV10.BUS1.G; SV10.BUS1.V to SV11.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.D SV10.BUS1.G; SV10.BUS1.G to SV11.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV10.BUS1.D SV10.BUS1.V

Seats on the brackets, end to end: channel trunk_top; none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge right_roll_to_pitch
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on body_middle_bottom (GAP: no CAD feature); adhesive tie mount on roll_motor_top (GAP: no CAD feature)
Reach check: fail, worst routed 133.4 mm, cut 150 mm.

### S8: kit cable ID 11 to ID 12

Regions: right_leg. Crosses joints: right_hip_roll. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV11.BUS1.D (ID11 data, pin 3) | SV12.BUS2.D (ID12 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV11.BUS1.V (ID11 supply, pin 2) | SV12.BUS2.V (ID12 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV11.BUS1.G (ID11 ground, pin 1) | SV12.BUS2.G (ID12 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV11.BUS1.D to SV12.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.V SV11.BUS1.G; SV11.BUS1.V to SV12.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.D SV11.BUS1.G; SV11.BUS1.G to SV12.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV11.BUS1.D SV11.BUS1.V

Seats on the brackets, end to end: none None; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; channel right_roll_to_pitch; none None; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch
Ties: adhesive tie mount on roll_motor_bottom (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature)
Reach check: pass with notes, worst routed 103.9 mm, cut 150 mm.

### S9: kit cable ID 12 to ID 13

Regions: right_leg. Crosses joints: right_hip_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV12.BUS1.D (ID12 data, pin 3) | SV13.BUS2.D (ID13 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV12.BUS1.V (ID12 supply, pin 2) | SV13.BUS2.V (ID13 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV12.BUS1.G (ID12 ground, pin 1) | SV13.BUS2.G (ID13 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV12.BUS1.D to SV13.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.V SV12.BUS1.G; SV12.BUS1.V to SV13.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.D SV12.BUS1.G; SV12.BUS1.G to SV13.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV12.BUS1.D SV12.BUS1.V

Seats on the brackets, end to end: none None; edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet
Ties: adhesive tie mount on knee_to_ankle_left_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature)
Reach check: pass with notes, worst routed 102.6 mm, cut 150 mm.

### S10: kit cable ID 13 to ID 14

Regions: right_leg. Crosses joints: right_knee. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV13.BUS1.D (ID13 data, pin 3) | SV14.BUS2.D (ID14 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV13.BUS1.V (ID13 supply, pin 2) | SV14.BUS2.V (ID14 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV13.BUS1.G (ID13 ground, pin 1) | SV14.BUS2.G (ID14 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV13.BUS1.D to SV14.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.V SV13.BUS1.G; SV13.BUS1.V to SV14.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.D SV13.BUS1.G; SV13.BUS1.G to SV14.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV13.BUS1.D SV13.BUS1.V

Seats on the brackets, end to end: none None; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge knee_to_ankle_right_sheet; edge foot_side
Ties: adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet
Reach check: pass with notes, worst routed 108.9 mm, cut 150 mm.

### S11: kit cable ID 30 BUS 1 to ID 31 BUS 2

Regions: trunk_top, neck. Crosses joints: neck_pitch. BLOCKER test fit

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV30.BUS1.D (ID30 data, pin 3) | SV31.BUS2.D (ID31 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV30.BUS1.V (ID30 supply, pin 2) | SV31.BUS2.V (ID31 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV30.BUS1.G (ID30 ground, pin 1) | SV31.BUS2.G (ID31 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV30.BUS1.D to SV31.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.V SV30.BUS1.G; SV30.BUS1.V to SV31.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.D SV30.BUS1.G; SV30.BUS1.G to SV31.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV30.BUS1.D SV30.BUS1.V

Seats on the brackets, end to end: none None; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw
Ties: adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet
Reach check: pass with notes, worst routed 98.4 mm, cut 150 mm.

### S12: kit cable ID 31 to ID 32

Regions: neck. Crosses joints: head_pitch, head_yaw. BLOCKER test fit (113 mm over 150); contingency X1/X2 made lead 270 mm

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV31.BUS1.D (ID31 data, pin 3) | SV32.BUS2.D (ID32 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV31.BUS1.V (ID31 supply, pin 2) | SV32.BUS2.V (ID32 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV31.BUS1.G (ID31 ground, pin 1) | SV32.BUS2.G (ID32 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV31.BUS1.D to SV32.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.V SV31.BUS1.G; SV31.BUS1.V to SV32.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.D SV31.BUS1.G; SV31.BUS1.G to SV32.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV31.BUS1.D SV31.BUS1.V

Seats on the brackets, end to end: none None; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw
Ties: cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature)
Reach check: pass with notes, worst routed 89.7 mm, cut 150 mm.

### S13: kit cable ID 32 to ID 33

Regions: neck, head. Crosses joints: head_roll. fits (2.7 mm margin)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SV32.BUS1.D (ID32 data, pin 3) | SV33.BUS2.D (ID33 data, pin 3) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 2 | SV32.BUS1.V (ID32 supply, pin 2) | SV33.BUS2.V (ID33 supply, pin 2) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |
| 3 | SV32.BUS1.G (ID32 ground, pin 1) | SV33.BUS2.G (ID33 ground, pin 1) | kit cable | kit | 150 | kit cable plug (ships with the servo), no work | kit cable plug (ships with the servo), no work |

Test: SV32.BUS1.D to SV33.BUS2.D: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.V SV32.BUS1.G; SV32.BUS1.V to SV33.BUS2.V: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.D SV32.BUS1.G; SV32.BUS1.G to SV33.BUS2.G: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SV32.BUS1.D SV32.BUS1.V

Seats on the brackets, end to end: none None; edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties: adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on head_bot_sheet (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 106.9 mm, cut 150 mm.

## 4. Power up the neck to the head

### P13: splices VSW and G up the neck to U3 VIN and GND on the head floor

Regions: battery_bay, trunk_top, neck, head. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. drop about 0.09 V at 2.5 A over 2 x 0.55 m of 20 AWG [I]

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | VSW.S (VSW splice) | U3.VIN (U3 input from VSW) | 20 AWG | red | 550 | join at splice VSW with P10, P13, P9, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole VIN |
| 2 | G.S (G splice) | U3.GND.1 (U3 ground (input side)) | 20 AWG | black | 550 | join at splice G with P10, P13, P14, P16, solder, cover with adhesive heat shrink (BOM 26) | solder into the board hole 1 |

Test: VSW.S to U3.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); G.S to U3.GND.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none None; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on head_bot_sheet (GAP: no CAD feature)
Reach check: pass with notes, worst routed 441.1 mm, cut 550 mm.

### P12: U3 VOUT and GND to Pi pin 2 and pin 6

Regions: head. Crosses joints: none. exact spot of U3 on the floor not fixed

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | U3.VOUT (U3 5 V out) | PI.2 (U4 5V) | 20 AWG | red | 130 | solder into the board hole VOUT | solder at the Pi header (pin 2) |
| 2 | U3.GND.2 (U3 ground (output side)) | PI.6 (U4 GND) | 20 AWG | black | 130 | solder into the board hole 2 | solder at the Pi header (pin 6) |

Test: U3.VOUT to PI.2: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U3.VIN U3.GND.1 U3.GND.2 U3.EN U3.PG; U3.GND.2 to PI.6: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to U3.VIN U3.GND.1 U3.VOUT U3.EN U3.PG

Reach check: pass, worst routed 33.7 mm, cut 130 mm.

### P17: Pi pin 4 and pin 14 to splices J5 and JG

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.4 (U4 5V) | J5.S (J5 splice) | 20 AWG | red | 90 | solder at the Pi header (pin 4) | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 2 | PI.14 (U4 GND) | JG.S (JG splice) | 20 AWG | black | 90 | solder at the Pi header (pin 14) | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: PI.4 to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.5 PI.6 PI.9; PI.14 to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6

Reach check: pass, worst routed 28.9 mm, cut 90 mm.

## 5. Pi, IMU and feet

### D1: Pi micro-USB data port to adapter USB-C

Regions: head, neck, trunk_top, belly. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. coil the slack in the belly

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.USB (U4 micro-USB OTG data port) | U2.USB (U2 USB-C to the CH343P serial bridge) | USB 2.0 cable | black jacket | 900 | bought cable end (micro-USB B plug), plug in | bought cable end (USB-C plug), plug in |

Test: PI.USB to U2.USB: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none None; edge body_middle_top; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_yaw_to_roll
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on body_middle_bottom (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature)
Reach check: pass with notes, worst routed 523.0 mm, cut 900 mm.

### D2: Pi to BNO055 (3V3, GND, SDA, SCL)

Regions: head, neck, trunk_top. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.1 (U4 3V3) | BNO.VIN (U7 supply) | 26 AWG | red | 550 | solder at the Pi header (pin 1) | solder |
| 2 | PI.9 (U4 GND) | BNO.GND (U7 ground) | 26 AWG | black | 550 | solder at the Pi header (pin 9) | solder |
| 3 | PI.3 (U4 GPIO2 SDA) | BNO.SDA (U7 I2C data) | 26 AWG | blue | 550 | solder at the Pi header (pin 3) | solder |
| 4 | PI.5 (U4 GPIO3 SCL) | BNO.SCL (U7 I2C clock) | 26 AWG | yellow | 550 | solder at the Pi header (pin 5) | solder |

Test: PI.1 to BNO.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.2 PI.3 PI.4 PI.5 PI.6 PI.9; PI.9 to BNO.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.3 to BNO.SDA: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.4 PI.5 PI.6 PI.9; PI.5 to BNO.SCL: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.6 PI.9

Seats on the brackets, end to end: none None; edge trunk_bottom; edge roll_motor_top; edge trunk_top; edge roll_motor_top; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_top; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none None; edge neck_right_sheet; edge neck_right_sheet; edge neck_right_sheet; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on trunk_top (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 439.3 mm, cut 550 mm.

### D3: Pi to left foot switches, with pull-up R4 at the header

Regions: head, neck, trunk_top, trunk_bottom, left_leg. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll, left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.17 (U4 3V3) | RFL.1 (R4 3V3 side (Pi pin 17)) | resistor lead | none | 0 | solder at the Pi header (pin 17) | use the part's own lead (resistor lead), solder joint covered with heat shrink |
| 2 | RFL.2 (R4 input side (Pi pin 15)) | PI.15 (U4 GPIO22 left foot) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | solder at the Pi header (pin 15) |
| 3 | PI.15 (U4 GPIO22 left foot) | FSL1.NO (SL1 normally open) | 26 AWG | green | 900 | solder at the Pi header (pin 15) | tin and solder to FSL1.NO, heat shrink if bare |
| 4 | PI.9 (U4 GND) | FSL1.COM (SL1 common) | 26 AWG | black | 900 | solder at the Pi header (pin 9) | tin and solder to FSL1.COM, heat shrink if bare |
| 5 | FSL1.NO (SL1 normally open) | FSL2.NO (SL2 normally open) | 26 AWG | green | 110 | tin and solder to FSL1.NO, heat shrink if bare | tin and solder to FSL2.NO, heat shrink if bare |
| 6 | FSL1.COM (SL1 common) | FSL2.COM (SL2 common) | 26 AWG | black | 110 | tin and solder to FSL1.COM, heat shrink if bare | tin and solder to FSL2.COM, heat shrink if bare |

Test: PI.17 to RFL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RFL.2 to PI.15: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RFL.1; PI.15 to FSL1.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.9 to FSL1.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; FSL1.NO to FSL2.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSL1.COM FSL1.NC; FSL1.COM to FSL2.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSL1.NO FSL1.NC

Seats on the brackets, end to end: none None; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none None; edge body_middle_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge trunk_top; edge trunk_bottom; edge trunk_bottom; edge roll_motor_bottom; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; channel left_roll_to_pitch; none None; edge left_roll_to_pitch; edge left_roll_to_pitch; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge left_roll_to_pitch; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; none None; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_top; channel foot_top; channel foot_top; edge foot_top; edge foot_top
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); cable tie on None (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on trunk_bottom (GAP: no CAD feature); adhesive tie mount on trunk_bottom (GAP: no CAD feature); adhesive tie mount on roll_motor_bottom (GAP: no CAD feature); adhesive tie mount on roll_motor_bottom (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on left_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on foot_top (GAP: no CAD feature)
Reach check: fail, worst routed 774.2 mm, cut 900 mm.

### D4: Pi to right foot switches, with pull-up R5 at the header

Regions: head, neck, trunk_top, trunk_bottom, right_leg. Crosses joints: neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.17 (U4 3V3) | RFR.1 (R5 3V3 side (Pi pin 17)) | resistor lead | none | 0 | solder at the Pi header (pin 17) | use the part's own lead (resistor lead), solder joint covered with heat shrink |
| 2 | RFR.2 (R5 input side (Pi pin 13)) | PI.13 (U4 GPIO27 right foot) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | solder at the Pi header (pin 13) |
| 3 | PI.13 (U4 GPIO27 right foot) | FSR1.NO (SR1 normally open) | 26 AWG | white | 950 | solder at the Pi header (pin 13) | tin and solder to FSR1.NO, heat shrink if bare |
| 4 | PI.9 (U4 GND) | FSR1.COM (SR1 common) | 26 AWG | black | 950 | solder at the Pi header (pin 9) | tin and solder to FSR1.COM, heat shrink if bare |
| 5 | FSR1.NO (SR1 normally open) | FSR2.NO (SR2 normally open) | 26 AWG | white | 110 | tin and solder to FSR1.NO, heat shrink if bare | tin and solder to FSR2.NO, heat shrink if bare |
| 6 | FSR1.COM (SR1 common) | FSR2.COM (SR2 common) | 26 AWG | black | 110 | tin and solder to FSR1.COM, heat shrink if bare | tin and solder to FSR2.COM, heat shrink if bare |

Test: PI.17 to RFR.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RFR.2 to PI.13: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RFR.1; PI.13 to FSR1.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.9 to FSR1.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; FSR1.NO to FSR2.NO: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSR1.COM FSR1.NC; FSR1.COM to FSR2.COM: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to FSR1.NO FSR1.NC

Seats on the brackets, end to end: none None; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge head_pitch_to_yaw; edge neck_right_sheet; edge neck_right_sheet; channel body_middle_top; none None; edge body_middle_top; edge neck_right_sheet; edge trunk_top; edge trunk_top; edge roll_motor_top; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_left_sheet; channel right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; none None; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge right_roll_to_pitch; edge knee_to_ankle_left_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; channel knee_to_ankle_right_sheet; none None; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge knee_to_ankle_right_sheet; edge foot_side; edge foot_top; channel foot_top; channel foot_top; edge foot_top; edge foot_top
Ties: adhesive tie mount on trunk_top (GAP: no CAD feature); adhesive tie mount on neck_right_sheet (GAP: no CAD feature); existing printed feature on neck_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on head_pitch_to_yaw (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); cable tie on None (GAP: no CAD feature); adhesive tie mount on head_yaw_to_roll (GAP: no CAD feature); adhesive tie mount on body_middle_top (GAP: no CAD feature); adhesive tie mount on roll_motor_top (GAP: no CAD feature); adhesive tie mount on roll_motor_top (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on right_roll_to_pitch (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_left_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_left_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); adhesive tie mount on knee_to_ankle_right_sheet (GAP: no CAD feature); existing printed feature on knee_to_ankle_right_sheet; cable tie on None (GAP: no CAD feature); adhesive tie mount on foot_top (GAP: no CAD feature)
Reach check: fail, worst routed 769.6 mm, cut 950 mm.

## 6. Head expression

### D5: Pi to left eye LED and resistor

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.18 (U4 GPIO24 left eye) | RL.1 (R1 GPIO side) | 26 AWG | yellow | 150 | solder at the Pi header (pin 18) | solder |
| 2 | RL.2 (R1 LED side) | LEDL.A (LED1 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDL.K (LED1 cathode) | PI.20 (U4 GND) | 26 AWG | black | 150 | solder | solder at the Pi header (pin 20) |

Test: PI.18 to RL.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RL.2 to LEDL.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RL.1; LEDL.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDL.A

Seats on the brackets, end to end: none None
Reach check: pass, worst routed 59.6 mm, cut 150 mm.

### D6: Pi to right eye LED and resistor

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.16 (U4 GPIO23 right eye) | RR.1 (R2 GPIO side) | 26 AWG | white | 230 | solder at the Pi header (pin 16) | solder |
| 2 | RR.2 (R2 LED side) | LEDR.A (LED2 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDR.K (LED2 cathode) | PI.20 (U4 GND) | 26 AWG | black | 230 | solder | solder at the Pi header (pin 20) |

Test: PI.16 to RR.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RR.2 to LEDR.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RR.1; LEDR.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDR.A

Seats on the brackets, end to end: none None; edge head_roll_mount
Ties: adhesive tie mount on head_roll_mount (GAP: no CAD feature); adhesive tie mount on head_roll_mount (GAP: no CAD feature)
Reach check: pass, worst routed 123.4 mm, cut 230 mm.

### D7: Pi to projector LED and resistor

Regions: head. Crosses joints: none. runs inside the head and through the 4 mm hole drilled in the head wall (D24): cables3d 78 mm worst, the 160 mm cut passes

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.22 (U4 GPIO25 projector) | RP.1 (R3 GPIO side) | 26 AWG | green | 160 | solder at the Pi header (pin 22) | solder |
| 2 | RP.2 (R3 LED side) | LEDP.A (LED3 anode) | resistor lead | none | 0 | use the part's own lead (resistor lead), solder joint covered with heat shrink | use the part's own lead (LED lead), solder joint covered with heat shrink |
| 3 | LEDP.K (LED3 cathode) | PI.20 (U4 GND) | 26 AWG | black | 160 | solder | solder at the Pi header (pin 20) |

Test: PI.22 to RP.1: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; RP.2 to LEDP.A: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to RP.1; LEDP.K to PI.20: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to LEDP.A

Seats on the brackets, end to end: none None; edge head; channel head; channel head; hole flash_light_module; hole flash_reflector_interface
Reach check: pass, worst routed 77.5 mm, cut 160 mm.

### D8: left antenna SG90 lead to Pi pin 33 and splices J5 and JG

Regions: head. Crosses joints: none. lead 250 mm fits

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SGL.SIG (M1 PWM in) | PI.33 (U4 GPIO13 left antenna PWM) | SG90 lead | orange | 250 | servo socket | solder at the Pi header (pin 33) |
| 2 | SGL.VCC (M1 supply) | J5.S (J5 splice) | SG90 lead | red | 250 | servo socket | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | SGL.GND (M1 ground) | JG.S (JG splice) | SG90 lead | brown | 250 | servo socket | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: SGL.SIG to PI.33: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.VCC SGL.GND; SGL.VCC to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.SIG SGL.GND; SGL.GND to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGL.SIG SGL.VCC

Seats on the brackets, end to end: none None
Ties: adhesive tie mount on head (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 117.5 mm, cut 250 mm.

### D9: right antenna SG90 lead to Pi pin 32 and splices J5 and JG

Regions: head. Crosses joints: none. lead 250 mm reaches without an extension: cables3d 170 mm worst, 210 mm with the slack (the 228 mm polyline runs through part centres)

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | SGR.SIG (M2 PWM in) | PI.32 (U4 GPIO12 right antenna PWM) | SG90 lead | orange | 250 | servo socket | solder at the Pi header (pin 32) |
| 2 | SGR.VCC (M2 supply) | J5.S (J5 splice) | SG90 lead | red | 250 | servo socket | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |
| 3 | SGR.GND (M2 ground) | JG.S (JG splice) | SG90 lead | brown | 250 | servo socket | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) |

Test: SGR.SIG to PI.32: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.VCC SGR.GND; SGR.VCC to J5.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.SIG SGR.GND; SGR.GND to JG.S: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to SGR.SIG SGR.VCC

Seats on the brackets, end to end: none None; edge head
Ties: adhesive tie mount on head (GAP: no CAD feature); adhesive tie mount on head (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: pass with notes, worst routed 169.9 mm, cut 270 mm.

### D10: Pi and splices to MAX98357A

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.35 (U4 GPIO19 I2S LRC) | AMP.LRC (U8 I2S frame) | 26 AWG | white | 210 | solder at the Pi header (pin 35) | solder |
| 2 | PI.12 (U4 GPIO18 I2S BCLK) | AMP.BCLK (U8 I2S bit clock) | 26 AWG | yellow | 210 | solder at the Pi header (pin 12) | solder |
| 3 | PI.40 (U4 GPIO21 I2S DIN) | AMP.DIN (U8 I2S data) | 26 AWG | green | 220 | solder at the Pi header (pin 40) | solder |
| 4 | J5.S (J5 splice) | AMP.VIN (U8 supply) | 26 AWG | red | 200 | join at splice J5 with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) | solder |
| 5 | JG.S (JG splice) | AMP.GND (U8 ground) | 26 AWG | black | 200 | join at splice JG with D10, D8, D9, P17, solder, cover with adhesive heat shrink (BOM 26) | solder |

Test: PI.35 to AMP.LRC: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.12 to AMP.BCLK: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; PI.40 to AMP.DIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to PI.1 PI.2 PI.3 PI.4 PI.5 PI.6; J5.S to AMP.VIN: under 1 ohm, read in ohms (TEST_PLAN.md section 2); JG.S to AMP.GND: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge head_roll_mount; edge head_bot_sheet
Ties: adhesive tie mount on head_roll_mount (GAP: no CAD feature); adhesive tie mount on head_roll_mount (GAP: no CAD feature); cable tie on None (GAP: no CAD feature)
Reach check: fail, worst routed 173.7 mm, cut 200 mm.

### D11: MAX98357A to speaker

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | AMP.SPK+ (U8 speaker +) | SPK.+ (LS1 speaker +) | 26 AWG | red | 120 | screw terminal AMP.SPK+ | tin and solder to SPK.+, heat shrink if bare |
| 2 | AMP.SPK- (U8 speaker -) | SPK.- (LS1 speaker -) | 26 AWG | black | 120 | screw terminal AMP.SPK- | tin and solder to SPK.-, heat shrink if bare |

Test: AMP.SPK+ to SPK.+: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to AMP.SPK-; AMP.SPK- to SPK.-: under 1 ohm, read in ohms (TEST_PLAN.md section 2), no short to AMP.SPK+

Seats on the brackets, end to end: none None; edge head_bot_sheet; edge head_bot_sheet
Ties: adhesive tie mount on head_bot_sheet (GAP: no CAD feature)
Reach check: fail, worst routed 73.0 mm, cut 100 mm.

### D12: Pi CSI to Camera Module 3

Regions: head. Crosses joints: none. 

| Wire | From | To | Gauge | Colour | Cut mm | End at From | End at To |
|---|---|---|---|---|---|---|---|
| 1 | PI.CSI (U4 camera connector) | CAM.CSI (U9 camera ribbon) | FPC ribbon | white ribbon | 150 | bought cable end (22-pin FPC), plug in | bought cable end (15-pin FPC), plug in |

Test: PI.CSI to CAM.CSI: under 1 ohm, read in ohms (TEST_PLAN.md section 2)

Seats on the brackets, end to end: none None; edge head_roll_mount; edge head
Ties: adhesive tie mount on head (GAP: no CAD feature); adhesive tie mount on head_roll_mount (GAP: no CAD feature)
Reach check: fail, worst routed 127.1 mm, cut 150 mm.

## Splices

Every splice is soldered and covered with adhesive heat shrink. Make each one after all its cables are cut and labelled.

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

Coverage: 47 active cables, 124 wires, all from the netlist.
