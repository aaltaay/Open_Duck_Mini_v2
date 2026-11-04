# Assembly twin (V1 track 2)

Written 2026-11-04 evening ET by the V1 track 2 agent. CAD check only (ray casts on robot.urdf and the stock print/ STLs, twin/assembly/asm_geom.py) and calc only (twin/assembly/asm_calc.py). Nothing printed, bought or sent. Outputs: asm_geom_summary.json, asm_calc.json, BUILD_ORDER.md, button_plate_d30.stl (this folder); full data /home/user/v1_out/asm/asm_geom.json (off git).

Decisions read: D28; D29 (two LEDs per eye) was reverted by Ahmed at about 6:45 PM ET (the lead's D33): the side projector lamp, its reflector, its lead and the D24 drill step stay as before D29, one eye LED per eye; this track keeps only the viewer LED labels. D30 (the Pololu 2813 swap, Ahmed's OK relayed by the lead at 5:58 PM ET) is applied here.

Shared numbers. Fall shock: worst of the 10 falls, soft 71 g head and 45 g trunk, mid (tile or concrete) 196 g head and 128 g trunk (twin/structure/STRUCTURE_TWIN.md section 3). VHB 4950: 3M's design value for dynamic loads 12 lb/in2, used as 82.7 kPa (3M VHB data sheets via search index), and the 4950 dynamic overlap shear 80 lb/in2 = 552 kPa (FindTape listing via search index); the 3M and FindTape hosts are not reachable from this session, so both were read through the search index.

## 1. Held: every part with no screw

| Part | Mass g (source) | Mount | Mid fall | Verdict |
|---|---|---|---|---|
| Side projector lamp: flash_light_module + flash_reflector_interface + E5 + LED | 12.52 (8.40 and 2.32 sliced, print/SLICE_SUMMARY.md; E5 1.5 and LED 0.3 UNVERIFIED) | none in the CAD (MOUNTING.md: no screw; it sits outside the head's left wall) | 24.1 N | FAIL before. FIX: VHB 4950 (BOM 29) on its contact face with the head shell, 1018 mm2 within 0.3 mm (CAD): 23.6 kPa, SF 3.5 on 82.7 kPa, 23 on 552 kPa (needs 291 mm2). The reflector interface sits in the module on 1080 mm2 of contact: tape it there too; the E5 reflector gets a VHB ring in its seat (needs 36 mm2). |
| Castle CC BEC Pro | 29.0 (Castle guide) | VHB on 1858 mm2 (THERMAL_TWIN.md) | 36.4 N | Direct 19.6 kPa, SF 4.2. RISK: tipping about the 33 mm edge with the load at the box centre, 13 mm up: edge 75.1 kPa, SF 1.1. FIX: one BOM 32 tie over the top through two BOM 34 mounts on the floor beside it (spares: 94 ties bought for 78, 39 mounts for 32): the edge load goes to the tie, 36.4 x 13 / 33 = 14.3 N against 80 N (18 lbf), SF 5.6; the tape is left with the direct 19.6 kPa, SF 4.2. Check the two 19 mm spots at the TEST_PLAN 1.4 dry fit. |
| Littelfuse fuse holder | 8.0 (UNVERIFIED) | VHB 745 mm2 on the lid | 10.0 N | 13.5 kPa SF 6.1; edge 47.2 kPa SF 1.75. OK. |
| Pololu 2813 (D30) | 2.7 (Pololu) | VHB 353 mm2, the 2815 seat on the lid | 3.4 N | 9.6 kPa SF 8.6. OK. |
| D30V30F5 5 V regulator | 3.3 (Pololu) | VHB, 0.7 x 0.8 in face (361 mm2) | 6.3 N | 17.6 kPa SF 4.7. OK. |
| MAX98357A amp | 1.2 (Adafruit) | VHB | 2.3 N | Needs 28 mm2; any face of the board is larger (board size not read). OK. |
| Speaker E1 | 28.8 (Same Sky) | caged by speaker_stand and speaker_interface, tape against rattle | 55.4 N | Every one of its 6 sides has a wall within 3 mm over 6 to 24 % of the face (CAD, the 36 x 36 x 14.5 box in the 38 x 16 x 34 pocket). The load goes into the 4 M2.5x5 interface screws, SF 11 (STRUCTURE_TWIN.md). OK. |
| USB cable slack coil | 10.95 (Adafruit 3878 share) | tie and tape | 13.8 N | Tape alone needs 166 mm2 of a round coil: tie it to a BOM 34 mount (80 N tie, SF 5.8). |
| Eye LED beads (stock, one per eye) | 0.3 (UNVERIFIED) | dome in the bulb's 8.0 mm centre hole (CAD r 4.0); nothing holds it in | 0.58 N | FIX: a VHB ring from the bead base to the bulb back (needs 7 mm2). |
| Eye glass E4 | 2.08 (upper bound) | between the eye lip and the head wall | | Both windows r 12.5 mm against the glass r 14.8 (CAD): captured. OK. |
| D30 button plate and NKK button | plate 0.64 | flange 23.4 x 11 on the outer face, VHB on the 149 mm2 ring, the button's nut | 0.8 N | SF 15. OK. |
| XT30 pair, splices, BMS, cells and holder | 0.9; 1; 3.0; 122 | XT30 on its leads inside the closed body_back module (no open direction, CAD); splices tied into the bundle; BMS sandwiched (0.83 mm play); cells behind the lid (4 x M2.5x10, SF 8.0) | | OK. |

Screwed parts (fasteners.json, mid-fall SF from STRUCTURE_TWIN.md): Pi 45, adapter 52, charger 22, eyes 33, camera 75, lid 8.0; the IMU's 3 g on 4 x M2.5x6 (about 1 N per screw at 128 g). Foot switches press fit (upstream guide). The 6804 bearings were not checked here (upstream seats).

## 2. Screws and the build order

- 286 screws are driven (342 fitted less the 56 factory case screws inside the servos). With every part in place at zero pose, 115 have a clear tool path: the rest need an order.
- FAIL before: the BOM has no screwdriver for the 95 cross-head screws (72 M2 pan heads, 14 Feetech M3x6 horn screws, 3 PA3x5 idle screws, 6 SG90 bag screws). FIX (needs Ahmed's OK, not on the buy lines): Wera 2050 PH 0 x 60 mm (blade 3.0 mm, $7.91, https://hausoftools.com/products/wera-05118022001-2050-precision-phillips-electronics-screwdriver-ph-0-x-60-mm), Wera 2050 PH 1 x 80 mm (blade 4.0 mm, $9.76, https://www.hausoftools.com/products/wera-05118024001-2050-ph-screwdriver-for-phillips-screws-for-electronic-applications-ph-1-x-80-mm), Wera 851/1 Z PH 0 x 25 mm bit (1/4 in hex, $1.95, https://www.jensentools.com/product/873SC5651-05056500001). The Feetech screw drive is not published (B2): the cast uses PH1 for it.
- FAIL before: 10 screws had no order in which any BOM tool reaches them. FIXED (CAD check, 0 violations in the final order, BUILD_ORDER.md): the trunk core order (trunk_top to trunk_bottom first, the centre servo second, the hip yaw servos third, their top case screws before the hip roll brackets); the PH0 25 mm bit for F126, F128, F130, F132 (58.5 mm free, the blade is 60) and F348, F350 (35.6 mm free); the 2.5 mm key's short arm for F158 to F161 (64.9 mm free, 210 to 250 deg of swing at 15 to 30 mm); the neck pitch at -9.4 deg for F083, F084 (body_middle_top 74 mm out of the 88 mm key). The 2.5 mm key's short arm is not published (Bondhus 12154: 88 mm overall); the swing check holds for any short arm from 15 to 30 mm.
- Tools as cast: BOM T4 2.0 mm key 82.6 mm overall, 15.9 mm short arm (Bondhus 13952 listing); 2.5 mm key 88 mm (Bondhus 12154 listings); radius plus 0.2 mm.

## 3. Service from the built duck

- Cells and XT30. The battery_pack_lid faces forward into the trunk: in the built duck its 4 screws point into the middle body (first part at 30.5 to 52.4 mm, 0 to 20 deg of short-arm swing): not reachable. FIX (procedure, CAD check, no part change): remove the 8 M3x8 from body_back to body_middle_bottom and body_middle_top (all 8 clear), pull body_back 20 mm back on its wires (netlist rule slack: P10 85.2 mm, P13 182 mm), then the lid screws take the 2.0 mm key's short arm (first part 50.5 to 72.4 mm, 260 to 310 deg free); the lid comes off with the fuse holder and the 2813 on it; the XT30 then sees 96 % of the forward directions open; the cells lift out. RISK left: the module stays on its wires (P10, P13, the D30 OFF wire).
- microSD and Pi USB. The Pi hangs inside the closed head (0.6 % of directions open from the card slot). Steps: the 8 M3x8 of head_bot_sheet (6 clear, F083 and F084 with the neck at -9.4 deg), drop the sheet down the neck; then 7 % of directions are open from the slot and the card slides 25.9 mm free (it needs 15): tweezers. The USB edge then sees 11 %, a plug has 62.5 mm free. RISK left (more than one lid). Option with a part (needs Ahmed's OK): a 25 cm microSD extender, cablecc EP-009 (microSD to SD), $7.99 (Amazon B08SW7ZCDM via specpicks.com); BLOCKER for its fit: the socket board size is not published. With D28's read-only root the card is rarely pulled, so no extender now.

## 4. Mass (calc only; sim/MASS_BUDGET.md section V1 track 2)

- Screws: the 286 driven screws weigh 174.3 g by the same ISO 4762 and A2 formulas (sim/mass_budget.py) against 175.3 g for the 274 modelled: -1.0 g. Washers +0.5 g. D30: +0.1 g (2813), +1.6 g (OFF wire, 26 AWG on the 531.7 mm P13 route), +0.6 g (plate).
- Cable ties: 78 fitted at most against the 1.0 g modelled: at most +31.5 g (0.417 g per tie is the gross weight of a longer 142 mm Panduit PLT1.5M-C, TME; the trimmed tails make it less).
- New total: 2654.7 g counted for sure, up to 2686.2 g with the tie upper bound (+1.26 %), plus the 55 tie mounts, whose mass is not published: BLOCKER, weigh 10 of each (and 10 trimmed ties) on arrival.
- Over 1 % only at the tie upper bound. It would touch every result run at 2652.8 g: the stock policy at our mass (sim/ADDED_MASS_SIM.md), the structure twin loads, the track 1 and 1b shove currents (B47), the thermal twin, and the RunPod training mass (STATE.md open question 1). The lead decides the gym model update.

## 5. Eye lamps: dropped (D29 reverted, D33)

No D29 change was made. The viewer now names each LED ("Eye LED left", "Eye LED right", "Projector LED") so no label hides behind another; the eye LED retention fix is in item 1.

## 6. Pololu 2813 swap (D30)

- Ratings (Pololu 2813 page, HP column, read with curl 2026-11-04): 4.5 to 40 V; 6 A continuous at 55 C, 16 A at 150 C, 90 A maximum, the same as the 2815; off state under 0.2 uA; 0.8 x 1.0 x 0.16 in, 2.7 g. The track 1b worst 4 ms window 15.89 A is 18 % of the 90 A maximum; the walking RMS 5.90 to 5.92 A is 98 to 99 % of the 6 A point, as with the 2815, so TEST_PLAN 4.2 (the switch heat check) applies unchanged.
- Wiring: the button across A and B (Pololu: "B Connect through momentary switch to pin A for standard push-on/push-off operation"); GPIO26 (pin 37) to OFF ("A high pulse (> 1 V) on this pin turns off the switch"), with dtoverlay=gpio-poweroff,gpiopin=26, active high. Boot and walk: GPIO26 is an input with its reset pull-down until the overlay loads, then driven inactive (low); the overlay drives it active only at poweroff and halt (README quoted in twin/electrical/ELECTRICAL_TWIN.md, Track 1b fixes); active_low is not used, so a reboot does not pulse it. OFF needs more than 1 V, so neither a boot nor a walk can switch the duck off. At connect the 2813 starts off (it can start on only near the top of its range; we run at 6.0 to 8.4 V).
- Off drain: under 0.2 uA (2813) plus 10 uA (BMS) = under 10.2 uA (track 1b): more than 5 years to 2.5 V. B49 fixed in the twin (calc only); TEST_PLAN 11 has the bench check.
- Button (BOM 10b): NKK MB2011SS1W01, MB2000 series momentary pushbutton, 1/4-40 threaded bushing with keyway, 8.5 mm long (NKK MB2000 drawing via search index), body 13 mm (sibling MB2011LS1W03-CA, Arrow). $8.16, 0 in stock at myMectronic (https://www.mymectronic.com/part-detail/NKK-Switches/MB2011SS1W01); the -CH variant $7.71 at DigiKey, out of stock. No datasheet part fits the 15.7 x 7.4 slot, so the smallest change is a printed plate, button_plate_d30.stl (535 mm3): a 15.0 x 6.5 x 3.0 mm plug in the measured 15.5 x 7.0 mm opening (0.25 mm a side, every plug cell open), a 23.4 x 11.0 x 1.5 mm flange on the outer face (face within -0.08 to +2.02 mm under it), a 6.4 mm hole. The bushing passes 4.5 mm of plate and leaves 4.0 mm for the nut (nut thickness from the NKK drawing at the first fit); 42 mm are free behind the plug for the 13 mm body and its lugs. body_back itself is not changed.

## 7. Anticipated (no track covers them yet)

1. Part paths: the cast checks tools, not whether each part can move into place past the others (the centre servo into trunk_top after trunk_bottom is on; the hip yaw horns through trunk_bottom). Check: a swept insertion test per part, or the TEST_PLAN 1.4 dry fit in BUILD_ORDER order.
2. Hand torque on the 25 mm bit (6 screws into PA case pilots and the head). Check: drive one on the TO1 servo and on coupon C4.
3. Pilot wear on the service parts: the 4 lid screws self-tap into printed pilots and come out at every battery service. Check: 5 drive cycles on a printed pilot coupon.
4. VHB cure: 3M's strength comes with dwell time; a fall in the first day loads green tape. Check: no falls (no walking) for 24 h after taping; a tape pull coupon at 24 h.
5. The body_back pull adds a moving seam that track 4 does not model. Check: add the 20 mm pull to track 4's cable model.
6. Loctite 243 on the metal horn screws (assembly guide) must cure before the next part hides them. Check: cure time in the TEST_PLAN dry run.
