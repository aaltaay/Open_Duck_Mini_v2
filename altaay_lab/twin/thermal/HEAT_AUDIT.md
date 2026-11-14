# Knee heat audit, 2026-11-14

The one-click twin had the right knee at 55 C in about a minute, then a powered stand that stayed there. This note checks that clock against the published STS3215 / ST3215 numbers. Temperatures from the twin stay sim pass only. Arithmetic is calc only. A figure from a datasheet or a published test is cited. A missing bench measurement is BLOCKER.

## What the sheet prints

ST-3215-C018 product specification A/0, 2023-07-20, downloaded from the Feetech page https://www.feetechrc.com/525603.html (the PDF link on that page). Cited.

| Item | Printed value |
|---|---|
| 1-2 operating temperature | -10 C to 60 C |
| 5-3 no-load running current | 180 mA at 12 V |
| 5-4 stall torque | 30 kg.cm at 12 V |
| 5-5 stall current | 2.7 A at 12 V |
| 5-6 idle current, stopped | 30 mA |
| 5-8 / 5-9 rated point | 10 kg.cm at 900 mA |
| 5-10 terminal resistance | 1.0 ohm |
| 5-11 Kt | 11 kg.cm/A |
| 7-11 overheat | torque off above 70 C |
| performance table | 15 kg.cm at 1450 mA, 30 kg.cm at 2650 mA |

The same product page prints the operating range as -20 C to 60 C. The PDF item 1-2 prints -10 C to 60 C. Both put the top of the operating range at 60 C. The earlier BLOCKER, that the C018 page had no operating temperature, is closed by this PDF.

The page and the PDF also print no-load running current 180 mA and, in the PDF, stopped idle 30 mA. The thermal twin had been adding the C001 sheet's 21 mA. The sit in this run uses the 30 mA stopped idle.

## The 3.753 ohm figure

12 V / 2.7 A = 4.444 ohm (calc only, from the cited stall voltage and stall current). The C001 sheet prints 2.5 ohm against a stall line of 7.4 V / 2.5 A = 2.96 ohm. The share 2.5 / 2.96 applied to 4.444 ohm is 3.753 ohm. That share is not printed for the C018. The C018 sheet prints 1.0 ohm in item 5-10.

Those two C018 numbers disagree with each other. A winding of 1.0 ohm across a hard 12 V bridge would draw about 12 A, and the sheet's stall current is 2.7 A. The same PDF turns torque off when current stays above 2 A for 2 s (item 7-11). A stall test that is sitting on that limit reads V/I = 4.444 ohm even when the copper is 1.0 ohm. At a partial load the bridge is switching, the motor voltage is about I times 1.0 ohm plus the back EMF, and the copper heat is I squared times 1.0 ohm.

## Does 55 C in one minute at 1.5 A match the published tests

Robo9, Feetech STS3215 C018, 12 V, 1:345: a 1 kg mass on a 15 cm arm held sideways, which is 15 kg.cm. The internal reading rose to 48 C in 10 minutes and stayed there for an hour. A later oscillation, already at 48 C, took 50 minutes to reach 60 C. Source: https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/ . The chart points used in twin/thermal/THERMAL_TWIN.md are 25, 30, 35, 40, 45, 48 C at 0, 2, 4, 6, 8, 10 minutes.

The C018 performance table puts 15 kg.cm at 1450 mA (cited). Copper at the printed 1.0 ohm is 1.45 squared times 1.0 = 2.10 W (calc only). The chart rises 23 K and stops. Implied case-to-ambient is 23 / 2.10 = 11.0 K/W (calc only, taking the chart's first point as the room). The thermal twin's bare-case convection and radiation on the measured 6690 mm2 case is 11.2 to 11.6 K/W (THERMAL_TWIN.md, sim pass only for that physics). The printed 1.0 ohm and that case-to-ambient describe the same plateau.

Copper at 1.5 A and 1.0 ohm is 2.25 W (calc only). At 11 K/W the steady rise is about 25 K, so the case levels off near 50 C in a 25 C room. It does not reach 55 C. The same current at 4.444 ohm is 10.0 W (calc only) and the steady rise is about 110 K. That is the one-minute clock.

55 C in about one minute at about 1.5 A RMS is not a credible hardware time. It is what the stall-line resistance produces when it is used as copper resistance. The published hold at the same current stops at 48 C.

## What this run uses

The one-click twin now heats each servo with I squared times the cited 1.0 ohm. It does not add the 0.691 ohm board term from the 3.753 split, because item 5-10 is already the terminal resistance. Friction heat is still omitted. A bench measurement of one C018 winding, next to a stall current at a known voltage, is still BLOCKER. Until that measurement, the sheet's own 1.0 ohm is the number that agrees with the only published temperature curve.

The knee joint in the walk model was compiled at 90 deg. The sit CAD allows 150 deg at the bumper, and the register soft stop is 147 deg (software/servo_limits.json, CAD check only). The rest now folds to that 147 deg pose and then sets the motor gains to zero. The powered stand is no longer the rest.
