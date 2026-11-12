# PARTS AUDIT

Written 2026-11-11 ET. Research only. Nothing was bought. This file does not change BOM.md.
No prices are written here. A number from a document opened this session is labeled with that document.
A number from a sim, a calc, or a CAD check keeps that label. Anything not opened is UNVERIFIED/BLOCKER.

This is the parts half of gate 0 and all of gate 1 in DEFINITION_OF_DONE.md. Neither gate passes because of this file.

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
- Cell envelope drawn at 21.4 x 70 mm. The opened P45B sheet gives 21.55 mm and 70.15 mm as maximums. Weld resistance of the pack is unknown (line 7). Some older twin runs still use a P30B pack model.
- Charger dropout and the 1.9 to 3.2 W of heat in the trunk: calc only. The thermal twin was not re-run with the charger inside the duck. The MCP73213 sheet was not opened.
- Camera: the nest sim uses true pose plus noise. It is not a camera model, not a lens, and not room light. The camera brief gives the sensor and the 0 C to 50 C range. It does not give a model of finding a mat.
- Mat edge in the sim is one 2 mm rise. The CAD edge is two 1 mm steps. Those steps have not been simulated.

## Proposed bill changes (not applied)

- Do not order DK1 for the nest. Do not order DK5 until the two-wire gate has a real parts list.
- Add the probe only after the tip code is chosen from the catalog (a round tip, 30 or 40, standard spring S, a tube whose current note is read). Add four 100-SDN250S sockets. Do not press them into PLA until a coupon holds the catalog hole.
- Size the cell bay to the opened sheet's maximum, 21.55 mm diameter and 70.15 mm height, and say which sheet revision the drawing uses.
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
| 6 | Li-ion cell | Molicel INR21700-P45B | 2 | 18650 Battery Store | https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf | MISMATCH | NOT TODAY |
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
- Lines with a datasheet opened this session and a matching purchase spec: 2 (the Pi, and the camera).
- Lines opened and marked MISMATCH: 2 (the STS3215 against the twin's stall and 70 C cut, and the P45B against the drawn cell size).
- Lines marked UNVERIFIED/BLOCKER in the special notes: 40, plus every fastener and every row whose datasheet cell says not opened.
- Orderable today, by the rule at the top: none. Two named sellers were opened and were out of stock (the Pi at Adafruit, the P45B at 18650 Battery Store). Every other line is STOCK NOT REOPENED, NOT ORDERABLE, or DO NOT ORDER.

