# Belly contact

2026-11-16 ET. Simulation and arithmetic. Nothing was built, bought, or run on hardware. The mat in cad/nest_v2 was not changed. D61 was not edited. The gold-dome result, 38 of 40 charging, is SEAT_CONTACTS.md.

Every number is marked **sim pass only**, **calc only**, **CAD check only**, or **cited**. A sim is not a hardware dock. If a number has none of those, it is a **BLOCKER**.

## How it works

The duck sits the cute sit, torque off, on the flat felt mat. The mat stripes are unchanged: 20 mm of copper, a 5 mm felt gap, repeating every 25 mm along the wall. Even periods are plus, odd periods are minus.

The charging metal is not a gold dome. It is two small plates in the seat bottom, one on each side of the duck. Each plate is one electrical half. A bridge of ideal-diode controllers inside the duck sorts out which half landed on plus. When both plates are on copper, and each is pressed hard enough, the nest's 15 V reaches the BQ24133. When the duck is not on the mat, those controllers are off and the plates are held near ground. They do not sit at pack voltage.

The plates are flush with the CAD seat face (z = -66 mm, sit_cad.json, CAD check only). The plastic of that face is 0.9 mm higher in the dock model, so the plates are the low points and nothing sticks out past the CAD shell. The bumper is 3 mm lower than the seat in the body (CAD check only, z -69 mm against z -66 mm). Left alone it holds the seat off the mat, which is why the flush wells read 0 N. The bumper box in this model is raised 4 mm so the seat plates can touch. That raise is a duck-side trial. It is not a mat change.

## Why the whole belly cannot be the contact

The seat is 80 mm wide and the bumper is 60 mm wide (CAD check only). The stripes repeat every 25 mm. A conductive half 40 mm wide is wider than one period, so that half touches a plus stripe and a minus stripe at the same time (calc only). The short is in the metal, before any diode. The nest supply would be shorted through the shell.

The plates stay narrow in the stripe direction so they cannot do that.

The split line is the duck's centre plane, parallel to the stripes when the duck faces the room. The plate centres are 25 mm apart, one period, so they fall on opposite poles when both are on copper. The bare PETG between the inner edges is 22.8 mm (calc only, 25 minus 2.2). That is the insulation. The mat's 5 mm gap was not narrowed.

At a heading error the plates tilt across the stripes. The world span of a plate, the number that has to stay under the 5 mm gap:

| Heading | Print | Span across the stripes |
|---|---|---|
| 0 deg | nominal 6.0 by 2.2 mm | 2.20 mm (calc only) |
| 14 deg | nominal | 3.59 mm (calc only) |
| 20 deg | nominal | 4.12 mm (calc only) |
| 20 deg | 0.3 mm fat on each side | 4.50 mm (calc only) |

4.50 mm is under 5 mm, so the fat plate at the dock's 20 deg heading gate still cannot reach both poles.

Every phase in 0.25 mm steps, and every heading from -20 deg to 20 deg in 1 deg steps (4,100 poses, calc only):

| Size | One plate on plus and one on minus | Shorts |
|---|---|---|
| 6.0 by 2.2 mm | 2,663 of 4,100 (65.0 percent) | 0 |
| 0.3 mm fat (6.3 by 2.5 mm) | 2,609 of 4,100 (63.6 percent) | 0 |
| 0.3 mm thin | 2,727 of 4,100 (66.5 percent) | 0 |

The misses are the felt gap. Two plates locked one period apart sit in the gap together. A single point misses 5 mm of every 25 mm, which is 20 percent (calc only). These plates miss more because they have width. The five 3 mm wells, 12 mm apart, cover every phase up to 46 deg (calc only, FLUSH_CONTACTS.md). Two halves cannot copy that without putting both poles on one piece of metal.

Putting a second plate on the same half, 50 mm away, does not fill the gap. It is the same phase, so it misses when the first one misses (calc only).

## Material

The plates in the model are 6.0 mm along the stripe, 2.2 mm across it, and 0.5 mm thick. Two of them.

| Option | Resistivity | Wear and corrosion | This duck |
|---|---|---|---|
| 304 stainless, the pick | 72 microohm-cm at 20 C (cited, Upmet 304 datasheet). Density 7.90 g/cm3 (cited, Sandmeyer Alloy 304/304L sheet). | Good in fresh water under 100 ppm chloride. Pits above that, and not for seawater (cited, the same Sandmeyer sheet). No rub-cycle count against this foil was opened. | Bulk resistance of one plate is 27 microohm (calc only). Two are 55 microohm. At 1.006 A that is 0.06 mV. The contact, not the metal, sets the drop. |
| Nickel 200 | 9 microohm-cm at 20 C, density 8.9 g/cm3 (cited, VDM Nickel 200 data sheet, the 20 C row). | Hyndman Nickel 200 sheet: severe attack in oxidizing salt solutions. A wet bowl is that kind of salt. | Eight times less resistive than 304, and still microohms. Worse in a bowl. Not the pick. |
| Copper foil on the PETG | 1.72e-8 ohm-m on ETP copper at room temperature (cited, BNL technote on commercial copper, the ETP 110-O row). | The foil face oxidizes. No cycle count for foil rubbing felt was opened. That is the same BLOCKER as the stripes. | Same tape family as the mat. Fine as a stripe. A bad rubbing face. |
| Conductive coating | Sheet resistance was not opened. BLOCKER. | A paint film on a rubbing face wears through. No cycle count. BLOCKER. | Not the pick. |

304 is the pick because the ohms do not matter and a bowl is more likely than a lab bench. The wear life is still BLOCKER for every row.

Mass, calc only. Two plates are 0.104 g. The dock model also raises the seat box 0.9 mm and the bumper box 4 mm. On those boxes that is 10.21 g of PETG removed, so the net is about 10.1 g less. The CAD bumper is a 12 mm radius cylinder (sit_cad.py), so a real 4 mm cap is smaller than the box. 10.2 g is an upper bound, not a weighed part. The MuJoCo geoms are density 0, same as the seat boxes, so the walk mass is unchanged.

A sheet price for 304 was not opened. BLOCKER. Nothing was bought.

## The circuit

The nest is 15.0 V. The BQ24133 recommended input is 4.5 V to 17 V (cited, SLUSAF7D, and parts.yaml). PVCC absolute maximum is 20 V and AVCC is 30 V (cited, the same sheet). 15.0 V is inside the recommended window and under both absolute maxima.

Each belly half feeds one AC corner of a full-wave bridge. The bridge is four TI LM74610-Q1 controllers, each on an N-channel MOSFET, the CSD18532Q5B named in that controller's table 2. The bridge positive goes to the BQ24133 adapter node, in front of the ACFET. The bridge negative is duck ground. Two 10 k ohm bleeds, one from each half to duck ground, are the only DC path on a half when the bridge is off. They do not tie a half to the pack.

Checked against the sheets:

| Part | Limit that matters | This use |
|---|---|---|
| LM74610-Q1 | Cathode to anode up to 42 V recommended (cited, the recommended-conditions row). The TVS section of the same sheet calls -45 V the absolute maximum reverse, and uses 15 V as a typical reverse-battery example. Reverse leakage does not exceed 110 uA at a constant 13.5 V (cited, the feature text). Zero quiescent current, and the controller is not referenced to ground (cited, the product page). Body-diode drop must be at least 0.48 V before the charge pump starts (cited). The MOSFET is on about 98 percent of the cycle (cited). | 15 V forward is inside 42 V. 15 V reverse on an off leg is inside the -45 V line. The 110 uA figure is at 13.5 V, not 15 V. Leakage at exactly 15 V is BLOCKER. A 10 k bleed at 110 uA sits at 1.1 V (calc only), not at the 12.6 V pack. |
| CSD18532Q5B, table 2 of that sheet | 60 V, drain current 23 A at 25 C, 3.3 milliohm at 4.5 V gate, body diode 0.53 V at 2 A when hot (cited, the table as printed). | 15 V is under 60 V. 1.006 A is under 23 A. The controller's gate drive is up to 5 V (cited), so the 4.5 V resistance column is the one that applies. The diode voltage in the table is at 2 A and hot, not at 1.006 A and room temperature. That exact diode voltage is BLOCKER. 0.53 V is above the 0.48 V startup line, at the hotter, higher-current point. |
| BQ24133 | Input 4.5 V to 17 V. ACFET stays off until an adapter is detected, and the power path keeps the pack from rising onto the input (cited, SLUSAF7D and the TI product page). | The bridge output is the adapter node. With the ACFET off, the pack is not on that node, so it is not on the belly. |
| Pololu 5382, already DK2 | 4 V to 60 V, 10 A, on resistance under 10 milliohm, blocks current from output back to input (cited, the Pololu 5382 page). Weight 0.2 g. Price 3.79 USD at quantity 1 on that page. | Not used in the bridge. It needs at least 4 V on VIN and it has a ground pin, so it cannot be the low-side leg. A high-side-only pair with the other half tied to ground would short the nest when the duck sits the wrong way round. DK2 stays on the old chest record. |
| DK6, DK7 | Ideal diodes on the servo bus (netlist). | Not in this charge path. Not retasked. |

Drop in the two legs that carry the charge, calc only, from the cited 98 percent and the 3.3 milliohm and the 0.53 V: 0.0277 V at 1.006 A. The wire is another 0.038 ohm (NEST_V2.md, calc only). The plate bulk is 55 microohm (calc only). The contact ohms are still the gold-dust assumption from CAMERA_DOCK.md (5 milliohm at 10 g, scaling as 1 over square root of force, times 5). That assumption is not a measurement for steel on this foil.

On the 18 charging docks the chip input is 14.922 V to 14.928 V (sim pass only, with that assumption and the 0.0277 V). All of them are inside 4.5 V to 17 V.

The live netlist was not edited. DK2, DK6, and DK7 stay as written. The bridge is a proposed front end on the adapter node of the BQ24133 board. A harness built from wiring/netlist.yaml does not contain it yet.

### The five safety cases

**Duck turned 180 deg.** The two halves swap. The bridge still puts the higher half on the charger input and the lower half on ground. The chip does not see -15 V. An off MOSFET sees 15 V reverse, which the LM74610 sheet treats as inside the -45 V line.

**Both halves on one stripe.** No voltage between them. The bridge does not conduct. The lamp stays dark. There is no short.

**One half touching two stripes of the same pole.** Same-pole stripes are 50 mm apart, with the other pole between them (calc only). A plate whose span is at most 4.50 mm cannot reach the next same-pole stripe, and the sweep found 0 opposite-pole shorts. A plated half the width of the seat would fail this case. These plates do not.

**Belly on a metal bowl, off the mat.** The duck is not docked. The ACFET is off, the bridge MOSFETs are off, and the bleeds hold each half near ground. The bowl does not get pack voltage. A bowl set on the mat can still bridge the 5 mm gap. That is the gate board, which is still not designed (NEST_V2.md, blocker 2).

**A child touching the belly.** Off the mat, the plates are near ground, not at pack voltage. On the mat, the half that landed on plus is near 15 V, under the duck. The thing that should keep the field dark until the duck is seated is the gate board. It is still BLOCKER. The duck-side diodes do not make a live mat safe to touch.

## The 40 docks

Same seeds as the camera dock, run D policy, belly plates in the model, gold wells not in the model. Sim pass only.

Geometry (one plate fully on plus and one fully on minus, heading under 20 deg, still upright): 19 of 40.
Charging (that geometry, both poles at least 0.294 N, chip input inside 4.5 V to 17 V): 18 of 40.
Shorts: 0.
The gold domes on these seeds: 38 of 40 charging (sim pass only, the earlier batch). 18 is not 38.

The one geometric dock that does not charge is seed 13. Both plates are on copper, one presses 8.2 N, the other presses 0 N, so that pole is open. The lamp stays dark. That clip is belly_charge_fail.mp4.

Seed 32 never sees a mark, the same miss as the gold batch. Seeds 3, 25, 35, and 38 tip over. Those four stood and docked with the gold domes. Raising the bumper and standing on two small plates is a less steady sit in this model.

On a charging sit the lower pole is at least 0.77 N (seed 30) and the chip sees about 14.93 V. Contact loss, a plate on copper with under 0.294 N, is seed 13 and the tipped seed 3.

| Seed | Result | Time s | Yaw err deg | Charging | Pole force N | Chip V |
|---|---|---|---|---|---|---|
| 1 | docked | 25.1 | 5.0 | yes | 4.69, 7.29 | 14.927 |
| 2 | off the foil | 26.1 | 5.1 | no | 0, 0 | |
| 3 | fell | 19.5 | 158.7 | no | 0, 0 | |
| 4 | docked | 27.5 | 6.1 | yes | 7.07, 6.34 | 14.928 |
| 5 | gap | 25.6 | 9.5 | no | 0, 0 | |
| 6 | off the foil | 49.4 | 2.6 | no | 0, 0 | |
| 7 | gap | 26.2 | 10.4 | no | 0, 0 | |
| 8 | one plate off | 36.5 | 11.5 | no | 4.20, 0 | |
| 9 | docked | 37.0 | 3.5 | yes | 3.87, 6.33 | 14.927 |
| 10 | gap | 26.8 | 5.2 | no | 0, 0 | |
| 11 | gap | 46.2 | 8.5 | no | 0, 0 | |
| 12 | docked | 27.8 | 5.5 | yes | 5.92, 7.23 | 14.928 |
| 13 | one plate light | 32.8 | 13.3 | no | 0, 8.20 | |
| 14 | off the foil | 26.2 | 0.9 | no | 0, 0 | |
| 15 | docked | 40.8 | 9.6 | yes | 5.67, 3.75 | 14.927 |
| 16 | docked | 25.6 | 7.0 | yes | 5.36, 5.72 | 14.927 |
| 17 | docked | 32.8 | 2.1 | yes | 4.47, 6.34 | 14.927 |
| 18 | docked | 24.7 | 9.0 | yes | 5.09, 2.90 | 14.926 |
| 19 | gap | 28.3 | 7.6 | no | 0, 0 | |
| 20 | gap | 51.6 | 10.3 | no | 0, 0 | |
| 21 | docked | 20.3 | 8.6 | yes | 5.54, 5.68 | 14.927 |
| 22 | docked | 28.3 | 0.5 | yes | 6.05, 5.67 | 14.928 |
| 23 | docked | 19.9 | 6.8 | yes | 7.52, 3.57 | 14.927 |
| 24 | docked | 26.7 | 2.7 | yes | 6.85, 3.28 | 14.927 |
| 25 | fell | 33.0 | 164.4 | no | 17.4, 17.6 | |
| 26 | gap | 21.7 | 10.4 | no | 0, 0 | |
| 27 | off the foil | 25.1 | 2.7 | no | 0, 0 | |
| 28 | docked | 44.6 | 9.7 | yes | 4.50, 6.17 | 14.927 |
| 29 | one plate off the foil | 28.9 | 6.8 | no | 9.05, 0 | |
| 30 | docked | 24.6 | 12.1 | yes | 8.12, 0.77 | 14.922 |
| 31 | gap | 33.2 | 13.5 | no | 0, 0 | |
| 32 | no mark | 28.0 | 91.0 | no | 0, 0 | |
| 33 | gap | 34.8 | 4.0 | no | 0, 0 | |
| 34 | docked | 26.1 | 4.6 | yes | 4.69, 6.35 | 14.927 |
| 35 | fell | 16.8 | 177.8 | no | 17.8, 17.9 | |
| 36 | docked | 30.0 | 3.2 | yes | 6.29, 3.88 | 14.927 |
| 37 | docked | 45.6 | 8.6 | yes | 3.01, 6.83 | 14.926 |
| 38 | fell | 29.0 | 178.4 | no | 17.5, 17.4 | |
| 39 | docked | 30.4 | 1.9 | yes | 6.42, 3.71 | 14.927 |
| 40 | gap | 25.6 | 4.1 | no | 0, 0 | |

Median time on the geometric docks is 27.8 s, max 45.6 s (sim pass only). Median seat-to-sun on those docks is 224 mm, max 264 mm. The tightest plate inside its 20 mm foil is 0.38 mm (calc only on the scored pose). That margin is thin.

The fell rows still show force because the plates hit the floor on the way over. They are not charges. The heading is past the 20 deg gate.

## Print, felt, and the walk

The 35 ducks that did sit were settled again with the plates moved (sim pass only, same pose, not a new walk):

| Case | Still charging | Shorts | Lowest pole on a charge |
|---|---|---|---|
| Print 0.3 mm short (plates higher) | 18 of 35 | 0 | 1.87 N |
| Print 0.3 mm long (plates lower) | 18 of 35 | 0 | 1.10 N |
| Felt dent 0.4 mm under the plate | 18 of 35 | 0 | 2.48 N |

The 0.4 mm dent is the gold-dome estimate (calc only, SEAT_CONTACTS.md), not a measurement of this felt. The 18 charges survive all three. The misses stay misses. No case starts to short.

A 20 s run D walk, plates in the model, command 0.20 m/s after the first 0.8 s (sim pass only): the duck does not fall. Nothing on the belly touches the floor or the mat. The closest belly point is the bumper, 88.6 mm clear of the floor, at 1.42 s. The plates are higher than that during the walk.

## Clips

twin/out/videos/belly_charge.mp4 is seed 1. The duck sits, the plates land, the lamp turns green. The caption says sim pass only. 1280 by 720.

twin/out/videos/belly_charge_fail.mp4 is seed 13. The duck sits and the lamp stays dark, because one plate does not press.

## Still unproven

1. Contact resistance of 304 on this copper foil, with dust and felt lint. The ohms in the 14.93 V figure are the gold assumption. The bench below is the measurement. BLOCKER until that number exists.
2. Wear life of 304, nickel, or foil against the felt. No cycle count was opened.
3. The mat gate board. While the field is on, 15 V is on the stripes and on a plate that touches them. A child can reach under a docked duck. BLOCKER, same as NEST_V2 blocker 2.
4. LM74610 leakage at 15 V, and the CSD18532 body-diode voltage at 1.006 A and room temperature. The neighbouring cited points are above, not the exact point.
5. Whether a real bumper cut of 4 mm, rather than the box in this model, still lets the seat plates land and still leaves the limp sit upright. Four falls are already in the sim.
6. Prices for the 304 sheet, the LM74610, and the MOSFET. Pages were not opened. BLOCKER.
7. The bridge is not in wiring/netlist.yaml. A built harness does not have it.

The proposed decision is BELLY_DECISION.md. It does not replace the gold wells. 18 of 40 is not as good as 38 of 40.
