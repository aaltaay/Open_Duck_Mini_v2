# DOCK_TWIN: the V1 self-charging dock, phase 2 (track 8)

Written 2026-11-05 by the V1 dock job (track 8); section 12 (the full dock: fixes, every part, screws, wires, BOM) 2026-11-06. Labels: sim pass only, calc only, CAD check only. Nothing was bought, printed,
built or tested on hardware. Decisions this follows: D37 (self-charge is a V1 must-have), D43 (contacts; the dock behaviour code
is a port of osrf/autodock), D44 (2S1P Molicel P45B pack), D45 (simplest, cheapest and most reliable at once). Ahmed, about
1:30 AM ET on 2026-11-05: "I'm also all about precision ... what about perception? Why don't we rely on perception as well?"

## 1. The answer in short

- **Behaviour code:** osrf/autodock (Apache-2.0, fd9c2a9) ported with no ROS to `altaay_lab/software/dock/autodock/`, the four
  upstream bugs fixed, and a duck layer on top. All motion goes through measured pulse tables in `duck_autodock.yaml`, so the
  retrained walk of track 10 (creep, symmetric turns, small sidesteps) can be swapped in by changing tables, not code. 15 unit tests.
- **Dock:** a 40 mm wide seat at 112 mm on a short spine between the feet, a **sprung, swivelling chest paddle** (40 mm travel,
  3 N at full travel, +/- 10 deg about a vertical pin so it lies flat on a yawed chest) with six spring pins (D50), and a three-tag mast
  (tag36h11 id 0 at 40 mm in the centre, ids 1 and 2 at 60 mm, 200 mm apart). The full build (every part, screw and wire) is section 12.
- **Contacts on the chest, not the belly:** four strips 100 mm wide and 17.5 mm tall on the flat chest face (CHG+, SENSE, GND,
  SYS, top to bottom; D50 added SYS, the dock supply that keeps the duck awake while docked, section 11). The seat sets their height, the paddle takes up the stop error, the strip length takes the lateral error: the window
  is fore-aft 0 to 40 mm into the paddle, lateral +/- 46.5 mm (doubled rows; +/- 49.5 mm single), vertical +/- 8.25 mm, yaw +/- 10 deg. The belly is not cut (the pocket
  tried earlier is reverted). The feet set the tighter lateral limit: the soles clear the seat by about 22 mm a side.
- **Perception closes the loop to the paddle:** the side tags square the duck and set the dock axis, saved on the IMU yaw; the
  40 mm centre tag gives the range and the lateral offset down to about 6 cm from the camera, the last 3 to 5 cm before the stop
  are dead-reckoned. Then a scripted balanced crouch carries the chest 30 to 50 mm forward onto the paddle and the belly onto the seat.
- **Charge path:** a hardware gate, no microcontroller and no Wi-Fi (seat microswitch in series, NTC window, pin-voltage window, a
  555 wake pulse); charger Microchip MCP73213 EV board (1.0 A with its PROG via grounded, 6 h safety timer; section 12.5); the duck confirms charging with its own pack monitor.
- **Acceptance (sim pass only), 20 seeds per floor, bar 19 of 20 within 3 tries and no fall: not met.** Best run hard 18/20,
  train 16/20, soft 10/20 (sections 4.4 to 4.6); the precision at the seat is inside the pin window on every docked run. The soft
  floor is held back by the stock policy, which falls when it steps back on it.

## 2. Geometry (sim, STLs and duck side)

Dock frame: x toward the mast, the paddle face at rest is x = 0, z up from the floor, mm.

| Part | Where | Why (sim pass only unless stated) |
|---|---|---|
| seat | x -110 to -15, y +/- 20, top z 112 | a 60 mm seat was touched by a sole; at 40 mm the closest sole edge stayed 22 to 41 mm away |
| spine | x -15 to 30, y +/- 20, top z 90 | links the seat to the mast base |
| paddle | x 0 to 12 at rest, y +/- 55, z 140 to 230 (D50: 10 mm taller for the fourth row), slides 40 mm on two 4 mm rods held at a constant 3.29 N by two CF37CS springs (section 12.1; was 75 N/m), swivels +/- 10 deg about a vertical pin at x 18, printed face (no PTFE since section 12.1) | a rigid bumper gave a 5 to 10 mm stop window; the sprung paddle takes any stop from 0 to 40 mm short of full travel; a fixed paddle left the pins 2.5 to 3.9 mm off a chest yawed 4.5 to 6 deg (acc6), the swivel lays it flat |
| paddle guide | a yoke (carrier) holds the pivot (two coaxial M3 x 20 screws) and the rods; the rods run through 4.4 mm bores in the mast face into two spring cups behind it, a shaft collar on each rod end, a constant-force spring coiled on a drum in each channel (section 12.1) | the 75 mm between the paddle face and the mast leaves no room for 40 mm of travel plus springs in front of the mast; CAD check: no overlap at 0, 20 and 40 mm of travel and -10, 0, +10 deg |
| pins | six Mill-Max 0933 (since section 12.1; were 0932) in the paddle (D50): CHG+ z 214.35 and SENSE z 194.85 at y 0, GND z 175.35 and SYS z 155.85 at y +/- 3 (the seated trunk origin z 147.1 plus each strip centre; dock_parts.py PADDLE_PINS) | GND carries the charge and SYS returns (about 2.1 A) and SYS up to 1.8 A: two pins each under the 2 A continuous rating; CAD check: all six pins sit 8.75 mm inside their strip edges with the duck seated (section 11.8) |
| mast | an 8 mm face plate at x 75 to 83, y +/- 140, z 10 to 460 | the head front overhangs the chest by 55 mm |
| tags | id 0, 40 mm, centre z 370; ids 1 and 2, 60 mm, y +/- 100 | id 0 stays readable to about 6 cm from the camera; ids 1 and 2 give the axis yaw from their baseline |

Duck side (CAD check only): a 0.8 mm adhesive FR4 (or flex) pad, 100 x 76 mm, on the flat chest face of print/body_front.stl (flat
from trunk z -2.8 to 78.9 mm; checked by ray tests on the V1 STL): since D50 SYS strip at trunk z 0 to 17.5, GND 19.5 to 37,
SENSE 39 to 56.5, CHG+ 58.5 to 76, 2 mm gaps, ENIG. Wires through one 6.0 mm hole printed in body_front (chest_hole.py: a 45 deg bell mouth inside, a chamfer at the pad; only the four pad conductors pass it, the branches are spliced inside). Behind it, inside the
trunk: the Pololu 5382 ideal diode, a 5 A fuse, the 100 k pack-sense resistor, the wake branch to the Pololu 2813 ON pad. The cell
NTC sits in the seat the battery job left between the cells (twin/battery/BAY.md). About 10 g with the leads (calc only).

Printed dock parts (`stl/`, `dock_parts.py`, sliced with the lab's light PLA profile in print/config_light; calc only): 15 STLs, 16
prints (the spring cup twice), 921 g of PLA, 67.4 h (D50 paddle and carrier re-sliced: 46.1 g, 3.12 h and 11.7 g, 0.96 h). The six mast face pieces are 530 g and 39 h of it; a foam board or plywood face
(price BLOCKER) would cut the print to about 392 g and 28.4 h. Every part fits a 220 x 220 mm bed and a 150 mm height.

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
| 25 C | MCP73213, 1.1 A (a bound for the 1.0 A EV board) | 40.1 C | at once | 40.1 C | 26.8 C | 159 min |
| 25 C | BQ24610, 2.0 A | 40.1 C | at once | 40.1 C | 30.4 C | 88 min |
| 32 C | MCP73213, 1.1 A | 47.0 C | 10.2 min | 45.0 C | 33.5 C | 169 min |
| 32 C | BQ24610, 2.0 A | 47.0 C | 10.2 min | 45.0 C | 36.7 C | 98 min |
The high corner (every pessimistic value at once, a bound): cells 64 to 71 C at docking and 38 to 58 min before charging. The hottest
knee reads 62 C (25 C room) and 69 C (32 C room) at docking and falls under 45 C in 4.2 and 8.0 min with the torque off. Losses while
charging (calc only): 0.11 W in the duck at 1.1 A (0.36 W at 2.0 A); 0.01 to 0.04 W at the three pins; in the dock the MCP73213
dissipates (9 V minus the pack) x 1.1 A, 1.8 W at mid charge and up to 2.8 W at the start (at the EV board's 1.0 A: 1.6 and 2.5 W), on its board with thermal regulation;
the duck's electronics 0 W (it is off). The cells stay at or under 45 C through every charge (the charge starts at 45 C at most and
they keep cooling). Left on while charging, the duck would add 5.7 W and keep the servos over 40 C for 5 h at 32 C. No dock fan (8 %
gain in phase 1).

## 6. Charge electronics

### 6.1 Charger (datasheets read; only these can be picked)
| Charger | CC/CV, termination | Safety timer | Thermistor | Reverse and short | Current | Dock heat | Price read | Verdict |
|---|---|---|---|---|---|---|---|---|
| TP5100 (TOP POWER) | +/- 1 %, C/10 end, recharge at 8.1 V | none in the datasheet | TS window, 45 to 80 % of VREG | reverse-battery shutdown, continuous BAT short protection, 145 C limit | to 2 A | low | not read | out: no timer, and a Chinese part without a warranty (lab rule) |
| Microchip MCP73213 | yes; end of charge 5 or 7.5 %; preconditioning; automatic recharge | 4, 6 or 8 h by option | none | reverse discharge protection, 13 V input OVP, thermal regulation | 1.0 A on the EV board (PROG via grounded; 1.1 A needs R_PROG 1.00 k) | linear, up to 2.5 W at 1.0 A | EVM MCP73213EV-2SOVP $33.58 (DigiKey, index; section 7) | **chosen**: simplest (linear, no inductor), timer, US maker; the gate supplies the over-temperature cut |
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
only): about 2.9 h at the EV board's 1.0 A (2.65 h at 1.1 A scaled by the 1.09 of section 12.5), 1.46 h at 2.0 A. Play to dock time (calc only; play 33 to 74 min per cycle by energy, the P30B's 22 to 49
min x 32.4 / 21.6 Wh; dock time from section 5): MCP73213 1 : 2.1 to 1 : 5.1; BQ24610 1 : 1.2 to 1 : 3.0.

## 7. BOM (prices read; buy nothing; no shipping)
Rebuilt 2026-11-06 by the full dock job from the sourcing research of the same day (page or index reads, kept per line) and
this job's own reads; generated by dock_bom.py from dock_bom.json, and checked there against the fasteners, the assembly
and the gate board (every Need equals the count found). Duck-side parts are in BOM.md DK1 to DK7.

<!-- dock-bom start: written by dock_bom.py -->
| Line | Part | Part number | Need | Buy | Unit $ | Buy $ | Seller | Link | Read |
|---|---|---|---|---|---|---|---|---|---|
| K1 | Charger board, MCP73213 2-cell, 8.40 V, 6 h timer, PROG via to ground for 1000 mA (U1 MCP73213-A6S/MF) | Microchip MCP73213EV-2SOVP, DigiKey MCP73213EV-2SOVP-ND | 1 | 1 | 33.58 | 33.58 | DigiKey | https://www.digikey.com/en/products/detail/microchip-technology/MCP73213EV-2SOVP/2170203 | index: $33.58 (Newark $32.88, index); A6S read in the user's guide BOM, DS51849A |
| K2 | Gate switch for CHG and SYS, MOSFET slide switch with reverse protection, HP | Pololu 2815 | 1 | 1 | 8.49 | 8.49 | Pololu | https://www.pololu.com/product/2815 | page: $8.49 |
| K3 | Seat microswitch, hinge lever, NO used (D2F-01L-D3 solder lug is the fallback) | Omron D2F-01L | 1 | 2 | 1.44 | 2.88 | Mouser | https://www.mouser.com/en/ProductDetail/Omron-Electronics/D2F-01L?qs=0w99tykdtPJyAZbwr7e4aQ%3D%3D | index: $1.44 |
| K4a | Dual comparator, DIP-8 (NTC window, pin-voltage window) | TI LM393P | 2 | 3 | 0.49 | 1.47 | DigiKey | https://www.digikey.com/en/products/detail/texas-instruments/LM393P/277045 | index: $0.49 |
| K4b | 555 timer, DIP-8 (110 ms wake one-shot) | TI NE555P | 1 | 2 | 0.51 | 1.02 | DigiKey | https://www.digikey.com/en/products/detail/texas-instruments/NE555P/277057 | index: $0.51 |
| K4c | 2.50 V shunt reference, TO-92 | TI TL431AILPR | 1 | 2 | 0.24 | 0.48 | Mouser | https://www.mouser.com/c/?q=TL431AILPR | index: $0.24 |
| K4d | NPN, TO-92: Q1 gate driver, Q3 STAT inverter | onsemi 2N3904BU | 2 | 3 | 0.28 | 0.84 | DigiKey | https://www.digikey.com/en/products/detail/onsemi/2N3904BU/1413 | index: $0.28 |
| K4f | 1N4148 (dock D1, D2; duck wake branch DK5) | onsemi 1N4148 | 3 | 10 | 0.039 | 0.39 | DigiKey | https://www.digikey.com/en/products/detail/onsemi/1N4148/458603 | index: $0.039 at 10 |
| K4g | Resistor kit 1/4 W, 500 pcs: the 31 gate resistors (some values as series pairs) and the duck's DK5 10 k and 100 k | SparkFun COM-10969 | 1 | 1 | 9.95 | 9.95 | SparkFun | https://www.sparkfun.com/products/10969 | page: $9.95 (22 k to 1 M, 1 k to 10 k ranges read 2026-11-06) |
| K4h | Capacitor kit (100 nF x 3, 1 uF, 10 nF x 2 used; all in the kit, read 2026-11-06) | SparkFun KIT-13698 | 1 | 1 | 11.50 | 11.50 | SparkFun | https://www.sparkfun.com/products/13698 | page: $11.50 |
| K4i | Gate board, Perma-Proto half (51 x 81 mm, 2 mounting holes 73.7 mm apart) | Adafruit 1609 | 1 | 1 | 4.50 | 4.50 | Adafruit | https://www.adafruit.com/product/1609 | page: $4.50 |
| K5 | Spring pin, press-fit into an insulator (1.600 mm hole), solder cup, 45 gf at mid stroke, 1.397 mm stroke, 6 A (4.80 A derated), 40 mOhm max | Mill-Max 0933-0-15-20-72-14-11-0, DigiKey 54-0933-0-15-20-72-14-11-0-ND | 6 | 8 | BLOCKER | BLOCKER | DigiKey | https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/0933-0-15-20-72-14-11-0/26950711 | BLOCKER: price not read (digikey.com is outside this session's network; no index price); specs read on the Mill-Max data sheet. The 0932 it replaces was $1.23 (index) |
| K6 | Wall adapter 9 V 4 A 36 W, Class II, 5.5 x 2.1 mm plug centre positive | Mean Well GSM36U09-P1J | 1 | 1 | 21.91 | 21.91 | TRC Electronics | https://www.trcelectronics.com/products/mean-well-gsm36u09-p1j | page: $21.91 |
| K6b | Panel DC jack, 5 A 24 V, 2.0 mm pin (mates 5.5 x 2.1), 5/16-32 bushing, nut and washer | Same Sky PJ-005A | 1 | 2 | 3.07 | 6.14 | DigiKey | https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/PJ-005A/165838 | index: $3.07 at 1 (digikey.com.br, USD); 5 A rating read on the Same Sky data sheet: the old BLOCKER (3 A needed) is closed |
| K9 | Adapter input fuse holder, inline ATO, 16 AWG leads 90 mm | Littelfuse FHAC0001ZXJ, Newark 56P4171 | 1 | 1 | 7.74 | 7.74 | Newark | https://www.newark.com/littelfuse/fhac0001zxj/fuse-holder-in-line/dp/56P4171 | as BOM.md L3 |
| K9b | Adapter input fuse, 5 A ATO fast | Littelfuse 0287005.PXCN | 1 | 2 | 0.44 | 0.88 | DigiKey | https://www.digikey.com/en/products/result?keywords=0287005.PXCN | as BOM.md DK4 (index) |
| K11 | Wire: 20 AWG red and black, 26 AWG white, yellow, blue, green (cut lengths in dock_netlist.yaml) | BOM.md lines 23 and 25 surplus | 1 | 0 | 0.000 | 0.00 | (robot BOM) | https://www.amazon.com/BNTECHGO-Gauge-Silicone-Wire-Temperature/dp/B01F8PO5XE | the robot buys 50 ft of 20 AWG for 2.8 m and 175 ft of 26 AWG for 12.7 m |
| K12 | Heat shrink and solder (pin cups, jack lugs, holder leads) | BOM.md lines 26 and 30 surplus | 1 | 0 | 0.000 | 0.00 | (robot BOM) | https://www.amazon.com/Wirefy-180-Heat-Shrink-Tubing/dp/B084GDLSCK | 180 sleeves bought, 42 used by the robot |
| K12b | VHB 4950 pads under the charger board, the 2815 and the fuse holder | BOM.md line 29 surplus | 1 | 0 | 0.000 | 0.00 | (robot BOM) | https://www.amazon.com/dp/B00D3RD9TO | 3/4 in x 5 yd; about 0.09 m used here |
| K7 | PLA for the 18 printed dock kinds (21 prints), 1102 g sliced with the light profile | Overture Easy PLA 1.75 mm 1 kg black, ASIN B09LCK7QJ2 | 1 | 1 | 29.98 | 29.98 | Amazon | https://www.amazon.com/dp/B09LCK7QJ2 | as BOM.md line 27; one roll plus 102 g of the 593 g the robot leaves |
| K8a | Guide rods: 4 mm 304 stainless, 100 mm, 10 pcs, cut to 2 x 76 mm (cheaper than the 17-4PH OnDrive GPM4000-100 at $16.89 each; slide fit checked at BT1) | 4 x 100 mm 304 stainless rod, 10 pcs | 2 | 10 | 1.17 | 11.66 | eBay | https://www.ebay.com/p/21050690914 | index: $11.66 for 10 (whole pack in both totals) |
| K8c | Paddle return: constant-force spring 1.65 N, 6.4 mm drum, 4.75 x 0.08 mm, 304.8 mm | Century Spring CF37CS | 2 | 3 | 2.82 | 8.46 | Century Spring | https://www.centuryspring.com/shop/cf37cs | page: $2.82 (2026-11-06) |
| K8d | Seat springs: music wire, OD 7.14, ID 6.12, free 23.88 mm, 0.25 N/mm | Century Spring CC-28CS | 2 | 3 | 2.81 | 8.43 | Century Spring | https://www.centuryspring.com/shop/cc-28cs | page: $2.81 (2026-11-06) |
| K8e | M3x18 DIN 912 A2 (paddle pivot 2, drum axles 2) | BelMetric BSH3X18SS | 4 | 5 | 0.13 | 0.65 | BelMetric | https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/ | page data: $0.13 (2026-11-06) |
| K8f | M3x16 DIN 912 A2 (spring channels to the mast face) | BelMetric BSH3X16SS | 4 | 5 | 0.10 | 0.50 | BelMetric | https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/ | page data: $0.10 |
| K8g | M3x30 DIN 912 A2 (column rib bolts) | BelMetric BSH3X30SS | 9 | 10 | 0.14 | 1.40 | BelMetric | https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/ | page data: $0.14 |
| K8h | M3x12 DIN 912 A2 (spine flange 4, base to column 4) | BelMetric BSH3X12SS | 8 | 10 | 0.090 | 0.90 | BelMetric | https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/ | page data: $0.09 (2026-11-06) |
| K8l | M3x8 DIN 912 A2 (seat to spine 2, strip ends 2, gate board 2, bay tray 4, bay lid 4) | BelMetric BSH3X8SS | 14 | 16 | 0.090 | 1.44 | BelMetric | https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/ | page data: $0.09 (2026-11-06) |
| K8m | M2x12 DIN 7985 A2 pan head (seat microswitch) | BelMetric MSP2X12SS | 2 | 3 | 0.080 | 0.24 | BelMetric | https://belmetric.com/m2x0-4-phillips-pan-head-stainless-coarse-din-7985/ | page data: $0.08 (2026-11-06) |
| K8i | M3 nylon insert lock nut DIN 985 A2 (ribs 9, channels 4, axles 2): single nuts, not a 100-pack | BelMetric NN3SS | 15 | 17 | 0.090 | 1.53 | BelMetric | https://belmetric.com/nylon-locking-nut-a2-stainless-din-985/ | page data: $0.09 (2026-11-06) |
| K8n | M2 nylon insert lock nut DIN 985 A2 (switch) | BelMetric NN2SS | 2 | 3 | 0.58 | 1.74 | BelMetric | https://belmetric.com/nylon-locking-nut-a2-stainless-din-985/ | page data: $0.58 (2026-11-06) |
| K8o | M3 heat-set inserts (20) | BOM.md line 16 surplus (100 bought, 48 used) | 20 | 0 | 0.000 | 0.00 | (robot BOM) | https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces | 52 left |
| K8k | Ballast: 1018 bar 5/16 x 2-1/2 x 12 in, cut to 2 x 120 mm (one per base pocket, 474 g each) | Zoro Select 18F312X25-12 | 1 | 1 | 18.85 | 18.85 | Zoro | https://zoro.com/zoro-select-carbon-steel-bar-12-l-2-12-w-18f312x25-12/i/G301842078 | index: $18.85 |
| K10 | Rubber feet about 8 x 4 mm, 4-pack (seat base 4, base halves 8) | Adafruit 550 | 3 | 3 | 0.95 | 2.85 | Adafruit | https://www.adafruit.com/product/550 | page: $0.95 per 4 |
| K13 | Three AprilTags tag36h11 (id 0 at 40 mm, ids 1 and 2 at 60 mm), printed on paper and glued | paper | 3 | 0 | 0.000 | 0.00 |  |  | no purchase |

Dock station totals (read prices): **$186.46** need only (whole kits and packs where a kit or pack is the smallest buy), **$200.40** with spares. Not in them: K5 (BLOCKER: the 0933's price; at the 0932's $1.23 it would add $7.38 and $9.84), shipping. Duck side (BOM.md DK1 to DK7): **$83.76** need only, **$88.35** with spares. Dock and duck side: **$270.22** and **$288.75**. Cut against the sourcing list, function kept: K4e 2N3906 PNP (wake pulse) $0.54 (the 555 drives SENSE through D2 and R18; the PNP needed an inverter it never had); K8b ServoCity 4 mm collar 2-pack $4.99 (the printed carriage nose is the rest stop); K8i (old) Foreverbolt M3 nylon nut 100-pack $22.45 (15 single nuts at $0.09 (BelMetric) instead: $1.53 with 2 spares); K8j 3M 5490 PTFE tape $43.55 (the pins carry the push; the face is only an over-travel stop (sim run with friction 0.4 on the face: section 12.1)); K8a (old) OnDrive GPM4000-100 x 2 $33.78 (a 10-pack of 4 x 100 mm 304 rods at $11.66 (index)) (together $105.31).
<!-- dock-bom end -->

## 8. Bench tests (proposed; nothing run)
| Test | Pass |
|---|---|
| BT1 paddle: travel, force, swivel | 40 mm free travel; 2.96 to 3.62 N at 0, 20 and 40 mm (two CF37CS, constant force, section 12.1); returns to rest; swivels +/- 10 deg freely at any travel and lies flat on a board held 6 deg off square |
| BT2 pin to pad resistance, 4-wire, 1 A | 30 mOhm or less per pin |
| BT3 SENSE window with a decade box | on from 4.4 k (45 C) to 25.9 k (5 C) for a B3950 NTC; off open and shorted |
| BT4 pin-voltage window | off at 4.9 V and 8.6 V, on at 5.1 V and 8.4 V; a coin across the pins keeps it off |
| BT5 microswitch interlock | the charger stays off with the switch open whatever the comparators read; set the slotted switch so it closes at 5.0 mm of the 6.0 mm travel (about 3.8 N), the seat bottoms by 5.9 N (section 12.2) |
| BT6 MCP73213 EVM into the P45B pack | CV 8.40 +/- 0.04 V, CC 1.0 A (PROG via grounded), end of charge, timer fault after the set time; EVM under 85 C in a 32 C room |
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
8. CLEARED by section 12.1 (the 0933 data sheet gives the 1.600 mm hole, 45 gf, 1.397 mm). Was: the Mill-Max 0932 mounting hole (1.9 mm assumed in the paddle), its spring force and stroke (the sim takes a pin as touching
   when the chest is within 2 mm of its tip).
9. The soft floor is a compliant-contact stand-in for carpet; the real floors at home are not measured.
10. A limp hold on the seat for hours (torque off), and the STS3215 unpowered backdrive torque (section 11.5).
11. D50: the 9 V 4 A adapter and its price; the MCP73213 EV board's option code (A6S assumed); the 2813 ON pad position (a stand-in at its control pads, as D13); the NTC lead's fit into the cell seat.

## 10. Files
- Duck repo: altaay_lab/software/dock/ (autodock/, duck_autodock.yaml, tests/, THIRD_PARTY.md); altaay_lab/twin/dock/ (this file,
  dock_parts.py, chest_hole.py, seats/, stl/).
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
the duck gains only the fourth strip, two 0.2 g diode boards and a printed lead hole (about 1.5 g in all, calc); the dock gets the bigger adapter
(9 V 4 A, 36 W, against 15 W), two more spring pins and nothing else. No fan.

### 11.3 Charge times with the load running (calc only, charge_awake model: generic NCA/NMC OCV, ASSUMPTION; 2 x 15 mOhm cells plus 50 mOhm path)
Docked load: the 5 V branch 3 W typical, 5 W conservative (THERMAL_TWIN.md) plus servo idle and BEC, 0.62 A at the pack.

| Charger | Load on | From empty | From the 48 % go-home point | After 6 h from empty |
|---|---|---|---|---|
| MCP73213, 1.0 A (the EV board, section 12.5) | SYS (D50) | 4.7 h (calc, scaled) | 2.6 h | full |
| MCP73213, 1.1 A (needs R_PROG 1.00 k, not done) | SYS (D50) | 4.3 h, terminated at 99.6 % | 2.4 h | full |
| MCP73213, 1.1 A | the pack (3 contacts) | timer at 6 h, 64 % | timer at 6 h, never terminates | 64 % |
| BQ24610, 2.0 A | SYS (D50) | 2.5 h | 1.4 h | full |
| BQ24610, 2.0 A | the pack (3 contacts) | full, never terminates (float) | float | full, floating |

With SYS the load does not touch the charge current, so the MCP73213 stays (1.0 A on its EV board, section 12.5) (D45: linear, fewest parts, $44.90 against
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
- wiring/netlist.yaml carries the dock wiring since 2026-11-05 9:26 PM ET: components DKP, DK2, F2, RT1, WK1, DK6, DK7 and the inside splices JGD (GND) and JSN (SENSE); cables DC1 to DC4;
  the fused pack run P7 now ends at DK7 and SW1 VIN is the OR node PACK_OR. duck_side_netlist.yaml stays as the change record;
  dock_netlist.yaml is the dock.
- 3D routes: seats/route2.py (1 mm grid of the trunk parts and placed boxes, a shortest clear path, string pulled) writes
  dock_routes.json; dock_cables3d.py puts DC1 to DC4 into cables3d/cables3d.json. All in the trunk, no joint crossed. Cuts are the
  routed length plus 2 x 20 mm, one route per wire between its own two terminals: DC1 60, 60, 180 and 110 mm; DC2 60 and 210 mm;
  DC3 60, 220, 120 and 180 mm (WK1 to SW1 ON is an inline joint, cut 0); DC4 190, 70, 80, 60 and 70 mm. Every placed body (the
  printed parts, the bought-part boxes and the seated dock parts) is an obstacle; only each pad's lead exit (at most 3.5 mm) is
  open. route2.py fails its self-check if a wire has no route of its own or any route point lies inside a body (passed), and
  dock_cables3d.py refuses a wire that reuses another's run. The NTC runs into the cell seat keep 0.35 mm to the parts (test fit).
- Seats (seats/pick3.py, dock_seats.json, close-ups dock_seats.png, CAD check only): each board on VHB 4950 with its large face
  1.5 mm off a printed wall, clear of every part, placed box and routed cable by 1 mm:
  | Part | Centre (world mm, zero pose) | On |
  |---|---|---|
  | DK2 Pololu 5382 | (33, 0, 24) | the inner face of body_front, below the lead hole |
  | F2 holder, standing | (-85, -42, 26) | the left inner side wall of body_middle_bottom |
  | DK6 Pololu 5382 | (-104, 1, 45) | the underside of trunk_top, beside the 2813 |
  | DK7 Pololu 5383 | (-104, 13, 45) | the underside of trunk_top, 16 mm from SW1 VIN |
  No screw and no hole is added for the seats (D42, D39); the only hole is the 6.0 mm lead hole printed through body_front, which carries the leads.
- Paddle (D50): dock_parts.py makes the 4-row, 6-pin plate (z 140 to 230, knuckles at 140 to 152 and 218 to 230 clear of the
  pin reliefs); the clearance check over 0 to 40 mm of travel and +/- 10 deg of swivel finds no overlap; with the duck seated
  every pin sits 8.75 mm inside its strip's edges (a section in the duck frame, CAD check only). The dock sim in the shared lab
  gym (overlay gym/overlays/duck) has the same four strips and six pins: hard floor seeds 0 to 4 dock with all six pins on
  their strips (sim pass only).
- Chest feedthrough (chest_hole.py, CAD check only; section stl/chest_hole_section.png): print/body_front.stl has one 6.0 mm
  hole at world (y 0, z 38) through the 10 mm chest wall (x 36 to 46), behind the pad centre, with the strain relief printed in
  the wall: a 45 deg bell mouth 2 mm deep inside (10 mm across at the inner face) and a 0.8 mm 45 deg chamfer on the pad side,
  so the leads bend over a wide mouth, not a sharp edge. The part loses 0.33 cm3 and stays watertight; re-sliced (light
  profile) 57.63 g and 3.97 h against 57.56 g and 3.94 h, no support. A grommet ring 2 mm proud of the inner face was tried and
  dropped: the part prints +x up, so the ring hangs under the chest wall and the slicer adds 1.8 g of support inside the shell. Only the four pad conductors pass it: 3 x 20 AWG
  (1.9 mm) and 1 x 26 AWG (1.3 mm), a 4.6 mm bundle with 0.7 mm a side. GND and SENSE each leave the pad as one wire and branch
  at a splice inside the trunk, 60 mm in: JGD (to DK2 G and BMS P-) and JSN (to the NTC and the wake branch). DK2 still sits 1.5 mm off the
  wall; the grid and routes were rebuilt on the new STL (self-check passed, cuts unchanged). If close_holes.py output
  is copied into print/ again, run chest_hole.py --write after it (it refuses a file that already has the hole).
- U3 at 9.2 V: the Pololu D30V30F5 takes 5 to 45 V in (Pololu product page, read via the search index): passes, no change.
- The thermal and charge runs: scratch data (lab rule 8).

## 12. The full dock (2026-11-06, CAD check only, calc only, sim pass only where said)

Ahmed: "we need to model every component of it including wires and cables and screws and 3d shape.. etc", and "take your
time". Files: dock_parts.py (printed parts), dock_assembly.py (every component, the docked pose, interference and motion
checks; dock_assembly.json), dock_fasteners.py (dock_fasteners.json and .csv, built on altaay_lab/fasteners/make_fasteners.py),
dock_netlist.yaml and dock_erc.py, dock_routes.py (dock_cables3d.json), dock_design.py (dock_design.json), dock_bom.py
(dock_bom.json, section 7), dock_slice.py (stl/slice.json), dock_render.py (pictures, outside the repo), wiring sheet 7
(wiring/sheets/make_dock_sheet.py) and the Dock and Docked scenes of the viewer (viewer/dock_scene.py through
make_viewer_data.py --scene).

### 12.1 Paddle contact force (calc only; sim pass only for the walk)
- The old paddle: 2 x 37.5 N/m with no preload pushed 0.5 to 2.3 N over the sim's 7 to 30 mm pushes; six 0932 pins need
  6 x 0.59 = 3.53 N to reach mid stroke. Short pushes left each pin at 0.08 to 0.4 N.
- Fix, two parts:
  1. Pins: Mill-Max **0933-0-15-20-72-14-11-0** in place of the 0932. The 0932 solders into a PCB (0.74 mm hole), so it had
     no real mounting in a printed paddle (old BLOCKER 8). The 0933 presses into an insulator (1.600 mm hole max; print
     1.4 mm, drill 1/16 in), has a solder cup for the wire, 6 A (4.80 A derated), 40 mOhm max, 1.397 mm stroke and 45 gf
     (0.441 N) at mid stroke [Mill-Max data sheet, 8/8/25]. Six need **2.65 N** to reach mid stroke.
  2. Springs: two Century **CF37CS** constant-force springs (0.37 lb, 1.65 N each [page]): **3.29 N at any travel** from
     0 to 40 mm. The coil sits on a printed drum on an M3 axle at the front of an open-top channel behind the mast face; its
     strip end is screwed to a printed carriage pressed on the rod end (12 mm of strip out at rest, against the 8 mm the
     1.25 x drum rule asks). The carriage nose stops on the channel's front wall, so the shaft collar is gone.
- Per pin 0.549 N nominal; with the spring load +10 % (no tolerance on the page: BLOCKER, BT1): 2.96 to 3.62 N for the six,
  12 to 37 % over what mid stroke needs. Each pin is pressed 0.87 to 1.04 mm (linear spring or a 50 % preload; mid stroke
  0.699 mm). The tips stand **1.05 mm proud** of the face, so the face is only an over-travel stop at 75 % of the stroke.
  This holds over the whole window: fore-aft 0 to 40 mm (constant force), yaw to 10 deg (the swivel), lateral and vertical
  (pins on the strips, section 11.6).
- What the duck feels: 3.62 N at most (the old paddle 3.0 N at full travel, 1.3 N at the 17 mm mean push). The belly must
  hold it by friction: **0.52** at the lightest sit (7 N), against 0.33 before. The sim uses 1.0; PLA on PLA is lower:
  BLOCKER 10 now carries this (BT9), and a printed TPU or rubber grip strip on the seat top is the fallback (Ahmed's call).
- No PTFE tape: the pins carry the push. **Sim pass only** (the shared lab gym, overlay gym/overlays/duck, dock_sim.py
  acc10 settings, run on a scratch copy with the paddle at a constant 3.29 N and the face friction 0.4 for PLA on the pad;
  20 seeds per floor): hard 17/20, train 16/20, soft 10/20 docked within 3 tries, falls 0 / 1 / 10, every docked run with
  all six pins on their strips, pushes 9.1 to 27.6 mm (hard), undock 17/17, 16/16, 0/10. acc10 (75 N/m, PTFE 0.15): 18/20,
  16/20, 10/20, falls 0 / 1 / 10. Within one run of seed noise; the bar (19/20, no fall) stays unmet for the reasons of 4.6.
  A first bracket at 4.36 N and friction 0.15 (hard and train seeds 0 to 9) gave 8/10 and 9/10.

**Note for the shared lab gym (overlay gym/overlays/duck, dock/dock_course.py; not edited by this job):** PADDLE_K 75 N/m
with springref 0 becomes a constant 3.29 N (stiffness 1 N/m, springref -3.29 m on paddle_slide), the dock_bumper face
friction 0.15 becomes 0.4, PIN_PROUD 1.5 mm becomes 1.05 mm, and the dock_base box ends at x 0.220 instead of 0.190 (behind the mast, out of the duck's reach; section 12.6). The scratch copy used environment overrides for the
first two.

### 12.2 Seat, springs and switch (CAD check only, calc only)
- The seat top floats 6 mm on two Century **CC-28CS** (OD 7.14, ID 6.12, free 23.88 mm, 0.25 N/mm, solid 6.1, max 4.45 N
  [page]) in 7.6 mm pockets on the posts, round the 4 mm guide pins (11 mm in their bores at rest). Rest length 22.88 mm
  (0.50 N preload, the top weighs about 0.26 N); loaded 16.88 mm. Under a duck the top sits on the walls at **112 mm**, the
  sim's rigid seat (the old top floated at 112 and sank 4 mm under the duck).
- Force: 2.0 N at 3 mm, 3.78 N when the switch closes at 5.0 mm, 5.86 N bottomed with the finger flexed; the sim's lightest
  sit is 7 N. The old text asked 8 to 12 N, above that.
- Switch: Omron D2F-01L (OF 0.78 N max, OT 0.55 mm min, FP 10 mm max, OP 6.8 +/- 1.5 mm [data sheet]) on a slotted tower,
  2 x M2x12 and M2 nylon nuts, 4 mm of height to set at BT5. A printed 12 x 4 x 1.2 mm beam on the seat top (3.5 N/mm)
  presses the lever and flexes past its over-travel. The old seat top had no actuator at all.

### 12.3 Bolt holes and grips (CAD check only; dock_fasteners.json: 41 screws, 18 nuts, 20 inserts, all OK)
| Joint | Was | Now |
|---|---|---|
| Spine to base | holes at x 40 and 60 in the base, spine ends at x 30 | a 6 mm spine flange on the base (x 30 to 70), 4 x M3x12 into inserts (6.0 mm engaged) |
| Base to column | M3 from below into no bore | 4 x M3x12 from 3.2 mm counterbores into inserts in the column bottoms (5.2 mm engaged) |
| Seat to spine | M3x50 through 45 mm + 3 mm + nut: 0.4 mm short | 2 x M3x8 from inside the seat into inserts in the spine (5.0 mm) |
| Column ribs | 6 x M3x30, halves split at the same heights (stack held by nothing) | ribs 13 mm per half, splits staggered (l 160/310, r 210/360), 9 x M3x30 at a 50 mm pitch, nylon nuts (26 + 4.0 = 30 mm) |
| Spring cups | 4 x M3x16 at z 169/191 | 4 x M3x16 at z 163/197, clear of the coil, nylon nuts (8 + 3 + 4.0 = 15 mm) |
| Rods | 100 mm rods hit the cup end at 14 mm | 76 mm rods; the carriage stops 1 mm short of the channel end at 40 mm |
| Ballast | comment "100 x 120 x 10", pocket 7 mm deep | 120 x 63.5 x 7.9 mm bar per half in a 121 x 64.5 x 8.0 mm pocket, held down by the bay tray |
| Paddle pivot | 2 x M3x20 (1 mm past the knuckle) | 2 x M3x18 (11 mm in the knuckle pilot) |
Every screw's path meets no solid (each part has its bore or pilot), no head meets a part, and every tip stops 0.3 mm or
more short (ray cast). Every printed hole has its fastener (D39); each joint uses one size in a uniform pattern (D42).

### 12.4 Electronics, wiring and routes
- Bay: a printed tray (and lid with vents over the charger) behind the mast on both base halves, 4 x M3x8 into the base.
  Charger board (no holes; bump-ons off) and 2815 on VHB 4950 in printed rims; gate perfboard on 2 printed standoffs, 2 x
  M3x8 into inserts (both holes used); fuse holder on VHB in a rim; Same Sky **PJ-005A** jack (5 A [data sheet]: the old
  jack BLOCKER is closed; Adafruit 610 is out of stock) in the rear wall.
- Gate (dock_netlist.yaml gate_board, dock_erc.py): NTC window NTC window (10 k B3950, 10 k from 2.495 V): on from 43.2 C (0.793 V) down to 3.7 C (1.833 V); open reads 2.50 V, short 0 V: both off; pin window pack window through the duck's 100 k (charger off): on from 5.05 V to 9.23 V; charger on (direct): off above 8.59 V; a coin or nothing reads 0 V. The 2N3906 is gone: the 555 drives
  SENSE through a diode and 1 k; a second 2N3904 inverts STAT, with its pull-ups on the gated supply so the 555 does not
  fire again each time the gate closes (a pulse loop the old sketch had). U1 on the board is MCP73213-A6S (user's guide BOM).
- 18 wires, every one routed in 3D (dock_cables3d.json). The two harnesses are routed as bundles: the paddle cable KP1 (4 conductors, a 5.15 mm envelope with the centres on a circle, neighbours at least one OD apart, through a 9 mm face hole) and the seat switch pair KC5 (2.9 mm through the spine channel, the base groove and the tray floor); each conductor keeps its slot along the bundle (parallel-transport frame) and fans out at the ends; every other wire is routed after them and keeps clear of the wires already placed and of every pad it does not end on. Self-check **PASS**: each wire enters a body only in the 3.5 mm lead exits of its own two terminals and touches only its own parts; elsewhere its centre line keeps its radius from every body; and no two wires come closer than the sum of their radii outside the terminal zones they share (C12 fails on any overlap). Cuts = route + 2 x 20 mm (+ 20 mm on the paddle cable for its 40 mm of travel): the paddle cable 450 to 550 mm, the seat switch pair 370 and 320 mm. Sheet 7 draws all 18.

### 12.5 Charge current
The EV board ships at 500 mA and gives 1000 mA with its PROG via grounded (DS51849A section 2.3.1); 1100 mA would need
R_PROG 1.00 k (table 2-1). The design uses **1.0 A**. Charge model (dock_design.py, the same kind of generic OCV model as
11.3, calc only): from empty 4.28 h at 1.1 A, **4.69 h at 1.0 A**; from the 48 % go-home point 2.32 h and **2.53 h**.
Scaled onto 11.3: 4.3 h becomes **4.7 h** and 2.4 h **2.6 h**: inside the 6 h timer and the 6 h night. Section 5 heat ran at
1.1 A, a bound for 1.0 A.

### 12.6 Print, mass, cost
18 printed kinds, 21 prints, 1102 g and 77.7 h sliced with the light profile (stl/slice.json). Dock 2.12 kg, CG (x 108, y -1, z 78) mm, measured on the model (sliced grams at each part centroid, the bars at 7.87 g/cm3, bought parts at 2.0 g/cm3).

**Tipping** (dock_design.py, calc only; the check picks the pivot itself: the support hull of the 12 feet, its farthest point along each load). Target 3x (the CG and the loads are estimates; 3x covers the CG a third of the way to the edge or a load twice the estimate). The walk-in push (3.62 N at 185 mm, +x) tips the dock about its **rear** feet, not the seat edge the first version used (that gave 7.7x; about the old rear feet at x 188 it was 2.5x). The base halves now run to x 220 with the rear feet at x 214: **3.4x** (tips at 12.4 N). A seated duck (its CG at the sim's worst lateral error, or its whole weight at the seat's back corner) stays over the feet, now at the seat corners: 16.6x and 14.7x with the push; the corner case alone 119x. A child: a 5 N push or pull at the mast top (460 mm) tips it 1.0x +x (toward the back), 1.97x -x (toward the seat), 1.22x +y, 1.2x -y, i.e. at 5.0 / 9.8 / 6.1 / 6.0 N: **under 3x**. More ballast cannot fix that at this height (3x at 5 N needs about 6 kg more over the rear); the choices are a strap or two screws to the wall behind the mast, or a lower, wider mast (the tags set its height): Ahmed's call (12.7). BOM (section 7): **$186.46** need only, **$200.40** with spares (was $284.45 and $297.54); duck side
$83.76 and $88.35. Cut with no loss of function: PTFE tape $43.55, the OnDrive rods $33.78 (a $11.66 pack of 304 rods), the
100-pack of nuts $22.45 (single nuts), the shaft collars $4.99, the 2N3906 $0.54.

### 12.7 BLOCKERs added or changed
- K5 0933 price (digikey.com outside this session's network).
- CF37CS load tolerance (+/- 10 % assumed); the 1.25 x drum rule is a general rule, BT1 checks the force at 0, 20, 40 mm.
- Tipping by a child at the mast top (5 to 10 N tips it): a wall strap or a lower mast (Ahmed's call).
- Belly friction on the seat: 0.52 needed (BLOCKER 10, BT9).
- EV board outline (26.0 x 22.6 mm scaled from the layout), the Perma-Proto hole diameter (3.2 mm assumed), the 2815 pad
  positions, the D2F terminal order: read on the parts.
- Closed: old BLOCKER 8 (pin hole: the 0933 data sheet gives it), the jack rating, the EV board option code (A6S), the seat
  springs.
