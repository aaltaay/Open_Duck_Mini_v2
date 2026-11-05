# BATTERY_STUDY: a DeWalt 20V MAX pack (DCB200 and family) for the Open Duck Mini v2 (V1 track 9, phase 1)

Written 2026-11-04 from about 9:50 PM ET (America/New_York; the box clock reads 2026-11-05 UTC), by the V1 battery option job (track 9) for the lead, who owns the
plan and merges. Phase 1: research, a spec and twin numbers. Nothing was bought, built, printed, committed or pushed, and no
message was sent. Labels: **sim pass only** (MuJoCo in the shared lab gym, overlay gym/overlays/duck), **calc only**
(arithmetic on cited numbers), **CAD check only** (geometry of the CAD meshes). Nothing physical was tested. Every number
carries a source tag (list at the end) or the word BLOCKER, ASSUMPTION or UNVERIFIED. The robot stays Open Duck Mini v2 (D40);
the self-charging dock is track 8 (D37, D41), and CHARGE_INTERFACE.md in this folder is written for it.

Ahmed, 2026-11-04 9:37 PM ET: "As you do this, I'm really trying to maybe replace the batteries with DCB200. It's a Dewalt. I
think for 5 A, we're talking about 500 g, around that. You could do your research and spec", and in the same message, "assume
the heat as well, so it needs to be good. We need full research."

## 1. Answer

**No: the DCB200 is not a good idea for this duck.** In plain words:
1. **It is heavier and smaller than expected.** The DCB200 is a 3.0 Ah pack, not 5 Ah, and it weighs 624 g measured [S1] to
   644 g listed (1.42 lb [R3]). DeWalt's 5 Ah pack, the DCB205, weighs 1.54 lb, 699 g [D5]. No 20V MAX pack is near 500 g with
   5 Ah; the lightest are the DCBP034 (1.7 Ah, 0.8 lb, 363 g [D6]) and the DCB203 (2 Ah, 0.91 lb, 413 g [D3]).
2. **It cannot go inside the duck, and every outside seat has a problem** (CAD check only, section 3): on the back it moves
   the centre of mass 32 mm back (the walk tips over backwards from about 5 mm, sim/ADDED_MASS_SIM.md); on top it sits inside
   the head at the home pose; under the belly (the only workable seat) the shins hit it at the hip yaw and hip roll range ends,
   and in 28 of 63 pushed and fallen runs the shins, feet or floor struck it (sim pass only).
3. **The duck gets 20 % heavier** (2.69 to 3.24 kg, 54 % over the 2.107 kg the policy was trained at), and the stock policy
   walks it much slower (sim pass only, section 5), and the hip roll bending load rises by 70 % in walking, which puts
   roll_to_pitch (walking SF 1.81 today) near 1.1 (calc only, section 5.6). A retrain at the new mass is needed before it walks.
4. **The one real gain, a regulated 7.2 V servo bus with no battery sag, does not need a DeWalt pack** (section 4.2).
5. The pack has no protection of its own (no low-voltage or over-current cut; the tool does that [S1], [S2], [D1]), so the
   robot must add a pack monitor, a hardware cut and an over-voltage cut (section 4.4), and its charger in the dock must be a
   5S CC/CV charger at 20.5 V (CHARGE_INTERFACE.md).

**What is better:** keep the 2S pack and the as-built power path, and swap the two Molicel P30B 18650 cells for two **Molicel
P45B 21700** cells as a spot-welded 2S pack (+50 % energy, 21.6 to 32.4 Wh, +26 g net), which needs the battery bay in body_back
grown 2.1 mm deeper and 2.9 mm wider (Ahmed: "go with the P45B cells then"; implemented on the local branch, section 14). If the sag gain of section 4.2 is wanted too, the next step is D23's 3S plan with 21700 cells
(3 x P45B, 48.6 Wh, about +100 g), not a 5S DeWalt pack. The numbers are in the table below and in section 5.

| Option (sim pass only, calc only) | Robot mass | Pack Wh (nominal) | Walking per charge (continuous, 32 C) | Session per charge (50/50 stand and walk, calc) | Walk speed (live twin, 32 C, backlash) | Falls: hard shoves / push ladder / 15 N push series | Heat: hottest servo reading, cut | Parts cost (read 2026-11-04 ET) | Charge time at 2 A (calc) |
|---|---|---|---|---|---|---|---|---|---|
| Today, 2S1P P30B | 2.692 kg | 21.6 | 24.6 min (twin, to the D16 walk stop) | 33 min | 0.086 m/s (whole charge) | 28 of 29 / 8 of 24 / no fall | right knee 63 C, no cut | in the BOM ($58.95) | 1.6 h (3.0 h on today's 1.1 A board) |
| **2S1P P45B 21700, spot-welded pack (chosen, implemented)** | **2.718 kg** | **32.4** | **39 min** (calc on the twin's 30 min run) | **50 min** | **0.103 m/s** (first 30 min) | **28 of 29 / 7 of 24 / no fall** | **right knee 64 C, no cut** | **+$9.99 net** (2 x $9.99 cells, less the $9.99 holder; strip and sleeve BLOCKER) | **2.6 h** |
| 2S1P P50B 21700 (drop-in alternate) | 2.720 kg | 36.0 | 43 min (P45B x 1.11, calc) | 56 min | as P45B | as P45B | as P45B (less heat: 12.8 against 15 mOhm) | +$13.99 net | 2.9 h |
| 2S2P P30B, second pair in the bay | 2.811 kg | 43.2 | about 50 min (calc; session not run) | about 66 min | 1.21 m in the 20 s walk (today 1.32 m) | **29 of 29 / 10 of 24 / fell** | not run | +$27.97 | 3.3 h |
| DCBP034 (5S1P 1.7 Ah), belly | 2.969 kg | 30.6 | 36 min | 50 min | 0.080 m/s | 28 of 29 / 3 of 24 / no fall; pack hit in 26 of 63 runs | right knee 69 C, no cut | $139.00 + $75.75 parts + a 5S dock charger | 1.0 h |
| DCB203 (5S1P 2 Ah), belly | about 3.02 kg | 36 | 43 min | 60 min | about 0.08 m/s (the DCBP034 run) | as DCBP034 | as DCBP034 | $119.00 + $75.75 + dock charger | 1.2 h |
| **DCB200 (5S2P 3 Ah), belly** | **3.240 kg** | **54** | **59 min** | **85 min** | **0.030 m/s** | **23 of 29 / 2 of 24 / no fall; pack hit in 28 of 63 runs** | **left hip pitch and right knee 70 C (cut at 71), left knee 69 C** | **$139.00 + $75.75 + dock charger** | **1.7 h** |
| DCB204 (5S2P 4 Ah), belly | about 3.24 kg | 72 | 80 min | 114 min | as DCB200 | as DCB200 | as DCB200 | $139.99 + $75.75 + dock charger | 2.3 h |
| DCB205 (5S2P 5 Ah), belly | 3.305 kg | 90 | about 95 min (calc, not run) | about 140 min | not run (heavier than the DCB200) | not run | not run | $169.00 + $75.75 + dock charger | 2.9 h |
| DCBP520 (5 Ah POWERSTACK), belly | about 3.29 kg | 90 | about 95 min (calc, not run) | about 140 min | not run | not run | not run | $219.00 + $75.75 + dock charger | 2.9 h |

"$75.75 parts" = the VXB adapter $49.93 [R8] + INA260 $9.95 [A1] + ADS1115 $14.95 [A2] + TPS3700 about $0.92 [T1]. Walk speeds:
the live twin in the shared lab gym (overlay gym/overlays/duck), continuous walking at a 0.15 m/s command, backlash model,
a 32 C room, STS3250 knees with the C001 knee damping as the stand-in for the retrained policy (the V1 knee job's
`sts3250_high_d0.56`; with the published STS3250 damping the stock policy barely walks, KNEE_TWIN.md B70). The P45B, regulated
and DeWalt runs stop at 30 minutes (the regulated bus does not change with charge; the P45B has 51 % left then); today's run
goes to the battery stop, so its speed includes the end-of-charge sag. Falls: the V1 electrical job's push sets with the track
1b guard (shoves: 60 N standing and 40 N walking, 29 runs; ladder: 10 to 25 N standing and 10 to 15 N walking, 24 runs; the 15 N
push series while walking). Runtime: section 5.5. All sim pass only or calc only; nothing was run on hardware.

## 2. The DeWalt 20V MAX family (research)

### 2.1 Packs

Read 2026-11-04 between 9:46 and 10:12 PM ET. DeWalt's own pages first [D3] to [D6]; the DCB200 has no DeWalt US page any
more (its old URL redirects to the batteries list, read 2026-11-04 ET) and the DCBP520 URL tried returned 404, so their lines use
a teardown and retailers.

| Pack | Voltage, max / nominal | Ah | Wh (nominal) | Cells, layout | Mass | Size | Max current | Price, stock (read 2026-11-04 ET, nothing bought) |
|---|---|---|---|---|---|---|---|---|
| DCB200 | 20 / 18 V | 3.0 | 54 | 10 x LG HB4 18650 (1.5 Ah, 30 A), 5S2P [S1] | 624 g measured (22 oz) [S1]; 1.42 lb (644 g) listed [R3] | 4.5 x 3 x 2.5 in (114 x 76 x 64 mm) measured [S1] | not published by DeWalt; cells 30 A each [S1], so about 60 A for the pack (calc only) | $139.00 in stock (Toolnut [R4]); $49.00 out of stock (Coastal Tool [R5]) |
| DCB203 | 20 / 18 V [D3] | 2.0 [D3] | 36 | 5S1P 18650 (calc: 2.0 Ah in 5 cells, cell model not published: BLOCKER) | 0.91 lb (413 g) [D3] | not published as a pack size (DeWalt gives 7.0 x 7.0 x 3.2 in, the box): BLOCKER; the twin assumes 114 x 76 x 45 mm (ASSUMPTION) | not published: BLOCKER | $119.00 in stock (The Power Tool Store [R1]) |
| DCB204 | 20 / 18 V [D4] | 4.0 [D4] | 72 | 5S2P 18650 (calc), cell model BLOCKER | 1.4 lb (635 g) [D4] | assumed the DCB200 housing (UNVERIFIED) | not published: BLOCKER | $139.99 (The Power Tool Store, read through a search index [R6]; not read on the page) |
| DCB205 | 20 / 18 V [D5] | 5.0 [D5] | 90 (DeWalt lists 100 Wh at 20 V [D5]) | 5S2P 18650 (calc), cell model BLOCKER | 1.54 lb (699 g) [D5] | assumed the DCB200 housing (UNVERIFIED) | not published: BLOCKER | $169.00 in stock (The Power Tool Store [R1]) |
| DCBP034 POWERSTACK | 20 / 18 V [D6] | 1.7 [D6] | 30.6 | pouch cells ("pouch cell technology" [D6]), 5 in series (calc) | 0.8 lb (363 g) [D6] | not published as a pack size; DeWalt says it is smaller than the DCB203 [D6]: BLOCKER | not published; DeWalt: "50% more power" than the DCB203 [D6] | $139.00 in stock (The Power Tool Store [R1]) |
| DCBP520 POWERSTACK | 20 / 18 V | 5.0 | 90 | pouch cells, 5 in series (calc) | 1.4 to 1.6 lb (635 to 725 g), retailers [R7] | 5.2 x 3.3 x 2.2 in (132 x 84 x 56 mm), retailers [R7] | not published: BLOCKER | $219.00 in stock (The Power Tool Store [R1]) |

All six are on DeWalt's "less than or equal to 100 Watt Hours" data sheet [D2] (so they ship and fly as ordinary Li-ion
packs). DeWalt: "Maximum initial battery voltage (measured without a workload) is 20 volts. Nominal voltage is 18" [D3] to [D6].
Warranty: "3 Year Limited Warranty, 1 Year Free Service, 90 Days Satisfaction Guaranteed" [D3] to [D6].

**Ahmed's "5 A, about 500 g":** the DCB200 is 3.0 Ah and 624 to 644 g. 5 Ah DeWalt packs weigh 699 g (DCB205 [D5]) or 635 to
725 g (DCBP520 [R7]). About 500 g buys 2 Ah at most (DCB203, 413 g [D3]). So the 5 Ah and the 500 g do not go together.

### 2.2 What is inside: who cuts off, and the terminals

- **The pack does not cut off.** Teardown of a DCB200: "There is no way that the BMS can cut off current if the pack voltage is
  low. It's up to the tool to determine the cutoff point and refuse to work below that" [S1]. Teardown of a 6 Ah pack: "There's
  also no low voltage cutoff or overcurrent cutoff - the tool is required to handle all that" [S2]. DeWalt's own manual puts
  the protection in the product: "XR Li-ion products are designed with an Electronic Protection System that will protect the
  battery pack against overloading, overheating or deep discharge. The product will automatically turn off if the Electronic
  Protection System engages" [D1]. **So the duck must do the cut itself** (section 4.4).
- **Terminals (8):** B+, B-, TH, ID, C1, C2, C3, C4 [S2]. TH: "a 10kΩ/25C NTC thermistor wired between B+ and TH" [S2]; measured
  10.68 kOhm at 21.6 C on the DCB200 board [S1]; it sits on the board and reads the board, not the cells [S1], [S2]. ID: a
  resistor to B- for pack identification (about 800 Ohm on one DCB200 [S1]; other values on other packs, UNVERIFIED). C1 to C4:
  "the individual cell bank voltages" [S1]; C1 is the first group up from B- [S2].
- **Balancing:** the 2016 DCB200 board balances by itself ("I did confirm that the BMS will balance cells" [S1]); the 6 Ah
  board "doesn't appear to do any balancing" [S2]; DeWalt chargers use C1 to C4 for balance charging [S2]. Today's packs may
  differ from these 2016 and 2017 teardowns (UNVERIFIED).
- **Full charge from a DeWalt charger:** 20.43 V, 4.08 to 4.09 V per group, on a healthy DCB200 [S1].

### 2.3 Charging

- **DeWalt chargers:** a Hot/Cold Pack Delay ("When the charger detects a battery pack that is too hot or too cold, it
  automatically starts a Hot/Cold Pack Delay, suspending charging until the battery pack has reached an appropriate
  temperature" [D1]); "Only charge batteries in air temperature over 4 ° C and below 40 ° C" [D1]; "Do not store or use the
  product and battery pack in locations where the temperature may fall below 4 ˚C ... or reach or exceed 40 ˚C (104 ˚F)" [D1].
  Charge times on DeWalt's pages: 35 min (DCBP034 [D6]), 45 min (DCB203 [D3]), 90 min (DCB204 [D4], DCB205 [D5]); the charger
  is not named there.
- **A third-party charger must:** charge 5S CC/CV to about 20.5 V (4.10 V per group, as a DeWalt charger leaves it [S1]; never
  over 21.0 V, 4.2 V per cell), check TH (10 k NTC to B+) and stop outside 4 to 40 C [D1], and either balance through C1 to C4
  or be paired with a robot-side group monitor that stops the charge when a group passes 4.15 V or the groups differ by more
  than 50 mV (ASSUMPTION thresholds). A genuine DeWalt charger cannot reach a pack held in the duck: the rail slot is its only
  interface. Details for the dock: CHARGE_INTERFACE.md section 4.

## 3. Mounting (CAD check only, sim pass only for the contacts)

### 3.1 Adapters and printable mounts

| Mount | Terminals and wire | Latch | Fuse, switch | Mass | Price, source |
|---|---|---|---|---|---|
| VXB "Dewalt 20V Battery Adapter For Power Wheels DIY Conversion Kit With Switch Fuse" | "12 AWG silicone copper wire", "wiring terminals" | the pack's own rail latch | "Built-in 30A fuse", "built-in switch", 3 spare 30 A fuses | 118 g listed (shipping weight, not the part) | $49.93, available [R8] |
| VXB "Power Wheels Adapter for DeWalt 20V Battery and 18V Dock Beefy Heavy Duty 12 Gauge" | 12 gauge; "Max current rating 55" A (listing) | rail | not stated | 77 g listed (shipping weight) | $49.98, available [R8b] |
| Walmart.ca 2-pack adapter kit | 12 AWG, "6 PCS 30Amp Fuses", switch | rail | 30 A fuse, switch | not stated | not read [R9] |
| Printables "DeWalt 20V Battery Mount Bracket (small)" (model 504186), "DeWalt 20v battery mount" (102778), "Dewalt 20V battery dock" (226563); Makerworld copper-terminal adapter (0.5 mm copper sheet, 12 AWG, "you are not allowed to sell this 3D model or the printed adapter") | printed rail; terminals from spade lugs, brass strip or copper sheet | the pack's latch | none | not published: BLOCKER | free files, licence per model [R10] |

None of the commercial adapters has a datasheet or a stated net mass (they are unbranded listings), so their current
ratings are UNVERIFIED. The twin uses 45 g for a printed rail plate with terminals and 16 AWG leads (ASSUMPTION); the listed
shipping weights (77 to 118 g) say the real part may be up to 73 g heavier. Our pack current is low (section 4.1), so 16 AWG
is enough; the 30 A fuses in the kits are far above our 15 A ATO (POWER.md section 4).

### 3.2 Where a pack this size could sit

The pack is 114 x 76 x 64 mm (DCB200 [S1]) plus a 15 mm rail plate (ASSUMPTION). The trunk shell is x -154 to +46 mm, y +/-55,
z -35 to +108 (trunk frame, x forward, y left, z up; meshes of the pinned Playground model, tools/geom_probe.py). The battery
bay inside body_back is 20 x 41 x 76.5 mm (DECISIONS.md D23): a DeWalt pack cannot go inside.

Check: the pack box on trunk_assembly in the collision duck (every printed part as a shell), signed distance to every other
part at home, each joint swept alone over its full MJCF range, 4000 random poses with all 14 joints in their ranges, and the
get-up bridge (hips -68 deg, knees -88 deg). Convex hulls, so slightly conservative. tools/mount_check.py, runs/mount_check.json.

| Seat (pack centre, trunk frame) | Home pose | Joint sweeps (worst, alone) | Random full-range poses in contact | Get-up bridge | Centre of mass change (section 3.3) | Verdict |
|---|---|---|---|---|---|---|
| Belly, under the trunk floor, x -46 mm, long axis along x (5S2P) | clear, 15.9 mm to hip_roll_assembly | hip yaw +/-30 deg: 13 mm into the shin; hip roll +/-25 deg: 18 mm into the shin; every other joint clear | 1605 of 4000 (worst 46 mm in) | clear, 15.9 mm | x +0.3, z -26.9 mm | the only workable seat, with joint limits or a retrain that keeps the legs out (section 5) |
| Belly, 5S1P (45 mm tall pack) | clear, 15.9 mm | hip yaw 13 mm in; hip roll 10 mm in | 1407 of 4000 | clear | x +2.0, z -16.0 mm (DCBP034) | same |
| Belly, DCBP520 size (132 x 84 x 56) | clear, 15.9 mm | hip yaw 17 mm in; hip roll 19 mm in | 1920 of 4000 | clear | about as DCB205 | worse than the 5S2P box |
| Top of the trunk, x -46 mm | **inside the head and neck by 31 mm** (head_pitch_to_yaw) | head pitch 78 mm in, neck pitch 61 mm in | 4000 of 4000 | inside | z +22.7 mm | fails |
| Top, 5S1P | inside by 25 mm | neck pitch 53 mm in | 4000 of 4000 | inside | | fails |
| Back face (backpack), 5S2P standing | clear, 50 mm | the head reaches it at neck pitch 52 deg (1.4 mm) | 804 of 4000 | clear (31 mm) | **x -32.3 mm** | fails on the centre of mass (the walk tips backwards from about 5 mm back, sim/ADDED_MASS_SIM.md) |
| Chest (in front of body_front, x +46 to +125) | not run | | | | about x +28 mm (calc only) | fails on the centre of mass (tested only up to +10.7 mm, sim/ADDED_MASS_SIM.md) |

In the push and fall runs with the belly pack (sim pass only, 63 runs, section 5.3), the pack touched something in 28 runs:
the floor (7983 contact steps), the right shin (1663), the left shin (828) and the feet (701, 467). It was not touched in the
20 s straight walk. In one 40 N walking push to the left it touched the floor while the duck stayed up. So the pack takes
hits in falls and the shins strike it in hard pushes: the mount needs to carry a fall (section 5.6) and the shin faces need
a check (track 4, joint motion).

### 3.3 Centre of mass and inertia

Whole robot at the home pose, trunk frame, with the STS3250 knees (D32); the pack, adapter and removed bay parts as boxes at
their seats, parallel-axis sums (tools/batt_twin.py info; bay part seats from sim/mass_budget.py build_budget()). Calc only.

| Option | Robot mass | Centre of mass x, y, z (mm) | Change from today (mm) | Inertia about the centre of mass Ixx, Iyy, Izz (kg m2) |
|---|---|---|---|---|
| Today, 2S1P P30B | 2.692 kg | -27.7, 0.4, 49.5 | 0 | 0.0399, 0.0391, 0.0165 |
| 2S1P P45B (same seats, 70 g cells [M2]) | 2.738 kg | -29.5, 0.4, 49.2 | x -1.8 | 0.0399, 0.0396, 0.0170 |
| 2S2P P30B, second pair stacked in the bay | 2.811 kg | -32.1, 0.4, 49.7 | **x -4.4** (at the edge: 4.4 mm back held, 5.3 mm tipped in the duck physics, sim/ADDED_MASS_SIM.md) | 0.0399, 0.0403, 0.0177 |
| DCBP034, belly | 2.969 kg | -25.7, 0.5, 33.5 | x +2.0, z -16.0 | 0.0452, 0.0434, 0.0159 |
| DCB200, belly | 3.240 kg | -27.4, 0.4, 22.6 | x +0.3, z -26.9 | 0.0495, 0.0481, 0.0164 |
| DCB205, belly | 3.305 kg | -27.8, 0.4, 20.5 | x -0.1, z -29.0 | 0.0503, 0.0489, 0.0165 |
| DCB200, top | 3.240 kg | -27.4, 0.4, 72.2 | z +22.7 | 0.0461, 0.0446, 0.0164 |
| DCB200, back | 3.240 kg | -60.0, 0.4, 48.1 | **x -32.3** | 0.0409, 0.0554, 0.0324 |

The masses above include +39 g for the two STS3250 knees (knee_swap.py); the inertias are without the knee change (small).
Removed for every 5S option: the two P30B cells (2 x 47 g), the holder (25 g), the Tenergy BMS (3 g) and the Adeept charger
(8.53 g) (sim/MASS_BUDGET.md). The belly seat keeps x where it is because the pack sits 18 mm behind the robot's centre of
mass, which balances the 131 g taken out of the bay at x -126 mm (calc only).

## 4. The power path from a 15 to 20.5 V pack (calc only, sim pass only where marked)

### 4.1 Servo bus: the Castle CC BEC Pro already fits a 5S pack

Castle's own chart for the CC BEC Pro (010-0004-01) [C1]: peak current 20 A; continuous "2S-4S: 15A, 5S-6S: 13A, 7S-8S: 11A";
max volts "Surface: 8S (33.6V)"; output 4.9 to 12.5 V (default 5.1 V); 47 x 33 x 22 mm, 40 g with full-length wires;
"Ratings are determined with a 5mph airflow at 25° C (77° F)" [C1]. $54.95 [C1]. So on 5S (15 to 20.5 V) it is inside its
input range and rated 13 A continuous, against our servo bus:
- The worst 4 ms window of the servo bus with the track 1b guard is 9.5 to 10.1 A (twin/knee/KNEE_TWIN.md section 4: 9.56 /
  9.47 / 10.06 A with C001 knees; 8.66 / 9.40 / 9.69 A with STS3250 knees). That is the BEC output. Under its 20 A peak.
- The 15.89 A figure of track 1b is the 2S pack side (twin/electrical/ELECTRICAL_TWIN.md). At 5S the same event draws about
  7.2 V x 10.1 A / 0.85 / 18 V = 4.8 A from the pack (calc only, at the assumed 0.85), plus the 5 V branch.
- Walking means (sim pass only, 30 min continuous walking): servo bus 3.31 A, 23.6 W at today's mass on the regulated bus; 3.62 A (DCBP034) and 4.09 A, 29.0 W (DCB200). Pack 1.71 A at 19.9 V (34.0 W, today's mass), 1.92 A (36.7 W, DCBP034), 2.06 A at 19.7 V (40.6 W, DCB200).
- Lowest servo volts on the regulated bus: 6.76 to 6.77 V (wire drops after the BEC), 0 % of the time under 6.0 V; the P45B on the 2S bus: 6.04 V lowest, 0 % under 6.0 V in its first 30 min.
- Efficiency: Castle does not publish it (B37, still open). The twins assume 0.85 at 2S. At 5S the BEC steps 18 V down to
  7.2 V instead of passing a 7 to 8 V input nearly through, so its switching loss is likely higher (UNVERIFIED). Heat at the walking bus power (calc only): today's mass 2.6 / 4.2 / 5.9 W at an efficiency of 0.90 / 0.85 / 0.80; DCB200 3.2 / 5.1 / 7.3 W. The thermal twin already puts the CC BEC Pro case at 98 to 122 C at 0.85 on today's 2S pack (B37), so a 5S pack makes the BEC's heat no better and likely worse.
- Setting 7.2 V still needs the Castle Link V4 kit ($29.95, Windows, POWER.md section 3).
- Other bucks checked in POWER.md (the Pololu D24V150F7 and D42V110F7 are fixed above 7.4 V; the D42V110F6 is 6 V): none is
  better at 5S. The CC BEC Pro stays.

### 4.2 Sag: what a regulated bus gains (sim pass only)

The electromechanical twin found that the sag of the 2S pack slows the walk to 79 % (typical) and 76 % (high-side) of its
trained speed at a nominal pack (twin/electromech/ELECTROMECH_TWIN.md). With a 5S pack the CC BEC Pro always regulates, so
the bus stays at 7.2 V minus the wire drops at every charge. The live twin, the same session and knee, our 2.69 kg build:
| Run (continuous, backlash, 32 C, 30 min or to the stop) | Speed | Knee peak reading |
|---|---|---|
| today's P30B pack, sagging bus, to the D16 walk stop at 24.6 min | 0.086 m/s | 63 C |
| P45B 2S pack, sagging bus, first 30 min (51 % left) | 0.103 m/s | 64 C |
| regulated 7.2 V bus, today's mass, 30 min | 0.104 m/s | 66 C |

So the regulated bus gains about 20 % of walking speed over today's whole charge, but a bigger 2S pack gets nearly all of that
(0.103 against 0.104 m/s) inside its first 30 minutes, because most of today's slowdown is the end-of-charge sag. The
regulated bus also runs the knees 2 C hotter (no sag starving them, as TWIN_LIVE.md found). The remaining gain belongs to the
last part of a charge only; it does not justify a 5S pack. (Sim pass only; the guard stop and the policy are as built.)

### 4.3 The other parts at 20.5 V

| Part | Rating (source) | At 5S | Change |
|---|---|---|---|
| Pololu D30V30F5 5 V regulator | 5 V to 45 V input, 3.4 A typical max (at 30 V in), 80 to 95 % efficiency, $29.95 [P2] | inside | none |
| Pololu 2813 switch, HP | 4.5 to 40 V (BOM line 10; the Pololu table as read lists 4.5 to 32 V and 4.5 to 40 V for its versions), 13 mOhm at 4.5 V and 8.6 mOhm at 10 V, 6.0 A at 55 C, 90 A max, $8.95, backorders allowed [P1] | inside; walking pack current about 2 A instead of 4.6 A, so about a fifth of today's switch heat (calc only) | none |
| Littelfuse ATO 15 A fuse and FHAC0001ZXJ holder | 32 V (POWER.md section 4) | inside | keep 15 A, or 10 A for the lower 5S current (calc only) |
| 16 AWG silicone harness | voltage rating not in the lab files: BLOCKER (read the wire sheet); 20.5 V is low for any hookup wire of this class (UNVERIFIED) | | none |
| Amass XT30U | 15 A continuous, 30 A peak (BOM line 12); voltage rating not read: BLOCKER | | none |
| Tenergy 32175 2S BMS | 2S only (POWER.md section 5) | cannot be used | removed; the protection moves to section 4.4 |
| Adeept USB-C 2S charger | 2S only (BOM line 11) | cannot be used | removed; charging moves to the dock (CHARGE_INTERFACE.md) |
| CC BEC Pro | section 4.1 | inside | none |
| **Servo over-voltage** | the C001 is rated 4 to 7.4 V input (KNEE_TWIN.md section 2); the STS3250 cuts above 14 V [F5 in KNEE_TWIN.md] | a shorted BEC would put 20.5 V on the bus (today 8.4 V at most) and burn every C001 | **add an over-voltage cut** (section 4.4) |

### 4.4 Low-voltage cutoff, over-voltage cut and the 5S battery guard (spec, calc only)

The DeWalt pack has no cut (section 2.2), and with a regulated bus the servos read 7.0 to 7.2 V at any charge, so **the D16
battery guard, which reads servo Present Voltage, no longer sees the pack** (DECISIONS.md D16 note; software/SOFTWARE.md
section 5). Spec:
1. Pack monitor on the Pi's I2C: Adafruit INA260 (high or low side, voltage, current and power, integrated shunt; $9.95, in
   stock [A1]) on B+ after the fuse.
2. Group monitor: Adafruit ADS1115 4-channel 16-bit ADC ($14.95, in stock [A2]) on C1 to C4 through dividers (the C taps are
   at 4.1, 8.2, 12.3 and 16.4 V full [S1]).
3. Hardware cut, independent of the Pi: TI TPS3700 window detector ("High voltage (18V) window voltage detector", 1.8 to 18 V
   supply, internal 400 mV reference, open-drain outputs rated to 18 V, 5.5 uA typical [T1]; TI lists about $0.92 [T1],
   quantity not read) driving the Pololu 2813 OFF input: undervoltage at 15.0 V on the pack (3.00 V per group) through a
   divider, overvoltage at 7.8 V on the servo bus. How fast the 2813 opens on OFF is not published: BLOCKER (bench).
4. Battery guard thresholds for 5S (replace the D16 servo-voltage rules; software, phase 2):
   - walk stop: pack under 17.0 V (3.40 V per group) for a 5 s mean while walking;
   - hard stop standing: under 16.0 V (3.20 V per group) for a 3 s mean; walking: under 15.5 V for a 2 s mean;
   - any group under 3.00 V (ADS1115): hard stop; groups differing by more than 0.10 V: walk stop and a "balance charge" flag;
   - hardware cut at 15.0 V (TPS3700, above) and the over-voltage cut at 7.8 V on the bus.
   The 3.40 V walk stop uses 73 to 75 % of the rated charge at our walking current (calc on the P30B surface). These thresholds are ASSUMPTIONS until
   the cells are known (the DeWalt cell model is not published for most packs: BLOCKER).

### 4.5 12 V servos (note with cost only)

A 5S pack could feed a 12 V servo bus (the CC BEC Pro sets up to 12.5 V [C1]). From SERVO_UPGRADE_OPTIONS.md: C018 or C047
(12 V, 30 kg.cm) $20.90 each at 10+, $334.40 for 16; STS3235 $40.29 each, $644.64 for 16; STS3250 $73.99 each, $1,183.84 for
16 (12 more plus 2 spares beside the 2 knees already chosen: 14 x $73.99 = $1,035.86, calc only). Each needs a bench BAM
identification and a retrain (SERVO_UPGRADE_OPTIONS.md). Not studied further here.

## 5. Twin numbers (sim pass only)

### 5.1 Setup
- The live twin (shared lab gym, overlay gym/overlays/duck, twin_live) with the knee option `sts3250_high_d0.56` (STS3250
  torque and heat, the C001 knee damping as the stand-in for the retrained policy; V1 knee job), the stock policy with the
  runtime handling, the gym physics (1 ms, implicitfast, elliptic cone, floor friction 1.0), the as-built power network in its
  typical corner, the thermal twin's central set, a 32 C room, continuous walking at 0.15 m/s, backlash model.
- Mass and centre of mass: tools/batt_twin.py patches the trunk inertial in its own process (section 3.3); the belly packs also
  get a collision box (the collision duck sees the pack hit the shins, feet and floor).
- Pack: the network keeps its two series cells; each is k x a P30B group of f parallel P30B-equivalents (k 2.5 for 5S), so
  the 5S runs feed the CC BEC Pro at 15 to 20.5 V and it regulates at 7.2 V all the time. The P45B is modelled as 1.58 P30B
  in parallel (the same surface per unit capacity: ASSUMPTION; the P45B sheet gives 15 mOhm DC against the P30B's 17 [M1],
  [M2], so the model is a little conservative). DeWalt cells as P30B-like high-power NMC (ASSUMPTION: cell models not published).
- Runs, one at a time under ramcap: 6 sessions (today from the knee job, P45B, regulated at today's mass, DCBP034, DCB200; the
  2S2P session was cut off by the chain's 2 h limit and the DCB205 session did not start), 6 push sets, get-ups for the chosen
  pack and today.

### 5.2 Sessions: walk, heat and runtime
| Run | Mass | Walking minutes (end) | Speed | Falls | Hottest servo readings (C) | Lowest servo V | Pack walking |
|---|---|---|---|---|---|---|---|
| Today, P30B 2S (knee job's run) | 2.692 kg | 24.6, battery walk stop | 0.086 m/s | none | right knee 63, left hip pitch 61, left knee 59 | (not logged) | 4.61 A (calc from charge) |
| P45B 2S | 2.738 kg | 30.0, cap (51 % left) | 0.103 m/s | none | right knee 64, left knee 60, head roll 56 | 6.04 V | 4.37 A at 7.46 V, 32.6 W |
| Regulated 7.2 V, today's mass | 2.692 kg | 30.0, cap | 0.104 m/s | none | right knee 66, left knee 62, left hip pitch 59 | 6.77 V | 1.71 A at 19.9 V, 34.0 W |
| DCBP034, belly | 2.969 kg | 30.0, cap | 0.080 m/s | none | right knee 69, left hip pitch 66, left knee 65 | 6.76 V | 1.92 A at 19.1 V, 36.7 W |
| DCB200, belly | 3.240 kg | 30.0, cap | **0.030 m/s** | none | **left hip pitch 70, right knee 70, left knee 69, left ankle 68, right hip pitch 67** | 6.76 V | 2.06 A at 19.7 V, 40.6 W |

No run cut a servo (the C001 cuts above a 70 C reading; the STS3250 sheet rates -20 to 60 C operating, KNEE_TWIN.md, and its
knees read 60 to 70 C in every run here, the BLOCKER the knee job already lists). The DCB200 duck walks at a third of
today's speed with the stock policy and puts the C001 hip pitch at its 70 C edge: more mass needs more hip and knee torque.

### 5.3 Falls in the push series
| Option | Hard shoves (29) | Policy on the floor (9) | Push ladder (24) | 15 N push series | 20 s walk | Worst 4 ms servo bus | Pack hit |
|---|---|---|---|---|---|---|---|
| Today (knee job, same knee) | 28 | not run | 8 (standing 15 to 25 N back and forward, 25 N left) | no fall | 1.321 m | 9.63 A | |
| **P45B, final pack (2.718 kg)** | 28 | 8 | **7** | no fall | **1.292 m** | 9.72 A | |
| P45B, first variant (+46 g, holder kept) | 28 | 8 | 6 | no fall | 1.244 m | | |
| 2S2P P30B stacked | **29** | 9 | **10** (back from 10 N) | **fell** | 1.212 m | | |
| DCBP034, belly | 28 | 8 | 3 | no fall | 0.936 m | 9.66 A | 26 runs (floor, shins) |
| DCB200, belly | 23 | 7 | 2 | no fall | **0.502 m** | 9.78 A | 28 runs (floor, shins, feet) |

The heavy, low belly pack makes the duck harder to push over (2 of 24 on the ladder) but it walks much slower and its shins
strike the pack. The 2S2P pair stacked in the bay moves the centre of mass 4.4 mm back and falls more: the narrow side the
added-mass study found. The P45B pack changes nothing that matters (7 against 8 of 24, the same walk within 2 %). Servo bus
peaks are the same for every option (9.6 to 9.8 A held 4 ms), well inside the CC BEC Pro's 20 A.

### 5.4 Get-ups
The get-up library's three scripted programs on every rest pose of our build at 7.2 V (V1 knee job's getup job, knee model
`sts3250_high` as the knee job ran it):

| Option | Back | Side | Front |
|---|---|---|---|
| Today (knee job) | 19 of 19, up 10.3 s median | 10 of 10, up 11.8 s | 0 of 9: the front program file fails to load (an unpack error, the same in the knee job's run) |
| P45B final pack | 19 of 19, up 10.3 s | 10 of 10, up 11.8 s | same error |

With the `sts3250_high_d0.56` stand-in every get-up rises (the same 10.3 and 11.8 s) but fails the 1 deg joint-limit rule
(1.39 to 1.40 deg over) for both today and the P45B, so the stand-in is not used for get-ups. The DeWalt get-ups did not run
(the first chain hit its limit); with the pack under the belly, the back program's bridge clears it by 15.9 mm (CAD check).
The front-program error is a pre-existing problem of the get-up library, not of the battery (anticipated problem 9).

### 5.5 Runtime per charge, with the converter losses (calc only, on the sim's pack power)
Calc only, on the twin's pack power. 2S: the D16 walk stop comes at 1895 mAh on today's pack (the knee job's run); a bigger
pack at the same current stops at least at the same share of its charge (it sags less), so the P45B stop is taken at
1.5 x 1895 = 2843 mAh (conservative). 5S: usable charge to a 17.0 V walk stop under the walking load on the P30B surface
(73 to 75 % of the rated Ah), the converter at 0.85 (B37, ASSUMPTION) inside the twin's pack power. Standing 16 W at the pack
(TWIN_LIVE.md: 2.0 to 2.2 A on the 2S pack) for the 50/50 mix.

| Option | Usable energy | Walking pack power | Continuous walking | 50/50 session |
|---|---|---|---|---|
| Today P30B | 13.6 Wh to the stop | 34.1 W | 24.6 min (twin) | 33 min |
| P45B (chosen) | 20.5 Wh | 32.6 W | 39 min | 50 min |
| P50B | 22.7 Wh | 32.6 W | 43 min | 56 min |
| 2S2P P30B | 27.3 Wh | about 33 W | about 50 min | about 66 min |
| DCBP034 | 22.2 Wh | 36.7 W | 36 min | 50 min |
| DCB203 | 26.3 Wh | 36.7 W | 43 min | 60 min |
| DCB200 | 40.1 Wh | 40.6 W | 59 min | 85 min |
| DCB204 | 54.0 Wh | 40.6 W | 80 min | 114 min |
| DCB205, DCBP520 | about 67 Wh | about 42 W (calc) | about 95 min | about 140 min |

In a 32 C room these walking minutes are not reachable in one stretch for any pack: the live twin needs the thermal guard
and rests (TWIN_LIVE.md), so the session column is the honest one.

### 5.6 Structure: fall loads scaled by mass (calc only)
Calc only (the structure twin's factors scaled by the joint loads of the 20 s walk in the push runs, or by mass):
- Walking joint loads, peak of the 20 s walk: knee axis moment 2.13 Nm today, 2.27 P45B, 2.15 DCBP034, 2.60 DCB200; hip roll
  bending 2.36 Nm today, 2.38 P45B, 3.41 DCBP034, **4.01 DCB200 (+70 %)**. One run each, so about +/-10 % (ASSUMPTION).
- roll_to_pitch at 3 walls (D38), walking SF 1.81 and push 1.20 (twin/knee/KNEE_TWIN.md), scaled by the hip roll bending:
  P45B 1.79 / 1.19 (unchanged), DCBP034 1.25 / 0.83, **DCB200 1.07 / 0.71**. The lab margin is 2 walking and 1.2 in falls.
- Falls from standing (rigid tipping over the sole edge, calc only): released energy x1.016 (P45B), x1.019 (DCBP034 belly),
  x1.049 (DCB200 belly), x1.335 (DCB200 on top), x1.196 (DCB200 on the back); head speed at impact x1.00 to x1.03. A low pack
  adds mass but little fall energy. The servo horn and case screws under margin in falls (STRUCTURE_TWIN.md) move with the
  energy: about +5 % for the DCB200 belly, about +2 % for the P45B. Neither fixes nor breaks them; D26 stays open.
- The belly mount itself has to carry the pack in a fall: 0.68 kg at the mid fall level's 128 g trunk shock (MOUNTING.md V1
  track 2 note) is about 850 N on the rail latch (calc only). No rail adapter publishes a latch rating: BLOCKER.

### 5.7 What a retrain at the new mass needs
The policy was trained at 2.107 kg; the live twin uses the stock policy everywhere here. What a retrain needs:
- **P45B (chosen):** nothing new beyond D32. The knee retrain (run2_sts3250, train/TRAIN.md in the shared lab gym, overlay
  gym/overlays/duck) uses `mass ours` from duck_inertials.json, so duck_inertials.json is rebuilt from the new mass budget
  (2.718 kg with the knees; the gym's duck_robot.py write-inertials) before the run. The bench BAM test of one STS3250 still
  comes first (D38, open question 9).
- **A DeWalt pack (not chosen):** a new inertial set (trunk 1.49 kg for the DCB200, centre of mass 27 mm lower), the pack as a
  collision box so the policy learns to keep the shins off it (or hip yaw and roll limits cut to about +/-15 deg, which
  changes the gait), the voltage range narrowed to 7.0 to 7.2 V (regulated), mass randomization over +/-10 % of 3.24 kg, and
  the knee preset; the same $18 ledger cap. GPU time for this mass was not estimated (BLOCKER).

## 6. Heat
- **Converter (CC BEC Pro):** section 4.1: 2.6 to 7.3 W at 5S depending on its unpublished efficiency (B37); on the chosen
  2S pack nothing changes from today.
- **The pack in a 32 C room:** P45B at the twin's walking current: 2 x 4.37^2 x 0.015 = 0.57 W (DC 15 mOhm [M2]), against
  0.72 W for today's P30B at 4.61 A (17 mOhm [M1]): about 20 % less cell heat. The cells sit in the trunk, where the thermal
  twin puts the air at 38 to 48 C at the battery stop and the cells at 44 to 56 C (THERMAL_TWIN.md), inside the Molicel
  -40 to 60 C discharge range [M1], [M2] but close to its top at 32 C. A DeWalt pack outside the shell would sit near room
  temperature (0.2 W at 2 A, calc only), inside DeWalt's 40 C use limit at 32 C [D1].
- **Charging limits:** Molicel 0 to 60 C [M1], [M2]; the dock rule 5 to 45 C at the cells (DOCK_INTERFACE.md, CHARGE_INTERFACE.md);
  DeWalt 4 to 40 C air [D1]. A duck that just stopped walking at 32 C is over 45 C and waits on the dock.
- **Charge heat at the dock's 2.0 A (DOCK_INTERFACE.md):** cells 2 x 2.0^2 x 0.015 = 0.12 W, BMS 2.0^2 x 0.025 = 0.10 W (main loop
  25 mOhm max, POWER.md), fuse and XT30 under 0.05 W: about 0.27 W in the bay. Adiabatic bound over the 2.6 h charge: 0.27 W x
  9360 s / (145 g x about 1.0 J/(g K)) = 17 K; with any path to the trunk air it is a few K (bay thermal resistance not
  known: BLOCKER, ASSUMPTION 10 to 20 K/W gives 3 to 5 K). Charging does not heat the pack; walking does.
- **The servos working harder:** the heavier the duck, the hotter the hips and knees (section 5.2): the DCB200 puts the C001
  hip pitch at its 70 C edge in a 32 C room; the P45B adds 1 C at the hottest knee.

## 7. Charging on the dock (track 8)
Full interface: CHARGE_INTERFACE.md (written first, for track 8). In short, for a DeWalt pack charged in place (calc only):
- Voltage: 5S CC/CV to 20.5 V (4.10 V per group, as a DeWalt charger leaves it [S1]); never above 21.0 V.
- Current: 2.0 A design value; charge time about 1.0 h (DCBP034) to 2.9 h (DCB205) at 2 A (capacity / I x 1.15, calc only).
- Thermistor: the 10 k NTC between B+ and TH [S2]; charge only between 4 and 40 C air [D1].
- Contacts: B+ and B- (3 A or more) plus one sense contact (TH or a pack-identity resistor); the robot keeps its contacts dead
  with a reverse-blocking switch until the dock drives them.
- Where the charger lives: in the dock (a 5S Li-ion CC/CV charger with a TH check). A genuine DeWalt charger cannot reach a
  pack held in the duck. Balancing needs C1 to C4, so the robot watches the groups (ADS1115) and asks for a bench DeWalt
  charge when they drift.
- The key point for any pack: standing with the torque on draws 2.0 to 2.2 A from the 2S pack (TWIN_LIVE.md), about 16 W, more
  than a 2 A charger supplies, so the duck must rest with its servos unloaded on the dock or the charger must cover the load.
- The dock job's DOCK_INTERFACE.md (2026-11-04 ET) takes CHARGE_INTERFACE.md's 2S plan, the 2.0 A design value, the 3 contacts and the 5 to 45 C rule (D43).

## 8. The simpler options: today's pack, 2S2P P30B, 2S P45B
Ahmed, 2026-11-04 about 11:10 PM ET (relayed by the lead): "go with the P45B cells then .. Or are there better batteries out
there? .. Okay, cool. Are our batteries swappable?" and at 11:13 PM ET: "I think we're good on the swappable battery, but we
definitely need to secure the self-charge. ... I do really expect the simplest solution, the cheapest and the most reliable one,
all at once".

### 8.1 Today's pack, 2S2P P30B and 2S P45B (sim pass only, calc only)

| Option | Fits today's bay | Mass | Energy | Change | Twin result |
|---|---|---|---|---|---|
| Today, 2S1P P30B | yes | 119 g (cells and holder) | 21.6 Wh | none | 24.6 walking min, 33 min sessions, 63 C knee |
| 2S2P P30B | **no**: 4 x 18650 need twice the bay; stacked in the bay the centre of mass moves 4.4 mm back | +119 g | 43.2 Wh | a second bay or a bigger one | more falls (ladder 10 of 24, push series fell); a forward seat needs CAD and wiring |
| 2S1P P45B 21700 | no: the bay grows 2.1 mm deeper and 2.9 mm wider (body_back only) | +26 g net with the holder replaced by a spot-welded pack | 32.4 Wh | body_back, BOM 6 and 7 | 39 walking min, 50 min sessions, same falls and get-ups, 64 C knee |

### 8.2 Is there a better cell than the P45B? (research, calc only)

Our need per cell (2S1P, so each cell carries the pack current): walking mean 4.6 A (the knee job's baseline session, calc
from its charge), RMS about 5 A, the worst 4 ms window 15.89 A with the track 1b guard and 20.6 A for at most a few ms in the
60 N shove (ELECTRICAL_TWIN.md). Prices and stock read 2026-11-04 ET at the 18650 Battery Store (the BOM's cell seller, line 6)
through its own product search [R11]; nothing bought.

| Cell (size) | Capacity, energy (typical) | Mass (max) | Wh/kg | Continuous current | DC resistance | Loss at 5 A RMS | Fits the bay | Price, stock [R11] | Source |
|---|---|---|---|---|---|---|---|---|---|
| Molicel P30B (18650, today) | 3.0 Ah, 10.8 Wh | 47 g | 230 | 30 A (80 C cut-off) | 17 mOhm (50 % SOC) | 0.43 W | yes (today) | $8.99, in stock | [M1] |
| **Molicel P45B (21700)** | 4.5 Ah (4.35 rated), 16.2 Wh | 70.0 g | 231 | 45 A | 15 mOhm (50 % SOC); 7 mOhm AC | 0.38 W | needs the bay change (section 8.3) | $9.99, **out of stock** | [M2] |
| Molicel P50B (21700) | 5.0 Ah (4.85 min), 18.0 Wh | 71 g | 254 | 60 A (80 C cut-off) | 12.8 mOhm (50 % SOC) | 0.32 W | same as the P45B (21.55 x 70.15 mm max) | $11.99, in stock | [M3] |
| Molicel P42A (21700) | 4.2 Ah, about 15.1 Wh (calc, 3.6 V) | not read: BLOCKER | | 45 A (store title) | not read | | same as the P45B | $6.99, out of stock | [R11] only (no data sheet read) |
| Molicel P60B (21700) | 6 Ah, 21.6 Wh; "low internal resistance of 12.8 mOhm" (press release) | not read | | 100 A (third-party library, UNVERIFIED) | 12.8 mOhm (press release) | 0.32 W | same size (21700) | not listed at the store: no US price or stock found (BLOCKER) | [M4] |
| Samsung 50S (21700) | 5.0 Ah, 18.0 Wh | 72.0 g | 250 | 25 A (45 A with an 80 C cut) | not found | | same as the P45B | $9.99, in stock | [SS1], [R11] |
| Samsung 40T (21700) | 4.0 Ah, 14.4 Wh | not read | | 35 A (store title) | not read | | same | $6.99, out of stock | [R11] only |
| Murata VTC6A (21700, not an 18650) | 4.1 Ah | 72.7 g (third-party library) | about 203 | 40 A (third-party library) | not found | | same | not found at the store | [MU1] (no Murata sheet read) |
| Murata VTC6 (18650, fits today's bay) | 3.12 Ah | 46.6 g typical (Murata sheet) | about 241 | disputed: 15 A without and 30 A with an 80 C cut (reseller) | not read | | yes | not read | [MU2] |
| Amprius (silicon anode) | pouch cells; no cylindrical cell found for this bay | | | | | | no (pouch, needs a new holder and compression) | not read | not pursued |

Verdict by Ahmed's three tests together:
- **Simplest:** every 21700 needs the same bay change; the P30B and VTC6 need none but give little or nothing (VTC6: +4 % capacity
  with a disputed current rating). Among the 21700s there is no difference in the change.
- **Cheapest:** P45B $9.99, Samsung 50S $9.99, P50B $11.99 per cell, so $4 more per duck for the P50B; all are a few dollars per
  duck against the $1,146 build.
- **Most reliable:** all the Molicel cells carry our 20 A peaks with 2x to 3x headroom; the Samsung 50S is rated 25 A without a
  temperature cut, the least headroom over our 20.6 A shove. The P50B has the lowest resistance (12.8 mOhm, so the least heat and
  sag) and the most current (60 A). Cycle life was not read for any cell here (BLOCKER for the final word).
- **Decision (lead rule: keep the P45B unless another cell clearly wins): the P45B stays the pick.** The P50B is better on paper
  (+11 % energy, -15 % resistance, in stock) but not by enough to change the decision, and it fits the same bay, so it is the
  **drop-in alternate if the P45B is still out of stock when Ahmed orders** (same bay, same BMS, same wiring; the twin numbers
  scale with capacity, +11 % runtime). The P60B is not on sale in the US at the store read, so it is not an option yet.

### 8.3 What the P45B needs in the bay (CAD check only)

The bay is a 20 x 41 x 76.5 mm box inside body_back closed by battery_pack_lid (DECISIONS.md D23); today's 2 x 18650 holder is
20 x 41 x 76 mm (MOUNTING.md). A P45B is 21.40 +/- 0.15 mm by 70.00 +/- 0.15 mm [M2] (P50B 21.55 x 70.15 max [M3]), so two cells
side by side need at least 21.55 x 43.1 x 70.15 mm before any holder: the bay must grow by about 2 mm in depth and 2 to 3 mm
in width at the least, more with a holder (a 2 x 21700 holder's size was not read: BLOCKER). Phase 2 (the implementation the
lead ordered) does this in body_back and battery_pack_lid.

### 8.4 Swapping the battery (not pursued, D45)

A tool-free slide-in pack was drafted and then dropped on Ahmed's words of 11:13 PM ET ("I think we're good on the swappable
battery, but we definitely need to secure the self-charge"; D45). Today's swap, as built (twin/assembly/ASSEMBLY_TWIN.md
section 3, D35, D38, MOUNTING.md): take the 6 M3x8 screws out of body_back (2.5 mm hex key; 6 since D39, twin/holes), pull body_back 20 mm back on its wires, take the 3 M2.5x10 lid screws out with the 2.0 mm key's short arm, lift
the lid off with the fuse holder and the Pololu 2813 still taped to it, unplug the XT30, lift the cells out, and reverse. Time,
calc only: about 18 screw operations at 8 to 12 s each (DFMA, twin/screws/SCREWS_TWIN.md) plus 2 plug and 4 cell moves at 2 to
4 s: about 3 to 4.5 minutes, plus handling (BLOCKER: not timed). The pack charges in place on the dock (CHARGE_INTERFACE.md),
so swapping is only for a spare.

## 9. What the change needs
For the chosen P45B (implemented on the local branch, see section 14):
- Parts: 2 x Molicel P45B, $9.99 each at the 18650 Battery Store, out of stock when read [R11] (P50B $11.99 in stock, same bay);
  pure nickel strip and a 2S heat-shrink sleeve with a fish-paper ring at the positive ends (prices not read: BLOCKER); the
  pack spot-welded, never soldered (a spot welder or a pack shop: BLOCKER). The 2 x 18650 holder ($9.99) goes. The BMS, the
  charger board, the fuse, the switch, the XT30, the BEC and every wire stay.
- Mount: the bay in body_back grows from 20.6 x 41.4 x 83.5 mm to 25.7 x 44.3 x 83.5 mm free space (2.1 mm toward the back
  wall and 0.5 mm behind the lid pad, 1.45 mm into each side wall); battery_pack_lid unchanged; a 1 mm foam pad on the lid's
  centre pad; the BMS and XT30 seats unchanged.
- Power path: unchanged (2S, 8.4 V full). Guard: unchanged (D16 servo-voltage rules); its minutes grow with the capacity.
- Retrain: the D32 knee retrain with duck_inertials.json rebuilt at 2.718 kg.
If a DeWalt pack were chosen anyway: the pack and adapter ($139.00 + $49.93 for the DCB200), the pack monitor, group monitor
and TPS3700 cuts ($25.82), a 5S dock charger, a belly rail mount (new STL), the guard rewrite of section 4.4, a retrain at
3.24 kg with hip limits, and the BOM lines 6, 7, 8 and 11 removed.

## 10. BLOCKERs
1. P45B stock: out of stock at the BOM's seller when read; the P50B is the in-stock drop-in [R11].
2. P45B and P50B cycle life not read; P42A, 40T masses and resistances not read; P60B has no US price or stock found.
3. The spot-welded pack: nickel strip, sleeve and welding (tool or shop) not sourced or priced.
4. The bay's thermal resistance (charge and walking heat in the bay).
5. The battery swap time, as built, not timed (calc 3 to 4.5 min plus handling).
6. DeWalt (only if chosen): cell models and pack sizes of the DCB203, DCB204, DCB205 and DCBP034; pack current limits; the
   CC BEC Pro efficiency at 5S (B37); the Pololu 2813 OFF response for the over-voltage cut; the rail adapter's net mass,
   current and latch rating; the XT30U and wire voltage ratings; GPU time for a 3.24 kg retrain.
7. Sims not run: the 2S2P session, the DCB205 session and the DeWalt get-ups (the chain hit its 2 h limit); the front get-up
   program's load error (pre-existing).
8. The STS3250 knees read 60 to 70 C in every 32 C session (its sheet rates 60 C): the knee job's BLOCKER, unchanged by the pack.

## 11. Anticipated problems, each with its fix
1. P45B still out of stock when Ahmed orders. Fix: the P50B, the same bay and pack (+$4 per duck, +11 % energy).
2. A builder without a spot welder. Fix: order the 2S pack built (P45B pair, nickel strip, sleeve, 16 AWG leads) or buy tabbed
   cells; never solder to a cell.
3. The lid's centre pad (x -121.5 mm) presses the pack. Fix: the pack front sits 0.5 mm behind it (the cut is placed so) with
   a 1 mm foam pad on the lid pad; checked in CAD (0 overlap).
4. Thinner bay walls (3.65 mm at the sides, 9.3 mm at the back, from 5 and 14.4). Fix: the walls are inside the shell and
   carry no fall load path of D39's ear seats (CAD); check the first print of body_back for the side walls.
5. Cells hotter than 45 C when the duck docks after walking. Fix: the dock's 5 to 45 C start rule; the duck rests torque-off.
6. A dock charge with the duck awake takes longer (0.75 A of the 2.0 A goes to the duck, DOCK_INTERFACE.md). Fix: the duck
   switches off on the dock and the dock wakes it (DOCK_INTERFACE.md).
7. The dock's sense NTC must touch the cells. Fix: a 10 k bead taped in the valley between the two cells under the lid pad,
   its leads out with the pack leads (the dock job wires it; seat reserved here).
8. Mismatched cells drift (no balancing on the Tenergy board). Fix: buy a matched pair from one batch and check both cell
   voltages at the first 10 charges (POWER.md section 5).
9. The front get-up program fails to load in the get-up library. Fix: the get-up job re-saves front_final.json (not this job).
10. If anyone mounts a DeWalt pack later: the 20.5 V behind one BEC can burn every C001. Fix: the over-voltage cut of section
    4.4 before any power-up.

## 12. Phase 2 file list

Phase 2 is the P45B implementation of section 14 (D44, D45: no further go needed). For a DeWalt pack (not chosen) it would
have been a new belly rail mount STL, POWER.md, WIRING.md and wiring/netlist.yaml, the BOM, bench/battery_guard.py and
software/SOFTWARE.md section 5, DECISIONS.md D16, the mass budget, the gym inertials and the training preset, MOUNTING.md,
HARDWARE_AUDIT.md and TEST_PLAN.md.

## 13. Files of this job and how to run them
All in the job's scratch folder (v1_out/battery/, not in git)  (not in either repo):
- tools/batt_twin.py: the option list (masses, seats, pack model), `info OPT`, `session OPT k=v`, `pushes OPT DIR`, `getup OPT DIR`.
  It patches duck_robot.robot_spec and the P30B pack class inside its own process only.
- tools/mount_check.py: the CAD check of section 3.2 (runs/mount_check.json). tools/geom_probe.py: trunk extents, joint ranges.
- tools/chain.sh: the sim chain, one job at a time, each under the gym's train/ramcap.py --cap-mb 3000.
- tools/analyze.py and tools/calcs.py: the tables. runs/: outputs (chain/results.jsonl, pushes_*/, getup_*/, info.jsonl,
  bay_items.json). web/: the pages read (data only, run with python3 -I).
- Baselines reused, same code and knee: the V1 knee job's runs (the V1 knee job's scratch runs: the sts3250_high_d0.56 continuous
  backlash 32 C session and its pushes).

## 14. Implemented: the P45B pack (local branch v1-battery-local, not pushed)

Done 2026-11-04 to 2026-11-05 ET on a worktree of origin/altaay-lab at 3191e03 (D42 to D45 merged). Details and numbers:
altaay_lab/twin/battery/BAY.md. In short: print/body_back.stl grown bay (CAD check only: the pack clears every part, the lid
screws keep 3.3 mm or more, the charger screw its 1.0 mm, walls 2.25 to 9.65 mm); battery_pack_lid, the BMS and the XT30 seats
unchanged; body_back re-sliced (79.21 g, 6.54 h, support 10.72 g); BOM lines 6 and 7, the full BOM rows E01 and E02, bom.json;
sim/mass_budget.py and MASS_BUDGET.md (2.72 kg, centre of mass 1.1 mm back); the netlist PACK entry; MOUNTING.md; the viewer
pack geometry and labels; c1, c2, c4 the same as the base and c9 PASS; the viewer test STATE loaded, ERRORS none, 0 mismatches;
pushes, the 20 s walk and get-ups at the new mass (sim pass only). No DECISIONS entry: the cell is the P45B of D44.

## Sources
- [D1] DeWalt batteries and chargers instruction manual NA485944 (GB/XE): https://service.blackanddecker.com.au/i/DEWALT/GLOBALBOM/XE/DCG412N/1/Instruction_Manual/EN/NA485944_man_dewalt_batteries_and_chargers_GB_XE.pdf
- [D2] DeWalt Li-ion battery product data sheet (packs of 100 Wh or less): https://anchors.dewalt.com/anchors/_documents/uploads/_msds_reports/DW_LithiumIonBatteryPacks-SDS-EN_DDS1.pdf
- [D3] DCB203 https://www.dewalt.com/en-us/product/dcb203/20v-max-2-ah-battery ; [D4] DCB204 https://www.dewalt.com/en-us/product/dcb204/20v-max-4ah-battery ; [D5] DCB205 https://www.dewalt.com/en-us/product/dcb205/20v-max-5ah-battery ; [D6] DCBP034 https://www.dewalt.com/en-us/product/dcbp034/20v-max-xr-compact-battery
- [S1] https://www.sevarg.net/2016/09/11/dewalt-20v-max-30ah-battery-pack/ ; [S2] https://www.sevarg.net/2017/04/22/dewalt-20v-max-60ah-pack-teardown/
- [R1] The Power Tool Store product data (Shopify .js): https://thepowertoolstore.com/products/dewalt-dcb203 , -dcb205, -dcbp034, -dcbp520
- [R3] https://toolup.com/products/dewalt-dcb200-20v-max-lithium-ion-battery-pack-3-0-ah (weight, via search; direct fetch refused)
- [R4] https://www.toolnut.com/products/dewalt-dcb200-20-v-max-lithium-ion-battery-pack ; [R5] https://www.coastaltool.com/products/dewalt-dcb200-20v-max-battery
- [R6] https://thepowertoolstore.com/products/dewalt-dcb204 (price via a search index) ; [R7] DCBP520 retailers via search: https://www.toolsource.com/batteries-and-chargers-c-294_297/powerstack-5ah-starter-kit-p-422621.html , https://thepowertoolstore.com/collections/vendors/products/dewalt-dcbp520
- [R8] https://vxb.com/products/dewalt-20v-battery-adapter-for-power-wheels-diy-co ; [R8b] https://vxb.com/products/power-wheels-adapter-for-dewalt-20v-battery-and-18 ; [R9] https://www.walmart.ca/en/ip/2-Pack-Power-Wheels-Adapter-Dewalt-Switch-Fuses-12AWG-Wire-20V-Battery-Conversion-Kit-6-PCS-30Amp-Fuses-DCB200-DCB203-DCB205-DCB206-DIY-Truck-Robotic/5H1AQLOL0PFM
- [R10] https://www.printables.com/model/504186-dewalt-20v-battery-mount-bracket-small , https://www.printables.com/model/102778-dewalt-20v-battery-mount , https://www.printables.com/model/226563-dewalt-20v-battery-dock , https://makerworld.com/models/673592
- [R11] 18650 Battery Store product search (suggest.json), read 2026-11-04 ET: https://www.18650batterystore.com/products/molicel-p45b , /molicel-21700-p50b-5000mah-50a-battery , /molicel-p42a , /samsung-50s-21700-5000mah-25a-battery , /samsung-40t , /molicel-p30b-18650-3000mah-36a-battery
- [C1] Castle CC BEC comparison chart (product data of 010-0153-00, chart covers 010-0004-01): https://castlecreations.com/products/voltage-regulator-cc-bec-2-15a-max-output-14s-58-8-volts-waterproof-010-0153-00 ; price: https://castlecreations.com/collections/voltage-regulators-becs
- [P1] https://www.pololu.com/product/2813 ; [P2] https://www.pololu.com/product/4892
- [A1] https://www.adafruit.com/product/4226 ; [A2] https://www.adafruit.com/product/1085 ; [T1] https://www.ti.com/product/TPS3700
- [M1] Molicel P30B data sheet v1.0: https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf
- [M2] Molicel INR21700P45B-01 v0.2: https://www.kronium.cz/uploads/p45b-datasheet.pdf (the data sheet v1.2 summary also at https://www.imrbatteries.com/content/molicel_p45b.pdf)
- [M3] Molicel INR-21700-P50B data sheet: https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
- [M4] Molicel P60B launch, 2025-06-24: https://www.prnewswire.com/news-releases/molicel-launches-inr-21700-m65a-and-inr-21700-p60b-pioneering-market-leading-power-for-e-bikes-and-light-electric-vehicles-302489911.html ; https://www.aboutenergy.io/cell-library-/molicel-inr-21700-p60b
- [SS1] Samsung INR21700-50S specification: https://www.dnkpower.com/wp-content/uploads/2022/07/SAMSUNG-INR21700-50S-Cell-Specification.pdf (values via search)
- [MU1] https://www.aboutenergy.io/voltt-battery-library/murata-vtc6a ; [MU2] https://www.murata.com/-/media/webrenewal/products/batteries/cylindrical/datasheet/us18650vtc6-product-datasheet.ashx
- Lab files (duck repo): POWER.md, MOUNTING.md, DECISIONS.md, STATE.md, BOM.md, sim/MASS_BUDGET.md, sim/ADDED_MASS_SIM.md, SERVO_UPGRADE_OPTIONS.md, twin/electromech, twin/electrical, twin/thermal, twin/knee, twin/structure, twin/assembly, twin/screws; the shared lab gym (overlay gym/overlays/duck): twin_live, v1_elec, v1_knee, getup, train; the dock job's DOCK_INTERFACE.md.
