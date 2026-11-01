# BOM (final, end to end)

Last updated: 2026-11-01 2:52 PM ET (blocker pass). Prices read on supplier pages 2026-11-01, before tax. Shipping is excluded by the owner's rule; every line ships to the USA. Nothing purchased.

Rules: every quantity comes from CAD/STL measurement (HARDWARE_AUDIT.md, PRINT_CHECK.md, CABLE_MAP.md, MOUNTING.md) or a cited source. Anything that could not be verified is marked BLOCKER with what is needed. Spares are 10 to 20% or the pack minimum, whichever is larger.

Columns: Need = measured requirement; Buy = what to order; Line = price for the Buy quantity.

## Robot

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Smart serial bus servo | Feetech STS3215 7.4 V 1:345 (C001); ships with one 15 cm 5264-3P cable and a screw bag each | 14 | 14 | 1 | 266.00 | Seeed Studio | https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html | Yes | Yes: $19.00 each at 10+ ($20.00 at 1 to 9), in stock 2026-11-01. Bag split: test order (B2) |
| 2 | Servo bus adapter | Waveshare Bus Servo Adapter (A), SKU 25514, 42x33 mm, 2 servo sockets (H3, H5 in parallel per schematic) | 1 | 1 | 1 | 4.99 | Waveshare | https://www.waveshare.com/bus-servo-adapter-a.htm | Yes (from China/HK) | Yes |
| 3 | Compute | Raspberry Pi Zero 2 W | 1 | 1 | 1 | 19.05 | Adafruit 5291 | https://www.adafruit.com/product/5291 | Yes | BLOCKER B24: out of stock online 2026-11-01; Micro Center is in-store only (does not ship); recheck at order time |
| 4 | microSD | SanDisk Ultra 32 GB microSDHC A1 C10, SDSQUAR-032G-GN6MA | 1 | 1 | 1 | 21.25 | Amazon | https://www.amazon.com/dp/B073JWXGNT | Yes | Yes (in stock 2026-11-01, B25) |
| 5 | IMU | Adafruit BNO055 breakout 2472 (NOT 4646: 4646 hole pattern does not match CAD, MOUNTING.md) | 1 | 1 | 1 | 34.95 | Adafruit 2472 | https://www.adafruit.com/product/2472 | Yes | Yes (in stock 2026-11-01) |
| 6 | Li-ion cell | Molicel INR18650-P30B | 2 | 2 | 1 | 17.98 | 18650 Battery Store | https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery | Yes | Yes |
| 7 | 2S cell holder | 2x18650 series holder with leads | 1 | 1 | 1 | 9.99 | Amazon | https://www.amazon.com/dp/B09WCT8672 | Yes | Yes |
| 8 | 2S BMS | JZK 2S 8 A balanced BMS, 41x16x3.5 mm per listing (the upstream bom.csv part), 5 pcs | 1 | 5 | 5 | 6.89 | Amazon (JZK) | https://www.amazon.com/dp/B09VGH38Y5 | Yes | BLOCKER B12: fits the measured envelope 17.75 x 47.2 x 5.33 mm (shift about 1 mm toward body_back) but is rated 8 A, under the 15 A fuse. AITRIP 20 A B08NSTF8CT (48x20x3.4) measured NOT to fit. Decision: smaller fuse or a 15 A board that fits |
| 9 | 5 V regulator | HENGE 4 A UBEC 5 V | 1 | 1 | 1 | 17.29 | Amazon | https://www.amazon.com/Malockos-HENGE-Aeroplane-Helicopter-Mulitcopter/dp/B0DBPXNN7N | Yes | Yes |
| 10 | Power switch | Rated 15 A DC or more, must fit the body_back opening of the stock rocker (23.4x7.4x16.8 mm CAD body) | 1 | 1 | 1 | 6.00 | not chosen | (none) | Yes | BLOCKER B22: no 15 A DC switch with a datasheet and US seller fits 23.4x7.4x16.8 mm; Pololu 2815 is 6 A. $6.00 is a placeholder |
| 11 | USB-C 2S charger | USB-C to 8.4 V 2S charge board (CAD body 38.2x18.1x5.2 mm, holes 2.5 mm at 14.4 mm pitch) | 1 | 1 | 1 | 7.99 | Amazon (Adeept) | https://www.amazon.com/Adeept-18650-Charge-Charging-Board/dp/B0BJTW4QBR | Yes | Price yes; hole pattern vs CAD on test order (no drawing published) |
| 12 | XT30 pair | Amass XT30U, 10 pairs | 1 | 1 | 10 pairs | 8.58 | Amazon | https://www.amazon.com/dp/B08P5HVMYT | Yes | Yes |
| 13 | Foot contact switch | Omron SS-10 (solder terminals), body 19.8x6.4x10.2 mm per datasheet; 2 per foot (Tnkr m11) | 4 | 5 | 1 | 14.70 | DigiKey | https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/SS-10/369860 | Yes | Yes: $2.94 each, min qty 1 (read via search index, direct fetch 403). Seat: foot_top has 2 slots 6.4 x 19.8 mm per foot (measured), press fit per upstream |
| 14 | Antenna servo | SG90-class 9 g, 10-pack | 2 | 10 | 10 | 19.99 | Amazon (Miuzei) | https://www.amazon.com/dp/B072V529YD | Yes | Yes: lead 250 +/- 5 mm per listing (B28); tab holes 27.6 mm match head pilots 27.5 mm (B5) |
| L1 | Servo buck regulator | Castle CC BEC Pro 010-0004-01 set to 7.2 V | 1 | 1 | 1 | 54.95 | Castle Creations | https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01 | Yes | Yes |
| L3 | Inline fuse holder | Littelfuse FHAC0001ZXJ ATO 20 A, 16 AWG leads 89.5 mm (Littelfuse page) | 1 | 1 | 1 | 7.74 | Newark 56P4171 | https://www.newark.com/littelfuse/fhac0001zxj/fuse-holder-in-line/dp/56P4171 | Yes | Yes: 3,553 in stock 2026-11-01 |
| L4 | Fuse | Littelfuse 0287015.PXCN ATO 15 A | 1 | 5 | 1 | 2.20 | DigiKey | https://www.digikey.com/en/products/detail/littelfuse-inc/0287015-PXCN/2519816 | Yes | Yes: $0.44 each, min qty 1 (read via search index, direct fetch 403). Rating vs BMS: B12 |

Subtotal: $520.54

## Fasteners and mechanical

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | M3 heat-set insert | CNC Kitchen M3 x 5.7, D1 4.6 mm, hole 4.0 mm | 58 | 100 | 100 | 10.90 | CNC Kitchen USA | https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces | Yes (US store) | Yes |
| 17a | M3x8 SHCS | DIN 912 A2 stainless, Bolt Depot 6379 | 44 | 52 | each | 3.12 | Bolt Depot | https://boltdepot.com/Product-Details?product=6379 | Yes (US) | Yes |
| 17b | M3x10 SHCS | DIN 912 A2, Bolt Depot 6380 | 12 | 14 | each | 0.84 | Bolt Depot | https://boltdepot.com/Product-Details?product=6380 | Yes | Yes |
| 17c | M3x12 SHCS | DIN 912 A2, Bolt Depot 6381 | 2 | 3 | each | 0.18 | Bolt Depot | https://boltdepot.com/Product-Details?product=6381 | Yes | Yes |
| 17d | M3x6 SHCS | DIN 912 A2, Bolt Depot 6378 (horn screws) | 88 | 100 | 100 | 3.83 | Bolt Depot | https://boltdepot.com/Product-Details?product=6378 | Yes | Yes |
| 17e | M3x5 SHCS | DIN 912 A2, Bolt Depot 6377 (short horn sites) | 12 | 14 | each | 0.70 | Bolt Depot | https://boltdepot.com/Product-Details?product=6377 | Yes | Yes |
| 17f | M2.5x6 SHCS | DIN 912 A2, Bolt Depot 6370 (electronics) | 17 | 20 | each | 1.80 | Bolt Depot | https://boltdepot.com/Product-Details?product=6370 | Yes | Yes (the head board.stl is the Pi footprint, one board, B7) |
| 17g | M2.5x8 SHCS | DIN 912 A2, Bolt Depot 6371 (eyes) | 8 | 10 | each | 0.90 | Bolt Depot | https://boltdepot.com/Product-Details?product=6371 | Yes | Yes |
| 17i | M2.5x10 SHCS | DIN 912 A2, Bolt Depot 6372 (battery lid, pilot depth 2.1 to 15.3 mm) | 4 | 5 | each | 0.50 | Bolt Depot | https://boltdepot.com/Product-Details?product=6372 | Yes | Yes: head sits proud on the lid face, clamp 5.2 mm, engagement 4.8 mm, no interference (GLB measured, B3) |
| 17h | M2 self-tapping kit | METALLIXITY 304 SS M2/M2.6 pan head kit with M2x4, M2x5, M2x6, M2x8: 2 x M2x5 at the short servo sites, 4 x M2x4 for the camera | 6 | 1 | kit | 9.49 | Amazon (ships from Amazon) | https://www.amazon.com/dp/B0FS13B75Y | Yes | Price yes (6 left 2026-11-01); head fit and camera length on test order (B21, B9) |
| 18 | Ball bearing | 6804ZZ 20x32x7 (CAD model measured 19.99/32.19/7.0), Motoforti 10-pack | 3 | 10 | 10 | 7.74 | Amazon | https://www.amazon.com/dp/B0D99THG1M | Yes | Yes (only 1 left 2026-11-01) |
| 19 | Threadlocker | Loctite 243, 6 mL, P/N 1330799 | 1 | 1 | 1 | 9.90 | Amazon | https://www.amazon.com/dp/B004L439FE | Yes | Yes |

Subtotal: $49.90

## Cables, connectors, wire

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | USB data cable | Micro-B to USB-C, 50 cm, QJJ T1G-W3R | 1 | 1 | 1 | 5.00 | Amazon | https://www.amazon.com/dp/B0B67NKCSW | Yes | Price yes; length vs route on test order (B18) |
| 21 | Mini-SPOX housing | Molex 50-37-5033, 3 pos 2.5 mm (mates STS3215 5264 sockets) | 2 | 10 | 1 | 1.43 | Newark 57H1785 | https://www.newark.com/search?st=50-37-5033 | Yes | Yes: $0.143 each at 1+ (one made lead, S14) |
| 22 | Mini-SPOX crimp terminal | Molex 08-70-1040 (5263, 22 to 28 AWG) | 6 | 30 | 1 | 5.40 | Newark 54H5573 | https://www.newark.com/search?st=08-70-1040 | Yes | Yes: $0.180 each at 25+ (Mouser $0.23, 160,210 in stock, read via search index) |
| L5 | Power wire 16 AWG | BNTECHGO silicone red and black 25 ft each | 1.7 m | 1 | 50 ft | 19.98 | Amazon | https://www.amazon.com/dp/B01MCRY7OT | Yes | Yes |
| 23 | Wire 20 AWG | BNTECHGO silicone red 25 ft and black 25 ft | 1.6 m | 1 | 50 ft | 12.48 | Amazon | https://www.amazon.com/BNTECHGO-Gauge-Silicone-Wire-Temperature/dp/B01F8PO5XE | Yes | Yes |
| 24 | Wire 22 AWG | BNTECHGO silicone 6 colors 25 ft each | 1.0 m | 1 | 150 ft | 16.98 | Amazon | https://www.amazon.com/BNTECHGO-Silicone-Spool-Color-100ft/dp/B09X4KY56S | Yes | Yes |
| 25 | Wire 26 AWG | BNTECHGO silicone 7 colors 25 ft each | 9 m | 1 | 175 ft | 15.98 | Amazon | https://www.amazon.com/dp/B08F9CF85N | Yes | Yes |
| 26 | Heat shrink | Wirefy 3:1 adhesive lined, 180 pcs | 1 | 1 | 180 | 14.99 | Amazon | https://www.amazon.com/Wirefy-180-Heat-Shrink-Tubing/dp/B084GDLSCK | Yes | Yes |

Subtotal: $92.24

## Print material

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 27 | PLA | Overture Easy PLA 1.75 mm 1 kg, black (need 1304 g sliced, 1.5 kg with 15% spare) | 1.5 kg | 2 | 1 kg | 29.98 | Amazon | https://www.amazon.com/dp/B09LCK7QJ2 | Yes | Yes |
| 28 | TPU | Overture TPU 95A 1.75 mm 1 kg, black (need 35 g; hardness not stated upstream) | 35 g | 1 | 1 kg | 23.99 | Amazon | https://www.amazon.com/dp/B0BGMP1MZ7 | Yes | Price yes; hardness on test order (B26, GAPS A8) |

Subtotal: $53.97

## Expression (optional upstream)

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | Speaker | uxcell 4 ohm 3 W 40x40x20 mm, 2 pcs (US equivalent of upstream ANGEEK B086JH2BTD, 40 mm 4 ohm 3 W; CAD envelope 38.5 x 38.7 x 15 mm) | 1 | 2 | 2 | 12.39 | Amazon (uxcell) | https://www.amazon.com/dp/B07M5K17SK | Yes | Price yes; fit and retention on test order (B8) |
| E2 | I2S amplifier | Adafruit MAX98357A 3006 | 1 | 1 | 1 | 5.95 | Adafruit | https://www.adafruit.com/product/3006 | Yes | Price yes; mount NO (not in CAD) |
| E3 | LEDs | 1 W warm white LED beads, 10 pcs (upstream bom.csv: 1 W beads) | 3 | 10 | 10 | 6.89 | Amazon (uxcell) | https://www.amazon.com/dp/B07DHB13J4 | Yes | Yes (B23) |
| E3b | LED resistor | 100 ohm 1/4 W, 20 pcs (Tnkr m7: 100 ohm per eye LED on GPIO) | 2 | 20 | 20 | 1.50 | SparkFun PRT-14493 | https://www.sparkfun.com/resistor-100-ohm-1-4-watt-pth-20-pack-thick-leads.html | Yes | Yes (B23) |
| E4 | Eye glass | round discs for the CAD eye glass ø29.6 x 1.85 mm, 60 pcs | 2 | 60 | 60 | 8.89 | Amazon (FINGERINSPIRE) | https://www.amazon.com/dp/B0C4H17QSH | Yes | Price yes; disc fit checked with the left_eye test print |
| E5 | Projector reflector | Aurorad S5 aluminium reflector 20x15 mm, 7 mm LED hole (CAD seat tapers to 20.0 mm, about 10 mm deep, narrow end 8.07 mm) | 1 | 1 | 1 | 9.15 | Amazon (Aurorad) | https://www.amazon.com/dp/B0BGS3C42N | Yes | Price yes (in stock, ships in 3 to 4 days); seat height on test order |
| E6 | Camera | Raspberry Pi Camera Module 3, 21 x 12.5 mm holes match head.stl pilots 20.9 x 12.5 (B9) | 1 | 1 | 1 | 29.25 | Adafruit 5657 | https://www.adafruit.com/product/5657 | Yes | Yes (in stock 2026-11-01) |
| E7 | Camera cable | Pi Zero camera cable 150 mm (Zero has the 22-pin port) | 1 | 1 | 1 | 5.95 | Adafruit 3157 | https://www.adafruit.com/product/3157 | Yes | Price yes; length on test order |

Subtotal: $79.97

## Tools (one-time)

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Soldering iron | Pine64 Pinecil V2 (needs a USB-C PD supply, not costed) | 1 | 1 | 1 | 25.99 | Pine64 | https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/ | Yes (ships from Pine64; US warehouse not verified) | Yes |
| T2 | Insert tips | Pinecil threaded insert tips set and adapter | 1 | 1 | 1 | 14.99 | Pine64 | https://pine64.com/product/pinecil-threaded-insert-tips-set-and-adapter/ | Yes | Yes |
| T3 | Crimper | Engineer PA-09 (Mini-SPOX 5263 and JST XH per DigiKey chart) | 1 | 1 | 1 | 37.93 | Amazon | https://www.amazon.com/Engineer-PA-09-Micro-Connector-Crimpers/dp/B002AVVO7K | Yes | Yes |
| T4 | Hex keys | Bondhus 12192 hex L-keys 1.5 to 6 mm, 7 pc (2.0 mm for M2.5, 2.5 mm for M3 SHCS) | 1 | 1 | 7 pc | 7.84 | Crawford Tool | https://crawfordtool.com/products/bondhus-12192-metric-hex-key-set-l-wrenches-7-pieces-1-5mm-to-6mm | Yes | Yes |
| T5 | Wire stripper | Klein 11057, 22 to 32 AWG stranded | 1 | 1 | 1 | 21.97 | Home Depot | https://www.homedepot.com/p/Klein-Tools-Klein-Kurve-Wire-Stripper-and-Cutter-20-30-AWG-Solid-22-32-AWG-Stranded-11057/100352112 | Yes | Yes |
| L2 | BEC programmer | Castle Link V4 011-0173-00 (needs Windows 10 PC) | 1 | 1 | 1 | 29.95 | Castle Creations | https://castlecreations.com/products/accessories-castle-link-v4-psoc-usb-programming-kit-011-0173-00 | Yes | Yes |

Subtotal: $138.67

## Totals

| Scope | $ |
|---|---|
| Robot | 520.54 |
| Fasteners and mechanical | 49.90 |
| Cables, connectors, wire | 92.24 |
| Print material | 53.97 |
| Expression (optional upstream) | 79.97 |
| Tools (one-time) | 138.67 |
| Build total (robot + fasteners + cables + filament) | 716.65 |
| Build + expression pack | 796.62 |
| Build + expression + tools | 935.29 |

Previous BOM (before this audit): core $684.99, grand $730.94 with lab changes. The build total now adds fasteners, inserts, bearings, filament, wire, connectors and heat shrink that were missing or unverified, and moves the Castle Link to Tools.

Order minimums (B29, cleared): Bolt Depot has no minimum order (service page); DigiKey and Newark allow qty 1 on every line used; Mouser has no minimum for stocked parts (help page, read via search index); the rest are pack products. Shipping is excluded by the owner's rule.

Not costed: sales tax, a 15 A switch (row 10 is a $6.00 placeholder, B22), a USB-C PD supply for the Pinecil, a 16 to 20 AWG stripper, a multimeter, digital calipers, a heat gun or lighter for heat shrink.

## Contingency (not in totals)

| # | Item | Qty | $ | Trigger |
|---|---|---|---|---|
| X1 | Extra Molex 50-37-5033 housings (Newark 57H1785, $0.143) | 20 | 2.86 | Kit 15 cm servo cables too short on test fit (CABLE_MAP S-hops) |
| X2 | Extra Molex 08-70-1040 terminals (Newark 54H5573, $0.170 at 50+) | 60 | 10.20 | Same as X1 (10 made leads at 22 AWG) |
| X3 | 1 m Micro-B to USB-C cable | 1 | not priced | USB route W12 longer than 50 cm on test fit |

## Removed from the previous BOM

- Barrel jack lead (old row 12): the lab build feeds the adapter through its screw terminal H1, so 0 needed.
- Braided cable sheath (old row 21): not required by any measured route; price was unverified. Dropped.
- Adafruit 4646 BNO055: replaced by 2472 because 4646 holes do not match the CAD pilots (MOUNTING.md).
- Castle Link V4 moved to Tools.
- Y-lead parts (old Need 3 housings, 9 terminals): dropped, the neck chain hangs off the left ankle (B19).
- AITRIP 20 A BMS: measured not to fit the CAD envelope (B12); replaced by the upstream JZK part, rating decision open.
- IMSCREWS M2x5 100 pcs: replaced by the METALLIXITY kit, which also has the camera M2x4.

## BLOCKERS that affect this BOM

See HARDWARE_AUDIT.md section 6 for all 29 with the method for each.
- 3 Compute: B24, out of stock online 2026-11-01.
- 8 2S BMS: B12, JZK fits but is rated 8 A; decide the fuse or find a 15 A board that fits 17.75 x 47.2 x 5.33 mm.
- 10 Power switch: B22, no fitting 15 A part; $6.00 placeholder.
- 1, 17h, 20, 28, E1, E5, E7 and row 11: fit or length settled only by the test order below.

## Needs test order

Parts where only a real part can settle the question. Every line below is already a BOM line, so buying these first adds nothing to the build total except the servo price break (1 now at $20.00 plus 13 later at $19.00 is $267.00, $1.00 more than 14 at once). Nothing has been bought.

| # | What to buy | Qty | $ | BOM line | Why (blockers) |
|---|---|---|---|---|---|
| TO1 | Feetech STS3215 7.4 V, Seeed | 1 | 20.00 | 1 | Count the 18-screw bag by size (B2); horn to case gap and pilot depth at the 2 M2x5 sites (B6); bus port positions (B10); kit cable length on the longest hop (B17); M2x5 head fit (B21) |
| TO2 | JZK 2S BMS, 5 pcs | 1 pack | 6.89 | 8 | Fit in the printed body at the measured envelope, solder pad access (B12) |
| TO3 | QJJ Micro-B to USB-C 50 cm | 1 | 5.00 | 20 | Route length 502.6 mm through the neck (B18) |
| TO4 | METALLIXITY M2 self-tapping kit | 1 | 9.49 | 17h | M2x5 head fit (B21); M2x4 vs camera PCB thickness (B9) |
| TO5 | Adafruit BNO055 2472 | 1 | 34.95 | 5 | Hole spacing with calipers (B13); IMU axis tilt test (B20) |
| TO6 | Miuzei SG90 10-pack | 1 | 19.99 | 14 | Bag screw sizes for the antenna holder and tabs (B5); D9 lead extension |
| TO7 | uxcell 40 mm 4 ohm 3 W speaker, 2 pcs | 1 | 12.39 | E1 | Fit and retention in speaker_interface (B8) |
| TO8 | Raspberry Pi Camera Module 3, Adafruit 5657 | 1 | 29.25 | E6 | Screw length on the 3.1 mm pilots (B9) |
| TO9 | Pi Zero camera cable 150 mm, Adafruit 3157 | 1 | 5.95 | E7 | Cable reaches the Pi on the head floor |
| TO10 | Aurorad S5 reflector | 1 | 9.15 | E5 | Height in the 20.0 mm seat |
| TO11 | Bolt Depot M2.5x8 SHCS, 10 pcs, plus a left_eye test print | 10 | 0.90 | 17g | Left eye pilot 2.2 mm vs right 2.05 mm (B14); eye glass disc fit |
| TO12 | CNC Kitchen M3 inserts, 100 pcs | 1 | 10.90 | 16 | Bore depth 5.8 vs 6.7 (B15); foot_top wall 1.5 mm pull test (B16) |
| TO13 | Overture TPU 95A 1 kg | 1 | 23.99 | 28 | Print foot_bottom_tpu, grip and fit (B26) |
| TO14 | Omron SS-10, DigiKey | 1 | 2.94 | 13 | Press fit in the foot_top 6.4 x 19.8 mm slot |
| TO15 | Adeept USB-C 2S charge board | 1 | 7.99 | 11 | Hole pattern vs CAD 2.5 mm at 14.4 mm pitch (no drawing published) |

Test order total: $199.78.
