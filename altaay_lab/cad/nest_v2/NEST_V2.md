# Nest mat, version 2

2026-11-12 ET. Design study and CAD. Nothing was built, bought, or run on hardware. DECISIONS.md was not edited. The older nest CAD, the flush study, the charger board, and the sim folders were read and not changed.

Every number is marked **sim pass only**, **CAD check only**, **calc only**, or **cited**. A sim is not a hardware dock rate. If a number has none of those, it is a **BLOCKER**.

## The pick

**A flat felt mat with a flush striped contact field.** The duck sits the cute sit (D59), torque off, head up, facing the room. Five gold wells sit flush in the seat. Nothing sticks out of the duck. The feet stay plain. The camera finds the nest. Springs are not on the duck, and they are not a field of pins under the felt.

This is the flush-contact layout already drawn (five 3 mm wells, 20 mm conductor, 5 mm felt gap, seat centre inside +/-254 mm along the wall and +/-161 mm deep). The mat edge is the two 1 mm steps from the nest sim, at the same stations (247 mm and 267 mm from the sun). The sun stays 190 mm from the wall. The charger stays the MCP73213 board already drawn for the 2S P45B pack. The mat is a gated supply into that board.

The other four lose on the landing spread, on power, or on part count. The table is below.

## What was reused

- The sit, the recorded pose, and the body meshes (twin/sit/sit_pose.json, the URDF, print/).
- The flush field rule (twin/dock/flush/draw_flush.py): stripe 20 mm, gap 5 mm, wells at y = -24, -12, 0, +12, +24 mm.
- The nest frame and the two-step edge (twin/dock/nest/cad/nestcad_lib.py and the nest sim v3).
- The STEP writer (twin/dock/nest/cad/step_export.py).
- The stored 540-seed runs. No new physics run. score_seats.py only reads them.
- The in-body charger (circuitry/CHARGER_BOARD.md) and the awake-while-docked split (D50, D61).
- Mill-Max 0906 and the EDAC magnetic series, as already read in the flush study, plus one DigiKey price page for the Mill-Max pin (BOM.md).

## Comparison

Landing spread the contacts have to live with (sim pass only, the stored seats, calc only for the radius test):

| | Blind walk, PR 45 | 40 mm wall card, PR 47 | True pose, nest sim v3 |
|---|---|---|---|
| Runs, falls | 540, 0 falls | 540, 1 fall | 540, 0 falls |
| Seat in the stripe box, first sit | 380 | 533 | 540 |
| Same, within 3 sits | 383 | 533 | 540 |
| Old sun and ring pins, first sit | 35 | 501 | 531 |
| Seat centre within 45 mm | 26 | 493 | 518 |
| Within 16.5 mm (largest magnetic housing) | 5 | 206 | 235 |
| Within 10 mm (phone-coil offset in the nest study) | 3 | 83 | 110 |
| Within 8.25 mm (half that housing) | 2 | 54 | 73 |
| Radial median / 95th, mm | 129.7 / 310.7 | 20.4 / 62.5 | 18.4 / 42.9 |

The stripe phase of this CAD matches the box on the two files that stored a heading: 380 and 540. Heading stayed inside 46 deg (max 44.8 deg blind, 15.4 deg true pose). The card file did not store a heading, so the phase test is not claimed on it. The box count is the one that file supports.

| | (a) Striped felt, this pick | (b) Magnetic pads | (c) Qi or other inductive | (d) Low cradle or wedge | (e) Springs in the mat only |
|---|---|---|---|---|---|
| Look | A low striped rug. No pins on the duck. Renders in renders/. | A connector face in the belly, 16.5 mm at most. | Nothing to see, if the coil fits. | A guide the duck has to step into. Reads as a station. | Hidden under felt, so the duck looks clean. The mat is a pin field or a small target. |
| Alignment vs the spread | The box holds 380 of 540 blind and 533 of 540 with the card. | 16.5 mm holds 5 of 540 blind and 206 of 540 with the card, and that 16.5 mm is the housing, not a published capture. | 10 mm holds 3 and 83. | A 2 mm wedge does not slide the foot. A tall guide is a step the walk trips on. | A 45 mm cluster holds 26 blind and 493 with the card. A field of pins that matches (a) is about 45,000 pins. |
| Charge current | The contacts carry 2.0 A typical and 2.8 A peak (calc only, the stripe study). The chip charges at 1.00 A (cited, charger board). | EDAC sheet: 2 A or 5 A codes, 30 milliohm (cited, flush study). One face does not cover the miss. | STWLC38: up to 15 W, 4 V to 12 V out (cited). Qi2 is 15 W, Qi2 25W is the July 2025 step (cited, WPC). | Same contacts as whatever sits in the cradle. The cradle does not make current. | Mill-Max 0906: 2 A continuous, 3 A peak (cited, flush study). One pin is on the 2 A line with no margin. |
| Heat | Chip: 2.30 W at a 7.2 V pack and 3.50 W at 6.0 V, if the current stays 1.00 A at 9.5 V in (calc only, charger board). Bus copper is under 0.2 W (calc only, below). Contact resistance is BLOCKER. | 30 milliohm at 2.0 A is 0.12 W for two contacts in series (calc only, from the cited 30 milliohm). | No efficiency percent on the WPC page or the ST brief. Belly heat is BLOCKER. The old coil study assumed losses; this file does not reuse that guess as a datasheet. | No new heat. | 20 milliohm at 2.0 A is 0.08 W per pin (calc only, cited resistance, clean lab). Dirt is not that number. |
| Safety | Stripes are gated by the signature already in D61. Once the field is on, a coin can bridge the 5 mm gap. That is an open BLOCKER. Belly diodes for either-polarity wells are not chosen yet. | Live metal is the connector, not a rug. Capture still fails. | Qi senders have foreign-object detection (the nest study). A phone coil still does not cover the miss. | A cradle does not remove a live contact. It adds a step. | Pins under felt stay dark until pressed. The count that would cover the box is not a thing to build. A few pins at the sun leave the same coin question on a small pad. |
| Wear | No cycle rating for foil on felt. BLOCKER. 3,650 mates in 10 years at one dock a day (calc only). | Up to 30,000 mates (cited). | No mate cycle. Coil life was not on the pages opened. BLOCKER. | The walk, not the dock, wears a guide. | 100,000 to 1,000,000 cycles, clean, mid stroke (cited). Not dust. |
| Parts | 2 felt sheets, 23 foil stripes on 2 buses, 5 wells, a cord pocket, the existing charger. | One pair fails the spread. A grid at 16.5 mm over 560 by 360 mm is about 748 housings (calc only). | A coil, a shield, a receiver, and a pad thicker than the walk wants. | A printed or felt guide, plus a contact method. | About 45,000 pins for a point tip on a 2.12 mm grid over that field (calc only). |
| Cost | Dollar figures for felt and foil were not opened. BLOCKER. The pin-field price that was opened is in BOM.md, and it is the reason (e) loses. | Housing price not opened. BLOCKER. Hundreds of housings. | Module prices in the old nest study were index, not re-opened. BLOCKER. | Not priced. BLOCKER. | BOM.md. Tens of thousands of USD at the opened pin price (calc only). |
| Print and build | Two felt cuts, foil in the top sheet, one small printed pocket, five wells in the seat. No new screw. | Each housing is a bought part. The belly still needs a recess per pad. | The coil stack is 3 to 6 mm in the old study. A printed pocket does not fix the thickness. | Easy to print, hard to walk onto if it is tall enough to guide. | Not a print. It is a pin machine. |
| Seamlessness, 1 to 5 | 4 | 2 | 2 | 2 | 2 |

Seamlessness is in the next section. 5 would be place the mat and forget it, including a coin on the rug and a fault the duck can explain. (a) is not a 5.

## Why the others lose

**(b) Magnetic flush pads.** The EDAC 685 and 686 sheet, as read in the flush study, lists round housings from 5.5 mm to 16.5 mm, says the magnet pulls the halves together, and does not give a capture distance. A 16.5 mm face cannot cover a median blind miss of 130 mm, or the card run's 95th of 62.5 mm. Granting the whole housing as a hit, which the sheet does not, still leaves 206 of 540 on the card run and 5 of 540 blind. A magnet that seats a phone will not drag this duck across that gap. The duck in the sit model is 2.8078 kg (sim pass only, the flush study).

**(c) Inductive.** Wireless Power Consortium, Qi wireless charging page, opened 2026-11-12: Qi2 is 15 W with magnetic alignment for phones; Qi v2.2.1, branded Qi2 25W, launched in July 2025, and the page says it is nearly 70 percent more power than Qi2. ST data brief DB5568, STWLC38JRM, 11 June 2025: up to 15 W, output programmable from 4 V to 12 V, package 2.12 mm by 3.32 mm by 0.56 mm. No efficiency percent and no millimetre of alignment on either page.

The nest study's awake-while-docked total is 13.6 W to 17.4 W typical and 24.6 W peak (calc only, NATURAL_DOCK_IDEAS.md section 4.2). A 15 W receiver is under the typical line once any loss is allowed, and under the peak. 25 W before loss sits near the peak. What arrives after loss is BLOCKER. The same study's air-core table puts a phone-size coil at about 10 mm for 70 percent of centred coupling (calc only, section 4.3). That 10 mm window holds 3 of 540 blind seats and 83 of 540 card seats. The walk crossed a 2 mm mat 6 of 6 times, a 3 mm mat 5 of 6, and a 7 mm mat 0 of 6 (sim pass only, cited in D61). A coil pad of 3 mm to 6 mm, the thickness in that study, is in the trip range.

**(d) A low cradle or wedge.** A 2 mm rise over 20 mm is a 5.7 deg slope. One sole at 13.6 N (sim pass only, flush study) gives a sideways push of about 1.4 N. Friction at 0.6 on that sole is about 8 N (calc only). The foot does not slide, so a low wedge does not guide. A guide tall enough to correct tens of millimetres is a step. The same edge sims say 3 mm already drops a crossing and 7 mm stops them. A new cradle sim was not run. BLOCKER for a dock rate. It also looks like a station, which is the shape the nest was chosen to avoid.

**(e) Springs in the mat only.** Mill-Max 0906, as read in the flush study: stroke 0.99 mm, so the body can sit in a pocket under 2 mm of felt with the tip level. 2 A continuous, 3 A peak, 20 milliohm, 100,000 to 1,000,000 cycles. The tip diameter was not in that extract. BLOCKER for the tip. For a point tip, a 3 mm well hits a pin only if the grid is about 2.12 mm or finer. Over a 560 mm by 360 mm field that is about 45,000 pins (calc only). DigiKey's page for 0906-0-15-20-76-14-11-0, opened 2026-11-12, lists 0.86 USD at quantity 1 (BOM.md). That field is not a mat. A handful of pins at the sun is the old small target: 26 of 540 blind, 493 of 540 with the card. The bumper still hangs clear (3.36 mm above this felt in the posed sit, CAD check only; 2.9 mm in the flush study, sim pass only), so both poles have to be on the seat, and a fixed pair on that small patch does not forgive a 40 mm miss.

## This mat

Nest frame, as the nest CAD: sun at the origin, x toward the wall, wall face at x = 190 mm.

- Lower felt, 1 mm, from x = -267 mm, 20 mm past the upper sheet on the front and the sides.
- Upper felt, 1 mm, from x = -247 mm to x = 184 mm (6 mm short of the wall). Walking surface 2.00 mm (CAD check only).
- 23 foil stripes, 20 mm, with 5 mm felt gaps, flush with the felt (z max 2.000 mm, CAD check only). Even periods are plus, odd periods are minus, the same rule as the flush study. 11 plus, 12 minus. Both poles run from x = -180 mm to x = 180 mm, so a well at the back of the window still lands on foil (CAD check only). The hidden bus link does not end a stripe early.
- Two foil buses between the felt layers at the wall end. Plus and minus do not share a volume (the polarity check passed, CAD check only).
- Cord pocket off the field, at the left end, clear 78 mm by 32 mm by 21 mm, which holds the 70 mm by 26 mm by 14 mm board the older nest CAD kept room for (CAD check only). One 8 mm hole, the jack exit. No screws. D39: the hole has a job. D42: there is no screw pattern to break.
- 40 mm card, 1 mm thick, on the wall, centre 350 mm up. This is the mark from the close-up study. It is still a mark. Ahmed has not approved it. The mat scores 380 of 540 without it.
- Five gold wells, 3 mm, 12 mm apart, in the seat. In the render they sit in pockets on the contact face. print/sit_seat.stl was not changed.

The posed sit (sim pass only for the pose, CAD check only for the placement) puts the seat's lowest point on the felt. The soles land 0.3 mm into the felt. The bumper is 3.36 mm above it. Trunk pitch in the pose file is 2.79 deg. No pin stands out of the duck.

Copper drop, calc only, from the 52.96 milliohm per metre already used for 22 AWG: 0.36 m of that wire is 0.019 ohm. Plus and minus are 0.038 ohm. At 2.0 A that is 0.076 V and 0.15 W. The charger board's window is above 8.70 V and at or under 10.0 V (cited, from the chip sheet). From the D61 9.5 V figure, 2.0 A can drop 0.40 ohm before the chip input is 8.70 V (calc only). The wire is inside that. Two contacts at the old 50 milliohm bench mark (not run) add 0.10 ohm, still inside. The real contact resistance on foil, with dust, is BLOCKER.

Files: nest_v2.py, stl/, step/, checks.json, renders/. All eight STEP volumes match the meshes (CAD check only). Each file is under 5 MB.

Renders, looked at before they were kept:

- renders/sit_three_quarter.png
- renders/sit_side.png
- renders/sit_front.png
- renders/mat_top.png
- renders/belly.png

## For the human and for an operator

Place the mat against the wall. That is the setup. The 40 mm card is a second stick, at 350 mm on the centre line, and it is what takes the first sit from 380 of 540 to 533 of 540 (sim pass only). Without the card the mat still charges a blind first sit in 380 of 540. With a true pose the same box holds 540 of 540, so the window is not the limit when the duck can see.

Finding is the camera walk already scored. The duck turns until the target is in the field, then walks at the speed it measured. After the turn the sit is blind (camera twin). Re-sits add 3 seats on the blind run (380 to 383) and none on the card run.

If the mat is moved, the same search runs again. 12 of 540 blind runs never see the target and do not sit (sim pass only, the blind report). The duck should stop there, not keep walking. That stop is the behavior, not a new sim. If the mat is blocked, the camera never gets the target, and the same stop applies.

Status uses parts already in the duck. The charger STAT pin is low while charging and high otherwise (cited, charger board, from the chip sheet). Type 1 does not flash, so one pin cannot say full from fault. The Pi uses pack voltage and time, as that board note already says. The eyes are the warm white beads (D33). The speaker is already there. A glow while STAT is low, and a short sound when the seat first connects, are behavior on those parts. No new lamp.

Low battery is already first and second in the arbiter: safety, then dock (D56), with the voltage stops in D16. Go-home is this walk. Nothing new is claimed for the policy.

A fault (STAT high, pack not rising) is not fixed by sitting again in the same bad spot. The blind re-sits barely move the count. The duck stands off, tries one more approach, then stops and holds the eyes steady. That sequence was not simulated. BLOCKER for a fault rate.

An operator fleet-checks the report the Pi already owes: pack voltage, current, and cell temperature (CHARGE_INTERFACE.md). No new radio. A duck that has not finished inside the 6 hour timer, or whose cells leave 0 C to 60 C, is the one to look at. The timer and the cell window are the charger board's (cited).

## Where home charging is heading, and whether this scales

Phone charging is moving to Qi2 and Qi2 25W (cited, WPC, above). The magnetic part of Qi2 is there to seat a phone, not this duck (2.8078 kg in the sit model, sim pass only), and the page does not give a pull force. BLOCKER for that force. The consortium's other public standard on the same page is Ki, for cordless kitchen appliances. The page does not give a watt figure for Ki. BLOCKER for that number.

Robot vacuums in the house charge from contacts on a base. This study did not open a vacuum service manual, so a watt figure for them is BLOCKER. The pattern that matters here is the one already in this repo: contacts, a gated supply, and the charger in the machine that holds the pack. Robot pets that sit on a pad have the same problem as (c) when the coil is phone-sized: the sitter has to be placed, or the coil has to be huge. The nest study already scored that and did not take it.

Does (a) scale?

- Faster charge. The P45B standard charge is 4.5 A (cited, the cell sheet, via the charger board). 4.5 A at 8.4 V is 37.8 W into the pack (calc only), plus the duck's load. Qi2 25W does not cover that. The MCP73213 stays the 1.00 A linear chip already designed. A faster charge is a switching charger, which the dock notes already considered, fed by these same two buses. The foil can be wider. The mat does not have to change shape.
- A bigger pack at the same 8.4 V is more current on the same two rails. The contact window does not shrink. The copper and the fuse do have to be checked again. BLOCKER until that current is chosen.
- A later model with the same sit uses the same mat. The window is already the large one. A second duck on one mat is not designed. BLOCKER.
- Inductive gets more interesting if a standard publishes both the power (past the duck's peak, not just 15 W) and an alignment of tens of millimetres. Neither number is on the pages opened here. Until then, coils stay the wrong tool for this landing spread.

## Open BLOCKERS

1. Contact resistance of the gold wells on the foil, with dust, hair, and felt. The 50 milliohm mark is not a measurement.
2. The signature gate board. The pocket fits the old 70 by 26 by 14 mm keep-out. The board is not designed. While the field is on, a coin can bridge a 5 mm gap.
3. Steering diodes in the belly, so a well on either stripe still feeds the charger the right way. The part is not chosen. The charger board expects fixed plus and minus.
4. Chip heat at 2.30 W and 3.50 W. The thermal twin ran 1.9 W and 3.2 W (sim pass only) and was not re-run.
5. A real camera detector, light, and the entrance pupil. The sims use a pose plus noise while a point is inside a cone.
6. The card as a solid. The card run used a point 4 mm off the wall, not a 1 mm plate, and it did not store a wall gap. Clearance of this plate is not a sim.
7. Felt compression under the seat's 0.88 N (sim pass only, flush study). A foil even 0.2 mm low may not meet the gold.
8. Wear life of foil against gold. No cycle rating was opened.
9. Dollar figures for felt, foil, and the magnetic housings. The one opened price is in BOM.md.
10. Heading on the card run, so the stripe phase is not scored on that file. The box count is.
11. A cradle, a coil, or a pin field was not given a new physics run. The scores above are the stored seats tested against each window.

Nothing here is a hardware pass.
