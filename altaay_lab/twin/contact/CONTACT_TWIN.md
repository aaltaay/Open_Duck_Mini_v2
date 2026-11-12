# Contact twin: four spring pins on cloth over felt

2026-11-11. Arithmetic and cited sheets only. No MuJoCo run, no hardware. The nest sequence sims, the nest CAD, and the sit study are used as they stand. This file does not replace them.

Labels: **cited** (a page opened for this twin), **calc only** (arithmetic on those pages or on numbers already in the repo), **sim pass only** (a MuJoCo result already reported), **CAD check only** (a mesh measurement already reported). Anything without one of those is **BLOCKER**.

Run `python3 ct_model.py` in this folder. It writes `results.json`. `python3 -m unittest test_ct_model.py` checks the arithmetic.

## 1. The pin that was read

The nest CAD names a QA Technology 100-40 series probe, standard spring, in a 100-SDN250S solder cup socket. The catalog was opened for this twin: https://www.qatech.com/downloads/100-40_Catalog.pdf

Cited from that catalog:

| Item | Value |
|---|---|
| Full stroke | 10.16 mm |
| Working stroke where the spring force is stated | 8.05 mm |
| Spring S, preload | 1.5 oz, 0.42 N |
| Spring S at 8.05 mm | 5.7 oz, 1.58 N |
| Spring S life at 8.05 mm | 500,000 cycles, in the socket |
| Spring S ounce table | 1.5, 2.8, 4.1, 5.4, 6.5 oz at 0, 2.54, 5.08, 7.62, 10.16 mm |
| Tube P | nickel silver, inside precious-metal clad, average resistance under 20 mOhm |
| Tube P current cell | 10.2 (14.3). The header pairs 120 C and 204 C. Footnote 4: with lubrication the range is -55 C to 120 C. This twin uses 10.2 A at 120 C and does not assign the 14.3. |
| Plunger | heat treated BeCu, gold plated over nickel |
| Tip 40 round | diameter 0.91 mm, radius 0.46 mm |
| Socket 100-SDN250S | drawn on the same page, solder cup |
| Mounting hole | 1.702 to 1.753 mm, drill 1.75 mm, in FR4 or the same class. Not a printed hole. |

Footnote 1 says the current rating depends on the spring and the lubrication, and points at an application note. That note was not opened. A derate below 10.2 A is **BLOCKER**. The highest contact current in section 3 is 2.8 A, which is under the printed 10.2 A.

Tip 30 round is named on the same page. This text extract did not recover its diameter, so every pressure below uses tip 40. The 2.3 mm head drawn in the nest CAD is not on this page (already recorded in PARTS_AUDIT.md). The orderable string is still open: tube letter, tip code, spring letter, options. The pieces read here are tube P, tip 40, spring S, and socket 100-SDN250S.

The 500,000 cycles are the probe in its socket at 8.05 mm. They are not cloth life. TEST_PLAN.md 20.4 already says that.

## 2. Contact force at the sitting weight

The force is the spring force at the stroke the sit actually holds. It is not the duck's weight divided by four.

The catalog ounce table, converted at the catalog's own 0.42 N per 1.5 oz and read between the printed points (**calc only**):

| Stroke | Where it comes from | Force |
|---|---|---|
| 3.0 mm | seat pins, design proud (nest CAD) | 0.85 N |
| 2.98 mm | seat pins, plane sit, mean (sim pass only) | 0.85 N |
| 4.55 mm | bumper pins, plane sit, mean (sim pass only) | 1.07 N |
| 4.27 mm | bumper pins, plane sit, least mean (sim pass only) | 1.03 N |
| 3.14 mm | bumper pins, height-field sit, mean (sim pass only) | 0.87 N |
| 1.85 mm | least single bumper pin, height-field sit (sim pass only) | 0.69 N |
| 7.5 mm | bumper pressed flush, the CAD stop | 1.49 N |

The two-point line the nest CAD used (0.42 N to 1.58 N at 8.05 mm) is within 0.01 N of this table at every row above (**calc only**). At the catalog's own 8.05 mm point the ounce table interpolates to 1.56 N against the printed 1.58 N.

Sitting weight, sit model 2.8078 kg (twin/sit/SIT.md) at 9.81 m/s2: **27.5 N (calc only)**. The 11 plane sits with these pins (twin/dock/nest/cad/pins_sit_check.json, **sim pass only**, mean) add up as:

| Support | Force | Share of 27.5 N |
|---|---|---|
| Both soles | 22.85 N | 83 % |
| Four pins together | 3.85 N | 14 % |
| Seat block still on the felt | 0.85 N | 3 % |

The three supports sum to 27.55 N (**calc only**). The bumper face is not in that sum: it is 2.95 mm off the felt on the plane (2.69 to 3.23 mm) and 4.36 mm off on the height field (3.13 to 5.57 mm), **sim pass only**. The bumper pins carry the front pin load alone.

What that means:

- The seat pins sit at their 3 mm proud stroke, about 0.85 N each, and the seat block still has 0.85 N on the felt. They are not holding the rear in the air. The older assumed pins (about 1.4 N each) did lift the seat block, because two of them pushed more than the seat's 0.9 N (NEST_SIM.md section 2.7, **sim pass only**). These catalog springs do not, in the 11 sits.
- All 8 loaded joints stayed on their stops in those 11 sits, and all 4 pins touched, on both mat models (**sim pass only**).
- A flush bumper strokes the pin 7.5 mm and leaves 2.66 mm of the 10.16 mm stroke (**calc only**). That 2.66 mm is the same remainder the nest CAD already has.

The height-field bumper gap is the fragile one, and it is already in the nest CAD: on a rigid mat the least bumper pin is still 1.85 mm into its stroke, 0.69 N, above the 0.42 N preload (**sim pass only** for the 1.85 mm, **calc only** for the 0.69 N). A local dent in the felt does not add stroke. The sit check defines compression as proud length minus the distance down to the contact surface (`comp = Lp - s` in pins_sit_check.py). The soles and the seat hold the body, so the tip reaches farther into a dent and the spring unloads by that depth. Section 5. A full 2.0 mm dent on this 1.85 mm pin opens the contact. Bottoming the spring is not the risk.

## 3. Resistance, drop, and heat

Three terms, kept separate so they are not added twice.

**Probe, cited.** Tube P average resistance is under 20 mOhm. That is the plunger-to-tube path. The catalog does not give it against force.

**Metal spot, cited at one force, scaled.** A connector fretting paper (gold-flashed palladium-nickel on itself, normal load 1 N, wipe ±25 um at 10 Hz) measured 3.1 mOhm at 1 cycle, 10.2 mOhm at 1,000 cycles, and 5,050 mOhm at 10,000 cycles: https://centralesupelec.hal.science/hal-03329833/document . That is not cloth, and a fretting cycle is not a dock. Plastic constriction scales as 1/sqrt(F). Anchored at the cited 3.1 mOhm at 1 N (**calc only**):

| Force | Metal-spot floor |
|---|---|
| 0.69 N (least bumper pin) | 3.7 mOhm |
| 0.85 N (seat pin) | 3.4 mOhm |
| 1.07 N (plane bumper pin) | 3.0 mOhm |
| 1.49 N (flush bumper) | 2.5 mOhm |

Across the whole sit the metal floor moves by about 1 mOhm. Pure gold resistivity is 22.14 nOhm m at 20 C (Wikipedia, gold, opened). Plating hardness was not opened, so a Holm spot from that resistivity is **BLOCKER** and is not used. The metal floor is not added on top of the 20 mOhm probe figure. It shows that force, in the range this sit uses, does not move a clean metal contact.

**Cloth sheet, cited ceiling, path is calc only.** Laird Flectron 3035-535 Ni/Cu polyester taffeta, the class the nest CAD already named: thickness 0.09 to 0.11 mm, surface resistivity under 0.07 ohm per square (Marian copy of the Laird sheet, opened). The sheet does not say the cloth is gold coloured. A gold or pale-gold colour is **BLOCKER** for the part number. There is no through-thickness number, and the foil adhesive under the sun was not opened, so the sun's through-path is **BLOCKER**.

A full-ring return from a 0.455 mm radius spot, at 0.07 ohm per square (**calc only**): 0.052 ohm at 50 mm, 0.060 ohm at 100 mm, 0.068 ohm at 200 mm. The working number below is 0.060 ohm at 100 mm. A narrow tab can crowd the current and land higher. That crowding is **BLOCKER**. The nest CAD's earlier "about 0.10 ohm" on the ring is the same order. This is not a tighter measurement, and it is not a ceiling.

Loop used below, **calc only**: each live pin adds 20 mOhm, the ring sheet is 0.060 ohm split across the live minus pins as if the paths did not share a tab, and the sun through-path is taken as 0 because the foil is the design intent. If the foil does not short the cloth, add the no-foil sun term, 0.052 ohm out to the 50 mm rim (**calc only**), on top.

Currents already in the studies, not re-derived: 1.0 A charge (D61; the MCP73213 sheet was not opened), 2.0 A typical and 2.8 A peak while the duck is awake on the dock (twin/dock/nest/stripes/STRIPE_MAT_STUDY.md, **calc only** there).

| Who is touching | Loop at 1.0 A | Loop at 2.0 A | Loop at 2.8 A | Still charges |
|---|---|---|---|---|
| All 4 | 0.050 ohm, 0.050 V, 0.050 W | 0.10 V, 0.20 W | 0.14 V, 0.39 W | yes |
| 1 plus pin misses | 0.060 ohm, 0.060 V, 0.060 W | 0.12 V, 0.24 W | 0.17 V, 0.47 W | yes, that plus pin carries all of the current |
| 1 minus pin misses | 0.090 ohm, 0.090 V, 0.090 W | 0.18 V, 0.36 W | 0.25 V, 0.71 W | yes, and the cloth path is no longer split |
| 1 of each pole misses | 0.100 ohm, 0.100 V, 0.100 W | 0.20 V, 0.40 W | 0.28 V, 0.78 W | yes, each remaining pin carries the full current |
| Both plus, or both minus | open | open | open | no |
| Any 3 pins miss | open | open | open | no |

Heat in one probe at 2.8 A through 20 mOhm is 0.16 W (**calc only**). The cloth term is the larger share: 0.47 W in the unsplit ring path at 2.8 A. The charger heat already on the books is 1.9 W to 3.2 W in the trunk (D61, **calc only**). On this working loop the contacts are the smaller heat. A cloth temperature is **BLOCKER**: no thermal resistance of the stack was opened.

TEST_PLAN.md 20.1's pass line is 0.15 ohm for the two-pin loop at 1.0 A. The working calc is 0.050 ohm with four pins and 0.100 ohm with one of each pole, so it sits under that line. Tab crowding, a real cloth interface, and a sun path that is not a short can eat the margin. The line is a bench pass, not a result of this file.

## 4. What a missed pin does, from the landing window

Pins: plus pair in the seat, minus pair in the bumper, 20 mm apart, pairs 130 mm apart. Sun radius 50 mm, felt gap 32 mm, ring from 82 mm to 235 mm, a pin counts 3 mm inside its zone. Same dimensions as the nest CAD. Heading 0 faces the room, so the seat is the end nearer the wall. Full annulus: no wall cut and no notch. **Calc only.** The nest CAD coverage, which has the cut, reported wrong-pole share 0. This section does not replace that.

The metal of one pair cannot bridge the gap. Centers 20 mm apart, tip diameter 0.91 mm, so the metal span is 19.1 mm against a 32 mm gap (**calc only**). One pair on both cloths at once, which would short the mat through that pair's wire, does not fit.

Heading 0, seat center moved off the sun:

| Shift | Pins | Charge |
|---|---|---|
| Lateral, up to 37 mm | all 4 counted | yes |
| Lateral, 38 mm to 57 mm | 1 plus pin off the sun, both minus pins still on the ring | yes, one plus pin carries the whole plus current |
| Lateral, 58 mm and out | both plus pins off | no |
| Toward the wall, up to 45 mm | all 4 | yes |
| Toward the wall, 46 mm | both bumper pins leave the inner edge of the ring together (radius 85.6 mm at the 45 mm step) | no |
| Away from the wall, up to 45 mm | all 4 | yes |
| Away from the wall, 46 mm | both seat pins leave the counted sun together | no |

The 45 mm radial window is the same 45 mm the nest CAD already states, and the bumper radius 85.6 mm at that edge is the same 85.6 mm in the CAD. The all-four lateral band here is 37 mm. The CAD's all-four window is 36 mm. This is the plain annulus; theirs includes the cut.

A 5 mm by 15 degree grid over ±80 mm and a full turn (calc only, not a landing distribution) found the same electrical rule: every cell with 1 pin missing still charged, every cell with 3 missing was open, and a 2-miss cell charged only when the two missing pins were one from each pole.

The sims already counted the landings (**sim pass only**, twin/dock/nest/sim/v2/NEST_SIM_V2.md section 3). They are not re-run here.

| | Steering walk-on | Straight crossing |
|---|---|---|
| Seat pins inside 45 mm | 97.1 % | 81.0 % |
| Sideways scatter, 1 sigma, all runs | 22.3 mm | 36.1 mm |
| 95th radial miss | 37.3 mm | 82.8 mm |
| First sits that miss | 8 of 511 (5 seat off the sun, 2 wrong zone, 1 bumper not touching) | 71 (52 wrong zone, 19 seat off the sun) |

Read with the table above: a landing inside 45 mm radial, and inside about 37 mm sideways, keeps all four pins and the 0.050 ohm loop. A sideways miss between 38 mm and 57 mm drops one plus pin, the loop goes to 0.060 ohm, and that pin carries the whole plus current (0.47 W in the loop at 2.8 A, **calc only**). Past 45 mm toward or away from the wall, or past 57 mm sideways, a whole pole is gone and the charge is open. There is no heat in an open loop. The straight crossing's 95th radial miss, 82.8 mm, is in that open region. The steering 95th, 37.3 mm, is still on the all-four side of this map. That is why the straight crossing's 71 misses and the steering run's 8 misses are the numbers to keep. This file does not produce a new miss rate.

## 5. Felt under the pin, cloth wear, traction

**Pressure, calc only, on cited tip and cited grades.** Tip 40 at the 0.85 N seat force: face area 0.65 mm2, 1.31 MPa, 190 psi. US Felt's SAE table (https://www.usfelt.com/sae_felt_specs.html, opened) gives the pressure for 10 % deflection: F-1 and F-2 at 21 psi, F-3 at 13 psi, F-5 and F-7 at 6 psi, F-10 and F-11 at 4 psi, down to F-26 at 1 psi. 190 psi is 9.0 times the F-1 pressure. Ten percent of the 2.0 mm nest stack is 0.2 mm. The dent is more than 0.2 mm. It cannot be more than the 2.0 mm stack unless the tip cuts through. The depth between those two is **BLOCKER**. The nest felt has no grade (PARTS_AUDIT.md), and the SAE rows are for a 1 inch basis weight, with F-50, F-51 and F-55 named only as the same grades under 1/8 inch. Which grade, and whether a 1 mm craft felt is any of them, is **BLOCKER**.

**What the dent does to the spring, calc only.** The dent is local. The tip face is 0.65 mm2. The seat block that shares the load is 80 mm wide (twin/sit/SIT.md). The body stays on the soles and the seat, and the pin extends into the hole. Spring compression after the dent is the rigid-mat compression minus the dent. Uniform sink of the whole mat would not change this, because the body would drop with the cloth. Only the dent relative to the felt under the feet and the seat does.

| Rigid-mat stroke | After a 0.2 mm dent | After a 2.0 mm dent |
|---|---|---|
| Seat, 3.0 mm, 0.85 N | 2.8 mm, still touching | 1.0 mm, 0.56 N, still touching |
| Bumper, plane mean 4.55 mm, 1.07 N | still touching | 2.55 mm, 0.79 N, still touching |
| Bumper, least height-field pin, 1.85 mm, 0.69 N | 1.65 mm, 0.66 N, still touching | open by 0.15 mm, force 0 |

The seat pins and the usual bumper pins stay in contact even if the felt dents the full 2.0 mm. The least bumper pin does not. It holds at the 0.2 mm edge and it lifts off if the dent is deeper than its 1.85 mm of rigid-mat compression. That depth is inside the unknown band, so whether this pin stays down is **BLOCKER**. If it lifts and its mate stays, the charge follows the "one minus pin misses" row in section 3 (0.090 ohm, still closed). The lowest pair average on the height field is 1.94 mm (**sim pass only**). A 2.0 mm dent is deeper than that average, so the worst of those sits can lose both bumper pins, and then the charge opens. Which of those two outcomes is real waits on the dent.

**Set.** Superior Felt's wool-felt sheet (opened) prints compression recovery 99 % for all wool felt type I, from -80 F to 200 F. That is their sheet's recovery, not a pin at 190 psi, and not a felt with no grade. If that 99 % were applied to a full 2.0 mm crush the leftover would be 0.02 mm (**calc only** on a condition the sheet does not state). The leftover under this pin is **BLOCKER**.

**Cloth life.** No abrasion count was on the Laird sheet. A Martindale paper on a Shieldex yarn was opened and is not this cloth and not a round tip, so its cycle counts are not used. The probe's 500,000 cycles are the socket. The fretting paper's 1,000 and 10,000 cycles are a 25 um wipe at 10 Hz. One dock is one sit: the pins meet the cloth at the sit and leave at the stand. During the walk the lowest pin tip is 77.4 mm off the floor (NEST_CAD.md check D, **CAD check only**), so the walk itself is not a pin rub. NEST_SIM.md puts the sit-down shift at about 1 mm (**sim pass only**), a short wipe, not a Martindale rub. How many docks until the cloth ohms rise is **BLOCKER**.

**Traction.** The friction page that was opened (Engineering Toolbox, friction coefficients) has no felt row and no TPU row. The nearest cited rows are not this mat: rubber on cardboard, static 0.5 to 0.8; rubber on dry concrete, kinetic 0.6 to 0.85; cotton thread on cotton thread, static 0.3. The nest sim swept mat friction 0.6, 0.8 and 1.0 and the fall counts on 180 runs were 12, 11 and 6, all edge trips (NEST_SIM.md, **sim pass only**). Those three numbers are controller inputs, not a measurement of felt. The floor geom in the nest harness defaults to 0.6. Whether the real mat slips under a TPU sole is **BLOCKER**. Coulomb friction does not care about area, so a worn cloth patch does not, by itself, change the grip. A glazed or wet patch can, and that is the same blocker.

## 6. Arc, hot plug, and a hand on the live cloth

Paschen's law, as stated on the page that was opened: the minimum breakdown in air at standard pressure is 327 V, at a gap of 7.5 um (https://en.wikipedia.org/wiki/Paschen%27s_law). The pack setpoint in D61 is 8.40 V. The mat supply in D61 is about 9.5 V (**calc only** there; the charger sheet was not opened, so 8.40 V is the decision's number). Those are 2.6 % and 2.9 % of 327 V (**calc only**). No air gap at atmospheric pressure breaks down below that minimum, so this voltage does not hold an arc while the duck sits down or stands up.

The make and the break are the sit and the stand, not the walking steps. The pins are 77.4 mm clear while walking (**CAD check only**). The intended order, already in TEST_PLAN.md 20.5 and in COMPLIANCE_FIRST_PASS.md, is: the mat stays at a small probe until the duck is recognised, and the supply opens when the duck lifts. If that order holds, the pins meet and leave an unpowered cloth. The probe voltage is not designed. **BLOCKER.**

If the supply is still on at 9.5 V during the lift, there is still no sustained air arc, for the same 327 V reason. A spark from stored energy needs the charger's input capacitance or the wiring inductance. Neither was opened. Spark energy is **BLOCKER**. What remains is I-squared-R in the spot while the spring unloads, bounded by the watts in section 3 if the resistance is the working loop, and unbounded if the cloth interface is worse than that loop. The coupon watches for a spark anyway.

Touch. The open cloth at about 9.5 V can source the 1.0 A to 2.8 A of section 3 into whatever bridges the sun and the ring. That current is the hazard. A body resistance from IEC 60479 was not opened, so the current through a person is **BLOCKER**. IEC 62368-1's text was not opened. Secondary pages name 60 V DC as an extra-low edge; the compliance note already marks that comparison uncertain, and this file does not turn 9.5 V into a pass. The 32 mm gap is wider than the 19.1 mm pin span and wider than a US quarter (24.26 mm, already in the nest notes). A hand can still span 32 mm, which is the case COMPLIANCE_FIRST_PASS.md already keeps: the supply stays off until the signature and the leak check pass, and it drops before the duck stands.

## 7. Proposed bench rows

These are not in TEST_PLAN.md. Section 20.1 to 20.4 already cover a first resistance reading, a snag pass, dirt, and 500 sits. The rows below are what would replace the blockers in this file. Nothing here is a pass until it is measured.

1. **Force against the catalog.** One tip 40 probe on the candidate cloth over two layers of the candidate felt. Four-wire ohms and a force reading at 0, 2.54, 5.08 and 7.62 mm of stroke. Pass on force: within 20 % of 0.42 N, 0.78 N, 1.15 N and 1.51 N (the catalog table, **calc only** at the printed ounce points). Write the ohms down. The 3.1 mOhm metal floor is not the pass line.
2. **The loop, including a lifted pin.** Four pins in the seat and bumper spacing, cloth and foil as drawn, 1.0 A and then 2.0 A. Then lift one plus pin, one minus pin, one of each, both of one pole, and three pins. Pass: four pins under 0.15 ohm at 1.0 A (the existing 20.1 line); one pin of a pair lifted still conducts and stays under 0.30 ohm at 1.0 A (the working calc is 0.060 to 0.090 ohm, so 0.30 ohm leaves room for the tab); both pins of one pole, or any three, read open. At 2.0 A for 5 minutes, write the cloth temperature. Fail on a hole, a scorch, or an open that the row says should conduct. There is no cloth temperature limit on a sheet opened here.
3. **Felt dent and leftover.** The same tip at 0.85 N and at 1.07 N, with the felt supported the way the block is supported, not floating under the tip alone. Measure the dent under the tip relative to the felt beside it, under the load and again after 1 hour. Pass for contact: the dent is under 1.85 mm, so the least bumper pin from the height-field sit still touches (that 1.85 mm is sim pass only, on a rigid mat). Fail: the dent is 1.85 mm or more, or the tip cuts the cloth. Write the leftover. Do not use 99 % recovery as the pass line until the felt is the wool that sheet covers.
4. **Wear, still without a life number.** TEST_PLAN.md 20.4's 500 sits, plus a four-wire reading every 50 sits. Pass: no hole, and the 20.1 loop still under 0.15 ohm at the end. That does not create a cycle life. A Martindale of the candidate cloth is worth doing if a rub tester is on hand. There is no cycle count in this file for it to match.
5. **Grip.** A TPU sole coupon and a 1 kg mass on the felt, and on the cloth, dry. Pull with a spring scale. mu is pull divided by weight. Write it down. No fail number: the sim's 0.6, 0.8 and 1.0 are not a material measurement.
6. **Make and break.** Supply at 9.5 V with a 2.0 A limit, in the dark, 20 lifts. Pass: no visible spark. Repeat with the supply switched on only after the pin is down and switched off before the lift. Pass: the meter shows the supply was off during the motion, and still no spark.
7. **The gap.** Two tips 20 mm apart on the real cloth edges, and a US quarter on the 32 mm gap. Pass: neither one connects plus to minus. This is the geometry of section 4 on the real cut.

## 8. What this does not close

- Tip 30's diameter, the full orderable probe string, and the spring-current application note.
- Gold or pale-gold cloth as a part number. The ohms above are the Ni/Cu taffeta ceiling, not a coloured cloth that was opened.
- Sun through-resistance, foil adhesive, and tab crowding. The 0.050 ohm loop is a working calc with those three left out.
- Felt grade, the dent between 0.2 mm and 2.0 mm, and whether that dent unloads the least bumper pin (1.85 mm of rigid-mat compression). The leftover after a pin crush.
- Cloth docks until the resistance rises. Pin-on-cloth ohms, as a measurement.
- Friction of this felt and this cloth under a TPU sole.
- Body current at 9.5 V, and any standard text that would clear or forbid the open cloth. The compliance note stands.
- Charger input capacitance, so hot-plug energy stays unknown. The 327 V comparison only rules out a sustained air arc.

The coupon in section 7 is the next measurement. The duck is not.
