# BOM: Open Duck Mini v2 (US sourcing)

Upstream BOM: https://docs.google.com/spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc (single sheet 'Feuille 1', EUR, EU/China sellers). Upstream core total 398.10 EUR (331.10 EUR lowest).

Prices in USD, checked 2026-11-01 via web search unless marked (not verified). No shipping, tax or tariffs included. Pack-only items are costed at the pack price.

| # | Part | Qty | Exact model | Unit USD | Line USD | US seller | Ships to USA | Origin | Warranty / longevity | Continuous rating | Single source | Backup |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Smart serial bus servo | 14 | Feetech STS3215 7.4V 19 kg.cm (ST-3215-C001, 1:345). Variant confirmed by evidence (about 85%), see GAPS A1 and SERVO_DEEP_DIVE.md | 20.00 | 280.00 | https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html | Yes (Seeed ships to US; stock and warehouse origin at order time not verified) | China | Feetech: 12 mo quality, 6 mo for motor, gears, housing; round-trip freight paid by buyer outside mainland China; over-voltage voids | Rated 6.5 kg.cm (0.64 Nm) @6V per Feetech; Seeed page says 5 kg.cm; stall 19.5 kg.cm @6V; sim forcerange 3.23 Nm | Yes (Feetech only maker) | RobotShop C044/C046 $22.76 to $22.83 (restocking) |
| 2 | Servo bus adapter | 1 | Waveshare Bus Servo Adapter (A), SKU 25514 | 4.99 | 4.99 | https://www.waveshare.com/bus-servo-adapter-a.htm | Yes (ships from China/HK; verify at checkout) | China | Not published (not verified) | n/a | Yes | Amazon.com 2-pack B0DK79JNNK $19.99 |
| 3 | Compute | 1 | Raspberry Pi Zero 2 W (512 MB) | 19.05 | 19.05 | https://www.adafruit.com/product/5291 | Yes, but OUT OF STOCK at Adafruit and PiShop.us on 2026-11-01 | UK design (Raspberry Pi Ltd) | Raspberry Pi statutory/limited warranty (term not verified) | n/a | Yes | PiShop.us $17.25 (OOS); eBay ~$82+ |
| 4 | microSD card | 1 | SanDisk 32 GB class 10/A1 (model not fixed upstream) | 8.00 | 8.00 | (not verified, any US retailer) | Yes | Various | Maker warranty | n/a | No | any A1 card |
| 5 | IMU | 1 | Bosch BNO055 breakout, Adafruit 4646 (STEMMA QT) or 2472 | 29.95 | 29.95 | https://www.digikey.com/en/products/result?keywords=adafruit%204646 (link pattern not verified, DigiKey blocks bots) | Yes (DigiKey/Mouser in stock per TrustedParts) | USA board, German chip | Adafruit standard (not verified) | n/a | No | Mouser 485-4646 $29.95 |
| 6 | Li-ion cell | 2 | Molicel INR18650-P30B 3000 mAh 30 A | 8.99 | 17.98 | https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery | Yes (US retailer) | Taiwan | Retailer policy (not verified) | 30 A continuous discharge (Molicel) | No | Molicel P28A, Samsung 30Q |
| 7 | 2S cell holder | 1 | 2x18650 series holder with leads (upstream: CABLEPELADO, amazon.fr) | 9.99 | 9.99 | https://www.amazon.com/dp/B09WCT8672 | Yes | China | None stated | Spring contacts, current limit not published (issue #51) | No | Spot-welded 2S pack |
| 8 | 2S BMS | 1 | 2S 20A balanced BMS (upstream: JZK, amazon.fr B09VGH38Y5) | 11.99 | 11.99 | https://www.amazon.com/AITRIP-Lithium-Battery-Charger-Balance/dp/B08NSTF8CT | Yes | China | None stated | 20 A (seller claim) | No | Teyleten B0F3TMC5JT |
| 9 | 5V regulator | 1 | HENGE 4A UBEC 5V (upstream: alibaba) | 17.29 | 17.29 | https://www.amazon.com/Malockos-HENGE-Aeroplane-Helicopter-Mulitcopter/dp/B0DBPXNN7N | Yes | China | None stated | 4 A (seller claim) | No | Pololu D36V28F5 $23.95 (USA, full spec) |
| 10 | Power switch | 1 | Small rocker switch (upstream amazon.fr B0CH3JCQM5, model not named) | 6.00 | 6.00 | (not verified) | Yes | China | None | Not published | No | any rated >=10 A |
| 11 | USB-C 2S charger | 1 | USB-C to 8.4V 2S charge module (upstream amazon.fr B0BWTK7SVN, model not named) | 7.99 | 7.99 | https://www.amazon.com/Adeept-18650-Charge-Charging-Board/dp/B0BJTW4QBR | Yes | China | None | ~1 A charge, no balancing (seller) | No | any 2S USB-C PD charger board |
| 12 | Barrel jack 2.1 mm | 2 | 5.5x2.1 mm male plug | 3.50 | 7.00 | (not verified) | Yes | China | None | n/a | No | any |
| 13 | XT30 pair | 1 | Amass XT30U (10 pairs) | 8.58 | 8.58 | https://www.amazon.com/dp/B08P5HVMYT | Yes | China (Amass) | None | 15 A cont (Amass spec) | No | genuine Amass |
| 14 | Foot contact switch | 4 | Omron SS-10 (BOM qty 4; wiring uses 2) | 1.75 | 7.00 | https://www.digikey.com/en/products/result?keywords=omron%20SS-10 (link pattern not verified) | Yes | Japan brand (Aratas) | Omron/DigiKey | 10 A rating | No | Mouser |
| 15 | Antenna servo 9g | 2 | SG90-class 9g servo (Miuzei 10-pack) | 19.99 | 19.99 | https://www.amazon.com/dp/B072V529YD | Yes | China | None | Not published | No | any SG90 |
| 16 | M3 heat-set inserts | 1 | M3 inserts, size not specified upstream (pack) | 10.00 | 10.00 | (not verified) | Yes | China | None | n/a | No | Ruthex/CNC Kitchen |
| 17 | M3 screws | 1 | M3x6, M3x10 and others; exact count TODO upstream | 12.00 | 12.00 | (not verified) | Yes | Various | None | n/a | No | McMaster |
| 18 | Ball bearing | 3 | Size not stated upstream; CAD model is 20x32x7 mm (6804ZZ, inferred) | 2.44 | 7.32 | https://www.amazon.com/dp/B0D99THG1M | Yes | China | None | n/a | No | McMaster 6804 |
| 19 | PLA filament | 1 | ~500 g to 1 kg standard PLA, 15% infill | 20.00 | 20.00 | (not verified) | Yes | Various | n/a | n/a | No | any |
| 20 | TPU filament | 1 | TPU (95A assumed, not stated) for 2 foot soles, 40% infill | 25.00 | 25.00 | (not verified) | Yes | Various | n/a | n/a | No | any |
| 21 | Cable sheath | 1 | braided sleeve (upstream amazon.fr B07PGMKC3T) | 9.00 | 9.00 | (not verified) | Yes | China | None | n/a | No | any |
| 22 | USB cables | 2 | micro-USB to USB-C 15 cm and 50 cm | 6.50 | 13.00 | (not verified) | Yes | Various | None | n/a | No | any |
| 23 | Threadlocker | 1 | Loctite 243 blue | 8.00 | 8.00 | (not verified) | Yes | USA/Germany (Henkel) | n/a | n/a | No | any |
| 24 | Hookup wire | 1 | not specified upstream | 10.00 | 10.00 | (not verified) | Yes | Various | n/a | n/a | No | any |

**Core walking robot total: $570.12**

## Expression package (optional upstream, partly not integrated)

| Part | Qty | Model | Line USD | Link |
|---|---|---|---|---|
| Speaker | 1 | small 8 ohm speaker (upstream amazon.fr B086JH2BTD) | 6.00 | (not verified) |
| I2S amplifier | 1 | Adafruit MAX98357A (3006) | 5.95 | https://www.adafruit.com/product/3006 |
| LEDs eyes + projector | 3 | LEDs (bulk pack) | 8.00 | (not verified) |
| Eye diffusers | 4 | diffusers (bulk pack) | 8.00 | (not verified) |
| Projector reflector | 1 | flashlight reflector (upstream aliexpress) | 3.00 | (not verified) |
| Camera | 1 | Raspberry Pi camera (not integrated upstream) | 15.00 | (not verified) |

**Expression total: $45.95. Grand total: $616.07**

## Lab change lines (Ahmed D3, 2026-11-01 1:09 PM ET: servos never above 7.4 V)

The stock lines above stay as they are. These lines are added on top. Details in POWER.md and WIRING.md.

| # | Part | Qty | Exact model | Unit USD | Line USD | US seller | Ships to USA | Origin | Warranty / longevity | Continuous rating | Single source | Backup |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | Servo buck regulator | 1 | Castle Creations CC BEC Pro, P/N 010-0004-01, set to 7.2 V | 54.95 | 54.95 | https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01 | Yes (Castle, Olathe KS; store shows available 2026-11-01, an older Castle page says temporarily out of stock) | USA brand, assembled in the Philippines | Castle 1 year from purchase, plus non-warranty replacement program | 15 A cont at 2S to 4S with 5 mph airflow, 20 A peak | No | Castle CC BEC 2.0 WP 010-0153-00 $56.95 (9 A cont); Pololu D42V110F6 6 V fixed |
| L2 | BEC programmer (one-time tool) | 1 | Castle Link V4 USB Programming Kit, P/N 011-0173-00 (Windows 10+, Castle Link 2) | 29.95 | 29.95 | https://castlecreations.com/products/accessories-castle-link-v4-psoc-usb-programming-kit-011-0173-00 | Yes (in stock at Castle, Havoc Speed FL, Nitro Hobbies on 2026-11-01) | USA brand, assembled in the Philippines | Castle 1 year | n/a | No | Castle Link V3 is discontinued |
| L3 | Inline fuse holder | 1 | Littelfuse FHAC0001ZXJ, ATO, 20 A, 32 V, 16 AWG leads | 7.74 | 7.74 | Newark (US), search FHAC0001ZXJ (stock not verified) | Yes | USA brand | Littelfuse standard | 20 A | No | DigiKey, Mouser |
| L4 | Fuse | 5 | Littelfuse ATO 15 A 32 V, 0287015.PXCN | 0.45 | 2.25 | DigiKey (price from EUR 0.39 listing, US price not verified) | Yes | USA brand | n/a | 15 A | No | any ATO 15 A from a named brand |
| L5 | Power wire | 1 | BNTECHGO 16 AWG silicone, red and black 25 ft each, SW16A252008F25C2 | 19.98 | 19.98 | https://www.amazon.com/dp/B01MCRY7OT (in stock, ships from Amazon, sold by BNTECHGO-US) | Yes | China (not stated) | Amazon returns until 2027-01-31 | 252 strands 0.08 mm tinned copper, 200 C, 600 V | No | any 16 AWG silicone |

**Lab change total: $114.87** (L2 is a one-time tool: $84.92 without it)

Not costed yet (open):
- Power switch rated 15 A DC or more (stock rocker has no rating). Model not chosen.
- Spot-welded 2S pack, only if the spring holder drop is over about 0.3 V at 10 A (POWER.md section 5).

**Totals with lab changes: core walking robot $684.99, grand total with expression $730.94** (stock: $570.12 and $616.07). No shipping, tax or tariffs.

## Lab rule check for Chinese parts (full spec + real warranty + sim model)

| Part | Full spec incl. continuous rating | Real warranty | Sim model | Verdict |
|---|---|---|---|---|
| Feetech STS3215 | Partial: rated torque published (6.5 kg.cm @6V) but sellers disagree (5 kg.cm on Seeed); no thermal duty curve | 12 mo / 6 mo wear parts, buyer pays round-trip freight from US, over-voltage excluded | Yes: MJCF class sts3215 plus BAM identification | Borderline, Ahmed decision (DECISIONS D2) |
| Waveshare Bus Servo Adapter (A) | Rated 9 to 12.6 V input, used at 7.4 to 8.4 V | Not found | n/a | Fails warranty rule |
| 2S BMS, UBEC, USB-C charger, holder, switch | No datasheet | None | n/a | Fails; US backups needed (Pololu regulator). Servo supply now via Castle CC BEC Pro (lab change L1) |
| SG90 antenna servos | No | None | Antennas not in MJCF | Fails (non-critical) |

Non-Chinese key parts: Pi Zero 2 W (Raspberry Pi Ltd), BNO055 (Bosch chip, Adafruit board), Molicel P30B (Taiwan), Omron SS-10.

