# PARTS AUDIT

Written 2026-11-11 ET. Research only. Nothing was bought. This file does not change BOM.md.
No prices are written here. A number from a document opened this session is labeled with that document.
A number from a sim, a calc, or a CAD check keeps that label. Anything not opened is UNVERIFIED/BLOCKER.

This is the parts half of gate 0 and all of gate 1 in DEFINITION_OF_DONE.md. Neither gate passes because of this file.

A later section, "Session 2026-11-11 ET", reopened stock and filled part numbers. Where this first write and that section disagree, use the later section.

## What "orderable today" means here

A part is orderable today only when all four are true: an exact manufacturer part number, a named distributor, a quantity, and a page opened this session that shows it can be bought.
STOCK NOT REOPENED means the bill of materials already names a part number, a distributor, and a quantity, and this session did not open a live stock page. That is not orderable today.
NOT TODAY means a page was opened and the part could not be bought there.
NOT ORDERABLE means the part number or the seller is missing.
DO NOT ORDER means the line is superseded or the quantity is zero, and a one-click of the current bill would be wrong if it included it.

## One-click order: not ready

A single order placed from today's BOM.md would both miss the nest and buy parts the nest no longer uses. What is missing:

1. The spring pin has no complete part number. The catalog family is real (below). The tip code is not chosen, so the probe cannot be ordered. The socket number 100-SDN250S is printed on the catalog page. No distributor stock page for it was opened.
2. Felt, the gold conductive cloth, the pale gold cloth, the foil under the sun, the rim foam, and the gate board have no part numbers. The foil was guessed as a 3M 1181 class tape. That guess was not checked against a 3M sheet.
3. The in-duck charger is not a seated, wired part. The dock list names Microchip MCP73213EV-2SOVP. The chip datasheet was not opened (dropout, the 6 hour timer, and the missing thermistor stay BLOCKER). The eval board is not a designed spot inside the duck.
4. Line 7, the spot-welded pack, has no strip, sleeve, or weld source. Line 17m, the two M2x12 screws for the neck stop, has no listing. Line 22c, the eleven Pi-header housings, has no completed part numbers.
5. Line 11 (the USB-C charge board), line 14 (the antenna servos), line E3 (the LED beads), line E4 (the eye discs), and line E5 (the reflector) have no manufacturer part number and no datasheet.
6. Line DK1 is the old four-strip chest pad. D61 removes it. A one-click of the current bill still buys it. Line DK5 serves the old SENSE wire, which D61 also removes.
7. Raspberry Pi Zero 2 W at Adafruit 5291, and the header version 6008, were out of stock on the page opened this session. Molicel P45B at 18650 Battery Store was out of stock on the page opened this session. Other sellers were not rechecked.
8. The nest CAD is not in the bill, the netlist, or print/parts.csv. Print files for the nest are not on the order. The old wall-dock parts list (twin/dock/DOCK_BOM_FULL.md) is still a separate list and is not the nest.
9. Almost every other line is STOCK NOT REOPENED. A one-click order needs a live cart, not a sourcing note from an earlier day.

## Documents opened this session

- QA Technology 100-40 catalog, TestEquity copy: https://assets.testequity.com/te1/Documents/pdf/qa-technology/QA-Technology_100-40_Catalog_1123.pdf
- Feetech STS3215 product specification A/1: https://files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf
- Molicel INR21700-P45B product data sheet version 1.2: https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf
- Raspberry Pi Zero 2 W product brief (October 2021): https://cdn.sparkfun.com/assets/f/8/d/a/c/Raspberry_Pi_Zero_2_W_Product_Brief.pdf
- Raspberry Pi Camera Module 3 product brief (June 2024): https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf
- Adafruit 5291 stock page, opened, out of stock (both header options).
- 18650 Battery Store P45B page, opened, out of stock.
- The MCP73213 datasheet was not opened. A Microchip file that search returned was a long catalog, and the pages read were not the charger sheet. Dropout stays BLOCKER.

## Nest parts (not on BOM.md)

| Part | Exact part number | Qty | Distributor | Datasheet | Status | Orderable today |
|---|---|---|---|---|---|---|
| Spring probe | Not complete. Family 100-PR, tube letter, tip code, spring letter. Standard spring letter is S. A round tip on the catalog page is 40 (0.91 mm) or 30 (1.40 mm). | 4 | none opened | catalog URL above | MISMATCH | NOT ORDERABLE |
| Socket | 100-SDN250S (nickel silver, solder cup), shown on the same catalog page | 4 | none opened | same catalog | VERIFIED as a catalog number; the press-fit hole is written for FR4, not printed PLA | STOCK NOT REOPENED, and the PLA press fit is UNVERIFIED/BLOCKER |
| Conductive cloth, gold and pale gold | none | sun disc and ring, cut sizes in the nest CAD | none | none for the gold color. A grey Laird cloth was cited in the nest study and was not opened here | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| Felt, about 2 mm | none | one mat | none | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| Foil under the sun | guessed 3M 1181 class, not confirmed | one disc | none | not opened | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| Charger moved into the duck | MCP73213EV-2SOVP is the dock list's board. Chip option named there as MCP73213-A6S/MF | 1 | DigiKey, stock not reopened | datasheet not opened | UNVERIFIED/BLOCKER | NOT ORDERABLE as an in-duck design |
| Gate board in the rim | none, not designed | 1 | none | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |

Catalog numbers that do match the nest note (QA Technology 100-40 catalog, opened): full stroke 10.16 mm; standard spring 0.42 N at first touch and 1.58 N at 8.05 mm; 500,000 cycles at that stroke for the standard spring; tube diameter 1.367 mm; tube P average current 10.2 A at 120 C, with a footnote that the spring changes the current rating (that note was not opened). Suggested mounting hole 1.702 to 1.753 mm, drill 1.75 mm, in FR4 or the same class of board, not in PLA. The drawn 2.3 mm round head is not on the page. The largest plain round tip on the page is 1.40 mm.

## Radios, camera, and connectors

There is no separate radio module. The radio is the Pi Zero 2 W (2.4 GHz Wi-Fi, Bluetooth 4.2, BLE, onboard antenna, product brief above). The Xbox controller has its own radio and stays outside the duck. The camera is Camera Module 3, and the brief marks that camera FCC Part 15 Subpart B Class B. Connectors the duck actually uses, and whether a manufacturer drawing was opened:

- Molex Mini-SPOX housing 50-37-5033 and terminal 08-70-1040 (lines 21 and 22): drawing not opened. UNVERIFIED/BLOCKER. STOCK NOT REOPENED. Newark.
- Molex KK 254 terminal 08-50-0114 (line 22b): drawing not opened. UNVERIFIED/BLOCKER. STOCK NOT REOPENED.
- Housings for those KK terminals (line 22c): NOT ORDERABLE, above.
- Amass XT30U (line 12): drawing not opened. UNVERIFIED/BLOCKER.
- Camera cable (line E7): above.
- The servo's own 5264 plug is confirmed on the Feetech sheet as the connector type. The mate is the Molex housing above, and that Molex drawing was not opened.

## Twin numbers that are still guesses

These are inputs the sims and the CAD use that are not a value from a datasheet opened for that material or that part. A sim that uses them is sim pass only. It is not a measurement.

- Pin contact resistance on cloth: not measured, and no cloth datasheet for the gold cloth was opened. The nest note's about 0.10 ohm ring path is calc only, and it leaves contact resistance out.
- Felt friction, cloth friction, and how far a 1 N tip sinks into felt: the sim mat is rigid. Real felt is not in the model (D61).
- Pin tip diameter 2.3 mm and several pin lengths in the nest CAD: estimates. The catalog, now opened, does not show a 2.3 mm round tip. Stroke and standard-spring force on that catalog do match the CAD's force line.
- Servo stall in the twin is stronger than the Feetech sheet opened here (19.5 kg.cm at 7.4 V). Servo operating temperature on that sheet is -20 C to 60 C. The thermal twin's 70 C cut is not on that sheet. Rotor inertia has not been measured.
- STS3250 knee torque, damping, and heat: no datasheet opened.
- Cell picture in the viewer is a 21.4 x 70 mm cylinder (nominal, twin/battery/BAY.md). The opened P45B sheet gives 21.55 mm and 70.15 mm as maximums, which is the top of the 21.40 plus or minus 0.15 mm by 70.00 plus or minus 0.15 mm band the bay already used. The sleeved pack is 22.2 x 43.7 x 71.0 mm (CAD check only, twin/battery/bay_edit.py). No bay resize. Weld resistance of the pack is unknown (line 7). Some older twin runs still use a P30B pack model.
- Charger dropout and the 1.9 to 3.2 W of heat in the trunk: calc only. The thermal twin was not re-run with the charger inside the duck. The MCP73213 sheet was not opened.
- Camera: the nest sim uses true pose plus noise. It is not a camera model, not a lens, and not room light. The camera brief gives the sensor and the 0 C to 50 C range. It does not give a model of finding a mat.
- Mat edge in the sim is one 2 mm rise. The CAD edge is two 1 mm steps. Those steps have not been simulated.

## Proposed bill changes (not applied)

- Do not order DK1 for the nest. Do not order DK5 until the two-wire gate has a real parts list.
- Add the probe only after the tip code is chosen from the catalog (a round tip, 30 or 40, standard spring S, a tube whose current note is read). Add four 100-SDN250S sockets. Do not press them into PLA until a coupon holds the catalog hole.
- Do not resize the cell bay for the opened sheet. Its maximum (21.55 mm by 70.15 mm) already fits the sleeved pack of 22.2 x 43.7 x 71.0 mm (twin/battery/bay_edit.py, CAD check only). The open battery item is line 7, the unsourced weld.
- Give line 7, line 17m, and line 22c real part numbers or drop them from the order with a named substitute.
- Point the nest charger at a read MCP73213 datasheet and a seated board, or keep the charger out of the duck. Line 11 is not that charger.
- Record a Raspberry Pi order code for line 3, and a second distributor, because Adafruit 5291 was out of stock.
- Record a second seller for the P45B, because 18650 Battery Store was out of stock. The P50B alternate was not rechecked.

## Every line on BOM.md

Test-order rows (TO) and the extra-buy notes (X) are the same parts as the lines below. They are not a second set. Printed parts in print/parts.csv are PLA or TPU from lines 27 and 28. They have no manufacturer part number of their own. The nest prints are not in that file.

Lines with a longer note are in the rows above and repeated here in short form so the list is complete.

| Line | What | Exact part number | Qty | Distributor | Datasheet | Status | Orderable today |
|---|---|---|---|---|---|---|---|
| 1 | Smart serial bus servo | STS3215 (C001 is the lab name; the opened sheet titles the model STS3215) | 12 | Seeed Studio | https://files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf | MISMATCH | STOCK NOT REOPENED |
| 1b | Smart serial bus servo, knees (D32) | STS3250-C002, as named in BOM.md | 2 | OpenELAB | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 2 | Servo bus adapter | Waveshare SKU 25514 | 1 | Waveshare | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 3 | Compute | Raspberry Pi Zero 2 W, Adafruit 5291 (distributor id, not a Raspberry Pi order code) | 1 | Adafruit 5291 | https://cdn.sparkfun.com/assets/f/8/d/a/c/Raspberry_Pi_Zero_2_W_Product_Brief.pdf | VERIFIED | NOT TODAY |
| 4 | microSD | SanDisk SDSQUAR-032G-GN6MA | 1 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 5 | IMU | Adafruit 2472, Bosch BNO055 | 1 | Adafruit 2472 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 5b | Cliff sensor (D54) | Adafruit 5396, ST VL53L4CD | 1 | Adafruit | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 6 | Li-ion cell | Molicel INR21700-P45B | 2 | 18650 Battery Store | https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf | VERIFIED | NOT TODAY |
| 7 | 2S pack build (D44) | none | 1 | not chosen | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| 8 | 2S BMS | Tenergy 32175 | 1 | Tenergy (Fremont, CA) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 9 | 5 V regulator | Pololu 4892, D30V30F5 | 1 | Pololu (Las Vegas, NV) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 10 | Main power switch (D30) | Pololu 2813 | 1 | Pololu (Las Vegas, NV) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 10r | Main power switch: replaced (D30) | Pololu 2815 | 0 | Pololu (Las Vegas, NV) | not opened | UNVERIFIED/BLOCKER | DO NOT ORDER |
| 10b | Control button (D30, D38) | NKK MB2011LS1W01-BB | 1 | Newark (941 in stock, search index) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 11 | USB-C 2S charger | none (Adeept board, Amazon listing) | 1 | Amazon (Adeept) | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| 12 | XT30 pair | Amass XT30U, as named; the Amazon pack is not a single Amass document | 2 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 13 | Foot contact switch | Omron SS-01 preferred, SS-10 fallback | 4 | DigiKey | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 13b | Foot switch pull-up | 2.2 kilohm, 5 percent, 1/4 W (Adafruit 2782) | 2 | Adafruit 2782 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 14 | Antenna servo | none (SG90-class, Miuzei 10-pack) | 2 | Amazon (Miuzei) | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| 15 | Game controller | Microsoft Xbox Wireless Controller | 1 | Microsoft Store (also Walmart, Best Buy) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| L1 | Servo buck regulator | Castle 010-0004-01 | 1 | Castle Creations; also Horizon Hobby CSE010000401 and Motion RC | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| L3 | Inline fuse holder | Littelfuse FHAC0001ZXJ | 1 | Newark 56P4171 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| L4 | Fuse | Littelfuse 0287015.PXCN | 1 | DigiKey | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| DK1 | Chest contact pad (dock, D43, D50) | custom OSH Park board, no manufacturer part | 1 | OSH Park (Portland, OR) | none | UNVERIFIED/BLOCKER | DO NOT ORDER |
| DK2 | Charge input ideal diode (dock, V1 track 8) | Pololu 5382 | 1 | Pololu | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| DK3 | Charge path fuse holder (dock, V1 track 8) | Littelfuse FHAC0001ZXJ (same as L3) | 1 | Newark 56P4171 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| DK4 | Charge path fuse (dock, V1 track 8) | Littelfuse 0287005.PXCN | 1 | DigiKey | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| DK5 | Cell NTC and wake branch parts (dock, V1 track 8) | Adafruit 372 NTC plus onsemi 1N5228B and a 1N4148 | 1 set | Adafruit, DigiKey | not opened | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| DK6 | Dock supply ideal diode (D50, V1 track 8) | Pololu 5382 | 1 | Pololu | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| DK7 | Pack side ideal diode (D50, V1 track 8) | Pololu 5383 | 1 | Pololu | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 16 | M3 heat-set insert | CNC Kitchen M3 x 5.7, D1 4.6 mm | 48 | CNC Kitchen USA | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17a | M3x8 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 18 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17b | M3x10 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 12 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17c | M3x12 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 2 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17d | M3x6 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 78 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17e | M3x5 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 28 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17f | M2.5x6 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 13 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17g | M2.5x8 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 4 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17i | M2.5x10 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 4 | Bolt Depot | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17h | M2 self-tapping kit | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 32 | Amazon (ships from Amazon) | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17j | M3x6 button head | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 10 | BelMetric (US: "Stocked in the USA", since 1976, +1-978-649-6201) | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17k | M2.5x5 SHCS | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 2 | BelMetric (US) | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17l | M2.5 flat washer, small series | standard screw or washer size named on the bill (DIN 912, ISO 7380, or the kit) | 8 | BelMetric (US) | standard text not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 17m | M2x12 self-tapping pan head | none | 2 | BLOCKER | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| 18 | Ball bearing | 6804ZZ (Motoforti pack or VXB) | 3 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 19 | Threadlocker | Loctite 243, P/N 1330799 | 1 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 29 | Foam mounting tape | as named on the bill | 1.2 m | Zoro (3M) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 20 | USB data cable | as named on the bill | 1 | Adafruit | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 21 | Mini-SPOX housing | as named on the bill | 7 | Newark 57H1785 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 22 | Mini-SPOX crimp terminal | as named on the bill | 17 | Newark 54H5573 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 22b | KK 254 crimp terminal (X1, D36) | as named on the bill | 27 | Octopart (lowest listed) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 22c | KK 254 crimp housings (X1, D36) | Molex KK 254 2695-series housings; 22-01-3027 was looked for and not found | 11 | BLOCKER | not opened | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| L5 | Power wire 16 AWG | as named on the bill | 1.3 m | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 23 | Wire 20 AWG | as named on the bill | 2.8 m | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 24 | Wire 22 AWG | as named on the bill | 3.6 m | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 25 | Wire 26 AWG | as named on the bill | 12.7 m | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 26 | Heat shrink | as named on the bill | 1 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 26b | Lever splices (X4, D36) | as named on the bill | 2 | eBay | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 30 | Solder wire | as named on the bill | see bill | Adafruit 1886 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 31 | Flux pen (optional, recommended for 16 AWG) | as named on the bill | 1 | Adafruit 3468 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 32 | Cable ties | as named on the bill | 75 along the cables | Home Depot | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 34 | Adhesive tie mount | as named on the bill | 27 | Standard Electric Supply (US) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 34b | Adhesive tie mount, small | as named on the bill | 24 | Hisco (Houston, TX) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 35 | Isopropyl alcohol | as named on the bill | 1 bottle | TestEquity (Moorpark, CA) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 33 | Polyimide (Kapton) tape | as named on the bill | about 0.2 m | Adafruit 3057 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 27 | PLA | Overture Easy PLA 1.75 mm, 1 kg | 1420 g | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| 28 | TPU | Overture TPU 95A 1.75 mm, 1 kg | 75.1 g | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E1 | Speaker | as named on the bill | 1 | DigiKey 102-1304-ND | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E2 | I2S amplifier | as named on the bill | 1 | Adafruit | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E3 | LEDs | none (1 W warm white bead, uxcell 10-pack) | 3 | Amazon (uxcell) | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| E3b | LED resistor | as named on the bill | 3 | SparkFun PRT-14493 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E4 | Eye glass | none (round disc about 29.6 mm) | 2 | Amazon (FINGERINSPIRE) | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| E5 | Projector reflector | Aurorad S5, as named on the listing | 1 | Amazon (Aurorad) | none | UNVERIFIED/BLOCKER | NOT ORDERABLE |
| E6 | Camera | Raspberry Pi Camera Module 3 (standard, with IR cut) | 1 | Adafruit 5657 | https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf | VERIFIED | STOCK NOT REOPENED |
| E7 | Camera cable (D34) | Raspberry Pi Camera Cable Standard-Mini 300 mm | 1 | X-On Electronics | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E7r | Camera cable, replaced (D34) | Adafruit 3157, 150 mm | 0 | Adafruit 3157 | not opened | UNVERIFIED/BLOCKER | DO NOT ORDER |
| E8 | I2S microphones (D47) | Adafruit 3421, Knowles SPH0645LM4H | 2 | Adafruit 3421 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E9 | Touch boards (D51) | as named on the bill | 2 | Adafruit | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| E10 | Touch pad foil (D51) | as named on the bill | 0.3 m | Adafruit | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T1 | Soldering iron | as named on the bill | 1 | Pine64 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T2 | Insert tips | as named on the bill | 1 | Pine64 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T3 | Crimper | as named on the bill | 1 | Amazon | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T4 | Hex keys | as named on the bill | 1 | Crawford Tool | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T5 | Wire stripper | as named on the bill | 1 | Home Depot | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| L2 | BEC programmer | as named on the bill | 1 | Castle Creations | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T6 | USB-C PD supply for T1 | as named on the bill | 1 | Amazon (ships from and sold by Amazon.com) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T6b | USB-C to USB-C cable, 5 A | as named on the bill | 1 | Adafruit 4199 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T7 | Robot charge adapter, 5 V | as named on the bill | 1 | Amazon (ships from and sold by Amazon.com) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T7b | USB-A to USB-C cable | as named on the bill | 1 | Amazon (ships from and sold by Amazon.com) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T8 | microSD card reader (optional, often on hand) | as named on the bill | 1 | Adafruit 5212 | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T9 | Wire stripper 12 to 20 AWG | as named on the bill | 1 | Home Depot | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T10 | Heat gun | as named on the bill | 1 | Home Depot | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T11 | Drill bit 6.0 mm | as named on the bill | 1 | Drills and Cutters (Doral, FL) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T12 | Drill bit 2.7 mm | as named on the bill | 1 | Drills and Cutters (Doral, FL) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T13 | Hand holder for T11, T12, T14 and T15 | as named on the bill | 1 | Drills and Cutters (Doral, FL) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T14 | Drill bit 4.0 mm | as named on the bill | 1 | Drills and Cutters (Doral, FL) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T15 | Drill bit 4.5 mm (contingency) | as named on the bill | 1 | Drills and Cutters (Doral, FL) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T16 | Screwdriver PH 0 (D36) | as named on the bill | 1 | Haus of Tools | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T17 | Screwdriver PH 1 (D36) | as named on the bill | 1 | Haus of Tools | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T18 | Bit PH 0 x 25 mm (D36) | as named on the bill | 1 | Jensen Tools | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| T19 | Drill bit 1/16 in (D36) | as named on the bill | 1 | Walmart | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| TE1 | Digital multimeter | as named on the bill | 1 | Home Depot | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| TE2 | Bench DC supply with current limit | as named on the bill | 1 | Siglent Technologies America (North Plains, OR) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| TE3 | Digital calipers 150 mm | as named on the bill | 1 | Penn Tool Co. (Maplewood, NJ) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |
| TE4 | DC electronic load | as named on the bill | 1 | Siglent Technologies America (North Plains, OR) | not opened | UNVERIFIED/BLOCKER | STOCK NOT REOPENED |

The note for each special line is in the sections above. For every other row, the datasheet cell is the whole finding: it was not opened, so the status is UNVERIFIED/BLOCKER, and orderable today is no.

## Old wall-dock parts list

twin/dock/DOCK_BOM_FULL.md is still the wall and paddle dock. D61 superseded that geometry. Those parts are not installed and are not the nest order. The charger board and the ideal diodes are the only items that the nest study still points at, and they are covered above. Mill-Max 0933 spring pins are the old dock pins (short stroke). They are not the nest pins. Their datasheet was not opened this session.

## Counts

- BOM lines in the table: 105.
- Lines with a datasheet opened this session and a matching purchase spec: 3 (the Pi, the camera, and the P45B; the cell maximum fits the existing sleeved bay).
- Lines opened and marked MISMATCH: 1 (the STS3215 against the twin's stall and 70 C cut).
- Lines marked UNVERIFIED/BLOCKER in the special notes: 40, plus every fastener and every row whose datasheet cell says not opened.
- Orderable today, by the rule at the top: none. Two named sellers were opened and were out of stock (the Pi at Adafruit, the P45B at 18650 Battery Store). Every other line is STOCK NOT REOPENED, NOT ORDERABLE, or DO NOT ORDER.

That count is the first write only. The next section reopened pages on 2026-11-11 evening ET and replaces it.

## Session 2026-11-11 ET

Reads in this session, evening of 2026-11-11 ET. A number from a page opened here is labeled with that page. A number from the nest CAD stays CAD check only. A number that was not opened stays BLOCKER. This section does not change BOM.md.

Orderable today still means all four: an exact manufacturer part number (or the seller model the opened page prints, when the maker publishes no other number), a named distributor, a quantity, and a page opened this session that shows the part can be bought. A fit that is still unchecked is labeled BLOCKER even when the listing itself can be bought.

### Spring pin

Catalog opened: QA Technology 2023 catalog, pages 32 and 33, https://www.qatech.com/pdfs/2023_QA-Catalog.pdf . The part number is built as 100-PR, then the tube letter, then 40, then the tip digits, then the spring letter. The example on page 32 is 100-PRP4003L.

Chosen probe: **100-PRP4030S**.

- Tube P (catalog page 32): nickel silver, ID precious metal clad, average resistance under 20 mOhm, average current 10.2 A at 120 C and 14.3 A at 204 C. The catalog footnote says the spring material and the lubrication change that current.
- Tip 30 Round (catalog page 33): head diameter 0.055 in, which the page prints as 1.40 mm.
- Spring S (catalog page 32): 1.5 oz at first touch, which the page prints as 43 g and 0.42 N, and 5.7 oz at 0.317 in stroke, which the page prints as 162 g, 1.58 N, and 8.05 mm. Life 500,000 cycles at that stroke. Full stroke 0.400 in, 10.16 mm. Tube diameter 0.0538 in, 1.367 mm.

Geometry change this probe needs: the nest drawing uses a round head of about 2.3 mm (nestcad_lib.py, estimate, and NEST_CAD.md). The catalog head is 1.40 mm. Redraw the tip to 1.40 mm. The TPU well is 3.6 mm (nestcad_lib.py, drawn for the 2.3 mm estimate). A 1.40 mm head has more side clearance in that well, so the well does not have to grow. The nest substitute line asked for a rounded tip 2 mm or more across (NEST_CAD.md). This tip does not meet that. Whether 1.40 mm punches the cloth is still a bench test, BLOCKER.

Closest options on the same pages, and the geometry change each needs:

| Probe | Tip on the catalog page | Geometry change |
|---|---|---|
| 100-PRP4030S | 30 Round, 1.40 mm | Redraw the tip from 2.3 mm to 1.40 mm. This is the one proposed. |
| 100-PRP4040S | 40 Round, 0.91 mm | Redraw the tip to 0.91 mm. Smaller contact on cloth. |
| 100-PRP4010S | 10 Flat, 1.57 mm | Redraw a flat face at 1.57 mm. Not a sphere. Still under 2 mm. |
| 100-PRP4009S | 09 Serrated, 2.92 mm, minimum centers 3.81 mm | The pins are 20 mm apart (NEST_CAD.md), so the center rule passes. The face is serrated. The nest text says a crown or a point catches cloth. A serrated face has the same risk. The 3.6 mm well is 0.34 mm clear of a 2.92 mm head on each side. Grow the well before this tip is used. |

No round conductive tip on the opened 100-40 pages is 2.3 mm. On the 100-25 pages the 0.090 in (2.29 mm) head is tip 99, an insulator, not a contact.

Socket: **100-SDN250S**, printed on the same 100-40 catalog pages. Nickel silver, no finish, solder cup, press ring code 0 at 0.300 in (7.62 mm). The length printed beside that part number is 1.187 in (30.15 mm). Suggested mounting hole 0.0670 to 0.0690 in (1.702 to 1.753 mm), drill 1.75 mm, in AT7000, G10/FR4 or similar, not in PLA. The drawing shows a typical socket outside of 0.066 in (1.68 mm). The nest estimate of a press ring at 10.03 mm is the other press-ring code (digit 1), not this part.

TestEquity page opened for 100-SDN250S: Out of Stock, manufacturer lead time 8 days. That page says the socket accepts 100-25 series probes, and the same page lists the series as 100-40. The catalog draws this socket on the 100-40 sheet. Follow the catalog. The TestEquity sentence is recorded so it is not hidden.

TME US page opened for 100-SDN250S: 533 in stock, minimum order 5, and the page says the product can be purchased only from the international offer. That is not a confirmed US cart. BLOCKER for a US one-click of the socket.

Probe 100-PRP4030S: no distributor page opened this session showed it in stock. NOT TODAY. The PLA press fit of the 1.75 mm hole stays BLOCKER, because the catalog hole is for board material, not printed PLA.

### Felt, cloth, foil, foam, gate

Felt, about 1 mm, two layers, and the 2 mm rim sleeve (NEST_CAD.md, CAD check only): no manufacturer part number on a page opened this session. BLOCKER. Do not order a craft sheet with no grade.

Conductive cloth: Shieldex Nora Dell, product ID 1401101S80, page https://www.shieldex.de/en-us/products/shieldex-nora-dell/ opened. Silver, copper, and nickel. Electrical surface resistivity under 0.009 ohm per square (that page). Thickness 0.125 mm plus or minus 15 percent (that page). Weight 100 g per square metre plus or minus 15 percent (that page). A datasheet link is on the page. The page does not call the cloth gold or pale gold. One grey cloth cannot be both the sun and the ring. If it is used for both, the camera loses the two colors, and both poles look the same. That is a look change, and the camera nest find is already untested (BLOCKER). The US shop link on the page was not opened, so stock is not confirmed. NOT ORDERABLE as the gold pair.

Foil: 3M 1181 X 1/2, DigiKey page https://www.digikey.com/en/products/detail/3m/1181-X-1-2/111515 opened. The page description says buy now, ships today. Copper foil, conductive adhesive, single sided, width 0.500 in (12.70 mm), length 54.000 ft (16.50 m), thickness 0.003 in (0.08 mm). The drawn feed is 12 mm (NEST_CAD.md). Change the feed from 12 mm to 12.7 mm, or slit the tape. The sun disc is 90 mm (NEST_CAD.md). A 12.7 mm roll cannot cut that disc in one piece. Tiling it makes seams. A wider 1181 roll was not opened, so it is not claimed in stock. The half-inch roll is the orderable feed. The one-piece disc stays BLOCKER.

Rim foam: no part number. BLOCKER. The bolsters are cut soft foam (NEST_CAD.md).

Gate board: the circuit is not designed. No manufacturer part number. BLOCKER. The CAD keeps a space of 70 x 26 x 14 mm (NEST_CAD.md). Do not order a board in its place.

In-duck charger: the MCP73213 datasheet was still not opened. Dropout, the timer, and the thermistor stay BLOCKER. The eval board is not a seated part. Line 11 is not that charger.

### Lines that had no manufacturer part number

Line 7, the spot-welded pack: no nickel strip, sleeve, fish-paper, or weld-shop part number on a page opened this session. BLOCKER. Leave it off a one-click order.

Line 11: Amazon page for ASIN B0BJTW4QBR opened. Manufacturer Adeept. The page prints manufacturer part number Li-ion_Battery_Charger_M-2S2A and model 18650 Charge Board, variant 2S-2A-8.4V. Availability text: Only 7 left in stock. No datasheet and no hole drawing. The CAD body on the bill is 38.2 x 18.1 x 5.2 mm, holes 2.5 mm at 14.4 mm pitch. Fit stays BLOCKER until that check. The listing itself can be bought.

Line 14: Amazon page for ASIN B072V529YD opened. Manufacturer Miuzei. Model on the page: SG90 9G Servo. The part number field is the ASIN. Availability: In Stock. The page calls the servo metal gear and digital. A Tower Pro datasheet was not opened. Datasheet BLOCKER. The listing itself can be bought. The stock-first PWM note in the lab rules is unchanged.

Line 17m: no page opened for an M2 x 12 thread-forming pan head with a head about 4.0 mm by 1.6 mm (the fastener schedule). BLOCKER. A slotted machine screw is a different part and is not proposed.

Line 22c: 22-01-3027 is not the Molex number. The 2-circuit KK 254 housing, series 2695, is Molex 0022012027. DigiKey page https://www.digikey.com/en/products/detail/molex/0022012027/171991 opened. The page description says buy now, ships today. That one housing is orderable. The line is not. The harness now lands a KK housing on 15 cables (D2, D3, D4, D5, D6, D7, D8, D9, D10, D13, D14, D16, D22, P12, P17), and several of those cables share a header pin or use both rows. Two housings cannot sit on one pin. A buy of 11 housings of one width is the wrong cart. BLOCKER until each header pin is given to one cavity. P12 and P17 are 20 AWG (HARNESS_BUILD.md). Terminal 08-50-0114 is 22 to 30 AWG on the bill. Those two crimps need a different terminal, and that terminal was not opened. BLOCKER for those two ends.

Line E3: Amazon page for ASIN B07DHB13J4 opened. Manufacturer uxcell. Manufacturer part number and model on the page: a18032300ux0174. Title: 1 W LED chip, warm white, 280 to 350 mA. Availability: Only 9 left in stock. The same page also says bulb shape B10, which fights the bead title. No mechanical drawing. Fit in the eye stays BLOCKER.

Line E4: Amazon page for ASIN B0C4H17QSH opened. Manufacturer FINGERINSPIRE. Model on the page: KY-FG0001-10-US18. The page says 30 mm diameter and 2 mm thick, 60 pieces. Availability: Only 9 left in stock. The CAD eye glass on the bill is 29.6 mm by 1.85 mm. The bill already says the disc fit was checked with the left eye test print. The listing can be bought. The 0.4 mm diameter difference and the 0.15 mm thickness difference are the ones that print already accepted.

Line E5: Amazon page for ASIN B0BGS3C42N opened. Title Aurorad S5. The page says diameter 20 mm, height 15 mm, LED hole 7 mm, which matches the seat text on the bill. Availability: in stock, ships in 3 to 4 days. The manufacturer part number field is the word Aurorad, not a unique number. D29 would have dropped this reflector. D33 reverts D29 and keeps the side projector lamp, the reflector, and its lead (DECISIONS.md D33). Keep Need 1 and Buy 1. The listing can be bought.

Line DK1: still the old chest pad. D61 replaces that dock. Proposed: do not order it for the nest. DECISIONS.md is not edited here.

Line DK5: Adafruit 372 (the 10 k NTC) is in stock on the product page. The zener onsemi 1N5228B, the 1N4148, and the resistors were not opened. The set is not one part number. NOT ORDERABLE as a set.

### Pi Zero 2 W and the P45B

Line 3, Adafruit 5291: product schema OutOfStock on the page opened this session.

CanaKit page https://www.canakit.com/raspberry-pi-zero-2-w.html opened. PI-Z2W (board only) Sold Out. PI-Z2WH (board only, pre-soldered header) Sold Out. Starter kit with pre-soldered header, code PI-Z2WH-STR32-C4-BLK, shows Add to Cart. That kit is the in-stock alternate that includes the board. The bare board is NOT TODAY.

Line 6, Molicel INR21700-P45B: 18650 Battery Store page opened, stock words "Sold out". Liion Wholesale page opened, SKU molicelnpe-inr21700-p45b, words "Out Of Stock". The P50B alternate was not on a page that showed stock this session. No in-stock alternate was confirmed. NOT TODAY.

### Stock seen this session, every BOM line

HTTP 403 means the distributor refused the fetch, so stock was not reopened. A mixed page means both "in stock" and "out of stock" appeared and the product itself was not isolated.

| Line | What was seen | Orderable today |
|---|---|---|
| 1 | Seeed, schema InStock, data-stock 41, title ST3215 C001, sku 108090023 | yes |
| 1b | OpenELAB, schema InStock, STS3250-C002 | yes. Datasheet not opened |
| 2 | Waveshare, schema InStock, SKU 25514 | yes |
| 3 | Adafruit 5291, schema OutOfStock | NOT TODAY. Kit alternate above |
| 4 | Amazon, Only 20 left, SDSQUAR-032G-GN6MA | yes |
| 5 | Adafruit 2472, schema InStock | yes |
| 5b | Adafruit 5396, schema InStock | yes |
| 6 | 18650 Battery Store Sold out. Liion Wholesale Out Of Stock | NOT TODAY |
| 7 | no part number | NOT ORDERABLE |
| 8 | Tenergy page: in stock, order now to ship in 1 business day | yes |
| 9 | Pololu 4892: Rationed (Active and Preferred), backorders allowed | yes, rationed |
| 10 | Pololu 2813: Rationed, backorders allowed | yes, rationed |
| 10r | Pololu 2815: Rationed, backorders allowed. Buy quantity 0 | DO NOT ORDER |
| 10b | page text "In stock", schema not isolated | not clean |
| 10b-old | no product page | DO NOT ORDER |
| 11 | Amazon, Only 7 left, MPN Li-ion_Battery_Charger_M-2S2A | yes as that listing. Fit BLOCKER |
| 12 | Amazon in stock, Amass XT30U named on the bill | yes |
| 13 | DigiKey HTTP 403 | STOCK NOT REOPENED |
| 13b | Adafruit 2782, schema InStock, page text 17 in stock | yes |
| 14 | Amazon In Stock, Miuzei model SG90 9G Servo | yes as that listing. Datasheet BLOCKER |
| 15 | Microsoft page HTTP 404 | STOCK NOT REOPENED |
| L1 | Horizon, schema InStock, stockLevel 366, 010-0004-01 | yes |
| L3 | Newark HTTP 403 | STOCK NOT REOPENED |
| L4 | DigiKey HTTP 403 | STOCK NOT REOPENED |
| DK1 | OSH Park service page, not a finished board | DO NOT ORDER for the nest |
| DK2 | Pololu 5382: Rationed, backorders allowed | yes, rationed |
| DK3 | Newark HTTP 403 | STOCK NOT REOPENED |
| DK4 | DigiKey HTTP 403 | STOCK NOT REOPENED |
| DK5 | Adafruit 372 schema InStock. The rest of the set was not opened | set NOT ORDERABLE |
| DK6 | Pololu 5382: Rationed, backorders allowed | yes, rationed |
| DK7 | Pololu 5383: schema InStock, page text Active and Preferred | yes |
| 16 | CNC Kitchen schema InStock. The HTML also contains Sold out | yes from the schema. Check the button |
| 17a | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17b | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17c | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17d | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17e | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17f | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17g | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17i | Bolt Depot HTTP 403 | STOCK NOT REOPENED |
| 17h | Amazon, Only 6 left, METALLIXITY M2 self-tapping kit | yes |
| 17j | BelMetric: in stock, and this configuration is not available | NOT TODAY |
| 17k | BelMetric: in stock, and this configuration is not available | NOT TODAY |
| 17l | BelMetric: in stock, and this configuration is not available | NOT TODAY |
| 17m | no listing | NOT ORDERABLE |
| 18 | Amazon, Only 1 left, 6804ZZ | yes, one left |
| 19 | Amazon, Only 3 left, Loctite 1330799 | yes |
| 29 | Zoro HTTP 403 | STOCK NOT REOPENED |
| 20 | Adafruit 3878, schema InStock | yes |
| 21 | Newark HTTP 403 | STOCK NOT REOPENED |
| 22 | Newark HTTP 403 | STOCK NOT REOPENED |
| 22b | Octopart HTTP 403 | STOCK NOT REOPENED |
| 22c | 0022012027 is orderable as a 2-circuit housing. The 11-piece line is not | NOT ORDERABLE as specified |
| L5 | Amazon In Stock, BNTECHGO 16 AWG | yes |
| 23 | Amazon, Only 18 left, BNTECHGO 20 AWG | yes |
| 24 | Amazon, Only 4 left, BNTECHGO 22 AWG | yes |
| 25 | Amazon, Only 13 left. The offer served ASIN B08FMDNRMW with the same 26 AWG title | yes |
| 26 | Amazon, Currently unavailable, Wirefy kit | NOT TODAY |
| 26b | eBay HTTP 403 | STOCK NOT REOPENED |
| 30 | Adafruit 1886, schema OutOfStock | NOT TODAY |
| 31 | Adafruit 3468, schema InStock | yes |
| 32 | Home Depot HTTP 403 | STOCK NOT REOPENED |
| 34 | Standard Electric, schema InStock, 151-01629 | yes |
| 34b | Hisco page fetched. Product quantity was not in the static HTML | STOCK NOT ISOLATED |
| 35 | TestEquity page mixed in stock and out of stock | STOCK NOT ISOLATED |
| 33 | Adafruit 3057, schema OutOfStock | NOT TODAY |
| 27 | Amazon In Stock, Overture Easy PLA black | yes |
| 28 | Amazon In Stock. Offer served ASIN B07VDP2S3P. Title is Overture TPU 95A black | yes |
| E1 | DigiKey HTTP 403 | STOCK NOT REOPENED |
| E2 | Adafruit 3006, schema OutOfStock | NOT TODAY |
| E3 | Amazon, Only 9 left, uxcell a18032300ux0174 | listing yes. Fit BLOCKER |
| E3b | SparkFun page mixed in stock and out of stock | STOCK NOT ISOLATED |
| E4 | Amazon, Only 9 left, model KY-FG0001-10-US18 | yes |
| E5 | Amazon in stock, ships in 3 to 4 days. Title Aurorad S5. D33 keeps it | yes as that listing. Unique maker number is only the brand word |
| E6 | Adafruit 5657, schema InStock | yes |
| E7 | X-On HTTP 403 | STOCK NOT REOPENED |
| E7r | Adafruit 3157 schema InStock. Buy quantity 0 | DO NOT ORDER |
| E8 | Adafruit 3421, schema InStock | yes |
| E9 | Adafruit 1982, schema InStock | yes |
| E10 | Adafruit page text, 16 in stock, product 1127 | yes |
| T1 | Pine64, schema InStock, PINECIL-BB2 | yes |
| T2 | Pine64 page fetched. Product schema not isolated | STOCK NOT ISOLATED |
| T3 | Amazon In Stock, Engineer PA-09 | yes |
| T4 | Crawford page mixed in stock and sold out | STOCK NOT ISOLATED |
| T5 | Home Depot HTTP 403 | STOCK NOT REOPENED |
| L2 | Castle page: Sold out, Castle Link V4 | NOT TODAY |
| T6 | Amazon In Stock | yes |
| T6b | Adafruit 4199 page fetched. Product schema not isolated | STOCK NOT ISOLATED |
| T7 | Amazon In Stock | yes |
| T7b | Amazon In Stock | yes |
| T8 | Adafruit page text, 25 in stock, product 5212 | yes |
| T9 | Home Depot HTTP 403 | STOCK NOT REOPENED |
| T10 | Home Depot HTTP 403 | STOCK NOT REOPENED |
| T11 | Drills and Cutters page text Ships Today next to DWDMM6.00 | yes |
| T12 | same site, page text Ships Today. Bit diameter not re-read off the title | not clean |
| T13 | same site, page text Ships Today | not clean |
| T14 | same site, page text Ships Today | not clean |
| T15 | same site, page text Ships Today | not clean |
| T16 | Haus of Tools page mixed in stock and sold out | STOCK NOT ISOLATED |
| T17 | Haus of Tools page mixed in stock and sold out | STOCK NOT ISOLATED |
| T18 | Jensen page mixed in stock and out of stock | STOCK NOT ISOLATED |
| T19 | Walmart page fetched, stock words not isolated | STOCK NOT ISOLATED |
| TE1 | Home Depot HTTP 403 | STOCK NOT REOPENED |
| TE2 | Siglent page, schema InStock, SPD1168X | yes |
| TE3 | Penn Tool page mixed in stock strings | STOCK NOT ISOLATED |
| TE4 | Siglent page, schema OutOfStock, SDL1020X-E | NOT TODAY |

### What a one-click can buy after this session

Clean orderable lines, by the four-part rule, from a page that showed the part can be bought: 1, 1b, 2, 4, 5, 5b, 8, 9, 10, 11, 12, 13b, 14, 17h, 18, 19, 20, 23, 24, 25, 27, 28, 31, 34, L1, L5, DK2, DK6, DK7, E4, E5, E6, E8, E9, E10, T1, T3, T6, T7, T7b, T8, T11, TE2. Line E5 is the Aurorad S5 listing. D33 keeps it. The maker field on that page is only the word Aurorad. Line 16 is orderable from the product schema, and the page also contains the words Sold out, so the button should be checked. Lines 9, 10, DK2, and DK6 are rationed with backorders allowed.

Still blocked, and why:

- Spring probe 100-PRP4030S: part number is now complete, and no in-stock US page was opened. Socket 100-SDN250S: TestEquity out of stock, TME not a confirmed US cart. PLA press fit BLOCKER. Tip geometry change above.
- Felt, pale gold cloth, gold cloth as a pair, the 90 mm foil disc, rim foam, the gate board, the in-duck charger: no orderable part.
- Line 7 weld, line 17m, line 22c as an 11-piece set: no completed buy.
- Line 6 P45B: out of stock at both sellers opened. No P50B stock page opened.
- Line 3 bare Pi: out of stock at Adafruit and at CanaKit as a bare board. The header starter kit PI-Z2WH-STR32-C4-BLK showed Add to Cart.
- Out of stock on a page that did open: line 26 heat shrink, line 30 solder, line 33 polyimide tape, line E2 amplifier, line L2 Castle Link, line TE4 load.
- Not reopened (HTTP 403 or 404): 13, 15, L3, L4, DK3, DK4, 17a, 17b, 17c, 17d, 17e, 17f, 17g, 17i, 21, 22, 22b, 26b, 29, 32, E1, E7, T5, T9, T10, TE1.
- BelMetric 17j, 17k, 17l: the page said the configuration is not available.
- Line DK1: do not order for the nest (D61). Line E5 stays (D33). Line 10r and line E7r stay at quantity 0.

