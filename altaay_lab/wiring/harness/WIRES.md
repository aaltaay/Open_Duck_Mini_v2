# Wire list

Built by `wiring/harness/make_harness.py` from `wiring/netlist.yaml`. Every active conductor in that file is below. The charger cable and the flush wells are after the netlist list, because they are not in the netlist yet.

Part numbers reused, not drawn up here:

- Mini-SPOX housing 50-37-5033 and contact 08-70-1040, already BOM lines 21 and 22, for every servo plug.
- KK 254 contact 08-50-0114, already BOM line 22b. Brass, 22 to 30 AWG, 2.5 A, insulation 1.57 mm maximum. Cited from the Molex 2759 sheet (https://www.newbue.sg/datasheets/f5/08-50-0114.pdf) and the 2759 catalog page (https://storage.sea.com.ua/tech_info/molex/MX2759.pdf).
- KK 254 friction-ramp housings from the Molex 2695 series chart (https://www.molex.com/en-us/products/series-chart/2695): 2 circuits 0022012027, 3 circuits 0022012037, 5 circuits 0022012057. The 2-circuit datasheet prints 0022012027 (https://asset.conrad.com/media10/add/160267/c1/-/en/002447773DS00/tehnicni-podatki-2447773-molex-ohisje-kabelske-vticnice-skupno-stevilo-polov-2-osnovna-mreza-254-mm-22012027-1-kos-bag.pdf). The chart prints the same parts as 22012027, 22012037 and 22012057.
- WAGO 221-413 (3 ports) and 221-415 (5 ports), already BOM line 26b. 24 to 12 AWG, strip 11 mm, UL 20 A. Cited from the 221-413 sheet (https://susacdn.azureedge.net/specsheets/Wago/221-413.pdf) and the 221-415 sheet (https://www.mouser.com/datasheet/2/737/221_415-1928680.pdf).
- Amass XT30U, already BOM line 12, for the battery plug and the neck plug on cable P13.

A new distribution board is not added. The WAGO levers already on that BOM line are the distribution nodes. One 221 body has at most 5 ports (cited). The servo plus node and the servo ground node each have 6 wires, so each uses one 221-415 and one 221-413. The ground node G uses one 221-415 (4 wires). The switched plus node VSW uses one 221-413 (3 wires). That is 3 of 221-415 and 3 of 221-413, which is the pocket pack already on BOM line 26b (calc only: 1+1+1 and 1+1+1). The 221-412 pieces in that pack are not needed.

The sixth port is a short jumper of the same 16 AWG between port 5 of the 221-415 and port 1 of the 221-413. Strip 11 mm each end (cited). The free length between the two clamps was not measured. BLOCKER for a pre-cut length. Cut it when the two levers sit side by side.

Jumper current, servo plus, is the sum of the SP4 and SP5 peaks because those two wires are the only loads on the small lever. 1.98 A + 2.11 A = 4.09 A (calc only, from the netlist peaks). 4.09 A is under the cited 20 A. Use 16 AWG for the jumper, the same gauge as P11, not 22 AWG: 4.09 A is over the 3.0 A Mini-SPOX figure, and this jumper is a WAGO joint, not a Mini-SPOX joint. The ground jumper is the same sum on the black side.

## Cable DC1

chest CHG+ to DK2, DK2 to the 5 A fuse F2, F2 to BMS P+ (D43)

Joints: none. This cable does not cross a moving joint.

Route polyline 135.7 mm is the netlist figure from cables3d (CAD check only).

### DC1 wire 1

- From: DKP.CHG
- To: DK2.VIN
- Net: CHG_IN
- From end: J9 pin CHG (charge strip (z 58.5 to 76)). solder pad.
- To end: D2 pin VIN (from the CHG+ strip). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 60 mm, from the netlist.
- Netlist current, mean / peak / fall: 1 / 1 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC1 wire 2

- From: JGD.S
- To: DK2.GND
- Net: GND
- From end: JGD pin S (splice). Solder splice, heat shrink. Pin is JGD.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: D2 pin GND (ground). solder pad.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 60 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC1 wire 3

- From: DK2.VOUT
- To: F2.IN
- Net: CHG_D
- From end: D2 pin VOUT (to the 5 A fuse). solder pad.
- To end: F2 pin IN (from DK2). holder lead.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 180 mm, from the netlist. The cut is 44.3 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1 / 1 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC1 wire 4

- From: F2.OUT
- To: BMS.P+
- Net: PACK_P
- From end: F2 pin OUT (to JFI (PACK_P)). holder lead.
- To end: U5 pin P+ (pack output + (charge and discharge)). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 110 mm, from the netlist.
- Netlist current, mean / peak / fall: 1 / 1 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable DC2

chest GND to the splice JGD inside the trunk, JGD to BMS P- (D43, D50)

Joints: none. This cable does not cross a moving joint.

Route polyline 160.1 mm is the netlist figure from cables3d (CAD check only).

### DC2 wire 1

- From: DKP.GND
- To: JGD.S
- Net: GND
- From end: J9 pin GND (ground strip (z 19.5 to 37)). solder pad.
- To end: JGD pin S (splice). Solder splice, heat shrink. Pin is JGD.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: black
- Cut: 60 mm, from the netlist.

### DC2 wire 2

- From: JGD.S
- To: BMS.P-
- Net: GND
- From end: JGD pin S (splice). Solder splice, heat shrink. Pin is JGD.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: U5 pin P- (pack output - (charge and discharge)). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: black
- Cut: 210 mm, from the netlist. The cut is 49.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 2.1 / 2.9 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable DC3

chest SENSE to the splice JSN inside the trunk, JSN to the cell NTC and to the wake branch at SW1 ON (D43)

Joints: none. This cable does not cross a moving joint.

Route polyline 179.4 mm is the netlist figure from cables3d (CAD check only).

### DC3 wire 1

- From: DKP.SNS
- To: JSN.S
- Net: SNS
- From end: J9 pin SNS (sense strip (z 39 to 56.5)). solder pad.
- To end: JSN pin S (splice). Solder splice, heat shrink. Pin is JSN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 60 mm, from the netlist.

### DC3 wire 2

- From: JSN.S
- To: RT1.1
- Net: SNS
- From end: JSN pin S (splice). Solder splice, heat shrink. Pin is JSN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: RT1 pin 1 (to SENSE). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 220 mm, from the netlist. The cut is 40.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC3 wire 3

- From: RT1.2
- To: BMS.P-
- Net: GND
- From end: RT1 pin 2 (to GND). solder.
- To end: U5 pin P- (pack output - (charge and discharge)). solder pad.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 120 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC3 wire 4

- From: JSN.S
- To: WK1.A
- Net: SNS
- From end: JSN pin S (splice). Solder splice, heat shrink. Pin is JSN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: D3 pin A (from SENSE). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 180 mm, from the netlist. The cut is 0.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC3 wire 5

- From: WK1.K
- To: SW1.ON
- Net: SW1_ON
- From end: D3 pin K (to SW1 ON). solder.
- To end: SW1 pin ON (logic ON input (dock wake, D43)). solder in 0.1 in hole.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: 0 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable DC4

chest SYS to DK6, DK6 and DK7 to SW1 VIN (D50)

Joints: none. This cable does not cross a moving joint.

Route polyline 149.5 mm is the netlist figure from cables3d (CAD check only).

### DC4 wire 1

- From: DKP.SYS
- To: DK6.VIN
- Net: SYS_IN
- From end: J9 pin SYS (dock supply strip (z 0 to 17.5)). solder pad.
- To end: D4 pin VIN (from the SYS strip). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 190 mm, from the netlist. The cut is 40.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1 / 1.8 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC4 wire 2

- From: DK6.VOUT
- To: SW1.VIN
- Net: PACK_OR
- From end: D4 pin VOUT (to SW1 VIN). solder pad.
- To end: SW1 pin VIN (pack in after the D50 ideal-diode OR (DK7 soldered here, DK6 output joins)). solder in large hole.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 70 mm, from the netlist.
- Netlist current, mean / peak / fall: 1 / 1.8 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC4 wire 3

- From: DK6.GND
- To: SW1.GND
- Net: GND
- From end: D4 pin GND (ground). solder pad.
- To end: SW1 pin GND (ground (large hole)). solder in large hole.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 80 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC4 wire 4

- From: DK7.VOUT
- To: SW1.VIN
- Net: PACK_OR
- From end: D5 pin VOUT (to SW1 VIN). solder pad.
- To end: SW1 pin VIN (pack in after the D50 ideal-diode OR (DK7 soldered here, DK6 output joins)). solder in large hole.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: red
- Cut: 60 mm, from the netlist.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### DC4 wire 5

- From: DK7.GND
- To: SW1.GND
- Net: GND
- From end: D5 pin GND (ground). solder pad.
- To end: SW1 pin GND (ground (large hole)). solder in large hole.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 70 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.001 / 0.001 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P1

holder + to BMS B+

Joints: none. This cable does not cross a moving joint.

Route polyline 30.1 mm is the netlist figure from cables3d (CAD check only).

### P1 wire 1

- From: PACK.B+
- To: BMS.B+
- Net: PACK_P
- From end: BT1 pin B+ (pack + (cell 2 +)). holder lead.
- To end: U5 pin B+ (cell stack +). solder pad.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: red
- Cut: 120 mm, from the netlist. The cut is 89.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P2

holder - to BMS B-

Joints: none. This cable does not cross a moving joint.

Route polyline 30.1 mm is the netlist figure from cables3d (CAD check only).

### P2 wire 1

- From: PACK.B-
- To: BMS.B-
- Net: CELL_N
- From end: BT1 pin B- (pack - (cell 1 -)). holder lead.
- To end: U5 pin B- (cell stack -). solder pad.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: black
- Cut: 120 mm, from the netlist. The cut is 89.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P3

holder series strap to BMS B1

Joints: none. This cable does not cross a moving joint.

Route polyline 30.1 mm is the netlist figure from cables3d (CAD check only).

### P3 wire 1

- From: PACK.MID
- To: BMS.B1
- Net: CELL_MID
- From end: BT1 pin MID (series strap (cell 1 + / cell 2 -)). solder to strap.
- To end: U5 pin B1 (mid tap (called BM in the brief)). solder pad.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 140 mm, from the netlist. The cut is 109.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0 / 0 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P4

BMS P+ to charger B+

Joints: none. This cable does not cross a moving joint.

Route polyline 39.4 mm is the netlist figure from cables3d (CAD check only).

### P4 wire 1

- From: BMS.P+
- To: CHG.B+
- Net: PACK_P
- From end: U5 pin P+ (pack output + (charge and discharge)). solder pad.
- To end: U6 pin B+ (charge output +). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: red
- Cut: 130 mm, from the netlist. The cut is 90.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0 / 2 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P5

BMS P- to charger B-

Joints: none. This cable does not cross a moving joint.

Route polyline 39.4 mm is the netlist figure from cables3d (CAD check only).

### P5 wire 1

- From: BMS.P-
- To: CHG.B-
- Net: GND
- From end: U5 pin P- (pack output - (charge and discharge)). solder pad.
- To end: U6 pin B- (charge output -). solder pad.
- Gauge and current: Gauge 20 AWG is the netlist value.
- Color: black
- Cut: 130 mm, from the netlist. The cut is 90.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0 / 2 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P6

BMS P+ to XT30U female +

Joints: none. This cable does not cross a moving joint.

Route polyline 23.5 mm is the netlist figure from cables3d (CAD check only).

### P6 wire 1

- From: BMS.P+
- To: XT30.F+
- Net: PACK_P
- From end: U5 pin P+ (pack output + (charge and discharge)). solder pad.
- To end: J1 pin F+ (pack side +). Amass XT30U solder cup. The shell is the key. No separate crimp contact.
- Gauge and current: Gauge 16 AWG is the netlist value. XT30 continuous rating is marked [I] on BOM line 12. The Amass sheet was not opened this pass. BLOCKER for a cited amp rating of the shell.
- Color: red
- Cut: 150 mm, from the netlist. The cut is 126.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P8

BMS P- to XT30U female -

Joints: none. This cable does not cross a moving joint.

Route polyline 23.5 mm is the netlist figure from cables3d (CAD check only).

### P8 wire 1

- From: BMS.P-
- To: XT30.F-
- Net: GND
- From end: U5 pin P- (pack output - (charge and discharge)). solder pad.
- To end: J1 pin F- (pack side -). Amass XT30U solder cup. The shell is the key. No separate crimp contact.
- Gauge and current: Gauge 16 AWG is the netlist value. XT30 continuous rating is marked [I] on BOM line 12. The Amass sheet was not opened this pass. BLOCKER for a cited amp rating of the shell.
- Color: black
- Cut: 150 mm, from the netlist. The cut is 126.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P7

XT30U male + to fuse holder to Pololu 2815 VIN (the holder leads)

Joints: none. This cable does not cross a moving joint.

Route polyline 42.0 mm is the netlist figure from cables3d (CAD check only).

### P7 wire 1

- From: XT30.M+
- To: JFI.S
- Branch: line
- Net: PACK_P
- From end: J1 pin M+ (robot side +). Amass XT30U solder cup. The shell is the key. No separate crimp contact.
- To end: JFI pin S (splice). Solder splice, heat shrink. Pin is JFI.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 16 AWG is the netlist value. XT30 continuous rating is marked [I] on BOM line 12. The Amass sheet was not opened this pass. BLOCKER for a cited amp rating of the shell.
- Color: red
- Cut: 30 mm, from the netlist.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P7 wire 2

- From: JFI.S
- To: F1.IN
- Branch: line
- Net: PACK_P
- From end: JFI pin S (splice). Solder splice, heat shrink. Pin is JFI.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: F1 pin IN (line side (from XT30)). holder lead.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: holder lead
- Cut: 90 mm, from the netlist. The cut is 48 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P7 wire 3

- From: F1.OUT
- To: JFO.S
- Branch: load
- Net: PACK_F
- From end: F1 pin OUT (load side (to 2815 VIN)). holder lead.
- To end: JFO pin S (splice). Solder splice, heat shrink. Pin is JFO.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: holder lead
- Cut: 90 mm, from the netlist. The cut is 48 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P7 wire 4

- From: JFO.S
- To: DK7.VIN
- Branch: load
- Net: PACK_F
- From end: JFO pin S (splice). Solder splice, heat shrink. Pin is JFO.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: D5 pin VIN (fused pack from JFO). solder pad.
- Gauge and current: Gauge 16 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: red
- Cut: 40 mm, from the netlist.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P14

XT30U male - to splice G

Joints: none. This cable does not cross a moving joint.

Route polyline 52.1 mm is the netlist figure from cables3d (CAD check only).

### P14 wire 1

- From: XT30.M-
- To: G.S
- Net: GND
- From end: J1 pin M- (robot side -). Amass XT30U solder cup. The shell is the key. No separate crimp contact.
- To end: G pin S (splice). WAGO 221-415 port 1, ground lever. No separate contact: the lever clamps the bare wire.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 17 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 3 A (calc only). XT30 continuous rating is marked [I] on BOM line 12. The Amass sheet was not opened this pass. BLOCKER for a cited amp rating of the shell.
- Color: black
- Cut: 140 mm, from the netlist. The cut is 87.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P9

2815 VOUT to splice VSW

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### P9 wire 1

- From: SW1.VOUT
- To: VSW.S
- Net: VSW
- From end: SW1 pin VOUT (switched pack out). solder in large hole.
- To end: VSW pin S (splice). WAGO 221-413 port 1, switched plus lever. No separate contact: the lever clamps the bare wire.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 17 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 3 A (calc only).
- Color: red
- Cut: 90 mm, from the netlist.
- Netlist current, mean / peak / fall: 5.66 / 7.04 / 17 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P16

splice G to 2815 GND (control ground)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### P16 wire 1

- From: G.S
- To: SW1.GND
- Net: GND
- From end: G pin S (splice). WAGO 221-415 port 4, ground lever. No separate contact: the lever clamps the bare wire.
- To end: SW1 pin GND (ground (large hole)). solder in large hole.
- Gauge and current: Gauge 20 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 0.0006 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 19.9994 A (calc only).
- Color: black
- Cut: 90 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.0006 / 0.0006 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P15

2813 A and B to the momentary button (D30; was the 2815 SW pad pair to the panel switch)

Joints: none. This cable does not cross a moving joint.

Route polyline 62.1 mm is the netlist figure from cables3d (CAD check only).

### P15 wire 1

- From: SW1.SW
- To: CTL.1
- Net: CTRL_SW
- From end: SW1 pin SW (switch control terminal (pad pair marked with a switch symbol)). solder in 0.1 in hole.
- To end: SW2 pin 1 (contact). solder lug.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 150 mm, from the netlist. The cut is 87.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 8.4e-05 / 8.4e-05 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P15 wire 2

- From: SW1.GND_SW
- To: CTL.2
- Net: GND
- From end: SW1 pin GND_SW (GND pad next to SW (pad pair marked with a switch symbol)). solder in 0.1 in hole.
- To end: SW2 pin 2 (contact). solder lug.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 150 mm, from the netlist. The cut is 87.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 8.4e-05 / 8.4e-05 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P10

splices VSW and G to the BEC input leads

Joints: none. This cable does not cross a moving joint.

Route polyline 61.1 mm is the netlist figure from cables3d (CAD check only).

### P10 wire 1

- From: VSW.S
- To: U1.IN+
- Net: VSW
- From end: VSW pin S (splice). WAGO 221-413 port 2, switched plus lever. No separate contact: the lever clamps the bare wire.
- To end: U1 pin IN+ (input + (red lead)). solder to BEC lead.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 14.6 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 5.4 A (calc only).
- Color: red
- Cut: 150 mm, from the netlist. The cut is 88.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 4.77 / 6.23 / 14.6 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P10 wire 2

- From: G.S
- To: U1.IN-
- Net: GND
- From end: G pin S (splice). WAGO 221-415 port 2, ground lever. No separate contact: the lever clamps the bare wire.
- To end: U1 pin IN- (input - (black lead)). solder to BEC lead.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 14.6 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 5.4 A (calc only).
- Color: black
- Cut: 150 mm, from the netlist. The cut is 88.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 4.77 / 6.23 / 14.6 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P11

both BEC output leads joined (JB+ JB-) to the belly power splices SPV and SPG

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### P11 wire 1

- From: U1.OUT1+
- To: JBP.S
- Branch: lead1
- Net: SERVO_7V2
- From end: U1 pin OUT1+ (output lead 1 + (red)). BEC lead.
- To end: JB+ pin S (splice). Solder splice, heat shrink. Pin is JBP.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "BEC lead".
- Color: red
- Cut: BLOCKER. The netlist has no cut length.
- Netlist current, mean / peak / fall: 2.13 / 2.78 / 6.3 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P11 wire 2

- From: U1.OUT2+
- To: JBP.S
- Branch: lead2
- Net: SERVO_7V2
- From end: U1 pin OUT2+ (output lead 2 + (red)). BEC lead.
- To end: JB+ pin S (splice). Solder splice, heat shrink. Pin is JBP.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "BEC lead".
- Color: red
- Cut: BLOCKER. The netlist has no cut length.
- Netlist current, mean / peak / fall: 2.13 / 2.78 / 6.3 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P11 wire 3

- From: U1.OUT1-
- To: JBN.S
- Branch: lead1
- Net: GND
- From end: U1 pin OUT1- (output lead 1 - (black)). BEC lead.
- To end: JB- pin S (splice). Solder splice, heat shrink. Pin is JBN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "BEC lead".
- Color: black
- Cut: BLOCKER. The netlist has no cut length.
- Netlist current, mean / peak / fall: 2.13 / 2.78 / 6.3 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P11 wire 4

- From: U1.OUT2-
- To: JBN.S
- Branch: lead2
- Net: GND
- From end: U1 pin OUT2- (output lead 2 - (black)). BEC lead.
- To end: JB- pin S (splice). Solder splice, heat shrink. Pin is JBN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "BEC lead".
- Color: black
- Cut: BLOCKER. The netlist has no cut length.
- Netlist current, mean / peak / fall: 2.13 / 2.78 / 6.3 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P11 wire 5

- From: JBP.S
- To: SPV.S
- Net: SERVO_7V2
- From end: JB+ pin S (splice). Solder splice, heat shrink. Pin is JBP.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: SPV pin S (splice). WAGO 221-415 port 1, servo plus lever. No separate contact: the lever clamps the bare wire.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 12.5 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 7.5 A (calc only).
- Color: red
- Cut: 100 mm, from the netlist.
- Netlist current, mean / peak / fall: 4.25 / 5.56 / 12.5 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P11 wire 6

- From: JBN.S
- To: SPG.S
- Net: GND
- From end: JB- pin S (splice). Solder splice, heat shrink. Pin is JBN.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: SPG pin S (splice). WAGO 221-415 port 1, servo ground lever. No separate contact: the lever clamps the bare wire.
- Gauge and current: Gauge 16 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 12.5 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 7.5 A (calc only).
- Color: black
- Cut: 100 mm, from the netlist.
- Netlist current, mean / peak / fall: 4.25 / 5.56 / 12.5 A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P13

splices VSW and G up the neck to U3 VIN and GND on the head floor

Joints: neck_pitch, head_pitch, head_yaw, head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 349.7 mm is the netlist figure from cables3d (CAD check only).

### P13 wire 1

- From: VSW.S
- To: U3.VIN
- Net: VSW
- From end: VSW pin S (splice). WAGO 221-413 port 3, switched plus lever. No separate contact: the lever clamps the bare wire.
- To end: U3 pin VIN (input from VSW). solder in 0.1 in hole.
- Gauge and current: Gauge 20 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.91 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.09 A (calc only).
- Color: red
- Cut: 550 mm, from the netlist. The cut is 200.3 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.48 / 1.91 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P13 wire 2

- From: G.S
- To: U3.GND.1
- Net: GND
- From end: G pin S (splice). WAGO 221-415 port 3, ground lever. No separate contact: the lever clamps the bare wire.
- To end: U3 pin GND.1 (ground (input side)). solder in 0.1 in hole.
- Gauge and current: Gauge 20 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.91 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.09 A (calc only).
- Color: black
- Cut: 550 mm, from the netlist. The cut is 200.3 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.48 / 1.91 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P12

U3 VOUT and GND to Pi pin 2 and pin 6

Joints: none. This cable does not cross a moving joint.

Route polyline 44.3 mm is the netlist figure from cables3d (CAD check only).

### P12 wire 1

- From: U3.VOUT
- To: PI.2
- Net: 5V
- From end: U3 pin VOUT (5 V out). solder in 0.1 in hole.
- To end: U4 pin 2 (5V). Solder to the header pin. Not a KK crimp: 20 AWG is outside 22 to 30 AWG (cited, Molex 08-50-0114 sheet).
- Gauge and current: Gauge 20 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: red
- Cut: 130 mm, from the netlist. The cut is 85.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.6 / 2.4 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P12 wire 2

- From: U3.GND.2
- To: PI.6
- Net: GND
- From end: U3 pin GND.2 (ground (output side)). solder in 0.1 in hole.
- To end: U4 pin 6 (GND). Solder to the header pin. Not a KK crimp: 20 AWG is outside 22 to 30 AWG (cited, Molex 08-50-0114 sheet).
- Gauge and current: Gauge 20 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: black
- Cut: 130 mm, from the netlist. The cut is 85.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.6 / 2.4 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable P17

Pi pin 4 and pin 14 to splices J5 and JG

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### P17 wire 1

- From: PI.4
- To: J5.S
- Net: 5V
- From end: U4 pin 4 (5V). Solder to the header pin. Not a KK crimp: 20 AWG is outside 22 to 30 AWG (cited, Molex 08-50-0114 sheet).
- To end: J5 pin S (splice). Solder splice, heat shrink. Pin is J5.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 20 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: red
- Cut: 90 mm, from the netlist.
- Netlist current, mean / peak / fall: None / 1.9 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### P17 wire 2

- From: PI.14
- To: JG.S
- Net: GND
- From end: U4 pin 14 (GND). Solder to the header pin. Not a KK crimp: 20 AWG is outside 22 to 30 AWG (cited, Molex 08-50-0114 sheet).
- To end: JG pin S (splice). Solder splice, heat shrink. Pin is JG.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 20 AWG is the netlist value. A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the copper's own amp rating. The gauge stays the netlist gauge.
- Color: black
- Cut: 90 mm, from the netlist.
- Netlist current, mean / peak / fall: None / 1.9 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable D1

Pi micro-USB data port to adapter USB-C

Joints: neck_pitch, head_pitch, head_yaw, head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 320.5 mm is the netlist figure from cables3d (CAD check only).

### D1 wire 1

- From: PI.USB
- To: U2.USB
- Net: USB_LINK
- From end: U4 pin USB (micro-USB OTG data port). The bought cable's own plug (micro-USB B plug).
- To end: U2 pin USB (USB-C to the CH343P serial bridge). The bought cable's own plug (USB-C plug).
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "USB 2.0 cable".
- Color: black jacket
- Cut: 900 mm, from the netlist. The cut is 579.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D2

Pi to BNO055 (3V3, GND, SDA, SCL)

Joints: neck_pitch, head_pitch, head_yaw, head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 329.3 mm is the netlist figure from cables3d (CAD check only).

### D2 wire 1

- From: PI.1
- To: BNO.VIN
- Net: 3V3
- From end: U4 pin 1 (3V3). KK 254 housing 0022012057 position 1, contact 08-50-0114.
- To end: U7 pin VIN (supply). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: red
- Cut: 550 mm, from the netlist. The cut is 220.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D2 wire 2

- From: PI.9
- To: BNO.GND
- Net: GND
- From end: U4 pin 9 (GND). KK 254 housing 0022012057 position 5, contact 08-50-0114.
- To end: U7 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: black
- Cut: 550 mm, from the netlist. The cut is 220.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D2 wire 3

- From: PI.3
- To: BNO.SDA
- Net: I2C_SDA
- From end: U4 pin 3 (GPIO2 SDA). KK 254 housing 0022012057 position 2, contact 08-50-0114.
- To end: U7 pin SDA (I2C data). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: blue
- Cut: 550 mm, from the netlist. The cut is 220.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D2 wire 4

- From: PI.5
- To: BNO.SCL
- Net: I2C_SCL
- From end: U4 pin 5 (GPIO3 SCL). KK 254 housing 0022012057 position 3, contact 08-50-0114.
- To end: U7 pin SCL (I2C clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: yellow
- Cut: 550 mm, from the netlist. The cut is 220.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D3

Pi to left foot switches, with pull-up R4 at the header

Joints: neck_pitch, head_pitch, head_yaw, head_roll, left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 602.4 mm is the netlist figure from cables3d (CAD check only).

### D3 wire 1

- From: PI.17
- To: RFL.1
- Branch: pullup
- Net: 3V3
- From end: U4 pin 17 (3V3). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- To end: R4 pin 1 (3V3 side (Pi pin 17)). resistor lead.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: None / 0.0015 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D3 wire 2

- From: RFL.2
- To: PI.15
- Branch: pullup
- Net: FOOT_L
- From end: R4 pin 2 (input side (Pi pin 15)). resistor lead.
- To end: U4 pin 15 (GPIO22 left foot). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: None / 0.0015 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D3 wire 3

- From: PI.15
- To: FSL1.NO
- Net: FOOT_L
- From end: U4 pin 15 (GPIO22 left foot). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: SL1 pin NO (normally open). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: green
- Cut: 900 mm, from the netlist. The cut is 297.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D3 wire 4

- From: PI.9
- To: FSL1.COM
- Net: GND
- From end: U4 pin 9 (GND). No second contact. Solder this wire to the D2 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: SL1 pin COM (common). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 900 mm, from the netlist. The cut is 297.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D3 wire 5

- From: FSL1.NO
- To: FSL2.NO
- Branch: jumper
- Net: FOOT_L
- From end: SL1 pin NO (normally open). solder terminal.
- To end: SL2 pin NO (normally open). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: green
- Cut: 110 mm, from the netlist.

### D3 wire 6

- From: FSL1.COM
- To: FSL2.COM
- Branch: jumper
- Net: GND
- From end: SL1 pin COM (common). solder terminal.
- To end: SL2 pin COM (common). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 110 mm, from the netlist.

## Cable D4

Pi to right foot switches, with pull-up R5 at the header

Joints: neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 632.4 mm is the netlist figure from cables3d (CAD check only).

### D4 wire 1

- From: PI.17
- To: RFR.1
- Branch: pullup
- Net: 3V3
- From end: U4 pin 17 (3V3). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- To end: R5 pin 1 (3V3 side (Pi pin 17)). resistor lead.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: None / 0.0015 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D4 wire 2

- From: RFR.2
- To: PI.13
- Branch: pullup
- Net: FOOT_R
- From end: R5 pin 2 (input side (Pi pin 13)). resistor lead.
- To end: U4 pin 13 (GPIO27 right foot). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: None / 0.0015 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D4 wire 3

- From: PI.13
- To: FSR1.NO
- Net: FOOT_R
- From end: U4 pin 13 (GPIO27 right foot). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: SR1 pin NO (normally open). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 950 mm, from the netlist. The cut is 317.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D4 wire 4

- From: PI.9
- To: FSR1.COM
- Net: GND
- From end: U4 pin 9 (GND). No second contact. Solder this wire to the D2 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: SR1 pin COM (common). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 950 mm, from the netlist. The cut is 317.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D4 wire 5

- From: FSR1.NO
- To: FSR2.NO
- Branch: jumper
- Net: FOOT_R
- From end: SR1 pin NO (normally open). solder terminal.
- To end: SR2 pin NO (normally open). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 110 mm, from the netlist.

### D4 wire 6

- From: FSR1.COM
- To: FSR2.COM
- Branch: jumper
- Net: GND
- From end: SR1 pin COM (common). solder terminal.
- To end: SR2 pin COM (common). solder terminal.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 110 mm, from the netlist.

## Cable D5

Pi to left eye LED and resistor

Joints: none. This cable does not cross a moving joint.

Route polyline 94.8 mm is the netlist figure from cables3d (CAD check only).

### D5 wire 1

- From: PI.18
- To: RL.1
- Net: EYE_L
- From end: U4 pin 18 (GPIO24 left eye). KK 254 housing 0022012037 position 2, contact 08-50-0114.
- To end: R1 pin 1 (GPIO side). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Peak 0.003 A vs 2.5 A brass rating (cited, Molex 2759 catalog). Margin 2.497 A (calc only). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: yellow
- Cut: 150 mm, from the netlist. The cut is 55.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D5 wire 2

- From: RL.2
- To: LEDL.A
- Branch: joint
- Net: EYE_L_A
- From end: R1 pin 2 (LED side). resistor lead.
- To end: LED1 pin A (anode). LED lead.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D5 wire 3

- From: LEDL.K
- To: PI.20
- Net: GND
- From end: LED1 pin K (cathode). solder.
- To end: U4 pin 20 (GND). KK 254 housing 0022012037 position 3, contact 08-50-0114.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Peak 0.003 A vs 2.5 A brass rating (cited, Molex 2759 catalog). Margin 2.497 A (calc only). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: black
- Cut: 150 mm, from the netlist. The cut is 55.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable D6

Pi to right eye LED and resistor

Joints: none. This cable does not cross a moving joint.

Route polyline 176.8 mm is the netlist figure from cables3d (CAD check only).

### D6 wire 1

- From: PI.16
- To: RR.1
- Net: EYE_R
- From end: U4 pin 16 (GPIO23 right eye). KK 254 housing 0022012037 position 1, contact 08-50-0114.
- To end: R2 pin 1 (GPIO side). solder.
- Gauge and current: Gauge 26 AWG is the netlist value. Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet). Peak 0.003 A vs 2.5 A brass rating (cited, Molex 2759 catalog). Margin 2.497 A (calc only). Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.
- Color: white
- Cut: 230 mm, from the netlist. The cut is 53.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D6 wire 2

- From: RR.2
- To: LEDR.A
- Branch: joint
- Net: EYE_R_A
- From end: R2 pin 2 (LED side). resistor lead.
- To end: LED2 pin A (anode). LED lead.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D6 wire 3

- From: LEDR.K
- To: PI.20
- Net: GND
- From end: LED2 pin K (cathode). solder.
- To end: U4 pin 20 (GND). No second contact. Solder this wire to the D5 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 230 mm, from the netlist. The cut is 53.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable D7

Pi to projector LED and resistor

Joints: none. This cable does not cross a moving joint.

Route polyline 112.4 mm is the netlist figure from cables3d (CAD check only).

### D7 wire 1

- From: PI.22
- To: RP.1
- Net: PROJ
- From end: U4 pin 22 (GPIO25 projector). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: R3 pin 1 (GPIO side). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: green
- Cut: 160 mm, from the netlist. The cut is 47.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D7 wire 2

- From: RP.2
- To: LEDP.A
- Branch: joint
- Net: PROJ_A
- From end: R3 pin 2 (LED side). resistor lead.
- To end: LED3 pin A (anode). LED lead.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "resistor lead".
- Color: none
- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### D7 wire 3

- From: LEDP.K
- To: PI.20
- Net: GND
- From end: LED3 pin K (cathode). solder.
- To end: U4 pin 20 (GND). No second contact. Solder this wire to the D5 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 160 mm, from the netlist. The cut is 47.6 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0.003 / 0.003 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable D8

left antenna SG90 lead to Pi pin 33 and splices J5 and JG

Joints: none. This cable does not cross a moving joint.

Route polyline 133.2 mm is the netlist figure from cables3d (CAD check only).

### D8 wire 1

- From: SGL.SIG
- To: PI.33
- Net: ANT_L
- From end: M1 pin SIG (PWM in). servo.
- To end: U4 pin 33 (GPIO13 left antenna PWM (hardware PWM1, D53)). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: orange
- Cut: 250 mm, from the netlist. The cut is 116.8 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D8 wire 2

- From: SGL.VCC
- To: J5.S
- Net: 5V
- From end: M1 pin VCC (supply). servo.
- To end: J5 pin S (splice). Solder splice, heat shrink. Pin is J5.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: red
- Cut: 250 mm, from the netlist. The cut is 116.8 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D8 wire 3

- From: SGL.GND
- To: JG.S
- Net: GND
- From end: M1 pin GND (ground). servo.
- To end: JG pin S (splice). Solder splice, heat shrink. Pin is JG.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: brown
- Cut: 250 mm, from the netlist. The cut is 116.8 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D9

right antenna SG90 lead to Pi pin 32 and splices J5 and JG

Joints: none. This cable does not cross a moving joint.

Route polyline 228.0 mm is the netlist figure from cables3d (CAD check only).

### D9 wire 1

- From: SGR.SIG
- To: PI.32
- Net: ANT_R
- From end: M2 pin SIG (PWM in). servo.
- To end: U4 pin 32 (GPIO12 right antenna PWM (hardware PWM0, D53)). Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: orange
- Cut: 250 mm, from the netlist. The cut is 22 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D9 wire 2

- From: SGR.VCC
- To: J5.S
- Net: 5V
- From end: M2 pin VCC (supply). servo.
- To end: J5 pin S (splice). Solder splice, heat shrink. Pin is J5.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: red
- Cut: 250 mm, from the netlist. The cut is 22 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D9 wire 3

- From: SGR.GND
- To: JG.S
- Net: GND
- From end: M2 pin GND (ground). servo.
- To end: JG pin S (splice). Solder splice, heat shrink. Pin is JG.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "SG90 lead".
- Color: brown
- Cut: 250 mm, from the netlist. The cut is 22 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D10

Pi and splices to MAX98357A

Joints: none. This cable does not cross a moving joint.

Route polyline 149.5 mm is the netlist figure from cables3d (CAD check only).

### D10 wire 1

- From: PI.35
- To: AMP.LRC
- Net: I2S_LRC
- From end: U4 pin 35 (GPIO19 I2S LRC). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U8 pin LRC (I2S frame). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 220 mm, from the netlist. The cut is 70.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D10 wire 2

- From: PI.12
- To: AMP.BCLK
- Net: I2S_BCLK
- From end: U4 pin 12 (GPIO18 I2S BCLK). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U8 pin BCLK (I2S bit clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 210 mm, from the netlist. The cut is 60.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D10 wire 3

- From: PI.40
- To: AMP.DIN
- Net: I2S_DIN
- From end: U4 pin 40 (GPIO21 I2S DIN). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U8 pin DIN (I2S data). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: green
- Cut: 220 mm, from the netlist. The cut is 70.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D10 wire 4

- From: J5.S
- To: AMP.VIN
- Net: 5V
- From end: J5 pin S (splice). Solder splice, heat shrink. Pin is J5.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: U8 pin VIN (supply). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 220 mm, from the netlist. The cut is 70.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D10 wire 5

- From: JG.S
- To: AMP.GND
- Net: GND
- From end: JG pin S (splice). Solder splice, heat shrink. Pin is JG.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: U8 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 220 mm, from the netlist. The cut is 70.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D10 wire 6

- From: PI.36
- To: AMP.SD
- Net: AMP_SD
- From end: U4 pin 36 (GPIO16 amp SD mode (D48)). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U8 pin SD (shutdown and channel select). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: brown
- Cut: 220 mm, from the netlist. The cut is 70.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D14

Pi header to the left mic board (D47)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D14 wire 1

- From: PI.17
- To: MICL.3V
- Net: 3V3
- From end: U4 pin 17 (3V3). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U10 pin 3V (supply). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 150 mm, from the netlist.

### D14 wire 2

- From: PI.39
- To: MICL.GND
- Net: GND
- From end: U4 pin 39 (GND). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U10 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 150 mm, from the netlist.

### D14 wire 3

- From: PI.12
- To: MICL.BCLK
- Net: I2S_BCLK
- From end: U4 pin 12 (GPIO18 I2S BCLK). No second contact. Solder this wire to the D10 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: U10 pin BCLK (I2S bit clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 150 mm, from the netlist.

### D14 wire 4

- From: PI.35
- To: MICL.LRCL
- Net: I2S_LRC
- From end: U4 pin 35 (GPIO19 I2S LRC). No second contact. Solder this wire to the D10 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: U10 pin LRCL (I2S frame). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 150 mm, from the netlist.

### D14 wire 5

- From: PI.38
- To: MICL.DOUT
- Net: I2S_MIC
- From end: U4 pin 38 (GPIO20 I2S mic data in (D47)). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U10 pin DOUT (I2S data out). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 150 mm, from the netlist.

## Cable D15

left mic board to the right mic board across the head (D47)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D15 wire 1

- From: MICL.3V
- To: MICR.3V
- Net: 3V3
- From end: U10 pin 3V (supply). solder.
- To end: U11 pin 3V (supply). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 240 mm, from the netlist.

### D15 wire 2

- From: MICL.GND
- To: MICR.GND
- Net: GND
- From end: U10 pin GND (ground). solder.
- To end: U11 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 240 mm, from the netlist.

### D15 wire 3

- From: MICL.BCLK
- To: MICR.BCLK
- Net: I2S_BCLK
- From end: U10 pin BCLK (I2S bit clock). solder.
- To end: U11 pin BCLK (I2S bit clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 240 mm, from the netlist.

### D15 wire 4

- From: MICL.LRCL
- To: MICR.LRCL
- Net: I2S_LRC
- From end: U10 pin LRCL (I2S frame). solder.
- To end: U11 pin LRCL (I2S frame). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 240 mm, from the netlist.

### D15 wire 5

- From: MICL.DOUT
- To: MICR.DOUT
- Net: I2S_MIC
- From end: U10 pin DOUT (I2S data out). solder.
- To end: U11 pin DOUT (I2S data out). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 240 mm, from the netlist.

## Cable D16

Pi header to the head touch board (3V3, GND, SDA, SCL; D51)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D16 wire 1

- From: PI.1
- To: TCHH.VIN
- Net: 3V3
- From end: U4 pin 1 (3V3). No second contact. Solder this wire to the D2 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: U12 pin VIN (supply 3 to 5 V (own 3.3 V regulator)). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 140 mm, from the netlist.

### D16 wire 2

- From: PI.25
- To: TCHH.GND
- Net: GND
- From end: U4 pin 25 (GND). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- To end: U12 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 140 mm, from the netlist.

### D16 wire 3

- From: PI.3
- To: TCHH.SDA
- Net: I2C_SDA
- From end: U4 pin 3 (GPIO2 SDA). No second contact. Solder this wire to the D2 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: U12 pin SDA (I2C data). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 140 mm, from the netlist.

### D16 wire 4

- From: PI.5
- To: TCHH.SCL
- Net: I2C_SCL
- From end: U4 pin 5 (GPIO3 SCL). No second contact. Solder this wire to the D2 wire on the same pin (heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited).
- To end: U12 pin SCL (I2C clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 140 mm, from the netlist.

## Cable D17

head touch board E0 and GND to the head-top pad PH1 (D51)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D17 wire 1

- From: TCHH.E0
- To: PH1.E
- Net: TOUCH_PH1
- From end: U12 pin E0 (electrode 0). solder.
- To end: TP1 pin E (electrode). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 90 mm, from the netlist.

### D17 wire 2

- From: TCHH.GND
- To: PH1.G
- Net: GND
- From end: U12 pin GND (ground). solder.
- To end: TP1 pin G (guard ring). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 90 mm, from the netlist.

## Cable D18

head touch board E1 and GND to the back-of-head pad PH2 (D51)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D18 wire 1

- From: TCHH.E1
- To: PH2.E
- Net: TOUCH_PH2
- From end: U12 pin E1 (electrode 1). solder.
- To end: TP2 pin E (electrode). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 90 mm, from the netlist.

### D18 wire 2

- From: TCHH.GND
- To: PH2.G
- Net: GND
- From end: U12 pin GND (ground). solder.
- To end: TP2 pin G (guard ring). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 90 mm, from the netlist.

## Cable D19

BNO055 header to the body touch board (3V3, GND, SDA, SCL, tapping D2; D51)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D19 wire 1

- From: BNO.VIN
- To: TCHB.VIN
- Net: 3V3
- From end: U7 pin VIN (supply). solder.
- To end: U13 pin VIN (supply 3 to 5 V (own 3.3 V regulator)). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 100 mm, from the netlist.

### D19 wire 2

- From: BNO.GND
- To: TCHB.GND
- Net: GND
- From end: U7 pin GND (ground). solder.
- To end: U13 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 100 mm, from the netlist.

### D19 wire 3

- From: BNO.SDA
- To: TCHB.SDA
- Net: I2C_SDA
- From end: U7 pin SDA (I2C data). solder.
- To end: U13 pin SDA (I2C data). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 100 mm, from the netlist.

### D19 wire 4

- From: BNO.SCL
- To: TCHB.SCL
- Net: I2C_SCL
- From end: U7 pin SCL (I2C clock). solder.
- To end: U13 pin SCL (I2C clock). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 100 mm, from the netlist.

## Cable D20

body touch board E0 and GND to the back pad PB1 (D51)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D20 wire 1

- From: TCHB.E0
- To: PB1.E
- Net: TOUCH_PB1
- From end: U13 pin E0 (electrode 0). solder.
- To end: TP3 pin E (electrode). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: white
- Cut: 80 mm, from the netlist.

### D20 wire 2

- From: TCHB.GND
- To: PB1.G
- Net: GND
- From end: U13 pin GND (ground). solder.
- To end: TP3 pin G (guard ring). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 80 mm, from the netlist.

## Cable D21

body touch board to the cliff ToF (3V3, GND, SDA, SCL; D54)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D21 wire 1

- From: TCHB.VIN
- To: TOF.VIN
- Net: 3V3
- From end: U13 pin VIN (supply 3 to 5 V (own 3.3 V regulator)). solder.
- To end: U14 pin VIN (supply 3 to 5 V (own 2.8 V regulator)). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 200 mm, from the netlist.

### D21 wire 2

- From: TCHB.GND
- To: TOF.GND
- Net: GND
- From end: U13 pin GND (ground). solder.
- To end: U14 pin GND (ground). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 200 mm, from the netlist.

### D21 wire 3

- From: TCHB.SDA
- To: TOF.SDA
- Net: I2C_SDA
- From end: U13 pin SDA (I2C data). solder.
- To end: U14 pin SDA (I2C data (10 k pull-up on the board)). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 200 mm, from the netlist.

### D21 wire 4

- From: TCHB.SCL
- To: TOF.SCL
- Net: I2C_SCL
- From end: U13 pin SCL (I2C clock). solder.
- To end: U14 pin SCL (I2C clock (10 k pull-up on the board)). solder.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: yellow
- Cut: 200 mm, from the netlist.

## Cable D22

cliff ToF interrupt to Pi GPIO17, pin 11 (D54), one wire in the D21, D19 and D2 bundles

Joints: neck_pitch, head_pitch, head_yaw, head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D22 wire 1

- From: TOF.GPIO
- To: PI.11
- Net: TOF_INT
- From end: U14 pin GPIO (interrupt out, 2.8 V logic). solder.
- To end: U4 pin 11 (GPIO17 cliff ToF interrupt (D54)). Solder to the header pin (one wire, no 1-circuit locked housing on the chart).
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: green
- Cut: 690 mm, from the netlist.

## Cable D11

MAX98357A to speaker

Joints: none. This cable does not cross a moving joint.

Route polyline 40.0 mm is the netlist figure from cables3d (CAD check only).

### D11 wire 1

- From: AMP.SPK+
- To: SPK.+
- Net: SPK_P
- From end: U8 pin SPK+ (speaker +). screw terminal.
- To end: LS1 pin + (speaker +). solder tab.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: red
- Cut: 120 mm, from the netlist. The cut is 80 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### D11 wire 2

- From: AMP.SPK-
- To: SPK.-
- Net: SPK_N
- From end: U8 pin SPK- (speaker -). screw terminal.
- To end: LS1 pin - (speaker -). solder tab.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: black
- Cut: 120 mm, from the netlist. The cut is 80 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable D12

Pi CSI to Camera Module 3

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### D12 wire 1

- From: PI.CSI
- To: CAM.CSI
- Net: CSI_LINK
- From end: U4 pin CSI (camera connector). The bought cable's own plug (22-pin FPC).
- To end: U9 pin CSI (camera ribbon). The bought cable's own plug (15-pin FPC).
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "FPC ribbon".
- Color: white ribbon
- Cut: 300 mm, from the netlist.

## Cable D13

Pi GPIO26 (pin 37) to the 2813 OFF input (D30; gpio-poweroff)

Joints: neck_pitch, head_pitch, head_yaw, head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 467.7 mm is the netlist figure from cables3d (CAD check only).

### D13 wire 1

- From: PI.37
- To: SW1.OFF
- Net: PWR_OFF
- From end: U4 pin 37 (GPIO26 to the 2813 OFF input (D30)). Solder to the header pin. A 1-circuit friction-ramp housing was not on the series chart (the chart rows opened start at 2 circuits).
- To end: SW1 pin OFF (logic OFF input (D30)). solder in 0.1 in hole.
- Gauge and current: Gauge 26 AWG is the netlist value.
- Color: blue
- Cut: 590 mm, from the netlist. The cut is 122.3 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 0 / 0 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SP1

power pair SPV and SPG to ID 20 BUS 2 (V and G)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### SP1 wire 1

- From: SPV.S
- To: SV20.BUS2.V
- Net: SERVO_7V2
- From end: SPV pin S (splice). WAGO 221-415 port 2, servo plus lever. No separate contact: the lever clamps the bare wire.
- To end: ID20 pin BUS2.V (supply, pin 2). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.64 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.36 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.64 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.36 A (calc only).
- Color: red
- Cut: 160 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.84 / 1.64 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP1 wire 2

- From: SPG.S
- To: JG20.S
- Net: GND
- From end: SPG pin S (splice). WAGO 221-415 port 2, servo ground lever. No separate contact: the lever clamps the bare wire.
- To end: JG20 pin S (splice). Solder splice, heat shrink. Pin is JG20.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.44 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.56 A (calc only).
- Color: black
- Cut: 140 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.85 / 1.44 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP1 wire 3

- From: JG20.S
- To: SV20.BUS2.G
- Branch: tail
- Net: GND
- From end: JG20 pin S (splice). Solder splice, heat shrink. Pin is JG20.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: ID20 pin BUS2.G (ground, pin 1). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.64 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.36 A (calc only).
- Color: black
- Cut: 30 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.84 / 1.64 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SP2

power pair SPV and SPG to ID 10 BUS 2 (V and G)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### SP2 wire 1

- From: SPV.S
- To: SV10.BUS2.V
- Net: SERVO_7V2
- From end: SPV pin S (splice). WAGO 221-415 port 3, servo plus lever. No separate contact: the lever clamps the bare wire.
- To end: ID10 pin BUS2.V (supply, pin 2). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 2.21 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 0.79 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 2.21 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 17.79 A (calc only).
- Color: red
- Cut: 150 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.84 / 2.21 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP2 wire 2

- From: SPG.S
- To: JG10.S
- Net: GND
- From end: SPG pin S (splice). WAGO 221-415 port 3, servo ground lever. No separate contact: the lever clamps the bare wire.
- To end: JG10 pin S (splice). Solder splice, heat shrink. Pin is JG10.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.88 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.12 A (calc only).
- Color: black
- Cut: 130 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.82 / 1.88 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP2 wire 3

- From: JG10.S
- To: SV10.BUS2.G
- Branch: tail
- Net: GND
- From end: JG10 pin S (splice). Solder splice, heat shrink. Pin is JG10.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: ID10 pin BUS2.G (ground, pin 1). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 2.22 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 0.78 A (calc only).
- Color: black
- Cut: 30 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.84 / 2.22 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SP3

power pair SPV and SPG to ID 30 BUS 2 (V and G)

Joints: none. This cable does not cross a moving joint.

Route polyline is empty in the netlist. BLOCKER for a new route measurement. The cut below is the netlist cut, where one is set.

### SP3 wire 1

- From: SPV.S
- To: SV30.BUS2.V
- Net: SERVO_7V2
- From end: SPV pin S (splice). WAGO 221-415 port 4, servo plus lever. No separate contact: the lever clamps the bare wire.
- To end: ID30 pin BUS2.V (supply, pin 2). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.52 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.48 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.52 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.48 A (calc only).
- Color: red
- Cut: 180 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.85 / 1.52 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP3 wire 2

- From: SPG.S
- To: JG30.S
- Net: GND
- From end: SPG pin S (splice). WAGO 221-415 port 4, servo ground lever. No separate contact: the lever clamps the bare wire.
- To end: JG30 pin S (splice). Solder splice, heat shrink. Pin is JG30.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.2 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.8 A (calc only).
- Color: black
- Cut: 160 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.77 / 1.2 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP3 wire 3

- From: JG30.S
- To: SV30.BUS2.G
- Branch: tail
- Net: GND
- From end: JG30 pin S (splice). Solder splice, heat shrink. Pin is JG30.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: ID30 pin BUS2.G (ground, pin 1). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.52 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.48 A (calc only).
- Color: black
- Cut: 30 mm, from the netlist.
- Netlist current, mean / peak / fall: 0.85 / 1.52 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SP4

power pair SPV and SPG to ID 24 BUS 1 (V and G), left leg

Joints: left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 286.5 mm is the netlist figure from cables3d (CAD check only).

### SP4 wire 1

- From: SPV.S
- To: SV24.BUS1.V
- Net: SERVO_7V2
- From end: SPV pin S (splice). WAGO 221-413 port 2, servo plus small lever. No separate contact: the lever clamps the bare wire.
- To end: ID24 pin BUS1.V (supply, pin 2). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.98 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.02 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.98 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.02 A (calc only).
- Color: red
- Cut: 420 mm, from the netlist. The cut is 133.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1.15 / 1.98 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP4 wire 2

- From: SPG.S
- To: SV24.BUS1.G
- Net: GND
- From end: SPG pin S (splice). WAGO 221-413 port 2, servo ground small lever. No separate contact: the lever clamps the bare wire.
- To end: ID24 pin BUS1.G (ground, pin 1). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 1.98 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 1.02 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 1.98 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 18.02 A (calc only).
- Color: black
- Cut: 420 mm, from the netlist. The cut is 133.5 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1.15 / 1.98 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SP5

power pair SPV and SPG to ID 14 BUS 1 (V and G), right leg

Joints: right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 319.3 mm is the netlist figure from cables3d (CAD check only).

### SP5 wire 1

- From: SPV.S
- To: SV14.BUS1.V
- Net: SERVO_7V2
- From end: SPV pin S (splice). WAGO 221-413 port 3, servo plus small lever. No separate contact: the lever clamps the bare wire.
- To end: ID14 pin BUS1.V (supply, pin 2). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 2.11 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 0.89 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 2.11 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 17.89 A (calc only).
- Color: red
- Cut: 450 mm, from the netlist. The cut is 130.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1.18 / 2.11 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

### SP5 wire 2

- From: SPG.S
- To: SV14.BUS1.G
- Net: GND
- From end: SPG pin S (splice). WAGO 221-413 port 3, servo ground small lever. No separate contact: the lever clamps the bare wire.
- To end: ID14 pin BUS1.G (ground, pin 1). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. Peak 2.11 A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, read 2026-11-02). Margin 0.89 A (calc only). Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415). Highest netlist current on this wire 2.11 A vs UL 20 A (cited, WAGO 221-413 sheet, use group). Margin 17.89 A (calc only).
- Color: black
- Cut: 450 mm, from the netlist. The cut is 130.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.
- Netlist current, mean / peak / fall: 1.18 / 2.11 / None A. The source on the wire says where that current came from (sim pass only unless that source says otherwise).

## Cable SD1

adapter H3 data lead: DATA and GND only (V position empty), data Y at YD3 to ID 20 and ID 30, GND Y at YG3 into the SP1 and SP3 grounds

Joints: none. This cable does not cross a moving joint.

Route polyline 87.3 mm is the netlist figure from cables3d (CAD check only).

### SD1 wire 1

- From: U2.H3.D
- To: YD3.S
- Branch: stem
- Net: BUS_DATA
- From end: U2 pin H3.D (bus data (H3 pin 1)). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- To end: YD3 pin S (splice). Solder splice, heat shrink. Pin is YD3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: yellow
- Cut: 30 mm, from the netlist.

### SD1 wire 2

- From: U2.H3.G
- To: YG3.S
- Branch: stem
- Net: GND
- From end: U2 pin H3.G (ground (H3 pin 3)). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- To end: YG3 pin S (splice). Solder splice, heat shrink. Pin is YG3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: black
- Cut: 45 mm, from the netlist.

### SD1 wire 3

- From: YD3.S
- To: SV20.BUS2.D
- Branch: a
- Net: BUS_DATA
- From end: YD3 pin S (splice). Solder splice, heat shrink. Pin is YD3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: ID20 pin BUS2.D (data, pin 3). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: yellow
- Cut: 130 mm, from the netlist. The cut is 42.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### SD1 wire 4

- From: YG3.S
- To: JG20.S
- Branch: a
- Net: GND
- From end: YG3 pin S (splice). Solder splice, heat shrink. Pin is YG3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: JG20 pin S (splice). Solder splice, heat shrink. Pin is JG20.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value.
- Color: black
- Cut: 120 mm, from the netlist. The cut is 32.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### SD1 wire 5

- From: YD3.S
- To: SV30.BUS2.D
- Branch: b
- Net: BUS_DATA
- From end: YD3 pin S (splice). Solder splice, heat shrink. Pin is YD3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: ID30 pin BUS2.D (data, pin 3). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: yellow
- Cut: 170 mm, from the netlist. The cut is 82.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### SD1 wire 6

- From: YG3.S
- To: JG30.S
- Branch: b
- Net: GND
- From end: YG3 pin S (splice). Solder splice, heat shrink. Pin is YG3.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- To end: JG30 pin S (splice). Solder splice, heat shrink. Pin is JG30.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value.
- Color: black
- Cut: 140 mm, from the netlist. The cut is 52.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable SD2

adapter H5 data lead: DATA and GND only, to ID 10 (DATA) and JG10 (GND)

Joints: none. This cable does not cross a moving joint.

Route polyline 63.8 mm is the netlist figure from cables3d (CAD check only).

### SD2 wire 1

- From: U2.H5.D
- To: SV10.BUS2.D
- Net: BUS_DATA
- From end: U2 pin H5.D (bus data (H5 pin 1)). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- To end: ID10 pin BUS2.D (data, pin 3). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: yellow
- Cut: 150 mm, from the netlist. The cut is 86.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### SD2 wire 2

- From: U2.H5.G
- To: JG10.S
- Net: GND
- From end: U2 pin H5.G (ground (H5 pin 3)). Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
- To end: JG10 pin S (splice). Solder splice, heat shrink. Pin is JG10.S. Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already used by the ground, switched-plus, and servo levers.
- Gauge and current: Gauge 22 AWG is the netlist value. No peak in the netlist for this data wire. The 22 AWG contact is the one already used on the power leads (3.0 A cited).
- Color: black
- Cut: 140 mm, from the netlist. The cut is 76.2 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S2

kit cable ID 20 BUS 1 to ID 21 BUS 2

Joints: left_hip_yaw.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 56.6 mm is the netlist figure from cables3d (CAD check only).

### S2 wire 1

- From: SV20.BUS1.D
- To: SV21.BUS2.D
- Net: BUS_DATA
- From end: ID20 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID21 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S2 wire 2

- From: SV20.BUS1.V
- To: SV21.BUS2.V
- Net: SERVO_7V2
- From end: ID20 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID21 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S2 wire 3

- From: SV20.BUS1.G
- To: SV21.BUS2.G
- Net: GND
- From end: ID20 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID21 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S3

kit cable ID 21 to ID 22

Joints: left_hip_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 82.3 mm is the netlist figure from cables3d (CAD check only).

### S3 wire 1

- From: SV21.BUS1.D
- To: SV22.BUS2.D
- Net: BUS_DATA
- From end: ID21 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID22 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S3 wire 2

- From: SV21.BUS1.V
- To: SV22.BUS2.V
- Net: SERVO_7V2
- From end: ID21 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID22 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S3 wire 3

- From: SV21.BUS1.G
- To: SV22.BUS2.G
- Net: GND
- From end: ID21 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID22 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S4

kit cable ID 22 to ID 23

Joints: left_hip_pitch.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 92.1 mm is the netlist figure from cables3d (CAD check only).

### S4 wire 1

- From: SV22.BUS1.D
- To: SV23.BUS2.D
- Net: BUS_DATA
- From end: ID22 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID23 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S4 wire 2

- From: SV22.BUS1.V
- To: SV23.BUS2.V
- Net: SERVO_7V2
- From end: ID22 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID23 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S4 wire 3

- From: SV22.BUS1.G
- To: SV23.BUS2.G
- Net: GND
- From end: ID22 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID23 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S5

kit cable ID 23 BUS 1 to ID 24 BUS 2

Joints: left_knee.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 92.1 mm is the netlist figure from cables3d (CAD check only).

### S5 wire 1

- From: SV23.BUS1.D
- To: SV24.BUS2.D
- Net: BUS_DATA
- From end: ID23 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID24 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S5 wire 2

- From: SV23.BUS1.V
- To: SV24.BUS2.V
- Net: SERVO_7V2
- From end: ID23 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID24 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S5 wire 3

- From: SV23.BUS1.G
- To: SV24.BUS2.G
- Net: GND
- From end: ID23 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID24 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S7

kit cable ID 10 to ID 11

Joints: right_hip_yaw.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 56.6 mm is the netlist figure from cables3d (CAD check only).

### S7 wire 1

- From: SV10.BUS1.D
- To: SV11.BUS2.D
- Net: BUS_DATA
- From end: ID10 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID11 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S7 wire 2

- From: SV10.BUS1.V
- To: SV11.BUS2.V
- Net: SERVO_7V2
- From end: ID10 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID11 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S7 wire 3

- From: SV10.BUS1.G
- To: SV11.BUS2.G
- Net: GND
- From end: ID10 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID11 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 93.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S8

kit cable ID 11 to ID 12

Joints: right_hip_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 82.3 mm is the netlist figure from cables3d (CAD check only).

### S8 wire 1

- From: SV11.BUS1.D
- To: SV12.BUS2.D
- Net: BUS_DATA
- From end: ID11 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID12 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S8 wire 2

- From: SV11.BUS1.V
- To: SV12.BUS2.V
- Net: SERVO_7V2
- From end: ID11 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID12 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S8 wire 3

- From: SV11.BUS1.G
- To: SV12.BUS2.G
- Net: GND
- From end: ID11 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID12 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 67.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S9

kit cable ID 12 to ID 13

Joints: right_hip_pitch.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 91.6 mm is the netlist figure from cables3d (CAD check only).

### S9 wire 1

- From: SV12.BUS1.D
- To: SV13.BUS2.D
- Net: BUS_DATA
- From end: ID12 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID13 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 58.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S9 wire 2

- From: SV12.BUS1.V
- To: SV13.BUS2.V
- Net: SERVO_7V2
- From end: ID12 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID13 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 58.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S9 wire 3

- From: SV12.BUS1.G
- To: SV13.BUS2.G
- Net: GND
- From end: ID12 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID13 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 58.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S10

kit cable ID 13 to ID 14

Joints: right_knee.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 92.1 mm is the netlist figure from cables3d (CAD check only).

### S10 wire 1

- From: SV13.BUS1.D
- To: SV14.BUS2.D
- Net: BUS_DATA
- From end: ID13 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID14 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S10 wire 2

- From: SV13.BUS1.V
- To: SV14.BUS2.V
- Net: SERVO_7V2
- From end: ID13 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID14 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S10 wire 3

- From: SV13.BUS1.G
- To: SV14.BUS2.G
- Net: GND
- From end: ID13 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID14 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 57.9 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S11

kit cable ID 30 BUS 1 to ID 31 BUS 2

Joints: neck_pitch.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 80.0 mm is the netlist figure from cables3d (CAD check only).

### S11 wire 1

- From: SV30.BUS1.D
- To: SV31.BUS2.D
- Net: BUS_DATA
- From end: ID30 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID31 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 70 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S11 wire 2

- From: SV30.BUS1.V
- To: SV31.BUS2.V
- Net: SERVO_7V2
- From end: ID30 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID31 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 70 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S11 wire 3

- From: SV30.BUS1.G
- To: SV31.BUS2.G
- Net: GND
- From end: ID30 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID31 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 70 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S12

kit cable ID 31 to ID 32

Joints: head_pitch, head_yaw.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 106.3 mm is the netlist figure from cables3d (CAD check only).

### S12 wire 1

- From: SV31.BUS1.D
- To: SV32.BUS2.D
- Net: BUS_DATA
- From end: ID31 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID32 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 43.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S12 wire 2

- From: SV31.BUS1.V
- To: SV32.BUS2.V
- Net: SERVO_7V2
- From end: ID31 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID32 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 43.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S12 wire 3

- From: SV31.BUS1.G
- To: SV32.BUS2.G
- Net: GND
- From end: ID31 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID32 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 43.7 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable S13

kit cable ID 32 to ID 33

Joints: head_roll.

Flex: the netlist already sets the twist lay where a lay fits (NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). A flex-cycle number for this silicone was not published. BLOCKER for a cycle life. Same gap already recorded for the knee loop.

Route polyline 51.6 mm is the netlist figure from cables3d (CAD check only).

### S13 wire 1

- From: SV32.BUS1.D
- To: SV33.BUS2.D
- Net: BUS_DATA
- From end: ID32 pin BUS1.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID33 pin BUS2.D (data, pin 3). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 98.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S13 wire 2

- From: SV32.BUS1.V
- To: SV33.BUS2.V
- Net: SERVO_7V2
- From end: ID32 pin BUS1.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID33 pin BUS2.V (supply, pin 2). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 98.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

### S13 wire 3

- From: SV32.BUS1.G
- To: SV33.BUS2.G
- Net: GND
- From end: ID32 pin BUS1.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- To end: ID33 pin BUS2.G (ground, pin 1). Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.
- Gauge and current: BLOCKER for a gauge number: the netlist leaves this as "kit cable".
- Color: kit
- Cut: 150 mm, from the netlist. The cut is 98.4 mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop.

## Cable CB, off the charger board

Source: `circuitry/charger_board.yaml` component JPI, and CHARGER_BOARD.md. These four conductors are not in `wiring/netlist.yaml`. The yaml marks the off-board rows cut_mm 0 and says that is not a cut length. Do not read 0 as a finished length.

Joints: the same four neck joints as cable D13 (neck_pitch, head_pitch, head_yaw, head_roll), because one end is in the battery bay and the other is on the Pi, which is the D13 path. This is the existing joint list, not a new route. Cut length: BLOCKER. Flex cycle life: BLOCKER, same as every other neck wire.

### CB wire 1, STAT

- From: charger JPI.STAT (the pad after the 1 kOhm, yaml pin JPI.STAT)
- To: Pi header pin 29 (GPIO5)
- From end: solder to pad JPI.STAT. The board yaml gives a pad, not a plug.
- To end: KK 254 housing 0022012027 position 1, contact 08-50-0114.
- Gauge: 26 AWG, the gauge already on that yaml row. Peak on that row is 0 A. The 2.5 A brass rating (cited) is far above a logic pull-up. Insulation fit is the same BLOCKER as the other 26 AWG KK crimps.
- Color: blue, the color on that yaml row.
- Cut: BLOCKER.

### CB wire 2, enable

- From: charger JPI.EN
- To: Pi header pin 31 (GPIO6)
- From end: solder to pad JPI.EN.
- To end: KK 254 housing 0022012027 position 2, contact 08-50-0114.
- Gauge: 26 AWG, from that yaml row. Same 2.5 A note and the same insulation BLOCKER.
- Color: green, the color on that yaml row.
- Cut: BLOCKER.

### CB wire 3, 3.3 V

- From: charger JPI.V3
- To: the D2 red wire (Pi pin 1, 3.3 V), spliced. Not a second contact on pin 1.
- From end: solder to pad JPI.V3. The yaml names the pin. It does not give this conductor its own AWG row.
- To end: solder splice to cable D2 red, heat shrink. Pin 1 already has the D2 contact.
- Gauge: 26 AWG, the same gauge as the STAT and EN rows of this cable. Not a separate published row. Current is the pull-up already calculated in CHARGER_BOARD.md (0.33 mA on the 10 kOhm STAT pull-up, calc only there).
- Color: orange, the color the yaml uses on the 3.3 V net.
- Cut: BLOCKER.

### CB wire 4, ground

- From: charger JPI.GND (the pin is on the yaml component)
- To: the D2 black wire (Pi pin 9), spliced. Not a second contact on pin 9.
- From end: solder to pad JPI.GND.
- To end: solder splice to cable D2 black.
- Gauge: 26 AWG, the gauge on the yaml row JPI.GND to JIN.M. That row is the board ground. The neck piece is the same net and the same gauge.
- Color: black.
- Cut: BLOCKER.

## Flush wells

Source: `twin/dock/flush/FLUSH_CONTACTS.md`. Five gold wells in the seat. No new wire crosses a joint (that file, line 3 of the belly column). The diode part is not chosen in that file. This harness does not pick one and does not draw a circuit.

Each well is one conductor. Near end: solder to that well. Far end: BLOCKER, no connector and no pin, because the board it would land on was not chosen. Do not connect these wires. Positions of the five wells are the ones in that file (y = -24, -12, 0, +12, +24 mm in the seat patch). Length: BLOCKER. That file says the nest lead lengths were not copied.

## What has no pin, and what was done

- BLOCKER: CHG.B+ label is not checked on the part ([U] CABLE_MAP; label [I]).
- BLOCKER: CHG.B- label is not checked on the part ([U] CABLE_MAP; label [I]).
- FIX: P14 at G.S was a solder splice with no part number. It is now WAGO 221-415 port 1, ground lever.
- FIX: P9 at VSW.S was a solder splice with no part number. It is now WAGO 221-413 port 1, switched plus lever.
- FIX: P16 at G.S was a solder splice with no part number. It is now WAGO 221-415 port 4, ground lever.
- BLOCKER: CTL.1 label is not checked on the part ([I]).
- BLOCKER: CTL.2 label is not checked on the part ([I]).
- FIX: P10 at VSW.S was a solder splice with no part number. It is now WAGO 221-413 port 2, switched plus lever.
- FIX: P10 at G.S was a solder splice with no part number. It is now WAGO 221-415 port 2, ground lever.
- FIX: P11 at SPV.S was a solder splice with no part number. It is now WAGO 221-415 port 1, servo plus lever.
- FIX: P11 at SPG.S was a solder splice with no part number. It is now WAGO 221-415 port 1, servo ground lever.
- FIX: P13 at VSW.S was a solder splice with no part number. It is now WAGO 221-413 port 3, switched plus lever.
- FIX: P13 at G.S was a solder splice with no part number. It is now WAGO 221-415 port 3, ground lever.
- FIX: P12 PI.2 is 20 AWG. Molex 08-50-0114 takes 22 to 30 AWG only (cited). Solder it to the header pin, as docs/assembly_guide.md does.
- FIX: P12 PI.6 is 20 AWG. Molex 08-50-0114 takes 22 to 30 AWG only (cited). Solder it to the header pin, as docs/assembly_guide.md does.
- FIX: P17 PI.4 is 20 AWG. Molex 08-50-0114 takes 22 to 30 AWG only (cited). Solder it to the header pin, as docs/assembly_guide.md does.
- BLOCKER: PI.14 label is not checked on the part ([I] pin 6 holds the U3 ground).
- FIX: P17 PI.14 is 20 AWG. Molex 08-50-0114 takes 22 to 30 AWG only (cited). Solder it to the header pin, as docs/assembly_guide.md does.
- BLOCKER: JG.S label is not checked on the part ([I]).
- FIX: D2 and D3 both landed on PI.9. One 08-50-0114 takes one wire. D2 keeps the contact. D3 is spliced to it.
- FIX: D2 and D4 both landed on PI.9. One 08-50-0114 takes one wire. D2 keeps the contact. D4 is spliced to it.
- BLOCKER: PI.20 label is not checked on the part ([I] LED returns).
- FIX: D5 and D6 both landed on PI.20. One 08-50-0114 takes one wire. D5 keeps the contact. D6 is spliced to it.
- FIX: D5 and D7 both landed on PI.20. One 08-50-0114 takes one wire. D5 keeps the contact. D7 is spliced to it.
- FIX: D10 and D14 both landed on PI.12. One 08-50-0114 takes one wire. D10 keeps the contact. D14 is spliced to it.
- FIX: D10 and D14 both landed on PI.35. One 08-50-0114 takes one wire. D10 keeps the contact. D14 is spliced to it.
- FIX: D2 and D16 both landed on PI.1. One 08-50-0114 takes one wire. D2 keeps the contact. D16 is spliced to it.
- FIX: D2 and D16 both landed on PI.3. One 08-50-0114 takes one wire. D2 keeps the contact. D16 is spliced to it.
- FIX: D2 and D16 both landed on PI.5. One 08-50-0114 takes one wire. D2 keeps the contact. D16 is spliced to it.
- FIX: D13 PI.37 was a KK socket, but a 1-circuit friction-ramp part was not on the Molex 2695 chart opened this pass. Solder to the header pin.
- FIX: SP1 at SPV.S was a solder splice with no part number. It is now WAGO 221-415 port 2, servo plus lever.
- FIX: SP1 at SPG.S was a solder splice with no part number. It is now WAGO 221-415 port 2, servo ground lever.
- FIX: SP2 at SPV.S was a solder splice with no part number. It is now WAGO 221-415 port 3, servo plus lever.
- FIX: SP2 at SPG.S was a solder splice with no part number. It is now WAGO 221-415 port 3, servo ground lever.
- FIX: SP3 at SPV.S was a solder splice with no part number. It is now WAGO 221-415 port 4, servo plus lever.
- FIX: SP3 at SPG.S was a solder splice with no part number. It is now WAGO 221-415 port 4, servo ground lever.
- FIX: SP4 at SPV.S was a solder splice with no part number. It is now WAGO 221-413 port 2, servo plus small lever.
- FIX: SP4 at SPG.S was a solder splice with no part number. It is now WAGO 221-413 port 2, servo ground small lever.
- FIX: SP5 at SPV.S was a solder splice with no part number. It is now WAGO 221-413 port 3, servo plus small lever.
- FIX: SP5 at SPG.S was a solder splice with no part number. It is now WAGO 221-413 port 3, servo ground small lever.
- BLOCKER: YD3.S label is not checked on the part ([L] D15; position next to the adapter [I]).
- BLOCKER: YG3.S label is not checked on the part ([L] D15 (H3 GND spliced into SP1 and SP3); position [I]).
- FIX: Charger STAT and EN had solder pads and cut length 0. Pi end is now KK 254 housing 0022012027 on pins 29 and 31. 3.3 V and ground splice to cable D2. Cut length stays BLOCKER.
- BLOCKER: Five flush-well wires have a near end (solder to the well) and no far pin or connector.

Counted here: 34 FIX lines, 10 BLOCKER lines, after dropping repeated wording (calc only, a count of this list).

Wires read from the netlist: 171 (calc only, a count of active rows).

