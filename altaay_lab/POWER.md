# POWER: servo regulator, fuse and battery path (lab change D3)

Decision (Ahmed, 2026-11-01 1:09 PM ET, answers D3): add a regulator so the servos never see more than 7.4 V.
Prices and stock checked 2026-11-01 (America/New_York). Nothing bought.

## 1. Requirement
- Input: 2S Li-ion, 6.0 V (empty) to 8.4 V (full).
- Output: 7.2 to 7.4 V, never above 7.4 V (STS3215 C001 rating 6 to 7.4 V; Feetech excludes over-voltage from warranty).
- Load: 14x STS3215 C001 on one bus through the Waveshare adapter.
- Below about 7.3 to 7.5 V of pack voltage the output may simply follow the input. That is acceptable (servos still in their 6 V minimum range).

## 2. Current sizing (estimate, not measured)
| Case | Estimate | Basis |
|---|---|---|
| Idle, torque on, standing | about 1 to 2 A | 14 servos holding a 2.1 kg robot |
| Walking, continuous average | about 4 to 8 A | 10 leg servos at roughly 0.4 to 0.8 A average each, head servos light |
| Walking, short peaks | about 15 to 20 A | several leg servos accelerating together at foot strike |
| All 14 stalled at once | about 38 A (14 x 2.7 A) | stall about 2.5 to 2.7 A each (Feetech C001); only in a jam or fall, not a design case. The fuse should open. |

Battery side current is higher than servo side current at high pack voltage only by the efficiency: I_pack = I_out x 7.2 / (0.9 x V_pack). At 10 A out and 7.4 V pack this is about 10.8 A. At 15 A out it is about 16 A.

So the regulator needs about 10 A continuous inside a closed body and 20 A peaks.

## 3. Candidates checked
| Part | Output | Current | Price, seller | Verdict |
|---|---|---|---|---|
| Castle Creations CC BEC Pro, P/N 010-0004-01 (UPC 899598001717) | adjustable 4.8 to 12.5 V (default 5.1 V), set to 7.2 V | 20 A peak; 15 A continuous at 2S to 4S (16 V) input, rated with 5 mph airflow | $54.95, castlecreations.com (Olathe, KS); store shows available | CHOSEN |
| Pololu D42V110F7 (#5674) | fixed 7.57 V +/-3% (up to about 7.8 V) | 7 to 14 A | $69.95, pololu.com (Las Vegas, NV) | Rejected: above 7.4 V, cannot be trimmed down |
| Pololu D42V110F6 (#5673) | fixed 6 V | about 11 A | pololu.com | Fallback only: complies but servos run slower than the 7.4 V sim |
| Pololu D24V150F7 (#2883) | fixed 7.5 V +/-4% | 15 A | $79.95, listed "Rationed" | Rejected: above 7.4 V |
| Pololu D36V50F7, D42V55F7 | fixed 7.5 V | 5 A class | pololu.com | Rejected: above 7.4 V, too small |
| Pololu custom voltage | any | any | needs contacting Pololu | Not done (no messages allowed) |
| Castle CC BEC 2.0 WP, 010-0153-00 | 6.25 to 8.5 V adjustable | 9 A continuous, 15 A peak | $56.95, castlecreations.com | Backup. Minimum input voltage not verified for 2S. |

Why the CC BEC Pro:
- It is the only US brand, US sold, full-spec part found that can be set at or below 7.4 V and still delivers about 15 A continuous and 20 A peaks.
- 7.2 V gives 0.2 V margin under the 7.4 V cap for setpoint tolerance and transients (Castle does not publish setpoint accuracy, so measure it).
- Castle warranty: one year from date of purchase (user guide P/N 095-0047-00 and product pages). Castle also has a non-warranty replacement program.
- Size 43 x 33 x 24 mm, 29 g without wires (user guide).
- Origin: current Castle pages say "Assembled in the Philippines", designed in Olathe, Kansas. The 2009 guide says components from USA, Mexico and China.

Limits and how we handle them:
- The 15 A continuous rating assumes 5 mph airflow. Inside the duck there is none. Our 4 to 8 A walking load leaves about 2x margin. Mount it against the body wall with an air gap and check its temperature after 10 minutes of walking.
- Output comes on two 3-pin servo leads, each good for 5 A continuous (Castle guide). Cut both, join red to red and black to black, and run 16 AWG to the adapter screw terminal.
- Setting 7.2 V needs the Castle Link V4 USB Programming Kit (011-0173-00, $29.95, Windows 10 or later, Castle Link 2 software, "compatible with ALL Castle Linkable devices"). We do not have a Windows PC on the box. The CC BEC Pro is powered at 5 V or more while it is programmed.
- Dropout below the setpoint: not published by Castle. Expected behavior for a buck is that the output tracks the input minus a small drop. Not verified. Measure the output with the pack at 7.0 V and 6.5 V on a bench supply.
- Stock: castlecreations.com store data says available on 2026-11-01, but an older Castle page said "temporarily out of stock". Not verified until checkout.

## 4. Fuse
- Fuse: Littelfuse ATO 15 A, 32 V, P/N 0287015.PXCN (current part; replaces 0257015.PXPV). About $0.45 each (DigiKey shows about EUR 0.39; DigiKey blocks our fetches, so the US price is not verified).
- Holder: Littelfuse FHAC0001ZXJ, inline ATO holder, 20 A, 32 V, 16 AWG leads. $7.74 at Newark (stock not verified).
- Place it right after BMS P+, before the switch, so it protects the BMS, the switch and the whole harness.
- Why 15 A: walking continuous pack current is about 5 to 9 A; ATO fuses carry 110% indefinitely and open at 135% only after 0.75 to 600 s, so 20 A bursts lasting a fraction of a second pass. A sustained jam (above about 20 A) or a short opens it. 15 A also matches the XT30 rating (15 A) and stays under the BMS 20 A claim.

## 5. BMS and holder (issue #51)
Issue #51 (https://github.com/apirrone/Open_Duck_Mini/issues/51, no replies as of 2026-11-01) asks whether the spring 2x18650 holder and thin wires bottleneck 14 servos, and about 8.4 V on 7.4 V servos.
- Cells: Molicel P30B is rated 30 A continuous. Not a bottleneck.
- BMS: AITRIP B08NSTF8CT claims 20 A. Seller claim only, no datasheet. Our continuous load (5 to 9 A) is fine; 16 A bursts are near its claimed limit. Its over-current trip point is unknown, so it might cut out on peaks. Test on the bench.
- Holder: spring contacts have no published current rating (Keystone 1049 dual 18650 holder also has none). This is the likely bottleneck. Measure the drop across the holder at 10 A. If it is over about 0.3 V, or the springs get warm, replace it with a spot-welded 2S pack with nickel strip and 16 AWG leads.
- Wires: use 16 AWG silicone on every power run (WIRING.md section 4).
- Over-voltage: solved by the regulator above.
