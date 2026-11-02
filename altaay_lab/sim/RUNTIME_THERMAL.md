# Walk time per charge and servo heat (sim pass only)

Written 2026-11-01 9:40 PM ET by agent M (simulation). Script: sim/runtime_thermal.py, run after sim/added_mass_sim.py (it reads that script's per-servo traces for the trained model, "stock", and our build, "ours", 2.77 kg, sim/MASS_BUDGET.md). Regenerate with
`ODM_SCRATCH=<scratch folder> python3 altaay_lab/sim/runtime_thermal.py` (tables in ODM_SCRATCH/runtime_thermal/tables.md; figure sim/runtime_thermal.png).

## Answer
- **Walk time from a full charge to the D16 stop** (3.5 V per cell under load, 7.0 V at the cells [L] DECISIONS.md D16, TEST_PLAN.md section 11), our build, typical corner [L]:
  - continuous walking forward: **31 min** (conservative corner 26 min; if the real servos draw 1.5 x the sim power, 18 min);
  - continuous walking, backlash model: 22 min (19, 12);
  - mixed stand and walk 50/50: **49 min** (40, 30); stand 75 %, walk 25 %: 66 min (53, 41).
  - The trained mass runs 2 min longer when walking continuously (33 min) and 4 to 7 min longer in the stand-heavy duty cycles: our extra 0.66 kg costs about 6 % of continuous walk time, because the pack power rises only 5 % (servo power 7 %) while the policy moves the heavier robot more slowly (sim/ADDED_MASS_SIM.md), and 8 to 10 % in the stand-heavy cycles, because holding still costs 79 % more.
- The D16 stop comes after only **1.59 to 1.87 Ah of the 2.85 to 2.92 Ah** the P30B gives down to 2.5 V [L], so 35 to 45 % of the charge is left unused. The older CURRENT_BUDGET.md line "about 40 to 60 minutes of continuous walking" is the time to an empty cell (34 to 49 min here), not to the D16 stop.
- **Copper loss** in the hottest servo, the knee, our build [L]: 3.1 to 3.7 W walking forward, 4.7 W turning, 5.2 to 5.8 W walking with the backlash model, 0.6 to 1.0 W standing. The Feetech rated point (0.65 A at 5 kg.cm) loses 1.06 W [I], so the knees run at **3 to 5.5 times their rated copper loss** while walking. Hip pitch and ankles 1.1 to 1.8 W; head servos 0.5 to 1.3 W; hip yaw and neck pitch under 0.3 W.
- **Thermal resistance: BLOCKER.** Feetech publishes no thermal resistance or thermal time constant for the STS3215 (the C001 spec gives only the operating range -20 to 60 C, a 70 C torque cut and the rated current [I]). No other source was found. So the knee temperature cannot be predicted. What can be said: in steady state a winding-to-room thermal resistance above **12 K/W (plain walk) or 7.8 K/W (backlash walk)** takes the knee to the 70 C cut from a 25 C room, and above 9.4 or 6.0 K/W if the air inside the body is 35 C [L]. Whether a 22 to 31 minute walk reaches steady state depends on the unknown time constant.
- **D2 thermal test**: as written it holds "1.5 Nm", which is ambiguous here: with the BAM torque constant that is 1.2 to 1.3 A (4 to 4.5 W), with the Feetech data-sheet constant (7.8 kg.cm/A = 0.765 Nm/A, spec item 5-11 [I]) it is 2.0 A, at the servo's own 2 A / 2 s over-current cut and at 78 % of the 1.91 Nm stall torque, next to the 80 % / 2 s overload cut [L], so the servo may switch itself off in 2 s and the test fails for the wrong reason. Proposed instead: hold by current at the knee's walking RMS (1.5 A), long enough to see the curve settle, and compute the thermal resistance and time constant from it (exact text below).

## Method
### Pack power per case
- Servo electrical power: the BAM motor model of sim/current_budget.py on every servo trace (applied voltage u = F R / kt, current I = (u - kt w) / R, power u I, sum of positive servo powers only, no credit for braking), statistics after the first 2 s [L]. kt 1.21164 in the typical corner (BAM m1.json, kt 1.2116, R 2.676 ohm [I] https://raw.githubusercontent.com/Rhoban/bam/b1769a6707e18e77fd656ea76a63588e0195bcc3/params/feetech_sts3215_7_4V/m1.json), 1.148 in the conservative corner (highest current of the three current_budget.py values [L]).
- Servo electronics: 14 x 21 mA at 7.2 V [I] (Feetech STS3215 C001 product specification 2023-06-23, item 5-6 "Idle Current (at stopped) 21 mA", copy https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf).
- BEC and 5 V regulator efficiency 0.85: ASSUMPTION, as sim/power_path_sim.py (Castle publishes no efficiency) [L].
- 5 V branch: 3 W typical, 5 W conservative [L] (CABLE_MAP.md P13 "typical 3 W, peak 12 W"; power_path_sim.py P_5V = 5 W).
- Pack path from the cells to the switched bus: holder 10 or 30 mOhm, BMS 25 mOhm, fuse 6 mOhm, XT30 2 x 1 mOhm, Pololu 2815 13 mOhm and 0.67 m of 16 AWG (8.8 mOhm): 64 mOhm typical, 84 mOhm high side [L] (sim/POWER_PATH_SIM.md table and power_path_sim.py lengths).
- Third corner: the conservative corner with the servo power x 1.5, because CURRENT_BUDGET.md says real servos may draw up to 2 x the sim until a bench log exists [L].

### Discharge
- 2 Molicel P30B in series, constant power from full charge, pack current solved so that (2 x cell voltage - I x path resistance) x I equals the load. Cell voltage under load from the data-sheet "Discharge Rate Characteristics" curves at 0.6, 1.5, 3, 10 and 20 A, interpolated in current and capacity [I] (digitized tables at https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery, figures 3.1 and 3.2 there, from the Molicel data sheet https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf; 23 C; capacity to 2.5 V 2846 mAh at 3 A and 2854 mAh at 10 A).
- Mixed duty cycles use the time-weighted mean power. The pack sees the mean current; walking peaks of 8 to 11 A (sim/POWER_PATH_SIM.md) dip the cells a further 0.1 to 0.15 V each for tens of ms (17 mOhm DC impedance [I] data sheet), which a filtered stop reading should ignore.
- Stops: D16 at 3.5 V per cell at the cells under load; also 7.0 V on the switched bus (the path drop is 0.2 to 0.45 V more), 3.3 V per cell, and empty (2.55 V per cell).

### Copper loss
- Per joint: RMS motor current over the case squared times the winding resistance, for each BAM kt (R = kt / 0.43649, 2.63 to 2.93 ohm [L] current_budget.py), largest of the three; in brackets the Feetech data-sheet terminal resistance 2.5 ohm [I] (spec item 5-10). Rated copper loss for comparison: 0.65 A rated current (item 5-9, at the 5 kg.cm rated torque, item 5-8) squared times 2.5 ohm = 1.06 W [I].
- Not included: iron loss, gear friction heat, driver board loss. They add heat, so the copper loss is a lower bound of the servo's heat.

## Results: walk time (sim pass only)
Our build ("ours"); the stock model in the last column for comparison. Minutes from a full charge.

| Duty cycle | Corner | Servo electrical W | Pack bus W | Mean pack A | to D16 stop | Ah to D16 stop | to 7.0 V bus | to 3.3 V/cell | to empty | stock, to D16 stop |
|---|---|---|---|---|---|---|---|---|---|---|
| Continuous walk forward 0.15 m/s | typical | 16.2 | 25.0 | 3.38 | **31** | 1.77 | 26 | 38 | 47 | 33 |
| | conservative | 17.5 | 29.0 | 3.98 | 26 | 1.74 | 19 | 32 | 40 | 28 |
| | 1.5 x servo power | 17.5 | 39.3 | 5.50 | 18 | 1.68 | 11 | 23 | 28 | 19 |
| Continuous walk forward, backlash model | typical | 23.4 | 33.6 | 4.59 | 22 | 1.72 | 17 | 28 | 34 | 24 |
| | conservative | 25.3 | 38.2 | 5.34 | 19 | 1.69 | 12 | 24 | 29 | 20 |
| | 1.5 x servo power | 25.3 | 53.1 | 7.67 | 12 | 1.59 | 5 | 16 | 20 | 13 |
| Continuous mixed walking (1/2 forward, 1/4 turn, 1/4 side) | typical | 16.2 | 25.1 | 3.38 | 31 | 1.77 | 26 | 38 | 47 | 33 |
| | conservative | 17.5 | 29.0 | 3.98 | 26 | 1.74 | 19 | 32 | 40 | 27 |
| Stand and walk 50/50 | typical | 9.3 | 16.9 | 2.25 | **49** | 1.83 | 43 | 58 | 70 | 53 |
| | conservative | 10.0 | 20.1 | 2.71 | 40 | 1.80 | 33 | 48 | 58 | 43 |
| | 1.5 x servo power | 10.0 | 26.0 | 3.55 | 30 | 1.76 | 23 | 36 | 44 | 32 |
| Stand 75 %, walk 25 % | typical | 5.8 | 12.8 | 1.70 | 66 | 1.87 | 61 | 78 | 94 | 73 |
| | conservative | 6.2 | 15.7 | 2.10 | 53 | 1.84 | 46 | 63 | 76 | 58 |

The walking-only cases are flat ground. Rough terrain is left out: the stock policy falls there within 10 s in most runs (sim/ADDED_MASS_SIM.md), so it gives no steady walking power.

## Results: copper loss per joint, our build (W; data-sheet R in brackets)
| Joint | stand | forward | turn | side | backlash forward | RMS current, backlash forward (A) |
|---|---|---|---|---|---|---|
| left_hip_yaw | 0.00 (0.00) | 0.09 (0.08) | 0.61 (0.58) | 0.08 (0.08) | 0.14 (0.14) | 0.23 |
| left_hip_roll | 0.34 (0.32) | 0.26 (0.25) | 0.72 (0.68) | 1.65 (1.57) | 0.71 (0.68) | 0.52 |
| left_hip_pitch | 0.01 (0.01) | 1.12 (1.06) | 1.00 (0.95) | 0.80 (0.76) | 1.62 (1.54) | 0.78 |
| left_knee | 1.00 (0.95) | 3.11 (2.96) | 3.04 (2.89) | 2.49 (2.37) | 5.23 (4.97) | 1.41 |
| left_ankle | 0.00 (0.00) | 1.56 (1.49) | 1.98 (1.88) | 0.81 (0.77) | 1.66 (1.58) | 0.79 |
| right_hip_yaw | 0.00 (0.00) | 0.10 (0.09) | 0.39 (0.37) | 0.11 (0.11) | 0.25 (0.24) | 0.31 |
| right_hip_roll | 0.39 (0.37) | 0.39 (0.37) | 0.49 (0.47) | 1.78 (1.69) | 0.60 (0.57) | 0.48 |
| right_hip_pitch | 0.02 (0.02) | 0.82 (0.78) | 0.84 (0.80) | 1.28 (1.22) | 1.11 (1.05) | 0.65 |
| right_knee | 0.65 (0.61) | 3.73 (3.55) | 4.66 (4.43) | 3.48 (3.30) | **5.79 (5.51)** | **1.48** |
| right_ankle | 0.04 (0.04) | 1.47 (1.40) | 1.12 (1.07) | 0.97 (0.93) | 1.76 (1.68) | 0.82 |
| neck_pitch | 0.00 (0.00) | 0.13 (0.12) | 0.06 (0.05) | 0.04 (0.04) | 0.27 (0.26) | 0.32 |
| head_pitch | 0.02 (0.02) | 0.93 (0.89) | 0.16 (0.15) | 0.23 (0.22) | 1.27 (1.21) | 0.69 |
| head_yaw | 0.00 (0.00) | 0.71 (0.68) | 1.08 (1.03) | 0.18 (0.17) | 1.16 (1.10) | 0.66 |
| head_roll | 0.00 (0.00) | 0.54 (0.52) | 0.21 (0.20) | 0.18 (0.17) | 0.73 (0.69) | 0.53 |

- Stock model for comparison [L]: right knee 3.56 W forward, 5.59 W backlash forward; our build is 2 to 5 % higher while walking and 1.6 to 1.9 x higher standing (knee RMS 0.62 A standing against 0.45 A), because standing torque scales with weight while the walking motion is limited by servo speed and torque.
- Knee RMS current walking forward: 1.19 A (ours), 1.16 A (stock); turning 1.33 A; backlash model 1.48 A [L].
- Mixed duty: the knee loss scales with the walking share, for example 2.2 W for stand and walk 50/50 (0.5 x 3.73 + 0.5 x 0.65).
- No case keeps any servo above 2 A for 2 s (the C001 over-current cut) or above 80 % output for 2 s (the overload cut) [L] (sim/ADDED_MASS_SIM.md, protection table).

## What it means for the D2 thermal test
1. The knees are the servos to test; at 3 to 5.5 x the rated copper loss they are the only joints whose temperature is in doubt. The hip pitch and ankle servos run near the rated loss.
2. Hold by current, not by torque, so the test does not depend on which torque constant is right and stays below the servo's 2 A self-protection. 1.5 A is the knee's walking RMS in the backlash model, rounded up; it is 1.2 A on the plain model.
3. Run until the curve settles. The walk to the D16 stop lasts 22 to 31 minutes, longer than the 10 minutes in D2 now.
4. From the log: thermal resistance R_th = (T_end - T_room) / (I^2 x 2.5 ohm), time constant = time to 63 % of the rise. Predicted knee temperature after a full charge of continuous walking: T_room + R_th x P x (1 - exp(-t / time constant)) with P = 3.7 W (plain) and 5.8 W (backlash) from the table above and t = 31 min. Note that Present Temperature is the servo's own sensor; whether it reads the winding or the board is not published, so the winding is hotter by an unknown amount.
5. If the prediction does not pass: limit continuous walking in software from Present Temperature (rest when the knees reach a set limit), or plan the walk as a stand and walk mix (the knee loss halves at 50/50).

## Proposed text for files owned by others
- TEST_PLAN.md section 7, replace item 3 with: "3. Thermal (D2): fix the servo horn against a rigid stop and command a position past it so that Present Current reads 1.5 A (the knee walking RMS current in the backlash model, sim/RUNTIME_THERMAL.md) at 7.2 V. Log Present Temperature, Present Current and Present Voltage every 10 s for 30 minutes, or until the temperature rises less than 0.5 C per minute; write down the room temperature and read the Max Temperature Limit register once. Compute the thermal resistance and time constant as in sim/RUNTIME_THERMAL.md. Pass: the predicted knee temperature after 31 minutes of continuous walking (3.7 W plain model and 5.8 W backlash model) is at least 10 C below both the Max Temperature Limit register and the 70 C over-temperature cut of the C001 spec. If the servo cuts its torque during the hold, write down when and at what temperature."
- DECISIONS.md D2, replace "(servo held at 1.5 Nm for 10 minutes at 7.2 V, read the Present Temperature register every 10 s and the servo's own Max Temperature Limit register once; pass if it stays at least 10 C below that limit)" with "(servo held at a Present Current of 1.5 A at 7.2 V for 30 minutes or until its temperature settles, Present Temperature every 10 s, Max Temperature Limit register once; pass if the predicted knee temperature after a full charge of continuous walking stays at least 10 C below both that limit and the 70 C cut, TEST_PLAN.md section 7, sim/RUNTIME_THERMAL.md)". Reason: 1.5 Nm is 1.2 to 2.0 A depending on the torque constant, and the knees run at 3 to 5.5 x the rated copper loss.
- CURRENT_BUDGET.md "Battery" bullet, replace "so about 40 to 60 minutes of continuous walking. Sim pass only, not measured." with "so about 40 to 60 minutes of continuous walking to an empty cell; to the D16 stop (3.5 V per cell under load) it is about 24 to 33 minutes at the trained model's mass and 22 to 31 minutes for our 2.77 kg build (backlash to plain model, typical corner, sim/RUNTIME_THERMAL.md). Sim pass only, not measured."

## Limits
- Sim pass only. The servo power comes from the BAM model of the servo; real servos may draw more (gear friction, issue 48). The 1.5 x corner brackets that only partly.
- The regulator efficiencies are assumptions; Castle publishes none. In dropout (pack under about 7.5 V) the BEC passes its input through, where its loss is probably lower than 15 % (not verified), so the corners are likely a little pessimistic there.
- The P30B curves are for new cells at 23 C; after 300 cycles at 1C the data sheet shows 93 % capacity [I] (same page, figure 6.1), so walk time drops by about the same share.
- Copper loss leaves out iron, friction and electronics heat; the thermal answer stays a BLOCKER until the TO1 bench run.
