# UPSTREAM_ISSUES: every issue and PR in the four Open Duck Mini repos

Date read: 2026-11-01 (America/New_York). Written by a Claude Code research agent (branch claude/print-ready) for the owner bot, Legged Robots, Grok Bot agent of Ahmed Altaay. Read only: nothing was posted, commented, reacted to, committed or pushed, upstream or here.

Repos (owner apirrone): Open_Duck_Mini ("Mini" below), Open_Duck_Mini_Runtime ("Runtime"), Open_Duck_Playground ("Playground"), Open_Duck_reference_motion_generator ("RefGen").

Our build, used to judge relevance: stock v2 at b23317a with the lab changes in DECISIONS.md D1 to D12: servo bus at 7.2 V from a Castle CC BEC Pro, 15 A ATO fuse, Tenergy 32175 2S board (10 A working), Pololu 2815 MOSFET switch run by the stock panel switch, 5 V regulator on the head floor, GPIO wired to the Runtime code (D9), STS3215 C001 7.4 V servos, BEST_WALK_ONNX_2, Pi Zero 2 W. Later lab steps: AprilTag self-docking with pogo pins, get-up after falls. Stairs: exempt.

## 1. Counts, method, limits

| Repo | Issues open | Issues closed | PRs open | PRs merged | PRs closed unmerged | Comments (issues + PRs) |
|---|---|---|---|---|---|---|
| Open_Duck_Mini (Mini) | 25 | 18 | 6 | 6 | 3 | 103 |
| Open_Duck_Mini_Runtime (Runtime) | 11 | 9 | 9 | 8 | 8 | 70 |
| Open_Duck_Playground (Playground) | 8 | 4 | 7 | 3 | 4 | 35 |
| Open_Duck_reference_motion_generator (RefGen) | 4 | 2 | 1 | 1 | 0 | 8 |
| Total | 48 | 33 | 23 | 18 | 15 | 216 |

Total: 81 issues and 56 PRs = 137 items, all read. Relevance to our build: high 14, medium 21, low 75, none 27.

How they were read:
- Bodies: GitHub search API through gh (search/issues, is:issue and is:pr per repo, all pages). Totals matched the API total_count for every repo and state. All 137 bodies were read in full.
- Fixes and code: local git (Runtime at 376de65 plus its 19 remote branches, Playground at b9be205 plus its 53 remote branches, hardware repo v2 history to b23317a, shallow from 2025-03-04) and gh search/commits (no Open_Duck_Mini commit after b23317a is indexed).
- Comments: the comments API is blocked in this session. WebSearch found indexed thread text only for Mini #48 (partial). Every other thread is marked "not read" with its comment count. Nothing below claims what an unread comment said; where a lab doc cites a comment, that is said.
- Checks run here: the shipped reference gaits were loaded with a restricted unpickler (numpy scalars only) to test Playground #26; the observation layout, joint velocity scale and default pose were compared between Playground and Runtime at the pins.
- Outside sources (marked "outside evidence" where used, listed in section 5): one third-party Open Duck Mini v2 build log, the pypot and rustypot STS3215 register tables, and the upstream BOM Google Sheet (CSV export).

What could not be read:
- 216 comments in 85 threads (only part of the Mini #48 thread, through the search index).
- Images and videos inside bodies, for example Mini #9 (BOM screenshot), #17 (photos), #52 and #56 (videos), Runtime #26 and #32 (screenshots), Playground #13 and #18 (error pictures).
- PR diffs through the API. Merged PRs and branches present in the local clones were read from git; the content of Playground PR #22 is unknown.
- Release pages (the image file itself) and Discord.
- A MuJoCo A/B run for Playground PR #24 (gap G7) was not done: running the upstream Playground code was blocked by this session's permission check.
- RefGen was not cloned; its issues are install and usage questions answered from their bodies.

## 2. Gaps we must fix or check (ranked by impact on our build)

Each entry: issues (main one first), problem, evidence (one short quote from the main body), fix upstream, our status (handled with the lab file, NEW action, or bench test), and whether it affects the 3D print phase. "Outside evidence" is not from an upstream issue and is marked as such (section 5).

### G1. Leg servos too slow: hip pitch, knee and ankle under-track, feet barely lift
- Issues: [Mini #48](https://github.com/apirrone/Open_Duck_Mini/issues/48) (main, open). Same symptom: [Mini #52](https://github.com/apirrone/Open_Duck_Mini/issues/52), [Mini #56](https://github.com/apirrone/Open_Duck_Mini/issues/56), [Mini #30](https://github.com/apirrone/Open_Duck_Mini/issues/30), [Playground #5](https://github.com/apirrone/Open_Duck_Playground/issues/5).
- Problem: on real robots the leg joints do not reach the speeds the walk asks for, so steps are short and feet drag.
- Evidence (#48): "the motor speed is too slow to maintain a proper gait". The indexed thread text (partial) also shows hip roll tracking about 1.0 and hip pitch, knee and ankle only 31 to 49%, also with the robot hanging, as SERVO_DEEP_DIVE section 5 says. No maintainer reply seen.
- Fix upstream: none for #48. The stock configure scripts (Runtime scripts/configure_motor.py and configure_all_motors.py) already write register 85 (max acceleration) = 0 and register 41 (acceleration) = 0 through pypot (checked: pypot maps "maximum acceleration" to address 85), but docs/configure_motors.md only says to run the script; no upstream doc says this step is what makes the servos fast.
- Outside evidence (third-party build log): with the factory value 50 in register 85 the servos lagged 200 ms (sim 60 ms) and the duck fell backward; writing 0 to all 14 cut the lag to 80 ms and the tracking error to one fifth. After that, leg P 30 gave a 5 Hz buzz on the ground and P 20 fixed it.
- Our status: partly handled (SERVO_DEEP_DIVE sections 5 and 6; D1: buy 1 C001 and bench test first; our question is posted on #48). NEW actions for the TO1 bench test:
  1. Configure every servo with configure_motor.py before building, as docs/configure_motors.md says, also when the ID was set with the Feetech tool.
  2. Read and log before and after: firmware (0, 1), max and min voltage (14, 15), P, D, I (21 to 23), mode (33), acceleration (41), goal time (44), goal speed (46), torque limit (48), max speed (84), max acceleration (85), acceleration multiplier (86). Expect 41, 44, 46 and 85 at 0. Keep the factory dump.
  3. Hanging-leg step test: compare the lag with the sim (the third-party log had 60 ms in sim, 80 ms on its fixed robot, 200 ms before the fix) and the no-load speed with about 5 rad/s.
  4. If the legs buzz on the ground, compare the walk script's -p 30 (default) with -p 20.
  5. Our BEC holds the bus at 7.2 V, while stock builds run 7.4 to 8.4 V for most of a charge. Back-EMF speed scales with voltage, so our joints can be up to about 14% slower than on a full stock pack. If the bench test shows the legs are speed limited, test at 7.4 V too (the rating cap) and tell Ahmed.
- 3D print phase: no.

### G2. IMU read glitches and axis setup
- Issues: [Runtime PR #35](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/35) (spike filter, open), [Runtime PR #36](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/36) (calibration test, open), [Runtime #3](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/3) (upside_down, closed).
- Problem: raw IMU reads can jump, and the policy takes a jump for a tilt.
- Evidence (PR #35): "Raw IMU Data (noisy, with occasional spikes)". raw_imu.py at the pin also carries a "TODO filter spikes" note.
- Fix upstream: none merged.
- Outside evidence (third-party build log): repeated backward falls while standing were traced to the Pi hardware I2C with the BNO055 (clock stretching); about 25% of reads had the top bit of the first byte flipped. Software I2C on the same pins (dtoverlay=i2c-gpio) gave 0%.
- Our status: lab B20 (axis signs) is a bench test; read glitches are not in the lab docs. NEW actions: before the first stand, log 1000 IMU reads with the robot still and count jumps; if there are any, switch to software I2C; run a check like PR #36 (gyro bias, gravity size, axis response); keep upside_down False (calibrate_imu.py and the walk script both use False at the pin).
- 3D print phase: no.

### G3. Servo firmware may not match what the policy was trained on
- Issues: [Runtime #26](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/26) (open). Related: [Mini #21](https://github.com/apirrone/Open_Duck_Mini/issues/21), [Runtime #7](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/7).
- Problem: set_kps fails with a parsing error at start; servos with different firmware behave differently.
- Evidence (#26): "It seems to come from the call to `set_kps()`."
- Fix upstream: none merged. Unmerged upstream branches show the author re-tuning for a newer Feetech firmware after BEST_WALK_ONNX_2 came out (2025-04-02): Runtime branch new_firmware (2025-06-24, its configure script starts with a warning not to use it), Playground branch new_feetech_firmware (e56e5ad, 2025-06-16, "firmware kp = 8, no speed limit") and branch improve_walk (a1a0b75, 2025-08-01, "new firmware bam values, kp 16"). pypot updated its STS3215 memory table the same month (f6d305e, 2025-06-16).
- Our status: SERVO_DEEP_DIVE says the author's firmware version is unknown and cites a #26 comment about mixed firmware (not re-read here). NEW actions: on arrival, read firmware major and minor on every servo, spares too; all 14 must match. If they do not, update with the Feetech tool (needs a Windows PC, the same blocker as the Castle Link). Record the version. If the hanging step test (G1) does not match the sim, suspect firmware before the policy.
- 3D print phase: no.

### G4. Power path: BMS trips, holder and wire
- Issues: [Mini #33](https://github.com/apirrone/Open_Duck_Mini/issues/33) (maintainer TODO list, open), [Mini #51](https://github.com/apirrone/Open_Duck_Mini/issues/51) (closed 2026-07-19 with no reply).
- Problem: the stock BMS gave builders trouble; the spring holder, thin wire and 8.4 V on 7.4 V servos were asked about and never answered.
- Evidence (#33): "Source new BMS (too many issues with the current one, and it's hard to get in certain parts of the world)".
- Fix upstream: none.
- Outside evidence (third-party build log): community advice to use a 20 A BMS because 10 A boards cut out at high current, and at least 18 AWG from battery to servo board. The same log found new servos set to an 8.0 V max input (register 14 = 80), so they stop on a full 8.4 V pack.
- Our status: mostly handled: CC BEC Pro at 7.2 V, 15 A fuse, 16 AWG, Pololu 2815 switch, Tenergy 32175 board (10 A working, trip 22 +/- 5 A, no cell balancing) (POWER.md, D3, D8, D10). The sizing comes from sim/CURRENT_BUDGET.md, which has the G7 input error; the lab already keeps 2x margin for real servos. NEW bench tests: (1) the Tenergy board with 15 to 20 A pulses: does it trip, after how long, how does it reset, with the Pi running (a trip also cuts the 5 V regulator, so the Pi resets); (2) log bus voltage and Present Current on the first walks; (3) the holder drop test at 10 A stays (POWER.md section 5); (4) check both cell voltages after the first charges (no balancing). For the dock step: with the BEC holding 7.2 V, Runtime check_voltage.py (servo Present Voltage) cannot show pack charge, so the 20% return rule needs its own pack voltage sense.
- 3D print phase: no (the Tenergy board fits the measured seat, HARDWARE_AUDIT B12).

### G5. A neck part breaks often
- Issue: [Mini #33](https://github.com/apirrone/Open_Duck_Mini/issues/33) (TODO item about a neck part that breaks often).
- Problem: the maintainer's TODO list says a neck part breaks often but does not name it (9 comments not read).
- Evidence: the TODO item itself (the #33 quote is used in G4).
- Fix upstream: none; no robot STL changed after 730c14b.
- Our status: not in the lab docs. In print/parts.csv the neck parts (neck_left_sheet, neck_right_sheet, head_pitch_to_yaw) have no strength override. NEW actions: print the neck and head chain parts with more walls and infill than the 15% base (test one setting first), print one spare set, and find out which part breaks (Discord; posting needs Ahmed's OK).
- 3D print phase: yes.

### G6. Offset calibration moves every joint at once and can break parts
- Issue: [Runtime #32](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/32) (open).
- Problem: find_soft_offsets.py drives all 14 joints to zero together; on one build the head swung and a part broke.
- Evidence (#32): "twisted and broken the component".
- Fix upstream: none; the script still warns that it moves the robot to zero quickly.
- Our status: not in the lab docs. NEW actions: fit each horn with the servo at the zero the configure step moves it to (configure_motor.py ends at goal position 0, and docs/configure_motors.md says to fit the horn then); check each joint alone first with check_motors.py (Runtime PR #18); run find_soft_offsets with the robot hanging on a stand (Mini PR #44 has stand files), the head clear and a hand on the switch.
- 3D print phase: yes (spare head and neck parts, see G5).

### G7. The lab sim ran with an accelerometer bias that training and the robot do not have
- Issue: [Playground PR #24](https://github.com/apirrone/Open_Duck_Playground/pull/24) (open).
- Problem: Playground mujoco_infer.py adds +1.3 to accel x; training and the Runtime do not.
- Evidence (PR #24): "The +1.3 offset was never applied during training."
- Checked at the pins: joystick.py line 502 `accelerometer.at[0].set(accelerometer[0] + 1.3)` throws its result away (JAX arrays do not change in place), so training saw no bias; mujoco_infer.py line 74 adds +1.3; the Runtime adds nothing (raw_imu.py x_offset stays 0 because tare_x() is commented out). The third-party build log reached the same result.
- Fix upstream: not merged.
- Our status: NEW. sim/run_stock_walk.py and sim/current_budget.py call upstream MjInfer.get_obs, so sim/SIM_WALK.md (0.097 m/s for a 0.15 m/s command) and sim/CURRENT_BUDGET.md (used for D8 and D10) ran with the bias. Action: re-run both with 1.3 subtracted from obs[3] and compare speed, falls and current (sim pass only). Not done here (see section 1).
- 3D print phase: no.

### G8. 1 W LEDs straight on GPIO pins
- Issues: [Mini #34](https://github.com/apirrone/Open_Duck_Mini/issues/34) (open), [Mini #33](https://github.com/apirrone/Open_Duck_Mini/issues/33) (TODO item on LED current), [Mini PR #24](https://github.com/apirrone/Open_Duck_Mini/pull/24) (pin table: anodes on GPIO, common cathode to GND).
- Problem: the eye and projector LEDs are 1 W parts hung on GPIO pins with no driver.
- Evidence (#34): "the 1 watt LED's pull too much current for the i/o pin on a rpiz2w."
- Fix upstream: none (TODO open).
- Our status: partly. BOM E3 and E3b: 1 W beads with a 100 ohm resistor on each eye; the projector LED (GPIO25) has no resistor or driver. NEW actions: drive all three LEDs from 5 V through a logic-level N-MOSFET each with a sized resistor (the #34 suggestion), or measure each GPIO current with its resistor and keep it inside the Pi pin limit. Fix the pin text in HARDWARE_AUDIT B23 (section 4).
- 3D print phase: no.

### G9. No game controller in the BOM, and no handling when it drops
- Issues: [Runtime PR #34](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/34) (open), [Runtime PR #29](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/29) (open), [Runtime PR #42](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/42) (open), [Mini #6](https://github.com/apirrone/Open_Duck_Mini/issues/6), [Mini #38](https://github.com/apirrone/Open_Duck_Mini/issues/38).
- Problem: the walk script needs a gamepad, and nothing stops the robot if the pad drops.
- Evidence (PR #34): "It can take a while for the system to detect connection loss."
- Fix upstream: none merged; Runtime TODO.md still says "Better handle xbox controller".
- Our status: NEW. xbox_controller.py opens pygame joystick 0, but BOM.md has no controller line (the upstream BOM sheet has none either). Actions: add a Bluetooth Xbox Wireless Controller from a US seller, or plan keyboard or network control; with the robot hanging, test what it does when the pad drops.
- 3D print phase: no.

### G10. Bus checksum errors crash the walk
- Issues: [Mini #49](https://github.com/apirrone/Open_Duck_Mini/issues/49) (open). Related: [Runtime #2](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/2).
- Problem: checksum errors, then rustypot panics on a non-empty input buffer and the walk script exits.
- Evidence (#49): "I tried replacing the corresponding servo with an error, but it still reported an error."
- Detail from the log in the body: every bad packet comes from ID 32 (head yaw, on the neck chain).
- Fix upstream: none.
- Outside evidence (third-party build log): one loose horn (ID 10) caused checksum errors; a servo board's bus died, probably from plugging cables with power on.
- Our status: NEW. Our neck chain hangs off the left ankle through one made lead (S14, 490 mm, CABLE_MAP.md). Actions: pull-test and strain-relieve the S14 crimps; fit all 4 horn screws on every horn; switch off before plugging any bus cable; on the bench, count checksum errors per ID per minute; later, make the walk loop skip a bad frame instead of exiting.
- 3D print phase: no.

### G11. Pi image and install traps
- Issues: [Runtime #38](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/38), [Runtime PR #43](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/43), [Runtime #30](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/30), [Runtime #41](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/41), [Runtime #44](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/44), [Mini #35](https://github.com/apirrone/Open_Duck_Mini/issues/35), [Mini #37](https://github.com/apirrone/Open_Duck_Mini/issues/37), [Mini #38](https://github.com/apirrone/Open_Duck_Mini/issues/38), [Mini #39](https://github.com/apirrone/Open_Duck_Mini/issues/39), [Mini #57](https://github.com/apirrone/Open_Duck_Mini/issues/57).
- Problem: installs fail on new OS versions or small cards; the image is hard to find and ships public default logins.
- Evidence (Runtime PR #43, Japanese, translated, not a quote): Debian 13's default Python 3.13 has no onnxruntime 1.18.1 wheel, so the install fails.
- Fix upstream: image 0.2.3 with install docs (Runtime PR #31, merged 2026-09-07; docs/INSTALL.md says it is Raspberry Pi OS Lite 64-bit Bookworm). PR #43 was not merged.
- Our status: REFERENCES.md names the image. NEW actions: flash image 0.2.3 or Raspberry Pi OS Bookworm, not a Debian 13 build (setup.cfg pins onnxruntime 1.18.1); change the default password and hotspot key at first boot (INSTALL.md says so); if the Xbox pad keeps dropping, add Privacy = device to /etc/bluetooth/main.conf (Mini #38); the 32 GB card in the BOM covers the space problem in Runtime #30.
- 3D print phase: no.

### G12. roll_motor_bottom screw head may rub roll_to_pitch
- Issue: [Mini #17](https://github.com/apirrone/Open_Duck_Mini/issues/17) (closed, 6 comments not read).
- Problem: the mount screw head on roll_motor_bottom sticks out and blocks roll_to_pitch.
- Evidence (#17): "the screw head will protrude and push against the "roll to pitch",and hindering its movement."
- Fix upstream: no STL change after the report: roll_motor_bottom.stl is unchanged since 2025-03-04 and roll_to_pitch last changed in 41eb809 (2025-03-18), before the report (2025-04-05).
- Our status: NEW. audit/screws2.json lists this screw (servo bag M2 self-tapper, head on a flat face of roll_motor_bottom), but the audit did not sweep the hip roll range for head clearance. Both parts are in the first leg print (print/parts.csv, leg1). Actions: check the head against roll_to_pitch over hip roll -0.44 to +0.44 rad in the GLB, or on the first leg; if it rubs, use a low-head screw or cut a relief slot in roll_to_pitch before the second leg.
- 3D print phase: yes.

### G13. Head stack must be partly taken apart to fit the top body piece
- Issue: [Mini #36](https://github.com/apirrone/Open_Duck_Mini/issues/36) (open).
- Problem: assembly order: the top body piece does not pass over the assembled head motor stack.
- Evidence (#36): "i need to dismantle part of the head motor structure to put on the top body piece".
- Fix upstream: none.
- Our status: NEW. Action: put this order in the assembly map (next lab step) and test fit the top body piece over the neck stack before the final screws.
- 3D print phase: no.

### G14. Stock walk policy limits for the later dock and get-up step
- Issues: [Mini #43](https://github.com/apirrone/Open_Duck_Mini/issues/43) (open), [Playground #26](https://github.com/apirrone/Open_Duck_Playground/issues/26) (open), [Playground #4](https://github.com/apirrone/Open_Duck_Playground/issues/4) (closed).
- Problem: little training data is published for the shipped policy, its behavior has limits, and generated reference gaits can be bad.
- Evidence (#43, in the reporter's own sim): "Duck falls down immediately after receiving a command to move forward."
- Fix upstream: none. No upstream issue covers charging, docking or getting up. Closest: a fall detector on the community Runtime branch feature/neopixels (8eab55b, 2026-05-10) and a stand-up experiment for another robot (Sigmaban) on Playground branch new_sigmaban_standup.
- Checked here: the observation layout matches between Playground and Runtime at the pins (101 values, same order, joint velocity scale 0.05, same default pose). Playground #26: 2 of the 240 shipped gaits have a bad knee (0.222_0.111_0.963, right knee negative all cycle; 0.222_-0.111_-1.111, left knee crosses 0). Both have dx 0.222, which the stock command range (max 0.15, nearest grid point 0.148) never picks, so our use of BEST_WALK_ONNX_2 is not affected. The Runtime always advances the gait phase, also at zero command (unmerged branch phase_freeze_no_command stops it).
- Outside evidence (third-party build log): the stock policy falls when walking backward, does not step at 0.05 m/s, does not step at 0.1 m/s sideways alone, and steps in place at zero command.
- Our status: GAPS B5, B6, A13. NEW (later step): a dock needs a slow approach, backing up and standing still on pogo pins, which the stock policy does not do; plan our own training; check knee signs in any new reference gaits; add IMU delay randomization (third-party build log).
- 3D print phase: no (dock contacts come in the later step).

### G15. Antennas twitch and swing only about 30 degrees
- Issues: [Runtime #13](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/13) (open), [Mini #41](https://github.com/apirrone/Open_Duck_Mini/issues/41) (open), [Runtime PR #27](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/27) (closed, not merged).
- Problem: SG90 antennas jitter, and the stock pulse mapping uses a small part of their range.
- Evidence (#41): "the antennas have a movement range of about 30 degrees."
- Fix upstream: none merged (tries on Runtime branch debug_antennas_twitch, 2025-05-05).
- Our status: SG90s kept for the stock build (GAPS B10a). Low priority: antennas are optional in duck_config; leave them off if they twitch.
- 3D print phase: no.

### G16. Pin table and code disagree on eyes and antennas
- Issue: [Mini PR #24](https://github.com/apirrone/Open_Duck_Mini/pull/24) (merged 2025-11-23).
- Problem: the assembly_guide pin table swaps left and right eyes and antennas compared with the Runtime code.
- Evidence (PR #24): "Added pin map table as per schematic diagram"
- Fix upstream: none in the v2 code. A community Runtime branch (feature/neopixels, 7bfe094, 2026-05-10) flips the antenna pins to match the table; its eye pins stay as in v2.
- Our status: handled (D9: wire to the Runtime code at 376de65; WIRING.md). If we ever move to that branch, swap the antenna leads or the pin numbers.
- 3D print phase: no.

### G17. Runtime and training code have no license
- Issue: [Runtime #45](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/45) (open, 0 comments).
- Problem: without a license file, reuse or redistribution of the Runtime, Playground and RefGen code is not granted.
- Evidence (#45): "these three repos have no LICENSE file".
- Fix upstream: none. Status 2026-11-01: Open_Duck_Mini is Apache-2.0; Runtime, Playground and RefGen have no LICENSE file; #45 (another builder, 2026-10-25) asks for Apache-2.0 and about the Onshape CAD; no reply yet.
- Our status: D6 decided (no message; use the code unmodified, do not republish). Action: watch #45; nothing to post.
- 3D print phase: no.

### Print phase summary
Only three gaps touch the print phase: G5 (stronger settings and a spare set for the neck chain), G6 (spare head and neck parts) and G12 (screw head clearance, check on the first leg). The bulb count (Mini #26) is already right in print/parts.csv.

### Already handled (no new action)
- Mini #51 over-voltage: BEC at 7.2 V (D3); fuse and holder test in POWER.md.
- Mini #26 bulbs: 2 in PRINT_CHECK.md and print/parts.csv.
- Mini #7 roll_to_pitch holes: fixed upstream in 41eb809, inside the 730c14b STL set we measured.
- Mini #22 missing STLs: added in 730c14b.
- Mini #3 trunk screws: the guide says M3x10 at b23317a; the lab audit agrees.
- Mini #14 foot switches: foot_top slots match the SS-10 body (HARDWARE_AUDIT B11).
- Mini #1 UBEC seat: our 5 V regulator sits on the head floor (D4, D11).
- Mini #20 and Runtime #7: MuJoCo kp mapping and 5.24 rad/s (SERVO_DEEP_DIVE E3, E5).
- Mini #9 BOM duplicate: one servo board (HARDWARE_AUDIT B7).
- Mini #5 and #21: buy the 7.4 V C001, not HS or 12 V units (D1).
- Mini #50 URDF: mini_bdx/robots/open_duck_mini_v2 (GAPS B8).
- Playground #8 ONNX export error: fixed by Playground PR #10 and b9be205 (only matters for our own training).
- Playground #4 obs mismatch: layouts match at the pins (checked, G14).

### Process note
The lab commit c4d9455 mentions #48 in its message, and GitHub shows it as a backlink on the upstream issue (seen in the search index text). In this public fork, leave upstream issue numbers out of commit messages unless a visible link is wanted.

## 3. Full table: every issue and PR

Relevance: high = can stop the walk, break parts or change a purchase or print; medium = setup, safety or a later lab step; low = minor or already handled; none = not about our build. Comments: "not read (N)" means N comments exist and were not readable here. G numbers point to section 2.

| Repo | # | Type | State | Title | Category | Relevance | Comments | Note |
|---|---|---|---|---|---|---|---|---|
| Mini | [1](https://github.com/apirrone/Open_Duck_Mini/issues/1) | issue | closed | Clarification on UBEC Assembly in Body Module | electrical/power | low | not read (2) | UBEC not modelled in the Onshape body. Ours: 5 V regulator on the head floor (D4, D11). Handled. |
| Mini | [2](https://github.com/apirrone/Open_Duck_Mini/issues/2) | issue | closed | Isaac sim environment | sim/training/policy | none | not read (2) | Third-party Isaac Sim training env for v1. |
| Mini | [3](https://github.com/apirrone/Open_Duck_Mini/issues/3) | issue | closed | The bolt size is incorrect in the Assembly Instructions. | print/mechanical | low | not read (5) | trunk_bottom to trunk_top needs M3x10, not M3x6. Guide says M3x10 at b23317a; lab audit agrees. Handled. |
| Mini | [4](https://github.com/apirrone/Open_Duck_Mini/issues/4) | issue | closed | Beee pooo beee - Great project! | community/other | none | not read (3) | Asks for a Discord or YouTube channel. |
| Mini | [5](https://github.com/apirrone/Open_Duck_Mini/issues/5) | issue | closed | servo compatibility | servo/firmware | medium | not read (2) | Asks if Waveshare ST3215 servos work. Lab cites a comment here advising ST3215-HS (not re-read). Keep C001 for the stock policy (D1). |
| Mini | [6](https://github.com/apirrone/Open_Duck_Mini/issues/6) | issue | closed | PS5 Controller | runtime software | medium | not read (2) | PS5 pad question. The walk script needs a pygame gamepad and our BOM has none (G9). |
| Mini | [7](https://github.com/apirrone/Open_Duck_Mini/issues/7) | issue | closed | The holes (two) on RIGHT_ROLL_TO_PITCH/LEFT_ROLL_TO_PITCH are not concentric with the holes on the servos | print/mechanical | low | not read (1) | Two roll_to_pitch holes 1.18 mm off the servo holes. Fixed by STL update 41eb809 (2025-03-18), inside the 730c14b set. Handled. |
| Mini | [8](https://github.com/apirrone/Open_Duck_Mini/issues/8) | issue | closed | NVIDIA Isaac GR00T N1 | community/other | none | not read (1) | Asks about NVIDIA GR00T N1. |
| Mini | [9](https://github.com/apirrone/Open_Duck_Mini/issues/9) | issue | closed | About the BOM | docs/BOM | low | not read (2) | Two BOM lines were the same board (screenshot not readable). Upstream sheet now lists one servo board; lab B7 agrees. |
| Mini | [10](https://github.com/apirrone/Open_Duck_Mini/pull/10) | PR | closed | Add Chinese Taobao BOM and still updating in Readme.md | docs/BOM | none | not read (2) | Chinese Taobao BOM; closed without merge. |
| Mini | [11](https://github.com/apirrone/Open_Duck_Mini/issues/11) | issue | open | Aliexpress BOM | docs/BOM | none | none | Community AliExpress BOM sheet. We use a US BOM. |
| Mini | [12](https://github.com/apirrone/Open_Duck_Mini/issues/12) | issue | closed | lib mujoco_viewer can not get | sim/training/policy | low | not read (2) | mujoco_viewer package missing (old sim tools). |
| Mini | [13](https://github.com/apirrone/Open_Duck_Mini/issues/13) | issue | closed | can i train my own robot .,my robot is soloidworks,and urd format | sim/training/policy | none | not read (2) | Asks how to train an own SolidWorks robot (no body). |
| Mini | [14](https://github.com/apirrone/Open_Duck_Mini/issues/14) | issue | closed | Confused about the ss10 switch | print/mechanical | low | not read (2) | How to fit the SS-10 foot switches. foot_top slots match the SS-10 body, press fit (B11). Handled. |
| Mini | [15](https://github.com/apirrone/Open_Duck_Mini/pull/15) | PR | closed | Add Bambu Labs 3MF file | print/mechanical | low | not read (4) | Bambu X1C 3MF; closed without merge (a Bambu project came later in PR #25 mods). |
| Mini | [16](https://github.com/apirrone/Open_Duck_Mini/pull/16) | PR | merged | Update README.md | docs/BOM | none | not read (5) | Chinese BOM and docs links in the README. |
| Mini | [17](https://github.com/apirrone/Open_Duck_Mini/issues/17) | issue | closed | 3d print part issue | print/mechanical | high | not read (6) | Mount screw head on roll_motor_bottom rubs roll_to_pitch. No STL change since; check on the first leg (G12). |
| Mini | [18](https://github.com/apirrone/Open_Duck_Mini/issues/18) | issue | open | Make a full build video | docs/BOM | low | not read (4) | Maintainer TODO: full build video. |
| Mini | [19](https://github.com/apirrone/Open_Duck_Mini/issues/19) | issue | open | Improve documentation | docs/BOM | low | not read (6) | Maintainer TODO: fix doc TODOs and old pictures, add a FAQ. Matches GAPS A7. |
| Mini | [20](https://github.com/apirrone/Open_Duck_Mini/issues/20) | issue | closed | motor kp and kd | servo/firmware | low | not read (2) | MuJoCo kp 17.8 equals firmware P 32 (lab E3 cites a comment, not re-read). Handled. |
| Mini | [21](https://github.com/apirrone/Open_Duck_Mini/issues/21) | issue | open | Other motor adaptation issues | servo/firmware | medium | not read (2) | 12 V 30 kg servos with the 7.4 V policy: feet tremble. We buy 7.4 V C001; leg P may need tuning (G1, G3). |
| Mini | [22](https://github.com/apirrone/Open_Duck_Mini/issues/22) | issue | closed | Add missing stl files | print/mechanical | low | not read (1) | Missing STLs added in 730c14b (2025-04-19), the set the lab measured. Handled. |
| Mini | [23](https://github.com/apirrone/Open_Duck_Mini/pull/23) | PR | merged | Park Head Mod | print/mechanical | low | not read (3) | Park style head mod under print/mods; not stock. |
| Mini | [24](https://github.com/apirrone/Open_Duck_Mini/pull/24) | PR | merged | Update assembly_guide.md with pin mapping | docs/BOM | medium | not read (1) | Pin map table in assembly_guide.md. Eyes and antennas swapped vs Runtime code; we wire to the code (G16, D9). |
| Mini | [25](https://github.com/apirrone/Open_Duck_Mini/pull/25) | PR | merged | Body and Cover Mods for V2 | print/mechanical | low | not read (2) | Jaime's mods: leg covers with cable guides, trunk with pass-through holes, Bambu project; not stock. |
| Mini | [26](https://github.com/apirrone/Open_Duck_Mini/issues/26) | issue | open | Bulb quantity x2 in print_guide.md | print/mechanical | low | none | print_guide says bulb x1, CAD needs 2. Still x1 upstream; PRINT_CHECK and print/parts.csv have 2. Handled. |
| Mini | [27](https://github.com/apirrone/Open_Duck_Mini/issues/27) | issue | closed | Mirror the leg servo | servo/firmware | low | not read (1) | Asks if the right knee and ankle must be mirrored in software (comment not read). Check each joint direction against the sim. |
| Mini | [28](https://github.com/apirrone/Open_Duck_Mini/pull/28) | PR | open | Create Servo_Info_update.png | servo/firmware | medium | not read (2) | Adds a servo info picture from Discord (image not readable here); continued in PR #45. |
| Mini | [29](https://github.com/apirrone/Open_Duck_Mini/issues/29) | issue | open | Phone requirement on Discord | community/other | low | not read (2) | Discord asks for phone verification (GAPS A11). |
| Mini | [30](https://github.com/apirrone/Open_Duck_Mini/issues/30) | issue | open | The duck cannot be lifted up and retreated by the handle | servo/firmware | high | not read (1) | Gait looks wrong when driven with an Xbox pad; asks about mirrored servos. Same family as #48 (G1). |
| Mini | [31](https://github.com/apirrone/Open_Duck_Mini/pull/31) | PR | open | Update README.md | docs/BOM | none | not read (2) | Chinese tutorial and voice control links. |
| Mini | [32](https://github.com/apirrone/Open_Duck_Mini/issues/32) | issue | open | Add voice control | community/other | none | none | Voice control with Xiaozhi (gitee and bilibili links). |
| Mini | [33](https://github.com/apirrone/Open_Duck_Mini/issues/33) | issue | open | TODO | electrical/power | high | not read (9) | Maintainer TODO for v2.5: new BMS, neck part that breaks often, LED current, screw docs, UART instead of USB, 12 V motors (G4, G5, G8). |
| Mini | [34](https://github.com/apirrone/Open_Duck_Mini/issues/34) | issue | open | 1w led lights | electrical/power | high | not read (2) | 1 W LEDs draw too much from GPIO and the 3.3 V rail; suggests N-MOSFET drivers from 5 V (G8). |
| Mini | [35](https://github.com/apirrone/Open_Duck_Mini/issues/35) | issue | open | complete raspberry pi zero 2 w image for burning the latest micro SD with all updates to date | runtime software | low | not read (1) | Asks for a ready Pi image. Image 0.2.3 exists now (Runtime PR #31). |
| Mini | [36](https://github.com/apirrone/Open_Duck_Mini/issues/36) | issue | open | cosmedic shells | print/mechanical | medium | none | Wants cosmetic-only shells; head motor stack must be partly removed to fit the top body piece (G13). |
| Mini | [37](https://github.com/apirrone/Open_Duck_Mini/issues/37) | issue | open | From OPENDUCK2_BUILD_V0.2.3 Max to SSH | runtime software | medium | not read (1) | Steps from image 0.2.3 to SSH. The image ships public default logins; change them (G11). |
| Mini | [38](https://github.com/apirrone/Open_Duck_Mini/issues/38) | issue | open | From .2.3 ssh to xbox bluetooth | runtime software | medium | none | Xbox pad kept dropping on image 0.2.3; fix: Privacy = device in Bluetooth main.conf (G9, G11). |
| Mini | [39](https://github.com/apirrone/Open_Duck_Mini/issues/39) | issue | closed | no module named 'mini_bdx_runtime' | runtime software | low | not read (3) | mini_bdx_runtime not found after image setup; closed (comments not read). |
| Mini | [40](https://github.com/apirrone/Open_Duck_Mini/pull/40) | PR | merged | Add Readme.md to Jaime's V2 Mods Folder | docs/BOM | none | none | README for Jaime's mods folder. |
| Mini | [41](https://github.com/apirrone/Open_Duck_Mini/issues/41) | issue | open | antenna servo range | runtime software | low | none | Stock pulse map moves the SG90 antennas only about 30 deg; gives a wider map (G15). |
| Mini | [42](https://github.com/apirrone/Open_Duck_Mini/issues/42) | issue | open | planning to implement a jetson orin nano | community/other | low | not read (1) | Asks about a Jetson Orin Nano mod and Isaac Sim docs. Vision for docking may need more than a Pi Zero 2 W (GAPS B4). |
| Mini | [43](https://github.com/apirrone/Open_Duck_Mini/issues/43) | issue | open | Training data for BEST_WALK_ONNX_2.onnx | sim/training/policy | medium | none | Wants training data for BEST_WALK_ONNX_2; asks how to start the 3 past actions (Runtime starts them at zero) (G14, GAPS A13). |
| Mini | [44](https://github.com/apirrone/Open_Duck_Mini/pull/44) | PR | merged | Add stand print files for my skins | print/mechanical | low | none | Stand print files for Jaime's skins. A stand helps hanging bench tests (G6). |
| Mini | [45](https://github.com/apirrone/Open_Duck_Mini/pull/45) | PR | open | Add servo info picture to configure_motors.md | servo/firmware | medium | not read (1) | Adds the servo info picture to configure_motors.md; the author says it helped the build. |
| Mini | [46](https://github.com/apirrone/Open_Duck_Mini/pull/46) | PR | closed | [feature] add set up guide | docs/BOM | none | none | Empty setup guide PR, closed in a minute. |
| Mini | [48](https://github.com/apirrone/Open_Duck_Mini/issues/48) | issue | open | Clarification on STS3215 Motor Specs in BOM | servo/firmware | high | partly, search index (5) | C001 too slow for the gait; asks which variant. Our question posted 2026-11-01; no maintainer reply seen (G1). |
| Mini | [49](https://github.com/apirrone/Open_Duck_Mini/issues/49) | issue | open | read crc: 251, computed crc: 219 data: [255, 255, 32, 4, 0, 0, 0, 251] | servo/firmware | high | not read (1) | Checksum errors from ID 32, then a rustypot panic stops the walk (G10). |
| Mini | [50](https://github.com/apirrone/Open_Duck_Mini/issues/50) | issue | open | 请问在哪里获取urdf文件？ | docs/BOM | low | not read (1) | (Chinese) Where is the URDF? In mini_bdx/robots/open_duck_mini_v2 (GAPS B8). |
| Mini | [51](https://github.com/apirrone/Open_Duck_Mini/issues/51) | issue | closed | Question about power (battery holder and servo voltage) | electrical/power | high | none | Spring holder and 8.4 V on 7.4 V servos. Closed 2026-07-19, no reply. BEC 7.2 V and fuse handle it; holder test open (G4). |
| Mini | [52](https://github.com/apirrone/Open_Duck_Mini/issues/52) | issue | open | Open duck mini stable walk | servo/firmware | high | none | 12 V 30 kg knees stopped the falls, but the right foot still lacks clearance. Same family as #48 (G1). |
| Mini | [53](https://github.com/apirrone/Open_Duck_Mini/pull/53) | PR | open | Animation: duck_anim core runtime library (workstream A) | runtime software | low | none | Animation library with joint safety limits (workstream A); not stock. |
| Mini | [54](https://github.com/apirrone/Open_Duck_Mini/pull/54) | PR | open | Animation: dock demo alive-head mode and documentation (workstream D) | runtime software | low | none | Head animation demo with the legs locked in a parked 'dock' pose; not a charging dock. |
| Mini | [55](https://github.com/apirrone/Open_Duck_Mini/pull/55) | PR | open | Animation: hybrid RL + animation controller and MuJoCo harness (workstream C) | sim/training/policy | low | none | Hybrid RL plus animation controller and MuJoCo harness; feeds raw policy actions back to the policy. |
| Mini | [56](https://github.com/apirrone/Open_Duck_Mini/issues/56) | issue | open | Not moving forward | servo/firmware | high | none | Robot will not walk forward on joystick input (IMU and feet connected). Check servo registers and command size (G1, G14). |
| Mini | [57](https://github.com/apirrone/Open_Duck_Mini/issues/57) | issue | open | zip file | runtime software | low | not read (6) | Where is the image zip (same as Runtime #44). |
| Mini | [58](https://github.com/apirrone/Open_Duck_Mini/issues/58) | issue | open | [ASTRA community outreach] Impressed by your Open Duck Mini work | community/other | none | none | Outreach spam. |
| Mini | [59](https://github.com/apirrone/Open_Duck_Mini/issues/59) | issue | open | [ASTRA community outreach] Impressed by your Open Duck Mini work | community/other | none | none | Outreach spam, duplicate of #58. |
| Runtime | [1](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/1) | PR | merged | Cleaning up | runtime software | none | none | Maintainer clean-up. |
| Runtime | [2](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/2) | issue | closed | `rustypot` Error | runtime software | low | not read (3) | rustypot serial error; the reporter used IDs 0 to 13. IDs must be 10 to 14, 20 to 24, 30 to 33. |
| Runtime | [3](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/3) | issue | closed | Confirmation on the variable | IMU/sensors | medium | not read (3) | Asks if upside_down must be True for IMU calibration. At the pin calibrate and walk both use False; test axis signs (G2, B20). |
| Runtime | [4](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/4) | PR | merged | Fix the configure script. | servo/firmware | low | not read (1) | configure script ignored the port and id arguments; fixed. |
| Runtime | [5](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/5) | PR | merged | Added Config File Support | runtime software | low | not read (1) | Config file and joint offsets support. |
| Runtime | [6](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/6) | PR | open | configure_motor: Add automatic port detection for waveshare boards. | runtime software | low | not read (5) | Auto-detect the Waveshare port by USB id; open. |
| Runtime | [7](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/7) | issue | closed | Discussion on the "max_motor_velocity = 5.24" | servo/firmware | low | not read (3) | Why 5.24 rad/s: from system identification (lab E5 cites the reply, not re-read). Handled. |
| Runtime | [8](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/8) | issue | open | Eyes LEDs run as a system service ? | runtime software | low | none | Maintainer TODO: eyes on as a service to show the robot is powered. |
| Runtime | [9](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/9) | issue | open | Play a sound on startup ? | runtime software | none | none | Maintainer TODO: startup sound. |
| Runtime | [10](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/10) | issue | closed | Config file | runtime software | low | not read (1) | Config file; done in PR #5. |
| Runtime | [11](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/11) | issue | open | Add a checklist script | runtime software | medium | none | Maintainer TODO: pre-walk checklist script (motor and IMU orientation, feet, motor params). Still missing; write our own (G1, G2). |
| Runtime | [12](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/12) | issue | closed | python run error | runtime software | low | not read (8) | adafruit_bno055 import error (DigitalInOut); dependency versions. |
| Runtime | [13](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/13) | issue | open | Fix antennas twitching | runtime software | low | not read (1) | Antennas twitch. Open; fix tries only on branch debug_antennas_twitch (G15). |
| Runtime | [14](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/14) | issue | closed | Integrate Buttons() into XboxController() | runtime software | none | none | Buttons merged into XboxController (PR #15). |
| Runtime | [15](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/15) | PR | merged | 14 integrate buttons into xboxcontroller | runtime software | none | none | Buttons into XboxController. |
| Runtime | [16](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/16) | PR | merged | Update find_soft_offsets.py | runtime software | low | not read (1) | find_soft_offsets y/Y answer bug fixed. |
| Runtime | [17](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/17) | PR | closed | Update project structure and add dual string runtime support (WIP) | runtime software | none | none | Two-Pi (body and head) runtime, WIP; closed without merge. |
| Runtime | [18](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/18) | PR | merged | Add a check_motors.py | servo/firmware | medium | not read (1) | check_motors.py finds missing or misconfigured motors. Use it before calibration (G6). |
| Runtime | [19](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/19) | PR | open | Added find_all_motor_offsets. | servo/firmware | low | not read (1) | Find all offsets from one pose; open. |
| Runtime | [20](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/20) | PR | closed | Support serial_port config settings | runtime software | low | not read (2) | serial_port setting; closed without merge. |
| Runtime | [21](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/21) | issue | closed | Package dir and package name have the same name, resulting in incorrect resource read path | runtime software | low | not read (3) | Package dir and name clash breaks resource paths; closed. |
| Runtime | [22](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/22) | PR | closed | support resource file read | runtime software | low | not read (4) | Resource file read fix; closed without merge. |
| Runtime | [23](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/23) | PR | merged | feat: GPIO compatible | runtime software | low | not read (4) | GPIO compatibility layer; merged 2025-06-24. |
| Runtime | [24](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/24) | issue | closed | GPIO compatible | runtime software | low | not read (1) | GPIO on other boards; done in PR #23. |
| Runtime | [25](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/25) | PR | closed | Functional testing for the droid to make life easier to test stuff | runtime software | low | not read (1) | Unit tests for antennas, eyes, feet and sounds; closed without merge. |
| Runtime | [26](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/26) | issue | open | OSError: Parsing error in set_kps() during runtime | servo/firmware | high | not read (6) | Parsing error in set_kps at start. Lab cites a comment blaming mixed firmware (not re-read) (G3). |
| Runtime | [27](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/27) | PR | closed | Use pigpio for remote projector, eyes and antennas on Pi Zero | runtime software | low | not read (1) | pigpio for eyes, projector and antennas on Pi Zero; closed without merge (G15). |
| Runtime | [28](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/28) | PR | closed | Feature/reorganized repo | runtime software | none | none | Repo reorganization part 1; closed without merge. |
| Runtime | [29](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/29) | PR | open | Add an autodetection routine to xbox_controller.py | runtime software | medium | not read (1) | Gamepad mapping auto-detect; open. Useful with a non-Xbox pad (G9). |
| Runtime | [30](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/30) | issue | closed | ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device | runtime software | low | not read (5) | pip ran out of space on a Pi Zero 2 W; the 32 GB card or the image avoids it (G11). |
| Runtime | [31](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/31) | PR | merged | Added release documentation | runtime software | medium | none | Docs for image 0.2.3 (Bookworm based); merged 2026-09-07 (G11). |
| Runtime | [32](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/32) | issue | open | V2 and when runing the find_soft_offsets file twisting the head components | servo/firmware | high | not read (1) | find_soft_offsets moved head and leg at once and broke a part (G6). |
| Runtime | [33](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/33) | PR | closed | Main | runtime software | none | not read (2) | 'Main' with no body; closed without merge. |
| Runtime | [34](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/34) | PR | open | Resilliant walk script for controller disconnects | runtime software | medium | none | Pause and zero commands on controller loss; open. The stock script has no such handling (G9). |
| Runtime | [35](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/35) | PR | open | Subtle filtering while keeping fast gyro response | IMU/sensors | high | none | Hampel and EMA filters for IMU spikes; open (G2). |
| Runtime | [36](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/36) | PR | open | Test script to validate if IMU is calibrated properly | IMU/sensors | medium | none | IMU calibration test script; open. Useful for lab B20 (G2). |
| Runtime | [37](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/37) | PR | open | Print and optionally write offsets to duck_config | runtime software | low | none | Write offsets into duck_config.json; open. |
| Runtime | [38](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/38) | issue | open | Issue with onnxruntime library 1.18.1 on branch v2 | runtime software | medium | not read (3) | onnxruntime 1.18.1 fails on 64-bit Pi OS; reporter tried 1.20 (G11). |
| Runtime | [39](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/39) | PR | open | Update README.md | docs/BOM | none | none | Chinese doc link in the README; open. |
| Runtime | [40](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/40) | issue | open | error about rpi5 | runtime software | low | none | Pi 5 needs other GPIO code and misses the 50 Hz budget. Not our board. |
| Runtime | [41](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/41) | issue | open | No module named 'mini_bdx_runtime.raw_imu' | runtime software | low | not read (1) | mini_bdx_runtime.raw_imu not found after install. |
| Runtime | [42](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/42) | PR | open | feat: add demo walking script | runtime software | low | not read (2) | Start walking once a controller connects (demo); open (G9). |
| Runtime | [43](https://github.com/apirrone/Open_Duck_Mini_Runtime/pull/43) | PR | closed | chore: Python 3.12 をデフォルトに固定 | runtime software | medium | not read (1) | (Japanese) Pin Python 3.12: Debian 13's Python 3.13 has no onnxruntime 1.18.1 wheel; closed without merge (G11). |
| Runtime | [44](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/44) | issue | open | File location | runtime software | low | not read (3) | Where is the image zip (same as Mini #57). |
| Runtime | [45](https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/45) | issue | open | Add a LICENSE file (Runtime, Playground, reference_motion_generator have none) | docs/BOM | medium | none | Asks for a LICENSE in Runtime, Playground and RefGen. Same topic as lab D6; no reply yet (G17). |
| Playground | [1](https://github.com/apirrone/Open_Duck_Playground/pull/1) | PR | merged | Idx by name | sim/training/policy | none | none | Index joints by name. |
| Playground | [2](https://github.com/apirrone/Open_Duck_Playground/pull/2) | PR | merged | Merge latest main into go_bdx | sim/training/policy | none | none | Branch merge for go_bdx. |
| Playground | [3](https://github.com/apirrone/Open_Duck_Playground/issues/3) | issue | closed | loop argument must agree with lock | sim/training/policy | low | not read (2) | orbax checkpoint asyncio error during training; closed. Pin versions for our later training. |
| Playground | [4](https://github.com/apirrone/Open_Duck_Playground/issues/4) | issue | closed | How can I modify the policy input (observation)? | sim/training/policy | low | not read (2) | Obs mismatch between Playground and Runtime; closed. At the pins both use the same 101-value layout (checked). |
| Playground | [5](https://github.com/apirrone/Open_Duck_Playground/issues/5) | issue | closed | Not work on real robot | sim/training/policy | high | not read (1) | Own trained policy cannot lift its feet on the real robot; closed (comment not read). Same family as Mini #48 (G1). |
| Playground | [6](https://github.com/apirrone/Open_Duck_Playground/pull/6) | PR | closed | Update project files and add new scripts | sim/training/policy | none | none | Project files; closed in seconds. |
| Playground | [7](https://github.com/apirrone/Open_Duck_Playground/pull/7) | PR | closed | docker support | sim/training/policy | low | not read (2) | Docker support; closed, resubmitted as #9. |
| Playground | [8](https://github.com/apirrone/Open_Duck_Playground/issues/8) | issue | open | AttributeError: 'dict' object has no attribute 'policy' | sim/training/policy | low | not read (5) | ONNX export AttributeError; fixed by PR #10 and b9be205, issue left open. |
| Playground | [9](https://github.com/apirrone/Open_Duck_Playground/pull/9) | PR | open | Docker support | sim/training/policy | low | none | Docker support; open. |
| Playground | [10](https://github.com/apirrone/Open_Duck_Playground/pull/10) | PR | merged | versatile policy retreival from brax | sim/training/policy | low | not read (4) | Policy parameter lookup fix for ONNX export (fixes #8). |
| Playground | [11](https://github.com/apirrone/Open_Duck_Playground/pull/11) | PR | open | Added contact-aided invariant ekf to mujoco_infer example | sim/training/policy | low | none | Contact-aided invariant EKF in mujoco_infer; open. Maybe useful for dock state estimation later. |
| Playground | [12](https://github.com/apirrone/Open_Duck_Playground/pull/12) | PR | open | Added EKF to mujoco infer and updated observations | sim/training/policy | low | none | EKF plus new observations; open. |
| Playground | [13](https://github.com/apirrone/Open_Duck_Playground/issues/13) | issue | open | Problems encountered when running runner.py | sim/training/policy | low | not read (1) | runner.py error on CUDA 12.3 (picture not readable). |
| Playground | [14](https://github.com/apirrone/Open_Duck_Playground/issues/14) | issue | open | running training using my own robot and polynomial coefficients | sim/training/policy | low | not read (2) | KeyError with own robot reference data (dy range). |
| Playground | [15](https://github.com/apirrone/Open_Duck_Playground/issues/15) | issue | closed | jaxlib._jax.XlaRuntimeError: INTERNAL: cuSolver internal error | sim/training/policy | low | not read (4) | cuSolver internal error on the GPU; closed. |
| Playground | [16](https://github.com/apirrone/Open_Duck_Playground/issues/16) | issue | open | TensorFlow with CUDA: RTX 5xxx series isn't supported (CUDA_ERROR_INVALID_HANDLE) | sim/training/policy | low | not read (4) | TensorFlow ONNX export fails on RTX 50 series GPUs. Matters only if we train on one. |
| Playground | [17](https://github.com/apirrone/Open_Duck_Playground/pull/17) | PR | open | Add FastAPI and local voice control support | runtime software | low | none | FastAPI and local voice control; open. |
| Playground | [18](https://github.com/apirrone/Open_Duck_Playground/issues/18) | issue | open | I encountered the problem in the picture when running runner.py | sim/training/policy | low | not read (3) | runner.py error (picture not readable). |
| Playground | [19](https://github.com/apirrone/Open_Duck_Playground/issues/19) | issue | open | about training num_envs increase | sim/training/policy | low | none | How to change num_envs; same RTX 5060 Ti export error as #16. |
| Playground | [20](https://github.com/apirrone/Open_Duck_Playground/pull/20) | PR | open | Features - Add MuJoCo validation | sim/training/policy | none | none | MuJoCo XML schema validation for editors; open. |
| Playground | [21](https://github.com/apirrone/Open_Duck_Playground/pull/21) | PR | closed | Reward/acceleration smoothing | sim/training/policy | low | none | Smoother action rewards; closed in seconds. |
| Playground | [22](https://github.com/apirrone/Open_Duck_Playground/pull/22) | PR | closed | Fix/dof vel | sim/training/policy | low | none | 'Fix/dof vel', no body, closed in seconds. At the pins the joint velocity scale is 0.05 in training and Runtime (checked). |
| Playground | [23](https://github.com/apirrone/Open_Duck_Playground/pull/23) | PR | open | Changed the requirements to also work on Mac OS (CPU only) | sim/training/policy | low | none | Mac CPU-only requirements; open. |
| Playground | [24](https://github.com/apirrone/Open_Duck_Playground/pull/24) | PR | open | Removed accelerometer bias | sim/training/policy | high | none | Training never applied the +1.3 accel bias that mujoco_infer adds; open. The lab sim used the bias (G7). |
| Playground | [25](https://github.com/apirrone/Open_Duck_Playground/issues/25) | issue | open | ModuleNotFoundError: No module named 'mujoco_playground._src.collision' | sim/training/policy | medium | not read (5) | mujoco_playground module missing (version mismatch). Pin versions before our own training (later step). |
| Playground | [26](https://github.com/apirrone/Open_Duck_Playground/issues/26) | issue | open | Initial IK placement sometimes lands on a backward-knee solution (intermittent); extreme gaits always do | sim/training/policy | low | none | Reference IK can give backward knees. Lab check: 2 of 240 shipped gaits bad, both at dx 0.222, unused by the stock range (G14). |
| RefGen | [1](https://github.com/apirrone/Open_Duck_reference_motion_generator/pull/1) | PR | merged | Poly fit | sim/training/policy | none | none | Polynomial fit of the reference motion. |
| RefGen | [2](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/2) | issue | closed | Error undefined symbol: EIGENPY_ARRAY_APIPyArray_RUNTIME_VERSION occured when run gait_generator.py | sim/training/policy | low | not read (3) | placo import error (eigenpy symbol); closed. |
| RefGen | [3](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/3) | issue | closed | An error occurred while running the generated data in the playground: KeyError. | sim/training/policy | low | not read (2) | KeyError when Playground loads a generated pkl; closed. |
| RefGen | [4](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/4) | issue | open | How to train the duck in MuJoCo to walk forward? | sim/training/policy | low | not read (1) | Forward-only gait set crashes Playground (KeyError); open. |
| RefGen | [5](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/5) | issue | open | Update on adding the function of adding new different robots | sim/training/policy | none | none | Asks for support for other robots. |
| RefGen | [6](https://github.com/apirrone/Open_Duck_reference_motion_generator/pull/6) | PR | open | Updating PlaCo to 0.8.8 | sim/training/policy | low | not read (2) | PlaCo 0.8.8 wheels (by the PlaCo author); open. |
| RefGen | [7](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/7) | issue | open | Install error:undefined symbol: EIGENPY_ARRAY_APIPyArray_RUNTIME_VERSION | sim/training/policy | low | none | Same placo eigenpy error; open. PR #6 (PlaCo 0.8.8) may fix it. |
| RefGen | [8](https://github.com/apirrone/Open_Duck_reference_motion_generator/issues/8) | issue | open | 【uv run scripts/replay_motion.py -f recordings/&lt;file&gt;.json】When I run this command, I find that there is no json file in the recordings directory. | sim/training/policy | low | none | replay_motion.py: no json in recordings; open. |

## 4. Where the issues contradict the lab docs

1. sim/SIM_WALK.md and sim/CURRENT_BUDGET.md (and through them POWER.md section 2, D8 and D10) treat the upstream MjInfer loop as the stock walk. Playground PR #24 and the code at the pins show that this loop feeds the policy a +1.3 accel x bias that training never had and the Runtime does not add. The sim numbers are for an input the robot will not see (G7).
2. HARDWARE_AUDIT B23 still says the eye LEDs go on GPIO27 and GPIO22 (Tnkr). Under D9 and the Runtime code those are the foot switch pins (Mini PR #24 table agrees), and the eyes are on GPIO24 and GPIO23. BOM E3b gives resistors for the two eyes only, so the projector LED (GPIO25) has none, while Mini #34 and the #33 TODO say the 1 W LEDs already overload the GPIO pins (G8).
3. GAPS A2 cites Mini #51 for "Feetech excludes over-voltage damage from warranty"; #51 only asks about 8.4 V on 7.4 V servos (the warranty point is from Feetech's after-sales page in REFERENCES.md). GAPS A3 reads #51 as stating the holder limit; #51 asks it as a question. No lab doc says #51 was closed on 2026-07-19 with no reply, so no upstream answer is coming.
4. sim/CURRENT_BUDGET.md says the Tenergy 10 A board "covers walking with margin". Mini #33 says the stock BMS had too many issues, and the third-party log relays community advice for 20 A boards after 10 A boards cut out. Neither side is measured on our parts; bench test it (G4).
5. SERVO_DEEP_DIVE section 6 (bench test) does not read registers 84, 85 and 86 or goal time and goal speed (44, 46). Section 5 cause 1 agrees in general, but the outside evidence says register 85 at its factory value is the main cause of the #48 symptom (G1).
6. HARDWARE_AUDIT B20 says the Runtime IMU code "runs IMUPLUS mode" (that is imu.py). The walk script and calibrate_imu.py import raw_imu.py, which runs NDOF mode (same axis remap Y, X, Z with signs -, +, + when upside_down is False). Related to Runtime #3 (G2).
7. Found while checking Mini #9, not from an issue: SERVO_DEEP_DIVE lists "BOM CSV: https://github.com/apirrone/Open_Duck_Mini/blob/v2/bom.csv", but there is no bom.csv in the repo at b23317a. The upstream BOM is the Google Sheet; the lab's "bom.csv" must be a local export of it.

No issue body contradicts any other lab decision (D1 to D12).

## 5. Outside sources used (not upstream issues)
- Third-party build log: https://github.com/jyxddd/open-duck-mini-notes (commit 7036c3a, 2026-11-01; main log docs/组装与调试问题记录.md dated 2026-10-25, Chinese, read in full). One builder: Pi Zero 2 W, Runtime v2, BEST_WALK_ONNX_2, 14 STS3215 7.4 V, Waveshare board. Numbers are theirs, not checked by us. Used in G1, G2, G4, G7, G10, G14.
- pypot, branch support-feetech-sts3215 (commit f6d305e, 2025-06-16), pypot/feetech/sts3215_io.py: "acceleration" at 41, "maximum velocity" at 84, "maximum acceleration" at 85. This is the library the Runtime configure scripts use.
- rustypot 1.13.1 on docs.rs (servo/feetech/sts3215): acceleration 41, maximum_velocity_limit 84, maximum_acceleration 85, acceleration_multiplier 86.
- Upstream BOM Google Sheet, CSV export read 2026-11-01: 22 robot lines and 7 expression lines, none for a game controller (G9).
- WebSearch index text for Mini #48 (part of the thread).
