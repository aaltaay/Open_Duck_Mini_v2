# Build guide: boxes of parts to a walking, docking Duckie

This is the path a second person can follow. It does not pass a gate.
[DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) says gates 0 through 8 are open.
A sim, a calc, and a CAD check are not a finished duck.
Nothing in this repo has been printed, bought, or run on a robot
([START_HERE.md](../START_HERE.md), [STATE.md](../STATE.md)).

Buy nothing from this page. Ahmed has to say yes, and gate 0 has to pass, before a full order
([DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md)). The part list is [BOM.md](../BOM.md) and
[BOM_FULL.md](../BOM_FULL.md). This guide does not copy prices.

## How to read a number

| Words next to a number | What they mean |
|---|---|
| cited | The number is copied from a decision, a netlist line, or a page the lab opened. |
| calc only | Arithmetic on those numbers. Not a measurement. |
| CAD check only | Measured on a mesh or on a fastener file. Not a fit on a printed part. |
| sim pass only | A simulation. Not a dock, a walk, or a charge on hardware. |
| BLOCKER | Not known, or not designed. Do not fill it in. |

If this page and a source file disagree, the source file named in the step wins.
Where an older file still prints a superseded voltage, this page says so in that step.
[DECISIONS.md](../DECISIONS.md) D61 is not edited by this guide.

Every step that touches a part, a print, a wire, or a powered robot is marked
**never done on hardware**.

## What you are building

Duckie is an Open Duck Mini v2: a small biped, a Raspberry Pi Zero 2 W in the head,
14 serial-bus joint servos, and a felt nest it is meant to find with the camera and sit on.
The story and the pins are in [START_HERE.md](../START_HERE.md) and [README.md](../README.md).

The mat to build is nest version 2, [cad/nest_v2/](../cad/nest_v2/NEST_V2.md).
Nest versions 3, 4, and 5 are studies only
([cad/nest_v3/DECISION.md](../cad/nest_v3/DECISION.md),
[cad/nest_v4/NEST_V4.md](../cad/nest_v4/NEST_V4.md),
[cad/nest_v5/NEST_V5.md](../cad/nest_v5/NEST_V5.md)).
Do not print them and do not cut a mat from them.

The duck-side charge contact is the gold domes: five wells, each a 1.5 mm radius cap standing
0.9 mm proud of the seat face (sim pass only, [twin/dock/camera/SEAT_CONTACTS.md](../twin/dock/camera/SEAT_CONTACTS.md)).
The nest v2 mesh and its belly render still show flush wells. Flush wells charged 0 of 40 sits
in that study. The 0.9 mm domes charged 38 of 40 (sim pass only). Leave the domes.
Do not swap in belly plates ([twin/dock/camera/BELLY_DECISION.md](../twin/dock/camera/BELLY_DECISION.md)).

Do not build the four spring pins. That drawing is superseded
([twin/dock/nest/cad/NEST_CAD.md](../twin/dock/nest/cad/NEST_CAD.md)).
Do not wire from [wiring/sheets/7_dock.svg](../wiring/sheets/7_dock.svg). That sheet is the older paddle dock.

Pictures for this section:

- Nest from above, rendered from the nest v2 meshes: [images/nest_mat_top.png](images/nest_mat_top.png).
- The same mat from the original CAD render: [cad/nest_v2/renders/mat_top.png](../cad/nest_v2/renders/mat_top.png).
- Sit on the mat: [cad/nest_v2/renders/sit_three_quarter.png](../cad/nest_v2/renders/sit_three_quarter.png).
- Belly render, flush wells, not the proud domes: [cad/nest_v2/renders/belly.png](../cad/nest_v2/renders/belly.png).
- Dome height to form: [images/gold_domes.png](images/gold_domes.png).

## 1. Tools

Names and BOM line ids only. Specs and links stay in [BOM.md](../BOM.md) under Tools and Test equipment.
Do not buy from this list until Ahmed says yes.

| Job | Bring | BOM line |
|---|---|---|
| Solder | Pinecil V2, PD supply, USB-C cable | T1, T6, T6b |
| Heat-set inserts | Pinecil insert tips | T2 |
| Crimp Mini-SPOX | Engineer PA-09 | T3 |
| Hex screws | Bondhus 1.5 mm to 6 mm L-keys. M2.5 uses 2.0 mm. M3 socket head uses 2.5 mm. M3 button head uses 2.0 mm. | T4 |
| Strip 22 to 32 AWG | Klein 11057 | T5 |
| Strip 12 to 20 AWG | Klein 11055 | T9 |
| Program the old Castle part, only if a Castle part is still in the harness you are holding | Castle Link V4 and a Windows PC | L2 |
| Heat shrink | Wagner Furno 300. Shrink a joint before it is near printed PLA. | T10 |
| Hand drills after printing | 6.0, 2.7, 4.0, 4.5 mm bits, 1/16 in bit, T-handle | T11, T12, T14, T15, T19, T13 |
| Cross-head screws | Wera PH0 x 60, PH1 x 80, PH0 x 25 mm bit | T16, T17, T18 |
| Meter, supply, calipers, load | Klein MM420, Siglent SPD1168X, iGaging calipers, Siglent SDL1020X-E | TE1, TE2, TE3, TE4 |

Threadlocker is Loctite 243, BOM line 19. Use it only where a later step says metal into motor metal.

Status of buying any of these: **never done on hardware**. Nothing has been bought.

## 2. Printing

Follow [print/PRINT_PLAN.md](../print/PRINT_PLAN.md) and check each plate against
[PRINT_CHECK.md](../PRINT_CHECK.md). The slicer settings, the coupon pass table, and the plate list
live there. This page does not copy them.

Printer bed at least 220 mm by 220 mm (cited, [START_HERE.md](../START_HERE.md)).
The printer model is not in the lab files. BLOCKER until Ahmed names one.
Dry the TPU as the maker page in PRINT_PLAN says before the sole prints.

### 2.1 Coupon session first

1. Print S1 (PLA coupons) and S2 (one TPU sole) from [print/PRINT_PLAN.md](../print/PRINT_PLAN.md) step 1.
   Status: **never done on hardware**.
2. Measure each coupon with the pass table in that same step. Calipers are TE3.
   Status: **never done on hardware**.
3. If a light coupon fails a test its heavy twin passes, keep 4 walls on the ten insert-ring parts,
   as that table says. Do not invent a new profile.
   Status: **never done on hardware**.
4. Do not start the right leg until D26 is decided
   ([START_HERE.md](../START_HERE.md) open decisions). The structure twin is under the margin it uses
   on roll_to_pitch and the knee sheet eye (sim pass only, FEA pass only,
   [twin/structure/STRUCTURE_TWIN.md](../twin/structure/STRUCTURE_TWIN.md)).

Picture: there is no photo of a coupon. The pass rules are the table in PRINT_PLAN step 1.

### 2.2 Left leg, then the rest

5. Print the left leg plates (PRINT_PLAN step 2). Run the seven left-leg checks in that step,
   including the hip-roll screw rub and the hip-pitch button heads.
   Status: **never done on hardware**.
6. Print the remaining plates (PRINT_PLAN step 3). Trunk bottom and the neck plates wait on the
   coupon rules named there. The head is the long job. Print it last.
   Status: **never done on hardware**.
7. Do not copy a topology STL or a shin-eye STL into the print folder
   ([print/PRINT_PLAN.md](../print/PRINT_PLAN.md)). Without the recess already drawn,
   the horn screws do not seat ([cad/fasteners/ASSEMBLY.md](../cad/fasteners/ASSEMBLY.md)).

### 2.3 Drills after printing

Hand tools only. The coordinates are in PRINT_PLAN, "After printing". Do not change an STL.

8. Open the 24 neck-chain recesses from 5.5 mm to 6.0 mm. Try it on coupon C4 first.
   Status: **never done on hardware**.
9. Open the four battery-lid clearance holes from 2.5 mm to 2.7 mm.
   Status: **never done on hardware**.
10. Open M2 head recesses to 4.5 mm only if coupon C4 showed a head that does not drop in.
    Status: **never done on hardware**.
11. Drill the projector lead hole (D24) at the point PRINT_PLAN gives, before the projector parts go in.
    Status: **never done on hardware**.
12. Drill the three cable-tie hole pairs (D25). Deburr both sides.
    Status: **never done on hardware**.
13. Drill the four camera pilots from 3.2 mm to 4.5 mm deep with the 1/16 in bit. Tape a flag at 4.5 mm.
    The pilot stays 1.65 mm across (CAD check only, PRINT_PLAN after-printing step 6).
    Status: **never done on hardware**.

## 3. Fasteners and torque

The schedule is [fasteners/FASTENERS.md](../fasteners/FASTENERS.md) and
[fasteners/fasteners.json](../fasteners/fasteners.json).
How to read torque, washers, and threadlocker is [cad/fasteners/SCHEDULE.md](../cad/fasteners/SCHEDULE.md).
The drive order is [twin/assembly/BUILD_ORDER.md](../twin/assembly/BUILD_ORDER.md).

Do not drive a screw whose status says LEAVE OUT or NOT FITTED.
The factory case screws stay as they arrived. Do not open a servo to add locker.

### 3.1 Torque

No build torque is set.

The cited dry A2 table in SCHEDULE.md (RLS TTD01_03, 6 Dec 2023) prints 0.35 Nm, 0.7 Nm, and 1.2 Nm
for DIN 912 M2, M2.5, and M3, and 0.19 Nm, 0.37 Nm, and 0.6 Nm for ISO 7380 M2, M2.5, and M3.
That page also requires a thread depth this duck does not have. Chart torque applies to 0 of 324
fitted screws (CAD check only, SCHEDULE.md). Do not use those newton-metre numbers on this duck.
Snug with the short arm of the key, the same check the coupon table uses. If an insert spins or a
plastic pilot strips, stop. That is a fail, not a cue to add force.

Picture of the count, CAD check only: [cad/fasteners/installed_screw_checks.png](../cad/fasteners/installed_screw_checks.png).

### 3.2 Threadlocker and washers

14. Loctite 243 only where the screw is metal against metal in a motor: horn screws and output-shaft
    screws (cited, SCHEDULE.md, from the upstream assembly guide). No locker on screws into plastic,
    screws into inserts, or factory case screws.
    Status: **never done on hardware**.
15. Eye screws: two 0.3 mm washers under each fitted M2.5x8 head (cited, D21, FASTENERS.md).
    The stack is the T1 coupon. Do not drive a bare M2.5x8 into the eye floor.
    Status: **never done on hardware**.
16. Heat-set the M3 inserts with the Pinecil insert tip until each insert ends flush, the same check
    as coupons C2 and C3. FASTENERS.md counts 48 inserts (CAD check only). A pull-out number on these
    printed bores is still open in that file. BLOCKER for a pull-out torque.
    Status: **never done on hardware**.

Where each board sits is [MOUNTING.md](../MOUNTING.md). Electronics pilots are printed holes.
An M2.5 machine screw cuts its own thread. There is no nut on the robot (CAD check only, FASTENERS.md).

## 4. Assembly

Drive screws in [twin/assembly/BUILD_ORDER.md](../twin/assembly/BUILD_ORDER.md) order.
A part goes on just before its first screw. JOIN marks a screw that joins two subassemblies.
The rules at the bottom of that file are part of the order: trunk core before the centre servo,
horn centre screw before the part that covers it, camera screws before the head-roll servo,
battery-lid screws only after the cells are in.

The 2026-11-04 tool cast was not re-run for the later mic and cliff screws. Their tools are the
PH0 and the 2.0 mm hex that file already uses (CAD check only, [cad/fasteners/ASSEMBLY.md](../cad/fasteners/ASSEMBLY.md)).

Status of the whole sequence: **never done on hardware**.

| Step | What you join | BUILD_ORDER lines | Picture or file |
|---|---|---|---|
| 17 | Trunk core: trunk_top into trunk_bottom, then the centre servo case screws | lines 1 to 3, and the trunk-core rule | BUILD_ORDER rules |
| 18 | Servo horns: centre screw into the output shaft before the link covers it | lines 4 to 22, and later horn lines as you reach them | FASTENERS.md. Locker only on metal into the motor. |
| 19 | Both feet: foot plates, TPU sole, horns | lines 23 to 30 | PRINT_PLAN left-leg check 4 |
| 20 | Both shins: knee sheets, spacers, thigh covers, button heads at the hip pitch | lines 31 to 54 | PRINT_PLAN left-leg check 5. Button heads are BOM 17j. |
| 21 | Both hips: roll_to_pitch, roll motor shells | lines 55 to 72 | PRINT_PLAN left-leg check 2. Stop if the outer hip-roll screw rubs. |
| 22 | Cliff board while body_front is in the hand, then body shells | lines 76b to 78 | MOUNTING.md V1 freeze |
| 23 | IMU, adapter board, charger screw, battery lid | lines 79 to 82 | MOUNTING.md. Lid holes already drilled in step 9. |
| 24 | Body back to the middle shells | lines 83 to 84 | MOUNTING.md D42 note |
| 25 | Neck sheets and head pitch linkage | lines 85 to 93 | PRINT_CHECK.md neck note |
| 26 | Head yaw, head roll, Pi, mics, eyes, camera, ears, speaker, head bottom sheet | lines 94 to 112 | MOUNTING.md. Neck pitch at -9.4 deg for F083 and F084 (BUILD_ORDER line 111). |

27. After the mechanical stack, do the dry fit in [TEST_PLAN.md](../TEST_PLAN.md) section 13
    before any power. Note any part that cannot move into place.
    Status: **never done on hardware**.

Servos are not powered in this section. Hip yaw must not be forced past the screw clash at 21.7 deg
(cited, TEST_PLAN 8.2a, D19). You will hold it by hand again at first power.

## 5. Harness

Build one cable at a time from [HARNESS_BUILD.md](../HARNESS_BUILD.md).
That sheet is generated from [wiring/netlist.yaml](../wiring/netlist.yaml). Do not edit it by hand.
Cut length, colour, and end treatment are on each cable's own lines. Label both ends before the cable
goes into the body.

Routes, ties, and joint loops are [cables3d/CABLES_3D.md](../cables3d/CABLES_3D.md) and
[CABLE_MAP.md](../CABLE_MAP.md). The length rule is at the top of CABLE_MAP. A cable marked test fit
reaches in CAD with less than the slack rule. TEST_PLAN 1.4 decides it on the parts.
S5, S10, SP4, and SP5 are short of that slack rule (CAD check only, [twin/sit/SIT.md](../twin/sit/SIT.md)).
BLOCKER until the test fit.

Drawings, one subsystem per sheet, from the netlist
([wiring/sheets/WIRING_SHEETS.md](../wiring/sheets/WIRING_SHEETS.md)):

- Power: [wiring/sheets/1_power.png](../wiring/sheets/1_power.png)
- Servo bus: [wiring/sheets/2_servo_bus.png](../wiring/sheets/2_servo_bus.png)
- Pi and sensors: [wiring/sheets/3_pi_sensors.png](../wiring/sheets/3_pi_sensors.png)
- Head expression: [wiring/sheets/4_head_expression.png](../wiring/sheets/4_head_expression.png)
- Harness overview: [wiring/sheets/5_harness.png](../wiring/sheets/5_harness.png)
- Touch and cliff: [wiring/sheets/6_touch_cliff.png](../wiring/sheets/6_touch_cliff.png)

Sheet 1 still draws a Castle BEC and calls the switch a 2815. Read the voltage note in section 6
before you program anything. Do not print [wiring/sheets/7_dock.svg](../wiring/sheets/7_dock.svg)
for this build.

### 5.1 Order

28. Battery bay power. HARNESS_BUILD section 1 (P1 through P16) is the cut list that was generated
    on 2026-11-06. It still shows one series strap to B1 and a cell holder.
    The live pack in [wiring/netlist.yaml](../wiring/netlist.yaml) is three Molicel P45B cells,
    spot welded, with two taps, B1 and B2, and no holder (cited, the pack part in that file).
    The window is 9.0 V to 12.6 V (cited, domain PACK_9V0_12V6).
    [START_HERE.md](../START_HERE.md) still says a 2S pack in its opening lines. That sentence is older
    than D65. Do not build two cells.
    The harness sheet has not been regenerated for the third tap. BLOCKER. Do not invent a weld.
    Use the netlist pin names. Do not follow the holder wording in section 1, and do not follow the
    2S holder story in [WIRING.md](../WIRING.md) section 1.
    Status: **never done on hardware**.
29. Belly servo power. HARNESS_BUILD section 2 (P11, SP1 to SP5).
    SP4 and SP5 are V and G only. Leave the data cavity empty (cited, D23).
    Status: **never done on hardware**.
30. Servo data leads and kit cables. HARNESS_BUILD section 3.
    Copy a kit-cable housing for every made lead. Pin order is in WIRING.md section 2.
    Status: **never done on hardware**.
31. Neck power to the head floor and the Pi. HARNESS_BUILD section 4 (P13, P12, P17).
    Status: **never done on hardware**.
32. Pi, IMU, and feet. HARNESS_BUILD section 5.
    Status: **never done on hardware**.
33. Head expression. HARNESS_BUILD section 6. Eyes stay white (cited, D57).
    Status: **never done on hardware**.
34. Touch and cliff. HARNESS_BUILD section 9.
    Status: **never done on hardware**.
35. Dress splices, drilled tie holes, and the bundle ties named at the end of HARNESS_BUILD.
    75 tie points are the D25 set in [START_HERE.md](../START_HERE.md).
    Status: **never done on hardware**.

### 5.2 Do not install these harness sections as drawn

36. HARNESS_BUILD section 7 is the chest-pad dock (D43, D50), not the gold domes.
    [circuitry/SERVO_RAIL.md](../circuitry/SERVO_RAIL.md) says the nest does not connect to the
    switch input. DK6 is not on that VIN. Do not land 15.0 V on the servo bus.
    The in-duck charger is the TI BQ24133 (cited, netlist and
    [circuitry/CHARGER_BOARD.md](../circuitry/CHARGER_BOARD.md)). It has no seat and no screw
    ([cad/fasteners/ASSEMBLY.md](../cad/fasteners/ASSEMBLY.md)). BLOCKER.
    Belly diodes so a well on either stripe still feeds the charger the right way are not chosen
    (BLOCKER, [cad/nest_v2/NEST_V2.md](../cad/nest_v2/NEST_V2.md)).
    Status: **never done on hardware**.
37. HARNESS_BUILD section 8 cable D13 is the Pi GPIO26 wire to a Pololu 2813 OFF pin.
    The netlist says that 2813 record is not the rail to build. The 2815 rail has no OFF pin
    (cited, netlist header and SERVO_RAIL.md). Do not add that OFF wire unless a later decision
    puts the 2813 back. The mic half of section 8 (D47) does still match MOUNTING.md.
    Status: **never done on hardware**.

## 6. Wiring checks before any power

Rules from [TEST_PLAN.md](../TEST_PLAN.md): never connect or disconnect a cable with power on.
First power is a current-limited bench supply, never the pack.

38. Mechanical check of every made cable. TEST_PLAN section 1: crimp pull, connector fit,
    heat shrink, twist lay, loops, and the 75 ties. Turn joints by hand. Keep head yaw inside
    plus or minus 45 deg on the first passes, and stop at the first pull (TEST_PLAN 1 and 8.2b).
    Status: **never done on hardware**.
39. Continuity and polarity. TEST_PLAN section 2, using
    [audit/continuity_checklist.csv](../audit/continuity_checklist.csv).
    Read ohms, not the beep. Pass in that section: under 1 ohm on the wire, over 1 Mohm between
    different nets on the same connector. On every servo lead the pin order matches the STS3215 port.
    Red is plus on the regulator output. XT30 plus goes to plus.
    Status: **never done on hardware**.
40. Kelvin hop. TEST_PLAN section 5. Pass at most 28 mOhm per conductor, warn over 28 up to 40 mOhm,
    fail over 40 mOhm (cited, lead decision L3). Those bands were written for the 2S story.
    A hop number for the 12.0 V rail is not a new pass line in that section. BLOCKER until the
    plan is rewritten. Still measure and write the ohms down. Do not skip the measurement.
    Status: **never done on hardware**.

The electrical rule check of the netlist is [audit/ERC_REPORT.md](../audit/ERC_REPORT.md).
Re-run it from the repo when the netlist changes. A previous run is not this build.

## 7. First power-on

Read this whole section before you turn a knob.
Status of every power step: **never done on hardware**.

### 7.1 Live voltages

| Rail | Number | Label |
|---|---|---|
| Pack window | 9.0 V to 12.6 V | cited, netlist PACK_9V0_12V6 |
| Walk stop | 10.0 V at the pack | cited, D65, netlist walk_stop_v |
| Servo rail set point | 12.0 V | cited, D65. The part is the TDK-Lambda i7C2W020A120V-0F1-R. |
| Servo rail pass band | 11.52 V to 12.48 V | cited, netlist SERVO_12V0, plus or minus 4 percent |
| Nest supply | 15.0 V | cited, [circuitry/SERVO_RAIL.md](../circuitry/SERVO_RAIL.md) |
| 5 V rail | 4.80 V to 5.20 V | cited, [software/DAY_ONE.md](../software/DAY_ONE.md), netlist domain 5V |

A 7.2 V reading on the servo rail fails (cited, DAY_ONE.md).
D63 set a Castle BEC to 12.0 V. D65 replaced that part with the i7C and kept 12.0 V
(cited, [DECISIONS.md](../DECISIONS.md)).
TEST_PLAN sections 4, 8, 9, and 11 still tell you to program 7.2 V and to use 7.4 V at the XT30.
Do not. Those voltages are the superseded 2S rail.
[WIRING.md](../WIRING.md) section 1 is the same older path. Use it for connector names and pin order.
Do not use it for the pack voltage or the servo set point.

The i7C input range that was cited is 9 V to 36 V (D65). A bench supply standing in for the pack
must sit inside 9.0 V to 12.6 V. Below 9 V the cited input range does not cover the part.

The bench supply TE2 stops at 8 A (cited, TEST_PLAN section 0). It cannot reproduce a walk peak
above that. The 1 A, 3 A, and 8 A steps in TEST_PLAN section 8 were written for the old rail.
Whether those amp limits still bound this 3S robot is BLOCKER. Use them as a ceiling, not as a
claim about current. Start at the 1 A limit with torque off. Stop if a part gets hot or the servo
rail leaves 11.52 V to 12.48 V.

### 7.2 Safety sequence

41. Mass and centre of mass before the first walk, TEST_PLAN 8.0. The expected kilograms in that
    line are the older mass model. Weigh the duck and write the number down. Do not "correct" it
    to a sim figure.
42. Mate the XT30 only with the switch off.
43. Bench supply in place of the pack, current limit on, torque off. Confirm every servo answers
    with the id in [software/SOFTWARE.md](../software/SOFTWARE.md) section 2
    (left leg 20 to 24, neck 30 to 33, right leg 10 to 14).
44. One hand on the supply's output switch for the rest of this section.
45. Hip yaw: keep both hips inside plus or minus 20 deg. Screws touch the shell past 21.7 deg
    (cited, TEST_PLAN 8.2a). Nothing in the Runtime clamps that joint.
46. Head yaw: keep it inside plus or minus 45 deg until the cable test fit has passed
    (cited, TEST_PLAN 8.2b).
47. Torque on only while the robot hangs, feet off the ground, nothing in reach of a leg or the head.
    TEST_PLAN 8 steps 2 and 3. The Runtime script find_soft_offsets.py moves every joint at once. That script is not in this repo.
    ([software/PI_SETUP.md](../software/PI_SETUP.md) step 10).
48. Do not put the pack in until TEST_PLAN sections 3 and 4 have a measured pass on the parts you
    actually fitted, with the voltages in the table above written into a new history file.
    The BMS trip procedure in TEST_PLAN 3.3 is the Tenergy board on the old pack voltage.
    A trip current for the 3S pack is BLOCKER until that section is rewritten. Do not short the pack.
49. After any battery hard stop, switch the duck fully off. Do not leave it on and walk away
    (TEST_PLAN section 11). The self-off behaviour of the 2813 is not this rail.

Pololu's own warning, quoted in WIRING.md: the main switch is not an emergency cutoff.
The XT30 is the disconnect. Pull it with the switch already off, and with your hand on the duck.

## 8. Pi install

50. Flash and the first boot are [software/PI_SETUP.md](../software/PI_SETUP.md) steps 1 to 9.
    Bookworm, not a newer default, as that file says. The Runtime stays unmodified (cited, D6).
    Status: **never done on hardware**.
51. On the Pi, from a checkout of this repo:

```bash
bash altaay_lab/software/install_pi.sh
```

The script is described in [software/DAY_ONE.md](../software/DAY_ONE.md). It does not enable the
walk service. Personality, the dock, the knee-heat guard, and the battery guard stay in this repo.
Status: **never done on hardware**. The mock run named in DAY_ONE.md is what CI uses.
That mock is not a Pi.

52. Check:

```bash
bash altaay_lab/software/check_pi_setup.sh
```

Status: **never done on hardware**. The script is read-only (PI_SETUP.md step 13).

53. Do not enable [software/odm-walk-guard.service](../software/odm-walk-guard.service) until the hanging walk and the floor walk in section 10
    have a written pass (PI_SETUP.md step 11).

## 9. Day-one bench and calibration

54. On the Pi, with the adapter on the serial device DAY_ONE.md names, and a meter, run the day-one bench in
    [software/DAY_ONE.md](../software/DAY_ONE.md). Pass the servo rail only if the meter reads
    11.52 V to 12.48 V. Pass the 5 V rail only at 4.80 V to 5.20 V.
    Camera frame rate, eye current, ear speed, mic latency, and contact ohms are BLOCKER.
    The script records them and does not invent a pass line.
    Status: **never done on hardware**.
55. Joint zeros: [software/CALIBRATION.md](../software/CALIBRATION.md), after the horns are on,
    robot on its back, bus powered from the bench supply inside the pack window.
    Five presses on each D59 stop. Pass there: spread 0.3 deg or less, then each joint reads its
    stop within 0.5 deg and the two legs agree within 0.5 deg.
    The real repeatability is BLOCKER until those five presses exist.
    Status: **never done on hardware**.
56. Write angle limits again after the offsets, as CALIBRATION.md step 5 and PI_SETUP.md step 10.
    Software limits sit 3 deg inside the printed stops (cited, CALIBRATION.md,
    [software/servo_limits.json](../software/servo_limits.json)).
    Status: **never done on hardware**.
57. IMU: PI_SETUP.md step 10.2, then TEST_PLAN section 10. Software I2C first.
    The sign of a nose-down pitch is BLOCKER until the tilt check passes (MOUNTING.md).
    Status: **never done on hardware**.

## 10. First walk

58. Hanging walk only, current limit at the supply's 8 A ceiling, feet off the ground,
    one hand on the off switch. PI_SETUP.md step 10.6. Policy file and command are in that step.
    The stock policy file named there is not the later run D policy.
    Run D is the twin default (cited, D66, [DECISIONS.md](../DECISIONS.md)).
    Which file the first hardware walk should load is BLOCKER until Ahmed picks it.
    Do not swap files on your own.
    Status: **never done on hardware**.
59. Floor: soft floor, a tether or a hand behind the duck, as TEST_PLAN section 9 asks Ahmed to
    decide (B45). After any fall, look at the parts that section names before you walk again.
    Status: **never done on hardware**.
60. Walking voltage log: TEST_PLAN section 9 and [bench/power_log.py](../bench/power_log.py).
    The 6.0 V servo gates in that section belong to the old 2S bus.
    On this rail the servo voltage should stay inside 11.52 V to 12.48 V while the regulator holds,
    and the pack must stay above the 10.0 V walk stop (cited, D65).
    A rewritten pass line for the log is BLOCKER. Still log every servo. Stop if the pack falls
    to 10.0 V or a knee reading reaches the 55 C walk stop
    (cited, [software/personality/PERSONALITY.md](../software/personality/PERSONALITY.md)).
    Status: **never done on hardware**.
61. Knee heat: the guard stops the walk at 55 C and walks again at 45 C (cited, PERSONALITY.md).
    Those are set points from the guard, not a measured knee on this duck.
    Status: **never done on hardware**.

Get-up from a fall is sim pass only ([twin/sit/getup/VIA_SIT_EVAL.md](../twin/sit/getup/VIA_SIT_EVAL.md)).
It is not a step you can sign off. Two misses in the supervisor sit and wait
([software/autonomy/AUTONOMY.md](../software/autonomy/AUTONOMY.md)).

## 11. Nest

The mat is not in the print folder and not in BUILD_ORDER.md. Build it from
[cad/nest_v2/](../cad/nest_v2/NEST_V2.md). Nothing in that folder has been built.

62. Cut the two felt sheets and the foil stripes to the stations in NEST_V2.md.
    Lower felt from the front edge, upper felt 1 mm, walking surface 2.00 mm (CAD check only).
    23 foil stripes, 20 mm, with 5 mm felt gaps (CAD check only). Even periods plus, odd periods minus.
    Status: **never done on hardware**.
63. Cord pocket from [cad/nest_v2/stl/cord_pocket.stl](../cad/nest_v2/stl/cord_pocket.stl) and [cad/nest_v2/stl/cord_cap.stl](../cad/nest_v2/stl/cord_cap.stl). No screws on that pocket
    (CAD check only, NEST_V2.md). The gate board that would sit in it is not designed. BLOCKER.
    Do not leave the stripes powered. A coin can bridge the 5 mm gap (BLOCKER, NEST_V2.md).
    Status: **never done on hardware**.
64. Place the mat against the wall. Sun to wall is 190 mm (cited, NEST_V2.md).
    The 40 mm wall card is not approved. D61 said no markers. NEST_V2.md asks Ahmed to say yes or no.
    Do not stick the card on until he does. The STL still shows it. That is not approval.
    Status: **never done on hardware**.
65. Form the five gold domes in the seat, 12 mm apart, 0.9 mm proud, 1.5 mm radius
    (sim pass only, SEAT_CONTACTS.md). Picture: [images/gold_domes.png](images/gold_domes.png).
    The flush wells in [cad/nest_v2/stl/seat_wells.stl](../cad/nest_v2/stl/seat_wells.stl) are the mat study, not this proud height.
    Contact resistance with dust, hair, and felt is BLOCKER.
    Status: **never done on hardware**.
66. Do not fit nest lid screws from the superseded pin CAD unless you are looking at that archive
    on purpose. [cad/fasteners/ASSEMBLY.md](../cad/fasteners/ASSEMBLY.md) says those steps are not
    this mat. No new screw on the duck for the domes.
67. Dock program: the supervisor starts a camera dock when the pack is at or under 10.8 V and still
    above 10.0 V (the 10.8 V line is a set point, [software/autonomy/AUTONOMY.md](../software/autonomy/AUTONOMY.md)).
    States are search, approach, turn, fine, sit. No tags. Nest v3, v4, and v5 are not used.
    A live camera on the Pi is BLOCKER. Charge on a real board is BLOCKER.
    Status: **never done on hardware**.
68. Bench the nest only after the coupon tests that still apply. TEST_PLAN section 20 was written
    for spring pins. Do not press those pins into this mat. Keep the safety ideas: a gate that
    refuses water, metal, and a skin stand-in (TEST_PLAN 20.5), cells 0 C to 45 C and nearest PLA
    under 45 C during a full charge (TEST_PLAN 20.8), and a camera find with no tag (TEST_PLAN 20.9).
    None of those have been run. The gate board is BLOCKER, so 20.5 cannot pass yet.

Picture of the mat you should see from above: [images/nest_mat_top.png](images/nest_mat_top.png)
and [cad/nest_v2/renders/sit_side.png](../cad/nest_v2/renders/sit_side.png).

## 12. Stop here

You do not have a second duck, and you do not have a home robot, until the gates in
[DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) pass on hardware.
The owner-facing pages are [OWNERS_MANUAL.md](OWNERS_MANUAL.md).
Write every measurement in a new file in the history folder. Do not edit an old history file. The note for this guide is [history/2026-11-19_1405_build_and_owners_docs.md](../history/2026-11-19_1405_build_and_owners_docs.md).
