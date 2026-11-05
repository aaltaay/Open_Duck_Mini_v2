# CHARGE_INTERFACE: what the duck's pack needs to charge on the dock (track 9 for track 8)

Written 2026-11-04 about 10:10 PM ET by the V1 battery option job (track 9, phase 1). Calc only: nothing was tested, bought or
built. Full research and sources: BATTERY_STUDY.md in this folder. The dock job (track 8, D37, D41) owns the dock; this file
only says what the pack side needs. The dock job's DOCK_INTERFACE.md (written after this file, 2026-11-04 ET) uses its 2S plan, 2.0 A, 3 contacts and the 5 to 45 C rule; D44 makes the 2S1P Molicel P45B pack the one to charge.

## 1. Which pack the dock should plan for

Track 9 recommends against the DeWalt DCB200 on this duck (BATTERY_STUDY.md section 1). Plan the dock for a **2S Li-ion
pack** (today's 2S1P Molicel P30B, or the recommended 2S1P Molicel P45B). Keep a **5S DeWalt** interface (section 4) only as
the fallback if Ahmed still picks a DeWalt pack. The two need different charge voltages, so the dock must know which one it
serves (a keyed contact pattern or a sense resistor, section 5).

## 2. 2S pack (today, and the recommendation)

| Item | Value | Source |
|---|---|---|
| Chemistry, layout | 2 cells in series (2S1P), Li-ion NMC 18650 (P30B) or 21700 (P45B) | BOM line 6; Molicel sheets [M1], [M2] |
| Charge voltage (CV) | 8.40 V (4.20 V per cell; the P45B sheet allows 4.20 +/- 0.05 V). The BMS trips over-charge at 4.280 +/- 0.025 V per cell | [M1], [M2]; Tenergy 32175 page (POWER.md section 5) |
| Charge current (CC) | P30B: standard 3 A, maximum 9 A per cell [M1]. P45B: rated 4.5 A, maximum 9 A [M2]. Dock design value: **2.0 A** (heat in the robot, section 6) | [M1], [M2] |
| Termination | CV until the current falls to C/20 (P45B test cycle: "charge to 4.2 V for 50 mA" [M2]) | [M2] |
| Cell temperature window for charging | 0 to 60 C (both sheets). Dock rule: charge only between 5 C and 45 C at the cells (margin), stop above 50 C | [M1], [M2]; margin is a lab choice |
| Temperature sensing | the Tenergy 32175 BMS carries a 10 k 3380 NTC (POWER.md section 5); its use by the board is not published. The robot's thermal twin puts the cells at 44 to 56 C at the battery stop (THERMAL_TWIN.md), so a just-stopped duck is often over the 45 C dock rule: the robot waits (or the dock waits) until the cells read under 45 C | POWER.md; THERMAL_TWIN.md |
| Balancing | none on the Tenergy board ("/" in its balance rows); same-batch cells, check both cell voltages at each charge for the first 10 charges (POWER.md section 5) | POWER.md |
| Protection in the charge path | the Tenergy BMS (over-charge 4.28 V, over-discharge 2.40 V, over-current 22 +/- 5 A); the Littelfuse 15 A ATO fuse | POWER.md sections 4, 5 |
| Today's charger | Adeept USB-C 2S board in body_back, 5 V in, 1.1 A charge (BOM). On the dock it needs 5 V at about 2 A on two contacts | BOM; calc: 8.4 V x 1.1 A / 5 V / 0.9 = 2.05 A |
| Charge time, calc only | P30B 2S1P (2.85 Ah to 2.5 V [p30b.py]): 1.1 A (Adeept) about 3.0 h; 2.0 A about 1.7 h. P45B 2S1P (4.35 to 4.5 Ah [M2]): 1.1 A about 4.6 h; 2.0 A about 2.6 h; 3.0 A about 1.8 h | capacity / I x 1.15 for the CV tail (calc only; 1.15 is an ASSUMPTION) |
| Energy per charge | P30B 2S1P 21.6 Wh (2 x 3.0 Ah x 3.6 V [M1]); P45B 2S1P 32.4 Wh (2 x 4.5 Ah x 3.6 V [M2]) | [M1], [M2] |

Two ways to put this on a dock (the dock job chooses; both are calc only):
- **A, 5 V dock (today's robot, no new robot part):** the dock feeds the Adeept board's 5 V input through two contacts
  (5 V, 2.5 A rating at least). Slow (1.1 A), but the contacts carry only 5 V, and the robot's own board does CC/CV.
- **B, 2S charger in the dock (faster):** a 2S CC/CV charger in the dock (8.40 V, 2.0 A) feeds BMS P+ and P- through the
  contacts and a reverse-blocking switch in the robot (section 5). The robot keeps the BMS; the Adeept board can stay for
  bench charging. The charger's heat stays in the dock.

## 3. What the robot side gives the dock (both packs)

- Contacts: **2 power contacts (+, -) rated 3 A or more, plus 1 sense contact** (pack NTC or a dock-detect resistor).
- The robot's power contacts are dead unless the dock drives them: a reverse-blocking ideal-diode switch on the robot side
  (part chosen in phase 2) keeps the pack voltage off the exposed contacts. The dock turns its output on only after it reads
  the sense contact (section 5).
- The robot reports its own charge state over Wi-Fi (the Pi): pack voltage, current and cell temperature (the phase 2 pack
  monitor, BATTERY_STUDY.md section 4). The dock needs no data link to charge safely.
- The robot stays switched on (Pololu 2813 on) while it docks and charges, so the Pi can watch the cells; standing with the
  torque on draws 2.0 to 2.2 A from the pack (TWIN_LIVE.md section 1), more than a 2 A charger gives. **So the duck must sit
  or rest with the servos unloaded on the dock** (torque-off on a stand: idle heat only, TWIN_LIVE.md lever rank 1), or the
  charger must give at least 2.5 A plus the charge current. This is the main point for the dock job.

## 4. 5S DeWalt 20V MAX pack (fallback only)

| Item | Value | Source |
|---|---|---|
| Layout | 5 cell groups in series: 5S1P (DCB203, 2 Ah; DCBP034 POWERSTACK 1.7 Ah), 5S2P (DCB200 3 Ah: LG HB4 1.5 Ah cells; DCB204 4 Ah; DCB205 5 Ah) | [S1] teardown; DeWalt pages [D3], [D4], [D5], [D6] |
| Voltage | 20 V maximum, 18 V nominal ("Maximum initial battery voltage (measured without a workload) is 20 volts. Nominal voltage is 18") | DeWalt pages [D3] to [D6] |
| Full charge as DeWalt charges it | 20.43 V, 4.08 to 4.09 V per group, measured on a DCB200 off a DeWalt charger | [S1] |
| Dock CV setting | **20.50 V (4.10 V per group)**, never above 21.0 V (4.2 V per cell). ASSUMPTION: the DeWalt cells' own charge voltage is not published by DeWalt | [S1]; calc |
| Terminals (8) | B+, B-, TH, ID, C1, C2, C3, C4. TH: a 10 k at 25 C NTC between B+ and TH, on the pack board (it reads the board, not the cells). ID: a resistor to B- that tells DeWalt chargers the pack type. C1 to C4: the cell-group taps (C1 is the first group up from B-) | [S1], [S2] |
| What the pack does by itself | nothing that cuts current: "There is no way that the BMS can cut off current if the pack voltage is low" [S1]; "no low voltage cutoff or overcurrent cutoff - the tool is required to handle all that" [S2]. DeWalt: "XR Li-ion products are designed with an Electronic Protection System that will protect the battery pack against overloading, overheating or deep discharge. The product will automatically turn off" [D1] (the product, not the pack) | [S1], [S2], [D1] |
| Balancing | DeWalt chargers use C1 to C4 [S2]; the 2016 DCB200 board also balances by itself, the 6 Ah board does not [S1], [S2]. A third-party CC/CV charger on B+ and B- only does not balance | [S1], [S2] |
| Charging temperature | DeWalt: "Only charge batteries in air temperature over 4 ° C and below 40 ° C"; "Do not store or use the product and battery pack in locations where the temperature may fall below 4 ˚C ... or reach or exceed 40 ˚C (104 ˚F)". DeWalt chargers pause a hot or cold pack (Hot/Cold Pack Delay) | DeWalt batteries and chargers manual NA485944 [D1] |
| Dock charge current | 2.0 A (dock design value). DeWalt lists charge times of 45 min (DCB203), 90 min (DCB204, DCB205) and 35 min (DCBP034) on its pages, charger not named | [D3] to [D6] |
| Charge time at 2.0 A, calc only | DCBP034 1.7 Ah 1.0 h; DCB203 2 Ah 1.2 h; DCB200 3 Ah 1.7 h; DCB205 5 Ah 2.9 h | capacity / I x 1.15 (calc only) |
| Where the charger lives | in the dock: a 5S Li-ion CC/CV charger (20.5 V, 2 A) with the TH check. A genuine DeWalt charger cannot charge a pack held in the robot without carrying all 8 pack terminals to the dock (the rail slot is the interface); not recommended | calc |
| Robot side, extra | a cell-group monitor on C1 to C4 (stop the charge if any group passes 4.15 V or the groups differ by more than 50 mV), and a manual DeWalt-charger balance charge when the monitor asks for it | calc; ASSUMPTION thresholds |

## 5. Sense contact and pack identity (proposal)

- 2S pack: a 10 k resistor from the sense contact to the robot's minus contact; 5S pack: 47 k. The dock reads it before it
  turns its output on and refuses any other value (so a 20.5 V dock never charges a 2S pack). Values are a lab proposal.
- With the NTC on the sense contact instead (5S: TH sits on B+, so the dock reads TH to B+), the dock gets the pack
  temperature too. Phase 2 decides with the dock job.

## 6. Heat on the dock

- Charge loss in the cells at 2.0 A: P30B 2S1P about 2 x 2.0^2 x 0.017 = 0.14 W (DC 17 mOhm at 50 % SOC [M1]); P45B 2S1P
  about 0.12 W (15 mOhm DC [M2]). Small (calc only).
- A charger inside the robot would add its own loss (about 1 to 2 W at 2 A, 85 to 92 % efficiency, ASSUMPTION) to a trunk that
  already runs warm (THERMAL_TWIN.md). Keep the charger in the dock (way B) or keep the slow 5 V board (way A).
- In a 32 C room the cells start a charge near 32 C or warmer (cells 44 to 56 C at the battery stop, THERMAL_TWIN.md): inside
  the Molicel 0 to 60 C window, outside the DeWalt 40 C air rule for a DeWalt pack until it cools.

## Sources
- [M1] Molicel INR-18650-P30B product data sheet v1.0: https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf (read 2026-11-04 ET)
- [M2] Molicel cell specification INR21700P45B-01 v0.2: https://www.kronium.cz/uploads/p45b-datasheet.pdf (read 2026-11-04 ET)
- [S1] Sevarg, "DeWalt 20V Max 3.0Ah Battery Pack Teardown & Analysis", 2016-09-11: https://www.sevarg.net/2016/09/11/dewalt-20v-max-30ah-battery-pack/
- [S2] Sevarg, "DeWalt 20V Max 6.0Ah Pack Teardown & Analysis", 2017-04-22: https://www.sevarg.net/2017/04/22/dewalt-20v-max-60ah-pack-teardown/
- [D1] DeWalt batteries and chargers instruction manual NA485944 (GB/XE): https://service.blackanddecker.com.au/i/DEWALT/GLOBALBOM/XE/DCG412N/1/Instruction_Manual/EN/NA485944_man_dewalt_batteries_and_chargers_GB_XE.pdf
- [D3] DCB203: https://www.dewalt.com/en-us/product/dcb203/20v-max-2-ah-battery ; [D4] DCB204: https://www.dewalt.com/en-us/product/dcb204/20v-max-4ah-battery ; [D5] DCB205: https://www.dewalt.com/en-us/product/dcb205/20v-max-5ah-battery ; [D6] DCBP034: https://www.dewalt.com/en-us/product/dcbp034/20v-max-xr-compact-battery (all read 2026-11-04 ET)
- Lab files: POWER.md, BOM.md, THERMAL_TWIN.md, TWIN_LIVE.md (shared lab gym, overlay gym/overlays/duck)
