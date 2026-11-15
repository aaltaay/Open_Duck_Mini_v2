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
| Five well disks on the duck, this choice | Collision only, at the CAD face, 3 mm across, 1 mm thick, density 0 | After the gains drop, 2.17, 1.96, 1.74, 1.53, 1.35 N. The soles still carry 10.5 N and 10.0 N | 14 of 20 and 10 of 20, 24 of 40 | yes (up 0.999, trunk 62.3 mm) | about 0.7 g of gold if the disks are solid (calc only, 5 times pi times 1.5 squared times 1 mm times 19.3 g/cm3). These are the wells already drawn. No new part, no new price |
| A thicker mat or a raised foil | Nest change | not tried |  |  | would change the approved flat mat |

The pose alone does not make a charge, because the force needs a body. The well disks are the smallest duck-side change that produces a force. The mat was not changed.

With those disks in the dock model, the original 20 seeds are 20 geometric docks and 14 charging docks. The 20 new starts are 19 geometric docks and 10 charging docks. Together that is 24 charging docks out of 40. Median time 33.5 s and 31.8 s (sim pass only). A dock that does not charge has the seat load on one well, so the other pole is open. The centred sit above does charge: contact resistance 0.012 ohm, 14.95 V at the chip, 0.012 W in the contacts (sim pass only, the ohms are the stated assumption).
