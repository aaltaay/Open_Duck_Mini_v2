# Run C joint current

UNRELIABLE: the heat clocks in commit 6d8c153, and the same clocks copied into the PR 87 description, are not to be used. That commit stepped the thermal model at 0.5 s on 0.1 s current bins, so four bins in five never heated the knee, and it stored a fall as a list, which aborts the thermal cut when a walk falls. Those withdrawn clocks were: reading 55 C at 1.22 min and 60 C at 1.43 min, case peak 61.41 C, 32 C case peak 62.14 C, guard walk share 0.142 at 25 C and 0.090 at 32 C, guard case peaks 50.44 C and 51.20 C. Commit a0e2251, included in merge 89da799, is the correction. The table below is that CPU rerun, one thermal step per bin. Do not quote the 6d8c153 clocks.

Written 2026-11-13, heat table corrected 2026-11-14. CPU only. The walk is the em_twin sheet walk with the run C policy and the 12 V ST-3215-C018 patch in `problems/sts12.py`. This note walks the PR 85 wire case (3S Molicel P45B wired to the servos, Castle off the trunk) as a study. That case is not the adopted power path. The adopted path keeps the Castle CC BEC Pro. D61 was not edited. Nothing was bought. The policy was not retrained.

Every walk figure is sim pass only. A temperature from the thermal twin is sim pass only. Arithmetic on those currents, and the blanking comparison, are calc only. A datasheet figure is cited. A missing measurement is BLOCKER.

Script: `altaay_lab/problems/runc_joint_current.py`. Numbers: `altaay_lab/problems/runc_joint_current.json`.

## What was logged

Run C had pack current and knee volts. It did not keep a per-servo current. The knee-heat note therefore scaled an older backlash session by Kt, and it marked a run C knee amp BLOCKER. This pass keeps the motor current and the supply current that `em_twin.py` already computes on each 2 ms step.

Commands are 0.15, 0.25, and 0.40 m/s, typical and high-side corners, 60 s. The longer duty is the same command held for 10 min. No walk in this pass fell. Stats start at 4 s, the same window as the pack figures in the electromechanical twin. The logged amps are the post-step sheet law (`servo_sts3215.electrical`), which is the series the twin already reports as motor RMS and supply current.

Baseline trunk before the third cell, from the mass budget after the same JPI seat PR 85 uses: 1.0654 kg (sim pass only). That matches the 1.0654 kg figure PR 85 records.

## Per-joint current

Motor current is the sheet winding current. Supply current is what the limb wire carries, idle included. The hottest joint is the one with the highest motor RMS, because copper heat follows that square.

| Command | Corner | Length | Hottest joint | Motor RMS A | Motor peak A | Pack mean A | Pack peak A | Speed m/s |
|---|---|---|---|---|---|---|---|---|
| 0.15 | high-side | 60 s | right_knee | 1.515 | 2.473 | 4.423 | 7.555 | 0.1136 |
| 0.15 | high-side | 600 s | right_knee | 1.497 | 2.473 | 4.380 | 7.874 | 0.1093 |
| 0.15 | typical | 60 s | right_knee | 1.551 | 2.542 | 4.554 | 8.132 | 0.1233 |
| 0.15 | typical | 600 s | right_knee | 1.520 | 2.542 | 4.443 | 8.162 | 0.1154 |
| 0.25 | high-side | 60 s | right_knee | 1.667 | 2.585 | 6.496 | 11.143 | 0.1753 |
| 0.25 | typical | 60 s | right_knee | 1.709 | 2.694 | 6.533 | 10.973 | 0.1832 |
| 0.40 | high-side | 60 s | left_knee | 1.685 | 2.536 | 8.113 | 13.875 | 0.2527 |
| 0.40 | typical | 60 s | left_knee | 1.719 | 2.658 | 8.236 | 14.509 | 0.2610 |
| 0.40 | typical | 600 s | left_knee | 1.689 | 2.658 | 8.149 | 14.511 | 0.2555 |

All of those rows are sim pass only. The 0.15 m/s typical pack peak is the check against PR 85, which printed 8.114 A and 0.1183 m/s. This run is 8.132 A and 0.1233 m/s (sim pass only).

Normal walk, 0.15 m/s, both corners, 60 s. Amps are sim pass only.

| Joint | Typ motor RMS | Typ motor peak | Typ supply RMS | Typ supply peak | High motor RMS | High motor peak | High supply peak |
|---|---|---|---|---|---|---|---|
| left_hip_yaw | 0.471 | 1.267 | 0.174 | 0.710 | 0.451 | 1.194 | 0.655 |
| left_hip_roll | 0.649 | 1.708 | 0.321 | 1.296 | 0.633 | 1.664 | 1.269 |
| left_hip_pitch | 0.847 | 2.277 | 0.516 | 2.138 | 0.826 | 2.159 | 1.958 |
| left_knee | 1.484 | 2.528 | 1.237 | 2.549 | 1.442 | 2.470 | 2.491 |
| left_ankle | 0.710 | 1.436 | 0.306 | 0.928 | 0.701 | 1.410 | 0.891 |
| neck_pitch | 0.350 | 0.756 | 0.085 | 0.246 | 0.347 | 0.779 | 0.253 |
| head_pitch | 0.447 | 0.971 | 0.129 | 0.380 | 0.457 | 1.113 | 0.513 |
| head_yaw | 0.498 | 1.503 | 0.181 | 0.909 | 0.507 | 1.434 | 0.830 |
| head_roll | 0.427 | 1.249 | 0.162 | 0.708 | 0.410 | 1.160 | 0.632 |
| right_hip_yaw | 0.540 | 1.294 | 0.198 | 0.660 | 0.508 | 1.272 | 0.647 |
| right_hip_roll | 0.569 | 1.643 | 0.239 | 1.224 | 0.548 | 1.597 | 1.185 |
| right_hip_pitch | 0.728 | 1.968 | 0.427 | 1.732 | 0.712 | 1.936 | 1.652 |
| right_knee | 1.551 | 2.542 | 1.340 | 2.563 | 1.515 | 2.473 | 2.494 |
| right_ankle | 0.598 | 1.472 | 0.256 | 1.006 | 0.578 | 1.389 | 0.831 |

Hottest joint on the 0.15 m/s typical walk: right_knee, motor RMS 1.551 A, motor peak 2.542 A (sim pass only). At 0.40 m/s typical the hottest joint is the left knee.

Longer duty, the command held for 10 min. 0.15 m/s high-side, 10 min: hottest joint right_knee, motor RMS 1.497 A over the whole window, 1.513 A in the first minute, 1.491 A in the last minute, pack mean 4.421 A then 4.375 A (sim pass only). 0.15 m/s typical, 10 min: hottest joint right_knee, motor RMS 1.520 A over the whole window, 1.550 A in the first minute, 1.506 A in the last minute, pack mean 4.555 A then 4.383 A (sim pass only). 0.40 m/s typical, 10 min: hottest joint left_knee, motor RMS 1.689 A over the whole window, 1.719 A in the first minute, 1.661 A in the last minute, pack mean 8.235 A then 8.057 A (sim pass only).

## Knee heat on these currents

The thermal twin is the PR 86 model: `twin_thermal.simulate`, the C018 stall-line split that file uses (winding 3.753 ohm, an assumption, the page does not print a winding resistance), the C001 21 mA idle, friction omitted, central corner, torque cut 70 C unless a row says the cut is off. `build_12v` multiplies by Kt 7.4 V over Kt 12 V because its input was a 7.4 V log. These amps are already the 12 V sheet, so the script divides by that factor first. The product is the logged current. A check on the first bin refuses a run that does not land on the log.

Each current bin is one thermal step. The bins are 0.100 s, from `em_twin` `bin_s`. An earlier draft stepped at 0.5 s and sampled one bin in five, so those clocks are withdrawn. The numbers in this table are the rerun that applies every bin (sim pass only).

This study's wire case has no Castle, so the 0.30 V drop in that file is set to 0 for these rows. One comparison row puts the 0.30 V drop back. The knee is outside the trunk. PR 86 already found that trunk vents do not move the knee. Keeping the Castle is a separate owner decision. It is not what these rows simulate.

PLA and PETG do not change the sim temperature. They change the limit the case is compared with. PLA low edge 49 C is cited (SD3D, ASTM D648, the thermal note). PETG 62 C at 1.8 MPa is cited (Bambu PETG HF, the knee-heat note). The C018 page opened for this lab does not print an operating temperature. Using the C001 60 C line and the 70 C torque-off on the C018 is BLOCKER, the same open item as PR 86.

| Series | Case | Room | Reading max | Case max | Time to reading 55 C | Time to reading 60 C | Time to case 49 C | Time to case 62 C | Case at 90 min | Walk share | Rise last 10 min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.15 m/s typical, 10 min | cont70_25 | 25 C | 70.03 C | 61.06 C | 1.16 min | 1.37 min | 1.40 min | does not cross in the run | 27.68 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 10 min | cont70_32 | 32 C | 70.01 C | 61.90 C | 0.87 min | 1.06 min | 1.06 min | does not cross in the run | 34.61 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 10 min | cont200_25 | 25 C | 200.01 C | 179.24 C | 1.16 min | 1.37 min | 1.40 min | 1.99 min | 27.68 C | 1.000 | -0.002 C |
| 0.15 m/s typical, 10 min | guard_25 | 25 C | 55.09 C | 50.31 C | 1.16 min | does not cross in the run | 4.42 min | does not cross in the run | 47.93 C | 0.140 | 0.198 C |
| 0.15 m/s typical, 10 min | guard_32 | 32 C | 55.09 C | 51.01 C | 0.87 min | does not cross in the run | 1.25 min | does not cross in the run | 48.70 C | 0.090 | -0.976 C |
| 0.15 m/s typical, 10 min | cont70_25_drop0p3 | 25 C | 70.03 C | 61.06 C | 1.16 min | 1.37 min | 1.40 min | does not cross in the run | 27.68 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont70_25 | 25 C | 70.02 C | 61.31 C | 1.24 min | 1.46 min | 1.47 min | does not cross in the run | 27.66 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont70_32 | 32 C | 70.02 C | 62.09 C | 0.92 min | 1.13 min | 1.11 min | 2.00 min | 34.60 C | 1.000 | -0.000 C |
| 0.15 m/s high-side, 10 min | cont200_25 | 25 C | 198.32 C | 178.04 C | 1.24 min | 1.46 min | 1.47 min | 2.10 min | 176.86 C | 1.000 | 0.048 C |
| 0.15 m/s high-side, 10 min | guard_25 | 25 C | 55.09 C | 50.33 C | 1.24 min | does not cross in the run | 1.86 min | does not cross in the run | 49.46 C | 0.146 | 0.352 C |
| 0.15 m/s high-side, 10 min | guard_32 | 32 C | 55.08 C | 51.04 C | 0.92 min | does not cross in the run | 1.27 min | does not cross in the run | 48.83 C | 0.093 | 1.530 C |
| 0.15 m/s typical, 60 s | cont70_25 | 25 C | 70.06 C | 61.01 C | 1.16 min | 1.36 min | 1.40 min | does not cross in the run | 27.72 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 60 s | cont70_32 | 32 C | 70.02 C | 61.86 C | 0.87 min | 1.06 min | 1.06 min | does not cross in the run | 34.66 C | 1.000 | -0.000 C |
| 0.15 m/s typical, 60 s | cont200_25 | 25 C | 200.02 C | 177.96 C | 1.16 min | 1.36 min | 1.40 min | 1.98 min | 27.72 C | 1.000 | -0.001 C |
| 0.15 m/s typical, 60 s | guard_25 | 25 C | 55.10 C | 50.29 C | 1.16 min | does not cross in the run | 4.40 min | does not cross in the run | 46.72 C | 0.134 | 0.086 C |
| 0.15 m/s typical, 60 s | guard_32 | 32 C | 55.07 C | 51.00 C | 0.87 min | does not cross in the run | 1.25 min | does not cross in the run | 50.70 C | 0.084 | 5.021 C |
| 0.25 m/s typical, 60 s | cont70_25 | 25 C | 70.09 C | 60.04 C | 0.91 min | 1.06 min | 1.17 min | does not cross in the run | 27.66 C | 1.000 | -0.000 C |
| 0.40 m/s high-side, 60 s | cont70_25 | 25 C | 70.00 C | 60.34 C | 1.01 min | 1.17 min | 1.25 min | does not cross in the run | 27.58 C | 1.000 | -0.000 C |
| 0.40 m/s typical, 10 min | cont70_25 | 25 C | 70.01 C | 60.11 C | 0.94 min | 1.09 min | 1.20 min | does not cross in the run | 27.54 C | 1.000 | -0.000 C |

Temperatures and the walk share are sim pass only. The blank comparison with PR 86 is the guard row: that note reported a walk share of 0.388 at 25 C and 0.201 at 32 C on the Kt-scaled old log (sim pass only). The shares in the table are the same guard, 55 C stop and 45 C resume, torque off while sitting, on the run C current.

A case near 28 C at 90 min, on a row whose reading hit 70 C or 200 C, is the cool-down after that cut unloads the servo. The case max is the peak before the cool-down. On a guard row the 70 C cut does not fire, so the 90 min case is one sample of the walk-and-rest cycle and the case max is the peak of that cycle.

Without the rest rule, cut still at 70 C, 25 C room: the right-knee reading reaches 55 C at 1.16 min and 60 C at 1.37 min. The case reaches 49 C at 1.40 min and peaks at 61.06 C. The case does not reach 62 C in that 25 C run. After the cut unloads the knee the case cools, and at 90 min it is 27.68 C (sim pass only). The 32 C room with the same cut peaks the case at 61.90 C. Sim pass only. With the torque cut raised to 200 C on the typical corner, the reading reaches 200.01 C and the case peaks at 179.24 C (sim pass only). That stand-in cut then unloads the servo. The high-side corner with the same 200 C stand-in ends at a 176.86 C case, last-10-min rise 0.048 C, reading max 198.32 C (sim pass only). That is the balance this model reaches when the sheet cut is not allowed to hide it. The 55/45 guard, on the 10 min current, walks 14.0 percent of the 90 min at 25 C and 9.0 percent at 32 C (sim pass only). PR 86 reported 38.8 percent and 20.1 percent on the Kt-scaled old log. Guard case peak is 50.31 C at 25 C and 51.01 C at 32 C (sim pass only). The 90 min samples are 47.93 C and 48.70 C, and the last 10 min move those samples by 0.198 C and -0.976 C. The 32 C guard cooled over the last 10 min. Both peaks are above the cited 49 C PLA edge and under the cited 62 C PETG point. Putting the 0.30 V Castle drop back leaves the case peak at 61.06 C against 61.06 C on the wire (sim pass only). The knee number does not move with that trunk drop.

Right-knee motor RMS on the 0.15 m/s typical 60 s walk is 1.551 A (sim pass only). The knee-heat note's 12 V shape was a 1.447 A log times the Kt scale 0.702, which is 1.02 A (calc only). This knee draws more than that shape, which is why the clock is shorter and the walk share is lower.

## The 36 g Castle check

PR 85 removed the Castle from the wire-rail body (35.97 g: 29.0 g cited body, 4.6 g leads, tape, and the two output splices) and printed the same speed and the same current to four digits as the wire walk that still carried that mass. The trunk field in that JSON did change, from 1.1354 kg to 1.0994 kg.

The cause is in `system_voltage._patch_trunk`. It parses the MJCF, edits the trunk inertial on the in-memory tree, and returns the new mass. It never writes the tree back to the file (`pr85_patch_writes_file` is False). MuJoCo loads the scene with `from_xml_string` and the asset dictionary, so it kept the unpatched trunk, 1.0654 kg, for both rows. The identical digits are the same model walked twice. This pass writes the inertial, checks that the loaded body mass matches the file, and walks again. The electrical extra stays the wire rail for both bodies. A third body adds 200 g at the original trunk COM and walks 20 s.

| Body | XML trunk kg | MuJoCo trunk kg | Speed m/s | Pack mean A | Pack peak A |
|---|---|---|---|---|---|
| Wire, Castle off | 1.0994 | 1.099411 | 0.123251 | 4.554280 | 8.131589 |
| Wire electrical, Castle mass kept | 1.1354 | 1.135376 | 0.120904 | 4.508240 | 7.743059 |
| Wire plus 200 g | 1.2994 | 1.299411 | 0.111245 | 4.416819 | 7.464018 |

Pose difference, wire against Castle kept, over the shared samples: max planar distance 0.357906 m. At 10 s the distance is 0.021742 m (sim pass only).

Pose difference, wire against the 200 g body, over the shared 20 s: max planar distance 0.176405 m (sim pass only).

The Castle mass reached MuJoCo, and this rerun moves speed or current at the printed digits. The earlier match does not repeat. A further 200 g at the original trunk COM does move the 20 s pose, so the walker is reading trunk mass. Sim pass only.

## Breaker, per limb

Three TPS259827ONRGE devices, one per limb, ahead of the feed split. That is the PR 86 candidate. Left is the five left servos, right is the five right servos, neck and head are the four head servos. The current is the sum of supply currents at 2 ms. RILIM 182 ohm is cited at ILIM 7.23 A to 9.07 A over temperature (SLVSFE7, the knee-heat note). The 600 nF timer's short corner is 150 ms and the long corner is 557 ms (calc only, C times dV over I, the cited 0.7 V to 1.3 V and 2.8 uA to 1.4 uA). A limb trips on that corner when its longest stay above the threshold is at least that long. Fast trip is 210 percent of ILIM, typical, cited. At the hot maximum that is 19.05 A (calc only).

The 100 ms moving average is recorded and is not used as a pulse width.

| Command | Corner | Length | Branch | Peak A | Max 100 ms A | Longest above 7.23 A | Longest above 9.07 A | Time above 7.23 A |
|---|---|---|---|---|---|---|---|---|
| 0.15 | high-side | 60 s | left_leg | 4.293 | 2.924 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 60 s | right_leg | 3.864 | 2.792 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 60 s | neck_and_head | 1.323 | 0.662 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | left_leg | 4.427 | 2.924 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | right_leg | 4.409 | 2.802 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | high-side | 600 s | neck_and_head | 1.359 | 0.667 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | left_leg | 4.632 | 3.058 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | right_leg | 4.081 | 2.888 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 60 s | neck_and_head | 1.448 | 0.690 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | left_leg | 4.632 | 3.058 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | right_leg | 4.351 | 2.888 | 0.000 s | 0.000 s | 0.000 s |
| 0.15 | typical | 600 s | neck_and_head | 1.448 | 0.690 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | left_leg | 5.511 | 4.278 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | right_leg | 5.529 | 3.652 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | high-side | 60 s | neck_and_head | 2.652 | 1.395 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | left_leg | 5.792 | 4.548 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | right_leg | 5.357 | 3.732 | 0.000 s | 0.000 s | 0.000 s |
| 0.25 | typical | 60 s | neck_and_head | 2.604 | 1.352 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | left_leg | 5.986 | 4.868 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | right_leg | 5.959 | 4.650 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | high-side | 60 s | neck_and_head | 3.246 | 2.142 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | left_leg | 6.411 | 5.012 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | right_leg | 6.165 | 4.647 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 60 s | neck_and_head | 3.513 | 2.199 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | left_leg | 6.411 | 5.012 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | right_leg | 6.246 | 4.728 | 0.000 s | 0.000 s | 0.000 s |
| 0.40 | typical | 600 s | neck_and_head | 3.515 | 2.199 | 0.000 s | 0.000 s | 0.000 s |

No limb sample in these walks is above 7.23 A. The highest limb peak is 6.411 A, on the 0.40 m/s jog, typical, left_leg (sim pass only). That peak is under the cited ILIM window, 7.23 A to 9.07 A, so the 600 nF timer does not start. A normal walk does not trip this breaker, and the 0.40 m/s jog does not trip it either. The 100 ms average is not the basis of that call. Calc only against the cited limits, on sim pass only currents.

## Sanity checks

- 0.15 m/s typical speed 0.1233 m/s and pack peak 8.132 A, against PR 85 0.1183 m/s and 8.114 A (sim pass only).
- Per-joint motor RMS matches em_twin's own accumulator within 0.000046 A (sim pass only).
- Falls: none.
- Baseline trunk 1.0654 kg against the PR 85 figure 1.0654 kg (sim pass only).
- MuJoCo trunk mass minus the patched XML mass on the wire body: 0.000011 kg.
- PR 85 printed 0.1183 m/s and 8.114 A from the unpatched 1.0654 kg trunk. This 0.15 m/s walk is the written 1.0994 kg trunk: speed differs by 0.0050 m/s and pack peak by 0.018 A (sim pass only).

## Still BLOCKER

- C018 operating temperature and torque-off current are not on the page this lab opened. The 60 C line, the 70 C cut, and the 21 mA idle are the C001 sheet.
- C018 winding resistance is not printed. The 3.753 ohm split is the PR 86 assumption.
- Creep of the knee sheets at the structure-twin stress is still open. The HDT comparison is the cited temperature, not a creep clearance.
- Whether 600 nF is under the TPS25982 startup limit on ITIMER. The knee-heat note could not extract that equation cleanly.
- Which Pi pin reads the power-good output.
- A 1 ohm nick on the pack lead ahead of the three limb devices still sits under the 15 A fuse. This pass does not re-score that path.

