# US-made parts for one duck

This is a study. It does not change the selected BOM, the order, the twin, or the domestic-content worksheet. Nothing was bought. No one was contacted.

This is not legal advice. A lawyer has to apply the FCC reading. A number is cited, calc only, sim pass only, or BLOCKER. The share math is recomputed by `altaay_lab/problems/us_parts_share.py` from `altaay_lab/compliance/DOMESTIC_ROWS.csv` and the judgments in that script. The line file is `altaay_lab/problems/US_PARTS.csv`.

## What this builds on

The content prong is the one in `altaay_lab/compliance/DOMESTIC_CONTENT.md`. Domestic components have to exceed 65 percent of component cost for a delivery in 2024 through 2028, and 75 percent starting in 2029. The worksheet follows the FCC FAQ: the off-the-shelf waiver is not applied, and unknown origin is counted foreign because 48 CFR 25.003 says so. The FAQ does not repeat that sentence. A lawyer can reject it. This study uses the same reading the worksheet uses.

Current share, carried forward, calc only: $47.33 domestic of $905.36, which is 5.23 percent. The domestic dollars are the Pololu 5 V regulator at $29.95 and 24 Panduit mounts at $17.38. The 14 servos are $288.82 of the foreign column. Per-duck parts on the order are $957.75 (calc only). The first-build cart is $1204.26 (calc only). Those two order figures are a different basis from the share: the cart includes tools and full spools, and the per-duck figure drops the tools and the full spools and keeps the controller. The share drops tools, the nest, the controller, and process aids, uses the Pi board at $19.60 rather than the kit, and counts the filament spools in full because that is how `domestic_share.py` treats the pla row when the order has a price. Printed-gram dollars stay the BLOCKER the order already names. This study does not switch bases.

A pass is a part made in the United States, or assembled there only where the page says the article is manufactured in the United States, that meets or beats the current part on every datasheet line that the duck uses: torque, speed, voltage, current, accuracy, temperature, life, tolerance, and safety marks, when the current page prints that line. A US seller, a US design office, and "ships from the United States" are not that sentence. "Designed in" is not that sentence. If no true equivalent was opened, the line is not passed, and a weaker part is not substituted.

The finished duck still has to be manufactured in the United States. That prong is open in the worksheet. None of the swaps below close it. Freight and duty are still not in the prices. BLOCKER, same as the worksheet.

## The servo

This is the line that moves the share. Fourteen Feetech ST-3215-C018, Waveshare SKU 22414, $20.63 each at four or more, $288.82 for fourteen (cited, `problems/NEST3.md`). That is 31.90 percent of the $905.36 (calc only).

The maker page opened for this study, https://www.feetech.cn/en/525603 , prints:

| Line | Value |
| --- | --- |
| Stall torque | 30 kg.cm at 12 V, which is 2.942 Nm (calc only, the same 30 times 0.0980665 already in `problems/STS12.md`) |
| Rated torque | 10 kg.cm at 12 V |
| Stall current | 2.7 A at 12 V |
| No-load speed | 0.222 s/60 deg at 12 V, which is 4.717 rad/s (calc only, `problems/STS12.md`) |
| No-load current | 180 mA at 12 V |
| Voltage | 4 V to 14 V |
| Temperature | operating -20 C to 60 C, storage -30 C to 80 C |
| Size | 45.2 mm by 24.7 mm by 35 mm |
| Mass | 55 +/- 1 g |
| Spline | 25T, outside diameter 5.9 mm |
| Gears | steel, ball bearings |
| Command | digital packet, half duplex asynchronous serial, ID 0 to 253, 38400 bps to 1 Mbps |
| Position | 360 deg when the word runs 0 to 4096 |

The page footer names Shenzhen FEETECH RC Model CO., Ltd., at an address in Longgang, Shenzhen, China. The Waveshare listing still does not print a country of origin. The worksheet counts the line foreign. The maker address agrees with that column. It does not by itself replace the worksheet.

The twin that walks is run C (`problems/retrain_sts12/SUMMARY.md`, sim pass only): the actuator is this sheet, the trunk carries the third P45B, and the bus is the 3S pack. Pack peak on that run is 15.6 A (sim pass only). Knee voltage goes to 9.31 V (sim pass only), inside the 4 V to 14 V page and inside the Waveshare 6 V to 12.6 V table. A dock that leaves the servo rail on can put about 14.7 V on that rail, which is already outside the 4 V to 14 V page (`circuitry/SERVO_RAIL.md`). The pick in that note holds the rail off while docked. A substitute has to live on the walk voltages, not on 14.7 V.

No United States serial-bus servo of this size was opened.

| Spec | ST-3215-C018 | ProModeler DS270DLHV | Mini-Torxis | Teknic ClearPath | Glentek GMB2005-8 |
| --- | --- | --- | --- | --- | --- |
| Stall or peak torque | 30 kg.cm (2.942 Nm) at 12 V | 270 oz-in, which is 19.44 kg.cm (calc only). Fail. The DL series text on the same page tops out at 360 oz-in, 25.92 kg.cm (calc only). Still under. | 700 oz-in, and the page also prints 4.9 N.m. That is above 2.942 Nm. Pass on torque. | Not used. The frame already fails. | 0.27 Nm continuous (2.4 lb-in on the category page). Under 2.942 Nm. Fail. |
| No-load speed | 0.222 s/60 deg at 12 V | Not printed on the page opened. | 0.13 s/60 deg at full voltage. Faster. Would pass speed. | Not the deciding line. | Not a hobby position speed. |
| Voltage | 4 V to 14 V | Not printed on the page opened. | A 12 V version is listed. The min and max are not printed. | Industrial supply, not this pack. | Not this pack. |
| Current | 2.7 A stall at 12 V | Not printed. | Not printed. | Not opened. | Not a 2.7 A stall figure. |
| Mass | 55 +/- 1 g | Not printed. | 158 g. Fail. Fourteen of them add 1.442 kg (calc only, 14 times 103 g). | NEMA 23 class, far above 55 g. Fail. | Not this mass. |
| Size | 45.2 x 24.7 x 35 mm, 25T spline | Standard-class RC case. Not this drawing. Fail. | Body size was not printed. The 6.5 x 5.5 x 4.5 in line reads as the ship box, not a drawing. Size is not a pass. | Smallest frame in the user manual is NEMA 23, body length code 82 mm. Fail. | Industrial frame. Fail. |
| Travel and counts | 360 deg, 0 to 4096 | RC servo. No 4096-count word. Fail. | 180 deg total. Fail for a joint that uses the 360 deg word. | 800 or 6400 counts per rev in the manual. Not the Feetech word. | A motor, not this servo. |
| Bus | Half duplex TTL, up to 1 Mbps | Not a serial bus. Fail. | "Standard 5VDC PWM". Fail. | Step and direction, or Teknic software. Fail. | Not this bus. |
| Temperature | -20 C to 60 C | Not printed. | Not printed. | Not the deciding line. | Not the deciding line. |
| Origin | Shenzhen address on the maker page | $54.99, in stock. The page opened does not say the servo is manufactured in the United States. | $79.99. No country sentence. | Homepage: "U.S. manufacturer". Footer address Victor, NY 14564 USA. Models start at $249. | About page: manufactured in El Segundo, California. No catalog price. |
| Call | Current part | Fail | Fail | Fail | Fail |

Links: https://www.feetech.cn/en/525603 , https://www.promodeler.com/DS270DLHV , https://gearwurx.com/product/mini-torxis-servo-2/ , https://teknic.com/ , https://www.teknic.com/files/downloads/clearpath_user_manual.pdf , https://www.glentek.com/about/ , https://www.glentek.com/product-category/motors/gmbgmbf/ , https://www.glentek.com/shop/motors/gmbgmbf/gmb2005-8/ .

A swap to any of those is a different machine. The case and the 25T spline are cut into the printed parts. PWM or a NEMA bolt circle does not land on the Feetech horn. The netlist bus is half duplex through the adapter U2, one control cycle for 14 servos (`TWIN_CHECKLIST.md` timing row). A PWM servo deletes that bus and needs a signal wire per joint. Mass changes the trunk and the legs. The torque curve changes the actuator the policy was trained on: run C uses 2.942 Nm and 4.717 rad/s, not the older 5.646 rad/s trained speed and not a 4.9 N.m PWM curve. That is a new training job, the same kind of job `problems/TRAIN_STS12.md` already names for this sheet. It is not started here. The knee, the sit, and the heat model stay on the STS3215.

The old worksheet's $56.59 actuator threshold was on a superseded total. On today's $905.36, fourteen domestic actuators clear 65 percent only when each one costs $72.13 or more (calc only). At $72.12 the share does not exceed 65 percent. They clear 75 percent at $118.60 or more (calc only). At $118.59 the share does not exceed 75 percent. Those are thresholds, not prices of a servo that passed. No such servo was found at any price.

## The BEC

Castle CC BEC Pro, 010-0004-01, $54.95 (cited, the order). The Castle product page opened this session, https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01 , prints 20 A peak, a continuous figure of 15 A at 16 V input (and less at a higher input), output adjustable from 4.9 V to 12.5 V through Castle Link, and a maximum input of 12S (50.4 V). The same page says the product is designed in Olathe, Kansas, USA. It does not say it is manufactured there. Other Castle pages say some ESCs are manufactured in Olathe. That sentence was not on the BEC page, and it is not borrowed. The line stays unknown origin, counted foreign.

The US board that was opened is the Pololu D42V110F12, https://www.pololu.com/product/5677 , $69.95. The page says these boards are manufactured in-house at the Las Vegas facility. That origin sentence would count, and the electrical lines do not.

| Spec | CC BEC Pro | Pololu D42V110F12 | Call |
| --- | --- | --- | --- |
| Peak current | 20 A | Typical maximum about 9 A, and less as the input rises | Fail |
| Continuous at a low input | 15 A at 16 V input | The page ties the continuous number to heat. It is not 15 A. | Fail |
| Output | 4.9 V to 12.5 V, adjustable | Fixed 12 V, 3 percent | Fail |
| Input | Up to 50.4 V | 12 V to 60 V, and dropout sits above 12 V | Fail on a 3S pack that sags under 12 V. Run C already draws 15.6 A peak (sim pass only). |
| Origin | Designed in Olathe. Manufacture not printed. | Manufactured in Las Vegas. | Origin would pass. The part is still not equivalent. |
| Price | $54.95 | $69.95 | Plus $15.00 (calc only). Not taken. |

The 5 V regulator already on the duck, Pololu D30V30F5, is the Las Vegas board the worksheet counts domestic. The big pushbutton page and the 12 A ideal-diode page were opened too. Those extracts did not print the Las Vegas sentence. They are not reclassified.

## The one pass: PLA

Overture Easy PLA, 1.75 mm, two 1 kg spools, $17.99 each, $35.98 on the order (cited). BOM.md line 27 prints nozzle 190 C to 220 C and bed 25 C to 60 C. It does not print a tensile strength. Origin was not printed. Counted foreign. Incorporated cost on the share is the full $35.98, not the printed grams.

3DXTech ECOMAX PLA, https://www.3dxtech.com/products/ecomax-r-pla . The page says the blend is made in the USA from virgin NatureWorks PLA resin, and that all of their filaments are manufactured in their plant in Grand Rapids, Michigan. The price on that page is $36.00. A data-sheet page that says its figures are sourced from the manufacturer, https://www.spoolscout.com/data-sheets/3dxtech/pla-ecomax-pla , prints diameter 1.75 mm, density 1.24 g/cm3, tensile strength at break 56 MPa (ISO 527), tensile modulus 2865 MPa (ISO 527), nozzle 210 C, bed 23 C. The product-page extract also contained a 365 C to 390 C figure. That is not a PLA nozzle and it is not used.

| Spec | Overture Easy PLA | 3DXTech ECOMAX PLA | Call |
| --- | --- | --- | --- |
| Polymer | PLA | PLA, virgin NatureWorks resin | Pass |
| Diameter | 1.75 mm | 1.75 mm | Pass |
| Nozzle | 190 C to 220 C | 210 C | Pass |
| Bed | 25 C to 60 C | 23 C recommended | A start setting. Not a limit that makes the resin worse. |
| Tensile | Not printed in BOM.md | 56 MPa, ISO 527 | The candidate publishes a number. There is no Overture number on the bill to beat. |
| Modulus | Not printed | 2865 MPa, ISO 527 | Same. |
| Origin | Not printed. Counted foreign. | Manufactured in Grand Rapids, Michigan. | Pass, on the worksheet's reading. A lawyer still decides whether the resin inside the spool is looked through. |
| Price | $17.99 a spool, $35.98 for two | $36.00 a spool, $72.00 for two (calc only) | Plus $36.02 (calc only). |
| Call | Current | Pass | Taken in the "all passing" scenario only. The order is not changed. |

Confirm the 1 kg variant on the product page before anyone buys. Nothing was bought. The NatureWorks sentence does not say the resin was polymerized in the United States. The component this study counts is the spool manufactured in Grand Rapids.

No twin change. The walk does not depend on a PLA tensile the bill never printed. If a later slice uses the 1.24 g/cm3 density and the grams move, that is a re-slice, not a retrain. The shin stays the Bambu PA6-CF. This study does not put ECOMAX on the order.

## Lines that were opened and did not pass

Cells. Three Molicel INR21700-P45B, $8.99 each, $26.97 (cited). The lab already uses about 4.5 Ah, 4.20 V charge, 21.4 mm by 70 mm, 70 g (`twin/battery/CHARGE_INTERFACE.md` and `problems/STS12.md`, from the Molicel sheet). The sheet named in the worksheet prints a Canada facility and a Taiwan facility. No US-made 21700 of that class was opened. A US shop selling another maker's cell is not a US factory. A different cell changes sag, mass, and the charge window. Not a pass.

Pi. The share uses the board at $19.60, already counted as United Kingdom or Japan. No US-made board was opened that runs this software, this CSI camera, and this GPIO map. Not a pass.

Camera. Raspberry Pi Camera Module 3, $29.25, on the CSI cable in the harness. No US-made module with that connector was opened. Not a pass.

IMU. Adafruit BNO055 breakout, $34.95, I2C, fused orientation. No US-made BNO055 board with a manufacture sentence was opened. Another IMU on another bus drops the current reader. Not a pass.

BMS. Tenergy 2S board, $22.99, 10 A working, 22 A cutoff on the order note. The walking pack is 3S. A US-made 2S board would still be the wrong series count. No US 3S board was opened. Not a pass. The 3S protection part stays the open design item it already is.

PA6-CF. Incorporated $5.34 on the gram fraction. The shin numbers that matter are already cited in `twin/structure/shin_eye/SHIN_EYE.md`: 102 MPa in X-Y, 48 MPa in Z, modulus 4430 MPa. No US-made PA6-CF page was opened that prints all three at or above those figures. A weaker nylon misses the shin. Not a pass.

TPU. Overture 95A, $21.59 for the spool the share counts. Nozzle 210 C to 240 C (BOM.md line 28). No US-compounded 95A page with shore, nozzle, and a price was opened. A softer shore changes the soles and the sit pads. Not a pass.

Wire. Four silicone reels, $19.98, $16.98, $15.98, and $12.48. Calmont publishes silicone cable, including a high-temperature construction, at https://www.calmont.com/resources/silicone/ . No priced 16, 20, 22, or 26 AWG reel with a matching strand, a 200 C class, and a country sentence was opened. Not a pass.

The remaining priced component lines are in the table and in the CSV. For each of them, no US datasheet and no country-of-origin sentence for an equivalent were opened. They stay unknown origin, counted foreign. They are not passes. That includes the microSD, the touch boards, the HellermannTyton mounts, the fuse holders, the speaker, the time-of-flight board, the microphones, the heat-shrink kit, the foot switches, the pushbutton, the fasteners, the passives, and the connectors. The Pololu switch and the two ideal diodes are in that set, for the reason in the BEC section.

Ten component lines have no incorporated price: solder, threadlocker, charger-board assembly, charger-board fabrication, the KK housings, the M2x12 screw, the WAGO splices, the pack weld materials, the five gold wells, and the duck-side ideal-diode paths. They are not in the 5.23 percent. If they are foreign once priced, the gap is wider. If they are domestic, they help only by their incorporated cost, which is BLOCKER. No priced US substitute was opened for them.

Tools, the nest, the controller, and process aids are not components of the walking duck on the worksheet. They are in the CSV as not in the share. They are not a path to 65 percent.

## Every component line

Dollar order. The sentence for each row is in `US_PARTS.csv`. Incorporated dollars are the worksheet figures (cited there, calc only in the sums).

| Line | Incorporated $ | Result | US candidate | Delta $ |
| --- | ---: | --- | --- | ---: |
| servo | 288.82 | fail | none |  |
| bec | 54.95 | fail | Pololu D42V110F12, rejected |  |
| pla | 35.98 | pass | 3DXTech ECOMAX PLA, two 1 kg spools | 36.02 |
| imu | 34.95 | fail | none |  |
| reg5 | 29.95 | already_domestic | current part |  |
| cam | 29.25 | fail | none |  |
| cell | 26.97 | fail | none |  |
| bms | 22.99 | fail | none |  |
| tpu | 21.59 | fail | none |  |
| sd | 21.49 | fail | none |  |
| wire16 | 19.98 | fail | none |  |
| pi | 19.60 | fail | none |  |
| mounts | 17.38 | already_domestic | current part |  |
| wire22 | 16.98 | fail | none |  |
| wire26 | 15.98 | fail | none |  |
| touch | 15.90 | fail | none |  |
| mount | 15.66 | fail | none |  |
| holder | 15.48 | fail | none |  |
| tof | 14.95 | fail | none |  |
| speaker | 14.82 | fail | none |  |
| mic | 13.90 | fail | none |  |
| shrink | 12.99 | fail | none |  |
| wire20 | 12.48 | fail | none |  |
| foot | 11.76 | fail | none |  |
| button | 10.37 | fail | none |  |
| reflector | 9.15 | fail | none |  |
| sw | 8.95 | fail | none |  |
| amp | 7.50 | fail | none |  |
| kk-term | 5.88 | fail | none |  |
| tie | 5.63 | fail | none |  |
| pa6 | 5.34 | fail | none |  |
| fs16 | 5.23 | fail | none |  |
| vhb | 4.99 | fail | none |  |
| waveshare | 4.99 | fail | none |  |
| dk7 | 4.95 | fail | none |  |
| ntc | 4.00 | fail | none |  |
| sg90 | 4.00 | fail | none |  |
| dk6 | 3.79 | fail | none |  |
| usb | 3.50 | fail | none |  |
| spoxt | 3.06 | fail | none |  |
| fs17d | 2.99 | fail | none |  |
| camcable | 2.94 | fail | none |  |
| mcp | 2.41 | fail | none |  |
| bearing | 2.32 | fail | none |  |
| led | 2.07 | fail | none |  |
| xt30 | 1.72 | fail | none |  |
| fs17e | 1.40 | fail | none |  |
| fs17a | 1.20 | fail | none |  |
| fs17f | 1.17 | fail | none |  |
| spoxh | 0.98 | fail | none |  |
| fs17j | 0.90 | fail | none |  |
| fs17h | 0.76 | fail | none |  |
| fs17b | 0.72 | fail | none |  |
| caps | 0.58 | fail | none |  |
| fs17l | 0.56 | fail | none |  |
| smaj | 0.51 | fail | none |  |
| dmp | 0.44 | fail | none |  |
| fuse15 | 0.44 | fail | none |  |
| fuse5 | 0.44 | fail | none |  |
| foil | 0.40 | fail | none |  |
| fs17i | 0.40 | fail | none |  |
| diode | 0.36 | fail | none |  |
| fs17g | 0.36 | fail | none |  |
| cqen | 0.35 | fail | none |  |
| glass | 0.30 | fail | none |  |
| cu3 | 0.29 | fail | none |  |
| cu2 | 0.26 | fail | none |  |
| fs17k | 0.24 | fail | none |  |
| r100 | 0.23 | fail | none |  |
| zener | 0.17 | fail | none |  |
| fs17c | 0.12 | fail | none |  |
| rhotb | 0.11 | fail | none |  |
| rka | 0.11 | fail | none |  |
| crprog | 0.10 | fail | none |  |
| rbias | 0.10 | fail | none |  |
| rcold | 0.10 | fail | none |  |
| rcoldb | 0.10 | fail | none |  |
| rg | 0.10 | fail | none |  |
| rhot | 0.10 | fail | none |  |
| rpu | 0.10 | fail | none |  |
| rser | 0.10 | fail | none |  |
| rstat | 0.10 | fail | none |  |
| r2k2 | 0.06 | fail | none |  |
| kapton | 0.02 | fail | none |  |
| asm | BLOCKER | unpriced |  |  |
| fs17m | BLOCKER | unpriced |  |  |
| kk-h | BLOCKER | unpriced |  |  |
| loctite | BLOCKER | unpriced |  |  |
| pcb | BLOCKER | unpriced |  |  |
| solder | BLOCKER | unpriced |  |  |
| wago | BLOCKER | unpriced |  |  |
| weld | BLOCKER | unpriced |  |  |
| well-route | BLOCKER | unpriced |  |  |
| wells | BLOCKER | unpriced |  |  |

## The three scenarios

All figures in this section are calc only, from `us_parts_share.py`, except the PLA unit price and the current share inputs, which are cited above. Per-duck parts stay $957.75 in every scenario, because the only passing swap is a filament spool and the order keeps full spools out of that total.

All passing swaps. One line, the PLA. Domestic $119.33. Foreign $822.05. Share basis $941.38. Share 12.68 percent. That does not exceed 65 percent, and it does not exceed 75 percent. Buy-today cart if the two Overture spools were replaced and nothing else moved: $1240.28, which is $1204.26 minus $35.98 plus $72.00. The order is not changed.

Cheapest set that clears 65 percent. There is no such set. The only passing swap does not clear 65 percent, and there is no cheaper passing swap to add.

Cheapest set that clears 75 percent. There is no such set.

Where 65 percent cannot be met at any price. The servo cannot. No US part that was opened meets the torque, the speed, the size, and the bus, at any price. The same is true of every failed line: there is no catalog price at which a failed line becomes a pass, because the missing part was not a price problem. It was a spec or an origin problem.

Arithmetic, not a sourcing plan. If the two PLA spools, the one passing line, were invoiced at more than $1479.33 together, the share would exceed 65 percent while every failed line stayed foreign. At $1479.33 the share does not exceed 65 percent. At $1479.34 it does. The first total that prints as 65.01 percent at two decimal places is $1480.00. For 75 percent the same pair has to exceed $2418.82. At $2418.82 the share is 75 percent, which the rule does not treat as enough. At $2418.83 it exceeds 75 percent. No spool at those prices was listed. This study does not use a higher filament price as a way through the test. A lawyer would also have to accept the invoice as a real component cost.

A second counterfactual, also not this study's result. If every priced foreign line except the servos were domestic at today's prices, domestic would be $616.54 of $905.36, which is 68.10 percent. That exceeds 65 percent and does not exceed 75 percent. Clearing 75 percent on that fantasy would take more than $249.92 of extra domestic component cost. At $249.92 the share is 75 percent. At $249.93 it exceeds 75 percent. This study did not find those equivalents, so 68.10 percent is a ceiling that was not reached. The 2029 test is not met by any path that was opened.

## Follow-up, not this change

- Do not put a PWM servo, a Mini-Torxis, a ClearPath, or a Glentek motor on the duck. The case, the spline, the bus, the mass, and the torque curve all move, and run C would be trained again.
- Do not replace the Castle BEC with the 9 A Pololu. The rail current and the 3S sag do not fit.
- Do not change the selected PLA. A coupon and a re-slice are the follow-up if ECOMAX is ever ordered.
- Do not treat a US 2S protection board as the 3S pack.
- Do not reclassify a Pololu board that did not print the Las Vegas sentence.
- The wells, the duck-side diode paths, the charger fab, the weld, and the WAGO splices are still unpriced.

## What a lawyer still has to close

- Whether unknown origin in 48 CFR 25.003 is part of the FCC test. This study uses it, as the worksheet does.
- Whether a spool manufactured in Grand Rapids from resin the page does not place in the United States is a domestic component, or whether the resin is looked through.
- Whether "designed in Olathe" can ever count. This study does not count it.
- The first prong: where the finished duck would be manufactured.
- Freight, duty, and the unpriced lines.
- The iron or steel branch, which the worksheet already leaves open.
- The nest, if the nest and the duck are one article.

Sources for the test are the ones already cited in `altaay_lab/compliance/DOMESTIC_CONTENT.md`: the DA 26-786 text, the FCC FAQ, 48 CFR 25.101, and 48 CFR 25.003. Part pages opened for this study are linked in the sections above and in the CSV.
