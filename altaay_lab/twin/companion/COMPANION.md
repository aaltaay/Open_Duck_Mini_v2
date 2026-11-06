# Companion hardware: microphones, ears, look at the caller (V1 track 11, D47)

Written 2026-11-05 about 4:55 PM ET (America/New_York). Hardware only (Ahmed, D47): no software, no agent and no gym sim in this track.
Labels: calc only for the acoustics, CAD check only for the seats. Sources are cited per line; [S] means a search result
page (the seller or datasheet page itself was not reachable from this session), [R] means read in full.
Hosts not reachable from this session's web reader: adafruit.com, cdn-shop.adafruit.com, invensense.tdk.com,
community.nxp.com, farnell.com, elemon.com.ar. Every number that only those hosts hold is a BLOCKER below.
Update 2026-11-05 about 7:50 PM ET: adafruit.com, its file host and the Adafruit guide were then read with curl. The
3421 page, its board files, its fab print and the SPH0645LM4H-B datasheet clear BLOCKERs 1 and 2 (section 9). The
real port sits 0.71 mm from the mic centre, so the seats were redrawn on it with taller bosses (section 8), and the
numbers below are the new ones.

## 1. Result

- Pick: **2 discrete I2S MEMS mics, Adafruit 3421 (Knowles SPH0645LM4H), one on each side wall of the head, 121.6 mm
  apart** (120.5 mm before the seats moved to the real port). $13.90 for both (BOM E8, $6.95 each and in stock [R]
  adafruit.com/product/3421, read 2026-11-05 about 7:45 PM ET). Two new GPIO:
  GPIO20 (pin 38) for the mic data and, since D48, GPIO16 (pin 36) for the amp SD pin. The mics share BCLK (GPIO18) and LRCLK (GPIO19) with the MAX98357A, which keeps its DIN on
  GPIO21. Front or back is settled by a head turn (section 3).
- Ears: the 2 antenna SG90s stay and become the ears. No new servo.
- No non-mic direction aid is worth adding for V1 (section 5). The camera already on the head does the last step.
- CAD: per side 2 bosses, 1 port tube and one 1.2 mm sound port in print/head.stl (twin/companion/mic_seat.py):
  CAD check PASS.
- Hazard (one line): the mic wires run next to the SG90 and neck servo leads in the head; keep them away from the 7.2 V
  feed (no extra hazard found).

## 2. I2S and GPIO (netlist wiring/netlist.yaml)

| item | result | source |
|---|---|---|
| Amp and mics on one I2S port | yes. The Pi has one PCM port: BCLK GPIO18, LRCLK GPIO19, DOUT GPIO21 (to the amp), DIN GPIO20 (from the mics). The Pi is the clock master for both directions | [R] raspberrypi/linux rpi-6.6.y googlevoicehat-soundcard-overlay.dts (i2s_clk_producer) |
| One overlay for both | dtoverlay=googlevoicehat-soundcard: the Google AIY voice HAT v1 was this same pair (MAX98357A out, 2 I2S MEMS mics in) | [R] overlays README; [R] sound/soc/bcm/googlevoicehat-codec.c |
| Formats | playback 2 ch, capture 2 ch, 48 kHz only, S32_LE | [R] googlevoicehat-codec.c, voicehat_dai |
| GPIO16 | the overlay drives GPIO16 as the amp SD mode pin (5 ms delay). D48 wires GPIO16 (pin 36) to the amp SD pin (a 6th wire in D10), so the amp is off whenever it is not playing (half duplex; section 11.4) | [R] the overlay (sdmode-gpios GPIO16) |
| New pins | GPIO20 (pin 38) data in, GND pin 39, 3V3 from pin 17 (shared with the D17 foot pull-ups, about 1.5 mA each) | netlist PI pins 38 and 39 |
| GPIO budget | used before: GPIO2, 3, 12, 13, 18, 19, 21, 22, 23, 24, 25, 26, 27. Now also 20 (mic data) and 16 (amp SD, D48). Free: GPIO4 to 11, 14, 15, 17 | netlist; c6_gpio PASS |
| Slots | left board SEL to GND (left slot), right board SEL to 3V (right slot); each DOUT floats in the other slot, so both share GPIO20 | [R] SPH0645LM4H-B Rev B datasheet: SEL high drives DATA while WS is high, SEL low while WS is low, tri-state otherwise; the 100 k pull-down it asks for is for a single mic on the bus |
| Clock range | BCLK = 48 kHz x 64 = 3.072 MHz, inside the 2.048 to 4.096 MHz range; WS must be BCLK/64, and the mode I2S with the MSB one BCLK after WS | [R] datasheet |
| Wires | cable D14, Pi to the left board, 5 wires twisted, cut 150 mm (route 78.3 mm); D15, left board to right board, 5 wires twisted, cut 240 mm (route 148.4 mm, over the head behind the head_roll_mount); 26 AWG from stock | twin/companion/route_mics.py, CAD check only |

## 3. Mic count and layout (calc only)

Inputs: c = 343 m/s; fs = 48 kHz (the codec's only rate), one sample = 20.8 us. The delay estimate is taken at one
tenth of a sample (2.1 us) after peak interpolation: an assumption that depends on the signal to noise ratio, to be
measured on the bench. Angle error of one pair: sigma_theta = c x sigma_tau / (d cos theta). Spatial aliasing for
one pair starts at f = c / (2 d); GCC-PHAT on voiced speech still works above it (broadband), but the main lobe
narrows and side peaks appear, so a larger d is not free.

| layout | spacing in this head | sigma at 0 / 60 / 80 deg off the pair axis normal | aliasing from | 360 deg? | Pi fit |
|---|---|---|---|---|---|
| 2 mics, left and right side walls (the pick) | 121.6 mm, measured on the CAD seats (mic_seats.json) | 0.34 / 0.67 / 1.94 deg; 3.4 deg at whole samples | 1.41 kHz | no: front and back mirror; a head turn of 0.25 rad or more between two readings tells them apart (the two mirror candidates move opposite ways) | 2 slots on GPIO20: fits |
| 3 mics, triangle: left, right, back wall | sides 121.6, about 80, about 80 mm (back seat near x = -90 mm from the head bounds; not seat-checked, the SG90s sit at x = -61) | short pairs 0.52 deg at their best angle; any bearing has one pair near its best | 2.15 kHz (short pairs) | yes | NO on one data pin: 3 slots need TDM mics or a codec |
| 4 mics: left, right, front, back | 121.6 mm and about 180 mm front to back (the front seat must clear the eyes, the camera and the bulbs: not seat-checked) | 0.34 deg and 0.23 deg on the two pairs | 1.41 and 0.95 kHz | yes | NO on one data pin (as for 3) |

Why 2: the I2S data pin carries two slots. The SPH0645LM4H has only left and right slots (no TDM), so a third or fourth
mic needs a 4-channel ADC board (AC108, section 4) or a USB array. For a homebody that is called from a room, the head
turn that settles front and back costs about one second and nothing else; the camera then finishes the look.

Matching needs (calc only):
- Timing: a fixed extra delay dt on one mic biases the angle by c x dt / d. For 1 deg at the front, dt must stay under
  6.2 us, an acoustic path difference under 2.1 mm. The seats are mirror images (0.2 mm mirror error in the CAD), the
  port tubes are the same length, and both mics sample on the same BCLK and LRCLK edge, so the pair is matched by build.
- Mic group delay spread between two SPH0645LM4H parts: not in the Rev B datasheet (BLOCKER; the clap check of
  TEST_PLAN 17.1 shows a fixed lag at 0 deg). Buy both boards in one order.
- Sensitivity spread: GCC-PHAT divides out the magnitude, so a 1 to 2 dB spread hardly moves the delay estimate.
- A wrong slot (SEL) swaps left and right: a sign flip that the bench check catches in one clap (TEST_PLAN note below).

## 4. Mic hardware options

| option | what it is | price | Pi Zero 2 W fit (I2S, GPIO vs the netlist) | mass, size | space in the head | noise next to the mics |
|---|---|---|---|---|---|---|
| A. 2 x Adafruit 3421 SPH0645LM4H (pick) | discrete I2S MEMS boards, bottom port | $13.90 [R] | GPIO20 only; shares the amp clocks; one overlay | 16.51 x 12.7 mm each [R] 3421 board files and fab print; 16.7 x 12.7 x 1.8 mm overall and 0.4 g each [R] product page | on the side walls, 6.05 mm clear of the SG90s (CAD check) | each mic sits beside its ear SG90 (6.05 mm): the ear commands feed the ego-noise model (D49) |
| B. Seeed ReSpeaker 2-Mics Pi HAT (107100001) | WM8960 codec on I2C1 at 0x1a, 2 mics on the board, speaker driver, 3 APA102 LEDs on SPI | about $19 [S] RobotShop and element14 listings; marked retired at one seller [S] | takes the whole 40-pin header on top of the Pi; its codec would replace the MAX98357A; I2C 0x1a does not clash with the BNO055 (0x28/0x29); the LEDs take SPI0; its Grove digital port is GPIO12 and 13, the antenna PWM pins (leave it empty) | 65 x 30 x 15 mm, 12 g net [S] Core Electronics | sits on the Pi in the head floor, the mics look up inside the shell, no wall ports; the mic spacing on the board is not read (BLOCKER) | the mics sit inside the head next to the Pi and the neck servo: muffled and closer to servo noise |
| C. Seeed ReSpeaker 4-Mic Array for Pi (AC108) | 4 mics on a round board, AC108 4-channel ADC, 12 LEDs, no audio out | $24.50 at launch, about $28 now [S]; discontinued at one seller [S] | uses 11 header pins [S] pinout.xyz; whether the MAX98357A can still share the PCM port with the AC108 TDM capture is a BLOCKER | not read (BLOCKER) | a full board over the Pi, spacing set by the board (not read) | as B |
| D. Seeed ReSpeaker USB Mic Array (XVF-3000) | 4 mics, on-board DOA, echo cancel, USB audio | $87.45 [S] RobotShop | USB: the Pi's only OTG port already feeds the servo bus adapter (netlist cable D1), so it needs a hub; no I2S pins | 77 mm disc, 43.6 g net [S] | a 77 mm disc does not fit flat between the side walls at the mic height (about 120 mm inside, but the Pi, the speaker and the neck mount fill the floor) | inside the head, as B |

Pick A: simplest (2 small boards, 1 new pin, the overlay already exists), cheapest ($13.90), and the most reliable
of the four for direction (ports on the outer shell, a known 121.6 mm baseline, no hub, no second codec).

## 5. Non-mic direction aids (comparison only)

| aid | what it adds | cost, mass | worth it for a homebody? |
|---|---|---|---|
| Camera (Camera Module 3, already fitted, BOM E6) | the last step: face or person bearing inside its 66 x 41 deg view (40.1 deg vertical at 16:9 in the dock sim camera) | $0 extra | yes, already there |
| mmWave radar, HLK-LD2450 class | up to 3 people, x and y in the room, azimuth +/- 60 deg, about 6 m, serial out [S] | $8.89 to $14.95 [S]; 15 x 44 mm [S]; mass not read | no for V1: it sees only the front 120 deg, needs the UART (GPIO14, 15 are free) and 5 V, and does not know who spoke |
| UWB | range and angle to a tag | needs a tag on the person | no: the person would have to carry a tag |
| BLE direction finding | angle to a phone or beacon | needs an antenna array and an AoA radio; the Pi Zero 2 W radio has no AoA (not read: BLOCKER) | no |
| PIR | someone moved, no angle | a few dollars (not read) | no: no direction |

## 6. Ears (the two antenna SG90s)

- Range: the Runtime drives them at 50 Hz with 1.0 to 2.0 ms pulses (value -1 to 1; Open_Duck_Mini_Runtime 376de65
  antennas.py). The travel per ms of the Miuzei SG90 (BOM 14) is not in the listing read so far: BLOCKER, measure on the
  bench (TO list). Perk (up), twitch (a flick) and droop are inside that range.
- Speed: the SG90 speed for this listing is not read: BLOCKER, bench item.
- Noise next to the mics: each SG90 is 6.05 mm from its mic board envelope (CAD check). Since D49 the duck listens
  always with the ego-noise model (section 12), which takes the ear commands as an input; holding the ears still
  during a direction capture is the fallback.
- Mount (CAD check only, twin/companion/ear_mount.py and ear_mount.json, 2026-11-05 ET): each ear SG90 hangs under the
  head side plate on its 2 tabs, flat on 7.25 mm of plastic (58.5 mm2 per tab, 0.00 mm gap), with the 2 SG90 bag tab
  screws into blind 1.5 mm pilots 27.5 mm apart that are coaxial with the tab holes (axis 0.4 deg, centre 0.001 mm
  off). The body ends sit in the plate pocket (117.7 mm2 within 0.15 mm, gap 0 to 0.1 mm): that and the 2 screws stop
  the servo turning under the horn load. The output shaft comes out through the plate on the ear joint axis (0.000 mm,
  0.000 deg). Over the full -90 to 90 deg the ear holder and rod clear the shell by 2.02 mm, the mic boards by 10.07 mm
  and the camera by 82.8 mm. The same in print/head.stl, twin/companion/stl/head.stl and the viewer mesh. The viewer
  used to explode the servos away from their plate, with their screws left in the shell, so they looked loose there;
  since 2026-11-05 (ET) they ride with the shell and part along the ear axis only (viewer/make_viewer_data.py EAR_PULL).
- No new servo, no new pin (GPIO12 and 13 stay the antenna PWM pins).
- Lab rule note: the SG90s are PWM hobby servos (GAPS.md B10a); as ears they keep that known gap.

## 7. Look at the caller: what the hardware allows

- Head yaw: the walk policy was trained with head yaw commands up to +/- 1.5 rad (Open_Duck_Playground b9be205
  joystick.py line 99); neck pitch -0.34 to 1.1 rad, head pitch +/- 0.78 rad (lines 97, 98). STS3215 C001 no-load
  5.45 rad/s at 7.4 V (SERVO_DEEP_DIVE.md); the walk loop clips targets at 5.24 rad/s.
- Past the head range the body turns. A quick gym probe before the scope change (sim pass only, not kept): with the
  head at 0, 0.5 and 1.0 rad, the stock policy turned 135, 64 and 0 deg in place in the same time, so the head should
  be near straight while the body turns.
- CPU (calc only): a 2-channel GCC-PHAT of a 0.5 s block took 21 ms on the build box (x86, 2.8 GHz); the Pi Zero 2 W
  number is a BLOCKER (bench), and it runs on a core next to the 50 Hz walk loop, not in it.

## 8. CAD seats (CAD check only; twin/companion/mic_seat.py, mic_seats.json, stl/head.stl)

- Update 2026-11-05 about 7:50 PM ET: the seats are drawn on the 3421 board files. The board outline and holes match
  the 6049 stand-in, but the sound port sits 0.71 mm from the mic centre: the PCB hole of footprint pad 3 (GND,
  drilled 1.025 mm) is at (8.255, 7.822) mm from the outline corner. The fab print gives "Port" 0.31 in above the pad
  edge. Before, the tube and the wall port were centred on the mic centre (7.112). The product page's 1.8 mm overall
  height points to a PCB of about 0.8 mm (calc only). With 3.0 mm bosses and 5.0 mm pilots, the M2x6 tip would then
  pass the pilot bottom by 0.2 mm, so the bosses are now 3.5 mm high with 5.6 mm pilots.
- Seat search on the inner side walls of print/head.stl: 15-ray plane fit per seat; chosen x = -37.5, z = 202 mm (URDF
  world; -40 before, the taller envelope moved it), wall 3.21 mm thick, flatness 0.00 mm; the right seat is the mirror
  (0.2 mm off).
- Per board: 2 bosses 5.0 mm, 3.5 mm high, pilots 1.65 mm x 5.6 mm (the camera pilot diameter, D34), M2x6
  self-tapping from the BOM 17h kit (it holds 50 M2x6). Engagement 5.2 to 4.4 mm with a 0.8 to 1.6 mm PCB (rule
  4.0 mm, Westfield table 2); tip gap 0.4 to 1.2 mm (rule 0.25 mm); 0.9 mm of wall left past the pilot. A port tube
  4.0 OD, 2.0 bore, 3.5 mm long, sits on the PCB port, and a 1.2 mm sound port goes through the wall on the same axis.
  The 2.0 mm bore takes the 1.025 mm PCB hole with 0.49 mm to spare each side, against the 0.25 mm play of an M2
  screw in a 2.5 mm hole.
- D42: the 2 screws of each board are a mirror pair about the board centre line; the two boards mirror each other.
- D39: both board holes take a screw; the sound port is a sound hole (kept open by D39).
- Clearance of the board envelope (PCB, parts, the wire bend; 0.8 to 1.6 mm PCB): 6.05 mm to the SG90s, 15.1 mm to
  head_bot_sheet, 26.9 mm to the speaker stand; shell 3.5 mm (the boss gap). Watertight, +285.6 mm3 of PLA.
- The edited head.stl is 2.45 MB (under the 5 MB rule).
- fasteners.json F356 to F359; MOUNTING.md row; viewer placeholders mic_l and mic_r (audit/placements.json).

## 9. BLOCKERs

1. (cleared 2026-11-05 about 7:50 PM ET) adafruit.com/product/3421 read with curl: $6.95 each (1 to 9), in stock,
   16.7 x 12.7 x 1.8 mm overall, 0.4 g. The 3421's own board files (github.com/adafruit/Adafruit-I2S-Microphone-
   Breakout-PCB) and its fab print give the outline (16.51 x 12.7 mm, 0.65 x 0.5 in), the holes (2.5 mm, 11.43 mm
   apart, 2.54 mm in from the edges, as the stand-in) and the port.
2. (mostly cleared 2026-11-05 about 7:50 PM ET) The SPH0645LM4H-B Rev B datasheet (the PDF on the Adafruit product
   page) is read:
   - clock 2.048 to 4.096 MHz (3.072 used);
   - AOP 120 dB SPL at 10 % THD at 1 kHz;
   - SNR 65 dB(A), sensitivity -26 dBFS (-29 to -23);
   - 24-bit I2S with 18-bit precision, the tri-state per SEL, a 0.325 mm acoustic port.
   The PCB port position is read from the board files, and the seats are redrawn on it (section 8).
   Still open:
   - the PCB thickness: not published; the 1.8 mm overall height points to about 0.8 mm; 0.8 to 1.6 mm is checked
     and the screws fit the whole range;
   - the group delay spread between two parts: not in the datasheet.
   One parts index [S] and a DigiKey search result [S] list the bare SPH0645LM4H as obsolete; Adafruit shows the
   board in stock.
3. (cleared 2026-11-05 about 5:15 PM ET; lengths updated 7:50 PM ET) Cables D14 and D15 are routed in 3D
   (twin/companion/route_mics.py, mic_routes.json: D14 78.3 mm, D15 148.4 mm). Both clear the parts by 1 mm or more,
   stay 17 mm or more from the P13 pack feed and 5 mm or more from the SG90 leads, and are drawn on sheet 4 with D13
   (the sheet generator runs again: c10 PASS).
4. SG90 travel per ms and speed for the Miuzei listing (bench).
5. Servo and SG90 noise at the mic ports, and the Pi Zero 2 W CPU time for the direction estimate (bench).
6. Options B to D: board spacing, mass and the AC108 and amp port sharing not read.

## 10. Bench checks (add to TEST_PLAN when the parts come; nothing bought)

1. One clap at 1 m at 0, +60 and -60 deg: the left channel leads for +60 (slot check).
2. A voice at 1.5 m on 12 bearings, 30 deg apart, head still and after a 0.3 rad head turn: front or back right on all 12.
3. Record 10 s with the ears moving, the neck moving and all still: the noise floor at the ports. (Since D49 these
   checks and the full ego-noise recording protocol are TEST_PLAN 17.)

## 11. D48: accuracy, self-noise and the hybrid (written 2026-11-05 about 5:25 PM ET)

Ahmed asked for accuracy, the right mic positions, a quiet listen next to the speaker and the servos, and a Bluetooth
direction sensor for a mixed answer (D48). Hardware first; no software is built.

### 11.1 Method for 2 mics, a head turn and the camera (calc only)

| method | what it needs | with 2 mics | source |
|---|---|---|---|
| GCC-PHAT | one cross-correlation per pair, PHAT weights | the right tool | [S] Knapp and Carter 1976; arXiv 2405.02991 (SRP tutorial): "the GCC function with PHAT weights is essentially the same as the SRP function with PHAT weights given a pair of microphones" |
| SRP-PHAT | a grid of steering directions, sums the pair correlations | equal to GCC-PHAT for one pair; gains only with 3 or more mics | same tutorial |
| MUSIC | a spatial covariance per frequency band, more mics than sources | with 2 mics it can resolve one source only, is narrowband per band and costs more CPU; no gain here | [S] the same search: MUSIC works best on narrowband signals; SRP-PHAT is cheaper online |

The pick is GCC-PHAT on the pair, and the head turn does three jobs:
1. Front or back: the two mirror candidates move apart when the head turns, so a second reading picks one.
2. Triangulation from two head angles: with the 121.6 mm pair, the two readings are a few milliseconds of rotation
   apart, so they give the same bearing twice. That averages noise but does not give range (the baseline is the pair,
   not the turn). Range is not needed: the camera finds the face along the bearing.
3. Accuracy: the pair is most accurate broadside (0.34 deg at one tenth of a sample, section 3) and worst end-on
   (2 deg at 80 deg). Turning the head toward the voice brings the source broadside before the final reading.

Then the camera takes over inside its 66 deg view: a face or person box sets the final bearing to about the face
width (a face at 1.5 m is about 6 deg wide).

Expected real-room error: no measured two-mic figure was read in this session (BLOCKER: the reverberation studies
found, arXiv 2507.07087 and the Virginia Tech thesis on reverberation and DOA, were not opened). What the calc gives:
- the ideal pair: 0.34 deg broadside, 0.68 deg at 60 deg;
- whole-sample timing (no interpolation): 3.4 deg broadside;
- reverberation adds wrong peaks from the walls rather than a small bias; the head turn rejects them (a wrong peak does
  not follow the head);
- the duck's own noise (servos, SG90s, the speaker) adds peaks at the noise source bearing, a fixed bearing in the
  head frame: since D49 the duck listens always with the ego-noise model (section 12); gating on motion (11.4) is
  the fallback.
So the voice only has to put the face inside the 66 deg view (plus or minus 33 deg). The camera does the last step.
Bench check: section 10, item 2.

A third mic (top or back of the head): no.
- One I2S data pin carries 2 slots. A third mic needs a 4-channel ADC (AC108 board, section 4) or TDM mics on a TDM
  capture path, which the googlevoicehat overlay does not set up.
- It removes the front or back turn and helps up and down bearings. A homebody turns its head anyway, and the camera
  finds the face height.
- Cost, if wanted later: one more board, a codec or a USB array, more wires through the head, and a second overlay.

### 11.2 Fit and placement (CAD check only)

- Mic: SPH0645LM4H, bottom port, 3.50 x 2.65 x 0.98 mm, acoustic port 0.325 mm. It takes BCLK of 2.048 to 4.096 MHz
  (3.072 MHz used here), has an SNR of 65 dB(A), a sensitivity of -26 dBFS (-29 to -23) and an AOP of 120 dB SPL
  [R Knowles SPH0645LM4H-B Rev B datasheet, read 2026-11-05 about 7:45 PM ET]. It draws 600 uA typical. Its
  specifications are guaranteed from 0 to 45 C, and it works with lower performance from -40 to 100 C [R]. The thermal
  twin puts the head air at 34 C in a 25 C room and 41 C in a 32 C room with about 3 W of head losses (sim pass only,
  twin/thermal/THERMAL_TWIN.md). That is inside the guaranteed range by 4 K at 32 C, but the D49 audio work adds CPU
  load in the head, and those watts are not measured (BLOCKER). TEST_PLAN 17.3 logs the Pi SoC temperature as an
  upper bound on the head air.
- Board: 16.51 x 12.7 mm, 2 plated 2.5 mm holes 11.43 mm apart, PCB port 1.025 mm at (8.255, 7.822) mm ([R] the
  3421 board files and fab print).
- Port: the wall port is 1.2 mm across through the 3.2 mm wall, then a printed tube 2.0 mm bore x 3.5 mm to the board,
  then the 1.025 mm PCB hole to the mic. Helmholtz estimate (calc only): neck area 1.13 mm2, effective length 4.2 mm
  (3.2 mm + 2 x 0.85 x 0.6 mm end corrections), and a cavity of about 11.0 mm3 (the tube; the PCB hole and the mic
  front volume are not read). That gives a resonance near 8.5 kHz, just above the 300 Hz to 8 kHz of speech. Both
  ports are the same, so the resonance gives no direction bias.
- Spacing: 121.6 mm, the widest the side walls give where the walls are flat (x -50 to -5 mm searched) and clear of the
  speaker stand (right, x 0 to 50) and the side lamp opening (left, x 67 to 95). A wider pair (up to about 167 mm
  further forward) would run into those parts and makes aliasing start lower (1.0 kHz). It gains about 0.1 deg,
  which the camera makes moot. Height: z 202 mm, 27 mm above the head floor plate, mid-height of the side wall, above
  the SG90 bodies.
- No reshape: the seats are mirror images (0.2 mm off) and point straight out of each side. The section and close-ups
  are mic_section.png, mic_seat_left.png and mic_seat_right.png. A ray along each port axis leaves the head with no
  hit (checked).

### 11.3 Wiring

| cable | wires | pins | route | away from |
|---|---|---|---|---|
| D14 | 5 x 26 AWG twisted (3V3, GND, BCLK, LRCL, DOUT) | Pi 17, 39, 12, 35, 38 to the left board | 78.3 mm, off the header bottom, along the left wall | P13 pack feed 17.3 mm, P12 23.1 mm, D8 SG90 lead 5.1 mm (it lands on pin 33, next to pin 35) |
| D15 | 5 x 26 AWG twisted | left board to right board | 148.4 mm, over the head behind the head_roll_mount | P13 45.5 mm, P12 64.2 mm, D8 6.6 mm, D9 7.2 mm |
| D10 + 1 wire | GPIO16 to the amp SD pin | Pi 36 to U8 SD | with the D10 amp bundle | as D10 |

Twisted, not shielded. All clock and data runs are short, under 0.25 m. Each wire is twisted with its return in the
D10 rule (lay 31 to 62 mm), and the mics are digital at the board, so no analog line runs in the head. A shield is not
needed at this length (calc only; a bench check of bit errors with the servos running is section 10, item 3).

### 11.4 Self-noise: concrete hardware answers

| source | distance to the nearest mic port | hardware answer |
|---|---|---|
| speaker (LS1, right side) | about 62 mm to the right port | half duplex in hardware: GPIO16 now drives the amp SD pin (D48 wire), so the amp is off whenever the codec is not playing (the googlevoicehat codec drives SD high only during playback, with a 5 ms delay, [R] googlevoicehat-codec.c). Since D49 the playback is the echo reference for an echo canceller (section 12.3), so the duck can keep listening while it speaks; until that is in, listening pauses while it speaks (the fallback). The speaker faces down through the head floor, away from the side ports (CAD) |
| SG90 ears | about 37 mm (body centre) to its own mic; 6.05 mm from the board envelope | listen always with the ego-noise model (D49, section 12; the ear commands are an input); gating is the fallback: the ears hold still during the capture and perk after it |
| neck and head servos (STS3215, the head yaw servo at the head centre) | about 111 mm | listen always with the ego-noise model (D49, section 12; joint commands and speeds are inputs); gating is the fallback: listen only when the neck and walk commands are still. The wake word runs at all times |
| walking (14 servos, feet) | the trunk, more than 150 mm | listen always with the ego-noise model (D49, section 12); gating is the fallback: the duck stops walking when called (the stock walk is noisy at the mics, level not published: BLOCKER, TEST_PLAN 17) |
| structure-borne gear noise through the shell | the bosses tie the boards to the shell | a closed-cell foam ring cut from the BOM 29 foam tape on the port tube end seals the port to the board and damps it. The screws stay (2 per board). The foam is a test-fit item: it must not lift the board off the bosses by more than its compressed thickness |

Noise spectra for the STS3215 and the SG90 are not published (BLOCKER): record them on the bench (TEST_PLAN 17,
D49) before any software choice.

### 11.5 Bluetooth direction finding and UWB (second sensor, for the hybrid)

| item | BLE 5.1 AoA | UWB AoA (PDoA) |
|---|---|---|
| on the duck | an antenna array and a direction-finding chip, for example u-blox XPLR-AOA-1 (ANT-B10 board, 8 patch antennas, NINA-B411); the Pi Zero 2 W radio cannot do AoA | a 2-antenna UWB module with phase difference, for example Qorvo DW3000 family |
| on the person | a BLE tag that sends the direction-finding tone (CTE); no iPhone or Android phone was found that sends it to third-party gear ([S] Nordic DevZone thread and Abalta posts, 2021: the chips exist, the OS support does not) | a UWB tag, or a UWB phone; that third-party UWB accessories work with phones is not read (BLOCKER) |
| accuracy | 5 deg mean error, 40 updates per second ([S] u-blox XPLR-AOA-1 product summary) | 2.4 deg mean over a 90 deg range, 2.45 deg standard deviation, under 1 deg with 10 averaged ([S] arXiv 2312.13672, DW3220) |
| size, mass | the kit board may be 29.5 x 93.5 mm (one slide, not tied to the ANT-B10: BLOCKER); mass not read | not read (BLOCKER) |
| cost | about $230 for the kit ([S] ichome); listed obsolete at DigiKey ([S]) | not read (BLOCKER) |
| where on the duck | flat, facing forward: only the chest or the top of the head has 90 mm of flat face; the head top would need a new printed cap (not designed) | a small module on the head top |
| Pi fit | UART on GPIO14 and 15 (free) and 3V3 | the same, or SPI (GPIO8 to 11, free) |

Verdict: not in V1. Both need the person to wear a tag. BLE AoA is no better than the voice and camera pair (5 deg),
and its kit is obsolete. UWB is the more accurate of the two if a tag is ever wanted. GPIO14 and 15 (UART) stay free
for it, and the chest and head top are the two places to study first. Nothing is bought or seated now.

### 11.6 Hybrid, as recommended for V1

| part | what | cost | mass |
|---|---|---|---|
| 2 x I2S mics (E8) | direction from the voice, front or back by a head turn | $13.90 | 0.8 g (0.4 g each [R] product page) |
| camera (E6, already in) | final look | $0 | already counted |
| GPIO16 to amp SD (one 26 AWG wire in D10) | the amp off whenever it is not playing (no idle hiss at the mics) | $0, wire from stock | under 1 g (calc) |
| foam ring on each port tube (BOM 29 tape) | seal and damping | $0, from the roll | under 0.1 g |
| 4 x M2x6 (17h kit) and the printed seats | mounting | $0 (kit) | PLA +285.6 mm3, about 0.35 g at 1.24 g/cm3 (calc only) |
| BLE or UWB direction | later, only with a worn tag | not bought | none now |

Added cost: $13.90. Added mass: about 0.35 g of PLA and 0.8 g of boards, plus the wires and the 4 screws (their
mass is not counted here).

## 12. D49: listen all the time, the duck's own noise removed by a learned model (written 2026-11-05 about 7:40 PM ET)

Ahmed (D49): the duck listens all the time, also while it walks, moves its neck or moves its ears. Its own noise
(ego-noise) is removed by a learned model. Motion gating (D48) stays only as the fallback. This section is the
design, the plan and the data protocol. No software module is written (D47: "maybe we don't need the software stuff
yet").

Source tags used here: [R] read in full, or the cited part read; [A] the abstract read (the OpenAlex record of the
paper; the full text was not read, so no number from the full text is used); [S] a search result only.
Labels: calc only for every estimate; bench numbers are BLOCKERs until TEST_PLAN 17 is run.

### 12.1 The layers, from cheapest to richest

| layer | where | method picked | main source | licence |
|---|---|---|---|---|
| L0 hardware (in) | head | foam ring seals, mic-to-servo distances, twisted D14 and D15, amp off when silent (D48) | section 11 | n/a |
| L1 motor-informed ego-noise estimate | Pi, audio core | a small network predicts the ego-noise power of each mic, per band and per 10 ms frame, from the joint commands, joint speeds, ear commands, gait phase and IMU; a motion template table is its first version and its fallback. Its output drives a Wiener-type gain (speech) and a mask (direction) | Ito et al. 2005 NPSS and MDSS [A]; Ince et al. 2009 [A] | the methods are published; the duck's code would be the lab's own |
| L2 single-model speech enhancer | Pi, audio core | RNNoise, retrained with the duck's ego-noise, on one 48 kHz channel | Valin 2018 [R]; xiph/rnnoise [R] | BSD-style (COPYING) [R] |
| L3 wake word | Pi, its own core | openWakeWord custom model for the duck's name, trained with the duck's ego-noise as background and as negative data | dscripka/openWakeWord [R] | code Apache-2.0; its pre-trained models CC BY-NC-SA 4.0 [R] |
| L4 heavier enhancer | home PC (the agent side) | DeepFilterNet on the speech that the agent hears | Rikorose/DeepFilterNet README [R] | MIT or Apache-2.0 [R] |
| L5 fallback | Pi | motion gating (D48): still the neck and ears, or stop walking, then listen | section 11.4 | n/a |

### 12.2 L1: motor-informed suppression, the literature and the pick

| work | what it does | fit for 2 mics on a Pi Zero 2 W |
|---|---|---|
| Ito, Kanayama, Suzuki, Makino, "Internal noise suppression for speech recognition by small robots", Interspeech 2005 [A] | spectral subtraction with a noise spectrum that depends on the motion. MDSS keeps a noise spectrum for each motion; NPSS predicts the noise spectrum from the angular velocities of all joints with a neural network. NPSS worked even when the motion noise was unstable; MDSS did well when the noise of one motion was stable | best fit: a small robot, few mics, joint speeds the duck already reads, one small network per frame |
| Ince, Nakadai, Rodemann, Hasegawa (Honda Research Institute Japan), "Ego noise suppression of a robot using template subtraction", IROS 2009 [A]; Ince et al. 2010, "Robust ego noise suppression of a robot" [A, record only] | ego-motion noise predicted from the current joint status, then subtracted; ASR during ego-motion improved considerably | fits; it is the template table that L1 starts from |
| Jaroslavceva, Wake, Sasabuchi, Ikeuchi, IEEJ Trans. 2021 [A] | templates indexed by a dance notation (Labanotation); notes that short motion templates and neural predictors did poorly on long, motion-linked ego-noise | a warning: the walk is a long, repeating motion, so L1 also takes the gait phase |
| Schmidt, Deleforge, Kellermann, "Ego-noise reduction using a motor data-guided multichannel dictionary", IROS 2016 [A] | a learned dictionary of spatial and spectral ego-noise; nonlinear classifiers pick the dictionary entries from the motor state, which cuts the computing load by one third | later, off the Pi first: a dictionary search per frame is heavier than one small network (calc only) |
| Schmidt, Brendel, Haubner, Kellermann, "Motor data-regularized nonnegative matrix factorization for ego-noise suppression", EURASIP JASMP 2020 [A]; Schmidt and Kellermann, ICAS 2021 (multichannel NMF) [A] | NMF dictionary of ego-noise; motor data regularize the activations because audio alone is easily misled by other sounds | later; iterative NMF updates per frame (calc only: too heavy to add next to the walk without a bench number) |
| Lagace, Ferland, Grondin, "Ego-noise reduction of a mobile robot using noise spatial covariance matrix learning and MVDR", IROS 2023 [R] | 16 mics on a wheeled robot; a dictionary of ego-noise spatial covariance matrices from 90 s of noise, chosen by PCA, then an MVDR beamformer; 32 kHz, 0.5 s segments; a laptop runs a 0.5 s segment in 0.2 s in Python; SDR up to 10 dB better and WER down by 55 % in some cases (abstract); it notes that template and motor-data methods need the audio and the motor data in sync | with 2 mics an MVDR has one null (calc only): enough for one fixed source such as an ear SG90, not for 14 joints. A later option |
| Schmidt, Lollmann, Kellermann, "Acoustic self-awareness of autonomous systems in a world of sounds", Proc. IEEE 2020 [A] | review of ego-noise suppression | background |
| Shoda et al., arXiv 2609.07440 (2026), legged-robot audition [A] | walking ego-noise is footstep impacts, joint-backlash rattle and motor noise | the duck is legged with backlash (KNEE_TWIN): L1 needs the gait phase and the foot contact, not only joint speeds |
| HARK (Nakadai et al., Humanoids 2008 [A]; Advanced Robotics 2010 [A]; JRM 2017 [A]) | open-source robot audition from Honda Research Institute Japan and Kyoto University | HARK License Agreement version 2.0, July 2020: use "only for the purpose of research, development, education and/or academic purpose" [R]. The duck uses the published methods, not HARK code. ODAS (Grondin, MIT licence [R]) is the open localization alternative |

Pick for V1: L1 is the NPSS idea (Ito 2005). Inputs, all already on the duck:
- the 14 joint commands, and the present positions and speeds, which the Runtime reads every cycle
  (scripts/v2_rl_walk_mujoco.py lines 127 and 134 at 376de65 [R]);
- the 2 ear commands, the walk command, the gait phase and the IMU.

Output: the ego-noise power of each mic in each band, for each 10 ms frame. The network is trained offline on the
bench recordings (12.6). A Wiener-type gain with a floor removes the estimate from the speech path. The same
estimate builds the direction mask (12.4).

The first version is the MDSS-style table: a mean spectrum per motion class (stand, each walk speed, turn, neck move,
ear move). It stays as the fallback when the network meets a motion it was not trained on.

### 12.3 L2 to L4, and the speaker echo

- RNNoise (L2):
  - Design: 20 ms windows with 10 ms hops at 48 kHz; 215 units in 4 hidden layers; 87,503 weights (8-bit
    quantizable); about 40 Mflops.
  - Speed in the paper: 14 % of one 1.2 GHz Cortex-A53 core (Raspberry Pi 3) for one 48 kHz channel, with the
    paper's floating-point C code [R Valin 2018, v3].
  - The current release changed the model format, ships a "little" model too, and does not state its complexity
    [R README]: the Pi number for today's model is a BLOCKER (bench).
  - Training takes clean speech, background noise and foreground noise (transients such as keyboard sounds)
    [R README]. The duck's gear whine is the background noise; footsteps and servo clicks are the foreground noise.
- openWakeWord (L3):
  - Input: 16 kHz 16-bit audio [R example detect_from_microphone.py], in 80 ms frames [R README].
  - Speed: "a single core of a Raspberry Pi 3 can run 15-20 openWakeWord models simultaneously in real-time"
    [R README].
  - Custom training reads background_paths with a duplication rate for each background type [R custom_model.yml,
    train.py]. The duck's ego-noise clips go in as an oversampled background and as negative data.
  - Options: Silero VAD and Speex noise suppression [R README].
  - Licence: the pre-trained models are non-commercial (CC BY-NC-SA 4.0), so the duck trains its own. The licence
    of the synthetic voices used to make training clips was not read: BLOCKER, and the model stays home-use until
    it is read.
- DeepFilterNet (L4, home PC): full-band 48 kHz, with a real-time version and a LADSPA plugin [R README]. The duck
  sends its L1 and L2 cleaned 16 kHz mono stream plus its motion flags. The PC runs the heavier model before the
  agent's speech recognition.
- Speaker echo, now that the duck listens always:
  - Playback and capture share one I2S clock in full duplex (googlevoicehat, section 2 [R]), so the samples the
    duck plays are an exact echo reference.
  - The SpeexDSP acoustic echo canceller (BSD-style [R COPYING; speex_echo.h]) is the planned way to listen while
    the duck speaks.
  - Until then the D48 half duplex is the fallback: the amp is off when silent, and listening pauses while the duck
    speaks.

### 12.4 Direction finding under ego-noise

Method: weighted GCC-PHAT. The L1 estimate weights every time-frequency bin:
- weight 0 where the predicted ego-noise power is above the observed power times a threshold;
- otherwise the soft weight 1 - (predicted noise power / observed power).

Precedents:
- a binary frequency mask on weighted GCC-PHAT on a mobile robot, which improves TDOA discrimination under coherent
  broadband noise and lowers the load when there is no voice (Grondin and Michaud, IROS 2015 [A]);
- a single-channel DNN soft ratio mask feeding SRP and time-frequency spatial filtering on a drone (Wang and
  Cavallaro, IEEE Sensors J. 2022 [A]);
- DREGON (Strauss, Mordel, Miguet, Deleforge, IROS 2018 [A]), which logged rotor speeds and IMU data with the audio
  and evaluated baselines with real time in mind.

The ear SG90 sits beside its own mic, so its noise arrives at a nearly fixed delay. That lag can also be left out of
the correlation peak search (calc only).

Expected accuracy:
- Standing: as D48 (0.34 deg for the ideal pair broadside, calc only), and the camera makes the last step.
- Walking: no figure for a two-mic walking robot was read: BLOCKER, bench (TEST_PLAN 17.5). A calc-only scaling:
  if the masked bins are independent, the delay error grows as one over the square root of the share of bins kept,
  so keeping a quarter of the bins doubles it.
- The head also moves while walking (the policy's head action). Its yaw is in the joint log at every frame, so each
  reading is turned into a body bearing frame by frame (sync, 12.5).
- Fallback: if the share of bins kept falls under a floor set on the bench, the duck uses the D48 gate (still the
  neck and the ears, take the reading).

### 12.5 Sync: one clock for audio frames and servo state

Needed alignment (calc only):
- Ego-noise changes with the joint state at the 50 Hz control rate (20 ms).
- Footsteps come twice per gait period of 0.54 s (Playground reference motion, as read in the shared lab gym
  (overlay gym/overlays/duck) duck_policy.py header [R]).
- L1 frames are 20 ms with a 10 ms hop (the RNNoise layout).
- An error of half a hop moves the estimate by half a frame, so the target is audio and servo timestamps within 5 ms.

How (no new hardware):
- One clock for everything: CLOCK_MONOTONIC_RAW on the Pi.
- ALSA gives a system timestamp with each status (avail and delay), and the clock is selectable, CLOCK_MONOTONIC_RAW
  included [R kernel doc "ALSA PCM Timestamping"]. Where a driver has no link timestamps, the audio time is the DMA
  time from the hardware pointer [R]. Each capture period therefore gives a (sample index, system time) pair, and a
  straight-line fit over many periods removes the DMA burst jitter (calc only).
- The long-term drift between audio time and system time is tracked with the ratio the same doc gives,
  (tstamp - trigger_tstamp) / audio_tstamp [R].
- The walk loop stamps the time before and after each bus read (positions and speeds) and at each write (commands).
  The ear PWM writes and the IMU read are stamped too.
- The walk policy's gait phase goes into every joint-log row in the exact form the policy sees it, and its origin
  and every reset, freeze and rate change are events in the session metadata (12.6). L1 then knows where in the
  step each audio frame falls.
- Check: at the start and end of each session, the duck plays a 50 ms chirp on its own speaker (its playback sample
  time is known on the same I2S clock) and gives one sharp ear command (a click). TEST_PLAN 17.2 measures both
  offsets.

### 12.6 Data plan, on the bench from day one (TEST_PLAN 17)

Format:
- Audio: 2 channels at 48 kHz, S32_LE (the googlevoicehat capture format [R]); WAV while recording, FLAC (lossless)
  for the archive. Channel 0 is the left board (SEL low), channel 1 the right.
- Joint log: one row per 20 ms cycle, gzip CSV. Columns:
  - time (CLOCK_MONOTONIC_RAW, ns), the bus read start and end times;
  - for each of the 14 joints: command, present position and present speed;
  - the walk command (7 values) and the 2 ear commands;
  - the IMU gyro and accelerometer;
  - the walk policy's gait phase, in the policy's own form:
    - the two observation values imitation_phase = [cos(2 pi i / N), sin(2 pi i / N)], the last 2 of the 101
      observation entries (indices 99 and 100);
    - the counter i (imitation_i) after this cycle's update.
    - The Runtime builds the observation before it updates the phase, so a row's two phase values come from the
      counter of the cycle before.
    - The update is i(k) = (i(k-1) + f + o) mod N, with N = nb_steps_in_period = int(period x fps) = 27;
      f = phase_frequency_factor (1.0, or 1.3 while LB is held); o = phase_frequency_factor_offset (from
      duck_config, plus or minus 0.05 per d-pad press).
    - At the start, i = 0 and the phase is [0, 0] (not [1, 0]).
    - Sources [R], Open_Duck_Mini_Runtime 376de65:
      - scripts/v2_rl_walk_mujoco.py line 95 (start_paused from duck_config);
      - the same file, lines 104 to 109 (start values), 156 to 170 (the observation, imitation_phase last),
        213 to 228 (offset and factor changes), 249 to 254 (a pause or an empty observation skips the update) and
        257 to 269 (the update);
      - mini_bdx_runtime/poly_reference_motion.py line 40 (nb_steps_in_period = int(period x fps));
      - period 0.54 s and fps 50, as read in the shared lab gym (overlay gym/overlays/duck) duck_policy.py header.
  - the foot switches, and flags (speaker playing, gate on, walk paused, observation empty so no phase update).
- Sidecar JSON per session:
  - session id, date and time ET, room id, floor, the RT60 from a hand clap (the method of Lagace 2023 [R]);
  - build state: foam rings on or off, ear horns fitted;
  - software commits;
  - audio settings (rate, format, channel map, ALSA period);
  - sync events: chirp and click times in samples and in system time, and the measured offsets;
  - phase events, each with the system time, the cycle index and i before and after:
    - the phase origin: the first policy cycle of this walk object, with i = 0, the observation phase [0, 0], N, f
      and o;
    - every reset: a new walk object (a script restart, a hand-back from a get-up or the dock), which sets i back
      to 0;
    - every freeze and resume: a pause, or a cycle with an empty observation;
    - every change of f or o;
    - the phase order: "runtime", the observation built before the update (the lab's sims use the other order,
      the gym overlay's "lab" mode);
  - the motion script and its parameters;
  - speech segments: start and end sample, source (loudspeaker or person id), text, wake word yes or no, bearing in
    deg from the duck's start heading, distance in m, mouth height in m;
  - the echo playback file and its start sample; consent ids; notes.
- An index in git: session id, sha256, size and labels in a small file (planned:
  altaay_lab/twin/companion/DATA_INDEX.md, made with the first session). The audio stays out of git.

Sessions (minutes, calc only):

| id | session | where | minutes |
|---|---|---|---|
| S0 | still and silent: duck off 2 min, then on and standing still 2 min | 3 rooms | 12 |
| S1 | each servo alone at 3 speeds, 30 s each: the 14 bus servos and the 2 SG90s (duck on a stand, feet free) | bench room | 24 |
| S2 | neck and head moves: yaw sweeps, nods, roll, quick look-at steps, 3 speeds | bench room | 10 |
| S3 | ear moves: perk, twitch, droop, wiggle, random | bench room | 5 |
| S4 | walking: vx 0.05, 0.10 and 0.15 m/s; vx 0.02 (the stock policy steps in place below 0.037 m/s, train/TRAIN.md in the shared lab gym (overlay gym/overlays/duck) [R]); turns in place at wz 0.5 and 1.0 both ways; vx 0.10 with wz 0.5 both ways; 1 min each | 3 rooms (hard floor, carpet, tile) | 30 |
| S5 | the speaker playing phrases and music at 3 volumes, standing and walking (echo) | bench room | 10 |
| S6 | foam rings off: S0 (on), S1 at mid speed for 6 actuators, S4 at 2 conditions; then the rings back | bench room | 7 |
| S7 | played speech: LibriSpeech (CC BY 4.0, 16 kHz [R openslr.org/12]) and the recorded wake word and phrases through a loudspeaker on hand, at 8 bearings x 3 distances (0.5, 1.5, 3.0 m) x 2 heights (0.6, 1.5 m), 30 s each, in 4 motion states (still, neck moving, ears moving, stepping in place) | 2 rooms | 192 |
| S8 | live voices: 3 people say the wake word and phrases, still and stepping in place, 15 min each | bench room | 90 |
| | total | | 380 (6.3 h) |

Size (calc only):
- Audio: 2 x 4 bytes x 48,000 per s = 384 kB/s = 1.38 GB per hour, so 8.8 GB raw for the 6.3 h. The FLAC size is
  measured on the first session.
- Joint log: about 268 bytes per row as binary numbers (256, plus 12 for the three phase values), 13.4 kB/s, about
  0.31 GB for the set; the gzip CSV size is measured too.
- Whole set: about 9.1 GB raw (D49 gave 9.0 GB before the phase columns).

Where the data lives:
- During a session: on the duck's 32 GB microSD (BOM 4).
- Each day: copied to the lab's big-file archive on Ahmed's PC (GrokBox_Archive, START_HERE.md: heavy data never in
  git), checked by sha256, then deleted from the card.
- Voices are personal data. The people recorded agree first, and the recordings never go to the public repo.

### 12.7 Hardware implications

- Keep: the foam ring seals and the mic-to-servo distances (section 11). They make the ego-noise steadier and so
  easier to learn. Keep the twisted D14 and D15 too.
- New parts: none.
  - A reference sensor near the motors (a mic or a piezo) is a known option in the literature (Lagace 2023,
    introduction, its refs 9 to 12 [R]).
  - Even, Sawada, Saruwatari, Shikano (IROS 2009) used extra internal sensors to record internal noise [A].
  - The duck already knows its motor state, and Ito 2005 did the job on small robots from joint speeds [A], so no
    sensor is added.
- Freeze the head before the data is taken: the model learns this head. A change to a seat, the foam, an ear horn or
  a screw pattern near the mics means recording S0 to S4 and S6 again (about 1.5 h, calc only).
- Clipping: the SPH0645LM4H overload point is 120 dB SPL at 10 % THD at 1 kHz [R datasheet, read after D49 was
  written]. TEST_PLAN 17.4 checks the peaks in the loudest sessions (walking, ears next to the mic).
- Storage: the full raw set is about 9.1 GB against the 32 GB card. The daily copy keeps the card from filling.

### 12.8 CPU budget next to the 50 Hz walk and the vision (calc only)

Pi Zero 2 W: quad-core Cortex-A53 at 1 GHz, 512 MB LPDDR2, Bluetooth 4.2 [R product brief, April 2024].

| core | task | basis | estimate |
|---|---|---|---|
| 0 | walk loop: 50 Hz policy, bus reads and writes, the guards | the policy and Python CPU time on the Pi is UNVERIFIED (software/SOFTWARE.md) | BLOCKER (bench) |
| 1 | capture 2 x 48 kHz, L1 estimate, mask, weighted GCC-PHAT | L1 network of the size planned here (48 inputs, 2 hidden layers of 64, 44 outputs, 100 frames per s): about 2 Mflop/s. GCC-PHAT for one pair: SRP-PHAT ran online on one Raspberry Pi 3 core up to 12 mics (66 pairs) and passed 100 % at 13 mics (106 %) [R Grondin and Michaud 2018, arXiv 1812.00115], so one pair is about 1.5 % of such a core | a few % of a core |
| 1 | RNNoise, 1 channel at 48 kHz | 14 % of a 1.2 GHz A53 core [R Valin 2018], about 17 % at 1.0 GHz if the work per clock is the same | about 17 % (today's model: BLOCKER) |
| 2 | wake word (openWakeWord, 16 kHz) | one Raspberry Pi 3 core runs 15 to 20 models [R README]; one model's share is not published | under one core; budget the whole core |
| 3 | camera and face detection after a call; Wi-Fi stream; logging | the vision is not measured (BLOCKER); the stream is 16 kHz x 16 bit = 256 kbit/s | BLOCKER for the vision |

Memory: RNNoise is small (87,503 weights). The footprint of onnxruntime with the wake word and the policy in 512 MB
is a BLOCKER (bench).

### 12.9 BLOCKERs (D49)

1. Pi Zero 2 W CPU time of the walk policy, the face detection, today's RNNoise model and one openWakeWord model;
   the memory footprint (bench).
2. Direction error while walking, with the mask (bench, TEST_PLAN 17.5).
3. Ego-noise levels and spectra of the STS3215s, the SG90s and the footsteps (bench, TEST_PLAN 17).
4. (cleared 2026-11-05 about 7:50 PM ET) The SPH0645LM4H acoustic overload point: 120 dB SPL at 10 % THD at 1 kHz
   [R datasheet].
5. The licence of the synthetic voices used to train a custom openWakeWord model (not read).
6. Only the abstracts were read for Ito 2005, Ince 2009, Schmidt 2016, 2020 and 2021, Grondin and Michaud 2015,
   Wang and Cavallaro 2022, DREGON, Even 2009, Jaroslavceva 2021 and Shoda 2026 (the publisher and HAL pages blocked
   this session's reader): no number from their full texts is used here.
7. The FLAC and gzip CSV sizes (first session).
8. A loudspeaker on hand for S7. Nothing is bought; if there is none, S7 waits.
