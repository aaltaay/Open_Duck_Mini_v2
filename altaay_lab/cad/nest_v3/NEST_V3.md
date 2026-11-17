# Nest mat, version 3

2026-11-16 ET. Ahmed approved a redesign the same evening (7:24 PM ET): the charging contact is the full metal belly, split into two halves, and the mat is redrawn to match. This file is that mat. nest_v2 is not changed. D61 is not edited.

Nothing was built or bought. The 40-seed numbers are sim pass only. They do not beat the gold domes (38 of 40, SEAT_CONTACTS.md).

Every number is **sim pass only**, **calc only**, **CAD check only**, or **cited**. Anything else is a **BLOCKER**.

## Why the split is front and back

A left and right split was the first try. The seat is 80 mm wide (CAD check only, sit_cad.json). Two full halves with a few millimetres of insulation between them can keep one half on each pad only while the belly centre stays within about 20 mm of the mat's dividing line (calc only, the same limit as in the belly-insert note: the window is about half the half-width).

The camera dock does not land there. On the 40 seeds the seat's along-wall position, for the ducks that sat, runs from 28 mm to 329 mm (sim pass only, the belly-insert batch). None of those 35 sits is within 20 mm of the centre line. Side-step was tried on this policy: 6 s at the maximum sideways command moves the body about 2 cm, and not always the way it was asked (sim pass only). The walk does move forward.

So the dividing strip runs parallel to the wall, at one depth. The rear half is the whole seat. The front half is the whole bumper. Lateral error does not matter, because each pad covers the full width of the mat. Depth is what the duck can aim, because forward walking works.

The marks stay where they are. They still mark the centre line. The new piece is a depth stop, not a new mark.

## The mat

Sun at the origin, wall at x = 190 mm, same frame as nest v2.

- Strip centre x = -200 mm, width 24 mm (calc only). Felt, no copper. It runs the full width of the mat, y from -280 mm to 280 mm.
- Rear pad (wall side of the strip) is plus. Front pad (room side) is minus.
- Both pads are flush with the 2 mm walking surface. The old 20 mm stripes are not on this mat.
- A trunk between x = -292 mm and x = -197 mm, heading within 14 deg of facing the room, puts at least 8 mm of each half on its own pad, even if the metal is 0.3 mm fat (calc only). Outside that band a half can sit on the strip, on one pad only, or across both.

The duck is asked to sit when the camera puts the trunk between x = -284 mm and x = -205 mm. That is 8 mm inside the deep end of the geometric band.

## The belly

- Rear half: the whole seat face, 32 mm by 80 mm (CAD check only). In the dock model its bottom is 5 mm below the CAD seat face, so it meets the bumper plane and then goes 2 mm past it. Both halves can take load. It does not change the mat.
- Front half: the whole bumper face, 24 mm by 60 mm, at the CAD bottom z = -69 mm.
- The shell between them, about 102 mm of body x (CAD check only, seat front at x = -94 mm, bumper back at x = 8 mm), is plain PETG. That gap is what has to cover the 24 mm strip.
- Metal is 0.5 mm 304. Two plates are 15.8 g (calc only, 7.90 g/cm3, Sandmeyer 304 sheet). The 5 mm seat standoff, if it is PETG at 1.27 g/cm3, is 16.3 g (calc only). MuJoCo keeps density 0 on these boxes, so the walk mass is unchanged.
- A 4.99 k ohm resistor between the halves is the signature the mat looks for. It is not the charge path.

The charge path is the same ideal-diode bridge as BELLY_CONTACT.md (four LM74610-Q1 and four CSD18532Q5B). Rear pad is plus and front pad is minus when the duck faces the room. Turned 180 deg, the halves swap. The bridge still feeds the BQ24133 the right way. A placed sit facing the wall, trunk x = -120 mm, put 10.8 N on one half and 6.5 N on the other and charged, no short (sim pass only).

## The 40 seeds

Same starts as the camera dock. Run D. The depth stop is on. Sim pass only.

Geometric docks: 15 of 40.
Charging docks: 15 of 40.
Shorts: 4 of 40. Seeds 18, 26, 33, and 37. The bumper footprint crosses the strip. The lamp stays dark. This is not zero shorts.
Falls: 3. No mark: 1 (seed 32, the same miss as before).
The other misses stop with both halves on the rear pad, or with the bumper in the air. The policy cannot walk backward, so a sit that is already too close to the wall is not walked back onto the strip.

On a charging sit each half is at least 8.4 N, and the chip input is 14.917 V (sim pass only). That is inside 4.5 V to 17 V. The contact ohms are still the gold-dust assumption. The bridge drop is 0.0277 V and the nest switch is 0.012 ohm at the cited 12 milliohm (calc only).

This does not beat 38 of 40.

Print 0.3 mm short, print 0.3 mm long, and a 0.4 mm felt dent (the old dent estimate, not a measurement): the same 15 still charge, and the same 4 still short (sim pass only, re-settle, not a new walk).

A 20 s run D walk does not fall and does not scrape. The closest belly point is the bumper, 84.6 mm off the floor (sim pass only).

## Clips

twin/out/videos/belly_v3_charge.mp4 is seed 1. The lamp turns green. Caption: sim pass only. 1280 by 720.

twin/out/videos/belly_v3_charge_fail.mp4 is seed 18. The bumper crosses the strip. The lamp stays dark.

## Sense, then 15 V

The pads stay at the sense voltage until the mat sees the duck. They are not at 15 V for a finger, a coin, or an empty mat.

Sense, calc only. 15 V, 12.1 k ohm over 3.48 k ohm, makes 3.35 V. From that node, 10.0 k ohm goes to the plus pad. The minus pad is the sense ground. Open-circuit pad voltage is 3.35 V. With 4.99 k ohm across the pads the pad voltage is 0.945 V.

The comparator is the LM393BIDR already on the charger board. Enable the 15 V switch only while the pad is between 0.80 V and 1.10 V. A dead short is near 0 V. An open pad is 3.35 V. Both are outside the window, so the switch stays off.

The switch is a Diodes DMP3018SFV P-channel MOSFET (cited, diodes.com product page): drain-source 30 V, gate-source plus or minus 25 V, 11 A at 25 C on the board, 12 milliohm at a 10 V gate. The nest is 15 V, so the drain-source is inside 30 V. Pulling the gate to 0 V with the source at 15 V is a gate-source of -15 V, inside plus or minus 25 V. 1.006 A is inside 11 A. The drop at 12 milliohm is 0.012 V (calc only).

A child on an idle mat sees at most 3.35 V, through about 13 k ohm, under 0.3 mA (calc only). Not 15 V.

A metal object across the pads is a short. The window stays closed. 15 V stays off.

A water spill was not measured. If its resistance is not near 4.99 k ohm, 15 V stays off. A spill that happens to read inside 0.80 V to 1.10 V would enable the pads. That resistance is BLOCKER.

The belly, off the mat, is the same story as BELLY_CONTACT.md. The bridge is off, the bleeds hold the halves near ground, and the pads themselves are not at 15 V until the sense passes. Pack voltage does not reach the shell.

## What this does not claim

1. It does not beat the gold domes. 15 of 40 is not 38 of 40.
2. It is not zero shorts. Four sits still cross the strip.
3. Contact resistance of 304 on copper is not measured. The bench in BENCH_CONTACT.md is that measurement.
4. Wear life is BLOCKER.
5. Finger and spill resistances on this felt are BLOCKER. The window rejects a short and an open. It does not reject every wet object.
6. A copper-sheet price for pads this size was not opened. BLOCKER. Felt sheet price is still BLOCKER (nest v2).
7. The sense board is not in the netlist. D61 was not edited.

The approval and the outcome are in DECISION.md. The gold wells stay the contact that charges more often.
