# Run C joint current

Written 2026-11-13. CPU only. The walk is the em_twin sheet walk with the run C policy and the 12 V ST-3215-C018 patch in `problems/sts12.py`. The rail is the PR 85 winner: 3S Molicel P45B wired to the servos, Castle off the trunk. The thermal cases call `knee_heat_chafe.py` from the open knee-heat branch. This note does not copy those scripts. D61 was not edited. Nothing was bought. The policy was not retrained.

Every walk figure is sim pass only. A temperature from the thermal twin is sim pass only. Arithmetic on those currents, and the blanking comparison, are calc only. A datasheet figure is cited. A missing measurement is BLOCKER.

Script: `altaay_lab/problems/runc_joint_current.py`. Numbers: `altaay_lab/problems/runc_joint_current.json`.

## What was logged

Run C had pack current and knee volts. It did not keep a per-servo current. The knee-heat note therefore scaled an older backlash session by Kt, and it marked a run C knee amp BLOCKER. This pass keeps the motor current and the supply current that `em_twin.py` already computes on each 2 ms step.

Commands are 0.15, 0.25, and 0.40 m/s, typical and high-side corners, 60 s, no fall in the runs below. The longer duty is the same command held for 10 min. Stats start at 4 s, the same window as the pack figures in the electromechanical twin. The logged amps are the post-step sheet law (`servo_sts3215.electrical`), which is the series the twin already reports as motor RMS and supply current.

Baseline trunk before the third cell, from the mass budget after the same JPI seat PR 85 uses: 1.0654 kg (sim pass only). That matches the 1.0654 kg figure PR 85 records.

## Per-joint current

Motor current is the sheet winding current. Supply current is what the limb wire carries, idle included. The hottest joint is the one with the highest motor RMS, because copper heat follows that square.

| Command | Corner | Length | Hottest joint | Motor RMS A | Motor peak A | Pack mean A | Pack peak A | Speed m/s |
|---|---|---|---|---|---|---|---|---|
| 0.15 | high-side | 60 s | right_knee | 1.513 | 2.480 | 4.422 | 7.655 | 0.1152 |
| 0.15 | high-side | 600 s | right_knee | 1.495 | 2.480 | 4.352 | 7.655 | 0.1084 |
| 0.15 | typical | 60 s | right_knee | 1.539 | 2.533 | 4.460 | 7.560 | 0.1196 |
| 0.15 | typical | 600 s | right_knee | 1.514 | 2.533 | 4.390 | 8.200 | 0.1133 |
| 0.25 | high-side | 60 s | right_knee | 1.671 | 2.629 | 6.494 | 11.277 | 0.1762 |
| 0.25 | typical | 60 s | right_knee | 1.705 | 2.697 | 6.532 | 11.198 | 0.1830 |
| 0.40 | high-side | 60 s | left_knee | 1.686 | 2.557 | 8.133 | 13.913 | 0.2528 |
| 0.40 | typical | 60 s | left_knee | 1.722 | 2.635 | 8.239 | 14.565 | 0.2598 |
| 0.40 | typical | 600 s | left_knee | 1.689 | 2.635 | 8.154 | 14.565 | 0.2563 |

All of those rows are sim pass only. The 0.15 m/s typical pack peak is the check against PR 85, which printed 8.114 A and 0.1183 m/s. This run is 7.560 A and 0.1196 m/s (sim pass only).

Normal walk, 0.15 m/s, both corners, 60 s. Amps are sim pass only.

| Joint | Typ motor RMS | Typ motor peak | Typ supply RMS | Typ supply peak | High motor RMS | High motor peak | High supply peak |
|---|---|---|---|---|---|---|---|
| left_hip_yaw | 0.460 | 1.230 | 0.169 | 0.694 | 0.455 | 1.225 | 0.680 |
| left_hip_roll | 0.643 | 1.774 | 0.318 | 1.350 | 0.630 | 1.689 | 1.279 |
| left_hip_pitch | 0.832 | 2.198 | 0.497 | 1.995 | 0.824 | 2.172 | 2.027 |
| left_knee | 1.471 | 2.521 | 1.218 | 2.540 | 1.442 | 2.469 | 2.490 |
| left_ankle | 0.700 | 1.429 | 0.299 | 0.950 | 0.699 | 1.413 | 0.911 |
| neck_pitch | 0.347 | 0.745 | 0.084 | 0.231 | 0.344 | 0.781 | 0.261 |
| head_pitch | 0.448 | 0.934 | 0.129 | 0.359 | 0.449 | 0.925 | 0.351 |
| head_yaw | 0.493 | 1.513 | 0.177 | 0.931 | 0.504 | 1.376 | 0.783 |
| head_roll | 0.417 | 1.224 | 0.155 | 0.673 | 0.413 | 1.205 | 0.678 |
| right_hip_yaw | 0.523 | 1.240 | 0.186 | 0.614 | 0.515 | 1.220 | 0.616 |
| right_hip_roll | 0.564 | 1.577 | 0.232 | 1.149 | 0.547 | 1.531 | 1.091 |
| right_hip_pitch | 0.716 | 1.940 | 0.411 | 1.637 | 0.711 | 1.893 | 1.613 |
| right_knee | 1.539 | 2.533 | 1.323 | 2.554 | 1.513 | 2.480 | 2.501 |
| right_ankle | 0.588 | 1.437 | 0.248 | 0.882 | 0.585 | 1.414 | 0.863 |

Hottest joint on the 0.15 m/s typical walk: right_knee, motor RMS 1.539 A, motor peak 2.533 A (sim pass only). At 0.40 m/s typical the hottest joint is the left knee.

Longer duty, the command held for 10 min. 0.15 m/s high-side, 10 min: hottest joint right_knee, motor RMS 1.495 A over the whole window, 1.511 A in the first minute, 1.489 A in the last minute, pack mean 4.415 A then 4.340 A (sim pass only). 0.15 m/s typical, 10 min: hottest joint right_knee, motor RMS 1.514 A over the whole window, 1.537 A in the first minute, 1.502 A in the last minute, pack mean 4.459 A then 4.347 A (sim pass only). 0.40 m/s typical, 10 min: hottest joint left_knee, motor RMS 1.689 A over the whole window, 1.721 A in the first minute, 1.661 A in the last minute, pack mean 8.240 A then 8.068 A (sim pass only).

## Knee heat on these currents

The thermal twin is the PR 86 model: `twin_thermal.simulate`, the C018 stall-line split that file uses (winding 3.753 ohm, an assumption, the page does not print a winding resistance), the C001 21 mA idle, friction omitted, central corner, torque cut 70 C unless a row says the cut is off. `build_12v` multiplies by Kt 7.4 V over Kt 12 V because its input was a 7.4 V log. These amps are already the 12 V sheet, so the script divides by that factor first. The product is the logged current. A check on the first bin refuses a run that does not land on the log.

The winner has no Castle, so the 0.30 V drop in that file is set to 0 for these rows. One comparison row puts the 0.30 V drop back. The knee is outside the trunk. PR 86 already found that trunk vents do not move the knee.

PLA and PETG do not change the sim temperature. They change the limit the case is compared with. PLA low edge 49 C is cited (SD3D, ASTM D648, the thermal note). PETG 62 C at 1.8 MPa is cited (Bambu PETG HF, the knee-heat note). The C018 page opened for this lab does not print an operating temperature. Using the C001 60 C line and the 70 C torque-off on the C018 is BLOCKER, the same open item as PR 86.

| Series | Case | Room | Reading max | Case max | Time to reading 55 C | Time to reading 60 C | Time to case 49 C | Time to case 62 C | Case at 90 min | Walk share | Rise last 10 min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.15 m/s typical, 10 min | cont70_25 | 25 C | 70.18 C | 61.41 C | 1.22 min | 1.43 min | 1.45 min | does not cross in the run | 27.68 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 10 min | cont70_32 | 32 C | 70.14 C | 62.14 C | 0.88 min | 1.10 min | 1.10 min | 1.95 min | 34.62 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 10 min | cont200_25 | 25 C | 200.09 C | 178.44 C | 1.22 min | 1.43 min | 1.45 min | 2.05 min | 27.68 C | 1.000 | -0.004 C |
| 0.15 m/s typical, 10 min | guard_25 | 25 C | 55.36 C | 50.44 C | 1.22 min | does not cross in the run | 1.88 min | does not cross in the run | 48.94 C | 0.142 | 0.198 C |
| 0.15 m/s typical, 10 min | guard_32 | 32 C | 55.40 C | 51.20 C | 0.88 min | does not cross in the run | 1.28 min | does not cross in the run | 49.87 C | 0.090 | 1.594 C |
| 0.15 m/s typical, 10 min | cont70_25_drop0p3 | 25 C | 70.18 C | 61.41 C | 1.22 min | 1.43 min | 1.45 min | does not cross in the run | 27.68 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont70_25 | 25 C | 70.10 C | 61.26 C | 1.27 min | 1.45 min | 1.48 min | does not cross in the run | 27.66 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont70_32 | 32 C | 70.31 C | 62.26 C | 0.95 min | 1.15 min | 1.13 min | 1.95 min | 34.60 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont200_25 | 25 C | 197.54 C | 176.76 C | 1.27 min | 1.45 min | 1.48 min | 2.13 min | 175.64 C | 1.000 | 0.035 C |
| 0.15 m/s high-side, 10 min | guard_25 | 25 C | 55.31 C | 50.52 C | 1.27 min | does not cross in the run | 1.82 min | does not cross in the run | 50.40 C | 0.149 | 0.250 C |
| 0.15 m/s high-side, 10 min | guard_32 | 32 C | 55.39 C | 51.27 C | 0.95 min | does not cross in the run | 1.27 min | does not cross in the run | 47.65 C | 0.093 | 0.385 C |
| 0.15 m/s typical, 60 s | cont70_25 | 25 C | 70.14 C | 61.61 C | 1.25 min | 1.45 min | 1.47 min | does not cross in the run | 27.72 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 60 s | cont70_32 | 32 C | 70.10 C | 62.17 C | 0.88 min | 1.13 min | 1.12 min | 1.95 min | 34.66 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 60 s | cont200_25 | 25 C | 200.06 C | 178.19 C | 1.25 min | 1.45 min | 1.47 min | 2.08 min | 27.73 C | 1.000 | -0.002 C |
| 0.15 m/s typical, 60 s | guard_25 | 25 C | 55.52 C | 50.50 C | 1.25 min | does not cross in the run | 1.73 min | does not cross in the run | 50.13 C | 0.141 | 0.536 C |
| 0.15 m/s typical, 60 s | guard_32 | 32 C | 55.46 C | 51.29 C | 0.88 min | does not cross in the run | 1.28 min | does not cross in the run | 46.31 C | 0.086 | -3.900 C |
| 0.25 m/s typical, 60 s | cont70_25 | 25 C | 70.22 C | 60.10 C | 0.97 min | 1.12 min | 1.20 min | does not cross in the run | 27.66 C | 1.000 | -0.000 C |
| 0.40 m/s high-side, 60 s | cont70_25 | 25 C | 70.07 C | 60.62 C | 1.03 min | 1.23 min | 1.28 min | does not cross in the run | 27.58 C | 1.000 | -0.000 C |
| 0.40 m/s typical, 10 min | cont70_25 | 25 C | 70.04 C | 60.29 C | 0.97 min | 1.10 min | 1.22 min | does not cross in the run | 27.54 C | 1.000 | -0.000 C |

Temperatures and the walk share are sim pass only. The blank comparison with PR 86 is the guard row: that note reported a walk share of 0.388 at 25 C and 0.201 at 32 C on the Kt-scaled old log (sim pass only). The shares in the table are the same guard, 55 C stop and 45 C resume, torque off while sitting, on the run C current.

A case near 28 C at 90 min, on a row whose reading hit 70 C or 200 C, is the cool-down after that cut unloads the servo. The case max is the peak before the cool-down. On a guard row the 70 C cut does not fire, so the 90 min case is one sample of the walk-and-rest cycle and the case max is the peak of that cycle.

Without the rest rule, cut still at 70 C, 25 C room: the right-knee reading reaches 55 C at 1.22 min and 60 C at 1.43 min. The case reaches 49 C at 1.45 min and peaks at 61.41 C. The case does not reach 62 C in that 25 C run. After the cut unloads the knee the case cools, and at 90 min it is 27.68 C (sim pass only). The 32 C room with the same cut peaks the case at 62.14 C. It reaches 62 C at 1.95 min. Sim pass only. With the torque cut raised to 200 C on the typical corner, the reading reaches 200.09 C and the case peaks at 178.44 C (sim pass only). That stand-in cut then unloads the servo. The high-side corner with the same 200 C stand-in ends at a 175.64 C case, last-10-min rise 0.035 C, reading max 197.54 C (sim pass only). That is the balance this model reaches when the sheet cut is not allowed to hide it. The 55/45 guard, on the 10 min current, walks 14.2 percent of the 90 min at 25 C and 9.0 percent at 32 C (sim pass only). PR 86 reported 38.8 percent and 20.1 percent on the Kt-scaled old log. Guard case peak is 50.44 C at 25 C and 51.20 C at 32 C (sim pass only). The 90 min samples are 48.94 C and 49.87 C, and the last 10 min move those samples by 0.198 C and 1.594 C. The 32 C guard is still climbing at 90 min. Both peaks are above the cited 49 C PLA edge and under the cited 62 C PETG point. Putting the 0.30 V Castle drop back leaves the case peak at 61.41 C against 61.41 C on the wire (sim pass only). The knee number does not move with that trunk drop.

Right-knee motor RMS on the 0.15 m/s typical 60 s walk is 1.539 A (sim pass only). The knee-heat note's 12 V shape was a 1.447 A log times the Kt scale 0.702, which is 1.02 A (calc only). This knee draws more than that shape, which is why the clock is shorter and the walk share is lower.

## The 36 g Castle check

PR 85 removed the Castle from the wire-rail body (35.97 g: 29.0 g cited body, 4.6 g leads, tape, and the two output splices) and printed the same speed and the same current to four digits as the wire walk that still carried that mass. The trunk field in that JSON did change, from 1.1354 kg to 1.0994 kg.

The cause is in `system_voltage._patch_trunk`. It parses the MJCF, edits the trunk inertial on the in-memory tree, and returns the new mass. It never writes the tree back to the file (`pr85_patch_writes_file` is False). MuJoCo loads the scene with `from_xml_string` and the asset dictionary, so it kept the unpatched trunk, 1.0654 kg, for both rows. The identical digits are the same model walked twice. This pass writes the inertial, checks that the loaded body mass matches the file, and walks again. The electrical extra stays the wire rail for both bodies. A third body adds 200 g at the original trunk COM and walks 20 s.

| Body | XML trunk kg | MuJoCo trunk kg | Speed m/s | Pack mean A | Pack peak A |
|---|---|---|---|---|---|
| Wire, Castle off | 1.0994 | 1.099411 | 0.119570 | 4.460184 | 7.560160 |
| Wire electrical, Castle mass kept | 1.1354 | 1.135376 | 0.115729 | 4.387864 | 7.803820 |
| Wire plus 200 g | 1.2994 | 1.299411 | 0.108535 | 4.365416 | 7.658226 |

Pose difference, wire against Castle kept, over the shared samples: max planar distance 0.519650 m. At 10 s the distance is 0.021660 m (sim pass only).

Pose difference, wire against the 200 g body, over the shared 20 s: max planar distance 0.212928 m (sim pass only).

The Castle mass reached MuJoCo, and this rerun moves speed or current at the printed digits. The earlier match does not repeat. A further 200 g at the original trunk COM does move the 20 s pose, so the walker is reading trunk mass. Sim pass only.

## Breaker, per limb

Three TPS259827ONRGE devices, one per limb, ahead of the feed split. That is the PR 86 candidate. Left is the five left servos, right is the five right servos, neck and head are the four head servos. The current is the sum of supply currents at 2 ms. RILIM 182 ohm is cited at ILIM 7.23 A to 9.07 A over temperature (SLVSFE7, the knee-heat note). The 600 nF timer's short corner is 150 ms and the long corner is 557 ms (calc only, C times dV over I, the cited 0.7 V to 1.3 V and 2.8 uA to 1.4 uA). A limb trips on that corner when its longest stay above the threshold is at least that long. Fast trip is 210 percent of ILIM, typical, cited. At the hot maximum that is 19.05 A (calc only).

The 100 ms moving average is recorded and is not used as a pulse width.

| Command | Corner | Length | Branch | Peak A | Max 100 ms A | Longest above 7.23 A | Longest above 9.07 A | Time above 7.23 A |
|---|---|---|---|---|---|---|---|---|
| 0.15 | high-side | 60 s | left_leg | 4.336 | 2.899 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 60 s | right_leg | 3.831 | 2.796 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 60 s | neck_and_head | 1.315 | 0.649 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | left_leg | 4.347 | 2.899 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | right_leg | 4.388 | 2.796 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | neck_and_head | 1.315 | 0.659 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | left_leg | 4.574 | 2.943 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | right_leg | 3.892 | 2.857 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | neck_and_head | 1.336 | 0.664 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | left_leg | 4.647 | 2.998 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | right_leg | 4.233 | 2.857 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | neck_and_head | 1.347 | 0.664 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | left_leg | 5.652 | 4.344 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | right_leg | 5.316 | 3.594 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | neck_and_head | 2.657 | 1.382 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | left_leg | 5.730 | 4.455 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | right_leg | 5.331 | 3.702 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | neck_and_head | 2.551 | 1.367 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | left_leg | 5.906 | 4.879 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | right_leg | 5.956 | 4.489 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | neck_and_head | 3.179 | 2.116 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | left_leg | 6.408 | 4.969 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | right_leg | 6.241 | 4.508 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | neck_and_head | 3.247 | 2.180 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | left_leg | 6.408 | 4.969 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | right_leg | 6.373 | 4.886 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | neck_and_head | 3.538 | 2.180 | 0.000 s | 0.000 s | 0.000 s |

No limb sample in these walks is above 7.23 A. The highest limb peak is 6.408 A, on the 0.40 m/s jog, typical, left_leg (sim pass only). That peak is under the cited ILIM window, 7.23 A to 9.07 A, so the 600 nF timer does not start. A normal walk does not trip this breaker, and the 0.40 m/s jog does not trip it either. The 100 ms average is not the basis of that call. Calc only against the cited limits, on sim pass only currents.

## Sanity checks

- 0.15 m/s typical speed 0.1196 m/s and pack peak 7.560 A, against PR 85 0.1183 m/s and 8.114 A (sim pass only).
- Per-joint motor RMS matches em_twin's own accumulator within 0.000049 A (sim pass only).
- Falls: none.
- Baseline trunk 1.0654 kg against the PR 85 figure 1.0654 kg (sim pass only).
- MuJoCo trunk mass minus the patched XML mass on the wire body: 0.000011 kg.
- PR 85 printed 0.1183 m/s and 8.114 A from the unpatched 1.0654 kg trunk. This 0.15 m/s walk is the written 1.0994 kg trunk: speed differs by 0.0013 m/s and pack peak by 0.554 A (sim pass only).

## Still BLOCKER

- C018 operating temperature and torque-off current are not on the page this lab opened. The 60 C line, the 70 C cut, and the 21 mA idle are the C001 sheet.
- C018 winding resistance is not printed. The 3.753 ohm split is the PR 86 assumption.
- Creep of the knee sheets at the structure-twin stress is still open. The HDT comparison is the cited temperature, not a creep clearance.
- Whether 600 nF is under the TPS25982 startup limit on ITIMER. The knee-heat note could not extract that equation cleanly.
- Which Pi pin reads the power-good output.
- A 1 ohm nick on the pack lead ahead of the three limb devices still sits under the 15 A fuse. This pass does not re-score that path.

