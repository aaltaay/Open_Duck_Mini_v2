# Servos

The bill is already a mixed fleet: 12 STS3215 C001 and two STS3250 knees (D32). This note asks whether a cheaper catalog servo can take a low-load joint, and whether the knee pick still holds after a heat rerun. Prices are COSTS.csv. No 100-quantity or 1000-quantity servo price was printed on any page opened tonight. Those rows are BLOCKER.

## Loads (sim pass only)

sim/ADDED_MASS_SIM.md table 4, backlash model, our build. RMS / peak, Nm.

| Joint | RMS | Peak |
|---|---|---|
| Hip yaw | 0.38 to 0.47 | 1.17 |
| Hip roll | 0.67 to 0.80 | 2.02 |
| Hip pitch | 1.10 to 1.29 | 3.23 |
| Knee | 2.07 to 2.19 | 3.23 |
| Ankle | 1.18 to 1.20 | 3.23 |
| Neck pitch | 0.40 | 0.73 |
| Head pitch | 1.03 | 2.19 |
| Head yaw | 1.05 | 3.21 |
| Head roll | 0.81 | 1.75 |

The policy speed cap is 5.24 rad/s (cited, the training joystick). The session CSV used for heat has no per-joint speed column, so the speed at the same moment as the peak is BLOCKER. The two limits are checked separately.

## What each catalog servo can do on the 7.2 V bus

Linear voltage scale, calc only, from the cited stall and no-load. kgf to N is 0.0980665.

| Servo | Stall at its rated voltage | At 7.2 V | Versus the loads | Case and bus |
|---|---|---|---|---|
| STS3215 C001 | 1.91 Nm at 7.4 V, no-load 5.45 rad/s (sheet, already in SERVO_UPGRADE_OPTIONS.md) | Stall 1.86 Nm, no-load 5.30 rad/s. Torque left at the 5.24 rad/s cap is 0.02 Nm | Peak of hip roll, hip pitch, knee, ankle, head pitch, and head yaw is over 1.86 Nm. Hip yaw, neck, and head roll peaks fit under it. Knee RMS 2.19 Nm does not | Same case as today. STS bus |
| STS3250 | 4.90 Nm and 7.87 rad/s at 12 V (sheet; knee twin rounds 50 kg.cm to 4.90 Nm) | Stall 2.94 Nm, no-load 4.72 rad/s. At 2.19 Nm the speed left on that line is 1.21 rad/s | RMS knee torque fits. The 3.23 Nm peak is still over 2.94 Nm, so the sheet line still saturates on peaks. The knee twin's own cap was 4.97 Nm at 7.2 V (sim pass only) and is higher than this sheet line | Same 45.2 mm case. STS bus. 7.2 V is inside the 6 to 12 V sheet and outside the wiki's 9 to 12.6 V line. That conflict is already in SERVO_UPGRADE_OPTIONS.md |
| Waveshare ST3215 7.4 V | Page table: 19.5 kg.cm, 2.5 A, 0.192 s/60 deg, Kt 7.8 kg.cm/A, 4 to 7.4 V | Same class as the C001 | Same load result as the C001 | Same family. Backlash and life were not on the page: BLOCKER |
| C044, C046, C047, ST3235 | Earlier read, 2026-11-01, not re-opened tonight | C046 is weaker. C047 and ST3235 are about 2.8 rad/s no-load at 7.2 V in that study | Not a heat fix and not cheaper than the C001 on that read | Same case for the ST-3215 codes. ST3235 is the aluminium 12 V servo |
| XL330-M288-T | 0.52 Nm stall, 103 rpm no-load, at 5 V (Robotis page) | Not scaled above 5 V | 0.52 Nm is under every peak in the table, including the neck at 0.73 Nm | 20 x 34 x 26 mm, 18 g. Dynamixel protocol, not the STS bus. Price is above the C001 |
| XL430-W250-T | 1.4 Nm stall at 11.1 V, 57 rpm, 65 g, 28.5 x 46.5 x 34 mm (Robotis page) | Linear scale 0.91 Nm | 0.91 Nm is under the hip yaw peak of 1.17 Nm. Only the neck peak fits, and the C001 already covers the neck for less money | Different case. Different protocol |
| HTD-45H | 45 kg.cm (4.41 Nm) and 0.18 s/60 deg at 11.1 V, 64 g, 51.1 x 20.14 x 40 mm (Hiwonder page) | Rated 9 to 12.6 V. No 7.2 V number. Scaling into an unrated voltage is not done | Could cover 3.23 Nm at 11.1 V. That needs a higher pack. The battery study already closed a bigger pack | New prints, Hiwonder UART, not a drop-in |
| Quasi-direct-drive or a custom BLDC | No catalog part in the 45 mm case was opened | BLOCKER | A new motor is not designed here. The catalog part that fits the case and raises stall is the STS3250 | |

Life and backlash, from work already opened, not re-measured:

- C001 life test on the sheet is about one fifth of stall, about 3.9 kg.cm (KNEE_HEAT_STUDY.md, cited sheet). The sim knee RMS is 2.19 Nm, above the sheet stall, so that life test is not this walk.
- STS3250 sheet backlash is 0.5 deg or less. A published check measured 0.43 deg (KNEE_TWIN.md). One published full-load test burnt a motor (same file, and KNEE_HEAT_STUDY.md).
- XL330 feedback is position, velocity, current, temperature, 4096 steps (Robotis page). Backlash was not on the page: BLOCKER.
- Waveshare 7.4 V feedback is position, load, speed, and voltage, 4096 steps (page table). Backlash BLOCKER.

## Heat rerun (the existing model)

knee_heat_rerun.py calls twin/thermal/gate_p45b.py run_walk and twin/thermal/twin_thermal.py simulate. It does not change those files.

The reproduction of the P45B backlash log, central corner, torque-off left off so the clock can be read, matches the published run:

| Room | Minutes to a 60 C reading | Minutes to 70 C | Body max |
|---|---|---|---|
| 25 C | 3.33 | 4.5 | 94.67 C |
| 32 C | 2.5 | 3.5 | 101.63 C |

That body temperature is the cut-off-disabled run, the same warning as PR 34 and KNEE_HEAT_STUDY.md. It is not a measured knee. With the 70 C cut left on, a C001 held at the sheet stall (2.5 A, 2.5 ohm, 15.6 W, calc only, not a walk) reaches a 60 C reading in 0.83 minutes and the cut stops the reading at 68.7 C. The rated 0.65 A point settles at 39.7 C (calc only), next to the "near 40 C" line already in the knee heat study.

STS3250 copper at the sim knee RMS of 2.19 Nm, only because 2.19 is under the 2.94 Nm scaled stall. Speed term left out (calc only). The two sheet resistances still disagree (1.2 ohm published, 12 V / 4.2 A = 2.86 ohm).

| Resistance used | Current | Copper | 25 C room, cut on | 32 C room, cut on |
|---|---|---|---|---|
| 1.2 ohm, published Kt | 2.03 A | 4.95 W | 60 C at 3.83 min, reading stops at 69.5 C | 60 C at 2.83 min, reading stops at 69.9 C |
| Stall-line R and Kt | 1.88 A | 10.05 W | 60 C at 1.33 min, reading stops at 69.4 C | 60 C at 1.17 min, reading stops at 68.7 C |

So a knee that actually holds 2.19 Nm still leaves the 60 C operating line in a few minutes, and the guard then cuts torque. The cooler knee-twin currents (0.71 to 0.88 A, sim pass only) are the stock policy, which walks badly. At those currents and 32 C, the same model stays under 60 C except the high current with the stall-line resistance, which reaches 60 C at 13.8 minutes and peaks at 62.6 C (calc only). That is not the heat of a walk that makes the sim torque.

The aluminium case has no published thermal resistance. This rerun keeps the C001 thermal mass. It does not invent a cooler case.

## Mixed fleet

A cheaper servo on a light joint has to cost less than the C001, speak the STS bus, fit the printed horn, and clear that joint's peak.

- XL330 costs more and misses every peak, including the neck.
- XL430 at 7.2 V misses the hip yaw peak. It also misses the case and the protocol. The one joint it might cover, the neck, is already on a cheaper C001.
- C046 was not cheaper on the 2026-11-01 read, and it is weaker.
- HTD-45H is not rated at 7.2 V.

No catalog servo opened here is both cheaper and strong enough for a light joint, except the Waveshare 7.4 V unit, which is the same torque class as the C001, not a weaker class. That is a supplier swap for the 12 body servos (row save_waveshare_12), and only after one unit is checked for backlash. The knees stay STS3250. Dropping those two knees is a larger dollar cut (row save_drop_sts3250_knees) and it puts the knee back on a servo whose stall is under the sim RMS. That cut is listed so the size is visible. It is not the pick.

The live STS3250 pair costs more than the figure on the bill (row knee_pair_live_vs_bill). That is a rise, not a cut.
