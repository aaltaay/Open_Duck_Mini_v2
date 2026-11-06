# DOCK_TWIN: the V1 self-charging dock, phase 2 (track 8)

Written 2026-11-05 by the V1 dock job (track 8). Labels: sim pass only, calc only, CAD check only. Nothing was bought, printed,
built or tested on hardware. Decisions this follows: D37 (self-charge is a V1 must-have), D43 (contacts; the dock behaviour code
is a port of osrf/autodock), D44 (2S1P Molicel P45B pack), D45 (simplest, cheapest and most reliable at once). Ahmed, about
1:30 AM ET on 2026-11-05: "I'm also all about precision ... what about perception? Why don't we rely on perception as well?"

## 1. The answer in short

- **Behaviour code:** osrf/autodock (Apache-2.0, fd9c2a9) ported with no ROS to `altaay_lab/software/dock/autodock/`, the four
  upstream bugs fixed, and a duck layer on top. All motion goes through measured pulse tables in `duck_autodock.yaml`, so the
  retrained walk of track 10 (creep, symmetric turns, small sidesteps) can be swapped in by changing tables, not code. 15 unit tests.
- **Dock:** a 40 mm wide seat at 112 mm on a short spine between the feet, a **sprung, swivelling chest paddle** (40 mm travel,
  3 N at full travel, +/- 10 deg about a vertical pin so it lies flat on a yawed chest) with three spring pins, and a three-tag mast
  (tag36h11 id 0 at 40 mm in the centre, ids 1 and 2 at 60 mm, 200 mm apart).
- **Contacts on the chest, not the belly:** three strips 100 mm wide and 20 mm tall on the flat chest face (CHG+, SENSE, GND, top
  to bottom). The seat sets their height, the paddle takes up the stop error, the strip length takes the lateral error: the window
  is fore-aft 0 to 40 mm into the paddle, lateral +/- 49.5 mm, vertical +/- 9.5 mm, yaw +/- 10 deg. The belly is not cut (the pocket
  tried earlier is reverted). The feet set the tighter lateral limit: the soles clear the seat by about 22 mm a side.
- **Perception closes the loop to the paddle:** the side tags square the duck and set the dock axis, saved on the IMU yaw; the
  40 mm centre tag gives the range and the lateral offset down to about 6 cm from the camera, the last 3 to 5 cm before the stop
  are dead-reckoned. Then a scripted balanced crouch carries the chest 30 to 50 mm forward onto the paddle and the belly onto the seat.
- **Charge path:** a hardware gate, no microcontroller and no Wi-Fi (seat microswitch in series, NTC window, pin-voltage window, a
  555 wake pulse); charger Microchip MCP73213 (1.1 A, safety timer); the duck confirms charging with its own pack monitor.
- **Acceptance (sim pass only), 20 seeds per floor, bar 19 of 20 within 3 tries and no fall: not met.** Best run hard 18/20,
  train 16/20, soft 10/20 (sections 4.4 to 4.6); the precision at the seat is inside the pin window on every docked run. The soft
  floor is held back by the stock policy, which falls when it steps back on it.

## 2. Geometry (sim, STLs and duck side)

Dock frame: x toward the mast, the paddle face at rest is x = 0, z up from the floor, mm.

| Part | Where | Why (sim pass only unless stated) |
|---|---|---|
| seat | x -110 to -15, y +/- 20, top z 112 | a 60 mm seat was touched by a sole; at 40 mm the closest sole edge stayed 22 to 41 mm away |
| spine | x -15 to 30, y +/- 20, top z 90 | links the seat to the mast base |
| paddle | x 0 to 12 at rest, y +/- 55, z 140 to 220, slides 40 mm on two 4 mm rods, 75 N/m, swivels +/- 10 deg about a vertical pin at x 18, PTFE face (friction 0.15, ASSUMPTION) | a rigid bumper gave a 5 to 10 mm stop window; the sprung paddle takes any stop from 0 to 40 mm short of full travel; a fixed paddle left the pins 2.5 to 3.9 mm off a chest yawed 4.5 to 6 deg (acc6), the swivel lays it flat |
| paddle guide | a yoke (carrier) holds the pivot (two coaxial M3 x 20 screws) and the rods; the rods run through 4.4 mm bores in the mast face into two spring cups behind it, a shaft collar on each rod end, a 37.5 N/m spring in each cup | the 75 mm between the paddle face and the mast leaves no room for 40 mm of travel plus springs in front of the mast; CAD check: no overlap at 0, 20 and 40 mm of travel and -10, 0, +10 deg |
| pins | three Mill-Max 0932 in the paddle at y 0: CHG+ z 201, SENSE z 179, GND z 157 | one pin per strip; the MCP73213's 1.1 A is under the pin's 2 A continuous rating (two pins per power strip if the BQ24610 at 2 A is used) |
| mast | an 8 mm face plate at x 75 to 83, y +/- 140, z 10 to 460 | the head front overhangs the chest by 55 mm |
| tags | id 0, 40 mm, centre z 370; ids 1 and 2, 60 mm, y +/- 100 | id 0 stays readable to about 6 cm from the camera; ids 1 and 2 give the axis yaw from their baseline |

Duck side (CAD check only): a 0.8 mm adhesive FR4 (or flex) pad, 100 x 64 mm, on the flat chest face of print/body_front.stl (flat
from trunk z -2.8 to 78.9 mm; checked by ray tests on the V1 STL): GND strip at trunk z 0 to 20, SENSE 22 to 42, CHG+ 44 to 64,
2 mm gaps, ENIG. Wires through one 4 mm hole drilled after printing (a drill step like D24, no STL edit). Behind it, inside the
trunk: the Pololu 5382 ideal diode, a 5 A fuse, the 100 k pack-sense resistor, the wake branch to the Pololu 2813 ON pad. The cell
NTC sits in the seat the battery job left between the cells (twin/battery/BAY.md). About 10 g with the leads (calc only).

Printed dock parts (`stl/`, `dock_parts.py`, sliced with the lab's light PLA profile in print/config_light; calc only): 15 STLs, 16
prints (the spring cup twice), 916 g of PLA, 67.0 h. The six mast face pieces are 530 g and 39 h of it; a foam board or plywood face
(price BLOCKER) would cut the print to about 387 g and 28 h. Every part fits a 220 x 220 mm bed and a 150 mm height.

## 3. The port (software, no ROS)

| File | From upstream | What changed |
|---|---|---|
| autodock/LICENSE | LICENSE | verbatim (no NOTICE file upstream) |
| autodock/autodock_utils.py | autodock_utils.py | numpy in place of tf.transformations; DockState an IntEnum; yaw averaged on the circle (bug 2) |
| autodock/autodock_base.py | autodock_server.py | ROS removed, every robot call through a DockIO object; publish_cmd clamps each axis against its own range (bug 1) and gains a lateral axis (bug 4); every exit(0) became a zero command and return False (bug 3) |
| autodock/duck_autodock.py | simple_autodock.py | the states rewritten for this policy (below) |
| duck_autodock.yaml | turtlebot3.yaml | the duck values and the pulse tables |
| tests/test_autodock.py | (new) | the fixes, frame round trips, full docks of a planar stand-in with the policy's measured response, a retry, the lost-tag recovery, the undock (after a long charge, detections on), both gates not waived, a give-up, a replay of side-tag looks recorded in the gym |

What the duck layer does, and why (gym probes, sim pass only):
- The stock policy does not step under a 0.10 forward command, **does not step right at all** (vy -0.2: 0 mm in 2 s; vy +0.2:
  112 to 132 mm), turns right at about half the left rate, and wz 0.25 is one-sided (+6.7 against -0.4 deg in 1.5 s). So every
  motion is a timed pulse from a measured table plus stop-and-look; a right move is turn right, walk, turn back (a weak turn is
  topped up first and the diagonal walk is capped, 70 mm at the last-mile check point: on the soft floor a 0.11 rad turn made it a
  0.22 m walk into the mast); the approach aims 25 mm right of the axis so the late corrections are left sidesteps.
- The side tags set the dock axis heading, carried on the IMU yaw once they leave the view (the 40 mm tag's own normal was off by
  up to 8 deg).
- LAST_MILE: a check point 0.16 m before the stop (the soles 70 mm clear of the seat end; corrections at 0.10 m put a sole on it),
  lateral within 15 mm there, then a straight walk on the centre tag's range (no heading hold: a wz 0.5 hold overshot to 8 to 17 deg),
  a one-frame jump guard on that range, a 20 mm stop lead for the coasting step, dead reckoning only for the last few cm, and up to
  three still checks with a top-up step.
- Looks: three frames, one of which may miss the markers (single dropped frames on the low-friction floor ended last miles).
- ACTIVATE_CHARGER: the scripted sit, then the pins must report within 10 s.
- RETRY: stand, back off along the axis in short pulses with left sidesteps for the rightward drift of backing (turning in place on
  the dock put a foot on the spine), then find the staging point again. When the tags are lost, the duck turns to the mast position
  remembered on odometry and steps back until it is 0.55 m away, before any blind search (facing the saved axis heading left the
  mast out of view from 0.2 m off the axis, and the blind search then turned the duck away). At most 3 retries.
- Gates are never waived (PR 20 review): when the ENTER gate's sidesteps run out with the lateral error over 30 mm, STEER_DOCK
  fails and the duck retries; at the last-mile check point, after its checks the duck walks in only within 20 mm and 4 deg (the
  soles' clearance of the seat), else it retries.
- UNDOCK (after the dock's wake pulse): stand, then the same back-off, with its own 90 s timeout budget (a charge outlasts the
  docking timeout) and the tag detections on for the retreat (they are off while docked), off again at the end. The sim checks
  it after every dock.

## 4. The docking sim (the shared lab gym, overlay gym/overlays/duck, `dock/`; sim pass only)

### 4.1 Set-up
Gym physics (1 ms, implicitfast, elliptic cone, impratio 5), our 2.653 kg build, plain model, BEST_WALK_ONNX_2 in lab mode, driven
only through its command interface. A camera at the measured Camera Module 3 seat (twin/complete3d camera_seat.json, 40.1 deg
vertical field, 768 x 432), rendered at every look, OpenCV aruco and solvePnP IPPE_SQUARE. The duck's trunk, shins, feet and head
collide with the dock. IMU and encoders are exact; translation is dead-reckoned from the command. Floors: hard (friction 1.0),
train (0.6, the training value), soft (0.8 on a compliant contact, a carpet stand-in). Starts: 1.0 to 1.6 m out, +/- 0.25 m to the
side, +/- 25 deg of yaw, seeded.

### 4.2 The sit
The balanced crouch row of the phase 1 kinematics (hip -70 deg, knee 85 deg, ankle -16 deg; knee 0.99 Nm at 2.699 kg), ramped
over 2 s at the stock gains, then the leg gains drop to 4 (to 2 if the belly is not down after 0.8 s). It carries the trunk about
50 mm forward on the hard floor and 30 to 45 mm on the soft one, and sets the belly on the seat at 112 mm with 7 to 22 N on it.
Walking into a rigid stop, or reaching it early in the crouch, pitches the trunk up; the sprung paddle removes that.

### 4.3 What the probes showed (sim pass only)
| Command (from standing) | Result |
|---|---|
| vx 0.15 for 1 / 2 / 4 s | 74 / 157 / 360 mm; 10 to 35 mm of coasting after the zero command |
| vy +0.2 for 0.5 / 1 / 2 s | 10 / 40 / 112 to 132 mm left |
| vy -0.2 for 1 or 2 s | 0 mm |
| wz +0.5 for 0.3 / 0.5 / 1 s | +4.2 / +10 / +16.9 deg |
| wz -0.5 for 0.3 / 0.5 / 1 s | -3.6 / -4.8 to -5.5 / -10.5 to -14.4 deg |
| wz +0.25 / -0.25 for 1.5 s | +6.7 / -0.4 deg |
| vx -0.15 for 3 s | -110 mm, 39 mm right, +9 deg |

### 4.4 Results per change (rate per floor; each line adds to the one above; sim pass only)
| Run | Change | hard | train | soft |
|---|---|---|---|---|
| t8 | 40 mm centre tag, range stop, rigid bumper, belly pads | 0/4 | | 0/4 |
| t10 | lost-tag extrapolation, sidestep caps | 1/4 | | 0/4 |
| t12 | measured pulse tables (wz 0.5 only) | 3/4 | | 0/2 |
| t14 | two-stage last mile, belly pins at y +/- 5 | 5/6 | 3/6 | 0/6 |
| t15 | stop 30 mm short, 2 deg yaw gate, settle, slow stand-up | 4/6 | 3/6 | 1/6 |
| t17 | asymmetric turn tables, right moves by turn-walk-turn | 1/6 | 0/6 | 2/6 |
| t19 | axis on the IMU, right-biased approach | 4/6 | 1/6 | 2/6 |
| acc3, acc4 | back off along the axis; stop lead 35 then 20 mm (stopped early) | 1/11, 2/6 | | |
| acc5 | chest contacts on the sprung paddle (9 mm strips), coarse lateral tolerances, turn-away fix (stopped after 36) | 17/20 | 6/16 | |
| acc6 | chest strips 20 mm tall (vertical +/- 9.5 mm) (stopped before the soft floor) | 15/20 | 5/20 | |
| acc7 | swivelling paddle; a look may miss one frame; check point 0.16 m back, 15 mm lateral there; no heading hold in the walk-in; lost tags: face the remembered mast (stopped after the soft floor) | | | 6/20 |
| acc8 | right moves: a weak turn is topped up and the diagonal walk capped | 18/20 | 16/20 | 10/20 |
| acc9 | right moves at the check point only with 0.12 m of room (else one back pulse first); no walk-in unless centred and square (stopped after 16 hard runs, not better; reverted; acc10 brings back only its walk-in limit, as a hard limit of 20 mm and 4 deg) | 13/16 | | |
| mat1 | acc8 code, the soft floor with a rigid mat flush with it under the last 0.78 m (option, section 4.6) | | | 0/20 (18 tripped at the mat edge) |
| acc10 | review fixes (PR 20 and 24): the sim's settle now holds kp 2 (acc8 held 4 in the 9 settle sits), gates fail instead of being waived (never triggered here), the undock's own timeout and detections; an undock after every dock | 18/20 | 16/20 | 10/20 |

Each rate is docked within 3 tries with no fall. Every failure in acc6 to acc8, by cause:
- acc6 (19 runs): 6 sits with the chest yawed 4.5 to 6 deg on the fixed paddle, pins 2.5 to 3.9 mm off the chest (fixed by the
  swivel); 7 last miles ended by one dropped frame in a look on the low-friction floor (fixed: a look may miss one frame); 4 turn-aways
  after the tags were lost, facing the saved axis from 0.2 m off it left the mast out of view (fixed: face the remembered mast); 2 falls
  where a sole hit the seat end during corrections 0.10 m before the stop (fixed: the check point 0.16 m back, no heading hold).
- acc7 soft (14 falls): 7 in the back-off of a retry, 6 when a right move at the check point turned only 0.11 rad and its diagonal
  walk became 0.22 m straight into the mast (head on the column), 1 in the approach.
- acc8 hard (2): two right moves at the check point walked the duck to the stop, yawed 12 deg, with the tags out of view; one sit
  48 mm short. Train (4): the same check-point exit, then retries that spiralled to 90 deg off in the approach at close range; 1 fall
  in that approach. Soft (10 falls): 5 in the retry back-off, 3 at the stand-up and back-off after sits that stopped 34 to 39 mm
  short (the soft sit carries about 30 mm, not 50), 1 in the walk-in, 1 in the approach. On the soft floor no run docked after a
  retry: every retry fell.
- Why the soft retries fall (probe away from the dock, `pulse_falls.py`, 3 seeds x 12 pulses of each kind, each pulse followed by a
  1.2 s stop): walk 1 s, turn left or right 0.5 s, sidestep left 0.7 s: 0 falls in 36 on every floor. Back (vx -0.15, 1.5 s): 0 falls
  in 36 on the hard and the training floor, and **a fall on the first pulse in 3 of 3 seeds on the soft floor.** The stock policy
  cannot step back on the soft floor, and backing is the only way off this dock (turning in place or sidestepping puts a foot on the
  seat or the spine).

### 4.5 Precision at the seat (docked runs; sim pass only)
Run acc10 (the code in this repo, with the review fixes), 20 seeds per floor. Lateral and yaw: the trunk at the end against the
dock axis; fore-aft: how far the chest pushed the paddle (0 to 40 mm is inside the window); pin errors against the strip centre
lines. Undock: after each dock the charge is taken to outlast dock_timeout, then the duck stands and backs off to the retreat
distance (0.47 m from the tags) without a fall.

| Floor | Docked within 3 tries | Tries used (1 / 2 / 3 / 4) | Falls | Lateral mean / worst | Yaw mean / worst | Paddle push mean (min to max) | Pin across the strip, mean / worst | Pin height, mean / worst | Time to dock, mean / worst | Undock |
|---|---|---|---|---|---|---|---|---|---|---|
| hard | 18/20 | 9 / 6 / 3 / 1 | 0 | 10.3 / 20.7 mm | 3.8 / 16.7 deg | 16.8 (9.9 to 29.1) mm | 12.7 / 40.3 mm | 0.4 / 1.1 mm | 90 / 231 s | 19/19 |
| train | 16/20 | 10 / 5 / 1 / 0 | 1 | 9.3 / 19.9 mm | 3.5 / 6.3 deg | 22.3 (6.9 to 30.3) mm | 9.2 / 23.4 mm | 0.8 / 3.2 mm | 65 / 190 s | 16/16 |
| soft | 10/20 | 10 / 0 / 0 / 0 | 10 | 7.2 / 18.1 mm | 2.7 / 7.4 deg | 12.0 (2.6 to 19.7) mm | 9.1 / 27.6 mm | 0.0 / 0.2 mm | 46 / 72 s | 0/10, all fell |

The rates are the same as acc8: the 9 settle sits now hold kp 2 and 6 of them end 1 to 4 s sooner, no outcome changed, and the
gates never ran out of corrections. Every docked run is inside the pin window (+/- 49.5 mm across, +/- 9.5 mm in height, 0 to 40 mm push) with margin; the worst yaw
(16.7 deg, one hard run) was taken by the swivel at its 10 deg stop with the pins 1.4 mm from the chest. The soles touched the sides
of the seat while walking on 13 of the 20 hard runs and 10 of the 20 training-floor runs (no fall from it); the closest sole edge on
the soft floor stayed 14 mm away. The precision is good enough for the pins; the rate is set by retries and falls, not by the pin
window.

### 4.6 The bar is not met: numbers and the best options
Best runs (acc8, and acc10 with the review fixes): hard 18/20, train 16/20, soft 10/20 docked within 3 tries; falls 0, 1 and 10.
Undocking works on the hard and the training floor (19/19, 16/16) and fails on the soft floor (0/10, every one a fall on the back
pulses). The bar is 19/20 per floor with no fall. It is not lowered here. Options, best first:
1. **The retrained walk of track 10** (backing on soft floors, creep, symmetric turns, right sidesteps). The soft-floor failures are
   the stock policy's backing (it falls on the first back pulse on the soft floor, so there it can neither retry nor undock), and
   the hard and train failures start at the last-mile check point, where a right move (turn, walk, turn back) walked the duck up
   to the stop with the tags out of view (traced on one run). Its measured pulse tables go into duck_autodock.yaml with no code change, and a right sidestep removes the
   turn-walk-turn branch.
2. **A rigid dock mat under the last 0.78 m** (hardware, cheap: a hardboard or PETG plate; the seat and the spine stand on it), so
   the docking moves (stop-and-go, sit, stand, back-off) happen on a hard floor whatever the room. Not yet shown: in mat1 the
   plate's edge was a step of the soft floor's sink depth and 18 of 20 runs tripped on it. It needs a ramped edge (to be modelled
   and probed) before it can be judged.
3. On the soft floor only, no retry (one attempt, then stand still and ask for help): no falls from retries, at the first-attempt
   rate (10/20 in acc8). Needs a floor estimate (for example the walk's own pulse response from the looks).
4. A right move at the check point that keeps its room (tried in acc9: not better); a floor-adaptive sit gap (the soft sit carries
   about 30 mm, the hard one 50 mm: 3 soft sits stopped 5 to 8 mm short of the paddle).

## 5. Heat (the duck repo's thermal twin, P45B cells 70 g and 15 mOhm, central corner; sim pass only)

After 18 min of continuous walking (no guard: a hot bound) and the walk home; the duck off on the seat, torque off.

| Room | Charger | Cells at docking | Cells under 45 C (charge starts) | Cells highest while charging | Cells at the end | Ready after docking |
|---|---|---|---|---|---|---|
| 25 C | MCP73213, 1.1 A | 40.1 C | at once | 40.1 C | 26.8 C | 159 min |
| 25 C | BQ24610, 2.0 A | 40.1 C | at once | 40.1 C | 30.4 C | 88 min |
| 32 C | MCP73213, 1.1 A | 47.0 C | 10.2 min | 45.0 C | 33.5 C | 169 min |
| 32 C | BQ24610, 2.0 A | 47.0 C | 10.2 min | 45.0 C | 36.7 C | 98 min |
The high corner (every pessimistic value at once, a bound): cells 64 to 71 C at docking and 38 to 58 min before charging. The hottest
knee reads 62 C (25 C room) and 69 C (32 C room) at docking and falls under 45 C in 4.2 and 8.0 min with the torque off. Losses while
charging (calc only): 0.11 W in the duck at 1.1 A (0.36 W at 2.0 A); 0.01 to 0.04 W at the three pins; in the dock the MCP73213
dissipates (9 V minus the pack) x 1.1 A, 1.8 W at mid charge and up to 2.8 W at the start, on its board with thermal regulation;
the duck's electronics 0 W (it is off). The cells stay at or under 45 C through every charge (the charge starts at 45 C at most and
they keep cooling). Left on while charging, the duck would add 5.7 W and keep the servos over 40 C for 5 h at 32 C. No dock fan (8 %
gain in phase 1).

## 6. Charge electronics

### 6.1 Charger (datasheets read; only these can be picked)
| Charger | CC/CV, termination | Safety timer | Thermistor | Reverse and short | Current | Dock heat | Price read | Verdict |
|---|---|---|---|---|---|---|---|---|
| TP5100 (TOP POWER) | +/- 1 %, C/10 end, recharge at 8.1 V | none in the datasheet | TS window, 45 to 80 % of VREG | reverse-battery shutdown, continuous BAT short protection, 145 C limit | to 2 A | low | not read | out: no timer, and a Chinese part without a warranty (lab rule) |
| Microchip MCP73213 | yes; end of charge 5 or 7.5 %; preconditioning; automatic recharge | 4, 6 or 8 h by option | none | reverse discharge protection, 13 V input OVP, thermal regulation | 1.1 A | linear, up to 2.8 W | EVM MCP73213EV-2SOVP about $44.90 (non-US DigiKey listing via search; US price BLOCKER) | **chosen**: simplest (linear, no inductor), timer, US maker; the gate supplies the over-temperature cut |
| TI BQ24610 | yes, programmable termination | programmable (TTC) | TS hot and cold suspend | input reverse FET, battery short protection | to 10 A | low | BQ24610EVM $99.00 (TI, undated listing) | the faster option: 1.46 h from the go-home point against 2.65 h |
| TI BQ25887 | yes, with cell balancing | yes | TS | yes | 2 A boost from 3.9 to 6.2 V | low | not read | out: balancing needs a fourth, mid-cell contact, and I2C set-up |

### 6.2 Gate: hardware, not a Pico W
| | Hardware gate (chosen) | Pico W with a Wi-Fi handshake |
|---|---|---|
| Parts | microswitch, 2 x LM393, TL431, NE555, Pololu 2815, about 20 passives | Pico W, INA228, Pololu 2813, microswitch, firmware |
| Code | none | firmware, Wi-Fi set-up, a watchdog |
| Failure modes | analog thresholds drift (bench check BT3, BT4) | hung firmware, Wi-Fi loss, configuration |
| Safety | the microswitch is in series with the charger switch's control line: no seated duck, no power | the same switch is still needed |
| How the duck knows | its own pack monitor sees the charge current (the battery job's monitor) | a Wi-Fi reply |
| Wake when full | the charger's STAT edge fires a 100 ms 555 pulse onto SENSE | a firmware pulse |

Wiring (calc only):
```
9 V adapter -> 5 A fuse -> Pololu 2815 (on-board slide OFF; CTRL to GND turns it on) -> MCP73213 EVM VIN
   2815 CTRL -> seat microswitch (Omron D2F-01L, NO) -> NPN collector; NPN base <- wired-AND of the LM393 outputs (open collector)
MCP73213 VBAT -> paddle pin CHG+ ; GND -> paddle pin GND
TL431 2.50 V -> 10 k -> paddle pin SENSE -> [duck: chest SENSE strip -> 10 k NTC in the cell seat -> GND]
   LM393 A: SENSE inside the 45 C to 5 C levels (a window of two halves)
   LM393 B: CHG+ through 1 M / 330 k reads 5.0 to 8.45 V (a pack is there; a coin, a finger or nothing reads 0 V)
MCP73213 STAT -> NE555 one-shot, 100 ms -> PNP -> 9 V through 1 k onto SENSE -> [duck: 3.9 V zener, diode, 10 k -> Pololu 2813 ON]
Duck: chest CHG+ strip -> Pololu 5382 ideal diode -> 5 A fuse -> BMS P+ ; 100 k across the ideal diode ; chest GND strip -> BMS P-
```

### 6.3 Pack (D44)
2S1P Molicel P45B: 4.5 Ah per cell, 8.40 V CV, 2.6 h at 2.0 A from empty (the battery job). From the 48 % go-home point (calc
only): 2.65 h at 1.1 A, 1.46 h at 2.0 A. Play to dock time (calc only; play 33 to 74 min per cycle by energy, the P30B's 22 to 49
min x 32.4 / 21.6 Wh; dock time from section 5): MCP73213 1 : 2.1 to 1 : 5.1; BQ24610 1 : 1.2 to 1 : 3.0.

## 7. BOM (prices read; buy nothing; no shipping)
| Line | Part | Qty | Price | Source |
|---|---|---|---|---|
| K1 | Microchip MCP73213EV-2SOVP charger board | 1 | about $44.90 (non-US listing; US BLOCKER) | DigiKey listing via search |
| K2 | Pololu 2815 MOSFET switch with reverse protection | 1 | $8.49 | BOM line 10r |
| K3 | Omron D2F-01L microswitch | 1 | BLOCKER | survey row 50 note |
| K4 | LM393 (x2), TL431, NE555, 2N3904, 2N3906, resistors, 3.9 V zener | 1 set | BLOCKER (commodity) | |
| K5 | Mill-Max 0932 spring pins | 4 (3 + 1 spare) | about $0.78 each, $3.12 (nearby part numbers; exact BLOCKER) | phase 1 sources |
| K6 | 9 V adapter, 15 W or more | 1 | BLOCKER | |
| K7 | printed dock parts, 923 g PLA | 1 set | the lab filament line | slice above |
| K8 | two 4 mm x 70 mm steel rods, two 4 mm shaft collars, two compression springs (about 37.5 N/m, 50 mm free, under 10 mm OD), two M3 x 20 screws (pivot) and four M3 bolts (cups) from the build's kit, PTFE tape, steel ballast 2 x 120 x 72 x 8 mm | 1 set | BLOCKER | |
| R1 | chest contact pad 100 x 64 x 0.8 mm FR4 ENIG | 1 | BLOCKER | robot BOM.md line DK1 |
| R2 | Pololu 5382 ideal diode 4 to 60 V, 10 A | 1 | $3.79 | Pololu listing and blog, via the search index 2026-11-05 (phase 1 had $1.75, wrong); robot BOM.md line DK2 |
| R3 | Littelfuse 0287005.PXCN ATO 5 A fuse and an FHAC0001ZXJ holder | 1 | $7.74 + $0.44 | robot BOM.md lines DK3, DK4 (two fuses there, one spare) |
| R4 | 10 k NTC for the cell seat, zener, diode, resistors | 1 set | BLOCKER (commodity) | robot BOM.md line DK5; wire from BOM 23 and 25, the pad tape from BOM 29 |
Read prices: **$68.48** (K1, K2, K5, R2, R3), before the BLOCKER lines. With the BQ24610EVM in place of K1: $122.58. The duck-side
lines R1 to R4 are in the robot's BOM.md (DK1 to DK5, +$12.41 on its build total with the spare fuse) and MOUNTING.md (V1 track 8);
the chest pad needs no STL change for V1.

## 8. Bench tests (proposed; nothing run)
| Test | Pass |
|---|---|
| BT1 paddle: travel, force, swivel | 40 mm free travel; 3 N or less at full travel; returns to rest; swivels +/- 10 deg freely at any travel and lies flat on a board held 6 deg off square |
| BT2 pin to pad resistance, 4-wire, 1 A | 30 mOhm or less per pin |
| BT3 SENSE window with a decade box | on from 4.4 k (45 C) to 25.9 k (5 C) for a B3950 NTC; off open and shorted |
| BT4 pin-voltage window | off at 4.9 V and 8.6 V, on at 5.1 V and 8.4 V; a coin across the pins keeps it off |
| BT5 microswitch interlock | the charger stays off with the switch open whatever the comparators read; closes at 8 to 12 N on the seat |
| BT6 MCP73213 EVM into the P45B pack | CV 8.40 +/- 0.04 V, CC 1.1 A, end of charge, timer fault after the set time; EVM under 85 C in a 32 C room |
| BT7 wake | the 2813 turns on from the SENSE pulse and never during the NTC reading |
| BT8 ideal diode | chest strips open with the pack in: 0.21 mA at most through the 100 k; reverse polarity at the strips draws nothing |
| BT9 the sit on real servos (after the knee and hip stops are known) | belly at 112 mm, chest on the paddle, three pins on their strips |
| BT10 tags on the Pi Zero 2 W | frame time at 768 x 432; the 40 mm tag read from 6 to 15 cm (autofocus) |
| BT11 a real charge | cell NTC at or under 45 C through the charge in a 25 and a 32 C room |

## 9. BLOCKERs
1. The real knee and hip stops for the sit (knee 85 deg; hip -70 deg, its sim limit).
2. The Camera Module 3 close focus for the 40 mm tag at 6 to 15 cm, its rolling shutter and the exposure while walking.
3. The Pi Zero 2 W aruco frame time next to the 50 Hz loop.
4. The PTFE paddle friction (0.15 assumed), the paddle spring (75 N/m) and the swivel friction (near zero in the sim); the seat is
   rigid in the sim.
5. The policy's lateral and turning asymmetry on the real duck (sim only); track 10's retrained walk is expected to remove most of it.
6. Prices: the MCP73213 EVM in the US, the microswitch, the commodity parts, the adapter, the chest pad, the rods, springs and ballast.
7. The battery job's pack monitor (it tells the duck that charging started) and the NTC type in the cell seat.
8. The Mill-Max 0932 mounting hole (1.9 mm assumed in the paddle), its spring force and stroke (the sim takes a pin as touching
   when the chest is within 2 mm of its tip).
9. The soft floor is a compliant-contact stand-in for carpet; the real floors at home are not measured.
10. A limp hold on the seat for hours (torque off), and the STS3215 unpowered backdrive torque (section 11.5).
11. D50: the 9 V 4 A adapter and its price; the MCP73213 EV board's option code (A6S assumed); the 2813 ON pad position (a stand-in at its control pads, as D13); the NTC lead's fit into the cell seat.

## 10. Files
- Duck repo: altaay_lab/software/dock/ (autodock/, duck_autodock.yaml, tests/, THIRD_PARTY.md); altaay_lab/twin/dock/ (this file,
  dock_parts.py, stl/).
- The shared lab gym (overlay gym/overlays/duck), dock/: DOCK.md (the course and the one-command acceptance run, also with a
  new policy), dock_course.py (floors hard, train, soft and the soft_mat option), dock_sim.py (--onnx, --mass, --knee, --mode),
  dock_stats.py, pulse_tables.py (a policy's pulse tables for duck_autodock.yaml), pulse_falls.py. Committed in the gym on the
  dock job's branch v1-dock-local. The probe results and the run records are scratch data (lab rule 8).

## 11. Awake while docked (phase 3, D50; calc only, sim pass only where said)

Ahmed, 2026-11-05 7:32 PM ET: "How long to charge? Can the Ducky stay running for like 8 hours?" 7:33 PM ET: "Since it's a
home buddy, it doesn't need to be small. And since it can charge for like 6 hours at night, that's awesome."

### 11.1 The pick: a fourth contact carries the dock supply (SYS), ORed into the duck's switch input
- The dock's gated 9 V (the same gate as the charger: seat microswitch, NTC window, pin-voltage window) goes out on a fourth
  strip, SYS. In the duck, SYS passes an ideal diode (DK6, Pololu 5382) to the 2813 input; the fused pack reaches the same node
  through a second ideal diode (DK7, Pololu 5383, under 5 mOhm, 12 A). The higher one wins: on the dock, SYS (8.82 to 9.18 V)
  runs the whole duck (Pi, camera, mics, amp, BEC, servo idle) and the pack, at 8.40 V or less, only charges.
- The charger then sees the pack alone, so CC/CV, the 10 % end-of-charge current and the 6 h timer of the MCP73213 work as
  designed. Microchip's load-sharing note for its stand-alone chargers (AN1149) gives the same rule: feed the system from the
  input when it is there, not from the cell.
- If SYS drops (the duck is lifted, the gate opens on heat), the node falls to the pack in microseconds: no brown-out.
- The 2813 stays the master switch: OFF is a full shutdown on or off the dock (SYS stops at the 2813 input like the pack). The
  555 wake pulse on SENSE stays, for the full-shutdown mode only; an awake duck does not need it.
- Rejected:
  | Option | Why not |
  |---|---|
  | The load on the pack with 3 contacts and the 1.1 A charger | the load eats 0.62 of 1.1 A: from empty the 6 h timer ends the charge at 64 %; the end-of-charge current is never reached (table 11.3) |
  | The same with a 2 A charger (BQ24610) | charges, but never terminates: the cells float at 4.20 V for hours every day, the worst case for their life |
  | A power-path charger in the duck | its 1 to 2 W of loss and its mass go into the trunk next to the cells; the extra size belongs in the dock |
  | SYS ORed into the 5 V regulator only, the 2813 off while docked to cut the servos | needs new control lines and a hold circuit so the Pi keeps itself on, and the button is no longer a hard off; more parts and code for 0.6 to 2.1 W |
- Servo power stays on while docked; torque is off (limp). Cutting it would save 0.6 to 2.1 W (14 servos idle at 6 to 21 mA,
  THERMAL_TWIN.md F1) from the dock, not from the pack, and would need a second switch in the servo feed (row above), so it is
  not done (D45). The servos stay ready for the head turn of D47.
- DK7 puts under 5 mOhm into the walking path (about 6 % of its resistance; 0.1 W at the 4.4 A walking mean); its 12 A rating
  with about 40 A for seconds covers the 100 ms walking peaks and the 20 ms fall peaks; a jam above 22 A is cut by the BMS.

### 11.2 Size goes into the dock, not the duck
Mass hurts the walk: the DCB200 duck (3.24 kg) walked at 0.030 m/s against 0.103 m/s (twin/battery/BATTERY_STUDY.md 5.2). So
the duck gains only the fourth strip and two 0.2 g diode boards (about 1.5 g in all, calc); the dock gets the bigger adapter
(9 V 4 A, 36 W, against 15 W), two more spring pins and nothing else. No fan.

### 11.3 Charge times with the load running (calc only, charge_awake model: generic NCA/NMC OCV, ASSUMPTION; 2 x 15 mOhm cells plus 50 mOhm path)
Docked load: the 5 V branch 3 W typical, 5 W conservative (THERMAL_TWIN.md) plus servo idle and BEC, 0.62 A at the pack.

| Charger | Load on | From empty | From the 48 % go-home point | After 6 h from empty |
|---|---|---|---|---|
| MCP73213, 1.1 A | SYS (D50) | 4.3 h, terminated at 99.6 % | 2.4 h | full |
| MCP73213, 1.1 A | the pack (3 contacts) | timer at 6 h, 64 % | timer at 6 h, never terminates | 64 % |
| BQ24610, 2.0 A | SYS (D50) | 2.5 h | 1.4 h | full |
| BQ24610, 2.0 A | the pack (3 contacts) | full, never terminates (float) | float | full, floating |

With SYS the load does not touch the charge current, so the 1.1 A MCP73213 stays (D45: linear, fewest parts, $44.90 against
$99.00): a full charge from empty fits the 6 h night and the 6 h timer; the 2 A option saves 1 h and changes nothing else.
Ahmed's 8 hours: on the dock, unlimited (the dock runs the duck); off the dock, sitting with the servos limp, about 5.5 h at
5.3 W and 9 h at 3.1 W from the 29 Wh above a 3.3 V per cell stop (calc); walking 39 to 50 min (BATTERY_STUDY.md 5.5).

### 11.4 Heat (the thermal twin, P45B, after 18 min of walking and the walk home; awake on the dock: 5 V branch 3 or 5 W in the head, servo idle and BEC loss in the trunk and the legs; sim pass only)
| Corner, room | Cells at docking | Charge starts after | Cells highest while charging | Cells at the end | Head air highest |
|---|---|---|---|---|---|
| central, 25 C | 40.1 C | at once | 40.1 C | 28.1 C | 33.7 C (3 W), 37.5 C (5 W) |
| central, 32 C | 47.0 C | 10.8 min | 45.0 C | 34.9 C | 40.5 C (3 W), 44.3 C (5 W) |
| high, 25 C | 63.9 C | 40.7 min | 45.0 C | 29.1 C | 40.7 C (5 W) |
| high, 32 C | 70.6 C | 65.0 min | 45.0 C | 35.9 C | 47.5 C (5 W) |
The cells stay at or under 45 C through every charge in both rooms (the charge waits for 45 C and they keep cooling). The twin
has no air path between the head and the trunk; with 30 % of a 5 W head heat put into the trunk air as a check, the charge
starts 2 to 13 min later and the cells still end at 31 to 39 C. The 2 A charger ends 2.5 C warmer.

### 11.5 Docked idle (hardware side)
- Pose: the existing sit (belly on the seat at 112 mm, chest on the paddle), then torque off. Torque off is the same as the
  sim's kp_settle step taken to zero; the sit test of the gym (test_dock_sim.py) holds at kp 2. A limp hold for hours is not
  yet simulated (BLOCKER 10). If it slides, the seat needs a 2 mm raised lip at its rear and sides (a dock_seat_top change).
- The paddle spring pushes the chest back with 0.5 to 2.3 N (7 to 30 mm of push at 75 N/m); the belly on the seat (7 to 22 N,
  friction about 1) holds it.
- Bench: the servo bus with the duck limp (no back-powering through the data line), and the STS3215's unpowered backdrive torque.

### 11.6 Contacts and gate
- Strips (bottom to top, 17.5 mm tall, 2 mm gaps): SYS z 0 to 17.5, GND 19.5 to 37, SENSE 39 to 56.5, CHG+ 58.5 to 76 (trunk z).
  SYS sits next to GND only: a coin across them shorts the adapter (its short protection, the 5 A fuse); a coin across SYS and
  CHG+ would charge the pack from SYS, so they are not neighbours, and the pin-voltage window would cut it at 8.45 V anyway.
- Pins: 6 Mill-Max 0932 (2 A each): SYS 2 and GND 2 at y +/- 3 mm, CHG+ 1, SENSE 1. Vertical window +/- 8.25 mm (acc10 worst
  3.2 mm); lateral +/- 46.5 mm for the doubled rows (acc10 worst 40.3 mm, computed from the recorded pin errors).
- The gate is unchanged in hardware: SYS and the charger share its switch, so a duck that is not seated, too hot or too cold, or
  shows a wrong pack voltage gets neither.

### 11.7 Cost (prices read; buy nothing)
Duck: DK6 $3.79 + DK7 $4.95 = +$8.74 (BOM.md). Dock: two more 0932 pins $1.56; the 9 V 4 A adapter (Mean Well GST36A09 class,
price BLOCKER) replaces the 15 W one (also BLOCKER). Read total of the dock change: +$10.30.

### 11.8 Files, wiring and seats
- wiring/netlist.yaml carries the dock wiring since 2026-11-06 ET: components DKP, DK2, F2, RT1, WK1, DK6, DK7; cables DC1 to DC4;
  the fused pack run P7 now ends at DK7 and SW1 VIN is the OR node PACK_OR. duck_side_netlist.yaml stays as the change record;
  dock_netlist.yaml is the dock.
- 3D routes: seats/route2.py (1 mm grid of the trunk parts and placed boxes, a shortest clear path, string pulled) writes
  dock_routes.json; dock_cables3d.py puts DC1 to DC4 into cables3d/cables3d.json. All in the trunk, no joint crossed. Cuts are the
  routed length plus 2 x 20 mm: DC1 50, 180 and 100 mm; DC2 220 mm; DC3 230, 120 and 190 mm; DC4 190 and 60 mm. The NTC lead
  enters the cell seat with no clearance to spare (test fit).
- Seats (seats/pick3.py, dock_seats.json, close-ups dock_seats.png, CAD check only): each board on VHB 4950 with its large face
  1.5 mm off a printed wall, clear of every part, placed box and routed cable by 1 mm:
  | Part | Centre (world mm, zero pose) | On |
  |---|---|---|
  | DK2 Pololu 5382 | (33, 0, 24) | the inner face of body_front, below the lead hole |
  | F2 holder, standing | (-85, -42, 26) | the left inner side wall of body_middle_bottom |
  | DK6 Pololu 5382 | (-104, 1, 45) | the underside of trunk_top, beside the 2813 |
  | DK7 Pololu 5383 | (-104, 13, 45) | the underside of trunk_top, 16 mm from SW1 VIN |
  No screw and no hole is added (D42, D39); the only hole is the 4 mm lead hole through body_front, which carries the leads.
- U3 at 9.2 V: the Pololu D30V30F5 takes 5 to 45 V in (Pololu product page, read via the search index): passes, no change.
- The thermal and charge runs: scratch data (lab rule 8).
