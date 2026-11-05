# SERVO UPGRADE OPTIONS: what a stronger servo would mean (contingency only)

Status 2026-11-05: **Option A is taken** (DECISIONS.md D32; Ahmed 2026-11-04 6:18 PM ET: "yes, put STS3250s on both knees"). The twin results are in twin/knee/KNEE_TWIN.md (sim pass only); BOM line 1b; the one-unit test is TEST_PLAN 15. The rest of this file is the study as written.

Written 2026-11-01, 10:47 to 10:53 PM ET, by agent SU (research; work started 10:05 PM ET). Nothing was bought, posted or changed. No other lab file was edited. Prices and stock were read on supplier pages on 2026-11-01 between about 10:10 and 10:45 PM ET, before tax and shipping. Sim numbers are sim pass only. Source tags in square brackets point to the Sources list at the end; [D] marks a number derived here, with the method next to it.

Ahmed's question: "if servos are running hot and we exceeded the limit, we may need something higher, unfortunately, which means an entire redesign, perhaps."

## Short answer

- **It is not a redesign.** Feetech makes stronger servos in the same body as the STS3215: the STS3250 (12 V, 50 kg.cm) and the STS3235 (12 V, 30 kg.cm). Their drawings show the same 45.22 x 24.72 x 35 mm case, the same 25T output spline in the same place and the same horns [F4, F5, F9]. The 12 V STS3215 (Feetech lists the C018; Seeed sells the C047 with the same published spec) and the faster C044 and C046 use the same plastic body [F3, F6, F7, F8]. A servo swap changes no printed part. Only the screws into an aluminium case change, from self-tapping to M2 machine screws [F9].
- **Our extra mass is not the cause of the knee heat.** In sim the right knee loses 3.55 W (plain model) and 5.58 W (backlash model) at the trained 2.11 kg mass, and 3.74 W and 5.80 W at our 2.77 kg [D, sim run below]. The stock gait itself runs the C001 knees at 3.4 to 5.2 times their rated copper loss. Retraining for 2.77 kg can win back about 5 % at most.
- **Walking slower buys little.** A 0.10 m/s command cuts the knee loss by 11 to 12 %. At 0.05 m/s the stock policy does not step at all [D].
- **Only the 12 V motors cut heat per newton-metre.** At the same torque, the STS3250 makes 0.25 to 0.41 times the C001's copper loss, and the C018/C047/STS3235 0.21 to 0.74 times. The C044 is about 0.77 times, the C046 2.4 times (worse) [D from F2 to F7].
- **On our 2S pack only the STS3250 works.** At our 7.2 V bus it is estimated at 4.7 rad/s no-load and 30 kg.cm stall, against 5.3 rad/s and 19 kg.cm for the C001 [D]. The 12 V STS3215 and the STS3235 would crawl at about 2.8 rad/s at 7.2 V, so they need a 3S pack, and a 3S pack does change the battery bay.
- **Every option needs a new BAM identification and a retrain.** BAM's public library has only the STS3215 7.4 V [B1]. One 300 M-step training run took 1 h 11 min on an RTX 3090 in a third-party build [X1].
- **Recommendation (section 5):** if TO1 gives a knee thermal resistance above 11 K/W, put STS3250s on the two knees and keep the 2S pack and the 7.2 V BEC. Between 6 and 11 K/W, keep the C001 and walk in bouts with the lab's thermal guard. At or below 6 K/W, change nothing.

## 1. Comparison table

The C001 row is today's servo. "On our bus" means the 7.2 V BEC output (POWER.md), or 12 V for a 3S pack.

| Servo (Feetech code) | Rated voltage | Stall torque, stall current | No-load speed | Rated torque / current; Kt; R | Gear | Case, material, weight | On our bus [D]: no-load speed, stall, speed at 11 kg.cm | Knee copper loss at today's knee torque [D] | US supplier, price, stock (2026-11-01) | Runtime servo library unchanged? |
|---|---|---|---|---|---|---|---|---|---|---|
| **ST-3215-C001** (today) | 6 to 7.4 V typical, 4 to 7.4 V input [F2] | 19.5 kg.cm (1.91 Nm), 2.5 A at 7.4 V [F2] | 0.192 s/60 deg = 52 RPM (5.45 rad/s) at 7.4 V [F2] | 5 kg.cm / 0.65 A; 8 kg.cm/A; 2.5 ohm [F2] | 1:345 [F2] | 45.2 x 24.7 x 35 mm, PA+GF plastic, 55 g [F2] | 7.2 V: 5.3 rad/s, 19.0 kg.cm (1.86 Nm), 2.2 rad/s | 3.1 to 5.8 W [L2]; 3.4 to 5.2 x its rated loss | Seeed: $20.00 (1 to 9), $19.00 (10+), in stock, US and China warehouse options [P1] | Yes (the code is written for it) [U2] |
| **ST-3215-C044** | 6 to 7.4 V typical, 5 to 8.4 V input [F6] | 27.4 kg.cm (2.69 Nm), 3.8 A at 7.4 V [F6] | 0.116 s/60 deg = 86 RPM (9.0 rad/s) [F6] | 9 kg.cm / 1.2 A; 7.2 kg.cm/A; R not published [F6] | 1:191 [F6] | 45.2 x 24.7 x 35 mm, PA+GF, 55 g [F6] | 7.2 V: 8.8 rad/s, 26.7 kg.cm (2.61 Nm), 5.2 rad/s | 0.77 x C001 = 2.4 to 4.5 W; 1.2 to 1.9 x its rated loss | Seeed: $21.99, $20.99 (10+), in stock [P2] | Walk path yes; configure scripts only if it reports model 777 (UNVERIFIED) [U3] |
| **ST-3215-C046** | 6 to 7.4 V typical, 5 to 8.4 V input [F7] | 14.4 kg.cm (1.41 Nm), 3.3 A at 7.4 V [F7] | 0.094 s/60 deg = 106 RPM (11.1 rad/s) [F7] | 4.8 kg.cm / 1.1 A; 4.36 kg.cm/A; R not published [F7] | 1:147 (the same sheet's title says 1:191) [F7] | 45.2 x 24.7 x 35 mm, PA+GF, 55 g [F7] | 7.2 V: 10.8 rad/s, 14.0 kg.cm (1.37 Nm), 2.3 rad/s | 2.4 x C001 = 7.5 to 14 W (worse) | Seeed: $21.99, $20.99 (10+), in stock [P3] | As C044 |
| **ST-3215-C018**, and **C047** (Seeed, same published spec) | 12 V, 4 to 14 V input [F3, F8] | 30 kg.cm (2.94 Nm), 2.7 A at 12 V [F3] | 0.222 s/60 deg = 45 RPM (4.71 rad/s) at 12 V [F3] | 10 kg.cm / 0.9 A; 11 kg.cm/A; 1.0 ohm [F3] | 1:345 [F3, F8] | 45.2 x 24.7 x 35 mm, PA+GF, 55 g [F3] | 7.2 V: 2.8 rad/s, 18 kg.cm, 1.1 rad/s (too slow). 12 V: 4.7 rad/s, 30 kg.cm, 3.0 rad/s | 0.21 to 0.74 x = 0.7 to 4.3 W; 0.9 to 1.4 x its rated loss | Seeed C047: $22.00, $20.90 (10+), in stock [P4] | As C044 |
| **STS3235** (ST-3235-C001) | 12 V, 6 to 12 V input [F4] | 30 kg.cm (2.94 Nm), 2.7 A at 12 V [F4] | 45 RPM (4.71 rad/s) at 12 V [F4] | 10 kg.cm / 0.9 A; 11 kg.cm/A; 1.0 ohm [F4] | 1:345 [F4] | 45.22 x 24.72 x 35 mm, aluminium, steel gears, 70.5 g [F4] | As C018 | As C018 | Waveshare (sold as ST3235): $41.99, $40.29 (4+), in stock, ships from China [W1]. Amazon B0D5B28BWF (Waveshare): listed, price hidden from a logged-out reader, UNVERIFIED [P9] | Walk path likely (shared STS register map [F10]); configure scripts: model number UNVERIFIED |
| **STS3250** (ST-3250-C001; C002 is the same servo without bracket [P7]) | 12 V, 6 to 12 V input [F5]; the FTServo wiki says 9 to 12.6 V [F9] (conflict) | 50 kg.cm (4.90 Nm), 4.2 A at 12 V [F5] | 0.133 s/60 deg = 75 RPM (7.85 rad/s) at 12 V [F5] | 16 kg.cm / 1.4 A; 11 kg.cm/A; 1.2 ohm [F5] | 1:345 [F5] | 45.22 x 24.72 x 35 mm, aluminium, coreless motor, steel gears, 74.5 g [F5] | 7.2 V: 4.7 rad/s, 30 kg.cm (2.94 Nm), 3.0 rad/s. 12 V: 7.85 rad/s, 50 kg.cm, 6.1 rad/s | 0.25 to 0.41 x = 0.8 to 2.4 W; 0.4 to 0.6 x its rated loss | OpenELAB (STS3250-C002): $73.99, in stock, warehouse China, 8 to 15 business days [P5]. Amazon B0HBJLD2QG (RCmall) and B0H6SBKSQ4 (DIYmall, ST-3250-C001 with bracket): ships from Amazon, price and stock hidden, UNVERIFIED [P6]. AIFITLAB $88, backorder [P7]. RCDrone $115, sold out [P8] | As STS3235 |
| Waveshare ST3215-HS (rejected) | 6 to 12.6 V [W2] | 20 kg.cm at 12 V, 2.4 A [W2] | 106 RPM (11.1 rad/s) at 12 V [W2] | not published; 8.3 kg.cm/A [W2] | not published | not published (UNVERIFIED) | 7.2 V: 6.7 rad/s, 12 kg.cm, 0.6 rad/s | 1.5 x C001 (worse) | Waveshare: $21.99, $20.63 (4+) [W2] | As C044 |

How the derived columns work:
- "On our bus": Feetech's no-load speed and stall torque scaled linearly with voltage (straight-line DC motor model), and the speed at 11 kg.cm read off that straight torque-speed line. These are estimates; measure them on a test unit.
- 11 kg.cm is about the knee's walking torque in datasheet units: the sim knee RMS current is 1.19 to 1.49 A [L2] and the C001 makes 8 kg.cm per amp [F2], so 9.5 to 11.9 kg.cm.
- Copper loss at equal torque scales as (Kt of C001 / Kt)^2 x (R / R of C001). The low end uses Feetech's published Kt and terminal resistance. The high end uses values derived from the stall line (Kt = stall torque / stall current, R = rated voltage / stall current), because the 12 V sheets' stall currents imply more resistance than their published 1.0 to 1.2 ohm. Applied to today's sim knee loss of 3.1 to 5.8 W [L2].
- "x its rated loss" = (knee current / the servo's rated current)^2. It needs no resistance value.
- Both heat columns assume the knee needs the same torque as today. Today's knee sits at its 3.23 Nm sim limit 14 to 23 % of the time in the backlash model (sim/ADDED_MASS_SIM.md table 4 [L10]); a stronger knee that no longer saturates may use somewhat more torque in those peaks.
- Copper loss leaves out iron, friction and electronics heat, as in sim/RUNTIME_THERMAL.md. No Feetech sheet gives a thermal resistance for any of these models; each gives only the operating range and the 70 C torque cut [F2 to F7].

Same case, checked two ways:
- From the URDF meshes wj-wk00-0122/0123/0124 (mini_bdx/robots/open_duck_mini_v2/) [D]: envelope 45.22 x 24.72 mm, 35.7 mm tall including the idle boss. The output axis is 10.1 mm from the near end and centred across the width. The drive horn is 19.95 mm across with four 2.5 mm holes on a 14.0 mm circle and a 3.2 mm centre hole; the idle horn is 19.95 mm across with a 6.1 mm bore. The top mounting holes (1.66 mm) sit 8.3 mm and 29.0 mm from the output axis, 20.5 mm apart across the case; the bottom holes are 20.5 mm apart as well.
- From Feetech's drawings [F9]: C001 and C018 share one drawing file. The STS3235 and STS3250 drawings show the same outline (45.22 x 24.72 x 35 mm), the 25T spline standing 3.4 mm proud, the 4.1 mm idle boss of 6 mm diameter, and mounting holes 20.5 mm apart across. Read off the drawing scale, the top hole rows are about 8.2 mm and 29.2 mm from the axis, within reading error of the mesh. The horn drawings are identical in all four spec sheets: 19.95 mm, four M3 holes on a 14 mm circle, 25T/OD5.9 spline [F2 to F5]. The difference: the aluminium cases label their mounting holes "4-M2.0" (machine thread) and the idle shaft takes an M3 machine screw. The plastic case takes PA2.0 self-tapping screws and a PA3.0x5 [F9].
- Other Feetech ST models are other sizes: for example ST-3020 and ST-3035 are 40.2 x 20.2 x 40 mm, ST-3025 is 40 x 20 x 40 mm, ST-3046 is 40 x 20 x 43.05 mm and ST-3095 is 30 x 65 x 48 mm [F11]. None of them fits without new printed parts.

## 2. What changes per option

### Option A: STS3250 on the two knees, 2S pack kept (the recommended contingency)
- **Pack, BEC, fuse, BMS: no change.** 7.2 V is inside the STS3250's 6 to 12 V rated input [F5]. Its estimated stall current at 7.2 V is 2.5 A (7.2 V / 2.86 ohm stall-line resistance), the same as the C001's 2.4 A [D]. Walking current drops (cable table below). The 15 A fuse, the Tenergy 32175 and the CC BEC Pro stay as in POWER.md. Caveat: the FTServo wiki lists 9 to 12.6 V for this model [F9], so the 7.2 V behaviour must be checked on one unit before buying more.
- **Policy: retrain needed. BAM identification needed.** BAM's library has no STS3250 [B1]. How the motor enters training now [U1]:
  - the MJCF class "sts3215" sets joint damping 0.56, frictionloss 0.068, armature 0.027, position kp 13.37 (17.11 in the backlash model) and forcerange plus or minus 3.23 Nm for every joint;
  - joystick.py clips motor targets to max_motor_velocity 5.24 rad/s per control step (one value for all joints);
  - randomize.py scales kp by U(0.9, 1.1), frictionloss by U(0.9, 1.1), armature by U(1.0, 1.05) and link masses by U(0.9, 1.1), and adds U(-0.1, 0.1) kg to the torso;
  - BAM maps its fit to these values: damping = kt^2/R + friction_viscous, frictionloss = friction_base, kp = vin x firmware P x 0.166 x kt/R, forcerange = vin x kt/R (SERVO_DEEP_DIVE.md E3 [L1]; bam/feetech/actuator.py [B1]).
  - For STS3250 knees: identify the servo at 7.2 V on a BAM pendulum bench (bam/feetech/record.py takes the arm mass, length, kp and vin [B1]), add an "sts3250" class for the two knee joints, give joystick.py a per-joint speed limit (a code change: the clip is one scalar today), add 19.5 g per knee to the model, and train. BAM's 0.166 error gain was measured on STS3215s with an oscilloscope; BAM fits a ratio to it (0.1 to 10), so a different firmware gain can be fitted [B1].
  - Runtime: the walk script sends one P to all leg servos (P 30, head 8) [U2]. The knees will want the P that the BAM fit implies. That is a lab change to the Runtime, which D6 keeps unmodified today [L5].
  - Possible shortcut, UNVERIFIED: with a BAM model of the STS3250, a sim run can test whether the stock policy still walks if the STS3250 knees are given a lower P and Torque Limit (register 48) that mimic the C001. If it walks, no retrain. If not, retrain.
- **Cables, current per hop** [D, scratch sim below]. One leg chain, worst leg, backlash walk at 0.15 m/s (the heaviest case), same joint motion as the stock policy. RMS A / worst 100 ms A:

  | Hop | C001 today, 7.2 V | Option A: STS3250 knees, 7.2 V | Option B: 12 V class on all leg joints, 11.1 V (C018/C047, STS3235) | Option B: STS3250 on all leg joints, 11.1 V (high end) |
  |---|---|---|---|---|
  | Feed lead SP1/SP2 (5 servos) | 1.86 / 2.52 | 1.19 to 1.30 / 1.99 to 2.02 | 0.46 to 0.94 / 0.67 to 1.29 | 0.63 / 0.86 |
  | S2, to hip roll (4 servos) | 1.81 / 2.50 | 1.17 to 1.28 / 1.95 to 1.97 | 0.46 to 0.92 / 0.65 to 1.28 | 0.62 / 0.85 |
  | S3, to hip pitch (3) | 1.69 / 2.29 | 1.04 to 1.15 / 1.83 to 1.86 | 0.42 to 0.86 / 0.58 to 1.17 | 0.57 / 0.79 |
  | S4, to knee (2) | 1.58 / 2.25 | 0.84 to 0.99 / 1.44 to 1.47 | 0.39 to 0.80 / 0.55 to 1.13 | 0.53 / 0.73 |
  | S5, to ankle (1) | 0.51 / 1.22 | 0.51 / 1.22 | 0.15 to 0.27 / 0.31 to 0.63 | 0.19 / 0.43 |

  All hops stay under the 3 A per Mini-SPOX contact that the lab uses (verify/c7_current_ratings.py [L6]). Option A changes no cable.
- **Printed parts: none.** Fasteners: the C001 knee servo takes 2 M2 self-tapping screws in each thigh (BOM_FULL.md F07: "Left thigh 2", "Right thigh 2" [L7]). The aluminium case is tapped M2 [F9], so those 4 screws become M2 machine screws. Thread depth is not published (UNVERIFIED): check it on the test unit. Horn screws and horns do not change [F2, F5].
- **Mass:** +19.5 g per knee, +39 g in all (74.5 g against 55 g [F2, F5]), about 1.4 % of 2.77 kg.
- **Runtime library:** the walk path (rustypot 0.1.0) has no model check and uses the fixed 4096-step conversion [U3]. Feetech says the STS register map applies to the whole STS TTL series [F10], so it should work unchanged. Nobody has reported this on a duck (UNVERIFIED). The configure scripts and check_voltage.py use pypot, which converts positions by model number: only 777 maps to "FEETECH_STS3215", and an unknown number falls back to a 1024-step, 300 degree range [U3]. If the STS3250 does not report 777 (UNVERIFIED; not found), configure_motor.py's final "go to 0" would send it to raw 512 instead of 2048. Fix: add its number to pypot's table (one line) or zero it with the Feetech tool.
- **Cost and lead time:** 3 x $73.99 = $221.97 at OpenELAB, 8 to 15 business days from China [P5]. Amazon may be faster (ships from Amazon), but its price was hidden [P6].
- **Walk time:** the two knees' copper loss falls from 6.8 W to 1.7 to 2.8 W (plain model), so pack power falls from about 25.0 W to 19 to 20 W, roughly 38 to 41 minutes to the D16 stop instead of 31 (linear estimate from sim/RUNTIME_THERMAL.md [L2]) [D].
- **Note 2026-11-03, a caution, not a decision** (twin/thermal/THERMAL_TWIN.md source R2 and section 6, applied by the twin integration agent; sim pass only): Robo9's comparison (2026-06) found the STS3250 the thermal outlier at 50 % load, 30 to 55 C in two minutes, and burnt one STS3250 motor in repeated 100 % load tests. So the STS3250's own heating is a question too, not only its unpublished thermal resistance. This note recommends no purchase: this file stays a contingency, the thermal guard with rests and the duty limits of THERMAL_TWIN.md section 6 come first, and buying needs Ahmed's OK. If option A is ever taken, the one-unit hold of section 5 is where this shows: log that unit's temperature at its walking current before any more are considered. TEST_PLAN 7.3 now holds the C001 at 0.9 A and 1.2 A, not the 1.5 A that section 5 names (DECISIONS.md D2 note of 2026-11-03); it still gives the R_th and time constant the section 5 table uses.

### Option B: all 14 servos to a 12 V class servo on a 3S pack
- B1: C018/C047, plastic, 55 g, same screws, $20.90 each at 10+ [P4]. 16 units (14 + 2 spares): $334.40.
- B2: STS3235, aluminium, 70.5 g (+217 g for 14), $40.29 each at 4+ [W1]. 16 units: $644.64.
- B3: STS3250, aluminium, 74.5 g (+273 g for 14), $73.99 each [P5]. 16 units: $1,183.84. At 12 V it gives 7.85 rad/s and 50 kg.cm [F5], about 3.9 times the C001's peak mechanical power on our bus (9.6 W against 2.5 W) [D].
- **Why all 14:** the four neck and head C001s are limited to 7.4 V [F2]. Either swap them too, or keep the BEC at 7.2 V on the neck lead SP3 only and feed the legs from the 3S bus (D15 already gives each chain its own lead [L5]).
- **Pack:** 3 x Molicel P30B (10.8 V nominal, 12.6 V full). The 2-cell holder (76 x 41 x 20 mm) is a press fit in body_back's battery bay with a 0.62 mm gap to the lid (MOUNTING.md [L8]). A third 18650 does not fit. So body_back and battery_pack_lid need a reprint with a bigger bay, or a 3S LiPo that fits 76 x 41 x 20 mm with less energy (no part sourced, UNVERIFIED). This is the only printed change in the whole upgrade question.
- **BEC:** the Castle CC BEC Pro takes 2S to 4S in and is adjustable from 4.8 to 12.5 V (POWER.md [L3]). Reprogram it with Castle Link to 11.1 to 12.0 V. The STS3250 is rated 6 to 12 V, so a full 3S pack (12.6 V) must not reach it directly. The C018/C047 takes 4 to 14 V [F3].
- **Fuse:** the 15 A, 32 V ATO stays [L3]. Walking current per hop falls (table above). Estimated stall per servo at 11.1 V: 2.5 A for C018/STS3235 and 3.9 A for STS3250 [D]. A jammed leg of STS3250s could push 4 x 3.9 = 15.5 A through hop S2 for up to 2 s, until each servo's 3.8 A / 2 s over-current cut [F5]. Lower the protection-current register, or use the 22 AWG made leads already in the BOM contingency (X1/X2, CABLE_MAP.md [L12]).
- **BMS and charger:** the Tenergy 32175 is a 2S board and the Adeept charger stops at 8.4 V [L4]. Both need 3S parts that fit the existing seats (not sourced, UNVERIFIED). The D16 software cut-offs scale to 3 cells (3.5 V per cell = 10.5 V under load).
- **Unchanged:** the Pololu 2815 switch (4.5 to 32 V), the D30V30F5 5 V regulator (5 to 45 V input) and the XT30 [L4].
- **Policy:** retrain all joints with a BAM model identified at the new bus voltage. Same steps as Option A, but for one new class on all joints.

### Option C: C044 or C046 on the 2S pack (not a heat fix)
- C044: same body, screws and mass, faster and stronger at 7.2 V (8.8 rad/s, 26.7 kg.cm), but about the same heat per newton-metre (0.77 x, stall-line values only) [D, F6]. Its "27.4 kg.cm at 1:191" is surprising next to the C001's 19.5 kg.cm at 1:345 [F2, F6]: check it on a unit. Worth it only if speed tracking (issue #48) turns out to be the real problem.
- C046 (2.4 x the heat) and Waveshare ST3215-HS (1.5 x): no.

## 3. Levers short of new servos

Sim pass only unless noted. "Ours" = the 2.77 kg build model of sim/ADDED_MASS_SIM.md, stock policy BEST_WALK_ONNX_2.

| Lever | What it buys | Source |
|---|---|---|
| Walk in bouts (duty cycle) | Knee loss 50/50 stand and walk: 2.2 W plain, 3.2 W backlash, against 3.7 W and 5.8 W walking without stops. 25 % walking: 1.4 W and 1.9 W. In steady state, the thermal resistance the knee can tolerate (60 C at a 25 C room) rises from 6.0 to 10.9 K/W (backlash, 50/50) | [L2]; standing 0.62 W backlash [D] |
| The thermal guard the lab already has | bench/walk_with_guard.py stops the walk at the Max Temperature Limit minus 15 C (55 C at the 70 C default) and cuts torque at minus 8 C (62 C). It does not restart by itself, so bouts are manual | [L9] |
| Retrain with the real mass (2.77 kg) | Knee loss at 0.15 m/s, trained mass against ours: 3.55 against 3.74 W plain, 5.58 against 5.80 W backlash. So at most 4 to 5 % heat to win back. It does restore tracking (0.67 back toward 0.73 of the command) and the side step (0.23 back toward 0.46) | [D]; [L10] |
| Retrain with a heat aim (higher torque cost than today's -1e-3, or a gentler reference gait) | No number: needs a training run. One 300 M-step run took 1 h 11 min on an RTX 3090 and 1 h 22 min on an A6000 in a third-party build; upstream's "current win" command is 300 M steps | UNVERIFIED gain; [X1], [U1] |
| Walk slower | 0.10 m/s command: right knee 3.32 W plain (-11 %), 5.12 W backlash (-12 %), but measured speed falls from 0.100 to 0.042 m/s plain (-58 %) and from 0.131 to 0.084 m/s backlash (-36 %), so heat per metre goes up. At 0.05 m/s the stock policy does not step on either mass (0.000 m/s); our knees lose 0.67 to 1.17 W, the same as standing | [D] |
| Cooling, vents in printed covers | Little. The knee servo is mostly in open air: by ray cast on the URDF meshes, 8 % of its case surface has a printed part within 10 mm and 30 % within 30 mm. The thigh cover (left_cache/right_cache) sits 10 to 30 mm off two faces. A fan or heat sink: no data; repeat the TO1 hold with one to measure it | [D] |
| Lower P if the knees buzz | Removes oscillation current. A third-party build saw a 5 Hz buzz at P 30 on the ground, fixed with P 20. It moves the servo away from the trained model | UNVERIFIED gain; [L11] |
| Lower bus voltage | Nothing for heat: copper loss is current squared times resistance, and the current is set by the torque. Lower voltage only costs speed | [D] |

## 4. Upstream and community: who has run other servos

Checked first in UPSTREAM_ISSUES.md [L11], then the GitHub search API on 2026-11-01 between about 10:15 and 10:45 PM ET [G1]. Issue and PR totals still match UPSTREAM_ISSUES.md (Mini 43 issues and 15 PRs, Runtime 20 and 25, Playground 12 and 14, reference motion generator 6 and 2), so nothing new was filed. Comment threads are blocked in this session; Discord is not readable.

- [Mini #21 "Other motor adaptation issues"](https://github.com/apirrone/Open_Duck_Mini/issues/21) (open, 2025-04-18, 2 comments): a builder ran 12 V 30 kg STS3215s with BEST_WALK_ONNX_2 at P 32: "my feet kept trembling". Voltage not stated. The maintainer's reply, as recorded in SERVO_DEEP_DIVE.md E6 (not re-read today): 12 V and 7.4 V servos differ, and the ONNX was trained for 7.4 V.
- [Mini #52 "Open duck mini stable walk"](https://github.com/apirrone/Open_Duck_Mini/issues/52) (open, 2026-08-20, no replies): 12 V 30 kg STS3215s in the knees "stopped the duck from falling over", but the right leg lacks foot clearance. Voltage not stated.
- [Mini #33 "TODO"](https://github.com/apirrone/Open_Duck_Mini/issues/33) (open, maintainer's v2.5 list): "12V motors ? -> update battery system (bms)" and "retrain walk policy for these motors". Nothing merged since.
- [Mini #48](https://github.com/apirrone/Open_Duck_Mini/issues/48) (open): C001 too slow, asks about C046 and C044. Last update 2026-11-01 18:08 UTC, which is our own question; no maintainer reply.
- [Mini #5](https://github.com/apirrone/Open_Duck_Mini/issues/5) (closed): asks whether Waveshare ST3215s work. The lab recorded a comment there recommending ST3215-HS (SERVO_DEEP_DIVE.md; not re-read).
- Playground branches new_feetech_firmware and improve_walk: the same servo, re-identified with BAM and re-tuned for a newer Feetech firmware (UPSTREAM_ISSUES.md G3). This is the same identify-then-retrain loop a servo swap needs.
- Third party, sim only: soyeon24/open-duck-mini-v2-build retrained with the force limit set to 1.86 Nm, their figure for the real STS3215 stall (19 kg.cm). Under that limit it walked 0.130 m/s, against 0.057 m/s for a policy trained at 3.23 Nm; neither fell. Their physical build is stopped [X1].
- Third party: HeyPCB/knuckle is a brushless gimbal-motor actuator that answers on the duck's bus as model 777. Its estimated stall is 0.047 Nm, 2.5 % of an STS3215, meant for the neck and head branch, not the legs [X2].
- GitHub repository search for "open duck mini 12v" and "open_duck sts3250": 0 results [G1].
- Bottom line: nobody has published an Open Duck Mini on STS3250 or STS3235. The only reports are 12 V STS3215s run with the 7.4 V-trained policy, with mixed results and no retrain.

## 5. Recommendation and decision threshold

**If the TO1 heat test fails, take Option A: STS3250 on the two knees, 2S pack and 7.2 V BEC kept.** It is the only same-case servo that cuts knee heat a lot (0.25 to 0.41 x per newton-metre) and still runs at our bus voltage. It needs no power-path change, no printed part and only 3 servos. Option B (3S, all 14 servos) is the next step only if more than the knees overheat.

TO1 (TEST_PLAN.md 7.3, D2 [L5]) holds one C001 at 1.5 A and gives its thermal resistance R_th in K/W and its time constant. Steady-state thresholds for a 25 C room and a 60 C ceiling (10 C under the 70 C cut). At another room temperature use allowed watts = (60 C - room) / R_th. If the time constant is long next to a 31-minute walk, use the sim/RUNTIME_THERMAL.md formula T = room + R_th x P x (1 - exp(-31 min / time constant)), which is less strict.

| TO1 result | Decision |
|---|---|
| R_th at or below 6.0 K/W (passes even the 5.8 W backlash knee) | Pass. Nothing changes. |
| 6.0 to 11 K/W (passes 50/50 stand and walk: 3.2 W backlash, 2.2 W plain) | Keep the C001. Walk in bouts of at most 50 % walking, with walk_with_guard.py running. Read the knee temperature in the first walking logs. No purchase. |
| 11 to 19 K/W | Option A. Order 1 STS3250 first (test order). Hold it at 1.1 A, the same torque as 1.5 A on a C001 by Feetech's Kt ratio (8 / 11). Check the M2 thread depth and the fit in a printed thigh. BAM-identify it at 7.2 V. Retrain. Then order 2 more (knees plus a spare). Expected knee loss 0.8 to 2.4 W: walking without stops passes if the STS3250's R_th is at or below 14.6 K/W (worst case); above that, 50/50 bouts (about 1.3 W) pass up to 26 K/W. |
| Above 19 K/W | Option A is not enough: the hip pitch and ankle servos (1.1 to 1.8 W [L2]) would also exceed 60 C walking without stops. Put STS3250s on all 10 leg joints on the 2S bus (11 units, $813.89 at OpenELAB [P5], +195 g), or take Option B3 if more speed is also wanted. |

Two reasons to buy one unit before the rest: the 7.2 V behaviour of the STS3250 is an estimate (the FTServo wiki lists 9 to 12.6 V [F9]), and the thermal resistance of its aluminium case is not published.

## How the sim numbers here were made (reproducible)

- Speed sweep: scratch script that imports altaay_lab/sim/added_mass_sim.py unchanged and runs its run() on the "stock" and "ours" model copies, flat and backlash scenes, forward commands 0, 0.05, 0.10 and 0.15 m/s, 22 s each, statistics after 2 s. Copper loss per joint = mean(I^2) x R from current_budget.electrical, worst of the three kt values (kt 1.148 won every case), as sim/runtime_thermal.py does. It reproduces sim/RUNTIME_THERMAL.md exactly at 0.15 m/s (ours: 3.105 and 3.737 W plain, 5.214 and 5.803 W backlash). Run 2026-11-01 about 10:35 PM ET, MuJoCo 3.17.0, about 4 s per case.

  | Model, scene | 0.00 m/s | 0.05 m/s | 0.10 m/s | 0.15 m/s |
  |---|---|---|---|---|
  | Ours, plain: measured speed (m/s); left / right knee (W) | 0.000; 1.00 / 0.65 | 0.000; 1.06 / 0.67 | 0.042; 2.62 / 3.32 | 0.100; 3.11 / 3.74 |
  | Ours, backlash | 0.000; 1.13 / 0.62 | 0.000; 1.17 / 0.69 | 0.084; 4.34 / 5.12 | 0.131; 5.21 / 5.80 |
  | Trained mass, plain | 0.000; 0.53 / 0.41 | 0.000; 0.54 / 0.42 | 0.056; 2.21 / 2.86 | 0.110; 2.85 / 3.55 |
  | Trained mass, backlash | 0.000; 0.61 / 0.39 | 0.000; 0.61 / 0.44 | 0.099; 4.32 / 5.11 | 0.141; 5.03 / 5.58 |

- Hop currents: same run() on "ours", 0.15 m/s, both scenes. Each servo's electrical power was split into copper loss (I^2 R) and the rest. A swapped servo keeps the rest and gets copper x the factor from section 1. Negative power was clipped (no regeneration), then summed down each chain and divided by the bus voltage (7.2 V or 11.1 V). This is a first-order estimate: it assumes the same joint motion, which a retrained policy would change.
- Knee enclosure: ray cast from 20,000 points on the knee servo case meshes along their normals against the other meshes of the knee_and_ankle_assembly link in robot.urdf.

## Sources

Lab files (read 2026-11-01):
- [L1] SERVO_DEEP_DIVE.md (E3 BAM to MuJoCo mapping, E6, issue #48 analysis).
- [L2] sim/RUNTIME_THERMAL.md (knee copper loss 3.1 to 5.8 W, rated 1.06 W, knee RMS current 1.19 to 1.48 A, walk times, 50/50 duty 2.2 W).
- [L3] POWER.md (CC BEC Pro 4.8 to 12.5 V, 2S to 4S input; 15 A 32 V ATO fuse; stall 14 x 2.67 A).
- [L4] BOM.md lines 1, 6, 8, 9, 10, 11 (C001 $19.00 x 14, P30B, Tenergy 32175 2S, D30V30F5 5 to 45 V, Pololu 2815 4.5 to 32 V, Adeept 2S charger).
- [L5] DECISIONS.md D2 (TO1 thermal hold at 1.5 A, updated 10:13 PM ET), D6, D15; TEST_PLAN.md section 7.3.
- [L6] verify/c7_current_ratings.py (3 A per Mini-SPOX contact).
- [L7] BOM_FULL.md F07, F13, F15 (servo screws).
- [L8] MOUNTING.md (2x18650 holder 76 x 41 x 20 mm, press fit, 0.62 mm to the lid).
- [L9] bench/walk_with_guard.py and bench/odm_bench/thermal.py (warn at limit minus 15 C, stop at minus 8 C, default limit 70 C).
- [L10] sim/ADDED_MASS_SIM.md (tracking 0.73 to 0.67, side step 0.46 to 0.23, table 4: knee at the 3.23 Nm limit 14 to 23 % of the time in the backlash model).
- [L11] UPSTREAM_ISSUES.md (G1 third-party P 20 buzz fix, G3 firmware branches, issue list).
- [L12] CABLE_MAP.md (leg chains fed at IDs 20 and 10 through SP1 and SP2, kit hops S2 to S5, contingency X1/X2 made leads).

Feetech and datasheets:
- [F1] Feetech STS(TTL) series listing: https://www.feetech.cn/en/sts_ttl_series%20servo and https://www.feetech.cn/en/products/sts_ttl_series%20servo-page-2
- [F2] ST-3215-C001 page https://www.feetech.cn/en/74v-19-kgcm-plastic-case-metal-tooth-magnetic-code-double-axis-ttl-series-steering-gear and spec sheet (edition A/0, 2020-04-10) https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772523943436695270694.pdf
- [F3] ST-3215-C018 page https://www.feetech.cn/en/525603 and spec sheet (2023-07-20) https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772519923113075854851.pdf
- [F4] STS3235 page https://www.feetech.cn/en/12v-30kg-metal-shell-metal-tooth-iron-core-motor-magnetic-coding-double-shaft-ttl-series-steering-gear and spec sheet (2021-11-19) https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772428699665192763255.pdf
- [F5] STS3250 page https://www.feetech.cn/en/562636 and spec sheet (2024-01-16; 3.8 A / 2 s over-current, 70 C cut, performance curve) https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772424007467984928587.pdf
- [F6] ST-3215-C044 Feetech spec sheet (2025-04-15), hosted by Seeed: https://files.seeedstudio.com/products/Feetech/101090141_Feetech_ST-3215-C044_Datasheet.pdf
- [F7] ST-3215-C046 Feetech spec sheet (2025-04-15), hosted by Akizuki: https://akizukidenshi.com/goodsaffix/ST-3215-C046%20SEPC.pdf
- [F8] Seeed datasheet, Feetech ST3215-C047 12 V 30 kg (4 to 14 V, 1:345, rated 10 kg.cm): https://download.kamami.pl/p1203183-17bcda86-6ebc-4dc5-b704-7e06e8de6af9.pdf
- [F9] FTServo wiki: ST model list https://ftservo.github.io/ftservo-wiki/products/datasheets/st/ ; STS3250 page (9 to 12.6 V key parameter) https://ftservo.github.io/ftservo-wiki/products/models/st-3250-c001/main/ ; drawings https://ftservo.github.io/ftservo-wiki/products/models/st-3215-c001/images/drawing.webp , .../st-3235-c001/images/drawing.webp , .../st-3250-c001/images/drawing.webp
- [F10] FTServo wiki STS memory table ("applies to the STS half-duplex TTL series"): https://ftservo.github.io/ftservo-wiki/reference/parameter/memory-sts/
- [F11] FTServo wiki model pages for ST-3020, ST-3025, ST-3035, ST-3046, ST-3095 (sizes): https://ftservo.github.io/ftservo-wiki/products/models/st-3046-c001/main/ and siblings.
- [W1] Waveshare ST3235 (SKU 27166, $41.99, 6 to 12 V, 70.5 g, 1:345): https://www.waveshare.com/st3235-servo.htm
- [W2] Waveshare ST3215-HS (SKU 25127, $21.99): https://www.waveshare.com/st3215-hs-servo-motor.htm

Suppliers (read 2026-11-01, about 10:10 to 10:45 PM ET):
- [P1] Seeed C001 (SKU 108090023): https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html
- [P2] Seeed C044 (SKU 101090141): https://www.seeedstudio.com/Feetech-ST-3215-C044-Heavy-Duty-Servo-7-4V-1-191-Gear-Reduction-p-6460.html
- [P3] Seeed C046 (SKU 101090142): https://www.seeedstudio.com/Feetech-ST-3215-C046-Standard-Torque-Servo-7-4V-1-147-Gear-Reduction-p-6461.html
- [P4] Seeed C047 (SKU 108090003): https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html
- [P5] OpenELAB Inc. STS3250-C002 ($73.99, "Location of the warehouse: China", 8 to 15 business days): https://openelab.com/products/feetech-sts3250-c002-servo-12v
- [P6] Amazon: https://www.amazon.com/dp/B0HBJLD2QG (RCmall, ships from Amazon) and https://www.amazon.com/dp/B0H6SBKSQ4 (DIYmall, model ST-3250-C001, ships from Amazon). Both show "To see product details, add this item to your cart"; price and stock not readable.
- [P7] AIFITLAB STS3250 (C001 with bracket $97, C002 without $88, backorder message): https://aifitlab.com/products/feetech-sts3250-servo-motor ; STS3235 $56: https://aifitlab.com/collections/servo-motor/products/feetech-sts3235-servo-motor
- [P8] RCDrone STS3250 ($115 to $125, all variants sold out, Shenzhen address): https://rcdrone.top/products/feetech-sts3250-servo-motor
- [P9] Amazon Waveshare ST3235: https://www.amazon.com/dp/B0D5B28BWF

Software:
- [U1] Open_Duck_Playground at b9be205: playground/open_duck_mini_v2/xmls/open_duck_mini_v2.xml (class sts3215), open_duck_mini_v2_backlash.xml (kp 17.11), joystick.py (max_motor_velocity 5.24, USE_MOTOR_SPEED_LIMITS, torques -1.0e-3), playground/common/randomize.py, README ("Current win", 300000000 timesteps).
- [U2] Open_Duck_Mini_Runtime at 376de65: mini_bdx_runtime/rustypot_position_hwi.py (IDs 10 to 14, 20 to 24, 30 to 33), scripts/v2_rl_walk_mujoco.py (P 30 legs, 8 head), scripts/configure_motor.py, setup.cfg (rustypot 0.1.0, pypot branch support-feetech-sts3215).
- [U3] rustypot 0.1.0 source, src/lib.rs (feetech_sts3215 module, no model check): https://files.pythonhosted.org/packages/80/c7/08d91421f2159f15c17d586c705de9e0ddfe62a7f3971403d878eac56b84/rustypot-0.1.0.tar.gz ; pypot conversion.py (dynamixelModels has only 777 for Feetech; unknown models use the 1024-step range): https://raw.githubusercontent.com/pollen-robotics/pypot/support-feetech-sts3215/pypot/dynamixel/conversion.py
- [B1] BAM: README (library list ends at "Feetech STS3215") https://github.com/Rhoban/bam ; bam/feetech/actuator.py (vin 7.4, kp 32, error_gain 0.166, max_pwm 0.97, 3400 steps/s) and bam/feetech/record.py, read from https://raw.githubusercontent.com/Rhoban/bam/main/

Community:
- [G1] GitHub search API (search/issues and search/repositories), 2026-11-01 between about 10:15 and 10:45 PM ET; issue bodies of Mini #5, #21, #33, #48, #52.
- [X1] soyeon24/open-duck-mini-v2-build README and HARDWARE_PREP.md (third party, sim only): https://github.com/soyeon24/open-duck-mini-v2-build
- [X2] HeyPCB/knuckle README (third party): https://github.com/HeyPCB/knuckle
