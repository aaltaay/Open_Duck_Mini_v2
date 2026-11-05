# Companion hardware: microphones, ears, look at the caller (V1 track 11, D47)

Written 2026-11-05 about 4:55 PM ET (America/New_York). Hardware only (Ahmed, D47): no software, no agent and no gym sim in this track.
Labels: calc only for the acoustics, CAD check only for the seats. Sources are cited per line; [S] means a search result
page (the seller or datasheet page itself was not reachable from this session), [R] means read in full.
Hosts not reachable from this session: adafruit.com, cdn-shop.adafruit.com, invensense.tdk.com, community.nxp.com,
farnell.com, elemon.com.ar. Every number that only those hosts hold is a BLOCKER below.

## 1. Result

- Pick: **2 discrete I2S MEMS mics, Adafruit 3421 (Knowles SPH0645LM4H), one on each side wall of the head, 120.5 mm
  apart.** $13.90 for both (BOM E8, $6.95 each [S] adafruit.com/product/3421 via search, 2026-11-05). Two new GPIO:
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
| Slots | left board SEL to GND (left slot), right board SEL to 3V (right slot); each DOUT floats in the other slot, so both share GPIO20 | [S] Adafruit product text; the SPH0645LM4H datasheet is a BLOCKER |
| Clock range | BCLK = 48 kHz x 64 = 3.072 MHz. That this sits inside the SPH0645LM4H clock range is a BLOCKER (datasheet not read) | calc only |
| Wires | cable D14, Pi to the left board, 5 wires twisted, cut 150 mm (route 80.7 mm); D15, left board to right board, 5 wires twisted, cut 240 mm (route 151.9 mm, over the head behind the head_roll_mount); 26 AWG from stock | twin/companion/route_mics.py, CAD check only |

## 3. Mic count and layout (calc only)

Inputs: c = 343 m/s; fs = 48 kHz (the codec's only rate), one sample = 20.8 us. The delay estimate is taken at one
tenth of a sample (2.1 us) after peak interpolation: an assumption that depends on the signal to noise ratio, to be
measured on the bench. Angle error of one pair: sigma_theta = c x sigma_tau / (d cos theta). Spatial aliasing for
one pair starts at f = c / (2 d); GCC-PHAT on voiced speech still works above it (broadband), but the main lobe
narrows and side peaks appear, so a larger d is not free.

| layout | spacing in this head | sigma at 0 / 60 / 80 deg off the pair axis normal | aliasing from | 360 deg? | Pi fit |
|---|---|---|---|---|---|
| 2 mics, left and right side walls (the pick) | 120.5 mm, measured on the CAD seats (mic_seats.json) | 0.34 / 0.68 / 1.96 deg; 3.4 deg at whole samples | 1.42 kHz | no: front and back mirror; a head turn of 0.25 rad or more between two readings tells them apart (the two mirror candidates move opposite ways) | 2 slots on GPIO20: fits |
| 3 mics, triangle: left, right, back wall | sides 120.5, about 80, about 80 mm (back seat near x = -90 mm from the head bounds; not seat-checked, the SG90s sit at x = -61) | short pairs 0.52 deg at their best angle; any bearing has one pair near its best | 2.15 kHz (short pairs) | yes | NO on one data pin: 3 slots need TDM mics or a codec |
| 4 mics: left, right, front, back | 120.5 mm and about 180 mm front to back (the front seat must clear the eyes, the camera and the bulbs: not seat-checked) | 0.34 deg and 0.23 deg on the two pairs | 1.42 and 0.95 kHz | yes | NO on one data pin (as for 3) |

Why 2: the I2S data pin carries two slots. The SPH0645LM4H has only left and right slots (no TDM), so a third or fourth
mic needs a 4-channel ADC board (AC108, section 4) or a USB array. For a homebody that is called from a room, the head
turn that settles front and back costs about one second and nothing else; the camera then finishes the look.

Matching needs (calc only):
- Timing: a fixed extra delay dt on one mic biases the angle by c x dt / d. For 1 deg at the front, dt must stay under
  6.1 us, an acoustic path difference under 2.1 mm. The seats are mirror images (0.2 mm mirror error in the CAD), the
  port tubes are the same length, and both mics sample on the same BCLK and LRCLK edge, so the pair is matched by build.
- Mic group delay spread between two SPH0645LM4H parts: not read (datasheet BLOCKER). Buy both boards in one order.
- Sensitivity spread: GCC-PHAT divides out the magnitude, so a 1 to 2 dB spread hardly moves the delay estimate.
- A wrong slot (SEL) swaps left and right: a sign flip that the bench check catches in one clap (TEST_PLAN note below).

## 4. Mic hardware options

| option | what it is | price | Pi Zero 2 W fit (I2S, GPIO vs the netlist) | mass, size | space in the head | noise next to the mics |
|---|---|---|---|---|---|---|
| A. 2 x Adafruit 3421 SPH0645LM4H (pick) | discrete I2S MEMS boards, bottom port | $13.90 [S] | GPIO20 only; shares the amp clocks; one overlay | 16.51 x 12.7 mm each [R] Adafruit 6049 board files (the 3421 outline BLOCKER); mass not read (BLOCKER) | on the side walls, 3.46 mm clear of the SG90s (CAD check) | each mic sits beside its ear SG90 (3.46 mm): the ears must hold still while the duck listens |
| B. Seeed ReSpeaker 2-Mics Pi HAT (107100001) | WM8960 codec on I2C1 at 0x1a, 2 mics on the board, speaker driver, 3 APA102 LEDs on SPI | about $19 [S] RobotShop and element14 listings; marked retired at one seller [S] | takes the whole 40-pin header on top of the Pi; its codec would replace the MAX98357A; I2C 0x1a does not clash with the BNO055 (0x28/0x29); the LEDs take SPI0; its Grove digital port is GPIO12 and 13, the antenna PWM pins (leave it empty) | 65 x 30 x 15 mm, 12 g net [S] Core Electronics | sits on the Pi in the head floor, the mics look up inside the shell, no wall ports; the mic spacing on the board is not read (BLOCKER) | the mics sit inside the head next to the Pi and the neck servo: muffled and closer to servo noise |
| C. Seeed ReSpeaker 4-Mic Array for Pi (AC108) | 4 mics on a round board, AC108 4-channel ADC, 12 LEDs, no audio out | $24.50 at launch, about $28 now [S]; discontinued at one seller [S] | uses 11 header pins [S] pinout.xyz; whether the MAX98357A can still share the PCM port with the AC108 TDM capture is a BLOCKER | not read (BLOCKER) | a full board over the Pi, spacing set by the board (not read) | as B |
| D. Seeed ReSpeaker USB Mic Array (XVF-3000) | 4 mics, on-board DOA, echo cancel, USB audio | $87.45 [S] RobotShop | USB: the Pi's only OTG port already feeds the servo bus adapter (netlist cable D1), so it needs a hub; no I2S pins | 77 mm disc, 43.6 g net [S] | a 77 mm disc does not fit flat between the side walls at the mic height (about 120 mm inside, but the Pi, the speaker and the neck mount fill the floor) | inside the head, as B |

Pick A: simplest (2 small boards, 1 new pin, the overlay already exists), cheapest ($13.90), and the most reliable
of the four for direction (ports on the outer shell, a known 120.5 mm baseline, no hub, no second codec).

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
- Noise next to the mics: each SG90 is 3.46 mm from its mic board envelope (CAD check). Rule for the build: the ears
  hold still while the duck captures the voice for direction; they perk after the capture.
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

- Seat search on the inner side walls of print/head.stl: 15-ray plane fit per seat; chosen x = -40, z = 202 mm (URDF
  world), wall 3.21 mm thick, flatness 0.00 mm; the right seat is the mirror (0.2 mm off).
- Per board: 2 bosses 5.0 mm, 3.0 mm high, pilots 1.65 mm x 5.0 mm (the camera pilot, D34), M2x6 self-tapping from the
  BOM 17h kit (it holds 50 M2x6), engagement 4.4 to 5.2 mm with a 1.6 to 0.8 mm PCB (rule 4.0 mm, Westfield table 2),
  1.0 mm of wall left past the pilot; a port tube 4.0 OD, 2.0 bore around the mic; a 1.2 mm sound port through the wall.
- D42: the 2 screws of each board are a mirror pair about the board centre line; the two boards mirror each other.
- D39: both board holes take a screw; the sound port is a sound hole (kept open by D39).
- Clearance of the board envelope (PCB, parts, the wire bend; 0.8 to 1.6 mm PCB): 3.46 mm to the SG90s, 15.2 mm to
  head_bot_sheet, 29.5 mm to the speaker stand; shell 3.0 mm (the boss gap). Watertight, +242 mm3 of PLA.
- The edited head.stl is 2.45 MB (under the 5 MB rule).
- fasteners.json F356 to F359; MOUNTING.md row; viewer placeholders mic_l and mic_r (audit/placements.json).

## 9. BLOCKERs

1. adafruit.com not reachable: the 3421 price and stock on the page itself, the 3421 board outline (the 6049 board files
   were used; Adafruit names the SPH0645LM4H the drop-in) and the board mass.
2. SPH0645LM4H datasheet not read (Knowles hosts not reachable): port offset (port tube bore 2.0 mm takes 0.4 mm),
   PCB thickness (0.8 to 1.6 mm checked), BCLK range at 3.072 MHz, slot and tri-state timing, group delay spread,
   SNR and sensitivity. The part is listed obsolete at one parts index [S]: check stock before an order.
3. (cleared 2026-11-05 about 5:15 PM ET) Cables D14 and D15 are routed in 3D (twin/companion/route_mics.py,
   mic_routes.json: D14 80.7 mm, D15 151.9 mm, both clear of the parts by 1 mm or more, 17 mm or more from the P13 pack
   feed and 5 mm or more from the SG90 leads) and drawn on sheet 4 with D13 (the sheet generator runs again: c10 PASS).
4. SG90 travel per ms and speed for the Miuzei listing (bench).
5. Servo and SG90 noise at the mic ports, and the Pi Zero 2 W CPU time for the direction estimate (bench).
6. Options B to D: board spacing, mass and the AC108 and amp port sharing not read.

## 10. Bench checks (add to TEST_PLAN when the parts come; nothing bought)

1. One clap at 1 m at 0, +60 and -60 deg: the left channel leads for +60 (slot check).
2. A voice at 1.5 m on 12 bearings, 30 deg apart, head still and after a 0.3 rad head turn: front or back right on all 12.
3. Record 10 s with the ears moving, the neck moving and all still: the noise floor at the ports.

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
2. Triangulation from two head angles: with the 120.5 mm pair, the two readings are a few milliseconds of rotation
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
  head frame: listening is gated on motion (11.4).
So the voice only has to put the face inside the 66 deg view (plus or minus 33 deg). The camera does the last step.
Bench check: section 10, item 2.

A third mic (top or back of the head): no.
- One I2S data pin carries 2 slots. A third mic needs a 4-channel ADC (AC108 board, section 4) or TDM mics on a TDM
  capture path, which the googlevoicehat overlay does not set up.
- It removes the front or back turn and helps up and down bearings. A homebody turns its head anyway, and the camera
  finds the face height.
- Cost, if wanted later: one more board, a codec or a USB array, more wires through the head, and a second overlay.

### 11.2 Fit and placement (CAD check only)

- Mic: SPH0645LM4H, bottom port, 3.50 x 2.65 x 0.98 mm. It takes BCLK of 2.048 to 4.096 MHz (3.072 MHz used here),
  draws 600 uA, has an SNR of 65 dB(A) and a sensitivity of -26 dBFS (-29 to -23). [S] Knowles Rev B and Rev C
  datasheet text, from a search result. The pages themselves were not reachable: mouser.com, community.nxp.com.
- Board: 16.51 x 12.7 mm, 2 plated 2.5 mm holes 11.43 mm apart ([R] Adafruit 6049 board files, the 3421 outline BLOCKER).
- Port: the wall port is 1.2 mm across through the 3.2 mm wall, then a printed tube 2.0 mm bore x 3.0 mm to the board,
  then the PCB hole to the mic. Helmholtz estimate (calc only): neck area 1.13 mm2, effective length 4.2 mm
  (3.2 mm + 2 x 0.85 x 0.6 mm end corrections), cavity about 9.4 mm3 (the tube; the PCB hole and the mic front volume
  are not read) gives a resonance near 9 kHz, above the 300 Hz to 8 kHz of speech. Both ports are the same, so the
  resonance gives no direction bias.
- Spacing: 120.5 mm, the widest the side walls give where the walls are flat (x -50 to -5 mm searched) and clear of the
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
| D14 | 5 x 26 AWG twisted (3V3, GND, BCLK, LRCL, DOUT) | Pi 17, 39, 12, 35, 38 to the left board | 80.7 mm, off the header bottom, along the left wall | P13 pack feed 17.3 mm, P12 23.1 mm, D8 SG90 lead 5.1 mm (it lands on pin 33, next to pin 35) |
| D15 | 5 x 26 AWG twisted | left board to right board | 151.9 mm, over the head behind the head_roll_mount | P13 45 mm, P12 64 mm, D8 and D9 7.1 mm |
| D10 + 1 wire | GPIO16 to the amp SD pin | Pi 36 to U8 SD | with the D10 amp bundle | as D10 |

Twisted, not shielded. All clock and data runs are short, under 0.25 m. Each wire is twisted with its return in the
D10 rule (lay 31 to 62 mm), and the mics are digital at the board, so no analog line runs in the head. A shield is not
needed at this length (calc only; a bench check of bit errors with the servos running is section 10, item 3).

### 11.4 Self-noise: concrete hardware answers

| source | distance to the nearest mic port | hardware answer |
|---|---|---|
| speaker (LS1, right side) | about 62 mm to the right port | half duplex in hardware: GPIO16 now drives the amp SD pin (D48 wire), so the amp is off whenever the codec is not playing (the googlevoicehat codec drives SD high only during playback, with a 5 ms delay, [R] googlevoicehat-codec.c). Listening starts after playback ends. Barge-in (talking over the duck) needs echo cancellation in software later. The speaker faces down through the head floor, away from the side ports (CAD) |
| SG90 ears | 37 mm (body centre) to its own mic; 3.46 mm from the board envelope | the ears hold still while listening; they perk after the capture |
| neck and head servos (STS3215, the head yaw servo at the head centre) | about 111 mm | gate: listen only when the neck and walk commands are still; the wake word runs at all times, and the direction is taken from the clean frames after it |
| walking (14 servos, feet) | the trunk, more than 150 mm | the same gate; the duck stops walking when called (the stock walk is noisy at the mics, level not published: BLOCKER, bench item 3) |
| structure-borne gear noise through the shell | the bosses tie the boards to the shell | a closed-cell foam ring cut from the BOM 29 foam tape on the port tube end seals the port to the board and damps it. The screws stay (2 per board). The foam is a test-fit item: it must not lift the board off the bosses by more than its compressed thickness |

Noise spectra for the STS3215 and the SG90 are not published (BLOCKER): record them on the bench (section 10,
item 3) before any software choice.

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
| 2 x I2S mics (E8) | direction from the voice, front or back by a head turn | $13.90 | board mass not read (BLOCKER) |
| camera (E6, already in) | final look | $0 | already counted |
| GPIO16 to amp SD (one 26 AWG wire in D10) | half duplex, the amp off while listening | $0, wire from stock | under 1 g (calc) |
| foam ring on each port tube (BOM 29 tape) | seal and damping | $0, from the roll | under 0.1 g |
| 4 x M2x6 (17h kit) and the printed seats | mounting | $0 (kit) | PLA +242 mm3, about 0.3 g at 1.24 g/cm3 (calc only) |
| BLE or UWB direction | later, only with a worn tag | not bought | none now |

Added cost: $13.90. Added mass: about 0.3 g of PLA plus the two boards, wires and screws. The board mass is a
BLOCKER; the boards are about the size of a postage stamp.
