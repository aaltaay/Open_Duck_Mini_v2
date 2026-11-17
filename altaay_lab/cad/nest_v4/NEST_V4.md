# Nest mat, version 4

A follow-up to the nest v3 study. Not an approval. nest v2 and D61 are not changed. Nothing was bought.

Every number is **sim pass only**, **calc only**, **CAD check only**, or **cited**. Anything else is a **BLOCKER**.

## What changed from v3

v3 shorted when the bumper half crossed the 24 mm strip. Here each plate is the full depth of its shell and only 40 mm wide. The fat diagonal, with 0.3 mm of print growth on every edge, is 52.1 mm for the seat and 47.5 mm for the bumper (calc only). The felt strip is 56 mm, wider than both. A rectangle shorter than the strip cannot touch both pads, at any heading and any depth. The check is `test_layout.py`. The 40-seed run found 0 shorts, and the print and felt re-settles found 0 shorts.

The strip is centred at x = -230 mm, where this walk actually sits after the turn. Rear pad (wall side) is plus. Front pad (room side) is minus. The front pad is extended to x = -500 mm so the bumper is not off the mat. The marks are not moved.

A raised felt lip was tried in the approach path. At 3 to 5 mm it stopped the duck on the way to the wall and the walk stalled or fell (sim pass only). It is not in this model. A negative forward command for 3 s moved the body about 10 mm the wrong way (sim pass only). This policy does not step backward. Turning around to walk back caused falls and timeouts in the trials, so the dock program is the same camera dock as the gold-well runs. The depth is set by where that dock already sits, not by a new creep.

## The belly

- Seat plate: 32 mm by 40 mm, dropped 5 mm from the CAD seat face so it shares the sit with the bumper.
- Bumper plate: 24 mm by 40 mm, at the CAD bumper bottom.
- 0.5 mm 304. Both plates are 8.8 g (calc only, 7.90 g/cm3, Sandmeyer sheet). The 5 mm seat standoff, if PETG at 1.27 g/cm3, is 8.1 g (calc only). The sim boxes stay density 0.
- The 4.99 k ohm sense resistor and the ideal-diode bridge are the same parts as NEST_V3.md. The pads stay at the sense voltage (about 3.35 V open, 0.945 V with the duck) until the window 0.80 V to 1.10 V enables the DMP3018SFV. A short reads near 0 V. An open reads 3.35 V. Both leave 15 V off.

## The 40 seeds

Same starts. Run D. Sim pass only.

Charging docks: 15 of 40.
Geometric docks: 20 of 40. Five of those press only one half hard enough.
Shorts: 0 of 40.
Falls: 1 of 40.
Timeouts: 6. No mark: 1 (seed 32).
On a charging sit the lighter half is at least 1.97 N and the chip input is 14.917 V. Inside 4.5 V to 17 V.

This does not beat 38 of 40. The misses are sits whose depth is outside the 93 mm band (trunk x from -324 mm to -231 mm, calc only, +/-14 deg, 0.3 mm fat, 4 mm of metal on the pad). The two halves are 102 mm apart in the body, so one strip cannot cover a wider band than that.

Print 0.3 mm short: the same 15 charge, 0 shorts. Print 0.3 mm long: 14 charge, 0 shorts. A 0.4 mm felt dent: 15 charge, 0 shorts. Re-settle, not a new walk.

A 20 s run D walk does not fall and does not scrape. Closest belly point 84.7 mm (sim pass only).

## Clips

twin/out/videos/belly_v4_charge.mp4 is seed 2. The lamp turns green. Caption: sim pass only. 1280 by 720.

twin/out/videos/belly_v4_charge_fail.mp4 is seed 5. The sit is too close to the wall, the bumper is off its pad, and the lamp stays dark. It is not a short.

## Still BLOCKER

304 on copper, wear, the real resistance of a finger or a spill, copper sheet and felt prices, and the sense board not in the netlist. Same list as the v3 study.
