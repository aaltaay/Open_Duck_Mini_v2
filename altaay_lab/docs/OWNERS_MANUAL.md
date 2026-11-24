# Duckie owner's manual

A picture of the first page of this book is [images/owners_page.png](images/owners_page.png).

This manual is for someone who lives with Duckie. It is plain language.
It is not a certificate, not a lab report, and not legal advice.

Duckie has not been built. No step below has been done on a robot.
When a step needs a part or a measurement that does not exist yet, it says **BLOCKER**.

How the duck is assembled is [BUILD_GUIDE.md](BUILD_GUIDE.md).
That guide points at the part list, the screws, and the wires.
This page does not repeat them.

A number is marked so you can see what it is:

- **cited** means it comes from a decision or a spec the lab wrote down.
- **set point** means the software uses that number. It is not a measurement of your duck.
- **sim pass only** means a simulation. The real duck has not done it.
- **BLOCKER** means nobody has checked it on hardware, or the part is not designed.

## What Duckie does

Duckie is a small home robot that stands on two legs. It is meant to:

- walk on a flat floor
- sit down facing the room
- go back to a felt mat (the nest) when the battery is low, and charge there
- look around, blink, and move its ears while it listens or waits
- set a timer, save a reminder, tell the time, and answer a short hello
- in adult mode only, and only if a cloud account is turned on outside this book, look at mail or a calendar

The walk, the sit, and the dock have been tried in simulation. They have not been tried on a robot
([software/personality/PERSONALITY.md](../software/personality/PERSONALITY.md),
[software/autonomy/AUTONOMY.md](../software/autonomy/AUTONOMY.md)).
Getting up from a fall is also simulation only. Do not count on it in your house yet.

Duckie is not a toy for a child to carry while it is walking. The legs pinch. The battery is a
lithium pack. The stairs in a normal house are too tall for these legs, and this duck is not
built to climb them ([START_HERE.md](../START_HERE.md)).

What people actually keep a home robot for is discussed in
[software/companion/USEFULNESS.md](../software/companion/USEFULNESS.md). That note is a reading list.
It is not a promise that Duckie does those jobs today.

## First boot, with no keyboard

Duckie has no screen. After the Pi image is installed, the next start does not
need a keyboard. Nothing in this section has been done on a robot.
Status: **never done on hardware**. A desktop picture of these pages is a demo,
not the duck. The steps are written in
[software/owner/OWNER.md](../software/owner/OWNER.md).

1. When the setup service is on and this duck has never been set up, it speaks
   a pairing code. The code is 8 characters (set point). It is new for this duck.
   There is no factory password and no cloud account.
2. Join the Wi-Fi network it names. The name starts with Duckie- and the
   passphrase is that code. Open 192.168.4.1 (set point). A QR code on that page
   is the same network, for a second phone. Anyone who can hear the code can
   join until you save the page. Then the temporary network turns off.
3. Enter the code, a name, a timezone, and your home Wi-Fi. Kid mode is already
   selected. Leave it selected unless you mean to turn it off.
4. Save. The duck joins the home network.
5. From a phone on that home network, open port 8080 on the duck (set point).
   Enter the pairing code again. The page shows the battery, the last docks,
   the falls, and the knee temperature copied from the supervisor log, and it
   can download that log. It does not answer a device that is not on the home
   network. A number there is not a new measurement. A pack sensor on the Pi
   is **BLOCKER**.

The camera stays on the duck. Frames are not uploaded. The microphone stays on
the duck. Audio is not uploaded.

## Updates

An update is a signed bundle. The duck checks it with the public key in
[software/owner/update_public_key.pem](../software/owner/update_public_key.pem).
The private key is not in this repository. Do not put one there. A production
key that a maintainer can sign with is **BLOCKER** until that private half is
created offline and this public file is replaced with its pair.

The install keeps two copies. After a new copy is selected, the duck runs a
self-test of the walk guards and one supervisor step. If either fails, it
switches back. That rollback is measured in emulation by the tests named in
[software/owner/OWNER.md](../software/owner/OWNER.md). It has not been done on
a robot. Status: **never done on hardware**.

## When the pack is low

At or under 10.0 V (cited, the pack walk stop) the low-pack service stops the
walk, the camera job, the voice job, and the supervisor, then it powers the Pi
off. It does not do that while the log says the duck is charging. If the log
has no voltage, it does not invent one and it does not power off. A pack sensor
on the Pi is **BLOCKER**. The shutdown itself is measured in emulation.
Status: **never done on hardware**.

A crash of the walk, the supervisor, the voice job, or the camera job is
restarted at most 3 times in 300 seconds (set point). Each of those jobs is
expected to answer a watchdog within 15 seconds (set point). The first-boot
service uses 30 seconds (set point). A guard stop of the walk is not restarted.

## Setting up the nest

The nest is a felt mat against a wall. Duckie walks onto it, turns around, and sits facing the room
with the motors off. The mat to use is version 2. Versions 3, 4, and 5 are experiments.
Do not cut those. Do not put pins in the feet. Do not put spring pins under the body.
The metal that touches the mat is five small gold domes under the seat
([twin/dock/camera/SEAT_CONTACTS.md](../twin/dock/camera/SEAT_CONTACTS.md)).

Pictures: [images/nest_mat_top.png](images/nest_mat_top.png),
[cad/nest_v2/renders/sit_three_quarter.png](../cad/nest_v2/renders/sit_three_quarter.png),
[images/gold_domes.png](images/gold_domes.png).

1. Put the mat against the wall, the way [cad/nest_v2/NEST_V2.md](../cad/nest_v2/NEST_V2.md) describes.
   The drawn distance from the mark called the sun to the wall is 190 mm (cited in that file).
   Status: **never done on hardware**.
2. Leave the wall card off until the owner of the project says yes. An earlier decision said no markers.
   The card is still drawn on the model. That is not permission to stick it up.
   Status: **never done on hardware**.
3. Plug the nest cord in only after the safety gate in the next section is real.
   That gate is **BLOCKER**. It has not been designed. Until it exists, do not leave the mat powered.
4. If you move the mat, Duckie has to find it again with the camera. There is no tag to scan.
   A camera find on a real Pi is **BLOCKER**.

## Charging and battery safety

The pack is three Molicel P45B cells. The window written for it is 9.0 V to 12.6 V (cited, the wiring netlist).
Duckie is supposed to stop walking at 10.0 V (cited, decision D65).
The software also starts for home at 10.8 V (set point, 0.8 V above that stop).

The nest supply in the notes is 15.0 V (cited, [circuitry/SERVO_RAIL.md](../circuitry/SERVO_RAIL.md)).
That voltage must not go straight onto the leg motors. The charger sits inside the duck and feeds the pack.
The charger part named for this pack is a TI BQ24133 (cited, the netlist).
It does not have a mounting place yet. **BLOCKER.**

While Duckie is on the mat the leg power is supposed to stay off, so the motors rest on the sit stops
and the charger can finish ([circuitry/SERVO_RAIL.md](../circuitry/SERVO_RAIL.md)).
That circuit has not been built. Status: **never done on hardware**.

Rules until someone measures a real charge:

- Charge only while the cells are between 0 C and 45 C. The cell sheet allows up to 60 C. The home test is tighter ([TEST_PLAN.md](../TEST_PLAN.md) section 20.8). Neither limit has been measured on this duck. **BLOCKER.**
- Nearest plastic under 45 C during a full charge is the same test. **BLOCKER.**
- Do not charge a pack that is swollen, leaking, wet, or hotter than your hand can comfortably touch. Stop and leave it somewhere that is not on a soft chair.
- Do not leave Duckie switched on and alone after it has shut itself down for battery. Turn the main switch off. The old notes say a duck left on can keep draining the cells ([TEST_PLAN.md](../TEST_PLAN.md) section 11).
- A coin can bridge the bare stripes on the mat. The gap is 5 mm (CAD check only, [cad/nest_v2/NEST_V2.md](../cad/nest_v2/NEST_V2.md)). The circuit that should refuse a coin is not designed. **BLOCKER.** Do not leave the mat live.
- Dirt, hair, and felt dust on the gold domes have no measured resistance. **BLOCKER.** If a sit does not charge, wipe the domes and the stripes with a dry cloth and try once more. Then stop.
- The pack is spot welded in the lab. It does not have the shipping test summary US rules ask for when a lithium battery is shipped (49 CFR 173.185, as named in [COMPLIANCE_FIRST_PASS.md](../COMPLIANCE_FIRST_PASS.md)). **BLOCKER.** Do not mail the pack. Do not put it on a plane.
- Do not ship a finished duck either. Certification is not done. See the last section.

A full charge on the hardware has never been done.

## Voice commands and kid mode

Speech runs on the duck, not in this paper manual. The wake phrase the software strips off is
"hey jarvis" ([software/companion/assistant.py](../software/companion/assistant.py)).
Timing on the real Pi is **BLOCKER** ([software/companion/LATENCY.md](../software/companion/LATENCY.md)).
Nothing here has been spoken to a robot. Status: **never done on hardware**.

Say the wake phrase, then one of these. The words are the ones the assistant actually looks for:

| You say | What the software does | Kid mode |
|---|---|---|
| set a timer for 5 minutes | Stores a timer. No cloud. | Works |
| remind me to stretch | Stores the note on the duck. | Works |
| remind me to stretch in 10 minutes | Stores it and can fire later. | Works |
| what time is it | Reads the clock on the duck. | Works |
| what is the weather in Chicago | Asks a weather service if the network works. No account key. | Works. If the network is down it says so. |
| go home | Starts the dock names already written. It does not, by itself, prove the duck can find the mat. | Works |
| go charge | Same as go home. | Works |
| good night | Night light flag. Eyes are meant to stay bright white. The demo does not drive the pins yet. | Works |
| night light | Same as good night. | Works |
| hello | A short hello. | Works |
| what is a duck? | An open question. In kid mode, or with the cloud off, the answer is: I can set a timer or a reminder. It does not call a model. | That same refusal |
| check my email | Refused in kid mode. | Refused |

Kid mode refuses mail, calendar, and open questions. Timers, reminders, the clock, weather, the night light,
and going home still work ([software/companion/ARCHITECTURE.md](../software/companion/ARCHITECTURE.md),
[software/personality/PERSONALITY.md](../software/personality/PERSONALITY.md)).

How a home turns kid mode on is the first-boot page above. It starts on.
Only the word adult on that page turns it off. A switch on the body that a
child can see is still **BLOCKER.** Until the first-boot page is saved, treat
the duck as kid mode: do not connect mail or a calendar.

Adult mail and calendar need a cloud key kept outside this repo. Do not write a key into a file in the project.
If the key is missing, those jobs stay off.

## What the expressions mean

The eyes stay white (cited, decision D57). Brightness and blink names are for the eye thread.
The beads on the duck today are on or off, not a measured dimmer.
How fast a real ear moves is **BLOCKER**.

The expression names are the ones in [software/personality/expressions.py](../software/personality/expressions.py)
and [software/personality/PERSONALITY.md](../software/personality/PERSONALITY.md).
The last row is a voice flag, not one of those names.
The expressions have been drawn in simulation. No servo has moved. Status: **never done on hardware**.

| What you see | Name | Meaning |
|---|---|---|
| Head tilted, ears up, eyes bright, steady blink | curious tilt | Listening |
| Head turns toward the caller, only if a cloud mock is actually in use | look_at | The assistant phase is called thinking. The expression name is look_at. |
| A nod | nod | Speaking |
| Head settles back to centre | settle | Done |
| Head shake, double blink | shake | Refused. Mail in kid mode does this. |
| Ears up, a small wiggle, eyes bright | happy wiggle | A pleased mood |
| Head low, ears down, slow blink | sleepy droop | Quiet, or a nap. A nap in the supervisor is 15 minutes (set point), then it tries to stand. |
| Ears up, double blink, a short peep | startled | A timer just fired |
| Looks toward a person | look at | A reminder is due and it was shown a face. The face finder on this Pi is **BLOCKER**. |
| A small nod toward someone, ears up | greeting | Hello |
| Slow look from side to side | bored glance | Nobody is around |
| Sitting, head up, slow blink | seated alert | Sitting and still awake |
| Head up, ears pointed opposite ways, eyes bright white, double blink | help me | It has given up and is waiting for a person. See the next section. |
| Eyes held bright white after good night | not an expression name | A voice flag. The beads are not a measured lamp. |

A fall, a hot knee, or a battery that is too low comes before any of these greetings.
Duckie should sit. It should not keep walking to finish a hello.

## When it asks for help

The help pose is the last row above: head up, ears opposite, eyes bright white.
A pet or a pickup is what clears it in the software
([software/autonomy/AUTONOMY.md](../software/autonomy/AUTONOMY.md)).
The pose is not a walk. Do not expect it to stand just because you talk.

It asks in these cases. All of them are written in software. None have been seen on a robot.
Status: **never done on hardware**.

- Dock: it tries the camera dock, and it may retry. The papers' own cap is two retries. After that it sits in the help pose. In one simulated day this did not happen to line up. The unit tests do show the pose. A real camera is **BLOCKER**.
- Fall: it tries a flat-floor get-up that works in simulation only. Two misses, and it shows the same pose. A hot knee or a pack at or under 10.0 V holds the fall. It should sit with the motors off instead of spending current. A fall rate on a real floor is **BLOCKER**.
- Nest fault, as described for a person running the mat: if the charger says it is not charging and the pack is not rising, sitting again in the same bad spot is not the fix. The note says stand off, try one more approach, then stop and hold the eyes steady. That sequence was not simulated. **BLOCKER** ([cad/nest_v2/NEST_V2.md](../cad/nest_v2/NEST_V2.md)).

What you should do:

1. Turn the main switch off if the duck is buzzing, hot, or you cannot tell if the motors are on.
2. If it is only waiting, the help pose, you can pet it or lift it. Support the body. Do not pull a leg.
3. Put it on the mat by hand if it did not get there. Do not leave it on a live mat until the coin gate exists.
4. If a knee was hot, let it sit until it is cool. The walk-again line in software is 45 C (cited set point). There is no thermometer on the outside of the duck for you to read. **BLOCKER** for a home reading.

## Cleaning

No cleaning method has been tried. Status of every line in this section: **never done on hardware**.
A solvent, a soap, and a washing machine are **BLOCKER**. Do not invent one.

1. Switch the duck off. Unplug the nest. Wait until nothing is warm.
2. Wipe the plastic shell with a dry soft cloth. Do not soak it. The body is printed plastic.
3. Shake the felt. Do not machine wash it. Water on the metal stripes is a short until the gate exists.
4. Wipe the five gold domes with a dry cloth. Dirt on gold is an open **BLOCKER**, not a finished cleaning spec.
5. Do not oil the joints. Do not spray anything into the head, the mic holes, or the camera.
6. Do not open the battery bay unless you are the person who built it, and the switch is off, and the nest is unplugged.

## Troubleshooting

| What you see | What it usually means in the software | What to do | Tried on a robot? |
|---|---|---|---|
| Help pose: head up, ears opposite, eyes bright | Dock retries or fall retries are used up | Pet or lift. See the help section. | Never done on hardware |
| Sits and will not walk after a long walk | Hot knee. Stop at 55 C, walk again at 45 C (cited set points) | Let it rest. Do not keep asking it to walk. | Never done on hardware |
| Heads for the mat while it can still walk | Pack at or under 10.8 V and above 10.0 V (set point and cited stop) | Clear a path to the mat. Do not stand on the mat. | Never done on hardware |
| Sits and will not get up, pack very low | At or under 10.0 V it should sit, not walk | Turn it off or put it on the nest by hand. | Never done on hardware |
| Refuses mail or a question | Kid mode, or the cloud is off | That is the safe answer. Do not bypass it for a child. | Never done on hardware |
| Weather answer fails | Network down, or the city was not understood | It should say the network is needed. Try again later. | Never done on hardware |
| You said go home and it does not move | The words only name the dock program. Vision and charge are **BLOCKER** | Carry it to the mat. Do not expect a search until those blockers close. | Never done on hardware |
| Motors stay stiff after you think you stopped | A stop can leave the last target in the servos ([software/PI_SETUP.md](../software/PI_SETUP.md)) | Hold the body. Switch off. Then open the battery disconnect plug, with the switch already off ([BUILD_GUIDE.md](BUILD_GUIDE.md)). | Never done on hardware |
| Mat does not charge | Domes not touching, dirt, or the charger is not fitted. The board seat is **BLOCKER** | One dry wipe, one more sit. Then stop. Do not raise the nest voltage. | Never done on hardware |
| Plastic smells hot, or a cell case looks swollen | Stop. This is not a software mood. | Switch off, unplug the nest, move it off soft furniture, and do not charge it. | Never done on hardware |
| It falls | Get-up is simulation only | Pick it up if the help pose does not clear. Check the shell for a crack before another walk ([TEST_PLAN.md](../TEST_PLAN.md) section 9). | Never done on hardware |
| The setup page never appears | The setup service is off, or this duck was already set up | The temporary network exists only before the first save. | Never done on hardware |
| An update did not stay | The self-test failed and the previous copy is back | Leave that copy running. Do not copy a private key onto the duck. | Measured in emulation. Never done on hardware |

## Safety around people

- Fingers, hair, and pet tails stay out of the hips, knees, and neck while it moves.
- First walks, when they happen, belong on a soft floor with a person behind the duck ([TEST_PLAN.md](../TEST_PLAN.md) section 9). That choice is still open. Status: **never done on hardware**.
- Do not let it walk near stairs, a pool, or a street. It is not a stair climber.
- The camera is for finding the nest and, later, a person you show it. Frames are not uploaded, and audio is not uploaded. A light on the body that shows the camera is on is not written. **BLOCKER.** There is no face library in this design ([software/companion/ARCHITECTURE.md](../software/companion/ARCHITECTURE.md)). A reviewer demo of that behaviour on a robot does not exist. **BLOCKER** ([DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) gate 6).
- Children can use timers, reminders, the clock, weather, the night light, and go home. They do not get mail, calendar, or open questions. The first-boot page starts in kid mode. A switch on the body is **BLOCKER**.

## Safety marks and FCC

**BLOCKER. Certification is not done.** Do not sell Duckie. Do not ship Duckie. Do not treat this manual as approval.

Placeholders, each one open on purpose:

- **BLOCKER.** FCC equipment authorization for the finished duck, as a host that hides or surrounds the Pi radio, is not done. 47 CFR 15.212 is the rule named in [DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) gate 6. The grant id was not read onto a label for this body. The Pi board's own mark is for the board. A case and the other devices can change the result ([COMPLIANCE_FIRST_PASS.md](../COMPLIANCE_FIRST_PASS.md)).
- **BLOCKER.** An unintentional-radiator check of the finished duck is not done.
- **BLOCKER.** Which UL or IEC charge standard applies was not opened. There is no lab report for charge temperature or the adapter.
- **BLOCKER.** The pack has no UN 38.3 test summary. 49 CFR 173.185 is the US shipping rule named in the compliance note. Do not ship the pack.
- **BLOCKER.** The mat is a live contact while charging, and the gate that should keep it dark is not designed. Do not leave it powered in a home.
- **BLOCKER.** A label on the outside of the body, a manual statement of radio frequencies, and a responsible party for a US sale are not filled in. [compliance/COMPLIANCE.md](../compliance/COMPLIANCE.md) is a research note, not a filing.

When a real certificate exists, this section should name the grant, the lab, and the date.
Until then the word is BLOCKER, and the duck stays in the lab.
