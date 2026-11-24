# Pi 5 seat and power study

Written 2026-11-24 for Ahmed to approve. The BOM files were not edited. D61 was not edited. The charging mat stays nest v2.

Nothing here ran on a duck. A number is one of: cited, calc only, CAD check only, measured in emulation, measured on the fit host, sim pass only, or BLOCKER. A sim is not a hardware pass.

The board is a Raspberry Pi 5, 2 GB. Ahmed chose it in place of the Pi Zero 2 W. The Zero fit result still stands: 467 MiB peak against 417 MiB that Bookworm Lite gives Linux (measured in emulation, FIT.md).

## Seat

The official drawing is RP-008347-DS-1 (https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf). The sheet says the figures are approximate and are not production data.

| Item | Value | Label |
|---|---|---|
| Board outline | 85 mm by 56 mm | cited, the drawing |
| Mounting holes | four, diameter 2.7 mm | cited, the drawing |
| Hole pitch | 58 mm by 49 mm | cited, the drawing |
| Left inset | 3.5 mm | cited, the drawing |
| End inset on the 56 mm side | 3.5 mm | calc only, (56 - 49) / 2 |
| Header | 40-pin, along one 85 mm edge | cited, the drawing and the product page ("Raspberry Pi standard 40-pin header") |
| Power inlet | USB-C on the short edge at the 3.5 mm hole end | cited, the drawing |
| USB and Ethernet | the other short edge | cited, the drawing |
| Camera | two 22-pin MIPI connectors on the long edge opposite the header | cited, the drawing and the product page ("2 x 4-lane MIPI camera/display transceivers") |
| PCB thickness | the side view prints component heights (0.45, 3, 3.2, 3.4, 4.1, 4.4) and no laminate thickness | BLOCKER |

The current mount is in the head (MOUNTING.md). A box of this outline, plus the cooler height below, hits the head shell: 225 triangles (CAD check only). The head shell is 199.8 by 197.3 by 59.4 mm (CAD check only, print/head.stl). The seat moves to the body.

The cooler is the official Active Cooler. Drawing: https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-mechanical-drawing.pdf . Outline 43.50 by 42.50 mm, height 12.70 mm (cited). It clips on with spring pins and takes 5 V from the fan header (cited, product page: 1.09 CFM, 8000 rpm plus or minus 15%). The heating note (https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/) says throttling starts at 80 C and the hard limit is 85 C, and that a heavy load without the fan reaches that limit. With the cooler, the same note's stress test stayed near 60 to 63 C. Those temperatures are the open-bench test in that note, not the duck body.

The seat is a printed plate, 2.4 mm, with four bosses 5 mm tall and 2.0 mm pilots, the same pilot the other electronics use (MOUNTING.md). The four holes are the drawing holes. The 85 mm side runs left to right. The 56 mm side runs fore and aft. The MIPI long edge faces forward. The header faces back. The USB and Ethernet short edges face the sides.

The flat pose with 56 mm across the hips does not fit. The gap between the hip middle cases is 45.28 mm, from y -22.64 to 22.64 (CAD check only), and the board is 56 mm, a shortfall of 10.72 mm (calc only). Standing the board on edge, tilting it, and moving it above the hip cases were searched. The pose that keeps the official Active Cooler and stays at least 2 mm off the shells and the servos sits behind the hips, in front of the back shell.

| Fit | Value | Label |
|---|---|---|
| Seat origin, print frame, mm | x -82, y -42, z -48 | CAD check only |
| Keep-out box | 56 by 85 by 15.1 mm | CAD check only. 56 is fore-aft, 85 is left-right, 15.1 is 12.70 cooler plus 2.4 plate. PCB thickness is not included |
| Shell clearance | 6.5 mm, to body_middle_bottom | CAD check only. The other four shells are at least 8 mm |
| Servo clearance over the hip sweep | 6.03 mm | CAD check only. Right hip yaw at its +0.524 rad stop, bottom case of hip_roll_assembly_2 |
| Plate lip, same sweep | 4.04 mm | CAD check only. The 2 mm lip, left hip yaw at its -0.524 rad stop |
| Head | does not fit | CAD check only |
| Shell change | none | the stock print shells are not edited |

The hip sweep is 7 yaw samples, 5 roll samples, and 7 pitch samples on each side, including both stops (CAD check only). Servo meshes on the hip chain move with those joints. Trunk, neck, and head servo meshes stay at the zero pose. trunk_top.stl matches the print file on all six faces after +19.0 mm in x and -64.9 mm in z, and that shift is applied to every servo visual.

A lower-profile passive sink was checked because the Active Cooler stack does not fit the further-forward spot under body_middle_top. The ED-Pi5PCOOLER datasheet lists 65 by 58 by 9.3 mm (cited, https://edatec.cn/storage/file/Pi5coolerdatasheet-en.pdf). With the 2.4 mm plate the stack is 11.7 mm and the in-plane keep-out is 85 by 58 mm. That box at x -80, y -30, z 24 clears the shells by 2.0 mm and the servos by 2.64 mm (CAD check only). Its open-bench sysbench figure is 69.6 C against 84.5 C with no sink, at 25 C ambient (cited, the same sheet). That test is not the duck body. The chosen seat keeps the Active Cooler, because 6.5 mm and 6.03 mm are the larger gaps and no new cooler is required.

The plate STL is altaay_lab/cad/pi5_seat/pi5_seat.stl. The picture, with the servo meshes at the two yaw stops, is altaay_lab/cad/pi5_seat/pi5_seat_in_body.png. The green box in that picture is the regulator keep-out.

## Centre of mass and the walk

The official drawing and the product brief print no board mass and no PCB thickness. A shop weight is used below, and it is the 4 GB listing.

The Zero board is 10.0 g (cited, Adafruit 5291, sim/mass_budget.py). The whole-robot mass used for the shift below is 2.949 kg (CAD mass model, DECISIONS.md D66, not a scale). The old position is the head shell centre. The new position is the seat box centre.

Raspberry Pi DK lists Weight 50 g on the Raspberry Pi 5 4 GB page, manufacturer number SC1111 (cited, https://raspberrypi.dk/en/product/raspberry-pi-5-4-gb/, additional information). That is the 4 GB board, not the 2 GB board, and it is a shop weight field, not a figure from the drawing. TME lists gross weight 52.79 g for the 2 GB board SC1642 (cited, https://www.tme.eu/en/details/sc1642/raspberry-pi-minicomputers/raspberry-pi/raspberry-pi-5-2gb-ram/). Gross weight is the listing's shipping figure, so the CoM uses the 50 g shop weight and does not use 52.79 g.

| Pi 5 mass | Fore-aft shift | Vertical shift | Label |
|---|---|---|---|
| 40 g | -0.792 mm (aft) | -1.011 mm | calc only, sensitivity around 50 g |
| 50 g | -0.970 mm | -1.143 mm | calc only, using the cited 50 g shop weight at the new seat centre |
| 60 g | -1.147 mm | -1.274 mm | calc only, sensitivity around 50 g |

The Active Cooler mass is not on its drawing: BLOCKER, so it is not in this shift. The 0.970 mm aft shift is inside the about 4 to 6 mm backward margin in sim/ADDED_MASS_SIM.md table 7 (sim pass only). It does use part of that margin.

The shared lab gym overlay is not in this checkout. The walk was re-run on the public playground scene at pin b9be205, the same scene as sim/SIM_WALK.md (sim pass only). The script is altaay_lab/sim/pi5_seat_walk.py. It takes 10.0 g off head_assembly and puts 50 g on the trunk at (-0.073, 0.0005, 0.02445) m, the new seat centre after the trunk_top shift. Model mass goes from 2.1071 kg to 2.1471 kg (sim pass only).

| | Published SIM_WALK.md | This script, stock mass | This script, new seat |
|---|---|---|---|
| Falls | none | none | none |
| Path | 2.7 m | 2.71 m | 2.57 m |
| Net | 1.32 m | 1.32 m | 1.16 m |
| Forward speed, 4 to 14 s | 0.097 m/s | 0.097 m/s | 0.089 m/s |
| Heading over that 10 s | about 4 deg | 4.2 deg | 6.1 deg |
| Turn in 6 s | 275 deg | 275.2 deg | 268.4 deg |
| Trunk height | 0.154 to 0.169 m | min 0.154 m, min up-vector z 0.992 | min 0.154 m, min up-vector z 0.991 |

The new seat still finishes the 26 s schedule with no fall (sim pass only). Path is 0.14 m shorter than the stock-mass run of the same script, and the straight-walk heading grows from 4.2 deg to 6.1 deg. The video is altaay_lab/sim/pi5_seat_walk_sim.mp4 (SIM in the corner). This is not a hardware pass.

The camera route is a polyline from the forward MIPI edge, under the top shell to x 38 mm, up that open column, and on to the head shell centre. The centerline is 240.6 mm (CAD check only). A 2 mm tube on that line misses the print shells. It is not a harness with connector tails. The 500 mm cable proposed earlier still covers 240.6 mm.

## Power

Set points stay the netlist. None of them move.

| Set point | Value | Label |
|---|---|---|
| 5 V rail | 5.00 V, domain 4.80 to 5.20 V | cited, netlist domain 5V, Pololu D30V30F5 4% accuracy |
| Pack | 9.0 to 12.6 V | cited, netlist PACK_9V0_12V6 |
| Walk stop | 10.0 V | cited, D65, netlist walk_stop_v |
| Servo rail | 12.0 V, domain 11.52 to 12.48 V | cited, netlist SERVO_12V0, i7C plus or minus 4% |

The Pi 5 product page asks for 5 V / 5 A DC on USB-C, with Power Delivery (cited, https://www.raspberrypi.com/products/raspberry-pi-5/). The FAQ on that page repeats the 5 V 5 A recommendation.

U3 in the live netlist is still the Pololu D30V30F5. The product page lists a typical maximum of 3.4 A at 30 V in, and says the typical maximum continuous current is 3 A to 4 A depending on input voltage (cited, https://www.pololu.com/product/4892). 5 A is above that 3 A to 4 A band.

The proposed replacement is the Pololu D36V50F5, item 4091 (cited, https://www.pololu.com/product/4091). Output is 5 V with 4% accuracy, so the domain stays 4.80 to 5.20 V. Input is 5.5 V to 50 V, which covers the pack window. circuitry/NEST_TWO_NET.md keeps this regulator on the pack domain at J5IN and does not put the 15.0 V nest on the 5 V pin. The same input range also covers 15.0 V, so a later nest tie would not need a different part. This proposal does not make that tie. The table's 5.5 A is at 36 V in. On the current graph (picture 0J10751) the 5 V trace reads about 7.5 A near 5 to 6 V in and about 8.2 A near 12 V, so across 9.0 to 12.6 V it is about 7.5 A to about 8.2 A (chart read). Dropout on the 5 V trace is about 1.0 V to 1.1 V at 5 A (chart read, picture 0J10753), so 9.0 V in still clears it. Price $44.95, 0 in stock, rationed, backorders allowed (cited). The full sum, the header-pin limit, and the proposed netlist block are in software/pi_fit/PROPOSED_BOM_CHANGES.md. The live netlist was not edited.

The 5 V loads, from the sheets: Pi 5 supply allocation 5 A (cited, product page; the cooler is on the fan header, so it is inside that 5 A), two SG90 stalls 1.500 A (calc only from 750 mA plus or minus 10% at 4.8 V on the SG90 specification that prints a stall current), MAX98357A quiescent 3.35 mA maximum at 5 V (cited). Sum 6.503 A, or 6.653 A at the high stall tolerance (calc only). Speaker current is not in the quiescent figure: BLOCKER. 6.653 A is under the chart-read floor of about 7.5 A and over the 6 A combined header-pin rating, so the power wires are soldered, as that page says.

The whitepaper minimum band used in BOARDS.md is 4 W to 5 W (cited, RP-010139-WP table 1). A measured idle watt for the duck's image is BLOCKER. The soak below uses 5.0 W, the high end of that minimum band, not the 25 W that 5 V times 5 A would be. 25 W is the supply rating, not a measured draw.

## Hours awake

The Zero soak computer term is 1.75 W (0.350 A times 5 V, plant.py). This run keeps every other set point. It uses 5.0 W for the computer, and it adds the 3.25 W difference on top of the 5.144 A walk mean (the published mean did not include a Pi 5). Sim pass only. Seed 1, three simulated days, same script as AUTONOMY.md.

| | Zero term, 1.75 W | Pi 5 term, 5.0 W |
|---|---|---|
| Hours awake | 23.211 | 21.624 |
| Minimum pack | 10.665 V | 10.627 V |
| Dock attempts | 24 | 25 |

The drop is 1.588 hours over the three simulated days (calc only from those two sim runs). About half an hour a day. The pack still stops above the 10.0 V walk stop in this seed. A heavier real draw, up toward the 5 A supply rating, would shorten this further, and U3 cannot feed that rating.

## Software

The Runtime file antennas.py is not modified. The ear overlay line stays:

`dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`

`install_pi.sh --pi5` records the board as pi5, names lgpio (or gpiod) for GPIO, and names picamera2 for the camera. It does not install RPi.GPIO on that path. `--mock` still fills a prefix and does not call apt. The default mock, without `--pi5`, is the Zero path.

`day_one.py --pi5` uses the same mock bench. On a live Pi 5, eyes go through software/pi_gpio.py (lgpio, then gpiod) and the camera frame goes through software/pi_camera.py (picamera2). The gpiochip number defaults to 4 and can be set with ODM_GPIO_CHIP. That number is a first-boot check: BLOCKER until it is read on a Pi 5. The PWM chip index on RP1 is the same kind of check. hw_pwm.py already takes ODM_PWM_CHIP. The index was not read here: BLOCKER.

The 40-pin map in the netlist does not change. GPIO12 and GPIO13 stay the ear PWM pins.

## Proposed BOM delta

Not applied. Prices are what the cited pages showed. Nothing was bought.

| Action | Item | Spec | Price | Note |
|---|---|---|---|---|
| Replace line 3 | Raspberry Pi 5, 2 GB | 85 by 56 mm, 2 GB LPDDR4X, 2.4 GHz Cortex-A76, RP1 | $77.50 | cited, the 1 Oct 2026 price note already in BOARDS.md. Not a new cart read |
| Add | Active Cooler | 43.50 by 42.50 by 12.70 mm, 5 V fan header | BLOCKER | official page names resellers and does not print a dollar figure |
| Replace the camera cable | Adafruit 5820 | 500 mm, 22-pin 0.5 mm to 15-pin 1 mm, for Pi 5 | $2.50, in stock | cited, the 5818 page lists the 500 mm option at $2.50 (https://www.adafruit.com/product/5818). The 200 mm cable is $2.70 and in stock, and the 300 mm was out of stock. Straight line is 190.3 mm (calc only), so 200 mm has 9.7 mm of straight-line slack and no neck bend. Routed length is BLOCKER |
| Replace line 20 | USB-A to USB-C data cable | Pi 5 USB-A to the Waveshare adapter USB-C | BLOCKER | the current line is USB-C to Micro-B (Adafruit 3878). A listing for the new cable was not read |
| Replace line 9 | Pololu D36V50F5, item 4091 | 5 V, 4% accuracy, 5.5 to 50 V in, chart read about 7.5 A to 8.2 A at 9.0 to 12.6 V in | $44.95, 0 in stock, backorders allowed | cited, https://www.pololu.com/product/4091. Proposed only. See software/pi_fit/PROPOSED_BOM_CHANGES.md. The live netlist still says D30V30F5 |
| Screws | four M2.5x6 instead of the diagonal pair | same line 17f screw | no new line | Buy 20 already covers a Need of 15. Proposed only |

The printed seat is not a bought line.

## Still open

- Official Pi 5 mass, and the 2 GB board's own mass. The 50 g figure is a 4 GB shop weight. BLOCKER for an official mass.
- PCB thickness. The drawing's side view has no laminate callout. BLOCKER.
- Servo clearance at the chosen seat is 6.03 mm over the hip sweep, and 4.04 mm at the plate lip (CAD check only). No shell change.
- Camera centerline is 240.6 mm (CAD check only). Connector tails and the bend radius are not in that line. USB cable price and Active Cooler price remain BLOCKER. Active Cooler mass is not on its drawing, so the CoM above is the board only.
- Speaker current of the MAX98357A at the 8 ohm load. BLOCKER. The stall sum without it is 6.503 A (calc only).
- A measured Pi 5 idle watt, and a CoreMark iterations/s for the Pi 5. BLOCKER.
- Voice peak on the 2 GB cap, re-measured. BLOCKER. The prior 467 MiB figure is the one that fits under 2048.
- gpiochip and pwmchip indexes on a Pi 5. BLOCKER.
- The shared lab gym overlay was not in this checkout. The walk above is the public playground scene (sim pass only).
- The D36V50F5 keep-out clears by 4.5 mm to the shells and 6.21 mm to the hip sweep (CAD check only). The live netlist part is still the D30V30F5 until Ahmed changes it.
