# Nest mat, version 5

Not an approval. nest v2 and D61 are not changed. Nothing was bought.

Every number is **sim pass only**, **calc only**, **CAD check only**, or **cited**. Anything else is a **BLOCKER**.

## The pattern

The v4 miss was depth. One 56 mm strip only covers about 93 mm of trunk depth. This mat repeats that strip along the depth.

The two plates are the v4 plates: seat 32 by 40 mm, bumper 24 by 40 mm. Their centres are 130 mm apart. The empty gap between them is 102 mm (CAD check only).

A pitch of 102 mm would be a 46 mm copper band plus the 56 mm strip. At a straight sit that covers about 40 percent of depths (calc only). The 32 mm seat does not have much room in a 46 mm band once the heading smears it.

The pitch used here is 130 mm: a 74 mm copper band, then a 56 mm felt strip, then the other pole, then another strip. The plate centres are one step apart, so they want opposite bands. At a straight sit this covers 71 percent of a 400 mm depth. With heading up to 14 deg either way, and the duck facing the room or the wall, the share is 68 percent (3604 of 5280 samples, calc only, plates 0.3 mm fat). The phase is placed so that 28 of 32 recorded v4 sits land on opposite bands (calc only).

## Zero shorts by construction

With 0.3 mm of growth on every edge, the seat diagonal is 52.1 mm and the bumper diagonal is 47.5 mm (calc only). Every felt strip is 56 mm. A plate shorter than the strip cannot reach both sides of it, so it cannot touch a plus band and a minus band. The sweep in test_layout.py finds 0 shorts at every heading. The 40-seed run also found 0 shorts, including the print and felt re-settles.

The walk stands on one flat mat. That box is stretched to the copper layout, from x = -550 mm to x = 184 mm, so a plate on a room-side band has a surface under it. The bands are paint on that mat, not a second set of collision boxes. Splitting the walking surface into separate boxes made the dock time out (17 of 40, an earlier run). That surface is not the one in this result.

## The 40 seeds

Same starts. Run D. The dock program is the camera dock. A stand-up and a short walk toward the room, as a retry when the sit missed, was tried on three seeds. All three fell. It is not in this run. Sim pass only.

Charging docks: 25 of 40.
Geometric docks: 27 of 40.
Shorts: 0 of 40.
Falls: 4 of 40.
Timeouts: 2. No mark: 1 (seed 32).
The other misses sat with a half off the copper.

This does not beat 38 of 40. It does not keep the fall count of the v4 run (1 fall).

On a charging sit the lighter half is at least 1.40 N (seed 31) and the chip input is 14.911 V to 14.917 V, inside 4.5 V to 17 V.

Print 0.3 mm either way, and a 0.4 mm felt dent: 25 charge, 0 shorts (re-settle, not a new walk).

A 20 s run D walk does not fall and does not scrape. Closest belly point 84.7 mm (sim pass only).

The sense-then-15 V gate is the one in NEST_V3.md. The bridge still sorts which band is plus.

## Clips

twin/out/videos/belly_v5_charge.mp4 is a charging sit, lamp green, caption sim pass only, 1280 by 720.

twin/out/videos/belly_v5_charge_fail.mp4 is seed 7. The sit misses the copper. The lamp stays dark. It is not a short.

## Still BLOCKER

304 on copper, wear, finger and spill resistance, copper sheet and felt prices, and the sense board not in the netlist.
