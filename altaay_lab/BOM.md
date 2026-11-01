# BOM (final, end to end)

Last updated: 2026-11-01 2:10 PM ET. Prices read on supplier pages 2026-11-01, before shipping and tax. Nothing purchased.

Rules: every quantity comes from CAD/STL measurement (HARDWARE_AUDIT.md, PRINT_CHECK.md, CABLE_MAP.md, MOUNTING.md) or a cited source. Anything that could not be verified is marked BLOCKER with what is needed. Spares are 10 to 20% or the pack minimum, whichever is larger.

Columns: Need = measured requirement; Buy = what to order; Line = price for the Buy quantity.

## Robot

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Smart serial bus servo | Feetech STS3215 7.4 V 1:345 (C001); ships with one 15 cm 5264-3P cable and a screw bag each | 14 | 14 | 1 | 280.00 | Seeed Studio | https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html | Yes | Price yes; stock at order time NO |
| 2 | Servo bus adapter | Waveshare Bus Servo Adapter (A), SKU 25514, 42x33 mm, 2 servo sockets (H3, H5 in parallel per schematic) | 1 | 1 | 1 | 4.99 | Waveshare | https://www.waveshare.com/bus-servo-adapter-a.htm | Yes (from China/HK) | Yes |
| 3 | Compute | Raspberry Pi Zero 2 W | 1 | 1 | 1 | 19.05 | Adafruit 5291 | https://www.adafruit.com/product/5291 | Yes | BLOCKER: out of stock 2026-11-01 |
| 4 | microSD | 32 GB A1 class 10, exact model not chosen | 1 | 1 | 1 | 8.00 | any US retailer | (none chosen) | Yes | BLOCKER: pick exact model and link |
| 5 | IMU | Adafruit BNO055 breakout 2472 (NOT 4646: 4646 hole pattern does not match CAD, MOUNTING.md) | 1 | 1 | 1 | 34.95 | Adafruit 2472 | https://www.adafruit.com/product/2472 | Yes | Yes (in stock 2026-11-01) |
| 6 | Li-ion cell | Molicel INR18650-P30B | 2 | 2 | 1 | 17.98 | 18650 Battery Store | https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery | Yes | Yes |
| 7 | 2S cell holder | 2x18650 series holder with leads | 1 | 1 | 1 | 9.99 | Amazon | https://www.amazon.com/dp/B09WCT8672 | Yes | Yes |
| 8 | 2S BMS | 2S 20 A balanced BMS | 1 | 1 | 1 | 11.99 | Amazon (AITRIP) | https://www.amazon.com/AITRIP-Lithium-Battery-Charger-Balance/dp/B08NSTF8CT | Yes | Yes; fit in CAD pocket NO (see MOUNTING) |
| 9 | 5 V regulator | HENGE 4 A UBEC 5 V | 1 | 1 | 1 | 17.29 | Amazon | https://www.amazon.com/Malockos-HENGE-Aeroplane-Helicopter-Mulitcopter/dp/B0DBPXNN7N | Yes | Yes |
| 10 | Power switch | Rated 15 A DC or more, must fit the body_back opening of the stock rocker (23.4x7.4x16.8 mm CAD body) | 1 | 1 | 1 | 6.00 | not chosen | (none) | Yes | BLOCKER: no rated part chosen |
| 11 | USB-C 2S charger | USB-C to 8.4 V 2S charge board (CAD body 38.2x18.1x5.2 mm, holes 2.5 mm at 14.4 mm pitch) | 1 | 1 | 1 | 7.99 | Amazon (Adeept) | https://www.amazon.com/Adeept-18650-Charge-Charging-Board/dp/B0BJTW4QBR | Yes | Price yes; hole pattern vs CAD NO |
| 12 | XT30 pair | Amass XT30U, 10 pairs | 1 | 1 | 10 pairs | 8.58 | Amazon | https://www.amazon.com/dp/B08P5HVMYT | Yes | Yes |
| 13 | Foot contact switch | Omron SS-10 (solder terminals) | 2 | 4 | 1 | 7.00 | DigiKey | https://www.digikey.com/en/products/result?keywords=omron%20SS-10 | Yes | Price yes; foot mount NO (not in CAD) |
| 14 | Antenna servo | SG90-class 9 g, 10-pack | 2 | 10 | 10 | 19.99 | Amazon (Miuzei) | https://www.amazon.com/dp/B072V529YD | Yes | Price yes; lead length NO |
| L1 | Servo buck regulator | Castle CC BEC Pro 010-0004-01 set to 7.2 V | 1 | 1 | 1 | 54.95 | Castle Creations | https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01 | Yes | Yes |
| L3 | Inline fuse holder | Littelfuse FHAC0001ZXJ ATO 20 A, 16 AWG leads | 1 | 1 | 1 | 7.74 | Newark | https://www.newark.com/search?st=FHAC0001ZXJ | Yes | Price yes; stock NO |
| L4 | Fuse | Littelfuse 0287015.PXCN ATO 15 A | 1 | 5 | 1 | 2.25 | DigiKey | https://www.digikey.com/en/products/result?keywords=0287015.PXCN | Yes | NO (US price from EUR listing) |

Subtotal: $518.74

## Fasteners and mechanical

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | M3 heat-set insert | CNC Kitchen M3 x 5.7, D1 4.6 mm, hole 4.0 mm | 58 | 100 | 100 | 10.90 | CNC Kitchen USA | https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces | Yes (US store) | Yes |
| 17a | M3x8 SHCS | DIN 912 A2 stainless, Bolt Depot 6379 | 44 | 52 | each | 3.12 | Bolt Depot | https://boltdepot.com/Product-Details?product=6379 | Yes (US) | Yes |
| 17b | M3x10 SHCS | DIN 912 A2, Bolt Depot 6380 | 12 | 14 | each | 0.84 | Bolt Depot | https://boltdepot.com/Product-Details?product=6380 | Yes | Yes |
| 17c | M3x12 SHCS | DIN 912 A2, Bolt Depot 6381 | 2 | 3 | each | 0.18 | Bolt Depot | https://boltdepot.com/Product-Details?product=6381 | Yes | Yes |
| 17d | M3x6 SHCS | DIN 912 A2, Bolt Depot 6378 (horn screws) | 88 | 100 | 100 | 3.83 | Bolt Depot | https://boltdepot.com/Product-Details?product=6378 | Yes | Yes |
| 17e | M3x5 SHCS | DIN 912 A2, Bolt Depot 6377 (short horn sites) | 12 | 14 | each | 0.70 | Bolt Depot | https://boltdepot.com/Product-Details?product=6377 | Yes | Yes |
| 17f | M2.5x6 SHCS | DIN 912 A2, Bolt Depot 6370 (electronics) | 21 | 25 | each | 2.25 | Bolt Depot | https://boltdepot.com/Product-Details?product=6370 | Yes | Yes |
| 17g | M2.5x8 SHCS | DIN 912 A2, Bolt Depot 6371 (eyes) | 8 | 10 | each | 0.90 | Bolt Depot | https://boltdepot.com/Product-Details?product=6371 | Yes | Yes |
| 17i | M2.5x10 SHCS | DIN 912 A2, Bolt Depot 6372 (battery lid, pilot depth 2.1 to 15.3 mm) | 4 | 5 | each | 0.50 | Bolt Depot | https://boltdepot.com/Product-Details?product=6372 | Yes | Price yes; head fit BLOCKER (recess 4.0 mm, head 4.5 mm) |
| 17h | M2x5 self-tapping | IMSCREWS 304 SS pan washer head Type A, 100 pcs | 2 | 100 | 100 | 7.99 | IMSCREWS | https://www.imscrews.com/products/imscrews-100-pcs-m2-x-5mm-black-self-tapping-screws-304-stainless-steel-phillips-pan-washer-head-natural-black-no-peeling-type-a-point-for-metal-wood-plastic | Yes | Price yes; head fit NO |
| 18 | Ball bearing | 6804ZZ 20x32x7 (CAD model measured 19.99/32.19/7.0), Motoforti 10-pack | 3 | 10 | 10 | 7.74 | Amazon | https://www.amazon.com/dp/B0D99THG1M | Yes | Yes (only 1 left 2026-11-01) |
| 19 | Threadlocker | Loctite 243, 6 mL, P/N 1330799 | 1 | 1 | 1 | 9.90 | Amazon | https://www.amazon.com/dp/B004L439FE | Yes | Yes |

Subtotal: $48.85

## Cables, connectors, wire

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | USB data cable | Micro-B to USB-C, 50 cm, QJJ T1G-W3R | 1 | 1 | 1 | 5.00 | Amazon | https://www.amazon.com/dp/B0B67NKCSW | Yes | Price yes; length vs route NO (CABLE_MAP W12) |
| 21 | Mini-SPOX housing | Molex 50-37-5033, 3 pos 2.5 mm (mates STS3215 5264 sockets) | 3 | 10 | 1 | 1.40 | Mouser | https://www.mouser.com/c/?q=50-37-5033 | Yes | Yes |
| 22 | Mini-SPOX crimp terminal | Molex 08-70-1040 (5263, 22 to 28 AWG) | 9 | 30 | 1 | 6.90 | Mouser | https://www.mouser.com/c/?q=08-70-1040 | Yes | Yes |
| L5 | Power wire 16 AWG | BNTECHGO silicone red and black 25 ft each | 1.7 m | 1 | 50 ft | 19.98 | Amazon | https://www.amazon.com/dp/B01MCRY7OT | Yes | Yes |
| 23 | Wire 20 AWG | BNTECHGO silicone red 25 ft and black 25 ft | 1.6 m | 1 | 50 ft | 12.48 | Amazon | https://www.amazon.com/BNTECHGO-Gauge-Silicone-Wire-Temperature/dp/B01F8PO5XE | Yes | Yes |
| 24 | Wire 22 AWG | BNTECHGO silicone 6 colors 25 ft each | 1.0 m | 1 | 150 ft | 16.98 | Amazon | https://www.amazon.com/BNTECHGO-Silicone-Spool-Color-100ft/dp/B09X4KY56S | Yes | Yes |
| 25 | Wire 26 AWG | BNTECHGO silicone 7 colors 25 ft each | 9 m | 1 | 175 ft | 15.98 | Amazon | https://www.amazon.com/dp/B08F9CF85N | Yes | Yes |
| 26 | Heat shrink | Wirefy 3:1 adhesive lined, 180 pcs | 1 | 1 | 180 | 14.99 | Amazon | https://www.amazon.com/Wirefy-180-Heat-Shrink-Tubing/dp/B084GDLSCK | Yes | Yes |

Subtotal: $93.71

## Print material

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 27 | PLA | Overture Easy PLA 1.75 mm 1 kg, black (need 1304 g sliced, 1.5 kg with 15% spare) | 1.5 kg | 2 | 1 kg | 29.98 | Amazon | https://www.amazon.com/dp/B09LCK7QJ2 | Yes | Yes |
| 28 | TPU | Overture TPU 95A 1.75 mm 1 kg, black (need 35 g; hardness not stated upstream) | 35 g | 1 | 1 kg | 23.99 | Amazon | https://www.amazon.com/dp/B0BGMP1MZ7 | Yes | Price yes; hardness BLOCKER (GAPS A8) |

Subtotal: $53.97

## Expression (optional upstream)

| # | Item | Spec | Need | Buy | Pack | Line $ | Supplier | Link | Ships to USA | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | Speaker | 8 ohm small speaker (upstream amazon.fr B086JH2BTD) | 1 | 1 | 1 | 6.00 | not chosen | (none) | Yes | BLOCKER: model and size vs speaker_interface |
| E2 | I2S amplifier | Adafruit MAX98357A 3006 | 1 | 1 | 1 | 5.95 | Adafruit | https://www.adafruit.com/product/3006 | Yes | Price yes; mount NO (not in CAD) |
| E3 | LEDs | eyes 2 + projector 1, type and resistor not stated | 3 | 1 pack | pack | 8.00 | not chosen | (none) | Yes | BLOCKER |
| E4 | Eye diffusers | not specified | 4 | 1 pack | pack | 8.00 | not chosen | (none) | Yes | BLOCKER |
| E5 | Projector reflector | flashlight reflector (aliexpress upstream) | 1 | 1 | 1 | 3.00 | not chosen | (none) | Yes | BLOCKER |
| E6 | Camera | Pi camera, not in CAD | 1 | 1 | 1 | 15.00 | not chosen | (none) | Yes | BLOCKER |

Subtotal: $45.95

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
| Robot | 518.74 |
| Fasteners and mechanical | 48.85 |
| Cables, connectors, wire | 93.71 |
| Print material | 53.97 |
| Expression (optional upstream) | 45.95 |
| Tools (one-time) | 138.67 |
| Build total (robot + fasteners + cables + filament) | 715.27 |
| Build + expression pack | 761.22 |
| Build + expression + tools | 899.89 |

Previous BOM (before this audit): core $684.99, grand $730.94 with lab changes. The build total now adds fasteners, inserts, bearings, filament, wire, connectors and heat shrink that were missing or unverified, and moves the Castle Link to Tools.

Not costed (not verified, BLOCKER for exact cost): shipping and order minimums (Bolt Depot, Mouser, DigiKey, CNC Kitchen), sales tax, a USB-C PD supply for the Pinecil, a 16 to 20 AWG stripper, a multimeter, digital calipers, a heat gun or lighter for heat shrink.

## Contingency (not in totals)

| # | Item | Qty | $ | Trigger |
|---|---|---|---|---|
| X1 | Extra Molex 50-37-5033 housings (Mouser $0.14) | 20 | 2.80 | Kit 15 cm servo cables too short on test fit (CABLE_MAP S-hops) |
| X2 | Extra Molex 08-70-1040 terminals (Mouser $0.23) | 60 | 13.80 | Same as X1 (10 made leads at 22 AWG) |
| X3 | 1 m Micro-B to USB-C cable | 1 | not priced | USB route W12 longer than 50 cm on test fit |

## Removed from the previous BOM

- Barrel jack lead (old row 12): the lab build feeds the adapter through its screw terminal H1, so 0 needed.
- Braided cable sheath (old row 21): not required by any measured route; price was unverified. Dropped.
- Adafruit 4646 BNO055: replaced by 2472 because 4646 holes do not match the CAD pilots (MOUNTING.md).
- Castle Link V4 moved to Tools.

## BLOCKERS that affect this BOM

See HARDWARE_AUDIT.md section 6 for the full list with what is needed to clear each one.
- 1 Smart serial bus servo: Price yes; stock at order time NO
- 3 Compute: BLOCKER: out of stock 2026-11-01
- 4 microSD: BLOCKER: pick exact model and link
- 8 2S BMS: Yes; fit in CAD pocket NO (see MOUNTING)
- 10 Power switch: BLOCKER: no rated part chosen
- 11 USB-C 2S charger: Price yes; hole pattern vs CAD NO
- 13 Foot contact switch: Price yes; foot mount NO (not in CAD)
- 14 Antenna servo: Price yes; lead length NO
- L3 Inline fuse holder: Price yes; stock NO
- L4 Fuse: NO (US price from EUR listing)
- 17i M2.5x10 SHCS: Price yes; head fit BLOCKER (recess 4.0 mm, head 4.5 mm)
- 17h M2x5 self-tapping: Price yes; head fit NO
- 20 USB data cable: Price yes; length vs route NO (CABLE_MAP W12)
- 28 TPU: Price yes; hardness BLOCKER (GAPS A8)
- E1 Speaker: BLOCKER: model and size vs speaker_interface
- E2 I2S amplifier: Price yes; mount NO (not in CAD)
- E3 LEDs: BLOCKER
- E4 Eye diffusers: BLOCKER
- E5 Projector reflector: BLOCKER
- E6 Camera: BLOCKER
