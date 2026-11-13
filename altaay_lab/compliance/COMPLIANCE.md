# Selling the duck in the United States

This is not legal advice. It is a research note. Nothing was bought. Nothing was sent to a lab or to an agency. A rule is cited only where a public page was opened on 2026-11-12, or where COMPLIANCE_FIRST_PASS.md already records that the page was opened. A number is marked cited or calc only. Where a number was not opened, the line says BLOCKER.

The duck is the home machine in this repo: a walking body, a camera, Wi-Fi and Bluetooth on the Pi, a 2S lithium pack, and a felt charging nest. COMPLIANCE_FIRST_PASS.md still holds for the open contacts, the charger heat, and the homemade pack. This file adds the restricted-party check and the rules that attach if the duck is sold. The 2026-07-28 Covered List notice is quoted in compliance/FCC_COVERED_ROBOT.md.

PARTS_CHECK.csv is one row per bill line, plus the nest parts that are not on the bill. Test-order rows buy the same makers. They are not a second set.

## Result of the list check

No named maker on the bill, and no named nest maker, is a record on the party lists below. The finding that can stop a sale is not a supplier record. It is the finished duck. If the duck is foreign-produced, the FCC Covered List category added on 2026-07-28 covers a walking machine of this kind, and 47 CFR 2.903 then bars the radio authorization.

Lists read on 2026-11-12:

- OFAC SDN file sdn.csv, and the alt-name file, from https://www.treasury.gov/ofac/downloads/sdn.csv
- Consolidated Screening List file consolidated.csv from https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv . Counted from that file: 26265 rows. Counted from the Military End User source inside it: 70 rows.
- UFLPA Entity List, https://www.dhs.gov/uflpa-entity-list . The page says last updated 2026-10-28.
- FCC Covered List public notice DA 26-786, released 2026-07-28, including the definitions in Appendix B and Appendix C. https://docs.fcc.gov/public/attachments/DA-26-786A1.pdf
- NDAA section 889 names in 48 CFR 4.2101, eCFR display date 2026-11-10.

Names were matched as whole words. These collisions were rejected because they are different parties: Russian Arzamas records (the letters sit inside that name) on the Entity List and the SDN list; Design Partner Microchip LLC on the SDN list; AO NKK on the SDN list; a person named Samuel Knowles on the SDN list; an SDN alias LA WERA, which is a person. Sellers Seeed and OpenELAB were screened as those strings. No hit.

Marketplace brands were screened as the brand string. The legal company name was not opened for Feetech, Waveshare, Adeept, Amass, Miuzei, Overture, BNTECHGO, uxcell, FINGERINSPIRE, Aurorad, Wirefy, METALLIXITY, and Motoforti. A parent under another name would not have been found. BLOCKER for a finished screen of those brands.

Lines with no maker to screen: the pack build (line 7), the unsourced M2x12 screw (line 17m), the replaced slide switch (line 10b-old), the felt, the conductive cloth, and the nest gate board. BLOCKER, not a clear.

## 1. Restricted components and suppliers

### OFAC specially designated nationals

Applies: yes, to a deal by a US person. A hit bars the purchase.

Why the names fail to hit: the screened strings are not on the SDN file that was downloaded.

Must do: screen the legal name again on the day of the purchase order. The file moves.

Cost and time: BLOCKER. No fee page was opened.

Source: https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists

### BIS Entity List

Applies: 15 CFR 744.16, opened, eCFR as of 2026-11-10. Without a license you may not export, reexport, or transfer items subject to the Export Administration Regulations to a listed party. The section is about sending items to them. It is not, by itself, a ban on buying a commercial part inside the United States. A hit would still be flagged here.

Result: no hit.

Must do: do not ship the duck, and do not ship design files that are technology subject to those regulations, to a listed party. No supplier screened today is listed.

Source: https://www.ecfr.gov/current/title-15/section-744.16

### BIS Military End User list

Applies: 15 CFR 744.21, opened. You may not export, reexport, or transfer the items the section covers if you know they are for a military end use, or a military end user, in the countries that section names. The Military End User list is supplement no. 7. A household sale inside the United States is not that export.

Result: none of the screened makers is among the 70 Military End User names counted in the downloaded file.

Must do: if a duck is shipped abroad, check the end user before it goes.

Source: https://www.ecfr.gov/current/title-15/section-744.21

### FCC Covered List, as a list of companies

Applies: 47 CFR 2.903, opened. Equipment on the Covered List cannot get a certification, a Supplier's Declaration of Conformity, or an exemption.

The named producers on DA 26-786 Appendix A include Huawei, ZTE, Hytera, Hangzhou Hikvision, Dahua, and Kaspersky, plus the named telephone companies (China Mobile, China Telecom, Pacific Networks and ComNet, China Unicom, and Digitalsystem Technology). The list note says subsidiaries and affiliates are included.

Result: none of those names is a maker on the bill. The camera is the Raspberry Pi camera, not a Hikvision or Dahua camera.

The same list has categories that are not a company. The robot category is in section 2 of this file, because it can cover the duck itself.

Source: https://docs.fcc.gov/public/attachments/DA-26-786A1.pdf and https://www.fcc.gov/supplychain/coveredlist

### NDAA section 889

Applies: if the seller is a federal contractor, or the buyer is the US government. It does not, by itself, ban a household sale. 48 CFR 4.2101, opened, defines covered telecommunications equipment as equipment from Huawei or ZTE, and, for the security uses it lists, from Hytera, Hikvision, or Dahua, plus affiliates.

Result: no part on the bill is that equipment.

Must do: do not add those brands. If a federal contract is ever signed, flow the contract clause down. The clause text was not read line by line.

Source: https://www.ecfr.gov/current/title-48/section-4.2101

### UFLPA forced-labor entity list

Applies: yes, to imports. Goods mined, produced, or manufactured wholly or in part in Xinjiang, or by an entity on the UFLPA Entity List, are presumed barred. Public Law 117-78.

Result for named makers: the screened names, including Molicel and Feetech, are not on the page that was read. The page does list other firms in lithium and battery materials. The names read there include SDIC Xinjiang Lithium Industry Co., Ltd. (effective 2026-08-03), Shihezi Xinren Battery Aluminum Foil Technology Co., Ltd. (effective 2026-08-03), and Jiangyin Xinren Aluminum Foil Technology Co., Ltd. (effective 2026-08-03). Many cotton firms are on the same page.

Must do: before the cells are imported, trace the lithium, the graphite, the foil, and the other materials to a source that is not Xinjiang and not a listed entity. The cell sheet does not do that. The felt has no maker. If the felt is cotton, the cotton entities apply in the same way. The sleeve on line 7 has no maker.

Cost and time: BLOCKER.

Source: https://www.dhs.gov/uflpa-entity-list and https://www.govinfo.gov/app/details/PLAW-117publ78

### Section 301 tariffs, HTS codes, and the small-parcel exemption

Applies: yes, when the article's country of origin is China and its HTS code is on a Section 301 list. Origin is where the article is made, not the brand, and not the country the box happens to ship from.

What was opened: the USTR notice of 2024-09-18 discusses HTS subheading 8507.60.0020 (lithium-ion batteries, other) and an increase in 2026. https://www.federalregister.gov/documents/2024/09/18/2024-21217/notice-of-modification-chinas-acts-policies-and-practices-related-to-technology-transfer

The P45B sheet, version 1.2, prints a Taiwan facility in Tainan. That is not a customs ruling. If the invoice origin is Taiwan, the China Section 301 list is not the duty that applies to those cells. The invoice origin was not opened. BLOCKER.

The rate in the current HTS chapter 99 was not opened. BLOCKER.

No other HTS code was opened. This file does not assign a code to the servos, the Pi, the camera, the filament, the connectors, or the finished duck. A broker classifies them. BLOCKER.

De minimis: 19 USC 1321 is the statute. On 2026-06-24 the Federal Register published an indefinite suspension of that exemption for merchandise other than international mail, and companion notices for mail. The search text of those notices says Executive Order 14324 had already suspended the exemption for most importations in 2025, and the June 2026 rules write the suspension into the customs regulations. The dollar cap in the statute is not copied here. The rule PDF was not read line by line, so any leftover exception is BLOCKER. Do not plan on a small parcel from abroad entering free of duty.

Must do: get origin and an HTS class from a broker before the first import of parts or of a finished duck.

Sources: the USTR notice linked above, https://www.govinfo.gov/link/uscode/19/1321 , and https://www.federalregister.gov/documents/2026/06/24/2026-12670/indefinite-suspension-of-the-de-minimis-exemption-for-merchandise-arriving-through-all-modes-other

## 2. FCC Part 15, and the robot category on the Covered List

### The category that can stop a sale

Applies: yes, if the duck is a foreign-produced advanced robotic device and the Department of War has not given a conditional approval for it.

DA 26-786 Appendix C (determination dated 2026-07-27) defines an advanced robotic device as a mechanical mobile device that does all of the following:

- It can move on the ground.
- It operates at a distance from a person, on commands or on sensor data.
- The device, plus the dock if it has one, weighs over 4.4 lb (cited, from the determination page).
- It has a sensor, and a network link of at least 200 kbps in either direction (cited), and the definition names Wi-Fi and Bluetooth, and it has software that controls navigation, perception, data collection, or remote command.

The definition does not include a connected vehicle, a rail vehicle, an uncrewed aircraft, an underwater vehicle, an FDA device (the page includes wheelchairs), or a fixed industrial arm.

On the papers already in the lab, the duck walks, it takes commands from the controller, and it runs a walk policy from sensors. sim/MASS_BUDGET.md gives Our build as 2.81 kg. That figure is a model, not a scale reading. 2.81 times 2.2046 is 6.19 lb (calc only, rounded to two decimals). 4.4 divided by 2.2046 is 2.00 kg (calc only, rounded to two decimals). The model is over the 4.4 lb line. The duck has a camera and an IMU. The Pi Zero 2 W brief, opened this session, says 2.4 GHz 802.11 b/g/n, Bluetooth 4.2, BLE, and modular compliance certification. The definition names Wi-Fi and Bluetooth. No line read in the brief states a cap under 200 kbps. The duck is not in the exclusion list that was read.

Foreign-produced, in that appendix, means the article would not qualify as a domestic end product under 48 CFR 25.101(a). That section, eCFR as of 2026-11-10, uses two parts for a manufactured product that is not mostly iron or steel: it is made in the United States, and the cost of domestic components exceeds 65 percent of the cost of all components for items delivered in calendar years 2024 through 2028 (cited). The percentage is 75 percent for items delivered starting in calendar year 2029 (cited). The same paragraph waives the content test for government purchases of COTS items. The FCC FAQ on this list, opened for DOMESTIC_CONTENT.md, says that off-the-shelf exception is inapplicable, and that off-the-shelf components are still counted. The worksheet follows the FAQ.

DOMESTIC_CONTENT.md is the content worksheet. On the priced components, domestic cost is $47.33 and the total is $779.39, which is 6.07 percent (calc only, in that file). That is under the 65 percent test. Lines with no incorporated price are BLOCKER and are not in that total. Until a lawyer accepts a worksheet that clears both prongs, treat the duck as foreign-produced for this list.

47 CFR 2.903 says covered equipment cannot get a certification, a Supplier's Declaration of Conformity, or an exemption. A covered duck cannot be marketed with its radio.

A footnote on the Covered List says a category entry covers only equipment that can do what 47 USC 1601(b)(2) describes. That statute section was not read line by line. BLOCKER for whether the footnote takes a home robot off the list. Do not sell on that hope. The uncrewed-aircraft entry has a toy exception. The robot entry, as read, does not.

Must do, before any sale that includes the radio. Pick one:

1. Show, with a worksheet, that the duck is a domestic end product under 48 CFR 25.101(a), including manufacture in the United States, or
2. Obtain a Department of War conditional approval for this duck or its class. The notice says the request uses the Advanced Robotic Devices Guidance Document. That guidance was not opened. BLOCKER for the form, the fee, and the time, or
3. Change the design so the definition does not fit. This file does not make that change.

Power inverters are a separate line in the same notice. Appendix B defines a power inverter as a device that converts direct current to alternating current, or alternating current to direct current, of the micro, string, central, or hybrid kind, and that has a Wi-Fi, cellular, Bluetooth, or similar link. The duck's Pololu and Castle regulators are direct-current to direct-current. The wall adapters on the bill are not described as networked. Not a hit on the text that was opened. Re-check a later supply if it is a networked inverter.

Foreign-produced routers are their own Covered List line, dated 2026-03-23. The router definition was not opened. Do not set the duck up to route traffic for other devices until that definition is read. BLOCKER if that feature is added.

### Part 15, if the duck is not covered equipment

Applies: yes, to the radio and to the digital circuits, once the Covered List does not bar the authorization.

Modular transmitters: 47 CFR 15.212 was opened for COMPLIANCE_FIRST_PASS.md. A certified module may be built into a host when that section's conditions are met. If the module's own FCC id is not visible, the outside of the product has to say that it contains the module. The Pi brief claims modular compliance certification. The grant was not opened. The FCC id was not in the brief lines read this session. Whether the grant is a full modular grant, and whether this closed body is inside it, is BLOCKER. One brief line that was read says the board should be operated in a well-ventilated environment, and, if used inside a case, the case should not (the rest of that sentence was cut off in the extract). COMPLIANCE_FIRST_PASS.md has the case limits taken from the same brief. Do not call the duck certified because the board is.

Unintentional radiators: 47 CFR 15.101, opened. Before marketing, a Class B digital device needs a Supplier's Declaration of Conformity or a certification. The camera brief, opened this session, shows Part 15, Subpart B, Class B. PARTS_AUDIT.md already recorded that the same brief marks that class under FCC. That claim is for the camera as sold, not for the duck. The finished duck still needs its own declaration or certification as a digital device.

Declaration paperwork: 47 CFR 2.1077, opened. The statement that ships with the product names the product, says it complies, and names a responsible party located in the United States, with an address and a telephone number or an internet contact.

Label: 47 CFR 15.19(a)(3), opened. The device carries the two conditions: it may not cause harmful interference, and it must accept interference. If the device is too small for a four-point font and has no screen, 15.19(a)(5) allows the statement in the manual and on the package or a removable label.

Must do: open the Pi grant and read the id, the modular type, and the host limits. Keep the printed antenna. Do not add another antenna. Put the outside label on, name a US responsible party, and have the finished duck tested as an unintentional radiator before a sale. Confirm the radio still matches the grant. Cost and time of that test: BLOCKER.

Sources: https://www.ecfr.gov/current/title-47/section-15.212 , https://www.ecfr.gov/current/title-47/section-15.101 , https://www.ecfr.gov/current/title-47/section-15.19 , https://www.ecfr.gov/current/title-47/section-2.903 , https://www.ecfr.gov/current/title-47/section-2.1077 , the Pi brief cited in PARTS_AUDIT.md, and https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf

## 3. The battery and the charger

Applies: yes. The pack is two cells, spot welded, and it would ship inside the duck.

49 CFR 173.185(a), opened, eCFR as of 2026-11-10: each lithium cell or battery must be of a type proven to meet part III, subsection 38.3 of the UN Manual of Tests and Criteria. Cells and batteries are subject to these tests regardless of whether the cells used to construct the battery are of a tested type. A pack welded from tested cells is still a battery. It needs its own type proof. The P45B sheet opened this session does not mention UN 38.3.

The same section requires a test summary, with the maker, the lab, a report number, the date, the mass, the watt-hour rating, the model, and the pass or fail list. The elements were read. For a pack built in the lab, the builder is the one who has to have that summary.

Paragraph (c), opened, sets a size cap for the smaller-battery provision: the watt-hour rating may not exceed 20 Wh for a lithium ion cell or 100 Wh for a lithium ion battery (cited). The sheet gives nominal voltage 3.6 V and typical capacity 4500 mAh (cited). 4.5 times 3.6 is 16.2 Wh for one cell (calc only). Two cells in series, 7.2 times 4.5, is 32.4 Wh for the pack (calc only). Both sit under the caps that were read. The rest of paragraph (c), including packing, marks, and air, was not read line by line. BLOCKER for a shipping procedure. The section also says a lithium ion battery subject to that provision must be marked with the watt-hour rating on the outside case. The number on the case should be the rating on the test summary.

UL 2054 and IEC 62133 were not opened. They were not found as a duty in the CFR sections that were opened. A retailer may still ask. BLOCKER for a legal duty, and for the fee.

Must do: do not ship a welded pack, and do not sell the duck with that pack, until the pack as built has a UN 38.3 test summary, or the duck uses a pack that already has one. Mark the case with the watt-hour rating if the smaller-battery provision is the path used.

The wall adapter should be a finished supply. Whether the adapters on the bill carry a US safety mark was not read this session. BLOCKER. UL 62368-1 was not opened. It is a standard, not a statute found in the pages opened. The in-duck charger named in the nest note is the Microchip MCP73213. Its datasheet was not opened (PARTS_AUDIT.md). Heat in the body remains the BLOCKER already written in COMPLIANCE_FIRST_PASS.md. This file does not move the charger.

Sources: https://www.ecfr.gov/current/title-49/section-173.185 , the cell sheet https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf , and the PHMSA page already cited in COMPLIANCE_FIRST_PASS.md, https://www.phmsa.dot.gov/training/hazmat/new-un-requirement-test-summaries

## 4. Product safety

### Children's products

Applies: the children's rules apply if the duck is designed or intended primarily for children 12 and under. That is 15 USC 2052. The section was not read line by line this session. COMPLIANCE_FIRST_PASS.md says not to add a toy claim. That note is not a decision by the CPSC. Ads, the box, and the way the product is recognized can still make it a children's product.

If it is a toy, 16 CFR 1250.2, opened, says each toy must comply with ASTM F963-23, with the carve-outs that section lists. 16 CFR 1307.3, opened, bars a children's toy or child care article with more than 0.1 percent (cited) of the phthalates that section names. The sleeve on line 7 has no maker, so its phthalate content is BLOCKER if the duck is sold as a toy. Lead limits for children's products were not read line by line. The solder on the bill is tin-lead. If the duck could be found to be a children's product, use the lead-free solder already named on that bill line.

Small parts: 16 CFR 1501.2, opened, applies to toys and other articles intended for children under 3 years, not to every object in a house. Tracking labels apply to children's products. That section was not read line by line. BLOCKER for the exact mark if a children's product is ever the plan.

Must do: keep the ads, the box, and the age grade as a home product for adults. Do not aim it at children under 12. Revisit this before any child-directed claim. The cost of a toy test: BLOCKER.

Sources: https://www.ecfr.gov/current/title-16/section-1250.2 , https://www.ecfr.gov/current/title-16/section-1307.3 , https://www.ecfr.gov/current/title-16/section-1501.2

### Reese's Law

Applies: no, for the duck as billed. 16 CFR 1263.1, opened, covers a consumer product that contains a button cell or a coin battery. No coin cell is on a duck line. The calipers on the test-gear list use a coin cell. They are not the product. If a later part adds a coin cell, this becomes yes, including the warnings on the package. The toy exemption in that section only helps a toy that already meets 16 CFR 1250.

Source: https://www.ecfr.gov/current/title-16/section-1263.1

### Other safety marks

UL 62368-1, IEC 62368-1, and ISO 13482 (personal care robots) were not opened. They are standards. No US statute found in the pages opened makes them a mandate for this duck. ISO 13482 is a reference only. Cost and time: BLOCKER.

The open contacts on the nest are already written in COMPLIANCE_FIRST_PASS.md. No charging-mat standard was opened then, and none was opened now. BLOCKER. If a sale rule says those contacts have to be inaccessible, the open cloth cannot stay as drawn. This file does not redraw it.

Reporting: 15 USC 2064 is the duty to tell the CPSC when a product is a substantial hazard. The section was not read line by line. The time limit is BLOCKER until it is read. Source: https://www.govinfo.gov/link/uscode/15/2064

## 5. Privacy

### COPPA

Applies: if the duck or the service is directed to children under 13, or the operator has actual knowledge that it is collecting personal information from a child. 16 CFR part 312 was not read section by section this session. The current plan is a home companion, not a children's service. That plan is not a finding that the rule can never apply.

Must do: no accounts for children, no ads aimed at children, and a written rule for the day the operator learns a child is the user. If a children's mode is added, stop and build verifiable parental consent first.

Source: https://www.ecfr.gov/current/title-16/part-312

### FTC Act section 5

Applies: yes. 15 USC 45 bars unfair or deceptive acts in commerce. The section was not read line by line. A home camera that records when the notice says it does not, or that stays on with no cue, is the kind of fact this statute is used for. No court opinion was opened, so this file states no case result.

Must do: the privacy notice has to match the software. COMPLIANCE_FIRST_PASS.md already asks for a light or a sound when the camera is on. No upload by default. Finding the nest should not require keeping the pictures. No face library.

Source: https://www.govinfo.gov/link/uscode/15/45

### Texas Data Privacy and Security Act

Applies: if the seller does business in Texas, or produces a product consumed by Texas residents, and processes personal data. The Attorney General's page, opened, says the act is Business and Commerce Code chapter 541, effective 2024-07-01. Small businesses, as the Small Business Administration defines them, are generally exempt, except that selling sensitive data needs the consumer's consent first. On that page, sensitive data includes biometric data processed to uniquely identify a person, and personal data of a child under 13. The same page says biometric data does not include a photograph, a video, or an audio recording, or data generated from that recording.

Must do: if the seller is not a small business, publish a privacy notice, give a way to ask for access, correction, and deletion, answer within 45 days (cited), with one extra 45 days when the reason is sent inside the first 45 (cited), get consent before processing sensitive data, and keep reasonable security. If the seller is a small business, do not sell sensitive data without consent. The page gives 30 days to cure after notice (cited). It also states a civil penalty per violation. The dollar amount is not copied here.

A camera picture, on that definition, is not biometric data. A face measurement used to identify a person is.

Source: https://www.texasattorneygeneral.gov/consumer-protection/file-consumer-complaint/consumer-privacy-rights/texas-data-privacy-and-security-act

### Texas biometric identifier law

Applies: if the duck captures a biometric identifier for a commercial purpose. The Attorney General's page defines a biometric identifier as a retina or iris scan, a fingerprint, a voiceprint, or a record of hand or face geometry.

Must do: do not add face recognition, and do not keep a voiceprint, unless notice and consent come first and the record is deleted on the statute's schedule. The statute was not read line by line. The deletion schedule is BLOCKER until it is read. The page states a civil penalty per violation. The dollar amount is not copied here.

Source: https://www.texasattorneygeneral.gov/consumer-protection/file-consumer-complaint/consumer-privacy-rights/biometric-identifier-act

## 6. Environmental rules

### California Proposition 65

Applies: yes, to a knowing and intentional exposure in California to a listed chemical, unless a safe harbor or another exception covers it. The safe-harbor page was found. The lead number on that page was not opened. BLOCKER for whether this duck needs a warning.

The solder on the bill is tin-lead. Lead is the chemical to check. A lead-free spool is already named on that same bill line.

Must do: use the lead-free solder for a duck that could be sold in California, or finish an exposure assessment first. The sleeve, the felt, and the filament were not tested for listed chemicals. BLOCKER.

Sources: https://oehha.ca.gov/proposition-65/general-info/current-proposition-65-no-significant-risk-levels-nsrls-maximum and https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=HSC&division=20.&title=&part=&chapter=6.6.

### Battery take-back

Applies: maybe. The official code search returns California Public Resources Code 42463. A covered battery-embedded product, in that return, is a product whose battery is not designed to be removed by the user with no more than common household tools. The pack sits behind screws. Whether that counts as easy removal was not decided on a CalRecycle page. BLOCKER for yes or no. If the duck is covered, the producer has duties under the state electronics recycling law as amended by SB 1215. The fee and the start date were not opened. BLOCKER.

Source: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PRC&sectionNum=42463

### State rules that resemble RoHS

A federal copy of the EU RoHS rule was not found in the pages opened. California's rule for covered electronic devices was not opened. BLOCKER for whether this duck is one of those devices. State rules that limit heavy metals in packaging were not opened. BLOCKER for the shipping box.

Must do: do not print a RoHS mark on the box. Ask the box maker for a heavy-metals statement before the first shipment. Cost: BLOCKER.

## 7. Open-source licenses for the code and the CAD

Applies: yes, to a duck that ships this code or is printed from this CAD.

The LICENSE file in this repo is Apache-2.0. If the code is redistributed, including in a product, the license requires a copy of the license for the recipient (section 4(a)), a notice on files that were changed (section 4(b)), and the copyright, patent, trademark, and attribution notices kept (section 4(c)). Section 4(d) applies when the work has a NOTICE file. This repo has no NOTICE file. Section 6 does not grant trademark rights, except the ordinary use of a name to say where the work came from. Section 3 includes a patent license that ends if the recipient files suit over the work. That is a condition of using the license. It is not a patent plan. Section 7 gives the work as is, with no warranty.

The dock copy of autodock is Apache-2.0. The license file and the change notes are kept. altaay_lab/software/dock/THIRD_PARTY.md records the copy. Keep those headers if that code ships.

The runtime, the playground, and the reference motion generator: the GitHub content API returned no LICENSE file at the commits pinned in altaay_lab/README.md, and none on the default branch, checked 2026-11-12. DECISIONS.md D6 says those trees stay unmodified and are not republished. A sold image that contains that code needs a license from the authors first. BLOCKER.

altaay_lab/twin/companion/COMPANION.md records that the pretrained wake-word models are under CC BY-NC-SA 4.0, which is noncommercial, and that the duck trains its own model for that reason. Do not ship those pretrained models in a product that is sold.

The Onshape document is public. altaay_lab/README.md says its license is not stated. The Apache license on this repo does not by itself license a CAD file that is not in the repo. BLOCKER for selling printed parts, until the CAD terms allow the sale.

The upstream README ties the shape to a third-party character. No license for that character is in this repo. This file does not clear those rights. BLOCKER for selling the duck as that character. The character is not named here.

Must do: ship the Apache license with the code, mark changed files, do not ship the unlicensed runtime, playground, or reference generator, do not ship the noncommercial wake models, and do not sell under a character name this repo has no right to use.

Sources: the LICENSE file in this repo, https://www.apache.org/licenses/LICENSE-2.0 , altaay_lab/README.md , altaay_lab/software/dock/THIRD_PARTY.md , and altaay_lab/twin/companion/COMPANION.md

## 8. Product liability and insurance

Applies: yes, once a duck is sold and someone is hurt.

Texas products liability is Civil Practice and Remedies Code chapter 82. The chapter was not read line by line. BLOCKER for the defenses and the time limit. In plain words, a seller can be sued when a manufacturing defect, a design defect, or a missing warning hurts someone. The facts a claim would point at are already in COMPLIANCE_FIRST_PASS.md: open contacts, a lithium pack, a charger in the body, and a machine that walks. This note does not decide that any of those is a defect.

No statute opened this session requires this seller to carry a named insurance policy. The premium is BLOCKER. No quote was requested.

Must do, as a practical step before the first sale, not as a statute that was found: place a commercial general liability policy that includes products and completed operations, and keep a path for telling the CPSC if a unit hurts someone.

Do not offer a written warranty until the warranty statute is read. 15 USC 2301 and the sections after it were not opened. BLOCKER for warranty words.

Sources: https://statutes.capitol.texas.gov/Docs/CP/htm/CP.82.htm and https://www.govinfo.gov/link/uscode/15/2064

## What has to be done before a sale

1. Settle the Covered List path. Show a domestic end product, or get a Department of War conditional approval, or change the design so the robot definition does not fit. Do not sell the radio until one of those is true.
2. Open the Pi grant. Do not treat the product brief as a grant for this body.
3. If the grant allows this host, complete the unintentional-radiator declaration or certification, name a responsible party in the United States, and put the part 15 statement on the duck.
4. Do not ship or sell the welded pack until that pack has a UN 38.3 test summary. Mark the watt-hour rating on the case if the smaller-battery path is used.
5. Trace the cells, and the felt if it is cotton, for the UFLPA presumption. Screen legal names of the marketplace brands on the day of the order.
6. Get origin and an HTS class from a broker. Do not rely on the old small-parcel exemption.
7. Use the lead-free solder for California, or do the exposure assessment. Do not add a children's claim. Do not add a coin cell.
8. Ship only code this repo has a right to ship. Do not ship the unlicensed runtime. Do not ship the noncommercial wake models.
9. Make the privacy notice match the software. No face library. No voiceprint. A cue when the camera is on.
10. Place products liability insurance before the first sale. The premium is not known.

## Open BLOCKERs

- The domestic-content percentage on the priced lines is 6.07 percent in DOMESTIC_CONTENT.md (calc only). Unpriced component lines, freight, and duty are still BLOCKER, and so is manufacture of the finished duck in the United States.
- The COTS waiver. The FCC FAQ opened for DOMESTIC_CONTENT.md says the off-the-shelf exception is inapplicable to this test.
- Whether 47 USC 1601(b)(2) narrows the robot category. The section was not read line by line.
- The Department of War guidance, its fee, and its time.
- The Pi FCC id, and the host limits on the grant.
- Lab cost and time for the host test and for UN 38.3.
- Legal names of the marketplace brands listed above.
- Makers not chosen: line 7, line 17m, line 10b-old, the felt, the cloth, and the nest gate board.
- The cell material trace, and the felt fiber.
- HTS class, invoice origin, and the current Section 301 rate.
- Any leftover small-parcel exception. The rule PDF was not read line by line.
- The MCP73213 datasheet, the charger heat, and a charging-mat standard. Those are already open in COMPLIANCE_FIRST_PASS.md.
- UL 2054, IEC 62133, UL 62368-1, and ISO 13482. Not opened, and not found as US statutes in the pages that were opened.
- The Proposition 65 safe-harbor number, and whether screws make the pack easy to remove under Public Resources Code 42463.
- Whether the duck is a California covered electronic device, and the heavy-metal rule for the box.
- COPPA part 312, not read section by section. The CUBI deletion schedule. Texas chapter 82, not read line by line. The 15 USC 2064 time limit. The warranty statute.
- The Onshape license, and the character rights.
- The runtime, the playground, and the reference motion generator have no LICENSE file.
