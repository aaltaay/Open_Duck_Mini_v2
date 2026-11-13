# Proposed BOM changes

Written 2026-11-11 evening ET. Research only. This file does not change BOM.md or bom.json. The nest install agent applies the rows below. PARTS_AUDIT.md, session 2026-11-11 ET, is the evidence. A number from a page opened that session is labeled there. A number from the nest CAD stays CAD check only.

Do not add a line that this file marks BLOCKER.

## Superseded 2026-11-12 ET by D62. Do not order the probe or the socket

The rows below stay as the record of the spring-pin proposal. They are not the nest. The official mat is altaay_lab/cad/nest_v2/. Felt, foil, the gate board, dirt on the gold, a coin short, charger heat, and a camera detector stay BLOCKER. Do not add a line from this table.

## Add when the tip change is accepted (superseded, do not add)

| Proposed line | Part | Qty | Distributor seen | Note |
|---|---|---|---|---|
| nest probe | QA Technology 100-PRP4030S | 4 | no in-stock US page opened | Tube P, tip 30 Round at 1.40 mm, spring S, full stroke 10.16 mm (QA Technology 2023 catalog, pages 32 and 33). Redraw the nest tip from the 2.3 mm estimate to 1.40 mm. The 2 mm minimum in NEST_CAD.md is not met. Cloth puncture stays BLOCKER. NOT TODAY until a US page shows stock. |
| nest socket | QA Technology 100-SDN250S | 4 | TestEquity: Out of Stock, lead time 8 days. TME US: 533 in stock, and the page says international offer only | Same catalog pages. Press ring at 7.62 mm. Length printed beside the part: 30.15 mm. Mounting hole 1.702 to 1.753 mm in FR4, not PLA. PLA press fit BLOCKER. Not a confirmed US cart. |
| nest feed foil | 3M 1181 X 1/2 | one roll | DigiKey page says buy now, ships today | Width 12.70 mm, thickness 0.08 mm (that page). Change the drawn 12 mm feed to 12.7 mm. This roll does not cut the 90 mm sun disc in one piece. |

## Do not add yet

| Item | Why it stays off the bill |
|---|---|
| Felt, 1 mm and 2 mm | No manufacturer part number on a page opened. BLOCKER. |
| Gold cloth and pale gold cloth | Shieldex Nora Dell, product ID 1401101S80, was opened. It is silver, copper, and nickel, under 0.009 ohm per square, 0.125 mm thick (that page). It is not gold and not pale gold. One grey cloth cannot be both poles. Stock page not opened. BLOCKER for the pair. |
| Sun foil disc, 90 mm | The half-inch 1181 roll cannot cut it in one piece. A wider roll was not opened. BLOCKER. |
| Rim foam | No part number. BLOCKER. |
| Gate board | The circuit is not designed. The CAD space is 70 x 26 x 14 mm. BLOCKER. Do not order a stand-in board. |
| In-duck MCP73213 board | Datasheet still not opened. Dropout stays BLOCKER. Do not seat the eval board. |

## Change existing lines (do not apply the buy until the note says the page can sell it)

| Line | Change | Stock this session |
|---|---|---|
| 3 | Keep Adafruit 5291 as the bare-board code. It was OutOfStock. If a board is bought while the bare board is out, the CanaKit code that showed Add to Cart is PI-Z2WH-STR32-C4-BLK (starter kit, pre-soldered header). Bare codes PI-Z2W and PI-Z2WH were Sold Out. | NOT TODAY for the bare board |
| 6 | Keep Molicel INR21700-P45B. Do not switch to the P50B until a page shows the P50B in stock. Both P45B pages opened were out of stock (18650 Battery Store Sold out, Liion Wholesale SKU molicelnpe-inr21700-p45b Out Of Stock). | NOT TODAY |
| 7 | Leave the line with no part number. Do not put it on a one-click order. Strip, sleeve, fish paper, and the weld source were not found. | NOT ORDERABLE. BLOCKER |
| 11 | Record manufacturer part number Li-ion_Battery_Charger_M-2S2A (Adeept, Amazon page). Keep the fit BLOCKER: CAD body 38.2 x 18.1 x 5.2 mm, holes 2.5 mm at 14.4 mm pitch, no drawing on the listing. | Only 7 left |
| 14 | Record the seller model Miuzei SG90 9G Servo. The page part number field is the ASIN. No Tower Pro datasheet was opened. Datasheet stays BLOCKER. | In Stock |
| 17m | No change until an M2 x 12 thread-forming pan head, head about 4.0 mm by 1.6 mm, is on an opened listing. | NOT ORDERABLE. BLOCKER |
| 22c | Delete the looked-up number 22-01-3027. It is not a Molex part. The 2-circuit housing is Molex 0022012027 (DigiKey, buy now, ships today). Do not buy 11 pieces of one width. The harness uses 15 cables on the header, and some share a pin or use both rows. Two housings cannot share a pin. Also name a 20 AWG KK terminal for P12 and P17 before those ends are crimped with 08-50-0114 (22 to 30 AWG on the bill). | the 2-circuit housing can be bought. The line as specified cannot |
| E3 | Record uxcell a18032300ux0174. The page also says bulb shape B10. Fit stays BLOCKER until the part in hand is a bead that fits the eye. | Only 9 left |
| E4 | Record FINGERINSPIRE model KY-FG0001-10-US18. Page size 30 mm by 2 mm. CAD on the bill is 29.6 mm by 1.85 mm. The bill already says the left eye test print checked the fit. | Only 9 left |
| E5 | Keep Need 1 and Buy 1. D33 reverts D29 and keeps the side projector lamp, the reflector, and its lead (DECISIONS.md D33; twin/assembly/ASSEMBLY_TWIN.md). The opened listing title is Aurorad S5. The page says diameter 20 mm, height 15 mm, and a 7 mm LED hole, which matches the seat text on the bill. The manufacturer part number field on that page is only the word Aurorad, so a unique maker number is still missing. Buy this listing. | in stock, ships in 3 to 4 days |
| DK1 | Do not order for the nest. D61 replaced the chest pad. DECISIONS.md is not edited by this pass, so the line stays on the bill until that agent applies the skip. | not a nest part |
| DK5 | Split later into Adafruit 372 (in stock this session) plus the zener, the diode, and the resistors, each with its own part number. Do not order the set as one line. | set NOT ORDERABLE |
| 26 | Wirefy kit ASIN was Currently unavailable. Pick another 3:1 adhesive kit before a one-click, or wait. | NOT TODAY |
| 30 | Adafruit 1886 schema OutOfStock. The bill already names Adafruit 2473 as a lead-free option. That page was not opened this session, so it is not confirmed in stock. | NOT TODAY |
| 33 | Adafruit 3057 schema OutOfStock. | NOT TODAY |
| E2 | Adafruit 3006 schema OutOfStock. No alternate board was opened. | NOT TODAY |
| L2 | Castle Link page: Sold out. | NOT TODAY |
| TE4 | Siglent SDL1020X-E schema OutOfStock. | NOT TODAY |
| 17j, 17k, 17l | BelMetric said the configuration is not available. Re-select the exact size on the page before those three are counted as in stock. | NOT TODAY |
| 10r, E7r | Leave Buy at 0. | DO NOT ORDER |

## One-click

A single order of today's BOM.md is still wrong. It would buy DK1, which the nest no longer uses. It would skip the nest. It would include lines that are out of stock or have no part number (3, 6, 7, 17m, 22c, 26, 30, 33, E2, L2, TE4). E5 stays on the order: D33 restored the side projector lamp. The clean in-stock lines are listed in PARTS_AUDIT.md under "What a one-click can buy after this session".
