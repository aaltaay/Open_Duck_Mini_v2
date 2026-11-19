# What Duckie feels like

Written 2026-11-16 ET. This is the personality layer. It sits beside the walk, not inside it. The 50 Hz walk thread is left alone. Nothing here needs a cloud account.

## What it does, and why

Duckie keeps a small mood: how pleasant things feel, how awake it is, how curious it is, and how much it wants company. Those numbers ease back toward a calm middle. The time constants are set points: 12 s, 8 s, 18 s, and 14 s. They are not a measurement of a feeling.

Energy comes from the pack voltage, or from the battery guard's servo reading when the pack voltage is not there. A full pack is 12.6 V and the walk stops at 10.0 V (cited, the pack window and the pack walk cutoff). Energy is 0 at 10.0 V and 1 at 12.6 V (calc only, from those two cited ends).

When the pack is still above 10.0 V but at or under 10.8 V, Duckie heads home. 10.8 V is a set point, 0.8 V above the cited stop, so it can still walk. Home means the dock states that are already written: APPROACH, STEER_DOCK, ACTIVATE_CHARGER. It does not invent a new walk. If the pack is already at or under 10.0 V, or the servo median is at or under 6.0 V (cited, the battery guard), it sits. It does not keep walking. A hello, a reminder, or a timer does not drop that last reading.

A hot knee (55 C stop, 45 C to walk again, cited, the knee heat guard) or a fall also sits, ahead of going home and ahead of saying hello. A fall stays until something says it stood up. Getting up from a fall is not in this program.

If none of that is wrong, people come next. A wake word, a face, a pet or a pickup, a timer, or a reminder changes the mood and the pose. With nobody around it glances about. If it has been still and drowsy it droops. While it is sitting and still alert, the head stays up. If it has been sitting 25 s (a set point) and is very quiet, how awake it is eases toward 0.10 (a set point) instead of the usual 0.35, and it naps.

A reminder is stored by the assistant, on the duck, with no cloud. When it comes due, Duckie looks around. If it is shown a face, it walks toward that person. When the face is close, it nods and the reminder counts as delivered. The face and the sound direction are handed in. This program does not find them.

The eyes stay white (D57). Brightness and a blink name (steady, slow, double, off) are for the eye thread. The beads today are on or off, not a measured dimmer. The ears use the antenna value from -1 to 1 (cited, the Runtime). How fast a real ear servo moves is still BLOCKER.

Assistant lines show on the body:

- listening: a curious tilt
- thinking: a look toward the caller (only if the mock cloud is actually used)
- speaking: a nod
- done: a settle back toward center
- refused: a head shake

Kid mode still refuses mail, calendar, and open questions. Timers, reminders, the night light, and going home still work. The night light holds the eyes bright and white.

If the autonomy supervisor gives up, it asks for the help_me pose. The head stays up, the ears point opposite ways, and the eyes stay bright white, so a person can see that the duck is waiting. A pet or a pickup clears that pose. The pose is not a walk. Getting up from a fall is still not decided in this file. The supervisor is the program that runs the get-up.

## The picture

twin/out/videos/personality_demo.mp4 is a scripted day on the run D policy. Sim pass only. It is 43.22 s, 1280 by 720, 20 frames a second. The file is 508870 bytes. The caption names the mood and the event, and it says sim pass only.

The scene is the playground flat ground at pin b9be205, plus a green stand-in for a person and a brown mark for home. It is not the pack circuit.

Standing, the four head joints are driven by this program. A 0.40 rad yaw command through the policy channels alone missed by 0.26 rad (sim pass only). The same command, written onto the head joints, missed by 0.002 rad (sim pass only). The infer script's own line that would copy the head command onto the joints is commented out, which is why the miss is large.

Walking, the head command goes in the channels the policy already reads, and the joints are not overwritten. During the walk home the yaw miss averaged 0.108 rad (sim pass only). The forward command was 0.15 m/s, inside the run D range of -0.15 to 0.40 m/s (cited, joystick_runD.py). The duck did not fall. It stopped near the brown mark (end x 0.924 m, the mark is at 1.20 m).

Ears and eye beads are not in that scene. The caption is the only place they show.

## Not proven on hardware

- No servo has moved. Every head target is inside the command box (the tighter of the cited joystick ranges and the calc soft stops in servo_limits.json) and under the cited 5.24 rad/s clip. That is a check in software, not a move on a duck.
- The mood times, the 10.8 V home line, the blink names, and the ear slew are set points.
- A face finder and a sound direction on this Pi are BLOCKER.
- Nest vision is BLOCKER. Naming the old dock states does not dock the duck. The brown mark is not the nest.
- Charge current is BLOCKER. There is no charge program.
- Sit from a walk, and stand from a sit, are not trained. The clip ends standing.
- Getting up from a fall is not written in this file. The autonomy supervisor runs the cited get-up and then calls stood_up.
- How kid or adult mode is chosen, and how a privacy choice shows on the body, are still open.
- Wake word, speech to text, and speech out on this Pi are still BLOCKER (SOFTWARE.md).
