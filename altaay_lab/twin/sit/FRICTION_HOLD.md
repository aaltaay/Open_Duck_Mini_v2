# Felt friction, backdrive, and a small holding torque

2026-11-13 ET. Separate from the rail interlock. Nothing was bought. The mat is not redrawn.

## What was looked for

A number for wool felt against the TPU seat or the PLA shell, and a number for the unpowered backdrive torque of the ST-3215, were not found on a datasheet or a paper that this note can cite. The Feetech C001 page and the C018 page still do not print a gear friction or a backdrive torque. A web search did not return a felt-on-plastic coefficient from a standards table or a servo sheet. The contact twin already marks sole friction on felt as BLOCKER. That mark stays.

The seated hold therefore stays BLOCKER until the bench below is run. The 20 s sim that keeps the wells down uses the training frictionloss of 0.068 Nm, which is not the sheet.

## Bench, spring scale

Unpowered duck, D59 sit, on the nest v2 mat. A spring scale is enough. No new part.

Seat, felt against the shell:

1. Mark the seat where it meets one stripe. The well is 3 mm on a 20 mm stripe, so 8.5 mm of cross-stripe room if it starts centered (calc only, (20 - 3) / 2).
2. Hook the scale to the trunk at the measured sit height, pull across the stripes, and raise the force in about 1 N steps. Hold each step for 5 s.
3. Also pull along the stripes, the same steps.
4. Pass: the seat mark moves less than 8.5 mm at 5 N, both directions. 5 N is the middle push already used in the sit study. Fail, or any tip: the unpowered sit does not hold, and this BLOCKER stays.
5. Write the breakaway force in newtons. That is the measurement. It is not a coefficient until someone also records the normal force under the seat.

One hip-roll servo, unpowered, off the duck or with the link free:

1. Set the horn so the scale is perpendicular to a 100 mm arm (calc only, torque = force times 0.10 m).
2. Increase the force until the horn moves 5 deg. Torque at that force is the breakaway.
3. The gravity torque on one hip roll at the sit, with friction set to 0, is 0.226 Nm (sim pass only, hold_torque.py). Pass for that joint replacing friction: breakaway at or above 0.23 Nm. Below that, the sheet still has no number, and the joint will not hold its own weight.

## If friction is zero, can two or three servos hold the sit

Kt is 1.090 Nm/A (calc only, 2.942 / 2.7, the C018 stall line in problems/STS12.md). The current below is the gravity torque divided by that Kt. It is not a measured motor current. Electronics idle on top of it is not added: the C018 page prints 180 mA no-load while spinning, not a holding idle.

The sim puts joint friction, joint damping, and floor friction at 0 after the powered sit, then applies only the gravity torque on the named joints. Sim pass only. Every run went unstable. None kept the seat down for 8 s.

| Joints | Current | Under 0.10 A | Seat held |
|---|---|---|---|
| two hip rolls | 0.412 A | no | no |
| two knees | 0.216 A | no | no |
| neck and head pitch | 0.191 A | no | no |
| two hip pitches | 0.066 A | yes | no |
| two hip pitches and one ankle | 0.074 A | yes | no |

The sets that fit under 0.10 A are the small gravity torques. They do not keep the seat when the hip rolls, the knees, and the head are free. The sets that include a hip roll or a knee are already over 0.10 A, so current termination cannot finish while they draw from the pack, and they still did not hold the seat in this zero-friction run.

Workaround, already in the interlock: the Pi end-charge line pulls ISET below 40 mV and the charger disables (cited). That is how a later, larger holding current can exist without waiting for the 0.10 A termination. It does not make the zero-friction sit stable. The bench above is what decides the hold.
