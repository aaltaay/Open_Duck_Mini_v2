# Flush contacts: a design that has to clear five lines

2026-11-11. Design study only. Nothing in here is installed: print/, the URDF, the netlist, the BOM, and the nest CAD are unchanged. The nest folder was read and not edited. The contact twin (PR 39) is merged. It studies the proud nest pins on cloth, and those resistance numbers are not inputs to the flush grades below. The in-body charger board (PR 40) is merged too. It is the board the nest pins would feed, not the per-pin mat switch in section 6.

Every number is marked **calc only**, **CAD check only**, **sim pass only**, **cited**, or **BLOCKER**. A sim is not hardware. The camera work cited below is geometry, not a photograph.

Script for the window in section 6: `python3 altaay_lab/twin/dock/flush/draw_flush.py`

Figures: [figs/F1_belly_field.png](figs/F1_belly_field.png), [figs/F2_feet_zones.png](figs/F2_feet_zones.png)

## 1. The answer, before the table

Neither a belly dock nor a feet dock meets all five lines Ahmed set.

Feet lose three lines outright. A charge wire has to flex through the hip, the knee, and the ankle on every step, not once per dock. The two soles are opposite poles, so a metal floor joins them. The gold is on the walking face, so it scuffs with the gait, not with the dock count. The published feet window is also smaller than misses the nest sim has already recorded.

A belly layout can keep the wires in the trunk and keep the feet plain. The bumper cannot be the second pole: it hangs 2.9 mm above the mat in the sit, and anything tall enough to reach it is a bump the walk already trips on. Five flush gold wells in the seat, on a large striped field that stays dead until the seat covers it, is the layout that can meet the "nothing sticks out" line and the "no joint wire" line. Its geometric window is large enough to hold the landings the nest sim already scored. That is not the same as docking reliably while the camera is blind. That walk has not been run. Dirt on the gold has not been measured. A flat metal sheet can still touch the gold; diodes in the belly are what stop that from draining the pack. So the belly field is the one to build toward, and it is not a pass of the full bar.

## 2. What the sit and the camera actually give

The cute sit stays. Torque off, head up (D59). In that pose the weight is on the feet, not the belly (sim pass only, NATURAL_DOCK_IDEAS.md section 1, model 2.8078 kg):

| Surface | Touches? | Force | Where |
|---|---|---|---|
| Left sole | yes, inner edge, rolled 7.9 to 8.2 deg | 13.6 N | centre of pressure x -37.5, y +91.8 mm |
| Right sole | yes, same | 13.1 N | x -37.7, y -93.4 mm |
| Seat block | yes, lightly | 0.88 N | patch x -113 to -103 mm, y +/-28 mm |
| Belly bumper | no | 0 N | hangs 2.9 mm up; patch would be x +18 to +27, y +/-22 |

The printed sole's flat face is 84.8 by 15.8 mm (CAD check only, STRIPE_MAT_STUDY.md section 1.1). In the sit the outer edge of that face is 2.2 mm up (sim pass only, same section). Standing, the seat block is 117 mm off the floor and the bumper is 136 mm up (sim pass only, NATURAL_DOCK_IDEAS.md section 1), so belly metal does not meet the floor on a walk. A fall that rolls onto the belly does (D60).

The nest sim's 45 mm window and its landing scatter used a pose stand-in: true pose plus noise, all the way in (sim pass only, NEST_SIM.md). The camera cannot do that.

From the merged camera twin (PR 38, altaay_lab/twin/camera/CAMERA_TWIN.md). CAD check only unless noted:

- Level head, URDF zero, soles on the floor: the gold disc and the ring are not in the field at 0.30 m or at 0.50 m. At 0.75 m the disc is 13 of 13 samples and the ring is 22 of 27. From 1.0 m through 2.0 m both are fully in.
- The first floor a level head sees is 707 mm ahead of the toe. The feet, and about 250 mm of floor ahead of the toe, stay outside the field at every pitch that was swept, including the printed -25 deg stop.
- At that -25 deg stop the first floor is 316 mm ahead of the toe. At 0.30 m the disc is in (13 of 13) and most of the ring is not (13 of 27).
- In the recorded sit the lens looks forward, 286 mm up (CAD check only on a pose that is sim pass only). The sun is behind the lens. 0 of 13 disc samples and 0 of 27 ring samples are in the field. The first floor is 507 mm ahead of the toe.
- The stock walk schedule commands head pitch 0. The policy's own head motion was not re-run (BLOCKER in that file).

So the final sit is blind. With a level head the last full look at the disc and the ring is 0.75 m from the lens. Inside 0.50 m the target is below the field. The feet are never a thing the camera can steer onto.

Landings already measured, with the pose stand-in the camera does not have (sim pass only, NEST_SIM_V2.md section 3):

| Controller | Radial 95th | Radial worst | Sideways sigma |
|---|---|---|---|
| Steering walk-on, all 540 | 37.3 mm | 249.8 mm | 22.3 mm |
| Straight crossing, all 540 | 82.8 mm | 158.9 mm | 36.1 mm |
| Straight crossing, 6.0 V | 105.4 mm | 158.9 mm | 43.7 mm |

Heading after torque off in the steering runs: mean -1.2 deg, sigma 3 to 4 deg, worst 10.5 deg (sim pass only, NEST_SIM.md section 2.4). The sit itself adds about 1 mm (sim pass only, NEST_SIM.md plain summary). Those heading and sit numbers are from the pose stand-in, not from the camera.

Charge current used below is the nest study's pair: 2.0 A typical and 2.8 A peak through the contacts while charging, about 1.0 A when the pack is full (calc only, STRIPE_MAT_STUDY.md section 2, from the dock notes: SYS about 1.0 A typical and 1.8 A peak, charge 1.0 A).

## 3. The five lines, graded

Pass means the line is met on evidence that is already in the repo or on a datasheet that was read. "Not shown" means the geometry might allow it and the test does not exist.

| Line | A. Springs in the mat, pads on the seat and the bumper | B. Magnetic pogo, recessed in the duck | C. Cloth or foam for the give | D. Feet, one pole per foot | Belly field in section 6 |
|---|---|---|---|---|---|
| 1. Nothing protrudes, and it looks clean on or off the mat | Duck pads can be flush. The bumper does not touch, so a spring has to stand about 2.9 mm out of the mat, or the bumper is not a contact. Fail. | The duck side can be the recessed housing. Cited, no millimetre of stick-out. Pass for the duck. The mate still has to meet it. | Flush on both faces. The cloth is 0.1 mm and the foam profiles on the sheet are 1.3 to 2.0 mm. Neither bridges 2.9 mm. Fail as a bumper contact. Pass as a flat mat under a foot or a seat that already touches. | The strip is flush with the sole. It does not protrude. It is visible metal on both feet, on and off the mat. Partial. | Five wells flush with the seat. Feet and bumper stay plain. Pins sit in pockets and stop at the felt. Pass. |
| 2. Blind sit, with a window number | The nest's 45 mm radius needs both the seat and the bumper (calc only, NEST_CAD.md). The bumper is 2.9 mm up. A seat-only pair sits inside a 10 by 56 mm patch, so a fixed plus and minus on that patch cannot forgive a 40 mm miss. Fail. | Housing diameters on the series sheet run from 5.5 mm to 16.5 mm (cited). The sheet says the magnet self-aligns and does not say by how many millimetres. BLOCKER for the capture distance. A connector face of that size does not cover a 37 mm miss, let alone a blind one. Fail. | Same windows as the pads they sit on. The two-zone feet window is +/-69 mm sideways, +/-72 mm deep, +/-30 deg (calc only, STRIPE_MAT_STUDY.md section 1.5). That is smaller than the straight-crossing 95th of 82.8 mm. Fail as proof. | Same +/-69 mm, +/-72 mm, +/-30 deg (calc only). Does not contain the straight-crossing 95th. The blind walk is not in that number. Fail. | Inscribed radius 161 mm, box +/-254 mm along the wall and +/-161 mm deep, heading +/-46 deg (calc only, section 6). Contains the 95ths above and the 158.9 mm straight-crossing worst. Does not contain the 249.8 mm outlier. Does not prove the blind walk. Not shown. |
| 3. No charge wire flexing through a joint, if it can be avoided | Wires stay in the trunk. Pass. | Pass if the connector is in the seat. Fail if it is in a foot. | Pass in the belly, fail in the feet. | Fail. One 22 AWG per leg through five joints. Section 5. | Wires stay in the trunk. Pass. |
| 4. Duck contacts dead or protected off the mat. No short on metal. No live metal left exposed on the mat. | Flush seat gold meets a metal sheet in a belly-down roll. A live stripe or a live ring is the open cloth the compliance note already flags. Fail unless each cell is off until covered. | A shrouded pair is easier to gate, and the live area is the connector, not a rug. Partial. Capture still fails line 2. | A large live cloth zone fails the exposed-metal line. Two foot zones stay bare beside the feet while charging. Fail. | The soles are the contact with every floor. Left plus and right minus is a short on a metal sheet. Fail. | Cells conduct only when the seat compresses them, and the high current waits for the signature. A sheet can still touch flush gold. Diodes block pack current. That is protected, not "no short". Partial. |
| 5. Wear over thousands of docks | A pin that only mates at the dock is in the 100,000-cycle class (cited, section 4). Dirt and cloth are not. Not shown. | Up to 30,000 mates (cited). Dirt not shown. The alignment failure comes first. | The EMI abrasion line on a gasket sheet is not a power-contact test. Not shown. | The strip scuffs every step. About 6,700 bends and scuffs per walking hour (calc only, section 5), against a few hundred docks a year. Fail the "dock wear" framing: the walk dominates, and sole wear is unmeasured. | Same pin class as column A. Thousands of docks fit in 100,000 cycles (calc only, section 6). One well can be the only contact on a pole, so one dirty well opens the charge. Dirt is BLOCKER. Not shown. |

## 4. Parts that were actually read

**Mill-Max 0906-0-15-20-76-14-11-0**, short-stroke spring pin. Cited from the maker's sheet (https://www.farnell.com/datasheets/3820075.pdf) and the family table (https://datasheet.octopart.com/0906-0-15-20-76-14-11-0-Mill-Max-datasheet-12530742.pdf):

- Stroke 0.039 in, which is 0.991 mm. Initial height 0.137 in, which is 3.480 mm. The body does not fit in 2 mm of felt. It sits in a pocket under the felt, and the tip is set level with the felt.
- Preload 25 g, which is 0.245 N. Force at mid stroke 60 g, which is 0.589 N.
- Contact resistance 20 milliohm max. Family table: 2 A continuous, 3 A peak. The same product sheet's spring table also lists 8 A at a 30 C rise and 6.4 A derated. The connector rating used here is the family table, 2 A continuous and 3 A peak. One pin at 2.0 A typical is on that continuous rating, with no margin. The 2.8 A peak is under the 3 A peak and over the 2 A continuous rating.
- Durability 100,000 to 1,000,000 cycles at mid stroke. Gold 20 microinch over nickel on the sleeve and plunger (family table).

At 20 milliohm, one pin at 2.0 A is 0.040 V and 0.080 W. At 2.8 A it is 0.056 V and 0.157 W (calc only, from the cited resistance, clean lab conditions). Two pins in series, the plus and the minus, are twice that. This is not a dirty-mat number.

**EDAC 685 male and 686 female magnetic pogo**, series sheet https://www.in2connect.uk.com/wp-content/uploads/2024/09/Magnetic-Pogo-Series.pdf (cited from that sheet):

- Current order codes include 2.0 A and 5.0 A, up to 5 A per contact. Contact resistance 30 milliohm. Life up to 30,000 mating cycles. Plating codes include 5, 10 and 15 microinch gold, and gold flash.
- Contact position 0 is the recessed, shrouded contact. Round housings are listed from 5.5 mm to 16.5 mm across.
- The sheet says the magnet pulls the halves together and self-aligns. It does not give a capture distance or a pull force. Both are BLOCKER. A 16.5 mm face cannot swallow an 83 mm miss.

The Multicomp Pro female MP009317 is 1 A and 50 milliohm (cited, https://www.farnell.com/datasheets/3703264.pdf). It does not meet 2.0 A typical, so it is not a candidate.

**Laird Flectron 3035-535** nickel-copper polyester taffeta (cited, https://www.laird.com/sites/default/files/2018-11/EMI-DS-FOF-3035-535_051315.pdf): surface resistivity under 0.07 ohm per square (ASTM F390), nominal thickness 0.0045 in (117 microns). That is a sheet resistance, not a contact resistance against a gold pad. Contact resistance at 0.88 N is BLOCKER.

**Laird fabric-over-foam** (cited, https://www.farnell.com/datasheets/317084.pdf): compression force 5 to 10 lb per foot, surface resistivity under 0.07 ohm per square, recommended compression 30 to 50 percent of the foam height for the D, rectangle, and square profiles. Profile 4320 is 0.050 in high (1.3 mm). Profile 4052 is 0.080 in high (2.0 mm). 5 lb per foot is 73.0 N per metre (calc only). A 40 mm length at the low end of that range needs 2.92 N, and at the high end 5.84 N. The seat's 0.88 N can compress about 12 mm of the soft end and about 6 mm of the stiff end (calc only). A foot at 13.6 N can compress a 40 mm strip. Foam of this class belongs under a foot, and it is still too short to bridge the bumper.

**Littelfuse MDSR-10** reed (cited, https://www.littelfuse.com/assetdocs/littelfuse_reed_switches_mdsr_10_datasheet.pdf): switching 0.5 A, carry 1.0 A, 10 W, contact resistance 120 milliohm max, pull-in 10 to 25 ampere-turns. It cannot carry 2.0 A, let alone 2.8 A. It can only enable a transistor. How far a magnet in the seat can be and still close it is not on the sheet. BLOCKER.

The 22 AWG silicone used everywhere else in the duck is 1.7 mm outside diameter, plus or minus 0.1 mm (cited, the wire table in altaay_lab/sim/mass_budget.py, from the BNTECHGO listing). Annealed-copper resistance used by the power sim is 52.96 milliohm per metre at 20 C (cited, altaay_lab/sim/power_path_sim.py). Mass is 5.12 g per metre (calc only, that same wire table).

## 5. Feet, counted properly, and why they still lose

Ahmed is right that servo leads already run the legs. The charge lead would not be the first wire in the joint. It would be an extra one, and it cannot share the copper that is already there.

What crosses the left knee today (wiring/netlist.yaml, CABLE_MAP.md):

| Cable | Conductors | Gauge | Joints |
|---|---|---|---|
| S5, kit bus, knee to ankle | 3 (V, G, data) | kit | left knee. Test-fit BLOCKER: the 150 mm kit lead is short of the 40 mm slack rule by 25 mm (CAD check only, SIT.md section 6). |
| SP4, second ankle feed | 2 (V, G) | 22 AWG | hip yaw, hip roll, hip pitch, knee. Stops at the ankle servo. Does not cross the ankle. Short of the slack rule by 17 mm (same section). |
| D3, foot switches | 2 | 26 AWG | those four, plus the ankle, plus the neck. Knee loop after the sit work: free length 29 mm, bend radius 11.0 mm against a 10.4 mm check (CAD check only, SIT.md section 6). |

That is 7 conductors through the knee and 2 through the ankle. The right leg is S10, SP5, and D4, the same counts.

A feet dock with one pole per foot adds one 22 AWG per leg. The knee goes from 7 conductors to 8. The ankle goes from 2 signal wires to 3, and the new one is the first power wire through the ankle. The route parallels SP4 from the belly splices through the hip and the knee, then parallels D3 through the ankle into the foot. It does not follow D3 up the neck.

It cannot share SP4's copper. SP4 is the 7.2 V servo bus. The mat is the gated supply, about 9.5 V in the nest notes (calc only, and the charger dropout is still BLOCKER). Tying them would put the dock supply on the servo bus. Sharing the ground would add up to 2.8 A of return on the ankle feed that was added because the ankle voltage was already low (D23). Parallel in the same sleeve, separate nets. Yes. The same conductor, no.

Planning length 0.50 m per leg, both ways, is 0.053 ohm and 5.12 g for the pair (calc only, from the 52.96 milliohm per metre and 5.12 g per metre above). At 2.0 A that is 0.106 V and 0.21 W in the copper. At 2.8 A it is 0.148 V and 0.42 W (calc only). The dressed cut, with slack and the 150 deg knee, is BLOCKER until someone routes it. This study does not edit the netlist.

Flex count (calc only, FEET_DOCK.md section 3): a 0.54 s gait is about 6,700 flexes of each joint per walking hour, or about 2.4 million a year at one hour a day. One dock a day is 365 sit-folds a year. One hour of walking is about 6,700 times one dock. The new wire sees the walk, not a dock counter. The sit also folds the knee to 150 deg (D59), which is a larger bend than the 90 deg in that flex table, once per dock.

Bend radius: the knee loop is 11.0 mm (CAD check only, above). The new wire is 1.7 mm outside diameter, so the loop is 6.5 times the diameter (calc only). FEET_DOCK.md section 3 used a 10-times rule for continuous flex and said the existing loops were short of it. No flex-life number exists for this loop (BLOCKER, the same one D58 recorded, TEST_PLAN.md 19.7). The servo wires already live in that unknown. Adding a charge wire extends the unknown to a power conductor, including through the ankle, where today there is only a signal pair.

Contact force on the sole is real: 13.6 N and 13.1 N (sim pass only). A 50 mm by 3 mm strip on the inner edge of the 15.8 mm face is the part that is down when the sole is rolled, and it is flush, so it also bears while walking. Recessing it would let the TPU edge touch first and the gold miss. Wear after carpet and tile is the unrun bench from D58. Fail line 5 on evidence, not on a guess that gold survives.

A metal tray under both feet joins plus to minus. That is a short of the charge input on a surface the duck stands on every time the floor conducts. Diode protection could stop pack current, and the short would still be there. Line 4 asked for no short. Feet do not meet it.

The two-zone window, +/-69 mm and +/-72 mm at +/-30 deg (calc only), does not contain the straight-crossing 95th of 82.8 mm, or 105.4 mm at 6.0 V (sim pass only). The camera never sees the feet, so nothing in the head can trim the last centimetres. Feet are the worse window and the worse harness.

## 6. What would actually clear the bar

Five gold wells in the seat patch, flush, 3 mm across, at y = -24, -12, 0, +12, +24 mm in that patch. The patch that touches is only 10 mm deep and 56 mm wide (sim pass only, section 2), and these five sit inside it. The bumper stays plain TPU. The soles stay plain. No new wire crosses a joint. The leads are the short belly runs the nest CAD already sketched for the seat pins (NP1 to NP3, CAD check only for those lengths, NEST_CAD.md). This study does not copy that CAD in.

The mat is felt, 560 mm along the wall and 360 mm deep, with stripes parallel to the depth axis: 20 mm of conductor, 5 mm of bare felt, repeating. Polarity alternates. A 3 mm well cannot bridge a 5 mm gap (the disc is smaller than the gap), so one well never joins plus to minus (calc only, same rule as STRIPE_MAT_STUDY.md section 1.3).

Under the felt, in pockets, one Mill-Max 0906 per landing the seat might use, tip level with the felt. The duck walks on felt, not on pin heads. High current is connected to a pin only while that pin is compressed and the signature says the thing on the mat is the duck. A coin, a hand, or a pet does not get the 2.8 A. The reed in section 4 can be the sense, not the power switch. The power switch is a transistor on a board that is not designed. The merged charger board (PR 40) is the pack charger, not this per-pin mat switch. BLOCKER for the mat switch.

Window, from draw_flush.py, calc only. Every stripe phase was tried in 0.25 mm steps:

- Heading 0 through 46 deg: every phase puts at least one well on plus and one well on minus.
- At 60 deg, 65 percent of phases still do. At 90 deg, none do.
- No heading puts two wells on each pole at every phase. The 56 mm patch is shorter than the 76 mm row the stripe study needed for a redundant foot. One dirty or missed well can open a pole.
- The seat centre may sit anywhere inside +/-254 mm along the wall and +/-161 mm deep, at up to 46 deg, and keep every well on the field. The inscribed radius of that box is 161 mm.

161 mm contains the steering 95th (37.3 mm) and the straight-crossing 95th (82.8 mm, and 105.4 mm at 6.0 V) and that controller's worst radial (158.9 mm). It does not contain the steering run's single 249.8 mm outlier (sim pass only, section 2). The heading band contains the 10.5 deg worst from the steering sit (sim pass only), and that heading was measured with the pose stand-in.

This does not cover the blind camera. The nest numbers were taken with a pose the camera does not have inside 0.50 m. Calling 161 mm a proof would be pretending. What would close line 2 is a sim that has not been run: head at the -25 deg stop so the last look at the disc is the 0.30 m case the camera twin already drew, then no pose updates, then the turn, then the sit. Pass is the seat centre inside the 161 mm radius. A second case with the head held level, last look at 0.75 m, will be worse and should be reported beside it. The stock schedule commands pitch 0, so the head-down look is a dock behavior, not something the walk does by itself.

Force. Five pins at the 25 g preload sum to 1.23 N (calc only). The seat brings 0.88 N (sim pass only). The extra 0.34 N goes into the feet, which already carry about 27 N together. The nest sit kept the legs on their stops with springs near 1 N each (sim pass only, NEST_SIM.md). Whether all five of these lighter pins stay down on real felt is BLOCKER. The stripe study's stiff-contact check is the warning: if only two contacts touch, a lot of poses go open.

Heat, if the 20 milliohm lab number held, would be under 0.2 W per pin at 2.8 A (calc only, section 4). It will not hold once there is dust. The pass mark already written for a pad is under 50 milliohm (D58's bench, not run). At 50 milliohm and 2.0 A, one contact is 0.10 V and 0.20 W. Two in series are 0.20 V and 0.40 W. At 2.8 A, two in series are 0.28 V and 0.78 W (calc only). The charger heat in the trunk, 1.9 to 3.2 W (calc only, STRIPE_MAT_STUDY.md section 2.5), is unchanged by moving the contacts, and the thermal twin has not been re-run with it (BLOCKER).

Diodes. A well can land on either stripe, so each well needs a path to either rail. Schottky diodes in the feet were the stripe study's 1.0 V drop, and that drop kept a 9 V mat from finishing the charge (calc only, that section). Here the diodes are in the trunk, not the feet, so the leg is spared, and they should be ideal diodes so the drop stays a small fraction of a volt. The part is not chosen. The MCP73213 dropout is still unread (BLOCKER). A metal sheet across the five wells ties the diode inputs together. With the mat absent, that tie has no pack behind it if the diodes point into the duck. Pack current does not flow. The gold still touches the sheet. Line 4's word was "no shorts", and also "dead or protected". This design is protected. It is not free of a metal-to-metal join. The join goes away only if the gold sits below the TPU and the pin rises into the well after the duck is down. No catalog pin does that rise by itself. It is not part of this drawing.

Wear. 10 years of one dock a day is 3,650 mates (calc only). The Mill-Max durability line starts at 100,000 cycles (cited). The count is inside the line. The line is a clean mid-stroke lab test, not dust, hair, or felt. Line 5 stays not shown until a bench holds a gold pair at about 0.25 N for 10,000 mates with dust and stays under 50 milliohm. That bench is the one that would close it.

Mass of the five short pins is not on the sheet that was opened. BLOCKER. They replace the four long probes the nest CAD had sticking out, and they do not add the leg wires.

CAD, not drawn into print/ and not into the nest folder:

- sit_seat: five flush gold inlays on the contact patch, no change to the outer shape.
- A belly feed for five leads instead of the nest's four pin sockets. The nest CAD is the other agent's file and was not touched.
- No change to the feet, the bumper, the URDF, or the netlist.
- The mat field is a drawing in this folder. Landing it is a later job, after the blind sim.

## 7. The other three, short

**Springs under both the seat and the bumper.** The seat half is section 6. The bumper half does not touch. Closing 2.9 mm with a pin that stands proud of the felt makes a bump. The stock walk crossed a 2 mm mat 6 of 6 times, a 3 mm mat 5 of 6, and a 7 mm mat 0 of 6 (sim pass only, as cited in D61). A field of proud pins is not a 2 mm mat. Not recommended.

**Magnetic pogo.** Best contact spec in the sheets that were opened: 30 milliohm, a 2 A or 5 A code, 30,000 mates, and a recessed housing so the duck side is flush (cited, section 4). The blind sit misses by tens of millimetres. The connector is at most 16.5 mm across, and the capture distance is not published. A magnet does not pull the duck across 80 mm. It is the wrong tool for a camera that has already lost the target.

**Cloth or foam instead of a spring.** Right material under a foot, where 13 N is available, and the wrong material under the seat, where 0.88 N meets a gasket that wants about 3 N on a 40 mm strip (calc only, section 4). Thickness 0.1 mm to 2.0 mm does not reach the bumper. Used as a big live zone, it is the open cloth in COMPLIANCE_FIRST_PASS.md. Fine as the felt colour and the insulating gap. Not the power contact.

## 8. What this does not claim

- The blind last half-metre has not been simulated. The 161 mm window is calc only. It is a size, not a dock rate.
- Pin-on-gold at 0.25 N with dust is not measured.
- The ideal-diode board is not designed. Dropout of the charger chip is BLOCKER.
- Felt compression under 0.88 N is not measured, so a pin set even 0.2 mm below the felt might never meet the seat. The drawing sets the tip level with the felt for that reason.
- PR 39 (contact twin) is merged. Its numbers are for the proud nest pins on cloth. They are not inputs to the flush grades above. The charger board (PR 40) is merged and is not the mat switch.
