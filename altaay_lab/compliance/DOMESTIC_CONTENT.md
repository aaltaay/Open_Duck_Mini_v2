# Domestic component share for one duck

This is not legal advice. A lawyer has to apply the test. Nothing was bought. No one was contacted. A sentence is quoted only from a page that was opened. A number is marked cited, calc only, or BLOCKER.

The walking duck is the end product in this worksheet. Tools, the controller, process aids, and the nest are not components of that article. Nest lines stay on the order. They are not in the share. If the duck and the nest are sold as one article, a lawyer adds the nest lines, and most of those lines have no price.

## What the test requires

DA 26-786, opened as text this session, accepts the definition and does not restate the arithmetic in the body. Cited from that text:

"We accept the National Security Determinations' definitions of "foreign-produced," "power inverters," and "advanced robotic devices," as provided in the Appendices below."

https://docs.fcc.gov/public/attachments/DA-26-786A1.txt

The appendix text is not in that text file. The FCC FAQ states the definition in words. The FAQ page was opened this session. It says it was updated Tuesday, October 27, 2026. Cited from the question "What constitutes "foreign-produced"? Is there a content threshold?":

"For the purposes of "foreign-produced advanced robotic devices," the term "foreign-produced" refers to any article that would not qualify as a "domestic end product," as that term is defined in 48 CFR § 25.101(a). The FCC's Covered List therefore tracks this language."

The same answer says the test has two prongs. Cited:

"The device must be "manufactured in the United States" and "the cost of domestic components shall exceed 65 percent for items delivered in calendar years 2024 through 2028 and 75 percent for items delivered starting in calendar year 2029.""

Cited from the same answer:

"Other provisions of the Buy America standard, such as the commercially available off-the-shelf exception to compliance with the standard, are inapplicable to whether a device is a "domestic end product" under section 25.101(a)."

A later question asks whether commercial-off-the-shelf components are left out of the calculation. Cited answer:

"No. If an advanced robotics device or power inverter includes COTS components, those components are still counted toward determining whether the device is "foreign-produced." All components, including COTS components, must be considered when determining whether article qualifies as a "domestic end product" under 48 § 25.101(a)."

https://www.fcc.gov/covered-list-faqs-robots-inverters

The rule the FAQ points at was opened this session. 48 CFR 25.101(a), current eCFR. The last Federal Register citation printed on that page is 89 FR 101831, December 16, 2024. Cited:

"(1) The article must be manufactured in the United States; and"

"(2)(i) Except for an end product that consists wholly or predominantly of iron or steel or a combination of both, the cost of domestic components shall exceed 60 percent of the cost of all the components, except that the percentage will be 65 percent for items delivered in calendar years 2024 through 2028 and 75 percent for items delivered starting in calendar year 2029."

The same paragraph then says the content test "has been waived for acquisitions of COTS items." The FAQ says that waiver is inapplicable to this Covered List test. The worksheet does not apply the waiver. The section uses "exceed," so 65 percent exactly is not enough.

https://www.ecfr.gov/current/title-48/section-25.101

The same section has a different content test for an end product that consists wholly or predominantly of iron or steel. The FAQ states the 65 and 75 percent test as the content prong for this list. It does not mention the iron or steel branch. "Predominantly of iron or steel" is defined in 48 CFR 25.003 as iron and steel content above 50 percent of component cost, and that definition excludes COTS fasteners from the iron and steel estimate. No iron or steel estimate for the servos was opened. BLOCKER for whether the iron or steel branch applies. The numbers below use the 65 and 75 percent test the FAQ states.

The words "component," "cost of components," and "United States" are defined in 48 CFR 25.003, opened this session. Cited:

"Component means an article, material, or supply incorporated directly into an end product or construction material."

"Cost of components means (1) For components purchased by the contractor, the acquisition cost, including transportation costs to the place of incorporation into the end product or construction material (whether or not such costs are paid to a domestic firm), and any applicable duty (whether or not a duty-free entry certificate is issued); or (2) For components manufactured by the contractor, all costs associated with the manufacture of the component, including transportation costs as described in paragraph (1) of this definition, plus allocable overhead costs, but excluding profit. Cost of components does not include any costs associated with the manufacture of the end product."

Cited from the domestic-end-product definition in the same section:

"Components of unknown origin are treated as foreign."

Cited:

"United States means the 50 States, the District of Columbia, and outlying areas."

https://www.ecfr.gov/current/title-48/section-25.003

25.003 also says an end product manufactured in the United States qualifies if it is a COTS item. The FAQ says that exception is inapplicable here. The worksheet follows the FAQ.

The FAQ does not repeat the unknown-origin sentence. This worksheet uses it because it is in the definition of the domestic end product in the same part as 25.101. A lawyer can decide that the FCC test does not import that sentence. The sensitivity further down shows that reading.

Assembly labor on the finished duck is a cost of manufacturing the end product. The definition excludes it from component cost. It does not satisfy the 65 percent prong. The first prong, manufacture in the United States, is separate. This repo does not name a factory for the finished duck. BLOCKER for that prong. The share below is only the content prong.

Transportation to the place of incorporation, and any duty that is not already in the seller's item price, are not in ORDER.csv or BOM.md. BLOCKER for those adders. The share uses item prices only. Shipping was excluded on the bill by the existing rule.

## How a dollar was assigned

Every line in bom/order/ORDER.csv is a row in compliance/DOMESTIC_ROWS.csv. compliance/domestic_share.py recomputes the sums from that row table.

A component is an article incorporated into the walking duck. The incorporated cost is the price times the quantity that stays in the duck, not the spare quantity and not a nest-only quantity. Pack math is calc only. Each cent is rounded half up, then the cents are added.

Where ORDER.csv has a unit price from 2026-11-12, that price is the price. Where that cell is empty, the price is the BOM.md line price recorded there, and the note says the page was not re-opened. Where neither file has a price, the row says BLOCKER and the dollar is not in the share.

Two purchased articles are not split. The solder spool is $9.25 in ORDER.csv (cited, out of stock). The threadlocker bottle is $9.90 in BOM.md line 19 (cited, not re-opened). The fraction left in the duck was not measured. Those two rows are BLOCKER for incorporated cost.

The Pi line in ORDER.csv is the CanaKit starter kit at $89.95 (cited, checked 2026-11-12). The kit includes a case, a supply, an HDMI adapter, and an OTG cable. Those are not incorporated. The component is the board. The CanaKit page opened this session prints the header board at $19.60 and sold out. The worksheet uses $19.60 (cited, this session). VOLUME.csv had printed $16.35 for the bare board and $87.95 for a kit on an earlier read the same day. The page this session shows the header kit at $99.95, sold out.

Origin:

- Pololu D30V30F5, $29.95 (cited, ORDER.csv). The product page opened this session says these boards are manufactured in-house at the Las Vegas facility. Domestic.
- Panduit ABM1M-AT-C, 24 fitted mounts, $17.38 (calc only, BOM.md line 34b price $72.41 per 100, cited from that file's 2026-11-02 Hisco read, not re-opened). That read printed country of origin US. Domestic.
- Feetech ST3215 C001, 14 servos, $280.00 (cited, ORDER.csv, $20.00 each). The Seeed page opened this session prints COO CHINA. Foreign.
- Raspberry Pi Zero 2 W, $19.60 (cited, this session). The CanaKit page prints Made in UK. Raspberry Pi PCN 21, opened this session, says all production moved from Sony in the United Kingdom to Sony Inazawa, Japan, in September 2023, with both in the channel during a transition. The United Kingdom and Japan are not the 50 States or the District of Columbia. Foreign either way. Which factory made the board in a given box was not read from a revision code. The box was not opened.

Every other priced component has no country-of-origin sentence on a page opened for this worksheet. Counted foreign under the 25.003 sentence above. "Ships from the United States" and a US seller's office are not that sentence. The Molicel sheet, opened this session, prints a Canada facility and a Taiwan facility and does not say which one makes the P45B. Neither address is a United States factory. The cell stays in the unknown group.

https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf

https://pip-assets.raspberrypi.com/categories/1163-pcn/documents/RP-004862-PC-1-PCN21,%20Raspberry%20Pi%20Zero%202%20W,%20Change%20of%20country%20of%20origin.pdf

## The share

Current share, 2026-11-12 9:41 PM ET, from compliance/domestic_share.py on the order after PR 77 and the third cell. Calc only. Not legal advice.

- Domestic: $47.33. The regulator is $29.95 and the 24 Panduit mounts are $17.38.
- Foreign, cited or unknown: $849.21.
- Total in the share: $896.54.
- Domestic share: 5.28 percent ($47.33 divided by $896.54).

A delivery in 2026 uses the 65 percent test. Domestic cost has to exceed 65 percent of $896.54, which is $582.75 (0.65 times $896.54). The sheet is short by $535.42. A delivery in 2029 uses 75 percent. That gap is $625.08. The smallest set that clears the 2026 gap is 10 lines and sums to $548.15. The earlier 6.07 percent, the $779.39 total, and the seven-line set below are superseded.

~~Priced components of the walking duck:~~

- ~~Domestic: $47.33 (calc only). The regulator is $29.95 and the 24 Panduit mounts are $17.38.~~
- ~~Foreign, cited or unknown: $732.06 (calc only).~~
- ~~Total in the share: $779.39 (calc only).~~
- ~~Domestic share: 6.07 percent (calc only, $47.33 divided by $779.39).~~

~~A delivery in 2026 uses the 65 percent test. Domestic cost has to exceed 65 percent of $779.39, which is $506.60 (calc only, 0.65 times $779.39). The sheet is short by $459.27 (calc only). A delivery in 2029 uses 75 percent. That gap is $537.21 (calc only).~~

Lines with no incorporated price are not in the $779.39. They are solder, threadlocker, the unwelded pack materials, the charger-board passives and the board fab, the KK 254 housings, the M2x12 screw, the five gold seat wells, and the duck-side ideal-diode path for each well. The wells sit in the seat and the diode paths sit in the trunk (FLUSH_CONTACTS.md section 6). Neither has a part or a price. If those lines are foreign, the gap is wider. If they are domestic, they help only to the extent of their incorporated cost, which is BLOCKER.

On a reading that refuses the unknown-origin sentence, the same script gives domestic $596.94 and foreign $299.60, which is 66.58 percent (calc only). That reading clears 65 percent by $14.19 (calc only). It is not the rule this worksheet uses. The servo line is still the 7.4 V part at $280.00. Swapping it for the 12 V servo would change this share and has not been done.

~~On the same $779.39 it would be domestic $479.79 and foreign $299.60, which is 61.56 percent (calc only). That reading is still short of 65 percent by $26.81 (calc only).~~ Superseded by the recompute above.

## Smallest set that crosses 65 percent

The rule used here counts unknown origin as foreign. Under that rule the smallest set of current lines whose incorporated cost exceeds the $459.27 gap is seven lines. The six largest foreign lines sum to $443.39 (calc only), which does not clear it.

| Line | What | Incorporated $ | Why it is in the foreign column |
| --- | --- | --- | --- |
| servo | 14 Feetech ST3215 | 280.00 | COO CHINA on the Seeed page |
| bec | Castle CC BEC Pro | 54.95 | No origin sentence opened. Unknown, counted foreign |
| imu | Adafruit BNO055 breakout | 34.95 | No origin sentence opened. Unknown, counted foreign |
| cam | Raspberry Pi Camera Module 3 | 29.25 | No origin sentence opened. Unknown, counted foreign |
| bms | Tenergy 2S protection board | 22.99 | No origin sentence opened. Unknown, counted foreign |
| sd | SanDisk Ultra 32 GB | 21.25 | BOM.md price, not re-opened. No origin sentence. Unknown, counted foreign |
| pla | Overture Easy PLA, 1346.71 g | 20.19 | BOM.md price, not re-opened. No origin sentence. Unknown, counted foreign |

Sum of these seven: $463.58 (calc only). That exceeds $459.27.

No page opened this session states a serial-bus servo of this size with country of origin United States and a printed price. ProModeler in Sanford, Florida, publishes the DS270DLHV at $54.99 (cited, https://www.promodeler.com/DS270DLHV, 270 oz-in, in stock). The About page says the company assembles servos and prints a Sanford address. It does not say the assembly is in the United States. That servo is a three-wire PWM servo, not the TTL bus on the STS3215. It is not used as a US-made alternative.

Glentek's own site, opened this session, says: "We manufacture our products in a multi-building complex in downtown El Segundo, California." A second page says: "All of our servo motors are made in-house, at our modern factory in El Segundo, California." The catalog that was opened gives a continuous-torque range for the GMB series of 2.4 lb-in to 1,092 lb-in (cited). 19 kg-cm is inside that range. The catalog and the motor pages that were opened do not print a motor price. Buyers are told to send a purchase order. No order was sent. The per-duck price of a Glentek motor is BLOCKER. The motor is not the STS3215 shape or the STS3215 bus. Fit is BLOCKER.

https://www.glentek.com/

https://www.glentek.com/mti-torque-systems/

Arithmetic only, if the 14 servos were replaced and every other line stayed as classified: the replacement clears the 65 percent test on this priced set when each actuator costs $56.59 or more (calc only). At $56.58 each, the share does not exceed 65 percent. Fourteen at $56.59 is $792.26, which is $512.26 above the $280 servo line (calc only). That is the threshold, not a quoted price.

The smaller purchase change is not a new motor. It is a US-made subassembly. 48 CFR 25.003 counts the whole acquisition cost of a purchased component, or the whole manufacture cost of a component the builder makes, excluding profit. It does not look through a domestic component to the foreign articles inside it, on the words that were read. Cost of making the end product is excluded. If the seven lines above, $463.58, are incorporated into components that are themselves manufactured in the United States, those dollars leave the foreign column. The part purchase does not change. The added cost is the US cost of manufacturing those components, excluding profit. That cost was not on a page. BLOCKER. Any such cost, if a lawyer counts it as component manufacture rather than end-product assembly, raises the domestic share further. A lawyer has to decide whether building those modules in the United States is "manufactured in the United States" for a component, or only assembly of the duck.

For a 2029 delivery the gap is $537.21 (calc only). The same sort, largest foreign line first, then needs twelve lines and sums to $548.20 (calc only): the seven above, plus the Pi at $19.60, the two cells at $17.98, the two touch boards at $15.90, the HellermannTyton mounts at $15.66, and the two fuse holders at $15.48.

The first prong is still open. None of these swaps, by themselves, show that the finished duck is manufactured in the United States.

## What a lawyer still has to close

- Whether the unknown-origin sentence in 48 CFR 25.003 is part of the FCC test. This worksheet uses it. The FAQ does not repeat it.
- Whether the iron or steel branch applies. No steel estimate was opened.
- Where the finished duck would be manufactured.
- Freight and duty on top of the item prices.
- Incorporated cost of the solder, the threadlocker, the pack build, the charger passives, the charger board, the KK housings, the M2x12 screw, the five seat wells, and the duck-side ideal-diode paths.
- Whether a US-built module that contains the seven lines is a domestic component, or only end-product assembly.
- A printed price, a fit, and a bus match for a motor made in the United States, if the path is a bought actuator instead of a subassembly.
- The nest, if the lawyer treats the nest and the duck as one article.

Sources for the test: the DA 26-786 text link above, the FAQ link above, https://www.ecfr.gov/current/title-48/section-25.101 , and https://www.ecfr.gov/current/title-48/section-25.003 . Line dollars and origin sentences are in DOMESTIC_ROWS.csv.
