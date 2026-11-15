# Why the wells did not charge

Simulation only. The flat mat is unchanged. D61 was not edited.

## What the sit design assumed

The approved sit (sit_pose.json, cute sit) puts the seat's lowest point on the felt and the soles 0.3 mm into it. The bumper is 3.36 mm above the felt. Trunk pitch in that file is 2.79 deg. The five gold wells are flush in the seat, 3 mm across, at y = -24, -12, 0, +12, +24 mm. The seat mesh face in the trunk is at z = -66 mm (sit_cad.json bbox). Nothing sticks out of the duck.

## What this walk model actually does

The dock sit commands the software stops: knee 147 deg, ankle -90 deg. Those are inside the hard stops (knee 150, ankle -95, servo_limits.json). This measurement places the duck and runs that sit, the same ramp the dock uses.

With the gains on, and with the well shapes turned off so they cannot hold the duck, the trunk is at 76.7 mm. The five well faces sit above the mat by 6.79, 6.81, 6.84, 6.86, and 6.88 mm (y = -24 to +24 mm). The left sole carries 13.8 N and the right sole 16.0 N. Every well is 0 N. Knee torque is 0.01 N m, ankle 0.007 N m. The stall is 2.94 N m (30 kg cm at 12 V, sts12.py).

After the gains go off, the trunk drops to 55.7 mm. The five faces are then 15.91, 15.85, 15.79, 15.73, and 15.67 mm under the mat. The duck stays up (up 0.999). The soles still carry it, 20.3 N and 17.7 N, because the walk model has no collision shape for the seat or the wells. That is why 0 of 40 docks counted as a charge.

## Options

| Option | What changes | Well force | Charges | Stays up after torque off | Mass or cost |
|---|---|---|---|---|---|
| Pose only, to the hard stop (knee 150, ankle -95) | The dock sit, still inside servo_limits.json | 0 N. Held, the five faces are still 6.95 to 7.04 mm above the mat. After the gains drop the faces are about 15 mm under the mat and the soles still carry 12.6 N and 17.0 N | 0 of 40, because there is still no well body | yes, in that one sit (up 1.0) | none |
| Five well disks and no seat face | Collision only, 3 mm across, 1 mm thick, density 0 | 2.17, 1.96, 1.74, 1.53, 1.35 N in a centred sit. The duck was balancing on the pins | 14 of 20 and 10 of 20 in that model | yes (up 0.999) | no new part. Not the real duck: the face was missing |
| Seat face, bumper, and flush wells. This model | Boxes on the sit_cad.json bbox, wells flush in the face, density 0 | Seat edges 8.2 N, bumper 13.1 N, each well 0 N. The well faces are 0.36 mm above the mat | 0 of 40 | yes (up 1.0, trunk 70.7 mm) | none. The shapes are the parts already drawn |
| A thicker mat or a raised foil | Nest change | not tried |  |  | would change the approved flat mat |

## The face and the bumper

The pin model was the wrong duck. The real seat face is 32 by 80 mm and the bumper face is 24 by 60 mm (sit_cad.json). Both are in the dock model now, as boxes on that bbox, density 0, so the trunk mass does not change. The wells are cylinders whose bottom is the CAD face at trunk z = -66 mm. They hit the floor and not the soles.

Felt spring, stated from a citation and a simulator limit. Pressed piano-hammer wool felt has a static modulus of 0.6 MPa (Kartofelev and Stulov, Forum Acusticum 2014, static stress-strain tests). On this face and the 2 mm stack (NEST_V2, walking surface 2.00 mm) that is 768 kN/m, and 10 N sinks it 0.013 mm (calc only, E times area over thickness). A spring that stiff has a time constant under one 0.002 s step, which this sim will not hold. The contact uses solref -8000 -113 on the seat box, -4500 -85 on the bumper, and -44 -8 on each well, with solimp 0.95 0.99 0.001 0.5 2. A flat 1.2 kg block on that pair puts 0.035 N on each well. The area share is 0.033 N (calc only, pi times 1.5 squared over 32 times 80). The nest craft sheet is not piano felt. Its modulus is still the open felt grade (BOM).

With the gains off, at the dock sit and again at the hard stops (knee 150, ankle -95), the trunk settles at pitch -1.27 deg in the sign used here (the sit file's +2.79 deg is the other sign). The bumper carries 13.1 N and the seat face 8.2 N. The feet carry 7.6 N. The duck stays up. The five well faces are 0.36, 0.36, 0.36, 0.36, and 0.36 mm above the mat, so each well is 0 N. The face is tipped: its edges are on the mat and the wells, in the middle of the face, are not. Hip pitch from 40 deg to 65 deg, held and then released, comes back to the same rest. At 70 deg the duck flips. Holding torque at the sit hip is about 0.05 N m, under the 2.94 N m stall, but the hold is what the feet are doing. Once the gains drop, the hip is not against its stop, and the bumper, which is 3 mm lower than the seat in the body, rocks the sit onto itself.

A shuffle, a heading fix, or a lower ankle does not change that rest. A felt that sank 0.36 mm under the 8 N on the seat would close the gap. The cited wool does not. That softness was not found for this sheet, so it was not put in the model. The mat was not changed.

## The 40 seeds with the face

Original 20: 20 geometric docks, 0 charging. Median time 33.5 s. New 20: 19 geometric docks, 0 charging. Median time 31.8 s. The one miss still never sees a mark. Every well force in both sets is 0 N. Together that is 0 charging docks out of 40 (sim pass only). The lamp in dock_charge.mp4 stays dark for that reason.

A 6 s run D walk with these shapes, and the same walk with them turned off, ends at the same place (x -1.476 m, y -0.134 m). No seat, bumper, or well contact occurs during the walk. The sole collision flags were changed so the seat does not hit the feet. Putting the old sole flags back gives the same 6 s place. This is not the 45 minute walk.

## Decision for Ahmed

The flush wells do not touch once the gains drop, because the bumper rocks the seat and the wells sit 0.36 mm clear. Nothing on the duck that stays inside the joint limits and then goes limp fixes it. Closing it wants one of these, and this note does not pick:

1. Hold the hip after the sit, so the trunk keeps the 2.79 deg pitch that lifts the bumper clear. That is not torque-off.
2. A hip stop at the sit angle, so the limp duck cannot rock onto the bumper. That is a new stop.
3. A craft-felt modulus soft enough to sink about 0.36 mm under the seat load. The grade is still open. It is not a mat redesign, and it is not in this sim.
4. Leave the score as it is: a geometric dock, and not a charge, until a bench says otherwise.
