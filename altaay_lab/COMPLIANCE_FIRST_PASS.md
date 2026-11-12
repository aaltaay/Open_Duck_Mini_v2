# COMPLIANCE FIRST PASS

Written 2026-11-11 ET. Research only. This is not legal advice, not a test report, and not a certification.
Nothing was bought. Nothing was submitted to a lab. A rule is cited only where a public page was opened or a
search result quoted that page. Where the text of a standard was not opened, the line says uncertain.

The duck this file talks about is a home robot: a Pi with Wi-Fi and Bluetooth, a camera, a lithium pack, a
charger that D61 moves inside the body, and open cloth contacts on a floor mat. None of that is built.

## Top 3 that can force a design change before freeze

These three can change the nest, the bay, or where the charger sits. The others below can add labels, tests,
or a decision about who the duck is sold to. They are less clear as a shape change before freeze.

1. **The cloth on the floor is a live contact while the duck charges.** D61 keeps only two wires. The mat is
   meant to stay at a small probe until it recognizes the duck, then it becomes the supply (about 9.5 V, calc
   only, D61) with enough current to run the duck and charge the pack. That live cloth is a large area a hand,
   a pet, a spill, or a piece of metal can touch, and the duck does not cover all of it. If a household or toy
   rule says those contacts must be inaccessible, or that the current a person can draw must stay very small
   the whole time, the open ring cannot stay as drawn. Design for now: the power switch stays open unless the
   signature and the leak check both pass (TEST_PLAN.md section 20.5), the felt gap is wider than a coin, and
   the high current is on only while the duck is sitting and is removed before it stands. Be ready to cover
   the cloth or to energize only the patch under the body. Uncertain: no charging-mat standard was opened.

2. **The charger inside the duck, next to the cells.** D61 puts the MCP73213 in the trunk because two wires
   cannot keep the charger outside and still let it see the pack alone. The heat is about 1.9 to 3.2 W (calc
   only). The thermal twin has not been re-run with it (BLOCKER). The cell sheet opened this session allows
   charge only from 0 C to 60 C. The servo sheet opened this session allows operation from -20 C to 60 C. The
   thermal twin's PLA band is 49 C to 57 C (twin/thermal/THERMAL_TWIN.md; not re-measured here). If the trunk
   cannot hold those limits, the charger has to move back out or become a switcher. Either one changes the
   two-wire nest. The MCP73213 datasheet itself was not opened, so dropout and the timer are still BLOCKER.

3. **The pack is two loose cells, spot welded, and the bay is tighter than the opened cell sheet.** 49 CFR
   173.185, as returned by the public rule search, says each lithium cell or battery must be of a type proven
   to meet UN 38.3. A pack built in the lab is a battery, not only a cell. The full section was not read line
   by line, so any exception for a pack assembled from tested cells is uncertain. If the pack needs its own
   test summary before it can be shipped, the bay may have to fit a pack that already has that summary. On
   size, the opened Molicel P45B sheet (version 1.2) gives 21.55 mm and 70.15 mm as maximums. The bay is drawn
   at 21.4 by 70 mm (twin/battery/BAY.md). Design for now: do not freeze the bay until it fits the maximums,
   and do not treat the cell's data sheet as a pack approval.

Close behind these, and uncertain as a shape change: the Pi's radio in this plastic body. See the FCC section.
If the grant does not cover this host, the fix might be a label and a test, or it might be moving metal away
from the antenna. The grant was not opened.

## FCC Part 15, the Pi and the camera

**What it is.** Part 15 is the US rule for radio-frequency devices. Intentional radiators are things that mean
to transmit (Wi-Fi, Bluetooth). Unintentional radiators are things that only make noise as a side effect
(a computer, a camera). A modular transmitter approval, 47 CFR 15.212 (eCFR, opened, displayed as of
2026-11-09), lets a radio be approved with its antenna and then built into a host, if the module meets the
conditions in that section (shielding, its own regulator, a fixed or unique antenna, a label, and RF exposure
in the final configuration). If the module is inside a product and its own FCC id is not visible, the outside
of the product must say that it contains the module. A limited modular approval is allowed when the maker can
show the radio still complies in the way that particular host will use it, and the maker has to keep control
of that end product.

**Why it might block the design.** The Raspberry Pi Zero 2 W product brief (October 2021, opened) says the
board has 2.4 GHz 802.11 b/g/n, Bluetooth 4.2, BLE, an onboard antenna, and "modular compliance certification."
The same brief says the board should be used in a ventilated case, not covered, not on a conductive surface,
and that connecting incompatible devices may affect compliance. The duck is a closed plastic body with servos,
a camera cable, and metal pins under the belly. That is not the bare board the brief describes. The FCC id
itself was not read from the FCC grant database this session (a secondary page names 2ABCB-RPIZ2; that id was
not confirmed here). Uncertain: whether the Pi's approval is a full modular grant or a limited one, and
whether this host is inside it.

The Camera Module 3 brief (June 2024, opened) lists FCC 47 CFR Part 15 Subpart B, Class B, for the camera.
That is an unintentional-radiator claim for the camera, not a radio approval, and it is for the camera as
Raspberry Pi sold it.

There is no other radio in the duck. The Xbox controller's radio stays in the controller.

**Design for now.** Keep the Pi's printed antenna. Do not add a different antenna or a USB radio. Leave air
around the board, which the brief asks for. Plan a label on the outside of the body once the real FCC id is
read from the grant. Plan a host check of the finished duck (the digital part as an unintentional radiator,
and a check that the radio still matches its grant) before any sale. Do not call the duck certified because
the Pi and the camera have their own marks.

## Charger moved inside the duck

**What it is.** D61 moves the MCP73213 into the trunk so the two cloth wires can feed a supply, the duck can
stay awake through the ideal diode, and the pack can charge on its own. The study's numbers are 8.40 V, 1.0 A,
and a 6 hour timer (D61 and the dock list). Those numbers were not confirmed on a Microchip datasheet this
session. The datasheet was not opened. Dropout is BLOCKER. The study also says the chip has no thermistor
pin, so cell temperature has to be watched by another circuit. That sentence was not checked on the datasheet.

**Why it might block the design.** Heat, as in item 2 of the top 3. A linear charger drops the extra volts as
heat in the same shell as the cells and the PLA. A hot cell outside 0 C to 60 C is outside the charge window
on the opened P45B sheet. A hot servo case above 60 C is outside the opened STS3215 operating range. The
thermal twin does not yet include this heat source.

**Design for now.** Do not freeze the charger seat until the datasheet is read and the thermal twin is re-run
with that heat, or until the charger stays in the rim. TEST_PLAN.md section 20.8 is the bench check: cells
0 C to 45 C while charging, charger case under 70 C, nearest PLA under 45 C. Those bench limits are tighter
than the cell sheet on purpose. They are not a pass until they are measured.

## Lithium cells and the pack

**What it is.** UN 38.3 is the UN transport test for lithium cells and batteries (altitude, thermal, vibration,
shock, short, impact, overcharge, forced discharge, as the manual lists them). 49 CFR 173.185 requires each
lithium cell or battery to be of a type proven to meet that subsection. PHMSA's public page on test summaries
says the same duty in plain words: https://www.phmsa.dot.gov/training/hazmat/new-un-requirement-test-summaries
(search result; the PDF form was not read line by line). IEC 62133 is the type test for cells and batteries
used in portable equipment. The IEC text was not opened. Uncertain which edition, and uncertain whether a
Molicel report exists for the P45B. The product data sheet opened this session does not mention 62133 or
UN 38.3, and it says it is not a warranty.

**Why it might block the design.** Item 3 of the top 3. Shipping a homemade 2S pack, or selling the duck with
that pack, can require a test summary for the pack as shipped, not only for the cell. The weld, the sleeve,
and the BMS are not sourced (BOM line 7, PARTS_AUDIT.md).

**Design for now.** Keep the cells as a known type (INR21700-P45B) and keep the bay large enough for the
sheet's maximum size. Do not ship a welded pack, and do not freeze a "pack" part, until a test-summary path
is chosen: a pack that already has one, or a lab test of this exact 2S build. The software cutoff in
TEST_PLAN.md section 11 stays, because the BMS cut the BOM cites (2.40 V per cell) is below the 2.5 V
discharge floor on the opened cell sheet. That BMS number was not re-read on a Tenergy datasheet this session.

## Toy, household, and robot safety marks

**What it is.** If the duck is sold as a children's toy, ASTM F963 is the US toy safety spec, and the EU toy
directive has its own rules. The Feetech STS3215 sheet opened this session marks ASTM F963 as No, EN71 as No,
and FCC as No, and marks EMC and RoHS as Yes. That is the servo maker's own table, not a test of the duck.
UL-style standards for audio, information, and household equipment, and any newer standard aimed at consumer
robots, were not opened. Uncertain which of them would be the one a lab would quote. The nest study's 24 V
toy-voltage comparison was from secondary notes. Those standard texts were not opened here, so that voltage
comparison stays uncertain.

**Why it might block the design.** Ahmed has called the duck a home companion. If a later decision markets it
to children, the servo's own "No" on ASTM F963, the open charge cloth, the loose spring pins, and a lithium
pack behind a screwed lid all become product questions, not only lab questions. That decision is not made.
Uncertain: this file does not decide that the duck is a toy.

**Design for now.** Do not add a toy claim. Keep the pack behind screws (D45). Keep the pins retained so they
are not loose parts. Keep the mat unpowered until the signature gate passes (TEST_PLAN.md 20.5). Use a listed
wall adapter for the mat, not a bare supply, when that adapter is chosen. Revisit this section before any
public sale.

## Open charge contacts, touch, pets, liquids

**What it is.** The plus disc and the minus ring are conductive cloth on a felt mat on the floor. They are
not covered. Pets, spills, coins, and hands can reach them. The safety idea, not yet a circuit, is a
signature plus a leak check so the mat stays at a probe until the duck is the thing on the cloth
(twin/dock/nest/stripes/STRIPE_MAT_STUDY.md, calc only).

**Why it might block the design.** Item 1 of the top 3. A probe that is only a few volts and a milliamp is a
different problem from a live charge at pack current. The dangerous state is the second one, while the duck
is charging and part of the ring is still bare.

**Design for now.** TEST_PLAN.md 20.1 to 20.5 before any mat is left powered: contact resistance, snag, hair
and dirt, a coin on the gap, and the gate against water, metal, and a resistor stand-in for skin. Current
limit on the bench supply the whole time. Do not copy the sim as a safety pass.

## Camera privacy at home

**What it is.** The duck carries Camera Module 3 and uses it to find the nest, and the companion work uses it
to look toward a person. A camera in a home can record people who did not agree, including guests and
children. Which US state rule applies (biometric face data, a voice recording, a notice at the door) was not
researched statute by statute. Uncertain, and not legal advice.

**Why it might block the design.** It does not by itself move a screw. It can force the software: the camera
on only when a person can tell, no face library stored, no upload by default, and a way to run the nest
find without keeping the pictures. If a later decision adds face recognition, that is a new privacy design,
not a small feature.

**Design for now.** Nest finding may use the camera without tags (D61). It should not need to store video to
do that. A light or a sound when the camera is active is the simple cue to design in. TEST_PLAN.md 20.9 is
the function test. Privacy behavior is gate 7 in DEFINITION_OF_DONE.md, and it is a GAP until that software
exists.

## What this pass did not do

No standard was purchased. IEC 62133, ASTM F963, and any UL robot standard were not opened. The FCC grant
for the Pi was not opened. The MCP73213 datasheet was not opened. Nothing here is a pass for gate 5 or
gate 6 in DEFINITION_OF_DONE.md.
