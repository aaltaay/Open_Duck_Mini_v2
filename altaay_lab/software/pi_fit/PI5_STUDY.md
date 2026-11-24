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
| PCB thickness | not a called-out dimension | BLOCKER |

The current mount is in the head (MOUNTING.md). A box of this outline, plus the cooler height below, hits the head shell: 225 triangles (CAD check only). The head shell is 199.8 by 197.3 by 59.4 mm (CAD check only, print/head.stl). The seat moves to the body.

The cooler is the official Active Cooler. Drawing: https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-mechanical-drawing.pdf . Outline 43.50 by 42.50 mm, height 12.70 mm (cited). It clips on with spring pins and takes 5 V from the fan header (cited, product page: 1.09 CFM, 8000 rpm plus or minus 15%). The heating note (https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/) says throttling starts at 80 C and the hard limit is 85 C, and that a heavy load without the fan reaches that limit. With the cooler, the same note's stress test stayed near 60 to 63 C. Those temperatures are the open-bench test in that note, not the duck body.

The seat is a printed plate, 2.4 mm, with four bosses 5 mm tall and 2.0 mm pilots, the same pilot the other electronics use (MOUNTING.md). The four holes are the drawing holes. The USB short edge faces forward. The header faces left. The MIPI edge faces right, toward the side the neck can leave.

| Fit | Value | Label |
|---|---|---|
| Seat origin, print frame, mm | x -35, y -24, z -58 | CAD check only |
| Keep-out box | 85 by 56 by 15.1 mm | CAD check only. 15.1 is 12.70 cooler plus 2.4 plate. PCB thickness is not included |
| Clearance to body shells and trunk_top | 4.5 mm | CAD check only. The rule used was 2 mm |
| Head | does not fit | CAD check only |

Shells checked: body_middle_top, body_middle_bottom, body_front, body_back, trunk_top, and the head for the rejected pose. Servo meshes were not in that intersection test. Clearance to the servo cases is BLOCKER until those meshes are in the same check. The plate STL is altaay_lab/cad/pi5_seat/pi5_seat.stl. The picture is altaay_lab/cad/pi5_seat/pi5_seat_in_body.png.

## Centre of mass and the walk

The walk in the shared lab gym was not re-run. MuJoCo is not what this check ran. The fore-aft margin in sim/ADDED_MASS_SIM.md table 7 is about 4 to 6 mm behind the estimate (sim pass only).

Pi 5 mass was not on the product page that was read: BLOCKER. The Zero board is 10.0 g (cited, Adafruit 5291, sim/mass_budget.py). The whole-robot mass used here is 2.949 kg (CAD mass model, DECISIONS.md D66, not a scale). The old position is the head shell centre. The new position is the seat box centre.

| Assumed Pi 5 mass | Fore-aft shift | Vertical shift | Label |
|---|---|---|---|
| 40 g | +0.033 mm (forward) | -1.145 mm | calc only |
| 50 g | +0.058 mm | -1.310 mm | calc only |
| 60 g | +0.083 mm | -1.474 mm | calc only |

The shift is forward, so it does not spend the backward margin. It is also far smaller than that 4 to 6 mm. That is not a walk pass.

Straight line from the head shell centre to the seat centre is 190.3 mm (calc only). That is not a cable route.

## Power

Set points stay the netlist. None of them move.

| Set point | Value | Label |
|---|---|---|
| 5 V rail | 5.00 V, domain 4.80 to 5.20 V | cited, netlist domain 5V, Pololu D30V30F5 4% accuracy |
| Pack | 9.0 to 12.6 V | cited, netlist PACK_9V0_12V6 |
| Walk stop | 10.0 V | cited, D65, netlist walk_stop_v |
| Servo rail | 12.0 V, domain 11.52 to 12.48 V | cited, netlist SERVO_12V0, i7C plus or minus 4% |

The Pi 5 product page asks for 5 V / 5 A DC on USB-C, with Power Delivery (cited, https://www.raspberrypi.com/products/raspberry-pi-5/). The FAQ on that page repeats the 5 V 5 A recommendation.

U3 is the Pololu D30V30F5 (netlist). The product page lists a typical maximum of 3.4 A at 30 V in, and says the typical maximum continuous current is 3 A to 4 A depending on input voltage (cited, https://www.pololu.com/product/4892). 5 A is above that 3 A to 4 A band. The graph point at the pack window 9.0 to 12.6 V was not read off the picture: BLOCKER for the exact amp at 12 V. It is not needed to see that 5 A is outside the published band. The duck also feeds the SG90s and the amp from the same 5 V splice (netlist domain 5V). Those currents are blank in the netlist cable rows: BLOCKER for the sum. The Pi's 5 A alone is already over U3.

The 5.00 V set point can stay. The part cannot. The proposed replacement is a 5.0 V regulator whose cited continuous current at 9.0 to 12.6 V in is at least 5 A, with accuracy inside 4% so the domain stays 4.80 to 5.20 V. Pololu's D30V30F5 page points at the D36V50Fx family for higher power. A SKU was not chosen, and its graph was not read: BLOCKER.

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
| Replace line 9 | 5.0 V regulator, at least 5 A from 9.0 to 12.6 V | accuracy inside 4%, so the 4.80 to 5.20 V domain stays | BLOCKER | SKU not chosen. D36V50Fx is the family Pololu names, not a pick |
| Screws | four M2.5x6 instead of the diagonal pair | same line 17f screw | no new line | Buy 20 already covers a Need of 15. Proposed only |

The printed seat is not a bought line.

## Still open

- Pi 5 mass. BLOCKER.
- PCB thickness. BLOCKER.
- Servo-case clearance in the same mesh check. BLOCKER.
- Routed camera length, USB cable price, cooler price, regulator SKU. BLOCKER.
- Exact D30V30F5 current at 9.0 to 12.6 V, and the SG90 plus amp sum. BLOCKER. The 5 A miss against the 3 A to 4 A band is not blocked.
- A measured Pi 5 idle watt, and a CoreMark iterations/s for the Pi 5. BLOCKER.
- Voice peak on the 2 GB cap, re-measured. BLOCKER. The prior 467 MiB figure is the one that fits under 2048.
- gpiochip and pwmchip indexes on a Pi 5. BLOCKER.
- The walk was not re-run. The fore-aft shift above is calc only.
