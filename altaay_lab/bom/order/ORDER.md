# Order: one Duckie and one nest

One bill for one finished duck and its nest. Prices that were read on a live page on 2026-11-12 use the label cited, checked 2026-11-12. Shipping and tax are not included, the same rule as BOM.md. Nothing was bought, and nothing was added to a cart.

This file only collects parts that the lab files already name. It does not add a new contact, a new board, or a new fastener pattern. Where a file has no part number, the line says BLOCKER.

Maker screening against restricted lists waits for altaay_lab/compliance/. That folder is not in the tree. This bill does not start that check.

## What was reused

- BOM.md, fasteners/fasteners.json, and fasteners/FASTENERS.md for the duck screws, inserts, washers, wire, and tools.
- wiring/netlist.yaml for the duck components. Splices whose part text says solder stay on the solder line.
- circuitry/CHARGER_BOARD.md and circuitry/charger_board.yaml for the in-duck MCP73213 board. The Adeept board is not ordered.
- twin/dock/nest/cad/NEST_CAD.md for the nest at 190 mm: felt, cloth, foil, foam, jack, and the six extra inserts and six extra screws.
- twin/dock/flush/FLUSH_CONTACTS.md for the Mill-Max 0906 pin and the five seat wells. Proud probes are not ordered.
- twin/dock/closeup/CLOSEUP.md for the 40 mm wall card. It is a plain square, not a coded tag.
- twin/structure/shin_eye/SHIN_EYE.md and shin_eye/slice.json for PA6-CF grams. twin/structure/TOPOLOGY.md for the PLA gram delta. print/SLICE_SUMMARY.md and print/PRINT_PLAN.md for the installed slice.
- The foot carve in the topology study is not ordered. That study already left it out.

## Not ordered, and why

- Chest pad, charge ideal diode DK2, the SENSE splice, the wake branch, and the Adeept USB-C board. CHARGER_BOARD.md and D61 already retire them. The netlist still contains those ids. check_order.py excludes them by those citations.
- The paddle dock in twin/dock/DOCK_BOM_FULL.md. D61 replaced it. Its gate, springs, ballast, and tags are not this nest.
- QA Technology probes. FLUSH_CONTACTS.md is the contact pick. The nest CAD still draws the long probes. They are not on this bill.
- A knee servo other than the STS3215. D32 names one. The current pick for this bill is STS3215 on all 14 joints, including the two knees.
- WAGO splices. BOM.md line 26b names them for two nodes. The netlist part text for those nodes still says solder. This bill follows the netlist and does not buy both.
- The 5 V wall supply that existed only to feed the Adeept board.
- Test equipment TE1 to TE4. BOM.md already keeps them out of the build. Their pages were not opened today, so they are not copied here as prices.
- Magnets: none. The flush study looked at a magnetic connector and did not pick it. fasteners.json has no magnet.
- Standoffs to buy: none. FASTENERS.md says the bosses are printed.
- Nuts to buy: none. fasteners.json has no nut. The DC jack brings its own nut.

## Totals

These sums are calc only. They add the line_usd column. A line is in that column only when a page opened today showed a price, the part was not out of stock, and the buy quantity is known. BLOCKER lines are not in the sum. This is not the cost of a finished duck.

- Adafruit: $155.05
- CNC Kitchen USA: $10.90
- CanaKit: $89.95
- DigiKey: $3.36
- Horizon Hobby: $54.95
- MatterHackers: $57.99
- Pine64: $40.98
- Pololu: $47.64
- Seeed Studio: $280.00
- SparkFun: $1.50
- Tenergy: $22.99
- illumn: $17.98

Grand total of lines that can be bought today: $783.29

## Filament grams

Calc only. Not weighed.

- Installed robot PLA is 1355.5 g (print/SLICE_SUMMARY.md total). The shin sheets in that total are 23.2 g and 22.2 g. 1355.5 minus 23.2 minus 22.2 is 1310.1 g of PLA that stays.
- Topology deltas that stay PLA are 44.09 minus 7.48, which is 36.61 g (twin/structure/TOPOLOGY.md). The 7.48 g is the shin row, and those sheets move to PA6-CF instead. The topology shin base is 10.38 g each. The installed slice is 11.58 g each. The 36.61 g is from the other slice, added onto the installed set. It is about 3 percent of 1310 g, which matches pads on existing parts, not a new body.
- Duck PLA after those two studies: 1310.1 plus 36.61 is 1346.71 g. The existing spare rule is 10 to 20 percent. At 20 percent, 1346.71 times 1.2 is 1616.05 g, which is under 2 kg. The buy stays 2 spools of 1 kg, the existing line. The spool page was not opened today, so the dollars are not in the total.
- Nest box and lid were not sliced (NEST_CAD.md). Whether 2 spools cover them is BLOCKER. No guessed gram number is added.
- TPU is 75.1 g (print/PRINT_PLAN.md, the D59 robot set). One 1 kg spool is the existing line. The flush wells were not re-sliced, so that delta is BLOCKER.
- PA6-CF is 28.03 g for the drive pair plus 17.97 g for the idle pair, 46.00 g (twin/structure/shin_eye/slice.json). One 0.5 kg spool covers that. The drive sheet is the recessed web. The idle sheet is the stock shin. The spacer stays PLA. Hot tensile, wet tensile, and the printer chamber are still BLOCKER in SHIN_EYE.md. The filament is still the named material.

## Fasteners

Duck counts are the fitted rows in fasteners/fasteners.json (CAD check only). Nest adds, from NEST_CAD.md section 5, 6 inserts, 4 of M3x6 button head, and 2 of M3x8. No new screw size. The lid is four corners. The terminals are a mirror pair. That is the pattern already in that file. D39 and D42 are unchanged by this bill.

## BLOCKER lines

A line is a BLOCKER when it has no source, the page was out of stock, the datasheet is still unread, or the count is not in the files. Out-of-stock lines keep the price that was on the page and stay out of the total.

- amp: MAX98357A I2S amplifier. out of stock
- kapton: Polyimide tape, 10 mm x 33 m. out of stock
- sdread: USB-C microSD reader. out of stock
- solder: Solder wire, 60/40 rosin core, 0.5 mm, 50 g. out of stock
- pin: Short-stroke spring pin for the flush mat. count is not in FLUSH_CONTACTS.md
- adapter: Nest wall supply, 8.70 V to 10.0 V. tolerance was not opened
- alcohol: Isopropyl alcohol, 99.8 percent, 1 pint. page not opened 2026-11-12
- asm: Charger board assembly. no gerber in the lab files
- bearing: Ball bearing 20 x 32 x 7 mm. page not opened 2026-11-12
- button: Momentary pushbutton. page not opened 2026-11-12
- camcable: Camera cable, standard to mini, 300 mm. page not opened 2026-11-12
- caps: 4.7 uF 25 V X5R 1206. page not opened 2026-11-12
- controller: Xbox wireless controller. page not opened 2026-11-12
- cqen: N-channel MOSFET, enable. datasheet not opened
- crprog: 1.10 k ohm, 1 percent, 0603. page not opened 2026-11-12
- cu2: Comparator, dual. distributor page not opened 2026-11-12
- cu3: Shunt reference. datasheet not opened
- diode: Small-signal diode. full order code not opened
- feed: Copper foil tape, 1/2 in, for the hidden feed. page not opened 2026-11-12
- felt1: Nest felt, 1 mm. no maker part number in the lab files
- felt2: Rim felt, 2 mm. no maker part number in the lab files
- foam: Rim bolster foam. no maker part number in the lab files
- foot: Foot contact switch. page not opened 2026-11-12
- fs17a: M3x8 socket head, A2. page not opened 2026-11-12
- fs17b: M3x10 socket head, A2. page not opened 2026-11-12
- fs17c: M3x12 socket head, A2. page not opened 2026-11-12
- fs17d: M3x6 socket head, A2, pack of 100. page not opened 2026-11-12
- fs17e: M3x5 socket head, A2. page not opened 2026-11-12
- fs17f: M2.5x6 socket head, A2. page not opened 2026-11-12
- fs17g: M2.5x8 socket head, A2. page not opened 2026-11-12
- fs17h: M2 self-tapping kit, 304 SS. page not opened 2026-11-12
- fs17i: M2.5x10 socket head, A2. page not opened 2026-11-12
- fs17j: M3x6 button head, A2. page not opened 2026-11-12
- fs17k: M2.5x5 socket head, A2. page not opened 2026-11-12
- fs17l: M2.5 flat washer, 0.3 mm. page not opened 2026-11-12
- fs17m: M2x12 thread-forming pan head. no listing in the lab files and none opened today
- fuse15: ATO fuse, 15 A. page not opened 2026-11-12
- fuse5: ATO fuse, 5 A. page not opened 2026-11-12
- gate: Rim gate board. the board is not designed
- glass: Eye glass discs. page not opened 2026-11-12
- holder: ATO inline fuse holder. page not opened 2026-11-12
- jack: DC jack, 2.1 mm. page not opened 2026-11-12
- l2: BEC programmer. page not opened 2026-11-12
- led: 1 W warm white LED bead, pack of 10. page not opened 2026-11-12
- loctite: Threadlocker. page not opened 2026-11-12
- mount: Adhesive tie mount, 19 mm. page not opened 2026-11-12
- mounts: Adhesive tie mount, 12.7 mm. page not opened 2026-11-12
- nestpla: Nest box and lid, PLA, grams not sliced. grams were not sliced
- nozzle: Hardened nozzle, 0.6 mm recommended. no listing opened today
- pcb: Charger board fabrication. no gerber in the lab files
- pla: PLA filament, 1.75 mm, 1 kg. page not opened 2026-11-12
- rbias: 0603 resistor, 1 percent, 10.0 k ohm NTC bias. full order code not opened
- rcold: 0603 resistor, 1 percent, 10.0 k ohm cold divider. full order code not opened
- rcoldb: 0603 resistor, 1 percent, 28.0 k ohm cold divider. full order code not opened
- reflector: Projector reflector. page not opened 2026-11-12
- rg: 10 k ohm, 1 percent, 0603. full order code not opened
- rhot: 0603 resistor, 1 percent, 10.0 k ohm hot divider. full order code not opened
- rhotb: 0603 resistor, 1 percent, 2.80 k ohm hot divider. full order code not opened
- ring: Pale gold conductive cloth, ring. no maker part number in the lab files
- rka: 0603 resistor, 1 percent, 4.99 k ohm reference feed. full order code not opened
- rpu: 0603 resistor, 1 percent, 100 k ohm pull-up. full order code not opened
- rser: 0603 resistor, 1 percent, 10 k ohm pull-up. full order code not opened
- rstat: 0603 resistor, 1 percent, 1 k ohm series. full order code not opened
- sd: microSD 32 GB. page not opened 2026-11-12
- sg90: SG90-class 9 g servo, pack of 10. page not opened 2026-11-12
- shrink: Heat shrink, 3:1 adhesive lined, 180 piece kit. page not opened 2026-11-12
- speaker: Speaker, 36 mm, 8 ohm, 2 W. page not opened 2026-11-12
- spoxh: Mini-SPOX housing, 3 position. page not opened 2026-11-12
- spoxt: Mini-SPOX crimp terminal. page not opened 2026-11-12
- sun: Gold conductive cloth, sun disc. no maker part number in the lab files
- t10: Heat gun. page not opened 2026-11-12
- t11: Drill bit 6.0 mm. page not opened 2026-11-12
- t12: Drill bit 2.7 mm. page not opened 2026-11-12
- t13: T-handle tap wrench. page not opened 2026-11-12
- t14: Drill bit 4.0 mm. page not opened 2026-11-12
- t15: Drill bit 4.5 mm. page not opened 2026-11-12
- t16: Screwdriver PH 0. page not opened 2026-11-12
- t17: Screwdriver PH 1. page not opened 2026-11-12
- t18: Bit PH 0 x 25 mm. page not opened 2026-11-12
- t19: Drill bit 1/16 in, pack of 3. page not opened 2026-11-12
- t3: Crimper. page not opened 2026-11-12
- t4: Hex key set, 1.5 to 6 mm. page not opened 2026-11-12
- t5: Wire stripper, 22 to 32 AWG. page not opened 2026-11-12
- t6: USB-C PD supply, 65 W. page not opened 2026-11-12
- t7b: USB-A to USB-C cable, 3 ft. page not opened 2026-11-12
- t9: Wire stripper, 12 to 20 AWG. page not opened 2026-11-12
- tie: Cable tie, 4 in, pack of 100. page not opened 2026-11-12
- tpu: TPU 95A filament, 1.75 mm, 1 kg. page not opened 2026-11-12
- vhb: Foam tape, 3M VHB 4950, 3/4 in x 5 yd. page not opened 2026-11-12
- wall: Wall card, 40 mm square, cut from felt, no electronics. no separate part to buy until the felt has a part number
- waveshare: Bus servo adapter, USB data only. page not opened 2026-11-12
- weld: 2S pack build: nickel strip, sleeve, fish paper, weld. no maker part number in the lab files
- wells: Flush gold wells in the seat, 3 mm, five of them. no maker part number in the lab files
- wire16: Silicone wire, 16 AWG, red and black. page not opened 2026-11-12
- wire20: Silicone wire, 20 AWG, red and black. page not opened 2026-11-12
- wire22: Silicone wire, 22 AWG, 6 colors. page not opened 2026-11-12
- wire26: Silicone wire, 26 AWG, 7 colors. page not opened 2026-11-12
- xt30: XT30U pair, pack. page not opened 2026-11-12
- zener: 4.7 V zener. datasheet not opened

## Check

python3 altaay_lab/bom/order/check_order.py

The script fails if a netlist part, a charger part, a print part, or a fastener line is missing from ORDER.csv, or if ORDER.csv maps a token the current design does not have.
