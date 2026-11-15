# Proud wells, a trimmed bumper, and a spring pin

Simulation only. The flat mat is unchanged. D61 was not edited. The flush face, with every well 0.36 mm clear and 0 of 40 charging, is SEAT_WELLS.md.

The approved nest says the wells are flush and nothing sticks out of the duck (cad/nest_v2/DECISION.md). Springs are not on the duck (NEST_V2.md). These three options are duck-side trials against that line.

The print band is plus or minus 0.3 mm on the height that was changed. The placed sit is the dock sit, gains off. A well force under 0.294 N (30 g, Samtec gold note, 23 Sep 2022) is not a contact.

## What was measured

| Option | Height | Well force in the placed sit | Low band, minus 0.3 mm | High band, plus 0.3 mm | Fits the approved nest |
|---|---|---|---|---|---|
| Dome, 1.5 mm radius | 0.3 mm proud | 0 N. Still short of the 0.36 mm gap | 0 N | 1.5 to 2.1 N, all five | No. Something stands out |
| Dome | 0.6 mm proud | 1.5 to 2.1 N, all five | 0 N | 1.5 to 2.1 N | No |
| Dome, this choice | 0.9 mm proud | 1.5 to 2.1 N, all five | 1.5 to 2.1 N at 0.6 mm | 1.5 to 2.1 N at 1.2 mm | No. 0.9 mm stands out of the face |
| Dome | 1.2 mm and 1.5 mm | 1.5 to 2.1 N, all five | still over 1.5 N | still over 1.5 N | No. Taller than it needs to be |
| Bumper lifted until the seat pitch is flat | 3 mm of bumper trimmed off | The solver assigns about 1.7 N to each flush disk. That is one contact point per constraint, not the area of the disk. The seat region carries about 10 N. The disk is 0.28 percent of the 32 by 80 mm face, so the share is about 0.03 N | same rest | same rest | Closer. The bumper stops being the low point, which is what the cute sit wanted. It does not put 0.294 N on a flush well |
| Mill-Max 0906, spring 76 | tip 0.99 mm proud, the full stroke | 0.52 N on each well, and the face also carries 5.8 N | 0.18 N at 0.69 mm proud, under the floor | about 1.5 to 2.2 N, and the face never lands | No. DECISION.md dropped springs on the duck |

A 1 mm or 2 mm bumper trim still leaves the wells clear. At 4 mm and 5 mm the pitch tips the other way and the wells are clear again. Only the 3 mm trim lays the face flat, and the flush disk still does not own enough of that load.

The spring is Mill-Max 0906-0-15-20-76-14-11-0. Stroke 0.991 mm, mid stroke 0.495 mm, 25 g at first touch, 60 g at mid stroke, 20 milliohm, 2 A continuous (Mill-Max data sheet, the Farnell copy, and the element14 listing). The DigiKey page opened 2026-11-12 lists 0.86 USD at quantity 1 (BOM.md). Five pins are 4.30 USD (calc only). The sim pair uses a 0.65 s time constant so a nearly full stroke sits at 0.52 N, next to the cited 60 g (0.59 N). Mass of the pin is not on the opened sheet. The low band fails the 30 g floor, so the pin does not survive the print tolerance.

## The 0.9 mm dome

This is the shortest dome whose low band still presses every well. The gold is the well already drawn, formed proud. A solid cap 0.9 mm tall on a 1.5 mm radius is about 0.06 g, and five are about 0.29 g (calc only, a spherical cap at 19.3 g/cm3). No new part and no new price. The foil dollars stay BLOCKER.

In the hard contact the dome sinks about 0.02 mm, a patch about 0.25 mm across (calc only, square root of 2 times radius times sink). At about 1.9 N that is about 10 MPa. Pressed wool felt is 0.6 MPa (Kartofelev and Stulov, Forum Acusticum 2014). A patch held at that modulus under 1.9 N is about 3.2 mm2, a dent about 0.4 mm deep on this dome (calc only). The top felt sheet is 1 mm (NEST_V2). No crush strength for the craft sheet was found. The wear risk is a dent in that sheet under each dome, on the order of the sheet's own thickness, if the sheet yields near the wool modulus. That is an assumption, not a measurement.

A 6 s run D walk with the domes ends at the same place as the walk without them (x -1.476 m, y -0.134 m). No seat, bumper, or well contact during the walk.

With the 0.9 mm domes in the dock, the original 20 seeds are 20 geometric docks and 20 charging docks. The 20 new starts are 19 geometric docks and 18 charging docks. Together that is 38 charging docks out of 40 (sim pass only). Median time 33.5 s and 31.8 s. Seed 32 never sees a mark. Seed 29 sits on the stripes but loads one well only, 8.6 N, so the other pole is open and the lamp stays dark. On a charging sit the five wells read about 2.2, 2.0, 1.8, 1.6, and 1.4 N, the chip sees 14.96 V, and the contacts dissipate 0.005 W (sim pass only, the ohms are the stated assumption).

`dock_charge.mp4` is seed 1. The lamp turns green. `dock_charge_fail.mp4` is seed 29. The lamp stays dark.

The mat was not changed. The dome does not meet the flush line. It is the duck-side option that still charges when the print is 0.3 mm short.
